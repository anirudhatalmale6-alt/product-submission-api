#!/usr/bin/env python3
"""
Add Conclusion/Final Verdict sections to PetHub Online WordPress posts that are missing them.
"""

import subprocess
import json
import re
import time
import os
import html

WP_API = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
LOG_FILE = "/var/lib/freelancer/projects/40416335/phase14_data/Conclusions_Log.txt"

# Regex to detect existing conclusion/verdict sections
CONCLUSION_REGEX = re.compile(
    r'<h[23][^>]*>[^<]*(Conclusion|Final Verdict|Final Thoughts|Our Pick|Summary|Verdict|The Bottom Line|Wrapping Up)',
    re.IGNORECASE
)

# Regex to detect sources/references section
SOURCES_REGEX = re.compile(
    r'(<h[23][^>]*>[^<]*(Sources|References|Bibliography|Works Cited|Citations)[^<]*</h[23]>)',
    re.IGNORECASE
)

def curl_get(url):
    """GET request via curl subprocess."""
    result = subprocess.run(
        ['curl', '-s', '-u', f'{WP_USER}:{WP_PASS}', url, '-H', 'Content-Type: application/json'],
        capture_output=True, text=True, timeout=60
    )
    return json.loads(result.stdout)

def curl_post_update(post_id, data):
    """POST update via curl subprocess."""
    json_data = json.dumps(data)
    result = subprocess.run(
        ['curl', '-s', '-X', 'POST', '-u', f'{WP_USER}:{WP_PASS}',
         f'{WP_API}/posts/{post_id}',
         '-H', 'Content-Type: application/json',
         '-d', json_data],
        capture_output=True, text=True, timeout=60
    )
    try:
        resp = json.loads(result.stdout)
        return resp
    except json.JSONDecodeError:
        return {"error": result.stdout[:500]}

def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_API}/posts?status=publish&per_page=100&page={page}&_fields=id,title,content"
        posts = curl_get(url)
        if not posts or isinstance(posts, dict):
            break
        all_posts.extend(posts)
        if len(posts) < 100:
            break
        page += 1
        time.sleep(1)
    return all_posts

def strip_html(html_text):
    """Strip HTML tags for content analysis."""
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_key_points(content_html, title):
    """Extract key points from the article content for conclusion generation."""
    text = strip_html(content_html)

    # Get headings to understand structure
    headings = re.findall(r'<h[23][^>]*>([^<]+)</h[23]>', content_html)

    # Get the first paragraph for topic context
    first_paras = re.findall(r'<p[^>]*>([^<]+)</p>', content_html[:2000])
    intro_text = ' '.join(first_paras[:3]) if first_paras else text[:500]

    return {
        'title': strip_html(title),
        'headings': headings,
        'intro': intro_text,
        'full_text': text,
        'word_count': len(text.split())
    }

def is_product_review(title):
    """Determine if the post is a product review/listicle."""
    title_lower = title.lower()
    product_keywords = ['best ', 'top ', 'review', 'compared', 'vs ', 'versus', 'picks', 'rated', 'recommended']
    return any(kw in title_lower for kw in product_keywords)

def generate_conclusion(info):
    """Generate a factual 2-3 sentence conclusion based on the article content."""
    title = info['title']
    headings = info['headings']
    intro = info['intro']
    full_text = info['full_text']

    # Clean title for use in conclusion
    title_clean = re.sub(r'^\d+\s+', '', title)

    if is_product_review(title):
        # Product review / "Best X" post
        subject_match = re.search(r'(?:Best|Top)\s+(?:\d+\s+)?(.+?)(?:\s+(?:for|in|of|on|to)\s+(.+))?$', title, re.IGNORECASE)
        if subject_match:
            product_type = subject_match.group(1).strip()
            context = subject_match.group(2) if subject_match.group(2) else ""

            if context:
                conclusion = (
                    f"Choosing the right {product_type.lower()} for {context.lower()} depends on your pet's specific needs, preferences, and your budget. "
                    f"Each option reviewed above offers unique advantages, from durability and comfort to specialized features that cater to different situations. "
                    f"Consider your pet's size, habits, and any special requirements when making your final selection."
                )
            else:
                conclusion = (
                    f"Selecting the ideal {product_type.lower()} comes down to understanding your pet's individual needs and your specific situation. "
                    f"The options covered in this guide range from budget-friendly choices to premium selections, each with distinct benefits. "
                    f"Take into account factors like your pet's size, activity level, and any particular preferences when deciding."
                )
        else:
            conclusion = (
                f"The products and options discussed in this guide each bring different strengths to the table. "
                f"Your best choice will depend on your pet's unique needs, your lifestyle, and your budget. "
                f"Consider the key features highlighted above to find the perfect match for your situation."
            )
    else:
        # Educational / guide post
        topic = title_clean

        if re.search(r'how to|guide|tips|ways to|steps', topic, re.IGNORECASE):
            topic_core = re.sub(r'^(how to|a guide to|guide to|tips for|tips on|ways to)\s+', '', topic, flags=re.IGNORECASE).strip()
            conclusion = (
                f"Understanding {topic_core.lower()} is essential for responsible pet ownership. "
                f"By following the guidance outlined above and paying attention to your pet's individual responses, you can ensure their health and happiness. "
                f"When in doubt, always consult with your veterinarian for personalized advice."
            )
        elif re.search(r'^(can |do |is |are |should |will |does |why |what |when |where )', topic, re.IGNORECASE):
            # Question-style posts
            conclusion = (
                f"We hope this article has thoroughly addressed your question about whether {topic.lower().rstrip('?')}. "
                f"Every pet is unique, so always observe your own animal's behavior and health when applying general advice. "
                f"For specific concerns, a consultation with your veterinarian is always recommended."
            )
        elif re.search(r'food|diet|eat|nutrition|feed', topic, re.IGNORECASE):
            conclusion = (
                f"Making informed dietary choices is one of the most impactful things you can do for your pet's long-term health. "
                f"The nutritional information covered in this article should help guide your decisions, but individual needs vary. "
                f"Always introduce new foods gradually and consult your veterinarian if you have concerns about your pet's diet."
            )
        elif re.search(r'health|disease|sick|symptom|treatment|vet', topic, re.IGNORECASE):
            conclusion = (
                f"Being informed about {topic.lower()} helps you recognize important signs and take timely action for your pet's wellbeing. "
                f"Early detection and proper care can make a significant difference in outcomes. "
                f"Always seek professional veterinary guidance for diagnosis and treatment of any health concerns."
            )
        elif re.search(r'train|behavior|bark|bite|aggress', topic, re.IGNORECASE):
            conclusion = (
                f"Understanding {topic.lower()} requires patience, consistency, and a willingness to see things from your pet's perspective. "
                f"The approaches discussed above can help you build a stronger bond with your pet while addressing behavioral challenges. "
                f"If issues persist, consider working with a certified animal behaviorist for personalized guidance."
            )
        elif re.search(r'breed|puppy|kitten|adopt', topic, re.IGNORECASE):
            conclusion = (
                f"Learning about {topic.lower()} helps you make well-informed decisions and provide the best possible care. "
                f"Every animal is an individual with its own personality and needs beyond breed generalizations. "
                f"Take the time to understand your specific pet and provide them with appropriate care, socialization, and love."
            )
        else:
            conclusion = (
                f"Being well-informed about {topic.lower()} helps you make better decisions for your pet's overall wellbeing. "
                f"The key points covered in this article provide a solid foundation for understanding this topic. "
                f"Remember that each pet is an individual, and professional veterinary guidance should always be sought for specific health concerns."
            )

    return conclusion

def insert_conclusion(content, conclusion_text, is_review):
    """Insert conclusion section into the post content."""
    heading_type = "Final Verdict" if is_review else "Conclusion"

    conclusion_block = (
        f'\n\n<h2 class="wp-block-heading">{heading_type}</h2>\n'
        f'<p class="wp-block-paragraph">{conclusion_text}</p>\n\n'
    )

    # Check for Sources/References section
    sources_match = SOURCES_REGEX.search(content)
    if sources_match:
        # Insert before the Sources/References heading
        insert_pos = sources_match.start()
        new_content = content[:insert_pos].rstrip() + conclusion_block + content[insert_pos:]
    else:
        # Insert at the end
        new_content = content.rstrip() + conclusion_block

    return new_content

def log(msg, log_lines):
    """Log a message."""
    print(msg)
    log_lines.append(msg)

def main():
    log_lines = []
    log(f"=== PetHub Online Conclusion Addition - {time.strftime('%Y-%m-%d %H:%M:%S')} ===", log_lines)
    log("", log_lines)

    # Step 1: Fetch all posts
    log("Fetching all published posts...", log_lines)
    posts = fetch_all_posts()
    log(f"Total published posts fetched: {len(posts)}", log_lines)
    log("", log_lines)

    # Step 2: Filter posts missing conclusions
    posts_needing_conclusion = []
    posts_with_conclusion = []

    for post in posts:
        content = post['content']['rendered']
        title = post['title']['rendered']

        if CONCLUSION_REGEX.search(content):
            posts_with_conclusion.append(post)
        else:
            posts_needing_conclusion.append(post)

    log(f"Posts already with conclusion/verdict: {len(posts_with_conclusion)}", log_lines)
    log(f"Posts needing conclusion: {len(posts_needing_conclusion)}", log_lines)
    log("", log_lines)

    # Step 3: Process posts in batches of 10
    updated_count = 0
    failed_count = 0
    batch_size = 10

    for i in range(0, len(posts_needing_conclusion), batch_size):
        batch = posts_needing_conclusion[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        log(f"--- Batch {batch_num} (posts {i+1}-{i+len(batch)}) ---", log_lines)

        for post in batch:
            post_id = post['id']
            title = post['title']['rendered']
            content = post['content']['rendered']

            # Determine post type
            title_text = strip_html(title)
            review = is_product_review(title_text)
            post_type = "Product Review" if review else "Educational/Guide"

            # Extract info and generate conclusion
            info = extract_key_points(content, title)
            conclusion_text = generate_conclusion(info)

            # Insert conclusion
            new_content = insert_conclusion(content, conclusion_text, review)

            # Wait before updating
            time.sleep(5)

            # Update post
            update_data = {"content": new_content}
            result = curl_post_update(post_id, update_data)

            if 'id' in result:
                heading_type = "Final Verdict" if review else "Conclusion"
                log(f"  [OK] Post {post_id}: \"{title_text[:60]}\" - Added {heading_type} ({post_type})", log_lines)
                updated_count += 1
            else:
                error_msg = result.get('message', result.get('error', 'Unknown error'))
                log(f"  [FAIL] Post {post_id}: \"{title_text[:60]}\" - Error: {error_msg}", log_lines)
                failed_count += 1

        log("", log_lines)

    # Summary
    log("=== SUMMARY ===", log_lines)
    log(f"Total posts processed: {len(posts_needing_conclusion)}", log_lines)
    log(f"Successfully updated: {updated_count}", log_lines)
    log(f"Failed: {failed_count}", log_lines)
    log(f"Already had conclusion: {len(posts_with_conclusion)}", log_lines)
    log(f"Completion time: {time.strftime('%Y-%m-%d %H:%M:%S')}", log_lines)

    # Write log file
    with open(LOG_FILE, 'w') as f:
        f.write('\n'.join(log_lines))

    print(f"\nLog saved to {LOG_FILE}")

if __name__ == '__main__':
    main()
