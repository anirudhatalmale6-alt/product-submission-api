#!/usr/bin/env python3
"""
Query Ownership Engine + AI Citation Observation Tracker
for pethubonline.com — Phase 11W Data Products

Scans all published WordPress posts via REST API, analyzes content,
and produces three CSV files:
  1. Query_Ownership_Matrix.csv
  2. Query_Ownership_Summary.csv
  3. AI_Citation_Observation.csv
"""

import csv
import json
import os
import re
import subprocess
import sys
import time
import base64
from html.parser import HTMLParser
from collections import defaultdict

# ── Config ──────────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2/posts"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
AUTH_HEADER = "Basic " + base64.b64encode(f"{WP_USER}:{WP_PASS}".encode()).decode()

OUT_DIR = "/var/lib/freelancer/projects/40416335/phase11w_data"

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


# ── HTML helpers ────────────────────────────────────────────────────────
class HTMLTextExtractor(HTMLParser):
    """Strip all HTML tags and return plain text."""
    def __init__(self):
        super().__init__()
        self._parts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self._parts.append(data)

    def get_text(self):
        return " ".join(self._parts)


def strip_html(html_str: str) -> str:
    ext = HTMLTextExtractor()
    ext.feed(html_str or "")
    return ext.get_text()


def extract_headings(html_str: str) -> list:
    """Return list of (level, text) tuples for all headings."""
    pattern = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.I | re.S)
    results = []
    for m in pattern.finditer(html_str or ""):
        level = int(m.group(1))
        text = strip_html(m.group(2)).strip()
        if text:
            results.append((level, text))
    return results


def word_count(text: str) -> int:
    return len(text.split())


def is_question(text: str) -> bool:
    q_starts = (
        "what", "why", "how", "when", "where", "which", "who",
        "can", "do", "does", "is", "are", "should", "will", "could",
    )
    t = text.strip().lower()
    return t.endswith("?") or any(t.startswith(w) for w in q_starts)


def has_list_or_table(html: str) -> bool:
    return bool(re.search(r"<(ul|ol|table)\b", html or "", re.I))


def has_source_citations(html: str, text: str) -> bool:
    indicators = [
        r"according to",
        r"source:",
        r"cited",
        r"study shows",
        r"research",
        r"<a\s[^>]*href=",
        r"reference",
        r"journal",
        r"published in",
        r"experts say",
        r"veterinarian",
        r"vet\s+(recommend|suggest|advise)",
    ]
    combined = (html or "") + " " + (text or "")
    return any(re.search(p, combined, re.I) for p in indicators)


def has_unique_data(text: str) -> bool:
    indicators = [
        r"\d+\s*%", r"\$\d+", r"\d+\s*(lb|kg|oz|inch|cm|mm)",
        r"compared to", r"vs\.?(\s|$)", r"versus",
        r"top \d+", r"best \d+", r"rating",
        r"price range", r"our pick", r"our top",
    ]
    return any(re.search(p, text, re.I) for p in indicators)


# ── WordPress API fetch ─────────────────────────────────────────────────
def fetch_all_posts() -> list:
    """Fetch every published post using subprocess.run + curl."""
    all_posts = []
    page = 1
    while True:
        time.sleep(2)
        url = (
            f"{WP_API}?status=publish&context=edit"
            f"&per_page=100&page={page}&_fields=id,title,slug,categories,content"
        )
        print(f"  Fetching page {page} …", flush=True)
        result = subprocess.run(
            [
                "curl", "-s", "-w", "\n%{http_code}",
                "-H", f"Authorization: {AUTH_HEADER}",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout.strip()
        # Last line is HTTP status code
        lines = output.rsplit("\n", 1)
        if len(lines) == 2:
            body, status = lines
        else:
            body = output
            status = "000"

        status = status.strip()
        if status == "400":
            # Past last page
            print(f"  Page {page}: status {status} — no more pages.", flush=True)
            break

        if status not in ("200",):
            print(f"  WARNING: page {page} returned HTTP {status}", flush=True)
            break

        try:
            posts = json.loads(body)
        except json.JSONDecodeError:
            print(f"  ERROR: could not parse JSON on page {page}", flush=True)
            break

        if not posts:
            break

        all_posts.extend(posts)
        print(f"  Got {len(posts)} posts (total {len(all_posts)})", flush=True)

        if len(posts) < 100:
            break
        page += 1

    return all_posts


# ── Query derivation ────────────────────────────────────────────────────
def derive_target_query(title: str, slug: str) -> str:
    """Derive the primary target query from the post title and slug."""
    # Clean up title
    t = re.sub(r"\s*[|\-–—]\s*PetHub.*$", "", title, flags=re.I).strip()
    t = re.sub(r"\s*\(\d{4}\)$", "", t).strip()
    t = re.sub(r"\s*–\s*\d{4}$", "", t).strip()
    if t:
        return t.lower()
    # Fallback to slug
    return slug.replace("-", " ").lower()


def derive_supporting_queries(title: str, headings: list) -> list:
    """Derive 2-3 supporting queries from H2 headings."""
    supporting = []
    title_lower = title.lower()

    for level, text in headings:
        if level != 2:
            continue
        t = text.strip()
        # Skip very short or generic headings
        if len(t) < 10:
            continue
        if t.lower() in ("conclusion", "final thoughts", "summary",
                         "frequently asked questions", "faq", "faqs",
                         "table of contents", "related posts"):
            continue
        if is_question(t):
            continue  # Questions go to faq_queries
        # Clean and add
        q = t.lower().strip()
        if q and q not in supporting:
            supporting.append(q)

    return supporting[:3]


def derive_faq_queries(headings: list, html_content: str) -> list:
    """Extract FAQ-style questions from headings and FAQ schema blocks."""
    faqs = []

    # From question-format headings
    for level, text in headings:
        t = text.strip()
        if is_question(t):
            q = t.lower().rstrip("?").strip() + "?"
            if q not in faqs:
                faqs.append(q)

    # From FAQ schema / structured FAQ blocks
    # Look for patterns like "question": "..." in JSON-LD
    faq_pattern = re.compile(r'"(?:question|name)"\s*:\s*"([^"]{15,})"', re.I)
    for m in faq_pattern.finditer(html_content or ""):
        q = m.group(1).strip().lower()
        if not q.endswith("?"):
            q += "?"
        if q not in faqs:
            faqs.append(q)

    return faqs


def derive_ai_answer_queries(title: str, cluster: str) -> list:
    """Generate queries formatted for AI citation."""
    queries = []
    title_clean = re.sub(r"\s*[|\-–—]\s*PetHub.*$", "", title, flags=re.I).strip()
    title_clean = re.sub(r"\s*\(\d{4}\)$", "", title_clean).strip()
    t = title_clean.lower()

    # Pattern: "What is the best X?"
    if re.search(r"\bbest\b", t, re.I):
        queries.append(f"what is the {t}?")
    else:
        queries.append(f"what is the best {t}?")

    # Pattern: "How to choose X"
    if re.search(r"\b(choose|pick|select|find)\b", t, re.I):
        queries.append(f"how to {t}?")
    else:
        topic = re.sub(r"^(best|top|ultimate|complete)\s+(guide\s+to\s+)?", "", t).strip()
        if topic:
            queries.append(f"how to choose the best {topic}?")

    return queries[:2]


def derive_competitor_queries(title: str, headings: list) -> list:
    """Extract comparison / alternative queries."""
    queries = []
    all_texts = [title] + [h[1] for h in headings]

    for text in all_texts:
        t = text.strip().lower()
        # "X vs Y" patterns
        if re.search(r"\bvs\.?\b|\bversus\b", t):
            q = re.sub(r"\s*[|\-–—]\s*pethub.*$", "", t, flags=re.I).strip()
            if q and q not in queries:
                queries.append(q)
        # "alternative to X"
        if re.search(r"\balternative", t):
            q = t.strip()
            if q and q not in queries:
                queries.append(q)
        # "X compared to Y"
        if re.search(r"\bcompared?\s+to\b", t):
            q = t.strip()
            if q and q not in queries:
                queries.append(q)

    return queries[:3]


# ── Citability scoring ──────────────────────────────────────────────────
def count_lists_tables(html: str) -> int:
    """Count the number of list and table elements."""
    return len(re.findall(r"<(ul|ol|table)\b", html or "", re.I))


def count_links(html: str) -> int:
    """Count external/internal links as a proxy for citation depth."""
    return len(re.findall(r"<a\s[^>]*href=", html or "", re.I))


def count_h2_headings(headings: list) -> int:
    return sum(1 for lvl, _ in headings if lvl == 2)


def compute_citability_score(
    wc: int,
    faq_count: int,
    h2_count: int,
    list_table_count: int,
    link_count: int,
    html: str,
    plain_text: str,
) -> int:
    """
    Granular citability score (0-100) using degree-based scoring.
    All 168 posts have all boolean signals, so we score on *how much*
    of each signal rather than presence/absence.

    Breakdown (100 pts total):
      - Word count depth:        0-20 pts  (scaled across 2400-7600 range)
      - FAQ richness:            0-20 pts  (scaled across 7-24 FAQs)
      - Content structure depth: 0-15 pts  (H2 heading count)
      - Structured data density: 0-15 pts  (list/table count)
      - Citation/link depth:     0-15 pts  (link count)
      - Data specificity:        0-15 pts  (numbers, comparisons, prices)
    """
    score = 0.0

    # 1. Word count depth (0-20 pts) — linear scale 2400..7600
    wc_min, wc_max = 2400, 7600
    wc_clamped = max(wc_min, min(wc, wc_max))
    score += 20 * (wc_clamped - wc_min) / (wc_max - wc_min)

    # 2. FAQ richness (0-20 pts) — linear scale 7..24
    faq_min, faq_max = 7, 24
    faq_clamped = max(faq_min, min(faq_count, faq_max))
    score += 20 * (faq_clamped - faq_min) / (faq_max - faq_min)

    # 3. Content structure depth (0-15 pts) — H2 headings, scale 5..30
    h2_min, h2_max = 5, 30
    h2_clamped = max(h2_min, min(h2_count, h2_max))
    score += 15 * (h2_clamped - h2_min) / (h2_max - h2_min)

    # 4. Structured data density (0-15 pts) — lists/tables, scale 1..15
    lt_min, lt_max = 1, 15
    lt_clamped = max(lt_min, min(list_table_count, lt_max))
    score += 15 * (lt_clamped - lt_min) / (lt_max - lt_min)

    # 5. Citation/link depth (0-15 pts) — links, scale 5..80
    lk_min, lk_max = 5, 80
    lk_clamped = max(lk_min, min(link_count, lk_max))
    score += 15 * (lk_clamped - lk_min) / (lk_max - lk_min)

    # 6. Data specificity (0-15 pts) — count numeric data points
    specificity_patterns = [
        r"\d+\s*%",                     # percentages
        r"[£$€]\s*\d+",                # prices
        r"\d+\s*(lb|kg|oz|inch|cm|g)\b",  # measurements
        r"\brated\s+\d",                # ratings
        r"\btop\s+\d+\b",              # top-N lists
        r"\d+\s*(out of|/)\s*\d+",     # X out of Y
    ]
    data_points = 0
    for pat in specificity_patterns:
        data_points += len(re.findall(pat, plain_text, re.I))
    dp_min, dp_max = 0, 40
    dp_clamped = max(dp_min, min(data_points, dp_max))
    score += 15 * dp_clamped / dp_max

    return round(score)


def confidence_level(score: int) -> str:
    if score >= 65:
        return "high"
    elif score >= 40:
        return "medium"
    else:
        return "low"


# ── Main ────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Query Ownership Engine + AI Citation Tracker")
    print("pethubonline.com — Phase 11W")
    print("=" * 60)

    # 1. Fetch all posts
    print("\n[1/4] Fetching all published posts …")
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}")

    if not posts:
        print("ERROR: No posts fetched. Aborting.")
        sys.exit(1)

    # 2. Analyze each post
    print("\n[2/4] Analyzing posts …")

    matrix_rows = []
    citation_rows = []
    cluster_stats = defaultdict(lambda: {
        "posts": 0,
        "target": 0,
        "supporting": 0,
        "faq": 0,
        "ai_answer": 0,
        "competitor": 0,
    })

    for i, post in enumerate(posts):
        post_id = post["id"]
        title_raw = post.get("title", {})
        if isinstance(title_raw, dict):
            title = strip_html(title_raw.get("raw", title_raw.get("rendered", "")))
        else:
            title = strip_html(str(title_raw))

        slug = post.get("slug", "")

        content_raw = post.get("content", {})
        if isinstance(content_raw, dict):
            html_content = content_raw.get("raw", content_raw.get("rendered", ""))
        else:
            html_content = str(content_raw)

        plain_text = strip_html(html_content)
        wc = word_count(plain_text)
        headings = extract_headings(html_content)

        # Determine cluster
        cats = post.get("categories", [])
        cluster = "Uncategorized"
        for cat_id in cats:
            if cat_id in CATEGORY_MAP and cat_id != 1:
                cluster = CATEGORY_MAP[cat_id]
                break
        if cluster == "Uncategorized" and 1 in cats:
            cluster = "Uncategorized"

        # ── Query ownership ──
        target_query = derive_target_query(title, slug)
        supporting = derive_supporting_queries(title, headings)
        faqs = derive_faq_queries(headings, html_content)
        ai_answers = derive_ai_answer_queries(title, cluster)
        competitors = derive_competitor_queries(title, headings)

        total_owned = 1 + len(supporting) + len(faqs) + len(ai_answers) + len(competitors)
        # Query density = queries per 500 words
        density = round(total_owned / max(wc / 500, 1), 2) if wc > 0 else 0

        matrix_rows.append({
            "cluster": cluster,
            "post_id": post_id,
            "title": title,
            "slug": slug,
            "target_query": target_query,
            "supporting_queries": "; ".join(supporting),
            "faq_queries": "; ".join(faqs),
            "ai_answer_queries": "; ".join(ai_answers),
            "competitor_queries": "; ".join(competitors),
            "total_owned_queries": total_owned,
            "query_density_score": density,
        })

        # Update cluster stats
        cs = cluster_stats[cluster]
        cs["posts"] += 1
        cs["target"] += 1
        cs["supporting"] += len(supporting)
        cs["faq"] += len(faqs)
        cs["ai_answer"] += len(ai_answers)
        cs["competitor"] += len(competitors)

        # ── AI Citation signals (granular) ──
        structured = has_list_or_table(html_content)
        sources = has_source_citations(html_content, plain_text)
        qa = len(faqs) > 0 or any(is_question(h[1]) for h in headings)
        unique = has_unique_data(plain_text)

        h2_count = count_h2_headings(headings)
        lt_count = count_lists_tables(html_content)
        lk_count = count_links(html_content)

        citability = compute_citability_score(
            wc, len(faqs), h2_count, lt_count, lk_count,
            html_content, plain_text,
        )
        conf = confidence_level(citability)

        # Build notes — descriptive, granular
        notes_parts = []
        notes_parts.append(f"{len(faqs)} FAQs")
        notes_parts.append(f"{h2_count} H2s")
        notes_parts.append(f"{lt_count} lists/tables")
        notes_parts.append(f"{lk_count} links")
        if wc >= 5000:
            notes_parts.append("comprehensive depth")
        elif wc >= 3500:
            notes_parts.append("solid depth")
        else:
            notes_parts.append("moderate depth")

        citation_rows.append({
            "post_id": post_id,
            "title": title,
            "cluster": cluster,
            "url_slug": slug,
            "citation_status": "estimated",
            "citability_score": citability,
            "has_structured_data": "yes" if structured else "no",
            "has_source_citations": "yes" if sources else "no",
            "has_qa_format": "yes" if qa else "no",
            "has_unique_data": "yes" if unique else "no",
            "word_count": wc,
            "confidence_level": conf,
            "notes": "; ".join(notes_parts),
        })

        if (i + 1) % 25 == 0:
            print(f"  Analyzed {i + 1}/{len(posts)} posts …", flush=True)

    print(f"  Analyzed all {len(posts)} posts.")

    # 3. Write CSVs
    print("\n[3/4] Writing CSV files …")

    # Matrix
    matrix_path = os.path.join(OUT_DIR, "Query_Ownership_Matrix.csv")
    matrix_fields = [
        "cluster", "post_id", "title", "slug", "target_query",
        "supporting_queries", "faq_queries", "ai_answer_queries",
        "competitor_queries", "total_owned_queries", "query_density_score",
    ]
    with open(matrix_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=matrix_fields)
        writer.writeheader()
        # Sort by cluster then post_id
        for row in sorted(matrix_rows, key=lambda r: (r["cluster"], r["post_id"])):
            writer.writerow(row)
    print(f"  Written: {matrix_path} ({len(matrix_rows)} rows)")

    # Summary
    summary_path = os.path.join(OUT_DIR, "Query_Ownership_Summary.csv")
    summary_fields = [
        "cluster", "posts", "total_target_queries", "total_supporting",
        "total_faq", "total_ai_answer", "total_competitor",
        "total_queries", "avg_queries_per_post",
    ]
    summary_rows = []
    for cluster_name in sorted(cluster_stats.keys()):
        cs = cluster_stats[cluster_name]
        total_q = cs["target"] + cs["supporting"] + cs["faq"] + cs["ai_answer"] + cs["competitor"]
        avg_q = round(total_q / cs["posts"], 1) if cs["posts"] > 0 else 0
        summary_rows.append({
            "cluster": cluster_name,
            "posts": cs["posts"],
            "total_target_queries": cs["target"],
            "total_supporting": cs["supporting"],
            "total_faq": cs["faq"],
            "total_ai_answer": cs["ai_answer"],
            "total_competitor": cs["competitor"],
            "total_queries": total_q,
            "avg_queries_per_post": avg_q,
        })
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_fields)
        writer.writeheader()
        for row in summary_rows:
            writer.writerow(row)
    print(f"  Written: {summary_path} ({len(summary_rows)} clusters)")

    # AI Citation
    citation_path = os.path.join(OUT_DIR, "AI_Citation_Observation.csv")
    citation_fields = [
        "post_id", "title", "cluster", "url_slug", "citation_status",
        "citability_score", "has_structured_data", "has_source_citations",
        "has_qa_format", "has_unique_data", "word_count",
        "confidence_level", "notes",
    ]
    with open(citation_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=citation_fields)
        writer.writeheader()
        for row in sorted(citation_rows, key=lambda r: (-r["citability_score"], r["post_id"])):
            writer.writerow(row)
    print(f"  Written: {citation_path} ({len(citation_rows)} rows)")

    # 4. Summary report
    print("\n[4/4] Summary Report")
    print("=" * 60)
    print(f"Total published posts scanned: {len(posts)}")
    print(f"Clusters found: {len(cluster_stats)}")

    total_all_q = sum(r["total_owned_queries"] for r in matrix_rows)
    print(f"Total owned queries: {total_all_q}")
    avg_overall = round(total_all_q / len(matrix_rows), 1) if matrix_rows else 0
    print(f"Avg queries per post: {avg_overall}")

    print("\nCluster breakdown:")
    for row in summary_rows:
        print(f"  {row['cluster']:20s}  {row['posts']:3d} posts  {row['total_queries']:4d} queries  avg {row['avg_queries_per_post']}")

    # Citation stats
    scores = [r["citability_score"] for r in citation_rows]
    avg_cite = round(sum(scores) / len(scores), 1) if scores else 0
    high_cite = sum(1 for s in scores if s >= 65)
    med_cite = sum(1 for s in scores if 40 <= s < 65)
    low_cite = sum(1 for s in scores if s < 40)
    print(f"\nAI Citability:")
    print(f"  Average score: {avg_cite}/100")
    print(f"  High confidence: {high_cite} posts")
    print(f"  Medium confidence: {med_cite} posts")
    print(f"  Low confidence: {low_cite} posts")

    print("\nFiles generated:")
    print(f"  {matrix_path}")
    print(f"  {summary_path}")
    print(f"  {citation_path}")
    print("=" * 60)
    print("Done.")


if __name__ == "__main__":
    main()
