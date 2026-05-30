#!/usr/bin/env python3
"""
PetHubOnline Phase 11W: Quick Answer Completion + Featured Snippet Assessment
Two engines:
  1. Quick Answer Completion - adds quick-answer blocks to posts missing them
  2. Featured Snippet Assessment - read-only audit of H2 snippet readiness
"""

import subprocess
import json
import time
import csv
import re
import os
import sys
import tempfile
from datetime import datetime

# ─── Configuration ───────────────────────────────────────────────────────────
WP_API_URL = "https://pethubonline.com/wp-json/wp/v2/posts"
WP_USER = "jasonsarah2026"
WP_APP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_DIR = "/var/lib/freelancer/projects/40416335/phase11w_data"

CATEGORY_MAP = {
    1377: "Cat Supplies", 1459: "Cat Toys", 1413: "Indoor Cats",
    1376: "Dog Supplies", 1397: "Pet Care", 1401: "Dog Beds",
    1489: "Dog Care", 1467: "Dog Food", 1422: "Dog Harnesses",
    1450: "Dog Health", 1441: "Dog Toys", 1442: "Puppy Care",
    1474: "Training Supplies", 1: "Uncategorized"
}

QUICK_ANSWER_TEMPLATE = """<!-- wp:group {{"style":{{"border":{{"width":"1px","color":"#d1fae5","radius":"8px"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}}}}}},"backgroundColor":"white","className":"quick-answer-block"}} -->
<div class="wp-block-group quick-answer-block has-border-color has-white-background-color has-background" style="border-color:#d1fae5;border-width:1px;border-radius:8px;padding-top:16px;padding-bottom:16px;padding-left:20px;padding-right:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Quick Answer</h4>
<!-- /wp:heading -->
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"15px"}}}}}} -->
<p class="wp-block-paragraph" style="font-size:15px">{answer_text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->"""


# ─── Utility Functions ───────────────────────────────────────────────────────

def wp_curl_get(url):
    """GET request via subprocess curl with Basic Auth."""
    time.sleep(2)
    result = subprocess.run(
        [
            "curl", "-s", "-S",
            "-u", f"{WP_USER}:{WP_APP_PASS}",
            "-H", "Content-Type: application/json",
            url
        ],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  [CURL ERROR] {result.stderr.strip()}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        # Check for rate limiting
        if "429" in result.stdout[:200] or "Too Many" in result.stdout[:200]:
            print("  [429] Rate limited, backing off 30s...")
            time.sleep(30)
            return wp_curl_get(url)
        print(f"  [JSON ERROR] Could not parse response (first 300 chars): {result.stdout[:300]}")
        return None


def wp_curl_get_with_headers(url):
    """GET request that also returns response headers (for pagination)."""
    time.sleep(2)
    result = subprocess.run(
        [
            "curl", "-s", "-S", "-D", "-",
            "-u", f"{WP_USER}:{WP_APP_PASS}",
            "-H", "Content-Type: application/json",
            url
        ],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  [CURL ERROR] {result.stderr.strip()}")
        return None, {}

    output = result.stdout
    # Split headers from body - find the blank line separating them
    # curl -D - writes headers then body
    parts = output.split("\r\n\r\n", 1)
    if len(parts) == 2:
        headers_raw, body = parts
    else:
        # Try \n\n
        parts = output.split("\n\n", 1)
        if len(parts) == 2:
            headers_raw, body = parts
        else:
            headers_raw = ""
            body = output

    # Parse headers
    headers = {}
    for line in headers_raw.split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            headers[key.strip().lower()] = val.strip()

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        if "429" in body[:200] or "Too Many" in body[:200]:
            print("  [429] Rate limited, backing off 30s...")
            time.sleep(30)
            return wp_curl_get_with_headers(url)
        print(f"  [JSON ERROR] Could not parse (first 300 chars): {body[:300]}")
        return None, headers

    return data, headers


def wp_curl_post(post_id, payload_dict):
    """POST update via subprocess curl, writing JSON to temp file."""
    time.sleep(3)
    url = f"{WP_API_URL}/{post_id}"

    # Write payload to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
        json.dump(payload_dict, tf, ensure_ascii=False)
        tmppath = tf.name

    try:
        result = subprocess.run(
            [
                "curl", "-s", "-S",
                "-X", "POST",
                "-u", f"{WP_USER}:{WP_APP_PASS}",
                "-H", "Content-Type: application/json",
                "-d", f"@{tmppath}",
                url
            ],
            capture_output=True, text=True, timeout=90
        )
        if result.returncode != 0:
            print(f"  [CURL POST ERROR] {result.stderr.strip()}")
            return None

        try:
            resp = json.loads(result.stdout)
        except json.JSONDecodeError:
            if "429" in result.stdout[:200] or "Too Many" in result.stdout[:200]:
                print("  [429] Rate limited on POST, backing off 30s...")
                time.sleep(30)
                return wp_curl_post(post_id, payload_dict)
            print(f"  [JSON POST ERROR] (first 300 chars): {result.stdout[:300]}")
            return None

        if "id" in resp:
            return resp
        else:
            print(f"  [WP ERROR] {json.dumps(resp)[:300]}")
            return None
    finally:
        os.unlink(tmppath)


def fetch_all_published_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    per_page = 20

    print("Fetching all published posts...")
    while True:
        url = f"{WP_API_URL}?status=publish&per_page={per_page}&page={page}&context=edit"
        data, headers = wp_curl_get_with_headers(url)

        if data is None:
            print(f"  Error fetching page {page}, retrying...")
            time.sleep(10)
            data, headers = wp_curl_get_with_headers(url)
            if data is None:
                print(f"  Failed again on page {page}, stopping pagination.")
                break

        if isinstance(data, dict) and "code" in data:
            # End of pages or error
            if data.get("code") == "rest_post_invalid_page_number":
                break
            print(f"  API error: {data}")
            break

        if not isinstance(data, list) or len(data) == 0:
            break

        all_posts.extend(data)
        total_pages = int(headers.get("x-wp-totalpages", "1"))
        total_posts = headers.get("x-wp-total", "?")
        print(f"  Page {page}/{total_pages} fetched ({len(data)} posts, cumulative: {len(all_posts)}/{total_posts})")

        if page >= total_pages:
            break
        page += 1

    print(f"Total posts fetched: {len(all_posts)}")
    return all_posts


def get_cluster_name(categories):
    """Return the cluster name from category IDs."""
    for cat_id in categories:
        if cat_id in CATEGORY_MAP:
            return CATEGORY_MAP[cat_id]
    return "Uncategorized"


def strip_html(text):
    """Remove HTML tags from text."""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = re.sub(r'&[a-zA-Z]+;', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def has_quick_answer(content):
    """Check if post content already has a quick-answer block."""
    if not content:
        return False
    lower = content.lower()
    return ("quick-answer" in lower or
            "quick answer" in lower or
            "quick-answer-block" in lower)


# ─── Quick Answer Generation (Rule-Based) ────────────────────────────────────

def extract_first_sentences(text, max_words=60):
    """Extract first few sentences up to max_words."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = []
    word_count = 0
    for sent in sentences:
        words = sent.split()
        if word_count + len(words) <= max_words:
            result.append(sent)
            word_count += len(words)
        else:
            # Take partial to reach ~40-60 words
            remaining = max_words - word_count
            if remaining > 5:
                result.append(' '.join(words[:remaining]) + '.')
            break
    return ' '.join(result)


def extract_plain_content(raw_content):
    """Extract plain text from Gutenberg content, paragraph by paragraph."""
    # Extract paragraph block text
    paragraphs = []
    # Match wp:paragraph blocks
    para_pattern = re.compile(r'<!-- wp:paragraph[^>]*-->\s*<p[^>]*>(.*?)</p>\s*<!-- /wp:paragraph -->', re.DOTALL)
    for m in para_pattern.finditer(raw_content):
        text = strip_html(m.group(1)).strip()
        if text and len(text) > 20:
            paragraphs.append(text)

    # Also match wp:list blocks
    list_pattern = re.compile(r'<li[^>]*>(.*?)</li>', re.DOTALL)
    for m in list_pattern.finditer(raw_content):
        text = strip_html(m.group(1)).strip()
        if text and len(text) > 10:
            paragraphs.append(text)

    return paragraphs


def generate_quick_answer(title, raw_content):
    """Generate a 40-60 word quick answer from the post title and content."""
    title_lower = title.lower().strip()
    paragraphs = extract_plain_content(raw_content)
    full_text = ' '.join(paragraphs[:10])  # First 10 paragraphs of content

    # ── Pattern 1: "Best X for Y" or numbered product list ──
    best_match = re.match(r'^(?:the\s+)?(\d+\s+)?best\s+(.+?)(?:\s+for\s+(.+))?$', title_lower)
    number_match = re.match(r'^(\d+)\s+(?:best\s+)?(.+?)(?:\s+for\s+(.+))?$', title_lower)

    if best_match or number_match:
        match = best_match or number_match
        num = match.group(1).strip() if match.group(1) else ""
        product = match.group(2).strip() if match.group(2) else ""
        audience = match.group(3).strip() if match.group(3) else ""

        # Try to find recommended products from H2s or bold text
        h2_pattern = re.compile(r'<h2[^>]*>(.*?)</h2>', re.DOTALL)
        h2_texts = [strip_html(m.group(1)) for m in h2_pattern.finditer(raw_content)]
        product_h2s = [h for h in h2_texts if not any(w in h.lower() for w in ['how', 'why', 'what', 'guide', 'faq', 'conclusion', 'factor', 'choose', 'tip', 'benefit'])]

        top_picks = product_h2s[:3]
        picks_str = ""
        if top_picks:
            if len(top_picks) >= 2:
                picks_str = f" Top picks include {top_picks[0]} and {top_picks[1]}."
            else:
                picks_str = f" A top pick is {top_picks[0]}."

        if audience:
            answer = f"The best {product} for {audience} should offer durability, comfort, and value."
        else:
            answer = f"The best {product} should offer quality materials, durability, and good value for money."

        answer += picks_str

        # Add guidance from content
        if paragraphs:
            key_point = extract_first_sentences(paragraphs[0], max_words=20)
            if key_point and len(answer.split()) < 35:
                answer += f" {key_point}"

        # Trim to 40-60 words
        words = answer.split()
        if len(words) > 60:
            answer = ' '.join(words[:58]) + '.'
        elif len(words) < 40 and paragraphs:
            # Pad with content insight
            extra = extract_first_sentences(paragraphs[0], max_words=60 - len(words))
            answer = answer.rstrip('.') + '. ' + extra
            words = answer.split()
            if len(words) > 60:
                answer = ' '.join(words[:58]) + '.'

        return answer.strip()

    # ── Pattern 2: Question titles ──
    question_match = re.match(r'^(how|what|why|when|where|which|can|do|does|is|are|should|will)\s+', title_lower)
    if question_match or title.rstrip().endswith('?'):
        # Extract answer from first paragraphs
        if paragraphs:
            # Skip paragraphs that are just restating the question
            answer_paras = []
            for p in paragraphs[:5]:
                # Skip if paragraph is mostly the title repeated
                if len(set(title_lower.split()) & set(p.lower().split())) / max(len(title_lower.split()), 1) < 0.6:
                    answer_paras.append(p)
                elif len(p.split()) > 30:
                    answer_paras.append(p)

            if not answer_paras:
                answer_paras = paragraphs[:3]

            answer = extract_first_sentences(' '.join(answer_paras[:3]), max_words=58)
            words = answer.split()
            if len(words) < 40:
                more = extract_first_sentences(' '.join(paragraphs[:5]), max_words=58)
                answer = more
            words = answer.split()
            if len(words) > 60:
                answer = ' '.join(words[:58]) + '.'
            return answer.strip()

    # ── Pattern 3: "How to..." educational ──
    how_to_match = re.match(r'^how\s+to\s+(.+)$', title_lower)
    if how_to_match:
        topic = how_to_match.group(1)
        if paragraphs:
            answer = extract_first_sentences(' '.join(paragraphs[:3]), max_words=58)
            words = answer.split()
            if len(words) > 60:
                answer = ' '.join(words[:58]) + '.'
            return answer.strip()

    # ── Pattern 4: General / Educational titles ──
    if paragraphs:
        # Use first substantive paragraph as base
        base = paragraphs[0]

        # If the first paragraph is too short, combine with second
        if len(base.split()) < 25 and len(paragraphs) > 1:
            base = base + ' ' + paragraphs[1]

        answer = extract_first_sentences(base, max_words=58)
        words = answer.split()

        if len(words) < 35 and len(paragraphs) > 1:
            # Add more content
            answer = extract_first_sentences(' '.join(paragraphs[:3]), max_words=58)

        words = answer.split()
        if len(words) > 60:
            answer = ' '.join(words[:58]) + '.'
        if len(words) < 30:
            answer = extract_first_sentences(full_text, max_words=58)
            words = answer.split()
            if len(words) > 60:
                answer = ' '.join(words[:58]) + '.'

        return answer.strip()

    return None


def insert_quick_answer_block(content, answer_text):
    """Insert quick answer block after the first paragraph in Gutenberg content."""
    block = QUICK_ANSWER_TEMPLATE.format(answer_text=answer_text)

    # Find the end of the first wp:paragraph block
    first_para_end = re.search(r'<!-- /wp:paragraph -->', content)
    if first_para_end:
        insert_pos = first_para_end.end()
        new_content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
        return new_content

    # Fallback: insert at the very beginning
    return block + "\n\n" + content


# ─── ENGINE 1: Quick Answer Completion ────────────────────────────────────────

def run_quick_answer_engine(posts):
    """Scan all posts, add quick answers where missing."""
    print("\n" + "=" * 70)
    print("ENGINE 1: QUICK ANSWER COMPLETION")
    print("=" * 70)

    csv_path = os.path.join(OUTPUT_DIR, "Quick_Answer_Log.csv")
    csv_rows = []

    already_have = 0
    added = 0
    failed = 0
    skipped = 0

    for i, post in enumerate(posts):
        post_id = post["id"]
        title = post["title"]["raw"] if isinstance(post["title"], dict) else strip_html(str(post["title"].get("rendered", post["title"]))) if isinstance(post["title"], dict) else str(post["title"])

        # Handle title extraction properly
        if isinstance(post.get("title"), dict):
            if "raw" in post["title"]:
                title = post["title"]["raw"]
            elif "rendered" in post["title"]:
                title = strip_html(post["title"]["rendered"])
            else:
                title = str(post["title"])
        else:
            title = str(post.get("title", ""))

        cluster = get_cluster_name(post.get("categories", []))

        # Get raw content
        if isinstance(post.get("content"), dict):
            if "raw" in post["content"]:
                content = post["content"]["raw"]
            elif "rendered" in post["content"]:
                content = post["content"]["rendered"]
            else:
                content = str(post["content"])
        else:
            content = str(post.get("content", ""))

        print(f"\n[{i+1}/{len(posts)}] Post {post_id}: {title[:70]}...")
        print(f"  Cluster: {cluster}")

        # Check if already has quick answer
        if has_quick_answer(content):
            print(f"  -> Already has quick answer. SKIP.")
            already_have += 1
            csv_rows.append({
                "post_id": post_id,
                "title": title,
                "cluster": cluster,
                "action": "already_exists",
                "answer_text": "",
                "word_count": "",
                "status": "skipped"
            })
            continue

        # Generate quick answer
        answer_text = generate_quick_answer(title, content)
        if not answer_text or len(answer_text.split()) < 15:
            print(f"  -> Could not generate sufficient answer. SKIP.")
            skipped += 1
            csv_rows.append({
                "post_id": post_id,
                "title": title,
                "cluster": cluster,
                "action": "generation_failed",
                "answer_text": answer_text or "",
                "word_count": len(answer_text.split()) if answer_text else 0,
                "status": "skipped"
            })
            continue

        word_count = len(answer_text.split())
        print(f"  -> Generated answer ({word_count} words): {answer_text[:100]}...")

        # Insert into content
        new_content = insert_quick_answer_block(content, answer_text)

        # Update post via API
        payload = {"content": new_content}
        result = wp_curl_post(post_id, payload)

        if result and "id" in result:
            print(f"  -> UPDATED successfully.")
            added += 1
            csv_rows.append({
                "post_id": post_id,
                "title": title,
                "cluster": cluster,
                "action": "added",
                "answer_text": answer_text,
                "word_count": word_count,
                "status": "success"
            })
        else:
            print(f"  -> FAILED to update.")
            failed += 1
            csv_rows.append({
                "post_id": post_id,
                "title": title,
                "cluster": cluster,
                "action": "add_attempted",
                "answer_text": answer_text,
                "word_count": word_count,
                "status": "failed"
            })

    # Write CSV log
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["post_id", "title", "cluster", "action", "answer_text", "word_count", "status"])
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"\n{'─' * 50}")
    print(f"ENGINE 1 SUMMARY:")
    print(f"  Total posts scanned:  {len(posts)}")
    print(f"  Already had QA:       {already_have}")
    print(f"  Quick answers added:  {added}")
    print(f"  Failed updates:       {failed}")
    print(f"  Skipped (no content): {skipped}")
    print(f"  CSV log: {csv_path}")
    print(f"{'─' * 50}")

    return {"already": already_have, "added": added, "failed": failed, "skipped": skipped}


# ─── ENGINE 2: Featured Snippet Assessment ────────────────────────────────────

def extract_h2_blocks(content):
    """Extract H2 headings and first paragraph after each."""
    blocks = []

    # Find all H2 headings (Gutenberg format)
    h2_pattern = re.compile(
        r'<!-- wp:heading(?:\s+\{[^}]*\})?\s*-->\s*<h2[^>]*>(.*?)</h2>\s*<!-- /wp:heading -->',
        re.DOTALL
    )

    matches = list(h2_pattern.finditer(content))

    for idx, match in enumerate(matches):
        h2_text = strip_html(match.group(1)).strip()
        h2_end = match.end()

        # Find first paragraph after this H2
        next_h2_start = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        section = content[h2_end:next_h2_start]

        # Extract first paragraph in this section
        para_match = re.search(
            r'<!-- wp:paragraph[^>]*-->\s*<p[^>]*>(.*?)</p>\s*<!-- /wp:paragraph -->',
            section, re.DOTALL
        )

        first_para_text = ""
        first_para_word_count = 0
        if para_match:
            first_para_text = strip_html(para_match.group(1)).strip()
            first_para_word_count = len(first_para_text.split())

        blocks.append({
            "h2_text": h2_text,
            "h2_position": idx + 1,
            "first_para_text": first_para_text,
            "first_para_word_count": first_para_word_count
        })

    return blocks


def is_question_format(h2_text):
    """Check if H2 is in question format."""
    h2_lower = h2_text.lower().strip()
    question_starters = [
        'what', 'why', 'how', 'when', 'where', 'which', 'who',
        'can', 'do', 'does', 'is', 'are', 'should', 'will', 'could', 'would'
    ]
    if h2_text.strip().endswith('?'):
        return True
    for starter in question_starters:
        if h2_lower.startswith(starter + ' '):
            return True
    return False


def suggest_question_h2(h2_text):
    """Suggest a question-format alternative for a statement H2."""
    h2_lower = h2_text.lower().strip()

    # Already a question
    if is_question_format(h2_text):
        return h2_text

    # Common patterns
    # "Benefits of X" -> "What Are the Benefits of X?"
    benefits_match = re.match(r'(?:the\s+)?benefits?\s+of\s+(.+)', h2_lower)
    if benefits_match:
        return f"What Are the Benefits of {benefits_match.group(1).title()}?"

    # "Types of X" -> "What Are the Types of X?"
    types_match = re.match(r'(?:the\s+)?types?\s+of\s+(.+)', h2_lower)
    if types_match:
        return f"What Are the Types of {types_match.group(1).title()}?"

    # "Choosing X" -> "How to Choose X?"
    choosing_match = re.match(r'choosing\s+(.+)', h2_lower)
    if choosing_match:
        return f"How Do You Choose {choosing_match.group(1).title()}?"

    # "Tips for X" -> "What Are the Best Tips for X?"
    tips_match = re.match(r'(?:top\s+)?tips?\s+for\s+(.+)', h2_lower)
    if tips_match:
        return f"What Are the Best Tips for {tips_match.group(1).title()}?"

    # "X vs Y" -> "What Is the Difference Between X and Y?"
    vs_match = re.match(r'(.+?)\s+(?:vs\.?|versus)\s+(.+)', h2_lower)
    if vs_match:
        return f"What Is the Difference Between {vs_match.group(1).title()} and {vs_match.group(2).title()}?"

    # "Features to Look For" -> "What Features Should You Look For?"
    features_match = re.match(r'(?:key\s+)?features?\s+(?:to\s+)?(?:look|consider|check)', h2_lower)
    if features_match:
        return f"What Features Should You Look For?"

    # "X Buying Guide" -> "How Do You Buy the Right X?"
    buying_match = re.match(r'(.+?)\s+buying\s+guide', h2_lower)
    if buying_match:
        return f"How Do You Choose the Right {buying_match.group(1).title()}?"

    # "Conclusion" / "Final Thoughts" -> skip meaningful suggestion
    skip_headings = ['conclusion', 'final thoughts', 'summary', 'wrapping up', 'in conclusion']
    if h2_lower in skip_headings:
        return f"What Are the Key Takeaways?"

    # "Top X" / "Best X" -> "What Are the Best X?"
    top_match = re.match(r'(?:top|best)\s+(.+)', h2_lower)
    if top_match:
        return f"What Are the Best {top_match.group(1).title()}?"

    # "X for Y" -> "What X Works Best for Y?"
    for_match = re.match(r'(.+?)\s+for\s+(.+)', h2_lower)
    if for_match:
        return f"What {for_match.group(1).title()} Works Best for {for_match.group(2).title()}?"

    # Generic fallback: "X" -> "What Is X?" or "What Should You Know About X?"
    if len(h2_text.split()) <= 4:
        return f"What Is {h2_text.strip().title()}?"
    else:
        return f"What Should You Know About {h2_text.strip().title()}?"


def run_snippet_assessment(posts):
    """Assess featured snippet readiness across all posts (read-only)."""
    print("\n" + "=" * 70)
    print("ENGINE 2: FEATURED SNIPPET ASSESSMENT (READ-ONLY)")
    print("=" * 70)

    opportunities_csv = os.path.join(OUTPUT_DIR, "Featured_Snippet_Opportunities.csv")
    readiness_csv = os.path.join(OUTPUT_DIR, "Featured_Snippet_Readiness.csv")

    opp_rows = []
    readiness_rows = []

    for i, post in enumerate(posts):
        post_id = post["id"]

        # Title extraction
        if isinstance(post.get("title"), dict):
            if "raw" in post["title"]:
                title = post["title"]["raw"]
            elif "rendered" in post["title"]:
                title = strip_html(post["title"]["rendered"])
            else:
                title = str(post["title"])
        else:
            title = str(post.get("title", ""))

        cluster = get_cluster_name(post.get("categories", []))

        # Content extraction
        if isinstance(post.get("content"), dict):
            if "raw" in post["content"]:
                content = post["content"]["raw"]
            elif "rendered" in post["content"]:
                content = post["content"]["rendered"]
            else:
                content = str(post["content"])
        else:
            content = str(post.get("content", ""))

        print(f"[{i+1}/{len(posts)}] Assessing post {post_id}: {title[:60]}...")

        h2_blocks = extract_h2_blocks(content)

        total_h2s = len(h2_blocks)
        question_h2s = 0
        statement_h2s = 0
        para_word_counts = []

        for block in h2_blocks:
            is_q = is_question_format(block["h2_text"])
            if is_q:
                question_h2s += 1
            else:
                statement_h2s += 1

            suggested = suggest_question_h2(block["h2_text"]) if not is_q else block["h2_text"]

            # Snippet-ready: question H2 + first para 40-60 words
            snippet_ready = "yes" if (is_q and 35 <= block["first_para_word_count"] <= 65) else "no"

            para_word_counts.append(block["first_para_word_count"])

            opp_rows.append({
                "post_id": post_id,
                "title": title,
                "cluster": cluster,
                "h2_text": block["h2_text"],
                "suggested_question_h2": suggested if not is_q else "",
                "h2_position": block["h2_position"],
                "first_para_word_count": block["first_para_word_count"],
                "snippet_ready": snippet_ready
            })

        # Post-level readiness
        if total_h2s > 0:
            readiness_pct = round(question_h2s / total_h2s * 100, 1)
            avg_para_words = round(sum(para_word_counts) / len(para_word_counts), 1) if para_word_counts else 0
        else:
            readiness_pct = 0
            avg_para_words = 0

        # Grade
        if readiness_pct >= 80:
            grade = "A"
        elif readiness_pct >= 60:
            grade = "B"
        elif readiness_pct >= 40:
            grade = "C"
        elif readiness_pct >= 20:
            grade = "D"
        else:
            grade = "F"

        readiness_rows.append({
            "post_id": post_id,
            "title": title,
            "cluster": cluster,
            "total_h2s": total_h2s,
            "question_h2s": question_h2s,
            "statement_h2s": statement_h2s,
            "snippet_readiness_pct": readiness_pct,
            "avg_first_para_words": avg_para_words,
            "overall_grade": grade
        })

        print(f"  H2s: {total_h2s} (Q: {question_h2s}, S: {statement_h2s}) -> {readiness_pct}% ready, Grade: {grade}")

    # Write Opportunities CSV
    with open(opportunities_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "h2_text", "suggested_question_h2",
            "h2_position", "first_para_word_count", "snippet_ready"
        ])
        writer.writeheader()
        writer.writerows(opp_rows)

    # Write Readiness CSV
    with open(readiness_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "total_h2s", "question_h2s",
            "statement_h2s", "snippet_readiness_pct", "avg_first_para_words", "overall_grade"
        ])
        writer.writeheader()
        writer.writerows(readiness_rows)

    # Summary stats
    total = len(readiness_rows)
    grades = {}
    for r in readiness_rows:
        g = r["overall_grade"]
        grades[g] = grades.get(g, 0) + 1

    total_h2_all = sum(r["total_h2s"] for r in readiness_rows)
    total_q_h2 = sum(r["question_h2s"] for r in readiness_rows)
    total_s_h2 = sum(r["statement_h2s"] for r in readiness_rows)
    avg_readiness = round(sum(r["snippet_readiness_pct"] for r in readiness_rows) / max(total, 1), 1)
    snippet_ready_count = sum(1 for r in opp_rows if r["snippet_ready"] == "yes")

    print(f"\n{'─' * 50}")
    print(f"ENGINE 2 SUMMARY:")
    print(f"  Posts assessed:        {total}")
    print(f"  Total H2 headings:     {total_h2_all}")
    print(f"  Question-format H2s:   {total_q_h2}")
    print(f"  Statement-format H2s:  {total_s_h2}")
    print(f"  Snippet-ready H2s:     {snippet_ready_count}")
    print(f"  Avg readiness score:   {avg_readiness}%")
    print(f"  Grade distribution:    {grades}")
    print(f"  Opportunities CSV:     {opportunities_csv}")
    print(f"  Readiness CSV:         {readiness_csv}")
    print(f"{'─' * 50}")

    return {"total_h2s": total_h2_all, "question_h2s": total_q_h2, "snippet_ready": snippet_ready_count}


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("PetHubOnline Phase 11W: Quick Answer + Snippet Assessment")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Fetch all posts
    posts = fetch_all_published_posts()
    if not posts:
        print("ERROR: No posts fetched. Exiting.")
        sys.exit(1)

    # Save raw post data for reference
    raw_path = os.path.join(OUTPUT_DIR, "raw_posts_data.json")
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump([{"id": p["id"], "title": p.get("title", {}).get("raw", ""), "categories": p.get("categories", [])} for p in posts], f, indent=2)
    print(f"Saved raw post metadata to {raw_path}")

    # ENGINE 1: Quick Answer Completion
    qa_results = run_quick_answer_engine(posts)

    # Re-fetch posts to get updated content for snippet assessment
    print("\n\nRe-fetching posts with updated content for snippet assessment...")
    posts_updated = fetch_all_published_posts()
    if not posts_updated:
        print("WARNING: Could not re-fetch posts, using original data for Engine 2.")
        posts_updated = posts

    # ENGINE 2: Featured Snippet Assessment
    snippet_results = run_snippet_assessment(posts_updated)

    # Final summary
    print("\n" + "=" * 70)
    print("PHASE 11W COMPLETE")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nEngine 1 (Quick Answers): {qa_results['added']} added, {qa_results['already']} already existed, {qa_results['failed']} failed")
    print(f"Engine 2 (Snippets): {snippet_results['total_h2s']} H2s assessed, {snippet_results['question_h2s']} question-format, {snippet_results['snippet_ready']} snippet-ready")
    print(f"\nOutput files in: {OUTPUT_DIR}/")
    print("  - Quick_Answer_Log.csv")
    print("  - Featured_Snippet_Opportunities.csv")
    print("  - Featured_Snippet_Readiness.csv")
    print("  - raw_posts_data.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
