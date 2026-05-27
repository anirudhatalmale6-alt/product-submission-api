#!/usr/bin/env python3
"""
Internal Linking Quality Audit for pethubonline.com
Fetches all published posts/pages via WP REST API, parses internal links,
and generates an actionable audit report.
"""

import requests
import re
import json
import os
from urllib.parse import urlparse, unquote
from collections import defaultdict
from html.parser import HTMLParser
from datetime import datetime

# === CONFIG ===
BASE_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
SITE_DOMAIN = "pethubonline.com"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10d"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "internal_links_audit.txt")

# Generic anchor texts to flag
GENERIC_ANCHORS = {
    "click here", "read more", "here", "this page", "this post",
    "this article", "learn more", "more info", "find out more",
    "check it out", "see more", "link", "this link", "go here",
    "read this", "click", "more", "continue reading"
}

# Cluster definitions: hub slug -> list of expected spoke slugs (partial matches)
CLUSTERS = {
    "Dog Beds": {
        "hub_keywords": ["best-dog-beds", "dog-beds-guide", "dog-beds"],
        "spoke_keywords": ["orthopedic", "orthopaedic", "cooling-bed", "puppy-bed",
                           "memory-foam", "waterproof-bed", "elevated-bed",
                           "heated-dog-bed", "calming-bed", "large-dog-bed",
                           "small-dog-bed", "dog-bed-size", "dog-sleep"]
    },
    "Dog Toys": {
        "hub_keywords": ["best-dog-toys", "dog-toys-guide", "dog-toys"],
        "spoke_keywords": ["indestructible", "interactive-toy", "puzzle-toy",
                           "chew-toy", "tug-toy", "fetch-toy", "puppy-toy",
                           "tough-toy", "squeaky", "rope-toy"]
    },
    "Dog Care": {
        "hub_keywords": ["dog-care", "dog-health-guide", "dog-health"],
        "spoke_keywords": ["dental-care", "flea-treatment", "joint-care",
                           "dog-grooming", "nail-clipping", "dog-shampoo",
                           "dog-brush", "ear-cleaning", "tick-prevention"]
    },
    "Pet Care": {
        "hub_keywords": ["pet-care", "pet-health", "pet-guide"],
        "spoke_keywords": ["pet-insurance", "vet-visit", "pet-first-aid",
                           "pet-nutrition", "pet-wellness"]
    },
    "Cat Toys": {
        "hub_keywords": ["best-cat-toys", "cat-toys-guide", "cat-toys"],
        "spoke_keywords": ["catnip", "interactive-cat", "wand-toy",
                           "laser-toy", "cat-puzzle", "indoor-cat-toy",
                           "cat-feather", "cat-ball"]
    },
    "Dog Harnesses": {
        "hub_keywords": ["dog-harness", "best-dog-harness", "harness-guide"],
        "spoke_keywords": ["no-pull", "front-clip", "step-in-harness",
                           "puppy-harness", "harness-vs-collar", "vest-harness",
                           "dog-collar", "dog-lead"]
    },
    "Training": {
        "hub_keywords": ["dog-training", "training-guide", "puppy-training"],
        "spoke_keywords": ["recall-training", "crate-training", "toilet-training",
                           "lead-training", "basic-commands", "clicker-training",
                           "treat-training", "training-treats", "training-equipment"]
    },
    "Puppy Care": {
        "hub_keywords": ["puppy-care", "puppy-guide", "new-puppy"],
        "spoke_keywords": ["puppy-food", "puppy-crate", "puppy-socialisation",
                           "puppy-vaccination", "puppy-teething", "puppy-sleep",
                           "puppy-training"]
    }
}

# Trust pages: about, contact, privacy, affiliate disclosure, etc.
TRUST_PAGE_KEYWORDS = [
    "about", "contact", "privacy", "terms", "disclaimer",
    "affiliate-disclosure", "editorial", "how-we-review",
    "our-process", "why-trust"
]


class LinkExtractor(HTMLParser):
    """Extract <a> tags with href and anchor text from HTML content."""

    def __init__(self):
        super().__init__()
        self.links = []
        self._current_href = None
        self._current_text = []
        self._in_a = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            self._current_href = href
            self._current_text = []
            self._in_a = True

    def handle_data(self, data):
        if self._in_a:
            self._current_text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._in_a:
            anchor = " ".join("".join(self._current_text).split()).strip()
            if self._current_href:
                self.links.append((self._current_href, anchor))
            self._in_a = False
            self._current_href = None
            self._current_text = []


def fetch_all_items(endpoint, params_extra=None):
    """Fetch all items from a paginated WP REST API endpoint."""
    items = []
    page = 1
    per_page = 100
    while True:
        params = {
            "per_page": per_page,
            "page": page,
            "status": "publish",
            "context": "edit",
        }
        if params_extra:
            params.update(params_extra)

        s = requests.Session()
        s.auth = AUTH
        s.headers["Accept-Encoding"] = "gzip, deflate"

        try:
            resp = s.get(f"{BASE_URL}/{endpoint}", params=params, timeout=60)
            if resp.status_code == 400:
                # No more pages
                break
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            items.extend(batch)
            total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
            print(f"  Fetched {endpoint} page {page}/{total_pages} ({len(batch)} items)")
            if page >= total_pages:
                break
            page += 1
        except Exception as e:
            print(f"  Error fetching {endpoint} page {page}: {e}")
            break
    return items


def normalize_url(url):
    """Normalize a URL to a canonical path for comparison."""
    url = url.strip()
    # Handle relative URLs
    if url.startswith("/"):
        path = url
    elif SITE_DOMAIN in url:
        parsed = urlparse(url)
        path = parsed.path
    else:
        return None  # External link

    # Normalize: lowercase, strip trailing slash, remove fragments/query
    path = unquote(path).lower().rstrip("/")
    if not path:
        path = "/"
    return path


def extract_internal_links(html_content):
    """Extract all internal links from HTML content."""
    if not html_content:
        return []

    extractor = LinkExtractor()
    try:
        extractor.feed(html_content)
    except Exception:
        pass

    internal_links = []
    for href, anchor in extractor.links:
        href = href.strip()
        # Skip empty, anchor-only, mailto, tel, javascript links
        if not href or href.startswith("#") or href.startswith("mailto:") or \
           href.startswith("tel:") or href.startswith("javascript:"):
            continue

        # Check if internal
        is_internal = False
        if href.startswith("/") and not href.startswith("//"):
            is_internal = True
        elif SITE_DOMAIN in href:
            is_internal = True

        if is_internal:
            normalized = normalize_url(href)
            if normalized and normalized != "/":
                internal_links.append({
                    "href": href,
                    "normalized_path": normalized,
                    "anchor_text": anchor
                })

    return internal_links


def get_content_html(item):
    """Get the HTML content from a WP item, handling both rendered and raw."""
    content = item.get("content", {})
    if isinstance(content, dict):
        return content.get("rendered", "") or content.get("raw", "")
    return str(content) if content else ""


def build_url_index(all_items):
    """Build a mapping of normalized URLs to item info."""
    url_index = {}
    for item in all_items:
        link = item.get("link", "")
        normalized = normalize_url(link)
        if normalized:
            url_index[normalized] = {
                "id": item["id"],
                "title": (item.get("title", {}).get("rendered", "") or
                          item.get("title", {}).get("raw", "") or
                          str(item.get("title", ""))),
                "type": item.get("type", "unknown"),
                "link": link,
                "slug": item.get("slug", ""),
            }
        # Also index by slug
        slug = item.get("slug", "")
        if slug:
            slug_path = f"/{slug}"
            if slug_path not in url_index:
                url_index[slug_path] = url_index.get(normalized, {
                    "id": item["id"],
                    "title": (item.get("title", {}).get("rendered", "") or
                              str(item.get("title", ""))),
                    "type": item.get("type", "unknown"),
                    "link": link,
                    "slug": slug,
                })
    return url_index


def classify_content(item):
    """Classify content into clusters and trust pages."""
    slug = item.get("slug", "").lower()
    title = ""
    t = item.get("title", {})
    if isinstance(t, dict):
        title = (t.get("rendered", "") or t.get("raw", "")).lower()
    else:
        title = str(t).lower()

    categories = []

    # Check trust pages
    for kw in TRUST_PAGE_KEYWORDS:
        if kw in slug:
            categories.append(("trust", kw))

    # Check clusters
    for cluster_name, cluster_def in CLUSTERS.items():
        for kw in cluster_def["hub_keywords"]:
            if kw in slug or kw.replace("-", " ") in title:
                categories.append(("hub", cluster_name))
                break
        for kw in cluster_def["spoke_keywords"]:
            if kw in slug or kw.replace("-", " ") in title:
                categories.append(("spoke", cluster_name))
                break

    return categories


def main():
    print("=" * 60)
    print("INTERNAL LINKING AUDIT - pethubonline.com")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. Fetch all published posts and pages
    print("\n[1/6] Fetching all published content...")
    posts = fetch_all_items("posts")
    pages = fetch_all_items("pages")
    all_items = posts + pages
    print(f"  Total: {len(posts)} posts + {len(pages)} pages = {len(all_items)} items")

    if not all_items:
        print("ERROR: No content fetched. Check API credentials.")
        return

    # 2. Build URL index
    print("\n[2/6] Building URL index...")
    url_index = build_url_index(all_items)
    print(f"  Indexed {len(url_index)} URLs")

    # 3. Extract all internal links
    print("\n[3/6] Extracting internal links from all content...")
    # outbound_links[source_url] = list of link dicts
    outbound_links = {}
    # inbound_links[target_url] = list of {source_url, anchor_text}
    inbound_links = defaultdict(list)
    # All found internal link targets (for broken link detection)
    all_link_targets = set()
    # Generic anchor instances
    generic_anchors_found = []
    # Broken links
    broken_links = []

    for item in all_items:
        link = item.get("link", "")
        source_normalized = normalize_url(link)
        if not source_normalized:
            continue

        html = get_content_html(item)
        links = extract_internal_links(html)
        outbound_links[source_normalized] = links

        title = ""
        t = item.get("title", {})
        if isinstance(t, dict):
            title = t.get("rendered", "") or t.get("raw", "")
        else:
            title = str(t)

        for lnk in links:
            target = lnk["normalized_path"]
            anchor = lnk["anchor_text"]
            all_link_targets.add(target)

            inbound_links[target].append({
                "source": source_normalized,
                "source_title": title,
                "anchor_text": anchor
            })

            # Check generic anchor
            if anchor.lower().strip() in GENERIC_ANCHORS:
                generic_anchors_found.append({
                    "source": source_normalized,
                    "source_title": title,
                    "target": target,
                    "anchor_text": anchor
                })

    print(f"  Extracted links from {len(outbound_links)} items")
    total_internal = sum(len(v) for v in outbound_links.values())
    print(f"  Total internal links found: {total_internal}")

    # 4. Analysis
    print("\n[4/6] Analyzing link quality...")

    # --- ORPHAN PAGES ---
    orphan_pages = []
    for item in all_items:
        link = item.get("link", "")
        normalized = normalize_url(link)
        if not normalized:
            continue
        # Check if any other page links to this one
        inbound_count = len(inbound_links.get(normalized, []))
        # Also check slug-based path
        slug = item.get("slug", "")
        slug_path = f"/{slug}" if slug else None
        if slug_path and slug_path != normalized:
            inbound_count += len(inbound_links.get(slug_path, []))

        if inbound_count == 0:
            title = ""
            t = item.get("title", {})
            if isinstance(t, dict):
                title = t.get("rendered", "") or t.get("raw", "")
            else:
                title = str(t)
            orphan_pages.append({
                "title": title,
                "url": link,
                "slug": slug,
                "type": item.get("type", "unknown"),
            })

    # --- BROKEN LINKS ---
    # Check each internal link target against the URL index
    for source_url, links in outbound_links.items():
        for lnk in links:
            target = lnk["normalized_path"]
            # Try to find target in URL index
            found = False
            if target in url_index:
                found = True
            else:
                # Try partial slug match
                target_slug = target.rstrip("/").split("/")[-1]
                for indexed_url in url_index:
                    if indexed_url.endswith(f"/{target_slug}"):
                        found = True
                        break
            if not found:
                # Find source title
                source_info = url_index.get(source_url, {})
                broken_links.append({
                    "source": source_url,
                    "source_title": source_info.get("title", "Unknown"),
                    "broken_target": lnk["href"],
                    "normalized": target,
                    "anchor_text": lnk["anchor_text"]
                })

    # --- LINK DISTRIBUTION ---
    outbound_counts = []
    for item in all_items:
        link = item.get("link", "")
        normalized = normalize_url(link)
        if not normalized:
            continue
        title = ""
        t = item.get("title", {})
        if isinstance(t, dict):
            title = t.get("rendered", "") or t.get("raw", "")
        else:
            title = str(t)
        count = len(outbound_links.get(normalized, []))
        outbound_counts.append({
            "title": title,
            "url": link,
            "count": count,
            "type": item.get("type", "unknown"),
        })

    inbound_counts = []
    for item in all_items:
        link = item.get("link", "")
        normalized = normalize_url(link)
        if not normalized:
            continue
        title = ""
        t = item.get("title", {})
        if isinstance(t, dict):
            title = t.get("rendered", "") or t.get("raw", "")
        else:
            title = str(t)
        slug = item.get("slug", "")
        slug_path = f"/{slug}" if slug else None
        count = len(inbound_links.get(normalized, []))
        if slug_path and slug_path != normalized:
            count += len(inbound_links.get(slug_path, []))
        inbound_counts.append({
            "title": title,
            "url": link,
            "count": count,
            "type": item.get("type", "unknown"),
        })

    # Sort
    outbound_counts.sort(key=lambda x: x["count"], reverse=True)
    inbound_counts.sort(key=lambda x: x["count"], reverse=True)
    zero_outbound = [x for x in outbound_counts if x["count"] == 0]

    # --- CLUSTER CONNECTIVITY ---
    print("\n[5/6] Analyzing cluster connectivity...")
    cluster_analysis = {}

    for cluster_name, cluster_def in CLUSTERS.items():
        # Find hub pages
        hubs = []
        spokes = []
        for item in all_items:
            slug = item.get("slug", "").lower()
            title_raw = item.get("title", {})
            if isinstance(title_raw, dict):
                title = (title_raw.get("rendered", "") or title_raw.get("raw", "")).lower()
            else:
                title = str(title_raw).lower()

            is_hub = False
            for kw in cluster_def["hub_keywords"]:
                if kw in slug:
                    is_hub = True
                    break
            if is_hub:
                hubs.append(item)
                continue

            is_spoke = False
            matched_kw = ""
            for kw in cluster_def["spoke_keywords"]:
                if kw in slug:
                    is_spoke = True
                    matched_kw = kw
                    break
            if is_spoke:
                spokes.append(item)

        # Check hub->spoke and spoke->hub links
        hub_to_spoke = {}
        spoke_to_hub = {}

        for hub in hubs:
            hub_norm = normalize_url(hub.get("link", ""))
            if not hub_norm:
                continue
            hub_outbound = outbound_links.get(hub_norm, [])
            hub_targets = {lnk["normalized_path"] for lnk in hub_outbound}

            for spoke in spokes:
                spoke_norm = normalize_url(spoke.get("link", ""))
                spoke_slug = spoke.get("slug", "")
                if not spoke_norm:
                    continue

                # Check if hub links to spoke
                linked = spoke_norm in hub_targets
                if not linked and spoke_slug:
                    linked = any(spoke_slug in t for t in hub_targets)

                spoke_title = ""
                st = spoke.get("title", {})
                if isinstance(st, dict):
                    spoke_title = st.get("rendered", "") or st.get("raw", "")
                else:
                    spoke_title = str(st)

                hub_to_spoke[spoke_title] = linked

        for spoke in spokes:
            spoke_norm = normalize_url(spoke.get("link", ""))
            if not spoke_norm:
                continue
            spoke_outbound = outbound_links.get(spoke_norm, [])
            spoke_targets = {lnk["normalized_path"] for lnk in spoke_outbound}

            spoke_title = ""
            st = spoke.get("title", {})
            if isinstance(st, dict):
                spoke_title = st.get("rendered", "") or st.get("raw", "")
            else:
                spoke_title = str(st)

            links_to_hub = False
            for hub in hubs:
                hub_norm = normalize_url(hub.get("link", ""))
                hub_slug = hub.get("slug", "")
                if hub_norm in spoke_targets:
                    links_to_hub = True
                    break
                if hub_slug and any(hub_slug in t for t in spoke_targets):
                    links_to_hub = True
                    break

            spoke_to_hub[spoke_title] = links_to_hub

        cluster_analysis[cluster_name] = {
            "hub_count": len(hubs),
            "spoke_count": len(spokes),
            "hub_to_spoke": hub_to_spoke,
            "spoke_to_hub": spoke_to_hub,
            "hub_titles": [
                (h.get("title", {}).get("rendered", "") if isinstance(h.get("title"), dict)
                 else str(h.get("title", "")))
                for h in hubs
            ],
        }

    # --- TRUST PAGE CONNECTIVITY ---
    print("\n[6/6] Analyzing trust page connectivity...")
    trust_pages = []
    commercial_pages = []

    for item in all_items:
        slug = item.get("slug", "").lower()
        title_raw = item.get("title", {})
        if isinstance(title_raw, dict):
            title = (title_raw.get("rendered", "") or title_raw.get("raw", "")).lower()
        else:
            title = str(title_raw).lower()

        is_trust = False
        for kw in TRUST_PAGE_KEYWORDS:
            if kw in slug or kw.replace("-", " ") in title:
                is_trust = True
                break

        if is_trust:
            trust_pages.append(item)
        elif item.get("type") == "post":
            commercial_pages.append(item)

    # Check trust page cross-links
    trust_crosslinks = {}
    for tp in trust_pages:
        tp_norm = normalize_url(tp.get("link", ""))
        tp_title = ""
        tt = tp.get("title", {})
        if isinstance(tt, dict):
            tp_title = tt.get("rendered", "") or tt.get("raw", "")
        else:
            tp_title = str(tt)

        tp_outbound = outbound_links.get(tp_norm, [])
        tp_targets = {lnk["normalized_path"] for lnk in tp_outbound}

        links_to = []
        missing_links_to = []
        for other_tp in trust_pages:
            if other_tp["id"] == tp["id"]:
                continue
            other_norm = normalize_url(other_tp.get("link", ""))
            other_slug = other_tp.get("slug", "")
            other_title = ""
            ot = other_tp.get("title", {})
            if isinstance(ot, dict):
                other_title = ot.get("rendered", "") or ot.get("raw", "")
            else:
                other_title = str(ot)

            found = other_norm in tp_targets
            if not found and other_slug:
                found = any(other_slug in t for t in tp_targets)

            if found:
                links_to.append(other_title)
            else:
                missing_links_to.append(other_title)

        trust_crosslinks[tp_title] = {
            "links_to": links_to,
            "missing": missing_links_to
        }

    # Check commercial -> trust links
    commercial_to_trust = defaultdict(int)
    commercial_no_trust = []
    for cp in commercial_pages:
        cp_norm = normalize_url(cp.get("link", ""))
        cp_outbound = outbound_links.get(cp_norm, [])
        cp_targets = {lnk["normalized_path"] for lnk in cp_outbound}

        cp_title = ""
        ct = cp.get("title", {})
        if isinstance(ct, dict):
            cp_title = ct.get("rendered", "") or ct.get("raw", "")
        else:
            cp_title = str(ct)

        trust_link_count = 0
        for tp in trust_pages:
            tp_norm = normalize_url(tp.get("link", ""))
            tp_slug = tp.get("slug", "")
            if tp_norm in cp_targets or (tp_slug and any(tp_slug in t for t in cp_targets)):
                trust_link_count += 1

        if trust_link_count == 0:
            commercial_no_trust.append(cp_title)
        commercial_to_trust[cp_title] = trust_link_count

    # === BUILD REPORT ===
    print("\nGenerating report...")
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("INTERNAL LINKING QUALITY AUDIT - pethubonline.com")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Content Audited: {len(posts)} posts + {len(pages)} pages = {len(all_items)} total")
    report_lines.append(f"Total Internal Links Found: {total_internal}")
    report_lines.append("=" * 70)

    # --- Section 1: ORPHAN PAGES ---
    report_lines.append("\n" + "=" * 70)
    report_lines.append("1. ORPHAN PAGES (Zero Inbound Internal Links)")
    report_lines.append("=" * 70)
    report_lines.append(f"Found: {len(orphan_pages)} orphan pages\n")
    if orphan_pages:
        # Separate by type
        orphan_posts = [o for o in orphan_pages if o["type"] == "post"]
        orphan_pgs = [o for o in orphan_pages if o["type"] == "page"]

        if orphan_posts:
            report_lines.append(f"  ORPHAN POSTS ({len(orphan_posts)}):")
            for o in orphan_posts:
                report_lines.append(f"    - {o['title']}")
                report_lines.append(f"      URL: {o['url']}")

        if orphan_pgs:
            report_lines.append(f"\n  ORPHAN PAGES ({len(orphan_pgs)}):")
            for o in orphan_pgs:
                report_lines.append(f"    - {o['title']}")
                report_lines.append(f"      URL: {o['url']}")

        report_lines.append(f"\n  ACTION: Add contextual internal links from related content")
        report_lines.append(f"  to these {len(orphan_pages)} orphan items to improve crawlability.")
    else:
        report_lines.append("  EXCELLENT - No orphan pages found!")

    # --- Section 2: BROKEN LINKS ---
    report_lines.append("\n" + "=" * 70)
    report_lines.append("2. BROKEN INTERNAL LINKS")
    report_lines.append("=" * 70)
    report_lines.append(f"Found: {len(broken_links)} potentially broken internal links\n")
    if broken_links:
        # Deduplicate by target
        seen_targets = {}
        for bl in broken_links:
            key = bl["normalized"]
            if key not in seen_targets:
                seen_targets[key] = []
            seen_targets[key].append(bl)

        for target, instances in sorted(seen_targets.items()):
            report_lines.append(f"  BROKEN TARGET: {target}")
            report_lines.append(f"  Referenced from {len(instances)} page(s):")
            for inst in instances[:5]:  # Show max 5 sources
                report_lines.append(f"    - {inst['source_title']}")
                report_lines.append(f"      Anchor: \"{inst['anchor_text']}\"")
                report_lines.append(f"      Link: {inst['broken_target']}")
            if len(instances) > 5:
                report_lines.append(f"    ... and {len(instances) - 5} more")
            report_lines.append("")

        report_lines.append(f"  ACTION: Fix or redirect these {len(seen_targets)} broken targets.")
    else:
        report_lines.append("  EXCELLENT - No broken internal links detected!")

    # --- Section 3: ANCHOR TEXT QUALITY ---
    report_lines.append("\n" + "=" * 70)
    report_lines.append("3. ANCHOR TEXT QUALITY (Generic Anchors)")
    report_lines.append("=" * 70)
    report_lines.append(f"Found: {len(generic_anchors_found)} links with generic anchor text\n")
    if generic_anchors_found:
        # Group by anchor text
        by_anchor = defaultdict(list)
        for ga in generic_anchors_found:
            by_anchor[ga["anchor_text"].lower().strip()].append(ga)

        for anchor, instances in sorted(by_anchor.items(), key=lambda x: -len(x[1])):
            report_lines.append(f"  \"{anchor}\" - {len(instances)} instance(s):")
            for inst in instances[:3]:
                report_lines.append(f"    - On: {inst['source_title']}")
                report_lines.append(f"      Links to: {inst['target']}")
            if len(instances) > 3:
                report_lines.append(f"    ... and {len(instances) - 3} more")
            report_lines.append("")

        report_lines.append(f"  ACTION: Replace generic anchors with descriptive, keyword-rich text.")
        report_lines.append(f"  Example: \"click here\" -> \"best orthopedic dog beds for large breeds\"")
    else:
        report_lines.append("  EXCELLENT - No generic anchor text found!")

    # --- Section 4: LINK DISTRIBUTION ---
    report_lines.append("\n" + "=" * 70)
    report_lines.append("4. LINK DISTRIBUTION")
    report_lines.append("=" * 70)

    report_lines.append(f"\n  TOP 15 PAGES BY OUTBOUND INTERNAL LINKS:")
    for item in outbound_counts[:15]:
        report_lines.append(f"    {item['count']:3d} links - {item['title']} [{item['type']}]")

    report_lines.append(f"\n  TOP 15 PAGES BY INBOUND INTERNAL LINKS:")
    for item in inbound_counts[:15]:
        report_lines.append(f"    {item['count']:3d} links - {item['title']} [{item['type']}]")

    report_lines.append(f"\n  PAGES WITH ZERO OUTBOUND INTERNAL LINKS ({len(zero_outbound)}):")
    if zero_outbound:
        for item in zero_outbound:
            report_lines.append(f"    - {item['title']} [{item['type']}]")
            report_lines.append(f"      URL: {item['url']}")
        report_lines.append(f"\n  ACTION: Add at least 2-3 contextual internal links to each page with zero outbound links.")
    else:
        report_lines.append("    None - all pages have outbound internal links!")

    # Average stats
    avg_outbound = sum(x["count"] for x in outbound_counts) / max(len(outbound_counts), 1)
    avg_inbound = sum(x["count"] for x in inbound_counts) / max(len(inbound_counts), 1)
    report_lines.append(f"\n  AVERAGES:")
    report_lines.append(f"    Average outbound internal links per page: {avg_outbound:.1f}")
    report_lines.append(f"    Average inbound internal links per page:  {avg_inbound:.1f}")

    # --- Section 5: CLUSTER CONNECTIVITY ---
    report_lines.append("\n" + "=" * 70)
    report_lines.append("5. CLUSTER CONNECTIVITY (Hub-Spoke Analysis)")
    report_lines.append("=" * 70)

    for cluster_name, analysis in cluster_analysis.items():
        report_lines.append(f"\n  --- {cluster_name.upper()} CLUSTER ---")
        report_lines.append(f"  Hubs found: {analysis['hub_count']} | Spokes found: {analysis['spoke_count']}")

        if analysis["hub_titles"]:
            report_lines.append(f"  Hub page(s): {', '.join(analysis['hub_titles'])}")

        if not analysis["hub_count"]:
            report_lines.append(f"  WARNING: No hub page found for {cluster_name}!")
            continue

        # Hub -> Spoke links
        missing_from_hub = [s for s, linked in analysis["hub_to_spoke"].items() if not linked]
        linked_from_hub = [s for s, linked in analysis["hub_to_spoke"].items() if linked]

        if analysis["hub_to_spoke"]:
            report_lines.append(f"  Hub links to {len(linked_from_hub)}/{len(analysis['hub_to_spoke'])} spokes")
            if missing_from_hub:
                report_lines.append(f"  MISSING hub->spoke links:")
                for s in missing_from_hub:
                    report_lines.append(f"    - Hub does NOT link to: {s}")

        # Spoke -> Hub links
        missing_to_hub = [s for s, linked in analysis["spoke_to_hub"].items() if not linked]
        linked_to_hub = [s for s, linked in analysis["spoke_to_hub"].items() if linked]

        if analysis["spoke_to_hub"]:
            report_lines.append(f"  {len(linked_to_hub)}/{len(analysis['spoke_to_hub'])} spokes link back to hub")
            if missing_to_hub:
                report_lines.append(f"  MISSING spoke->hub links:")
                for s in missing_to_hub:
                    report_lines.append(f"    - {s} does NOT link back to hub")

        if not missing_from_hub and not missing_to_hub and analysis["spoke_count"] > 0:
            report_lines.append(f"  EXCELLENT - Full hub-spoke connectivity!")

    # --- Section 6: TRUST PAGE CONNECTIVITY ---
    report_lines.append("\n" + "=" * 70)
    report_lines.append("6. TRUST PAGE CONNECTIVITY")
    report_lines.append("=" * 70)
    report_lines.append(f"\n  Trust pages found: {len(trust_pages)}")

    if trust_pages:
        for tp_title, info in trust_crosslinks.items():
            report_lines.append(f"\n  {tp_title}:")
            if info["links_to"]:
                report_lines.append(f"    Links to {len(info['links_to'])} other trust pages")
            if info["missing"]:
                report_lines.append(f"    MISSING links to: {', '.join(info['missing'][:5])}")
                if len(info["missing"]) > 5:
                    report_lines.append(f"      ... and {len(info['missing']) - 5} more")

        # Commercial pages linking to trust
        report_lines.append(f"\n  COMMERCIAL PAGES WITHOUT TRUST LINKS ({len(commercial_no_trust)}/{len(commercial_pages)}):")
        if len(commercial_no_trust) <= 20:
            for title in commercial_no_trust:
                report_lines.append(f"    - {title}")
        else:
            for title in commercial_no_trust[:15]:
                report_lines.append(f"    - {title}")
            report_lines.append(f"    ... and {len(commercial_no_trust) - 15} more")

        report_lines.append(f"\n  ACTION: Ensure all commercial posts link to at least the affiliate")
        report_lines.append(f"  disclosure and/or editorial process trust pages for E-E-A-T compliance.")
    else:
        report_lines.append("  WARNING: No trust pages found!")

    # === SUMMARY ===
    report_lines.append("\n" + "=" * 70)
    report_lines.append("EXECUTIVE SUMMARY & PRIORITY ACTIONS")
    report_lines.append("=" * 70)
    report_lines.append(f"""
  HEALTH SCORES:
    Orphan pages:         {len(orphan_pages)} (target: 0)
    Broken internal links:{len(broken_links)} (target: 0)
    Generic anchors:      {len(generic_anchors_found)} (target: 0)
    Zero-outbound pages:  {len(zero_outbound)} (target: 0)
    Avg outbound links:   {avg_outbound:.1f} (target: 3-5)
    Avg inbound links:    {avg_inbound:.1f} (target: 2-3)

  PRIORITY ACTIONS (ordered by SEO impact):
    1. Fix {len(broken_links)} broken internal links (crawl health)
    2. Link to {len(orphan_pages)} orphan pages (indexation)
    3. Add outbound links to {len(zero_outbound)} dead-end pages (link equity flow)
    4. Replace {len(generic_anchors_found)} generic anchors with keyword-rich text (relevance)
    5. Complete hub-spoke linking in all clusters (topical authority)
    6. Add trust page links to {len(commercial_no_trust)} commercial pages (E-E-A-T)
""")

    # Write report
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_text = "\n".join(report_lines)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\nReport saved to: {OUTPUT_FILE}")
    print(f"Report length: {len(report_lines)} lines")
    print("\nDone!")


if __name__ == "__main__":
    main()
