#!/usr/bin/env python3
"""
Phase 10AG: Reinforce internal links for weak posts (only 1 incoming link).
For each weak post, find 2-3 source posts and insert a contextual link paragraph
BEFORE the Sources/Related Articles section in the source post.
"""

import csv
import json
import subprocess
import time
import re
import os
import tempfile

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
API_BASE = "https://pethubonline.com/wp-json/wp/v2"
LOG_PATH = "/var/lib/freelancer/projects/40416335/phase10ag_data/weak_post_reinforcement_log.csv"

# ── Weak posts ──────────────────────────────────────────────────────────
WEAK_POSTS = [
    (5950, "Dog Toy Durability Guide", "Dog Toys", "dog-toy-durability-guide"),
    (5935, "Dog Toy Storage and Organisation", "Dog Toys", "dog-toy-storage-organisation"),
    (5933, "Safe Tug Play with Dogs", "Dog Toys", "safe-tug-play-dogs"),
    (5930, "Dog Toy Safety by Breed Size", "Dog Toys", "dog-toy-safety-breed-size"),
    (5520, "Dog Health Basics", "Dog Health", "dog-health-basics-guide"),
    (5511, "Pet Enrichment Explained", "Dog Toys", "pet-enrichment-guide"),
    (5510, "Dog Bed Sizing Guide", "Dog Beds", "dog-bed-sizing-guide"),
    (5508, "Puppy Development Stages", "Puppy Care", "puppy-development-stages-guide"),
    (5467, "Pet Feeding Guide", "Dog Food", "pet-feeding-guide"),
    (5460, "Pet Nutrition Terminology", "Dog Food", "pet-nutrition-terminology-guide"),
    (5458, "Cat Scratching Behaviour", "Dog Training", "cat-scratching-behaviour-explained"),
    (5421, "Puppy-Safe Dog Toys", "Dog Toys", "puppy-safe-dog-toys"),
    (5419, "Cat Care Basics Glossary", "Educational", "cat-care-basics-glossary"),
    (5418, "Dog Harness Types", "Dog Harnesses", "dog-harness-types-glossary"),
    (5415, "Dog Play Styles Explained", "Educational", "dog-play-styles-explained"),
    (5414, "Cat Toy Types Glossary", "Educational", "cat-toy-types-glossary"),
    (5296, "Best Indoor Cat Toys", "Indoor Cats", "best-indoor-cat-toys"),
    (4064, "Best Dog Brushes", "Dog Grooming", "best-dog-brushes-uk"),
    (4011, "Best Cooling Dog Beds", "Dog Beds", "best-cooling-dog-beds-uk"),
    (4004, "Best Orthopaedic Dog Beds", "Dog Beds", "best-orthopaedic-dog-beds-uk"),
    (3960, "Best Puppy Toys", "Puppy Care", "best-puppy-toys-uk"),
    (3959, "Best Interactive Dog Toys", "Dog Toys", "best-interactive-dog-toys-uk"),
]

# ── Full inventory (id -> info) ─────────────────────────────────────────
INVENTORY = {}
with open("/var/lib/freelancer/projects/40416335/phase10af_data/post_authority_inventory.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        pid = int(row["id"])
        INVENTORY[pid] = {
            "id": pid,
            "title": row["title"],
            "cluster": row["cluster"],
        }

# Set of weak post IDs (don't use them as sources)
WEAK_IDS = {wp[0] for wp in WEAK_POSTS}

# ── Mapping: for each weak post, define source posts to link FROM ────────
# Strategy: pick 2-3 posts from same/related clusters that are NOT weak themselves
# Prefer hub pages, educational posts, and cross-cluster bridges

LINK_PLAN = {
    # Dog Toy Durability Guide (5950) - Dog Toys
    5950: [
        (5483, "dog toy lifespan and replacement"),       # Dog Toy Lifespan
        (5509, "toy materials and durability"),            # Pet Toy Safety
        (3957, "durable toys for heavy chewers"),         # Best Indestructible Dog Toys
    ],
    # Dog Toy Storage and Organisation (5935) - Dog Toys
    5935: [
        (5420, "keeping toys clean and organised"),       # Dog Toy Cleaning Guide
        (5469, "organising your toy rotation system"),    # Dog Toy Rotation
        (6046, "storing toys between cleaning sessions"), # Dog Toy Hygiene Schedules
    ],
    # Safe Tug Play with Dogs (5933) - Dog Toys
    5933: [
        (4789, "tug toys for different play styles"),     # Best Types of Dog Toys
        (5512, "understanding play signals during tug"),  # Dog Behaviour Explained
        (3956, "choosing safe tug toys"),                 # Best Dog Toys UK
    ],
    # Dog Toy Safety by Breed Size (5930) - Dog Toys
    5930: [
        (4787, "size-appropriate toy safety"),            # Dog Toy Safety
        (5509, "material safety by breed size"),          # Pet Toy Safety
        (5424, "safe toy sizing for power chewers"),      # Aggressive Chewer Guide
    ],
    # Dog Health Basics (5520) - Dog Health
    5520: [
        (4089, "common health conditions in dogs"),       # Best Dog Health and Care UK
        (4568, "health basics including dental care"),    # Dog Dental Health
        (5521, "understanding common health terms"),      # Pet Health Terminology
    ],
    # Pet Enrichment Explained (5511) - Dog Toys
    5511: [
        (5476, "enrichment through mental stimulation"),  # Mental Stimulation Toys
        (5471, "enrichment ideas for boredom prevention"),# Dog Boredom Prevention
        (4788, "enrichment beyond physical exercise"),    # Mental Stimulation for Dogs
    ],
    # Dog Bed Sizing Guide (5510) - Dog Beds
    5510: [
        (4783, "choosing the right bed size"),            # How to Choose the Right Dog Bed Size
        (3996, "finding the right fit for your dog"),     # Best Dog Beds UK
        (4784, "bed materials and sizing considerations"),# Dog Bed Materials Explained
    ],
    # Puppy Development Stages (5508) - Puppy Care
    5508: [
        (5417, "key puppy development milestones"),       # Puppy Care Essentials
        (4792, "socialisation during development stages"),# Puppy Socialisation
        (4132, "first year training by development stage"),# Best Puppy Training Guide
    ],
    # Pet Feeding Guide (5467) - Dog Food
    5467: [
        (3836, "understanding feeding portions and schedules"), # Best Dog Food UK
        (3838, "feeding methods for wet and dry food"),         # Dry vs Wet Dog Food
        (3839, "feeding schedules for growing puppies"),        # Best Puppy Food UK
    ],
    # Pet Nutrition Terminology (5460) - Dog Food
    5460: [
        (3837, "understanding nutrition labels"),         # Best Dry Dog Food UK
        (3836, "decoding pet food terminology"),          # Best Dog Food UK
        (5521, "nutrition-related health terminology"),   # Pet Health Terminology
    ],
    # Cat Scratching Behaviour (5458) - Dog Training
    5458: [
        (5519, "managing scratching behaviour indoors"),  # Indoor Cat Care
        (4286, "choosing the right scratching post"),     # Best Cat Scratching Posts
        (696, "essential scratching supplies for cats"),  # Essential Cat Supplies
    ],
    # Puppy-Safe Dog Toys (5421) - Dog Toys
    5421: [
        (4790, "safe homemade options for puppies"),      # DIY Dog Toys
        (4787, "toy safety basics for puppies"),          # Dog Toy Safety
        (5417, "choosing safe toys for your new puppy"),  # Puppy Care Essentials
    ],
    # Cat Care Basics Glossary (5419) - Educational
    5419: [
        (5519, "key cat care terms explained"),           # Indoor Cat Care
        (696, "understanding cat care essentials"),       # Essential Cat Supplies
        (4174, "cat care fundamentals for new owners"),   # Best Cat Toys UK
    ],
    # Dog Harness Types (5418) - Dog Harnesses
    5418: [
        (4411, "understanding different harness types"),  # Dog Harnesses Complete Guide
        (4414, "comparing harness types to collars"),     # Harness vs Collar
        (4027, "exploring harness options for your dog"), # Best Dog Collars and Harnesses
    ],
    # Dog Play Styles Explained (5415) - Educational
    5415: [
        (4789, "matching toys to your dog's play style"),  # Best Types of Dog Toys
        (5512, "understanding play body language"),         # Dog Behaviour Explained
        (5423, "enrichment play beyond basic fetch"),       # Dog Toy Enrichment
    ],
    # Cat Toy Types Glossary (5414) - Educational
    5414: [
        (4174, "understanding different cat toy types"),   # Best Cat Toys UK
        (5033, "choosing toys by type and personality"),   # How to Choose the Right Cat Toy
        (4181, "interactive toy types including wands"),   # Best Interactive Cat Toys UK
    ],
    # Best Indoor Cat Toys (5296) - Indoor Cats
    5296: [
        (4195, "top enrichment toys for indoor cats"),    # Best Cat Toys for Indoor Cats
        (4406, "interactive options for house cats"),      # Best Interactive Cat Toys for Indoor Cats
        (5519, "keeping indoor cats entertained"),         # Indoor Cat Care
    ],
    # Best Dog Brushes (4064) - Dog Grooming
    4064: [
        (4057, "choosing the right brush for your dog"),  # Best Dog Grooming Supplies
        (4563, "brushing as part of grooming basics"),    # Dog Grooming Basics
        (4071, "pairing the right brush with shampoo"),   # Best Dog Shampoo
    ],
    # Best Cooling Dog Beds (4011) - Dog Beds
    4011: [
        (3996, "cooling options in our dog bed guide"),    # Best Dog Beds UK
        (4784, "cooling materials for dog beds"),          # Dog Bed Materials Explained
        (5522, "temperature-regulating beds for joint care"),# Orthopaedic Care for Dogs
    ],
    # Best Orthopaedic Dog Beds (4004) - Dog Beds
    4004: [
        (3996, "orthopaedic options in our bed guide"),    # Best Dog Beds UK
        (5522, "orthopaedic beds for joint support"),      # Orthopaedic Care for Dogs
        (4110, "pairing orthopaedic beds with joint supplements"),# Best Dog Joint Supplements
    ],
    # Best Puppy Toys (3960) - Puppy Care
    3960: [
        (5417, "choosing first toys for your puppy"),     # Puppy Care Essentials
        (4792, "age-appropriate toys during socialisation"),# Puppy Socialisation
        (3956, "puppy-friendly options in our toy guide"),# Best Dog Toys UK
    ],
    # Best Interactive Dog Toys (3959) - Dog Toys
    3959: [
        (5476, "puzzle toys for mental stimulation"),     # Mental Stimulation Toys
        (5423, "interactive enrichment beyond basic fetch"),# Dog Toy Enrichment
        (3956, "interactive options in our complete guide"),# Best Dog Toys UK
    ],
}

# ── Natural lead-in templates (varied) ──────────────────────────────────
TEMPLATES = [
    'For more on {topic}, see our detailed guide to <a href="https://pethubonline.com/{slug}/">{title}</a>.',
    'If you want to learn more about {topic}, our <a href="https://pethubonline.com/{slug}/">{title}</a> guide covers this in depth.',
    'We also cover {topic} in our comprehensive <a href="https://pethubonline.com/{slug}/">{title}</a> article.',
    'For practical advice on {topic}, have a look at our <a href="https://pethubonline.com/{slug}/">{title}</a>.',
    'You may also find our <a href="https://pethubonline.com/{slug}/">{title}</a> helpful for understanding {topic}.',
    'Our <a href="https://pethubonline.com/{slug}/">{title}</a> explores {topic} in more detail.',
    'To go deeper into {topic}, see our guide: <a href="https://pethubonline.com/{slug}/">{title}</a>.',
]

template_counter = 0

def get_template(topic, slug, title):
    global template_counter
    tpl = TEMPLATES[template_counter % len(TEMPLATES)]
    template_counter += 1
    return tpl.format(topic=topic, slug=slug, title=title)


def api_get(endpoint):
    """GET from WP API using curl subprocess."""
    url = f"{API_BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"  CURL ERROR: {result.stderr}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  JSON DECODE ERROR for {url}: {result.stdout[:200]}")
        return None


def api_update_post(post_id, content):
    """Update post content via WP API using curl + temp file."""
    payload = json.dumps({"content": content})
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(payload)
        tmppath = f.name
    try:
        url = f"{API_BASE}/posts/{post_id}"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmppath}",
             url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  UPDATE CURL ERROR: {result.stderr}")
            return False
        resp = json.loads(result.stdout)
        if "id" in resp:
            return True
        else:
            print(f"  UPDATE FAILED: {json.dumps(resp)[:300]}")
            return False
    except Exception as e:
        print(f"  UPDATE EXCEPTION: {e}")
        return False
    finally:
        os.unlink(tmppath)


def find_insertion_point(content):
    """
    Find the best insertion point: before Sources/Related Articles/Editorial Standards.
    Returns index where we should insert, or -1 if appending to end.
    """
    # Look for common section markers (in Gutenberg block format)
    patterns = [
        r'<!-- wp:heading[^>]*>.*?Sources and Further Reading',
        r'<!-- wp:heading[^>]*>.*?Sources &amp; Further Reading',
        r'<!-- wp:heading[^>]*>.*?Our Editorial Standards',
        r'<!-- wp:heading[^>]*>.*?Related Articles',
        r'<!-- wp:heading[^>]*>.*?Further Reading',
        r'<!-- wp:heading[^>]*>.*?References',
    ]
    for pat in patterns:
        match = re.search(pat, content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.start()

    # Also try plain HTML headings
    patterns_plain = [
        r'<h[23][^>]*>.*?Sources and Further Reading',
        r'<h[23][^>]*>.*?Sources &amp; Further Reading',
        r'<h[23][^>]*>.*?Our Editorial Standards',
        r'<h[23][^>]*>.*?Related Articles',
        r'<h[23][^>]*>.*?Further Reading',
    ]
    for pat in patterns_plain:
        match = re.search(pat, content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.start()

    return -1


def slug_in_content(slug, content):
    """Check if a slug already appears in the content (link already exists)."""
    return slug in content


def build_link_paragraph(topic, slug, title):
    """Build a Gutenberg paragraph block with a contextual link."""
    sentence = get_template(topic, slug, title)
    return f'\n<!-- wp:paragraph -->\n<p>{sentence}</p>\n<!-- /wp:paragraph -->\n'


def main():
    log_rows = []
    total_inserted = 0
    total_skipped = 0
    total_errors = 0

    # Build a quick lookup for weak posts
    weak_lookup = {}
    for wp_id, wp_title, wp_cluster, wp_slug in WEAK_POSTS:
        weak_lookup[wp_id] = {
            "id": wp_id,
            "title": wp_title,
            "cluster": wp_cluster,
            "slug": wp_slug,
        }

    print(f"=== Phase 10AG: Weak Post Reinforcement ===")
    print(f"Weak posts: {len(WEAK_POSTS)}")
    print(f"Planned links: {sum(len(v) for v in LINK_PLAN.values())}")
    print()

    for wp_id, wp_title, wp_cluster, wp_slug in WEAK_POSTS:
        print(f"\n--- Weak Post {wp_id}: {wp_title} ({wp_cluster}) ---")
        sources = LINK_PLAN.get(wp_id, [])
        if not sources:
            print(f"  No source posts planned, skipping.")
            continue

        for src_id, topic_hint in sources:
            src_info = INVENTORY.get(src_id, {})
            src_title = src_info.get("title", f"Post {src_id}")
            print(f"  Source {src_id}: {src_title}")

            # Fetch source post content
            data = api_get(f"posts/{src_id}?_fields=id,content,title")
            time.sleep(0.5)

            if not data or "content" not in data:
                print(f"    ERROR: Could not fetch post {src_id}")
                log_rows.append([wp_id, wp_title, src_id, src_title, "", "error_fetch"])
                total_errors += 1
                continue

            content = data["content"]["rendered"]

            # Check if link already exists
            if slug_in_content(wp_slug, content):
                print(f"    SKIP: Link to {wp_slug} already exists in post {src_id}")
                log_rows.append([wp_id, wp_title, src_id, src_title, wp_slug, "already_exists"])
                total_skipped += 1
                continue

            # Build the link paragraph
            anchor_text = weak_lookup[wp_id]["title"]
            full_title_from_csv = None
            for row_wp in WEAK_POSTS:
                if row_wp[0] == wp_id:
                    # Use the full title from weak_posts.csv data
                    break

            # Get full title from inventory for display
            wp_inv = INVENTORY.get(wp_id, {})
            display_title = wp_inv.get("title", wp_title)

            paragraph = build_link_paragraph(topic_hint, wp_slug, display_title)

            # We need the RAW content to edit, not rendered. Fetch raw.
            raw_data = api_get(f"posts/{src_id}?_fields=id,content&context=edit")
            time.sleep(0.5)

            if not raw_data or "content" not in raw_data:
                print(f"    ERROR: Could not fetch raw content for post {src_id}")
                log_rows.append([wp_id, wp_title, src_id, src_title, "", "error_fetch_raw"])
                total_errors += 1
                continue

            raw_content = raw_data["content"]["raw"]

            # Check slug in raw content too
            if slug_in_content(wp_slug, raw_content):
                print(f"    SKIP: Link to {wp_slug} already exists in raw content of {src_id}")
                log_rows.append([wp_id, wp_title, src_id, src_title, wp_slug, "already_exists"])
                total_skipped += 1
                continue

            # Find insertion point
            ins_point = find_insertion_point(raw_content)

            if ins_point > 0:
                new_content = raw_content[:ins_point] + paragraph + "\n" + raw_content[ins_point:]
                print(f"    Inserting before Sources/Editorial section at pos {ins_point}")
            else:
                # Append before last closing block or at end
                new_content = raw_content + paragraph
                print(f"    Appending at end of content")

            # Update the post
            success = api_update_post(src_id, new_content)
            time.sleep(0.5)

            if success:
                print(f"    SUCCESS: Inserted link to {wp_slug} in post {src_id}")
                log_rows.append([wp_id, wp_title, src_id, src_title, display_title, "inserted"])
                total_inserted += 1
            else:
                print(f"    ERROR: Failed to update post {src_id}")
                log_rows.append([wp_id, wp_title, src_id, src_title, "", "error_update"])
                total_errors += 1

    # Write log CSV
    with open(LOG_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["weak_post_id", "weak_post_title", "source_post_id", "source_post_title", "anchor_text", "status"])
        writer.writerows(log_rows)

    print(f"\n=== SUMMARY ===")
    print(f"Total inserted: {total_inserted}")
    print(f"Total skipped (already exists): {total_skipped}")
    print(f"Total errors: {total_errors}")
    print(f"Log saved to: {LOG_PATH}")


if __name__ == "__main__":
    main()
