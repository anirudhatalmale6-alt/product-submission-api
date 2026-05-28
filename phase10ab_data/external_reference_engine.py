#!/usr/bin/env python3
"""
10AB-D (part): External Reference Layer
Adds truthful external references (FEDIAF, BVA, RSPCA, Battersea, Cats Protection)
to posts where they naturally fit, boosting trust and citation readiness.
"""

import subprocess, json, time, csv, re

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"

TRUST_BLOCK_MARKER = '<!-- wp:separator {"className":"is-style-wide"} -->'

REFERENCE_ADDITIONS = {
    5508: {
        "title": "Puppy Development Stages",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Authoritative Sources on Puppy Development</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The developmental milestones described in this guide are consistent with guidance from established animal welfare organisations. The <a href="https://www.rspca.org.uk/" target="_blank" rel="noopener">RSPCA</a> recommends that puppies remain with their mother until at least 8 weeks of age, which aligns with the critical socialisation period discussed above. The <a href="https://www.bva.co.uk/" target="_blank" rel="noopener">British Veterinary Association (BVA)</a> advises that early socialisation and positive exposure to a range of environments, people, and other animals is essential for long-term behavioural health. For breed-specific developmental guidance, <a href="https://www.battersea.org.uk/" target="_blank" rel="noopener">Battersea</a> provides practical puppy care resources that complement the general timeline in this guide.</p>
<!-- /wp:paragraph -->"""
    },
    5520: {
        "title": "Dog Health Basics",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Veterinary and Welfare Sources</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The health information in this guide is informed by publicly available guidance from UK veterinary and animal welfare bodies. The <a href="https://www.bva.co.uk/" target="_blank" rel="noopener">British Veterinary Association (BVA)</a> provides guidance on preventive health care, vaccination schedules, and recognising signs of illness. The <a href="https://www.rspca.org.uk/" target="_blank" rel="noopener">RSPCA</a> publishes advice on common dog health conditions and when to seek veterinary attention. This guide does not replace professional veterinary advice — if your dog shows signs of illness or injury, contact your vet directly.</p>
<!-- /wp:paragraph -->"""
    },
    5519: {
        "title": "Indoor Cat Care",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Welfare Guidance for Indoor Cats</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Keeping cats indoors is a growing practice in the UK, and welfare organisations provide guidance on making indoor environments suitable. <a href="https://www.cats.org.uk/" target="_blank" rel="noopener">Cats Protection</a> recommends that indoor cats have access to vertical climbing space, scratching surfaces, and environmental enrichment to maintain physical and mental health. The <a href="https://www.rspca.org.uk/" target="_blank" rel="noopener">RSPCA</a> advises that indoor cats need regular interactive play sessions and environmental variety to prevent boredom-related behavioural issues.</p>
<!-- /wp:paragraph -->"""
    },
    5467: {
        "title": "Pet Feeding Guide",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Nutritional Guidance Sources</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Feeding guidelines in this guide are informed by established nutritional standards. <a href="https://fediaf.org/" target="_blank" rel="noopener">FEDIAF</a> (the European Pet Food Industry Federation) publishes nutritional guidelines that underpin pet food formulation across Europe. The <a href="https://www.bva.co.uk/" target="_blank" rel="noopener">BVA</a> advises that portion sizes should be adjusted based on your pet's age, weight, activity level, and health status. If you are unsure about your pet's dietary needs, consult your veterinarian for personalised feeding advice.</p>
<!-- /wp:paragraph -->"""
    },
    5509: {
        "title": "Pet Toy Safety",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Safety Standards and Regulatory Sources</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Pet toy safety in the UK falls under general product safety regulations. The <a href="https://www.gov.uk/government/organisations/office-for-product-safety-and-standards" target="_blank" rel="noopener">Office for Product Safety and Standards</a> oversees product safety enforcement, including pet products. The <a href="https://www.rspca.org.uk/" target="_blank" rel="noopener">RSPCA</a> advises that toys should be appropriate for your pet's size and chewing strength, and that damaged toys should be replaced promptly to avoid choking or ingestion hazards. There is currently no specific British Standard for pet toys, which makes owner vigilance particularly important.</p>
<!-- /wp:paragraph -->"""
    },
    5522: {
        "title": "Orthopaedic Care for Dogs",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Veterinary Sources on Joint Health</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The joint health guidance in this article is consistent with advice from UK veterinary bodies. The <a href="https://www.bva.co.uk/" target="_blank" rel="noopener">British Veterinary Association</a> recommends that dogs showing signs of joint stiffness, lameness, or reluctance to exercise should be examined by a veterinarian, as early intervention can significantly improve outcomes. The BVA/Kennel Club hip and elbow screening schemes help identify predisposition to joint conditions in breeding dogs. This guide does not replace veterinary diagnosis or treatment.</p>
<!-- /wp:paragraph -->"""
    },
    5510: {
        "title": "Dog Bed Sizing Guide",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Welfare Guidance on Resting Areas</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Providing a suitable resting area is part of responsible dog ownership. The <a href="https://www.rspca.org.uk/" target="_blank" rel="noopener">RSPCA</a> includes comfortable bedding in a quiet, draught-free area as one of the basic welfare needs for dogs under the Animal Welfare Act 2006. <a href="https://www.battersea.org.uk/" target="_blank" rel="noopener">Battersea</a> advises that dogs should have a bed large enough to stretch out fully and in a location where they feel safe and settled.</p>
<!-- /wp:paragraph -->"""
    },
    4792: {
        "title": "Puppy Socialisation",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Socialisation Guidance from Welfare Organisations</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The socialisation timeline in this guide aligns with recommendations from major UK animal welfare organisations. The <a href="https://www.rspca.org.uk/" target="_blank" rel="noopener">RSPCA</a> emphasises that the critical socialisation period (approximately 3 to 14 weeks) is when puppies are most receptive to new experiences, and that positive early exposure helps prevent fear-based behaviour problems in adult dogs. The <a href="https://www.bva.co.uk/" target="_blank" rel="noopener">BVA</a> recommends starting socialisation before the vaccination course is complete, using safe environments and controlled introductions.</p>
<!-- /wp:paragraph -->"""
    },
    5460: {
        "title": "Pet Nutrition Terminology",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Nutritional Standards and Labelling Sources</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The nutritional terminology in this guide is informed by <a href="https://fediaf.org/" target="_blank" rel="noopener">FEDIAF</a> guidelines, which set the nutritional standards used by pet food manufacturers across Europe. UK pet food labelling is governed by the <a href="https://www.gov.uk/government/organisations/animal-and-plant-health-agency" target="_blank" rel="noopener">Animal and Plant Health Agency (APHA)</a> and must comply with feed marketing regulations. Understanding these terms helps you evaluate pet food labels more effectively.</p>
<!-- /wp:paragraph -->"""
    },
    5458: {
        "title": "Cat Scratching Behaviour",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Welfare Guidance on Scratching Behaviour</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><a href="https://www.cats.org.uk/" target="_blank" rel="noopener">Cats Protection</a> identifies scratching as a natural and essential behaviour that serves multiple functions: claw maintenance, territory marking, and stretching. They advise that declawing is illegal in the UK and that providing appropriate scratching surfaces is a welfare responsibility. The <a href="https://www.rspca.org.uk/" target="_blank" rel="noopener">RSPCA</a> recommends offering both vertical and horizontal scratching options to accommodate individual cat preferences.</p>
<!-- /wp:paragraph -->"""
    },
    5511: {
        "title": "Pet Enrichment Explained",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Welfare Perspective on Enrichment</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Environmental enrichment is recognised by UK welfare organisations as essential for pet wellbeing. The <a href="https://www.rspca.org.uk/" target="_blank" rel="noopener">RSPCA</a> includes mental stimulation as part of the five welfare needs under the Animal Welfare Act 2006. <a href="https://www.battersea.org.uk/" target="_blank" rel="noopener">Battersea</a> provides practical enrichment guides for both dogs and cats, emphasising that enrichment should be tailored to the individual animal's age, health, and preferences.</p>
<!-- /wp:paragraph -->"""
    },
    4568: {
        "title": "Dog Dental Health",
        "block": """<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">Veterinary Guidance on Dental Health</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The <a href="https://www.bva.co.uk/" target="_blank" rel="noopener">British Veterinary Association</a> reports that dental disease is one of the most common conditions seen in veterinary practice, affecting a significant proportion of dogs over the age of three. Regular dental checks, appropriate chew toys, and professional cleaning when recommended by your vet are all part of preventive dental care. The <a href="https://www.rspca.org.uk/" target="_blank" rel="noopener">RSPCA</a> advises that signs such as bad breath, difficulty eating, or drooling may indicate dental problems requiring veterinary attention.</p>
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

for post_id, ref_data in REFERENCE_ADDITIONS.items():
    print(f"\n--- Processing {post_id}: {ref_data['title']} ---")
    try:
        post = fetch_post(post_id)
        if "id" not in post:
            print(f"  ERROR: Could not fetch")
            results.append({"post_id": post_id, "title": ref_data["title"], "refs_added": "", "status": "fetch_error"})
            time.sleep(3)
            continue

        content = post["content"]["raw"]

        # Check if already has external references section
        if "Authoritative Sources" in content or "Welfare Sources" in content or "Veterinary Sources" in content or "Regulatory Sources" in content or "Nutritional Standards" in content or "Welfare Guidance on" in content or "Welfare Perspective" in content:
            print(f"  SKIP: Already has external reference section")
            results.append({"post_id": post_id, "title": post["title"]["raw"], "refs_added": "already_present", "status": "skipped"})
            time.sleep(1)
            continue

        if TRUST_BLOCK_MARKER in content:
            last_idx = content.rfind(TRUST_BLOCK_MARKER)
            new_content = content[:last_idx] + f"\n{ref_data['block']}\n\n" + content[last_idx:]
        else:
            new_content = content + f"\n\n{ref_data['block']}"

        # Count which orgs referenced
        orgs = []
        if "rspca.org" in ref_data["block"]: orgs.append("RSPCA")
        if "bva.co.uk" in ref_data["block"]: orgs.append("BVA")
        if "fediaf.org" in ref_data["block"]: orgs.append("FEDIAF")
        if "battersea.org" in ref_data["block"]: orgs.append("Battersea")
        if "cats.org.uk" in ref_data["block"]: orgs.append("Cats Protection")
        if "gov.uk" in ref_data["block"]: orgs.append("UK Gov")

        updated = update_post(post_id, new_content)
        if "id" in updated:
            print(f"  SUCCESS: Added refs to {', '.join(orgs)}")
            results.append({
                "post_id": post_id,
                "title": post["title"]["raw"],
                "refs_added": ", ".join(orgs),
                "status": "updated"
            })
        else:
            print(f"  ERROR: {str(updated)[:200]}")
            results.append({"post_id": post_id, "title": ref_data["title"], "refs_added": "", "status": "update_error"})

        time.sleep(3)
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        results.append({"post_id": post_id, "title": ref_data["title"], "refs_added": "", "status": f"error: {e}"})
        time.sleep(3)

csv_path = "/var/lib/freelancer/projects/40416335/phase10ab_data/External_Reference_Layer.csv"
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["post_id", "title", "refs_added", "status"])
    w.writeheader()
    w.writerows(results)

success = sum(1 for r in results if r.get("status") == "updated")
print(f"\n=== COMPLETE: {success}/{len(results)} posts updated with external references ===")
