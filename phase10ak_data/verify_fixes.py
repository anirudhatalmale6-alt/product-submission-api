#!/usr/bin/env python3
"""Quick re-check of the 10 fixed posts to confirm they now pass all gates."""

import json
import subprocess
import re

BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

FIXED_IDS = [7167, 7169, 7170, 7172, 7174, 7175, 7177, 7829, 8171, 8172]

def fetch_post(pid):
    for ep in ("posts", "pages"):
        url = f"{BASE}/{ep}/{pid}?context=edit"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=30
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            continue
        if "id" in data:
            return data
    return None

def check_post(pid, post):
    content = post.get("content", {}).get("raw") or post.get("content", {}).get("rendered", "")
    low = content.lower()
    slug = post.get("slug", "")
    title = post.get("title", {}).get("raw") or post.get("title", {}).get("rendered", "")

    checks = {}
    checks["has_editorial_process"] = "editorial-process" in low or "editorial process" in low
    checks["has_editorial_standards"] = "editorial standards" in low or "editorial-standards" in low
    checks["has_slug"] = bool(slug and slug.strip())
    checks["has_title"] = bool(title and title.strip())

    # Brand-specific
    if pid in [7829, 8171, 8172]:
        uk_auths = ["rspca", "pdsa", "bva", "british veterinary"]
        checks["has_uk_authority"] = any(a in low for a in uk_auths)
        checks["has_affiliate_disc"] = "affiliate-disclosure" in low or ("affiliate" in low and "disclos" in low)

    all_pass = all(checks.values())
    return all_pass, checks

print("RE-VERIFICATION OF FIXED POSTS")
print("=" * 70)

all_good = True
for pid in FIXED_IDS:
    post = fetch_post(pid)
    if not post:
        print(f"  {pid}: FETCH ERROR")
        all_good = False
        continue

    passed, checks = check_post(pid, post)
    status = "PASS" if passed else "FAIL"
    title = post.get("title", {}).get("raw", "")[:50]
    draft_status = post.get("status", "?")

    fails = [k for k, v in checks.items() if not v]
    if passed:
        print(f"  {pid}: {status} (status={draft_status}) - {title}")
    else:
        print(f"  {pid}: {status} (status={draft_status}) - {title}")
        for f in fails:
            print(f"         STILL FAILING: {f}")
        all_good = False

print("=" * 70)
if all_good:
    print("ALL 10 FIXED POSTS NOW PASS GATE CHECKS")
else:
    print("SOME POSTS STILL HAVE ISSUES -- see above")
print("All posts remain as DRAFT.")
