#!/usr/bin/env python3
"""
Cluster Leadership Engine - PetHubOnline.com
Generates two data products:
1. Cluster Leadership Rankings (per-cluster)
2. Visibility Readiness Scores (per-post and per-cluster)
"""

import subprocess
import json
import csv
import re
import time
import os
from collections import defaultdict
from html.parser import HTMLParser

# ─── Config ───────────────────────────────────────────────────────────────────
API_URL = "https://pethubonline.com/wp-json/wp/v2/posts"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase11w_data"

CATEGORY_MAP = {
    1377: "Cat Supplies",
    1459: "Cat Toys",
    1413: "Indoor Cats",
    1376: "Dog Supplies",
    1397: "Pet Care",
    1401: "Dog Beds",
    1489: "Dog Care",
    1467: "Dog Food",
    1422: "Dog Harnesses",
    1450: "Dog Health",
    1441: "Dog Toys",
    1442: "Puppy Care",
    1474: "Training Supplies",
    1: "Uncategorized",
}


# ─── HTML text extractor ─────────────────────────────────────────────────────
class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text = []

    def handle_data(self, data):
        self._text.append(data)

    def get_text(self):
        return " ".join(self._text)


def strip_html(html_str):
    extractor = HTMLTextExtractor()
    try:
        extractor.feed(html_str or "")
    except Exception:
        pass
    return extractor.get_text()


# ─── Fetch all published posts ───────────────────────────────────────────────
def fetch_all_posts():
    """Fetch all published posts using subprocess.run(curl)."""
    all_posts = []
    page = 1
    per_page = 100

    while True:
        time.sleep(2)
        url = (
            f"{API_URL}?status=publish&per_page={per_page}&page={page}"
            f"&context=edit&_fields=id,title,content,categories,link"
        )
        print(f"  Fetching page {page}...")
        result = subprocess.run(
            [
                "curl", "-s", "-w", "\n%{http_code}",
                "-u", AUTH,
                url,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        output = result.stdout.strip()
        lines = output.rsplit("\n", 1)
        if len(lines) == 2:
            body, status_code = lines
        else:
            body = output
            status_code = "200"

        if status_code.strip() not in ("200",):
            print(f"  Got HTTP {status_code.strip()} on page {page}, stopping.")
            break

        try:
            posts = json.loads(body)
        except json.JSONDecodeError:
            print(f"  JSON decode error on page {page}, stopping.")
            break

        if not posts or not isinstance(posts, list):
            break

        all_posts.extend(posts)
        print(f"  Got {len(posts)} posts (total: {len(all_posts)})")

        if len(posts) < per_page:
            break
        page += 1

    return all_posts


# ─── Content analysis ────────────────────────────────────────────────────────
def analyze_post(post):
    """Analyze a single post's raw Gutenberg content."""
    post_id = post["id"]
    title = post.get("title", {})
    if isinstance(title, dict):
        title_text = title.get("raw", title.get("rendered", ""))
    else:
        title_text = str(title)
    title_text = strip_html(title_text)

    content = post.get("content", {})
    if isinstance(content, dict):
        raw_content = content.get("raw", content.get("rendered", ""))
    else:
        raw_content = str(content)

    categories = post.get("categories", [])
    cluster = "Uncategorized"
    for cat_id in categories:
        if cat_id in CATEGORY_MAP and cat_id != 1:
            cluster = CATEGORY_MAP[cat_id]
            break
    else:
        if 1 in categories:
            cluster = "Uncategorized"

    link = post.get("link", "")

    # Plain text for word count
    plain_text = strip_html(raw_content)
    word_count = len(plain_text.split())

    # 1. Quick-answer block
    has_quick_answer = bool(re.search(r'quick-answer', raw_content, re.IGNORECASE))

    # 2. Question-format H2s
    h2_matches = re.findall(r'<h2[^>]*>(.*?)</h2>', raw_content, re.IGNORECASE | re.DOTALL)
    h2_count = len(h2_matches)
    question_h2_count = 0
    for h2 in h2_matches:
        h2_text = strip_html(h2).strip()
        if h2_text.endswith("?"):
            question_h2_count += 1

    # 3. Sources and References section
    has_sources = bool(re.search(
        r'(Sources\s+and\s+References|Sources|References|Bibliography)',
        raw_content, re.IGNORECASE
    ))

    # Count source citations (links in sources section or cite elements)
    source_citation_count = 0
    sources_section = re.search(
        r'(Sources\s+and\s+References|Sources|References)(.*?)($|<h[23])',
        raw_content, re.IGNORECASE | re.DOTALL
    )
    if sources_section:
        source_links = re.findall(r'<a\s+[^>]*href=', sources_section.group(2), re.IGNORECASE)
        source_citation_count = len(source_links)
    # Also count cite/blockquote elements
    source_citation_count += len(re.findall(r'<cite', raw_content, re.IGNORECASE))

    # 4. Trust editorial block
    has_trust_editorial = bool(re.search(r'trust-editorial-block', raw_content, re.IGNORECASE))

    # 5. FAQ section
    has_faq = bool(re.search(r'(Frequently\s+Asked\s+Questions|FAQ)', raw_content, re.IGNORECASE))
    # Count FAQ items (look for question patterns in FAQ section)
    faq_item_count = 0
    faq_section = re.search(
        r'(Frequently\s+Asked\s+Questions|FAQ)(.*?)($|<!-- /wp:|<h2)',
        raw_content, re.IGNORECASE | re.DOTALL
    )
    if faq_section:
        # Count H3s or strong/dt elements in FAQ section as items
        faq_items_h3 = re.findall(r'<h3[^>]*>.*?</h3>', faq_section.group(2), re.IGNORECASE | re.DOTALL)
        faq_items_dt = re.findall(r'<dt[^>]*>.*?</dt>', faq_section.group(2), re.IGNORECASE | re.DOTALL)
        faq_items_strong = re.findall(r'<strong>.*?\?</strong>', faq_section.group(2), re.IGNORECASE | re.DOTALL)
        faq_item_count = max(len(faq_items_h3), len(faq_items_dt), len(faq_items_strong))
    # Also check for wp:yoast/faq-block or schema FAQ
    yoast_faq_items = re.findall(r'"question":', raw_content)
    if yoast_faq_items:
        faq_item_count = max(faq_item_count, len(yoast_faq_items))

    # 6. Internal links to pethubonline.com
    internal_links = re.findall(
        r'<a\s+[^>]*href=["\']https?://(?:www\.)?pethubonline\.com[^"\']*["\']',
        raw_content, re.IGNORECASE
    )
    internal_link_count = len(internal_links)

    # 7. wp-block-table presence
    has_table = bool(re.search(r'wp-block-table', raw_content, re.IGNORECASE))

    # 8. Comparison table/section
    has_comparison = bool(re.search(
        r'(comparison|vs\.|versus|compare)', raw_content, re.IGNORECASE
    ))

    # 9. Glossary section
    has_glossary = bool(re.search(r'glossary', raw_content, re.IGNORECASE))

    # 10. Structured data / schema markup
    has_structured_data = bool(re.search(
        r'(schema\.org|itemtype|application/ld\+json|wp:yoast)',
        raw_content, re.IGNORECASE
    ))

    # 11. Disclosure links (affiliate, sponsored, etc.)
    has_disclosure = bool(re.search(
        r'(disclosure|affiliate|sponsored|commission|earn.*commission)',
        raw_content, re.IGNORECASE
    ))

    return {
        "post_id": post_id,
        "title": title_text,
        "cluster": cluster,
        "link": link,
        "word_count": word_count,
        "has_quick_answer": has_quick_answer,
        "h2_count": h2_count,
        "question_h2_count": question_h2_count,
        "has_sources": has_sources,
        "source_citation_count": source_citation_count,
        "has_trust_editorial": has_trust_editorial,
        "has_faq": has_faq,
        "faq_item_count": faq_item_count,
        "internal_link_count": internal_link_count,
        "has_table": has_table,
        "has_comparison": has_comparison,
        "has_glossary": has_glossary,
        "has_structured_data": has_structured_data,
        "has_disclosure": has_disclosure,
    }


# ─── Scoring functions ───────────────────────────────────────────────────────
def clamp(value, lo=0, hi=100):
    return max(lo, min(hi, value))


def compute_post_scores(analysis):
    """Compute per-post visibility readiness dimension scores."""

    wc = max(analysis["word_count"], 1)

    # authority_density: trust links + FAQ + glossary + comparison + sources + table
    authority_signals = sum([
        analysis["has_trust_editorial"],
        analysis["has_faq"],
        analysis["has_glossary"],
        analysis["has_comparison"],
        analysis["has_sources"],
        analysis["has_table"],
    ])
    authority_density = clamp((authority_signals / 6) * 100)

    # citation_confidence: source quality + structured data + factual density
    cite_score = clamp(analysis["source_citation_count"] * 12, 0, 50)
    structured_bonus = 20 if analysis["has_structured_data"] else 0
    source_section_bonus = 15 if analysis["has_sources"] else 0
    factual_bonus = 15 if analysis["has_table"] or analysis["has_comparison"] else 0
    citation_confidence = clamp(cite_score + structured_bonus + source_section_bonus + factual_bonus)

    # quick_answer_coverage: binary
    quick_answer_coverage = 100 if analysis["has_quick_answer"] else 0

    # snippet_readiness: % of H2s in question format
    if analysis["h2_count"] > 0:
        snippet_readiness = clamp((analysis["question_h2_count"] / analysis["h2_count"]) * 100)
    else:
        snippet_readiness = 0

    # faq_density: FAQ items per 1000 words
    faq_per_1k = (analysis["faq_item_count"] / wc) * 1000
    faq_density = clamp(faq_per_1k * 20)  # 5 items/1000 words = 100

    # trust_depth: trust editorial block + source block + disclosure
    trust_signals = sum([
        analysis["has_trust_editorial"],
        analysis["has_sources"],
        analysis["has_disclosure"],
    ])
    trust_depth = clamp((trust_signals / 3) * 100)

    # source_quality: authoritative source citation count
    source_quality = clamp(analysis["source_citation_count"] * 15, 0, 100)

    return {
        "authority_density": round(authority_density, 1),
        "citation_confidence": round(citation_confidence, 1),
        "quick_answer_coverage": round(quick_answer_coverage, 1),
        "snippet_readiness": round(snippet_readiness, 1),
        "faq_density": round(faq_density, 1),
        "trust_depth": round(trust_depth, 1),
        "source_quality": round(source_quality, 1),
    }


def compute_visibility_readiness(scores):
    """Weighted VRS formula."""
    vrs = (
        scores["authority_density"] * 0.20
        + scores["citation_confidence"] * 0.15
        + scores["quick_answer_coverage"] * 0.15
        + scores["snippet_readiness"] * 0.15
        + scores["faq_density"] * 0.10
        + scores["trust_depth"] * 0.15
        + scores["source_quality"] * 0.10
    )
    return round(vrs, 1)


def grade(score):
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    else:
        return "D"


# ─── Cluster Leadership Scoring ──────────────────────────────────────────────
def compute_cluster_leadership(cluster_name, posts_in_cluster, all_analyzed):
    """Compute all six leadership dimensions for a cluster."""
    n = len(posts_in_cluster)
    if n == 0:
        return None

    # Get all cluster sizes for normalization
    cluster_sizes = defaultdict(int)
    for p in all_analyzed:
        cluster_sizes[p["cluster"]] += 1
    max_cluster_size = max(cluster_sizes.values()) if cluster_sizes else 1

    # 1. Ownership: relative cluster size
    ownership_score = clamp((n / max_cluster_size) * 100)

    # 2. Trust depth: average trust signals per post
    total_trust_links = sum(1 for p in posts_in_cluster if p["has_trust_editorial"])
    total_sources = sum(1 for p in posts_in_cluster if p["has_sources"])
    total_editorial = sum(1 for p in posts_in_cluster if p["has_trust_editorial"])
    total_citations = sum(p["source_citation_count"] for p in posts_in_cluster)

    trust_pct = ((total_trust_links + total_sources + total_editorial) / (n * 3)) * 100
    citation_bonus = clamp(total_citations / n * 10, 0, 20)
    trust_depth_score = clamp(trust_pct + citation_bonus)

    # 3. Citation confidence: sources + structured data + tables
    posts_with_sources = sum(1 for p in posts_in_cluster if p["has_sources"])
    posts_with_structured = sum(1 for p in posts_in_cluster if p["has_structured_data"])
    posts_with_tables = sum(1 for p in posts_in_cluster if p["has_table"])
    citation_confidence_score = clamp(
        ((posts_with_sources + posts_with_structured + posts_with_tables) / (n * 3)) * 100
    )

    # 4. AI preference: question H2 density + answer block coverage
    total_h2 = sum(p["h2_count"] for p in posts_in_cluster)
    total_q_h2 = sum(p["question_h2_count"] for p in posts_in_cluster)
    q_h2_pct = (total_q_h2 / total_h2 * 100) if total_h2 > 0 else 0
    posts_with_quick = sum(1 for p in posts_in_cluster if p["has_quick_answer"])
    quick_pct = (posts_with_quick / n) * 100
    ai_preference_score = clamp(q_h2_pct * 0.5 + quick_pct * 0.5)

    # 5. Moat: internal link density within cluster
    total_internal_links = sum(p["internal_link_count"] for p in posts_in_cluster)
    avg_internal = total_internal_links / n if n > 0 else 0
    # More internal links = stronger moat; 10+ links/post = 100
    moat_score = clamp(avg_internal * 10)

    # 6. Visibility potential: snippet readiness + quick-answer coverage
    posts_with_faq = sum(1 for p in posts_in_cluster if p["has_faq"])
    faq_pct = (posts_with_faq / n) * 100
    visibility_potential_score = clamp(q_h2_pct * 0.3 + quick_pct * 0.4 + faq_pct * 0.3)

    # Weighted leadership score
    leadership_score = (
        ownership_score * 0.15
        + trust_depth_score * 0.15
        + citation_confidence_score * 0.15
        + ai_preference_score * 0.15
        + moat_score * 0.20
        + visibility_potential_score * 0.20
    )

    return {
        "cluster": cluster_name,
        "posts": n,
        "ownership_score": round(ownership_score, 1),
        "trust_depth_score": round(trust_depth_score, 1),
        "citation_confidence_score": round(citation_confidence_score, 1),
        "ai_preference_score": round(ai_preference_score, 1),
        "moat_score": round(moat_score, 1),
        "visibility_potential_score": round(visibility_potential_score, 1),
        "leadership_score": round(leadership_score, 1),
        "grade": grade(leadership_score),
    }


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("CLUSTER LEADERSHIP ENGINE - PetHubOnline.com")
    print("=" * 70)

    # Step 1: Fetch all posts
    print("\n[1/5] Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}")

    # Step 2: Analyze each post
    print("\n[2/5] Analyzing post content...")
    analyzed = []
    for i, post in enumerate(posts):
        a = analyze_post(post)
        analyzed.append(a)
        if (i + 1) % 25 == 0:
            print(f"  Analyzed {i + 1}/{len(posts)} posts")
    print(f"  Analysis complete: {len(analyzed)} posts")

    # Step 3: Group by cluster
    print("\n[3/5] Grouping by cluster...")
    clusters = defaultdict(list)
    for a in analyzed:
        clusters[a["cluster"]].append(a)
    for c, posts_list in sorted(clusters.items(), key=lambda x: -len(x[1])):
        print(f"  {c}: {len(posts_list)} posts")

    # Step 4: Compute scores and generate CSVs
    print("\n[4/5] Computing scores and generating data products...")

    # ── Product 1: Cluster Leadership Rankings ─────────────────────────────
    leadership_rows = []
    for cluster_name, cluster_posts in clusters.items():
        result = compute_cluster_leadership(cluster_name, cluster_posts, analyzed)
        if result:
            leadership_rows.append(result)

    # Sort by leadership score descending
    leadership_rows.sort(key=lambda x: -x["leadership_score"])
    for i, row in enumerate(leadership_rows):
        row["rank"] = i + 1

    leadership_file = os.path.join(OUTPUT_DIR, "Cluster_Leadership_Rankings.csv")
    with open(leadership_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "rank", "cluster", "posts", "ownership_score", "trust_depth_score",
            "citation_confidence_score", "ai_preference_score", "moat_score",
            "visibility_potential_score", "leadership_score", "grade",
        ])
        writer.writeheader()
        writer.writerows(leadership_rows)
    print(f"  Written: {leadership_file}")

    # ── Product 2a: Visibility Readiness (per-post) ────────────────────────
    post_vrs_rows = []
    for a in analyzed:
        scores = compute_post_scores(a)
        vrs = compute_visibility_readiness(scores)
        post_vrs_rows.append({
            "post_id": a["post_id"],
            "title": a["title"],
            "cluster": a["cluster"],
            **scores,
            "visibility_readiness_score": vrs,
            "grade": grade(vrs),
        })

    # Sort by VRS descending
    post_vrs_rows.sort(key=lambda x: -x["visibility_readiness_score"])

    post_vrs_file = os.path.join(OUTPUT_DIR, "Visibility_Readiness_Posts.csv")
    with open(post_vrs_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "authority_density",
            "citation_confidence", "quick_answer_coverage", "snippet_readiness",
            "faq_density", "trust_depth", "source_quality",
            "visibility_readiness_score", "grade",
        ])
        writer.writeheader()
        writer.writerows(post_vrs_rows)
    print(f"  Written: {post_vrs_file}")

    # ── Product 2b: Visibility Readiness (per-cluster) ─────────────────────
    cluster_vrs_rows = []
    for cluster_name, cluster_posts in clusters.items():
        n = len(cluster_posts)
        if n == 0:
            continue

        # Compute scores for each post in cluster
        cluster_scores = []
        for a in cluster_posts:
            s = compute_post_scores(a)
            s["vrs"] = compute_visibility_readiness(s)
            cluster_scores.append(s)

        avg_ad = sum(s["authority_density"] for s in cluster_scores) / n
        avg_cc = sum(s["citation_confidence"] for s in cluster_scores) / n
        quick_pct = sum(1 for s in cluster_scores if s["quick_answer_coverage"] == 100) / n * 100
        avg_sr = sum(s["snippet_readiness"] for s in cluster_scores) / n
        avg_fd = sum(s["faq_density"] for s in cluster_scores) / n
        avg_td = sum(s["trust_depth"] for s in cluster_scores) / n
        avg_sq = sum(s["source_quality"] for s in cluster_scores) / n

        cluster_vrs = (
            avg_ad * 0.20
            + avg_cc * 0.15
            + quick_pct * 0.15
            + avg_sr * 0.15
            + avg_fd * 0.10
            + avg_td * 0.15
            + avg_sq * 0.10
        )

        cluster_vrs_rows.append({
            "cluster": cluster_name,
            "posts": n,
            "avg_authority_density": round(avg_ad, 1),
            "avg_citation_confidence": round(avg_cc, 1),
            "quick_answer_pct": round(quick_pct, 1),
            "avg_snippet_readiness": round(avg_sr, 1),
            "avg_faq_density": round(avg_fd, 1),
            "avg_trust_depth": round(avg_td, 1),
            "avg_source_quality": round(avg_sq, 1),
            "visibility_readiness_score": round(cluster_vrs, 1),
            "grade": grade(cluster_vrs),
        })

    cluster_vrs_rows.sort(key=lambda x: -x["visibility_readiness_score"])

    cluster_vrs_file = os.path.join(OUTPUT_DIR, "Visibility_Readiness_Clusters.csv")
    with open(cluster_vrs_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cluster", "posts", "avg_authority_density", "avg_citation_confidence",
            "quick_answer_pct", "avg_snippet_readiness", "avg_faq_density",
            "avg_trust_depth", "avg_source_quality", "visibility_readiness_score",
            "grade",
        ])
        writer.writeheader()
        writer.writerows(cluster_vrs_rows)
    print(f"  Written: {cluster_vrs_file}")

    # Step 5: Summary report
    print("\n[5/5] RESULTS SUMMARY")
    print("=" * 70)

    print("\n--- CLUSTER LEADERSHIP RANKINGS ---")
    print(f"{'Rank':<5} {'Cluster':<20} {'Posts':<6} {'Score':<8} {'Grade'}")
    print("-" * 50)
    for row in leadership_rows:
        print(f"{row['rank']:<5} {row['cluster']:<20} {row['posts']:<6} {row['leadership_score']:<8} {row['grade']}")

    print(f"\n--- VISIBILITY READINESS (Clusters) ---")
    print(f"{'Cluster':<20} {'Posts':<6} {'VRS':<8} {'Grade'}")
    print("-" * 45)
    for row in cluster_vrs_rows:
        print(f"{row['cluster']:<20} {row['posts']:<6} {row['visibility_readiness_score']:<8} {row['grade']}")

    # Top/bottom posts
    print(f"\n--- TOP 10 POSTS by Visibility Readiness ---")
    for row in post_vrs_rows[:10]:
        print(f"  [{row['grade']}] {row['visibility_readiness_score']:>5} | {row['title'][:60]}")

    print(f"\n--- BOTTOM 10 POSTS by Visibility Readiness ---")
    for row in post_vrs_rows[-10:]:
        print(f"  [{row['grade']}] {row['visibility_readiness_score']:>5} | {row['title'][:60]}")

    print(f"\n--- GRADE DISTRIBUTION (Posts) ---")
    grade_counts = defaultdict(int)
    for row in post_vrs_rows:
        grade_counts[row["grade"]] += 1
    for g in ["A", "B", "C", "D"]:
        print(f"  {g}: {grade_counts.get(g, 0)} posts")

    print(f"\nTotal posts analyzed: {len(analyzed)}")
    print(f"Total clusters: {len(clusters)}")
    print(f"\nOutput files:")
    print(f"  {leadership_file}")
    print(f"  {post_vrs_file}")
    print(f"  {cluster_vrs_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
