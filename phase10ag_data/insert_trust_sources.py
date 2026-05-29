#!/usr/bin/env python3
"""
Phase 10AG: Insert trust footer blocks and UK authority Sources sections
into PetHub Online WordPress posts that are missing them.
"""

import subprocess
import json
import time
import csv
import tempfile
import os
import re
import html

WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
LOG_DIR = "/var/lib/freelancer/projects/40416335/phase10ag_data"
LOG_FILE = os.path.join(LOG_DIR, "trust_sources_insertion_log.csv")

# ──────────────────────────────────────────────────────────────
# Trust footer block (new styled version)
# ──────────────────────────────────────────────────────────────
TRUST_FOOTER = """<!-- wp:group {"style":{"color":{"background":"#f8fafb"},"border":{"radius":"8px","color":"#e2e8f0","width":"1px"},"spacing":{"padding":{"top":"20px","bottom":"20px","left":"24px","right":"24px"},"margin":{"top":"32px","bottom":"32px"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:8px;background-color:#f8fafb;margin-top:32px;margin-bottom:32px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px">
<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">Our Editorial Standards</h4>
<!-- /wp:heading -->
<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"}}} -->
<p style="font-size:14px">All content on Pet Hub Online is created following our <a href="https://pethubonline.com/our-editorial-process/">editorial process</a>, supported by thorough <a href="https://pethubonline.com/how-we-research-pet-products/">research methodology</a>. We maintain transparency through our <a href="https://pethubonline.com/corrections-and-updates-policy/">corrections and updates policy</a>. For details on how we handle affiliate relationships, see our <a href="https://pethubonline.com/affiliate-disclosure/">affiliate disclosure</a>.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->"""

# ──────────────────────────────────────────────────────────────
# UK Authority source templates by topic
# ──────────────────────────────────────────────────────────────
SOURCES_BY_TOPIC = {
    "dog_toys": [
        '<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/dogs/environment" target="_blank" rel="noopener nofollow">RSPCA – Providing a suitable environment and enrichment for dogs</a></li>',
        '<li><a href="https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/dog-toys-and-games" target="_blank" rel="noopener nofollow">PDSA – Dog toys and games: keeping your dog entertained</a></li>',
        '<li><a href="https://www.bluecross.org.uk/advice/dog/wellbeing-and-care/mental-stimulation-for-dogs" target="_blank" rel="noopener nofollow">Blue Cross – Mental stimulation for dogs: enrichment ideas</a></li>',
        '<li><a href="https://www.battersea.org.uk/pet-advice/dog-advice/dog-enrichment" target="_blank" rel="noopener nofollow">Battersea – Dog enrichment: toys, games, and activities</a></li>',
    ],
    "dog_training": [
        '<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/dogs/behaviour" target="_blank" rel="noopener nofollow">RSPCA – Understanding dog behaviour and training advice</a></li>',
        '<li><a href="https://www.thekennelclub.org.uk/getting-a-dog/are-you-ready/basic-dog-training/" target="_blank" rel="noopener nofollow">The Kennel Club – Basic dog training tips and techniques</a></li>',
        '<li><a href="https://www.dogstrust.org.uk/dog-advice/training" target="_blank" rel="noopener nofollow">Dogs Trust – Positive training methods and advice</a></li>',
        '<li><a href="https://www.bluecross.org.uk/advice/dog/training-and-behaviour" target="_blank" rel="noopener nofollow">Blue Cross – Dog training and behaviour guidance</a></li>',
    ],
    "dog_health": [
        '<li><a href="https://www.pdsa.org.uk/pet-help-and-advice/pet-health-hub" target="_blank" rel="noopener nofollow">PDSA – Pet Health Hub: common conditions and treatments</a></li>',
        '<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/dogs/health" target="_blank" rel="noopener nofollow">RSPCA – Dog health and welfare advice</a></li>',
        '<li><a href="https://www.bva.co.uk/take-action/our-policies/companion-animals/" target="_blank" rel="noopener nofollow">BVA – Companion animal health and welfare policies</a></li>',
        '<li><a href="https://www.bluecross.org.uk/advice/dog/health-and-care" target="_blank" rel="noopener nofollow">Blue Cross – Dog health and care advice</a></li>',
    ],
    "dog_beds": [
        '<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/dogs/environment" target="_blank" rel="noopener nofollow">RSPCA – Providing a comfortable environment for your dog</a></li>',
        '<li><a href="https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/your-dogs-environment" target="_blank" rel="noopener nofollow">PDSA – Creating the right environment for your dog</a></li>',
        '<li><a href="https://www.bluecross.org.uk/advice/dog/wellbeing-and-care" target="_blank" rel="noopener nofollow">Blue Cross – Dog wellbeing and care guidance</a></li>',
        '<li><a href="https://www.battersea.org.uk/pet-advice/dog-advice/settling-your-new-dog" target="_blank" rel="noopener nofollow">Battersea – Settling your dog at home: comfort and bedding</a></li>',
    ],
    "dog_food": [
        '<li><a href="https://www.pfma.org.uk/dog-nutrition" target="_blank" rel="noopener nofollow">PFMA – Dog nutrition guidelines and feeding advice</a></li>',
        '<li><a href="https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/your-dogs-diet" target="_blank" rel="noopener nofollow">PDSA – Your dog\'s diet: what to feed and how much</a></li>',
        '<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/dogs/diet" target="_blank" rel="noopener nofollow">RSPCA – Dog diet and nutrition advice</a></li>',
        '<li><a href="https://www.bluecross.org.uk/advice/dog/nutrition" target="_blank" rel="noopener nofollow">Blue Cross – Dog nutrition and feeding guidance</a></li>',
    ],
    "dog_grooming": [
        '<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/dogs/health/grooming" target="_blank" rel="noopener nofollow">RSPCA – Grooming your dog: coat, nails, and dental care</a></li>',
        '<li><a href="https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/grooming-your-dog" target="_blank" rel="noopener nofollow">PDSA – How to groom your dog at home</a></li>',
        '<li><a href="https://www.thekennelclub.org.uk/health-and-dog-care/grooming/" target="_blank" rel="noopener nofollow">The Kennel Club – Grooming advice by breed and coat type</a></li>',
        '<li><a href="https://www.bluecross.org.uk/advice/dog/wellbeing-and-care/grooming-your-dog" target="_blank" rel="noopener nofollow">Blue Cross – Dog grooming tips and techniques</a></li>',
    ],
    "dog_harnesses": [
        '<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/dogs/walking" target="_blank" rel="noopener nofollow">RSPCA – Walking your dog: leads, collars, and harnesses</a></li>',
        '<li><a href="https://www.dogstrust.org.uk/dog-advice/life-with-your-dog/at-home/dog-collars-leads-and-harnesses" target="_blank" rel="noopener nofollow">Dogs Trust – Choosing the right collar, lead, or harness</a></li>',
        '<li><a href="https://www.thekennelclub.org.uk/getting-a-dog/are-you-ready/walking-your-dog/" target="_blank" rel="noopener nofollow">The Kennel Club – Walking your dog safely and comfortably</a></li>',
        '<li><a href="https://www.bluecross.org.uk/advice/dog/wellbeing-and-care/walking-your-dog" target="_blank" rel="noopener nofollow">Blue Cross – Walking your dog: equipment and safety</a></li>',
    ],
    "cat_toys": [
        '<li><a href="https://www.cats.org.uk/help-and-advice/getting-a-cat/playing-with-your-cat" target="_blank" rel="noopener nofollow">Cats Protection – Playing with your cat: toys and enrichment</a></li>',
        '<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/cats/environment" target="_blank" rel="noopener nofollow">RSPCA – Providing a stimulating environment for cats</a></li>',
        '<li><a href="https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/kittens-cats/keeping-your-cat-entertained" target="_blank" rel="noopener nofollow">PDSA – Keeping your cat entertained: toys and games</a></li>',
        '<li><a href="https://www.bluecross.org.uk/advice/cat/wellbeing-and-care/cat-enrichment" target="_blank" rel="noopener nofollow">Blue Cross – Cat enrichment: toys, play, and activities</a></li>',
    ],
    "cat_supplies": [
        '<li><a href="https://www.cats.org.uk/help-and-advice" target="_blank" rel="noopener nofollow">Cats Protection – Cat care advice and welfare guidance</a></li>',
        '<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/cats" target="_blank" rel="noopener nofollow">RSPCA – Cat care, health, and welfare advice</a></li>',
        '<li><a href="https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/kittens-cats" target="_blank" rel="noopener nofollow">PDSA – Cat and kitten care advice</a></li>',
        '<li><a href="https://www.bluecross.org.uk/advice/cat" target="_blank" rel="noopener nofollow">Blue Cross – Cat advice and care guidance</a></li>',
    ],
    "indoor_cats": [
        '<li><a href="https://www.cats.org.uk/help-and-advice/getting-a-cat/indoor-cats" target="_blank" rel="noopener nofollow">Cats Protection – Keeping indoor cats happy and healthy</a></li>',
        '<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/cats/environment/indoors" target="_blank" rel="noopener nofollow">RSPCA – Indoor cat environment and enrichment advice</a></li>',
        '<li><a href="https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/kittens-cats/keeping-your-cat-entertained" target="_blank" rel="noopener nofollow">PDSA – Keeping indoor cats stimulated and active</a></li>',
        '<li><a href="https://www.bluecross.org.uk/advice/cat/wellbeing-and-care/keeping-your-cat-happy-indoors" target="_blank" rel="noopener nofollow">Blue Cross – Keeping your cat happy indoors</a></li>',
    ],
    "puppy_care": [
        '<li><a href="https://www.thekennelclub.org.uk/getting-a-dog/puppy/" target="_blank" rel="noopener nofollow">The Kennel Club – Puppy care, training, and development</a></li>',
        '<li><a href="https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/getting-a-puppy" target="_blank" rel="noopener nofollow">PDSA – Getting a puppy: care and development guide</a></li>',
        '<li><a href="https://www.dogstrust.org.uk/dog-advice/getting-a-dog/puppies" target="_blank" rel="noopener nofollow">Dogs Trust – Puppy advice: health, socialisation, and training</a></li>',
        '<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/dogs/puppy" target="_blank" rel="noopener nofollow">RSPCA – Puppy care and welfare advice</a></li>',
    ],
    "educational": [
        '<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets" target="_blank" rel="noopener nofollow">RSPCA – Pet welfare advice and guidance</a></li>',
        '<li><a href="https://www.pdsa.org.uk/pet-help-and-advice" target="_blank" rel="noopener nofollow">PDSA – Pet health and care advice hub</a></li>',
        '<li><a href="https://www.bva.co.uk/take-action/our-policies/" target="_blank" rel="noopener nofollow">BVA – Veterinary policies and animal welfare guidance</a></li>',
        '<li><a href="https://www.bluecross.org.uk/advice" target="_blank" rel="noopener nofollow">Blue Cross – Pet advice and welfare resources</a></li>',
    ],
    "dog_care": [
        '<li><a href="https://www.rspca.org.uk/adviceandwelfare/pets/dogs" target="_blank" rel="noopener nofollow">RSPCA – Dog care, health, and welfare advice</a></li>',
        '<li><a href="https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs" target="_blank" rel="noopener nofollow">PDSA – Looking after your dog: care and health</a></li>',
        '<li><a href="https://www.dogstrust.org.uk/dog-advice" target="_blank" rel="noopener nofollow">Dogs Trust – Dog advice: care, health, and training</a></li>',
        '<li><a href="https://www.thekennelclub.org.uk/health-and-dog-care/" target="_blank" rel="noopener nofollow">The Kennel Club – Health and dog care resources</a></li>',
    ],
}

# Map cluster names to source topics
CLUSTER_TO_TOPIC = {
    "Dog Toys": "dog_toys",
    "Dog Training": "dog_training",
    "Dog Health": "dog_health",
    "Dog Beds": "dog_beds",
    "Dog Food": "dog_food",
    "Dog Grooming": "dog_grooming",
    "Dog Harnesses": "dog_harnesses",
    "Dog Care": "dog_care",
    "Cat Toys": "cat_toys",
    "Cat Supplies": "cat_supplies",
    "Indoor Cats": "indoor_cats",
    "Puppy Care": "puppy_care",
    "Educational": "educational",
    "Uncategorized": "educational",  # fallback
}

# ──────────────────────────────────────────────────────────────
# Posts to process
# ──────────────────────────────────────────────────────────────
POSTS_NEED_TRUST = [
    6052, 6050, 6049, 6048, 6047, 6046, 6045, 6044, 6042, 6039,
    5950, 5946, 5942, 5938, 5935, 5934, 5933, 5932, 5931, 5930,
    5523, 5522, 5521, 5520, 5519, 5512, 5511, 5510, 5509, 5508,
    5483, 5476, 5473, 5471, 5469, 5467, 5464, 5462, 5460, 5458,
    5425, 5424, 5423, 5422, 5421, 5420, 5419, 5418, 5417, 5416,
    5415, 5414, 5296, 5036, 5035, 5034, 5033, 5032,
    4792, 4791, 4790, 4789, 4788, 4787, 4786, 4785, 4784, 4783,
    4573, 4570, 4576, 4574, 4571, 4407,
    3996, 3959, 3957, 3956, 3960,
    3839, 3838, 3837, 3836,
    696, 3,
]

POSTS_NEED_SOURCES = [
    6052, 6050, 6049, 6048, 6047, 6046, 6045, 6044, 6042, 6039,
    5950, 5946, 5942, 5938, 5935, 5934, 5933, 5932, 5931, 5930,
    3996, 3959, 3957, 3956,
]

# Merge into single set of all post IDs to process
ALL_POST_IDS = sorted(set(POSTS_NEED_TRUST) | set(POSTS_NEED_SOURCES), reverse=True)

# ──────────────────────────────────────────────────────────────
# Load cluster info from inventory
# ──────────────────────────────────────────────────────────────
def load_inventory():
    """Load cluster info from inventory CSV."""
    inv = {}
    csv_path = "/var/lib/freelancer/projects/40416335/phase10af_data/post_authority_inventory.csv"
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = int(row["id"])
            inv[pid] = {
                "title": row["title"],
                "cluster": row["cluster"],
            }
    return inv


def fetch_post(post_id):
    """Fetch post content (raw) via WP API using curl."""
    url = f"{WP_API}/posts/{post_id}?_fields=id,title,content&context=edit"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        return {
            "id": data["id"],
            "title": data["title"]["raw"],
            "content": data["content"]["raw"],
        }
    except (json.JSONDecodeError, KeyError) as e:
        print(f"  ERROR parsing post {post_id}: {e}")
        return None


def update_post(post_id, new_content):
    """Update post content via WP API using curl with temp file."""
    payload = json.dumps({"content": new_content})
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(payload)
        tmpfile = f.name

    try:
        url = f"{WP_API}/posts/{post_id}"
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmpfile}",
             url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return False, f"curl error: {result.returncode}"
        try:
            data = json.loads(result.stdout)
            if "id" in data:
                return True, "ok"
            else:
                msg = data.get("message", str(data)[:200])
                return False, f"API error: {msg}"
        except json.JSONDecodeError:
            return False, f"Invalid JSON response: {result.stdout[:200]}"
    finally:
        os.unlink(tmpfile)


def get_sources_block(cluster, title):
    """Build Sources and Further Reading block based on cluster/topic."""
    topic = CLUSTER_TO_TOPIC.get(cluster, "educational")

    # Smart override based on title keywords
    title_lower = title.lower()
    if "cat" in title_lower and topic == "dog_toys":
        topic = "cat_toys"
    elif "cat" in title_lower and topic not in ("cat_toys", "cat_supplies", "indoor_cats"):
        topic = "cat_toys"
    elif "puppy" in title_lower and topic not in ("puppy_care",):
        topic = "puppy_care"
    elif "food" in title_lower or "nutrition" in title_lower or "feeding" in title_lower:
        topic = "dog_food"
    elif "groom" in title_lower:
        topic = "dog_grooming"
    elif "bed" in title_lower and "dog" in title_lower:
        topic = "dog_beds"
    elif "harness" in title_lower or "collar" in title_lower or "lead" in title_lower:
        topic = "dog_harnesses"
    elif "health" in title_lower or "dental" in title_lower or "vet" in title_lower:
        topic = "dog_health"
    elif "train" in title_lower or "behaviour" in title_lower or "behavior" in title_lower:
        topic = "dog_training"

    sources = SOURCES_BY_TOPIC.get(topic, SOURCES_BY_TOPIC["educational"])

    # Build the block
    items = "\n".join(sources)
    block = f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Sources and Further Reading</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul class="wp-block-list">
{items}
</ul>
<!-- /wp:list -->"""
    return block, len(sources)


def find_heading_start(content, text_idx):
    """Given a position of text inside a heading, find the start of that heading block.
    Looks back for <h3 or <!-- wp:heading within a reasonable distance."""
    search_start = max(0, text_idx - 200)
    zone = content[search_start:text_idx]

    # Look for wp:heading comment first (block editor)
    wp_idx = zone.rfind("<!-- wp:heading")
    if wp_idx != -1:
        return search_start + wp_idx

    # Fall back to raw <h3 tag
    h3_idx = zone.rfind("<h3")
    if h3_idx != -1:
        return search_start + h3_idx

    # No heading found, return the text position
    return text_idx


def find_separator_before(content, pos):
    """Look for an <hr> separator in the 300 chars before pos."""
    search_start = max(0, pos - 300)
    zone = content[search_start:pos]

    # Look for wp:separator comment
    wp_idx = zone.rfind("<!-- wp:separator")
    if wp_idx != -1:
        return search_start + wp_idx

    # Fall back to raw <hr tag
    hr_idx = zone.rfind("<hr")
    if hr_idx != -1:
        return search_start + hr_idx

    return None


def find_insertion_point(content):
    """Find best insertion point for trust footer and sources.

    Returns dict of marker positions for key content sections.
    """
    markers = {
        "sources": None,
        "trusted_external": None,
        "old_editorial": None,
        "related_reading": None,
    }

    # Find Sources and Further Reading
    idx = content.find("Sources and Further Reading")
    if idx != -1:
        markers["sources"] = find_heading_start(content, idx)

    # Find Trusted External Resources
    idx = content.find("Trusted External Resources")
    if idx != -1:
        markers["trusted_external"] = find_heading_start(content, idx)

    # Find About Our Editorial Standards
    idx = content.find("About Our Editorial Standards")
    if idx != -1:
        heading_pos = find_heading_start(content, idx)
        sep_pos = find_separator_before(content, heading_pos)
        markers["old_editorial"] = sep_pos if sep_pos is not None else heading_pos

    # Find Related Reading / Related Articles (as headings)
    for term in ["Related Reading", "Related Articles"]:
        idx = content.find(term)
        if idx != -1:
            pos = find_heading_start(content, idx)
            if markers["related_reading"] is None or pos < markers["related_reading"]:
                markers["related_reading"] = pos

    # Find "For related guidance" paragraphs - but only the FIRST one
    idx = content.find("For related guidance")
    if idx != -1:
        search_start = max(0, idx - 200)
        zone = content[search_start:idx]
        # Look for wp:paragraph comment
        wp_idx = zone.rfind("<!-- wp:paragraph")
        if wp_idx != -1:
            pos = search_start + wp_idx
        else:
            p_idx = zone.rfind("<p")
            pos = (search_start + p_idx) if p_idx != -1 else idx

        if markers["related_reading"] is None or pos < markers["related_reading"]:
            markers["related_reading"] = pos

    return markers


def process_post(post_id, inventory, need_trust, need_sources):
    """Process a single post: add trust footer and/or sources."""
    post = fetch_post(post_id)
    if not post:
        return {"id": post_id, "title": "FETCH_ERROR", "trust_inserted": False,
                "sources_inserted": False, "source_count": 0, "status": "error_fetch"}

    content = post["content"]
    title = post["title"]
    inv_info = inventory.get(post_id, {"title": title, "cluster": "Uncategorized"})
    cluster = inv_info["cluster"]

    # Check for existing new-style trust footer
    has_new_trust = "#f8fafb" in content or ("Our Editorial Standards</h4>" in content)
    # Check for existing sources
    has_existing_sources = "Sources and Further Reading" in content

    trust_inserted = False
    sources_inserted = False
    source_count = 0
    modified = False

    # Determine what we actually need to do
    do_trust = need_trust and not has_new_trust
    do_sources = need_sources and not has_existing_sources

    if not do_trust and not do_sources:
        status = "skipped_already_present"
        if need_trust and has_new_trust:
            status = "skipped_trust_exists"
        if need_sources and has_existing_sources:
            status = "skipped_sources_exist" if not need_trust else "skipped_both_exist"
        return {"id": post_id, "title": title, "trust_inserted": False,
                "sources_inserted": False, "source_count": 0, "status": status}

    markers = find_insertion_point(content)

    # Build the blocks to insert
    sources_block = ""
    trust_block = ""

    if do_sources:
        sources_block, source_count = get_sources_block(cluster, title)

    if do_trust:
        trust_block = TRUST_FOOTER

    # Strategy: Insert the new trust footer (and sources if needed) at the right position.
    # Priority order for insertion point:
    #   1. Before old "About Our Editorial Standards" section (includes hr separator)
    #   2. Before "Trusted External Resources" section
    #   3. After end of "Sources and Further Reading" section
    #   4. Before "Related Reading" if it's in the last 20% of content
    #   5. End of content

    insert_pos = None

    if markers["old_editorial"] is not None:
        insert_pos = markers["old_editorial"]
    elif markers["trusted_external"] is not None:
        insert_pos = markers["trusted_external"]
    elif markers["sources"] is not None:
        # Insert after the sources section
        src_heading = content.find("Sources and Further Reading", markers["sources"])
        if src_heading != -1:
            ul_end = content.find("</ul>", src_heading)
            if ul_end != -1:
                after_ul = ul_end + len("</ul>")
                # Check for wp:list closing comment
                rest = content[after_ul:after_ul + 50]
                list_end = rest.find("<!-- /wp:list -->")
                if list_end != -1:
                    insert_pos = after_ul + list_end + len("<!-- /wp:list -->")
                else:
                    insert_pos = after_ul
    elif markers["related_reading"] is not None:
        # Only use related_reading if it's in the last 30% of content
        if markers["related_reading"] > len(content) * 0.7:
            insert_pos = markers["related_reading"]

    # Build combined block
    blocks_to_insert = []
    if do_sources:
        blocks_to_insert.append(sources_block)
    if do_trust:
        blocks_to_insert.append(trust_block)

    combined = "\n\n".join(blocks_to_insert)

    if insert_pos is not None:
        new_content = content[:insert_pos] + combined + "\n\n" + content[insert_pos:]
    else:
        # Append at end
        new_content = content.rstrip() + "\n\n" + combined

    # Update the post
    success, msg = update_post(post_id, new_content)

    if success:
        trust_inserted = do_trust
        sources_inserted = do_sources
        status = "updated"
        actions = []
        if trust_inserted:
            actions.append("trust")
        if sources_inserted:
            actions.append(f"sources({source_count})")
        status = f"updated: {'+'.join(actions)}"
    else:
        status = f"error_update: {msg}"

    return {
        "id": post_id,
        "title": title,
        "trust_inserted": trust_inserted,
        "sources_inserted": sources_inserted,
        "source_count": source_count,
        "status": status,
    }


def main():
    print("=" * 70)
    print("Phase 10AG: Trust Footer + UK Authority Sources Insertion")
    print("=" * 70)

    # Load inventory
    inventory = load_inventory()
    print(f"Loaded {len(inventory)} posts from inventory")

    # Prepare log
    os.makedirs(LOG_DIR, exist_ok=True)
    log_rows = []

    need_trust_set = set(POSTS_NEED_TRUST)
    need_sources_set = set(POSTS_NEED_SOURCES)

    total = len(ALL_POST_IDS)
    print(f"Total posts to process: {total}")
    print(f"  Need trust footer: {len(need_trust_set)}")
    print(f"  Need sources: {len(need_sources_set)}")
    print()

    # Process in batches
    BATCH_SIZE = 15
    updated = 0
    skipped = 0
    errors = 0

    for i in range(0, total, BATCH_SIZE):
        batch = ALL_POST_IDS[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"--- Batch {batch_num}/{total_batches} (posts {batch[0]}..{batch[-1]}) ---")

        for post_id in batch:
            need_trust = post_id in need_trust_set
            need_sources = post_id in need_sources_set

            print(f"  Processing {post_id} (trust={need_trust}, sources={need_sources})...", end=" ", flush=True)

            result = process_post(post_id, inventory, need_trust, need_sources)
            log_rows.append(result)

            if "error" in result["status"]:
                errors += 1
                print(f"ERROR: {result['status']}")
            elif "skipped" in result["status"]:
                skipped += 1
                print(f"SKIP: {result['status']}")
            else:
                updated += 1
                print(f"OK: {result['status']}")

            time.sleep(0.5)

        print()

    # Write CSV log
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "trust_inserted", "sources_inserted", "source_count", "status"])
        writer.writeheader()
        writer.writerows(log_rows)

    print("=" * 70)
    print(f"COMPLETE: {updated} updated, {skipped} skipped, {errors} errors")
    print(f"Log: {LOG_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
