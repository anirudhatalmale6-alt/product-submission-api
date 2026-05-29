#!/usr/bin/env python3
"""
Phase 10AI Batch 3 FIX: Add missing blocks that failed due to content format issues.
Handles both Gutenberg comment blocks and class-based HTML paragraphs.
"""

import csv
import json
import os
import re
import subprocess
import tempfile
import time
import html

# ── credentials ──
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ai_data"
LOG_FILE = os.path.join(DATA_DIR, "batch3_cat_clusters_log.csv")
FIX_LOG_FILE = os.path.join(DATA_DIR, "batch3_cat_fix_log.csv")


def api_get(endpoint):
    url = f"{WP_BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise Exception(f"curl GET failed: {result.stderr}")
    return json.loads(result.stdout)


def api_post(endpoint, data):
    url = f"{WP_BASE}/{endpoint}"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        tmpfile = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST", "-H", "Content-Type: application/json",
             "-d", f"@{tmpfile}", url],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            raise Exception(f"curl POST failed: {result.stderr}")
        resp = json.loads(result.stdout)
        if "id" not in resp:
            raise Exception(f"Update failed: {json.dumps(resp)[:500]}")
        return resp
    finally:
        os.unlink(tmpfile)


def has_block(content, marker):
    return marker.lower() in content.lower()


def find_first_para_end(content):
    """Find end of first paragraph - handles both <!-- /wp:paragraph --> and </p> formats."""
    # Try Gutenberg comment first
    m = re.search(r'<!-- /wp:paragraph -->', content)
    if m and m.start() < 1000:
        return m.end()
    # Fall back to first </p> tag
    m = re.search(r'</p>', content)
    if m:
        return m.end()
    return 0


def find_second_para_end(content):
    """Find end of second paragraph."""
    first_end = find_first_para_end(content)
    if first_end == 0:
        return 0
    rest = content[first_end:]
    # Skip whitespace and look for next paragraph end
    m = re.search(r'</p>', rest)
    if m:
        return first_end + m.end()
    m = re.search(r'<!-- /wp:paragraph -->', rest)
    if m:
        return first_end + m.end()
    return 0


def find_faq_or_sources_position(content):
    """Find position before FAQ, Sources, or similar end-section heading."""
    patterns = [
        r'<h[23][^>]*>\s*(?:FAQ|Frequently Asked Questions)',
        r'<h[23][^>]*>\s*(?:Common Questions|Questions and Answers)',
        r'<h[23][^>]*>\s*Sources and Further Reading',
        r'<h[23][^>]*>\s*Related Reading',
        r'<h[23][^>]*>\s*(?:Common Mistakes)',
        r'<h[23][^>]*>\s*(?:Quick Suitability Guide)',
    ]
    best_pos = None
    for pat in patterns:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            # Find the start of the wp:heading comment if it exists before this
            preceding = content[max(0, m.start()-50):m.start()]
            heading_comment = preceding.rfind("<!-- wp:heading")
            if heading_comment >= 0:
                actual_pos = max(0, m.start()-50) + heading_comment
            else:
                actual_pos = m.start()
            if best_pos is None or actual_pos < best_pos:
                best_pos = actual_pos
    return best_pos


def find_key_takeaways_position(content):
    """Find position of Key Takeaways block."""
    m = re.search(r'Key Takeaways', content)
    if m:
        # Walk backwards to find group start
        preceding = content[max(0, m.start()-300):m.start()]
        group_start = preceding.rfind("<!-- wp:group")
        if group_start >= 0:
            return max(0, m.start()-300) + group_start
        # Try div start
        div_start = preceding.rfind('<div class="wp-block-group')
        if div_start >= 0:
            return max(0, m.start()-300) + div_start
    return None


def find_about_editorial_or_trust(content):
    """Find position of 'About Our Editorial Standards' or trust footer block."""
    patterns = [
        r'<h[34][^>]*>\s*About Our Editorial Standards',
        r'<h[34][^>]*>\s*Our Editorial Standards',
    ]
    for pat in patterns:
        m = re.search(pat, content)
        if m:
            # Walk backwards
            preceding = content[max(0, m.start()-300):m.start()]
            group_start = preceding.rfind("<!-- wp:group")
            if group_start >= 0:
                return max(0, m.start()-300) + group_start
            div_start = preceding.rfind('<div class="wp-block-group')
            if div_start >= 0:
                return max(0, m.start()-300) + div_start
            return m.start()
    return None


# Import content generators from main script
import importlib.util
spec = importlib.util.spec_from_file_location("batch3", os.path.join(DATA_DIR, "batch3_cat_enhance.py"))
batch3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch3)


def process_fix(post_id, title, cluster, original_log):
    """Fix missing blocks in a post."""
    title_clean = html.unescape(title)
    log = {
        "id": post_id,
        "title": title_clean,
        "cluster": cluster,
        "at_a_glance": original_log.get("at_a_glance", "skip"),
        "why_this_matters": original_log.get("why_this_matters", "skip"),
        "what_we_considered": original_log.get("what_we_considered", "skip"),
        "troubleshooting": original_log.get("troubleshooting", "skip"),
        "when_to_seek_help": original_log.get("when_to_seek_help", "skip"),
        "key_takeaways": original_log.get("key_takeaways", "skip"),
        "trust_upgraded": original_log.get("trust_upgraded", "skip"),
        "status": "no_fix_needed"
    }

    # Determine what needs fixing
    needs_fix = False
    for field in ["at_a_glance", "why_this_matters", "what_we_considered", "troubleshooting", "when_to_seek_help"]:
        if original_log.get(field) in ("no_insert_point", "no_faq_section"):
            needs_fix = True
            break

    if not needs_fix:
        return log

    try:
        print(f"  Fetching post {post_id}...")
        data = api_get(f"posts/{post_id}?context=edit")
        content = data["content"]["raw"]
        time.sleep(2)

        modified = False

        # 1. AT A GLANCE
        if original_log.get("at_a_glance") == "no_insert_point" and not has_block(content, "At a Glance"):
            bullets = batch3.gen_at_a_glance(title_clean, content)
            block = batch3.build_at_a_glance_block(bullets)
            insert_pos = find_first_para_end(content)
            if insert_pos > 0:
                content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                log["at_a_glance"] = "fixed"
                modified = True
            else:
                log["at_a_glance"] = "still_no_insert"

        # 2. WHY THIS MATTERS
        if original_log.get("why_this_matters") == "no_insert_point" and not has_block(content, "Why this matters"):
            text = batch3.gen_why_this_matters(title_clean, cluster)
            block = batch3.build_why_this_matters_block(text)
            # Place after At a Glance if it exists
            aag_pos = content.find("At a Glance")
            if aag_pos >= 0:
                # Find end of the At a Glance wp:group
                group_end = content.find("<!-- /wp:group -->", aag_pos)
                if group_end >= 0:
                    insert_pos = group_end + len("<!-- /wp:group -->")
                else:
                    # Try </div> as the group end
                    div_end = content.find("</div>", aag_pos)
                    if div_end >= 0:
                        # Find the matching /wp:group after the </div>
                        after_div = content.find("<!-- /wp:group -->", div_end)
                        if after_div >= 0 and after_div < div_end + 100:
                            insert_pos = after_div + len("<!-- /wp:group -->")
                        else:
                            insert_pos = div_end + len("</div>")
                    else:
                        insert_pos = None

                if insert_pos:
                    content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                    log["why_this_matters"] = "fixed"
                    modified = True
                else:
                    log["why_this_matters"] = "still_no_insert"
            else:
                # Place after second paragraph
                insert_pos = find_second_para_end(content)
                if insert_pos > 0:
                    content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                    log["why_this_matters"] = "fixed"
                    modified = True
                else:
                    log["why_this_matters"] = "still_no_insert"

        # 3. WHAT WE CONSIDERED
        if original_log.get("what_we_considered") == "no_insert_point" and not has_block(content, "What we considered"):
            criteria_text = batch3.gen_what_we_considered(title_clean)
            if criteria_text:
                block = batch3.build_what_we_considered_block(criteria_text)
                # Place after Why This Matters
                wtm_pos = content.find("Why this matters")
                if wtm_pos >= 0:
                    group_end = content.find("<!-- /wp:group -->", wtm_pos)
                    if group_end >= 0:
                        insert_pos = group_end + len("<!-- /wp:group -->")
                        content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                        log["what_we_considered"] = "fixed"
                        modified = True
                    else:
                        # Try </div> + /wp:group
                        div_end = content.find("</div>", wtm_pos)
                        if div_end >= 0:
                            after = content.find("<!-- /wp:group -->", div_end)
                            if after and after < div_end + 100:
                                insert_pos = after + len("<!-- /wp:group -->")
                            else:
                                insert_pos = div_end + len("</div>")
                            content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                            log["what_we_considered"] = "fixed"
                            modified = True
                        else:
                            log["what_we_considered"] = "still_no_insert"
                else:
                    # Place after At a Glance
                    aag_pos = content.find("At a Glance")
                    if aag_pos >= 0:
                        group_end = content.find("<!-- /wp:group -->", aag_pos)
                        if group_end >= 0:
                            insert_pos = group_end + len("<!-- /wp:group -->")
                            content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                            log["what_we_considered"] = "fixed"
                            modified = True
                        else:
                            log["what_we_considered"] = "still_no_insert"
                    else:
                        # Place after second paragraph
                        insert_pos = find_second_para_end(content)
                        if insert_pos > 0:
                            content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                            log["what_we_considered"] = "fixed"
                            modified = True
                        else:
                            log["what_we_considered"] = "still_no_insert"

        # 4. TROUBLESHOOTING
        if original_log.get("troubleshooting") in ("no_faq_section", "no_insert_point") and not has_block(content, "Troubleshooting Common Issues"):
            text = batch3.gen_troubleshooting(title_clean, cluster)
            block = batch3.build_troubleshooting_block(text)
            # Try FAQ/Sources/Related Reading headings
            insert_pos = find_faq_or_sources_position(content)
            if insert_pos is None:
                # Fall back: before Key Takeaways
                insert_pos = find_key_takeaways_position(content)
            if insert_pos is None:
                # Fall back: before trust footer
                insert_pos = find_about_editorial_or_trust(content)
            if insert_pos:
                content = content[:insert_pos] + block + "\n\n" + content[insert_pos:]
                log["troubleshooting"] = "fixed"
                modified = True
            else:
                log["troubleshooting"] = "still_no_insert"

        # 5. WHEN TO SEEK HELP
        if original_log.get("when_to_seek_help") == "no_insert_point" and not has_block(content, "When to seek professional help"):
            text = batch3.gen_when_to_seek_help(title_clean, cluster)
            block = batch3.build_when_to_seek_help_block(text)
            # Place after troubleshooting
            ts_pos = content.find("Troubleshooting Common Issues")
            if ts_pos >= 0:
                # Find end of troubleshooting paragraph
                para_end = content.find("</p>", ts_pos)
                if para_end >= 0:
                    # Check if there's a <!-- /wp:paragraph --> right after
                    wp_end = content.find("<!-- /wp:paragraph -->", para_end)
                    if wp_end and wp_end < para_end + 50:
                        insert_pos = wp_end + len("<!-- /wp:paragraph -->")
                    else:
                        insert_pos = para_end + len("</p>")
                    content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                    log["when_to_seek_help"] = "fixed"
                    modified = True
                else:
                    log["when_to_seek_help"] = "still_no_insert"
            else:
                # Place before Key Takeaways or trust footer
                insert_pos = find_key_takeaways_position(content)
                if insert_pos is None:
                    insert_pos = find_about_editorial_or_trust(content)
                if insert_pos:
                    content = content[:insert_pos] + block + "\n\n" + content[insert_pos:]
                    log["when_to_seek_help"] = "fixed"
                    modified = True
                else:
                    log["when_to_seek_help"] = "still_no_insert"

        if modified:
            print(f"  Updating post {post_id}...")
            api_post(f"posts/{post_id}", {"content": content})
            log["status"] = "fixed"
            time.sleep(2)
        else:
            log["status"] = "no_fix_possible"

    except Exception as e:
        log["status"] = f"error: {str(e)[:200]}"
        print(f"  ERROR: {e}")

    return log


def main():
    # Read original log
    original_logs = {}
    with open(LOG_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            original_logs[int(row["id"])] = row

    # Find posts that need fixing
    needs_fix = []
    for pid, log in original_logs.items():
        for field in ["at_a_glance", "why_this_matters", "what_we_considered", "troubleshooting", "when_to_seek_help"]:
            if log.get(field) in ("no_insert_point", "no_faq_section"):
                needs_fix.append((pid, log["title"], log["cluster"], log))
                break

    print(f"Found {len(needs_fix)} posts needing fixes")
    print()

    results = []
    for i, (pid, title, cluster, orig_log) in enumerate(needs_fix, 1):
        print(f"[{i}/{len(needs_fix)}] Fixing: {title[:70]}...")
        log = process_fix(pid, title, cluster, orig_log)
        results.append(log)
        print(f"  -> {log['status']}")
        print(f"     AAG={log['at_a_glance']}, WTM={log['why_this_matters']}, WWC={log['what_we_considered']}, "
              f"TS={log['troubleshooting']}, WTSH={log['when_to_seek_help']}")
        print()

    # Write fix log
    fieldnames = ["id", "title", "cluster", "at_a_glance", "why_this_matters",
                  "what_we_considered", "troubleshooting", "when_to_seek_help",
                  "key_takeaways", "trust_upgraded", "status"]
    with open(FIX_LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    fixed = sum(1 for r in results if r["status"] == "fixed")
    errors = sum(1 for r in results if r["status"].startswith("error"))
    print(f"\nFIX COMPLETE: {fixed} fixed, {errors} errors, {len(needs_fix)} attempted")
    print(f"Fix log: {FIX_LOG_FILE}")


if __name__ == "__main__":
    main()
