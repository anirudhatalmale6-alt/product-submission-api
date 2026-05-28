#!/usr/bin/env python3
"""
Phase 10AB Combined Scoring Engines
Generates CSVs for:
- 10AB-B: Actionability Score (per page)
- 10AB-C: Comparison Intelligence (per page)
- 10AB-D: Citation Acceleration (per page)
- 10AB-E: Semantic Link Quality (per page)
- 10AB-G: Trust Density (per page)
- 10AB-A: Glossary Reinforcement (per page)
"""

import subprocess, json, time, csv, re
from collections import defaultdict

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

def fetch_all_posts():
    posts = []
    page = 1
    while True:
        cmd = ["curl", "-s", "--compressed", "-u", AUTH,
               f"{WP_URL}/posts?status=publish&per_page=100&page={page}&context=edit"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        batch = json.loads(r.stdout)
        if not batch or isinstance(batch, dict):
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        time.sleep(2)
    return posts

print("Fetching all published posts...")
posts = fetch_all_posts()
print(f"Found {len(posts)} posts\n")

actionability_rows = []
comparison_rows = []
citation_rows = []
link_quality_rows = []
trust_density_rows = []
glossary_rows = []

all_slugs = {p["slug"] for p in posts}
slug_to_id = {p["slug"]: p["id"] for p in posts}

for post in posts:
    pid = post["id"]
    title = post["title"]["raw"]
    content = post["content"]["raw"]
    slug = post["slug"]
    wc = len(content.split())

    # ======== ACTIONABILITY (10AB-B) ========
    has_steps = bool(re.search(r'<ol>', content))
    has_practical = "Practical Example" in content or "practical example" in content
    has_measurable = "Measurable check" in content or "measurable" in content.lower()
    has_troubleshoot = any(w in content.lower() for w in ["warning sign", "if your dog", "if your cat", "what to do if", "signs to watch"])
    has_beginner = any(w in content.lower() for w in ["beginner", "first-time", "new owner", "getting started"])
    has_timeline = any(w in content.lower() for w in ["weekly", "daily", "monthly", "minutes", "hours", "days", "weeks"])
    has_checklist = bool(re.search(r'<li><strong>[^<]+:</strong>', content))
    has_safety = any(w in content.lower() for w in ["safety", "warning", "avoid", "never", "do not", "important"])

    act_score = (
        (20 if has_steps else 0) +
        (20 if has_practical else 0) +
        (15 if has_measurable else 0) +
        (10 if has_troubleshoot else 0) +
        (10 if has_beginner else 0) +
        (10 if has_timeline else 0) +
        (10 if has_checklist else 0) +
        (5 if has_safety else 0)
    )

    actionability_rows.append({
        "post_id": pid, "title": title, "word_count": wc,
        "has_steps": has_steps, "has_practical_example": has_practical,
        "has_measurable_guidance": has_measurable, "has_troubleshooting": has_troubleshoot,
        "has_beginner_access": has_beginner, "has_temporal_guidance": has_timeline,
        "has_structured_checklist": has_checklist, "has_safety_clarity": has_safety,
        "actionability_score": act_score
    })

    # ======== COMPARISON INTELLIGENCE (10AB-C) ========
    tables = re.findall(r'<figure class="wp-block-table">(.*?)</figure>', content, re.DOTALL)
    table_count = len(tables)
    total_rows = sum(len(re.findall(r'<tr>', t)) - 1 for t in tables)  # minus header
    total_cols = 0
    for t in tables:
        header_match = re.search(r'<thead><tr>(.*?)</tr></thead>', t, re.DOTALL)
        if header_match:
            total_cols = max(total_cols, len(re.findall(r'<th>', header_match.group(1))))

    has_comparison_heading = bool(re.search(r'[Cc]ompar', content[:5000]))
    has_vs = " vs " in title.lower() or " versus " in content.lower()

    comp_score = min(100, (
        (30 if table_count > 0 else 0) +
        (min(30, total_rows * 3)) +
        (min(20, total_cols * 5)) +
        (10 if has_comparison_heading else 0) +
        (10 if has_vs else 0)
    ))

    comparison_rows.append({
        "post_id": pid, "title": title,
        "table_count": table_count, "total_rows": total_rows,
        "max_columns": total_cols, "has_comparison_heading": has_comparison_heading,
        "has_vs_structure": has_vs, "comparison_score": comp_score
    })

    # ======== CITATION ACCELERATION (10AB-D) ========
    has_external_ref = any(ref in content for ref in ["rspca.org", "bva.co.uk", "fediaf.org", "battersea.org", "cats.org.uk", "gov.uk"])
    ext_ref_count = sum(1 for ref in ["rspca.org", "bva.co.uk", "fediaf.org", "battersea.org", "cats.org.uk", "gov.uk"] if ref in content)
    has_definitions = bool(re.search(r'<strong>[^<]+</strong>\s*[—–-]\s*[A-Z]', content))
    has_summary = bool(re.search(r'<p>[^<]{50,200}</p>\s*<!-- /wp:paragraph -->\s*\n\s*<!-- wp:heading', content[:1500]))
    has_faq = "FAQ" in content or "Common Questions" in content or "Frequently Asked" in content
    faq_count = len(re.findall(r'<!-- wp:heading {"level":3}', content))
    has_trust = "Editorial Standards" in content

    citation_score = min(100, (
        (15 if has_external_ref else 0) +
        (min(15, ext_ref_count * 5)) +
        (15 if has_definitions else 0) +
        (10 if has_summary else 0) +
        (10 if has_faq else 0) +
        (min(15, faq_count * 3)) +
        (10 if has_trust else 0) +
        (min(10, table_count * 10))
    ))

    citation_rows.append({
        "post_id": pid, "title": title,
        "has_external_refs": has_external_ref, "external_ref_count": ext_ref_count,
        "has_definitions": has_definitions, "has_summary_block": has_summary,
        "has_faq": has_faq, "faq_count": faq_count,
        "has_trust_block": has_trust, "has_comparison_table": table_count > 0,
        "citation_score": citation_score
    })

    # ======== SEMANTIC LINK QUALITY (10AB-E) ========
    internal_links = re.findall(r'href="https://pethubonline\.com/([^"]*?)/"', content)
    glossary_links = sum(1 for l in internal_links if any(kw in l for kw in ["glossary", "terminology", "key-terms", "explained"]))
    faq_links = sum(1 for l in internal_links if "faq" in l)
    trust_links = sum(1 for l in internal_links if any(kw in l for kw in ["methodology", "transparency", "quality-assurance", "corrections", "editorial"]))
    educational_links = sum(1 for l in internal_links if any(kw in l for kw in ["guide", "how-to", "tips", "basics", "explained", "complete"]))
    hub_links = sum(1 for l in internal_links if l.rstrip("/") in ["dog-toys", "cat-supplies", "dog-supplies", "dog-beds", "dog-food"])

    # Check if linked-to pages exist
    valid_links = sum(1 for l in internal_links if l.rstrip("/") in all_slugs)
    broken_links = len(internal_links) - valid_links

    link_quality = min(100, (
        (min(20, len(internal_links) * 4)) +
        (min(15, glossary_links * 10)) +
        (min(15, trust_links * 8)) +
        (min(15, educational_links * 5)) +
        (min(10, hub_links * 10)) +
        (min(10, faq_links * 10)) +
        (15 if broken_links == 0 else max(0, 15 - broken_links * 5))
    ))

    link_quality_rows.append({
        "post_id": pid, "title": title,
        "total_internal_links": len(internal_links),
        "glossary_links": glossary_links, "faq_links": faq_links,
        "trust_links": trust_links, "educational_links": educational_links,
        "hub_links": hub_links, "valid_links": valid_links,
        "broken_links": broken_links, "semantic_link_score": link_quality
    })

    # ======== TRUST DENSITY (10AB-G) ========
    has_trust_block = "Editorial Standards" in content
    has_disclosure = "affiliate" in content.lower() or "Affiliate Disclosure" in content
    has_methodology_link = "our-methodology" in content or "editorial-process" in content
    has_corrections_link = "corrections-policy" in content or "corrections-and-updates" in content
    has_ai_transparency = "ai-transparency" in content
    has_qa_link = "quality-assurance" in content
    has_date_updated = "Last Updated" in content or "last updated" in content
    external_trust = has_external_ref

    trust_score = min(100, (
        (20 if has_trust_block else 0) +
        (15 if has_disclosure else 0) +
        (10 if has_methodology_link else 0) +
        (10 if has_corrections_link else 0) +
        (10 if has_ai_transparency else 0) +
        (10 if has_qa_link else 0) +
        (10 if has_date_updated else 0) +
        (15 if external_trust else 0)
    ))

    trust_density_rows.append({
        "post_id": pid, "title": title,
        "has_trust_block": has_trust_block, "has_disclosure": has_disclosure,
        "has_methodology_link": has_methodology_link, "has_corrections_link": has_corrections_link,
        "has_ai_transparency": has_ai_transparency, "has_qa_link": has_qa_link,
        "has_date_updated": has_date_updated, "has_external_trust_refs": external_trust,
        "trust_density_score": trust_score
    })

    # ======== GLOSSARY REINFORCEMENT (10AB-A) ========
    key_terms_section = "Key Terms" in content
    glossary_terms = re.findall(r'<strong>([^<]+)</strong>\s*[—–-]', content)
    term_count = len(glossary_terms)
    has_definition_list = bool(re.search(r'<li><strong>[^<]+</strong>\s*[—–-]', content))
    inline_definitions = len(re.findall(r'meaning\s', content.lower())) + len(re.findall(r'refers to\s', content.lower())) + len(re.findall(r'defined as\s', content.lower()))

    glossary_score = min(100, (
        (25 if key_terms_section else 0) +
        (min(30, term_count * 5)) +
        (15 if has_definition_list else 0) +
        (min(15, inline_definitions * 5)) +
        (15 if term_count >= 6 else (term_count * 2))
    ))

    glossary_rows.append({
        "post_id": pid, "title": title,
        "has_key_terms_section": key_terms_section,
        "glossary_term_count": term_count,
        "has_definition_list": has_definition_list,
        "inline_definitions": inline_definitions,
        "glossary_reinforcement_score": glossary_score
    })

# Write all CSVs
base = "/var/lib/freelancer/projects/40416335/phase10ab_data"

def write_csv(path, rows, fields):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda x: x[fields[-1]], reverse=True))
    print(f"  Saved: {path}")

write_csv(f"{base}/Actionability_Scores.csv", actionability_rows,
    ["post_id","title","word_count","has_steps","has_practical_example","has_measurable_guidance",
     "has_troubleshooting","has_beginner_access","has_temporal_guidance","has_structured_checklist",
     "has_safety_clarity","actionability_score"])

write_csv(f"{base}/Comparison_Intelligence.csv", comparison_rows,
    ["post_id","title","table_count","total_rows","max_columns",
     "has_comparison_heading","has_vs_structure","comparison_score"])

write_csv(f"{base}/Citation_Acceleration.csv", citation_rows,
    ["post_id","title","has_external_refs","external_ref_count","has_definitions",
     "has_summary_block","has_faq","faq_count","has_trust_block","has_comparison_table",
     "citation_score"])

write_csv(f"{base}/Semantic_Link_Quality.csv", link_quality_rows,
    ["post_id","title","total_internal_links","glossary_links","faq_links","trust_links",
     "educational_links","hub_links","valid_links","broken_links","semantic_link_score"])

write_csv(f"{base}/Trust_Density_Scores.csv", trust_density_rows,
    ["post_id","title","has_trust_block","has_disclosure","has_methodology_link",
     "has_corrections_link","has_ai_transparency","has_qa_link","has_date_updated",
     "has_external_trust_refs","trust_density_score"])

write_csv(f"{base}/Glossary_Reinforcement.csv", glossary_rows,
    ["post_id","title","has_key_terms_section","glossary_term_count","has_definition_list",
     "inline_definitions","glossary_reinforcement_score"])

# Print summaries
print(f"\n{'='*60}")
print("PHASE 10AB ENGINE SUMMARIES")
print(f"{'='*60}")

act_avg = sum(r["actionability_score"] for r in actionability_rows) / len(actionability_rows)
comp_avg = sum(r["comparison_score"] for r in comparison_rows) / len(comparison_rows)
cit_avg = sum(r["citation_score"] for r in citation_rows) / len(citation_rows)
link_avg = sum(r["semantic_link_score"] for r in link_quality_rows) / len(link_quality_rows)
trust_avg = sum(r["trust_density_score"] for r in trust_density_rows) / len(trust_density_rows)
gloss_avg = sum(r["glossary_reinforcement_score"] for r in glossary_rows) / len(glossary_rows)

print(f"\nActionability:  avg {act_avg:.1f}/100  |  {sum(1 for r in actionability_rows if r['actionability_score']>=70)} posts >=70")
print(f"Comparison:     avg {comp_avg:.1f}/100  |  {sum(1 for r in comparison_rows if r['comparison_score']>=50)} posts >=50")
print(f"Citation:       avg {cit_avg:.1f}/100  |  {sum(1 for r in citation_rows if r['citation_score']>=70)} posts >=70")
print(f"Semantic Links: avg {link_avg:.1f}/100  |  {sum(1 for r in link_quality_rows if r['semantic_link_score']>=70)} posts >=70")
print(f"Trust Density:  avg {trust_avg:.1f}/100  |  {sum(1 for r in trust_density_rows if r['trust_density_score']>=70)} posts >=70")
print(f"Glossary:       avg {gloss_avg:.1f}/100  |  {sum(1 for r in glossary_rows if r['glossary_reinforcement_score']>=70)} posts >=70")

print(f"\nTop 5 citation-ready:")
for r in sorted(citation_rows, key=lambda x: x["citation_score"], reverse=True)[:5]:
    print(f"  {r['citation_score']}/100 — {r['title'][:60]}")

print(f"\nWeakest 5 by trust density:")
for r in sorted(trust_density_rows, key=lambda x: x["trust_density_score"])[:5]:
    print(f"  {r['trust_density_score']}/100 — {r['title'][:60]}")

print(f"\nWeakest 5 by actionability:")
for r in sorted(actionability_rows, key=lambda x: x["actionability_score"])[:5]:
    print(f"  {r['actionability_score']}/100 — {r['title'][:60]}")
