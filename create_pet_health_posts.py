#!/usr/bin/env python3
"""
Phase 23: Create and publish 32 Pet Health educational posts on PetHub Online.
Push Pet Health cluster from 8 to 40 posts (OWNED status).
"""

import requests
import json
import time
import os
import re
import sys
import traceback
from datetime import datetime
from urllib.parse import quote

# ── Configuration ──────────────────────────────────────────────────────────
WP_URL = "https://pethubonline.com/wp-json/wp/v2"
WP_AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
WP_HEADERS = {"Accept-Encoding": "gzip, deflate"}
PEXELS_API_KEY = "dmGyKrZqTlwukxWzOK1EkH4jbEv9EaIDpLGj7eL5MZ07bl6AR9OEoHlB"
AMAZON_TAG = "pethubonline-21"
PET_HEALTH_CAT_ID = 1391
RESULTS_PATH = "/var/lib/freelancer/projects/40416335/phase23_pet_health_results.json"
DELAY = 2  # seconds between API calls
RETRY_DELAY = 10  # seconds on 429

# ── Topic Definitions ──────────────────────────────────────────────────────
TOPICS = [
    {
        "title": "How to Create a Pet First Aid Kit at Home",
        "slug": "pet-first-aid-kit-at-home",
        "pexels_query": "pet first aid",
        "meta_desc": "Learn how to create a pet first aid kit at home. Essential supplies, step-by-step guide, and recommended products for UK pet owners.",
        "focus": "first aid kit essentials for pets",
        "products": [
            {"name": "Rosewood Pet First Aid Kit", "asin": "B00BSQFFNY", "price": "£14.99", "desc": "Comprehensive 40-piece pet first aid kit with bandages, wipes, and emergency guide"},
            {"name": "YUEJIDZ Pet First Aid Kit", "asin": "B0D7LHZ4TH", "price": "£16.99", "desc": "Portable 70-piece pet emergency kit with thermal blanket and tick remover"},
            {"name": "Wahl Pet Thermometer", "asin": "B07RM6MXFG", "price": "£9.99", "desc": "Digital pet thermometer with flexible tip for accurate temperature readings"},
        ],
        "sections": {
            "why": "Why Every Pet Owner Needs a First Aid Kit",
            "essentials": "What Should Be in a Pet First Aid Kit?",
            "build": "How to Build Your Pet First Aid Kit Step by Step",
            "use": "How to Use Common First Aid Items on Your Pet",
            "when_vet": "When Should You Go to the Vet Instead?",
        },
        "faqs": [
            ("What should be in a basic pet first aid kit?", "A basic pet first aid kit should include sterile gauze, adhesive bandages, antiseptic wipes, a digital thermometer, tweezers for tick removal, saline solution for eye washing, a muzzle (injured pets may bite), and your vet's emergency contact number."),
            ("Can I use human first aid supplies on my pet?", "Some human first aid items like sterile gauze, saline solution, and adhesive bandages can be used on pets. However, never use human medications such as paracetamol or ibuprofen on pets as these can be toxic. Always check with your vet before using any human product on your pet."),
            ("How often should I replace items in my pet's first aid kit?", "Check your pet first aid kit every 3-6 months. Replace any expired items, restock used supplies, and ensure all packaging is intact. Medications and antiseptic solutions typically expire within 1-2 years."),
            ("Where should I keep my pet's first aid kit?", "Keep your pet first aid kit in an easily accessible location that all family members know about. Consider keeping a smaller portable kit in your car for walks and trips. Store it in a cool, dry place away from direct sunlight."),
            ("Should I take a pet first aid course?", "Yes, taking a pet first aid course is highly recommended. Organisations like the PDSA, Blue Cross, and St John Ambulance offer pet first aid training courses across the UK. These teach practical skills like CPR, wound care, and how to handle emergencies."),
        ],
    },
    {
        "title": "Complete Guide to Pet Worming Schedules UK",
        "slug": "pet-worming-schedules-uk",
        "pexels_query": "dog health medicine",
        "meta_desc": "Complete guide to pet worming schedules in the UK. Learn when and how to worm your dog or cat, recommended products, and prevention tips.",
        "focus": "pet worming schedule UK",
        "products": [
            {"name": "Drontal Dog Worming Tablets", "asin": "B07D5LGWG5", "price": "£8.49", "desc": "Broad-spectrum worming tablets for dogs, treats roundworm and tapeworm"},
            {"name": "Panacur Wormer Granules", "asin": "B00BB4FV2M", "price": "£11.99", "desc": "Veterinary strength granules for dogs treating all common worms"},
            {"name": "Bob Martin Clear Wormer for Cats", "asin": "B00FWA3FPK", "price": "£5.99", "desc": "Easy-to-administer worming tablets for cats covering roundworm and tapeworm"},
        ],
        "sections": {
            "why": "Why Is Regular Worming Important for Pets?",
            "types": "What Types of Worms Affect Pets in the UK?",
            "schedule_dogs": "What Is the Recommended Worming Schedule for Dogs?",
            "schedule_cats": "What Is the Recommended Worming Schedule for Cats?",
            "signs": "How Can You Tell If Your Pet Has Worms?",
        },
        "faqs": [
            ("How often should I worm my adult dog?", "Adult dogs should be wormed at least every 3 months (four times a year). Dogs that hunt, scavenge, or live with young children may need more frequent worming. Puppies need worming more often — every 2 weeks until 12 weeks old, then monthly until 6 months old."),
            ("How often should I worm my cat?", "Adult cats should be wormed every 3 months. Cats that hunt regularly may need monthly treatment. Kittens should be wormed from 3 weeks old, then every 2 weeks until 8 weeks, and monthly until 6 months old."),
            ("Can worms from pets spread to humans?", "Yes, some pet worms can spread to humans (zoonotic transmission). Toxocara roundworms from dogs and cats can cause toxocariasis in humans, particularly children. This is why regular worming and good hygiene — especially handwashing — are essential."),
            ("What are the signs of worms in pets?", "Common signs include visible worms in faeces or around the bottom, scooting (dragging bottom along the floor), weight loss despite normal appetite, bloated stomach (especially in puppies/kittens), dull coat, diarrhoea, and vomiting."),
            ("Do indoor cats need worming?", "Yes, indoor cats still need regular worming. They can pick up worms from contaminated soil on shoes, from fleas (which carry tapeworm larvae), from hunting insects, or from other pets in the household. Worm indoor cats at least every 3-6 months."),
        ],
    },
    {
        "title": "How to Check Your Pet's Vital Signs at Home",
        "slug": "check-pets-vital-signs-at-home",
        "pexels_query": "pet health check veterinary",
        "meta_desc": "Learn how to check your pet's vital signs at home including heart rate, breathing rate, temperature, and gum colour. Essential monitoring guide for UK pet owners.",
        "focus": "checking pet vital signs at home",
        "products": [
            {"name": "Wahl Pet Thermometer", "asin": "B07RM6MXFG", "price": "£9.99", "desc": "Digital pet thermometer with flexible tip for safe, accurate readings"},
            {"name": "3M Littmann Classic III Stethoscope", "asin": "B00GXLY898", "price": "£89.99", "desc": "High-quality stethoscope for monitoring pet heart rate and breathing"},
            {"name": "Pet Wellness Journal", "asin": "B0CX56MM2T", "price": "£7.99", "desc": "Health tracking journal for recording your pet's vital signs and symptoms"},
        ],
        "sections": {
            "why": "Why Should You Monitor Your Pet's Vital Signs?",
            "heart_rate": "How to Check Your Pet's Heart Rate",
            "breathing": "How to Monitor Your Pet's Breathing Rate",
            "temperature": "How to Take Your Pet's Temperature Safely",
            "gums": "What Do Your Pet's Gums Tell You About Their Health?",
        },
        "faqs": [
            ("What is a normal heart rate for a dog?", "Normal resting heart rate for dogs varies by size: small dogs 100-140 beats per minute, medium dogs 80-120 bpm, and large dogs 60-100 bpm. Puppies may have higher rates up to 220 bpm. Count beats for 15 seconds and multiply by 4."),
            ("What is a normal heart rate for a cat?", "A normal resting heart rate for a cat is 120-140 beats per minute. Kittens may have rates up to 200 bpm. You can feel the heartbeat by placing your hand on the left side of the chest, just behind the front leg."),
            ("What should my pet's temperature be?", "Normal body temperature for dogs is 38.3-39.2°C (101-102.5°F) and for cats is 38.1-39.2°C (100.5-102.5°F). A temperature above 39.5°C or below 37.5°C requires veterinary attention."),
            ("What colour should my pet's gums be?", "Healthy gum colour is pink (like bubblegum). Pale or white gums may indicate anaemia or shock. Blue or purple gums suggest oxygen deprivation. Bright red gums can indicate overheating or carbon monoxide poisoning. Yellow gums may indicate liver problems."),
            ("How often should I check my pet's vital signs?", "Get into the habit of checking your pet's vital signs weekly when they are healthy. This helps you learn what is normal for your individual pet. During illness or recovery, check more frequently as directed by your vet."),
        ],
    },
    {
        "title": "Pet Flea Prevention: Year-Round Protection Guide UK",
        "slug": "pet-flea-prevention-year-round-uk",
        "pexels_query": "dog scratching fleas",
        "meta_desc": "Year-round flea prevention guide for UK pets. Learn about flea treatments, prevention methods, and the best products to keep your pet flea-free.",
        "focus": "year-round flea prevention for pets UK",
        "products": [
            {"name": "Frontline Plus Flea Treatment for Dogs", "asin": "B002AKK05K", "price": "£18.99", "desc": "Spot-on flea and tick treatment providing 4 weeks of protection for dogs"},
            {"name": "Seresto Flea and Tick Collar for Cats", "asin": "B00B8CG59A", "price": "£27.49", "desc": "Long-lasting 8-month flea and tick collar for cats"},
            {"name": "Indorex Flea Spray", "asin": "B003YMNHNI", "price": "£12.99", "desc": "Household flea spray that kills fleas and prevents re-infestation for up to 12 months"},
        ],
        "sections": {
            "why": "Why Is Year-Round Flea Prevention Essential?",
            "lifecycle": "Understanding the Flea Life Cycle",
            "treatments": "What Types of Flea Treatments Are Available?",
            "home": "How to Treat Your Home for Fleas",
            "signs": "How to Tell If Your Pet Has Fleas",
        },
        "faqs": [
            ("Do I need flea treatment in winter?", "Yes, fleas can survive indoors year-round thanks to central heating. While flea activity peaks in warmer months, UK homes provide ideal conditions for fleas throughout winter. Year-round treatment prevents costly infestations."),
            ("How often should I apply flea treatment?", "This depends on the product type. Spot-on treatments typically last 4 weeks, flea collars can last 6-8 months, and oral tablets may provide 1-3 months of protection. Always follow the specific product instructions."),
            ("Can I use dog flea treatment on my cat?", "Never use dog flea treatments on cats. Some dog flea treatments contain permethrin, which is highly toxic and potentially fatal to cats. Always use species-specific products and keep treated dogs away from cats until the treatment has dried."),
            ("How do I know if my pet has fleas?", "Look for excessive scratching, biting at the skin, red irritated skin, flea dirt (small black specks in the fur), and visible fleas. Run a fine-toothed flea comb through your pet's coat — place any debris on a wet white tissue; if it turns reddish-brown, it is flea dirt."),
            ("How long does it take to get rid of a flea infestation?", "A flea infestation can take 2-3 months to fully resolve because you must break the flea life cycle. Treat all pets in the household simultaneously, wash bedding at 60°C, vacuum thoroughly, and use a household flea spray. Continue pet flea treatment consistently."),
        ],
    },
    {
        "title": "How to Recognise Signs of Dehydration in Pets",
        "slug": "signs-of-dehydration-in-pets",
        "pexels_query": "dog drinking water bowl",
        "meta_desc": "Learn how to recognise signs of dehydration in dogs and cats. Quick checks, prevention tips, and when to seek emergency veterinary help.",
        "focus": "recognising pet dehydration signs",
        "products": [
            {"name": "PetSafe Drinkwell Water Fountain", "asin": "B000L3XYZ4", "price": "£29.99", "desc": "Flowing water fountain encouraging pets to drink more throughout the day"},
            {"name": "Catit Flower Water Fountain", "asin": "B0146QXOB0", "price": "£22.99", "desc": "3L cat water fountain with three water flow settings"},
            {"name": "Oralade GI Support Drink", "asin": "B01FVON29O", "price": "£8.49", "desc": "Isotonic rehydration support drink designed specifically for pets"},
        ],
        "sections": {
            "why": "Why Is Hydration So Important for Pets?",
            "signs": "What Are the Signs of Dehydration in Dogs and Cats?",
            "skin_test": "How to Do the Skin Turgor Test on Your Pet",
            "prevent": "How to Prevent Dehydration in Pets",
            "emergency": "When Is Dehydration a Veterinary Emergency?",
        },
        "faqs": [
            ("How much water should my dog drink daily?", "Dogs generally need 50-60ml of water per kilogram of body weight per day. A 10kg dog should drink approximately 500-600ml daily. Water intake increases during hot weather, after exercise, and when eating dry food."),
            ("How much water should my cat drink daily?", "Cats need approximately 40-60ml of water per kilogram of body weight daily. A 4kg cat should drink around 160-240ml per day. Cats eating wet food get some moisture from their food and may drink less."),
            ("How do I check if my pet is dehydrated?", "Gently pinch the skin on the back of your pet's neck and release. In a well-hydrated pet, the skin snaps back immediately. If it returns slowly or stays tented, your pet may be dehydrated. Also check for dry, tacky gums and sunken eyes."),
            ("What causes dehydration in pets?", "Common causes include vomiting, diarrhoea, fever, excessive panting, kidney disease, diabetes, not drinking enough water, and hot weather. Puppies, kittens, and senior pets are more vulnerable to dehydration."),
            ("Can I give my pet electrolyte drinks?", "Do not give human electrolyte drinks like Lucozade Sport or Dioralyte to pets without veterinary guidance. Pet-specific rehydration solutions are available. In mild cases, offering fresh water frequently is usually sufficient. Severe dehydration requires veterinary treatment with intravenous fluids."),
        ],
    },
    {
        "title": "Pet Vaccination FAQs: What UK Pet Owners Need to Know",
        "slug": "pet-vaccination-faqs-uk",
        "pexels_query": "puppy veterinary vaccination",
        "meta_desc": "Everything UK pet owners need to know about pet vaccinations. Schedules, core vaccines, boosters, costs, and common questions answered.",
        "focus": "pet vaccination guide UK",
        "products": [
            {"name": "Pet Health Record Book", "asin": "B0CX56MM2T", "price": "£7.99", "desc": "Comprehensive health record book to track vaccinations, treatments, and vet visits"},
            {"name": "Pet Carrier for Vet Visits", "asin": "B071KPSGL5", "price": "£24.99", "desc": "Comfortable, well-ventilated pet carrier ideal for trips to the vet"},
            {"name": "Adaptil Calm Spray", "asin": "B0035KSJA6", "price": "£12.49", "desc": "Calming pheromone spray to reduce stress during vet visits"},
        ],
        "sections": {
            "core": "What Are the Core Vaccines for Dogs and Cats in the UK?",
            "schedule": "What Is the Recommended Vaccination Schedule?",
            "boosters": "How Often Do Pets Need Booster Vaccinations?",
            "side_effects": "What Are the Possible Side Effects of Pet Vaccinations?",
            "travel": "What Vaccinations Does My Pet Need for Travel?",
        },
        "faqs": [
            ("What are core vaccinations for dogs in the UK?", "Core vaccinations for dogs in the UK protect against distemper, parvovirus, infectious hepatitis (adenovirus), and leptospirosis. Kennel cough (Bordetella) vaccination is also commonly recommended, especially for dogs that socialise with other dogs."),
            ("What are core vaccinations for cats in the UK?", "Core vaccinations for cats protect against feline parvovirus (feline infectious enteritis), feline calicivirus, and feline herpesvirus (cat flu). Feline leukaemia virus (FeLV) vaccination is recommended for cats that go outdoors."),
            ("When should puppies have their first vaccination?", "Puppies typically receive their first vaccination at 6-8 weeks of age, with a second dose at 10-12 weeks. Some vaccine protocols include a third dose at 14-16 weeks. Puppies should not go to public areas until 1-2 weeks after their final puppy vaccination."),
            ("Are pet vaccinations mandatory in the UK?", "Pet vaccinations are not legally mandatory in the UK for domestic pets. However, a rabies vaccination is legally required for pets travelling abroad under the Animal Health Certificate scheme. Vaccinations are strongly recommended by veterinary professionals to prevent serious diseases."),
            ("How much do pet vaccinations cost in the UK?", "Primary puppy vaccinations typically cost £50-£80, and kitten vaccinations £50-£70. Annual boosters usually cost £40-£60. Costs vary by region and veterinary practice. Charities like PDSA and Blue Cross offer reduced-cost vaccinations for eligible owners."),
        ],
    },
    {
        "title": "How to Monitor Your Pet's Weight at Home",
        "slug": "monitor-pets-weight-at-home",
        "pexels_query": "dog on weighing scale",
        "meta_desc": "Learn how to monitor your pet's weight at home with body condition scoring, weighing techniques, and tips for maintaining a healthy weight.",
        "focus": "monitoring pet weight at home",
        "products": [
            {"name": "Salter Pet Weighing Scale", "asin": "B0000C609U", "price": "£34.99", "desc": "Precision digital scale suitable for weighing pets up to 150kg"},
            {"name": "Catit Senses Food Puzzle", "asin": "B00D3NI2PG", "price": "£8.99", "desc": "Interactive food puzzle to slow down eating and support weight management"},
            {"name": "Kong Classic Dog Toy", "asin": "B0002AR0I8", "price": "£7.49", "desc": "Durable treat-dispensing toy that encourages active play and mental stimulation"},
        ],
        "sections": {
            "why": "Why Is Monitoring Your Pet's Weight Important?",
            "weigh": "How to Weigh Your Pet at Home",
            "bcs": "What Is Body Condition Scoring?",
            "ideal": "What Is the Ideal Weight for My Pet?",
            "manage": "How to Help Your Pet Reach a Healthy Weight",
        },
        "faqs": [
            ("How often should I weigh my pet?", "Weigh your pet at least once a month. Puppies and kittens should be weighed weekly during their growth phase. Pets on a weight management plan should be weighed every 1-2 weeks. Always weigh at the same time of day for consistency."),
            ("How do I weigh my cat at home?", "Weigh yourself on bathroom scales, then pick up your cat and weigh again. Subtract your weight from the combined weight. Alternatively, place your cat in a carrier on the scales and subtract the carrier weight. Baby scales also work well for cats."),
            ("What is body condition scoring?", "Body condition scoring (BCS) is a hands-on assessment of your pet's body fat. Using a 1-9 scale, you evaluate the ribs, waist, and abdominal tuck. A score of 4-5 is ideal. You should be able to feel ribs easily without pressing hard, and see a visible waist when viewed from above."),
            ("How much weight gain is concerning in pets?", "Even small weight changes can be significant. A 1kg gain in a 5kg cat is equivalent to roughly 14kg in an average human. A sudden weight gain or loss of more than 5-10% of body weight warrants a veterinary check, as it could indicate an underlying health condition."),
            ("Is my pet overweight?", "Signs your pet may be overweight include: difficulty feeling ribs under a layer of fat, no visible waist when viewed from above, a rounded or sagging belly, reluctance to exercise, and heavy breathing during light activity. Your vet can confirm with a body condition assessment."),
        ],
    },
    {
        "title": "Pet Dental Health: Preventing Gum Disease and Tooth Decay",
        "slug": "pet-dental-health-preventing-gum-disease",
        "pexels_query": "dog teeth dental health",
        "meta_desc": "Complete guide to pet dental health. Learn how to prevent gum disease and tooth decay in dogs and cats with brushing tips, dental products, and warning signs.",
        "focus": "pet dental health and gum disease prevention",
        "products": [
            {"name": "Virbac C.E.T. Enzymatic Dog Toothpaste", "asin": "B01AAFQZ0Y", "price": "£10.49", "desc": "Enzymatic toothpaste specifically formulated for dogs, poultry flavoured"},
            {"name": "Pedigree Dentastix Daily Dental Chews", "asin": "B003377N2E", "price": "£15.99", "desc": "Daily dental chews clinically proven to reduce tartar build-up in dogs"},
            {"name": "Mind Up Cat Toothbrush", "asin": "B00EPNAPUE", "price": "£6.99", "desc": "Gentle finger toothbrush designed for easy cat dental care"},
        ],
        "sections": {
            "why": "Why Is Dental Health Important for Pets?",
            "signs": "What Are the Signs of Dental Disease in Pets?",
            "brushing": "How to Brush Your Pet's Teeth",
            "alternatives": "What Are Alternatives to Toothbrushing for Pets?",
            "professional": "When Does Your Pet Need Professional Dental Cleaning?",
        },
        "faqs": [
            ("How often should I brush my pet's teeth?", "Ideally, brush your pet's teeth daily. If daily brushing is not possible, aim for at least 3 times per week. Consistency is more important than perfection — even a quick 30-second brush is better than nothing."),
            ("Can I use human toothpaste on my pet?", "Never use human toothpaste on pets. Human toothpaste contains fluoride and foaming agents like sodium lauryl sulphate that can make pets ill if swallowed. Always use pet-specific enzymatic toothpaste that is safe to swallow."),
            ("At what age should I start brushing my pet's teeth?", "Start handling your pet's mouth as early as possible. Begin proper brushing once adult teeth come in — around 6-7 months for dogs and 6 months for cats. Start slowly with short sessions and lots of positive reinforcement."),
            ("How common is dental disease in pets?", "Dental disease is extremely common in pets. According to veterinary research, around 80% of dogs and 70% of cats show signs of dental disease by age 3. Regular dental care can significantly reduce this risk and improve overall health."),
            ("What does a professional dental cleaning involve?", "A professional dental cleaning (scale and polish) is performed under general anaesthesia. It involves full examination, scaling to remove plaque and tartar, polishing, and sometimes dental X-rays. Diseased teeth may need extraction. Costs typically range from £150-£400 depending on the extent of work needed."),
        ],
    },
    {
        "title": "How to Spot Signs of Stress in Your Pet",
        "slug": "signs-of-stress-in-pets",
        "pexels_query": "anxious dog hiding",
        "meta_desc": "Learn how to spot signs of stress in dogs and cats. Understand body language, common stressors, and effective calming strategies for pets.",
        "focus": "recognising stress signs in pets",
        "products": [
            {"name": "Adaptil Calm Home Diffuser", "asin": "B0035KSJA6", "price": "£19.99", "desc": "Clinically proven calming pheromone diffuser for stressed dogs"},
            {"name": "Feliway Classic Diffuser", "asin": "B0018NEPGA", "price": "£21.99", "desc": "Synthetic feline pheromone diffuser to reduce stress and anxiety in cats"},
            {"name": "PetSafe Anxiety Wrap", "asin": "B003J4Q5FI", "price": "£27.99", "desc": "Pressure wrap that applies gentle, constant pressure to calm anxious pets"},
        ],
        "sections": {
            "dog_signs": "What Are the Signs of Stress in Dogs?",
            "cat_signs": "What Are the Signs of Stress in Cats?",
            "causes": "What Commonly Causes Stress in Pets?",
            "reduce": "How to Reduce Stress in Your Pet",
            "when_help": "When Should You Seek Professional Help for a Stressed Pet?",
        },
        "faqs": [
            ("What are common signs of stress in dogs?", "Common signs include excessive panting, pacing, whining, drooling, yawning, lip licking, tucked tail, flattened ears, whale eye (showing whites of eyes), hiding, destructive behaviour, loss of appetite, and digestive upset. Each dog may show different combinations of these signs."),
            ("What are common signs of stress in cats?", "Stressed cats may hide more, groom excessively (sometimes creating bald patches), spray urine, stop using the litter tray, become aggressive or withdrawn, eat less, vocalise more, or develop cystitis (stress-related bladder problems). Changes in normal behaviour are key indicators."),
            ("Can stress make my pet ill?", "Yes, chronic stress can significantly impact your pet's physical health. It can weaken the immune system, worsen skin conditions, cause digestive problems, trigger urinary issues in cats (feline idiopathic cystitis), and contribute to behavioural problems. Addressing stress is an important part of overall pet health."),
            ("How can I help my stressed pet?", "Provide a safe, quiet space where your pet can retreat. Maintain consistent routines for feeding and walks. Use pheromone products (Adaptil for dogs, Feliway for cats). Ensure adequate exercise and mental stimulation. Gradually desensitise them to known stressors. Avoid punishment, which increases stress."),
            ("Should I see a behaviourist for my pet's stress?", "If your pet's stress is severe, persistent, or affecting their quality of life despite your efforts, consult your vet first to rule out medical causes. They may refer you to a certified animal behaviourist (ABTC-registered in the UK). Behaviourists can create tailored plans to address the root causes of stress."),
        ],
    },
    {
        "title": "Pet Microchipping Guide UK: Legal Requirements and Benefits",
        "slug": "pet-microchipping-guide-uk",
        "pexels_query": "dog microchip veterinary",
        "meta_desc": "Complete guide to pet microchipping in the UK. Legal requirements, how microchipping works, keeping details updated, and benefits for pet safety.",
        "focus": "pet microchipping UK legal requirements",
        "products": [
            {"name": "Pet ID Tag Engraved", "asin": "B072MPNG7V", "price": "£4.99", "desc": "Personalised engraved pet ID tag with contact details — legally required alongside microchip"},
            {"name": "Pet Health Record Book", "asin": "B0CX56MM2T", "price": "£7.99", "desc": "Record book to store microchip number, vaccination records, and vet details"},
            {"name": "Tractive GPS Dog Tracker", "asin": "B07B4SZFV2", "price": "£44.99", "desc": "Real-time GPS tracker for dogs with activity monitoring and virtual fence alerts"},
        ],
        "sections": {
            "law": "What Are the UK Microchipping Laws?",
            "how": "How Does Pet Microchipping Work?",
            "update": "How to Keep Your Microchip Details Up to Date",
            "benefits": "What Are the Benefits of Microchipping?",
            "myths": "Common Microchipping Myths Debunked",
        },
        "faqs": [
            ("Is it a legal requirement to microchip my dog in the UK?", "Yes, all dogs in England, Scotland, and Wales must be microchipped by 8 weeks of age under the Microchipping of Dogs (England) Regulations 2015, with similar laws in Scotland and Wales. Failure to comply can result in a fine of up to £500."),
            ("Is it a legal requirement to microchip my cat in the UK?", "Yes, as of June 2024, all cats in England must be microchipped by 20 weeks of age under the Microchipping of Cats (England) Regulations 2023. Cat owners who fail to microchip face a fine of up to £500 if they do not comply within 21 days of being served a notice."),
            ("Does microchipping hurt my pet?", "Microchipping is a quick procedure similar to a routine vaccination. The microchip (about the size of a grain of rice) is injected under the skin between the shoulder blades. Most pets show minimal reaction. No anaesthesia is needed. The procedure takes just seconds."),
            ("How much does microchipping cost?", "Microchipping typically costs £10-£30 at a veterinary practice. Many animal charities including the PDSA, Dogs Trust, and Blue Cross offer free or reduced-cost microchipping. Some local councils also run free microchipping events."),
            ("What should I do if I move house or change phone number?", "You must update your microchip details whenever your contact information changes. Contact your microchip database provider (such as Petlog, PetScanner, or MicroChipCentral) to update your address, phone number, and other details. Keeping details current is essential — an out-of-date microchip cannot reunite you with a lost pet."),
        ],
    },
    {
        "title": "How to Prepare Your Pet for a Vet Visit",
        "slug": "prepare-pet-for-vet-visit",
        "pexels_query": "cat carrier vet visit",
        "meta_desc": "Tips for preparing your pet for a vet visit. Reduce stress, what to bring, handling nervous pets, and making vet trips easier for dogs and cats.",
        "focus": "preparing pets for vet visits",
        "products": [
            {"name": "Feliway Classic Spray", "asin": "B001B4SNE8", "price": "£11.99", "desc": "Calming pheromone spray for cat carriers and vet waiting rooms"},
            {"name": "AmazonBasics Pet Carrier", "asin": "B00OP6SVJW", "price": "£19.99", "desc": "Well-ventilated, secure pet carrier with top and side openings"},
            {"name": "Adaptil Transport Spray", "asin": "B008N7HK9C", "price": "£10.99", "desc": "Calming spray for dogs during car journeys and vet visits"},
        ],
        "sections": {
            "prep": "How Should You Prepare Before the Vet Visit?",
            "carrier": "How to Get Your Pet Comfortable with a Carrier",
            "journey": "Tips for a Stress-Free Journey to the Vet",
            "waiting": "How to Keep Your Pet Calm in the Waiting Room",
            "after": "What to Do After the Vet Visit",
        },
        "faqs": [
            ("How can I make vet visits less stressful for my cat?", "Leave the carrier out at home permanently with comfortable bedding inside. Spray with Feliway 30 minutes before travel. Cover the carrier with a towel during the journey. Choose a cat-friendly practice if possible. Avoid feeding for 2-3 hours before the visit in case of car sickness."),
            ("What should I bring to a vet appointment?", "Bring your pet's vaccination record or pet passport, a list of any medications they are taking, a note of any symptoms or changes in behaviour, a fresh faecal sample if requested, treats for positive reinforcement, and a secure lead or carrier."),
            ("How can I reduce my dog's fear of the vet?", "Make happy visits — pop into the surgery just for treats and a fuss from staff. Use positive associations with car travel. Practice handling your dog's ears, paws, and mouth at home. Use calming products like Adaptil. Stay calm yourself, as dogs pick up on your anxiety."),
            ("Should I stay with my pet during examinations?", "Most vets welcome owners staying during routine examinations. Your presence can comfort your pet. However, for some procedures, the vet may ask you to wait outside. Trust the veterinary team's judgement — sometimes pets are calmer without their owner present."),
            ("How often should my pet see the vet?", "Healthy adult pets should have a check-up at least once a year. Puppies and kittens need more frequent visits for vaccinations and growth monitoring. Senior pets (over 7-8 years) benefit from twice-yearly health checks to catch age-related conditions early."),
        ],
    },
    {
        "title": "Pet Nutrition Basics: Understanding Pet Food Labels UK",
        "slug": "pet-nutrition-understanding-food-labels-uk",
        "pexels_query": "dog food bowl nutrition",
        "meta_desc": "Understand pet food labels in the UK. Learn what ingredients mean, nutritional requirements, how to compare brands, and choose the right food for your pet.",
        "focus": "understanding pet food labels UK",
        "products": [
            {"name": "Lily's Kitchen Adult Dog Food", "asin": "B009L4XVSS", "price": "£24.99", "desc": "Natural, complete dry food for adult dogs with freshly prepared meat"},
            {"name": "Applaws Natural Cat Food", "asin": "B003TNXWDG", "price": "£17.99", "desc": "High-protein, grain-free natural cat food with real meat"},
            {"name": "Slow Feeder Dog Bowl", "asin": "B00FPKNR8K", "price": "£9.99", "desc": "Anti-gulp slow feeder bowl promoting healthier eating habits"},
        ],
        "sections": {
            "labels": "How to Read Pet Food Labels in the UK",
            "ingredients": "What Do Ingredients Lists Really Mean?",
            "complete_vs_complementary": "What Is the Difference Between Complete and Complementary Pet Food?",
            "requirements": "What Are the Nutritional Requirements for Dogs and Cats?",
            "choosing": "How to Choose the Right Food for Your Pet",
        },
        "faqs": [
            ("What does 'complete' pet food mean?", "'Complete' pet food means it contains all the nutrients your pet needs in the correct proportions. A pet fed exclusively on a complete food should not need any additional supplements. This is regulated by FEDIAF (European Pet Food Industry Federation) guidelines in the UK."),
            ("What does 'complementary' pet food mean?", "'Complementary' food is designed to be fed alongside other foods — it does not provide all necessary nutrients on its own. Treats, mixer biscuits, and some wet foods are complementary. Always check the label and ensure your pet's overall diet is nutritionally complete."),
            ("Should I feed my pet wet or dry food?", "Both wet and dry food can provide complete nutrition. Wet food has higher moisture content (good for hydration), while dry food can be better for dental health and is more economical. Many owners feed a combination. The best choice depends on your pet's individual needs, preferences, and any health conditions."),
            ("What ingredients should I avoid in pet food?", "Watch for excessive fillers (large amounts of cereals or grains listed first), artificial colours and flavours, unnamed meat sources (like 'animal derivatives' without specifying the animal), added sugars, and excessive salt. Higher-quality foods tend to list specific named meat sources as the primary ingredient."),
            ("How much should I feed my pet?", "Follow the feeding guidelines on the packaging as a starting point, adjusting based on your pet's age, weight, activity level, and body condition. Weigh food portions rather than estimating. Monitor your pet's weight regularly and adjust portions accordingly. Your vet can provide personalised feeding advice."),
        ],
    },
    {
        "title": "How to Help Your Pet Recover from Illness",
        "slug": "help-pet-recover-from-illness",
        "pexels_query": "sick dog resting recovery",
        "meta_desc": "How to help your pet recover from illness at home. Nursing care tips, medication advice, nutrition during recovery, and signs to watch for.",
        "focus": "pet illness recovery care at home",
        "products": [
            {"name": "Royal Canin Recovery Diet", "asin": "B003AKWBYG", "price": "£15.99", "desc": "Veterinary recovery diet for cats and dogs providing high-energy nutrition during illness"},
            {"name": "Pet Remedy Calming Spray", "asin": "B00FWA4IPC", "price": "£9.99", "desc": "Natural calming spray to help pets relax during recovery"},
            {"name": "Snuggle Safe Heat Pad", "asin": "B00008AJH2", "price": "£16.99", "desc": "Microwave heat pad providing 10 hours of safe warmth for recovering pets"},
        ],
        "sections": {
            "environment": "How to Create a Comfortable Recovery Space",
            "medication": "How to Give Your Pet Medication",
            "nutrition": "What Should You Feed a Recovering Pet?",
            "monitoring": "What Signs Should You Watch for During Recovery?",
            "follow_up": "When to Schedule Follow-Up Vet Visits",
        },
        "faqs": [
            ("How do I give my pet tablets?", "For dogs, hide the tablet in a small piece of soft food or a pill pocket treat. For cats, use a pill popper tool or wrap the tablet in a small amount of soft food. Always check with your vet whether tablets can be given with food. Remain calm and positive, and reward your pet afterwards."),
            ("How long does recovery from illness usually take?", "Recovery time varies greatly depending on the illness, your pet's age, and overall health. Minor infections may resolve in a few days, while more serious conditions could take weeks or months. Follow your vet's guidance on expected recovery timelines and attend all follow-up appointments."),
            ("Should I restrict my pet's activity during recovery?", "Follow your vet's specific advice on activity restriction. Generally, recovering pets benefit from reduced activity — shorter walks for dogs, keeping cats indoors. Avoid rough play, jumping, and stairs if advised. Gradually increase activity as your vet recommends."),
            ("What should I feed my pet during recovery?", "Your vet may recommend a specific recovery diet that is highly digestible and energy-dense. If not, offer small, frequent meals of your pet's regular food. Ensure fresh water is always available. Some pets may have reduced appetite during illness — tempt them with slightly warmed food."),
            ("When should I be concerned during my pet's recovery?", "Contact your vet if your pet stops eating or drinking for more than 24 hours, develops vomiting or diarrhoea, seems to be getting worse rather than better, shows signs of pain (whimpering, guarding, aggression), has difficulty breathing, or if their medication causes adverse reactions."),
        ],
    },
    {
        "title": "Pet Parasite Prevention: Fleas, Ticks, and Worms Guide",
        "slug": "pet-parasite-prevention-fleas-ticks-worms",
        "pexels_query": "veterinary pet treatment",
        "meta_desc": "Complete guide to pet parasite prevention covering fleas, ticks, and worms. Treatment schedules, product recommendations, and prevention tips for UK pets.",
        "focus": "pet parasite prevention guide UK",
        "products": [
            {"name": "Frontline Plus for Dogs", "asin": "B002AKK05K", "price": "£18.99", "desc": "Combined flea and tick spot-on treatment for dogs, 4-week protection"},
            {"name": "Drontal Dog Wormer", "asin": "B07D5LGWG5", "price": "£8.49", "desc": "Broad-spectrum worming tablets treating roundworm and tapeworm"},
            {"name": "O'Tom Tick Twister", "asin": "B0002YHFQI", "price": "£3.99", "desc": "Safe tick removal tool that removes ticks without squeezing the body"},
        ],
        "sections": {
            "overview": "What Parasites Affect Pets in the UK?",
            "fleas": "How to Prevent and Treat Flea Infestations",
            "ticks": "How to Protect Your Pet from Ticks",
            "worms": "How to Prevent Worm Infestations in Pets",
            "schedule": "What Is the Recommended Parasite Prevention Schedule?",
        },
        "faqs": [
            ("Do I need to treat my pet for all parasites year-round?", "Yes, year-round parasite prevention is recommended in the UK. Fleas thrive indoors in winter due to central heating, ticks are active from March to November (though some are active year-round), and worm infections can occur at any time. Consistent treatment prevents infestations."),
            ("Can I use one product for fleas, ticks, and worms?", "Some combined products cover multiple parasites, but no single product covers everything. Your vet can recommend the best combination for your pet. Common approaches include a monthly spot-on for fleas and ticks combined with a quarterly wormer."),
            ("How do I safely remove a tick from my pet?", "Use a tick removal tool (tick twister or tick hook) to grasp the tick as close to the skin as possible. Twist gently and pull upward with steady pressure. Do not squeeze, burn, or apply chemicals to the tick, as this can cause it to regurgitate bacteria into your pet. Clean the area with antiseptic afterwards."),
            ("Are natural parasite treatments effective?", "Most natural remedies (garlic, essential oils, herbal collars) have limited scientific evidence supporting their effectiveness against parasites. Some can even be harmful — garlic is toxic to dogs and cats, and certain essential oils are dangerous for cats. Veterinary-recommended products have proven efficacy and safety data."),
            ("What diseases can parasites transmit to pets?", "Fleas can transmit tapeworms and cause flea allergy dermatitis. Ticks can transmit Lyme disease, babesiosis, and ehrlichiosis. Lungworm (Angiostrongylus vasorum), transmitted by slugs and snails, can be fatal in dogs. Roundworms can cause toxocariasis in humans, particularly children."),
        ],
    },
    {
        "title": "How to Recognise Allergies in Pets",
        "slug": "recognise-allergies-in-pets",
        "pexels_query": "dog itching scratching allergy",
        "meta_desc": "Learn how to recognise allergies in dogs and cats. Common allergens, symptoms, diagnosis, treatment options, and management tips for UK pet owners.",
        "focus": "recognising pet allergies symptoms",
        "products": [
            {"name": "Yumega Plus Skin and Coat Oil", "asin": "B003U2NQYA", "price": "£15.99", "desc": "Omega oil supplement to support skin health and reduce itching in dogs"},
            {"name": "Vet's Best Allergy Itch Relief Shampoo", "asin": "B004NTJI90", "price": "£9.99", "desc": "Soothing oatmeal shampoo for dogs with itchy, sensitive skin"},
            {"name": "Protexin Pro-Fibre", "asin": "B004O6NJGA", "price": "£11.49", "desc": "Prebiotic and fibre supplement supporting digestive health and immunity in pets"},
        ],
        "sections": {
            "types": "What Types of Allergies Affect Pets?",
            "signs": "What Are the Signs of Allergies in Dogs and Cats?",
            "diagnosis": "How Are Pet Allergies Diagnosed?",
            "treatment": "What Treatment Options Are Available for Pet Allergies?",
            "management": "How to Manage Your Pet's Allergies Long-Term",
        },
        "faqs": [
            ("What are the most common allergies in pets?", "The most common pet allergies are flea allergy dermatitis (an allergic reaction to flea saliva), environmental allergies (atopy — reacting to pollen, dust mites, or mould), and food allergies (reactions to specific proteins such as beef, chicken, dairy, or wheat)."),
            ("How can I tell if my pet has a food allergy?", "Food allergy symptoms include itchy skin (especially around the face, ears, and paws), recurrent ear infections, chronic digestive issues (vomiting, diarrhoea, wind), and licking or chewing at paws. Symptoms are non-seasonal — they occur year-round regardless of the time of year."),
            ("What is an elimination diet for pets?", "An elimination diet involves feeding your pet a novel protein source (one they have never eaten before) or a hydrolysed diet for 8-12 weeks. If symptoms improve, individual ingredients are reintroduced one at a time to identify the specific allergen. This should be done under veterinary guidance."),
            ("Can pets develop allergies at any age?", "Yes, although allergies most commonly develop between 1 and 3 years of age. Some breeds are more predisposed — French Bulldogs, Labradors, Golden Retrievers, and West Highland White Terriers are among the breeds more prone to allergies. Allergies can worsen over time without proper management."),
            ("Are antihistamines safe for pets?", "Some antihistamines can be used in pets under veterinary guidance, but the dose and type differ from humans. Never give your pet human allergy medication without consulting your vet first. Veterinary-prescribed treatments are generally more effective for pet allergies than over-the-counter antihistamines."),
        ],
    },
    {
        "title": "Pet Health Supplements: What Works and What Doesn't",
        "slug": "pet-health-supplements-guide",
        "pexels_query": "pet vitamins supplements health",
        "meta_desc": "Guide to pet health supplements. Which supplements work, which are unnecessary, joint support, probiotics, omega oils, and what to ask your vet.",
        "focus": "pet health supplements guide",
        "products": [
            {"name": "YuMOVE Joint Supplement for Dogs", "asin": "B003DXIHR8", "price": "£22.99", "desc": "Veterinary-recommended joint supplement with glucosamine and green-lipped mussel"},
            {"name": "Protexin Pro-Kolin Probiotic", "asin": "B002Y1KH2C", "price": "£14.99", "desc": "Probiotic paste supporting digestive health in dogs and cats"},
            {"name": "Salmon Oil for Dogs", "asin": "B00J49OLXE", "price": "£12.99", "desc": "Pure salmon oil supplement rich in omega-3 for skin, coat, and joint health"},
        ],
        "sections": {
            "overview": "Do Pets Need Supplements?",
            "joint": "What Are the Best Joint Supplements for Pets?",
            "digestive": "Do Probiotics Work for Pets?",
            "skin_coat": "Which Supplements Support Skin and Coat Health?",
            "avoid": "What Supplements Should You Avoid for Pets?",
        },
        "faqs": [
            ("Does my pet need supplements if they eat a complete diet?", "If your pet is eating a good-quality complete pet food, they should be getting all essential nutrients without additional supplements. However, supplements may benefit pets with specific health conditions — joint supplements for arthritis, probiotics after antibiotics, or omega oils for skin issues. Always consult your vet."),
            ("Are joint supplements effective for pets?", "There is reasonable evidence that glucosamine, chondroitin, and green-lipped mussel extract can support joint health in pets. Products like YuMOVE have some veterinary backing. They work best as part of a broader joint care plan including weight management and appropriate exercise. They are not a replacement for veterinary treatment of arthritis."),
            ("Are human supplements safe for pets?", "Do not give human supplements to pets without veterinary advice. Human supplements may contain ingredients toxic to pets (such as xylitol, garlic, or excessive vitamin D), and dosages are formulated for human bodyweight. Always use pet-specific supplement products."),
            ("How long do pet supplements take to work?", "Most supplements need 4-8 weeks of consistent use before visible results. Joint supplements may take 6-8 weeks. Probiotics may show improvement within a few days to 2 weeks. Omega oils for skin and coat health typically need 4-6 weeks. Be patient and consistent with dosing."),
            ("Can supplements interact with my pet's medication?", "Yes, some supplements can interact with medications. For example, fish oil supplements can affect blood clotting and may interact with anti-inflammatory drugs. Always tell your vet about any supplements your pet is taking, especially before surgery or when starting new medications."),
        ],
    },
    {
        "title": "How to Keep Your Pet Safe in Hot Weather UK",
        "slug": "keep-pet-safe-hot-weather-uk",
        "pexels_query": "dog summer heat water",
        "meta_desc": "How to keep your pet safe in hot weather in the UK. Heat stroke signs, cooling tips, walking times, and essential summer safety advice for dogs and cats.",
        "focus": "pet safety in hot weather UK",
        "products": [
            {"name": "Pecute Dog Cooling Mat", "asin": "B07213R953", "price": "£16.99", "desc": "Self-cooling gel mat that provides relief from heat without electricity or refrigeration"},
            {"name": "Portable Dog Water Bottle", "asin": "B07QMG9VBT", "price": "£10.99", "desc": "Leak-proof travel water bottle with built-in drinking trough for dogs"},
            {"name": "Ruffwear Sun Shower Dog Coat", "asin": "B07D3Y94VL", "price": "£34.99", "desc": "Lightweight, breathable sun protection coat for dogs with UV resistance"},
        ],
        "sections": {
            "risks": "What Are the Risks of Hot Weather for Pets?",
            "heatstroke": "How to Recognise and Respond to Heatstroke in Pets",
            "walking": "When Is It Safe to Walk Your Dog in Hot Weather?",
            "cooling": "How to Keep Your Pet Cool in Summer",
            "car": "Why You Should Never Leave a Pet in a Car",
        },
        "faqs": [
            ("What temperature is too hot for dogs?", "Dogs can struggle in temperatures above 20°C, especially brachycephalic breeds (flat-faced dogs like Bulldogs, Pugs, and Shih Tzus). When air temperature reaches 25°C or above, pavement can be over 50°C — hot enough to burn paws. Walk early morning or late evening when it is cooler."),
            ("What are the signs of heatstroke in pets?", "Signs include excessive panting, drooling, bright red tongue and gums, vomiting, diarrhoea, staggering, collapse, and seizures. Heatstroke is a veterinary emergency. Move your pet to a cool area, apply cool (not cold) water to their body, offer small amounts of water, and seek immediate veterinary attention."),
            ("How do I test if pavement is too hot for my dog?", "Place the back of your hand flat on the pavement and hold it there for 7 seconds. If it is too hot for your hand, it is too hot for your dog's paws. Alternatively, walk on grass where possible. Consider using protective paw wax or booties in extreme heat."),
            ("Do cats overheat in hot weather?", "Yes, cats can overheat, although they are generally better at seeking shade and cool spots. Ensure indoor cats have access to cool, ventilated rooms. Provide multiple water sources. White-furred and light-coloured cats are also at risk of sunburn, particularly on their ears and nose."),
            ("Can I clip my dog's fur to keep them cool?", "While light trimming may help some breeds, shaving a double-coated dog (like a Husky, Golden Retriever, or German Shepherd) can actually make them hotter as their coat provides insulation and UV protection. Consult a professional groomer for breed-appropriate summer grooming advice."),
        ],
    },
    {
        "title": "Pet Mental Health: Recognising and Reducing Anxiety",
        "slug": "pet-mental-health-reducing-anxiety",
        "pexels_query": "calm relaxed dog pet",
        "meta_desc": "Guide to pet mental health. Recognise anxiety in dogs and cats, understand triggers, and learn effective strategies to reduce stress and improve wellbeing.",
        "focus": "pet mental health and anxiety reduction",
        "products": [
            {"name": "Adaptil Calm Home Diffuser Starter Kit", "asin": "B0035KSJA6", "price": "£19.99", "desc": "Clinically proven DAP diffuser releasing calming pheromones for dogs"},
            {"name": "Feliway Optimum Diffuser", "asin": "B097DYKSJV", "price": "£24.99", "desc": "Advanced feline pheromone diffuser addressing multiple signs of stress in cats"},
            {"name": "Kong Wobbler Treat Dispenser", "asin": "B003ALMW0M", "price": "£13.99", "desc": "Interactive treat dispenser providing mental stimulation to reduce boredom and anxiety"},
        ],
        "sections": {
            "what": "What Is Pet Anxiety and How Common Is It?",
            "types": "What Are the Different Types of Anxiety in Pets?",
            "signs_dogs": "How to Recognise Anxiety in Dogs",
            "signs_cats": "How to Recognise Anxiety in Cats",
            "strategies": "Effective Strategies for Reducing Pet Anxiety",
        },
        "faqs": [
            ("What causes separation anxiety in dogs?", "Separation anxiety can be triggered by changes in routine, moving house, loss of a family member or another pet, being re-homed, or lack of early socialisation. Some breeds are more prone than others. It is not a sign of disobedience — it is a genuine distress response when left alone."),
            ("Can cats have anxiety?", "Yes, cats frequently experience anxiety. Common triggers include changes in environment, new pets or people, loud noises, lack of resources (not enough litter trays, hiding spots, or vertical space), inter-cat conflict, and changes in routine. Cats often show anxiety through subtle behavioural changes."),
            ("Do calming products work for pets?", "Pheromone products (Adaptil for dogs, Feliway for cats) have scientific evidence supporting their calming effects. Calming supplements containing L-theanine or casein may also help. Pressure wraps (like ThunderShirts) work for some animals. Results vary between individual pets — what works for one may not work for another."),
            ("Should I medicate my pet for anxiety?", "Medication may be appropriate for severe anxiety that significantly affects quality of life and does not respond to behavioural modification alone. Your vet can prescribe anti-anxiety medication if needed. Medication works best alongside a behaviour modification programme — it is not a standalone solution."),
            ("How can I help my pet with noise phobia?", "Start desensitisation well before the noise season (fireworks, thunderstorms). Play recordings of the sounds at very low volume while giving treats, gradually increasing volume over weeks. Provide a safe den area. Use pheromone products. Close curtains and play background music. Talk to your vet about additional support for severe cases."),
        ],
    },
    {
        "title": "How to Care for an Ageing Pet",
        "slug": "care-for-ageing-pet",
        "pexels_query": "senior old dog grey muzzle",
        "meta_desc": "Complete guide to caring for an ageing pet. Health changes to watch for, nutrition, exercise, comfort tips, and when senior pets need vet attention.",
        "focus": "caring for ageing senior pets",
        "products": [
            {"name": "YuMOVE Senior Dog Joint Supplement", "asin": "B00C66CAIO", "price": "£26.99", "desc": "Triple-action joint supplement specifically formulated for senior dogs"},
            {"name": "Orthopaedic Memory Foam Dog Bed", "asin": "B07BQJQH48", "price": "£39.99", "desc": "Supportive memory foam bed reducing pressure on ageing joints"},
            {"name": "PetSafe Easy Walk Harness", "asin": "B0009ZBKG4", "price": "£17.99", "desc": "Front-clip harness providing gentle control for senior dogs on walks"},
        ],
        "sections": {
            "when": "When Is a Pet Considered Senior?",
            "changes": "What Health Changes Occur in Ageing Pets?",
            "nutrition": "How Should You Adjust Nutrition for a Senior Pet?",
            "exercise": "How to Adapt Exercise for an Older Pet",
            "comfort": "How to Keep Your Senior Pet Comfortable at Home",
        },
        "faqs": [
            ("At what age is a dog considered senior?", "It depends on breed and size. Small dogs (under 10kg) are considered senior from around 10-12 years. Medium dogs (10-25kg) from 8-10 years. Large dogs (25-45kg) from 7-8 years. Giant breeds (over 45kg) may be considered senior from as young as 5-6 years."),
            ("At what age is a cat considered senior?", "Cats are generally considered senior from 7-10 years of age and geriatric from 11-14 years. With good care, many cats live well into their late teens and even early twenties. Indoor cats tend to live longer than outdoor cats on average."),
            ("What health checks do senior pets need?", "Senior pets should have veterinary health checks at least twice a year. These typically include a full physical examination, blood tests (checking kidney, liver, and thyroid function), urine analysis, blood pressure measurement, and weight assessment. Early detection of age-related conditions allows for better management."),
            ("How do I know if my senior pet is in pain?", "Signs of pain in older pets can be subtle: reluctance to jump or climb stairs, stiffness after rest, reduced activity, changes in sleeping position, decreased grooming (cats), irritability, loss of appetite, or vocalising when touched. Do not assume slowing down is just normal ageing — pain can often be managed effectively."),
            ("Should I change my senior pet's food?", "Senior pets may benefit from specially formulated senior diets that are lower in calories (to prevent weight gain with reduced activity), higher in digestible protein (to maintain muscle mass), and enriched with joint-supporting nutrients. Consult your vet about the best dietary transition for your ageing pet."),
        ],
    },
    {
        "title": "Pet Health Records: What to Track and Why",
        "slug": "pet-health-records-what-to-track",
        "pexels_query": "pet health record notebook",
        "meta_desc": "Guide to keeping pet health records. What to track, why it matters, digital and paper options, and how records help your vet provide better care.",
        "focus": "keeping pet health records",
        "products": [
            {"name": "Pet Health Record Book", "asin": "B0CX56MM2T", "price": "£7.99", "desc": "Comprehensive paper health record book for tracking vaccinations, weight, and vet visits"},
            {"name": "Pet Medication Organiser", "asin": "B07Y5FWNCN", "price": "£8.99", "desc": "Weekly pill organiser for managing pet medication schedules"},
            {"name": "Digital Kitchen Scale", "asin": "B0B1HLXH3M", "price": "£11.99", "desc": "Precision scale for weighing pet food portions and monitoring intake"},
        ],
        "sections": {
            "why": "Why Are Pet Health Records Important?",
            "what": "What Should You Include in Your Pet's Health Record?",
            "how": "How to Organise Your Pet's Health Records",
            "digital": "Digital vs Paper Pet Health Records",
            "sharing": "How to Share Health Records with Your Vet",
        },
        "faqs": [
            ("What should be in my pet's health record?", "A comprehensive pet health record should include: vaccination dates and due dates, worming and flea treatment dates, weight history, any diagnosed conditions, current medications, allergy information, microchip number and database, vet contact details, emergency vet details, and notes on any behavioural changes."),
            ("Why is tracking my pet's weight important?", "Weight tracking helps identify trends early. Gradual weight gain can lead to obesity and associated health problems. Unexpected weight loss can indicate underlying illness such as diabetes, kidney disease, or cancer. Monthly weigh-ins create a clear picture of your pet's health trajectory."),
            ("Are there apps for tracking pet health?", "Yes, several apps help track pet health including PitPat, PetDesk, and 11Pets. Many UK veterinary practices also offer client portals where you can view your pet's records online. Choose a system you will actually use consistently — the best record system is one you keep updated."),
            ("How long should I keep pet health records?", "Keep your pet's health records for their entire lifetime. Vaccination records, surgery notes, and diagnostic results should be kept permanently. If you need to re-home your pet or change vets, having complete records ensures continuity of care."),
            ("What information does my vet need at each visit?", "Bring notes on any changes since the last visit: appetite changes, drinking habits, bowel movements, energy levels, new lumps or bumps, behavioural changes, and any concerns. If your pet is on medication, note whether it seems to be working and any side effects observed."),
        ],
    },
    {
        "title": "How to Recognise Emergency Health Situations in Pets",
        "slug": "recognise-emergency-health-situations-pets",
        "pexels_query": "emergency veterinary pet care",
        "meta_desc": "Learn how to recognise emergency health situations in pets. Signs that require immediate vet attention, what to do in a pet emergency, and how to prepare.",
        "focus": "recognising pet health emergencies",
        "products": [
            {"name": "Rosewood Pet First Aid Kit", "asin": "B00BSQFFNY", "price": "£14.99", "desc": "Comprehensive pet first aid kit for emergency situations at home"},
            {"name": "Pet Emergency Information Card", "asin": "B0BNLV48Y9", "price": "£5.99", "desc": "Wallet-sized emergency card with space for vet details and pet medical information"},
            {"name": "Wahl Pet Thermometer", "asin": "B07RM6MXFG", "price": "£9.99", "desc": "Digital thermometer for quickly checking your pet's temperature in emergencies"},
        ],
        "sections": {
            "signs": "What Are the Signs of a Pet Health Emergency?",
            "breathing": "Breathing Emergencies: What to Do",
            "poisoning": "What to Do If Your Pet Is Poisoned",
            "injury": "How to Handle Injuries and Trauma in Pets",
            "prepare": "How to Prepare for a Pet Emergency",
        },
        "faqs": [
            ("What constitutes a pet emergency?", "Veterinary emergencies include: difficulty breathing, collapse or inability to stand, seizures, suspected poisoning, heavy bleeding that does not stop, bloated abdomen (especially in large dogs), inability to urinate, severe vomiting or diarrhoea (especially with blood), eye injuries, and suspected broken bones."),
            ("What should I do if my pet is poisoned?", "Contact your vet or the Animal PoisonLine (01202 509000) immediately. Note what your pet ate, how much, and when. Do not try to make your pet vomit unless specifically instructed by a vet. Bring any packaging or a sample of the substance to the vet. Common pet poisons include chocolate, grapes, xylitol, lilies (cats), and rat poison."),
            ("How do I find an emergency vet?", "Your regular vet should have an out-of-hours emergency number on their answerphone. Many areas have dedicated emergency veterinary clinics. Save the number of your nearest emergency vet in your phone before you need it. The RCVS Find a Vet tool on their website can help locate practices near you."),
            ("What first aid can I give my pet in an emergency?", "Keep calm. For bleeding, apply firm pressure with a clean cloth. For choking, check the mouth for visible obstructions (be careful of being bitten). For burns, run cool water over the area for 10 minutes. For seizures, do not restrain your pet — move dangerous objects away and time the seizure. Always seek veterinary help promptly."),
            ("Should I learn pet CPR?", "Learning pet CPR is valuable for any pet owner. The British Veterinary Association and organisations like the PDSA provide guides on pet CPR. The basic technique involves 30 chest compressions followed by 2 rescue breaths. However, CPR should only be performed if the pet has stopped breathing and has no heartbeat. Always get to a vet as quickly as possible."),
        ],
    },
    {
        "title": "Pet Digestive Health: Common Issues and Prevention",
        "slug": "pet-digestive-health-common-issues",
        "pexels_query": "dog eating food bowl healthy",
        "meta_desc": "Guide to pet digestive health. Common digestive issues in dogs and cats, prevention strategies, diet tips, and when digestive problems need vet attention.",
        "focus": "pet digestive health issues and prevention",
        "products": [
            {"name": "Protexin Pro-Kolin Advanced", "asin": "B002Y1KH2C", "price": "£14.99", "desc": "Probiotic paste supporting digestive health and recovery in dogs and cats"},
            {"name": "Royal Canin Gastrointestinal Dog Food", "asin": "B004H813T0", "price": "£21.99", "desc": "Veterinary digestive support diet with highly digestible proteins"},
            {"name": "Slow Feeder Dog Bowl", "asin": "B00FPKNR8K", "price": "£9.99", "desc": "Anti-gulp maze bowl reducing eating speed and improving digestion"},
        ],
        "sections": {
            "common": "What Are the Most Common Digestive Issues in Pets?",
            "causes": "What Causes Digestive Problems in Pets?",
            "diet": "How Does Diet Affect Pet Digestive Health?",
            "prebiotics": "Do Probiotics and Prebiotics Help Pet Digestion?",
            "vet": "When Do Digestive Issues Require Veterinary Attention?",
        },
        "faqs": [
            ("Why does my dog have diarrhoea?", "Common causes of diarrhoea in dogs include dietary indiscretion (eating something they should not have), sudden food changes, stress, infections, parasites, food intolerances, and underlying health conditions. Mild, brief diarrhoea may resolve on its own, but persistent or severe diarrhoea needs veterinary attention."),
            ("Why is my cat vomiting?", "Occasional vomiting in cats can be caused by hairballs, eating too quickly, or mild stomach upset. However, frequent vomiting is not normal and can indicate conditions such as inflammatory bowel disease, kidney disease, hyperthyroidism, or intestinal obstruction. Consult your vet if vomiting occurs more than once or twice a month."),
            ("How should I change my pet's food?", "Always transition to new food gradually over 7-10 days. Start with 25% new food mixed with 75% old food, then move to 50/50, then 75/25, before switching fully. Sudden food changes are one of the most common causes of digestive upset in pets."),
            ("Are probiotics beneficial for pets?", "Probiotics can be beneficial for pets, particularly after antibiotic treatment, during stress, or for those with chronic digestive issues. Pet-specific probiotics like Protexin Pro-Kolin contain strains suitable for pets. They can help restore healthy gut bacteria balance and support immune function."),
            ("What foods are toxic to pets' digestive systems?", "Dangerous foods include chocolate, grapes and raisins, onions and garlic, xylitol (artificial sweetener), macadamia nuts, cooked bones (can splinter), avocado, alcohol, and caffeine. Lilies are extremely toxic to cats. Keep all toxic foods well out of reach and educate all family members."),
        ],
    },
    {
        "title": "How to Keep Your Pet's Coat Healthy and Shiny",
        "slug": "keep-pets-coat-healthy-shiny",
        "pexels_query": "dog grooming brushing coat",
        "meta_desc": "How to keep your pet's coat healthy and shiny. Grooming tips, nutrition advice, common coat problems, and the best products for dogs and cats.",
        "focus": "healthy shiny pet coat care",
        "products": [
            {"name": "FURminator Deshedding Tool", "asin": "B0040QS3PO", "price": "£24.99", "desc": "Professional deshedding tool removing loose undercoat without damaging topcoat"},
            {"name": "Salmon Oil for Pets", "asin": "B00J49OLXE", "price": "£12.99", "desc": "Pure salmon oil rich in omega-3 and omega-6 for healthy skin and shiny coat"},
            {"name": "Wahl Dog Shampoo Oatmeal Formula", "asin": "B0002DHXX2", "price": "£8.49", "desc": "Gentle oatmeal shampoo for sensitive skin, promoting a clean and shiny coat"},
        ],
        "sections": {
            "grooming": "How Often Should You Groom Your Pet?",
            "nutrition": "How Does Nutrition Affect Your Pet's Coat?",
            "problems": "Common Coat Problems and What They Mean",
            "bathing": "How to Bathe Your Pet Properly",
            "seasonal": "How Does Your Pet's Coat Change with the Seasons?",
        },
        "faqs": [
            ("How often should I brush my dog?", "Brushing frequency depends on coat type. Long-haired breeds need daily brushing to prevent matting. Medium-coated dogs benefit from brushing 2-3 times per week. Short-haired breeds need weekly brushing. Regular brushing removes loose hair, distributes natural oils, and helps you spot skin problems early."),
            ("How often should I brush my cat?", "Short-haired cats generally need brushing once a week. Long-haired breeds like Persians need daily grooming to prevent mats and reduce hairballs. Most cats enjoy being brushed once they are accustomed to it. Start with short sessions and use treats for positive association."),
            ("Why is my pet's coat dull?", "A dull coat can indicate nutritional deficiencies (particularly omega fatty acids), dehydration, parasites (fleas or mites), skin conditions, hormonal imbalances (hypothyroidism), stress, or underlying illness. If diet and grooming are adequate but the coat remains dull, consult your vet for a health check."),
            ("Can diet improve my pet's coat?", "Yes, diet significantly affects coat quality. Foods rich in omega-3 and omega-6 fatty acids promote a healthy, shiny coat. High-quality protein supports hair growth. Supplements like salmon oil can improve coat condition within 4-6 weeks. Ensure your pet is eating a nutritionally complete diet appropriate for their life stage."),
            ("How often should I bathe my dog?", "Most dogs need bathing every 4-8 weeks, though this varies by breed, coat type, and lifestyle. Over-bathing strips natural oils and can cause dry, itchy skin. Use a dog-specific shampoo — human shampoo has the wrong pH for dogs. Some breeds with oily coats may need more frequent bathing."),
        ],
    },
    {
        "title": "Pet Joint Health: Prevention and Support for Mobility",
        "slug": "pet-joint-health-prevention-mobility",
        "pexels_query": "dog running exercise joint health",
        "meta_desc": "Guide to pet joint health. Prevention tips, exercise advice, supplements, weight management, and support for dogs and cats with mobility issues.",
        "focus": "pet joint health and mobility support",
        "products": [
            {"name": "YuMOVE Joint Supplement for Dogs", "asin": "B003DXIHR8", "price": "£22.99", "desc": "Triple-action joint supplement with glucosamine, chondroitin, and green-lipped mussel"},
            {"name": "Dog Ramp for Car and Sofa", "asin": "B0002AT37Y", "price": "£29.99", "desc": "Lightweight folding ramp reducing joint strain when getting in and out of cars"},
            {"name": "Heated Pet Pad", "asin": "B00008AJH2", "price": "£16.99", "desc": "Microwave heat pad providing soothing warmth for stiff joints"},
        ],
        "sections": {
            "anatomy": "How Do Pet Joints Work?",
            "risks": "What Puts Pets at Risk of Joint Problems?",
            "signs": "How to Recognise Joint Problems in Pets",
            "prevention": "How to Protect Your Pet's Joint Health",
            "management": "Managing Joint Conditions in Pets",
        },
        "faqs": [
            ("What causes joint problems in pets?", "Common causes include osteoarthritis (age-related wear), hip or elbow dysplasia (genetic, common in larger breeds), previous injuries, obesity (excess weight stresses joints), cruciate ligament disease, and inflammatory joint conditions. Some breeds are genetically predisposed to joint problems."),
            ("How do I know if my pet has joint pain?", "Signs include: stiffness after rest (especially in the morning), reluctance to jump, climb stairs, or get into the car, limping or lameness, slowing down on walks, difficulty getting up or lying down, licking or chewing at joints, and changes in posture or gait. Cats may stop jumping to high surfaces."),
            ("Do joint supplements work for pets?", "Joint supplements containing glucosamine, chondroitin, and omega-3 fatty acids have shown positive results in many pets. Green-lipped mussel extract has evidence supporting its anti-inflammatory properties. Supplements work best for prevention and mild-to-moderate joint issues. Severe arthritis may require veterinary pain management alongside supplements."),
            ("How does weight affect my pet's joints?", "Excess weight significantly increases stress on joints. Research shows that maintaining an ideal weight can add years to a dog's life and delay the onset of osteoarthritis. Losing even 5-10% of excess body weight can noticeably improve mobility in overweight pets with joint issues."),
            ("What exercise is best for pets with joint problems?", "Low-impact exercise is ideal: short, regular walks rather than long sessions; swimming or hydrotherapy (excellent for joints); gentle play on soft surfaces. Avoid high-impact activities like jumping, running on hard surfaces, or rough play. Little and often is better than occasional intense exercise."),
        ],
    },
    {
        "title": "How to Help Your Pet Maintain a Healthy Weight",
        "slug": "help-pet-maintain-healthy-weight",
        "pexels_query": "dog exercise walking healthy",
        "meta_desc": "How to help your pet maintain a healthy weight. Diet tips, portion control, exercise plans, and weight management strategies for dogs and cats.",
        "focus": "helping pets maintain healthy weight",
        "products": [
            {"name": "Slow Feeder Dog Bowl", "asin": "B00FPKNR8K", "price": "£9.99", "desc": "Maze-design bowl that slows eating and improves portion awareness"},
            {"name": "Catit Senses Food Tree", "asin": "B00D3NI2PG", "price": "£8.99", "desc": "Interactive food puzzle encouraging active feeding and mental stimulation"},
            {"name": "Digital Kitchen Scale", "asin": "B0B1HLXH3M", "price": "£11.99", "desc": "Precision scale for accurately measuring pet food portions"},
        ],
        "sections": {
            "why": "Why Is a Healthy Weight Important for Pets?",
            "assess": "How to Assess Whether Your Pet Is a Healthy Weight",
            "diet": "How to Adjust Your Pet's Diet for Weight Management",
            "exercise": "Exercise Strategies for Weight Management in Pets",
            "treats": "How to Handle Treats Without Causing Weight Gain",
        },
        "faqs": [
            ("How do I know if my pet is overweight?", "Feel along your pet's ribcage — you should be able to feel the ribs without pressing hard, with only a thin layer of fat covering them. View your pet from above — there should be a visible waist behind the ribs. From the side, the abdomen should tuck up. If ribs are hard to feel or there is no visible waist, your pet may be overweight."),
            ("How much should I feed my pet to lose weight?", "Weight loss should be gradual — 1-2% of body weight per week for dogs, 0.5-1% for cats. Your vet can calculate the correct calorie intake. As a starting point, reducing current food by 10-20% while increasing exercise often helps. Never crash diet a cat — rapid weight loss can cause dangerous hepatic lipidosis (fatty liver disease)."),
            ("Are diet pet foods effective?", "Veterinary weight management diets are formulated to reduce calories while maintaining essential nutrients and keeping pets feeling full. They are more effective than simply feeding less of a regular food, which can cause nutritional imbalances. Your vet can recommend the most appropriate option for your pet."),
            ("How much exercise does my pet need for weight management?", "Dogs generally need 30-120 minutes of exercise daily, depending on breed and age. Start slowly if your pet is unfit and gradually increase. Cats need 15-30 minutes of active play daily. Interactive toys, puzzle feeders, and play sessions all count. Consistency is more important than intensity."),
            ("Do treats cause weight gain in pets?", "Treats can be a significant source of excess calories. A single dental chew can contain 100+ calories. Treats should make up no more than 10% of your pet's daily calorie intake. Use small, low-calorie treats for training, and deduct treat calories from their main meal allowance."),
        ],
    },
    {
        "title": "Pet Eye Health: Common Issues and When to Seek Help",
        "slug": "pet-eye-health-common-issues",
        "pexels_query": "dog eyes close up healthy",
        "meta_desc": "Guide to pet eye health. Common eye problems in dogs and cats, symptoms to watch for, home care tips, and when eye issues need veterinary attention.",
        "focus": "pet eye health problems and care",
        "products": [
            {"name": "Burt's Bees Eye Wash for Dogs", "asin": "B01BKL00R2", "price": "£7.99", "desc": "Gentle saline eye wash solution for cleaning and soothing dog eyes"},
            {"name": "Petpost Tear Stain Remover", "asin": "B015OUS5N0", "price": "£12.99", "desc": "Natural coconut oil-based solution for removing tear stains around pet eyes"},
            {"name": "Elizabethan E-Collar", "asin": "B00B3M9PRI", "price": "£8.49", "desc": "Protective cone collar preventing pets from rubbing or scratching at eye injuries"},
        ],
        "sections": {
            "common": "What Are the Most Common Eye Problems in Pets?",
            "signs": "What Signs Indicate an Eye Problem in Your Pet?",
            "care": "How to Care for Your Pet's Eyes at Home",
            "breeds": "Which Breeds Are Prone to Eye Problems?",
            "emergency": "When Is an Eye Problem a Veterinary Emergency?",
        },
        "faqs": [
            ("What are common eye problems in dogs?", "Common dog eye problems include conjunctivitis (pink eye), dry eye (keratoconjunctivitis sicca), corneal ulcers, cherry eye (prolapsed third eyelid gland), cataracts, glaucoma, and entropion (inward-rolling eyelids). Breeds with prominent eyes (Pugs, Shih Tzus, Cavalier King Charles Spaniels) are more prone to eye issues."),
            ("What are common eye problems in cats?", "Common cat eye problems include conjunctivitis (often linked to cat flu), corneal ulcers, uveitis (inflammation inside the eye), glaucoma, and cataracts. Cat flu viruses (feline herpesvirus, calicivirus) are common causes of eye problems in cats, particularly in kittens and rescue cats."),
            ("How do I clean my pet's eyes?", "Gently wipe around the eyes with a clean, damp cotton pad, using a fresh pad for each eye. Wipe from the inner corner outward. Use plain sterile saline or a pet-specific eye wash. Do not use tea bags, human eye drops, or cotton buds near the eye. If there is heavy discharge, consult your vet."),
            ("When should I take my pet to the vet for eye problems?", "See a vet promptly if you notice: squinting or keeping the eye closed, excessive discharge (especially yellow or green), cloudiness or change in eye colour, swelling around the eye, visible injury to the eye, sudden blindness or bumping into things, or if your pet is pawing at their eye. Eye conditions can deteriorate rapidly."),
            ("Can pets go blind?", "Yes, pets can lose their sight due to cataracts, glaucoma, retinal detachment, progressive retinal atrophy, diabetes, or injury. Many pets adapt remarkably well to blindness, using their other senses to navigate. Keep furniture in the same position, use verbal cues, and consider a halo harness for blind pets to prevent bumping into objects."),
        ],
    },
    {
        "title": "How to Choose the Right Vet for Your Pet UK",
        "slug": "choose-right-vet-for-pet-uk",
        "pexels_query": "veterinary clinic pet consultation",
        "meta_desc": "How to choose the right vet for your pet in the UK. What to look for, questions to ask, fees, and tips for finding the best veterinary practice.",
        "focus": "choosing the right vet UK",
        "products": [
            {"name": "Pet Health Record Book", "asin": "B0CX56MM2T", "price": "£7.99", "desc": "Health record book to keep track of all vet visits and treatments"},
            {"name": "Pet Carrier", "asin": "B071KPSGL5", "price": "£24.99", "desc": "Comfortable pet carrier for safe transport to veterinary appointments"},
            {"name": "Adaptil Calm Spray", "asin": "B0035KSJA6", "price": "£12.49", "desc": "Calming pheromone spray for stress-free vet visits"},
        ],
        "sections": {
            "factors": "What Factors Should You Consider When Choosing a Vet?",
            "questions": "What Questions Should You Ask a New Vet?",
            "types": "What Types of Veterinary Practices Are Available in the UK?",
            "costs": "How Much Do Vet Fees Cost in the UK?",
            "switching": "How to Switch Vets and Transfer Records",
        },
        "faqs": [
            ("How do I find a good vet near me?", "Check the RCVS (Royal College of Veterinary Surgeons) Find a Vet tool to confirm a practice is registered. Ask for recommendations from friends, family, and local pet groups. Visit the practice before registering — check cleanliness, staff friendliness, and facilities. Read online reviews, but consider them alongside personal visits."),
            ("What should I look for in a veterinary practice?", "Look for RCVS registration, convenient location and opening hours (including emergency provision), clean and well-equipped facilities, friendly and approachable staff, clear communication about treatments and costs, a range of services, and whether they offer payment plans or health plans."),
            ("How much does a vet consultation cost in the UK?", "Standard consultations typically cost £30-£60, with specialist or out-of-hours consultations costing more. Fees vary significantly by region (London practices are generally more expensive) and practice type. Many practices offer health plans (monthly subscription covering vaccinations, flea/worm treatment, and consultations) which can save money."),
            ("Should I choose a specialist vet for my pet?", "General practice vets handle most conditions effectively. However, for complex or rare conditions, a referral to a specialist (such as a cardiologist, oncologist, or orthopaedic surgeon) may be recommended. RCVS-recognised specialists have additional qualifications and expertise in specific areas."),
            ("Can I get a second opinion from another vet?", "Yes, you have every right to seek a second opinion. A good vet will not be offended. You can ask your vet for a referral, or register with another practice independently. Bring copies of your pet's records, test results, and imaging to the new vet for a thorough assessment."),
        ],
    },
    {
        "title": "Pet Seasonal Health Risks: Spring, Summer, Autumn, Winter",
        "slug": "pet-seasonal-health-risks-uk",
        "pexels_query": "dog four seasons outdoors",
        "meta_desc": "Seasonal health risks for pets in the UK. Spring, summer, autumn, and winter dangers, prevention tips, and how to keep your pet safe all year round.",
        "focus": "seasonal pet health risks UK",
        "products": [
            {"name": "Pecute Dog Cooling Mat", "asin": "B07213R953", "price": "£16.99", "desc": "Self-cooling mat for summer heat relief"},
            {"name": "Ancol Muddy Paws Dog Coat", "asin": "B004CNEFSS", "price": "£19.99", "desc": "Waterproof, fleece-lined coat for autumn and winter walks"},
            {"name": "O'Tom Tick Twister", "asin": "B0002YHFQI", "price": "£3.99", "desc": "Safe tick removal tool essential for spring and summer outdoor activities"},
        ],
        "sections": {
            "spring": "What Pet Health Risks Come with Spring?",
            "summer": "What Pet Health Risks Come with Summer?",
            "autumn": "What Pet Health Risks Come with Autumn?",
            "winter": "What Pet Health Risks Come with Winter?",
            "year_round": "Year-Round Pet Health Precautions",
        },
        "faqs": [
            ("What are the main pet health risks in spring?", "Spring risks include increased tick activity, adder bites (UK's only venomous snake becomes active), spring bulb poisoning (daffodils, tulips, bluebells are toxic), increased pollen triggering allergies, and slug/snail activity increasing lungworm risk in dogs. Ensure parasite prevention is up to date."),
            ("What are the main pet health risks in summer?", "Summer risks include heatstroke, sunburn (especially light-coloured pets), hot pavement burns, algae poisoning in lakes and ponds (blue-green algae is toxic), grass seeds lodging in ears and paws, adder bites, barbecue hazards (skewers, toxic foods), and increased flea and tick exposure."),
            ("What are the main pet health risks in autumn?", "Autumn risks include conker and acorn poisoning, mushroom toxicity (wild mushrooms), antifreeze poisoning (as people prepare cars for winter), firework phobia (Bonfire Night, Diwali), dark evenings reducing visibility on walks (use reflective gear), and fallen fruit fermenting in gardens."),
            ("What are the main pet health risks in winter?", "Winter risks include antifreeze poisoning (highly toxic, sweet-tasting), rock salt irritation on paws, hypothermia in very cold weather, frozen ponds (risk of falling through), reduced exercise leading to weight gain, and dry indoor air affecting skin and coat. Senior and small pets are more vulnerable to cold."),
            ("How can I keep my pet safe during fireworks season?", "Close curtains, play background music or TV, create a safe den, use pheromone products (Adaptil/Feliway), walk dogs before dark, keep cats indoors, never take pets to fireworks displays, and consider a ThunderShirt. For severe phobia, speak to your vet about medication well in advance — not on the night itself."),
        ],
    },
    {
        "title": "How to Support Your Pet Through Recovery After Surgery",
        "slug": "support-pet-recovery-after-surgery",
        "pexels_query": "dog recovery cone veterinary",
        "meta_desc": "How to support your pet through recovery after surgery. Post-operative care, pain management, activity restriction, and signs of complications to watch for.",
        "focus": "pet post-surgery recovery care",
        "products": [
            {"name": "BENCMATE Protective Inflatable Collar", "asin": "B073XBBT5Y", "price": "£14.99", "desc": "Comfortable alternative to traditional cones, allowing eating and drinking while protecting surgical sites"},
            {"name": "Snuggle Safe Heat Pad", "asin": "B00008AJH2", "price": "£16.99", "desc": "Microwave heat pad providing comforting warmth during post-surgery recovery"},
            {"name": "Vetbed Original Fleece", "asin": "B0019R76B0", "price": "£22.99", "desc": "Veterinary bedding that stays dry and warm, ideal for post-surgical recovery"},
        ],
        "sections": {
            "prep": "How to Prepare for Your Pet's Surgery",
            "home": "Bringing Your Pet Home After Surgery",
            "wound": "How to Care for Your Pet's Surgical Wound",
            "pain": "How to Manage Pain After Pet Surgery",
            "complications": "Signs of Post-Surgery Complications to Watch For",
        },
        "faqs": [
            ("How long does it take for a pet to recover from surgery?", "Recovery time varies by procedure. Minor surgeries like neutering typically need 10-14 days for wound healing. Orthopaedic surgeries may require 6-12 weeks of restricted activity. Your vet will provide a specific recovery timeline and schedule follow-up appointments."),
            ("How do I stop my pet from licking their surgical wound?", "Use an Elizabethan collar (cone), inflatable collar, or surgical recovery suit. These prevent your pet from reaching and licking the wound, which can cause infection and delayed healing. Keep the protective device on at all times unless directly supervised."),
            ("What should I feed my pet after surgery?", "Offer a small amount of your pet's normal food a few hours after returning home. Some pets may be nauseous from anaesthesia — offer half their normal portion initially. If they refuse food for more than 24 hours after surgery, contact your vet. Ensure fresh water is readily accessible."),
            ("How much exercise can my pet have after surgery?", "Most post-surgical pets need strict rest for the initial recovery period. Dogs should only go outside for brief toilet breaks on a lead. Cats should be kept indoors, ideally in a single room. No running, jumping, or playing until your vet clears increased activity. Crate rest may be recommended for some procedures."),
            ("When should I be concerned about my pet's recovery?", "Contact your vet if you notice: wound opening or discharge, excessive swelling or redness around the incision, bleeding, your pet refusing to eat or drink for more than 24 hours, lethargy beyond the first 24-48 hours, vomiting, difficulty breathing, or if your pet seems to be in worsening pain despite medication."),
        ],
    },
    {
        "title": "Pet Health Myths Debunked: Common Misconceptions",
        "slug": "pet-health-myths-debunked",
        "pexels_query": "happy healthy dog and cat together",
        "meta_desc": "Common pet health myths debunked with facts. Separate fact from fiction on dog and cat health, nutrition, behaviour, and care misconceptions.",
        "focus": "debunking common pet health myths",
        "products": [
            {"name": "Pet Nutrition Book", "asin": "B07FKWRKXZ", "price": "£12.99", "desc": "Evidence-based guide to pet nutrition cutting through marketing myths"},
            {"name": "Digital Pet Thermometer", "asin": "B07RM6MXFG", "price": "£9.99", "desc": "Accurate digital thermometer — because a warm nose does not mean your pet has a fever"},
            {"name": "Pet First Aid Manual", "asin": "B01MYXWCW0", "price": "£10.99", "desc": "Comprehensive first aid guide with factual, evidence-based pet health information"},
        ],
        "sections": {
            "nose_myths": "Is a Warm Nose Really a Sign of Illness?",
            "food_myths": "Common Pet Food and Nutrition Myths",
            "behaviour_myths": "Pet Behaviour Myths That Need Correcting",
            "health_myths": "Dangerous Health Myths About Pets",
            "facts": "Evidence-Based Pet Health Facts Every Owner Should Know",
        },
        "faqs": [
            ("Does a warm nose mean my pet is ill?", "No, this is one of the most persistent pet myths. A pet's nose temperature fluctuates naturally throughout the day and can be warm or cool regardless of health status. A more reliable health indicator is your pet's overall behaviour, appetite, energy levels, and actual body temperature taken with a thermometer."),
            ("Do dogs eat grass because they are ill?", "Not necessarily. While some dogs eat grass when they have an upset stomach, many healthy dogs eat grass regularly. It may be due to instinct, boredom, taste preference, or dietary fibre needs. Occasional grass eating is generally harmless, but frequent grass eating followed by vomiting warrants a vet check."),
            ("Is it true that one dog year equals seven human years?", "This is an oversimplification. Dogs age more rapidly in their first two years — a 1-year-old dog is roughly equivalent to a 15-year-old human, and a 2-year-old dog is about 24 in human years. After that, each dog year adds approximately 4-5 human years, varying by breed size. Large breeds age faster than small breeds."),
            ("Can cats always land on their feet?", "While cats have a remarkable righting reflex that allows them to twist mid-air, they cannot always land safely. Falls from very low heights may not give enough time to right themselves, and falls from great heights (high-rise syndrome) can cause serious injuries or death. Keep windows secured with cat-safe netting."),
            ("Is garlic a natural flea remedy for pets?", "No, garlic is toxic to both dogs and cats and should never be given as a flea remedy. Garlic and onions contain thiosulphates that damage red blood cells, potentially causing anaemia. This myth is dangerous and persists online despite clear veterinary evidence against it. Use proven, vet-recommended flea treatments instead."),
        ],
    },
    {
        "title": "How to Create a Wellness Routine for Your Pet",
        "slug": "create-wellness-routine-for-pet",
        "pexels_query": "happy pet daily routine walking",
        "meta_desc": "How to create a wellness routine for your pet. Daily, weekly, and monthly health checks, exercise plans, grooming schedules, and preventive care tips.",
        "focus": "creating a pet wellness routine",
        "products": [
            {"name": "Pet Health Journal", "asin": "B0CX56MM2T", "price": "£7.99", "desc": "Health tracking journal for recording daily observations and wellness checks"},
            {"name": "Kong Classic Treat Toy", "asin": "B0002AR0I8", "price": "£7.49", "desc": "Durable enrichment toy supporting mental wellness and reducing boredom"},
            {"name": "FURminator Grooming Tool", "asin": "B0040QS3PO", "price": "£24.99", "desc": "Professional grooming tool for regular coat maintenance as part of a wellness routine"},
        ],
        "sections": {
            "daily": "What Should a Daily Pet Wellness Routine Include?",
            "weekly": "What Weekly Health Checks Should You Do?",
            "monthly": "What Monthly Wellness Tasks Are Important?",
            "seasonal": "Seasonal Wellness Adjustments for Your Pet",
            "annual": "Annual Veterinary Wellness Checks",
        },
        "faqs": [
            ("What should I check daily on my pet?", "Daily checks should include: observing appetite and water intake, checking energy levels and behaviour, looking at eyes and ears for discharge, monitoring toilet habits (frequency, consistency, colour), and checking for any limping or discomfort. These quick observations help you notice changes early."),
            ("How do I create a grooming schedule?", "Base your grooming schedule on your pet's breed and coat type. Short-haired pets may only need weekly brushing, while long-haired breeds need daily attention. Include regular nail trimming (every 4-6 weeks), ear cleaning (as needed), dental care (daily toothbrushing ideally), and bathing (every 4-8 weeks for dogs)."),
            ("How important is routine for pets?", "Routine is very important for most pets. Consistent feeding times, walk schedules, play sessions, and bedtimes provide security and reduce anxiety. Disruptions to routine can cause stress, especially in cats and anxious dogs. When changes are unavoidable, introduce them gradually."),
            ("What preventive care does my pet need annually?", "Annual preventive care should include: veterinary health check (twice yearly for seniors), vaccination boosters as recommended by your vet, regular parasite prevention (flea, tick, worm treatments), dental check-up, weight assessment, and any breed-specific screenings recommended by your vet."),
            ("How much exercise does my pet need?", "Exercise needs vary widely. Most dogs need 30 minutes to 2 hours daily, depending on breed, age, and health. Working breeds need more. Cats need 15-30 minutes of interactive play daily. Senior pets need regular but gentler exercise. Puppies and kittens need frequent short bursts rather than prolonged sessions."),
        ],
    },
    {
        "title": "Pet Health Warning Signs Every Owner Should Know",
        "slug": "pet-health-warning-signs-every-owner",
        "pexels_query": "concerned pet owner dog health",
        "meta_desc": "Essential pet health warning signs every owner should know. Recognise when your dog or cat needs veterinary attention with this comprehensive guide.",
        "focus": "pet health warning signs for owners",
        "products": [
            {"name": "Pet First Aid Kit", "asin": "B00BSQFFNY", "price": "£14.99", "desc": "Comprehensive first aid kit for immediate response to pet health emergencies"},
            {"name": "Digital Pet Thermometer", "asin": "B07RM6MXFG", "price": "£9.99", "desc": "Quick-reading digital thermometer for checking your pet's temperature at home"},
            {"name": "Pet Health Record Book", "asin": "B0CX56MM2T", "price": "£7.99", "desc": "Record book for tracking symptoms, changes, and health observations"},
        ],
        "sections": {
            "urgent": "What Warning Signs Require Immediate Vet Attention?",
            "behavioural": "Behavioural Changes That May Indicate Illness",
            "physical": "Physical Warning Signs to Watch For",
            "eating": "Changes in Eating and Drinking Habits",
            "chronic": "Subtle Signs of Chronic Health Conditions",
        },
        "faqs": [
            ("What are the most urgent pet health warning signs?", "Seek immediate veterinary attention for: difficulty breathing, collapse or inability to stand, seizures, heavy bleeding, suspected poisoning, bloated abdomen, inability to urinate, pale or blue gums, and sudden blindness. These are life-threatening emergencies where every minute counts."),
            ("When should I be concerned about my pet's vomiting?", "Occasional vomiting may not be serious, but contact your vet if: vomiting persists for more than 24 hours, there is blood in the vomit, your pet is also lethargic or has diarrhoea, they cannot keep water down, vomiting is projectile, or if you suspect they have swallowed something they should not have."),
            ("What changes in behaviour could indicate illness?", "Watch for: hiding or withdrawing (especially in cats), unusual aggression or irritability, excessive sleeping beyond normal, restlessness or pacing, loss of interest in activities they normally enjoy, changes in vocalisation, and house-soiling in a normally clean pet. Any significant behaviour change warrants attention."),
            ("Is it normal for my pet to drink more water?", "A noticeable increase in water consumption (polydipsia) can indicate conditions such as diabetes, kidney disease, liver disease, Cushing's disease, or a urinary tract infection. If you notice your pet drinking significantly more than usual, consult your vet — it is one of the most important warning signs to act on."),
            ("How do I know if my pet is in pain?", "Pets often hide pain. Signs include: reluctance to move or be touched, whimpering or crying, panting at rest, changes in posture or gait, reduced appetite, aggression when approached, excessive licking of a specific area, trembling, and restlessness. Cats may purr when in pain (self-soothing), which can be misleading."),
        ],
    },
]

# ── Internal Links (cross-reference between posts) ─────────────────────────
# Map slugs to titles for internal linking
INTERNAL_LINKS_MAP = {
    "pet-first-aid-kit-at-home": "How to Create a Pet First Aid Kit at Home",
    "pet-worming-schedules-uk": "Complete Guide to Pet Worming Schedules UK",
    "check-pets-vital-signs-at-home": "How to Check Your Pet's Vital Signs at Home",
    "pet-flea-prevention-year-round-uk": "Pet Flea Prevention: Year-Round Protection Guide UK",
    "signs-of-dehydration-in-pets": "How to Recognise Signs of Dehydration in Pets",
    "pet-vaccination-faqs-uk": "Pet Vaccination FAQs: What UK Pet Owners Need to Know",
    "monitor-pets-weight-at-home": "How to Monitor Your Pet's Weight at Home",
    "pet-dental-health-preventing-gum-disease": "Pet Dental Health: Preventing Gum Disease and Tooth Decay",
    "signs-of-stress-in-pets": "How to Spot Signs of Stress in Your Pet",
    "pet-microchipping-guide-uk": "Pet Microchipping Guide UK: Legal Requirements and Benefits",
    "prepare-pet-for-vet-visit": "How to Prepare Your Pet for a Vet Visit",
    "pet-nutrition-understanding-food-labels-uk": "Pet Nutrition Basics: Understanding Pet Food Labels UK",
    "help-pet-recover-from-illness": "How to Help Your Pet Recover from Illness",
    "pet-parasite-prevention-fleas-ticks-worms": "Pet Parasite Prevention: Fleas, Ticks, and Worms Guide",
    "recognise-allergies-in-pets": "How to Recognise Allergies in Pets",
    "pet-health-supplements-guide": "Pet Health Supplements: What Works and What Doesn't",
    "keep-pet-safe-hot-weather-uk": "How to Keep Your Pet Safe in Hot Weather UK",
    "pet-mental-health-reducing-anxiety": "Pet Mental Health: Recognising and Reducing Anxiety",
    "care-for-ageing-pet": "How to Care for an Ageing Pet",
    "pet-health-records-what-to-track": "Pet Health Records: What to Track and Why",
    "recognise-emergency-health-situations-pets": "How to Recognise Emergency Health Situations in Pets",
    "pet-digestive-health-common-issues": "Pet Digestive Health: Common Issues and Prevention",
    "keep-pets-coat-healthy-shiny": "How to Keep Your Pet's Coat Healthy and Shiny",
    "pet-joint-health-prevention-mobility": "Pet Joint Health: Prevention and Support for Mobility",
    "help-pet-maintain-healthy-weight": "How to Help Your Pet Maintain a Healthy Weight",
    "pet-eye-health-common-issues": "Pet Eye Health: Common Issues and When to Seek Help",
    "choose-right-vet-for-pet-uk": "How to Choose the Right Vet for Your Pet UK",
    "pet-seasonal-health-risks-uk": "Pet Seasonal Health Risks: Spring, Summer, Autumn, Winter",
    "support-pet-recovery-after-surgery": "How to Support Your Pet Through Recovery After Surgery",
    "pet-health-myths-debunked": "Pet Health Myths Debunked: Common Misconceptions",
    "create-wellness-routine-for-pet": "How to Create a Wellness Routine for Your Pet",
    "pet-health-warning-signs-every-owner": "Pet Health Warning Signs Every Owner Should Know",
}

# Internal link groups - which posts link to which (2-3 links each)
INTERNAL_LINK_GROUPS = {
    0: [2, 20, 28],  # First Aid -> Vital Signs, Emergency, Surgery Recovery
    1: [13, 3, 26],   # Worming -> Parasite Prevention, Flea Prevention, Choose Vet
    2: [0, 19, 31],   # Vital Signs -> First Aid, Health Records, Warning Signs
    3: [1, 13, 27],   # Flea Prevention -> Worming, Parasite Prevention, Seasonal
    4: [2, 16, 31],   # Dehydration -> Vital Signs, Hot Weather, Warning Signs
    5: [10, 9, 19],   # Vaccination -> Vet Visit, Microchipping, Health Records
    6: [24, 11, 18],  # Weight Monitor -> Healthy Weight, Nutrition, Ageing
    7: [30, 22, 15],  # Dental Health -> Wellness Routine, Coat, Supplements
    8: [17, 10, 30],  # Stress -> Mental Health, Vet Visit, Wellness Routine
    9: [5, 19, 26],   # Microchipping -> Vaccination, Health Records, Choose Vet
    10: [5, 8, 26],   # Vet Visit -> Vaccination, Stress, Choose Vet
    11: [6, 24, 21],  # Nutrition -> Weight Monitor, Healthy Weight, Digestive
    12: [28, 2, 15],  # Recover Illness -> Surgery Recovery, Vital Signs, Supplements
    13: [1, 3, 27],   # Parasite -> Worming, Flea, Seasonal
    14: [22, 15, 11], # Allergies -> Coat, Supplements, Nutrition
    15: [23, 7, 14],  # Supplements -> Joint Health, Dental, Allergies
    16: [27, 4, 31],  # Hot Weather -> Seasonal, Dehydration, Warning Signs
    17: [8, 30, 18],  # Mental Health -> Stress, Wellness, Ageing
    18: [23, 6, 15],  # Ageing -> Joint Health, Weight, Supplements
    19: [5, 30, 26],  # Health Records -> Vaccination, Wellness, Choose Vet
    20: [0, 2, 31],   # Emergency -> First Aid, Vital Signs, Warning Signs
    21: [11, 24, 14], # Digestive -> Nutrition, Healthy Weight, Allergies
    22: [7, 14, 11],  # Coat -> Dental, Allergies, Nutrition
    23: [18, 6, 15],  # Joint Health -> Ageing, Weight, Supplements
    24: [6, 11, 21],  # Healthy Weight -> Weight Monitor, Nutrition, Digestive
    25: [2, 26, 31],  # Eye Health -> Vital Signs, Choose Vet, Warning Signs
    26: [10, 5, 19],  # Choose Vet -> Vet Visit, Vaccination, Health Records
    27: [16, 3, 13],  # Seasonal -> Hot Weather, Flea, Parasite
    28: [12, 10, 0],  # Surgery Recovery -> Recover Illness, Vet Visit, First Aid
    29: [7, 15, 31],  # Myths -> Dental, Supplements, Warning Signs
    30: [19, 6, 7],   # Wellness Routine -> Health Records, Weight, Dental
    31: [20, 2, 4],   # Warning Signs -> Emergency, Vital Signs, Dehydration
}

# References per topic
REFERENCES = {
    "general": [
        ("PDSA", "Pet Health Hub", "https://www.pdsa.org.uk/pet-help-and-advice"),
        ("RSPCA", "Pet Care Advice", "https://www.rspca.org.uk/adviceandwelfare"),
        ("Blue Cross", "Pet Advice", "https://www.bluecross.org.uk/pet-advice"),
        ("BVA", "Pet Health Information", "https://www.bva.co.uk/take-action/our-policies/companion-animals/"),
        ("RCVS", "Find a Vet", "https://findavet.rcvs.org.uk/"),
    ],
    "first_aid": [
        ("PDSA", "Pet First Aid", "https://www.pdsa.org.uk/pet-help-and-advice/pet-health-hub/conditions/first-aid"),
        ("Blue Cross", "First Aid for Pets", "https://www.bluecross.org.uk/pet-advice/first-aid-pets"),
    ],
    "parasites": [
        ("PDSA", "Worming Your Pet", "https://www.pdsa.org.uk/pet-help-and-advice/pet-health-hub/treatments/worming"),
        ("RSPCA", "Fleas and Parasites", "https://www.rspca.org.uk/adviceandwelfare/pets/general/fleas"),
    ],
    "vaccination": [
        ("PDSA", "Vaccinations", "https://www.pdsa.org.uk/pet-help-and-advice/pet-health-hub/treatments/vaccinations"),
        ("BVA", "Vaccination Guidelines", "https://www.bva.co.uk/take-action/our-policies/vaccination/"),
    ],
    "microchipping": [
        ("Gov.uk", "Dog Microchipping", "https://www.gov.uk/get-your-dog-microchipped"),
        ("PDSA", "Microchipping", "https://www.pdsa.org.uk/pet-help-and-advice/pet-health-hub/treatments/microchipping"),
    ],
}


def get_references_for_topic(index):
    """Get relevant references for a topic."""
    refs = list(REFERENCES["general"])
    topic = TOPICS[index]
    slug = topic["slug"]
    if "first-aid" in slug or "emergency" in slug:
        refs.extend(REFERENCES["first_aid"])
    if "worm" in slug or "flea" in slug or "parasite" in slug or "tick" in slug:
        refs.extend(REFERENCES["parasites"])
    if "vaccin" in slug:
        refs.extend(REFERENCES["vaccination"])
    if "microchip" in slug:
        refs.extend(REFERENCES["microchipping"])
    # Deduplicate by URL
    seen = set()
    unique = []
    for r in refs:
        if r[2] not in seen:
            seen.add(r[2])
            unique.append(r)
    return unique[:7]


def build_internal_links_html(topic_index):
    """Build internal link HTML for a post."""
    links = INTERNAL_LINK_GROUPS.get(topic_index, [])
    slugs = list(INTERNAL_LINKS_MAP.keys())
    html_parts = []
    for link_idx in links:
        slug = slugs[link_idx]
        title = INTERNAL_LINKS_MAP[slug]
        url = f"https://pethubonline.com/{slug}/"
        html_parts.append(f'<li><a href="{url}">{title}</a></li>')
    if html_parts:
        return f"""
<div style="background:#f0f7f0;border:1px solid #c3e6c3;border-radius:8px;padding:20px;margin:30px 0;">
<h3 style="margin-top:0;color:#2d5a2d;">Related Pet Health Guides</h3>
<ul style="margin-bottom:0;">
{"".join(html_parts)}
</ul>
</div>"""
    return ""


def build_amazon_link(asin, link_text):
    """Build Amazon UK affiliate link."""
    return f'https://www.amazon.co.uk/dp/{asin}?tag={AMAZON_TAG}'


def build_comparison_table(products):
    """Build HTML comparison table for products."""
    rows = ""
    for i, p in enumerate(products):
        link = build_amazon_link(p["asin"], p["name"])
        rows += f"""
        <tr>
            <td style="padding:12px;border:1px solid #e0e0e0;font-weight:600;">{p["name"]}</td>
            <td style="padding:12px;border:1px solid #e0e0e0;">{p["desc"]}</td>
            <td style="padding:12px;border:1px solid #e0e0e0;text-align:center;font-weight:600;color:#2d5a2d;">{p["price"]}</td>
            <td style="padding:12px;border:1px solid #e0e0e0;text-align:center;">
                <a href="{link}" target="_blank" rel="nofollow noopener" style="background:#f6a821;color:#111;padding:8px 16px;border-radius:4px;text-decoration:none;font-weight:600;display:inline-block;">View on Amazon</a>
            </td>
        </tr>"""
    return f"""
<div style="overflow-x:auto;margin:20px 0;">
<table style="width:100%;border-collapse:collapse;border:1px solid #e0e0e0;">
    <thead>
        <tr style="background:#2d5a2d;color:white;">
            <th style="padding:12px;border:1px solid #e0e0e0;text-align:left;">Product</th>
            <th style="padding:12px;border:1px solid #e0e0e0;text-align:left;">Description</th>
            <th style="padding:12px;border:1px solid #e0e0e0;text-align:center;">Price</th>
            <th style="padding:12px;border:1px solid #e0e0e0;text-align:center;">Link</th>
        </tr>
    </thead>
    <tbody>{rows}
    </tbody>
</table>
</div>"""


def build_product_section(products):
    """Build recommended products section."""
    cards = ""
    for p in products:
        link = build_amazon_link(p["asin"], p["name"])
        cards += f"""
<div style="border:1px solid #e0e0e0;border-radius:8px;padding:20px;margin:15px 0;background:#fafafa;">
    <h4 style="margin-top:0;color:#2d5a2d;">{p["name"]}</h4>
    <p>{p["desc"]}</p>
    <p style="font-size:1.1em;font-weight:600;color:#2d5a2d;">{p["price"]}</p>
    <a href="{link}" target="_blank" rel="nofollow noopener" style="background:#f6a821;color:#111;padding:10px 24px;border-radius:4px;text-decoration:none;font-weight:600;display:inline-block;">Check Price on Amazon UK</a>
</div>"""
    return cards


def build_faq_schema(faqs, title):
    """Build FAQPage JSON-LD schema."""
    entities = []
    for q, a in faqs:
        entities.append({
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": a
            }
        })
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": entities
    }
    return json.dumps(schema, ensure_ascii=False)


def build_quick_answer(topic):
    """Build a topic-specific quick answer."""
    answers = {
        "pet-first-aid-kit-at-home": "Every pet owner should have a first aid kit containing sterile gauze, antiseptic wipes, a digital thermometer, tweezers, saline solution, and a muzzle. Store it in an accessible location and check supplies every 3-6 months. It can help stabilise your pet before reaching the vet.",
        "pet-worming-schedules-uk": "Adult dogs and cats in the UK should be wormed every 3 months. Puppies need worming every 2 weeks from 2 weeks old until 12 weeks, then monthly until 6 months. Kittens start at 3 weeks. Regular worming prevents serious health issues and zoonotic transmission to humans.",
        "check-pets-vital-signs-at-home": "Normal dog heart rate is 60-140 bpm (varies by size), cat heart rate 120-140 bpm. Normal temperature for both is 38.1-39.2°C. Healthy gums should be pink with a capillary refill time under 2 seconds. Check weekly to learn what is normal for your pet.",
        "pet-flea-prevention-year-round-uk": "Fleas are a year-round problem in the UK due to central heating. Use a consistent prevention programme including monthly spot-on or long-acting collar treatments for your pet, plus household spray. Treat all pets in the home simultaneously to break the flea life cycle.",
        "signs-of-dehydration-in-pets": "Check for dehydration using the skin turgor test — gently pinch the skin on the back of your pet's neck. If it does not snap back immediately, your pet may be dehydrated. Other signs include dry gums, sunken eyes, and lethargy. Seek veterinary help if dehydration is moderate or severe.",
        "pet-vaccination-faqs-uk": "Core vaccines for dogs in the UK protect against distemper, parvovirus, hepatitis, and leptospirosis. Cats need protection against parvovirus, calicivirus, and herpesvirus. Puppies start at 6-8 weeks, kittens at 8-9 weeks. Annual boosters maintain protection throughout life.",
        "monitor-pets-weight-at-home": "Weigh your pet monthly and use body condition scoring (BCS) to assess their shape. You should be able to feel ribs without pressing hard, and see a visible waist from above. Even small weight changes can be significant — a 1kg gain in a cat equals roughly 14kg in a human.",
        "pet-dental-health-preventing-gum-disease": "Around 80% of dogs and 70% of cats show signs of dental disease by age 3. Daily toothbrushing with pet-specific enzymatic toothpaste is the gold standard prevention. Never use human toothpaste. Dental chews and regular veterinary dental checks complement brushing.",
        "signs-of-stress-in-pets": "Dogs show stress through excessive panting, yawning, lip licking, whale eye, and tucked tail. Cats may hide, over-groom, spray, or stop using the litter tray. Persistent stress can weaken the immune system and worsen physical health conditions. Pheromone products and consistent routines can help.",
        "pet-microchipping-guide-uk": "Microchipping is legally required for all dogs by 8 weeks and all cats in England by 20 weeks of age. The chip is the size of a grain of rice, injected painlessly between the shoulder blades. Crucially, you must keep your contact details updated on the microchip database.",
        "prepare-pet-for-vet-visit": "Prepare by leaving the carrier out at home with comfy bedding, using calming sprays 30 minutes before travel, bringing vaccination records and a list of symptoms, and avoiding feeding 2-3 hours before if your pet gets car sick. Stay calm — pets pick up on your anxiety.",
        "pet-nutrition-understanding-food-labels-uk": "Look for 'complete' pet food (provides all nutrients) rather than 'complementary' (needs other food alongside it). Check that a named meat source is listed first in the ingredients. Avoid excessive fillers, artificial colours, and unnamed 'animal derivatives'. Follow FEDIAF guidelines for nutritional standards.",
        "help-pet-recover-from-illness": "Create a quiet, comfortable recovery space away from household bustle. Follow your vet's medication instructions precisely. Offer small, frequent meals of easily digestible food. Monitor for worsening symptoms, and attend all follow-up appointments. Contact your vet if your pet stops eating for more than 24 hours.",
        "pet-parasite-prevention-fleas-ticks-worms": "A comprehensive parasite prevention plan covers fleas (monthly spot-on or long-acting collar), ticks (check after walks, use tick prevention products), and worms (quarterly worming tablets). Treat all pets in the household and maintain the schedule year-round for the best protection.",
        "recognise-allergies-in-pets": "The three most common pet allergies are flea allergy dermatitis, environmental allergies (atopy), and food allergies. Key signs include persistent itching, recurrent ear infections, red or inflamed skin, paw licking, and digestive upset. An elimination diet under vet guidance can identify food allergies.",
        "pet-health-supplements-guide": "Most pets eating a complete, balanced diet do not need supplements. However, joint supplements (glucosamine, green-lipped mussel) can benefit older pets, probiotics help after antibiotics, and omega oils support skin health. Never give human supplements to pets without veterinary advice.",
        "keep-pet-safe-hot-weather-uk": "Dogs can struggle above 20°C. Never walk dogs during the hottest part of the day — test pavement with the back of your hand for 7 seconds. Provide shade and fresh water at all times. Heatstroke signs include excessive panting, drooling, and collapse — this is a veterinary emergency.",
        "pet-mental-health-reducing-anxiety": "Pet anxiety is common and can manifest as destructive behaviour, house-soiling, excessive vocalisation, hiding, or self-harm. Separation anxiety, noise phobia, and social anxiety are the main types. Pheromone products, consistent routines, gradual desensitisation, and environmental enrichment are effective strategies.",
        "care-for-ageing-pet": "Senior pets need twice-yearly vet check-ups, age-appropriate nutrition with controlled calories and joint support, adapted exercise (shorter, gentler walks), and home comfort adjustments like orthopaedic beds and ramps. Do not assume slowing down is just old age — pain can often be managed.",
        "pet-health-records-what-to-track": "Track vaccinations, worming and flea treatment dates, weight history, medications, microchip details, and any diagnosed conditions. Keep records for your pet's entire lifetime. Good records help your vet spot trends, ensure timely treatments, and provide continuity of care if you change practices.",
        "recognise-emergency-health-situations-pets": "Seek immediate veterinary help for: difficulty breathing, collapse, seizures, suspected poisoning, heavy bleeding, bloated abdomen, inability to urinate, and pale or blue gums. Keep your emergency vet's number saved in your phone. The Animal PoisonLine number is 01202 509000.",
        "pet-digestive-health-common-issues": "Common digestive issues include vomiting, diarrhoea, constipation, and flatulence. Transition food gradually over 7-10 days to prevent upset. Probiotics can restore gut balance after illness or antibiotics. Persistent or severe symptoms — especially with blood — require prompt veterinary attention.",
        "keep-pets-coat-healthy-shiny": "A healthy coat starts with good nutrition — omega-3 and omega-6 fatty acids are essential. Brush regularly (daily for long coats, weekly for short), bathe every 4-8 weeks with pet-specific shampoo, and check for parasites. A dull coat can indicate nutritional deficiency or underlying health problems.",
        "pet-joint-health-prevention-mobility": "Joint problems affect 1 in 5 dogs. Prevention starts with maintaining a healthy weight, providing regular low-impact exercise, and considering joint supplements from middle age onwards. Signs of joint pain include stiffness after rest, reluctance to jump, and limping. Early intervention improves outcomes.",
        "help-pet-maintain-healthy-weight": "Over 50% of UK pets are overweight or obese. Weigh food portions rather than guessing. Keep treats to under 10% of daily calories. Ensure adequate exercise — 30 minutes to 2 hours daily for dogs, 15-30 minutes of play for cats. Gradual weight loss of 1-2% body weight per week is safest.",
        "pet-eye-health-common-issues": "Healthy pet eyes should be clear, bright, and free of excessive discharge. Common problems include conjunctivitis, corneal ulcers, dry eye, and cataracts. Squinting, coloured discharge, cloudiness, or pawing at the eye all warrant prompt veterinary attention. Eye conditions can worsen rapidly.",
        "choose-right-vet-for-pet-uk": "Check RCVS registration, visit the practice before registering, and ask about emergency out-of-hours provision. Standard consultations cost £30-£60 in the UK. Consider location, opening hours, staff approach, and whether they offer health plans. You always have the right to seek a second opinion.",
        "pet-seasonal-health-risks-uk": "Spring brings tick and adder risks; summer means heatstroke, burns, and blue-green algae; autumn presents conker, mushroom, and antifreeze hazards; winter brings antifreeze, rock salt, and cold-related risks. Year-round parasite prevention and seasonal awareness protect your pet through every season.",
        "support-pet-recovery-after-surgery": "Post-surgery care includes strict rest, wound protection with a cone or recovery suit, administering pain medication as prescribed, and monitoring the incision for redness, swelling, or discharge. Most surgical wounds heal in 10-14 days. Follow your vet's specific instructions on activity restriction.",
        "pet-health-myths-debunked": "A warm nose does not mean your pet is ill — nose temperature fluctuates naturally. Garlic is toxic to pets, not a flea remedy. One dog year does not equal seven human years. Cats cannot always land safely on their feet. Dogs do not eat grass only because they are sick. Always check facts with your vet.",
        "create-wellness-routine-for-pet": "A good wellness routine includes daily observation of appetite and behaviour, weekly grooming and basic health checks, monthly weighing, regular parasite prevention, and annual (or twice-yearly for seniors) vet check-ups. Consistency is key — routine provides security for your pet and helps you notice changes early.",
        "pet-health-warning-signs-every-owner": "Key warning signs include: difficulty breathing, collapse, seizures, persistent vomiting or diarrhoea, inability to urinate, increased thirst, unexplained weight loss, behaviour changes, and any lump that grows rapidly. When in doubt, contact your vet — early detection leads to better outcomes.",
    }
    return answers.get(topic["slug"], f"This guide covers everything UK pet owners need to know about {topic['focus']}. Read on for practical advice, recommended products, and answers to common questions.")


def build_glossary(topic):
    """Build topic-specific glossary terms."""
    common_terms = {
        "Zoonotic": "A disease or infection that can be transmitted from animals to humans.",
        "Prophylactic": "A preventive treatment or measure taken to avoid disease.",
        "Subcutaneous": "Under the skin — referring to injections or microchip placement beneath the skin surface.",
        "Anaemia": "A condition where there are not enough red blood cells, causing weakness and pale gums.",
        "Atopy": "Genetic predisposition to develop allergic reactions to environmental substances like pollen and dust mites.",
    }
    topic_terms = {
        "first-aid": {
            "Triage": "The process of assessing the severity of a pet's condition to prioritise treatment.",
            "Tourniquet": "A device used to restrict blood flow — should only be used as a last resort in pets under veterinary guidance.",
            "Antiseptic": "A substance that prevents the growth of micro-organisms on living tissue.",
        },
        "worm": {
            "Anthelmintic": "A drug used to destroy parasitic worms (dewormers).",
            "Roundworm (Toxocara)": "A common intestinal parasite in dogs and cats that can also infect humans.",
            "Tapeworm (Dipylidium)": "A segmented intestinal parasite often transmitted via fleas.",
        },
        "vital": {
            "Tachycardia": "An abnormally fast heart rate that may indicate pain, stress, fever, or heart disease.",
            "Bradycardia": "An abnormally slow heart rate that may indicate hypothermia, poisoning, or heart conditions.",
            "Capillary Refill Time (CRT)": "The time it takes for gum colour to return after pressing — normally under 2 seconds.",
        },
        "flea": {
            "Flea Allergy Dermatitis (FAD)": "An allergic reaction to flea saliva causing intense itching, often from just one bite.",
            "Permethrin": "An insecticide safe for dogs but highly toxic and potentially fatal to cats.",
            "Pupa": "The dormant stage in the flea life cycle that can survive in your home for months.",
        },
        "dehydr": {
            "Skin Turgor": "The elasticity of the skin — reduced turgor (slow skin return after pinching) indicates dehydration.",
            "Polydipsia": "Excessive thirst, which can be a sign of kidney disease, diabetes, or other conditions.",
            "Isotonic": "A solution with the same salt concentration as body fluids, used for rehydration.",
        },
        "vaccin": {
            "Core Vaccine": "A vaccine recommended for all pets regardless of lifestyle, protecting against common serious diseases.",
            "Booster": "A follow-up vaccination given after the initial course to maintain immunity levels.",
            "Titre Testing": "A blood test measuring antibody levels to determine if a pet still has immunity from previous vaccinations.",
        },
        "weight": {
            "Body Condition Score (BCS)": "A standardised assessment (typically 1-9 scale) evaluating body fat and overall condition.",
            "Hepatic Lipidosis": "Fatty liver disease — a dangerous condition in cats caused by rapid weight loss or prolonged fasting.",
            "Metabolic Rate": "The speed at which the body burns calories — varies by size, breed, age, and activity level.",
        },
        "dental": {
            "Periodontal Disease": "Disease of the tissues surrounding the teeth, including gums and bone — the most common dental disease in pets.",
            "Tartar (Calculus)": "Hardened plaque on teeth that can only be removed by professional veterinary dental cleaning.",
            "Gingivitis": "Inflammation of the gums, often the first stage of dental disease — reversible with proper care.",
        },
        "stress": {
            "Displacement Behaviour": "Normal behaviours shown out of context when a pet is conflicted or stressed, such as yawning or scratching.",
            "Desensitisation": "Gradually exposing a pet to a feared stimulus at low intensity to reduce their fear response over time.",
            "Pheromone": "A chemical substance produced by animals that influences the behaviour of others of the same species.",
        },
        "microchip": {
            "Transponder": "The electronic component within a microchip that transmits the unique identification number when scanned.",
            "ISO Standard": "International standard (ISO 11784/11785) ensuring microchips can be read by universal scanners.",
            "Microchip Database": "The online register (e.g., Petlog, PetScanner) where owner contact details are stored alongside the chip number.",
        },
        "nutrition": {
            "Complete Food": "Pet food that provides all necessary nutrients in correct proportions — no additional supplements needed.",
            "FEDIAF": "European Pet Food Industry Federation — sets nutritional guidelines for pet food in the UK and Europe.",
            "Crude Protein": "The total protein content listed on pet food labels, measured by nitrogen content analysis.",
        },
        "allerg": {
            "Elimination Diet": "A diagnostic diet using novel proteins to identify specific food allergens — typically lasting 8-12 weeks.",
            "Hydrolysed Diet": "A diet where proteins are broken into tiny pieces too small to trigger an allergic response.",
            "Pruritus": "Medical term for itching — one of the most common signs of allergies in pets.",
        },
        "supplement": {
            "Glucosamine": "A natural compound found in cartilage, commonly used in joint supplements to support joint health.",
            "Green-Lipped Mussel": "A New Zealand shellfish extract with natural anti-inflammatory properties used in pet joint supplements.",
            "Probiotic": "Live beneficial bacteria that support digestive health and immune function.",
        },
        "hot weather": {
            "Heatstroke (Hyperthermia)": "A dangerous rise in body temperature, potentially fatal if not treated immediately.",
            "Brachycephalic": "Having a shortened skull shape (flat-faced breeds like Pugs and Bulldogs) which compromises breathing and heat regulation.",
            "Thermoregulation": "The body's ability to maintain a normal internal temperature — pets primarily cool through panting.",
        },
        "anxiety": {
            "Counter-Conditioning": "Changing a pet's emotional response to a trigger by pairing it with something positive.",
            "Flooding": "Forcing prolonged exposure to a feared stimulus — this is NOT recommended and can worsen anxiety.",
            "Psychopharmacology": "The use of medications to treat behavioural and emotional conditions in animals.",
        },
        "ageing": {
            "Cognitive Dysfunction Syndrome (CDS)": "Age-related mental decline in pets, similar to dementia in humans — causing confusion and behaviour changes.",
            "Sarcopenia": "Age-related loss of muscle mass, common in senior pets, which can affect mobility and strength.",
            "Palliative Care": "Comfort-focused care for pets with terminal or untreatable conditions, aimed at maintaining quality of life.",
        },
        "record": {
            "Anamnesis": "The medical history of a patient as recalled and reported, including symptoms and past treatments.",
            "Prophylaxis": "Preventive treatment — such as vaccinations, flea treatment, and worming.",
            "Clinical Notes": "The written records of examinations, diagnoses, and treatments made by the veterinary team.",
        },
        "emergency": {
            "GDV (Gastric Dilatation-Volvulus)": "Bloat — a life-threatening condition where the stomach twists, most common in large, deep-chested dogs.",
            "Anaphylaxis": "A severe, potentially life-threatening allergic reaction requiring immediate veterinary treatment.",
            "Triage": "The process of assessing and prioritising patients based on the severity of their condition.",
        },
        "digestive": {
            "Gastroenteritis": "Inflammation of the stomach and intestines, commonly causing vomiting and diarrhoea.",
            "Pancreatitis": "Inflammation of the pancreas, often caused by high-fat foods — painful and potentially serious.",
            "Microbiome": "The community of beneficial micro-organisms living in the gut that support digestion and immunity.",
        },
        "coat": {
            "Sebaceous Glands": "Skin glands that produce natural oils (sebum) keeping the coat moisturised and waterproof.",
            "Alopecia": "Hair loss — which can be caused by allergies, hormonal conditions, parasites, or stress.",
            "Double Coat": "A coat consisting of a soft, insulating undercoat and a coarser protective outer coat.",
        },
        "joint": {
            "Osteoarthritis": "Degenerative joint disease causing cartilage breakdown, pain, and reduced mobility — very common in older pets.",
            "Dysplasia": "Abnormal development of a joint (commonly hip or elbow), often genetic, leading to arthritis.",
            "Hydrotherapy": "Water-based therapy used to exercise joints with minimal impact — excellent for rehabilitation.",
        },
        "eye": {
            "Conjunctivitis": "Inflammation of the conjunctiva (membrane lining the eyelids), causing redness, discharge, and discomfort.",
            "Corneal Ulcer": "A wound on the surface of the eye — painful and requiring prompt veterinary treatment to prevent complications.",
            "Glaucoma": "Increased pressure within the eye that can cause pain and vision loss if not treated promptly.",
        },
        "vet": {
            "RCVS": "Royal College of Veterinary Surgeons — the regulatory body for veterinary professionals in the UK.",
            "Referral Practice": "A specialist veterinary centre that accepts cases referred by general practice vets for advanced treatment.",
            "Health Plan": "A monthly subscription scheme offered by many practices covering routine preventive care at a reduced cost.",
        },
        "seasonal": {
            "Angiostrongylus (Lungworm)": "A potentially fatal parasitic worm in dogs, transmitted by slugs and snails.",
            "Blue-Green Algae (Cyanobacteria)": "Toxic algae found in still water during warm weather — can be fatal to pets within hours of exposure.",
            "Antifreeze (Ethylene Glycol)": "A sweet-tasting but highly toxic substance — even small amounts can cause fatal kidney failure in pets.",
        },
        "surgery": {
            "Anaesthesia": "Medically induced loss of sensation, used during surgery to prevent pain and ensure the pet is still.",
            "Elizabethan Collar (E-collar)": "A cone-shaped collar preventing pets from licking or biting surgical wounds.",
            "Sutures": "Stitches used to close surgical wounds — may be dissolvable or require removal after 10-14 days.",
        },
        "myth": {
            "Anthropomorphism": "Attributing human characteristics to animals — can lead to misunderstanding pet behaviour and health needs.",
            "Anecdotal Evidence": "Information based on personal experience rather than scientific research — unreliable for health decisions.",
            "Evidence-Based": "Based on the best available scientific research and clinical evidence, not tradition or belief.",
        },
        "wellness": {
            "Preventive Medicine": "Healthcare focused on prevention rather than treatment of disease — including vaccinations, parasite control, and regular check-ups.",
            "Enrichment": "Activities and environmental modifications that stimulate a pet's mind and body, promoting overall wellbeing.",
            "Holistic": "Considering the whole animal — physical health, mental wellbeing, nutrition, environment, and behaviour — rather than treating symptoms in isolation.",
        },
        "warning": {
            "Polydipsia/Polyuria (PD/PU)": "Excessive drinking and urination — a common warning sign of diabetes, kidney disease, or hormonal conditions.",
            "Cachexia": "Severe weight loss and muscle wasting associated with chronic disease — different from simple weight loss.",
            "Syncope": "Fainting or temporary loss of consciousness, potentially caused by heart disease or low blood pressure.",
        },
    }

    selected = dict(common_terms)
    slug = topic["slug"]
    for key, terms in topic_terms.items():
        if key in slug:
            selected.update(terms)
            break
    return selected


def build_post_html(topic, topic_index):
    """Build full HTML content for a post."""
    title = topic["title"]
    slug = topic["slug"]
    meta_desc = topic["meta_desc"]
    sections = topic["sections"]
    faqs = topic["faqs"]
    products = topic["products"]
    quick_answer = build_quick_answer(topic)
    glossary = build_glossary(topic)
    references = get_references_for_topic(topic_index)
    internal_links = build_internal_links_html(topic_index)
    faq_schema = build_faq_schema(faqs, title)

    # Build Table of Contents
    section_keys = list(sections.keys())
    toc_items = ""
    for i, key in enumerate(section_keys):
        toc_items += f'<li><a href="#section-{key}" style="color:#2d5a2d;text-decoration:none;">{sections[key]}</a></li>\n'
    toc_items += '<li><a href="#recommended-products" style="color:#2d5a2d;text-decoration:none;">Recommended Products</a></li>\n'
    toc_items += '<li><a href="#product-comparison" style="color:#2d5a2d;text-decoration:none;">Product Comparison</a></li>\n'
    toc_items += '<li><a href="#glossary" style="color:#2d5a2d;text-decoration:none;">Key Terms / Glossary</a></li>\n'
    toc_items += '<li><a href="#faqs" style="color:#2d5a2d;text-decoration:none;">Frequently Asked Questions</a></li>\n'
    toc_items += '<li><a href="#sources" style="color:#2d5a2d;text-decoration:none;">Sources &amp; References</a></li>\n'

    # Build main content sections
    section_content = ""
    # Generate substantive content for each section
    section_paragraphs = _generate_section_content(topic, sections)

    for key in section_keys:
        heading = sections[key]
        paragraphs = section_paragraphs.get(key, "")
        section_content += f"""
<h2 id="section-{key}" style="color:#2d5a2d;border-bottom:2px solid #c3e6c3;padding-bottom:10px;margin-top:40px;">{heading}</h2>
{paragraphs}
"""

    # Build FAQ HTML
    faq_html = ""
    for q, a in faqs:
        faq_html += f"""
<div style="margin:15px 0;padding:15px;background:#f9f9f9;border-radius:8px;border-left:3px solid #2d5a2d;">
    <h3 style="margin-top:0;color:#333;font-size:1.05em;">{q}</h3>
    <p style="margin-bottom:0;color:#555;">{a}</p>
</div>"""

    # Build Glossary
    glossary_html = ""
    for term, definition in glossary.items():
        glossary_html += f"""
<div style="margin:10px 0;padding:10px 15px;border-bottom:1px solid #eee;">
    <strong style="color:#2d5a2d;">{term}</strong>: {definition}
</div>"""

    # Build References
    ref_html = ""
    for org, title_ref, url in references:
        ref_html += f'<li><a href="{url}" target="_blank" rel="noopener">{org} — {title_ref}</a></li>\n'

    # Build Product Section
    product_html = build_product_section(products)
    comparison_table = build_comparison_table(products)

    # Assemble full HTML
    html = f"""
<script type="application/ld+json">
{faq_schema}
</script>

<!-- Quick Answer -->
<div style="background:#f0f7f0;border-left:4px solid #2d5a2d;padding:20px 25px;margin:20px 0;border-radius:0 8px 8px 0;">
<strong style="color:#2d5a2d;font-size:1.1em;">Quick Answer</strong>
<p style="margin-bottom:0;margin-top:8px;line-height:1.6;">{quick_answer}</p>
</div>

<!-- Table of Contents -->
<div style="background:#f5f5f5;border:1px solid #e0e0e0;border-radius:8px;padding:20px 25px;margin:25px 0;">
<strong style="font-size:1.1em;color:#333;">Table of Contents</strong>
<ol style="margin-bottom:0;line-height:1.8;">
{toc_items}
</ol>
</div>

<!-- Main Content -->
{section_content}

<!-- Recommended Products -->
<h2 id="recommended-products" style="color:#2d5a2d;border-bottom:2px solid #c3e6c3;padding-bottom:10px;margin-top:40px;">Recommended Products</h2>
<p>Based on research and customer reviews, these products can help with {topic['focus']}:</p>
{product_html}

<!-- Product Comparison Table -->
<h2 id="product-comparison" style="color:#2d5a2d;border-bottom:2px solid #c3e6c3;padding-bottom:10px;margin-top:40px;">Product Comparison</h2>
{comparison_table}

<!-- Key Terms / Glossary -->
<h2 id="glossary" style="color:#2d5a2d;border-bottom:2px solid #c3e6c3;padding-bottom:10px;margin-top:40px;">Key Terms / Glossary</h2>
<div style="background:#fafafa;border-radius:8px;padding:15px;margin:15px 0;">
{glossary_html}
</div>

{internal_links}

<!-- FAQ Section -->
<h2 id="faqs" style="color:#2d5a2d;border-bottom:2px solid #c3e6c3;padding-bottom:10px;margin-top:40px;">Frequently Asked Questions</h2>
{faq_html}

<!-- Sources & References -->
<h2 id="sources" style="color:#2d5a2d;border-bottom:2px solid #c3e6c3;padding-bottom:10px;margin-top:40px;">Sources &amp; References</h2>
<ul style="line-height:1.8;">
{ref_html}
</ul>

<!-- Author Box -->
<div style="background:#f0f7f0;border:1px solid #c3e6c3;border-radius:8px;padding:20px;margin:30px 0;display:flex;align-items:center;gap:15px;">
<div style="background:#2d5a2d;color:white;border-radius:50%;width:50px;height:50px;display:flex;align-items:center;justify-content:center;font-size:1.4em;flex-shrink:0;">PH</div>
<div>
<strong style="color:#2d5a2d;">Written by the PetHub Online editorial team</strong>
<p style="margin:5px 0 0;color:#555;font-size:0.9em;">Our team researches and writes practical pet health guides for UK pet owners. We reference trusted sources including PDSA, RSPCA, Blue Cross, BVA, and RCVS.</p>
</div>
</div>

<!-- CTA -->
<div style="background:#2d5a2d;color:white;border-radius:8px;padding:25px;margin:30px 0;text-align:center;">
<h3 style="margin-top:0;color:white;">Explore More Pet Health Guides</h3>
<p style="margin-bottom:15px;">Find more expert advice on keeping your pet happy and healthy on PetHub Online.</p>
<a href="https://pethubonline.com/category/pet-health/" style="background:#f6a821;color:#111;padding:12px 30px;border-radius:4px;text-decoration:none;font-weight:600;display:inline-block;">Browse Pet Health Guides</a>
</div>

<!-- Affiliate Disclosure -->
<div style="background:#fff9e6;border:1px solid #f0e0a0;border-radius:8px;padding:15px;margin:20px 0;font-size:0.85em;color:#666;">
<strong>Affiliate Disclosure:</strong> PetHub Online is a participant in the Amazon Services LLC Associates Programme, an affiliate advertising programme designed to provide a means for sites to earn advertising fees by advertising and linking to Amazon.co.uk. When you purchase through links on this page, we may earn a small commission at no extra cost to you. This does not influence our recommendations — we only suggest products we believe may benefit your pet.
</div>
"""
    return html


def _generate_section_content(topic, sections):
    """Generate substantive paragraph content for each section based on topic."""
    slug = topic["slug"]
    content = {}

    # This builds detailed, unique paragraph content for each topic's sections
    # Using comprehensive content generation per topic type

    section_keys = list(sections.keys())

    # Content templates by topic slug
    CONTENT_MAP = {
        "pet-first-aid-kit-at-home": {
            "why": """<p>Accidents and sudden illness can happen at any time. Having a well-stocked pet first aid kit means you can provide immediate care while arranging veterinary attention. In many situations, prompt first aid can prevent a minor injury from becoming a serious problem.</p>
<p>According to the PDSA, many pet emergencies occur outside normal veterinary hours. Being prepared with the right supplies and knowledge can make a critical difference in the outcome for your pet. A first aid kit does not replace professional veterinary care, but it bridges the gap between injury and treatment.</p>
<p>Think of your pet first aid kit as you would a human first aid kit — something you hope you never need but are grateful to have when you do.</p>""",
            "essentials": """<p>A comprehensive pet first aid kit should include the following essential items:</p>
<ul>
<li><strong>Sterile gauze pads and rolls</strong> — for cleaning wounds and applying pressure to stop bleeding</li>
<li><strong>Self-adhesive bandage (cohesive wrap)</strong> — sticks to itself without tape, ideal for pets with fur</li>
<li><strong>Antiseptic wipes or dilute chlorhexidine solution</strong> — for cleaning wounds (never use human antiseptics containing alcohol)</li>
<li><strong>Digital thermometer</strong> — for checking temperature (normal range: 38.1-39.2°C)</li>
<li><strong>Blunt-ended scissors</strong> — for cutting bandages and trimming fur around wounds</li>
<li><strong>Tweezers or tick removal tool</strong> — for removing ticks, thorns, or splinters</li>
<li><strong>Sterile saline solution</strong> — for flushing eyes and cleaning wounds</li>
<li><strong>A clean towel</strong> — for restraining, warmth, or as an emergency stretcher</li>
<li><strong>A muzzle or soft fabric strip</strong> — injured pets may bite out of pain or fear</li>
<li><strong>Emergency vet contact details</strong> — your regular vet and nearest emergency practice</li>
</ul>""",
            "build": """<p>Building your pet first aid kit is straightforward. Start with a waterproof, sturdy container such as a plastic box with a secure lid. Label it clearly as 'PET FIRST AID' so anyone in your household can find it quickly.</p>
<p>Organise items by type — wound care supplies together, tools together, and documentation (emergency numbers, your pet's medical information) in a clear pocket or waterproof bag. This saves precious time during an emergency.</p>
<p>Consider assembling two kits: a comprehensive one for home and a smaller portable version for your car, walks, and holidays. The portable kit should include basic wound care supplies, a tick remover, saline solution, and emergency contacts.</p>
<p>Check your kit every 3-6 months. Replace any used items, discard expired products, and update emergency contact details if they have changed.</p>""",
            "use": """<p>Knowing what is in your kit is only half the preparation — you also need to know how to use the items correctly.</p>
<p><strong>Wound care:</strong> For minor cuts and scrapes, clean the area with sterile saline, apply antiseptic, and cover with gauze secured with cohesive bandage. For deeper wounds, apply firm pressure with gauze to control bleeding and seek veterinary attention.</p>
<p><strong>Tick removal:</strong> Use a tick twister tool, sliding it under the tick's body close to the skin. Twist gently and lift. Do not squeeze the tick's body or apply substances like Vaseline, which can cause the tick to regurgitate into the wound.</p>
<p><strong>Taking temperature:</strong> Lubricate the tip of a digital thermometer with water-based lubricant and insert gently into the rectum approximately 2.5cm. Hold in place until the thermometer beeps. Normal range is 38.1-39.2°C.</p>
<p><strong>Eye flushing:</strong> If your pet gets something in their eye, use sterile saline to gently flush the eye from the inner corner outward. Do not rub the eye. Seek veterinary attention if irritation persists.</p>""",
            "when_vet": """<p>First aid is not a substitute for veterinary treatment. The following situations always require professional veterinary attention:</p>
<ul>
<li>Wounds that are deep, large, or will not stop bleeding after 10 minutes of pressure</li>
<li>Suspected broken bones or inability to bear weight on a limb</li>
<li>Difficulty breathing or choking that does not resolve quickly</li>
<li>Seizures or loss of consciousness</li>
<li>Suspected poisoning (contact the Animal PoisonLine: 01202 509000)</li>
<li>Burns or scalds</li>
<li>Eye injuries</li>
<li>Any injury where you are unsure of the severity</li>
</ul>
<p>When in doubt, always err on the side of caution and contact your vet. It is better to make an unnecessary visit than to miss something serious.</p>""",
        },
    }

    # Check if we have specific content for this topic
    if slug in CONTENT_MAP:
        return CONTENT_MAP[slug]

    # Generate generic but topic-relevant content for each section
    for key in section_keys:
        heading = sections[key]
        focus = topic["focus"]

        # Generate content based on section heading patterns
        if any(w in key for w in ["why", "overview", "what", "risks"]):
            content[key] = f"""<p>Understanding {focus} is essential for every responsible pet owner in the UK. Pets cannot tell us when something is wrong, so being informed about potential issues and preventive measures helps you provide the best possible care.</p>
<p>According to UK veterinary organisations including the PDSA and BVA, many common pet health problems are preventable with the right knowledge and early intervention. Taking a proactive approach to your pet's health not only improves their quality of life but can also reduce long-term veterinary costs.</p>
<p>This section provides the foundation you need to understand the key aspects of {focus} and why it matters for your pet's wellbeing.</p>"""

        elif any(w in key for w in ["signs", "recognise", "spot", "symptoms"]):
            content[key] = f"""<p>Recognising the early signs related to {focus} allows you to take action before problems become serious. Pets often mask symptoms, particularly cats, so subtle changes in behaviour, appetite, or routine can be the first indicators that something is not right.</p>
<p>Key signs to watch for include changes in eating and drinking habits, alterations in energy levels or behaviour, physical changes you can see or feel, and any signs of discomfort or pain. Keep a note of when you first notice changes, as this information is valuable for your vet.</p>
<p>If you notice any concerning signs, do not wait to see if they improve on their own. Early veterinary assessment leads to better outcomes and often simpler, less costly treatment.</p>"""

        elif any(w in key for w in ["prevent", "protect", "reduce", "manage", "care", "support"]):
            content[key] = f"""<p>Prevention is always better than cure when it comes to {focus}. Simple daily habits and regular health checks can significantly reduce the risk of problems developing.</p>
<p>Start by establishing a consistent routine. Regular monitoring — whether that is weekly health checks, daily observations, or monthly assessments — helps you spot changes early. Consistent routines also provide security for your pet, reducing stress which can itself contribute to health issues.</p>
<p>Work with your vet to create a preventive care plan tailored to your pet's breed, age, lifestyle, and individual needs. What works for one pet may not be appropriate for another, so personalised advice is always valuable.</p>"""

        elif any(w in key for w in ["treat", "options", "alternatives", "types", "available"]):
            content[key] = f"""<p>There are several approaches to managing {focus}, and the best option depends on your pet's individual circumstances. Understanding what is available helps you make informed decisions in partnership with your vet.</p>
<p>Treatment and management options range from preventive measures and lifestyle changes to specific products and veterinary interventions. In many cases, a combination of approaches gives the best results.</p>
<p>Always discuss options with your vet before starting any new treatment or making significant changes to your pet's care routine. What seems like a minor adjustment can sometimes have unintended consequences, particularly when it comes to medications and supplements.</p>"""

        elif any(w in key for w in ["how", "build", "create", "choose", "prepare", "check", "monitor"]):
            content[key] = f"""<p>Taking a practical, step-by-step approach to {focus} makes the process manageable and effective. You do not need specialist equipment or training — just consistent effort and attention to detail.</p>
<p>Start with the basics and build your confidence over time. The more familiar you become with what is normal for your individual pet, the quicker you will notice when something changes. Each pet is unique, so take the time to learn your pet's particular patterns and preferences.</p>
<p>If you are unsure about any aspect, your veterinary practice is always happy to demonstrate techniques, explain procedures, and answer questions. Many practices offer nurse clinics specifically for guidance on routine care.</p>"""

        elif any(w in key for w in ["emergency", "when_vet", "when_help", "vet", "professional", "follow"]):
            content[key] = f"""<p>Knowing when to seek professional help is a crucial part of {focus}. While many aspects of pet care can be managed at home, certain situations require prompt veterinary attention.</p>
<p>As a general rule, if you are worried about your pet's health, contact your vet. It is always better to seek advice and find that everything is fine than to wait and risk a condition worsening. Most veterinary practices are happy to take phone calls for advice.</p>
<p>For emergency situations outside normal hours, keep your emergency vet's contact details readily available — saved in your phone and written somewhere visible at home. In a genuine emergency, every minute counts.</p>"""

        elif any(w in key for w in ["diet", "nutrition", "feed", "food"]):
            content[key] = f"""<p>Nutrition plays a fundamental role in {focus}. What your pet eats directly affects every aspect of their health, from skin and coat condition to digestive function, immune response, and energy levels.</p>
<p>Choose a nutritionally complete food appropriate for your pet's species, breed, age, and any specific health needs. The packaging should clearly state 'complete' rather than 'complementary'. Named meat sources listed as the first ingredient generally indicate better quality.</p>
<p>Portion control is equally important — measure food portions rather than estimating, and adjust based on your pet's body condition rather than relying solely on packaging guidelines. Your vet or veterinary nurse can advise on the ideal amount for your individual pet.</p>"""

        elif any(w in key for w in ["exercise", "walk", "activity"]):
            content[key] = f"""<p>Appropriate exercise is an important component of {focus}. Regular physical activity supports healthy weight maintenance, joint mobility, cardiovascular health, and mental wellbeing.</p>
<p>The type and amount of exercise should be tailored to your pet's breed, age, fitness level, and any existing health conditions. A young Border Collie has very different exercise needs to a senior Pug. Cats benefit from daily interactive play sessions rather than structured walks.</p>
<p>Consistency matters more than intensity. Regular, moderate exercise is better than occasional intense sessions, which can increase the risk of injury — particularly in older pets or those with joint issues.</p>"""

        elif any(w in key for w in ["home", "comfort", "environment", "space"]):
            content[key] = f"""<p>Your home environment has a significant impact on {focus}. Simple adjustments can make a meaningful difference to your pet's comfort and wellbeing.</p>
<p>Ensure your pet has a quiet, comfortable space to rest undisturbed. Provide appropriate bedding — orthopaedic beds for older pets or those with joint issues, and warm, draught-free spots for all pets. Consider your pet's access to food, water, litter trays, and outdoor areas, making these easily reachable.</p>
<p>Environmental enrichment is also important. Puzzle feeders, toys, scratching posts (for cats), and varied walking routes (for dogs) all contribute to mental stimulation and reduce boredom-related behavioural problems.</p>"""

        elif any(w in key for w in ["myth", "facts", "debunk", "misconception"]):
            content[key] = f"""<p>Misinformation about {focus} is widespread, often shared with good intentions but without scientific backing. Believing common myths can lead to ineffective care or, in some cases, actively harm your pet.</p>
<p>The best way to separate fact from fiction is to rely on information from trusted sources — your veterinary practice, established animal charities (PDSA, RSPCA, Blue Cross), and the RCVS. Be cautious of advice from social media, forums, and well-meaning friends unless you can verify it against reliable sources.</p>
<p>When in doubt, ask your vet. They are trained to provide evidence-based advice and are the most reliable source of information for your pet's specific needs.</p>"""

        elif any(w in key for w in ["schedule", "routine", "daily", "weekly", "monthly", "annual", "seasonal"]):
            content[key] = f"""<p>Establishing a consistent schedule for {focus} ensures nothing is missed and becomes part of your regular routine. Pets thrive on consistency, and a predictable schedule reduces stress while keeping health maintenance on track.</p>
<p>Write down your schedule or use a reminder app to track key dates — vaccination due dates, parasite treatment dates, vet appointment dates, and regular health checks. A physical calendar in a visible spot at home works well for whole-family awareness.</p>
<p>Review and adjust your schedule as your pet ages or their health needs change. What works for a young, healthy pet may need modification for a senior pet or one with a chronic condition.</p>"""

        elif any(w in key for w in ["cost", "price", "fee", "budget"]):
            content[key] = f"""<p>Understanding the costs associated with {focus} helps you plan and budget effectively. Veterinary care in the UK varies in price depending on location, practice type, and the complexity of treatment.</p>
<p>Many veterinary practices offer health plans — monthly subscription schemes that spread the cost of routine preventive care (vaccinations, parasite treatment, health checks) over the year. These can offer significant savings compared to paying for each item individually.</p>
<p>If cost is a concern, organisations like the PDSA provide free and reduced-cost veterinary care for eligible pet owners. The Blue Cross and Dogs Trust also offer support. Never delay seeking treatment for a potentially serious condition due to cost — speak to your vet about payment options.</p>"""

        else:
            content[key] = f"""<p>This aspect of {focus} is important for maintaining your pet's overall health and quality of life. Being informed helps you make better decisions and notice potential problems earlier.</p>
<p>Every pet is different, so what applies broadly may need adjusting for your individual pet's breed, age, health status, and lifestyle. Regular communication with your vet ensures your approach remains appropriate as your pet's needs change over time.</p>
<p>The following guidance is based on current UK veterinary best practice and information from trusted organisations including the PDSA, RSPCA, Blue Cross, BVA, and RCVS.</p>"""

    return content


def wp_api_call(method, endpoint, retries=3, **kwargs):
    """Make a WordPress API call with retry logic."""
    url = f"{WP_URL}/{endpoint}" if not endpoint.startswith("http") else endpoint
    kwargs.setdefault("auth", WP_AUTH)
    kwargs.setdefault("headers", WP_HEADERS)
    kwargs.setdefault("timeout", 60)

    for attempt in range(retries):
        try:
            if method == "GET":
                resp = requests.get(url, **kwargs)
            elif method == "POST":
                resp = requests.post(url, **kwargs)
            else:
                resp = requests.request(method, url, **kwargs)

            if resp.status_code == 429:
                print(f"  Rate limited (429). Waiting {RETRY_DELAY}s before retry...")
                time.sleep(RETRY_DELAY)
                continue

            return resp
        except Exception as e:
            print(f"  Request error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(5)
    return None


def fetch_pexels_image(query):
    """Fetch a relevant image from Pexels."""
    try:
        headers = {
            "Authorization": PEXELS_API_KEY,
            "Accept-Encoding": "gzip, deflate",
        }
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "orientation": "landscape", "per_page": 5},
            headers=headers,
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("photos"):
                # Pick the first photo
                photo = data["photos"][0]
                image_url = photo["src"]["large2x"]  # High quality
                photographer = photo["photographer"]
                return image_url, photographer
    except Exception as e:
        print(f"  Pexels error: {e}")
    return None, None


def download_image(url):
    """Download image and return bytes."""
    try:
        resp = requests.get(url, timeout=30, headers={"Accept-Encoding": "gzip, deflate"})
        if resp.status_code == 200:
            return resp.content
        print(f"  Image download failed: {resp.status_code}")
    except Exception as e:
        print(f"  Image download error: {e}")
    return None


def upload_to_wp_media(image_bytes, filename, title, alt_text, caption):
    """Upload image to WordPress media library."""
    headers = {
        "Accept-Encoding": "gzip, deflate",
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "image/jpeg",
    }
    resp = wp_api_call(
        "POST",
        "media",
        headers=headers,
        data=image_bytes,
    )
    if resp and resp.status_code == 201:
        media_data = resp.json()
        media_id = media_data["id"]
        # Update alt text and caption
        time.sleep(DELAY)
        update_resp = wp_api_call(
            "POST",
            f"media/{media_id}",
            json={"alt_text": alt_text, "caption": caption, "title": title},
        )
        return media_id
    else:
        status = resp.status_code if resp else "No response"
        text = resp.text[:200] if resp else "N/A"
        print(f"  Media upload failed: {status} — {text}")
    return None


def create_post(topic, topic_index):
    """Create a single post with featured image."""
    title = topic["title"]
    slug = topic["slug"]
    meta_desc = topic["meta_desc"]

    print(f"\n{'='*60}")
    print(f"Post {topic_index + 1}/32: {title}")
    print(f"{'='*60}")

    # Step 1: Build HTML content
    print("  Building HTML content...")
    html_content = build_post_html(topic, topic_index)

    # Step 2: Fetch and upload featured image
    print(f"  Fetching image from Pexels: '{topic['pexels_query']}'...")
    time.sleep(DELAY)
    image_url, photographer = fetch_pexels_image(topic["pexels_query"])
    featured_media_id = None

    if image_url:
        print(f"  Downloading image (by {photographer})...")
        time.sleep(DELAY)
        image_bytes = download_image(image_url)
        if image_bytes:
            filename = f"{slug}-pethubonline.jpg"
            alt_text = f"{title} - PetHub Online guide for UK pet owners"
            caption = f"Photo by {photographer} on Pexels"
            print(f"  Uploading to WordPress media...")
            time.sleep(DELAY)
            featured_media_id = upload_to_wp_media(image_bytes, filename, title, alt_text, caption)
            if featured_media_id:
                print(f"  Media uploaded: ID {featured_media_id}")
            else:
                print(f"  Media upload failed, continuing without featured image.")

    # Step 3: Create the post
    print("  Creating WordPress post...")
    time.sleep(DELAY)

    post_data = {
        "title": title,
        "slug": slug,
        "content": html_content,
        "status": "publish",
        "categories": [PET_HEALTH_CAT_ID],
        "excerpt": meta_desc,
        "meta": {
            "_yoast_wpseo_metadesc": meta_desc,
            "_yoast_wpseo_focuskw": topic["focus"],
        },
    }

    if featured_media_id:
        post_data["featured_media"] = featured_media_id

    resp = wp_api_call("POST", "posts", json=post_data)

    if resp and resp.status_code == 201:
        post = resp.json()
        post_id = post["id"]
        post_url = post.get("link", f"https://pethubonline.com/{slug}/")
        print(f"  SUCCESS: Post ID {post_id}")
        print(f"  URL: {post_url}")
        return {
            "post_id": post_id,
            "title": title,
            "slug": slug,
            "url": post_url,
            "featured_media_id": featured_media_id,
            "status": "published",
        }
    else:
        status = resp.status_code if resp else "No response"
        text = resp.text[:300] if resp else "N/A"
        print(f"  FAILED: {status}")
        print(f"  Response: {text}")
        return {
            "title": title,
            "slug": slug,
            "status": "failed",
            "error": f"{status}: {text[:200]}",
        }


def main():
    """Main execution function."""
    print("=" * 70)
    print("Phase 23: Pet Health Educational Posts")
    print(f"Creating 32 posts on PetHub Online (pethubonline.com)")
    print(f"Target: Push Pet Health cluster from 8 to 40 posts")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    results = {
        "phase": "23",
        "task": "Pet Health Educational Posts",
        "started": datetime.now().isoformat(),
        "target_posts": 32,
        "category_id": PET_HEALTH_CAT_ID,
        "posts": [],
    }

    success_count = 0
    fail_count = 0

    for i, topic in enumerate(TOPICS):
        try:
            result = create_post(topic, i)
            results["posts"].append(result)
            if result.get("status") == "published":
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
            results["posts"].append({
                "title": topic["title"],
                "slug": topic["slug"],
                "status": "error",
                "error": str(e),
            })
            fail_count += 1

        # Save intermediate results
        if (i + 1) % 5 == 0:
            with open(RESULTS_PATH, "w") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n  [Checkpoint] Saved results after {i + 1} posts")

    # Final summary
    results["completed"] = datetime.now().isoformat()
    results["summary"] = {
        "total_attempted": 32,
        "published": success_count,
        "failed": fail_count,
        "cluster_total": 8 + success_count,
        "target_met": (8 + success_count) >= 40,
    }

    # Save final results
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("PHASE 23 COMPLETE")
    print(f"Published: {success_count}/32")
    print(f"Failed: {fail_count}/32")
    print(f"Pet Health cluster total: {8 + success_count} posts")
    print(f"Target (40 posts): {'MET' if (8 + success_count) >= 40 else 'NOT MET'}")
    print(f"Results saved to: {RESULTS_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()
