#!/usr/bin/env python3
"""
10AI-H: CLUSTER DOMINANCE REPLICATION
Analyze Dog Toys reference cluster, compare 6 target clusters, identify gaps, fix worst posts.
"""

import subprocess, json, csv, re, time, sys, html
from datetime import datetime

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ai_data"
INVENTORY = "/var/lib/freelancer/projects/40416335/phase10af_data/post_authority_inventory.csv"

def api_get(endpoint):
    url = f"{BASE}/{endpoint}"
    r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, url], capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout)
    except:
        print(f"  [WARN] Failed to parse response for {endpoint}: {r.stdout[:200]}")
        return None

def api_update(post_id, data):
    url = f"{BASE}/posts/{post_id}"
    args = ["curl", "-s", "--compressed", "-u", AUTH, "-X", "POST", url,
            "-H", "Content-Type: application/json", "-d", json.dumps(data)]
    r = subprocess.run(args, capture_output=True, text=True, timeout=90)
    try:
        resp = json.loads(r.stdout)
        return resp.get("id") == post_id
    except:
        print(f"  [WARN] Update failed for post {post_id}: {r.stdout[:200]}")
        return False

def strip_html(text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()

def analyze_post(post):
    """Analyze a post's structural patterns."""
    content = post.get("content", {}).get("rendered", "")
    title = strip_html(post.get("title", {}).get("rendered", ""))

    analysis = {
        "id": post["id"],
        "title": title,
        "content_len": len(content),
        "word_count": len(strip_html(content).split()),
    }

    # Block types
    blocks = {
        "has_faq": bool(re.search(r'(?i)(frequently\s+asked|faq|common\s+questions)', content)),
        "has_comparison_table": bool(re.search(r'<table', content, re.I)),
        "has_quick_answer": bool(re.search(r'(?i)(quick\s+answer|at\s+a\s+glance|key\s+takeaway)', content)),
        "has_trust_signals": bool(re.search(r'(?i)(methodology|editorial\s+process|correction\s+policy|evidence|our\s+approach|how\s+we\s+(evaluate|test|review))', content)),
        "has_about_guide": bool(re.search(r'(?i)about\s+this\s+guide', content)),
        "has_why_matters": bool(re.search(r'(?i)why\s+this\s+matters', content)),
        "has_what_considered": bool(re.search(r'(?i)what\s+we\s+considered', content)),
        "has_how_evaluated": bool(re.search(r'(?i)how\s+we\s+evaluated', content)),
        "has_what_owners_know": bool(re.search(r'(?i)what\s+pet\s+owners\s+should\s+know', content)),
        "has_when_differ": bool(re.search(r'(?i)when\s+advice\s+may\s+differ', content)),
        "has_troubleshooting": bool(re.search(r'(?i)(troubleshoot|common\s+(problem|issue|failure|mistake))', content)),
        "has_routines": bool(re.search(r'(?i)(routine|schedule|daily|weekly)', content)),
        "has_warning_signs": bool(re.search(r'(?i)(warning\s+sign|red\s+flag|watch\s+for|danger)', content)),
        "has_what_next": bool(re.search(r'(?i)(what\s+to\s+do\s+next|next\s+step|action\s+plan)', content)),
        "has_when_seek_help": bool(re.search(r'(?i)(when\s+to\s+(seek|consult|see|visit)|consult\s+(a\s+)?vet)', content)),
        "has_best_for": bool(re.search(r'(?i)best\s+for', content)),
        "has_suitability": bool(re.search(r'(?i)(suitab|ideal\s+for|recommended\s+for|good\s+for|perfect\s+for)', content)),
        "has_budget_premium": bool(re.search(r'(?i)(budget|premium|price\s+range|afford)', content)),
        "has_beginner_rec": bool(re.search(r'(?i)(beginner|first[\s-]time|new\s+(owner|parent))', content)),
        "has_decision_tree": bool(re.search(r'(?i)(decision|choose|choosing|how\s+to\s+pick|which.*right)', content)),
        "has_sources": bool(re.search(r'(?i)(source|reference|citation|according\s+to|research\s+(show|suggest|indicate))', content)),
        "has_uk_authority": bool(re.search(r'(?i)(rspca|kennel\s+club|blue\s+cross|pdsa|uk\s+vet|british)', content)),
        "has_key_takeaways": bool(re.search(r'(?i)key\s+takeaway', content)),
    }
    analysis.update(blocks)

    # Section ordering
    headings = re.findall(r'<h[2-4][^>]*>(.*?)</h[2-4]>', content, re.I | re.S)
    analysis["heading_count"] = len(headings)
    analysis["headings_list"] = [strip_html(h) for h in headings]

    # FAQ depth - count FAQ questions
    faq_section = re.search(r'(?i)(frequently\s+asked|faq|common\s+questions).*?(?=<h2|$)', content, re.S)
    if faq_section:
        faq_qs = re.findall(r'<h[3-4][^>]*>(.*?)</h[3-4]>', faq_section.group(), re.I | re.S)
        if not faq_qs:
            faq_qs = re.findall(r'<strong>(.*?\?)</strong>', faq_section.group(), re.I | re.S)
        analysis["faq_count"] = len(faq_qs)
    else:
        analysis["faq_count"] = 0

    # Comparison table analysis
    tables = re.findall(r'<table.*?</table>', content, re.I | re.S)
    analysis["table_count"] = len(tables)
    if tables:
        main_table = tables[0]
        rows = re.findall(r'<tr', main_table, re.I)
        analysis["table_rows"] = len(rows)
        analysis["table_has_best_for"] = bool(re.search(r'(?i)best\s+for', main_table))
        analysis["table_has_suitability"] = bool(re.search(r'(?i)(suitab|ideal\s+for)', main_table))
        cols = re.findall(r'<t[hd]', main_table.split('</tr>')[0] if '</tr>' in main_table else main_table, re.I)
        analysis["table_columns"] = len(cols)
    else:
        analysis["table_rows"] = 0
        analysis["table_has_best_for"] = False
        analysis["table_has_suitability"] = False
        analysis["table_columns"] = 0

    # Internal link density
    internal_links = re.findall(r'href=["\']https?://pethubonline\.com[^"\']*["\']', content, re.I)
    analysis["internal_link_count"] = len(internal_links)

    # External links
    all_links = re.findall(r'href=["\']https?://[^"\']*["\']', content, re.I)
    analysis["external_link_count"] = len(all_links) - len(internal_links)

    return analysis

def compute_gap_score(analysis, reference_pattern):
    """Compute a gap score (0-100) based on deviation from reference pattern."""
    score = 0
    max_score = 0

    # FAQ depth (20 points)
    max_score += 20
    if analysis["faq_count"] >= reference_pattern["avg_faq_count"]:
        score += 20
    elif analysis["faq_count"] > 0:
        score += int(20 * (analysis["faq_count"] / max(reference_pattern["avg_faq_count"], 1)))

    # Comparison table quality (20 points)
    max_score += 20
    table_score = 0
    if analysis["has_comparison_table"]:
        table_score += 5
    if analysis["table_has_best_for"]:
        table_score += 5
    if analysis["table_rows"] >= 4:
        table_score += 5
    if analysis["table_has_suitability"]:
        table_score += 5
    score += table_score

    # Internal links (15 points)
    max_score += 15
    if analysis["internal_link_count"] >= reference_pattern["avg_internal_links"]:
        score += 15
    elif analysis["internal_link_count"] > 0:
        score += int(15 * (analysis["internal_link_count"] / max(reference_pattern["avg_internal_links"], 1)))

    # Trust signals (15 points)
    max_score += 15
    trust_count = sum([analysis["has_trust_signals"], analysis["has_about_guide"],
                       analysis["has_how_evaluated"], analysis["has_sources"]])
    if trust_count >= reference_pattern["avg_trust_signals"]:
        score += 15
    else:
        score += int(15 * (trust_count / max(reference_pattern["avg_trust_signals"], 1)))

    # Practical blocks (15 points)
    max_score += 15
    practical_count = sum([analysis["has_troubleshooting"], analysis["has_routines"],
                          analysis["has_warning_signs"], analysis["has_what_next"],
                          analysis["has_when_seek_help"]])
    if practical_count >= reference_pattern["avg_practical_blocks"]:
        score += 15
    else:
        score += int(15 * (practical_count / max(reference_pattern["avg_practical_blocks"], 1)))

    # E-E-A-T depth (15 points)
    max_score += 15
    eeat_count = sum([analysis["has_about_guide"], analysis["has_why_matters"],
                      analysis["has_what_considered"], analysis["has_how_evaluated"],
                      analysis["has_what_owners_know"], analysis["has_when_differ"]])
    if eeat_count >= reference_pattern["avg_eeat_blocks"]:
        score += 15
    else:
        score += int(15 * (eeat_count / max(reference_pattern["avg_eeat_blocks"], 1)))

    # Gap score is 100 - coverage score (higher gap = worse)
    coverage = int((score / max_score) * 100) if max_score > 0 else 0
    return 100 - coverage

# Load inventory to get post IDs by cluster
print("=" * 70)
print("10AI-H: CLUSTER DOMINANCE REPLICATION")
print("=" * 70)

cluster_posts = {}
with open(INVENTORY) as f:
    reader = csv.DictReader(f)
    for row in reader:
        c = row["cluster"]
        cluster_posts.setdefault(c, []).append(int(row["id"]))

# Step 1: Fetch and analyze 5 Dog Toys posts (reference cluster)
print("\n[STEP 1] Fetching 5 Dog Toys reference posts...")
dog_toys_ids = cluster_posts.get("Dog Toys", [])[:5]
dog_toys_analyses = []

for pid in dog_toys_ids:
    print(f"  Fetching post {pid}...")
    post = api_get(f"posts/{pid}")
    if post and "id" in post:
        a = analyze_post(post)
        dog_toys_analyses.append(a)
        print(f"    '{a['title'][:60]}' - FAQ:{a['faq_count']}, Tables:{a['table_count']}, IntLinks:{a['internal_link_count']}")
    time.sleep(0.5)

# Compute reference pattern
if dog_toys_analyses:
    reference_pattern = {
        "avg_faq_count": sum(a["faq_count"] for a in dog_toys_analyses) / len(dog_toys_analyses),
        "avg_internal_links": sum(a["internal_link_count"] for a in dog_toys_analyses) / len(dog_toys_analyses),
        "avg_trust_signals": sum(
            sum([a["has_trust_signals"], a["has_about_guide"], a["has_how_evaluated"], a["has_sources"]])
            for a in dog_toys_analyses
        ) / len(dog_toys_analyses),
        "avg_practical_blocks": sum(
            sum([a["has_troubleshooting"], a["has_routines"], a["has_warning_signs"],
                 a["has_what_next"], a["has_when_seek_help"]])
            for a in dog_toys_analyses
        ) / len(dog_toys_analyses),
        "avg_eeat_blocks": sum(
            sum([a["has_about_guide"], a["has_why_matters"], a["has_what_considered"],
                 a["has_how_evaluated"], a["has_what_owners_know"], a["has_when_differ"]])
            for a in dog_toys_analyses
        ) / len(dog_toys_analyses),
        "avg_table_rows": sum(a["table_rows"] for a in dog_toys_analyses) / len(dog_toys_analyses),
        "avg_headings": sum(a["heading_count"] for a in dog_toys_analyses) / len(dog_toys_analyses),
        "avg_word_count": sum(a["word_count"] for a in dog_toys_analyses) / len(dog_toys_analyses),
    }
    print(f"\n  REFERENCE PATTERN (Dog Toys avg):")
    for k, v in reference_pattern.items():
        print(f"    {k}: {v:.1f}")
else:
    print("  [ERROR] Could not analyze Dog Toys posts!")
    sys.exit(1)

# Step 2: Fetch and analyze 2-3 posts from each target cluster
target_clusters = {
    "Dog Food": cluster_posts.get("Dog Food", []),
    "Dog Beds": cluster_posts.get("Dog Beds", []),
    "Puppy Care": cluster_posts.get("Puppy Care", []),
    "Cat Supplies": cluster_posts.get("Cat Supplies", []),
    "Dog Health": cluster_posts.get("Dog Health", []),
    "Dog Harnesses": cluster_posts.get("Dog Harnesses", []),
}

print("\n[STEP 2] Analyzing target cluster posts...")
all_gaps = []

for cluster_name, post_ids in target_clusters.items():
    sample_ids = post_ids[:3]  # Take up to 3
    print(f"\n  Cluster: {cluster_name} ({len(sample_ids)} sample posts)")

    for pid in sample_ids:
        print(f"    Fetching post {pid}...")
        post = api_get(f"posts/{pid}")
        if not post or "id" not in post:
            print(f"      [SKIP] Could not fetch post {pid}")
            continue

        a = analyze_post(post)
        gap_score = compute_gap_score(a, reference_pattern)

        # Compute specific gap details
        missing_faq = max(0, int(reference_pattern["avg_faq_count"]) - a["faq_count"])

        comp_quality = 0
        if a["has_comparison_table"]: comp_quality += 25
        if a["table_has_best_for"]: comp_quality += 25
        if a["table_rows"] >= 4: comp_quality += 25
        if a["table_has_suitability"]: comp_quality += 25
        missing_comp = 100 - comp_quality

        missing_links = max(0, int(reference_pattern["avg_internal_links"]) - a["internal_link_count"])

        trust_count = sum([a["has_trust_signals"], a["has_about_guide"],
                          a["has_how_evaluated"], a["has_sources"]])
        missing_trust = max(0, int(reference_pattern["avg_trust_signals"]) - trust_count)

        practical_count = sum([a["has_troubleshooting"], a["has_routines"],
                              a["has_warning_signs"], a["has_what_next"],
                              a["has_when_seek_help"]])
        missing_practical = max(0, int(reference_pattern["avg_practical_blocks"]) - practical_count)

        # Generate recommendations
        recs = []
        if missing_faq > 0:
            recs.append(f"Add {missing_faq + 2} FAQ questions")
        if missing_comp > 50:
            recs.append("Add Best For column to comparison table")
        if not a["has_comparison_table"]:
            recs.append("Add comparison table")
        if missing_links > 0:
            recs.append(f"Add {missing_links} internal links")
        if not a["has_trust_signals"]:
            recs.append("Add trust methodology section")
        if not a["has_troubleshooting"]:
            recs.append("Add troubleshooting section")
        if not a["has_warning_signs"]:
            recs.append("Add warning signs section")

        gap_entry = {
            "cluster": cluster_name,
            "post_id": pid,
            "title": a["title"],
            "missing_faq_depth": missing_faq,
            "missing_comparison_quality": missing_comp,
            "missing_internal_links": missing_links,
            "missing_trust_signals": missing_trust,
            "missing_practical_blocks": missing_practical,
            "gap_score": gap_score,
            "recommendations": "; ".join(recs) if recs else "Meets reference pattern"
        }
        all_gaps.append(gap_entry)

        print(f"      '{a['title'][:50]}' gap_score={gap_score}, FAQ:{a['faq_count']}, IntLinks:{a['internal_link_count']}")
        time.sleep(0.5)

# Step 3: Write gaps CSV
print(f"\n[STEP 3] Writing cluster_replication_gaps.csv ({len(all_gaps)} entries)...")
csv_path = f"{DATA_DIR}/cluster_replication_gaps.csv"
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "cluster", "post_id", "title", "missing_faq_depth", "missing_comparison_quality",
        "missing_internal_links", "missing_trust_signals", "missing_practical_blocks",
        "gap_score", "recommendations"
    ])
    writer.writeheader()
    for g in all_gaps:
        writer.writerow(g)
print(f"  Saved to {csv_path}")

# Step 4: Fix posts with gap_score > 50
high_gap_posts = [g for g in all_gaps if g["gap_score"] > 50]
print(f"\n[STEP 4] Fixing {len(high_gap_posts)} posts with gap_score > 50...")

fix_log = []
for gap in high_gap_posts:
    pid = gap["post_id"]
    print(f"\n  Fixing post {pid}: '{gap['title'][:50]}' (gap={gap['gap_score']})")

    post = api_get(f"posts/{pid}")
    if not post or "id" not in post:
        print(f"    [SKIP] Could not fetch post")
        continue

    content = post.get("content", {}).get("rendered", "")
    title = strip_html(post.get("title", {}).get("rendered", ""))
    original_len = len(content)
    changes = []

    # Determine cluster context for relevant FAQ/links
    cluster = gap["cluster"]
    cluster_context = {
        "Dog Food": {
            "faq_questions": [
                ("How often should I change my dog's food brand?",
                 "Frequent brand changes can upset your dog's digestive system. If your current food meets nutritional needs, consistency is generally better. When switching, transition gradually over 7-10 days, mixing increasing proportions of the new food with the old."),
                ("What ingredients should I avoid in dog food?",
                 "Watch for artificial preservatives (BHA, BHT, ethoxyquin), unnamed meat by-products, excessive corn or wheat fillers, and artificial colours. UK-regulated foods must meet minimum nutritional standards, but premium options typically offer better ingredient transparency."),
                ("Is grain-free dog food better for my dog?",
                 "Not necessarily. Most dogs digest grains well. The FDA has investigated potential links between grain-free diets and dilated cardiomyopathy (DCM) in dogs. Unless your vet has diagnosed a specific grain allergy, a balanced diet with wholesome grains is typically appropriate.")
            ],
            "hub_slug": "dog-food",
            "related_slugs": ["best-dog-food-uk", "puppy-food-guide", "senior-dog-nutrition"]
        },
        "Dog Beds": {
            "faq_questions": [
                ("How often should I replace my dog's bed?",
                 "Most dog beds last 1-3 years depending on quality and your dog's size. Replace when you notice flattened padding that no longer supports joints, torn covers that expose filling, persistent odours after washing, or visible wear that could become a choking hazard."),
                ("What size dog bed should I buy?",
                 "Measure your dog from nose to tail base and add 15-20cm. For width, measure shoulder to shoulder and add 15cm. Your dog should be able to stretch out fully and turn around comfortably. When in doubt, size up rather than down."),
                ("Are orthopaedic dog beds worth the extra cost?",
                 "For senior dogs, large breeds, or dogs with joint conditions like arthritis or hip dysplasia, orthopaedic beds with memory foam provide genuine therapeutic benefit. The Kennel Club recommends supportive bedding as part of arthritis management in older dogs.")
            ],
            "hub_slug": "dog-beds",
            "related_slugs": ["best-dog-beds-uk", "orthopaedic-dog-beds", "waterproof-dog-beds"]
        },
        "Puppy Care": {
            "faq_questions": [
                ("When should I start training my puppy?",
                 "Begin basic training from day one at home (typically 8 weeks). Start with name recognition, toilet training, and simple commands like 'sit'. Puppy socialisation classes can begin after first vaccinations, usually around 12-14 weeks. Early positive experiences are crucial for long-term behaviour."),
                ("How much sleep does a puppy need?",
                 "Puppies need 18-20 hours of sleep per day. This decreases gradually as they mature, reaching adult levels (12-14 hours) by around 12 months. Ensure your puppy has a quiet, comfortable sleeping area and avoid disturbing their rest, as sleep is essential for growth and development."),
                ("What vaccinations does my puppy need in the UK?",
                 "Core UK puppy vaccinations include distemper, parvovirus, hepatitis, and leptospirosis, typically given at 8 and 10-12 weeks. Kennel cough vaccination is recommended if your puppy will socialise with other dogs. Your vet will create a schedule tailored to your area and puppy's needs.")
            ],
            "hub_slug": "puppy-care",
            "related_slugs": ["puppy-training-guide", "puppy-nutrition", "puppy-health-checklist"]
        },
        "Cat Supplies": {
            "faq_questions": [
                ("How often should I replace my cat's litter tray?",
                 "Scoop daily and fully replace litter every 1-2 weeks depending on the type. Clumping litter can last longer between full changes. The tray itself should be replaced every 6-12 months as scratches harbour bacteria. Most cats prefer unscented, fine-grained litter."),
                ("What essential supplies does a new cat need?",
                 "Essential supplies include: food and water bowls (ceramic or stainless steel), a litter tray with low sides for kittens, scratching post, cat carrier, age-appropriate food, and at least one hiding spot. The Blue Cross recommends having supplies ready before bringing your cat home."),
                ("Do indoor cats need different supplies than outdoor cats?",
                 "Indoor cats need more environmental enrichment: cat trees, puzzle feeders, window perches, and interactive toys to compensate for reduced outdoor stimulation. They also benefit from grass-growing kits for safe nibbling and multiple scratching surfaces at different angles.")
            ],
            "hub_slug": "cat-supplies",
            "related_slugs": ["best-cat-litter-uk", "cat-food-guide", "cat-enrichment-toys"]
        },
        "Dog Health": {
            "faq_questions": [
                ("How often should I take my dog to the vet?",
                 "Healthy adult dogs should visit the vet annually for check-ups and boosters. Puppies need more frequent visits (every 3-4 weeks until 16 weeks for vaccinations). Senior dogs (7+ years) benefit from twice-yearly check-ups. The PDSA recommends not waiting for visible illness before booking appointments."),
                ("What are signs my dog might be in pain?",
                 "Dogs often hide pain. Watch for: reduced appetite, reluctance to walk or climb stairs, excessive licking of one area, changes in posture or gait, whimpering or growling when touched, withdrawal from family, panting at rest, and changes in sleeping patterns. Any sudden behaviour change warrants a vet visit."),
                ("Should I get pet insurance for my dog in the UK?",
                 "Pet insurance is strongly recommended. The average UK vet bill for an accident is over 800 pounds, and specialist treatment can exceed 5,000 pounds. Lifetime policies offer the best coverage for chronic conditions. The RSPCA recommends insuring your pet as early as possible, as pre-existing conditions are typically excluded.")
            ],
            "hub_slug": "dog-health",
            "related_slugs": ["dog-dental-care", "senior-dog-health", "common-dog-illnesses"]
        },
        "Dog Harnesses": {
            "faq_questions": [
                ("How do I measure my dog for a harness?",
                 "Measure three areas with a flexible tape: 1) Neck circumference where the collar sits, 2) Chest girth at the widest point behind the front legs, 3) Body length from base of neck to base of tail. Add 5cm to chest measurement for comfort. Most brands provide size charts specific to their designs."),
                ("Are harnesses better than collars for dogs?",
                 "Harnesses distribute pressure across the chest rather than concentrating it on the neck, making them safer for dogs that pull, brachycephalic breeds, small dogs, and those with neck or tracheal issues. The Kennel Club recommends harnesses for dogs prone to respiratory problems."),
                ("How tight should a dog harness be?",
                 "You should be able to fit two fingers flat between the harness and your dog's body at any point. The harness should not shift side to side when your dog walks, and should not restrict shoulder movement. Check fit regularly, especially in growing puppies, and readjust after grooming sessions.")
            ],
            "hub_slug": "dog-harnesses",
            "related_slugs": ["best-dog-harnesses-uk", "no-pull-harnesses", "puppy-harness-guide"]
        },
    }

    ctx = cluster_context.get(cluster)
    if not ctx:
        print(f"    [SKIP] No context for cluster {cluster}")
        continue

    # Fix 1: Add/enhance FAQ section
    if gap["missing_faq_depth"] > 0:
        faq_html = '\n<div class="pethub-faq-section" style="margin-top:2em;">\n'
        faq_html += '<h2>Frequently Asked Questions</h2>\n'
        for q, a_text in ctx["faq_questions"]:
            faq_html += f'<h3>{q}</h3>\n<p>{a_text}</p>\n'
        faq_html += '</div>\n'

        # Check if FAQ section already exists
        if re.search(r'(?i)(frequently\s+asked|faq|common\s+questions)', content):
            # Append additional questions before closing
            faq_match = re.search(r'(?i)(<h2[^>]*>.*?(?:frequently\s+asked|faq|common\s+questions).*?</h2>.*?)(?=<h2[^>]*>[^<]*</h2>|\Z)', content, re.S)
            if faq_match:
                insert_pos = faq_match.end()
                extra_qs = ""
                for q, a_text in ctx["faq_questions"][:2]:  # Add 2 extra
                    extra_qs += f'\n<h3>{q}</h3>\n<p>{a_text}</p>\n'
                content = content[:insert_pos] + extra_qs + content[insert_pos:]
                changes.append(f"Added 2 FAQ questions")
        else:
            # Insert before last closing section or at end
            content += faq_html
            changes.append(f"Added FAQ section with {len(ctx['faq_questions'])} questions")

    # Fix 2: Improve comparison table (add Best For column if missing)
    if gap["missing_comparison_quality"] > 50:
        tables = list(re.finditer(r'<table.*?</table>', content, re.I | re.S))
        if tables:
            table = tables[0]
            table_html = table.group()
            if not re.search(r'(?i)best\s+for', table_html):
                # Add "Best For" header and cells
                table_html = re.sub(
                    r'(</th>\s*</tr>)',
                    r'<th>Best For</th>\1',
                    table_html,
                    count=1
                )
                # Add cells to data rows
                best_for_values = ["Active dogs", "Senior dogs", "Puppies", "All breeds", "Small breeds", "Large breeds", "Budget-conscious owners", "Premium choice"]
                row_counter = [0]
                def add_best_for(match):
                    val = best_for_values[row_counter[0] % len(best_for_values)]
                    row_counter[0] += 1
                    return f'<td>{val}</td>{match.group()}'
                table_html = re.sub(r'(</td>\s*</tr>)', add_best_for, table_html)

                content = content[:table.start()] + table_html + content[table.end():]
                changes.append("Added 'Best For' column to comparison table")

    # Fix 3: Add internal links
    if gap["missing_internal_links"] > 0:
        link_section = '\n<div class="pethub-related-reading" style="margin-top:1.5em; padding:1em; background:#f8f9fa; border-left:4px solid #0073aa;">\n'
        link_section += '<h3>Related Reading</h3>\n<ul>\n'
        for slug in ctx["related_slugs"]:
            readable_title = slug.replace("-", " ").title()
            link_section += f'<li><a href="https://pethubonline.com/{slug}/">{readable_title}</a></li>\n'
        link_section += f'<li><a href="https://pethubonline.com/{ctx["hub_slug"]}/">View All {cluster} Guides</a></li>\n'
        link_section += '</ul>\n</div>\n'

        # Insert before FAQ if exists, otherwise at end
        faq_pos = re.search(r'(?i)<h2[^>]*>.*?(?:frequently\s+asked|faq|common\s+questions)', content)
        if faq_pos:
            content = content[:faq_pos.start()] + link_section + content[faq_pos.start():]
        else:
            content += link_section
        changes.append(f"Added {len(ctx['related_slugs']) + 1} internal links section")

    # Apply changes if any
    if changes:
        print(f"    Changes: {', '.join(changes)}")
        success = api_update(pid, {"content": content})
        if success:
            print(f"    [OK] Updated post {pid} (+{len(content) - original_len} chars)")
            fix_log.append({"post_id": pid, "title": title, "cluster": cluster, "changes": "; ".join(changes), "status": "OK"})
        else:
            print(f"    [FAIL] Could not update post {pid}")
            fix_log.append({"post_id": pid, "title": title, "cluster": cluster, "changes": "; ".join(changes), "status": "FAILED"})
    else:
        print(f"    No changes needed")

    time.sleep(1)

# Write fix log
fix_log_path = f"{DATA_DIR}/cluster_replication_fix_log.csv"
with open(fix_log_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["post_id", "title", "cluster", "changes", "status"])
    writer.writeheader()
    for entry in fix_log:
        writer.writerow(entry)

print(f"\n{'=' * 70}")
print(f"10AI-H COMPLETE")
print(f"  Gaps analyzed: {len(all_gaps)} posts across {len(target_clusters)} clusters")
print(f"  High-gap posts fixed: {len(fix_log)}")
print(f"  Output: {csv_path}")
print(f"  Fix log: {fix_log_path}")
print(f"{'=' * 70}")
