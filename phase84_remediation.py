#!/usr/bin/env python3
"""
Phase 8.4 Remediation Script - PetHub Online Dog Food Posts
Audits and fixes 4 draft posts (3836-3839) for:
  Task 1: Price disclaimer updates (3837, 3838)
  Task 2: Trust/compliance banned phrase scan & fix (all 4)
  Task 3: H1/Astra audit (all 4)
  Task 4: Missing content sections (3837, 3839)
  Task 5: Affiliate disclosure update (all 4)
"""

import json
import re
import sys
import datetime
import requests
from collections import OrderedDict

# ── Configuration ──────────────────────────────────────────────────────────
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "***REDACTED_WP_PASSWORD***"
AUTH = (WP_USER, WP_PASS)

POST_IDS = [3836, 3837, 3838, 3839]
POST_META = {
    3836: {"slug": "best-dog-food-uk", "kw": "best dog food uk"},
    3837: {"slug": "best-dry-dog-food-uk", "kw": "best dry dog food uk"},
    3838: {"slug": "dry-vs-wet-dog-food-uk", "kw": "dry vs wet dog food"},
    3839: {"slug": "best-puppy-food-uk", "kw": "best puppy food uk"},
}

CHANGE_LOG_PATH = "/var/lib/freelancer/projects/40416335/phase84_change_log.json"

# ── New wording constants ──────────────────────────────────────────────────

NEW_PRICE_DISCLAIMER = (
    '<p style="font-size:0.88em;color:#666;font-style:italic;margin-top:6px;margin-bottom:16px;">'
    "These are broad estimated UK market ranges for general guidance only. "
    "They are not live product prices and may vary by brand, retailer, pack size, "
    "feeding amount and availability. We do not show product-specific prices until "
    "they are verified in the Product Evidence Register.</p>"
)

NEW_AFFILIATE_DISCLOSURE = (
    "We may earn a commission if you buy through some links on this page. "
    "This does not affect our editorial approach. We aim to explain how we "
    "compare products clearly and only make product-specific recommendations "
    "when evidence is available."
)

HEALTH_DISCLAIMER_3839 = (
    '<div style="background:#fff8e1;border-left:4px solid #ff9800;padding:12px 16px;'
    'margin:20px 0;font-size:0.92em;color:#7b5800;line-height:1.5;">'
    "<strong>Health Disclaimer:</strong> Dog food needs can vary by age, breed, "
    "activity level and health history. If your dog has allergies, digestive issues, "
    "growth concerns or a medical condition, speak to your vet before changing food.</div>"
)

# ── New sections for post 3837 ────────────────────────────────────────────

SECTION_HOW_WE_RESEARCH_3837 = """
<hr />

<h2>How We Research Dry Dog Food Information</h2>
<p>Our approach to reviewing dry dog food is based on publicly available product information rather than in-house laboratory testing. Here is what our research process involves:</p>
<ul>
<li><strong>Ingredient list review:</strong> We examine published ingredient lists from manufacturer packaging and websites, looking at protein sources, grain content, and additive profiles.</li>
<li><strong>Feeding guidance analysis:</strong> We compare manufacturer feeding recommendations against FEDIAF (European Pet Food Industry Federation) nutritional guidelines for adult dogs.</li>
<li><strong>Label information assessment:</strong> We review the analytical constituents (crude protein, fat, fibre, ash, moisture) declared on UK-compliant labels and convert to dry matter basis for fair comparison.</li>
<li><strong>Publicly available data:</strong> We reference PFMA (Pet Food Manufacturers Association) reports, FEDIAF nutritional guidelines, and FSA (Food Standards Agency) safety notices where relevant.</li>
</ul>
<p>We do not claim to have conducted independent feeding trials or laboratory analysis. Where product-specific evidence is still being gathered, we say so clearly. Our goal is to present factual, verifiable information that helps UK dog owners make informed choices.</p>
"""

SECTION_LABEL_READING_3837 = """
<hr />

<h2>What to Check on a UK Dog Food Label</h2>
<p>Understanding a UK dog food label helps you compare products on substance rather than marketing. Here are the key things to check:</p>
<ul>
<li><strong>"Complete" vs "Complementary":</strong> Complete food provides all the nutrition your dog needs as a sole diet. Complementary food must be fed alongside other food. Always check this distinction first.</li>
<li><strong>Ingredient order:</strong> Ingredients are listed in descending order by weight. The first ingredient makes up the largest proportion. Look for a named meat source (e.g., "chicken", "lamb") rather than vague terms like "cereals" or "meat and animal derivatives".</li>
<li><strong>Percentage declarations:</strong> Better brands state the percentage of key ingredients. "Chicken 26%" is more transparent than just listing "chicken" without a figure.</li>
<li><strong>Analytical constituents:</strong> Check crude protein (25%+ for adults), crude fat (12-18% for active adults), crude fibre (2-5%), and crude ash (5-10%). These figures help you compare nutritional content between brands.</li>
<li><strong>Additives section:</strong> Look for natural preservatives (tocopherols, rosemary extract) rather than BHA, BHT, or artificial colours (E102, E110, E124).</li>
<li><strong>Best-before date and batch number:</strong> Useful for tracking recalls and ensuring freshness, particularly with large bags that take weeks to use.</li>
</ul>
<p>Remember that UK pet food labelling is governed by the Animal Feed Regulations and overseen by Trading Standards. All "complete" food must meet minimum nutritional standards, but quality varies significantly within those minimums.</p>
"""

SECTION_WHEN_NOT_DRY_3837 = """
<hr />

<h2>When Dry Food May Not Be the Right Choice</h2>
<p>Dry dog food suits the majority of healthy adult dogs, but there are situations where wet food, mixed feeding, or other formats may be more appropriate:</p>
<ul>
<li><strong>Dogs with dental problems:</strong> If your dog has missing teeth, gum disease, or jaw issues, hard kibble can be painful to eat. Wet food or soaked kibble may be more comfortable.</li>
<li><strong>Dogs that drink very little water:</strong> Kibble contains only 8-10% moisture. Dogs that are reluctant drinkers may benefit from wet food (75-85% moisture) to maintain hydration, particularly in warmer months or if prone to urinary issues.</li>
<li><strong>Senior dogs with reduced appetite:</strong> Older dogs often find wet food more palatable due to its stronger aroma and softer texture. If your senior dog is losing interest in kibble, adding wet food or switching formats may help.</li>
<li><strong>Dogs recovering from illness or surgery:</strong> Soft food is often recommended during recovery. Your vet will advise on the appropriate diet.</li>
<li><strong>Dogs with specific medical conditions:</strong> Some conditions (e.g., kidney disease, certain urinary problems) benefit from increased water intake. Speak to your vet for health-specific feeding advice.</li>
</ul>
<p>Many UK dog owners find that a mixed feeding approach — primarily kibble with some wet food — provides a practical balance of convenience, cost, and palatability. There is no single "correct" format for all dogs.</p>
"""

SECTION_EVIDENCE_STATUS_3837 = """
<hr />

<h2>Evidence Status of Product Recommendations</h2>
<p>We believe in being transparent about the basis for any recommendations we make. Here is where we currently stand:</p>
<ul>
<li><strong>Nutritional guidance:</strong> Our general advice on what to look for in dry dog food is based on FEDIAF nutritional standards, UK labelling regulations, and publicly available veterinary nutritional science. We have high confidence in this information.</li>
<li><strong>Product-specific recommendations:</strong> We are currently building a Product Evidence Register that will document the factual basis for any specific product recommendations. Until a product has been reviewed against our criteria and the evidence is documented, we mark it as "evidence pending."</li>
<li><strong>Price information:</strong> Prices quoted are broad market ranges for general guidance. They are not live, verified product prices and may vary by retailer, region, and time of purchase.</li>
<li><strong>Brand mentions:</strong> Where we mention brands by name, this is based on publicly available product information and UK market availability, not paid placement or brand partnership.</li>
</ul>
<p>We would rather leave a gap in our recommendations than fill it with unverified claims. As our evidence review progresses, specific product recommendations will be added to this guide with clear documentation of the supporting evidence.</p>
"""

# ── Banned phrase replacement rules (Task 2) ──────────────────────────────

BANNED_PHRASES = [
    # (pattern, replacement, description)
    (r'\bwe tested\b', 'we reviewed publicly available product information', 'banned: "we tested"'),
    (r'\bour tests\b', 'we reviewed publicly available product information', 'banned: "our tests"'),
    (r'\bHow we tested\b', 'How we research dog food information', 'banned: "How we tested"'),
    (r'\bHow We Tested\b', 'How We Research Dog Food Information', 'banned: "How We Tested"'),
    (r'\bvet[\-\s]backed\b', 'speak to your vet for health-specific feeding advice', 'banned: "vet-backed"'),
    (r'\bvet recommended\b', 'speak to your vet for health-specific feeding advice', 'banned: "vet recommended"'),
    (r'\bour vets? recommend\b', 'speak to your vet for health-specific feeding advice', 'banned: "our vet(s) recommend"'),
    (r'\bour vet\b', 'your vet', 'banned: "our vet"'),
    (r'\bclinically proven\b', 'designed for', 'banned: "clinically proven"'),
    (r'\bcustomer favourite\b', '', 'banned: "customer favourite"'),
    (r'\bcustomers say\b', '', 'banned: "customers say"'),
    (r'\bverified buyers say\b', '', 'banned: "verified buyers say"'),
    (r'\breviews show\b', '', 'banned: "reviews show"'),
    (r'\bcures\b', 'may support', 'banned: "cures" (health context)'),
    (r'\bprevents\b(?=\s+(?:growth|disease|illness|health|dental|weight|joint|skin|allergy|digest))', 'may help with', 'banned: "prevents" (health context)'),
    (r'\btreats\b(?=\s+(?:disease|illness|condition|symptom|allergy|joint|skin|digest))', 'may be useful for', 'banned: "treats" (medical claim)'),
    (r'\bguaranteed\b(?=\s+(?:to\s+|healthy|nutrition|quality|growth|result|fresh))', 'designed to', 'banned: "guaranteed" (product context)'),
    (r'\bguarantees healthy growth\b', 'designed to support puppy development', 'banned: "guarantees healthy growth"'),
    (r'\bprevents growth problems\b', 'supports normal growth', 'banned: "prevents growth problems"'),
]

# Additional puppy-specific replacements for post 3839
PUPPY_SPECIFIC_REPLACEMENTS = [
    (r'\bprevents growth problems\b', 'supports normal growth', 'puppy-specific: "prevents growth problems"'),
    (r'\bguarantees healthy growth\b', 'designed to support puppy development', 'puppy-specific: "guarantees healthy growth"'),
]

# ── Global change log ─────────────────────────────────────────────────────
change_log = {}  # post_id -> list of change dicts


def log_change(post_id, task, original, replacement, context="", position=""):
    """Record a change in the log."""
    if post_id not in change_log:
        change_log[post_id] = []
    change_log[post_id].append({
        "task": task,
        "original_text": original[:200] if original else "",
        "replacement_text": replacement[:200] if replacement else "",
        "context": context[:300] if context else "",
        "position": position,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    })


def fetch_post(post_id):
    """Fetch post content from WP REST API."""
    url = f"{WP_BASE}/posts/{post_id}?context=edit"
    resp = requests.get(url, auth=AUTH, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data


def update_post_content(post_id, new_content):
    """Push updated content back via REST API, keeping draft status."""
    url = f"{WP_BASE}/posts/{post_id}"
    payload = {"content": new_content, "status": "draft"}
    resp = requests.post(url, auth=AUTH, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ═══════════════════════════════════════════════════════════════════════════
# TASK 1: Update price disclaimers (posts 3837, 3838)
# ═══════════════════════════════════════════════════════════════════════════

def task1_update_price_disclaimers(post_id, content):
    """Replace existing price disclaimers after price tables with new wording."""
    if post_id not in (3837, 3838):
        return content

    original_content = content

    # Pattern: find existing italic price disclaimers that appear after tables with £ signs
    # The existing disclaimers look like:
    # <p style="font-size:0.88em;color:#666;margin-top:4px;"><em>Prices are approximate...</em></p>
    old_disclaimer_pattern = re.compile(
        r'<p\s+style="[^"]*font-size:\s*0\.88em[^"]*">\s*<em>\s*Prices?\s+(?:are\s+)?approximate[^<]*</em>\s*</p>',
        re.IGNORECASE | re.DOTALL
    )

    matches = list(old_disclaimer_pattern.finditer(content))
    if matches:
        for match in reversed(matches):  # reverse to preserve positions
            old_text = match.group(0)
            content = content[:match.start()] + NEW_PRICE_DISCLAIMER + content[match.end():]
            log_change(post_id, "Task 1: Price Disclaimer", old_text, NEW_PRICE_DISCLAIMER,
                       "Replaced old price disclaimer after table with £ signs",
                       f"position {match.start()}")
    else:
        # No existing disclaimer found -- look for tables with £ signs and add after them
        table_pattern = re.compile(r'</table>', re.IGNORECASE)
        pound_table_pattern = re.compile(
            r'<table[^>]*>.*?</table>',
            re.IGNORECASE | re.DOTALL
        )
        tables_with_pounds = [m for m in pound_table_pattern.finditer(content) if '£' in m.group(0)]

        for table_match in reversed(tables_with_pounds):
            table_end = table_match.end()
            # Check if there's already a disclaimer right after
            after_table = content[table_end:table_end + 500]
            if "Product Evidence Register" not in after_table:
                content = content[:table_end] + "\n" + NEW_PRICE_DISCLAIMER + content[table_end:]
                log_change(post_id, "Task 1: Price Disclaimer", "(none)",
                           NEW_PRICE_DISCLAIMER,
                           "Added new price disclaimer after price table with £ signs",
                           f"position {table_end}")

    if content != original_content:
        print(f"  [Task 1] Post {post_id}: Price disclaimer(s) updated")
    else:
        print(f"  [Task 1] Post {post_id}: No price disclaimer changes needed")

    return content


# ═══════════════════════════════════════════════════════════════════════════
# TASK 2: Trust/compliance wording scan & fix (all 4 posts)
# ═══════════════════════════════════════════════════════════════════════════

def task2_banned_phrase_scan(post_id, content):
    """Scan and replace banned phrases in content body."""
    original_content = content
    total_replacements = 0

    for pattern_str, replacement, desc in BANNED_PHRASES:
        pattern = re.compile(pattern_str, re.IGNORECASE)
        matches = list(pattern.finditer(content))
        if matches:
            for match in reversed(matches):
                old_text = match.group(0)
                # Get surrounding context (50 chars each side)
                ctx_start = max(0, match.start() - 50)
                ctx_end = min(len(content), match.end() + 50)
                context = content[ctx_start:ctx_end]

                # Skip if the match is inside an HTML tag attribute or metadata div
                # We only want to replace in content body text
                before_text = content[max(0, match.start() - 200):match.start()]
                if '<div class="affiliate-disclosure"' in before_text and '</div>' not in before_text:
                    continue  # inside affiliate disclosure div

                if replacement:
                    # Preserve original case for first letter if applicable
                    if old_text[0].isupper() and replacement[0].islower():
                        actual_replacement = replacement[0].upper() + replacement[1:]
                    else:
                        actual_replacement = replacement
                    content = content[:match.start()] + actual_replacement + content[match.end():]
                else:
                    # Empty replacement - remove the phrase, clean up whitespace
                    content = content[:match.start()] + content[match.end():]

                log_change(post_id, f"Task 2: Banned Phrase ({desc})",
                           old_text, replacement if replacement else "(removed)",
                           context, f"position {match.start()}")
                total_replacements += 1

    # Check for "best product" without qualification
    best_product_pattern = re.compile(r'\bbest product\b', re.IGNORECASE)
    for match in best_product_pattern.finditer(content):
        ctx_start = max(0, match.start() - 100)
        ctx_end = min(len(content), match.end() + 100)
        context = content[ctx_start:ctx_end].lower()
        if 'based on' not in context and 'according to' not in context:
            log_change(post_id, "Task 2: Warning - 'best product' without qualification",
                       match.group(0), "(flagged - needs manual review)",
                       content[ctx_start:ctx_end], f"position {match.start()}")

    if total_replacements > 0:
        print(f"  [Task 2] Post {post_id}: {total_replacements} banned phrase(s) replaced")
    else:
        print(f"  [Task 2] Post {post_id}: No banned phrases found")

    return content


# ═══════════════════════════════════════════════════════════════════════════
# TASK 3: H1/Astra audit (all 4 posts)
# ═══════════════════════════════════════════════════════════════════════════

def task3_h1_astra_audit(post_id, content):
    """Check for manual H1 tags and heading hierarchy."""
    original_content = content

    # Find all H1 tags
    h1_pattern = re.compile(r'<h1[^>]*>(.*?)</h1>', re.IGNORECASE | re.DOTALL)
    h1_matches = list(h1_pattern.finditer(content))

    h1_count = len(h1_matches)

    if h1_count > 0:
        print(f"  [Task 3] Post {post_id}: Found {h1_count} manual <h1> tag(s) - removing (Astra provides H1)")
        for match in reversed(h1_matches):
            h1_text = match.group(1).strip()
            # Get the post title to check if H1 duplicates it
            post_title = POST_META.get(post_id, {}).get("kw", "")

            # Convert H1 to a styled intro paragraph if the text adds value
            # Check if it's essentially a duplicate of the post title
            h1_clean = re.sub(r'<[^>]+>', '', h1_text).strip()
            # The H1 likely duplicates the page title, so we can just remove it
            # since Astra auto-generates H1 from the post title
            replacement = ""

            # Check if there's a newline or content right after the H1
            after_h1 = content[match.end():match.end() + 5].strip()

            content = content[:match.start()] + replacement + content[match.end():]

            log_change(post_id, "Task 3: H1 Removal",
                       match.group(0)[:150],
                       "(removed - Astra generates H1 from post title)",
                       f"H1 text: {h1_clean[:100]}",
                       f"position {match.start()}")
    else:
        print(f"  [Task 3] Post {post_id}: No manual <h1> tags found (correct)")

    # Count H2s and H3s
    h2_pattern = re.compile(r'<h2[^>]*>(.*?)</h2>', re.IGNORECASE | re.DOTALL)
    h3_pattern = re.compile(r'<h3[^>]*>(.*?)</h3>', re.IGNORECASE | re.DOTALL)

    h2_matches = list(h2_pattern.finditer(content))
    h3_matches = list(h3_pattern.finditer(content))

    h2_count = len(h2_matches)
    h3_count = len(h3_matches)

    print(f"  [Task 3] Post {post_id}: {h2_count} H2s, {h3_count} H3s found")

    # Check heading hierarchy: H3s should come after H2s
    hierarchy_issues = []
    h2_positions = [m.start() for m in h2_matches]
    for h3_match in h3_matches:
        h3_pos = h3_match.start()
        # Find if there's an H2 before this H3
        h2_before = [p for p in h2_positions if p < h3_pos]
        if not h2_before:
            h3_text = re.sub(r'<[^>]+>', '', h3_match.group(1)).strip()
            hierarchy_issues.append(f"H3 '{h3_text[:50]}' appears before any H2")

    if hierarchy_issues:
        for issue in hierarchy_issues:
            print(f"  [Task 3] Post {post_id}: Hierarchy issue - {issue}")
            log_change(post_id, "Task 3: Heading Hierarchy Warning",
                       issue, "(flagged for review)", issue, "")
    else:
        print(f"  [Task 3] Post {post_id}: Heading hierarchy OK")

    # Check for over-optimized headings (keyword stuffing)
    kw = POST_META.get(post_id, {}).get("kw", "").lower()
    if kw:
        kw_in_headings = 0
        total_headings = h2_count + h3_count
        for m in h2_matches + h3_matches:
            heading_text = re.sub(r'<[^>]+>', '', m.group(1)).strip().lower()
            if kw in heading_text:
                kw_in_headings += 1

        if total_headings > 0:
            kw_ratio = kw_in_headings / total_headings
            if kw_ratio > 0.5:
                msg = f"Keyword '{kw}' appears in {kw_in_headings}/{total_headings} headings ({kw_ratio:.0%}) - may be over-optimized"
                print(f"  [Task 3] Post {post_id}: WARNING - {msg}")
                log_change(post_id, "Task 3: Keyword Stuffing Warning",
                           f"{kw_in_headings}/{total_headings} headings contain primary keyword",
                           "(flagged for review)", msg, "")
            else:
                print(f"  [Task 3] Post {post_id}: Keyword density in headings OK ({kw_in_headings}/{total_headings})")

    log_change(post_id, "Task 3: H1/Astra Audit Summary",
               f"H1: {h1_count} (removed: {h1_count}), H2: {h2_count}, H3: {h3_count}",
               "Audit complete", "", "")

    return content


# ═══════════════════════════════════════════════════════════════════════════
# TASK 4: Add missing content sections (posts 3837, 3839)
# ═══════════════════════════════════════════════════════════════════════════

def task4_add_missing_sections(post_id, content):
    """Add required content sections if missing."""
    if post_id == 3837:
        return task4_post_3837(content)
    elif post_id == 3839:
        return task4_post_3839(post_id, content)
    return content


def task4_post_3837(content):
    """Add missing sections to post 3837 (Best Dry Dog Food UK)."""
    post_id = 3837
    sections_added = 0

    # Check for "How We Research Dry Dog Food Information"
    if 'How We Research Dry Dog Food Information' not in content:
        # Insert before "Related Guides" section or at end
        insert_point = content.find('<h2>Related Guides</h2>')
        if insert_point == -1:
            insert_point = content.find('<h2>Frequently Asked Questions</h2>')
        if insert_point == -1:
            # Find last <hr /> before end
            last_hr = content.rfind('<hr />')
            insert_point = last_hr if last_hr != -1 else len(content)

        content = content[:insert_point] + SECTION_HOW_WE_RESEARCH_3837 + "\n" + content[insert_point:]
        sections_added += 1
        log_change(post_id, "Task 4: Added Section",
                   "(missing)", "How We Research Dry Dog Food Information",
                   "New H2 section about research methodology", f"before position {insert_point}")
        print(f"  [Task 4] Post {post_id}: Added 'How We Research Dry Dog Food Information' section")
    else:
        print(f"  [Task 4] Post {post_id}: 'How We Research...' section already exists")

    # Check for "What to Check on a UK Dog Food Label"
    if 'What to Check on a UK Dog Food Label' not in content:
        # Insert after the research methodology section
        research_pos = content.find('How We Research Dry Dog Food Information')
        if research_pos != -1:
            # Find next <hr /> after the research section
            next_section = content.find('<hr />', research_pos + 100)
            if next_section == -1:
                next_section = content.find('<h2>', research_pos + 100)
            if next_section == -1:
                next_section = len(content)
            content = content[:next_section] + SECTION_LABEL_READING_3837 + "\n" + content[next_section:]
        else:
            insert_point = content.find('<h2>Related Guides</h2>')
            if insert_point == -1:
                insert_point = len(content)
            content = content[:insert_point] + SECTION_LABEL_READING_3837 + "\n" + content[insert_point:]

        sections_added += 1
        log_change(post_id, "Task 4: Added Section",
                   "(missing)", "What to Check on a UK Dog Food Label",
                   "New H2 section about label reading guidance", "")
        print(f"  [Task 4] Post {post_id}: Added 'What to Check on a UK Dog Food Label' section")
    else:
        print(f"  [Task 4] Post {post_id}: 'What to Check...' section already exists")

    # Check for "When Dry Food May Not Be the Right Choice"
    if 'When Dry Food May Not Be the Right Choice' not in content:
        label_pos = content.find('What to Check on a UK Dog Food Label')
        if label_pos != -1:
            next_section = content.find('<hr />', label_pos + 100)
            if next_section == -1:
                next_section = content.find('<h2>', label_pos + 100)
            if next_section == -1:
                next_section = len(content)
            content = content[:next_section] + SECTION_WHEN_NOT_DRY_3837 + "\n" + content[next_section:]
        else:
            insert_point = content.find('<h2>Related Guides</h2>')
            if insert_point == -1:
                insert_point = len(content)
            content = content[:insert_point] + SECTION_WHEN_NOT_DRY_3837 + "\n" + content[insert_point:]

        sections_added += 1
        log_change(post_id, "Task 4: Added Section",
                   "(missing)", "When Dry Food May Not Be the Right Choice",
                   "New H2 section about alternatives to dry food", "")
        print(f"  [Task 4] Post {post_id}: Added 'When Dry Food May Not Be the Right Choice' section")
    else:
        print(f"  [Task 4] Post {post_id}: 'When Dry Food...' section already exists")

    # Check for "Evidence Status of Product Recommendations"
    if 'Evidence Status of Product Recommendations' not in content:
        dry_not_right_pos = content.find('When Dry Food May Not Be the Right Choice')
        if dry_not_right_pos != -1:
            next_section = content.find('<hr />', dry_not_right_pos + 100)
            if next_section == -1:
                next_section = content.find('<h2>', dry_not_right_pos + 100)
            if next_section == -1:
                next_section = len(content)
            content = content[:next_section] + SECTION_EVIDENCE_STATUS_3837 + "\n" + content[next_section:]
        else:
            insert_point = content.find('<h2>Related Guides</h2>')
            if insert_point == -1:
                insert_point = len(content)
            content = content[:insert_point] + SECTION_EVIDENCE_STATUS_3837 + "\n" + content[insert_point:]

        sections_added += 1
        log_change(post_id, "Task 4: Added Section",
                   "(missing)", "Evidence Status of Product Recommendations",
                   "New H2 section about evidence status", "")
        print(f"  [Task 4] Post {post_id}: Added 'Evidence Status of Product Recommendations' section")
    else:
        print(f"  [Task 4] Post {post_id}: 'Evidence Status...' section already exists")

    if sections_added == 0:
        print(f"  [Task 4] Post {post_id}: All required sections already present")

    return content


def task4_post_3839(post_id, content):
    """Handle post 3839 (Best Puppy Food UK) - health wording + disclaimer."""
    replacements_made = 0

    # Replace "prevents growth problems" -> "supports normal growth"
    pattern1 = re.compile(r'\bprevents growth problems\b', re.IGNORECASE)
    for match in reversed(list(pattern1.finditer(content))):
        old = match.group(0)
        new = 'supports normal growth'
        if old[0].isupper():
            new = new[0].upper() + new[1:]
        content = content[:match.start()] + new + content[match.end():]
        log_change(post_id, "Task 4: Puppy Health Wording",
                   old, new, "prevents growth problems -> supports normal growth",
                   f"position {match.start()}")
        replacements_made += 1

    # Replace "guarantees healthy growth" -> "designed to support puppy development"
    pattern2 = re.compile(r'\bguarantees healthy growth\b', re.IGNORECASE)
    for match in reversed(list(pattern2.finditer(content))):
        old = match.group(0)
        new = 'designed to support puppy development'
        if old[0].isupper():
            new = new[0].upper() + new[1:]
        content = content[:match.start()] + new + content[match.end():]
        log_change(post_id, "Task 4: Puppy Health Wording",
                   old, new, "guarantees healthy growth -> designed to support puppy development",
                   f"position {match.start()}")
        replacements_made += 1

    if replacements_made > 0:
        print(f"  [Task 4] Post {post_id}: {replacements_made} health wording replacement(s) made")
    else:
        print(f"  [Task 4] Post {post_id}: No sensitive health wording found to replace")

    # Add health disclaimer if not present
    if 'Dog food needs can vary by age, breed, activity level and health history' not in content:
        # Insert before Related Guides or FAQ section
        insert_before = content.find('<h2>Related Guides</h2>')
        if insert_before == -1:
            insert_before = content.find('<h2>Frequently Asked Questions</h2>')
        if insert_before == -1:
            last_hr = content.rfind('<hr />')
            insert_before = last_hr if last_hr != -1 else len(content)

        content = content[:insert_before] + "\n" + HEALTH_DISCLAIMER_3839 + "\n\n" + content[insert_before:]
        log_change(post_id, "Task 4: Health Disclaimer Added",
                   "(missing)", HEALTH_DISCLAIMER_3839[:150],
                   "Added health disclaimer about vet consultation", f"before position {insert_before}")
        print(f"  [Task 4] Post {post_id}: Health disclaimer added")
    else:
        print(f"  [Task 4] Post {post_id}: Health disclaimer already present")

    return content


# ═══════════════════════════════════════════════════════════════════════════
# TASK 5: Affiliate disclosure update (all 4 posts)
# ═══════════════════════════════════════════════════════════════════════════

def task5_affiliate_disclosure(post_id, content):
    """Update affiliate disclosure to client's preferred wording."""
    original_content = content

    # Pattern to match the affiliate disclosure div
    aff_pattern = re.compile(
        r'(<div\s+class="affiliate-disclosure"[^>]*>)\s*<strong>Affiliate Disclosure:</strong>\s*(.*?)(</div>)',
        re.IGNORECASE | re.DOTALL
    )

    match = aff_pattern.search(content)
    if match:
        old_text = match.group(2).strip()
        # Preserve the div wrapper and styling, just update the content
        new_div_content = (
            f'{match.group(1)}'
            f'<strong>Affiliate Disclosure:</strong> {NEW_AFFILIATE_DISCLOSURE} '
            f'<a href="https://pethubonline.com/affiliate-disclosure/" style="color:#0073aa;">Learn more</a>.'
            f'{match.group(3)}'
        )
        content = content[:match.start()] + new_div_content + content[match.end():]

        log_change(post_id, "Task 5: Affiliate Disclosure Update",
                   old_text[:150], NEW_AFFILIATE_DISCLOSURE[:150],
                   "Updated affiliate disclosure to client preferred wording",
                   f"position {match.start()}")
        print(f"  [Task 5] Post {post_id}: Affiliate disclosure updated")
    else:
        print(f"  [Task 5] Post {post_id}: No affiliate disclosure div found")

    return content


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("PHASE 8.4 REMEDIATION - PetHub Online Dog Food Posts")
    print(f"Started: {datetime.datetime.utcnow().isoformat()}Z")
    print("=" * 70)
    print()

    results = {}

    for post_id in POST_IDS:
        print(f"\n{'─' * 50}")
        print(f"Processing Post {post_id} ({POST_META[post_id]['slug']})")
        print(f"{'─' * 50}")

        # Fetch current content
        try:
            post_data = fetch_post(post_id)
        except Exception as e:
            print(f"  ERROR fetching post {post_id}: {e}")
            results[post_id] = {"status": "ERROR", "error": str(e)}
            continue

        content = post_data["content"]["raw"]
        title = post_data["title"]["raw"]
        status = post_data["status"]
        original_length = len(content)

        print(f"  Title: {title}")
        print(f"  Status: {status}")
        print(f"  Content length: {original_length} chars")
        print()

        # Run all 5 tasks in order
        print("  --- Task 1: Price Disclaimers ---")
        content = task1_update_price_disclaimers(post_id, content)

        print("  --- Task 2: Banned Phrase Scan ---")
        content = task2_banned_phrase_scan(post_id, content)

        print("  --- Task 3: H1/Astra Audit ---")
        content = task3_h1_astra_audit(post_id, content)

        print("  --- Task 4: Missing Sections ---")
        content = task4_add_missing_sections(post_id, content)

        print("  --- Task 5: Affiliate Disclosure ---")
        content = task5_affiliate_disclosure(post_id, content)

        # Push changes back
        new_length = len(content)
        if content != post_data["content"]["raw"]:
            try:
                updated = update_post_content(post_id, content)
                final_status = updated.get("status", "unknown")
                print(f"\n  >>> Post {post_id} UPDATED successfully (status: {final_status})")
                print(f"  >>> Content: {original_length} -> {new_length} chars ({new_length - original_length:+d})")
                results[post_id] = {
                    "status": "UPDATED",
                    "final_status": final_status,
                    "original_length": original_length,
                    "new_length": new_length,
                    "changes": len(change_log.get(post_id, [])),
                }
            except Exception as e:
                print(f"\n  ERROR updating post {post_id}: {e}")
                results[post_id] = {"status": "UPDATE_ERROR", "error": str(e)}
        else:
            print(f"\n  >>> Post {post_id}: No changes needed")
            results[post_id] = {
                "status": "NO_CHANGES",
                "original_length": original_length,
                "changes": len(change_log.get(post_id, [])),
            }

    # ── Save change log ────────────────────────────────────────────────────
    log_output = {
        "script": "phase84_remediation.py",
        "executed": datetime.datetime.utcnow().isoformat() + "Z",
        "posts_processed": POST_IDS,
        "changes_by_post": {},
        "summary": results,
    }

    for pid in POST_IDS:
        log_output["changes_by_post"][str(pid)] = change_log.get(pid, [])

    with open(CHANGE_LOG_PATH, "w") as f:
        json.dump(log_output, f, indent=2, ensure_ascii=False)

    print(f"\n\nChange log saved to: {CHANGE_LOG_PATH}")

    # ── Summary table ──────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Post ID':<10} {'Slug':<28} {'Status':<15} {'Changes':<10} {'Size Delta':<12}")
    print("-" * 70)

    for pid in POST_IDS:
        r = results.get(pid, {})
        slug = POST_META[pid]["slug"]
        status = r.get("status", "N/A")
        changes = r.get("changes", 0)
        if "original_length" in r and "new_length" in r:
            delta = f"{r['new_length'] - r['original_length']:+d} chars"
        elif "original_length" in r:
            delta = "0 chars"
        else:
            delta = "N/A"
        print(f"{pid:<10} {slug:<28} {status:<15} {changes:<10} {delta:<12}")

    print("-" * 70)

    # Detailed change log per post
    print("\n" + "=" * 70)
    print("DETAILED CHANGE LOG")
    print("=" * 70)

    for pid in POST_IDS:
        changes = change_log.get(pid, [])
        if changes:
            print(f"\nPost {pid} ({POST_META[pid]['slug']}) - {len(changes)} change(s):")
            for i, c in enumerate(changes, 1):
                print(f"  {i}. [{c['task']}]")
                if c['original_text']:
                    print(f"     Original: {c['original_text'][:120]}...")
                if c['replacement_text']:
                    print(f"     Replaced: {c['replacement_text'][:120]}...")
                if c['context']:
                    print(f"     Context:  {c['context'][:120]}...")
                if c['position']:
                    print(f"     Position: {c['position']}")
        else:
            print(f"\nPost {pid} ({POST_META[pid]['slug']}): No changes recorded")

    print("\n" + "=" * 70)
    print(f"Phase 8.4 remediation complete at {datetime.datetime.utcnow().isoformat()}Z")
    print("All posts remain in DRAFT status.")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
