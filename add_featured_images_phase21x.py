#!/usr/bin/env python3
"""Add Pexels featured images to Phase 21X posts (IDs 21081-21155)."""

import requests
import json
import time
import os

WP_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
HEADERS = {"Accept-Encoding": "gzip, deflate"}
PEXELS_KEY = "dmGyKrZqTlwukxWzOK1EkH4jbEv9EaIDpLGj7eL5MZ07bl6AR9OEoHlB"

def search_pexels(query):
    """Search Pexels for a landscape image."""
    r = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": PEXELS_KEY},
        params={"query": query, "per_page": 3, "orientation": "landscape"}
    )
    if r.status_code == 200:
        photos = r.json().get("photos", [])
        if photos:
            return photos[0]["src"]["large2x"], photos[0]["photographer"]
    return None, None

def upload_image(session, image_url, filename, alt_text):
    """Download from Pexels and upload to WordPress."""
    img_resp = requests.get(image_url, timeout=30)
    if img_resp.status_code != 200:
        return None

    files = {"file": (filename, img_resp.content, "image/jpeg")}
    data = {"alt_text": alt_text, "caption": f"Photo by Pexels"}
    r = session.post(f"{WP_URL}/media", files=files, data=data)
    if r.status_code == 201:
        return r.json()["id"]
    return None

def set_featured_image(session, post_id, media_id):
    """Set featured image on a post."""
    r = session.post(f"{WP_URL}/posts/{post_id}", json={"featured_media": media_id})
    return r.status_code == 200

def get_search_term(title):
    """Extract a good Pexels search term from the post title."""
    title_lower = title.lower()
    if "cat" in title_lower:
        if "carrier" in title_lower: return "cat carrier travel"
        if "water" in title_lower and "fountain" in title_lower: return "cat drinking water"
        if "feeding" in title_lower: return "cat eating food bowl"
        if "litter" in title_lower: return "cat litter box clean"
        if "safety" in title_lower and "household" in title_lower: return "cat home safe"
        if "travel" in title_lower: return "cat travel carrier"
        if "new owner" in title_lower: return "cute kitten home"
        if "cleaning" in title_lower: return "cat hygiene clean"
        if "seasonal" in title_lower: return "cat seasons cozy"
        if "budget" in title_lower: return "cat supplies shopping"
        if "lifespan" in title_lower: return "cat playing toys"
        if "window" in title_lower: return "cat window perch watching"
        if "shelving" in title_lower: return "cat climbing shelf"
        if "storage" in title_lower: return "cat supplies organized"
        if "dehydration" in title_lower or "water intake" in title_lower: return "cat drinking water bowl"
        if "grooming" in title_lower: return "cat grooming brushing"
        if "indoor" in title_lower: return "indoor cat playing"
        if "collar" in title_lower or "microchip" in title_lower: return "cat collar tag"
        if "carrier training" in title_lower: return "cat carrier calm"
        if "bowls" in title_lower or "puzzle" in title_lower or "slow feeder" in title_lower: return "cat puzzle feeder"
        if "organisation" in title_lower: return "cat supplies tidy"
        if "emergency" in title_lower: return "cat first aid kit"
        if "age" in title_lower or "kitten" in title_lower: return "kitten adult senior cat"
        if "senior" in title_lower: return "senior cat comfortable"
        if "household setup" in title_lower: return "home prepared cat"
        return "happy cat UK home"
    if "joint" in title_lower or "mobility" in title_lower: return "dog running walking healthy"
    if "weight loss" in title_lower: return "dog exercise healthy weight"
    if "weight gain" in title_lower: return "dog eating healthy food"
    if "allergy" in title_lower: return "dog skin allergy itching"
    if "digestive" in title_lower: return "dog stomach health"
    if "monitoring" in title_lower and "health" in title_lower: return "dog vet checkup"
    if "surgery" in title_lower or "recovery" in title_lower: return "dog recovery resting"
    if "medication" in title_lower: return "dog medicine pills"
    if "senior" in title_lower: return "senior old dog resting"
    if "hydration" in title_lower or "dehydration" in title_lower: return "dog drinking water bowl"
    if "parasite" in title_lower: return "dog flea tick prevention"
    if "skin" in title_lower: return "dog skin coat healthy"
    if "coat condition" in title_lower or "fur" in title_lower: return "dog shiny coat grooming"
    if "dental" in title_lower: return "dog teeth dental care"
    if "record" in title_lower: return "dog vet records papers"
    if "red flag" in title_lower: return "dog sick symptoms"
    if "vet visit" in title_lower: return "dog veterinary clinic"
    if "preventive" in title_lower: return "healthy happy dog"
    if "seasonal" in title_lower and "health" in title_lower: return "dog seasons weather"
    if "first aid" in title_lower: return "dog first aid kit"
    if "arthritis" in title_lower: return "older dog joint care"
    if "hearing" in title_lower or "vision" in title_lower: return "senior dog face close"
    if "cost" in title_lower or "budget" in title_lower: return "dog vet cost money"
    if "emergency" in title_lower: return "dog emergency vet"
    if "coat buying" in title_lower: return "dog wearing coat winter"
    if "lead" in title_lower: return "dog lead walking owner"
    if "travel gear" in title_lower or "road trip" in title_lower: return "dog car travel road trip"
    if "water bottle" in title_lower: return "dog drinking portable water"
    if "storage" in title_lower: return "pet supplies organized storage"
    if "feeding station" in title_lower: return "dog food bowl station"
    if "walking accessories" in title_lower: return "dog walking park lead"
    if "seasonal equipment" in title_lower or "each season" in title_lower: return "dog four seasons"
    if "replacement" in title_lower: return "dog equipment gear"
    if "safety equipment" in title_lower or "high-visibility" in title_lower: return "dog high visibility vest"
    if "outdoor adventure" in title_lower or "hiking" in title_lower: return "dog hiking outdoor adventure"
    if "camping" in title_lower: return "dog camping tent outdoor"
    if "beach" in title_lower: return "dog beach water playing"
    if "rainy" in title_lower: return "dog rain coat wet"
    if "winter" in title_lower: return "dog winter snow coat"
    if "summer" in title_lower: return "dog summer cool shade"
    if "car safety" in title_lower: return "dog car seatbelt safety"
    if "crate" in title_lower: return "dog travel crate carrier"
    if "cleaning" in title_lower: return "dog equipment cleaning"
    if "breed size" in title_lower: return "small medium large dogs"
    if "household setup" in title_lower: return "dog home setup room"
    if "new owner" in title_lower: return "puppy new owner supplies"
    if "emergency equipment" in title_lower: return "dog emergency kit supplies"
    if "lifespan tracker" in title_lower: return "dog gear equipment quality"
    return "happy dog UK garden"


def main():
    session = requests.Session()
    session.auth = AUTH
    session.headers.update(HEADERS)

    # Load all result files
    all_posts = []
    for fname in ["dog_health_expansion_results.json", "dog_supplies_expansion_results.json", "cat_supplies_expansion_results.json"]:
        fpath = f"/var/lib/freelancer/projects/40416335/{fname}"
        if os.path.exists(fpath):
            data = json.load(open(fpath))
            all_posts.extend(data["posts"])

    print(f"Total posts to process: {len(all_posts)}")

    results = {"processed": 0, "success": 0, "errors": []}

    for i, post in enumerate(all_posts):
        post_id = post["id"]
        title = post["title"]
        search_term = get_search_term(title)

        try:
            print(f"[{i+1}/{len(all_posts)}] ID={post_id}: {title[:50]}... -> '{search_term}'")

            img_url, photographer = search_pexels(search_term)
            if not img_url:
                results["errors"].append(f"No Pexels image for '{search_term}' (post {post_id})")
                print(f"  No image found")
                continue

            filename = f"pethub-{post_id}-featured.jpg"
            alt_text = title.split(":")[0].strip()

            media_id = upload_image(session, img_url, filename, alt_text)
            if not media_id:
                results["errors"].append(f"Upload failed for post {post_id}")
                print(f"  Upload failed")
                time.sleep(3)
                continue

            if set_featured_image(session, post_id, media_id):
                results["success"] += 1
                print(f"  Set featured image (media={media_id})")
            else:
                results["errors"].append(f"Set featured failed for post {post_id}")

            results["processed"] += 1
            time.sleep(2)

        except Exception as e:
            results["errors"].append(f"Error post {post_id}: {str(e)}")
            print(f"  ERROR: {e}")
            time.sleep(3)

    print(f"\nResults: {results['success']}/{len(all_posts)} images set, {len(results['errors'])} errors")

    with open("/var/lib/freelancer/projects/40416335/phase21x_featured_images_results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
