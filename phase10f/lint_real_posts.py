#!/usr/bin/env python3
"""Run trust lint against real published posts from pethubonline.com"""
import requests, json

s = requests.Session()
s.headers["Accept-Encoding"] = "gzip, deflate"
s.auth = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")

r = s.get("https://pethubonline.com/wp-json/wp/v2/posts?per_page=10&status=publish&_fields=id,title,content,yoast_head_json,link")
posts = r.json()

results = []
for post in posts[:5]:
    pid = post["id"]
    title = post["title"]["rendered"]
    body = post["content"]["rendered"]
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

    issues = [r["rule"] for r in lint.get("results", []) if not r.get("passed")]
    results.append({
        "id": pid, "title": title[:60],
        "checks": lint.get("total_checks"),
        "passed": lint.get("passed"),
        "warnings": lint.get("warnings"),
        "errors": lint.get("errors"),
        "blockers": lint.get("blockers"),
        "issues": issues
    })

for r in results:
    status = "CLEAN" if r["blockers"] == 0 and r["errors"] == 0 else "ISSUES"
    print(f"[{status}] Post {r['id']}: {r['title']}")
    print(f"  Pass: {r['passed']}/{r['checks']} | Warn: {r['warnings']} | Err: {r['errors']} | Block: {r['blockers']}")
    if r["issues"]:
        print(f"  Flagged: {', '.join(r['issues'])}")
    print()

print(f"Total posts checked: {len(results)}")
clean = sum(1 for r in results if r["blockers"] == 0 and r["errors"] == 0)
print(f"Clean: {clean}/{len(results)}")
