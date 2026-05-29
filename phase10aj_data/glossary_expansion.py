#!/usr/bin/env python3
"""
Phase 10AJ-H: GLOSSARY DOMINANCE WAVE 2
Expands 7 existing glossary pages with 10-15 new advanced terms each.
"""

import subprocess
import json
import tempfile
import csv
import re
import os

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
API = "https://pethubonline.com/wp-json/wp/v2/posts"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10aj_data"
LOG_FILE = os.path.join(DATA_DIR, "glossary_expansion_log.csv")

# ─── NEW TERMS FOR EACH GLOSSARY ───

GLOSSARY_TERMS = {
    7167: {
        # Indoor Cat Terminology
        "title": "Indoor Cat Terminology",
        "terms": [
            ("RSPCA Assured", "RSPCA Assured is a welfare certification scheme primarily applied to farm animals, but indoor cat owners often encounter the label on cat food products. Food carrying this label meets higher welfare standards for the animals used as ingredients. When shopping for cat food in the UK, this certification provides an additional layer of confidence that the sourcing meets recognised ethical standards."),
            ("Feline Cognitive Dysfunction (FCD)", "Feline cognitive dysfunction is a progressive neurological condition affecting older cats, similar to dementia in humans. Indoor cats with FCD may show increased vocalisation at night, disorientation in familiar rooms, or changes in litter tray habits. If your senior indoor cat suddenly seems confused in their own home, a veterinary assessment for FCD is worthwhile. The condition cannot be cured but can be managed with environmental adjustments and, in some cases, medication."),
            ("Resource Guarding", "Resource guarding occurs when a cat becomes defensive over food, litter trays, resting spots, or attention from their owner. In indoor multi-cat households, this behaviour is particularly common due to the inability to establish separate territories naturally. Providing multiple feeding stations, litter trays, and resting areas helps reduce resource-related conflict."),
            ("Enrichment Hierarchy", "An enrichment hierarchy is a structured approach to providing mental and physical stimulation for indoor cats, prioritising the most impactful activities first. At the base are essential provisions like scratching surfaces and hiding spots. Mid-level enrichment includes puzzle feeders and rotating toys. At the top are interactive play sessions with owners, which Cats Protection identifies as the single most beneficial enrichment activity for indoor cats."),
            ("Whisker Fatigue", "Whisker fatigue, sometimes called whisker stress, occurs when a cat's sensitive whiskers are repeatedly overstimulated by narrow food or water bowls. Indoor cats eating exclusively from bowls may show reluctance to eat, pawing food out of the dish, or apparent fussiness. Switching to a wide, shallow bowl or a whisker-friendly feeding plate often resolves the issue immediately."),
            ("Feline Idiopathic Cystitis (FIC)", "Feline idiopathic cystitis is a stress-related bladder condition that is significantly more common in indoor cats. Symptoms include frequent urination, blood in urine, and urinating outside the litter tray. Environmental stress is the primary trigger, and management typically involves increasing water intake, reducing household stressors, and providing more environmental enrichment. It is one of the most common reasons indoor cats visit the vet."),
            ("Thermal Comfort Zone", "A cat's thermal comfort zone is the ambient temperature range in which they can maintain body temperature without expending extra energy, typically between twenty and twenty-five degrees Celsius. Indoor cats cannot seek sun or shade as freely as outdoor cats, so owners need to ensure their home provides warm spots in winter and cool retreats in summer. Radiator beds and cooling mats help bridge this gap."),
            ("Clicker Training", "Clicker training is a positive reinforcement technique that uses a small handheld device producing a consistent clicking sound to mark desired behaviour, followed by a food reward. It is highly effective for indoor cats and can be used to teach recall, tricks, and even to manage behavioural issues. The RSPCA endorses clicker training as a humane and effective method for cat training."),
            ("Substrate Preference", "Substrate preference refers to a cat's individual preference for the type of material they choose to eliminate on. Indoor cats develop strong preferences for particular litter textures, and switching litter type abruptly is a common cause of litter tray avoidance. If you need to change litter, a gradual transition mixing the old and new types over seven to ten days is recommended."),
            ("Compulsive Overgrooming", "Compulsive overgrooming, also called psychogenic alopecia, is a stress-related behaviour where a cat excessively licks or pulls out their own fur, resulting in bald patches. It is more prevalent in indoor cats due to environmental stress and understimulation. While it can also indicate allergies or pain, a veterinary assessment is essential to rule out physical causes before addressing it as a behavioural issue."),
            ("Window Bird Feeder Enrichment", "Placing a bird feeder outside a window that your indoor cat can observe from provides passive visual enrichment. Watching bird activity stimulates a cat's hunting instincts without the welfare concerns of actual predation. This is a low-cost, high-impact enrichment strategy recommended by International Cat Care, particularly for cats in flats without garden access."),
            ("VAT on Pet Supplies", "In the UK, most pet food and supplies are subject to the standard twenty percent VAT rate. Unlike human food, pet food is not zero-rated for VAT purposes. This is a common source of confusion for new pet owners budgeting for ongoing costs. Veterinary fees are also subject to standard-rate VAT, which can significantly increase the cost of treatment."),
        ]
    },
    7169: {
        # Puppy Care Glossary
        "title": "Puppy Care Glossary",
        "terms": [
            ("KC Registered", "KC registered means a puppy has been registered with The Kennel Club, the UK's largest dog breed registry. Registration confirms the puppy's breed pedigree and parentage, but it is not a guarantee of health or quality of breeding. Prospective puppy buyers should look for KC registration alongside health test certificates for breed-specific conditions. The Kennel Club also runs the Assured Breeder Scheme, which sets higher standards."),
            ("Socialisation Window", "The primary socialisation window for puppies runs from approximately three to fourteen weeks of age. During this period, positive exposure to different people, animals, environments, sounds, and surfaces has the greatest lasting impact on temperament. Missing this window does not make socialisation impossible, but it becomes significantly more challenging. The Dogs Trust and Kennel Club both provide detailed socialisation checklists for new owners."),
            ("Puppy Contract", "The Puppy Contract is a free document developed by the RSPCA and the Animal Welfare Foundation that formalises the sale agreement between breeder and buyer. It includes health information, vaccination records, and details of the puppy's early environment. Using the Puppy Contract is strongly recommended by UK animal welfare organisations and provides a framework for holding breeders accountable."),
            ("Maternal Immunity", "Maternal immunity refers to the antibodies a puppy receives from its mother through colostrum in the first hours of life. These antibodies provide temporary protection against diseases but gradually decline over the first few weeks. This declining immunity is why puppies require a course of vaccinations rather than a single jab, as the vaccines need to take effect as maternal protection wanes."),
            ("Bite Inhibition", "Bite inhibition is a learned behaviour where a puppy discovers how to moderate the force of its bite during play. Puppies that are separated from their litter too early often have poor bite inhibition because they missed the critical feedback from littermates. Teaching bite inhibition is one of the most important early training tasks, and the RSPCA recommends using the yelp-and-withdraw technique during play."),
            ("Crate Training", "Crate training involves teaching a puppy to associate a crate or enclosed space with safety and relaxation rather than punishment. When done correctly, the crate becomes a voluntary den where the puppy can rest undisturbed. The Dogs Trust recommends crate training as a positive tool for house training, preventing destructive behaviour, and providing travel safety. A crate should never be used as punishment or for prolonged confinement."),
            ("Fear Imprint Period", "Puppies go through fear imprint periods at approximately eight to eleven weeks and again at six to fourteen months. Negative experiences during these windows can have disproportionately lasting effects on behaviour. Understanding these periods helps owners avoid overwhelming introductions and manage potentially frightening situations such as fireworks, which are a significant issue for UK dog owners every autumn."),
            ("Lucy's Law", "Lucy's Law, which came into effect in England in April 2020, bans the commercial third-party sale of puppies and kittens. Under this law, anyone wanting to buy a puppy must deal directly with the breeder or adopt from a rescue centre. The law is named after Lucy, a Cavalier King Charles Spaniel rescued from a puppy farm. It is designed to reduce demand for puppy farming and improve welfare standards."),
            ("Teething Timeline", "Puppy teething typically begins at three to four weeks when deciduous (baby) teeth emerge, and the transition to adult teeth occurs between three and seven months of age. During the adult teething phase, puppies experience significant discomfort and increased chewing behaviour. Providing appropriate teething toys and frozen cloths for soothing gums is essential. If baby teeth have not fallen out by seven months, veterinary intervention may be needed."),
            ("Hypoallergenic", "The term hypoallergenic, when applied to dog breeds, is widely misunderstood. No dog breed is truly non-allergenic. Breeds marketed as hypoallergenic, such as Poodles and Bichon Frises, typically produce less dander or shed less, which can reduce allergic reactions in some people. However, allergies are triggered by proteins in saliva, urine, and dander, not just fur. Prospective owners with allergies should spend time with the specific breed before committing."),
            ("Puppy Farming", "Puppy farming refers to the large-scale commercial breeding of dogs, often in poor welfare conditions, with profit prioritised over animal health. Puppies from farms frequently arrive with health and behavioural problems. The RSPCA estimates that hundreds of thousands of puppies are still bred in substandard conditions annually across the UK. Signs of a puppy farm include being unable to see the mother, multiple breeds available simultaneously, and puppies offered for collection at motorway services or car parks."),
            ("Incomplete Vaccination", "A puppy with incomplete vaccination has not yet received all the jabs in its primary vaccination course, which typically consists of two injections given two to four weeks apart. Until the course is complete, the puppy is not fully protected against diseases like parvovirus and distemper. Veterinary guidance is to avoid contact with unvaccinated dogs and public spaces until two weeks after the final vaccination."),
        ]
    },
    7170: {
        # Dog Health Terminology
        "title": "Dog Health Terminology",
        "terms": [
            ("PDSA PAW Report", "The PDSA PAW (People's Animal Wellbeing) Report is an annual survey published by the PDSA assessing the state of pet welfare across the UK. It provides data on vaccination rates, obesity levels, microchipping compliance, and common health issues. Dog owners and veterinary professionals reference it as the most comprehensive snapshot of UK pet welfare trends. The report is freely available on the PDSA website."),
            ("Brachycephalic Obstructive Airway Syndrome (BOAS)", "BOAS is a set of breathing difficulties caused by the shortened skull shape in flat-faced breeds such as Bulldogs, Pugs, and French Bulldogs. Symptoms include snoring, exercise intolerance, and difficulty breathing in warm weather. The BVA has launched campaigns urging prospective owners to consider the welfare implications of choosing brachycephalic breeds. Surgical correction is sometimes necessary but does not fully resolve the underlying structural issues."),
            ("Titre Testing", "Titre testing is a blood test that measures a dog's existing antibody levels against specific diseases, helping determine whether revaccination is necessary. Some UK veterinary practices now offer titre testing as an alternative to routine annual boosters for core vaccines. While it can avoid unnecessary vaccination, it does not cover all diseases, and not all insurance companies accept titre results in place of vaccination records."),
            ("Crude Protein", "Crude protein is a measurement listed on dog food labels indicating the total protein content, determined by measuring nitrogen levels rather than actual protein quality. A higher crude protein percentage does not necessarily mean better nutrition, as the measurement does not distinguish between highly digestible animal protein and less bioavailable plant protein. Understanding this distinction helps owners evaluate food labels more critically."),
            ("FEDIAF Guidelines", "FEDIAF (the European Pet Food Industry Federation) sets nutritional guidelines that serve as the European equivalent of the US-based AAFCO standards. Dog food sold in the UK should meet FEDIAF nutritional adequacy requirements. Products labelled as nutritionally complete must meet these guidelines for the specified life stage. Checking for FEDIAF compliance is one of the most reliable ways to assess whether a dog food meets minimum nutritional standards."),
            ("Elective Gastropexy", "Elective gastropexy is a surgical procedure where the stomach is tacked to the abdominal wall to prevent gastric dilatation-volvulus (bloat), a life-threatening emergency most common in large, deep-chested breeds. The procedure is increasingly offered as a preventative measure during neutering. Breeds at higher risk include Great Danes, German Shepherds, and Standard Poodles. The BVA considers it a reasonable preventative discussion for at-risk breeds."),
            ("Antimicrobial Resistance (AMR)", "Antimicrobial resistance is a growing concern in veterinary medicine where bacteria become resistant to antibiotics through overuse. UK veterinary practices are increasingly following responsible prescribing guidelines, which means antibiotics may not be prescribed for minor infections where the dog's immune system can manage. Pet owners should never use leftover antibiotics or share medication between pets."),
            ("Body Condition Score (BCS)", "Body condition scoring is a standardised system used by veterinarians to assess whether a dog is underweight, ideal weight, or overweight. The most common scale runs from one to nine, with four to five being ideal. The PDSA estimates that over half of UK dogs are overweight or obese. Owners can learn to assess BCS at home by checking whether ribs are easily felt and whether the dog has a visible waist when viewed from above."),
            ("Prescription Diet", "A prescription diet is a therapeutic food formulated to manage specific health conditions such as kidney disease, diabetes, or food allergies. In the UK, these diets are available through veterinary practices and authorised retailers, and they require a veterinary recommendation. They are not suitable for healthy dogs and should only be used under veterinary guidance. Common brands include Royal Canin Veterinary and Hills Prescription Diet."),
            ("Zoonotic Disease", "A zoonotic disease is any illness that can be transmitted between animals and humans. Common zoonotic risks from dogs in the UK include ringworm, Campylobacter from raw-fed dogs, and toxocariasis from roundworm eggs in dog faeces. Basic hygiene measures such as handwashing after handling dogs, regular worming, and prompt faeces disposal significantly reduce these risks. The NHS provides guidance on zoonotic disease prevention."),
            ("Phantom Pregnancy", "Phantom pregnancy, or pseudopregnancy, is a hormonal condition where an unspayed female dog displays signs of pregnancy, including nesting, milk production, and behavioural changes, despite not being pregnant. It is relatively common and usually resolves within two to three weeks. In persistent or severe cases, veterinary treatment may be needed. Neutering prevents phantom pregnancies from recurring."),
            ("Cherry Eye", "Cherry eye is the prolapse of the third eyelid gland, appearing as a red, swollen mass in the corner of the eye. It is most common in brachycephalic breeds and young dogs. While not typically painful, it requires surgical correction to prevent chronic dry eye. Owners often mistake it for an infection, but it is a structural condition that will not resolve with eye drops alone."),
        ]
    },
    7172: {
        # Dog Food Glossary
        "title": "Dog Food Glossary",
        "terms": [
            ("AAFCO Equivalent (FEDIAF)", "FEDIAF is the European equivalent of the US-based AAFCO (Association of American Feed Control Officials). While AAFCO standards are frequently referenced in international dog food discussions, UK and European dog foods are governed by FEDIAF nutritional guidelines. When reading American-centric dog food reviews, UK owners should look for FEDIAF compliance rather than AAFCO statements on products sold domestically."),
            ("Ash Content", "Ash content on a dog food label represents the mineral residue remaining after the food is incinerated at high temperature. It includes essential minerals like calcium, phosphorus, and magnesium. A high ash content is not inherently bad but can indicate excessive bone meal or mineral supplementation. For dogs with urinary issues, lower ash content is sometimes recommended by veterinarians. Typical ranges are three to eight percent for dry food."),
            ("Cold-Pressed Dog Food", "Cold-pressed dog food is manufactured at lower temperatures than traditional kibble, which proponents argue preserves more nutrients and natural enzymes. The process presses ingredients together under pressure rather than using high-heat extrusion. While it is growing in popularity in the UK, independent evidence comparing nutritional outcomes with conventional kibble is limited. Brands like Guru and Forthglade offer cold-pressed options."),
            ("Guaranteed Analysis", "The guaranteed analysis is the section of a dog food label that lists minimum or maximum percentages of key nutrients including crude protein, crude fat, crude fibre, and moisture. In the UK, this is a legal requirement under feed labelling regulations. Understanding these figures allows owners to compare products on a like-for-like basis, though converting to a dry matter basis is necessary for accurate comparison between wet and dry foods."),
            ("Meat Meal vs Fresh Meat", "Meat meal is a rendered, dried protein concentrate that is more protein-dense by weight than fresh meat, which contains around seventy percent water. A food listing fresh chicken as the first ingredient may actually contain less chicken protein than one listing chicken meal, because the fresh meat weight drops significantly after cooking. Understanding this distinction is crucial for evaluating ingredient lists accurately."),
            ("Grain-Free Controversy", "Grain-free dog food became popular based on the assumption that grains are unnatural for dogs. However, the US FDA investigated a potential link between grain-free diets and dilated cardiomyopathy (DCM) in dogs, although definitive causation has not been established. UK veterinary professionals generally advise that grains are not inherently harmful to most dogs and that grain-free is not automatically superior. Dogs with diagnosed grain allergies are the exception."),
            ("Complete vs Complementary", "UK pet food labelling legally distinguishes between complete and complementary foods. A complete food provides all necessary nutrients for the specified life stage and can be fed as the sole diet. Complementary food, such as many wet food pouches and treats, is intended to be fed alongside other products. Feeding only complementary food as a main diet can lead to nutritional deficiencies over time."),
            ("Novel Protein", "A novel protein is any protein source that a dog has not previously been exposed to, commonly used in elimination diets to diagnose food allergies. Examples include venison, duck, rabbit, or insect protein. If a dog has been eating chicken and beef throughout its life, these are not novel proteins for that individual. UK veterinary dermatologists use novel protein diets as a diagnostic tool before recommending long-term dietary changes."),
            ("Dry Matter Basis", "Dry matter basis is a calculation method that removes moisture content to allow accurate nutritional comparison between wet and dry dog foods. Wet food typically contains seventy-five to eighty percent moisture, making its protein percentage appear lower than dry food on the label. To convert, divide the nutrient percentage by the dry matter percentage (one hundred minus moisture percentage). This provides a true comparison."),
            ("Palatant", "A palatant is a flavour-enhancing coating or additive applied to dog food, particularly kibble, to increase its appeal. Common palatants include animal digest, fat sprays, and yeast extracts. While palatants make food more attractive to dogs, they can also encourage overeating in food-motivated breeds. High-quality foods typically rely less on artificial palatants and more on genuine ingredient quality for flavour."),
            ("Life-Stage Feeding", "Life-stage feeding means selecting a food formulated for the dog's current age and activity level: puppy, adult, or senior. Puppy food has higher protein and calorie density for growth, while senior food typically has reduced calories and added joint-support ingredients. Feeding adult food to puppies or puppy food to adult dogs can cause nutritional imbalances. The PFMA (Pet Food Manufacturers' Association) provides UK-specific feeding guidelines."),
            ("Insect Protein", "Insect protein dog food uses black soldier fly larvae or similar insects as the primary protein source. It has gained traction in the UK as an environmentally sustainable alternative to traditional meat-based food. Studies indicate it is highly digestible and nutritionally adequate for dogs. Brands like Yora and Lovebug are available in UK retailers. It is also a genuinely novel protein for dogs with multiple meat allergies."),
        ]
    },
    7174: {
        # Dog Bed Terminology
        "title": "Dog Bed Terminology",
        "terms": [
            ("Orthopaedic Foam Density", "Foam density in dog beds is measured in kilograms per cubic metre and indicates the foam's durability and support level. Higher-density foam, typically above thirty-five kilogrammes per cubic metre, provides better joint support and lasts longer before compressing permanently. Budget beds often use lower-density foam that flattens within months. For dogs with arthritis or joint conditions, veterinary physiotherapists recommend beds with density of forty or above."),
            ("Bolster Bed", "A bolster bed features raised edges or cushioned sides that provide a sense of security and a surface for dogs to rest their heads on. They are particularly popular with dogs that like to curl up or lean against a surface while sleeping. The bolster also helps reduce draughts in cooler rooms. Bolster beds are available in various sizes and are suitable for most breeds, though very large dogs may find the interior space restrictive."),
            ("Anti-Microbial Treatment", "Anti-microbial treatment is a chemical or natural coating applied to dog bed fabrics to inhibit the growth of bacteria, mould, and odour-causing organisms. This is particularly useful for dogs that spend time outdoors or have skin conditions. Common treatments include silver-ion technology and natural options like bamboo-derived fabrics. While beneficial for hygiene, anti-microbial treatments do not replace regular washing."),
            ("Calming Bed", "Calming beds, often called anxiety beds or donut beds, feature deep sides and ultra-soft plush material designed to mimic the feeling of being nestled against another animal. They are marketed for anxious dogs, and while there is limited clinical evidence for their effectiveness, many owners report improved settling behaviour. They work best as part of a broader anxiety management plan rather than as a standalone solution."),
            ("Waterproof Liner", "A waterproof liner is a barrier layer between the bed cover and the foam or filling that protects the inner material from moisture, urine, and saliva. This is essential for incontinent dogs, puppies in house training, and elderly dogs. Quality waterproof liners are breathable to prevent heat buildup while remaining fully impermeable. Some beds integrate the liner permanently, while others offer removable options."),
            ("Elevated Cot Bed", "An elevated or raised cot bed suspends the sleeping surface off the ground on a rigid frame, typically made of metal or PVC. This design improves airflow beneath the dog, making it ideal for warm climates or summer use in the UK. Elevated beds also keep dogs away from cold or damp floors in winter. Brands like Coolaroo are widely available, and the design is particularly popular for outdoor use and kennels."),
            ("Egg-Crate Foam", "Egg-crate foam has a convoluted surface resembling an egg carton, designed to distribute pressure more evenly and improve air circulation. While it is commonly found in human mattress toppers, it is also used in mid-range dog beds. It provides some pressure relief but is generally less supportive than solid memory foam or high-density orthopaedic foam. It is a reasonable option for healthy adult dogs but may not provide sufficient support for joint conditions."),
            ("Nest Bed", "A nest bed features a flat base with gently sloping, cushioned sides, creating a nest-like shape that allows dogs to burrow and curl up. Unlike bolster beds with defined raised edges, nest beds have softer, more flexible sides that mould around the dog. They are particularly popular with smaller breeds and dogs that prefer to sleep in a curled position. Many nest beds are machine-washable, which adds practicality."),
            ("Thermoregulating Fabric", "Thermoregulating fabrics in dog beds are designed to respond to the dog's body temperature, absorbing excess heat when warm and releasing it when cool. Phase-change materials (PCMs) are sometimes incorporated into premium beds for this purpose. While the technology is proven in human bedding, its effectiveness in dog beds depends on the quality and quantity of the thermoregulating material used. It is most beneficial for breeds prone to overheating."),
            ("Filling Shift", "Filling shift occurs when the stuffing material inside a dog bed migrates away from high-pressure areas, creating uneven support and flat spots. It is the most common reason dog beds need replacing. Beds with baffled or channelled construction reduce filling shift by keeping material in designated zones. Memory foam beds do not experience filling shift but can develop permanent compression over time instead."),
            ("Removable Inner", "A removable inner refers to a separate cushion or mattress insert that can be taken out of the bed's outer cover for independent washing or replacement. Beds with removable inners are more practical for long-term use because the filling can be replaced when it compresses without buying an entirely new bed. This design is particularly cost-effective for large breed owners where replacement beds are expensive."),
            ("ISO 9001 Certified Manufacturing", "Some premium UK dog bed manufacturers reference ISO 9001 certification, which is an international quality management standard for consistent manufacturing processes. While it does not directly measure comfort or durability, it indicates the manufacturer follows documented procedures and quality checks. For owners investing in a premium bed, ISO certification provides some assurance of manufacturing consistency."),
        ]
    },
    7175: {
        # Cat Supply Essentials Glossary
        "title": "Cat Supply Essentials Glossary",
        "terms": [
            ("Obligate Carnivore", "An obligate carnivore is an animal that requires nutrients found only in animal tissue to survive. Cats are obligate carnivores, meaning they cannot thrive on plant-based diets alone. Essential nutrients like taurine, arachidonic acid, and preformed vitamin A must come from animal sources. This is why cat food must always contain animal protein as its primary ingredient, and why feeding dog food to cats can lead to serious nutritional deficiencies."),
            ("Taurine", "Taurine is an essential amino acid for cats that they cannot produce in sufficient quantities themselves and must obtain from their diet. It is critical for heart function, vision, and reproduction. Taurine deficiency can lead to dilated cardiomyopathy and retinal degeneration. All commercially produced complete cat foods in the UK contain supplemental taurine, but owners feeding homemade or raw diets must ensure adequate levels."),
            ("FLUTD (Feline Lower Urinary Tract Disease)", "FLUTD is a collective term for conditions affecting the bladder and urethra of cats, including cystitis, urethral blockages, and bladder stones. Symptoms include frequent urination, blood in urine, and inappropriate elimination. Male cats are at higher risk of life-threatening urethral blockages. Diet, water intake, and stress levels all influence FLUTD risk. Veterinary attention is urgent if a cat is straining to urinate without producing urine."),
            ("Microchip Compliance (England)", "Since June 2024, microchipping is compulsory for all cats in England before they reach twenty weeks of age. Owners who fail to comply may face a fine of up to five hundred pounds. The microchip must be registered on an approved database with current owner contact details. Scotland, Wales, and Northern Ireland have separate regulations. Microchipping costs typically range from twenty to thirty pounds through a veterinary practice."),
            ("Feliway", "Feliway is a brand-name synthetic pheromone product that mimics the feline facial pheromone cats deposit when they rub their cheeks on surfaces. It is available as a plug-in diffuser, spray, or collar and is used to reduce stress-related behaviours such as urine spraying, scratching, and hiding. While not effective for all cats, it is widely recommended by UK veterinary behaviourists as a first-line intervention for anxiety-related issues."),
            ("Kneading", "Kneading, sometimes called making biscuits, is the rhythmic pushing motion cats make with their front paws against soft surfaces. It originates from the instinctive motion kittens use to stimulate milk flow while nursing. In adult cats, it typically indicates contentment and relaxation. Some cats extend their claws during kneading, which can damage furniture or blankets. Providing a dedicated kneading blanket can redirect this behaviour."),
            ("Cat Grass", "Cat grass typically refers to wheatgrass, barley grass, or oat grass grown specifically for cats to chew on. It provides dietary fibre and may aid digestion or help with hairball management. For indoor cats, cat grass offers a safe chewing outlet that prevents them from nibbling on potentially toxic houseplants. Growing kits are widely available in UK pet shops and supermarkets and cost only a few pounds."),
            ("SureFlap and Microchip Cat Flaps", "Microchip-activated cat flaps, such as those made by SureFlap, read the cat's implanted microchip to allow entry while preventing access by neighbourhood cats or wildlife. This technology eliminates the need for collar-mounted keys or magnets. In the UK, where urban cat densities can be high, microchip cat flaps significantly reduce territorial intrusions and associated stress. They range from around sixty to one hundred and fifty pounds depending on features."),
            ("Indoor vs Outdoor Risk Assessment", "An indoor versus outdoor risk assessment involves weighing the welfare benefits and dangers of allowing a cat outdoor access based on individual circumstances. Factors include proximity to busy roads, presence of other aggressive cats, wildlife conservation concerns, and the cat's temperament. The RSPCA does not take a blanket position for or against indoor keeping but advises that indoor cats must receive adequate enrichment to compensate for restricted access."),
            ("Dental Disease in Cats", "Dental disease affects an estimated seventy percent of cats over the age of three, according to veterinary dental specialists. Common conditions include gingivitis, periodontal disease, and feline odontoclastic resorptive lesions (FORLs). Signs include bad breath, drooling, difficulty eating, and pawing at the mouth. Regular veterinary dental checks and, where possible, tooth brushing with cat-specific toothpaste help manage this widespread issue."),
            ("Complete vs Complementary Cat Food", "UK pet food law requires cat food to be labelled as either complete or complementary. Complete food provides all the nutrients a cat needs and can be the sole diet. Complementary food, including most cat treats and many pouches, must be fed alongside a complete food. A common mistake is feeding only complementary food, which can lead to nutritional deficiencies over time. Always check the label before relying on a product as the main meal."),
            ("Slow Feeder", "A slow feeder is a bowl or puzzle designed with ridges, mazes, or obstacles that force a cat to eat more slowly. They are used to prevent vomiting caused by eating too quickly, reduce obesity by extending meal times, and provide mental stimulation. For indoor cats prone to boredom eating, slow feeders serve a dual purpose of portion management and enrichment. They are available from around five to fifteen pounds in most UK pet shops."),
        ]
    },
    7177: {
        # Cat Toy Terminology
        "title": "Cat Toy Terminology",
        "terms": [
            ("Prey Sequence", "The prey sequence in cats follows a predictable pattern: stare, stalk, chase, pounce, and bite. Understanding this sequence helps owners select toys that satisfy each stage of the hunting instinct. Wand toys are excellent for the stalk-and-chase phases, while kick toys allow the pounce-and-bite phase. Completing the full prey sequence during play, ending with a treat to simulate a successful hunt, provides the most satisfying enrichment for cats."),
            ("Catnip Sensitivity", "Approximately sixty to seventy percent of cats respond to catnip (Nepeta cataria), with sensitivity being an inherited genetic trait. Kittens under six months typically show no response. The active compound, nepetalactone, triggers a temporary euphoric response lasting five to fifteen minutes when inhaled. For cats that do not respond to catnip, alternatives such as silver vine (Actinidia polygama) or valerian root often produce a similar effect."),
            ("Silver Vine", "Silver vine (Actinidia polygama) is an Asian climbing plant that produces a stronger response than catnip in many cats. Research published in BMC Veterinary Research found that nearly eighty percent of cats respond to silver vine, including many that are indifferent to catnip. It is available in the UK as dried sticks, powder, or infused in toys. It provides an effective enrichment alternative for the approximately thirty percent of cats that lack the catnip sensitivity gene."),
            ("Interactive vs Passive Toys", "Interactive toys require the owner's participation, such as wand toys, laser pointers, and feather teasers. Passive toys are those a cat can play with independently, including balls, crinkle toys, and automated moving toys. Cats Protection recommends a mix of both types, with interactive play sessions being particularly important for bonding and providing the highest quality enrichment. A minimum of two fifteen-minute interactive play sessions per day is recommended for indoor cats."),
            ("Toy Rotation", "Toy rotation is the practice of keeping only a few toys available at any time and swapping them every few days to maintain novelty. Cats quickly habituate to familiar toys, leading to disinterest and reduced play. Research suggests that even moving a familiar toy to a new location can temporarily restore interest. Keeping a selection of toys in a sealed container between rotations helps preserve any catnip or scent infusion."),
            ("Kick Toy", "A kick toy, sometimes called a bunny-kick toy or kicker, is an elongated stuffed toy designed for cats to grab with their front paws and kick vigorously with their hind legs. This behaviour mimics the killing bite sequence cats use with prey and provides vigorous physical exercise. Kick toys are typically fifteen to thirty centimetres long and often infused with catnip. They are particularly valuable for indoor cats that lack natural hunting opportunities."),
            ("Laser Pointer Frustration", "While laser pointers effectively trigger the chase instinct, they can cause frustration because the cat can never physically catch the light dot. This inability to complete the prey sequence may lead to compulsive behaviour or redirected aggression in some cats. Veterinary behaviourists recommend always ending a laser play session by directing the dot onto a physical toy or treat that the cat can capture, providing the satisfaction of a successful hunt."),
            ("Crinkle Toy", "Crinkle toys contain materials that produce a rustling sound when manipulated, mimicking the sounds of small prey moving through undergrowth. The auditory stimulation appeals to cats' highly sensitive hearing and triggers investigative behaviour. Crinkle toys are particularly effective for kittens and playful adults. When selecting crinkle toys, ensure the crinkle material is fully enclosed and cannot be ingested if the toy is torn open."),
            ("Food Puzzle Difficulty Levels", "Food puzzles and treat-dispensing toys are typically graded by difficulty level, from beginner to advanced. Starting a cat on a puzzle that is too difficult leads to frustration and abandonment. International Cat Care recommends beginning with simple, transparent puzzles where the cat can see and easily access the food, then gradually increasing difficulty as the cat masters each level. The progression builds problem-solving confidence."),
            ("Automated Toy Safety", "Automated and battery-operated cat toys, including robotic mice, rotating feather attachments, and app-controlled devices, require supervision during initial use. Cats may chew on electrical cords, swallow small detached components, or become tangled in moving parts. The UK does not have specific safety standards for pet toys, so owners should check for CE marking and inspect toys regularly for wear. Remove automated toys when not supervised."),
            ("Teaser Wand Construction", "Teaser wands, also called fishing rod toys or da-bird style toys, consist of a flexible rod with a string and attachment. The quality of the attachment point, string material, and rod flexibility all affect durability and safety. Elastic string should be avoided as it can snap back and injure eyes. Swivel attachments at the connection point prevent string tangling. Replacement attachments should be stored safely, as cats may chew swallowed feathers or string, risking intestinal obstruction."),
            ("Sensory Play Categories", "Cat toys can be categorised by the sense they primarily stimulate: visual (moving objects, light), auditory (bells, crinkle material), olfactory (catnip, silver vine, valerian), tactile (texture variety, fur-like coverings), and gustatory (treat-dispensing toys). Providing toys across all sensory categories ensures comprehensive enrichment. Cats often have individual preferences for particular sensory types, which owners can identify through observation and use to select the most engaging toys."),
        ]
    },
}


def fetch_content(post_id):
    """Fetch current post content."""
    url = f"{API}/{post_id}?context=edit"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return data


def update_content(post_id, new_content):
    """Update post content via WP REST API."""
    payload = {"content": new_content}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f)
        tmpfile = f.name

    url = f"{API}/{post_id}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH,
         "-d", f"@{tmpfile}",
         "-H", "Content-Type: application/json",
         "-X", "POST", url],
        capture_output=True, text=True
    )
    os.unlink(tmpfile)

    try:
        resp = json.loads(result.stdout)
        if "id" in resp:
            return True, resp["id"]
        else:
            return False, resp.get("message", "Unknown error")
    except json.JSONDecodeError:
        return False, result.stdout[:500]


def count_existing_terms(content):
    """Count existing terms (h3 headings that are glossary terms, not section headers)."""
    # Terms are h3 headings in the glossary body
    h3_matches = re.findall(r'<h3[^>]*>(.*?)</h3>', content)
    # Exclude known section headers
    section_headers = [
        "Frequently Asked Questions", "Sources and Further Reading",
        "Our Editorial Standards", "Indoor Cat Care Glossary",
        "Puppy Care Glossary", "Dog Health Glossary",
        "Dog Food Glossary", "Dog Bed Glossary",
        "Cat Supply Essentials Glossary", "Cat Toy Glossary"
    ]
    terms = [h for h in h3_matches if h not in section_headers and not h.startswith("Do ") and not h.startswith("How ") and not h.startswith("What ") and not h.startswith("Is ") and not h.startswith("Can ") and not h.startswith("Which ") and not h.startswith("Are ") and not h.startswith("Should ") and not h.startswith("Why ")]
    return terms


def build_term_blocks(terms_list):
    """Build Gutenberg blocks for new terms."""
    blocks = []
    for term_name, definition in terms_list:
        block = f"""
<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">{term_name}</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{definition}</p>
<!-- /wp:paragraph -->
"""
        blocks.append(block)
    return "\n".join(blocks)


def find_insertion_point(content):
    """Find the best insertion point - before FAQ section or Sources section or Editorial section."""
    # Try to find "Frequently Asked Questions" heading
    faq_match = re.search(r'<!-- wp:heading.*?-->.*?Frequently Asked Questions.*?<!-- /wp:heading -->', content, re.DOTALL)
    if faq_match:
        return faq_match.start()

    # Try to find "Sources and Further Reading"
    sources_match = re.search(r'<!-- wp:heading.*?-->.*?Sources and Further Reading.*?<!-- /wp:heading -->', content, re.DOTALL)
    if sources_match:
        return sources_match.start()

    # Try to find "Our Editorial Standards"
    editorial_match = re.search(r'<!-- wp:separator.*?-->.*?<!-- wp:heading.*?-->.*?Our Editorial Standards', content, re.DOTALL)
    if editorial_match:
        return editorial_match.start()

    # Fallback: append before last separator
    sep_matches = list(re.finditer(r'<!-- wp:separator', content))
    if sep_matches:
        return sep_matches[-1].start()

    # Last resort: append at end
    return len(content)


def process_glossary(post_id, glossary_data):
    """Process a single glossary page."""
    title = glossary_data["title"]
    new_terms = glossary_data["terms"]

    print(f"\n{'='*60}")
    print(f"Processing: {title} (ID {post_id})")
    print(f"{'='*60}")

    data = fetch_content(post_id)
    content = data.get("content", {}).get("raw", "")
    actual_title = data.get("title", {}).get("raw", "")
    print(f"  Title: {actual_title}")
    print(f"  Content length: {len(content)} chars")

    # Count existing terms
    existing = count_existing_terms(content)
    print(f"  Existing terms: {len(existing)}")

    # Filter out terms that already exist
    existing_lower = [t.lower() for t in existing]
    filtered_terms = [(name, defn) for name, defn in new_terms if name.lower() not in existing_lower]
    print(f"  New terms to add: {len(filtered_terms)}")

    if not filtered_terms:
        print("  No new terms needed - skipping")
        return post_id, actual_title, len(existing), 0, "skipped_all_exist"

    # Build term blocks
    new_blocks = build_term_blocks(filtered_terms)

    # Find insertion point (before FAQ section)
    insert_pos = find_insertion_point(content)
    print(f"  Inserting at position: {insert_pos}")

    # Insert new terms
    updated = content[:insert_pos] + new_blocks + "\n" + content[insert_pos:]
    print(f"  Updated content length: {len(updated)} chars")

    # Update via API
    success, info = update_content(post_id, updated)
    if success:
        print(f"  SUCCESS: Updated post {info}")
        return post_id, actual_title, len(existing), len(filtered_terms), "success"
    else:
        print(f"  FAILED: {info}")
        return post_id, actual_title, len(existing), len(filtered_terms), f"failed: {info}"


def main():
    results = []

    for post_id, glossary_data in GLOSSARY_TERMS.items():
        result = process_glossary(post_id, glossary_data)
        results.append(result)

    # Write log
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["glossary_id", "title", "existing_terms", "new_terms_added", "status"])
        for row in results:
            writer.writerow(row)

    print(f"\nLog written to {LOG_FILE}")
    print(f"\n=== GLOSSARY DOMINANCE WAVE 2 COMPLETE ===")
    print(f"Total glossaries processed: {len(results)}")
    print(f"Total new terms added: {sum(r[3] for r in results)}")


if __name__ == "__main__":
    main()
