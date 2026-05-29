#!/usr/bin/env python3
"""
Final fixes for remaining 15 posts:
- 4 posts with trust footer at top: strip misplaced footer, add missing blocks
- 11 posts missing At a Glance: add the block
"""
import subprocess, json, tempfile, os, time, re, csv
from datetime import datetime

API_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ai_data"
LOG_FILE = os.path.join(DATA_DIR, "batch4_grooming_harness_beds_log.csv")
DELAY = 2.5

import importlib.util
spec = importlib.util.spec_from_file_location("v2", os.path.join(DATA_DIR, "batch4_enhance_v2.py"))
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)


def api_get(endpoint):
    url = f"{API_BASE}/{endpoint}"
    r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, url], capture_output=True, text=True, timeout=60)
    return json.loads(r.stdout)


def api_post(endpoint, data):
    url = f"{API_BASE}/{endpoint}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f, ensure_ascii=False)
        tmppath = f.name
    try:
        r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, "-X", "POST", "-H", "Content-Type: application/json", "-d", f"@{tmppath}", url], capture_output=True, text=True, timeout=60)
        return json.loads(r.stdout)
    finally:
        os.unlink(tmppath)


def find_clean_revision(post_id):
    revisions = api_get(f"posts/{post_id}/revisions?per_page=25&_fields=id,date")
    for rev in revisions:
        if rev['date'] < '2026-05-28T23:50':
            time.sleep(1)
            rd = api_get(f"posts/{post_id}/revisions/{rev['id']}?_fields=content")
            rc = rd.get('content', {}).get('rendered', '') or rd.get('content', {}).get('raw', '')
            if len(rc) > 5000:
                return rc, rev['id'], rev['date']
    return None, None, None


def remove_all_editorial(content):
    content = re.sub(r'<!-- wp:group[^>]*-->\s*<div[^>]*>.*?Our Editorial Standards.*?</div>\s*<!-- /wp:group -->', '', content, flags=re.DOTALL)
    content = re.sub(r'<div[^>]*class="wp-block-group[^"]*"[^>]*>\s*<h4[^>]*>\s*Our Editorial Standards\s*</h4>\s*<p[^>]*>.*?</p>\s*</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'(?:<!-- wp:heading[^>]*-->\s*)?<h3[^>]*>\s*About Our Editorial Standards\s*</h3>\s*(?:<!-- /wp:heading -->\s*)?(?:<!-- wp:paragraph[^>]*-->\s*)?<p[^>]*>.*?(?:corrections|editorial).*?</p>\s*(?:<!-- /wp:paragraph -->\s*)?', '', content, flags=re.DOTALL)
    content = re.sub(r'(?:<!-- wp:separator[^>]*-->\s*)?<hr[^>]*/>\s*(?:<!-- /wp:separator -->\s*)?(?:<!-- wp:paragraph[^>]*-->\s*)?<p[^>]*>.*?(?:editorial process|how we create).*?(?:affiliate|corrections).*?</p>\s*(?:<!-- /wp:paragraph -->\s*)?', '', content, flags=re.DOTALL | re.IGNORECASE)
    return re.sub(r'\n{4,}', '\n\n\n', content).strip()


# Group 1: 4 posts with TOP_FOOTER - need full restore + enhance
TOP_FOOTER_POSTS = [
    (4078, "Best Dog Nail Clippers UK (2026) – Trimming & Grinding Guide", "Dog Grooming"),
    (4071, "Best Dog Shampoo UK (2026) – Ingredients & Safety Guide", "Dog Grooming"),
    (4064, "Best Dog Brushes UK (2026) – Guide by Coat Type", "Dog Grooming"),
    (4057, "Best Dog Grooming Supplies UK (2026) – Complete Guide", "Dog Grooming"),
]

# Group 2: 11 posts missing just At a Glance
MISSING_AAG = [
    (4230, "Best Cat Grooming Supplies UK (2026) – Complete Guide", "Dog Grooming"),
    (4272, "Best Cat ID Tags UK (2026) – Identification Guide", "Educational"),
    (4265, "Best Cat GPS Trackers UK (2026) – Location Tracking Guide", "Educational"),
    (4216, "Best Cat Radiator Beds UK (2026) – Hook-On Warmth Guide", "Educational"),
    (4167, "Best Dog Water Bottles UK (2026) – Travel Hydration Guide", "Educational"),
    (4160, "Best Elevated Dog Bowls UK (2026) – Raised Feeder Guide", "Educational"),
    (4146, "Best Dog Bowls and Feeding UK (2026) – Complete Guide", "Educational"),
    (4328, "Best Self-Cleaning Litter Trays UK (2026) – Automatic Options", "Uncategorized"),
    (4293, "Best Cat Trees UK (2026) – Climbing & Scratching Towers", "Uncategorized"),
    (4223, "Best Cat Window Perches UK (2026) – Sunning & Bird Watching", "Uncategorized"),
    (4153, "Best Slow Feeder Dog Bowls UK (2026) – Prevent Speed Eating", "Uncategorized"),
]


def full_restore_enhance(post_id, title, cluster):
    """Restore from clean revision and fully enhance."""
    print(f"  Finding clean revision...")
    clean_content, rev_id, rev_date = find_clean_revision(post_id)
    if not clean_content:
        return "NO_REVISION", "No clean revision found", []

    print(f"  Using rev {rev_id} ({rev_date}), {len(clean_content)} chars")

    # Remove any existing editorial sections
    content = remove_all_editorial(clean_content)
    blocks_added = []

    # Add At a Glance
    bullets = v2.generate_at_a_glance(post_id, title, cluster)
    block = v2.build_at_a_glance(bullets)
    insert_pos = v2.find_first_paragraph_end(content)
    if insert_pos > 0:
        content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
        blocks_added.append("at_a_glance")

    # Why this matters
    text = v2.generate_why_matters(post_id, title, cluster)
    block = v2.build_why_matters(text)
    aag_match = re.search(r'<!-- /wp:group -->', content)
    if aag_match:
        insert_pos = aag_match.end()
    else:
        insert_pos = v2.find_first_paragraph_end(content)
    content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
    blocks_added.append("why_this_matters")

    # What we considered (buying guides)
    if v2.is_buying_guide(title):
        ct = v2.generate_what_we_considered(post_id, title, cluster)
        if ct:
            block = v2.build_what_we_considered(ct)
            wtm_pos = content.find("Why this matters")
            if wtm_pos >= 0:
                after = content[wtm_pos:]
                ge = after.find("<!-- /wp:group -->")
                if ge >= 0:
                    insert_pos = wtm_pos + ge + len("<!-- /wp:group -->")
                    content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                    blocks_added.append("what_we_considered")

    # Troubleshooting
    if 'Troubleshooting Common Issues' not in content:
        tt = v2.generate_troubleshooting(post_id, title, cluster)
        block = v2.build_troubleshooting(tt)
        faq_pos = v2.find_faq_position(content)
        if faq_pos:
            content = content[:faq_pos] + block + "\n\n" + content[faq_pos:]
        else:
            content = content.rstrip() + "\n\n" + block
        blocks_added.append("troubleshooting")

    # When to seek help
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

    # Key Takeaways
    bullets = v2.generate_key_takeaways(post_id, title, cluster)
    block = v2.build_key_takeaways(bullets)
    content = content.rstrip() + "\n\n" + block
    blocks_added.append("key_takeaways")

    # Trust footer at end
    footer = v2.get_trust_footer(cluster, post_id, title)
    content = content.rstrip() + "\n\n" + footer
    blocks_added.append("trust_footer")

    # Save
    time.sleep(DELAY)
    result = api_post(f"posts/{post_id}", {"content": content})
    if "id" in result:
        return "OK", f"rev{rev_id}:{len(clean_content)}->{len(content)}", blocks_added
    else:
        return "ERROR", result.get("message", str(result)[:200]), blocks_added


def add_at_a_glance(post_id, title, cluster):
    """Add just the At a Glance block to a post that's otherwise complete."""
    data = api_get(f"posts/{post_id}?context=edit")
    content = data.get("content", {}).get("raw", "")
    original_len = len(content)

    # Check if there's already an h4 At a Glance
    has_h4_aag = bool(re.search(r'<h4[^>]*>\s*At a Glance\s*</h4>', content))
    if has_h4_aag:
        return "SKIP", "Already has At a Glance h4", []

    bullets = v2.generate_at_a_glance(post_id, title, cluster)
    block = v2.build_at_a_glance(bullets)

    insert_pos = v2.find_first_paragraph_end(content)
    if insert_pos > 0:
        content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]

        time.sleep(DELAY)
        result = api_post(f"posts/{post_id}", {"content": content})
        if "id" in result:
            return "OK", f"{original_len}->{len(content)}", ["at_a_glance"]
        else:
            return "ERROR", result.get("message", str(result)[:200]), []
    else:
        return "SKIP", "No paragraph found for insertion", []


def main():
    total = len(TOP_FOOTER_POSTS) + len(MISSING_AAG)
    done = 0
    errors = 0

    print(f"Final fix: {total} posts ({len(TOP_FOOTER_POSTS)} full restore, {len(MISSING_AAG)} add AAG)")
    print("=" * 70)

    # Group 1: Full restore + enhance
    print("\n--- Full Restore Posts ---")
    for pid, title, cluster in TOP_FOOTER_POSTS:
        done += 1
        print(f"\n[{done}/{total}] #{pid}: {title[:50]}...")
        try:
            status, detail, blocks = full_restore_enhance(pid, title, cluster)
            print(f"  -> {status} | {detail}")
            if status != "OK":
                errors += 1
            with open(LOG_FILE, 'a', newline='') as f:
                csv.writer(f).writerow([datetime.now().isoformat(), pid, title, cluster, status, detail, ",".join(blocks)])
        except Exception as e:
            errors += 1
            print(f"  -> EXCEPTION: {str(e)[:200]}")
        time.sleep(DELAY)

    # Group 2: Add At a Glance
    print("\n--- Add At a Glance ---")
    for pid, title, cluster in MISSING_AAG:
        done += 1
        print(f"\n[{done}/{total}] #{pid}: {title[:50]}...")
        try:
            status, detail, blocks = add_at_a_glance(pid, title, cluster)
            print(f"  -> {status} | {detail}")
            if status not in ("OK", "SKIP"):
                errors += 1
            with open(LOG_FILE, 'a', newline='') as f:
                csv.writer(f).writerow([datetime.now().isoformat(), pid, title, cluster, status, detail, ",".join(blocks)])
        except Exception as e:
            errors += 1
            print(f"  -> EXCEPTION: {str(e)[:200]}")
        time.sleep(DELAY)

    print(f"\n{'=' * 70}")
    print(f"COMPLETE: {done} processed, {errors} errors")


if __name__ == "__main__":
    main()
