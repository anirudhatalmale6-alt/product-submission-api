#!/usr/bin/env python3
"""
10AD-B: Terminology Intelligence Engine for pethubonline.com
Detects missing terminology, weak definitions, missing beginner explanations,
and recommends terminology expansions across all published posts.
"""

import subprocess
import json
import csv
import re
import os
import sys
from collections import defaultdict
from html import unescape

# ─── Configuration ───────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ad_data"

# ─── Terminology Knowledge Base ──────────────────────────────────────────────
CLUSTER_TERMS = {
    "dog_toys": {
        "keywords": ["toy", "toys", "chew", "play", "fetch", "tug", "puzzle", "kong", "nylabone"],
        "terms": {
            "enrichment": "Activities and objects that stimulate a dog's mind and body, preventing boredom and destructive behaviour.",
            "desensitisation": "Gradually exposing a dog to a feared stimulus at low intensity to reduce reactivity over time.",
            "resource guarding": "A behaviour where a dog protects food, toys, or other valued items from people or other animals.",
            "puzzle feeder": "A toy or device that requires a dog to solve a problem to access food or treats inside.",
            "interactive toy": "A toy designed for engagement between a dog and its owner, or that responds to the dog's actions.",
            "tug toy": "A rope or fabric toy designed for tug-of-war games that build impulse control and strengthen the bond.",
            "flirt pole": "A long pole with a lure attached by a rope, used for chase and impulse-control training exercises.",
            "snuffle mat": "A fabric mat with hiding spots that encourages dogs to use their nose to find hidden treats.",
            "dental chew": "A chew product designed to help clean teeth and reduce plaque and tartar build-up as a dog chews.",
            "lick mat": "A textured mat spread with soft food that encourages slow licking, reducing anxiety and promoting calm.",
            "denier": "A unit measuring the thickness and durability of fabric fibres used in dog beds and toys.",
            "stuffable toy": "A hollow toy (like a Kong) that can be filled with food or treats to keep dogs occupied.",
            "nylon chew": "A durable synthetic chew (like a Nylabone) designed for aggressive chewers as a safe alternative to bones.",
        }
    },
    "dog_food": {
        "keywords": ["food", "feed", "diet", "nutrition", "kibble", "raw", "wet food", "dry food", "treat", "treats", "eating"],
        "terms": {
            "kibble": "Dry, pellet-shaped dog food that is cooked at high temperatures and formed into uniform pieces.",
            "complete food": "A pet food that contains all required nutrients in correct proportions — no supplementation needed.",
            "complementary food": "A pet food that does not meet all nutritional needs alone and must be combined with other food.",
            "grain-free": "Food formulated without grains like wheat, corn, or rice, often using potato or legume alternatives.",
            "freeze-dried": "Food preserved by removing moisture through sublimation, retaining nutrients and flavour without refrigeration.",
            "slow feeder": "A bowl or device with obstacles that forces dogs to eat more slowly, reducing bloat and improving digestion.",
            "body condition score": "A 1-9 scale used by vets to assess whether a pet is underweight, ideal, or overweight by visual and physical checks.",
            "FEDIAF": "The European Pet Food Industry Federation that sets nutritional guidelines for complete and complementary pet foods.",
            "palatability": "How appealing and tasty a food is to a pet, influenced by aroma, texture, and ingredient quality.",
            "digestibility": "The proportion of food that is broken down and absorbed by the body rather than excreted as waste.",
            "guaranteed analysis": "The label section showing minimum/maximum percentages of protein, fat, fibre, and moisture in pet food.",
            "crude protein": "The total protein content in pet food measured by nitrogen analysis, shown on the guaranteed analysis label.",
            "moisture content": "The percentage of water in pet food — typically 10% in dry kibble and 75-80% in wet food.",
        }
    },
    "dog_beds": {
        "keywords": ["bed", "beds", "sleep", "sleeping", "crate", "den", "nest", "mat"],
        "terms": {
            "orthopaedic": "A bed with supportive foam designed to relieve pressure on joints, ideal for senior or arthritic dogs.",
            "memory foam": "Viscoelastic foam that moulds to a dog's body shape, distributing weight evenly to reduce joint stress.",
            "bolster bed": "A bed with raised edges that provide a sense of security and a place to rest the head.",
            "nest bed": "A round, deep-sided bed that allows dogs to curl up in a cosy, enclosed sleeping position.",
            "elevated bed": "A raised cot-style bed that keeps dogs off cold or hot floors and improves airflow underneath.",
            "denier": "A unit measuring the thickness and durability of fabric fibres used in dog beds and toys.",
            "waterproof liner": "A moisture-barrier layer inside a bed cover that protects the foam from accidents and spills.",
            "anti-microbial": "A fabric treatment that inhibits the growth of bacteria, mould, and odour-causing organisms in bedding.",
        }
    },
    "dog_health": {
        "keywords": ["health", "vet", "medical", "illness", "disease", "parasite", "flea", "tick", "worm",
                      "supplement", "joint", "dental", "teeth", "skin", "allergy", "vaccination", "neutering"],
        "terms": {
            "microchip": "A tiny RFID implant placed under the skin that stores a unique ID, legally required in the UK since 2016.",
            "body condition score": "A 1-9 scale used by vets to assess whether a pet is underweight, ideal, or overweight by visual and physical checks.",
            "dental scaling": "A veterinary procedure that removes hardened tartar from teeth using ultrasonic or hand instruments under anaesthesia.",
            "joint supplement": "A dietary supplement containing ingredients like glucosamine or chondroitin to support joint cartilage and mobility.",
            "glucosamine": "A natural compound that helps maintain cartilage health and is commonly used to manage arthritis in dogs.",
            "omega fatty acids": "Essential fats (omega-3 and omega-6) that support skin health, coat condition, and reduce inflammation.",
            "parasite lifecycle": "The stages a parasite goes through (egg, larva, adult) — understanding this helps time treatments effectively.",
            "spot-on treatment": "A topical liquid applied between the shoulder blades that protects against fleas, ticks, or worms for weeks.",
        }
    },
    "puppy_care": {
        "keywords": ["puppy", "puppies", "pup", "new dog", "first dog", "getting a dog", "bringing home"],
        "terms": {
            "socialisation": "The critical period (3-14 weeks) where puppies learn to accept new people, animals, and environments confidently.",
            "counter-conditioning": "Changing a dog's emotional response to a stimulus by pairing it with something positive like treats.",
            "positive reinforcement": "Rewarding desired behaviour with treats, praise, or play to increase the likelihood it is repeated.",
            "recall": "Training a dog to come back reliably when called — one of the most important safety commands.",
            "mouthing": "A natural puppy behaviour of gently biting during play, which must be redirected to appropriate chew items.",
            "crate training": "Teaching a dog to see a crate as a safe, comfortable den — useful for house training and travel.",
            "high-value treat": "An especially tasty reward (like chicken or cheese) used for difficult training tasks or high-distraction environments.",
            "clicker training": "A training method using a clicking sound to precisely mark desired behaviour before delivering a reward.",
            "separation anxiety": "A distress condition where dogs become anxious and destructive when left alone, requiring gradual desensitisation.",
            "bite inhibition": "A learned ability to control the force of mouthing, taught during puppyhood through play and social feedback.",
        }
    },
    "cat": {
        "keywords": ["cat", "cats", "kitten", "feline", "kitty"],
        "terms": {
            "catnip": "A herb (Nepeta cataria) that triggers a temporary euphoric response in about 50-70% of cats.",
            "pheromone diffuser": "A plug-in device that releases synthetic calming pheromones (like Feliway) to reduce feline stress and anxiety.",
            "scratching post": "A vertical surface (sisal, cardboard, or wood) that allows cats to scratch naturally, protecting furniture.",
            "interactive toy": "A toy designed for engagement between a cat and its owner, like feather wands or laser pointers.",
            "indoor enrichment": "Activities, toys, and environmental modifications that keep indoor cats mentally stimulated and physically active.",
            "vertical space": "Shelves, cat trees, and high perches that satisfy a cat's natural instinct to climb and survey from above.",
            "litter substrate": "The material inside a litter tray (clay, silica, wood, paper) that absorbs moisture and controls odour.",
        }
    },
    "general": {
        "keywords": [],
        "terms": {
            "RSPCA": "The Royal Society for the Prevention of Cruelty to Animals — the UK's leading animal welfare charity.",
            "BVA": "The British Veterinary Association — the national representative body for the veterinary profession in the UK.",
            "positive reinforcement": "Rewarding desired behaviour with treats, praise, or play to increase the likelihood it is repeated.",
            "enrichment": "Activities and objects that stimulate a pet's mind and body, preventing boredom and destructive behaviour.",
            "body condition score": "A 1-9 scale used by vets to assess whether a pet is underweight, ideal, or overweight by visual and physical checks.",
            "microchip": "A tiny RFID implant placed under the skin that stores a unique ID, legally required in the UK since 2016.",
        }
    },
}

# ─── Definition patterns ─────────────────────────────────────────────────────
DEFINITION_PATTERNS = [
    r'meaning\s+[\"“]',
    r'refers\s+to\s+',
    r'defined\s+as\s+',
    r'—\s+a[n]?\s+',
    r'–\s+a[n]?\s+',
    r'—\s+a[n]?\s+',
    r'–\s+a[n]?\s+',
    r'which\s+is\s+a\s+',
    r'which\s+means\s+',
    r'also\s+known\s+as\s+',
    r'is\s+a\s+type\s+of\s+',
    r'is\s+a\s+form\s+of\s+',
    r'in\s+other\s+words\s*,',
    r'put\s+simply\s*,',
    r'essentially\s*,',
    r'basically\s*,\s+this',
]


def strip_html(html_text):
    """Remove HTML tags and decode entities."""
    if not html_text:
        return ""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def wp_api_call(endpoint):
    """Call WP REST API via curl with basic auth."""
    url = f"{WP_API}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  [WARN] curl error for {endpoint}: {result.stderr[:200]}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [WARN] JSON decode error for {endpoint}: {result.stdout[:200]}")
        return None


def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    while True:
        print(f"  Fetching posts page {page}...")
        data = wp_api_call(f"posts?status=publish&per_page=100&page={page}&context=edit")
        if not data or not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        print(f"    Got {len(data)} posts (total: {len(all_posts)})")
        if len(data) < 100:
            break
        page += 1
    return all_posts


def classify_cluster(title, content_text):
    """Determine which cluster a post belongs to based on title and content keywords."""
    title_lower = title.lower()
    content_lower = content_text.lower()[:2000]  # Check first 2000 chars
    combined = title_lower + " " + content_lower

    scores = {}
    for cluster_name, cluster_data in CLUSTER_TERMS.items():
        if cluster_name == "general":
            continue
        score = 0
        for kw in cluster_data["keywords"]:
            kw_lower = kw.lower()
            # Title matches are worth more
            if kw_lower in title_lower:
                score += 5
            if kw_lower in content_lower:
                score += 1
        scores[cluster_name] = score

    if not scores or max(scores.values()) == 0:
        return "general"

    best = max(scores, key=scores.get)
    return best


def find_glossary_block_terms(html_content):
    """Find terms defined in Key Terms / glossary blocks."""
    glossary_terms = []
    # Look for common glossary/key terms patterns in HTML
    # Pattern 1: <strong>Term</strong> or <b>Term</b> followed by definition
    # Pattern 2: Key Terms / Glossary section headings
    # Pattern 3: <dt>Term</dt><dd>Definition</dd>

    # Find glossary sections
    glossary_section = re.findall(
        r'(?:key\s+terms|glossary|terminology|definitions?)\s*(?:</[^>]+>)?\s*(.*?)(?:<h[23]|$)',
        html_content, re.IGNORECASE | re.DOTALL
    )

    for section in glossary_section:
        # Extract bold terms within the section
        bold_terms = re.findall(r'<(?:strong|b)>([^<]+)</(?:strong|b)>', section, re.IGNORECASE)
        glossary_terms.extend([t.strip().lower() for t in bold_terms if len(t.strip()) > 2])

    # Also find dt/dd patterns
    dt_terms = re.findall(r'<dt[^>]*>([^<]+)</dt>', html_content, re.IGNORECASE)
    glossary_terms.extend([t.strip().lower() for t in dt_terms if len(t.strip()) > 2])

    return list(set(glossary_terms))


def count_inline_definitions(text):
    """Count inline definitions in the text."""
    count = 0
    for pattern in DEFINITION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        count += len(matches)
    return count


def find_terms_in_text(text, terms_dict):
    """Find which terms from a dict appear in the text."""
    text_lower = text.lower()
    present = []
    missing = []
    for term in terms_dict:
        term_lower = term.lower()
        # Use word boundary matching for short terms
        if len(term_lower) <= 4:
            pattern = r'\b' + re.escape(term_lower) + r'\b'
            if re.search(pattern, text_lower):
                present.append(term)
            else:
                missing.append(term)
        else:
            if term_lower in text_lower:
                present.append(term)
            else:
                missing.append(term)
    return present, missing


def check_term_has_definition(text, term):
    """Check if a term has a definition nearby (within ~200 chars)."""
    text_lower = text.lower()
    term_lower = term.lower()
    positions = [m.start() for m in re.finditer(re.escape(term_lower), text_lower)]

    for pos in positions:
        # Check 200 chars around the term for definition patterns
        start = max(0, pos - 50)
        end = min(len(text_lower), pos + len(term_lower) + 200)
        context = text_lower[start:end]

        for pattern in DEFINITION_PATTERNS:
            if re.search(pattern, context, re.IGNORECASE):
                return True

        # Also check for colon pattern: "Term: definition"
        colon_pattern = re.escape(term_lower) + r'\s*[:–—―]\s*\w'
        if re.search(colon_pattern, context):
            return True

    return False


def calculate_completeness_score(terms_present, terms_missing, glossary_count, inline_defs):
    """Calculate a 0-100 terminology completeness score."""
    total_terms = len(terms_present) + len(terms_missing)
    if total_terms == 0:
        return 50  # Neutral if no applicable terms

    # Term coverage: 60% weight
    term_coverage = (len(terms_present) / total_terms) * 100 if total_terms > 0 else 0

    # Glossary presence: 20% weight
    glossary_score = min(glossary_count * 15, 100)  # 7+ glossary terms = 100

    # Inline definitions: 20% weight
    inline_score = min(inline_defs * 10, 100)  # 10+ inline defs = 100

    score = (term_coverage * 0.60) + (glossary_score * 0.20) + (inline_score * 0.20)
    return round(min(100, max(0, score)))


def determine_priority(term, cluster, terms_present_count, total_terms):
    """Determine priority for adding a missing term."""
    # High priority: fundamental terms that most posts in the cluster should have
    high_priority_terms = {
        "enrichment", "positive reinforcement", "body condition score",
        "socialisation", "microchip", "kibble", "complete food",
        "orthopaedic", "memory foam", "catnip", "scratching post"
    }

    if term.lower() in high_priority_terms:
        return "HIGH"

    # Medium if less than half the relevant terms are present
    if terms_present_count < total_terms * 0.5:
        return "MEDIUM"

    return "LOW"


def generate_reason(term, cluster):
    """Generate a human-readable reason for adding a term."""
    reasons = {
        "HIGH": f"Core {cluster.replace('_', ' ')} concept missing — essential for beginner readers",
        "MEDIUM": f"Important {cluster.replace('_', ' ')} term that adds depth and SEO value",
        "LOW": f"Supplementary term that enhances thoroughness of {cluster.replace('_', ' ')} coverage",
    }
    priority = determine_priority(term, cluster, 0, 1)
    return reasons.get(priority, f"Relevant {cluster.replace('_', ' ')} term not found in post")


def main():
    print("=" * 70)
    print("10AD-B: TERMINOLOGY INTELLIGENCE ENGINE")
    print("pethubonline.com — Full Site Analysis")
    print("=" * 70)

    # ── Step 1: Fetch all posts ──────────────────────────────────────────
    print("\n[1/5] Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}")

    if not posts:
        print("ERROR: No posts fetched. Check API credentials and URL.")
        sys.exit(1)

    # ── Step 2: Analyse each post ────────────────────────────────────────
    print(f"\n[2/5] Analysing terminology across {len(posts)} posts...")

    completeness_rows = []
    expansion_rows = []
    cluster_term_data = defaultdict(lambda: {"present": set(), "missing": set(), "posts": 0})

    for i, post in enumerate(posts):
        post_id = post.get("id", 0)
        title_raw = post.get("title", {})
        if isinstance(title_raw, dict):
            title = strip_html(title_raw.get("rendered", title_raw.get("raw", "")))
        else:
            title = strip_html(str(title_raw))

        content_raw = post.get("content", {})
        if isinstance(content_raw, dict):
            html_content = content_raw.get("rendered", content_raw.get("raw", ""))
        else:
            html_content = str(content_raw)

        content_text = strip_html(html_content)

        if (i + 1) % 20 == 0 or i == 0:
            print(f"  Processing post {i+1}/{len(posts)}: {title[:60]}...")

        # Classify cluster
        cluster = classify_cluster(title, content_text)

        # Get relevant terms (cluster + general)
        relevant_terms = dict(CLUSTER_TERMS[cluster]["terms"])
        if cluster != "general":
            relevant_terms.update(CLUSTER_TERMS["general"]["terms"])

        # Find present/missing terms
        terms_present, terms_missing = find_terms_in_text(content_text, relevant_terms)

        # Glossary analysis
        glossary_terms = find_glossary_block_terms(html_content)
        glossary_count = len(glossary_terms)

        # Inline definitions
        inline_defs = count_inline_definitions(content_text)

        # Completeness score
        score = calculate_completeness_score(terms_present, terms_missing, glossary_count, inline_defs)

        # Find weak definitions (term present but not defined)
        weak_defs = []
        for term in terms_present:
            if not check_term_has_definition(content_text, term):
                weak_defs.append(term)

        # Record completeness
        completeness_rows.append({
            "post_id": post_id,
            "title": title,
            "cluster": cluster,
            "terms_present": len(terms_present),
            "terms_missing": len(terms_missing),
            "glossary_terms": glossary_count,
            "inline_defs": inline_defs,
            "completeness_score": score,
            "missing_terms_list": "; ".join(terms_missing) if terms_missing else "(none)",
            "weak_definitions": "; ".join(weak_defs) if weak_defs else "(none)",
        })

        # Record expansion recommendations
        total_terms = len(terms_present) + len(terms_missing)
        for term in terms_missing:
            priority = determine_priority(term, cluster, len(terms_present), total_terms)
            expansion_rows.append({
                "post_id": post_id,
                "title": title,
                "cluster": cluster,
                "term_to_add": term,
                "term_definition": relevant_terms.get(term, ""),
                "priority": priority,
                "reason": generate_reason(term, cluster),
            })

        # Also add weak definitions as LOW priority expansions (need inline def added)
        for term in weak_defs:
            expansion_rows.append({
                "post_id": post_id,
                "title": title,
                "cluster": cluster,
                "term_to_add": f"{term} (add definition)",
                "term_definition": relevant_terms.get(term, ""),
                "priority": "MEDIUM",
                "reason": f"Term '{term}' appears but lacks a nearby definition for beginners",
            })

        # Track cluster-level data
        cluster_term_data[cluster]["present"].update(terms_present)
        cluster_term_data[cluster]["missing"].update(terms_missing)
        cluster_term_data[cluster]["posts"] += 1

    # ── Step 3: Build Semantic Overlap Matrix ────────────────────────────
    print("\n[3/5] Building semantic overlap matrix...")

    # Compute actual terms used per cluster across all posts
    cluster_all_terms = {}
    for cluster_name in CLUSTER_TERMS:
        if cluster_name == "general":
            continue
        all_terms_in_cluster = cluster_term_data[cluster_name]["present"] | cluster_term_data[cluster_name]["missing"]
        cluster_all_terms[cluster_name] = cluster_term_data[cluster_name]["present"]

    overlap_rows = []
    cluster_names = [c for c in CLUSTER_TERMS if c != "general"]

    for cluster_name in cluster_names:
        my_terms = cluster_all_terms.get(cluster_name, set())
        shared_count = 0
        unique_terms = set(my_terms)

        overlaps = {}
        for other_cluster in cluster_names:
            if other_cluster == cluster_name:
                continue
            other_terms = cluster_all_terms.get(other_cluster, set())
            overlap = my_terms & other_terms
            shared_count += len(overlap)
            unique_terms -= overlap
            overlaps[other_cluster] = len(overlap)

        # Calculate overlap with dog_toys specifically
        dog_toys_terms = cluster_all_terms.get("dog_toys", set())
        dog_toys_overlap = len(my_terms & dog_toys_terms) if cluster_name != "dog_toys" else len(my_terms)

        total_terms = len(my_terms)
        overlap_score = round((shared_count / max(total_terms * len(cluster_names), 1)) * 100, 1)

        overlap_rows.append({
            "cluster": cluster_name,
            "posts_in_cluster": cluster_term_data[cluster_name]["posts"],
            "terms_found": len(my_terms),
            "shared_terms_count": shared_count,
            "unique_terms_count": len(unique_terms),
            "overlap_with_dog_toys": dog_toys_overlap,
            "overlap_score": overlap_score,
        })

    # ── Step 4: Write CSVs ───────────────────────────────────────────────
    print("\n[4/5] Writing output CSVs...")

    # Terminology Completeness CSV
    completeness_path = os.path.join(OUTPUT_DIR, "Terminology_Completeness.csv")
    with open(completeness_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "terms_present", "terms_missing",
            "glossary_terms", "inline_defs", "completeness_score",
            "missing_terms_list", "weak_definitions"
        ])
        writer.writeheader()
        writer.writerows(completeness_rows)
    print(f"  Written: {completeness_path} ({len(completeness_rows)} rows)")

    # Terminology Expansion Plan CSV
    expansion_path = os.path.join(OUTPUT_DIR, "Terminology_Expansion_Plan.csv")
    # Sort by priority (HIGH first, then MEDIUM, then LOW)
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    expansion_rows.sort(key=lambda r: (priority_order.get(r["priority"], 3), r["cluster"], r["term_to_add"]))

    with open(expansion_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "term_to_add",
            "term_definition", "priority", "reason"
        ])
        writer.writeheader()
        writer.writerows(expansion_rows)
    print(f"  Written: {expansion_path} ({len(expansion_rows)} rows)")

    # Semantic Overlap Matrix CSV
    overlap_path = os.path.join(OUTPUT_DIR, "Semantic_Overlap_Matrix.csv")
    with open(overlap_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cluster", "posts_in_cluster", "terms_found",
            "shared_terms_count", "unique_terms_count",
            "overlap_with_dog_toys", "overlap_score"
        ])
        writer.writeheader()
        writer.writerows(overlap_rows)
    print(f"  Written: {overlap_path} ({len(overlap_rows)} rows)")

    # ── Step 5: Print Summary Report ─────────────────────────────────────
    print("\n" + "=" * 70)
    print("TERMINOLOGY INTELLIGENCE REPORT")
    print("=" * 70)

    print(f"\nPosts analysed: {len(posts)}")
    print(f"Expansion recommendations: {len(expansion_rows)}")

    # Cluster distribution
    print("\n--- Cluster Distribution ---")
    cluster_counts = defaultdict(int)
    for row in completeness_rows:
        cluster_counts[row["cluster"]] += 1
    for cluster, count in sorted(cluster_counts.items(), key=lambda x: -x[1]):
        print(f"  {cluster:20s}  {count:3d} posts")

    # Average completeness by cluster
    print("\n--- Average Completeness Score by Cluster ---")
    cluster_scores = defaultdict(list)
    for row in completeness_rows:
        cluster_scores[row["cluster"]].append(row["completeness_score"])
    for cluster, scores in sorted(cluster_scores.items(), key=lambda x: sum(x[1])/len(x[1])):
        avg = sum(scores) / len(scores)
        print(f"  {cluster:20s}  avg={avg:5.1f}  min={min(scores):3d}  max={max(scores):3d}")

    # Overall stats
    all_scores = [r["completeness_score"] for r in completeness_rows]
    if all_scores:
        print(f"\n--- Overall Scores ---")
        print(f"  Average completeness: {sum(all_scores)/len(all_scores):.1f}")
        print(f"  Median completeness:  {sorted(all_scores)[len(all_scores)//2]}")
        print(f"  Posts scoring < 30:   {sum(1 for s in all_scores if s < 30)}")
        print(f"  Posts scoring 30-60:  {sum(1 for s in all_scores if 30 <= s < 60)}")
        print(f"  Posts scoring 60-80:  {sum(1 for s in all_scores if 60 <= s < 80)}")
        print(f"  Posts scoring 80+:    {sum(1 for s in all_scores if s >= 80)}")

    # Top missing terms across all posts
    print("\n--- Top 15 Most Commonly Missing Terms ---")
    term_miss_count = defaultdict(int)
    for row in completeness_rows:
        if row["missing_terms_list"] != "(none)":
            for term in row["missing_terms_list"].split("; "):
                term_miss_count[term.strip()] += 1
    for term, count in sorted(term_miss_count.items(), key=lambda x: -x[1])[:15]:
        print(f"  {term:30s}  missing in {count:3d} posts")

    # Expansion priority breakdown
    print("\n--- Expansion Priority Breakdown ---")
    priority_counts = defaultdict(int)
    for row in expansion_rows:
        priority_counts[row["priority"]] += 1
    for p in ["HIGH", "MEDIUM", "LOW"]:
        print(f"  {p:8s}  {priority_counts.get(p, 0):5d} recommendations")

    # Top posts needing attention
    print("\n--- Top 10 Posts Needing Terminology Work ---")
    worst = sorted(completeness_rows, key=lambda r: r["completeness_score"])[:10]
    for row in worst:
        print(f"  [{row['completeness_score']:3d}] (ID {row['post_id']}) {row['title'][:55]}")

    # Glossary coverage
    total_glossary = sum(r["glossary_terms"] for r in completeness_rows)
    posts_with_glossary = sum(1 for r in completeness_rows if r["glossary_terms"] > 0)
    print(f"\n--- Glossary Coverage ---")
    print(f"  Posts with glossary blocks: {posts_with_glossary}/{len(posts)}")
    print(f"  Total glossary terms found: {total_glossary}")

    # Inline definitions
    total_inline = sum(r["inline_defs"] for r in completeness_rows)
    posts_with_inline = sum(1 for r in completeness_rows if r["inline_defs"] > 0)
    print(f"\n--- Inline Definition Coverage ---")
    print(f"  Posts with inline defs:     {posts_with_inline}/{len(posts)}")
    print(f"  Total inline defs found:    {total_inline}")

    # Semantic overlap summary
    print("\n--- Semantic Overlap Matrix Summary ---")
    for row in overlap_rows:
        print(f"  {row['cluster']:20s}  {row['terms_found']:2d} terms found | "
              f"{row['shared_terms_count']:2d} shared | {row['unique_terms_count']:2d} unique | "
              f"overlap score: {row['overlap_score']:.1f}%")

    print("\n" + "=" * 70)
    print("Analysis complete. CSVs written to:")
    print(f"  {completeness_path}")
    print(f"  {expansion_path}")
    print(f"  {overlap_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
