#!/usr/bin/env python3
"""
PetHub Online - Phase 11Q Internal Link Optimization Engine
============================================================
Pushes authority into 12 new drafts and existing money pages through
strategic internal linking with hub-and-spoke architecture.

- Fetches all published posts + pages from WP REST API
- Builds complete internal link map
- Designs hub-and-spoke architecture for 4 priority clusters
- Adds 3-5 contextual internal links per post
- Generates anchor diversity reports + 5 CSVs
- NEVER removes existing links, NEVER modifies drafts
"""

import csv
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "https://pethubonline.com"
WP_API_BASE = f"{BASE_URL}/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase11_data"

API_SLEEP_GET = 2
API_SLEEP_POST = 3
MAX_RETRIES = 3
CURL_TIMEOUT = 45

# Priority clusters with category IDs
PRIORITY_CLUSTERS = {
    "Indoor Cats": {
        "category_id": 1413,
        "draft_ids": [12756, 12757, 12758],
    },
    "Cat Toys": {
        "category_id": 1459,
        "draft_ids": [12765, 12766, 12767],
    },
    "Pet Care": {
        "category_id": 1397,
        "draft_ids": [12759, 12760, 12761],
    },
    "Dog Supplies": {
        "category_id": 1376,
        "draft_ids": [12762, 12763, 12764],
    },
}

# Draft post info (from opportunity_execution_log.csv)
DRAFT_POSTS = {
    12756: {"title": "Catio Kits UK: Complete Guide to Outdoor Cat Enclosures", "cluster": "Indoor Cats"},
    12757: {"title": "DIY Catio Plans: How to Build a Cat Enclosure in the UK", "cluster": "Indoor Cats"},
    12758: {"title": "Indoor Cat Exercise: Daily Routines to Keep UK Cats Active", "cluster": "Indoor Cats"},
    12759: {"title": "Multi-Pet Household Management: UK Guide for Harmony", "cluster": "Pet Care"},
    12760: {"title": "Seasonal Pet Care Calendar UK: Monthly Guide for Pet Owners", "cluster": "Pet Care"},
    12761: {"title": "First-Time Pet Owner UK: Complete Beginner Guide", "cluster": "Pet Care"},
    12762: {"title": "Dog Coats and Jackets UK: Choosing the Right One", "cluster": "Dog Supplies"},
    12763: {"title": "Dog Travel Accessories UK: Essential Gear for UK Trips", "cluster": "Dog Supplies"},
    12764: {"title": "Dog Feeding Station Setup: Complete Guide for UK Owners", "cluster": "Dog Supplies"},
    12765: {"title": "DIY Cat Toys from Household Items: Easy Projects", "cluster": "Cat Toys"},
    12766: {"title": "Cat Puzzle Feeders UK: Guide to Food Puzzles for Cats", "cluster": "Cat Toys"},
    12767: {"title": "Interactive Cat Toys for Solo Play UK: Keep Cats Busy", "cluster": "Cat Toys"},
}

ALL_DRAFT_IDS = set(DRAFT_POSTS.keys())

# Exclusion patterns - do NOT add links to dog food or dog harness commercial content
EXCLUSION_PATTERNS = [
    r"\bdog\s+food\b",
    r"\bdog\s+harness\b",
    r"\bharness.*dog\b",
    r"\bdog.*harness\b",
]


# ---------------------------------------------------------------------------
# HTML Link Extractor
# ---------------------------------------------------------------------------
class LinkExtractor(HTMLParser):
    """Extract internal links from HTML content."""

    def __init__(self):
        super().__init__()
        self.links = []
        self._current_href = None
        self._current_text = ""
        self._in_link = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            if href and self._is_internal(href):
                self._current_href = href
                self._current_text = ""
                self._in_link = True

    def handle_data(self, data):
        if self._in_link:
            self._current_text += data

    def handle_endtag(self, tag):
        if tag == "a" and self._in_link:
            self.links.append({
                "href": self._current_href,
                "anchor_text": self._current_text.strip(),
            })
            self._in_link = False
            self._current_href = None
            self._current_text = ""

    @staticmethod
    def _is_internal(href):
        if not href:
            return False
        parsed = urlparse(href)
        if parsed.scheme and parsed.scheme not in ("http", "https"):
            return False
        if parsed.netloc and "pethubonline.com" not in parsed.netloc:
            return False
        if not parsed.netloc and not href.startswith("/"):
            return False
        return True


def extract_links(html_content):
    """Extract all internal links from HTML content."""
    if not html_content:
        return []
    parser = LinkExtractor()
    try:
        parser.feed(html_content)
    except Exception:
        pass
    return parser.links


# ---------------------------------------------------------------------------
# Curl helpers
# ---------------------------------------------------------------------------
def curl_get(url, retries=MAX_RETRIES):
    """GET request via curl with retry logic."""
    for attempt in range(1, retries + 1):
        try:
            cmd = ["curl", "-s", "--compressed", "-u", AUTH,
                   "--max-time", str(CURL_TIMEOUT), url]
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=CURL_TIMEOUT + 10)
            body = result.stdout.strip()
            if not body:
                raise ValueError("Empty response")

            # Check for rate limit
            if '"code":"rest_rate_limit"' in body or result.returncode != 0:
                raise ValueError(f"Rate limited or error (rc={result.returncode})")

            data = json.loads(body)

            # WP REST API error
            if isinstance(data, dict) and data.get("code"):
                code = data["code"]
                if code == "rest_post_invalid_page_number":
                    return None  # No more pages
                raise ValueError(f"WP API error: {code}")

            return data

        except json.JSONDecodeError as e:
            if attempt < retries:
                wait = 5 * attempt
                print(f"  [RETRY {attempt}/{retries}] JSON decode error at {url}: {e} -- waiting {wait}s")
                time.sleep(wait)
            else:
                print(f"  [FAILED] Could not parse JSON from {url}: {e}")
                return None
        except Exception as e:
            if attempt < retries:
                wait = 5 * attempt
                print(f"  [RETRY {attempt}/{retries}] {url}: {e} -- waiting {wait}s")
                time.sleep(wait)
            else:
                print(f"  [FAILED] {url}: {e}")
                return None
    return None


def curl_post_update(post_id, content, post_type="posts", retries=MAX_RETRIES):
    """POST update to a WP post via curl, using temp file for payload."""
    url = f"{WP_API_BASE}/{post_type}/{post_id}"
    payload = json.dumps({"content": content})

    for attempt in range(1, retries + 1):
        try:
            # Write JSON to temp file for large payloads
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                              delete=False) as f:
                f.write(payload)
                tmpfile = f.name

            cmd = ["curl", "-s", "-X", "POST", "--compressed",
                   "-u", AUTH,
                   "-H", "Content-Type: application/json",
                   "-d", f"@{tmpfile}",
                   "--max-time", str(CURL_TIMEOUT),
                   url]

            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=CURL_TIMEOUT + 10)

            # Clean up temp file
            os.unlink(tmpfile)

            body = result.stdout.strip()
            if not body:
                raise ValueError("Empty response from POST")

            data = json.loads(body)

            if isinstance(data, dict) and data.get("code"):
                code = data["code"]
                if "429" in str(code) or "rate" in str(code).lower():
                    raise ValueError(f"Rate limited: {code}")
                print(f"  [WARN] API returned: {code} for post {post_id}")
                return data

            return data

        except Exception as e:
            try:
                os.unlink(tmpfile)
            except Exception:
                pass
            if attempt < retries:
                wait = 5 * attempt
                print(f"  [RETRY {attempt}/{retries}] POST {post_id}: {e} -- waiting {wait}s")
                time.sleep(wait)
            else:
                print(f"  [FAILED] POST {post_id}: {e}")
                return None
    return None


# ---------------------------------------------------------------------------
# 1. Fetch ALL published posts and pages
# ---------------------------------------------------------------------------
def fetch_all_content():
    """Fetch all published posts and pages from WP REST API."""
    all_posts = []
    all_pages = []

    # Fetch posts
    print("\n=== Fetching published posts ===")
    page_num = 1
    while True:
        url = f"{WP_API_BASE}/posts?per_page=100&page={page_num}&context=edit"
        print(f"  Fetching posts page {page_num}...")
        time.sleep(API_SLEEP_GET)
        data = curl_get(url)
        if data is None or (isinstance(data, list) and len(data) == 0):
            break
        if isinstance(data, list):
            all_posts.extend(data)
            print(f"    Got {len(data)} posts (total: {len(all_posts)})")
            if len(data) < 100:
                break
        else:
            break
        page_num += 1

    # Fetch pages
    print("\n=== Fetching published pages ===")
    page_num = 1
    while True:
        url = f"{WP_API_BASE}/pages?per_page=100&page={page_num}&context=edit"
        print(f"  Fetching pages page {page_num}...")
        time.sleep(API_SLEEP_GET)
        data = curl_get(url)
        if data is None or (isinstance(data, list) and len(data) == 0):
            break
        if isinstance(data, list):
            all_pages.extend(data)
            print(f"    Got {len(data)} pages (total: {len(all_pages)})")
            if len(data) < 100:
                break
        else:
            break
        page_num += 1

    print(f"\n  Total posts: {len(all_posts)}, Total pages: {len(all_pages)}")
    return all_posts, all_pages


# ---------------------------------------------------------------------------
# 2. Build internal link map
# ---------------------------------------------------------------------------
def classify_post_cluster(post):
    """Classify a post into one of the priority clusters."""
    categories = post.get("categories", [])
    for cluster_name, cluster_info in PRIORITY_CLUSTERS.items():
        if cluster_info["category_id"] in categories:
            return cluster_name

    # Fallback: check title keywords
    title = get_title(post).lower()
    slug = post.get("slug", "").lower()
    text = f"{title} {slug}"

    if any(kw in text for kw in ["indoor cat", "catio", "cat enclosure", "cat exercise"]):
        return "Indoor Cats"
    if any(kw in text for kw in ["cat toy", "cat puzzle", "cat feeder", "interactive cat"]):
        return "Cat Toys"
    if any(kw in text for kw in ["pet care", "pet owner", "multi-pet", "seasonal pet"]):
        return "Pet Care"
    if any(kw in text for kw in ["dog supply", "dog supplies", "dog coat", "dog travel", "dog feeding"]):
        return "Dog Supplies"

    return "Other"


def get_title(post):
    """Extract title from post object."""
    title = post.get("title", {})
    if isinstance(title, dict):
        return title.get("rendered", title.get("raw", ""))
    return str(title)


def get_content_raw(post):
    """Extract raw content from post object (context=edit gives raw field)."""
    content = post.get("content", {})
    if isinstance(content, dict):
        return content.get("raw", content.get("rendered", ""))
    return str(content)


def get_link(post):
    """Get the permalink of a post."""
    return post.get("link", "")


def is_excluded_content(post):
    """Check if post should be excluded from link insertion (dog food/harness commercial)."""
    title = get_title(post).lower()
    slug = post.get("slug", "").lower()
    text = f"{title} {slug}"
    for pattern in EXCLUSION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def build_link_map(all_posts, all_pages):
    """Build comprehensive internal link map."""
    print("\n=== Building internal link map ===")

    # Combined content list
    all_content = []
    for p in all_posts:
        p["_type"] = "post"
        all_content.append(p)
    for p in all_pages:
        p["_type"] = "page"
        all_content.append(p)

    # Build URL-to-post lookup
    url_to_post = {}
    id_to_post = {}
    for post in all_content:
        link = get_link(post)
        if link:
            # Normalize URL
            normalized = normalize_url(link)
            url_to_post[normalized] = post
        pid = post.get("id")
        if pid:
            id_to_post[pid] = post

    # Extract all internal links
    link_map = []  # List of {source_id, source_title, source_cluster, target_url, anchor_text}
    incoming_links = defaultdict(list)  # target_url -> [source_ids]
    outgoing_links = defaultdict(list)  # source_id -> [target_urls]

    for post in all_content:
        pid = post.get("id")
        title = get_title(post)
        cluster = classify_post_cluster(post)
        content = get_content_raw(post)

        links = extract_links(content)
        for link_info in links:
            href = link_info["href"]
            anchor = link_info["anchor_text"]

            # Normalize URL
            if href.startswith("/"):
                href = f"{BASE_URL}{href}"
            normalized_target = normalize_url(href)

            link_entry = {
                "source_id": pid,
                "source_title": title,
                "source_cluster": cluster,
                "target_url": href,
                "target_normalized": normalized_target,
                "anchor_text": anchor,
            }
            link_map.append(link_entry)
            incoming_links[normalized_target].append(pid)
            outgoing_links[pid].append(normalized_target)

    print(f"  Total internal links found: {len(link_map)}")
    print(f"  Unique target URLs: {len(incoming_links)}")

    # Identify orphan pages (no incoming links)
    orphans = []
    for post in all_content:
        link = get_link(post)
        normalized = normalize_url(link) if link else ""
        pid = post.get("id")
        incoming_count = len(incoming_links.get(normalized, []))
        outgoing_count = len(outgoing_links.get(pid, []))
        if incoming_count == 0 and post.get("status") == "publish":
            orphans.append({
                "post_id": pid,
                "title": get_title(post),
                "cluster": classify_post_cluster(post),
                "incoming_links": incoming_count,
                "outgoing_links": outgoing_count,
                "url": link,
            })

    # Identify authority hubs (most outgoing)
    hubs = sorted(outgoing_links.items(), key=lambda x: len(x[1]), reverse=True)[:20]
    print(f"  Top authority hub: post {hubs[0][0]} with {len(hubs[0][1])} outgoing links" if hubs else "  No hubs found")

    # Identify link sinks (most incoming)
    sinks = sorted(incoming_links.items(), key=lambda x: len(x[1]), reverse=True)[:20]
    print(f"  Top link sink: {sinks[0][0]} with {len(sinks[0][1])} incoming links" if sinks else "  No sinks found")

    print(f"  Orphan pages: {len(orphans)}")

    return link_map, incoming_links, outgoing_links, orphans, url_to_post, id_to_post


def normalize_url(url):
    """Normalize URL for comparison."""
    if not url:
        return ""
    url = url.lower().strip()
    # Remove trailing slash
    url = url.rstrip("/")
    # Remove fragment
    parsed = urlparse(url)
    url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return url


# ---------------------------------------------------------------------------
# 3. Design hub-and-spoke architecture
# ---------------------------------------------------------------------------
def design_hub_spoke(all_posts, incoming_links, outgoing_links, id_to_post, url_to_post):
    """Design hub-and-spoke link architecture for priority clusters."""
    print("\n=== Designing hub-and-spoke architecture ===")

    cluster_posts = defaultdict(list)  # cluster -> [post objects]
    cluster_hubs = {}  # cluster -> post object

    # Sort posts into clusters
    for post in all_posts:
        if post.get("status") != "publish":
            continue
        cluster = classify_post_cluster(post)
        if cluster in PRIORITY_CLUSTERS:
            cluster_posts[cluster].append(post)

    # Select hubs: post with most incoming + outgoing links in cluster
    for cluster_name, posts in cluster_posts.items():
        best_hub = None
        best_score = -1
        for post in posts:
            pid = post.get("id")
            link = get_link(post)
            normalized = normalize_url(link)
            inc = len(incoming_links.get(normalized, []))
            out = len(outgoing_links.get(pid, []))
            score = inc * 2 + out  # Incoming links weighted more
            if score > best_score:
                best_score = score
                best_hub = post

        if best_hub:
            cluster_hubs[cluster_name] = best_hub
            print(f"  {cluster_name} hub: [{best_hub.get('id')}] {get_title(best_hub)} (score: {best_score})")

    # Build spoke lists per cluster
    hub_spoke_data = {}
    for cluster_name, cluster_info in PRIORITY_CLUSTERS.items():
        hub = cluster_hubs.get(cluster_name)
        spokes = []
        for post in cluster_posts.get(cluster_name, []):
            if hub and post.get("id") == hub.get("id"):
                continue
            spokes.append(post)

        hub_spoke_data[cluster_name] = {
            "hub": hub,
            "spokes": spokes,
            "drafts": cluster_info["draft_ids"],
        }
        spoke_count = len(spokes) + len(cluster_info["draft_ids"])
        print(f"  {cluster_name}: {len(spokes)} published spokes + {len(cluster_info['draft_ids'])} draft spokes = {spoke_count} total")

    return hub_spoke_data, cluster_posts


# ---------------------------------------------------------------------------
# 4. Generate anchor text variations
# ---------------------------------------------------------------------------
def generate_anchor_variations(title, cluster):
    """Generate diverse anchor text variations for a post title."""
    variations = [title]  # Original title

    # Shortened version
    words = title.split()
    if len(words) > 5:
        variations.append(" ".join(words[:5]))
    if len(words) > 3:
        variations.append(" ".join(words[:3]) + " guide")

    # Cluster-specific variations
    title_lower = title.lower()
    if "uk" in title_lower:
        # Remove UK prefix/suffix
        no_uk = re.sub(r'\bUK\b', '', title, flags=re.IGNORECASE).strip()
        no_uk = re.sub(r'\s+', ' ', no_uk).strip(": ")
        if no_uk and no_uk != title:
            variations.append(no_uk)

    # Action-oriented
    if "guide" in title_lower:
        variations.append(title_lower.replace("guide", "tips").title())
    if "how to" in title_lower:
        variations.append(re.sub(r'how to\s+', '', title_lower, flags=re.IGNORECASE).strip().capitalize())

    # Descriptive variations
    if cluster == "Indoor Cats":
        variations.extend(["keeping indoor cats happy", "indoor cat enrichment", "cat indoor living tips"])
    elif cluster == "Cat Toys":
        variations.extend(["best cat toys", "engaging cat activities", "cat playtime essentials"])
    elif cluster == "Pet Care":
        variations.extend(["essential pet care tips", "pet ownership guide", "caring for your pet"])
    elif cluster == "Dog Supplies":
        variations.extend(["essential dog gear", "dog accessories guide", "supplies for your dog"])

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for v in variations:
        v_clean = v.strip()
        if v_clean and v_clean.lower() not in seen:
            seen.add(v_clean.lower())
            unique.append(v_clean)

    return unique[:8]  # Cap at 8 variations


# ---------------------------------------------------------------------------
# 5. Add contextual internal links
# ---------------------------------------------------------------------------
def find_contextual_insertion_points(content, target_keywords):
    """Find paragraphs in content that are contextually relevant for link insertion."""
    # Split into Gutenberg blocks
    blocks = re.split(r'(<!-- wp:\w+[^>]*-->)', content)
    insertion_points = []

    for i, block in enumerate(blocks):
        # Only insert in paragraph blocks
        if '<!-- wp:paragraph' in block or (i > 0 and '<!-- wp:paragraph' in blocks[i-1]):
            block_lower = block.lower()
            relevance = 0
            for kw in target_keywords:
                if kw.lower() in block_lower:
                    relevance += 1
            if relevance > 0:
                insertion_points.append({
                    "index": i,
                    "text": block,
                    "relevance": relevance,
                })

    # Sort by relevance
    insertion_points.sort(key=lambda x: x["relevance"], reverse=True)
    return insertion_points


def add_contextual_link(paragraph_html, url, anchor_text):
    """Insert a link into a paragraph at a natural position."""
    # Find a sentence boundary near the middle
    text_match = re.search(r'<p[^>]*>(.*?)</p>', paragraph_html, re.DOTALL)
    if not text_match:
        return paragraph_html, False

    inner_text = text_match.group(1)

    # Don't insert if this URL is already linked
    if url.rstrip("/") in paragraph_html:
        return paragraph_html, False

    # Don't insert if anchor text is already linked
    if f">{anchor_text}<" in paragraph_html:
        return paragraph_html, False

    # Find sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', inner_text)
    if not sentences:
        return paragraph_html, False

    # Try to find a sentence with related keywords
    link_html = f'<a href="{url}">{anchor_text}</a>'

    # Insert at end of a sentence with period
    # Find a good insertion point (after a period, before next sentence)
    for idx, sentence in enumerate(sentences):
        if len(sentence) > 30 and "." in sentence:
            # Append link reference naturally
            modified = sentence.rstrip(".") + f". See our {link_html} for more details."
            sentences[idx] = modified
            new_inner = " ".join(sentences)
            new_paragraph = paragraph_html.replace(inner_text, new_inner)
            return new_paragraph, True

    # Fallback: append at end
    if inner_text.strip():
        new_inner = inner_text.rstrip() + f" For more, check out our {link_html}."
        new_paragraph = paragraph_html.replace(inner_text, new_inner)
        return new_paragraph, True

    return paragraph_html, False


def build_related_reading_section(links_to_add):
    """Build a Gutenberg-formatted Related Reading section."""
    if not links_to_add:
        return ""

    items = []
    for link in links_to_add:
        items.append(f'<li><a href="{link["url"]}">{link["anchor"]}</a> - {link["description"]}</li>')

    items_html = "".join(items)
    section = (
        '\n\n<!-- wp:heading {"level":2} -->\n'
        '<h2 class="wp-block-heading">Related Reading</h2>\n'
        '<!-- /wp:heading -->\n\n'
        '<!-- wp:list -->\n'
        f'<ul class="wp-block-list">{items_html}</ul>\n'
        '<!-- /wp:list -->'
    )
    return section


def get_link_description(title, cluster):
    """Generate a brief, natural description for a related reading link."""
    title_lower = title.lower()

    if "guide" in title_lower:
        return f"A comprehensive overview for {cluster.lower()} enthusiasts"
    if "how to" in title_lower:
        return "Step-by-step instructions and expert advice"
    if "tips" in title_lower:
        return "Practical advice from pet care professionals"
    if "best" in title_lower:
        return "Our top picks reviewed and compared"
    if "review" in title_lower:
        return "Honest reviews with pros and cons"
    if "uk" in title_lower:
        return "Tailored recommendations for UK pet owners"

    descriptions = {
        "Indoor Cats": "Helping your indoor cat thrive",
        "Cat Toys": "Keeping your cat entertained and active",
        "Pet Care": "Expert pet care guidance",
        "Dog Supplies": "Essential gear for your canine companion",
    }
    return descriptions.get(cluster, "Helpful reading for pet owners")


def generate_link_keywords(title, cluster):
    """Generate keywords from a title for contextual relevance matching."""
    # Remove common words
    stopwords = {"a", "an", "the", "to", "for", "of", "in", "on", "and", "or",
                 "is", "are", "was", "were", "be", "been", "your", "our", "how",
                 "what", "why", "when", "with", "from", "uk", "complete", "guide",
                 "best", "top"}
    words = re.findall(r'\b\w+\b', title.lower())
    keywords = [w for w in words if w not in stopwords and len(w) > 2]

    # Add cluster keywords
    cluster_kw = {
        "Indoor Cats": ["indoor", "cat", "catio", "enclosure", "exercise", "play"],
        "Cat Toys": ["cat", "toy", "puzzle", "feeder", "interactive", "play"],
        "Pet Care": ["pet", "care", "owner", "health", "seasonal", "household"],
        "Dog Supplies": ["dog", "supply", "coat", "travel", "feeding", "gear"],
    }
    keywords.extend(cluster_kw.get(cluster, []))

    return list(set(keywords))


# ---------------------------------------------------------------------------
# 6. Core optimization logic
# ---------------------------------------------------------------------------
def optimize_internal_links(all_posts, all_pages, hub_spoke_data, cluster_posts,
                             link_map, incoming_links, outgoing_links, url_to_post, id_to_post):
    """Main optimization: add contextual links to published posts."""
    print("\n=== Optimizing internal links ===")

    optimization_log = []
    new_link_map_entries = []
    anchor_usage = defaultdict(lambda: defaultdict(int))  # anchor -> {target_url: count}
    posts_updated = 0
    total_links_added = 0
    cluster_link_counts = defaultdict(int)

    # Build draft URL lookup (we'll fetch draft URLs from the API)
    draft_urls = {}
    for draft_id, draft_info in DRAFT_POSTS.items():
        # Draft posts typically have a preview URL pattern
        # We'll try to get the actual permalink
        draft_urls[draft_id] = None  # Will be populated

    # Fetch draft post URLs
    print("\n  Fetching draft post URLs...")
    for draft_id in DRAFT_POSTS:
        time.sleep(API_SLEEP_GET)
        url = f"{WP_API_BASE}/posts/{draft_id}?context=edit"
        data = curl_get(url)
        if data and isinstance(data, dict):
            permalink = data.get("link", "")
            if permalink:
                draft_urls[draft_id] = permalink
                print(f"    Draft {draft_id}: {permalink}")
            else:
                # Construct likely URL from slug
                slug = data.get("slug", "")
                if slug:
                    draft_urls[draft_id] = f"{BASE_URL}/{slug}/"
                    print(f"    Draft {draft_id} (from slug): {draft_urls[draft_id]}")
                else:
                    draft_urls[draft_id] = f"{BASE_URL}/?p={draft_id}"
                    print(f"    Draft {draft_id} (fallback): {draft_urls[draft_id]}")

    # Build list of target posts per cluster (for link suggestions)
    cluster_link_targets = {}
    for cluster_name, hs_data in hub_spoke_data.items():
        targets = []

        # Hub
        hub = hs_data["hub"]
        if hub:
            targets.append({
                "id": hub.get("id"),
                "title": get_title(hub),
                "url": get_link(hub),
                "is_hub": True,
                "is_draft": False,
                "cluster": cluster_name,
            })

        # Spokes
        for spoke in hs_data["spokes"]:
            targets.append({
                "id": spoke.get("id"),
                "title": get_title(spoke),
                "url": get_link(spoke),
                "is_hub": False,
                "is_draft": False,
                "cluster": cluster_name,
            })

        # Drafts
        for draft_id in hs_data["drafts"]:
            draft_info = DRAFT_POSTS[draft_id]
            targets.append({
                "id": draft_id,
                "title": draft_info["title"],
                "url": draft_urls.get(draft_id, f"{BASE_URL}/?p={draft_id}"),
                "is_hub": False,
                "is_draft": True,
                "cluster": cluster_name,
            })

        cluster_link_targets[cluster_name] = targets

    # Cross-cluster related map (for cross-linking)
    related_clusters = {
        "Indoor Cats": ["Cat Toys", "Pet Care"],
        "Cat Toys": ["Indoor Cats", "Pet Care"],
        "Pet Care": ["Indoor Cats", "Cat Toys", "Dog Supplies"],
        "Dog Supplies": ["Pet Care"],
    }

    # Process each published post in priority clusters
    print("\n  Processing published posts for link optimization...")

    posts_to_update = []
    for cluster_name, posts in cluster_posts.items():
        print(f"\n  --- Cluster: {cluster_name} ({len(posts)} posts) ---")

        for post in posts:
            pid = post.get("id")
            title = get_title(post)
            status = post.get("status", "")

            # Skip drafts - NEVER modify drafts
            if pid in ALL_DRAFT_IDS or status != "publish":
                print(f"    [SKIP] {pid} '{title}' (draft/unpublished)")
                continue

            # Skip excluded content
            if is_excluded_content(post):
                print(f"    [SKIP] {pid} '{title}' (excluded: dog food/harness)")
                continue

            content = get_content_raw(post)
            if not content:
                print(f"    [SKIP] {pid} '{title}' (no content)")
                continue

            # Get existing links in this post
            existing_links = extract_links(content)
            existing_urls = set(normalize_url(l["href"]) for l in existing_links)
            links_before = len(existing_links)

            # Determine which links to add (3-5 per post)
            links_to_add = []
            contextual_added = 0

            # Priority 1: Link to hub (if not already linked and this isn't the hub)
            hub = hub_spoke_data[cluster_name]["hub"]
            if hub and pid != hub.get("id"):
                hub_url = get_link(hub)
                hub_normalized = normalize_url(hub_url)
                if hub_normalized not in existing_urls:
                    anchors = generate_anchor_variations(get_title(hub), cluster_name)
                    links_to_add.append({
                        "url": hub_url,
                        "anchor": anchors[0] if anchors else get_title(hub),
                        "title": get_title(hub),
                        "type": "hub_spoke",
                        "cluster": cluster_name,
                        "description": get_link_description(get_title(hub), cluster_name),
                        "keywords": generate_link_keywords(get_title(hub), cluster_name),
                    })

            # Priority 2: Link to draft posts in same cluster
            for draft_id in hub_spoke_data[cluster_name]["drafts"]:
                if len(links_to_add) >= 5:
                    break
                draft_info = DRAFT_POSTS[draft_id]
                draft_url = draft_urls.get(draft_id, f"{BASE_URL}/?p={draft_id}")
                draft_normalized = normalize_url(draft_url)
                if draft_normalized not in existing_urls:
                    anchors = generate_anchor_variations(draft_info["title"], cluster_name)
                    # Pick a varied anchor
                    anchor_idx = len(links_to_add) % len(anchors) if anchors else 0
                    links_to_add.append({
                        "url": draft_url,
                        "anchor": anchors[anchor_idx] if anchors else draft_info["title"],
                        "title": draft_info["title"],
                        "type": "hub_spoke",
                        "cluster": cluster_name,
                        "description": get_link_description(draft_info["title"], cluster_name),
                        "keywords": generate_link_keywords(draft_info["title"], cluster_name),
                    })

            # Priority 3: Link to other spokes in same cluster
            for spoke in hub_spoke_data[cluster_name]["spokes"]:
                if len(links_to_add) >= 5:
                    break
                spoke_id = spoke.get("id")
                if spoke_id == pid:
                    continue
                spoke_url = get_link(spoke)
                spoke_normalized = normalize_url(spoke_url)
                if spoke_normalized not in existing_urls:
                    anchors = generate_anchor_variations(get_title(spoke), cluster_name)
                    anchor_idx = len(links_to_add) % len(anchors) if anchors else 0
                    links_to_add.append({
                        "url": spoke_url,
                        "anchor": anchors[anchor_idx] if anchors else get_title(spoke),
                        "title": get_title(spoke),
                        "type": "hub_spoke",
                        "cluster": cluster_name,
                        "description": get_link_description(get_title(spoke), cluster_name),
                        "keywords": generate_link_keywords(get_title(spoke), cluster_name),
                    })

            # Priority 4: Cross-cluster links (if we still have room)
            if len(links_to_add) < 3:
                for related_cluster in related_clusters.get(cluster_name, []):
                    if len(links_to_add) >= 5:
                        break
                    related_targets = cluster_link_targets.get(related_cluster, [])
                    for target in related_targets[:2]:  # Max 2 from each related cluster
                        if len(links_to_add) >= 5:
                            break
                        target_normalized = normalize_url(target["url"])
                        if target_normalized not in existing_urls:
                            anchors = generate_anchor_variations(target["title"], related_cluster)
                            links_to_add.append({
                                "url": target["url"],
                                "anchor": anchors[1] if len(anchors) > 1 else target["title"],
                                "title": target["title"],
                                "type": "contextual",
                                "cluster": related_cluster,
                                "description": get_link_description(target["title"], related_cluster),
                                "keywords": generate_link_keywords(target["title"], related_cluster),
                            })

            if not links_to_add:
                print(f"    [OK] {pid} '{title}' - no new links needed")
                optimization_log.append({
                    "post_id": pid,
                    "title": title,
                    "cluster": cluster_name,
                    "links_added": 0,
                    "links_before": links_before,
                    "links_after": links_before,
                    "action_taken": "no_action_needed",
                })
                continue

            # Enforce anchor diversity: no anchor used more than 3 times for same target
            filtered_links = []
            for link in links_to_add:
                anchor = link["anchor"]
                target = normalize_url(link["url"])
                if anchor_usage[anchor.lower()][target] >= 3:
                    # Pick alternative anchor
                    alts = generate_anchor_variations(link["title"], link["cluster"])
                    found_alt = False
                    for alt in alts:
                        if anchor_usage[alt.lower()][target] < 3:
                            link["anchor"] = alt
                            found_alt = True
                            break
                    if not found_alt:
                        continue  # Skip this link entirely
                filtered_links.append(link)
                anchor_usage[link["anchor"].lower()][normalize_url(link["url"])] += 1

            links_to_add = filtered_links[:5]  # Cap at 5

            if not links_to_add:
                print(f"    [OK] {pid} '{title}' - all anchors exhausted")
                continue

            # Insert links into content
            modified_content = content
            contextual_inserted = 0

            # Try contextual insertion first (up to 3)
            for link in links_to_add[:3]:
                keywords = link.get("keywords", [])
                insertion_points = find_contextual_insertion_points(modified_content, keywords)

                if insertion_points:
                    best_point = insertion_points[0]
                    old_block = best_point["text"]
                    new_block, success = add_contextual_link(
                        old_block, link["url"], link["anchor"]
                    )
                    if success and old_block != new_block:
                        modified_content = modified_content.replace(old_block, new_block, 1)
                        contextual_inserted += 1
                        link["_inserted"] = "contextual"

            # Remaining links go into Related Reading section
            remaining = [l for l in links_to_add if "_inserted" not in l]
            if remaining or contextual_inserted < 3:
                # Also add any contextual ones that failed to insert
                related_items = remaining
                if related_items:
                    # Check if Related Reading section already exists
                    if "Related Reading" in modified_content:
                        # Find existing Related Reading section and append to it
                        rr_match = re.search(
                            r'(<!-- wp:list -->\s*<ul[^>]*>)(.*?)(</ul>\s*<!-- /wp:list -->)',
                            modified_content, re.DOTALL
                        )
                        if rr_match:
                            existing_items = rr_match.group(2)
                            new_items = ""
                            for link in related_items:
                                new_items += f'<li><a href="{link["url"]}">{link["anchor"]}</a> - {link["description"]}</li>'
                                link["_inserted"] = "related_reading"
                            modified_content = modified_content.replace(
                                rr_match.group(0),
                                f'{rr_match.group(1)}{existing_items}{new_items}{rr_match.group(3)}'
                            )
                    else:
                        section = build_related_reading_section(related_items)
                        if section:
                            modified_content = modified_content + section
                            for link in related_items:
                                link["_inserted"] = "related_reading"

            # Count total links added
            links_added = sum(1 for l in links_to_add if "_inserted" in l)
            links_after = links_before + links_added

            if links_added > 0 and modified_content != content:
                posts_to_update.append({
                    "id": pid,
                    "title": title,
                    "cluster": cluster_name,
                    "content": modified_content,
                    "links_added": links_added,
                    "links_before": links_before,
                    "links_after": links_after,
                    "type": post.get("_type", "post"),
                })

                # Record new link map entries
                for link in links_to_add:
                    if "_inserted" in link:
                        target_title = link.get("title", "")
                        target_cluster = link.get("cluster", cluster_name)
                        link_type = link.get("_inserted", "contextual")
                        if link.get("type") == "hub_spoke":
                            link_type = "hub_spoke"
                        new_link_map_entries.append({
                            "source_id": pid,
                            "source_title": title,
                            "source_cluster": cluster_name,
                            "target_url": link["url"],
                            "target_title": target_title,
                            "target_cluster": target_cluster,
                            "anchor_text": link["anchor"],
                            "link_type": link_type,
                        })

                total_links_added += links_added
                cluster_link_counts[cluster_name] += links_added
                print(f"    [ADD] {pid} '{title}' +{links_added} links ({contextual_inserted} contextual, {links_added - contextual_inserted} related_reading)")

            optimization_log.append({
                "post_id": pid,
                "title": title,
                "cluster": cluster_name,
                "links_added": links_added,
                "links_before": links_before,
                "links_after": links_after,
                "action_taken": f"added_{links_added}_links" if links_added > 0 else "no_changes",
            })

    # Also add hub->spoke links (hub should link to all spokes)
    print("\n  --- Adding hub -> spoke links ---")
    for cluster_name, hs_data in hub_spoke_data.items():
        hub = hs_data["hub"]
        if not hub:
            continue

        pid = hub.get("id")
        title = get_title(hub)

        if pid in ALL_DRAFT_IDS or hub.get("status") != "publish":
            continue

        if is_excluded_content(hub):
            continue

        content = get_content_raw(hub)
        existing_links = extract_links(content)
        existing_urls = set(normalize_url(l["href"]) for l in existing_links)
        links_before = len(existing_links)

        # Hub should link to all spokes + drafts
        links_to_add = []

        for spoke in hs_data["spokes"]:
            spoke_url = get_link(spoke)
            if normalize_url(spoke_url) not in existing_urls:
                anchors = generate_anchor_variations(get_title(spoke), cluster_name)
                anchor_idx = len(links_to_add) % len(anchors) if anchors else 0
                links_to_add.append({
                    "url": spoke_url,
                    "anchor": anchors[anchor_idx] if anchors else get_title(spoke),
                    "title": get_title(spoke),
                    "type": "hub_spoke",
                    "cluster": cluster_name,
                    "description": get_link_description(get_title(spoke), cluster_name),
                    "keywords": generate_link_keywords(get_title(spoke), cluster_name),
                })

        for draft_id in hs_data["drafts"]:
            draft_info = DRAFT_POSTS[draft_id]
            draft_url = draft_urls.get(draft_id, f"{BASE_URL}/?p={draft_id}")
            if normalize_url(draft_url) not in existing_urls:
                anchors = generate_anchor_variations(draft_info["title"], cluster_name)
                anchor_idx = len(links_to_add) % len(anchors) if anchors else 0
                links_to_add.append({
                    "url": draft_url,
                    "anchor": anchors[anchor_idx] if anchors else draft_info["title"],
                    "title": draft_info["title"],
                    "type": "hub_spoke",
                    "cluster": cluster_name,
                    "description": get_link_description(draft_info["title"], cluster_name),
                    "keywords": generate_link_keywords(draft_info["title"], cluster_name),
                })

        if not links_to_add:
            print(f"    [OK] Hub {pid} '{title}' - already links to all spokes")
            continue

        # Enforce anchor diversity
        filtered = []
        for link in links_to_add:
            anchor = link["anchor"]
            target = normalize_url(link["url"])
            if anchor_usage[anchor.lower()][target] >= 3:
                alts = generate_anchor_variations(link["title"], link["cluster"])
                found = False
                for alt in alts:
                    if anchor_usage[alt.lower()][target] < 3:
                        link["anchor"] = alt
                        found = True
                        break
                if not found:
                    continue
            filtered.append(link)
            anchor_usage[link["anchor"].lower()][normalize_url(link["url"])] += 1

        links_to_add = filtered

        if not links_to_add:
            continue

        # Insert via Related Reading section (hubs get a comprehensive spoke index)
        modified_content = content
        if "Related Reading" in modified_content:
            rr_match = re.search(
                r'(<!-- wp:list -->\s*<ul[^>]*>)(.*?)(</ul>\s*<!-- /wp:list -->)',
                modified_content, re.DOTALL
            )
            if rr_match:
                new_items = ""
                for link in links_to_add:
                    new_items += f'<li><a href="{link["url"]}">{link["anchor"]}</a> - {link["description"]}</li>'
                    link["_inserted"] = "related_reading"
                modified_content = modified_content.replace(
                    rr_match.group(0),
                    f'{rr_match.group(1)}{rr_match.group(2)}{new_items}{rr_match.group(3)}'
                )
        else:
            section = build_related_reading_section(links_to_add)
            if section:
                modified_content = modified_content + section
                for link in links_to_add:
                    link["_inserted"] = "related_reading"

        links_added = sum(1 for l in links_to_add if "_inserted" in l)

        if links_added > 0 and modified_content != content:
            # Check if hub was already queued for update
            existing_update = next((u for u in posts_to_update if u["id"] == pid), None)
            if existing_update:
                # Merge: use hub's latest content
                existing_update["content"] = modified_content
                existing_update["links_added"] += links_added
                existing_update["links_after"] += links_added
            else:
                posts_to_update.append({
                    "id": pid,
                    "title": title,
                    "cluster": cluster_name,
                    "content": modified_content,
                    "links_added": links_added,
                    "links_before": links_before,
                    "links_after": links_before + links_added,
                    "type": hub.get("_type", "post"),
                })

            for link in links_to_add:
                if "_inserted" in link:
                    new_link_map_entries.append({
                        "source_id": pid,
                        "source_title": title,
                        "source_cluster": cluster_name,
                        "target_url": link["url"],
                        "target_title": link["title"],
                        "target_cluster": link["cluster"],
                        "anchor_text": link["anchor"],
                        "link_type": "hub_spoke",
                    })

            total_links_added += links_added
            cluster_link_counts[cluster_name] += links_added
            print(f"    [ADD] Hub {pid} '{title}' +{links_added} spoke links")

        optimization_log.append({
            "post_id": pid,
            "title": title,
            "cluster": cluster_name,
            "links_added": links_added,
            "links_before": links_before,
            "links_after": links_before + links_added,
            "action_taken": f"hub_added_{links_added}_spoke_links" if links_added > 0 else "no_changes",
        })

    return posts_to_update, optimization_log, new_link_map_entries, anchor_usage, total_links_added, cluster_link_counts


# ---------------------------------------------------------------------------
# 7. Push updates to WordPress
# ---------------------------------------------------------------------------
def push_updates(posts_to_update):
    """Push updated content to WordPress via REST API."""
    print(f"\n=== Pushing {len(posts_to_update)} updates to WordPress ===")
    success_count = 0
    fail_count = 0

    for i, update in enumerate(posts_to_update):
        pid = update["id"]
        title = update["title"]
        content = update["content"]
        post_type = "posts" if update.get("type", "post") == "post" else "pages"

        print(f"  [{i+1}/{len(posts_to_update)}] Updating {pid} '{title}'...")
        time.sleep(API_SLEEP_POST)

        result = curl_post_update(pid, content, post_type=post_type)
        if result and isinstance(result, dict) and result.get("id"):
            success_count += 1
            print(f"    [OK] Updated successfully")
        else:
            fail_count += 1
            print(f"    [FAIL] Update failed")

    print(f"\n  Results: {success_count} succeeded, {fail_count} failed")
    return success_count, fail_count


# ---------------------------------------------------------------------------
# 8. Generate CSV reports
# ---------------------------------------------------------------------------
def write_csv_report(filename, rows, fieldnames):
    """Write a CSV report."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> {filepath} ({len(rows)} rows)")


def generate_reports(link_map, new_link_map_entries, optimization_log, orphans,
                     anchor_usage, hub_spoke_data, cluster_posts, draft_urls):
    """Generate all CSV reports."""
    print("\n=== Generating CSV reports ===")

    # a. internal_link_map.csv - combine existing + new
    all_link_entries = []

    # Existing links from the map
    for entry in link_map:
        all_link_entries.append({
            "source_id": entry["source_id"],
            "source_title": entry["source_title"],
            "source_cluster": entry["source_cluster"],
            "target_url": entry["target_url"],
            "target_title": "",  # Would need reverse lookup
            "target_cluster": "",
            "anchor_text": entry["anchor_text"],
            "link_type": "existing",
        })

    # New links added
    for entry in new_link_map_entries:
        all_link_entries.append(entry)

    write_csv_report("internal_link_map.csv", all_link_entries,
                     ["source_id", "source_title", "source_cluster", "target_url",
                      "target_title", "target_cluster", "anchor_text", "link_type"])

    # b. link_optimization_log.csv
    write_csv_report("link_optimization_log.csv", optimization_log,
                     ["post_id", "title", "cluster", "links_added", "links_before",
                      "links_after", "action_taken"])

    # c. orphan_pages.csv
    orphan_rows = []
    for o in orphans:
        orphan_rows.append({
            "post_id": o["post_id"],
            "title": o["title"],
            "cluster": o["cluster"],
            "incoming_links": o["incoming_links"],
            "outgoing_links": o["outgoing_links"],
            "status": "orphan",
        })
    write_csv_report("orphan_pages.csv", orphan_rows,
                     ["post_id", "title", "cluster", "incoming_links", "outgoing_links", "status"])

    # d. anchor_diversity.csv
    anchor_rows = []
    for anchor, targets in anchor_usage.items():
        for target_url, count in targets.items():
            status = "ok"
            if count > 3:
                status = "duplicate"
            elif count == 3:
                status = "warning"
            anchor_rows.append({
                "anchor_text": anchor,
                "target_url": target_url,
                "usage_count": count,
                "diversity_status": status,
            })
    write_csv_report("anchor_diversity.csv", anchor_rows,
                     ["anchor_text", "target_url", "usage_count", "diversity_status"])

    # e. hub_spoke_map.csv
    hub_spoke_rows = []
    for cluster_name, hs_data in hub_spoke_data.items():
        hub = hs_data["hub"]
        if not hub:
            continue
        spoke_urls = []
        for spoke in hs_data["spokes"]:
            spoke_urls.append(get_link(spoke))
        for draft_id in hs_data["drafts"]:
            spoke_urls.append(draft_urls.get(draft_id, f"{BASE_URL}/?p={draft_id}"))

        hub_spoke_rows.append({
            "cluster": cluster_name,
            "hub_url": get_link(hub),
            "hub_title": get_title(hub),
            "spoke_count": len(spoke_urls),
            "spoke_urls": " | ".join(spoke_urls),
        })
    write_csv_report("hub_spoke_map.csv", hub_spoke_rows,
                     ["cluster", "hub_url", "hub_title", "spoke_count", "spoke_urls"])

    return anchor_rows


# ---------------------------------------------------------------------------
# 9. Print summary
# ---------------------------------------------------------------------------
def print_summary(total_links_added, cluster_link_counts, orphans, anchor_rows,
                  optimization_log, posts_updated_ok, posts_updated_fail):
    """Print final summary."""
    print("\n" + "=" * 70)
    print("  PHASE 11Q - INTERNAL LINK OPTIMIZATION SUMMARY")
    print("=" * 70)

    print(f"\n  Total links added: {total_links_added}")
    print(f"  Posts updated: {posts_updated_ok} succeeded, {posts_updated_fail} failed")

    print(f"\n  Per-cluster breakdown:")
    for cluster, count in sorted(cluster_link_counts.items()):
        print(f"    {cluster}: +{count} links")

    # Orphan analysis
    orphan_fixed = sum(1 for log in optimization_log if log["links_added"] > 0
                       and any(o["post_id"] == log["post_id"] for o in orphans))
    print(f"\n  Orphan pages found: {len(orphans)}")
    print(f"  Orphan pages with new incoming links: {orphan_fixed}")

    # Anchor diversity score
    total_anchors = len(anchor_rows)
    duplicates = sum(1 for a in anchor_rows if a["diversity_status"] == "duplicate")
    warnings = sum(1 for a in anchor_rows if a["diversity_status"] == "warning")
    if total_anchors > 0:
        diversity_score = round((1 - duplicates / total_anchors) * 100, 1)
    else:
        diversity_score = 100.0
    print(f"\n  Anchor diversity score: {diversity_score}%")
    print(f"    OK: {total_anchors - duplicates - warnings}")
    print(f"    Warnings (3x): {warnings}")
    print(f"    Duplicates (>3x): {duplicates}")

    print(f"\n  Reports generated in: {OUTPUT_DIR}/")
    print(f"    - internal_link_map.csv")
    print(f"    - link_optimization_log.csv")
    print(f"    - orphan_pages.csv")
    print(f"    - anchor_diversity.csv")
    print(f"    - hub_spoke_map.csv")
    print("=" * 70)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("  PetHub Online - Phase 11Q Internal Link Optimization Engine")
    print("=" * 70)

    # Step 1: Fetch all content
    all_posts, all_pages = fetch_all_content()

    if not all_posts:
        print("[ERROR] No posts fetched. Exiting.")
        sys.exit(1)

    # Step 2: Build internal link map
    link_map, incoming_links, outgoing_links, orphans, url_to_post, id_to_post = \
        build_link_map(all_posts, all_pages)

    # Step 3: Design hub-and-spoke architecture
    hub_spoke_data, cluster_posts = design_hub_spoke(
        all_posts, incoming_links, outgoing_links, id_to_post, url_to_post
    )

    # Step 4-5: Optimize and add links
    posts_to_update, optimization_log, new_link_map_entries, anchor_usage, \
        total_links_added, cluster_link_counts = optimize_internal_links(
            all_posts, all_pages, hub_spoke_data, cluster_posts,
            link_map, incoming_links, outgoing_links, url_to_post, id_to_post
        )

    # Step 6: Push updates to WordPress
    posts_updated_ok, posts_updated_fail = 0, 0
    if posts_to_update:
        posts_updated_ok, posts_updated_fail = push_updates(posts_to_update)
    else:
        print("\n  No posts to update.")

    # Step 7: Fetch draft URLs for reports (already done in optimize step)
    draft_urls = {}
    for draft_id in DRAFT_POSTS:
        draft_urls[draft_id] = f"{BASE_URL}/?p={draft_id}"  # Fallback

    # Step 8: Generate reports
    anchor_rows = generate_reports(
        link_map, new_link_map_entries, optimization_log, orphans,
        anchor_usage, hub_spoke_data, cluster_posts, draft_urls
    )

    # Step 9: Print summary
    print_summary(total_links_added, cluster_link_counts, orphans, anchor_rows,
                  optimization_log, posts_updated_ok, posts_updated_fail)


if __name__ == "__main__":
    main()
