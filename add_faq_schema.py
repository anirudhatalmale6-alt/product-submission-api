"""
Add FAQPage structured data (JSON-LD) to all posts that have FAQ sections.
This enables Google FAQ rich snippets, improving CTR in search results.
"""
import requests, json, time, re, html

WP_URL = 'https://pethubonline.com/wp-json/wp/v2'
AUTH = ('jasonsarah2026', 'yUmn Rngy EFE1 r7jr kjtm jmqx')

session = requests.Session()
session.auth = AUTH
session.headers.update({'Accept-Encoding': 'gzip, deflate'})

def extract_faq_pairs(content):
    """Extract Q&A pairs from the FAQ section of a post."""
    faq_section = None

    # Find FAQ section start
    faq_markers = [
        r'<h2[^>]*>.*?(?:FAQ|Frequently Asked Questions).*?</h2>',
    ]

    for marker in faq_markers:
        match = re.search(marker, content, re.IGNORECASE | re.DOTALL)
        if match:
            faq_section = content[match.start():]
            break

    if not faq_section:
        return []

    # Extract Q&A pairs - questions are typically in h3 tags or strong tags
    pairs = []

    # Pattern 1: h3 questions followed by paragraph answers
    h3_pattern = r'<h3[^>]*>(.*?)</h3>\s*(.*?)(?=<h3|<h2|$)'
    matches = re.findall(h3_pattern, faq_section, re.DOTALL | re.IGNORECASE)

    for question, answer_block in matches:
        q = clean_text(question)
        # Extract text from paragraphs in the answer block
        answer_parts = re.findall(r'<p[^>]*>(.*?)</p>', answer_block, re.DOTALL)
        if answer_parts:
            a = clean_text(' '.join(answer_parts))
        else:
            a = clean_text(answer_block)

        if q and a and len(q) > 5 and len(a) > 10:
            pairs.append({'question': q[:500], 'answer': a[:2000]})

    # Pattern 2: strong/bold questions if no h3 found
    if not pairs:
        strong_pattern = r'<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>\s*(.*?)(?=<(?:strong|b)|<h2|$)'
        matches = re.findall(strong_pattern, faq_section, re.DOTALL | re.IGNORECASE)
        for question, answer_block in matches:
            q = clean_text(question)
            if '?' not in q:
                continue
            answer_parts = re.findall(r'<p[^>]*>(.*?)</p>', answer_block, re.DOTALL)
            if answer_parts:
                a = clean_text(' '.join(answer_parts))
            else:
                a = clean_text(answer_block)
            if q and a and len(q) > 5 and len(a) > 10:
                pairs.append({'question': q[:500], 'answer': a[:2000]})

    return pairs[:10]  # Max 10 FAQ pairs per post

def clean_text(text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def build_faq_schema(pairs, post_url):
    """Build FAQPage JSON-LD schema."""
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": []
    }
    for pair in pairs:
        schema["mainEntity"].append({
            "@type": "Question",
            "name": pair["question"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": pair["answer"]
            }
        })
    return schema

def has_faq_schema(content):
    """Check if post already has FAQPage schema."""
    return 'FAQPage' in content

def inject_faq_schema(post_id, content, schema):
    """Add FAQ schema JSON-LD block to the end of post content."""
    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)
    schema_block = f'\n<!-- wp:html -->\n<script type="application/ld+json">\n{schema_json}\n</script>\n<!-- /wp:html -->'
    new_content = content + schema_block

    r = session.post(f'{WP_URL}/posts/{post_id}', json={'content': new_content})
    return r.status_code == 200

# Main execution
print("Fetching all published posts...")
all_posts = []
page = 1
while True:
    r = session.get(f'{WP_URL}/posts', params={
        'per_page': 100, 'page': page, 'status': 'publish',
        '_fields': 'id,title,link'
    })
    if r.status_code != 200:
        break
    posts = r.json()
    if not posts:
        break
    all_posts.extend(posts)
    page += 1
    time.sleep(0.5)

print(f"Total posts: {len(all_posts)}")

added = 0
skipped_no_faq = 0
skipped_has_schema = 0
skipped_no_pairs = 0
errors = 0

for i, post in enumerate(all_posts):
    pid = post['id']
    title = post['title']['rendered']

    # Fetch content
    r = session.get(f'{WP_URL}/posts/{pid}', params={'_fields': 'id,content'})
    if r.status_code != 200:
        errors += 1
        continue

    content = r.json()['content']['rendered']

    # Check if has FAQ section
    has_faq = bool(re.search(r'<h2[^>]*>.*?(?:FAQ|Frequently Asked Questions).*?</h2>', content, re.IGNORECASE | re.DOTALL))

    if not has_faq:
        skipped_no_faq += 1
        continue

    # Check if already has schema
    if has_faq_schema(content):
        skipped_has_schema += 1
        continue

    # Extract FAQ pairs
    pairs = extract_faq_pairs(content)
    if not pairs:
        skipped_no_pairs += 1
        continue

    # Build and inject schema
    schema = build_faq_schema(pairs, post['link'])

    if inject_faq_schema(pid, content, schema):
        added += 1
    else:
        errors += 1

    time.sleep(1.5)

    if (i + 1) % 50 == 0:
        print(f"Progress: {i+1}/{len(all_posts)} | Schema added: {added} | No FAQ: {skipped_no_faq} | Has schema: {skipped_has_schema} | No pairs: {skipped_no_pairs} | Errors: {errors}")

print(f"\n{'='*60}")
print(f"FAQ SCHEMA INJECTION COMPLETE")
print(f"{'='*60}")
print(f"Total posts: {len(all_posts)}")
print(f"Schema added: {added}")
print(f"Skipped (no FAQ section): {skipped_no_faq}")
print(f"Skipped (already has schema): {skipped_has_schema}")
print(f"Skipped (no extractable pairs): {skipped_no_pairs}")
print(f"Errors: {errors}")

results = {
    'total_posts': len(all_posts),
    'schema_added': added,
    'skipped_no_faq': skipped_no_faq,
    'skipped_has_schema': skipped_has_schema,
    'skipped_no_pairs': skipped_no_pairs,
    'errors': errors
}
with open('/var/lib/freelancer/projects/40416335/faq_schema_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Results saved to faq_schema_results.json")
