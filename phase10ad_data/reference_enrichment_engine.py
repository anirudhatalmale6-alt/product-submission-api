#!/usr/bin/env python3
"""
10AD-E: Reference Enrichment Engine for pethubonline.com
Audits and scores every post's external reference quality, tracks which UK
authority sources are cited, identifies posts missing references, and
recommends specific reference additions.

STRICTLY EDUCATIONAL and TRUST-SAFE — no fake references, no invented citations.
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

# ─── Trusted UK Reference Sources ───────────────────────────────────────────
TRUSTED_SOURCES = {
    "rspca": {
        "name": "RSPCA",
        "domains": ["rspca.org.uk"],
        "text_patterns": [r"\brspca\b"],
        "description": "animal welfare guidance",
    },
    "battersea": {
        "name": "Battersea",
        "domains": ["battersea.org.uk"],
        "text_patterns": [r"\bbattersea\b"],
        "description": "pet care advice",
    },
    "cats_protection": {
        "name": "Cats Protection",
        "domains": ["cats.org.uk"],
        "text_patterns": [r"\bcats\s+protection\b"],
        "description": "cat welfare and care",
    },
    "blue_cross": {
        "name": "Blue Cross",
        "domains": ["bluecross.org.uk"],
        "text_patterns": [r"\bblue\s*cross\b"],
        "description": "pet health advice",
    },
    "pdsa": {
        "name": "PDSA",
        "domains": ["pdsa.org.uk"],
        "text_patterns": [r"\bpdsa\b"],
        "description": "vet charity, pet health",
    },
    "bva": {
        "name": "BVA",
        "domains": ["bva.co.uk"],
        "text_patterns": [r"\bbva\b", r"\bbritish\s+veterinary\s+association\b"],
        "description": "British Veterinary Association",
    },
    "fediaf": {
        "name": "FEDIAF",
        "domains": ["fediaf.org"],
        "text_patterns": [r"\bfediaf\b", r"\beuropean\s+pet\s+food\s+industry\s+federation\b"],
        "description": "European pet food nutrition guidelines",
    },
    "defra": {
        "name": "DEFRA",
        "domains": ["gov.uk/defra", "gov.uk/government/organisations/department-for-environment-food-rural-affairs"],
        "text_patterns": [r"\bdefra\b", r"\bdepartment\s+for\s+environment.{0,20}food\b"],
        "description": "UK government animal regulations",
    },
    "uk_gov": {
        "name": "UK Government",
        "domains": ["gov.uk"],
        "text_patterns": [r"\bgov\.uk\b", r"\buk\s+government\b", r"\bgovernment\s+legislation\b"],
        "description": "legislation, microchipping, pet travel",
    },
    "kennel_club": {
        "name": "Kennel Club",
        "domains": ["thekennelclub.org.uk"],
        "text_patterns": [r"\bkennel\s+club\b", r"\bthe\s+kennel\s+club\b"],
        "description": "breed standards, health testing",
    },
    "pfma": {
        "name": "PFMA",
        "domains": ["pfma.org.uk"],
        "text_patterns": [r"\bpfma\b", r"\bpet\s+food\s+manufacturers?\s+association\b"],
        "description": "Pet Food Manufacturers Association",
    },
}

# ─── Cluster Classification ─────────────────────────────────────────────────
CLUSTER_KEYWORDS = {
    "Dog Toys": ["toy", "toys", "chew", "play", "fetch", "tug", "puzzle", "kong", "nylabone"],
    "Dog Food": ["food", "feed", "diet", "nutrition", "kibble", "raw", "wet food", "dry food",
                 "treat", "treats", "eating", "recipe"],
    "Dog Beds": ["bed", "beds", "sleep", "sleeping", "crate", "den", "nest", "mat", "blanket"],
    "Dog Health": ["health", "vet", "medical", "illness", "disease", "parasite", "flea", "tick",
                   "worm", "supplement", "joint", "dental", "teeth", "skin", "allergy",
                   "vaccination", "neutering", "spay"],
    "Puppy Care": ["puppy", "puppies", "pup", "new dog", "first dog", "getting a dog",
                   "bringing home", "puppy-proof"],
    "Dog Walking": ["walk", "walking", "lead", "leash", "harness", "collar", "hiking",
                    "outdoor", "exercise"],
    "Dog Grooming": ["groom", "grooming", "bath", "bathing", "brush", "brushing", "coat",
                     "fur", "shampoo", "shedding", "nail", "clipping"],
    "Dog Training": ["train", "training", "obedience", "behaviour", "behavior", "command",
                     "recall", "sit", "stay", "heel", "agility"],
    "Cat": ["cat", "cats", "kitten", "feline", "kitty", "litter"],
    "Dog Breeds": ["breed", "breeds", "labrador", "poodle", "spaniel", "terrier", "bulldog",
                   "shepherd", "retriever", "collie", "dachshund", "husky"],
    "Pet Travel": ["travel", "travelling", "holiday", "car", "transport", "pet passport",
                   "microchip", "carrier"],
    "Pet Insurance": ["insurance", "pet insurance", "cover", "claim", "policy", "vet bill"],
}

# ─── Source Relevance by Cluster ─────────────────────────────────────────────
# Which sources SHOULD be referenced for each cluster (high relevance)
CLUSTER_SOURCE_RELEVANCE = {
    "Dog Toys": ["rspca", "blue_cross", "battersea", "kennel_club"],
    "Dog Food": ["fediaf", "pfma", "pdsa", "rspca", "bva", "blue_cross"],
    "Dog Beds": ["rspca", "blue_cross", "pdsa", "kennel_club"],
    "Dog Health": ["bva", "pdsa", "rspca", "blue_cross", "kennel_club", "defra"],
    "Puppy Care": ["rspca", "kennel_club", "blue_cross", "battersea", "pdsa", "uk_gov"],
    "Dog Walking": ["rspca", "kennel_club", "blue_cross", "uk_gov"],
    "Dog Grooming": ["rspca", "blue_cross", "pdsa", "kennel_club"],
    "Dog Training": ["rspca", "kennel_club", "blue_cross", "battersea"],
    "Cat": ["cats_protection", "rspca", "blue_cross", "pdsa", "battersea"],
    "Dog Breeds": ["kennel_club", "rspca", "bva", "blue_cross"],
    "Pet Travel": ["uk_gov", "defra", "rspca", "kennel_club"],
    "Pet Insurance": ["pdsa", "bva", "rspca", "blue_cross"],
    "General": ["rspca", "blue_cross", "pdsa", "bva"],
}

# Topic-specific reference suggestions per source per cluster
SOURCE_TOPIC_SUGGESTIONS = {
    "rspca": {
        "Dog Toys": "safe toy choices and enrichment guidance",
        "Dog Food": "pet nutrition and feeding advice",
        "Dog Beds": "comfortable sleeping environment guidance",
        "Dog Health": "animal welfare and health monitoring",
        "Puppy Care": "responsible puppy ownership advice",
        "Dog Walking": "safe exercise and walking guidance",
        "Dog Grooming": "grooming welfare and coat care",
        "Dog Training": "positive training methods and welfare",
        "Cat": "cat welfare and care standards",
        "Dog Breeds": "breed-specific welfare considerations",
        "Pet Travel": "safe pet travel and transport welfare",
        "Pet Insurance": "financial protection for pet welfare",
        "General": "general animal welfare guidance",
    },
    "battersea": {
        "Dog Toys": "enrichment and play advice for rescue dogs",
        "Puppy Care": "rehoming and settling-in guidance",
        "Dog Training": "behavioural advice for adopted pets",
        "Cat": "cat rehoming and settling-in advice",
        "General": "pet adoption and care guidance",
    },
    "cats_protection": {
        "Cat": "feline welfare, behaviour, and health resources",
        "General": "cat-specific welfare guidance",
    },
    "blue_cross": {
        "Dog Toys": "safe play and enrichment tips",
        "Dog Food": "healthy diet and feeding guidance",
        "Dog Beds": "comfortable rest environment advice",
        "Dog Health": "pet health conditions and symptoms",
        "Puppy Care": "new puppy care and settling advice",
        "Dog Walking": "exercise requirements and safe walking",
        "Dog Grooming": "coat care and grooming tips",
        "Dog Training": "positive reinforcement training resources",
        "Cat": "cat health and care information",
        "Dog Breeds": "breed-specific health and care",
        "Pet Travel": "safe travel with pets advice",
        "Pet Insurance": "pet health cost guidance",
        "General": "general pet health and wellbeing",
    },
    "pdsa": {
        "Dog Food": "veterinary nutrition guidance and weight management",
        "Dog Health": "pet health conditions, treatments, and prevention",
        "Puppy Care": "puppy health checks and vaccination schedules",
        "Dog Grooming": "skin and coat health advice",
        "Cat": "cat health and veterinary care advice",
        "Pet Insurance": "vet cost information and financial support",
        "General": "veterinary health and wellbeing information",
    },
    "bva": {
        "Dog Food": "professional veterinary nutrition standards",
        "Dog Health": "veterinary best practices and clinical guidance",
        "Puppy Care": "vaccination and health check protocols",
        "Dog Breeds": "breed health testing and welfare standards",
        "Pet Insurance": "veterinary profession perspectives on pet insurance",
        "General": "professional veterinary association guidance",
    },
    "fediaf": {
        "Dog Food": "European nutritional guidelines for complete/complementary pet food",
        "Cat": "feline nutritional requirements and feeding guidelines",
        "General": "pet food industry nutritional standards",
    },
    "defra": {
        "Dog Health": "animal disease control and notifiable conditions",
        "Pet Travel": "pet travel scheme regulations and import/export rules",
        "Puppy Care": "puppy farming regulations and breeder licensing",
        "Dog Breeds": "dangerous dogs legislation and breed restrictions",
        "General": "UK animal welfare legislation and regulations",
    },
    "uk_gov": {
        "Puppy Care": "microchipping law, Lucy's Law, breeder regulations",
        "Pet Travel": "pet passport requirements and border regulations",
        "Dog Walking": "dog control orders and public space rules",
        "Dog Breeds": "breed-specific legislation (Dangerous Dogs Act)",
        "General": "UK pet ownership legislation and requirements",
    },
    "kennel_club": {
        "Dog Toys": "breed-appropriate toy and enrichment recommendations",
        "Dog Beds": "breed-specific comfort and sleeping needs",
        "Dog Health": "breed health screening schemes and testing",
        "Puppy Care": "Assured Breeders scheme and puppy buying guide",
        "Dog Walking": "breed-specific exercise requirements",
        "Dog Grooming": "breed-specific grooming standards",
        "Dog Training": "Good Citizen Dog Scheme training resources",
        "Dog Breeds": "breed standards, health data, and registration",
        "General": "breed information and responsible ownership",
    },
    "pfma": {
        "Dog Food": "UK pet food industry data and feeding guidelines",
        "Cat": "cat feeding guidelines and pet food facts",
        "General": "pet food industry statistics and standards",
    },
}


def strip_html(html_text):
    """Remove HTML tags and decode entities."""
    if not html_text:
        return ""
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
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
    content_lower = content_text.lower()[:2000]

    scores = {}
    for cluster_name, keywords in CLUSTER_KEYWORDS.items():
        score = 0
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in title_lower:
                score += 5
            if kw_lower in content_lower:
                score += 1
        scores[cluster_name] = score

    if not scores or max(scores.values()) == 0:
        return "General"

    return max(scores, key=scores.get)


def extract_href_links(html_content):
    """Extract all href URLs from HTML content."""
    if not html_content:
        return []
    links = re.findall(r'href=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
    return links


def check_source_in_post(source_key, source_info, html_content, text_content):
    """
    Check how a trusted source appears in a post.
    Returns: "linked", "mentioned", or "absent"
    Also returns counts: (link_count, mention_count)
    """
    html_lower = html_content.lower() if html_content else ""
    text_lower = text_content.lower() if text_content else ""

    # Check for href links to the source domain
    links = extract_href_links(html_content)
    link_count = 0
    for link in links:
        link_lower = link.lower()
        for domain in source_info["domains"]:
            if domain in link_lower:
                link_count += 1
                break

    # Special handling for uk_gov vs defra — avoid double counting
    # DEFRA URLs are a subset of gov.uk, so uk_gov should not count DEFRA-specific links
    if source_key == "uk_gov":
        defra_domains = TRUSTED_SOURCES["defra"]["domains"]
        for link in links:
            link_lower = link.lower()
            for dd in defra_domains:
                if dd in link_lower:
                    link_count = max(0, link_count - 1)
                    break

    # Check for text mentions (case-insensitive regex)
    mention_count = 0
    for pattern in source_info["text_patterns"]:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        mention_count += len(matches)

    # Avoid double-counting: if we found links, text mentions of the name
    # likely accompany them, so only count excess text mentions
    if link_count > 0:
        # Text mentions that aren't just the anchor text of links
        status = "linked"
    elif mention_count > 0:
        status = "mentioned"
    else:
        status = "absent"

    return status, link_count, mention_count


def calculate_reference_score(source_statuses):
    """
    Calculate a 0-100 reference quality score.
    - Each linked source: 10 points (max 60)
    - Each mentioned source: 4 points (max 24)
    - Diversity bonus: up to 16 points based on how many distinct sources cited
    """
    linked_count = sum(1 for s in source_statuses.values() if s == "linked")
    mentioned_count = sum(1 for s in source_statuses.values() if s == "mentioned")
    total_cited = linked_count + mentioned_count
    total_sources = len(source_statuses)

    # Base scoring
    link_points = min(linked_count * 10, 60)
    mention_points = min(mentioned_count * 4, 24)

    # Diversity bonus: proportion of sources cited
    if total_sources > 0:
        diversity_ratio = total_cited / total_sources
        diversity_points = diversity_ratio * 16
    else:
        diversity_points = 0

    score = link_points + mention_points + diversity_points
    return round(min(100, max(0, score)))


def determine_recommendation_priority(source_key, cluster, source_statuses):
    """
    Determine priority for adding a reference to a post.
    HIGH = source is highly relevant to cluster and completely absent
    MEDIUM = source is relevant and absent
    LOW = source is somewhat relevant or only mentioned (could upgrade to link)
    """
    relevant_sources = CLUSTER_SOURCE_RELEVANCE.get(cluster, CLUSTER_SOURCE_RELEVANCE["General"])
    status = source_statuses.get(source_key, "absent")

    if status == "linked":
        return None  # Already linked, no recommendation needed

    if source_key in relevant_sources[:3] and status == "absent":
        return "HIGH"
    elif source_key in relevant_sources and status == "absent":
        return "MEDIUM"
    elif status == "mentioned":
        return "LOW"  # Upgrade from mention to link
    else:
        return None  # Not relevant enough to recommend


def get_reference_topic(source_key, cluster):
    """Get the specific topic to reference for a source in a cluster."""
    source_topics = SOURCE_TOPIC_SUGGESTIONS.get(source_key, {})
    topic = source_topics.get(cluster, source_topics.get("General", ""))
    if not topic:
        source_info = TRUSTED_SOURCES.get(source_key, {})
        topic = source_info.get("description", "general guidance")
    return topic


def get_recommendation_reason(source_key, cluster, status):
    """Generate a reason for the recommendation."""
    source_name = TRUSTED_SOURCES[source_key]["name"]
    relevant_sources = CLUSTER_SOURCE_RELEVANCE.get(cluster, CLUSTER_SOURCE_RELEVANCE["General"])

    if status == "mentioned":
        return f"{source_name} is text-mentioned but not hyperlinked — adding a link improves trust signals and user navigation"

    if source_key in relevant_sources[:2]:
        return f"{source_name} is a primary authority for {cluster} content — essential for credibility and E-E-A-T signals"
    elif source_key in relevant_sources[:4]:
        return f"{source_name} is a key UK reference for {cluster} topics — adds significant trust value"
    else:
        return f"{source_name} provides relevant {cluster} guidance — strengthens reference diversity"


def main():
    print("=" * 74)
    print("10AD-E: REFERENCE ENRICHMENT ENGINE")
    print("pethubonline.com — Full Site Reference Audit")
    print("=" * 74)

    # ── Step 1: Fetch all posts ──────────────────────────────────────────
    print("\n[1/5] Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}")

    if not posts:
        print("ERROR: No posts fetched. Check API credentials and URL.")
        sys.exit(1)

    # ── Step 2: Analyse references in each post ─────────────────────────
    print(f"\n[2/5] Auditing references across {len(posts)} posts...")

    audit_rows = []
    enrichment_rows = []

    # Track global source coverage
    source_coverage = defaultdict(lambda: {"linked": 0, "mentioned": 0, "absent": 0, "clusters": set()})

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

        text_content = strip_html(html_content)

        if (i + 1) % 20 == 0 or i == 0:
            print(f"  Processing post {i+1}/{len(posts)}: {title[:60]}...")

        # Classify cluster
        cluster = classify_cluster(title, text_content)

        # Check each trusted source
        source_statuses = {}
        total_linked = 0
        total_mentioned = 0
        total_missing = 0

        for source_key, source_info in TRUSTED_SOURCES.items():
            status, link_count, mention_count = check_source_in_post(
                source_key, source_info, html_content, text_content
            )
            source_statuses[source_key] = status

            if status == "linked":
                total_linked += 1
                source_coverage[source_key]["linked"] += 1
                source_coverage[source_key]["clusters"].add(cluster)
            elif status == "mentioned":
                total_mentioned += 1
                source_coverage[source_key]["mentioned"] += 1
                source_coverage[source_key]["clusters"].add(cluster)
            else:
                total_missing += 1
                source_coverage[source_key]["absent"] += 1

        # Calculate reference score
        ref_score = calculate_reference_score(source_statuses)

        # Build audit row
        audit_row = {
            "post_id": post_id,
            "title": title,
            "cluster": cluster,
            "rspca_status": source_statuses.get("rspca", "absent"),
            "battersea_status": source_statuses.get("battersea", "absent"),
            "cats_protection_status": source_statuses.get("cats_protection", "absent"),
            "blue_cross_status": source_statuses.get("blue_cross", "absent"),
            "pdsa_status": source_statuses.get("pdsa", "absent"),
            "bva_status": source_statuses.get("bva", "absent"),
            "fediaf_status": source_statuses.get("fediaf", "absent"),
            "defra_status": source_statuses.get("defra", "absent"),
            "uk_gov_status": source_statuses.get("uk_gov", "absent"),
            "kennel_club_status": source_statuses.get("kennel_club", "absent"),
            "pfma_status": source_statuses.get("pfma", "absent"),
            "total_linked": total_linked,
            "total_mentioned": total_mentioned,
            "total_missing": total_missing,
            "reference_score": ref_score,
        }
        audit_rows.append(audit_row)

        # Generate enrichment recommendations
        for source_key in TRUSTED_SOURCES:
            priority = determine_recommendation_priority(source_key, cluster, source_statuses)
            if priority is not None:
                status = source_statuses.get(source_key, "absent")
                if status == "mentioned":
                    rec_type = "upgrade_to_link"
                else:
                    rec_type = "add_link_and_mention"

                enrichment_rows.append({
                    "post_id": post_id,
                    "title": title,
                    "cluster": cluster,
                    "source_to_add": TRUSTED_SOURCES[source_key]["name"],
                    "reference_type_recommended": rec_type,
                    "specific_topic_to_reference": get_reference_topic(source_key, cluster),
                    "priority": priority,
                    "reason": get_recommendation_reason(source_key, cluster, status),
                })

    # ── Step 3: Build Coverage Summary ───────────────────────────────────
    print("\n[3/5] Building coverage summary...")

    total_posts = len(posts)
    coverage_rows = []
    for source_key, source_info in TRUSTED_SOURCES.items():
        sc = source_coverage[source_key]
        posts_with_links = sc["linked"]
        posts_with_mentions = sc["mentioned"]
        posts_missing = sc["absent"]
        coverage_pct = round(((posts_with_links + posts_with_mentions) / total_posts) * 100, 1) if total_posts > 0 else 0
        priority_clusters = ", ".join(sorted(sc["clusters"])) if sc["clusters"] else "(none)"

        coverage_rows.append({
            "source_name": source_info["name"],
            "domain": source_info["domains"][0],
            "posts_with_links": posts_with_links,
            "posts_with_mentions": posts_with_mentions,
            "posts_missing": posts_missing,
            "coverage_pct": coverage_pct,
            "priority_clusters": priority_clusters,
        })

    # ── Step 4: Write CSVs ───────────────────────────────────────────────
    print("\n[4/5] Writing output CSVs...")

    # Reference Audit CSV
    audit_path = os.path.join(OUTPUT_DIR, "Reference_Audit.csv")
    audit_fields = [
        "post_id", "title", "cluster",
        "rspca_status", "battersea_status", "cats_protection_status",
        "blue_cross_status", "pdsa_status", "bva_status",
        "fediaf_status", "defra_status", "uk_gov_status",
        "kennel_club_status", "pfma_status",
        "total_linked", "total_mentioned", "total_missing",
        "reference_score",
    ]
    with open(audit_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=audit_fields)
        writer.writeheader()
        writer.writerows(audit_rows)
    print(f"  Written: {audit_path} ({len(audit_rows)} rows)")

    # Reference Enrichment Plan CSV
    enrichment_path = os.path.join(OUTPUT_DIR, "Reference_Enrichment_Plan.csv")
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    enrichment_rows.sort(key=lambda r: (priority_order.get(r["priority"], 3), r["cluster"], r["source_to_add"]))

    enrichment_fields = [
        "post_id", "title", "cluster", "source_to_add",
        "reference_type_recommended", "specific_topic_to_reference",
        "priority", "reason",
    ]
    with open(enrichment_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=enrichment_fields)
        writer.writeheader()
        writer.writerows(enrichment_rows)
    print(f"  Written: {enrichment_path} ({len(enrichment_rows)} rows)")

    # Reference Coverage Summary CSV
    coverage_path = os.path.join(OUTPUT_DIR, "Reference_Coverage_Summary.csv")
    coverage_fields = [
        "source_name", "domain", "posts_with_links", "posts_with_mentions",
        "posts_missing", "coverage_pct", "priority_clusters",
    ]
    with open(coverage_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=coverage_fields)
        writer.writeheader()
        writer.writerows(coverage_rows)
    print(f"  Written: {coverage_path} ({len(coverage_rows)} rows)")

    # ── Step 5: Print Summary Report ─────────────────────────────────────
    print("\n" + "=" * 74)
    print("REFERENCE ENRICHMENT REPORT")
    print("=" * 74)

    print(f"\nPosts analysed: {total_posts}")
    print(f"Enrichment recommendations: {len(enrichment_rows)}")

    # Overall reference density
    all_scores = [r["reference_score"] for r in audit_rows]
    total_all_linked = sum(r["total_linked"] for r in audit_rows)
    total_all_mentioned = sum(r["total_mentioned"] for r in audit_rows)
    total_all_missing = sum(r["total_missing"] for r in audit_rows)
    avg_linked_per_post = total_all_linked / total_posts if total_posts > 0 else 0
    avg_mentioned_per_post = total_all_mentioned / total_posts if total_posts > 0 else 0
    posts_with_zero_refs = sum(1 for r in audit_rows if r["total_linked"] == 0 and r["total_mentioned"] == 0)

    print(f"\n--- Overall Reference Density ---")
    print(f"  Total linked references:    {total_all_linked} across all posts")
    print(f"  Total text mentions:        {total_all_mentioned} across all posts")
    print(f"  Avg linked per post:        {avg_linked_per_post:.2f}")
    print(f"  Avg mentions per post:      {avg_mentioned_per_post:.2f}")
    print(f"  Posts with ZERO references: {posts_with_zero_refs}/{total_posts} ({posts_with_zero_refs/total_posts*100:.1f}%)")

    if all_scores:
        print(f"\n--- Reference Score Distribution ---")
        print(f"  Average score:    {sum(all_scores)/len(all_scores):.1f}")
        print(f"  Median score:     {sorted(all_scores)[len(all_scores)//2]}")
        print(f"  Score 0 (none):   {sum(1 for s in all_scores if s == 0)}")
        print(f"  Score 1-20:       {sum(1 for s in all_scores if 1 <= s <= 20)}")
        print(f"  Score 21-40:      {sum(1 for s in all_scores if 21 <= s <= 40)}")
        print(f"  Score 41-60:      {sum(1 for s in all_scores if 41 <= s <= 60)}")
        print(f"  Score 61-80:      {sum(1 for s in all_scores if 61 <= s <= 80)}")
        print(f"  Score 81-100:     {sum(1 for s in all_scores if 81 <= s <= 100)}")

    # Per-source coverage
    print(f"\n--- Per-Source Coverage ---")
    print(f"  {'Source':<22} {'Linked':>7} {'Mention':>8} {'Missing':>8} {'Coverage':>9}")
    print(f"  {'-'*22} {'-'*7} {'-'*8} {'-'*8} {'-'*9}")
    for row in sorted(coverage_rows, key=lambda r: -r["coverage_pct"]):
        print(f"  {row['source_name']:<22} {row['posts_with_links']:>7} {row['posts_with_mentions']:>8} "
              f"{row['posts_missing']:>8} {row['coverage_pct']:>8.1f}%")

    # Per-cluster breakdown
    print(f"\n--- Per-Cluster Reference Breakdown ---")
    cluster_stats = defaultdict(lambda: {"count": 0, "scores": [], "linked": 0, "mentioned": 0})
    for row in audit_rows:
        c = row["cluster"]
        cluster_stats[c]["count"] += 1
        cluster_stats[c]["scores"].append(row["reference_score"])
        cluster_stats[c]["linked"] += row["total_linked"]
        cluster_stats[c]["mentioned"] += row["total_mentioned"]

    print(f"  {'Cluster':<18} {'Posts':>5} {'AvgScore':>9} {'TotLinked':>10} {'TotMentioned':>13} {'AvgLinked/Post':>15}")
    print(f"  {'-'*18} {'-'*5} {'-'*9} {'-'*10} {'-'*13} {'-'*15}")
    for cluster, stats in sorted(cluster_stats.items(), key=lambda x: -sum(x[1]["scores"])/max(len(x[1]["scores"]),1)):
        avg_score = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
        avg_linked = stats["linked"] / stats["count"] if stats["count"] > 0 else 0
        print(f"  {cluster:<18} {stats['count']:>5} {avg_score:>9.1f} {stats['linked']:>10} "
              f"{stats['mentioned']:>13} {avg_linked:>15.2f}")

    # Top recommended additions (HIGH priority)
    print(f"\n--- Top 20 HIGH Priority Enrichment Recommendations ---")
    high_recs = [r for r in enrichment_rows if r["priority"] == "HIGH"]
    for rec in high_recs[:20]:
        print(f"  Post {rec['post_id']:>5}: +{rec['source_to_add']:<20} [{rec['cluster']}]")
        print(f"           Topic: {rec['specific_topic_to_reference']}")

    # Enrichment priority breakdown
    print(f"\n--- Enrichment Priority Breakdown ---")
    priority_counts = defaultdict(int)
    for row in enrichment_rows:
        priority_counts[row["priority"]] += 1
    for p in ["HIGH", "MEDIUM", "LOW"]:
        print(f"  {p:8s}  {priority_counts.get(p, 0):5d} recommendations")

    # Posts with worst reference scores
    print(f"\n--- Top 10 Posts Needing Reference Work ---")
    worst = sorted(audit_rows, key=lambda r: r["reference_score"])[:10]
    for row in worst:
        print(f"  [Score {row['reference_score']:>3}] (ID {row['post_id']}) {row['title'][:55]}")
        print(f"            Linked: {row['total_linked']} | Mentioned: {row['total_mentioned']} | Missing: {row['total_missing']} | Cluster: {row['cluster']}")

    # Posts with best reference scores
    print(f"\n--- Top 5 Best-Referenced Posts ---")
    best = sorted(audit_rows, key=lambda r: -r["reference_score"])[:5]
    for row in best:
        print(f"  [Score {row['reference_score']:>3}] (ID {row['post_id']}) {row['title'][:55]}")
        print(f"            Linked: {row['total_linked']} | Mentioned: {row['total_mentioned']} | Cluster: {row['cluster']}")

    # Sources with zero coverage
    zero_sources = [r for r in coverage_rows if r["posts_with_links"] == 0 and r["posts_with_mentions"] == 0]
    if zero_sources:
        print(f"\n--- Sources With ZERO Coverage ---")
        for row in zero_sources:
            print(f"  {row['source_name']} ({row['domain']}) — not found in any post")

    print("\n" + "=" * 74)
    print("Analysis complete. CSVs written to:")
    print(f"  {audit_path}")
    print(f"  {enrichment_path}")
    print(f"  {coverage_path}")
    print("=" * 74)


if __name__ == "__main__":
    main()
