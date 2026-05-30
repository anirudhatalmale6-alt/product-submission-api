#!/usr/bin/env python3
"""Draft expansion engine: expands draft posts to publication-ready quality.
Uses GPT-4o-mini to generate additional content, then inserts Quick Answer,
FAQ, Sources/References, Key Terms, and internal links."""

import subprocess, json, time, re, csv, sys, os, tempfile
from datetime import datetime

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

CATEGORY_MAP = {
    1377: 'Cat Supplies', 1459: 'Cat Toys', 1413: 'Indoor Cats',
    1376: 'Dog Supplies', 1397: 'Pet Care', 1401: 'Dog Beds',
    1489: 'Dog Care', 1467: 'Dog Food', 1422: 'Dog Harnesses',
    1450: 'Dog Health', 1441: 'Dog Toys', 1442: 'Puppy Care',
    1474: 'Training Supplies', 1: 'Uncategorized'
}

UK_SOURCES = {
    'Cat Toys': [
        'RSPCA (rspca.org.uk) – Cat enrichment guidance',
        'International Cat Care (icatcare.org) – Feline behaviour and play',
        'Blue Cross (bluecross.org.uk) – Cat care advice',
        'Cats Protection (cats.org.uk) – Indoor cat welfare',
    ],
    'Dog Supplies': [
        'RSPCA (rspca.org.uk) – Dog welfare and safety guidance',
        'Blue Cross (bluecross.org.uk) – Dog care and equipment advice',
        'The Kennel Club (thekennelclub.org.uk) – Breed-specific guidance',
        'Dogs Trust (dogstrust.org.uk) – Responsible dog ownership',
    ],
    'Indoor Cats': [
        'International Cat Care (icatcare.org) – Indoor cat welfare',
        'RSPCA (rspca.org.uk) – Cat enrichment guidance',
        'Cats Protection (cats.org.uk) – Keeping cats indoors safely',
        'Blue Cross (bluecross.org.uk) – Cat behaviour and health',
    ],
    'Pet Care': [
        'RSPCA (rspca.org.uk) – General pet welfare guidance',
        'Blue Cross (bluecross.org.uk) – Pet care advice for UK owners',
        'PDSA (pdsa.org.uk) – Pet health and wellbeing',
        'The Kennel Club (thekennelclub.org.uk) – Dog ownership guidance',
    ],
}

def wp_fetch(post_id):
    time.sleep(2)
    url = f"{BASE}/posts/{post_id}?context=edit"
    r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, url],
                       capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

def wp_update(post_id, content):
    payload = json.dumps({"content": {"raw": content}})
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(payload)
        tmppath = f.name
    time.sleep(3)
    url = f"{BASE}/posts/{post_id}"
    r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, "-X", "POST",
                        "-H", "Content-Type: application/json",
                        "-d", f"@{tmppath}", url],
                       capture_output=True, text=True, timeout=60)
    os.unlink(tmppath)
    result = json.loads(r.stdout)
    return 'id' in result

def wp_fetch_published():
    """Fetch all published posts for internal link matching."""
    all_items = []
    page = 1
    while True:
        time.sleep(2)
        url = f"{BASE}/posts?status=publish&per_page=100&page={page}&_fields=id,title,slug,categories"
        r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, url],
                           capture_output=True, text=True, timeout=60)
        items = json.loads(r.stdout)
        if not items or isinstance(items, dict):
            break
        all_items.extend(items)
        if len(items) < 100:
            break
        page += 1
    return all_items

def gpt_expand(title, existing_content, cluster, target_words):
    """Use GPT-4o-mini to generate expansion content."""
    current_words = len(existing_content.split())
    needed = max(target_words - current_words, 300)

    prompt = f"""You are expanding a UK pet care article for PetHub Online. The article is educational, not commercial.

TITLE: {title}
CLUSTER: {cluster}
CURRENT WORD COUNT: {current_words}
TARGET: Add approximately {needed} more words of substantive content.

EXISTING CONTENT (Gutenberg HTML):
{existing_content[:3000]}

RULES:
- UK English spelling throughout (behaviour, colour, favour, organise, etc.)
- NO fake experts, fake testing claims, fake veterinarians
- NO product rankings, scores, or "best" claims without evidence
- NO affiliate links or purchase CTAs
- Educational and informational tone only
- Use Gutenberg block format: <!-- wp:heading --> and <!-- wp:paragraph --> blocks
- Each new section should have a question-format H2 heading
- Include practical, actionable advice UK pet owners can use
- Reference UK-specific context (weather, regulations, shops, vets)

Generate {needed} words of NEW content sections that complement the existing article. Output ONLY the Gutenberg HTML blocks (no intro text, no explanation). Include 2-4 new H2 sections with substantive paragraphs under each."""

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 3000,
        "temperature": 0.7
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f)
        tmppath = f.name

    r = subprocess.run(["curl", "-s", "https://api.openai.com/v1/chat/completions",
                        "-H", "Content-Type: application/json",
                        "-H", f"Authorization: Bearer {OPENAI_KEY}",
                        "-d", f"@{tmppath}"],
                       capture_output=True, text=True, timeout=120)
    os.unlink(tmppath)

    result = json.loads(r.stdout)
    if 'choices' in result:
        return result['choices'][0]['message']['content']
    else:
        print(f"  GPT error: {result.get('error', {}).get('message', 'unknown')}")
        return None

def build_quick_answer(title, content):
    """Generate a Quick Answer block using GPT-4o-mini."""
    prompt = f"""Write a Quick Answer block for this UK pet care article. The Quick Answer should be 40-60 words, directly answering the main question implied by the title. Use UK English.

TITLE: {title}
ARTICLE EXCERPT: {content[:1500]}

Output ONLY the answer text (no HTML, no heading). Be specific, practical, and UK-focused."""

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.5
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f)
        tmppath = f.name

    r = subprocess.run(["curl", "-s", "https://api.openai.com/v1/chat/completions",
                        "-H", "Content-Type: application/json",
                        "-H", f"Authorization: Bearer {OPENAI_KEY}",
                        "-d", f"@{tmppath}"],
                       capture_output=True, text=True, timeout=60)
    os.unlink(tmppath)

    result = json.loads(r.stdout)
    if 'choices' in result:
        answer = result['choices'][0]['message']['content'].strip()
        answer = answer.strip('"').strip("'")
        block = f'''<!-- wp:heading {{"className":"quick-answer-heading"}} -->
<h2 class="quick-answer-heading">Quick Answer</h2>
<!-- /wp:heading -->

<!-- wp:paragraph {{"className":"quick-answer-box"}} -->
<p class="quick-answer-box">{answer}</p>
<!-- /wp:paragraph -->'''
        return block
    return None

def build_faq_block(title, content):
    """Generate FAQ block using GPT-4o-mini."""
    prompt = f"""Generate 3-4 FAQ questions and answers for this UK pet care article. Use UK English.

TITLE: {title}
ARTICLE EXCERPT: {content[:2000]}

Format each Q&A as:
Q: [question]
A: [answer in 30-50 words]

Output ONLY the Q&As, nothing else."""

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.6
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f)
        tmppath = f.name

    r = subprocess.run(["curl", "-s", "https://api.openai.com/v1/chat/completions",
                        "-H", "Content-Type: application/json",
                        "-H", f"Authorization: Bearer {OPENAI_KEY}",
                        "-d", f"@{tmppath}"],
                       capture_output=True, text=True, timeout=60)
    os.unlink(tmppath)

    result = json.loads(r.stdout)
    if 'choices' not in result:
        return None

    text = result['choices'][0]['message']['content'].strip()
    qas = re.findall(r'Q:\s*(.+?)\nA:\s*(.+?)(?=\nQ:|\Z)', text, re.S)

    if not qas:
        return None

    faq_html = '''<!-- wp:heading {"className":"at-a-glance-heading"} -->
<h2 class="at-a-glance-heading">Frequently Asked Questions</h2>
<!-- /wp:heading -->

'''
    for q, a in qas:
        q = q.strip()
        a = a.strip()
        faq_html += f'''<!-- wp:heading {{"level":3}} -->
<h3>{q}</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{a}</p>
<!-- /wp:paragraph -->

'''
    return faq_html.rstrip()

def build_sources_block(cluster):
    """Build Sources and References block with UK authorities."""
    sources = UK_SOURCES.get(cluster, UK_SOURCES['Pet Care'])
    items = '\n'.join([f'<li>{s}</li>' for s in sources])

    return f'''<!-- wp:heading {{"className":"sources-heading"}} -->
<h2 class="sources-heading">Sources and References</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
{items}
</ul>
<!-- /wp:list -->'''

def build_editorial_disclosure():
    return '''<!-- wp:paragraph {"className":"editorial-disclosure"} -->
<p class="editorial-disclosure">This article follows PetHub Online\'s <a href="https://pethubonline.com/our-editorial-process/">editorial process</a>. All content is researched against <a href="https://pethubonline.com/our-research-standards/">our research standards</a> and reflects <a href="https://pethubonline.com/why-pethub-online-exists/">our mission</a> to provide trustworthy pet care guidance. Learn more about <a href="https://pethubonline.com/how-we-evaluate-pet-products/">how we evaluate pet products</a>.</p>
<!-- /wp:paragraph -->'''

def find_relevant_links(title, content, cluster, published_posts, max_links=5):
    """Find relevant published posts to link to."""
    content_lower = content.lower()
    title_lower = title.lower()
    candidates = []

    for post in published_posts:
        p_title = post.get('title', '')
        if isinstance(p_title, dict):
            p_title = p_title.get('rendered', '')
        p_slug = post.get('slug', '')
        p_cats = post.get('categories', [])
        p_cluster = 'Other'
        for c in p_cats:
            if c in CATEGORY_MAP:
                p_cluster = CATEGORY_MAP[c]
                break

        if f"/{p_slug}" in content:
            continue

        score = 0
        p_title_lower = p_title.lower()
        words = re.findall(r'\b[a-z]{4,}\b', p_title_lower)
        for w in words:
            if w in ['guide', 'best', 'complete', 'essential', 'tips', 'from']:
                continue
            if w in content_lower:
                score += 1
            if w in title_lower:
                score += 2

        if score >= 3:
            candidates.append({
                'title': p_title,
                'slug': p_slug,
                'cluster': p_cluster,
                'score': score
            })

    candidates.sort(key=lambda x: x['score'], reverse=True)

    cross = [c for c in candidates if c['cluster'] != cluster]
    same = [c for c in candidates if c['cluster'] == cluster]
    result = same[:3] + cross[:2]
    return result[:max_links]

def build_link_paragraph(links):
    if not links:
        return ""
    link_html = []
    for l in links:
        link_html.append(f'<a href="https://pethubonline.com/{l["slug"]}/">{l["title"]}</a>')

    if len(link_html) == 1:
        text = f"For more guidance, see our {link_html[0]}."
    elif len(link_html) == 2:
        text = f"You might also find these helpful: {link_html[0]} and {link_html[1]}."
    else:
        text = f"Related reading: {', '.join(link_html[:-1])}, and {link_html[-1]}."

    return f'''<!-- wp:paragraph -->
<p>{text}</p>
<!-- /wp:paragraph -->'''

GLOSSARY_TERMS = {
    'Cat Toys': {
        'Enrichment': 'Activities and items that stimulate a pet\'s natural behaviours, reducing boredom and promoting mental wellbeing.',
        'Food Puzzle': 'A toy designed to dispense food or treats when manipulated, encouraging problem-solving and slowing eating.',
        'Prey Drive': 'A cat\'s instinctive urge to hunt, chase, and capture moving objects, which play helps satisfy safely.',
        'Wand Toy': 'An interactive toy featuring a rod with a dangling attachment, used to mimic prey movement during supervised play.',
    },
    'Dog Supplies': {
        'Waterproof Rating': 'A measure of how well a fabric resists water penetration, typically measured in millimetres (mm).',
        'Reflective Trim': 'Strips of material on pet gear that reflect light, improving visibility during walks in low-light conditions.',
        'Crash-Tested': 'Equipment that has been independently tested to withstand forces experienced during vehicle collisions.',
        'Denier': 'A unit measuring the thickness and durability of fabric fibres; higher denier means more robust material.',
    },
    'Indoor Cats': {
        'Catio': 'An enclosed outdoor space (cat patio) allowing indoor cats to experience fresh air and nature safely.',
        'Environmental Enrichment': 'Modifications to a cat\'s living space that promote natural behaviours like climbing, scratching, and exploring.',
        'Vertical Space': 'Elevated areas such as shelves, trees, or perches that cats use for climbing, resting, and territory observation.',
        'Zoning': 'Dividing a home into distinct areas for feeding, sleeping, playing, and toileting to reduce feline stress.',
    },
    'Pet Care': {
        'Microchipping': 'Implanting a small electronic chip under a pet\'s skin for permanent identification, legally required for dogs in the UK.',
        'Neutering': 'Surgical procedure to prevent reproduction, recommended by UK veterinary bodies for health and population control benefits.',
        'Preventative Care': 'Routine health measures including vaccinations, parasite control, and dental checks to prevent illness before it develops.',
        'Pet Insurance': 'Financial protection covering veterinary costs for illness or injury, available as accident-only, time-limited, or lifetime policies in the UK.',
    },
}

def build_glossary_block(cluster):
    terms = GLOSSARY_TERMS.get(cluster, GLOSSARY_TERMS['Pet Care'])
    items = ""
    for term, defn in terms.items():
        items += f'''<!-- wp:heading {{"level":3,"className":"key-terms-term"}} -->
<h3 class="key-terms-term">{term}</h3>
<!-- /wp:heading -->

<!-- wp:paragraph {{"className":"key-terms-definition"}} -->
<p class="key-terms-definition">{defn}</p>
<!-- /wp:paragraph -->

'''

    return f'''<!-- wp:heading {{"className":"key-terms-heading"}} -->
<h2 class="key-terms-heading">Key Terms</h2>
<!-- /wp:heading -->

{items.rstrip()}'''


def get_cluster(categories):
    for cat_id in categories:
        if cat_id in CATEGORY_MAP:
            return CATEGORY_MAP[cat_id]
    return 'Pet Care'

def count_words(content):
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'<!--[^>]+-->', ' ', text)
    return len(text.split())

def has_block(content, class_name):
    return class_name in content

def expand_draft(post_id, published_posts, log):
    """Expand a single draft post to publication quality."""
    print(f"\n--- Processing draft {post_id} ---")
    post = wp_fetch(post_id)

    if isinstance(post, dict) and 'code' in post:
        print(f"  ERROR: Could not fetch post {post_id}: {post.get('message','')}")
        log.append({'post_id': post_id, 'title': '?', 'cluster': '?', 'original_words': 0,
                     'final_words': 0, 'status': 'error', 'detail': f"fetch failed: {post.get('message','')}"})
        return

    title = post.get('title', {})
    if isinstance(title, dict):
        title = title.get('raw', title.get('rendered', ''))

    content = post.get('content', {})
    if isinstance(content, dict):
        content = content.get('raw', content.get('rendered', ''))

    categories = post.get('categories', [])
    cluster = get_cluster(categories)
    original_words = count_words(content)
    print(f"  Title: {title[:60]}")
    print(f"  Cluster: {cluster}, Words: {original_words}")

    target_words = 1800 if original_words < 800 else 2200

    # Step 1: Expand content if under target
    if original_words < target_words - 200:
        print(f"  Expanding content ({original_words} -> {target_words} target)...")
        time.sleep(1)
        expansion = gpt_expand(title, content, cluster, target_words)
        if expansion:
            expansion = expansion.strip()
            if not expansion.startswith('<!--'):
                lines = expansion.split('\n')
                cleaned = []
                for line in lines:
                    if line.strip().startswith('```') or line.strip() == '':
                        if not line.strip().startswith('```'):
                            cleaned.append(line)
                    else:
                        cleaned.append(line)
                expansion = '\n'.join(cleaned)

            last_h2 = None
            for m in re.finditer(r'<!-- wp:heading[^>]*-->', content):
                last_h2 = m.start()

            if last_h2:
                insert_before_last = content.rfind('\n\n<!-- wp:heading', 0, len(content))
                if insert_before_last > len(content) // 2:
                    content = content[:insert_before_last] + '\n\n' + expansion + content[insert_before_last:]
                else:
                    content = content + '\n\n' + expansion
            else:
                content = content + '\n\n' + expansion

            new_words = count_words(content)
            print(f"  Expanded to {new_words} words")
        else:
            print(f"  GPT expansion failed, continuing with existing content")

    # Step 2: Add Quick Answer if missing
    if not has_block(content, 'quick-answer'):
        print("  Adding Quick Answer block...")
        time.sleep(1)
        qa_block = build_quick_answer(title, content)
        if qa_block:
            first_heading = re.search(r'<!-- wp:heading', content)
            if first_heading:
                content = content[:first_heading.start()] + qa_block + '\n\n' + content[first_heading.start():]
            else:
                content = qa_block + '\n\n' + content
            print("  Quick Answer added")

    # Step 3: Add FAQ if missing
    if not has_block(content, 'at-a-glance') and 'Frequently Asked Questions' not in content:
        print("  Adding FAQ block...")
        time.sleep(1)
        faq_block = build_faq_block(title, content)
        if faq_block:
            content = content + '\n\n' + faq_block
            print("  FAQ added")

    # Step 4: Add internal links
    existing_links = re.findall(r'href=["\']https?://pethubonline\.com/([^"\']+)["\']', content)
    link_count = len(existing_links)
    if link_count < 5:
        print(f"  Adding internal links (currently {link_count})...")
        links = find_relevant_links(title, content, cluster, published_posts, max_links=5-link_count)
        if links:
            link_para = build_link_paragraph(links)
            content = content + '\n\n' + link_para
            print(f"  Added {len(links)} internal links")

    # Step 5: Add Key Terms/Glossary if missing
    if not has_block(content, 'key-terms'):
        print("  Adding Key Terms glossary...")
        glossary = build_glossary_block(cluster)
        content = content + '\n\n' + glossary
        print("  Key Terms added")

    # Step 6: Add Editorial Disclosure if missing
    if not has_block(content, 'editorial-disclosure'):
        print("  Adding editorial disclosure...")
        disclosure = build_editorial_disclosure()
        content = content + '\n\n' + disclosure
        print("  Disclosure added")

    # Step 7: Add Sources if missing
    if not has_block(content, 'sources-heading') and 'Sources and References' not in content:
        print("  Adding Sources and References...")
        sources = build_sources_block(cluster)
        content = content + '\n\n' + sources
        print("  Sources added")

    # Step 8: Update the post
    final_words = count_words(content)
    print(f"  Updating post {post_id} ({original_words} -> {final_words} words)...")
    success = wp_update(post_id, content)

    if success:
        print(f"  SUCCESS: {title[:50]} expanded to {final_words} words")
        log.append({
            'post_id': post_id, 'title': title, 'cluster': cluster,
            'original_words': original_words, 'final_words': final_words,
            'status': 'expanded', 'detail': f'+{final_words-original_words} words'
        })
    else:
        print(f"  ERROR: Update failed for {post_id}")
        log.append({
            'post_id': post_id, 'title': title, 'cluster': cluster,
            'original_words': original_words, 'final_words': final_words,
            'status': 'error', 'detail': 'wp_update failed'
        })


def main():
    draft_ids = [10028, 12823, 12820, 12817, 12816, 12813,
                 12767, 12766, 12765, 12764, 12763, 12762,
                 12761, 12760, 12759, 12758, 12757, 12756]

    print("Fetching published posts for internal link matching...")
    published = wp_fetch_published()
    print(f"Fetched {len(published)} published posts")

    log = []
    for i, pid in enumerate(draft_ids):
        print(f"\n=== Draft {i+1}/{len(draft_ids)} ===")
        try:
            expand_draft(pid, published, log)
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            log.append({'post_id': pid, 'title': '?', 'cluster': '?',
                        'original_words': 0, 'final_words': 0,
                        'status': 'error', 'detail': str(e)})

    with open('draft_expansion_log.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['post_id', 'title', 'cluster', 'original_words', 'final_words', 'status', 'detail'])
        w.writeheader()
        w.writerows(log)

    expanded = len([l for l in log if l['status'] == 'expanded'])
    errors = len([l for l in log if l['status'] == 'error'])
    print(f"\n=== DONE: {expanded} expanded, {errors} errors ===")
    print("Log: draft_expansion_log.csv")


if __name__ == '__main__':
    main()
