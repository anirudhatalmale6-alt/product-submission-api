#!/usr/bin/env python3
"""
Fix the 5 sanity-fail posts from batch4 v2.
Handles: rendered HTML trust footer with duplicate editorial sections,
and trust footer at wrong position.
"""
import subprocess, json, tempfile, os, time, re, csv
from datetime import datetime

API_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ai_data"
LOG_FILE = os.path.join(DATA_DIR, "batch4_grooming_harness_beds_log.csv")
DELAY = 2.5

# Import block builders and content generators from v2
import importlib.util
spec = importlib.util.spec_from_file_location("v2", os.path.join(DATA_DIR, "batch4_enhance_v2.py"))
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)

FAIL_POSTS = [
    (5521, "Pet Health Terminology: A Guide to Common Veterinary Terms", "Educational"),
    (5419, "Cat Care Basics: A Glossary for New Cat Owners", "Educational"),
    (5414, "Cat Toy Types Explained: A Complete Glossary", "Educational"),
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


def remove_all_editorial_sections(content):
    """Remove ALL editorial/trust footer sections from content.

    This handles both:
    1. Rendered div blocks with 'Our Editorial Standards'
    2. Old h3 'About Our Editorial Standards' sections
    3. Old separator + paragraph format
    """
    # Remove rendered div blocks containing 'Our Editorial Standards'
    # These are <div class="wp-block-group...">...<h4>Our Editorial Standards</h4>...</div>
    pattern1 = re.compile(
        r'<div[^>]*class="wp-block-group[^"]*"[^>]*>\s*'
        r'<h4[^>]*>\s*Our Editorial Standards\s*</h4>\s*'
        r'<p[^>]*>.*?</p>\s*'
        r'</div>',
        re.DOTALL
    )
    content = pattern1.sub('', content)

    # Remove Gutenberg comment-wrapped editorial blocks
    pattern1b = re.compile(
        r'<!-- wp:group[^>]*-->\s*'
        r'<div[^>]*>.*?Our Editorial Standards.*?</div>\s*'
        r'<!-- /wp:group -->',
        re.DOTALL
    )
    content = pattern1b.sub('', content)

    # Remove old 'About Our Editorial Standards' h3 + paragraph
    pattern2 = re.compile(
        r'(?:<!-- wp:heading[^>]*-->\s*)?'
        r'<h3[^>]*>\s*About Our Editorial Standards\s*</h3>\s*'
        r'(?:<!-- /wp:heading -->\s*)?'
        r'(?:<!-- wp:paragraph[^>]*-->\s*)?'
        r'<p[^>]*>.*?(?:corrections|editorial).*?</p>\s*'
        r'(?:<!-- /wp:paragraph -->\s*)?',
        re.DOTALL
    )
    content = pattern2.sub('', content)

    # Remove old separator + editorial paragraph
    pattern3 = re.compile(
        r'(?:<!-- wp:separator[^>]*-->\s*)?'
        r'<hr[^>]*/>\s*'
        r'(?:<!-- /wp:separator -->\s*)?'
        r'(?:<!-- wp:paragraph[^>]*-->\s*)?'
        r'<p[^>]*>.*?(?:editorial process|how we create).*?(?:affiliate|corrections).*?</p>\s*'
        r'(?:<!-- /wp:paragraph -->\s*)?',
        re.DOTALL | re.IGNORECASE
    )
    content = pattern3.sub('', content)

    # Clean up excessive whitespace
    content = re.sub(r'\n{4,}', '\n\n\n', content)

    return content.strip()


def enhance_post(post_id, title, cluster):
    blocks_added = []

    data = api_get(f"posts/{post_id}?context=edit")
    content = data.get("content", {}).get("raw", "")
    if not content:
        return "SKIP", "Empty content", []

    original_len = len(content)
    print(f"  Fetched: {original_len} chars")

    # Step 1: Remove ALL existing editorial/trust sections
    content = remove_all_editorial_sections(content)
    cleaned_len = len(content)
    print(f"  After removing editorial sections: {cleaned_len} chars")

    # Step 2: Add missing blocks

    # AT A GLANCE
    if 'At a Glance' not in content:
        bullets = v2.generate_at_a_glance(post_id, title, cluster)
        block = v2.build_at_a_glance(bullets)
        insert_pos = v2.find_first_paragraph_end(content)
        if insert_pos > 0:
            content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
            blocks_added.append("at_a_glance")

    # WHY THIS MATTERS
    if 'Why this matters' not in content:
        text = v2.generate_why_matters(post_id, title, cluster)
        block = v2.build_why_matters(text)
        aag_pos = content.lower().find("at a glance")
        if aag_pos >= 0:
            after = content[aag_pos:]
            group_end = after.find("<!-- /wp:group -->")
            if group_end >= 0:
                insert_pos = aag_pos + group_end + len("<!-- /wp:group -->")
            else:
                div_end = after.find("</div>")
                if div_end >= 0:
                    insert_pos = aag_pos + div_end + len("</div>")
                else:
                    insert_pos = v2.find_first_paragraph_end(content)
        else:
            insert_pos = v2.find_first_paragraph_end(content)
        content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
        blocks_added.append("why_this_matters")

    # WHAT WE CONSIDERED (buying guides only)
    if v2.is_buying_guide(title) and 'What we considered' not in content:
        considered_text = v2.generate_what_we_considered(post_id, title, cluster)
        if considered_text:
            block = v2.build_what_we_considered(considered_text)
            wtm_pos = content.lower().find("why this matters")
            if wtm_pos >= 0:
                after = content[wtm_pos:]
                group_end = after.find("<!-- /wp:group -->")
                if group_end >= 0:
                    insert_pos = wtm_pos + group_end + len("<!-- /wp:group -->")
                else:
                    div_end = after.find("</div>")
                    insert_pos = wtm_pos + div_end + len("</div>") if div_end >= 0 else v2.find_first_paragraph_end(content)
            else:
                insert_pos = v2.find_first_paragraph_end(content)
            content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
            blocks_added.append("what_we_considered")

    # TROUBLESHOOTING
    if 'Troubleshooting Common Issues' not in content:
        trouble_text = v2.generate_troubleshooting(post_id, title, cluster)
        block = v2.build_troubleshooting(trouble_text)
        faq_pos = v2.find_faq_position(content)
        if faq_pos:
            content = content[:faq_pos] + block + "\n\n" + content[faq_pos:]
        else:
            content = content.rstrip() + "\n\n" + block
        blocks_added.append("troubleshooting")

    # WHEN TO SEEK HELP
    if 'When to seek professional help' not in content:
        seek_text = v2.generate_when_to_seek_help(post_id, title, cluster)
        block = v2.build_when_to_seek_help(seek_text)
        trouble_pos = content.find("Troubleshooting Common Issues")
        if trouble_pos >= 0:
            after = content[trouble_pos:]
            para_end = after.find("<!-- /wp:paragraph -->")
            if para_end >= 0:
                insert_pos = trouble_pos + para_end + len("<!-- /wp:paragraph -->")
            else:
                p_ends = [m.end() for m in re.finditer(r'</p>', after)]
                insert_pos = trouble_pos + p_ends[0] if p_ends else len(content)
        else:
            insert_pos = len(content)
        content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
        blocks_added.append("when_to_seek_help")

    # KEY TAKEAWAYS
    if 'Key Takeaways' not in content:
        takeaway_bullets = v2.generate_key_takeaways(post_id, title, cluster)
        block = v2.build_key_takeaways(takeaway_bullets)
        content = content.rstrip() + "\n\n" + block
        blocks_added.append("key_takeaways")

    # Step 3: Add new trust footer at the END
    new_footer = v2.get_trust_footer(cluster, post_id, title)
    content = content.rstrip() + "\n\n" + new_footer
    blocks_added.append("trust_footer_added")

    final_len = len(content)
    print(f"  Final content: {final_len} chars")

    # Sanity check - we should have grown
    if final_len < original_len * 0.7:
        return "SANITY_FAIL", f"{original_len}->{final_len}", blocks_added

    # Update
    time.sleep(DELAY)
    result = api_post(f"posts/{post_id}", {"content": content})
    if "id" in result:
        return "OK", f"{original_len}->{final_len}", blocks_added
    else:
        return "ERROR", result.get("message", str(result)[:200]), blocks_added


def main():
    print(f"Fixing {len(FAIL_POSTS)} sanity-fail posts")
    print("=" * 70)

    for post_id, title, cluster in FAIL_POSTS:
        print(f"\n#{post_id}: {title[:50]}...")
        try:
            status, detail, blocks = enhance_post(post_id, title, cluster)
            blocks_str = ",".join(blocks)
            print(f"  -> {status} | {detail} | blocks: {blocks_str}")

            with open(LOG_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    post_id, title, cluster, status, detail, blocks_str
                ])
        except Exception as e:
            print(f"  -> EXCEPTION: {str(e)[:200]}")
            with open(LOG_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    post_id, title, cluster, "EXCEPTION", str(e)[:200], ""
                ])

        time.sleep(DELAY)

    print(f"\n{'=' * 70}")
    print("Fix complete")


if __name__ == "__main__":
    main()
