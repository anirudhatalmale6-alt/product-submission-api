#!/usr/bin/env python3
"""Phase 11X: Featured Snippet Dominance Engine
Converts statement H2s to question format and adds 40-60 word answer blocks.
Priority clusters: Cat Supplies, Dog Supplies, Dog Beds, Dog Food, Indoor Cats.
"""

import csv
import json
import subprocess
import time
import re
import os
import sys
import tempfile
from collections import defaultdict

WP_AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_URL = "https://pethubonline.com/wp-json/wp/v2/posts"
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

PRIORITY_CLUSTERS = ["Cat Supplies", "Dog Supplies", "Dog Beds", "Dog Food", "Indoor Cats"]
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OPPS_CSV = os.path.join(DATA_DIR, "Featured_Snippet_Opportunities.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "Featured_Snippet_Acceleration.csv")

SKIP_H2_PATTERNS = [
    r"^Sources and References",
    r"^Compared:",
    r"^Quick [Aa]nswer",
    r"^Related ",
    r"^Frequently Asked",
    r"^FAQ",
]


def should_skip_h2(h2_text):
    for pat in SKIP_H2_PATTERNS:
        if re.match(pat, h2_text.strip()):
            return True
    return False


def is_question(h2_text):
    t = h2_text.strip().rstrip("?")
    q_starts = ["what", "how", "why", "when", "which", "where", "who", "is", "are", "do", "does", "can", "should"]
    first_word = t.lower().split()[0] if t.split() else ""
    return first_word in q_starts or h2_text.strip().endswith("?")


def wp_get(post_id):
    time.sleep(2)
    url = f"{WP_URL}/{post_id}?context=edit"
    r = subprocess.run(
        ["curl", "-s", "--compressed", "-u", WP_AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def wp_update(post_id, content):
    time.sleep(3)
    payload = json.dumps({"content": content})
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(payload)
        tmp = f.name
    try:
        url = f"{WP_URL}/{post_id}"
        r = subprocess.run(
            ["curl", "-s", "--compressed", "-u", WP_AUTH,
             "-X", "POST", "-H", "Content-Type: application/json",
             "-d", f"@{tmp}", url],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode != 0:
            return False, r.stderr
        resp = json.loads(r.stdout)
        if "id" in resp:
            return True, "ok"
        return False, r.stdout[:200]
    except Exception as e:
        return False, str(e)
    finally:
        os.unlink(tmp)


def call_openai(system_prompt, user_prompt, max_tokens=500):
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        tmp = f.name
    try:
        r = subprocess.run(
            ["curl", "-s", "https://api.openai.com/v1/chat/completions",
             "-H", f"Authorization: Bearer {OPENAI_KEY}",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmp}"],
            capture_output=True, text=True, timeout=30
        )
        resp = json.loads(r.stdout)
        return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  OpenAI error: {e}")
        return None
    finally:
        os.unlink(tmp)


def extract_sections(content):
    """Parse Gutenberg content into sections keyed by H2 text."""
    h2_pattern = re.compile(
        r'<!-- wp:heading[^>]*-->\s*<h2[^>]*>(.*?)</h2>\s*<!-- /wp:heading -->',
        re.DOTALL
    )
    matches = list(h2_pattern.finditer(content))
    sections = {}
    for i, m in enumerate(matches):
        h2_text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(content)
        section_content = content[start:end]
        text_only = re.sub(r'<[^>]+>', '', section_content)
        text_only = re.sub(r'<!--.*?-->', '', text_only)
        text_only = re.sub(r'\s+', ' ', text_only).strip()
        sections[h2_text] = {
            "raw": section_content,
            "text": text_only[:1000],
            "match": m,
        }
    return sections


def generate_question_and_answer(h2_text, section_text, post_title):
    """Use GPT-4o-mini to generate a natural question rewrite and 40-60 word answer."""
    system = """You are a UK pet care content editor optimizing for Google featured snippets.
Given an H2 heading and the section content below it, produce:
1. A natural question-format H2 (starting with What/How/Why/When/Which/Where)
2. A concise 40-60 word answer paragraph that directly answers the question

Rules:
- The question must sound natural, not awkward
- The answer must be factual, based ONLY on the provided section content
- Do NOT invent information not in the section
- Do NOT use "we tested" or claim expertise
- Do NOT reference specific brands unless they appear in the content
- UK English spelling
- The answer should be a complete, standalone paragraph

Respond in exactly this JSON format:
{"question": "...", "answer": "..."}"""

    user = f"""Post title: {post_title}
H2 heading: {h2_text}
Section content: {section_text[:800]}"""

    result = call_openai(system, user, max_tokens=300)
    if not result:
        return None, None
    try:
        result = result.strip()
        if result.startswith("```"):
            result = re.sub(r'^```\w*\n?', '', result)
            result = re.sub(r'\n?```$', '', result)
        data = json.loads(result)
        q = data.get("question", "").strip()
        a = data.get("answer", "").strip()
        word_count = len(a.split())
        if word_count < 30 or word_count > 80:
            return q, None
        return q, a
    except (json.JSONDecodeError, KeyError):
        return None, None


def insert_answer_after_h2(content, h2_match, new_h2_text, answer_text):
    """Replace H2 text and insert answer paragraph block after the H2 block."""
    old_block = h2_match.group(0)
    h2_inner = h2_match.group(1)

    new_block = old_block.replace(h2_inner, new_h2_text)

    answer_block = (
        f'\n\n<!-- wp:paragraph {{"className":"snippet-answer"}} -->\n'
        f'<p class="snippet-answer">{answer_text}</p>\n'
        f'<!-- /wp:paragraph -->'
    )

    insertion_point = h2_match.end()
    new_content = content[:h2_match.start()] + new_block + answer_block + content[insertion_point:]
    return new_content


def load_opportunities():
    """Load and filter convertible H2s from the opportunities CSV."""
    posts = defaultdict(list)
    with open(OPPS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cluster = row.get("cluster", "")
            h2_text = row.get("h2_text", "")
            suggested = row.get("suggested_question_h2", "")

            if cluster not in PRIORITY_CLUSTERS:
                continue
            if should_skip_h2(h2_text):
                continue
            if is_question(h2_text):
                continue
            if not suggested.strip():
                continue

            post_id = row["post_id"]
            posts[post_id].append({
                "title": row["title"],
                "cluster": cluster,
                "h2_text": h2_text,
                "suggested": suggested,
                "h2_position": int(row.get("h2_position", 0)),
            })
    return posts


def main():
    print("Phase 11X: Featured Snippet Dominance Engine")
    print("=" * 60)

    posts_h2s = load_opportunities()
    total_h2s = sum(len(v) for v in posts_h2s.values())
    print(f"Found {total_h2s} convertible H2s across {len(posts_h2s)} posts in priority clusters")

    results = []
    posts_updated = 0
    h2s_converted = 0
    h2s_failed = 0
    h2s_skipped = 0

    sorted_posts = sorted(posts_h2s.items(), key=lambda x: len(x[1]), reverse=True)

    for idx, (post_id, h2_list) in enumerate(sorted_posts):
        title = h2_list[0]["title"]
        cluster = h2_list[0]["cluster"]
        print(f"\n[{idx+1}/{len(sorted_posts)}] Post {post_id}: {title} ({cluster})")
        print(f"  {len(h2_list)} H2s to convert")

        post_data = wp_get(post_id)
        if not post_data or "content" not in post_data:
            print(f"  ERROR: Could not fetch post {post_id}")
            for h2 in h2_list:
                results.append({
                    "post_id": post_id, "title": title, "cluster": cluster,
                    "h2_original": h2["h2_text"], "h2_new": "",
                    "answer_text": "", "word_count": 0,
                    "status": "fetch_error"
                })
                h2s_failed += 1
            continue

        content = post_data["content"]["raw"]
        sections = extract_sections(content)
        modified = False
        current_content = content

        for h2 in sorted(h2_list, key=lambda x: x["h2_position"], reverse=True):
            h2_text = h2["h2_text"]

            if h2_text not in sections:
                fuzz = [k for k in sections if h2_text[:20] in k]
                if fuzz:
                    h2_text = fuzz[0]
                else:
                    print(f"  SKIP: H2 '{h2['h2_text'][:40]}' not found in content")
                    results.append({
                        "post_id": post_id, "title": title, "cluster": cluster,
                        "h2_original": h2["h2_text"], "h2_new": "",
                        "answer_text": "", "word_count": 0,
                        "status": "not_found"
                    })
                    h2s_skipped += 1
                    continue

            section_info = sections[h2_text]
            section_text = section_info["text"]

            if len(section_text.split()) < 15:
                print(f"  SKIP: H2 '{h2_text[:40]}' section too short ({len(section_text.split())} words)")
                results.append({
                    "post_id": post_id, "title": title, "cluster": cluster,
                    "h2_original": h2["h2_text"], "h2_new": "",
                    "answer_text": "", "word_count": 0,
                    "status": "section_too_short"
                })
                h2s_skipped += 1
                continue

            question, answer = generate_question_and_answer(h2_text, section_text, title)

            if not question or not answer:
                print(f"  SKIP: Could not generate Q&A for '{h2_text[:40]}'")
                results.append({
                    "post_id": post_id, "title": title, "cluster": cluster,
                    "h2_original": h2["h2_text"], "h2_new": question or "",
                    "answer_text": "", "word_count": 0,
                    "status": "generation_failed"
                })
                h2s_skipped += 1
                continue

            sections_current = extract_sections(current_content)
            if h2_text in sections_current:
                match = sections_current[h2_text]["match"]
                current_content = insert_answer_after_h2(current_content, match, question, answer)
                modified = True
                word_count = len(answer.split())
                print(f"  OK: '{h2_text[:35]}' -> '{question[:35]}' ({word_count}w)")
                results.append({
                    "post_id": post_id, "title": title, "cluster": cluster,
                    "h2_original": h2["h2_text"], "h2_new": question,
                    "answer_text": answer, "word_count": word_count,
                    "status": "converted"
                })
                h2s_converted += 1
            else:
                print(f"  SKIP: H2 '{h2_text[:40]}' lost after prior edits")
                results.append({
                    "post_id": post_id, "title": title, "cluster": cluster,
                    "h2_original": h2["h2_text"], "h2_new": "",
                    "answer_text": "", "word_count": 0,
                    "status": "lost_in_edit"
                })
                h2s_skipped += 1

        if modified:
            ok, msg = wp_update(post_id, current_content)
            if ok:
                posts_updated += 1
                print(f"  POST UPDATED successfully")
            else:
                print(f"  POST UPDATE FAILED: {msg[:100]}")
                for r in results:
                    if r["post_id"] == post_id and r["status"] == "converted":
                        r["status"] = "update_failed"
                        h2s_converted -= 1
                        h2s_failed += 1

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "h2_original", "h2_new",
            "answer_text", "word_count", "status"
        ])
        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 60)
    print("PHASE 11X COMPLETE")
    print(f"Posts processed: {len(sorted_posts)}")
    print(f"Posts updated: {posts_updated}")
    print(f"H2s converted: {h2s_converted}")
    print(f"H2s skipped: {h2s_skipped}")
    print(f"H2s failed: {h2s_failed}")
    print(f"Output: {OUTPUT_CSV}")

    if total_h2s > 0:
        new_readiness = (h2s_converted / total_h2s) * 100
        print(f"Estimated snippet readiness improvement: +{new_readiness:.1f}% for priority clusters")


if __name__ == "__main__":
    main()
