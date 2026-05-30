#!/usr/bin/env python3
"""
Phase 11AD - Search Opportunity Execution Planning
===================================================
Analyzes focus clusters (Indoor Cats, Pet Care, Dog Supplies, Cat Toys)
to identify content gaps, AI-answer opportunities, long-tail queries,
and UK-specific opportunities.

Reads existing posts from Query_Ownership_Matrix.csv and post content
from WordPress API to understand current coverage, then identifies gaps.

Output: Search_Opportunity_Plan.csv
"""

import csv
import json
import os
import re
import subprocess
import time
import html

WORK_DIR = "/var/lib/freelancer/projects/40416335/phase11w_data"
QUERY_CSV = os.path.join(WORK_DIR, "Query_Ownership_Matrix.csv")
CITATION_CSV = os.path.join(WORK_DIR, "AI_Citation_Observation.csv")
VISIBILITY_CSV = os.path.join(WORK_DIR, "Visibility_Readiness_Posts.csv")
SNIPPET_CSV = os.path.join(WORK_DIR, "Featured_Snippet_Readiness.csv")
OUTPUT_CSV = os.path.join(WORK_DIR, "Search_Opportunity_Plan.csv")

WP_URL = "https://pethubonline.com/wp-json/wp/v2/posts"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"

FOCUS_CLUSTERS = ["Indoor Cats", "Pet Care", "Dog Supplies", "Cat Toys"]


def strip_html(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def fetch_post(post_id):
    """Fetch a single post from WordPress API."""
    time.sleep(2)
    url = f"{WP_URL}/{post_id}"
    result = subprocess.run(
        ["curl", "-s", "-u", f"{WP_USER}:{WP_PASS}", url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        return data if "id" in data else None
    except json.JSONDecodeError:
        return None


def load_cluster_posts():
    """Load existing posts and queries for focus clusters."""
    cluster_data = {c: [] for c in FOCUS_CLUSTERS}
    with open(QUERY_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cluster = row.get('cluster', '')
            if cluster in FOCUS_CLUSTERS:
                cluster_data[cluster].append(row)
    return cluster_data


def load_visibility_data():
    """Load visibility readiness scores per post."""
    data = {}
    with open(VISIBILITY_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row['post_id']] = row
    return data


def load_snippet_data():
    """Load snippet readiness per post."""
    data = {}
    with open(SNIPPET_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row['post_id']] = row
    return data


def load_citation_data():
    """Load citation scores per post."""
    data = {}
    with open(CITATION_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row['post_id']] = row
    return data


def extract_covered_topics(posts):
    """Extract topic themes from existing posts."""
    topics = set()
    for post in posts:
        title = post.get('title', '').lower()
        # Extract key themes
        for keyword in ['toy', 'food', 'bed', 'health', 'safety', 'exercise',
                         'behaviour', 'diet', 'nutrition', 'grooming', 'training',
                         'enrichment', 'harness', 'collar', 'lead', 'bowl',
                         'water', 'treat', 'chew', 'puzzle', 'interactive',
                         'indestructible', 'indoor', 'outdoor', 'puppy', 'senior',
                         'kitten', 'cleaning', 'hygiene', 'socialisation',
                         'first aid', 'hydration', 'teething', 'faq']:
            if keyword in title:
                topics.add(keyword)
    return topics


def identify_indoor_cats_gaps(posts, vis_data, snippet_data, cit_data):
    """Identify opportunities for Indoor Cats cluster."""
    opportunities = []
    covered = extract_covered_topics(posts)
    existing_titles = [p['title'].lower() for p in posts]

    # Current coverage: exercise, safety, enrichment, behaviour, diet/nutrition
    # = 5 posts

    # Educational content gaps
    educational_gaps = [
        ("indoor cat litter training guide uk", "litter", "No comprehensive litter box guide for indoor-only cats; high search volume topic"),
        ("best cat trees for indoor cats uk 2026", "cat tree", "Vertical space is critical for indoor cats; product-focused gap with buying intent"),
        ("indoor cat mental health and wellbeing", "mental health", "Stress and anxiety in house cats is underserved; strong AI-citation potential"),
        ("how to transition outdoor cat to indoor uk", "transition", "Common UK concern with rescue cats; high editorial value"),
        ("indoor cat window perch and catio guide uk", "catio", "Catios are trending in UK; combines safety + enrichment topics"),
        ("indoor cat health risks vs outdoor cats uk", "health risks", "Comparative health data creates unique reference content"),
        ("indoor cat breed guide uk: best breeds for flats", "breeds", "Breed-specific indoor content has low competition and high intent"),
        ("multi-cat indoor household management guide", "multi-cat", "Managing multiple indoor cats is distinct from general multi-pet content"),
    ]

    for query, topic, rationale in educational_gaps:
        if topic not in covered:
            opportunities.append({
                'cluster': 'Indoor Cats',
                'opportunity_type': 'educational',
                'topic': f"Indoor cat {topic} guide",
                'target_query': query,
                'difficulty_estimate': 'low',
                'priority': 1,
                'rationale': rationale
            })

    # AI-answer opportunities
    ai_gaps = [
        ("how long can an indoor cat be left alone", "Indoor cat alone time limits", "Direct factual answer AI models seek; currently no concise answer in cluster"),
        ("do indoor cats need vaccinations uk", "Indoor cat vaccination requirements UK", "UK-specific factual query with definitive answer; high AI-citation fit"),
        ("how much space does an indoor cat need", "Indoor cat space requirements", "Quantifiable answer (sq ft/metres) ideal for AI extraction"),
        ("indoor cat lifespan vs outdoor cat uk", "Indoor vs outdoor cat lifespan comparison", "Statistical comparison AI models frequently cite; unique data point"),
        ("why does my indoor cat meow at the door", "Indoor cat door meowing behaviour", "Behavioural query with structured answer format; high search volume"),
    ]

    for query, topic, rationale in ai_gaps:
        opportunities.append({
            'cluster': 'Indoor Cats',
            'opportunity_type': 'ai_answer',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'low',
            'priority': 1,
            'rationale': rationale
        })

    # UK-specific opportunities
    uk_gaps = [
        ("uk indoor cat regulations and microchipping law 2026", "UK cat law compliance", "Compulsory microchipping law (2024) + indoor cat implications; authoritative reference"),
        ("rspca indoor cat welfare guidelines uk", "RSPCA indoor cat standards", "Citing official UK welfare body creates authority; few competitors cover this"),
        ("indoor cat insurance uk comparison 2026", "UK indoor cat insurance", "UK-specific pricing and provider comparison; high commercial intent"),
    ]

    for query, topic, rationale in uk_gaps:
        opportunities.append({
            'cluster': 'Indoor Cats',
            'opportunity_type': 'uk_specific',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'medium',
            'priority': 2,
            'rationale': rationale
        })

    # Long-tail / low competition
    longtail_gaps = [
        ("best air purifier for homes with indoor cats uk", "Air purifiers for cat owners", "Niche crossover query; almost no competition in pet niche"),
        ("indoor cat weight chart by breed uk", "Indoor cat weight reference chart", "Data-table format ideal for snippets; low competition"),
        ("how to stop indoor cat scratching sofa uk", "Indoor cat furniture protection", "Specific problem-solution format; long-tail with intent"),
        ("indoor cat toy rotation schedule weekly", "Weekly toy rotation plan", "Actionable schedule content; complementary to existing enrichment post"),
    ]

    for query, topic, rationale in longtail_gaps:
        opportunities.append({
            'cluster': 'Indoor Cats',
            'opportunity_type': 'low_competition',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'low',
            'priority': 2,
            'rationale': rationale
        })

    return opportunities


def identify_pet_care_gaps(posts, vis_data, snippet_data, cit_data):
    """Identify opportunities for Pet Care cluster (only 2 posts currently)."""
    opportunities = []

    # Massive gap: only 2 posts (seasonal safety + multi-pet household)
    # This cluster needs foundational content

    educational_gaps = [
        ("new pet owner checklist uk 2026", "New pet owner essentials", "Foundational guide missing; high search volume and AI-citation potential", 1),
        ("pet care cost calculator uk 2026", "UK pet ownership costs", "Interactive/data-heavy content with UK pricing; unique value proposition", 1),
        ("how to choose between a cat and a dog uk", "Cat vs dog decision guide", "High-volume query with structured comparison format; ideal for AI", 1),
        ("pet microchipping uk law 2024 explained", "UK microchipping law guide", "Legal requirement content creates authority; high citation value", 1),
        ("senior pet care guide uk: aging dogs and cats", "Senior pet care essentials", "Growing demographic; age-specific advice with UK vet recommendations", 2),
        ("pet emergency preparedness uk guide", "Emergency pet care planning", "Underserved topic with strong editorial value", 2),
        ("adopting vs buying pets uk: what to consider", "Pet adoption guide UK", "Ethical/practical comparison content; strong editorial authority", 2),
        ("pet obesity uk statistics and prevention guide", "Pet obesity prevention", "Data-rich content with UK statistics; high AI-citation potential", 1),
        ("travelling with pets uk: car train and plane guide", "UK pet travel guide", "Comprehensive transport guide with UK-specific rules; low competition", 2),
        ("pet dental care guide uk: teeth cleaning for dogs and cats", "Pet dental health", "Cross-species dental care; underserved with high search intent", 2),
    ]

    for query, topic, rationale, priority in educational_gaps:
        opportunities.append({
            'cluster': 'Pet Care',
            'opportunity_type': 'educational',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'medium',
            'priority': priority,
            'rationale': rationale
        })

    # AI-answer opportunities
    ai_gaps = [
        ("how much does it cost to own a dog per year uk 2026", "Annual dog ownership cost UK", "Quantifiable answer with UK data; top AI-cited query format", 1),
        ("how much does it cost to own a cat per year uk 2026", "Annual cat ownership cost UK", "Companion to dog cost guide; definitive data-point content", 1),
        ("what vaccinations do pets need uk", "UK pet vaccination schedule", "Factual reference content AI models prioritise", 1),
        ("how often should i take my pet to the vet uk", "UK vet visit frequency guide", "Clear recommendation format ideal for AI answers", 2),
        ("is pet insurance worth it uk 2026", "Pet insurance value analysis UK", "Decision-support content with UK market data", 2),
    ]

    for query, topic, rationale, priority in ai_gaps:
        opportunities.append({
            'cluster': 'Pet Care',
            'opportunity_type': 'ai_answer',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'medium',
            'priority': priority,
            'rationale': rationale
        })

    # UK-specific
    uk_gaps = [
        ("uk pet ownership statistics 2026", "UK pet population data", "Statistical reference page AI models cite frequently; high authority", 1),
        ("dangerous dogs act uk 2026 guide", "UK dangerous dogs legislation", "Legal reference content; high citation value", 2),
        ("uk pet food regulations and labelling guide", "UK pet food standards", "Regulatory content with authority signals", 2),
    ]

    for query, topic, rationale, priority in uk_gaps:
        opportunities.append({
            'cluster': 'Pet Care',
            'opportunity_type': 'uk_specific',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'high',
            'priority': priority,
            'rationale': rationale
        })

    # Long-tail
    longtail_gaps = [
        ("best pet subscription boxes uk 2026", "UK pet subscription box reviews", "Commercial intent + low competition; product-comparison format", 3),
        ("pet-friendly office uk guide for employers", "Pet-friendly workplace guide", "Niche but growing topic; unique angle", 3),
        ("how to introduce a new pet to existing pets uk", "New pet introduction guide", "Specific process content complementing multi-pet post", 2),
    ]

    for query, topic, rationale, priority in longtail_gaps:
        opportunities.append({
            'cluster': 'Pet Care',
            'opportunity_type': 'low_competition',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'low',
            'priority': priority,
            'rationale': rationale
        })

    return opportunities


def identify_dog_supplies_gaps(posts, vis_data, snippet_data, cit_data):
    """Identify opportunities for Dog Supplies cluster (29 posts)."""
    opportunities = []
    covered = extract_covered_topics(posts)
    existing_titles = [p['title'].lower() for p in posts]

    # Dog Supplies is well-covered but has specific gaps

    educational_gaps = [
        ("dog coat and jacket guide uk 2026", "Dog clothing and coats UK", "Seasonal product guide missing; high UK search volume in winter", 2),
        ("best dog crates uk 2026 buying guide", "Dog crate selection guide", "No crate content despite training leads/collars coverage; natural extension", 1),
        ("dog travel accessories uk: car harness boot liner crate", "Dog travel gear UK", "Multi-product travel guide; complements water bottle guide", 2),
        ("best dog poop bags uk 2026: eco-friendly options", "Eco-friendly dog waste bags UK", "Environmental angle differentiator; low competition", 3),
        ("dog agility equipment uk: home training setup guide", "Home agility equipment UK", "Extends training category; niche with dedicated enthusiasts", 3),
        ("best dog car seat covers uk 2026", "Dog car seat protection UK", "Product guide gap; high commercial intent query", 2),
    ]

    for query, topic, rationale, priority in educational_gaps:
        opportunities.append({
            'cluster': 'Dog Supplies',
            'opportunity_type': 'educational',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'medium',
            'priority': priority,
            'rationale': rationale
        })

    # AI-answer opportunities
    ai_gaps = [
        ("how to measure a dog for a harness uk", "Dog harness measurement guide", "Step-by-step measurement content perfect for AI extraction; high volume", 1),
        ("what size dog crate do i need", "Dog crate sizing chart", "Quantifiable answer with breed-size table; top snippet format", 1),
        ("how to choose the right dog lead length", "Dog lead length selection", "Decision-tree content AI models love; complements lead guide", 2),
        ("best material for dog toys: rubber vs rope vs nylon", "Dog toy material comparison", "Comparison format ideal for structured AI answers", 2),
        ("how often should i replace dog toys", "Dog toy replacement schedule", "Factual recommendation with clear timeframes; AI-friendly format", 2),
    ]

    for query, topic, rationale, priority in ai_gaps:
        opportunities.append({
            'cluster': 'Dog Supplies',
            'opportunity_type': 'ai_answer',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'low',
            'priority': priority,
            'rationale': rationale
        })

    # UK-specific
    uk_gaps = [
        ("pets at home vs independent pet shops uk comparison", "UK pet retailer comparison", "UK-specific retail landscape content; unique data", 3),
        ("uk dog supply brands: british-made pet products", "British-made dog products guide", "Patriotic purchasing trend; unique angle with low competition", 2),
        ("amazon uk vs pets at home dog supplies price comparison", "UK dog supply price comparison", "Price data creates citeable reference; high commercial intent", 2),
    ]

    for query, topic, rationale, priority in uk_gaps:
        opportunities.append({
            'cluster': 'Dog Supplies',
            'opportunity_type': 'uk_specific',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'medium',
            'priority': priority,
            'rationale': rationale
        })

    # Long-tail
    longtail_gaps = [
        ("best dog supplies for flat living uk", "Dog supplies for apartment dogs", "Niche but growing UK urban dog ownership; low competition", 2),
        ("eco-friendly dog supplies uk 2026", "Sustainable dog products UK", "Growing sustainability demand; differentiating angle", 2),
        ("dog supplies for elderly owners uk", "Accessible dog supplies guide", "Underserved demographic; unique helpful content", 3),
        ("budget dog supplies uk under £20", "Budget dog supplies roundup", "Price-focused content; high intent and low competition", 2),
    ]

    for query, topic, rationale, priority in longtail_gaps:
        opportunities.append({
            'cluster': 'Dog Supplies',
            'opportunity_type': 'low_competition',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'low',
            'priority': priority,
            'rationale': rationale
        })

    return opportunities


def identify_cat_toys_gaps(posts, vis_data, snippet_data, cit_data):
    """Identify opportunities for Cat Toys cluster (5 posts)."""
    opportunities = []
    covered = extract_covered_topics(posts)

    # Current: FAQ, choosing by personality, rotation, enrichment beyond toys, play behaviour
    # = 5 posts

    educational_gaps = [
        ("best cat toys for kittens uk 2026", "Kitten toy guide UK", "Age-specific product guide missing; high commercial intent", 1),
        ("best cat toys for senior cats uk", "Senior cat toy guide", "Age-specific gap; growing elderly cat population", 1),
        ("automated cat toys uk 2026: self-playing options", "Automated/electronic cat toys UK", "Product category not covered; high buying intent", 1),
        ("cat puzzle feeders uk 2026: best food puzzles", "Cat puzzle feeder guide UK", "Distinct from toys; combines feeding + enrichment", 2),
        ("best cat laser toys uk: safety and recommendations", "Cat laser toy safety guide UK", "Safety-focused angle creates authority; addresses common concern", 2),
        ("diy cat toys: safe homemade options uk", "DIY cat toy ideas", "Budget-friendly content complements commercial guides", 3),
    ]

    for query, topic, rationale, priority in educational_gaps:
        opportunities.append({
            'cluster': 'Cat Toys',
            'opportunity_type': 'educational',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'low',
            'priority': priority,
            'rationale': rationale
        })

    # AI-answer opportunities
    ai_gaps = [
        ("how many toys does a cat need", "Cat toy quantity recommendation", "Quantifiable answer AI models extract; very high search volume", 1),
        ("why does my cat not play with toys", "Cat toy disinterest troubleshooting", "Problem-solution format ideal for AI; complements personality guide", 1),
        ("are catnip toys safe for kittens", "Catnip safety for kittens", "Factual yes/no + explanation; top AI answer format", 1),
        ("how long should you play with a cat each day", "Daily cat playtime recommendation", "Clear numerical answer AI models cite; high volume", 1),
        ("best type of toy for a bored cat", "Bored cat toy recommendations", "Decision-support content with structured options", 2),
    ]

    for query, topic, rationale, priority in ai_gaps:
        opportunities.append({
            'cluster': 'Cat Toys',
            'opportunity_type': 'ai_answer',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'low',
            'priority': priority,
            'rationale': rationale
        })

    # UK-specific
    uk_gaps = [
        ("uk cat toy safety standards and regulations", "UK cat toy safety standards", "Regulatory reference content; high authority and citation value", 2),
        ("where to buy cat toys uk: best shops online and in-store", "UK cat toy retailers guide", "UK-specific retail landscape; combines value with local relevance", 2),
    ]

    for query, topic, rationale, priority in uk_gaps:
        opportunities.append({
            'cluster': 'Cat Toys',
            'opportunity_type': 'uk_specific',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'medium',
            'priority': priority,
            'rationale': rationale
        })

    # Long-tail
    longtail_gaps = [
        ("best subscription cat toy boxes uk 2026", "Cat toy subscription boxes UK", "Recurring revenue angle; low competition niche", 3),
        ("cat toys for blind cats uk", "Sensory toys for blind cats", "Accessibility niche; extremely low competition", 2),
        ("best cat toys for anxious cats uk", "Anxiety-relief cat toys", "Growing awareness of feline anxiety; differentiating angle", 2),
        ("cat toy safety checklist printable uk", "Cat toy safety checklist", "Downloadable/printable format; link-worthy resource", 3),
    ]

    for query, topic, rationale, priority in longtail_gaps:
        opportunities.append({
            'cluster': 'Cat Toys',
            'opportunity_type': 'low_competition',
            'topic': topic,
            'target_query': query,
            'difficulty_estimate': 'low',
            'priority': priority,
            'rationale': rationale
        })

    return opportunities


def main():
    print("Phase 11AD - Search Opportunity Execution Planning")
    print("=" * 55)

    # Load all existing data
    print("Loading existing data...")
    cluster_data = load_cluster_posts()
    vis_data = load_visibility_data()
    snippet_data = load_snippet_data()
    cit_data = load_citation_data()

    for cluster, posts in cluster_data.items():
        print(f"  {cluster}: {len(posts)} posts")

    # Fetch a sample of posts per cluster to understand content depth
    print("\nFetching sample posts to analyze content coverage...")
    cluster_content = {}
    for cluster in FOCUS_CLUSTERS:
        posts = cluster_data[cluster]
        # Fetch up to 2 posts per cluster as samples
        sample_posts = posts[:2]
        content_samples = []
        for post in sample_posts:
            pid = post['post_id']
            print(f"  Fetching {cluster} sample: post {pid}...")
            data = fetch_post(pid)
            if data:
                content_text = strip_html(data.get('content', {}).get('rendered', ''))
                content_samples.append(content_text[:2000])  # First 2000 chars
        cluster_content[cluster] = content_samples

    # Generate opportunities for each cluster
    print("\nGenerating opportunities...")

    all_opportunities = []

    indoor_opps = identify_indoor_cats_gaps(
        cluster_data['Indoor Cats'], vis_data, snippet_data, cit_data)
    all_opportunities.extend(indoor_opps)
    print(f"  Indoor Cats: {len(indoor_opps)} opportunities")

    pet_care_opps = identify_pet_care_gaps(
        cluster_data['Pet Care'], vis_data, snippet_data, cit_data)
    all_opportunities.extend(pet_care_opps)
    print(f"  Pet Care: {len(pet_care_opps)} opportunities")

    dog_supply_opps = identify_dog_supplies_gaps(
        cluster_data['Dog Supplies'], vis_data, snippet_data, cit_data)
    all_opportunities.extend(dog_supply_opps)
    print(f"  Dog Supplies: {len(dog_supply_opps)} opportunities")

    cat_toys_opps = identify_cat_toys_gaps(
        cluster_data['Cat Toys'], vis_data, snippet_data, cit_data)
    all_opportunities.extend(cat_toys_opps)
    print(f"  Cat Toys: {len(cat_toys_opps)} opportunities")

    # Sort by priority then cluster
    all_opportunities.sort(key=lambda x: (x['priority'], x['cluster']))

    # Write output
    fieldnames = ['cluster', 'opportunity_type', 'topic', 'target_query',
                  'difficulty_estimate', 'priority', 'rationale']

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_opportunities)

    print(f"\nWrote {len(all_opportunities)} opportunities to {OUTPUT_CSV}")

    # Summary
    print(f"\nSummary by type:")
    type_counts = {}
    for o in all_opportunities:
        t = o['opportunity_type']
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")

    print(f"\nSummary by priority:")
    prio_counts = {}
    for o in all_opportunities:
        p = o['priority']
        prio_counts[p] = prio_counts.get(p, 0) + 1
    for p, c in sorted(prio_counts.items()):
        print(f"  Priority {p}: {c}")

    print(f"\nSummary by cluster:")
    cluster_counts = {}
    for o in all_opportunities:
        cl = o['cluster']
        cluster_counts[cl] = cluster_counts.get(cl, 0) + 1
    for cl, c in sorted(cluster_counts.items()):
        print(f"  {cl}: {c}")

    # Top priority items
    print(f"\nTop Priority-1 opportunities:")
    for o in all_opportunities:
        if o['priority'] == 1:
            print(f"  [{o['cluster']}] [{o['opportunity_type']}] {o['target_query']}")


if __name__ == "__main__":
    main()
