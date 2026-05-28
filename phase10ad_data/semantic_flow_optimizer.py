#!/usr/bin/env python3
"""
10AD-F: Semantic Flow Optimizer for pethubonline.com
Analyzes internal link graph and semantic reinforcement pathways across all posts.
"""

import subprocess
import json
import csv
import re
import os
import sys
from collections import defaultdict
from urllib.parse import urlparse, unquote

# === Configuration ===
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ad_data"
SITE_DOMAIN = "pethubonline.com"

# === Cluster Classification Keywords ===
CLUSTER_KEYWORDS = {
    "Dog Toys": ["dog toy", "dog toys", "chew toy", "fetch toy", "tug toy", "squeaky toy", "interactive dog toy", "durable dog toy", "plush dog toy", "rope toy"],
    "Dog Food": ["dog food", "puppy food", "dog diet", "dog nutrition", "dog treat", "dog treats", "raw dog food", "dry dog food", "wet dog food", "grain-free dog food", "dog feeding"],
    "Dog Beds": ["dog bed", "dog beds", "orthopedic dog bed", "dog crate pad", "dog mattress", "dog sleeping", "elevated dog bed", "calming dog bed"],
    "Dog Harnesses": ["dog harness", "dog harnesses", "no-pull harness", "dog leash", "dog collar", "dog walking", "dog lead", "front-clip harness"],
    "Dog Health": ["dog health", "dog vet", "dog vaccination", "dog flea", "dog tick", "dog dental", "dog grooming", "dog allergy", "dog supplement", "dog vitamin", "dog medicine", "dog illness", "dog disease"],
    "Dog Care": ["dog care", "dog training", "dog behavior", "dog exercise", "dog bath", "dog nail", "dog ear", "how to train", "dog obedience", "dog socialization"],
    "Cat Toys": ["cat toy", "cat toys", "catnip", "laser toy", "feather toy", "interactive cat toy", "cat wand", "cat puzzle"],
    "Cat Supplies": ["cat supplies", "cat food", "cat bed", "cat litter", "cat tree", "cat scratch", "cat carrier", "cat bowl", "cat treat", "cat health", "cat care", "cat grooming"],
    "Puppy Care": ["puppy care", "puppy training", "puppy food", "puppy toy", "new puppy", "puppy supplies", "puppy crate", "housebreaking", "puppy socialization", "puppy teething"],
    "Dog Supplies": ["dog supplies", "dog bowl", "dog crate", "dog gate", "dog pen", "dog carrier", "dog tag", "dog accessory", "dog water", "dog feeder"],
    "Pet Care General": ["pet care", "pet health", "pet insurance", "pet safety", "pet travel", "pet owner", "pet product", "pet supply", "pet tip", "best pet"],
    "Educational": ["guide", "how to", "what is", "why do", "tips for", "benefits of", "comparison", "vs", "review", "best", "top 10", "everything you need to know"],
}

# Trust/glossary/FAQ page indicators
TRUST_INDICATORS = ["editorial", "methodology", "corrections", "disclosure", "about", "privacy", "terms", "affiliate", "disclaimer", "policy"]
GLOSSARY_INDICATORS = ["glossary", "terminology", "definitions", "dictionary", "terms-explained", "pet-terms"]
FAQ_INDICATORS = ["faq", "frequently-asked", "questions", "q-and-a"]
COMPARISON_INDICATORS = ["vs", "versus", "comparison", "compared", "best", "top-10", "top-5", "review"]


def api_call(endpoint):
    """Make WordPress API call using curl subprocess."""
    url = f"{WP_BASE}{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  [WARN] curl error for {endpoint}: {result.stderr[:200]}")
        return None
    try:
        data = json.loads(result.stdout)
        if isinstance(data, dict) and data.get("code"):
            # WP error response
            return None
        return data
    except json.JSONDecodeError:
        return None


def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    while True:
        print(f"  Fetching posts page {page}...")
        data = api_call(f"/posts?status=publish&per_page=100&page={page}&context=edit")
        if not data or len(data) == 0:
            break
        all_posts.extend(data)
        if len(data) < 100:
            break
        page += 1
    print(f"  Total posts fetched: {len(all_posts)}")
    return all_posts


def classify_cluster(title, slug, content_text=""):
    """Classify a post into a cluster based on title, slug, and content."""
    combined = f"{title} {slug} {content_text[:500]}".lower()
    scores = {}
    for cluster, keywords in CLUSTER_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in combined:
                # Title matches count more
                if kw in title.lower():
                    score += 3
                elif kw in slug.lower():
                    score += 2
                else:
                    score += 1
        scores[cluster] = score

    if max(scores.values()) == 0:
        return "Pet Care General"

    return max(scores, key=scores.get)


def extract_internal_links(html_content):
    """Extract all internal links from HTML content."""
    links = []
    # Match href attributes containing the site domain
    pattern = r'<a\s[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>'
    matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)

    for url, anchor in matches:
        # Check if it's an internal link
        if SITE_DOMAIN in url or (url.startswith("/") and not url.startswith("//")):
            # Clean anchor text
            anchor_clean = re.sub(r'<[^>]+>', '', anchor).strip()
            # Normalize URL
            if url.startswith("/"):
                url = f"https://{SITE_DOMAIN}{url}"
            links.append({
                "url": url.rstrip("/").split("?")[0].split("#")[0],
                "anchor": anchor_clean[:200]
            })
    return links


def url_to_slug(url):
    """Extract slug from a URL."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    # Get the last path segment
    parts = path.split("/")
    return parts[-1] if parts and parts[-1] else path


def is_trust_page(slug, title):
    """Check if a URL/title indicates a trust page."""
    combined = f"{slug} {title}".lower()
    return any(ind in combined for ind in TRUST_INDICATORS)


def is_glossary_page(slug, title):
    """Check if a URL/title indicates a glossary page."""
    combined = f"{slug} {title}".lower()
    return any(ind in combined for ind in GLOSSARY_INDICATORS)


def is_faq_page(slug, title):
    """Check if a URL/title indicates an FAQ page."""
    combined = f"{slug} {title}".lower()
    return any(ind in combined for ind in FAQ_INDICATORS)


def is_comparison_page(slug, title):
    """Check if a URL/title indicates a comparison page."""
    combined = f"{slug} {title}".lower()
    return any(ind in combined for ind in COMPARISON_INDICATORS)


def has_faq_section(html_content):
    """Check if the post content contains an FAQ section."""
    lower = html_content.lower()
    faq_markers = [
        "frequently asked questions",
        "faq",
        '<div class="wp-block-yoast-faq',
        "schema.org/faqpage",
        '<h2>faq',
        '<h3>faq',
        "class=\"faq",
    ]
    return any(m in lower for m in faq_markers)


def strip_html(html):
    """Strip HTML tags for text analysis."""
    return re.sub(r'<[^>]+>', ' ', html)


def compute_semantic_flow_score(outbound, inbound, cross_cluster_out, cross_cluster_in, glossary, faq, trust):
    """Compute a 0-100 semantic flow score for a post."""
    score = 0
    # Outbound links (max 25 points)
    score += min(outbound * 5, 25)
    # Inbound links (max 30 points)
    score += min(inbound * 5, 30)
    # Cross-cluster outbound (max 15 points)
    score += min(cross_cluster_out * 5, 15)
    # Cross-cluster inbound (max 10 points)
    score += min(cross_cluster_in * 5, 10)
    # Glossary links (max 5 points)
    score += min(glossary * 5, 5)
    # FAQ links (max 5 points)
    score += min(faq * 5, 5)
    # Trust links (max 10 points)
    score += min(trust * 5, 10)
    return min(score, 100)


def main():
    print("=" * 70)
    print("10AD-F: SEMANTIC FLOW OPTIMIZER")
    print("pethubonline.com - Internal Link Graph & Semantic Pathway Analysis")
    print("=" * 70)
    print()

    # --- Step 1: Fetch all posts ---
    print("[1/6] Fetching all published posts...")
    posts = fetch_all_posts()
    if not posts:
        print("ERROR: No posts fetched. Check API credentials and connectivity.")
        sys.exit(1)

    # --- Step 2: Build post index ---
    print(f"\n[2/6] Building post index and classifying clusters...")
    post_index = {}  # id -> post data
    url_to_id = {}   # normalized url -> post id
    slug_to_id = {}  # slug -> post id

    for p in posts:
        pid = p["id"]
        title = p.get("title", {}).get("rendered", "") or p.get("title", {}).get("raw", "")
        slug = p.get("slug", "")
        link = p.get("link", "").rstrip("/").split("?")[0].split("#")[0]
        content = p.get("content", {}).get("rendered", "") or p.get("content", {}).get("raw", "")
        content_text = strip_html(content)

        cluster = classify_cluster(title, slug, content_text)

        post_index[pid] = {
            "id": pid,
            "title": title,
            "slug": slug,
            "link": link,
            "cluster": cluster,
            "content": content,
            "content_text": content_text,
            "has_faq": has_faq_section(content),
            "is_trust": is_trust_page(slug, title),
            "is_glossary": is_glossary_page(slug, title),
            "is_comparison": is_comparison_page(slug, title),
        }

        if link:
            url_to_id[link] = pid
            # Also map with and without www
            alt = link.replace("://www.", "://") if "://www." in link else link.replace("://", "://www.")
            url_to_id[alt] = pid

        if slug:
            slug_to_id[slug] = pid

    # Print cluster distribution
    cluster_counts = defaultdict(int)
    for p in post_index.values():
        cluster_counts[p["cluster"]] += 1
    print("  Cluster distribution:")
    for c in sorted(cluster_counts.keys()):
        print(f"    {c}: {cluster_counts[c]} posts")

    # --- Step 3: Extract internal links and build graph ---
    print(f"\n[3/6] Extracting internal links and building directed graph...")
    outbound_links = defaultdict(list)   # pid -> [{"target_id", "url", "anchor"}]
    inbound_links = defaultdict(list)    # pid -> [{"source_id", "url", "anchor"}]
    total_internal_links = 0

    for pid, pdata in post_index.items():
        links = extract_internal_links(pdata["content"])
        seen_targets = set()
        for link in links:
            url_norm = link["url"].rstrip("/")
            target_id = url_to_id.get(url_norm)

            # Try slug matching if URL match fails
            if target_id is None:
                link_slug = url_to_slug(url_norm)
                target_id = slug_to_id.get(link_slug)

            if target_id and target_id != pid and target_id not in seen_targets:
                outbound_links[pid].append({
                    "target_id": target_id,
                    "url": link["url"],
                    "anchor": link["anchor"]
                })
                inbound_links[target_id].append({
                    "source_id": pid,
                    "url": link["url"],
                    "anchor": link["anchor"]
                })
                seen_targets.add(target_id)
                total_internal_links += 1

    print(f"  Total unique internal links found: {total_internal_links}")

    # --- Step 4: Analyze reinforcement pathways ---
    print(f"\n[4/6] Analyzing reinforcement pathways...")

    # Glossary reinforcement
    glossary_links_per_post = defaultdict(int)
    for pid in post_index:
        for link in outbound_links.get(pid, []):
            tid = link["target_id"]
            if tid in post_index and post_index[tid]["is_glossary"]:
                glossary_links_per_post[pid] += 1

    # FAQ reinforcement
    faq_links_per_post = defaultdict(int)
    for pid in post_index:
        if post_index[pid]["has_faq"]:
            for link in outbound_links.get(pid, []):
                tid = link["target_id"]
                if tid in post_index and post_index[tid]["has_faq"]:
                    faq_links_per_post[pid] += 1

    # Trust reinforcement
    trust_links_per_post = defaultdict(int)
    for pid in post_index:
        for link in outbound_links.get(pid, []):
            tid = link["target_id"]
            if tid in post_index and post_index[tid]["is_trust"]:
                trust_links_per_post[pid] += 1

    # Comparison reinforcement
    comparison_links_per_post = defaultdict(int)
    for pid in post_index:
        if post_index[pid]["is_comparison"]:
            for link in outbound_links.get(pid, []):
                tid = link["target_id"]
                if tid in post_index and post_index[tid]["is_comparison"]:
                    comparison_links_per_post[pid] += 1

    glossary_count = sum(1 for v in glossary_links_per_post.values() if v > 0)
    faq_count = sum(1 for v in faq_links_per_post.values() if v > 0)
    trust_count = sum(1 for v in trust_links_per_post.values() if v > 0)
    print(f"  Posts with glossary links: {glossary_count}")
    print(f"  Posts with FAQ cross-links: {faq_count}")
    print(f"  Posts with trust links: {trust_count}")

    # --- Step 5: Cross-cluster analysis ---
    print(f"\n[5/6] Analyzing cross-cluster flow...")
    cross_cluster_matrix = defaultdict(lambda: {"link_count": 0, "unique_posts": set()})

    for pid in post_index:
        src_cluster = post_index[pid]["cluster"]
        for link in outbound_links.get(pid, []):
            tid = link["target_id"]
            if tid in post_index:
                tgt_cluster = post_index[tid]["cluster"]
                key = (src_cluster, tgt_cluster)
                cross_cluster_matrix[key]["link_count"] += 1
                cross_cluster_matrix[key]["unique_posts"].add(pid)

    # Compute outbound/inbound cross-cluster counts per post
    cross_cluster_out = defaultdict(int)
    cross_cluster_in = defaultdict(int)
    for pid in post_index:
        src_cluster = post_index[pid]["cluster"]
        for link in outbound_links.get(pid, []):
            tid = link["target_id"]
            if tid in post_index and post_index[tid]["cluster"] != src_cluster:
                cross_cluster_out[pid] += 1
        for link in inbound_links.get(pid, []):
            sid = link["source_id"]
            if sid in post_index and post_index[sid]["cluster"] != src_cluster:
                cross_cluster_in[pid] += 1

    # --- Step 6: Write CSVs ---
    print(f"\n[6/6] Writing output CSVs...")

    # CSV 1: Semantic_Flow_Graph.csv
    csv1_path = os.path.join(OUTPUT_DIR, "Semantic_Flow_Graph.csv")
    with open(csv1_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "post_id", "title", "cluster", "outbound_links", "inbound_links",
            "outbound_clusters", "inbound_clusters", "glossary_links", "faq_links",
            "trust_links", "semantic_flow_score"
        ])
        for pid in sorted(post_index.keys()):
            p = post_index[pid]
            ob = len(outbound_links.get(pid, []))
            ib = len(inbound_links.get(pid, []))

            # Outbound clusters
            ob_clusters = set()
            for link in outbound_links.get(pid, []):
                tid = link["target_id"]
                if tid in post_index:
                    ob_clusters.add(post_index[tid]["cluster"])
            # Inbound clusters
            ib_clusters = set()
            for link in inbound_links.get(pid, []):
                sid = link["source_id"]
                if sid in post_index:
                    ib_clusters.add(post_index[sid]["cluster"])

            gl = glossary_links_per_post.get(pid, 0)
            fl = faq_links_per_post.get(pid, 0)
            tl = trust_links_per_post.get(pid, 0)

            score = compute_semantic_flow_score(
                ob, ib, cross_cluster_out.get(pid, 0),
                cross_cluster_in.get(pid, 0), gl, fl, tl
            )

            writer.writerow([
                pid, p["title"], p["cluster"], ob, ib,
                "; ".join(sorted(ob_clusters)) if ob_clusters else "none",
                "; ".join(sorted(ib_clusters)) if ib_clusters else "none",
                gl, fl, tl, score
            ])
    print(f"  Written: {csv1_path}")

    # CSV 2: Semantic_Isolation_Zones.csv
    csv2_path = os.path.join(OUTPUT_DIR, "Semantic_Isolation_Zones.csv")
    with open(csv2_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "post_id", "title", "cluster", "inbound_links", "outbound_links",
            "isolation_severity", "recommended_link_sources"
        ])

        # Find posts with few inbound links
        for pid in sorted(post_index.keys()):
            p = post_index[pid]
            ib = len(inbound_links.get(pid, []))
            ob = len(outbound_links.get(pid, []))

            if ib < 3:  # Threshold for isolation
                if ib == 0:
                    severity = "critical"
                elif ib == 1:
                    severity = "moderate"
                else:
                    severity = "minor"

                # Recommend link sources: posts in same cluster with most outbound links
                same_cluster = [
                    (oid, len(outbound_links.get(oid, [])))
                    for oid, op in post_index.items()
                    if op["cluster"] == p["cluster"] and oid != pid
                ]
                same_cluster.sort(key=lambda x: x[1], reverse=True)
                recommended = [
                    f"{post_index[oid]['title'][:50]} (ID:{oid})"
                    for oid, _ in same_cluster[:5]
                ]

                writer.writerow([
                    pid, p["title"], p["cluster"], ib, ob, severity,
                    "; ".join(recommended) if recommended else "no same-cluster posts"
                ])
    print(f"  Written: {csv2_path}")

    # CSV 3: Cross_Cluster_Flow.csv
    csv3_path = os.path.join(OUTPUT_DIR, "Cross_Cluster_Flow.csv")
    all_clusters = sorted(cluster_counts.keys())

    # Determine flow strengths
    all_counts = [v["link_count"] for v in cross_cluster_matrix.values() if v["link_count"] > 0]
    if all_counts:
        median_count = sorted(all_counts)[len(all_counts) // 2]
    else:
        median_count = 1

    with open(csv3_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "source_cluster", "target_cluster", "link_count", "unique_posts_linking",
            "flow_strength", "is_weak_corridor"
        ])
        for src in all_clusters:
            for tgt in all_clusters:
                key = (src, tgt)
                data = cross_cluster_matrix.get(key, {"link_count": 0, "unique_posts": set()})
                lc = data["link_count"]
                up = len(data["unique_posts"])

                if lc == 0:
                    strength = "none"
                    is_weak = "yes" if src != tgt else ""
                elif lc <= max(1, median_count // 2):
                    strength = "weak"
                    is_weak = "yes"
                elif lc <= median_count * 2:
                    strength = "moderate"
                    is_weak = "no"
                else:
                    strength = "strong"
                    is_weak = "no"

                if src == tgt:
                    is_weak = ""  # intra-cluster, not a corridor

                writer.writerow([src, tgt, lc, up, strength, is_weak])
    print(f"  Written: {csv3_path}")

    # ===== SUMMARY =====
    print()
    print("=" * 70)
    print("SEMANTIC FLOW ANALYSIS SUMMARY")
    print("=" * 70)

    print(f"\nTotal posts analyzed: {len(post_index)}")
    print(f"Total unique internal links: {total_internal_links}")

    # Orphan pages (0 inbound)
    orphans = [pid for pid in post_index if len(inbound_links.get(pid, [])) == 0]
    print(f"\nOrphan pages (0 inbound links): {len(orphans)}")
    for pid in orphans[:15]:
        p = post_index[pid]
        print(f"  - [{p['cluster']}] {p['title'][:70]} (ID:{pid})")
    if len(orphans) > 15:
        print(f"  ... and {len(orphans) - 15} more")

    # Weak pages (<3 inbound)
    weak = [pid for pid in post_index if 0 < len(inbound_links.get(pid, [])) < 3]
    print(f"\nWeak pages (1-2 inbound links): {len(weak)}")
    for pid in sorted(weak, key=lambda x: len(inbound_links.get(x, [])))[:10]:
        p = post_index[pid]
        ib = len(inbound_links.get(pid, []))
        print(f"  - [{p['cluster']}] {p['title'][:60]} (ID:{pid}, inbound:{ib})")
    if len(weak) > 10:
        print(f"  ... and {len(weak) - 10} more")

    # Strongest corridors (cross-cluster, excluding self-links)
    corridors = [
        (k, v) for k, v in cross_cluster_matrix.items()
        if k[0] != k[1] and v["link_count"] > 0
    ]
    corridors.sort(key=lambda x: x[1]["link_count"], reverse=True)

    print(f"\nStrongest cross-cluster corridors:")
    for (src, tgt), data in corridors[:10]:
        print(f"  {src} -> {tgt}: {data['link_count']} links ({len(data['unique_posts'])} unique posts)")

    # Weakest corridors (non-zero but low)
    weak_corridors = [
        (k, v) for k, v in cross_cluster_matrix.items()
        if k[0] != k[1] and v["link_count"] > 0
    ]
    weak_corridors.sort(key=lambda x: x[1]["link_count"])
    print(f"\nWeakest cross-cluster corridors (non-zero):")
    for (src, tgt), data in weak_corridors[:10]:
        print(f"  {src} -> {tgt}: {data['link_count']} links ({len(data['unique_posts'])} unique posts)")

    # Missing corridors (zero links between clusters that both have posts)
    missing = []
    for src in all_clusters:
        for tgt in all_clusters:
            if src != tgt:
                key = (src, tgt)
                if key not in cross_cluster_matrix or cross_cluster_matrix[key]["link_count"] == 0:
                    if cluster_counts.get(src, 0) > 0 and cluster_counts.get(tgt, 0) > 0:
                        missing.append((src, tgt))
    print(f"\nMissing corridors (0 links between active clusters): {len(missing)}")
    for src, tgt in missing[:15]:
        print(f"  {src} -> {tgt}")
    if len(missing) > 15:
        print(f"  ... and {len(missing) - 15} more")

    # Cluster flow matrix
    print(f"\nCluster Flow Matrix (link counts):")
    # Header
    short = {c: c[:8] for c in all_clusters}
    header = f"{'Source':<20}" + "".join(f"{short[c]:>10}" for c in all_clusters)
    print(header)
    print("-" * len(header))
    for src in all_clusters:
        row = f"{src:<20}"
        for tgt in all_clusters:
            key = (src, tgt)
            count = cross_cluster_matrix.get(key, {"link_count": 0})["link_count"]
            row += f"{count:>10}"
        print(row)

    # Top semantic isolation zones by severity
    isolation_critical = [pid for pid in post_index if len(inbound_links.get(pid, [])) == 0]
    isolation_moderate = [pid for pid in post_index if len(inbound_links.get(pid, [])) == 1]
    print(f"\nSemantic Isolation Zones:")
    print(f"  Critical (0 inbound): {len(isolation_critical)} posts")
    print(f"  Moderate (1 inbound): {len(isolation_moderate)} posts")
    print(f"  Minor (2 inbound): {len([pid for pid in post_index if len(inbound_links.get(pid, [])) == 2])} posts")

    # Reinforcement pathway summary
    print(f"\nReinforcement Pathway Summary:")
    print(f"  Glossary pathways: {glossary_count} posts link to glossary content")
    print(f"  FAQ cross-links: {faq_count} FAQ posts cross-link to other FAQ posts")
    print(f"  Trust pathways: {trust_count} posts link to trust/editorial pages")
    comparison_count = sum(1 for v in comparison_links_per_post.values() if v > 0)
    print(f"  Comparison pathways: {comparison_count} comparison posts cross-link")

    # Top connected posts
    print(f"\nTop 10 most connected posts (by total links):")
    connected = [
        (pid, len(outbound_links.get(pid, [])) + len(inbound_links.get(pid, [])))
        for pid in post_index
    ]
    connected.sort(key=lambda x: x[1], reverse=True)
    for pid, total in connected[:10]:
        p = post_index[pid]
        ob = len(outbound_links.get(pid, []))
        ib = len(inbound_links.get(pid, []))
        print(f"  [{p['cluster']}] {p['title'][:55]} (ID:{pid}) - out:{ob} in:{ib} total:{total}")

    # Average flow score by cluster
    print(f"\nAverage Semantic Flow Score by Cluster:")
    cluster_scores = defaultdict(list)
    for pid in post_index:
        p = post_index[pid]
        ob = len(outbound_links.get(pid, []))
        ib = len(inbound_links.get(pid, []))
        gl = glossary_links_per_post.get(pid, 0)
        fl = faq_links_per_post.get(pid, 0)
        tl = trust_links_per_post.get(pid, 0)
        score = compute_semantic_flow_score(
            ob, ib, cross_cluster_out.get(pid, 0),
            cross_cluster_in.get(pid, 0), gl, fl, tl
        )
        cluster_scores[p["cluster"]].append(score)

    for c in sorted(cluster_scores.keys()):
        scores = cluster_scores[c]
        avg = sum(scores) / len(scores) if scores else 0
        print(f"  {c}: {avg:.1f}/100 ({len(scores)} posts)")

    print(f"\nOutput files:")
    print(f"  {csv1_path}")
    print(f"  {csv2_path}")
    print(f"  {csv3_path}")
    print(f"\n{'=' * 70}")
    print("10AD-F: Semantic Flow Optimizer COMPLETE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
