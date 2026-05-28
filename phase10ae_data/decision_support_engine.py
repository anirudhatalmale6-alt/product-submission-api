#!/usr/bin/env python3
"""
10AE-D: Decision Support Engine + Checklist Saturation
For pethubonline.com — 144 published posts WordPress pet supplies blog.

Analyzes every post for decision-support quality across 10 dimensions,
identifies missing practical guidance elements, and generates
checklist/troubleshooting templates.
"""

import subprocess
import json
import csv
import re
import os
import sys
import html
from collections import defaultdict
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ae_data"

# ── WordPress API Fetch ────────────────────────────────────────────────────
def fetch_all_posts():
    """Fetch all published posts via curl with pagination."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}/posts?status=publish&per_page=100&page={page}&context=edit"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  [WARN] curl error on page {page}: {result.stderr}")
            break
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"  [WARN] JSON decode error on page {page}")
            break
        if not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        print(f"  Fetched page {page}: {len(data)} posts (total: {len(all_posts)})")
        if len(data) < 100:
            break
        page += 1
    return all_posts


def strip_html(raw_html):
    """Remove HTML tags and decode entities."""
    if not raw_html:
        return ""
    text = re.sub(r'<[^>]+>', ' ', raw_html)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ── Cluster Detection ──────────────────────────────────────────────────────
CLUSTER_KEYWORDS = {
    "Dog Care": ["dog", "puppy", "canine", "poodle", "labrador", "retriever", "bulldog",
                  "shepherd", "terrier", "beagle", "husky", "corgi", "dachshund", "chihuahua",
                  "pitbull", "rottweiler", "dalmatian", "boxer", "collie", "spaniel", "hound"],
    "Cat Care": ["cat", "kitten", "feline", "tabby", "siamese", "persian", "bengal",
                 "ragdoll", "maine coon", "sphynx", "calico"],
    "Fish & Aquatics": ["fish", "aquarium", "tank", "betta", "goldfish", "tropical fish",
                        "reef", "coral", "aquatic", "koi", "guppy", "tetra", "cichlid"],
    "Bird Care": ["bird", "parrot", "parakeet", "cockatiel", "budgie", "avian", "canary",
                  "finch", "macaw", "cockatoo", "lovebird"],
    "Small Pets": ["hamster", "rabbit", "bunny", "guinea pig", "gerbil", "ferret", "chinchilla",
                   "hedgehog", "rat", "mouse", "small pet", "rodent"],
    "Reptile Care": ["reptile", "lizard", "snake", "gecko", "turtle", "tortoise", "iguana",
                     "chameleon", "bearded dragon", "terrarium", "vivarium"],
    "Pet Nutrition": ["food", "diet", "nutrition", "feeding", "kibble", "treats", "meal",
                      "calories", "protein", "grain-free", "raw diet", "supplement", "vitamin"],
    "Pet Health": ["health", "vet", "veterinar", "disease", "symptom", "illness", "medication",
                   "vaccine", "spay", "neuter", "parasite", "flea", "tick", "worm", "allergy",
                   "infection", "surgery", "dental"],
    "Training & Behavior": ["train", "behavior", "obedience", "trick", "command", "socialize",
                            "aggression", "anxiety", "barking", "biting", "leash", "crate",
                            "housebreak", "potty train", "clicker"],
    "Pet Products & Gear": ["product", "review", "best", "buy", "recommend", "collar", "harness",
                            "bed", "toy", "crate", "carrier", "cage", "bowl", "feeder", "brush",
                            "shampoo", "grooming", "accessory", "supplies"],
    "Pet Safety": ["safety", "poison", "toxic", "danger", "emergency", "first aid", "hazard",
                   "escape", "lost pet", "microchip", "pet-proof"],
    "Grooming": ["groom", "bath", "brush", "nail", "trim", "coat", "fur", "shed", "haircut",
                 "deshed", "matting"],
}

def detect_cluster(title, content):
    """Detect the primary topic cluster for a post."""
    combined = (title + " " + content).lower()
    scores = {}
    for cluster, keywords in CLUSTER_KEYWORDS.items():
        score = 0
        for kw in keywords:
            count = combined.count(kw.lower())
            score += count
        scores[cluster] = score
    if not scores or max(scores.values()) == 0:
        return "General Pet Care"
    return max(scores, key=scores.get)


# ── Decision Support Dimension Scoring ─────────────────────────────────────
def score_troubleshooting(text):
    """Dimension 1: Troubleshooting Quality."""
    patterns = [
        r'\bif\b.*\bthen\b', r'\bcommon\s+problem', r'\bsolution\b', r'\bnot\s+working\b',
        r'\bwhat\s+to\s+do\s+when\b', r'\btroubleshoot', r'\bfix\b', r'\bsolve\b',
        r'\bproblem\b', r'\bissue\b', r'\bwon\'?t\b', r'\bdoesn\'?t\b.*\bwork',
        r'\bhow\s+to\s+fix\b', r'\bstep\s+to\s+resolve\b', r'\bquick\s+fix\b',
        r'\bwhat\s+if\b', r'\bif\s+your\b.*\b(dog|cat|pet|fish|bird)\b',
        r'\bcause\b.*\b(of|for)\b', r'\breason\b.*\bwhy\b',
        r'\btry\b.*\binstead\b', r'\balternative\b',
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(100, int((hits / len(patterns)) * 140))


def score_measurable_guidance(text):
    """Dimension 2: Measurable Guidance."""
    patterns = [
        r'\b\d+\s*(minutes?|hours?|days?|weeks?|months?|years?)\b',
        r'\b\d+\s*(cups?|ounces?|oz|grams?|pounds?|lbs?|kg|mg|ml|liters?)\b',
        r'\b\d+\s*(times?|x)\s*(per|a|each)\s*(day|week|month)\b',
        r'\b\d+\s*[-–]\s*\d+\b',  # ranges like 2-3
        r'\b(once|twice|three\s+times)\s*(a|per|each)\s*(day|week|month)\b',
        r'\b\d+%\b', r'\b\d+\s*degrees?\b', r'\b\d+\s*(inches?|feet|cm|meters?)\b',
        r'\bevery\s+\d+\b', r'\b(at\s+least|up\s+to|no\s+more\s+than)\s+\d+\b',
        r'\b\d+\s*(calories|kcal)\b', r'\btemperature\b.*\d+',
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(100, int((hits / len(patterns)) * 130))


def score_safety_pathways(text):
    """Dimension 3: Safety Pathways."""
    patterns = [
        r'\bdanger\s+sign', r'\bwhen\s+to\s+stop\b', r'\bwarning\b', r'\bcaution\b',
        r'\bnever\b', r'\bdo\s+not\b', r'\bavoid\b', r'\bdangerous\b', r'\btoxic\b',
        r'\bpoison', r'\bharmful\b', r'\bunsafe\b', r'\brisk\b', r'\bemergency\b',
        r'\bimmediately\b.*\b(stop|call|vet|contact)\b', r'\bfatal\b',
        r'\blethal\b', r'\bsevere\b', r'\bcritical\b', r'\blife-threatening\b',
        r'\bdon\'?t\s+(ever|use|give|feed|let)\b', r'\bkeep\s+away\b',
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(100, int((hits / len(patterns)) * 130))


def score_beginner_walkthroughs(text):
    """Dimension 4: Beginner Walkthroughs."""
    patterns = [
        r'\bstep\s*\d+\b', r'\bstep[-\s]by[-\s]step\b', r'\bbeginner', r'\bfirst[-\s]?time\b',
        r'\bhow\s+to\b', r'\bguide\b', r'\btutorial\b', r'\bstart\s+by\b',
        r'\bnext\s*,?\s*(you|we)\b', r'\bfinally\b', r'\bstart\s+with\b',
        r'\b(first|second|third|fourth|fifth)\s*,\b', r'\bnew\s+(owner|pet\s+parent)\b',
        r'\b1\.\s', r'\b2\.\s', r'\b3\.\s',  # numbered steps
        r'\beasy\b', r'\bsimple\b', r'\bbasic\b',
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(100, int((hits / len(patterns)) * 130))


def score_routines(text):
    """Dimension 5: Routines (daily/weekly/monthly)."""
    patterns = [
        r'\bdaily\b', r'\bweekly\b', r'\bmonthly\b', r'\beveryday\b',
        r'\broutine\b', r'\bschedule\b', r'\bregular\b', r'\bconsistent\b',
        r'\beach\s+(morning|evening|night|day|week)\b', r'\bmaintenance\b',
        r'\bfrequen(cy|tly)\b', r'\brepeat\b', r'\bhabit\b',
        r'\b(morning|evening|night)\s+routine\b', r'\bregimen\b',
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(100, int((hits / len(patterns)) * 140))


def score_practical_schedules(text):
    """Dimension 6: Practical Schedules (age-specific, seasonal)."""
    patterns = [
        r'\b\d+\s*(week|month|year)[-\s]?old\b', r'\bpuppy\b', r'\bkitten\b',
        r'\bsenior\b', r'\badult\b', r'\bage\b', r'\bstage\b',
        r'\b(spring|summer|fall|autumn|winter)\b', r'\bseasonal\b',
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
        r'\blife\s*stage\b', r'\bgrowth\b', r'\bmaturity\b',
        r'\b(baby|juvenile|adolescent|young|old|elder)\b',
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(100, int((hits / len(patterns)) * 140))


def score_next_actions(text):
    """Dimension 7: 'What to Do Next' guidance."""
    patterns = [
        r'\bnext\s+step\b', r'\bwhat\s+to\s+do\s+next\b', r'\baction\s+plan\b',
        r'\bdecision\s+tree\b', r'\bif\s+.*\bthen\s+.*\b(do|try|call|visit)\b',
        r'\byour\s+next\s+move\b', r'\bafter\s+(that|this)\b.*\b(you|we)\b',
        r'\bfollow\s+up\b', r'\bproceed\b', r'\bcontinue\s+(with|to)\b',
        r'\bnow\s+(that|you)\b', r'\bonce\s+you\b', r'\btake\s+action\b',
        r'\bhere\'?s\s+what\b', r'\bstart\s+(by|with)\b',
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(100, int((hits / len(patterns)) * 140))


def score_seek_help(text):
    """Dimension 8: 'When to Seek Help' signals."""
    patterns = [
        r'\bcall\s+(your\s+)?vet\b', r'\bsee\s+(a\s+|your\s+)?vet\b',
        r'\bvet(erinar)?\s+visit\b', r'\bprofessional\s+help\b',
        r'\bmedical\s+attention\b', r'\bemergency\b', r'\bseek\s+help\b',
        r'\bconsult\b', r'\bspecialist\b', r'\bexpert\b',
        r'\bif\b.*\b(persists?|worsens?|continues?|doesn\'?t\s+improve)\b',
        r'\bwhen\s+to\s+(call|see|visit|contact)\b', r'\bget\s+checked\b',
        r'\bdon\'?t\s+wait\b', r'\bimmediately\b.*\bvet\b',
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(100, int((hits / len(patterns)) * 140))


def score_evaluate(text):
    """Dimension 9: 'How to Evaluate' frameworks."""
    patterns = [
        r'\bquality\b', r'\bcriteria\b', r'\bwhat\s+to\s+look\s+for\b',
        r'\bhow\s+to\s+(choose|pick|select|evaluate|compare|tell)\b',
        r'\bbest\b.*\bfor\b', r'\bcompare\b', r'\bpros?\s+and\s+cons?\b',
        r'\bfeature\b', r'\bfactor\b', r'\bconsider\b',
        r'\bcheck\s+(for|if|that|whether)\b', r'\blook\s+for\b',
        r'\bsign\s+of\s+(good|quality|healthy)\b', r'\bindicator\b',
        r'\brating\b', r'\breview\b', r'\brecommend\b',
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(100, int((hits / len(patterns)) * 130))


def score_what_to_avoid(text):
    """Dimension 10: 'What to Avoid' guidance."""
    patterns = [
        r'\bmistake\b', r'\berror\b', r'\bavoid\b', r'\bdon\'?t\b',
        r'\bnever\b', r'\bwrong\b', r'\bbad\b.*\b(for|idea|practice)\b',
        r'\bcommon\s+(mistake|error|myth|misconception)\b',
        r'\bstop\s+(doing|using|giving|feeding)\b', r'\bunsafe\b',
        r'\bharmful\b', r'\boverdo\b', r'\btoo\s+much\b',
        r'\bwaste\s+of\b', r'\bmyth\b', r'\bfalse\b.*\bbeliev',
        r'\bpitfall\b', r'\btrap\b',
    ]
    hits = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return min(100, int((hits / len(patterns)) * 130))


DIMENSION_SCORERS = [
    ("troubleshooting", score_troubleshooting),
    ("measurable_guidance", score_measurable_guidance),
    ("safety_pathways", score_safety_pathways),
    ("beginner_walkthroughs", score_beginner_walkthroughs),
    ("routines", score_routines),
    ("practical_schedules", score_practical_schedules),
    ("next_actions", score_next_actions),
    ("seek_help", score_seek_help),
    ("evaluate", score_evaluate),
    ("what_to_avoid", score_what_to_avoid),
]

DIMENSION_LABELS = {
    "troubleshooting": "Troubleshooting Quality",
    "measurable_guidance": "Measurable Guidance",
    "safety_pathways": "Safety Pathways",
    "beginner_walkthroughs": "Beginner Walkthroughs",
    "routines": "Routines",
    "practical_schedules": "Practical Schedules",
    "next_actions": "What to Do Next",
    "seek_help": "When to Seek Help",
    "evaluate": "How to Evaluate",
    "what_to_avoid": "What to Avoid",
}


def compute_decision_support(text):
    """Compute all 10 dimension scores and overall score."""
    scores = {}
    for name, scorer in DIMENSION_SCORERS:
        scores[name] = scorer(text)
    overall = sum(scores.values()) / len(scores)
    return scores, round(overall, 1)


def tier_label(overall):
    """Assign decision support tier."""
    if overall >= 70:
        return "A: Strong Decision Support"
    elif overall >= 50:
        return "B: Moderate Decision Support"
    elif overall >= 30:
        return "C: Weak Decision Support"
    else:
        return "D: Minimal Decision Support"


# ── Checklist Saturation Analysis ──────────────────────────────────────────
CHECKLIST_PATTERNS = [
    r'checklist', r'[✓✅☑]', r'^\s*[-*]\s*\[[ x]\]',  # markdown checkboxes
    r'<input\s+type=["\']checkbox',  # HTML checkboxes
]

CHECKLIST_TOPIC_SIGNALS = {
    "buying_guide": [r'\bbuy(ing)?\s+guide\b', r'\bbest\b.*\bfor\b', r'\bhow\s+to\s+choose\b',
                     r'\bshopping\b', r'\btop\s+\d+\b', r'\bpick\b.*\bright\b',
                     r'\bwhat\s+to\s+look\s+for\b', r'\bproduct\s+review\b'],
    "setup_guide": [r'\bset\s*up\b', r'\bhow\s+to\s+(set|start|install|assemble)\b',
                    r'\bgetting\s+started\b', r'\bnew\s+(owner|pet)\b',
                    r'\bfirst\s+(time|day)\b', r'\bprepare\b'],
    "safety_guide": [r'\bsafety\b', r'\bpoison\b', r'\btoxic\b', r'\bdanger\b',
                     r'\bemergency\b', r'\bfirst\s+aid\b', r'\bpet[-\s]?proof\b'],
    "care_routine": [r'\bcare\s+(routine|guide|schedule|plan)\b', r'\bdaily\s+care\b',
                     r'\bgrooming\s+(routine|guide|schedule)\b', r'\bmaintenance\b',
                     r'\bfeeding\s+(schedule|guide|plan|routine)\b'],
    "health_checklist": [r'\bhealth\s+check\b', r'\bsymptom\b', r'\bsign\b.*\bof\b',
                         r'\bwhen\s+to\s+see\b.*\bvet\b', r'\bvaccin(e|ation)\b',
                         r'\bprevent(ion|ative)\b'],
    "training_checklist": [r'\btraining\b', r'\bobedience\b', r'\bcommand\b',
                           r'\bhousebreak\b', r'\bpotty\s+train\b', r'\bsocialize\b'],
    "travel_checklist": [r'\btravel\b', r'\bflying\b.*\bpet\b', r'\broad\s+trip\b',
                         r'\bvacation\b.*\bpet\b', r'\bcarrier\b', r'\bpacking\b'],
}


def count_existing_checklists(text):
    """Count existing checklist-like elements in post content."""
    count = 0
    for p in CHECKLIST_PATTERNS:
        matches = re.findall(p, text, re.IGNORECASE | re.MULTILINE)
        count += len(matches)
    # Also count ordered list sequences (3+ consecutive numbered items with actionable verbs)
    numbered = re.findall(r'^\s*\d+[\.\)]\s+\w', text, re.MULTILINE)
    if len(numbered) >= 3:
        count += 1
    return count


def detect_checklist_need(title, text):
    """Determine if post needs a checklist and what type."""
    combined = (title + " " + text).lower()
    needs = []
    for ctype, patterns in CHECKLIST_TOPIC_SIGNALS.items():
        for p in patterns:
            if re.search(p, combined, re.IGNORECASE):
                needs.append(ctype)
                break
    return needs


def generate_checklist_template(post_title, cluster, checklist_type):
    """Generate a contextual checklist template based on post topic and type."""
    title_lower = post_title.lower()

    templates = {
        "buying_guide": [
            "[ ] Research breed/species-specific requirements",
            "[ ] Set budget range (product + ongoing costs)",
            "[ ] Compare at least 3 options/brands",
            "[ ] Check ingredient list / material quality",
            "[ ] Read verified user reviews (min 50+)",
            "[ ] Verify size/fit for your specific pet",
            "[ ] Check return policy and warranty",
            "[ ] Confirm compatibility with existing setup",
        ],
        "setup_guide": [
            "[ ] Gather all required supplies before starting",
            "[ ] Pet-proof the designated area",
            "[ ] Set up feeding station (bowl, water, food)",
            "[ ] Prepare sleeping/resting area",
            "[ ] Install safety barriers if needed",
            "[ ] Schedule first vet visit within 48 hours",
            "[ ] Introduce to household members gradually",
            "[ ] Establish immediate routine (feeding times, potty schedule)",
        ],
        "safety_guide": [
            "[ ] Identify and remove toxic plants/foods from access",
            "[ ] Secure medications and cleaning products",
            "[ ] Check for small choking hazards",
            "[ ] Verify fence/enclosure integrity",
            "[ ] Save emergency vet number in phone",
            "[ ] Prepare pet first-aid kit",
            "[ ] Know nearest 24-hour emergency vet location",
            "[ ] Review signs that require immediate vet visit",
        ],
        "care_routine": [
            "[ ] Daily: Fresh water and measured food portions",
            "[ ] Daily: Exercise/play session (minimum 20 min)",
            "[ ] Daily: Quick health visual check (eyes, ears, nose)",
            "[ ] Weekly: Brush coat / clean enclosure thoroughly",
            "[ ] Weekly: Check teeth and gums",
            "[ ] Monthly: Parasite prevention treatment",
            "[ ] Monthly: Nail trim check",
            "[ ] Quarterly: Weight check and diet adjustment",
            "[ ] Annually: Full vet checkup + vaccinations",
        ],
        "health_checklist": [
            "[ ] Monitor eating and drinking habits daily",
            "[ ] Watch for changes in energy level or behavior",
            "[ ] Check for lumps, bumps, or skin changes weekly",
            "[ ] Monitor stool consistency and frequency",
            "[ ] Track weight monthly (sudden changes = vet visit)",
            "[ ] Note any limping, stiffness, or mobility changes",
            "[ ] Check eyes for discharge, redness, cloudiness",
            "[ ] Review vaccination schedule — up to date?",
        ],
        "training_checklist": [
            "[ ] Start with one command at a time",
            "[ ] Keep training sessions under 10 minutes",
            "[ ] Use high-value treats for reinforcement",
            "[ ] Practice in low-distraction environment first",
            "[ ] Add distractions gradually as skill improves",
            "[ ] Be consistent with command words and signals",
            "[ ] End every session on a positive note",
            "[ ] Track progress weekly — note improvements and setbacks",
        ],
        "travel_checklist": [
            "[ ] Update microchip information",
            "[ ] Get health certificate from vet (if required)",
            "[ ] Pack sufficient food, water, medications",
            "[ ] Bring familiar comfort item (toy, blanket)",
            "[ ] Research pet-friendly accommodations",
            "[ ] Prepare carrier with proper ventilation",
            "[ ] Plan rest stops every 2-3 hours for walks",
            "[ ] Bring copies of vaccination records",
        ],
    }

    return templates.get(checklist_type, [
        "[ ] Review current setup against best practices",
        "[ ] Identify gaps in care or equipment",
        "[ ] Create action plan with timeline",
        "[ ] Set reminders for recurring tasks",
        "[ ] Schedule follow-up review in 30 days",
    ])


# ── Main Engine ────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("10AE-D: DECISION SUPPORT ENGINE + CHECKLIST SATURATION")
    print(f"Target: pethubonline.com | Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    # ── Fetch Posts ─────────────────────────────────────────────────────
    print("\n[1/5] Fetching all published posts...")
    posts = fetch_all_posts()
    if not posts:
        print("ERROR: No posts fetched. Exiting.")
        sys.exit(1)
    print(f"  Total posts fetched: {len(posts)}")

    # ── Process Posts ───────────────────────────────────────────────────
    print("\n[2/5] Analyzing decision support dimensions...")
    results = []
    for i, post in enumerate(posts):
        pid = post.get("id", 0)
        title_raw = post.get("title", {})
        if isinstance(title_raw, dict):
            title = strip_html(title_raw.get("rendered", title_raw.get("raw", "")))
        else:
            title = strip_html(str(title_raw))

        content_raw = post.get("content", {})
        if isinstance(content_raw, dict):
            content = strip_html(content_raw.get("rendered", content_raw.get("raw", "")))
        else:
            content = strip_html(str(content_raw))

        cluster = detect_cluster(title, content)
        dim_scores, overall = compute_decision_support(content)
        tier = tier_label(overall)

        # Checklist analysis
        existing_cl = count_existing_checklists(content)
        cl_needs = detect_checklist_need(title, content)
        needs_checklist = len(cl_needs) > 0 and existing_cl < 2

        # Find weakest dimension
        weakest_dim = min(dim_scores, key=dim_scores.get)
        weakest_score = dim_scores[weakest_dim]

        results.append({
            "post_id": pid,
            "title": title,
            "cluster": cluster,
            "dim_scores": dim_scores,
            "overall": overall,
            "tier": tier,
            "existing_checklists": existing_cl,
            "needs_checklist": needs_checklist,
            "checklist_needs": cl_needs,
            "weakest_dim": weakest_dim,
            "weakest_score": weakest_score,
            "content_length": len(content),
        })

        if (i + 1) % 25 == 0 or (i + 1) == len(posts):
            print(f"  Processed {i+1}/{len(posts)} posts...")

    # ── CSV 1: Decision Support Scores ──────────────────────────────────
    print("\n[3/5] Writing Decision_Support_Scores.csv...")
    csv1_path = os.path.join(OUTPUT_DIR, "Decision_Support_Scores.csv")
    with open(csv1_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["post_id", "title", "cluster"]
        for name, _ in DIMENSION_SCORERS:
            header.append(DIMENSION_LABELS[name])
        header.extend(["overall_decision_support", "decision_support_tier"])
        writer.writerow(header)
        for r in results:
            row = [r["post_id"], r["title"], r["cluster"]]
            for name, _ in DIMENSION_SCORERS:
                row.append(r["dim_scores"][name])
            row.extend([r["overall"], r["tier"]])
            writer.writerow(row)
    print(f"  Written: {csv1_path}")

    # ── CSV 2: Checklist Saturation Plan ────────────────────────────────
    print("\n[4/5] Writing Checklist_Saturation_Plan.csv...")
    csv2_path = os.path.join(OUTPUT_DIR, "Checklist_Saturation_Plan.csv")
    with open(csv2_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "post_id", "title", "cluster", "existing_checklists",
            "needs_checklist", "checklist_type_recommended",
            "checklist_template", "priority"
        ])
        for r in results:
            if r["checklist_needs"]:
                for ctype in r["checklist_needs"]:
                    template_items = generate_checklist_template(r["title"], r["cluster"], ctype)
                    template_str = " | ".join(template_items)
                    # Priority: high if no existing + low overall, medium if some gaps
                    if r["existing_checklists"] == 0 and r["overall"] < 40:
                        priority = "HIGH"
                    elif r["existing_checklists"] == 0:
                        priority = "MEDIUM"
                    else:
                        priority = "LOW"
                    writer.writerow([
                        r["post_id"], r["title"], r["cluster"],
                        r["existing_checklists"], "Yes",
                        ctype.replace("_", " ").title(),
                        template_str, priority
                    ])
            else:
                # Posts without identified checklist needs
                writer.writerow([
                    r["post_id"], r["title"], r["cluster"],
                    r["existing_checklists"], "No",
                    "N/A", "N/A",
                    "LOW"
                ])
    print(f"  Written: {csv2_path}")

    # ── CSV 3: Decision Support Gaps ────────────────────────────────────
    print("\n[4.5/5] Writing Decision_Support_Gaps.csv...")
    csv3_path = os.path.join(OUTPUT_DIR, "Decision_Support_Gaps.csv")

    SUGGESTED_ADDITIONS = {
        "troubleshooting": "Add 'Common Problems & Solutions' section with if/then troubleshooting pairs",
        "measurable_guidance": "Include specific numbers: dosages, timeframes, measurements, frequency",
        "safety_pathways": "Add 'Warning Signs' and 'When to Stop' safety callout boxes",
        "beginner_walkthroughs": "Add numbered step-by-step walkthrough for first-time pet owners",
        "routines": "Include daily/weekly/monthly routine schedule or maintenance calendar",
        "practical_schedules": "Add age-specific or seasonal timeline with concrete dates/milestones",
        "next_actions": "Add 'Your Next Steps' section with clear action items and decision tree",
        "seek_help": "Add 'When to Call Your Vet' section with specific trigger symptoms",
        "evaluate": "Add 'How to Choose' comparison framework with evaluation criteria",
        "what_to_avoid": "Add 'Common Mistakes to Avoid' section with specific pitfalls",
    }

    MISSING_ELEMENTS = {
        "troubleshooting": "No if/then problem-solution pairs found",
        "measurable_guidance": "Lacks specific numbers, measurements, or timeframes",
        "safety_pathways": "Missing danger signs, warnings, or safety cautions",
        "beginner_walkthroughs": "No step-by-step beginner guidance found",
        "routines": "Missing daily/weekly/monthly routine structure",
        "practical_schedules": "No age-specific or seasonal scheduling found",
        "next_actions": "Missing clear next-step or action guidance",
        "seek_help": "No professional help or vet referral triggers found",
        "evaluate": "Missing quality criteria or evaluation framework",
        "what_to_avoid": "No common mistakes or avoidance guidance found",
    }

    with open(csv3_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "post_id", "title", "cluster", "weakest_dimension",
            "missing_element", "suggested_addition", "priority"
        ])
        for r in results:
            # Report up to 3 weakest dimensions per post
            sorted_dims = sorted(r["dim_scores"].items(), key=lambda x: x[1])
            reported = 0
            for dim_name, dim_score in sorted_dims:
                if dim_score < 40 and reported < 3:
                    if r["overall"] < 30:
                        priority = "CRITICAL"
                    elif r["overall"] < 50:
                        priority = "HIGH"
                    elif dim_score == 0:
                        priority = "HIGH"
                    else:
                        priority = "MEDIUM"
                    writer.writerow([
                        r["post_id"], r["title"], r["cluster"],
                        DIMENSION_LABELS[dim_name],
                        MISSING_ELEMENTS[dim_name],
                        SUGGESTED_ADDITIONS[dim_name],
                        priority
                    ])
                    reported += 1
    print(f"  Written: {csv3_path}")

    # ── Summary Report ──────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("DECISION SUPPORT ENGINE — SUMMARY REPORT")
    print("=" * 70)

    # Overall stats
    overalls = [r["overall"] for r in results]
    avg_overall = sum(overalls) / len(overalls)
    tier_counts = defaultdict(int)
    for r in results:
        tier_counts[r["tier"]] += 1

    print(f"\n--- OVERALL DECISION SUPPORT SCORES ---")
    print(f"  Posts analyzed:          {len(results)}")
    print(f"  Average overall score:   {avg_overall:.1f}/100")
    print(f"  Highest score:           {max(overalls):.1f}")
    print(f"  Lowest score:            {min(overalls):.1f}")
    print(f"  Median score:            {sorted(overalls)[len(overalls)//2]:.1f}")

    print(f"\n--- TIER DISTRIBUTION ---")
    for tier in sorted(tier_counts.keys()):
        count = tier_counts[tier]
        pct = count / len(results) * 100
        bar = "#" * int(pct / 2)
        print(f"  {tier}: {count} posts ({pct:.1f}%) {bar}")

    # Dimension averages
    print(f"\n--- DIMENSION AVERAGES (across all posts) ---")
    dim_avgs = {}
    for name, _ in DIMENSION_SCORERS:
        vals = [r["dim_scores"][name] for r in results]
        avg = sum(vals) / len(vals)
        dim_avgs[name] = avg

    sorted_dims_global = sorted(dim_avgs.items(), key=lambda x: x[1], reverse=True)
    for name, avg in sorted_dims_global:
        bar = "#" * int(avg / 2)
        print(f"  {DIMENSION_LABELS[name]:30s} {avg:5.1f} {bar}")

    strongest = sorted_dims_global[0]
    weakest = sorted_dims_global[-1]
    print(f"\n  STRONGEST dimension: {DIMENSION_LABELS[strongest[0]]} ({strongest[1]:.1f})")
    print(f"  WEAKEST dimension:   {DIMENSION_LABELS[weakest[0]]} ({weakest[1]:.1f})")

    # Checklist coverage
    print(f"\n--- CHECKLIST SATURATION ---")
    has_checklist = sum(1 for r in results if r["existing_checklists"] > 0)
    needs_cl = sum(1 for r in results if r["needs_checklist"])
    total_existing = sum(r["existing_checklists"] for r in results)
    print(f"  Posts with existing checklists:     {has_checklist}/{len(results)} ({has_checklist/len(results)*100:.1f}%)")
    print(f"  Total checklist elements found:     {total_existing}")
    print(f"  Posts needing checklists:           {needs_cl}/{len(results)} ({needs_cl/len(results)*100:.1f}%)")

    # Checklist type breakdown
    cl_type_counts = defaultdict(int)
    for r in results:
        for ct in r["checklist_needs"]:
            cl_type_counts[ct] += 1
    if cl_type_counts:
        print(f"\n  Checklist types needed:")
        for ct, count in sorted(cl_type_counts.items(), key=lambda x: -x[1]):
            print(f"    {ct.replace('_', ' ').title():30s} {count} posts")

    # Cluster analysis
    print(f"\n--- CLUSTER ANALYSIS ---")
    cluster_data = defaultdict(list)
    for r in results:
        cluster_data[r["cluster"]].append(r)

    cluster_summary = []
    for cluster, items in sorted(cluster_data.items()):
        avg_sc = sum(i["overall"] for i in items) / len(items)
        cluster_summary.append((cluster, len(items), avg_sc))

    cluster_summary.sort(key=lambda x: -x[2])
    print(f"  {'Cluster':35s} {'Posts':>6s} {'Avg Score':>10s}")
    print(f"  {'-'*35} {'-'*6} {'-'*10}")
    for cluster, count, avg in cluster_summary:
        bar = "#" * int(avg / 3)
        print(f"  {cluster:35s} {count:6d} {avg:9.1f}  {bar}")

    strongest_cluster = cluster_summary[0]
    weakest_cluster = cluster_summary[-1]
    print(f"\n  STRONGEST cluster: {strongest_cluster[0]} (avg {strongest_cluster[2]:.1f})")
    print(f"  WEAKEST cluster:   {weakest_cluster[0]} (avg {weakest_cluster[2]:.1f})")

    # Top gaps
    print(f"\n--- TOP 15 PRIORITY GAPS ---")
    all_gaps = []
    for r in results:
        sorted_d = sorted(r["dim_scores"].items(), key=lambda x: x[1])
        for dim_name, dim_score in sorted_d[:2]:
            if dim_score < 30:
                all_gaps.append((r["post_id"], r["title"][:50], r["cluster"],
                                 DIMENSION_LABELS[dim_name], dim_score, r["overall"]))

    all_gaps.sort(key=lambda x: (x[5], x[4]))
    for gap in all_gaps[:15]:
        pid, title, cluster, dim, dscore, overall = gap
        print(f"  [{pid}] {title:50s} | {dim:25s} = {dscore:3d} (overall: {overall:.0f})")

    # Top 10 best posts
    print(f"\n--- TOP 10 HIGHEST DECISION SUPPORT POSTS ---")
    top10 = sorted(results, key=lambda x: -x["overall"])[:10]
    for r in top10:
        print(f"  [{r['post_id']}] {r['title'][:55]:55s} | {r['overall']:5.1f} | {r['tier']}")

    # Bottom 10 posts
    print(f"\n--- BOTTOM 10 LOWEST DECISION SUPPORT POSTS ---")
    bottom10 = sorted(results, key=lambda x: x["overall"])[:10]
    for r in bottom10:
        print(f"  [{r['post_id']}] {r['title'][:55]:55s} | {r['overall']:5.1f} | {r['tier']}")

    print(f"\n{'=' * 70}")
    print(f"OUTPUT FILES:")
    print(f"  1. {csv1_path}")
    print(f"  2. {csv2_path}")
    print(f"  3. {csv3_path}")
    print(f"{'=' * 70}")
    print(f"Decision Support Engine complete. {len(results)} posts analyzed.")


if __name__ == "__main__":
    main()
