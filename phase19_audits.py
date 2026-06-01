#!/usr/bin/env python3
"""
Phase 19 Authority Audit - PetHub Online (pethubonline.com)
Comprehensive content audit: CTA, FAQ, Affiliate, Table, Image compliance.
"""

import json
import re
import time
import sys
import os
from datetime import datetime
from collections import defaultdict
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qs

import requests
from requests.auth import HTTPBasicAuth

# ── Config ──────────────────────────────────────────────────────────────────
WP_API = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
PER_PAGE = 100
DELAY = 0.5
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335"

HEADERS = {
    "Accept-Encoding": "gzip, deflate",
    "User-Agent": "Phase19AuditBot/1.0",
}
AUTH = HTTPBasicAuth(WP_USER, WP_PASS)


# ── HTML helpers ────────────────────────────────────────────────────────────
class LinkExtractor(HTMLParser):
    """Extract all <a href>, <img>, <table>, headings from HTML."""

    def __init__(self):
        super().__init__()
        self.links = []          # (href, text)
        self.images = []         # (src, alt)
        self.tables = 0
        self.table_rows = 0
        self.headings = []       # (tag, text)
        self._current_tag = None
        self._current_attrs = {}
        self._text_buf = []
        self._in_table = False
        self._in_heading = False
        self._in_link = False
        self._link_href = None
        self._scripts = []       # script content for ld+json
        self._in_script = False
        self._script_type = None
        self._script_buf = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag_lower = tag.lower()

        if tag_lower == "a":
            self._in_link = True
            self._link_href = attrs_dict.get("href", "")
            self._text_buf = []

        elif tag_lower == "img":
            src = attrs_dict.get("src", "")
            alt = attrs_dict.get("alt", "")
            self.images.append((src, alt))

        elif tag_lower == "table":
            self.tables += 1
            self._in_table = True

        elif tag_lower == "tr" and self._in_table:
            self.table_rows += 1

        elif tag_lower in ("h1", "h2", "h3", "h4"):
            self._in_heading = True
            self._current_tag = tag_lower
            self._text_buf = []

        elif tag_lower == "script":
            stype = attrs_dict.get("type", "")
            if "ld+json" in stype:
                self._in_script = True
                self._script_buf = []

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower == "a" and self._in_link:
            text = "".join(self._text_buf).strip()
            self.links.append((self._link_href, text))
            self._in_link = False
            self._link_href = None

        elif tag_lower in ("h1", "h2", "h3", "h4") and self._in_heading:
            text = "".join(self._text_buf).strip()
            self.headings.append((self._current_tag, text))
            self._in_heading = False

        elif tag_lower == "table":
            self._in_table = False

        elif tag_lower == "script" and self._in_script:
            self._scripts.append("".join(self._script_buf))
            self._in_script = False

    def handle_data(self, data):
        if self._in_link or self._in_heading:
            self._text_buf.append(data)
        if self._in_script:
            self._script_buf.append(data)


def parse_html(html):
    """Parse HTML and return extracted data."""
    parser = LinkExtractor()
    try:
        parser.feed(html or "")
    except Exception:
        pass
    return parser


# ── Category fetcher ────────────────────────────────────────────────────────
def fetch_categories():
    """Fetch all categories and return {id: name} map."""
    cats = {}
    page = 1
    while True:
        try:
            resp = requests.get(
                f"{WP_API}/categories",
                params={"per_page": 100, "page": page},
                headers=HEADERS,
                auth=AUTH,
                timeout=30,
            )
            if resp.status_code != 200:
                break
            data = resp.json()
            if not data:
                break
            for c in data:
                cats[c["id"]] = c["name"]
            total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
            if page >= total_pages:
                break
            page += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"  [WARN] Category fetch error page {page}: {e}")
            break
    return cats


# ── Post fetcher ────────────────────────────────────────────────────────────
def fetch_all_posts():
    """Fetch all published posts, paginated."""
    all_posts = []
    page = 1

    # First request to get total
    resp = requests.get(
        f"{WP_API}/posts",
        params={
            "per_page": PER_PAGE,
            "page": page,
            "status": "publish",
            "_fields": "id,title,link,categories,content,featured_media",
        },
        headers=HEADERS,
        auth=AUTH,
        timeout=60,
    )
    resp.raise_for_status()
    total_posts = int(resp.headers.get("X-WP-Total", 0))
    total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
    print(f"Total posts reported by API: {total_posts}")
    print(f"Total pages: {total_pages}")

    data = resp.json()
    all_posts.extend(data)
    print(f"  Fetched page 1 — {len(data)} posts (cumulative: {len(all_posts)})")

    for page in range(2, total_pages + 1):
        time.sleep(DELAY)
        try:
            resp = requests.get(
                f"{WP_API}/posts",
                params={
                    "per_page": PER_PAGE,
                    "page": page,
                    "status": "publish",
                    "_fields": "id,title,link,categories,content,featured_media",
                },
                headers=HEADERS,
                auth=AUTH,
                timeout=60,
            )
            if resp.status_code != 200:
                print(f"  [WARN] Page {page} returned {resp.status_code}, skipping")
                continue
            data = resp.json()
            all_posts.extend(data)
            if len(all_posts) % 50 < len(data):
                print(f"  Fetched page {page} — {len(data)} posts (cumulative: {len(all_posts)})")
            else:
                print(f"  Fetched page {page} — {len(data)} posts (cumulative: {len(all_posts)})")
        except Exception as e:
            print(f"  [ERROR] Page {page}: {e}")

    print(f"\nTotal posts fetched: {len(all_posts)}")
    return all_posts


# ── Audit functions ─────────────────────────────────────────────────────────
def is_amazon_affiliate(href):
    """Check if a link is an Amazon affiliate link with pethubonline-21 tag."""
    if not href:
        return False
    href_lower = href.lower()
    if "amazon.co.uk" in href_lower or "amzn.to" in href_lower:
        if "pethubonline-21" in href_lower or "tag=" in href_lower:
            return True
        # amzn.to short links are likely affiliate
        if "amzn.to" in href_lower:
            return True
    return False


def is_internal_link(href):
    """Check if link is internal pethubonline.com."""
    if not href:
        return False
    return "pethubonline.com" in href.lower()


def is_newsletter_cta(href, text):
    """Check if link/text relates to newsletter signup."""
    combined = (href or "").lower() + " " + (text or "").lower()
    keywords = ["mailerlite", "subscribe", "newsletter", "signup", "sign-up", "email list", "join our"]
    return any(kw in combined for kw in keywords)


def audit_cta(parsed):
    """Audit CTA coverage for a post."""
    result = {
        "has_cta": False,
        "types": [],
        "affiliate_count": 0,
        "internal_count": 0,
        "newsletter": False,
        "category_browse": False,
    }

    for href, text in parsed.links:
        if is_amazon_affiliate(href):
            result["affiliate_count"] += 1
            if "affiliate" not in result["types"]:
                result["types"].append("affiliate")

        if is_internal_link(href):
            result["internal_count"] += 1
            if "internal_link" not in result["types"]:
                result["types"].append("internal_link")
            # Check for category browse
            if href and "/category/" in href.lower():
                result["category_browse"] = True
                if "category_browse" not in result["types"]:
                    result["types"].append("category_browse")

        if is_newsletter_cta(href, text):
            result["newsletter"] = True
            if "newsletter" not in result["types"]:
                result["types"].append("newsletter")

    # Also check raw HTML for newsletter/subscribe patterns
    # (some are forms not links)
    result["has_cta"] = len(result["types"]) > 0
    return result


def audit_faq(parsed, html):
    """Audit FAQ coverage for a post."""
    result = {
        "has_faq": False,
        "question_count": 0,
        "has_schema": False,
    }

    # Check headings for FAQ section
    faq_found = False
    for tag, text in parsed.headings:
        text_lower = text.lower()
        if "faq" in text_lower or "frequently asked" in text_lower:
            faq_found = True
            break

    if faq_found:
        result["has_faq"] = True
        # Count questions — look for h3 tags or <strong> after FAQ heading
        # Simple heuristic: count h3s that look like questions
        question_patterns = [
            r'<h3[^>]*>.*?\?.*?</h3>',
            r'<strong>.*?\?.*?</strong>',
            r'<h4[^>]*>.*?\?.*?</h4>',
        ]
        for pattern in question_patterns:
            matches = re.findall(pattern, html or "", re.IGNORECASE | re.DOTALL)
            result["question_count"] += len(matches)

    # Check for FAQ schema
    for script_content in parsed._scripts:
        try:
            schema = json.loads(script_content)
            if isinstance(schema, dict) and schema.get("@type") == "FAQPage":
                result["has_schema"] = True
            elif isinstance(schema, list):
                for item in schema:
                    if isinstance(item, dict) and item.get("@type") == "FAQPage":
                        result["has_schema"] = True
        except (json.JSONDecodeError, TypeError):
            pass

    # Also check raw HTML for ld+json FAQPage
    if not result["has_schema"]:
        if "FAQPage" in (html or ""):
            result["has_schema"] = True

    return result


def audit_affiliate(parsed):
    """Audit affiliate link coverage."""
    result = {
        "amazon_links": 0,
        "has_tag": False,
        "links": [],
    }

    for href, text in parsed.links:
        if not href:
            continue
        href_lower = href.lower()
        if "amazon.co.uk" in href_lower or "amzn.to" in href_lower:
            result["amazon_links"] += 1
            if "pethubonline-21" in href_lower:
                result["has_tag"] = True
            result["links"].append({"href": href[:200], "text": text[:100]})

    return result


def audit_tables(parsed, html):
    """Audit comparison table coverage."""
    result = {
        "has_table": parsed.tables > 0,
        "table_count": parsed.tables,
        "row_count": parsed.table_rows,
        "has_wp_table_block": False,
    }

    # Check for wp:table block comments
    if html and "wp:table" in html:
        result["has_wp_table_block"] = True

    return result


def audit_images(parsed, featured_media):
    """Audit image compliance."""
    result = {
        "has_featured": featured_media > 0 if featured_media else False,
        "image_count": len(parsed.images),
        "missing_alt": 0,
        "empty_alt": 0,
        "images_with_alt": 0,
    }

    for src, alt in parsed.images:
        if alt is None or alt == "":
            result["empty_alt"] += 1
        else:
            result["images_with_alt"] += 1

    result["missing_alt"] = result["empty_alt"]
    return result


# ── Main audit orchestrator ─────────────────────────────────────────────────
def run_audit():
    start_time = time.time()
    print("=" * 70)
    print("PHASE 19 AUTHORITY AUDIT — PetHub Online (pethubonline.com)")
    print(f"Started: {datetime.utcnow().isoformat()}Z")
    print("=" * 70)

    # Fetch categories
    print("\n[1/3] Fetching categories...")
    cat_map = fetch_categories()
    print(f"  Found {len(cat_map)} categories")

    # Fetch posts
    print("\n[2/3] Fetching all published posts...")
    posts = fetch_all_posts()

    if not posts:
        print("ERROR: No posts fetched. Aborting.")
        sys.exit(1)

    # Audit each post
    print(f"\n[3/3] Auditing {len(posts)} posts...")

    # Result accumulators
    cta_results = []
    faq_results = []
    affiliate_results = []
    table_results = []
    image_results = []

    # Counters
    stats = {
        "total": len(posts),
        "cta_present": 0,
        "cta_missing": 0,
        "faq_present": 0,
        "faq_missing": 0,
        "faq_with_schema": 0,
        "affiliate_present": 0,
        "affiliate_missing": 0,
        "table_present": 0,
        "table_missing": 0,
        "featured_present": 0,
        "featured_missing": 0,
        "alt_issues": 0,
        "low_image": 0,
    }

    # CTA type tracker
    cta_type_counts = defaultdict(int)

    # Affiliate by category
    affiliate_by_cat = defaultdict(lambda: {"total": 0, "with_links": 0, "link_count": 0})

    # All question counts for averaging
    all_question_counts = []

    errors = 0

    for idx, post in enumerate(posts):
        try:
            post_id = post.get("id", 0)
            title_raw = post.get("title", {})
            if isinstance(title_raw, dict):
                title = title_raw.get("rendered", "Untitled")
            else:
                title = str(title_raw)
            link = post.get("link", "")
            categories = post.get("categories", [])
            content_obj = post.get("content", {})
            if isinstance(content_obj, dict):
                html = content_obj.get("rendered", "")
            else:
                html = str(content_obj)
            featured_media = post.get("featured_media", 0)

            # Get category names
            cat_names = [cat_map.get(c, f"cat-{c}") for c in categories]
            primary_cat = cat_names[0] if cat_names else "Uncategorized"

            # Parse HTML
            parsed = parse_html(html)

            # ── CTA audit ──
            cta = audit_cta(parsed)
            post_cta = {
                "id": post_id,
                "title": title,
                "link": link,
                "category": primary_cat,
                "has_cta": cta["has_cta"],
                "types": cta["types"],
                "affiliate_count": cta["affiliate_count"],
                "internal_count": cta["internal_count"],
            }
            cta_results.append(post_cta)
            if cta["has_cta"]:
                stats["cta_present"] += 1
                for t in cta["types"]:
                    cta_type_counts[t] += 1
            else:
                stats["cta_missing"] += 1

            # ── FAQ audit ──
            faq = audit_faq(parsed, html)
            post_faq = {
                "id": post_id,
                "title": title,
                "link": link,
                "category": primary_cat,
                "has_faq": faq["has_faq"],
                "question_count": faq["question_count"],
                "has_schema": faq["has_schema"],
            }
            faq_results.append(post_faq)
            if faq["has_faq"]:
                stats["faq_present"] += 1
                all_question_counts.append(faq["question_count"])
            else:
                stats["faq_missing"] += 1
            if faq["has_schema"]:
                stats["faq_with_schema"] += 1

            # ── Affiliate audit ──
            aff = audit_affiliate(parsed)
            post_aff = {
                "id": post_id,
                "title": title,
                "link": link,
                "category": primary_cat,
                "amazon_links": aff["amazon_links"],
                "has_tag": aff["has_tag"],
            }
            affiliate_results.append(post_aff)
            if aff["amazon_links"] > 0:
                stats["affiliate_present"] += 1
            else:
                stats["affiliate_missing"] += 1

            # Affiliate by category
            for cat_name in cat_names:
                affiliate_by_cat[cat_name]["total"] += 1
                if aff["amazon_links"] > 0:
                    affiliate_by_cat[cat_name]["with_links"] += 1
                    affiliate_by_cat[cat_name]["link_count"] += aff["amazon_links"]

            # ── Table audit ──
            tbl = audit_tables(parsed, html)
            post_tbl = {
                "id": post_id,
                "title": title,
                "link": link,
                "category": primary_cat,
                "has_table": tbl["has_table"],
                "table_count": tbl["table_count"],
                "row_count": tbl["row_count"],
            }
            table_results.append(post_tbl)
            if tbl["has_table"]:
                stats["table_present"] += 1
            else:
                stats["table_missing"] += 1

            # ── Image audit ──
            img = audit_images(parsed, featured_media)
            post_img = {
                "id": post_id,
                "title": title,
                "link": link,
                "category": primary_cat,
                "has_featured": img["has_featured"],
                "image_count": img["image_count"],
                "missing_alt": img["missing_alt"],
            }
            image_results.append(post_img)
            if img["has_featured"]:
                stats["featured_present"] += 1
            else:
                stats["featured_missing"] += 1
            if img["missing_alt"] > 0:
                stats["alt_issues"] += 1
            if img["image_count"] < 2:
                stats["low_image"] += 1

        except Exception as e:
            errors += 1
            print(f"  [ERROR] Post {post.get('id', '?')}: {e}")

        # Progress
        if (idx + 1) % 50 == 0:
            elapsed = time.time() - start_time
            print(f"  Progress: {idx + 1}/{len(posts)} audited ({elapsed:.1f}s elapsed, {errors} errors)")

    print(f"\n  Audit complete: {len(posts)} posts, {errors} errors")

    # ── Build output JSON files ─────────────────────────────────────────────

    # 1. CTA Audit
    posts_missing_cta = [
        {"id": p["id"], "title": p["title"], "link": p["link"], "category": p["category"]}
        for p in cta_results if not p["has_cta"]
    ]
    cta_output = {
        "audit": "Phase 19 CTA Coverage",
        "date": datetime.utcnow().isoformat() + "Z",
        "total_posts": stats["total"],
        "posts_with_cta": stats["cta_present"],
        "posts_without_cta": stats["cta_missing"],
        "cta_rate_pct": round(stats["cta_present"] / max(stats["total"], 1) * 100, 1),
        "cta_by_type": dict(cta_type_counts),
        "posts_missing_cta": posts_missing_cta,
    }

    # 2. FAQ Audit
    posts_missing_faq = [
        {"id": p["id"], "title": p["title"], "link": p["link"], "category": p["category"]}
        for p in faq_results if not p["has_faq"]
    ]
    posts_missing_schema = [
        {"id": p["id"], "title": p["title"], "link": p["link"]}
        for p in faq_results if p["has_faq"] and not p["has_schema"]
    ]
    avg_q = round(sum(all_question_counts) / max(len(all_question_counts), 1), 1)
    faq_output = {
        "audit": "Phase 19 FAQ Coverage",
        "date": datetime.utcnow().isoformat() + "Z",
        "total_posts": stats["total"],
        "posts_with_faq": stats["faq_present"],
        "posts_without_faq": stats["faq_missing"],
        "faq_rate_pct": round(stats["faq_present"] / max(stats["total"], 1) * 100, 1),
        "posts_with_schema": stats["faq_with_schema"],
        "avg_questions_per_faq": avg_q,
        "posts_missing_faq": posts_missing_faq,
        "posts_with_faq_but_no_schema": posts_missing_schema,
    }

    # 3. Affiliate Audit
    posts_without_affiliate = [
        {"id": p["id"], "title": p["title"], "link": p["link"], "category": p["category"]}
        for p in affiliate_results if p["amazon_links"] == 0
    ]
    # Sort categories by coverage rate
    cat_coverage = {}
    for cat_name, data in affiliate_by_cat.items():
        rate = round(data["with_links"] / max(data["total"], 1) * 100, 1)
        cat_coverage[cat_name] = {
            "total_posts": data["total"],
            "posts_with_affiliates": data["with_links"],
            "total_affiliate_links": data["link_count"],
            "coverage_pct": rate,
        }
    # Top opportunities: posts without affiliates in categories with high coverage
    top_opportunities = sorted(
        posts_without_affiliate,
        key=lambda p: cat_coverage.get(p["category"], {}).get("coverage_pct", 0),
        reverse=True,
    )[:50]

    affiliate_output = {
        "audit": "Phase 19 Affiliate Coverage",
        "date": datetime.utcnow().isoformat() + "Z",
        "total_posts": stats["total"],
        "posts_with_affiliates": stats["affiliate_present"],
        "posts_without_affiliates": stats["affiliate_missing"],
        "affiliate_rate_pct": round(stats["affiliate_present"] / max(stats["total"], 1) * 100, 1),
        "by_category": cat_coverage,
        "top_opportunities": top_opportunities,
    }

    # 4. Table Audit
    posts_missing_tables = [
        {"id": p["id"], "title": p["title"], "link": p["link"], "category": p["category"]}
        for p in table_results if not p["has_table"]
    ]
    table_output = {
        "audit": "Phase 19 Comparison Table Coverage",
        "date": datetime.utcnow().isoformat() + "Z",
        "total_posts": stats["total"],
        "posts_with_tables": stats["table_present"],
        "posts_without_tables": stats["table_missing"],
        "table_rate_pct": round(stats["table_present"] / max(stats["total"], 1) * 100, 1),
        "missing": posts_missing_tables,
    }

    # 5. Image Audit
    missing_featured = [
        {"id": p["id"], "title": p["title"], "link": p["link"], "category": p["category"]}
        for p in image_results if not p["has_featured"]
    ]
    low_image_posts = [
        {"id": p["id"], "title": p["title"], "link": p["link"], "image_count": p["image_count"]}
        for p in image_results if p["image_count"] < 2
    ]
    alt_issue_posts = [
        {"id": p["id"], "title": p["title"], "link": p["link"], "missing_alt": p["missing_alt"]}
        for p in image_results if p["missing_alt"] > 0
    ]
    image_output = {
        "audit": "Phase 19 Image Compliance",
        "date": datetime.utcnow().isoformat() + "Z",
        "total_posts": stats["total"],
        "posts_with_featured_image": stats["featured_present"],
        "missing_featured_image": stats["featured_missing"],
        "featured_rate_pct": round(stats["featured_present"] / max(stats["total"], 1) * 100, 1),
        "posts_with_alt_text_issues": stats["alt_issues"],
        "posts_with_low_image_count": stats["low_image"],
        "missing_featured": missing_featured,
        "low_image_count": low_image_posts[:100],
        "alt_text_issues": alt_issue_posts[:100],
    }

    # 6. Summary
    # Calculate authority score (weighted)
    cta_score = stats["cta_present"] / max(stats["total"], 1) * 100
    faq_score = stats["faq_present"] / max(stats["total"], 1) * 100
    affiliate_score = stats["affiliate_present"] / max(stats["total"], 1) * 100
    table_score = stats["table_present"] / max(stats["total"], 1) * 100
    image_score = stats["featured_present"] / max(stats["total"], 1) * 100
    alt_score = (1 - stats["alt_issues"] / max(stats["total"], 1)) * 100

    # Weighted authority score
    authority_score = round(
        cta_score * 0.25 +
        faq_score * 0.15 +
        affiliate_score * 0.25 +
        table_score * 0.10 +
        image_score * 0.15 +
        alt_score * 0.10,
        1
    )

    # Top 20 priority fixes - posts missing the most elements
    post_deficiencies = {}
    for p in cta_results:
        pid = p["id"]
        if pid not in post_deficiencies:
            post_deficiencies[pid] = {
                "id": pid, "title": p["title"], "link": p["link"],
                "category": p["category"], "missing": [], "score": 0
            }
        if not p["has_cta"]:
            post_deficiencies[pid]["missing"].append("CTA")
            post_deficiencies[pid]["score"] += 3

    for p in faq_results:
        pid = p["id"]
        if pid in post_deficiencies and not p["has_faq"]:
            post_deficiencies[pid]["missing"].append("FAQ")
            post_deficiencies[pid]["score"] += 2

    for p in affiliate_results:
        pid = p["id"]
        if pid in post_deficiencies and p["amazon_links"] == 0:
            post_deficiencies[pid]["missing"].append("Affiliates")
            post_deficiencies[pid]["score"] += 3

    for p in table_results:
        pid = p["id"]
        if pid in post_deficiencies and not p["has_table"]:
            post_deficiencies[pid]["missing"].append("ComparisonTable")
            post_deficiencies[pid]["score"] += 1

    for p in image_results:
        pid = p["id"]
        if pid in post_deficiencies:
            if not p["has_featured"]:
                post_deficiencies[pid]["missing"].append("FeaturedImage")
                post_deficiencies[pid]["score"] += 2
            if p["missing_alt"] > 0:
                post_deficiencies[pid]["missing"].append("AltText")
                post_deficiencies[pid]["score"] += 1

    top_fixes = sorted(post_deficiencies.values(), key=lambda x: x["score"], reverse=True)[:20]

    summary_output = {
        "audit": "Phase 19 Authority Audit Summary",
        "date": datetime.utcnow().isoformat() + "Z",
        "site": "pethubonline.com",
        "total_posts_audited": stats["total"],
        "authority_score": authority_score,
        "breakdown": {
            "cta_coverage": {
                "score": round(cta_score, 1),
                "weight": "25%",
                "present": stats["cta_present"],
                "missing": stats["cta_missing"],
                "by_type": dict(cta_type_counts),
            },
            "faq_coverage": {
                "score": round(faq_score, 1),
                "weight": "15%",
                "present": stats["faq_present"],
                "missing": stats["faq_missing"],
                "with_schema": stats["faq_with_schema"],
                "avg_questions": avg_q,
            },
            "affiliate_coverage": {
                "score": round(affiliate_score, 1),
                "weight": "25%",
                "present": stats["affiliate_present"],
                "missing": stats["affiliate_missing"],
            },
            "table_coverage": {
                "score": round(table_score, 1),
                "weight": "10%",
                "present": stats["table_present"],
                "missing": stats["table_missing"],
            },
            "image_compliance": {
                "featured_score": round(image_score, 1),
                "alt_text_score": round(alt_score, 1),
                "weight": "25% (15% featured + 10% alt)",
                "featured_present": stats["featured_present"],
                "featured_missing": stats["featured_missing"],
                "alt_issues": stats["alt_issues"],
                "low_image_count": stats["low_image"],
            },
        },
        "top_20_priority_fixes": [
            {
                "id": f["id"],
                "title": f["title"],
                "link": f["link"],
                "category": f["category"],
                "missing_elements": f["missing"],
                "deficiency_score": f["score"],
            }
            for f in top_fixes
        ],
        "recommendations": [
            f"CTA gap: {stats['cta_missing']} posts lack any call-to-action — add affiliate links or internal links",
            f"FAQ gap: {stats['faq_missing']} posts lack FAQ sections — add FAQPage schema for rich snippets",
            f"Affiliate gap: {stats['affiliate_missing']} posts have no Amazon links — prioritize product review categories",
            f"Table gap: {stats['table_missing']} posts lack comparison tables — add for product comparison posts",
            f"Image gap: {stats['featured_missing']} posts missing featured image, {stats['alt_issues']} posts have alt text issues",
        ],
        "audit_duration_seconds": round(time.time() - start_time, 1),
        "errors": errors,
    }

    # ── Save files ──────────────────────────────────────────────────────────
    files = {
        "phase19_cta_audit.json": cta_output,
        "phase19_faq_audit.json": faq_output,
        "phase19_affiliate_audit.json": affiliate_output,
        "phase19_table_audit.json": table_output,
        "phase19_image_audit.json": image_output,
        "phase19_summary.json": summary_output,
    }

    print("\n" + "=" * 70)
    print("SAVING RESULTS")
    print("=" * 70)

    for filename, data in files.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        size = os.path.getsize(filepath)
        print(f"  Saved: {filepath} ({size:,} bytes)")

    # ── Print summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("PHASE 19 AUDIT SUMMARY")
    print("=" * 70)
    print(f"  Total posts audited: {stats['total']}")
    print(f"  Authority Score: {authority_score}/100")
    print()
    print(f"  CTA Coverage:       {stats['cta_present']}/{stats['total']} ({round(cta_score,1)}%)")
    print(f"  FAQ Coverage:       {stats['faq_present']}/{stats['total']} ({round(faq_score,1)}%)")
    print(f"  Affiliate Coverage: {stats['affiliate_present']}/{stats['total']} ({round(affiliate_score,1)}%)")
    print(f"  Table Coverage:     {stats['table_present']}/{stats['total']} ({round(table_score,1)}%)")
    print(f"  Featured Image:     {stats['featured_present']}/{stats['total']} ({round(image_score,1)}%)")
    print(f"  Alt Text Clean:     {stats['total'] - stats['alt_issues']}/{stats['total']} ({round(alt_score,1)}%)")
    print()
    print(f"  Errors during audit: {errors}")
    print(f"  Duration: {round(time.time() - start_time, 1)}s")
    print("=" * 70)


if __name__ == "__main__":
    run_audit()
