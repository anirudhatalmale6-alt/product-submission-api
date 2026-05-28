#!/usr/bin/env python3
"""
10AD-C: Operational Usefulness Engine
pethubonline.com — 144 published posts

Analyzes and scores every published post for real-world educational usefulness
across 10 dimensions: measurable steps, practical routines, scenario walkthroughs,
troubleshooting pathways, checklists, what-to-avoid, when-to-seek-help,
real-world examples, safety checks, and beginner guidance.
"""

import csv
import html
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict

# ─── WordPress API config ───────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ad_data"

# ─── Fetch helpers ───────────────────────────────────────────────────────────
def wp_get(endpoint):
    """Fetch from WP REST API using curl subprocess."""
    url = f"{WP_API}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  [WARN] curl error for {url}: {result.stderr[:200]}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [WARN] JSON decode error for {url}: {result.stdout[:200]}")
        return None


def fetch_all_posts():
    """Paginate through all published posts."""
    all_posts = []
    page = 1
    while True:
        print(f"  Fetching posts page {page}...")
        data = wp_get(f"posts?status=publish&per_page=100&page={page}&context=edit")
        if not data or not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        if len(data) < 100:
            break
        page += 1
    print(f"  Total posts fetched: {len(all_posts)}")
    return all_posts


# ─── HTML stripping ─────────────────────────────────────────────────────────
def strip_html(raw_html):
    """Remove HTML tags and decode entities to plain text."""
    if not raw_html:
        return ""
    text = re.sub(r'<[^>]+>', ' ', raw_html)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_content(post):
    """Extract rendered content from post, trying multiple fields."""
    content = ""
    if isinstance(post.get("content"), dict):
        content = post["content"].get("rendered", "") or post["content"].get("raw", "")
    elif isinstance(post.get("content"), str):
        content = post["content"]
    return content


def get_title(post):
    """Extract title string from post."""
    if isinstance(post.get("title"), dict):
        return strip_html(post["title"].get("rendered", ""))
    return strip_html(str(post.get("title", "")))


# ─── Cluster classification ─────────────────────────────────────────────────
CLUSTER_RULES = [
    # Order matters — first match wins; more specific before general
    ("Dog Toys", [
        r"dog\s+toy", r"\btug\b", r"\bfetch\b", r"chew\s+toy",
        r"enrichment.*dog", r"mental\s+stimulation.*dog",
        r"dog.*enrichment", r"dog.*mental\s+stimulation"
    ]),
    ("Dog Food", [
        r"dog\s+food", r"puppy\s+food", r"dry\s+food", r"dry\s+vs\s+wet"
    ]),
    ("Dog Beds", [r"dog\s+bed"]),
    ("Dog Harnesses", [r"\bharness"]),
    ("Dog Health", [
        r"\bflea\b", r"joint\s+supplement", r"dental\s+care", r"dog\s+health"
    ]),
    ("Dog Care", [
        r"\bgrooming\b", r"seasonal\s+dog", r"first[- ]time\s+dog",
        r"dental\s+health", r"measure\s+your\s+dog"
    ]),
    ("Cat Toys", [r"cat\s+toy", r"cat\s+play"]),
    ("Puppy Care", [r"\bpuppy\b", r"\bsocialisation\b", r"\bsocialization\b"]),
    ("Dog Supplies", [
        r"\bcollar\b", r"\blead\b", r"\bbowl\b", r"training\s+treat",
        r"interactive\s+dog", r"\bindestructible\b"
    ]),
    ("Cat Supplies", [r"\bcat\s"]),
    ("Pet Care General", [
        r"\bpet\s", r"multi[- ]pet", r"first\s+aid", r"seasonal\s+pet"
    ]),
    ("Educational", [
        r"\bterminology\b", r"\bglossary\b", r"\bexplained\b",
        r"\benrichment\b", r"\bbehaviour\b", r"\bbehavior\b"
    ]),
]


def classify_cluster(title):
    """Classify a post into a cluster based on title keywords."""
    t = title.lower()
    for cluster_name, patterns in CLUSTER_RULES:
        for pat in patterns:
            if re.search(pat, t):
                return cluster_name
    return "Uncategorized"


# ─── Usefulness dimension scoring ────────────────────────────────────────────
def count_pattern_hits(text, patterns, case_insensitive=True):
    """Count total regex matches across a list of patterns."""
    flags = re.IGNORECASE if case_insensitive else 0
    total = 0
    for pat in patterns:
        total += len(re.findall(pat, text, flags))
    return total


def score_from_hits(hits, low=1, mid=4, high=8):
    """Convert raw hit count to 0-100 score with sigmoid-like curve."""
    if hits == 0:
        return 0
    if hits >= high:
        return min(100, 70 + int(30 * min(hits / (high * 2), 1.0)))
    if hits >= mid:
        return 40 + int(30 * (hits - mid) / (high - mid))
    if hits >= low:
        return 10 + int(30 * (hits - low) / (mid - low))
    return 5


def score_measurable_steps(raw_html, plain_text):
    """Score for ordered lists, numbered instructions, step-by-step content."""
    # Count <ol> items
    ol_items = len(re.findall(r'<li[^>]*>', raw_html)) if '<ol' in raw_html.lower() else 0
    # Count numbered patterns in text: "Step 1", "1.", "1)", "First,"
    numbered = len(re.findall(
        r'(?:step\s+\d|^\s*\d{1,2}[\.\)]\s|\bfirst(?:ly)?\b|\bsecond(?:ly)?\b|\bthird(?:ly)?\b'
        r'|\bnext\b.*\bthen\b|\bfinally\b)',
        plain_text, re.IGNORECASE | re.MULTILINE
    ))
    # Count <ol> tags themselves
    ol_tags = len(re.findall(r'<ol', raw_html, re.IGNORECASE))
    step_phrases = len(re.findall(
        r'step[- ]by[- ]step|how\s+to|instructions?|procedure|follow\s+these',
        plain_text, re.IGNORECASE
    ))
    hits = ol_items // 2 + numbered + ol_tags * 2 + step_phrases * 2
    return score_from_hits(hits, low=1, mid=5, high=12)


def score_practical_routines(plain_text):
    """Score for daily/weekly/routine/schedule patterns."""
    patterns = [
        r'\bdaily\b', r'\bweekly\b', r'\bmonthly\b', r'\broutine\b',
        r'\bschedule\b', r'\bregular(?:ly)?\b', r'\bevery\s+(?:day|week|month|morning|evening)',
        r'\beach\s+(?:day|week|month)', r'\bconsistent(?:ly)?\b',
        r'\bhabit\b', r'\brepeat\b', r'\bfrequen(?:cy|t|tly)\b'
    ]
    hits = count_pattern_hits(plain_text, patterns)
    return score_from_hits(hits, low=1, mid=4, high=9)


def score_scenario_walkthroughs(plain_text):
    """Score for scenario-based guidance."""
    patterns = [
        r'if\s+your\s+(?:dog|cat|pet|puppy|kitten)',
        r'when\s+your\s+(?:dog|cat|pet|puppy|kitten)',
        r'in\s+case\s+of', r'what\s+to\s+do\s+(?:when|if)',
        r'imagine\s+(?:your|a)', r'suppose\s+(?:your|a)',
        r'(?:for|with)\s+(?:a\s+)?(?:nervous|anxious|aggressive|shy|senior|young)\s+(?:dog|cat|pet)',
        r'scenario', r'situation\s+where',
        r'if\s+(?:he|she|it|they)\s+(?:refuse|won\'t|doesn\'t|does not|isn\'t)',
    ]
    hits = count_pattern_hits(plain_text, patterns)
    return score_from_hits(hits, low=1, mid=3, high=7)


def score_troubleshooting(plain_text):
    """Score for troubleshooting pathways."""
    patterns = [
        r'\bif\b.*\bthen\b', r'not\s+working', r'common\s+(?:problem|issue|mistake)',
        r'\bsolution\b', r'\bfix\b', r'\btroubleshoot', r'\bproblem\b',
        r'what\s+(?:to\s+do\s+)?if.*(?:doesn\'t|won\'t|refuse|fail)',
        r'\bwon\'t\s+(?:eat|drink|play|sleep|stop)',
        r'\brefuse[sd]?\b', r'not\s+(?:eating|drinking|playing|sleeping)',
        r'\bcause[sd]?\b.*\bby\b',
    ]
    hits = count_pattern_hits(plain_text, patterns)
    return score_from_hits(hits, low=1, mid=3, high=7)


def score_checklists(raw_html, plain_text):
    """Score for checklist patterns."""
    # Checkbox characters and HTML patterns
    checkbox_chars = len(re.findall(r'[✓✅☑☐□▢]', plain_text))
    checklist_words = len(re.findall(
        r'\bchecklist\b|\bcheck\s+list\b|\bbuyer\'?s?\s+guide\b|\bshopping\s+list\b'
        r'|\bwhat\s+to\s+look\s+for\b|\bthings\s+to\s+(?:check|consider|look)\b'
        r'|\bkey\s+(?:features?|factors?|considerations?)\b',
        plain_text, re.IGNORECASE
    ))
    # <ul> with many items could be checklist-like
    ul_blocks = re.findall(r'<ul[^>]*>(.*?)</ul>', raw_html, re.IGNORECASE | re.DOTALL)
    long_lists = sum(1 for block in ul_blocks if block.count('<li') >= 4)
    hits = checkbox_chars + checklist_words * 2 + long_lists
    return score_from_hits(hits, low=1, mid=3, high=7)


def score_what_to_avoid(plain_text):
    """Score for avoidance/warning content."""
    patterns = [
        r'\bavoid\b', r'\bnever\b', r'\bdon\'t\b', r'\bdo\s+not\b',
        r'\bmistake\b', r'\bwarning\b', r'\bdanger(?:ous)?\b', r'\brisk\b',
        r'\bharmful\b', r'\btoxic\b', r'\bunsafe\b',
        r'\bsteer\s+clear\b', r'\bstay\s+away\b',
        r'\bcommon\s+(?:error|mistake|pitfall)',
        r'\bwatch\s+out\b', r'\bbe\s+(?:careful|cautious|wary)\b',
    ]
    hits = count_pattern_hits(plain_text, patterns)
    return score_from_hits(hits, low=1, mid=4, high=10)


def score_when_to_seek_help(plain_text):
    """Score for professional help / vet referral content."""
    patterns = [
        r'\bvet(?:erinarian)?\b', r'\bprofessional\b',
        r'\bconsult\b', r'\bseek\s+help\b', r'\bemergency\b',
        r'\burgent(?:ly)?\b', r'\bmedical\s+(?:attention|advice|help)',
        r'\bsee\s+(?:a\s+)?(?:vet|doctor|specialist)',
        r'\btake\s+(?:them|your\s+(?:dog|cat|pet))\s+to\b',
        r'\bimmediate(?:ly)?\b.*\b(?:vet|help|attention)',
        r'\bpoisoning\b', r'\bcall\s+(?:your\s+)?(?:vet|emergency)',
    ]
    hits = count_pattern_hits(plain_text, patterns)
    return score_from_hits(hits, low=1, mid=3, high=7)


def score_real_world_examples(plain_text):
    """Score for practical real-world examples."""
    patterns = [
        r'\bfor\s+example\b', r'\bsuch\s+as\b', r'\blike\s+a\b',
        r'\bfor\s+instance\b', r'\be\.g\.\b', r'\bspecifically\b',
        r'\bin\s+practice\b', r'\bin\s+real\s+life\b',
        r'\bwe\s+(?:tested|tried|used|recommend)\b',
        r'\bour\s+(?:pick|choice|recommendation|favorite)\b',
        r'\bpersonal(?:ly)?\b',
    ]
    # Also count specific brand/product mentions (common pet brands)
    brand_patterns = [
        r'\bKong\b', r'\bNylabone\b', r'\bPurina\b', r'\bRoyal\s+Canin\b',
        r'\bOrijen\b', r'\bBlue\s+Buffalo\b', r'\bHills?\b', r'\bIAMS\b',
        r'\bPedigree\b', r'\bWhiskas\b', r'\bFrontline\b',
        r'\bAmazon\b', r'\bPetSafe\b', r'\bFurHaven\b',
    ]
    hits = count_pattern_hits(plain_text, patterns)
    brand_hits = count_pattern_hits(plain_text, brand_patterns, case_insensitive=False)
    total = hits + brand_hits
    return score_from_hits(total, low=1, mid=4, high=10)


def score_safety_checks(plain_text):
    """Score for safety-related content."""
    patterns = [
        r'\bsafety\b', r'\bsafe\b', r'\bunsafe\b', r'\bhazard(?:ous)?\b',
        r'\btoxic\b', r'\bchoking\b', r'\bsupervise\b', r'\bsupervision\b',
        r'\bswallow\b', r'\bingest\b', r'\bpoisonous\b',
        r'\bnon[- ]toxic\b', r'\bBPA[- ]free\b',
        r'\bchild[- ](?:proof|safe)\b', r'\bpet[- ](?:proof|safe)\b',
        r'\bprotect(?:ion)?\b.*(?:from|against)',
        r'\bsafe(?:ty)?\s+(?:tip|precaution|measure|check|first)',
    ]
    hits = count_pattern_hits(plain_text, patterns)
    return score_from_hits(hits, low=1, mid=3, high=8)


def score_beginner_guidance(plain_text):
    """Score for beginner/new-owner content."""
    patterns = [
        r'\bbeginner\b', r'\bfirst[- ]time\b', r'\bnew\s+(?:owner|pet\s+owner|parent)',
        r'\bgetting\s+started\b', r'\bbasics?\b', r'\bintroduction\b',
        r'\bultimate\s+guide\b', r'\bcomplete\s+guide\b',
        r'\beverything\s+you\s+need\b', r'\bwhat\s+you\s+need\s+to\s+know\b',
        r'\bguide\s+(?:to|for)\b', r'\btips?\s+for\s+(?:new|first)',
        r'\bstart(?:ing)?\s+(?:with|out)\b',
        r'\bessential\b', r'\bmust[- ](?:have|know)\b',
    ]
    hits = count_pattern_hits(plain_text, patterns)
    return score_from_hits(hits, low=1, mid=3, high=7)


def compute_overall(scores):
    """Weighted average of all dimensions."""
    weights = {
        'measurable_steps': 1.5,
        'practical_routines': 1.2,
        'scenario_walkthroughs': 1.3,
        'troubleshooting': 1.3,
        'checklists': 1.0,
        'what_to_avoid': 1.2,
        'when_to_seek_help': 1.1,
        'real_world_examples': 1.2,
        'safety_checks': 1.0,
        'beginner_guidance': 1.0,
    }
    total_w = sum(weights.values())
    weighted_sum = sum(scores[k] * weights[k] for k in weights)
    return round(weighted_sum / total_w, 1)


# ─── Dimension labels ───────────────────────────────────────────────────────
DIMENSIONS = [
    'measurable_steps', 'practical_routines', 'scenario_walkthroughs',
    'troubleshooting', 'checklists', 'what_to_avoid', 'when_to_seek_help',
    'real_world_examples', 'safety_checks', 'beginner_guidance'
]

DIMENSION_LABELS = {
    'measurable_steps': 'Measurable Steps',
    'practical_routines': 'Practical Routines',
    'scenario_walkthroughs': 'Scenario Walkthroughs',
    'troubleshooting': 'Troubleshooting',
    'checklists': 'Checklists',
    'what_to_avoid': 'What to Avoid',
    'when_to_seek_help': 'When to Seek Help',
    'real_world_examples': 'Real-World Examples',
    'safety_checks': 'Safety Checks',
    'beginner_guidance': 'Beginner Guidance',
}


# ─── Main analysis ───────────────────────────────────────────────────────────
def analyze_post(post):
    """Analyze a single post and return all scores."""
    title = get_title(post)
    raw_html = get_content(post)
    plain = strip_html(raw_html)
    cluster = classify_cluster(title)

    scores = {
        'measurable_steps': score_measurable_steps(raw_html, plain),
        'practical_routines': score_practical_routines(plain),
        'scenario_walkthroughs': score_scenario_walkthroughs(plain),
        'troubleshooting': score_troubleshooting(plain),
        'checklists': score_checklists(raw_html, plain),
        'what_to_avoid': score_what_to_avoid(plain),
        'when_to_seek_help': score_when_to_seek_help(plain),
        'real_world_examples': score_real_world_examples(plain),
        'safety_checks': score_safety_checks(plain),
        'beginner_guidance': score_beginner_guidance(plain),
    }
    overall = compute_overall(scores)

    return {
        'post_id': post.get('id', 0),
        'title': title,
        'cluster': cluster,
        'scores': scores,
        'overall': overall,
    }


def build_improvement_plan(results):
    """For each post, identify weakest dimension and suggest action."""
    plan = []
    for r in results:
        scores = r['scores']
        # Find weakest dimension
        weakest = min(DIMENSIONS, key=lambda d: scores[d])
        weakest_score = scores[weakest]

        # Priority based on overall score and weakest dimension
        if r['overall'] < 25:
            priority = "HIGH"
        elif r['overall'] < 45:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        # If weakest is already decent, lower priority
        if weakest_score >= 40:
            priority = "LOW"

        # Suggested action per dimension
        actions = {
            'measurable_steps': "Add numbered step-by-step instructions or ordered lists for key procedures",
            'practical_routines': "Include daily/weekly routine schedules or regular care patterns",
            'scenario_walkthroughs': "Add 'if your pet does X' scenarios with guided responses",
            'troubleshooting': "Add a troubleshooting section with common problems and solutions",
            'checklists': "Add a buyer's checklist or key-features-to-check list",
            'what_to_avoid': "Add a 'Common Mistakes to Avoid' or 'Warning' section",
            'when_to_seek_help': "Add guidance on when to consult a vet or professional",
            'real_world_examples': "Include specific product examples, brand names, or real-life scenarios",
            'safety_checks': "Add safety precautions, supervision tips, or toxicity warnings",
            'beginner_guidance': "Add a 'Getting Started' or 'For New Owners' section",
        }

        plan.append({
            'post_id': r['post_id'],
            'title': r['title'],
            'cluster': r['cluster'],
            'weakest_dimension': DIMENSION_LABELS.get(weakest, weakest),
            'current_score': weakest_score,
            'suggested_action': actions.get(weakest, "Review and enhance this dimension"),
            'priority': priority,
        })
    return plan


def build_cluster_summary(results):
    """Aggregate usefulness data per cluster."""
    clusters = defaultdict(list)
    for r in results:
        clusters[r['cluster']].append(r)

    summary = []
    for cluster_name, posts in sorted(clusters.items()):
        n = len(posts)
        avg_overall = round(sum(p['overall'] for p in posts) / n, 1)

        # Average per dimension
        dim_avgs = {}
        for d in DIMENSIONS:
            dim_avgs[d] = round(sum(p['scores'][d] for p in posts) / n, 1)

        strongest = max(DIMENSIONS, key=lambda d: dim_avgs[d])
        weakest = min(DIMENSIONS, key=lambda d: dim_avgs[d])

        # Growth potential: how much could actionable guidance improve
        # (gap between current avg and 80 target for troubleshooting and steps)
        actionable_gap = max(0, 80 - dim_avgs.get('measurable_steps', 0))
        actionable_growth = round((actionable_gap / 80) * 100, 1) if actionable_gap > 0 else 0.0

        troubleshooting_gap = max(0, 80 - dim_avgs.get('troubleshooting', 0))
        troubleshooting_growth = round((troubleshooting_gap / 80) * 100, 1) if troubleshooting_gap > 0 else 0.0

        summary.append({
            'cluster': cluster_name,
            'post_count': n,
            'avg_usefulness': avg_overall,
            'strongest_dimension': DIMENSION_LABELS.get(strongest, strongest),
            'weakest_dimension': DIMENSION_LABELS.get(weakest, weakest),
            'actionable_guidance_growth_pct': actionable_growth,
            'troubleshooting_growth_pct': troubleshooting_growth,
        })

    return summary


def write_scores_csv(results, path):
    """Write Operational_Usefulness_Scores.csv."""
    fieldnames = [
        'post_id', 'title', 'cluster',
        'measurable_steps', 'practical_routines', 'scenario_walkthroughs',
        'troubleshooting', 'checklists', 'what_to_avoid', 'when_to_seek_help',
        'real_world_examples', 'safety_checks', 'beginner_guidance',
        'overall_usefulness_score'
    ]
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {
                'post_id': r['post_id'],
                'title': r['title'],
                'cluster': r['cluster'],
                'overall_usefulness_score': r['overall'],
            }
            row.update(r['scores'])
            writer.writerow(row)
    print(f"  Wrote {path} ({len(results)} rows)")


def write_improvement_csv(plan, path):
    """Write Usefulness_Improvement_Plan.csv."""
    fieldnames = [
        'post_id', 'title', 'cluster', 'weakest_dimension',
        'current_score', 'suggested_action', 'priority'
    ]
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in plan:
            writer.writerow(row)
    print(f"  Wrote {path} ({len(plan)} rows)")


def write_cluster_csv(summary, path):
    """Write Cluster_Usefulness_Summary.csv."""
    fieldnames = [
        'cluster', 'post_count', 'avg_usefulness',
        'strongest_dimension', 'weakest_dimension',
        'actionable_guidance_growth_pct', 'troubleshooting_growth_pct'
    ]
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary:
            writer.writerow(row)
    print(f"  Wrote {path} ({len(summary)} rows)")


def print_summary_report(results, cluster_summary):
    """Print comprehensive summary report."""
    print("\n" + "=" * 80)
    print("  10AD-C: OPERATIONAL USEFULNESS ENGINE — SUMMARY REPORT")
    print("  pethubonline.com | {} published posts analyzed".format(len(results)))
    print("=" * 80)

    # Overall average
    avg_overall = round(sum(r['overall'] for r in results) / len(results), 1) if results else 0
    print(f"\n  OVERALL AVERAGE USEFULNESS SCORE: {avg_overall}/100")

    # Dimension-level averages
    print("\n  ── DIMENSION-LEVEL AVERAGES ──")
    dim_avgs = {}
    for d in DIMENSIONS:
        avg = round(sum(r['scores'][d] for r in results) / len(results), 1) if results else 0
        dim_avgs[d] = avg

    sorted_dims = sorted(DIMENSIONS, key=lambda d: dim_avgs[d], reverse=True)
    for d in sorted_dims:
        bar_len = int(dim_avgs[d] / 2.5)
        bar = "#" * bar_len
        label = DIMENSION_LABELS[d]
        print(f"    {label:<25s} {dim_avgs[d]:>5.1f}  {bar}")

    # Identify strengths and weaknesses
    strongest_dim = sorted_dims[0]
    weakest_dim = sorted_dims[-1]
    print(f"\n    Strongest: {DIMENSION_LABELS[strongest_dim]} ({dim_avgs[strongest_dim]})")
    print(f"    Weakest:  {DIMENSION_LABELS[weakest_dim]} ({dim_avgs[weakest_dim]})")

    # Per-cluster averages
    print("\n  ── PER-CLUSTER AVERAGES ──")
    sorted_clusters = sorted(cluster_summary, key=lambda c: c['avg_usefulness'], reverse=True)
    for c in sorted_clusters:
        bar_len = int(c['avg_usefulness'] / 2.5)
        bar = "#" * bar_len
        print(f"    {c['cluster']:<22s} ({c['post_count']:>3d} posts)  avg={c['avg_usefulness']:>5.1f}  {bar}")
        print(f"      strongest: {c['strongest_dimension']}, weakest: {c['weakest_dimension']}")

    # Top 10 most useful
    sorted_results = sorted(results, key=lambda r: r['overall'], reverse=True)
    print("\n  ── TOP 10 MOST USEFUL POSTS ──")
    for i, r in enumerate(sorted_results[:10], 1):
        print(f"    {i:>2}. [{r['overall']:>5.1f}] (ID {r['post_id']}) {r['title'][:65]}")
        top_dims = sorted(DIMENSIONS, key=lambda d: r['scores'][d], reverse=True)[:3]
        top_labels = [f"{DIMENSION_LABELS[d]}={r['scores'][d]}" for d in top_dims]
        print(f"        Top: {', '.join(top_labels)}")

    # Bottom 10 least useful
    print("\n  ── BOTTOM 10 LEAST USEFUL POSTS ──")
    for i, r in enumerate(sorted_results[-10:], 1):
        rank = len(sorted_results) - 10 + i
        print(f"    {rank:>3}. [{r['overall']:>5.1f}] (ID {r['post_id']}) {r['title'][:65]}")
        bot_dims = sorted(DIMENSIONS, key=lambda d: r['scores'][d])[:3]
        bot_labels = [f"{DIMENSION_LABELS[d]}={r['scores'][d]}" for d in bot_dims]
        print(f"         Weak: {', '.join(bot_labels)}")

    # Priority distribution
    print("\n  ── IMPROVEMENT PRIORITY DISTRIBUTION ──")
    priority_counts = defaultdict(int)
    for r in results:
        scores = r['scores']
        weakest = min(DIMENSIONS, key=lambda d: scores[d])
        if r['overall'] < 25:
            priority_counts["HIGH"] += 1
        elif r['overall'] < 45:
            priority_counts["MEDIUM"] += 1
        else:
            priority_counts["LOW"] += 1

    for p in ["HIGH", "MEDIUM", "LOW"]:
        cnt = priority_counts.get(p, 0)
        pct = round(100 * cnt / len(results), 1) if results else 0
        print(f"    {p:<8s}: {cnt:>3d} posts ({pct}%)")

    print("\n" + "=" * 80)
    print("  CSVs written to: {}".format(OUT_DIR))
    print("=" * 80 + "\n")


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("  10AD-C: Operational Usefulness Engine")
    print("  pethubonline.com — scoring all published posts")
    print("=" * 70)

    # Step 1: Fetch all posts
    print("\n[1/5] Fetching published posts from WordPress API...")
    posts = fetch_all_posts()
    if not posts:
        print("  ERROR: No posts fetched. Aborting.")
        sys.exit(1)

    # Step 2: Analyze each post
    print(f"\n[2/5] Analyzing {len(posts)} posts across 10 usefulness dimensions...")
    results = []
    for i, post in enumerate(posts, 1):
        r = analyze_post(post)
        results.append(r)
        if i % 20 == 0 or i == len(posts):
            print(f"  Analyzed {i}/{len(posts)} posts...")

    # Step 3: Build improvement plan
    print("\n[3/5] Building improvement plan...")
    improvement_plan = build_improvement_plan(results)

    # Step 4: Build cluster summary
    print("\n[4/5] Building cluster usefulness summary...")
    cluster_summary = build_cluster_summary(results)

    # Step 5: Write CSVs
    print("\n[5/5] Writing output CSVs...")
    write_scores_csv(results, os.path.join(OUT_DIR, "Operational_Usefulness_Scores.csv"))
    write_improvement_csv(improvement_plan, os.path.join(OUT_DIR, "Usefulness_Improvement_Plan.csv"))
    write_cluster_csv(cluster_summary, os.path.join(OUT_DIR, "Cluster_Usefulness_Summary.csv"))

    # Summary report
    print_summary_report(results, cluster_summary)


if __name__ == "__main__":
    main()
