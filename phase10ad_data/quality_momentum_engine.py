#!/usr/bin/env python3
"""
10AD-G: Quality Momentum Engine
pethubonline.com - WordPress pet supplies blog (144 published posts)

Tracks quality momentum across 8 dimensions per post/cluster:
  Authority, Semantic, Glossary, Trust, Comparison,
  AI-Readiness, Practical Usefulness, Citation

Outputs:
  - Quality_Momentum_Scores.csv      (per-post scores)
  - Cluster_Momentum_Summary.csv     (per-cluster averages)
  - Acceleration_Opportunities.csv   (gap-to-next-tier actions)
"""

import csv
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict
from html import unescape

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ad_data"

# ──────────────────────────────────────────────────────────────
# Cluster classification keywords
# ──────────────────────────────────────────────────────────────
CLUSTER_KEYWORDS = {
    "Dog Toys": ["dog toy", "chew toy", "fetch toy", "tug toy", "puzzle toy for dog",
                 "squeaky toy", "plush toy for dog", "rope toy", "interactive dog toy",
                 "indestructible toy", "dog ball"],
    "Dog Food": ["dog food", "kibble", "dry food for dog", "wet food for dog",
                 "raw diet dog", "dog nutrition", "dog diet", "grain-free dog",
                 "puppy food", "senior dog food", "dog treat", "dog feeding"],
    "Dog Beds": ["dog bed", "orthopedic bed", "elevated bed", "dog crate pad",
                 "calming bed", "dog mattress", "dog sleeping", "bolster bed"],
    "Dog Harnesses": ["dog harness", "no-pull harness", "step-in harness",
                      "front-clip harness", "dog leash", "dog collar", "dog walking",
                      "harness for dog"],
    "Dog Health": ["dog health", "dog vet", "dog disease", "dog allergy",
                   "dog supplement", "dog vitamin", "dog medication", "flea",
                   "tick", "heartworm", "dog dental", "dog vaccination",
                   "dog parasite", "dog first aid", "dog symptom"],
    "Dog Care": ["dog grooming", "dog bath", "dog nail", "dog ear clean",
                 "dog brush", "dog shampoo", "dog coat", "dog shedding",
                 "dog care tip", "dog hygiene", "how to groom"],
    "Cat Toys": ["cat toy", "catnip toy", "laser toy", "feather toy",
                 "interactive cat", "cat puzzle", "cat ball", "cat wand"],
    "Cat Supplies": ["cat supply", "cat supplies", "cat litter", "cat tree",
                     "cat scratcher", "cat bed", "cat food", "cat bowl",
                     "cat carrier", "cat collar", "cat fountain", "cat feeder",
                     "cat health", "cat grooming", "kitten"],
    "Puppy Care": ["puppy care", "puppy training", "house training",
                   "crate training", "puppy socialization", "new puppy",
                   "puppy tip", "puppy guide", "puppy essential"],
    "Dog Supplies": ["dog supply", "dog supplies", "dog bowl", "dog crate",
                     "dog gate", "dog carrier", "dog kennel", "dog tag",
                     "dog fence", "dog ramp", "dog stroller", "dog feeder",
                     "dog water", "dog accessory", "dog product"],
    "Pet Care General": ["pet care", "pet safety", "pet travel", "pet insurance",
                         "pet owner", "pet tip", "pet advice", "pet wellness",
                         "pet-friendly", "pet emergency", "pet first aid",
                         "pet wellness", "animal care"],
    "Educational": ["guide", "how to choose", "what to look for", "buying guide",
                    "review", "comparison", "best practice", "tips for",
                    "everything you need to know", "ultimate guide", "complete guide"],
}


def strip_html(text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_all_posts():
    """Fetch all published posts via WP REST API using curl."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_BASE}/posts?status=publish&per_page=100&page={page}&context=edit"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=120
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
        print(f"  Fetched page {page} — {len(data)} posts (total: {len(all_posts)})")
        if len(data) < 100:
            break
        page += 1
    return all_posts


def classify_cluster(title, content_text):
    """Classify a post into a cluster based on title + content keywords."""
    combined = (title + " " + content_text[:2000]).lower()
    scores = {}
    for cluster, keywords in CLUSTER_KEYWORDS.items():
        score = 0
        for kw in keywords:
            # title matches worth 3x
            if kw in title.lower():
                score += 3
            if kw in combined:
                score += 1
        scores[cluster] = score
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "Pet Care General"
    return best


def clamp(val, lo=0, hi=100):
    return max(lo, min(hi, val))


# ──────────────────────────────────────────────────────────────
# Scoring functions — each returns 0-100
# ──────────────────────────────────────────────────────────────

def score_authority(raw_content, text):
    """Editorial standards, trust signals, methodology, external citations."""
    s = 0
    low = text.lower()
    raw_low = raw_content.lower()

    # External links count (href pointing outside pethubonline.com)
    ext_links = len(re.findall(r'href=["\']https?://(?!pethubonline\.com)', raw_low))
    s += min(ext_links * 4, 30)

    # Methodology / research references
    method_words = ["study", "research", "according to", "published in", "journal",
                    "veterinarian", "vet-recommended", "vet recommended", "expert",
                    "board-certified", "clinical", "peer-reviewed", "evidence-based",
                    "data shows", "statistics show", "survey"]
    method_hits = sum(1 for w in method_words if w in low)
    s += min(method_hits * 5, 25)

    # Trust signals
    trust_phrases = ["written by", "reviewed by", "medically reviewed",
                     "fact-checked", "fact checked", "editorial team",
                     "updated on", "last updated", "sources:", "references:"]
    trust_hits = sum(1 for w in trust_phrases if w in low)
    s += min(trust_hits * 6, 20)

    # Word count factor (longer = potentially more authoritative)
    wc = len(text.split())
    if wc > 3000:
        s += 15
    elif wc > 2000:
        s += 12
    elif wc > 1000:
        s += 8
    elif wc > 500:
        s += 4

    # Headings structure (h2/h3 depth)
    h2_count = len(re.findall(r"<h2", raw_low))
    h3_count = len(re.findall(r"<h3", raw_low))
    s += min((h2_count + h3_count) * 2, 10)

    return clamp(s)


def score_semantic(raw_content, text):
    """Glossary coverage, key terms blocks, inline definitions, bold-dash definitions."""
    s = 0
    low = text.lower()
    raw_low = raw_content.lower()

    # Key Terms / glossary section headings
    if re.search(r"(key terms|glossary|terminology|definitions|key concepts)", low):
        s += 20

    # Bold-dash definitions: **term** — definition   or  **term** - definition
    bold_dash = len(re.findall(r"\*\*[^*]+\*\*\s*[-–—]", raw_content))
    bold_dash += len(re.findall(r"<strong>[^<]+</strong>\s*[-–—]", raw_content))
    s += min(bold_dash * 4, 30)

    # Inline definitions (parenthetical explanations)
    inline_defs = len(re.findall(r"\([^)]{15,120}\)", text))
    s += min(inline_defs * 2, 15)

    # Definition list markup
    dl_count = len(re.findall(r"<dt|<dd", raw_low))
    s += min(dl_count * 3, 15)

    # Technical/domain terms density
    domain_terms = ["protein", "fiber", "nutrient", "ingredient", "breed",
                    "behavioral", "digestive", "orthopedic", "ergonomic",
                    "hypoallergenic", "antimicrobial", "biodegradable",
                    "durability", "bioavailability", "palatability",
                    "temperament", "socialization", "desensitization"]
    term_hits = sum(1 for t in domain_terms if t in low)
    s += min(term_hits * 3, 20)

    return clamp(s)


def score_glossary(raw_content, text):
    """Glossary block presence, definition count, terminology depth."""
    s = 0
    low = text.lower()
    raw_low = raw_content.lower()

    # Explicit glossary / key terms section
    if re.search(r"(glossary|key terms|terminology|vocabulary|definitions)", low):
        s += 25

    # Definition-like patterns
    # "X is a ..." or "X refers to ..." or "X means ..."
    def_patterns = len(re.findall(
        r"(?:is a |refers to |means |defined as |known as |also called )", low))
    s += min(def_patterns * 3, 25)

    # Bold terms (often glossary-style)
    bold_terms = len(re.findall(r"<strong>[^<]{3,50}</strong>", raw_content))
    s += min(bold_terms * 2, 20)

    # Ordered / unordered lists (structured definitions)
    list_items = len(re.findall(r"<li", raw_low))
    s += min(list_items * 1, 15)

    # Heading count suggesting organized terminology
    h_count = len(re.findall(r"<h[2-4]", raw_low))
    s += min(h_count * 2, 15)

    return clamp(s)


def score_trust(raw_content, text):
    """Editorial links, methodology, corrections, AI transparency, disclosure, update dates."""
    s = 0
    low = text.lower()
    raw_low = raw_content.lower()

    # Updated / last updated date
    if re.search(r"(updated on|last updated|last modified|date updated)", low):
        s += 15

    # Editorial / disclosure
    disclosure_phrases = ["disclosure", "affiliate", "sponsored", "disclaimer",
                          "editorial policy", "editorial standards",
                          "we may earn", "commission"]
    disc_hits = sum(1 for d in disclosure_phrases if d in low)
    s += min(disc_hits * 5, 20)

    # AI transparency
    ai_phrases = ["ai-generated", "ai generated", "written with ai",
                  "assisted by ai", "ai transparency", "human-reviewed"]
    ai_hits = sum(1 for a in ai_phrases if a in low)
    s += min(ai_hits * 8, 15)

    # Corrections / methodology
    method_phrases = ["correction:", "editor's note", "methodology",
                      "how we test", "how we review", "our process",
                      "testing methodology", "evaluation criteria"]
    meth_hits = sum(1 for m in method_phrases if m in low)
    s += min(meth_hits * 6, 20)

    # Author attribution
    if re.search(r"(written by|author:|by [A-Z][a-z]+ [A-Z][a-z]+)", text):
        s += 10

    # Internal editorial links
    int_links = len(re.findall(r'href=["\']https?://pethubonline\.com', raw_low))
    s += min(int_links * 2, 15)

    # Sources / references section
    if re.search(r"(sources|references|bibliography|works cited)", low):
        s += 5

    return clamp(s)


def score_comparison(raw_content, text):
    """Comparison tables, vs content, pro/con sections, structured comparisons."""
    s = 0
    low = text.lower()
    raw_low = raw_content.lower()

    # Tables
    table_count = len(re.findall(r"<table", raw_low))
    s += min(table_count * 12, 30)

    # "vs" / "versus" in title or content
    vs_hits = len(re.findall(r"\bvs\.?\b|\bversus\b", low))
    s += min(vs_hits * 5, 20)

    # Pro/con sections
    procon = len(re.findall(r"(pros?[\s:&]|cons?[\s:]|advantages|disadvantages|drawbacks|benefits)", low))
    s += min(procon * 4, 20)

    # Comparison headings
    comp_headings = len(re.findall(
        r"(comparison|compared|comparing|head.to.head|side.by.side|which is better|difference between)", low))
    s += min(comp_headings * 5, 15)

    # Rating / score mentions
    rating_hits = len(re.findall(r"(rating|score|out of 5|out of 10|★|⭐|/5|/10)", low))
    s += min(rating_hits * 3, 15)

    return clamp(s)


def score_ai_readiness(raw_content, text):
    """FAQ blocks, quick-answer blocks, structured Q&A, extractable format, summaries."""
    s = 0
    low = text.lower()
    raw_low = raw_content.lower()

    # FAQ schema / section
    if re.search(r"(faq|frequently asked|common questions)", low):
        s += 20

    # Question-answer patterns
    qa_patterns = len(re.findall(r"\?(?:\s*</(?:h[2-4]|strong|p)>)", raw_content))
    qa_patterns += len(re.findall(r"^[QA]:\s", text, re.MULTILINE))
    s += min(qa_patterns * 4, 20)

    # Quick answer / summary / TL;DR / key takeaway
    quick_phrases = ["quick answer", "short answer", "tl;dr", "key takeaway",
                     "bottom line", "in summary", "in short", "the verdict",
                     "our pick", "our recommendation", "editor's choice",
                     "summary", "at a glance", "quick summary"]
    quick_hits = sum(1 for q in quick_phrases if q in low)
    s += min(quick_hits * 5, 20)

    # Structured data markers (schema.org, JSON-LD hints)
    if re.search(r"(schema\.org|itemtype|json-ld|structured data|faqpage)", raw_low):
        s += 10

    # Bullet / numbered lists (extractable format)
    list_items = len(re.findall(r"<li", raw_low))
    s += min(list_items * 1, 15)

    # Headings as questions
    q_headings = len(re.findall(r"<h[2-4][^>]*>[^<]*\?", raw_content))
    s += min(q_headings * 3, 15)

    return clamp(s)


def score_practical(raw_content, text):
    """Checklists, step-by-step, how-to, tips, examples, troubleshooting."""
    s = 0
    low = text.lower()
    raw_low = raw_content.lower()

    # Step-by-step / numbered instructions
    step_patterns = len(re.findall(r"(step \d|step-by-step|instructions:|directions:)", low))
    s += min(step_patterns * 5, 20)

    # How-to
    howto = len(re.findall(r"(how to |how do |how can )", low))
    s += min(howto * 3, 15)

    # Tips
    tip_patterns = len(re.findall(r"(tip:|tips:|pro tip|expert tip|quick tip|helpful tip)", low))
    s += min(tip_patterns * 4, 15)

    # Checklists
    checklist = len(re.findall(r"(checklist|✓|✔|☑|checkbox|\[x\]|\[ \])", low))
    s += min(checklist * 5, 15)

    # Examples
    example_hits = len(re.findall(r"(for example|example:|e\.g\.|such as|for instance)", low))
    s += min(example_hits * 3, 15)

    # Troubleshooting / problem-solution
    trouble = len(re.findall(
        r"(troubleshoot|problem|solution|common issue|if .+ doesn't work|warning:|caution:|note:)", low))
    s += min(trouble * 3, 10)

    # Actionable lists
    list_items = len(re.findall(r"<li", raw_low))
    s += min(list_items * 1, 10)

    return clamp(s)


def score_citation(raw_content, text):
    """External references, source attributions, educational depth, reference quality."""
    s = 0
    low = text.lower()
    raw_low = raw_content.lower()

    # External links (non-pethubonline)
    ext_links = len(re.findall(r'href=["\']https?://(?!pethubonline\.com)', raw_low))
    s += min(ext_links * 3, 25)

    # Source / citation phrases
    cite_phrases = ["according to", "source:", "reference:", "cited from",
                    "study by", "published in", "research from", "data from",
                    "report by", "per the", "as noted by", "as stated by"]
    cite_hits = sum(1 for c in cite_phrases if c in low)
    s += min(cite_hits * 5, 25)

    # Academic / authoritative domains
    auth_domains = [".edu", ".gov", ".org", "ncbi.nlm.nih", "pubmed",
                    "aspca.org", "akc.org", "avma.org", "vet.cornell",
                    "merckvetmanual", "petmd.com"]
    domain_hits = sum(1 for d in auth_domains if d in raw_low)
    s += min(domain_hits * 6, 25)

    # Sources / references section
    if re.search(r"(sources|references|bibliography|works cited|further reading)", low):
        s += 10

    # Footnotes / endnotes
    fn = len(re.findall(r"(\[\d+\]|footnote|endnote)", low))
    s += min(fn * 3, 15)

    return clamp(s)


# ──────────────────────────────────────────────────────────────
# Quality tier logic
# ──────────────────────────────────────────────────────────────
TIER_THRESHOLDS = [
    (90, "S"),
    (75, "A"),
    (60, "B"),
    (45, "C"),
    (0,  "D"),
]

def quality_tier(score):
    for threshold, tier in TIER_THRESHOLDS:
        if score >= threshold:
            return tier
    return "D"


# ──────────────────────────────────────────────────────────────
# Acceleration opportunity logic
# ──────────────────────────────────────────────────────────────
TIER_BOUNDARIES = [90, 75, 60, 45]

DIMENSION_ACTIONS = {
    "authority": "Add expert citations, vet references, methodology sections, external authoritative links",
    "semantic": "Add Key Terms blocks, bold-dash definitions, inline terminology, glossary sections",
    "glossary": "Create dedicated glossary blocks, add definition patterns, structured terminology lists",
    "trust": "Add 'last updated' dates, editorial disclosures, author attribution, methodology transparency",
    "comparison": "Add comparison tables, vs sections, pro/con lists, rating structures",
    "ai_readiness": "Add FAQ sections, quick-answer blocks, structured Q&A, summary/verdict sections",
    "practical": "Add step-by-step guides, checklists, tips blocks, troubleshooting sections, examples",
    "citation": "Add external references, academic sources, 'according to' attributions, source sections",
}

def find_acceleration_opportunities(cluster_data):
    """Find dimensions where clusters are close to the next tier threshold."""
    opportunities = []
    for cluster, dims in cluster_data.items():
        for dim_name, avg_score in dims.items():
            if dim_name in ("post_count", "overall", "tier"):
                continue
            # Find next tier threshold above current score
            next_threshold = None
            for t in sorted(TIER_BOUNDARIES):
                if t > avg_score:
                    next_threshold = t
                    break
            if next_threshold is None:
                continue  # already at S tier
            gap = next_threshold - avg_score
            if gap <= 25:  # within striking distance
                priority = "HIGH" if gap <= 10 else "MEDIUM" if gap <= 18 else "LOW"
                opportunities.append({
                    "cluster": cluster,
                    "dimension": dim_name,
                    "current_score": round(avg_score, 1),
                    "next_tier_threshold": next_threshold,
                    "gap_to_next": round(gap, 1),
                    "suggested_actions": DIMENSION_ACTIONS.get(dim_name, "Improve content quality"),
                    "priority": priority,
                })
    # Sort: HIGH first, then by smallest gap
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    opportunities.sort(key=lambda x: (priority_order[x["priority"]], x["gap_to_next"]))
    return opportunities


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("  10AD-G: QUALITY MOMENTUM ENGINE")
    print("  pethubonline.com")
    print("=" * 70)

    # 1. Fetch posts
    print("\n[1/5] Fetching all published posts...")
    posts = fetch_all_posts()
    if not posts:
        print("ERROR: No posts fetched. Aborting.")
        sys.exit(1)
    print(f"  Total posts fetched: {len(posts)}")

    # 2. Score every post
    print("\n[2/5] Scoring all posts on 8 quality dimensions...")
    post_scores = []
    for i, post in enumerate(posts):
        pid = post.get("id", 0)
        title_raw = post.get("title", {})
        if isinstance(title_raw, dict):
            title = strip_html(title_raw.get("rendered", title_raw.get("raw", "")))
        else:
            title = strip_html(str(title_raw))

        content_raw = post.get("content", {})
        if isinstance(content_raw, dict):
            raw_html = content_raw.get("rendered", content_raw.get("raw", ""))
        else:
            raw_html = str(content_raw)
        text = strip_html(raw_html)

        cluster = classify_cluster(title, text)

        auth  = score_authority(raw_html, text)
        sem   = score_semantic(raw_html, text)
        glos  = score_glossary(raw_html, text)
        tru   = score_trust(raw_html, text)
        comp  = score_comparison(raw_html, text)
        air   = score_ai_readiness(raw_html, text)
        prac  = score_practical(raw_html, text)
        cit   = score_citation(raw_html, text)

        overall = round((auth + sem + glos + tru + comp + air + prac + cit) / 8, 1)
        tier = quality_tier(overall)

        post_scores.append({
            "post_id": pid,
            "title": title,
            "cluster": cluster,
            "authority": auth,
            "semantic": sem,
            "glossary": glos,
            "trust": tru,
            "comparison": comp,
            "ai_readiness": air,
            "practical_usefulness": prac,
            "citation": cit,
            "overall_quality": overall,
            "quality_tier": tier,
        })

        if (i + 1) % 25 == 0 or (i + 1) == len(posts):
            print(f"  Scored {i + 1}/{len(posts)} posts...")

    # 3. Cluster aggregation
    print("\n[3/5] Aggregating cluster-level momentum...")
    cluster_agg = defaultdict(lambda: {
        "post_count": 0,
        "authority": [], "semantic": [], "glossary": [],
        "trust": [], "comparison": [], "ai_readiness": [],
        "practical": [], "citation": [], "overall": [],
    })

    for ps in post_scores:
        c = ps["cluster"]
        cluster_agg[c]["post_count"] += 1
        cluster_agg[c]["authority"].append(ps["authority"])
        cluster_agg[c]["semantic"].append(ps["semantic"])
        cluster_agg[c]["glossary"].append(ps["glossary"])
        cluster_agg[c]["trust"].append(ps["trust"])
        cluster_agg[c]["comparison"].append(ps["comparison"])
        cluster_agg[c]["ai_readiness"].append(ps["ai_readiness"])
        cluster_agg[c]["practical"].append(ps["practical_usefulness"])
        cluster_agg[c]["citation"].append(ps["citation"])
        cluster_agg[c]["overall"].append(ps["overall_quality"])

    cluster_summaries = []
    cluster_dim_avgs = {}  # for acceleration
    dims_list = ["authority", "semantic", "glossary", "trust",
                 "comparison", "ai_readiness", "practical", "citation"]

    for cluster in sorted(cluster_agg.keys()):
        data = cluster_agg[cluster]
        avg = {}
        for d in dims_list:
            avg[d] = round(sum(data[d]) / len(data[d]), 1) if data[d] else 0
        overall_cluster = round(sum(data["overall"]) / len(data["overall"]), 1) if data["overall"] else 0
        tier = quality_tier(overall_cluster)

        # Strongest / weakest
        dim_scores = {d: avg[d] for d in dims_list}
        strongest = max(dim_scores, key=dim_scores.get)
        weakest = min(dim_scores, key=dim_scores.get)

        cluster_summaries.append({
            "cluster": cluster,
            "post_count": data["post_count"],
            "avg_authority": avg["authority"],
            "avg_semantic": avg["semantic"],
            "avg_glossary": avg["glossary"],
            "avg_trust": avg["trust"],
            "avg_comparison": avg["comparison"],
            "avg_ai_readiness": avg["ai_readiness"],
            "avg_practical": avg["practical"],
            "avg_citation": avg["citation"],
            "overall_cluster_score": overall_cluster,
            "cluster_tier": tier,
            "strongest_dimension": strongest,
            "weakest_dimension": weakest,
        })
        cluster_dim_avgs[cluster] = avg

    # 4. Acceleration opportunities
    print("\n[4/5] Identifying acceleration opportunities...")
    accel_opps = find_acceleration_opportunities(cluster_dim_avgs)

    # 5. Write CSVs
    print("\n[5/5] Writing output CSVs...")

    # CSV 1: Post-level scores
    csv1_path = os.path.join(OUT_DIR, "Quality_Momentum_Scores.csv")
    with open(csv1_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "authority", "semantic", "glossary",
            "trust", "comparison", "ai_readiness", "practical_usefulness",
            "citation", "overall_quality", "quality_tier"
        ])
        writer.writeheader()
        for row in sorted(post_scores, key=lambda x: x["overall_quality"], reverse=True):
            writer.writerow(row)
    print(f"  -> {csv1_path}")

    # CSV 2: Cluster summary
    csv2_path = os.path.join(OUT_DIR, "Cluster_Momentum_Summary.csv")
    with open(csv2_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cluster", "post_count", "avg_authority", "avg_semantic", "avg_glossary",
            "avg_trust", "avg_comparison", "avg_ai_readiness", "avg_practical",
            "avg_citation", "overall_cluster_score", "cluster_tier",
            "strongest_dimension", "weakest_dimension"
        ])
        writer.writeheader()
        for row in sorted(cluster_summaries, key=lambda x: x["overall_cluster_score"], reverse=True):
            writer.writerow(row)
    print(f"  -> {csv2_path}")

    # CSV 3: Acceleration opportunities
    csv3_path = os.path.join(OUT_DIR, "Acceleration_Opportunities.csv")
    with open(csv3_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cluster", "dimension", "current_score", "next_tier_threshold",
            "gap_to_next", "suggested_actions", "priority"
        ])
        writer.writeheader()
        for row in accel_opps:
            writer.writerow(row)
    print(f"  -> {csv3_path}")

    # ──────────────────────────────────────────────────────────
    # SUMMARY REPORT
    # ──────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  QUALITY MOMENTUM REPORT")
    print("=" * 70)

    # Overall site quality
    all_overalls = [p["overall_quality"] for p in post_scores]
    site_avg = round(sum(all_overalls) / len(all_overalls), 1) if all_overalls else 0
    site_tier = quality_tier(site_avg)
    print(f"\n  OVERALL SITE QUALITY: {site_avg}/100 (Tier {site_tier})")
    print(f"  Total posts analyzed: {len(post_scores)}")

    # Tier distribution
    tier_dist = defaultdict(int)
    for p in post_scores:
        tier_dist[p["quality_tier"]] += 1
    print(f"\n  TIER DISTRIBUTION:")
    for t in ["S", "A", "B", "C", "D"]:
        count = tier_dist.get(t, 0)
        pct = round(count / len(post_scores) * 100, 1) if post_scores else 0
        bar = "#" * int(pct / 2)
        print(f"    Tier {t}: {count:>3} posts ({pct:>5.1f}%)  {bar}")

    # Dimension averages site-wide
    print(f"\n  SITE-WIDE DIMENSION AVERAGES:")
    dim_names_full = {
        "authority": "Authority",
        "semantic": "Semantic",
        "glossary": "Glossary",
        "trust": "Trust",
        "comparison": "Comparison",
        "ai_readiness": "AI-Readiness",
        "practical_usefulness": "Practical",
        "citation": "Citation",
    }
    site_dim_avgs = {}
    for dim_key, dim_label in dim_names_full.items():
        vals = [p[dim_key] for p in post_scores]
        avg = round(sum(vals) / len(vals), 1) if vals else 0
        site_dim_avgs[dim_key] = avg
        bar = "#" * int(avg / 2)
        print(f"    {dim_label:<16}: {avg:>5.1f}/100  {bar}")

    # Per-cluster breakdown
    print(f"\n  PER-CLUSTER BREAKDOWN:")
    print(f"  {'Cluster':<22} {'Posts':>5} {'Overall':>8} {'Tier':>5} {'Strongest':<14} {'Weakest':<14}")
    print(f"  {'-'*22} {'-'*5} {'-'*8} {'-'*5} {'-'*14} {'-'*14}")
    for cs in sorted(cluster_summaries, key=lambda x: x["overall_cluster_score"], reverse=True):
        print(f"  {cs['cluster']:<22} {cs['post_count']:>5} {cs['overall_cluster_score']:>8.1f} "
              f"{cs['cluster_tier']:>5} {cs['strongest_dimension']:<14} {cs['weakest_dimension']:<14}")

    # Top 5 acceleration opportunities
    print(f"\n  TOP 5 ACCELERATION OPPORTUNITIES:")
    for i, opp in enumerate(accel_opps[:5], 1):
        print(f"    {i}. [{opp['priority']}] {opp['cluster']} / {opp['dimension']}")
        print(f"       Score: {opp['current_score']} -> next tier at {opp['next_tier_threshold']} "
              f"(gap: {opp['gap_to_next']})")
        print(f"       Action: {opp['suggested_actions']}")

    # Strongest / weakest clusters
    if cluster_summaries:
        best_cluster = max(cluster_summaries, key=lambda x: x["overall_cluster_score"])
        worst_cluster = min(cluster_summaries, key=lambda x: x["overall_cluster_score"])
        print(f"\n  STRONGEST CLUSTER: {best_cluster['cluster']} "
              f"({best_cluster['overall_cluster_score']}/100, Tier {best_cluster['cluster_tier']})")
        print(f"  WEAKEST  CLUSTER: {worst_cluster['cluster']} "
              f"({worst_cluster['overall_cluster_score']}/100, Tier {worst_cluster['cluster_tier']})")

    print(f"\n  Total acceleration opportunities found: {len(accel_opps)}")
    print(f"    HIGH priority: {sum(1 for o in accel_opps if o['priority'] == 'HIGH')}")
    print(f"    MEDIUM priority: {sum(1 for o in accel_opps if o['priority'] == 'MEDIUM')}")
    print(f"    LOW priority: {sum(1 for o in accel_opps if o['priority'] == 'LOW')}")

    print("\n" + "=" * 70)
    print("  Quality Momentum Engine complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
