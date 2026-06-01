#!/usr/bin/env python3
"""Phase 17E: Create 10 Pet Care spoke posts with full AI-visibility structure."""
import requests, json, time, re

WP = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
PEXELS_KEY = "dmGyKrZqTlwukxWzOK1EkH4jbEv9EaIDpLGj7eL5MZ07bl6AR9OEoHlB"
PEXELS_URL = "https://api.pexels.com/v1/search"
CATEGORY_PET_CARE = 1397
AFFILIATE_TAG = "pethubonline-21"

INTERNAL_LINKS = {
    "seasonal_care": "https://pethubonline.com/seasonal-pet-care-calendar-uk/",
    "first_time": "https://pethubonline.com/first-time-pet-owner-guide-uk/",
    "multi_pet": "https://pethubonline.com/multi-pet-household-management-uk/",
    "senior_care": "https://pethubonline.com/senior-pet-care-guide-3/",
    "seasonal_safety": "https://pethubonline.com/seasonal-pet-safety-calendar/",
    "travel_prep": "https://pethubonline.com/pet-travel-preparation-guide/",
    "first_aid": "https://pethubonline.com/pet-first-aid-checklist/",
    "behaviour": "https://pethubonline.com/pet-behaviour-tracking/",
    "home_safety": "https://pethubonline.com/pet-home-safety-audit/",
    "hydration": "https://pethubonline.com/pet-hydration-guide/",
    "first_aid_basics": "https://pethubonline.com/pet-first-aid-basics/",
    "grooming": "https://pethubonline.com/pet-grooming-glossary/",
    "seasonal_safety_guide": "https://pethubonline.com/seasonal-pet-safety-guide/",
    "multi_pet_tips": "https://pethubonline.com/multi-pet-household-tips/",
}

SPOKES = [
    # ── SPOKE 1: Pet Emergency Contact List UK ──
    {
        "title": "Pet Emergency Contact List UK: Essential Numbers Every Owner Needs",
        "slug": "pet-emergency-contact-list-uk",
        "focus_keyword": "pet emergency contact list UK",
        "seo_title": "Pet Emergency Contact List UK: Essential Numbers | PetHub Online",
        "seo_desc": "Complete UK pet emergency contact list including out-of-hours vets, poison helplines, animal rescue, and insurance claims numbers. Free printable template for your fridge.",
        "quick_answer": "Every UK pet owner should have immediate access to their regular vet, nearest emergency vet, the Animal Poisonline (01202 509000), RSPCA (0300 1234 999), and their pet insurance claims line. Keep a printed list on your fridge and a digital copy on your phone for emergencies.",
        "at_a_glance": [
            "Animal Poisonline operates 24/7 at 01202 509000 (charge applies)",
            "RSPCA emergency line: 0300 1234 999 (England and Wales)",
            "SSPCA emergency line: 03000 999 999 (Scotland)",
            "Most emergency vets charge £200-£400 for out-of-hours consultation",
            "Pet insurance claims must typically be reported within 30-90 days",
            "Microchip databases have 24/7 lost pet reporting services"
        ],
        "sections": [
            {
                "heading": "Emergency Veterinary Contacts",
                "content": f"""<p>Your regular vet should always be your first call during surgery hours. Most UK veterinary practices display their out-of-hours emergency provider on their answerphone message. The largest emergency vet networks in the UK include Vets Now (over 60 clinics), Linnaeus Group, and IVC Evidensia. Emergency consultation fees typically range from £200 to £400, with treatment costs additional. If you are unsure whether your pet needs emergency care, many practices offer triage phone consultations. Keep your vet's daytime and emergency numbers saved in your phone contacts with clear labels. For more on pet health basics, see our <a href="{INTERNAL_LINKS['first_aid']}">Pet First Aid Checklist</a>.</p>"""
            },
            {
                "heading": "Poison and Toxicity Helplines",
                "content": f"""<p>The Animal Poisonline (01202 509000) is the UK's dedicated veterinary toxicology service, available 24 hours a day, 365 days a year. A consultation costs around £45 (2026 pricing) and provides expert toxicology advice directly to you or your vet. Common poisoning emergencies include chocolate, grapes, raisins, lilies (cats), xylitol, ibuprofen, and slug pellets. The VPIS (Veterinary Poisons Information Service) is available to veterinary professionals only and provides detailed treatment protocols. Time is critical in poisoning cases - calling within the first hour dramatically improves outcomes. Keep packaging from any suspected poison to show your vet. See our <a href="{INTERNAL_LINKS['home_safety']}">Pet Home Safety Audit</a> for prevention tips.</p>"""
            },
            {
                "heading": "Animal Welfare and Rescue Contacts",
                "content": f"""<p>The RSPCA operates a 24-hour cruelty and emergency line at 0300 1234 999 for England and Wales. In Scotland, the SSPCA can be reached at 03000 999 999. The Dogs Trust has a rehoming helpline, while Cats Protection operates a national helpline for cat welfare concerns. If you find an injured wild animal, contact your nearest wildlife rescue centre or the RSPB for bird emergencies. For stray dogs, your local council's dog warden service is the official point of contact during business hours. Police should be contacted (101 non-emergency) for dangerous dogs or road traffic accidents involving animals. Our <a href="{INTERNAL_LINKS['first_time']}">First-Time Pet Owner Guide</a> covers more welfare basics.</p>"""
            },
            {
                "heading": "Insurance and Microchip Services",
                "content": f"""<p>Keep your pet insurance policy number, claims phone number, and online portal login details easily accessible. Most UK pet insurers require you to report a claim within 30 to 90 days of treatment. The major UK microchip databases include PetLog (Kennel Club), Petrac, Chipworks, and SmartTrace. Under UK law (since 2016 for dogs, 2024 for cats in England), all dogs and cats must be microchipped. If your pet goes missing, report it to your microchip database immediately - most offer 24/7 online reporting. Also contact local vets, rescue centres, and post on DogLost.co.uk or CatAware. Review your <a href="{INTERNAL_LINKS['seasonal_care']}">Seasonal Pet Care Calendar</a> for regular check-up scheduling.</p>"""
            },
            {
                "heading": "Building Your Emergency Contact Card",
                "content": f"""<p>Create a physical card or fridge magnet with your essential contacts: regular vet (daytime and emergency numbers), Animal Poisonline, RSPCA/SSPCA, pet insurance claims line, microchip database, and a trusted pet sitter or neighbour who can help in emergencies. Include your pet's microchip number, insurance policy number, and any critical medical information such as allergies or ongoing medications. Save all numbers in your phone under a consistent naming convention (e.g., "PET - Emergency Vet") so they are easy to find under pressure. Share this information with anyone who regularly cares for your pet. For multi-pet households, see our <a href="{INTERNAL_LINKS['multi_pet']}">Multi-Pet Household Management Guide</a>.</p>"""
            }
        ],
        "comparison_table": {
            "title": "UK Pet Emergency Services Comparison",
            "headers": ["Service", "Phone Number", "Hours", "Cost", "Best For"],
            "rows": [
                ["Animal Poisonline", "01202 509000", "24/7", "~£45/call", "Suspected poisoning"],
                ["RSPCA (England/Wales)", "0300 1234 999", "24/7", "Free", "Animal cruelty/welfare"],
                ["SSPCA (Scotland)", "03000 999 999", "24/7", "Free", "Animal cruelty/welfare"],
                ["Vets Now", "Local clinic", "Out-of-hours", "£200-400+", "Emergency vet care"],
                ["DogLost", "Online only", "24/7", "Free", "Lost/found dogs"],
                ["PetLog (Kennel Club)", "020 7518 1075", "Office hours", "Free", "Microchip queries"]
            ]
        },
        "common_mistakes": [
            "Not knowing your emergency vet location before an emergency occurs - visit during daylight hours first",
            "Calling 999 for a pet emergency - police and ambulance do not attend animal emergencies (use 101 for RTAs)",
            "Waiting too long to call in poisoning cases - the first 1-2 hours are critical for treatment success",
            "Not updating microchip details after moving house or changing phone number",
            "Assuming pet insurance covers everything - check exclusions, excess amounts, and claim time limits"
        ],
        "what_to_do_next": [
            "Save your regular vet's daytime and out-of-hours numbers in your phone now",
            "Call Animal Poisonline (01202 509000) to save the number - hang up before connection if just saving it",
            "Check your microchip database details are current at your chip provider's website",
            "Create a physical emergency card for your fridge with all key numbers",
            "Share emergency contacts with anyone who regularly looks after your pet"
        ],
        "key_terms": [
            ("Triage", "A rapid assessment process to determine the severity and urgency of a medical condition. Many emergency vets offer phone triage to help you decide if an emergency visit is needed."),
            ("Out-of-Hours (OOH)", "Veterinary care provided outside normal surgery hours, typically evenings, weekends, and bank holidays. Usually costs significantly more than daytime consultations."),
            ("VPIS", "Veterinary Poisons Information Service - a specialist toxicology advisory service available to veterinary professionals for managing animal poisoning cases."),
            ("Microchip Database", "An electronic register linking a pet's implanted microchip number to the owner's contact details. UK law requires all dogs and cats to be registered."),
            ("Excess", "The amount you must pay before your pet insurance covers the remaining costs. Can be a fixed amount, a percentage, or both.")
        ],
        "faq": [
            ("What is the emergency vet number in the UK?", "There is no single national emergency vet number. Call your regular vet's practice and listen to their answerphone for out-of-hours emergency details. Most practices partner with a local emergency provider such as Vets Now."),
            ("How much does an emergency vet visit cost in the UK?", "An out-of-hours emergency consultation typically costs £200 to £400 in the UK, with additional charges for diagnostics, treatment, and medication. Pet insurance can cover these costs depending on your policy."),
            ("When should I take my pet to an emergency vet?", "Seek emergency care for difficulty breathing, suspected poisoning, severe bleeding, seizures, inability to urinate, collapse, bloated abdomen (especially in large dogs), or any injury from a road traffic accident."),
            ("Is the RSPCA free to call?", "The RSPCA emergency line (0300 1234 999) is free to report animal cruelty or welfare concerns. However, the RSPCA is not a veterinary service and cannot provide emergency medical treatment for your pet."),
            ("Can I call 999 for a pet emergency?", "No. The 999 emergency services (police, ambulance, fire) do not respond to animal emergencies. For pet medical emergencies, contact your vet or emergency vet directly. Call 101 if a pet is involved in a road traffic accident.")
        ],
        "products": [
            ("Pet First Aid Kit", "Comprehensive pet first aid kit including bandages, antiseptic wipes, tick remover, digital thermometer, and emergency blanket - essential for every pet owner", "pet+first+aid+kit+dog+cat"),
            ("Waterproof Pet Emergency Card Holder", "Durable waterproof card holder for attaching emergency contact details to your dog's collar or lead", "pet+emergency+id+tag+holder+waterproof"),
            ("Pet Medical Record Folder", "Organised folder for keeping vaccination records, insurance documents, microchip details, and vet contact information together", "pet+medical+record+folder+organiser"),
            ("Reflective Dog Safety Vest", "High-visibility safety vest for dogs to improve visibility during evening walks and emergencies", "reflective+dog+safety+vest+high+visibility")
        ],
        "sources": [
            "Animal Poisonline - UK Veterinary Toxicology Service (animalpoisonline.co.uk)",
            "RSPCA - Emergency Reporting Guide",
            "British Veterinary Association - Finding Emergency Veterinary Care",
            "Kennel Club - PetLog Microchip Database Guidelines",
            "PDSA - When to Contact an Emergency Vet"
        ],
        "image_queries": ["pet first aid supplies", "dog at veterinary clinic", "pet emergency care", "pet owner phone call vet"]
    },
    # ── SPOKE 2: Pet Health Record Template ──
    {
        "title": "Pet Health Record Template UK: Track Vaccinations, Treatments and Vet Visits",
        "slug": "pet-health-record-template-uk",
        "focus_keyword": "pet health record template UK",
        "seo_title": "Pet Health Record Template UK: Track Vet Visits & Vaccinations | PetHub Online",
        "seo_desc": "Free UK pet health record template to track vaccinations, flea and worming treatments, vet visits, weight, and medications. Printable and digital versions for dogs and cats.",
        "quick_answer": "A pet health record should track vaccinations (with batch numbers and due dates), flea and worming treatments, weight history, vet visit notes, medications, microchip details, and insurance information. Keeping accurate records helps your vet provide better care and is essential for boarding kennels, travel, and insurance claims.",
        "at_a_glance": [
            "UK dogs need annual boosters for leptospirosis and 3-yearly for distemper/parvo",
            "Cats need annual boosters for cat flu and feline parvovirus",
            "Flea treatment should be recorded monthly with product name and date",
            "Worming frequency varies: monthly for puppies, quarterly for adult dogs",
            "Weight should be recorded at least quarterly to detect gradual changes",
            "Insurance claims require dated treatment records with costs"
        ],
        "sections": [
            {
                "heading": "Essential Information to Record",
                "content": f"""<p>Every pet health record should begin with permanent information: your pet's name, breed, date of birth, sex, neutering status, microchip number, and any known allergies or chronic conditions. Record your vet practice name, address, phone number, and emergency vet details. Include your pet insurance provider, policy number, and claims contact. For puppies and kittens, record the breeder or rescue centre details, as this information may be needed for hereditary health claims. Update this section whenever details change. For more on getting started, see our <a href="{INTERNAL_LINKS['first_time']}">First-Time Pet Owner Guide</a>.</p>"""
            },
            {
                "heading": "Vaccination Record Tracking",
                "content": f"""<p>Record every vaccination with the date given, vaccine name, batch number, and next due date. UK dogs typically receive a primary course (8 and 10-12 weeks) followed by annual leptospirosis boosters and 3-yearly DHP (distemper, hepatitis, parvovirus) boosters. Cats receive primary vaccinations at 8-9 weeks and 12 weeks, with annual boosters for cat flu and feline parvovirus. Kennel cough vaccination is required by most boarding facilities. Rabbit vaccinations (myxomatosis and RVHD) should also be tracked if applicable. Always get your vet to sign the vaccination card and keep it with your records. See our <a href="{INTERNAL_LINKS['seasonal_care']}">Seasonal Pet Care Calendar</a> for scheduling reminders.</p>"""
            },
            {
                "heading": "Parasite Treatment Log",
                "content": f"""<p>Flea, tick, and worming treatments should be recorded with the product name, date applied, dose, and next treatment due date. Most UK flea treatments are applied monthly, while adult dog worming is typically quarterly (more frequently for dogs with higher exposure risk). Cats that hunt may need more frequent worming. Record any adverse reactions to specific products so your vet can recommend alternatives. With the increasing resistance of parasites to certain products, tracking which treatments you have used helps your vet adjust protocols. Never use dog flea treatments on cats - permethrin toxicity is a leading cause of cat poisoning in the UK. Refer to our <a href="{INTERNAL_LINKS['first_aid_basics']}">Pet First Aid Basics</a> for emergency guidance.</p>"""
            },
            {
                "heading": "Weight and Health Monitoring",
                "content": f"""<p>Regular weight tracking is one of the most valuable health indicators for pets. Weigh your pet at least quarterly and record the date and weight. For puppies and kittens, monthly weighing is recommended during the first year. A change of more than 10% in body weight warrants a vet consultation. Record body condition score (BCS) alongside weight using the 1-9 scale recommended by UK vets. Note any changes in appetite, water intake, energy levels, or behaviour patterns. Track dental check dates and any dental treatments performed. For senior pets, more frequent monitoring is advisable. Our <a href="{INTERNAL_LINKS['senior_care']}">Senior Pet Care Guide</a> covers age-specific monitoring in detail.</p>"""
            },
            {
                "heading": "Organising Your Pet Health Records",
                "content": f"""<p>Use a dedicated folder or binder with dividers for each section: vaccinations, parasite treatments, vet visits, medications, and insurance documents. Many UK vet practices now offer digital portals where you can access your pet's records online - check with your practice. Apps like PetDesk, VitusVet, and some insurance provider apps allow digital record-keeping. Keep physical copies of vaccination certificates as these are legally required for pet travel under the UK Animal Health Certificate scheme. For households with multiple pets, maintain separate records for each animal. Store a backup copy digitally (photo or scan) on your phone or cloud storage. For multi-pet organisation, see our <a href="{INTERNAL_LINKS['multi_pet']}">Multi-Pet Household Management Guide</a>.</p>"""
            }
        ],
        "comparison_table": {
            "title": "Pet Health Record Methods Compared",
            "headers": ["Method", "Cost", "Accessibility", "Backup Safety", "Best For"],
            "rows": [
                ["Paper folder/binder", "£5-15", "At home only", "Low (fire/flood risk)", "Simple tracking"],
                ["Vet practice portal", "Free", "Online anytime", "High (vet servers)", "Vet visit history"],
                ["Spreadsheet (Excel/Sheets)", "Free", "Any device", "Medium (if backed up)", "Detailed tracking"],
                ["Dedicated pet app", "Free-£5/month", "Phone/tablet", "High (cloud)", "On-the-go access"],
                ["Pet insurance app", "Free with policy", "Phone/tablet", "High (provider servers)", "Claims tracking"],
                ["Printed template", "Free (printable)", "At home", "Low", "Quick reference"]
            ]
        },
        "common_mistakes": [
            "Not recording vaccine batch numbers - these are essential for traceability and adverse reaction reporting",
            "Forgetting to update records when changing vet practice - request a copy of your full history to take with you",
            "Only tracking illness visits and ignoring routine preventive care records like flea and worming dates",
            "Not recording weight regularly enough to spot gradual changes that indicate health problems",
            "Keeping all records digitally without a physical backup - phone loss or app discontinuation can lose everything"
        ],
        "what_to_do_next": [
            "Gather all existing vet paperwork, vaccination cards, and insurance documents into one place",
            "Create or download a health record template and fill in your pet's permanent details today",
            "Schedule a weight check at your vet or use pet weighing scales at home this week",
            "Check when your pet's next vaccination and parasite treatment are due and add reminders",
            "Take photos of all physical documents and save to cloud storage as a digital backup"
        ],
        "key_terms": [
            ("Primary Vaccination Course", "The initial series of vaccinations given to puppies or kittens, typically 2-3 injections spaced 2-4 weeks apart, that establishes baseline immunity against key diseases."),
            ("Booster Vaccination", "A follow-up vaccination given at regular intervals (annually or 3-yearly depending on the vaccine) to maintain immunity levels established by the primary course."),
            ("Body Condition Score (BCS)", "A standardised 1-9 scale used by vets to assess whether a pet is underweight, ideal weight, or overweight based on visual and physical examination of body fat and muscle."),
            ("Titre Testing", "A blood test that measures antibody levels to determine whether a pet still has adequate immunity from previous vaccinations, sometimes used as an alternative to routine boosters."),
            ("Animal Health Certificate (AHC)", "The official document required for pets travelling from Great Britain to the EU or Northern Ireland, issued by an OV (Official Veterinarian) within 10 days of travel.")
        ],
        "faq": [
            ("What records should I keep for my pet?", "Keep records of vaccinations (with dates, vaccine names, and batch numbers), flea and worming treatments, weight history, vet visit notes, medications, microchip number, insurance details, and any diagnostic results or test outcomes."),
            ("How long should I keep pet health records?", "Keep pet health records for the lifetime of your pet and ideally for at least 2 years after. Insurance companies may request historical records for claims, and some hereditary conditions only become apparent later in life."),
            ("Do I need a vaccination record for boarding kennels?", "Yes, virtually all UK boarding kennels require proof of up-to-date vaccinations including kennel cough (Bordetella). Most require vaccinations to be given at least 2 weeks before boarding but not more than 12 months prior."),
            ("Can I access my pet's records from my vet?", "Yes, you have the right to request a copy of your pet's veterinary records. Many UK practices now offer online portals for clients to view records digitally. There may be a small administrative charge for printed copies."),
            ("What is the best app for tracking pet health in the UK?", "Popular options include PitPat (activity and weight tracking), the Kennel Club app (for registered pedigree dogs), and your pet insurance provider's app. Many UK vet practices also offer their own client portal apps for appointment booking and record access.")
        ],
        "products": [
            ("Pet Health Record Book", "Hardback pet health log book with pre-printed sections for vaccinations, treatments, weight tracking, and vet visit notes", "pet+health+record+book+log+vaccination"),
            ("Digital Pet Scales", "Accurate digital scales suitable for weighing dogs and cats at home, with hold function for wriggly pets", "digital+pet+scales+dog+cat+weighing"),
            ("Document Organiser Folder", "Multi-pocket document folder for organising pet insurance, vet records, vaccination certificates, and microchip details", "document+organiser+folder+a4+multi+pocket"),
            ("Pet Medication Organiser", "Weekly pill organiser box for managing daily pet medications with labelled compartments", "pill+organiser+weekly+medication+box")
        ],
        "sources": [
            "British Veterinary Association - Vaccination Guidelines for Dogs and Cats",
            "PDSA - Preventive Healthcare for Pets",
            "Kennel Club - Puppy and Dog Health Records",
            "RCVS - Client Access to Veterinary Records",
            "DEFRA - Pet Travel and Animal Health Certificates"
        ],
        "image_queries": ["pet health record book", "dog veterinary checkup", "cat vaccination vet", "pet owner notebook records"]
    },
    # ── SPOKE 3: Pet Care Budget Planner ──
    {
        "title": "Pet Care Budget Planner UK: Monthly Costs for Dogs and Cats",
        "slug": "pet-care-budget-planner-uk",
        "focus_keyword": "pet care budget planner UK",
        "seo_title": "Pet Care Budget Planner UK: Monthly & Annual Pet Costs | PetHub Online",
        "seo_desc": "Complete UK pet care budget planner with monthly and annual cost breakdowns for dogs and cats. Covers food, vet bills, insurance, grooming, and emergency fund planning.",
        "quick_answer": "The average annual cost of owning a dog in the UK is £1,500 to £2,500, while cats cost approximately £1,000 to £1,800 per year. These figures include food, insurance, vaccinations, flea and worming treatments, grooming, and routine vet visits. Building an emergency fund of at least £1,000 is recommended for unexpected veterinary bills.",
        "at_a_glance": [
            "Average UK dog ownership costs £1,500-£2,500 per year",
            "Average UK cat ownership costs £1,000-£1,800 per year",
            "Pet insurance ranges from £15-£80/month depending on breed and cover level",
            "Emergency vet visits cost £200-£400 for out-of-hours consultation alone",
            "PDSA estimates lifetime dog cost at £15,000-£33,000 over 10-13 years",
            "Budget at least £1,000 emergency fund for unexpected vet bills"
        ],
        "sections": [
            {
                "heading": "Monthly Food and Nutrition Costs",
                "content": f"""<p>UK dog food costs vary enormously based on size, brand, and diet type. A small dog eating quality kibble costs approximately £30-50 per month, medium dogs £40-70, and large breeds £60-100+. Raw feeding is typically more expensive at £80-150 per month for medium dogs. Cat food costs range from £20-40 per month for dry food to £40-70 for premium wet food or raw diets. Treats, dental chews, and supplements add £10-20 per month. Buying in bulk, subscribing for regular deliveries, and comparing prices across retailers can reduce costs by 10-20%. Always prioritise nutrition quality - cheaper food can lead to higher vet bills from diet-related health issues. See our <a href="{INTERNAL_LINKS['hydration']}">Pet Hydration Guide</a> for complementary care advice.</p>"""
            },
            {
                "heading": "Insurance and Veterinary Costs",
                "content": f"""<p>Pet insurance is one of the most important budget items. UK pet insurance premiums range from £15-30 per month for basic accident-only cover to £40-80 per month for comprehensive lifetime policies. Factors affecting price include breed, age, location, and cover level. Annual vaccinations cost £50-80 for dogs and £40-60 for cats. Routine flea and worming treatments cost approximately £100-150 per year. Neutering costs £150-300 for dogs and £50-100 for cats (lower through PDSA or rescue organisations). Dental treatment, a commonly overlooked cost, can run £300-800 if professional cleaning or extractions are needed. Our <a href="{INTERNAL_LINKS['first_aid']}">Pet First Aid Checklist</a> covers what to keep at home to manage minor issues yourself.</p>"""
            },
            {
                "heading": "Grooming and Maintenance Costs",
                "content": f"""<p>Professional grooming costs depend heavily on breed and coat type. Short-haired dogs may need grooming only 2-4 times per year at £30-50 per session, while breeds like Poodles, Cockapoos, and Shih Tzus need grooming every 6-8 weeks at £40-70 per session. Cat grooming is less common but long-haired breeds may need professional grooming at £30-50 per session. Home grooming supplies (brushes, nail clippers, shampoo) cost £30-60 as a one-off purchase. Ongoing costs include replacement blades for clippers (£15-25), shampoo refills (£5-10), and dental care products (£5-10 per month). Investing in quality grooming tools reduces long-term costs compared to frequent professional visits. See our <a href="{INTERNAL_LINKS['grooming']}">Pet Grooming Glossary</a> for more information.</p>"""
            },
            {
                "heading": "Equipment and Lifestyle Costs",
                "content": f"""<p>Initial setup costs for a new pet include bed (£20-80), bowls (£10-30), lead and collar or harness (£20-50), crate (£30-80), and toys (£20-40). Annual replacement costs for these items average £100-200. Cat owners additionally need a litter tray (£10-30), scratching post (£20-60), and ongoing litter costs of £10-20 per month. Boarding costs are a significant consideration: kennels charge £15-35 per night for dogs, while catteries charge £10-20 per night. Pet sitting services range from £10-25 per visit. Dog walking services cost £10-20 per walk. These costs add up quickly during holiday periods. For seasonal planning, consult our <a href="{INTERNAL_LINKS['seasonal_care']}">Seasonal Pet Care Calendar</a>.</p>"""
            },
            {
                "heading": "Building a Pet Emergency Fund",
                "content": f"""<p>Even with insurance, unexpected costs arise. Insurance excesses, non-covered treatments, and waiting periods mean you need accessible savings. Aim for an emergency fund of at least £1,000, ideally £2,000-3,000. Build this gradually by setting aside £50-100 per month in a dedicated savings account. Consider that the most common emergency treatments in the UK include foreign body ingestion (£1,000-3,000), cruciate ligament repair (£2,000-4,000), and cancer treatment (£2,000-8,000+). The PDSA provides reduced-cost treatment for eligible owners, and some vet practices offer payment plans through services like Klarna or dedicated veterinary finance providers. Review your pet budget quarterly and adjust for price increases. Our <a href="{INTERNAL_LINKS['senior_care']}">Senior Pet Care Guide</a> covers the higher costs associated with ageing pets.</p>"""
            }
        ],
        "comparison_table": {
            "title": "Average Annual UK Pet Costs by Category",
            "headers": ["Cost Category", "Small Dog", "Large Dog", "Indoor Cat", "Outdoor Cat"],
            "rows": [
                ["Food", "£400-600", "£700-1,200", "£250-400", "£300-500"],
                ["Insurance", "£200-400", "£400-800", "£150-300", "£180-360"],
                ["Vaccinations", "£50-80", "£50-80", "£40-60", "£40-60"],
                ["Flea/Worming", "£80-120", "£100-150", "£60-100", "£80-120"],
                ["Grooming", "£100-300", "£150-400", "£0-100", "£0-100"],
                ["Equipment/Toys", "£100-200", "£150-300", "£100-200", "£100-200"],
                ["TOTAL", "£930-1,700", "£1,550-2,930", "£600-1,160", "£700-1,340"]
            ]
        },
        "common_mistakes": [
            "Not budgeting for pet insurance and then facing a £3,000+ emergency vet bill with no cover",
            "Choosing the cheapest food to save money - poor nutrition leads to higher vet bills long-term",
            "Forgetting to budget for boarding or pet sitting during holidays - these costs add up quickly",
            "Not building an emergency fund even when you have insurance - excess fees and non-covered treatments still cost money",
            "Underestimating first-year costs which are typically 50-100% higher than subsequent years due to setup, neutering, and primary vaccinations"
        ],
        "what_to_do_next": [
            "Calculate your current monthly pet spending across all categories for the last 3 months",
            "Compare your pet insurance policy annually - switching can save £100-200 per year",
            "Set up a standing order for £50-100/month into a dedicated pet emergency savings account",
            "Review your pet food costs and compare prices across at least 3 retailers",
            "Schedule a vet wellness check to catch any developing issues before they become expensive"
        ],
        "key_terms": [
            ("Lifetime Pet Insurance", "A policy that covers ongoing conditions for the pet's entire life, with the annual limit resetting each year. The most comprehensive but most expensive type of UK pet insurance."),
            ("Excess", "The amount you pay towards each insurance claim before the insurer covers the rest. Can be a fixed amount (e.g., £100), a percentage of the claim, or both combined."),
            ("Pre-existing Condition", "Any illness, injury, or symptom that existed before the insurance policy started or during a waiting period. These are excluded from cover by all UK pet insurers."),
            ("PDSA", "People's Dispensary for Sick Animals - a UK veterinary charity providing free and reduced-cost treatment for pets of owners receiving certain means-tested benefits."),
            ("Preventive Care", "Routine health measures such as vaccinations, flea treatment, worming, dental checks, and neutering that prevent illness rather than treating it. Not always covered by insurance.")
        ],
        "faq": [
            ("How much does it cost to own a dog per month in the UK?", "The average monthly cost of owning a dog in the UK is £125 to £210, covering food, insurance, flea and worming treatments, and allowing for routine vet visits. Larger breeds, those requiring regular grooming, or those with health conditions will cost more."),
            ("How much does it cost to own a cat per month in the UK?", "The average monthly cost of owning a cat in the UK is £85 to £150, covering food, insurance, litter, and routine veterinary care. Indoor cats may cost slightly less due to lower parasite treatment needs, but enrichment costs can offset this."),
            ("Is pet insurance worth it in the UK?", "For most UK pet owners, pet insurance is worth it. A single emergency surgery can cost £2,000 to £5,000 or more. Lifetime policies offering £4,000 to £12,000 annual cover provide significant financial protection. The younger and healthier your pet when you start, the lower the premiums."),
            ("What is the biggest pet expense UK owners face?", "Unexpected veterinary treatment is typically the biggest single expense. Emergency surgery, cancer treatment, and ongoing chronic condition management can cost thousands of pounds. Insurance and emergency savings are the best protection against these costs."),
            ("How can I reduce pet care costs in the UK?", "Buy food in bulk, compare insurance annually, learn basic grooming at home, use preventive healthcare to avoid expensive treatments, and take advantage of PDSA or charity-run vaccination clinics if eligible. Never cut corners on parasite prevention or dental care as these prevent more expensive problems.")
        ],
        "products": [
            ("Pet Budget Planner Notebook", "Dedicated budget tracking notebook with pre-printed categories for food, vet bills, insurance, grooming, and equipment spending", "budget+planner+notebook+monthly+expense+tracker"),
            ("Automatic Pet Feeder", "Programmable automatic feeder to control portion sizes and reduce food waste, helping manage food costs accurately", "automatic+pet+feeder+programmable+portion+control"),
            ("Pet Grooming Kit", "Complete home grooming kit including clippers, scissors, brush, nail trimmer, and comb to reduce professional grooming costs", "pet+grooming+kit+clippers+scissors+complete"),
            ("Pet First Aid Kit", "Comprehensive first aid kit to handle minor injuries at home, reducing unnecessary emergency vet visits", "pet+first+aid+kit+dog+cat+comprehensive")
        ],
        "sources": [
            "PDSA - Animal Wellbeing (PAW) Report 2025: Pet Ownership Costs",
            "Association of British Insurers - Pet Insurance Statistics UK",
            "British Veterinary Association - Preventive Healthcare Cost Guide",
            "Money Advice Service - Budgeting for Pet Ownership",
            "Battersea Dogs & Cats Home - True Cost of Pet Ownership"
        ],
        "image_queries": ["pet care supplies cost", "dog cat food bowls", "veterinary bill receipt", "pet owner budget planning"]
    },
    # ── SPOKE 4: Pet Safety Checklist UK ──
    {
        "title": "Pet Safety Checklist UK: Room-by-Room Home Hazard Guide",
        "slug": "pet-safety-checklist-uk",
        "focus_keyword": "pet safety checklist UK",
        "seo_title": "Pet Safety Checklist UK: Room-by-Room Home Hazard Guide | PetHub Online",
        "seo_desc": "Complete UK pet safety checklist covering every room in your home. Identify and eliminate hazards for dogs and cats including toxic plants, chemicals, electrical dangers, and small objects.",
        "quick_answer": "A thorough pet safety audit should cover every room: secure chemicals and medications in locked cabinets, remove or relocate toxic plants (lilies, daffodils, azaleas), cover electrical cables, secure bins with lids, block access to balconies and open windows, and remove small chokeable objects. Conduct this audit before bringing a new pet home and revisit it seasonally.",
        "at_a_glance": [
            "Over 4,000 pets are poisoned by household items in the UK each year",
            "Lilies are the most common fatal plant poisoning in UK cats",
            "Chocolate, grapes, raisins, and xylitol are top dog toxins",
            "Small objects and string/ribbon are the most common foreign body ingestions",
            "Cleaning products, medications, and antifreeze are leading chemical hazards",
            "Garden sheds and garages pose the highest concentration of pet hazards"
        ],
        "sections": [
            {
                "heading": "Kitchen and Dining Area Safety",
                "content": f"""<p>The kitchen contains more pet hazards per square metre than any other room. Store all toxic foods out of reach: chocolate, grapes, raisins, onions, garlic, xylitol (often in sugar-free products), macadamia nuts, and alcohol. Secure bins with lockable lids - food waste bins are the most common source of pet poisoning in UK kitchens. Keep cleaning products in locked cupboards or install child-proof latches. Ensure hot surfaces (hobs, ovens) have guards or restricted access. Dishwasher tablets and pods are attractive to pets and highly toxic. Never leave unattended food on worktops, and be cautious with kebab skewers, corn cobs, and cooked bones which cause intestinal blockages. Our <a href="{INTERNAL_LINKS['home_safety']}">Pet Home Safety Audit</a> provides a detailed kitchen protocol.</p>"""
            },
            {
                "heading": "Living Room and Bedroom Hazards",
                "content": f"""<p>Electrical cables are a major hazard - puppies and kittens are particularly prone to chewing them. Use cable management systems or bitter apple spray as deterrents. Secure blinds cords which pose strangulation risks for cats. Check houseplants against the ASPCA and Blue Cross toxic plant databases. Common UK houseplants that are toxic include lilies (fatal for cats), poinsettias, aloe vera, peace lilies, and philodendrons. Small items such as hair ties, rubber bands, coins, and children's toys are choking and intestinal blockage risks. Candles, essential oil diffusers, and incense can cause burns or respiratory problems. Salt lamps are toxic to cats if licked. Store medications, especially paracetamol (toxic to cats) and ibuprofen, in closed drawers. See our <a href="{INTERNAL_LINKS['first_aid_basics']}">Pet First Aid Basics</a> for emergency guidance.</p>"""
            },
            {
                "heading": "Bathroom and Laundry Hazards",
                "content": f"""<p>Keep toilet lids closed - toilet water may contain cleaning chemicals, and small pets can fall in. Store all medications in a locked medicine cabinet, as even a single paracetamol tablet can be fatal to a cat. Laundry pods and detergent capsules are brightly coloured and attractive to pets but cause severe chemical burns. Hair ties and dental floss are common causes of linear foreign body obstruction in cats. Essential oils, bath salts, and cosmetics should be stored out of reach. Bleach, drain cleaner, and mould remover are highly corrosive - clean up any spills immediately and ventilate the room. Washing machines and tumble dryers should be checked before each use as cats may climb inside. Our <a href="{INTERNAL_LINKS['seasonal_safety']}">Seasonal Pet Safety Calendar</a> covers seasonal chemical hazards.</p>"""
            },
            {
                "heading": "Garden and Outdoor Safety",
                "content": f"""<p>UK gardens present both plant and chemical hazards. Toxic garden plants include foxglove, yew, laburnum, azalea, rhododendron, daffodil bulbs, and lily of the valley. Slug pellets containing metaldehyde are extremely toxic to pets - use pet-safe alternatives containing ferric phosphate instead. Weedkillers, pesticides, and fertilisers should be stored in locked sheds and used according to label instructions for pet-safe drying times. Compost heaps can contain mycotoxins that cause tremors and seizures. Cocoa shell mulch contains theobromine (the same toxin in chocolate). Check fencing for gaps, especially at ground level where dogs can dig under. Swimming pools and ponds should have safe exit points for any pet that falls in. Review our <a href="{INTERNAL_LINKS['seasonal_safety_guide']}">Seasonal Pet Safety Guide</a> for seasonal garden hazards.</p>"""
            },
            {
                "heading": "Garage, Shed and Storage Areas",
                "content": f"""<p>Garages and sheds typically contain the highest concentration of pet toxins in any home. Antifreeze (ethylene glycol) is the single most dangerous garage chemical - it has a sweet taste attractive to pets and even a small amount can cause fatal kidney failure. Switch to propylene glycol-based antifreeze which is less toxic. Store all chemicals, paints, solvents, and automotive products on high shelves or in locked cabinets. Rat poison and mouse bait are common causes of pet poisoning - use pet-safe alternatives or enclosed bait stations. Sharp tools, nails, screws, and broken glass are injury hazards. Check stored items for hiding cats before closing doors. Ensure adequate ventilation and never run engines in enclosed spaces. For overall household safety, review our <a href="{INTERNAL_LINKS['home_safety']}">Pet Home Safety Audit</a>.</p>"""
            }
        ],
        "comparison_table": {
            "title": "Common UK Pet Hazards by Room",
            "headers": ["Room", "Top Hazard", "Risk Level", "Most Affected Pet", "Prevention"],
            "rows": [
                ["Kitchen", "Food waste bins", "High", "Dogs", "Lockable bin lids"],
                ["Living Room", "Toxic plants", "High", "Cats", "Remove or relocate plants"],
                ["Bathroom", "Medications", "Critical", "Both", "Locked medicine cabinet"],
                ["Bedroom", "Hair ties/small objects", "Medium", "Cats", "Store in closed drawers"],
                ["Garden", "Slug pellets", "Critical", "Dogs", "Use ferric phosphate type"],
                ["Garage/Shed", "Antifreeze", "Critical", "Both", "Switch to propylene glycol"]
            ]
        },
        "common_mistakes": [
            "Assuming a pet will not eat something because it tastes bad - dogs especially will eat almost anything",
            "Placing toxic plants on high shelves thinking cats cannot reach them - cats can access virtually any surface",
            "Using standard slug pellets in the garden without checking they are pet-safe (metaldehyde is lethal)",
            "Leaving medications on bedside tables or in bags on the floor - a single pill can be fatal for small pets",
            "Not checking washing machines and dryers before use - cats frequently climb inside warm appliances"
        ],
        "what_to_do_next": [
            "Walk through every room in your home today and check for the hazards listed above",
            "Install child-proof latches on cupboards containing chemicals and medications",
            "Check all houseplants and garden plants against the ASPCA toxic plant database online",
            "Replace standard slug pellets with pet-safe ferric phosphate alternatives immediately",
            "Save the Animal Poisonline number (01202 509000) in your phone contacts"
        ],
        "key_terms": [
            ("Metaldehyde", "The active ingredient in most traditional slug pellets in the UK. Highly toxic to dogs and cats, causing tremors, seizures, and death. Being phased out of some products but still widely available."),
            ("Theobromine", "The toxic compound found in chocolate and cocoa products. Dogs metabolise it much more slowly than humans, making even small amounts of dark chocolate potentially dangerous."),
            ("Linear Foreign Body", "A string-like object (dental floss, ribbon, tinsel, thread) that becomes lodged in the intestines and causes a sawing motion as the gut contracts around it. Requires emergency surgery."),
            ("Ethylene Glycol", "The toxic chemical in most standard antifreeze products. Has a sweet taste attractive to pets and causes irreversible kidney failure within hours of ingestion."),
            ("ASPCA Toxic Plant Database", "A comprehensive online resource listing plants toxic to dogs, cats, and horses. Used worldwide as the reference standard for pet plant toxicity information.")
        ],
        "faq": [
            ("What household items are toxic to dogs in the UK?", "Common household dog toxins include chocolate, grapes, raisins, onions, garlic, xylitol (in sugar-free products), paracetamol, ibuprofen, antifreeze, slug pellets, cleaning products, and certain houseplants. The most common emergency presentations are chocolate ingestion and bin raiding."),
            ("What plants are toxic to cats in the UK?", "Lilies (all species) are the most dangerous UK cat toxin - even pollen can cause fatal kidney failure. Other toxic plants include azaleas, rhododendrons, poinsettias, peace lilies, aloe vera, daffodils, foxglove, and yew. Check all houseplants and bouquets before bringing them home."),
            ("How do I pet-proof my home in the UK?", "Conduct a room-by-room audit: lock away chemicals and medications, remove toxic plants, cover electrical cables, secure bins, check fencing for gaps, replace metaldehyde slug pellets, store small objects, and install child-proof latches on low cupboards."),
            ("What should I do if my pet eats something toxic?", "Call your vet or Animal Poisonline (01202 509000) immediately. Do not make your pet vomit unless specifically instructed by a professional. Keep the packaging or sample of what was eaten. Time is critical - act within the first 1-2 hours for the best outcome."),
            ("Is antifreeze dangerous for pets?", "Yes, antifreeze containing ethylene glycol is one of the most dangerous pet toxins. It has a sweet taste that attracts pets and even a small amount can cause fatal kidney failure within hours. Switch to pet-safe propylene glycol-based antifreeze and clean any spills immediately.")
        ],
        "products": [
            ("Child-Proof Cabinet Locks", "Adhesive child-proof safety locks for kitchen and bathroom cupboards containing chemicals and medications - no drilling required", "child+proof+cabinet+locks+adhesive+safety"),
            ("Cable Management Kit", "Complete cable tidy kit with covers and clips to protect exposed electrical cables from pet chewing", "cable+management+kit+cover+protector+tidy"),
            ("Pet-Safe Slug Pellets", "Ferric phosphate slug pellets that are safe for use around dogs, cats, and wildlife - effective slug and snail control without toxic metaldehyde", "pet+safe+slug+pellets+ferric+phosphate+organic"),
            ("Lockable Kitchen Bin", "Stainless steel kitchen bin with lockable lid to prevent pets from bin raiding and accessing food waste", "lockable+kitchen+bin+pedal+stainless+steel")
        ],
        "sources": [
            "Blue Cross - Toxic Plants for Pets Guide",
            "Animal Poisonline - Top 10 Pet Poisons in UK Homes",
            "RSPCA - Pet-Proofing Your Home Advice",
            "British Veterinary Association - Common Pet Poisoning Prevention",
            "PDSA - Keeping Your Pet Safe at Home"
        ],
        "image_queries": ["pet safe home interior", "dog puppy proofing house", "toxic plants pets avoid", "pet safety household"]
    },
    # ── SPOKE 5: Pet Travel Checklist UK ──
    {
        "title": "Pet Travel Checklist UK: Everything You Need for Domestic and EU Travel",
        "slug": "pet-travel-checklist-uk",
        "focus_keyword": "pet travel checklist UK",
        "seo_title": "Pet Travel Checklist UK: Domestic & EU Pet Travel Guide | PetHub Online",
        "seo_desc": "Complete UK pet travel checklist covering car travel, public transport, ferries, and EU travel requirements. Includes Animal Health Certificate, microchip, vaccination, and packing lists.",
        "quick_answer": "For UK domestic travel, ensure your pet has a secure carrier or car harness, up-to-date microchip, familiar items for comfort, and access to water. For EU travel, you need a valid Animal Health Certificate (AHC) from an Official Veterinarian, microchip, rabies vaccination (given at least 21 days before travel), and tapeworm treatment for dogs entering certain countries.",
        "at_a_glance": [
            "Pets must be restrained in vehicles under the Highway Code (Rule 57)",
            "Animal Health Certificate costs £100-200 and is valid for 10 days of entry",
            "Rabies vaccination must be given at least 21 days before EU travel",
            "Dogs entering Finland, Ireland, Norway, or Malta need tapeworm treatment",
            "Major UK ferry operators allow pets with advance booking",
            "Eurotunnel Le Shuttle allows pets in vehicles (not foot passengers)"
        ],
        "sections": [
            {
                "heading": "UK Car Travel Essentials",
                "content": f"""<p>The Highway Code (Rule 57) states that pets must be suitably restrained so they cannot distract the driver or cause injury in a collision. Options include a crash-tested crate secured in the boot, a car harness attached to the seatbelt system, or a secure pet carrier on the back seat. Never leave a pet in a parked car - temperatures can reach dangerous levels within minutes, even on mild days. Plan rest stops every 2-3 hours for toilet breaks, water, and leg stretching. Carry a travel water bowl and fresh water. For anxious travellers, consider Adaptil (dogs) or Feliway (cats) spray applied to bedding 15 minutes before travel. Build up to longer journeys gradually if your pet is not used to car travel. Our <a href="{INTERNAL_LINKS['travel_prep']}">Pet Travel Preparation Guide</a> covers acclimatisation techniques.</p>"""
            },
            {
                "heading": "Public Transport and Train Travel",
                "content": f"""<p>Most UK train operators allow dogs for free, though some require a lead and muzzle on busy services. Cats and small pets should travel in secure carriers. National Rail's general policy permits two dogs per passenger. London Underground, buses, and trams generally allow dogs on leads but check individual operator policies. Avanti West Coast, LNER, and CrossCountry all allow dogs. Airline pet policies vary significantly - most UK airlines do not allow pets in the cabin except assistance dogs. British Airways, for example, only allows service dogs. For air travel with pets, specialist pet transport companies such as PetAir UK or Airpets can arrange cargo hold travel. Always book pet spaces in advance and carry a copy of vaccination records. See our <a href="{INTERNAL_LINKS['first_time']}">First-Time Pet Owner Guide</a> for travel preparation basics.</p>"""
            },
            {
                "heading": "Ferry and Eurotunnel Travel",
                "content": f"""<p>Major UK ferry operators including P&O Ferries, DFDS, Brittany Ferries, Stena Line, and Irish Ferries allow pets with advance booking. Policies typically require pets to stay in your vehicle or in designated pet-friendly cabins (available on some Brittany Ferries and Stena Line routes). Book pet-friendly cabin or kennel options well in advance as spaces are limited. Eurotunnel Le Shuttle allows pets to travel in your vehicle throughout the crossing - this is often the easiest option for channel crossings. Pets must remain in the vehicle during the 35-minute crossing. Carry water, a lead, and waste bags for the terminal areas. Both ferries and Eurotunnel require proof of rabies vaccination and microchip for cross-border travel. Check our <a href="{INTERNAL_LINKS['seasonal_care']}">Seasonal Care Calendar</a> for travel timing considerations.</p>"""
            },
            {
                "heading": "EU Travel Requirements Post-Brexit",
                "content": f"""<p>Since Brexit, UK pets travelling to the EU require an Animal Health Certificate (AHC) issued by an Official Veterinarian (OV) within 10 days of your travel date. Requirements include: a valid microchip (ISO 11784/11785 standard), rabies vaccination given at least 21 days before travel (but not expired), and the AHC itself (Part 1 for dogs, cats, and ferrets). Dogs travelling to Finland, Ireland, Norway, or Malta need additional tapeworm (Echinococcus multilocularis) treatment given by a vet 24-120 hours before entry. The AHC costs £100-200 depending on your vet. For return to the UK, no AHC is needed but your pet's microchip and vaccination status will be checked. EU pet passports issued before 1 January 2021 remain valid for UK pets. See our <a href="{INTERNAL_LINKS['travel_prep']}">Pet Travel Preparation Guide</a> for detailed planning timelines.</p>"""
            },
            {
                "heading": "Packing List and Travel Day Tips",
                "content": f"""<p>Essential packing items: pet food (enough for the trip plus 2 extra days), collapsible water bowl, fresh water, lead and harness, waste bags, favourite toy or blanket for comfort, any medications with dosage instructions, vaccination records and AHC (if travelling abroad), microchip paperwork, pet first aid kit, and your vet's contact details. For cats, bring a litter tray and litter for the destination. Consider packing a photograph of your pet in case they go missing. On travel day, feed your pet 3-4 hours before departure to reduce car sickness. Arrive at ports and terminals early to allow time for pet check-in procedures. Never sedate your pet for travel without veterinary advice - sedation can affect breathing and temperature regulation. For multi-pet travel, our <a href="{INTERNAL_LINKS['multi_pet']}">Multi-Pet Household Guide</a> has additional tips.</p>"""
            }
        ],
        "comparison_table": {
            "title": "UK Pet Travel Options Compared",
            "headers": ["Transport", "Dogs Allowed", "Cats Allowed", "Cost", "Key Requirement"],
            "rows": [
                ["Car", "Yes (restrained)", "Yes (carrier)", "Fuel only", "Highway Code compliance"],
                ["Train (most UK)", "Yes (on lead)", "Yes (in carrier)", "Usually free", "Varies by operator"],
                ["Eurotunnel", "Yes (in vehicle)", "Yes (in vehicle)", "Included in ticket", "Rabies vax + microchip"],
                ["Ferry (P&O/DFDS)", "Yes (vehicle/cabin)", "Yes (vehicle/cabin)", "£15-30+ booking fee", "Advance booking required"],
                ["UK Domestic Flight", "Service dogs only", "No (most airlines)", "N/A", "Assistance dog ID"],
                ["EU Flight (cargo)", "Yes (hold)", "Yes (hold)", "£200-500+", "AHC + rabies + microchip"]
            ]
        },
        "common_mistakes": [
            "Not booking the Animal Health Certificate appointment early enough - OV appointments can have 2-3 week waiting lists",
            "Getting the rabies vaccination less than 21 days before EU travel - the 21-day wait is a legal requirement",
            "Leaving a pet in a parked car even for a few minutes - temperatures rise dangerously within 10 minutes",
            "Forgetting to update microchip details before travel - if your pet goes missing abroad, outdated details prevent reunification",
            "Assuming all trains and buses allow pets - policies vary between operators and some restrict pets during peak hours"
        ],
        "what_to_do_next": [
            "Check your pet's microchip is registered and all contact details are current",
            "Verify your pet's rabies vaccination status if planning EU travel (must be at least 21 days before departure)",
            "Practice short car journeys to build up your pet's comfort with vehicle travel",
            "Book an OV appointment for your Animal Health Certificate at least 3 weeks before EU travel",
            "Create a pet travel packing list and store it with your travel documents"
        ],
        "key_terms": [
            ("Animal Health Certificate (AHC)", "The official document required for pets travelling from Great Britain to the EU or Northern Ireland, replacing the EU Pet Passport for UK pets post-Brexit. Issued by an Official Veterinarian."),
            ("Official Veterinarian (OV)", "A veterinarian authorised by APHA (Animal and Plant Health Agency) to issue Animal Health Certificates and other official veterinary documentation for pet travel."),
            ("ISO Microchip", "A pet microchip conforming to ISO standards 11784 and 11785, which is the format required for international pet travel. Virtually all UK microchips meet this standard."),
            ("Tapeworm Treatment", "An Echinococcus multilocularis treatment required for dogs entering Finland, Ireland, Norway, or Malta from the UK. Must be administered by a vet 24-120 hours before entry."),
            ("Highway Code Rule 57", "The UK Highway Code rule stating that animals must be suitably restrained in vehicles so they cannot distract the driver or be injured in an emergency stop.")
        ],
        "faq": [
            ("Do I need a pet passport to travel from the UK?", "UK-issued EU Pet Passports are no longer valid for travel from Great Britain to the EU since Brexit. You now need an Animal Health Certificate (AHC) issued by an Official Veterinarian within 10 days of your travel date. EU Pet Passports issued before 1 January 2021 are still valid for return to the UK."),
            ("Can I take my dog on a UK train?", "Most UK train operators allow dogs to travel for free. Dogs should be on a lead and under control. Some operators may request a muzzle on busy services. Cats and small pets should be in secure carriers. Always check the specific operator's pet policy before travelling."),
            ("How much does it cost to take a pet to Europe?", "Typical costs include: rabies vaccination (£40-60 if not already vaccinated), Animal Health Certificate (£100-200), tapeworm treatment if required (£20-30), and ferry or Eurotunnel pet supplement (£15-30). Total EU travel preparation costs approximately £175-320 per pet."),
            ("Can I fly with my pet from the UK?", "Most UK airlines do not allow pets in the cabin except certified assistance dogs. Pets can travel in the aircraft cargo hold through specialist pet transport companies, typically costing £200-500+ depending on destination and pet size. Short-nose (brachycephalic) breeds may be restricted due to breathing risks."),
            ("How do I keep my dog calm during car travel?", "Build up tolerance with short journeys first. Use a comfortable, secure crate or harness. Apply Adaptil spray to bedding 15 minutes before travel. Avoid feeding 3-4 hours before departure. Play calming music and keep the car well-ventilated. Never sedate your pet without veterinary advice.")
        ],
        "products": [
            ("Crash-Tested Dog Car Crate", "Crash-tested metal dog crate sized for vehicle boot installation with secure latching and ventilation", "crash+tested+dog+car+crate+transport+boot"),
            ("Dog Car Harness Seatbelt", "Adjustable dog car harness with seatbelt attachment for safe vehicle restraint during travel", "dog+car+harness+seatbelt+safety+restraint"),
            ("Collapsible Travel Water Bowl", "Lightweight silicone collapsible water bowl for on-the-go hydration during pet travel", "collapsible+dog+travel+water+bowl+silicone"),
            ("Pet Travel First Aid Kit", "Compact travel-sized pet first aid kit including bandages, antiseptic, tick remover, and emergency blanket", "pet+travel+first+aid+kit+compact")
        ],
        "sources": [
            "GOV.UK - Taking Your Pet Dog, Cat, or Ferret Abroad",
            "APHA - Animal Health Certificate Requirements",
            "Highway Code - Rule 57: Animals in Vehicles",
            "National Rail - Conditions of Travel (Animals)",
            "Eurotunnel Le Shuttle - Travelling with Pets"
        ],
        "image_queries": ["dog car travel crate", "pet carrier travel bag", "dog ferry boat travel", "pet passport documents travel"]
    },
    # ── SPOKE 6: Pet Seasonal Risk Guide ──
    {
        "title": "Pet Seasonal Risk Guide UK: Month-by-Month Hazards and Prevention",
        "slug": "pet-seasonal-risk-guide-uk",
        "focus_keyword": "pet seasonal risk guide UK",
        "seo_title": "Pet Seasonal Risk Guide UK: Monthly Hazards & Prevention | PetHub Online",
        "seo_desc": "Month-by-month UK pet seasonal risk guide covering heatstroke, fireworks, toxic plants, antifreeze, ticks, and seasonal hazards. Prevention advice for dogs and cats throughout the year.",
        "quick_answer": "UK pets face different hazards each season: spring brings toxic bulbs, ticks, and adder bites; summer brings heatstroke, algae toxicity, and grass seeds; autumn brings fireworks, conkers, and acorns; winter brings antifreeze, rock salt, and hypothermia. Understanding seasonal risks allows you to prevent most emergencies before they happen.",
        "at_a_glance": [
            "Heatstroke is the leading summer emergency - dogs cannot cool efficiently above 25C",
            "Firework season (October-November) causes more pet anxiety than any other period",
            "Tick activity peaks March-October with Lyme disease risk in UK hotspots",
            "Antifreeze poisoning peaks November-March during cold snaps",
            "Alabama Rot cases are most common January-May in woodland areas",
            "Seasonal allergies affect approximately 10% of UK dogs"
        ],
        "sections": [
            {
                "heading": "Spring Hazards: March to May",
                "content": f"""<p>Spring in the UK brings several pet-specific risks. Toxic spring bulbs including daffodils, tulips, crocuses, and hyacinths emerge - all parts are toxic to dogs and cats, with bulbs being the most dangerous. Adder season begins in March as snakes emerge from hibernation; most bites occur in southern England and Wales on heathland and coastal paths. Tick activity increases significantly from March, bringing Lyme disease risk in endemic areas including the Scottish Highlands, New Forest, Exmoor, South Downs, and Lake District. Spring cleaning products used more intensively during this period pose chemical risks. Grass pollen allergies begin in late spring, causing skin irritation and ear infections in susceptible dogs. For year-round scheduling, see our <a href="{INTERNAL_LINKS['seasonal_care']}">Seasonal Pet Care Calendar</a>.</p>"""
            },
            {
                "heading": "Summer Dangers: June to August",
                "content": f"""<p>Heatstroke is the most serious summer risk for UK pets. Dogs cannot regulate body temperature efficiently above 25C, and brachycephalic breeds (Bulldogs, Pugs, French Bulldogs) are at extreme risk. Never walk dogs during the hottest part of the day (11am-3pm), always carry water, and test pavement temperature with the back of your hand (5-second rule). Blue-green algae (cyanobacteria) in lakes, ponds, and slow-moving water can be rapidly fatal - avoid any water with a blue-green sheen or scum. Grass seeds are a major summer hazard, embedding in ears, paws, eyes, and nostrils, requiring veterinary removal. Barbecue foods (onions, corn cobs, skewers, cooked bones) cause poisoning and intestinal blockages. Flystrike affects rabbits in warm weather. Our <a href="{INTERNAL_LINKS['hydration']}">Pet Hydration Guide</a> covers summer water intake requirements.</p>"""
            },
            {
                "heading": "Autumn Risks: September to November",
                "content": f"""<p>Firework season is the most stressful period for pets. Approximately 45% of UK dogs show signs of firework fear. Prepare by creating a safe den, using Adaptil or Feliway diffusers, playing desensitisation recordings weeks in advance, and speaking to your vet about anxiety medication for severe cases. Conkers (horse chestnuts) and acorns are toxic to dogs, causing vomiting, diarrhoea, and intestinal blockage. Autumn fungi including death cap and destroying angel mushrooms are potentially fatal if ingested. Harvest mites (orange mites on paws and ears) cause intense itching in late summer and early autumn. Darker evenings increase road accident risk - use reflective collars, leads, and coats for visibility. Our <a href="{INTERNAL_LINKS['seasonal_safety']}">Seasonal Pet Safety Calendar</a> covers preparation timelines in detail.</p>"""
            },
            {
                "heading": "Winter Hazards: December to February",
                "content": f"""<p>Antifreeze (ethylene glycol) is the most dangerous winter toxin - it has a sweet taste and even a teaspoon can be fatal to a cat. Switch to pet-safe propylene glycol-based antifreeze and clean any spills immediately. Rock salt used for de-icing roads and pavements irritates paws and is toxic if licked. Wipe your pet's paws after walks and consider using paw wax or boots. Christmas hazards include chocolate, raisins (in mince pies and Christmas cake), tinsel (intestinal blockage), poinsettias, and mistletoe. Hypothermia affects small, elderly, and short-coated dogs in prolonged cold. Check underneath cars before starting engines as cats often shelter near warm engines. Our <a href="{INTERNAL_LINKS['seasonal_safety_guide']}">Seasonal Pet Safety Guide</a> covers winter protection strategies.</p>"""
            },
            {
                "heading": "Year-Round Seasonal Prevention Strategy",
                "content": f"""<p>Create a seasonal prevention calendar with monthly reminders for parasite treatments, vaccination boosters, and hazard awareness. Keep your pet's flea and tick treatment up to date year-round (not just summer) as central heating keeps parasites active indoors during winter. Maintain a pet first aid kit and update it seasonally - add tick removal tools in spring, cooling products in summer, reflective gear in autumn, and paw balm in winter. Review your home and garden safety quarterly using our checklist. Keep the Animal Poisonline number (01202 509000) saved in your phone. Join local pet owner groups on social media for real-time alerts about seasonal hazards in your area (e.g., blue-green algae sightings, Alabama Rot cases). For comprehensive care planning, our <a href="{INTERNAL_LINKS['senior_care']}">Senior Pet Care Guide</a> covers age-specific seasonal considerations.</p>"""
            }
        ],
        "comparison_table": {
            "title": "UK Seasonal Pet Hazards Quick Reference",
            "headers": ["Season", "Top Hazard", "Signs", "Urgency", "Prevention"],
            "rows": [
                ["Spring", "Tick bites / Lyme disease", "Lameness, fever, lethargy", "Vet within 24h", "Tick prevention treatment"],
                ["Summer", "Heatstroke", "Panting, drooling, collapse", "Emergency (minutes)", "Avoid midday walks"],
                ["Summer", "Blue-green algae", "Vomiting, seizures, collapse", "Critical (minutes)", "Avoid stagnant water"],
                ["Autumn", "Firework anxiety", "Trembling, hiding, panting", "Planned management", "Safe den + desensitisation"],
                ["Winter", "Antifreeze poisoning", "Wobbly, vomiting, seizures", "Critical (1-2 hours)", "Pet-safe antifreeze"],
                ["Winter", "Rock salt paw damage", "Limping, licking paws", "Mild-moderate", "Paw wax + post-walk wipe"]
            ]
        },
        "common_mistakes": [
            "Walking dogs during the hottest part of a summer day - pavement burns and heatstroke can occur above 25C",
            "Only using flea and tick treatment in summer - parasites remain active year-round in UK homes with central heating",
            "Not preparing for firework season until November 5th - desensitisation programmes need weeks to be effective",
            "Allowing dogs to drink from stagnant ponds or lakes - blue-green algae is often invisible and can be fatal within hours",
            "Assuming antifreeze is only a risk if you use it yourself - it leaks from other vehicles onto driveways and roads"
        ],
        "what_to_do_next": [
            "Check which seasonal hazards are relevant to your area right now and take immediate prevention steps",
            "Ensure your pet's flea and tick treatment is current and set monthly reminders for the next 12 months",
            "Create a seasonal pet safety calendar with monthly prevention reminders on your phone",
            "Stock your pet first aid kit with season-appropriate items (tick tool for spring, cooling mat for summer)",
            "Save the Animal Poisonline number (01202 509000) in your phone if you have not already"
        ],
        "key_terms": [
            ("Brachycephalic", "Short-nosed dog breeds such as Bulldogs, Pugs, and French Bulldogs that are at significantly higher risk of heatstroke due to their restricted airways and reduced ability to cool through panting."),
            ("Alabama Rot (CRGV)", "Cutaneous and Renal Glomerular Vasculopathy - a rare but often fatal disease causing skin lesions and kidney failure in dogs. Most UK cases occur January-May in woodland areas."),
            ("Blue-Green Algae", "Cyanobacteria found in lakes, ponds, and slow rivers that produce toxins capable of killing pets within hours of exposure. Appears as a blue-green sheen, foam, or scum on water surfaces."),
            ("Desensitisation", "A behavioural therapy technique involving gradual, controlled exposure to a fear trigger (such as firework sounds) at low intensity, slowly increasing over weeks to build tolerance."),
            ("Tick-Borne Disease", "Infections transmitted through tick bites, most commonly Lyme disease (Borrelia burgdorferi) in the UK. Symptoms include lameness, fever, and lethargy, appearing days to weeks after a bite.")
        ],
        "faq": [
            ("What temperature is too hot to walk a dog in the UK?", "Most veterinary organisations advise caution above 20C and avoiding walks above 25C, especially for brachycephalic breeds, elderly dogs, and puppies. Walk early morning (before 8am) or late evening (after 8pm) during warm weather. Test pavement with the back of your hand for 5 seconds."),
            ("How do I prepare my pet for fireworks?", "Start preparation 4-6 weeks before firework season. Play firework sounds at very low volume and gradually increase over weeks. Create a safe den with blankets and familiar items. Use Adaptil (dogs) or Feliway (cats) diffusers. Close curtains and play background music or TV. Speak to your vet about anti-anxiety medication for severe cases."),
            ("What are the signs of antifreeze poisoning in pets?", "Early signs (within 1-2 hours) include vomiting, wobbliness, excessive thirst, and appearing drunk. Later signs (12-24 hours) include reduced urination, seizures, and coma as kidney failure develops. Seek emergency veterinary treatment immediately - early treatment with ethanol or fomepizole can be life-saving."),
            ("Are conkers poisonous to dogs?", "Yes, conkers (horse chestnuts) contain aesculin which is toxic to dogs, causing vomiting, diarrhoea, abdominal pain, and in severe cases, intestinal blockage. The spiky shell can also cause mouth and digestive tract injuries. Acorns pose similar risks with additional kidney damage potential."),
            ("When is tick season in the UK?", "Ticks are most active March to October in the UK, with peak activity in spring (March-May) and autumn (September-November). However, mild winters can extend tick activity year-round. High-risk areas include woodland, moorland, long grass, and deer habitats.")
        ],
        "products": [
            ("Tick Removal Tool Kit", "Veterinary-grade tick removal tool set with multiple sizes for safe, complete tick removal from dogs and cats", "tick+removal+tool+kit+pet+dog+cat"),
            ("Dog Cooling Mat", "Pressure-activated gel cooling mat that provides instant relief from heat without refrigeration or electricity", "dog+cooling+mat+gel+pressure+activated"),
            ("Pet Reflective Safety Vest", "High-visibility reflective vest for dogs to improve safety during dark autumn and winter walks", "dog+reflective+safety+vest+high+visibility"),
            ("Paw Protection Wax", "Natural beeswax-based paw balm that protects against rock salt, ice, and hot pavements throughout the year", "paw+protection+wax+balm+dog+natural")
        ],
        "sources": [
            "PDSA - Seasonal Pet Safety Advice",
            "British Veterinary Association - Seasonal Pet Health Warnings",
            "Animal Poisonline - Seasonal Toxin Report UK",
            "Blue Cross - Firework Safety for Pets",
            "Public Health England - Tick-Borne Diseases in the UK"
        ],
        "image_queries": ["dog winter snow walk", "pet summer heatstroke prevention", "cat safe cozy indoor autumn", "spring garden dog playing"]
    },
    # ── SPOKE 7: Pet Home Maintenance Guide ──
    {
        "title": "Pet Home Maintenance Guide UK: Keeping Your House Clean with Pets",
        "slug": "pet-home-maintenance-guide-uk",
        "focus_keyword": "pet home maintenance guide UK",
        "seo_title": "Pet Home Maintenance Guide UK: Clean Home with Pets | PetHub Online",
        "seo_desc": "Practical UK guide to maintaining a clean, fresh home with dogs and cats. Covers hair removal, odour control, stain cleaning, pet-safe products, and damage prevention strategies.",
        "quick_answer": "Maintaining a clean home with pets requires a systematic approach: hoover pet-heavy areas 2-3 times per week with a pet-specific vacuum, use enzyme-based cleaners for accidents, wash pet bedding weekly at 60C, groom your pet regularly to reduce loose hair, and use pet-safe cleaning products throughout. Prevention through grooming and training reduces cleaning workload by 50% or more.",
        "at_a_glance": [
            "Pet-specific vacuums with HEPA filters remove 99.9% of pet allergens",
            "Enzyme cleaners break down urine proteins completely - regular cleaners just mask odour",
            "Wash pet bedding at 60C minimum to kill bacteria, dust mites, and parasites",
            "Dogs shed more during spring and autumn - increase grooming frequency during these periods",
            "Many standard cleaning products (bleach, pine-based cleaners) are toxic to pets",
            "Preventive grooming reduces household pet hair by up to 80%"
        ],
        "sections": [
            {
                "heading": "Pet Hair Management Strategy",
                "content": f"""<p>The most effective pet hair strategy combines prevention with removal. Regular grooming (daily for long-haired breeds, 2-3 times weekly for short-haired) dramatically reduces loose hair in the home. Use a deshedding tool such as a Furminator during spring and autumn moulting seasons. For furniture, use lint rollers, rubber gloves (dampen and stroke surfaces), or specialist pet hair removal brushes. Invest in a vacuum with genuine HEPA filtration and a motorised pet tool attachment - brands like Dyson, Shark, and Henry Pet are popular UK choices. Robot vacuums can maintain floors between deep cleans but are not sufficient alone. Throws and washable covers on sofas and beds are cheaper to maintain than reupholstering. Hard floors are significantly easier to keep hair-free than carpet. See our <a href="{INTERNAL_LINKS['grooming']}">Pet Grooming Glossary</a> for grooming tool recommendations.</p>"""
            },
            {
                "heading": "Odour Control and Air Quality",
                "content": f"""<p>Pet odour has three sources: the pet itself, their bedding, and accident spots. Regular bathing (every 4-6 weeks for most dogs) and dental care address the pet directly. Wash all pet bedding weekly at 60C with a pet-safe detergent. For persistent odours in carpets and upholstery, use enzyme-based bio cleaners that break down organic compounds rather than masking them. Baking soda sprinkled on carpet before vacuuming is a natural odour absorber. Air purifiers with activated carbon filters remove pet odours and allergens from the air - these are particularly beneficial for allergy sufferers. Open windows daily for 15-20 minutes to ventilate, even in winter. Avoid air fresheners and plug-ins as many contain chemicals harmful to pets, particularly cats. Essential oil diffusers can be toxic to cats. Our <a href="{INTERNAL_LINKS['home_safety']}">Pet Home Safety Audit</a> covers air quality in detail.</p>"""
            },
            {
                "heading": "Stain Removal and Accident Cleanup",
                "content": f"""<p>For pet urine accidents, act fast: blot (never rub) with paper towels, then apply an enzyme-based cleaner such as Simple Solution, Nature's Miracle, or Bio One. These products contain enzymes that completely break down uric acid crystals - essential because pets can smell residual urine even after regular cleaning and will return to the same spot. For vomit stains, remove solids first, then clean with enzyme cleaner. Blood stains respond to cold water and hydrogen peroxide (test on a hidden area first). Mud should be allowed to dry completely, then brushed or vacuumed before damp cleaning. For carpet, consider professional deep cleaning every 6-12 months. Avoid ammonia-based cleaners on pet accident areas as the scent resembles urine and encourages repeat marking. For general cleaning, our <a href="{INTERNAL_LINKS['behaviour']}">Pet Behaviour Tracking</a> guide can help identify and address the underlying cause of indoor accidents.</p>"""
            },
            {
                "heading": "Pet-Safe Cleaning Products",
                "content": f"""<p>Many common household cleaners are toxic to pets. Avoid: bleach (chlorine fumes irritate respiratory systems), pine-based cleaners (phenols are toxic to cats), products containing benzalkonium chloride (found in many antibacterial sprays), and ammonia-based cleaners (resemble urine scent). Pet-safe alternatives include enzyme-based bio cleaners, white vinegar and water solution (50/50), baking soda for odour absorption, and specifically formulated pet-safe products from brands like Method, Ecover, or specialist pet cleaning ranges. When mopping hard floors, ensure they are fully dry before allowing pets to walk on them. Store all cleaning products in locked cupboards. When in doubt, check the product label for pet safety warnings or contact the manufacturer. Our <a href="{INTERNAL_LINKS['first_aid_basics']}">Pet First Aid Basics</a> covers what to do if your pet contacts a harmful cleaning product.</p>"""
            },
            {
                "heading": "Preventing Pet Damage to Your Home",
                "content": f"""<p>Prevention is more effective and cheaper than repair. For dogs: provide appropriate chew toys to redirect chewing behaviour, crate train puppies when unsupervised, use baby gates to restrict access to certain rooms, and ensure adequate exercise and mental stimulation to reduce destructive behaviour. For cats: provide multiple scratching posts and pads in strategic locations (near sleeping areas and doorways), use Feliway diffusers to reduce stress-related scratching, and apply double-sided tape or furniture protectors to vulnerable surfaces. Protect door frames and skirting boards during the puppy stage with corner guards. Use washable pet throws on furniture rather than trying to keep pets off entirely. Trim your pet's nails regularly to reduce floor and furniture scratching. For multi-pet households, our <a href="{INTERNAL_LINKS['multi_pet_tips']}">Multi-Pet Household Tips</a> guide has additional prevention strategies.</p>"""
            }
        ],
        "comparison_table": {
            "title": "Pet-Safe vs Unsafe Cleaning Products",
            "headers": ["Product Type", "Pet Safety", "Effectiveness", "Cost", "Best Use"],
            "rows": [
                ["Enzyme bio cleaner", "Safe", "Excellent for organics", "£5-10/bottle", "Urine, vomit, organic stains"],
                ["White vinegar solution", "Safe", "Good general purpose", "Under £1", "Surfaces, glass, deodorising"],
                ["Baking soda", "Safe", "Good odour control", "Under £1", "Carpet deodorising"],
                ["Bleach", "TOXIC", "Excellent disinfectant", "£1-3", "AVOID around pets"],
                ["Pine cleaner (Zoflora etc.)", "TOXIC to cats", "Good disinfectant", "£2-5", "AVOID if you have cats"],
                ["Antibacterial spray", "Check label", "Good for surfaces", "£2-5", "Check for benzalkonium chloride"]
            ]
        },
        "common_mistakes": [
            "Using bleach or ammonia-based cleaners on pet accident areas - ammonia mimics urine scent and encourages re-marking",
            "Rubbing urine stains instead of blotting - rubbing pushes the stain deeper into carpet fibres and padding",
            "Not washing pet bedding frequently enough - weekly washing at 60C is the minimum for hygiene",
            "Using essential oil diffusers or plug-in air fresheners which can be toxic to cats and cause respiratory issues",
            "Attempting to train pets off furniture instead of using washable covers - protection is easier than enforcement"
        ],
        "what_to_do_next": [
            "Replace any bleach or pine-based cleaners in pet-accessible areas with enzyme-based pet-safe alternatives",
            "Establish a weekly pet bedding washing schedule at 60C starting this week",
            "Invest in a pet-specific vacuum with HEPA filter if your current vacuum is not managing pet hair",
            "Set up a grooming routine: daily brushing for long coats, 2-3 times weekly for short coats",
            "Place washable throws on any furniture your pet uses regularly"
        ],
        "key_terms": [
            ("Enzyme Cleaner", "A cleaning product containing biological enzymes that break down organic matter (urine, vomit, faeces) at a molecular level, completely eliminating stains and odours rather than masking them."),
            ("HEPA Filter", "High Efficiency Particulate Air filter that captures 99.97% of particles as small as 0.3 microns, including pet dander, pollen, and dust mites. Essential for pet allergy management."),
            ("Phenol", "A chemical compound found in many pine-based and coal-tar cleaning products (including some Dettol and Zoflora variants) that is toxic to cats due to their inability to metabolise it through their liver."),
            ("Uric Acid Crystals", "Microscopic crystals formed from dried urine that are extremely difficult to remove with standard cleaning products. They continue to emit odour and attract pets to re-mark the same location."),
            ("Deshedding", "A grooming technique using specialised tools to remove loose undercoat fur before it falls out naturally. The most effective single strategy for reducing pet hair in the home.")
        ],
        "faq": [
            ("What is the best vacuum for pet hair in the UK?", "The most highly rated pet-specific vacuums in the UK include the Dyson V15 Detect, Shark Anti Hair Wrap, and Henry Pet. Key features to look for are: genuine HEPA filtration, motorised pet tool attachment, strong suction on carpet, and easy bin emptying. Budget options from Vax and Samsung also perform well."),
            ("How do I remove pet urine smell from carpet?", "Blot the area thoroughly with paper towels. Apply an enzyme-based cleaner (such as Simple Solution or Bio One) according to the product instructions - these break down uric acid crystals that cause lingering odour. Allow to dry completely. For old stains, you may need to apply the enzyme cleaner twice. Avoid bleach or ammonia-based products."),
            ("Are air fresheners safe for pets?", "Many standard air fresheners, plug-ins, and essential oil diffusers are not safe for pets, particularly cats. Phenol-based products, certain essential oils (tea tree, eucalyptus, citrus oils), and chemical fragrances can cause respiratory irritation, liver damage, or poisoning. Use pet-safe alternatives like baking soda or enzyme cleaners."),
            ("How often should I wash my dog's bed?", "Wash your dog's bed cover and any removable liners weekly at 60C minimum. This kills bacteria, dust mites, flea eggs, and parasites. Use a pet-safe detergent without strong fragrances. The bed insert or mattress should be deep cleaned monthly and replaced every 1-2 years."),
            ("What cleaning products are toxic to cats?", "Products containing phenols (pine-based cleaners, some Dettol and Zoflora products), essential oils (tea tree, eucalyptus, peppermint, citrus), benzalkonium chloride (many antibacterial sprays), and formaldehyde are particularly toxic to cats. Always check product labels and choose certified pet-safe alternatives.")
        ],
        "products": [
            ("Enzyme Pet Stain Cleaner", "Professional-grade enzyme cleaner for pet urine, vomit, and organic stains - completely breaks down odour-causing compounds", "enzyme+pet+stain+cleaner+urine+odour+remover"),
            ("Pet Hair Removal Roller", "Reusable lint roller with washable sticky surface designed specifically for pet hair removal from furniture and clothing", "pet+hair+removal+roller+reusable+washable"),
            ("HEPA Air Purifier", "Room air purifier with true HEPA and activated carbon filters to remove pet allergens, dander, and odours", "hepa+air+purifier+pet+allergen+odour+room"),
            ("Waterproof Pet Bed Cover", "Machine-washable waterproof pet bed cover that protects bedding from accidents, dirt, and odours", "waterproof+pet+bed+cover+washable+protective")
        ],
        "sources": [
            "Blue Cross - Cleaning and Hygiene with Pets",
            "PDSA - Living with Pets Safely",
            "British Veterinary Association - Pet-Safe Household Products",
            "Allergy UK - Managing Pet Allergens at Home",
            "RSPCA - Creating a Pet-Friendly Home Environment"
        ],
        "image_queries": ["clean home with dog", "pet hair removal vacuum", "cat clean modern home", "pet bedding washing laundry"]
    },
    # ── SPOKE 8: Senior Pet Monitoring Guide ──
    {
        "title": "Senior Pet Monitoring Guide UK: Health Tracking for Older Dogs and Cats",
        "slug": "senior-pet-monitoring-guide-uk",
        "focus_keyword": "senior pet monitoring guide UK",
        "seo_title": "Senior Pet Monitoring Guide UK: Health Tracking for Older Pets | PetHub Online",
        "seo_desc": "Complete UK guide to monitoring senior pet health. Track weight, mobility, appetite, behaviour changes, and early warning signs in older dogs and cats. Includes monitoring checklist.",
        "quick_answer": "Senior pets (dogs 7+ years, cats 10+ years) need more frequent health monitoring than younger animals. Track weight monthly, monitor water intake and appetite daily, observe mobility and behaviour changes weekly, and schedule vet check-ups every 6 months rather than annually. Early detection of age-related conditions dramatically improves outcomes and quality of life.",
        "at_a_glance": [
            "Dogs are considered senior at 7 years (5-6 for giant breeds)",
            "Cats are considered senior at 10-11 years and geriatric at 15+",
            "Senior pets should see a vet every 6 months rather than annually",
            "Weight loss of more than 10% warrants an immediate vet consultation",
            "Increased thirst is often the first sign of kidney disease or diabetes",
            "Cognitive dysfunction affects up to 68% of dogs over 15 years"
        ],
        "sections": [
            {
                "heading": "When Does a Pet Become Senior?",
                "content": f"""<p>The age at which a pet becomes senior varies significantly by species and size. Small dogs (under 10kg) are generally considered senior at 8-10 years, medium dogs at 7-8 years, large dogs at 6-7 years, and giant breeds at 5-6 years. Cats are typically classified as senior at 10-11 years and geriatric (super-senior) at 15 years and above. These are guidelines rather than fixed rules - individual genetics, breed, and lifetime health all influence ageing. The key transition point is when age-related changes begin to affect quality of life or require management. Your vet can advise on when to transition to senior-specific monitoring and care protocols. For comprehensive senior care advice, see our <a href="{INTERNAL_LINKS['senior_care']}">Senior Pet Care Guide</a>.</p>"""
            },
            {
                "heading": "Weight and Body Condition Monitoring",
                "content": f"""<p>Weight is the single most important metric for senior pet health. Weigh your pet monthly on the same scales at the same time of day. Record the weight and compare trends over time. Unexplained weight loss of more than 5% over 3 months is a red flag that warrants veterinary investigation. Common causes include thyroid disease, kidney disease, diabetes, cancer, and dental pain preventing eating. Equally, weight gain in senior pets increases the risk of arthritis, heart disease, and diabetes. Use body condition scoring (BCS) on the 1-9 scale alongside weight: you should be able to feel ribs without pressing hard, see a waist from above, and observe a belly tuck from the side. Senior cats can lose muscle mass while appearing the same weight due to fat redistribution - palpation is as important as scales. Our <a href="{INTERNAL_LINKS['hydration']}">Pet Hydration Guide</a> complements weight monitoring with intake tracking.</p>"""
            },
            {
                "heading": "Behaviour and Cognitive Changes",
                "content": f"""<p>Cognitive dysfunction syndrome (CDS) affects a significant proportion of senior pets - studies suggest 28% of dogs aged 11-12 and up to 68% of dogs aged 15-16 show at least one sign. The DISHAA checklist helps monitor cognitive health: Disorientation (getting lost in familiar places), Interaction changes (less social or more clingy), Sleep-wake cycle disruption (restless at night, sleeping more during the day), House soiling (accidents in previously clean pets), Activity level changes (less interested in play or walks), and Anxiety (new fears, vocalisation, pacing). In cats, look for excessive vocalisation (especially at night), litter tray avoidance, reduced grooming, and confusion. Report any sudden behaviour changes to your vet as they may indicate pain, illness, or treatable conditions. Our <a href="{INTERNAL_LINKS['behaviour']}">Pet Behaviour Tracking</a> guide provides monitoring frameworks.</p>"""
            },
            {
                "heading": "Mobility and Pain Assessment",
                "content": f"""<p>Arthritis affects approximately 80% of dogs over 8 years and 90% of cats over 12 years in the UK. Signs in dogs include stiffness after rest, reluctance to jump or climb stairs, slower on walks, limping, and difficulty getting up. Cats often hide pain: look for reduced jumping (particularly down from heights), less grooming (especially the lower back and hind legs), changed litter tray posture, and reduced play. The Canine Brief Pain Inventory (CBPI) and Feline Musculoskeletal Pain Index (FMPI) are validated tools your vet can use for ongoing assessment. Joint supplements containing glucosamine, chondroitin, and omega-3 fatty acids may provide mild benefit but are not a substitute for veterinary pain management. Hydrotherapy and physiotherapy are increasingly available in the UK for senior pet mobility. See our <a href="{INTERNAL_LINKS['seasonal_care']}">Seasonal Care Calendar</a> for cold-weather arthritis management.</p>"""
            },
            {
                "heading": "Senior Health Check Schedule",
                "content": f"""<p>Senior pets should transition from annual to biannual (every 6 months) vet check-ups. These visits should include a full physical examination, weight check, dental assessment, and discussion of any changes you have observed. Annual blood panels (complete blood count, biochemistry, thyroid function) help detect kidney disease, liver issues, diabetes, and thyroid problems before symptoms become obvious. Urine analysis is particularly important for detecting early kidney disease in cats. Blood pressure measurement helps identify hypertension, which is common in senior cats and can cause retinal damage and kidney deterioration. Dental disease worsens with age and untreated dental pain significantly impacts quality of life and appetite. Keep a monitoring diary noting any changes in eating, drinking, toileting, mobility, behaviour, or sleep patterns to share with your vet. See our <a href="{INTERNAL_LINKS['first_aid']}">Pet First Aid Checklist</a> for senior-specific emergency signs.</p>"""
            }
        ],
        "comparison_table": {
            "title": "Senior Pet Monitoring Schedule",
            "headers": ["What to Monitor", "Frequency", "Method", "Red Flag", "Action"],
            "rows": [
                ["Weight", "Monthly", "Home scales", ">5% change in 3 months", "Vet appointment"],
                ["Water intake", "Daily", "Measure bowl volume", "Significant increase", "Vet within 1 week"],
                ["Appetite", "Daily", "Observe meal completion", "Skipping meals 2+ days", "Vet within 2-3 days"],
                ["Mobility", "Weekly", "Observe movement", "New stiffness or limping", "Vet within 1 week"],
                ["Behaviour", "Weekly", "DISHAA checklist", "New confusion or anxiety", "Vet within 2 weeks"],
                ["Vet check-up", "Every 6 months", "Full examination + bloods", "Any abnormal results", "Follow vet guidance"]
            ]
        },
        "common_mistakes": [
            "Assuming slowing down is just normal ageing rather than treatable pain - 80% of senior dogs have arthritis that can be managed",
            "Waiting for annual vet visits when biannual checks catch age-related disease much earlier",
            "Not monitoring water intake - increased thirst is often the first sign of kidney disease or diabetes",
            "Ignoring dental disease because the pet is still eating - pets often eat through significant dental pain",
            "Reducing exercise entirely instead of modifying it - gentle, regular exercise maintains muscle mass and joint health"
        ],
        "what_to_do_next": [
            "Weigh your senior pet today and start a monthly weight log on your phone or in a notebook",
            "Measure your pet's daily water intake for the next week to establish a baseline",
            "Schedule a senior health check with your vet if the last check was more than 6 months ago",
            "Download or print the DISHAA checklist to assess your pet's cognitive function",
            "Review your pet's mobility during their next walk and note any stiffness, hesitation, or changes"
        ],
        "key_terms": [
            ("Cognitive Dysfunction Syndrome (CDS)", "The veterinary equivalent of dementia in senior dogs and cats. Causes confusion, disorientation, sleep disruption, and behavioural changes. Can be managed with medication, supplements, and environmental enrichment."),
            ("DISHAA", "An acronym used to assess cognitive function in senior dogs: Disorientation, Interaction changes, Sleep-wake disruption, House soiling, Activity changes, and Anxiety. A useful home monitoring framework."),
            ("Body Condition Score (BCS)", "A 1-9 scale assessment of body fat and muscle condition used alongside weight to determine whether a pet is underweight (1-3), ideal (4-5), or overweight (6-9). Particularly important for seniors whose body composition changes."),
            ("Chronic Kidney Disease (CKD)", "Progressive, irreversible loss of kidney function that is extremely common in senior cats. Early detection through blood and urine tests allows dietary and medical management that significantly extends quality of life."),
            ("Hydrotherapy", "Controlled swimming or underwater treadmill exercise used for rehabilitation and mobility maintenance in senior pets. Reduces joint stress while building muscle. Increasingly available at UK veterinary rehabilitation centres.")
        ],
        "faq": [
            ("At what age is a dog considered senior?", "Dogs are generally considered senior at 7 years old, but this varies by size. Small breeds (under 10kg) may not show age-related changes until 8-10 years, while giant breeds (over 40kg) may be considered senior as early as 5-6 years. Individual health and breed predispositions also influence the ageing timeline."),
            ("How often should a senior pet see the vet?", "Senior pets should visit the vet every 6 months rather than annually. These biannual checks should include a full physical examination, weight assessment, dental check, and ideally annual blood work and urine analysis to screen for age-related conditions like kidney disease, diabetes, and thyroid issues."),
            ("What are the signs of dementia in dogs?", "Signs of canine cognitive dysfunction include disorientation in familiar environments, changes in social interaction (more clingy or withdrawn), disrupted sleep-wake cycles (restless at night), house soiling in previously clean dogs, reduced activity or interest in play, and new anxieties or fears."),
            ("How can I tell if my senior cat is in pain?", "Cats are expert at hiding pain. Subtle signs include reduced jumping, less grooming (especially back and hind legs), changed posture in the litter tray, reduced appetite, hiding more, personality changes, and altered facial expressions. A vet can use validated pain assessment tools for a more thorough evaluation."),
            ("Should I change my senior pet's food?", "Many senior pets benefit from a diet formulated for older animals, which typically contains adjusted protein, phosphorus, and calorie levels. However, the decision should be made with your vet based on your pet's individual health status, weight, and any diagnosed conditions. Do not switch food without veterinary guidance.")
        ],
        "products": [
            ("Digital Pet Scales", "Accurate digital pet scales with memory function to track weight changes over time for dogs and cats", "digital+pet+scales+accurate+memory+dog+cat"),
            ("Orthopaedic Pet Bed", "Memory foam orthopaedic pet bed designed for senior dogs with joint pain, arthritis, and mobility issues", "orthopaedic+memory+foam+dog+bed+senior+arthritis"),
            ("Joint Supplement for Dogs", "Veterinary-grade joint supplement containing glucosamine, chondroitin, and omega-3 for senior dog joint support", "joint+supplement+dog+glucosamine+chondroitin+senior"),
            ("Pet Monitoring Camera", "Indoor pet camera with night vision to monitor senior pet behaviour, movement, and activity patterns while away", "pet+monitoring+camera+indoor+night+vision")
        ],
        "sources": [
            "British Veterinary Association - Senior Pet Health Monitoring",
            "PDSA - Caring for Older Pets",
            "International Society of Feline Medicine - Feline Life Stage Guidelines",
            "Canine Arthritis Management - UK Evidence-Based Resources",
            "Journal of Small Animal Practice - Cognitive Dysfunction in Dogs (UK Study)"
        ],
        "image_queries": ["senior dog grey muzzle resting", "elderly cat sleeping comfortable", "old dog vet checkup", "senior pet care monitoring"]
    },
    # ── SPOKE 9: Multi-Pet Household Checklist ──
    {
        "title": "Multi-Pet Household Checklist UK: Managing Dogs and Cats Together",
        "slug": "multi-pet-household-checklist-uk",
        "focus_keyword": "multi-pet household checklist UK",
        "seo_title": "Multi-Pet Household Checklist UK: Dogs & Cats Together Guide | PetHub Online",
        "seo_desc": "Complete UK checklist for managing a multi-pet household with dogs and cats. Covers feeding, space management, introductions, resource guarding prevention, and veterinary scheduling.",
        "quick_answer": "A successful multi-pet household requires separate feeding stations (preventing food theft and aggression), individual resting spaces, gradual introductions over 2-4 weeks, separate litter trays (one per cat plus one extra), regular individual attention time for each pet, and coordinated veterinary and parasite treatment schedules.",
        "at_a_glance": [
            "37% of UK pet-owning households have more than one pet",
            "Each cat needs its own litter tray plus one extra (n+1 rule)",
            "Separate feeding stations prevent 80% of multi-pet food aggression",
            "New pet introductions should take at least 2-4 weeks for stability",
            "Cats need vertical escape routes in homes shared with dogs",
            "Insurance costs are typically 10-15% lower per pet with multi-pet policies"
        ],
        "sections": [
            {
                "heading": "Space Planning and Territory Management",
                "content": f"""<p>Every pet in a multi-pet household needs its own defined space. Dogs need individual beds or crates positioned so they can rest without being disturbed by other pets. Cats need vertical territory - cat trees, wall shelves, and high perches that allow them to observe from safe heights, especially in homes with dogs. The litter tray rule for cats is n+1 (one tray per cat plus one extra), placed in quiet, accessible locations away from food and water bowls. Each pet should have access to hiding spots where they can retreat if feeling stressed. Baby gates are invaluable for creating separate zones, allowing visual contact while preventing physical interaction when needed. Consider traffic flow - pets should be able to reach food, water, litter trays, and outdoor access without having to pass through another pet's territory. Our <a href="{INTERNAL_LINKS['multi_pet']}">Multi-Pet Household Management Guide</a> covers territory planning in depth.</p>"""
            },
            {
                "heading": "Feeding Strategies for Multiple Pets",
                "content": f"""<p>Separate feeding stations are the single most important multi-pet management strategy. Feed each pet in a different location, ideally in separate rooms or at different heights (cats on elevated surfaces, dogs on the floor). Fixed meal times are preferable to free-feeding as they allow you to monitor each pet's intake and prevent food theft. Cat food is too high in protein and fat for dogs, while dog food lacks essential nutrients cats need - cross-eating can cause health problems. Use microchip-activated feeders (SureFlap SureFeed) if pets eat each other's food when you are not supervising. For households with one overweight and one underweight pet, controlled portions at separate stations are essential. If resource guarding occurs around food, increase distance between stations and consult a behaviourist. Our <a href="{INTERNAL_LINKS['hydration']}">Pet Hydration Guide</a> covers water station management for multiple pets.</p>"""
            },
            {
                "heading": "Introduction Protocols",
                "content": f"""<p>Introducing a new pet should take 2-4 weeks minimum. Week 1: keep the new pet in a separate room with their own food, water, bed, and litter tray. Exchange bedding between pets so they become familiar with each other's scent. Week 2: allow brief visual contact through a baby gate or slightly open door, rewarding calm behaviour with treats. Week 3: supervised short meetings in a neutral area, keeping dogs on leads. Week 4: gradually increase interaction time while always maintaining escape routes and safe spaces. Never force interaction or leave unsupervised until you are confident both pets are relaxed together. Signs of stress include hissing, growling, stiff body posture, raised hackles, and avoidance. For dog-to-dog introductions, meet on neutral ground first. For cat-to-cat introductions, scent swapping is particularly crucial. See our <a href="{INTERNAL_LINKS['multi_pet_tips']}">Multi-Pet Household Tips</a> for detailed introduction protocols.</p>"""
            },
            {
                "heading": "Health Management Across Multiple Pets",
                "content": f"""<p>Coordinate parasite treatment so all pets in the household are treated simultaneously - treating one while others carry parasites is ineffective. Some dog flea treatments (especially those containing permethrin) are lethal to cats, so check product labels carefully and separate treated dogs from cats according to product instructions. Schedule vet appointments efficiently - some practices offer multi-pet consultation discounts. Maintain separate health records for each pet with clear labelling. Multi-pet insurance policies from providers like Bought By Many, ManyPets, and Direct Line can save 10-15% compared to individual policies. If one pet becomes ill with a contagious condition, isolate them from other pets and consult your vet about transmission risks. Vaccination schedules may differ between pets even of the same species depending on age and risk factors. Our <a href="{INTERNAL_LINKS['first_aid']}">Pet First Aid Checklist</a> covers multi-pet emergency protocols.</p>"""
            },
            {
                "heading": "Preventing and Managing Conflict",
                "content": f"""<p>Resource guarding (aggression around food, toys, beds, or owner attention) is the most common multi-pet conflict. Prevention strategies include providing multiple resources (enough beds, toys, and water bowls that no pet needs to compete), feeding separately, and avoiding favouritism during attention time. Spend individual quality time with each pet daily - walks alone with each dog, play sessions alone with each cat. Never punish a pet for growling, as this removes their warning system and increases the risk of sudden biting. If guarding behaviour persists, consult a certified animal behaviourist (ABTC registered in the UK). Cats in conflict may show subtle signs: staring, blocking pathways, guarding the litter tray, or one cat consistently hiding. These tensions can escalate if not addressed. For more on recognising multi-pet stress, see our <a href="{INTERNAL_LINKS['behaviour']}">Pet Behaviour Tracking</a> guide.</p>"""
            }
        ],
        "comparison_table": {
            "title": "Multi-Pet Resource Requirements",
            "headers": ["Resource", "Dogs", "Cats", "Rule", "Why It Matters"],
            "rows": [
                ["Feeding stations", "1 per dog", "1 per cat (elevated)", "Separate locations", "Prevents food aggression"],
                ["Water bowls", "1 per 2 dogs + 1", "1 per cat + 1", "Different rooms", "Ensures hydration access"],
                ["Beds/resting spots", "1 per dog + 1", "1 per cat + multiple perches", "Undisturbed locations", "Reduces territorial stress"],
                ["Litter trays", "N/A", "1 per cat + 1 extra", "Quiet, accessible locations", "Prevents toileting issues"],
                ["Toys", "Selection per dog", "Selection per cat", "Enough to avoid competition", "Reduces resource guarding"],
                ["Scratching posts", "N/A", "2+ in different locations", "Near sleeping areas", "Protects furniture and territory"]
            ]
        },
        "common_mistakes": [
            "Rushing introductions between pets - a 2-4 week gradual introduction prevents long-term relationship problems",
            "Free-feeding in a multi-pet home which makes it impossible to monitor individual intake and leads to food theft",
            "Using permethrin-containing dog flea treatments in homes with cats - this is one of the leading causes of cat poisoning in the UK",
            "Assuming pets will sort out their own hierarchy - unmanaged conflict escalates and can result in injury or chronic stress",
            "Having too few litter trays for the number of cats - the n+1 rule (cats + 1) prevents toileting issues and territorial disputes"
        ],
        "what_to_do_next": [
            "Audit your current resource distribution: count beds, bowls, feeding stations, and litter trays against the guidelines above",
            "Set up separate feeding stations in different rooms or at different heights for each pet",
            "Check that all parasite treatments used in your household are safe for all species present",
            "Schedule individual quality time with each pet every day, even if just 10 minutes each",
            "Install at least one baby gate if you have both dogs and cats to create safe zones"
        ],
        "key_terms": [
            ("Resource Guarding", "Aggressive behaviour displayed by a pet to protect food, toys, beds, or owner attention from other pets or people. Ranges from subtle stiffening to growling, snapping, or biting."),
            ("N+1 Rule", "The guideline that multi-cat households should have one litter tray per cat plus one additional tray. This prevents territorial blocking and ensures every cat always has access to a tray."),
            ("Scent Swapping", "An introduction technique where bedding, blankets, or cloths rubbed on one pet are placed with another to familiarise them with each other's scent before physical meeting."),
            ("Vertical Territory", "Elevated spaces (cat trees, shelves, perches) that cats use for security and observation. Essential in multi-pet homes as cats feel safer when they can observe from height."),
            ("ABTC", "Animal Behaviour and Training Council - the UK regulatory body for animal behaviourists and trainers. ABTC-registered professionals meet specific qualification and ethical standards.")
        ],
        "faq": [
            ("How many pets can I have in the UK?", "There is no UK law limiting the number of pets in a private home, but local council bylaws, tenancy agreements, and leasehold restrictions may apply. The Animal Welfare Act requires that you can provide adequate care, space, and attention for every animal. Quality of care should always take priority over quantity."),
            ("Can dogs and cats live together?", "Yes, with proper introduction and management. Many UK households successfully keep dogs and cats together. Success depends on the individual temperaments of the animals, proper introductions over 2-4 weeks, and providing each pet with their own space, feeding area, and escape routes."),
            ("How do I stop my pets fighting?", "First, identify the trigger (usually resource guarding or territorial behaviour). Provide separate resources for each pet, avoid favouritism, use baby gates to create separate zones, and never punish warning behaviours like growling. If fights continue, consult an ABTC-registered animal behaviourist for a professional assessment."),
            ("Should I get a second pet?", "Consider your current pet's temperament, your living space, your budget (costs increase per pet), and your time availability. Some pets prefer being the only animal. If your current pet is well-socialised, your space allows separate resources, and you can afford doubled costs, a companion pet can benefit both animals."),
            ("Is multi-pet insurance cheaper?", "Yes, most UK pet insurance providers offer multi-pet discounts of 10-15% when insuring two or more pets on the same policy. Providers like ManyPets, Bought By Many, and Direct Line offer specific multi-pet policies. Compare total costs rather than just the discount percentage.")
        ],
        "products": [
            ("Microchip Pet Feeder", "SureFlap SureFeed microchip-activated pet feeder that only opens for the registered pet, preventing food theft in multi-pet homes", "surefeed+microchip+pet+feeder+surepetcare"),
            ("Extra-Tall Baby Gate", "Tall pet gate for doorways with cat flap built in, allowing cats to pass freely while restricting dog access", "tall+baby+gate+pet+cat+flap+door"),
            ("Multi-Level Cat Tree", "Large multi-level cat tree with platforms, scratching posts, and hiding spots for vertical territory in multi-pet homes", "cat+tree+large+multi+level+scratching+post"),
            ("Automatic Water Fountain", "Pet water fountain with multi-pet capacity providing fresh filtered running water for dogs and cats", "pet+water+fountain+automatic+dog+cat+large")
        ],
        "sources": [
            "PDSA - Multi-Pet Household Advice",
            "International Cat Care - Multi-Cat Living",
            "Dogs Trust - Introducing a New Pet to Your Household",
            "Blue Cross - Living with Multiple Pets",
            "Animal Behaviour and Training Council (ABTC) - Finding a Behaviourist"
        ],
        "image_queries": ["dog and cat together home", "multiple pets living room", "cat dog introduction meeting", "multi pet household feeding"]
    },
    # ── SPOKE 10: Pet Owner Annual Planner ──
    {
        "title": "Pet Owner Annual Planner UK: Month-by-Month Care Calendar",
        "slug": "pet-owner-annual-planner-uk",
        "focus_keyword": "pet owner annual planner UK",
        "seo_title": "Pet Owner Annual Planner UK: Monthly Pet Care Calendar | PetHub Online",
        "seo_desc": "Complete UK pet owner annual planner with month-by-month tasks for dogs and cats. Covers vaccinations, parasite treatments, seasonal hazards, grooming schedules, and vet appointments.",
        "quick_answer": "A UK pet owner annual planner should include monthly parasite treatments, vaccination booster dates, biannual vet check-ups, seasonal hazard awareness (fireworks prep by September, heatstroke prevention May-August, antifreeze vigilance November-March), quarterly weight checks, grooming schedules, and annual insurance renewal reviews. Setting monthly reminders ensures nothing is missed.",
        "at_a_glance": [
            "Monthly flea treatment and quarterly worming is the minimum UK prevention schedule",
            "Annual vaccination boosters are due 12 months after the previous dose",
            "Senior pets (7+ dogs, 10+ cats) should see a vet every 6 months",
            "Firework preparation should begin in September for November events",
            "Insurance policies should be compared annually at renewal - do not auto-renew",
            "Teeth cleaning and dental checks should be part of every vet visit"
        ],
        "sections": [
            {
                "heading": "January to March: New Year Health Checks",
                "content": f"""<p>January is the ideal time for a fresh start with your pet's care routine. Schedule an early-year vet check-up, especially for senior pets, to establish a health baseline for the year. Review and compare pet insurance policies before auto-renewal - switching can save £100-200 annually. Restock flea and worming treatments for the quarter ahead. January and February are peak Alabama Rot risk months in the UK - clean muddy paws thoroughly after woodland walks. March marks the start of tick season - begin regular tick checks after walks and ensure tick prevention treatment is current. Spring-clean pet bedding and replace any worn items. Update microchip contact details if you have moved or changed phone number. Order flea treatments before March as tick activity increases significantly. For seasonal hazard details, see our <a href="{INTERNAL_LINKS['seasonal_care']}">Seasonal Pet Care Calendar</a>.</p>"""
            },
            {
                "heading": "April to June: Spring and Summer Preparation",
                "content": f"""<p>April brings longer daylight hours and increased outdoor activity. Check garden fencing for winter damage and close any gaps before pets spend more time outside. Remove toxic spring plants (daffodils, tulips, azaleas) from pet-accessible garden areas. May is typically when pollen allergies begin to affect susceptible dogs - watch for excessive scratching, licking paws, and ear infections. Start monitoring temperatures for heatstroke risk as daily highs exceed 20C. June is a good month for annual dental scaling if your vet has recommended it. Schedule grooming appointments for thick-coated breeds as summer approaches. Check that all outdoor water sources are clean and accessible. Begin grass seed checks after walks - ears, paws, and eyes are common embedding sites. Review your pet's body condition and adjust food portions if needed for the warmer months. See our <a href="{INTERNAL_LINKS['hydration']}">Pet Hydration Guide</a> for summer water intake advice.</p>"""
            },
            {
                "heading": "July to September: Summer Safety and Firework Prep",
                "content": f"""<p>July and August require peak heat awareness. Walk dogs before 8am and after 8pm when temperatures exceed 25C. Never leave pets in vehicles. Check for blue-green algae warnings before visiting lakes and ponds. July is typically the busiest month for grass seed vet visits - check paws and ears thoroughly after every walk. August is ideal for booking autumn grooming appointments as they fill quickly. September is the critical month to begin firework preparation: start desensitisation training with firework sound recordings at low volume, set up a safe den or hiding place, order Adaptil or Feliway diffusers, and speak to your vet about anxiety medication if your pet has a history of severe firework fear. Book pet-friendly bonfire night care or boarding if needed. Late September is also time for the second parasite treatment restock of the year. Our <a href="{INTERNAL_LINKS['seasonal_safety']}">Seasonal Pet Safety Calendar</a> has detailed summer-to-autumn transition guidance.</p>"""
            },
            {
                "heading": "October to December: Autumn and Winter Readiness",
                "content": f"""<p>October requires active firework management as events begin before November 5th. Keep pets indoors during dark hours, close curtains, and play background music. November brings antifreeze risk - check driveways for puddles and switch to pet-safe propylene glycol antifreeze. Rock salt on roads and pavements irritates paws and is toxic if licked - wipe paws after winter walks and consider paw wax. December Christmas hazards include chocolate, raisins (in mince pies and Christmas cake), tinsel and ribbon (intestinal blockage risk for cats), and poinsettia plants. Ensure your pet has a warm, draught-free sleeping area as temperatures drop. Schedule a year-end vet check-up, particularly for senior pets. Review the year's health records and note any concerns for the coming year. Begin planning January insurance reviews. Stock up on winter-specific supplies: reflective leads, warm coats for thin-coated breeds, and paw protection products. For comprehensive senior monitoring, see our <a href="{INTERNAL_LINKS['senior_care']}">Senior Pet Care Guide</a>.</p>"""
            },
            {
                "heading": "Setting Up Your Annual Reminder System",
                "content": f"""<p>The most effective annual planner uses digital reminders that cannot be forgotten. Set recurring monthly phone reminders for flea treatment day (pick a consistent date like the 1st of each month). Set quarterly reminders for worming treatment. Enter vaccination booster dates as calendar events with 2-week advance reminders to allow time for booking appointments. Mark biannual vet check-up months (every 6 months from your pet's last visit). Set seasonal alerts: March (tick treatment review), May (heatstroke awareness), September (firework prep), November (antifreeze check). Annual reminders should include: insurance renewal comparison (6 weeks before expiry), microchip database detail check, and pet first aid kit restock. Shared family calendars ensure everyone in the household is aware of pet care responsibilities. Our <a href="{INTERNAL_LINKS['first_time']}">First-Time Pet Owner Guide</a> includes a starter annual planner template.</p>"""
            }
        ],
        "comparison_table": {
            "title": "UK Pet Owner Annual Task Calendar",
            "headers": ["Month", "Key Task", "Frequency", "Who", "Reminder Tip"],
            "rows": [
                ["January", "Insurance renewal review", "Annual", "Owner", "Set reminder 6 weeks before expiry"],
                ["March", "Begin tick prevention", "Monthly Mar-Oct", "Owner/Vet", "Monthly phone reminder"],
                ["Every month", "Flea treatment", "Monthly", "Owner", "Same date each month"],
                ["Every 3 months", "Worming treatment", "Quarterly", "Owner", "Quarterly phone reminder"],
                ["May + November", "Vet health check", "Biannual", "Vet", "Book 2 weeks ahead"],
                ["September", "Firework prep begins", "Annual", "Owner", "September 1st reminder"],
                ["November", "Antifreeze safety check", "Annual", "Owner", "First frost reminder"]
            ]
        },
        "common_mistakes": [
            "Relying on memory for monthly parasite treatments instead of setting phone reminders - missed doses leave gaps in protection",
            "Auto-renewing pet insurance without comparing alternatives - premiums typically increase 10-20% annually and switching saves money",
            "Not starting firework preparation until November - desensitisation programmes need 4-6 weeks to be effective",
            "Skipping winter vet check-ups because the pet 'seems fine' - many age-related conditions show no symptoms until advanced stages",
            "Only monitoring seasonal hazards reactively after an incident rather than proactively preparing month by month"
        ],
        "what_to_do_next": [
            "Set up 12 monthly flea treatment reminders on your phone starting from today's date",
            "Enter your pet's next vaccination booster date in your calendar with a 2-week advance reminder",
            "Book your next vet check-up if the last one was more than 6 months ago",
            "Check when your pet insurance policy renews and set a reminder to compare prices 6 weeks before",
            "Create a shared family calendar event for this month's seasonal pet care tasks"
        ],
        "key_terms": [
            ("Booster Vaccination", "A follow-up vaccination given at regular intervals to maintain immunity. UK dogs typically need annual leptospirosis boosters and 3-yearly DHP boosters. Cats need annual boosters for cat flu and parvovirus."),
            ("Preventive Healthcare", "Routine treatments and checks designed to prevent illness before it occurs. Includes vaccinations, parasite prevention, dental care, weight monitoring, and regular vet examinations."),
            ("Titre Testing", "A blood test measuring antibody levels to check if a pet's immunity from previous vaccinations is still adequate. Some owners and vets use titre tests to avoid unnecessary booster vaccinations."),
            ("Desensitisation", "A gradual exposure programme used to reduce fear responses to specific triggers. For firework fear, involves playing recorded sounds at increasing volume over several weeks to build tolerance."),
            ("Body Condition Score", "A standardised 1-9 assessment scale used to evaluate whether a pet is at ideal weight. A score of 4-5 is ideal, with 1-3 being underweight and 6-9 overweight. Should be assessed alongside weight at every vet visit.")
        ],
        "faq": [
            ("How often should I take my pet to the vet?", "Adult pets in good health should see a vet at least annually for a routine check-up and vaccination boosters. Senior pets (dogs 7+, cats 10+) should visit every 6 months. Puppies and kittens need more frequent visits during their first year for primary vaccinations and development checks."),
            ("How often should I worm my dog in the UK?", "Adult dogs should be wormed at least every 3 months (quarterly) in the UK. Dogs with higher exposure (raw fed, living with children, or frequently eating prey animals) may need monthly worming. Puppies need worming every 2 weeks until 12 weeks old, then monthly until 6 months."),
            ("When should I start preparing for fireworks?", "Begin firework preparation at least 4-6 weeks before expected events. For UK bonfire night (November 5th), start in early to mid-September. This allows time for desensitisation training, setting up safe dens, and consulting your vet about medication for severe cases."),
            ("How often should I give my dog flea treatment?", "Most UK flea treatments should be applied monthly, year-round. Even during winter, central heating keeps fleas active indoors. Check the specific product instructions as some treatments last 4, 8, or 12 weeks. Using the same product consistently is more effective than switching between brands."),
            ("When should I renew my pet insurance?", "Review your pet insurance at least 6 weeks before your renewal date. Compare prices and cover levels across multiple providers. Never let a policy lapse as pre-existing conditions from the old policy will not be covered by a new insurer. Consider that the cheapest policy is not always the best value.")
        ],
        "products": [
            ("Pet Care Planner", "Dedicated annual pet care planner with monthly sections for treatments, vet visits, weight tracking, and seasonal reminders", "pet+care+planner+annual+calendar+diary"),
            ("Pill Reminder Box", "Weekly organiser box for managing monthly and quarterly pet medications and treatments", "pill+organiser+weekly+box+medication+reminder"),
            ("Reflective Dog Lead", "High-visibility reflective lead for safe autumn and winter walking in low-light conditions", "reflective+dog+lead+high+visibility+safety"),
            ("Pet Paw Wax", "Natural protective paw wax for winter walks to guard against rock salt, ice, and chemical de-icers", "pet+paw+wax+protection+winter+natural")
        ],
        "sources": [
            "British Veterinary Association - Annual Pet Health Calendar",
            "PDSA - Preventive Pet Healthcare Guide",
            "RSPCA - Seasonal Pet Care Advice",
            "Kennel Club - Responsible Dog Ownership Calendar",
            "International Cat Care - Feline Health Calendar"
        ],
        "image_queries": ["pet owner calendar planning", "dog seasonal care outdoor", "cat indoor care routine", "veterinary appointment checkup"]
    }
]


# ──────── HELPER FUNCTIONS ────────

def fetch_pexels_image(query):
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
    try:
        img_data = requests.get(image_url, timeout=30).content
        fname = f"{filename}.jpeg"
        headers = {"Content-Disposition": f'attachment; filename="{fname}"',
                   "Content-Type": "image/jpeg"}
        r = requests.post(f"{WP}/media", auth=AUTH, headers=headers, data=img_data)
        if r.status_code == 201:
            return r.json().get("source_url", ""), r.json().get("id", 0)
    except Exception as e:
        print(f"    Upload error: {e}")
    return "", 0


def build_post_html(spoke, images):
    html_parts = []

    html_parts.append("""<div class="wp-block-group alignwide has-background" style="background-color:#fff8e1;border-left:4px solid #ff9800;padding:16px 20px;margin-bottom:30px;border-radius:6px">
<p style="margin:0;font-size:14px"><strong>Affiliate Disclosure:</strong> PetHub Online is reader-supported. When you buy through links on our site, we may earn an affiliate commission at no extra cost to you. This helps us continue providing free, research-backed pet care content. <a href="https://pethubonline.com/affiliate-disclosure/">Learn more</a>.</p>
</div>""")

    html_parts.append(f"""<div class="wp-block-group alignwide has-background" style="background-color:#e8f5e9;border-left:4px solid #4caf50;padding:18px 22px;margin-bottom:30px;border-radius:6px">
<p style="margin:0"><strong>Quick Answer:</strong> {spoke['quick_answer']}</p>
</div>""")

    toc_items = ['<li><a href="#at-a-glance">At A Glance</a></li>']
    for sec in spoke['sections']:
        anchor = re.sub(r'[^a-z0-9-]', '', sec['heading'].lower().replace(' ', '-'))[:50]
        toc_items.append(f'<li><a href="#{anchor}">{sec["heading"]}</a></li>')
    toc_items += [
        '<li><a href="#comparison-table">Comparison Table</a></li>',
        '<li><a href="#common-mistakes">Common Mistakes to Avoid</a></li>',
        '<li><a href="#what-to-do-next">What To Do Next</a></li>',
        '<li><a href="#key-terms">Key Terms</a></li>',
        '<li><a href="#faq">Frequently Asked Questions</a></li>',
        '<li><a href="#recommended-products">Recommended Products</a></li>',
        '<li><a href="#sources">Sources &amp; References</a></li>'
    ]
    html_parts.append(f"""<div class="wp-block-group alignwide" style="background:#f8f9fa;border:1px solid #e0e0e0;border-radius:8px;padding:20px 24px;margin-bottom:30px">
<h2 style="font-size:20px;margin-top:0">Table of Contents</h2>
<ol style="margin-bottom:0">{''.join(toc_items)}</ol>
</div>""")

    glance_items = ''.join(f'<li>{item}</li>' for item in spoke['at_a_glance'])
    html_parts.append(f"""<div class="wp-block-group alignwide has-background" id="at-a-glance" style="background-color:#e3f2fd;border:1px solid #90caf9;border-radius:8px;padding:20px 24px;margin-bottom:30px">
<h2 style="font-size:22px;margin-top:0">At A Glance</h2>
<ul style="margin-bottom:0">{glance_items}</ul>
</div>""")

    if len(images) > 0:
        alt_text = spoke['image_queries'][0].replace('"', '&quot;')
        html_parts.append(f'<figure class="wp-block-image alignwide size-large"><img src="{images[0]}" alt="{alt_text} - PetHub Online UK" /><figcaption>{alt_text.title()}</figcaption></figure>')

    for i, sec in enumerate(spoke['sections']):
        anchor = re.sub(r'[^a-z0-9-]', '', sec['heading'].lower().replace(' ', '-'))[:50]
        html_parts.append(f'<h2 id="{anchor}">{sec["heading"]}</h2>')
        html_parts.append(sec['content'])
        img_idx = (i // 2) + 1
        if img_idx < len(images) and i % 2 == 1:
            alt_text = spoke['image_queries'][min(img_idx, len(spoke['image_queries'])-1)].replace('"', '&quot;')
            html_parts.append(f'<figure class="wp-block-image alignwide size-large"><img src="{images[img_idx]}" alt="{alt_text} - PetHub Online UK" /><figcaption>{alt_text.title()}</figcaption></figure>')

    headers_html = ''.join(f'<th>{h}</th>' for h in spoke['comparison_table']['headers'])
    rows_html = ''.join(f'<tr>{"".join(f"<td>{c}</td>" for c in row)}</tr>' for row in spoke['comparison_table']['rows'])
    html_parts.append(f"""<div class="wp-block-group alignwide has-background" id="comparison-table" style="background-color:#f4f4f4;border-radius:8px;padding:24px;margin-bottom:30px">
<h2 style="margin-top:0">{spoke['comparison_table']['title']}</h2>
<figure class="wp-block-table"><table class="has-fixed-layout"><thead><tr>{headers_html}</tr></thead><tbody>{rows_html}</tbody></table></figure>
</div>""")

    mistakes_html = ''.join(f'<li>{m}</li>' for m in spoke['common_mistakes'])
    html_parts.append(f"""<div class="wp-block-group alignwide has-background" id="common-mistakes" style="background-color:#fce4ec;border-left:4px solid #e53935;border-radius:6px;padding:20px 24px;margin-bottom:30px">
<h2 style="font-size:22px;margin-top:0">Common Mistakes to Avoid</h2>
<ul style="margin-bottom:0">{mistakes_html}</ul>
</div>""")

    remaining_imgs = images[2:]
    if remaining_imgs:
        alt_text = spoke['image_queries'][-1].replace('"', '&quot;')
        html_parts.append(f'<figure class="wp-block-image alignwide size-large"><img src="{remaining_imgs[0]}" alt="{alt_text} - PetHub Online UK" /><figcaption>{alt_text.title()}</figcaption></figure>')

    next_items = ''.join(f'<li>{item}</li>' for item in spoke['what_to_do_next'])
    html_parts.append(f"""<div class="wp-block-group alignwide has-background" id="what-to-do-next" style="background-color:#e8f5e9;border:1px solid #81c784;border-radius:8px;padding:20px 24px;margin-bottom:30px">
<h2 style="font-size:22px;margin-top:0">What To Do Next</h2>
<ol style="margin-bottom:0">{next_items}</ol>
</div>""")

    terms_html = ''.join(f'<dt><strong>{term}</strong></dt><dd>{defn}</dd>' for term, defn in spoke['key_terms'])
    html_parts.append(f"""<div class="wp-block-group alignwide" id="key-terms" style="background:#f5f5f5;border:1px solid #e0e0e0;border-radius:8px;padding:20px 24px;margin-bottom:30px">
<h2 style="font-size:22px;margin-top:0">Key Terms</h2>
<dl style="margin-bottom:0">{terms_html}</dl>
</div>""")

    faq_html = ''
    for question, answer in spoke['faq']:
        faq_html += f"""<details class="wp-block-details alignwide has-border-color" style="border-color:#e5e5e5;border-width:1px;border-style:solid;border-radius:6px;padding:12px 16px;margin-bottom:8px">
<summary style="font-size:17px;font-weight:600;cursor:pointer">{question}</summary>
<p style="margin-top:10px">{answer}</p>
</details>"""
    html_parts.append(f'<div id="faq"><h2>Frequently Asked Questions</h2>{faq_html}</div>')

    products_html = ''
    for name, desc, search_terms in spoke['products']:
        amazon_url = f"https://www.amazon.co.uk/s?k={search_terms}&tag={AFFILIATE_TAG}"
        products_html += f"""<div class="wp-block-group" style="border:3px solid #0073aa;border-radius:12px;padding:20px;margin-bottom:16px;background:#ffffff">
<h3 style="color:#0073aa;margin-top:0">{name}</h3>
<p>{desc}</p>
<p><a href="{amazon_url}" target="_blank" rel="noopener nofollow sponsored" style="display:inline-block;background:#0073aa;color:#ffffff;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:600">Check Price on Amazon UK</a></p>
</div>"""
    html_parts.append(f"""<div id="recommended-products" style="margin-bottom:30px">
<h2>Recommended Products</h2>
<p style="font-size:14px;color:#666">These products are selected based on relevance to this guide. As an Amazon Associate, PetHub Online earns from qualifying purchases.</p>
{products_html}
</div>""")

    html_parts.append("""<div class="wp-block-group alignwide has-background" style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:12px;padding:30px;margin-bottom:30px;text-align:center">
<h2 style="color:#ffffff;margin-top:0">Get Expert Pet Care Advice</h2>
<p style="color:#f0f0f0;font-size:16px">Subscribe to PetHub Online for research-backed pet care guides, seasonal safety alerts, and exclusive resources for UK pet owners.</p>
<p><a href="https://pethubonline.com/subscribe-to-pethub-uk-newsletter/" style="display:inline-block;background:#ffffff;color:#667eea;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px">Subscribe Free</a></p>
</div>""")

    sources_html = ''.join(f'<li>{s}</li>' for s in spoke['sources'])
    html_parts.append(f"""<div class="wp-block-group alignwide" id="sources" style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:8px;padding:20px 24px;margin-bottom:30px">
<h2 style="font-size:20px;margin-top:0">Sources &amp; References</h2>
<ul style="font-size:14px;margin-bottom:0">{sources_html}</ul>
</div>""")

    html_parts.append("""<div class="wp-block-group alignwide" style="background:#f0f4f8;border-left:4px solid #0073aa;padding:16px 20px;margin-bottom:30px;border-radius:6px">
<p style="font-size:14px;margin:0"><strong>Trust &amp; Transparency:</strong> PetHub Online provides research-backed pet care information for UK pet owners. Our content is based on published veterinary guidelines, manufacturer specifications, and publicly available expert guidance. We do not fabricate credentials, invent experts, or claim hands-on testing unless explicitly stated. <a href="https://pethubonline.com/editorial-policy/">Read our editorial policy</a>.</p>
</div>""")

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
    rm_url = "https://pethubonline.com/wp-json/rankmath/v1/updateMeta"
    rm_data = {
        "objectID": post_id,
        "objectType": "post",
        "meta": {
            "rank_math_focus_keyword": spoke['focus_keyword'],
            "rank_math_title": spoke['seo_title'],
            "rank_math_description": spoke['seo_desc']
        }
    }
    try:
        r = requests.post(rm_url, auth=AUTH, json=rm_data)
        if r.status_code == 200:
            return True, "Rank Math API"
    except:
        pass
    try:
        r2 = requests.post(f"{WP}/posts/{post_id}", auth=AUTH, json={"meta": {
            "rank_math_focus_keyword": spoke['focus_keyword'],
            "rank_math_title": spoke['seo_title'],
            "rank_math_description": spoke['seo_desc']
        }})
        if r2.status_code == 200:
            return True, "WP meta fallback"
    except:
        pass
    return False, "failed"


def create_spoke_post(spoke):
    print(f"\n{'='*60}")
    print(f"Creating: {spoke['title']}")
    print(f"{'='*60}")

    print("\n[1/4] Fetching and uploading images...")
    images = []
    first_media_id = 0
    for i, query in enumerate(spoke['image_queries']):
        print(f"  Searching Pexels: '{query}'")
        img_url = fetch_pexels_image(query)
        if img_url:
            filename = f"{spoke['slug'].replace('-', '_')}_{i+1}"
            wp_url, media_id = upload_image_to_wp(img_url, filename)
            if wp_url:
                images.append(wp_url)
                if i == 0:
                    first_media_id = media_id
                print(f"  Uploaded: {wp_url[:70]}...")
            else:
                print(f"  WARN: Upload failed for '{query}'")
        else:
            print(f"  WARN: No Pexels result for '{query}'")
        time.sleep(0.5)
    print(f"  Total images: {len(images)}")

    print("\n[2/4] Building HTML content...")
    content = build_post_html(spoke, images)
    print(f"  Content length: {len(content)} characters")

    print("\n[3/4] Creating WordPress draft...")
    post_data = {
        "title": spoke['title'],
        "slug": spoke['slug'],
        "content": content,
        "status": "draft",
        "categories": [CATEGORY_PET_CARE],
    }
    if first_media_id:
        post_data["featured_media"] = first_media_id

    r = requests.post(f"{WP}/posts", auth=AUTH, json=post_data)
    if r.status_code == 201:
        post_id = r.json()['id']
        print(f"  Created post ID: {post_id}")
    else:
        print(f"  FAIL: {r.status_code}")
        print(f"  {r.text[:300]}")
        return None
    time.sleep(1)

    print("\n[4/4] Setting SEO metadata...")
    seo_ok, seo_method = set_rankmath_seo(post_id, spoke)
    if seo_ok:
        print(f"  SEO metadata set via {seo_method}: {spoke['focus_keyword']}")
    else:
        print(f"  WARN: SEO metadata could not be set")
    time.sleep(0.5)

    # Publish immediately (autonomous mode)
    print("  Publishing...")
    rp = requests.post(f"{WP}/posts/{post_id}", auth=AUTH, json={"status": "publish"})
    link = rp.json().get('link', '') if rp.status_code == 200 else 'PUBLISH FAILED'
    print(f"  Live: {link}")
    time.sleep(1)

    return {"id": post_id, "title": spoke['title'], "slug": spoke['slug'],
            "link": link, "content_length": len(content)}


if __name__ == "__main__":
    print("Phase 17E: Pet Care Expansion - 10 Spoke Posts")
    print("=" * 60)
    print(f"Target cluster: Pet Care (category {CATEGORY_PET_CARE})")
    print(f"Total spokes: {len(SPOKES)}")
    print()

    results = []
    for spoke in SPOKES:
        result = create_spoke_post(spoke)
        if result:
            results.append(result)
        time.sleep(2)

    print("\n" + "=" * 60)
    print("SUMMARY - Phase 17E Pet Care Spokes")
    print("=" * 60)
    total_chars = 0
    for r in results:
        print(f"  ID {r['id']}: {r['title']}")
        print(f"    Live: {r['link']}")
        print(f"    Content: {r['content_length']} chars")
        total_chars += r['content_length']
    print(f"\nTotal created: {len(results)}/{len(SPOKES)}")
    print(f"Total content: {total_chars:,} characters")
