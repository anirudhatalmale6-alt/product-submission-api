#!/usr/bin/env python3
"""Phase 22B: CTR Optimization
Adds/improves Yoast meta descriptions for posts missing them.
Better meta descriptions = better CTR from search results."""

import requests, json, time, re, html as html_mod
from datetime import datetime

WP = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
HEADERS = {"Accept-Encoding": "gzip, deflate"}


def fetch_all_published():
    posts = []
    page = 1
    while True:
        r = requests.get(f"{WP}/posts", params={
            "status": "publish", "per_page": 100, "page": page,
            "_fields": "id,title,excerpt,content,yoast_head_json,link"
        }, auth=AUTH, headers=HEADERS)
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        posts.extend(batch)
        page += 1
        time.sleep(0.5)
    return posts


def strip_html(text):
    clean = re.sub(r'<[^>]+>', '', text)
    clean = html_mod.unescape(clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def extract_first_paragraph(content):
    rendered = content.get("rendered", "") if isinstance(content, dict) else str(content)
    paras = re.findall(r'<p[^>]*>(.*?)</p>', rendered, re.DOTALL)
    for p in paras:
        text = strip_html(p)
        if len(text) > 40 and not text.startswith("Table of") and "affiliate" not in text.lower():
            return text
    return ""


def generate_meta_description(title, first_para):
    title_clean = strip_html(title)
    if first_para and len(first_para) > 60:
        desc = first_para[:155]
        last_space = desc.rfind(' ')
        if last_space > 100:
            desc = desc[:last_space]
        if not desc.endswith('.'):
            desc += '.'
        return desc
    desc = f"Learn about {title_clean.lower()}. Expert UK guide with practical tips, recommended products, and FAQs."
    if len(desc) > 160:
        desc = desc[:157] + "..."
    return desc


def has_meta_description(post):
    yoast = post.get("yoast_head_json", {})
    if not yoast:
        return False, ""
    og_desc = yoast.get("og_description", "")
    desc = yoast.get("description", "")
    meta = desc or og_desc
    if not meta or len(meta) < 30:
        return False, meta
    return True, meta


def update_meta(post_id, meta_desc):
    for attempt in range(3):
        r = requests.post(f"{WP}/posts/{post_id}",
            json={"meta": {"_yoast_wpseo_metadesc": meta_desc}},
            auth=AUTH, headers=HEADERS)
        if r.status_code == 200:
            return True
        if r.status_code == 429:
            time.sleep(10)
            continue
        r2 = requests.post(f"{WP}/posts/{post_id}",
            json={"excerpt": meta_desc},
            auth=AUTH, headers=HEADERS)
        if r2.status_code == 200:
            return True
        print(f"    Error updating {post_id}: {r.status_code}")
        return False
    return False


def main():
    print("=" * 60)
    print("PHASE 22B: CTR OPTIMIZATION - META DESCRIPTION AUDIT")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    print("\nFetching all published posts...")
    posts = fetch_all_published()
    print(f"  Total published: {len(posts)}")

    missing = []
    has_meta = 0
    short_meta = 0

    for post in posts:
        has_it, current = has_meta_description(post)
        if not has_it:
            missing.append(post)
        elif len(current) < 80:
            short_meta += 1
            missing.append(post)
        else:
            has_meta += 1

    print(f"  Have good meta description: {has_meta}")
    print(f"  Missing or too short: {len(missing)}")

    results = {
        "phase": "22B",
        "timestamp": datetime.now().isoformat(),
        "total_posts": len(posts),
        "already_good": has_meta,
        "missing_or_short": len(missing),
        "updated": 0,
        "errors": 0,
        "samples": [],
    }

    for i, post in enumerate(missing):
        pid = post["id"]
        title = post["title"]["rendered"] if isinstance(post["title"], dict) else post["title"]
        first_para = extract_first_paragraph(post.get("content", ""))
        meta_desc = generate_meta_description(title, first_para)

        if update_meta(pid, meta_desc):
            results["updated"] += 1
            if len(results["samples"]) < 20:
                results["samples"].append({
                    "id": pid,
                    "title": strip_html(title)[:60],
                    "meta": meta_desc,
                })
            if (i + 1) % 25 == 0:
                print(f"  Progress: {i+1}/{len(missing)} updated")
        else:
            results["errors"] += 1

        time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"CTR OPTIMIZATION COMPLETE")
    print(f"Updated: {results['updated']}")
    print(f"Errors: {results['errors']}")

    with open("/var/lib/freelancer/projects/40416335/phase22b_ctr_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
