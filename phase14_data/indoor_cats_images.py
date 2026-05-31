#!/usr/bin/env python3
"""
Add Pexels images to 12 Indoor Cats draft posts on PetHub Online WordPress.
Uses curl subprocess for ALL HTTP requests.
"""

import json
import subprocess
import time
import re
import html
from datetime import datetime

# Configuration
WP_API = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
PEXELS_KEY = "dmGyKrZqTlwukxWzOK1EkH4jbEv9EaIDpLGj7eL5MZ07bl6AR9OEoHlB"

DRAFT_IDS = [14199, 14212, 14209, 14216, 14194, 14204, 14201, 14190, 12756, 12757, 12758, 12816]

LOG_FILE = "/var/lib/freelancer/projects/40416335/phase14_data/Indoor_Cats_Images_Log.txt"

log_lines = []

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    log_lines.append(line)

def curl_get(url, headers=None):
    """GET request via curl subprocess."""
    cmd = ["curl", "-s", "-S", "--max-time", "30"]
    if headers:
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise Exception(f"curl GET failed: {result.stderr}")
    return json.loads(result.stdout)

def curl_post_json(url, data, user, password):
    """POST JSON to WordPress via curl subprocess with basic auth."""
    json_str = json.dumps(data)
    cmd = [
        "curl", "-s", "-S", "--max-time", "60",
        "-X", "POST",
        "-u", f"{user}:{password}",
        "-H", "Content-Type: application/json",
        "-d", json_str,
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise Exception(f"curl POST failed: {result.stderr}")
    return json.loads(result.stdout)

def fetch_post(post_id):
    """Fetch a WordPress post by ID."""
    url = f"{WP_API}/posts/{post_id}?context=edit"
    cmd = [
        "curl", "-s", "-S", "--max-time", "30",
        "-u", f"{WP_USER}:{WP_PASS}",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise Exception(f"curl GET post failed: {result.stderr}")
    return json.loads(result.stdout)

def search_pexels(query):
    """Search Pexels for landscape images."""
    import urllib.parse
    encoded = urllib.parse.quote(query)
    url = f"https://api.pexels.com/v1/search?query={encoded}&per_page=6&orientation=landscape"
    headers = {"Authorization": PEXELS_KEY}
    return curl_get(url, headers)

def generate_search_query(title, slug):
    """Generate a relevant Pexels search query based on post title/slug."""
    title_lower = title.lower()
    slug_lower = slug.lower()

    query_map = {
        "exercise": "indoor cat exercise playing",
        "play": "cat playing with toy indoors",
        "toy": "cat toys playing indoors",
        "climb": "cat climbing shelves indoor",
        "scratch": "cat scratching post indoor",
        "enrich": "indoor cat enrichment activities",
        "bored": "bored cat indoor activities",
        "safe": "cat safe home indoor",
        "health": "healthy indoor cat veterinarian",
        "weight": "cat weight exercise indoor",
        "obes": "overweight cat indoor exercise",
        "mental": "cat mental stimulation indoor",
        "stimul": "cat puzzle toy stimulation",
        "window": "cat looking out window perch",
        "perch": "cat window perch indoor",
        "catio": "catio outdoor cat enclosure",
        "outdoor": "catio outdoor cat enclosure",
        "enclosure": "cat outdoor enclosure catio",
        "garden": "cat garden outdoor safe",
        "balcony": "cat balcony safe enclosure",
        "food": "cat food bowl indoor feeding",
        "diet": "cat healthy diet food",
        "feed": "cat feeding indoor",
        "nutrition": "cat nutrition healthy food",
        "groom": "cat grooming brushing indoor",
        "fur": "cat grooming fur care",
        "litter": "cat litter box clean",
        "train": "cat training indoor tricks",
        "behav": "cat behavior indoor calm",
        "stress": "cat relaxing calm indoor",
        "anxi": "cat anxiety comfort indoor",
        "sleep": "cat sleeping cozy indoor",
        "bed": "cat sleeping bed cozy",
        "kitten": "kitten playing indoor cute",
        "senior": "senior old cat resting indoor",
        "multi": "multiple cats indoor together",
        "companion": "two cats cuddling indoor",
        "breed": "indoor cat breed domestic",
        "apartment": "cat apartment small space indoor",
        "space": "cat small space apartment living",
        "plant": "cat safe plants indoor",
        "danger": "cat safety home indoor",
        "toxic": "cat safe home environment",
        "entertainment": "cat entertainment indoor fun",
        "happy": "happy cat indoor content",
        "transition": "cat indoor outdoor transition",
        "comfort": "comfortable cat indoor home",
    }

    for keyword, query in query_map.items():
        if keyword in title_lower or keyword in slug_lower:
            return query

    # Fallback
    stop_words = {"the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with", "your", "how", "why", "what", "best", "top", "guide", "tips", "indoor", "cats", "cat"}
    words = re.findall(r'[a-z]+', title_lower)
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    if keywords:
        return f"indoor cat {' '.join(keywords[:3])}"
    return "indoor cat cozy home"

def generate_alt_texts(title, num=4):
    """Generate descriptive alt texts based on post topic."""
    title_lower = title.lower()

    if any(w in title_lower for w in ["exercise", "play", "activ"]):
        alts = [
            "Cat actively playing with a feather toy indoors",
            "Indoor cat exercising by jumping and stretching",
            "Playful cat chasing a toy across the living room floor",
            "Cat engaged in interactive play session at home",
        ]
    elif any(w in title_lower for w in ["climb", "shelf", "vertical", "tree"]):
        alts = [
            "Cat perched on a tall climbing tree near a window",
            "Indoor cat exploring vertical shelving spaces",
            "Cat resting on an elevated shelf watching the room below",
            "Feline climbing a multi-level cat tree indoors",
        ]
    elif any(w in title_lower for w in ["scratch", "furniture", "protect"]):
        alts = [
            "Cat using a sisal scratching post indoors",
            "Indoor cat stretching and scratching on a dedicated post",
            "Cat scratching a textured surface to maintain claws",
            "Well-designed scratching station for indoor cats",
        ]
    elif any(w in title_lower for w in ["catio", "outdoor", "enclosure", "outside"]):
        alts = [
            "Cat enjoying fresh air in a screened outdoor catio",
            "Secure outdoor cat enclosure attached to a home window",
            "Cat relaxing in a sunlit catio enclosure with plants",
            "Safe outdoor space designed for indoor cats to explore",
        ]
    elif any(w in title_lower for w in ["health", "vet", "wellness", "check"]):
        alts = [
            "Healthy indoor cat resting peacefully on a soft surface",
            "Cat at a wellness checkup at the veterinary clinic",
            "Well-cared-for indoor cat with bright eyes and glossy coat",
            "Cat being gently examined during a health assessment",
        ]
    elif any(w in title_lower for w in ["food", "diet", "nutrition", "feed", "weight", "obes"]):
        alts = [
            "Indoor cat eating from a portion-controlled food bowl",
            "Cat enjoying a healthy meal at its feeding station",
            "Well-nourished indoor cat with a balanced diet",
            "Cat food bowl with nutritious meal for indoor cats",
        ]
    elif any(w in title_lower for w in ["window", "perch", "view", "watch"]):
        alts = [
            "Cat gazing out a window from a comfortable perch",
            "Indoor cat watching birds from a window-mounted bed",
            "Cat relaxing on a sunny window perch indoors",
            "Feline enjoying the outdoor view from an indoor window seat",
        ]
    elif any(w in title_lower for w in ["sleep", "rest", "bed", "cozy", "comfort"]):
        alts = [
            "Cat sleeping peacefully in a cozy indoor bed",
            "Indoor cat curled up in a warm blanket",
            "Relaxed cat napping in a comfortable resting spot",
            "Peaceful sleeping cat in a soft indoor hideaway",
        ]
    elif any(w in title_lower for w in ["toy", "puzzle", "enrich", "mental", "stimul", "bored", "entertainment"]):
        alts = [
            "Cat investigating an interactive puzzle toy indoors",
            "Indoor cat mentally stimulated by a treat-dispensing game",
            "Curious cat engaged with enrichment toys at home",
            "Cat focused on solving a puzzle feeder for treats",
        ]
    elif any(w in title_lower for w in ["train", "trick", "learn"]):
        alts = [
            "Indoor cat learning a new trick during training",
            "Cat focused on a clicker training session at home",
            "Owner training an indoor cat with positive reinforcement",
            "Attentive cat responding to training cues indoors",
        ]
    elif any(w in title_lower for w in ["stress", "anxi", "calm", "relax"]):
        alts = [
            "Calm indoor cat relaxing in a quiet corner",
            "Relaxed cat resting in a stress-free home environment",
            "Content cat feeling safe in its indoor surroundings",
            "Peaceful indoor cat in a serene home setting",
        ]
    elif any(w in title_lower for w in ["groom", "fur", "brush", "coat"]):
        alts = [
            "Cat being gently groomed with a soft brush",
            "Indoor cat with well-maintained grooming routine",
            "Owner brushing a cat's coat for healthy fur care",
            "Cat enjoying a grooming session at home",
        ]
    elif any(w in title_lower for w in ["litter", "bathroom", "box"]):
        alts = [
            "Clean litter box setup for an indoor cat",
            "Cat approaching a well-maintained litter area",
            "Modern litter box station for indoor cat hygiene",
            "Indoor cat with access to a clean litter arrangement",
        ]
    elif any(w in title_lower for w in ["safe", "danger", "toxic", "plant", "hazard"]):
        alts = [
            "Indoor cat in a safe and cat-proofed home environment",
            "Cat-safe living room with no hazards visible",
            "Indoor cat exploring a pet-safe room carefully",
            "Well-protected indoor space designed for cat safety",
        ]
    elif any(w in title_lower for w in ["kitten", "young", "baby"]):
        alts = [
            "Adorable kitten exploring a safe indoor space",
            "Young kitten playing with a small toy indoors",
            "Curious kitten investigating its indoor environment",
            "Playful kitten enjoying its first indoor adventures",
        ]
    elif any(w in title_lower for w in ["senior", "old", "elder", "aging"]):
        alts = [
            "Senior cat resting comfortably in a warm indoor spot",
            "Older cat relaxing on a soft cushion at home",
            "Aging cat enjoying peaceful indoor retirement",
            "Senior feline in a comfortable and accessible home space",
        ]
    elif any(w in title_lower for w in ["multi", "two", "companion", "friend"]):
        alts = [
            "Two indoor cats snuggling together on a couch",
            "Multiple cats sharing a cozy indoor space peacefully",
            "Companion cats grooming each other at home",
            "Two feline friends resting side by side indoors",
        ]
    elif any(w in title_lower for w in ["breed", "type", "best"]):
        alts = [
            "Beautiful domestic cat relaxing in an indoor setting",
            "Indoor cat breed lounging on a comfortable surface",
            "Purebred cat enjoying the indoor lifestyle",
            "Elegant cat resting in a well-furnished indoor space",
        ]
    elif any(w in title_lower for w in ["apartment", "small", "space", "studio"]):
        alts = [
            "Cat comfortably living in a small apartment space",
            "Indoor cat making the most of a compact living area",
            "Cat exploring vertical spaces in a small apartment",
            "Cozy apartment setup optimized for an indoor cat",
        ]
    elif any(w in title_lower for w in ["transition", "convert", "indoor-only", "keep"]):
        alts = [
            "Cat adjusting to a new indoor-only lifestyle",
            "Indoor cat contentedly resting near a window",
            "Cat transitioning to indoor living with enrichment",
            "Happy cat adapting to its indoor home environment",
        ]
    else:
        alts = [
            "Indoor cat in a cozy home environment",
            "Cat relaxing comfortably in an indoor setting",
            "Domestic cat enjoying the indoor lifestyle at home",
            "Content indoor cat resting in a well-furnished room",
        ]

    return alts[:num]

def build_image_block(img_url, alt_text, photographer):
    """Build a WordPress Gutenberg image block."""
    return (
        f'\n\n<figure class="wp-block-image size-large">'
        f'<img src="{img_url}" alt="{alt_text}" />'
        f'<figcaption>Photo by {photographer} on Pexels</figcaption>'
        f'</figure>\n\n'
    )

def find_insertion_points(content):
    """Find good insertion points in the content (after every 3-4 paragraphs)."""
    # Find all positions of paragraph/block endings
    pattern = r'(</p>|</ul>|</ol>|</h[2-6]>|</blockquote>)'

    endings = []
    for match in re.finditer(pattern, content):
        endings.append(match.end())

    if not endings:
        # Fallback: split by double newlines
        parts = content.split('\n\n')
        positions = []
        pos = 0
        for part in parts:
            pos += len(part) + 2
            positions.append(pos - 2)
        endings = positions

    # Select insertion points at roughly even intervals
    # We want 4 images, so we need 4 insertion points
    total = len(endings)
    if total < 4:
        return endings

    # Distribute evenly: 5 segments, 4 insertion points
    step = total / 5
    points = []
    for i in range(1, 5):
        idx = min(int(i * step), total - 1)
        points.append(endings[idx])

    return points

def insert_images_into_content(content, image_blocks):
    """Insert image blocks at even intervals throughout the content."""
    points = find_insertion_points(content)

    if not points or not image_blocks:
        return content + "\n\n".join(image_blocks)

    num_inserts = min(len(points), len(image_blocks))

    # Insert from end to start to preserve positions
    result = content
    for i in range(num_inserts - 1, -1, -1):
        pos = points[i]
        result = result[:pos] + image_blocks[i] + result[pos:]

    return result

def process_post(post_id):
    """Process a single post: fetch, search Pexels, insert images, update."""
    log(f"--- Processing post ID {post_id} ---")

    # Fetch post
    post = fetch_post(post_id)

    if "id" not in post:
        log(f"  ERROR: Could not fetch post {post_id}: {json.dumps(post)[:200]}")
        return False

    title = post["title"]["raw"] if "raw" in post.get("title", {}) else post["title"].get("rendered", "Unknown")
    title = html.unescape(title)
    slug = post.get("slug", "")
    content = post["content"]["raw"] if "raw" in post.get("content", {}) else post["content"].get("rendered", "")

    log(f"  Title: {title}")
    log(f"  Slug: {slug}")
    log(f"  Content length: {len(content)} chars")

    # Check if images already exist
    if 'wp-block-image' in content and 'pexels' in content.lower():
        log(f"  SKIP: Post already has Pexels images")
        return True

    # Generate search query
    query = generate_search_query(title, slug)
    log(f"  Pexels query: {query}")

    # Search Pexels
    time.sleep(1)
    try:
        pexels_data = search_pexels(query)
    except Exception as e:
        log(f"  ERROR searching Pexels: {e}")
        return False

    photos = pexels_data.get("photos", [])
    if len(photos) < 4:
        log(f"  Only {len(photos)} results, trying broader query...")
        time.sleep(1)
        try:
            pexels_data = search_pexels("indoor cat")
            photos = pexels_data.get("photos", [])
        except Exception as e:
            log(f"  ERROR on fallback Pexels search: {e}")
            return False

    if len(photos) < 4:
        log(f"  ERROR: Only {len(photos)} Pexels results even with fallback")
        return False

    # Select 4 images
    selected = photos[:4]
    alt_texts = generate_alt_texts(title, 4)

    image_blocks = []
    for i, photo in enumerate(selected):
        img_url = photo["src"]["medium"]
        photographer = photo["photographer"]
        alt = alt_texts[i]
        block = build_image_block(img_url, alt, photographer)
        image_blocks.append(block)
        log(f"  Image {i+1}: {photographer} - {img_url[:80]}...")

    # Insert images into content
    updated_content = insert_images_into_content(content, image_blocks)
    log(f"  Updated content length: {len(updated_content)} chars (was {len(content)})")

    # Update the post
    time.sleep(5)
    try:
        update_data = {"content": updated_content}
        result = curl_post_json(f"{WP_API}/posts/{post_id}", update_data, WP_USER, WP_PASS)

        if "id" in result:
            log(f"  SUCCESS: Post {post_id} updated")
            return True
        else:
            error_msg = result.get("message", json.dumps(result)[:200])
            log(f"  ERROR updating post: {error_msg}")
            return False
    except Exception as e:
        log(f"  ERROR updating post: {e}")
        return False

def main():
    log("=" * 60)
    log("Indoor Cats Image Insertion - PetHub Online")
    log(f"Processing {len(DRAFT_IDS)} draft posts")
    log("=" * 60)

    success = 0
    failed = 0

    for post_id in DRAFT_IDS:
        try:
            if process_post(post_id):
                success += 1
            else:
                failed += 1
        except Exception as e:
            log(f"  EXCEPTION processing post {post_id}: {e}")
            failed += 1

    log("=" * 60)
    log(f"COMPLETE: {success} succeeded, {failed} failed out of {len(DRAFT_IDS)}")
    log("=" * 60)

    # Write log file
    with open(LOG_FILE, "w") as f:
        f.write("\n".join(log_lines) + "\n")
    print(f"\nLog saved to {LOG_FILE}")

if __name__ == "__main__":
    main()
