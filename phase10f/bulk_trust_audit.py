#!/usr/bin/env python3
"""Bulk trust audit: lint all published posts and populate trust_audit table."""
import requests, json, sys

s = requests.Session()
s.headers["Accept-Encoding"] = "gzip, deflate"
s.auth = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")

page = 1
all_posts = []
while True:
    r = s.get(f"https://pethubonline.com/wp-json/wp/v2/posts?per_page=50&page={page}&status=publish&_fields=id,title,content,link,yoast_head_json")
    if r.status_code != 200:
        break
    posts = r.json()
    if not posts:
        break
    all_posts.extend(posts)
    page += 1

print(f"Found {len(all_posts)} published posts")

stats = {"total": 0, "clean": 0, "warnings_only": 0, "errors": 0, "blockers": 0}
issues_summary = {}

for post in all_posts:
    pid = post["id"]
    title = post["title"]["rendered"]
    body = post["content"]["rendered"]
    link = post.get("link", "")
    yoast = post.get("yoast_head_json", {})
    meta_title = yoast.get("title", "")
    meta_desc = yoast.get("description", "")

    lint = requests.post("http://127.0.0.1:8100/api/trust/lint/run", json={
        "content_id": pid,
        "content_title": title,
        "content_body": body,
        "meta_title": meta_title,
        "meta_description": meta_desc
    }).json()

    b = lint.get("blockers", 0)
    e = lint.get("errors", 0)
    w = lint.get("warnings", 0)

    stats["total"] += 1
    if b > 0:
        stats["blockers"] += 1
    elif e > 0:
        stats["errors"] += 1
    elif w > 0:
        stats["warnings_only"] += 1
    else:
        stats["clean"] += 1

    for r_item in lint.get("results", []):
        if not r_item.get("passed"):
            rule = r_item["rule"]
            issues_summary[rule] = issues_summary.get(rule, 0) + 1

    # Also run audit to populate trust_audit table
    try:
        requests.post("http://127.0.0.1:8100/api/trust/audit/run", json={
            "content_id": pid,
            "content_title": title,
            "content_url": link
        }, timeout=10)
    except:
        pass

    status_char = "." if b == 0 and e == 0 else "!" if b > 0 else "x"
    sys.stdout.write(status_char)
    sys.stdout.flush()

print(f"\n\nAudit complete: {stats['total']} posts")
print(f"  Clean (0 issues):  {stats['clean']}")
print(f"  Warnings only:     {stats['warnings_only']}")
print(f"  Errors:            {stats['errors']}")
print(f"  Blockers:          {stats['blockers']}")
print(f"\nMost common issues:")
for rule, count in sorted(issues_summary.items(), key=lambda x: -x[1]):
    print(f"  {rule}: {count}")
