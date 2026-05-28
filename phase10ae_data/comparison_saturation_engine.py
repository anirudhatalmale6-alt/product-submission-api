#!/usr/bin/env python3
"""
10AE-F: Comparison Saturation Engine
pethubonline.com - WordPress pet supplies blog (144 published posts)

PURPOSE: Aggressively expand SAFE EDUCATIONAL COMPARISONS.
Generates comparison table templates for posts that lack them.
"""

import subprocess
import json
import csv
import re
import os
import html
import sys
from collections import defaultdict

# ── Config ──────────────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ae_data"

# ── Allowed comparison dimensions ───────────────────────────────────────────
COMPARISON_DIMENSIONS = {
    "materials": {
        "label": "Materials",
        "description": "rubber vs nylon vs rope vs fabric",
        "keywords": ["rubber", "nylon", "rope", "fabric", "cotton", "polyester",
                      "leather", "plush", "silicone", "plastic", "wood", "bamboo",
                      "ceramic", "stainless steel", "metal", "fleece", "canvas",
                      "material", "made of", "construction"],
    },
    "suitability": {
        "label": "Breed/Size Suitability",
        "description": "breed size, age, activity level",
        "keywords": ["small breed", "large breed", "medium breed", "puppy", "kitten",
                      "senior", "active", "lazy", "energetic", "calm", "toy breed",
                      "giant breed", "small dog", "large dog", "breed", "size"],
    },
    "enrichment": {
        "label": "Enrichment Value",
        "description": "mental stimulation level",
        "keywords": ["puzzle", "enrichment", "mental stimulation", "brain", "interactive",
                      "treat-dispensing", "snuffle", "foraging", "intelligence",
                      "boredom", "stimulat", "engage", "challenge"],
    },
    "safety": {
        "label": "Safety",
        "description": "choking risk, toxicity, durability",
        "keywords": ["safe", "safety", "choking", "toxic", "non-toxic", "hazard",
                      "supervise", "supervision", "swallow", "ingest", "bpa-free",
                      "chemical", "danger", "risk", "harmful"],
    },
    "maintenance": {
        "label": "Maintenance",
        "description": "washable, replacement frequency",
        "keywords": ["wash", "clean", "machine washable", "dishwasher", "maintenance",
                      "replace", "replacement", "hygien", "sanitize", "wipe",
                      "care", "easy to clean"],
    },
    "durability": {
        "label": "Durability",
        "description": "light chewer vs heavy chewer",
        "keywords": ["durable", "durability", "tough", "indestructible", "heavy chewer",
                      "light chewer", "aggressive chewer", "tear", "rip", "destroy",
                      "long-lasting", "sturdy", "robust", "chew-proof", "bite"],
    },
    "comfort": {
        "label": "Comfort",
        "description": "support level, temperature",
        "keywords": ["comfort", "comfortable", "soft", "cushion", "orthopedic",
                      "memory foam", "support", "temperature", "cooling", "warming",
                      "cozy", "plush", "padded", "ergonomic", "joint"],
    },
    "age_suitability": {
        "label": "Age Suitability",
        "description": "puppy vs adult vs senior",
        "keywords": ["puppy", "kitten", "adult", "senior", "age", "young", "old",
                      "growing", "mature", "elderly", "geriatric", "life stage",
                      "junior", "baby"],
    },
    "behavioral": {
        "label": "Behavioral Suitability",
        "description": "anxious dogs, aggressive chewers",
        "keywords": ["anxiety", "anxious", "aggressive", "separation", "fearful",
                      "nervous", "calm", "hyperactive", "reactive", "behavior",
                      "destructive", "stress", "soothing", "therapeutic"],
    },
    "environmental": {
        "label": "Environmental Suitability",
        "description": "indoor vs outdoor",
        "keywords": ["indoor", "outdoor", "apartment", "yard", "garden", "travel",
                      "car", "crate", "weather", "waterproof", "rain", "sun",
                      "portable", "space", "home"],
    },
}

# ── Topic clusters for pet supplies ─────────────────────────────────────────
TOPIC_CLUSTERS = {
    "toys": {
        "keywords": ["toy", "toys", "play", "fetch", "tug", "ball", "frisbee", "squeaky",
                      "chew toy", "plush toy", "rope toy", "interactive toy"],
        "dimensions": ["materials", "durability", "safety", "enrichment", "suitability",
                        "age_suitability", "behavioral", "environmental"],
    },
    "beds_and_furniture": {
        "keywords": ["bed", "beds", "crate", "kennel", "house", "mat", "blanket",
                      "furniture", "couch", "sofa", "ramp", "stairs", "step"],
        "dimensions": ["comfort", "materials", "durability", "maintenance", "suitability",
                        "age_suitability", "environmental"],
    },
    "food_and_nutrition": {
        "keywords": ["food", "diet", "nutrition", "feed", "treat", "snack", "kibble",
                      "wet food", "raw", "grain-free", "protein", "vitamin",
                      "supplement", "meal", "recipe", "ingredient"],
        "dimensions": ["suitability", "age_suitability", "safety", "behavioral"],
    },
    "grooming": {
        "keywords": ["groom", "grooming", "brush", "shampoo", "bath", "nail", "clipper",
                      "coat", "fur", "hair", "shed", "deshed", "trim", "comb"],
        "dimensions": ["materials", "suitability", "maintenance", "safety",
                        "comfort", "age_suitability"],
    },
    "health_and_wellness": {
        "keywords": ["health", "vet", "veterinar", "medicine", "supplement", "joint",
                      "dental", "teeth", "flea", "tick", "worm", "parasite",
                      "allergy", "skin", "ear", "eye", "wound", "first aid"],
        "dimensions": ["safety", "suitability", "age_suitability", "behavioral",
                        "maintenance"],
    },
    "training": {
        "keywords": ["train", "training", "obedience", "command", "leash", "collar",
                      "harness", "clicker", "reward", "behavior", "potty",
                      "housebreak", "socialize", "crate train"],
        "dimensions": ["suitability", "behavioral", "age_suitability", "safety",
                        "durability", "materials"],
    },
    "collars_leashes_harnesses": {
        "keywords": ["collar", "leash", "harness", "lead", "retractable", "chain",
                      "nylon leash", "leather collar", "martingale", "no-pull"],
        "dimensions": ["materials", "durability", "safety", "suitability",
                        "comfort", "behavioral"],
    },
    "bowls_and_feeders": {
        "keywords": ["bowl", "feeder", "water", "fountain", "slow feeder",
                      "elevated", "automatic", "dispenser", "dish"],
        "dimensions": ["materials", "maintenance", "safety", "suitability",
                        "durability", "environmental"],
    },
    "carriers_and_travel": {
        "keywords": ["carrier", "travel", "crate", "backpack", "stroller", "car seat",
                      "seatbelt", "airline", "portable", "transport"],
        "dimensions": ["suitability", "comfort", "safety", "materials",
                        "durability", "environmental"],
    },
    "clothing_and_accessories": {
        "keywords": ["cloth", "jacket", "sweater", "coat", "boot", "shoe", "bandana",
                      "costume", "raincoat", "vest", "dress"],
        "dimensions": ["materials", "comfort", "suitability", "maintenance",
                        "environmental", "durability"],
    },
    "cat_specific": {
        "keywords": ["cat", "kitten", "feline", "litter", "scratching post", "cat tree",
                      "catnip", "cat toy", "cat bed", "cat food", "cat treat"],
        "dimensions": ["materials", "safety", "enrichment", "maintenance",
                        "durability", "age_suitability", "environmental"],
    },
    "general_pet_care": {
        "keywords": ["pet", "animal", "care", "owner", "adopt", "rescue", "breed",
                      "puppy", "kitten", "tips", "guide", "how to", "advice"],
        "dimensions": ["suitability", "safety", "age_suitability", "behavioral",
                        "environmental"],
    },
}


def wp_api_get(endpoint):
    """Fetch from WP REST API using curl subprocess."""
    url = f"{WP_API}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  [WARN] curl failed for {endpoint}: {result.stderr[:200]}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [WARN] JSON decode failed for {endpoint}: {result.stdout[:200]}")
        return None


def fetch_all_posts():
    """Paginate through all published posts."""
    all_posts = []
    page = 1
    while True:
        print(f"  Fetching posts page {page}...")
        data = wp_api_get(f"posts?status=publish&per_page=100&page={page}&context=edit")
        if data is None or (isinstance(data, dict) and "code" in data):
            break
        if not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        if len(data) < 100:
            break
        page += 1
    return all_posts


def strip_html(text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_raw_content(post):
    """Extract raw content from post (supports both rendered and raw)."""
    content = ""
    if isinstance(post.get("content"), dict):
        content = post["content"].get("raw", "") or post["content"].get("rendered", "")
    elif isinstance(post.get("content"), str):
        content = post["content"]
    return content


def get_title(post):
    """Extract title from post."""
    title = ""
    if isinstance(post.get("title"), dict):
        title = post["title"].get("raw", "") or post["title"].get("rendered", "")
    elif isinstance(post.get("title"), str):
        title = post["title"]
    return strip_html(title)


def detect_existing_comparisons(raw_content, text_content):
    """Detect existing comparison structures in post content."""
    tables = 0
    vs_sections = 0
    pro_con = 0

    # Count HTML tables
    tables += len(re.findall(r'<table[\s>]', raw_content, re.IGNORECASE))
    tables += len(re.findall(r'<!-- wp:table', raw_content, re.IGNORECASE))

    # Count "vs" sections
    vs_sections += len(re.findall(r'\bvs\.?\b', text_content, re.IGNORECASE))
    vs_sections += len(re.findall(r'\bversus\b', text_content, re.IGNORECASE))
    vs_sections += len(re.findall(r'\bcompared?\s+to\b', text_content, re.IGNORECASE))
    vs_sections += len(re.findall(r'\bcomparison\b', text_content, re.IGNORECASE))

    # Count pro/con sections
    pro_con += len(re.findall(r'\bpros?\s*(and|&)\s*cons?\b', text_content, re.IGNORECASE))
    pro_con += len(re.findall(r'\badvantages?\s*(and|&)\s*disadvantages?\b', text_content, re.IGNORECASE))
    pro_con += len(re.findall(r'\bbenefits?\s*(and|&)\s*drawbacks?\b', text_content, re.IGNORECASE))

    return tables, vs_sections, pro_con


def classify_cluster(title, text_content):
    """Determine which topic cluster a post belongs to."""
    combined = (title + " " + text_content).lower()
    best_cluster = "general_pet_care"
    best_score = 0

    for cluster_name, cluster_data in TOPIC_CLUSTERS.items():
        score = 0
        for kw in cluster_data["keywords"]:
            occurrences = len(re.findall(r'\b' + re.escape(kw) + r'\b', combined, re.IGNORECASE))
            score += occurrences
        # Boost title matches
        for kw in cluster_data["keywords"]:
            if re.search(r'\b' + re.escape(kw) + r'\b', title, re.IGNORECASE):
                score += 5
        if score > best_score:
            best_score = score
            best_cluster = cluster_name

    return best_cluster


def compute_comparison_score(tables, vs_sections, pro_con, word_count):
    """
    Score comparison readiness (0-100).
    Higher = more comparison content already present.
    """
    score = 0.0

    # Tables are the strongest comparison signal
    score += min(tables * 25, 50)

    # VS sections indicate comparison intent
    score += min(vs_sections * 5, 20)

    # Pro/con lists
    score += min(pro_con * 10, 20)

    # Longer posts with no comparisons get a small base score (more opportunity)
    if tables == 0 and vs_sections == 0 and pro_con == 0:
        if word_count > 1000:
            score = 5
        elif word_count > 500:
            score = 3

    return min(round(score, 1), 100)


def determine_relevant_dimensions(cluster, text_content):
    """Determine which comparison dimensions are relevant for a post."""
    cluster_dims = TOPIC_CLUSTERS.get(cluster, {}).get("dimensions", [])
    relevant = []

    text_lower = text_content.lower()
    for dim_key in cluster_dims:
        dim = COMPARISON_DIMENSIONS.get(dim_key)
        if not dim:
            continue
        # Check if any keywords appear in the content
        match_count = 0
        for kw in dim["keywords"]:
            if kw.lower() in text_lower:
                match_count += 1
        # Include dimension if it has keyword matches or is a core cluster dimension
        if match_count >= 1:
            relevant.append(dim_key)

    # If too few matched, include top 3 default dimensions for the cluster
    if len(relevant) < 2 and cluster_dims:
        for d in cluster_dims[:3]:
            if d not in relevant:
                relevant.append(d)
            if len(relevant) >= 3:
                break

    return relevant


def extract_comparison_options(title, text_content, cluster):
    """Extract potential comparison options from the post content."""
    options = []

    # Look for "X vs Y" patterns in title
    vs_match = re.search(r'(.+?)\s+vs\.?\s+(.+)', title, re.IGNORECASE)
    if vs_match:
        options.append(vs_match.group(1).strip())
        options.append(vs_match.group(2).strip())
        return options[:4]

    # For toy posts, try to extract toy types
    if cluster == "toys":
        toy_types = ["rubber toy", "nylon toy", "rope toy", "plush toy",
                      "squeaky toy", "puzzle toy", "ball", "frisbee",
                      "chew toy", "tug toy", "interactive toy"]
        for t in toy_types:
            if t.lower() in text_content.lower():
                label = t.title()
                if label not in options:
                    options.append(label)
        if not options:
            options = ["Option A", "Option B", "Option C"]
    elif cluster == "beds_and_furniture":
        bed_types = ["orthopedic bed", "memory foam bed", "bolster bed",
                      "elevated bed", "cave bed", "heated bed", "cooling bed",
                      "donut bed", "flat mat"]
        for t in bed_types:
            if t.lower() in text_content.lower():
                label = t.title()
                if label not in options:
                    options.append(label)
        if not options:
            options = ["Option A", "Option B", "Option C"]
    elif cluster == "food_and_nutrition":
        food_types = ["dry food", "wet food", "raw food", "grain-free",
                       "limited ingredient", "freeze-dried", "dehydrated"]
        for t in food_types:
            if t.lower() in text_content.lower():
                label = t.title()
                if label not in options:
                    options.append(label)
        if not options:
            options = ["Option A", "Option B", "Option C"]
    elif cluster == "collars_leashes_harnesses":
        gear_types = ["flat collar", "martingale collar", "no-pull harness",
                       "front-clip harness", "back-clip harness", "retractable leash",
                       "standard leash", "chain leash"]
        for t in gear_types:
            if t.lower() in text_content.lower():
                label = t.title()
                if label not in options:
                    options.append(label)
        if not options:
            options = ["Option A", "Option B", "Option C"]
    else:
        options = ["Option A", "Option B", "Option C"]

    # Ensure at least 2, at most 4 options
    if len(options) < 2:
        while len(options) < 3:
            idx = len(options)
            options.append(f"Option {chr(65 + idx)}")
    return options[:4]


def generate_table_template(dimensions, options):
    """Generate a Gutenberg-compatible comparison table HTML template."""
    header_cells = '<th>Feature</th>'
    for opt in options:
        header_cells += f'<th>{opt}</th>'

    rows = ""
    for dim_key in dimensions:
        dim = COMPARISON_DIMENSIONS.get(dim_key)
        if not dim:
            continue
        row = f'<td>{dim["label"]}</td>'
        for _ in options:
            row += f'<td>[{dim["description"]}]</td>'
        rows += f'<tr>{row}</tr>'

    table_html = (
        '<!-- wp:table -->\n'
        '<figure class="wp-block-table"><table><thead><tr>'
        f'{header_cells}'
        '</tr></thead><tbody>'
        f'{rows}'
        '</tbody></table></figure>\n'
        '<!-- /wp:table -->'
    )
    return table_html


def determine_comparison_type(title, text_content, cluster):
    """Determine the most appropriate comparison type."""
    title_lower = title.lower()
    text_lower = text_content.lower()

    if re.search(r'\bvs\.?\b', title_lower) or "versus" in title_lower:
        return "head_to_head"
    elif re.search(r'\btop\s+\d+\b', title_lower) or "best" in title_lower:
        return "multi_option_feature"
    elif "how to choose" in title_lower or "buying guide" in title_lower or "guide" in title_lower:
        return "buyer_guide_matrix"
    elif "review" in title_lower:
        return "feature_breakdown"
    elif cluster in ["toys", "beds_and_furniture", "collars_leashes_harnesses",
                      "bowls_and_feeders", "clothing_and_accessories"]:
        return "multi_option_feature"
    elif cluster in ["food_and_nutrition", "health_and_wellness"]:
        return "suitability_matrix"
    elif cluster in ["training", "grooming"]:
        return "method_comparison"
    else:
        return "general_comparison"


def compute_priority(comparison_score, word_count, cluster):
    """Compute priority for adding comparison table (1=highest, 5=lowest)."""
    # Lower existing comparison score = higher priority
    if comparison_score <= 5:
        base = 1
    elif comparison_score <= 15:
        base = 2
    elif comparison_score <= 30:
        base = 3
    elif comparison_score <= 50:
        base = 4
    else:
        base = 5

    # Longer posts have more room for tables
    if word_count > 1500:
        base = max(1, base - 1)

    # Product-oriented clusters benefit most
    high_value_clusters = ["toys", "beds_and_furniture", "food_and_nutrition",
                            "collars_leashes_harnesses", "bowls_and_feeders",
                            "grooming", "carriers_and_travel"]
    if cluster in high_value_clusters:
        base = max(1, base - 1)

    return min(base, 5)


def main():
    print("=" * 70)
    print("10AE-F: Comparison Saturation Engine")
    print("pethubonline.com — Pet Supplies Blog")
    print("=" * 70)
    print()

    # ── Fetch all posts ─────────────────────────────────────────────────
    print("[1/5] Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"  Fetched {len(posts)} published posts")
    print()

    if not posts:
        print("ERROR: No posts fetched. Exiting.")
        sys.exit(1)

    # ── Analyze each post ───────────────────────────────────────────────
    print("[2/5] Analyzing posts for comparison structures...")
    scores_rows = []
    template_rows = []
    cluster_stats = defaultdict(lambda: {
        "post_count": 0,
        "with_comparisons": 0,
        "needing_comparisons": 0,
        "scores": [],
    })

    for i, post in enumerate(posts):
        post_id = post.get("id", "?")
        title = get_title(post)
        raw_content = get_raw_content(post)
        text_content = strip_html(raw_content)
        word_count = len(text_content.split())

        # Classify cluster
        cluster = classify_cluster(title, text_content)

        # Detect existing comparisons
        tables, vs_sections, pro_con = detect_existing_comparisons(raw_content, text_content)

        # Score
        comparison_score = compute_comparison_score(tables, vs_sections, pro_con, word_count)
        needs_comparison = "YES" if comparison_score < 30 else "NO"

        scores_rows.append({
            "post_id": post_id,
            "title": title,
            "cluster": cluster,
            "existing_tables": tables,
            "existing_vs_sections": vs_sections,
            "existing_pro_con": pro_con,
            "comparison_score": comparison_score,
            "needs_comparison": needs_comparison,
        })

        # Cluster stats
        cluster_stats[cluster]["post_count"] += 1
        cluster_stats[cluster]["scores"].append(comparison_score)
        if tables > 0 or (vs_sections >= 2 and pro_con > 0):
            cluster_stats[cluster]["with_comparisons"] += 1
        if needs_comparison == "YES":
            cluster_stats[cluster]["needing_comparisons"] += 1

        # Generate template if needed
        if needs_comparison == "YES" and word_count >= 200:
            dimensions = determine_relevant_dimensions(cluster, text_content)
            if dimensions:
                options = extract_comparison_options(title, text_content, cluster)
                comparison_type = determine_comparison_type(title, text_content, cluster)
                table_html = generate_table_template(dimensions, options)
                priority = compute_priority(comparison_score, word_count, cluster)

                template_rows.append({
                    "post_id": post_id,
                    "title": title,
                    "cluster": cluster,
                    "comparison_type": comparison_type,
                    "comparison_dimensions": "; ".join(dimensions),
                    "table_html_template": table_html,
                    "priority": priority,
                })

        if (i + 1) % 25 == 0:
            print(f"  Analyzed {i + 1}/{len(posts)} posts...")

    print(f"  Analyzed all {len(posts)} posts")
    print()

    # ── Write CSV 1: Comparison Saturation Scores ───────────────────────
    print("[3/5] Writing Comparison_Saturation_Scores.csv...")
    scores_path = os.path.join(OUTPUT_DIR, "Comparison_Saturation_Scores.csv")
    with open(scores_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "existing_tables",
            "existing_vs_sections", "existing_pro_con",
            "comparison_score", "needs_comparison"
        ])
        writer.writeheader()
        writer.writerows(scores_rows)
    print(f"  Written: {scores_path} ({len(scores_rows)} rows)")

    # ── Write CSV 2: Comparison Table Templates ─────────────────────────
    print("[4/5] Writing Comparison_Table_Templates.csv...")
    templates_path = os.path.join(OUTPUT_DIR, "Comparison_Table_Templates.csv")
    # Sort by priority (ascending = highest priority first)
    template_rows.sort(key=lambda x: x["priority"])
    with open(templates_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "comparison_type",
            "comparison_dimensions", "table_html_template", "priority"
        ])
        writer.writeheader()
        writer.writerows(template_rows)
    print(f"  Written: {templates_path} ({len(template_rows)} rows)")

    # ── Write CSV 3: Cluster Summary ────────────────────────────────────
    print("[5/5] Writing Comparison_Cluster_Summary.csv...")
    summary_path = os.path.join(OUTPUT_DIR, "Comparison_Cluster_Summary.csv")
    summary_rows = []
    for cluster_name in sorted(cluster_stats.keys()):
        stats = cluster_stats[cluster_name]
        avg_score = (sum(stats["scores"]) / len(stats["scores"])) if stats["scores"] else 0
        # Priority: clusters with most posts needing comparisons get highest priority
        if stats["needing_comparisons"] > 0:
            ratio = stats["needing_comparisons"] / stats["post_count"]
            if ratio >= 0.8:
                priority = 1
            elif ratio >= 0.6:
                priority = 2
            elif ratio >= 0.4:
                priority = 3
            else:
                priority = 4
        else:
            priority = 5

        summary_rows.append({
            "cluster": cluster_name,
            "post_count": stats["post_count"],
            "posts_with_comparisons": stats["with_comparisons"],
            "posts_needing_comparisons": stats["needing_comparisons"],
            "avg_comparison_score": round(avg_score, 1),
            "priority": priority,
        })

    # Sort by priority then by needing comparisons count descending
    summary_rows.sort(key=lambda x: (x["priority"], -x["posts_needing_comparisons"]))

    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cluster", "post_count", "posts_with_comparisons",
            "posts_needing_comparisons", "avg_comparison_score", "priority"
        ])
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"  Written: {summary_path} ({len(summary_rows)} rows)")

    # ── Summary ─────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("COMPARISON SATURATION ENGINE - SUMMARY")
    print("=" * 70)
    print()

    total_posts = len(scores_rows)
    posts_needing = sum(1 for r in scores_rows if r["needs_comparison"] == "YES")
    posts_ok = total_posts - posts_needing
    templates_generated = len(template_rows)
    avg_score = sum(r["comparison_score"] for r in scores_rows) / total_posts if total_posts else 0
    posts_with_tables = sum(1 for r in scores_rows if r["existing_tables"] > 0)
    posts_with_vs = sum(1 for r in scores_rows if r["existing_vs_sections"] > 0)
    posts_with_procon = sum(1 for r in scores_rows if r["existing_pro_con"] > 0)

    print(f"  Total published posts analyzed:   {total_posts}")
    print(f"  Average comparison score:         {avg_score:.1f}/100")
    print()
    print(f"  Posts with existing tables:       {posts_with_tables} ({100*posts_with_tables/total_posts:.1f}%)")
    print(f"  Posts with vs-sections:           {posts_with_vs} ({100*posts_with_vs/total_posts:.1f}%)")
    print(f"  Posts with pro/con:               {posts_with_procon} ({100*posts_with_procon/total_posts:.1f}%)")
    print()
    print(f"  Posts NEEDING comparisons:        {posts_needing} ({100*posts_needing/total_posts:.1f}%)")
    print(f"  Posts with adequate comparisons:   {posts_ok} ({100*posts_ok/total_posts:.1f}%)")
    print(f"  Comparison templates generated:    {templates_generated}")
    print()

    # Priority breakdown
    p1 = sum(1 for r in template_rows if r["priority"] == 1)
    p2 = sum(1 for r in template_rows if r["priority"] == 2)
    p3 = sum(1 for r in template_rows if r["priority"] == 3)
    p4 = sum(1 for r in template_rows if r["priority"] == 4)
    p5 = sum(1 for r in template_rows if r["priority"] == 5)
    print(f"  Priority 1 (critical):  {p1} posts")
    print(f"  Priority 2 (high):      {p2} posts")
    print(f"  Priority 3 (medium):    {p3} posts")
    print(f"  Priority 4 (low):       {p4} posts")
    print(f"  Priority 5 (minimal):   {p5} posts")
    print()

    # Cluster breakdown
    print("  CLUSTER BREAKDOWN:")
    print(f"  {'Cluster':<30} {'Posts':>5} {'Need Comp':>10} {'Avg Score':>10} {'Priority':>8}")
    print(f"  {'-'*30} {'-'*5} {'-'*10} {'-'*10} {'-'*8}")
    for row in summary_rows:
        print(f"  {row['cluster']:<30} {row['post_count']:>5} "
              f"{row['posts_needing_comparisons']:>10} "
              f"{row['avg_comparison_score']:>10.1f} "
              f"{row['priority']:>8}")
    print()

    # Top 10 highest-priority posts
    print("  TOP 10 HIGHEST-PRIORITY POSTS FOR COMPARISON TABLES:")
    print(f"  {'ID':>6}  {'Score':>5}  {'Cluster':<25} Title")
    print(f"  {'-'*6}  {'-'*5}  {'-'*25} {'-'*40}")
    for row in template_rows[:10]:
        title_short = row["title"][:50] + "..." if len(row["title"]) > 50 else row["title"]
        score = next((s["comparison_score"] for s in scores_rows if s["post_id"] == row["post_id"]), "?")
        print(f"  {row['post_id']:>6}  {score:>5}  {row['cluster']:<25} {title_short}")
    print()

    print("  OUTPUT FILES:")
    print(f"    {scores_path}")
    print(f"    {templates_path}")
    print(f"    {summary_path}")
    print()
    print("=" * 70)
    print("DONE - Comparison Saturation Engine complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
