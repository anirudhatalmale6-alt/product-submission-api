#!/usr/bin/env python3
"""
PetHub Online Phase 11 - Search Opportunity Engine
Identifies content gaps and search opportunities per cluster.
"""

import csv
import json
import os
import subprocess
import time
import re

DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10cc_data"
OUT_DIR = "/var/lib/freelancer/projects/40416335/phase11_data"

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2/posts"

# ---------------------------------------------------------------------------
# 1. Fetch all published posts from WordPress
# ---------------------------------------------------------------------------

def fetch_all_posts():
    """Fetch all published posts from WP REST API."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}?per_page=100&page={page}&context=edit"
        print(f"  Fetching page {page}...")
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"  Failed to parse page {page}, stopping.")
            break

        if isinstance(data, dict) and "code" in data:
            # WP returns error object when past last page
            print(f"  Reached end of posts (page {page}).")
            break

        if not isinstance(data, list) or len(data) == 0:
            break

        all_posts.extend(data)
        print(f"  Got {len(data)} posts (total: {len(all_posts)})")

        if len(data) < 100:
            break

        page += 1
        time.sleep(2)

    return all_posts


def extract_post_info(posts):
    """Extract title, cluster, and content keywords from posts."""
    post_data = []
    for p in posts:
        title_raw = p.get("title", {})
        if isinstance(title_raw, dict):
            title = title_raw.get("rendered", title_raw.get("raw", ""))
        else:
            title = str(title_raw)

        # Strip HTML entities
        title = title.replace("&#8211;", "-").replace("&#8217;", "'").replace("&amp;", "&")
        title = re.sub(r'<[^>]+>', '', title)

        # Get categories
        cats = p.get("categories", [])

        # Get content text (strip HTML for keyword matching)
        content_raw = p.get("content", {})
        if isinstance(content_raw, dict):
            content = content_raw.get("rendered", content_raw.get("raw", ""))
        else:
            content = str(content_raw)
        content_text = re.sub(r'<[^>]+>', '', content).lower()

        post_data.append({
            "id": p.get("id"),
            "title": title,
            "categories": cats,
            "content_lower": content_text[:3000],  # First 3000 chars for matching
            "title_lower": title.lower(),
        })
    return post_data


# ---------------------------------------------------------------------------
# 2. Cluster mappings and seed search intents
# ---------------------------------------------------------------------------

# Load cluster info from phase10cc
def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(filename, rows, fieldnames):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  -> Wrote {path} ({len(rows)} rows)")


# Comprehensive seed search intents per cluster
CLUSTER_INTENTS = {
    "Dog Food": {
        "informational": [
            "best grain free dog food UK 2026",
            "raw dog food guide UK complete",
            "dog food for sensitive stomachs UK",
            "puppy feeding schedule by age and weight",
            "dog food allergy symptoms and solutions",
            "how much to feed a dog by weight UK",
            "best dog food for senior dogs UK",
            "homemade dog food recipes UK safe ingredients",
            "dog food ingredients to avoid toxic list",
            "best dog food for small breeds UK",
            "cold pressed dog food benefits vs kibble",
            "hypoallergenic dog food UK options guide",
            "dog food rotation diet benefits",
            "best budget dog food UK that's still healthy",
        ],
        "commercial": [
            "raw dog food delivery UK comparison",
            "best subscription dog food UK services",
            "Butternut Box vs tails.com honest comparison",
            "best freeze dried dog food UK",
        ],
        "comparison": [
            "wet vs dry vs raw dog food comparison UK",
            "grain free vs grain inclusive dog food debate",
            "cold pressed vs extruded kibble comparison",
            "fresh dog food vs kibble cost comparison UK",
        ],
        "how-to": [
            "how to switch dog food without upset stomach",
            "how to read dog food labels UK guide",
            "how to make homemade dog treats UK",
            "how to feed a fussy eater dog UK tips",
        ],
    },
    "Dog Beds": {
        "informational": [
            "best dog bed for arthritis UK orthopaedic guide",
            "dog bed size guide by breed chart",
            "elevated dog bed benefits UK complete guide",
            "waterproof dog beds UK outdoor use guide",
            "calming dog beds UK do they actually work",
            "best indestructible dog beds UK chew-proof",
            "dog crate bed vs crate mat differences",
            "heated dog beds UK safety and benefits",
            "travel dog beds UK portable options",
            "best dog bed for large breeds UK",
        ],
        "commercial": [
            "best luxury dog beds UK premium brands",
            "best washable dog beds UK machine-friendly",
        ],
        "comparison": [
            "memory foam vs orthopaedic dog bed comparison",
            "raised vs flat dog bed which is better",
            "bolster vs nest dog bed comparison guide",
        ],
        "how-to": [
            "how to clean a dog bed properly UK",
            "how to stop dog chewing their bed",
            "how to choose the right dog bed for your breed",
        ],
    },
    "Dog Care": {
        "informational": [
            "dog dental care guide UK teeth cleaning at home",
            "dog ear cleaning guide UK safe methods",
            "dog paw care winter UK protection guide",
            "seasonal dog care checklist UK by month",
            "dog bathing frequency guide how often UK",
            "senior dog care checklist UK complete guide",
            "dog eye care and cleaning UK guide",
            "dog skin care UK dry skin and allergies",
            "dog grooming at home vs professional UK cost",
            "first aid kit for dogs UK essentials list",
            "dog microchipping UK guide legal requirements",
            "dog insurance UK what to look for guide",
        ],
        "commercial": [
            "best dog grooming tools UK starter kit",
            "best dog dental chews UK vet recommended",
        ],
        "comparison": [
            "professional vs home dog grooming UK comparison",
            "dog wipes vs dog shampoo which to use when",
            "manual vs electric dog nail clippers comparison",
        ],
        "how-to": [
            "how to clip dog nails at home safely UK",
            "how to clean dog ears without stress",
            "how to brush a double-coated dog UK guide",
            "how to check dog for ticks UK step by step",
        ],
    },
    "Dog Health": {
        "informational": [
            "common dog health problems UK by breed",
            "dog vaccination schedule UK complete guide",
            "dog flea treatment guide UK best options",
            "dog worm treatment guide UK schedule",
            "dog joint supplements UK do they work",
            "dog anxiety signs and calming solutions UK",
            "dog weight management guide UK healthy weight",
            "dog digestive health guide UK probiotics",
            "dog hip dysplasia symptoms and management UK",
            "kennel cough symptoms treatment UK guide",
            "dog heatstroke prevention UK summer safety",
            "dog dental disease signs UK when to see vet",
        ],
        "commercial": [
            "best dog joint supplements UK glucosamine",
            "best dog calming supplements UK natural options",
        ],
        "comparison": [
            "spot-on vs tablet flea treatment comparison UK",
            "natural vs chemical flea treatment for dogs UK",
            "dog insurance vs vet plan UK cost comparison",
        ],
        "how-to": [
            "how to give a dog a tablet UK easy methods",
            "how to check if your dog is overweight UK",
            "how to help a dog with separation anxiety UK",
            "how to keep dogs cool in summer UK heatwave guide",
        ],
    },
    "Dog Toys": {
        "informational": [
            "best dog toys for teething puppies UK",
            "dog enrichment toys UK mental stimulation guide",
            "best water toys for dogs UK swimming play",
            "dog fetch toys guide UK best balls and launchers",
            "squeaky toys for dogs UK safety guide",
            "best rope toys for dogs UK tug play guide",
            "dog toy safety guide UK what to watch for",
            "best toys for dogs home alone UK separation",
            "seasonal dog toy guide UK summer and winter",
            "dog toy subscription boxes UK comparison",
        ],
        "commercial": [
            "best Kong alternatives UK indestructible stuffable toys",
            "best dog puzzle feeders UK slow feeding",
        ],
        "comparison": [
            "rubber vs nylon dog toys durability comparison",
            "Kong vs West Paw vs Nylabone comparison UK",
            "interactive vs passive dog toys which is better",
        ],
        "how-to": [
            "how to stuff a Kong for dogs UK recipes",
            "how to make DIY dog toys at home UK",
            "how to rotate dog toys to keep interest",
        ],
    },
    "Dog Harnesses": {
        "informational": [
            "best dog harness for small dogs UK",
            "dog harness sizing guide UK how to measure",
            "best front-clip harness UK for pulling dogs",
            "padded dog harness UK comfort guide",
            "dog harness for car travel UK safety rated",
            "best dog harness for puppies UK first harness",
            "step-in vs overhead dog harness comparison",
            "reflective dog harness UK night walking safety",
            "dog harness for disabled dogs UK mobility",
            "best dog harness for French Bulldogs UK",
        ],
        "commercial": [
            "best no-pull dog harness UK tested and reviewed",
            "Julius K9 vs Ruffwear harness comparison UK",
        ],
        "comparison": [
            "harness vs head collar for pulling dogs comparison",
            "Y-harness vs H-harness comparison guide UK",
            "cheap vs premium dog harness UK worth the price",
        ],
        "how-to": [
            "how to put on a dog harness correctly UK",
            "how to stop a dog pulling on harness UK",
            "how to adjust a dog harness for perfect fit",
        ],
    },
    "Dog Supplies": {
        "informational": [
            "essential dog supplies checklist UK new owner",
            "dog travel supplies UK road trip essentials",
            "dog walking accessories UK must-have gear",
            "dog ID tags UK legal requirements guide",
            "best dog bowls UK stainless vs ceramic vs slow feeder",
            "dog crate guide UK sizing and training",
            "dog gate guide UK baby gates for dogs",
            "outdoor dog supplies UK garden and kennel",
            "dog poop bag guide UK biodegradable options",
            "dog whistle training UK frequency and use guide",
            "best dog coat UK waterproof winter jackets",
            "dog first aid supplies UK emergency kit list",
        ],
        "commercial": [
            "best dog subscription boxes UK monthly treats",
            "best dog water bottles UK portable and travel",
        ],
        "comparison": [
            "plastic vs stainless vs ceramic dog bowl comparison",
            "retractable vs fixed length dog lead comparison UK",
            "dog crate vs dog pen vs playpen comparison",
        ],
        "how-to": [
            "how to crate train a dog UK step by step",
            "how to choose the right dog crate size UK",
            "how to set up a puppy pen correctly UK",
        ],
    },
    "Cat Supplies": {
        "informational": [
            "best cat litter UK 2026 complete guide",
            "cat carrier guide UK best options for travel",
            "best cat water fountain UK running water guide",
            "cat scratching post guide UK types and materials",
            "best cat bowls UK elevated and slow feeder",
            "cat collar UK safety breakaway guide",
            "cat microchip UK legal requirements guide",
            "best cat flap UK microchip and manual options",
            "cat grooming gloves UK do they work",
            "best cat tree UK guide by cat size",
            "cat harness and lead UK outdoor training guide",
            "best cat litter tray UK open vs covered guide",
        ],
        "commercial": [
            "best self-cleaning cat litter tray UK",
            "best cat subscription boxes UK treats and toys",
        ],
        "comparison": [
            "clumping vs non-clumping cat litter comparison UK",
            "wood vs silica vs clay cat litter comparison",
            "covered vs open cat litter tray comparison",
            "cat tree vs cat shelves comparison space saving",
        ],
        "how-to": [
            "how to train a cat to use a cat flap UK",
            "how to introduce a cat to a harness UK",
            "how to clean a cat water fountain UK guide",
            "how to trim cat claws at home safely UK",
        ],
    },
    "Cat Toys": {
        "informational": [
            "best cat toys UK 2026 updated guide",
            "cat laser toy safety UK guide and alternatives",
            "best cat puzzle feeders UK mental stimulation",
            "cat feather toys UK best wand toys guide",
            "electronic cat toys UK do they work",
            "cat kicker toys UK best for bunny kicks",
            "best toys for kittens UK safe play guide",
            "cat tunnel toys UK best options reviewed",
            "cat toy safety guide UK choking hazards",
            "best cat toys for older cats UK senior play",
            "DIY cat toys UK homemade safe ideas",
        ],
        "commercial": [
            "best cat toy subscription box UK monthly",
            "Catit Senses range UK review and guide",
        ],
        "comparison": [
            "interactive vs self-play cat toys comparison",
            "battery-powered vs manual cat toys comparison UK",
            "catnip vs silvervine vs valerian for cats comparison",
        ],
        "how-to": [
            "how to get a lazy cat to play UK tips",
            "how to rotate cat toys to maintain interest",
            "how to make safe DIY cat toys at home UK",
        ],
    },
    "Indoor Cats": {
        "informational": [
            "indoor cat enrichment guide UK keeping cats happy",
            "best indoor cat breeds UK apartment living",
            "indoor cat exercise guide UK keeping fit",
            "indoor cat safety checklist UK poisonous plants",
            "indoor cat behaviour problems UK solutions guide",
            "catio guide UK outdoor enclosure for indoor cats",
            "indoor cat diet guide UK weight management",
            "indoor vs outdoor cat pros cons UK debate",
            "how to keep indoor cats entertained UK",
            "indoor cat window perch UK best options guide",
            "indoor cat grass UK safe growing guide",
            "indoor cat litter solutions UK odour control",
        ],
        "commercial": [
            "best cat window perch UK indoor enrichment",
            "best catio kit UK outdoor cat enclosure",
        ],
        "comparison": [
            "indoor only vs outdoor access cats UK comparison",
            "cat tree vs catio for indoor cats comparison",
            "window perch vs wall shelf for indoor cats UK",
        ],
        "how-to": [
            "how to transition outdoor cat to indoor UK",
            "how to build a DIY catio UK guide",
            "how to create a cat-friendly room UK guide",
            "how to prevent indoor cat obesity UK",
        ],
    },
    "Puppy Care": {
        "informational": [
            "puppy vaccination schedule UK 2026 complete guide",
            "puppy socialisation checklist UK critical period",
            "puppy crate training guide UK night and day",
            "puppy house training guide UK toilet training",
            "puppy biting and nipping guide UK how to stop",
            "puppy sleeping guide UK first night tips",
            "puppy development stages UK week by week",
            "puppy nutrition guide UK feeding amounts by age",
            "puppy worming schedule UK treatment guide",
            "puppy recall training UK guide for beginners",
            "new puppy checklist UK everything you need",
            "puppy-safe garden guide UK toxic plants list",
        ],
        "commercial": [
            "best puppy starter kit UK essentials bundle",
            "best puppy training pads UK disposable vs washable",
        ],
        "comparison": [
            "puppy classes vs home training UK comparison",
            "puppy pad vs outdoor toilet training comparison UK",
            "dry vs wet puppy food comparison UK",
        ],
        "how-to": [
            "how to stop puppy crying at night UK",
            "how to socialise a puppy during restrictions UK",
            "how to introduce puppy to resident dog UK",
            "how to puppy-proof your garden UK guide",
        ],
    },
    "Training Supplies": {
        "informational": [
            "best dog clicker UK training guide",
            "dog treat pouch UK best options for training",
            "dog training whistle UK recall training guide",
            "best dog training books UK 2026 recommended",
            "agility training equipment UK home starter guide",
            "dog training dummy UK gundog retrieve guide",
            "best long line lead UK recall training",
            "dog training mat UK place training guide",
            "target stick dog training UK guide",
            "dog training vest UK hands-free walking gear",
        ],
        "commercial": [
            "best dog training starter kit UK everything included",
            "dog agility course kit UK garden setup",
        ],
        "comparison": [
            "clicker vs verbal marker training comparison",
            "positive reinforcement vs balanced training comparison UK",
            "online dog training vs in-person classes UK comparison",
        ],
        "how-to": [
            "how to teach a dog to walk on a loose lead UK",
            "how to train a reliable recall UK step by step",
            "how to start agility training at home UK",
            "how to use a dog training clicker UK guide",
        ],
    },
    "Pet Care": {
        "informational": [
            "pet insurance UK comparison guide 2026",
            "pet travel guide UK flying with pets",
            "pet passport UK requirements and process guide",
            "pet-friendly holidays UK accommodation guide",
            "multi-pet household guide UK cats and dogs together",
            "exotic pet care UK beginners guide",
            "pet bereavement support UK coping with loss guide",
            "pet first aid course UK where to learn",
            "seasonal pet care UK spring summer autumn winter",
            "pet adoption UK guide rescue centres process",
            "pet microchipping UK law 2026 requirements",
            "pet poison helpline UK emergency guide",
        ],
        "commercial": [
            "best pet camera UK monitor pets while away",
            "best pet GPS tracker UK comparison",
        ],
        "comparison": [
            "pet insurance vs vet payment plan UK comparison",
            "adopting vs buying a pet UK pros and cons",
            "pet sitter vs boarding kennel comparison UK",
        ],
        "how-to": [
            "how to introduce a new pet to your home UK",
            "how to pet-proof your home UK complete guide",
            "how to travel with a pet in the car UK safely",
            "how to find a good vet UK checklist",
        ],
    },
    "Uncategorized": {
        "informational": [
            "best pet gifts UK 2026 guide for pet lovers",
            "pet-friendly cleaning products UK safe guide",
            "pet odour removal guide UK home cleaning",
            "best pet vacuum cleaner UK for pet hair",
            "pet hair removal guide UK furniture and clothes",
            "pet photography tips UK getting great shots",
            "pet memorial ideas UK remembering your pet",
            "pet-friendly garden design UK plants and layout",
            "working from home with pets UK productivity tips",
            "pet-safe air fresheners UK non-toxic options",
            "best pet stain remover UK carpet and upholstery",
            "pet anxiety during fireworks UK calming guide",
        ],
        "commercial": [
            "best robot vacuum for pet hair UK",
            "best pet hair lint roller UK comparison",
        ],
        "comparison": [
            "robot vacuum vs upright for pet hair comparison UK",
            "enzymatic vs standard pet stain cleaner comparison",
            "natural vs chemical pet odour eliminator comparison",
        ],
        "how-to": [
            "how to remove pet hair from furniture UK",
            "how to reduce pet allergens in home UK",
            "how to keep house clean with pets UK guide",
            "how to calm pets during fireworks UK",
        ],
    },
}

# ---------------------------------------------------------------------------
# 3. Match existing posts to identify gaps
# ---------------------------------------------------------------------------

def normalize_for_matching(text):
    """Normalize text for fuzzy matching."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text


def is_topic_covered(intent, posts, cluster_posts):
    """Check if a search intent is already covered by existing content."""
    intent_norm = normalize_for_matching(intent)
    intent_words = set(intent_norm.split())
    # Remove common stop words for matching
    stop_words = {"uk", "2026", "best", "guide", "complete", "for", "the", "a", "an",
                  "and", "or", "vs", "how", "to", "your", "what", "which", "is", "of",
                  "in", "on", "with"}
    intent_keywords = intent_words - stop_words

    if len(intent_keywords) < 2:
        return False  # Too generic to match

    # Check against cluster posts first, then all posts
    for post in cluster_posts + posts:
        title_norm = normalize_for_matching(post["title_lower"])
        content_norm = normalize_for_matching(post["content_lower"][:2000])

        title_words = set(title_norm.split())
        content_words = set(content_norm.split())
        all_words = title_words | content_words

        # If 60%+ of intent keywords appear in title+content, consider it covered
        overlap = intent_keywords & all_words
        if len(overlap) >= max(2, len(intent_keywords) * 0.6):
            return True

    return False


def estimate_search_volume(intent):
    """Estimate search volume based on topic characteristics."""
    intent_lower = intent.lower()
    # High volume indicators
    high_indicators = ["best", "how to", "guide", "uk 2026", "schedule", "checklist"]
    medium_indicators = ["comparison", "vs", "tips", "review", "options"]

    if any(h in intent_lower for h in high_indicators):
        return "high"
    elif any(m in intent_lower for m in medium_indicators):
        return "medium"
    else:
        return "low"


def estimate_competition(intent):
    """Estimate competition based on topic."""
    intent_lower = intent.lower()
    high_comp = ["best dog food", "best cat food", "pet insurance", "dog training"]
    medium_comp = ["guide", "comparison", "how to"]
    low_comp = ["diy", "homemade", "niche", "specific breed"]

    if any(h in intent_lower for h in high_comp):
        return "high"
    elif any(m in intent_lower for m in medium_comp):
        return "medium"
    else:
        return "low"


def calculate_authority_fit(cluster, intent, cluster_dom_scores):
    """Calculate how well this topic fits PetHub's existing authority."""
    base_score = 70  # PetHub already has good pet authority
    dom_score = cluster_dom_scores.get(cluster, 85)

    # Higher dominance = better authority fit
    if dom_score >= 90:
        base_score += 20
    elif dom_score >= 85:
        base_score += 15
    else:
        base_score += 10

    # Topic relevance boosters
    intent_lower = intent.lower()
    if "uk" in intent_lower:
        base_score += 5  # UK focus matches PetHub
    if any(w in intent_lower for w in ["puppy", "kitten", "dog", "cat", "pet"]):
        base_score += 5

    return min(100, base_score)


def calculate_cluster_contribution(cluster, cluster_dom_scores, post_count):
    """Calculate how much this new post would strengthen a weak cluster."""
    dom_score = cluster_dom_scores.get(cluster, 85)
    gap = max(0, 90 - dom_score)

    # Higher gap and lower post count = higher contribution
    base = 50
    if gap > 3:
        base += 30
    elif gap > 1:
        base += 20
    elif gap > 0:
        base += 10

    if post_count < 5:
        base += 15
    elif post_count < 10:
        base += 10

    return min(100, base)


def calculate_ai_answer_potential(intent):
    """Calculate likelihood that AI systems would cite this content."""
    intent_lower = intent.lower()
    high_ai = ["guide", "explained", "complete", "what is", "how to", "step by step",
               "schedule", "checklist", "symptoms", "signs"]
    medium_ai = ["best", "comparison", "vs", "tips", "review"]

    score = 60
    if any(h in intent_lower for h in high_ai):
        score += 30
    if any(m in intent_lower for m in medium_ai):
        score += 15
    if "uk" in intent_lower:
        score += 5

    return min(100, score)


def intent_type_from_key(key):
    """Map intent category key to display label."""
    mapping = {
        "informational": "informational",
        "commercial": "commercial",
        "comparison": "comparison",
        "how-to": "how-to",
    }
    return mapping.get(key, "informational")


def recommended_format(intent_type, intent):
    """Recommend content format based on intent type."""
    intent_lower = intent.lower()
    if "comparison" in intent_lower or "vs" in intent_lower:
        return "comparison"
    elif "how to" in intent_lower:
        return "guide"
    elif "faq" in intent_lower or "questions" in intent_lower:
        return "faq"
    elif "checklist" in intent_lower or "list" in intent_lower:
        return "guide"
    elif "glossary" in intent_lower or "explained" in intent_lower:
        return "glossary"
    elif intent_type == "commercial":
        return "comparison"
    else:
        return "guide"


# ---------------------------------------------------------------------------
# 4. Main execution
# ---------------------------------------------------------------------------

print("=" * 60)
print("SEARCH OPPORTUNITY ENGINE - Phase 11")
print("=" * 60)

# Load cluster dominance scores
roadmaps = load_csv("Cluster_Dominance_Roadmaps.csv")
cluster_dom_scores = {}
for r in roadmaps:
    c = r["cluster"].strip()
    if c:
        cluster_dom_scores[c] = float(r["dominance_score"])

# Load cluster post counts from citations
citations = load_csv("Citation_Dominance_Report.csv")
cluster_post_counts = {}
for row in citations:
    c = row["cluster"].strip()
    cluster_post_counts[c] = cluster_post_counts.get(c, 0) + 1

# Fetch WordPress posts
print("\n--- Fetching published posts from WordPress ---")
wp_posts = fetch_all_posts()
print(f"Total posts fetched: {len(wp_posts)}")

# Extract post info for matching
post_info = extract_post_info(wp_posts)

# Organize posts by rough cluster matching
cluster_posts_map = {c: [] for c in CLUSTER_INTENTS.keys()}
for p in post_info:
    title_lower = p["title_lower"]
    # Simple cluster assignment by title keywords
    if "dog food" in title_lower or "puppy food" in title_lower or "feeding" in title_lower:
        cluster_posts_map["Dog Food"].append(p)
    elif "dog bed" in title_lower or "puppy bed" in title_lower:
        cluster_posts_map["Dog Beds"].append(p)
    elif "harness" in title_lower or "collar" in title_lower:
        cluster_posts_map["Dog Harnesses"].append(p)
    elif "dog toy" in title_lower or "chew" in title_lower or "puzzle" in title_lower:
        cluster_posts_map["Dog Toys"].append(p)
    elif "cat toy" in title_lower or "catnip" in title_lower:
        cluster_posts_map["Cat Toys"].append(p)
    elif "cat" in title_lower and ("supply" in title_lower or "brush" in title_lower or
          "bed" in title_lower or "litter" in title_lower or "carrier" in title_lower):
        cluster_posts_map["Cat Supplies"].append(p)
    elif "indoor cat" in title_lower:
        cluster_posts_map["Indoor Cats"].append(p)
    elif "puppy" in title_lower:
        cluster_posts_map["Puppy Care"].append(p)
    elif "training" in title_lower or "lead" in title_lower:
        cluster_posts_map["Training Supplies"].append(p)
    elif "dog health" in title_lower or "flea" in title_lower or "worm" in title_lower or "vet" in title_lower:
        cluster_posts_map["Dog Health"].append(p)
    elif "groom" in title_lower or "shampoo" in title_lower or "brush" in title_lower or "nail" in title_lower:
        cluster_posts_map["Dog Care"].append(p)
    elif "dog supply" in title_lower or "dog bowl" in title_lower or "crate" in title_lower:
        cluster_posts_map["Dog Supplies"].append(p)
    elif "pet care" in title_lower or "pet insurance" in title_lower:
        cluster_posts_map["Pet Care"].append(p)

# ---------------------------------------------------------------------------
# 5. Identify gaps and score opportunities
# ---------------------------------------------------------------------------

print("\n--- Analyzing content gaps per cluster ---")

all_opportunities = []
gap_by_cluster = []

for cluster, intent_categories in CLUSTER_INTENTS.items():
    cluster_posts = cluster_posts_map.get(cluster, [])
    total_intents = 0
    gap_count = 0
    gap_titles = []

    for intent_type_key, intents in intent_categories.items():
        for intent in intents:
            total_intents += 1

            covered = is_topic_covered(intent, post_info, cluster_posts)
            if not covered:
                gap_count += 1
                gap_titles.append(intent)

                # Score the opportunity
                sv = estimate_search_volume(intent)
                comp = estimate_competition(intent)
                auth_fit = calculate_authority_fit(cluster, intent, cluster_dom_scores)
                clust_contrib = calculate_cluster_contribution(
                    cluster, cluster_dom_scores,
                    cluster_post_counts.get(cluster, 0)
                )
                ai_pot = calculate_ai_answer_potential(intent)

                # Priority score: weighted combination
                sv_num = {"high": 90, "medium": 60, "low": 30}[sv]
                comp_num = {"high": 30, "medium": 60, "low": 90}[comp]  # Lower competition = better

                priority_score = round(
                    sv_num * 0.20 +
                    comp_num * 0.10 +
                    auth_fit * 0.25 +
                    clust_contrib * 0.25 +
                    ai_pot * 0.20,
                    1
                )

                rec_format = recommended_format(intent_type_key, intent)

                all_opportunities.append({
                    "opportunity_title": intent,
                    "cluster": cluster,
                    "intent_type": intent_type_from_key(intent_type_key),
                    "search_volume_est": sv,
                    "competition_est": comp,
                    "authority_fit": auth_fit,
                    "cluster_contribution": clust_contrib,
                    "ai_answer_potential": ai_pot,
                    "priority_score": priority_score,
                    "recommended_format": rec_format,
                })

    # Calculate coverage
    coverage_pct = round(((total_intents - gap_count) / total_intents * 100) if total_intents > 0 else 0, 1)
    top_3_gaps = " | ".join(gap_titles[:3]) if gap_titles else "None"

    # Expansion priority
    dom_score = cluster_dom_scores.get(cluster, 85)
    if dom_score < 90 and gap_count >= 5:
        exp_priority = "HIGH"
    elif dom_score < 90 or gap_count >= 3:
        exp_priority = "MEDIUM"
    else:
        exp_priority = "LOW"

    gap_by_cluster.append({
        "cluster": cluster,
        "total_posts": cluster_post_counts.get(cluster, 0),
        "gap_count": gap_count,
        "top_3_gaps": top_3_gaps,
        "coverage_pct": coverage_pct,
        "expansion_priority": exp_priority,
    })

    print(f"  {cluster}: {gap_count} gaps found out of {total_intents} intents ({coverage_pct}% coverage)")

# Sort opportunities by priority score descending
all_opportunities.sort(key=lambda r: -r["priority_score"])

# ---------------------------------------------------------------------------
# 6. Generate quick wins
# ---------------------------------------------------------------------------

quick_wins = []
for opp in all_opportunities:
    is_quick = False
    why = []

    # Quick win if: high authority fit + low competition + high AI potential
    if opp["competition_est"] == "low" and opp["authority_fit"] >= 85:
        is_quick = True
        why.append("low competition + strong authority fit")
    elif opp["ai_answer_potential"] >= 85 and opp["competition_est"] != "high":
        is_quick = True
        why.append("high AI citation potential")
    elif opp["cluster_contribution"] >= 80:
        is_quick = True
        why.append("significantly strengthens weak cluster")
    elif opp["search_volume_est"] == "high" and opp["competition_est"] == "low":
        is_quick = True
        why.append("high demand + low competition")

    if is_quick:
        # Estimate effort
        if opp["intent_type"] == "how-to":
            effort = "medium"
        elif opp["intent_type"] == "comparison":
            effort = "medium"
        elif opp["intent_type"] == "commercial":
            effort = "low"
        else:
            effort = "medium"

        if opp["search_volume_est"] == "low":
            effort = "low"

        quick_wins.append({
            "opportunity_title": opp["opportunity_title"],
            "cluster": opp["cluster"],
            "why_quick_win": "; ".join(why),
            "estimated_effort": effort,
            "priority_score": opp["priority_score"],
        })

# Sort quick wins by priority score descending
quick_wins.sort(key=lambda r: -r["priority_score"])

# ---------------------------------------------------------------------------
# 7. Write output CSVs
# ---------------------------------------------------------------------------

print("\n--- Writing output CSVs ---")

write_csv("search_opportunities.csv", all_opportunities, [
    "opportunity_title", "cluster", "intent_type", "search_volume_est",
    "competition_est", "authority_fit", "cluster_contribution",
    "ai_answer_potential", "priority_score", "recommended_format",
])

# Sort gap_by_cluster by expansion priority
priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
gap_by_cluster.sort(key=lambda r: priority_order.get(r["expansion_priority"], 99))

write_csv("content_gap_by_cluster.csv", gap_by_cluster, [
    "cluster", "total_posts", "gap_count", "top_3_gaps",
    "coverage_pct", "expansion_priority",
])

write_csv("quick_wins.csv", quick_wins, [
    "opportunity_title", "cluster", "why_quick_win",
    "estimated_effort", "priority_score",
])

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("\n=== SEARCH OPPORTUNITY ENGINE COMPLETE ===")
print(f"Total opportunities identified: {len(all_opportunities)}")
print(f"Quick wins identified: {len(quick_wins)}")
print(f"Clusters analyzed: {len(gap_by_cluster)}")

high_priority = [g for g in gap_by_cluster if g["expansion_priority"] == "HIGH"]
print(f"\nHigh priority expansion clusters: {len(high_priority)}")
for g in high_priority:
    print(f"  {g['cluster']}: {g['gap_count']} gaps, {g['coverage_pct']}% coverage")

print(f"\nTop 10 opportunities by priority score:")
for opp in all_opportunities[:10]:
    print(f"  [{opp['priority_score']}] {opp['cluster']}: {opp['opportunity_title']}")
