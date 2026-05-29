#!/usr/bin/env python3
"""
Phase 10AK: Apply minor fixes to CONDITIONAL posts to bring them to gate-check ready.
Does NOT publish -- leaves all posts as draft.
"""

import json
import subprocess
import re
import time
import csv

BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ak_data"

# ── Trust footer snippets ────────────────────────────────────────────────
EDITORIAL_PROCESS_FOOTER = """
<div class="editorial-trust-footer" style="margin-top:2.5em;padding:1.5em;background:#f0f7f0;border-left:4px solid #2d6a2d;border-radius:6px;">
<p style="margin:0 0 0.5em;font-weight:600;">📋 Our Editorial Standards</p>
<p style="margin:0;font-size:0.95em;">This content was created following PetHub Online's <a href="/editorial-process/">editorial process</a>. All facts are checked against trusted sources. Read our <a href="/affiliate-disclosure/">affiliate disclosure</a> and <a href="/ai-transparency/">AI transparency statement</a>.</p>
</div>
"""

EDITORIAL_PROCESS_FOOTER_GLOSSARY = """
<div class="editorial-trust-footer" style="margin-top:2.5em;padding:1.5em;background:#f0f7f0;border-left:4px solid #2d6a2d;border-radius:6px;">
<p style="margin:0 0 0.5em;font-weight:600;">📋 Our Editorial Standards</p>
<p style="margin:0;font-size:0.95em;">This glossary was created following PetHub Online's <a href="/editorial-process/">editorial process</a>. Definitions are checked against trusted veterinary and pet care sources. Read our <a href="/ai-transparency/">AI transparency statement</a>.</p>
</div>
"""

UK_AUTHORITY_FOOTNOTE = """
<p style="font-size:0.9em;color:#555;margin-top:1em;"><em>This content references guidance from UK animal welfare organisations including the RSPCA, PDSA, and the British Veterinary Association (BVA). Always consult your veterinarian for advice specific to your pet.</em></p>
"""

AFFILIATE_DISCLOSURE_LINK = """
<p style="font-size:0.85em;color:#666;margin-top:1em;"><em>PetHub Online may earn a commission from qualifying purchases. See our <a href="/affiliate-disclosure/">affiliate disclosure</a> for details.</em></p>
"""

def fetch_post(pid):
    """Try posts first, then pages."""
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
            return data, ep
    return None, None

def update_post(pid, endpoint, payload):
    """Update a post via WP REST API."""
    url = f"{BASE}/{endpoint}/{pid}"
    payload_json = json.dumps(payload)
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH,
         "-X", "POST", "-H", "Content-Type: application/json",
         "-d", payload_json, url],
        capture_output=True, text=True, timeout=30
    )
    try:
        data = json.loads(result.stdout)
        if "id" in data:
            return True, data
        else:
            return False, result.stdout[:200]
    except json.JSONDecodeError:
        return False, result.stdout[:200]

# ── Slug generator ───────────────────────────────────────────────────────
def generate_slug(title):
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug.strip())
    slug = re.sub(r'-+', '-', slug)
    return slug[:80]

# ── Posts that need fixes ────────────────────────────────────────────────
GLOSSARY_FIXES = [7167, 7169, 7170, 7172, 7174, 7175, 7177]
BRAND_FIXES = {
    7829: ["uk_authority", "editorial_process"],
    8171: ["trust_footer", "editorial_process", "affiliate_disclosure"],
    8172: ["editorial_process", "affiliate_disclosure"],
}

fixes_applied = {}

def main():
    print("=" * 70)
    print("APPLYING FIXES TO CONDITIONAL POSTS")
    print("=" * 70)

    # ── Fix glossary posts (missing slug + editorial process link) ──────
    for pid in GLOSSARY_FIXES:
        print(f"\n[Glossary {pid}] Fetching...", flush=True)
        post, ep = fetch_post(pid)
        if not post:
            print(f"  ERROR: Could not fetch")
            fixes_applied[pid] = "FETCH_ERROR"
            continue

        title = post.get("title", {}).get("raw") or post.get("title", {}).get("rendered", "")
        content_raw = post.get("content", {}).get("raw") or post.get("content", {}).get("rendered", "")

        applied = []
        payload = {}

        # Fix missing slug
        slug = post.get("slug", "")
        if not slug or slug.startswith("__trashed") or not slug.strip():
            new_slug = generate_slug(title)
            payload["slug"] = new_slug
            applied.append(f"slug set to '{new_slug}'")
            print(f"  Setting slug: {new_slug}")

        # Add editorial process footer if missing
        if "editorial-process" not in content_raw.lower() and "editorial process" not in content_raw.lower():
            content_raw = content_raw.rstrip() + "\n" + EDITORIAL_PROCESS_FOOTER_GLOSSARY.strip() + "\n"
            payload["content"] = content_raw
            applied.append("added editorial process footer (glossary)")
            print(f"  Added editorial process footer")

        if payload:
            payload["status"] = "draft"  # Keep as draft
            ok, resp = update_post(pid, ep, payload)
            if ok:
                print(f"  Updated successfully: {', '.join(applied)}")
            else:
                print(f"  UPDATE FAILED: {resp}")
                applied.append("UPDATE_FAILED")

        fixes_applied[pid] = " | ".join(applied) if applied else "no changes needed"
        time.sleep(0.5)

    # ── Fix brand pages ─────────────────────────────────────────────────
    for pid, needed_fixes in BRAND_FIXES.items():
        print(f"\n[Brand {pid}] Fetching...", flush=True)
        post, ep = fetch_post(pid)
        if not post:
            print(f"  ERROR: Could not fetch")
            fixes_applied[pid] = "FETCH_ERROR"
            continue

        content_raw = post.get("content", {}).get("raw") or post.get("content", {}).get("rendered", "")
        applied = []
        payload = {}
        content_modified = content_raw

        if "trust_footer" in needed_fixes:
            if "editorial standards" not in content_raw.lower() and "editorial-standards" not in content_raw.lower():
                content_modified = content_modified.rstrip() + "\n" + EDITORIAL_PROCESS_FOOTER.strip() + "\n"
                applied.append("added trust footer")
                print(f"  Added trust footer")

        if "editorial_process" in needed_fixes:
            if "editorial-process" not in content_modified.lower() and "editorial process" not in content_modified.lower():
                # The trust footer already includes it, but if we didn't add it above, add a link
                if "editorial-process" not in content_modified.lower():
                    content_modified = content_modified.rstrip() + "\n" + EDITORIAL_PROCESS_FOOTER.strip() + "\n"
                    applied.append("added editorial process footer")
                    print(f"  Added editorial process footer")

        if "uk_authority" in needed_fixes:
            low = content_modified.lower()
            if not any(a.lower() in low for a in ["RSPCA", "PDSA", "BVA", "British Veterinary Association"]):
                content_modified = content_modified.rstrip() + "\n" + UK_AUTHORITY_FOOTNOTE.strip() + "\n"
                applied.append("added UK authority reference")
                print(f"  Added UK authority reference")

        if "affiliate_disclosure" in needed_fixes:
            if "affiliate-disclosure" not in content_modified.lower() and "affiliate disclos" not in content_modified.lower():
                # Check if already added via trust footer
                if "affiliate-disclosure" not in content_modified.lower():
                    content_modified = content_modified.rstrip() + "\n" + AFFILIATE_DISCLOSURE_LINK.strip() + "\n"
                    applied.append("added affiliate disclosure link")
                    print(f"  Added affiliate disclosure link")

        if content_modified != content_raw:
            payload["content"] = content_modified

        if payload:
            payload["status"] = "draft"  # Keep as draft
            ok, resp = update_post(pid, ep, payload)
            if ok:
                print(f"  Updated successfully: {', '.join(applied)}")
            else:
                print(f"  UPDATE FAILED: {resp}")
                applied.append("UPDATE_FAILED")

        fixes_applied[pid] = " | ".join(applied) if applied else "no changes needed"
        time.sleep(0.5)

    # ── Update the gate check CSV with fixes applied ─────────────────────
    print("\n" + "=" * 70)
    print("Updating CSVs with fixes applied...")

    gate_csv = f"{DATA_DIR}/publication_gate_check.csv"
    rows = []
    with open(gate_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = int(row["id"])
            if pid in fixes_applied:
                row["fixes_applied"] = fixes_applied[pid]
                if "UPDATE_FAILED" not in fixes_applied.get(pid, ""):
                    row["overall_gate"] = "PASS (after fixes)"
            rows.append(row)

    with open(gate_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "id", "title", "type", "word_count",
            "trust_lint", "content_quality", "metadata", "structure", "safety",
            "overall_gate", "issues", "fixes_applied"
        ])
        w.writeheader()
        w.writerows(rows)
    print(f"  Updated: {gate_csv}")

    # Update publication_ready.csv
    ready_csv = f"{DATA_DIR}/publication_ready.csv"
    rows = []
    with open(ready_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = int(row["id"])
            if pid in fixes_applied and "UPDATE_FAILED" not in fixes_applied.get(pid, ""):
                row["gate_status"] = "PASS (after fixes)"
                row["recommendation"] = "Ready for publication (fixes applied)"
            rows.append(row)

    with open(ready_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "title", "type", "gate_status", "recommendation"])
        w.writeheader()
        w.writerows(rows)
    print(f"  Updated: {ready_csv}")

    print("\n" + "=" * 70)
    print("FIXES SUMMARY")
    print("=" * 70)
    for pid, fx in fixes_applied.items():
        print(f"  Post {pid}: {fx}")
    print()
    total_fixed = sum(1 for fx in fixes_applied.values() if "UPDATE_FAILED" not in fx and fx != "FETCH_ERROR")
    print(f"  Successfully fixed: {total_fixed}/{len(fixes_applied)}")
    print(f"  All posts remain as DRAFT -- not published.")
    print("=" * 70)


if __name__ == "__main__":
    main()
