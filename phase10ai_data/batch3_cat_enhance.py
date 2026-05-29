#!/usr/bin/env python3
"""
Phase 10AI Batch 3: Cat Toys, Cat Supplies, Indoor Cats content enhancement.
Adds authority blocks (At a Glance, Why This Matters, What We Considered,
Troubleshooting, When to Seek Help, Key Takeaways, upgraded trust footer).
"""

import csv
import json
import os
import re
import subprocess
import tempfile
import time
import html

# ── credentials ──
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
DATA_DIR = "/var/lib/freelancer/projects/40416335/phase10ai_data"
INVENTORY = "/var/lib/freelancer/projects/40416335/phase10af_data/post_authority_inventory.csv"
LOG_FILE = os.path.join(DATA_DIR, "batch3_cat_clusters_log.csv")
TARGET_CLUSTERS = {"Cat Toys", "Cat Supplies", "Indoor Cats"}

# ── API helpers ──
def api_get(endpoint):
    """GET from WP REST API using curl subprocess."""
    url = f"{WP_BASE}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise Exception(f"curl GET failed: {result.stderr}")
    return json.loads(result.stdout)


def api_post(endpoint, data):
    """POST to WP REST API using curl subprocess with temp file."""
    url = f"{WP_BASE}/{endpoint}"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        tmpfile = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmpfile}",
             url],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            raise Exception(f"curl POST failed: {result.stderr}")
        resp = json.loads(result.stdout)
        if "id" not in resp:
            raise Exception(f"Update failed: {json.dumps(resp)[:500]}")
        return resp
    finally:
        os.unlink(tmpfile)


# ── content generation ──

def gen_at_a_glance(title, content_text):
    """Generate 3-5 bullet points summarizing the post's key information."""
    title_lower = title.lower()

    # Cat Toys posts
    if "best cat toys uk" in title_lower:
        return [
            "Covers wand toys, puzzle feeders, electronic options, and plush toys suitable for UK cats",
            "Focuses on safety-tested products that meet UKCA and CE marking standards",
            "Includes guidance on matching toy type to your cat's natural hunting instincts",
            "Price ranges covered from budget-friendly to premium enrichment options",
            "Recommendations account for indoor-only cats, kittens, seniors, and multi-cat households"
        ]
    elif "best interactive cat toys uk" in title_lower and "indoor" not in title_lower:
        return [
            "Reviews wand toys, puzzle feeders, and electronic interactive toys available in the UK",
            "Explains how interactive play supports mental stimulation and weight management",
            "Safety considerations for battery-operated and motorised cat toys",
            "Guidance on supervised vs unsupervised interactive toy use",
            "Suitable for cats of all ages including kittens and senior cats"
        ]
    elif "best interactive cat toys for indoor cats" in title_lower:
        return [
            "Focuses specifically on engagement toys designed for cats that live exclusively indoors",
            "Covers puzzle feeders, wand toys, electronic chasers, and treat-dispensing options",
            "Indoor cats need 15-30 minutes of active play daily according to welfare guidelines",
            "Addresses boredom-related behavioural issues in house cats",
            "All recommended products are available from UK retailers"
        ]
    elif "best catnip toys" in title_lower:
        return [
            "Explains how catnip (Nepeta cataria) affects cats and why roughly 50-70% of cats respond",
            "Reviews stuffed catnip toys, catnip sprays, and silvervine alternatives",
            "Covers safety considerations including moderation and kitten suitability",
            "Guides on refreshing dried catnip toys to maintain potency",
            "Includes UK-sourced and UK-available catnip product options"
        ]
    elif "cat toy rotation" in title_lower:
        return [
            "Explains the science behind toy novelty and how rotation prevents boredom",
            "Provides a practical weekly rotation schedule for different toy types",
            "Covers how many toys to keep in active rotation versus stored away",
            "Addresses signs that your cat has lost interest in current toys",
            "Relevant for both indoor-only cats and cats with outdoor access"
        ]
    elif "choose the right cat toy" in title_lower:
        return [
            "Matches cat toy types to personality traits: hunters, chasers, wrestlers, and observers",
            "Covers age-related play preferences from kittens to senior cats",
            "Explains how breed characteristics can influence toy preferences",
            "Includes safety sizing guidance to prevent choking or ingestion risks",
            "Helps owners identify their cat's dominant play style through observation"
        ]
    elif "cat toys faq" in title_lower:
        return [
            "Answers the most common questions UK cat owners ask about toys and play",
            "Covers safety, frequency of play, toy replacement, and supervision needs",
            "Addresses concerns about catnip safety and age-appropriate toys",
            "Provides guidance on toy budgets and DIY alternatives",
            "References UK veterinary and welfare organisation recommendations"
        ]
    elif "kitten vs adult cat toys" in title_lower:
        return [
            "Explains developmental differences that affect toy suitability at different life stages",
            "Kittens need softer, smaller toys that support teething and coordination development",
            "Adult cats benefit from puzzle feeders and hunting-simulation toys",
            "Senior cats may need gentler, slower-moving toy options",
            "Safety sizing differs significantly between kittens and adult cats"
        ]
    elif "how often should you replace cat toys" in title_lower:
        return [
            "Provides a practical replacement timeline for different toy materials",
            "Identifies specific signs of wear that indicate a toy has become unsafe",
            "Fabric and feather toys typically need replacing every 1-3 months",
            "Hard plastic and rubber toys can last 6-12 months with regular inspection",
            "Explains when damaged toys pose choking, ingestion, or injury risks"
        ]
    elif "diy cat toys" in title_lower:
        return [
            "Provides safe homemade toy ideas using common household materials",
            "Covers cardboard puzzles, sock toys, paper bag tunnels, and wand toys",
            "Lists materials to avoid including string, rubber bands, and small buttons",
            "DIY toys should always be used under supervision and inspected for damage",
            "Cost-effective enrichment options suitable for all cat ages"
        ]
    elif "wall-mounted cat scratcher" in title_lower:
        return [
            "Reviews vertical scratching solutions that save floor space in UK homes",
            "Covers sisal, carpet, and cardboard wall-mounted options",
            "Installation guidance for different wall types including plasterboard",
            "Ideal for small flats and multi-cat households where floor space is limited",
            "Explains why vertical scratching is important for shoulder and spine health"
        ]
    elif "cardboard cat scratcher" in title_lower:
        return [
            "Reviews budget-friendly corrugated cardboard scratchers available in the UK",
            "Cardboard scratchers typically cost £5-£15 and last 2-6 months",
            "Many cats prefer the texture of corrugated cardboard over sisal or carpet",
            "Covers flat, angled, and lounge-style cardboard scratcher designs",
            "Environmentally recyclable option compared to synthetic scratching materials"
        ]
    elif "cat scratching posts" in title_lower and "best" in title_lower:
        return [
            "Comprehensive guide to freestanding cat scratching posts available in the UK",
            "Covers sisal rope, sisal fabric, carpet, and wood scratching post options",
            "Height matters: posts should be tall enough for full-stretch scratching (minimum 60cm)",
            "Stability is critical — wobbly posts are quickly abandoned by cats",
            "Addresses placement strategy for redirecting scratching away from furniture"
        ]
    # Cat Supplies posts
    elif "cat litter disposal" in title_lower:
        return [
            "Reviews dedicated cat litter disposal bins and waste management systems for UK homes",
            "Covers odour-locking systems, biodegradable bag options, and standard disposal methods",
            "Explains UK council regulations on cat waste disposal (not suitable for compost or garden waste bins)",
            "Addresses hygiene considerations including toxoplasmosis risks from cat faeces",
            "Compares refill costs and long-term value of different disposal systems"
        ]
    elif "best cat litter uk" in title_lower and "tray" not in title_lower and "disposal" not in title_lower:
        return [
            "Compares clumping, non-clumping, silica crystal, wood pellet, and paper-based litters",
            "Covers dust levels, odour control, tracking, and flushability for UK plumbing",
            "Most cats prefer fine-grained, unscented clumping litter according to behavioural studies",
            "Addresses eco-friendly and biodegradable options available from UK retailers",
            "Includes guidance on litter depth (typically 5-7cm) and changing frequency"
        ]
    elif "cat litter tray" in title_lower:
        return [
            "Reviews open, hooded, top-entry, and corner litter trays available in the UK",
            "The general rule is one tray per cat plus one extra in multi-cat households",
            "Covers sizing — trays should be 1.5 times the length of the cat",
            "Addresses placement considerations for UK homes including flats and terraced houses",
            "Explains how tray type affects litter scatter, odour containment, and cleaning ease"
        ]
    elif "heated cat bed" in title_lower:
        return [
            "Reviews electrically heated and self-warming cat beds for UK winters",
            "Covers safety features including chew-resistant cords and auto-shutoff thermostats",
            "Particularly beneficial for senior cats, arthritic cats, and hairless breeds",
            "Explains the difference between mains-powered and self-heating (body-heat reflective) options",
            "All electrical products should carry UKCA or CE marking for UK safety compliance"
        ]
    elif "best cat beds uk" in title_lower:
        return [
            "Comprehensive guide to cat bed types: igloo, donut, bolster, hammock, and flat mat styles",
            "Most cats prefer enclosed or semi-enclosed beds that provide a sense of security",
            "Covers washability, material safety, and sizing for different cat breeds",
            "Addresses placement tips — cats prefer elevated, warm, and quiet sleeping spots",
            "Reviews options across budget, mid-range, and premium price points"
        ]
    elif "essential cat supplies" in title_lower:
        return [
            "Covers the core supplies every new cat owner in the UK needs from day one",
            "Includes feeding equipment, litter setup, scratching provision, and sleeping options",
            "Addresses microchipping requirements (compulsory in England from June 2024)",
            "Provides estimated startup costs for bringing a new cat home in the UK",
            "References Cats Protection and RSPCA guidance on essential cat welfare needs"
        ]
    # Indoor Cats posts
    elif "indoor cat care" in title_lower and "complete guide" in title_lower:
        return [
            "Comprehensive guide covering all aspects of keeping cats exclusively indoors in the UK",
            "Addresses environmental enrichment, exercise, mental stimulation, and social needs",
            "Indoor cats can live longer on average but face unique challenges including obesity and boredom",
            "Covers litter management, vertical space, and window access for house cats",
            "References Cats Protection and International Cat Care guidance on indoor cat welfare"
        ]
    elif "best indoor cat toys" in title_lower:
        return [
            "Curated selection of toys specifically designed for cats that live entirely indoors",
            "Indoor cats need dedicated play sessions to compensate for lack of outdoor hunting",
            "Covers puzzle feeders, wand toys, electronic toys, and solo-play options",
            "Addresses the recommended 15-30 minutes of daily interactive play for indoor cats",
            "All products reviewed are available from UK retailers and online stores"
        ]
    else:
        # Generic cat fallback
        return [
            "Practical guidance based on current UK veterinary and welfare standards",
            "Covers key considerations for cat owners in the United Kingdom",
            "References recommendations from Cats Protection and International Cat Care",
            "Includes safety and welfare information relevant to the topic",
            "Suitable for both new and experienced cat owners"
        ]


def gen_why_this_matters(title, cluster):
    """Generate 1-2 sentences on why this topic matters for UK cat owners."""
    title_lower = title.lower()

    if "best cat toys uk" in title_lower:
        return "Regular play is essential for cats' physical health and mental wellbeing. Cats Protection reports that insufficient stimulation is a leading contributor to behavioural problems and obesity in UK cats, making appropriate toy selection a genuine welfare concern."
    elif "best interactive cat toys uk" in title_lower and "indoor" not in title_lower:
        return "Interactive toys simulate the hunting sequence that cats are hardwired to perform — stalk, chase, pounce, and catch. International Cat Care emphasises that this type of play reduces stress, prevents obesity, and strengthens the bond between cat and owner."
    elif "best interactive cat toys for indoor cats" in title_lower:
        return "Indoor cats lack the natural stimulation that outdoor access provides, making dedicated interactive play critical for their welfare. The PDSA's PAW Report consistently highlights that many UK indoor cats do not receive enough mental enrichment, contributing to stress-related behaviours."
    elif "best catnip toys" in title_lower:
        return "Catnip provides a safe, non-addictive form of sensory enrichment that can encourage play in cats that are otherwise sedentary. Cats Protection notes that environmental enrichment, including appropriate use of catnip, supports the emotional wellbeing of domestic cats."
    elif "cat toy rotation" in title_lower:
        return "Cats are neophilic — they are naturally attracted to novelty, which means even favourite toys lose their appeal over time. Regularly rotating toys is a simple strategy recommended by International Cat Care to maintain engagement and prevent boredom-related behavioural issues."
    elif "choose the right cat toy" in title_lower:
        return "Not all cats play the same way, and mismatched toys often go unused while the cat remains under-stimulated. Understanding your cat's individual play style helps ensure they receive the mental and physical enrichment that Cats Protection identifies as essential for welfare."
    elif "cat toys faq" in title_lower:
        return "Misinformation about cat toys — from unsafe materials to incorrect play guidance — can put cats at risk of injury or ingestion. Having reliable, evidence-based answers helps UK owners make safer choices aligned with PDSA and Cats Protection welfare standards."
    elif "kitten vs adult cat toys" in title_lower:
        return "A kitten's play needs differ significantly from an adult cat's, and using the wrong toys at the wrong life stage can cause injury or developmental issues. International Cat Care advises that age-appropriate play supports healthy physical development and socialisation in young cats."
    elif "how often should you replace cat toys" in title_lower:
        return "Worn or damaged toys are one of the most common preventable hazards for cats, with risks including choking on loose parts and intestinal obstruction from ingested materials. The RSPCA advises regular toy inspection as part of responsible pet ownership."
    elif "diy cat toys" in title_lower:
        return "Homemade toys can provide excellent enrichment at minimal cost, but poorly chosen materials pose real dangers including string ingestion and chemical exposure. Cats Protection warns that linear foreign bodies (string, thread, ribbon) are a leading cause of emergency veterinary surgery in cats."
    elif "wall-mounted cat scratcher" in title_lower:
        return "Scratching is a fundamental feline need for claw maintenance, territory marking, and muscle stretching. International Cat Care states that providing appropriate scratching surfaces is essential welfare provision, and wall-mounted options are particularly valuable in smaller UK homes."
    elif "cardboard cat scratcher" in title_lower:
        return "Many cats show a strong preference for the texture of corrugated cardboard, and providing preferred scratching substrates reduces the likelihood of furniture damage. Cats Protection recommends offering multiple scratching options to meet this essential natural behaviour."
    elif "cat scratching posts" in title_lower:
        return "A scratching post is considered a basic welfare requirement for indoor cats by both Cats Protection and International Cat Care. Without appropriate scratching provision, cats may develop stress-related behaviours or redirect scratching to household furnishings."
    elif "cat litter disposal" in title_lower:
        return "Proper litter waste disposal is both a hygiene and public health matter — cat faeces can contain Toxoplasma gondii, which poses risks to pregnant women and immunocompromised individuals. The RSPCA advises that used cat litter should be double-bagged and placed in household waste, never flushed or composted."
    elif "best cat litter uk" in title_lower and "tray" not in title_lower:
        return "Litter type directly affects whether cats will reliably use their tray — inappropriate litter is a common cause of house soiling that leads to cats being surrendered to rescue centres. International Cat Care recommends fine-grained, unscented clumping litter based on feline preference research."
    elif "cat litter tray" in title_lower:
        return "Litter tray problems are the most common reason cats are referred to behaviourists in the UK. Cats Protection emphasises that tray type, size, number, and placement are all critical factors in preventing toileting issues that can damage the cat-owner relationship."
    elif "heated cat bed" in title_lower:
        return "Warmth is particularly important for senior cats and those with arthritis, as cold temperatures can worsen joint stiffness and pain. The PDSA notes that providing warm, comfortable resting areas supports the welfare of older and health-compromised cats during UK winters."
    elif "best cat beds uk" in title_lower:
        return "Cats spend up to 16 hours a day sleeping, making their bed one of the most-used items in any home. International Cat Care advises that providing appropriate resting places in quiet, elevated locations supports cats' natural need for security and undisturbed sleep."
    elif "essential cat supplies" in title_lower:
        return "Getting the right supplies before bringing a cat home reduces stress for both cat and owner during the settling-in period. Cats Protection recommends having all essential items in place at least 24 hours before the cat arrives."
    elif "indoor cat care" in title_lower:
        return "The number of indoor-only cats in the UK is increasing, particularly in urban areas. International Cat Care and Cats Protection both emphasise that indoor cats have specific welfare requirements around environmental enrichment, space utilisation, and mental stimulation that differ from cats with outdoor access."
    elif "best indoor cat toys" in title_lower:
        return "Indoor cats rely entirely on their owners for physical exercise and mental stimulation opportunities. The PDSA's annual PAW Report consistently finds that many UK indoor cats lack sufficient enrichment, which can lead to obesity, stress-related illness, and behavioural problems."
    else:
        return "Providing appropriate care and resources for cats is a responsibility recognised under the Animal Welfare Act 2006. UK welfare organisations including Cats Protection, the RSPCA, and the PDSA all emphasise that meeting cats' behavioural needs is as important as meeting their physical needs."


def gen_what_we_considered(title):
    """Generate criteria text for 'Best X' buying guides. Returns None if not applicable."""
    title_lower = title.lower()
    if "best" not in title_lower:
        return None

    if "best cat toys uk" in title_lower:
        return "We evaluated cat toys based on safety (material quality, small-part risks, UKCA/CE compliance), engagement level (ability to stimulate natural hunting behaviours), durability relative to price, and suitability across different cat ages and play styles. We also considered ease of cleaning and whether toys could be used for solo play or required owner participation."
    elif "best interactive cat toys uk" in title_lower and "indoor" not in title_lower:
        return "We assessed interactive toys on their ability to simulate natural prey movements, build quality and safety of moving parts, battery life for electronic options, and noise levels. We prioritised toys that encourage the full hunting sequence — stalk, chase, pounce, catch — as recommended by feline behaviourists."
    elif "best interactive cat toys for indoor cats" in title_lower:
        return "We focused on toys that address the specific enrichment deficit indoor cats face, evaluating engagement duration, ability to provide exercise, mental challenge level, and safety for unsupervised use. We also considered space requirements, as many UK indoor cats live in flats with limited room."
    elif "best catnip toys" in title_lower:
        return "We evaluated catnip toys based on the quality and potency of catnip used, construction durability (cats tend to kick and bite these vigorously), safety of materials including stitching strength, and value for money considering typical replacement frequency. We also considered alternatives like silvervine for the 30-50% of cats that don't respond to catnip."
    elif "best indoor cat toys" in title_lower:
        return "We assessed toys specifically for cats living entirely indoors, evaluating their ability to provide physical exercise, mental stimulation, and solo entertainment. We considered space requirements for UK flats, noise levels, safety for unsupervised play, and whether toys address common indoor-cat issues such as boredom and weight management."
    elif "wall-mounted cat scratcher" in title_lower:
        return "We assessed wall-mounted scratchers on mounting security across different wall types (plasterboard, brick, stud walls), scratching surface material and durability, height adjustability, visual appearance in UK home interiors, and ease of replacing worn scratch pads."
    elif "cardboard cat scratcher" in title_lower:
        return "We evaluated cardboard scratchers on corrugation density (affecting durability), stability during use, scatter mess levels, value for money relative to lifespan, and whether they included catnip to encourage initial use. We also considered recyclability and environmental credentials."
    elif "cat scratching posts" in title_lower:
        return "We assessed scratching posts on height (minimum 60cm for full-stretch scratching), base stability under vigorous use, scratching surface material (sisal rope vs sisal fabric vs carpet), durability, and value across budget to premium price points. We also considered aesthetics for integration into UK living spaces."
    elif "cat litter disposal" in title_lower:
        return "We evaluated disposal systems on odour containment effectiveness, refill bag costs and availability in the UK, capacity (suitable for one-cat vs multi-cat households), ease of use, and overall hygiene. We also considered environmental impact of refill bags and long-term running costs."
    elif "best cat litter uk" in title_lower and "tray" not in title_lower:
        return "We compared litters across clumping performance, dust levels (important for respiratory health), odour control, tracking outside the tray, environmental credentials, and price per kilogram. We also considered compatibility with UK plumbing for litters marketed as flushable and preferences identified in feline behaviour research."
    elif "cat litter tray" in title_lower:
        return "We assessed litter trays on size (minimum 1.5 times cat length), entry accessibility for kittens and senior cats, odour containment, litter scatter prevention, ease of cleaning, and suitability for different UK home layouts including flats. We also considered multi-cat household needs."
    elif "heated cat bed" in title_lower:
        return "We evaluated heated beds on temperature regulation and safety features (auto-shutoff, chew-resistant cords, low-voltage operation), warmth distribution, washability of covers, energy consumption, and UKCA/CE electrical safety compliance. We gave particular consideration to suitability for senior and arthritic cats."
    elif "best cat beds uk" in title_lower:
        return "We assessed cat beds on comfort and support quality, washability (essential for hygiene), sizing across cat breeds, material durability, and value for money. We also considered different bed styles (igloo, donut, bolster, flat) to match cats' individual sleeping preferences and the placement flexibility each design offers."
    elif "essential cat supplies" in title_lower:
        return "We evaluated essential supplies based on welfare necessity (items cats genuinely need versus nice-to-have accessories), quality relative to price, availability from UK retailers, and alignment with Cats Protection and RSPCA recommendations for new cat owners."
    else:
        return "We evaluated products based on build quality, safety compliance (UKCA/CE marking), value for money at UK retail prices, user feedback from verified purchasers, and alignment with welfare guidelines from organisations including Cats Protection and International Cat Care."


def gen_troubleshooting(title, cluster):
    """Generate 3-4 common problems with solutions."""
    title_lower = title.lower()

    if "cat toy" in title_lower or cluster == "Cat Toys":
        if "interactive" in title_lower:
            return """<strong>Cat ignores interactive toys:</strong> Try varying the speed and direction of movement — drag toys away from your cat rather than towards them to trigger the chase instinct. Cats are ambush predators, so partially hiding a wand toy behind furniture can reignite interest.

<strong>Cat becomes aggressive during play:</strong> If your cat redirects onto your hands or feet, immediately stop the session and walk away. Avoid using hands as toys. Resume play after a 5-minute cool-down period using a wand toy that keeps distance between your hands and the cat.

<strong>Electronic toy stops holding attention:</strong> Rotate electronic toys out of use for 1-2 weeks to restore novelty. Many battery-operated toys also work better on hard floors than carpet, so try changing the surface.

<strong>Cat only plays for a few seconds:</strong> Short play bursts are normal for cats — they are sprinters, not marathon runners. Aim for several 2-5 minute sessions rather than one long session, and always end play with a treat to complete the hunting sequence."""
        elif "catnip" in title_lower:
            return """<strong>Cat does not respond to catnip:</strong> Approximately 30-50% of cats lack the gene for catnip sensitivity. Try silvervine (Actinidia polygama) or valerian root as alternatives — many catnip-immune cats respond to these.

<strong>Catnip toy has lost its effect:</strong> Dried catnip loses potency over time. Place the toy in a sealed bag with fresh dried catnip for 24-48 hours to refresh it, or apply a catnip spray directly to the toy's surface.

<strong>Cat becomes aggressive after catnip exposure:</strong> Some cats experience an excitable or aggressive phase. Limit catnip sessions to 10-15 minutes and remove the toy once the active period passes. Not every cat enjoys the sensation.

<strong>Kitten shows no interest in catnip:</strong> Kittens under 3-6 months typically do not respond to catnip as the sensitivity develops with maturity. Wait until they are at least 6 months old before trying again."""
        elif "diy" in title_lower:
            return """<strong>Cat eats parts of homemade toys:</strong> Immediately remove the toy and monitor your cat. If you suspect ingestion of string, fabric, or other materials, contact your vet without delay — do not attempt to pull string from the mouth or rear end.

<strong>DIY toy falls apart quickly:</strong> Reinforce seams with double stitching and avoid glue, which can be toxic. For cardboard toys, use thicker corrugated board and replace them as soon as they start to disintegrate.

<strong>Cat prefers packaging over the toy:</strong> This is completely normal — many cats are more attracted to boxes, bags (with handles removed), and crinkly paper. Embrace this and create enrichment around these preferences.

<strong>Homemade wand toy string is too long:</strong> Keep strings under 30cm when attached to wand toys and always supervise use. Store wand toys out of reach between sessions, as trailing strings pose a serious strangulation and ingestion risk."""
        elif "scratcher" in title_lower or "scratching" in title_lower:
            return """<strong>Cat ignores the new scratcher:</strong> Place it near where your cat already scratches (often near sleeping areas or room entrances). Rub a small amount of catnip on the surface or hang a toy from it to encourage initial investigation.

<strong>Cat still scratches furniture despite having a scratcher:</strong> Your cat may prefer a different scratching angle or material. If they scratch sofa arms, they likely want vertical scratching; if they scratch carpets, try a horizontal scratcher. Some cats prefer sisal over cardboard or vice versa.

<strong>Scratching post wobbles during use:</strong> An unstable post will be abandoned quickly. Ensure the base is weighted or wide enough, or consider wall-mounting for maximum stability. Some owners secure freestanding posts to a wall bracket for added security.

<strong>Cardboard scratcher creates too much mess:</strong> Place a mat or old towel underneath to catch debris. Corrugated cardboard naturally sheds — this is normal use rather than a fault. Vacuum around the scratcher every few days."""
        elif "replace" in title_lower or "often" in title_lower:
            return """<strong>Unsure whether a toy is still safe:</strong> Check for loose threads, exposed stuffing, cracked plastic, or detached small parts. If in doubt, replace it — the cost of a new toy is far less than an emergency vet visit for foreign body ingestion.

<strong>Cat seems to prefer old, damaged toys:</strong> The scent and familiarity are comforting. Replace like-for-like where possible, and rub the new toy against the cat's bedding to transfer familiar scent before introducing it.

<strong>Feather toys lose feathers quickly:</strong> Feather toys are inherently short-lived. Consider them consumable enrichment items and budget accordingly. Always supervise feather toy play, as ingested feathers can cause digestive irritation.

<strong>Rubber toy has become sticky or discoloured:</strong> This indicates material degradation. Replace immediately, as deteriorating rubber can release harmful compounds and break apart more easily during play."""
        elif "kitten" in title_lower:
            return """<strong>Kitten chews through toys quickly:</strong> Teething kittens (3-6 months) chew more aggressively. Provide purpose-made kitten teething toys and check all toys twice daily for damage. Remove any toy with exposed stuffing or detached parts.

<strong>Kitten plays too roughly with adult cat's toys:</strong> Keep larger, heavier toys away from kittens. Supervise shared play sessions and provide kitten-sized alternatives. Kittens can choke on toys designed for adult cats.

<strong>Kitten loses interest in toys very quickly:</strong> Short attention spans are normal for kittens. Offer 5-10 minute play sessions multiple times daily rather than one long session. Rotating toys every few days maintains novelty.

<strong>Kitten attacks feet and hands instead of toys:</strong> This is learned behaviour that becomes problematic in adult cats. Always redirect onto an appropriate toy immediately. Never use fingers or toes as play objects, even if it seems cute at the kitten stage."""
        else:
            return """<strong>Cat has lost interest in all toys:</strong> Rotate toys weekly, keeping only 3-4 available at a time and storing the rest. Reintroduce stored toys after 1-2 weeks — the novelty effect often restores interest. Also ensure your cat is not unwell, as sudden loss of playfulness can indicate illness.

<strong>Cat only plays at inconvenient times (e.g., 4am):</strong> Cats are crepuscular, meaning they are most active at dawn and dusk. Schedule a vigorous 10-15 minute play session before your bedtime, followed by a small meal, to help shift their active period.

<strong>Toys keep disappearing under furniture:</strong> This is extremely common. Consider toys that are too large to fit under sofas, or use furniture gap blockers. Check under furniture regularly — forgotten toys with small parts can become hazards for small children or other pets.

<strong>Cat prefers non-toy items (hair ties, bottle caps):</strong> These items pose serious choking and ingestion risks. Remove them from accessible areas and provide safe alternatives that mimic the same properties — lightweight, small, and easy to bat around."""

    elif cluster == "Cat Supplies":
        if "litter disposal" in title_lower:
            return """<strong>Disposal bin still smells despite being sealed:</strong> Check that the lid mechanism is closing fully and that bags are being twisted or sealed correctly. Clean the inside of the bin with a mild disinfectant weekly. Some systems rely on specific refill cassettes — generic replacements may not seal as effectively.

<strong>Refill bags for the system are expensive:</strong> Calculate the annual refill cost before purchasing a dedicated system. Standard nappy bags or biodegradable dog waste bags can work as alternatives for basic pail-style disposal units, reducing ongoing costs significantly.

<strong>Unsure whether cat litter can go in council green waste:</strong> No — used cat litter should never be placed in garden waste, recycling, or compost bins. It should be double-bagged and placed in general household waste. Cat faeces can contain Toxoplasma gondii parasites that survive composting temperatures.

<strong>Litter bin attracts flies in warm weather:</strong> Empty and clean the bin more frequently during summer months. A small amount of bicarbonate of soda in the base between bag changes helps reduce odour that attracts insects."""
        elif "cat litter uk" in title_lower and "tray" not in title_lower:
            return """<strong>Cat refuses to use new litter type:</strong> Cats dislike sudden changes. Transition gradually by mixing 25% new litter with 75% old, increasing the ratio over 7-10 days. If the cat still refuses, they may simply prefer the original type.

<strong>Excessive dust from litter:</strong> Dust can irritate both feline and human respiratory systems. Switch to a low-dust formula (look for "99% dust-free" labelling). Wood pellet and recycled paper litters generally produce less airborne dust than clay.

<strong>Litter tracks throughout the house:</strong> Use a litter-trapping mat outside the tray entrance. Top-entry trays also significantly reduce tracking. Larger granule litters (wood pellets, silica crystals) track less than fine-grained clumping clay.

<strong>Strong ammonia odour despite regular cleaning:</strong> Scoop clumps at least twice daily and fully replace all litter every 1-2 weeks. If odour persists despite good cleaning habits, consult your vet — unusually strong urine odour can indicate urinary tract issues."""
        elif "litter tray" in title_lower:
            return """<strong>Cat toilets outside the litter tray:</strong> Ensure you have enough trays (one per cat plus one extra), that they are placed in quiet low-traffic areas, and that the tray size is adequate (1.5 times cat length). If the problem persists, consult your vet to rule out medical causes before assuming a behavioural issue.

<strong>Cat refuses to use a hooded tray:</strong> Some cats feel trapped in enclosed trays, especially in multi-cat homes where they cannot see approaching cats. Try removing the hood or switching to an open tray. Not every cat appreciates a covered toilet.

<strong>Tray is difficult for senior cat to access:</strong> Older or arthritic cats may struggle with high-sided trays or top-entry designs. Switch to a tray with a low front entry (under 10cm lip height) and place it on the same floor as the cat's main living area.

<strong>Litter tray odour in a small flat:</strong> Use a high-quality clumping litter, scoop twice daily, and consider a carbon-filter-equipped hooded tray. Placing the tray away from eating and sleeping areas is essential. A nearby small air purifier can also help in confined spaces."""
        elif "heated cat bed" in title_lower:
            return """<strong>Cat won't use the heated bed:</strong> Place the bed in a location your cat already sleeps in, and add a piece of your worn clothing for familiar scent. Some cats are initially suspicious of the warmth — leave it switched on for a few days without forcing interaction.

<strong>Concerned about electrical safety:</strong> Only use heated beds with UKCA or CE marking. Check the cord regularly for bite marks or damage. Low-voltage (12V) heated pads are safer than mains-voltage options, especially for cats that chew.

<strong>Heated bed runs constantly and increases energy bills:</strong> Most quality heated beds use only 4-10 watts — comparable to a nightlight. Look for models with thermostatic controls that only heat when the cat is present, reducing both cost and overheating risk.

<strong>Self-warming bed does not feel warm to the touch:</strong> Self-warming beds use reflective layers to return body heat and will not feel warm when empty. They need the cat's body weight and heat to function. They are best suited to cats that already have a preferred sleeping spot."""
        elif "best cat beds" in title_lower:
            return """<strong>Cat ignores the new bed:</strong> Place it where your cat already sleeps. Add familiar-scented bedding and avoid washing the bed's cover immediately — let your cat's scent accumulate first. Some cats take days or weeks to adopt a new bed.

<strong>Cat bed develops odour quickly:</strong> Choose beds with removable, machine-washable covers. Wash covers fortnightly at 30-40°C. Beds without removable covers can be freshened with a pet-safe fabric spray between washes but will eventually need replacing.

<strong>Unsure which bed style your cat prefers:</strong> Observe where and how your cat currently sleeps. Cats that curl up tightly often prefer donut or igloo beds. Cats that sprawl prefer flat mats or bolster beds with low sides. Offer two different styles initially and see which gets used.

<strong>Bed filling goes flat over time:</strong> Polyester fibre fills compress with use. Look for beds with memory foam or high-density polyester inserts that retain shape longer. Some beds have zip access for adding replacement filling."""
        elif "essential cat supplies" in title_lower:
            return """<strong>Overwhelmed by the number of products available:</strong> Focus on the five essentials first: food and water bowls, litter tray and litter, scratching post, carrier, and a safe sleeping area. Everything else can be added gradually as you learn your cat's preferences.

<strong>New cat will not eat or drink:</strong> This is common in the first 24-48 hours due to stress. Place food and water in a quiet room and leave the cat undisturbed. If refusal continues beyond 48 hours, contact your vet — cats should not go without food for extended periods as they risk hepatic lipidosis.

<strong>Unsure whether to buy kitten-specific or adult products:</strong> Kittens need kitten-formulated food (higher protein and calorie content), smaller litter trays, and appropriately sized toys. Beds, carriers, and scratching posts can usually be adult-sized from the start.

<strong>Cat rejects the carrier:</strong> Leave the carrier open in a living area with bedding inside so the cat can explore it voluntarily. Feed treats near and inside the carrier. Making it a normal part of the environment reduces stress when vet visits are needed."""
        else:
            return """<strong>Cat rejects a newly purchased product:</strong> Cats are creatures of habit. Introduce new items gradually alongside existing ones rather than replacing everything at once. Adding familiar scent (bedding, clothing) can help acceptance.

<strong>Product does not match the online description:</strong> Check the retailer's returns policy. UK consumer law gives you 14 days to return online purchases. Measure your cat and compare against the listed product dimensions before ordering.

<strong>Unsure about product safety standards:</strong> Look for UKCA or CE marking on any manufactured product. Avoid products with strong chemical odours, loose small parts, or materials not designed for pet use. When in doubt, check the manufacturer's safety testing claims.

<strong>Product wears out faster than expected:</strong> Document the issue and contact the retailer — UK consumer rights legislation covers products that are not of satisfactory quality. Keep receipts and photographs for any warranty or returns claim."""

    elif cluster == "Indoor Cats":
        if "indoor cat care" in title_lower:
            return """<strong>Indoor cat seems lethargic or bored:</strong> Increase environmental enrichment — add vertical climbing spaces, puzzle feeders, and schedule at least two 15-minute interactive play sessions daily. Boredom in indoor cats is a genuine welfare concern flagged by Cats Protection.

<strong>Indoor cat is gaining weight:</strong> Indoor cats are more prone to obesity due to reduced activity. Review portion sizes against feeding guidelines, switch to an indoor-formula food if appropriate, and increase daily play. Consult your vet if weight gain continues despite adjustments.

<strong>Cat meows excessively at doors or windows:</strong> This may indicate frustration with confinement. Enhance the indoor environment with window perches, cat TV (bird feeder outside a window), and new enrichment. Consider whether a secure catio or harness-walking could be appropriate.

<strong>Indoor cat urinates outside the litter tray:</strong> Inappropriate toileting in indoor cats often stems from stress, insufficient tray provision, or medical issues. Ensure one tray per cat plus one extra, placed in quiet areas. If the behaviour is new, see your vet to rule out urinary tract problems."""
        else:
            return """<strong>Indoor cat becomes hyperactive at night:</strong> Schedule an active play session 30-60 minutes before your bedtime, followed by a small meal. This mimics the natural hunt-eat-sleep cycle and can significantly reduce nighttime activity.

<strong>Cat scratches furniture despite having scratching posts:</strong> Ensure you have both vertical and horizontal scratching options positioned near the furniture being targeted. Temporarily cover the furniture with double-sided tape or a scratch deterrent while redirecting to appropriate surfaces.

<strong>Two indoor cats are not getting along:</strong> In multi-cat indoor households, ensure each cat has their own resources (food bowl, water bowl, litter tray, resting area) in separate locations. Cats Protection recommends at least one of each resource per cat plus one extra, placed in different rooms.

<strong>Indoor cat seems stressed or hides constantly:</strong> Provide elevated hiding spots (shelves, cat trees) and quiet retreat areas. Avoid forcing interaction. If hiding persists or is a new behaviour, consult your vet — hiding can indicate pain or illness."""
    else:
        return """<strong>Unsure if the product is right for your cat:</strong> Consider your cat's age, size, health status, and individual preferences. Most reputable UK retailers offer returns within 14 days for unused items.

<strong>Cat shows no interest in new items:</strong> Place new products near existing favourites and allow the cat to investigate at their own pace. Adding familiar scent from their bedding can speed up acceptance.

<strong>Product seems lower quality than described:</strong> Check UKCA/CE marking compliance and contact the retailer if the product does not match its description. UK consumer protection law covers goods that are not as described.

<strong>Concerned about product safety:</strong> Remove any small detachable parts, check for sharp edges, and supervise initial use. If a product causes an adverse reaction, stop use immediately and consult your vet if needed."""


def gen_when_to_seek_help(title, cluster):
    """Generate 1-2 sentences about when to consult a vet."""
    title_lower = title.lower()

    if "toy" in title_lower or "play" in title_lower or cluster == "Cat Toys":
        if "scratcher" in title_lower or "scratching" in title_lower:
            return "If your cat suddenly stops scratching entirely, scratches obsessively in one spot, or shows signs of pain when stretching, consult your vet. Changes in scratching behaviour can indicate arthritis, claw problems, or skin conditions. Cats Protection advises that any sudden behaviour change warrants a veterinary check."
        elif "kitten" in title_lower:
            return "If a kitten shows persistent lethargy, refuses to play for more than 24 hours, has difficulty walking or jumping, or chews and swallows non-food items compulsively, seek veterinary advice promptly. The PDSA notes that kittens can deteriorate quickly, so early intervention is important."
        else:
            return "If your cat suddenly loses all interest in play, shows signs of pain during movement, or you suspect they have swallowed part of a toy, contact your vet immediately. The PDSA advises that sudden behavioural changes — including loss of playfulness — can be early signs of illness or pain."
    elif "litter" in title_lower:
        return "If your cat strains to urinate, passes blood in urine, toilets outside the tray suddenly, or visits the tray frequently without producing urine, seek emergency veterinary attention. Cats Protection warns that urinary blockage is a life-threatening emergency, particularly in male cats."
    elif "bed" in title_lower:
        return "If your cat suddenly changes sleeping patterns dramatically — sleeping far more than usual, hiding in unusual locations, or refusing to lie down comfortably — consult your vet. The PDSA notes that changes in sleeping behaviour can indicate pain, illness, or cognitive decline in older cats."
    elif "essential" in title_lower or "supplies" in title_lower:
        return "If your new cat refuses food for more than 48 hours, shows signs of respiratory infection (sneezing, discharge), has diarrhoea lasting more than 24 hours, or seems excessively lethargic, contact your vet promptly. Cats Protection advises registering with a vet before bringing your cat home so that help is available immediately if needed."
    elif cluster == "Indoor Cats":
        return "If your indoor cat shows signs of extreme stress (over-grooming causing bald patches, persistent hiding, aggression, or inappropriate toileting), or develops weight changes, breathing difficulties, or lethargy, consult your vet. International Cat Care emphasises that indoor cats should have health checks at least annually, as early signs of illness are easily missed without outdoor activity as a comparison."
    else:
        return "If your cat displays sudden changes in behaviour, appetite, or energy levels, consult your vet. The PDSA recommends at least annual veterinary health checks for all cats, with more frequent visits for senior cats over 11 years of age."


def gen_key_takeaways(title, cluster):
    """Generate 4-6 actionable takeaways."""
    title_lower = title.lower()

    if "best cat toys uk" in title_lower:
        return [
            "Match toy types to your cat's natural play style — observe whether they prefer chasing, pouncing, wrestling, or batting",
            "Rotate toys weekly and keep only 3-4 available at a time to maintain novelty and engagement",
            "Always supervise play with wand toys, string toys, and small parts; store these out of reach between sessions",
            "Schedule at least two 10-15 minute play sessions daily, especially for indoor cats",
            "Inspect toys regularly for damage and replace immediately when stuffing, feathers, or small parts become loose",
            "End each play session with a treat or small meal to complete the natural hunt-catch-eat cycle"
        ]
    elif "best interactive cat toys uk" in title_lower and "indoor" not in title_lower:
        return [
            "Interactive play strengthens the cat-owner bond while providing essential physical and mental exercise",
            "Vary toy speed and movement patterns to mimic real prey behaviour — drag away rather than towards your cat",
            "Let your cat catch the toy regularly during play to prevent frustration and maintain motivation",
            "Electronic interactive toys complement but should not replace hands-on play sessions with you",
            "Store wand and string toys out of reach between sessions to prevent unsupervised ingestion risks"
        ]
    elif "best interactive cat toys for indoor cats" in title_lower:
        return [
            "Indoor cats depend entirely on their owners for interactive stimulation — commit to daily play sessions",
            "Combine puzzle feeders with active toys to address both mental and physical enrichment needs",
            "Rotate between electronic, wand, and puzzle toys to engage different aspects of hunting behaviour",
            "Schedule play during your cat's natural active periods — typically dawn and dusk",
            "Monitor your indoor cat's weight and adjust play intensity if they are gaining or losing unexpectedly"
        ]
    elif "best catnip toys" in title_lower:
        return [
            "Not all cats respond to catnip — try silvervine or valerian root as alternatives if your cat is uninterested",
            "Limit catnip exposure to 10-15 minute sessions to maintain its effectiveness and prevent overstimulation",
            "Store catnip toys in sealed bags or containers between uses to preserve potency",
            "Kittens under 6 months typically do not respond to catnip — wait until maturity to introduce it",
            "Choose catnip toys with reinforced stitching, as cats tend to kick and bite them vigorously"
        ]
    elif "cat toy rotation" in title_lower:
        return [
            "Keep only 3-4 toys available at a time and store the rest to maintain novelty",
            "Reintroduce stored toys after 1-2 weeks — the novelty effect works even with familiar items",
            "Include a variety of toy types in each rotation: something to chase, something to kick, and something to puzzle over",
            "Observe which toys get the most use and ensure those types are always in the active rotation",
            "Pair toy rotation with scheduled play sessions for maximum engagement"
        ]
    elif "choose the right cat toy" in title_lower:
        return [
            "Watch how your cat plays naturally to identify their dominant play style before buying toys",
            "Hunters prefer toys that mimic small prey; chasers love fast-moving wand toys; wrestlers enjoy kickable plush toys",
            "Consider your cat's age — kittens need softer, smaller toys while seniors prefer gentler options",
            "Safety first: avoid toys smaller than your cat's mouth and remove any detachable small parts",
            "Budget for variety rather than spending heavily on one toy — cats tire of repetition quickly"
        ]
    elif "cat toys faq" in title_lower:
        return [
            "Supervised play with appropriate toys is the safest approach for all cats",
            "Most cats need at least 15-30 minutes of interactive play daily for adequate stimulation",
            "Replace worn toys immediately — frayed strings, loose feathers, and cracked plastic are hazards",
            "Catnip is safe for adult cats in moderation but is unnecessary and usually ineffective for kittens",
            "Store string and wand toys out of reach — these should never be left with unsupervised cats"
        ]
    elif "kitten vs adult cat" in title_lower:
        return [
            "Kittens need softer, smaller toys appropriate for their developing teeth and coordination",
            "Adult cats benefit from more complex toys including puzzle feeders and hunting simulation toys",
            "Senior cats may need slower-moving, lighter toys that accommodate reduced mobility",
            "Never leave kittens unsupervised with toys that have small detachable parts",
            "Transition toy complexity gradually as your kitten grows — matching challenge to developmental stage"
        ]
    elif "how often should you replace" in title_lower:
        return [
            "Inspect all cat toys weekly for signs of wear: loose threads, exposed stuffing, cracked plastic",
            "Feather and fabric toys typically need replacing every 1-3 months with regular use",
            "Hard plastic and rubber toys can last 6-12 months if they remain intact and undamaged",
            "When in doubt, replace — the cost of a new toy is negligible compared to an emergency vet bill",
            "Keep a small stock of replacement toys so worn items can be swapped out immediately"
        ]
    elif "diy cat toys" in title_lower:
        return [
            "Never use string, ribbon, rubber bands, or yarn in unsupervised DIY toys — linear foreign bodies are a serious veterinary emergency",
            "Cardboard boxes, paper bags (handles removed), and toilet roll tubes make safe, simple enrichment",
            "Supervise all homemade toy play and inspect regularly for damage or detached parts",
            "Avoid toxic materials including glue, markers, treated wood, and polystyrene foam",
            "DIY toys are excellent enrichment but should be rotated and replaced just like shop-bought options"
        ]
    elif "wall-mounted cat scratcher" in title_lower:
        return [
            "Wall-mounted scratchers save floor space and suit smaller UK homes and flats",
            "Mount at a height that allows your cat to fully stretch — typically 30-40cm above their standing reach",
            "Check wall fixings are suitable for your wall type (plasterboard needs specialist anchors)",
            "Position near sleeping areas or room entrances where cats naturally want to scratch",
            "Replace the scratching surface when it becomes severely shredded — most designs allow pad swaps"
        ]
    elif "cardboard cat scratcher" in title_lower:
        return [
            "Many cats actively prefer cardboard's texture over sisal or carpet scratching surfaces",
            "Budget for regular replacement — cardboard scratchers typically last 2-6 months with normal use",
            "Place a mat underneath to catch cardboard debris and make cleanup easier",
            "Sprinkle a small amount of catnip on a new scratcher to encourage initial use",
            "Offer cardboard scratchers alongside other materials to learn your cat's texture preferences"
        ]
    elif "cat scratching posts" in title_lower:
        return [
            "Choose a post at least 60cm tall to allow full-stretch scratching — taller is generally better",
            "Stability is non-negotiable: a wobbly post will be quickly abandoned in favour of your furniture",
            "Place scratching posts near furniture your cat currently targets and near their sleeping areas",
            "Sisal fabric wrapping tends to last longer than sisal rope and is preferred by many cats",
            "Provide at least one scratching post per cat, placed in different locations around the home",
            "Never punish a cat for scratching — redirect to appropriate surfaces instead"
        ]
    elif "cat litter disposal" in title_lower:
        return [
            "Used cat litter should always be double-bagged and placed in general household waste — never composted or flushed",
            "Dedicated disposal bins significantly reduce odour between bin collection days",
            "Factor in ongoing refill bag costs when comparing disposal systems — these vary significantly",
            "Clean the disposal bin itself regularly with mild disinfectant to prevent bacterial build-up",
            "Pregnant women should avoid handling used cat litter due to Toxoplasma gondii risks"
        ]
    elif "best cat litter uk" in title_lower and "tray" not in title_lower:
        return [
            "Most cats prefer fine-grained, unscented clumping litter based on behavioural preference studies",
            "Maintain a depth of 5-7cm and scoop at least twice daily for optimal hygiene",
            "Transition between litter types gradually over 7-10 days to avoid tray refusal",
            "Low-dust formulas are important for respiratory health — both feline and human",
            "Consider the full cost per month rather than just the bag price when comparing litter types"
        ]
    elif "cat litter tray" in title_lower:
        return [
            "Provide one litter tray per cat plus one extra, placed in different quiet locations",
            "Trays should be at least 1.5 times the length of the cat for comfortable use",
            "Not all cats accept hooded trays — observe your cat's preference before committing",
            "Senior and arthritic cats need low-entry trays placed on the same floor they mainly occupy",
            "Clean trays thoroughly with hot water weekly — avoid strong-smelling disinfectants that deter cats"
        ]
    elif "heated cat bed" in title_lower:
        return [
            "Heated beds are particularly valuable for senior cats, arthritic cats, and hairless breeds during UK winters",
            "Always choose products with UKCA or CE electrical safety marking and chew-resistant cords",
            "Low-voltage (12V) heated pads are generally safer than mains-voltage alternatives",
            "Self-warming beds rely on body heat reflection and will not feel warm until the cat lies on them",
            "Place heated beds in your cat's existing preferred sleeping location for fastest adoption"
        ]
    elif "best cat beds uk" in title_lower:
        return [
            "Observe how your cat sleeps naturally — curlers prefer donut beds, sprawlers prefer flat mats",
            "Washable covers are essential for hygiene — aim to wash cat bedding at least fortnightly",
            "Cats prefer beds in elevated, warm, quiet locations away from heavy foot traffic",
            "Provide at least one bed per cat in multi-cat households, placed in different rooms",
            "Memory foam or high-density filling maintains support longer than standard polyester fibre",
            "Allow time for your cat to adopt a new bed — scent familiarity takes days to develop"
        ]
    elif "essential cat supplies" in title_lower:
        return [
            "Have all essential supplies in place before bringing your new cat home to reduce settling-in stress",
            "The five non-negotiable items are: food and water bowls, litter tray and litter, scratching post, carrier, and bed",
            "Microchipping is compulsory for cats in England — budget for this if your cat is not yet chipped",
            "Register with a local vet before your cat arrives so that help is available immediately if needed",
            "Add enrichment items gradually — observe your cat's preferences before investing heavily in accessories"
        ]
    elif "indoor cat care" in title_lower:
        return [
            "Indoor cats need deliberate environmental enrichment to compensate for the lack of outdoor stimulation",
            "Provide vertical space (cat trees, shelves) — cats feel safer with height and it increases their usable territory",
            "Schedule at least two interactive play sessions daily totalling 20-30 minutes minimum",
            "Maintain strict litter hygiene — indoor cats have no alternative toileting option",
            "Monitor weight carefully, as indoor cats are significantly more prone to obesity",
            "Consider a window perch or secure catio to give your indoor cat safe access to fresh air and outdoor views"
        ]
    elif "best indoor cat toys" in title_lower:
        return [
            "Prioritise toys that simulate hunting: wand toys for chase, kick toys for capture, and puzzle feeders for foraging",
            "Combine supervised interactive toys with safe solo-play options for when you are away",
            "Schedule dedicated play sessions rather than relying on toys alone to keep your indoor cat active",
            "Rotate toys weekly to maintain the novelty that indoor cats cannot get from outdoor exploration",
            "Monitor your indoor cat's weight and activity level to ensure toys are providing sufficient exercise"
        ]
    else:
        return [
            "Prioritise safety and welfare-approved products for your cat",
            "Reference UK organisations like Cats Protection and International Cat Care for evidence-based guidance",
            "Observe your individual cat's preferences — every cat is different",
            "Inspect and replace products regularly to maintain safety and hygiene",
            "Consult your vet if you notice any sudden changes in behaviour, appetite, or activity levels"
        ]


# ── block builders ──

def build_at_a_glance_block(bullets):
    li_items = "".join(f"<li>{b}</li>" for b in bullets)
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#eef2ff"}},"border":{{"radius":"6px","width":"1px","color":"#c7d2fe"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#c7d2fe;border-width:1px;border-radius:6px;background-color:#eef2ff;margin-top:20px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">At a Glance</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">{li_items}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''


def build_why_this_matters_block(text):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fffbeb"}},"border":{{"radius":"6px","width":"1px","color":"#fde68a"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fde68a;border-width:1px;border-radius:6px;background-color:#fffbeb;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px"><strong>Why this matters:</strong> {text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def build_what_we_considered_block(text):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f5f3ff"}},"border":{{"radius":"6px","width":"1px","color":"#ddd6fe"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#ddd6fe;border-width:1px;border-radius:6px;background-color:#f5f3ff;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px"><strong>What we considered:</strong> {text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def build_troubleshooting_block(text):
    return f'''<!-- wp:heading {{"level":3}} -->
<h3 class="wp-block-heading">Troubleshooting Common Issues</h3>
<!-- /wp:heading -->
<!-- wp:paragraph -->
<p>{text}</p>
<!-- /wp:paragraph -->'''


def build_when_to_seek_help_block(text):
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#fef2f2"}},"border":{{"radius":"6px","width":"1px","color":"#fecaca"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"20px","bottom":"20px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#fecaca;border-width:1px;border-radius:6px;background-color:#fef2f2;margin-top:20px;margin-bottom:20px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px"><strong>When to seek professional help:</strong> {text}</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def build_key_takeaways_block(bullets):
    li_items = "".join(f"<li>{b}</li>" for b in bullets)
    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f0fdf4"}},"border":{{"radius":"6px","width":"1px","color":"#bbf7d0"}},"spacing":{{"padding":{{"top":"16px","bottom":"16px","left":"20px","right":"20px"}},"margin":{{"top":"24px","bottom":"24px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#bbf7d0;border-width:1px;border-radius:6px;background-color:#f0fdf4;margin-top:24px;margin-bottom:24px;padding-top:16px;padding-right:20px;padding-bottom:16px;padding-left:20px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Key Takeaways</h4>
<!-- /wp:heading -->
<!-- wp:list -->
<ul class="wp-block-list">{li_items}</ul>
<!-- /wp:list -->
</div>
<!-- /wp:group -->'''


TRUST_FOOTER = '''<!-- wp:group {"style":{"color":{"background":"#f8fafb"},"border":{"radius":"8px","color":"#e2e8f0","width":"1px"},"spacing":{"padding":{"top":"20px","bottom":"20px","left":"24px","right":"24px"},"margin":{"top":"32px","bottom":"32px"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:8px;background-color:#f8fafb;margin-top:32px;margin-bottom:32px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px">
<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">Our Editorial Standards</h4>
<!-- /wp:heading -->
<!-- wp:paragraph {"style":{"typography":{"fontSize":"14px"}}} -->
<p style="font-size:14px">All content on Pet Hub Online is created following our <a href="https://pethubonline.com/our-editorial-process/">editorial process</a>, supported by thorough <a href="https://pethubonline.com/how-we-research-pet-products/">research methodology</a>. We reference UK veterinary and welfare organisations including the <a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, <a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>, <a href="https://www.cats.org.uk/" rel="nofollow">Cats Protection</a>, and <a href="https://icatcare.org/" rel="nofollow">International Cat Care</a>. We maintain transparency through our <a href="https://pethubonline.com/corrections-and-updates-policy/">corrections and updates policy</a>. Content is AI-assisted and editorially reviewed. For details on how we handle affiliate relationships, see our <a href="https://pethubonline.com/affiliate-disclosure/">affiliate disclosure</a>.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


# ── content insertion logic ──

def has_block(content, marker):
    """Check if a block already exists in content."""
    return marker.lower() in content.lower()


def find_first_para_end(content):
    """Find the end of the first paragraph block."""
    # Match the first complete wp:paragraph block
    m = re.search(r'(<!-- /wp:paragraph -->)', content)
    if m:
        return m.end()
    return 0


def find_faq_position(content):
    """Find position just before FAQ section."""
    # Look for FAQ heading
    patterns = [
        r'<!-- wp:heading[^>]*-->\s*<h[23][^>]*>.*?(?:FAQ|Frequently Asked)',
        r'<h[23][^>]*>.*?(?:FAQ|Frequently Asked)',
    ]
    for pat in patterns:
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            return m.start()
    return None


def find_trust_footer(content):
    """Find and return (start, end) of existing trust footer block."""
    # Look for editorial standards / trust footer patterns
    patterns = [
        # Expanded editorial standards block
        r'<!-- wp:group[^>]*-->.*?Our Editorial Standards.*?<!-- /wp:group -->',
        # Older trust footers
        r'<!-- wp:group[^>]*-->.*?editorial process.*?affiliate disclosure.*?<!-- /wp:group -->',
        r'<!-- wp:group[^>]*-->.*?(?:Pet Hub Online|pethubonline).*?(?:editorial|research).*?<!-- /wp:group -->',
    ]
    for pat in patterns:
        m = re.search(pat, content, re.IGNORECASE | re.DOTALL)
        if m:
            return (m.start(), m.end())
    return None


def remove_old_trust_footer(content):
    """Remove old trust footer if it exists, return (cleaned_content, was_removed)."""
    loc = find_trust_footer(content)
    if loc:
        return content[:loc[0]] + content[loc[1]:], True
    return content, False


def process_post(post_id, title, cluster):
    """Process a single post: fetch, enhance, update. Returns a log dict."""
    title_clean = html.unescape(title)
    log = {
        "id": post_id,
        "title": title_clean,
        "cluster": cluster,
        "at_a_glance": "skip",
        "why_this_matters": "skip",
        "what_we_considered": "skip",
        "troubleshooting": "skip",
        "when_to_seek_help": "skip",
        "key_takeaways": "skip",
        "trust_upgraded": "skip",
        "status": "pending"
    }

    try:
        # Fetch post
        print(f"  Fetching post {post_id}: {title_clean[:60]}...")
        data = api_get(f"posts/{post_id}?context=edit")
        content = data["content"]["raw"]
        time.sleep(2)

        modified = False

        # 1. AT A GLANCE (after first paragraph)
        if not has_block(content, "At a Glance"):
            bullets = gen_at_a_glance(title_clean, content)
            block = build_at_a_glance_block(bullets)
            insert_pos = find_first_para_end(content)
            if insert_pos > 0:
                content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                log["at_a_glance"] = "added"
                modified = True
            else:
                log["at_a_glance"] = "no_insert_point"
        else:
            log["at_a_glance"] = "exists"

        # 2. WHY THIS MATTERS (after At a Glance or after first heading)
        if not has_block(content, "Why this matters"):
            text = gen_why_this_matters(title_clean, cluster)
            block = build_why_this_matters_block(text)
            # Place after At a Glance block if it exists
            aag_end = content.find("At a Glance")
            if aag_end >= 0:
                # Find the end of the At a Glance group
                group_end = content.find("<!-- /wp:group -->", aag_end)
                if group_end >= 0:
                    insert_pos = group_end + len("<!-- /wp:group -->")
                    content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                    log["why_this_matters"] = "added"
                    modified = True
                else:
                    log["why_this_matters"] = "no_insert_point"
            else:
                # Place after second paragraph
                second_para = content.find("<!-- /wp:paragraph -->")
                if second_para >= 0:
                    next_para = content.find("<!-- /wp:paragraph -->", second_para + 1)
                    if next_para >= 0:
                        insert_pos = next_para + len("<!-- /wp:paragraph -->")
                    else:
                        insert_pos = second_para + len("<!-- /wp:paragraph -->")
                    content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                    log["why_this_matters"] = "added"
                    modified = True
                else:
                    log["why_this_matters"] = "no_insert_point"
        else:
            log["why_this_matters"] = "exists"

        # 3. WHAT WE CONSIDERED (for "Best X" guides only)
        criteria_text = gen_what_we_considered(title_clean)
        if criteria_text and not has_block(content, "What we considered"):
            block = build_what_we_considered_block(criteria_text)
            # Place after Why This Matters block
            wtm_marker = "Why this matters"
            wtm_pos = content.find(wtm_marker)
            if wtm_pos >= 0:
                group_end = content.find("<!-- /wp:group -->", wtm_pos)
                if group_end >= 0:
                    insert_pos = group_end + len("<!-- /wp:group -->")
                    content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                    log["what_we_considered"] = "added"
                    modified = True
                else:
                    log["what_we_considered"] = "no_insert_point"
            else:
                # After At a Glance if WTM not found
                aag_marker = "At a Glance"
                aag_pos = content.find(aag_marker)
                if aag_pos >= 0:
                    group_end = content.find("<!-- /wp:group -->", aag_pos)
                    if group_end >= 0:
                        insert_pos = group_end + len("<!-- /wp:group -->")
                        content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                        log["what_we_considered"] = "added"
                        modified = True
                    else:
                        log["what_we_considered"] = "no_insert_point"
                else:
                    log["what_we_considered"] = "no_insert_point"
        elif not criteria_text:
            log["what_we_considered"] = "n/a"
        else:
            log["what_we_considered"] = "exists"

        # 4. TROUBLESHOOTING (before FAQ)
        if not has_block(content, "Troubleshooting Common Issues"):
            text = gen_troubleshooting(title_clean, cluster)
            block = build_troubleshooting_block(text)
            faq_pos = find_faq_position(content)
            if faq_pos:
                content = content[:faq_pos] + block + "\n\n" + content[faq_pos:]
                log["troubleshooting"] = "added"
                modified = True
            else:
                # Place before Key Takeaways or trust footer, or at end
                # Try before the last few blocks
                log["troubleshooting"] = "no_faq_section"
        else:
            log["troubleshooting"] = "exists"

        # 5. WHEN TO SEEK HELP (after troubleshooting or before FAQ)
        if not has_block(content, "When to seek professional help"):
            text = gen_when_to_seek_help(title_clean, cluster)
            block = build_when_to_seek_help_block(text)
            # Place after troubleshooting section
            ts_marker = "Troubleshooting Common Issues"
            ts_pos = content.find(ts_marker)
            if ts_pos >= 0:
                # Find end of troubleshooting paragraph
                para_end = content.find("<!-- /wp:paragraph -->", ts_pos)
                if para_end >= 0:
                    insert_pos = para_end + len("<!-- /wp:paragraph -->")
                    content = content[:insert_pos] + "\n\n" + block + "\n\n" + content[insert_pos:]
                    log["when_to_seek_help"] = "added"
                    modified = True
                else:
                    log["when_to_seek_help"] = "no_insert_point"
            else:
                # Place before FAQ
                faq_pos = find_faq_position(content)
                if faq_pos:
                    content = content[:faq_pos] + block + "\n\n" + content[faq_pos:]
                    log["when_to_seek_help"] = "added"
                    modified = True
                else:
                    log["when_to_seek_help"] = "no_insert_point"
        else:
            log["when_to_seek_help"] = "exists"

        # 6 & 7. KEY TAKEAWAYS + TRUST FOOTER
        # Remove old trust footer first
        content, had_old_trust = remove_old_trust_footer(content)

        # Add Key Takeaways if not present
        if not has_block(content, "Key Takeaways"):
            bullets = gen_key_takeaways(title_clean, cluster)
            kt_block = build_key_takeaways_block(bullets)
            # Append Key Takeaways + new trust footer at end
            content = content.rstrip() + "\n\n" + kt_block + "\n\n" + TRUST_FOOTER
            log["key_takeaways"] = "added"
            log["trust_upgraded"] = "added" if not had_old_trust else "upgraded"
            modified = True
        else:
            log["key_takeaways"] = "exists"
            # Still add/upgrade trust footer
            content = content.rstrip() + "\n\n" + TRUST_FOOTER
            log["trust_upgraded"] = "added" if not had_old_trust else "upgraded"
            modified = True

        # Update post if modified
        if modified:
            print(f"  Updating post {post_id}...")
            api_post(f"posts/{post_id}", {"content": content})
            log["status"] = "updated"
            time.sleep(2)
        else:
            log["status"] = "no_changes"

    except Exception as e:
        log["status"] = f"error: {str(e)[:200]}"
        print(f"  ERROR on post {post_id}: {e}")

    return log


# ── main ──

def main():
    # Read inventory
    posts = []
    with open(INVENTORY) as f:
        reader = csv.DictReader(f)
        for row in reader:
            cluster = row["cluster"].strip()
            if cluster in TARGET_CLUSTERS:
                posts.append({
                    "id": int(row["id"]),
                    "title": html.unescape(row["title"]),
                    "cluster": cluster
                })

    print(f"Found {len(posts)} posts to process across Cat Toys, Cat Supplies, Indoor Cats")
    print(f"Clusters: {', '.join(sorted(set(p['cluster'] for p in posts)))}")
    print()

    # Process each post
    results = []
    for i, post in enumerate(posts, 1):
        print(f"[{i}/{len(posts)}] Processing: {post['title'][:70]}...")
        log = process_post(post["id"], post["title"], post["cluster"])
        results.append(log)
        print(f"  -> {log['status']}")
        print(f"     AAG={log['at_a_glance']}, WTM={log['why_this_matters']}, WWC={log['what_we_considered']}, "
              f"TS={log['troubleshooting']}, WTSH={log['when_to_seek_help']}, KT={log['key_takeaways']}, "
              f"TF={log['trust_upgraded']}")
        print()

    # Write log CSV
    fieldnames = ["id", "title", "cluster", "at_a_glance", "why_this_matters",
                  "what_we_considered", "troubleshooting", "when_to_seek_help",
                  "key_takeaways", "trust_upgraded", "status"]
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Summary
    updated = sum(1 for r in results if r["status"] == "updated")
    errors = sum(1 for r in results if r["status"].startswith("error"))
    print(f"\n{'='*60}")
    print(f"BATCH 3 COMPLETE: {updated} updated, {errors} errors, {len(posts)} total")
    print(f"Log written to: {LOG_FILE}")


if __name__ == "__main__":
    main()
