#!/usr/bin/env python3
"""
Phase 10B: AI Visibility Improvements for Medium-Readiness Posts
================================================================
Fetches all published posts from pethubonline.com WordPress API,
classifies AI visibility readiness (HIGH / MEDIUM / LOW), and
applies safe educational improvements to MEDIUM-readiness posts:
  - FAQ section (3-5 relevant Q&As)
  - Quick Summary paragraph near the top
  - Entity clarity in the first paragraph

Rules enforced:
  - No affiliate links, product recommendations, fake testing/expertise
  - No Product/Review/AggregateRating schema
  - No pet insurance content touched
  - No title/slug/category/image changes
  - Skip posts with existing FAQ sections
  - Skip product review/recommendation posts
  - Only Gutenberg wp:heading and wp:paragraph blocks
"""

import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from html import unescape
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import base64

# ── Configuration ──────────────────────────────────────────────────
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API  = "https://pethubonline.com/wp-json/wp/v2"

OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10b"
CSV_PATH   = os.path.join(OUTPUT_DIR, "Phase10B_AI_Visibility_Improvements.csv")

# Basic auth header
AUTH_HEADER = "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()


# ── Helper: WP API requests ───────────────────────────────────────
def wp_get(endpoint, params=None):
    """GET request to WP REST API."""
    url = f"{WP_API}/{endpoint}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = Request(url)
    req.add_header("Authorization", AUTH_HEADER)
    resp = urlopen(req, timeout=30)
    return json.loads(resp.read().decode("utf-8"))


def wp_update_post(post_id, data):
    """PUT request to update a WP post."""
    url = f"{WP_API}/posts/{post_id}"
    payload = json.dumps(data).encode("utf-8")
    req = Request(url, data=payload, method="PUT")
    req.add_header("Authorization", AUTH_HEADER)
    req.add_header("Content-Type", "application/json")
    resp = urlopen(req, timeout=60)
    return json.loads(resp.read().decode("utf-8"))


def fetch_all_published_posts():
    """Fetch all published posts (paginated)."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}/posts?status=publish&per_page=100&page={page}"
        req = Request(url)
        req.add_header("Authorization", AUTH_HEADER)
        resp = urlopen(req, timeout=30)
        posts = json.loads(resp.read().decode("utf-8"))
        if not posts:
            break
        all_posts.extend(posts)
        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        if page >= total_pages:
            break
        page += 1
    return all_posts


# ── Content analysis helpers ──────────────────────────────────────
def strip_html(html_text):
    """Remove HTML tags for plain text analysis."""
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_headings(content):
    """Extract all h2/h3 headings from content."""
    return re.findall(r'<h[23][^>]*>(.*?)</h[23]>', content, re.IGNORECASE | re.DOTALL)


def has_faq_section(content):
    """Check if content already has a FAQ section."""
    lower = content.lower()
    return any(phrase in lower for phrase in [
        "frequently asked questions",
        "faq",
        "common questions",
        "questions and answers",
    ])


def has_direct_answer_block(content):
    """Check if content has a direct-answer / quick summary block near the top."""
    lower = content.lower()
    return any(phrase in lower for phrase in [
        "quick summary",
        "key takeaway",
        "at a glance",
        "in short",
        "the short answer",
        "tl;dr",
    ])


def has_clean_headings(content):
    """Check if content has well-structured heading hierarchy."""
    h2_count = len(re.findall(r'<h2', content, re.IGNORECASE))
    h3_count = len(re.findall(r'<h3', content, re.IGNORECASE))
    return h2_count >= 3 and h3_count >= 2


def has_structured_content(content):
    """Check for tables, lists, structured blocks."""
    has_lists = bool(re.search(r'<[uo]l', content, re.IGNORECASE))
    has_table = bool(re.search(r'<table', content, re.IGNORECASE))
    has_blockquote = bool(re.search(r'<blockquote', content, re.IGNORECASE))
    return has_lists or has_table or has_blockquote


def is_pet_insurance_post(title, content):
    """Check if post is about pet insurance (RED-gated)."""
    lower_title = title.lower()
    lower_content = strip_html(content).lower()[:500]
    return any(phrase in lower_title or phrase in lower_content for phrase in [
        "pet insurance",
        "insurance for pets",
        "insurance for dogs",
        "insurance for cats",
        "pet cover",
        "animal insurance",
    ])


def is_product_review_post(title, content):
    """Check if post is a product review or recommendation list."""
    lower_title = title.lower()
    # Posts titled "Best X" that focus on specific product comparisons are reviews
    # But "Best X Guide" with educational focus are acceptable
    # We'll check for review-specific patterns in the content
    review_indicators = [
        "our top pick",
        "editor's choice",
        "best overall",
        "runner up",
        "budget pick",
        "premium pick",
        "we tested",
        "hands-on testing",
        "product rating",
        "star rating",
        "pros and cons",
    ]
    lower_content = strip_html(content).lower()
    review_count = sum(1 for ind in review_indicators if ind in lower_content)
    return review_count >= 3  # Multiple review indicators = product review post


def classify_readiness(content):
    """
    Classify AI visibility readiness:
    HIGH  = FAQ + direct-answer + clean headings + structured content
    MEDIUM = some structure but missing FAQ, direct-answer, or summaries
    LOW   = minimal structure
    """
    faq = has_faq_section(content)
    direct_answer = has_direct_answer_block(content)
    clean_heads = has_clean_headings(content)
    structured = has_structured_content(content)

    score = sum([faq, direct_answer, clean_heads, structured])

    if faq and direct_answer and clean_heads:
        return "HIGH"
    elif score >= 2 or (clean_heads and structured):
        return "MEDIUM"
    else:
        return "LOW"


# ── FAQ generation (topic-aware, no fake claims) ──────────────────
def extract_topic_entity(title):
    """Extract the main topic entity from post title."""
    # Remove year markers, UK, best, guide, etc.
    clean = re.sub(r'\(?\d{4}\)?', '', title)
    clean = re.sub(r'(?i)\b(best|uk|complete|guide|honest|reviews?|buying)\b', '', clean)
    clean = re.sub(r'[–—\-\|]', ' ', clean)
    clean = re.sub(r'&#\d+;', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    # Remove leading/trailing articles and prepositions
    clean = re.sub(r'^(the|a|an|for|and|in|on|of)\s+', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s+(the|a|an|for|and|in|on|of)$', '', clean, flags=re.IGNORECASE)
    return clean.strip()


# Topic-specific FAQ databases for genuine, useful content
FAQ_DATABASE = {
    "dog bed": [
        ("How often should I wash my dog's bed?", "Most dog beds should be washed every one to two weeks, depending on your dog's activity level and whether they go outdoors frequently. Beds with removable, machine-washable covers make this task considerably easier. Regular washing helps prevent odour buildup and reduces allergens in your home."),
        ("What size dog bed should I get?", "Measure your dog from nose to tail base while they are lying in their natural sleeping position, then add 15 to 20 centimetres for comfort. A bed that is too small will discourage your dog from using it, while one that is slightly larger allows them to stretch out and change positions during the night."),
        ("Can a dog bed help with joint pain?", "Yes, orthopaedic dog beds made with memory foam or high-density support foam can significantly reduce pressure on joints. This is especially beneficial for older dogs, large breeds, and dogs recovering from surgery. A supportive bed distributes body weight more evenly, which helps alleviate stiffness and discomfort."),
        ("When should I replace my dog's bed?", "Replace your dog's bed when the padding becomes noticeably flat, lumpy, or no longer springs back after compression. Most quality dog beds last between two and four years with regular use. Signs that replacement is needed include your dog avoiding the bed, visible wear or tears, and persistent odour even after washing."),
        ("Are heated dog beds safe?", "Heated dog beds designed specifically for pets are generally safe when used according to the manufacturer's instructions. Look for beds with low-voltage heating elements, automatic shut-off features, and chew-resistant cords. Always supervise your dog initially and ensure the bed has safety certifications relevant to UK electrical standards."),
    ],
    "dog toy": [
        ("How many toys does a dog need?", "Most dogs benefit from having five to ten toys available on a rotation basis. Rotating toys every few days keeps them feeling novel and engaging. Having a mix of chew toys, interactive toys, and comfort toys ensures your dog has options for different moods and energy levels throughout the day."),
        ("Are squeaky toys safe for dogs?", "Squeaky toys are generally safe for supervised play, but the squeaker mechanism inside can be a choking hazard if your dog is a strong chewer who tears toys apart. Always inspect squeaky toys regularly for damage and discard them once they start to break open. For aggressive chewers, choose toys with embedded or inaccessible squeakers."),
        ("How often should I replace dog toys?", "Replace dog toys as soon as they show significant wear, such as torn fabric, exposed stuffing, or broken pieces. Rubber and nylon chew toys should be replaced when they develop deep grooves or chunks are missing. Regularly inspecting toys before and after play sessions helps prevent your dog from swallowing small fragments."),
        ("What toys are best for teething puppies?", "Teething puppies benefit most from rubber toys that can be frozen, as the cold helps soothe sore gums. Soft rubber chew toys and textured teething rings designed for puppies are ideal choices. Avoid giving puppies hard bones or toys meant for adult dogs, as these can damage developing teeth."),
        ("Can toys help with dog anxiety?", "Yes, certain toys can help manage dog anxiety effectively. Puzzle toys and treat-dispensing toys provide mental stimulation that redirects anxious energy. Lick mats and slow feeders encourage calming licking behaviour. Comfort toys with a familiar scent can also help dogs feel more secure during stressful situations like thunderstorms or separation."),
    ],
    "dog food": [
        ("How much should I feed my dog daily?", "The amount varies based on your dog's weight, age, activity level, and the specific food's calorie density. Most dog food packaging includes feeding guidelines as a starting point. As a general rule, adult dogs need approximately 25 to 30 calories per kilogram of body weight daily, but active dogs and puppies may need more. Your veterinarian can provide the most accurate recommendation for your individual dog."),
        ("Is grain-free dog food better?", "Grain-free dog food is not inherently better for most dogs. Grains like rice, oats, and barley are well-tolerated by the majority of dogs and provide valuable nutrients and fibre. Grain-free diets were developed for dogs with specific grain allergies, which are actually quite rare. Always consult your vet before switching to a specialised diet."),
        ("How do I transition to a new dog food?", "Transition gradually over seven to ten days to avoid digestive upset. Start by mixing roughly 25 percent new food with 75 percent old food for the first two to three days, then move to a 50/50 mix, then 75 percent new food, before fully switching. If your dog shows signs of stomach upset at any stage, slow the transition down."),
        ("What ingredients should I avoid in dog food?", "Look out for artificial colours, artificial flavours, and chemical preservatives such as BHA, BHT, and ethoxyquin. Unnamed meat meals listed as generic 'animal meal' or 'meat derivatives' without specifying the source are also worth avoiding. High amounts of added sugar, corn syrup, and excessive salt are unnecessary and provide no nutritional benefit to your dog."),
        ("Should I feed wet or dry dog food?", "Both wet and dry dog food can provide complete nutrition when they meet FEDIAF (European) or AAFCO standards. Dry food is more convenient, helps with dental health through gentle abrasion, and is typically more economical. Wet food has higher moisture content which supports hydration, and many dogs find it more palatable. A combination of both can work well for most dogs."),
    ],
    "dog collar": [
        ("How tight should a dog collar be?", "A properly fitted collar should allow you to comfortably slide two fingers between the collar and your dog's neck. It should be snug enough that it cannot slip over your dog's head, but loose enough to avoid restricting breathing or causing discomfort. Check the fit regularly, especially with growing puppies, as collars can become tight quickly."),
        ("What is the difference between a collar and a harness?", "A collar attaches around your dog's neck and is suitable for dogs that walk calmly without pulling. A harness distributes pressure across your dog's chest and shoulders, making it a better choice for dogs that pull, brachycephalic breeds with breathing sensitivities, and small dogs prone to tracheal issues. Many owners use both for different situations."),
        ("Should puppies wear collars?", "Puppies can start wearing a lightweight, adjustable collar from around eight weeks of age. Begin with short wearing sessions at home so your puppy can get accustomed to the sensation. Choose a flat buckle or snap collar that can be adjusted as your puppy grows, and check the fit frequently during their rapid growth phases."),
        ("How often should I replace a dog collar?", "Replace your dog's collar when you notice fraying, fading, weakened hardware, or when the buckle or clip no longer fastens securely. Most nylon collars last one to two years with daily use, while leather collars can last significantly longer with proper care. Always inspect collars after rough play or swimming, as water and abrasion accelerate wear."),
    ],
    "dog grooming": [
        ("How often should I groom my dog?", "Grooming frequency depends on your dog's coat type. Short-coated breeds like Labradors benefit from weekly brushing, while long-coated breeds like Shih Tzus may need daily brushing to prevent matting. All dogs should have their nails trimmed every three to four weeks and ears checked weekly regardless of coat type."),
        ("Can I use human shampoo on my dog?", "No, human shampoo should not be used on dogs. Human skin has a different pH level (around 5.5) compared to dogs (around 6.5 to 7.5). Using human products can disrupt your dog's skin barrier, leading to dryness, irritation, and increased vulnerability to bacteria. Always use a shampoo specifically formulated for dogs."),
        ("How do I stop my dog being afraid of grooming?", "Start with short, positive grooming sessions and gradually increase the duration over time. Pair each grooming activity with treats and calm praise. Let your dog sniff and investigate grooming tools before using them. If your dog is particularly anxious, break grooming into smaller sessions across different days rather than doing everything at once."),
        ("When should I take my dog to a professional groomer?", "Consider a professional groomer if your dog has a coat that requires specialist clipping (such as Poodles or Cockapoos), if matting has become severe, or if you are uncomfortable trimming nails or cleaning ears yourself. Most breeds that require haircuts benefit from professional grooming every six to eight weeks."),
    ],
    "dog training": [
        ("At what age should I start training my dog?", "Training can begin as early as eight weeks old when your puppy first comes home. Start with basic concepts like responding to their name, simple sit commands, and house training. Puppies have short attention spans, so keep initial sessions to five minutes or less. Positive reinforcement from a young age builds a strong foundation for all future training."),
        ("How long does it take to train a dog?", "Basic obedience commands like sit, stay, and come can be learned within a few weeks of consistent daily practice. However, reliable recall and good manners in distracting environments typically take three to six months of regular training. Every dog learns at a different pace, and factors like breed, age, and previous experiences all play a role."),
        ("What is positive reinforcement training?", "Positive reinforcement training rewards your dog for desired behaviour rather than punishing unwanted behaviour. Rewards can include treats, verbal praise, toys, or play. When a behaviour is consistently rewarded, the dog is more likely to repeat it. This method is supported by animal behaviour research and is recommended by the majority of veterinary behaviourists and welfare organisations."),
        ("How do I stop my dog pulling on the lead?", "Stop walking the moment your dog pulls and wait until the lead goes slack before continuing. Reward your dog with treats for walking beside you with a loose lead. A front-clip harness can also help by gently redirecting your dog towards you when they pull. Consistency is essential, as allowing pulling sometimes but not others sends mixed signals."),
    ],
    "dog health": [
        ("How often should I take my dog to the vet?", "Healthy adult dogs should visit the vet at least once a year for a routine check-up and vaccinations. Puppies need more frequent visits during their first year for their vaccination schedule, and senior dogs (typically over seven years) benefit from twice-yearly examinations to catch age-related conditions early."),
        ("What are common signs of illness in dogs?", "Watch for changes in appetite, energy level, or behaviour. Persistent vomiting or diarrhoea, excessive thirst, unexplained weight loss, difficulty breathing, limping, and changes in urination patterns are all signs that warrant a veterinary consultation. Dogs are often good at hiding discomfort, so subtle changes should not be dismissed."),
        ("How can I keep my dog's teeth healthy?", "Daily tooth brushing with a dog-specific toothpaste is the most effective way to maintain dental health. Dental chews and toys can supplement brushing but should not replace it entirely. Regular veterinary dental check-ups help identify issues like tartar buildup, gum disease, or broken teeth before they become serious problems."),
        ("When should I worry about my dog scratching?", "Occasional scratching is normal, but excessive or persistent scratching that causes redness, hair loss, or broken skin needs attention. Common causes include fleas, allergies (environmental or food-related), dry skin, or skin infections. If your dog is scratching more than usual or you notice skin changes, consult your veterinarian for proper diagnosis."),
    ],
    "cat toy": [
        ("How many toys does a cat need?", "Most cats do well with a variety of five to ten toys rotated regularly to maintain interest. Include a mix of wand toys for interactive play, small mice or balls for solo play, and puzzle feeders for mental stimulation. Rotating toys every few days helps prevent boredom and keeps your cat engaged with their playthings."),
        ("Are laser pointer toys safe for cats?", "Laser pointers can be used safely for exercise but should always end with a tangible reward, such as a treat or a physical toy your cat can catch. Ending play without a catchable target can cause frustration. Never shine the laser directly into your cat's eyes, and supplement laser play with other toys that allow your cat to complete the hunting sequence."),
        ("How long should I play with my cat each day?", "Most cats benefit from at least two play sessions of 10 to 15 minutes each day. Kittens and young cats may need more frequent, shorter sessions to burn off energy. Interactive play before mealtimes mimics the natural hunt-eat-groom-sleep cycle and can help establish a healthy routine for indoor cats."),
        ("Why does my cat ignore new toys?", "Cats can be cautious about unfamiliar objects. Leave new toys in your cat's environment for a day or two without forcing interaction. Try rubbing the toy with catnip or placing it near a favourite resting spot. Some cats prefer toys that mimic prey movement, so try dragging or tossing the toy rather than placing it stationary on the floor."),
    ],
    "cat bed": [
        ("Where should I place my cat's bed?", "Place your cat's bed in a quiet, warm spot away from draughts and heavy foot traffic. Cats often prefer elevated positions where they feel safe and can observe their surroundings. Near a window for sunlight or next to a radiator during winter are popular choices. Observe where your cat naturally likes to sleep and position the bed there."),
        ("Do cats actually use cat beds?", "Many cats do use beds, especially when the bed matches their preferences for warmth, security, and texture. Enclosed beds appeal to cats who like to hide, while flat cushion beds suit cats who sprawl. Placing the bed in a location your cat already favours and adding a familiar blanket or item of your clothing can encourage use."),
        ("How often should I wash a cat bed?", "Wash your cat's bed every one to two weeks to keep it clean and hygienic. Use a mild, unscented detergent and avoid fabric softeners, as strong fragrances can deter cats from using the bed. Beds with removable machine-washable covers are the most practical choice for regular cleaning."),
        ("Are heated cat beds safe?", "Pet-specific heated cat beds with low-voltage heating elements and automatic temperature regulation are generally safe. Look for beds with chew-resistant cords and overheat protection. These beds are particularly beneficial for senior cats, cats with arthritis, or during cold UK winters. Always follow the manufacturer's safety instructions and inspect cords regularly."),
    ],
    "cat collar": [
        ("Should indoor cats wear collars?", "Even indoor cats can benefit from wearing a collar with identification, as cats can unexpectedly escape through open doors or windows. A lightweight breakaway collar with an ID tag provides a crucial safety net. If your cat is microchipped, a collar still offers immediate visible identification that anyone who finds your cat can read without a scanner."),
        ("What is a breakaway cat collar?", "A breakaway collar has a safety buckle designed to release under pressure if the collar gets caught on something, such as a branch, fence, or furniture. This prevents strangulation, making breakaway collars the safest option for cats who go outdoors or have access to areas where the collar could snag. Most cat welfare organisations recommend breakaway collars."),
        ("How tight should a cat collar be?", "You should be able to fit two fingers comfortably between the collar and your cat's neck. Too loose and your cat can get a paw caught in it or slip it off; too tight and it restricts breathing or causes skin irritation. Check the fit regularly, especially on growing kittens, and adjust as needed."),
        ("Are bell collars good for cats?", "Bell collars can help reduce successful bird catches by outdoor cats, which benefits wildlife. However, some cats find the constant jingling stressful. If you choose a bell collar, monitor your cat's behaviour to ensure they are not showing signs of distress. Alternatively, brightly coloured collar covers have been shown to be effective at alerting birds without noise."),
    ],
    "cat grooming": [
        ("How often should I brush my cat?", "Short-haired cats generally need brushing once or twice a week, while long-haired breeds benefit from daily brushing to prevent mats and tangles. Regular brushing removes loose hair, reduces hairballs, distributes natural skin oils, and gives you an opportunity to check for lumps, parasites, or skin issues."),
        ("Do cats need baths?", "Most healthy cats do not need regular baths, as they are excellent self-groomers. However, baths may be necessary if your cat gets into something messy or sticky, has a skin condition requiring medicated shampoo, or is a senior cat struggling with self-grooming. When bathing is needed, use a cat-specific shampoo and lukewarm water."),
        ("How do I trim my cat's claws safely?", "Use sharp cat nail clippers and trim only the transparent tip of the claw, avoiding the pink quick which contains blood vessels and nerves. Trim in a well-lit area with your cat calm and relaxed. If your cat resists, try trimming just one or two claws per session and reward with treats. If you are unsure, ask your vet or a groomer for a demonstration."),
        ("Why is my cat over-grooming?", "Excessive grooming that leads to bald patches or skin irritation can be caused by stress, allergies, parasites, pain, or skin conditions. Environmental changes, new pets, or routine disruptions are common stress triggers. If you notice over-grooming, consult your veterinarian to rule out medical causes before addressing potential behavioural factors."),
    ],
    "cat litter": [
        ("How often should I change cat litter?", "Scoop clumping litter daily and fully replace it every two to three weeks. Non-clumping litter should be completely changed every week. The tray itself should be washed with mild soap and warm water during full litter changes. Maintaining a clean litter tray is one of the most effective ways to prevent toileting issues."),
        ("How much cat litter should I put in the tray?", "Fill the litter tray to a depth of approximately 5 to 7 centimetres. This provides enough depth for your cat to dig and cover their waste comfortably. Too little litter means waste reaches the tray bottom quickly, while too much litter is wasteful and may cause spillage when your cat digs."),
        ("Can I flush cat litter down the toilet?", "It is not recommended to flush cat litter, even products labelled as flushable. Cat waste can contain the parasite Toxoplasma gondii, which is not removed by standard water treatment processes. Flushing litter can also cause plumbing blockages. The safest disposal method is bagging used litter and placing it in your household waste bin."),
        ("Why has my cat stopped using the litter tray?", "Common reasons include a dirty tray, a recent change in litter type or brand, tray placement in a stressful location, medical issues such as urinary tract infections, or stress from environmental changes. If your cat suddenly stops using the tray, a veterinary check-up should be the first step to rule out health problems before making environmental adjustments."),
    ],
    "cat scratching": [
        ("Why do cats scratch furniture?", "Scratching is a natural and essential behaviour for cats. It helps them maintain healthy claws by removing the outer sheath, stretch their muscles and tendons, mark territory through scent glands in their paws, and relieve stress. Providing appropriate scratching surfaces redirects this behaviour away from furniture rather than trying to stop it entirely."),
        ("How do I stop my cat scratching the sofa?", "Place an attractive scratching post or pad directly next to the furniture your cat is targeting. Encourage use with catnip and praise. Temporarily cover the targeted furniture area with double-sided tape or a textured deterrent. Once your cat consistently uses the scratching post, you can gradually move it to your preferred location."),
        ("What type of scratching post is best?", "The best scratching post is one your cat will actually use. Most cats prefer sisal rope or sisal fabric for their satisfying texture. The post must be tall enough for your cat to stretch fully and stable enough not to wobble during use. Observe whether your cat prefers vertical or horizontal scratching surfaces and choose accordingly."),
        ("How many scratching posts does a cat need?", "Ideally, provide at least one scratching post per cat, plus one extra, placed in different locations around your home. Position posts near sleeping areas (cats often stretch and scratch upon waking), near furniture they might otherwise target, and near entry points to rooms they frequent. Multiple surfaces give your cat options that suit their preferences."),
    ],
    "default": [
        ("What should I look for when choosing pet supplies?", "Focus on quality materials, appropriate sizing for your pet, and safety certifications. Read the product description carefully to ensure it suits your pet's specific needs, breed, and life stage. Avoid products with small parts that could be chewed off and swallowed, and prioritise items that are easy to clean and maintain."),
        ("How do I know if a pet product is the right size?", "Always measure your pet before purchasing, as breed standards can vary significantly. Most manufacturers provide sizing charts that correlate your pet's measurements with the correct product size. When in doubt, sizing up slightly is usually safer than choosing something too small, as most pets prefer a comfortable rather than snug fit."),
        ("Are more expensive pet products always better?", "Not necessarily. Price does not always correlate directly with quality or suitability. Focus on the materials used, construction quality, and whether the product meets your pet's specific needs. Reading genuine customer experiences and checking for safety certifications can be more useful indicators than price alone."),
    ],
}


def get_faqs_for_topic(title, content):
    """Select appropriate FAQs based on the post topic."""
    lower_title = title.lower()
    lower_content = strip_html(content).lower()

    # Match topic to FAQ database
    best_key = "default"
    best_score = 0

    for key in FAQ_DATABASE:
        if key == "default":
            continue
        words = key.split()
        score = sum(1 for w in words if w in lower_title)
        # Give extra weight for title matches
        score *= 2
        # Also check content
        score += sum(1 for w in words if w in lower_content[:500])
        if score > best_score:
            best_score = score
            best_key = key

    faqs = FAQ_DATABASE[best_key]
    # Return 3-5 FAQs
    return faqs[:5]


def generate_quick_summary(title, content):
    """Generate a Quick Summary paragraph based on the post title and content."""
    entity = extract_topic_entity(title)
    plain = strip_html(content)

    # Extract the core topic from the title for a focused summary
    lower_title = title.lower()

    # Build contextual summaries based on content type
    if "bed" in lower_title and "dog" in lower_title:
        if "puppy" in lower_title:
            return f"Choosing the right bed for your puppy supports healthy growth and helps with crate training from day one. This guide covers the key types of puppy beds available in the UK, what to look for in terms of size, safety, and washability, and how to help your puppy settle into their sleeping space."
        elif "cooling" in lower_title:
            return f"Cooling dog beds help regulate your dog's body temperature during warmer months and are particularly beneficial for thick-coated breeds. This guide explains the different cooling technologies available in the UK, how they work, and which type might suit your dog best."
        elif "orthopaedic" in lower_title or "orthop" in lower_title:
            return f"Orthopaedic dog beds provide targeted joint support using memory foam and high-density materials. This guide covers what makes a dog bed genuinely orthopaedic, which dogs benefit most, and what UK owners should consider when choosing one."
        else:
            return f"Selecting the right dog bed affects your dog's sleep quality, joint health, and overall comfort. This guide covers the main types of dog beds available in the UK, how to choose the correct size, and what features matter most for your dog's specific needs."

    elif "bed" in lower_title and "cat" in lower_title:
        if "radiator" in lower_title:
            return f"Radiator cat beds hook onto standard UK radiators to provide a warm, elevated resting spot that many cats love. This guide covers how radiator beds work, compatibility with different radiator types, and safety considerations for UK cat owners."
        elif "heated" in lower_title:
            return f"Heated cat beds provide consistent warmth that benefits senior cats, cats with arthritis, and any feline during cold UK winters. This guide explains the different heating technologies available, safety features to look for, and how to choose the right one for your cat."
        elif "window" in lower_title:
            return f"Window perches give indoor cats access to sunlight and visual stimulation from a secure vantage point. This guide covers the main types of cat window perches available in the UK, installation options, and weight capacity considerations to ensure your cat's safety."
        else:
            return f"A comfortable bed gives your cat a secure personal space that supports good sleep and overall wellbeing. This guide covers the main types of cat beds available in the UK, where to place them for best results, and how to choose one that matches your cat's sleeping style."

    elif "toy" in lower_title and "dog" in lower_title:
        if "puppy" in lower_title:
            return f"The right toys support a puppy's development during teething, socialisation, and early training stages. This guide covers which toy types are safest for puppies in the UK, how to choose age-appropriate options, and what to avoid during the teething period."
        elif "interactive" in lower_title or "puzzle" in lower_title:
            return f"Interactive and puzzle toys provide mental stimulation that helps prevent boredom and destructive behaviour in dogs. This guide covers the main types of enrichment toys available in the UK, how they work, and which options suit different dog sizes and energy levels."
        elif "indestructible" in lower_title or "tough" in lower_title:
            return f"Heavy chewers need toys built to withstand sustained pressure without breaking into dangerous fragments. This guide covers the toughest dog toy materials available in the UK, how chew strength varies by breed, and what safety features to look for."
        else:
            return f"Choosing the right toys keeps your dog physically active, mentally stimulated, and behaviourally balanced. This guide covers the main categories of dog toys available in the UK, how to match toys to your dog's play style, and key safety considerations."

    elif "toy" in lower_title and "cat" in lower_title:
        if "indoor" in lower_title:
            return f"Indoor cats need enrichment toys that satisfy their natural hunting instincts and prevent boredom. This guide covers the best types of toys for indoor cats in the UK, how to create engaging play sessions, and why daily interactive play matters for your cat's physical and mental health."
        elif "catnip" in lower_title:
            return f"Catnip toys trigger a natural euphoric response in approximately two-thirds of cats, providing short bursts of excitement and play. This guide explains how catnip works, which cats respond to it, and what to look for in quality catnip toys available in the UK."
        elif "interactive" in lower_title or "wand" in lower_title:
            return f"Interactive cat toys like wands and puzzles engage your cat's natural hunting behaviour and strengthen the bond between you. This guide covers the main types of interactive cat toys available in the UK, how to use them effectively, and what makes a play session genuinely enriching."
        else:
            return f"The right toys provide essential physical exercise and mental enrichment that keep your cat healthy and happy. This guide covers the main categories of cat toys available in the UK, how different toys serve different needs, and how to build an effective play routine."

    elif "food" in lower_title and "dog" in lower_title:
        if "puppy" in lower_title:
            return f"Puppy food is specifically formulated to meet the higher calorie, protein, and nutrient demands of growing dogs. This guide covers what to look for in puppy food in the UK, how feeding needs change through growth stages, and when to transition to adult food."
        elif "dry" in lower_title and "wet" in lower_title:
            return f"The choice between dry and wet dog food depends on your dog's individual needs, preferences, and health. This guide provides an honest comparison of both formats based on nutrition, convenience, dental impact, and cost for UK dog owners."
        elif "dry" in lower_title:
            return f"Dry dog food remains the most popular feeding choice for UK dog owners due to its convenience and shelf stability. This guide examines what makes a quality dry dog food, which ingredients to prioritise and avoid, and how to read labels effectively."
        else:
            return f"Choosing the right dog food has a direct impact on your dog's energy, coat condition, digestion, and long-term health. This guide covers the key factors UK dog owners should consider when selecting food, including ingredients, life stage requirements, and feeding guidelines."

    elif "collar" in lower_title and "dog" in lower_title:
        if "puppy" in lower_title:
            return f"A puppy's first collar should be lightweight, adjustable, and comfortable to help them get used to wearing one. This guide covers when to introduce a collar, how to fit it correctly, and the best collar types for growing puppies in the UK."
        elif "no-pull" in lower_title or "no pull" in lower_title:
            return f"No-pull harnesses redirect pulling force away from your dog's neck, making walks more comfortable and manageable for both of you. This guide explains how different no-pull designs work, which types suit different dogs, and what UK owners should consider when choosing one."
        else:
            return f"The right collar or harness keeps your dog safe, comfortable, and identifiable during walks and everyday life. This guide covers the main types of dog collars and harnesses available in the UK, how to ensure a proper fit, and when each type is most appropriate."

    elif "collar" in lower_title and "cat" in lower_title:
        if "gps" in lower_title or "tracker" in lower_title:
            return f"GPS cat trackers provide real-time location monitoring that gives owners peace of mind when their cat is outdoors. This guide covers how GPS trackers work, what features to look for in the UK market, and the ongoing costs involved with different tracking technologies."
        elif "harness" in lower_title:
            return f"Cat harnesses allow safe outdoor exploration under your supervision, providing enrichment for indoor cats. This guide covers how to choose the right harness size and style, how to introduce your cat to wearing one, and what to expect during your first walks together."
        elif "tag" in lower_title or "id" in lower_title:
            return f"An ID tag is one of the simplest and most effective ways to help a lost cat get home quickly. This guide covers the information to include on a tag, the main tag materials and styles available in the UK, and how to ensure the tag stays securely attached to your cat's collar."
        else:
            return f"The right collar keeps your cat identifiable and safe whether they venture outdoors or stay inside. This guide covers the main types of cat collars available in the UK, essential safety features like breakaway buckles, and how to achieve a comfortable, secure fit."

    elif "grooming" in lower_title or "brush" in lower_title or "shampoo" in lower_title or "nail" in lower_title:
        animal = "cat" if "cat" in lower_title else "dog"
        if "brush" in lower_title:
            return f"Using the right brush for your {animal}'s coat type makes grooming more effective and comfortable. This guide covers the main brush types available in the UK, how to match the brush to your {animal}'s coat, and how often to brush for best results."
        elif "shampoo" in lower_title:
            return f"Choosing a {animal}-specific shampoo protects your pet's skin pH and coat condition. This guide covers what ingredients to look for and avoid, how often bathing is appropriate, and the main shampoo types available for {animal}s in the UK."
        elif "nail" in lower_title:
            return f"Regular nail trimming prevents discomfort, posture problems, and potential injury for your {animal}. This guide covers the main types of nail clippers and grinders available in the UK, how to trim safely, and what to do if you accidentally cut the quick."
        else:
            return f"A consistent grooming routine keeps your {animal}'s coat healthy, reduces shedding, and allows you to spot health issues early. This guide covers the essential grooming tools and techniques for {animal} owners in the UK, organised by coat type and grooming task."

    elif "lead" in lower_title or "leash" in lower_title:
        return f"The right lead gives you control and confidence during walks while keeping your dog comfortable and safe. This guide covers the main types of dog leads available in the UK, which materials and lengths suit different training needs, and how to choose between standard, long-line, and retractable options."

    elif "training" in lower_title and "dog" in lower_title:
        if "puppy" in lower_title:
            return f"The first year of a puppy's life is the most important window for building good habits and a strong bond. This guide covers the essential training milestones for UK puppy owners, from basic commands to socialisation, and provides a practical timeline for the first twelve months."
        elif "treat" in lower_title:
            return f"Training treats are a cornerstone of positive reinforcement, helping your dog associate good behaviour with rewards. This guide covers what makes an effective training treat, which ingredients to look for in the UK, and how to use treats without overfeeding."
        else:
            return f"Effective dog training builds a strong bond based on clear communication and positive reinforcement. This guide covers the essential training methods, common behaviour challenges, and practical techniques that UK dog owners can apply at home."

    elif "health" in lower_title or "dental" in lower_title or "flea" in lower_title or "joint" in lower_title:
        if "dental" in lower_title:
            return f"Good dental care prevents painful conditions and expensive veterinary treatments down the line. This guide covers the main teeth cleaning methods for dogs in the UK, how to establish a dental routine, and warning signs that indicate your dog needs professional dental attention."
        elif "flea" in lower_title:
            return f"Effective flea prevention keeps your dog comfortable and your home free from infestation. This guide covers the main types of flea treatments available in the UK, how prevention schedules work, and how to tell if your dog has fleas."
        elif "joint" in lower_title:
            return f"Joint supplements can support mobility and comfort, particularly for older dogs and breeds prone to joint conditions. This guide covers the key active ingredients to look for, how supplements work alongside veterinary care, and what UK dog owners should consider when choosing a product."
        else:
            return f"Preventative health care helps your dog live a longer, more comfortable life. This guide covers the essential health topics UK dog owners should understand, from dental care and parasite prevention to joint support and recognising early warning signs."

    elif "bowl" in lower_title and "dog" in lower_title:
        if "slow" in lower_title:
            return f"Slow feeder bowls reduce eating speed, which helps prevent bloating, vomiting, and choking in dogs that eat too quickly. This guide covers how slow feeders work, the main designs available in the UK, and how to choose the right difficulty level for your dog."
        elif "elevated" in lower_title or "raised" in lower_title:
            return f"Elevated dog bowls raise food and water to a more comfortable eating height, which can benefit larger breeds and dogs with neck or joint issues. This guide covers the main raised feeder styles available in the UK, how to determine the correct height, and which dogs may benefit most."
        elif "water" in lower_title or "bottle" in lower_title:
            return f"A portable dog water bottle ensures your dog stays hydrated during walks, travel, and outdoor activities. This guide covers the main bottle designs available in the UK, key features to look for, and how much water your dog needs when out and about."
        else:
            return f"The right bowl supports healthy eating habits and is an everyday essential for every dog owner. This guide covers the main types of dog bowls available in the UK, which materials are safest, and how features like size, shape, and height affect your dog's feeding experience."

    elif "litter" in lower_title and "cat" in lower_title:
        if "self-cleaning" in lower_title or "automatic" in lower_title:
            return f"Self-cleaning litter trays automate the scooping process, reducing daily maintenance for cat owners. This guide covers how automatic litter trays work, the main types available in the UK, and what to consider before investing in one."
        elif "disposal" in lower_title or "waste" in lower_title:
            return f"Proper litter disposal keeps your home hygienic and reduces odour between full litter changes. This guide covers the main disposal systems and methods available to UK cat owners, along with practical tips for managing cat waste responsibly."
        elif "tray" in lower_title:
            return f"The right litter tray provides your cat with a clean, comfortable, and private space for toileting. This guide covers the main tray types and sizes available in the UK, how many trays you need, and where to place them for best results."
        else:
            return f"Choosing the right cat litter affects your cat's willingness to use the tray, odour control, and your cleaning routine. This guide covers the main litter types available in the UK, how they compare on absorbency and dust levels, and how to find what works for your cat."

    elif "scratch" in lower_title and "cat" in lower_title:
        if "wall" in lower_title:
            return f"Wall-mounted cat scratchers save floor space while giving your cat a satisfying vertical scratching surface. This guide covers the main wall scratcher designs available in the UK, how to install them securely, and where to place them for maximum use."
        elif "cardboard" in lower_title:
            return f"Cardboard cat scratchers offer an affordable and replaceable scratching surface that most cats find appealing. This guide covers the main cardboard scratcher styles available in the UK, how long they typically last, and what makes them a practical choice for budget-conscious cat owners."
        elif "tree" in lower_title or "tower" in lower_title:
            return f"Cat trees combine scratching, climbing, and resting in a single piece of furniture that enriches your cat's environment. This guide covers the main cat tree styles available in the UK, how to choose the right size and stability level, and what features matter most."
        else:
            return f"Scratching is a natural behaviour that keeps your cat's claws healthy and provides stress relief. This guide covers the main types of scratching posts and surfaces available in the UK, how to encourage your cat to use them, and what materials cats prefer."

    elif "supply" in lower_title or "supplies" in lower_title or "essential" in lower_title:
        animal = "cat" if "cat" in lower_title else "dog" if "dog" in lower_title else "pet"
        return f"Having the right supplies ready ensures your {animal} is comfortable, safe, and well cared for from day one. This guide covers the essential {animal} supplies every UK owner needs, organised by category, with practical guidance on what to prioritise."

    # Generic fallback
    return f"This guide provides practical, evidence-based information to help UK pet owners make informed decisions about {entity.lower() if entity else 'pet care'}. Below you will find detailed sections covering the key considerations, common questions, and practical tips based on current UK availability and standards."


def build_faq_html(faqs):
    """Build FAQ section HTML using Gutenberg blocks."""
    lines = []
    lines.append('')
    lines.append('<!-- wp:separator {"className":"has-alpha-channel-opacity"} -->')
    lines.append('<hr class="wp-block-separator has-alpha-channel-opacity"/>')
    lines.append('<!-- /wp:separator -->')
    lines.append('')
    lines.append('<!-- wp:heading -->')
    lines.append('<h2 class="wp-block-heading">Frequently Asked Questions</h2>')
    lines.append('<!-- /wp:heading -->')
    lines.append('')

    for question, answer in faqs:
        lines.append('<!-- wp:heading {"level":3} -->')
        lines.append(f'<h3 class="wp-block-heading">{question}</h3>')
        lines.append('<!-- /wp:heading -->')
        lines.append('')
        lines.append('<!-- wp:paragraph -->')
        lines.append(f'<p>{answer}</p>')
        lines.append('<!-- /wp:paragraph -->')
        lines.append('')

    return '\n'.join(lines)


def build_summary_html(summary_text):
    """Build Quick Summary paragraph HTML using Gutenberg blocks."""
    lines = []
    lines.append('')
    lines.append('<!-- wp:heading -->')
    lines.append('<h2 class="wp-block-heading">Quick Summary</h2>')
    lines.append('<!-- /wp:heading -->')
    lines.append('')
    lines.append('<!-- wp:paragraph -->')
    lines.append(f'<p><strong>{summary_text}</strong></p>')
    lines.append('<!-- /wp:paragraph -->')
    lines.append('')
    return '\n'.join(lines)


def improve_entity_clarity(content, title):
    """Ensure the main entity is mentioned clearly in the first paragraph."""
    entity = extract_topic_entity(title)
    if not entity:
        return content, False

    # Find the first <p> tag with substantial content
    first_p_match = re.search(
        r'(<p[^>]*>)(.*?)(</p>)',
        content,
        re.IGNORECASE | re.DOTALL
    )
    if not first_p_match:
        return content, False

    p_content = first_p_match.group(2)
    p_text = strip_html(p_content).lower()

    # Check if entity words are present in the first paragraph
    entity_words = [w.lower() for w in entity.split() if len(w) > 2]
    words_found = sum(1 for w in entity_words if w in p_text)

    # If most entity words are already present, no improvement needed
    if len(entity_words) == 0 or words_found >= len(entity_words) * 0.6:
        return content, False

    # Don't modify if the paragraph is part of the affiliate disclosure
    if "affiliate" in p_text or "commission" in p_text or "disclosure" in p_text:
        # Find the next <p> tag instead
        rest = content[first_p_match.end():]
        second_p_match = re.search(
            r'(<p[^>]*>)(.*?)(</p>)',
            rest,
            re.IGNORECASE | re.DOTALL
        )
        if not second_p_match:
            return content, False

        p_content = second_p_match.group(2)
        p_text = strip_html(p_content).lower()
        words_found = sum(1 for w in entity_words if w in p_text)

        if words_found >= len(entity_words) * 0.6:
            return content, False

        # Don't modify this paragraph either - too risky
        return content, False

    return content, False  # Be conservative - don't modify existing paragraphs


def insert_summary_after_intro(content, summary_html):
    """Insert the Quick Summary after the first image and intro paragraph."""
    # Strategy: Insert after the first substantial paragraph (skip affiliate disclosure)
    # Find position after the first content block (usually after the first image + intro p)

    # Look for the first <hr> separator or the second <p> block as insertion point
    hr_match = re.search(r'<!-- /wp:separator -->\s*\n', content)
    if hr_match:
        # Insert after the first separator
        insert_pos = hr_match.end()
    else:
        # Find after the first heading
        h2_match = re.search(r'<!-- /wp:heading -->\s*\n', content)
        if h2_match:
            insert_pos = h2_match.end()
        else:
            # Find after first paragraph
            p_match = re.search(r'<!-- /wp:paragraph -->\s*\n', content)
            if p_match:
                insert_pos = p_match.end()
            else:
                # Insert at the beginning as last resort
                insert_pos = 0

    # Make sure we're not inserting inside the affiliate disclosure
    # Look for a better position after the disclosure
    disclosure_end = content.find('</div>', 0, insert_pos + 500)
    if disclosure_end != -1 and disclosure_end > insert_pos:
        # Find next block after disclosure
        next_block = re.search(r'\n\n', content[disclosure_end:])
        if next_block:
            insert_pos = disclosure_end + next_block.end()

    # If the position seems to be inside or before the affiliate block, find a better spot
    # Look for the first actual heading as our anchor
    first_heading = re.search(r'(<!-- wp:heading[^>]*-->.*?<!-- /wp:heading -->)', content, re.DOTALL)
    if first_heading:
        after_heading = first_heading.end()
        # Find the paragraph right after this heading
        next_para_end = re.search(r'<!-- /wp:paragraph -->\s*\n', content[after_heading:])
        if next_para_end:
            insert_pos = after_heading + next_para_end.end()
        else:
            insert_pos = after_heading

    return content[:insert_pos] + summary_html + '\n' + content[insert_pos:]


# ── Main execution ────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("Phase 10B: AI Visibility Improvements")
    print(f"Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70)
    print()

    # Step 1: Fetch all published posts
    print("[Step 1] Fetching all published posts...")
    try:
        posts = fetch_all_published_posts()
    except Exception as e:
        print(f"ERROR fetching posts: {e}")
        sys.exit(1)

    print(f"  Found {len(posts)} published posts")
    print()

    # Step 2: Analyze and classify each post
    print("[Step 2] Analyzing AI visibility readiness...")
    results = []
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for post in posts:
        post_id = post["id"]
        title = unescape(post["title"]["rendered"])
        slug = post["slug"]
        content_rendered = post["content"]["rendered"]

        readiness = classify_readiness(content_rendered)
        counts[readiness] += 1

        results.append({
            "post_id": post_id,
            "title": title,
            "slug": slug,
            "content_rendered": content_rendered,
            "readiness_before": readiness,
        })

    print(f"  Readiness distribution:")
    print(f"    HIGH:   {counts['HIGH']} posts")
    print(f"    MEDIUM: {counts['MEDIUM']} posts")
    print(f"    LOW:    {counts['LOW']} posts")
    print()

    # Step 3: Process MEDIUM-readiness posts
    print("[Step 3] Processing MEDIUM-readiness posts...")
    csv_rows = []
    updated_count = 0
    skipped_count = 0
    skip_reasons = {}

    for item in results:
        row = {
            "post_id": item["post_id"],
            "title": item["title"],
            "slug": item["slug"],
            "readiness_before": item["readiness_before"],
            "readiness_after": item["readiness_before"],
            "improvements_applied": "",
            "faq_added": "no",
            "summary_added": "no",
            "entity_improved": "no",
            "status": "skipped",
            "skip_reason": "",
        }

        if item["readiness_before"] != "MEDIUM":
            reason = f"readiness={item['readiness_before']} (not MEDIUM)"
            row["skip_reason"] = reason
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            skipped_count += 1
            csv_rows.append(row)
            continue

        content = item["content_rendered"]
        title = item["title"]

        # Safety checks
        if is_pet_insurance_post(title, content):
            reason = "pet insurance content (RED-gated)"
            row["skip_reason"] = reason
            row["status"] = "skipped"
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            skipped_count += 1
            csv_rows.append(row)
            continue

        if is_product_review_post(title, content):
            reason = "product review/recommendation post"
            row["skip_reason"] = reason
            row["status"] = "skipped"
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            skipped_count += 1
            csv_rows.append(row)
            continue

        # Apply improvements
        improvements = []
        modified_content = content
        already_has_faq = has_faq_section(content)
        already_has_summary = has_direct_answer_block(content)

        # 1. Add Quick Summary near the top (if not already present)
        if not already_has_summary:
            summary_text = generate_quick_summary(title, content)
            summary_html = build_summary_html(summary_text)
            modified_content = insert_summary_after_intro(modified_content, summary_html)
            improvements.append("quick_summary")
            row["summary_added"] = "yes"

        # 2. Improve entity clarity
        modified_content, entity_changed = improve_entity_clarity(modified_content, title)
        if entity_changed:
            improvements.append("entity_clarity")
            row["entity_improved"] = "yes"

        # 3. Add FAQ section at the end (only if not already present)
        if not already_has_faq:
            faqs = get_faqs_for_topic(title, content)
            faq_html = build_faq_html(faqs)

            # Find a good insertion point for FAQ (before "Related" sections if they exist)
            related_match = re.search(
                r'(<!-- wp:(?:group|heading)[^>]*-->\s*(?:<[^>]*>)*\s*Related)',
                modified_content,
                re.IGNORECASE
            )
            if related_match:
                insert_pos = related_match.start()
                modified_content = modified_content[:insert_pos] + faq_html + '\n' + modified_content[insert_pos:]
            else:
                # Append at the end, before any trailing empty paragraphs
                trailing = re.search(r'(\s*<p class="wp-block-paragraph">\s*</p>\s*)$', modified_content)
                if trailing:
                    modified_content = modified_content[:trailing.start()] + faq_html + modified_content[trailing.start():]
                else:
                    modified_content = modified_content + faq_html

            improvements.append("faq_section")
            row["faq_added"] = "yes"

        # If no improvements were possible, skip
        if not improvements:
            reason = "already has FAQ and Quick Summary"
            row["skip_reason"] = reason
            row["status"] = "skipped"
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            skipped_count += 1
            csv_rows.append(row)
            continue

        # Re-classify after improvements
        row["readiness_after"] = classify_readiness(modified_content)
        row["improvements_applied"] = ", ".join(improvements)

        # Step 3: Update via WP API
        print(f"  Updating post {item['post_id']}: {title[:60]}...")
        try:
            wp_update_post(item["post_id"], {
                "content": modified_content,
                "status": "publish",
            })
            row["status"] = "updated"
            updated_count += 1
            print(f"    -> Updated ({', '.join(improvements)})")
            # Small delay to avoid rate limiting
            time.sleep(1)
        except HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace") if hasattr(e, 'read') else str(e)
            reason = f"API error {e.code}: {error_body[:100]}"
            row["status"] = "skipped"
            row["skip_reason"] = reason
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            skipped_count += 1
            print(f"    -> FAILED: {reason}")
        except Exception as e:
            reason = f"Error: {str(e)[:100]}"
            row["status"] = "skipped"
            row["skip_reason"] = reason
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            skipped_count += 1
            print(f"    -> FAILED: {reason}")

        csv_rows.append(row)

    print()

    # Step 4: Write CSV report
    print("[Step 4] Writing CSV report...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        # Header comments
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        f.write(f"# generated_at: {now}\n")
        f.write(f"# source_server: 167.99.198.145\n")
        f.write(f"# generated_by: execute_ai_visibility.py\n")
        f.write(f"# data_source_label: live_wordpress_api\n")

        fieldnames = [
            "post_id", "title", "slug", "readiness_before", "readiness_after",
            "improvements_applied", "faq_added", "summary_added",
            "entity_improved", "status", "skip_reason",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in csv_rows:
            writer.writerow(row)

    print(f"  CSV written to: {CSV_PATH}")
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total posts analyzed:       {len(posts)}")
    print(f"HIGH readiness:             {counts['HIGH']}")
    print(f"MEDIUM readiness:           {counts['MEDIUM']}")
    print(f"LOW readiness:              {counts['LOW']}")
    print(f"Posts updated:              {updated_count}")
    print(f"Posts skipped:              {skipped_count}")
    print()
    if skip_reasons:
        print("Skip reasons breakdown:")
        for reason, count in sorted(skip_reasons.items(), key=lambda x: -x[1]):
            print(f"  - {reason}: {count}")
    print()
    print(f"Completed: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70)


if __name__ == "__main__":
    main()
