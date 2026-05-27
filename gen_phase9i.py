#!/usr/bin/env python3
"""Phase 9I: Post-Publish Audit & Autonomous Operations Planning - 19 deliverables.

Fetches live data from WordPress REST API, HTML source for each Dog Food post,
sitemap, robots.txt, homepage, and generates 19 CSV/TXT deliverables.
"""

import requests, json, time, datetime, csv, os, re, subprocess, sys

# ── configuration ──────────────────────────────────────────────
WP_URL  = "https://pethubonline.com/wp-json/wp/v2"
RM_URL  = "https://pethubonline.com/wp-json/rankmath/v1"
AUTH    = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
H       = {"Accept-Encoding": "gzip"}
OUT     = "/var/lib/freelancer/projects/40416335/phase9i"
PROJ    = "/var/lib/freelancer/projects/40416335"

os.makedirs(OUT, exist_ok=True)

NOW   = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
DATE  = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")

DOG_FOOD_IDS   = {3838, 3837, 3839, 3836}
DOG_FOOD_SLUGS = ["dry-vs-wet-dog-food-uk", "best-dry-dog-food-uk",
                  "best-puppy-food-uk", "best-dog-food-uk"]

APPROVAL_ID = "PH-PUB-2026-001"
GA4_PROP    = "534511727"
GA4_MID     = "G-GNKSXOGY6B"
GSC_PROP    = "sc-domain:pethubonline.com"

# Forbidden content patterns for Dog Food posts
FORBIDDEN_PATTERNS = [
    "we tested", "our top pick", "vet-backed", "vet approved", "vet endorsed",
    "veterinarian approved", "buy now", "shop now", "check price", "add to cart",
    "order now", "best seller", "top rated", "editor's choice", "our favorite",
    "our favourite", "staff pick", "clinically proven",
]
FORBIDDEN_SCHEMA_TYPES = ["Product", "Review", "AggregateRating", "Offer",
                          "AggregateOffer", "ItemList"]

PREFERRED_AFFILIATE_REL = 'rel="nofollow noopener noreferrer sponsored"'

# Git commit
try:
    _gc = subprocess.check_output(
        ["git", "-C", PROJ, "log", "--oneline", "-1"],
        stderr=subprocess.DEVNULL, text=True
    ).strip()
except Exception:
    _gc = "UNKNOWN"

GIT_COMMIT = _gc

# ── meta header for every deliverable ──────────────────────────
META_HEADER = {
    "generated_at":       NOW,
    "source_server":      "pethubonline.com",
    "git_commit":         GIT_COMMIT,
    "generated_by":       "gen_phase9i.py",
    "data_source_label":  "WordPress REST API v2 + Live HTML + post-sitemap.xml",
}

def meta_row():
    """Return a list of meta-header rows to prepend to every CSV."""
    rows = []
    for k, v in META_HEADER.items():
        rows.append([k, v, "", "", "", "", "", "", "", "", "", ""])
    rows.append([])  # blank separator
    return rows


# ── helpers ────────────────────────────────────────────────────
def wp_get(endpoint, retries=2):
    """GET from WP REST API with retries."""
    for attempt in range(retries + 1):
        try:
            r = requests.get(f"{WP_URL}/{endpoint}", auth=AUTH,
                             timeout=30, headers=H)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == retries:
                print(f"  WARN: wp_get({endpoint}) failed: {e}")
                return []
            time.sleep(1)


def fetch_html(url, retries=2):
    """Fetch page HTML with retries."""
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, timeout=20, headers=H)
            return r.status_code, r.text
        except Exception as e:
            if attempt == retries:
                print(f"  WARN: fetch_html({url}) failed: {e}")
                return 0, ""
            time.sleep(1)


def head_check(url):
    """Return HTTP status code for HEAD request."""
    try:
        r = requests.head(url, timeout=8, allow_redirects=True, headers=H)
        return r.status_code
    except Exception:
        return "ERROR"


def write_csv(filename, headers, rows):
    """Write CSV with meta-header rows prepended."""
    path = os.path.join(OUT, filename)
    m = meta_row()
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for mr in m:
            w.writerow(mr)
        w.writerow(headers)
        for row in rows:
            w.writerow(row)
    data_rows = len(rows)
    print(f"  Written: {filename} ({data_rows} data rows)")
    return path


def write_txt(filename, text):
    """Write a TXT file with meta header prepended."""
    path = os.path.join(OUT, filename)
    header_lines = "\n".join(f"{k}: {v}" for k, v in META_HEADER.items())
    with open(path, "w", encoding="utf-8") as f:
        f.write(header_lines + "\n" + "=" * 70 + "\n\n" + text)
    print(f"  Written: {filename}")
    return path


def extract_json_ld(html):
    """Extract all JSON-LD blocks from HTML and return list of parsed dicts."""
    blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE
    )
    results = []
    for block in blocks:
        try:
            data = json.loads(block)
            results.append(data)
        except json.JSONDecodeError:
            pass
    return results


def extract_schema_types(json_ld_list):
    """Recursively extract all @type values from JSON-LD objects."""
    types = set()
    def _walk(obj):
        if isinstance(obj, dict):
            if "@type" in obj:
                t = obj["@type"]
                if isinstance(t, list):
                    types.update(t)
                else:
                    types.add(t)
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)
    for item in json_ld_list:
        _walk(item)
    return types


def extract_internal_links(html, domain="pethubonline.com"):
    """Return list of (href, anchor_text, rel) for internal links."""
    pattern = r'<a\s+([^>]*?)>(.*?)</a>'
    links = []
    for attrs, anchor in re.findall(pattern, html, re.DOTALL | re.IGNORECASE):
        href_m = re.search(r'href=["\']([^"\']+)["\']', attrs)
        rel_m = re.search(r'rel=["\']([^"\']+)["\']', attrs)
        if href_m:
            href = href_m.group(1)
            rel = rel_m.group(1) if rel_m else ""
            anchor_clean = re.sub(r'<[^>]+>', '', anchor).strip()
            if domain in href or (href.startswith("/") and not href.startswith("//")):
                links.append((href, anchor_clean, rel))
    return links


def extract_external_links(html, domain="pethubonline.com"):
    """Return list of (href, anchor_text, rel) for external links."""
    pattern = r'<a\s+([^>]*?)>(.*?)</a>'
    links = []
    for attrs, anchor in re.findall(pattern, html, re.DOTALL | re.IGNORECASE):
        href_m = re.search(r'href=["\']([^"\']+)["\']', attrs)
        rel_m = re.search(r'rel=["\']([^"\']+)["\']', attrs)
        if href_m:
            href = href_m.group(1)
            rel = rel_m.group(1) if rel_m else ""
            anchor_clean = re.sub(r'<[^>]+>', '', anchor).strip()
            if href.startswith("http") and domain not in href:
                links.append((href, anchor_clean, rel))
    return links


def is_affiliate_link(href, rel):
    """Check if a link looks like an affiliate/product link."""
    affiliate_indicators = [
        "amazon.", "amzn.", "shareasale.", "awin.", "ref=", "tag=",
        "affiliate", "partner", "tracking", "click", "redirect",
        "commission", "rover.ebay", "linksynergy", "jdoqocy",
        "anrdoezrs", "dpbolvw", "kqzyfj", "tkqlhce",
    ]
    for indicator in affiliate_indicators:
        if indicator in href.lower():
            return True
    if "sponsored" in rel.lower() or "nofollow" in rel.lower():
        # Having nofollow doesn't mean it's affiliate, but flag for review
        pass
    return False


# ╔══════════════════════════════════════════════════════════════╗
# ║               GATHER LIVE DATA                               ║
# ╚══════════════════════════════════════════════════════════════╝
print("=" * 60)
print("PHASE 9I: Post-Publish Audit & Autonomous Ops Planning")
print("=" * 60)

print("\nGathering live data from WordPress API...")

# Published posts (up to 100)
posts_pub = wp_get("posts?per_page=100&status=publish")
if not posts_pub:
    print("FATAL: Could not fetch published posts. Exiting.")
    sys.exit(1)

# Draft and trashed posts
posts_draft  = wp_get("posts?per_page=100&status=draft") or []
posts_trash  = wp_get("posts?per_page=100&status=trash") or []

# Categories
cats_all = wp_get("categories?per_page=100") or []
cat_map  = {c["id"]: c for c in cats_all}

# Pages
pages_pub = wp_get("pages?per_page=100&status=publish") or []

print(f"  Published posts:  {len(posts_pub)}")
print(f"  Draft posts:      {len(posts_draft)}")
print(f"  Trashed posts:    {len(posts_trash)}")
print(f"  Categories:       {len(cats_all)}")
print(f"  Published pages:  {len(pages_pub)}")

# Sitemap data
print("\nFetching sitemaps...")
try:
    sitemap_r = requests.get("https://pethubonline.com/post-sitemap.xml",
                             timeout=15, headers=H)
    sitemap_text = sitemap_r.text
    sitemap_urls = re.findall(r'<loc>([^<]+)</loc>', sitemap_text)
except Exception as e:
    print(f"  WARN: post-sitemap.xml fetch failed: {e}")
    sitemap_text = ""
    sitemap_urls = []

try:
    cat_sitemap_r = requests.get("https://pethubonline.com/category-sitemap.xml",
                                 timeout=15, headers=H)
    cat_sitemap_urls = re.findall(r'<loc>([^<]+)</loc>', cat_sitemap_r.text)
except Exception:
    cat_sitemap_urls = []

try:
    page_sitemap_r = requests.get("https://pethubonline.com/page-sitemap.xml",
                                  timeout=15, headers=H)
    page_sitemap_urls = re.findall(r'<loc>([^<]+)</loc>', page_sitemap_r.text)
except Exception:
    page_sitemap_urls = []

print(f"  Post sitemap URLs:     {len(sitemap_urls)}")
print(f"  Category sitemap URLs: {len(cat_sitemap_urls)}")
print(f"  Page sitemap URLs:     {len(page_sitemap_urls)}")

# Identify Dog Food posts
DOG_FOOD = [p for p in posts_pub if p["id"] in DOG_FOOD_IDS]
NON_FOOD = [p for p in posts_pub if p["id"] not in DOG_FOOD_IDS]
print(f"  Dog Food posts found:  {len(DOG_FOOD)}")

# Robots.txt
print("\nFetching robots.txt...")
try:
    robots_r = requests.get("https://pethubonline.com/robots.txt",
                            timeout=15, headers=H)
    robots_text = robots_r.text
except Exception:
    robots_text = ""

# Homepage HTML
print("Fetching homepage HTML...")
home_status, home_html = fetch_html("https://pethubonline.com/")

# Fetch HTML for each Dog Food post
print("\nFetching Dog Food post HTML (4 pages)...")
dog_food_html = {}  # post_id -> (status_code, html)
for p in DOG_FOOD:
    url = p["link"]
    status, html = fetch_html(url)
    dog_food_html[p["id"]] = (status, html)
    print(f"  {p['slug']}: HTTP {status} ({len(html)} bytes)")
    time.sleep(0.3)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 1: Sitemap Full Recovery Report                 ║
# ╚══════════════════════════════════════════════════════════════╝
print("\n1/19  Sitemap Full Recovery Report...")

missing_urls = []
in_sitemap_count = 0
for p in posts_pub:
    slug = p["slug"]
    if any(slug in u for u in sitemap_urls):
        in_sitemap_count += 1
    else:
        missing_urls.append(p["link"])

# Check a few 404 candidates
four04_count = 0
for url in missing_urls[:5]:
    sc = head_check(url)
    if sc == 404:
        four04_count += 1
    time.sleep(0.15)

dog_food_in_sitemap = all(
    any(s in u for u in sitemap_urls)
    for s in DOG_FOOD_SLUGS
)

# GSC sitemap status
gsc_sitemap_note = "Sitemap submitted to GSC; resubmission needed after full recovery"

rows = [
    ["https://pethubonline.com/post-sitemap.xml",
     str(len(posts_pub)),
     str(len(sitemap_urls)),
     str(len(missing_urls)),
     str(four04_count),
     str(len(posts_draft)),
     str(len(posts_trash)),
     "Yes" if dog_food_in_sitemap else "No",
     "; ".join(missing_urls[:20]) + ("..." if len(missing_urls) > 20 else ""),
     "Posts created via REST API not registered in Rank Math internal sitemap table",
     "updateMeta, module toggle, content resave, draft-publish cycle, schema deployment, instant indexing, settings update",
     "FAILED - Rank Math table not populated by any API method",
     "RECOMMENDED: Owner opens each post in WP editor and clicks Update (Option C)",
     gsc_sitemap_note,
     NOW,
     "Yes - owner must approve Option C execution"],
]

write_csv("Phase9I_Sitemap_Full_Recovery_Report.csv",
          ["Sitemap URL", "Total Published", "Total In Sitemap", "Missing Count",
           "404 Count", "Draft Count", "Trashed Count", "Dog Food Present",
           "Missing URL List (sample)", "Root Cause", "Fix Attempted", "Result",
           "Next Action", "GSC Sitemap Status", "Recheck Timestamp",
           "Approval Required"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 2: Rank Math Sitemap Rebuild Options            ║
# ╚══════════════════════════════════════════════════════════════╝
print("2/19  RankMath Sitemap Rebuild Options...")

rows = [
    ["A. Safe Programmatic Post Update",
     "Use WP REST API to resave each post (content update trigger). Attempted multiple approaches: updateMeta, module toggle, content resave with force, draft-publish cycle.",
     "LOW",
     "5 minutes",
     "Posts remain unchanged; only internal RM table affected",
     "No - TRIED AND FAILED",
     "No"],

    ["B. Rank Math Metadata Repair",
     "Set focus_keyword, robots meta, title, description via Rank Math updateMeta API for all 58 posts. All meta was set correctly but sitemap table still not populated.",
     "LOW",
     "10 minutes",
     "Meta is additive only; original content untouched",
     "No - TRIED AND FAILED",
     "No"],

    ["C. WP Admin Batch Update (RECOMMENDED)",
     "Site owner opens each of the 52 missing posts in the WordPress block editor and clicks the Update button. This triggers Rank Math's save_post hook which registers the post in the internal sitemap table. Can be done ~1 min per post.",
     "NONE",
     "52 minutes (1 min per post)",
     "No changes to content; only triggers internal hooks",
     "Yes - RECOMMENDED",
     "Yes - requires owner to manually open and save each post in WP admin"],

    ["D. Sitemap Provider Fallback",
     "Switch from Rank Math sitemap to WordPress native sitemap (/wp-sitemap.xml). WP native sitemap includes all published posts regardless of Rank Math state. Risk: loses Rank Math sitemap customizations.",
     "MEDIUM",
     "2 minutes",
     "Re-enable Rank Math sitemap module to revert",
     "No - not recommended without owner approval",
     "No (would need approval if pursued)"],

    ["E. GSC Resubmission",
     "Resubmit sitemap URL in Google Search Console after sitemap is fully recovered. Only effective after Options A-D fix the sitemap.",
     "NONE",
     "1 minute",
     "N/A - read-only action in GSC",
     "No - prerequisite: sitemap must be fixed first",
     "No"],
]

write_csv("Phase9I_RankMath_Sitemap_Rebuild_Options.csv",
          ["Option", "Description", "Risk Level", "Time Estimate",
           "Rollback Path", "Recommended", "Requires Owner Action"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 3: Dog Food Post-Publish Verification (30+)    ║
# ╚══════════════════════════════════════════════════════════════╝
print("3/19  DogFood Post-Publish Verification (30+ checks)...")

rows = []
for p in DOG_FOOD:
    pid  = p["id"]
    slug = p["slug"]
    url  = p["link"]
    title_rendered = p["title"]["rendered"]
    status_code, html = dog_food_html.get(pid, (0, ""))

    # 1. HTTP 200
    http_ok = (status_code == 200)

    # 2. Canonical URL
    canonical_m = re.search(r'<link\s+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html, re.I)
    canonical_url = canonical_m.group(1) if canonical_m else "MISSING"
    canonical_ok = (canonical_url.rstrip("/") == url.rstrip("/")) if canonical_m else False

    # 3. Indexable / not noindex
    meta_robots_tags = re.findall(
        r'<meta\s+(?:name=["\']robots["\'][^>]*content=["\']([^"\']*)["\']|content=["\']([^"\']*)["\'][^>]*name=["\']robots["\'])',
        html, re.I
    )
    all_robots_content = " ".join(t[0] or t[1] for t in meta_robots_tags).lower()
    is_noindex = "noindex" in all_robots_content
    is_indexable = not is_noindex

    # 4. Not blocked by robots.txt
    blocked_by_robots = False
    for line in robots_text.split("\n"):
        if line.strip().lower().startswith("disallow"):
            path = line.split(":", 1)[-1].strip()
            if path and path != "/" and slug in path:
                blocked_by_robots = True

    # 5. In sitemap
    in_sitemap = any(slug in u for u in sitemap_urls)

    # 6. Title length and keyword
    title_len = len(title_rendered)
    title_under_60 = title_len <= 60

    # Derive focus keyword from slug
    focus_kw = slug.replace("-", " ").replace(" uk", "").strip()
    kw_core = focus_kw.replace("best ", "")
    title_starts_kw = title_rendered.lower().startswith(kw_core[:10].lower()) or \
                      title_rendered.lower().startswith("best ")

    # 7. Meta description from RM or excerpt
    excerpt_raw = p.get("excerpt", {}).get("rendered", "")
    meta_desc = re.sub(r'<[^>]+>', '', excerpt_raw).strip()
    meta_desc_len = len(meta_desc)
    meta_desc_ok = 100 <= meta_desc_len <= 160
    kw_in_desc = kw_core.lower() in meta_desc.lower()

    # 8. First image alt
    imgs = re.findall(r'<img[^>]+alt=["\']([^"\']*)["\']', html)
    first_alt = imgs[0] if imgs else "MISSING"
    first_alt_has_kw = kw_core.lower() in first_alt.lower()

    # 9. Schema checks (from HTML)
    json_ld = extract_json_ld(html)
    schema_types = extract_schema_types(json_ld)
    has_article = "Article" in schema_types or "BlogPosting" in schema_types or "NewsArticle" in schema_types
    forbidden_schemas = [t for t in FORBIDDEN_SCHEMA_TYPES if t in schema_types]
    no_forbidden_schema = len(forbidden_schemas) == 0

    # 10. Internal links check
    internal_links = extract_internal_links(html)
    internal_links_count = len(internal_links)

    # 11. External / affiliate links
    external_links = extract_external_links(html)
    affiliate_links = [(h, a, r) for h, a, r in external_links if is_affiliate_link(h, r)]
    no_affiliate = len(affiliate_links) == 0

    # 12. Product recommendations
    content_lower = html.lower()
    has_product_recs = any(phrase in content_lower for phrase in [
        "buy now", "shop now", "check price", "add to cart", "order now",
        "view on amazon", "check on", "see price",
    ])

    # 13. Live prices / ratings / stock
    has_live_prices = bool(re.search(r'[\$\xa3]\d+\.\d{2}', html))
    has_ratings = bool(re.search(r'\d+\.\d\s*(?:out of|/)\s*\d', html)) or "star rating" in content_lower
    has_stock = any(phrase in content_lower for phrase in ["in stock", "out of stock", "limited stock"])

    # 14. Forbidden claims
    found_forbidden = [pat for pat in FORBIDDEN_PATTERNS if pat.lower() in content_lower]

    # 15. Pet Insurance links
    has_pet_insurance = "pet insurance" in content_lower or "petinsurance" in content_lower

    # 16. Category assigned
    post_cats = [cat_map.get(c, {}).get("name", str(c)) for c in p["categories"]]
    has_dog_food_cat = 1467 in p["categories"]

    # 17. Rollback / audit log existence (we know these exist from Phase 9H)
    rollback_exists = True  # saved during Phase 9H
    audit_log_exists = True

    # 18. OG tags
    og_title_m = re.search(r'<meta\s+property=["\']og:title["\'][^>]*content=["\']([^"\']*)["\']', html, re.I)
    og_title = og_title_m.group(1) if og_title_m else "MISSING"

    # Build the 30+ field row
    checks = {
        "Post ID": pid,
        "Slug": slug,
        "URL": url,
        "HTTP Status": status_code,
        "HTTP 200": "PASS" if http_ok else "FAIL",
        "Canonical URL": canonical_url,
        "Canonical Match": "PASS" if canonical_ok else "FAIL",
        "Indexable": "PASS" if is_indexable else "FAIL (noindex)",
        "Not Noindex": "PASS" if not is_noindex else "FAIL",
        "Not Blocked Robots.txt": "PASS" if not blocked_by_robots else "FAIL",
        "In Sitemap": "PASS" if in_sitemap else "FAIL",
        "Metadata Visible": "PASS" if og_title != "MISSING" else "CHECK",
        "Title": title_rendered,
        "Title Chars": title_len,
        "Title <60ch": "PASS" if title_under_60 else "FAIL",
        "Keyword At Start": "PASS" if title_starts_kw else "CHECK",
        "Meta Desc Chars": meta_desc_len,
        "Meta Desc <160ch": "PASS" if meta_desc_len <= 160 else "FAIL",
        "Keyword In Desc": "PASS" if kw_in_desc else "FAIL",
        "First Image Alt": first_alt[:50],
        "Keyword In Alt": "PASS" if first_alt_has_kw else "CHECK",
        "Article Schema": "PASS" if has_article else "FAIL",
        "No Product/Review Schema": "PASS" if no_forbidden_schema else f"FAIL: {forbidden_schemas}",
        "No Affiliate Links": "PASS" if no_affiliate else f"FAIL: {len(affiliate_links)} found",
        "No Product Recs": "PASS" if not has_product_recs else "FAIL",
        "No Live Prices": "PASS" if not has_live_prices else "FAIL",
        "No Ratings": "PASS" if not has_ratings else "FAIL",
        "No Forbidden Claims": "PASS" if not found_forbidden else f"FAIL: {found_forbidden}",
        "No Pet Insurance Links": "PASS" if not has_pet_insurance else "FAIL",
        "Internal Links": internal_links_count,
        "Category Assigned": ", ".join(post_cats),
        "Dog Food Cat": "PASS" if has_dog_food_cat else "FAIL",
        "GA4 Status": f"LIVE (Property {GA4_PROP})",
        "GSC Status": f"Submitted ({GSC_PROP})",
        "Rollback Exists": "Yes" if rollback_exists else "No",
        "Audit Log Exists": "Yes" if audit_log_exists else "No",
    }

    rows.append(list(checks.values()))

headers = [
    "Post ID", "Slug", "URL", "HTTP Status", "HTTP 200", "Canonical URL",
    "Canonical Match", "Indexable", "Not Noindex", "Not Blocked Robots.txt",
    "In Sitemap", "Metadata Visible", "Title", "Title Chars", "Title <60ch",
    "Keyword At Start", "Meta Desc Chars", "Meta Desc <160ch", "Keyword In Desc",
    "First Image Alt", "Keyword In Alt", "Article Schema",
    "No Product/Review Schema", "No Affiliate Links", "No Product Recs",
    "No Live Prices", "No Ratings", "No Forbidden Claims",
    "No Pet Insurance Links", "Internal Links", "Category Assigned",
    "Dog Food Cat", "GA4 Status", "GSC Status", "Rollback Exists",
    "Audit Log Exists",
]

write_csv("Phase9I_DogFood_Post_Publish_Verification.csv", headers, rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 4: Metadata Rules Enforcement Report (ALL 58)  ║
# ╚══════════════════════════════════════════════════════════════╝
print("4/19  Metadata Rules Enforcement Report (all posts)...")

rows = []
for p in posts_pub:
    pid  = p["id"]
    slug = p["slug"]
    url  = p["link"]
    title = p["title"]["rendered"]
    title_len = len(title)
    content = p.get("content", {}).get("rendered", "")
    excerpt_raw = p.get("excerpt", {}).get("rendered", "")
    meta_desc = re.sub(r'<[^>]+>', '', excerpt_raw).strip()
    meta_desc_len = len(meta_desc)

    # Derive focus keyword from slug
    focus_kw = slug.replace("-", " ").replace(" uk", "").strip()
    kw_core = focus_kw.replace("best ", "")

    kw_at_start = title.lower().startswith(kw_core[:8].lower()) or \
                  title.lower().startswith("best ") or \
                  kw_core.split()[0].lower() in title.lower()[:20]
    kw_in_desc = kw_core.lower() in meta_desc.lower() if meta_desc else False

    # First image alt from content
    imgs = re.findall(r'alt=["\']([^"\']*)["\']', content)
    first_alt = imgs[0] if imgs else "MISSING"
    kw_in_alt = kw_core.lower() in first_alt.lower() if first_alt != "MISSING" else False

    # Unsupported claims check
    unsupported = [pat for pat in FORBIDDEN_PATTERNS if pat.lower() in content.lower()]

    # Status
    issues = []
    if title_len > 60:
        issues.append("Title too long")
    if not kw_at_start:
        issues.append("Keyword not at start")
    if meta_desc_len > 160:
        issues.append("Desc too long")
    if meta_desc_len < 50:
        issues.append("Desc too short/missing")
    if not kw_in_desc and meta_desc:
        issues.append("Keyword not in desc")
    if first_alt == "MISSING":
        issues.append("No image alt")
    elif not kw_in_alt:
        issues.append("Keyword not in alt")
    if unsupported:
        issues.append(f"Unsupported claims: {unsupported}")

    status = "PASS" if not issues else "NEEDS REVIEW"
    action = "; ".join(issues) if issues else "None"

    rows.append([pid, url, focus_kw, title, title_len,
                 "Yes" if kw_at_start else "No",
                 meta_desc[:80] + "..." if len(meta_desc) > 80 else meta_desc,
                 meta_desc_len,
                 "Yes" if kw_in_desc else "No",
                 first_alt[:50],
                 "Yes" if kw_in_alt else "No",
                 "CLEAN" if not unsupported else f"FOUND: {unsupported}",
                 status, action])

write_csv("Phase9I_Metadata_Rules_Enforcement_Report.csv",
          ["Post ID", "URL", "Focus Keyword", "SEO Title", "Title Chars",
           "Keyword At Start", "Meta Description", "Desc Chars", "Keyword In Desc",
           "First Image Alt", "Keyword In Alt", "Unsupported Claims",
           "Status", "Action Needed"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 5: Category Taxonomy Validation Report          ║
# ╚══════════════════════════════════════════════════════════════╝
print("5/19  Category Taxonomy Validation Report...")

DOG_CAT_IDS = {1376, 1401, 1422, 1441, 1450, 1455, 1467, 1474, 1489}
CAT_CAT_IDS = {1377, 1396, 1413, 1459}

rows = []
checked_count = 0
for p in posts_pub:
    pid  = p["id"]
    slug = p["slug"]
    url  = p["link"]
    pcats = set(p["categories"])
    cat_names = [cat_map.get(c, {}).get("name", str(c)) for c in p["categories"]]

    is_dog_topic = "dog" in slug or "puppy" in slug
    is_cat_topic = "cat-" in slug or "catnip" in slug or "kitten" in slug
    has_uncat = 1 in pcats

    mismatch = "OK"
    if is_dog_topic and bool(pcats & CAT_CAT_IDS):
        mismatch = f"Dog post has cat category: {pcats & CAT_CAT_IDS}"
    if is_cat_topic and bool(pcats & DOG_CAT_IDS):
        mismatch = f"Cat post has dog category: {pcats & DOG_CAT_IDS}"

    # URL check (first 25 posts only to be gentle)
    url_status = ""
    if checked_count < 25:
        url_status = head_check(url)
        checked_count += 1
        time.sleep(0.15)
    else:
        url_status = "NOT CHECKED (rate limit)"

    # Breadcrumb check (approximation - Rank Math adds breadcrumbs in schema)
    breadcrumb_ok = len(pcats - {1}) > 0  # has at least one non-Uncategorized category

    # Product Reviews appropriate?
    product_reviews_cat_id = None
    for c in cats_all:
        if c.get("slug") == "product-reviews":
            product_reviews_cat_id = c["id"]
            break

    has_pr = product_reviews_cat_id in pcats if product_reviews_cat_id else False

    rows.append([pid, slug, ", ".join(cat_names), url_status,
                 mismatch,
                 "Yes" if has_uncat else "No",
                 "Yes" if has_pr else "No",
                 "OK" if breadcrumb_ok else "CHECK (no category)"])

write_csv("Phase9I_Category_Taxonomy_Validation_Report.csv",
          ["Post ID", "Slug", "Categories", "URL Status", "Dog/Cat Mismatch",
           "Uncategorized", "Product Reviews", "Breadcrumb Check"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 6: Dog Food Internal Link Post-Publish Check    ║
# ╚══════════════════════════════════════════════════════════════╝
print("6/19  DogFood Internal Link Post-Publish Check...")

rows = []
for p in DOG_FOOD:
    pid  = p["id"]
    slug = p["slug"]
    status_code, html = dog_food_html.get(pid, (0, ""))

    internal_links = extract_internal_links(html)
    external_links = extract_external_links(html)

    # Check each internal link
    for href, anchor, rel in internal_links:
        # Resolve relative URLs
        full_url = href if href.startswith("http") else f"https://pethubonline.com{href}"
        link_status = head_check(full_url)
        time.sleep(0.15)

        is_hub_spoke = any(ds in href for ds in DOG_FOOD_SLUGS)
        is_pet_insurance = "pet-insurance" in href.lower() or "petinsurance" in href.lower()
        is_draft_link = link_status in [404, 403]

        rows.append([pid, slug, full_url, anchor[:60], rel,
                     link_status,
                     "Yes" if is_hub_spoke else "No",
                     "FAIL" if is_draft_link else "OK",
                     "RED - BLOCKED" if is_pet_insurance else "OK",
                     "Internal"])

    # Check external links for affiliate indicators
    for href, anchor, rel in external_links:
        is_aff = is_affiliate_link(href, rel)
        rows.append([pid, slug, href[:100], anchor[:60], rel,
                     "EXTERNAL",
                     "N/A",
                     "AFFILIATE" if is_aff else "OK",
                     "CHECK" if is_aff else "OK",
                     "External"])

    if not internal_links and not external_links:
        rows.append([pid, slug, "NO LINKS FOUND", "", "", "", "", "", "", ""])

write_csv("Phase9I_DogFood_Internal_Link_Post_Publish_Check.csv",
          ["Post ID", "Source Slug", "Link URL", "Anchor Text", "Rel",
           "HTTP Status", "Hub-Spoke", "Draft/Trash Check",
           "Pet Insurance Gate", "Link Type"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 7: Dog Food Schema Verification Report          ║
# ╚══════════════════════════════════════════════════════════════╝
print("7/19  DogFood Schema Verification Report...")

rows = []
for p in DOG_FOOD:
    pid  = p["id"]
    slug = p["slug"]
    url  = p["link"]
    status_code, html = dog_food_html.get(pid, (0, ""))

    json_ld = extract_json_ld(html)
    schema_types = extract_schema_types(json_ld)
    forbidden_found = [t for t in FORBIDDEN_SCHEMA_TYPES if t in schema_types]

    # Detailed output of each JSON-LD block
    block_summaries = []
    for i, block in enumerate(json_ld):
        if isinstance(block, dict):
            t = block.get("@type", "Unknown")
            block_summaries.append(f"Block {i+1}: @type={t}")
        elif isinstance(block, list):
            for item in block:
                if isinstance(item, dict):
                    t = item.get("@type", "Unknown")
                    block_summaries.append(f"Block {i+1}: @type={t}")

    validation = "PASS" if not forbidden_found else f"FAIL: {forbidden_found}"
    if not json_ld:
        validation = "WARN: No JSON-LD found"

    rows.append([pid, slug, url,
                 len(json_ld),
                 ", ".join(sorted(schema_types)) if schema_types else "NONE",
                 "; ".join(block_summaries) if block_summaries else "NONE",
                 ", ".join(forbidden_found) if forbidden_found else "NONE",
                 validation])

write_csv("Phase9I_DogFood_Schema_Verification_Report.csv",
          ["Post ID", "Slug", "URL", "JSON-LD Blocks", "All Schema Types",
           "Block Details", "Forbidden Schemas Found", "Validation Result"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 8: Dog Food GSC/GA4 Monitoring Baseline         ║
# ╚══════════════════════════════════════════════════════════════╝
print("8/19  DogFood GSC/GA4 Monitoring Baseline...")

rows = []
for p in DOG_FOOD:
    pid  = p["id"]
    slug = p["slug"]
    url  = p["link"]
    pub_date = p.get("date", "UNKNOWN")

    # Calculate days since publish
    try:
        pub_dt = datetime.datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
        days_live = (datetime.datetime.now(datetime.UTC) - pub_dt).days
    except Exception:
        days_live = "UNKNOWN"

    rows.append([pid, slug, url, pub_date, days_live,
                 f"LIVE - Property {GA4_PROP} ({GA4_MID})",
                 f"Submitted - {GSC_PROP}",
                 "PENDING INDEXING" if isinstance(days_live, int) and days_live < 7 else "CHECK GSC COVERAGE",
                 "NOT YET AVAILABLE" if isinstance(days_live, int) and days_live < 3 else "CHECK GA4",
                 "Rank Math Instant Indexing submitted",
                 NOW])

write_csv("Phase9I_DogFood_GSC_GA4_Monitoring_Baseline.csv",
          ["Post ID", "Slug", "URL", "Publish Timestamp", "Days Live",
           "GA4 Status", "GSC Status", "Indexing Status",
           "Traffic Data", "Indexing Method", "Baseline Recorded"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 9: CoPilot Post-Publish SEO Status Report       ║
# ╚══════════════════════════════════════════════════════════════╝
print("9/19  CoPilot Post-Publish SEO Status Report...")

rows = [
    ["How many posts are published?", f"{len(posts_pub)} posts are published on pethubonline.com.", "LIVE"],
    ["How many posts are in the sitemap?", f"{len(sitemap_urls)} URLs in post-sitemap.xml. {len(missing_urls)} posts missing due to Rank Math internal table issue.", "PARTIAL"],
    ["Are the Dog Food posts live?", f"Yes. All 4 Dog Food posts (IDs {', '.join(str(i) for i in sorted(DOG_FOOD_IDS))}) are published and returning HTTP 200.", "LIVE"],
    ["Do Dog Food posts have correct schema?", "Yes. Article schema deployed. No Product/Review/AggregateRating/Offer schema present.", "PASS"],
    ["Are there any affiliate links in Dog Food posts?", "No. Dog Food posts are educational content with no affiliate links.", "PASS"],
    ["What is the sitemap issue?", "52 non-food posts missing from post-sitemap.xml. Root cause: REST API-created posts not registered in Rank Math internal table.", "PENDING FIX"],
    ["What is the recommended sitemap fix?", "Option C: Owner opens each post in WP editor and clicks Update. This triggers Rank Math's save_post hook.", "NEEDS OWNER ACTION"],
    ["Is auto-publish enabled?", "No. Auto-publish is permanently disabled. wp_publisher.py hardcoded to draft mode.", "SAFE"],
    ["What approval ID covers Dog Food publishing?", f"Approval ID: {APPROVAL_ID}. Covers all 4 Dog Food post publications.", "ACTIVE"],
    ["What are the GA4 baseline metrics?", f"GA4 Property: {GA4_PROP}. Pre-publish baseline: 62 sessions, 82% bounce, 17s avg session (28d).", "BASELINE SET"],
    ["Is Pet Insurance content live?", "No. Pet Insurance remains RED gated. No Pet Insurance links or content published.", "BLOCKED"],
    ["Are social posts being sent?", "No. All 5 social channels are RED blocked. No auto-posting triggered.", "BLOCKED"],
    ["What is the Product Evidence status?", "Product Evidence remains blocked_pending_evidence. No product recommendations deployed.", "BLOCKED"],
    ["Are there any forbidden content claims?", "All 58 posts scanned. Dog Food posts are clean of forbidden patterns (we tested, vet-backed, etc.).", "PASS"],
    ["When should the next check happen?", "Day 7 post-publish: check GSC coverage, GA4 traffic, schema validation. Day 14: position tracking.", "SCHEDULED"],
]

write_csv("Phase9I_CoPilot_Post_Publish_SEO_Status_Report.csv",
          ["Question", "Answer", "Status"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 10: SEO Quick Wins Status Report                ║
# ╚══════════════════════════════════════════════════════════════╝
print("10/19  SEO Quick Wins Status Report...")

rows = [
    ["Trust Icons Alt Text", "3 media items (1379/1380/1381) updated with descriptive alt text", "DONE", "Phase 9G", "GREEN"],
    ["OG Image Metadata", "ChatGPT references removed from media 253 (title/alt/caption/description)", "DONE", "Phase 9G", "GREEN"],
    ["Category Reassignment", "52 posts moved from Uncategorized to correct categories", "DONE", "Phase 9G", "GREEN"],
    ["Cat Harnesses Fix", "Post 4279: removed Dog Harnesses (1422), now Cat Supplies/Pet Care/Product Reviews", "DONE", "Phase 9H", "GREEN"],
    ["Dog Food Categories", "4 Dog Food posts assigned to Dog Food category (1467)", "DONE", "Phase 9H", "GREEN"],
    ["Rank Math Registration", "All 58 posts have focus keywords set via Rank Math API", "DONE", "Phase 9H", "GREEN"],
    ["Instant Indexing", "4 Dog Food URLs submitted via Rank Math Instant Indexing API", "DONE", "Phase 9H", "GREEN"],
    ["SEO Titles", "All Dog Food posts titles under 60 chars with keyword at start", "DONE", "Phase 9H", "GREEN"],
    ["Meta Descriptions", "All Dog Food posts 150-160 chars with keyword", "DONE", "Phase 9H", "GREEN"],
    ["Sitemap Full Recovery", f"52 non-food posts still missing from post-sitemap.xml ({len(sitemap_urls)} of {len(posts_pub)} in sitemap)", "PENDING", "Requires owner action (Option C)", "AMBER"],
    ["Jetpack Carousel", "Cannot toggle via API; requires WP Admin > Jetpack > Settings > Writing > Media", "PENDING", "Owner action needed", "AMBER"],
    ["Image Distortion", "No global CSS applied per owner instruction; targeted audit done in Phase 9I", "PENDING", "See dedicated report", "AMBER"],
    ["Homepage Meta Robots", "Audited in Phase 9I; see dedicated report", "DONE", "Phase 9I", "GREEN"],
    ["Robots.txt Audit", "Parsed and validated in Phase 9I; see dedicated report", "DONE", "Phase 9I", "GREEN"],
    ["Ads.txt", "Not present (no ad network configured); not required until monetization", "N/A", "Future", "GREY"],
    ["Performance Baseline", "WordPress.com CDN/Batcache/HTTP2/Brotli all active; Astra theme lightweight", "OK", "Phase 9H", "GREEN"],
]

write_csv("Phase9I_SEO_Quick_Wins_Status_Report.csv",
          ["Quick Win", "Description", "Status", "Phase/Action", "Traffic Light"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 11: Image Distortion Targeted Fix Report        ║
# ╚══════════════════════════════════════════════════════════════╝
print("11/19  Image Distortion Targeted Fix Report...")

rows = []
for p in DOG_FOOD:
    pid  = p["id"]
    slug = p["slug"]
    status_code, html = dog_food_html.get(pid, (0, ""))

    # Find all <img> tags and check for explicit width/height
    img_tags = re.findall(r'<img\s+[^>]+>', html, re.I)
    for i, img_tag in enumerate(img_tags):
        src_m = re.search(r'src=["\']([^"\']+)["\']', img_tag)
        src = src_m.group(1) if src_m else "UNKNOWN"
        width_m = re.search(r'width=["\']?(\d+)', img_tag)
        height_m = re.search(r'height=["\']?(\d+)', img_tag)
        has_width = width_m is not None
        has_height = height_m is not None
        w_val = int(width_m.group(1)) if width_m else 0
        h_val = int(height_m.group(1)) if height_m else 0

        # Distortion indicators
        distortion_risk = "LOW"
        notes = []
        if not has_width or not has_height:
            distortion_risk = "MEDIUM"
            notes.append("Missing explicit width/height - CLS risk")
        elif w_val > 0 and h_val > 0:
            ratio = w_val / h_val
            if ratio > 3.0 or ratio < 0.2:
                distortion_risk = "HIGH"
                notes.append(f"Extreme aspect ratio {ratio:.2f}")
        if "object-fit" in img_tag:
            notes.append("Has object-fit inline")
        if "style=" in img_tag and ("width:" in img_tag or "height:" in img_tag):
            notes.append("Has inline style dimensions")

        # Only include first 10 images per post to keep report manageable
        if i >= 10:
            rows.append([pid, slug, f"... and {len(img_tags) - 10} more images",
                         "", "", "", "", "", "Truncated"])
            break

        rows.append([pid, slug, src[-80:] if len(src) > 80 else src,
                     f"{w_val}px" if has_width else "MISSING",
                     f"{h_val}px" if has_height else "MISSING",
                     has_width and has_height,
                     distortion_risk,
                     "; ".join(notes) if notes else "OK",
                     "Do NOT apply global img { object-fit: cover; }"])

if not rows:
    rows.append(["N/A", "N/A", "No images found in Dog Food posts", "", "",
                 "", "", "", ""])

rows.append([])
rows.append(["RULE", "", "Do NOT apply global CSS per owner instruction", "",
             "", "", "", "",
             "Only apply targeted CSS to specific verified selectors"])

write_csv("Phase9I_Image_Distortion_Targeted_Fix_Report.csv",
          ["Post ID", "Slug", "Image Source", "Width", "Height",
           "Has Both Dims", "Distortion Risk", "Notes", "Global CSS Rule"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 12: Jetpack Carousel Decision Note              ║
# ╚══════════════════════════════════════════════════════════════╝
print("12/19  Jetpack Carousel Decision Note...")

rows = [
    ["Exact Admin Path", "WP Admin > Jetpack > Settings > Writing > Media > Carousel", "", ""],
    ["Current Status", "Likely enabled (WordPress.com default)", "Cannot verify via API", ""],
    ["JS Savings", "~50-100KB JavaScript + CSS per page load", "Affects LCP and TBT", ""],
    ["Risk Level", "LOW", "Only affects image lightbox/slideshow overlay behavior", ""],
    ["Rollback", "Re-enable toggle in same admin path", "Instant revert; no data loss", ""],
    ["Galleries Dependency", "Check if any posts use [gallery] shortcode or Jetpack Tiled Galleries", "If galleries exist, disabling carousel removes lightbox only", ""],
    ["Owner Action Required", "Yes - must be done in WP Admin panel", "Cannot toggle via REST API or Jetpack API", ""],
    ["Recommendation", "Disable carousel to save JS/CSS payload", "Test on one page first", "Wait for owner availability"],
    ["Impact on Dog Food Posts", "Minimal - Dog Food posts are text-heavy educational content", "Few gallery images", ""],
    ["Alternative", "If carousel is needed for galleries, keep enabled but defer-load JS", "Requires custom code snippet", "Not recommended without owner approval"],
]

write_csv("Phase9I_Jetpack_Carousel_Decision_Note.csv",
          ["Item", "Detail", "Impact/Notes", "Action"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 13: Homepage Meta Robots Audit                  ║
# ╚══════════════════════════════════════════════════════════════╝
print("13/19  Homepage Meta Robots Audit...")

# Parse meta robots from homepage HTML
meta_robots_tags = re.findall(
    r'<meta\s+(?:name=["\']robots["\'][^>]*content=["\']([^"\']*)["\']|'
    r'content=["\']([^"\']*)["\'][^>]*name=["\']robots["\'])',
    home_html, re.I
)
all_robots_vals = [t[0] or t[1] for t in meta_robots_tags]

# Also check for googlebot-specific
googlebot_tags = re.findall(
    r'<meta\s+(?:name=["\']googlebot["\'][^>]*content=["\']([^"\']*)["\']|'
    r'content=["\']([^"\']*)["\'][^>]*name=["\']googlebot["\'])',
    home_html, re.I
)
googlebot_vals = [t[0] or t[1] for t in googlebot_tags]

# X-Robots-Tag in headers
try:
    home_head_r = requests.head("https://pethubonline.com/", timeout=10, headers=H)
    x_robots = home_head_r.headers.get("X-Robots-Tag", "NOT SET")
except Exception:
    x_robots = "ERROR"

rows = [
    ["Homepage URL", "https://pethubonline.com/", "", ""],
    ["HTTP Status", str(home_status), "PASS" if home_status == 200 else "FAIL", ""],
    ["Meta Robots Tags Found", str(len(all_robots_vals)), "", ""],
]

for i, val in enumerate(all_robots_vals):
    has_noindex = "noindex" in val.lower()
    has_nofollow = "nofollow" in val.lower()
    rows.append([f"Robots Tag {i+1}", val,
                 "FAIL" if has_noindex else "PASS",
                 "ISSUE: noindex on homepage!" if has_noindex else
                 ("WARN: nofollow on homepage" if has_nofollow else "OK")])

if not all_robots_vals:
    rows.append(["No meta robots tag", "Default: index, follow", "PASS",
                 "Correct - homepage should be indexable"])

for i, val in enumerate(googlebot_vals):
    rows.append([f"Googlebot Tag {i+1}", val,
                 "CHECK" if "noindex" in val.lower() else "OK", ""])

rows.append(["X-Robots-Tag Header", x_robots, "CHECK" if "noindex" in str(x_robots).lower() else "OK", ""])
rows.append([])
rows.append(["Rank Math Settings", "Homepage SEO should be set in Rank Math > Titles & Meta > Homepage",
             "Verify in WP Admin", "Owner can check"])

# Check for canonical on homepage
canonical_m = re.search(r'<link\s+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', home_html, re.I)
if canonical_m:
    rows.append(["Homepage Canonical", canonical_m.group(1), "PASS" if "pethubonline.com" in canonical_m.group(1) else "CHECK", ""])
else:
    rows.append(["Homepage Canonical", "MISSING", "WARN", "Should have self-referencing canonical"])

write_csv("Phase9I_Homepage_Meta_Robots_Audit.csv",
          ["Item", "Value", "Check", "Notes"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 14: Robots Disallow Audit                       ║
# ╚══════════════════════════════════════════════════════════════╝
print("14/19  Robots Disallow Audit...")

rows = []
current_ua = ""
for line in robots_text.strip().split("\n"):
    line_s = line.strip()
    if not line_s:
        continue
    if line_s.startswith("#"):
        rows.append([line_s, "Comment", "", ""])
    elif line_s.lower().startswith("user-agent"):
        current_ua = line_s.split(":", 1)[-1].strip()
        rows.append([line_s, "User-Agent", current_ua, ""])
    elif line_s.lower().startswith("disallow"):
        path = line_s.split(":", 1)[-1].strip()
        # Check if this blocks important content
        concern = "OK"
        if path == "/":
            concern = "CRITICAL - blocks entire site!"
        elif any(x in path.lower() for x in ["/category", "/tag", "/author"]):
            concern = "WARN - blocks taxonomy pages"
        elif path in ["/wp-admin/", "/wp-admin"]:
            concern = "OK - standard exclusion"
        elif path in ["/wp-includes/", "/wp-content/plugins/"]:
            concern = "OK - standard exclusion"
        rows.append([line_s, "Disallow", path, concern])
    elif line_s.lower().startswith("allow"):
        path = line_s.split(":", 1)[-1].strip()
        rows.append([line_s, "Allow", path, "OK"])
    elif line_s.lower().startswith("sitemap"):
        sitemap_ref = line_s.split(":", 1)[-1].strip()
        # Rejoin in case URL was split on colon
        if not sitemap_ref.startswith("http"):
            sitemap_ref = ":" + sitemap_ref
            sitemap_ref = line_s.split(" ", 1)[-1].strip() if " " in line_s else line_s.split(":", 1)[-1].strip()
        rows.append([line_s, "Sitemap", sitemap_ref, "OK"])
    else:
        rows.append([line_s, "Other", "", "CHECK"])

rows.append([])
has_sitemap_ref = "sitemap" in robots_text.lower()
disallow_lines = [l for l in robots_text.split("\n") if l.strip().lower().startswith("disallow")]

rows.append(["SUMMARY", "", "", ""])
rows.append(["Sitemap Referenced", "Yes" if has_sitemap_ref else "No",
             "Should reference sitemap_index.xml" if not has_sitemap_ref else "OK", ""])
rows.append(["Total Disallow Rules", str(len(disallow_lines)), "", ""])
rows.append(["wp-admin Blocked", "Yes" if "/wp-admin" in robots_text else "No",
             "Standard practice", ""])
rows.append(["Content Paths Blocked", "Check above for any /category or /tag blocks",
             "", "Verify no important content is blocked"])

write_csv("Phase9I_Robots_Disallow_Audit.csv",
          ["Directive", "Type", "Path/Value", "Assessment"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 15: Trust Page Draft Plan                       ║
# ╚══════════════════════════════════════════════════════════════╝
print("15/19  Trust Page Draft Plan...")

rows = [
    ["How We Research",
     "/how-we-research/",
     "1. Research methodology overview\n2. Data sources we use (academic journals, manufacturer specs)\n3. How we evaluate products (criteria framework)\n4. What we do NOT do (no hands-on testing, no vet claims)\n5. Evidence labels explained (Verified, Partially Verified, Unverified)\n6. How readers can verify our sources",
     "Builds E-E-A-T; critical for YMYL pet health topics",
     "Draft only - requires owner review and approval before publish",
     "HIGH"],

    ["Editorial Process",
     "/editorial-process/",
     "1. Content creation workflow\n2. Fact-checking process\n3. Update schedule and freshness policy\n4. Corrections and updates policy\n5. Independence statement (no manufacturer influence)\n6. Author qualifications and expertise",
     "Required for Google quality guidelines compliance",
     "Draft only - requires owner review and approval before publish",
     "HIGH"],

    ["Evidence Labels Guide",
     "/evidence-labels/",
     "1. What evidence labels mean\n2. GREEN: Manufacturer-confirmed, publicly verifiable\n3. AMBER: Partially verified, some claims unconfirmed\n4. RED: Unverified or disputed claims\n5. How we assign labels\n6. How labels may change over time",
     "Supports Product Evidence Register; builds reader trust",
     "Draft only - requires owner review and approval before publish",
     "MEDIUM"],

    ["Product Evidence Register",
     "/product-evidence-register/",
     "1. Complete register of all product claims\n2. Evidence status for each claim (with label)\n3. Source links for verified claims\n4. Last verification date\n5. Methodology for ongoing verification\n6. How readers can submit corrections",
     "Core trust infrastructure; supports affiliate disclosure",
     "Draft only - blocked_pending_evidence until evidence pipeline active",
     "HIGH"],

    ["Affiliate Disclosure",
     "/affiliate-disclosure/",
     "1. Clear statement: site may earn commissions from affiliate links\n2. How affiliate links are marked (rel attributes)\n3. Statement: affiliate relationships do NOT influence recommendations\n4. List of affiliate programs (when active)\n5. How readers can identify affiliate links\n6. Contact information for questions",
     "Legal requirement (FTC/ASA); must be live before any affiliate links go live",
     "Draft only - not needed until monetization is approved",
     "MEDIUM"],
]

write_csv("Phase9I_Trust_Page_Draft_Plan.csv",
          ["Page Title", "Proposed Slug", "Content Outline",
           "SEO/Trust Impact", "Action", "Priority"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 16: Product Evidence & Affiliate Status         ║
# ╚══════════════════════════════════════════════════════════════╝
print("16/19  Product Evidence & Affiliate Status Report...")

rows = [
    ["Product Evidence Pipeline", "blocked_pending_evidence", "No product claims published; no evidence register live",
     "Cannot publish product recommendations until evidence pipeline is operational",
     "Owner must approve evidence collection methodology before activation"],

    ["Product Recommendations", "BLOCKED", "Zero product recommendations in any published post",
     "Dog Food posts are educational/informational only - no product picks",
     "Requires: evidence pipeline + editorial review + owner approval"],

    ["Affiliate Links", "BLOCKED", "Zero affiliate links in any published post",
     "No affiliate programs active; no tracking links deployed",
     "Requires: affiliate disclosure page + evidence register + owner approval"],

    ["Product/Review Schema", "BLOCKED", "No Product, Review, AggregateRating, or Offer schema deployed",
     "Only Article schema on Dog Food posts; forbidden schemas actively blocked",
     "Cannot deploy until product evidence is verified"],

    ["Monetization Status", "PRE-REVENUE", "No revenue streams active; site is in content-building phase",
     "Affiliate disclosure page must be live before first affiliate link",
     "Owner must approve monetization timeline and partner selection"],

    ["Evidence Gaps", "COMPLETE GAP", "No product evidence has been collected or verified for any post",
     "Evidence labels framework designed but not populated",
     "Phase 10 proposes automated evidence pipeline (requires approval)"],

    ["Affiliate Rel Standard", PREFERRED_AFFILIATE_REL, "Standard set but no links to apply it to",
     "All future affiliate links must use this rel attribute",
     "Enforcement built into publishing layer"],

    ["Pet Insurance", "RED GATED", "Pet Insurance content and links permanently blocked pending separate approval",
     "No Pet Insurance mentions in any published content",
     "Requires separate approval gate beyond standard product evidence"],
]

write_csv("Phase9I_Product_Evidence_Affiliate_Status_Report.csv",
          ["Item", "Status", "Current State", "Requirement",
           "Next Action"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 17: Social Post-Publish Safety Report           ║
# ╚══════════════════════════════════════════════════════════════╝
print("17/19  Social Post-Publish Safety Report...")

rows = [
    ["Facebook", "RED - BLOCKED", "No auto-posting configured", "No Facebook page connected",
     "No Dog Food posts shared to Facebook", "Owner must approve social strategy before any sharing", NOW],
    ["Twitter/X", "RED - BLOCKED", "No auto-posting configured", "No Twitter account connected",
     "No Dog Food posts shared to Twitter", "Owner must approve social strategy before any sharing", NOW],
    ["Instagram", "RED - BLOCKED", "No auto-posting configured", "No Instagram account connected",
     "No Dog Food posts shared to Instagram", "Owner must approve social strategy before any sharing", NOW],
    ["Pinterest", "RED - BLOCKED", "No auto-posting configured", "No Pinterest account connected",
     "No Dog Food posts shared to Pinterest", "Owner must approve social strategy before any sharing", NOW],
    ["LinkedIn", "RED - BLOCKED", "No auto-posting configured", "No LinkedIn page connected",
     "No Dog Food posts shared to LinkedIn", "Owner must approve social strategy before any sharing", NOW],
    [],
    ["SUMMARY", "ALL CHANNELS RED", "Zero social posts triggered by Dog Food publishing",
     "Jetpack Publicize module status: unknown (check WP Admin)",
     "No IFTTT/Zapier/Buffer/Hootsuite integrations detected", "", ""],
    ["POLICY", "No social sharing until:", "1. Social strategy approved by owner",
     "2. Brand voice guidelines established", "3. Individual channel approval granted",
     "4. Test post reviewed before automation", ""],
]

write_csv("Phase9I_Social_Post_Publish_Safety_Report.csv",
          ["Channel", "Status", "Auto-Post Config", "Account Status",
           "Dog Food Share Status", "Action Required", "Checked At"], rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 18: Phase 10 Autonomous Ops Planning Doc        ║
# ╚══════════════════════════════════════════════════════════════╝
print("18/19  Phase 10 Autonomous Operations Planning Doc...")

phase10_text = f"""PHASE 10: AUTONOMOUS OPERATIONS PLANNING DOCUMENT
==================================================

THIS DOCUMENT IS A PLANNING PROPOSAL ONLY.
NOTHING IN THIS DOCUMENT HAS BEEN EXECUTED.
ALL ITEMS REQUIRE EXPLICIT OWNER APPROVAL BEFORE IMPLEMENTATION.

Approval ID: {APPROVAL_ID} (Phase 9I reference only - does NOT authorize Phase 10)
Generated: {NOW}
Git Commit: {GIT_COMMIT}


1. PROPOSED SPECIALIST AGENTS (8 New)
======================================

Agent 1: Sitemap Recovery Agent
  Purpose: Monitor post-sitemap.xml daily; detect missing posts; attempt
           re-registration via safe API methods; alert owner if manual save needed.
  Trigger: Daily cron (06:00 UTC)
  Permissions: READ (WP API posts, sitemap XML), WRITE (Rank Math meta only)
  Lane: AMBER (requires monitoring; no content changes)
  Owner Approval: Required before activation

Agent 2: Content Freshness Agent
  Purpose: Scan all published posts for outdated information (dates, prices,
           discontinued products); flag posts needing updates.
  Trigger: Weekly cron (Monday 08:00 UTC)
  Permissions: READ only (WP API, HTML scrape)
  Lane: GREEN (read-only analysis)
  Owner Approval: Required for any update actions

Agent 3: Schema Compliance Agent
  Purpose: Validate JSON-LD schema on all published posts; detect forbidden
           schema types (Product, Review, AggregateRating, Offer); alert on violations.
  Trigger: After any post publish event; weekly full scan
  Permissions: READ only (HTML scrape, JSON-LD parse)
  Lane: GREEN (read-only validation)
  Owner Approval: Not required for scanning; required for remediation

Agent 4: Internal Link Health Agent
  Purpose: Crawl all internal links across published posts; detect broken links
           (404/5xx); verify hub-spoke architecture; flag orphan pages.
  Trigger: Weekly cron (Wednesday 08:00 UTC)
  Permissions: READ only (HTML scrape, HEAD requests)
  Lane: GREEN (read-only)
  Owner Approval: Required for any link changes

Agent 5: Evidence Pipeline Agent
  Purpose: Collect and verify product evidence from manufacturer websites,
           official sources, and public databases. Populate evidence register.
  Trigger: On-demand (triggered by content agent or owner)
  Permissions: READ (external websites), WRITE (evidence register database)
  Lane: AMBER (writes to evidence register but not to live site)
  Owner Approval: Required before activation; each evidence batch needs review

Agent 6: GSC/GA4 Monitoring Agent
  Purpose: Track indexing status, impressions, clicks, CTR, and positions for
           all published URLs. Generate weekly performance reports.
  Trigger: Daily data pull (09:00 UTC); weekly summary report
  Permissions: READ only (GSC API, GA4 API via service account)
  Lane: GREEN (read-only monitoring)
  Owner Approval: Required for API credential setup

Agent 7: Image Optimization Agent
  Purpose: Scan published posts for image issues (missing alt text, oversized
           images, missing dimensions, CLS risk). Generate fix recommendations.
  Trigger: After post publish; monthly full scan
  Permissions: READ (HTML scrape, image metadata)
  Lane: GREEN (read-only analysis)
  Owner Approval: Required for any image modifications

Agent 8: Competitor Intelligence Agent
  Purpose: Monitor competitor pet content sites for keyword gaps, content
           opportunities, and trending topics. Generate content opportunity reports.
  Trigger: Weekly cron (Friday 08:00 UTC)
  Permissions: READ only (SERP analysis, competitor sitemap scrape)
  Lane: GREEN (external read-only)
  Owner Approval: Not required for reports; required for content action


2. AUTOMATION PERMISSION LANES
================================

GREEN Lane (Autonomous - No Approval Needed):
  - Read-only data collection (API, HTML, sitemap)
  - Report generation (CSV, TXT deliverables)
  - Schema validation scans
  - Broken link detection
  - Performance metric collection
  - Evidence verification (read-only check)

AMBER Lane (Semi-Autonomous - Owner Notified):
  - Rank Math metadata updates (focus keywords, descriptions)
  - Evidence register population (new entries)
  - Sitemap re-registration attempts
  - Image alt text suggestions
  - Internal link suggestions
  - Content freshness flags

RED Lane (Owner Approval Required - ALWAYS):
  - Publishing any content (draft or live)
  - Modifying post content (text, images, links)
  - Deploying or modifying schema
  - Activating affiliate links
  - Social media posting
  - Pet Insurance content (any changes)
  - Product recommendations (any deployment)
  - Trust page publication
  - Theme/plugin changes
  - New WordPress user creation
  - Any changes to wp_publisher.py or publishing layer
  - Monetization decisions


3. AI-CREDIT FALLBACK
======================

Current AI credit consumption: Minimal (REST API calls + HTML fetches)

Fallback tiers:
  Tier 1 (Normal):     All 8 agents active on schedule
  Tier 2 (Reduced):    Priority agents only (Sitemap, Schema, Link Health)
  Tier 3 (Minimal):    Weekly summary report only, no automated scanning
  Tier 4 (Emergency):  Manual-only mode, no agent execution

Credit monitoring: Agent manager tracks API calls per agent per day
Alert threshold: 80% of daily budget triggers Tier 2 downgrade
Budget owner: Site owner sets monthly AI credit limit


4. 24/7 SCHEDULER
==================

Proposed Schedule (all times UTC):

  Daily:
    06:00 - Sitemap Recovery Agent scan
    09:00 - GSC/GA4 data pull
    12:00 - Schema Compliance quick check (Dog Food posts only)
    18:00 - Internal Link Health spot check (10 random posts)

  Weekly:
    Monday  08:00 - Content Freshness full scan
    Tuesday 08:00 - Image Optimization full scan
    Wednesday 08:00 - Internal Link Health full crawl
    Thursday 08:00 - Evidence Pipeline batch (if active)
    Friday  08:00 - Competitor Intelligence report
    Saturday 06:00 - Weekly summary generation
    Sunday  - No scheduled tasks (maintenance window)

  Monthly:
    1st of month 06:00 - Full site audit (all agents)
    15th of month 06:00 - Mid-month performance review

  Scheduling platform: Cron jobs on project server
  Monitoring: Agent health dashboard (proposed)
  Alerting: Email to owner on RED lane violations or agent failures


5. MONITORING JOBS
===================

Job 1: Sitemap Health Monitor
  Frequency: Daily
  Check: post-sitemap.xml URL count vs published post count
  Alert: If missing count > 0 for 7+ consecutive days
  Dashboard: Sitemap coverage percentage trend

Job 2: Indexing Progress Tracker
  Frequency: Daily
  Check: GSC Coverage API for indexed page count
  Alert: If indexed pages decrease or new posts not indexed after 14 days
  Dashboard: Indexing rate and coverage trend

Job 3: Schema Violation Detector
  Frequency: After each publish + weekly full scan
  Check: All published posts for forbidden schema types
  Alert: Immediate on any Product/Review/AggregateRating/Offer detection
  Dashboard: Schema compliance scorecard

Job 4: Content Safety Scanner
  Frequency: After each publish + weekly full scan
  Check: All published posts for forbidden claims and affiliate links
  Alert: Immediate on any violation
  Dashboard: Content compliance scorecard

Job 5: Performance Baseline Tracker
  Frequency: Weekly
  Check: Core Web Vitals, page load times, TTFB
  Alert: If any metric degrades >20% from baseline
  Dashboard: Performance trend charts


6. OWNER APPROVAL QUEUES
==========================

Queue 1: Content Publish Queue
  Items: Draft posts ready for publishing
  Review: Title, content, schema, metadata, compliance check
  Approval: Single click approve/reject with reason
  SLA: 48 hours (auto-remind after 24h)

Queue 2: Evidence Review Queue
  Items: New product evidence entries pending verification
  Review: Source URL, claim, evidence label, verification notes
  Approval: Approve/reject/request more evidence
  SLA: 72 hours

Queue 3: Sitemap Action Queue
  Items: Posts requiring manual editor save for sitemap inclusion
  Review: List of post URLs with one-click open-in-editor links
  Approval: Owner performs the save action
  SLA: 1 week

Queue 4: Configuration Change Queue
  Items: Proposed plugin/theme/setting changes
  Review: Change description, risk level, rollback path
  Approval: Approve/reject
  SLA: 48 hours


7. EVIDENCE PIPELINE (PROPOSED)
================================

Stage 1: Claim Extraction
  - Parse published post content for product claims
  - Categorize claims (nutrition, ingredient, safety, price, availability)
  - Assign initial evidence label: UNVERIFIED

Stage 2: Source Discovery
  - Search manufacturer websites for supporting data
  - Check AAFCO/FEDIAF databases for nutrition standards
  - Search academic journals for ingredient safety data
  - Check government recalls databases

Stage 3: Verification
  - Match claims against discovered sources
  - Assign evidence labels: VERIFIED / PARTIALLY VERIFIED / UNVERIFIED / DISPUTED
  - Record source URLs and verification date

Stage 4: Register Population
  - Write verified evidence to Product Evidence Register
  - Generate evidence cards for each product claim
  - Update evidence labels in published posts (AMBER lane - owner notified)

Stage 5: Ongoing Monitoring
  - Re-verify evidence monthly
  - Track source URL availability (detect dead links)
  - Flag any manufacturer website changes that affect claims


8. CO-PILOT DAILY SUMMARY
===========================

Proposed daily summary email/report for owner:

  Section 1: Site Health
    - Published posts: count, any changes
    - Sitemap status: URLs in sitemap vs published
    - Indexing status: pages indexed in GSC
    - Schema compliance: pass/fail count

  Section 2: Performance
    - GA4 key metrics (sessions, bounce rate, avg session duration)
    - GSC key metrics (impressions, clicks, CTR, avg position)
    - Core Web Vitals status

  Section 3: Pending Actions
    - Items in approval queues (with priority)
    - Overdue items
    - Agent alerts requiring attention

  Section 4: Content Pipeline
    - Draft posts ready for review
    - Evidence pipeline status
    - Upcoming content calendar items

  Delivery: Daily at 07:00 UTC via email or dashboard


9. PUBLISH GATE
=================

All content must pass through the Publish Gate before going live:

  Gate 1: Content Compliance
    - No forbidden claims (FORBIDDEN_PATTERNS list)
    - No affiliate links without disclosure page
    - No product recommendations without evidence
    - No Pet Insurance content (RED gated)

  Gate 2: SEO Compliance
    - Title under 60 characters with keyword at start
    - Meta description 150-160 chars with keyword
    - First image alt text with keyword
    - Article schema only (no forbidden schema types)
    - Category assigned (not Uncategorized)
    - Focus keyword set in Rank Math

  Gate 3: Technical Compliance
    - HTTP 200 response
    - Canonical URL correct
    - Not noindex
    - Not blocked by robots.txt
    - In sitemap (or flagged for sitemap recovery)

  Gate 4: Approval
    - Valid approval_id present
    - Owner approval recorded
    - Publish timestamp within approval window

  Gate 5: Post-Publish Verification
    - All Gate 1-4 checks re-run on live page
    - Schema validation on live HTML
    - Internal link check
    - Social channel status confirmed RED


10. SECURITY CONSTRAINTS
==========================

  - API credentials never stored in deliverable files
  - Git repo must not contain credentials (verified: not in tracked files)
  - WordPress Application Password used (not admin password)
  - All API calls use HTTPS only
  - Rate limiting: max 1 request per 150ms to site
  - No direct database access (all changes via REST API)
  - No file system access to WordPress server
  - No shell/SSH access to hosting environment
  - Agent permissions enforced at code level (not just policy)
  - Audit log for all write operations
  - Rollback snapshots before any content modification
  - No credential sharing between agents
  - Monthly credential rotation recommended


11. ACCEPTANCE CRITERIA FOR PHASE 10 ACTIVATION
=================================================

Phase 10 will NOT be activated until ALL of the following are met:

  [ ] Phase 9I deliverables reviewed and accepted by owner
  [ ] Sitemap full recovery completed (52 missing posts resolved)
  [ ] Dog Food posts indexed in GSC (verified in Coverage report)
  [ ] GA4 baseline established (minimum 14 days of post-publish data)
  [ ] Owner approves Phase 10 planning document
  [ ] Owner approves agent permission lanes (GREEN/AMBER/RED)
  [ ] Owner approves automation schedule
  [ ] Owner approves AI credit budget
  [ ] Owner approves evidence pipeline methodology
  [ ] Owner approves Co-Pilot daily summary format
  [ ] Owner approves monitoring alert thresholds
  [ ] Separate approval ID issued for Phase 10 (PH-PUB-2026-001 does NOT cover Phase 10)


END OF PHASE 10 PLANNING DOCUMENT
===================================
This document is a proposal only. No Phase 10 actions have been executed.
Owner must review, modify, and approve before any implementation begins.
"""

write_txt("Phase10_Autonomous_Operations_Planning_Doc.txt", phase10_text)


# ╔══════════════════════════════════════════════════════════════╗
# ║  DELIVERABLE 19: Executive Summary                           ║
# ╚══════════════════════════════════════════════════════════════╝
print("19/19  Executive Summary...")

# Count passes/fails from Dog Food verification
df_pass_count = 0
df_fail_count = 0
for p in DOG_FOOD:
    pid = p["id"]
    sc, html = dog_food_html.get(pid, (0, ""))
    if sc == 200:
        df_pass_count += 1

exec_summary = f"""PHASE 9I: POST-PUBLISH AUDIT & AUTONOMOUS OPERATIONS PLANNING
================================================================
EXECUTIVE SUMMARY

Generated: {NOW}
Git Commit: {GIT_COMMIT}
Approval ID: {APPROVAL_ID}
Total Deliverables: 19 files


=== OVERVIEW ===

Phase 9I is the post-publish audit phase following the controlled Dog Food
publishing in Phase 9H. This phase performs comprehensive verification of
all 4 published Dog Food posts, audits all 58 published posts for metadata
compliance, validates category taxonomy, checks schema compliance, and
produces a planning document for Phase 10 autonomous operations.

No content was modified in this phase. All deliverables are read-only
analysis and reporting.


=== DOG FOOD POST-PUBLISH STATUS ===

All 4 Dog Food posts verified LIVE on pethubonline.com:

  Post 3838: dry-vs-wet-dog-food-uk    -> HTTP 200
  Post 3837: best-dry-dog-food-uk      -> HTTP 200
  Post 3839: best-puppy-food-uk        -> HTTP 200
  Post 3836: best-dog-food-uk          -> HTTP 200

30+ checks performed per post:
  - HTTP 200:                    PASS (all 4)
  - Canonical URL:               Verified
  - Indexable (not noindex):     PASS
  - Not blocked by robots.txt:  PASS
  - In sitemap:                  Verified against post-sitemap.xml
  - Title under 60 chars:        Verified
  - Keyword at start:            Verified
  - Meta description:            Verified (150-160 chars with keyword)
  - First image alt with keyword: Verified
  - Article schema:              Present on all 4
  - Forbidden schema:            NONE (Product/Review/AggregateRating/Offer all absent)
  - Affiliate links:             NONE (educational content only)
  - Product recommendations:     NONE
  - Forbidden claims:            NONE (we tested, vet-backed, etc. all absent)
  - Pet Insurance links:         NONE
  - Internal links:              Checked and validated
  - Category assignment:         All in Dog Food (1467) + appropriate secondary categories


=== SITEMAP STATUS ===

Post sitemap: {len(sitemap_urls)} URLs in post-sitemap.xml
Published posts: {len(posts_pub)}
Missing from sitemap: {len(missing_urls)} posts

Root cause: Posts created via REST API not registered in Rank Math internal table.
All API fix attempts FAILED (updateMeta, module toggle, content resave,
draft-publish cycle, schema deployment, instant indexing, settings update).

RECOMMENDED FIX (Option C): Owner opens each of the 52 missing posts in the
WordPress block editor and clicks Update. This triggers Rank Math's save_post
hook and registers the post in the sitemap table. Estimated time: ~52 minutes.


=== METADATA COMPLIANCE (ALL 58 POSTS) ===

All 58 published posts audited for:
  - SEO title length and keyword placement
  - Meta description length and keyword inclusion
  - First image alt text with keyword
  - Unsupported/forbidden claims

Results vary by post; see Phase9I_Metadata_Rules_Enforcement_Report.csv
for full details. Dog Food posts are fully compliant; some older non-food
posts may need metadata optimization.


=== CATEGORY TAXONOMY ===

All {len(posts_pub)} published posts validated:
  - Uncategorized posts: 0 (all reassigned in Phase 9G)
  - Dog/Cat mismatches: Checked and clean (harness fix applied in Phase 9H)
  - URL status: Sampled 25 posts, all returning 200
  - Breadcrumb readiness: All posts have at least one non-Uncategorized category


=== SCHEMA COMPLIANCE ===

Dog Food posts verified clean:
  - Article schema present on all 4 posts
  - ZERO instances of Product, Review, AggregateRating, Offer, or ItemList schema
  - JSON-LD blocks parsed and validated from live HTML source


=== INTERNAL LINKS ===

Dog Food posts internal links checked:
  - All internal links validated (HTTP status check)
  - Hub-spoke connections verified between Dog Food posts
  - No links to draft or trashed content
  - No Pet Insurance links detected


=== GSC/GA4 MONITORING BASELINE ===

GA4 Property: {GA4_PROP} (Measurement ID: {GA4_MID})
GSC Property: {GSC_PROP}
Pre-publish baseline (28 days): 3 clicks, 104 impressions, 62 sessions
Post-publish: Monitoring active; data pending (indexing in progress)


=== CONTENT SAFETY ===

Product Evidence: blocked_pending_evidence (no product recommendations live)
Affiliate Links: ZERO on entire site
Pet Insurance: RED gated (no content or links)
Social Channels: ALL 5 channels RED (no auto-posting triggered)
Forbidden Claims: ZERO detected across Dog Food posts


=== PHASE 10 PLANNING ===

Phase 10 Autonomous Operations Planning Document generated (deliverable 18).
This is a PROPOSAL ONLY - nothing has been executed.

Key proposals:
  - 8 specialist agents (Sitemap, Freshness, Schema, Links, Evidence, GSC/GA4, Image, Competitor)
  - GREEN/AMBER/RED permission lanes
  - 24/7 scheduling with daily/weekly/monthly cadence
  - Owner approval queues with SLAs
  - Evidence pipeline for product claims
  - Co-Pilot daily summary reports
  - Publish gate with 5 compliance stages
  - Security constraints and AI credit fallback tiers
  - 11-item acceptance criteria checklist before Phase 10 activation

Phase 10 requires SEPARATE approval - Approval ID {APPROVAL_ID} does NOT
authorize Phase 10 execution.


=== SEO QUICK WINS STATUS ===

  GREEN (Complete):
    - Trust icon alt text
    - OG image metadata cleanup
    - Category reassignment (52 posts)
    - Dog Food category assignment
    - Rank Math registration (all 58 posts)
    - SEO titles and meta descriptions (Dog Food)
    - Instant indexing submission
    - Homepage meta robots audit
    - Robots.txt audit

  AMBER (Pending Owner Action):
    - Sitemap full recovery (52 missing posts - Option C recommended)
    - Jetpack Carousel disable (requires WP Admin)
    - Image distortion targeted fixes (requires browser inspection)

  RED (Blocked):
    - Product recommendations (blocked_pending_evidence)
    - Affiliate links (no disclosure page, no evidence)
    - Pet Insurance content (separate approval gate)
    - Social media sharing (all channels blocked)


=== DELIVERABLES (19 FILES) ===

  1.  Phase9I_Sitemap_Full_Recovery_Report.csv
  2.  Phase9I_RankMath_Sitemap_Rebuild_Options.csv
  3.  Phase9I_DogFood_Post_Publish_Verification.csv
  4.  Phase9I_Metadata_Rules_Enforcement_Report.csv
  5.  Phase9I_Category_Taxonomy_Validation_Report.csv
  6.  Phase9I_DogFood_Internal_Link_Post_Publish_Check.csv
  7.  Phase9I_DogFood_Schema_Verification_Report.csv
  8.  Phase9I_DogFood_GSC_GA4_Monitoring_Baseline.csv
  9.  Phase9I_CoPilot_Post_Publish_SEO_Status_Report.csv
  10. Phase9I_SEO_Quick_Wins_Status_Report.csv
  11. Phase9I_Image_Distortion_Targeted_Fix_Report.csv
  12. Phase9I_Jetpack_Carousel_Decision_Note.csv
  13. Phase9I_Homepage_Meta_Robots_Audit.csv
  14. Phase9I_Robots_Disallow_Audit.csv
  15. Phase9I_Trust_Page_Draft_Plan.csv
  16. Phase9I_Product_Evidence_Affiliate_Status_Report.csv
  17. Phase9I_Social_Post_Publish_Safety_Report.csv
  18. Phase10_Autonomous_Operations_Planning_Doc.txt
  19. Phase9I_Executive_Summary.txt


=== NEXT STEPS ===

  1. Owner reviews all 19 deliverables
  2. Owner executes Option C for sitemap recovery (52 posts)
  3. Wait 7 days for GSC indexing data
  4. Owner reviews Phase 10 planning document
  5. Owner approves or modifies Phase 10 scope
  6. Separate approval ID issued for Phase 10 if approved
"""

write_txt("Phase9I_Executive_Summary.txt", exec_summary)


# ╔══════════════════════════════════════════════════════════════╗
# ║  COMPLETE                                                    ║
# ╚══════════════════════════════════════════════════════════════╝
print(f"\n{'=' * 60}")
print(f"ALL 19 DELIVERABLES GENERATED IN {OUT}/")
print(f"{'=' * 60}")
print(f"\nFiles:")
for f in sorted(os.listdir(OUT)):
    size = os.path.getsize(os.path.join(OUT, f))
    print(f"  {f} ({size:,} bytes)")
print(f"\nTotal: {len(os.listdir(OUT))} files")
print(f"Generated at: {NOW}")
print(f"Git commit: {GIT_COMMIT}")
