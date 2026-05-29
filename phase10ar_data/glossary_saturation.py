#!/usr/bin/env python3
"""
Phase 10AR – Glossary Saturation for Dog Toys + Uncategorized clusters.
Adds Key Terms and Common Mistakes blocks to posts on pethubonline.com.
"""

import subprocess, json, time, csv, os, re, tempfile, html
from datetime import datetime

# ── credentials ──────────────────────────────────────────────────────────
BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ar_data"
CSV_PATH = os.path.join(DATA_DIR, "glossary_dog_toys_uncat.csv")
DELAY = 2  # seconds between API calls

# ── Uncategorized IDs ────────────────────────────────────────────────────
UNCAT_IDS = [6048, 6044, 4786, 4785, 4573, 4570, 4576, 4574, 4571, 4328, 4293, 4223, 4153]

# ── API helpers ──────────────────────────────────────────────────────────
def api_get(url):
    """GET via curl subprocess."""
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"  [CURL ERROR] {result.stderr[:200]}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [JSON ERROR] {result.stdout[:300]}")
        return None


def api_post(url, payload):
    """POST JSON via curl subprocess using temp file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        tmp = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmp}",
             url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"  [CURL POST ERROR] {result.stderr[:200]}")
            return None
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"  [JSON POST ERROR] {result.stdout[:300]}")
            return None
    finally:
        os.unlink(tmp)


# ── Fetch Dog Toys posts ────────────────────────────────────────────────
def fetch_dog_toy_posts():
    """Search multiple keywords and deduplicate."""
    searches = [
        "dog+toy", "enrichment", "puzzle+toy", "chew+toy",
        "fetch+toy", "tug+toy", "dog+enrichment"
    ]
    seen = {}
    for term in searches:
        page = 1
        while True:
            url = f"{BASE}/posts?search={term}&per_page=50&status=publish&page={page}"
            print(f"  Searching '{term}' page {page} ...")
            data = api_get(url)
            if not data or not isinstance(data, list) or len(data) == 0:
                break
            for p in data:
                pid = p["id"]
                if pid not in seen:
                    seen[pid] = p
            if len(data) < 50:
                break
            page += 1
            time.sleep(DELAY)
        time.sleep(DELAY)
    print(f"  Dog Toys search: {len(seen)} unique posts found")
    return seen


def fetch_uncat_posts():
    """Fetch Uncategorized posts by ID."""
    posts = {}
    for pid in UNCAT_IDS:
        url = f"{BASE}/posts/{pid}"
        print(f"  Fetching Uncategorized post {pid} ...")
        data = api_get(url)
        if data and isinstance(data, dict) and "id" in data:
            posts[pid] = data
        else:
            print(f"  [WARN] Could not fetch post {pid}")
        time.sleep(DELAY)
    print(f"  Uncategorized: {len(posts)} posts fetched")
    return posts


# ── Content analysis ─────────────────────────────────────────────────────
def strip_html(text):
    """Rough HTML tag removal for keyword analysis."""
    return re.sub(r'<[^>]+>', ' ', text)


def get_topic_keywords(title, content_text):
    """Return lowercase keyword set from title + content."""
    combined = (title + " " + content_text).lower()
    return combined


def pick_glossary_terms(title, content_raw):
    """Choose 5-8 relevant Key Terms based on post topic."""
    text = strip_html(content_raw).lower()
    title_l = title.lower()

    # Master term bank – grouped by topic relevance
    term_bank = {
        # Enrichment / puzzle
        "cognitive enrichment": "Mental stimulation through problem-solving activities that engage a dog’s natural curiosity and intelligence.",
        "sensory play": "Activities that stimulate a dog’s senses – sight, smell, touch, taste, and hearing – to promote mental wellbeing.",
        "food puzzle": "A toy or device that requires a dog to manipulate it in order to access treats or kibble hidden inside.",
        "scent work": "Activities that harness a dog’s powerful sense of smell, encouraging them to locate hidden treats or objects.",
        "foraging behaviour": "The instinctive drive to search for and obtain food, which enrichment toys aim to replicate.",
        "mental stimulation": "Activities designed to keep a dog’s brain active, reducing boredom and associated behavioural issues.",
        "environmental enrichment": "Modifications to a dog’s living space or routine that encourage natural behaviours and reduce stress.",
        "snuffle mat": "A fabric mat with hiding spots woven into it, used to scatter kibble and encourage nose-driven foraging.",
        "lick mat": "A textured mat onto which soft food is spread, promoting slow licking that can calm anxious dogs.",
        "treat-dispensing toy": "A hollow or mechanical toy that releases treats as a dog interacts with it, rewarding persistence.",

        # Toy safety
        "choking hazard": "Any small component or fragment of a toy that could become lodged in a dog’s airway if swallowed.",
        "squeaker": "A small air-filled plastic device inside a toy that produces sound when compressed; a common choking risk if exposed.",
        "stuffing-free": "Toys manufactured without internal polyester filling, reducing the risk of ingestion if the outer fabric tears.",
        "rubber durometer": "A measure of rubber hardness; higher durometer values indicate firmer material suited to aggressive chewers.",
        "non-toxic material": "Materials certified free from harmful chemicals such as BPA, phthalates, and lead, safe for oral contact.",
        "destructive chewer": "A dog that habitually tears apart toys quickly, requiring extra-durable or heavy-duty toy options.",
        "supervised play": "Toy use that occurs only while an owner is present to intervene if the toy breaks or poses a risk.",
        "toy rotation": "The practice of cycling available toys on a schedule to maintain novelty and sustained interest.",

        # Chew-specific
        "dental chew": "A chew toy or edible designed to help scrape plaque and tartar from a dog’s teeth during normal chewing.",
        "bully stick": "A single-ingredient, dried beef tendon chew that is highly digestible and long-lasting for most dogs.",
        "antler chew": "A naturally shed deer or elk antler offered as a durable, long-lasting chewing option with minimal odour.",
        "nylon chew": "A synthetic chew toy made from tough nylon, designed for power chewers; should be replaced when worn.",
        "chew drive": "A dog’s innate motivation to gnaw, which serves to relieve teething pain, boredom, and anxiety.",
        "jaw fatigue": "Tiredness in the jaw muscles after sustained chewing, which can naturally calm an overstimulated dog.",

        # Fetch / tug / play
        "prey drive": "The instinctive urge to chase moving objects, which fetch and tug games channel into constructive play.",
        "tug-of-war": "A two-player pulling game that builds a dog’s confidence and strengthens the human–dog bond when played with rules.",
        "fetch drive": "A dog’s enthusiasm for retrieving thrown objects, often strongest in sporting and herding breeds.",
        "flirt pole": "A pole with a lure attached by a cord, used to simulate prey movement for high-energy chase play.",
        "drop cue": "A trained verbal command instructing a dog to release an object from its mouth, essential for safe tug games.",
        "impulse control": "A dog’s learned ability to resist acting on immediate urges, strengthened through structured play and training.",
        "high-value reward": "A treat or toy a dog finds exceptionally motivating, used to reinforce desired behaviours during training.",

        # Training-adjacent
        "positive reinforcement": "A training approach that rewards desired behaviours with treats, praise, or play to increase their frequency.",
        "resource guarding": "A behaviour in which a dog defends food, toys, or other valued items through growling, snapping, or body blocking.",
        "desensitisation": "Gradual, controlled exposure to a trigger at low intensity, aimed at reducing a dog’s fearful or reactive response.",
        "counter-conditioning": "Pairing a previously negative stimulus with something positive to change the dog’s emotional association.",
        "marker signal": "A consistent sound or word (e.g., a clicker) that precisely marks the moment a dog performs a desired behaviour.",
        "engagement": "A dog’s willing, focused attention on its handler, built through play, rewards, and relationship trust.",

        # Breed / size
        "size-appropriate toy": "A toy matched to a dog’s body size to prevent choking (too small) or disinterest (too large).",
        "breed-specific play style": "The characteristic way certain breeds prefer to interact with toys, shaped by their original working purpose.",
        "teething puppy": "A young dog (typically 3–6 months) whose adult teeth are emerging, creating a strong need to chew.",
        "senior dog enrichment": "Lower-impact mental and physical activities adapted for older dogs with reduced mobility or dental sensitivity.",

        # General / wellbeing
        "boredom-related behaviour": "Destructive habits such as excessive barking, digging, or furniture chewing that arise from insufficient stimulation.",
        "separation anxiety": "Distress a dog experiences when left alone, often eased by long-lasting enrichment toys.",
        "calming aid": "Any product or technique – including lick mats and Kongs – that helps reduce a dog’s stress or arousal level.",
        "interactive play": "Play that requires active participation from both dog and owner, strengthening the bond and providing exercise.",
        "independent play": "Self-directed activity with toys that does not require human involvement, useful for building confidence.",
        "durability rating": "A manufacturer’s or reviewer’s assessment of how well a toy withstands chewing and rough play over time.",
    }

    # Score each term by relevance to the post
    scored = []
    for term, definition in term_bank.items():
        score = 0
        term_words = term.lower().split()
        # Direct mention in content
        if term.lower() in text:
            score += 10
        # Partial word matches
        for w in term_words:
            if w in text:
                score += 3
            if w in title_l:
                score += 5
        # Topic-cluster boosts
        if any(kw in text for kw in ["enrichment", "puzzle", "mental", "brain", "stimulat"]):
            if any(kw in term.lower() for kw in ["enrichment", "sensory", "puzzle", "forag", "scent", "mental", "snuffle", "lick"]):
                score += 4
        if any(kw in text for kw in ["safety", "safe", "hazard", "toxic", "choking", "supervise"]):
            if any(kw in term.lower() for kw in ["chok", "squeak", "stuffing", "durometer", "toxic", "destruct", "supervis"]):
                score += 4
        if any(kw in text for kw in ["chew", "dental", "teeth", "gnaw", "bully", "antler", "nylon"]):
            if any(kw in term.lower() for kw in ["chew", "dental", "bully", "antler", "nylon", "jaw"]):
                score += 4
        if any(kw in text for kw in ["fetch", "tug", "chase", "retriev", "throw", "ball"]):
            if any(kw in term.lower() for kw in ["prey", "tug", "fetch", "flirt", "drop", "impulse"]):
                score += 4
        if any(kw in text for kw in ["train", "reinforc", "reward", "cue", "marker", "click"]):
            if any(kw in term.lower() for kw in ["reinforc", "guard", "desensit", "counter", "marker", "engag"]):
                score += 4
        if any(kw in text for kw in ["puppy", "senior", "breed", "size"]):
            if any(kw in term.lower() for kw in ["puppy", "senior", "breed", "size"]):
                score += 4
        if any(kw in text for kw in ["bored", "anxiet", "calm", "stress", "separation"]):
            if any(kw in term.lower() for kw in ["boredom", "separation", "calm", "independ"]):
                score += 4

        if score > 0:
            scored.append((score, term, definition))

    # Sort by score descending, take top 5-8
    scored.sort(key=lambda x: -x[0])
    # Take 6-8 to aim for good density
    count = min(max(6, len([s for s in scored if s[0] >= 5])), 8)
    selected = scored[:count]

    # Fallback: if fewer than 5, pad with general terms not yet selected
    fallback_terms = [
        ("interactive play", term_bank["interactive play"]),
        ("toy rotation", term_bank["toy rotation"]),
        ("mental stimulation", term_bank["mental stimulation"]),
        ("positive reinforcement", term_bank["positive reinforcement"]),
        ("size-appropriate toy", term_bank["size-appropriate toy"]),
        ("supervised play", term_bank["supervised play"]),
        ("durability rating", term_bank["durability rating"]),
        ("treat-dispensing toy", term_bank["treat-dispensing toy"]),
    ]
    selected_terms = {s[1] for s in selected}
    for ft, fd in fallback_terms:
        if len(selected) >= 5:
            break
        if ft not in selected_terms:
            selected.append((1, ft, fd))
            selected_terms.add(ft)

    return [(t, d) for (_, t, d) in selected[:8]]


def pick_common_mistakes(title, content_raw):
    """Choose 4-6 relevant Common Mistakes based on post topic."""
    text = strip_html(content_raw).lower()
    title_l = title.lower()

    mistake_bank = {
        # Enrichment
        "enrichment": [
            "Leaving puzzle toys out all day, which removes novelty and reduces their enrichment value.",
            "Using puzzles that are too difficult, causing frustration rather than enjoyment for the dog.",
            "Relying on a single type of enrichment instead of rotating sensory, food-based, and social activities.",
            "Skipping scent-based enrichment, which taps into the dog’s strongest and most satisfying sense.",
            "Offering enrichment only when the dog is already bored or destructive, rather than proactively scheduling it.",
            "Assuming all dogs enjoy the same puzzles – breed, age, and experience level affect preference.",
        ],
        # Safety
        "safety": [
            "Leaving a dog unsupervised with a new toy before knowing how aggressively they chew.",
            "Ignoring wear and tear – a toy that was safe last week may have exposed stuffing or squeakers today.",
            "Choosing toys based on appearance rather than checking the manufacturer’s size and durability ratings.",
            "Assuming “indestructible” labelling guarantees safety; no toy is truly indestructible for every dog.",
            "Not removing small plastic eyes, ribbons, or decorative parts before giving plush toys to dogs.",
            "Giving cooked bones or brittle materials that can splinter and puncture the digestive tract.",
        ],
        # Chew
        "chew": [
            "Offering chews that are too hard (e.g., weight-bearing bones), which can fracture teeth.",
            "Letting a chew shrink to a swallowable size without replacing it, creating a choking risk.",
            "Giving rawhide without supervision – large swallowed pieces can cause intestinal blockages.",
            "Choosing a chew based on price alone rather than verifying single-ingredient sourcing and origin.",
            "Not matching chew toughness to the dog’s jaw strength, leading to either instant destruction or disinterest.",
            "Offering too many chews at once, which can lead to resource guarding between dogs in multi-pet homes.",
        ],
        # Fetch / tug
        "fetch": [
            "Throwing sticks instead of purpose-built fetch toys, risking splinter injuries to the mouth and throat.",
            "Playing fetch on hard surfaces like concrete, which can damage a dog’s joints and paw pads over time.",
            "Using tennis balls as everyday chews – the abrasive felt wears down tooth enamel with prolonged gnawing.",
            "Forcing a dog that has no natural retrieve instinct into repetitive fetch, causing stress rather than fun.",
            "Not teaching a reliable “drop” cue before starting tug games, which can escalate possessive behaviour.",
            "Playing tug with jerky, vertical motions that strain the dog’s neck and spine.",
        ],
        # Training
        "training": [
            "Using toys only as bribes rather than earned rewards, which undermines the training relationship.",
            "Punishing a dog for destroying a toy instead of redirecting to an appropriate, durable alternative.",
            "Failing to pair a marker signal with the reward, making timing unclear for the dog.",
            "Practising the same game in the same location, so the dog’s skills don’t generalise to new environments.",
            "Ending play abruptly without a cool-down, leaving the dog in a heightened state of arousal.",
            "Ignoring early signs of resource guarding (freezing, hard stare) and allowing them to escalate.",
        ],
        # General / wellbeing
        "general": [
            "Buying the cheapest toys without checking for non-toxic certification or country-of-origin labelling.",
            "Assuming a tired dog is a happy dog – mental enrichment is just as important as physical exercise.",
            "Providing toys but never engaging in interactive play, missing the bonding benefit entirely.",
            "Storing all toys in an open basket so the dog has constant access, eliminating novelty and value.",
            "Not adjusting toy selection as the dog ages – a senior dog’s dental and mobility needs differ from a puppy’s.",
            "Overlooking water-based enrichment (e.g., paddling pools with floating toys) during warm weather.",
        ],
    }

    # Score categories
    category_scores = {}
    for cat, mistakes in mistake_bank.items():
        score = 0
        if cat == "enrichment" and any(kw in text for kw in ["enrichment", "puzzle", "mental", "stimulat", "forag", "scent", "snuffle"]):
            score += 10
        if cat == "safety" and any(kw in text for kw in ["safe", "hazard", "toxic", "choking", "supervise", "destruct"]):
            score += 10
        if cat == "chew" and any(kw in text for kw in ["chew", "dental", "teeth", "gnaw", "bully", "antler", "rawhide", "nylon"]):
            score += 10
        if cat == "fetch" and any(kw in text for kw in ["fetch", "tug", "chase", "retriev", "throw", "ball", "frisbee", "flirt"]):
            score += 10
        if cat == "training" and any(kw in text for kw in ["train", "reinforc", "reward", "cue", "marker", "click", "guard"]):
            score += 10
        if cat == "general":
            score += 3  # always somewhat relevant
        if any(kw in title_l for kw in cat.split()):
            score += 5
        category_scores[cat] = score

    # Sort and pick top 2 categories, take 2-3 from each to get 4-6 total
    sorted_cats = sorted(category_scores.items(), key=lambda x: -x[1])
    result = []
    for cat, sc in sorted_cats:
        if len(result) >= 6:
            break
        available = mistake_bank[cat]
        take = 3 if len(result) <= 2 else min(3, 6 - len(result))
        result.extend(available[:take])
    return result[:6]


# ── Block builders ───────────────────────────────────────────────────────
def build_key_terms_block(terms):
    """Build the Key Terms Gutenberg block."""
    li_items = "\n".join(
        f'<li><strong>{t}</strong> – {d}</li>' for t, d in terms
    )
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f8fafc"}},"border":{{"radius":"6px","width":"1px","color":"#e2e8f0"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:6px;background-color:#f8fafc;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">Key Terms</h4><!-- /wp:heading -->
<!-- wp:list --><ul class="wp-block-list">{li_items}</ul><!-- /wp:list -->
</div><!-- /wp:group -->'''


def build_common_mistakes_block(mistakes):
    """Build the Common Mistakes Gutenberg block."""
    li_items = "\n".join(f'<li>{m}</li>' for m in mistakes)
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fef2f2"}},"border":{{"radius":"6px","width":"1px","color":"#fecaca"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fecaca;border-width:1px;border-radius:6px;background-color:#fef2f2;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} --><h4 class="wp-block-heading">Common Mistakes</h4><!-- /wp:heading -->
<!-- wp:list --><ul class="wp-block-list">{li_items}</ul><!-- /wp:list -->
</div><!-- /wp:group -->'''


# ── Insertion logic ──────────────────────────────────────────────────────
# The editorial standards trust footer typically contains "editorial standards"
# or "PetHub Editorial" or similar trust-signal block.
FOOTER_PATTERNS = [
    '<!-- wp:group',  # last group block — we'll find the trust footer specifically
    'Editorial Standards',
    'editorial standards',
    'PetHub Editorial',
    'pethub editorial',
    'Our Editorial',
    'our editorial',
    'Transparency Disclaimer',
    'transparency disclaimer',
    'Editorial Integrity',
    'editorial integrity',
    'Trust & Transparency',
    'Sources &amp; References',
    'Sources & References',
    'sources &amp; references',
    'Further Reading',
    'further reading',
]


def find_footer_position(content):
    """Find the position just BEFORE the editorial standards trust footer."""
    # Look for known footer markers
    for pattern in FOOTER_PATTERNS[:8]:  # Check specific editorial patterns first
        idx = content.lower().rfind(pattern.lower())
        if idx > 0:
            # Walk back to the start of the wp:group block containing this
            # Find the nearest <!-- wp:group before this position
            search_area = content[:idx]
            group_start = search_area.rfind('<!-- wp:group')
            if group_start > 0:
                return group_start
            return idx

    # Fallback: insert before the very last <!-- wp:group block
    last_group = content.rfind('<!-- wp:group')
    if last_group > 100:  # Only if it's not the only group
        return last_group

    # Ultimate fallback: end of content
    return len(content)


def insert_blocks(content, key_terms_block, mistakes_block, has_terms, has_mistakes):
    """Insert blocks before the footer. Returns updated content."""
    insertion = ""
    if not has_terms:
        insertion += "\n\n" + key_terms_block
    if not has_mistakes:
        insertion += "\n\n" + mistakes_block

    if not insertion:
        return content

    pos = find_footer_position(content)
    # Insert with proper spacing
    updated = content[:pos].rstrip() + "\n\n" + insertion.strip() + "\n\n" + content[pos:]
    return updated


# ── Main processing ──────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("Phase 10AR – Glossary Saturation: Dog Toys + Uncategorized")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    # Fetch all posts
    print("\n[1/4] Fetching Dog Toys posts...")
    dog_toy_posts = fetch_dog_toy_posts()

    print("\n[2/4] Fetching Uncategorized posts...")
    uncat_posts = fetch_uncat_posts()

    # Combine with cluster labels
    all_posts = []
    for pid, post in dog_toy_posts.items():
        all_posts.append((pid, post, "Dog Toys"))
    for pid, post in uncat_posts.items():
        if pid not in dog_toy_posts:  # avoid duplicates
            all_posts.append((pid, post, "Uncategorized"))

    print(f"\n[3/4] Processing {len(all_posts)} total posts...")

    # CSV log
    csv_rows = []

    for i, (pid, post, cluster) in enumerate(all_posts):
        title = post.get("title", {}).get("rendered", f"Post {pid}")
        title_clean = html.unescape(re.sub(r'<[^>]+>', '', title))
        content_raw = post.get("content", {}).get("rendered", "")

        print(f"\n  [{i+1}/{len(all_posts)}] Post {pid}: {title_clean[:60]} ({cluster})")

        # Check existing blocks
        has_key_terms = "Key Terms" in content_raw
        has_common_mistakes = "Common Mistakes" in content_raw

        if has_key_terms and has_common_mistakes:
            print(f"    -> SKIP: both blocks already present")
            csv_rows.append({
                "id": pid, "title": title_clean, "cluster": cluster,
                "glossary_added": "already_present", "common_mistakes_added": "already_present",
                "status": "skipped"
            })
            continue

        # Need to fetch full content via raw context
        # The rendered content may have processed HTML; fetch raw
        url_raw = f"{BASE}/posts/{pid}?context=edit"
        print(f"    Fetching raw content...")
        post_edit = api_get(url_raw)
        time.sleep(DELAY)

        if not post_edit or "content" not in post_edit:
            print(f"    -> ERROR: could not fetch raw content")
            csv_rows.append({
                "id": pid, "title": title_clean, "cluster": cluster,
                "glossary_added": "error", "common_mistakes_added": "error",
                "status": "fetch_error"
            })
            continue

        raw_content = post_edit["content"].get("raw", "")
        if not raw_content:
            raw_content = post_edit["content"].get("rendered", "")

        # Re-check on raw content
        has_key_terms = "Key Terms" in raw_content
        has_common_mistakes = "Common Mistakes" in raw_content

        if has_key_terms and has_common_mistakes:
            print(f"    -> SKIP: both blocks already present (raw check)")
            csv_rows.append({
                "id": pid, "title": title_clean, "cluster": cluster,
                "glossary_added": "already_present", "common_mistakes_added": "already_present",
                "status": "skipped"
            })
            continue

        # Pick terms and mistakes
        glossary_added = "no"
        mistakes_added = "no"

        key_terms_block = ""
        mistakes_block = ""

        if not has_key_terms:
            terms = pick_glossary_terms(title_clean, raw_content)
            key_terms_block = build_key_terms_block(terms)
            term_names = [t for t, _ in terms]
            print(f"    Key Terms ({len(terms)}): {', '.join(term_names[:4])}...")

        if not has_common_mistakes:
            mistakes = pick_common_mistakes(title_clean, raw_content)
            mistakes_block = build_common_mistakes_block(mistakes)
            print(f"    Common Mistakes: {len(mistakes)} items")

        # Insert blocks
        updated_content = insert_blocks(
            raw_content, key_terms_block, mistakes_block,
            has_key_terms, has_common_mistakes
        )

        # Update post
        update_url = f"{BASE}/posts/{pid}"
        payload = {"content": updated_content}
        print(f"    Updating post {pid}...")
        result = api_post(update_url, payload)
        time.sleep(DELAY)

        if result and "id" in result:
            glossary_added = "yes" if not has_key_terms else "already_present"
            mistakes_added = "yes" if not has_common_mistakes else "already_present"
            print(f"    -> SUCCESS: glossary={glossary_added}, mistakes={mistakes_added}")
            status = "updated"
        else:
            print(f"    -> ERROR: update failed")
            glossary_added = "error"
            mistakes_added = "error"
            status = "update_error"

        csv_rows.append({
            "id": pid, "title": title_clean, "cluster": cluster,
            "glossary_added": glossary_added, "common_mistakes_added": mistakes_added,
            "status": status
        })

    # Write CSV log
    print(f"\n[4/4] Writing CSV log to {CSV_PATH}")
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "cluster", "glossary_added", "common_mistakes_added", "status"])
        writer.writeheader()
        writer.writerows(csv_rows)

    # Summary
    total = len(csv_rows)
    updated = sum(1 for r in csv_rows if r["status"] == "updated")
    skipped = sum(1 for r in csv_rows if r["status"] == "skipped")
    errors = sum(1 for r in csv_rows if "error" in r["status"])

    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {total} posts processed")
    print(f"  Updated:  {updated}")
    print(f"  Skipped:  {skipped} (already had both blocks)")
    print(f"  Errors:   {errors}")
    print(f"  CSV log:  {CSV_PATH}")
    print(f"Finished: {datetime.now().isoformat()}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
