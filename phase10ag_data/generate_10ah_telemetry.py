#!/usr/bin/env python3
"""
Phase 10AH Telemetry Generator
Generates 6 CSV reports with new scoring dimensions:
  Humanization Intensity, Decision Confidence, Practical Depth, Answer Ownership
"""

import csv
import json
import os
import re
import subprocess
import sys
import time
from html.parser import HTMLParser

# ── Config ──────────────────────────────────────────────────────────────────
BASE_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ag_data"

# ── HTML stripper ───────────────────────────────────────────────────────────
class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
    def handle_data(self, d):
        self.result.append(d)
    def get_text(self):
        return " ".join(self.result)

def strip_html(html):
    s = HTMLStripper()
    s.feed(html or "")
    return s.get_text()

# ── Wait for other agents ──────────────────────────────────────────────────
print("⏳ Waiting 180 seconds for other agents to finish modifying posts...")
time.sleep(180)
print("✅ Wait complete. Fetching posts now.")

# ── Fetch all published posts ───────────────────────────────────────────────
def fetch_all_posts():
    posts = []
    page = 1
    while True:
        url = f"{BASE_URL}/posts?status=publish&per_page=100&page={page}"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"  ⚠ JSON decode error on page {page}, stopping pagination.")
            break
        if isinstance(data, dict) and data.get("code"):
            # e.g. rest_post_invalid_page_number
            break
        if not isinstance(data, list) or len(data) == 0:
            break
        posts.extend(data)
        print(f"  Fetched page {page}: {len(data)} posts (total so far: {len(posts)})")
        if len(data) < 100:
            break
        page += 1
    return posts

print("📡 Fetching all published posts...")
all_posts = fetch_all_posts()
print(f"✅ Total posts fetched: {len(all_posts)}\n")

# ── Cluster classification ──────────────────────────────────────────────────
CLUSTER_RULES = [
    ("Cat Toys",        ["cat toy", "cat toys", "toys for cats", "kitten toy"]),
    ("Cat Supplies",    ["cat supply", "cat supplies", "cat litter", "cat carrier", "cat bed", "cat food", "cat treat", "cat harness", "cat collar", "cat fountain", "cat feeder", "cat scratcher", "scratching post", "cat tree"]),
    ("Dog Toys",        ["dog toy", "dog toys", "toys for dogs", "puppy toy", "chew toy"]),
    ("Dog Beds",        ["dog bed", "dog beds", "orthopedic bed", "dog crate", "dog kennel"]),
    ("Dog Food",        ["dog food", "dog treat", "dog diet", "dog nutrition", "raw diet", "kibble"]),
    ("Dog Grooming",    ["dog grooming", "dog shampoo", "dog brush", "grooming", "nail clipper", "deshed"]),
    ("Dog Harnesses",   ["dog harness", "harness", "dog leash", "dog collar", "no-pull"]),
    ("Dog Health",      ["dog health", "dog supplement", "dog allergy", "joint health", "dental", "flea", "tick", "dewormer"]),
    ("Dog Training",    ["dog training", "training", "obedience", "clicker", "positive reinforcement"]),
    ("Educational",     ["guide", "how to", "what is", "why do", "tips for", "understand"]),
    ("Indoor Cats",     ["indoor cat", "indoor cats", "house cat", "apartment cat"]),
    ("Puppy Care",      ["puppy", "puppies", "new puppy"]),
    ("Dog Care",        ["dog care", "dog owner", "dog walk", "dog exercise", "dog anxiety", "dog behavior"]),
]

def classify_cluster(title):
    t = title.lower()
    for cluster_name, keywords in CLUSTER_RULES:
        for kw in keywords:
            if kw in t:
                return cluster_name
    return "Uncategorized"

# ── Signal detection functions ──────────────────────────────────────────────

def detect_humanization(raw_content, text_content):
    """Returns dict of humanization signals."""
    raw_lower = (raw_content or "").lower()
    text_lower = (text_content or "").lower()

    has_about_guide = "about this guide" in text_lower
    has_common_mistakes = "common mistakes" in text_lower or "common mistake" in text_lower
    has_what_to_expect = "what to expect" in text_lower
    has_routine_checklist = (
        ("daily:" in text_lower and ("weekly:" in text_lower or "monthly:" in text_lower))
        or "routine checklist" in text_lower
    )
    has_practical_tips = any(x in text_lower for x in ["practical tip", "top tip", "useful tip"])
    has_safety_warning = any(x in text_lower for x in ["safety warning", "important:", "caution:"])
    has_beginner_guidance = any(x in text_lower for x in ["beginner", "first-time", "new owner"])

    score = (
        (15 if has_about_guide else 0)
        + (20 if has_common_mistakes else 0)
        + (15 if has_what_to_expect else 0)
        + (15 if has_routine_checklist else 0)
        + (10 if has_practical_tips else 0)
        + (10 if has_safety_warning else 0)
        + (15 if has_beginner_guidance else 0)
    )

    return {
        "has_about_guide": int(has_about_guide),
        "has_common_mistakes": int(has_common_mistakes),
        "has_what_to_expect": int(has_what_to_expect),
        "has_routine_checklist": int(has_routine_checklist),
        "has_practical_tips": int(has_practical_tips),
        "has_safety_warning": int(has_safety_warning),
        "has_beginner_guidance": int(has_beginner_guidance),
        "humanization_intensity_score": score,
    }


def detect_decision_confidence(raw_content, text_content):
    """Returns dict of decision confidence / buyer-intent signals."""
    raw_lower = (raw_content or "").lower()
    text_lower = (text_content or "").lower()

    has_suitability = any(x in text_lower for x in [
        "quick suitability", "suitability guide", "best for:"
    ])
    has_pros_cons = (
        ("advantages" in text_lower and "things to watch" in text_lower)
        or "key considerations" in text_lower
    )
    # Count "best for" occurrences
    best_for_count = len(re.findall(r"best for\b", text_lower))
    has_comparison_table = "wp:table" in raw_lower or "<table" in raw_lower
    has_budget = any(x in text_lower for x in ["budget", "mid-range", "premium"])

    # best_for score: 4 points per occurrence, capped at 20
    best_for_score = min(best_for_count * 4, 20)

    score = (
        (25 if has_suitability else 0)
        + (25 if has_pros_cons else 0)
        + best_for_score
        + (15 if has_comparison_table else 0)
        + (15 if has_budget else 0)
    )

    return {
        "has_suitability_guide": int(has_suitability),
        "has_pros_cons": int(has_pros_cons),
        "has_best_for_count": best_for_count,
        "has_comparison_table": int(has_comparison_table),
        "has_budget_guidance": int(has_budget),
        "decision_confidence_score": score,
    }


def detect_practical_depth(raw_content, text_content):
    """Returns dict of practical depth signals."""
    raw_lower = (raw_content or "").lower()
    text_lower = (text_content or "").lower()

    has_troubleshooting = any(x in text_lower for x in [
        "troubleshoot", "common problem", "if your dog", "if your cat"
    ])
    # Checklist: look for wp:list with checkmarks, or bullet lists with action items
    has_checklist = (
        "checklist" in text_lower
        or "✓" in text_content
        or "✅" in text_content
        or "☑" in text_content
        or ("wp:list" in raw_lower and ("check" in text_lower or "ensure" in text_lower))
    )
    # Measurable guidance: specific numbers, timeframes
    has_measurable = bool(re.search(
        r"\b(\d+\s*(minutes?|hours?|days?|weeks?|months?|times?\s+per|grams?|cups?|inches?|cm|lbs?|kg|ml|oz))\b",
        text_lower
    ))
    has_when_to_replace = any(x in text_lower for x in ["when to replace", "how often"])
    has_when_to_seek_help = any(x in text_lower for x in ["vet", "veterinary", "seek help", "consult"])

    score = (
        (20 if has_troubleshooting else 0)
        + (20 if has_checklist else 0)
        + (20 if has_measurable else 0)
        + (20 if has_when_to_replace else 0)
        + (20 if has_when_to_seek_help else 0)
    )

    return {
        "has_troubleshooting": int(has_troubleshooting),
        "has_checklist": int(has_checklist),
        "has_measurable_guidance": int(has_measurable),
        "has_when_to_replace": int(has_when_to_replace),
        "has_when_to_seek_help": int(has_when_to_seek_help),
        "practical_depth_score": score,
    }


def detect_answer_ownership(raw_content, text_content):
    """Returns dict of answer ownership signals."""
    raw_lower = (raw_content or "").lower()
    text_lower = (text_content or "").lower()

    has_faq = "faq" in text_lower or "frequently asked" in text_lower
    has_quick_answer = "quick answer" in text_lower

    # Count FAQ questions (look for patterns like Q: or numbered questions under FAQ)
    faq_count = 0
    if has_faq:
        # Count H3/H4 headings after FAQ section, or Q: patterns
        faq_questions = re.findall(r"<h[34][^>]*>.*?\?.*?</h[34]>", raw_lower)
        faq_count = len(faq_questions)
        if faq_count == 0:
            # Fallback: count question marks in FAQ section
            faq_idx = text_lower.find("faq")
            if faq_idx == -1:
                faq_idx = text_lower.find("frequently asked")
            if faq_idx >= 0:
                faq_section = text_lower[faq_idx:]
                faq_count = faq_section.count("?")

    # Glossary terms: H3 followed by definition-like paragraph
    has_glossary = bool(re.search(
        r"glossary|key terms|terminology|definitions",
        text_lower
    ))

    # Step-by-step content
    has_step_by_step = bool(re.search(
        r"step\s*[1-9]|step\s+one|step\s+two|step-by-step",
        text_lower
    ))

    # FAQ count score: 4 points per question, capped at 20
    faq_count_score = min(faq_count * 4, 20)

    score = (
        (20 if has_faq else 0)
        + (20 if has_quick_answer else 0)
        + faq_count_score
        + (20 if has_glossary else 0)
        + (20 if has_step_by_step else 0)
    )

    return {
        "has_faq": int(has_faq),
        "has_quick_answer": int(has_quick_answer),
        "faq_count": faq_count,
        "has_glossary_terms": int(has_glossary),
        "has_step_by_step": int(has_step_by_step),
        "answer_ownership_score": score,
    }

# ── Analyze all posts ───────────────────────────────────────────────────────
print("🔍 Analyzing posts...")

results = []
for post in all_posts:
    pid = post["id"]
    title = post["title"]["rendered"]
    raw_content = post["content"]["rendered"]
    text_content = strip_html(raw_content)
    cluster = classify_cluster(title)

    h = detect_humanization(raw_content, text_content)
    d = detect_decision_confidence(raw_content, text_content)
    p = detect_practical_depth(raw_content, text_content)
    a = detect_answer_ownership(raw_content, text_content)

    results.append({
        "id": pid,
        "title": title,
        "cluster": cluster,
        **h, **d, **p, **a,
    })

print(f"✅ Analyzed {len(results)} posts.\n")

# ── CSV 1: Humanization Intensity ───────────────────────────────────────────
csv1_path = os.path.join(OUT_DIR, "humanization_intensity_scores.csv")
csv1_fields = [
    "id", "title", "cluster",
    "has_about_guide", "has_common_mistakes", "has_what_to_expect",
    "has_routine_checklist", "has_practical_tips", "has_safety_warning",
    "has_beginner_guidance", "humanization_intensity_score",
]
with open(csv1_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=csv1_fields, extrasaction="ignore")
    w.writeheader()
    for r in results:
        w.writerow(r)
print(f"📄 Written: {csv1_path}")

# ── CSV 2: Decision Confidence ──────────────────────────────────────────────
csv2_path = os.path.join(OUT_DIR, "decision_confidence_scores.csv")
csv2_fields = [
    "id", "title", "cluster",
    "has_suitability_guide", "has_pros_cons", "has_best_for_count",
    "has_comparison_table", "has_budget_guidance", "decision_confidence_score",
]
with open(csv2_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=csv2_fields, extrasaction="ignore")
    w.writeheader()
    for r in results:
        w.writerow(r)
print(f"📄 Written: {csv2_path}")

# ── CSV 3: Practical Depth Engine ───────────────────────────────────────────
csv3_path = os.path.join(OUT_DIR, "practical_depth_engine_scores.csv")
csv3_fields = [
    "id", "title", "cluster",
    "has_troubleshooting", "has_checklist", "has_measurable_guidance",
    "has_when_to_replace", "has_when_to_seek_help", "practical_depth_score",
]
with open(csv3_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=csv3_fields, extrasaction="ignore")
    w.writeheader()
    for r in results:
        w.writerow(r)
print(f"📄 Written: {csv3_path}")

# ── CSV 4: Answer Ownership Engine ─────────────────────────────────────────
csv4_path = os.path.join(OUT_DIR, "answer_ownership_engine_scores.csv")
csv4_fields = [
    "id", "title", "cluster",
    "has_faq", "has_quick_answer", "faq_count",
    "has_glossary_terms", "has_step_by_step", "answer_ownership_score",
]
with open(csv4_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=csv4_fields, extrasaction="ignore")
    w.writeheader()
    for r in results:
        w.writerow(r)
print(f"📄 Written: {csv4_path}")

# ── CSV 5: Cluster Humanization Summary ─────────────────────────────────────
from collections import defaultdict

cluster_data = defaultdict(lambda: {
    "posts": [],
    "humanization_scores": [],
    "decision_scores": [],
    "practical_scores": [],
    "answer_scores": [],
})

for r in results:
    c = r["cluster"]
    cluster_data[c]["posts"].append(r)
    cluster_data[c]["humanization_scores"].append(r["humanization_intensity_score"])
    cluster_data[c]["decision_scores"].append(r["decision_confidence_score"])
    cluster_data[c]["practical_scores"].append(r["practical_depth_score"])
    cluster_data[c]["answer_scores"].append(r["answer_ownership_score"])

csv5_path = os.path.join(OUT_DIR, "cluster_humanization_summary.csv")
csv5_fields = [
    "cluster", "post_count", "avg_humanization", "avg_decision_confidence",
    "avg_practical_depth", "avg_answer_ownership", "weakest_dimension",
    "posts_fully_humanized", "humanization_coverage_pct",
]

csv5_rows = []
for cluster_name in sorted(cluster_data.keys()):
    cd = cluster_data[cluster_name]
    n = len(cd["posts"])
    avg_h = sum(cd["humanization_scores"]) / n if n else 0
    avg_d = sum(cd["decision_scores"]) / n if n else 0
    avg_p = sum(cd["practical_scores"]) / n if n else 0
    avg_a = sum(cd["answer_scores"]) / n if n else 0

    dims = {
        "humanization": avg_h,
        "decision_confidence": avg_d,
        "practical_depth": avg_p,
        "answer_ownership": avg_a,
    }
    weakest = min(dims, key=dims.get)

    # "Fully humanized" = humanization score >= 70 (out of 100)
    fully_humanized = sum(1 for s in cd["humanization_scores"] if s >= 70)
    coverage_pct = round(fully_humanized / n * 100, 1) if n else 0

    csv5_rows.append({
        "cluster": cluster_name,
        "post_count": n,
        "avg_humanization": round(avg_h, 1),
        "avg_decision_confidence": round(avg_d, 1),
        "avg_practical_depth": round(avg_p, 1),
        "avg_answer_ownership": round(avg_a, 1),
        "weakest_dimension": weakest,
        "posts_fully_humanized": fully_humanized,
        "humanization_coverage_pct": coverage_pct,
    })

with open(csv5_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=csv5_fields)
    w.writeheader()
    for row in csv5_rows:
        w.writerow(row)
print(f"📄 Written: {csv5_path}")

# ── CSV 6: Brand Transformation Dashboard ──────────────────────────────────
total_posts = len(results)

# Current (after) metrics
after_humanization_coverage = round(
    sum(1 for r in results if r["humanization_intensity_score"] >= 70) / total_posts * 100, 1
) if total_posts else 0

after_humanization_avg = round(
    sum(r["humanization_intensity_score"] for r in results) / total_posts, 1
) if total_posts else 0

after_decision_avg = round(
    sum(r["decision_confidence_score"] for r in results) / total_posts, 1
) if total_posts else 0

after_practical_avg = round(
    sum(r["practical_depth_score"] for r in results) / total_posts, 1
) if total_posts else 0

after_answer_avg = round(
    sum(r["answer_ownership_score"] for r in results) / total_posts, 1
) if total_posts else 0

after_comparison_coverage = round(
    sum(1 for r in results if r["has_comparison_table"]) / total_posts * 100, 1
) if total_posts else 0

after_trust_coverage = round(
    sum(1 for r in results if r["has_safety_warning"] or r["has_when_to_seek_help"]) / total_posts * 100, 1
) if total_posts else 0

after_faq_coverage = round(
    sum(1 for r in results if r["has_faq"]) / total_posts * 100, 1
) if total_posts else 0

after_about_guide_coverage = round(
    sum(1 for r in results if r["has_about_guide"]) / total_posts * 100, 1
) if total_posts else 0

# Before baselines from Phase 10AG
dashboard_rows = [
    {
        "metric": "humanization_coverage",
        "before_10ah": "20.8%",
        "after_10ah": f"{after_humanization_coverage}%",
        "change": f"{round(after_humanization_coverage - 20.8, 1):+}%",
        "target": "80%",
    },
    {
        "metric": "humanization_avg_score",
        "before_10ah": "4.7",
        "after_10ah": str(after_humanization_avg),
        "change": f"{round(after_humanization_avg - 4.7, 1):+}",
        "target": "70",
    },
    {
        "metric": "decision_confidence_avg",
        "before_10ah": "15.3",
        "after_10ah": str(after_decision_avg),
        "change": f"{round(after_decision_avg - 15.3, 1):+}",
        "target": "60",
    },
    {
        "metric": "practical_depth_avg",
        "before_10ah": "20.7",
        "after_10ah": str(after_practical_avg),
        "change": f"{round(after_practical_avg - 20.7, 1):+}",
        "target": "60",
    },
    {
        "metric": "answer_ownership_avg",
        "before_10ah": "0",
        "after_10ah": str(after_answer_avg),
        "change": f"{round(after_answer_avg - 0, 1):+}",
        "target": "60",
    },
    {
        "metric": "comparison_coverage",
        "before_10ah": "15.3%",
        "after_10ah": f"{after_comparison_coverage}%",
        "change": f"{round(after_comparison_coverage - 15.3, 1):+}%",
        "target": "70%",
    },
    {
        "metric": "trust_coverage",
        "before_10ah": "20.7%",
        "after_10ah": f"{after_trust_coverage}%",
        "change": f"{round(after_trust_coverage - 20.7, 1):+}%",
        "target": "80%",
    },
    {
        "metric": "faq_coverage",
        "before_10ah": "0%",
        "after_10ah": f"{after_faq_coverage}%",
        "change": f"{round(after_faq_coverage - 0, 1):+}%",
        "target": "80%",
    },
    {
        "metric": "about_guide_coverage",
        "before_10ah": "0%",
        "after_10ah": f"{after_about_guide_coverage}%",
        "change": f"{round(after_about_guide_coverage - 0, 1):+}%",
        "target": "80%",
    },
]

csv6_path = os.path.join(OUT_DIR, "brand_transformation_dashboard.csv")
csv6_fields = ["metric", "before_10ah", "after_10ah", "change", "target"]
with open(csv6_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=csv6_fields)
    w.writeheader()
    for row in dashboard_rows:
        w.writerow(row)
print(f"📄 Written: {csv6_path}")

# ── Summary ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("  PHASE 10AH TELEMETRY SUMMARY")
print("=" * 70)
print(f"  Total posts analyzed: {total_posts}")
print(f"  Clusters found: {len(cluster_data)}")
print()
print("  DIMENSION AVERAGES (out of 100):")
print(f"    Humanization Intensity:  {after_humanization_avg}")
print(f"    Decision Confidence:     {after_decision_avg}")
print(f"    Practical Depth:         {after_practical_avg}")
print(f"    Answer Ownership:        {after_answer_avg}")
print()
print("  COVERAGE METRICS:")
print(f"    Humanization >= 70:      {after_humanization_coverage}%")
print(f"    Comparison Tables:       {after_comparison_coverage}%")
print(f"    Trust Signals:           {after_trust_coverage}%")
print(f"    FAQ Sections:            {after_faq_coverage}%")
print(f"    About This Guide:        {after_about_guide_coverage}%")
print()
print("  SIGNAL BREAKDOWN:")
h_signals = {
    "about_guide": sum(r["has_about_guide"] for r in results),
    "common_mistakes": sum(r["has_common_mistakes"] for r in results),
    "what_to_expect": sum(r["has_what_to_expect"] for r in results),
    "routine_checklist": sum(r["has_routine_checklist"] for r in results),
    "practical_tips": sum(r["has_practical_tips"] for r in results),
    "safety_warning": sum(r["has_safety_warning"] for r in results),
    "beginner_guidance": sum(r["has_beginner_guidance"] for r in results),
    "suitability_guide": sum(r["has_suitability_guide"] for r in results),
    "pros_cons": sum(r["has_pros_cons"] for r in results),
    "comparison_table": sum(r["has_comparison_table"] for r in results),
    "budget_guidance": sum(r["has_budget_guidance"] for r in results),
    "troubleshooting": sum(r["has_troubleshooting"] for r in results),
    "checklist": sum(r["has_checklist"] for r in results),
    "measurable_guidance": sum(r["has_measurable_guidance"] for r in results),
    "when_to_replace": sum(r["has_when_to_replace"] for r in results),
    "when_to_seek_help": sum(r["has_when_to_seek_help"] for r in results),
    "faq": sum(r["has_faq"] for r in results),
    "quick_answer": sum(r["has_quick_answer"] for r in results),
    "glossary_terms": sum(r["has_glossary_terms"] for r in results),
    "step_by_step": sum(r["has_step_by_step"] for r in results),
}
for sig, count in h_signals.items():
    pct = round(count / total_posts * 100, 1) if total_posts else 0
    print(f"    {sig:25s}: {count:4d} / {total_posts} ({pct}%)")

print()
print("  CLUSTER SUMMARY:")
for row in csv5_rows:
    print(f"    {row['cluster']:20s}: {row['post_count']:3d} posts | "
          f"H={row['avg_humanization']:5.1f} D={row['avg_decision_confidence']:5.1f} "
          f"P={row['avg_practical_depth']:5.1f} A={row['avg_answer_ownership']:5.1f} | "
          f"Weakest: {row['weakest_dimension']}")

print()
print("  FILES GENERATED:")
for p in [csv1_path, csv2_path, csv3_path, csv4_path, csv5_path, csv6_path]:
    print(f"    {p}")
print("=" * 70)
print("Done.")
