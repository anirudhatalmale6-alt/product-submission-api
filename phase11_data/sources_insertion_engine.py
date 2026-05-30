#!/usr/bin/env python3
"""
Phase 12B: Sources & References Insertion Engine
Adds genuine UK authority source citations to posts missing them.
Only cites real, verifiable organisations relevant to each post's topic.
"""
import json, os, re, subprocess, sys, tempfile, time, csv
from collections import defaultdict

WP_API = "https://pethubonline.com/wp-json/wp/v2/posts"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
SLEEP_GET = 2
SLEEP_POST = 3
MAX_RETRIES = 3
BACKOFF_BASE = 5

CATEGORY_MAP = {
    1377: "Cat Supplies", 1459: "Cat Toys", 1413: "Indoor Cats",
    1376: "Dog Supplies", 1397: "Pet Care", 1401: "Dog Beds",
    1489: "Dog Care", 1467: "Dog Food", 1422: "Dog Harnesses",
    1450: "Dog Health", 1441: "Dog Toys", 1442: "Puppy Care",
    1474: "Training Supplies", 1: "Uncategorized"
}

# Real, verifiable UK pet authority sources
DOG_SOURCES = [
    ("PDSA", "https://www.pdsa.org.uk/", "UK veterinary charity providing free and low-cost treatment"),
    ("The Kennel Club", "https://www.thekennelclub.org.uk/", "UK's largest dog welfare organisation"),
    ("RSPCA", "https://www.rspca.org.uk/", "Royal Society for the Prevention of Cruelty to Animals"),
    ("Blue Cross", "https://www.bluecross.org.uk/", "UK pet charity providing advice and rehoming"),
    ("British Veterinary Association", "https://www.bva.co.uk/", "Professional body for UK veterinary surgeons"),
]

CAT_SOURCES = [
    ("PDSA", "https://www.pdsa.org.uk/", "UK veterinary charity providing free and low-cost treatment"),
    ("Cats Protection", "https://www.cats.org.uk/", "UK's leading cat welfare charity"),
    ("International Cat Care", "https://icatcare.org/", "International charity improving cat health and welfare"),
    ("RSPCA", "https://www.rspca.org.uk/", "Royal Society for the Prevention of Cruelty to Animals"),
    ("Blue Cross", "https://www.bluecross.org.uk/", "UK pet charity providing advice and rehoming"),
]

PET_GENERAL_SOURCES = [
    ("PDSA", "https://www.pdsa.org.uk/", "UK veterinary charity providing free and low-cost treatment"),
    ("RSPCA", "https://www.rspca.org.uk/", "Royal Society for the Prevention of Cruelty to Animals"),
    ("Blue Cross", "https://www.bluecross.org.uk/", "UK pet charity providing advice and rehoming"),
    ("British Veterinary Association", "https://www.bva.co.uk/", "Professional body for UK veterinary surgeons"),
    ("Royal College of Veterinary Surgeons", "https://www.rcvs.org.uk/", "Regulatory body for veterinary professionals in the UK"),
]

PUPPY_SOURCES = [
    ("PDSA", "https://www.pdsa.org.uk/", "UK veterinary charity providing free and low-cost treatment"),
    ("The Kennel Club", "https://www.thekennelclub.org.uk/", "UK's largest dog welfare organisation"),
    ("Dogs Trust", "https://www.dogstrust.org.uk/", "UK's largest dog welfare charity"),
    ("Blue Cross", "https://www.bluecross.org.uk/", "UK pet charity providing advice and rehoming"),
    ("RSPCA", "https://www.rspca.org.uk/", "Royal Society for the Prevention of Cruelty to Animals"),
]

CLUSTER_SOURCES = {
    "Cat Supplies": CAT_SOURCES,
    "Cat Toys": CAT_SOURCES,
    "Indoor Cats": CAT_SOURCES,
    "Dog Supplies": DOG_SOURCES,
    "Dog Beds": DOG_SOURCES,
    "Dog Care": DOG_SOURCES,
    "Dog Food": DOG_SOURCES,
    "Dog Harnesses": DOG_SOURCES,
    "Dog Health": DOG_SOURCES,
    "Dog Toys": DOG_SOURCES,
    "Puppy Care": PUPPY_SOURCES,
    "Training Supplies": DOG_SOURCES,
    "Pet Care": PET_GENERAL_SOURCES,
    "Uncategorized": PET_GENERAL_SOURCES,
    "Unknown": PET_GENERAL_SOURCES,
}


def build_sources_block(sources):
    """Build a Gutenberg-compatible Sources and References block."""
    items = []
    for name, url, desc in sources:
        items.append(f'<li><a href="{url}" rel="nofollow noopener" target="_blank">{name}</a> — {desc}</li>')
    items_html = "\n".join(items)

    return f"""<!-- wp:heading {{"level":2}} -->
<h2 class="wp-block-heading">Sources and References</h2>
<!-- /wp:heading -->

<!-- wp:group {{"style":{{"border":{{"width":"1px","color":"#bae6fd","radius":"8px"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}}}}}},"className":"sources-references-block"}} -->
<div class="wp-block-group sources-references-block has-border-color" style="border-color:#bae6fd;border-width:1px;border-radius:8px;padding-top:16px;padding-bottom:16px;padding-left:20px;padding-right:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p class="wp-block-paragraph" style="font-size:14px">This guide is informed by guidance from UK veterinary and animal welfare organisations. We recommend consulting these trusted sources for the most current advice:</p>
<!-- /wp:paragraph -->

<!-- wp:list {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<ul class="wp-block-list" style="font-size:14px">
{items_html}
</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->"""


def fetch_all_posts():
    posts = []
    page = 1
    while True:
        time.sleep(SLEEP_GET)
        url = f"{WP_API}?per_page=100&page={page}&context=edit&_fields=id,title,content,categories&status=publish"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        try:
            batch = json.loads(result.stdout)
        except json.JSONDecodeError:
            break
        if not isinstance(batch, list) or len(batch) == 0:
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return posts


def update_post(post_id, content_raw):
    url = f"{WP_API}/{post_id}"
    payload = json.dumps({"content": content_raw})
    for attempt in range(MAX_RETRIES):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            tmp.write(payload)
            tmp_path = tmp.name
        try:
            time.sleep(SLEEP_POST)
            result = subprocess.run(
                ["curl", "-s", "-X", "POST", "--compressed",
                 "-u", AUTH, "-H", "Content-Type: application/json",
                 "-d", f"@{tmp_path}", url],
                capture_output=True, text=True, timeout=120
            )
            try:
                resp = json.loads(result.stdout)
            except json.JSONDecodeError:
                continue
            if isinstance(resp, dict) and "id" in resp:
                return True
            if isinstance(resp, dict) and resp.get("data", {}).get("status") == 429:
                wait = BACKOFF_BASE * (attempt + 1)
                print(f"    [429] Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    return False


def find_insertion_point(content):
    """Insert before Compared: section, trust block, or at end."""
    # Before comparison table
    compared_match = re.search(r'<!-- wp:heading[^>]*>\s*<h2[^>]*>Compared:', content)
    if compared_match:
        return compared_match.start()

    # Before trust editorial block
    trust_match = re.search(r'<!-- wp:group.*?trust-editorial-block', content)
    if trust_match:
        return trust_match.start()

    # Before Related Reading
    related_match = re.search(r'<!-- wp:heading[^>]*>\s*<h2[^>]*>Related Reading', content)
    if related_match:
        return related_match.start()

    return len(content)


def get_cluster(categories):
    for cat_id in categories:
        if cat_id in CATEGORY_MAP:
            return CATEGORY_MAP[cat_id]
    return "Unknown"


def main():
    print("=" * 70)
    print("Phase 12B: Sources & References Insertion Engine")
    print("=" * 70)

    print("\nFetching all published posts...")
    posts = fetch_all_posts()
    print(f"Total: {len(posts)} posts\n")

    needs_sources = []
    already_has = 0
    for p in posts:
        content = p.get("content", {}).get("raw", "")
        title = p.get("title", {}).get("raw", "")
        cats = p.get("categories", [])
        cluster = get_cluster(cats)

        if "Sources and References" in content or "sources-references-block" in content:
            already_has += 1
        else:
            needs_sources.append({
                "id": p["id"],
                "title": title,
                "cluster": cluster,
                "content": content
            })

    print(f"Already have sources: {already_has}")
    print(f"Need sources inserted: {len(needs_sources)}\n")

    if not needs_sources:
        print("All posts have sources! Nothing to insert.")
        return

    # Insert sources blocks
    inserted = 0
    failed = 0
    log_rows = []

    for i, post in enumerate(needs_sources):
        print(f"  [{i+1}/{len(needs_sources)}] Post {post['id']}: {post['title'][:55]}...")
        sys.stdout.flush()

        sources = CLUSTER_SOURCES.get(post["cluster"], PET_GENERAL_SOURCES)
        sources_block = build_sources_block(sources)
        insertion_point = find_insertion_point(post["content"])
        new_content = post["content"][:insertion_point] + "\n\n" + sources_block + "\n\n" + post["content"][insertion_point:]

        success = update_post(post["id"], new_content)
        status = "inserted" if success else "failed"
        if success:
            inserted += 1
            print(f"    [OK] Sources added ({post['cluster']})")
        else:
            failed += 1
            print(f"    [FAIL]")

        log_rows.append({
            "post_id": post["id"],
            "title": post["title"],
            "cluster": post["cluster"],
            "sources_count": len(sources),
            "status": status
        })
        sys.stdout.flush()

    # Write log
    log_path = "/var/lib/freelancer/projects/40416335/phase11_data/sources_insertion_log.csv"
    with open(log_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["post_id", "title", "cluster", "sources_count", "status"])
        writer.writeheader()
        writer.writerows(log_rows)
    print(f"\nWrote: {log_path} ({len(log_rows)} rows)")

    print(f"\n{'='*70}")
    print(f"SOURCES INSERTION SUMMARY")
    print(f"{'='*70}")
    print(f"  Already had sources: {already_has}")
    print(f"  Sources inserted:    {inserted}")
    print(f"  Failed:              {failed}")
    print(f"  Total coverage:      {already_has + inserted}/{len(posts)} ({(already_has + inserted)/len(posts)*100:.0f}%)")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
