#!/usr/bin/env python3
"""Phase 11X v3: Featured Snippet Dominance — ALL clusters
Processes all 168 posts across all 14 clusters for maximum snippet readiness.
"""

import csv
import json
import subprocess
import time
import re
import os
import tempfile

WP_AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_URL = "https://pethubonline.com/wp-json/wp/v2/posts"
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(DATA_DIR, "Featured_Snippet_Acceleration_Full.csv")

ALL_CATS = {
    1377: "Cat Supplies", 1459: "Cat Toys", 1413: "Indoor Cats",
    1376: "Dog Supplies", 1397: "Pet Care", 1401: "Dog Beds",
    1489: "Dog Care", 1467: "Dog Food", 1422: "Dog Harnesses",
    1450: "Dog Health", 1441: "Dog Toys", 1442: "Puppy Care",
    1474: "Training Supplies", 1: "Uncategorized",
}

SKIP_LOWER = [
    "sources and references", "sources and further reading",
    "compared:", "quick answer", "related articles", "related posts",
    "related reading", "related guides", "frequently asked questions",
    "faq", "our editorial standards", "editorial standards",
    "table of contents",
]

Q_STARTS = {"what","how","why","when","which","where","who","is","are","do","does","can","should","will"}


def should_skip(h2):
    lower = h2.strip().lower()
    return any(lower.startswith(p) for p in SKIP_LOWER)


def is_question(h2):
    t = h2.strip()
    if t.endswith("?"): return True
    fw = t.lower().split()[0] if t.split() else ""
    return fw in Q_STARTS


def wp_fetch_all():
    all_posts = []
    page = 1
    while True:
        time.sleep(2)
        url = f"{WP_URL}?status=publish&per_page=100&page={page}&context=edit&_fields=id,title,content,categories"
        r = subprocess.run(["curl","-s","--compressed","-u",WP_AUTH,url],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0: break
        try:
            posts = json.loads(r.stdout)
            if not isinstance(posts, list) or len(posts) == 0: break
            all_posts.extend(posts)
            if len(posts) < 100: break
            page += 1
        except json.JSONDecodeError: break
    return all_posts


def get_cluster(cats):
    for c in (cats if isinstance(cats, list) else []):
        if c in ALL_CATS:
            return ALL_CATS[c]
    return "Unknown"


def wp_update(post_id, content):
    time.sleep(3)
    payload = json.dumps({"content": content})
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(payload); tmp = f.name
    try:
        r = subprocess.run(["curl","-s","--compressed","-u",WP_AUTH,
            "-X","POST","-H","Content-Type: application/json",
            "-d",f"@{tmp}",f"{WP_URL}/{post_id}"],
            capture_output=True, text=True, timeout=60)
        resp = json.loads(r.stdout)
        return ("id" in resp), (resp.get("message","ok") if "id" not in resp else "ok")
    except Exception as e:
        return False, str(e)
    finally:
        os.unlink(tmp)


def call_openai(h2_sections, title):
    sections_text = ""
    for i, (h2, text) in enumerate(h2_sections):
        sections_text += f"\n--- Section {i+1} ---\nH2: {h2}\nContent: {text[:350]}\n"

    system = """You are a UK pet care content editor optimizing for Google featured snippets.
For each H2 heading and section content, produce:
1. A natural question-format H2 (What/How/Why/When/Which/Where)
2. A 40-60 word answer paragraph directly answering the question

Rules:
- Questions must sound natural and grammatically correct
- Answers based ONLY on provided content, no invented information
- No "we tested" claims, no fake expertise
- UK English spelling
- Each answer: standalone paragraph, 40-60 words

JSON array response: [{"section": 1, "question": "...", "answer": "..."}, ...]"""

    payload = {"model":"gpt-4o-mini","messages":[
        {"role":"system","content":system},
        {"role":"user","content":f"Post: {title}\n{sections_text}"}
    ],"max_tokens":2000,"temperature":0.3}
    with tempfile.NamedTemporaryFile(mode="w",suffix=".json",delete=False) as f:
        json.dump(payload, f); tmp = f.name
    try:
        r = subprocess.run(["curl","-s","https://api.openai.com/v1/chat/completions",
            "-H",f"Authorization: Bearer {OPENAI_KEY}",
            "-H","Content-Type: application/json","-d",f"@{tmp}"],
            capture_output=True, text=True, timeout=60)
        resp = json.loads(r.stdout)
        c = resp["choices"][0]["message"]["content"].strip()
        if c.startswith("```"): c = re.sub(r'^```\w*\n?','',c); c = re.sub(r'\n?```$','',c)
        return json.loads(c)
    except Exception as e:
        print(f"  API err: {e}")
        return []
    finally:
        os.unlink(tmp)


def find_h2s(content):
    pat = re.compile(r'(<!-- wp:heading[^>]*-->\s*<h2[^>]*>)(.*?)(</h2>\s*<!-- /wp:heading -->)', re.DOTALL)
    blocks = []
    for m in pat.finditer(content):
        clean = re.sub(r'<[^>]+>','',m.group(2)).strip()
        blocks.append({"match":m,"clean":clean,"prefix":m.group(1),"suffix":m.group(3),
                        "start":m.start(),"end":m.end()})
    return blocks


def section_text(content, h2_end, next_start):
    s = content[h2_end:next_start]
    s = re.sub(r'<!--.*?-->','',s); s = re.sub(r'<[^>]+>','',s)
    return re.sub(r'\s+',' ',s).strip()


def main():
    print("Phase 11X v3: ALL-CLUSTER Snippet Optimization")
    print("=" * 60)

    posts = wp_fetch_all()
    print(f"Fetched {len(posts)} published posts")

    results = []
    converted = 0; already = 0; skipped = 0; updated = 0
    cluster_stats = {}

    for idx, post in enumerate(posts):
        pid = post["id"]
        title = post["title"]["raw"] if isinstance(post["title"],dict) else str(post["title"])
        cluster = get_cluster(post.get("categories",[]))
        content = post["content"]["raw"] if isinstance(post["content"],dict) else str(post["content"])

        h2s = find_h2s(content)
        if not h2s: continue

        eligible = []
        for i, h2 in enumerate(h2s):
            if should_skip(h2["clean"]): continue
            if is_question(h2["clean"]): already += 1; continue
            ns = h2s[i+1]["start"] if i+1<len(h2s) else len(content)
            if 'snippet-answer' in content[h2["end"]:h2["end"]+300]:
                already += 1; continue
            st = section_text(content, h2["end"], ns)
            if len(st.split()) < 15: skipped += 1; continue
            eligible.append((h2, st, i))

        if not eligible: continue

        print(f"\n[{idx+1}/{len(posts)}] {pid}: {title[:55]} ({cluster}) — {len(eligible)} eligible")

        batch = [(h["clean"],t) for h,t,_ in eligible]
        # Process in batches of 8
        for batch_start in range(0, len(batch), 8):
            batch_chunk = batch[batch_start:batch_start+8]
            eligible_chunk = eligible[batch_start:batch_start+8]
            qa = call_openai(batch_chunk, title)
            qa_map = {}
            for item in qa:
                si = item.get("section",0)-1
                if 0 <= si < len(eligible_chunk):
                    qa_map[si] = item

            for li, (h2, st, gi) in enumerate(eligible_chunk):
                if li not in qa_map:
                    skipped += 1; continue
                q = qa_map[li].get("question","").strip()
                a = qa_map[li].get("answer","").strip()
                if not q or not a: skipped += 1; continue
                wc = len(a.split())
                if wc < 30 or wc > 80: skipped += 1; continue

                results.append({"post_id":pid,"title":title,"cluster":cluster,
                    "h2_original":h2["clean"],"h2_new":q,"answer_text":a,
                    "word_count":wc,"status":"converted"})
                converted += 1
                cluster_stats[cluster] = cluster_stats.get(cluster,0)+1
                print(f"  OK: '{h2['clean'][:30]}' -> '{q[:30]}' ({wc}w)")

        # Apply all conversions
        if any(r["post_id"]==pid and r["status"]=="converted" for r in results):
            current = content
            conv_for_post = [r for r in results if r["post_id"]==pid and r["status"]=="converted"]

            h2s_current = find_h2s(current)
            offset = 0
            applied = 0
            for r in conv_for_post:
                orig = r["h2_original"]
                for h2 in find_h2s(current):
                    if h2["clean"] == orig:
                        old_s = h2["start"]
                        old_e = h2["end"]
                        new_block = h2["prefix"] + r["h2_new"] + h2["suffix"]
                        ans_block = ('\n\n<!-- wp:paragraph {"className":"snippet-answer"} -->\n'
                            f'<p class="snippet-answer">{r["answer_text"]}</p>\n'
                            '<!-- /wp:paragraph -->')
                        current = current[:old_s] + new_block + ans_block + current[old_e:]
                        applied += 1
                        break

            if applied > 0:
                ok, msg = wp_update(pid, current)
                if ok:
                    updated += 1
                    print(f"  UPDATED ({applied} conversions)")
                else:
                    print(f"  FAILED: {msg[:80]}")

    with open(OUTPUT_CSV,'w',newline='',encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=["post_id","title","cluster","h2_original",
            "h2_new","answer_text","word_count","status"])
        w.writeheader(); w.writerows(results)

    print("\n" + "=" * 60)
    print("PHASE 11X v3 COMPLETE")
    print(f"Posts scanned: {len(posts)}")
    print(f"Posts updated: {updated}")
    print(f"H2s converted: {converted}")
    print(f"H2s already question/done: {already}")
    print(f"H2s skipped: {skipped}")
    print(f"\nConversions per cluster:")
    for c in sorted(cluster_stats, key=lambda x: -cluster_stats[x]):
        print(f"  {c}: {cluster_stats[c]}")
    print(f"\nOutput: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
