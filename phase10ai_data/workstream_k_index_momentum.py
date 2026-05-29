#!/usr/bin/env python3
"""
10AI-K: INDEX MOMENTUM ENGINE
Comprehensive indexing health audit - measurement only.
"""

import subprocess, json, csv, re, html, sys
from datetime import datetime, timezone

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ai_data"

NOW = datetime.now(timezone.utc)

def api_get(endpoint):
    url = f"{BASE}/{endpoint}"
    r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, url], capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout)
    except:
        print(f"  [WARN] Failed to parse: {r.stdout[:200]}")
        return None

def strip_html(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()

def parse_date(date_str):
    """Parse WordPress date string."""
    if not date_str:
        return None
    try:
        # WordPress dates are in ISO format without timezone (assumed UTC)
        return datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
    except:
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        except:
            return None

def days_since(date_str):
    d = parse_date(date_str)
    if not d:
        return 9999
    return (NOW - d).days

print("=" * 70)
print("10AI-K: INDEX MOMENTUM ENGINE")
print("=" * 70)

# Step 1: Fetch ALL published posts
print("\n[STEP 1] Fetching all published posts...")
all_published = []
page = 1
while True:
    print(f"  Page {page}...")
    data = api_get(f"posts?per_page=100&page={page}&status=publish&_fields=id,title,slug,date,modified,status,categories,content")
    if not data or not isinstance(data, list) or len(data) == 0:
        break
    all_published.extend(data)
    print(f"    Got {len(data)} posts (total: {len(all_published)})")
    if len(data) < 100:
        break
    page += 1

print(f"\n  Total published posts: {len(all_published)}")

# Step 2: Fetch ALL draft posts
print("\n[STEP 2] Fetching all draft posts...")
all_drafts = []
page = 1
while True:
    print(f"  Page {page}...")
    data = api_get(f"posts?per_page=100&page={page}&status=draft&_fields=id,title,slug,date,modified,status,categories,content")
    if not data or not isinstance(data, list) or len(data) == 0:
        break
    all_drafts.extend(data)
    print(f"    Got {len(data)} drafts (total: {len(all_drafts)})")
    if len(data) < 100:
        break
    page += 1

print(f"\n  Total draft posts: {len(all_drafts)}")

# Step 3: Process and create CSVs

# 3a: Published posts CSV
print("\n[STEP 3a] Creating index_momentum_published.csv...")
published_rows = []
for post in all_published:
    title = strip_html(post.get("title", {}).get("rendered", ""))
    content_text = strip_html(post.get("content", {}).get("rendered", ""))
    word_count = len(content_text.split())
    pub_date = post.get("date", "")
    mod_date = post.get("modified", "")
    days_mod = days_since(mod_date)
    cats = post.get("categories", [])

    # Estimate crawl priority based on freshness + word count
    # Fresh + long content = higher priority
    if days_mod <= 7:
        freshness_score = 10
    elif days_mod <= 14:
        freshness_score = 8
    elif days_mod <= 30:
        freshness_score = 5
    else:
        freshness_score = 2

    if word_count >= 1500:
        depth_score = 10
    elif word_count >= 1000:
        depth_score = 7
    elif word_count >= 500:
        depth_score = 4
    else:
        depth_score = 2

    crawl_priority = (freshness_score * 0.6 + depth_score * 0.4)

    published_rows.append({
        "id": post["id"],
        "title": title,
        "slug": post.get("slug", ""),
        "published_date": pub_date,
        "last_modified": mod_date,
        "days_since_modified": days_mod,
        "word_count": word_count,
        "category_ids": ";".join(str(c) for c in cats),
        "estimated_crawl_priority": round(crawl_priority, 1)
    })

pub_csv = f"{DATA_DIR}/index_momentum_published.csv"
with open(pub_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id", "title", "slug", "published_date", "last_modified",
        "days_since_modified", "word_count", "category_ids", "estimated_crawl_priority"
    ])
    writer.writeheader()
    for row in published_rows:
        writer.writerow(row)
print(f"  Saved {len(published_rows)} rows to {pub_csv}")

# 3b: Drafts CSV
print("\n[STEP 3b] Creating index_momentum_drafts.csv...")
draft_rows = []
for post in all_drafts:
    title = strip_html(post.get("title", {}).get("rendered", ""))
    content_text = strip_html(post.get("content", {}).get("rendered", ""))
    word_count = len(content_text.split())
    created = post.get("date", "")

    # Estimate readiness (0-100)
    readiness = 0
    if word_count >= 1000:
        readiness += 40
    elif word_count >= 500:
        readiness += 25
    elif word_count >= 200:
        readiness += 10

    content_raw = post.get("content", {}).get("rendered", "")
    if re.search(r'<h2', content_raw): readiness += 15
    if re.search(r'<h3', content_raw): readiness += 10
    if re.search(r'(?i)(faq|frequently)', content_raw): readiness += 10
    if re.search(r'<table', content_raw): readiness += 10
    if re.search(r'href=', content_raw): readiness += 10
    if title and len(title) > 10: readiness += 5

    draft_rows.append({
        "id": post["id"],
        "title": title,
        "slug": post.get("slug", ""),
        "created_date": created,
        "word_count": word_count,
        "readiness_estimate": min(readiness, 100)
    })

draft_csv = f"{DATA_DIR}/index_momentum_drafts.csv"
with open(draft_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id", "title", "slug", "created_date", "word_count", "readiness_estimate"
    ])
    writer.writeheader()
    for row in draft_rows:
        writer.writerow(row)
print(f"  Saved {len(draft_rows)} rows to {draft_csv}")

# 3c: Freshness report
print("\n[STEP 3c] Creating freshness_report.csv...")
freshness_rows = []
for row in published_rows:
    days_stale = row["days_since_modified"]
    needs_refresh = days_stale > 30

    if days_stale > 90:
        priority = "CRITICAL"
    elif days_stale > 60:
        priority = "HIGH"
    elif days_stale > 30:
        priority = "MEDIUM"
    elif days_stale > 14:
        priority = "LOW"
    else:
        priority = "FRESH"

    freshness_rows.append({
        "id": row["id"],
        "title": row["title"],
        "days_stale": days_stale,
        "needs_refresh": needs_refresh,
        "refresh_priority": priority
    })

fresh_csv = f"{DATA_DIR}/freshness_report.csv"
with open(fresh_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id", "title", "days_stale", "needs_refresh", "refresh_priority"
    ])
    writer.writeheader()
    for row in freshness_rows:
        writer.writerow(row)
print(f"  Saved {len(freshness_rows)} rows to {fresh_csv}")

# Step 4: Calculate metrics
print("\n[STEP 4] Calculating index momentum metrics...")
print(f"\n{'=' * 50}")
print(f"INDEX MOMENTUM METRICS")
print(f"{'=' * 50}")

total_pub = len(published_rows)
total_drafts = len(draft_rows)
print(f"\n  Total published posts: {total_pub}")
print(f"  Total draft posts: {total_drafts}")

if published_rows:
    all_days = [r["days_since_modified"] for r in published_rows]
    avg_freshness = sum(all_days) / len(all_days)
    print(f"\n  Average freshness: {avg_freshness:.1f} days since last modified")

    # Distribution
    fresh_0_7 = sum(1 for d in all_days if d <= 7)
    fresh_7_14 = sum(1 for d in all_days if 7 < d <= 14)
    fresh_14_30 = sum(1 for d in all_days if 14 < d <= 30)
    fresh_30_plus = sum(1 for d in all_days if d > 30)

    print(f"\n  Freshness distribution:")
    print(f"    0-7 days:   {fresh_0_7} posts ({100*fresh_0_7/total_pub:.1f}%)")
    print(f"    7-14 days:  {fresh_7_14} posts ({100*fresh_7_14/total_pub:.1f}%)")
    print(f"    14-30 days: {fresh_14_30} posts ({100*fresh_14_30/total_pub:.1f}%)")
    print(f"    30+ days:   {fresh_30_plus} posts ({100*fresh_30_plus/total_pub:.1f}%)")

    print(f"\n  Update velocity (posts modified in last 7 days): {fresh_0_7}")

    # Word count stats
    wcs = [r["word_count"] for r in published_rows]
    avg_wc = sum(wcs) / len(wcs)
    min_wc = min(wcs)
    max_wc = max(wcs)
    print(f"\n  Word count: avg={avg_wc:.0f}, min={min_wc}, max={max_wc}")

    # Crawl priority distribution
    priorities = [r["estimated_crawl_priority"] for r in published_rows]
    high_pri = sum(1 for p in priorities if p >= 8)
    med_pri = sum(1 for p in priorities if 5 <= p < 8)
    low_pri = sum(1 for p in priorities if p < 5)
    print(f"\n  Crawl priority distribution:")
    print(f"    High (8+):  {high_pri} posts")
    print(f"    Medium (5-8): {med_pri} posts")
    print(f"    Low (<5):   {low_pri} posts")

if draft_rows:
    readiness = [r["readiness_estimate"] for r in draft_rows]
    ready_high = sum(1 for r in readiness if r >= 70)
    ready_med = sum(1 for r in readiness if 40 <= r < 70)
    ready_low = sum(1 for r in readiness if r < 40)
    print(f"\n  Draft readiness:")
    print(f"    Ready to publish (70+): {ready_high}")
    print(f"    Needs work (40-70):     {ready_med}")
    print(f"    Early stage (<40):      {ready_low}")

# Save metrics summary
metrics = {
    "total_published": total_pub,
    "total_drafts": total_drafts,
    "avg_freshness_days": round(avg_freshness, 1) if published_rows else 0,
    "posts_0_7_days": fresh_0_7 if published_rows else 0,
    "posts_7_14_days": fresh_7_14 if published_rows else 0,
    "posts_14_30_days": fresh_14_30 if published_rows else 0,
    "posts_30_plus_days": fresh_30_plus if published_rows else 0,
    "update_velocity_7d": fresh_0_7 if published_rows else 0,
    "avg_word_count": round(avg_wc) if published_rows else 0,
}

metrics_csv = f"{DATA_DIR}/index_momentum_metrics.csv"
with open(metrics_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(metrics.keys()))
    writer.writeheader()
    writer.writerow(metrics)
print(f"\n  Metrics saved to {metrics_csv}")

print(f"\n{'=' * 70}")
print(f"10AI-K COMPLETE")
print(f"{'=' * 70}")
