#!/usr/bin/env python3
"""
Phase 24C - H2 Question Format Conversion for PetHub Online
Converts non-question H2 headings to question format for featured snippet readiness.
Google featured snippets strongly prefer H2 headings phrased as questions.
Supports resume from partial runs via results JSON.
"""

import requests
import json
import time
import re
import os
import sys
import html
from datetime import datetime
from requests.auth import HTTPBasicAuth

# ── Config ──────────────────────────────────────────────────────────────
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = HTTPBasicAuth("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
HEADERS = {
    "Accept-Encoding": "gzip, deflate",
    "Content-Type": "application/json",
}
FETCH_HEADERS = {"Accept-Encoding": "gzip, deflate"}
RESULTS_PATH = "/var/lib/freelancer/projects/40416335/phase24c_h2_question_results.json"
DELAY = 2        # seconds between API calls
RETRY_WAIT = 10  # seconds on 429

# H2s to skip (exact or partial match, case-insensitive)
SKIP_H2S = [
    "frequently asked questions",
    "faqs",
    "faq",
    "table of contents",
    "conclusion",
    "final thoughts",
    "related posts",
    "explore more",
    "sources",
    "references",
    "about the author",
    "disclaimer",
    "share this",
    "leave a comment",
    "comments",
    "summary",
    "in summary",
    "wrapping up",
    "the bottom line",
    "bottom line",
]

# Words that signal singular (use "What Is" instead of "What Are")
SINGULAR_SIGNALS = [
    "cost", "price", "importance", "purpose", "role", "impact",
    "history", "difference", "best way", "best time", "right way",
    "right time", "ideal", "average", "process", "method",
    "lifespan", "temperament", "behavior", "behaviour", "diet",
    "schedule", "routine", "environment", "habitat",
]

# Words that signal plural (use "What Are")
PLURAL_SIGNALS = [
    "tips", "benefits", "signs", "symptoms", "types", "breeds",
    "ways", "steps", "reasons", "causes", "effects", "risks",
    "advantages", "disadvantages", "features", "options", "factors",
    "ingredients", "nutrients", "vitamins", "toys", "tools",
    "products", "foods", "treats", "exercises", "activities",
    "commands", "tricks", "habits", "mistakes", "myths",
    "characteristics", "requirements", "needs", "supplies",
    "accessories", "essentials", "basics", "facts", "questions",
]


def api_call(method, url, retries=3, **kwargs):
    """Make an API call with retry on 429 and connection errors."""
    for attempt in range(retries):
        try:
            resp = method(url, timeout=30, **kwargs)
            if resp.status_code == 429:
                print(f"    [429] Rate limited, waiting {RETRY_WAIT}s...", flush=True)
                time.sleep(RETRY_WAIT)
                continue
            return resp
        except requests.exceptions.RequestException as e:
            print(f"    [ERROR] Request failed (attempt {attempt+1}/{retries}): {e}", flush=True)
            if attempt < retries - 1:
                time.sleep(5)
    return None


def fetch_all_posts():
    """Fetch all published posts with pagination."""
    all_posts = []
    page = 1
    while True:
        print(f"  Fetching posts page {page}...", flush=True)
        resp = api_call(
            requests.get,
            f"{WP_BASE}/posts",
            params={
                "per_page": 100,
                "page": page,
                "status": "publish",
                "context": "edit",
                "_fields": "id,title,content",
            },
            headers=FETCH_HEADERS,
            auth=AUTH,
        )
        if resp is None or resp.status_code != 200:
            print(f"    Failed to fetch page {page}: {resp.status_code if resp else 'no response'}", flush=True)
            break
        posts = resp.json()
        if not posts:
            break
        all_posts.extend(posts)
        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        print(f"    Got {len(posts)} posts (page {page}/{total_pages})", flush=True)
        if page >= total_pages:
            break
        page += 1
        time.sleep(DELAY)
    return all_posts


def clean_text(text):
    """Strip HTML tags and decode entities from heading text."""
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    return text.strip()


def should_skip_h2(heading_text):
    """Check if this H2 should be skipped."""
    lower = heading_text.lower().strip()
    # Already a question
    if '?' in heading_text:
        return True
    # In the skip list
    for skip in SKIP_H2S:
        if skip in lower:
            return True
    # Very short headings (1-2 chars) or just numbers
    if len(lower) < 3 or lower.replace(' ', '').isdigit():
        return True
    return False


def is_singular(text):
    """Determine if the heading topic is singular or plural."""
    lower = text.lower()
    # Check explicit plural signals
    for word in PLURAL_SIGNALS:
        if word in lower:
            return False
    # Check explicit singular signals
    for word in SINGULAR_SIGNALS:
        if word in lower:
            return True
    # Check if the last significant word ends in 's' (likely plural)
    words = lower.split()
    if words:
        last_word = words[-1].rstrip('.,!;:')
        if last_word.endswith('s') and not last_word.endswith('ss') and not last_word.endswith('ness'):
            return False
    return True


def is_gerund_phrase(text):
    """Check if heading starts with a gerund (-ing verb) that makes sense as a verb."""
    words = text.strip().split()
    if not words:
        return False
    first = words[0]
    first_lower = first.lower()

    # Must end in 'ing' and be at least 5 chars (avoids "King", "Ring", "Sing" etc.)
    if not first_lower.endswith('ing') or len(first_lower) < 5:
        return False

    # Exclude words that end in 'ing' but are NOT gerunds
    not_gerunds = {
        "spring", "string", "king", "ring", "wing", "thing", "nothing",
        "something", "everything", "anything", "morning", "evening",
        "during", "ceiling", "feeling", "darling", "sterling", "pudding",
        "bedding", "wedding", "building", "sibling", "offspring",
        "according", "amazing", "interesting", "existing", "underlying",
        "incoming", "outgoing", "ongoing", "pending", "ending",
    }
    if first_lower in not_gerunds:
        return False

    return True


def is_how_to_phrase(text):
    """Check if heading is a 'how to' phrase."""
    lower = text.lower().strip()
    return lower.startswith("how to ")


def is_when_phrase(text):
    """Check if heading is about timing."""
    lower = text.lower().strip()
    timing_words = ["when to", "the right time", "best time", "ideal time"]
    return any(lower.startswith(tw) for tw in timing_words)


def gerund_to_base(gerund):
    """Convert a gerund (e.g., 'Feeding') to its base verb ('Feed')."""
    word = gerund.strip()
    lower = word.lower()

    # Explicit special cases dictionary
    specials = {
        "choosing": "Choose", "making": "Make", "having": "Have",
        "giving": "Give", "coming": "Come", "taking": "Take",
        "living": "Live", "moving": "Move", "using": "Use",
        "losing": "Lose", "coping": "Cope", "caring": "Care",
        "raising": "Raise", "saving": "Save", "preparing": "Prepare",
        "creating": "Create", "providing": "Provide",
        "introducing": "Introduce", "recognizing": "Recognize",
        "recognising": "Recognise", "reducing": "Reduce",
        "improving": "Improve", "ensuring": "Ensure",
        "managing": "Manage", "exploring": "Explore",
        "discovering": "Discover", "organizing": "Organize",
        "organising": "Organise", "maximizing": "Maximize",
        "maximising": "Maximise", "minimizing": "Minimize",
        "minimising": "Minimise", "increasing": "Increase",
        "socializing": "Socialize", "socialising": "Socialise",
        "exercising": "Exercise", "travelling": "Travel",
        "traveling": "Travel", "evaluating": "Evaluate",
        "adjusting": "Adjust", "establishing": "Establish",
        "developing": "Develop", "planning": "Plan",
        "beginning": "Begin", "getting": "Get", "setting": "Set",
        "picking": "Pick", "running": "Run", "swimming": "Swim",
        "sitting": "Sit", "stopping": "Stop", "trimming": "Trim",
        "clipping": "Clip", "wrapping": "Wrap", "shopping": "Shop",
        "dropping": "Drop", "bathing": "Bathe", "breathing": "Breathe",
        "clothing": "Clothe", "soothing": "Soothe",
        "changing": "Change", "chasing": "Chase",
        "comparing": "Compare", "competing": "Compete",
        "guiding": "Guide", "housing": "House",
        "purchasing": "Purchase", "practising": "Practise",
        "practicing": "Practice", "advising": "Advise",
        "noticing": "Notice", "dancing": "Dance",
        "balancing": "Balance", "slicing": "Slice",
        "storing": "Store", "securing": "Secure",
        "sharing": "Share", "dining": "Dine",
        "preventing": "Prevent", "treating": "Treat",
        "selecting": "Select", "finding": "Find", "buying": "Buy",
        "adopting": "Adopt", "breeding": "Breed",
        "monitoring": "Monitor", "handling": "Handle",
        "building": "Build", "maintaining": "Maintain",
        "keeping": "Keep", "protecting": "Protect",
        "identifying": "Identify", "dealing": "Deal",
        "transitioning": "Transition", "switching": "Switch",
        "teaching": "Teach", "learning": "Learn",
        "starting": "Start", "avoiding": "Avoid",
        "walking": "Walk", "feeding": "Feed", "training": "Train",
        "grooming": "Groom", "cleaning": "Clean",
        "understanding": "Understand", "drying": "Dry",
    }
    if lower in specials:
        return specials[lower]

    if not lower.endswith("ing"):
        return word.capitalize()

    stem = lower[:-3]  # Remove 'ing'

    # "ying" -> "y" (e.g., "identifying" already in specials but fallback)
    if lower.endswith("ying") and len(stem) >= 2:
        return (stem + "y").capitalize()

    # Double consonant at end: "running" -> "runn" -> "run"
    if len(stem) >= 3 and stem[-1] == stem[-2] and stem[-1] not in 'aeiou':
        return stem[:-1].capitalize()

    # Try adding 'e' back for common patterns (CVC+ing where C dropped e)
    # e.g., "scor" + "e" = "score", "shar" + "e" = "share"
    if len(stem) >= 3 and stem[-1] not in 'aeiou' and stem[-2] in 'aeiou':
        # Likely dropped an 'e': return stem + 'e'
        return (stem + "e").capitalize()

    # Default: just return stem capitalized
    return stem.capitalize()


def convert_h2_to_question(heading_text):
    """
    Convert a non-question H2 heading to question format.
    Returns (new_text, conversion_type) or (None, None) if no conversion.
    """
    text = heading_text.strip()
    lower = text.lower()

    # Already starts with a question word - just add ?
    q_starts = ["what ", "how ", "why ", "when ", "where ", "which ", "who ",
                 "can ", "should ", "do ", "does ", "is ", "are "]
    for qs in q_starts:
        if lower.startswith(qs):
            return text.rstrip('.') + "?", "added_question_mark"

    # "How to X" -> "How Do You X?"
    if is_how_to_phrase(text):
        rest = text[7:]  # Remove "How to "
        if rest:
            return f"How Do You {rest.rstrip('.')}?", "how_to_conversion"

    # "When to X" -> "When Should You X?"
    if is_when_phrase(text):
        if lower.startswith("when to "):
            rest = text[8:]
            return f"When Should You {rest.rstrip('.')}?", "when_conversion"

    # "Reasons for/to X"
    if lower.startswith("reasons for "):
        rest = text[12:]
        return f"What Are the Reasons for {rest.rstrip('.')}?", "reasons_conversion"
    if lower.startswith("reasons to "):
        rest = text[11:]
        return f"What Are the Reasons to {rest.rstrip('.')}?", "reasons_conversion"

    # Gerund phrases: "Feeding Your Puppy" -> "How Should You Feed Your Puppy?"
    if is_gerund_phrase(text):
        words = text.split()
        gerund = words[0]
        rest = " ".join(words[1:])
        base_verb = gerund_to_base(gerund)

        if rest:
            return f"How Should You {base_verb} {rest.rstrip('.')}?", "gerund_conversion"
        else:
            return f"How Should You Handle {base_verb.rstrip('.')}?", "gerund_conversion"

    # "The X of Y" or "The X for Y" -> "What Is/Are the X of Y?"
    if lower.startswith("the "):
        rest = text[4:]
        if is_singular(rest):
            return f"What Is the {rest.rstrip('.')}?", "the_noun_conversion"
        else:
            return f"What Are the {rest.rstrip('.')}?", "the_noun_conversion"

    # General noun phrases
    if is_singular(text):
        return f"What Is the {text.rstrip('.')}?", "noun_phrase_singular"
    else:
        return f"What Are the {text.rstrip('.')}?", "noun_phrase_plural"


def process_content(content):
    """
    Find and convert H2 headings in post content.
    Returns (new_content, changes_list).
    """
    changes = []

    def replace_h2(match):
        full_match = match.group(0)
        inner_html = match.group(1)
        plain_text = clean_text(inner_html)

        if should_skip_h2(plain_text):
            return full_match

        new_text, conv_type = convert_h2_to_question(plain_text)

        if new_text is None or new_text == plain_text:
            return full_match

        # Replace text in the inner HTML while preserving tags
        if '<' in inner_html:
            new_inner = replace_text_in_html(inner_html, plain_text, new_text)
        else:
            new_inner = new_text

        new_full = full_match.replace(inner_html, new_inner)

        changes.append({
            "original": plain_text,
            "converted": new_text,
            "type": conv_type,
        })

        return new_full

    pattern = r'<h2[^>]*>(.*?)</h2>'
    new_content = re.sub(pattern, replace_h2, content, flags=re.DOTALL | re.IGNORECASE)

    return new_content, changes


def replace_text_in_html(inner_html, old_text, new_text):
    """Replace text content inside HTML while preserving tags."""
    simple_match = re.match(r'^(<[^>]+>)(.*?)(</[^>]+>)$', inner_html, re.DOTALL)
    if simple_match:
        tag_open, text_content, tag_close = simple_match.groups()
        clean_inner = clean_text(text_content)
        if clean_inner == old_text:
            return f"{tag_open}{new_text}{tag_close}"

    stripped = clean_text(inner_html)
    if stripped == old_text:
        return new_text

    return inner_html


def update_post(post_id, new_content):
    """Update a post's content via WordPress REST API."""
    resp = api_call(
        requests.post,
        f"{WP_BASE}/posts/{post_id}",
        headers=HEADERS,
        auth=AUTH,
        json={"content": new_content},
    )
    if resp and resp.status_code == 200:
        return True
    else:
        status = resp.status_code if resp else "no response"
        print(f"    [ERROR] Failed to update post {post_id}: {status}", flush=True)
        return False


def load_existing_results():
    """Load existing results to support resume."""
    if os.path.exists(RESULTS_PATH):
        try:
            with open(RESULTS_PATH, 'r') as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def save_results(results):
    """Save results to disk."""
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def main():
    print("=" * 70, flush=True)
    print("Phase 24C - H2 Question Format Conversion", flush=True)
    print(f"Started: {datetime.now().isoformat()}", flush=True)
    print("=" * 70, flush=True)

    # Check for existing results (resume support)
    existing = load_existing_results()
    already_done = set()
    if existing and "details" in existing:
        already_done = {d["post_id"] for d in existing["details"] if d.get("success")}
        if already_done:
            print(f"\n  Resuming: {len(already_done)} posts already updated in previous run.", flush=True)

    # Step 1: Fetch all posts
    print("\n[1/3] Fetching all published posts...", flush=True)
    posts = fetch_all_posts()
    print(f"  Total posts fetched: {len(posts)}", flush=True)

    if not posts:
        print("  No posts found. Exiting.", flush=True)
        return

    # Step 2: Process each post
    print(f"\n[2/3] Scanning H2 headings across {len(posts)} posts...", flush=True)
    posts_to_update = []
    total_h2s_found = 0
    total_h2s_converted = 0
    total_h2s_skipped = 0

    for i, post in enumerate(posts):
        post_id = post["id"]
        title = post.get("title", {})
        if isinstance(title, dict):
            title = title.get("raw", title.get("rendered", f"Post {post_id}"))
        title = clean_text(str(title))

        content = post.get("content", {})
        if isinstance(content, dict):
            content = content.get("raw", content.get("rendered", ""))
        content = str(content)

        h2_matches = re.findall(r'<h2[^>]*>(.*?)</h2>', content, re.DOTALL | re.IGNORECASE)
        total_h2s_found += len(h2_matches)

        if not h2_matches:
            continue

        # Skip if already updated in previous run
        if post_id in already_done:
            total_h2s_skipped += len(h2_matches)
            continue

        new_content, changes = process_content(content)

        if changes:
            posts_to_update.append({
                "id": post_id,
                "title": title,
                "new_content": new_content,
                "changes": changes,
            })
            total_h2s_converted += len(changes)
            total_h2s_skipped += len(h2_matches) - len(changes)
        else:
            total_h2s_skipped += len(h2_matches)

        if (i + 1) % 100 == 0:
            print(f"  Processed {i+1}/{len(posts)} posts... ({len(posts_to_update)} need updates)", flush=True)

    print(f"\n  Scan complete:", flush=True)
    print(f"    Total H2s found:      {total_h2s_found}", flush=True)
    print(f"    H2s to convert:       {total_h2s_converted}", flush=True)
    print(f"    H2s skipped:          {total_h2s_skipped}", flush=True)
    print(f"    Posts needing update:  {len(posts_to_update)}", flush=True)

    # Step 3: Update posts
    print(f"\n[3/3] Updating {len(posts_to_update)} posts via API...", flush=True)

    # Initialize results from existing or fresh
    if existing and "details" in existing:
        results = existing.copy()
        results["resumed_at"] = datetime.now().isoformat()
        results["total_posts_scanned"] = len(posts)
        results["total_h2s_found"] = total_h2s_found
    else:
        results = {
            "phase": "24C",
            "task": "H2 Question Format Conversion",
            "started": datetime.now().isoformat(),
            "total_posts_scanned": len(posts),
            "total_h2s_found": total_h2s_found,
            "total_h2s_converted": 0,
            "total_h2s_skipped": total_h2s_skipped,
            "posts_updated": 0,
            "posts_failed": 0,
            "details": [],
        }

    for i, item in enumerate(posts_to_update):
        post_id = item["id"]
        title = item["title"]
        changes = item["changes"]

        print(f"  [{i+1}/{len(posts_to_update)}] Updating post {post_id}: {title[:60]}...", flush=True)
        for c in changes:
            print(f"    H2: \"{c['original'][:50]}\" -> \"{c['converted'][:55]}\"", flush=True)

        success = update_post(post_id, item["new_content"])

        detail = {
            "post_id": post_id,
            "title": title,
            "changes": changes,
            "success": success,
        }
        results["details"].append(detail)

        if success:
            results["posts_updated"] = results.get("posts_updated", 0) + 1
            results["total_h2s_converted"] = results.get("total_h2s_converted", 0) + len(changes)
        else:
            results["posts_failed"] = results.get("posts_failed", 0) + 1

        # Save after every 20 posts for resume safety
        if (i + 1) % 20 == 0:
            save_results(results)

        time.sleep(DELAY)

    results["completed"] = datetime.now().isoformat()
    save_results(results)

    total_updated = results.get("posts_updated", 0)
    total_converted = results.get("total_h2s_converted", 0)
    total_failed = results.get("posts_failed", 0)

    print(f"\n{'=' * 70}", flush=True)
    print("Phase 24C COMPLETE", flush=True)
    print(f"  Posts scanned:    {results['total_posts_scanned']}", flush=True)
    print(f"  H2s found:        {results['total_h2s_found']}", flush=True)
    print(f"  H2s converted:    {total_converted}", flush=True)
    print(f"  Posts updated:     {total_updated}", flush=True)
    print(f"  Posts failed:      {total_failed}", flush=True)
    print(f"  Results saved:     {RESULTS_PATH}", flush=True)
    print(f"  Completed:         {datetime.now().isoformat()}", flush=True)
    print("=" * 70, flush=True)


if __name__ == "__main__":
    main()
