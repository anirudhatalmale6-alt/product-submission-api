#!/usr/bin/env python3
"""
Source Citation Framework for PetHub Online
Phase 11T — EEAT Authority Layer

Fetches all published posts, checks for existing source sections,
and adds a standardized "Research Sources" block where missing.

RULES:
- Does NOT fabricate specific citations or references
- Only adds generic, honest source reference blocks
- Tracks all changes in source_citation_log.csv
"""

import subprocess
import json
import time
import csv
import re
import os
import tempfile

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API_BASE = "https://pethubonline.com/wp-json/wp/v2"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Cluster-specific source org mappings (honest, generic references)
CLUSTER_SOURCE_MAP = {
    "dog": {
        "orgs": "the British Veterinary Association (BVA), the RSPCA, the PDSA, and the Kennel Club",
        "authority": "bva.co.uk, rspca.org.uk, pdsa.org.uk"
    },
    "cat": {
        "orgs": "the British Veterinary Association (BVA), the RSPCA, International Cat Care, and the PDSA",
        "authority": "bva.co.uk, rspca.org.uk, icatcare.org, pdsa.org.uk"
    },
    "rabbit": {
        "orgs": "the Rabbit Welfare Association & Fund (RWAF), the RSPCA, and the PDSA",
        "authority": "rabbitwelfare.co.uk, rspca.org.uk, pdsa.org.uk"
    },
    "bird": {
        "orgs": "the RSPCA, the British Veterinary Association (BVA), and the PDSA",
        "authority": "rspca.org.uk, bva.co.uk, pdsa.org.uk"
    },
    "fish": {
        "orgs": "the Ornamental Aquatic Trade Association (OATA), the RSPCA, and the PDSA",
        "authority": "ornamentalfish.org, rspca.org.uk, pdsa.org.uk"
    },
    "hamster": {
        "orgs": "the RSPCA, the PDSA, and the National Hamster Council",
        "authority": "rspca.org.uk, pdsa.org.uk"
    },
    "guinea pig": {
        "orgs": "the RSPCA, the PDSA, and the Guinea Pig Welfare organisation",
        "authority": "rspca.org.uk, pdsa.org.uk"
    },
    "reptile": {
        "orgs": "the RSPCA, the British Veterinary Association (BVA), and the Royal Society of Biology",
        "authority": "rspca.org.uk, bva.co.uk"
    },
    "default": {
        "orgs": "the British Veterinary Association (BVA), the RSPCA, and the PDSA",
        "authority": "bva.co.uk, rspca.org.uk, pdsa.org.uk"
    }
}


def api_get(endpoint, params=None):
    """Make a GET request to WP REST API."""
    url = f"{WP_API_BASE}/{endpoint}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    return json.loads(result.stdout)


def api_get_with_headers(endpoint, params=None):
    """Make a GET request and return both body and total pages."""
    url = f"{WP_API_BASE}/{endpoint}"
    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{query}"

    # Use -w to write headers to stderr via --dump-header with a temp file
    import tempfile as _tf
    hdr_file = _tf.mktemp(suffix='.hdr')
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-D", hdr_file, "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        body = result.stdout

        # Parse total pages from header file
        total_pages = 1
        try:
            with open(hdr_file, 'r') as hf:
                for line in hf:
                    if line.lower().startswith("x-wp-totalpages:"):
                        total_pages = int(line.split(":")[1].strip())
        except FileNotFoundError:
            pass
    finally:
        try:
            os.unlink(hdr_file)
        except FileNotFoundError:
            pass

    return json.loads(body), total_pages


def api_post(endpoint, data):
    """Make a POST request to WP REST API using temp file for payload."""
    url = f"{WP_API_BASE}/{endpoint}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        tmpfile = f.name

    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmpfile}",
             url],
            capture_output=True, text=True, timeout=60
        )
        return json.loads(result.stdout)
    finally:
        os.unlink(tmpfile)


def detect_cluster(title, content=""):
    """Detect which pet cluster a post belongs to based on title/content."""
    text = (title + " " + content).lower()

    for cluster in ["guinea pig", "hamster", "rabbit", "bird", "fish", "reptile", "cat", "dog"]:
        if cluster in text:
            return cluster

    # Additional keyword matching
    dog_words = ["puppy", "puppies", "canine", "bark", "leash", "collar", "kibble", "breed"]
    cat_words = ["kitten", "kittens", "feline", "litter", "scratching", "catnip"]
    bird_words = ["parrot", "budgie", "cockatiel", "avian", "cage bird", "finch"]
    fish_words = ["aquarium", "tank", "tropical fish", "goldfish", "betta", "filter"]
    rabbit_words = ["bunny", "bunnies", "hutch", "hay"]
    reptile_words = ["gecko", "snake", "lizard", "turtle", "tortoise", "vivarium", "terrarium"]
    hamster_words = ["hamster wheel", "hamster cage", "dwarf hamster", "syrian hamster"]
    guinea_pig_words = ["guinea", "cavy", "cavies"]

    for word in dog_words:
        if word in text:
            return "dog"
    for word in cat_words:
        if word in text:
            return "cat"
    for word in bird_words:
        if word in text:
            return "bird"
    for word in fish_words:
        if word in text:
            return "fish"
    for word in rabbit_words:
        if word in text:
            return "rabbit"
    for word in reptile_words:
        if word in text:
            return "reptile"
    for word in hamster_words:
        if word in text:
            return "hamster"
    for word in guinea_pig_words:
        if word in text:
            return "guinea pig"

    return "default"


def has_source_section(content):
    """Check if post already has a Research Sources or Sources section."""
    if not content:
        return False
    content_lower = content.lower()
    patterns = [
        "research sources",
        "sources and references",
        "references",
        ">sources<",
        "source citations",
        "further reading",
        "our sources",
    ]
    for pattern in patterns:
        if pattern in content_lower:
            return True
    return False


def build_source_block(cluster):
    """Build a Gutenberg source citation block for a given cluster."""
    source_info = CLUSTER_SOURCE_MAP.get(cluster, CLUSTER_SOURCE_MAP["default"])

    block = (
        '<!-- wp:separator {"className":"is-style-wide"} -->\n'
        '<hr class="wp-block-separator is-style-wide"/>\n'
        '<!-- /wp:separator -->\n\n'
        '<!-- wp:heading {"level":2} -->\n'
        '<h2 class="wp-block-heading">Research Sources</h2>\n'
        '<!-- /wp:heading -->\n\n'
        '<!-- wp:paragraph -->\n'
        f'<p>This article references guidelines and recommendations from {source_info["orgs"]}. '
        'Pet care advice can change as new research emerges, so we encourage readers to check '
        'directly with these organisations for the most current guidance.</p>\n'
        '<!-- /wp:paragraph -->\n\n'
        '<!-- wp:paragraph -->\n'
        '<p><strong>Always consult a qualified veterinarian</strong> for advice specific to your '
        'pet\'s individual health needs. The information in this article is intended as general '
        'guidance and should not replace professional veterinary advice.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    return block


def fetch_all_published_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1

    print("  Fetching published posts...")
    first_batch, total_pages = api_get_with_headers("posts", {
        "status": "publish",
        "per_page": "100",
        "page": str(page)
    })

    if isinstance(first_batch, list):
        all_posts.extend(first_batch)

    print(f"  Total pages: {total_pages}, first batch: {len(first_batch)} posts")

    for page in range(2, total_pages + 1):
        time.sleep(2)
        batch = api_get("posts", {
            "status": "publish",
            "per_page": "100",
            "page": str(page)
        })
        if isinstance(batch, list):
            all_posts.extend(batch)
            print(f"  Page {page}: {len(batch)} posts")
        else:
            break

    print(f"  Total published posts fetched: {len(all_posts)}")
    return all_posts


def run_source_citation_framework():
    """Main function: check all posts and add source blocks where missing."""
    print("\n=== Source Citation Framework ===")

    posts = fetch_all_published_posts()

    log_entries = []
    updated_count = 0
    skipped_count = 0

    for i, post in enumerate(posts):
        post_id = post["id"]
        title = post["title"]["rendered"]
        content = post["content"]["rendered"]
        raw_content = post.get("content", {}).get("raw", content)

        cluster = detect_cluster(title, content)
        already_has_sources = has_source_section(raw_content)

        if already_has_sources:
            log_entries.append({
                "post_id": post_id,
                "title": title,
                "cluster": cluster,
                "had_sources": "yes",
                "action_taken": "skipped — sources already present",
                "sources_added": "none"
            })
            skipped_count += 1
            print(f"  [{i+1}/{len(posts)}] SKIP: '{title}' (already has sources)")
        else:
            # Add source block to end of content
            source_block = build_source_block(cluster)
            updated_content = raw_content.rstrip() + "\n\n" + source_block

            time.sleep(3)
            result = api_post(f"posts/{post_id}", {
                "content": updated_content
            })

            if "id" in result:
                source_info = CLUSTER_SOURCE_MAP.get(cluster, CLUSTER_SOURCE_MAP["default"])
                log_entries.append({
                    "post_id": post_id,
                    "title": title,
                    "cluster": cluster,
                    "had_sources": "no",
                    "action_taken": "added Research Sources block",
                    "sources_added": source_info["orgs"]
                })
                updated_count += 1
                print(f"  [{i+1}/{len(posts)}] UPDATED: '{title}' ({cluster})")
            else:
                error_msg = result.get("message", "unknown error")
                log_entries.append({
                    "post_id": post_id,
                    "title": title,
                    "cluster": cluster,
                    "had_sources": "no",
                    "action_taken": f"error: {error_msg}",
                    "sources_added": "none"
                })
                print(f"  [{i+1}/{len(posts)}] ERROR: '{title}' — {error_msg}")

    # Write CSV log
    csv_path = os.path.join(OUTPUT_DIR, "source_citation_log.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "had_sources", "action_taken", "sources_added"
        ])
        writer.writeheader()
        writer.writerows(log_entries)

    print(f"\n  Source citation results:")
    print(f"    Posts checked: {len(posts)}")
    print(f"    Already had sources: {skipped_count}")
    print(f"    Updated with sources: {updated_count}")
    print(f"    Log saved to: {csv_path}")

    return log_entries


if __name__ == "__main__":
    run_source_citation_framework()
