#!/usr/bin/env python3
"""Phase 22D: Create and publish 25 Dog Health posts on PetHub Online."""

import requests
import json
import time
import re
import os
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────
WP_URL = "https://pethubonline.com/wp-json/wp/v2"
WP_AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
WP_HEADERS = {"Accept-Encoding": "gzip, deflate"}
PEXELS_KEY = "dmGyKrZqTlwukxWzOK1EkH4jbEv9EaIDpLGj7eL5MZ07bl6AR9OEoHlB"
AMAZON_TAG = "pethubonline-21"
CATEGORY_ID = 1450
RESULTS_FILE = "/var/lib/freelancer/projects/40416335/phase22d_dog_health_results.json"

session = requests.Session()
session.auth = WP_AUTH
session.headers.update(WP_HEADERS)

# ── Topics ──────────────────────────────────────────────────────────────
TOPICS = [
    {
        "title": "How to Recognise Early Signs of Pain in Dogs",
        "slug": "early-signs-of-pain-in-dogs",
        "pexels": "dog pain limping",
        "excerpt": "Learn the subtle signs that indicate your dog may be in pain, from behavioural changes to physical symptoms.",
        "amazon_products": [
            ("Dog Pain Relief Supplements", "dog+pain+relief+supplement+glucosamine"),
            ("Orthopaedic Dog Beds", "orthopaedic+dog+bed"),
            ("Dog Thermal Heat Pads", "dog+heat+pad+pain+relief"),
            ("Dog Massage Tools", "dog+massage+tool"),
            ("Dog Mobility Harness", "dog+mobility+support+harness"),
        ],
        "faq": [
            ("What are the first signs of pain in dogs?", "Common early signs include limping, reluctance to move, whimpering, changes in eating habits, excessive licking of a specific area, and unusual aggression or withdrawal. Dogs often hide pain instinctively, so subtle behavioural changes are key indicators."),
            ("How do dogs show they are in pain?", "Dogs may pant excessively, tremble, become restless, avoid being touched, hold their body in unusual positions, or show changes in sleeping patterns. Some dogs become clingy while others withdraw completely."),
            ("Can dogs cry from pain?", "Dogs don't produce emotional tears like humans, but they may whimper, yelp, howl, or whine when experiencing pain. Silence doesn't mean absence of pain — many dogs suffer quietly."),
            ("When should I take my dog to the vet for pain?", "Seek veterinary attention if pain signs persist for more than 24 hours, if your dog stops eating or drinking, if there is visible swelling or injury, or if your dog shows sudden behavioural changes."),
            ("How can I comfort a dog in pain at home?", "Provide a quiet, comfortable resting area with supportive bedding. Keep them warm, offer gentle reassurance without excessive handling, and follow any pain management plan from your vet. Never give human painkillers to dogs."),
        ],
    },
    {
        "title": "Complete Guide to Dog Vaccination Schedules in the UK",
        "slug": "dog-vaccination-schedule-uk",
        "pexels": "dog veterinarian injection",
        "excerpt": "Everything UK dog owners need to know about core and non-core vaccinations, boosters, and puppy vaccination timelines.",
        "amazon_products": [
            ("Dog Health Record Book", "dog+health+record+book"),
            ("Dog First Aid Kit", "dog+first+aid+kit"),
            ("Pet Thermometer", "pet+digital+thermometer"),
            ("Puppy Training Treats", "puppy+training+treats+uk"),
            ("Dog Carrier for Vet Visits", "dog+carrier+vet+visits"),
        ],
        "faq": [
            ("What vaccinations do puppies need in the UK?", "UK puppies typically need core vaccinations against canine distemper, parvovirus, canine hepatitis, and leptospirosis. The primary course usually starts at 6-8 weeks with a second dose at 10-12 weeks."),
            ("How much do dog vaccinations cost in the UK?", "Primary puppy vaccinations typically cost between £30-£60 at most UK veterinary practices. Annual boosters usually cost £30-£50. Prices vary by region and veterinary practice."),
            ("Are annual booster vaccinations necessary for dogs?", "The BVA and BSAVA recommend regular boosters, though not all components need annual renewal. Leptospirosis requires annual boosters, while distemper, parvovirus, and hepatitis may only need boosting every three years."),
            ("Can I walk my puppy before vaccinations are complete?", "Puppies should not walk in public areas until 1-2 weeks after their second vaccination. You can carry them to experience outdoor sights and sounds, and they can play in secure private gardens."),
            ("What are non-core vaccines for dogs in the UK?", "Non-core vaccines include kennel cough (Bordetella bronchiseptica and parainfluenza), rabies (required for pet travel), and Lyme disease. Your vet will recommend these based on your dog's lifestyle and risk factors."),
        ],
    },
    {
        "title": "How to Monitor Your Dog's Weight at Home",
        "slug": "monitor-dog-weight-at-home",
        "pexels": "dog weighing scale",
        "excerpt": "Practical guide to tracking your dog's weight, understanding body condition scoring, and maintaining a healthy weight.",
        "amazon_products": [
            ("Pet Weighing Scale", "pet+weighing+scale+dog"),
            ("Dog Slow Feeder Bowl", "dog+slow+feeder+bowl"),
            ("Dog Weight Management Food", "dog+weight+management+food"),
            ("Dog Measuring Cups for Food", "dog+food+measuring+cup"),
            ("Dog Activity Monitor", "dog+activity+monitor+tracker"),
        ],
        "faq": [
            ("How often should I weigh my dog?", "Weigh your dog at least once a month for adults and weekly for puppies. Senior dogs or those on weight management programmes should be weighed fortnightly. Consistency in timing helps track trends accurately."),
            ("How do I weigh a large dog at home?", "Weigh yourself on a bathroom scale, then pick up your dog and weigh again. The difference is your dog's weight. Alternatively, invest in a pet-specific platform scale rated for your dog's size."),
            ("What is body condition scoring for dogs?", "Body condition scoring (BCS) is a hands-on assessment using a 1-9 scale. An ideal score is 4-5, where ribs are easily felt but not visible, there is a clear waist when viewed from above, and a tummy tuck from the side."),
            ("How do I know if my dog is overweight?", "Signs include difficulty feeling ribs under a fat layer, no visible waist from above, a sagging belly, reduced stamina during walks, and difficulty getting up. Your vet can confirm with a body condition assessment."),
            ("How much should I feed my dog to maintain healthy weight?", "Follow feeding guidelines on your dog food packaging as a starting point, then adjust based on body condition. Most guidelines overestimate portions. An active working dog needs more than a sedentary pet of the same size."),
        ],
    },
    {
        "title": "Understanding Canine Diabetes: Symptoms and Management",
        "slug": "canine-diabetes-symptoms-management",
        "pexels": "dog drinking water bowl",
        "excerpt": "Learn about diabetes mellitus in dogs, recognising symptoms early, and managing the condition with diet and insulin.",
        "amazon_products": [
            ("Pet Blood Glucose Monitor", "pet+blood+glucose+monitor"),
            ("Diabetic Dog Food", "diabetic+dog+food"),
            ("Dog Insulin Syringes", "pet+insulin+syringes"),
            ("Dog Water Fountain", "dog+water+fountain+large"),
            ("Sharps Disposal Container", "sharps+disposal+container+small"),
        ],
        "faq": [
            ("What are the symptoms of diabetes in dogs?", "Key symptoms include excessive thirst (polydipsia), frequent urination (polyuria), increased appetite with weight loss, lethargy, cloudy eyes (cataracts), and recurring urinary tract infections."),
            ("Can canine diabetes be cured?", "Diabetes mellitus in dogs is typically a lifelong condition requiring ongoing management. While it cannot be cured, it can be well-controlled with insulin therapy, dietary management, and regular veterinary monitoring."),
            ("How much does treating a diabetic dog cost in the UK?", "Initial diagnosis and stabilisation may cost £200-£500. Ongoing monthly costs for insulin, syringes, and monitoring typically range from £50-£150. Regular check-ups add further costs."),
            ("What should a diabetic dog eat?", "Diabetic dogs benefit from high-fibre, complex-carbohydrate diets fed at consistent times. Avoid high-sugar treats. Your vet may recommend a prescription diabetic diet. Consistent meal timing alongside insulin is crucial."),
            ("Can I give my dog insulin at home?", "Yes, most dog owners learn to give insulin injections at home. Your vet will demonstrate the technique, which involves a small subcutaneous injection typically given at mealtimes. It becomes routine with practice."),
        ],
    },
    {
        "title": "How to Keep Your Dog's Heart Healthy",
        "slug": "keep-dog-heart-healthy",
        "pexels": "dog running exercise healthy",
        "excerpt": "Essential tips for maintaining your dog's cardiovascular health through diet, exercise, and early detection of heart disease.",
        "amazon_products": [
            ("Dog Heart Health Supplements", "dog+heart+health+supplement+taurine"),
            ("Dog Omega 3 Fish Oil", "dog+omega+3+fish+oil"),
            ("Dog Harness No Pull", "dog+harness+no+pull"),
            ("Elevated Dog Bowl Stand", "elevated+dog+bowl+stand"),
            ("Dog Stethoscope Pet", "pet+stethoscope"),
        ],
        "faq": [
            ("What are signs of heart disease in dogs?", "Watch for persistent cough (especially at night), difficulty breathing, exercise intolerance, fainting or collapsing, swollen abdomen, and rapid weight loss. A racing or irregular heartbeat may also be detected."),
            ("Which dog breeds are prone to heart disease?", "Cavalier King Charles Spaniels are prone to mitral valve disease. Dobermanns and Boxers are prone to dilated cardiomyopathy. Large breeds generally face higher risk, but heart disease can affect any breed."),
            ("Can diet help prevent heart disease in dogs?", "A balanced diet rich in omega-3 fatty acids, taurine, and L-carnitine supports heart health. Maintaining a healthy weight reduces cardiac workload. Avoid grain-free diets linked to DCM concerns unless vet-recommended."),
            ("How is heart disease diagnosed in dogs?", "Vets use a combination of physical examination, chest X-rays, electrocardiogram (ECG), and echocardiography (heart ultrasound). Blood tests including proBNP can also indicate heart stress."),
            ("How long can a dog live with heart disease?", "Prognosis varies greatly depending on the type and stage of disease. Many dogs with early-stage heart disease live years with proper medication and monitoring. Advanced heart failure has a more guarded prognosis."),
        ],
    },
    {
        "title": "Common Dog Eye Problems and When to See a Vet",
        "slug": "dog-eye-problems-when-to-see-vet",
        "pexels": "dog eyes close up",
        "excerpt": "Identify common eye conditions in dogs, from conjunctivitis to cataracts, and know when veterinary attention is needed.",
        "amazon_products": [
            ("Dog Eye Wipes", "dog+eye+wipes+tear+stain"),
            ("Dog Eye Drops Saline", "dog+eye+drops+saline"),
            ("Dog Eye Protection Goggles", "dog+eye+goggles+protection"),
            ("Dog Tear Stain Remover", "dog+tear+stain+remover"),
            ("Elizabethan Cone for Dogs", "elizabethan+cone+dog+comfortable"),
        ],
        "faq": [
            ("What are common eye problems in dogs?", "Common conditions include conjunctivitis (pink eye), corneal ulcers, cataracts, glaucoma, cherry eye, dry eye (KCS), and entropion. Breeds with prominent eyes like Pugs are more susceptible to eye injuries."),
            ("How do I know if my dog has an eye infection?", "Signs include redness, swelling, discharge (clear, yellow, or green), squinting, pawing at the eye, cloudiness, and excessive tearing. Any sudden change in eye appearance warrants veterinary attention."),
            ("Can I use human eye drops on my dog?", "Never use human eye drops on dogs without veterinary guidance. Some human drops contain ingredients toxic to dogs. Only use products specifically recommended by your vet for your dog's condition."),
            ("Are cataracts in dogs treatable?", "Yes, cataracts can be surgically removed by a veterinary ophthalmologist. Surgery success rates are high (90%+) when performed early. Not all dogs are candidates — your vet will assess overall health first."),
            ("How can I prevent eye problems in my dog?", "Keep hair trimmed around eyes, clean eye discharge regularly with damp cotton wool, avoid exposing dogs to irritants, and attend regular vet check-ups. Breed-specific screening helps catch hereditary conditions early."),
        ],
    },
    {
        "title": "How to Protect Your Dog from Seasonal Allergies",
        "slug": "protect-dog-seasonal-allergies",
        "pexels": "dog scratching itching grass",
        "excerpt": "Practical strategies to identify, prevent, and manage seasonal allergies in dogs throughout the year.",
        "amazon_products": [
            ("Dog Allergy Supplement", "dog+allergy+supplement+skin"),
            ("Dog Antihistamine Wipes", "dog+allergy+wipes+paws"),
            ("Dog Oatmeal Shampoo", "dog+oatmeal+shampoo+itchy+skin"),
            ("Dog Paw Washer", "dog+paw+washer+cleaner"),
            ("Air Purifier for Pet Allergies", "air+purifier+pet+allergies"),
        ],
        "faq": [
            ("What are the signs of seasonal allergies in dogs?", "Common signs include excessive scratching, red or inflamed skin, ear infections, watery eyes, sneezing, chewing paws, and hot spots. Symptoms typically worsen during spring and autumn pollen seasons."),
            ("Can dogs take antihistamines?", "Some human antihistamines like chlorphenamine can be used in dogs, but only under veterinary guidance with correct dosing. Never give medication without consulting your vet, as some antihistamines are unsuitable for dogs."),
            ("How do I know if my dog has allergies or something else?", "Seasonal patterns suggest environmental allergies. Year-round symptoms may indicate food sensitivities. Your vet can perform intradermal skin tests or blood tests to identify specific allergens."),
            ("Should I bathe my dog more often during allergy season?", "Yes, weekly bathing with a gentle, hypoallergenic or oatmeal-based shampoo can help remove allergens from the coat. Wiping paws after walks also reduces allergen exposure significantly."),
            ("What time of year are dog allergies worst?", "In the UK, tree pollen peaks in March-May, grass pollen in May-July, and weed pollen in June-September. Mould spore allergies may worsen in autumn. Some dogs react to multiple seasonal triggers."),
        ],
    },
    {
        "title": "Understanding Hip Dysplasia in Dogs: Prevention and Care",
        "slug": "hip-dysplasia-dogs-prevention-care",
        "pexels": "large dog hip walking",
        "excerpt": "Comprehensive guide to hip dysplasia in dogs, including risk factors, symptoms, treatment options, and preventive measures.",
        "amazon_products": [
            ("Dog Hip Dysplasia Supplement", "dog+hip+joint+supplement+glucosamine+chondroitin"),
            ("Orthopaedic Dog Bed Large", "orthopaedic+memory+foam+dog+bed+large"),
            ("Dog Ramp for Car", "dog+ramp+car+folding"),
            ("Dog Hip Support Brace", "dog+hip+support+brace"),
            ("Non-Slip Dog Socks", "non+slip+dog+socks+grip"),
        ],
        "faq": [
            ("What causes hip dysplasia in dogs?", "Hip dysplasia is primarily genetic, where the hip joint develops abnormally. Contributing factors include rapid growth, excessive exercise in puppies, obesity, and poor nutrition. Large and giant breeds are most commonly affected."),
            ("Which dog breeds are most prone to hip dysplasia?", "German Shepherds, Labrador Retrievers, Golden Retrievers, Rottweilers, Great Danes, Saint Bernards, and Bulldogs are among the most affected breeds. However, it can occur in any breed including smaller dogs."),
            ("Can hip dysplasia be prevented?", "While genetic predisposition cannot be eliminated, risk can be reduced through responsible breeding (hip-scored parents), controlled growth rate in puppies, appropriate exercise, maintaining healthy weight, and proper nutrition."),
            ("What are the treatment options for hip dysplasia?", "Options range from conservative management (weight control, physiotherapy, anti-inflammatories, joint supplements) to surgical options including femoral head ostectomy, triple pelvic osteotomy, and total hip replacement."),
            ("How much does hip dysplasia surgery cost in the UK?", "Total hip replacement costs £3,000-£6,000 per hip in the UK. Femoral head ostectomy is typically £1,500-£3,000. Conservative management costs vary but are significantly less. Pet insurance may cover treatment if the condition wasn't pre-existing."),
        ],
    },
    {
        "title": "How to Care for a Dog with Epilepsy",
        "slug": "care-for-dog-with-epilepsy",
        "pexels": "calm dog resting peaceful",
        "excerpt": "Essential guidance for managing epilepsy in dogs, understanding seizure types, and providing the best care at home.",
        "amazon_products": [
            ("Dog Seizure Diary Notebook", "pet+health+diary+record+book"),
            ("Dog Calming Bed", "dog+calming+bed+anti+anxiety"),
            ("Pet Camera WiFi", "pet+camera+wifi+monitor"),
            ("Dog ID Tag Medical Alert", "dog+id+tag+medical+alert"),
            ("Dog Pill Pockets Treats", "dog+pill+pockets+treats"),
        ],
        "faq": [
            ("What does a seizure look like in a dog?", "Seizures may involve collapsing, stiffening, paddling legs, drooling, chomping jaws, loss of consciousness, and involuntary urination or defecation. Milder seizures may cause twitching, staring, or brief confusion."),
            ("What should I do when my dog has a seizure?", "Stay calm, ensure the area is safe (remove sharp objects), do not put anything in their mouth, time the seizure, and speak softly. Contact your vet if the seizure lasts more than 5 minutes or if multiple seizures occur in 24 hours."),
            ("Can epilepsy in dogs be cured?", "Idiopathic epilepsy cannot be cured but can usually be managed effectively with anti-epileptic medication. The goal is to reduce seizure frequency and severity while maintaining quality of life."),
            ("What triggers seizures in dogs?", "Common triggers include stress, excitement, changes in routine, sleep disruption, certain foods or medications, hormonal changes, and flashing lights. Keeping a seizure diary helps identify individual triggers."),
            ("How long do dogs with epilepsy live?", "Most epileptic dogs have a normal or near-normal lifespan with proper medication and management. Some dogs achieve complete seizure control, while others have occasional breakthrough seizures."),
        ],
    },
    {
        "title": "Dog Ear Infections: Causes, Treatment, and Prevention",
        "slug": "dog-ear-infections-causes-treatment-prevention",
        "pexels": "dog ear close up floppy",
        "excerpt": "Everything you need to know about ear infections in dogs, from identifying symptoms to effective treatment and long-term prevention.",
        "amazon_products": [
            ("Dog Ear Cleaner Solution", "dog+ear+cleaner+solution"),
            ("Dog Ear Wipes", "dog+ear+wipes+cleaning"),
            ("Dog Ear Drying Powder", "dog+ear+drying+powder"),
            ("Dog Snood Ear Protector", "dog+snood+ear+protector+eating"),
            ("Dog Ear Infection Treatment", "dog+ear+infection+drops"),
        ],
        "faq": [
            ("What causes ear infections in dogs?", "Common causes include bacteria, yeast, ear mites, allergies, moisture trapped in the ear canal, foreign bodies (grass seeds), and excessive ear hair. Floppy-eared breeds are particularly prone due to reduced air circulation."),
            ("How do I know if my dog has an ear infection?", "Signs include head shaking, scratching at ears, redness or swelling, dark or smelly discharge, pain when ears are touched, tilting head to one side, and loss of balance in severe cases."),
            ("Can I treat my dog's ear infection at home?", "Mild cases may respond to regular cleaning with a vet-approved ear cleaner. However, most infections require veterinary diagnosis to determine the cause (bacterial, yeast, or mites) and appropriate prescription medication."),
            ("How often should I clean my dog's ears?", "Clean ears weekly for dogs prone to infections, or fortnightly for most dogs. Always clean after swimming or bathing. Over-cleaning can also cause problems, so follow your vet's recommendations for your specific dog."),
            ("Why does my dog keep getting ear infections?", "Recurrent infections often indicate an underlying issue such as allergies (food or environmental), anatomical factors (narrow ear canals, floppy ears), hormonal conditions, or immune system problems. A thorough veterinary workup is recommended."),
        ],
    },
    {
        "title": "How to Support Your Dog's Immune System Naturally",
        "slug": "support-dog-immune-system-naturally",
        "pexels": "healthy dog outdoors active",
        "excerpt": "Natural ways to boost and maintain your dog's immune health through nutrition, exercise, and lifestyle choices.",
        "amazon_products": [
            ("Dog Probiotic Supplement", "dog+probiotic+supplement"),
            ("Dog Immune Support Supplement", "dog+immune+support+supplement"),
            ("Dog Coconut Oil Supplement", "dog+coconut+oil+supplement"),
            ("Dog Bone Broth", "dog+bone+broth+supplement"),
            ("Dog Vitamin Supplement", "dog+multivitamin+supplement"),
        ],
        "faq": [
            ("How can I boost my dog's immune system naturally?", "Key strategies include feeding a balanced, high-quality diet, ensuring regular exercise, maintaining a healthy weight, providing mental stimulation, supporting gut health with probiotics, and minimising unnecessary chemical exposure."),
            ("What foods boost a dog's immune system?", "Beneficial foods include blueberries (antioxidants), sweet potatoes (beta-carotene), oily fish (omega-3s), spinach (vitamins), and plain yoghurt (probiotics). Always introduce new foods gradually and in moderation."),
            ("Do dogs need vitamin supplements?", "Dogs on a complete, balanced commercial diet generally don't need additional vitamins. However, supplements may benefit dogs with specific health conditions, senior dogs, or those on home-prepared diets. Consult your vet before supplementing."),
            ("Can stress affect my dog's immune system?", "Yes, chronic stress suppresses immune function in dogs just as in humans. Cortisol released during prolonged stress reduces white blood cell effectiveness. Reducing stress through routine, exercise, and enrichment supports immune health."),
            ("Are probiotics good for dogs?", "Yes, probiotics can support gut health and immune function in dogs. The gut contains roughly 70% of the immune system. Choose canine-specific probiotic strains and introduce them gradually."),
        ],
    },
    {
        "title": "Understanding Canine Cognitive Dysfunction in Senior Dogs",
        "slug": "canine-cognitive-dysfunction-senior-dogs",
        "pexels": "old senior dog grey muzzle",
        "excerpt": "Recognise the signs of cognitive decline in ageing dogs and discover strategies to slow progression and maintain quality of life.",
        "amazon_products": [
            ("Senior Dog Brain Supplement", "senior+dog+brain+supplement+cognitive"),
            ("Dog Puzzle Toy Interactive", "dog+puzzle+toy+interactive"),
            ("Senior Dog Food", "senior+dog+food+brain+health"),
            ("Dog Night Light", "dog+night+light+plug+in"),
            ("Dog Calming Diffuser", "dog+calming+diffuser+adaptil"),
        ],
        "faq": [
            ("What is canine cognitive dysfunction (CCD)?", "CCD is a neurodegenerative condition similar to Alzheimer's in humans. It affects senior dogs, causing progressive decline in memory, learning, awareness, and responsiveness. It results from physical changes in the brain including beta-amyloid plaque accumulation."),
            ("What are the signs of dementia in dogs?", "Use the DISHAA acronym: Disorientation, Interaction changes, Sleep-wake cycle disruption, House soiling, Activity level changes, and Anxiety. Dogs may get stuck in corners, fail to recognise family members, or pace at night."),
            ("At what age do dogs develop cognitive dysfunction?", "CCD typically affects dogs over 8-10 years old, with prevalence increasing with age. Studies suggest roughly 28% of dogs aged 11-12 and 68% of dogs aged 15-16 show at least one sign of cognitive decline."),
            ("Can canine cognitive dysfunction be treated?", "While CCD cannot be reversed, progression can be slowed with medication (selegiline), dietary supplements (omega-3s, antioxidants, SAMe), mental enrichment, regular exercise, and environmental management to reduce confusion."),
            ("How can I help my senior dog with dementia at home?", "Maintain consistent routines, keep furniture in the same place, use night lights for nighttime navigation, provide mental stimulation through simple puzzles, continue gentle exercise, and be patient with house-training lapses."),
        ],
    },
    {
        "title": "How to Manage Separation Anxiety in Dogs",
        "slug": "manage-separation-anxiety-dogs",
        "pexels": "dog looking out window waiting",
        "excerpt": "Effective strategies for understanding and managing separation anxiety in dogs, from mild distress to severe cases.",
        "amazon_products": [
            ("Dog Calming Supplement", "dog+calming+supplement+anxiety"),
            ("Dog Calming Diffuser Adaptil", "adaptil+calming+diffuser+dog"),
            ("Dog Camera Treat Dispenser", "dog+camera+treat+dispenser"),
            ("Kong Dog Toy Stuffable", "kong+dog+toy+stuffable"),
            ("Dog Anxiety Vest Thundershirt", "thundershirt+dog+anxiety+vest"),
        ],
        "faq": [
            ("What are signs of separation anxiety in dogs?", "Signs include destructive behaviour when left alone, excessive barking or howling, pacing, house soiling despite being house-trained, drooling, escape attempts, and refusal to eat when alone. Symptoms occur specifically when separated from their owner."),
            ("What causes separation anxiety in dogs?", "Causes include changes in routine or household, rehoming, loss of a family member, lack of early socialisation, traumatic experiences, and over-attachment. Some breeds are genetically predisposed to stronger attachment behaviours."),
            ("How long does it take to treat separation anxiety?", "Improvement timelines vary greatly. Mild cases may improve within weeks with consistent training, while severe cases can take months of behaviour modification, potentially combined with medication. Patience and consistency are essential."),
            ("Should I get another dog to help with separation anxiety?", "Getting a second dog is not a reliable solution. Separation anxiety is about attachment to the human, not loneliness. The second dog may even develop anxiety themselves. Address the underlying issue through behaviour modification first."),
            ("Can medication help with separation anxiety in dogs?", "In moderate to severe cases, your vet may prescribe anti-anxiety medication (such as fluoxetine) alongside a behaviour modification programme. Medication alone is rarely sufficient — it works best combined with training."),
        ],
    },
    {
        "title": "Complete Guide to Dog Dental Care at Home",
        "slug": "dog-dental-care-at-home-guide",
        "pexels": "dog teeth mouth open",
        "excerpt": "Keep your dog's teeth healthy with this guide to at-home dental care, including brushing techniques and dental products.",
        "amazon_products": [
            ("Dog Toothbrush and Toothpaste Set", "dog+toothbrush+toothpaste+set"),
            ("Dog Dental Chews", "dog+dental+chews+sticks"),
            ("Dog Dental Water Additive", "dog+dental+water+additive"),
            ("Dog Dental Toy", "dog+dental+toy+chew"),
            ("Dog Finger Toothbrush", "dog+finger+toothbrush"),
        ],
        "faq": [
            ("How often should I brush my dog's teeth?", "Ideally, brush your dog's teeth daily for the best results. If daily brushing isn't possible, aim for at least 3-4 times per week. Even occasional brushing is better than none and helps reduce plaque and tartar buildup."),
            ("What toothpaste should I use for my dog?", "Always use toothpaste specifically formulated for dogs. Human toothpaste contains fluoride and xylitol, which are toxic to dogs. Dog toothpastes come in appealing flavours like poultry or beef to make brushing more enjoyable."),
            ("How do I know if my dog has dental disease?", "Signs include bad breath, red or swollen gums, yellow-brown tartar on teeth, difficulty eating, drooling, pawing at the mouth, loose teeth, and bleeding gums. By age 3, most dogs have some degree of dental disease."),
            ("Do dental chews really work for dogs?", "VOHC-approved dental chews can help reduce plaque and tartar when used alongside brushing. They are not a replacement for brushing but serve as a useful supplement. Look for the VOHC seal of acceptance."),
            ("How much does professional dog dental cleaning cost in the UK?", "Professional dental cleaning under general anaesthesia typically costs £200-£400 in the UK, depending on the extent of treatment needed. Extractions and additional procedures increase the cost. Regular home care helps reduce the need for professional cleanings."),
        ],
    },
    {
        "title": "How to Recognise and Treat Hot Spots on Dogs",
        "slug": "recognise-treat-hot-spots-dogs",
        "pexels": "dog skin care grooming",
        "excerpt": "Learn how to identify, treat, and prevent acute moist dermatitis (hot spots) in dogs with practical at-home care tips.",
        "amazon_products": [
            ("Dog Hot Spot Treatment Spray", "dog+hot+spot+treatment+spray"),
            ("Dog Wound Care Spray", "dog+wound+care+antiseptic+spray"),
            ("Dog Recovery Suit", "dog+recovery+suit+alternative+cone"),
            ("Dog Grooming Clippers", "dog+grooming+clippers+professional"),
            ("Dog Skin Soothing Balm", "dog+skin+soothing+balm"),
        ],
        "faq": [
            ("What causes hot spots on dogs?", "Hot spots are caused by self-trauma through scratching, licking, or chewing. Triggers include flea bites, allergies, insect stings, ear infections, matted fur, moisture trapped against skin, and boredom. Any irritation that leads to scratching can start the cycle."),
            ("How do you treat hot spots on dogs at home?", "Gently clip fur around the area, clean with a mild antiseptic solution, apply a vet-approved topical treatment, and prevent further licking with an Elizabethan collar or recovery suit. Seek veterinary advice if the spot is large, deep, or not improving within 24-48 hours."),
            ("How long do hot spots take to heal?", "With proper treatment, most hot spots begin improving within 3-7 days and heal fully within 1-2 weeks. Without treatment, they can spread rapidly and become infected, leading to more serious complications."),
            ("Are certain dog breeds more prone to hot spots?", "Breeds with thick, dense coats like Golden Retrievers, German Shepherds, Labrador Retrievers, and Saint Bernards are more susceptible. Dogs that swim frequently or live in hot, humid climates are also at higher risk."),
            ("Can hot spots spread to other dogs or humans?", "Hot spots themselves are not contagious. However, if the underlying cause is a contagious condition such as fleas or certain skin infections, those can spread to other animals. Hot spots do not spread to humans."),
        ],
    },
    {
        "title": "Understanding Thyroid Problems in Dogs",
        "slug": "thyroid-problems-in-dogs",
        "pexels": "dog lethargy lying down tired",
        "excerpt": "Comprehensive guide to hypothyroidism and other thyroid issues in dogs, covering symptoms, diagnosis, and treatment.",
        "amazon_products": [
            ("Dog Thyroid Supplement", "dog+thyroid+support+supplement"),
            ("Dog Weight Management Food", "dog+weight+management+low+calorie+food"),
            ("Dog Coat Health Supplement", "dog+coat+health+supplement+skin"),
            ("Dog Pill Organiser", "pet+pill+organiser+weekly"),
            ("Dog Warming Blanket", "dog+warming+blanket+thermal"),
        ],
        "faq": [
            ("What is hypothyroidism in dogs?", "Hypothyroidism occurs when the thyroid gland doesn't produce enough thyroid hormone. It's the most common hormonal disorder in dogs, typically caused by immune-mediated destruction of the thyroid gland or its natural atrophy."),
            ("What are the symptoms of thyroid problems in dogs?", "Common symptoms include unexplained weight gain, lethargy, cold intolerance, hair loss (often symmetrical), dry/dull coat, skin infections, ear infections, and a 'tragic' facial expression caused by skin thickening."),
            ("Which dog breeds are prone to thyroid issues?", "Golden Retrievers, Dobermanns, Irish Setters, Dachshunds, Cocker Spaniels, and Airedale Terriers are among the more commonly affected breeds. It typically develops in middle-aged dogs (4-10 years)."),
            ("How is hypothyroidism treated in dogs?", "Treatment involves daily oral thyroid hormone replacement medication (levothyroxine). Dose is adjusted based on blood tests taken 4-6 hours after medication. Treatment is lifelong but very effective, with most dogs showing improvement within weeks."),
            ("How much does thyroid treatment cost for dogs in the UK?", "Thyroid blood tests typically cost £50-£100. Monthly medication costs approximately £15-£30 depending on dose and brand. Regular monitoring blood tests are needed, especially initially. Total annual cost is usually under £500."),
        ],
    },
    {
        "title": "How to Help Your Dog Recover from Surgery",
        "slug": "help-dog-recover-from-surgery",
        "pexels": "dog resting recovery comfortable",
        "excerpt": "Post-surgery care guide for dogs covering pain management, wound care, nutrition, and getting back to normal activity.",
        "amazon_products": [
            ("Dog Recovery Suit Post Surgery", "dog+recovery+suit+post+surgery"),
            ("Dog Orthopaedic Recovery Bed", "dog+orthopaedic+bed+washable"),
            ("Dog Playpen Indoor", "dog+playpen+indoor+large"),
            ("Dog Lick Mat", "dog+lick+mat+enrichment"),
            ("Dog Wound Care Spray", "dog+wound+care+spray+gentle"),
        ],
        "faq": [
            ("How long does it take a dog to recover from surgery?", "Recovery time varies by procedure. Minor surgeries (neutering, lump removal) typically need 10-14 days. Orthopaedic procedures may require 6-12 weeks. Your vet will provide a specific recovery timeline and activity restrictions."),
            ("How do I stop my dog licking their stitches?", "Use an Elizabethan collar (cone), inflatable collar, or recovery suit to prevent licking. Recovery suits are often better tolerated than cones. Never leave your dog unsupervised without protection during the healing period."),
            ("What should I feed my dog after surgery?", "Offer small, frequent meals of easily digestible food for the first 24-48 hours. Some dogs may need a bland diet (plain chicken and rice). Ensure fresh water is always available. Appetite should return to normal within a few days."),
            ("When should I be worried after my dog's surgery?", "Contact your vet if you notice excessive swelling, bleeding, or discharge from the wound, foul smell, persistent vomiting, refusal to eat for more than 24 hours, extreme lethargy, or signs of severe pain."),
            ("Can I leave my dog alone after surgery?", "Ideally, don't leave your dog alone for the first 24-48 hours after surgery. After that, ensure they are confined to a safe area with no access to stairs or furniture they could jump from. A pet camera can help you monitor them remotely."),
        ],
    },
    {
        "title": "Common Digestive Issues in Dogs and Natural Remedies",
        "slug": "common-digestive-issues-dogs-natural-remedies",
        "pexels": "dog eating food bowl healthy",
        "excerpt": "Understand common digestive problems in dogs and explore safe, natural approaches alongside veterinary care.",
        "amazon_products": [
            ("Dog Probiotic Digestive Supplement", "dog+probiotic+digestive+supplement"),
            ("Dog Sensitive Stomach Food", "dog+sensitive+stomach+food"),
            ("Dog Slow Feeder Bowl Maze", "dog+slow+feeder+bowl+maze"),
            ("Dog Pumpkin Supplement Digestive", "dog+pumpkin+supplement+digestive"),
            ("Dog Digestive Enzyme Supplement", "dog+digestive+enzyme+supplement"),
        ],
        "faq": [
            ("What are common digestive problems in dogs?", "Common issues include vomiting, diarrhoea, constipation, flatulence, gastritis, pancreatitis, and inflammatory bowel disease. Dietary indiscretion (eating inappropriate items) is the most frequent cause of acute digestive upset."),
            ("When is dog vomiting serious?", "Seek urgent veterinary attention if vomiting persists for more than 24 hours, contains blood, is accompanied by lethargy or abdominal pain, occurs alongside diarrhoea, or if your dog cannot keep water down. Puppies and seniors are at higher risk of dehydration."),
            ("Can pumpkin help with dog digestive issues?", "Plain, tinned pumpkin (not pumpkin pie filling) can help with both diarrhoea and constipation due to its soluble fibre content. Offer 1-4 tablespoons depending on dog size. It's generally safe but not a substitute for veterinary care."),
            ("What is a bland diet for dogs?", "A bland diet typically consists of boiled chicken breast (no skin or bones) mixed with plain white rice in a 1:2 ratio. Feed small, frequent meals for 2-3 days until stools normalise, then gradually reintroduce regular food."),
            ("Are probiotics safe for dogs with digestive issues?", "Yes, canine-specific probiotics are generally safe and can help restore healthy gut bacteria after digestive upset or antibiotic use. Choose products with documented canine strains and introduce gradually."),
        ],
    },
    {
        "title": "How to Prevent and Treat Urinary Tract Infections in Dogs",
        "slug": "prevent-treat-urinary-tract-infections-dogs",
        "pexels": "dog drinking water hydration",
        "excerpt": "Learn about UTIs in dogs, including causes, symptoms, veterinary treatments, and prevention strategies.",
        "amazon_products": [
            ("Dog Cranberry Supplement UTI", "dog+cranberry+supplement+urinary"),
            ("Dog Water Fountain", "dog+water+fountain+stainless+steel"),
            ("Dog Urinary Health Food", "dog+urinary+health+food"),
            ("Dog Belly Band Male", "dog+belly+band+male+incontinence"),
            ("Dog Washable Pee Pads", "dog+washable+pee+pads+reusable"),
        ],
        "faq": [
            ("What are the signs of a UTI in dogs?", "Signs include frequent urination, straining to urinate, blood in urine, accidents in the house, excessive licking of the genital area, foul-smelling urine, and signs of discomfort when urinating."),
            ("What causes urinary tract infections in dogs?", "UTIs are most commonly caused by bacteria entering the urethra. Risk factors include female anatomy, diabetes, Cushing's disease, bladder stones, urinary incontinence, weakened immune system, and infrequent urination."),
            ("Can dog UTIs clear up on their own?", "UTIs in dogs typically require antibiotic treatment prescribed by a vet. Untreated UTIs can progress to kidney infections, which are serious and potentially life-threatening. Always seek veterinary diagnosis and treatment."),
            ("How much does UTI treatment cost for dogs in the UK?", "A vet consultation plus urinalysis typically costs £50-£100. Antibiotics may cost £20-£50. If further diagnostics (ultrasound, culture) are needed, costs increase to £200-£400. Recurrent UTIs require more extensive investigation."),
            ("Can cranberry supplements prevent UTIs in dogs?", "Some evidence suggests cranberry supplements may help prevent bacterial adhesion to the bladder wall, but evidence in dogs is limited. They should not replace veterinary treatment for active infections. Consult your vet before using."),
        ],
    },
    {
        "title": "Understanding Canine Cancer: Early Detection Guide",
        "slug": "canine-cancer-early-detection-guide",
        "pexels": "dog vet examination check up",
        "excerpt": "A guide to understanding cancer in dogs, recognising warning signs early, and navigating diagnosis and treatment options.",
        "amazon_products": [
            ("Dog Health Record Book", "dog+health+record+book+journal"),
            ("Dog Supplement Cancer Support", "dog+supplement+immune+support+antioxidant"),
            ("Elevated Dog Food Bowl", "elevated+dog+food+bowl+stand"),
            ("Dog Comfort Blanket Soft", "dog+comfort+blanket+soft+washable"),
            ("Dog Gentle Grooming Brush", "dog+gentle+grooming+brush+soft"),
        ],
        "faq": [
            ("What are the early signs of cancer in dogs?", "Warning signs include lumps or bumps that grow or change, wounds that don't heal, unexplained weight loss, loss of appetite, difficulty eating or swallowing, bleeding or discharge, persistent lameness, difficulty breathing, and changes in bathroom habits."),
            ("How common is cancer in dogs?", "Cancer is the leading cause of death in dogs over 10 years old. Approximately 1 in 4 dogs will develop cancer at some point. Some breeds have higher predisposition, but cancer can affect any dog regardless of breed."),
            ("Which dog breeds are most prone to cancer?", "Golden Retrievers, Boxers, Bernese Mountain Dogs, Rottweilers, German Shepherds, and Flat-Coated Retrievers have higher cancer rates. However, mixed-breed dogs are also susceptible."),
            ("How is cancer treated in dogs in the UK?", "Treatment options include surgery, chemotherapy, radiation therapy, immunotherapy, and palliative care. Treatment choice depends on cancer type, stage, and location. UK veterinary oncologists provide specialised care at referral centres."),
            ("How much does cancer treatment cost for dogs in the UK?", "Costs vary enormously. Surgery may cost £1,000-£5,000+. Chemotherapy protocols typically cost £2,000-£8,000 for a full course. Radiation therapy can cost £3,000-£8,000. Pet insurance can significantly help manage these costs."),
        ],
    },
    {
        "title": "How to Care for a Dog with Arthritis in Winter",
        "slug": "care-dog-arthritis-winter",
        "pexels": "dog winter coat cold weather",
        "excerpt": "Practical winter care tips for dogs with arthritis, keeping them comfortable, mobile, and pain-free during colder months.",
        "amazon_products": [
            ("Dog Arthritis Supplement Glucosamine", "dog+arthritis+supplement+glucosamine"),
            ("Dog Winter Coat Waterproof", "dog+winter+coat+waterproof+warm"),
            ("Dog Heated Bed", "dog+heated+bed+arthritis"),
            ("Dog Non-Slip Boots", "dog+boots+non+slip+winter"),
            ("Dog Joint Support Treats", "dog+joint+support+treats"),
        ],
        "faq": [
            ("Why is arthritis worse in dogs during winter?", "Cold weather causes muscles and tissues to contract, reducing flexibility around already compromised joints. Reduced activity in winter leads to stiffness, and drops in barometric pressure may increase joint inflammation."),
            ("How can I keep my arthritic dog comfortable in winter?", "Provide a warm, orthopaedic bed away from draughts, use a dog coat on walks, keep walks shorter but more frequent, warm up gently before exercise, maintain a consistent indoor temperature, and consider ramps for getting in/out of cars."),
            ("Should I reduce walks for my arthritic dog in winter?", "Don't eliminate walks — keep your dog moving with shorter, more frequent walks on flat, non-slippery surfaces. Cold muscles are prone to injury, so start with a gentle warm-up. Avoid icy or uneven terrain."),
            ("What supplements help dogs with arthritis?", "Evidence-based supplements include glucosamine and chondroitin, omega-3 fatty acids (fish oil), green-lipped mussel extract, and turmeric (curcumin). Always discuss supplements with your vet, especially if your dog takes other medications."),
            ("Can physiotherapy help arthritic dogs?", "Yes, canine physiotherapy and hydrotherapy can significantly benefit arthritic dogs. Warm-water hydrotherapy is particularly effective, providing low-impact exercise that strengthens muscles and improves joint mobility without stressing joints."),
        ],
    },
    {
        "title": "Dog Breathing Problems: When to Worry",
        "slug": "dog-breathing-problems-when-to-worry",
        "pexels": "dog panting breathing heavy",
        "excerpt": "Learn to distinguish normal panting from concerning breathing issues in dogs and know when to seek emergency veterinary care.",
        "amazon_products": [
            ("Dog Cooling Mat", "dog+cooling+mat+summer"),
            ("Dog Harness Front Clip", "dog+harness+front+clip+no+pull"),
            ("Pet Oxygen Mask Emergency", "pet+oxygen+mask+first+aid"),
            ("Dog Calm Supplement Breathing", "dog+calming+supplement"),
            ("Dog Humidifier Pet Safe", "humidifier+pet+safe+quiet"),
        ],
        "faq": [
            ("What is normal breathing for a dog?", "Normal resting respiratory rate for dogs is 10-30 breaths per minute. Panting after exercise or in warm weather is normal. At rest, breathing should be quiet and effortless, with no visible straining or unusual sounds."),
            ("When should I worry about my dog's breathing?", "Seek veterinary attention for persistent panting at rest, laboured breathing, open-mouth breathing, blue or purple gums, gasping, wheezing, persistent coughing, rapid breathing without cause, and any breathing that seems painful or distressed."),
            ("What causes breathing difficulties in dogs?", "Causes include heart disease, pneumonia, allergies, tracheal collapse, laryngeal paralysis, brachycephalic syndrome, foreign body aspiration, lung tumours, anaemia, pain, anxiety, and heatstroke."),
            ("Are certain dog breeds more prone to breathing problems?", "Brachycephalic (flat-faced) breeds like Bulldogs, Pugs, French Bulldogs, Boston Terriers, and Pekingese are most prone due to their shortened airways. Large breeds are more susceptible to laryngeal paralysis."),
            ("What should I do if my dog is having trouble breathing?", "Keep your dog calm, ensure good air circulation, remove any collar or tight clothing, keep the environment cool, and transport to the vet immediately. Breathing emergencies can deteriorate rapidly and require urgent professional care."),
        ],
    },
    {
        "title": "How to Keep Senior Dogs Active and Comfortable",
        "slug": "keep-senior-dogs-active-comfortable",
        "pexels": "senior old dog walking gentle",
        "excerpt": "Comprehensive guide to maintaining quality of life for ageing dogs through appropriate exercise, nutrition, and home adaptations.",
        "amazon_products": [
            ("Senior Dog Joint Supplement", "senior+dog+joint+supplement"),
            ("Dog Ramp Stairs Bed", "dog+ramp+stairs+bed+couch"),
            ("Senior Dog Food High Quality", "senior+dog+food+high+quality"),
            ("Dog Non-Slip Floor Mat", "dog+non+slip+floor+mat"),
            ("Dog Supportive Harness Senior", "dog+support+harness+senior+lifting"),
        ],
        "faq": [
            ("At what age is a dog considered senior?", "Small breeds (under 10kg) are senior at 10-12 years, medium breeds at 8-10 years, large breeds at 6-8 years, and giant breeds at 5-6 years. Age-related changes can begin before these milestones."),
            ("How much exercise does a senior dog need?", "Senior dogs still need daily exercise, but adjust intensity and duration. Two to three shorter walks of 15-20 minutes are often better than one long walk. Watch for signs of fatigue and allow rest when needed."),
            ("What should I feed my senior dog?", "Senior dogs typically need fewer calories but maintained protein levels to preserve muscle mass. Look for senior-specific diets with joint-supporting ingredients, easily digestible proteins, and appropriate fibre levels."),
            ("How can I make my home more comfortable for a senior dog?", "Add non-slip rugs on hard floors, provide ramps for furniture and cars, use raised food and water bowls, ensure easy access to outdoor areas, provide orthopaedic bedding, maintain warm indoor temperatures, and add night lights."),
            ("When should I take my senior dog to the vet?", "Senior dogs should have veterinary check-ups every 6 months rather than annually. Seek prompt attention for changes in appetite, water intake, mobility, behaviour, bathroom habits, or any new lumps, bumps, or symptoms."),
        ],
    },
    {
        "title": "Understanding Food Sensitivities vs Food Allergies in Dogs",
        "slug": "food-sensitivities-vs-food-allergies-dogs",
        "pexels": "dog food bowl nutrition healthy",
        "excerpt": "Learn the difference between food allergies and food sensitivities in dogs, how to identify triggers, and manage dietary needs.",
        "amazon_products": [
            ("Dog Hypoallergenic Food", "dog+hypoallergenic+food"),
            ("Dog Allergy Test Kit", "dog+allergy+test+kit"),
            ("Dog Limited Ingredient Diet", "dog+limited+ingredient+diet+food"),
            ("Dog Food Storage Container", "dog+food+storage+container+airtight"),
            ("Dog Slow Feeder Bowl", "dog+slow+feeder+bowl+anti+bloat"),
        ],
        "faq": [
            ("What is the difference between a food allergy and food sensitivity in dogs?", "Food allergies involve an immune system response (IgE-mediated) causing symptoms like itching, hives, and facial swelling. Food sensitivities (intolerances) are non-immune reactions causing primarily digestive symptoms like vomiting, diarrhoea, and gas."),
            ("What are the most common food allergens for dogs?", "The most common canine food allergens are beef, dairy, chicken, wheat, soy, and lamb. Contrary to popular belief, grains are rarely the primary allergen — animal proteins are more commonly responsible."),
            ("How do I find out what food my dog is allergic to?", "The gold standard is an elimination diet trial lasting 8-12 weeks, feeding a novel protein or hydrolysed diet, then reintroducing foods individually. Blood and saliva allergy tests for dogs have limited reliability."),
            ("Can food allergies develop at any age in dogs?", "Yes, food allergies can develop at any age, even to foods your dog has eaten for years without problems. Most dogs develop food allergies between 1-5 years of age, but it can occur in puppies or seniors too."),
            ("What should I feed a dog with food allergies?", "Options include novel protein diets (using a protein your dog hasn't eaten before, such as venison or duck), hydrolysed protein diets (where proteins are broken down to avoid triggering reactions), and carefully managed home-prepared diets under veterinary nutritionist guidance."),
        ],
    },
    {
        "title": "How to Create a Wellness Plan for Your Dog",
        "slug": "create-wellness-plan-for-dog",
        "pexels": "happy healthy dog outdoors park",
        "excerpt": "Build a comprehensive annual wellness plan for your dog covering preventive care, nutrition, exercise, and health monitoring.",
        "amazon_products": [
            ("Dog Health Journal Record", "dog+health+journal+record+book"),
            ("Dog Grooming Kit Complete", "dog+grooming+kit+complete"),
            ("Dog First Aid Kit", "dog+first+aid+kit+uk"),
            ("Dog Activity Tracker", "dog+activity+tracker+fitness"),
            ("Dog Dental Care Kit", "dog+dental+care+kit+toothbrush"),
        ],
        "faq": [
            ("What should a dog wellness plan include?", "A comprehensive wellness plan covers vaccination schedules, parasite prevention, dental care, nutrition, exercise, weight monitoring, grooming, mental enrichment, senior health screening, and emergency preparedness."),
            ("How often should a healthy dog see the vet?", "Healthy adult dogs should have annual check-ups. Puppies need more frequent visits for vaccinations. Senior dogs (over 7-8 years) benefit from biannual check-ups to catch age-related conditions early."),
            ("How much does annual preventive care cost for a dog in the UK?", "Annual preventive care including vaccinations, flea/worming treatments, and a check-up typically costs £200-£400. Dental cleaning adds £200-£400. Pet health plans from many practices spread costs into monthly payments of £10-£30."),
            ("Should I get pet insurance as part of my dog's wellness plan?", "Pet insurance is strongly recommended as veterinary costs for accidents and illnesses can be substantial. Lifetime policies offer the best coverage. Insure early before any pre-existing conditions develop."),
            ("What parasite prevention does my dog need year-round?", "UK dogs need year-round flea treatment, regular worming (at least every 3 months for adults), and tick prevention, especially if walking in rural areas. Lungworm prevention is increasingly important — ask your vet about monthly preventatives."),
        ],
    },
]

def amazon_link(search_term):
    """Generate Amazon UK affiliate link."""
    return f"https://www.amazon.co.uk/s?k={search_term}&tag={AMAZON_TAG}"

def generate_post_content(topic, index):
    """Generate full Gutenberg-format post content for a topic."""
    title = topic["title"]
    slug = topic["slug"]
    excerpt = topic["excerpt"]
    products = topic["amazon_products"]
    faqs = topic["faq"]

    # Build FAQ JSON-LD
    faq_entities = []
    for q, a in faqs:
        faq_entities.append({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": a
            }
        })
    faq_schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faq_entities
    }, indent=2)

    # Build sections based on topic
    sections = _build_sections(topic, index)

    # Build product comparison table
    comparison_table = _build_comparison_table(products)

    # Build product recommendations
    product_section = _build_product_section(products)

    # Build FAQ HTML
    faq_html = _build_faq_html(faqs)

    # Build glossary
    glossary = _build_glossary(topic)

    # Assemble full content
    content = f"""<!-- wp:html -->
<script type="application/ld+json">
{faq_schema}
</script>
<!-- /wp:html -->

<!-- wp:group {{"style":{{"border":{{"width":"2px","color":"#2e7d32","radius":"8px"}},"spacing":{{"padding":{{"top":"20px","bottom":"20px","left":"20px","right":"20px"}}}}}},"backgroundColor":"pale-green"}} -->
<div class="wp-block-group has-pale-green-background-color has-background" style="border-color:#2e7d32;border-width:2px;border-radius:8px;padding-top:20px;padding-bottom:20px;padding-left:20px;padding-right:20px">
<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">🐾 Quick Answer</h3>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>{excerpt}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->

<!-- wp:heading -->
<h2 class="wp-block-heading">Table of Contents</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
<li><a href="#overview">Overview</a></li>
<li><a href="#signs-symptoms">Key Signs and Symptoms</a></li>
<li><a href="#causes-risk">Causes and Risk Factors</a></li>
<li><a href="#prevention-care">Prevention and Care</a></li>
<li><a href="#when-to-see-vet">When to See a Vet</a></li>
<li><a href="#recommended-products">Recommended Products</a></li>
<li><a href="#comparison">Product Comparison</a></li>
<li><a href="#glossary">Key Terms / Glossary</a></li>
<li><a href="#faq">Frequently Asked Questions</a></li>
<li><a href="#sources">Sources &amp; References</a></li>
</ul>
<!-- /wp:list -->

{sections}

<!-- wp:heading {{"anchor":"recommended-products"}} -->
<h2 class="wp-block-heading" id="recommended-products">Recommended Products</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The following products may help support your dog's health in relation to this topic. All links go to Amazon UK where you can read reviews and compare options.</p>
<!-- /wp:paragraph -->

{product_section}

<!-- wp:heading {{"anchor":"comparison"}} -->
<h2 class="wp-block-heading" id="comparison">Product Comparison Table</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Here is a quick comparison of our top recommended products to help you choose the right option for your dog.</p>
<!-- /wp:paragraph -->

<!-- wp:html -->
{comparison_table}
<!-- /wp:html -->

<!-- wp:heading {{"anchor":"glossary"}} -->
<h2 class="wp-block-heading" id="glossary">Key Terms / Glossary</h2>
<!-- /wp:heading -->

{glossary}

<!-- wp:heading {{"anchor":"faq"}} -->
<h2 class="wp-block-heading" id="faq">Frequently Asked Questions</h2>
<!-- /wp:heading -->

{faq_html}

<!-- wp:heading {{"anchor":"sources"}} -->
<h2 class="wp-block-heading" id="sources">Sources &amp; References</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
<li><a href="https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/all-pets/pet-health-hub" target="_blank" rel="noopener noreferrer">PDSA Pet Health Hub</a> — Free veterinary guidance for UK pet owners</li>
<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/dogs" target="_blank" rel="noopener noreferrer">RSPCA Dog Advice</a> — Comprehensive welfare and health information</li>
<li><a href="https://www.bva.co.uk/" target="_blank" rel="noopener noreferrer">British Veterinary Association (BVA)</a> — Professional veterinary standards and guidance</li>
<li><a href="https://www.bluecross.org.uk/advice/dog" target="_blank" rel="noopener noreferrer">Blue Cross Dog Health Advice</a> — Charity-backed pet health resources</li>
<li><a href="https://www.rcvs.org.uk/" target="_blank" rel="noopener noreferrer">Royal College of Veterinary Surgeons (RCVS)</a> — UK veterinary regulatory body</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><em>Note: This article is for informational purposes only and does not replace professional veterinary advice. Always consult your vet regarding your dog's specific health needs.</em></p>
<!-- /wp:paragraph -->

<!-- wp:separator -->
<hr class="wp-block-separator has-alpha-channel-opacity"/>
<!-- /wp:separator -->

<!-- wp:group {{"style":{{"border":{{"width":"1px","color":"#e0e0e0","radius":"8px"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"16px","right":"16px"}}}}}}}} -->
<div class="wp-block-group" style="border-color:#e0e0e0;border-width:1px;border-radius:8px;padding-top:16px;padding-bottom:16px;padding-left:16px;padding-right:16px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">About the Author</h4>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>Written by the <strong>PetHub Online editorial team</strong>. Our team researches and compiles the latest pet health information from trusted UK veterinary sources to help pet owners make informed decisions about their animals' wellbeing.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->

<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Explore More Dog Health Guides</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Looking for more expert guidance on keeping your dog healthy? <a href="https://pethubonline.com/category/dog-health/">Explore our full collection of Dog Health guides on PetHub Online</a> for in-depth articles on nutrition, behaviour, grooming, and veterinary care.</p>
<!-- /wp:paragraph -->

<!-- wp:separator -->
<hr class="wp-block-separator has-alpha-channel-opacity"/>
<!-- /wp:separator -->

<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"13px"}}}}}} -->
<p style="font-size:13px"><em><strong>Affiliate Disclosure:</strong> PetHub Online is a participant in the Amazon Services LLC Associates Programme, an affiliate advertising programme designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.co.uk. When you purchase through links on this page, we may earn a small commission at no extra cost to you. We only recommend products we believe will genuinely help your pet.</em></p>
<!-- /wp:paragraph -->"""

    return content


def _build_sections(topic, index):
    """Build the main content sections for a topic."""
    title = topic["title"]

    # Topic-specific content generation
    section_content = SECTION_CONTENT[index]

    overview = section_content["overview"]
    signs = section_content["signs"]
    causes = section_content["causes"]
    prevention = section_content["prevention"]
    vet_section = section_content["vet"]

    return f"""<!-- wp:heading {{"anchor":"overview"}} -->
<h2 class="wp-block-heading" id="overview">What Every Dog Owner Should Know</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{overview[0]}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{overview[1]}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{overview[2]}</p>
<!-- /wp:paragraph -->

<!-- wp:heading {{"anchor":"signs-symptoms"}} -->
<h2 class="wp-block-heading" id="signs-symptoms">What Are the Key Signs and Symptoms?</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{signs[0]}</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
<li>{signs[1]}</li>
<li>{signs[2]}</li>
<li>{signs[3]}</li>
<li>{signs[4]}</li>
<li>{signs[5]}</li>
<li>{signs[6]}</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>{signs[7]}</p>
<!-- /wp:paragraph -->

<!-- wp:heading {{"anchor":"causes-risk"}} -->
<h2 class="wp-block-heading" id="causes-risk">What Causes This and What Are the Risk Factors?</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{causes[0]}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{causes[1]}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{causes[2]}</p>
<!-- /wp:paragraph -->

<!-- wp:heading {{"anchor":"prevention-care"}} -->
<h2 class="wp-block-heading" id="prevention-care">How Can You Prevent and Manage This?</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{prevention[0]}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{prevention[1]}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{prevention[2]}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{prevention[3]}</p>
<!-- /wp:paragraph -->

<!-- wp:heading {{"anchor":"when-to-see-vet"}} -->
<h2 class="wp-block-heading" id="when-to-see-vet">When Should You See a Vet?</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{vet_section[0]}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{vet_section[1]}</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{vet_section[2]}</p>
<!-- /wp:paragraph -->"""


def _build_comparison_table(products):
    """Build an HTML comparison table for products."""
    rows = ""
    for i, (name, search) in enumerate(products):
        link = amazon_link(search)
        rows += f'<tr><td style="padding:10px;border:1px solid #ddd;">{i+1}</td><td style="padding:10px;border:1px solid #ddd;">{name}</td><td style="padding:10px;border:1px solid #ddd;"><a href="{link}" target="_blank" rel="noopener noreferrer nofollow">View on Amazon UK</a></td></tr>\n'

    return f"""<table style="width:100%;border-collapse:collapse;margin:20px 0;">
<thead>
<tr style="background-color:#2e7d32;color:#fff;">
<th style="padding:12px;border:1px solid #ddd;text-align:left;">#</th>
<th style="padding:12px;border:1px solid #ddd;text-align:left;">Product</th>
<th style="padding:12px;border:1px solid #ddd;text-align:left;">Where to Buy</th>
</tr>
</thead>
<tbody>
{rows}</tbody>
</table>"""


def _build_product_section(products):
    """Build the recommended products section."""
    blocks = ""
    for name, search in products:
        link = amazon_link(search)
        blocks += f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">{name}</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Browse a selection of top-rated {name.lower()} on Amazon UK. Compare features, read customer reviews, and find the best option for your dog's needs.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong><a href="{link}" target="_blank" rel="noopener noreferrer nofollow">Browse {name} on Amazon UK →</a></strong></p>
<!-- /wp:paragraph -->

"""
    return blocks


def _build_faq_html(faqs):
    """Build FAQ section HTML."""
    blocks = ""
    for q, a in faqs:
        blocks += f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">{q}</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{a}</p>
<!-- /wp:paragraph -->

"""
    return blocks


def _build_glossary(topic):
    """Build glossary section based on topic."""
    index = TOPICS.index(topic)
    terms = GLOSSARY_TERMS[index]
    items = ""
    for term, definition in terms:
        items += f"<li><strong>{term}:</strong> {definition}</li>\n"
    return f"""<!-- wp:list -->
<ul class="wp-block-list">
{items}</ul>
<!-- /wp:list -->"""


# ── Section content for all 25 topics ──────────────────────────────────
SECTION_CONTENT = [
    # 0: Early Signs of Pain
    {
        "overview": [
            "Dogs are instinctively hardwired to mask pain — a survival mechanism inherited from their wild ancestors. This makes it remarkably challenging for even devoted owners to recognise when their dog is suffering. Understanding the subtle signals your dog may use to communicate discomfort is one of the most important skills you can develop as a responsible pet owner.",
            "Pain in dogs can be acute (sudden onset from injury or illness) or chronic (long-term conditions like arthritis or dental disease). Acute pain tends to produce more obvious signs like yelping or limping, while chronic pain often manifests through gradual behavioural changes that are easy to dismiss as normal ageing or personality quirks.",
            "Research published by the British Veterinary Association suggests that up to 80% of dogs over the age of 8 experience some form of chronic pain, most commonly from osteoarthritis. Early recognition and intervention can dramatically improve your dog's quality of life and may slow the progression of underlying conditions."
        ],
        "signs": [
            "Learning to spot the signs of pain in your dog requires attentive observation of their normal behaviour. Changes from their baseline behaviour patterns are often the earliest indicators. Here are the key signs to watch for:",
            "Reduced mobility or reluctance to jump, climb stairs, or walk as far as usual",
            "Changes in posture — hunched back, tucked abdomen, or holding a limb abnormally",
            "Altered facial expressions — squinting, flattened ears, or a tense muzzle",
            "Behavioural changes including withdrawal, aggression when touched, or unusual clinginess",
            "Changes in eating habits — eating more slowly, dropping food, or losing interest in meals",
            "Excessive licking, chewing, or grooming of a specific body area",
            "If you notice any combination of these signs persisting for more than 24 hours, it is worth discussing with your veterinarian. Dogs cannot tell us where it hurts, so your observations are invaluable diagnostic tools."
        ],
        "causes": [
            "Pain in dogs can stem from numerous sources. Musculoskeletal issues such as arthritis, hip dysplasia, cruciate ligament injuries, and intervertebral disc disease are among the most common causes of chronic pain. Dental disease is another extremely prevalent but frequently overlooked source of significant discomfort.",
            "Internal conditions including pancreatitis, urinary tract infections, gastrointestinal problems, and cancer can all cause pain that may not be immediately apparent from external observation. Age is a significant risk factor, with older dogs being more susceptible to painful degenerative conditions.",
            "Breed predispositions also play a role. Large and giant breeds are more prone to joint conditions, while brachycephalic breeds may experience pain related to their respiratory anatomy. Understanding your dog's breed-specific risks helps you know what to monitor for."
        ],
        "prevention": [
            "Maintaining a healthy body weight is one of the most effective ways to prevent and reduce pain in dogs. Excess weight places additional stress on joints, organs, and the cardiovascular system. Even a 10% reduction in body weight can significantly improve mobility in overweight dogs with arthritis.",
            "Regular, appropriate exercise helps maintain muscle tone that supports joints and prevents stiffness. Low-impact activities like swimming and controlled walking are excellent for dogs prone to joint problems. Avoid high-impact activities for growing puppies of large breeds.",
            "Providing supportive bedding, especially for older dogs, helps reduce pressure on joints during rest. Orthopaedic dog beds with memory foam or similar materials can make a genuine difference to your dog's comfort levels.",
            "Regular veterinary check-ups allow early detection of painful conditions before they become advanced. Your vet can assess your dog's pain levels using standardised scoring systems and recommend appropriate management strategies."
        ],
        "vet": [
            "Seek veterinary attention promptly if your dog shows sudden onset of severe pain (crying out, inability to stand, acute lameness), as this may indicate a fracture, disc disease, or other emergency. Do not administer any human pain medications — many are toxic to dogs.",
            "For gradually developing signs of pain, schedule a veterinary appointment within a few days. Bring notes about what you have observed, when changes started, and which activities seem to worsen symptoms. Video footage of concerning behaviours can be invaluable for your vet.",
            "Your veterinarian has access to safe, effective pain management options including prescription anti-inflammatory medications, opioid analgesics for severe pain, adjunctive therapies like gabapentin, and referral to canine physiotherapists or pain management specialists when needed."
        ],
    },
    # 1: Vaccination Schedules
    {
        "overview": [
            "Vaccination is one of the most important preventive health measures you can take for your dog. In the UK, core vaccinations protect against potentially fatal diseases that still circulate in the canine population. Understanding the vaccination schedule helps ensure your dog maintains optimal immunity throughout their life.",
            "The UK vaccination protocol has been refined over decades based on extensive veterinary research. The World Small Animal Veterinary Association (WSAVA) and the British Small Animal Veterinary Association (BSAVA) provide evidence-based guidelines that most UK veterinary practices follow, though individual vets may adjust timings based on local disease risk.",
            "Vaccination works by priming the immune system to recognise and fight specific pathogens. The primary course in puppies establishes initial immunity, while subsequent boosters maintain protection. Modern vaccination protocols are designed to provide maximum protection with minimum unnecessary intervention."
        ],
        "signs": [
            "Understanding which diseases vaccinations protect against helps illustrate why they are so important. Here are the key diseases covered by UK canine vaccinations:",
            "Canine Distemper — affects the respiratory, gastrointestinal, and nervous systems; often fatal",
            "Canine Parvovirus — causes severe bloody diarrhoea and vomiting; particularly dangerous for puppies",
            "Infectious Canine Hepatitis (Adenovirus) — affects the liver, kidneys, and blood vessels",
            "Leptospirosis — bacterial infection spread through contaminated water; can also infect humans (zoonotic)",
            "Kennel Cough (Bordetella/Parainfluenza) — highly contagious respiratory infection; non-core but commonly recommended",
            "Rabies — required only for dogs travelling abroad under the Pet Travel Scheme",
            "Signs that your dog may not be adequately protected include not completing the primary vaccination course, missing booster appointments by more than the recommended window, or immune-compromising conditions that may reduce vaccine effectiveness."
        ],
        "causes": [
            "Vaccine-preventable diseases persist in the UK canine population, particularly in areas with lower vaccination rates. Parvovirus remains a significant threat and can survive in the environment for months or even years. Leptospirosis is carried by rats and found in stagnant water, making it a risk for dogs who enjoy outdoor activities.",
            "Risk factors for contracting these diseases include being unvaccinated or under-vaccinated, exposure to infected dogs (kennels, dog parks, shows), contact with wildlife, and swimming in or drinking from contaminated water sources.",
            "There has been increasing concern among veterinary professionals about declining vaccination rates in some UK areas. The PDSA Animal Wellbeing (PAW) Report indicates that a significant percentage of UK dogs are not receiving regular vaccinations, creating potential gaps in population-level immunity."
        ],
        "prevention": [
            "Follow the standard UK puppy vaccination schedule: first vaccination at 6-8 weeks, second at 10-12 weeks, with some practices adding a third dose at 14-16 weeks. Your puppy should not walk in public areas until 1-2 weeks after the final primary vaccination.",
            "Annual health checks with your vet should include a review of vaccination status. Core vaccines (DHP — distemper, hepatitis, parvovirus) typically need boosting every 3 years after the first annual booster, while leptospirosis requires annual vaccination due to shorter-lasting immunity.",
            "Keep a record of all vaccinations in your dog's health booklet. This documentation is essential for boarding kennels, doggy daycare, training classes, and international pet travel. Most veterinary practices also maintain digital records.",
            "If your dog's vaccinations have lapsed, consult your vet about restarting the course. Depending on how long ago the last vaccination was given, your dog may need a full primary course again rather than just a booster."
        ],
        "vet": [
            "Discuss your dog's individual risk factors with your vet to determine the optimal vaccination schedule. Dogs that spend time in kennels, attend shows, or live in rural areas near waterways may need more comprehensive protection than urban dogs with minimal contact with other animals.",
            "Mild side effects after vaccination (slight lethargy, mild swelling at the injection site, reduced appetite for 24-48 hours) are normal and typically resolve without treatment. Contact your vet if side effects are severe or persist beyond 48 hours.",
            "In rare cases, dogs may have adverse reactions to vaccines. Your vet can discuss the very low risks versus the significant benefits of vaccination. Dogs with a history of vaccine reactions may need modified protocols or pre-treatment."
        ],
    },
    # 2: Monitor Weight at Home
    {
        "overview": [
            "Maintaining a healthy weight is one of the most impactful things you can do for your dog's long-term health. Studies show that lean dogs live on average 1.8 years longer than their overweight counterparts. Yet the PDSA estimates that over a third of UK dogs are overweight or obese, making canine obesity one of the most prevalent welfare issues in the country.",
            "Regular weight monitoring at home allows you to catch gradual weight changes early, before they become significant health problems. Weight gain in dogs tends to be incremental — a few hundred grams per month can add up to significant excess weight over a year without owners noticing.",
            "Beyond the number on the scale, learning to assess your dog's body condition gives you a hands-on method to evaluate their fitness at any time. Combining regular weighing with body condition scoring provides a complete picture of your dog's physical health."
        ],
        "signs": [
            "Recognising whether your dog is at a healthy weight involves both visual assessment and physical examination. Here are the key indicators to evaluate:",
            "Ribs should be easily felt without pressing hard but not prominently visible (except in naturally lean breeds like Whippets)",
            "A clear waist should be visible when viewing your dog from above — the body should taper behind the ribs",
            "A noticeable tummy tuck should be present when viewed from the side — the abdomen should rise from the ribcage towards the hind legs",
            "Your dog should move freely without excessive waddling, panting during light exercise, or reluctance to be active",
            "The base of the tail should have a smooth covering of tissue rather than thick fat pads",
            "Hip bones should be palpable but not prominently protruding",
            "If your dog fails several of these assessments, they may be carrying excess weight. Conversely, if ribs and hip bones are highly prominent with little tissue covering, your dog may be underweight — both situations warrant veterinary attention."
        ],
        "causes": [
            "Weight gain in dogs is caused by calorie intake exceeding energy expenditure. Common contributing factors include overfeeding (including treats and table scraps), lack of exercise, neutering (which can reduce metabolic rate by up to 30%), and certain medical conditions such as hypothyroidism and Cushing's disease.",
            "Many owners underestimate how many calories treats contribute to their dog's daily intake. A single dental chew can contain 10-15% of a medium dog's daily calorie requirement. Table scraps, training treats, and chews all add up quickly.",
            "Age is also a factor, as older dogs typically have reduced metabolic rates and activity levels. Breed predisposition plays a role too — Labrador Retrievers, Beagles, Pugs, and Cavalier King Charles Spaniels are among the breeds most prone to weight gain."
        ],
        "prevention": [
            "Weigh your dog regularly using a consistent method. For small dogs, use a kitchen or bathroom scale (weigh yourself, then weigh holding the dog, and subtract). For larger dogs, consider investing in a pet platform scale or visiting your veterinary practice — most welcome you to use their scales at any time.",
            "Record weights in a log or app so you can track trends over time. A weight change of more than 5-10% from the ideal warrants investigation. Work with your vet to determine your dog's ideal weight, as breed averages may not apply to every individual.",
            "Measure food portions accurately rather than estimating. Feeding guidelines on packaging are starting points — adjust based on your dog's body condition. Consider using slow feeder bowls to extend mealtimes and improve satiety.",
            "Ensure your dog gets appropriate daily exercise for their breed, age, and fitness level. If your dog needs to lose weight, increase exercise gradually — sudden intense activity can cause injury, particularly in overweight or unfit dogs."
        ],
        "vet": [
            "Consult your vet if your dog is gaining or losing weight unexpectedly, as this can indicate underlying medical conditions. Sudden weight loss may signal conditions like diabetes, kidney disease, or cancer. Unexplained weight gain may point to hypothyroidism or Cushing's disease.",
            "Many veterinary practices run free weight clinics staffed by veterinary nurses who can help you develop a tailored weight management plan. These clinics provide regular weigh-ins, dietary advice, and encouragement — often more effective than managing weight loss alone.",
            "If your dog needs to lose weight, aim for gradual loss of 1-2% of body weight per week. Crash dieting is dangerous for dogs and can lead to hepatic lipidosis and muscle loss. Your vet can recommend appropriate calorie-controlled diets."
        ],
    },
    # 3: Canine Diabetes
    {
        "overview": [
            "Diabetes mellitus is one of the most common endocrine disorders in dogs, affecting approximately 1 in 300 dogs in the UK. The condition occurs when the body cannot produce sufficient insulin (Type 1, most common in dogs) or cannot respond to insulin effectively. Without treatment, diabetes can lead to serious complications including cataracts, ketoacidosis, and organ damage.",
            "The good news is that canine diabetes can be managed very effectively with proper treatment. Most diabetic dogs can live long, comfortable lives with appropriate insulin therapy, dietary management, and regular monitoring. Understanding the condition empowers you to provide the best care.",
            "Early diagnosis significantly improves outcomes. The classic symptoms of diabetes — increased thirst, frequent urination, weight loss despite good appetite, and lethargy — should prompt a veterinary visit. A simple blood and urine test can confirm the diagnosis."
        ],
        "signs": [
            "Diabetes in dogs develops gradually, and recognising the early signs allows for prompt treatment. Here are the key symptoms to watch for:",
            "Increased thirst (polydipsia) — your dog may drain their water bowl more frequently or seek water from unusual sources",
            "Frequent urination (polyuria) — you may notice more toilet breaks, larger puddles, or house-training accidents in previously reliable dogs",
            "Weight loss despite normal or increased appetite — the body cannot utilise glucose properly, so it breaks down fat and muscle for energy",
            "Lethargy and reduced activity levels — cells starved of glucose have less energy available",
            "Cloudy eyes — diabetic cataracts can develop rapidly, sometimes within weeks of diagnosis",
            "Recurrent urinary tract infections — high glucose in urine creates an ideal environment for bacterial growth",
            "If these signs progress without treatment, more serious symptoms may develop including vomiting, loss of appetite, weakness, and a distinctive sweet or fruity breath odour — this indicates diabetic ketoacidosis, which is a veterinary emergency."
        ],
        "causes": [
            "Type 1 diabetes (insulin-dependent) is the most common form in dogs, caused by immune-mediated destruction of the insulin-producing beta cells in the pancreas. Unlike in humans, Type 2 diabetes is rare in dogs. The immune system attacks and destroys the cells that make insulin, leading to absolute insulin deficiency.",
            "Risk factors include genetics (certain breeds are predisposed), obesity, pancreatitis (which can damage insulin-producing cells), Cushing's disease, and certain medications including long-term steroid use. Female dogs are approximately twice as likely to develop diabetes as males, particularly unspayed females.",
            "Breeds with higher diabetes risk include Samoyeds, Australian Terriers, Miniature Schnauzers, Miniature and Toy Poodles, Pugs, and Bichon Frises. However, any breed can be affected. Diabetes most commonly develops in middle-aged to older dogs (7-9 years)."
        ],
        "prevention": [
            "While genetic predisposition to diabetes cannot be prevented, you can reduce modifiable risk factors. Maintaining a healthy weight through appropriate diet and exercise is crucial, as obesity increases insulin resistance and stresses the pancreas.",
            "Feeding a consistent, high-quality diet at regular mealtimes helps maintain stable blood glucose levels. Avoid sudden dietary changes and limit high-sugar treats. Diets rich in complex carbohydrates and fibre help slow glucose absorption.",
            "Spaying female dogs may reduce diabetes risk, as the hormonal fluctuations during the heat cycle can interfere with insulin function. Discuss the optimal timing of spaying with your vet.",
            "Regular veterinary check-ups that include blood glucose screening (especially for at-risk breeds and older dogs) enable early detection when the condition is easiest to manage."
        ],
        "vet": [
            "If you notice the classic symptoms of increased thirst, urination, and weight loss, book a veterinary appointment as soon as possible. Diagnosis involves blood tests (showing elevated glucose) and urinalysis (showing glucose in the urine). Your vet may run additional tests to rule out other conditions and check for complications.",
            "Once diagnosed, your vet will prescribe insulin injections (typically given twice daily at mealtimes) and recommend a suitable diet. The initial stabilisation period requires close monitoring with regular blood glucose curves to find the right insulin dose.",
            "Diabetic dogs need regular veterinary monitoring, typically every 3-6 months once stable, to check glucose control and screen for complications such as cataracts, urinary infections, and kidney issues. Your vet may also teach you to monitor blood glucose at home using a pet glucometer."
        ],
    },
    # 4: Heart Health
    {
        "overview": [
            "Heart disease affects approximately 10% of all dogs, with prevalence increasing significantly in older animals. In the UK, the most common forms are mitral valve disease (particularly in small breeds) and dilated cardiomyopathy (more common in large breeds). Understanding how to support your dog's cardiovascular health can help prevent disease or slow its progression.",
            "The heart is a tireless muscle that pumps blood carrying oxygen and nutrients throughout your dog's body. When heart function is compromised, every organ system can be affected. The good news is that many heart conditions can be managed effectively when caught early, allowing dogs to maintain good quality of life for years.",
            "Heart disease in dogs is often categorised as congenital (present from birth) or acquired (developing later in life). Acquired heart disease is far more common and is the focus of most preventive care efforts."
        ],
        "signs": [
            "Heart disease can be silent in its early stages, making regular veterinary check-ups essential. However, as the condition progresses, the following signs may become apparent:",
            "A persistent cough, particularly at night or after rest — caused by fluid accumulation in or around the lungs",
            "Exercise intolerance — becoming tired more quickly during walks or play than previously",
            "Rapid or laboured breathing, even at rest — an increased resting respiratory rate is an early indicator of heart failure",
            "Fainting or collapsing episodes (syncope) — caused by irregular heart rhythms or inadequate blood flow to the brain",
            "Swollen abdomen (ascites) — fluid accumulation due to right-sided heart failure",
            "Restlessness at night or difficulty settling — dogs may struggle to find a comfortable position for breathing",
            "If you notice any of these signs, veterinary evaluation is important. Monitoring your dog's resting respiratory rate at home (counting breaths per minute while they sleep) is a valuable tool — normal is under 30 breaths per minute. Consistently higher rates may indicate early heart failure."
        ],
        "causes": [
            "Mitral valve disease (MVD) is the single most common heart condition in dogs, accounting for roughly 75% of cases. The mitral valve between the left atrium and ventricle degenerates over time, causing it to leak. Small breeds are most commonly affected, with Cavalier King Charles Spaniels having an exceptionally high prevalence.",
            "Dilated cardiomyopathy (DCM) primarily affects large and giant breeds. The heart muscle weakens and stretches, reducing its ability to pump effectively. Dobermanns, Boxers, Great Danes, and Irish Wolfhounds are among the most commonly affected breeds. A link between grain-free diets and DCM has been investigated, though the relationship remains under study.",
            "Other causes include congenital heart defects (present from birth), heartworm disease (rare in the UK but relevant for travelling dogs), pericardial disease, and arrhythmias. Obesity, poor dental health, and chronic infection can also contribute to cardiovascular strain."
        ],
        "prevention": [
            "Maintain a healthy body weight for your dog. Obesity forces the heart to work harder to circulate blood through extra tissue. Even moderate weight loss in overweight dogs can reduce cardiovascular workload and improve heart health.",
            "Provide regular, appropriate exercise. Consistent moderate exercise strengthens the heart muscle and supports overall cardiovascular fitness. Tailor exercise to your dog's age, breed, and current fitness level — avoid sudden intense activity in unfit dogs.",
            "Feed a balanced diet rich in omega-3 fatty acids (found in fish oil), taurine, and L-carnitine — nutrients that support heart muscle function. Discuss supplementation with your vet, especially for breeds predisposed to heart disease.",
            "Good dental hygiene matters for heart health. Bacteria from dental disease can enter the bloodstream and damage heart valves (endocarditis). Regular tooth brushing and professional dental cleanings help reduce this risk."
        ],
        "vet": [
            "Regular veterinary check-ups should include heart auscultation (listening with a stethoscope). Heart murmurs are often the first sign of valve disease and can be detected before any symptoms appear. Early detection allows for monitoring and timely treatment initiation.",
            "If heart disease is suspected, your vet may recommend chest X-rays, echocardiography (heart ultrasound), ECG, and blood tests. Breeds at high risk should be screened regularly — the Kennel Club recommends annual heart screening for Cavalier King Charles Spaniels.",
            "Modern cardiac medications can significantly slow disease progression and manage symptoms. Drugs such as pimobendan, ACE inhibitors, and diuretics are commonly used. Research, including the landmark EPIC trial, has shown that early treatment of MVD with pimobendan delays the onset of heart failure by approximately 15 months."
        ],
    },
    # 5: Eye Problems
    {
        "overview": [
            "Your dog's eyes are sensitive organs that can be affected by a wide range of conditions, from minor irritations to sight-threatening diseases. Understanding common eye problems helps you recognise when something is wrong and when to seek veterinary attention. Early treatment of eye conditions is crucial — delays can sometimes lead to permanent vision loss.",
            "Dogs have several anatomical differences from human eyes, including a third eyelid (nictitating membrane) and a reflective layer (tapetum lucidum) that enhances night vision. These structures can be involved in certain eye conditions unique to dogs.",
            "Some eye conditions are breed-specific due to facial anatomy. Brachycephalic breeds (flat-faced dogs like Pugs and Bulldogs) are particularly prone to eye problems due to their shallow eye sockets and prominent eyes. Understanding your breed's specific risks helps you provide targeted preventive care."
        ],
        "signs": [
            "Eye problems in dogs can develop suddenly or gradually. Regular observation of your dog's eyes helps you notice changes early. Here are the key signs that indicate an eye problem:",
            "Redness, swelling, or inflammation of the eye or surrounding tissue",
            "Discharge — clear, white, yellow, or green — that is excessive or unusual for your dog",
            "Squinting, holding the eye partially or fully closed, or excessive blinking",
            "Cloudiness, colour change, or visible film over the eye surface",
            "Pawing or rubbing at the eye, or rubbing their face along furniture or carpet",
            "Visible third eyelid (cherry eye) — a pink or red mass appearing in the corner of the eye",
            "Any sudden change in your dog's eye appearance should be treated as urgent. Eye conditions can deteriorate rapidly — what appears as minor redness in the morning could become a serious corneal ulcer by evening. When in doubt, seek same-day veterinary attention."
        ],
        "causes": [
            "Conjunctivitis (inflammation of the conjunctiva) is the most common eye condition in dogs, caused by bacteria, viruses, allergies, or irritants. Corneal ulcers result from trauma (scratches, foreign bodies) or dry eye and can rapidly worsen if untreated.",
            "Cataracts (clouding of the lens) are common in older dogs and diabetic dogs, progressively impairing vision. Glaucoma (increased pressure within the eye) is a painful emergency that can cause rapid vision loss. Dry eye (keratoconjunctivitis sicca or KCS) occurs when tear production is insufficient.",
            "Breed-specific conditions include entropion (inward-rolling eyelids common in Shar Peis and Bulldogs), ectropion (outward-rolling eyelids in Bloodhounds and Saint Bernards), progressive retinal atrophy (PRA — inherited degeneration in many breeds), and cherry eye (prolapsed third eyelid gland, common in young Bulldogs and Beagles)."
        ],
        "prevention": [
            "Keep the hair around your dog's eyes trimmed to prevent irritation. Long facial hair can scratch the cornea and trap debris. This is particularly important for breeds like Shih Tzus, Maltese, and Old English Sheepdogs.",
            "Clean eye discharge daily using damp cotton wool — use a separate piece for each eye to avoid cross-contamination. Wipe gently from the inner corner outward. For breeds prone to tear staining, regular cleaning prevents bacterial buildup in damp fur.",
            "Protect your dog's eyes during activities that pose injury risk. Dog goggles (doggles) can protect eyes during car rides with heads out of windows, beach trips, or activities in brushy terrain.",
            "Attend regular veterinary check-ups that include eye examination. For breeds prone to hereditary eye conditions, annual eye screening through the BVA/KC Eye Scheme helps detect conditions early when treatment is most effective."
        ],
        "vet": [
            "Seek same-day veterinary attention for any sudden eye changes including squinting, significant redness, cloudiness, visible injury, or signs of pain. Eye emergencies include suspected corneal ulcers, acute glaucoma, and eye trauma. Delays in treatment can result in permanent damage.",
            "Your vet can perform diagnostic tests including fluorescein staining (to detect corneal ulcers), Schirmer tear tests (measuring tear production), tonometry (measuring eye pressure), and ophthalmoscopy (examining internal eye structures).",
            "Treatment varies by condition and may include antibiotic or anti-inflammatory eye drops, artificial tears, surgical correction of eyelid abnormalities, or referral to a veterinary ophthalmologist for advanced procedures like cataract removal or glaucoma management."
        ],
    },
    # 6: Seasonal Allergies
    {
        "overview": [
            "Seasonal allergies (atopic dermatitis) affect an estimated 10-15% of dogs in the UK, causing significant discomfort during peak pollen seasons. Unlike humans who typically experience respiratory symptoms, dogs with seasonal allergies predominantly show skin-related signs — itching, redness, and recurrent infections.",
            "Atopic dermatitis is an inflammatory skin condition caused by an overreactive immune response to environmental allergens such as pollens, mould spores, and dust mites. The condition is chronic and tends to worsen over time without management, but effective strategies exist to keep symptoms under control.",
            "Understanding the seasonal patterns of allergens in the UK helps you prepare and implement preventive measures before symptoms flare. Tree pollens peak in spring, grass pollens dominate summer, and weed pollens and mould spores are most problematic in late summer and autumn."
        ],
        "signs": [
            "Dogs with seasonal allergies display a distinct pattern of symptoms that typically worsen during specific times of year. Recognising these signs allows early intervention, which is more effective than treating established flare-ups:",
            "Intense itching, particularly around the face, ears, paws, armpits, and groin area",
            "Red, inflamed skin that may develop into rashes or hot spots",
            "Frequent ear infections — allergies are the number one cause of recurrent otitis in dogs",
            "Constant paw licking or chewing, often causing reddish-brown staining of light-coloured fur",
            "Watery eyes, sneezing, or clear nasal discharge (less common than skin signs)",
            "Hair loss in affected areas and thickened, darkened skin from chronic scratching",
            "Symptoms often follow a seasonal pattern — worsening in spring and summer for pollen allergies, or year-round for dust mite sensitivities. Keep a diary of when symptoms appear and their severity to help your vet identify specific triggers."
        ],
        "causes": [
            "Seasonal allergies in dogs are caused by an inherited tendency to develop IgE antibodies against environmental allergens. When these allergens contact the skin (which is the primary route of exposure in dogs, rather than inhalation), they trigger an inflammatory cascade that causes itching and skin damage.",
            "Common environmental allergens in the UK include timothy grass, ryegrass, birch tree pollen, dock and nettle pollen, Alternaria and Aspergillus mould spores, and house dust mites. Most allergic dogs react to multiple allergens.",
            "Breed predisposition is significant. West Highland White Terriers, Labrador Retrievers, Golden Retrievers, Staffordshire Bull Terriers, French Bulldogs, and German Shepherds are among the breeds most commonly affected. The condition typically first appears between 1-3 years of age."
        ],
        "prevention": [
            "Reduce allergen exposure by wiping your dog's paws and belly with a damp cloth or hypoallergenic wipe after every walk. This simple step removes pollen before it penetrates the skin barrier. Consider using a dog paw washer for thorough cleaning.",
            "Bathe your dog weekly during allergy season with a gentle, oatmeal-based or hypoallergenic shampoo. This removes allergens from the coat and soothes irritated skin. Leave the shampoo on for 10 minutes for maximum benefit before rinsing thoroughly.",
            "Walk during lower pollen times — early morning and late evening typically have lower pollen counts than midday. Check the Met Office pollen forecast and avoid grassy fields during high pollen days. Keep windows closed during peak pollen periods.",
            "Support skin barrier health from within by feeding a diet rich in omega-3 fatty acids or supplementing with fish oil. A strong skin barrier is more resistant to allergen penetration. Probiotics may also help modulate the immune response."
        ],
        "vet": [
            "If your dog's allergies are causing significant distress or not responding to basic management, veterinary intervention is important. Your vet can prescribe medications including Apoquel (oclacitinib), Cytopoint (lokivetmab injections), or short courses of corticosteroids to control flare-ups.",
            "For definitive diagnosis, your vet may recommend intradermal skin testing or serum allergy testing to identify specific allergens. This information can be used to formulate allergen-specific immunotherapy (desensitisation), which is the only treatment that can modify the underlying allergic response.",
            "Regular veterinary monitoring helps adjust treatment plans seasonally. Many dogs benefit from a multi-modal approach combining allergen avoidance, skin barrier support, anti-itch medication, and immunotherapy. Secondary infections (bacterial or yeast) that develop due to scratching also require appropriate treatment."
        ],
    },
    # 7: Hip Dysplasia
    {
        "overview": [
            "Hip dysplasia is one of the most common orthopaedic conditions in dogs, particularly affecting medium to large breeds. It occurs when the hip joint develops abnormally, with the ball and socket not fitting together properly. This leads to joint laxity, inflammation, and eventually osteoarthritis, causing pain and reduced mobility.",
            "The condition has a strong genetic component but is also influenced by environmental factors including growth rate, nutrition, exercise patterns, and body weight. This means that while breeding from hip-scored parents reduces risk, management of environmental factors during growth is equally important.",
            "Hip dysplasia can range from mild (detectable only on X-ray with no clinical signs) to severe (causing significant lameness and pain from a young age). Understanding the condition allows you to take preventive measures for at-risk puppies and manage the condition effectively if it develops."
        ],
        "signs": [
            "Hip dysplasia can present differently depending on the dog's age and severity of the condition. Puppies may show different signs than adult dogs. Here are the key indicators to watch for:",
            "Bunny-hopping gait — running with both hind legs moving together rather than alternating",
            "Difficulty rising from a lying or sitting position, particularly noticeable after rest",
            "Reluctance to climb stairs, jump into cars, or engage in vigorous play",
            "Audible clicking or grinding from the hip joint during movement",
            "Decreased range of motion in the hind legs and reduced muscle mass in the thighs",
            "Shifting weight to the front legs (noticeable by enlarged shoulder muscles relative to hindquarters)",
            "In puppies (typically 5-12 months), signs include intermittent hind leg lameness, reluctance to exercise, and pain when the hip is manipulated. In adult dogs, chronic osteoarthritis develops gradually, causing progressive stiffness and lameness that worsens with activity and cold weather."
        ],
        "causes": [
            "Genetics is the primary factor in hip dysplasia. Multiple genes are involved, making it a polygenic condition that cannot be predicted with certainty from parentage alone. The BVA/KC Hip Dysplasia Scheme scores breeding dogs' hips via X-ray, with lower scores indicating better hip conformation. Always check hip scores of both parents when buying a puppy from a predisposed breed.",
            "Rapid growth in puppies — caused by over-feeding, excessive calorie intake, or calcium supplementation — can worsen hip dysplasia. Growing joints are vulnerable, and excess body weight during development places abnormal forces on forming hip joints. Large-breed puppy diets are specifically formulated to support controlled growth.",
            "Inappropriate exercise during growth also contributes. Activities that place high impact on developing joints — jumping, running on hard surfaces, excessive stair climbing — can exacerbate genetic predisposition. However, moderate, controlled exercise supports normal joint development."
        ],
        "prevention": [
            "If purchasing a breed prone to hip dysplasia, ensure both parents have been hip-scored through the BVA/KC scheme with scores below the breed median. Responsible breeders are transparent about hip scores and will provide documentation.",
            "Feed large-breed puppies an appropriate growth diet that supports controlled, steady growth rather than rapid weight gain. Avoid free-feeding (leaving food out all day) and do not supplement with calcium unless directed by a vet. Aim for a lean body condition throughout growth.",
            "Follow the 5-minute rule for puppy exercise — approximately 5 minutes of structured exercise per month of age, twice daily. Avoid high-impact activities (jumping, excessive stair use, running on hard surfaces) until growth plates have closed (typically 12-18 months depending on breed).",
            "Maintain a lean body weight throughout your dog's life. Research shows that keeping dogs lean from puppyhood significantly reduces the severity and progression of hip dysplasia. Even in dogs with genetic predisposition, weight management is the single most impactful intervention."
        ],
        "vet": [
            "If you notice signs of hip dysplasia, seek veterinary assessment. Early diagnosis allows for more treatment options and better long-term outcomes. Your vet can perform orthopaedic examination and X-rays to assess hip joint conformation and any arthritic changes.",
            "Conservative management includes weight control, controlled exercise, physiotherapy, hydrotherapy, anti-inflammatory medications, and joint supplements (glucosamine, chondroitin, omega-3 fatty acids). Many dogs respond well to multimodal conservative management and maintain good quality of life.",
            "Surgical options are available for cases that don't respond adequately to conservative management. Options include juvenile pubic symphysiodesis (for very young puppies), triple pelvic osteotomy (for young dogs without arthritis), femoral head ostectomy (removing the ball of the joint), and total hip replacement (the gold standard for severe cases)."
        ],
    },
    # 8: Dog Epilepsy
    {
        "overview": [
            "Epilepsy is the most common chronic neurological condition in dogs, affecting an estimated 0.5-5% of the canine population. Idiopathic epilepsy — where no underlying cause can be identified — is the most frequent diagnosis, believed to have a genetic basis. Living with an epileptic dog can be daunting, but with proper management, most epileptic dogs lead happy, fulfilling lives.",
            "A seizure occurs when there is abnormal electrical activity in the brain, causing temporary disruption to normal neurological function. Seizures can range from mild, barely noticeable episodes (focal seizures) to dramatic full-body convulsions (generalised tonic-clonic seizures). Understanding seizure types helps you describe episodes accurately to your vet.",
            "Epilepsy management is a partnership between you and your veterinarian. Your detailed observations of seizure frequency, duration, and character are essential for optimising treatment. With appropriate medication, many epileptic dogs achieve significant seizure reduction or even complete seizure freedom."
        ],
        "signs": [
            "Recognising seizure activity is important for timely management. Seizures typically progress through distinct phases. Here are the key things to observe:",
            "Pre-ictal phase (aura) — restlessness, clinginess, whining, staring, or hiding that may occur minutes to hours before a seizure",
            "Tonic phase — sudden stiffening of the body, often with the dog falling to their side",
            "Clonic phase — rhythmic paddling or jerking of the limbs, often accompanied by jaw chomping and drooling",
            "Loss of consciousness, involuntary urination or defecation during the seizure",
            "Post-ictal phase — confusion, disorientation, temporary blindness, pacing, excessive hunger or thirst lasting minutes to hours after the seizure",
            "Focal seizures — twitching of one body part, sudden unusual behaviour, fly-biting movements, or brief staring episodes without full-body involvement",
            "Keep a seizure diary recording the date, time, duration, description, and any potential triggers for each episode. This information is invaluable for your vet in adjusting medication and assessing treatment effectiveness."
        ],
        "causes": [
            "Idiopathic epilepsy (no identifiable cause) is the most common form, typically first appearing between 6 months and 6 years of age. It is believed to have a genetic basis, with certain breeds showing higher prevalence including Border Collies, Labrador Retrievers, German Shepherds, Beagles, and Belgian Shepherds.",
            "Structural epilepsy is caused by identifiable brain abnormalities including brain tumours, encephalitis (brain inflammation), head trauma, or stroke. These causes are more likely when seizures first occur in dogs under 6 months or over 6 years old.",
            "Reactive seizures are triggered by factors outside the brain, such as liver disease (hepatic encephalopathy), low blood sugar (hypoglycaemia), electrolyte imbalances, or toxin exposure. Identifying and treating the underlying cause can resolve these seizures."
        ],
        "prevention": [
            "While idiopathic epilepsy cannot be prevented, you can reduce seizure triggers and optimise management. Maintain consistent daily routines — regular feeding times, exercise schedules, and sleep patterns. Sudden changes in routine can lower seizure thresholds in susceptible dogs.",
            "Administer anti-epileptic medication (AEDs) at exactly the same times every day. Never skip doses or abruptly stop medication, as this can trigger severe breakthrough seizures or status epilepticus (a life-threatening continuous seizure). Set phone alarms as reminders.",
            "Minimise stress where possible, as stress is a common seizure trigger. Provide a calm environment during known stressors (fireworks, thunderstorms, visitors). Consider calming supplements or pheromone diffusers as adjunctive support.",
            "Avoid known seizure triggers for your individual dog. Common triggers include overexcitement, overtiredness, flashing lights, certain sounds, and temperature extremes. Your seizure diary will help identify patterns specific to your dog."
        ],
        "vet": [
            "Seek emergency veterinary attention if a seizure lasts longer than 5 minutes (status epilepticus), if your dog has multiple seizures within 24 hours (cluster seizures), or if your dog does not return to normal consciousness between seizures. These are veterinary emergencies requiring immediate treatment.",
            "Diagnosis of epilepsy involves ruling out other causes of seizures through blood tests, neurological examination, and potentially MRI and cerebrospinal fluid analysis. Your vet may refer to a veterinary neurologist for complex cases.",
            "Common anti-epileptic medications for dogs include phenobarbitone (the most commonly used first-line AED in the UK), imepitoin, potassium bromide, and levetiracetam. Regular blood monitoring is essential to ensure medication levels remain therapeutic and to check liver function."
        ],
    },
    # 9: Ear Infections
    {
        "overview": [
            "Ear infections (otitis) are one of the top reasons dogs visit the veterinarian in the UK. The canine ear canal is L-shaped, creating a warm, dark, moist environment that can harbour bacteria and yeast. Dogs with floppy ears, narrow ear canals, or allergies are particularly susceptible to recurrent infections.",
            "Ear infections are categorised by location: otitis externa (outer ear canal — most common), otitis media (middle ear), and otitis interna (inner ear — least common but most serious). While outer ear infections are usually straightforward to treat, neglected infections can progress deeper, causing more severe problems including hearing loss and balance issues.",
            "Understanding the underlying cause of ear infections is crucial for long-term management. Simply treating the infection without addressing the root cause — whether allergies, anatomy, or moisture — leads to frustrating cycles of recurrence."
        ],
        "signs": [
            "Ear infections can cause significant discomfort. Dogs typically show obvious signs that alert owners to the problem. Here are the key symptoms:",
            "Head shaking — frequent, vigorous shaking that is clearly beyond normal behaviour",
            "Scratching or pawing at the affected ear, sometimes causing self-inflicted wounds",
            "Redness, swelling, or warmth of the ear flap or visible canal opening",
            "Discharge — brown, yellow, or black material with an unpleasant or yeasty odour",
            "Pain response when the ear is touched — flinching, pulling away, or snapping",
            "Head tilt towards the affected side, particularly with middle or inner ear infections",
            "In severe or chronic cases, you may notice thickened, narrowed ear canals, hearing loss, balance problems, or facial nerve paralysis (drooping lip or eyelid on the affected side). These signs indicate the infection has progressed and requires urgent veterinary attention."
        ],
        "causes": [
            "Primary causes that initiate ear infections include allergies (the single most common underlying factor), parasites (ear mites, especially in puppies), foreign bodies (grass seeds are particularly common in summer), and hormonal conditions (hypothyroidism, Cushing's disease).",
            "Perpetuating factors that maintain or worsen infections include bacteria (Staphylococcus, Pseudomonas), yeast (Malassezia), ear canal changes (thickening, narrowing, calcification from chronic inflammation), and ruptured eardrums allowing middle ear involvement.",
            "Predisposing factors include breed anatomy (Cocker Spaniels, Basset Hounds, Springer Spaniels have pendulous ears that trap moisture), excessive ear hair (Poodles, Schnauzers), swimming, and excessive cleaning. Any factor that disrupts the ear's natural self-cleaning mechanism can predispose to infection."
        ],
        "prevention": [
            "Regular ear cleaning using a veterinary-approved ear cleaner helps maintain a healthy ear environment. Apply the cleaner, massage the base of the ear for 30 seconds, then allow your dog to shake. Wipe away visible debris with cotton wool. Never insert cotton buds into the ear canal.",
            "Dry your dog's ears thoroughly after swimming or bathing. Moisture trapped in the ear canal is a major contributor to infections. An ear drying product used after water exposure can help — ask your vet for recommendations.",
            "Address underlying allergies, as these are the most common root cause of recurrent ear infections. If your dog gets frequent ear infections, allergy testing and management may break the cycle permanently.",
            "Avoid over-cleaning — once weekly for prone dogs, fortnightly for most others, or as directed by your vet. Excessive cleaning strips natural oils and beneficial bacteria, potentially creating rather than preventing problems."
        ],
        "vet": [
            "Always seek veterinary attention for suspected ear infections rather than using over-the-counter products. Your vet needs to examine the ear canal with an otoscope, take a sample for cytology (microscopic examination), and check eardrum integrity before prescribing appropriate treatment.",
            "Treatment typically involves a thorough ear clean (which may require sedation in painful cases), followed by topical medication (antibiotic, antifungal, and/or steroid). The specific medication depends on whether the infection is bacterial, yeast, or mixed. Complete the full treatment course even if the ear appears better.",
            "For recurrent infections (3 or more per year), your vet should investigate underlying causes. This may involve allergy testing, thyroid function tests, or referral to a veterinary dermatologist. In severe chronic cases, surgical options such as total ear canal ablation (TECA) may be discussed as a last resort."
        ],
    },
    # 10: Immune System Support
    {
        "overview": [
            "Your dog's immune system is their first line of defence against infections, parasites, and disease. A well-functioning immune system identifies and destroys harmful invaders while tolerating normal body tissues and beneficial organisms. Supporting immune health through nutrition and lifestyle choices can help your dog stay healthier throughout their life.",
            "The immune system is remarkably complex, involving multiple organs, cell types, and chemical messengers working in concert. The gut plays a particularly important role, housing approximately 70% of the immune system's cells. This gut-immune connection means that digestive health and immune health are closely linked.",
            "It is important to note that 'boosting' the immune system is not always desirable — an overactive immune system causes autoimmune diseases and allergies. The goal is to support balanced, appropriate immune function rather than maximum immune activation."
        ],
        "signs": [
            "A well-functioning immune system keeps your dog healthy and resilient. Signs that immune function may be compromised include:",
            "Frequent or recurring infections — skin infections, ear infections, urinary infections that keep returning despite treatment",
            "Slow wound healing — cuts, scrapes, or surgical wounds that take longer than expected to heal",
            "Chronic lethargy or low energy levels that cannot be explained by other conditions",
            "Frequent digestive upsets — recurring diarrhoea, vomiting, or poor appetite",
            "Poor coat condition — dull, dry, brittle fur or excessive shedding",
            "Persistent or recurrent parasitic infections despite appropriate preventive treatment",
            "Conversely, an overactive immune system may manifest as allergies, autoimmune skin conditions, inflammatory bowel disease, or autoimmune haemolytic anaemia. Balancing immune function is more nuanced than simply boosting it."
        ],
        "causes": [
            "Immune function can be compromised by poor nutrition (particularly protein deficiency and lack of essential vitamins and minerals), chronic stress, inadequate sleep, obesity, lack of exercise, ageing, and certain medications (particularly long-term corticosteroid use).",
            "Underlying health conditions including Cushing's disease, diabetes, cancer, and certain viral infections can suppress immune function. Puppies and senior dogs naturally have less robust immune systems — puppies because their immune system is still developing, and seniors due to age-related immune decline (immunosenescence).",
            "Environmental factors including chemical exposure (household cleaners, pesticides, cigarette smoke), over-vaccination, chronic inflammation, and gut microbiome disruption (from antibiotics or poor diet) can also affect immune health."
        ],
        "prevention": [
            "Feed a high-quality, complete diet appropriate for your dog's life stage. Protein is essential for immune cell production, while vitamins A, C, E, and minerals zinc and selenium support immune function. A balanced commercial diet should provide all essential nutrients, but quality varies between brands.",
            "Support gut health with prebiotics (found in vegetables like sweet potato and asparagus) and probiotics (beneficial bacteria available as canine-specific supplements). A diverse, healthy gut microbiome is fundamental to strong immune function.",
            "Provide regular, moderate exercise. Research shows that regular physical activity enhances immune surveillance and reduces chronic inflammation. Avoid exhaustive exercise, which can temporarily suppress immune function.",
            "Minimise chronic stress through consistent routines, appropriate socialisation, mental enrichment, and ensuring your dog gets adequate rest. Chronic stress elevates cortisol, which suppresses immune function. A calm, enriched environment supports both mental and immune health."
        ],
        "vet": [
            "If your dog experiences recurring infections or any signs of immune dysfunction, consult your vet. Blood tests can evaluate immune cell counts, protein levels, and identify underlying conditions that may be compromising immunity.",
            "Your vet can advise on appropriate supplements for your individual dog. While many over-the-counter immune supplements are marketed for dogs, not all have scientific evidence supporting their efficacy. Your vet can recommend evidence-based options.",
            "Regular preventive care — vaccinations, parasite control, dental care, and health screenings — supports immune health by preventing infections that can overwhelm or dysregulate the immune system. Keep up with your dog's preventive care schedule."
        ],
    },
    # 11: Canine Cognitive Dysfunction
    {
        "overview": [
            "Canine Cognitive Dysfunction (CCD) is a progressive neurodegenerative condition affecting senior dogs, analogous to Alzheimer's disease in humans. It results from physical and chemical changes in the brain, including beta-amyloid plaque deposition, oxidative damage, and neuronal loss. Understanding CCD helps you recognise early signs and take steps to slow progression.",
            "CCD is significantly underdiagnosed. Many owners and even veterinarians attribute early signs to 'normal ageing,' leading to delayed intervention. Research suggests that over 50% of dogs over 11 years old show at least one sign of cognitive decline, yet fewer than 2% receive a formal CCD diagnosis.",
            "While CCD cannot be reversed, early intervention with a combination of dietary management, mental enrichment, appropriate supplements, and medication can meaningfully slow progression and maintain quality of life for longer."
        ],
        "signs": [
            "Veterinary behaviourists use the DISHAA acronym to categorise CCD symptoms. These signs develop gradually and progressively worsen. Here are the key indicators:",
            "Disorientation — getting lost in familiar environments, getting stuck in corners, going to the wrong side of doors",
            "Interaction changes — decreased interest in social interaction, failing to recognise familiar people, altered greeting behaviour",
            "Sleep-wake cycle disruption — sleeping more during the day, pacing and restlessness at night, vocalising during nighttime hours",
            "House soiling — loss of previously reliable house training, urinating or defecating indoors without signalling the need to go out",
            "Activity level changes — aimless wandering or pacing, repetitive behaviours, decreased interest in play, staring into space",
            "Anxiety — increased anxiety including separation distress, sound sensitivities, and general fearfulness that were not previously present",
            "These signs overlap with many other medical conditions (pain, sensory loss, organ disease), so a thorough veterinary examination is essential to rule out other treatable causes before diagnosing CCD."
        ],
        "causes": [
            "CCD is caused by age-related degenerative changes in the brain. Beta-amyloid plaques (similar to those found in human Alzheimer's) accumulate between neurons, disrupting communication. Oxidative stress damages brain cells over time, and cerebral blood flow may decrease with age.",
            "Neurotransmitter imbalances develop, particularly reduced dopamine and serotonin levels, which affect mood, cognition, and sleep regulation. Brain volume decreases (cerebral atrophy), particularly in the frontal lobe, which governs decision-making and learned behaviours.",
            "Risk factors include advancing age (the primary factor), genetics (some breeds may be predisposed), chronic oxidative stress, lack of mental stimulation throughout life, obesity, and possibly cardiovascular disease that reduces cerebral blood flow."
        ],
        "prevention": [
            "Provide lifelong mental stimulation through puzzle toys, training sessions, social interaction, and varied experiences. The brain follows a 'use it or lose it' principle — dogs with consistently enriched environments may develop cognitive reserve that delays CCD onset.",
            "Feed a diet rich in antioxidants (vitamins C and E, selenium, flavonoids), omega-3 fatty acids (DHA and EPA from fish oil), and medium-chain triglycerides (MCTs from coconut oil). These nutrients support brain cell health and may slow age-related cognitive decline.",
            "Maintain regular exercise appropriate for your senior dog. Physical activity promotes cerebral blood flow, supports neurogenesis (new brain cell growth), and reduces inflammation. Even gentle daily walks benefit cognitive health.",
            "Continue engaging your senior dog socially and introducing gentle novel experiences. Regular positive interactions with people and other dogs, visits to new environments, and learning simple new skills all exercise the brain and support cognitive function."
        ],
        "vet": [
            "If you notice signs of cognitive decline, schedule a veterinary appointment. Your vet will perform a thorough physical examination, blood tests, and neurological assessment to rule out other conditions that mimic CCD, such as brain tumours, pain, organ disease, or sensory loss.",
            "The medication selegiline (Selgian) is licensed for CCD treatment in dogs. It works by increasing dopamine levels in the brain. Some dogs show noticeable improvement within 2-4 weeks of starting treatment. Your vet may also recommend dietary supplements including SAMe, phosphatidylserine, and medium-chain triglycerides.",
            "Regular veterinary monitoring (every 3-6 months) helps track progression and adjust management. Discuss quality of life openly with your vet — while CCD is progressive, meaningful interventions can maintain quality of life significantly longer than no treatment."
        ],
    },
    # 12: Separation Anxiety
    {
        "overview": [
            "Separation anxiety is one of the most common behavioural problems in dogs, estimated to affect 14-20% of the UK canine population. It describes a state of extreme distress that occurs when a dog is separated from their primary attachment figure. True separation anxiety is a clinical condition — not simply a dog being naughty or poorly trained.",
            "The pandemic significantly impacted separation anxiety prevalence. Dogs acquired during lockdowns became accustomed to constant human presence, and the subsequent return to offices and normal routines triggered separation-related behaviours in many animals. This has made understanding and managing separation anxiety more important than ever.",
            "Effective management requires patience, consistency, and often professional guidance. Punishment is never appropriate — it increases anxiety and worsens the condition. The goal is to help your dog develop confidence and coping mechanisms for being alone."
        ],
        "signs": [
            "Separation anxiety behaviours occur specifically when the dog is separated from their attachment figure, or when separation is anticipated. Here are the key signs:",
            "Destructive behaviour — chewing door frames, scratching at exits, destroying household items (often items carrying the owner's scent)",
            "Excessive vocalisation — persistent barking, howling, or whining that begins shortly after the owner leaves",
            "House soiling — urinating or defecating indoors despite being fully house-trained when the owner is present",
            "Pacing, drooling, or trembling in the period leading up to the owner's departure (pre-departure anxiety)",
            "Escape attempts — scratching at doors and windows, jumping fences, sometimes causing self-injury in the process",
            "Refusal to eat — many dogs with separation anxiety will not eat treats, meals, or chews when left alone",
            "It is important to distinguish true separation anxiety from other causes of these behaviours. Boredom, insufficient exercise, incomplete house training, and noise phobias can all produce similar signs. Video recording your dog when left alone provides valuable diagnostic information."
        ],
        "causes": [
            "The exact cause of separation anxiety is not fully understood but likely involves a combination of genetic predisposition (towards anxious temperament), early life experiences (premature separation from mother, multiple rehomings), and learning (inadvertent reinforcement of clingy behaviour).",
            "Significant life changes can trigger or worsen separation anxiety, including moving house, changes in household members (new baby, bereavement, divorce), changes in the owner's work schedule, a traumatic event while alone (burglary, severe weather), or returning to work after extended time at home.",
            "Certain breeds may be predisposed to stronger attachment behaviours, though any breed can develop separation anxiety. Dogs adopted from shelters or rescue centres may be more susceptible due to past experiences of abandonment."
        ],
        "prevention": [
            "From puppyhood, gradually teach your dog that being alone is safe and normal. Start with very brief absences (seconds) and slowly increase duration. Leave a special treat or stuffed Kong that your dog only gets when alone, creating a positive association with your departure.",
            "Avoid making departures and arrivals emotionally charged. Dramatic goodbyes and excited greetings reinforce the idea that separations are significant events. Practise calm, low-key transitions.",
            "Build your dog's independence while you are home. Encourage them to settle in a separate room, reward calm behaviour when you move between rooms, and avoid allowing constant physical contact or following behaviour.",
            "Ensure your dog's physical and mental needs are met before leaving them alone. A good walk, training session, or play session before departure helps your dog settle. Leave puzzle feeders, safe chew toys, and gentle background noise (radio or TV) to occupy them."
        ],
        "vet": [
            "If your dog shows signs of separation anxiety, consult your vet first to rule out medical causes (urinary issues for house soiling, pain conditions for vocalisation). Your vet can assess severity and discuss whether medication may be appropriate alongside behaviour modification.",
            "For moderate to severe cases, anxiolytic medication (such as fluoxetine or clomipramine) may be prescribed to reduce baseline anxiety, making behaviour modification more effective. Medication is not a standalone solution — it works best when combined with a structured desensitisation programme.",
            "Your vet may recommend referral to a certified clinical animal behaviourist (CCAB or ABTC-registered in the UK) for a tailored behaviour modification plan. Professional guidance significantly improves outcomes compared to general advice alone."
        ],
    },
    # 13: Dental Care at Home
    {
        "overview": [
            "Dental disease is the most common health problem in adult dogs, with the PDSA estimating that 80% of dogs over three years old have some degree of dental disease. Yet it remains one of the most overlooked aspects of canine healthcare. Poor dental health doesn't just affect the mouth — bacteria from dental infections can spread to the heart, kidneys, and liver.",
            "The foundation of good canine dental health is regular at-home care. While professional dental cleanings under anaesthesia are sometimes necessary, establishing a daily tooth-brushing routine is the single most effective way to prevent dental disease and the costly, uncomfortable procedures it requires.",
            "Starting dental care early — ideally during puppyhood — makes the process easier for both you and your dog. However, it's never too late to begin. With patience and positive associations, most adult dogs can learn to accept tooth brushing."
        ],
        "signs": [
            "Dental disease often progresses silently, with many dogs continuing to eat normally despite significant oral pain. Knowing what to look for during regular mouth checks helps you catch problems early:",
            "Bad breath (halitosis) — while not all dog breath smells minty fresh, a foul or rotten odour indicates dental disease",
            "Yellow or brown deposits on teeth (tartar/calculus) — particularly along the gum line and on back teeth",
            "Red, swollen, or bleeding gums — healthy gums should be pink (or pigmented) and firm",
            "Difficulty eating, dropping food, or chewing on one side of the mouth",
            "Excessive drooling, pawing at the mouth, or rubbing the face on surfaces",
            "Loose, broken, or discoloured teeth visible when you lift the lips",
            "Check your dog's mouth regularly — ideally weekly. Gently lift the lips and look at the outer surfaces of the teeth and gums. Compare both sides. Any asymmetry, redness, or obvious tartar buildup warrants veterinary attention."
        ],
        "causes": [
            "Dental disease begins with plaque — a sticky biofilm of bacteria that forms on teeth within hours of eating. If not removed by brushing, plaque mineralises into tartar (calculus) within 24-48 hours. Tartar provides a rough surface for more bacteria to adhere to, creating a destructive cycle.",
            "As bacteria accumulate along and below the gum line, they cause gingivitis (gum inflammation). Untreated gingivitis progresses to periodontitis — infection and destruction of the structures supporting the teeth, including bone. This can lead to tooth loss, jaw fractures, and systemic infection.",
            "Risk factors include breed (small breeds are particularly prone due to dental crowding), diet (soft foods don't provide the mechanical cleaning action of harder diets), genetics, age, and lack of dental home care. Brachycephalic breeds often have misaligned teeth that trap food and debris."
        ],
        "prevention": [
            "Brush your dog's teeth daily using a soft-bristled dog toothbrush and canine-specific toothpaste. Use a gentle circular motion, focusing on the outer tooth surfaces and gum line. Even 30-60 seconds of brushing makes a meaningful difference to plaque control.",
            "If your dog won't tolerate a toothbrush initially, start with a finger brush or even a piece of gauze wrapped around your finger. The key is making the experience positive — use tasty dog toothpaste, give praise, and keep sessions short. Gradually build up to longer brushing over weeks.",
            "Supplement brushing with VOHC-approved dental products. The Veterinary Oral Health Council tests and certifies products proven to reduce plaque and tartar. Look for the VOHC seal on dental chews, water additives, and dental diets.",
            "Provide appropriate chew toys and dental toys that promote mechanical cleaning. Raw, uncooked bones can be given under supervision (never cooked bones, which can splinter), but discuss this with your vet as bones carry their own risks including tooth fractures."
        ],
        "vet": [
            "Schedule annual dental check-ups as part of your dog's health examination. Your vet can assess the degree of dental disease, recommend appropriate interventions, and advise on your home care routine.",
            "Professional dental cleaning under general anaesthesia allows thorough cleaning above and below the gum line, dental X-rays to assess tooth root health, and extraction of diseased teeth. While anaesthesia carries small risks, modern protocols are very safe and the benefits of treating dental disease are significant.",
            "Some veterinary practices offer free dental check-up events — take advantage of these. If your vet recommends a dental procedure, ask about pre-anaesthetic blood tests, pain management, and aftercare instructions."
        ],
    },
    # 14: Hot Spots
    {
        "overview": [
            "Hot spots (acute moist dermatitis) are areas of intensely inflamed, infected skin that can appear seemingly overnight. They are among the most common skin conditions seen in veterinary practice, particularly during warmer, more humid months. A hot spot can go from a small patch of reddened skin to a large, oozing, painful lesion within hours.",
            "Hot spots develop through a cycle of irritation and self-trauma. Something initially irritates the skin — a flea bite, an insect sting, an allergen — and the dog's scratching or licking response damages the skin surface. Bacteria naturally present on the skin then colonise the moist, damaged area, creating a rapidly expanding infection.",
            "Prompt treatment is important because hot spots can spread and worsen remarkably quickly. Understanding the triggers and managing them prevents recurrence, which is key to long-term control."
        ],
        "signs": [
            "Hot spots are usually fairly obvious once established, but recognising them early — before they become large and severely infected — allows for simpler treatment. Here are the key characteristics:",
            "A well-defined area of reddened, moist, oozing skin that may be warm to the touch",
            "Hair loss over the affected area — fur may mat over the lesion, trapping moisture and bacteria",
            "Intense pain and sensitivity — dogs may cry out when the area is touched",
            "Rapid expansion — a small spot in the morning can become hand-sized by evening",
            "Pus, discharge, or a foul smell from the affected area indicating bacterial infection",
            "Intense itching leading to constant licking, chewing, or scratching that worsens the lesion",
            "Common locations include the head and neck (often associated with ear infections), the hip and thigh area (often associated with flea allergy), and areas under thick coat where moisture gets trapped."
        ],
        "causes": [
            "Flea allergy dermatitis is the most common trigger for hot spots. Even a single flea bite can cause an intense allergic reaction in sensitised dogs, leading to frantic scratching and rapid hot spot development. Consistent flea prevention is essential.",
            "Other common triggers include environmental allergies (pollen, mould), ear infections (causing head and neck scratching), matted or dirty fur (trapping moisture against skin), insect bites or stings, and contact irritants. Swimming or bathing followed by inadequate drying can also create conditions for hot spots.",
            "Breeds with thick, dense double coats are most predisposed. Golden Retrievers, German Shepherds, Labrador Retrievers, Saint Bernards, and Bernese Mountain Dogs develop hot spots more frequently. The thick undercoat traps moisture against the skin, creating an ideal environment for bacterial growth."
        ],
        "prevention": [
            "Maintain rigorous flea prevention year-round, as flea allergy is the most common hot spot trigger. Use a veterinary-recommended flea product and treat all pets in the household to prevent environmental flea burden.",
            "Keep your dog's coat clean and well-groomed. Regular brushing removes loose fur and prevents mats that trap moisture. Ensure thorough drying after swimming or bathing, paying particular attention to the undercoat in thick-coated breeds.",
            "Address any underlying allergies with your vet. If your dog develops hot spots seasonally, preemptive allergy management (starting antihistamines or other allergy medication before the problem season) can prevent the cycle from starting.",
            "Treat ear infections promptly, as the scratching associated with ear discomfort frequently triggers hot spots on the head and neck. Regular ear cleaning in prone breeds reduces infection risk."
        ],
        "vet": [
            "Seek veterinary attention for hot spots that are large, deep, spreading rapidly, or not improving with basic home care within 24-48 hours. Hot spots on the face near the eyes also warrant professional attention due to the sensitive location.",
            "Your vet will typically clip the fur around the lesion (to expose it to air and allow topical treatment), clean the area, and prescribe appropriate topical and sometimes oral antibiotics. Anti-inflammatory medication or short-course steroids may be used to reduce itching and break the scratch cycle.",
            "For recurrent hot spots, investigate and address the underlying trigger. This may involve allergy testing, dietary trials, or management of chronic skin conditions. Recurring hot spots without root cause treatment will continue to be a frustrating problem."
        ],
    },
    # 15: Thyroid Problems
    {
        "overview": [
            "Thyroid dysfunction is one of the most common hormonal (endocrine) disorders in dogs. Hypothyroidism — underproduction of thyroid hormones — accounts for the vast majority of cases, while hyperthyroidism (overproduction) is rare in dogs (unlike in cats where it is common). The thyroid gland, located in the neck, produces hormones that regulate metabolism throughout the body.",
            "When thyroid hormone levels are insufficient, virtually every body system is affected. Metabolism slows, leading to weight gain, lethargy, and skin problems. The condition develops gradually, and early signs are often subtle and easily attributed to normal ageing.",
            "The good news is that hypothyroidism is one of the most treatable endocrine conditions. Once diagnosed, daily thyroid hormone replacement medication is straightforward, affordable, and highly effective, typically resolving symptoms within weeks to months."
        ],
        "signs": [
            "Hypothyroidism produces a wide range of symptoms because thyroid hormones affect every organ system. The classic presentation includes several of the following signs:",
            "Unexplained weight gain despite no increase in food intake — often the first change owners notice",
            "Lethargy, reduced activity, and mental dullness — dogs may seem 'slowed down' or less interested in walks and play",
            "Skin and coat changes — dry, dull, brittle coat; symmetrical hair loss (often sparing the head and legs); thickened skin; recurring skin infections",
            "Cold intolerance — seeking warm spots, reluctance to go outside in cool weather",
            "A 'tragic' facial expression caused by skin thickening and facial puffiness (myxoedema)",
            "Recurrent ear infections and skin infections that respond to treatment but keep returning",
            "Less common signs include reproductive problems, nerve dysfunction (facial paralysis, weakness), corneal lipid deposits, and cardiovascular changes. The combination of weight gain, lethargy, and skin changes in a middle-aged dog should always prompt thyroid testing."
        ],
        "causes": [
            "The most common cause of hypothyroidism in dogs (over 95% of cases) is lymphocytic thyroiditis — an autoimmune condition where the immune system gradually destroys the thyroid gland. The second most common cause is idiopathic thyroid atrophy, where thyroid tissue is replaced by fat tissue for unknown reasons.",
            "Hypothyroidism typically develops in middle-aged dogs (4-10 years). Medium to large breeds are more commonly affected than small breeds. Breeds with higher prevalence include Golden Retrievers, Dobermanns, Irish Setters, Dachshunds, Cocker Spaniels, Boxers, and Airedale Terriers.",
            "Less commonly, hypothyroidism can be caused by thyroid tumours, iodine deficiency, or pituitary gland problems affecting thyroid-stimulating hormone (TSH) production. Certain medications can also affect thyroid function."
        ],
        "prevention": [
            "While the autoimmune form of hypothyroidism cannot be prevented, maintaining overall health supports thyroid function. Feed a balanced diet that includes adequate iodine (most commercial dog foods provide sufficient iodine) and avoid unnecessary iodine supplementation.",
            "Keep your dog at a healthy weight and provide regular exercise. Obesity can affect thyroid function tests, making diagnosis more challenging, and compounds the metabolic effects of hypothyroidism.",
            "Be aware of your breed's predisposition and discuss thyroid screening with your vet during annual health checks, particularly for middle-aged dogs of susceptible breeds. Early detection before significant symptoms develop allows prompt treatment.",
            "If your dog is diagnosed with hypothyroidism, consistent medication administration is essential for prevention of complications. Never adjust the dose or stop medication without veterinary guidance, even if your dog appears well."
        ],
        "vet": [
            "If you notice the combination of weight gain, lethargy, and skin changes in your dog, schedule a veterinary appointment for thyroid testing. Diagnosis involves blood tests measuring total T4, free T4, and sometimes TSH levels. Multiple tests may be needed as thyroid levels can fluctuate.",
            "Treatment with levothyroxine (synthetic thyroid hormone) is started at a calculated dose based on body weight. Blood levels are rechecked 4-6 hours post-medication at 4-6 weeks, with dose adjustments as needed. Most dogs require lifelong treatment with blood monitoring every 6-12 months once stable.",
            "Response to treatment is typically gratifying. Energy levels often improve within 1-2 weeks, weight normalisation takes 2-3 months, and skin and coat improvements are visible within 3-6 months. If response is poor, your vet may investigate other concurrent conditions."
        ],
    },
    # 16: Surgery Recovery
    {
        "overview": [
            "Whether your dog has undergone a routine neutering procedure or major orthopaedic surgery, proper post-operative care at home is crucial for a smooth recovery. The way you manage the recovery period directly impacts healing speed, complication risk, and your dog's comfort.",
            "Modern veterinary surgery and anaesthesia are remarkably safe, but the recovery period requires attentive care. Most complications — wound infections, dehiscence (wound opening), and self-trauma — occur during the home recovery phase and are largely preventable with proper management.",
            "Planning ahead makes the recovery period easier for both you and your dog. Prepare your home before the surgery day, stock up on supplies, arrange time off work if possible, and understand the specific aftercare instructions for your dog's procedure."
        ],
        "signs": [
            "Knowing what is normal after surgery and what should cause concern helps you provide appropriate care. Here is what to expect and watch for during recovery:",
            "Mild grogginess and reduced appetite for 12-24 hours after anaesthesia is normal — this should progressively improve",
            "The surgical site may be slightly swollen and pink for the first few days — this is normal healing inflammation",
            "Minor bruising around the wound site is common, particularly after orthopaedic procedures",
            "A small amount of clear or slightly blood-tinged discharge from the wound for the first 24 hours may be normal",
            "Gradual return to normal behaviour over 2-7 days, depending on the procedure",
            "Stitches or staples visible at the wound site (unless internal/dissolvable sutures were used)",
            "Contact your vet if you notice: wound opening or gaping, significant swelling or redness increasing after day 2, foul-smelling discharge, persistent bleeding, refusal to eat or drink beyond 24 hours, vomiting or diarrhoea, extreme pain despite prescribed medication, or any signs of distress."
        ],
        "causes": [
            "Post-surgical complications can arise from several factors. Wound infection occurs when bacteria contaminate the surgical site, often through licking, moisture, or environmental contamination. Self-trauma (licking, chewing, scratching the wound) is the single most common cause of post-surgical complications.",
            "Excessive activity during the recovery period can stress surgical repairs, particularly after orthopaedic, abdominal, or cruciate ligament procedures. Internal sutures and implants need time to integrate, and premature activity can cause repair failure.",
            "Individual factors including your dog's age, overall health, nutritional status, and concurrent conditions (diabetes, Cushing's disease, immune suppression) affect healing speed and complication risk. Discuss these factors with your vet before surgery."
        ],
        "prevention": [
            "Prevent wound interference using an Elizabethan collar (cone), inflatable recovery collar, or surgical recovery suit. Keep the protective device on at all times — including overnight and during meals — until your vet confirms the wound has healed sufficiently. Brief removals for eating should be directly supervised.",
            "Restrict activity as directed by your vet. This typically means lead-only walks for toileting, no running, jumping, or playing, and confinement to one room or a crate when unsupervised. A playpen or baby gates can help manage activity restrictions in busy households.",
            "Keep the wound clean and dry. Do not bathe your dog or allow swimming until your vet gives the all-clear. Check the wound twice daily for signs of infection, discharge, or opening. Avoid applying any creams, ointments, or home remedies unless specifically instructed by your vet.",
            "Administer all prescribed medications (pain relief, antibiotics, anti-inflammatories) exactly as directed. Complete the full course even if your dog seems recovered. Pain management is particularly important — well-managed pain promotes faster healing and better outcomes."
        ],
        "vet": [
            "Attend all scheduled post-operative check-ups. These allow your vet to assess wound healing, remove sutures if needed, adjust medications, and advise on gradually returning to normal activity. Do not skip these appointments even if everything appears fine.",
            "Contact your vet immediately if you notice any warning signs of complications. Wound infections caught early are easily treated with antibiotics, but delayed treatment can result in serious complications including wound breakdown, abscess formation, or systemic infection.",
            "Ask your vet clear questions about the recovery plan: How long should exercise be restricted? When can the cone be removed? When can they bathe or swim? When should stitches be removed? What pain signs should you watch for? Having a clear plan reduces anxiety for both you and your dog."
        ],
    },
    # 17: Digestive Issues
    {
        "overview": [
            "Digestive problems are among the most common reasons dogs visit the veterinarian. From an occasional upset stomach to chronic conditions like inflammatory bowel disease, understanding your dog's digestive health helps you know when to manage at home and when to seek veterinary attention.",
            "The canine digestive system is remarkably resilient but also remarkably indiscriminate — dogs will eat things that would never cross a human's mind. This dietary adventurousness is the most common cause of acute digestive upset, but chronic digestive problems often have more complex underlying causes.",
            "The gut also plays a critical role in immune function and overall health, housing trillions of beneficial microorganisms (the microbiome) that support digestion, nutrient absorption, and immune regulation. Supporting digestive health has far-reaching benefits beyond just avoiding upset stomachs."
        ],
        "signs": [
            "Digestive problems manifest through a range of symptoms. Understanding the pattern and severity helps determine the appropriate response:",
            "Vomiting — acute episodes may be dietary; persistent vomiting (more than 24 hours) requires veterinary attention",
            "Diarrhoea — note consistency (soft, watery, bloody), frequency, and duration; bloody diarrhoea or diarrhoea lasting more than 48 hours warrants urgent vet assessment",
            "Excessive flatulence — occasional wind is normal; constant, foul-smelling gas suggests dietary issues or maldigestion",
            "Abdominal pain — indicated by a tense belly, hunched posture, reluctance to move, or yelping when lifted",
            "Changes in appetite — refusing food, eating less than usual, or conversely, eating non-food items (pica)",
            "Constipation — straining to defecate, producing small hard stools, or passing no stool for more than 48 hours",
            "Monitor your dog's stool quality regularly using a simple scoring system. Healthy dog stools should be formed, easy to pick up, and chocolate brown in colour. Significant changes in colour (black, very pale, red-streaked) or consistency should prompt veterinary evaluation."
        ],
        "causes": [
            "Dietary indiscretion (eating inappropriate items including rubbish, foreign objects, rich foods, or toxic substances) is the most common cause of acute digestive upset. Sudden diet changes also commonly cause gastrointestinal disturbance, which is why gradual food transitions over 7-10 days are recommended.",
            "Chronic digestive issues may be caused by food allergies or sensitivities, inflammatory bowel disease (IBD), exocrine pancreatic insufficiency (EPI), chronic pancreatitis, intestinal parasites, or gut microbiome imbalance (dysbiosis). Some breeds are predisposed to specific conditions — German Shepherds to EPI, for example.",
            "Stress is an often-overlooked cause of digestive problems. The gut-brain axis means that anxiety, changes in routine, boarding, or travel can directly affect gastrointestinal function, causing soft stools, diarrhoea, or loss of appetite."
        ],
        "prevention": [
            "Feed a consistent, high-quality diet appropriate for your dog's age, size, and activity level. Avoid sudden food changes — when switching diets, transition gradually over 7-10 days by mixing increasing proportions of new food with decreasing proportions of old food.",
            "Prevent scavenging on walks using a 'leave it' command and appropriate lead control. Dog-proof your kitchen and rubbish bins. Be aware of toxic foods including chocolate, grapes/raisins, xylitol (artificial sweetener), onions, and garlic.",
            "Support gut health with prebiotics and probiotics. Prebiotic fibre (found in pumpkin, sweet potato, and commercial diets with added prebiotics) feeds beneficial gut bacteria. Canine-specific probiotics can help maintain a healthy microbiome, particularly after antibiotic courses or digestive upset.",
            "Avoid feeding fatty table scraps, which can trigger pancreatitis — a painful and potentially life-threatening inflammatory condition of the pancreas. Even a single fatty meal can cause acute pancreatitis in susceptible dogs."
        ],
        "vet": [
            "Seek veterinary attention for: vomiting lasting more than 24 hours, bloody vomiting or diarrhoea, signs of abdominal pain, suspected foreign body ingestion, dehydration signs (lethargy, sunken eyes, dry gums, skin that stays 'tented' when pinched), or any digestive symptoms in puppies or elderly dogs, who are more vulnerable to dehydration.",
            "Diagnosis of chronic digestive issues may involve blood tests, faecal analysis, abdominal ultrasound, endoscopy with biopsies, or food elimination trials. Your vet will determine the appropriate diagnostic pathway based on your dog's symptoms and history.",
            "Emergency situations requiring immediate veterinary care include suspected bloat (gastric dilatation-volvulus or GDV — a life-threatening condition with symptoms of retching without producing vomit, swollen abdomen, restlessness, and rapid decline), suspected toxin ingestion, and complete inability to keep water down."
        ],
    },
    # 18: UTIs
    {
        "overview": [
            "Urinary tract infections (UTIs) are a common health problem in dogs, particularly affecting females due to their shorter, wider urethra that allows bacteria easier access to the bladder. While UTIs are usually straightforward to treat with antibiotics, they can indicate underlying health issues that need addressing.",
            "The urinary system includes the kidneys, ureters, bladder, and urethra. Most infections (cystitis) affect the bladder, but if left untreated, bacteria can ascend to the kidneys (pyelonephritis), which is a much more serious condition. Prompt recognition and treatment prevents complications.",
            "Recurrent UTIs — defined as three or more infections in a 12-month period — affect a significant proportion of dogs and warrant thorough investigation to identify predisposing factors. Simply treating each infection with antibiotics without addressing the root cause leads to antibiotic resistance and ongoing discomfort."
        ],
        "signs": [
            "Changes in urination patterns are the most obvious signs of a UTI. Being observant during toilet breaks helps you catch infections early. Key symptoms include:",
            "Frequent urination — your dog needs to go out more often and may produce only small amounts each time",
            "Straining to urinate — visible effort or discomfort when attempting to pass urine",
            "Blood in the urine (haematuria) — urine may appear pink, red, or orange-tinged",
            "Accidents indoors — a previously house-trained dog having frequent urinary accidents",
            "Excessive licking of the genital area — attempting to soothe discomfort",
            "Strong, foul-smelling, or cloudy urine — bacterial byproducts change urine characteristics",
            "Note that some dogs, particularly those with chronic UTIs, may show minimal signs. Regular observation of your dog's urination habits helps you notice subtle changes. Male dogs with UTIs may also strain and produce small amounts, which can be confused with prostate problems."
        ],
        "causes": [
            "The vast majority of canine UTIs are caused by bacteria — most commonly Escherichia coli — that ascend from the external environment through the urethra into the bladder. Female dogs are more susceptible due to their anatomy. Other common bacteria include Staphylococcus, Proteus, and Enterococcus species.",
            "Predisposing factors include diabetes (high glucose in urine promotes bacterial growth), Cushing's disease (suppresses immune function), bladder stones (harbour bacteria and irritate the bladder wall), anatomical abnormalities (recessed vulva in females), urinary incontinence, and immunosuppressive medication.",
            "Less commonly, UTIs can be caused by fungal organisms or be associated with bladder tumours that provide a surface for bacterial colonisation. Prostate disease in intact male dogs can also predispose to urinary infections."
        ],
        "prevention": [
            "Ensure your dog always has access to fresh, clean water and encourage adequate water intake. Adequate hydration produces dilute urine that flushes bacteria from the bladder. Some dogs prefer flowing water and may drink more from a pet fountain.",
            "Provide frequent opportunities to urinate. Dogs that hold urine for extended periods give bacteria more time to multiply in the bladder. Aim for at least 3-4 toilet breaks per day for adult dogs, more for puppies and seniors.",
            "Maintain good hygiene around your dog's genital area, particularly for females. Keep fur trimmed short around the vulva to prevent bacterial accumulation. After swimming or muddy walks, clean the area gently.",
            "Address any underlying conditions that predispose to UTIs. Good diabetic control, management of Cushing's disease, removal of bladder stones, and surgical correction of anatomical abnormalities (such as vulvoplasty for recessed vulva) can dramatically reduce UTI recurrence."
        ],
        "vet": [
            "If you suspect a UTI, collect a urine sample (a clean container held under your dog mid-stream, ideally a morning sample) and bring it to your vet. Urinalysis and bacterial culture with sensitivity testing identify the specific bacteria and the most effective antibiotic.",
            "Complete the entire course of prescribed antibiotics even when symptoms resolve quickly. Incomplete treatment is a major cause of recurrent infections and contributes to antibiotic resistance. Your vet may recommend a follow-up urinalysis to confirm the infection has cleared.",
            "For recurrent UTIs, your vet will investigate underlying causes through blood tests (checking for diabetes, Cushing's disease, kidney function), imaging (X-rays or ultrasound for bladder stones or tumours), and possibly a urine culture performed on a sterile sample obtained by cystocentesis (needle aspiration from the bladder)."
        ],
    },
    # 19: Canine Cancer Detection
    {
        "overview": [
            "Cancer is the leading cause of death in dogs over 10 years of age. Approximately 1 in 4 dogs will develop some form of cancer during their lifetime. While these statistics are sobering, advances in veterinary oncology mean that many cancers can be treated successfully, particularly when detected early.",
            "Cancer in dogs encompasses a wide range of conditions, from benign fatty tumours (lipomas) that may need no treatment, to aggressive malignancies that require intensive intervention. Understanding the common types and their early warning signs empowers you to seek prompt veterinary assessment when something seems wrong.",
            "Early detection is the single most important factor in cancer treatment success. Dogs whose cancers are caught in early stages generally have significantly better prognoses and more treatment options available to them. Regular home checks and veterinary examinations are your best tools for early detection."
        ],
        "signs": [
            "Cancer can affect virtually any part of the body and produce a wide range of symptoms. The American Veterinary Medical Association identifies ten common warning signs adapted here for UK dog owners:",
            "New lumps or bumps, or existing lumps that are growing, changing shape, or changing texture — check your dog's body regularly for new or changing masses",
            "Wounds or sores that fail to heal within a normal timeframe despite appropriate treatment",
            "Unexplained weight loss — losing weight without a change in diet or exercise is a significant warning sign",
            "Loss of appetite or difficulty eating/swallowing — may indicate oral, oesophageal, or gastrointestinal cancer",
            "Bleeding or unusual discharge from any body opening — including nose, mouth, or other orifices",
            "Persistent lameness or stiffness — bone cancer (osteosarcoma) often presents as lameness in a limb",
            "Any of these signs individually may have benign explanations, but any that persist for more than two weeks, are worsening, or are accompanied by general malaise should be investigated promptly. Trust your instincts — you know your dog better than anyone."
        ],
        "causes": [
            "Cancer develops when cells mutate and grow uncontrollably. The causes are multifactorial and include genetic predisposition (certain breeds carry inherited cancer risk), age (cellular mutations accumulate over a lifetime), environmental carcinogens (chemicals, UV radiation, secondhand smoke), and possibly viral factors.",
            "Some of the most common cancers in dogs include lymphoma (affecting the lymph nodes), mast cell tumours (skin), osteosarcoma (bone), haemangiosarcoma (blood vessels, often affecting the spleen or heart), melanoma (mouth and skin), and mammary cancer (breast tissue, primarily in unspayed females).",
            "Breed predispositions are significant. Golden Retrievers have a lifetime cancer risk of approximately 60%. Boxers are prone to mast cell tumours. Rottweilers and large breeds have higher osteosarcoma rates. Flat-Coated Retrievers and Bernese Mountain Dogs have notably high cancer prevalence."
        ],
        "prevention": [
            "Perform monthly home health checks on your dog. Run your hands over their entire body feeling for new lumps, bumps, or swellings. Check the mouth for growths or colour changes. Monitor body weight, energy levels, appetite, and bathroom habits.",
            "Spay female dogs to significantly reduce mammary cancer risk. Spaying before the first heat virtually eliminates mammary cancer risk. Even spaying later in life provides some reduction. Discuss optimal timing with your vet considering both cancer prevention and orthopaedic considerations.",
            "Minimise exposure to known carcinogens. Avoid using chemical lawn treatments where your dog plays, don't expose dogs to cigarette smoke, limit sun exposure for light-skinned and white-coated dogs (apply pet-safe sunscreen to vulnerable areas), and use pet-safe household cleaning products.",
            "Maintain a healthy lifestyle including balanced nutrition, regular exercise, and healthy body weight. While these measures don't guarantee cancer prevention, they support immune surveillance (the body's natural ability to identify and destroy abnormal cells) and overall resilience."
        ],
        "vet": [
            "If you find a lump or notice any cancer warning signs, schedule a veterinary appointment promptly. A fine-needle aspirate — a quick, usually painless procedure where cells are extracted with a needle — can often provide initial information about the nature of a lump within 24-48 hours.",
            "Cancer diagnosis may involve blood tests, imaging (X-rays, ultrasound, CT or MRI), biopsy, and sometimes referral to a veterinary oncologist. Staging (determining the extent of cancer spread) is essential for treatment planning and prognosis.",
            "Treatment options in UK veterinary oncology are increasingly sophisticated. Depending on the cancer type and stage, options include surgery, chemotherapy (generally much better tolerated by dogs than humans), radiation therapy, immunotherapy, and palliative care. Your vet can discuss realistic expectations, treatment costs, and quality of life considerations to help you make informed decisions."
        ],
    },
    # 20: Arthritis in Winter
    {
        "overview": [
            "Arthritis (osteoarthritis) is the most common joint disease in dogs, estimated to affect up to 80% of dogs over 8 years of age to some degree. Winter presents particular challenges for arthritic dogs, as cold weather, reduced activity, and environmental conditions can significantly worsen joint pain and stiffness.",
            "Understanding why winter exacerbates arthritis helps you implement targeted strategies to keep your dog comfortable. Cold temperatures cause muscles and soft tissues to contract, reducing flexibility around compromised joints. Reduced physical activity during darker, wetter months leads to muscle atrophy and increased stiffness.",
            "With proper management, arthritic dogs can navigate winter comfortably. The key is proactive care — preparing before symptoms worsen rather than reacting once your dog is already in significant discomfort."
        ],
        "signs": [
            "Arthritis symptoms often worsen noticeably during winter months. Be alert for these signs of increased joint discomfort:",
            "Increased stiffness after rest, particularly first thing in the morning or after napping — taking longer to 'warm up' before moving normally",
            "Reluctance to go outside in cold or wet weather, when previously willing",
            "Difficulty with stairs, getting into cars, or jumping onto furniture that they previously managed",
            "Visible lameness or favouring one or more limbs, which may improve after gentle movement (warming-up effect)",
            "Reduced willingness to walk as far or play as actively as in warmer months",
            "Behavioural changes including irritability when touched around affected joints, disturbed sleep, or loss of appetite",
            "Monitor your dog's comfort levels throughout winter. Dogs are stoic and may not show obvious pain until it is severe. Subtle changes in behaviour, activity patterns, and willingness to move are often the earliest indicators of worsening joint pain."
        ],
        "causes": [
            "The winter worsening of arthritis is caused by several interconnected factors. Cold temperatures reduce blood flow to extremities and muscles, causing them to tighten and lose flexibility. Stiff muscles provide less support and shock absorption for arthritic joints, increasing pain during movement.",
            "Changes in barometric pressure associated with winter weather fronts may increase joint fluid viscosity and activate pain receptors in inflamed joint capsules. While the science is still evolving, both human and veterinary clinicians widely observe weather-related pain flare-ups.",
            "Reduced activity during winter creates a vicious cycle. Less movement leads to muscle wastage, which reduces joint support, which causes more pain, which leads to even less movement. Breaking this cycle through appropriate managed exercise is essential."
        ],
        "prevention": [
            "Keep your arthritic dog warm, both indoors and out. Invest in a well-fitting, waterproof dog coat for walks. Indoors, provide a warm, orthopaedic bed positioned away from draughts and cold floors. Consider a heated pet bed or pad for dogs with significant arthritis.",
            "Maintain regular, gentle exercise throughout winter rather than becoming inactive. Shorter, more frequent walks on flat surfaces are better than long walks. Aim for consistency — even 10-15 minutes twice daily keeps muscles engaged. Warm up gradually with slow walking before increasing pace.",
            "Non-slip flooring is crucial for arthritic dogs. Place rugs or yoga mats on slippery hard floors — arthritic dogs who slip and splay their legs experience pain and may become reluctant to move. Non-slip dog socks or boots can help on walks when paths are icy.",
            "Continue or intensify joint supplement regimes during winter. Omega-3 fatty acids (fish oil) have anti-inflammatory properties. Glucosamine and chondroitin support cartilage health. Green-lipped mussel extract contains unique anti-inflammatory compounds. Discuss optimal dosing with your vet."
        ],
        "vet": [
            "Review your dog's pain management plan with your vet before winter sets in. Many arthritic dogs benefit from increased pain medication during colder months. Your vet may adjust NSAID dosages, add adjunctive pain medications like gabapentin, or recommend acupuncture.",
            "Hydrotherapy (warm-water exercise) is particularly beneficial for arthritic dogs in winter. Warm water soothes joints while providing low-impact exercise that maintains muscle mass without stressing compromised joints. Many veterinary practices and canine hydrotherapy centres offer this service across the UK.",
            "Regular veterinary check-ups (every 6 months for arthritic dogs) help monitor disease progression and pain control. Be honest about your dog's comfort levels and activity — your vet relies on your observations at home to optimise treatment."
        ],
    },
    # 21: Breathing Problems
    {
        "overview": [
            "Breathing is so fundamental that any abnormality demands attention. Dogs can develop breathing difficulties from numerous causes, ranging from easily managed conditions to life-threatening emergencies. Knowing what constitutes normal breathing and recognising abnormalities allows you to respond appropriately.",
            "A healthy dog at rest breathes quietly and effortlessly at a rate of 10-30 breaths per minute. Panting after exercise, during warm weather, or when excited is entirely normal. The concern arises when breathing is laboured, noisy, or rapid without an obvious cause.",
            "Breathing problems in dogs can be categorised as upper airway (nose, throat, trachea), lower airway (bronchi, lungs), or non-respiratory (heart disease, anaemia, pain). Identifying the category helps determine urgency and appropriate response."
        ],
        "signs": [
            "Distinguishing concerning breathing from normal panting is important. Here are the signs that indicate a breathing problem requiring attention:",
            "Open-mouth breathing at rest when not hot or excited — healthy dogs breathe through their nose when relaxed",
            "Increased respiratory rate at rest (consistently above 30 breaths per minute while sleeping)",
            "Increased respiratory effort — visible abdominal movement, extended neck, elbows held out from the body, or flared nostrils",
            "Noisy breathing — stridor (high-pitched), stertor (snoring-type), wheeze, or crackle sounds that are new or worsening",
            "Cyanosis — blue, purple, or grey gums and tongue indicating inadequate oxygenation (EMERGENCY)",
            "Coughing — persistent, especially at night, after exercise, or when pulling on the lead",
            "Breathing emergencies require immediate veterinary attention. If your dog has blue or grey gums, is gasping, cannot breathe lying down, or collapses, transport to the nearest emergency vet immediately. Time matters in respiratory emergencies."
        ],
        "causes": [
            "Upper airway causes include brachycephalic obstructive airway syndrome (BOAS) in flat-faced breeds, laryngeal paralysis (common in older large breeds), tracheal collapse (common in small breeds), nasal tumours, and foreign bodies lodged in the throat.",
            "Lower airway and lung causes include pneumonia (bacterial, viral, or aspiration), chronic bronchitis, pulmonary oedema (fluid in the lungs, often from heart failure), lung tumours, and pulmonary thromboembolism (blood clots in the lungs).",
            "Non-respiratory causes of breathing difficulty include heart disease (the most common cause of chronic coughing in older dogs), anaemia (insufficient red blood cells to carry oxygen), pain, anxiety, heatstroke, obesity (restricting chest expansion), and metabolic disorders."
        ],
        "prevention": [
            "Maintain a healthy body weight. Obesity significantly compromises respiratory function by restricting chest wall movement, reducing lung volume, and increasing oxygen demand. Overweight brachycephalic dogs are at particular risk.",
            "For brachycephalic breeds, be especially vigilant during hot weather. These dogs cannot thermoregulate effectively through panting due to their shortened airways. Keep them cool, avoid exercise in heat, and consider BOAS surgery if they have significant breathing compromise even in normal conditions.",
            "Use a harness instead of a collar for dogs prone to tracheal collapse or those that pull on the lead. Collars place direct pressure on the trachea, potentially worsening airway conditions. Front-clip harnesses are effective for managing pulling without airway compression.",
            "Avoid exposing your dog to respiratory irritants including cigarette smoke, strong household chemicals, heavy perfume, and dusty environments. Dogs with existing respiratory conditions are particularly sensitive to airborne irritants."
        ],
        "vet": [
            "Any breathing difficulty that is new, sudden, or worsening warrants veterinary assessment. Acute respiratory distress (severe difficulty breathing) is a veterinary emergency — do not wait to see if it improves. Keep your dog calm during transport and ensure good air circulation in the vehicle.",
            "Diagnostic workup for breathing problems typically includes physical examination, chest X-rays (often the most informative initial test), blood tests, and potentially echocardiography (heart ultrasound), bronchoscopy, or CT scan depending on the suspected cause.",
            "Treatment depends entirely on the underlying cause. Heart failure may require diuretics and cardiac medication. Pneumonia needs antibiotics. Tracheal collapse may be managed with cough suppressants and weight loss or surgical stenting. BOAS surgery can dramatically improve quality of life for affected brachycephalic dogs."
        ],
    },
    # 22: Senior Dogs Active
    {
        "overview": [
            "Ageing is not a disease — it is a natural process that, with appropriate management, allows dogs to remain comfortable and engaged well into their senior years. However, ageing does bring changes that require adapting how we care for our canine companions. Understanding these changes helps you provide targeted support.",
            "The onset of 'senior' status varies significantly by breed size. Giant breeds (over 40kg) may be considered senior at 5-6 years, while small breeds (under 10kg) may not show age-related changes until 10-12 years. Most dogs fall somewhere in between, with medium and large breeds entering their senior years at 7-9 years.",
            "The goal of senior dog care is maintaining quality of life — ensuring your dog can continue enjoying their daily activities, social interactions, and favourite pastimes with minimal discomfort. This often requires adjustments to exercise, diet, environment, and healthcare frequency."
        ],
        "signs": [
            "Age-related changes develop gradually, making them easy to overlook. Regular assessment of your senior dog's condition helps you adapt their care appropriately. Here are common changes to monitor:",
            "Reduced endurance and speed — taking longer to complete walks, stopping more frequently, or being reluctant to start",
            "Stiffness, particularly after rest — slow to rise, reluctant on stairs, difficulty jumping",
            "Changes in sleep patterns — sleeping more during the day, restlessness at night",
            "Sensory decline — reduced responsiveness to sounds (hearing loss) or bumping into things in dim light (vision loss)",
            "Weight changes — tendency to gain weight due to reduced metabolism and activity, or sometimes weight loss from muscle wastage or dental problems",
            "Behavioural changes — increased anxiety, less tolerance for change, confusion in familiar situations",
            "Regular monitoring using a simple quality-of-life assessment helps track changes over time. Rate your dog's mobility, comfort, happiness, appetite, and social engagement on a regular basis. Discuss any declining trends with your vet."
        ],
        "causes": [
            "Age-related changes result from cumulative cellular and tissue degeneration. Cartilage wears down in joints (osteoarthritis), muscles lose mass and strength (sarcopenia), organs gradually lose function, and the immune system becomes less efficient (immunosenescence).",
            "Hormonal changes accompany ageing, affecting metabolism, energy levels, and body composition. Thyroid function may decline, growth hormone decreases, and cortisol regulation may change. These shifts contribute to weight gain, muscle loss, and reduced healing capacity.",
            "Cognitive changes occur as the brain ages, with reduced neurotransmitter production, accumulated oxidative damage, and beta-amyloid deposition. While not all senior dogs develop clinical cognitive dysfunction, some degree of cognitive change is common."
        ],
        "prevention": [
            "Keep your senior dog moving with appropriate exercise. 'Use it or lose it' applies strongly to ageing dogs. Regular gentle exercise maintains muscle mass, joint flexibility, cardiovascular health, and mental sharpness. Adjust intensity — two shorter walks are often better than one long walk.",
            "Transition to a senior-appropriate diet. Senior dogs typically need fewer calories (to prevent obesity) but maintained or increased protein (to combat muscle loss). Look for diets enriched with joint-supporting ingredients, antioxidants, and easily digestible proteins. Consult your vet for specific dietary recommendations.",
            "Adapt your home environment. Add non-slip rugs on hard floors, provide ramps for furniture and cars, raise food and water bowls to reduce neck strain, provide orthopaedic bedding, ensure easy access to outdoor toilet areas, and add night lights for dogs with declining vision.",
            "Continue mental enrichment. Senior dogs benefit from ongoing mental stimulation through puzzle feeders, nose work, gentle training sessions, and varied (if shorter) walking routes. Mental engagement supports cognitive health and provides purpose and enjoyment."
        ],
        "vet": [
            "Increase veterinary check-ups to every 6 months for senior dogs. Age-related conditions are progressive, and more frequent monitoring allows earlier intervention. Senior health screens typically include blood tests, urinalysis, blood pressure measurement, and thorough physical examination.",
            "Discuss a comprehensive senior health plan with your vet covering pain management (for arthritis and other conditions), dental care, weight management, supplement recommendations, and any breed-specific health screening. Proactive management is always more effective than reactive treatment.",
            "Don't dismiss changes as 'just old age.' Many conditions common in senior dogs — hypothyroidism, dental disease, kidney disease, cognitive dysfunction — are treatable. Proper diagnosis and management can significantly improve quality of life and comfort."
        ],
    },
    # 23: Food Sensitivities vs Allergies
    {
        "overview": [
            "Food-related adverse reactions are increasingly recognised in dogs, yet the terminology can be confusing. True food allergies (involving an immune system response) and food sensitivities/intolerances (non-immune reactions) have different mechanisms, symptoms, and management approaches. Understanding the distinction helps you and your vet develop the most effective management strategy.",
            "Food allergies account for approximately 10-15% of all allergic skin disease in dogs. The immune system mistakenly identifies certain food proteins as threats, triggering an inflammatory response. Common culprits are proteins (beef, chicken, dairy, wheat) rather than additives or preservatives, contrary to popular belief.",
            "Food sensitivities (intolerances) are more common and involve non-immune mechanisms such as enzyme deficiencies (like lactose intolerance), pharmacological reactions to food components, or idiosyncratic responses. They typically cause digestive symptoms rather than the skin problems characteristic of true food allergies."
        ],
        "signs": [
            "The symptoms of food allergy and food sensitivity overlap but tend to differ in their primary presentation. Here is how to distinguish between them:",
            "Food allergy symptoms — primarily skin-related: chronic itching (especially around ears, paws, face, and rear end), recurrent ear infections, skin infections, and occasionally gastrointestinal signs",
            "Food sensitivity symptoms — primarily digestive: vomiting, diarrhoea, flatulence, borborygmi (loud gut sounds), and occasionally skin signs",
            "Year-round symptoms (not seasonal) — food reactions occur regardless of time of year, unlike environmental allergies that follow pollen seasons",
            "Symptoms that do not respond to standard allergy medications — Apoquel or Cytopoint may provide only partial relief if food allergy is the primary cause",
            "Onset at any age — food allergies can develop to foods your dog has eaten without problems for years",
            "Failure of multiple dietary changes to resolve symptoms — especially if the new diets contain the same protein sources (e.g., switching between chicken-based brands)",
            "It is worth noting that many dogs have concurrent food and environmental allergies. Addressing the food component reduces the overall 'allergic load,' often bringing environmental allergy symptoms below the threshold that triggers clinical signs."
        ],
        "causes": [
            "True food allergies involve the immune system producing IgE antibodies against specific food proteins. When these proteins are consumed, they trigger mast cell degranulation and histamine release, causing inflammation. The most common canine food allergens are beef, dairy products, chicken, wheat, soy, and lamb.",
            "Food sensitivities involve non-immune mechanisms. Lactose intolerance (lack of the enzyme lactase) is common in adult dogs. Histamine intolerance can occur with certain preserved or fermented foods. Some dogs react to specific carbohydrate sources or food additives through poorly understood mechanisms.",
            "Genetic predisposition influences food allergy development. Breeds with higher prevalence include West Highland White Terriers, Labrador Retrievers, Cocker Spaniels, German Shepherds, and Staffordshire Bull Terriers. The gut barrier function, immune system programming, and microbiome composition all play roles in whether food allergies develop."
        ],
        "prevention": [
            "The gold standard for diagnosing food allergies is an elimination diet trial. Feed a single novel protein source (one your dog has never eaten before, such as venison, duck, or insect protein) or a hydrolysed protein diet for 8-12 weeks. During this period, the dog must eat NOTHING else — no treats, no table scraps, no flavoured medications.",
            "If symptoms improve during the elimination trial, individual ingredients are reintroduced one at a time (every 2 weeks) to identify the specific triggers. This provocation phase is essential — without it, you cannot confirm which ingredients cause reactions.",
            "Avoid blood and saliva allergy tests marketed for food allergy diagnosis in dogs. Multiple studies have shown these tests have poor accuracy for food allergies, frequently producing false positives and false negatives. The elimination diet trial remains the only reliable diagnostic method.",
            "Once trigger ingredients are identified, long-term management involves strict avoidance. Read ingredient labels carefully — many commercial dog foods and treats contain multiple protein sources. A veterinary nutritionist can help formulate a balanced exclusion diet if commercial options are limited."
        ],
        "vet": [
            "Work with your vet throughout the diagnostic and management process. An elimination diet trial should be conducted under veterinary supervision to ensure nutritional adequacy, monitor for improvement, and guide the reintroduction phase correctly.",
            "Your vet can distinguish between food allergies, food sensitivities, and environmental allergies through clinical history, elimination trials, and where appropriate, intradermal skin testing for environmental allergens. Many dogs require management for both food and environmental allergies simultaneously.",
            "In some cases, referral to a veterinary dermatologist provides specialist expertise for complex cases. They can conduct advanced diagnostics, formulate comprehensive management plans, and supervise allergen-specific immunotherapy for concurrent environmental allergies."
        ],
    },
    # 24: Wellness Plan
    {
        "overview": [
            "A comprehensive wellness plan is a proactive approach to your dog's health that covers preventive care, nutrition, exercise, dental health, mental wellbeing, and age-appropriate screening. Rather than reacting to health problems as they arise, a wellness plan anticipates and prevents issues, saving both money and suffering in the long run.",
            "Just as humans benefit from regular health check-ups and preventive measures, dogs thrive when their healthcare is structured and consistent. A wellness plan provides a framework for ensuring nothing is overlooked and that your dog receives age-appropriate care at every life stage — from puppyhood through their senior years.",
            "Creating a wellness plan is a collaborative process between you and your veterinary team. Your knowledge of your dog's daily habits, behaviour, and preferences combines with your vet's clinical expertise to create a tailored plan that suits your dog's individual needs."
        ],
        "signs": [
            "A wellness plan helps you track your dog's health status over time. Here are the key health parameters you should regularly monitor as part of your plan:",
            "Body weight and body condition — monthly weigh-ins and body condition scoring to maintain a healthy weight",
            "Dental health — weekly mouth checks looking at teeth, gums, and breath",
            "Coat and skin condition — regular brushing while checking for lumps, bumps, parasites, and skin changes",
            "Energy levels and mobility — noting any changes in activity, willingness to exercise, or ease of movement",
            "Eating and drinking habits — monitoring appetite, water intake, and any changes in eating behaviour",
            "Toilet habits — observing stool quality, urination frequency, and any signs of difficulty",
            "By establishing your dog's 'normal' baseline across all these parameters, you become expertly positioned to notice changes early. A simple monthly health check at home — running your hands over your dog's body, checking ears, eyes, teeth, and nails — takes just 5-10 minutes but provides invaluable early warning of developing issues."
        ],
        "causes": [
            "Many common health problems in dogs are preventable or can be caught early through structured preventive care. Dental disease, obesity, parasitic infections, and many infectious diseases are largely preventable with appropriate management.",
            "Dogs age approximately 7 times faster than humans (as a rough guide), meaning that health changes can develop rapidly. A year without a vet check-up is equivalent to a human going 5-7 years without seeing a doctor. Regular professional assessment catches developing conditions that home monitoring may miss.",
            "Financial barriers often lead to reactive rather than preventive care. However, preventive care is significantly less expensive than treating established disease. Monthly veterinary practice health plans can spread costs and make comprehensive preventive care more accessible."
        ],
        "prevention": [
            "Build your wellness plan around these core components: vaccination (core and non-core as appropriate), parasite prevention (flea, worm, tick — year-round), dental care (daily brushing plus annual professional assessment), nutrition (age-appropriate, portion-controlled diet), and exercise (daily activity appropriate for breed, age, and fitness).",
            "Include regular health screening: annual vet check-ups (biannual for seniors), annual blood tests for senior dogs, breed-specific screening (hip/elbow scoring, heart checks, eye tests), and at-home monthly health checks.",
            "Keep comprehensive health records. A dog health journal or app recording weights, vaccinations, parasite treatments, medications, and health observations creates an invaluable longitudinal record. This information helps your vet identify trends and make better clinical decisions.",
            "Plan for emergencies. Have a pet first aid kit stocked and accessible. Know your nearest emergency vet clinic and their phone number. Consider pet insurance — a lifetime policy taken out when your dog is young provides the most comprehensive and cost-effective coverage."
        ],
        "vet": [
            "Discuss creating a personalised wellness plan at your next veterinary appointment. Your vet can recommend age-appropriate screening, vaccination protocols, and parasite prevention based on your dog's individual risk factors, breed, and lifestyle.",
            "Many UK veterinary practices offer wellness or health care plans that bundle preventive care (vaccinations, parasite treatments, health checks, and often discounts on other services) into affordable monthly payments. These plans make comprehensive preventive care more accessible and ensure nothing is forgotten.",
            "As your dog enters different life stages (puppy, adult, senior), review and update the wellness plan with your vet. A puppy's needs are very different from a senior dog's needs, and the plan should evolve accordingly. Life events like neutering, pregnancy, illness, or changes in activity level should also prompt a plan review."
        ],
    },
]

# ── Glossary terms for each topic ──────────────────────────────────────
GLOSSARY_TERMS = [
    # 0: Pain
    [("Acute pain", "Sudden onset pain from injury or illness, typically with an identifiable cause"),
     ("Chronic pain", "Long-lasting pain persisting for weeks or months, often from degenerative conditions"),
     ("NSAIDs", "Non-steroidal anti-inflammatory drugs — prescription pain medications commonly used in veterinary medicine"),
     ("Nociception", "The nervous system's process of detecting and transmitting pain signals"),
     ("Multimodal analgesia", "Using multiple types of pain relief simultaneously for more effective pain control")],
    # 1: Vaccination
    [("Core vaccines", "Vaccines recommended for all dogs regardless of lifestyle — DHP in the UK"),
     ("Non-core vaccines", "Vaccines recommended based on individual risk factors and lifestyle"),
     ("Titre testing", "Blood test measuring antibody levels to assess existing immunity"),
     ("Herd immunity", "Population-level protection achieved when a sufficient proportion is vaccinated"),
     ("Booster", "A follow-up vaccination dose that reinforces and extends immunity")],
    # 2: Weight
    [("Body Condition Score (BCS)", "A standardised assessment of body fat using a 1-9 scale"),
     ("Metabolic rate", "The rate at which the body burns calories at rest"),
     ("Caloric deficit", "Consuming fewer calories than the body uses, leading to weight loss"),
     ("Sarcopenia", "Age-related loss of muscle mass that can affect weight assessment"),
     ("Obesity", "Excessive body fat accumulation — generally defined as more than 20% above ideal weight")],
    # 3: Diabetes
    [("Insulin", "A hormone produced by the pancreas that allows cells to absorb glucose from the blood"),
     ("Glucose", "A simple sugar that serves as the primary energy source for cells"),
     ("Ketoacidosis", "A dangerous complication where the body breaks down fat too rapidly, producing toxic ketones"),
     ("Glycaemic control", "The management of blood sugar levels within a target range"),
     ("Polydipsia/Polyuria", "Excessive thirst and excessive urination — classic signs of diabetes")],
    # 4: Heart
    [("Mitral valve disease", "Degeneration of the heart valve between the left atrium and ventricle"),
     ("Dilated cardiomyopathy", "Weakening and enlargement of the heart muscle, reducing pumping efficiency"),
     ("Heart murmur", "An abnormal sound heard through a stethoscope, caused by turbulent blood flow"),
     ("Congestive heart failure", "A condition where the heart cannot pump blood effectively, causing fluid buildup"),
     ("Echocardiography", "Ultrasound examination of the heart to assess structure and function")],
    # 5: Eyes
    [("Conjunctivitis", "Inflammation of the membrane lining the eyelids and covering the white of the eye"),
     ("Corneal ulcer", "A wound on the clear outer surface of the eye"),
     ("Glaucoma", "Increased pressure within the eye that can damage the optic nerve and cause blindness"),
     ("Keratoconjunctivitis sicca (KCS)", "Dry eye — insufficient tear production leading to corneal damage"),
     ("Entropion", "A condition where the eyelid rolls inward, causing eyelashes to rub against the eye surface")],
    # 6: Allergies
    [("Atopic dermatitis", "Chronic inflammatory skin condition caused by environmental allergens"),
     ("IgE antibodies", "Immune proteins that trigger allergic reactions when they encounter specific allergens"),
     ("Allergen", "A substance that triggers an immune response in sensitised individuals"),
     ("Immunotherapy", "Treatment that gradually desensitises the immune system to specific allergens"),
     ("Pruritus", "Medical term for itching — the primary symptom of allergic skin disease in dogs")],
    # 7: Hip Dysplasia
    [("Hip dysplasia", "Abnormal development of the hip joint where the ball and socket don't fit properly"),
     ("BVA/KC Hip Score", "A standardised X-ray assessment scoring hip joint quality from 0 (perfect) to 106 (worst)"),
     ("Osteoarthritis", "Degenerative joint disease causing cartilage breakdown, pain, and stiffness"),
     ("Total hip replacement", "Surgical procedure replacing the diseased hip joint with artificial components"),
     ("Growth plate", "The area of developing tissue near the end of growing bones — vulnerable to damage in young dogs")],
    # 8: Epilepsy
    [("Seizure", "A sudden, uncontrolled burst of electrical activity in the brain"),
     ("Idiopathic epilepsy", "Epilepsy with no identifiable underlying cause, presumed genetic"),
     ("Status epilepticus", "A seizure lasting more than 5 minutes — a life-threatening emergency"),
     ("Anti-epileptic drug (AED)", "Medication used to prevent or reduce seizure frequency"),
     ("Seizure threshold", "The level of brain excitability at which seizures are triggered")],
    # 9: Ear Infections
    [("Otitis externa", "Infection or inflammation of the external ear canal"),
     ("Otitis media", "Infection of the middle ear, beyond the eardrum"),
     ("Cytology", "Microscopic examination of ear discharge to identify bacteria, yeast, or mites"),
     ("Tympanic membrane", "The eardrum — separating the external ear canal from the middle ear"),
     ("Malassezia", "A type of yeast commonly involved in canine ear infections")],
    # 10: Immune System
    [("Immune system", "The body's complex defence network that identifies and destroys harmful invaders"),
     ("Microbiome", "The community of trillions of beneficial microorganisms living in and on the body"),
     ("Probiotics", "Live beneficial bacteria that support gut health and immune function"),
     ("Antioxidants", "Substances that protect cells from damage caused by free radicals"),
     ("Immunosenescence", "Age-related decline in immune system function")],
    # 11: Cognitive Dysfunction
    [("Canine Cognitive Dysfunction (CCD)", "A neurodegenerative condition in senior dogs similar to Alzheimer's disease"),
     ("Beta-amyloid plaques", "Abnormal protein deposits that accumulate in the ageing brain"),
     ("DISHAA", "Acronym summarising CCD symptoms: Disorientation, Interaction changes, Sleep changes, House soiling, Activity changes, Anxiety"),
     ("Selegiline", "Medication that increases dopamine levels in the brain, used to treat CCD"),
     ("Neurogenesis", "The process of creating new brain cells, which can be supported by exercise and enrichment")],
    # 12: Separation Anxiety
    [("Separation anxiety", "A clinical condition causing extreme distress when separated from an attachment figure"),
     ("Desensitisation", "Gradually exposing a dog to a trigger at sub-threshold intensity to reduce reactivity"),
     ("Counter-conditioning", "Changing a dog's emotional response to a trigger by pairing it with positive experiences"),
     ("Fluoxetine", "An SSRI antidepressant medication sometimes prescribed for canine anxiety disorders"),
     ("Attachment behaviour", "Behaviours that function to maintain proximity to a caregiver")],
    # 13: Dental Care
    [("Plaque", "A sticky bacterial biofilm that forms on teeth within hours of eating"),
     ("Tartar (calculus)", "Hardened, mineralised plaque that cannot be removed by brushing alone"),
     ("Periodontal disease", "Infection and destruction of the tissues supporting the teeth"),
     ("VOHC", "Veterinary Oral Health Council — certifies products proven to reduce plaque and tartar"),
     ("Gingivitis", "Inflammation of the gums — the earliest, reversible stage of dental disease")],
    # 14: Hot Spots
    [("Acute moist dermatitis", "The clinical term for hot spots — rapidly developing areas of infected, inflamed skin"),
     ("Pyoderma", "Bacterial skin infection — hot spots are a form of surface pyoderma"),
     ("Self-trauma", "Damage a dog inflicts on itself through scratching, licking, or chewing"),
     ("Elizabethan collar", "A cone-shaped collar that prevents dogs from reaching wounds with their mouth"),
     ("Flea allergy dermatitis", "An allergic reaction to flea saliva — the most common hot spot trigger")],
    # 15: Thyroid
    [("Hypothyroidism", "Underproduction of thyroid hormones by the thyroid gland"),
     ("Levothyroxine", "Synthetic thyroid hormone used to treat hypothyroidism"),
     ("T4 (thyroxine)", "The primary hormone produced by the thyroid gland"),
     ("Lymphocytic thyroiditis", "Autoimmune destruction of the thyroid gland — the most common cause of hypothyroidism in dogs"),
     ("Myxoedema", "Skin and tissue swelling caused by severe hypothyroidism")],
    # 16: Surgery Recovery
    [("General anaesthesia", "Drug-induced state of unconsciousness for surgical procedures"),
     ("Dehiscence", "Wound breakdown — when a surgical wound opens or separates"),
     ("Sutures", "Stitches used to close surgical wounds — may be external or internal/dissolvable"),
     ("Post-operative", "The period following a surgical procedure"),
     ("Recovery suit", "A body-covering garment that prevents wound access — an alternative to the cone collar")],
    # 17: Digestive Issues
    [("Microbiome", "The community of beneficial microorganisms in the digestive tract"),
     ("Pancreatitis", "Inflammation of the pancreas, often triggered by fatty foods"),
     ("GDV (Bloat)", "Gastric dilatation-volvulus — a life-threatening stomach twisting emergency"),
     ("Prebiotics", "Non-digestible fibres that feed beneficial gut bacteria"),
     ("Bland diet", "A simple, easily digestible diet used during digestive recovery — typically boiled chicken and rice")],
    # 18: UTIs
    [("Cystitis", "Inflammation or infection of the bladder"),
     ("Urinalysis", "Laboratory analysis of urine to detect infection, crystals, and other abnormalities"),
     ("Pyelonephritis", "Kidney infection — a serious complication of untreated lower urinary tract infections"),
     ("Cystocentesis", "Collection of a sterile urine sample directly from the bladder using a needle"),
     ("Antimicrobial resistance", "When bacteria become resistant to antibiotics through repeated or incomplete treatment")],
    # 19: Cancer
    [("Benign tumour", "A non-cancerous growth that does not spread to other parts of the body"),
     ("Malignant tumour", "A cancerous growth that can invade surrounding tissues and spread (metastasise)"),
     ("Metastasis", "The spread of cancer cells from the original site to other parts of the body"),
     ("Fine-needle aspirate", "A diagnostic procedure extracting cells from a lump for microscopic examination"),
     ("Oncology", "The branch of medicine dealing with the diagnosis and treatment of cancer")],
    # 20: Arthritis Winter
    [("Osteoarthritis", "Degenerative joint disease caused by cartilage breakdown over time"),
     ("NSAID", "Non-steroidal anti-inflammatory drug — commonly prescribed for arthritis pain"),
     ("Hydrotherapy", "Therapeutic exercise in warm water — beneficial for arthritic joints"),
     ("Glucosamine", "A supplement that supports cartilage health and may slow joint degeneration"),
     ("Sarcopenia", "Loss of muscle mass — accelerated by inactivity and worsens joint instability")],
    # 21: Breathing
    [("Dyspnoea", "Medical term for difficulty breathing or laboured breathing"),
     ("Brachycephalic", "Flat-faced — breeds like Pugs, Bulldogs, and French Bulldogs with shortened skulls"),
     ("BOAS", "Brachycephalic Obstructive Airway Syndrome — breathing problems caused by flat-faced anatomy"),
     ("Tracheal collapse", "Weakening of the tracheal cartilage rings, causing airway narrowing"),
     ("Cyanosis", "Blue or purple discolouration of gums and tongue due to insufficient oxygen")],
    # 22: Senior Dogs
    [("Geriatric", "Relating to old age — senior dogs requiring age-appropriate healthcare"),
     ("Quality of life", "A measure of a dog's overall comfort, happiness, and ability to enjoy daily activities"),
     ("Immunosenescence", "Age-related decline in immune system effectiveness"),
     ("Cognitive decline", "Gradual reduction in mental function including memory, learning, and awareness"),
     ("Palliative care", "Care focused on comfort and quality of life rather than cure of disease")],
    # 23: Food Allergies
    [("Food allergy", "An immune-mediated adverse reaction to specific food proteins"),
     ("Food sensitivity", "A non-immune adverse reaction to food, also called food intolerance"),
     ("Elimination diet", "A diagnostic diet using novel or hydrolysed proteins to identify food allergens"),
     ("Hydrolysed protein", "Protein broken down into tiny fragments too small to trigger an immune response"),
     ("Novel protein", "A protein source the dog has never eaten before, used in elimination diets")],
    # 24: Wellness Plan
    [("Preventive care", "Healthcare measures designed to prevent disease rather than treat it after onset"),
     ("Titre testing", "Blood test measuring antibody levels to assess immunity status"),
     ("Parasite prevention", "Regular treatments to protect against fleas, ticks, worms, and other parasites"),
     ("Health screening", "Routine tests to detect early signs of disease before symptoms appear"),
     ("Lifetime insurance", "Pet insurance that covers conditions for the dog's entire life, including pre-existing claims once covered")],
]


# ── Publishing functions ───────────────────────────────────────────────

def publish_post(title, slug, content, excerpt):
    """Publish a single post via WordPress REST API."""
    data = {
        "title": title,
        "slug": slug,
        "content": content,
        "excerpt": excerpt,
        "status": "publish",
        "categories": [CATEGORY_ID],
    }
    for attempt in range(3):
        try:
            r = session.post(f"{WP_URL}/posts", json=data, timeout=60)
            if r.status_code == 429:
                print(f"  Rate limited, waiting 10s...")
                time.sleep(10)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(5)
    return None


def search_pexels(query):
    """Search Pexels for an image and return the URL."""
    try:
        headers = {"Authorization": PEXELS_KEY}
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params={"query": query, "per_page": 1, "orientation": "landscape"},
            timeout=15
        )
        r.raise_for_status()
        data = r.json()
        if data.get("photos"):
            return data["photos"][0]["src"]["large"]
    except Exception as e:
        print(f"  Pexels search failed: {e}")
    return None


def upload_featured_image(image_url, post_id, filename):
    """Download image from URL and upload as featured image."""
    try:
        img_r = requests.get(image_url, timeout=30, headers={"Accept-Encoding": "gzip, deflate"})
        img_r.raise_for_status()
        content_type = img_r.headers.get("Content-Type", "image/jpeg")

        ext = "jpg"
        if "png" in content_type:
            ext = "png"
        elif "webp" in content_type:
            ext = "webp"

        fname = f"{filename}.{ext}"
        media_headers = {
            "Content-Disposition": f'attachment; filename="{fname}"',
            "Content-Type": content_type,
            "Accept-Encoding": "gzip, deflate",
        }
        upload_r = session.post(
            f"{WP_URL}/media",
            headers=media_headers,
            data=img_r.content,
            timeout=60
        )
        if upload_r.status_code == 429:
            time.sleep(10)
            upload_r = session.post(
                f"{WP_URL}/media",
                headers=media_headers,
                data=img_r.content,
                timeout=60
            )
        upload_r.raise_for_status()
        media_id = upload_r.json().get("id")

        if media_id:
            set_r = session.post(
                f"{WP_URL}/posts/{post_id}",
                json={"featured_media": media_id},
                timeout=30
            )
            set_r.raise_for_status()
            return media_id
    except Exception as e:
        print(f"  Featured image failed: {e}")
    return None


def add_internal_links(results):
    """Add internal links section to each published post."""
    print("\n=== Adding Internal Links ===")
    published = [(r["title"], r["url"], r["post_id"]) for r in results if r.get("post_id")]

    for i, result in enumerate(results):
        if not result.get("post_id"):
            continue

        # Pick 3-4 related posts (not self)
        related = []
        for j, (title, url, pid) in enumerate(published):
            if pid != result["post_id"]:
                related.append((title, url))
        # Take up to 4 related
        related = related[:4] if len(related) > 4 else related

        if not related:
            continue

        links_html = "\n".join([
            f'<li><a href="{url}">{title}</a></li>' for title, url in related
        ])

        internal_block = f"""

<!-- wp:separator -->
<hr class="wp-block-separator has-alpha-channel-opacity"/>
<!-- /wp:separator -->

<!-- wp:heading -->
<h2 class="wp-block-heading">Related Dog Health Guides</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Continue exploring our Dog Health series with these related guides:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list">
{links_html}
</ul>
<!-- /wp:list -->"""

        try:
            # Get current content
            get_r = session.get(f"{WP_URL}/posts/{result['post_id']}", timeout=30)
            get_r.raise_for_status()
            current = get_r.json()
            current_content = current.get("content", {}).get("rendered", "")

            # Append internal links before the affiliate disclosure
            update_r = session.post(
                f"{WP_URL}/posts/{result['post_id']}",
                json={"content": current.get("content", {}).get("raw", "") + internal_block},
                timeout=30
            )
            if update_r.status_code == 429:
                time.sleep(10)
                update_r = session.post(
                    f"{WP_URL}/posts/{result['post_id']}",
                    json={"content": current.get("content", {}).get("raw", "") + internal_block},
                    timeout=30
                )
            update_r.raise_for_status()
            print(f"  [{i+1}] Internal links added to: {result['title']}")
        except Exception as e:
            print(f"  [{i+1}] Failed to add links to {result['title']}: {e}")

        time.sleep(1)


def main():
    results = []
    print(f"=== Phase 22D: Publishing 25 Dog Health Posts ===")
    print(f"Started: {datetime.now().isoformat()}\n")

    for i, topic in enumerate(TOPICS):
        print(f"[{i+1}/25] Publishing: {topic['title']}")

        # Generate content
        content = generate_post_content(topic, i)

        # Publish
        resp = publish_post(topic["title"], topic["slug"], content, topic["excerpt"])

        if resp and resp.get("id"):
            post_id = resp["id"]
            post_url = resp.get("link", "")
            print(f"  Published: ID={post_id}, URL={post_url}")

            # Search Pexels and set featured image
            img_url = search_pexels(topic["pexels"])
            media_id = None
            if img_url:
                media_id = upload_featured_image(img_url, post_id, topic["slug"])
                if media_id:
                    print(f"  Featured image set: media_id={media_id}")

            results.append({
                "index": i + 1,
                "title": topic["title"],
                "slug": topic["slug"],
                "post_id": post_id,
                "url": post_url,
                "media_id": media_id,
                "status": "published"
            })
        else:
            print(f"  FAILED to publish")
            results.append({
                "index": i + 1,
                "title": topic["title"],
                "slug": topic["slug"],
                "post_id": None,
                "url": None,
                "media_id": None,
                "status": "failed"
            })

        # Delay between posts
        if i < len(TOPICS) - 1:
            time.sleep(3)

    # Add internal links
    add_internal_links(results)

    # Save results
    summary = {
        "phase": "22D",
        "category": "Dog Health",
        "category_id": CATEGORY_ID,
        "total_topics": len(TOPICS),
        "published": sum(1 for r in results if r["status"] == "published"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "timestamp": datetime.now().isoformat(),
        "posts": results,
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n=== SUMMARY ===")
    print(f"Published: {summary['published']}/{summary['total_topics']}")
    print(f"Failed: {summary['failed']}/{summary['total_topics']}")
    print(f"Results saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
