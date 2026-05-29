#!/usr/bin/env python3
"""
PetHub Online - Phase 10AG-10AN Authority Telemetry Report Generator
Fetches all published posts and generates 8 comprehensive CSV reports.
"""

import subprocess
import json
import csv
import re
import os
import sys
from html.parser import HTMLParser
from collections import defaultdict
from datetime import datetime

# ─── Configuration ───────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ag_data"

# ─── Cluster Classification ─────────────────────────────────────────────────
CLUSTER_RULES = [
    ("Indoor Cats", ["indoor cat"]),
    ("Cat Toys", ["cat toy", "catnip", "interactive cat", "cat scratching", "cat tree"]),
    ("Cat Supplies", ["cat litter", "cat bed", "cat supplies", "cat collar", "cat harness",
                       "heated cat", "cat radiator", "cat window"]),
    ("Dog Beds", ["dog bed", "orthopaedic", "cooling bed", "puppy bed"]),
    ("Dog Food", ["dog food", "nutrition", "feeding", "dry vs wet", "puppy food"]),
    ("Dog Grooming", ["grooming", "brush", "shampoo", "nail clip", "cat brush",
                       "cat shampoo", "cat nail", "cat grooming"]),
    ("Dog Harnesses", ["harness", "collar", "lead", "no-pull", "puppy collar",
                        "cat harness", "cat collar"]),
    ("Dog Health", ["health", "flea", "dental", "joint supplement"]),
    ("Dog Training", ["training", "behaviour", "socialisation", "treat", "scratching behaviour"]),
    ("Dog Toys", ["dog toy", "enrichment", "fetch", "tug", "chew", "puzzle", "boredom",
                   "play style", "overstimulation", "pet toy safety", "cat toy safety",
                   "cat enrichment", "cat toy rotation"]),
    ("Puppy Care", ["puppy"]),
    ("Dog Care", ["seasonal dog", "seasonal pet"]),
    ("Educational", ["glossary", "explained", "guide"]),
]


def classify_cluster(title):
    """Classify a post into a cluster based on title keywords."""
    title_lower = title.lower()
    for cluster_name, keywords in CLUSTER_RULES:
        for kw in keywords:
            if kw in title_lower:
                return cluster_name
    return "Uncategorized"


class TextExtractor(HTMLParser):
    """Extract plain text from HTML."""
    def __init__(self):
        super().__init__()
        self._text = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self._text.append(data)

    def get_text(self):
        return ' '.join(self._text)


def html_to_text(html):
    """Convert HTML to plain text."""
    extractor = TextExtractor()
    try:
        extractor.feed(html or "")
    except Exception:
        pass
    return extractor.get_text()


def word_count(html):
    """Count words in HTML content."""
    text = html_to_text(html)
    words = text.split()
    return len(words)


def fetch_all_posts():
    """Fetch all published posts from WordPress API with pagination."""
    posts = []
    page = 1
    while True:
        url = f"{WP_API}/posts?per_page=100&page={page}&context=edit&status=publish"
        print(f"  Fetching page {page}...", flush=True)
        r = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=120
        )
        if r.returncode != 0:
            print(f"  curl error on page {page}: {r.stderr}", file=sys.stderr)
            break
        try:
            batch = json.loads(r.stdout)
        except json.JSONDecodeError:
            print(f"  JSON decode error on page {page}. Response: {r.stdout[:300]}", file=sys.stderr)
            break
        if not isinstance(batch, list) or len(batch) == 0:
            # Could be an error object like {"code":"rest_post_invalid_page_number",...}
            if isinstance(batch, dict) and batch.get("code"):
                print(f"  API says: {batch.get('code')} - stopping pagination.", flush=True)
            break
        posts.extend(batch)
        print(f"  Got {len(batch)} posts (total: {len(posts)})", flush=True)
        if len(batch) < 100:
            break
        page += 1
    return posts


def analyze_post(post):
    """Analyze a single post and return metrics dict."""
    pid = post.get("id", 0)
    title_raw = post.get("title", {})
    if isinstance(title_raw, dict):
        title = title_raw.get("rendered", title_raw.get("raw", ""))
    else:
        title = str(title_raw)
    # Decode HTML entities in title
    title = re.sub(r'&#8217;', "'", title)
    title = re.sub(r'&#8211;', "-", title)
    title = re.sub(r'&#8220;', '"', title)
    title = re.sub(r'&#8221;', '"', title)
    title = re.sub(r'&#038;', '&', title)
    title = re.sub(r'&amp;', '&', title)
    title = re.sub(r'<[^>]+>', '', title)

    content_raw = post.get("content", {})
    if isinstance(content_raw, dict):
        content = content_raw.get("rendered", content_raw.get("raw", ""))
    else:
        content = str(content_raw)

    cluster = classify_cluster(title)
    wc = word_count(content)
    content_lower = content.lower()

    # ── FAQ detection ──
    has_faq = bool(
        re.search(r'(?i)(frequently\s+asked\s+questions|faq)', content) or
        re.search(r'(?i)<h[2-4][^>]*>.*?faq.*?</h[2-4]>', content)
    )
    # Count FAQ questions (look for patterns like <strong>Q: or <h3> inside FAQ section, or <dt>, or numbered Q&A)
    faq_questions = []
    if has_faq:
        # Look for question patterns after FAQ heading
        faq_section = re.split(r'(?i)(frequently\s+asked\s+questions|faq)', content)
        faq_text = faq_section[-1] if len(faq_section) > 1 else content
        # Count headings that look like questions (h3/h4 with ?)
        faq_questions = re.findall(r'<h[3-4][^>]*>[^<]*\?[^<]*</h[3-4]>', faq_text, re.IGNORECASE)
        # Also count <strong> questions and <dt> items
        faq_questions += re.findall(r'<strong>[^<]*\?[^<]*</strong>', faq_text)
        faq_questions += re.findall(r'<dt>[^<]*\?[^<]*</dt>', faq_text)
    faq_count = len(faq_questions)

    # ── Sources detection ──
    has_sources = bool(
        re.search(r'(?i)(sources?\s+and\s+further\s+reading|references|bibliography|sources)', content)
    )
    # Count source links in sources section
    source_count = 0
    if has_sources:
        sources_section = re.split(r'(?i)(sources?\s+and\s+further\s+reading|references|bibliography)', content)
        if len(sources_section) > 1:
            src_text = sources_section[-1]
            source_count = len(re.findall(r'<a\s+[^>]*href=', src_text, re.IGNORECASE))

    # ── Quick Answer detection ──
    has_quick_answer = bool(
        re.search(r'(?i)(quick\s+answer|key\s+takeaway|tldr|tl;dr|at\s+a\s+glance)', content)
    )

    # ── Comparison Table detection ──
    has_comparison_table = bool(
        re.search(r'(?i)wp:table', content) or
        re.search(r'<table', content) or
        re.search(r'(?i)(comparison|vs\.?|versus)', content) and re.search(r'<table', content)
    )
    # More precise: table with comparison keywords
    has_real_comparison = bool(
        re.search(r'<table', content, re.IGNORECASE) and
        re.search(r'(?i)(comparison|vs\.?|versus|pros?\s+(and|&)\s+cons?|feature)', content)
    )

    # ── Trust Links detection ──
    has_editorial_standards = bool(
        re.search(r'(?i)our\s+editorial\s+standards', content) or
        re.search(r'(?i)editorial.standards', content)
    )
    has_methodology_link = bool(
        re.search(r'(?i)(methodology|how\s+we\s+(test|review|rate|evaluate))', content)
    )
    has_corrections_link = bool(
        re.search(r'(?i)(corrections?\s+policy|report\s+an?\s+error|errata)', content)
    )
    has_affiliate_disclosure = bool(
        re.search(r'(?i)(affiliate\s+disclosure|affiliate\s+link|commission|sponsored)', content)
    )
    has_trust_links = has_editorial_standards or has_methodology_link or has_corrections_link

    # ── Glossary terms ──
    has_glossary_terms = bool(
        re.search(r'(?i)(glossary|terminology|definitions?|key\s+terms)', content)
    )
    glossary_term_count = 0
    if has_glossary_terms:
        glossary_section = re.split(r'(?i)(glossary|terminology|definitions?|key\s+terms)', content)
        if len(glossary_section) > 1:
            gl_text = glossary_section[-1]
            # Count <dt> or <strong> definitions or <li> items
            glossary_term_count = max(
                len(re.findall(r'<dt>', gl_text)),
                len(re.findall(r'<li>', gl_text)),
                len(re.findall(r'<strong>[^<]+</strong>\s*[-:–]', gl_text))
            )

    # ── Link counting ──
    all_links = re.findall(r'<a\s+[^>]*href=["\']([^"\']*)["\']', content, re.IGNORECASE)
    internal_links = [l for l in all_links if 'pethubonline.com' in l]
    external_links = [l for l in all_links if l.startswith('http') and 'pethubonline.com' not in l]
    internal_link_count = len(internal_links)
    external_link_count = len(external_links)

    # ── Heading count ──
    headings = re.findall(r'<h[1-6][^>]*>', content, re.IGNORECASE)
    heading_count = len(headings)

    # ── Structured data ──
    has_structured_data = bool(
        re.search(r'(?i)(schema|application/ld\+json|itemtype|itemscope)', content)
    )

    # ── List density ──
    list_items = len(re.findall(r'<li[^>]*>', content, re.IGNORECASE))
    list_density = round(list_items / max(wc, 1) * 100, 2)

    # ── Heading density ──
    heading_density = round(heading_count / max(wc, 1) * 1000, 2)

    # ── Publication date ──
    date_published = post.get("date", "")

    # ── Authority Density Score ──
    # FAQ(15) + Sources(20) + QuickAnswer(10) + Comparison(10) + TrustLinks(15) + InternalLinks(15) + ExternalLinks(15)
    auth_score = 0
    if has_faq:
        auth_score += 15
    if has_sources:
        auth_score += 20
    if has_quick_answer:
        auth_score += 10
    if has_comparison_table:
        auth_score += 10
    if has_trust_links:
        auth_score += 15
    # Internal links: scale 0-15 based on count (5+ = full score)
    auth_score += min(internal_link_count / 5.0, 1.0) * 15
    # External links: scale 0-15 based on count (3+ = full score)
    auth_score += min(external_link_count / 3.0, 1.0) * 15
    auth_score = round(auth_score, 1)

    # ── AI Readiness Score ──
    ai_score = 0
    if has_quick_answer:
        ai_score += 20
    if has_faq:
        ai_score += 20
    if has_structured_data:
        ai_score += 15
    if has_comparison_table:
        ai_score += 10
    if has_sources:
        ai_score += 10
    # Heading density bonus (well-structured content)
    if heading_density >= 3:
        ai_score += 10
    elif heading_density >= 1.5:
        ai_score += 5
    # List density bonus
    if list_density >= 2:
        ai_score += 10
    elif list_density >= 1:
        ai_score += 5
    # Word count bonus (comprehensive content)
    if wc >= 2000:
        ai_score += 5
    elif wc >= 1000:
        ai_score += 3
    ai_score = min(ai_score, 100)

    # ── Trust Density Score ──
    trust_score = 0
    if has_editorial_standards:
        trust_score += 25
    if has_methodology_link:
        trust_score += 20
    if has_corrections_link:
        trust_score += 15
    if has_affiliate_disclosure:
        trust_score += 15
    if has_sources:
        trust_score += 15
    # Source quality: based on count of sources
    if source_count >= 5:
        source_quality = "high"
        trust_score += 10
    elif source_count >= 2:
        source_quality = "medium"
        trust_score += 5
    elif source_count >= 1:
        source_quality = "low"
        trust_score += 2
    else:
        source_quality = "none"
    trust_score = min(trust_score, 100)

    # ── Cross-cluster linking ──
    linked_clusters = set()
    for link in internal_links:
        # Try to extract slug and guess cluster from link text
        # We'll do a second pass for this after all posts are analyzed
        pass

    # ── Comparison usefulness ──
    comparison_usefulness = 0
    if has_comparison_table:
        if has_real_comparison:
            comparison_usefulness = 80
        else:
            comparison_usefulness = 40
        if wc >= 1500:
            comparison_usefulness += 10
        if has_sources:
            comparison_usefulness += 10
        comparison_usefulness = min(comparison_usefulness, 100)

    # ── Recommended table topic ──
    recommended_table = ""
    if not has_comparison_table:
        title_lower = title.lower()
        if "vs" in title_lower or "versus" in title_lower or "compare" in title_lower:
            recommended_table = "Direct product comparison table"
        elif "best" in title_lower or "top" in title_lower:
            recommended_table = "Feature comparison of top picks"
        elif "review" in title_lower:
            recommended_table = "Pros vs cons summary table"
        elif any(k in title_lower for k in ["food", "nutrition", "feeding"]):
            recommended_table = "Nutritional comparison table"
        elif any(k in title_lower for k in ["toy", "enrichment"]):
            recommended_table = "Toy type comparison (features/age/price)"
        elif any(k in title_lower for k in ["bed", "crate"]):
            recommended_table = "Bed size/material comparison table"
        elif any(k in title_lower for k in ["harness", "collar", "lead"]):
            recommended_table = "Harness type comparison table"
        elif any(k in title_lower for k in ["grooming", "brush", "shampoo"]):
            recommended_table = "Grooming tool comparison table"
        elif any(k in title_lower for k in ["health", "supplement"]):
            recommended_table = "Health supplement comparison table"
        elif any(k in title_lower for k in ["training", "behaviour"]):
            recommended_table = "Training method comparison table"
        else:
            recommended_table = "Product/feature comparison relevant to topic"

    return {
        "id": pid,
        "title": title,
        "cluster": cluster,
        "word_count": wc,
        "has_faq": has_faq,
        "faq_count": faq_count,
        "has_sources": has_sources,
        "source_count": source_count,
        "has_quick_answer": has_quick_answer,
        "has_comparison_table": has_comparison_table,
        "has_real_comparison": has_real_comparison,
        "has_trust_links": has_trust_links,
        "has_editorial_standards": has_editorial_standards,
        "has_methodology_link": has_methodology_link,
        "has_corrections_link": has_corrections_link,
        "has_affiliate_disclosure": has_affiliate_disclosure,
        "has_glossary_terms": has_glossary_terms,
        "glossary_term_count": glossary_term_count,
        "has_structured_data": has_structured_data,
        "internal_link_count": internal_link_count,
        "external_link_count": external_link_count,
        "internal_links": internal_links,
        "heading_count": heading_count,
        "heading_density": heading_density,
        "list_density": list_density,
        "authority_density_score": auth_score,
        "ai_readiness_score": ai_score,
        "trust_density_score": trust_score,
        "source_quality": source_quality,
        "date_published": date_published,
        "comparison_usefulness": comparison_usefulness,
        "recommended_table": recommended_table,
    }


def compute_semantic_flow(analyzed_posts):
    """Compute cross-cluster linking metrics for each post."""
    # Build a map of URL slug -> cluster
    slug_cluster = {}
    for p in analyzed_posts:
        # Extract slug from title (rough approximation)
        slug = re.sub(r'[^a-z0-9]+', '-', p["title"].lower()).strip('-')
        slug_cluster[slug] = p["cluster"]

    for p in analyzed_posts:
        linked_clusters = set()
        cross_cluster = 0
        for link in p["internal_links"]:
            # Extract slug from URL
            slug_match = re.search(r'pethubonline\.com/([^/\?#]+)', link)
            if slug_match:
                link_slug = slug_match.group(1).lower()
                # Try to find matching cluster
                for known_slug, clust in slug_cluster.items():
                    if link_slug in known_slug or known_slug in link_slug:
                        linked_clusters.add(clust)
                        if clust != p["cluster"]:
                            cross_cluster += 1
                        break

        p["unique_clusters_linked"] = len(linked_clusters)
        p["cross_cluster_links"] = cross_cluster
        p["orphan_risk"] = "high" if p["internal_link_count"] == 0 else (
            "medium" if p["internal_link_count"] <= 2 else "low"
        )
        # Semantic coverage: ratio of clusters linked vs total clusters
        total_clusters = len(set(pp["cluster"] for pp in analyzed_posts))
        p["semantic_coverage_score"] = round(
            len(linked_clusters) / max(total_clusters, 1) * 100, 1
        )


def write_csv(filepath, fieldnames, rows):
    """Write rows to CSV."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"  Wrote {len(rows)} rows to {os.path.basename(filepath)}")


def bool_to_str(val):
    return "yes" if val else "no"


def main():
    print("=" * 70)
    print("PetHub Online - Phase 10AG-10AN Telemetry Report Generator")
    print("=" * 70)

    # ── Step 1: Fetch all posts ──
    print("\n[1/3] Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}")

    if not posts:
        print("ERROR: No posts fetched. Exiting.")
        sys.exit(1)

    # ── Step 2: Analyze each post ──
    print("\n[2/3] Analyzing posts...")
    analyzed = []
    for i, post in enumerate(posts):
        metrics = analyze_post(post)
        analyzed.append(metrics)
        if (i + 1) % 20 == 0:
            print(f"  Analyzed {i + 1}/{len(posts)}...", flush=True)
    print(f"  Analysis complete: {len(analyzed)} posts processed.")

    # Compute semantic flow (needs all posts analyzed first)
    compute_semantic_flow(analyzed)

    # ── Step 3: Generate CSVs ──
    print("\n[3/3] Generating CSV reports...")

    # CSV 1: Authority Density Scores
    write_csv(
        os.path.join(OUTPUT_DIR, "authority_density_scores.csv"),
        ["id", "title", "cluster", "word_count", "has_faq", "faq_count",
         "has_sources", "source_count", "has_quick_answer", "has_comparison_table",
         "has_trust_links", "has_glossary_terms", "internal_link_count",
         "external_link_count", "heading_count", "authority_density_score"],
        [{
            **p,
            "has_faq": bool_to_str(p["has_faq"]),
            "has_sources": bool_to_str(p["has_sources"]),
            "has_quick_answer": bool_to_str(p["has_quick_answer"]),
            "has_comparison_table": bool_to_str(p["has_comparison_table"]),
            "has_trust_links": bool_to_str(p["has_trust_links"]),
            "has_glossary_terms": bool_to_str(p["has_glossary_terms"]),
        } for p in analyzed]
    )

    # CSV 2: AI Readiness Scores
    write_csv(
        os.path.join(OUTPUT_DIR, "ai_readiness_scores.csv"),
        ["id", "title", "cluster", "has_quick_answer", "has_faq",
         "has_structured_data", "has_comparison_table", "has_sources",
         "word_count", "heading_density", "list_density", "ai_readiness_score"],
        [{
            **p,
            "has_quick_answer": bool_to_str(p["has_quick_answer"]),
            "has_faq": bool_to_str(p["has_faq"]),
            "has_structured_data": bool_to_str(p["has_structured_data"]),
            "has_comparison_table": bool_to_str(p["has_comparison_table"]),
            "has_sources": bool_to_str(p["has_sources"]),
        } for p in analyzed]
    )

    # CSV 3: Trust Density Scores
    write_csv(
        os.path.join(OUTPUT_DIR, "trust_density_scores.csv"),
        ["id", "title", "cluster", "has_editorial_standards", "has_methodology_link",
         "has_corrections_link", "has_affiliate_disclosure", "has_sources",
         "source_quality", "trust_density_score"],
        [{
            **p,
            "has_editorial_standards": bool_to_str(p["has_editorial_standards"]),
            "has_methodology_link": bool_to_str(p["has_methodology_link"]),
            "has_corrections_link": bool_to_str(p["has_corrections_link"]),
            "has_affiliate_disclosure": bool_to_str(p["has_affiliate_disclosure"]),
            "has_sources": bool_to_str(p["has_sources"]),
        } for p in analyzed]
    )

    # CSV 4: Cluster Authority Summary
    clusters = defaultdict(list)
    for p in analyzed:
        clusters[p["cluster"]].append(p)

    cluster_summary = []
    for cluster_name, cluster_posts in sorted(clusters.items()):
        n = len(cluster_posts)
        avg_wc = round(sum(p["word_count"] for p in cluster_posts) / n, 1)
        avg_auth = round(sum(p["authority_density_score"] for p in cluster_posts) / n, 1)
        avg_ai = round(sum(p["ai_readiness_score"] for p in cluster_posts) / n, 1)
        avg_trust = round(sum(p["trust_density_score"] for p in cluster_posts) / n, 1)
        faq_pct = round(sum(1 for p in cluster_posts if p["has_faq"]) / n * 100, 1)
        src_pct = round(sum(1 for p in cluster_posts if p["has_sources"]) / n * 100, 1)
        trust_pct = round(sum(1 for p in cluster_posts if p["has_trust_links"]) / n * 100, 1)
        comp_pct = round(sum(1 for p in cluster_posts if p["has_comparison_table"]) / n * 100, 1)
        gl_count = sum(p["glossary_term_count"] for p in cluster_posts)

        cluster_summary.append({
            "cluster": cluster_name,
            "post_count": n,
            "avg_word_count": avg_wc,
            "avg_authority_score": avg_auth,
            "avg_ai_readiness": avg_ai,
            "avg_trust_density": avg_trust,
            "faq_coverage_pct": faq_pct,
            "source_coverage_pct": src_pct,
            "trust_link_coverage_pct": trust_pct,
            "comparison_table_pct": comp_pct,
            "glossary_count": gl_count,
        })

    write_csv(
        os.path.join(OUTPUT_DIR, "cluster_authority_summary.csv"),
        ["cluster", "post_count", "avg_word_count", "avg_authority_score",
         "avg_ai_readiness", "avg_trust_density", "faq_coverage_pct",
         "source_coverage_pct", "trust_link_coverage_pct", "comparison_table_pct",
         "glossary_count"],
        cluster_summary
    )

    # CSV 5: Publication Velocity Log
    write_csv(
        os.path.join(OUTPUT_DIR, "publication_velocity_log.csv"),
        ["id", "title", "cluster", "status", "date_published", "word_count",
         "authority_score"],
        [{
            **p,
            "status": "publish",
            "authority_score": p["authority_density_score"],
        } for p in sorted(analyzed, key=lambda x: x["date_published"])]
    )

    # CSV 6: Semantic Flow Audit
    write_csv(
        os.path.join(OUTPUT_DIR, "semantic_flow_audit.csv"),
        ["id", "title", "cluster", "internal_links_out", "unique_clusters_linked",
         "cross_cluster_links", "orphan_risk", "semantic_coverage_score"],
        [{
            **p,
            "internal_links_out": p["internal_link_count"],
        } for p in analyzed]
    )

    # CSV 7: FAQ Completeness Report
    faq_rows = []
    for p in analyzed:
        faq_quality = 0
        if p["has_faq"]:
            faq_quality += 40
            if p["faq_count"] >= 5:
                faq_quality += 30
            elif p["faq_count"] >= 3:
                faq_quality += 20
            elif p["faq_count"] >= 1:
                faq_quality += 10
            if p["has_quick_answer"]:
                faq_quality += 20
            if p["has_sources"]:
                faq_quality += 10
        faq_quality = min(faq_quality, 100)

        faq_rows.append({
            **p,
            "has_faq": bool_to_str(p["has_faq"]),
            "faq_question_count": p["faq_count"],
            "has_quick_answer": bool_to_str(p["has_quick_answer"]),
            "faq_quality_score": faq_quality,
        })

    write_csv(
        os.path.join(OUTPUT_DIR, "faq_completeness_report.csv"),
        ["id", "title", "cluster", "has_faq", "faq_question_count",
         "has_quick_answer", "faq_quality_score"],
        faq_rows
    )

    # CSV 8: Comparison Table Gaps
    write_csv(
        os.path.join(OUTPUT_DIR, "comparison_table_gaps.csv"),
        ["id", "title", "cluster", "has_comparison_table",
         "comparison_usefulness_score", "recommended_table_topic"],
        [{
            **p,
            "has_comparison_table": bool_to_str(p["has_comparison_table"]),
            "comparison_usefulness_score": p["comparison_usefulness"],
            "recommended_table_topic": p["recommended_table"],
        } for p in analyzed]
    )

    # ── Summary ──
    print("\n" + "=" * 70)
    print("REPORT GENERATION COMPLETE")
    print("=" * 70)
    print(f"  Total posts analyzed: {len(analyzed)}")
    print(f"  Clusters found: {len(clusters)}")
    for cname, cposts in sorted(clusters.items()):
        print(f"    - {cname}: {len(cposts)} posts")
    print(f"\n  Output directory: {OUTPUT_DIR}")
    print("  Files generated:")
    for fname in sorted(os.listdir(OUTPUT_DIR)):
        if fname.endswith('.csv'):
            fpath = os.path.join(OUTPUT_DIR, fname)
            size = os.path.getsize(fpath)
            print(f"    - {fname} ({size:,} bytes)")

    # Print key metrics
    avg_auth_all = round(sum(p["authority_density_score"] for p in analyzed) / len(analyzed), 1)
    avg_ai_all = round(sum(p["ai_readiness_score"] for p in analyzed) / len(analyzed), 1)
    avg_trust_all = round(sum(p["trust_density_score"] for p in analyzed) / len(analyzed), 1)
    faq_total = sum(1 for p in analyzed if p["has_faq"])
    src_total = sum(1 for p in analyzed if p["has_sources"])
    qa_total = sum(1 for p in analyzed if p["has_quick_answer"])
    tbl_total = sum(1 for p in analyzed if p["has_comparison_table"])
    trust_total = sum(1 for p in analyzed if p["has_trust_links"])
    orphan_high = sum(1 for p in analyzed if p["orphan_risk"] == "high")

    print(f"\n  KEY METRICS:")
    print(f"    Avg Authority Density Score: {avg_auth_all}/100")
    print(f"    Avg AI Readiness Score:      {avg_ai_all}/100")
    print(f"    Avg Trust Density Score:     {avg_trust_all}/100")
    print(f"    FAQ coverage:                {faq_total}/{len(analyzed)} ({round(faq_total/len(analyzed)*100,1)}%)")
    print(f"    Sources coverage:            {src_total}/{len(analyzed)} ({round(src_total/len(analyzed)*100,1)}%)")
    print(f"    Quick Answer coverage:       {qa_total}/{len(analyzed)} ({round(qa_total/len(analyzed)*100,1)}%)")
    print(f"    Comparison tables:           {tbl_total}/{len(analyzed)} ({round(tbl_total/len(analyzed)*100,1)}%)")
    print(f"    Trust links:                 {trust_total}/{len(analyzed)} ({round(trust_total/len(analyzed)*100,1)}%)")
    print(f"    High orphan risk:            {orphan_high}/{len(analyzed)}")


if __name__ == "__main__":
    main()
