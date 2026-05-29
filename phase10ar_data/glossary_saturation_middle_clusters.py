#!/usr/bin/env python3
"""
Phase 10AR + 10AS: Glossary Saturation & Decision Support
Middle-ranked clusters: Cat Supplies, Dog Grooming, Dog Harnesses, Cat Toys

For EACH post, add missing:
  1. Key Terms block (grey bg #f8fafc, border #e2e8f0) — 5-8 terms
  2. Common Mistakes block (red bg #fef2f2, border #fecaca) — 4-6 mistakes
  3. Beginner Recommendations block (blue bg #eff6ff, border #bfdbfe) — practical starting advice

Rules:
  - UK spelling throughout
  - No fake experts/credentials, no Product/Review schema, no affiliate links
  - Skip existing blocks
  - 2-second delay between API calls
  - Insert before editorial standards trust footer
"""

import subprocess, json, time, csv, os, re, tempfile, html

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ar_data"
LOG_FILE = os.path.join(DATA_DIR, "glossary_saturation_middle_clusters.csv")
DELAY = 2

# ── All post IDs by cluster ──
CLUSTERS = {
    "Cat Supplies": [4335, 4321, 4314, 4209, 4202, 696, 7175],
    "Cat Toys": [5033, 5032, 4409, 4408, 4407, 4406, 4307, 4300, 4286, 4188, 4181, 4174],
    "Dog Grooming": [5464, 4563, 4251, 4244, 4237, 4230, 4078, 4071, 4064, 4057],
    "Dog Harnesses": [5418, 4414, 4413, 4412, 4411, 4279, 4258, 4139, 4049, 4042, 4034, 4027],
}

# ══════════════════════════════════════════════════════════════════════
# KEY TERMS — 5-8 topic-specific terms per post
# ══════════════════════════════════════════════════════════════════════

KEY_TERMS = {
    # ── Cat Supplies ──
    4335: [  # Cat Litter Disposal
        ("Nappy sack", "A small, scented plastic bag originally designed for nappy disposal, widely used in the UK for bagging soiled cat litter before placing it in the household waste bin."),
        ("Litter genie", "A dedicated pail system with a continuous liner that seals odour between uses, reducing the number of trips to the outdoor bin during daily scooping routines."),
        ("Biodegradable liner", "A compostable bag or liner made from plant-based materials such as cornstarch, used inside litter trays or disposal units to simplify cleaning and reduce plastic waste."),
        ("Clumping litter", "A clay- or plant-based litter that forms solid clumps on contact with moisture, making daily scooping easier and helping to keep the remaining litter cleaner for longer."),
        ("Toxoplasmosis risk", "A parasitic infection carried in cat faeces that can pose health risks to pregnant women and immunocompromised individuals, which is why litter should never be flushed and gloves should be worn during cleaning."),
        ("Dual-bin method", "A waste management approach where soiled litter is sealed in a dedicated small bin with a lid, which is emptied into the main household waste on collection day, keeping odour contained between collections."),
    ],
    4321: [  # Cat Litter Types
        ("Clumping clay", "A bentonite-based litter that forms firm clumps around urine and faeces, allowing spot removal without changing the entire tray. It is the most popular litter type in the UK."),
        ("Crystal litter", "Silica gel granules that absorb moisture and trap odour without clumping. Crystal litter lasts longer between full changes but does not form removable clumps."),
        ("Tofu litter", "A plant-based litter made from soybean fibre that clumps on contact with moisture. It is lightweight, flushable in small quantities, and biodegradable."),
        ("Non-clumping litter", "Traditional absorbent litter, often clay or wood-based, that soaks up moisture without forming clumps. The entire tray must be emptied and replaced regularly."),
        ("Dust-free rating", "A manufacturer's claim about the amount of airborne particles produced when litter is poured or disturbed. Lower dust levels are important for cats and owners with respiratory sensitivities."),
        ("Tracking", "The tendency of litter granules to stick to a cat's paws and be carried outside the tray onto surrounding floors. Larger, heavier granules typically track less."),
        ("Odour control", "The ability of a litter to neutralise or contain ammonia and faecal smells. Methods include activated carbon, baking soda, or the moisture-sealing properties of clumping formulas."),
    ],
    4314: [  # Cat Litter Trays
        ("Hooded tray", "An enclosed litter tray with a removable lid or hood that provides privacy for the cat and helps contain odour and litter scatter within the unit."),
        ("Open tray", "A simple, lidless litter tray that offers easy access and good ventilation. Many cats prefer open trays because they allow a clear view of their surroundings while using it."),
        ("Self-cleaning tray", "An automated litter tray that uses a motorised rake, rotating mechanism, or other system to separate waste from clean litter after each use, reducing manual scooping."),
        ("Top-entry tray", "A litter tray design where the cat enters through a hole in the lid, which significantly reduces litter tracking and prevents dogs from accessing the contents."),
        ("Tray liner", "A disposable or reusable sheet placed inside the tray beneath the litter to protect the base from staining and make full litter changes quicker and cleaner."),
        ("Carbon filter", "An activated charcoal filter fitted into hooded litter trays to absorb ammonia and other odours before they escape through the ventilation openings."),
    ],
    4209: [  # Heated Cat Beds
        ("Thermostatically controlled", "A heating element that automatically maintains a set temperature, switching off when the bed reaches the target warmth and reactivating when it cools, preventing overheating."),
        ("Self-warming bed", "A bed that uses reflective thermal layers to capture and return the cat's own body heat without any electrical components, making it safe for unsupervised use."),
        ("Low-voltage heating pad", "An electrically heated mat that operates on a reduced voltage, typically twelve volts, to minimise the risk of burns or electrical faults. Commonly used inside cat beds during winter."),
        ("Chew-resistant cord", "A power cable wrapped in a reinforced sheath, often steel or nylon, designed to withstand biting by cats or other pets and reduce the risk of electrical injury."),
        ("Thermal comfort zone", "The ambient temperature range, roughly twenty to twenty-five degrees Celsius, within which a cat can maintain its body temperature without expending extra energy."),
        ("MET/CE certification", "Safety marks indicating that an electrical product has been tested against recognised safety standards. Look for these marks on any heated pet product sold in the UK."),
    ],
    4202: [  # Cat Beds
        ("Bolster bed", "A cat bed with raised, cushioned edges that provide head and neck support while creating a sense of enclosure and security. Particularly popular with cats that like to curl up."),
        ("Donut bed", "A round, deep-sided plush bed that allows cats to burrow into soft material. Often marketed as calming beds because the enclosed shape mimics being nestled against another animal."),
        ("Igloo bed", "A fully enclosed, cave-style bed with a small entrance that provides warmth, darkness, and privacy. Suited to shy or anxious cats that prefer hidden sleeping spots."),
        ("Memory foam", "A pressure-responsive material that moulds to the cat's body shape, distributing weight evenly and supporting joints. Recommended for older cats or those with arthritis."),
        ("Removable cover", "A washable outer fabric layer that can be unzipped and machine-washed separately from the bed's filling, making hygiene maintenance easier and extending the bed's usable life."),
        ("Radiator hammock", "A suspended bed that hooks over a household radiator, using the warmth from central heating to provide a cosy elevated sleeping spot during colder months."),
    ],
    696: [  # Essential Cat Supplies
        ("Starter kit", "A collection of basic items a new cat owner needs from day one, typically including a litter tray, food and water bowls, a carrier, a scratching post, and basic toys."),
        ("Microchip cat flap", "A pet door that reads your cat's implanted microchip to grant access, preventing neighbourhood cats or wildlife from entering your home."),
        ("Breakaway collar", "A cat collar with a safety release mechanism that opens under pressure if the collar catches on a branch, fence, or other object, preventing strangulation."),
        ("Scratching post", "A vertical or angled surface covered in sisal rope, carpet, or cardboard that allows cats to maintain their claws, stretch their muscles, and mark territory without damaging furniture."),
        ("Water fountain", "An electrically powered bowl that circulates and filters water continuously, encouraging cats to drink more. Many cats prefer moving water to a still bowl."),
        ("Carrier training", "The gradual process of helping a cat feel comfortable inside a carrier before it is needed for vet visits or travel, reducing stress for both cat and owner."),
    ],
    7175: [  # Cat Supply Essentials Glossary
        ("Obligate carnivore", "An animal that must eat meat to obtain essential nutrients. Cats cannot synthesise taurine or arachidonic acid from plant sources, making animal protein a non-negotiable dietary requirement."),
        ("Substrate preference", "A cat's individual preference for the texture and type of litter material it eliminates on. Abrupt changes to litter type are a common cause of tray avoidance."),
        ("Whisker fatigue", "Sensory overload caused by a cat's whiskers repeatedly touching the sides of a narrow bowl during feeding. Switching to a wide, shallow dish usually resolves reluctant eating."),
        ("FLUTD", "Feline Lower Urinary Tract Disease — a group of conditions affecting the bladder and urethra. Symptoms include frequent urination, straining, and blood in urine. Urgent veterinary attention is needed if a cat cannot urinate."),
        ("Feliway", "A synthetic feline facial pheromone product available as a diffuser or spray, used to reduce stress-related behaviours such as urine spraying, scratching, and hiding."),
        ("Complete food", "A pet food that provides all the nutrients a cat requires and can be fed as the sole diet, as opposed to complementary food which must be combined with other products."),
        ("Slow feeder", "A bowl or puzzle with ridges and obstacles that forces a cat to eat more slowly, reducing vomiting from fast eating and providing mental stimulation."),
    ],

    # ── Cat Toys ──
    5033: [  # How to Choose Right Cat Toy
        ("Prey drive", "A cat's innate instinct to hunt, which follows a predictable sequence of stare, stalk, chase, pounce, and bite. Toys that engage this full sequence provide the most satisfying play."),
        ("Interactive toy", "Any toy that requires owner participation during play, such as wand toys or feather teasers. Interactive play builds the bond between cat and owner while providing superior exercise."),
        ("Passive toy", "A toy a cat can play with independently, including balls, crinkle toys, and automated devices. Useful when owners are away but less enriching than interactive options."),
        ("Catnip response", "The inherited genetic sensitivity to nepetalactone in catnip, present in roughly sixty to seventy percent of cats. Kittens under six months rarely respond."),
        ("Toy rotation", "The practice of keeping only a few toys out at any time and swapping them every few days to maintain novelty and prevent habituation."),
        ("Silver vine", "An Asian plant (Actinidia polygama) that triggers a euphoric response in approximately eighty percent of cats, including many that do not react to catnip."),
    ],
    5032: [  # Cat Toys FAQ
        ("Prey sequence", "The natural hunting pattern — stare, stalk, chase, pounce, bite — that effective cat toys should mimic to provide complete physical and mental satisfaction."),
        ("Kick toy", "An elongated stuffed toy designed for cats to grab with their front paws and kick vigorously with their hind legs, mimicking the killing bite used on prey."),
        ("Puzzle feeder", "A food-dispensing toy that requires the cat to solve a problem to access treats, providing mental stimulation and slowing down fast eaters."),
        ("Wand toy", "A flexible rod with string and an attachment such as feathers or fabric, used by owners to simulate prey movement during interactive play sessions."),
        ("Laser pointer frustration", "The stress that can build when a cat chases a laser dot but never physically catches it. Best practice is to end laser play by directing the dot onto a real toy or treat."),
        ("Sensory enrichment", "Toys and activities that stimulate one or more of a cat's senses — visual, auditory, olfactory, tactile, and gustatory — to maintain overall wellbeing."),
    ],
    4409: [  # Kitten vs Adult Cat Toys
        ("Socialisation window", "The critical period from approximately two to seven weeks of age during which kittens learn to interact with other animals and their environment. Play during this window shapes lifelong behaviour."),
        ("Age-appropriate play", "Selecting toys and play intensity based on a cat's life stage, from gentle, smaller toys for kittens to sturdier, more challenging options for adults."),
        ("Bite inhibition", "The learned ability to moderate bite force during play, typically acquired through interactions with littermates. Kittens removed too early may bite harder during play."),
        ("Teething toy", "A chewable toy designed for kittens between three and seven months old who are losing baby teeth and developing adult teeth, providing relief from gum discomfort."),
        ("Play aggression", "Rough or biting behaviour during play that is normal in kittens but should be redirected onto toys rather than hands or feet to prevent adult biting habits."),
        ("Senior cat enrichment", "Adapted play options for older cats with reduced mobility, such as ground-level toys, gentle wand play, and scent-based enrichment like catnip or silver vine."),
    ],
    4408: [  # When to Replace Cat Toys
        ("Safety inspection", "A regular check of toys for loose parts, fraying string, exposed stuffing, or damaged mechanisms that could pose a choking or ingestion hazard."),
        ("Material fatigue", "The gradual weakening of toy materials through repeated use, washing, and exposure to saliva, which can cause unexpected breakage during play."),
        ("Linear foreign body", "A string, ribbon, or thread swallowed by a cat that can become anchored in the digestive tract and cause life-threatening intestinal damage. A veterinary emergency."),
        ("Catnip potency", "The strength of the nepetalactone compound in catnip, which diminishes over time with exposure to air and light. Stored catnip maintains potency longer."),
        ("Replacement schedule", "A routine timetable for inspecting and replacing worn toys, typically every one to three months for heavily used items and whenever visible damage appears."),
    ],
    4407: [  # DIY Cat Toys
        ("Non-toxic materials", "Crafting supplies that are safe if a cat licks, chews, or accidentally ingests small amounts. Water-based glues, untreated cardboard, and undyed fabric are common safe choices."),
        ("Crinkle material", "Any material that produces a rustling sound when manipulated, mimicking the sounds of small prey moving through undergrowth. Cellophane or tissue paper work well inside DIY toys."),
        ("Supervised play", "Play sessions where the owner is present and actively watching, essential for DIY toys that may contain small parts or materials not tested to pet safety standards."),
        ("Foraging toy", "A homemade puzzle or container that hides treats, requiring the cat to use problem-solving skills to access the food. Toilet roll tubes and egg boxes make simple versions."),
        ("Feather attachment", "Natural or synthetic feathers tied to string or a stick for interactive play. Must always be stored out of reach after play as swallowed feathers can cause intestinal blockage."),
    ],
    4406: [  # Best Interactive Cat Toys Indoor
        ("Environmental enrichment", "Any modification to a cat's living space that increases physical activity, mental stimulation, or natural behaviour expression, reducing stress and boredom."),
        ("Prey simulation", "A toy design or play technique that mimics the movement, sound, or texture of real prey animals, engaging the cat's natural hunting instincts."),
        ("Solo play capability", "A toy's ability to entertain a cat without human involvement, often through automated movement, built-in timers, or self-rolling mechanisms."),
        ("Overstimulation signs", "Behavioural cues such as dilated pupils, flattened ears, skin twitching, or tail lashing that indicate a cat has become overwhelmed during play and needs a break."),
        ("Play session duration", "The recommended length of a single interactive play period, typically ten to fifteen minutes for most adult cats, adjusted based on age and fitness level."),
        ("Hunting reward", "Ending a play session with a treat or small meal to simulate the satisfaction of a successful hunt, which helps the cat settle calmly after vigorous play."),
    ],
    4307: [  # Wall-Mounted Cat Scratchers
        ("Sisal rope", "A natural fibre rope derived from the agave plant, commonly wound around scratching posts and surfaces. Cats prefer its coarse texture for claw maintenance."),
        ("Vertical scratching", "The upward stretching motion cats perform when scratching on tall, wall-mounted, or post-mounted surfaces, which exercises shoulder and back muscles."),
        ("Territory marking", "The behaviour of depositing scent from glands in a cat's paw pads onto scratched surfaces, communicating presence to other cats in the household."),
        ("Wall anchor", "A fixing used to secure heavy cat furniture to a wall, preventing it from toppling when a cat jumps onto or climbs the unit. Essential for safety in homes with children."),
        ("Horizontal scratcher", "A flat or angled scratching surface placed on the floor, preferred by some cats over vertical options. Many cats use both depending on their stretching position."),
    ],
    4300: [  # Cardboard Cat Scratchers
        ("Corrugated cardboard", "Layered cardboard with a fluted inner layer that creates a satisfying texture for cats to scratch. It is inexpensive, recyclable, and widely preferred by cats."),
        ("Scratch pad", "A flat or angled board made from compressed corrugated cardboard, designed to be placed on the floor or mounted at an incline for scratching."),
        ("Catnip infusion", "The practice of sprinkling dried catnip onto or into a scratching surface to attract cats and encourage them to use the scratcher instead of furniture."),
        ("Reversible design", "A scratcher built so that both sides can be used, effectively doubling its lifespan before needing replacement. Many budget cardboard scratchers offer this feature."),
        ("Scratch debris", "The small fragments of cardboard that collect around a scratcher during use. Regular vacuuming keeps the area tidy and helps owners monitor wear rate."),
    ],
    4286: [  # Cat Scratching Posts
        ("Sisal fabric", "A woven material made from sisal fibre that provides a flat, textured scratching surface. Some cats prefer sisal fabric over sisal rope."),
        ("Cat tree", "A multi-level structure combining scratching posts, platforms, and sometimes enclosed hideaways, providing exercise, scratching, and vertical territory in one unit."),
        ("Stability base", "A wide, heavy base on a scratching post that prevents wobbling or toppling when a cat pushes against it at full stretch, which is critical for encouraging use."),
        ("Claw sheath", "The outer layer of a cat's claw that is shed during scratching, revealing a sharper new claw beneath. Finding sheaths around a scratcher confirms it is being used."),
        ("Post height", "The measurement from base to tip of a scratching post, which should be tall enough for the cat to fully extend its body while stretching upward — at least the cat's full body length."),
        ("Replacement post", "A spare or refill scratching surface that can be fitted to an existing cat tree or base unit, extending the product's life without buying an entirely new structure."),
    ],
    4188: [  # Catnip Toys
        ("Nepetalactone", "The active chemical compound in catnip that triggers the euphoric rolling, rubbing, and playful behaviour seen in sensitive cats. It is inhaled through the nose and is completely harmless."),
        ("Catnip sensitivity", "The inherited genetic trait that determines whether a cat responds to catnip. Approximately sixty to seventy percent of cats carry the gene, and kittens under six months typically show no reaction."),
        ("Silver vine", "An alternative to catnip from the plant Actinidia polygama, effective for roughly eighty percent of cats including many that do not respond to catnip."),
        ("Valerian root", "A plant-based attractant that produces a strong response in some cats, particularly those indifferent to catnip. It has a strong odour that many humans find unpleasant."),
        ("Recharge period", "The roughly thirty-minute refractory period after exposure to catnip during which a cat will not respond to further catnip stimulation, regardless of the amount offered."),
        ("Potency preservation", "Storing catnip toys in sealed containers or bags between uses to maintain the strength of the nepetalactone compound, which degrades with exposure to air and light."),
    ],
    4181: [  # Interactive Cat Toys Wand & Puzzle
        ("Da Bird style", "A wand toy design using a swivel connector and feather attachment that spins and flutters realistically during play, closely mimicking the movement of a bird in flight."),
        ("Puzzle difficulty", "The complexity level of a food puzzle, which should start easy and increase gradually as the cat masters each stage. Starting too difficult causes frustration and abandonment."),
        ("Swivel attachment", "A rotating connector between the wand tip and the toy attachment that prevents string tangling and creates more natural, unpredictable movement during play."),
        ("Treat-dispensing toy", "A device that releases small amounts of food or treats when manipulated by the cat, combining physical activity with mental problem-solving and slowing eating pace."),
        ("Elastic hazard", "The danger posed by elastic string on wand toys, which can snap back and injure eyes or be ingested and cause intestinal blockage. Non-elastic string is always safer."),
        ("Food motivation", "The degree to which a cat is driven by food rewards, which determines how effectively puzzle feeders and treat-dispensing toys engage that individual."),
    ],
    4174: [  # Best Cat Toys Complete Guide
        ("Interactive play", "Owner-led play using wand toys, feather teasers, or similar equipment that requires human participation. Recognised by welfare organisations as the highest-quality enrichment for cats."),
        ("Prey drive", "A cat's instinctive motivation to hunt, present in all cats regardless of whether they have outdoor access. Toys that mimic prey movement engage this drive most effectively."),
        ("Enrichment rotation", "A structured schedule of swapping toys, scents, and play activities to maintain novelty and prevent the habituation that leads to toy disinterest."),
        ("Catnip response", "The genetic sensitivity to nepetalactone that triggers euphoric behaviour in roughly two-thirds of cats, with alternatives like silver vine available for non-responders."),
        ("Kick toy", "An elongated, sturdy toy designed for cats to grab, wrestle, and kick with their hind legs, satisfying the pounce-and-bite phase of the prey sequence."),
        ("Safety sizing", "Selecting toys that are too large to be swallowed and free of detachable parts small enough to pose a choking hazard, particularly important for kittens and vigorous chewers."),
    ],

    # ── Dog Grooming ──
    5464: [  # Pet Grooming Glossary
        ("Double coat", "A coat structure consisting of a dense, insulating undercoat beneath a protective outer coat of guard hairs. Common in breeds such as Labradors, Huskies, and German Shepherds."),
        ("Undercoat rake", "A grooming tool with long, widely spaced teeth designed to reach through the top coat and remove loose undercoat hair, reducing shedding and preventing matting."),
        ("Deshedding", "The process of removing loose and dead fur from a dog's undercoat using a specialised tool, typically performed more frequently during spring and autumn moult cycles."),
        ("Hand stripping", "A grooming technique used on wire-coated breeds where dead hair is pulled out by hand or with a stripping knife, maintaining the correct coat texture and colour."),
        ("Quick (nail)", "The blood vessel and nerve running through the centre of a dog's nail. Cutting into the quick causes pain and bleeding, which is why nail trimming requires care and good lighting."),
        ("Blade guard", "A clip-on attachment for electric clippers that controls the cutting length, preventing accidental close shaving and allowing consistent coat length across the body."),
        ("Coat blowing", "The seasonal shedding period when double-coated breeds shed their entire undercoat over a few weeks, typically occurring in spring and autumn."),
    ],
    4563: [  # Dog Grooming Basics
        ("Slicker brush", "A grooming tool with fine, short wire bristles set at an angle on a flat or curved pad, used for removing tangles, loose hair, and light matting from most coat types."),
        ("Pin brush", "A brush with widely spaced, rounded-tip metal pins, suitable for longer coats. It detangles without pulling and is gentler than a slicker brush on sensitive skin."),
        ("Matting", "Tangled clumps of fur that form close to the skin when loose hair is not regularly removed. Severe mats restrict airflow to the skin and can cause irritation or infection."),
        ("Desensitisation", "Gradually introducing a dog to grooming tools and handling through short, positive sessions to build comfort and reduce fear or resistance over time."),
        ("Nail grinding", "Using a rotary tool to file down a dog's nails gradually instead of clipping. Some dogs tolerate grinding better, and it reduces the risk of cutting into the quick."),
        ("Ear cleaning solution", "A veterinary-formulated liquid used to dissolve wax and debris from a dog's ear canal. Essential for floppy-eared breeds prone to moisture buildup and infection."),
    ],
    4251: [  # Cat Shampoo
        ("pH-balanced formula", "A shampoo formulated to match the natural pH of a cat's skin, which is more alkaline than human skin. Using human shampoo disrupts the skin barrier and causes dryness."),
        ("Hypoallergenic shampoo", "A shampoo made without common irritants such as artificial fragrances, dyes, and harsh detergents, designed for cats with sensitive or reactive skin."),
        ("Waterless shampoo", "A dry or foam shampoo that cleans and freshens a cat's coat without the need for rinsing, useful for cats that strongly resist bathing or for quick spot cleaning."),
        ("Medicated shampoo", "A veterinary-prescribed shampoo containing active ingredients to treat specific skin conditions such as fungal infections, bacterial dermatitis, or severe dandruff."),
        ("Oatmeal formula", "A shampoo containing colloidal oatmeal, which soothes irritated skin and provides a mild cleansing action. Suitable for cats with dry, itchy, or flaky skin."),
        ("Contact time", "The period a medicated or conditioning shampoo must remain on the coat before rinsing, typically three to ten minutes, for the active ingredients to take effect."),
    ],
    4244: [  # Cat Nail Clippers
        ("Quick (nail)", "The pink blood vessel visible inside lighter-coloured nails. In dark nails it is not visible, so trimming must proceed in small increments to avoid cutting into it."),
        ("Guillotine clipper", "A nail trimming tool with a single blade that slides across an opening when the handle is squeezed, cutting the nail cleanly. Popular for small to medium cats."),
        ("Scissor clipper", "A nail trimmer shaped like small scissors with curved blades that close together to cut the nail, offering more control and visibility than guillotine styles."),
        ("Styptic powder", "A clotting agent, typically containing ferric subsulphate, applied to a nail tip if the quick is accidentally cut. Stops bleeding within seconds and should be kept on hand."),
        ("Nail grinding", "Using a small rotary tool to file a cat's nails smooth rather than clipping them. It removes less material per pass and some cats tolerate it better than clippers."),
        ("Dewclaw", "The small, higher claw on the inner side of a cat's leg that does not touch the ground. Dewclaws need regular trimming as they can curl and grow into the paw pad if neglected."),
    ],
    4237: [  # Cat Brushes
        ("Slicker brush", "A tool with fine, angled wire bristles used to remove tangles, loose fur, and light mats from medium to long-haired cats. Gentle pressure is essential to avoid scratching the skin."),
        ("Deshedding tool", "A specialised grooming implement that reaches through the topcoat to remove loose undercoat hair, significantly reducing shedding around the home."),
        ("Bristle brush", "A brush with natural or synthetic bristles suited to short-haired cats, used for smoothing the coat, distributing natural oils, and removing surface debris."),
        ("Undercoat", "The dense, soft layer of fur beneath the outer guard hairs that provides insulation. Breeds with a thick undercoat require regular grooming to prevent matting."),
        ("Flea comb", "A fine-toothed metal comb used to detect and remove fleas and flea dirt from a cat's coat. The narrow spacing between teeth traps adult fleas during combing."),
        ("Grooming glove", "A rubber-studded mitten that removes loose hair while mimicking the sensation of petting, useful for cats that are nervous around traditional brushes."),
    ],
    4230: [  # Cat Grooming Supplies
        ("Grooming routine", "A regular schedule of brushing, nail trimming, ear checking, and dental care tailored to a cat's coat type and temperament, ideally established from kittenhood."),
        ("Mat splitter", "A grooming tool with one or more recessed blades designed to cut through matted fur safely, splitting mats into smaller sections that can then be combed out."),
        ("Ear mites", "Tiny parasites (Otodectes cynotis) that live in the ear canal, causing intense itching, dark discharge, and head shaking. Veterinary treatment is needed to eliminate them."),
        ("Dental care kit", "A set containing a cat-specific toothbrush and enzymatic toothpaste designed for feline use. Human toothpaste contains fluoride and foaming agents that are toxic to cats."),
        ("Coat conditioner", "A leave-in or rinse-out product that softens fur, reduces static, and makes detangling easier. Particularly useful for long-haired breeds prone to knotting."),
        ("Grooming table", "A raised, non-slip surface used by professional groomers and some owners to keep a cat at a comfortable working height during grooming sessions, with a restraint arm for safety."),
    ],
    4078: [  # Dog Nail Clippers
        ("Quick identification", "The process of locating the blood vessel inside a dog's nail before trimming. In light nails, the quick appears as a pink line; in dark nails, the chalky white ring at the cut surface signals proximity."),
        ("Guillotine trimmer", "A nail cutting tool with a replaceable blade that slides across an opening when squeezed, designed for small to medium dogs. The blade dulls over time and needs periodic replacement."),
        ("Rotary grinder", "An electric or battery-powered tool with a spinning abrasive head used to gradually file down nail length. It produces a smoother finish and reduces the risk of cutting the quick."),
        ("Styptic powder", "A clotting compound applied to a bleeding nail tip if the quick is accidentally nicked. Every dog owner who trims nails at home should keep a pot within reach."),
        ("Dewclaw trimming", "Maintenance of the higher, non-weight-bearing claws on the inner leg, which do not wear down naturally and can curl into the pad if left untrimmed."),
        ("Desensitisation", "A training process that gradually accustoms a dog to having its paws handled and nails touched before actual trimming begins, reducing fear and resistance."),
    ],
    4071: [  # Dog Shampoo — already has Key Terms; will skip
        ("Soap-free formula", "A shampoo that cleans without traditional soap agents, using milder surfactants that do not strip natural oils from a dog's coat and skin."),
        ("pH balance", "The acid-alkaline level of a shampoo, ideally matched to canine skin (pH 6.5–7.5). Human shampoo is too acidic for dogs and disrupts the skin barrier."),
        ("Hypoallergenic", "A product formulated without common irritants, fragrances, and dyes, designed for dogs with sensitive or allergy-prone skin."),
        ("Medicated shampoo", "A veterinary-directed shampoo containing active therapeutic ingredients to treat conditions such as fungal infections, bacterial dermatitis, or seborrhoea."),
        ("Conditioner", "A post-wash product that restores moisture, reduces tangles, and adds a protective layer to the coat. Especially useful for long-coated and curly breeds."),
        ("Contact time", "The duration a medicated or deep-cleaning shampoo must remain on the coat before rinsing for its active ingredients to work, typically five to ten minutes."),
    ],
    4064: [  # Dog Brushes
        ("Slicker brush", "A grooming tool with fine, angled wire bristles used to detangle, remove loose fur, and smooth medium to long coats. Light pressure avoids scratching the skin."),
        ("Pin brush", "A brush with rounded-tip metal pins set in a rubber cushion, ideal for long, flowing coats. It separates hair without breaking it and is gentler on sensitive dogs."),
        ("Bristle brush", "A brush with tightly packed natural or nylon bristles, best for short-coated breeds. It distributes natural oils, adds shine, and removes surface dirt."),
        ("Undercoat rake", "A tool with long, rotating or fixed teeth designed to penetrate the topcoat and remove loose undercoat hair, essential for double-coated breeds during shedding season."),
        ("Dematting comb", "A tool with sharp, recessed blades that safely cut through mats and tangles close to the skin without pulling. Used carefully to avoid nicking the skin beneath mats."),
        ("Grooming frequency", "How often a dog should be brushed, determined by coat type: daily for long and curly coats, two to three times weekly for double coats, and weekly for short coats."),
    ],
    4057: [  # Dog Grooming Supplies
        ("Grooming kit", "A bundled set of essential tools — typically a brush, comb, nail clippers, ear cleaner, and shampoo — providing everything needed for a basic home grooming routine."),
        ("Styptic pencil", "A solid stick of styptic compound used to stop minor bleeding from small nicks during grooming. Effective on nail quick cuts and minor skin abrasions."),
        ("Thinning shears", "Scissors with one or both blades serrated, used to reduce bulk in thick coats without creating harsh lines. They blend and soften the finish around ears, legs, and tails."),
        ("Ear powder", "A drying agent applied inside the ear canal before plucking or cleaning to improve grip on ear hair and reduce moisture that encourages bacterial growth."),
        ("Grooming spray", "A light conditioning mist applied to the coat before or during brushing to reduce static, ease tangles, and add a protective layer against dirt and moisture."),
        ("Blade cooling spray", "A lubricant and coolant sprayed on clipper blades during use to prevent overheating, which can cause discomfort or burns on the dog's skin during prolonged clipping sessions."),
    ],

    # ── Dog Harnesses ──
    5418: [  # Dog Harness Types Explained
        ("No-pull harness", "A harness designed with a front-clip attachment or tightening mechanism that redirects a pulling dog's momentum back toward the handler, discouraging forward lunging."),
        ("Front-clip harness", "A harness with the lead attachment point on the chest, which steers the dog to the side when it pulls, naturally redirecting forward movement."),
        ("Back-clip harness", "A harness with the lead attachment on the back, offering comfort for well-trained dogs but providing less control over pulling behaviour."),
        ("Step-in harness", "A harness design where the dog steps into two leg loops that are then buckled or clipped together on the back, avoiding the need to pass anything over the head."),
        ("Overhead harness", "A harness that slips over the dog's head before being fastened around the chest, typically quicker to fit than step-in designs on calm or trained dogs."),
        ("Girth measurement", "The circumference of a dog's ribcage measured at the widest point just behind the front legs, used to determine correct harness size."),
    ],
    4414: [  # Harness vs Collar
        ("Tracheal pressure", "The compression force applied to a dog's windpipe by a collar when the dog pulls or lunges, which can cause coughing, choking, or long-term tracheal damage."),
        ("Pressure distribution", "The way a harness spreads the force of pulling across the chest and shoulders rather than concentrating it on the neck, reducing the risk of injury."),
        ("Collar tag requirement", "UK law (Control of Dogs Order 1992) requires dogs to wear a collar with a tag showing the owner's name and address when in a public place."),
        ("Escape-proof design", "A harness with a secondary strap connecting the chest and back sections, preventing dogs that back up or twist from slipping out of the harness."),
        ("Flat collar", "A standard adjustable collar with a buckle or clip closure, suitable for carrying identification tags and appropriate for dogs that walk calmly on a lead."),
        ("Head halter", "A device that loops around a dog's muzzle and behind the ears, controlling the head direction to reduce pulling. Not a muzzle — the dog can still eat, drink, and pant."),
    ],
    4413: [  # How to Measure Dog for Harness
        ("Girth measurement", "The most critical harness measurement, taken around the widest part of the ribcage just behind the front legs using a flexible tape measure."),
        ("Neck circumference", "The distance around the base of the dog's neck where a collar would sit, needed for harnesses with a neck loop or overhead design."),
        ("Two-finger rule", "The fitting standard that requires two fingers to fit comfortably between the harness strap and the dog's body at every contact point, ensuring security without restriction."),
        ("Adjustment points", "The buckles, sliders, or Velcro sections on a harness that allow strap length to be fine-tuned for a precise fit as the dog grows or its weight changes."),
        ("Chest breadth", "The measurement across the front of the chest from one shoulder point to the other, important for wide-chested breeds to ensure the harness front panel fits correctly."),
    ],
    4412: [  # No-Pull Dog Harness Guide
        ("Front-clip mechanism", "A lead attachment point positioned on the chest that redirects forward momentum to the side when the dog pulls, naturally discouraging lunging without causing pain."),
        ("Martingale loop", "A tightening strap section that closes gently when a dog pulls, providing a corrective sensation without choking. Some harnesses incorporate this feature on the chest strap."),
        ("Positive reinforcement", "A training approach where desired behaviour is rewarded with treats, praise, or play. No-pull harnesses work best when combined with reward-based loose-lead training."),
        ("Chafing", "Skin irritation caused by a harness rubbing against the dog's body, particularly behind the front legs and across the sternum. Padded straps and correct sizing prevent this."),
        ("Dual-clip harness", "A harness with both front and back attachment points, allowing the handler to choose the configuration based on the walking situation and the dog's training progress."),
        ("Loose-lead walking", "The trained behaviour where a dog walks beside or near the handler without tension on the lead, which is the ultimate goal when using any no-pull harness."),
    ],
    4411: [  # Complete Guide Types Fitting Safety — already has Key Terms and Common Mistakes
        ("Padded harness", "A harness with cushioned straps or a fleece-lined chest panel that distributes pressure evenly and prevents rubbing on short-haired or sensitive-skinned dogs."),
        ("Quick-release buckle", "A clip mechanism that allows the harness to be removed rapidly with one hand, useful in emergencies or when a dog needs to be freed from an entanglement."),
        ("Reflective trim", "High-visibility strips or stitching on harness straps that reflect light from vehicle headlights, improving the dog's visibility during early morning, evening, and winter walks."),
        ("Weight rating", "The maximum dog weight a harness is designed to safely restrain, which should be checked against your dog's actual weight to ensure the hardware and webbing can cope."),
        ("Y-frame design", "A harness shape where the front straps form a Y on the chest, leaving the shoulder joints unobstructed and allowing full range of motion during walking or running."),
    ],
    4279: [  # Cat Harnesses
        ("Figure-eight harness", "A cat harness design formed from two connected loops — one around the neck and one around the chest — that provides a secure fit with minimal bulk."),
        ("Escape-proof design", "A harness with a secondary connecting strap between the neck and chest loops that prevents cats from backing out, which is a common issue with loose-fitting models."),
        ("Indoor training", "The process of allowing a cat to wear a harness indoors for short, supervised periods before venturing outside, building familiarity and reducing stress."),
        ("Lightweight webbing", "Thin, flexible strap material that is strong enough to restrain a cat but light enough not to weigh down or restrict natural movement."),
        ("Vest-style harness", "A cat harness with a broad fabric panel covering the chest and back, distributing pressure over a larger area and making it harder for the cat to escape."),
        ("Lead attachment point", "The D-ring on a cat harness where the lead clips on, typically positioned on the back between the shoulder blades to allow natural walking movement."),
    ],
    4258: [  # Cat Collars
        ("Breakaway collar", "A cat collar with a safety buckle that releases under pressure if the collar catches on a branch, fence, or other object, preventing strangulation."),
        ("Quick-release buckle", "A clip mechanism on a collar that can be opened with a simple squeeze, allowing fast removal by the owner. Not the same as a breakaway safety release."),
        ("Reflective collar", "A collar with high-visibility reflective strips or material that makes the cat visible to drivers during low-light conditions, an important safety feature for outdoor cats."),
        ("Bell attachment", "A small bell fitted to a cat's collar that jingles during movement, intended to alert birds and wildlife to the cat's approach. Effectiveness is debated among ecologists."),
        ("Elasticated section", "A stretchy panel within a collar that provides some give if the collar catches, intended as a secondary safety feature alongside a breakaway mechanism."),
        ("ID tag", "A small engraved disc attached to the collar displaying the owner's contact details. While microchipping is now compulsory in England, a visible ID tag aids faster reunification."),
    ],
    4139: [  # Dog Training Leads
        ("Long line", "A lead typically five to fifteen metres in length used during recall training, allowing the dog freedom to explore while the handler maintains control at a distance."),
        ("Biothane lead", "A synthetic material that looks and feels like leather but is waterproof, odour-resistant, and easy to clean, making it ideal for training in wet UK conditions."),
        ("Trigger clip", "The most common lead attachment, a spring-loaded metal clip that snaps onto a harness or collar D-ring and can be released by pressing a lever."),
        ("Double-ended lead", "A training lead with clips at both ends and a handle in the middle, allowing attachment to both the front and back clips of a dual-clip harness simultaneously."),
        ("Carabiner clip", "A robust, screw-lock metal fastener used on heavier-duty leads for larger or stronger dogs, providing more secure attachment than a standard trigger clip."),
        ("Drag line", "A lightweight long line allowed to trail on the ground during training, giving the handler a way to step on the lead and regain control without the dog wearing a formal long line."),
    ],
    4049: [  # Puppy Collars & First Harness
        ("Growth allowance", "Extra adjustment range in a collar or harness that accommodates a puppy's rapid growth, reducing the frequency of buying replacement equipment."),
        ("Lightweight hardware", "Small, low-weight buckles and D-rings appropriate for puppies, which do not weigh down the neck or chest and help the puppy accept wearing equipment sooner."),
        ("Desensitisation", "Gradually introducing a puppy to wearing a collar or harness through short, positive sessions with treats and play, building acceptance before attaching a lead."),
        ("First collar sizing", "Measuring a puppy's neck and adding two fingers of room for growth and comfort. Puppies' necks grow rapidly, so rechecking the fit weekly is essential."),
        ("ID disc", "A small metal tag engraved with the owner's name and address, required by UK law to be attached to the collar of any dog in a public place."),
        ("Soft webbing", "Lightweight, flexible nylon or fabric strap material that is gentle on a puppy's skin and fur, preferable to stiff or heavy materials during the early training period."),
    ],
    4042: [  # Dog Leads
        ("Standard lead", "A fixed-length lead, typically 1.2 to 1.8 metres, providing consistent control and a predictable distance between handler and dog during regular walks."),
        ("Retractable lead", "A spring-loaded lead that extends and retracts from a handheld housing, allowing variable distance. Widely available but associated with safety concerns around entanglement and sudden jerks."),
        ("Traffic lead", "A short lead, typically 30 to 60 centimetres, used in busy environments to keep the dog close to the handler. Often features an additional handle on a standard lead."),
        ("Padded handle", "A lead handle wrapped in neoprene, gel, or foam cushioning to prevent blisters and hand fatigue during long walks or when managing a dog that pulls."),
        ("Webbing width", "The width of the flat lead strap, which should be proportional to the dog's size and strength. Wider webbing distributes pull force over a larger area of the hand."),
        ("Carabiner clip", "A heavy-duty, screw-lock metal attachment used on leads for large or strong breeds, offering more security than a standard trigger clip."),
    ],
    4034: [  # No-Pull Harnesses
        ("Front-clip design", "A harness with the lead attachment on the chest, which pivots the dog sideways when it pulls forward, naturally discouraging lunging without pain or punishment."),
        ("Back-clip design", "A harness with the lead ring on the back between the shoulder blades, offering comfort for calm walkers but providing minimal pull redirection."),
        ("Padded chest panel", "A broad, cushioned section on the front of the harness that distributes pressure across the sternum, preventing the thin-strap dig that causes discomfort during pulling."),
        ("Escape prevention", "Design features such as a belly strap or dual-buckle closure that stop a dog from backing out of the harness, critical for fearful or flight-risk dogs."),
        ("Training transition", "The planned process of moving from a no-pull harness to a standard back-clip harness or collar as the dog masters loose-lead walking through positive reinforcement training."),
        ("Strap chafing", "Skin irritation caused by harness straps rubbing repeatedly against the dog's body, most common behind the front legs and preventable through correct sizing and padded materials."),
    ],
    4027: [  # Dog Collars and Harnesses Complete Guide
        ("Flat collar", "A standard collar with a simple buckle or clip closure, suitable for everyday wear, carrying ID tags, and walking dogs that do not pull."),
        ("Martingale collar", "A limited-slip collar that tightens slightly when the dog pulls but stops at a predetermined point, preventing escape without full choking. Popular for sighthound breeds."),
        ("No-pull harness", "A harness designed to reduce pulling by redirecting the dog's momentum through a front attachment point, chest tightening, or both."),
        ("Head halter", "A device worn around the muzzle and behind the ears that controls head direction, reducing pulling by steering the dog rather than physically restraining it."),
        ("Dual-clip harness", "A harness offering both front and back lead attachment points, giving the handler flexibility to switch between control-focused and comfort-focused walking configurations."),
        ("Reflective webbing", "Lead or harness strap material with built-in reflective fibres or stitching that increases visibility in low light, an important safety feature for UK winter walks."),
    ],
}

# ══════════════════════════════════════════════════════════════════════
# COMMON MISTAKES — 4-6 topic-specific mistakes per post
# ══════════════════════════════════════════════════════════════════════

COMMON_MISTAKES = {
    # ── Cat Supplies ──
    696: [
        "Buying a litter tray that is too small — the tray should be at least 1.5 times the length of your cat from nose to tail base.",
        "Choosing a covered litter tray without checking whether your cat is comfortable using it. Many cats prefer open trays with a clear line of sight.",
        "Placing food and water bowls next to the litter tray. Cats instinctively avoid eating near their elimination area.",
        "Purchasing a scratching post that is too short for your cat to stretch fully while using it, which reduces its appeal compared to your sofa.",
        "Using a standard bowl that causes whisker fatigue. Wide, shallow dishes are more comfortable for most cats.",
    ],
    7175: [
        "Feeding complementary food as the sole diet, which leads to nutritional deficiencies over time. Always check the label for 'complete' or 'complementary'.",
        "Switching litter type abruptly, which often causes litter tray avoidance. Transition gradually by mixing old and new litter over seven to ten days.",
        "Assuming all cats respond to catnip. Roughly thirty percent lack the sensitivity gene — try silver vine or valerian as alternatives.",
        "Using human toothpaste for dental care. Fluoride and foaming agents in human toothpaste are toxic to cats. Use only cat-specific enzymatic toothpaste.",
        "Neglecting to register a microchip on an approved database. An unregistered chip cannot reunite a lost cat with its owner.",
    ],

    # ── Cat Toys ──
    5033: [
        "Leaving string toys and wand attachments out after play. Cats can chew and swallow string, causing life-threatening intestinal blockages.",
        "Offering the same toys every day without rotation. Cats habituate quickly and lose interest — rotate toys every few days to maintain novelty.",
        "Ending play sessions abruptly instead of winding down gradually. A sudden stop can leave cats frustrated and hyperactive. End with a treat to simulate a completed hunt.",
        "Using toys that are too small for your cat, creating a choking hazard. Ensure no toy or detachable part can fit entirely inside your cat's mouth.",
    ],
    4409: [
        "Giving kittens adult-sized toys that are too heavy or large for them to manipulate, leading to disinterest rather than engagement.",
        "Using laser pointers as the sole play method for kittens, which can develop into compulsive chasing behaviour if the sequence is never completed with a real catch.",
        "Introducing too many toys at once, which overwhelms kittens and reduces the novelty value of each individual toy.",
        "Playing with hands or feet instead of toys, which teaches kittens that biting skin is acceptable play behaviour — a habit that becomes painful in adult cats.",
    ],
    4408: [
        "Continuing to use toys with exposed stuffing, loose ribbons, or fraying string, which are ingestion hazards that can cause intestinal blockage.",
        "Never inspecting catnip toys for mould, especially after exposure to saliva and moisture. Mouldy catnip toys should be discarded immediately.",
        "Assuming a toy is still safe because it looks intact from the outside. Squeeze and check internal components regularly for broken mechanisms.",
        "Replacing all toys at once, which removes familiar scents and comforts. Stagger replacements so your cat always has some familiar items available.",
    ],
    4407: [
        "Using small components like buttons, beads, or sequins in DIY toys that can be chewed off and swallowed.",
        "Gluing parts with hot glue or superglue that can be peeled off and ingested. Use securely sewn or tied connections instead.",
        "Making toys from materials treated with chemicals, dyes, or finishes that may be toxic if licked or chewed.",
        "Leaving DIY string or ribbon toys unattended. Homemade toys that have not been safety tested should always be supervised play only.",
    ],
    4406: [
        "Relying entirely on automated toys for enrichment. While useful, they cannot replace the bonding and quality that comes from interactive play with the owner.",
        "Not ending interactive sessions with a food reward. Cats need the satisfaction of a 'successful hunt' to feel the play sequence is complete.",
        "Overstimulating a cat during play by ignoring body language signals like tail lashing, flattened ears, or dilated pupils that indicate it is time to stop.",
        "Placing interactive toys in areas where the cat cannot move freely, such as narrow corridors, which restricts natural stalking and chasing behaviour.",
    ],
    4307: [
        "Mounting wall scratchers at the wrong height. The bottom of the scratching surface should be at your cat's shoulder height for comfortable stretching.",
        "Failing to secure wall-mounted scratchers with appropriate fixings. A scratcher that shifts or falls when used will be permanently avoided by the cat.",
        "Placing the scratcher in an isolated room where the cat rarely spends time. Scratchers should be in or near social areas where the cat wants to mark territory.",
        "Removing a well-used scratcher because it looks worn. Cats prefer familiar, scent-marked scratching surfaces and may reject a brand-new replacement.",
    ],
    4300: [
        "Throwing away a cardboard scratcher before it is fully worn. Many models are reversible — flip it over before replacing it.",
        "Placing the scratcher on a slippery floor where it slides during use, which discourages the cat from returning to it.",
        "Not refreshing the catnip on the scratcher periodically. A light sprinkle of new catnip every few days maintains the attraction for responsive cats.",
        "Buying a scratcher that is too small for your cat to stretch out on fully. The scratching surface should be at least as long as your cat's body.",
    ],
    4286: [
        "Choosing a scratching post that wobbles or tips when the cat pushes against it. An unstable post is a safety hazard and will be avoided in favour of your furniture.",
        "Positioning the scratching post in an out-of-the-way corner. Cats prefer to scratch in prominent locations near resting areas and room entrances.",
        "Assuming all cats prefer sisal rope. Some cats strongly prefer cardboard, carpet, or sisal fabric — observe your cat's preference before investing.",
        "Discarding a post that has been heavily scratched. The visible claw marks and deposited scent make a used post more attractive to the cat, not less.",
    ],
    4188: [
        "Assuming your cat is broken if it does not respond to catnip. Roughly thirty percent of cats lack the sensitivity gene — try silver vine or valerian root instead.",
        "Offering catnip continuously rather than occasionally. Over-exposure leads to desensitisation, reducing the response. Once or twice a week is sufficient.",
        "Storing catnip toys in open containers where the active compound evaporates. Sealed bags or airtight containers preserve potency significantly longer.",
        "Giving catnip toys to kittens under six months old and expecting a response. Catnip sensitivity does not develop until around six months of age.",
    ],
    4181: [
        "Using wand toys with elastic string that can snap back and injure the cat's eyes. Non-elastic cord or leather lace is always safer.",
        "Starting a cat on the hardest puzzle feeder level, which leads to frustration and refusal. Begin with the easiest setting and increase difficulty gradually.",
        "Leaving wand toys on the floor after play. The dangling string poses a strangulation and ingestion hazard when unattended.",
        "Playing with a wand in short, quick jerks that do not allow the cat to complete the stalk-chase-pounce sequence. Vary the pace to mimic natural prey movement.",
    ],
    4174: [
        "Spending heavily on one premium toy instead of building a varied collection. Cats tire of individual toys quickly — variety matters more than cost.",
        "Choosing toys based on what looks appealing to humans rather than what mimics prey movement, texture, or sound for the cat.",
        "Ignoring safety ratings and purchasing toys with small detachable parts, feathers that pull off easily, or bells that can be chewed free.",
        "Assuming senior cats do not want to play. Older cats still benefit from gentle, adapted play sessions that accommodate reduced mobility.",
        "Not providing any toys for outdoor cats. Even cats with outdoor access benefit from indoor play sessions for bonding and rainy-day enrichment.",
    ],

    # ── Dog Grooming ──
    5464: [
        "Shaving a double-coated breed to reduce shedding. Shaving removes the insulating undercoat and protective guard hairs, and the coat may never regrow correctly.",
        "Bathing a dog too frequently, which strips natural oils from the coat and skin, leading to dryness, irritation, and increased shedding.",
        "Using human shampoo on dogs. Human products have a different pH level and can disrupt the canine skin barrier, causing itching and flaking.",
        "Neglecting to check between the toes and paw pads during grooming, where grass seeds, mats, and debris commonly accumulate.",
        "Cutting nails too short by rushing. Take small increments and stop when you see the chalky white centre on dark nails to avoid hitting the quick.",
    ],
    4563: [
        "Starting grooming too late in a dog's life. Puppies should be gently introduced to brushing, handling, and nail touching from their first weeks at home.",
        "Brushing only the topcoat and missing the undercoat, which allows mats to form close to the skin where they cause pain and restrict airflow.",
        "Using a single brush type for all coat areas. Different regions of the body often need different tools — a slicker for the body, a comb for ears and legs.",
        "Pulling mats apart with force rather than working through them with a dematting tool or conditioner spray, which causes pain and creates grooming anxiety.",
        "Grooming only when the coat looks visibly dirty or tangled. A regular schedule prevents problems from developing in the first place.",
    ],
    4251: [
        "Using human shampoo on a cat, which has a different skin pH and can cause irritation, dryness, and stripping of natural coat oils.",
        "Bathing a cat unnecessarily. Most cats groom themselves effectively and only need bathing if they have a skin condition, are elderly, or have got into something they cannot clean themselves.",
        "Not rinsing thoroughly after shampooing. Residual product left on the skin causes irritation, flaking, and excessive grooming.",
        "Using cold water for bathing, which causes stress and shivering. Water should be comfortably warm — roughly body temperature.",
    ],
    4244: [
        "Cutting too much nail in one go, risking hitting the quick and causing pain and bleeding that makes the cat fearful of future trimming.",
        "Using dull clippers that crush the nail rather than cutting cleanly, which is painful and can split the nail.",
        "Restraining the cat forcefully during nail trimming, which creates lasting negative associations. Gradual desensitisation with treats is far more effective.",
        "Forgetting the dewclaws, which do not wear down naturally and can curl into the paw pad if left untrimmed.",
        "Trimming all nails in one session if the cat is stressed. It is perfectly acceptable to do one or two paws at a time across several days.",
    ],
    4237: [
        "Using a slicker brush with too much pressure on short-haired cats, which can scratch and irritate the skin rather than removing loose fur.",
        "Brushing against the direction of hair growth, which is uncomfortable and pulls at the follicles.",
        "Not brushing regularly enough for long-haired breeds, allowing mats to form close to the skin where they trap moisture and cause skin problems.",
        "Using only one type of brush for all coat lengths. Different coats need different tools — a bristle brush for short hair, a slicker for medium, a comb for long.",
    ],
    4230: [
        "Buying every grooming tool at once before knowing what your cat's coat actually needs. Start with a basic brush and add tools as you learn your cat's requirements.",
        "Neglecting ear cleaning in fold-eared breeds, where the ear anatomy traps moisture and debris, increasing infection risk.",
        "Using human dental products on cats. Fluoride and foaming agents in human toothpaste are toxic to cats — use only veterinary-approved enzymatic cat toothpaste.",
        "Starting a full grooming routine on an adult cat that has never been groomed. Begin with short, positive sessions and build up gradually.",
    ],
    4078: [
        "Cutting too much nail at once, hitting the quick and causing pain and bleeding that makes the dog fearful of future trimming sessions.",
        "Using dull clippers that crush rather than cut the nail cleanly. Replace or sharpen blades regularly for a smooth cut.",
        "Not having styptic powder readily available before starting. If you cut the quick, you need to stop the bleeding immediately.",
        "Trimming nails only when they are visibly long, rather than maintaining a regular schedule. Frequent small trims keep the quick receded and reduce the risk of over-cutting.",
    ],
    4064: [
        "Using a deshedding tool too aggressively, which can damage the topcoat and irritate the skin. Follow the tool's directions and use gentle, short strokes.",
        "Brushing a dry, tangled coat without first applying a detangling spray, which causes painful pulling and makes the dog dread grooming sessions.",
        "Neglecting to brush areas behind the ears, under the legs, and around the collar where mats form most frequently.",
        "Choosing a brush based on marketing claims rather than matching it to your dog's actual coat type. A slicker brush is not suitable for every dog.",
    ],
    4057: [
        "Buying professional-grade grooming equipment without the skill to use it properly. Thinning shears and clippers can cause uneven cuts or injury without training.",
        "Storing grooming tools in damp conditions, which causes metal components to rust and blades to dull faster.",
        "Not cleaning grooming tools between uses, which can spread skin conditions, parasites, or bacteria from one grooming session to the next.",
        "Skipping ear and dental care in the grooming routine. A complete routine includes more than just brushing — ears, teeth, nails, and paw pads all need attention.",
    ],

    # ── Dog Harnesses ──
    5418: [
        "Buying a harness based on breed alone without measuring your individual dog. Two dogs of the same breed can have very different chest and girth measurements.",
        "Choosing an overhead harness for a dog that is anxious about things passing over its head. A step-in design avoids this trigger entirely.",
        "Leaving a harness on all day. Harnesses should be removed when not walking to prevent chafing, overheating, and matting of the fur beneath the straps.",
        "Assuming a harness alone will stop pulling. It is a management tool, not a training solution — pair it with consistent loose-lead training and rewards.",
    ],
    4414: [
        "Assuming a harness is always better than a collar. Well-trained dogs that walk calmly are perfectly fine on a flat collar, which is also legally required for ID tags in public.",
        "Using a collar on a brachycephalic breed (flat-faced dogs like Pugs or Bulldogs) that is already prone to breathing difficulties. A harness avoids additional pressure on the airway.",
        "Choosing the cheapest collar or harness without checking hardware quality. Weak buckles and thin webbing fail under load when a dog lunges suddenly.",
        "Not using both a collar and a harness together when appropriate. The collar carries the legally required ID tag while the harness provides safe lead attachment.",
    ],
    4413: [
        "Measuring over a thick coat and buying a harness that is too loose once the coat is trimmed or wet. Measure against the body, parting the fur if needed.",
        "Using a rigid tape measure instead of a flexible one, which cannot follow the contours of the dog's chest accurately.",
        "Taking measurements while the dog is sitting or lying down. The dog should be standing naturally on all four legs for accurate results.",
        "Not rechecking the fit regularly. Puppies grow rapidly, adult dogs gain or lose weight seasonally, and straps stretch with use — recheck monthly.",
    ],
    4412: [
        "Relying entirely on the no-pull harness without combining it with training. The harness manages pulling but does not teach the dog to walk on a loose lead.",
        "Using a no-pull harness with the lead clipped to the back ring, which provides no pull-redirection benefit. The lead must be clipped to the front chest ring.",
        "Tightening the harness excessively in an attempt to increase control, which causes discomfort, chafing, and restricted movement.",
        "Choosing a harness with thin straps that dig into the chest when the dog pulls. Padded, wider straps distribute force more comfortably.",
    ],
    4279: [
        "Using a dog harness on a cat, which is typically too heavy and bulky for feline anatomy. Purpose-built cat harnesses are lighter and better shaped.",
        "Taking a harness-wearing cat outdoors without first allowing several indoor practice sessions. Cats need time to adjust to the sensation before facing outdoor stimuli.",
        "Using a retractable lead with a cat harness. The sudden resistance from a locked retractable lead can panic a cat and cause escape attempts. Use a fixed lightweight lead.",
        "Assuming all cats will enjoy harness walking. Some cats find it stressful regardless of training, and their preference should be respected.",
    ],
    4258: [
        "Choosing a collar without a breakaway safety mechanism for a cat. Non-breakaway collars can catch on branches, fences, or furniture and cause strangulation.",
        "Fitting a collar too loosely, allowing the cat to hook a front leg through it and become trapped. Two fingers of space is the correct fit.",
        "Relying on a collar bell to fully protect wildlife. Research shows bells reduce predation on some species but are not completely effective.",
        "Fitting a collar on a kitten and not rechecking the fit weekly as the kitten grows. A too-tight collar can become embedded in the neck skin.",
    ],
    4139: [
        "Using a long training lead without first mastering basic recall in a secure, enclosed area. An untrained dog on a long line in open space creates hazards.",
        "Allowing the long line to wrap around the dog's legs or the handler's hands during recall practice, risking rope burns and entanglement injuries.",
        "Attaching a long line to a collar rather than a harness. The sudden stop at the end of a long line can cause cervical injury if connected to the neck.",
        "Choosing a line that is too heavy for the dog's size, which weighs down the harness and teaches the dog that a pull sensation is always present.",
    ],
    4049: [
        "Buying an adult-sized collar for a puppy to save money. An oversized collar is an escape risk and provides no feedback during early lead training.",
        "Fitting the collar or harness too loosely on a puppy, allowing the puppy to back out of it in a frightening situation — a serious safety risk near roads.",
        "Introducing a collar or harness without any positive association. Pair the first fitting with treats and play to create a pleasant experience.",
        "Forgetting to attach an ID tag to the puppy's collar. UK law requires every dog in a public place to wear a collar with the owner's name and address.",
    ],
    4042: [
        "Using a retractable lead in busy or urban environments where the extended length creates a tripping hazard for pedestrians and reduces control over the dog.",
        "Choosing a lead that is too long for everyday walking. A standard lead of 1.2 to 1.8 metres provides the best balance of freedom and control for pavement walking.",
        "Buying a thin, lightweight lead for a strong-pulling breed. The lead should be proportional to the dog's size and strength to prevent snapping under sudden load.",
        "Wrapping the lead around your hand or wrist for a better grip, which risks hand injury if the dog lunges unexpectedly. Use a lead with a padded handle instead.",
    ],
    4034: [
        "Expecting the no-pull harness to solve pulling without any training effort. The harness is a tool — consistent reward-based training is still essential.",
        "Clipping the lead to the back ring instead of the front ring, which bypasses the pull-redirection feature entirely.",
        "Not checking the fit after the first few walks. Webbing can stretch and buckles can loosen, reducing both comfort and effectiveness.",
        "Removing the harness by pulling it over the dog's head in the wrong direction, which can cause negative associations and make the dog reluctant to be harnessed next time.",
    ],
    4027: [
        "Choosing equipment based on appearance rather than function. A well-fitted, plain harness is always better than an ill-fitting designer one.",
        "Using a choke chain or prong collar for pulling control. These devices cause pain and are opposed by the RSPCA, Dogs Trust, and the BVA. Use a no-pull harness instead.",
        "Not replacing equipment that shows signs of wear. Fraying webbing, stretched elastic, and corroded buckles can fail under load during a sudden lunge.",
        "Assuming one collar or harness type suits every situation. Many owners benefit from having a flat collar for ID, a harness for walks, and a training lead for recall practice.",
    ],
}

# ══════════════════════════════════════════════════════════════════════
# BEGINNER RECOMMENDATIONS — practical starting advice per post
# ══════════════════════════════════════════════════════════════════════

BEGINNER_RECS = {
    # ── Cat Supplies ──
    4335: [
        "Start with nappy sacks for daily scooping — they are inexpensive, widely available, and seal odour effectively for standard council bin collection.",
        "Scoop the tray at least once a day and do a full litter change weekly. This prevents odour buildup and keeps your cat willing to use the tray consistently.",
        "Place a small pedal bin with a lid next to the litter tray for sealed waste storage between outdoor bin collection days.",
        "If odour is a persistent problem despite daily scooping, try switching to a clumping litter, which isolates soiled material more effectively than non-clumping types.",
    ],
    4321: [
        "Begin with a mid-range clumping clay litter. It is the most popular type in the UK because it is effective, widely available, and most cats accept it readily.",
        "If your cat seems reluctant to use a new litter, try switching gradually by mixing twenty-five percent new litter with seventy-five percent old, increasing the ratio over ten days.",
        "Buy a small bag first to test whether your cat accepts the texture and scent before committing to a bulk purchase.",
        "Keep the tray filled to a depth of about five to seven centimetres for clumping litter. Too shallow prevents proper clumping; too deep wastes product.",
    ],
    4314: [
        "Start with a simple, open-top tray. Most cats prefer them to hooded options, and they are easier to clean and monitor.",
        "Choose a tray at least 1.5 times the length of your cat. Kittens grow fast, so buying an adult-sized tray from the start avoids early replacement.",
        "Position the tray in a quiet, accessible spot away from food, water, and the cat's sleeping area. Avoid high-traffic zones.",
        "If you have more than one cat, the general guideline is one tray per cat plus one extra, placed in different locations around the home.",
    ],
    4209: [
        "Consider a self-warming bed first. They use no electricity, require no maintenance, and are safe for unsupervised cats. Only upgrade to electric if your home is particularly cold.",
        "If using an electric heated bed, choose one with a chew-resistant cord and a thermostat that limits the temperature to prevent overheating.",
        "Place the heated bed away from draughts but not directly against a radiator, which could cause overheating. A quiet corner at floor level works well for most cats.",
        "Monitor your cat's use for the first few days. Some cats prefer warmth only while resting, so a self-warming bed near their favourite sleeping spot may be all you need.",
    ],
    4202: [
        "Watch where your cat naturally sleeps before buying a bed. If your cat curls up, a donut or bolster bed is a good match. If it stretches out, choose a flat mat or cushion.",
        "Washability matters more than appearance. Choose a bed with a removable, machine-washable cover — you will need to wash it regularly.",
        "Place the bed in a spot your cat already favours. Cats are unlikely to use a bed placed in a location they do not naturally gravitate toward.",
        "Do not spend heavily on your first cat bed. Cats are unpredictable in their sleeping preferences, so start with a mid-range option and upgrade once you know what your cat prefers.",
    ],
    696: [
        "Prioritise the essentials first: a litter tray, food and water bowls, a carrier, a scratching post, and one or two toys. Add extras gradually as you learn your cat's preferences.",
        "Buy a sturdy carrier before your cat arrives. You will need it for the journey home and for vet visits, and carrier training is easier when started from day one.",
        "Choose a scratching post that is tall enough for your cat to stretch fully. A post that is too short will be ignored in favour of furniture.",
        "Set up a dedicated quiet space with all essentials before bringing your new cat home, so it has a safe room to settle into on arrival.",
    ],
    7175: [
        "Read through the glossary terms that relate to products you are currently shopping for. Understanding what 'complete' versus 'complementary' means on a cat food label prevents common feeding mistakes.",
        "Start with the feeding and litter sections first, as these are the products you will use daily and where correct choices have the biggest impact.",
        "Bookmark this page for reference when reading product descriptions or speaking with your vet about cat care supplies.",
        "If a term relates to a health condition, the glossary provides context for understanding it — but always consult your vet for diagnosis and treatment specific to your cat.",
    ],

    # ── Cat Toys ──
    5033: [
        "Start with one wand toy and one independent toy (like a crinkle ball). This gives you one interactive option and one for solo play without overwhelming your cat with choices.",
        "Schedule two play sessions of ten to fifteen minutes each day. Consistency matters more than session length — cats benefit most from a reliable routine.",
        "Always end play sessions with a treat or small meal to simulate the satisfaction of a successful hunt, which helps your cat wind down and settle.",
        "Watch your cat's body language during play. Flattened ears, a lashing tail, or dilated pupils mean it is time to reduce intensity or stop.",
    ],
    5032: [
        "If your cat seems uninterested in toys, try different types — some cats prefer ground-level prey simulation, while others respond to airborne, bird-like movement.",
        "Rotate toys every three to four days to maintain novelty. Store unused toys in a sealed container to preserve any catnip scent.",
        "Budget for variety rather than one expensive toy. A selection of three to five different toy types, rotated regularly, provides better enrichment than a single premium item.",
        "For cats that ignore traditional toys, try a puzzle feeder with treats. Food motivation can kick-start play interest in reluctant cats.",
    ],
    4409: [
        "For kittens, choose lightweight, small toys they can easily bat and carry. Kittens are developing coordination and need appropriately sized equipment.",
        "Supervise all kitten play and remove string toys, ribbons, and feather attachments after each session — kittens are more likely to chew and swallow parts.",
        "For senior cats, bring the toys to them. Ground-level puzzle feeders and gentle wand play at low height accommodate reduced mobility while still providing enrichment.",
        "If transitioning from kitten to adult toys, do so gradually around twelve months of age as the cat's play preferences and physical capabilities mature.",
    ],
    4408: [
        "Inspect your cat's toys weekly for signs of wear — fraying, loose parts, exposed stuffing, or cracked mechanisms. Replace any toy that shows damage.",
        "Set a calendar reminder to check toys monthly. It is easy to overlook gradual deterioration, and a scheduled check prevents unsafe toys from lingering.",
        "Keep two or three spare toys on hand so you can replace worn items immediately without leaving your cat without enrichment options.",
        "When a favourite toy needs replacing, introduce the new one alongside the old one for a day before removing the worn toy, easing the transition.",
    ],
    4407: [
        "Start with the simplest DIY option: a scrunched ball of plain paper or an empty toilet roll tube with treats inside. These cost nothing and most cats enjoy them.",
        "Use only non-toxic, uncoated materials. Plain cardboard, untreated cotton fabric, and brown paper bags (with handles removed) are all safe choices.",
        "Always supervise play with homemade toys. Unlike commercial products, DIY toys have not been tested for durability or safety under vigorous feline play.",
        "If your cat enjoys a particular DIY toy, make several so you can rotate them and always have a replacement ready.",
    ],
    4406: [
        "Begin with a basic wand toy for interactive play — it is the single most effective cat toy type according to UK welfare organisations.",
        "Add one automated or independent toy for times when you are unavailable. A ball track or motion-activated toy can provide solo enrichment between interactive sessions.",
        "Place interactive toys in open areas where the cat has space to stalk, chase, and pounce. Cramped spaces limit natural hunting behaviour.",
        "If your cat becomes overstimulated during play, pause the session and let the cat calm down. Resume with slower, less intense movements.",
    ],
    4307: [
        "Mount the scratcher at a height where the bottom edge meets your cat's shoulder level when standing. This encourages full-body stretching during scratching.",
        "Use the wall fixings provided by the manufacturer, or heavy-duty plasterboard anchors if the scratcher will be mounted on a hollow wall.",
        "Place the scratcher near areas where your cat already scratches or in high-traffic social zones rather than tucked away in an unused room.",
        "If your cat does not use the scratcher immediately, try rubbing a small amount of catnip onto the surface or placing a few treats at its base.",
    ],
    4300: [
        "Start with an affordable corrugated cardboard scratcher to discover whether your cat prefers flat, angled, or curved scratching surfaces before investing in a permanent option.",
        "Place the scratcher on a non-slip surface or use the anti-slip pads often included with the product. A sliding scratcher discourages use.",
        "Sprinkle a small amount of catnip on the scratcher to attract your cat initially. Most cardboard scratchers include a sachet for this purpose.",
        "When the surface becomes worn, flip the scratcher over if it is a reversible design — you will get roughly double the use before needing a replacement.",
    ],
    4286: [
        "Choose a scratching post that is tall enough for your cat to stretch fully — at minimum, the cat's body length from nose to tail base.",
        "Stability is non-negotiable. A post that wobbles will be rejected by your cat and may topple over. Choose a heavy base or wall-mount option.",
        "Position the post near your cat's favourite resting spot. Cats often stretch and scratch immediately after waking up.",
        "If your cat scratches furniture despite having a post, try different materials — sisal rope, sisal fabric, cardboard, or carpet — to discover which texture your cat prefers.",
    ],
    4188: [
        "Buy a small, inexpensive catnip toy first to confirm whether your cat responds to catnip before investing in multiple products.",
        "If your cat shows no reaction to catnip, try a silver vine stick or a valerian root toy as alternatives that work for many non-responders.",
        "Use catnip toys once or twice a week rather than daily. Occasional exposure keeps the response strong; constant exposure leads to desensitisation.",
        "Store catnip toys in an airtight container or zip-lock bag between uses. Catnip loses potency quickly when exposed to air and light.",
    ],
    4181: [
        "Start with a basic wand toy with a feather or fabric attachment. Move it along the floor in short, erratic movements to mimic mouse-like prey behaviour.",
        "For puzzle feeders, begin with the easiest level — a transparent container where the cat can see and easily access the food. Increase difficulty gradually as confidence builds.",
        "After every wand play session, store the wand and all string attachments in a closed cupboard. Dangling string left unattended is a serious safety hazard.",
        "Combine both types: use the wand toy for high-energy play and the puzzle feeder for calm, mental enrichment. Together they satisfy different needs.",
    ],
    4174: [
        "Begin with three toy types: one wand toy for interactive play, one kick toy for independent play, and one puzzle feeder for mental stimulation.",
        "Set a daily play routine of two sessions, ten to fifteen minutes each. Morning and evening sessions align well with a cat's natural activity peaks.",
        "Rotate toys every three to four days. Put unused toys in a sealed bag and bring out stored ones to maintain novelty without needing to buy new toys constantly.",
        "Watch your cat's preferences over the first week. Some cats are chasers, others are ambushers, and some prefer puzzles — let your cat's behaviour guide future purchases.",
    ],

    # ── Dog Grooming ──
    5464: [
        "If you are new to grooming terminology, read through the glossary terms that match your dog's coat type first — double coat, wire coat, or single coat terms will be most relevant.",
        "Start with the basic tools: a suitable brush for your dog's coat type, a nail clipper or grinder, and a veterinary-approved ear cleaner. Add tools as your confidence grows.",
        "If any term relates to a procedure you have not performed before, such as hand stripping or nail grinding, ask your groomer to demonstrate it before attempting it at home.",
        "Bookmark this page as a reference. When your groomer or vet uses an unfamiliar term, you can look it up here for a plain-language explanation.",
    ],
    4563: [
        "Start by handling your dog's paws, ears, and muzzle gently each day with treats, even before you introduce any tools. This builds trust and reduces grooming anxiety.",
        "Buy a slicker brush as your first tool — it works on the widest range of coat types and handles everyday brushing well.",
        "Keep initial grooming sessions short — five minutes is plenty for a puppy or a dog new to grooming. Gradually increase the time as the dog's comfort grows.",
        "Brush in the direction of hair growth using gentle, short strokes. Let the brush do the work rather than pressing hard against the skin.",
    ],
    4251: [
        "Most cats do not need regular baths. Only bathe your cat if it has a skin condition, is elderly and struggling to self-groom, or has got into something it cannot clean off.",
        "Use only a shampoo specifically formulated for cats. Human shampoo and dog shampoo both have the wrong pH for feline skin.",
        "If you must bathe your cat, prepare everything in advance — towels, shampoo, a non-slip mat, and lukewarm water — to keep the experience as brief and calm as possible.",
        "For quick cleaning between baths, a waterless cat shampoo or grooming wipe is less stressful than a full bath and sufficient for most spot-cleaning needs.",
    ],
    4244: [
        "If you have never trimmed cat nails before, ask your vet or vet nurse to demonstrate the technique during a routine check-up.",
        "Use sharp, purpose-built cat nail clippers — not human nail clippers — for a clean, comfortable cut.",
        "Trim one or two nails at a time if your cat is anxious. Spread the full trim across several days if needed, rewarding each session with a treat.",
        "Keep styptic powder within reach before you begin. If you accidentally cut the quick, a dab of styptic powder stops the bleeding within seconds.",
    ],
    4237: [
        "Match the brush to your cat's coat length: a bristle brush for short hair, a slicker brush for medium coats, and a wide-toothed comb followed by a slicker for long hair.",
        "Brush your short-haired cat once a week and your long-haired cat at least every other day. Regular brushing prevents mats, reduces shedding, and distributes natural coat oils.",
        "If your cat dislikes being brushed, try a grooming glove first. The petting motion is less intimidating than a brush for cats that are new to grooming.",
        "Always brush before bathing (if a bath is needed). Wet mats tighten and become much harder and more painful to remove.",
    ],
    4230: [
        "Start with the basics: a brush suited to your cat's coat type, a pair of cat nail clippers, and veterinary-approved ear cleaner. You do not need every tool on day one.",
        "Introduce each tool individually over several days, pairing it with treats, so your cat builds positive associations before you use it for actual grooming.",
        "Establish a brief weekly grooming routine — five to ten minutes of brushing and a quick ear check. Add nail trimming and dental care as your cat becomes comfortable.",
        "Keep all grooming supplies together in one clean, dry container so they are ready when you need them and stay in good condition between uses.",
    ],
    4078: [
        "If you have never trimmed a dog's nails, ask your vet or groomer to show you the correct technique and how to identify the quick before attempting it at home.",
        "Start with a nail grinder if your dog is nervous. The gradual filing process is less abrupt than clipping and gives you more control over how much nail you remove.",
        "Trim a tiny amount at a time — just the tip — especially on dark nails where the quick is not visible. Frequent small trims are safer than infrequent big cuts.",
        "Have styptic powder, treats, and good lighting ready before you begin. Preparation makes the process calmer for both you and your dog.",
    ],
    4071: [
        "Start with a general-purpose, soap-free dog shampoo. It covers the majority of bathing needs without risking irritation from unnecessary active ingredients.",
        "Only bathe your dog when it genuinely needs it — every four to eight weeks for most breeds. Over-bathing strips natural coat oils and causes skin problems.",
        "If your dog has a skin condition, consult your vet before choosing a medicated shampoo. Using the wrong product can worsen the condition.",
        "Rinse thoroughly after shampooing. Residual product left on the skin is the most common cause of post-bath itching and flaking.",
    ],
    4064: [
        "Identify your dog's coat type first — short and smooth, double-layered, long and silky, or wire-haired — then choose a brush designed specifically for that coat.",
        "Brush your dog at least once a week regardless of coat length. Even short-coated dogs benefit from regular brushing to remove dead hair and distribute natural oils.",
        "Start with gentle, short strokes and work in the direction of hair growth. If you encounter a tangle, hold the hair above the tangle and work the brush through from the tip upward.",
        "Pay extra attention to behind the ears, under the legs, and around the collar where mats form most frequently.",
    ],
    4057: [
        "Start with a basic grooming kit: a breed-appropriate brush, nail clippers or a grinder, ear cleaner, and a gentle shampoo. You can add specialist tools later as needed.",
        "Clean your grooming tools after every session. Remove hair from brushes, wipe clipper blades, and wash combs in warm soapy water to maintain hygiene and tool lifespan.",
        "Store metal tools in a dry location to prevent rust. A simple toolbox or zip-up case keeps everything organised and protected.",
        "Book a professional grooming session once to observe technique before replicating it at home. Many groomers are happy to explain what they are doing as they work.",
    ],

    # ── Dog Harnesses ──
    5418: [
        "Measure your dog's girth (around the widest part of the ribcage behind the front legs) with a flexible tape measure before looking at any harness.",
        "For a first harness, a simple Y-frame or H-frame design with adjustable straps is the most versatile choice for most dogs.",
        "Let your dog wear the new harness indoors with treats for a few short sessions before attaching a lead and heading outside.",
        "Check the fit using the two-finger rule: you should be able to fit two fingers under every strap without difficulty.",
    ],
    4414: [
        "If your dog pulls on walks, start with a front-clip harness rather than relying on a collar, which concentrates all the pressure on the neck.",
        "Keep a flat collar with an ID tag on your dog at all times in public — it is a UK legal requirement. Attach the lead to the harness for walking control.",
        "For brachycephalic (flat-faced) breeds, always use a harness rather than a collar to avoid adding pressure to already compromised airways.",
        "Try both a collar and a harness to see which your dog is most comfortable with on walks. Many owners use a collar for casual outings and a harness for longer or busier walks.",
    ],
    4413: [
        "Use a flexible tape measure, not a rigid one, and measure your dog while it is standing naturally on all four legs.",
        "Take the girth measurement first — it is the most important dimension and the one most harness sizing charts are based on.",
        "After fitting a new harness, check the two-finger rule at every strap and watch for rubbing marks behind the front legs during the first few walks.",
        "Recheck measurements monthly for puppies and seasonally for adult dogs. Weight changes and coat thickness affect harness fit.",
    ],
    4412: [
        "Clip the lead to the front (chest) ring, not the back ring, to activate the pull-redirection feature. This is the single most important step for effectiveness.",
        "Combine the harness with reward-based training: every time your dog walks with a loose lead, mark the behaviour with a treat or verbal praise.",
        "Start in a quiet, low-distraction environment. Once your dog walks consistently on a loose lead there, gradually introduce busier settings.",
        "Check for chafing behind the front legs after the first week. If you see redness, adjust the fit or switch to a harness with padded straps.",
    ],
    4411: [
        "Measure your dog before purchasing. Use a flexible tape measure to get the girth (chest circumference behind the front legs) and compare against the manufacturer's size chart.",
        "A front-clip harness is the best starting point for dogs that pull. It redirects forward momentum without causing discomfort.",
        "Introduce the harness gradually using treats and positive reinforcement. Forcing a harness onto a reluctant dog creates lasting negative associations.",
        "Remove the harness after each walk. Wearing it constantly can cause matting, chafing, and overheating, especially in thick-coated breeds.",
    ],
    4279: [
        "Choose a lightweight, cat-specific harness — not a small dog harness. Cat harnesses are designed for feline anatomy and are lighter and more flexible.",
        "Let your cat wear the harness indoors for five to ten minutes at a time, with treats and play, for at least a week before attempting outdoor walks.",
        "Use a fixed-length lead of 1.5 to 2 metres rather than a retractable lead. Retractable leads can jerk and panic a harnessed cat.",
        "Accept that harness walking is not for every cat. If your cat remains distressed after gradual indoor training, respect its preference and provide enrichment in other ways.",
    ],
    4258: [
        "Always choose a collar with a breakaway safety mechanism for cats. This is the single most important safety feature, preventing strangulation if the collar catches on something.",
        "Fit the collar so you can slide two fingers underneath it. Check the fit weekly, especially for growing kittens.",
        "Attach an ID tag with your name, address, and phone number. Even though microchipping is now compulsory in England, a visible tag speeds up reunification if your cat is found.",
        "If your cat has never worn a collar, introduce it gradually with treats and short wearing periods before leaving it on full-time.",
    ],
    4139: [
        "Start recall training in a secure, enclosed area before using a long line in an open space. The line is a safety backup, not a teaching tool by itself.",
        "Attach the long line to a harness, never a collar. The sudden stop when a dog reaches the end of a long line can injure the neck if connected to a collar.",
        "Choose a lightweight line — five metres is a good starting length. Longer lines are harder to manage and create more entanglement risk for beginners.",
        "Let the line trail on the ground during training rather than holding it taut. This teaches the dog to make good decisions independently while you maintain a safety net.",
    ],
    4049: [
        "Start with a lightweight, adjustable collar that has room for growth, and a simple step-in or overhead harness for lead walking.",
        "Introduce the collar and harness separately, each with plenty of treats and praise. Do not rush — a few minutes of positive association each day builds lasting comfort.",
        "Attach an ID tag to the collar immediately. UK law requires it whenever the puppy is in a public place.",
        "Check the fit every week as your puppy grows. Puppy necks and chests change rapidly, and a too-tight collar or harness can cause discomfort or injury.",
    ],
    4042: [
        "Start with a standard fixed-length lead of 1.5 metres for everyday walking. It provides the best balance of freedom and control for pavement walks.",
        "Avoid retractable leads until your dog has reliable recall and lead manners. The variable length makes consistent training difficult and creates safety risks in busy areas.",
        "Choose a lead with a padded handle if your dog is still learning lead manners. It prevents blisters and hand fatigue during training walks.",
        "Match the lead width and clip strength to your dog's size. A small-breed lead will not withstand a sudden lunge from a large dog.",
    ],
    4034: [
        "Start with a front-clip harness and a standard lead. Clip the lead to the chest D-ring, not the back, to activate the pull-redirection effect.",
        "Combine the harness with reward-based training from day one. Every moment of loose-lead walking should be marked and rewarded with a treat or praise.",
        "Check for chafing behind the front legs and across the sternum after the first few walks. If redness appears, adjust the straps or switch to a padded model.",
        "Plan to transition to a back-clip harness or collar once your dog consistently walks on a loose lead. The no-pull harness is a training aid, not a permanent solution.",
    ],
    4027: [
        "Start with two items: a flat collar with an ID tag for legal compliance, and a well-fitted harness for lead walking. This covers everyday needs.",
        "Measure your dog's neck and girth before shopping. Online sizing charts are only useful if you have accurate measurements.",
        "For pulling dogs, begin with a front-clip harness. For calm walkers, a simple back-clip harness or flat collar is sufficient.",
        "Replace any equipment that shows fraying, stretched webbing, or corroded buckles. Compromised hardware can fail under sudden load.",
    ],
}


# ══════════════════════════════════════════════════════════════════════
# BLOCK BUILDERS
# ══════════════════════════════════════════════════════════════════════

def build_key_terms_block(post_id):
    """Build Key Terms block (grey bg #f8fafc, border #e2e8f0)."""
    terms = KEY_TERMS.get(post_id, [])
    if not terms:
        return None

    li_items = "\n".join(
        f"<li><strong>{t}</strong> – {d}</li>"
        for t, d in terms
    )

    return f"""<!-- wp:group {{"style":{{"color":{{"background":"#f8fafc"}},"border":{{"radius":"6px","width":"1px","color":"#e2e8f0"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:6px;background-color:#f8fafc;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">Key Terms</h4><!-- /wp:heading -->
<!-- wp:list --><ul class="wp-block-list">
{li_items}
</ul><!-- /wp:list -->
</div><!-- /wp:group -->"""


def build_common_mistakes_block(post_id):
    """Build Common Mistakes block (red bg #fef2f2, border #fecaca)."""
    mistakes = COMMON_MISTAKES.get(post_id, [])
    if not mistakes:
        return None

    li_items = "\n".join(f"<li>{m}</li>" for m in mistakes)

    return f"""<!-- wp:group {{"style":{{"color":{{"background":"#fef2f2"}},"border":{{"radius":"6px","width":"1px","color":"#fecaca"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fecaca;border-width:1px;border-radius:6px;background-color:#fef2f2;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">Common Mistakes to Avoid</h4><!-- /wp:heading -->
<!-- wp:list --><ul class="wp-block-list">
{li_items}
</ul><!-- /wp:list -->
</div><!-- /wp:group -->"""


def build_beginner_recs_block(post_id):
    """Build Beginner Recommendations block (blue bg #eff6ff, border #bfdbfe)."""
    recs = BEGINNER_RECS.get(post_id, [])
    if not recs:
        return None

    li_items = "\n".join(f"<li>{r}</li>" for r in recs)

    return f"""<!-- wp:group {{"style":{{"color":{{"background":"#eff6ff"}},"border":{{"radius":"6px","width":"1px","color":"#bfdbfe"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#bfdbfe;border-width:1px;border-radius:6px;background-color:#eff6ff;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">Beginner Recommendations</h4><!-- /wp:heading -->
<!-- wp:list --><ul class="wp-block-list">
{li_items}
</ul><!-- /wp:list -->
</div><!-- /wp:group -->"""


# ══════════════════════════════════════════════════════════════════════
# API HELPERS
# ══════════════════════════════════════════════════════════════════════

def api_get(post_id):
    """Fetch post content via WP REST API."""
    url = f"{BASE}/posts/{post_id}?context=edit"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout)


def api_update(post_id, new_content):
    """Update post content via WP REST API."""
    payload = {"content": new_content}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f)
        tmpfile = f.name

    url = f"{BASE}/posts/{post_id}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH,
         "-d", f"@{tmpfile}",
         "-H", "Content-Type: application/json",
         "-X", "POST", url],
        capture_output=True, text=True, timeout=60
    )
    os.unlink(tmpfile)

    try:
        resp = json.loads(result.stdout)
        if "id" in resp:
            return True, resp["id"]
        else:
            return False, resp.get("message", result.stdout[:300])
    except json.JSONDecodeError:
        return False, result.stdout[:300]


# ══════════════════════════════════════════════════════════════════════
# CONTENT DETECTION & INSERTION
# ══════════════════════════════════════════════════════════════════════

def has_key_terms(content):
    return "Key Terms</h4>" in content or ">Key Terms<" in content


def has_common_mistakes(content):
    return "Common Mistakes" in content


def has_beginner_recs(content):
    # Check for our specific block or close variations
    return "Beginner Recommendation" in content or "Beginner recommendation" in content


def find_editorial_footer_pos(content):
    """Find the position right before the editorial standards footer block."""
    # Pattern 1: Gutenberg group block containing "Our Editorial Standards"
    # We need to find the outermost wp:group that wraps the editorial standards
    idx = content.find("Our Editorial Standards")
    if idx < 0:
        return -1

    # Walk backwards from "Our Editorial Standards" to find the start of containing block
    search_area = content[:idx]

    # Look for the nearest wp:group opening before this text
    # We need to find the one that is the actual container
    last_group = search_area.rfind("<!-- wp:group")
    if last_group >= 0:
        return last_group

    return -1


def insert_blocks_before_footer(content, blocks_html):
    """Insert blocks just before the editorial standards footer."""
    pos = find_editorial_footer_pos(content)
    if pos >= 0:
        return content[:pos] + blocks_html + "\n\n" + content[pos:]
    else:
        # Fallback: append at end
        return content + "\n\n" + blocks_html


# ══════════════════════════════════════════════════════════════════════
# MAIN PROCESSING
# ══════════════════════════════════════════════════════════════════════

def process_post(post_id, cluster):
    """Process a single post, adding missing Key Terms, Common Mistakes, Beginner Recs."""
    print(f"  Fetching post {post_id}...")
    data = api_get(post_id)

    if "id" not in data:
        print(f"    ERROR: Could not fetch post {post_id}: {str(data)[:200]}")
        return {
            "id": post_id, "title": "FETCH_ERROR", "cluster": cluster,
            "glossary_added": False, "common_mistakes_added": False,
            "beginner_recs_added": False, "status": "fetch_error"
        }

    title = data.get("title", {}).get("raw", "Unknown")
    content = data.get("content", {}).get("raw", "")
    print(f"    Title: {title[:80]}")
    print(f"    Content length: {len(content)} chars")

    # Check what's already present
    needs_key_terms = not has_key_terms(content)
    needs_common_mistakes = not has_common_mistakes(content)
    needs_beginner_recs = not has_beginner_recs(content)

    # Check if we have data for this post
    kt_block = build_key_terms_block(post_id) if needs_key_terms else None
    cm_block = build_common_mistakes_block(post_id) if needs_common_mistakes else None
    br_block = build_beginner_recs_block(post_id) if needs_beginner_recs else None

    # Track what we're actually adding
    adding_kt = kt_block is not None
    adding_cm = cm_block is not None
    adding_br = br_block is not None

    if not adding_kt and not adding_cm and not adding_br:
        reason = []
        if not needs_key_terms:
            reason.append("key_terms_exists")
        else:
            reason.append("no_kt_data")
        if not needs_common_mistakes:
            reason.append("common_mistakes_exists")
        else:
            reason.append("no_cm_data")
        if not needs_beginner_recs:
            reason.append("beginner_recs_exists")
        else:
            reason.append("no_br_data")
        print(f"    SKIP: nothing to add ({', '.join(reason)})")
        return {
            "id": post_id, "title": title, "cluster": cluster,
            "glossary_added": False, "common_mistakes_added": False,
            "beginner_recs_added": False, "status": "skipped"
        }

    # Build combined insertion block
    blocks = []
    if adding_kt:
        blocks.append(kt_block)
        print(f"    + Adding Key Terms ({len(KEY_TERMS.get(post_id, []))} terms)")
    if adding_cm:
        blocks.append(cm_block)
        print(f"    + Adding Common Mistakes ({len(COMMON_MISTAKES.get(post_id, []))} items)")
    if adding_br:
        blocks.append(br_block)
        print(f"    + Adding Beginner Recommendations ({len(BEGINNER_RECS.get(post_id, []))} items)")

    combined = "\n\n".join(blocks)

    # Insert before editorial footer
    new_content = insert_blocks_before_footer(content, combined)
    print(f"    Updated content length: {len(new_content)} chars (delta: +{len(new_content)-len(content)})")

    # Push to WP
    success, info = api_update(post_id, new_content)
    if success:
        print(f"    SUCCESS: Updated post {info}")
        return {
            "id": post_id, "title": title, "cluster": cluster,
            "glossary_added": adding_kt, "common_mistakes_added": adding_cm,
            "beginner_recs_added": adding_br, "status": "updated"
        }
    else:
        print(f"    FAILED: {info}")
        return {
            "id": post_id, "title": title, "cluster": cluster,
            "glossary_added": False, "common_mistakes_added": False,
            "beginner_recs_added": False, "status": f"update_error: {str(info)[:100]}"
        }


def main():
    print("=" * 70)
    print("Phase 10AR + 10AS: Glossary Saturation & Decision Support")
    print("Clusters: Cat Supplies, Cat Toys, Dog Grooming, Dog Harnesses")
    print("=" * 70)

    results = []
    total_posts = sum(len(ids) for ids in CLUSTERS.values())
    processed = 0
    updated_count = 0
    skipped_count = 0
    error_count = 0

    for cluster, post_ids in CLUSTERS.items():
        print(f"\n{'─'*60}")
        print(f"CLUSTER: {cluster} ({len(post_ids)} posts)")
        print(f"{'─'*60}")

        for post_id in post_ids:
            processed += 1
            print(f"\n[{processed}/{total_posts}] Post {post_id} ({cluster})")

            try:
                result = process_post(post_id, cluster)
                results.append(result)

                if result["status"] == "updated":
                    updated_count += 1
                elif result["status"] == "skipped":
                    skipped_count += 1
                else:
                    error_count += 1
            except Exception as e:
                print(f"    EXCEPTION: {e}")
                results.append({
                    "id": post_id, "title": "EXCEPTION", "cluster": cluster,
                    "glossary_added": False, "common_mistakes_added": False,
                    "beginner_recs_added": False, "status": f"exception: {str(e)[:100]}"
                })
                error_count += 1

            time.sleep(DELAY)

    # Write CSV log
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "title", "cluster", "glossary_added",
            "common_mistakes_added", "beginner_recs_added", "status"
        ])
        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 70)
    print("PHASE 10AR + 10AS COMPLETE")
    print(f"  Total posts: {total_posts}")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    print(f"  Log: {LOG_FILE}")
    print("=" * 70)

    # Summary by cluster
    for cluster in CLUSTERS:
        cluster_results = [r for r in results if r["cluster"] == cluster]
        kt_added = sum(1 for r in cluster_results if r["glossary_added"])
        cm_added = sum(1 for r in cluster_results if r["common_mistakes_added"])
        br_added = sum(1 for r in cluster_results if r["beginner_recs_added"])
        print(f"\n  {cluster}:")
        print(f"    Key Terms added: {kt_added}/{len(cluster_results)}")
        print(f"    Common Mistakes added: {cm_added}/{len(cluster_results)}")
        print(f"    Beginner Recs added: {br_added}/{len(cluster_results)}")


if __name__ == "__main__":
    main()
