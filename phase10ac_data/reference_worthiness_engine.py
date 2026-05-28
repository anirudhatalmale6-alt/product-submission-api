#!/usr/bin/env python3
"""
10AC-E: Reference-Worthiness Engine
Adds authoritative external references (Blue Cross, PDSA, RSPCA, BVA,
FEDIAF, Battersea, Cats Protection, UK Gov) to posts that lack them.
Expanded source list per Phase 10AC directive.
"""

import subprocess, json, time, csv, re

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

TRUST_BLOCK_MARKER = '<!-- wp:separator {"className":"is-style-wide"} -->'

AUTHORITY_SOURCES = {
    "dog_toy": [
        ("RSPCA", "https://www.rspca.org.uk/adviceandwelfare/pets/dogs/play", "RSPCA guide to safe play and enrichment for dogs"),
        ("Blue Cross", "https://www.bluecross.org.uk/advice/dog/exercise-and-play", "Blue Cross advice on dog exercise and play"),
        ("Battersea", "https://www.battersea.org.uk/pet-advice/dog-advice/how-play-your-dog", "Battersea guidance on playing with dogs safely"),
    ],
    "dog_food": [
        ("FEDIAF", "https://fediaf.org/nutritional-guidelines.html", "FEDIAF European pet food nutritional guidelines"),
        ("PDSA", "https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/your-dogs-diet", "PDSA guide to feeding your dog"),
        ("RSPCA", "https://www.rspca.org.uk/adviceandwelfare/pets/dogs/diet", "RSPCA guidance on dog diet and nutrition"),
        ("Blue Cross", "https://www.bluecross.org.uk/advice/dog/nutrition-and-diet", "Blue Cross dog nutrition advice"),
    ],
    "dog_bed": [
        ("Blue Cross", "https://www.bluecross.org.uk/advice/dog/settling-your-new-dog-at-home", "Blue Cross guide to creating a comfortable home environment"),
        ("PDSA", "https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/creating-a-safe-space-for-your-dog", "PDSA advice on creating a safe resting space"),
    ],
    "dog_harness": [
        ("RSPCA", "https://www.rspca.org.uk/adviceandwelfare/pets/dogs/walkingthedog", "RSPCA guidance on walking equipment for dogs"),
        ("Blue Cross", "https://www.bluecross.org.uk/advice/dog/walking-your-dog", "Blue Cross dog walking advice and equipment guide"),
        ("BVA", "https://www.bva.co.uk/", "British Veterinary Association — professional veterinary body"),
    ],
    "dog_health": [
        ("BVA", "https://www.bva.co.uk/take-action/our-policies/companion-animals/", "British Veterinary Association guidance on companion animal health"),
        ("PDSA", "https://www.pdsa.org.uk/pet-help-and-advice/pet-health-hub/conditions", "PDSA Pet Health Hub — conditions and symptoms guide"),
        ("RSPCA", "https://www.rspca.org.uk/adviceandwelfare/pets/dogs/health", "RSPCA dog health and welfare guidance"),
        ("Blue Cross", "https://www.bluecross.org.uk/advice/dog/health-and-sickness", "Blue Cross dog health advice"),
    ],
    "puppy_care": [
        ("RSPCA", "https://www.rspca.org.uk/adviceandwelfare/pets/dogs/puppy", "RSPCA complete guide to puppy care"),
        ("Blue Cross", "https://www.bluecross.org.uk/advice/dog/getting-a-puppy", "Blue Cross puppy advice and socialisation guidance"),
        ("PDSA", "https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs/getting-a-puppy", "PDSA guide to caring for your new puppy"),
        ("Battersea", "https://www.battersea.org.uk/pet-advice/dog-advice/bringing-your-new-dog-home", "Battersea guidance on bringing a new dog home"),
    ],
    "cat_supplies": [
        ("Cats Protection", "https://www.cats.org.uk/help-and-advice", "Cats Protection comprehensive feline care guidance"),
        ("RSPCA", "https://www.rspca.org.uk/adviceandwelfare/pets/cats", "RSPCA advice on cat welfare and environment"),
        ("Blue Cross", "https://www.bluecross.org.uk/advice/cat", "Blue Cross cat care and enrichment advice"),
        ("PDSA", "https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/kittens-cats", "PDSA guide to looking after your cat"),
    ],
    "dog_care": [
        ("RSPCA", "https://www.rspca.org.uk/adviceandwelfare/pets/dogs", "RSPCA comprehensive dog care and welfare guidance"),
        ("PDSA", "https://www.pdsa.org.uk/pet-help-and-advice/looking-after-your-pet/puppies-dogs", "PDSA complete guide to looking after your dog"),
        ("Blue Cross", "https://www.bluecross.org.uk/advice/dog", "Blue Cross dog care advice hub"),
    ],
    "pet_care_general": [
        ("RSPCA", "https://www.rspca.org.uk/adviceandwelfare/pets", "RSPCA pet welfare and care advice"),
        ("PDSA", "https://www.pdsa.org.uk/pet-help-and-advice", "PDSA pet health and care advice hub"),
        ("Blue Cross", "https://www.bluecross.org.uk/advice", "Blue Cross pet advice and welfare guidance"),
        ("UK Gov", "https://www.gov.uk/guidance/animal-welfare", "UK Government animal welfare guidance and legislation"),
    ],
}

KNOWN_REFS = ["rspca.org", "bva.co.uk", "fediaf.org", "battersea.org", "cats.org.uk",
              "gov.uk", "pdsa.org", "bluecross.org"]

def fetch_all_posts():
    posts = []
    page = 1
    while True:
        cmd = ["curl", "-s", "--compressed", "-u", AUTH,
               f"{WP_URL}/posts?status=publish&per_page=100&page={page}&context=edit"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        batch = json.loads(r.stdout)
        if not batch or isinstance(batch, dict):
            break
        posts.extend(batch)
        if len(batch) < 100:
            break
        page += 1
        time.sleep(2)
    return posts

def update_post(post_id, content):
    cmd = ["curl", "-s", "--compressed", "-u", AUTH,
           "-X", "POST", f"{WP_URL}/posts/{post_id}",
           "-H", "Content-Type: application/json",
           "-d", json.dumps({"content": content})]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

def classify_cluster(post):
    title = post["title"]["raw"].lower()
    cats = post.get("categories", [])
    if 1344 in cats or "dog toy" in title or ("toy" in title and "cat" not in title):
        return "dog_toy"
    if any(kw in title for kw in ["dog food", "puppy food", "dry food", "dry vs wet"]):
        return "dog_food"
    if "dog bed" in title or ("bed" in title and "cat" not in title):
        return "dog_bed"
    if "harness" in title and "cat" not in title:
        return "dog_harness"
    if any(kw in title for kw in ["flea", "joint supplement", "dental care", "dog health"]):
        return "dog_health"
    if any(kw in title for kw in ["grooming", "seasonal dog", "first-time dog", "dental health", "measure your dog"]):
        return "dog_care"
    if "cat toy" in title or "cat play" in title:
        return "cat_supplies"
    if "cat " in title:
        return "cat_supplies"
    if "puppy" in title or "socialisation" in title:
        return "puppy_care"
    if any(kw in title for kw in ["collar", "lead", "bowl", "training treat", "interactive dog", "indestructible"]):
        return "dog_care"
    return "pet_care_general"

def count_external_refs(content):
    return sum(1 for ref in KNOWN_REFS if ref in content)

def get_missing_sources(content, cluster):
    sources = AUTHORITY_SOURCES.get(cluster, AUTHORITY_SOURCES["pet_care_general"])
    missing = []
    for name, url, desc in sources:
        domain = url.split("//")[1].split("/")[0].replace("www.", "")
        if domain not in content:
            missing.append((name, url, desc))
    return missing

def build_reference_block(sources):
    items = ""
    for name, url, desc in sources[:3]:
        items += f'<li><a href="{url}" target="_blank" rel="noopener">{name}</a> — {desc}</li>\n'

    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Trusted External Resources</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
{items.rstrip()}
</ul>
<!-- /wp:list -->"""

print("Fetching all published posts...")
posts = fetch_all_posts()
print(f"Found {len(posts)} posts\n")

candidates = []
for post in posts:
    content = post["content"]["raw"]
    ext_count = count_external_refs(content)
    if ext_count >= 2:
        continue

    cluster = classify_cluster(post)
    missing = get_missing_sources(content, cluster)
    if not missing:
        continue

    candidates.append({
        "post": post,
        "cluster": cluster,
        "current_refs": ext_count,
        "missing": missing
    })

candidates.sort(key=lambda x: x["current_refs"])
targets = candidates[:30]

print(f"Found {len(candidates)} posts needing external refs, targeting {len(targets)}\n")

results = []
updated_count = 0

for item in targets:
    post = item["post"]
    pid = post["id"]
    title = post["title"]["raw"]
    content = post["content"]["raw"]
    missing = item["missing"]

    block = build_reference_block(missing)

    if TRUST_BLOCK_MARKER in content:
        last_idx = content.rfind(TRUST_BLOCK_MARKER)
        new_content = content[:last_idx] + f"\n{block}\n\n" + content[last_idx:]
    else:
        new_content = content + f"\n\n{block}"

    result = update_post(pid, new_content)
    refs_added = min(3, len(missing))
    if "id" in result:
        updated_count += 1
        results.append({
            "post_id": pid,
            "title": title[:60],
            "cluster": item["cluster"],
            "refs_added": refs_added,
            "sources": ", ".join(s[0] for s in missing[:3]),
            "status": "updated"
        })
        print(f"  {pid}: +{refs_added} refs ({', '.join(s[0] for s in missing[:3])}) — {title[:45]}")
    else:
        results.append({
            "post_id": pid,
            "title": title[:60],
            "cluster": item["cluster"],
            "refs_added": 0,
            "sources": "",
            "status": "error"
        })
    time.sleep(2)

csv_path = "/var/lib/freelancer/projects/40416335/phase10ac_data/Reference_Worthiness_Expansion.csv"
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["post_id", "title", "cluster", "refs_added", "sources", "status"])
    w.writeheader()
    w.writerows(results)

total_refs = sum(r["refs_added"] for r in results)
print(f"\n=== REFERENCE WORTHINESS: {updated_count} posts updated, {total_refs} external refs added ===")
