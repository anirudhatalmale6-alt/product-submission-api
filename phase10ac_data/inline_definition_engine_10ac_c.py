#!/usr/bin/env python3
"""
10AC-C: Inline Definition Engine v2
Targets posts that either lack Key Terms blocks entirely, or have
thin glossary coverage. Adds/expands Key Terms with relevant definitions.
"""

import subprocess, json, time, csv, re

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

TRUST_BLOCK_MARKER = '<!-- wp:separator {"className":"is-style-wide"} -->'

DEFINITIONS_POOL = {
    "enrichment": ("Enrichment", "structured activities that stimulate a dog's mind and body beyond basic exercise"),
    "desensitisation": ("Desensitisation", "gradually exposing a dog to a feared stimulus at low intensity until the emotional response diminishes"),
    "resource guarding": ("Resource Guarding", "behaviour where a dog protects valued items such as food, toys, or sleeping spots from people or other animals"),
    "brachycephalic": ("Brachycephalic", "short-skulled breeds such as Pugs, Bulldogs, and French Bulldogs, which can have breathing difficulties"),
    "kibble": ("Kibble", "dry, pellet-shaped commercially processed dog food"),
    "orthopedic": ("Orthopaedic Bed", "a bed with supportive memory foam designed to cushion joints and relieve pressure points"),
    "no-pull harness": ("No-Pull Harness", "a harness with a front clip that discourages pulling without causing pain"),
    "positive reinforcement": ("Positive Reinforcement", "a training method that rewards desired behaviour to increase the likelihood of it being repeated"),
    "socialisation": ("Socialisation", "the process of exposing puppies to a wide range of people, animals, and environments during a critical developmental window, typically between 3 and 14 weeks"),
    "recall": ("Recall", "the ability of a dog to return to its owner when called, regardless of distractions"),
    "counter-conditioning": ("Counter-Conditioning", "a technique that changes an animal's emotional response to a stimulus by pairing it with something enjoyable"),
    "mouthing": ("Mouthing", "a natural puppy behaviour involving gentle biting during play, which needs redirection before becoming problematic"),
    "puzzle feeder": ("Puzzle Feeder", "a toy or device requiring a dog to solve a problem to access food rewards, providing mental stimulation"),
    "high-value treat": ("High-Value Treat", "a particularly appealing reward such as cooked chicken or cheese, used for difficult training behaviours"),
    "clicker training": ("Clicker Training", "a positive reinforcement method using a small device that marks the exact moment a desired behaviour occurs"),
    "slow feeder": ("Slow Feeder", "a bowl with ridges or obstacles that forces slower eating, reducing the risk of bloat and improving digestion"),
    "separation anxiety": ("Separation Anxiety", "a behavioural condition where a dog becomes extremely distressed when left alone"),
    "crate training": ("Crate Training", "the process of teaching a dog to accept and feel comfortable in a crate as a safe den-like space"),
    "lick mat": ("Lick Mat", "a textured silicone mat spread with soft food that encourages slow licking, which has a calming effect"),
    "denier": ("Denier", "a unit measuring fabric fibre thickness — higher denier means tougher, more tear-resistant material"),
    "catnip": ("Catnip", "a herb from the mint family that triggers a temporary euphoric response in about 60–70% of cats"),
    "feliway": ("Pheromone Diffuser", "a synthetic version of feline facial pheromones that can help reduce stress-related behaviours in cats"),
    "interactive toy": ("Interactive Toy", "a toy requiring human participation or active manipulation by the pet, as opposed to a passive chew or plush"),
    "tug toy": ("Tug Toy", "a toy designed for pulling games between dog and owner, typically made from rope, rubber, or reinforced fabric"),
    "kong": ("Stuffable Toy", "a hollow rubber toy that can be filled with food or treats to provide extended mental stimulation"),
    "nylabone": ("Nylon Chew", "a synthetic chewing toy made from durable nylon, designed for dogs who destroy softer materials quickly"),
    "flirt pole": ("Flirt Pole", "a pole with a rope and lure attachment used for chase-based play, engaging a dog's prey drive in a controlled way"),
    "snuffle mat": ("Snuffle Mat", "a fabric mat with strips or folds where treats can be hidden, encouraging dogs to use their nose to forage"),
    "dental chew": ("Dental Chew", "a treat or toy with textured surfaces designed to help clean teeth and reduce plaque during chewing"),
    "raw hide": ("Rawhide", "dried animal skin given as a long-lasting chew, which carries a choking risk if large pieces break off"),
    "antler": ("Antler Chew", "a naturally shed deer or elk antler used as a durable chew, though it can crack teeth in aggressive chewers"),
    "freeze-dried": ("Freeze-Dried Treats", "treats produced by removing moisture at low temperature, preserving nutrients and flavour without artificial preservatives"),
    "grain-free": ("Grain-Free", "food formulated without wheat, corn, rice, or other grains — note that the FDA has investigated a potential link between grain-free diets and heart disease in dogs"),
    "complete food": ("Complete Food", "food that contains all the nutrients a pet needs in the correct proportions, requiring no supplements"),
    "complementary food": ("Complementary Food", "food that does not contain all required nutrients and must be fed alongside a complete food"),
    "body condition score": ("Body Condition Score", "a 1–9 scale used by vets to assess whether a pet is underweight, ideal, or overweight based on visible and palpable fat"),
    "microchip": ("Microchip", "a small electronic chip implanted under the skin that stores a unique ID number, legally required for dogs in the UK since 2016"),
}

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

def find_matching_terms(content):
    content_lower = content.lower()
    existing_terms = re.findall(r'<strong>([^<]+)</strong>\s*[—–-]', content)
    existing_set = set(t.lower().strip() for t in existing_terms)

    matched = []
    for keyword, (term_name, definition) in DEFINITIONS_POOL.items():
        if keyword.lower() in content_lower:
            if term_name.lower() not in existing_set and keyword.lower() not in existing_set:
                matched.append((term_name, definition))
    return matched

def build_key_terms_block(terms):
    items = ""
    for name, defn in terms:
        items += f"<li><strong>{name}</strong> — {defn}</li>\n"
    return f"""<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Key Terms</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
{items.rstrip()}
</ul>
<!-- /wp:list -->"""

def expand_key_terms(content, new_terms):
    end_list = content.rfind("</ul>\n<!-- /wp:list -->")
    if end_list == -1:
        return content, 0

    key_terms_heading = content.rfind("Key Terms", 0, end_list)
    if key_terms_heading == -1:
        return content, 0

    list_end = content.find("</ul>", key_terms_heading)
    if list_end == -1:
        return content, 0

    new_items = ""
    for name, defn in new_terms:
        new_items += f"\n<li><strong>{name}</strong> — {defn}</li>"

    new_content = content[:list_end] + new_items + "\n" + content[list_end:]
    return new_content, len(new_terms)

print("Fetching all published posts...")
posts = fetch_all_posts()
print(f"Found {len(posts)} posts\n")

no_glossary = []
thin_glossary = []

for post in posts:
    content = post["content"]["raw"]
    word_count = len(content.split())
    if word_count < 300:
        continue

    has_key_terms = "Key Terms" in content
    existing_count = len(re.findall(r'<strong>[^<]+</strong>\s*[—–-]', content))
    new_terms = find_matching_terms(content)

    if not has_key_terms and len(new_terms) >= 3:
        no_glossary.append({"post": post, "terms": new_terms[:6]})
    elif has_key_terms and existing_count < 4 and len(new_terms) >= 2:
        thin_glossary.append({"post": post, "terms": new_terms[:3], "existing": existing_count})

print(f"Posts without Key Terms needing them: {len(no_glossary)}")
print(f"Posts with thin Key Terms to expand: {len(thin_glossary)}\n")

results = []
updated_count = 0

for item in no_glossary[:20]:
    post = item["post"]
    pid = post["id"]
    title = post["title"]["raw"]
    content = post["content"]["raw"]
    terms = item["terms"]

    block = build_key_terms_block(terms)

    if TRUST_BLOCK_MARKER in content:
        last_idx = content.rfind(TRUST_BLOCK_MARKER)
        new_content = content[:last_idx] + f"\n{block}\n\n" + content[last_idx:]
    else:
        new_content = content + f"\n\n{block}"

    result = update_post(pid, new_content)
    if "id" in result:
        updated_count += 1
        results.append({
            "post_id": pid,
            "title": title[:60],
            "action": "new_block",
            "terms_added": len(terms),
            "term_names": ", ".join(t[0] for t in terms),
            "status": "updated"
        })
        print(f"  {pid}: NEW +{len(terms)} terms — {title[:50]}")
    else:
        results.append({
            "post_id": pid, "title": title[:60], "action": "new_block",
            "terms_added": 0, "term_names": "", "status": "error"
        })
    time.sleep(2)

for item in thin_glossary[:15]:
    post = item["post"]
    pid = post["id"]
    title = post["title"]["raw"]
    content = post["content"]["raw"]
    terms = item["terms"]

    new_content, added = expand_key_terms(content, terms)
    if added == 0:
        continue

    result = update_post(pid, new_content)
    if "id" in result:
        updated_count += 1
        results.append({
            "post_id": pid,
            "title": title[:60],
            "action": "expanded",
            "terms_added": added,
            "term_names": ", ".join(t[0] for t in terms),
            "status": "updated"
        })
        print(f"  {pid}: EXPANDED +{added} terms — {title[:50]}")
    else:
        results.append({
            "post_id": pid, "title": title[:60], "action": "expanded",
            "terms_added": 0, "term_names": "", "status": "error"
        })
    time.sleep(2)

csv_path = "/var/lib/freelancer/projects/40416335/phase10ac_data/Inline_Definition_Expansion.csv"
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["post_id", "title", "action", "terms_added", "term_names", "status"])
    w.writeheader()
    w.writerows(results)

total_terms = sum(r["terms_added"] for r in results)
print(f"\n=== INLINE DEFINITIONS: {updated_count} posts updated, {total_terms} terms added/expanded ===")
