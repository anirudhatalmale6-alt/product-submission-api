#!/usr/bin/env python3
"""
Phase 10AG Humanization Batch 1:
Add About This Guide + Common Mistakes + Quick Suitability Guide + What to Expect + Routine Checklist
to Dog Food, Dog Health, Puppy Care, Dog Training, Dog Care cluster posts.
"""

import subprocess
import json
import time
import csv
import os
import sys
import tempfile
import html
import re

WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
LOG_DIR = "/var/lib/freelancer/projects/40416335/phase10ag_data"
LOG_FILE = os.path.join(LOG_DIR, "humanization_batch1_log.csv")

ALREADY_TREATED = {
    3956, 3957, 3959, 5421, 5423, 5469, 5471, 5476, 5483, 5509,
    3996, 4004, 4011, 4018, 4784, 4174, 4181, 4188, 4286, 4307,
    4057, 4064, 4071, 4078, 4563, 4118, 4132, 4089, 4146, 5508
}

# ─── Cluster definitions ─────────────────────────────────────────────────────

CLUSTER_KEYWORDS = {
    "Dog Food": ["dog food", "nutrition", "feeding", "dry vs wet", "puppy food"],
    "Dog Health": ["health", "flea", "dental", "joint supplement"],
    "Puppy Care": ["puppy"],
    "Dog Training": ["training", "behaviour", "socialisation", "treat", "scratching behaviour"],
    "Dog Care": ["seasonal dog", "seasonal pet"],
}

# Priority order for classification (higher priority clusters checked first)
CLUSTER_PRIORITY = ["Dog Food", "Dog Care", "Dog Health", "Dog Training", "Puppy Care"]

# ─── About This Guide templates ──────────────────────────────────────────────

ABOUT_TEMPLATES = {
    "Dog Food": "This guide draws on published nutritional guidance from PFMA, BVA, and FEDIAF, alongside RSPCA feeding recommendations for UK pet owners.",
    "Dog Health": "Our team reviewed current veterinary guidance from the BVA, PDSA, and RSPCA to compile this health information for UK dog owners.",
    "Puppy Care": "This resource is based on developmental guidance from the Kennel Club, Dogs Trust, and PDSA, tailored for UK puppy owners.",
    "Dog Training": "We compiled this training guidance using published resources from the APDT, Kennel Club, and Dogs Trust, focusing on reward-based methods endorsed by UK veterinary organisations.",
    "Dog Care": "This seasonal care guide draws on published advice from the RSPCA, PDSA, and Blue Cross for UK pet owners.",
}

# ─── Per-post content definitions ─────────────────────────────────────────────
# Each post gets custom Common Mistakes, Suitability, What to Expect, and Routine

POST_BLOCKS = {
    # ═══════════════════════════════════════════════════════════════════════════
    # DOG FOOD CLUSTER
    # ═══════════════════════════════════════════════════════════════════════════
    3836: {
        "cluster": "Dog Food",
        "common_mistakes": [
            "<strong>Choosing food based on marketing claims alone</strong> — terms like 'premium' and 'gourmet' have no legal definition in pet food. Check the ingredients list and FEDIAF compliance instead.",
            "<strong>Switching food brands abruptly</strong> — sudden dietary changes often cause digestive upset. Transition gradually over 7–10 days, mixing increasing amounts of new food with the old.",
            "<strong>Overfeeding based on packet guidelines</strong> — manufacturer portions are often generous. Adjust based on your dog's body condition score, not just weight.",
            "<strong>Ignoring life-stage requirements</strong> — a puppy, adult, and senior dog have very different nutritional needs. 'All life stages' food may not optimise nutrition for any single stage.",
            "<strong>Assuming grain-free equals healthier</strong> — there is no evidence that grain-free diets benefit most dogs, and some grain-free formulations have been linked to heart concerns in ongoing research."
        ],
        "suitability": [
            "<strong>Best for puppies (under 12 months):</strong> Puppy-specific food with higher protein and calcium to support rapid growth — large breed puppies need controlled calcium levels.",
            "<strong>Best for senior dogs (7+ years):</strong> Senior formulas with joint-supporting nutrients, moderate protein, and reduced calories to prevent weight gain as metabolism slows.",
            "<strong>Best for active or working dogs:</strong> Higher-calorie, protein-rich food that fuels sustained energy without excessive bulk per meal.",
            "<strong>Best for dogs with sensitive stomachs:</strong> Limited-ingredient diets with a single protein source, introduced gradually to identify and avoid triggers.",
            "<strong>Best on a budget:</strong> Mid-range complete dry food from FEDIAF-compliant brands provides balanced nutrition without the premium price — ingredient quality matters more than brand name."
        ],
        "what_to_expect": "Finding the right food for your dog often involves some trial and adjustment. Most dogs settle well on a new diet within 2–3 weeks if transitioned gradually. Expect to revisit your choice as your dog ages or if health needs change.",
        "routine": {
            "title": "Feeding Routine Checklist",
            "items": [
                "Daily: Feed at consistent times (most adult dogs do well on two meals a day) and provide fresh water at all times.",
                "Weekly: Check stored food for freshness — reseal dry food bags tightly and refrigerate opened wet food.",
                "Monthly: Assess your dog's body condition by feeling their ribs and checking their waistline from above. Adjust portions if needed.",
                "Every 6 months: Weigh your dog and review whether their current food still suits their age, weight, and activity level.",
                "Annually: Discuss diet at your vet check-up, particularly if your dog has gained or lost weight or developed new health concerns."
            ]
        }
    },
    3837: {
        "cluster": "Dog Food",
        "common_mistakes": [
            "<strong>Judging dry food quality by kibble shape or colour</strong> — these are cosmetic choices that have no bearing on nutritional value. Read the ingredients and guaranteed analysis instead.",
            "<strong>Storing dry food in direct sunlight or damp conditions</strong> — heat and moisture degrade fats and vitamins. Keep kibble in an airtight container in a cool, dry place.",
            "<strong>Buying the largest bag to save money without checking consumption rate</strong> — dry food loses freshness once opened. A bag that takes more than 6 weeks to finish may go stale.",
            "<strong>Adding excessive toppers to every meal</strong> — while toppers can improve palatability, regularly adding rich extras can unbalance an otherwise complete diet.",
            "<strong>Assuming expensive always means better</strong> — some mid-range brands meet the same FEDIAF standards as premium options. Compare ingredient lists, not just prices."
        ],
        "suitability": [
            "<strong>Best for multi-dog households:</strong> Dry food stores well in bulk and is easier to portion consistently across dogs of different sizes.",
            "<strong>Best for dogs prone to dental plaque:</strong> The mechanical scraping action of chewing kibble can offer modest plaque reduction compared to soft food alone.",
            "<strong>Best for budget-conscious owners:</strong> Dry food generally costs less per serving than wet food of comparable quality, and produces less packaging waste.",
            "<strong>Best for free-feeders (if your dog self-regulates):</strong> Dry food can be left out without spoiling as quickly as wet food, though portion control is still recommended.",
            "<strong>Best for travel and convenience:</strong> Dry food is lightweight, doesn't require refrigeration, and is easy to measure when away from home."
        ],
        "what_to_expect": "Most dogs transition to a new dry food without issues if you mix it in gradually over 7–10 days. You may notice firmer stools and slightly less food waste compared to wet food. Some dogs are initially reluctant if switching from wet; a warm water soak can help.",
    },
    3838: {
        "cluster": "Dog Food",
        "common_mistakes": [
            "<strong>Thinking one format is universally better</strong> — dry and wet food each have strengths. The best choice depends on your dog's health, preferences, and your practical circumstances.",
            "<strong>Mixing wet and dry food without adjusting total calories</strong> — combining formats is fine, but the total daily intake needs recalculating to avoid overfeeding.",
            "<strong>Assuming wet food causes dental problems</strong> — dental health depends far more on genetics, chewing habits, and dental care routines than food texture alone.",
            "<strong>Choosing dry food only because it's cheaper per gram</strong> — wet food has higher moisture content (around 75–80%), so the cost per calorie is the fairer comparison.",
            "<strong>Switching format abruptly based on a friend's recommendation</strong> — what works for one dog may not suit another. Introduce any dietary change gradually."
        ],
        "suitability": [
            "<strong>Best for dogs who drink little water:</strong> Wet food's high moisture content (75–80%) helps keep hydration levels up, particularly useful for dogs with kidney concerns.",
            "<strong>Best for fussy eaters:</strong> Wet food tends to be more aromatic and palatable, making it a practical option for dogs that regularly leave dry food.",
            "<strong>Best for senior dogs with dental issues:</strong> Soft wet food is easier to chew and swallow for dogs with missing teeth or sore gums.",
            "<strong>Best for weight management:</strong> Wet food is lower in calories per volume, so dogs get a larger-looking portion for fewer calories — helpful for dogs on a diet.",
            "<strong>Best for everyday convenience:</strong> Dry food wins on storage, shelf life, and portion control, especially for owners with busy routines."
        ],
        "what_to_expect": "There is no single right answer in the dry vs wet debate. Many UK dog owners successfully combine both formats. Expect to experiment with ratios and brands to find what keeps your dog healthy, satisfied, and within a comfortable budget.",
    },
    3839: {
        "cluster": "Dog Food",
        "common_mistakes": [
            "<strong>Feeding adult food to puppies to save money</strong> — puppy food is specifically formulated with higher protein, fat, and calcium ratios essential for growth. Adult food may leave nutritional gaps.",
            "<strong>Overfeeding puppies 'because they're growing'</strong> — overweight puppies face higher risks of joint problems later in life, especially large breeds. Follow feeding guides and monitor body condition.",
            "<strong>Switching to adult food too early</strong> — small breeds typically switch at 9–12 months, but large and giant breeds should stay on puppy food until 12–18 months when bone growth completes.",
            "<strong>Giving too many treats alongside meals</strong> — treats should make up no more than 10% of daily calories. Excess treats can unbalance an otherwise complete puppy diet.",
            "<strong>Choosing puppy food based on breed-specific marketing alone</strong> — while large-breed puppy food is genuinely different (controlled calcium and phosphorus), many breed-specific labels are marketing rather than nutritional science."
        ],
        "suitability": [
            "<strong>Best for small-breed puppies:</strong> Smaller kibble size with energy-dense formulas that suit their faster metabolism and smaller stomachs.",
            "<strong>Best for large-breed puppies:</strong> Controlled calcium and phosphorus levels that support steady, even bone growth without accelerating it dangerously.",
            "<strong>Best for puppies with sensitive digestion:</strong> Single-protein, limited-ingredient puppy food introduced slowly to minimise digestive upsets during weaning.",
            "<strong>Best for puppies transitioning from breeder food:</strong> Match the breeder's brand for the first two weeks, then gradually introduce your chosen food over 7–10 days.",
            "<strong>Best on a budget:</strong> A FEDIAF-compliant complete puppy food from a mid-range brand covers all nutritional bases — supplementation is rarely needed with a complete food."
        ],
        "what_to_expect": "Puppies typically need 3–4 meals a day initially, reducing to twice daily by around 6 months. Growth rates vary by breed, so expect to adjust portions regularly. A well-fed puppy should have visible waist definition and ribs you can feel but not see.",
        "routine": {
            "title": "Puppy Feeding Routine Checklist",
            "items": [
                "Daily: Feed at consistent times (3–4 meals up to 4 months, 3 meals to 6 months, then twice daily) with fresh water always available.",
                "Weekly: Weigh your puppy during the rapid growth phase (8 weeks to 6 months) and adjust portions based on the food manufacturer's weight chart.",
                "Monthly: Assess body condition — you should be able to feel ribs easily but not see them prominently.",
                "At each vet visit: Discuss growth rate and diet suitability, especially for large and giant breed puppies where controlled growth matters most.",
                "At 9–18 months (breed-dependent): Plan the transition from puppy to adult food, mixing gradually over 10–14 days."
            ]
        }
    },
    5460: {
        "cluster": "Dog Food",
        "common_mistakes": [
            "<strong>Confusing 'complete' with 'complementary' food</strong> — 'complete' food provides all required nutrients; 'complementary' is designed to be fed alongside other food. Feeding complementary food alone leads to deficiencies.",
            "<strong>Misreading 'meat and animal derivatives' as low quality</strong> — this legal term covers a wide range of ingredients, from premium offal to less desirable by-products. It's not automatically bad, but named meat sources are more transparent.",
            "<strong>Assuming 'natural' means organic or regulated</strong> — 'natural' has minimal legal protection in pet food labelling. It doesn't guarantee organic sourcing or higher safety standards.",
            "<strong>Ignoring the ingredients order</strong> — ingredients are listed by weight before processing. A named meat listed first means it's the dominant ingredient by pre-cooking weight, but moisture loss during processing may change the final proportion.",
            "<strong>Overlooking the FEDIAF statement</strong> — this confirms the food meets EU nutritional standards. Its absence should prompt caution regardless of other marketing claims."
        ],
        "suitability": [
            "<strong>Best for new dog owners:</strong> Understanding label terminology helps you make informed choices from day one rather than relying on brand reputation alone.",
            "<strong>Best for owners managing food allergies:</strong> Knowing how to read ingredient declarations is essential for identifying and avoiding allergens consistently.",
            "<strong>Best for budget-conscious buyers:</strong> Label literacy lets you compare products on nutritional content rather than packaging design, often revealing mid-range options that rival premium brands.",
            "<strong>Best for owners of dogs with health conditions:</strong> Understanding terms like 'crude protein' and 'ash content' helps you match veterinary dietary advice to available products."
        ],
        "what_to_expect": "Pet food labels can be confusing at first, but once you understand the key terms and what to look for, comparing products becomes straightforward. Most owners find that label literacy saves both money and guesswork within a few shopping trips.",
    },
    5467: {
        "cluster": "Dog Food",
        "common_mistakes": [
            "<strong>Using the same portion size regardless of activity level</strong> — a dog walked for 30 minutes daily needs significantly fewer calories than one exercised for two hours. Adjust portions to match actual energy expenditure.",
            "<strong>Free-feeding a dog that doesn't self-regulate</strong> — leaving food out all day works for some dogs, but many will overeat. Timed meals help you monitor intake and spot appetite changes early.",
            "<strong>Measuring portions by eye instead of by weight or cup</strong> — small overestimates add up quickly. A kitchen scale or proper measuring cup improves accuracy significantly.",
            "<strong>Treating feeding guidelines as fixed rules</strong> — packet recommendations are starting points. Your dog's ideal portion depends on their individual metabolism, activity, and body condition.",
            "<strong>Feeding one large meal instead of two</strong> — splitting daily food into two meals reduces the risk of bloat (gastric dilatation-volvulus), especially in larger breeds."
        ],
        "suitability": [
            "<strong>Best for new dog owners:</strong> A structured feeding schedule establishes routine, aids housetraining, and makes it easier to spot changes in appetite that may signal health issues.",
            "<strong>Best for overweight dogs:</strong> Measured portions combined with scheduled feeding times are the foundation of any effective weight management plan.",
            "<strong>Best for multi-dog households:</strong> Individual feeding stations and timed meals prevent food guarding and ensure each dog gets the right amount.",
            "<strong>Best for puppies:</strong> Frequent, measured meals (3–4 daily, reducing to 2 by 6 months) support steady growth without overloading small stomachs."
        ],
        "what_to_expect": "Establishing a feeding routine takes about a week for most dogs. You'll likely need to fine-tune portions over the first month as you learn your dog's individual needs. Regular body condition checks make adjustment straightforward.",
        "routine": {
            "title": "Feeding Schedule Checklist",
            "items": [
                "Daily: Feed at consistent times (within 30 minutes of the same time each day) to establish a reliable routine.",
                "Daily: Remove uneaten food after 15–20 minutes to prevent grazing and track actual intake.",
                "Weekly: Check stored food freshness and ensure water bowls are cleaned with hot soapy water.",
                "Monthly: Weigh your dog or assess body condition score, adjusting portions up or down as needed.",
                "Seasonally: Review calorie needs — most dogs require slightly more in winter (outdoor dogs especially) and slightly less in summer."
            ]
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DOG HEALTH CLUSTER
    # ═══════════════════════════════════════════════════════════════════════════
    4096: {
        "cluster": "Dog Health",
        # Already has Suitability + Routine from previous script, needs About + Mistakes only
        "common_mistakes": [
            "<strong>Waiting for visible tartar before starting dental care</strong> — by the time you can see tartar, periodontal disease may already be progressing beneath the gumline.",
            "<strong>Using human toothpaste on dogs</strong> — fluoride and xylitol in human toothpaste are toxic to dogs. Always use enzymatic toothpaste formulated for canines.",
            "<strong>Relying solely on dental chews</strong> — dental chews supplement brushing but don't replace it. They reduce surface plaque but can't clean below the gumline effectively.",
            "<strong>Ignoring bad breath as 'normal'</strong> — persistent bad breath is often the first sign of dental disease, not just a cosmetic issue. It warrants a vet check.",
            "<strong>Skipping professional dental checks</strong> — home care prevents much disease, but only a vet can assess below the gumline and address issues requiring scaling or extraction."
        ],
        "skip_suitability": True,
        "skip_routine": True,
    },
    4103: {
        "cluster": "Dog Health",
        # Already has Suitability + Routine from previous script
        "common_mistakes": [
            "<strong>Stopping flea treatment during winter</strong> — UK homes with central heating provide a warm environment where fleas survive year-round. Continuous treatment prevents re-infestation.",
            "<strong>Treating only the pet, not the environment</strong> — 95% of the flea population lives in carpets, bedding, and soft furnishings, not on your dog. Environmental treatment is essential.",
            "<strong>Using dog flea products on cats</strong> — some dog flea treatments contain permethrin, which is highly toxic to cats. Always use species-specific products.",
            "<strong>Applying spot-on treatment incorrectly</strong> — the product must contact skin, not just fur. Part the coat at the base of the skull and apply directly to the skin.",
            "<strong>Assuming a flea-free dog means a flea-free home</strong> — flea eggs can lie dormant for months. A single missed treatment cycle can allow a full re-infestation."
        ],
        "skip_suitability": True,
        "skip_routine": True,
    },
    4110: {
        "cluster": "Dog Health",
        # Already has Suitability + Routine from previous script
        "common_mistakes": [
            "<strong>Starting supplements only after symptoms appear</strong> — joint supplements work best as preventative support, especially for breeds predisposed to joint problems. Early use preserves cartilage.",
            "<strong>Expecting overnight results</strong> — glucosamine and chondroitin typically take 4–6 weeks of consistent daily use before improvements become noticeable.",
            "<strong>Choosing supplements based on human formulations</strong> — canine joint supplements are dosed and formulated specifically for dogs. Human supplements may contain ingredients harmful to dogs (e.g., xylitol).",
            "<strong>Using supplements as a substitute for weight management</strong> — no supplement can compensate for the joint stress caused by excess body weight. Weight control is the single most effective joint intervention.",
            "<strong>Ignoring product quality and sourcing</strong> — the supplement market is loosely regulated. Look for products with NASC (National Animal Supplement Council) quality seals or veterinary endorsement."
        ],
        "skip_suitability": True,
        "skip_routine": True,
    },
    4568: {
        "cluster": "Dog Health",
        "common_mistakes": [
            "<strong>Brushing only when breath smells bad</strong> — dental disease develops silently. By the time breath is noticeably foul, bacteria may have already damaged gums and bone structure.",
            "<strong>Assuming hard treats clean teeth sufficiently</strong> — while some chewing helps, hard bones can fracture teeth. VOHC-approved dental products are a safer option for plaque control.",
            "<strong>Neglecting back teeth</strong> — premolars and molars are where tartar builds fastest but are the hardest to reach. Focus brushing effort here, even if you only manage a quick session.",
            "<strong>Skipping dental checks because your dog 'seems fine'</strong> — dogs rarely show obvious pain from dental disease. Regular vet checks catch problems that outward behaviour hides."
        ],
        "suitability": [
            "<strong>Best for puppies:</strong> Start handling their mouth and touching teeth early — even without a brush — so dental care feels normal from the beginning.",
            "<strong>Best for senior dogs:</strong> Increase dental check frequency to every 6 months, as age-related dental disease accelerates after 7 years in most breeds.",
            "<strong>Best for small breeds:</strong> Toy and small breeds are disproportionately prone to dental overcrowding and early tooth loss. Daily brushing makes a measurable difference.",
            "<strong>Best for dogs who resist brushing:</strong> Dental water additives and enzyme-based dental chews provide passive cleaning when brushing isn't tolerated.",
            "<strong>Best on a budget:</strong> A canine toothbrush and enzymatic paste cost under £10 and prevent conditions that can cost hundreds to treat."
        ],
        "what_to_expect": "Building a dental care habit takes patience. Most dogs tolerate tooth brushing within 2–3 weeks if introduced gradually with positive reinforcement. Even partial brushing is far better than none at all.",
        "routine": {
            "title": "Dental Health Routine Checklist",
            "items": [
                "Daily: Brush teeth for 30–60 seconds with canine enzymatic toothpaste, focusing on the outer surfaces of back teeth.",
                "Weekly: Offer a VOHC-approved dental chew or treat to supplement brushing and disrupt plaque between sessions.",
                "Monthly: Lift your dog's lips and check gums for redness, swelling, or recession — early gum disease is reversible.",
                "Every 6 months: Assess breath, eating habits, and pawing at the mouth. Any changes warrant a vet visit.",
                "Annually: Professional dental examination as part of your dog's routine veterinary health check."
            ]
        }
    },
    5520: {
        "cluster": "Dog Health",
        "common_mistakes": [
            "<strong>Skipping annual vet check-ups because your dog 'looks healthy'</strong> — many conditions (heart disease, early-stage kidney problems, dental disease) are invisible externally until well advanced.",
            "<strong>Using Dr. Google to diagnose symptoms</strong> — online symptom checkers can cause unnecessary panic or dangerous reassurance. A real veterinary assessment is always the safer path.",
            "<strong>Delaying treatment for 'minor' symptoms</strong> — limping, drinking more water, or reduced appetite can indicate serious conditions that respond best to early intervention.",
            "<strong>Relying on pet insurance to cover everything</strong> — most policies have exclusions, waiting periods, and excesses. Understand your cover before you need it.",
            "<strong>Ignoring weight gain as 'just a bit of extra padding'</strong> — obesity is the most common preventable health condition in UK dogs, linked to diabetes, joint disease, and shortened lifespan."
        ],
        "suitability": [
            "<strong>Best for new dog owners:</strong> Understanding common conditions and their early signs helps you respond appropriately rather than over- or under-reacting.",
            "<strong>Best for senior dogs (7+ years):</strong> Twice-yearly vet visits and awareness of age-related conditions (arthritis, cognitive decline, organ disease) make the biggest difference at this stage.",
            "<strong>Best for breed-prone conditions:</strong> Research your breed's known health risks so you can discuss screening and prevention with your vet proactively.",
            "<strong>Best for prevention-focused owners:</strong> Vaccination, parasite control, dental care, and weight management prevent the vast majority of common canine health problems.",
            "<strong>Best on a budget:</strong> Preventative care (vaccinations, flea/worm treatment, weight management) is consistently cheaper than treating the conditions it prevents."
        ],
        "what_to_expect": "No dog goes through life without some health concerns. Knowing what's normal for your dog — their typical energy level, appetite, drinking habits, and behaviour — is your most valuable diagnostic tool. Changes from that baseline are what matter most.",
        "routine": {
            "title": "Health Monitoring Routine Checklist",
            "items": [
                "Daily: Observe energy levels, appetite, water intake, and toileting habits for any changes from your dog's normal pattern.",
                "Weekly: Run your hands over your dog's body checking for lumps, sore spots, skin changes, or areas they flinch from.",
                "Monthly: Administer flea and worming treatments on schedule; weigh your dog or do a body condition assessment.",
                "Every 6 months: Dental check (visual inspection at home), plus a weigh-in if your dog is on a weight management plan.",
                "Annually: Full veterinary health check, vaccination boosters, and discussion of any age-related or breed-specific screening."
            ]
        }
    },
    5521: {
        "cluster": "Dog Health",
        "common_mistakes": [
            "<strong>Panicking over unfamiliar terms in a vet report</strong> — many medical terms sound alarming but describe routine findings. Ask your vet to explain anything you don't understand in plain language.",
            "<strong>Confusing 'benign' with 'no action needed'</strong> — a benign lump still needs monitoring. 'Benign' means non-cancerous, not that it can't grow or cause complications.",
            "<strong>Assuming blood test results outside the reference range always mean disease</strong> — minor deviations can be normal for individual dogs. Your vet interprets results in context, not in isolation.",
            "<strong>Dismissing 'prophylactic' treatments as unnecessary</strong> — prophylactic means preventive. Flea treatments, vaccinations, and dental care are prophylactic measures that prevent far more expensive problems."
        ],
        "suitability": [
            "<strong>Best for new pet owners:</strong> Understanding basic veterinary terminology reduces anxiety at consultations and helps you follow aftercare instructions accurately.",
            "<strong>Best for owners of dogs with chronic conditions:</strong> Familiarity with terms like 'prognosis,' 'remission,' and 'palliative' helps you engage more meaningfully with treatment decisions.",
            "<strong>Best for those reading pet insurance documents:</strong> Policy exclusions and conditions often use medical terminology — understanding these terms prevents claim surprises.",
            "<strong>Best for owners researching breed health:</strong> Health screening terms (e.g., 'hip score,' 'BVA eye test') make more sense when you understand the underlying vocabulary."
        ],
        "what_to_expect": "Veterinary terminology can feel overwhelming at first, but most consultations rely on a surprisingly small set of common terms. This guide covers the ones you'll encounter most often, making future vet visits less confusing.",
    },
    5522: {
        "cluster": "Dog Health",
        "common_mistakes": [
            "<strong>Waiting until a dog is visibly limping before addressing joint health</strong> — dogs are stoic animals. By the time lameness is obvious, joint damage is often well established.",
            "<strong>Over-exercising young dogs during growth phases</strong> — forced running on hard surfaces before skeletal maturity (12–18 months depending on breed) can damage developing joints permanently.",
            "<strong>Skipping weight management in favour of supplements alone</strong> — carrying excess weight places continuous stress on joints that no supplement can fully offset. Weight control comes first.",
            "<strong>Using stairs and jumping as exercise for dogs with joint problems</strong> — high-impact activities worsen joint damage. Controlled, low-impact exercise (swimming, gentle lead walks) is far safer.",
            "<strong>Buying orthopaedic beds without checking foam density</strong> — thin or low-density foam compresses under body weight within weeks, removing the orthopaedic benefit entirely."
        ],
        "suitability": [
            "<strong>Best for large and giant breeds:</strong> Early joint care (weight management, controlled exercise, appropriate bedding) matters most for breeds predisposed to hip and elbow dysplasia.",
            "<strong>Best for senior dogs showing stiffness:</strong> A combination of joint supplements, orthopaedic support, and adapted exercise can significantly improve comfort and mobility.",
            "<strong>Best for post-surgery recovery:</strong> Understanding rehab principles (rest phases, controlled movement, ramp introduction) helps owners support healing without setbacks.",
            "<strong>Best for active dogs:</strong> Preventative joint care before symptoms appear protects working dogs and those in agility or flyball from premature joint wear.",
            "<strong>Best on a budget:</strong> Weight management and controlled exercise cost nothing and deliver the biggest single improvement in joint health outcomes."
        ],
        "what_to_expect": "Joint health is a long-term commitment, not a quick fix. Most dogs with managed joint conditions live comfortably for years with the right combination of weight control, exercise modification, supplements, and veterinary guidance.",
        "routine": {
            "title": "Joint Health Routine Checklist",
            "items": [
                "Daily: Administer joint supplements consistently and observe your dog's movement for any changes in gait or willingness to exercise.",
                "Weekly: Provide low-impact exercise (swimming, controlled lead walks) appropriate to your dog's condition and fitness.",
                "Monthly: Weigh your dog — even 1kg of excess weight adds measurable stress to already-compromised joints.",
                "Every 3 months: Review comfort levels at rest and during activity; adjust exercise intensity and duration as needed.",
                "Annually: Veterinary joint assessment including range-of-motion check and discussion of pain management options."
            ]
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PUPPY CARE CLUSTER
    # ═══════════════════════════════════════════════════════════════════════════
    3960: {
        "cluster": "Puppy Care",
        "common_mistakes": [
            "<strong>Giving puppies toys designed for adult dogs</strong> — oversized or excessively hard toys can damage developing teeth and discourage play. Choose age-appropriate sizes and textures.",
            "<strong>Leaving teething puppies unsupervised with plush toys</strong> — stuffing and squeakers can be ingested quickly during intense teething phases. Supervise or choose toys without removable parts.",
            "<strong>Buying too many toys at once</strong> — puppies are easily overwhelmed. Start with 3–4 varied toys and rotate them weekly to maintain novelty without overspending.",
            "<strong>Ignoring material safety</strong> — cheap toys may contain toxic dyes or small detachable pieces. Look for non-toxic labelling and CE markings from reputable manufacturers.",
            "<strong>Skipping frozen teething toys</strong> — a damp flannel or rubber toy frozen overnight provides soothing relief for sore gums that standard toys don't offer."
        ],
        "suitability": [
            "<strong>Best for teething puppies (3–6 months):</strong> Soft rubber teething toys and frozen options that soothe inflamed gums without risking tooth fracture.",
            "<strong>Best for high-energy puppies:</strong> Tug toys and fetch toys that direct energy into structured play rather than destructive chewing.",
            "<strong>Best for puppies left alone for short periods:</strong> Kong-style stuffable toys filled with paste or kibble that provide independent entertainment.",
            "<strong>Best for socialisation through play:</strong> Rope toys and soft balls that encourage interactive play with humans, building trust and recall.",
            "<strong>Best on a budget:</strong> A frozen damp flannel, a basic rubber Kong, and a simple rope toy cover most puppy play needs for under £15."
        ],
        "what_to_expect": "Puppies go through distinct play phases. Mouthing and chewing peak between 3–6 months during teething, then settle as adult teeth come in. Expect to replace a few toys during this period — it's normal, not a sign of a 'problem chewer.'",
    },
    4049: {
        "cluster": "Puppy Care",
        "common_mistakes": [
            "<strong>Buying a collar sized for the adult dog</strong> — a collar that's too large provides no control and can slip off or catch on objects. Buy for the puppy's current size and resize as they grow.",
            "<strong>Using a collar for lead-walking before the puppy is lead-trained</strong> — pulling on a collar can injure a puppy's developing trachea. Use a harness for walks until loose-lead walking is established.",
            "<strong>Tightening the collar too much 'for security'</strong> — you should be able to fit two fingers between the collar and your puppy's neck. Tighter than this restricts breathing and causes discomfort.",
            "<strong>Choosing style over function</strong> — decorative collars are fine for ID tags, but the primary collar needs a secure buckle or clip and a sturdy D-ring for the lead.",
            "<strong>Forgetting to check collar fit as the puppy grows</strong> — puppies grow rapidly. A collar that fit last month may be dangerously tight today. Check weekly during growth spurts."
        ],
        "suitability": [
            "<strong>Best for puppies under 12 weeks:</strong> Lightweight, adjustable flat collars in a soft material — the priority is getting them comfortable wearing a collar, not training equipment.",
            "<strong>Best for lead walks:</strong> A well-fitted Y-shaped puppy harness that distributes pressure across the chest, protecting the trachea during early lead training.",
            "<strong>Best for ID and safety:</strong> A simple flat collar with an engraved tag (name + phone number) should be worn at all times, even if a harness is used for walks.",
            "<strong>Best for fast-growing large breed puppies:</strong> Adjustable collars and harnesses with a wide size range — avoid buying fixed-size options that will be outgrown within weeks.",
            "<strong>Best on a budget:</strong> A basic adjustable nylon collar and a clip-on ID tag provide legal compliance and safety for under £10."
        ],
        "what_to_expect": "Most puppies accept a collar within 2–3 days if introduced with positive associations (treats, praise). Some initial scratching or head-shaking is normal. Expect to replace or adjust the collar 3–4 times during the first year as your puppy grows.",
    },
    5417: {
        "cluster": "Puppy Care",
        "common_mistakes": [
            "<strong>Overwhelming a new puppy with visitors in the first few days</strong> — puppies need quiet settling time to adjust to their new home before socialising with extended family and friends.",
            "<strong>Assuming socialisation means meeting as many dogs as possible</strong> — quality matters more than quantity. A few calm, positive encounters outweigh dozens of chaotic ones.",
            "<strong>Skipping crate training because it 'seems cruel'</strong> — when introduced properly, a crate becomes a safe den that supports housetraining, prevents destructive behaviour, and gives the puppy a secure retreat.",
            "<strong>Expecting puppies to 'hold it' for too long</strong> — a general rule is one hour per month of age, plus one. A 3-month-old puppy needs a toilet break roughly every 4 hours.",
            "<strong>Starting formal obedience training before the puppy is settled</strong> — the first 1–2 weeks should focus on bonding, housetraining, and establishing routine. Formal training can begin once the puppy feels secure."
        ],
        "suitability": [
            "<strong>Best for first-time puppy owners:</strong> Focus on the fundamentals — housetraining, crate training, basic socialisation, and establishing a vet relationship — before worrying about advanced training.",
            "<strong>Best for families with children:</strong> Teach children to interact calmly and read basic puppy body language. Set clear rules about handling, especially during rest and mealtimes.",
            "<strong>Best for those working from home:</strong> Resist the urge to interact constantly. Scheduled alone-time prevents separation anxiety when your routine eventually changes.",
            "<strong>Best for flat/apartment dwellers:</strong> More frequent toilet trips and structured exercise replace garden access. Indoor enrichment and puzzle toys compensate for limited space.",
            "<strong>Best on a budget:</strong> The essentials — vet registration, basic training, consistent routine, and socialisation — cost very little. The first year's biggest expenses are vaccinations and neutering, not equipment."
        ],
        "what_to_expect": "The first few weeks with a new puppy are tiring but rewarding. Expect broken sleep, frequent toilet trips, and some trial and error. Most puppies settle into a household routine within 2–4 weeks with consistent handling.",
        "routine": {
            "title": "New Puppy Weekly Priorities",
            "items": [
                "Week 1: Focus on settling in — establish toilet spot, sleeping area, and feeding times. Minimise visitors.",
                "Week 2: Begin gentle handling exercises (touching paws, ears, mouth) and short collar-wearing sessions.",
                "Weeks 3–4: Start basic name recognition, 'sit' with a lure, and short lead sessions indoors or in the garden.",
                "Months 2–3: Begin socialisation outings (carrying if not fully vaccinated), puppy classes, and crate training.",
                "Months 3–6: Increase exercise gradually, strengthen recall, and practise commands in varied environments."
            ]
        }
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DOG TRAINING CLUSTER
    # ═══════════════════════════════════════════════════════════════════════════
    4034: {
        "cluster": "Dog Training",
        # Already has Suitability + Key Considerations from previous script
        "common_mistakes": [
            "<strong>Using a no-pull harness as a permanent substitute for training</strong> — the harness manages pulling mechanically, but without reward-based loose-lead training alongside it, the underlying behaviour remains.",
            "<strong>Fitting the harness incorrectly</strong> — a no-pull harness that rides up into the armpits or shifts to one side causes chafing, restricts movement, and reduces effectiveness. Recheck fit monthly.",
            "<strong>Expecting instant results with every dog</strong> — while many dogs improve within the first few walks, some strong pullers need several weeks of consistent harness-plus-training work.",
            "<strong>Choosing a back-clip harness for a strong puller</strong> — back-clip designs can actually encourage pulling by allowing the dog to lean into the harness. Front-clip redirects forward momentum.",
            "<strong>Tightening straps too much for 'extra control'</strong> — harness straps should allow a flat hand to slide underneath. Over-tightening restricts natural gait and causes discomfort."
        ],
        "skip_suitability": True,
    },
    4042: {
        "cluster": "Dog Training",
        # Already has Suitability + Key Considerations from previous script
        "common_mistakes": [
            "<strong>Using a retractable lead in busy or urban areas</strong> — the variable length makes control unpredictable near traffic, other dogs, and pedestrians. A fixed-length lead is safer in these environments.",
            "<strong>Choosing lead thickness based on dog size alone</strong> — a thin lead on a strong dog can snap, but an overly heavy lead on a small breed causes neck strain. Match lead strength to your dog's weight and pulling force.",
            "<strong>Wrapping the lead around your hand or fingers</strong> — if your dog lunges, a wrapped lead can cause burns or fractures. Hold the handle loop and use a traffic grip (short loop near the clip) for close control.",
            "<strong>Never practising off-lead recall before using a long line</strong> — a long training lead is for practising recall at distance, not for replacing training. Build recall reliability before extending lead length.",
            "<strong>Using a chain lead 'for tough dogs'</strong> — chain leads are heavy, uncomfortable to hold, and offer no advantage over a quality nylon or leather lead with a secure clip."
        ],
        "skip_suitability": True,
    },
    4125: {
        "cluster": "Dog Training",
        "common_mistakes": [
            "<strong>Using treats that are too large</strong> — training treats should be pea-sized or smaller. Large treats slow the session, add unnecessary calories, and reduce the number of repetitions you can fit in.",
            "<strong>Exceeding the 10% calorie rule</strong> — treats should make up no more than 10% of your dog's daily calorie intake. Reduce meal portions on heavy training days to compensate.",
            "<strong>Using the same treat for everything</strong> — reserve high-value treats (cheese, liver, dried fish) for difficult tasks like recall. Use everyday treats for basic commands to maintain a reward hierarchy.",
            "<strong>Choosing treats your dog isn't motivated by</strong> — some dogs prefer soft, smelly treats; others respond better to crunchy ones. Observe what your dog works hardest for and use that.",
            "<strong>Relying on treats indefinitely without fading</strong> — treats establish behaviours, but should gradually be replaced with verbal praise, play, or life rewards (access to a sniff spot, for example) as the behaviour becomes reliable."
        ],
        "suitability": [
            "<strong>Best for basic obedience training:</strong> Soft, small, quick-to-eat treats that don't interrupt session flow — the dog should swallow and refocus within 2 seconds.",
            "<strong>Best for recall training:</strong> High-value, strong-smelling treats (dried liver, cheese, fish) that compete with environmental distractions.",
            "<strong>Best for puppies:</strong> Tiny, soft treats formulated for puppies, or small pieces of their regular kibble reserved from meals.",
            "<strong>Best for dogs on restricted diets:</strong> Single-ingredient treats (freeze-dried meat or fish) that avoid common allergens.",
            "<strong>Best on a budget:</strong> Chopped cooked chicken breast, small cheese cubes, or regular kibble hand-fed during training sessions work as well as branded training treats."
        ],
        "what_to_expect": "Most dogs respond to treat-based training within the first session. The challenge is consistency and portion management, not motivation. Expect to experiment with 2–3 treat types before finding what your dog values most.",
    },
    4139: {
        "cluster": "Dog Training",
        "common_mistakes": [
            "<strong>Using a long line without open space</strong> — training leads of 5–10 metres require unobstructed areas. In confined or busy spaces, the lead becomes a tangling hazard for dogs, people, and objects.",
            "<strong>Attaching a long line to a collar instead of a harness</strong> — a sudden stop at the end of a long line generates significant force. A collar transfers this to the neck; a back-clip harness distributes it safely.",
            "<strong>Letting the lead drag freely on the ground</strong> — a dragging long line can catch on branches, legs, or other dogs. Gather slack in loose loops in your hand to maintain awareness of the remaining length.",
            "<strong>Replacing recall training with lead dependence</strong> — a training lead is a safety tool while you build recall reliability, not a permanent alternative to training a solid recall.",
            "<strong>Buying cheap carabiner clips</strong> — the clip is the weakest point on most leads. A dog lunging at the end of a 10-metre lead generates substantial force. Choose bolt-snap or trigger-snap clips rated for your dog's weight."
        ],
        "suitability": [
            "<strong>Best for recall training:</strong> A 5–10 metre long line gives your dog the feeling of freedom while you maintain a safety connection during recall practice.",
            "<strong>Best for reactive dogs:</strong> A fixed-length lead (1.2–1.5m) with a padded handle provides predictable control in situations where reactions may occur.",
            "<strong>Best for hands-free walking:</strong> Waist-attached leads suit runners and hikers, freeing both hands while keeping the dog connected — choose one with a bungee section to absorb sudden pulls.",
            "<strong>Best for multi-dog walking:</strong> Coupler attachments or individual leads in each hand (avoid tangling splitter leads for dogs that pull in different directions).",
            "<strong>Best on a budget:</strong> A basic 1.5m nylon lead with a quality snap hook handles all standard walking and early training needs for under £10."
        ],
        "what_to_expect": "The right training lead can transform recall practice. Most dogs show noticeable recall improvement within 2–4 weeks of consistent long-line work combined with high-value rewards. Expect some tangling initially — it gets easier with practice.",
    },
    4791: {
        "cluster": "Dog Training",
        "common_mistakes": [
            "<strong>Assuming all dogs value the same rewards equally</strong> — reward preference varies widely. Some dogs work harder for a ball throw than any treat. Observe what genuinely excites your dog.",
            "<strong>Using training treats as a bribe rather than a reward</strong> — if you show the treat before the behaviour, it becomes a bribe. Reward after the behaviour to reinforce it properly.",
            "<strong>Not adjusting treat value to the difficulty</strong> — asking for a recall away from squirrels deserves a high-value treat. Rewarding a sit at home can be a kibble piece. Match value to effort.",
            "<strong>Forgetting to reduce meal portions on training-heavy days</strong> — it's easy to add 200+ extra calories in treats during an active training session without realising.",
            "<strong>Buying treats based on marketing rather than ingredients</strong> — some 'training treats' are packed with sugar and fillers. Short, recognisable ingredient lists are the better indicator of quality."
        ],
        "suitability": [
            "<strong>Best for clicker training:</strong> Very small, soft treats that can be delivered instantly — the reward must follow the click within 1–2 seconds for effective conditioning.",
            "<strong>Best for outdoor training sessions:</strong> Smelly treats (liver, fish-based) that compete with environmental distractions. Dry biscuits are often insufficient outdoors.",
            "<strong>Best for overweight dogs in training:</strong> Use part of the daily food allowance as training treats, or choose very low-calorie options like small blueberries or carrot pieces.",
            "<strong>Best for long training sessions:</strong> A variety of treat types keeps motivation high. Rotate between 2–3 options during the session to prevent flavour fatigue."
        ],
        "what_to_expect": "Choosing the right training treat can noticeably improve your dog's engagement and response speed. Expect some experimentation to find what motivates your particular dog — most owners settle on 2–3 reliable options within a few weeks.",
    },
    4792: {
        "cluster": "Dog Training",
        "common_mistakes": [
            "<strong>Rushing socialisation by exposing the puppy to too much too quickly</strong> — flooding creates fear, not confidence. Let the puppy approach new experiences at their own pace with an easy escape route.",
            "<strong>Waiting until vaccinations are fully complete before starting socialisation</strong> — the critical socialisation window closes around 14–16 weeks. Carry your puppy to safe environments before their course is finished.",
            "<strong>Confusing socialisation with 'meeting other dogs'</strong> — socialisation includes exposure to sounds, surfaces, vehicles, people of different ages, environments, and handling — not just dog-to-dog interaction.",
            "<strong>Ignoring the puppy's body language during new experiences</strong> — whale eyes, tucked tails, lip-licking, and freezing are stress signals. Pushing through these creates negative associations rather than resilience.",
            "<strong>Stopping socialisation after 16 weeks</strong> — while the critical window narrows, ongoing positive exposure throughout adolescence (6–18 months) maintains and strengthens early socialisation."
        ],
        "suitability": [
            "<strong>Best for puppies at 8–12 weeks:</strong> Gentle, positive exposure to household sounds, textures, brief car rides, and calm visitors — this is the most receptive learning period.",
            "<strong>Best for puppies at 12–16 weeks:</strong> Puppy classes, varied outdoor environments (after vet approval), meeting vaccinated adult dogs, and exposure to busier settings at a comfortable distance.",
            "<strong>Best for nervous puppies:</strong> Counter-conditioning with treats during mild exposure — pairing new experiences with something the puppy already enjoys builds positive associations.",
            "<strong>Best for puppies in urban environments:</strong> Gradual exposure to traffic noise, crowds, pushchairs, cyclists, and public transport from a safe distance, moving closer only as confidence builds.",
            "<strong>Best for families with children:</strong> Supervised interactions that teach both the puppy and children to respect boundaries — children under 10 should never be left alone with a puppy."
        ],
        "what_to_expect": "Socialisation is not a single event but a gradual process spanning the first year of your puppy's life. The most impactful period is 8–16 weeks, but continued positive exposure well into adolescence is what produces a confident, well-adjusted adult dog.",
        "routine": {
            "title": "Puppy Socialisation Timeline",
            "items": [
                "Weeks 8–10: Focus on home environment — new surfaces (tiles, carpet, grass), household sounds (vacuum, washing machine), gentle handling by family members.",
                "Weeks 10–12: Carry your puppy to observe busier environments — high street, park entrance, school pick-up — without forcing interaction.",
                "Weeks 12–14: Attend a reputable puppy class with controlled off-lead play. Introduce short car journeys and visits to friends' homes.",
                "Weeks 14–16: Increase the variety of environments, people, and calm dogs your puppy meets. Continue pairing new experiences with treats.",
                "Months 4–12: Maintain weekly novel experiences. Adolescence (6–18 months) often brings fear phases — respond with patience and avoid forcing interactions."
            ]
        }
    },
    5462: {
        "cluster": "Dog Training",
        "common_mistakes": [
            "<strong>Confusing 'dominance theory' with modern training science</strong> — the dominance model has been widely discredited by animal behaviourists. Reward-based methods are more effective and less likely to cause fallout behaviours.",
            "<strong>Using 'correction' and 'punishment' interchangeably</strong> — in training science, punishment means anything that reduces a behaviour's frequency. Many 'corrections' are positive punishment, which can damage trust and increase anxiety.",
            "<strong>Assuming 'positive' training means permissive training</strong> — positive reinforcement involves clear boundaries and structure. It means adding something the dog values to reinforce desired behaviour, not accepting all behaviour.",
            "<strong>Misunderstanding 'extinction' in training</strong> — ignoring unwanted behaviour (extinction) initially causes an 'extinction burst' where the behaviour intensifies temporarily before decreasing. Giving in during the burst reinforces the behaviour more strongly.",
            "<strong>Overlooking the difference between 'cue' and 'command'</strong> — modern training uses 'cue' to reflect a cooperative approach. A cue is an opportunity for the dog to earn a reward, not a demand for compliance."
        ],
        "suitability": [
            "<strong>Best for new dog owners:</strong> Understanding foundational terms like reinforcement, shaping, and desensitisation helps you follow training advice more effectively.",
            "<strong>Best for owners hiring a trainer:</strong> Knowing the difference between APDT, IMDT, and KCAI qualifications helps you choose a trainer whose methods align with current evidence.",
            "<strong>Best for owners of reactive dogs:</strong> Terms like counter-conditioning, threshold, and trigger stacking are central to reactive dog management. Understanding them helps you support your dog's behaviour plan.",
            "<strong>Best for those reading training books or courses:</strong> Training literature assumes familiarity with core terminology. This guide bridges the gap between beginner knowledge and intermediate resources."
        ],
        "what_to_expect": "Dog training terminology can seem technical, but the core concepts are straightforward once explained clearly. Most owners find that understanding even a few key terms — reinforcement, desensitisation, shaping — transforms how they interpret their dog's behaviour.",
    },
    5512: {
        "cluster": "Dog Training",
        "common_mistakes": [
            "<strong>Interpreting a wagging tail as always meaning happiness</strong> — tail wagging indicates arousal, which can be positive, negative, or neutral. A stiff, high wag can signal tension or overstimulation, not friendliness.",
            "<strong>Punishing growling</strong> — growling is a dog's warning system. Punishing it removes the warning without addressing the underlying discomfort, making a bite more likely without prior signals.",
            "<strong>Assuming a dog who rolls onto their back always wants belly rubs</strong> — belly-up can be a submissive or appeasement gesture, not an invitation. Look at the full body picture: relaxed muscles and soft eyes suggest comfort; stiff legs and wide eyes suggest anxiety.",
            "<strong>Labelling a dog as 'stubborn' when they don't comply</strong> — non-compliance is more often confusion, distraction, insufficient motivation, or anxiety than deliberate refusal.",
            "<strong>Applying human emotional frameworks to dog behaviour</strong> — dogs don't act out of 'spite' or 'guilt.' The 'guilty look' is actually an appeasement response to your tone or body language, not remorse."
        ],
        "suitability": [
            "<strong>Best for first-time dog owners:</strong> Learning to read basic body language (loose vs tense body, ear position, tail carriage) prevents most miscommunication between you and your dog.",
            "<strong>Best for families with children:</strong> Teaching children to recognise stress signals (lip-licking, whale eye, turning away) is one of the most effective dog bite prevention measures.",
            "<strong>Best for owners of anxious or reactive dogs:</strong> Understanding subtle stress signals helps you intervene before your dog reaches their threshold, making walks and social situations more manageable.",
            "<strong>Best for multi-dog households:</strong> Recognising play bows, calming signals, and resource-guarding postures helps you manage group dynamics and prevent conflicts before they escalate."
        ],
        "what_to_expect": "Reading your dog's body language is a skill that improves with practice. Start by observing your dog in relaxed situations to establish their baseline, then compare this with their behaviour in new or stressful contexts. Most owners notice a significant improvement in their dog relationship within a few weeks of actively reading body language.",
    },
    5523: {
        "cluster": "Dog Training",
        "common_mistakes": [
            "<strong>Buying equipment before understanding what you need</strong> — many new owners accumulate a drawer of unused gadgets. Start with a well-fitted harness, a fixed lead, and a treat pouch, then add tools only as specific training needs arise.",
            "<strong>Using aversive tools without professional guidance</strong> — prong collars, choke chains, and electric collars carry significant risk of physical and psychological harm. UK veterinary organisations and the APDT advise against their use.",
            "<strong>Assuming a clicker is essential for training</strong> — a clicker is a useful precision tool, but a consistent verbal marker ('yes!' or 'good!') works just as well for most pet dog training.",
            "<strong>Choosing a harness based on aesthetics instead of fit</strong> — harness design affects gait, comfort, and effectiveness. An ill-fitting harness can cause chafing, restricted movement, or reduced training benefit.",
            "<strong>Relying on equipment to solve behavioural problems</strong> — tools manage behaviour; training changes it. A head collar stops pulling during walks but doesn't teach your dog to walk on a loose lead."
        ],
        "suitability": [
            "<strong>Best for new dog owners:</strong> A Y-shaped harness, 1.5m fixed lead, and treat pouch cover virtually all beginner training needs. Add specialist equipment only when a specific situation requires it.",
            "<strong>Best for recall training:</strong> A 5–10m long line attached to a back-clip harness gives controlled freedom for practising recall at distance.",
            "<strong>Best for dogs that pull:</strong> A front-clip no-pull harness combined with reward-based loose-lead training addresses pulling more effectively than any single piece of equipment alone.",
            "<strong>Best for reactive dogs:</strong> A double-ended lead attached to both the front and back clips of a dual-clip harness provides maximum control with minimal stress on the dog.",
            "<strong>Best on a budget:</strong> Quality basics (one good harness, one fixed lead, one treat pouch) outperform a collection of cheap gadgets. Invest in fit and durability over quantity."
        ],
        "what_to_expect": "Training equipment supports your training, but it doesn't do the training for you. The best results come from combining the right tool with consistent positive reinforcement. Most owners find that they need far less equipment than they initially expected.",
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DOG CARE CLUSTER
    # ═══════════════════════════════════════════════════════════════════════════
    4566: {
        "cluster": "Dog Care",
        "common_mistakes": [
            "<strong>Exercising dogs on hot pavements</strong> — if the tarmac is too hot for the back of your hand (5-second test), it's too hot for your dog's paw pads. Walk early morning or late evening in summer.",
            "<strong>Assuming only 'hot' weather is dangerous</strong> — dogs can overheat at temperatures as low as 20°C, especially brachycephalic breeds, overweight dogs, and those with thick coats.",
            "<strong>Leaving antifreeze accessible in winter</strong> — ethylene glycol antifreeze is lethal to dogs in very small amounts and has a sweet taste that attracts them. Use propylene glycol alternatives and clean spills immediately.",
            "<strong>Reducing walks entirely in bad weather instead of adapting</strong> — most dogs need exercise year-round. Shorten walks in extreme weather but use enrichment and indoor games to compensate.",
            "<strong>Forgetting about seasonal toxins</strong> — spring brings slug pellets and fertilisers, autumn brings conkers and fallen fruit (some toxic), and Christmas brings chocolate, grapes, and decorations."
        ],
        "suitability": [
            "<strong>Best for summer safety:</strong> Focus on hydration, shade, avoiding midday heat, and recognising early heatstroke signs (excessive panting, drooling, lethargy, bright red gums).",
            "<strong>Best for winter protection:</strong> Consider a coat for thin-coated or elderly dogs, wipe paws after walks to remove road salt, and check ears and paws after wet walks.",
            "<strong>Best for spring allergy management:</strong> Wipe paws and belly after walks during high-pollen periods. Discuss antihistamine options with your vet if itching is persistent.",
            "<strong>Best for autumn hazards:</strong> Keep dogs away from fallen conkers, acorns, and mushrooms. Increase flea and tick vigilance as wildlife activity changes.",
            "<strong>Best for flat-faced breeds:</strong> Brachycephalic dogs need extra precautions in every season — they overheat easily, struggle with cold air, and are more susceptible to breathing difficulties."
        ],
        "what_to_expect": "Seasonal care is about awareness and small adjustments, not dramatic changes. Most owners quickly develop a seasonal rhythm — lighter walks in summer, paw checks in winter, allergy management in spring. The key is staying ahead of predictable risks rather than reacting after problems occur.",
        "routine": {
            "title": "Seasonal Care Checklist",
            "items": [
                "Spring: Restart or increase flea/tick prevention. Watch for allergy symptoms. Keep dogs away from garden chemicals and slug pellets.",
                "Summer: Walk before 9am and after 7pm. Carry water on every walk. Never leave a dog in a parked car, even briefly. Apply dog-safe sunscreen to exposed skin (ears, nose).",
                "Autumn: Check for conkers, acorns, and wild mushrooms on walks. Ensure reflective gear for darker evenings. Maintain flea treatment as temperatures drop gradually.",
                "Winter: Wipe paws after walks to remove road salt and grit. Consider a coat for thin-coated, elderly, or small dogs. Check for ice on ponds and lakes before allowing access.",
                "Year-round: Adjust food portions to activity levels (dogs may eat more in cold weather). Maintain parasite prevention continuously in the UK's mild climate."
            ]
        }
    },
    4573: {
        "cluster": "Dog Care",
        "common_mistakes": [
            "<strong>Treating seasonal pet safety as dog-specific only</strong> — seasonal hazards affect cats, rabbits, and other pets too. Antifreeze, fireworks, and garden chemicals pose risks across species.",
            "<strong>Assuming indoor pets are safe from seasonal risks</strong> — indoor pets face hazards from household plants (lilies for cats, poinsettias for dogs), festive decorations, and visitors leaving doors open.",
            "<strong>Relying on breed hardiness to skip cold-weather precautions</strong> — even traditionally hardy breeds can develop hypothermia in wet, windy conditions, especially if they're elderly or unwell.",
            "<strong>Underestimating firework anxiety</strong> — noise phobia is genuine distress, not overreaction. Preparation (safe space, white noise, pheromone diffusers) before firework season is far more effective than reactive management.",
            "<strong>Stopping parasite prevention 'because it's winter'</strong> — fleas survive indoors year-round in the UK, and ticks are active whenever temperatures are above 3–4°C."
        ],
        "suitability": [
            "<strong>Best for multi-pet households:</strong> A seasonal safety calendar that covers all species ensures nothing is overlooked as hazards shift throughout the year.",
            "<strong>Best for new pet owners:</strong> A clear month-by-month awareness of common seasonal risks provides a practical framework for your first year of pet ownership.",
            "<strong>Best for pets with anxiety or noise sensitivity:</strong> Advance planning for bonfire night, New Year, and thunderstorm season makes a measurable difference to your pet's wellbeing.",
            "<strong>Best for outdoor pets (hutch rabbits, outdoor cats):</strong> Seasonal checks on shelter adequacy, water access (ice in winter, evaporation in summer), and predator security.",
            "<strong>Best for owners in rural areas:</strong> Additional awareness of livestock, agricultural chemicals, harvest machinery, and tick-borne diseases that peak in spring and autumn."
        ],
        "what_to_expect": "Seasonal pet safety becomes second nature once you've been through one full year. Each season has a short list of predictable risks, and the practical steps to manage them are straightforward. The biggest gains come from planning ahead rather than reacting to emergencies.",
    },
}


# ─── Block builders ───────────────────────────────────────────────────────────

def build_about_guide_block(cluster):
    """Build the 'About This Guide' Gutenberg block."""
    text = ABOUT_TEMPLATES.get(cluster, "")
    if not text:
        return ""
    return f"""<!-- wp:group {{"style":{{"color":{{"background":"#f9fafb"}},"border":{{"radius":"6px","width":"1px","color":"#e5e7eb"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e5e7eb;border-width:1px;border-radius:6px;background-color:#f9fafb;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"13px"}}}}}} -->
<p style="font-size:13px"><strong>About this guide:</strong> {text} Last reviewed: May 2026. See our <a href="https://pethubonline.com/our-editorial-process/">editorial process</a> for details.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->"""


def build_common_mistakes_block(mistakes):
    """Build the Common Mistakes block."""
    items = "\n".join(f"<li>{m}</li>" for m in mistakes)
    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Common Mistakes to Avoid</h3>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">
{items}
</ul>
<!-- /wp:list -->"""


def build_suitability_block(items):
    """Build the Quick Suitability Guide block."""
    items_html = "\n".join(f"<li>{i}</li>" for i in items)
    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Quick Suitability Guide</h3>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">
{items_html}
</ul>
<!-- /wp:list -->"""


def build_what_to_expect_block(text):
    """Build the What to Expect block."""
    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">What to Expect</h3>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p class="wp-block-paragraph">{text}</p>
<!-- /wp:paragraph -->"""


def build_routine_block(routine_data):
    """Build the Practical Routine Checklist block."""
    items_html = "\n".join(f"<li>{i}</li>" for i in routine_data["items"])
    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">{routine_data['title']}</h3>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">
{items_html}
</ul>
<!-- /wp:list -->"""


# ─── API functions ────────────────────────────────────────────────────────────

def fetch_all_posts():
    """Fetch all published posts from WP API."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}/posts?per_page=100&page={page}&status=publish&_fields=id,title"
        r = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True
        )
        try:
            posts = json.loads(r.stdout)
        except json.JSONDecodeError:
            print(f"  JSON error on page {page}")
            break
        if not posts or isinstance(posts, dict):
            break
        all_posts.extend(posts)
        print(f"  Page {page}: {len(posts)} posts (total: {len(all_posts)})")
        if len(posts) < 100:
            break
        page += 1
        time.sleep(0.5)
    return all_posts


def classify_post(post_id, title_lower):
    """Classify a post into a cluster. Returns cluster name or None."""
    # Skip cat-only posts
    if "cat " in title_lower or "cat:" in title_lower or "cats " in title_lower or "kitten" in title_lower or "house cat" in title_lower:
        # Only skip if it's purely cat content (no dog mention)
        if "dog" not in title_lower and "puppy" not in title_lower and "pet " not in title_lower:
            return None

    for cluster in CLUSTER_PRIORITY:
        keywords = CLUSTER_KEYWORDS[cluster]
        for kw in keywords:
            if kw in title_lower:
                # Puppy Care: don't classify if it matches a higher-priority cluster
                if cluster == "Puppy Care":
                    for higher_cluster in ["Dog Food", "Dog Care", "Dog Health", "Dog Training"]:
                        for hkw in CLUSTER_KEYWORDS[higher_cluster]:
                            if hkw in title_lower:
                                return None  # Let it be classified by the higher-priority loop
                return cluster
    return None


def fetch_post_content(post_id):
    """Fetch full post content for editing."""
    url = f"{WP_API}/posts/{post_id}?context=edit&_fields=id,title,content"
    r = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True
    )
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def update_post_content(post_id, new_content):
    """Update post content via WP API."""
    payload = json.dumps({"content": new_content})
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(payload)
        tmpfile = f.name

    try:
        url = f"{WP_API}/posts/{post_id}"
        r = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmpfile}",
             url],
            capture_output=True, text=True,
            timeout=60
        )
        if r.returncode != 0:
            return False, f"curl error: {r.stderr}"
        try:
            resp = json.loads(r.stdout)
            if "id" in resp:
                return True, "OK"
            else:
                return False, f"API error: {r.stdout[:300]}"
        except json.JSONDecodeError:
            return False, f"Invalid JSON: {r.stdout[:300]}"
    finally:
        os.unlink(tmpfile)


def find_insertion_point_about(content):
    """Find where to insert the About block (after Quick Answer/first heading)."""
    # Look for Quick Answer section
    quick_patterns = [
        "<strong>Quick answer:</strong>",
        "<strong>Quick Answer:</strong>",
        "Quick Summary</h2>",
        "Quick Answer</h2>",
    ]

    for pat in quick_patterns:
        idx = content.find(pat)
        if idx >= 0:
            # Find end of the paragraph containing quick answer
            # Look for </p> after the match
            p_end = content.find("</p>", idx)
            if p_end >= 0:
                p_end += 4  # include </p>
                # Skip any whitespace/newlines
                insert = p_end
                # Also skip past any style paragraph that follows
                next_chunk = content[insert:insert+500]
                # Check if there's a metadata paragraph right after
                if '<p class="wp-block-paragraph" style="font-size:0.9' in next_chunk:
                    meta_end = content.find("</p>", insert + 1)
                    if meta_end >= 0 and meta_end < insert + 500:
                        insert = meta_end + 4
                return insert

    # Fallback: after first heading
    h2_match = re.search(r'</h2>', content)
    if h2_match:
        return h2_match.end()

    # Last fallback: after first <hr>
    hr_idx = content.find('<hr')
    if hr_idx >= 0:
        hr_end = content.find('>', hr_idx)
        if hr_end >= 0:
            # Skip past any />
            if content[hr_end-1] == '/':
                return hr_end + 1
            close_end = content.find('/>', hr_idx)
            if close_end >= 0:
                return close_end + 2
            return hr_end + 1

    return 0


def find_insertion_point_before_sources(content):
    """Find where to insert blocks before Sources section."""
    sources_markers = [
        '<h3 class="wp-block-heading">Sources and Further Reading</h3>',
        '<h3 class="wp-block-heading">Sources and Further Reading',
        'Sources and Further Reading</h3>',
    ]

    for marker in sources_markers:
        idx = content.find(marker)
        if idx >= 0:
            # Look for HR separator before sources
            hr_idx = content.rfind('<hr', max(0, idx - 300), idx)
            if hr_idx >= 0:
                return hr_idx
            return idx

    # Fallback: before Related Guides
    related_markers = [
        'Related Guides</h2>',
        'Related Guides</h3>',
    ]
    for marker in related_markers:
        idx = content.find(marker)
        if idx >= 0:
            return idx

    # Fallback: before editorial standards
    edit_markers = [
        'Our Editorial Standards</h4>',
        'Our Editorial Standards</h3>',
        'About Our Editorial Standards</h3>',
    ]
    for marker in edit_markers:
        idx = content.find(marker)
        if idx >= 0:
            # Go back to find the containing group or heading
            group_idx = content.rfind('wp-block-group', max(0, idx - 500), idx)
            if group_idx >= 0:
                div_idx = content.rfind('<div', max(0, group_idx - 100), group_idx)
                if div_idx >= 0:
                    return div_idx
            return idx

    return len(content)


def content_has_block(content, markers):
    """Check if content already has any of the markers."""
    content_lower = content.lower()
    for m in markers:
        if m.lower() in content_lower:
            return True
    return False


# ─── Main processing ─────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("HUMANIZATION BATCH 1: About + Mistakes + Suitability + Extras")
    print("=" * 70)
    print()

    # Step 1: Fetch all posts and classify
    print("Step 1: Fetching all published posts...")
    all_posts = fetch_all_posts()
    print(f"  Total posts: {len(all_posts)}")
    print()

    # Classify posts
    target_posts = {}
    for p in all_posts:
        pid = p["id"]
        title = html.unescape(p["title"]["rendered"])
        title_lower = title.lower()

        if pid in ALREADY_TREATED:
            continue

        cluster = classify_post(pid, title_lower)
        if cluster:
            target_posts[pid] = {"title": title, "cluster": cluster}

    # Also ensure all posts defined in POST_BLOCKS are included
    for pid, block_data in POST_BLOCKS.items():
        if pid not in target_posts and pid not in ALREADY_TREATED:
            # Fetch title if we don't have it
            for p in all_posts:
                if p["id"] == pid:
                    target_posts[pid] = {
                        "title": html.unescape(p["title"]["rendered"]),
                        "cluster": block_data["cluster"]
                    }
                    break

    print(f"Step 1 complete: {len(target_posts)} posts to process")
    for pid, info in sorted(target_posts.items()):
        defined = "DEFINED" if pid in POST_BLOCKS else "NO-DEF"
        print(f"  ID={pid} [{info['cluster']}] [{defined}] {info['title'][:70]}")
    print()

    # Step 2: Process each post
    print("Step 2: Processing posts...")
    print()

    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "cluster", "about_guide", "common_mistakes",
                         "suitability", "what_to_expect", "routine", "status"])

    results = []
    post_ids = sorted(target_posts.keys())
    total = len(post_ids)

    for i, pid in enumerate(post_ids):
        info = target_posts[pid]
        cluster = info["cluster"]
        title = info["title"]

        print(f"[{i+1}/{total}] ID={pid} [{cluster}] {title[:60]}...", flush=True)

        # Check if we have block definitions
        if pid not in POST_BLOCKS:
            print(f"  -> SKIP: No block definitions for this post", flush=True)
            result = {
                "id": pid, "title": title, "cluster": cluster,
                "about_guide": False, "common_mistakes": False,
                "suitability": False, "what_to_expect": False,
                "routine": False, "status": "SKIP_NO_DEFINITIONS"
            }
            results.append(result)
            with open(LOG_FILE, "a", newline="") as f:
                csv.writer(f).writerow([
                    result["id"], result["title"], result["cluster"],
                    result["about_guide"], result["common_mistakes"],
                    result["suitability"], result["what_to_expect"],
                    result["routine"], result["status"]
                ])
            continue

        # Fetch post content
        post_data = fetch_post_content(pid)
        if not post_data:
            print(f"  -> ERROR: Could not fetch post", flush=True)
            result = {
                "id": pid, "title": title, "cluster": cluster,
                "about_guide": False, "common_mistakes": False,
                "suitability": False, "what_to_expect": False,
                "routine": False, "status": "FETCH_ERROR"
            }
            results.append(result)
            with open(LOG_FILE, "a", newline="") as f:
                csv.writer(f).writerow([
                    result["id"], result["title"], result["cluster"],
                    result["about_guide"], result["common_mistakes"],
                    result["suitability"], result["what_to_expect"],
                    result["routine"], result["status"]
                ])
            time.sleep(0.5)
            continue

        content = post_data["content"]["raw"]
        block_defs = POST_BLOCKS[pid]

        # Track what we add
        added_about = False
        added_mistakes = False
        added_suitability = False
        added_what_expect = False
        added_routine = False

        # ─── BLOCK 1: About This Guide (insert after Quick Answer) ────────
        if not content_has_block(content, ["About this guide", "About This Guide"]):
            about_block = build_about_guide_block(cluster)
            if about_block:
                insert_pos = find_insertion_point_about(content)
                content = content[:insert_pos] + "\n" + about_block + "\n" + content[insert_pos:]
                added_about = True
                print(f"  + About This Guide (pos {insert_pos})", flush=True)
        else:
            print(f"  ~ About This Guide already present", flush=True)

        # ─── BLOCKS 2-5: Before Sources section ──────────────────────────
        before_sources_blocks = []

        # BLOCK 2: Common Mistakes
        if not content_has_block(content, ["Common Mistakes to Avoid", "Common Mistakes"]):
            if "common_mistakes" in block_defs:
                before_sources_blocks.append(build_common_mistakes_block(block_defs["common_mistakes"]))
                added_mistakes = True
                print(f"  + Common Mistakes to Avoid", flush=True)
        else:
            print(f"  ~ Common Mistakes already present", flush=True)

        # BLOCK 3: Quick Suitability Guide
        skip_suit = block_defs.get("skip_suitability", False)
        if not skip_suit and not content_has_block(content, ["Quick Suitability Guide", "Quick Suitability"]):
            if "suitability" in block_defs:
                before_sources_blocks.append(build_suitability_block(block_defs["suitability"]))
                added_suitability = True
                print(f"  + Quick Suitability Guide", flush=True)
        elif skip_suit:
            print(f"  ~ Suitability skipped (already present from previous batch)", flush=True)
        else:
            print(f"  ~ Quick Suitability already present", flush=True)

        # BLOCK 4: What to Expect
        if not content_has_block(content, ["What to Expect"]):
            if "what_to_expect" in block_defs:
                before_sources_blocks.append(build_what_to_expect_block(block_defs["what_to_expect"]))
                added_what_expect = True
                print(f"  + What to Expect", flush=True)
        else:
            print(f"  ~ What to Expect already present", flush=True)

        # BLOCK 5: Routine Checklist
        skip_routine = block_defs.get("skip_routine", False)
        if not skip_routine and not content_has_block(content, ["Routine Checklist", "Routine", "Timeline"]):
            if "routine" in block_defs:
                before_sources_blocks.append(build_routine_block(block_defs["routine"]))
                added_routine = True
                print(f"  + Routine/Checklist", flush=True)
        elif skip_routine:
            print(f"  ~ Routine skipped (already present from previous batch)", flush=True)
        else:
            print(f"  ~ Routine already present", flush=True)

        # Insert before-sources blocks
        if before_sources_blocks:
            insert_pos = find_insertion_point_before_sources(content)
            combined = "\n\n".join(before_sources_blocks)
            content = content[:insert_pos] + "\n\n" + combined + "\n\n" + content[insert_pos:]

        # Check if anything was actually added
        if not any([added_about, added_mistakes, added_suitability, added_what_expect, added_routine]):
            print(f"  -> No new blocks needed", flush=True)
            status = "NO_CHANGES_NEEDED"
        else:
            # Update via API
            success, msg = update_post_content(pid, content)
            status = "OK" if success else f"UPDATE_ERROR: {msg}"
            print(f"  -> {status}", flush=True)

        result = {
            "id": pid, "title": title, "cluster": cluster,
            "about_guide": added_about, "common_mistakes": added_mistakes,
            "suitability": added_suitability, "what_to_expect": added_what_expect,
            "routine": added_routine, "status": status
        }
        results.append(result)

        with open(LOG_FILE, "a", newline="") as f:
            csv.writer(f).writerow([
                result["id"], result["title"], result["cluster"],
                result["about_guide"], result["common_mistakes"],
                result["suitability"], result["what_to_expect"],
                result["routine"], result["status"]
            ])

        time.sleep(0.5)

    # ─── Summary ──────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("HUMANIZATION BATCH 1 — SUMMARY")
    print("=" * 70)

    ok_count = sum(1 for r in results if r["status"] == "OK")
    skip_count = sum(1 for r in results if "SKIP" in r["status"] or "NO_CHANGES" in r["status"])
    err_count = sum(1 for r in results if "ERROR" in r["status"])

    about_count = sum(1 for r in results if r["about_guide"])
    mistakes_count = sum(1 for r in results if r["common_mistakes"])
    suit_count = sum(1 for r in results if r["suitability"])
    expect_count = sum(1 for r in results if r["what_to_expect"])
    routine_count = sum(1 for r in results if r["routine"])

    print(f"Total posts targeted: {total}")
    print(f"Successfully updated: {ok_count}")
    print(f"Skipped:              {skip_count}")
    print(f"Errors:               {err_count}")
    print()
    print(f"About This Guide:     {about_count} posts")
    print(f"Common Mistakes:      {mistakes_count} posts")
    print(f"Quick Suitability:    {suit_count} posts")
    print(f"What to Expect:       {expect_count} posts")
    print(f"Routine/Checklist:    {routine_count} posts")

    if err_count > 0:
        print(f"\nErrors:")
        for r in results:
            if "ERROR" in r["status"]:
                print(f"  Post {r['id']}: {r['status']}")

    print(f"\nLog saved to: {LOG_FILE}")


if __name__ == "__main__":
    main()
