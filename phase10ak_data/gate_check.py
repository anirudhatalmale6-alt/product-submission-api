#!/usr/bin/env python3
"""
Phase 10AK Publication Gate-Check for PetHub Online
Fetches all 26 draft posts and runs 5 quality gates.
"""

import csv
import json
import subprocess
import re
import html
import sys
import time
from html.parser import HTMLParser

# ── credentials ──────────────────────────────────────────────────────────
BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ak_data"

# ── post IDs by type ─────────────────────────────────────────────────────
GLOSSARY_IDS   = [7167, 7169, 7170, 7172, 7174, 7175, 7177]
SPOKE_IDS      = list(range(7332, 7347))          # 7332-7346 inclusive = 15
BRAND_IDS      = [7828, 7829, 8171, 8172]
ALL_IDS        = GLOSSARY_IDS + SPOKE_IDS + BRAND_IDS

def post_type(pid):
    if pid in GLOSSARY_IDS: return "glossary"
    if pid in SPOKE_IDS:    return "educational_spoke"
    if pid in BRAND_IDS:    return "editorial_brand"
    return "unknown"

# ── HTML helpers ─────────────────────────────────────────────────────────
class TextExtractor(HTMLParser):
    """Strip tags, collect plain text."""
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True
    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False
    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)
    def get_text(self):
        return " ".join(self.parts)

def strip_html(raw):
    t = TextExtractor()
    t.feed(raw or "")
    return t.get_text()

def word_count(raw):
    txt = strip_html(raw)
    return len(txt.split())

# ── API fetch ────────────────────────────────────────────────────────────
def fetch_post(pid, endpoint="posts"):
    """Try posts, then pages endpoint."""
    for ep in (endpoint, "pages"):
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

# ── GATE 1: TRUST LINT ──────────────────────────────────────────────────
UK_AUTHORITIES = [
    "RSPCA", "PDSA", "BVA", "British Veterinary Association",
    "Battersea", "Dogs Trust", "Blue Cross", "Cats Protection",
    "DEFRA", "Kennel Club", "Animal Welfare Act",
    "Royal College of Veterinary Surgeons", "RCVS",
    "PFMA", "Pet Food Manufacturers", "Veterinary Medicines Directorate",
]

def gate1_trust(content_raw, ptype):
    issues = []
    low = (content_raw or "").lower()

    has_trust_footer = ("editorial standards" in low or
                        "our editorial standards" in low or
                        "editorial-standards" in low)
    if not has_trust_footer:
        issues.append("MISSING trust footer (Editorial Standards)")

    has_uk_auth = any(a.lower() in low for a in UK_AUTHORITIES)
    if not has_uk_auth and ptype != "glossary":
        issues.append("MISSING UK authority reference")

    has_editorial_link = ("editorial-process" in low or
                          "editorial process" in low or
                          "editorial-standards" in low)
    if not has_editorial_link:
        issues.append("MISSING editorial process link")

    has_affiliate_disc = ("affiliate" in low and "disclos" in low) or "affiliate-disclosure" in low
    if not has_affiliate_disc and ptype != "glossary":
        issues.append("MISSING affiliate disclosure link")

    has_ai_transparency = ("ai" in low and ("transparency" in low or "assisted" in low or "generated" in low)) or "ai-transparency" in low
    if not has_ai_transparency:
        issues.append("RECOMMENDED: AI transparency disclosure missing")

    required_pass = all(
        "MISSING" not in i or "RECOMMENDED" in i for i in issues
    )
    # recalc: only MISSING (not RECOMMENDED) are required failures
    req_issues = [i for i in issues if i.startswith("MISSING")]
    return len(req_issues) == 0, issues

# ── GATE 2: CONTENT QUALITY ─────────────────────────────────────────────
PLACEHOLDER_PATTERNS = [
    r"\{title\}", r"\{vendor_count\}", r"\{product_count\}",
    r"\{category\}", r"\{brand\}", r"\{price\}", r"\{url\}",
    r"\{name\}", r"\{description\}", r"\{keyword\}",
    r"Lorem ipsum", r"TODO", r"FIXME", r"XXX",
    r"\[INSERT", r"\[PLACEHOLDER",
]

def gate2_content(content_raw, ptype):
    issues = []
    wc = word_count(content_raw)
    if wc < 500:
        issues.append(f"Word count {wc} < 500")

    # FAQ check (required for spokes only)
    low = (content_raw or "").lower()
    has_faq = ("faq" in low or "frequently asked" in low or
               "common questions" in low or
               re.search(r'class="[^"]*faq', low) is not None)
    if not has_faq and ptype == "educational_spoke":
        issues.append("MISSING FAQ section")

    # Heading structure
    has_h2 = bool(re.search(r"<h2[ >]", content_raw or "", re.I))
    has_h3 = bool(re.search(r"<h3[ >]", content_raw or "", re.I))
    if not has_h2:
        issues.append("MISSING H2 headings")

    # Placeholders
    for pat in PLACEHOLDER_PATTERNS:
        if re.search(pat, content_raw or "", re.I):
            issues.append(f"Placeholder found: {pat}")
            break

    # Internal links check
    internal_links = re.findall(r'href="(/[^"]*)"', content_raw or "")
    # We just flag obviously broken patterns (double slashes, empty, etc.)
    for link in internal_links:
        if "//" in link or link.strip() == "/" or "{" in link:
            issues.append(f"Suspect internal link: {link}")
            break

    req_issues = [i for i in issues if not i.startswith("RECOMMENDED")]
    return len(req_issues) == 0, issues

# ── GATE 3: METADATA ────────────────────────────────────────────────────
def gate3_metadata(post):
    issues = []
    title = post.get("title", {}).get("rendered") or post.get("title", {}).get("raw", "")
    if not title or not title.strip():
        issues.append("MISSING title")

    slug = post.get("slug", "")
    if not slug or not slug.strip():
        issues.append("MISSING slug")

    cats = post.get("categories", [])
    if not cats:
        issues.append("RECOMMENDED: no categories assigned")

    excerpt = post.get("excerpt", {}).get("rendered") or post.get("excerpt", {}).get("raw", "")
    if not excerpt or not strip_html(excerpt).strip():
        issues.append("RECOMMENDED: no excerpt")

    req_issues = [i for i in issues if not i.startswith("RECOMMENDED")]
    return len(req_issues) == 0, issues

# ── GATE 4: STRUCTURE ────────────────────────────────────────────────────
def gate4_structure(content_raw, ptype):
    issues = []

    if ptype == "glossary":
        # Count defined terms: look for <dt>, <strong> in list, or H3 terms
        dt_count = len(re.findall(r"<dt[ >]", content_raw or "", re.I))
        # Also count H3 or bold terms that look like definitions
        h3_count = len(re.findall(r"<h3[ >]", content_raw or "", re.I))
        # Count <li> with bold starts as potential term definitions
        li_bold = len(re.findall(r"<li[^>]*>\s*<strong>", content_raw or "", re.I))
        term_count = max(dt_count, h3_count, li_bold)
        if term_count < 15:
            issues.append(f"Glossary has ~{term_count} terms (need >=15)")

    if ptype == "educational_spoke":
        has_table = bool(re.search(r"<table[ >]", content_raw or "", re.I))
        if not has_table:
            issues.append("RECOMMENDED: no comparison table found")

    if ptype == "editorial_brand":
        low = (content_raw or "").lower()
        has_mission = ("mission" in low or "methodology" in low or
                       "approach" in low or "how we" in low or
                       "our process" in low or "our team" in low or
                       "about us" in low or "who we are" in low or
                       "our philosophy" in low or "what we do" in low)
        if not has_mission:
            issues.append("MISSING mission/methodology content")

    # Duplicate content blocks check (look for large repeated passages)
    if content_raw:
        # Split into paragraphs and check for duplicates
        paras = re.findall(r"<p[^>]*>(.*?)</p>", content_raw, re.I | re.S)
        para_texts = [strip_html(p).strip() for p in paras if len(strip_html(p).strip()) > 80]
        seen = set()
        for pt in para_texts:
            if pt in seen:
                issues.append("Duplicate content block detected")
                break
            seen.add(pt)

    req_issues = [i for i in issues if not i.startswith("RECOMMENDED")]
    return len(req_issues) == 0, issues

# ── GATE 5: SAFETY ──────────────────────────────────────────────────────
FAKE_EXPERT_PATTERNS = [
    r"Dr\.\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+(says|recommends|advises|suggests)",
    r"veterinar(y|ian)\s+expert\s+[A-Z]",
    r"according to\s+(our|the)\s+expert",
    r"certified\s+pet\s+nutritionist\s+[A-Z]",
]

HARMFUL_HEALTH = [
    r"cure[sd]?\s+(cancer|diabetes|disease)",
    r"guaranteed?\s+to\s+(heal|cure|treat)",
    r"proven\s+to\s+cure",
    r"eliminates?\s+(all\s+)?disease",
    r"replace\s+(your\s+)?vet",
    r"no\s+need\s+(to\s+)?see\s+a\s+vet",
]

def gate5_safety(content_raw, ptype):
    issues = []

    # Fake expert claims
    for pat in FAKE_EXPERT_PATTERNS:
        m = re.search(pat, content_raw or "", re.I)
        if m:
            issues.append(f"Possible fake expert claim: ...{m.group(0)}...")
            break

    # Harmful health claims
    for pat in HARMFUL_HEALTH:
        m = re.search(pat, content_raw or "", re.I)
        if m:
            issues.append(f"Harmful health claim: ...{m.group(0)}...")
            break

    # Affiliate links (must be BLOCKED)
    affiliate_patterns = [
        r"amzn\.to", r"amazon\..*[?&]tag=", r"shareasale\.com",
        r"commission-?junction", r"awin1\.com", r"ref=", r"affiliate",
        r"tracking.*click", r"partner.*link",
    ]
    # Be more precise: look for actual hrefs with affiliate markers
    hrefs = re.findall(r'href="([^"]*)"', content_raw or "")
    for h in hrefs:
        hl = h.lower()
        if any(x in hl for x in ["amzn.to", "shareasale", "awin1.com",
                                   "commission-junction", "?tag=",
                                   "affiliate_id=", "ref_id=", "partner_id="]):
            issues.append(f"Affiliate link detected: {h[:80]}")
            break

    # Specific product recommendations without evidence
    # (light heuristic: "you should buy X" or "we recommend buying X")
    buy_recs = re.findall(
        r"(you should buy|we recommend (buying|purchasing)|must buy|best .*to buy)",
        content_raw or "", re.I
    )
    if buy_recs:
        issues.append("RECOMMENDED: review specific purchase recommendations")

    req_issues = [i for i in issues if not i.startswith("RECOMMENDED")]
    return len(req_issues) == 0, issues


# ── MAIN ─────────────────────────────────────────────────────────────────
def main():
    results = []
    fixes_log = []

    print(f"Starting gate-check for {len(ALL_IDS)} posts...")
    print("=" * 70)

    for idx, pid in enumerate(ALL_IDS, 1):
        ptype = post_type(pid)
        print(f"\n[{idx}/{len(ALL_IDS)}] Fetching post {pid} ({ptype})...", flush=True)

        post = fetch_post(pid)
        if not post:
            print(f"  ERROR: Could not fetch post {pid}")
            results.append({
                "id": pid,
                "title": "FETCH_ERROR",
                "type": ptype,
                "word_count": 0,
                "trust_lint": "FAIL",
                "content_quality": "FAIL",
                "metadata": "FAIL",
                "structure": "FAIL",
                "safety": "FAIL",
                "overall_gate": "FAIL",
                "issues": "Could not fetch post",
                "fixes_applied": "",
            })
            continue

        # Extract content
        content_raw = post.get("content", {}).get("rendered") or post.get("content", {}).get("raw", "")
        title = post.get("title", {}).get("rendered") or post.get("title", {}).get("raw", "")
        title_clean = strip_html(title).strip()
        wc = word_count(content_raw)

        print(f"  Title: {title_clean[:70]}")
        print(f"  Word count: {wc}")
        print(f"  Status: {post.get('status', 'unknown')}")

        # Run all gates
        g1_pass, g1_issues = gate1_trust(content_raw, ptype)
        g2_pass, g2_issues = gate2_content(content_raw, ptype)
        g3_pass, g3_issues = gate3_metadata(post)
        g4_pass, g4_issues = gate4_structure(content_raw, ptype)
        g5_pass, g5_issues = gate5_safety(content_raw, ptype)

        all_issues = g1_issues + g2_issues + g3_issues + g4_issues + g5_issues
        required_issues = [i for i in all_issues if not i.startswith("RECOMMENDED")]
        recommended_issues = [i for i in all_issues if i.startswith("RECOMMENDED")]

        # Determine overall gate
        critical_fail = (not g2_pass and any("Word count" in i for i in g2_issues)) or \
                        (not g5_pass) or \
                        (not g3_pass and any("MISSING title" in i for i in g3_issues))

        if len(required_issues) == 0:
            overall = "PASS"
        elif critical_fail:
            overall = "FAIL"
        elif len(required_issues) <= 3:
            overall = "CONDITIONAL"
        else:
            overall = "FAIL"

        # Print gate results
        gate_labels = [
            ("Gate 1 Trust", g1_pass, g1_issues),
            ("Gate 2 Content", g2_pass, g2_issues),
            ("Gate 3 Metadata", g3_pass, g3_issues),
            ("Gate 4 Structure", g4_pass, g4_issues),
            ("Gate 5 Safety", g5_pass, g5_issues),
        ]
        for label, passed, iss in gate_labels:
            status = "PASS" if passed else "FAIL"
            print(f"  {label}: {status}")
            for i in iss:
                print(f"    - {i}")

        print(f"  >>> OVERALL: {overall}")

        results.append({
            "id": pid,
            "title": title_clean[:120],
            "type": ptype,
            "word_count": wc,
            "trust_lint": "PASS" if g1_pass else "FAIL",
            "content_quality": "PASS" if g2_pass else "FAIL",
            "metadata": "PASS" if g3_pass else "FAIL",
            "structure": "PASS" if g4_pass else "FAIL",
            "safety": "PASS" if g5_pass else "FAIL",
            "overall_gate": overall,
            "issues": " | ".join(all_issues) if all_issues else "None",
            "fixes_applied": "",
        })

        # Small delay to be gentle on the server
        time.sleep(0.3)

    # ── Write CSVs ───────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("Writing CSV reports...")

    # Full gate check CSV
    gate_csv = f"{DATA_DIR}/publication_gate_check.csv"
    with open(gate_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "id", "title", "type", "word_count",
            "trust_lint", "content_quality", "metadata", "structure", "safety",
            "overall_gate", "issues", "fixes_applied"
        ])
        w.writeheader()
        w.writerows(results)
    print(f"  Wrote: {gate_csv}")

    # Publication-ready CSV
    ready_csv = f"{DATA_DIR}/publication_ready.csv"
    with open(ready_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "title", "type", "gate_status", "recommendation"])
        w.writeheader()
        for r in results:
            if r["overall_gate"] == "PASS":
                rec = "Ready for publication"
            elif r["overall_gate"] == "CONDITIONAL":
                rec = "Needs minor fixes before publication"
            else:
                rec = "Needs significant rework"
            w.writerow({
                "id": r["id"],
                "title": r["title"],
                "type": r["type"],
                "gate_status": r["overall_gate"],
                "recommendation": rec,
            })
    print(f"  Wrote: {ready_csv}")

    # ── Summary ──────────────────────────────────────────────────────────
    pass_count = sum(1 for r in results if r["overall_gate"] == "PASS")
    cond_count = sum(1 for r in results if r["overall_gate"] == "CONDITIONAL")
    fail_count = sum(1 for r in results if r["overall_gate"] == "FAIL")

    print(f"\n{'=' * 70}")
    print(f"GATE-CHECK SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Total posts checked: {len(results)}")
    print(f"  PASS:        {pass_count}")
    print(f"  CONDITIONAL: {cond_count}")
    print(f"  FAIL:        {fail_count}")
    print(f"{'=' * 70}")

    # Per-type breakdown
    for t in ["glossary", "educational_spoke", "editorial_brand"]:
        subset = [r for r in results if r["type"] == t]
        p = sum(1 for r in subset if r["overall_gate"] == "PASS")
        c = sum(1 for r in subset if r["overall_gate"] == "CONDITIONAL")
        fa = sum(1 for r in subset if r["overall_gate"] == "FAIL")
        print(f"  {t}: {len(subset)} total — {p} PASS / {c} CONDITIONAL / {fa} FAIL")

    print()

    # List FAIL posts with their issues
    fails = [r for r in results if r["overall_gate"] == "FAIL"]
    if fails:
        print("POSTS THAT NEED REWORK:")
        for r in fails:
            print(f"  ID {r['id']} ({r['type']}): {r['title'][:60]}")
            for issue in r["issues"].split(" | "):
                if not issue.startswith("RECOMMENDED"):
                    print(f"    - {issue}")

    conds = [r for r in results if r["overall_gate"] == "CONDITIONAL"]
    if conds:
        print("\nPOSTS NEEDING MINOR FIXES:")
        for r in conds:
            print(f"  ID {r['id']} ({r['type']}): {r['title'][:60]}")
            for issue in r["issues"].split(" | "):
                if not issue.startswith("RECOMMENDED"):
                    print(f"    - {issue}")

    passes = [r for r in results if r["overall_gate"] == "PASS"]
    if passes:
        print("\nPOSTS READY FOR PUBLICATION:")
        for r in passes:
            print(f"  ID {r['id']} ({r['type']}): {r['title'][:60]}")


if __name__ == "__main__":
    main()
