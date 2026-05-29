#!/usr/bin/env python3
"""
PetHub Online - Indexation & Crawl Intelligence Engine
======================================================
Comprehensive crawl analysis for pethubonline.com
- WordPress REST API inventory (posts, pages, categories)
- XML sitemap parsing & cross-reference
- robots.txt compliance check
- HEAD request status/canonical/robots-tag audit
- CSV report generation
"""

import csv
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urlparse, urljoin

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "https://pethubonline.com"
WP_API_BASE = f"{BASE_URL}/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase11_data"

API_SLEEP = 2        # seconds between WP API calls
HEAD_SLEEP = 1        # seconds between HEAD checks
MAX_HEAD_CHECKS = 50  # cap on HEAD requests
MAX_RETRIES = 3       # retry count for failed requests
CURL_TIMEOUT = 30     # seconds

# Pet product cluster keywords (for classification)
CLUSTER_KEYWORDS = {
    "dog": ["dog", "puppy", "canine", "k9"],
    "cat": ["cat", "kitten", "feline"],
    "bird": ["bird", "parrot", "avian", "budgie", "cockatiel"],
    "fish": ["fish", "aquarium", "aquatic", "tank", "reef"],
    "reptile": ["reptile", "lizard", "snake", "turtle", "gecko"],
    "small-animal": ["hamster", "rabbit", "guinea pig", "ferret", "gerbil", "small animal"],
    "food": ["food", "treat", "nutrition", "diet", "kibble", "feed"],
    "health": ["health", "supplement", "vitamin", "flea", "tick", "worm", "vet", "medicine"],
    "accessories": ["toy", "collar", "leash", "bed", "crate", "bowl", "feeder", "harness"],
    "grooming": ["groom", "shampoo", "brush", "nail", "bath"],
}


def classify_cluster(title, url):
    """Classify a page into a product/content cluster based on title + URL."""
    text = f"{title} {url}".lower()
    scores = {}
    for cluster, keywords in CLUSTER_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[cluster] = score
    if scores:
        return max(scores, key=scores.get)
    return "general"


# ---------------------------------------------------------------------------
# Curl helper with retry + exponential backoff
# ---------------------------------------------------------------------------
def curl_fetch(url, auth=None, method="GET", headers_only=False, retries=MAX_RETRIES):
    """
    Fetch a URL using subprocess curl. Returns (body, headers_dict, status_code).
    For headers_only (HEAD), body will be empty.
    """
    for attempt in range(1, retries + 1):
        try:
            cmd = ["curl", "-s", "--compressed", "--max-time", str(CURL_TIMEOUT)]

            if headers_only:
                # Use -I for HEAD, and -o /dev/null -D - for headers
                cmd += ["-I"]
            else:
                # Include headers in output so we can parse them
                cmd += ["-D", "-"]

            if auth:
                cmd += ["-u", auth]

            # Follow redirects but capture the final status
            cmd += ["-L", "--write-out", "\n%{http_code}", url]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=CURL_TIMEOUT + 10)

            raw = result.stdout
            if not raw.strip():
                raise ValueError(f"Empty response from {url}")

            # The last line is the HTTP status code (from --write-out)
            lines = raw.rsplit("\n", 1)
            status_code = 0
            body_and_headers = raw
            if lines:
                try:
                    status_code = int(lines[-1].strip())
                    body_and_headers = lines[0]
                except ValueError:
                    body_and_headers = raw

            if headers_only:
                # For HEAD requests, everything is headers
                headers = _parse_headers(body_and_headers)
                return "", headers, status_code
            else:
                # Split headers from body (separated by \r\n\r\n)
                # With -L (follow redirects), there may be multiple header blocks
                parts = re.split(r'\r?\n\r?\n', body_and_headers)
                if len(parts) >= 2:
                    # Last header block is the final response headers
                    # Body is everything after the last header block
                    # Find the boundary: headers end, body begins
                    header_text = ""
                    body = body_and_headers
                    # Walk through to find last HTTP header block
                    for i, part in enumerate(parts):
                        if part.strip().startswith("HTTP/"):
                            header_text = part
                            body = "\r\n\r\n".join(parts[i + 1:])
                    headers = _parse_headers(header_text)
                else:
                    headers = {}
                    body = body_and_headers

                return body, headers, status_code

        except (subprocess.TimeoutExpired, Exception) as e:
            if attempt < retries:
                wait = 2 ** attempt
                print(f"  [RETRY {attempt}/{retries}] {url}: {e} -- waiting {wait}s")
                time.sleep(wait)
            else:
                print(f"  [FAILED] {url}: {e}")
                return "", {}, 0

    return "", {}, 0


def _parse_headers(header_text):
    """Parse raw HTTP headers into a dict (lowercase keys)."""
    headers = {}
    for line in header_text.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            headers[key.strip().lower()] = value.strip()
    return headers


def curl_fetch_json(url, auth=AUTH):
    """Fetch JSON from a URL, return (parsed_data, headers, status)."""
    body, headers, status = curl_fetch(url, auth=auth)
    try:
        data = json.loads(body) if body.strip() else None
    except json.JSONDecodeError as e:
        print(f"  [JSON ERROR] {url}: {e}")
        data = None
    return data, headers, status


# ---------------------------------------------------------------------------
# 1. WordPress REST API: posts, pages, categories
# ---------------------------------------------------------------------------
def fetch_wp_collection(endpoint, label="items"):
    """Paginate through a WP REST API collection endpoint."""
    all_items = []
    page = 1
    total_pages = 1

    while page <= total_pages:
        sep = "&" if "?" in endpoint else "?"
        url = f"{WP_API_BASE}/{endpoint}{sep}per_page=100&page={page}"
        print(f"  Fetching {label} page {page}/{total_pages}: {url}")

        data, headers, status = curl_fetch_json(url)

        if status == 400 and page > 1:
            # WP returns 400 when page exceeds total -- we're done
            break

        if data is None or not isinstance(data, list):
            print(f"  [WARN] Unexpected response for {label} page {page} (status={status})")
            break

        all_items.extend(data)

        # Parse total pages from headers
        tp = headers.get("x-wp-totalpages", "1")
        try:
            total_pages = int(tp)
        except ValueError:
            total_pages = 1

        total_items_hdr = headers.get("x-wp-total", "?")
        if page == 1:
            print(f"  Total {label}: {total_items_hdr} across {total_pages} page(s)")

        page += 1
        if page <= total_pages:
            time.sleep(API_SLEEP)

    return all_items


def fetch_all_wp_content():
    """Fetch posts, pages, and categories from WordPress."""
    print("\n[1/5] Fetching WordPress content via REST API...")

    print("\n--- Posts ---")
    posts = fetch_wp_collection("posts?status=publish", "posts")

    time.sleep(API_SLEEP)
    print("\n--- Pages ---")
    pages = fetch_wp_collection("pages?status=publish", "pages")

    time.sleep(API_SLEEP)
    print("\n--- Categories ---")
    categories = fetch_wp_collection("categories", "categories")

    # Normalize into a unified list
    wp_items = []

    for p in posts:
        title = p.get("title", {}).get("rendered", "").strip()
        link = p.get("link", "").strip().rstrip("/") + "/"
        content_raw = p.get("content", {}).get("rendered", "")
        word_count = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', content_raw)))
        wp_items.append({
            "wp_id": p.get("id"),
            "title": title,
            "url": link,
            "type": "post",
            "cluster": classify_cluster(title, link),
            "published_date": p.get("date", ""),
            "word_count": word_count,
        })

    for p in pages:
        title = p.get("title", {}).get("rendered", "").strip()
        link = p.get("link", "").strip().rstrip("/") + "/"
        content_raw = p.get("content", {}).get("rendered", "")
        word_count = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', content_raw)))
        wp_items.append({
            "wp_id": p.get("id"),
            "title": title,
            "url": link,
            "type": "page",
            "cluster": classify_cluster(title, link),
            "published_date": p.get("date", ""),
            "word_count": word_count,
        })

    for c in categories:
        name = c.get("name", "").strip()
        link = c.get("link", "").strip().rstrip("/") + "/"
        count = c.get("count", 0)
        # Skip empty categories or "Uncategorized" with 0 posts
        if count == 0 and name.lower() == "uncategorized":
            continue
        wp_items.append({
            "wp_id": c.get("id"),
            "title": name,
            "url": link,
            "type": "category",
            "cluster": classify_cluster(name, link),
            "published_date": "",
            "word_count": 0,
        })

    print(f"\n  Total WP items: {len(wp_items)} (posts={len(posts)}, pages={len(pages)}, categories={len(categories)})")
    return wp_items


# ---------------------------------------------------------------------------
# 2. XML Sitemap parsing
# ---------------------------------------------------------------------------
def fetch_sitemaps():
    """Fetch and parse the sitemap index + child sitemaps."""
    print("\n[2/5] Fetching and parsing XML sitemaps...")

    sitemap_index_url = f"{BASE_URL}/sitemap_index.xml"
    sitemap_data = []  # list of {"sitemap_url": ..., "urls": [...], "last_modified": ...}
    all_sitemap_urls = set()

    # Fetch sitemap index
    body, _, status = curl_fetch(sitemap_index_url)
    print(f"  Sitemap index: {sitemap_index_url} (status={status})")

    child_sitemaps = []

    if status == 200 and body.strip():
        try:
            root = ET.fromstring(body.strip())
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            # Check if this is a sitemap index
            for sitemap in root.findall(".//sm:sitemap", ns):
                loc = sitemap.find("sm:loc", ns)
                lastmod = sitemap.find("sm:lastmod", ns)
                if loc is not None and loc.text:
                    child_sitemaps.append({
                        "url": loc.text.strip(),
                        "lastmod": lastmod.text.strip() if lastmod is not None and lastmod.text else "",
                    })

            # If no <sitemap> children, maybe it's a direct urlset
            if not child_sitemaps:
                urls_found = []
                for url_el in root.findall(".//sm:url/sm:loc", ns):
                    if url_el.text:
                        u = url_el.text.strip().rstrip("/") + "/"
                        urls_found.append(u)
                        all_sitemap_urls.add(u)
                if urls_found:
                    sitemap_data.append({
                        "sitemap_url": sitemap_index_url,
                        "url_count": len(urls_found),
                        "last_modified": "",
                    })
                    print(f"  Direct sitemap with {len(urls_found)} URLs")
        except ET.ParseError as e:
            print(f"  [WARN] Failed to parse sitemap index XML: {e}")
    else:
        # Try common sitemap paths
        alt_paths = ["/sitemap.xml", "/wp-sitemap.xml"]
        for path in alt_paths:
            alt_url = f"{BASE_URL}{path}"
            print(f"  Trying alternate sitemap: {alt_url}")
            body, _, status = curl_fetch(alt_url)
            time.sleep(API_SLEEP)
            if status == 200 and body.strip():
                try:
                    root = ET.fromstring(body.strip())
                    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                    for sitemap in root.findall(".//sm:sitemap", ns):
                        loc = sitemap.find("sm:loc", ns)
                        lastmod = sitemap.find("sm:lastmod", ns)
                        if loc is not None and loc.text:
                            child_sitemaps.append({
                                "url": loc.text.strip(),
                                "lastmod": lastmod.text.strip() if lastmod is not None and lastmod.text else "",
                            })
                    if not child_sitemaps:
                        urls_found = []
                        for url_el in root.findall(".//sm:url/sm:loc", ns):
                            if url_el.text:
                                u = url_el.text.strip().rstrip("/") + "/"
                                urls_found.append(u)
                                all_sitemap_urls.add(u)
                        sitemap_data.append({
                            "sitemap_url": alt_url,
                            "url_count": len(urls_found),
                            "last_modified": "",
                        })
                    break
                except ET.ParseError:
                    continue

    print(f"  Found {len(child_sitemaps)} child sitemap(s)")

    # Fetch each child sitemap
    for i, csm in enumerate(child_sitemaps):
        time.sleep(API_SLEEP)
        csm_url = csm["url"]
        print(f"  Fetching child sitemap {i+1}/{len(child_sitemaps)}: {csm_url}")
        body, _, status = curl_fetch(csm_url)

        urls_in_child = []
        if status == 200 and body.strip():
            try:
                root = ET.fromstring(body.strip())
                ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

                # Could be nested sitemap index
                nested = root.findall(".//sm:sitemap", ns)
                if nested:
                    for ns_el in nested:
                        loc = ns_el.find("sm:loc", ns)
                        if loc is not None and loc.text:
                            child_sitemaps.append({
                                "url": loc.text.strip(),
                                "lastmod": "",
                            })
                    continue

                for url_el in root.findall(".//sm:url/sm:loc", ns):
                    if url_el.text:
                        u = url_el.text.strip().rstrip("/") + "/"
                        urls_in_child.append(u)
                        all_sitemap_urls.add(u)
            except ET.ParseError as e:
                print(f"  [WARN] Parse error for {csm_url}: {e}")

        sitemap_data.append({
            "sitemap_url": csm_url,
            "url_count": len(urls_in_child),
            "last_modified": csm.get("lastmod", ""),
        })
        print(f"    -> {len(urls_in_child)} URLs")

    print(f"\n  Total unique sitemap URLs: {len(all_sitemap_urls)}")
    return sitemap_data, all_sitemap_urls


# ---------------------------------------------------------------------------
# 3. robots.txt parsing
# ---------------------------------------------------------------------------
def fetch_robots_txt():
    """Fetch and parse robots.txt, return list of disallow patterns."""
    print("\n[3/5] Fetching robots.txt...")

    robots_url = f"{BASE_URL}/robots.txt"
    body, _, status = curl_fetch(robots_url)
    print(f"  robots.txt status: {status}")

    disallow_rules = []
    sitemap_refs = []
    raw_lines = []

    if status == 200 and body.strip():
        current_agent = "*"
        for line in body.split("\n"):
            line = line.strip()
            raw_lines.append(line)
            if line.lower().startswith("user-agent:"):
                current_agent = line.split(":", 1)[1].strip()
            elif line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    disallow_rules.append({"agent": current_agent, "path": path})
            elif line.lower().startswith("sitemap:"):
                sm = line.split(":", 1)[1].strip()
                # Re-join in case of "Sitemap: https://..." split on first ":"
                if not sm.startswith("http"):
                    sm = "https:" + sm
                sitemap_refs.append(sm)

    print(f"  Disallow rules: {len(disallow_rules)}")
    for r in disallow_rules:
        print(f"    [{r['agent']}] Disallow: {r['path']}")
    print(f"  Sitemap references: {len(sitemap_refs)}")
    for s in sitemap_refs:
        print(f"    {s}")

    return disallow_rules, sitemap_refs, raw_lines


def is_blocked_by_robots(url, disallow_rules):
    """Check if a URL is blocked by any robots.txt disallow rule for * or Googlebot."""
    parsed = urlparse(url)
    path = parsed.path
    for rule in disallow_rules:
        agent = rule["agent"].lower()
        if agent in ("*", "googlebot"):
            pattern = rule["path"]
            if pattern.endswith("*"):
                if path.startswith(pattern[:-1]):
                    return True
            elif path.startswith(pattern):
                return True
    return False


# ---------------------------------------------------------------------------
# 4. HEAD request checks (status, canonical, x-robots-tag)
# ---------------------------------------------------------------------------
def check_page_status(url):
    """Do a HEAD-like check on a URL using curl. Returns dict with findings."""
    # Use GET with range to also check for canonical in HTML
    cmd = [
        "curl", "-s", "--compressed", "--max-time", str(CURL_TIMEOUT),
        "-L",
        "-D", "-",
        "-o", "/dev/null",
        "-w", "\n%{http_code}\n%{redirect_url}",
        url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=CURL_TIMEOUT + 10)
        raw = result.stdout.strip()
        lines = raw.split("\n")

        status_code = 0
        redirect_url = ""
        if len(lines) >= 2:
            try:
                redirect_url = lines[-1].strip()
                status_code = int(lines[-2].strip())
            except (ValueError, IndexError):
                pass
        elif len(lines) == 1:
            try:
                status_code = int(lines[-1].strip())
            except ValueError:
                pass

        # Parse headers for x-robots-tag
        header_text = "\n".join(lines[:-2]) if len(lines) > 2 else ""
        headers = _parse_headers(header_text)
        x_robots = headers.get("x-robots-tag", "")

        return {
            "status_code": status_code,
            "x_robots_tag": x_robots,
            "redirect_url": redirect_url,
        }

    except Exception as e:
        print(f"  [HEAD ERROR] {url}: {e}")
        return {"status_code": 0, "x_robots_tag": "", "redirect_url": ""}


def check_canonical(url):
    """Fetch a small portion of the page to find canonical tag."""
    cmd = [
        "curl", "-s", "--compressed", "--max-time", str(CURL_TIMEOUT),
        "-L",
        "-r", "0-16384",  # first 16KB should contain <head>
        url
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=CURL_TIMEOUT + 10)
        body = result.stdout
        # Look for <link rel="canonical" href="...">
        match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', body, re.IGNORECASE)
        if not match:
            match = re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']', body, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Check for structured data (JSON-LD)
        has_jsonld = bool(re.search(r'<script[^>]+type=["\']application/ld\+json["\']', body, re.IGNORECASE))

        return f"__STRUCTURED_DATA__" if has_jsonld else ""
    except Exception:
        return ""


def run_head_checks(wp_items):
    """Run HEAD + canonical checks on up to MAX_HEAD_CHECKS pages."""
    print(f"\n[4/5] Running page status checks (max {MAX_HEAD_CHECKS})...")

    results = {}
    checked = 0

    for item in wp_items:
        if checked >= MAX_HEAD_CHECKS:
            break

        url = item["url"]
        print(f"  [{checked + 1}/{min(len(wp_items), MAX_HEAD_CHECKS)}] {url}")

        head_info = check_page_status(url)
        time.sleep(0.5)

        canonical = check_canonical(url)
        has_structured = False
        if canonical == "__STRUCTURED_DATA__":
            has_structured = True
            canonical = ""

        results[url] = {
            "status_code": head_info["status_code"],
            "canonical": canonical,
            "x_robots_tag": head_info["x_robots_tag"],
            "has_structured_data": has_structured or bool(canonical),
        }

        checked += 1
        if checked < MAX_HEAD_CHECKS and checked < len(wp_items):
            time.sleep(HEAD_SLEEP)

    print(f"\n  Checked {checked} pages")
    return results


# ---------------------------------------------------------------------------
# 5. CSV generation
# ---------------------------------------------------------------------------
def normalize_url(url):
    """Ensure consistent URL format for comparison."""
    if not url:
        return url
    url = url.strip()
    if not url.endswith("/"):
        url += "/"
    return url


def generate_csvs(wp_items, sitemap_data, sitemap_urls, disallow_rules, head_results):
    """Generate all analysis CSV files."""
    print("\n[5/5] Generating analysis CSVs...")

    sitemap_urls_normalized = {normalize_url(u) for u in sitemap_urls}

    # Enrich wp_items with check results
    enriched = []
    for item in wp_items:
        url = normalize_url(item["url"])
        in_sitemap = "yes" if url in sitemap_urls_normalized else "no"
        blocked = is_blocked_by_robots(url, disallow_rules)

        hr = head_results.get(url, head_results.get(item["url"], {}))
        status_code = hr.get("status_code", "")
        canonical = hr.get("canonical", "")
        x_robots = hr.get("x_robots_tag", "")
        has_structured = hr.get("has_structured_data", False)

        enriched.append({
            **item,
            "url": url,
            "in_sitemap": in_sitemap,
            "status_code": status_code,
            "canonical": canonical,
            "x_robots_tag": x_robots,
            "robots_blocked": "yes" if blocked else "no",
            "has_structured_data": has_structured,
        })

    # --- a. indexation_inventory.csv ---
    inv_path = os.path.join(OUTPUT_DIR, "indexation_inventory.csv")
    with open(inv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "url", "title", "type", "cluster", "wp_id",
            "in_sitemap", "status_code", "canonical", "robots_blocked"
        ])
        writer.writeheader()
        for item in enriched:
            writer.writerow({
                "url": item["url"],
                "title": item["title"],
                "type": item["type"],
                "cluster": item["cluster"],
                "wp_id": item["wp_id"],
                "in_sitemap": item["in_sitemap"],
                "status_code": item["status_code"],
                "canonical": item["canonical"],
                "robots_blocked": item["robots_blocked"],
            })
    print(f"  -> {inv_path} ({len(enriched)} rows)")

    # --- b. indexation_gaps.csv ---
    gaps = []
    for item in enriched:
        if item["in_sitemap"] == "no":
            gaps.append({
                "url": item["url"],
                "title": item["title"],
                "issue": "not_in_sitemap",
                "severity": "critical",
            })
        if item["robots_blocked"] == "yes":
            gaps.append({
                "url": item["url"],
                "title": item["title"],
                "issue": "blocked_by_robots",
                "severity": "critical",
            })
        sc = item["status_code"]
        if sc:
            if sc == 404:
                gaps.append({
                    "url": item["url"],
                    "title": item["title"],
                    "issue": "404_not_found",
                    "severity": "critical",
                })
            elif 300 <= sc < 400:
                gaps.append({
                    "url": item["url"],
                    "title": item["title"],
                    "issue": "redirect",
                    "severity": "warning",
                })
            elif sc >= 500:
                gaps.append({
                    "url": item["url"],
                    "title": item["title"],
                    "issue": f"server_error_{sc}",
                    "severity": "critical",
                })
        if item["canonical"] == "" and item["status_code"] and item["status_code"] == 200:
            gaps.append({
                "url": item["url"],
                "title": item["title"],
                "issue": "no_canonical",
                "severity": "warning",
            })
        if item.get("x_robots_tag") and "noindex" in item["x_robots_tag"].lower():
            gaps.append({
                "url": item["url"],
                "title": item["title"],
                "issue": "x_robots_noindex",
                "severity": "critical",
            })

    # Also flag sitemap URLs not found in WP
    wp_urls = {normalize_url(item["url"]) for item in enriched}
    for sm_url in sitemap_urls_normalized:
        if sm_url not in wp_urls:
            gaps.append({
                "url": sm_url,
                "title": "(in sitemap but not in WP API)",
                "issue": "orphan_sitemap_url",
                "severity": "info",
            })

    gaps_path = os.path.join(OUTPUT_DIR, "indexation_gaps.csv")
    with open(gaps_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "title", "issue", "severity"])
        writer.writeheader()
        for g in gaps:
            writer.writerow(g)
    print(f"  -> {gaps_path} ({len(gaps)} rows)")

    # --- c. crawl_readiness.csv ---
    clusters = {}
    for item in enriched:
        c = item["cluster"]
        if c not in clusters:
            clusters[c] = {"total": 0, "in_sitemap": 0, "not_in_sitemap": 0, "blocked": 0, "accessible": 0}
        clusters[c]["total"] += 1
        if item["in_sitemap"] == "yes":
            clusters[c]["in_sitemap"] += 1
        else:
            clusters[c]["not_in_sitemap"] += 1
        if item["robots_blocked"] == "yes":
            clusters[c]["blocked"] += 1
        sc = item["status_code"]
        if sc and 200 <= sc < 300 and item["robots_blocked"] == "no":
            clusters[c]["accessible"] += 1

    crawl_path = os.path.join(OUTPUT_DIR, "crawl_readiness.csv")
    with open(crawl_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cluster", "total_pages", "in_sitemap", "not_in_sitemap",
            "blocked", "accessible", "crawl_readiness_pct"
        ])
        writer.writeheader()
        for cluster_name in sorted(clusters.keys()):
            d = clusters[cluster_name]
            pct = round((d["accessible"] / d["total"] * 100), 1) if d["total"] > 0 else 0
            writer.writerow({
                "cluster": cluster_name,
                "total_pages": d["total"],
                "in_sitemap": d["in_sitemap"],
                "not_in_sitemap": d["not_in_sitemap"],
                "blocked": d["blocked"],
                "accessible": d["accessible"],
                "crawl_readiness_pct": pct,
            })
    print(f"  -> {crawl_path} ({len(clusters)} clusters)")

    # --- d. sitemap_analysis.csv ---
    sma_path = os.path.join(OUTPUT_DIR, "sitemap_analysis.csv")
    with open(sma_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sitemap_url", "url_count", "last_modified"])
        writer.writeheader()
        for sm in sitemap_data:
            writer.writerow(sm)
    print(f"  -> {sma_path} ({len(sitemap_data)} sitemaps)")

    # --- e. page_discovery.csv ---
    disc_path = os.path.join(OUTPUT_DIR, "page_discovery.csv")
    with open(disc_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "url", "title", "cluster", "type", "published_date",
            "word_count_estimate", "has_structured_data"
        ])
        writer.writeheader()
        for item in enriched:
            writer.writerow({
                "url": item["url"],
                "title": item["title"],
                "cluster": item["cluster"],
                "type": item["type"],
                "published_date": item.get("published_date", ""),
                "word_count_estimate": item.get("word_count", 0),
                "has_structured_data": "yes" if item.get("has_structured_data") else "no",
            })
    print(f"  -> {disc_path} ({len(enriched)} rows)")

    return enriched, gaps, clusters


# ---------------------------------------------------------------------------
# 6. Summary
# ---------------------------------------------------------------------------
def print_summary(enriched, gaps, clusters, sitemap_data, sitemap_urls, disallow_rules):
    """Print a comprehensive summary."""
    print("\n" + "=" * 72)
    print("  PETHUB ONLINE - INDEXATION & CRAWL INTELLIGENCE SUMMARY")
    print("=" * 72)

    total = len(enriched)
    posts = sum(1 for i in enriched if i["type"] == "post")
    pages = sum(1 for i in enriched if i["type"] == "page")
    cats = sum(1 for i in enriched if i["type"] == "category")

    print(f"\n  WordPress Content Inventory:")
    print(f"    Total items:      {total}")
    print(f"    Posts:            {posts}")
    print(f"    Pages:            {pages}")
    print(f"    Categories:       {cats}")

    in_sm = sum(1 for i in enriched if i["in_sitemap"] == "yes")
    not_in_sm = sum(1 for i in enriched if i["in_sitemap"] == "no")
    print(f"\n  Sitemap Coverage:")
    print(f"    Sitemaps found:   {len(sitemap_data)}")
    print(f"    Sitemap URLs:     {len(sitemap_urls)}")
    print(f"    WP in sitemap:    {in_sm}/{total} ({round(in_sm/total*100,1) if total else 0}%)")
    print(f"    WP NOT in sitemap:{not_in_sm}")

    blocked = sum(1 for i in enriched if i["robots_blocked"] == "yes")
    print(f"\n  Robots.txt:")
    print(f"    Disallow rules:   {len(disallow_rules)}")
    print(f"    Blocked pages:    {blocked}")

    checked = sum(1 for i in enriched if i["status_code"])
    ok_200 = sum(1 for i in enriched if i["status_code"] == 200)
    redirects = sum(1 for i in enriched if i["status_code"] and 300 <= i["status_code"] < 400)
    errors_4xx = sum(1 for i in enriched if i["status_code"] and 400 <= i["status_code"] < 500)
    errors_5xx = sum(1 for i in enriched if i["status_code"] and i["status_code"] >= 500)
    print(f"\n  Status Codes (from {checked} checked):")
    print(f"    200 OK:           {ok_200}")
    print(f"    3xx Redirect:     {redirects}")
    print(f"    4xx Client Error: {errors_4xx}")
    print(f"    5xx Server Error: {errors_5xx}")

    has_canonical = sum(1 for i in enriched if i.get("canonical"))
    no_canonical = sum(1 for i in enriched if i["status_code"] == 200 and not i.get("canonical"))
    print(f"\n  Canonical Tags:")
    print(f"    Has canonical:    {has_canonical}")
    print(f"    Missing canonical:{no_canonical}")

    # Gaps summary
    gap_types = {}
    for g in gaps:
        gt = g["issue"]
        gap_types[gt] = gap_types.get(gt, 0) + 1

    print(f"\n  Indexation Issues ({len(gaps)} total):")
    for gt, count in sorted(gap_types.items(), key=lambda x: -x[1]):
        sev = next((g["severity"] for g in gaps if g["issue"] == gt), "?")
        print(f"    [{sev.upper():8s}] {gt}: {count}")

    # Cluster readiness
    print(f"\n  Crawl Readiness by Cluster:")
    print(f"    {'Cluster':<20s} {'Total':>6s} {'Ready':>6s} {'Pct':>7s}")
    print(f"    {'-'*20} {'-'*6} {'-'*6} {'-'*7}")
    for cluster_name in sorted(clusters.keys()):
        d = clusters[cluster_name]
        pct = round((d["accessible"] / d["total"] * 100), 1) if d["total"] > 0 else 0
        print(f"    {cluster_name:<20s} {d['total']:>6d} {d['accessible']:>6d} {pct:>6.1f}%")

    print(f"\n  Output Files:")
    for fname in ["indexation_inventory.csv", "indexation_gaps.csv",
                   "crawl_readiness.csv", "sitemap_analysis.csv", "page_discovery.csv"]:
        fpath = os.path.join(OUTPUT_DIR, fname)
        size = os.path.getsize(fpath) if os.path.exists(fpath) else 0
        print(f"    {fname:<30s} {size:>8,d} bytes")

    print("\n" + "=" * 72)
    print("  Engine complete. All CSVs written to:")
    print(f"  {OUTPUT_DIR}/")
    print("=" * 72 + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    start_time = time.time()
    print("=" * 72)
    print("  PetHub Online - Indexation & Crawl Intelligence Engine")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Target:  {BASE_URL}")
    print(f"  Output:  {OUTPUT_DIR}/")
    print("=" * 72)

    try:
        # 1. WordPress content
        wp_items = fetch_all_wp_content()

        # 2. Sitemaps
        sitemap_data, sitemap_urls = fetch_sitemaps()

        # 3. robots.txt
        disallow_rules, sitemap_refs, _ = fetch_robots_txt()

        # 4. HEAD checks
        head_results = run_head_checks(wp_items)

        # 5. Generate CSVs
        enriched, gaps, clusters = generate_csvs(
            wp_items, sitemap_data, sitemap_urls, disallow_rules, head_results
        )

        # 6. Summary
        print_summary(enriched, gaps, clusters, sitemap_data, sitemap_urls, disallow_rules)

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Exiting gracefully...")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    elapsed = time.time() - start_time
    print(f"Total runtime: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
