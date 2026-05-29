#!/usr/bin/env python3
"""
Phase 10AK: Weakest Cluster Rescue
Target clusters: DOG GROOMING, DOG HARNESSES, DOG BEDS
Adds missing: comparison tables, At a Glance boxes, beginner recs, budget vs premium
"""

import subprocess
import json
import time
import csv
import os
import re
import tempfile

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
BASE = "https://pethubonline.com/wp-json/wp/v2"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ak_data"
LOG_FILE = os.path.join(DATA_DIR, "weak_cluster_rescue_log.csv")
DELAY = 2

# All posts in the three weak clusters from the inventory
POSTS = {
    "Dog Grooming": [
        5464, 4563, 4251, 4244, 4237, 4230, 4078, 4071, 4064, 4057
    ],
    "Dog Harnesses": [
        5418, 4414, 4413, 4412, 4411, 4279, 4258, 4139, 4049, 4042, 4034, 4027
    ],
    "Dog Beds": [
        5522, 5510, 4784, 4783, 4018, 4011, 4004, 3996
    ],
}

# Additional post 5416 is in "Educational" cluster, skip it

def api_get(endpoint):
    """GET from WP REST API."""
    url = f"{BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=30
    )
    return json.loads(result.stdout)

def api_update(post_id, data):
    """Update a post via WP REST API."""
    url = f"{BASE}/posts/{post_id}"
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir=DATA_DIR)
    json.dump(data, tmp)
    tmp.close()
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, "-d", f"@{tmp.name}",
         "-H", "Content-Type: application/json", "-X", "POST", url],
        capture_output=True, text=True, timeout=60
    )
    os.unlink(tmp.name)
    resp = json.loads(result.stdout)
    if "id" in resp:
        return True
    print(f"  ERROR updating {post_id}: {result.stdout[:300]}")
    return False


# ──────────────────────────────────────────────────────────────────────
# CONTENT GENERATORS: produce blocks specific to each post's topic
# ──────────────────────────────────────────────────────────────────────

def generate_comparison_table(title, cluster):
    """Generate a comparison table specific to the post topic and cluster."""
    title_lower = title.lower()

    # ── DOG GROOMING ──
    if cluster == "Dog Grooming":
        if "brush" in title_lower and "cat" not in title_lower:
            rows = (
                "<tr><td>Slicker Brush</td><td>Medium to long coats</td><td>Removes tangles and loose undercoat</td><td>Clean after each use</td><td>Most breeds</td></tr>"
                "<tr><td>Bristle Brush</td><td>Short, smooth coats</td><td>Distributes natural oils</td><td>Wash weekly</td><td>Short-haired breeds</td></tr>"
                "<tr><td>Undercoat Rake</td><td>Double-coated breeds</td><td>Reaches deep undercoat</td><td>Clean after each use</td><td>Huskies, Retrievers</td></tr>"
                "<tr><td>Pin Brush</td><td>Long, silky coats</td><td>Gentle detangling</td><td>Remove hair after use</td><td>Setters, Spaniels</td></tr>"
                "<tr><td>Rubber Curry Brush</td><td>Short coats, bath time</td><td>Massages skin, removes loose hair</td><td>Rinse after use</td><td>Bulldogs, Boxers</td></tr>"
            )
        elif "shampoo" in title_lower and "cat" not in title_lower:
            rows = (
                "<tr><td>General Purpose</td><td>Healthy coats, routine bathing</td><td>Balanced pH, gentle cleansing</td><td>Every 4-6 weeks</td><td>Most dogs</td></tr>"
                "<tr><td>Hypoallergenic</td><td>Sensitive or allergy-prone skin</td><td>Fragrance-free, minimal ingredients</td><td>As needed</td><td>Sensitive breeds</td></tr>"
                "<tr><td>Medicated</td><td>Skin conditions (vet-directed)</td><td>Antifungal or antibacterial agents</td><td>Per vet advice</td><td>Dogs with skin issues</td></tr>"
                "<tr><td>Puppy Formula</td><td>Dogs under 12 months</td><td>Extra-gentle, tear-free</td><td>Monthly or as needed</td><td>All puppies</td></tr>"
                "<tr><td>Deodorising</td><td>Dogs prone to odour</td><td>Neutralises smell without masking</td><td>Every 3-4 weeks</td><td>Active, outdoor dogs</td></tr>"
            )
        elif "nail" in title_lower and "cat" not in title_lower:
            rows = (
                "<tr><td>Guillotine Clipper</td><td>Small to medium dogs</td><td>Single blade, clean cut</td><td>Sharpen/replace blade</td><td>Thinner nails</td></tr>"
                "<tr><td>Scissor-Style Clipper</td><td>Medium to large dogs</td><td>Strong leverage, precise control</td><td>Oil pivot point</td><td>Thicker nails</td></tr>"
                "<tr><td>Nail Grinder</td><td>Nervous dogs, smooth finish</td><td>Gradual filing, less risk of quick</td><td>Replace sanding bands</td><td>All sizes</td></tr>"
                "<tr><td>Plier-Style Clipper</td><td>Large and giant breeds</td><td>Heavy-duty cutting power</td><td>Keep blades sharp</td><td>Thick, tough nails</td></tr>"
            )
        elif "cat brush" in title_lower:
            rows = (
                "<tr><td>Soft Slicker Brush</td><td>Medium to long cat coats</td><td>Gentle tangle removal</td><td>Clean after each use</td><td>Persians, Maine Coons</td></tr>"
                "<tr><td>Fine-Tooth Comb</td><td>Detecting fleas, fine debris</td><td>Close-set teeth for precision</td><td>Rinse after use</td><td>All cats</td></tr>"
                "<tr><td>Rubber Grooming Mitt</td><td>Short-haired cats</td><td>Massages while removing loose fur</td><td>Rinse after use</td><td>British Shorthairs</td></tr>"
                "<tr><td>Deshedding Tool</td><td>Heavy shedders</td><td>Reaches undercoat safely</td><td>Clean teeth after use</td><td>Double-coated breeds</td></tr>"
            )
        elif "cat nail" in title_lower:
            rows = (
                "<tr><td>Small Scissor Clipper</td><td>Kittens and small cats</td><td>Precise, gentle cuts</td><td>Sharpen regularly</td><td>Kittens, small breeds</td></tr>"
                "<tr><td>Guillotine Clipper</td><td>Average-sized cats</td><td>Quick, clean single cut</td><td>Replace blade as needed</td><td>Most adult cats</td></tr>"
                "<tr><td>Cat Nail Grinder</td><td>Nervous cats</td><td>Gradual filing, quiet motor</td><td>Replace sanding bands</td><td>Anxious cats</td></tr>"
                "<tr><td>Human Nail Clipper (small)</td><td>Kittens only</td><td>Familiar tool, precise for tiny nails</td><td>Standard care</td><td>Very young kittens</td></tr>"
            )
        elif "cat shampoo" in title_lower:
            rows = (
                "<tr><td>Waterless/Dry Shampoo</td><td>Cats that dislike water</td><td>No-rinse foam or spray</td><td>Use as needed</td><td>Most cats</td></tr>"
                "<tr><td>Gentle Liquid Shampoo</td><td>Occasional full bath</td><td>Cat-safe pH, mild formula</td><td>Every few months</td><td>Tolerant cats</td></tr>"
                "<tr><td>Medicated Shampoo</td><td>Skin conditions (vet-directed)</td><td>Treats fungal or bacterial issues</td><td>Per vet advice</td><td>Cats with skin issues</td></tr>"
                "<tr><td>Kitten Formula</td><td>Kittens under 6 months</td><td>Ultra-gentle, tear-free</td><td>Only when necessary</td><td>All kittens</td></tr>"
            )
        elif "cat grooming" in title_lower or "cat" in title_lower and "supplies" in title_lower:
            rows = (
                "<tr><td>Grooming Brush</td><td>Regular coat maintenance</td><td>Removes loose fur, prevents matting</td><td>Clean after each use</td><td>All cats</td></tr>"
                "<tr><td>Nail Clipper</td><td>Routine claw trimming</td><td>Prevents overgrowth and snagging</td><td>Sharpen/replace</td><td>All cats</td></tr>"
                "<tr><td>Ear Cleaner</td><td>Ear hygiene</td><td>Removes wax and debris gently</td><td>Use as directed</td><td>Fold-eared breeds</td></tr>"
                "<tr><td>Deshedding Tool</td><td>Heavy shedders</td><td>Reduces loose undercoat</td><td>Clean teeth after use</td><td>Long-haired breeds</td></tr>"
                "<tr><td>Grooming Wipes</td><td>Quick clean-ups</td><td>Fragrance-free, safe for skin</td><td>Dispose after use</td><td>All cats</td></tr>"
            )
        elif "glossary" in title_lower or "terms" in title_lower:
            rows = (
                "<tr><td>Stripping</td><td>Wire-coated breeds</td><td>Removes dead outer coat by hand</td><td>Every 6-8 weeks</td><td>Terriers, Schnauzers</td></tr>"
                "<tr><td>Clipping</td><td>Breeds needing regular haircuts</td><td>Electric clipper with guard combs</td><td>Every 4-8 weeks</td><td>Poodles, Bichons</td></tr>"
                "<tr><td>Dematting</td><td>Severely tangled coats</td><td>Specialist comb or splitter</td><td>As needed</td><td>Long-coated breeds</td></tr>"
                "<tr><td>Scissoring</td><td>Precision shaping</td><td>Thinning and blending shears</td><td>Professional sessions</td><td>Show dogs</td></tr>"
                "<tr><td>Deshedding</td><td>Heavy shedders</td><td>Undercoat removal tool</td><td>Weekly during moult</td><td>Double-coated breeds</td></tr>"
            )
        elif "basics" in title_lower or "complete guide" in title_lower:
            rows = (
                "<tr><td>Brushing</td><td>All dogs</td><td>Removes loose hair, distributes oils</td><td>2-3 times per week</td><td>All breeds</td></tr>"
                "<tr><td>Bathing</td><td>Dogs needing a wash</td><td>Cleanses skin and coat</td><td>Every 4-8 weeks</td><td>All breeds</td></tr>"
                "<tr><td>Nail Trimming</td><td>All dogs</td><td>Prevents overgrowth and discomfort</td><td>Every 2-4 weeks</td><td>All breeds</td></tr>"
                "<tr><td>Ear Cleaning</td><td>Floppy-eared breeds especially</td><td>Prevents infection and wax build-up</td><td>Weekly checks</td><td>Spaniels, Retrievers</td></tr>"
                "<tr><td>Teeth Brushing</td><td>All dogs</td><td>Reduces plaque and tartar</td><td>Daily ideally</td><td>All breeds</td></tr>"
            )
        elif "supplies" in title_lower and "cat" not in title_lower:
            rows = (
                "<tr><td>Brush Set</td><td>Daily coat maintenance</td><td>Multiple brush types for versatility</td><td>Clean after each use</td><td>All coat types</td></tr>"
                "<tr><td>Nail Clippers</td><td>Regular claw trimming</td><td>Sharp blades, safety guard</td><td>Sharpen or replace</td><td>All dogs</td></tr>"
                "<tr><td>Shampoo &amp; Conditioner</td><td>Bath time</td><td>pH-balanced for dogs</td><td>Replace when empty</td><td>All dogs</td></tr>"
                "<tr><td>Ear Cleaning Solution</td><td>Ear hygiene</td><td>Dissolves wax, vet-approved</td><td>Use as directed</td><td>Floppy-eared breeds</td></tr>"
                "<tr><td>Grooming Table/Mat</td><td>Home grooming setup</td><td>Non-slip surface, secure footing</td><td>Wipe down after use</td><td>Regular home groomers</td></tr>"
            )
        else:
            # generic grooming fallback
            rows = (
                "<tr><td>Brushing</td><td>Coat maintenance</td><td>Removes tangles and loose fur</td><td>Several times weekly</td><td>All breeds</td></tr>"
                "<tr><td>Bathing</td><td>Cleansing</td><td>Removes dirt and odour</td><td>Every 4-8 weeks</td><td>All breeds</td></tr>"
                "<tr><td>Nail Care</td><td>Paw health</td><td>Prevents overgrowth</td><td>Every 2-4 weeks</td><td>All breeds</td></tr>"
                "<tr><td>Ear Cleaning</td><td>Infection prevention</td><td>Removes wax build-up</td><td>Weekly checks</td><td>All breeds</td></tr>"
            )

    # ── DOG HARNESSES ──
    elif cluster == "Dog Harnesses":
        if "no-pull" in title_lower or "no pull" in title_lower:
            rows = (
                "<tr><td>Front-Clip Harness</td><td>Moderate pullers</td><td>Redirects dog towards handler</td><td>Check stitching monthly</td><td>Medium to large dogs</td></tr>"
                "<tr><td>Dual-Clip Harness</td><td>Training versatility</td><td>Front and back attachment points</td><td>Inspect clips regularly</td><td>All sizes</td></tr>"
                "<tr><td>Head Halter Style</td><td>Strong pullers</td><td>Controls head direction gently</td><td>Check fit weekly</td><td>Large, strong dogs</td></tr>"
                "<tr><td>Tightening Harness</td><td>Persistent pullers</td><td>Mild pressure feedback on pull</td><td>Ensure no chafing</td><td>Dogs in active training</td></tr>"
            )
        elif "measure" in title_lower or "step-by-step" in title_lower:
            rows = (
                "<tr><td>Chest Girth</td><td>Primary harness sizing</td><td>Widest part of ribcage</td><td>Re-measure quarterly</td><td>All harness types</td></tr>"
                "<tr><td>Neck Circumference</td><td>Neck loop fit</td><td>Base of neck, two-finger gap</td><td>Check after growth spurts</td><td>Overhead harnesses</td></tr>"
                "<tr><td>Back Length</td><td>Full-body harnesses</td><td>Base of neck to tail base</td><td>Re-measure for puppies</td><td>Full-coverage styles</td></tr>"
                "<tr><td>Weight Range</td><td>Manufacturer sizing charts</td><td>Cross-reference with girth</td><td>Weigh regularly</td><td>All harness types</td></tr>"
            )
        elif "vs" in title_lower or "collar" in title_lower and "harness" in title_lower and "puppy" not in title_lower and "cat" not in title_lower:
            rows = (
                "<tr><td>Flat Collar</td><td>ID tags, well-trained dogs</td><td>Simple, lightweight</td><td>Check fit monthly</td><td>Non-pullers</td></tr>"
                "<tr><td>Back-Clip Harness</td><td>Small dogs, casual walks</td><td>No neck pressure</td><td>Wash monthly</td><td>Small breeds</td></tr>"
                "<tr><td>Front-Clip Harness</td><td>Training, moderate pullers</td><td>Redirects pulling force</td><td>Inspect stitching</td><td>Medium to large dogs</td></tr>"
                "<tr><td>Head Collar</td><td>Strong pullers, training</td><td>Controls head direction</td><td>Check for rubbing</td><td>Large, strong breeds</td></tr>"
            )
        elif "types explained" in title_lower:
            rows = (
                "<tr><td>Step-In Harness</td><td>Dogs that dislike overhead fitting</td><td>Dog steps in, clips on back</td><td>Check buckle security</td><td>Small to medium dogs</td></tr>"
                "<tr><td>Overhead Harness</td><td>Quick fitting</td><td>Slips over head, clips at chest</td><td>Inspect straps</td><td>Cooperative dogs</td></tr>"
                "<tr><td>Vest Harness</td><td>Even weight distribution</td><td>Padded, wide chest panel</td><td>Machine wash</td><td>Brachycephalic breeds</td></tr>"
                "<tr><td>Front-Clip Harness</td><td>Training and pull management</td><td>Lead attaches at chest</td><td>Check clip function</td><td>Pullers in training</td></tr>"
                "<tr><td>Dual-Clip Harness</td><td>Versatile training</td><td>Front and back D-rings</td><td>Regular strap checks</td><td>All sizes, all stages</td></tr>"
            )
        elif "complete guide" in title_lower and ("collar" in title_lower or "harness" in title_lower):
            rows = (
                "<tr><td>Flat Collar</td><td>Everyday ID, trained dogs</td><td>Lightweight, carries tags</td><td>Check fit monthly</td><td>All dogs (with tags)</td></tr>"
                "<tr><td>Back-Clip Harness</td><td>Small dogs, gentle walkers</td><td>Comfortable, no neck strain</td><td>Wash regularly</td><td>Small breeds</td></tr>"
                "<tr><td>Front-Clip Harness</td><td>Pullers in training</td><td>Redirects pulling</td><td>Inspect clips</td><td>Medium to large dogs</td></tr>"
                "<tr><td>Martingale Collar</td><td>Escape-prone dogs</td><td>Tightens gently, cannot slip off</td><td>Check adjustment</td><td>Greyhounds, Whippets</td></tr>"
                "<tr><td>Padded Vest Harness</td><td>Brachycephalic breeds</td><td>Distributes pressure across chest</td><td>Machine washable</td><td>Pugs, Bulldogs</td></tr>"
            )
        elif "cat harness" in title_lower:
            rows = (
                "<tr><td>H-Style Harness</td><td>Slim, agile cats</td><td>Lightweight, minimal coverage</td><td>Check buckles</td><td>Active cats</td></tr>"
                "<tr><td>Vest/Jacket Harness</td><td>Nervous cats</td><td>Secure, escape-resistant</td><td>Machine washable</td><td>First-time walkers</td></tr>"
                "<tr><td>Figure-8 Harness</td><td>Quick fitting</td><td>Simple loop design</td><td>Inspect for wear</td><td>Cooperative cats</td></tr>"
                "<tr><td>Step-In Harness</td><td>Cats that dislike overhead fitting</td><td>Paws step through loops</td><td>Check strap tension</td><td>Calm cats</td></tr>"
            )
        elif "cat collar" in title_lower:
            rows = (
                "<tr><td>Breakaway Collar</td><td>Outdoor cats</td><td>Releases under pressure for safety</td><td>Test clasp monthly</td><td>All outdoor cats</td></tr>"
                "<tr><td>Reflective Collar</td><td>Cats out at dusk/dawn</td><td>Increases visibility to drivers</td><td>Check reflectivity</td><td>Outdoor cats</td></tr>"
                "<tr><td>Elastic/Stretch Collar</td><td>Moderate safety</td><td>Stretches if snagged</td><td>Replace when stretched</td><td>Indoor/outdoor cats</td></tr>"
                "<tr><td>GPS Tracker Collar</td><td>Cats that roam</td><td>Real-time location tracking</td><td>Charge battery</td><td>Adventurous cats</td></tr>"
            )
        elif "training lead" in title_lower or "long line" in title_lower:
            rows = (
                "<tr><td>Standard Lead (1.2m)</td><td>Everyday walks</td><td>Good control in busy areas</td><td>Inspect clip</td><td>All dogs</td></tr>"
                "<tr><td>Long Line (5-10m)</td><td>Recall training</td><td>Freedom with safety backup</td><td>Check for fraying</td><td>Dogs learning recall</td></tr>"
                "<tr><td>Double-Ended Lead</td><td>Harness + collar setup</td><td>Two clip points for control</td><td>Check both clips</td><td>Pullers in training</td></tr>"
                "<tr><td>Bungee/Shock-Absorbing Lead</td><td>Active, energetic dogs</td><td>Reduces jolt from lunging</td><td>Inspect elastic</td><td>Strong, reactive dogs</td></tr>"
            )
        elif "puppy" in title_lower:
            rows = (
                "<tr><td>Lightweight Flat Collar</td><td>First collar for puppies</td><td>Adjustable, carries ID tag</td><td>Resize as puppy grows</td><td>All puppies from 8 weeks</td></tr>"
                "<tr><td>Puppy Harness</td><td>Lead training</td><td>No neck pressure for fragile puppy</td><td>Check fit weekly</td><td>Puppies starting walks</td></tr>"
                "<tr><td>Breakaway Collar</td><td>Safety during play</td><td>Releases under pressure</td><td>Test clasp regularly</td><td>Playful puppies</td></tr>"
                "<tr><td>Adjustable Harness</td><td>Growing puppies</td><td>Multiple adjustment points</td><td>Re-fit fortnightly</td><td>Fast-growing breeds</td></tr>"
            )
        elif "lead" in title_lower and "walking" in title_lower:
            rows = (
                "<tr><td>Standard Nylon Lead</td><td>Daily walks</td><td>Durable, easy to clean</td><td>Machine washable</td><td>All dogs</td></tr>"
                "<tr><td>Leather Lead</td><td>Comfortable grip</td><td>Softens with use, long-lasting</td><td>Condition leather</td><td>Medium to large dogs</td></tr>"
                "<tr><td>Retractable Lead</td><td>Open spaces only</td><td>Variable length</td><td>Test lock mechanism</td><td>Well-trained dogs only</td></tr>"
                "<tr><td>Rope Lead</td><td>Active dogs</td><td>Strong, weather-resistant</td><td>Rinse after muddy walks</td><td>Outdoor and working dogs</td></tr>"
                "<tr><td>Hands-Free Lead</td><td>Runners and joggers</td><td>Waist-worn, shock-absorbing</td><td>Check waist clip</td><td>Active owners</td></tr>"
            )
        else:
            rows = (
                "<tr><td>Back-Clip Harness</td><td>Small dogs, gentle walkers</td><td>Comfortable, simple design</td><td>Wash monthly</td><td>Small breeds</td></tr>"
                "<tr><td>Front-Clip Harness</td><td>Pullers in training</td><td>Redirects forward motion</td><td>Check clips</td><td>Medium to large dogs</td></tr>"
                "<tr><td>Vest Harness</td><td>Even pressure distribution</td><td>Padded chest panel</td><td>Machine washable</td><td>Brachycephalic breeds</td></tr>"
                "<tr><td>Dual-Clip Harness</td><td>Versatile training</td><td>Front and back D-rings</td><td>Inspect regularly</td><td>All sizes</td></tr>"
            )

    # ── DOG BEDS ──
    elif cluster == "Dog Beds":
        if "orthopaedic" in title_lower or "orthop" in title_lower or "joint" in title_lower:
            rows = (
                "<tr><td>Memory Foam Bed</td><td>Senior dogs, joint issues</td><td>Moulds to body shape</td><td>Removable, washable cover</td><td>Arthritis, hip dysplasia</td></tr>"
                "<tr><td>Gel-Infused Foam Bed</td><td>Dogs that overheat</td><td>Cooling gel layer</td><td>Wipe gel surface</td><td>Large breeds, warm climates</td></tr>"
                "<tr><td>Bolster Orthopaedic Bed</td><td>Dogs that lean or rest heads</td><td>Supportive raised edges</td><td>Machine-wash cover</td><td>Older dogs seeking comfort</td></tr>"
                "<tr><td>Platform/Elevated Orthopaedic</td><td>Dogs needing airflow</td><td>Raised off floor, firm surface</td><td>Wipe frame, wash pad</td><td>Post-surgery recovery</td></tr>"
                "<tr><td>Egg-Crate Foam Bed</td><td>Budget joint support</td><td>Pressure-point relief</td><td>Replace foam annually</td><td>Mild joint stiffness</td></tr>"
            )
        elif "cooling" in title_lower or "temperature" in title_lower:
            rows = (
                "<tr><td>Gel Cooling Mat</td><td>Hot weather, overheating dogs</td><td>Pressure-activated cooling gel</td><td>Wipe clean</td><td>All breeds in summer</td></tr>"
                "<tr><td>Elevated/Raised Bed</td><td>Year-round airflow</td><td>Mesh surface, air circulation</td><td>Hose down</td><td>Outdoor and indoor use</td></tr>"
                "<tr><td>Water-Filled Cooling Pad</td><td>Intense heat</td><td>Cold water circulation</td><td>Refill water, check for leaks</td><td>Large, heavy-coated breeds</td></tr>"
                "<tr><td>Breathable Fabric Bed</td><td>Mild temperature regulation</td><td>Open-weave or mesh material</td><td>Machine washable</td><td>Dogs that sleep indoors</td></tr>"
            )
        elif "puppy" in title_lower or "crate" in title_lower:
            rows = (
                "<tr><td>Crate Mat/Pad</td><td>Crate training</td><td>Fits standard crate sizes</td><td>Machine washable</td><td>Puppies in crate training</td></tr>"
                "<tr><td>Waterproof Puppy Bed</td><td>Puppies prone to accidents</td><td>Waterproof liner protects filling</td><td>Wipe and wash cover</td><td>Young, untrained puppies</td></tr>"
                "<tr><td>Bolster Nest Bed</td><td>Puppies seeking security</td><td>Raised edges for snuggling</td><td>Machine-wash cover</td><td>Anxious or new puppies</td></tr>"
                "<tr><td>Chew-Resistant Bed</td><td>Teething puppies</td><td>Reinforced fabric, tough seams</td><td>Inspect for damage</td><td>Destructive chewers</td></tr>"
            )
        elif "size" in title_lower or "sizing" in title_lower or "measure" in title_lower:
            rows = (
                "<tr><td>Small (up to 45cm)</td><td>Toy and miniature breeds</td><td>Cosy, enclosed feel</td><td>Machine washable</td><td>Chihuahuas, Yorkies</td></tr>"
                "<tr><td>Medium (45-75cm)</td><td>Spaniels, Beagles, Corgis</td><td>Room to stretch and curl</td><td>Removable cover</td><td>Mid-sized breeds</td></tr>"
                "<tr><td>Large (75-100cm)</td><td>Labradors, Setters, Collies</td><td>Full stretch space</td><td>Machine-wash cover</td><td>Large breeds</td></tr>"
                "<tr><td>Extra Large (100cm+)</td><td>Giant breeds</td><td>Reinforced base, extra filling</td><td>Spot clean or hose</td><td>Great Danes, Mastiffs</td></tr>"
            )
        elif "material" in title_lower or "foam" in title_lower or "memory" in title_lower:
            rows = (
                "<tr><td>Memory Foam</td><td>Joint support, older dogs</td><td>Conforms to body shape</td><td>Cover wash, foam spot-clean</td><td>Senior dogs, large breeds</td></tr>"
                "<tr><td>Polyester Fibre Fill</td><td>Budget, general comfort</td><td>Soft, lightweight</td><td>Machine washable</td><td>Healthy, young dogs</td></tr>"
                "<tr><td>Orthopaedic Foam</td><td>Firm support</td><td>High-density, durable</td><td>Spot clean foam</td><td>Dogs with mobility issues</td></tr>"
                "<tr><td>Cedar/Buckwheat Fill</td><td>Natural pest deterrent</td><td>Insect-repelling, breathable</td><td>Replace fill periodically</td><td>Outdoor beds</td></tr>"
                "<tr><td>Faux Fur/Sherpa</td><td>Warmth and cosiness</td><td>Plush surface, insulating</td><td>Machine wash gentle</td><td>Small breeds, winter use</td></tr>"
            )
        elif "complete guide" in title_lower or ("best" in title_lower and "bed" in title_lower and "cooling" not in title_lower and "puppy" not in title_lower and "ortho" not in title_lower):
            rows = (
                "<tr><td>Bolster/Nest Bed</td><td>Dogs that curl up</td><td>Raised edges for head resting</td><td>Machine-wash cover</td><td>Most dogs</td></tr>"
                "<tr><td>Flat Mat/Cushion</td><td>Dogs that sprawl</td><td>Low profile, large surface</td><td>Machine washable</td><td>Large breeds</td></tr>"
                "<tr><td>Orthopaedic Bed</td><td>Senior dogs, joint issues</td><td>Memory foam or high-density foam</td><td>Removable cover</td><td>Older or injured dogs</td></tr>"
                "<tr><td>Elevated/Raised Bed</td><td>Warm climates, outdoor use</td><td>Airflow underneath</td><td>Hose down frame</td><td>Active, outdoor dogs</td></tr>"
                "<tr><td>Cave/Hooded Bed</td><td>Anxious or burrowing dogs</td><td>Enclosed, den-like feel</td><td>Machine-wash cover</td><td>Small, nervous breeds</td></tr>"
            )
        else:
            rows = (
                "<tr><td>Bolster Bed</td><td>Dogs that curl up</td><td>Supportive raised edges</td><td>Machine-wash cover</td><td>Most breeds</td></tr>"
                "<tr><td>Orthopaedic Bed</td><td>Senior dogs, joint support</td><td>Memory foam base</td><td>Removable cover</td><td>Older dogs</td></tr>"
                "<tr><td>Elevated Bed</td><td>Warm weather, airflow</td><td>Raised mesh platform</td><td>Hose down</td><td>Active dogs</td></tr>"
                "<tr><td>Flat Cushion</td><td>Dogs that sprawl</td><td>Low profile, wide surface</td><td>Machine washable</td><td>Large breeds</td></tr>"
            )
    else:
        return None

    table_block = (
        '<!-- wp:heading {"level":3} -->\n'
        '<h3 class="wp-block-heading">Quick Comparison</h3>\n'
        '<!-- /wp:heading -->\n'
        '<!-- wp:table {"className":"is-style-stripes"} -->\n'
        '<figure class="wp-block-table is-style-stripes"><table><thead><tr>'
        '<th>Type</th><th>Best For</th><th>Key Feature</th><th>Maintenance</th><th>Suitability</th>'
        '</tr></thead><tbody>\n'
        f'{rows}\n'
        '</tbody></table></figure>\n'
        '<!-- /wp:table -->'
    )
    return table_block


def generate_at_a_glance(title, cluster):
    """Generate At a Glance bullet points specific to the post topic."""
    title_lower = title.lower()

    # ── DOG GROOMING ──
    if cluster == "Dog Grooming":
        if "brush" in title_lower and "cat" not in title_lower:
            bullets = (
                "<li>Different coat types need different brush styles -- there is no single universal brush</li>"
                "<li>Brush direction matters: always follow the natural lie of your dog's coat</li>"
                "<li>Regular brushing (2-3 times weekly) prevents matting and reduces shedding around the home</li>"
                "<li>Watch for signs of skin irritation while brushing, especially around ears and belly</li>"
            )
        elif "shampoo" in title_lower and "cat" not in title_lower:
            bullets = (
                "<li>Human shampoo is too acidic for dogs -- always use a canine-specific formula</li>"
                "<li>Most dogs only need bathing every 4-8 weeks unless they get particularly dirty</li>"
                "<li>Hypoallergenic options are best for dogs with sensitive or allergy-prone skin</li>"
                "<li>Rinse thoroughly -- leftover shampoo residue can cause itching and flaky skin</li>"
            )
        elif "nail" in title_lower and "cat" not in title_lower:
            bullets = (
                "<li>Overgrown nails can affect posture and cause joint pain over time</li>"
                "<li>Trim every 2-4 weeks; if you hear clicking on hard floors, they are overdue</li>"
                "<li>The quick (blood vessel inside the nail) is harder to see in dark nails -- trim small amounts</li>"
                "<li>Grinders are a good alternative for dogs frightened by the clipping sound</li>"
            )
        elif "cat brush" in title_lower:
            bullets = (
                "<li>Cats groom themselves, but brushing reduces hairballs and removes loose undercoat</li>"
                "<li>Long-haired breeds benefit from daily brushing; short-haired cats need it 1-2 times per week</li>"
                "<li>Use gentle strokes and stop if your cat shows signs of irritation or overstimulation</li>"
            )
        elif "cat nail" in title_lower:
            bullets = (
                "<li>Most cats need their claws trimmed every 2-4 weeks to prevent overgrowth</li>"
                "<li>Only trim the transparent tip -- avoid the pink quick inside the claw</li>"
                "<li>Start handling your cat's paws early so they become comfortable with the process</li>"
            )
        elif "cat shampoo" in title_lower:
            bullets = (
                "<li>Most cats rarely need a full bath -- waterless options are usually sufficient</li>"
                "<li>Never use dog shampoo on cats as certain ingredients can be toxic to felines</li>"
                "<li>If a full bath is needed, keep the water lukewarm and dry your cat thoroughly afterwards</li>"
            )
        elif "cat grooming" in title_lower or ("cat" in title_lower and "supplies" in title_lower):
            bullets = (
                "<li>A basic cat grooming kit includes a brush, nail clipper, and ear cleaner</li>"
                "<li>Most cats prefer short, gentle grooming sessions -- 5 to 10 minutes at a time</li>"
                "<li>Never use essential oils or human grooming products on cats as many are toxic to felines</li>"
                "<li>Start grooming routines when your cat is young for best long-term tolerance</li>"
            )
        elif "glossary" in title_lower or "terms" in title_lower:
            bullets = (
                "<li>Grooming terminology can be confusing -- this glossary covers the most common techniques</li>"
                "<li>Some techniques (like stripping) are breed-specific and not needed for every dog</li>"
                "<li>Understanding the terms helps you communicate clearly with professional groomers</li>"
                "<li>Always check whether a technique is suitable for your dog's coat type before trying it</li>"
            )
        elif "basics" in title_lower or ("complete guide" in title_lower and "cat" not in title_lower and "supplies" not in title_lower):
            bullets = (
                "<li>A regular grooming routine helps you spot health issues like lumps, parasites, or skin problems early</li>"
                "<li>The five basics are brushing, bathing, nail trimming, ear cleaning, and teeth brushing</li>"
                "<li>Start grooming your dog young -- even if a puppy does not need it yet, early handling builds tolerance</li>"
                "<li>Frequency depends on breed: long-coated dogs need more frequent attention than short-coated ones</li>"
            )
        elif "supplies" in title_lower and "cat" not in title_lower:
            bullets = (
                "<li>Investing in quality grooming tools saves money long-term and is gentler on your dog</li>"
                "<li>Essential supplies include a suitable brush, nail clipper, dog shampoo, and ear cleaner</li>"
                "<li>Choose tools based on your dog's coat type, size, and temperament</li>"
                "<li>Keep all grooming tools clean and stored in a dedicated grooming bag or box</li>"
            )
        else:
            bullets = (
                "<li>Regular grooming is essential for all dogs regardless of coat type</li>"
                "<li>Frequency and tools vary depending on breed, coat type, and lifestyle</li>"
                "<li>Grooming is also a chance to check for skin issues, parasites, and lumps</li>"
            )

    # ── DOG HARNESSES ──
    elif cluster == "Dog Harnesses":
        if "no-pull" in title_lower or "no pull" in title_lower:
            bullets = (
                "<li>No-pull harnesses discourage pulling by redirecting your dog's forward momentum</li>"
                "<li>Front-clip designs are the most common and effective for moderate pullers</li>"
                "<li>A harness alone will not solve pulling -- consistent training alongside it is essential</li>"
                "<li>Always ensure the harness fits properly to avoid chafing under the front legs</li>"
            )
        elif "measure" in title_lower or "step-by-step" in title_lower:
            bullets = (
                "<li>Chest girth (widest part of the ribcage) is the single most important measurement</li>"
                "<li>Use a flexible tape measure and allow two fingers of space for comfort</li>"
                "<li>Puppies grow fast -- re-measure every 2-4 weeks until they reach adult size</li>"
                "<li>Different brands size differently, so always check each manufacturer's chart</li>"
            )
        elif "vs" in title_lower or ("collar" in title_lower and "harness" in title_lower and "puppy" not in title_lower and "cat" not in title_lower and "complete" not in title_lower):
            bullets = (
                "<li>Harnesses distribute pressure across the chest; collars concentrate it on the neck</li>"
                "<li>Flat-faced (brachycephalic) breeds should almost always use a harness instead of a collar</li>"
                "<li>A collar is still useful for carrying ID tags even if you walk with a harness</li>"
                "<li>The best choice depends on your dog's size, breed, training stage, and walking behaviour</li>"
            )
        elif "types explained" in title_lower:
            bullets = (
                "<li>The main harness types are step-in, overhead, vest, front-clip, and dual-clip</li>"
                "<li>Step-in harnesses suit dogs that dislike things going over their head</li>"
                "<li>Vest harnesses provide the widest pressure distribution and suit flat-faced breeds</li>"
                "<li>Dual-clip harnesses offer the most flexibility for training progression</li>"
            )
        elif "complete guide" in title_lower:
            bullets = (
                "<li>Every dog needs a collar for ID, but the right walking gear depends on their behaviour</li>"
                "<li>Front-clip harnesses help reduce pulling; back-clip ones are more comfortable for non-pullers</li>"
                "<li>Replace any collar or harness showing signs of fraying, cracking, or weakened clips</li>"
                "<li>Always allow a two-finger gap between the harness strap and your dog's body</li>"
            )
        elif "cat harness" in title_lower:
            bullets = (
                "<li>Cats require escape-proof harnesses -- they are far more flexible than dogs</li>"
                "<li>Vest-style harnesses are the most secure and hardest for cats to wriggle out of</li>"
                "<li>Introduce the harness gradually indoors before attempting outdoor walks</li>"
                "<li>Never leave a cat unattended while wearing a harness</li>"
            )
        elif "cat collar" in title_lower:
            bullets = (
                "<li>Safety breakaway collars are essential -- they release if the collar snags on something</li>"
                "<li>Reflective collars improve visibility for cats that go outdoors at night</li>"
                "<li>Ensure the collar fits snugly but allows two fingers between the collar and neck</li>"
                "<li>Regularly check that the breakaway clasp still releases properly</li>"
            )
        elif "training lead" in title_lower or "long line" in title_lower:
            bullets = (
                "<li>Long lines (5-10m) are essential for safe recall training in open spaces</li>"
                "<li>Never attach a long line to a collar -- always use a harness to prevent neck injury</li>"
                "<li>Double-ended leads allow you to clip to both a harness and collar for extra control</li>"
                "<li>Retractable leads are not recommended for training as they teach dogs to pull</li>"
            )
        elif "puppy" in title_lower:
            bullets = (
                "<li>Puppies can start wearing a lightweight collar from around 8 weeks of age</li>"
                "<li>Choose adjustable gear that grows with your puppy to avoid frequent replacements</li>"
                "<li>A harness is generally safer than a collar for puppies learning to walk on a lead</li>"
                "<li>Let your puppy wear the collar or harness at home first before attaching a lead</li>"
            )
        elif "lead" in title_lower and "walking" in title_lower:
            bullets = (
                "<li>A standard 1.2m fixed lead gives the best control for everyday walks</li>"
                "<li>Leather leads become softer with use and are comfortable for longer walks</li>"
                "<li>Avoid retractable leads in busy areas -- they reduce your control significantly</li>"
                "<li>Match lead strength to your dog's size and pulling tendency</li>"
            )
        else:
            bullets = (
                "<li>Harnesses spread pressure across the chest and are generally safer than collars for walking</li>"
                "<li>Correct fit is crucial -- an ill-fitting harness can cause chafing and restrict movement</li>"
                "<li>Replace harnesses that show signs of wear, especially frayed stitching or damaged clips</li>"
            )

    # ── DOG BEDS ──
    elif cluster == "Dog Beds":
        if "orthopaedic" in title_lower or "orthop" in title_lower or "joint" in title_lower:
            bullets = (
                "<li>Orthopaedic beds use high-density or memory foam to support joints and relieve pressure points</li>"
                "<li>Dogs with arthritis, hip dysplasia, or post-surgery recovery benefit most from orthopaedic support</li>"
                "<li>Look for beds at least 10cm thick for effective pressure relief</li>"
                "<li>A removable, washable cover is essential for hygiene and longevity</li>"
            )
        elif "cooling" in title_lower or "temperature" in title_lower:
            bullets = (
                "<li>Dogs regulate temperature partly through their paw pads and belly -- a cool surface helps</li>"
                "<li>Gel cooling mats activate with pressure and need no electricity or refrigeration</li>"
                "<li>Elevated beds allow airflow underneath, which provides natural cooling</li>"
                "<li>Brachycephalic and heavy-coated breeds are most vulnerable to overheating</li>"
            )
        elif "puppy" in title_lower or "crate" in title_lower:
            bullets = (
                "<li>Puppies grow fast -- start with a budget-friendly bed you can replace as they grow</li>"
                "<li>Waterproof liners are essential for puppies still being house-trained</li>"
                "<li>Crate mats should fit the crate snugly without bunching up</li>"
                "<li>Avoid beds with removable small parts that a teething puppy could chew and swallow</li>"
            )
        elif "size" in title_lower or "sizing" in title_lower or "measure" in title_lower:
            bullets = (
                "<li>Measure your dog from nose to tail base and add 15-20cm for the ideal bed length</li>"
                "<li>Dogs that curl up need a smaller bed than dogs that sprawl on their side</li>"
                "<li>If between sizes, always size up -- a bed that is too small will not be used</li>"
                "<li>Re-measure if your dog is still growing or has gained/lost significant weight</li>"
            )
        elif "material" in title_lower or "foam" in title_lower or "memory" in title_lower:
            bullets = (
                "<li>Memory foam moulds to your dog's body and is ideal for older dogs with joint issues</li>"
                "<li>Polyester fibre fill is affordable but compresses over time and needs replacing sooner</li>"
                "<li>High-density foam provides firmer, longer-lasting support than standard foam</li>"
                "<li>Always choose a bed with a removable, machine-washable cover for easy cleaning</li>"
            )
        elif "complete guide" in title_lower or ("best" in title_lower and "bed" in title_lower):
            bullets = (
                "<li>The right bed depends on your dog's size, age, sleeping style, and any health conditions</li>"
                "<li>Dogs that curl up prefer bolster or nest beds; sprawlers need flat mats or cushions</li>"
                "<li>Orthopaedic beds are worth the investment for senior dogs or those with joint problems</li>"
                "<li>Replace a dog bed when the filling compresses and no longer springs back</li>"
                "<li>Washability is one of the most important practical features to look for</li>"
            )
        else:
            bullets = (
                "<li>Every dog benefits from a dedicated, comfortable sleeping space</li>"
                "<li>The right bed type depends on size, age, health, and sleeping style</li>"
                "<li>Washable covers are essential for hygiene and reducing allergens</li>"
            )
    else:
        return None

    block = (
        '<!-- wp:group {"style":{"color":{"background":"#eef2ff"},"border":{"radius":"6px","width":"1px","color":"#c7d2fe"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"20px","bottom":"24px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#c7d2fe;border-width:1px;border-radius:6px;background-color:#eef2ff;margin-top:20px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:heading {"level":4} -->\n'
        '<h4 class="wp-block-heading">At a Glance</h4>\n'
        '<!-- /wp:heading -->\n'
        '<!-- wp:list -->\n'
        f'<ul class="wp-block-list">{bullets}</ul>\n'
        '<!-- /wp:list -->\n'
        '</div>\n'
        '<!-- /wp:group -->'
    )
    return block


def generate_beginner_rec(title, cluster):
    """Generate beginner recommendation specific to the post."""
    title_lower = title.lower()

    # ── DOG GROOMING ──
    if cluster == "Dog Grooming":
        if "brush" in title_lower and "cat" not in title_lower:
            text = "Start with a basic slicker brush -- it works well on most coat types. Brush gently in the direction of hair growth, working in small sections. If you are unsure which brush suits your dog, ask your vet or groomer at your next visit."
        elif "shampoo" in title_lower and "cat" not in title_lower:
            text = "Choose a gentle, general-purpose dog shampoo for your first purchase. Avoid anything with strong fragrances or long ingredient lists. Bathe your dog every 4-6 weeks unless they get particularly dirty between washes."
        elif "nail" in title_lower and "cat" not in title_lower:
            text = "If you have never trimmed dog nails before, start with a nail grinder rather than clippers. Grinders remove small amounts at a time, reducing the risk of cutting the quick. Ask your vet to demonstrate the technique at your next appointment."
        elif "cat" in title_lower and "brush" in title_lower:
            text = "A soft rubber grooming mitt is the easiest starting point for cat grooming. Most cats tolerate it well because it feels like being stroked. Use it 2-3 times per week for short-haired cats."
        elif "cat" in title_lower and "nail" in title_lower:
            text = "Start by handling your cat's paws gently each day without clipping. Once they are comfortable, trim just one or two nails per session using small, sharp cat nail clippers. Never rush the process."
        elif "cat" in title_lower and "shampoo" in title_lower:
            text = "Most cats rarely need a bath. Start with waterless grooming wipes or a dry shampoo spray for spot-cleaning. Only attempt a full bath if truly necessary, and always use a product specifically made for cats."
        elif "cat" in title_lower and ("grooming" in title_lower or "supplies" in title_lower):
            text = "Begin with just a soft brush and a pair of cat nail clippers. Add other tools as you learn what your cat tolerates. Keep sessions short (under 5 minutes) and reward your cat with a treat afterwards."
        elif "glossary" in title_lower:
            text = "You do not need to learn every grooming term at once. Focus on the basics first: brushing, bathing, and nail trimming. Use this glossary as a reference when you encounter unfamiliar terms at the groomer or vet."
        elif "basics" in title_lower or "complete guide" in title_lower:
            text = "Start with three essentials: regular brushing (2-3 times per week), monthly baths with dog shampoo, and nail trimming every 2-4 weeks. Get comfortable with these before adding ear cleaning or teeth brushing to your routine."
        elif "supplies" in title_lower:
            text = "You only need four items to start: a slicker brush, basic nail clippers, gentle dog shampoo, and some treats for positive reinforcement. Avoid buying specialist tools until you know what your dog's coat actually needs."
        else:
            text = "Start with the basics -- a suitable brush, dog shampoo, and nail clippers. Keep grooming sessions short and positive. Gradually introduce new tools as your dog becomes comfortable with the routine."

    # ── DOG HARNESSES ──
    elif cluster == "Dog Harnesses":
        if "no-pull" in title_lower or "no pull" in title_lower:
            text = "Start with a front-clip harness -- it is the simplest no-pull option and works well for most dogs. Pair it with consistent loose-lead walking practice. Do not expect the harness to solve pulling on its own; it is a training aid, not a fix."
        elif "measure" in title_lower or "step-by-step" in title_lower:
            text = "Use a soft tape measure and measure your dog's chest girth at the widest point of the ribcage. Write down the number and check it against the brand's specific sizing chart before ordering. When in doubt, size up rather than down."
        elif "vs" in title_lower or ("collar" in title_lower and "harness" in title_lower and "puppy" not in title_lower and "cat" not in title_lower and "complete" not in title_lower):
            text = "If your dog pulls at all, start with a harness rather than a collar. A front-clip harness is the safest first choice for most dogs. Keep a flat collar on for ID tags, but attach the lead to the harness for walks."
        elif "types explained" in title_lower:
            text = "If you are buying your first harness, a dual-clip (front and back attachment) model offers the most flexibility. Start with the front clip for better control, then switch to the back clip as your dog's walking improves."
        elif "complete guide" in title_lower:
            text = "Begin with a well-fitting flat collar for ID tags and a front-clip harness for walks. This combination covers the essentials for any new dog owner. Measure your dog's chest girth carefully before purchasing."
        elif "cat harness" in title_lower:
            text = "Choose a snug-fitting vest-style harness for your cat's first harness -- they are the hardest to escape from. Let your cat wear it indoors for short periods before ever attaching a lead. Never force it; patience is key."
        elif "cat collar" in title_lower:
            text = "Always buy a breakaway (safety) collar for your cat. Test that the clasp releases with moderate pressure. Add a small bell if you want to alert wildlife, and ensure your cat's ID tag has a current phone number."
        elif "training lead" in title_lower or "long line" in title_lower:
            text = "Start with a standard 1.2m fixed lead for everyday walks. Add a 5m long line later when you begin recall training in open spaces. Always attach long lines to a harness, never a collar, to protect your dog's neck."
        elif "puppy" in title_lower:
            text = "Get a lightweight, adjustable collar and a simple harness that can grow with your puppy. Let them wear the collar at home for a few days before attaching a lead. Start with short, positive indoor lead sessions before heading outdoors."
        elif "lead" in title_lower:
            text = "A simple 1.2m nylon lead is all you need to start. It gives good control without being heavy. Avoid retractable leads until your dog walks reliably on a loose lead -- they can teach bad pulling habits."
        else:
            text = "Start with a well-fitting front-clip harness and a standard 1.2m lead. Measure your dog's chest girth before buying and always check the manufacturer's size chart. A harness is generally safer and more comfortable than walking on a collar alone."

    # ── DOG BEDS ──
    elif cluster == "Dog Beds":
        if "orthopaedic" in title_lower or "orthop" in title_lower or "joint" in title_lower:
            text = "If your dog is over 7 years old or has been diagnosed with joint issues, a memory foam bed at least 10cm thick is a good starting point. Look for a removable, washable cover and place the bed in a warm, draught-free spot."
        elif "cooling" in title_lower or "temperature" in title_lower:
            text = "An elevated mesh bed is the simplest cooling option and works year-round. Place it in a shaded area and ensure your dog always has access to fresh water. Add a gel cooling mat on top during heatwaves for extra relief."
        elif "puppy" in title_lower or "crate" in title_lower:
            text = "Start with an inexpensive, washable bed or crate mat that fits your crate size. Puppies grow quickly and may chew their first bed, so save the premium purchase for when they are fully grown. A waterproof liner underneath is a wise addition."
        elif "size" in title_lower or "sizing" in title_lower or "measure" in title_lower:
            text = "Measure your dog from nose to tail base, then add 15-20cm. That is your minimum bed length. If your dog likes to stretch out, measure them while sleeping on their side for the most accurate sizing. When between sizes, always go larger."
        elif "material" in title_lower or "foam" in title_lower:
            text = "For most dogs, a polyester-filled bed with a washable cover is a perfectly good starting point. Upgrade to memory foam when your dog reaches their senior years or if a vet recommends extra joint support. Washability matters more than filling type for everyday life."
        elif "complete guide" in title_lower or ("best" in title_lower and "bed" in title_lower):
            text = "Start with a simple bolster bed in the right size -- it suits most dogs and sleeping styles. Focus on washability and the correct size rather than fancy features. You can always upgrade to a specialist bed later if your dog's needs change."
        else:
            text = "Choose a bed that suits your dog's size and sleeping position. A bolster bed works for most dogs. Make sure the cover is machine washable and the bed is placed in a quiet, draught-free area of your home."
    else:
        return None

    block = (
        '<!-- wp:group {"style":{"color":{"background":"#eff6ff"},"border":{"radius":"6px","width":"1px","color":"#bfdbfe"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"20px","bottom":"20px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#bfdbfe;border-width:1px;border-radius:6px;background-color:#eff6ff;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"}}} -->\n'
        f'<p style="font-size:14px"><strong>If you\'re a beginner:</strong> {text}</p>\n'
        '<!-- /wp:paragraph -->\n'
        '</div>\n'
        '<!-- /wp:group -->'
    )
    return block


def generate_budget_premium(title, cluster):
    """Generate budget vs premium block specific to the post."""
    title_lower = title.lower()

    # ── DOG GROOMING ──
    if cluster == "Dog Grooming":
        if "brush" in title_lower and "cat" not in title_lower:
            budget = "A basic slicker brush is perfectly adequate for most coat types. Look for one with flexible pins and a comfortable grip. Budget brushes work well and last a reasonable time with proper care."
            premium = "Higher-end brushes feature self-cleaning mechanisms, ergonomic handles, and finer pin quality that reduce coat breakage. Worth the upgrade if you groom frequently or have a breed that requires daily brushing."
        elif "shampoo" in title_lower and "cat" not in title_lower:
            budget = "A simple, pH-balanced dog shampoo with minimal ingredients does the job for healthy coats. Concentrated formulas offer better value as you dilute them before use."
            premium = "Premium shampoos use higher-quality ingredients, natural extracts, and targeted formulations for specific coat or skin needs. Worth considering if your dog has skin sensitivities or a demanding coat type."
        elif "nail" in title_lower and "cat" not in title_lower:
            budget = "A basic guillotine or scissor-style clipper is affordable and effective. Ensure the blade is sharp and replace it when it dulls. This is all most dog owners need."
            premium = "Premium nail grinders offer quieter motors, multiple speed settings, and replaceable sanding bands. They are worth the investment for nervous dogs or owners who trim nails frequently."
        elif "cat" in title_lower and "brush" in title_lower:
            budget = "A rubber grooming mitt or a basic fine-tooth comb is inexpensive and effective for most short-haired cats. Both are easy to clean and last well."
            premium = "Self-cleaning slicker brushes and ergonomic deshedding tools make grooming faster and more comfortable for both you and your cat. A good investment for long-haired breeds that need daily attention."
        elif "cat" in title_lower and "nail" in title_lower:
            budget = "A simple pair of small scissor-style clippers is all most cat owners need. Keep them sharp and store them safely."
            premium = "Quiet nail grinders with LED guides reduce stress for anxious cats and give a smoother finish. Useful if your cat is particularly sensitive to the clipping sensation."
        elif "cat" in title_lower and "shampoo" in title_lower:
            budget = "Waterless grooming wipes are an affordable, low-stress option for occasional cleaning. They work well for spot-cleaning and quick freshening up."
            premium = "Veterinary-grade cat shampoos with soothing ingredients like oatmeal or aloe are gentler on sensitive skin. Worth it if your cat has dermatitis or requires regular bathing."
        elif "cat" in title_lower and ("grooming" in title_lower or "supplies" in title_lower):
            budget = "A rubber brush, basic nail clippers, and grooming wipes cover the essentials for most cats. You can find quality versions of all three without spending much."
            premium = "A complete grooming kit with ergonomic tools, self-cleaning brushes, and a quiet nail grinder makes sessions quicker and less stressful. Worthwhile for multi-cat households or long-haired breeds."
        elif "glossary" in title_lower:
            budget = "Basic grooming tools (brush, clippers, shampoo) are enough for home maintenance of most coat types. Professional grooming sessions can supplement your routine 2-4 times per year."
            premium = "Investing in professional-grade tools allows you to perform more advanced techniques at home, reducing the frequency and cost of professional appointments over time."
        elif "basics" in title_lower or ("complete guide" in title_lower and "supplies" not in title_lower):
            budget = "A slicker brush, basic nail clippers, gentle shampoo, and treats for positive reinforcement cost relatively little and cover the essentials for home grooming."
            premium = "A full grooming station with a non-slip mat, professional clippers, multiple brush types, and a quiet nail grinder transforms home grooming into a quicker, more comfortable experience for both you and your dog."
        elif "supplies" in title_lower and "cat" not in title_lower:
            budget = "Start with a slicker brush, standard nail clippers, and a bottle of general-purpose dog shampoo. These three items handle the most common grooming tasks at minimal cost."
            premium = "A comprehensive kit with ergonomic tools, multiple brush types for different areas, a quiet grinder, and a grooming table gives you professional-level capability at home. Best for owners who groom regularly."
        else:
            budget = "Basic, well-made grooming tools are perfectly adequate for most dogs. Focus on buying sharp, clean tools rather than expensive brands."
            premium = "Professional-grade tools offer better ergonomics, quieter operation, and longer lifespan. Worth the investment for frequent groomers or dogs with high-maintenance coats."

    # ── DOG HARNESSES ──
    elif cluster == "Dog Harnesses":
        if "no-pull" in title_lower or "no pull" in title_lower:
            budget = "A basic front-clip nylon harness provides effective pull reduction at a low cost. Ensure adjustable straps and a secure buckle. Adequate for dogs in the early stages of training."
            premium = "Padded, dual-clip harnesses with reflective stitching and multiple adjustment points offer greater comfort and versatility. Worth the upgrade for strong pullers or dogs worn the harness daily for long walks."
        elif "measure" in title_lower or "step-by-step" in title_lower:
            budget = "A flexible fabric tape measure costs very little and is all you need for accurate sizing. In a pinch, use a piece of string and measure it against a ruler."
            premium = "Some brands offer online fit-check tools or generous return policies so you can try before committing. Worth considering if your dog is between sizes or has an unusual body shape."
        elif "vs" in title_lower or ("collar" in title_lower and "harness" in title_lower and "puppy" not in title_lower and "cat" not in title_lower and "complete" not in title_lower):
            budget = "A nylon flat collar and a basic front-clip harness cover most everyday walking needs. Both are durable, easy to clean, and widely available."
            premium = "Leather collars, padded harnesses with reflective trim, and custom-fitted options provide greater comfort and longevity. A sound investment for dogs walked multiple times daily."
        elif "types explained" in title_lower:
            budget = "A simple adjustable nylon harness (step-in or overhead) is sufficient for most well-behaved dogs. Check that buckles and clips are sturdy, even on budget models."
            premium = "Harnesses with padded chest plates, breathable mesh linings, and dual attachment points are more comfortable for extended use. Worth the cost for active dogs or those with sensitive skin."
        elif "complete guide" in title_lower:
            budget = "A flat nylon collar for ID and a basic front-clip harness for walks is a reliable, affordable combination. Prioritise correct fit over brand name."
            premium = "High-quality leather or biothane collars paired with padded, multi-point harnesses last longer and offer superior comfort. Worth investing in once your dog is fully grown and you know their walking style."
        elif "cat harness" in title_lower:
            budget = "A basic adjustable vest harness provides good security for cats new to walking. Nylon models are easy to clean and widely available in small sizes."
            premium = "Escape-proof vest harnesses with soft padding and reflective strips offer peace of mind for regular outdoor adventurers. Worth the upgrade once your cat is comfortable on a lead."
        elif "cat collar" in title_lower:
            budget = "A simple breakaway collar with an ID tag is all most cats need. They are inexpensive and widely available. Replace yearly or when the clasp weakens."
            premium = "GPS tracker collars and reflective safety collars offer extra features for outdoor cats. The investment is worthwhile if your cat roams and you want real-time tracking capability."
        elif "training lead" in title_lower or "long line" in title_lower:
            budget = "A standard nylon lead and a basic biothane long line are affordable and effective. Both are easy to clean and dry quickly after muddy walks."
            premium = "Leather leads, shock-absorbing bungee leads, and multi-function leads with padded handles improve comfort on longer walks. Worth the upgrade for dogs walked frequently or owners with joint issues in their hands."
        elif "puppy" in title_lower:
            budget = "An adjustable nylon collar and a simple puppy harness are cost-effective choices since puppies outgrow gear quickly. Buy for fit, not for longevity, at this stage."
            premium = "Growth-adjustable harnesses with wider size ranges reduce the number of replacements needed. Worth considering for large breeds that will grow significantly over several months."
        elif "lead" in title_lower:
            budget = "A standard 1.2m nylon lead with a secure clip is durable, washable, and costs very little. It handles most everyday walking situations perfectly well."
            premium = "Leather leads, padded-handle leads, and waterproof biothane options feel better in the hand and last for years. A worthwhile purchase once your dog walks reliably and you want long-term comfort."
        else:
            budget = "A nylon harness with adjustable straps and a sturdy clip is all most dogs need for comfortable walks. Focus on correct fit rather than price."
            premium = "Padded, reflective, and multi-clip harnesses offer better comfort and versatility for active dogs. Worth the investment for daily use and long walks."

    # ── DOG BEDS ──
    elif cluster == "Dog Beds":
        if "orthopaedic" in title_lower or "orthop" in title_lower or "joint" in title_lower:
            budget = "An egg-crate foam bed provides basic pressure relief at a fraction of the cost of memory foam. Adequate for dogs with mild stiffness who need some extra support."
            premium = "Genuine memory foam or gel-infused orthopaedic beds offer superior joint support and pressure relief. A worthwhile investment for dogs with diagnosed arthritis, hip dysplasia, or post-surgery recovery needs."
        elif "cooling" in title_lower or "temperature" in title_lower:
            budget = "A basic elevated mesh bed allows airflow underneath and provides effective passive cooling at low cost. Easy to clean with a hose and suitable for indoor or outdoor use."
            premium = "Gel-infused cooling mats and self-cooling beds with phase-change materials offer more effective temperature regulation. Worth the upgrade for brachycephalic breeds or dogs in consistently warm environments."
        elif "puppy" in title_lower or "crate" in title_lower:
            budget = "An inexpensive polyester-filled crate mat with a washable cover is ideal for puppies. Expect to replace it as your puppy grows, so there is no need to invest heavily at this stage."
            premium = "Chew-resistant, waterproof beds with reinforced seams survive the puppy phase better and can last into adulthood. Worth considering if you want one bed that grows with your dog."
        elif "size" in title_lower or "sizing" in title_lower or "measure" in title_lower:
            budget = "A simple cushion or flat mat in the correct size gives your dog a comfortable sleeping space without a large outlay. Prioritise getting the right size over a premium brand."
            premium = "Custom-sized or made-to-measure beds ensure a perfect fit, especially for unusually shaped dogs or non-standard sleeping areas. Worth considering if standard sizes do not suit your dog or space."
        elif "material" in title_lower or "foam" in title_lower:
            budget = "Polyester-filled beds are light, inexpensive, and machine washable. They suit young, healthy dogs perfectly well. Replace when the filling compresses and no longer springs back."
            premium = "CertiPUR-certified memory foam with a high-density base provides lasting support and does not flatten over time. A sound investment for senior dogs or breeds prone to joint issues."
        elif "complete guide" in title_lower or ("best" in title_lower and "bed" in title_lower):
            budget = "A simple bolster bed with a polyester fill and washable cover meets most dogs' needs. Focus on correct sizing and washability rather than premium materials at this stage."
            premium = "Memory foam beds with removable, machine-washable covers and waterproof liners last longer and provide better support. Worth the cost for your dog's permanent, long-term sleeping spot."
        else:
            budget = "A basic cushion or mat bed with a washable cover is a good starting point. It covers the essentials: comfort, warmth, and easy cleaning."
            premium = "Orthopaedic or memory foam beds with removable covers and waterproof liners provide long-term comfort and durability. Worth the investment for senior dogs or heavy daily use."
    else:
        return None

    block = (
        '<!-- wp:group {"style":{"color":{"background":"#faf5ff"},"border":{"radius":"6px","width":"1px","color":"#e9d5ff"},"spacing":{"padding":{"top":"16px","bottom":"16px","left":"20px","right":"20px"},"margin":{"top":"20px","bottom":"20px"}}},"layout":{"type":"constrained"}} -->\n'
        '<div class="wp-block-group has-border-color has-background" style="border-color:#e9d5ff;border-width:1px;border-radius:6px;background-color:#faf5ff;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">\n'
        '<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"}}} -->\n'
        f'<p style="font-size:14px"><strong>Budget option:</strong> {budget}</p>\n'
        '<!-- /wp:paragraph -->\n'
        '<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"}}} -->\n'
        f'<p style="font-size:14px"><strong>Premium option:</strong> {premium}</p>\n'
        '<!-- /wp:paragraph -->\n'
        '</div>\n'
        '<!-- /wp:group -->'
    )
    return block


# ──────────────────────────────────────────────────────────────────────
# TRUST FOOTER DETECTION
# ──────────────────────────────────────────────────────────────────────

TRUST_FOOTER_MARKERS = [
    "Our Editorial Standards",
    "our editorial standards",
    "editorial standards",
    "Trust &amp; Transparency",
    "trust-footer",
    "How We Research",
    "how we research",
]

def find_trust_footer_position(content):
    """Find the position of the trust footer in the content."""
    content_lower = content.lower()
    for marker in TRUST_FOOTER_MARKERS:
        pos = content_lower.find(marker.lower())
        if pos != -1:
            # Find the start of the block containing this marker
            # Walk backwards to find the start of the wp:group or wp:heading
            search_region = content[:pos]
            # Look for the nearest block start before this marker
            for block_start in ["<!-- wp:group", "<!-- wp:heading", "<!-- wp:separator"]:
                idx = search_region.rfind(block_start)
                if idx != -1:
                    return idx
            return pos
    return -1


# ──────────────────────────────────────────────────────────────────────
# MAIN PROCESSING
# ──────────────────────────────────────────────────────────────────────

def process_post(post_id, cluster, log_rows):
    """Fetch, analyze, enrich, and update a single post."""
    print(f"\n{'='*60}")
    print(f"Processing post {post_id} (cluster: {cluster})")

    # Fetch post
    data = api_get(f"posts/{post_id}?context=edit")
    if "id" not in data:
        print(f"  ERROR: Could not fetch post {post_id}")
        log_rows.append([post_id, "FETCH_ERROR", cluster, "no", "no", "no", "no", "error"])
        return
    time.sleep(DELAY)

    title = data["title"]["raw"]
    content = data["content"]["raw"]
    print(f"  Title: {title}")
    print(f"  Content length: {len(content)} chars")

    # Analyze existing elements
    content_lower = content.lower()
    has_table = "<table" in content_lower or "wp:table" in content_lower
    has_at_a_glance = "at a glance" in content_lower
    has_beginner = "if you're a beginner" in content_lower or "if you&#8217;re a beginner" in content_lower or "beginner" in content_lower.split("if you")[0] if "if you" in content_lower else False
    # More precise beginner check
    has_beginner = ("if you're a beginner" in content_lower or
                    "if you&#8217;re a beginner" in content_lower or
                    "if you&rsquo;re a beginner" in content_lower)
    has_budget_premium = ("budget option" in content_lower and "premium option" in content_lower)

    print(f"  Has table: {has_table}")
    print(f"  Has At a Glance: {has_at_a_glance}")
    print(f"  Has Beginner Rec: {has_beginner}")
    print(f"  Has Budget/Premium: {has_budget_premium}")

    # Generate missing blocks
    blocks_to_add_before_footer = []
    blocks_to_add_after_first_para = []

    comparison_added = "no"
    at_a_glance_added = "no"
    beginner_added = "no"
    budget_premium_added = "no"

    if not has_table:
        table_block = generate_comparison_table(title, cluster)
        if table_block:
            blocks_to_add_before_footer.append(table_block)
            comparison_added = "yes"
            print("  -> Will add comparison table")

    if not has_at_a_glance:
        glance_block = generate_at_a_glance(title, cluster)
        if glance_block:
            blocks_to_add_after_first_para.append(glance_block)
            at_a_glance_added = "yes"
            print("  -> Will add At a Glance")

    if not has_beginner:
        beginner_block = generate_beginner_rec(title, cluster)
        if beginner_block:
            blocks_to_add_before_footer.append(beginner_block)
            beginner_added = "yes"
            print("  -> Will add Beginner Recommendation")

    if not has_budget_premium:
        bp_block = generate_budget_premium(title, cluster)
        if bp_block:
            blocks_to_add_before_footer.append(bp_block)
            budget_premium_added = "yes"
            print("  -> Will add Budget vs Premium")

    if not blocks_to_add_before_footer and not blocks_to_add_after_first_para:
        print("  -> All elements already present, skipping")
        log_rows.append([post_id, title, cluster, comparison_added, at_a_glance_added, beginner_added, budget_premium_added, "already_complete"])
        return

    # Insert At a Glance after first paragraph
    new_content = content
    if blocks_to_add_after_first_para:
        # Find end of first paragraph block
        first_para_end = new_content.find("<!-- /wp:paragraph -->")
        if first_para_end != -1:
            insert_pos = first_para_end + len("<!-- /wp:paragraph -->")
            glance_insert = "\n\n" + "\n\n".join(blocks_to_add_after_first_para) + "\n\n"
            new_content = new_content[:insert_pos] + glance_insert + new_content[insert_pos:]
            print(f"  -> Inserted At a Glance after first paragraph (pos {insert_pos})")
        else:
            # Fallback: insert at beginning
            glance_insert = "\n\n".join(blocks_to_add_after_first_para) + "\n\n"
            new_content = glance_insert + new_content
            print("  -> Inserted At a Glance at beginning (no paragraph found)")

    # Insert remaining blocks before trust footer
    if blocks_to_add_before_footer:
        footer_pos = find_trust_footer_position(new_content)
        insert_text = "\n\n" + "\n\n".join(blocks_to_add_before_footer) + "\n\n"
        if footer_pos != -1:
            new_content = new_content[:footer_pos] + insert_text + new_content[footer_pos:]
            print(f"  -> Inserted {len(blocks_to_add_before_footer)} block(s) before trust footer (pos {footer_pos})")
        else:
            # Fallback: append to end
            new_content = new_content + insert_text
            print(f"  -> Appended {len(blocks_to_add_before_footer)} block(s) to end (no trust footer found)")

    # Update the post
    update_data = {"content": new_content}
    success = api_update(post_id, update_data)
    time.sleep(DELAY)

    status = "updated" if success else "update_failed"
    print(f"  -> Status: {status}")
    log_rows.append([post_id, title, cluster, comparison_added, at_a_glance_added, beginner_added, budget_premium_added, status])


def main():
    print("=" * 60)
    print("Phase 10AK: Weakest Cluster Rescue")
    print("Target: Dog Grooming, Dog Harnesses, Dog Beds")
    print("=" * 60)

    log_rows = []

    total_posts = sum(len(v) for v in POSTS.values())
    processed = 0

    for cluster, post_ids in POSTS.items():
        print(f"\n{'#'*60}")
        print(f"# CLUSTER: {cluster} ({len(post_ids)} posts)")
        print(f"{'#'*60}")

        for post_id in post_ids:
            processed += 1
            print(f"\n[{processed}/{total_posts}]")
            try:
                process_post(post_id, cluster, log_rows)
            except Exception as e:
                print(f"  EXCEPTION: {e}")
                log_rows.append([post_id, "EXCEPTION", cluster, "no", "no", "no", "no", f"error: {e}"])
            time.sleep(DELAY)

    # Write log
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "cluster", "comparison_added", "at_a_glance_added", "beginner_rec_added", "budget_premium_added", "status"])
        writer.writerows(log_rows)

    print(f"\n{'='*60}")
    print(f"COMPLETE: Processed {processed} posts")
    print(f"Log written to: {LOG_FILE}")

    # Summary
    updated = sum(1 for r in log_rows if r[7] == "updated")
    already = sum(1 for r in log_rows if r[7] == "already_complete")
    errors = sum(1 for r in log_rows if "error" in r[7])
    print(f"Updated: {updated}, Already complete: {already}, Errors: {errors}")

    # Block counts
    tables = sum(1 for r in log_rows if r[3] == "yes")
    glances = sum(1 for r in log_rows if r[4] == "yes")
    beginners = sum(1 for r in log_rows if r[5] == "yes")
    budgets = sum(1 for r in log_rows if r[6] == "yes")
    print(f"Comparison tables added: {tables}")
    print(f"At a Glance boxes added: {glances}")
    print(f"Beginner recs added: {beginners}")
    print(f"Budget vs Premium added: {budgets}")
    print(f"Total new blocks: {tables + glances + beginners + budgets}")


if __name__ == "__main__":
    main()
