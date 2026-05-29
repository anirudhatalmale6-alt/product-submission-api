#!/usr/bin/env python3
"""
Phase 10AI Batch 4 v3: Restore posts from pre-batch revisions, then enhance.

Strategy:
1. For each post, find the revision from BEFORE any Phase 10AI runs
   (before 2026-05-29 00:25 UTC - the earliest batch)
2. Restore that content
3. Apply all blocks cleanly to the original content
"""
import subprocess, json, tempfile, os, time, re, csv
from datetime import datetime

API_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ai_data"
LOG_FILE = os.path.join(DATA_DIR, "batch4_grooming_harness_beds_log.csv")
DELAY = 2.5

# Import from v2
import importlib.util
spec = importlib.util.spec_from_file_location("v2", os.path.join(DATA_DIR, "batch4_enhance_v2.py"))
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)

# Posts that need restoration + enhancement (TOP_FOOTER or PARTIAL from verification)
NEEDS_FIX = [
    # Dog Grooming
    (5464, "Pet Grooming Glossary: Understanding Grooming Terms and Techniques", "Dog Grooming"),
    (4563, "Dog Grooming Basics: A Complete Guide for Owners", "Dog Grooming"),
    (4078, "Best Dog Nail Clippers UK (2026) – Trimming & Grinding Guide", "Dog Grooming"),
    (4071, "Best Dog Shampoo UK (2026) – Ingredients & Safety Guide", "Dog Grooming"),
    (4064, "Best Dog Brushes UK (2026) – Guide by Coat Type", "Dog Grooming"),
    (4057, "Best Dog Grooming Supplies UK (2026) – Complete Guide", "Dog Grooming"),
    # Dog Harnesses
    (5418, "Dog Harness Types Explained: Finding the Right Fit", "Dog Harnesses"),
    (4414, "Harness vs Collar: Which Is Better for Your Dog?", "Dog Harnesses"),
    (4413, "How to Measure Your Dog for a Harness: Step-by-Step Guide", "Dog Harnesses"),
    (4412, "No-Pull Dog Harness Guide: How They Work and When to Use One", "Dog Harnesses"),
    (4279, "Best Cat Harnesses UK (2026) – Safe Walking Guide", "Dog Harnesses"),
    (4258, "Best Cat Collars UK (2026) – Complete Safety Guide", "Dog Harnesses"),
    (4139, "Best Dog Training Leads UK (2026) – Long Lines & Harnesses", "Dog Harnesses"),
    (4042, "Best Dog Leads UK (2026) – Walking & Training Lead Guide", "Dog Harnesses"),
    (4034, "Best No-Pull Dog Harnesses UK (2026) – Training & Comfort Guide", "Dog Harnesses"),
    (4027, "Best Dog Collars and Harnesses UK (2026) – Complete Guide", "Dog Harnesses"),
    # Dog Beds
    (5510, "Dog Bed Sizing Guide: How to Measure Your Dog and Choose the Right Fit", "Dog Beds"),
    (4783, "How to Choose the Right Dog Bed Size", "Dog Beds"),
    (4011, "Best Cooling Dog Beds UK (2026) – Temperature Regulation Guide", "Dog Beds"),
    (4004, "Best Orthopaedic Dog Beds UK (2026) – Joint Support Guide", "Dog Beds"),
    (3996, "Best Dog Beds UK (2026) – Complete Guide & Honest Reviews", "Dog Beds"),
    # Educational
    (5521, "Pet Health Terminology: A Guide to Common Veterinary Terms", "Educational"),
    (5424, "Aggressive Chewer Guide: Safe Toys for Power Chewers", "Educational"),
    (5419, "Cat Care Basics: A Glossary for New Cat Owners", "Educational"),
    (5415, "Dog Play Styles Explained: Understanding How Your Dog Plays", "Educational"),
    (5414, "Cat Toy Types Explained: A Complete Glossary", "Educational"),
    # Uncategorized
    (6048, "Confidence-Building Play: Helping Shy and Fearful Dogs Through Toys", "Uncategorized"),
    (6044, "Rotating Puzzle Complexity: Progressive Challenge for Smart Dogs", "Uncategorized"),
    (4573, "Seasonal Pet Safety: Protecting Pets Through the Year", "Uncategorized"),
    (4576, "Multi-Pet Household Tips: Living with Dogs and Cats Together", "Uncategorized"),
]


def api_get(endpoint):
    url = f"{API_BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    return json.loads(result.stdout)


def api_post(endpoint, data):
    url = f"{API_BASE}/{endpoint}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f, ensure_ascii=False)
        tmppath = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST", "-H", "Content-Type: application/json",
             "-d", f"@{tmppath}", url],
            capture_output=True, text=True, timeout=60
        )
        return json.loads(result.stdout)
    finally:
        os.unlink(tmppath)


def find_clean_revision(post_id):
    """Find a revision from before any Phase 10AI runs.

    We look for the latest revision before 2026-05-28T23:50 (before any batch).
    If not found, we look for the latest revision where the editorial standards
    section is NOT at the top and content is substantial.
    """
    revisions = api_get(f"posts/{post_id}/revisions?per_page=20&_fields=id,date")

    # Strategy 1: Find revision before any of our runs
    for rev in revisions:
        if rev['date'] < '2026-05-28T23:50':
            time.sleep(1)
            rev_data = api_get(f"posts/{post_id}/revisions/{rev['id']}?_fields=content")
            rc = rev_data.get('content', {}).get('rendered', '') or rev_data.get('content', {}).get('raw', '')
            if len(rc) > 5000:
                return rc, rev['id'], rev['date']

    # Strategy 2: Find most recent revision with editorial NOT at top
    for rev in revisions:
        time.sleep(1)
        rev_data = api_get(f"posts/{post_id}/revisions/{rev['id']}?_fields=content")
        rc = rev_data.get('content', {}).get('rendered', '') or rev_data.get('content', {}).get('raw', '')
        if len(rc) < 5000:
            continue
        es_pos = rc.lower().find('our editorial standards')
        about_es_pos = rc.lower().find('about our editorial standards')
        # Check editorial is in the latter half or not present
        if es_pos < 0 or es_pos > len(rc) * 0.5:
            if about_es_pos < 0 or about_es_pos > len(rc) * 0.5:
                return rc, rev['id'], rev['date']

    return None, None, None


def remove_all_editorial(content):
    """Remove ALL editorial/trust sections from content."""
    # Gutenberg wrapped
    content = re.sub(
        r'<!-- wp:group[^>]*-->\s*<div[^>]*>.*?Our Editorial Standards.*?</div>\s*<!-- /wp:group -->',
        '', content, flags=re.DOTALL
    )
    # Rendered div
    content = re.sub(
        r'<div[^>]*class="wp-block-group[^"]*"[^>]*>\s*<h4[^>]*>\s*Our Editorial Standards\s*</h4>\s*<p[^>]*>.*?</p>\s*</div>',
        '', content, flags=re.DOTALL
    )
    # Old h3 About Our Editorial Standards
    content = re.sub(
        r'(?:<!-- wp:heading[^>]*-->\s*)?<h3[^>]*>\s*About Our Editorial Standards\s*</h3>\s*(?:<!-- /wp:heading -->\s*)?(?:<!-- wp:paragraph[^>]*-->\s*)?<p[^>]*>.*?(?:corrections|editorial).*?</p>\s*(?:<!-- /wp:paragraph -->\s*)?',
        '', content, flags=re.DOTALL
    )
    # Old separator + editorial
    content = re.sub(
        r'(?:<!-- wp:separator[^>]*-->\s*)?<hr[^>]*/>\s*(?:<!-- /wp:separator -->\s*)?(?:<!-- wp:paragraph[^>]*-->\s*)?<p[^>]*>.*?(?:editorial process|how we create).*?(?:affiliate|corrections).*?</p>\s*(?:<!-- /wp:paragraph -->\s*)?',
        '', content, flags=re.DOTALL | re.IGNORECASE
    )
    return re.sub(r'\n{4,}', '\n\n\n', content).strip()


def enhance_content(content, post_id, title, cluster):
    """Add all enhancement blocks to clean content."""
    blocks_added = []

    # Remove any existing editorial sections first
    content = remove_all_editorial(content)

    # 1. AT A GLANCE
    if 'at a glance' not in content.lower().replace('at a glance', '', 1).lower():
        # Check more carefully - avoid matching table headings like "X: At a Glance"
        has_aag_block = bool(re.search(r'<h4[^>]*>\s*At a Glance\s*</h4>', content))
        if not has_aag_block:
            bullets = v2.generate_at_a_glance(post_id, title, cluster)
            block = v2.build_at_a_glance(bullets)
            insert_pos = v2.find_first_paragraph_end(content)
            if insert_pos > 0:
                content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                blocks_added.append("at_a_glance")

    # 2. WHY THIS MATTERS
    if 'Why this matters' not in content:
        text = v2.generate_why_matters(post_id, title, cluster)
        block = v2.build_why_matters(text)
        # Insert after At a Glance if present
        aag_match = re.search(r'<h4[^>]*>\s*At a Glance\s*</h4>', content)
        if aag_match:
            after = content[aag_match.start():]
            ge = after.find("<!-- /wp:group -->")
            if ge >= 0:
                insert_pos = aag_match.start() + ge + len("<!-- /wp:group -->")
            else:
                de = after.find("</div>")
                insert_pos = aag_match.start() + de + len("</div>") if de >= 0 else v2.find_first_paragraph_end(content)
        else:
            insert_pos = v2.find_first_paragraph_end(content)
        content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
        blocks_added.append("why_this_matters")

    # 3. WHAT WE CONSIDERED (buying guides)
    if v2.is_buying_guide(title) and 'What we considered' not in content:
        ct = v2.generate_what_we_considered(post_id, title, cluster)
        if ct:
            block = v2.build_what_we_considered(ct)
            wtm_pos = content.find("Why this matters")
            if wtm_pos >= 0:
                after = content[wtm_pos:]
                ge = after.find("<!-- /wp:group -->")
                if ge >= 0:
                    insert_pos = wtm_pos + ge + len("<!-- /wp:group -->")
                else:
                    de = after.find("</div>")
                    insert_pos = wtm_pos + de + len("</div>") if de >= 0 else v2.find_first_paragraph_end(content)
            else:
                insert_pos = v2.find_first_paragraph_end(content)
            content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
            blocks_added.append("what_we_considered")

    # 4. TROUBLESHOOTING
    if 'Troubleshooting Common Issues' not in content:
        tt = v2.generate_troubleshooting(post_id, title, cluster)
        block = v2.build_troubleshooting(tt)
        faq_pos = v2.find_faq_position(content)
        if faq_pos:
            content = content[:faq_pos] + block + "\n\n" + content[faq_pos:]
        else:
            content = content.rstrip() + "\n\n" + block
        blocks_added.append("troubleshooting")

    # 5. WHEN TO SEEK HELP
    if 'When to seek professional help' not in content:
        st = v2.generate_when_to_seek_help(post_id, title, cluster)
        block = v2.build_when_to_seek_help(st)
        tp = content.find("Troubleshooting Common Issues")
        if tp >= 0:
            after = content[tp:]
            pe = after.find("<!-- /wp:paragraph -->")
            if pe >= 0:
                insert_pos = tp + pe + len("<!-- /wp:paragraph -->")
            else:
                p_ends = [m.end() for m in re.finditer(r'</p>', after)]
                insert_pos = tp + p_ends[0] if p_ends else len(content)
        else:
            insert_pos = len(content)
        content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
        blocks_added.append("when_to_seek_help")

    # 6. KEY TAKEAWAYS
    if 'Key Takeaways' not in content:
        tb = v2.generate_key_takeaways(post_id, title, cluster)
        block = v2.build_key_takeaways(tb)
        content = content.rstrip() + "\n\n" + block
        blocks_added.append("key_takeaways")

    # 7. TRUST FOOTER at the very end
    footer = v2.get_trust_footer(cluster, post_id, title)
    content = content.rstrip() + "\n\n" + footer
    blocks_added.append("trust_footer")

    return content, blocks_added


def process_post(post_id, title, cluster):
    """Restore from clean revision and enhance."""
    # Step 1: Find clean revision
    print(f"  Finding clean revision...")
    clean_content, rev_id, rev_date = find_clean_revision(post_id)

    if not clean_content:
        return "NO_REVISION", "Could not find clean revision", []

    print(f"  Using revision {rev_id} ({rev_date}), {len(clean_content)} chars")

    # Step 2: Enhance
    enhanced, blocks_added = enhance_content(clean_content, post_id, title, cluster)
    print(f"  Enhanced: {len(clean_content)} -> {len(enhanced)} chars, blocks: {','.join(blocks_added)}")

    # Sanity check
    if len(enhanced) < len(clean_content) * 0.8:
        return "SANITY_FAIL", f"{len(clean_content)}->{len(enhanced)}", blocks_added

    # Step 3: Save
    time.sleep(DELAY)
    result = api_post(f"posts/{post_id}", {"content": enhanced})

    if "id" in result:
        return "OK", f"rev{rev_id}:{len(clean_content)}->{len(enhanced)}", blocks_added
    else:
        return "ERROR", result.get("message", str(result)[:200]), blocks_added


def main():
    # Overwrite log
    with open(LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "post_id", "title", "cluster", "status", "detail", "blocks_added"])

    total = len(NEEDS_FIX)
    done = 0
    errors = 0

    print(f"Phase 10AI Batch 4 v3: Restoring & enhancing {total} posts")
    print("=" * 70)

    for post_id, title, cluster in NEEDS_FIX:
        done += 1
        short = title[:50] + "..." if len(title) > 50 else title
        print(f"\n[{done}/{total}] #{post_id}: {short}")

        try:
            status, detail, blocks = process_post(post_id, title, cluster)
            bs = ",".join(blocks) if blocks else "none"
            print(f"  -> {status} | {detail}")

            if status != "OK":
                errors += 1

            with open(LOG_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([datetime.now().isoformat(), post_id, title, cluster, status, detail, bs])

        except Exception as e:
            errors += 1
            print(f"  -> EXCEPTION: {str(e)[:200]}")
            with open(LOG_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([datetime.now().isoformat(), post_id, title, cluster, "EXCEPTION", str(e)[:200], ""])

        time.sleep(DELAY)

    print(f"\n{'=' * 70}")
    print(f"COMPLETE: {done} processed, {errors} issues")


if __name__ == "__main__":
    main()
