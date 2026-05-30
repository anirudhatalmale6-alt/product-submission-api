#!/usr/bin/env python3
"""
Phase 12A: Trust Link Reinforcement Engine
Scans all published posts and inserts missing trust editorial blocks
linking to methodology, editorial process, corrections, and disclosure pages.
"""
import json, os, re, subprocess, sys, tempfile, time, csv
from collections import defaultdict

WP_API = "https://pethubonline.com/wp-json/wp/v2/posts"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
SLEEP_GET = 2
SLEEP_POST = 3
MAX_RETRIES = 3
BACKOFF_BASE = 5

TRUST_PAGES = {
    "research": {
        "url": "https://pethubonline.com/how-we-research-pet-products/",
        "anchor": "research methodology",
        "check": "how-we-research-pet-products"
    },
    "editorial": {
        "url": "https://pethubonline.com/our-editorial-process/",
        "anchor": "editorial process",
        "check": "our-editorial-process"
    },
    "corrections": {
        "url": "https://pethubonline.com/corrections-and-updates-policy/",
        "anchor": "corrections and updates policy",
        "check": "corrections-and-updates-policy"
    },
    "disclosure": {
        "url": "https://pethubonline.com/affiliate-disclosure/",
        "anchor": "affiliate disclosure",
        "check": "affiliate-disclosure"
    },
}

TRUST_BLOCK = """<!-- wp:group {"style":{"border":{"width":"1px","color":"#e2e8f0","radius":"8px"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"}}},"backgroundColor":"white","className":"trust-editorial-block"} -->
<div class="wp-block-group trust-editorial-block has-border-color has-white-background-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:8px;padding-top:16px;padding-bottom:16px;padding-left:20px;padding-right:20px">
<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">Editorial Standards</h4>
<!-- /wp:heading -->

<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"}}} -->
<p class="wp-block-paragraph" style="font-size:14px">All content on Pet Hub Online is created following our <a href="https://pethubonline.com/how-we-research-pet-products/">research methodology</a> and <a href="https://pethubonline.com/our-editorial-process/">editorial process</a>. We are committed to accuracy and transparency — see our <a href="https://pethubonline.com/corrections-and-updates-policy/">corrections and updates policy</a> and <a href="https://pethubonline.com/affiliate-disclosure/">affiliate disclosure</a> for details.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->"""

CATEGORY_MAP = {
    1377: "Cat Supplies", 1459: "Cat Toys", 1413: "Indoor Cats",
    1376: "Dog Supplies", 1397: "Pet Care", 1401: "Dog Beds",
    1489: "Dog Care", 1467: "Dog Food", 1422: "Dog Harnesses",
    1450: "Dog Health", 1441: "Dog Toys", 1442: "Puppy Care",
    1474: "Training Supplies", 1: "Uncategorized"
}


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
        print(f"  Page {page}: {len(batch)} posts (total: {len(posts)})")
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


def check_trust_links(content):
    """Returns dict of which trust links are present."""
    content_lower = content.lower()
    return {
        key: info["check"] in content_lower
        for key, info in TRUST_PAGES.items()
    }


def get_cluster(categories):
    for cat_id in categories:
        if cat_id in CATEGORY_MAP:
            return CATEGORY_MAP[cat_id]
    return "Unknown"


def find_insertion_point(content):
    """Find the best place to insert the trust block.
    Priority: before comparison table, before FAQ, or at end.
    """
    # Before comparison table (Compared: section)
    compared_match = re.search(r'<!-- wp:heading[^>]*>\s*<h2[^>]*>Compared:', content)
    if compared_match:
        return compared_match.start()

    # Before Sources and References
    sources_match = re.search(r'<!-- wp:heading[^>]*>\s*<h2[^>]*>Sources and References', content)
    if sources_match:
        return sources_match.start()

    # Before Related Reading
    related_match = re.search(r'<!-- wp:heading[^>]*>\s*<h2[^>]*>Related Reading', content)
    if related_match:
        return related_match.start()

    # At the very end
    return len(content)


def main():
    print("=" * 70)
    print("Phase 12A: Trust Link Reinforcement Engine")
    print("=" * 70)

    print("\nFetching all published posts...")
    posts = fetch_all_posts()
    print(f"Total: {len(posts)} posts\n")

    # Audit all posts for trust link presence
    audit_results = []
    needs_insertion = []

    for p in posts:
        content = p.get("content", {}).get("raw", "")
        title_raw = p.get("title", {}).get("raw", p.get("title", {}).get("rendered", ""))
        categories = p.get("categories", [])
        cluster = get_cluster(categories)
        links = check_trust_links(content)
        has_trust_block = "trust-editorial-block" in content or "Editorial Standards</h4>" in content

        missing = [k for k, v in links.items() if not v]
        all_present = len(missing) == 0

        audit_results.append({
            "post_id": p["id"],
            "title": title_raw,
            "cluster": cluster,
            "has_research": links["research"],
            "has_editorial": links["editorial"],
            "has_corrections": links["corrections"],
            "has_disclosure": links["disclosure"],
            "has_trust_block": has_trust_block,
            "missing_count": len(missing),
            "missing_links": ", ".join(missing) if missing else "none"
        })

        if not has_trust_block and not all_present:
            needs_insertion.append({
                "id": p["id"],
                "title": title_raw,
                "cluster": cluster,
                "content": content,
                "missing": missing,
                "links": links
            })

    # Summary by cluster
    cluster_stats = defaultdict(lambda: {"total": 0, "complete": 0, "missing": 0})
    for r in audit_results:
        c = r["cluster"]
        cluster_stats[c]["total"] += 1
        if r["missing_count"] == 0 or r["has_trust_block"]:
            cluster_stats[c]["complete"] += 1
        else:
            cluster_stats[c]["missing"] += 1

    print("TRUST LINK COVERAGE BY CLUSTER:")
    print("-" * 60)
    for cluster, stats in sorted(cluster_stats.items()):
        pct = (stats["complete"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {cluster:20s}: {stats['complete']}/{stats['total']} ({pct:.0f}%) — {stats['missing']} need trust links")
    print()

    print(f"Posts needing trust block insertion: {len(needs_insertion)}\n")

    # Write audit CSV
    audit_path = "/var/lib/freelancer/projects/40416335/phase11_data/trust_link_audit_full.csv"
    with open(audit_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "has_research", "has_editorial",
            "has_corrections", "has_disclosure", "has_trust_block",
            "missing_count", "missing_links"
        ])
        writer.writeheader()
        writer.writerows(audit_results)
    print(f"  Wrote audit: {audit_path} ({len(audit_results)} rows)")

    if not needs_insertion:
        print("\nAll posts have trust links! Nothing to insert.")
        return

    # Insert trust blocks
    inserted = 0
    failed = 0
    log_rows = []

    for i, post in enumerate(needs_insertion):
        print(f"  [{i+1}/{len(needs_insertion)}] Inserting trust block in post {post['id']}: {post['title'][:55]}...")
        sys.stdout.flush()

        content = post["content"]
        insertion_point = find_insertion_point(content)
        new_content = content[:insertion_point] + "\n\n" + TRUST_BLOCK + "\n\n" + content[insertion_point:]

        success = update_post(post["id"], new_content)
        status = "inserted" if success else "failed"
        if success:
            inserted += 1
            print(f"    [OK] Trust block inserted")
        else:
            failed += 1
            print(f"    [FAIL] Update failed")

        log_rows.append({
            "post_id": post["id"],
            "title": post["title"],
            "cluster": post["cluster"],
            "missing_links": ", ".join(post["missing"]),
            "status": status,
            "insertion_point": "before_compared" if "Compared:" in content[insertion_point:insertion_point+50] else
                              "before_sources" if "Sources" in content[insertion_point:insertion_point+50] else
                              "before_related" if "Related" in content[insertion_point:insertion_point+50] else "end"
        })
        sys.stdout.flush()

    # Write insertion log
    log_path = "/var/lib/freelancer/projects/40416335/phase11_data/trust_reinforcement_log.csv"
    with open(log_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "missing_links", "status", "insertion_point"
        ])
        writer.writeheader()
        writer.writerows(log_rows)
    print(f"\n  Wrote log: {log_path} ({len(log_rows)} rows)")

    print(f"\n{'='*70}")
    print(f"TRUST REINFORCEMENT SUMMARY")
    print(f"{'='*70}")
    print(f"  Posts audited:     {len(audit_results)}")
    print(f"  Already complete:  {len(audit_results) - len(needs_insertion)}")
    print(f"  Blocks inserted:   {inserted}")
    print(f"  Insertions failed: {failed}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
