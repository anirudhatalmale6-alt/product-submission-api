#!/usr/bin/env python3
"""
10AE-C: Semantic Autocomplete Engine
pethubonline.com — WordPress pet supplies blog (144 published posts)

Detects missing terminology, weak semantic reinforcement, and generates
inline educational context recommendations.
"""

import csv
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from html import unescape

# ── WordPress API config ─────────────────────────────────────────────
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ae_data"

# ── Terminology Knowledge Base ───────────────────────────────────────
TERMINOLOGY_KB = {
    "Dog Toys": [
        "enrichment", "desensitisation", "resource guarding", "puzzle feeder",
        "interactive toy", "tug toy", "flirt pole", "snuffle mat", "dental chew",
        "lick mat", "denier", "stuffable toy", "nylon chew"
    ],
    "Dog Food": [
        "kibble", "complete food", "complementary food", "grain-free",
        "freeze-dried", "slow feeder", "body condition score", "FEDIAF",
        "palatability", "digestibility", "guaranteed analysis", "crude protein",
        "moisture content"
    ],
    "Dog Beds": [
        "orthopaedic", "memory foam", "bolster bed", "nest bed", "elevated bed",
        "denier", "waterproof liner", "anti-microbial"
    ],
    "Dog Health": [
        "microchip", "body condition score", "dental scaling", "joint supplement",
        "glucosamine", "omega fatty acids", "parasite lifecycle", "spot-on treatment"
    ],
    "Puppy Care": [
        "socialisation", "counter-conditioning", "positive reinforcement", "recall",
        "mouthing", "crate training", "high-value treat", "clicker training",
        "separation anxiety", "bite inhibition"
    ],
    "Cat": [
        "catnip", "pheromone diffuser", "scratching post", "interactive toy",
        "indoor enrichment", "vertical space", "litter substrate"
    ],
    "General": [
        "RSPCA", "BVA", "positive reinforcement", "enrichment",
        "body condition score", "microchip"
    ],
}

# ── Plain-English definitions for every term ─────────────────────────
TERM_DEFINITIONS = {
    # Dog Toys
    "enrichment": "Enrichment -- activities and objects that stimulate a pet's mind and body, preventing boredom and behavioural problems.",
    "desensitisation": "Desensitisation -- gradually exposing a dog to a trigger (sound, object, situation) at low intensity so it learns to stay calm.",
    "resource guarding": "Resource guarding -- when a dog becomes protective or aggressive over food, toys, or other valued items.",
    "puzzle feeder": "Puzzle feeder -- a toy that hides treats inside compartments, making the dog work to get the food out.",
    "interactive toy": "Interactive toy -- a toy designed for play between pet and owner, or one that responds to the pet's actions.",
    "tug toy": "Tug toy -- a rope or fabric toy built for two-way pulling games between dog and handler.",
    "flirt pole": "Flirt pole -- a long stick with a lure on a string at the end, used for chase-and-catch exercise.",
    "snuffle mat": "Snuffle mat -- a fabric mat with deep loops where treats are hidden, encouraging dogs to sniff and forage.",
    "dental chew": "Dental chew -- a hard treat or toy designed to scrape plaque from teeth during chewing.",
    "lick mat": "Lick mat -- a textured silicone mat you spread soft food onto; the repetitive licking soothes anxious dogs.",
    "denier": "Denier -- a measure of fabric thickness and durability; higher denier means tougher, more tear-resistant material.",
    "stuffable toy": "Stuffable toy -- a hollow rubber or silicone toy you can fill with treats or paste to keep a dog occupied.",
    "nylon chew": "Nylon chew -- a hard synthetic chew toy that lasts longer than natural materials, suitable for aggressive chewers.",
    # Dog Food
    "kibble": "Kibble -- dry, pellet-shaped dog food that is shelf-stable and convenient for everyday feeding.",
    "complete food": "Complete food -- a diet that contains every nutrient a dog needs, so nothing else has to be added.",
    "complementary food": "Complementary food -- a product (like a topper or treat) that must be fed alongside a complete diet, not on its own.",
    "grain-free": "Grain-free -- food made without wheat, corn, or rice, often using potato or legume starches instead.",
    "freeze-dried": "Freeze-dried -- raw food preserved by removing moisture at low temperatures, keeping nutrients and flavour intact.",
    "slow feeder": "Slow feeder -- a bowl or mat with ridges that forces a dog to eat more slowly, reducing bloat and overeating.",
    "body condition score": "Body condition score (BCS) -- a 1-to-9 scale vets use to judge whether a pet is underweight, ideal, or overweight by feeling ribs and waist.",
    "FEDIAF": "FEDIAF -- the European Pet Food Industry Federation, which sets nutritional guidelines for pet food sold in Europe.",
    "palatability": "Palatability -- how appealing and tasty a food is to a pet; high palatability means the pet eats it eagerly.",
    "digestibility": "Digestibility -- the percentage of nutrients in food that a pet's body can actually absorb and use.",
    "guaranteed analysis": "Guaranteed analysis -- the label section listing minimum or maximum levels of protein, fat, fibre, and moisture.",
    "crude protein": "Crude protein -- the total protein content shown on a pet food label, measured by nitrogen content.",
    "moisture content": "Moisture content -- the percentage of water in a pet food; wet food is typically 75-80 percent moisture.",
    # Dog Beds
    "orthopaedic": "Orthopaedic -- designed to support joints and bones, usually with dense or memory foam, ideal for older or arthritic dogs.",
    "memory foam": "Memory foam -- a dense foam that moulds to a dog's body shape, relieving pressure on joints.",
    "bolster bed": "Bolster bed -- a dog bed with raised cushioned sides that give a sense of security and a place to rest the head.",
    "nest bed": "Nest bed -- a round, deep-walled bed that lets dogs curl up and feel enclosed, mimicking a den.",
    "elevated bed": "Elevated bed -- a raised cot-style bed that keeps the dog off the floor, improving airflow and cooling.",
    "waterproof liner": "Waterproof liner -- a moisture-blocking layer inside the bed cover that protects the foam from accidents and spills.",
    "anti-microbial": "Anti-microbial -- treated to resist bacteria, mould, and odour, keeping the bed fresher for longer.",
    # Dog Health
    "microchip": "Microchip -- a tiny electronic chip implanted under the skin that stores a unique ID, helping reunite lost pets with owners.",
    "dental scaling": "Dental scaling -- a veterinary procedure that removes tartar and plaque from teeth, usually under anaesthesia.",
    "joint supplement": "Joint supplement -- a daily pill or powder containing ingredients like glucosamine to support cartilage and joint health.",
    "glucosamine": "Glucosamine -- a natural compound that helps maintain healthy cartilage in joints, commonly used for arthritis management.",
    "omega fatty acids": "Omega fatty acids -- essential fats (omega-3 and omega-6) that support skin, coat, brain, and joint health.",
    "parasite lifecycle": "Parasite lifecycle -- the stages a parasite goes through (egg, larva, adult); understanding it helps time treatments correctly.",
    "spot-on treatment": "Spot-on treatment -- a liquid anti-parasite medication applied to the back of the neck, absorbed through the skin.",
    # Puppy Care
    "socialisation": "Socialisation -- the critical period (roughly 3-14 weeks) when puppies learn to accept new people, animals, and environments.",
    "counter-conditioning": "Counter-conditioning -- changing a dog's negative emotional response to a trigger by pairing it with something positive.",
    "positive reinforcement": "Positive reinforcement -- rewarding desired behaviour (with treats, praise, or play) so the dog is more likely to repeat it.",
    "recall": "Recall -- training a dog to come back to you reliably when called, one of the most important safety commands.",
    "mouthing": "Mouthing -- when a puppy chews or nibbles on hands and objects; normal exploration behaviour that needs gentle redirection.",
    "crate training": "Crate training -- teaching a dog to see a crate as a safe, comfortable den, useful for house-training and travel.",
    "high-value treat": "High-value treat -- an especially tasty reward (like cheese or liver) used for difficult training situations.",
    "clicker training": "Clicker training -- using a small clicking device to mark the exact moment a dog does something right, followed by a treat.",
    "separation anxiety": "Separation anxiety -- extreme distress a dog feels when left alone, often leading to destructive behaviour or vocalisation.",
    "bite inhibition": "Bite inhibition -- a learned behaviour where a dog controls the force of its bite, usually taught during puppy play.",
    # Cat
    "catnip": "Catnip -- a herb (Nepeta cataria) that triggers a temporary euphoric response in about two-thirds of cats.",
    "pheromone diffuser": "Pheromone diffuser -- a plug-in device that releases synthetic calming pheromones to reduce stress in cats.",
    "scratching post": "Scratching post -- a vertical or angled surface (sisal, cardboard, or wood) that lets cats scratch naturally, protecting furniture.",
    "indoor enrichment": "Indoor enrichment -- toys, climbing structures, and puzzle feeders that keep house cats mentally and physically active.",
    "vertical space": "Vertical space -- shelves, cat trees, and wall perches that let cats climb and survey their territory from above.",
    "litter substrate": "Litter substrate -- the material inside a litter tray (clay, silica, wood, paper) that absorbs waste and odour.",
    # General / authority bodies
    "RSPCA": "RSPCA -- the Royal Society for the Prevention of Cruelty to Animals, the UK's leading animal welfare charity.",
    "BVA": "BVA -- the British Veterinary Association, the national body representing veterinary professionals in the UK.",
}

# ── Cluster classification keywords ──────────────────────────────────
CLUSTER_KEYWORDS = {
    "Dog Toys": ["toy", "chew", "puzzle", "tug", "fetch", "play", "ball", "rope"],
    "Dog Food": ["food", "diet", "nutrition", "feed", "kibble", "raw", "meal", "treat", "recipe"],
    "Dog Beds": ["bed", "sleep", "crate", "mat", "cushion", "blanket", "den"],
    "Dog Health": ["health", "vet", "disease", "parasite", "flea", "tick", "worm", "vaccine", "supplement", "dental"],
    "Puppy Care": ["puppy", "puppies", "training", "socialisation", "socialization", "house-training", "housetraining"],
    "Cat": ["cat", "kitten", "feline", "litter", "catnip", "scratching"],
}

# ── Educational context detection patterns ───────────────────────────
DEFINITION_PATTERNS = [
    r"(?:which|that)\s+(?:means?|is|refers?\s+to|stands?\s+for)",
    r"(?:also\s+)?(?:known|called|referred\s+to)\s+as",
    r"(?:in\s+)?(?:simple|plain|other)\s+(?:terms|words)",
    r"--\s+(?:a|an|the)\s+",
    r"[–—]\s*(?:a|an|the)\s+",
    r"\(\s*(?:i\.?e\.?|meaning|that\s+is)",
    r"defined\s+as",
    r"what\s+(?:this|it|that)\s+means",
]
DEFINITION_RE = re.compile("|".join(DEFINITION_PATTERNS), re.IGNORECASE)

BEGINNER_PATTERNS = [
    r"what\s+(?:this|it|that)\s+means",
    r"in\s+simple\s+terms",
    r"for\s+beginners?",
    r"put\s+simply",
    r"in\s+other\s+words",
    r"if\s+you(?:'re|\s+are)\s+new\s+to",
    r"beginner(?:'s)?\s+guide",
    r"simply\s+put",
]
BEGINNER_RE = re.compile("|".join(BEGINNER_PATTERNS), re.IGNORECASE)


# ─────────────────────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────────────────────

def fetch_all_posts():
    """Paginate through the WP REST API and return all published posts."""
    posts = []
    page = 1
    while True:
        url = f"{WP_BASE}/posts?status=publish&per_page=100&page={page}&context=edit"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60,
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            break
        if not isinstance(data, list) or len(data) == 0:
            break
        posts.extend(data)
        print(f"  Fetched page {page}: {len(data)} posts (total {len(posts)})")
        if len(data) < 100:
            break
        page += 1
    return posts


def strip_html(html_text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", " ", html_text or "")
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def classify_cluster(title, content):
    """Assign post to the best-matching cluster based on keyword density."""
    combined = (title + " " + content).lower()
    scores = {}
    for cluster, keywords in CLUSTER_KEYWORDS.items():
        score = sum(combined.count(kw) for kw in keywords)
        scores[cluster] = score
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "General"
    return best


def term_present(term, text_lower):
    """Check if a term appears in the text (case-insensitive, word-boundary)."""
    # Handle both UK and US spellings
    variants = [term.lower()]
    if "isation" in term.lower():
        variants.append(term.lower().replace("isation", "ization"))
    if "isation" not in term.lower() and "ization" in term.lower():
        variants.append(term.lower().replace("ization", "isation"))
    if "orthopaedic" in term.lower():
        variants.append("orthopedic")
    if "orthopaedic" not in term.lower() and "orthopedic" in term.lower():
        variants.append("orthopaedic")

    for v in variants:
        pattern = re.compile(r"\b" + re.escape(v) + r"\b", re.IGNORECASE)
        if pattern.search(text_lower):
            return True
    return False


def term_has_definition(term, text):
    """Check whether the term is followed by definitional context within 200 chars."""
    variants = [term.lower()]
    if "isation" in term.lower():
        variants.append(term.lower().replace("isation", "ization"))
    if "orthopaedic" in term.lower():
        variants.append("orthopedic")

    text_lower = text.lower()
    for v in variants:
        pattern = re.compile(r"\b" + re.escape(v) + r"\b", re.IGNORECASE)
        for match in pattern.finditer(text_lower):
            start = match.start()
            window = text_lower[start:start + 300]
            if DEFINITION_RE.search(window):
                return True
    return False


def has_beginner_support(text):
    """Check if the content has beginner-friendly language patterns."""
    return bool(BEGINNER_RE.search(text))


def get_relevant_clusters(cluster):
    """Return the list of term clusters relevant to a post's cluster."""
    relevant = [cluster]
    if cluster != "General":
        relevant.append("General")
    return relevant


def determine_insertion_location(term, text):
    """Suggest where a definition should be inserted."""
    text_lower = text.lower()
    variants = [term.lower()]
    if "isation" in term.lower():
        variants.append(term.lower().replace("isation", "ization"))
    if "orthopaedic" in term.lower():
        variants.append("orthopedic")

    for v in variants:
        pattern = re.compile(r"\b" + re.escape(v) + r"\b", re.IGNORECASE)
        m = pattern.search(text_lower)
        if m:
            return "After first mention"
    return "In glossary block at end of post"


# ─────────────────────────────────────────────────────────────────────
# Main analysis
# ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("10AE-C: Semantic Autocomplete Engine")
    print("pethubonline.com - Semantic Reinforcement Analysis")
    print("=" * 70)

    # 1. Fetch all posts
    print("\n[1/4] Fetching published posts from WordPress API...")
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}")

    if not posts:
        print("ERROR: No posts fetched. Aborting.")
        sys.exit(1)

    # 2. Analyse each post
    print("\n[2/4] Analysing posts for semantic completeness...")
    detections = []          # rows for Semantic_Autocomplete_Detections.csv
    inline_queue = []        # rows for Inline_Definition_Queue.csv
    cluster_stats = defaultdict(lambda: {
        "total_detections": 0,
        "missing_terms": 0,
        "weak_definitions": 0,
        "weak_beginner_support": 0,
        "completeness_scores": [],
    })

    for post in posts:
        post_id = post.get("id", "?")
        title_raw = post.get("title", {})
        if isinstance(title_raw, dict):
            title = strip_html(title_raw.get("rendered", ""))
        else:
            title = strip_html(str(title_raw))

        content_raw = post.get("content", {})
        if isinstance(content_raw, dict):
            content = strip_html(content_raw.get("rendered", ""))
        else:
            content = strip_html(str(content_raw))

        cluster = classify_cluster(title, content)
        text_lower = (title + " " + content).lower()
        full_text = title + " " + content

        # Determine which term sets apply
        relevant_clusters = get_relevant_clusters(cluster)
        applicable_terms = []
        for rc in relevant_clusters:
            if rc in TERMINOLOGY_KB:
                applicable_terms.extend(TERMINOLOGY_KB[rc])
        applicable_terms = list(dict.fromkeys(applicable_terms))  # dedupe preserving order

        post_missing = 0
        post_weak_def = 0
        post_total_applicable = len(applicable_terms)

        for term in applicable_terms:
            present = term_present(term, text_lower)
            has_def = False
            if present:
                has_def = term_has_definition(term, full_text)

            # Detection type 1: Missing terminology
            if not present:
                severity = "high" if term in TERMINOLOGY_KB.get(cluster, []) else "medium"
                detections.append({
                    "post_id": post_id,
                    "title": title,
                    "cluster": cluster,
                    "detection_type": "missing_terminology",
                    "term": term,
                    "severity": severity,
                    "current_state": "Term not found anywhere in post content",
                    "recommended_action": f"Add '{term}' with inline definition to strengthen topical authority",
                })
                cluster_stats[cluster]["total_detections"] += 1
                cluster_stats[cluster]["missing_terms"] += 1
                post_missing += 1

                # Queue inline definition
                definition = TERM_DEFINITIONS.get(term, f"{term} -- [definition needed]")
                inline_queue.append({
                    "post_id": post_id,
                    "title": title,
                    "cluster": cluster,
                    "term": term,
                    "definition_text": definition,
                    "insertion_location": "In glossary block at end of post",
                    "priority": "high" if severity == "high" else "medium",
                })

            # Detection type 2: Weak semantic reinforcement (present but no definition)
            elif present and not has_def:
                detections.append({
                    "post_id": post_id,
                    "title": title,
                    "cluster": cluster,
                    "detection_type": "weak_semantic_reinforcement",
                    "term": term,
                    "severity": "medium",
                    "current_state": "Term mentioned but not defined or explained in context",
                    "recommended_action": f"Add inline definition after first mention of '{term}'",
                })
                cluster_stats[cluster]["total_detections"] += 1
                cluster_stats[cluster]["weak_definitions"] += 1
                post_weak_def += 1

                definition = TERM_DEFINITIONS.get(term, f"{term} -- [definition needed]")
                loc = determine_insertion_location(term, full_text)
                inline_queue.append({
                    "post_id": post_id,
                    "title": title,
                    "cluster": cluster,
                    "term": term,
                    "definition_text": definition,
                    "insertion_location": loc,
                    "priority": "medium",
                })

        # Detection type 3: Unclear definitions -- technical terms without plain language
        # Check all terms that ARE present but lack nearby plain language
        tech_terms_present = [t for t in applicable_terms if term_present(t, text_lower)]
        for term in tech_terms_present:
            if not term_has_definition(term, full_text):
                # Already captured as weak_semantic_reinforcement above, skip duplicate
                pass

        # Detection type 5 & 6: Weak beginner support / educational context
        if not has_beginner_support(content):
            detections.append({
                "post_id": post_id,
                "title": title,
                "cluster": cluster,
                "detection_type": "weak_beginner_support",
                "term": "(post-level)",
                "severity": "low",
                "current_state": "No beginner-friendly framing detected (no 'in simple terms', 'what this means', etc.)",
                "recommended_action": "Add an introductory sentence or 'what this means for you' section for new pet owners",
            })
            cluster_stats[cluster]["total_detections"] += 1
            cluster_stats[cluster]["weak_beginner_support"] += 1

        # Semantic completeness score for this post
        if post_total_applicable > 0:
            terms_present_defined = post_total_applicable - post_missing - post_weak_def
            completeness = round((terms_present_defined / post_total_applicable) * 100, 1)
        else:
            completeness = 100.0
        cluster_stats[cluster]["completeness_scores"].append(completeness)

    print(f"  Total detections: {len(detections)}")
    print(f"  Inline definitions queued: {len(inline_queue)}")

    # 3. Write CSVs
    print("\n[3/4] Writing output CSV files...")

    # CSV 1: Semantic_Autocomplete_Detections.csv
    det_path = os.path.join(OUTPUT_DIR, "Semantic_Autocomplete_Detections.csv")
    with open(det_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "detection_type", "term",
            "severity", "current_state", "recommended_action"
        ])
        writer.writeheader()
        writer.writerows(detections)
    print(f"  -> {det_path} ({len(detections)} rows)")

    # CSV 2: Inline_Definition_Queue.csv
    inl_path = os.path.join(OUTPUT_DIR, "Inline_Definition_Queue.csv")
    with open(inl_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "term", "definition_text",
            "insertion_location", "priority"
        ])
        writer.writeheader()
        writer.writerows(inline_queue)
    print(f"  -> {inl_path} ({len(inline_queue)} rows)")

    # CSV 3: Semantic_Reinforcement_Summary.csv
    summary_rows = []
    for cluster_name in sorted(set(list(TERMINOLOGY_KB.keys()) + list(cluster_stats.keys()))):
        stats = cluster_stats.get(cluster_name, {
            "total_detections": 0, "missing_terms": 0,
            "weak_definitions": 0, "weak_beginner_support": 0,
            "completeness_scores": [],
        })
        scores = stats.get("completeness_scores", [])
        avg_completeness = round(sum(scores) / len(scores), 1) if scores else 0.0
        summary_rows.append({
            "cluster": cluster_name,
            "total_detections": stats["total_detections"],
            "missing_terms": stats["missing_terms"],
            "weak_definitions": stats["weak_definitions"],
            "weak_beginner_support": stats["weak_beginner_support"],
            "avg_semantic_completeness": f"{avg_completeness}%",
        })

    sum_path = os.path.join(OUTPUT_DIR, "Semantic_Reinforcement_Summary.csv")
    with open(sum_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cluster", "total_detections", "missing_terms", "weak_definitions",
            "weak_beginner_support", "avg_semantic_completeness"
        ])
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"  -> {sum_path} ({len(summary_rows)} rows)")

    # 4. Summary
    print("\n" + "=" * 70)
    print("SEMANTIC AUTOCOMPLETE ENGINE - SUMMARY")
    print("=" * 70)
    print(f"\nPosts analysed: {len(posts)}")
    print(f"Total detections: {len(detections)}")
    print(f"Inline definitions queued: {len(inline_queue)}")

    # By detection type
    type_counts = defaultdict(int)
    for d in detections:
        type_counts[d["detection_type"]] += 1
    print(f"\nDetection breakdown:")
    for dt, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        label = dt.replace("_", " ").title()
        print(f"  {label}: {count}")

    # By severity
    sev_counts = defaultdict(int)
    for d in detections:
        sev_counts[d["severity"]] += 1
    print(f"\nSeverity breakdown:")
    for sev in ["high", "medium", "low"]:
        if sev in sev_counts:
            print(f"  {sev.capitalize()}: {sev_counts[sev]}")

    # By cluster
    print(f"\nCluster summary:")
    print(f"  {'Cluster':<15} {'Detect':>7} {'Missing':>8} {'WeakDef':>8} {'BeginSup':>9} {'Completeness':>13}")
    print(f"  {'-'*15} {'-'*7} {'-'*8} {'-'*8} {'-'*9} {'-'*13}")
    for row in summary_rows:
        print(f"  {row['cluster']:<15} {row['total_detections']:>7} {row['missing_terms']:>8} "
              f"{row['weak_definitions']:>8} {row['weak_beginner_support']:>9} "
              f"{row['avg_semantic_completeness']:>13}")

    # Top missing terms
    term_missing_count = defaultdict(int)
    for d in detections:
        if d["detection_type"] == "missing_terminology":
            term_missing_count[d["term"]] += 1
    if term_missing_count:
        print(f"\nTop 15 most-missing terms across all posts:")
        for term, count in sorted(term_missing_count.items(), key=lambda x: -x[1])[:15]:
            print(f"  {term:<25} missing from {count} posts")

    # Top weakly-defined terms
    term_weak_count = defaultdict(int)
    for d in detections:
        if d["detection_type"] == "weak_semantic_reinforcement":
            term_weak_count[d["term"]] += 1
    if term_weak_count:
        print(f"\nTop 15 weakly-defined terms (mentioned but not explained):")
        for term, count in sorted(term_weak_count.items(), key=lambda x: -x[1])[:15]:
            print(f"  {term:<25} weak in {count} posts")

    print(f"\nOutput files:")
    print(f"  {det_path}")
    print(f"  {inl_path}")
    print(f"  {sum_path}")
    print(f"\n{'=' * 70}")
    print("Semantic Autocomplete Engine complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
