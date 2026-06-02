#!/usr/bin/env python3
"""
Phase 24C - FAQPage JSON-LD Schema Completion for PetHub Online
Audits ALL published posts and adds FAQ schema where missing.
"""

import requests
import json
import time
import re
import os
import html
from datetime import datetime
from requests.auth import HTTPBasicAuth

# ── Config ──────────────────────────────────────────────────────────────
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = HTTPBasicAuth("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
HEADERS = {
    "Accept-Encoding": "gzip, deflate",
    "Content-Type": "application/json",
}
RESULTS_PATH = "/var/lib/freelancer/projects/40416335/phase24c_faq_completion_results.json"
DELAY = 2        # seconds between API calls
RETRY_WAIT = 10  # seconds on 429

# ── FAQ Generation ──────────────────────────────────────────────────────
def generate_faqs(title):
    """Generate 5 relevant FAQ Q&As based on the post title/topic."""
    # Clean the title
    clean = html.unescape(re.sub(r'<[^>]+>', '', title)).strip()

    # Extract key topic from title
    topic = clean

    # Remove common prefixes/suffixes
    for prefix in ["How to ", "Why ", "What ", "The Best ", "Top ", "A Guide to ", "Guide to ", "Ultimate Guide to "]:
        if topic.lower().startswith(prefix.lower()):
            topic = topic[len(prefix):]
            break

    # Determine if it's about a specific pet type
    pet_type = "pet"
    pet_keywords = {
        "dog": ["dog", "puppy", "canine", "pup", "doggy"],
        "cat": ["cat", "kitten", "feline", "kitty"],
        "bird": ["bird", "parrot", "parakeet", "cockatiel", "avian"],
        "fish": ["fish", "aquarium", "tank", "goldfish", "betta"],
        "rabbit": ["rabbit", "bunny", "hare"],
        "hamster": ["hamster", "gerbil", "guinea pig"],
        "reptile": ["reptile", "snake", "lizard", "gecko", "turtle", "tortoise"],
        "horse": ["horse", "pony", "equine", "foal"],
    }

    title_lower = clean.lower()
    for ptype, keywords in pet_keywords.items():
        if any(kw in title_lower for kw in keywords):
            pet_type = ptype
            break

    # Detect topic categories
    is_health = any(w in title_lower for w in ["health", "disease", "sick", "vet", "medical", "symptom", "treatment", "cure", "infection", "pain", "allergy", "allergies", "vaccine", "vaccination"])
    is_food = any(w in title_lower for w in ["food", "feed", "diet", "nutrition", "eat", "meal", "treat", "snack", "kibble", "raw diet"])
    is_training = any(w in title_lower for w in ["train", "training", "behavior", "behaviour", "obedience", "trick", "command", "socialize", "socialization"])
    is_grooming = any(w in title_lower for w in ["groom", "grooming", "bath", "brush", "nail", "fur", "coat", "shed", "shedding", "haircut"])
    is_breed = any(w in title_lower for w in ["breed", "breeds", "type", "types", "species"])
    is_care = any(w in title_lower for w in ["care", "caring", "look after", "maintain", "maintenance", "tips"])
    is_product = any(w in title_lower for w in ["best", "top", "review", "buy", "product", "recommend", "toy", "toys", "bed", "cage", "crate", "leash", "collar", "harness"])
    is_adoption = any(w in title_lower for w in ["adopt", "adoption", "rescue", "shelter", "rehome", "foster"])
    is_safety = any(w in title_lower for w in ["safe", "safety", "danger", "toxic", "poison", "protect", "hazard", "risk"])
    is_travel = any(w in title_lower for w in ["travel", "trip", "car", "fly", "flight", "vacation", "road trip", "transport"])
    is_exercise = any(w in title_lower for w in ["exercise", "walk", "run", "play", "activity", "active", "energy"])
    is_puppy_kitten = any(w in title_lower for w in ["puppy", "kitten", "baby", "newborn", "young", "juvenile"])
    is_senior = any(w in title_lower for w in ["senior", "old", "aging", "elderly", "older"])
    is_cost = any(w in title_lower for w in ["cost", "price", "expensive", "cheap", "affordable", "budget", "money", "spend"])

    faqs = []

    if is_health:
        faqs = [
            {"q": f"What are the most common health issues related to {clean.lower()}?",
             "a": f"Common health concerns related to {clean.lower()} include infections, nutritional deficiencies, and breed-specific conditions. Regular veterinary checkups can help identify these issues early. Always consult your veterinarian if you notice any unusual symptoms in your {pet_type}."},
            {"q": f"When should I take my {pet_type} to the vet regarding {topic.lower()}?",
             "a": f"You should visit your veterinarian if your {pet_type} shows persistent symptoms for more than 24-48 hours, experiences sudden behavioral changes, stops eating or drinking, or shows signs of pain. Early intervention often leads to better treatment outcomes and can prevent complications."},
            {"q": f"Can {topic.lower()} be prevented in {pet_type}s?",
             "a": f"Many health issues can be prevented or minimized through proper nutrition, regular exercise, routine veterinary care, and maintaining a clean living environment. Preventive measures like vaccinations, parasite control, and dental care also play important roles in your {pet_type}'s overall health."},
            {"q": f"What are the warning signs I should watch for with {topic.lower()}?",
             "a": f"Key warning signs include changes in appetite, lethargy, unusual discharge, changes in bathroom habits, excessive scratching or licking, weight loss or gain, and behavioral changes. If you notice any of these symptoms persisting, schedule a veterinary appointment promptly."},
            {"q": f"How much does treatment for {topic.lower()} typically cost?",
             "a": f"Treatment costs vary widely depending on the severity and specific condition. Basic veterinary visits typically range from $50-$200, while specialized treatments can cost significantly more. Pet insurance can help manage unexpected medical expenses. Discuss treatment options and costs with your veterinarian to find the best approach for your situation."},
        ]
    elif is_food:
        faqs = [
            {"q": f"What is the best diet for {pet_type}s when it comes to {topic.lower()}?",
             "a": f"The ideal diet depends on your {pet_type}'s age, size, activity level, and health condition. High-quality commercial foods that list real protein as the first ingredient are generally recommended. Consult your veterinarian for personalized dietary recommendations specific to your {pet_type}'s needs."},
            {"q": f"How often should I feed my {pet_type} based on {topic.lower()} guidelines?",
             "a": f"Feeding frequency depends on your {pet_type}'s age and size. Puppies and kittens typically need 3-4 meals daily, while adult animals usually do well with 2 meals per day. Senior {pet_type}s may benefit from smaller, more frequent meals. Always follow portion guidelines and adjust based on your {pet_type}'s weight and activity level."},
            {"q": f"Are there foods that are dangerous for {pet_type}s?",
             "a": f"Yes, several common human foods are toxic to {pet_type}s. These include chocolate, grapes, raisins, onions, garlic, xylitol, and caffeine for dogs and cats. Always research before sharing human food with your {pet_type}, and keep potentially harmful foods securely stored away from your pet's reach."},
            {"q": f"Should I consider homemade or raw diets for my {pet_type}?",
             "a": f"While homemade and raw diets can be beneficial, they require careful planning to ensure complete nutrition. Without proper formulation, these diets may lack essential vitamins and minerals. If you choose a homemade diet, work with a veterinary nutritionist to create a balanced meal plan for your {pet_type}."},
            {"q": f"How do I know if my {pet_type}'s current diet is meeting their nutritional needs?",
             "a": f"Signs of good nutrition include a healthy coat, consistent energy levels, normal weight, regular digestion, and bright eyes. If your {pet_type} shows dull fur, low energy, weight changes, or digestive issues, their diet may need adjustment. Regular veterinary checkups with weight monitoring help ensure your {pet_type}'s nutritional needs are being met."},
        ]
    elif is_training:
        faqs = [
            {"q": f"What is the best age to start {topic.lower()} with my {pet_type}?",
             "a": f"Training can begin as early as 8 weeks for puppies and kittens, starting with basic socialization and simple commands. The key is to keep sessions short, positive, and age-appropriate. Early training helps establish good behaviors and strengthens the bond between you and your {pet_type}."},
            {"q": f"How long does it take to see results from {topic.lower()}?",
             "a": f"Most {pet_type}s begin showing improvement within 1-2 weeks of consistent training. However, fully establishing new behaviors typically takes 4-8 weeks of regular practice. Patience and consistency are essential, and every {pet_type} learns at their own pace."},
            {"q": f"What training methods work best for {topic.lower()}?",
             "a": f"Positive reinforcement is widely considered the most effective and humane training method. This involves rewarding desired behaviors with treats, praise, or play. Avoid punishment-based methods as they can create fear and anxiety. Consistency, patience, and short training sessions of 5-15 minutes yield the best results."},
            {"q": f"Can older {pet_type}s still learn through {topic.lower()}?",
             "a": f"Absolutely! While younger animals may learn faster, older {pet_type}s are fully capable of learning new behaviors and commands. The saying 'you can't teach an old dog new tricks' is a myth. Older {pet_type}s may simply need more patience and shorter training sessions to accommodate their attention span and energy levels."},
            {"q": f"Should I hire a professional trainer for {topic.lower()}?",
             "a": f"Professional trainers can be extremely helpful, especially for behavioral issues, aggression, or if you are a first-time {pet_type} owner. Look for certified trainers who use positive reinforcement methods. Group classes are great for socialization, while private sessions address specific behavioral concerns more effectively."},
        ]
    elif is_grooming:
        faqs = [
            {"q": f"How often should I groom my {pet_type} as part of {topic.lower()}?",
             "a": f"Grooming frequency depends on your {pet_type}'s breed and coat type. Long-haired breeds may need daily brushing, while short-haired breeds typically need grooming once or twice a week. Regular grooming prevents matting, reduces shedding, and helps you spot potential skin issues early."},
            {"q": f"What grooming tools are essential for {topic.lower()}?",
             "a": f"Essential grooming tools include a breed-appropriate brush or comb, nail clippers or grinder, gentle pet shampoo, ear cleaning solution, and a toothbrush with pet-safe toothpaste. Investing in quality tools makes the grooming process easier and more comfortable for both you and your {pet_type}."},
            {"q": f"How can I make grooming less stressful for my {pet_type}?",
             "a": f"Start grooming routines early in your {pet_type}'s life to build comfort. Use positive reinforcement with treats and praise during sessions. Keep initial sessions short and gradually increase duration. Ensure a calm environment and handle your {pet_type} gently. If your {pet_type} becomes very stressed, take breaks and try again later."},
            {"q": f"Can I do {topic.lower()} at home, or should I use a professional?",
             "a": f"Basic grooming like brushing, bathing, and ear cleaning can easily be done at home. However, tasks like breed-specific haircuts, difficult nail trimming, or handling anxious {pet_type}s may benefit from professional grooming. Many owners combine home maintenance with periodic professional grooming sessions for the best results."},
            {"q": f"What are signs that my {pet_type} needs professional grooming attention?",
             "a": f"Signs include severely matted fur, overgrown nails that affect walking, persistent odor despite regular bathing, ear infections, skin irritation, or excessive shedding. If you notice any of these issues, professional grooming can address them safely. Regular grooming helps prevent these problems from developing in the first place."},
        ]
    elif is_product:
        faqs = [
            {"q": f"What should I look for when choosing {topic.lower()} for my {pet_type}?",
             "a": f"When selecting products for your {pet_type}, consider quality of materials, safety ratings, size appropriateness, durability, and reviews from other {pet_type} owners. Look for products that are non-toxic and designed specifically for {pet_type}s. Price does not always indicate quality, so research thoroughly before purchasing."},
            {"q": f"How much should I expect to spend on {topic.lower()}?",
             "a": f"Prices vary widely depending on brand, quality, and specific features. Budget-friendly options can be found starting around $10-$30, while premium products may cost $50-$150 or more. Consider the long-term value and durability rather than just the initial price when making your decision."},
            {"q": f"Are there any safety concerns with {topic.lower()}?",
             "a": f"Always check for small parts that could be a choking hazard, toxic materials, and sharp edges. Look for products that meet safety standards and have been tested for {pet_type}s. Monitor your {pet_type} when introducing new products and replace worn or damaged items promptly to prevent injuries."},
            {"q": f"Where is the best place to buy {topic.lower()}?",
             "a": f"Quality {pet_type} products can be found at specialty pet stores, veterinary clinics, and reputable online retailers. Online shopping offers convenience and often better prices, but make sure to read reviews and buy from trusted sellers. Local pet stores allow you to see products in person and get expert advice."},
            {"q": f"How often should I replace {topic.lower()} for my {pet_type}?",
             "a": f"Replacement frequency depends on the product type and how heavily your {pet_type} uses it. Toys should be replaced when showing signs of wear or damage. Bedding should be replaced every 1-2 years or when it loses its support. Food and water bowls should be replaced if cracked or heavily scratched, as bacteria can accumulate in damaged surfaces."},
        ]
    elif is_adoption:
        faqs = [
            {"q": f"What should I consider before {topic.lower()}?",
             "a": f"Before adopting a {pet_type}, consider your living space, daily schedule, budget for food and veterinary care, family members' allergies, and long-term commitment. Ensure everyone in your household is prepared for the responsibility. Research the specific needs of the {pet_type} you are considering to ensure a good match."},
            {"q": f"Where is the best place to adopt a {pet_type}?",
             "a": f"Reputable animal shelters, rescue organizations, and breed-specific rescues are excellent places to adopt. These organizations typically provide health screenings, vaccinations, and spaying or neutering before adoption. Avoid purchasing from puppy mills or unverified online sellers to promote ethical pet ownership."},
            {"q": f"What does the {pet_type} adoption process typically involve?",
             "a": f"The adoption process usually includes filling out an application, meeting the {pet_type}, a home visit or check, paying an adoption fee, and a trial period. Fees typically cover vaccinations, microchipping, and spaying or neutering. The process ensures that both you and the {pet_type} are a good match."},
            {"q": f"How do I help my newly adopted {pet_type} adjust to their new home?",
             "a": f"Give your new {pet_type} a quiet, safe space to decompress. Introduce family members and other pets gradually. Maintain a consistent routine for feeding, walks, and bedtime. Be patient as adjustment can take days to weeks. Provide plenty of love, positive reinforcement, and allow them to explore at their own pace."},
            {"q": f"What supplies do I need before bringing a new {pet_type} home?",
             "a": f"Essential supplies include food and water bowls, appropriate food, a comfortable bed, a collar with ID tag, leash, toys, grooming supplies, and a crate or carrier. You should also schedule an initial veterinary appointment and {pet_type}-proof your home by removing hazardous items and securing dangerous areas."},
        ]
    elif is_travel:
        faqs = [
            {"q": f"How do I prepare my {pet_type} for {topic.lower()}?",
             "a": f"Start by ensuring your {pet_type} is comfortable with their carrier or travel crate through gradual introduction at home. Visit your vet for a health check and ensure vaccinations are current. Pack essential supplies including food, water, medications, waste bags, and comfort items like a favorite toy or blanket."},
            {"q": f"Is it safe to travel long distances with my {pet_type}?",
             "a": f"Most healthy {pet_type}s can travel safely with proper preparation. Consult your veterinarian before long trips, especially for senior pets or those with health conditions. Take regular breaks during car travel, never leave your {pet_type} unattended in a vehicle, and ensure proper ventilation and comfortable temperatures throughout the journey."},
            {"q": f"What documents do I need when traveling with my {pet_type}?",
             "a": f"Essential documents include current vaccination records, a health certificate from your veterinarian (especially for air travel or crossing borders), your {pet_type}'s microchip information, and any required permits. For international travel, research destination-specific requirements well in advance as quarantine periods may apply."},
            {"q": f"How can I reduce my {pet_type}'s travel anxiety?",
             "a": f"Gradually acclimate your {pet_type} to travel with short practice trips. Use calming aids like pheromone sprays or anxiety wraps. Maintain routine feeding and walking schedules as much as possible. Bring familiar items from home for comfort. In severe cases, consult your veterinarian about anti-anxiety medications for travel."},
            {"q": f"What are the best travel accessories for {pet_type}s?",
             "a": f"Essential travel accessories include an airline-approved carrier, collapsible food and water bowls, a car safety harness or seat belt attachment, portable water bottle, waste bags, a first aid kit, and identification tags with your travel contact information. A GPS tracker can provide extra peace of mind during travels."},
        ]
    elif is_safety:
        faqs = [
            {"q": f"What are the biggest safety risks for {pet_type}s regarding {topic.lower()}?",
             "a": f"Common safety risks include toxic plants and foods, household chemicals, small objects that could be swallowed, open windows or unsecured balconies, and extreme temperatures. Being aware of these hazards and taking preventive measures can significantly reduce the risk of accidents and keep your {pet_type} safe."},
            {"q": f"How can I {pet_type}-proof my home for {topic.lower()}?",
             "a": f"Secure cabinets containing chemicals and medications, cover electrical cords, remove toxic plants, install baby gates near stairs, secure trash cans, and store small objects out of reach. Check your home from your {pet_type}'s perspective to identify potential hazards you might otherwise miss."},
            {"q": f"What should I do in case of a {pet_type} emergency?",
             "a": f"Keep your veterinarian's number and the nearest emergency animal hospital contact readily available. Have a pet first aid kit prepared. Know basic pet first aid including how to handle choking, wounds, and poisoning. Stay calm, assess the situation, and seek professional veterinary care as quickly as possible."},
            {"q": f"Are there common household items that are toxic to {pet_type}s?",
             "a": f"Yes, many common items are dangerous for {pet_type}s including chocolate, certain plants like lilies and sago palms, antifreeze, cleaning products, medications like ibuprofen and acetaminophen, and some essential oils. Keep these items securely stored and contact your vet or animal poison control immediately if ingestion is suspected."},
            {"q": f"How do I keep my {pet_type} safe outdoors?",
             "a": f"Use a secure leash or harness during walks, ensure your yard is properly fenced, avoid letting your {pet_type} near treated lawns or gardens, provide shade and water in hot weather, and be cautious around wildlife. Microchipping and updated ID tags are essential in case your {pet_type} gets lost during outdoor activities."},
        ]
    elif is_exercise:
        faqs = [
            {"q": f"How much exercise does my {pet_type} need daily?",
             "a": f"Exercise needs vary by breed, age, and health. Most dogs need 30 minutes to 2 hours of daily activity, while cats benefit from 15-30 minutes of play. Young and active breeds require more exercise, while senior {pet_type}s need gentler, shorter sessions. Consult your vet for personalized recommendations."},
            {"q": f"What are the best exercise activities for {pet_type}s?",
             "a": f"Great activities include walks, fetch, swimming, agility training, and interactive play with toys. For indoor exercise, puzzle toys, treat-dispensing games, and hide-and-seek work well. Vary activities to keep your {pet_type} mentally stimulated and physically engaged while preventing boredom."},
            {"q": f"What are the signs my {pet_type} is not getting enough exercise?",
             "a": f"Common signs include weight gain, destructive behavior, excessive barking or meowing, restlessness, hyperactivity, and depression. Under-exercised {pet_type}s may also develop behavioral problems. If you notice these signs, gradually increase your {pet_type}'s activity level and provide more mental stimulation."},
            {"q": f"Can too much exercise be harmful to my {pet_type}?",
             "a": f"Yes, over-exercising can lead to joint problems, heat exhaustion, paw pad injuries, and muscle strains. This is especially concerning for growing puppies, senior {pet_type}s, and brachycephalic breeds. Watch for signs of fatigue like excessive panting, limping, or reluctance to continue, and provide rest breaks."},
            {"q": f"How do I exercise my {pet_type} during bad weather?",
             "a": f"Indoor options include interactive toys, puzzle feeders, indoor fetch in safe spaces, stair climbing, treadmill training for dogs, and play sessions with wand toys for cats. Mental exercise through training sessions and food puzzles can also tire your {pet_type} out. Many pet stores and indoor facilities offer play areas for rainy days."},
        ]
    elif is_breed:
        faqs = [
            {"q": f"How do I choose the right {pet_type} breed for my lifestyle?",
             "a": f"Consider your living space, activity level, work schedule, family composition, and experience with {pet_type}s. Active breeds need more exercise, while some breeds are better suited for apartments. Research temperament, grooming needs, and health predispositions. Meeting the breed in person through shelters or reputable breeders can help you make an informed decision."},
            {"q": f"What are the most popular {pet_type} breeds for families?",
             "a": f"Family-friendly breeds are typically known for being patient, gentle, and adaptable. For dogs, Labrador Retrievers, Golden Retrievers, and Beagles are popular choices. For cats, Ragdolls, Maine Coons, and British Shorthairs are excellent family companions. Always consider individual temperament alongside breed characteristics."},
            {"q": f"Do different {pet_type} breeds have different health concerns?",
             "a": f"Yes, many breeds have genetic predispositions to specific health conditions. For example, large dog breeds are more prone to hip dysplasia, while flat-faced breeds may have breathing difficulties. Research breed-specific health issues before choosing a {pet_type} and ensure regular veterinary checkups to catch any issues early."},
            {"q": f"Are mixed breed {pet_type}s healthier than purebreds?",
             "a": f"Mixed breed {pet_type}s often benefit from greater genetic diversity, which can reduce the risk of some inherited conditions. However, they can still develop health issues. Both mixed and purebred {pet_type}s need regular veterinary care, proper nutrition, and exercise. The individual animal's health depends on many factors beyond breed alone."},
            {"q": f"How much does breed affect a {pet_type}'s temperament and behavior?",
             "a": f"Breed provides general behavioral tendencies, but individual personality varies significantly. Genetics influence traits like energy level, trainability, and social behavior, but environment, training, and socialization play equally important roles. Every {pet_type} is unique, so spend time with an individual animal before making assumptions based solely on breed."},
        ]
    elif is_cost:
        faqs = [
            {"q": f"What is the average annual cost of owning a {pet_type}?",
             "a": f"Annual costs vary by {pet_type} type and size but typically range from $500 to $2,000 or more. This includes food, veterinary care, grooming, toys, and supplies. Unexpected medical expenses can add significantly to these costs. Budgeting for both routine and emergency expenses is essential for responsible {pet_type} ownership."},
            {"q": f"What are the biggest expenses of {pet_type} ownership?",
             "a": f"The largest expenses are typically veterinary care, food, and grooming. Emergency medical treatments can cost thousands of dollars. Other significant costs include pet insurance, boarding or pet-sitting, training, and supplies like beds, crates, and toys. These costs should all be factored into your budget before adopting."},
            {"q": f"How can I save money on {pet_type} care without compromising quality?",
             "a": f"Buy food in bulk, learn basic grooming at home, keep up with preventive veterinary care to avoid costly emergencies, compare prices across pet stores and online retailers, and take advantage of vaccination clinics. Pet insurance can help manage unexpected costs. Avoid cutting corners on nutrition and healthcare as this can lead to higher costs long-term."},
            {"q": f"Is pet insurance worth the cost?",
             "a": f"Pet insurance can be very valuable, especially for unexpected emergencies or chronic conditions. Monthly premiums typically range from $20 to $60 depending on coverage level and your {pet_type}'s breed and age. Compare plans carefully, reading the fine print for exclusions and waiting periods. For many {pet_type} owners, insurance provides financial peace of mind."},
            {"q": f"What hidden costs should I expect as a new {pet_type} owner?",
             "a": f"Hidden costs include pet deposits for rentals, travel expenses for pet-friendly accommodations, replacement of damaged furniture or belongings, higher utility bills for climate control, and time off work for veterinary appointments. Training classes, licensing fees, and microchipping are additional costs that new owners often overlook."},
        ]
    else:
        # General / catch-all FAQs
        faqs = [
            {"q": f"What are the most important things to know about {clean.lower()}?",
             "a": f"Understanding {clean.lower()} requires knowledge of proper care routines, nutrition, health monitoring, and creating a safe environment for your {pet_type}. Regular veterinary checkups, a balanced diet, adequate exercise, and plenty of love and attention are the foundations of good {pet_type} care. Stay informed through reputable sources and consult professionals when needed."},
            {"q": f"How does {clean.lower()} affect my {pet_type}'s overall well-being?",
             "a": f"This topic directly impacts your {pet_type}'s physical health, mental stimulation, and quality of life. Proper attention to {clean.lower()} can prevent common problems, strengthen your bond with your {pet_type}, and ensure they live a happy, healthy life. Consistency and attention to your {pet_type}'s individual needs are key."},
            {"q": f"What common mistakes do {pet_type} owners make regarding {clean.lower()}?",
             "a": f"Common mistakes include not doing enough research, ignoring early warning signs of problems, following outdated advice, and not consulting veterinary professionals when needed. Many owners also underestimate the time and financial commitment involved. Staying educated and proactive helps avoid these pitfalls."},
            {"q": f"Where can I find reliable information about {clean.lower()}?",
             "a": f"Reliable sources include your veterinarian, board-certified veterinary specialists, reputable pet care organizations like the ASPCA and AKC, and peer-reviewed veterinary journals. Be cautious with social media advice and always verify information with professional sources. Your {pet_type}'s veterinarian should always be your primary resource for health-related questions."},
            {"q": f"How can I tell if my approach to {clean.lower()} is working?",
             "a": f"Positive indicators include a healthy weight, shiny coat, good energy levels, normal eating and bathroom habits, and a happy demeanor. Regular veterinary checkups provide objective health assessments. If you notice any negative changes in your {pet_type}'s health or behavior, consult your veterinarian to adjust your approach accordingly."},
        ]

    return faqs


def build_faq_html(faqs):
    """Build the FAQ HTML section with JSON-LD schema."""
    # Build JSON-LD
    main_entity = []
    for faq in faqs:
        main_entity.append({
            "@type": "Question",
            "name": faq["q"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": faq["a"]
            }
        })

    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": main_entity
    }

    json_ld = json.dumps(schema, ensure_ascii=False)

    # Build visible FAQ HTML
    faq_html = '\n<h2>Frequently Asked Questions</h2>\n'
    faq_html += f'<script type="application/ld+json">{json_ld}</script>\n'

    for faq in faqs:
        faq_html += f'<h3>{faq["q"]}</h3>\n<p>{faq["a"]}</p>\n'

    return faq_html


def api_request(method, url, retries=3, **kwargs):
    """Make an API request with retry logic for 429."""
    for attempt in range(retries):
        try:
            if method == "GET":
                resp = requests.get(url, auth=AUTH, headers=HEADERS, timeout=30, **kwargs)
            elif method == "POST":
                resp = requests.post(url, auth=AUTH, headers=HEADERS, timeout=60, **kwargs)
            else:
                raise ValueError(f"Unknown method: {method}")

            if resp.status_code == 429:
                print(f"  [429] Rate limited. Waiting {RETRY_WAIT}s (attempt {attempt+1}/{retries})...")
                time.sleep(RETRY_WAIT)
                continue

            return resp
        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] Request failed: {e} (attempt {attempt+1}/{retries})")
            if attempt < retries - 1:
                time.sleep(5)
            else:
                raise
    return resp  # Return last response even if 429


def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1

    while True:
        print(f"  Fetching page {page}...")
        url = f"{WP_BASE}/posts?per_page=100&page={page}&_fields=id,title,content&status=publish"
        resp = api_request("GET", url)

        if resp.status_code != 200:
            print(f"  [ERROR] Status {resp.status_code} on page {page}: {resp.text[:200]}")
            break

        posts = resp.json()
        if not posts:
            break

        all_posts.extend(posts)
        print(f"  Got {len(posts)} posts (total: {len(all_posts)})")

        # Check for more pages
        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        if page >= total_pages:
            break

        page += 1
        time.sleep(DELAY)

    return all_posts


def has_faq_schema(content):
    """Check if content already has FAQPage JSON-LD schema."""
    if not content:
        return False
    rendered = content.get("rendered", "")
    return "FAQPage" in rendered


def main():
    print("=" * 60)
    print("Phase 24C - FAQPage JSON-LD Schema Completion")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    # Step 1: Fetch all posts
    print("\n[1/4] Fetching all published posts...")
    all_posts = fetch_all_posts()
    total = len(all_posts)
    print(f"  Total published posts: {total}")

    # Step 2: Audit FAQ coverage
    print("\n[2/4] Auditing FAQPage schema coverage...")
    have_faq = []
    missing_faq = []

    for post in all_posts:
        pid = post["id"]
        title = post["title"]["rendered"] if isinstance(post["title"], dict) else post["title"]

        if has_faq_schema(post.get("content", {})):
            have_faq.append({"id": pid, "title": title})
        else:
            missing_faq.append({"id": pid, "title": title})

    print(f"  Already have FAQ schema: {len(have_faq)}")
    print(f"  Missing FAQ schema: {len(missing_faq)}")

    # Step 3: Fix missing posts
    print(f"\n[3/4] Adding FAQ schema to {len(missing_faq)} posts...")
    fixed = []
    errors = []

    for i, post_info in enumerate(missing_faq):
        pid = post_info["id"]
        title = post_info["title"]
        clean_title = html.unescape(re.sub(r'<[^>]+>', '', title)).strip()

        print(f"\n  [{i+1}/{len(missing_faq)}] Post {pid}: {clean_title[:60]}...")

        try:
            # First fetch the full content for this post
            time.sleep(DELAY)
            resp = api_request("GET", f"{WP_BASE}/posts/{pid}?_fields=id,content&context=edit")

            if resp.status_code != 200:
                err = f"Failed to fetch post {pid}: status {resp.status_code}"
                print(f"    [ERROR] {err}")
                errors.append({"id": pid, "title": clean_title, "error": err})
                continue

            post_data = resp.json()
            # context=edit returns raw content
            current_content = post_data.get("content", {})
            if isinstance(current_content, dict):
                current_content = current_content.get("raw", current_content.get("rendered", ""))

            # Double-check it doesn't have FAQ already (in raw content)
            if "FAQPage" in current_content:
                print(f"    [SKIP] Already has FAQ in raw content")
                have_faq.append({"id": pid, "title": clean_title})
                continue

            # Generate FAQs
            faqs = generate_faqs(clean_title)
            faq_html = build_faq_html(faqs)

            # Append FAQ to content
            new_content = current_content + faq_html

            # Update the post
            time.sleep(DELAY)
            update_resp = api_request("POST", f"{WP_BASE}/posts/{pid}",
                                       json={"content": new_content})

            if update_resp.status_code == 200:
                print(f"    [OK] FAQ schema added successfully")
                fixed.append({
                    "id": pid,
                    "title": clean_title,
                    "faq_count": len(faqs),
                    "questions": [f["q"] for f in faqs]
                })
            else:
                err = f"Update failed: status {update_resp.status_code} - {update_resp.text[:200]}"
                print(f"    [ERROR] {err}")
                errors.append({"id": pid, "title": clean_title, "error": err})

        except Exception as e:
            err = f"Exception: {str(e)}"
            print(f"    [ERROR] {err}")
            errors.append({"id": pid, "title": clean_title, "error": err})

    # Step 4: Save results
    print(f"\n[4/4] Saving results...")

    results = {
        "timestamp": datetime.now().isoformat(),
        "site": "pethubonline.com",
        "phase": "24C - FAQPage JSON-LD Schema Completion",
        "total_posts_scanned": total,
        "already_have_faq": len(have_faq),
        "missing_faq": len(missing_faq),
        "fixed_count": len(fixed),
        "errors": len(errors),
        "fixed_posts": fixed,
        "error_details": errors,
        "posts_with_existing_faq": [p["id"] for p in have_faq],
    }

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"RESULTS SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total posts scanned:    {total}")
    print(f"  Already had FAQ schema: {len(have_faq)}")
    print(f"  Missing FAQ schema:     {len(missing_faq)}")
    print(f"  Successfully fixed:     {len(fixed)}")
    print(f"  Errors:                 {len(errors)}")
    print(f"  Coverage:               {((len(have_faq) + len(fixed)) / total * 100) if total > 0 else 0:.1f}%")
    print(f"\n  Results saved to: {RESULTS_PATH}")
    print(f"  Completed: {datetime.now().isoformat()}")

    if errors:
        print(f"\n  Error details:")
        for err in errors:
            print(f"    - Post {err['id']} ({err['title'][:40]}): {err['error'][:80]}")


if __name__ == "__main__":
    main()
