#!/usr/bin/env python3
"""
10AE-G: Semantic Corridor Engine for pethubonline.com
Purpose: Map semantic corridors between content clusters, fix orphan pages,
         and strengthen weak cross-cluster internal linking.
"""

import subprocess
import json
import csv
import re
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from collections import defaultdict
from urllib.parse import urlparse, unquote

# ── Config ──────────────────────────────────────────────────────────────────
WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ae_data"

# Priority corridors (bidirectional)
PRIORITY_CORRIDORS = [
    ("Cat Toys", "Cat Supplies"),
    ("Dog Health", "Dog Food"),
    ("Dog Toys", "Puppy Care"),
    ("Dog Beds", "Dog Care"),
    ("Dog Harnesses", "Dog Training/Care"),
    ("Pet Care", "Educational"),
]

# Cluster classification keywords (order matters: first match wins)
CLUSTER_KEYWORDS = {
    "Cat Toys":           ["cat toy", "cat toys", "toys for cats", "kitten toy", "kitten toys"],
    "Cat Supplies":       ["cat suppli", "cat litter", "cat bed", "cat food", "cat bowl", "cat carrier",
                           "cat collar", "cat harness", "cat tree", "cat scratch", "cat feeder",
                           "cat fountain", "cat grooming", "cat shampoo", "cat treat"],
    "Cat Health":         ["cat health", "cat vet", "cat disease", "cat sick", "cat medicat", "cat flea",
                           "cat dental", "cat vaccin"],
    "Cat Care":           ["cat care", "cats need", "caring for cat", "cat groom", "cat bath",
                           "indoor cat", "outdoor cat"],
    "Dog Toys":           ["dog toy", "dog toys", "toys for dog", "puppy toy", "puppy toys", "chew toy"],
    "Dog Food":           ["dog food", "puppy food", "dog diet", "dog nutrition", "dog feed",
                           "dog treat", "best food for dog", "raw diet dog", "dog kibble"],
    "Dog Health":         ["dog health", "dog vet", "dog disease", "dog sick", "dog medicat", "dog flea",
                           "dog dental", "dog vaccin", "dog allerg", "dog hip", "dog joint",
                           "dog arthritis", "dog supplement"],
    "Dog Beds":           ["dog bed", "dog beds", "puppy bed", "orthopedic bed", "dog crate pad",
                           "dog mattress", "dog cushion", "dog sleeping"],
    "Dog Harnesses":      ["dog harness", "harnesses for dog", "no-pull harness", "puppy harness",
                           "dog leash", "dog collar", "dog lead"],
    "Dog Training/Care":  ["dog training", "puppy training", "obedience", "dog behavio", "crate train",
                           "potty train", "leash train", "dog command", "dog socializ"],
    "Dog Care":           ["dog care", "dog groom", "dog bath", "dog nail", "dog brush", "dog shampoo",
                           "dog exercise", "dog walk"],
    "Puppy Care":         ["puppy care", "new puppy", "puppy guid", "puppy essential", "puppy checklist",
                           "bringing puppy home", "puppy proof", "first puppy"],
    "Pet Care":           ["pet care", "pet health", "pet safety", "pet insurance", "pet owner",
                           "pet parent", "pet-friendly", "pet grooming"],
    "Educational":        ["how to", "guide to", "beginner", "what is", "why do", "tips for",
                           "best way", "everything you need", "ultimate guide", "complete guide"],
    "Comparison":         ["vs", "versus", " or ", "compared", "comparison", "best.*202", "top.*202",
                           "review"],
    "FAQ":                ["faq", "frequently asked", "questions about", "common question"],
    "Glossary":           ["glossary", "terms", "definitions", "vocabulary", "terminology"],
}


def api_get(endpoint, params=None):
    """GET from WP REST API using curl subprocess."""
    url = f"{WP_URL}{endpoint}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  [WARN] curl error on {url}: {result.stderr[:200]}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [WARN] JSON decode error on {url}: {result.stdout[:200]}")
        return None


def api_post(endpoint, payload):
    """POST to WP REST API using curl subprocess with temp file for large bodies."""
    url = f"{WP_URL}{endpoint}"
    body_json = json.dumps(payload)
    # Write to temp file to handle large content safely
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp.write(body_json)
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmp_path}",
             url],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"  [WARN] curl POST error on {url}: {result.stderr[:200]}")
            return None
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"  [WARN] JSON decode error on POST {url}: {result.stdout[:300]}")
            return None
    finally:
        os.unlink(tmp_path)


def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    while True:
        print(f"  Fetching posts page {page}...")
        data = api_get("/posts", {
            "status": "publish",
            "per_page": "100",
            "page": str(page),
            "context": "edit"
        })
        if data is None or (isinstance(data, dict) and "code" in data):
            break
        if not isinstance(data, list) or len(data) == 0:
            break
        all_posts.extend(data)
        if len(data) < 100:
            break
        page += 1
        time.sleep(0.5)
    return all_posts


def classify_post(post):
    """Classify a post into a content cluster based on title + slug."""
    title = post.get("title", {})
    if isinstance(title, dict):
        title_text = title.get("rendered", title.get("raw", ""))
    else:
        title_text = str(title)
    slug = post.get("slug", "")
    combined = (title_text + " " + slug).lower()

    for cluster, keywords in CLUSTER_KEYWORDS.items():
        for kw in keywords:
            if kw in combined:
                return cluster

    # Fallback: try matching against content excerpt
    content = post.get("content", {})
    if isinstance(content, dict):
        content_text = content.get("rendered", content.get("raw", ""))
    else:
        content_text = str(content)
    content_lower = content_text[:1500].lower()

    for cluster, keywords in CLUSTER_KEYWORDS.items():
        for kw in keywords:
            if kw in content_lower:
                return cluster

    return "Uncategorized"


def extract_internal_links(html_content):
    """Extract all internal links (pethubonline.com) from HTML content."""
    links = []
    pattern = r'<a\s+[^>]*href=["\']([^"\']*pethubonline\.com[^"\']*)["\'][^>]*>'
    for match in re.finditer(pattern, html_content, re.IGNORECASE):
        url = match.group(1)
        # Normalize: remove trailing slash, query params, fragments
        parsed = urlparse(url)
        clean_path = parsed.path.rstrip("/")
        if clean_path:
            links.append(clean_path)
    return links


def build_url_to_post_map(posts):
    """Map URL paths to post data."""
    url_map = {}
    for p in posts:
        link = p.get("link", "")
        if link:
            parsed = urlparse(link)
            clean_path = parsed.path.rstrip("/")
            if clean_path:
                url_map[clean_path] = p
    return url_map


def get_post_content(post):
    """Get the rendered HTML content of a post."""
    content = post.get("content", {})
    if isinstance(content, dict):
        return content.get("rendered", content.get("raw", ""))
    return str(content)


def get_post_title(post):
    """Get the rendered title of a post."""
    title = post.get("title", {})
    if isinstance(title, dict):
        return title.get("rendered", title.get("raw", ""))
    return str(title)


def check_url_exists(url_path, url_map):
    """Check if a URL path exists in our post map."""
    clean = url_path.rstrip("/")
    return clean in url_map


def compute_text_similarity(text_a, text_b):
    """Simple word-overlap similarity score between two texts."""
    # Tokenize: lowercase, split on non-alpha
    words_a = set(re.findall(r'[a-z]{3,}', text_a.lower()))
    words_b = set(re.findall(r'[a-z]{3,}', text_b.lower()))
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    # Jaccard similarity
    union = words_a | words_b
    return len(intersection) / len(union) if union else 0.0


def insert_link_into_content(html_content, target_url, target_title):
    """
    Insert a contextual internal link paragraph at the end of the post content.
    Inserts before any trust blocks (<!-- trust -->) or at the very end.
    Only adds links, never removes existing content.
    """
    link_paragraph = (
        '\n<!-- wp:paragraph -->\n'
        f'<p>For related guidance, see our article on '
        f'<a href="{target_url}">{target_title}</a>.</p>\n'
        '<!-- /wp:paragraph -->\n'
    )

    # Check if the link already exists in the content
    if target_url in html_content:
        return html_content, False

    # Try to insert before trust blocks or closing sections
    trust_markers = ["<!-- trust", "<!-- /wp:group -->"]
    for marker in trust_markers:
        idx = html_content.rfind(marker)
        if idx > 0:
            return html_content[:idx] + link_paragraph + html_content[idx:], True

    # Otherwise append at the end
    return html_content + link_paragraph, True


def normalize_cluster_for_priority(cluster):
    """Normalize cluster name for priority matching."""
    return cluster.strip().lower()


def is_priority_pair(c1, c2):
    """Check if a cluster pair is a priority corridor."""
    n1 = normalize_cluster_for_priority(c1)
    n2 = normalize_cluster_for_priority(c2)
    for a, b in PRIORITY_CORRIDORS:
        na = normalize_cluster_for_priority(a)
        nb = normalize_cluster_for_priority(b)
        if (n1 == na and n2 == nb) or (n1 == nb and n2 == na):
            return True
    return False


def main():
    print("=" * 70)
    print("10AE-G: SEMANTIC CORRIDOR ENGINE")
    print(f"Target: pethubonline.com | Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)

    # ── Step 1: Fetch all posts ─────────────────────────────────────────
    print("\n[1/6] Fetching all published posts...")
    posts = fetch_all_posts()
    print(f"  Fetched {len(posts)} published posts.")

    if not posts:
        print("  ERROR: No posts fetched. Aborting.")
        sys.exit(1)

    # ── Step 2: Classify posts into clusters ────────────────────────────
    print("\n[2/6] Classifying posts into content clusters...")
    post_clusters = {}
    cluster_posts = defaultdict(list)
    for p in posts:
        pid = p["id"]
        cluster = classify_post(p)
        post_clusters[pid] = cluster
        cluster_posts[cluster].append(p)

    print("  Cluster distribution:")
    for cluster in sorted(cluster_posts.keys()):
        print(f"    {cluster}: {len(cluster_posts[cluster])} posts")

    # ── Step 3: Extract internal links and build corridor map ───────────
    print("\n[3/6] Extracting internal links and mapping corridors...")
    url_map = build_url_to_post_map(posts)
    post_by_id = {p["id"]: p for p in posts}

    # Track inbound links per post
    inbound_links = defaultdict(set)   # post_id -> set of source post_ids
    outbound_links = defaultdict(set)  # post_id -> set of target post_ids

    # Corridor map: (source_cluster, target_cluster) -> list of (source_id, target_id)
    corridor_links = defaultdict(list)

    for p in posts:
        pid = p["id"]
        content = get_post_content(p)
        internal_paths = extract_internal_links(content)

        for path in internal_paths:
            target_post = url_map.get(path)
            if target_post and target_post["id"] != pid:
                tid = target_post["id"]
                outbound_links[pid].add(tid)
                inbound_links[tid].add(pid)

                src_cluster = post_clusters[pid]
                tgt_cluster = post_clusters[tid]
                corridor_links[(src_cluster, tgt_cluster)].append((pid, tid))

    total_internal_links = sum(len(v) for v in outbound_links.values())
    print(f"  Total internal links found: {total_internal_links}")
    print(f"  Unique corridor pairs: {len(corridor_links)}")

    # ── Step 4: Identify orphans and weak corridors ─────────────────────
    print("\n[4/6] Identifying orphan pages and corridor gaps...")

    # Orphan pages (0 inbound links from other posts)
    orphan_posts = []
    for p in posts:
        pid = p["id"]
        if len(inbound_links[pid]) == 0:
            orphan_posts.append(p)

    orphan_posts.sort(key=lambda p: p["id"])
    print(f"  Orphan pages (0 inbound): {len(orphan_posts)}")
    for op in orphan_posts[:20]:
        print(f"    ID {op['id']}: {get_post_title(op)} [{post_clusters[op['id']]}]")

    # Build full corridor map with strength ratings
    all_clusters = sorted(set(post_clusters.values()))
    corridor_map_rows = []

    for i, c1 in enumerate(all_clusters):
        for c2 in all_clusters[i:]:
            if c1 == c2:
                continue
            # Count links in both directions
            fwd = corridor_links.get((c1, c2), [])
            rev = corridor_links.get((c2, c1), [])
            all_links = fwd + rev
            link_count = len(all_links)
            unique_sources = len(set(s for s, t in all_links))
            priority = is_priority_pair(c1, c2)

            if link_count == 0:
                strength = "Missing"
                status = "NEEDS_LINKS"
            elif link_count < 2:
                strength = "Weak"
                status = "NEEDS_REINFORCEMENT"
            elif link_count < 5:
                strength = "Moderate"
                status = "OK"
            else:
                strength = "Strong"
                status = "GOOD"

            if priority and status in ("NEEDS_LINKS", "NEEDS_REINFORCEMENT"):
                status = "PRIORITY_" + status

            corridor_map_rows.append({
                "source_cluster": c1,
                "target_cluster": c2,
                "link_count": link_count,
                "unique_posts": unique_sources,
                "corridor_strength": strength,
                "is_priority": "YES" if priority else "NO",
                "status": status,
            })

    # Sort: priority corridors first, then by link count ascending
    corridor_map_rows.sort(key=lambda r: (
        0 if r["is_priority"] == "YES" else 1,
        r["link_count"]
    ))

    weak_corridors = [r for r in corridor_map_rows if r["corridor_strength"] in ("Missing", "Weak")]
    print(f"  Weak/Missing corridors: {len(weak_corridors)}")
    for wc in weak_corridors[:10]:
        flag = " [PRIORITY]" if wc["is_priority"] == "YES" else ""
        print(f"    {wc['source_cluster']} <-> {wc['target_cluster']}: "
              f"{wc['link_count']} links ({wc['corridor_strength']}){flag}")

    # ── Step 5: Insert cross-cluster links for orphans ──────────────────
    print("\n[5/6] Inserting cross-cluster links for orphan pages...")

    insertion_log = []
    orphan_resolution_log = []
    links_inserted_count = 0
    orphans_fixed_count = 0

    for orphan in orphan_posts:
        oid = orphan["id"]
        orphan_title = get_post_title(orphan)
        orphan_cluster = post_clusters[oid]
        orphan_url = orphan.get("link", "")
        orphan_content_text = get_post_content(orphan)[:2000].lower()

        print(f"\n  Processing orphan ID {oid}: {orphan_title} [{orphan_cluster}]")

        # Find best candidate posts to link FROM (other posts that should link to this orphan)
        candidates = []
        for p in posts:
            pid = p["id"]
            if pid == oid:
                continue
            p_cluster = post_clusters[pid]
            # Prefer different clusters for cross-cluster linking, but also accept same cluster
            p_content = get_post_content(p)[:2000].lower()
            p_title_text = get_post_title(p).lower()

            # Compute relevance score
            similarity = compute_text_similarity(orphan_content_text, p_content)

            # Bonus for priority corridor matches
            priority_bonus = 0.15 if is_priority_pair(orphan_cluster, p_cluster) else 0.0

            # Bonus for cross-cluster (we want cross-cluster links)
            cross_bonus = 0.05 if p_cluster != orphan_cluster else 0.0

            # Penalty if post already has too many outbound links (> 10)
            outbound_penalty = 0.1 if len(outbound_links[pid]) > 10 else 0.0

            score = similarity + priority_bonus + cross_bonus - outbound_penalty

            # Check that orphan URL isn't already linked in this post
            if orphan_url and orphan_url in get_post_content(p):
                continue

            candidates.append((p, score, p_cluster))

        # Sort by score descending, take top 3-5
        candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = candidates[:4]  # 4 links per orphan

        orphan_fixed = False
        for candidate_post, score, cand_cluster in top_candidates:
            cid = candidate_post["id"]
            cand_title = get_post_title(candidate_post)

            if score < 0.02:
                print(f"    Skipping {cid} ({cand_title}): score too low ({score:.3f})")
                continue

            print(f"    Inserting link in post {cid} ({cand_title}) -> orphan {oid} (score: {score:.3f})")

            # Fetch fresh content for the candidate post
            fresh = api_get(f"/posts/{cid}", {"context": "edit"})
            if not fresh:
                print(f"    [WARN] Could not fetch fresh content for post {cid}")
                insertion_log.append({
                    "source_post_id": cid,
                    "source_title": cand_title,
                    "source_cluster": cand_cluster,
                    "target_post_id": oid,
                    "target_title": orphan_title,
                    "target_cluster": orphan_cluster,
                    "link_inserted": orphan_url,
                    "status": "FETCH_FAILED",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                continue

            fresh_content = fresh.get("content", {})
            if isinstance(fresh_content, dict):
                current_html = fresh_content.get("raw", fresh_content.get("rendered", ""))
            else:
                current_html = str(fresh_content)

            # Double check: link not already present
            if orphan_url and orphan_url in current_html:
                print(f"    Link already exists in post {cid}, skipping.")
                insertion_log.append({
                    "source_post_id": cid,
                    "source_title": cand_title,
                    "source_cluster": cand_cluster,
                    "target_post_id": oid,
                    "target_title": orphan_title,
                    "target_cluster": orphan_cluster,
                    "link_inserted": orphan_url,
                    "status": "ALREADY_EXISTS",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                continue

            # Insert the link
            updated_html, was_inserted = insert_link_into_content(
                current_html, orphan_url, orphan_title
            )

            if not was_inserted:
                insertion_log.append({
                    "source_post_id": cid,
                    "source_title": cand_title,
                    "source_cluster": cand_cluster,
                    "target_post_id": oid,
                    "target_title": orphan_title,
                    "target_cluster": orphan_cluster,
                    "link_inserted": orphan_url,
                    "status": "ALREADY_EXISTS",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                continue

            # Push update to WordPress
            update_result = api_post(f"/posts/{cid}", {"content": updated_html})
            time.sleep(0.8)

            if update_result and "id" in update_result:
                status = "INSERTED"
                links_inserted_count += 1
                orphan_fixed = True
                print(f"    SUCCESS: Link inserted in post {cid}")
            else:
                status = "UPDATE_FAILED"
                err_msg = ""
                if update_result:
                    err_msg = str(update_result)[:200]
                print(f"    FAILED: Could not update post {cid}: {err_msg}")

            insertion_log.append({
                "source_post_id": cid,
                "source_title": cand_title,
                "source_cluster": cand_cluster,
                "target_post_id": oid,
                "target_title": orphan_title,
                "target_cluster": orphan_cluster,
                "link_inserted": orphan_url,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            orphan_resolution_log.append({
                "orphan_post_id": oid,
                "orphan_title": orphan_title,
                "orphan_cluster": orphan_cluster,
                "linking_post_id": cid,
                "linking_post_title": cand_title,
                "link_added": orphan_url,
                "status": status,
            })

        if orphan_fixed:
            orphans_fixed_count += 1

    # ── Step 6: Also reinforce priority weak corridors ──────────────────
    print("\n[5b/6] Reinforcing priority weak corridors...")

    for corridor_row in corridor_map_rows:
        if corridor_row["is_priority"] != "YES":
            continue
        if corridor_row["corridor_strength"] not in ("Missing", "Weak"):
            continue

        c1 = corridor_row["source_cluster"]
        c2 = corridor_row["target_cluster"]
        print(f"\n  Reinforcing priority corridor: {c1} <-> {c2} (current: {corridor_row['link_count']} links)")

        posts_c1 = cluster_posts.get(c1, [])
        posts_c2 = cluster_posts.get(c2, [])

        if not posts_c1 or not posts_c2:
            print(f"    No posts in one/both clusters, skipping.")
            continue

        # Find best cross-link pairs
        pairs = []
        for p1 in posts_c1:
            for p2 in posts_c2:
                sim = compute_text_similarity(
                    get_post_content(p1)[:1500].lower(),
                    get_post_content(p2)[:1500].lower()
                )
                pairs.append((p1, p2, sim))

        pairs.sort(key=lambda x: x[2], reverse=True)

        inserted_for_corridor = 0
        max_for_corridor = 3  # Insert up to 3 links per weak priority corridor

        for p1, p2, sim in pairs:
            if inserted_for_corridor >= max_for_corridor:
                break
            if sim < 0.02:
                continue

            # Check if link already exists from p1 -> p2
            p1_content = get_post_content(p1)
            p2_url = p2.get("link", "")
            p2_title = get_post_title(p2)

            if p2_url in p1_content:
                continue

            # Already inserted in this run?
            already_done = any(
                r["source_post_id"] == p1["id"] and r["target_post_id"] == p2["id"]
                for r in insertion_log
            )
            if already_done:
                continue

            print(f"    Linking {p1['id']} ({get_post_title(p1)}) -> {p2['id']} ({p2_title}) [sim={sim:.3f}]")

            # Fetch fresh content
            fresh = api_get(f"/posts/{p1['id']}", {"context": "edit"})
            if not fresh:
                continue

            fresh_content = fresh.get("content", {})
            if isinstance(fresh_content, dict):
                current_html = fresh_content.get("raw", fresh_content.get("rendered", ""))
            else:
                current_html = str(fresh_content)

            if p2_url in current_html:
                continue

            updated_html, was_inserted = insert_link_into_content(current_html, p2_url, p2_title)
            if not was_inserted:
                continue

            update_result = api_post(f"/posts/{p1['id']}", {"content": updated_html})
            time.sleep(0.8)

            if update_result and "id" in update_result:
                status = "INSERTED"
                links_inserted_count += 1
                inserted_for_corridor += 1
                print(f"    SUCCESS: Corridor link inserted")
            else:
                status = "UPDATE_FAILED"
                print(f"    FAILED: Could not update post {p1['id']}")

            insertion_log.append({
                "source_post_id": p1["id"],
                "source_title": get_post_title(p1),
                "source_cluster": c1,
                "target_post_id": p2["id"],
                "target_title": p2_title,
                "target_cluster": c2,
                "link_inserted": p2_url,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    # ── Step 6: Write output CSVs ───────────────────────────────────────
    print("\n[6/6] Writing output CSVs...")

    # Corridor_Map.csv
    map_path = os.path.join(OUT_DIR, "Corridor_Map.csv")
    with open(map_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "source_cluster", "target_cluster", "link_count", "unique_posts",
            "corridor_strength", "is_priority", "status"
        ])
        w.writeheader()
        w.writerows(corridor_map_rows)
    print(f"  Written: {map_path} ({len(corridor_map_rows)} rows)")

    # Corridor_Insertion_Log.csv
    ins_path = os.path.join(OUT_DIR, "Corridor_Insertion_Log.csv")
    with open(ins_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "source_post_id", "source_title", "source_cluster",
            "target_post_id", "target_title", "target_cluster",
            "link_inserted", "status", "timestamp"
        ])
        w.writeheader()
        w.writerows(insertion_log)
    print(f"  Written: {ins_path} ({len(insertion_log)} rows)")

    # Orphan_Resolution_Log.csv
    orph_path = os.path.join(OUT_DIR, "Orphan_Resolution_Log.csv")
    with open(orph_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "orphan_post_id", "orphan_title", "orphan_cluster",
            "linking_post_id", "linking_post_title", "link_added", "status"
        ])
        w.writeheader()
        w.writerows(orphan_resolution_log)
    print(f"  Written: {orph_path} ({len(orphan_resolution_log)} rows)")

    # ── Summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SEMANTIC CORRIDOR ENGINE - SUMMARY")
    print("=" * 70)
    print(f"  Total posts analyzed:       {len(posts)}")
    print(f"  Content clusters:           {len(all_clusters)}")
    print(f"  Total internal links found: {total_internal_links}")
    print(f"  Corridor pairs mapped:      {len(corridor_map_rows)}")
    print(f"  Weak/Missing corridors:     {len(weak_corridors)}")
    print(f"  Priority corridors:         {sum(1 for r in corridor_map_rows if r['is_priority'] == 'YES')}")
    print(f"  Orphan pages found:         {len(orphan_posts)}")
    print(f"  Orphans fixed:              {orphans_fixed_count}")
    print(f"  Total links inserted:       {links_inserted_count}")
    print(f"  Insertion log entries:       {len(insertion_log)}")
    print("=" * 70)
    print("DONE.")


if __name__ == "__main__":
    main()
