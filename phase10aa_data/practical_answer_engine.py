#!/usr/bin/env python3
"""
Practical Answer Expansion Engine
Adds practical examples, step-by-step guidance, and measurable tips to
educational posts with low actionability scores.
"""

import subprocess, json, time, csv

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

TRUST_BLOCK_MARKER = '<!-- wp:separator {"className":"is-style-wide"} -->'

PRACTICAL_ADDITIONS = {
    5471: {
        "title": "Dog Boredom Prevention",
        "section_title": "Practical Example: A Daily Anti-Boredom Routine",
        "content": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: A Daily Anti-Boredom Routine</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Here is a sample daily enrichment schedule for a medium-energy adult dog. Adjust the timings and activities to match your dog's breed, age, and preferences.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Morning (before you leave):</strong> 10-minute scatter feed in the garden or a snuffle mat session. This uses the dog's natural foraging instinct and provides calm mental work.</li>
<li><strong>Mid-morning:</strong> Leave a frozen Kong or lick mat with a smear of dog-safe peanut butter. This occupies the dog for 20–40 minutes during a typically quiet period.</li>
<li><strong>Afternoon:</strong> If possible, a 5-minute training session with 3–4 known commands. Keep sessions short to maintain engagement.</li>
<li><strong>Evening:</strong> 15-minute interactive play (tug, fetch, or a puzzle toy). End with a calm chew toy to help the dog wind down before settling for the night.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Measurable check:</strong> A well-enriched dog typically settles within 10–15 minutes of the last activity. If your dog remains restless, paces, or chews household items, consider adding one more enrichment session or increasing walk duration by 10 minutes.</p>
<!-- /wp:paragraph -->"""
    },
    5469: {
        "title": "Dog Toy Rotation",
        "section_title": "Practical Example: Setting Up a Weekly Rotation",
        "content": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: Setting Up a Weekly Rotation</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Follow these steps to set up a simple toy rotation system that keeps your dog interested without requiring daily effort.</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol>
<li><strong>Gather all toys</strong> — Collect every toy your dog currently has. Discard any that are damaged, have missing squeakers, or show exposed stuffing.</li>
<li><strong>Sort into 3–4 groups</strong> — Each group should include one chew toy, one interactive toy, and one comfort toy. Aim for 3–5 toys per group.</li>
<li><strong>Store unused groups</strong> — Place each group in a sealed bag or box. Store out of sight and out of reach. The key is that your dog cannot see or smell these toys.</li>
<li><strong>Swap weekly</strong> — Every Sunday (or whichever day suits your routine), swap the current group for the next one. Return the old group to storage.</li>
<li><strong>Observe reactions</strong> — Note which toys get the most attention each week. Toys that are consistently ignored can be retired or donated.</li>
</ol>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Measurable check:</strong> Most dogs show renewed interest in rotated toys within 2–3 minutes of reintroduction. If your dog ignores a toy after rotation, it may have lost appeal permanently — replace it with something new.</p>
<!-- /wp:paragraph -->"""
    },
    5483: {
        "title": "Dog Toy Lifespan",
        "section_title": "Practical Example: Monthly Toy Inspection Checklist",
        "content": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: Monthly Toy Inspection Checklist</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Set a monthly reminder to inspect all of your dog's toys. Use this checklist to decide what to keep, repair, or replace.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Check for tears or holes:</strong> Run your fingers over the surface. If stuffing is visible or the toy has a tear larger than 1 cm, discard it.</li>
<li><strong>Test squeakers:</strong> Press each squeaker. If it no longer works or sounds muffled, the squeaker may be loose inside — a swallowing hazard.</li>
<li><strong>Inspect rope toys:</strong> Pull gently on the fibres. If strands come away easily or the rope has thinned noticeably, replace it to avoid intestinal blockage from ingested fibres.</li>
<li><strong>Check rubber toys:</strong> Look for deep bite marks, cracks, or chunks missing. Small pieces of rubber can cause choking or digestive issues.</li>
<li><strong>Smell test:</strong> Toys that smell sour or mouldy even after cleaning should be replaced. Bacteria can build up in textured surfaces.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Typical lifespans:</strong> Plush toys last 1–4 weeks for heavy chewers, 2–6 months for gentle dogs. Rubber toys typically last 3–12 months depending on chewing intensity. Rope toys average 1–3 months of regular use.</p>
<!-- /wp:paragraph -->"""
    },
    5424: {
        "title": "Aggressive Chewer Guide",
        "section_title": "Practical Example: Testing a New Toy for a Power Chewer",
        "content": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: Testing a New Toy for a Power Chewer</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Before leaving a new toy unsupervised with a heavy chewer, follow this graduated introduction process.</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol>
<li><strong>Supervised introduction (15 minutes):</strong> Give the toy while you are present. Watch how your dog engages — gentle mouthing, moderate chewing, or immediate destructive biting.</li>
<li><strong>Check after first session:</strong> Inspect the toy for bite marks, deformation, or material loss. If the toy shows significant damage after 15 minutes, it is not suitable for unsupervised use.</li>
<li><strong>Extended supervised use (1 hour):</strong> If the toy survived the first test, allow a longer session. Check again for structural integrity.</li>
<li><strong>Short unsupervised trial (30 minutes):</strong> Leave the toy with your dog while you are in another room. Return and inspect.</li>
<li><strong>Full clearance:</strong> If the toy passes all stages with no concerning damage, it can be left for regular unsupervised play.</li>
</ol>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Warning signs to stop immediately:</strong> chunks breaking off, exposed interior layers, squeaker becoming accessible, or any deformation that creates sharp edges. When in doubt, remove the toy.</p>
<!-- /wp:paragraph -->"""
    },
    5423: {
        "title": "Dog Toy Enrichment Beyond Fetch",
        "section_title": "Practical Example: Three Enrichment Activities Beyond Fetch",
        "content": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: Three Enrichment Activities Beyond Fetch</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>These activities require minimal equipment and can be set up in under 5 minutes. Each targets a different type of mental engagement.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>1. The Muffin Tin Game (scent work, 10 minutes):</strong> Place treats in 3–4 cups of a muffin tin. Cover all cups with tennis balls. Your dog must use their nose to find which cups contain treats and figure out how to remove the balls. Increase difficulty by using fewer treats across more cups.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>2. The Towel Roll (problem-solving, 5–15 minutes):</strong> Lay out a hand towel flat. Place a line of small treats along one edge. Roll the towel up with the treats inside. Your dog unrolls it to access the food. For advanced dogs, use a bath towel and scatter treats throughout.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>3. The Find-It Trail (nose work, 10–20 minutes):</strong> While your dog waits in another room, place 8–10 treats in a trail around your house — under a chair leg, behind a door, on a low shelf. Release your dog with the cue "find it." Start with easy, visible placements and progress to hidden ones as your dog improves.</p>
<!-- /wp:paragraph -->"""
    },
    5473: {
        "title": "Senior Dog Toys",
        "section_title": "Practical Example: Adapting Play for an Ageing Dog",
        "content": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: Adapting Play for an Ageing Dog</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>As dogs age, their play needs change. Here is how to adjust enrichment for a typical senior dog (roughly 8+ years for large breeds, 10+ for small breeds).</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Reduce session length:</strong> Shorten play sessions from 15–20 minutes to 5–10 minutes. Watch for signs of fatigue — heavy panting, lying down mid-play, or loss of interest.</li>
<li><strong>Lower the physical demands:</strong> Replace high-impact fetch with gentle tug (held low), slow-roll treat balls, or scent-based games where the dog walks rather than runs.</li>
<li><strong>Choose softer materials:</strong> Senior dogs often have weaker teeth and sore gums. Switch from hard rubber and nylon to softer rubber, plush toys, or fabric-based puzzle toys.</li>
<li><strong>Prioritise mental over physical:</strong> A 10-minute snuffle mat session can tire a senior dog as effectively as a 20-minute walk, without the joint stress.</li>
<li><strong>Keep toys accessible:</strong> Place toys at ground level. Avoid toys that require jumping, climbing, or sustained standing.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Measurable check:</strong> A good enrichment session for a senior dog ends with the dog settling calmly within 5 minutes. If your dog seems agitated or in discomfort after play, reduce intensity further and consult your vet if pain persists.</p>
<!-- /wp:paragraph -->"""
    },
    5035: {
        "title": "Cat Enrichment Beyond Toys",
        "section_title": "Practical Example: Enriching Your Cat's Environment in Three Steps",
        "content": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: Enriching Your Cat's Environment in Three Steps</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>You do not need to buy specialist equipment to enrich your cat's home. These three changes can be made with items you likely already have.</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol>
<li><strong>Create vertical space:</strong> Clear a shelf at window height (ideally 90–120 cm from the floor) and place a folded towel on it. Most cats will begin using this as a perch within 1–2 days. Position it near a window for visual stimulation from outdoor activity.</li>
<li><strong>Add a foraging station:</strong> Place a portion of your cat's daily kibble inside a cardboard egg box with the lid partially closed. This forces the cat to use their paws to extract food, extending mealtime from 2 minutes to 10–15 minutes and providing mental engagement.</li>
<li><strong>Rotate scent stimulation:</strong> Once a week, place a small amount of dried catnip, silver vine, or valerian root on a cloth and leave it in a different room. Roughly 60–70% of cats respond to catnip; if yours does not, try silver vine as an alternative.</li>
</ol>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Signs of success:</strong> An enriched cat spends more time exploring, less time sleeping during active hours, and shows fewer stress behaviours such as over-grooming or excessive vocalisation.</p>
<!-- /wp:paragraph -->"""
    },
    5034: {
        "title": "Cat Toy Rotation",
        "section_title": "Practical Example: A Simple Cat Toy Rotation Plan",
        "content": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: A Simple Cat Toy Rotation Plan</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Cats lose interest in toys faster than dogs. A structured rotation plan helps maintain engagement without buying new toys constantly.</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol>
<li><strong>Select 3–4 toys to leave out:</strong> Include one wand or feather toy (for interactive play), one small ball or mouse (for solo batting), and one catnip toy. This covers different play styles.</li>
<li><strong>Store the rest out of sight:</strong> Place remaining toys in a sealed container. Unlike dogs, cats are especially sensitive to novelty — a toy that has been hidden for even 3–5 days can feel new again.</li>
<li><strong>Rotate every 3–5 days:</strong> Cats typically lose peak interest in a toy after 2–3 days. Swapping on a 3–5 day cycle maintains the novelty response.</li>
<li><strong>Always have one interactive toy available:</strong> Wand toys should be stored after supervised play (string is a swallowing hazard), but at least one solo-safe toy should always be accessible.</li>
</ol>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Measurable check:</strong> A cat engaging with a newly rotated toy will typically investigate it within 5 minutes of reintroduction. If a toy consistently gets no attention after rotation, it has lost its appeal — retire it.</p>
<!-- /wp:paragraph -->"""
    },
    5420: {
        "title": "Dog Toy Cleaning Guide",
        "section_title": "Practical Example: Weekly Toy Cleaning Routine",
        "content": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: Weekly Toy Cleaning Routine</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Set aside 15 minutes each week to clean your dog's toys. Here is a straightforward routine that covers the main toy types.</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol>
<li><strong>Gather all active toys:</strong> Collect every toy your dog has used that week. This is also a good time to inspect for damage (see our replacement guide).</li>
<li><strong>Sort by material:</strong> Separate rubber, plush, rope, and any natural material toys. Each needs a different approach.</li>
<li><strong>Rubber toys:</strong> Place in the top rack of your dishwasher without detergent, or hand-wash in warm water with a small amount of dog-safe dish soap. Rinse thoroughly — soap residue can cause stomach upset.</li>
<li><strong>Plush toys:</strong> Machine wash on a gentle cycle at 30°C in a mesh laundry bag. Air dry completely before returning — damp plush toys can harbour mould within 24 hours.</li>
<li><strong>Rope toys:</strong> Machine wash on gentle. Ensure they dry fully — rope retains moisture and can develop bacteria if stored damp. In warm weather, drying outdoors in sunlight adds natural disinfection.</li>
</ol>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>How often is enough?</strong> Weekly cleaning suits most households. If your dog takes toys outdoors, slobbers heavily, or shares toys with other dogs, clean every 3–4 days.</p>
<!-- /wp:paragraph -->"""
    },
    5458: {
        "title": "Cat Scratching Behaviour",
        "section_title": "Practical Example: Redirecting Scratching from Furniture",
        "content": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: Redirecting Scratching from Furniture</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>If your cat scratches furniture, these steps can help redirect the behaviour to an appropriate surface. This process typically takes 1–3 weeks of consistent effort.</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol>
<li><strong>Observe the current target:</strong> Note where and how your cat scratches. Vertical (sofa arm) or horizontal (carpet edge)? This tells you which scratcher orientation to provide.</li>
<li><strong>Place a scratcher next to the target:</strong> Put an appropriate scratching post or pad directly beside the furniture being scratched. Match the orientation — vertical post for vertical scratching, flat pad for horizontal.</li>
<li><strong>Make the scratcher attractive:</strong> Sprinkle a small amount of catnip on the surface, or dangle a toy near it to draw attention. Most cats will investigate within a few hours.</li>
<li><strong>Make the furniture less attractive:</strong> Temporarily cover the scratched area with double-sided tape or aluminium foil. Cats dislike the texture and will seek the nearby scratcher instead.</li>
<li><strong>Reward use:</strong> When your cat uses the scratcher, offer a treat or gentle praise within 3 seconds. Timing matters — delayed rewards do not create the association.</li>
<li><strong>Gradually move the scratcher:</strong> Once your cat uses the scratcher consistently (usually 1–2 weeks), move it 10–15 cm per day toward your preferred location.</li>
</ol>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Important:</strong> Never punish scratching — it is a natural and necessary behaviour. Punishment increases stress and often worsens the problem.</p>
<!-- /wp:paragraph -->"""
    },
    4566: {
        "title": "Seasonal Dog Care",
        "section_title": "Practical Example: Summer Walk Safety Check",
        "content": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: Summer Walk Safety Check</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Heatstroke is one of the most common preventable emergencies in dogs during summer. Use this quick check before every warm-weather walk.</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>The pavement test:</strong> Place the back of your hand flat on the pavement for 7 seconds. If it is too hot for your hand, it is too hot for your dog's paws. At 25°C air temperature, tarmac can reach 52°C.</li>
<li><strong>Time your walk:</strong> Walk before 8am or after 7pm during summer months. Midday sun (11am–3pm) poses the highest risk, even on cloudy days.</li>
<li><strong>Carry water:</strong> Bring a collapsible bowl and fresh water. Offer water every 10–15 minutes during warm walks. A dog weighing 20 kg needs roughly 40–60 ml of water per kilogram per day — more during exercise.</li>
<li><strong>Watch for early signs:</strong> Heavy panting, bright red tongue, drooling more than usual, or slowing down are early warning signs. Stop walking, find shade, and offer water immediately.</li>
<li><strong>Flat-faced breeds:</strong> Brachycephalic breeds (Bulldogs, Pugs, French Bulldogs) are at significantly higher risk. Keep walks under 15 minutes in warm weather and avoid any exercise above 20°C for these breeds.</li>
</ul>
<!-- /wp:list -->"""
    },
    5512: {
        "title": "Dog Behaviour Explained",
        "section_title": "Practical Example: Reading Your Dog's Body Language",
        "content": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Practical Example: Reading Your Dog's Body Language in Common Situations</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Understanding body language helps you respond appropriately. Here are three common scenarios and what to look for.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>Scenario 1 — Meeting a new dog on a walk:</strong> A relaxed dog shows a loose, wagging tail (at mid-height, not stiff), soft eyes, and a play bow (front end down, rear up). A stressed dog shows a stiff body, tail tucked or held high and rigid, lip licking, or turning the head away. If you see stress signals, calmly increase distance — do not force the greeting.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>Scenario 2 — Your dog yawns repeatedly indoors:</strong> Occasional yawning is normal. Repeated yawning when the dog is not tired is often a calming signal — it can indicate stress, discomfort, or overstimulation. Check the environment: is there a loud noise, an unfamiliar visitor, or another pet nearby? Remove or reduce the stressor.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>Scenario 3 — Whale eye (showing the whites):</strong> If your dog turns their head away but keeps their eyes fixed on something, exposing the white sclera, they are uncomfortable and may be guarding a resource or feeling trapped. Give them space immediately. Do not reach toward them or remove whatever they are guarding without professional guidance.</p>
<!-- /wp:paragraph -->"""
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

for post_id, addition in PRACTICAL_ADDITIONS.items():
    print(f"\n--- Processing {post_id}: {addition['title']} ---")
    try:
        post = fetch_post(post_id)
        if "id" not in post:
            print(f"  ERROR: Could not fetch post {post_id}")
            results.append({"post_id": post_id, "title": addition["title"], "status": "fetch_error"})
            time.sleep(3)
            continue

        content = post["content"]["raw"]

        # Insert before trust editorial block
        if TRUST_BLOCK_MARKER in content:
            last_idx = content.rfind(TRUST_BLOCK_MARKER)
            if last_idx > 0:
                new_content = content[:last_idx] + f"\n{addition['content']}\n\n" + content[last_idx:]
                print(f"  Inserted before trust block")
            else:
                new_content = content + f"\n\n{addition['content']}"
                print(f"  Appended to end")
        else:
            new_content = content + f"\n\n{addition['content']}"
            print(f"  Appended to end (no trust block)")

        updated = update_post(post_id, new_content)
        if "id" in updated:
            print(f"  SUCCESS: Updated post {post_id}")
            results.append({
                "post_id": post_id,
                "title": post["title"]["raw"],
                "section_added": addition["section_title"],
                "status": "updated"
            })
        else:
            print(f"  ERROR: {str(updated)[:200]}")
            results.append({"post_id": post_id, "title": addition["title"], "status": "update_error"})

        time.sleep(3)
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        results.append({"post_id": post_id, "title": addition["title"], "status": f"error: {e}"})
        time.sleep(3)

csv_path = "/var/lib/freelancer/projects/40416335/phase10aa_data/Practical_Answer_Expansion.csv"
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["post_id", "title", "section_added", "status"])
    w.writeheader()
    w.writerows(results)

success = sum(1 for r in results if r.get("status") == "updated")
print(f"\n=== COMPLETE: {success}/{len(results)} posts updated with practical examples ===")
print(f"CSV saved to: {csv_path}")
