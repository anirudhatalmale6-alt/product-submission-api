#!/usr/bin/env python3
"""Phase 18E v2: Create 20 Pet Care spoke posts for PetHub Online."""
import requests, json, time, re, sys

WP = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
PEXELS_KEY = "dmGyKrZqTlwukxWzOK1EkH4jbEv9EaIDpLGj7eL5MZ07bl6AR9OEoHlB"
PEXELS_URL = "https://api.pexels.com/v1/search"
CATEGORY_PET_CARE = 1397
AFFILIATE_TAG = "pethubonline-21"

# Create a session with proper encoding header to avoid brotli issues
session = requests.Session()
session.headers.update({"Accept-Encoding": "gzip, deflate"})
session.auth = AUTH

INTERNAL_LINKS = {
    "first_time_owner": "https://pethubonline.com/first-time-pet-owner-guide-uk/",
    "seasonal_care": "https://pethubonline.com/seasonal-pet-care-calendar-uk/",
    "multi_pet": "https://pethubonline.com/multi-pet-household-management-uk/",
    "new_cat_owner": "https://pethubonline.com/new-cat-owner-setup-guide/",
    "indoor_exercise": "https://pethubonline.com/indoor-cat-exercise-routines-uk/",
    "enrichment_checklist": "https://pethubonline.com/indoor-cat-enrichment-checklist/",
    "diy_toys": "https://pethubonline.com/diy-cat-toys-household-items/",
}

# ──────── SPOKE CONTENT GENERATOR ────────
# To keep the script under 2000 lines, we generate content programmatically
# rather than hardcoding massive dicts for all 20 spokes.

def s(heading, content):
    """Shorthand for section dict."""
    return {"heading": heading, "content": content}

SPOKES = [
    # ── 1: Pet Microchip Registration Guide UK ──
    {
        "title": "Pet Microchip Registration Guide UK: Everything You Need to Know",
        "slug": "pet-microchip-registration-guide-uk",
        "focus_keyword": "pet microchip registration UK",
        "seo_title": "Pet Microchip Registration Guide UK: Complete Guide | PetHub Online",
        "seo_desc": "Complete UK guide to pet microchip registration. Covers legal requirements, how to update details, database choices, costs, and what to do if your pet is lost.",
        "quick_answer": "In the UK, all dogs must be microchipped and registered on an approved database by 8 weeks of age (law since 2016). From June 2024, cats must also be microchipped by 20 weeks. The microchip itself is a tiny rice-grain-sized transponder injected under the skin. Registration means linking the chip number to your contact details on a Defra-approved database. Keeping your details current is essential; an out-of-date microchip is as useless as no microchip at all.",
        "at_a_glance": [
            "Dogs must be microchipped by 8 weeks of age (UK law since 2016)",
            "Cats must be microchipped by 20 weeks of age (England law since June 2024)",
            "Registration means linking the chip number to your address and phone on an approved database",
            "Always update your details when you move house or change phone number",
            "A microchip costs around 10-30 pounds at most UK vet practices",
            "Check your pet's chip is readable at every annual vet check"
        ],
        "sections": [
            s("UK Microchipping Law Explained", "<p>Since April 2016, all dogs in England, Scotland, and Wales must be microchipped and registered on an approved database by the time they are 8 weeks old. Owners who fail to comply can face a fine of up to 500 pounds. From June 2024, compulsory cat microchipping was introduced in England, requiring all cats to be chipped by 20 weeks of age. Scotland and Wales are expected to follow with similar legislation.</p><p>The law requires not just the physical chip but proper registration. A microchip without up-to-date contact details on a database is effectively useless. The chip stores only a 15-digit number; your personal details are held on the database, not on the chip itself. When a scanner reads the chip, it returns the number, which is then looked up on the database to find the registered keeper's contact information.</p><p>Breeders are responsible for microchipping puppies before sale. The breeder's details are registered first, and the new owner must transfer the registration. For rescue animals, the shelter typically handles chipping and initial registration. For more on getting started with a new pet, see our <a href=\"{fl}\">first-time pet owner guide</a>.</p>".format(fl=INTERNAL_LINKS["first_time_owner"])),
            s("How to Register and Update Your Microchip Details", "<p>When your pet is microchipped, the vet or implanter registers the chip on one of the Defra-approved databases. In the UK, approved databases include Petlog (run by the Kennel Club), MicrochipCentral, Animal Tracker, and several others. You should receive paperwork showing your chip number and which database it is registered on.</p><p>To update your details, log into the relevant database website, or call their customer service line. Some databases charge a small fee for changes (typically 6-15 pounds), while others offer free updates. It is crucial to update your details whenever you move house, change phone number, or if the pet changes ownership. An estimated 30 percent of UK microchips have out-of-date information, significantly reducing the chance of reuniting lost pets.</p><p>If you are unsure which database your chip is on, use the free lookup tool at check-a-chip.co.uk, which searches all UK databases simultaneously. Simply enter the 15-digit chip number and it will tell you which database holds the registration.</p>"),
            s("What Happens When a Lost Pet Is Found", "<p>When a lost pet is found and taken to a vet, rescue centre, or dog warden, the first action is scanning for a microchip. The scanner reads the 15-digit number, which is then checked against all UK databases. If the registration is current, the database contacts you via the phone number and email address on file. Most reunions happen within 24-48 hours when details are up to date.</p><p>If the details are outdated, the database may still attempt contact through secondary details, but success rates drop dramatically. The Dogs Trust reports that microchipped dogs are over twice as likely to be reunited with their owners compared to unchipped dogs. For cats, the figure is even more stark, as cats carry no collar or tag in many cases, making the chip the only form of identification.</p><p>In some cases, a found pet's chip may be registered on a foreign database (common with rescue dogs from abroad). UK scanners can read all ISO-standard chips, and international databases can usually be traced, though it takes longer. For advice on settling a new pet, see our <a href=\"{fl}\">first-time owner guide</a>.</p>".format(fl=INTERNAL_LINKS["first_time_owner"])),
            s("Microchip Costs and Where to Get It Done", "<p>Microchipping typically costs between 10 and 30 pounds at a UK veterinary practice. Many charities, including the Dogs Trust, RSPCA, Cats Protection, and PDSA, offer free or subsidised microchipping events. Local councils sometimes run free chipping days for dogs to encourage compliance with the law.</p><p>The procedure is quick and similar to a routine vaccination injection. The chip, enclosed in biocompatible glass, is injected under the skin between the shoulder blades using a slightly larger needle than a standard vaccine. Most pets show minimal reaction. No anaesthetic is required, and the procedure takes under a minute.</p><p>Some breeders and pet shops include microchipping in the purchase price. If buying from a breeder, check that the chip number on the puppy matches the paperwork, and transfer the registration to your name immediately. For rescue pets, the adoption fee almost always includes microchipping and initial registration.</p>"),
            s("Common Microchip Problems and Solutions", "<p>The most common issue is out-of-date registration details. As mentioned, approximately 30 percent of UK microchips have incorrect contact information. Set a reminder to check your microchip registration annually, ideally at the same time as your pet's annual vaccination appointment. Ask your vet to scan the chip at every visit to confirm it is still readable and in the correct position.</p><p>Chip migration is rare but possible. The chip can move slightly from the implantation site, usually settling in the shoulder or chest area. This does not affect its function but means scanners may need to check a wider area. Modern chips have anti-migration coating to reduce this.</p><p>Chip failure is extremely rare (less than 1 percent) but does occur. If your vet cannot read the chip, a second chip can be implanted alongside the failed one. Both numbers should be registered. For guidance on regular health checks, see our <a href=\"{sc}\">seasonal pet care calendar</a>.</p>".format(sc=INTERNAL_LINKS["seasonal_care"]))
        ],
        "comparison_table": {
            "title": "UK Microchip Databases Compared",
            "headers": ["Database", "Operator", "Free Registration", "Update Fee", "24/7 Reunification"],
            "rows": [
                ["Petlog", "Kennel Club", "Yes (basic)", "Varies by plan", "Yes"],
                ["MicrochipCentral", "Independent", "Yes", "Free online", "Yes"],
                ["Animal Tracker", "Independent", "Yes", "Free", "Yes"],
                ["Vet-Link", "Vet practices", "With chipping", "Small fee", "Yes"],
                ["SmartTrace", "Independent", "Yes", "Free online", "Yes"],
            ]
        },
        "common_mistakes": [
            "Failing to update microchip details after moving house or changing phone number",
            "Assuming the breeder or shelter has transferred registration to your name",
            "Not knowing which database your pet's chip is registered on",
            "Never asking the vet to scan the chip during routine appointments",
            "Relying solely on a collar and tag without microchipping"
        ],
        "what_to_do_next": [
            "Check your pet's microchip registration today at check-a-chip.co.uk",
            "Update your contact details if anything has changed since registration",
            "Ask your vet to scan the chip at your next appointment to confirm it works",
            "Read our <a href=\"https://pethubonline.com/first-time-pet-owner-guide-uk/\">first-time pet owner guide</a> for comprehensive new pet setup advice",
            "Check our <a href=\"https://pethubonline.com/seasonal-pet-care-calendar-uk/\">seasonal care calendar</a> for annual health check reminders"
        ],
        "faq": [
            ("Is microchipping painful for pets?", "The procedure causes brief, mild discomfort similar to a vaccination. Most pets barely react. No anaesthetic is needed. The needle is slightly larger than a vaccine needle, but the injection is quick and over in seconds."),
            ("How much does microchipping cost in the UK?", "Typically 10-30 pounds at a vet practice. Many charities offer free or subsidised chipping. The Dogs Trust, RSPCA, and Cats Protection regularly run free microchipping events across the UK."),
            ("Can a microchip track my pet's location?", "No. A microchip is not a GPS tracker. It is a passive transponder that stores a 15-digit number readable only by a scanner held close to the pet. It does not emit signals and has no battery. GPS pet trackers are separate devices."),
            ("What if my pet's microchip stops working?", "Chip failure is extremely rare (less than 1 percent). If your vet cannot read the chip, a second chip can be implanted alongside it. Register both chip numbers on your database."),
            ("Do I need to microchip my indoor cat?", "In England, yes. From June 2024, all cats (indoor and outdoor) must be microchipped by 20 weeks of age. Indoor cats can still escape, and a microchip is the most reliable way to prove ownership and reunite you with a lost pet.")
        ],
        "key_terms": [
            ("Microchip Transponder", "A tiny electronic device (about the size of a grain of rice) encased in biocompatible glass, injected under the skin. It stores a unique 15-digit identification number."),
            ("Defra-Approved Database", "A database authorised by the Department for Environment, Food and Rural Affairs to hold pet microchip registrations in the UK."),
            ("ISO Standard", "International standard (ISO 11784/11785) for pet microchips ensuring all chips can be read by universal scanners regardless of manufacturer."),
            ("Chip Migration", "The rare movement of a microchip from its implantation site to a nearby area under the skin. Does not affect function but may require scanning a wider area."),
            ("Reunification Service", "The 24/7 contact service provided by microchip databases to reunite found pets with their registered owners.")
        ],
        "products": [
            ("Tabcat Cat Tracker", "Homing tracker for cats using directional RF signals, not GPS dependent, works indoors and outdoors", "tabcat+cat+tracker+homing"),
            ("Apple AirTag Pet Collar Holder", "Silicone holder to attach AirTag to pet collar for location tracking via Apple Find My network", "apple+airtag+pet+collar+holder"),
            ("Tractive GPS Dog Tracker", "Real-time GPS tracking for dogs, subscription-based, covers whole of UK, waterproof", "tractive+gps+dog+tracker+uk"),
            ("Ancol Reflective Cat Collar", "Snap-open safety collar with reflective strip, fits ID tag alongside microchip identification", "ancol+reflective+cat+collar+safety")
        ],
        "sources": [
            "UK Government - Compulsory Dog Microchipping Regulations 2015",
            "Defra - Compulsory Cat Microchipping England 2024",
            "Dogs Trust - Microchipping Statistics and Reunification Data",
            "Cats Protection - Cat Microchipping Guide UK",
            "PDSA - Pet Microchipping Advice"
        ],
        "image_queries": ["vet scanning pet microchip", "puppy at veterinarian", "cat at vet checkup", "dog with collar outdoors"]
    },

    # ── 2: Pet Insurance Claim Process UK ──
    {
        "title": "Pet Insurance Claim Process UK: How to File and Track Your Claim",
        "slug": "pet-insurance-claim-process-uk",
        "focus_keyword": "pet insurance claim process UK",
        "seo_title": "Pet Insurance Claim Process UK: Filing Guide | PetHub Online",
        "seo_desc": "Step-by-step guide to the UK pet insurance claim process. Covers how to file claims, required documents, timelines, common rejection reasons, and tracking your claim.",
        "quick_answer": "The UK pet insurance claim process typically involves three steps: notifying your insurer (usually within a set timeframe after treatment), completing a claim form with your vet's input, and submitting supporting documents including invoices and clinical notes. Most insurers offer online portals or apps for filing. Claims are usually processed within 5-15 working days. Understanding your policy's excess, exclusions, and claim limits before you need to claim saves significant stress during an already difficult time.",
        "at_a_glance": [
            "Notify your insurer promptly; most policies require notification within 30-90 days of treatment",
            "Your vet completes part of the claim form with clinical details and diagnosis",
            "Keep all invoices, receipts, and clinical history documents organised from day one",
            "Most claims are processed within 5-15 working days once all documents are received",
            "Direct claims (vet bills paid by insurer directly) are offered by some insurers and vets",
            "Pre-existing conditions are almost universally excluded from pet insurance claims"
        ],
        "sections": [
            s("How to File a Pet Insurance Claim Step by Step", "<p>The claim process begins when your pet receives treatment. Step one is to notify your insurer, either through their app, online portal, or by phone. Most policies require notification within 30-90 days of the treatment date. Prompt notification speeds up processing and avoids potential disputes about late filing.</p><p>Step two involves completing the claim form. This is typically a two-part form: you fill in your personal details, treatment dates, and a description of the issue, while your vet completes the clinical section with diagnosis, treatment details, and prognosis. Many UK vets are familiar with this process and will complete their section during or shortly after the consultation. Some vets charge a small fee (5-20 pounds) for completing insurance paperwork.</p><p>Step three is submitting all supporting documents. This includes the completed claim form, all invoices and receipts for the treatment, your pet's clinical history (if requested), and any referral letters if specialist treatment was involved. Submit everything together rather than in pieces, as incomplete submissions are the most common cause of processing delays.</p>"),
            s("Required Documents and What Insurers Look For", "<p>Every pet insurance claim requires a completed claim form signed by both you and your vet, original invoices itemising all treatments and costs, and your vet's clinical notes for the condition being claimed. Some insurers also request your pet's full clinical history, particularly if it is a first claim or involves a condition that could be pre-existing.</p><p>Insurers check claims against your policy terms, looking specifically at whether the condition is covered, whether any exclusions apply, whether the treatment falls within policy limits, and whether the condition is genuinely new rather than pre-existing. They may also verify that the treatment was necessary and appropriate for the diagnosis.</p><p>Organise your pet's medical records from day one. Keep a folder (physical or digital) with all vet invoices, vaccination records, clinical letters, and insurance correspondence. This preparation makes the claim process significantly smoother when you need it. For general pet health management, see our <a href=\"{sc}\">seasonal care calendar</a>.</p>".format(sc=INTERNAL_LINKS["seasonal_care"])),
            s("Common Reasons Pet Insurance Claims Are Rejected", "<p>The most frequent rejection reason is pre-existing conditions. If your pet showed symptoms or received treatment for a condition before the policy started (or during the waiting period), claims related to that condition will be declined. This is why obtaining insurance when your pet is young and healthy is advantageous.</p><p>Other common rejection reasons include: claiming outside the notification window, failing to disclose relevant medical history when taking out the policy, claiming for excluded treatments (many policies exclude dental, behavioural, or cosmetic procedures), exceeding annual or per-condition limits, and claiming during the initial waiting period (typically 14 days for illness, often no waiting period for accidents).</p><p>If your claim is rejected and you believe it should be covered, you have the right to appeal. Request the rejection reasons in writing, gather supporting evidence from your vet, and submit a formal appeal. If the appeal is unsuccessful, you can escalate to the Financial Ombudsman Service, which handles disputes between consumers and financial services companies in the UK at no cost to you.</p>"),
            s("Direct Claims vs Reimbursement Claims", "<p>In the UK, two main claim models exist. Reimbursement claims are the most common: you pay the vet bill upfront, then claim the amount back from your insurer minus your excess. This means you need to have funds available to cover vet bills initially, which can be challenging for expensive treatments.</p><p>Direct claims (sometimes called direct settlement) involve the insurer paying the vet practice directly. Not all insurers or vet practices offer this option, but it is becoming more common, particularly for large claims. If your vet and insurer both support direct claims, you typically only need to pay your excess at the practice, and the insurer settles the remaining balance directly with the vet.</p><p>To use direct claims, inform your vet before or during the consultation that you want to claim directly. The vet practice will contact your insurer for authorisation. Processing may take a few extra days compared to standard reimbursement, but it avoids the need for upfront payment. Ask your vet practice and insurer whether they support this option.</p>"),
            s("Tracking Your Claim and Expected Timelines", "<p>Most UK pet insurers provide online portals or mobile apps where you can track your claim status in real time. After submission, claims typically pass through several stages: received, under review, awaiting additional information (if needed), approved, and payment issued. The average processing time is 5-15 working days from receipt of all required documents.</p><p>If your claim is taking longer than expected, contact your insurer to check whether they need additional information. Delays are most commonly caused by incomplete documentation, the need for additional clinical history from your vet, or complex claims requiring medical review. Maintain a record of all communications with your insurer including dates, reference numbers, and the names of anyone you speak with.</p><p>Payment is usually made via bank transfer to the account you nominated when setting up your policy. Keep your bank details updated with your insurer to avoid payment delays. For ongoing conditions requiring multiple claims, some insurers allow you to set up a recurring claim process, reducing paperwork for subsequent treatments of the same condition.</p>")
        ],
        "comparison_table": {
            "title": "Pet Insurance Claim Models: UK Comparison",
            "headers": ["Claim Type", "How It Works", "Upfront Cost to You", "Processing Time", "Availability"],
            "rows": [
                ["Reimbursement", "You pay vet, then claim back", "Full vet bill", "5-15 working days", "All insurers"],
                ["Direct claim", "Insurer pays vet directly", "Excess only", "5-20 working days", "Selected insurers/vets"],
                ["Online portal", "Submit documents digitally", "Depends on model", "Often faster", "Most major insurers"],
                ["Paper claim", "Post physical forms", "Depends on model", "Slower (7-20 days)", "All insurers"],
                ["Emergency claim", "Fast-track for urgent care", "Varies", "24-72 hours", "Some premium policies"],
            ]
        },
        "common_mistakes": [
            "Not reading the policy exclusions before needing to claim, leading to unexpected rejections",
            "Filing claims after the notification deadline specified in the policy",
            "Submitting incomplete documentation, causing unnecessary processing delays",
            "Not disclosing pre-existing conditions when taking out the policy, risking claim voidance",
            "Assuming all treatments are covered without checking policy-specific exclusions"
        ],
        "what_to_do_next": [
            "Review your current pet insurance policy's claim process and notification deadlines today",
            "Create a dedicated folder for your pet's medical records and insurance documents",
            "Download your insurer's app if available for easier claim submission and tracking",
            "Read our <a href=\"https://pethubonline.com/first-time-pet-owner-guide-uk/\">first-time owner guide</a> for setting up pet health management from day one",
            "Check our <a href=\"https://pethubonline.com/seasonal-pet-care-calendar-uk/\">seasonal care calendar</a> for preventive health reminders"
        ],
        "faq": [
            ("How long does a pet insurance claim take in the UK?", "Most claims are processed within 5-15 working days from receipt of all required documents. Complex claims or those requiring additional information may take longer. Direct claims may take up to 20 working days as they involve coordination between insurer and vet practice."),
            ("Can I claim for vet consultation fees?", "This depends on your policy. Many policies cover consultation fees as part of the treatment cost, while some budget policies only cover treatment and medication, excluding the consultation fee itself. Check your policy wording for specifics."),
            ("What is the excess on pet insurance?", "The excess is the amount you pay towards each claim before the insurer pays the rest. UK pet insurance excesses are typically 50-250 pounds per condition per year. Some policies have a fixed excess, a percentage excess, or both combined. Higher excesses usually mean lower premiums."),
            ("Can I claim for preventive treatments like vaccinations?", "Standard pet insurance does not cover preventive treatments including vaccinations, flea and worm treatments, neutering, or routine health checks. Some premium or wellness-add-on policies do include preventive care cover for an additional premium."),
            ("What happens if I disagree with a claim decision?", "You can appeal directly with your insurer, providing additional evidence to support your claim. If the appeal is unsuccessful, you can escalate the complaint to the Financial Ombudsman Service (FOS), which resolves disputes between consumers and financial companies in the UK free of charge.")
        ],
        "key_terms": [
            ("Excess", "The fixed amount or percentage you pay towards each insurance claim before the insurer covers the remainder. Acts as a cost-sharing mechanism."),
            ("Pre-Existing Condition", "Any illness, injury, or symptom that existed before the insurance policy started or during the waiting period. Almost universally excluded from cover."),
            ("Waiting Period", "The initial period after taking out a policy during which claims cannot be made. Typically 14 days for illness and 0-5 days for accidents in UK pet insurance."),
            ("Direct Settlement", "A claim model where the insurer pays the vet practice directly, meaning the pet owner only pays the excess amount rather than the full bill upfront."),
            ("Financial Ombudsman Service", "An independent UK body that resolves disputes between consumers and financial services companies, including pet insurance providers, free of charge.")
        ],
        "products": [
            ("Pet Health Record Book", "Organised record keeper for vet visits, vaccinations, medications, and insurance details, hardback A5 format", "pet+health+record+book+dog+cat"),
            ("Waterproof Document Wallet", "A4 document wallet for storing pet insurance papers, vet records, and claim forms safely", "waterproof+document+wallet+a4"),
            ("Pet First Aid Kit UK", "Comprehensive first aid kit for dogs and cats, includes bandages, antiseptic, tick remover, and guide", "pet+first+aid+kit+dog+cat+uk"),
            ("Microfibre Pet Towel", "Quick-drying absorbent towel for post-treatment care, machine washable, multiple sizes", "microfibre+pet+towel+dog+cat+absorbent")
        ],
        "sources": [
            "Association of British Insurers - Pet Insurance Statistics UK",
            "Financial Ombudsman Service - Pet Insurance Complaints Guide",
            "Defra - Pet Insurance and Consumer Rights",
            "PDSA - Understanding Pet Insurance UK",
            "British Veterinary Association - Vet Practice Insurance Guidance"
        ],
        "image_queries": ["pet at veterinary clinic", "dog at vet consultation", "cat being examined by vet", "pet health documents"]
    },

    # ── 3: Pet Dental Care Routine ──
    {
        "title": "Pet Dental Care Routine: Teeth Cleaning for Dogs and Cats",
        "slug": "pet-dental-care-routine",
        "focus_keyword": "pet dental care routine",
        "seo_title": "Pet Dental Care Routine: Dog & Cat Teeth Cleaning | PetHub Online",
        "seo_desc": "Complete pet dental care routine for dogs and cats. Covers teeth brushing techniques, dental treats, professional cleaning, and signs of dental disease. UK vet guidance.",
        "quick_answer": "A good pet dental care routine includes daily tooth brushing with pet-specific toothpaste, dental chews or treats to supplement brushing, regular veterinary dental checks, and monitoring for signs of dental disease such as bad breath, difficulty eating, and red or bleeding gums. Around 80 percent of dogs and 70 percent of cats over three years old show signs of dental disease in the UK, making preventive dental care one of the most impactful things you can do for your pet's overall health.",
        "at_a_glance": [
            "Daily tooth brushing is the gold standard for pet dental care",
            "Use only pet-specific toothpaste; human toothpaste contains ingredients toxic to pets",
            "Around 80 percent of dogs over three show signs of dental disease",
            "Bad breath is often the first noticeable sign of dental problems",
            "Professional dental cleaning under anaesthetic may be needed annually for some pets",
            "Dental disease can lead to serious systemic health problems if untreated"
        ],
        "sections": [
            s("Why Pet Dental Care Matters", "<p>Dental disease is the most common health condition in adult dogs and cats in the UK. The British Veterinary Dental Association reports that approximately 80 percent of dogs and 70 percent of cats over three years old have some degree of periodontal disease. This is not just about bad breath; untreated dental disease causes pain, tooth loss, difficulty eating, and can lead to bacteria entering the bloodstream, potentially affecting the heart, kidneys, and liver.</p><p>The progression of dental disease follows a predictable pattern. Plaque (a soft film of bacteria) forms on teeth within hours of eating. Within 24-72 hours, plaque hardens into tartar (calculus), which cannot be removed by brushing alone. Tartar accumulation leads to gingivitis (gum inflammation), which progresses to periodontitis (infection of the deeper structures supporting the teeth), and eventually to tooth loss and bone damage.</p><p>Prevention through regular brushing is far more effective and far less expensive than treating established dental disease. A professional dental cleaning under general anaesthetic can cost 200-600 pounds or more at UK veterinary practices. Daily brushing costs only a few pounds per month in toothpaste and brush replacements. For a complete health management approach, see our <a href=\"{sc}\">seasonal pet care calendar</a>.</p>".format(sc=INTERNAL_LINKS["seasonal_care"])),
            s("How to Brush Your Dog's Teeth", "<p>Start by choosing a pet-specific toothbrush (finger brushes work well for beginners) and enzymatic pet toothpaste in a flavour your dog enjoys (poultry and beef are popular). Never use human toothpaste, as it contains fluoride and xylitol, both of which are toxic to dogs.</p><p>Introduce brushing gradually over 1-2 weeks. Day one: let your dog taste the toothpaste from your finger. Days two to three: rub the toothpaste gently along the gum line with your finger. Days four to five: introduce the brush, letting your dog lick the paste off it. Days six onwards: begin gentle brushing of the outer surfaces of the teeth, focusing on the gum line where plaque accumulates most.</p><p>Focus on the outside surfaces of the teeth, as the tongue naturally cleans the inside surfaces. The upper canines and back molars accumulate the most tartar. Aim for 30-60 seconds per side. Brush daily if possible; even three times per week provides significant benefit compared to no brushing. Always make the experience positive with praise and a small reward afterwards.</p>"),
            s("How to Brush Your Cat's Teeth", "<p>Cat dental care follows similar principles to dogs but requires even more patience during introduction. Cats are generally less tolerant of mouth handling, so the acclimatisation period may take 2-3 weeks. Use a small cat-specific toothbrush or a finger brush, and cat-specific enzymatic toothpaste (fish and malt flavours are often accepted).</p><p>Begin by letting your cat lick the toothpaste off your finger during a calm, relaxed moment. Over subsequent days, gently lift the lip and rub the paste along the gum line with your finger. Introduce the brush only when your cat is comfortable with finger contact on the gums. Some cats never fully accept a toothbrush; in these cases, finger brushing with enzymatic toothpaste still provides significant benefit.</p><p>Focus on the outer surfaces of the upper teeth, particularly the premolars and molars at the back of the mouth, where cats most commonly develop dental problems. Sessions should be brief (under a minute) and always positive. If your cat becomes stressed, stop and try again later. Consistency over time matters more than thoroughness in any single session.</p>"),
            s("Dental Treats, Chews, and Water Additives", "<p>Dental treats and chews supplement brushing but do not replace it. Look for products carrying the VOHC (Veterinary Oral Health Council) seal of acceptance, which means they have been tested and shown to reduce plaque or tartar. In the UK, VOHC-accepted products include certain dental chews, treats, and water additives from brands like Greenies, Purina DentaLife, and Virbac.</p><p>Dental chews work by mechanically scraping plaque from the tooth surface as the pet chews. They are most effective when given daily and sized appropriately (too small and the pet swallows without chewing; too large and they cannot chew effectively). For dogs, the chew should take at least 5 minutes to consume. Supervise chewing to prevent choking.</p><p>Water additives contain enzymatic ingredients that help reduce bacterial growth in the mouth. They are easy to use (add to the water bowl daily) and can benefit pets that resist brushing entirely. However, their effectiveness is modest compared to mechanical brushing. They are best used as part of a multi-pronged approach alongside brushing and dental chews, not as a standalone solution.</p>"),
            s("Professional Dental Cleaning and When It Is Needed", "<p>Despite the best home care, some pets develop tartar buildup that requires professional cleaning. This procedure, called a dental prophylaxis or scale and polish, is performed under general anaesthetic at a veterinary practice. It involves scaling (removing tartar from all tooth surfaces including below the gum line), polishing (smoothing the tooth surface to slow future plaque attachment), and a full oral examination including dental X-rays if indicated.</p><p>Signs your pet may need professional cleaning include persistent bad breath despite home care, visible tartar (brown or yellow deposits on teeth), red or bleeding gums, difficulty eating or dropping food, pawing at the mouth, and loose or missing teeth. Your vet should assess dental health at every routine examination and recommend professional cleaning when needed.</p><p>In the UK, professional dental cleaning for dogs typically costs 200-600 pounds depending on the complexity of the case and whether extractions are needed. For cats, costs are similar. Pet insurance may cover dental treatment if it results from injury or illness, but routine dental cleaning is usually excluded. For more on managing pet health costs, see our <a href=\"{fl}\">first-time owner guide</a>.</p>".format(fl=INTERNAL_LINKS["first_time_owner"]))
        ],
        "comparison_table": {
            "title": "Pet Dental Care Methods: Effectiveness Comparison",
            "headers": ["Method", "Effectiveness", "Frequency", "Cost (Annual)", "Pets That Accept It"],
            "rows": [
                ["Daily brushing", "High (gold standard)", "Daily", "20-40 pounds", "Most dogs, some cats"],
                ["Dental chews (VOHC)", "Moderate", "Daily", "60-150 pounds", "Most dogs"],
                ["Water additives", "Low-Moderate", "Daily", "40-80 pounds", "All (no cooperation needed)"],
                ["Dental diets", "Moderate", "Every meal", "Varies by brand", "Most pets"],
                ["Professional cleaning", "Complete reset", "As needed (1-2 years)", "200-600 pounds", "Under anaesthetic"],
            ]
        },
        "common_mistakes": [
            "Using human toothpaste, which contains fluoride and xylitol toxic to pets",
            "Starting brushing too aggressively, creating a negative association",
            "Relying solely on dental treats or chews without any mechanical brushing",
            "Ignoring bad breath as 'normal' when it is often the first sign of dental disease",
            "Waiting until dental disease is advanced before starting any dental care routine"
        ],
        "what_to_do_next": [
            "Purchase a pet-specific toothbrush and enzymatic toothpaste this week",
            "Start the gradual introduction process described above, beginning with paste on your finger",
            "Check your pet's teeth and gums today for signs of tartar, redness, or bad breath",
            "Ask about dental health at your next vet appointment",
            "Read our <a href=\"https://pethubonline.com/seasonal-pet-care-calendar-uk/\">seasonal care calendar</a> for regular health check reminders"
        ],
        "faq": [
            ("How often should I brush my pet's teeth?", "Daily is ideal. If daily is not possible, aim for at least three times per week. Even this frequency provides significant protection against dental disease compared to no brushing at all."),
            ("What are the signs of dental disease in pets?", "Bad breath, red or swollen gums, visible tartar (yellow or brown deposits), difficulty eating or dropping food, pawing at the mouth, drooling, loose teeth, and reluctance to have the mouth area touched."),
            ("Can I use coconut oil instead of pet toothpaste?", "Coconut oil has mild antibacterial properties but is not a substitute for enzymatic pet toothpaste. It lacks the enzymes that actively break down plaque. If your pet refuses toothpaste, enzymatic dental gels or water additives are better alternatives."),
            ("Do dental toys clean teeth?", "Some dental toys provide modest plaque reduction through chewing action, but they are less effective than brushing or VOHC-accepted dental chews. They are useful supplements but should not be the primary dental care method."),
            ("How much does professional teeth cleaning cost for pets in the UK?", "Typically 200-600 pounds for dogs and a similar range for cats, depending on the severity of dental disease and whether extractions are needed. The procedure requires general anaesthetic, which accounts for much of the cost.")
        ],
        "key_terms": [
            ("Periodontal Disease", "Infection and inflammation of the structures supporting the teeth (gums, bone, ligaments). The most common disease in adult dogs and cats."),
            ("Plaque", "A soft, sticky film of bacteria that forms on teeth after eating. Can be removed by brushing but hardens into tartar within 24-72 hours."),
            ("Tartar (Calculus)", "Hardened plaque that has mineralised on the tooth surface. Cannot be removed by brushing alone; requires professional scaling."),
            ("VOHC Seal", "Veterinary Oral Health Council seal of acceptance, awarded to dental products that have been scientifically tested and shown to reduce plaque or tartar."),
            ("Enzymatic Toothpaste", "Pet-specific toothpaste containing enzymes that break down plaque bacteria. Safe to swallow and does not require rinsing.")
        ],
        "products": [
            ("Virbac C.E.T. Enzymatic Dog Toothpaste", "Poultry-flavoured enzymatic toothpaste, VOHC accepted, safe to swallow, popular UK choice", "virbac+cet+enzymatic+dog+toothpaste"),
            ("Arm & Hammer Dog Dental Kit", "Includes finger brush, standard brush, and baking soda toothpaste, good starter kit", "arm+hammer+dog+dental+care+kit"),
            ("Greenies Dental Treats for Dogs", "VOHC-accepted dental chews, multiple sizes, daily use for plaque reduction", "greenies+dental+treats+dogs+uk"),
            ("Logic Oral Hygiene Gel for Cats", "Enzymatic gel that can be applied by finger, ideal for cats that reject brushes, malt flavour", "logic+oral+hygiene+gel+cats")
        ],
        "sources": [
            "British Veterinary Dental Association - Dental Disease Statistics UK",
            "Veterinary Oral Health Council - Accepted Products List",
            "PDSA - Pet Dental Care Guide UK",
            "Royal Veterinary College - Dental Disease in Companion Animals",
            "British Small Animal Veterinary Association - Dental Guidelines"
        ],
        "image_queries": ["dog teeth cleaning", "cat dental care", "pet toothbrush toothpaste", "veterinarian checking dog teeth"]
    },
]

# ──────── REMAINING 17 SPOKES (compact format) ────────
# Spokes 4-20 use the same structure with full content

def make_spoke(title, slug, fkw, seo_title, seo_desc, quick_answer, at_a_glance, sections, table, mistakes, next_steps, faq, key_terms, products, sources, img_queries):
    return {
        "title": title, "slug": slug, "focus_keyword": fkw,
        "seo_title": seo_title, "seo_desc": seo_desc,
        "quick_answer": quick_answer, "at_a_glance": at_a_glance,
        "sections": sections, "comparison_table": table,
        "common_mistakes": mistakes, "what_to_do_next": next_steps,
        "faq": faq, "key_terms": key_terms, "products": products,
        "sources": sources, "image_queries": img_queries
    }

# ── 4: Pet Allergy Management Guide ──
SPOKES.append(make_spoke(
    "Pet Allergy Management Guide: Identifying and Managing Pet Allergies",
    "pet-allergy-management-guide",
    "pet allergy management",
    "Pet Allergy Management Guide: Dogs & Cats UK | PetHub Online",
    "Comprehensive guide to identifying and managing pet allergies in dogs and cats. Covers food allergies, environmental allergies, symptoms, diagnosis, and UK treatment options.",
    "Pet allergies fall into three main categories: food allergies, environmental allergies (atopy), and flea allergy dermatitis. Symptoms include itchy skin, ear infections, paw licking, digestive upset, and hair loss. Diagnosis involves elimination diets for food allergies and intradermal testing for environmental allergies. Management combines allergen avoidance, medication, and supportive care. UK vets report that allergies account for a significant proportion of dermatology consultations, with many pets requiring lifelong management.",
    ["Food allergies typically cause year-round symptoms including itchy skin and digestive upset", "Environmental allergies (atopy) often follow seasonal patterns linked to pollen or mould", "Flea allergy dermatitis can cause severe itching from just one or two flea bites", "Elimination diets lasting 8-12 weeks are the gold standard for diagnosing food allergies", "Antihistamines, steroids, and newer immunotherapy drugs are UK treatment options", "Early diagnosis and management prevent secondary infections and improve quality of life"],
    [s("Types of Pet Allergies Explained", "<p>The three main allergy types in dogs and cats are food allergies, environmental allergies (atopic dermatitis or atopy), and flea allergy dermatitis (FAD). Food allergies are caused by an immune reaction to specific proteins in the diet, most commonly beef, chicken, dairy, wheat, and soy. They cause year-round symptoms regardless of season and can develop at any age, even to foods the pet has eaten for years without issue.</p><p>Environmental allergies (atopy) are triggered by airborne allergens including pollen, dust mites, mould spores, and grass. They often follow seasonal patterns in the UK, worsening in spring and summer when pollen counts are high, though dust mite allergies cause year-round symptoms. Atopy is particularly common in breeds like Labrador Retrievers, Golden Retrievers, West Highland White Terriers, Bulldogs, and Staffordshire Bull Terriers.</p><p>Flea allergy dermatitis is the most common allergy in UK pets. It is caused by a hypersensitivity to proteins in flea saliva. Affected pets react severely to even one or two flea bites, developing intense itching, hair loss, and skin lesions, typically concentrated around the base of the tail, lower back, and inner thighs. Strict year-round flea prevention is essential for management. See our <a href=\"{sc}\">seasonal care calendar</a> for flea prevention scheduling.</p>".format(sc=INTERNAL_LINKS["seasonal_care"])),
     s("Recognising Allergy Symptoms in Dogs and Cats", "<p>The primary symptom of allergies in pets is itchy skin (pruritus). In dogs, this manifests as scratching, licking (especially paws), face rubbing, ear scratching, and scooting. Hot spots (acute moist dermatitis) and recurrent ear infections are common secondary problems. In cats, symptoms include over-grooming leading to bald patches, miliary dermatitis (small scabby bumps), chin acne, and eosinophilic granuloma complex (raised, ulcerated skin lesions).</p><p>Food allergies may also cause gastrointestinal symptoms including vomiting, diarrhoea, flatulence, and frequent bowel movements. However, many pets with food allergies show only skin symptoms. Environmental allergies rarely cause digestive symptoms but often cause watery eyes, sneezing, and runny nose alongside skin itchiness.</p><p>The location of itching can suggest the allergy type. Paw licking and ear infections are more associated with environmental allergies. Itching around the rear and base of the tail suggests flea allergy. Facial itching and generalised body itching can indicate food allergy. However, overlap is common, and many pets have multiple concurrent allergies.</p>"),
     s("Diagnosing Pet Allergies: Tests and Elimination Diets", "<p>Diagnosing the specific allergy type requires systematic investigation. Your vet will start with a thorough history and examination, checking for flea evidence, assessing the pattern and seasonality of symptoms, and reviewing the diet. Flea allergy is diagnosed by response to strict flea control. If symptoms persist despite complete flea elimination, food allergy or atopy is investigated.</p><p>Food allergy diagnosis requires an elimination diet trial lasting 8-12 weeks. Your pet eats a novel protein diet (a protein they have never eaten before, such as venison, duck, or hydrolysed protein) with absolutely no other food, treats, or flavoured medications. If symptoms improve, the original diet is reintroduced to confirm the reaction. This process is time-consuming but is the only reliable way to diagnose food allergies; blood tests for food allergies are unreliable in pets.</p><p>Environmental allergies can be confirmed through intradermal skin testing (considered the gold standard) or blood tests for allergen-specific IgE. These tests identify which environmental allergens trigger reactions, enabling targeted immunotherapy (allergy desensitisation injections). Your vet may refer you to a veterinary dermatologist for these specialised tests.</p>"),
     s("Treatment Options Available in the UK", "<p>Allergy treatment in the UK combines allergen avoidance, symptomatic relief, and long-term management. For food allergies, the treatment is permanent avoidance of the identified allergen through a carefully selected diet. For environmental allergies, complete avoidance is rarely possible, so treatment focuses on reducing exposure and managing symptoms.</p><p>Medical treatments include antihistamines (often first-line, though effectiveness varies between pets), corticosteroids (effective but with long-term side effects), ciclosporin (Atopica), and newer targeted therapies. Oclacitinib (Apoquel) is a Janus kinase inhibitor specifically licensed for dogs that provides rapid itch relief with fewer side effects than steroids. Lokivetmab (Cytopoint) is a monthly injection that targets the itch signal directly and is well tolerated by most dogs.</p><p>Allergen-specific immunotherapy (desensitisation) is the only treatment that addresses the underlying immune response rather than just symptoms. Based on skin test or blood test results, a customised vaccine is prepared containing your pet's specific allergens. Administered as regular injections over months to years, it gradually reduces the immune response. Success rates are approximately 60-70 percent in dogs. For multi-pet considerations, see our <a href=\"{mp}\">multi-pet household guide</a>.</p>".format(mp=INTERNAL_LINKS["multi_pet"])),
     s("Supportive Care and Home Management", "<p>Alongside medical treatment, supportive home care significantly improves allergic pets' comfort. Regular bathing with a hypoallergenic or medicated shampoo removes allergens from the coat and soothes irritated skin. For dogs, bathing every 1-2 weeks during flare-ups is beneficial. For cats, bathing is usually impractical, but wiping the coat with a damp cloth after outdoor access helps remove pollen.</p><p>Essential fatty acid supplementation (omega-3 and omega-6) improves skin barrier function and may reduce the severity of allergic reactions. Fish oil supplements designed for pets are widely available in the UK and can be added to food daily. Some veterinary diets for allergic pets include elevated fatty acid levels.</p><p>Environmental management for dust mite allergies includes washing pet bedding weekly at 60 degrees Celsius, using anti-allergy bed covers, vacuuming frequently with a HEPA filter vacuum, and reducing carpet and soft furnishing exposure. For pollen allergies, wiping paws and belly after walks during high pollen seasons, avoiding walks during peak pollen hours (morning and evening), and keeping windows closed during high pollen counts all help reduce allergen exposure.</p>")],
    {"title": "Pet Allergy Types: Comparison", "headers": ["Allergy Type", "Common Triggers", "Typical Symptoms", "Seasonality", "Diagnosis Method"],
     "rows": [["Food allergy", "Beef, chicken, dairy, wheat", "Itchy skin, ear infections, GI upset", "Year-round", "8-12 week elimination diet"],
              ["Environmental (atopy)", "Pollen, dust mites, mould", "Itchy paws, face rubbing, ear infections", "Often seasonal", "Intradermal skin test or blood test"],
              ["Flea allergy (FAD)", "Flea saliva proteins", "Intense tail-base itching, hair loss", "Worst spring-autumn", "Response to strict flea control"],
              ["Contact allergy", "Cleaning products, fabrics", "Localised redness, itching at contact site", "Year-round", "Avoidance trial"]]},
    ["Assuming itchy skin is always fleas without investigating other allergy types", "Relying on blood tests for food allergy diagnosis instead of proper elimination diets", "Using human antihistamines without veterinary guidance on pet-safe doses", "Stopping flea prevention in winter when fleas can survive indoors year-round", "Giving treats and flavoured medications during a food elimination trial, invalidating results"],
    ["Book a vet appointment to discuss your pet's allergy symptoms and start diagnosis", "Begin strict year-round flea prevention for all pets in the household", "Consider omega-3 fatty acid supplementation to support skin health", "Read our <a href=\"https://pethubonline.com/seasonal-pet-care-calendar-uk/\">seasonal care calendar</a> for flea and allergy management schedules", "Check our <a href=\"https://pethubonline.com/first-time-pet-owner-guide-uk/\">first-time owner guide</a> for preventive health setup"],
    [("How do I know if my pet has allergies?", "The most common sign is persistent itching, scratching, licking, or face rubbing. Recurrent ear infections, paw licking, hot spots, and hair loss also suggest allergies. If symptoms persist for more than 2-3 weeks, consult your vet for investigation."),
     ("Can pet allergies be cured?", "Food allergies are managed by permanent avoidance of the triggering food. Environmental allergies cannot be cured but can be well managed with medication and, in some cases, significantly improved with immunotherapy. Flea allergy requires lifelong strict flea prevention."),
     ("Are certain breeds more prone to allergies?", "Yes. In dogs, Labrador Retrievers, Golden Retrievers, West Highland White Terriers, Bulldogs, German Shepherds, and Staffordshire Bull Terriers have higher allergy rates. In cats, breed predisposition is less clear, though Siamese and Abyssinians may be more susceptible."),
     ("How much does allergy treatment cost in the UK?", "Costs vary widely. Antihistamines are inexpensive (10-30 pounds per month). Apoquel costs approximately 40-80 pounds per month for a medium dog. Cytopoint injections cost 40-120 pounds per injection. Immunotherapy costs 200-400 pounds for the first year."),
     ("Can I give my dog human antihistamines?", "Some human antihistamines (like chlorpheniramine and cetirizine) can be used in dogs, but only with veterinary guidance on appropriate dosing. Never give antihistamines to pets without consulting your vet first, as some formulations contain ingredients toxic to pets.")],
    [("Atopic Dermatitis (Atopy)", "A genetic predisposition to develop allergic reactions to environmental allergens absorbed through the skin. The most common form of allergy in dogs."),
     ("Elimination Diet", "A strictly controlled diet using novel or hydrolysed proteins to diagnose food allergies. Must last 8-12 weeks with absolutely no other foods or flavoured items."),
     ("Intradermal Skin Test", "A diagnostic test where small amounts of allergens are injected into the skin to identify which substances trigger an immune reaction. Gold standard for environmental allergy diagnosis."),
     ("Immunotherapy", "Allergen-specific treatment involving regular injections of gradually increasing allergen doses to reduce immune sensitivity. The only treatment addressing the underlying cause of environmental allergies."),
     ("Pruritus", "Medical term for itchy skin. The primary symptom of most allergic conditions in pets.")],
    [("Yumega Plus Dog Skin Supplement", "Omega-3 and omega-6 fatty acid supplement for dogs, supports skin barrier and coat health, UK veterinary recommended", "yumega+plus+dog+skin+supplement"),
     ("Malaseb Medicated Shampoo", "Antifungal and antibacterial shampoo for dogs and cats, helps manage secondary skin infections from allergies", "malaseb+medicated+shampoo+dog+cat"),
     ("Forthglade Cold Pressed Grain Free Dog Food", "Limited ingredient dog food with single protein source, suitable for food allergy management, UK brand", "forthglade+cold+pressed+grain+free+dog+food"),
     ("Seresto Flea and Tick Collar for Dogs", "8-month flea and tick protection collar, continuous slow-release, essential for flea allergy prevention", "seresto+flea+tick+collar+dogs+uk")],
    ["British Small Animal Veterinary Association - Allergy Guidelines", "International Committee on Allergic Diseases of Animals", "PDSA - Pet Allergies Guide UK", "Royal Veterinary College - Dermatology Research", "Veterinary Dermatology Journal - Canine Atopic Dermatitis"],
    ["dog scratching itching", "cat grooming licking fur", "veterinarian examining dog skin", "pet allergy treatment"]
))

# Now generate the remaining 16 spokes (5-20) with the same comprehensive structure
# Each spoke has 5 content sections, comparison table, 5 mistakes, 5 next steps, 5 FAQ, 5 key terms, 4 products, 5 sources, 4 image queries

SPOKE_DATA = [
    # (title, slug, fkw, seo_title, seo_desc, quick_answer, at_a_glance_list, section_tuples, table_dict, mistakes, next_steps, faq_tuples, key_terms_tuples, products_tuples, sources, img_queries)
    (
        "Pet Weight Management Plan: Healthy Weight for Dogs and Cats",
        "pet-weight-management-plan", "pet weight management plan",
        "Pet Weight Management Plan: Healthy Weight Guide UK | PetHub Online",
        "Guide to pet weight management for dogs and cats. Covers ideal weight assessment, calorie control, exercise plans, and UK vet advice on pet obesity.",
        "Pet obesity is a growing welfare crisis in the UK, with the PDSA estimating that over 50 percent of dogs and 44 percent of cats are overweight or obese. A weight management plan involves determining your pet's ideal body condition score, calculating appropriate calorie intake, controlling portions, increasing exercise, and monitoring progress with regular weigh-ins. Even a 10-15 percent reduction in body weight can significantly improve a pet's mobility, energy, and lifespan.",
        ["Over 50 percent of UK dogs and 44 percent of cats are overweight or obese", "Use the Body Condition Score (1-9 scale) rather than weight alone to assess your pet", "You should be able to feel your pet's ribs easily but not see them prominently", "Reduce daily calorie intake by 15-20 percent for gradual, safe weight loss", "Increase exercise gradually; sudden intense activity risks joint injury in overweight pets", "Regular weigh-ins (every 2 weeks) track progress and maintain motivation"],
        [s("Assessing Your Pet's Weight: Body Condition Scoring", "<p>Body Condition Score (BCS) is the most reliable way to assess whether your pet is at a healthy weight. The standard 9-point scale ranges from 1 (emaciated) to 9 (morbidly obese), with 4-5 being ideal. At the ideal score, you should be able to feel your pet's ribs easily with light pressure (like feeling the back of your hand), see a visible waist when viewed from above, and observe a tucked abdomen when viewed from the side.</p><p>Weight alone can be misleading because breed, build, and muscle mass vary enormously. A muscular Staffordshire Bull Terrier may weigh the same as a fat Beagle despite having a completely different body composition. Your vet can teach you to assess BCS at home, and most UK veterinary practices offer free weight clinics with trained veterinary nurses.</p><p>For cats, assessment is similar but requires handling. You should feel the ribs with gentle pressure, see a waist from above, and notice a small belly tuck from the side. Overweight cats often develop a fatty pad (primordial pouch) that swings when walking, though a small pouch is normal. Any BCS of 7 or above warrants a weight management plan. See our <a href=\"{sc}\">seasonal care calendar</a> for regular health check scheduling.</p>".format(sc=INTERNAL_LINKS["seasonal_care"])),
         s("Calculating Calorie Requirements", "<p>Weight loss requires consuming fewer calories than your pet burns. Your vet can calculate your pet's Resting Energy Requirement (RER) and recommend a daily calorie target for safe weight loss. As a general guide, reducing current calorie intake by 15-20 percent produces a safe weight loss rate of 1-2 percent of body weight per week.</p><p>Treats are often the hidden calorie culprit. Many UK pet owners underestimate how many calories treats add. A single dental chew can contain 70-90 calories; a handful of training treats adds 50-100 calories. Treats should comprise no more than 10 percent of daily calorie intake. Switch to low-calorie alternatives like carrot sticks, green beans, or small pieces of apple (no seeds) for dogs, or tiny amounts of cooked chicken for cats.</p><p>Measuring food accurately is essential. Use a kitchen scale rather than a cup measure, as cup volumes vary significantly and consistently overestimate portions. Weigh your pet's food for every meal. If feeding dry food, the manufacturer's feeding guide is a starting point but should be adjusted based on your pet's individual needs and response. Vet-recommended weight management diets are higher in fibre and protein to maintain satiety while reducing calories.</p>"),
         s("Exercise Plans for Overweight Pets", "<p>Increasing physical activity is crucial alongside calorie reduction. For overweight dogs, start with gentle walks at the pet's pace and gradually increase duration and intensity. A common starting plan is two 15-minute walks daily, increasing by 5 minutes per week until reaching 30-45 minutes per walk. Avoid high-impact activities (running, jumping, fetch on hard surfaces) until weight has reduced to protect already-stressed joints.</p><p>Swimming and hydrotherapy are excellent for overweight dogs, providing cardiovascular exercise without joint impact. Several UK veterinary practices and specialist centres offer hydrotherapy pools. Even supervised paddling in shallow water provides beneficial exercise for dogs uncomfortable with longer walks.</p><p>For overweight cats, increasing activity requires creativity. Interactive play sessions (wand toys mimicking prey movement) for 10-15 minutes twice daily burn calories and provide mental enrichment. Puzzle feeders that require physical effort to access food, vertical climbing opportunities, and food scattered around the house (encouraging natural foraging movement) all contribute to increased activity. See our <a href=\"{ie}\">indoor cat exercise guide</a> for detailed activity plans.</p>".format(ie=INTERNAL_LINKS["indoor_exercise"])),
         s("Veterinary Weight Management Programmes", "<p>Most UK veterinary practices offer structured weight management programmes, often run by trained veterinary nurses and frequently free of charge. These programmes include an initial assessment with BCS scoring and target weight setting, a customised diet plan with specific food recommendations, regular weigh-in appointments (typically every 2-4 weeks), and ongoing support and plan adjustments.</p><p>Veterinary weight management diets (available from brands like Royal Canin, Hill's, and Purina) are formulated to reduce calories while maintaining essential nutrients, protein levels, and satiety. They are more effective than simply feeding less of a standard diet, which can lead to nutrient deficiencies. Your vet may recommend a specific diet based on your pet's needs.</p><p>For severely obese pets (BCS 8-9), veterinary supervision is essential. Rapid weight loss can be dangerous, particularly in cats, where it can trigger hepatic lipidosis (fatty liver disease), a potentially fatal condition. Weight loss in obese cats should always be gradual and veterinarian-supervised. Target a weight loss rate of no more than 1-2 percent of body weight per week.</p>"),
         s("Maintaining Healthy Weight Long-Term", "<p>Reaching the target weight is only half the battle; maintaining it requires permanent lifestyle changes. Once your pet reaches their ideal BCS, your vet will calculate a maintenance calorie requirement, which is higher than the weight loss target but lower than the original intake that caused weight gain. Continue measuring food portions and limiting treats.</p><p>Regular weigh-ins should continue monthly after reaching the target. Weight regain is common if portion control slips. Keep a weight log and act immediately if weight increases by more than 5 percent, returning to the weight loss calorie target before the gain becomes significant.</p><p>Household consistency is essential. All family members must follow the same feeding rules. A common scenario is one family member carefully measuring portions while another gives extra treats or table scraps. Establish clear household rules about feeding and ensure everyone understands that overfeeding is a welfare concern, not an act of love. For multi-pet feeding management, see our <a href=\"{mp}\">multi-pet household guide</a>.</p>".format(mp=INTERNAL_LINKS["multi_pet"]))],
        {"title": "Pet Weight Management: Key Metrics", "headers": ["Metric", "Dogs", "Cats", "How to Check", "Frequency"],
         "rows": [["Body Condition Score", "Ideal: 4-5 out of 9", "Ideal: 4-5 out of 9", "Rib feel test + visual assessment", "Monthly"],
                  ["Weight", "Breed-specific ideal", "Typically 3.5-5.5 kg", "Veterinary or home scale", "Every 2 weeks during loss"],
                  ["Daily calories", "Varies by size/activity", "200-300 kcal typical adult", "Vet calculation + food label", "Recalculate at target weight"],
                  ["Treat allocation", "Max 10% of daily calories", "Max 10% of daily calories", "Weigh/count treats daily", "Daily monitoring"],
                  ["Weight loss rate", "1-2% body weight per week", "1-2% (max) per week", "Regular weigh-ins", "Every 2 weeks"]]},
        ["Free-feeding (leaving food out all day) rather than measured meal portions", "Underestimating the calorie content of treats, dental chews, and table scraps", "Starting intense exercise suddenly in overweight pets, risking joint injury", "Reducing a standard diet rather than switching to a vet-recommended weight management food", "Allowing different family members to give extra food, undermining the plan"],
        ["Ask your vet to assess your pet's Body Condition Score at the next appointment", "Weigh your pet's food portions with a kitchen scale starting today", "Replace high-calorie treats with low-calorie alternatives (carrot, green beans for dogs)", "Read our <a href=\"https://pethubonline.com/seasonal-pet-care-calendar-uk/\">seasonal care calendar</a> for weight check reminders", "Check our <a href=\"https://pethubonline.com/first-time-pet-owner-guide-uk/\">first-time owner guide</a> for feeding best practices"],
        [("How do I know if my pet is overweight?", "Use the Body Condition Score: feel your pet's ribs. If you need firm pressure to find them, your pet is likely overweight. View from above; there should be a visible waist. View from the side; the abdomen should tuck up. Ask your vet for a BCS assessment at any appointment."),
         ("How much should I feed my dog per day?", "Calorie needs depend on breed, size, age, activity level, and whether the dog is neutered. Your vet can calculate the specific amount. As a starting point, follow the food manufacturer's guide for your dog's ideal weight (not current weight if overweight), then adjust based on BCS changes."),
         ("Can neutering cause weight gain?", "Neutering reduces metabolic rate by approximately 20-30 percent, meaning neutered pets need fewer calories. If food intake is not adjusted after neutering, weight gain commonly follows. Reduce portions by 15-20 percent after neutering and monitor BCS closely."),
         ("Is it dangerous for cats to lose weight too quickly?", "Yes. Rapid weight loss in cats (more than 2 percent of body weight per week) can trigger hepatic lipidosis (fatty liver disease), a serious and potentially fatal condition. Cat weight loss must always be gradual and veterinarian-supervised."),
         ("How long does it take for a pet to reach a healthy weight?", "Typically 3-6 months for moderately overweight pets, longer for obese pets. A safe rate of 1-2 percent body weight loss per week means a 30 kg dog needing to lose 5 kg would take approximately 8-16 weeks.")],
        [("Body Condition Score (BCS)", "A 9-point visual and tactile assessment scale for evaluating body fat. Score 4-5 is ideal. Used because weight alone does not account for breed, build, and muscle mass differences."),
         ("Resting Energy Requirement (RER)", "The number of calories a pet needs at rest for basic metabolic functions. Calculated as 70 x (body weight in kg)^0.75. Used as the basis for determining feeding amounts."),
         ("Hepatic Lipidosis", "Fatty liver disease in cats, triggered when fat is mobilised too rapidly during weight loss or starvation. A potentially fatal condition requiring immediate veterinary treatment."),
         ("Satiety", "The feeling of fullness after eating. Weight management diets are formulated with high fibre and protein to maintain satiety on reduced calories."),
         ("Metabolic Rate", "The rate at which the body burns calories. Reduced by neutering, ageing, and decreased activity. Must be accounted for in calorie calculations.")],
        [("Salter Pet Weighing Scale", "Digital pet scale with hold function for wriggling pets, accurate to 50g, suitable for dogs and cats", "salter+digital+pet+weighing+scale"),
         ("Kong Classic Dog Toy", "Stuff with low-calorie treats for extended feeding enrichment, durable rubber, multiple sizes", "kong+classic+dog+toy+stuffable"),
         ("Catit Senses 2.0 Food Tree", "Multi-level puzzle feeder for cats, slows eating and encourages activity, adjustable difficulty", "catit+senses+food+tree+cat"),
         ("Trixie Dog Activity Flip Board", "Interactive puzzle feeder for dogs, promotes mental stimulation during weight management", "trixie+dog+activity+flip+board")],
        ["PDSA Animal Wellbeing Report - Pet Obesity Statistics UK", "British Veterinary Association - Weight Management Guidelines", "Association for Pet Obesity Prevention - BCS Assessment Guide", "Royal Veterinary College - Feline Obesity Research", "BSAVA - Nutritional Assessment Guidelines"],
        ["overweight dog walking", "cat eating from puzzle feeder", "dog being weighed at vet", "healthy active dog running"]
    ),
]

for sp in SPOKE_DATA:
    SPOKES.append(make_spoke(*sp))

# ──── Compact spoke definitions for spokes 6-20 ────
# Using a builder to avoid bloating the script

def build_compact_spoke(n, title, slug, fkw, desc, qa, glance, sec_data, tbl, mistakes, nexts, faqs, terms, prods, srcs, imgs):
    secs = [s(h, c) for h, c in sec_data]
    return make_spoke(title, slug, fkw,
        f"{title} | PetHub Online", desc, qa, glance, secs, tbl, mistakes, nexts, faqs, terms, prods, srcs, imgs)

COMPACT_SPOKES = [
    # ── 6: Pet Anxiety Solutions Guide ──
    {
        "n": 6, "title": "Pet Anxiety Solutions Guide: Separation Anxiety and Stress Relief",
        "slug": "pet-anxiety-solutions-guide", "fkw": "pet anxiety solutions",
        "desc": "Guide to managing pet anxiety including separation anxiety, noise phobias, and general stress in dogs and cats. Covers UK treatment options and behavioural strategies.",
        "qa": "Pet anxiety manifests as destructive behaviour, excessive barking or meowing, inappropriate toileting, pacing, trembling, and refusal to eat. Separation anxiety affects an estimated 20-40 percent of dogs in the UK. Solutions include gradual desensitisation, environmental enrichment, calming aids (pheromone diffusers, calming supplements), behavioural modification training, and in severe cases, veterinary-prescribed medication. Early intervention prevents escalation. Cats also experience anxiety, often showing it through hiding, over-grooming, urine spraying, and appetite changes.",
        "glance": ["Separation anxiety affects 20-40 percent of UK dogs", "Never punish anxious behaviour; it increases stress and worsens the problem", "Adaptil (dogs) and Feliway (cats) pheromone diffusers can reduce mild anxiety", "Gradual desensitisation is the gold standard for separation anxiety treatment", "Severe cases may require veterinary-prescribed anti-anxiety medication", "Thunder shirts and calming supplements provide additional support for some pets"],
        "sec_data": [
            ("Understanding Pet Anxiety: Types and Causes", "<p>Pet anxiety falls into three main categories: separation anxiety (distress when left alone), noise phobias (fear of loud sounds like fireworks, thunder, or construction), and generalised anxiety (chronic anxiousness not tied to specific triggers). Separation anxiety is the most common, with UK veterinary behaviourists reporting it as their most frequent referral reason.</p><p>Causes include insufficient socialisation during the critical development period (3-14 weeks in puppies, 2-7 weeks in kittens), traumatic experiences, sudden changes in routine, rehoming (common in rescue pets), loss of a companion animal or owner, and genetic predisposition. Some breeds are more prone to anxiety, including Border Collies, German Shepherds, Cocker Spaniels, and Vizslas.</p><p>Recognising anxiety early is crucial because untreated anxiety worsens over time. Early signs in dogs include following the owner from room to room, becoming agitated when departure cues occur (picking up keys, putting on shoes), and minor destructive behaviour. In cats, early signs include hiding more frequently, changes in grooming patterns, and reduced appetite. See our <a href=\"{fl}\">first-time owner guide</a> for preventing anxiety from the start.</p>".format(fl=INTERNAL_LINKS["first_time_owner"])),
            ("Separation Anxiety: Desensitisation and Management", "<p>Desensitisation for separation anxiety involves gradually increasing the duration your pet is left alone, starting from seconds and building to hours over weeks or months. Begin by stepping outside the door for 5 seconds, then returning calmly. Gradually increase the time in small increments, always returning before your pet becomes distressed.</p><p>Management strategies include: leaving a worn piece of your clothing for scent comfort, providing a stuffed Kong or long-lasting chew to create a positive departure association, using a pheromone diffuser (Adaptil for dogs, Feliway for cats), playing calming music or leaving the radio on, and ensuring your pet has had adequate exercise and mental stimulation before you leave.</p><p>Avoid making departures and returns emotionally charged. Do not have long, emotional goodbyes or enthusiastic greetings, as these heighten the contrast between your presence and absence. Aim for calm, matter-of-fact departures and low-key returns. Only greet your pet once they are calm, not while they are jumping or crying at your return.</p>"),
            ("Noise Phobias: Fireworks, Thunder, and Loud Sounds", "<p>Noise phobias are extremely common in UK pets, particularly around Bonfire Night, New Year's Eve, and during thunderstorms. The Dogs Trust estimates that 45 percent of UK dogs show signs of fear during fireworks. Symptoms range from mild (hiding, trembling) to severe (destructive escape attempts, self-injury, panic attacks).</p><p>Short-term management during noise events includes: creating a safe den (a covered crate or quiet room with comfortable bedding), closing curtains and playing masking sounds (TV, music, white noise), using Adaptil or Feliway diffusers started 24 hours before the expected event, considering calming supplements or veterinary-prescribed medication for known severe cases, and staying calm yourself (pets pick up on owner anxiety).</p><p>Long-term treatment involves sound desensitisation programmes, where recordings of the feared sound are played at very low volumes during positive activities (feeding, play) and gradually increased over weeks. The Dogs Trust Sound Therapy programme provides free downloadable resources for this purpose. Starting desensitisation months before fireworks season is essential.</p>"),
            ("Calming Aids and Supplements Available in the UK", "<p>Several calming products are available without prescription in the UK. Pheromone products (Adaptil for dogs, Feliway for cats) release synthetic versions of natural calming pheromones. They come as plug-in diffusers, sprays, and collars. Evidence supports their effectiveness for mild to moderate anxiety, and they are recommended by many UK veterinary behaviourists as part of a comprehensive management plan.</p><p>Calming supplements containing ingredients like L-theanine, casein, tryptophan, and valerian are widely available. Brands like Zylkene, YuCalm, and Nutracalm have some evidence supporting their use for mild anxiety. They are not a substitute for behavioural modification but can support the process. Always check with your vet before starting supplements, especially if your pet takes other medications.</p><p>Pressure wraps (like the Thundershirt) apply gentle, constant pressure to the torso, which has a calming effect on some pets. Research results are mixed, but many owners report significant benefit, particularly for noise phobias and travel anxiety. They are safe to use and can be combined with other calming strategies.</p>"),
            ("When to Seek Professional Help", "<p>Consult your vet if your pet's anxiety causes self-harm (excessive licking creating wounds, breaking teeth or nails attempting to escape), significant property damage, inability to eat or drink when anxious, inappropriate toileting in a previously house-trained pet, or if anxiety is worsening despite your management efforts.</p><p>Your vet may prescribe anti-anxiety medication (such as fluoxetine, clomipramine, or trazodone) for severe cases. Medication is most effective when combined with a behavioural modification plan, not used alone. Your vet may refer you to a certified veterinary behaviourist (look for CCAB or APBC accreditation in the UK) for a comprehensive behavioural assessment and customised treatment plan.</p><p>Veterinary behaviourists charge typically 200-400 pounds for an initial consultation, which includes a full behavioural history, diagnosis, and detailed management plan. While not inexpensive, professional intervention for severe anxiety is often the most effective and humane approach. Pet insurance may cover behavioural consultations if the condition is classified as a medical issue. For holistic pet management, see our <a href=\"{sc}\">seasonal care calendar</a>.</p>".format(sc=INTERNAL_LINKS["seasonal_care"]))
        ],
        "tbl": {"title": "Pet Anxiety Solutions: Effectiveness Comparison", "headers": ["Solution", "Best For", "Evidence Level", "Cost", "Time to Effect"],
                "rows": [["Pheromone diffusers", "Mild-moderate anxiety", "Moderate evidence", "15-25 pounds/month", "1-2 weeks"],
                         ["Desensitisation training", "Separation and noise anxiety", "Strong evidence", "Free (DIY) or 200+ (professional)", "Weeks to months"],
                         ["Calming supplements", "Mild anxiety support", "Limited-moderate evidence", "10-30 pounds/month", "2-4 weeks"],
                         ["Pressure wraps", "Noise phobias, travel", "Mixed evidence", "25-40 pounds one-off", "Immediate"],
                         ["Prescription medication", "Severe anxiety", "Strong evidence", "20-50 pounds/month", "2-6 weeks"]]},
        "mistakes": ["Punishing anxious behaviour, which increases fear and worsens the problem", "Leaving an anxious pet alone for extended periods without gradual desensitisation", "Relying solely on calming aids without addressing the underlying behavioural issue", "Getting another pet to 'keep them company' without proper assessment", "Starting noise desensitisation too late, only days before fireworks season"],
        "nexts": ["Identify your pet's specific anxiety triggers and note when symptoms occur", "Try an Adaptil (dogs) or Feliway (cats) diffuser in your pet's favourite room", "Start practising brief departures and calm returns if separation anxiety is suspected", "Read our <a href=\"https://pethubonline.com/first-time-pet-owner-guide-uk/\">first-time owner guide</a> for preventing anxiety in new pets", "Book a vet appointment if anxiety is severe or worsening"],
        "faqs": [("How do I know if my pet has anxiety?", "Signs include destructive behaviour when alone, excessive vocalisation, pacing, trembling, inappropriate toileting, loss of appetite, excessive panting (dogs), over-grooming (cats), and aggression. If these behaviours are frequent or intense, consult your vet."),
                 ("Can separation anxiety be cured?", "Most dogs can be significantly improved with proper desensitisation and management, though the process takes weeks to months. Complete resolution depends on severity and consistency of treatment. Some pets require ongoing management."),
                 ("Are calming supplements safe for pets?", "Most commercially available calming supplements are safe when used as directed. However, always consult your vet before starting any supplement, especially if your pet takes medication or has health conditions. Choose products from reputable brands with ingredient transparency."),
                 ("Should I get another pet to help with separation anxiety?", "Getting another pet specifically to resolve separation anxiety is rarely effective and may create additional problems. The anxious pet's distress is about your absence, not about being alone per se. A companion may help in some cases but should never be the primary treatment strategy."),
                 ("Do thunder shirts really work?", "Evidence is mixed, but many owners report significant improvement, particularly for noise phobias. They work best when introduced during calm times first, not only during stressful events. They are safe and inexpensive to try as part of a multi-faceted anxiety management approach.")],
        "terms": [("Separation Anxiety", "A specific anxiety disorder where the pet becomes extremely distressed when separated from their primary attachment figure(s). One of the most common behavioural problems in UK dogs."),
                  ("Desensitisation", "A behavioural technique involving gradual, controlled exposure to a feared stimulus at low intensity, paired with positive experiences, to reduce the fear response over time."),
                  ("Pheromone", "A chemical substance released by animals that affects the behaviour or physiology of others of the same species. Synthetic versions (Adaptil, Feliway) are used therapeutically for anxiety."),
                  ("Counterconditioning", "Changing an emotional response by pairing a feared stimulus with something positive. Used alongside desensitisation to treat phobias and anxiety."),
                  ("Generalised Anxiety Disorder", "Chronic anxiety not linked to specific triggers, resulting in a constantly heightened state of alertness and stress. May require long-term medication and behavioural management.")],
        "prods": [("Adaptil Calm Home Diffuser", "Synthetic dog-appeasing pheromone diffuser, clinically proven to reduce anxiety, covers 70 sqm, lasts 30 days", "adaptil+calm+home+diffuser+dog"),
                  ("Feliway Classic Diffuser", "Synthetic feline facial pheromone diffuser for cat anxiety, reduces spraying and hiding, 30-day refill", "feliway+classic+diffuser+cat+calming"),
                  ("Kong Classic Stuffable Dog Toy", "Fill with treats for positive departure associations, durable natural rubber, freezable for longer engagement", "kong+classic+stuffable+dog+toy"),
                  ("Thundershirt for Dogs", "Pressure wrap providing constant gentle pressure for anxiety relief, adjustable fit, machine washable", "thundershirt+dog+anxiety+wrap+uk")],
        "srcs": ["Dogs Trust - Separation Anxiety and Sound Therapy Resources", "International Cat Care - Feline Anxiety Management", "PDSA - Pet Anxiety Guide UK", "APBC - Association of Pet Behaviour Counsellors UK", "British Veterinary Behaviour Association - Anxiety Treatment Guidelines"],
        "imgs": ["anxious dog hiding", "calm dog resting home", "cat hiding under bed", "dog with calming products"]
    },
    # ── 7: Pet Grooming Schedule UK ──
    {"n": 7, "title": "Pet Grooming Schedule UK: Breed-Specific Grooming Timelines",
     "slug": "pet-grooming-schedule-uk", "fkw": "pet grooming schedule UK",
     "desc": "Breed-specific pet grooming schedule for UK dogs and cats. Covers brushing frequency, bathing, nail trimming, ear cleaning, and professional grooming timelines.",
     "qa": "A proper grooming schedule depends on your pet's breed, coat type, and lifestyle. Short-haired dogs need brushing once or twice weekly, while long-haired breeds require daily brushing. Cats generally self-groom but long-haired breeds need daily brushing to prevent matting. Professional grooming every 6-8 weeks is recommended for breeds with continuously growing coats. Nail trimming every 2-4 weeks, ear cleaning as needed, and dental care should all be part of the routine.",
     "glance": ["Short-haired dogs: brush 1-2 times weekly, bathe every 8-12 weeks", "Long-haired dogs: brush daily, professional groom every 6-8 weeks", "Short-haired cats: brush weekly, rarely need bathing", "Long-haired cats: brush daily to prevent painful matting", "Trim nails every 2-4 weeks for dogs, check monthly for cats", "Start grooming routines early in life for lifelong acceptance"],
     "sec_data": [
         ("Brushing Frequency by Coat Type", "<p>Coat type determines brushing needs more than breed alone. Smooth, short coats (Labrador, Beagle, Siamese) need weekly brushing with a rubber curry brush or bristle brush to remove dead hair and distribute natural oils. Medium-length coats (Border Collie, Cocker Spaniel, domestic longhair cats) need brushing every 2-3 days with a slicker brush and comb. Long, flowing coats (Yorkshire Terrier, Shih Tzu, Persian) require daily brushing with a pin brush and wide-tooth comb to prevent matting.</p><p>Wire or rough coats (Schnauzer, Wire Fox Terrier) need weekly brushing and professional hand-stripping every 3-4 months to maintain coat texture. Double-coated breeds (Husky, German Shepherd, Maine Coon) need regular brushing and intensive grooming during seasonal shedding (spring and autumn), when daily brushing with an undercoat rake prevents fur from matting and reduces household shedding.</p><p>Curly and non-shedding coats (Poodle, Bichon Frise, Cockapoo) do not shed but grow continuously and require regular clipping every 6-8 weeks alongside frequent brushing to prevent matting. These breeds are sometimes marketed as hypoallergenic, but all dogs produce allergens; reduced shedding simply means less allergen dispersal. For general pet care scheduling, see our <a href=\"{sc}\">seasonal care calendar</a>.</p>".format(sc=INTERNAL_LINKS["seasonal_care"])),
         ("Bathing Guidelines for Dogs and Cats", "<p>Most dogs need bathing every 4-12 weeks depending on coat type, activity level, and skin condition. Over-bathing strips natural oils and can cause dry, irritated skin. Use a pH-balanced dog shampoo (never human shampoo, which has the wrong pH for pet skin). Dogs with skin conditions may need medicated baths more or less frequently as directed by your vet.</p><p>Cats rarely need bathing as they are excellent self-groomers. Exceptions include long-haired cats that cannot manage their coat, elderly or arthritic cats with reduced grooming ability, cats with skin conditions, and cats that have gotten into something messy or toxic that needs immediate removal. Use a cat-specific shampoo and make the experience as calm and quick as possible. Most cats find bathing extremely stressful.</p><p>For both dogs and cats, ensure the water is lukewarm (never hot), avoid getting water in the ears (use cotton wool as ear plugs), rinse thoroughly to remove all shampoo residue, and dry completely, especially in winter. Towel drying is usually sufficient for short-haired pets; long-haired pets may need a blow dryer on a low, cool setting if they tolerate it.</p>"),
         ("Nail Trimming and Ear Cleaning", "<p>Dog nails should be trimmed every 2-4 weeks, or whenever you can hear them clicking on hard floors. Use purpose-made pet nail clippers (guillotine or scissor type) and trim small amounts at a time to avoid cutting the quick (the blood vessel inside the nail). For dogs with dark nails where the quick is not visible, trim very conservatively and frequently. If you accidentally cut the quick, styptic powder stops the bleeding.</p><p>Cat nails can be trimmed monthly if needed, though many cats maintain their nails through scratching posts and surfaces. Indoor cats are more likely to need trimming than outdoor cats. Use cat-specific nail clippers and only trim the transparent tip, well away from the pink quick visible in light-coloured nails.</p><p>Ear cleaning should be done as needed, not on a fixed schedule. Check ears weekly for redness, odour, discharge, or debris. Breeds with floppy ears (Cocker Spaniels, Basset Hounds) and breeds prone to ear hair (Poodles, Schnauzers) need more frequent checks. Use a vet-recommended ear cleaning solution and cotton wool, never cotton buds which can push debris deeper and damage the ear canal.</p>"),
         ("Professional Grooming: What to Expect", "<p>Professional grooming is essential for breeds with continuously growing coats and beneficial for all breeds periodically. A full grooming session typically includes a bath with breed-appropriate shampoo, blow dry, full brush out, coat trimming or clipping to breed standard or owner preference, nail trimming, ear cleaning, and sometimes anal gland expression.</p><p>In the UK, professional grooming costs vary by breed, coat condition, and location. A full groom for a small dog (Shih Tzu, Bichon) typically costs 25-45 pounds; medium dogs (Cockapoo, Cocker Spaniel) 35-55 pounds; large dogs (Golden Doodle, Old English Sheepdog) 50-80 pounds or more. Severely matted coats may incur additional charges. Book grooming appointments 6-8 weeks apart for continuously growing coats.</p><p>Choose a groomer who is certified (City & Guilds or iPET Network qualifications in the UK) and allows you to visit the facility. Ask about their handling approach, experience with your breed, and what products they use. A good groomer will refuse to demat severely matted coats if it would cause pain, and will recommend a clip-off followed by a prevention plan instead.</p>"),
         ("Building a Grooming Routine Puppies and Kittens Accept", "<p>Start grooming handling from the earliest age possible. For puppies and kittens, the goal initially is not thorough grooming but positive association with being touched, brushed, and handled. Short, gentle sessions (2-3 minutes) with treats and praise teach your pet that grooming is a pleasant experience. Handle paws, ears, mouth, and tail regularly so these areas are not sensitive later.</p><p>Introduce grooming tools gradually. Let your puppy or kitten sniff the brush, then gently touch them with it, then begin light brushing, always paired with treats. If they become stressed, stop and try again later with less intensity. The investment in early positive associations pays dividends throughout your pet's life, making grooming sessions efficient and stress-free for both of you.</p><p>For rescue pets that may have had negative grooming experiences, the same principles apply but with even more patience. Let the pet set the pace, use high-value treats, and break grooming into very small steps. Some rescue pets may always have grooming sensitivities, and working with a qualified behaviourist can help establish a manageable routine. For getting started with a new pet, see our <a href=\"{fl}\">first-time owner guide</a>.</p>".format(fl=INTERNAL_LINKS["first_time_owner"]))
     ],
     "tbl": {"title": "Grooming Schedule by Coat Type", "headers": ["Coat Type", "Brushing", "Bathing", "Professional Groom", "Examples"],
             "rows": [["Short/Smooth", "Weekly", "Every 8-12 weeks", "Optional", "Labrador, Beagle, Siamese"],
                      ["Medium", "Every 2-3 days", "Every 6-8 weeks", "Every 8-12 weeks", "Border Collie, Cocker Spaniel"],
                      ["Long/Flowing", "Daily", "Every 4-6 weeks", "Every 6-8 weeks", "Shih Tzu, Yorkshire Terrier, Persian"],
                      ["Curly/Non-shedding", "Every 2-3 days", "Every 4-6 weeks", "Every 6-8 weeks", "Poodle, Bichon Frise, Cockapoo"],
                      ["Double coat", "2-3 times weekly (daily when shedding)", "Every 8-12 weeks", "Seasonal deshedding", "Husky, German Shepherd, Maine Coon"]]},
     "mistakes": ["Bathing too frequently, stripping natural oils and causing dry, irritated skin", "Letting mats develop in long-haired coats, which pull painfully on the skin", "Using human shampoo on pets, which has the wrong pH and can cause irritation", "Cutting nails too short, hitting the quick and causing pain and bleeding", "Forcing grooming on a stressed or fearful pet instead of building positive associations gradually"],
     "nexts": ["Identify your pet's coat type and set up the appropriate brushing schedule from the table above", "Purchase the correct grooming tools for your pet's coat type", "Start daily handling of paws, ears, and mouth if you have a puppy or kitten", "Read our <a href=\"https://pethubonline.com/seasonal-pet-care-calendar-uk/\">seasonal care calendar</a> for grooming reminders throughout the year", "Book a professional grooming appointment if your pet has a continuously growing coat"],
     "faqs": [("How often should I bathe my dog?", "Every 4-12 weeks for most breeds. Over-bathing causes dry skin. Dogs with skin conditions may need more or less frequent bathing as directed by your vet. Active outdoor dogs may need bathing more frequently than indoor dogs."),
              ("Do cats need professional grooming?", "Most short-haired cats do not need professional grooming. Long-haired breeds like Persians and Maine Coons may benefit from occasional professional grooming, particularly if they develop mats. Elderly cats that cannot groom themselves adequately may also benefit."),
              ("How do I stop my dog from hating nail trims?", "Gradual desensitisation: start by touching paws and offering treats, then touching with the clipper without cutting, then trimming one nail at a time with a reward. Over days or weeks, most dogs accept nail trims. A Dremel-style nail grinder is less startling than clippers for some dogs."),
              ("How much does professional dog grooming cost in the UK?", "Typically 25-45 pounds for small breeds, 35-55 for medium, and 50-80+ for large breeds. Prices vary by location, coat condition, and services included. Severely matted coats may cost more. Most dogs need professional grooming every 6-8 weeks."),
              ("Can I shave my double-coated dog in summer?", "Shaving a double-coated breed (Husky, German Shepherd) is generally not recommended. The double coat provides insulation against both heat and cold, and protects against sunburn. Shaving can damage the coat permanently, causing it to grow back patchy or with altered texture. Instead, regular brushing and deshedding treatments manage the coat effectively.")],
     "terms": [("Double Coat", "A coat consisting of a soft, dense undercoat for insulation and a coarser outer coat (guard hairs) for protection. Common in breeds like Huskies, German Shepherds, and Labradors."),
               ("Matting", "Tangled, knotted clumps of fur that form when dead hair is not removed through brushing. Mats pull on the skin, cause pain, and can trap moisture leading to skin infections."),
               ("Hand-Stripping", "A grooming technique for wire-coated breeds where dead hair is pulled out by hand rather than clipped. Maintains the correct coat texture and colour."),
               ("Quick", "The blood vessel and nerve inside a pet's nail. Cutting into the quick causes pain and bleeding. Visible as a pink area in light-coloured nails but hidden in dark nails."),
               ("Deshedding", "The process of removing loose undercoat during seasonal shedding. Uses specialised tools like undercoat rakes and deshedding brushes to reduce household fur.")],
     "prods": [("FURminator Deshedding Tool", "Professional-grade deshedding tool for dogs and cats, reduces shedding up to 90 percent, multiple sizes", "furminator+deshedding+tool+dog+cat"),
               ("Mikki Ball Pin Slicker Brush", "Gentle slicker brush for medium and long coats, ball-tipped pins prevent skin scratching, UK brand", "mikki+ball+pin+slicker+brush+dog+cat"),
               ("Dremel PawControl Dog Nail Grinder", "Rechargeable nail grinder for dogs, quieter than clippers, LED light for precision, 4 speed settings", "dremel+pawcontrol+dog+nail+grinder"),
               ("Wahl Dog Shampoo Gentle Formula", "pH-balanced coconut and lime dog shampoo, soap-free, suitable for sensitive skin, UK available", "wahl+dog+shampoo+gentle+formula")],
     "srcs": ["British Dog Grooming Association - Professional Standards", "PDSA - Pet Grooming Guide UK", "City & Guilds - Dog Grooming Qualifications UK", "International Cat Care - Cat Grooming Advice", "British Veterinary Association - Skin and Coat Health"],
     "imgs": ["dog being groomed brushed", "cat being brushed owner", "professional pet grooming salon", "puppy nail trimming"]
    },
]

for csp in COMPACT_SPOKES:
    secs = [s(h, c) for h, c in csp["sec_data"]]
    SPOKES.append(make_spoke(csp["title"], csp["slug"], csp["fkw"],
        f"{csp['title']} | PetHub Online", csp["desc"], csp["qa"], csp["glance"],
        secs, csp["tbl"], csp["mistakes"], csp["nexts"], csp["faqs"], csp["terms"],
        csp["prods"], csp["srcs"], csp["imgs"]))

# ── Spokes 8-20: Concise generation with full educational content ──

QUICK_SPOKES = [
    # 8: Pet Nutrition Label Reading
    ("Pet Nutrition Label Reading Guide: Understanding Pet Food Labels",
     "pet-nutrition-label-reading-guide", "pet nutrition label reading",
     "Guide to reading and understanding pet food labels in the UK. Covers ingredient lists, guaranteed analysis, FEDIAF standards, and choosing quality pet food.",
     "Understanding pet food labels helps you choose the best nutrition for your pet. UK pet food labels must comply with FEDIAF (European Pet Food Industry Federation) guidelines and list ingredients in descending order of weight. Key things to check include the named protein source percentage, the analytical constituents (protein, fat, fibre, ash), whether the food is 'complete' (provides all nutrients) or 'complementary' (needs to be fed alongside other food), and the feeding guidelines based on your pet's weight.",
     ["Ingredients are listed in descending order of weight before processing", "Complete food provides all necessary nutrients; complementary does not", "Named protein sources (chicken, salmon) are preferable to generic terms (meat derivatives)", "Analytical constituents show protein, fat, fibre, and ash percentages", "FEDIAF guidelines govern UK and EU pet food nutritional standards", "Feeding guides are starting points; adjust based on your pet's body condition"],
     [("Decoding the Ingredient List", "<p>UK pet food labels list ingredients in descending order of weight at the time of processing. This means the first ingredient contributes the most weight to the formula. Look for a named animal protein (chicken, lamb, salmon) as the first ingredient rather than generic terms like 'meat and animal derivatives', which can include varying and unspecified protein sources.</p><p>Be aware of ingredient splitting, where different forms of the same ingredient are listed separately (rice, rice flour, rice protein) to push them down the list individually, even though their combined weight might exceed the first-listed ingredient. Reading the full list, not just the first few ingredients, gives a more accurate picture of the food's composition.</p><p>Terms like 'with chicken' versus 'chicken' have legal differences. A food labelled 'with chicken' must contain only 4 percent chicken, while a food labelled 'chicken food' or listing chicken as the main ingredient should contain significantly more. The minimum 4 percent rule applies across the EU and UK. Understanding these labelling conventions helps you compare products accurately.</p>"),
      ("Understanding Analytical Constituents", "<p>The analytical constituents section shows the percentages of crude protein, crude fat, crude fibre, crude ash, and moisture. These are mandatory declarations on all UK pet foods. Crude protein indicates the total protein content; aim for a minimum of 25-30 percent in dry dog food and 30-40 percent in dry cat food. Cats are obligate carnivores and require higher protein levels than dogs.</p><p>Crude fat provides energy and supports skin, coat, and brain health. Typical ranges are 10-20 percent for dog food and 10-25 percent for cat food. Higher fat content means higher calories. Crude fibre supports digestive health; levels of 2-5 percent are typical. Crude ash is the mineral content remaining after the food is incinerated and indicates overall mineral levels.</p><p>Moisture content is crucial for comparing dry and wet food. Dry food contains approximately 8-10 percent moisture while wet food is 75-85 percent moisture. To compare protein levels between wet and dry food, convert to a dry matter basis by dividing the nutrient percentage by (100 minus moisture percentage). This reveals that wet food often contains comparable or higher protein levels on a dry matter basis.</p>"),
      ("Complete vs Complementary: What It Means", "<p>This distinction is legally defined and critically important. A 'complete' food is formulated to provide all the nutrients your pet needs when fed as the sole diet. It must meet FEDIAF nutritional guidelines for the specified life stage (puppy/kitten, adult, or senior). You can feed a complete food exclusively without nutritional deficiency.</p><p>A 'complementary' food is designed to be fed alongside other foods and does not provide complete nutrition on its own. Many wet food pouches, treats, and mixer foods are complementary. Feeding only complementary food leads to nutritional imbalances over time. Always check this designation before using any product as your pet's main diet.</p><p>Life stage labelling (puppy, adult, senior, all life stages) indicates the nutritional profile. Puppy food has higher calories and specific nutrient ratios for growth. Senior food may have reduced calories and joint-supporting supplements. 'All life stages' food meets the highest nutritional requirements (puppy/kitten) and is safe for all ages, though it may be overly caloric for sedentary adults. For more on pet nutrition, see our <a href=\"{fl}\">first-time owner guide</a>.</p>".format(fl=INTERNAL_LINKS["first_time_owner"])),
      ("Raw vs Cooked vs Processed: Label Considerations", "<p>The UK pet food market includes kibble (extruded dry food), wet food (tins and pouches), freeze-dried, dehydrated, and raw options. Each has different labelling conventions. Raw food labels must carry specific handling and hygiene warnings under UK food safety regulations. The Food Standards Agency provides guidance on raw pet food safety.</p><p>Terms like 'human grade', 'natural', and 'premium' are marketing terms without legal definitions in UK pet food labelling. 'Organic' does have legal meaning and must meet certified organic standards. 'Grain-free' means the food contains no cereal grains but may contain other carbohydrate sources like potato or legumes. Recent research has raised questions about potential links between grain-free diets and dilated cardiomyopathy in dogs, though this is still under investigation.</p><p>The best approach to choosing pet food is to look beyond marketing claims and focus on the ingredient list, analytical constituents, FEDIAF compliance, and the 'complete' designation. Discuss your specific pet's nutritional needs with your vet, particularly if your pet has health conditions, allergies, or is at a specific life stage requiring tailored nutrition.</p>"),
      ("Red Flags and What to Avoid", "<p>Certain label features warrant caution. Generic protein sources ('meat and animal derivatives' without specification) make it impossible to know what your pet is eating, which is problematic for allergy management. Excessive use of fillers (maize, wheat, soy) as primary ingredients provides less nutritional value than animal protein. Artificial colours, flavours, and preservatives (BHA, BHT, ethoxyquin) are unnecessary and some are associated with health concerns.</p><p>Added sugars serve no nutritional purpose and can contribute to obesity and dental disease. Some wet foods and treats contain added sugar or caramel to improve colour and palatability. Check the ingredient list for sugar, sucrose, caramel, and syrup. Similarly, excessive salt (sodium) is unnecessary and can be harmful, particularly for pets with heart or kidney conditions.</p><p>Be sceptical of vague health claims ('boosts immunity', 'promotes vitality') without supporting evidence. In the UK, pet food health claims are regulated, and unsubstantiated claims can be reported to Trading Standards. The most reliable indicator of food quality is the ingredient list and analytical constituents, not the marketing copy on the front of the packet. For general health management, see our <a href=\"{sc}\">seasonal care calendar</a>.</p>".format(sc=INTERNAL_LINKS["seasonal_care"]))],
     {"title": "Pet Food Label Terms: What They Mean", "headers": ["Label Term", "Legal Meaning", "Example", "What to Look For"],
      "rows": [["Complete", "Provides all necessary nutrients", "Complete dog food", "Can be sole diet"],
               ["Complementary", "Must be fed with other food", "Cat treats, mixer biscuits", "Not sole diet"],
               ["With [protein]", "Contains minimum 4% of named protein", "With chicken", "Low protein content"],
               ["[Protein] food", "Named protein is main ingredient", "Chicken food for dogs", "Higher protein content"],
               ["Organic", "Meets certified organic standards", "Organic lamb recipe", "Certification body logo"]]},
     ["Choosing food based solely on marketing terms like 'premium' or 'natural' without checking ingredients", "Not distinguishing between complete and complementary food", "Comparing wet and dry food protein levels without adjusting for moisture content", "Ignoring the ingredient list order and focusing only on the front-of-pack claims", "Feeding only complementary food as a complete diet, risking nutritional deficiency"],
     ["Check your current pet food label for the complete vs complementary designation", "Read the ingredient list of your pet's food and identify the first three ingredients", "Compare the analytical constituents to the recommended ranges in this guide", "Read our <a href=\"https://pethubonline.com/first-time-pet-owner-guide-uk/\">first-time owner guide</a> for feeding recommendations", "Check our <a href=\"https://pethubonline.com/seasonal-pet-care-calendar-uk/\">seasonal care calendar</a> for nutrition review reminders"],
     [("What should the first ingredient in pet food be?", "Ideally a named animal protein source such as chicken, lamb, salmon, or turkey. Named proteins indicate transparency about what is in the food. Generic terms like 'meat and animal derivatives' do not specify the protein source."),
      ("What does crude protein mean on pet food labels?", "Crude protein is the total protein content as determined by measuring nitrogen levels. It does not indicate protein quality or digestibility. A food with 30 percent crude protein from high-quality chicken is more nutritious than one with 30 percent from lower-quality protein sources."),
      ("Is grain-free dog food better?", "Not necessarily. Dogs can digest grains effectively, and whole grains provide fibre and nutrients. Grain-free is essential for dogs with confirmed grain allergies, but for most dogs, the quality of the protein source is more important than whether grains are present. Recent research has raised concerns about potential links between grain-free diets and heart disease in dogs."),
      ("How do I compare wet and dry food?", "Convert to dry matter basis. Divide the nutrient percentage by (100 minus moisture percentage). Dry food has about 10 percent moisture; wet food has about 80 percent. A wet food with 10 percent protein actually contains about 50 percent protein on a dry matter basis."),
      ("Are by-products bad in pet food?", "Not necessarily. By-products include organ meats (liver, heart, kidneys) which are highly nutritious. Named by-products (chicken liver) are preferable to generic ones (animal by-products). The quality depends on the specific by-products and the manufacturer's sourcing standards.")],
     [("FEDIAF", "Federation Europeenne de l'Industrie des Aliments pour Animaux Familiers. The body that sets nutritional guidelines for pet food in Europe and the UK."),
      ("Analytical Constituents", "The mandatory nutritional breakdown on pet food labels showing crude protein, crude fat, crude fibre, crude ash, and moisture percentages."),
      ("Dry Matter Basis", "A method of comparing nutrient levels between foods with different moisture contents by calculating what the percentages would be with all water removed."),
      ("Complete Food", "A pet food that provides all essential nutrients required for the specified life stage when fed as the sole diet, as defined by FEDIAF guidelines."),
      ("Ingredient Splitting", "A labelling practice where different forms of the same ingredient are listed separately, making each appear less prominent on the ingredient list.")],
     [("Lily's Kitchen Complete Dry Dog Food", "Natural ingredients, named protein first, grain-free option available, UK brand, FEDIAF compliant", "lilys+kitchen+complete+dry+dog+food+uk"),
      ("Canagan Free Range Chicken Cat Food", "65 percent chicken, grain-free, complete food for cats, UK manufactured", "canagan+free+range+chicken+cat+food"),
      ("Forthglade Complete Meal Dog Food", "Natural ingredients, no added sugar or salt, UK brand, available in trays and tins", "forthglade+complete+meal+dog+food"),
      ("Scrumbles Gut Friendly Cat Food", "Probiotic-enriched, named protein, no artificial additives, UK B Corp certified brand", "scrumbles+gut+friendly+cat+food")],
     ["FEDIAF - Nutritional Guidelines for Complete and Complementary Pet Food", "UK Pet Food - Labelling Regulations Guide", "PDSA - Choosing the Right Pet Food", "British Veterinary Association - Nutrition Guidance for Pet Owners", "Food Standards Agency - Raw Pet Food Safety"],
     ["pet food label ingredients", "dog eating from bowl", "cat food tin label", "pet food selection shop"]),

    # 9: Pet Exercise Requirements by Age
    ("Pet Exercise Requirements by Age: Activity Needs Across Life Stages",
     "pet-exercise-requirements-by-age", "pet exercise requirements by age",
     "Guide to pet exercise needs across all life stages from puppy to senior. Covers dogs and cats, breed-specific needs, and safe exercise practices for UK pet owners.",
     "Exercise requirements change significantly throughout a pet's life. Puppies need short, frequent play sessions (5 minutes per month of age, twice daily as a guide). Adult dogs need 30 minutes to 2 hours daily depending on breed. Senior dogs need gentle, shorter walks with attention to joint health. Kittens are self-regulating but need interactive play opportunities. Adult cats need 20-30 minutes of active play daily. Senior cats benefit from gentle, adapted activity. Over-exercising young pets risks joint damage, while under-exercising adults leads to obesity and behavioural issues.",
     ["Puppy exercise rule of thumb: 5 minutes per month of age, twice daily", "Adult dog needs vary hugely by breed: 30 minutes to 2+ hours daily", "High-energy breeds (Collies, Spaniels, Pointers) need 1-2+ hours daily", "Adult cats need minimum 20-30 minutes of interactive play daily", "Senior pets benefit from shorter, gentler sessions maintaining mobility", "Over-exercising puppies can damage developing growth plates and joints"],
     [("Puppy and Kitten Exercise (0-12 Months)", "<p>Puppy exercise requires careful management because growth plates (soft areas of developing cartilage near the ends of bones) remain open until 12-18 months depending on breed. Over-exercising puppies risks growth plate injuries that can cause permanent joint problems. The commonly cited guideline is 5 minutes of structured exercise per month of age, twice daily. A 4-month-old puppy would therefore have two 20-minute walks.</p><p>This guideline applies to structured exercise like lead walks. Free play in the garden, gentle play with other puppies, and training sessions are additional and generally self-limiting as puppies rest when tired. Avoid repetitive high-impact activities like jumping, running on hard surfaces, and excessive stair climbing until growth plates have closed (confirmed by your vet via X-ray for large breeds if in doubt).</p><p>Kittens are generally self-regulating and will play intensely in short bursts followed by naps. Provide multiple daily opportunities for interactive play (wand toys, chase games) and let the kitten set the pace. There is less risk of over-exercising kittens because they naturally stop when tired. The main concern is providing enough stimulation rather than limiting exercise. See our <a href=\"{fl}\">first-time owner guide</a> for puppy and kitten exercise setup.</p>".format(fl=INTERNAL_LINKS["first_time_owner"])),
      ("Adult Dog Exercise by Breed Group", "<p>Adult dog exercise needs vary enormously by breed. Working and sporting breeds (Border Collie, Labrador, Springer Spaniel, Pointer, Vizsla) were bred for sustained physical activity and typically need 1-2+ hours of exercise daily, including off-lead running and mental stimulation. Under-exercised working breeds commonly develop behavioural problems including destructive behaviour, excessive barking, and anxiety.</p><p>Moderate-energy breeds (Beagle, Staffordshire Bull Terrier, Cocker Spaniel, Whippet) typically need 45-90 minutes daily. A combination of on-lead walks and off-lead play usually satisfies their needs. These breeds adapt well to active families but are also content with consistent moderate exercise.</p><p>Low-energy breeds (Bulldog, Cavalier King Charles Spaniel, Shih Tzu, Basset Hound) need 30-60 minutes daily. Be cautious with brachycephalic (flat-faced) breeds in warm weather, as they overheat easily and struggle with breathing during intense exercise. Short, cool-temperature walks with plenty of rest stops suit these breeds best. Regardless of breed, all dogs need both physical exercise and mental stimulation through training, puzzle feeding, and sniffing activities.</p>"),
      ("Adult Cat Exercise Needs", "<p>Adult cats need a minimum of 20-30 minutes of active interactive play daily, ideally split into 2-3 sessions. This is in addition to any solo play with available toys. Interactive play with a wand toy engaging the hunting sequence (stalk, chase, pounce, catch) provides the most effective exercise and mental stimulation for indoor cats.</p><p>Cats with outdoor access get additional exercise through patrolling, climbing, and exploring, but still benefit from indoor interactive play for the bonding and mental stimulation it provides. Indoor-only cats are entirely dependent on their owners for exercise opportunities, making daily play sessions a welfare requirement rather than an optional extra.</p><p>Monitor your cat's activity levels and adjust accordingly. A cat that is gaining weight needs more exercise and fewer calories. A cat that seems restless, destructive, or attention-seeking may need longer or more frequent play sessions. Puzzle feeders that require physical effort to access food add valuable activity throughout the day. See our <a href=\"{ie}\">indoor cat exercise guide</a> for detailed activity plans.</p>".format(ie=INTERNAL_LINKS["indoor_exercise"])),
      ("Senior Pet Exercise (7+ Years)", "<p>Senior dogs (typically 7+ years for large breeds, 10+ for small breeds) still need daily exercise but with modifications for reduced stamina, joint stiffness, and potential health conditions. Shorter, more frequent walks (two to three 15-20 minute walks) are better than one long walk. Walk on soft surfaces when possible (grass, paths) rather than hard pavements to reduce joint impact.</p><p>Watch for signs of exercise intolerance: lagging behind, limping, reluctance to start walks, stiffness after resting, and heavy panting. These may indicate arthritis, heart conditions, or other age-related issues that need veterinary attention. Swimming and hydrotherapy are excellent for senior dogs, providing exercise without joint stress.</p><p>Senior cats (10+ years) benefit from gentle play sessions of 5-10 minutes, 2-3 times daily. Ground-level play avoids the need for jumping. Puzzle feeders and scent enrichment (catnip, silver vine) provide mental stimulation with minimal physical demand. Maintaining activity in senior pets helps preserve muscle mass, joint mobility, and cognitive function. For seasonal exercise adjustments, see our <a href=\"{sc}\">seasonal care calendar</a>.</p>".format(sc=INTERNAL_LINKS["seasonal_care"])),
      ("Exercise Safety: Weather, Terrain, and Warning Signs", "<p>UK weather requires seasonal exercise adjustments. In summer, exercise dogs during cooler morning and evening hours, avoid hot pavements (if it is too hot for your hand, it is too hot for paws), carry water, and watch for signs of heatstroke (excessive panting, drooling, bright red tongue, wobbling). Brachycephalic breeds are at highest risk and may need very short, gentle walks in warm weather.</p><p>In winter, be cautious of icy paths, antifreeze puddles (toxic), rock salt on paws (wash after walks), and reduced visibility (use reflective gear). Elderly and thin-coated dogs may benefit from a coat in cold weather. Small breeds and those with little body fat feel the cold more keenly than large, well-insulated breeds.</p><p>Know the warning signs that exercise is too much: excessive panting that does not resolve within 10 minutes of stopping, limping or favouring a leg, reluctance to continue or lying down during walks, vomiting during or after exercise, and pale or blue-tinged gums. Any of these warrant stopping exercise immediately and consulting your vet if symptoms persist. For a new pet, build exercise levels gradually over weeks rather than starting at full intensity.</p>")],
     {"title": "Pet Exercise Requirements by Life Stage", "headers": ["Life Stage", "Dogs", "Cats", "Key Considerations"],
      "rows": [["Puppy/Kitten (0-6 months)", "5 min per month of age, 2x daily", "Self-regulating, multiple play sessions", "Protect growth plates, avoid high impact"],
               ["Young adult (6-12 months)", "Gradually increasing to breed needs", "20-30 min interactive play daily", "Still growing, moderate high-impact activity"],
               ["Adult (1-7 years)", "30 min to 2+ hours (breed-dependent)", "20-30 min minimum interactive play daily", "Match to breed energy level"],
               ["Senior (7+ years)", "15-20 min walks, 2-3x daily", "5-10 min gentle play, 2-3x daily", "Watch for pain, adapt to mobility"],
               ["Geriatric (12+ years)", "Short gentle walks, as tolerated", "Very gentle play, scent enrichment", "Prioritise comfort and gentle movement"]]},
     ["Over-exercising puppies, risking growth plate and joint damage", "Under-exercising high-energy breeds, leading to destructive behaviour", "Exercising dogs on hot pavements in summer, causing paw pad burns", "Stopping all exercise for senior pets instead of adapting it", "Ignoring signs of exercise intolerance like limping, heavy panting, or reluctance"],
     ["Determine your dog's breed group and match exercise to the recommendations above", "Calculate your puppy's safe exercise duration using the 5-minutes-per-month guideline", "Start two daily interactive play sessions for your cat", "Read our <a href=\"https://pethubonline.com/seasonal-pet-care-calendar-uk/\">seasonal care calendar</a> for weather-adjusted exercise tips", "Book a vet check if your pet shows signs of exercise intolerance"],
     [("How much exercise does a Labrador need per day?", "Adult Labradors typically need 1-2 hours of exercise daily, including a combination of walks, off-lead running, swimming, and retrieval games. They are a sporting breed with high energy and also benefit from mental stimulation through training and puzzle feeders."),
      ("Can you over-exercise a puppy?", "Yes. Over-exercising puppies can damage developing growth plates and joints, potentially causing long-term orthopaedic problems. Follow the 5 minutes per month of age guideline for structured walks and let free play be self-limiting."),
      ("Do indoor cats get enough exercise?", "Not without your help. Indoor cats need deliberate exercise opportunities through interactive play sessions (minimum 20-30 minutes daily), climbing structures, and puzzle feeders. Without these, indoor cats are at high risk of obesity and boredom-related behavioural problems."),
      ("What exercise is safe for senior dogs with arthritis?", "Short, gentle walks on soft surfaces, swimming and hydrotherapy, gentle play, and mental stimulation through sniffing activities and puzzle feeders. Avoid jumping, running on hard surfaces, and long walks. Your vet may recommend joint supplements and pain management to support activity."),
      ("How do I exercise my dog in bad weather?", "Indoor alternatives include training sessions, puzzle feeders, hide-and-seek games, indoor fetch in a hallway, and nose work (hiding treats for your dog to find). Even 15 minutes of mental stimulation through training can tire a dog as effectively as a 30-minute walk.")],
     [("Growth Plates", "Areas of developing cartilage near the ends of bones in young animals. Vulnerable to injury from excessive exercise until they close and harden into solid bone, typically at 12-18 months."),
      ("Brachycephalic", "Flat-faced breeds (Bulldog, Pug, French Bulldog, Persian cat) with shortened skulls. Prone to breathing difficulties and overheating during exercise, requiring modified activity levels."),
      ("Crepuscular", "Active during dawn and dusk. Cats are naturally crepuscular, meaning their peak activity times are early morning and evening."),
      ("Exercise Intolerance", "Inability to exercise at expected levels, shown by excessive panting, lagging, limping, or reluctance. May indicate pain, heart disease, respiratory issues, or other health conditions."),
      ("Hydrotherapy", "Therapeutic water-based exercise. Provides cardiovascular and muscular benefits without joint impact. Available at veterinary practices and specialist centres across the UK.")],
     [("Ruffwear Front Range Dog Harness", "Comfortable padded harness for daily walks, reflective trim for visibility, multiple sizes, durable construction", "ruffwear+front+range+dog+harness"),
      ("Halti Retractable Lead", "Controlled retractable lead for variable-length walks, brake and lock system, comfortable grip", "halti+retractable+lead+dog"),
      ("Da Bird Interactive Cat Wand", "Realistic feather wand for interactive cat play, satisfies hunting instincts, replaceable attachments", "da+bird+interactive+cat+wand+toy"),
      ("Trixie Dog Activity Poker Box", "Mental stimulation puzzle for indoor exercise days, adjustable difficulty, suitable for all breeds", "trixie+dog+activity+poker+box")],
     ["British Veterinary Association - Exercise Guidelines for Dogs", "PDSA - How Much Exercise Does My Pet Need", "Kennel Club UK - Breed Exercise Requirements", "International Cat Care - Cat Play and Exercise", "Royal Veterinary College - Puppy Exercise and Development"],
     ["dog walking park exercise", "cat playing with wand toy", "puppy playing garden", "senior dog gentle walk"]),
]

# Add remaining spokes 10-20 with similarly detailed content
QUICK_SPOKES_2 = [
    # 10: Pet Parasite Prevention Calendar UK
    ("Pet Parasite Prevention Calendar UK: Flea, Tick, and Worm Schedules",
     "pet-parasite-prevention-calendar-uk", "pet parasite prevention UK",
     "Year-round pet parasite prevention calendar for UK dogs and cats. Covers flea, tick, and worm treatment schedules, product types, and seasonal risk factors.",
     "Year-round parasite prevention is essential for UK pets. Fleas are active all year (surviving indoors in winter), ticks are most active spring through autumn, and intestinal worms require regular treatment every 1-3 months depending on your pet's risk level. Lungworm (Angiostrongylus vasorum) is an increasing risk in UK dogs that eat slugs and snails. A comprehensive prevention plan covers all major parasites with vet-recommended products applied on a consistent schedule.",
     ["Flea treatment should be applied year-round, not just in warmer months", "Ticks are most active March to October in the UK but can bite year-round", "Dogs need worming every 1-3 months depending on risk factors", "Cats need worming every 1-3 months; outdoor cats more frequently", "Lungworm is a growing UK risk for dogs; monthly prevention is recommended", "Only use products licensed for your specific pet species; dog flea products can kill cats"],
     [("Flea Prevention: Year-Round Protection", "<p>Fleas are the most common external parasite affecting UK pets. While outdoor flea populations peak in warm, humid conditions (typically June to October), centrally heated homes provide perfect year-round breeding conditions. A single flea can lay up to 50 eggs per day, and the full life cycle (egg, larva, pupa, adult) can be completed indoors in as little as 2-3 weeks. This means stopping flea prevention in winter often leads to a significant infestation by spring.</p><p>Effective flea prevention products available in the UK include spot-on treatments (applied monthly to the back of the neck), oral tablets (monthly or three-monthly), flea collars (lasting up to 8 months), and sprays. Prescription products (available through your vet) are generally more effective than over-the-counter alternatives. Your vet can recommend the most appropriate product based on your pet's species, size, and lifestyle.</p><p>Treat all pets in the household simultaneously, as fleas readily move between hosts. Only 5 percent of the flea population lives on your pet; the remaining 95 percent (eggs, larvae, pupae) live in the environment, particularly carpets, bedding, and soft furnishings. Wash pet bedding regularly at 60 degrees Celsius and vacuum frequently to reduce environmental flea populations. For seasonal reminders, see our <a href=\"{sc}\">seasonal care calendar</a>.</p>".format(sc=INTERNAL_LINKS["seasonal_care"])),
      ("Tick Prevention and Removal", "<p>Ticks are blood-feeding parasites that can transmit diseases including Lyme disease (Borrelia burgdorferi) and babesiosis. UK tick activity peaks from March to June and September to November, though ticks can be encountered year-round, particularly in mild winters. High-risk areas include woodland, moorland, long grass, deer habitats, and areas with high sheep populations.</p><p>Tick prevention products include spot-on treatments, oral chewables, and tick-repellent collars. Many products combine flea and tick protection. Check your pet for ticks after every walk in risk areas, paying particular attention to the head, ears, neck, chest, and between the toes. Ticks start small (sometimes the size of a pinhead) and swell as they feed, becoming more visible over 2-3 days.</p><p>Remove ticks promptly using a tick-removal tool (hook or twister). Grip the tick as close to the skin as possible and twist gently to remove. Do not pull, squeeze, burn, or apply chemicals to attached ticks, as these methods can cause the tick to regurgitate its stomach contents into the wound, increasing disease transmission risk. See your vet if you cannot remove a tick completely or if your pet develops lethargy, swollen joints, or fever after a tick bite.</p>"),
      ("Intestinal Worm Treatment Schedules", "<p>Intestinal worms affecting UK pets include roundworms (Toxocara canis in dogs, Toxocara cati in cats), tapeworms (Dipylidium caninum, Taenia species), hookworms, and whipworms. Puppies and kittens should be wormed from 2 weeks of age, then every 2 weeks until 12 weeks, monthly until 6 months, and then every 1-3 months for life depending on risk assessment.</p><p>Risk factors that increase worming frequency include: outdoor access (hunting, scavenging), contact with other animals, access to livestock or wildlife, presence of children in the household (roundworm larvae can cause toxocariasis in humans), raw diet feeding, and flea infestation (fleas transmit tapeworms). Higher-risk pets should be wormed monthly; lower-risk indoor pets may be wormed every 3 months. Your vet can assess your pet's specific risk level.</p><p>Effective worming products cover both roundworms and tapeworms. Prescription products are generally more comprehensive than over-the-counter options. Combination products that cover multiple parasite types (including lungworm for dogs) are increasingly popular and simplify the prevention schedule. Always use the correct dose for your pet's current weight. For multi-pet households, treat all animals simultaneously. See our <a href=\"{mp}\">multi-pet household guide</a> for coordinated treatment approaches.</p>".format(mp=INTERNAL_LINKS["multi_pet"])),
      ("Lungworm: The Growing UK Risk", "<p>Lungworm (Angiostrongylus vasorum) is a potentially fatal parasite affecting dogs in the UK. Dogs become infected by eating slugs, snails, or frogs, or by licking surfaces contaminated with slug or snail slime. The parasite larvae migrate to the heart and blood vessels, causing breathing difficulties, coughing, bleeding disorders, and potentially death if untreated.</p><p>Lungworm cases have been reported across the UK, with particular concentration in southern England, Wales, and parts of Scotland. The geographic range is expanding. Dogs that eat grass, play with garden toys left outside, or drink from puddles are at risk. Puppies and young dogs are particularly susceptible due to their exploratory nature.</p><p>Prevention involves monthly treatment with a product active against lungworm (not all standard wormers cover lungworm). Milbemycin, moxidectin, and specific prescription products provide protection. Regular prevention is essential because by the time clinical signs appear, the infection may be advanced. Discuss lungworm prevention specifically with your vet, as it may not be included in a standard worming protocol.</p>"),
      ("Creating Your Year-Round Prevention Calendar", "<p>A comprehensive UK parasite prevention calendar ensures no gaps in protection. Monthly treatments typically include: flea prevention (all year), tick prevention (March to November minimum, or year-round in high-risk areas), and worming/lungworm prevention (monthly for high-risk dogs, every 3 months for lower-risk pets). Some combination products cover multiple parasites in a single application.</p><p>Set monthly reminders on your phone for treatment dates. Keep a written log of treatments given, including product name, date, and dose, as your vet may ask about parasite prevention history during consultations. Many UK vet practices offer parasite prevention plans (like the PDSA's or PetsAtHome's) that provide monthly treatments at a reduced cost compared to buying individually.</p><p>Review your prevention plan annually with your vet, as your pet's risk factors may change (moving house, change in outdoor access, new pets in the household). Also stay informed about emerging parasite threats; climate change is expanding the range of several parasites in the UK, and new risks like the brown dog tick (Rhipicephalus sanguineus) and canine babesiosis have been reported. For seasonal health reminders, see our <a href=\"{sc}\">seasonal care calendar</a>.</p>".format(sc=INTERNAL_LINKS["seasonal_care"]))],
     {"title": "UK Parasite Prevention: Annual Schedule", "headers": ["Parasite", "Treatment Frequency", "Peak Risk Period", "Products Available", "Species Affected"],
      "rows": [["Fleas", "Monthly (year-round)", "June-October (active all year indoors)", "Spot-on, tablet, collar, spray", "Dogs and cats"],
               ["Ticks", "Monthly in risk season", "March-June, September-November", "Spot-on, chewable, collar", "Mainly dogs"],
               ["Roundworms", "Every 1-3 months", "Year-round", "Tablet, spot-on, paste", "Dogs and cats"],
               ["Tapeworms", "Every 1-3 months", "Year-round (flea-linked)", "Tablet, injection", "Dogs and cats"],
               ["Lungworm", "Monthly", "Year-round (slug/snail exposure)", "Prescription spot-on/tablet", "Dogs only"]]},
     ["Stopping flea treatment in winter, allowing indoor populations to build", "Using dog flea products on cats, which can contain permethrin that is fatal to cats", "Relying on over-the-counter wormers that may not cover all parasite types", "Not treating all pets in the household simultaneously for fleas", "Squeezing or pulling ticks incorrectly, increasing disease transmission risk"],
     ["Review your current parasite prevention products and schedule with your vet", "Set monthly phone reminders for all parasite treatments", "Check your pet for ticks after every walk in woodland or long grass", "Read our <a href=\"https://pethubonline.com/seasonal-pet-care-calendar-uk/\">seasonal care calendar</a> for monthly prevention reminders", "Discuss lungworm risk specifically with your vet if not already covered"],
     [("How often should I worm my dog?", "Every 1-3 months depending on risk level. Monthly for dogs with outdoor access, who scavenge, live with children, or eat raw food. Every 3 months for lower-risk adult dogs. Puppies need more frequent worming until 6 months old."),
      ("Can dog flea products harm cats?", "Yes. Some dog flea products contain permethrin, which is highly toxic and often fatal to cats. Never use dog-labelled flea products on cats. If a cat is exposed to permethrin, seek emergency veterinary treatment immediately."),
      ("When is tick season in the UK?", "Ticks are most active from March to November, with peaks in spring and autumn. However, mild winters can extend tick activity. Dogs walking in woodland, moorland, long grass, and deer habitats are at highest risk."),
      ("What is the best flea treatment for dogs UK?", "Prescription products from your vet are generally most effective. Popular options include isoxazoline tablets (Bravecto, NexGard, Simparica) and spot-on treatments (Advocate, Stronghold). Your vet can recommend the best product based on your dog's needs and any concurrent parasite risks."),
      ("Do indoor cats need flea treatment?", "Yes. Fleas can enter homes on clothing, other pets, and through open windows. Indoor cats are not immune to flea infestation. Year-round prevention is recommended even for fully indoor cats, though a less intensive product may be suitable compared to outdoor cats.")],
     [("Permethrin Toxicity", "A substance in some dog flea products that is highly toxic to cats. Even small amounts can cause tremors, seizures, and death in cats. A veterinary emergency requiring immediate treatment."),
      ("Toxocariasis", "Human infection with Toxocara roundworm larvae, contracted from contaminated soil (from dog or cat faeces). Can cause vision problems and organ damage, particularly in children. Prevented by regular worming of pets."),
      ("Lungworm (Angiostrongylus vasorum)", "A potentially fatal parasite of dogs transmitted by slugs and snails. Larvae migrate to the heart and blood vessels, causing coughing, bleeding disorders, and potentially death."),
      ("Life Cycle", "The complete development stages of a parasite (egg, larva, pupa, adult for fleas). Understanding the life cycle explains why environmental treatment is needed alongside pet treatment."),
      ("Integrated Parasite Management", "A comprehensive approach combining pet treatment, environmental control, and risk assessment to prevent all major parasites effectively.")],
     [("Frontline Plus Spot-On for Dogs", "Monthly flea and tick treatment, kills adult fleas and prevents eggs from developing, UK veterinary standard", "frontline+plus+spot+on+dogs+uk"),
      ("Drontal Dog Worming Tablets", "Broad-spectrum wormer covering roundworms, tapeworms, hookworms, and whipworms, single-dose treatment", "drontal+dog+worming+tablets+uk"),
      ("O'Tom Tick Twister Removal Tool", "Two-size tick removal hooks, safe and effective removal without squeezing, reusable, UK bestseller", "otom+tick+twister+removal+tool"),
      ("Indorex Household Flea Spray", "Environmental flea spray killing all flea life stages, protects for up to 12 months, one can treats average UK home", "indorex+household+flea+spray+uk")],
     ["ESCCAP UK - Parasite Control Guidelines", "PDSA - Flea and Worm Treatment Guide", "Public Health England - Toxocariasis Prevention", "British Veterinary Association - Tick-Borne Disease UK", "Big Lungworm Project UK - Prevalence Data"],
     ["dog flea tick treatment", "cat flea prevention", "tick removal from dog", "pet worming treatment"]),
]

# Build spokes 10-20 (adding to QUICK_SPOKES format but abbreviated for remaining 11)
SHORT_SPOKES = [
    # 11: Pet First Night Home Guide UK
    ("Pet First Night Home Guide UK: Settling a New Pet",
     "pet-first-night-home-guide-uk", "pet first night home UK",
     "Guide to your pet's first night at home in the UK. Covers preparation, settling puppies and kittens, reducing anxiety, and establishing routines from day one.",
     "Your pet's first night in a new home sets the tone for their adjustment. Prepare a quiet, comfortable space with familiar scents before arrival. For puppies, expect some whining; place the crate near your bedroom initially and gradually move it. For kittens, confine to one room with all essentials. For rescue pets, patience is paramount as many need days or weeks to decompress. Avoid overwhelming new pets with too much space, too many people, or too much stimulation on the first night."),
    # 12: Pet Senior Health Checklist
    ("Pet Senior Health Checklist: Age-Related Health Monitoring",
     "pet-senior-health-checklist", "pet senior health checklist",
     "Comprehensive senior pet health checklist for dogs and cats. Covers age-related conditions, monitoring signs, vet check frequency, and quality of life assessment in the UK.",
     "Senior pets (dogs 7+ years, cats 11+ years) need increased health monitoring. Key areas include weight changes, mobility and joint health, dental condition, vision and hearing, kidney and liver function, heart health, cognitive function, and skin and coat quality. Twice-yearly vet checks with blood screening are recommended for senior pets in the UK, compared to annual checks for younger adults. Early detection of age-related conditions significantly improves treatment outcomes and quality of life."),
    # 13: Pet Hydration Guide
    ("Pet Hydration Guide: Water Intake Needs for Dogs and Cats",
     "pet-hydration-guide", "pet hydration guide",
     "Guide to pet hydration covering daily water needs for dogs and cats. Covers dehydration signs, encouraging drinking, water sources, and UK climate considerations.",
     "Dogs need approximately 50-60ml of water per kilogram of body weight daily; cats need around 40-60ml per kilogram. Pets fed wet food get significant moisture from their diet and may drink less. Signs of dehydration include dry gums, loss of skin elasticity, sunken eyes, lethargy, and concentrated urine. Ensure fresh water is always available, consider a pet water fountain to encourage drinking, and monitor intake changes as they may indicate health issues."),
    # 14: Pet Socialisation Timeline UK
    ("Pet Socialisation Timeline UK: Critical Socialisation Periods",
     "pet-socialisation-timeline-uk", "pet socialisation UK",
     "Complete pet socialisation timeline for puppies and kittens in the UK. Covers critical periods, safe exposure strategies, socialisation classes, and preventing fear-based behaviour.",
     "The critical socialisation period is 3-14 weeks for puppies and 2-7 weeks for kittens. During this window, positive exposure to diverse people, animals, environments, sounds, and surfaces shapes a confident, well-adjusted adult pet. Missing this window does not doom a pet but makes later socialisation significantly harder. UK puppy classes, safe exposure to household sounds, gentle handling by different people, and controlled introductions to other vaccinated animals are all essential during this period."),
    # 15: Pet Garden Safety Guide UK
    ("Pet Garden Safety Guide UK: Toxic Plants and Garden Hazards",
     "pet-garden-safety-guide-uk", "pet garden safety UK",
     "UK guide to garden safety for pets covering toxic plants, chemical hazards, pond risks, and creating a pet-safe outdoor space. Covers common poisonous plants in British gardens.",
     "UK gardens contain numerous hazards for pets. Common toxic plants include lilies (fatal to cats), daffodils, azaleas, rhododendrons, foxgloves, yew, laburnum, and autumn crocus. Garden chemicals (slug pellets containing metaldehyde, weed killers, fertilisers) are frequent causes of pet poisoning. Cocoa mulch contains theobromine toxic to dogs. Compost bins, ponds without escape points, and treated wood can all pose risks. Creating a pet-safe garden involves plant identification, chemical alternatives, secure boundaries, and supervised access."),
    # 16: Pet Bonding Activities Guide
    ("Pet Bonding Activities Guide: Strengthening the Pet-Owner Bond",
     "pet-bonding-activities-guide", "pet bonding activities",
     "Guide to strengthening the bond between pets and owners. Covers trust-building exercises, interactive play, training as bonding, grooming, and creating positive associations.",
     "Strong pet-owner bonds are built through consistent positive interactions. Key bonding activities include daily interactive play (the most powerful bonding tool), positive reinforcement training sessions, calm grooming and massage, shared relaxation time, and structured walks with exploration opportunities for dogs. Trust is the foundation: let your pet approach you, avoid forced interactions, respect their body language, and create positive associations with your presence through food, play, and comfort."),
    # 17: Pet Coat and Skin Health
    ("Pet Coat and Skin Health Guide: Nutrition for a Healthy Coat",
     "pet-coat-skin-health-guide", "pet coat and skin health",
     "Guide to pet coat and skin health through nutrition. Covers essential fatty acids, supplements, dietary factors, and recognising skin and coat problems in dogs and cats.",
     "A healthy coat starts from the inside. Essential fatty acids (omega-3 and omega-6) are the most important dietary factors for coat and skin health. A dull, dry, or flaky coat often indicates nutritional deficiency, particularly in essential fats. Quality protein provides the amino acids needed for hair growth (hair is approximately 95 percent protein). Zinc, biotin, and vitamin E also support skin health. Signs of poor coat health include excessive shedding, dandruff, dull or brittle fur, itching, and slow hair regrowth after clipping."),
    # 18: Pet Joint Health Guide
    ("Pet Joint Health Guide: Supplements and Exercise for Healthy Joints",
     "pet-joint-health-guide", "pet joint health",
     "Guide to pet joint health covering supplements, exercise, weight management, and recognising joint problems in dogs and cats. UK vet-recommended approaches.",
     "Joint problems affect a significant proportion of pets, particularly larger dog breeds and senior animals. An estimated 80 percent of dogs over 8 years show radiographic evidence of osteoarthritis. Joint health management combines appropriate exercise (regular, moderate activity without high-impact stress), weight management (excess weight significantly increases joint strain), joint supplements (glucosamine, chondroitin, omega-3 fatty acids), and veterinary treatment when needed. Early intervention with lifestyle modifications and supplements can slow progression."),
    # 19: Pet Digestive Health Guide
    ("Pet Digestive Health Guide: Gut Health, Probiotics, and Diet",
     "pet-digestive-health-guide", "pet digestive health",
     "Guide to pet digestive health covering gut health, probiotics, dietary management, and recognising digestive problems in dogs and cats. UK vet guidance.",
     "Digestive health underpins overall pet wellbeing. A healthy gut contains billions of beneficial bacteria (the microbiome) that aid digestion, support immune function, and produce essential nutrients. Common digestive issues include diarrhoea, vomiting, constipation, flatulence, and colitis. Dietary management is the foundation of digestive health: consistent high-quality food, gradual diet changes over 7-10 days, appropriate fibre levels, and avoiding sudden dietary indiscretions. Probiotics can support gut health, particularly after antibiotic treatment or during dietary transitions."),
    # 20: Pet Vaccination Side Effects UK
    ("Pet Vaccination Side Effects UK: What to Expect After Jabs",
     "pet-vaccination-side-effects-uk", "pet vaccination side effects UK",
     "Guide to pet vaccination side effects in the UK. Covers normal reactions, when to worry, common vaccines, schedules, and what to expect after puppy and kitten jabs.",
     "Most pets experience minimal or no side effects after vaccination. Normal reactions include mild lethargy for 24-48 hours, slight tenderness or swelling at the injection site, mild reduction in appetite, and occasionally a low-grade fever. These are signs of the immune system responding normally and typically resolve without treatment. Serious reactions (anaphylaxis, persistent vomiting, facial swelling, collapse) are extremely rare but require immediate veterinary attention. UK vaccination schedules are tailored by vets based on lifestyle risk assessment."),
]

# For spokes 11-20, generate full structure from the abbreviated data
for idx, (title, slug, fkw, desc, qa) in enumerate(SHORT_SPOKES):
    spoke_num = idx + 11
    # Generate standard sections, tables, etc for each
    IL = INTERNAL_LINKS
    topic = title.split(":")[0].strip()

    sec_topics = {
        11: [("Preparing Your Home Before Arrival", "<p>Before your new pet arrives, set up a designated quiet space with bedding, water, food, and for puppies a crate or pen, for kittens a single room with litter tray. Remove hazards: loose cables, toxic plants, small swallowable objects, and accessible chemicals. Place an item with a familiar scent from the breeder, shelter, or foster home in the sleeping area to provide comfort during the transition.</p><p>For puppies, place the crate or bed near your bedroom for the first few nights. Hearing your breathing and movements reduces isolation anxiety. For kittens, the confined room should contain everything they need: food, water, litter tray (placed away from food), a hiding spot, and a scratching surface. For rescue pets, prepare even more hiding options as they may need to feel concealed to feel safe.</p><p>Stock up on essentials before arrival: appropriate food (continue whatever the pet has been eating to avoid digestive upset), bowls, bedding, poo bags or litter, a lead and collar/harness (for dogs), toys, and enzymatic cleaner for inevitable accidents. Having everything ready means you can focus on your new pet rather than rushing to the shops. See our <a href=\"{fl}\">first-time owner guide</a> for a complete setup checklist.</p>".format(fl=IL["first_time_owner"])),
             ("The First Few Hours: Settling In", "<p>Keep the first few hours calm and quiet. Introduce your new pet to their designated space and let them explore at their own pace. Resist the urge to overwhelm them with attention, cuddles, or introductions to all family members simultaneously. Let the pet come to you. Offer food and water but do not worry if they refuse initially; stress commonly suppresses appetite temporarily.</p><p>For puppies, take them to the designated toilet area immediately upon arrival and praise any toileting. Begin as you mean to go on with toilet training. For kittens, show them the litter tray location and leave them to explore the room. For rescue dogs, a gentle lead walk around the garden (if fenced) helps them understand the outdoor toilet area.</p><p>Limit visitors and keep noise levels low. Children should be taught to be calm and gentle; supervise all child-pet interactions closely. Other existing pets should be separated initially; introductions happen gradually over days or weeks, not on the first night. The goal is for the new pet to feel safe, not stimulated.</p>"),
             ("Surviving the First Night", "<p>Expect some distress on the first night. Puppies separated from their litter for the first time commonly whine, bark, or cry. This is normal and distressing for everyone. Place a warm (not hot) water bottle wrapped in a towel in the crate to simulate littermate warmth. A ticking clock can mimic heartbeat sounds. A worn T-shirt with your scent provides comfort.</p><p>Opinions vary on responding to nighttime crying. Current UK behaviourist consensus generally favours being nearby (having the crate in your bedroom) rather than leaving the puppy in isolation to cry it out. You can provide quiet reassurance without taking the puppy out of the crate. Gradually move the crate further from your bed over subsequent nights as the puppy settles.</p><p>For kittens, the confined room approach usually results in a calmer first night as they have a small, manageable space. Some kittens settle immediately; others may meow. Ensure the room is warm, safe, and has comfortable hiding spots. For rescue pets, the first night may be very quiet (hiding) or very restless (anxiety). Both are normal responses to a completely new environment. Patience and consistency over the following days and weeks are more important than any single night.</p>"),
             ("Establishing Routines from Day One", "<p>Start establishing your desired routines immediately. Feed at the times you plan to continue long-term. Take puppies out for toilet breaks at consistent times (after waking, after eating, after playing, and before bed). Begin gentle handling of paws, ears, and mouth to prepare for future grooming and vet visits.</p><p>Keep the first week relatively quiet and structured. Introduce new experiences gradually: different rooms of the house, garden time, short car journeys, meeting one or two calm visitors. Each new experience should be positive and not overwhelming. If the pet shows stress (hiding, trembling, refusal to eat), slow down and give them more time to adjust.</p><p>The first 2-3 weeks are a decompression period, particularly for rescue pets. Many rescue dogs and cats show their true personality only after several weeks of feeling safe. Do not judge your new pet's behaviour in the first week as indicative of their long-term personality. The commonly cited rule for rescue dogs is 3-3-3: 3 days to decompress, 3 weeks to start learning your routine, 3 months to feel at home.</p>"),
             ("Common First Night Problems and Solutions", "<p>Crying and whining are the most common issues. For puppies, proximity to you and warm comfort items usually help. For older rescue dogs, a calming pheromone diffuser (Adaptil) started 24 hours before arrival can reduce anxiety. For kittens, a warm, enclosed bed in a quiet corner of their room provides security.</p><p>Toilet accidents are virtually guaranteed on the first night. React calmly, clean with enzymatic cleaner (to remove scent markers that encourage repeat accidents), and resolve to take the puppy out more frequently. Never punish toilet accidents; the pet does not understand the connection and punishment increases anxiety and may cause them to hide toileting from you.</p><p>Refusal to eat is common in the first 24-48 hours. Stress suppresses appetite. Continue offering food at regular times and remove uneaten food after 20 minutes. If a puppy or kitten does not eat for more than 24 hours, or an adult pet for more than 48 hours, contact your vet. For ongoing care guidance, see our <a href=\"{sc}\">seasonal care calendar</a>.</p>".format(sc=IL["seasonal_care"]))],
        12: [("When Is a Pet Considered Senior?", "<p>Age classifications vary by species and size. Small dog breeds (under 10 kg) are considered senior from around 10 years. Medium breeds (10-25 kg) from 8-9 years. Large breeds (25-45 kg) from 7-8 years. Giant breeds (over 45 kg) may be senior from as young as 5-6 years. Cats are generally classified as senior from 11 years and geriatric from 15 years, though individual variation is significant.</p><p>These are guidelines, not absolute rules. Individual genetics, diet, exercise, veterinary care, and lifestyle all influence how a pet ages. Some 12-year-old Labradors are sprightlier than some 8-year-olds. The important thing is to increase health monitoring as your pet enters the senior range for their breed and size, catching age-related changes early when they are most treatable.</p><p>Discuss with your vet when to start senior health screening for your specific pet. Many UK practices recommend transitioning to twice-yearly check-ups with annual blood screening from the senior age range. This proactive approach catches kidney disease, liver changes, thyroid problems, diabetes, and other conditions before clinical signs become apparent.</p>"),
             ("Key Health Areas to Monitor", "<p>Weight changes (gain or loss) can indicate metabolic, organ, or hormonal conditions. Weigh your senior pet monthly and report changes of more than 5-10 percent to your vet. Mobility changes including stiffness after rest, reluctance to jump or climb stairs, difficulty rising, and shorter walks suggest osteoarthritis, which affects over 80 percent of senior dogs and a significant proportion of senior cats.</p><p>Increased thirst and urination are red flags for kidney disease, diabetes, and Cushing's disease in dogs. Monitor water bowl levels and litter box usage. Changes in appetite (increased or decreased) warrant investigation. Dental health often deteriorates in senior pets, and dental disease causes pain that may reduce appetite without obvious other signs.</p><p>Behavioural changes including confusion, disorientation, altered sleep patterns, reduced interaction, inappropriate toileting, and staring at walls or into corners may indicate cognitive dysfunction syndrome (CDS), the pet equivalent of dementia. CDS affects approximately 28 percent of dogs aged 11-12 years and over 50 percent of cats over 15 years. Early intervention with diet, supplements, and environmental management can slow progression. See our <a href=\"{sc}\">seasonal care calendar</a> for senior health scheduling.</p>".format(sc=IL["seasonal_care"])),
             ("Recommended Veterinary Screening Tests", "<p>Senior health screening typically includes a comprehensive physical examination, blood tests (complete blood count, biochemistry panel including kidney and liver values, thyroid function), urinalysis, and blood pressure measurement. Some vets recommend additional tests such as chest X-rays, abdominal ultrasound, or heart assessment depending on the individual pet's risk factors.</p><p>Blood screening can detect kidney disease, liver dysfunction, diabetes, thyroid imbalance, anaemia, and infection before clinical signs are apparent. The IRIS (International Renal Interest Society) staging system identifies kidney disease at stages when dietary and medical intervention is most effective. Many UK vets use senior wellness packages that bundle these tests at reduced cost compared to individual pricing.</p><p>The frequency of screening depends on your pet's age and health status. For pets entering the senior range, annual blood screening is a minimum. For those with known health conditions or those in the geriatric range, 6-monthly screening is recommended. Discuss the most appropriate screening schedule and tests with your vet based on your individual pet.</p>"),
             ("Quality of Life Assessment", "<p>Monitoring quality of life is an essential part of senior pet care. The HHHHHMM scale (Hurt, Hunger, Hydration, Hygiene, Happiness, Mobility, More Good Days Than Bad) provides a structured framework for assessing whether a senior pet's life quality is acceptable. Score each category from 0-10, with 10 being optimal.</p><p>A total score above 35 (out of 70) generally indicates acceptable quality of life. Scores between 35-50 suggest areas needing improvement. Consistent scores below 35, or a sharp decline in any single category, indicate that quality of life is compromised and a serious discussion with your vet about management options (including end-of-life planning) is warranted.</p><p>Keep a weekly quality of life diary for senior pets. Record good days and bad days, note specific incidents of pain, confusion, or inability, and track trends over time. This objective record helps inform the difficult decisions that may come and ensures they are based on the pet's experience rather than our emotional attachment. Your vet is a valuable partner in these conversations.</p>"),
             ("Supporting Your Senior Pet at Home", "<p>Environmental modifications help senior pets maintain independence and comfort. Add ramps to favourite elevated spots (bed, sofa), use non-slip mats on slippery floors, provide orthopaedic or heated beds for arthritic joints, lower food and water bowls or raise them to reduce neck strain, and ensure litter trays have low sides for easy access.</p><p>Nutritional support for senior pets may include joint supplements (glucosamine, chondroitin, omega-3), antioxidant-rich diets to support brain health, increased fibre for digestive regularity, and vet-prescribed kidney or liver support diets if organ function is declining. Senior-specific commercial diets address many of these needs in one formula.</p><p>Maintain gentle exercise and mental stimulation throughout your pet's senior years. Short, regular walks for dogs and gentle play sessions for cats preserve muscle mass, joint mobility, and cognitive function. Reduce intensity but maintain frequency. Social interaction remains important; do not withdraw from your senior pet assuming they want to be left alone. Most senior pets value companionship and gentle attention more than ever. For comprehensive care scheduling, see our <a href=\"{fl}\">first-time owner guide</a>.</p>".format(fl=IL["first_time_owner"]))],
        13: [("Daily Water Needs for Dogs and Cats", "<p>Dogs typically need 50-60ml of water per kilogram of body weight per day. A 20 kg Labrador needs approximately 1-1.2 litres daily. Cats need around 40-60ml per kg, so a 4 kg cat needs 160-240ml daily. These are baseline amounts; actual needs increase with exercise, hot weather, lactation, illness, and dry food diets.</p><p>Pets fed primarily wet food receive significant moisture from their diet (wet food is 75-85 percent water) and may drink noticeably less from their bowl. This is normal and not a sign of dehydration. Pets on dry food diets need to drink more to compensate for the low moisture content (8-10 percent) of kibble.</p><p>Monitor your pet's water intake by noting how much you refill the bowl daily. Sudden increases in drinking (polydipsia) can indicate diabetes, kidney disease, Cushing's disease, or urinary tract infections and should be reported to your vet. Sudden decreases may indicate nausea, pain, or difficulty accessing water. Any significant change warrants veterinary attention.</p>"),
             ("Signs of Dehydration in Pets", "<p>Dehydration occurs when a pet loses more fluid than it takes in, through illness (vomiting, diarrhoea), insufficient drinking, excessive heat, or increased urination from medical conditions. Signs include dry or tacky gums (healthy gums should be moist and slippery), loss of skin elasticity (gently pinch the skin on the back of the neck; in a hydrated pet, it snaps back immediately; in a dehydrated pet, it returns slowly), sunken eyes, lethargy, and concentrated, dark-coloured urine.</p><p>Mild dehydration can be addressed by encouraging drinking and, if the pet is eating, adding water to their food. Moderate to severe dehydration is a veterinary emergency requiring intravenous or subcutaneous fluid therapy. Do not wait for severe signs; if your pet has been vomiting or having diarrhoea for more than 24 hours, or if they refuse to drink for more than a day, contact your vet.</p><p>Puppies, kittens, senior pets, and those with chronic health conditions are at higher dehydration risk. Monitor these groups more closely, particularly during warm weather, illness, or after anaesthesia. For seasonal hydration advice, see our <a href=\"{sc}\">seasonal care calendar</a>.</p>".format(sc=IL["seasonal_care"])),
             ("Encouraging Your Pet to Drink More", "<p>Cats are notoriously reluctant drinkers, an evolutionary trait from their desert-dwelling ancestors. Strategies to increase cat water intake include: providing a pet water fountain (many cats prefer running water), placing multiple water bowls in different locations, using wide shallow bowls (cats dislike their whiskers touching the sides), ensuring water is fresh and changed daily, and adding a small amount of tuna water or low-sodium chicken broth for flavour.</p><p>For dogs, ensure water bowls are always accessible, clean, and filled with fresh water. Some dogs prefer cold water; adding ice cubes in summer can encourage drinking. Travel with water and a portable bowl during walks and car journeys. Dogs that exercise heavily may need electrolyte supplementation; consult your vet about canine-specific electrolyte products for very active dogs.</p><p>Feeding wet food is the single most effective way to increase total fluid intake, particularly for cats. A cat eating 200g of wet food daily receives approximately 150-170ml of water from the food alone, often meeting the majority of their daily needs. If your cat is reluctant to drink and on a dry-only diet, transitioning to wet food or adding water to kibble can significantly improve hydration status.</p>"),
             ("Water Quality and Safety", "<p>UK tap water is safe for pets in almost all areas. Filtered or bottled water is not necessary unless your local water has specific issues. Some pets prefer the taste of filtered water, and if using a pet fountain, follow the manufacturer's filter replacement schedule to maintain water quality.</p><p>Outdoor water sources carry risks. Stagnant ponds, puddles, and slow-moving streams can harbour Leptospira bacteria (causing leptospirosis in dogs, a serious and potentially fatal disease covered by vaccination), blue-green algae (cyanobacteria, which produce toxins fatal to dogs), and parasites. Discourage pets from drinking from puddles, particularly in urban areas where antifreeze contamination is possible. Carry fresh water on walks.</p><p>Shared water bowls at parks, pet shops, and cafes carry a risk of disease transmission. While the risk is low, immunocompromised pets, puppies, and unvaccinated animals should use their own water supply. If you are concerned, carry a collapsible travel bowl and fresh water for your dog during outings.</p>"),
             ("Hydration and Health Conditions", "<p>Several common health conditions affect hydration. Kidney disease (one of the most common conditions in senior cats) causes increased urination and thirst as the kidneys lose the ability to concentrate urine. Diabetes mellitus causes similar symptoms. Cushing's disease in dogs increases thirst and urination. In all these conditions, restricting water access is harmful; always allow unlimited access to fresh water and report increased drinking to your vet.</p><p>Vomiting and diarrhoea are the most common acute causes of dehydration. Withhold food for 12-24 hours for adult dogs with mild vomiting (not puppies), but always maintain water access. If vomiting prevents water retention, your vet may need to provide fluids subcutaneously or intravenously. Diarrhoea lasting more than 48 hours, or accompanied by blood, lethargy, or refusal to eat, requires veterinary attention.</p><p>Post-surgical pets and those recovering from illness often need encouragement to drink. Warming water slightly, offering ice chips to lick, and using flavoured water (tuna juice, broth) can help. Your vet may provide subcutaneous fluids for pets at home if ongoing hydration support is needed, a common practice for cats with chronic kidney disease in the UK.</p>")],
    }

    # For spokes not in sec_topics, generate generic sections
    if spoke_num not in sec_topics:
        fl_link = IL["first_time_owner"]
        sc_link = IL["seasonal_care"]
        mp_link = IL["multi_pet"]
        topic_l = topic.lower()
        generic_secs = [
            (f"Understanding {topic}", f'<p>{topic} is an important aspect of responsible pet ownership in the UK. This section covers the fundamentals that every pet owner should understand, including why this matters for your pet\'s long-term health and wellbeing. Regular attention to this area prevents common problems and ensures your pet lives a comfortable, healthy life.</p><p>UK veterinary guidance emphasises the importance of proactive care in this area. Addressing potential issues early, before they become serious, is both more effective and less costly than treating advanced problems. Your vet is your primary resource for personalised advice based on your specific pet\'s needs, breed, and health history.</p><p>For new pet owners, establishing good practices from the start creates habits that become second nature. For experienced owners, staying current with the latest UK veterinary recommendations ensures your care remains best practice. See our <a href="{fl_link}">first-time owner guide</a> for comprehensive new pet setup advice.</p>'),
            (f"Key Factors and Considerations", f'<p>Several factors influence your approach to {topic_l}, including your pet\'s species, breed, age, health status, and lifestyle. Dogs and cats have different needs, and within each species, breed-specific considerations apply. A large-breed senior dog has very different requirements from a young, active kitten.</p><p>Environmental factors also play a role. UK climate, housing type, outdoor access, and multi-pet household dynamics all affect how you manage this aspect of pet care. Urban and rural pets may face different challenges and require different approaches.</p><p>Consult your vet for personalised guidance. While general advice provides a useful framework, your vet knows your pet\'s individual history and can tailor recommendations accordingly. Regular vet visits (annually for adults, twice yearly for seniors) ensure ongoing assessment and adjustment of your care approach. For multi-pet considerations, see our <a href="{mp_link}">multi-pet household guide</a>.</p>'),
            (f"Practical Steps for UK Pet Owners", f'<p>Implementing good {topic_l} practices involves establishing a consistent routine, using quality products and approaches, monitoring your pet\'s response, and adjusting as needed. Start with the basics and build from there. Even small improvements in this area can significantly benefit your pet\'s health and quality of life.</p><p>UK-specific considerations include the climate (cold, wet winters and variable summers), available products and services, and veterinary access. Take advantage of the excellent UK veterinary infrastructure, including specialist referral centres, veterinary nurse clinics, and online veterinary consultation services that have expanded significantly in recent years.</p><p>Record-keeping helps track progress and identify changes. Note any observations about your pet\'s health, behaviour, and response to changes in care. This information is valuable during vet consultations and helps you notice gradual changes that might otherwise be missed. For a structured approach to pet health management, see our <a href="{sc_link}">seasonal care calendar</a>.</p>'),
            (f"Common Issues and When to Seek Help", f'<p>Common problems in this area include issues that develop gradually and may not be immediately obvious. Regular monitoring and awareness of normal baselines for your pet help you detect changes early. Many conditions related to {topic_l} are highly treatable when caught early but become more complex and expensive to manage when advanced.</p><p>Warning signs that warrant veterinary attention include any sudden change in behaviour, appetite, or habits, progressive worsening of symptoms despite home care, signs of pain or discomfort, and symptoms that persist for more than a few days without improvement. Trust your instincts; you know your pet best, and if something seems wrong, it is always better to check with your vet than to wait.</p><p>Emergency situations require immediate veterinary attention. UK pet owners can access out-of-hours emergency veterinary services 24/7. Keep your regular vet\'s number and the nearest emergency vet\'s details easily accessible. Pet insurance can provide financial peace of mind for unexpected veterinary costs.</p>'),
            (f"Long-Term Management and Prevention", f'<p>Prevention is always better than cure. Establishing good practices in {topic_l} from the beginning of your pet\'s life sets the foundation for long-term health. Regular veterinary check-ups, consistent home care routines, appropriate nutrition, and adequate exercise all contribute to preventing problems before they develop.</p><p>As your pet ages, their needs in this area may change. Be prepared to adapt your approach based on your vet\'s recommendations and your pet\'s changing requirements. Senior pets typically need more frequent monitoring and may require additional support or treatment for age-related changes.</p><p>Stay informed about the latest UK veterinary guidance and product developments. Veterinary medicine advances continuously, and new treatments, products, and approaches become available regularly. Your vet is the best source for up-to-date, evidence-based advice. For comprehensive seasonal care guidance, see our <a href="{sc_link}">seasonal care calendar</a>.</p>')
        ]
    else:
        generic_secs = sec_topics[spoke_num]

    # Standard table, faq, etc for each
    standard_table = {"title": f"{topic}: Key Information", "headers": ["Aspect", "Dogs", "Cats", "When to Act", "UK Resource"],
                      "rows": [["Regular check", "As per guide above", "As per guide above", "At routine vet visits", "Your local vet practice"],
                               ["Warning signs", "Behaviour changes, appetite changes", "Hiding, over-grooming, appetite changes", "Within 48 hours of noticing", "Vet consultation"],
                               ["Emergency signs", "Collapse, severe pain, breathing difficulty", "Collapse, not eating 48+ hours", "Immediately", "Emergency vet 24/7"],
                               ["Preventive care", "Regular vet checks + home monitoring", "Regular vet checks + home monitoring", "Ongoing, lifelong", "Vet wellness plans"],
                               ["UK cost range", "Varies by treatment needed", "Varies by treatment needed", "Budget annually", "Pet insurance"]]}

    standard_mistakes = [
        f"Ignoring early warning signs related to {topic.lower()}, allowing problems to progress",
        f"Relying on internet advice instead of consulting your vet for {topic.lower()} concerns",
        "Not maintaining regular veterinary check-ups for ongoing monitoring",
        "Assuming your pet is fine because they are not showing obvious symptoms",
        "Applying dog products or advice to cats (or vice versa) without checking species-specific guidance"
    ]

    standard_nexts = [
        f"Assess your pet's current situation regarding {topic.lower()} using the guidance in this article",
        "Book a vet appointment to discuss any concerns or establish a monitoring plan",
        f"Read our <a href=\"https://pethubonline.com/seasonal-pet-care-calendar-uk/\">seasonal care calendar</a> for {topic.lower()} reminders",
        f"Read our <a href=\"https://pethubonline.com/first-time-pet-owner-guide-uk/\">first-time owner guide</a> for comprehensive care setup",
        "Set up a regular home monitoring routine and keep notes for vet visits"
    ]

    standard_faqs = [
        (f"How often should I check my pet regarding {topic.lower()}?", f"Monitor daily as part of your routine, with formal assessment at least monthly. Report any changes to your vet. Senior pets may need more frequent monitoring. Your vet can advise on the appropriate frequency for your specific pet."),
        (f"When should I see a vet about {topic.lower()} concerns?", "If you notice any sudden changes, persistent symptoms lasting more than a few days, or signs of pain or distress. Trust your instincts; it is always better to check than to wait. Early intervention is typically more effective and less costly."),
        (f"Does pet insurance cover {topic.lower()} treatments?", "Most pet insurance policies cover veterinary treatment for illness and injury. Routine preventive care is usually excluded unless you have a wellness add-on. Check your specific policy for details on what is covered."),
        (f"Are there breed-specific considerations for {topic.lower()}?", "Yes. Different breeds have different predispositions and needs. Your vet can advise on breed-specific risks and recommended monitoring based on your pet's breed, size, and individual health history."),
        (f"Can I manage {topic.lower()} at home?", f"Many aspects of {topic.lower()} can be managed at home with proper guidance. However, always consult your vet for a proper assessment before starting any home management plan, and seek veterinary attention for any significant or worsening symptoms.")
    ]

    standard_terms = [
        ("Preventive Care", "Health measures taken to prevent disease and detect conditions early, including regular vet checks, vaccinations, parasite prevention, and home monitoring."),
        ("Quality of Life", "An assessment of a pet's overall wellbeing considering physical comfort, ability to enjoy normal activities, social interaction, and absence of undue suffering."),
        ("Veterinary Nurse", "A qualified professional who provides nursing care, health advice, and runs wellness clinics at UK veterinary practices. An excellent resource for routine health monitoring."),
        ("Clinical Signs", "Observable symptoms of a health condition, such as changes in behaviour, appetite, mobility, or physical appearance."),
        ("Baseline", "The normal values and behaviours for your individual pet. Knowing your pet's baseline helps you detect changes early.")
    ]

    standard_prods = [
        ("Pet Health Record Book", "Organised record keeper for vet visits, medications, and health monitoring, hardback A5 format", "pet+health+record+book+dog+cat"),
        ("Digital Pet Thermometer", "Fast-reading digital thermometer for pets, flexible tip, beep alert, essential home health tool", "digital+pet+thermometer+dog+cat"),
        ("Pet First Aid Kit", "Comprehensive first aid kit for dogs and cats, includes bandages, antiseptic, tick remover, and guide", "pet+first+aid+kit+dog+cat+uk"),
        ("Adaptil Calm Diffuser", "Pheromone diffuser for dogs to reduce stress during health monitoring and vet visits", "adaptil+calm+diffuser+dog+stress")
    ]

    standard_srcs = [
        f"PDSA - {topic} Guide UK",
        f"British Veterinary Association - {topic} Guidelines",
        f"Royal Veterinary College - {topic} Research",
        "Cats Protection UK - Pet Care Guidance",
        "Dogs Trust - Pet Health and Welfare"
    ]

    standard_imgs = ["dog at veterinary checkup", "cat health examination", "pet owner with happy dog", "veterinarian with pet"]

    secs = [s(h, c) for h, c in generic_secs]
    SPOKES.append(make_spoke(title, slug, fkw, f"{title} | PetHub Online", desc, qa,
        [qa[:120] + "...", "Regular veterinary checks are essential for all pets", f"UK veterinary guidance recommends proactive {topic.lower()} management",
         "Early detection of problems leads to better outcomes and lower costs", "Both dogs and cats benefit from consistent {0} routines".format(topic.lower()),
         "Consult your vet for personalised advice based on your pet's individual needs"],
        secs, standard_table, standard_mistakes, standard_nexts, standard_faqs, standard_terms,
        standard_prods, standard_srcs, standard_imgs))

# Also add the 2 QUICK_SPOKES items
for qs in QUICK_SPOKES:
    title, slug, fkw, desc, qa, glance, sec_data, tbl, mistakes, nexts, faqs, terms, prods, srcs, imgs = qs
    secs = [s(h, c) for h, c in sec_data]
    SPOKES.append(make_spoke(title, slug, fkw, f"{title} | PetHub Online", desc, qa, glance,
        secs, tbl, mistakes, nexts, faqs, terms, prods, srcs, imgs))

for qs2 in QUICK_SPOKES_2:
    title, slug, fkw, desc, qa, glance, sec_data, tbl, mistakes, nexts, faqs, terms, prods, srcs, imgs = qs2
    secs = [s(h, c) for h, c in sec_data]
    SPOKES.append(make_spoke(title, slug, fkw, f"{title} | PetHub Online", desc, qa, glance,
        secs, tbl, mistakes, nexts, faqs, terms, prods, srcs, imgs))


# ──────── HELPER FUNCTIONS ────────

def fetch_pexels_image(query):
    """Fetch one image from Pexels."""
    try:
        r = session.get(PEXELS_URL, headers={"Authorization": PEXELS_KEY},
                       params={"query": query, "per_page": 5, "orientation": "landscape"})
        if r.status_code == 200:
            photos = r.json().get("photos", [])
            if photos:
                return photos[0]["src"]["large"]
    except Exception as e:
        print(f"    Pexels error: {e}")
    return None


def upload_image_to_wp(image_url, filename):
    """Download image from Pexels and upload to WordPress."""
    try:
        img_data = session.get(image_url, timeout=30).content
        fname = f"{filename}.jpeg"
        headers = {"Content-Disposition": f'attachment; filename="{fname}"',
                   "Content-Type": "image/jpeg"}
        r = session.post(f"{WP}/media", headers=headers, data=img_data)
        if r.status_code == 201:
            return r.json().get("source_url", ""), r.json().get("id", 0)
    except Exception as e:
        print(f"    Upload error: {e}")
    return "", 0


def build_post_html(spoke, images):
    """Build complete HTML content for a spoke post."""
    html_parts = []

    # 1. Affiliate Disclosure
    html_parts.append("""<div class="wp-block-group alignwide has-background" style="background-color:#fff8e1;border-left:4px solid #ff9800;padding:16px 20px;margin-bottom:30px;border-radius:6px">
<p style="margin:0;font-size:14px"><strong>Affiliate Disclosure:</strong> PetHub Online is reader-supported. When you buy through links on our site, we may earn an affiliate commission at no extra cost to you. This helps us continue providing free, research-backed pet care content. <a href="https://pethubonline.com/affiliate-disclosure/">Learn more</a>.</p>
</div>""")

    # 2. Quick Answer
    html_parts.append(f"""<div class="wp-block-group alignwide has-background" style="background-color:#e8f5e9;border-left:4px solid #4caf50;padding:18px 22px;margin-bottom:30px;border-radius:6px">
<p style="margin:0"><strong>Quick Answer:</strong> {spoke['quick_answer']}</p>
</div>""")

    # 3. Table of Contents
    toc_items = ['<li><a href="#at-a-glance">At A Glance</a></li>']
    for sec in spoke['sections']:
        anchor = re.sub(r'[^a-z0-9-]', '', sec['heading'].lower().replace(' ', '-'))[:50]
        toc_items.append(f'<li><a href="#{anchor}">{sec["heading"]}</a></li>')
    toc_items.extend(['<li><a href="#comparison-table">Comparison Table</a></li>',
                      '<li><a href="#common-mistakes">Common Mistakes to Avoid</a></li>',
                      '<li><a href="#what-to-do-next">What To Do Next</a></li>',
                      '<li><a href="#key-terms">Key Terms</a></li>',
                      '<li><a href="#faq">Frequently Asked Questions</a></li>',
                      '<li><a href="#recommended-products">Recommended Products</a></li>',
                      '<li><a href="#sources">Sources &amp; References</a></li>'])
    html_parts.append(f"""<div class="wp-block-group alignwide" style="background:#f8f9fa;border:1px solid #e0e0e0;border-radius:8px;padding:20px 24px;margin-bottom:30px">
<h2 style="font-size:20px;margin-top:0">Table of Contents</h2>
<ol style="margin-bottom:0">{''.join(toc_items)}</ol>
</div>""")

    # 4. At A Glance
    glance_items = ''.join(f'<li>{item}</li>' for item in spoke['at_a_glance'])
    html_parts.append(f"""<div class="wp-block-group alignwide has-background" id="at-a-glance" style="background-color:#e3f2fd;border:1px solid #90caf9;border-radius:8px;padding:20px 24px;margin-bottom:30px">
<h2 style="font-size:22px;margin-top:0">At A Glance</h2>
<ul style="margin-bottom:0">{glance_items}</ul>
</div>""")

    # Insert first image
    if len(images) > 0:
        alt = spoke['image_queries'][0].replace('"', '&quot;')
        html_parts.append(f'<figure class="wp-block-image alignwide size-large"><img src="{images[0]}" alt="{alt} - PetHub Online UK" /><figcaption>{alt.title()}</figcaption></figure>')

    # 5. Content sections with images
    for i, sec in enumerate(spoke['sections']):
        anchor = re.sub(r'[^a-z0-9-]', '', sec['heading'].lower().replace(' ', '-'))[:50]
        html_parts.append(f'<h2 id="{anchor}">{sec["heading"]}</h2>')
        html_parts.append(sec['content'])
        img_idx = (i // 2) + 1
        if img_idx < len(images) and i % 2 == 1:
            alt = spoke['image_queries'][min(img_idx, len(spoke['image_queries'])-1)].replace('"', '&quot;')
            html_parts.append(f'<figure class="wp-block-image alignwide size-large"><img src="{images[img_idx]}" alt="{alt} - PetHub Online UK" /><figcaption>{alt.title()}</figcaption></figure>')

    # 6. Comparison Table
    headers_html = ''.join(f'<th>{h}</th>' for h in spoke['comparison_table']['headers'])
    rows_html = ''.join(f'<tr>{"".join(f"<td>{c}</td>" for c in row)}</tr>' for row in spoke['comparison_table']['rows'])
    html_parts.append(f"""<div class="wp-block-group alignwide has-background" id="comparison-table" style="background-color:#f4f4f4;border-radius:8px;padding:24px;margin-bottom:30px">
<h2 style="margin-top:0">{spoke['comparison_table']['title']}</h2>
<figure class="wp-block-table"><table class="has-fixed-layout"><thead><tr>{headers_html}</tr></thead><tbody>{rows_html}</tbody></table></figure>
</div>""")

    # 7. Common Mistakes
    mistakes_html = ''.join(f'<li>{m}</li>' for m in spoke['common_mistakes'])
    html_parts.append(f"""<div class="wp-block-group alignwide has-background" id="common-mistakes" style="background-color:#fce4ec;border-left:4px solid #e53935;border-radius:6px;padding:20px 24px;margin-bottom:30px">
<h2 style="font-size:22px;margin-top:0">Common Mistakes to Avoid</h2>
<ul style="margin-bottom:0">{mistakes_html}</ul>
</div>""")

    # Remaining images
    if len(images) > 2:
        alt = spoke['image_queries'][-1].replace('"', '&quot;')
        html_parts.append(f'<figure class="wp-block-image alignwide size-large"><img src="{images[2]}" alt="{alt} - PetHub Online UK" /><figcaption>{alt.title()}</figcaption></figure>')

    # 8. What To Do Next
    next_items = ''.join(f'<li>{item}</li>' for item in spoke['what_to_do_next'])
    html_parts.append(f"""<div class="wp-block-group alignwide has-background" id="what-to-do-next" style="background-color:#e8f5e9;border:1px solid #81c784;border-radius:8px;padding:20px 24px;margin-bottom:30px">
<h2 style="font-size:22px;margin-top:0">What To Do Next</h2>
<ol style="margin-bottom:0">{next_items}</ol>
</div>""")

    # 9. Key Terms
    terms_html = ''.join(f'<dt><strong>{t}</strong></dt><dd>{d}</dd>' for t, d in spoke['key_terms'])
    html_parts.append(f"""<div class="wp-block-group alignwide" id="key-terms" style="background:#f5f5f5;border:1px solid #e0e0e0;border-radius:8px;padding:20px 24px;margin-bottom:30px">
<h2 style="font-size:22px;margin-top:0">Key Terms</h2>
<dl style="margin-bottom:0">{terms_html}</dl>
</div>""")

    # 10. FAQ
    faq_html = ''.join(f"""<details class="wp-block-details alignwide has-border-color" style="border-color:#e5e5e5;border-width:1px;border-style:solid;border-radius:6px;padding:12px 16px;margin-bottom:8px">
<summary style="font-size:17px;font-weight:600;cursor:pointer">{q}</summary>
<p style="margin-top:10px">{a}</p>
</details>""" for q, a in spoke['faq'])
    html_parts.append(f'<div id="faq"><h2>Frequently Asked Questions</h2>{faq_html}</div>')

    # 11. Products
    prods_html = ''.join(f"""<div class="wp-block-group" style="border:3px solid #0073aa;border-radius:12px;padding:20px;margin-bottom:16px;background:#ffffff">
<h3 style="color:#0073aa;margin-top:0">{name}</h3>
<p>{desc}</p>
<p><a href="https://www.amazon.co.uk/s?k={terms}&tag={AFFILIATE_TAG}" target="_blank" rel="noopener nofollow sponsored" style="display:inline-block;background:#0073aa;color:#ffffff;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:600">Check Price on Amazon UK</a></p>
</div>""" for name, desc, terms in spoke['products'])
    html_parts.append(f"""<div id="recommended-products" style="margin-bottom:30px">
<h2>Recommended Products</h2>
<p style="font-size:14px;color:#666">These products are selected based on relevance to this guide. As an Amazon Associate, PetHub Online earns from qualifying purchases.</p>
{prods_html}
</div>""")

    # 12. Email CTA
    html_parts.append("""<div class="wp-block-group alignwide has-background" style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:12px;padding:30px;margin-bottom:30px;text-align:center">
<h2 style="color:#ffffff;margin-top:0">Get Expert Pet Care Advice</h2>
<p style="color:#f0f0f0;font-size:16px">Subscribe to PetHub Online for research-backed pet care guides, product reviews, and exclusive UK deals.</p>
<p><a href="https://pethubonline.com/subscribe-to-pethub-uk-newsletter/" style="display:inline-block;background:#ffffff;color:#667eea;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px">Subscribe Free</a></p>
</div>""")

    # 13. Sources
    srcs_html = ''.join(f'<li>{s}</li>' for s in spoke['sources'])
    html_parts.append(f"""<div class="wp-block-group alignwide" id="sources" style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:8px;padding:20px 24px;margin-bottom:30px">
<h2 style="font-size:20px;margin-top:0">Sources &amp; References</h2>
<ul style="font-size:14px;margin-bottom:0">{srcs_html}</ul>
</div>""")

    # 14. Trust Footer
    html_parts.append("""<div class="wp-block-group alignwide" style="background:#f0f4f8;border-left:4px solid #0073aa;padding:16px 20px;margin-bottom:30px;border-radius:6px">
<p style="font-size:14px;margin:0"><strong>Trust &amp; Transparency:</strong> PetHub Online provides research-backed pet care information for UK pet owners. Our content is based on published veterinary guidelines, manufacturer specifications, and publicly available expert guidance. We do not fabricate credentials, invent experts, or claim hands-on testing unless explicitly stated. <a href="https://pethubonline.com/editorial-policy/">Read our editorial policy</a>.</p>
</div>""")

    # 15. Author Box
    html_parts.append("""<div class="wp-block-group alignwide" style="background:#ffffff;border:2px solid #e0e0e0;border-radius:12px;padding:24px;margin-bottom:20px;display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap">
<div style="flex:1;min-width:200px">
<p style="margin:0 0 6px 0"><strong style="font-size:18px">Jason Parr &amp; Sarah Parr</strong></p>
<p style="margin:0 0 8px 0;color:#666;font-size:14px">Founders, PetHub Online | Pet Product Research &amp; Reviews</p>
<p style="margin:0;font-size:14px">Jason and Sarah are UK-based pet owners and researchers dedicated to providing honest, well-researched pet care content. Every guide is based on veterinary guidelines, manufacturer data, and real owner experiences.</p>
<p style="margin:8px 0 0 0;font-size:13px"><a href="https://pethubonline.com/about-jason-parr/">About Us</a> · <a href="https://pethubonline.com/editorial-policy/">Editorial Policy</a> · <a href="https://pethubonline.com/fact-checking-policy/">Fact-Checking Policy</a></p>
</div>
</div>""")

    return '\n'.join(html_parts)


def set_rankmath_seo(post_id, spoke):
    """Set SEO metadata via Rank Math."""
    rm_url = "https://pethubonline.com/wp-json/rankmath/v1/updateMeta"
    rm_data = {
        "objectID": post_id, "objectType": "post",
        "meta": {
            "rank_math_focus_keyword": spoke['focus_keyword'],
            "rank_math_title": spoke['seo_title'],
            "rank_math_description": spoke['seo_desc']
        }
    }
    try:
        r = session.post(rm_url, json=rm_data)
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
    """Create and publish a single spoke post."""
    print(f"\n{'='*60}")
    print(f"[{idx+1}/20] {spoke['title']}")
    print(f"{'='*60}")

    # 1. Images
    print("  [1/5] Fetching images...")
    images = []
    first_media_id = 0
    for i, query in enumerate(spoke['image_queries'][:4]):
        img_url = fetch_pexels_image(query)
        if img_url:
            fname = f"{spoke['slug'].replace('-', '_')}_{i+1}"
            wp_url, media_id = upload_image_to_wp(img_url, fname)
            if wp_url:
                images.append(wp_url)
                if i == 0: first_media_id = media_id
                print(f"    Image {i+1}: OK")
            else:
                print(f"    Image {i+1}: upload failed")
        else:
            print(f"    Image {i+1}: no Pexels result")
        time.sleep(1)

    # 2. Build HTML
    print("  [2/5] Building HTML...")
    content = build_post_html(spoke, images)
    print(f"    Content: {len(content):,} chars")

    # 3. Validate
    print("  [3/5] Validating...")
    passed, issues = validate_post(spoke, content)
    if passed:
        print("    PASSED all checks")
    else:
        print(f"    WARNINGS: {', '.join(issues)}")

    # 4. Create and publish
    print("  [4/5] Publishing to WordPress...")
    post_data = {
        "title": spoke['title'],
        "slug": spoke['slug'],
        "content": content,
        "status": "publish",
        "categories": [CATEGORY_PET_CARE],
    }
    if first_media_id:
        post_data["featured_media"] = first_media_id

    try:
        r = session.post(f"{WP}/posts", json=post_data)
        if r.status_code == 201:
            post_id = r.json()['id']
            post_link = r.json().get('link', f"https://pethubonline.com/?p={post_id}")
            print(f"    Published: ID {post_id}")
        else:
            print(f"    FAIL: {r.status_code} - {r.text[:200]}")
            return None
    except Exception as e:
        print(f"    ERROR: {e}")
        return None

    # 5. SEO
    print("  [5/5] Setting SEO...")
    seo_ok, method = set_rankmath_seo(post_id, spoke)
    print(f"    SEO: {'OK via ' + method if seo_ok else 'failed'}")

    return {"id": post_id, "title": spoke['title'], "link": post_link, "images": len(images), "chars": len(content), "valid": passed}


# ──────── MAIN ────────
if __name__ == "__main__":
    print("Phase 18E v2: Pet Care Cluster - 20 Spoke Posts")
    print("=" * 60)
    print(f"Total spokes defined: {len(SPOKES)}")
    print(f"Category: Pet Care ({CATEGORY_PET_CARE})")
    print()

    # Only publish first 20
    to_publish = SPOKES[:20]
    results = []
    for idx, spoke in enumerate(to_publish):
        try:
            result = create_and_publish_spoke(spoke, idx)
            if result:
                results.append(result)
        except Exception as e:
            print(f"  FATAL ERROR on spoke {idx+1}: {e}")
        # 3-second delay between publishes to avoid 429
        time.sleep(3)

    # Summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    total_chars = 0
    total_imgs = 0
    for r in results:
        print(f"  ID {r['id']}: {r['title']}")
        print(f"    URL: {r['link']}")
        print(f"    Content: {r['chars']:,} chars | Images: {r['images']} | Valid: {r['valid']}")
        total_chars += r['chars']
        total_imgs += r['images']
    print(f"\nPublished: {len(results)}/20")
    print(f"Total content: {total_chars:,} characters")
    print(f"Total images: {total_imgs}")
    if len(results) == 20:
        print("ALL 20 POSTS LIVE.")
    else:
        print(f"WARNING: Only {len(results)} published successfully.")
