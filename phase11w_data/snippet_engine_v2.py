#!/usr/bin/env python3
"""Phase 11X v2: Featured Snippet Dominance Engine
Scans WordPress directly for all statement H2s in priority clusters,
converts to question format with 40-60 word answer blocks.
"""

import csv
import json
import subprocess
import time
import re
import os
import tempfile
from collections import defaultdict

WP_AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_URL = "https://pethubonline.com/wp-json/wp/v2/posts"
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

PRIORITY_CATS = {
    1377: "Cat Supplies",
    1376: "Dog Supplies",
    1401: "Dog Beds",
    1467: "Dog Food",
    1413: "Indoor Cats",
}

ALL_CATS = {
    1377: "Cat Supplies", 1459: "Cat Toys", 1413: "Indoor Cats",
    1376: "Dog Supplies", 1397: "Pet Care", 1401: "Dog Beds",
    1489: "Dog Care", 1467: "Dog Food", 1422: "Dog Harnesses",
    1450: "Dog Health", 1441: "Dog Toys", 1442: "Puppy Care",
    1474: "Training Supplies", 1: "Uncategorized",
}

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(DATA_DIR, "Featured_Snippet_Acceleration.csv")

SKIP_H2_PATTERNS = [
    "sources and references",
    "sources and further reading",
    "compared:",
    "quick answer",
    "related articles",
    "related posts",
    "related guides",
    "frequently asked questions",
    "faq",
    "our editorial standards",
    "editorial standards",
    "table of contents",
]


def should_skip_h2(h2_text):
    lower = h2_text.strip().lower()
    for pat in SKIP_H2_PATTERNS:
        if lower.startswith(pat):
            return True
    return False


def is_question(h2_text):
    t = h2_text.strip()
    if t.endswith("?"):
        return True
    q_starts = ["what", "how", "why", "when", "which", "where", "who", "is", "are",
                 "do", "does", "can", "should", "will"]
    first_word = t.lower().split()[0] if t.split() else ""
    return first_word in q_starts


def wp_fetch_all_posts(cat_ids):
    """Fetch all published posts from priority categories."""
    all_posts = []
    for cat_id in cat_ids:
        page = 1
        while True:
            time.sleep(2)
            url = f"{WP_URL}?categories={cat_id}&status=publish&per_page=50&page={page}&context=edit&_fields=id,title,content,categories"
            r = subprocess.run(
                ["curl", "-s", "--compressed", "-u", WP_AUTH, url],
                capture_output=True, text=True, timeout=60
            )
            if r.returncode != 0:
                break
            try:
                posts = json.loads(r.stdout)
                if not isinstance(posts, list) or len(posts) == 0:
                    break
                for p in posts:
                    p["_cluster"] = PRIORITY_CATS.get(cat_id, ALL_CATS.get(cat_id, "Unknown"))
                all_posts.extend(posts)
                if len(posts) < 50:
                    break
                page += 1
            except json.JSONDecodeError:
                break
    seen = set()
    unique = []
    for p in all_posts:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)
    return unique


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


def call_openai_batch(h2_sections, post_title):
    """Call GPT-4o-mini with multiple H2s at once for efficiency."""
    sections_text = ""
    for i, (h2, text) in enumerate(h2_sections):
        sections_text += f"\n--- Section {i+1} ---\nH2: {h2}\nContent: {text[:400]}\n"

    system = """You are a UK pet care content editor optimizing for Google featured snippets.
Given multiple H2 headings and their section content, produce for each:
1. A natural question-format H2 (starting with What/How/Why/When/Which/Where)
2. A concise 40-60 word answer paragraph that directly answers the question

Rules:
- Questions must sound natural, not awkward or grammatically incorrect
- Answers must be factual, based ONLY on the provided section content
- Do NOT invent information not in the sections
- Do NOT use "we tested" or claim expertise not present in the content
- Do NOT reference specific brands unless they appear in the content
- UK English spelling
- Each answer should be a complete, standalone paragraph
- Keep answers between 40 and 60 words

Respond as a JSON array:
[{"section": 1, "question": "...", "answer": "..."}, ...]"""

    user = f"Post title: {post_title}\n{sections_text}"

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "max_tokens": 1500,
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
            capture_output=True, text=True, timeout=60
        )
        resp = json.loads(r.stdout)
        content = resp["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = re.sub(r'^```\w*\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
        return json.loads(content)
    except Exception as e:
        print(f"  OpenAI batch error: {e}")
        return []
    finally:
        os.unlink(tmp)


def find_h2_blocks(content):
    """Find all H2 heading blocks with their positions and text."""
    pattern = re.compile(
        r'(<!-- wp:heading[^>]*-->\s*<h2[^>]*>)(.*?)(</h2>\s*<!-- /wp:heading -->)',
        re.DOTALL
    )
    h2_blocks = []
    for m in pattern.finditer(content):
        raw_text = m.group(2)
        clean_text = re.sub(r'<[^>]+>', '', raw_text).strip()
        h2_blocks.append({
            "match": m,
            "clean_text": clean_text,
            "raw_inner": raw_text,
            "prefix": m.group(1),
            "suffix": m.group(3),
            "start": m.start(),
            "end": m.end(),
        })
    return h2_blocks


def extract_section_text(content, h2_end, next_h2_start):
    """Extract clean text from the section between two H2s."""
    section = content[h2_end:next_h2_start]
    text = re.sub(r'<!--.*?-->', '', section)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def has_snippet_answer(content, h2_end, next_h2_start):
    """Check if there's already a snippet-answer block right after this H2."""
    section = content[h2_end:h2_end + 300]
    return 'snippet-answer' in section


def main():
    print("Phase 11X v2: Featured Snippet Dominance Engine")
    print("=" * 60)

    print("Fetching posts from priority clusters...")
    posts = wp_fetch_all_posts(list(PRIORITY_CATS.keys()))
    print(f"Fetched {len(posts)} posts from priority clusters")

    results = []
    total_converted = 0
    total_skipped = 0
    total_already_done = 0
    posts_updated = 0

    for idx, post in enumerate(posts):
        post_id = post["id"]
        title = post["title"]["raw"] if isinstance(post["title"], dict) else str(post["title"])
        cluster = post.get("_cluster", "Unknown")
        content = post["content"]["raw"] if isinstance(post["content"], dict) else str(post["content"])

        h2_blocks = find_h2_blocks(content)
        if not h2_blocks:
            continue

        eligible_h2s = []
        for i, h2 in enumerate(h2_blocks):
            if should_skip_h2(h2["clean_text"]):
                continue
            if is_question(h2["clean_text"]):
                total_already_done += 1
                continue

            next_start = h2_blocks[i+1]["start"] if i+1 < len(h2_blocks) else len(content)
            if has_snippet_answer(content, h2["end"], next_start):
                total_already_done += 1
                continue

            section_text = extract_section_text(content, h2["end"], next_start)
            if len(section_text.split()) < 15:
                total_skipped += 1
                continue

            eligible_h2s.append((h2, section_text, i))

        if not eligible_h2s:
            continue

        print(f"\n[{idx+1}/{len(posts)}] Post {post_id}: {title[:60]} ({cluster})")
        print(f"  {len(eligible_h2s)} eligible H2s (of {len(h2_blocks)} total)")

        batch_input = [(h2["clean_text"], text) for h2, text, _ in eligible_h2s]
        qa_results = call_openai_batch(batch_input, title)

        if not qa_results or len(qa_results) == 0:
            print("  SKIP: GPT-4o-mini returned no results")
            for h2, text, i in eligible_h2s:
                results.append({
                    "post_id": post_id, "title": title, "cluster": cluster,
                    "h2_original": h2["clean_text"], "h2_new": "",
                    "answer_text": "", "word_count": 0, "status": "api_error"
                })
                total_skipped += 1
            continue

        qa_map = {}
        for item in qa_results:
            sec_idx = item.get("section", 0) - 1
            if 0 <= sec_idx < len(eligible_h2s):
                qa_map[sec_idx] = item

        current_content = content
        offset = 0
        conversions_this_post = 0

        for local_idx, (h2, section_text, global_idx) in enumerate(eligible_h2s):
            if local_idx not in qa_map:
                results.append({
                    "post_id": post_id, "title": title, "cluster": cluster,
                    "h2_original": h2["clean_text"], "h2_new": "",
                    "answer_text": "", "word_count": 0, "status": "no_qa_generated"
                })
                total_skipped += 1
                continue

            qa = qa_map[local_idx]
            question = qa.get("question", "").strip()
            answer = qa.get("answer", "").strip()

            if not question or not answer:
                total_skipped += 1
                continue

            word_count = len(answer.split())
            if word_count < 30 or word_count > 80:
                results.append({
                    "post_id": post_id, "title": title, "cluster": cluster,
                    "h2_original": h2["clean_text"], "h2_new": question,
                    "answer_text": answer, "word_count": word_count,
                    "status": "word_count_out_of_range"
                })
                total_skipped += 1
                continue

            old_start = h2["start"] + offset
            old_end = h2["end"] + offset
            old_block = current_content[old_start:old_end]

            new_h2_block = h2["prefix"] + question + h2["suffix"]
            answer_block = (
                '\n\n<!-- wp:paragraph {"className":"snippet-answer"} -->\n'
                f'<p class="snippet-answer">{answer}</p>\n'
                '<!-- /wp:paragraph -->'
            )
            replacement = new_h2_block + answer_block

            current_content = current_content[:old_start] + replacement + current_content[old_end:]
            offset += len(replacement) - len(old_block)

            print(f"  OK: '{h2['clean_text'][:35]}' -> '{question[:35]}' ({word_count}w)")
            results.append({
                "post_id": post_id, "title": title, "cluster": cluster,
                "h2_original": h2["clean_text"], "h2_new": question,
                "answer_text": answer, "word_count": word_count,
                "status": "converted"
            })
            total_converted += 1
            conversions_this_post += 1

        if conversions_this_post > 0:
            ok, msg = wp_update(post_id, current_content)
            if ok:
                posts_updated += 1
                print(f"  POST UPDATED ({conversions_this_post} conversions)")
            else:
                print(f"  UPDATE FAILED: {msg[:100]}")
                for r in results[-conversions_this_post:]:
                    if r["status"] == "converted":
                        r["status"] = "update_failed"
                        total_converted -= 1

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "post_id", "title", "cluster", "h2_original", "h2_new",
            "answer_text", "word_count", "status"
        ])
        writer.writeheader()
        writer.writerows(results)

    print("\n" + "=" * 60)
    print("PHASE 11X v2 COMPLETE")
    print(f"Posts scanned: {len(posts)}")
    print(f"Posts updated: {posts_updated}")
    print(f"H2s converted: {total_converted}")
    print(f"H2s already question/done: {total_already_done}")
    print(f"H2s skipped: {total_skipped}")
    print(f"Output: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
