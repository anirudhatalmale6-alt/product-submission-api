#!/usr/bin/env python3
"""
10AB-C: Comparison table expansion for Cat Supplies and Cat Toys clusters.
Also adds practical examples to weakest actionability posts.
"""

import subprocess, json, time, csv

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
TRUST_BLOCK_MARKER = '<!-- wp:separator {"className":"is-style-wide"} -->'

ADDITIONS = {
    4409: {
        "type": "comparison_table",
        "section": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Kitten vs Adult Cat Toy Requirements Compared</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Kittens and adult cats have different play needs. This table summarises the key differences to help you choose age-appropriate toys.</p>
<!-- /wp:paragraph -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>Factor</th><th>Kittens (under 12 months)</th><th>Adult Cats (1-7 years)</th><th>Senior Cats (7+ years)</th></tr></thead><tbody><tr><td>Play energy</td><td>Very high — frequent short bursts</td><td>Moderate — structured play sessions</td><td>Low — gentle, brief sessions</td></tr><tr><td>Preferred toy size</td><td>Small, lightweight, easy to bat</td><td>Medium, varied textures</td><td>Soft, easy to grasp</td></tr><tr><td>Supervision needed</td><td>High — risk of swallowing small parts</td><td>Moderate — depends on toy type</td><td>Moderate — watch for frustration</td></tr><tr><td>Play session length</td><td>5-10 minutes, multiple times daily</td><td>10-15 minutes, twice daily</td><td>5-10 minutes, once or twice daily</td></tr><tr><td>Best toy types</td><td>Feather wands, small balls, crinkle toys</td><td>Puzzle feeders, wand toys, kick toys</td><td>Gentle wand play, catnip toys, soft balls</td></tr></tbody></table></figure>
<!-- /wp:table -->"""
    },
    4415: {
        "type": "comparison_table",
        "section": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Cat Toy Safety: Material Risk Overview</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Different toy materials carry different safety considerations. This table helps you assess risk levels when choosing cat toys.</p>
<!-- /wp:paragraph -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>Material</th><th>Common Toys</th><th>Primary Risk</th><th>Supervision Needed</th></tr></thead><tbody><tr><td>Feathers</td><td>Wand toys, teasers</td><td>Ingestion if detached</td><td>Always supervised; store after use</td></tr><tr><td>String / ribbon</td><td>Wand attachments, dangling toys</td><td>Linear foreign body if swallowed</td><td>Always supervised; never leave accessible</td></tr><tr><td>Small bells</td><td>Ball toys, mice</td><td>Choking if detached</td><td>Check attachment regularly</td></tr><tr><td>Plush fabric</td><td>Stuffed mice, kick toys</td><td>Stuffing ingestion if torn</td><td>Replace when damaged</td></tr><tr><td>Hard plastic</td><td>Ball tracks, puzzle toys</td><td>Cracking with aggressive play</td><td>Inspect for cracks weekly</td></tr><tr><td>Cardboard</td><td>Scratchers, boxes</td><td>Low risk; minor ingestion usually passes</td><td>Minimal — generally safe</td></tr></tbody></table></figure>
<!-- /wp:table -->"""
    },
    4410: {
        "type": "comparison_table",
        "section": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Cat Enrichment Activities Compared</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Beyond toys, several enrichment approaches can improve your cat's quality of life. This table compares common options by effort, cost, and suitability.</p>
<!-- /wp:paragraph -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>Activity</th><th>Type of Stimulation</th><th>Setup Effort</th><th>Cost</th><th>Best For</th></tr></thead><tbody><tr><td>Window bird feeder</td><td>Visual</td><td>Low</td><td>Low</td><td>Indoor cats, elderly cats</td></tr><tr><td>Puzzle feeder</td><td>Mental + foraging</td><td>Low</td><td>Low to moderate</td><td>Food-motivated cats</td></tr><tr><td>Cat grass / herbs</td><td>Sensory (smell, taste)</td><td>Low</td><td>Low</td><td>All cats, especially indoor</td></tr><tr><td>Vertical climbing space</td><td>Physical + territory</td><td>Moderate</td><td>Moderate to high</td><td>Active cats, multi-cat homes</td></tr><tr><td>Rotating scent objects</td><td>Olfactory</td><td>Low</td><td>Low</td><td>Catnip-responsive cats</td></tr><tr><td>Supervised outdoor access (catio)</td><td>Multi-sensory</td><td>High</td><td>High</td><td>Cats wanting outdoor stimulation safely</td></tr></tbody></table></figure>
<!-- /wp:table -->"""
    },
    4407: {
        "type": "both",
        "section": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">DIY Cat Toy Safety Comparison</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Not all DIY materials are equally safe. This table helps you choose appropriate household items for homemade cat toys.</p>
<!-- /wp:paragraph -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>Material</th><th>Safe to Use?</th><th>Toy Ideas</th><th>Precautions</th></tr></thead><tbody><tr><td>Cardboard boxes</td><td>Yes</td><td>Hiding boxes, tunnels, treat puzzles</td><td>Remove tape and staples first</td></tr><tr><td>Paper bags (no handles)</td><td>Yes</td><td>Crinkle toys, hide-and-seek</td><td>Remove handles to prevent choking</td></tr><tr><td>Toilet roll tubes</td><td>Yes</td><td>Treat dispensers, batting toys</td><td>Discard when soggy or chewed</td></tr><tr><td>Fabric scraps</td><td>Caution</td><td>Tied knot toys, dragging toys</td><td>Avoid loose threads; supervise</td></tr><tr><td>Aluminium foil balls</td><td>Caution</td><td>Batting toys</td><td>Some cats chew and swallow; supervise</td></tr><tr><td>Rubber bands / hair ties</td><td>No</td><td>None recommended</td><td>Common foreign body in cats; avoid completely</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: Making a Cardboard Treat Puzzle</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>This takes under 5 minutes and uses only a cardboard box and your cat's regular kibble.</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol>
<li><strong>Take a small cardboard box</strong> (a tissue box or small delivery box works well). Remove any tape, staples, or plastic.</li>
<li><strong>Cut 3-4 holes</strong> in the sides, each roughly 4 cm in diameter — large enough for a paw but small enough to require effort.</li>
<li><strong>Drop 10-15 pieces of kibble inside</strong> and close the top loosely. Your cat must reach through the holes to extract the food.</li>
<li><strong>Observe the first session:</strong> Most cats figure out the puzzle within 5-10 minutes. If your cat loses interest quickly, make the holes slightly larger or shake the box to remind them food is inside.</li>
<li><strong>Increase difficulty over time:</strong> Use a deeper box, smaller holes, or wrap kibble in small paper balls inside the box.</li>
</ol>
<!-- /wp:list -->"""
    },
    5032: {
        "type": "practical",
        "section": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: Choosing a Toy Based on Your Cat's Play Style</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Cats have distinct play preferences. Observe your cat for a few days and match them to one of these common play styles.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>The Stalker:</strong> Your cat crouches, wiggles their rear, and pounces. Best toys: wand toys with feather or fabric attachments that mimic prey movement. Drag the toy slowly across the floor, then let it "hide" behind furniture.</li>
<li><strong>The Batter:</strong> Your cat swats at objects with their paws. Best toys: lightweight balls, crinkle balls, or small mice that skitter across hard floors. Place these on a tile or wood floor for maximum sliding distance.</li>
<li><strong>The Wrestler:</strong> Your cat grabs toys with all four paws and bunny-kicks. Best toys: kick toys (long, narrow stuffed toys) filled with catnip. Look for toys roughly the length of your cat's body.</li>
<li><strong>The Thinker:</strong> Your cat investigates objects carefully. Best toys: puzzle feeders, treat balls, or DIY foraging puzzles. Start with easy puzzles and increase complexity as your cat learns.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Measurable check:</strong> A well-matched toy holds your cat's attention for at least 5 minutes of active play. If your cat loses interest within 1-2 minutes, try a different play style category.</p>
<!-- /wp:paragraph -->"""
    },
    5036: {
        "type": "both",
        "section": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Cat Play Styles Compared</h3>
<!-- /wp:heading -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>Play Style</th><th>Behaviour Signs</th><th>Best Toy Types</th><th>Session Length</th></tr></thead><tbody><tr><td>Chase / stalk</td><td>Crouching, tail twitching, rear wiggle before pounce</td><td>Wand toys, laser pointers (end with physical toy)</td><td>10-15 minutes</td></tr><tr><td>Bat / swat</td><td>Quick paw strikes, batting objects across floor</td><td>Small balls, crinkle balls, spring toys</td><td>5-10 minutes</td></tr><tr><td>Wrestle / kick</td><td>Grabbing with front paws, bunny kicking</td><td>Kick toys, large stuffed mice</td><td>5-10 minutes</td></tr><tr><td>Problem-solve</td><td>Careful investigation, persistent manipulation</td><td>Puzzle feeders, treat dispensers</td><td>10-20 minutes</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: Identifying Your Cat's Dominant Play Style</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Spend 3 days observing your cat during play to identify their dominant style.</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol>
<li><strong>Day 1 — Offer a wand toy:</strong> Drag it slowly across the floor. Does your cat stalk and pounce, or bat at it with a paw? Note which behaviour dominates.</li>
<li><strong>Day 2 — Offer a small ball:</strong> Roll it across a hard floor. Does your cat chase it enthusiastically, or watch it with mild interest?</li>
<li><strong>Day 3 — Offer a treat puzzle:</strong> Place kibble in a toilet roll tube with one end folded. Does your cat engage persistently, or lose interest quickly?</li>
<li><strong>Assess:</strong> The toy type that produced the longest, most engaged play session indicates your cat's dominant play style. Most cats have a primary and secondary preference.</li>
</ol>
<!-- /wp:list -->"""
    },
    5033: {
        "type": "practical",
        "section": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: A Three-Step Toy Selection Process</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Use this process when buying a new toy for your cat. It takes less than a minute and significantly improves the chances of choosing a toy your cat will actually use.</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol>
<li><strong>Match the play style:</strong> Is your cat primarily a chaser, batter, wrestler, or thinker? Choose a toy designed for that style (see our play behaviour guide for identification help).</li>
<li><strong>Check the size:</strong> The toy should be small enough for your cat to carry or bat, but large enough that no piece can be swallowed. As a rough guide, avoid anything smaller than a ping-pong ball for adult cats.</li>
<li><strong>Assess the material:</strong> Avoid loose string, detachable small parts, or strong chemical odours. Give the toy a firm pull to test whether any components come loose easily.</li>
</ol>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Measurable check:</strong> A well-chosen toy should engage your cat within the first 5 minutes of introduction. If your cat completely ignores a new toy, try rubbing it with catnip or attaching it to a wand for interactive play before concluding it is not suitable.</p>
<!-- /wp:paragraph -->"""
    },
    5035: {
        "type": "comparison_table",
        "section": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Home Enrichment Options Compared</h3>
<!-- /wp:heading -->

<!-- wp:table -->
<figure class="wp-block-table"><table><thead><tr><th>Enrichment Type</th><th>Examples</th><th>Setup Cost</th><th>Maintenance</th><th>Indoor Cat Suitability</th></tr></thead><tbody><tr><td>Vertical space</td><td>Cat shelves, tall cat trees, window perches</td><td>Moderate to high</td><td>Low</td><td>Excellent — essential for territory</td></tr><tr><td>Hiding spots</td><td>Cardboard boxes, tunnels, cat caves</td><td>Free to low</td><td>Replace as needed</td><td>Excellent — reduces stress</td></tr><tr><td>Foraging opportunities</td><td>Puzzle feeders, scatter feeding, treat hunts</td><td>Low</td><td>Daily setup</td><td>Excellent — mimics natural behaviour</td></tr><tr><td>Visual stimulation</td><td>Bird feeders at windows, fish videos</td><td>Low</td><td>Low</td><td>Good — passive engagement</td></tr><tr><td>Scent enrichment</td><td>Catnip, silver vine, valerian, outdoor scents</td><td>Low</td><td>Weekly rotation</td><td>Good — 60-70% of cats respond to catnip</td></tr></tbody></table></figure>
<!-- /wp:table -->"""
    },
}

def fetch_post(post_id):
    cmd = ["curl", "-s", "--compressed", "-u", AUTH,
           f"{WP_URL}/posts/{post_id}?context=edit"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

def update_post(post_id, content):
    cmd = ["curl", "-s", "--compressed", "-u", AUTH,
           "-X", "POST", f"{WP_URL}/posts/{post_id}",
           "-H", "Content-Type: application/json",
           "-d", json.dumps({"content": content})]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

results = []
for post_id, data in ADDITIONS.items():
    print(f"\n--- {post_id}: {data['type']} ---")
    try:
        post = fetch_post(post_id)
        if "id" not in post:
            print(f"  ERROR fetching")
            results.append({"post_id": post_id, "type": data["type"], "status": "fetch_error"})
            time.sleep(3)
            continue

        content = post["content"]["raw"]
        if TRUST_BLOCK_MARKER in content:
            last_idx = content.rfind(TRUST_BLOCK_MARKER)
            new_content = content[:last_idx] + f"\n{data['section']}\n\n" + content[last_idx:]
        else:
            new_content = content + f"\n\n{data['section']}"

        updated = update_post(post_id, new_content)
        if "id" in updated:
            print(f"  SUCCESS: {post['title']['raw'][:50]}")
            results.append({"post_id": post_id, "title": post["title"]["raw"], "type": data["type"], "status": "updated"})
        else:
            print(f"  ERROR: {str(updated)[:150]}")
            results.append({"post_id": post_id, "type": data["type"], "status": "update_error"})
        time.sleep(3)
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        results.append({"post_id": post_id, "type": data["type"], "status": f"error: {e}"})
        time.sleep(3)

csv_path = "/var/lib/freelancer/projects/40416335/phase10ab_data/Cat_Comparison_Expansion.csv"
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["post_id", "title", "type", "status"])
    w.writeheader()
    w.writerows(results)

success = sum(1 for r in results if r.get("status") == "updated")
print(f"\n=== COMPLETE: {success}/{len(results)} posts updated ===")
