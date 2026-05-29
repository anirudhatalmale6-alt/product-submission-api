#!/usr/bin/env python3
"""
Fix script: Upgrade the 'About Our Editorial Standards' plain h3 section
to the proper styled trust footer block for the 9 posts where it was NOT_FOUND.
"""

import csv
import json
import os
import re
import subprocess
import tempfile
import time

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
API = "https://pethubonline.com/wp-json/wp/v2"
DELAY = 2.5

# Post ID -> cluster mapping for the 9 NOT_FOUND posts
POSTS_TO_FIX = {
    4568: "Dog Health",     # Dog Dental Health
    4566: "Dog Care",       # Seasonal Dog Care
    4132: "Dog Training",   # Best Puppy Training Guide
    4125: "Dog Training",   # Best Dog Training Treats
    4118: "Dog Training",   # Best Dog Training and Behaviour
    4110: "Dog Health",     # Best Dog Joint Supplements
    4103: "Dog Health",     # Best Dog Flea Treatment
    4096: "Dog Health",     # Best Dog Dental Care
    4089: "Dog Health",     # Best Dog Health and Care
}


def api_get(endpoint):
    url = f"{API}/{endpoint}"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    return json.loads(result.stdout)


def api_update(post_id, data):
    url = f"{API}/posts/{post_id}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        tmppath = f.name
    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST", "-H", "Content-Type: application/json",
             "-d", f"@{tmppath}", url],
            capture_output=True, text=True, timeout=120
        )
        resp = json.loads(result.stdout)
        return "id" in resp, resp
    finally:
        os.unlink(tmppath)


def generate_upgraded_trust_footer(cluster):
    if cluster == "Dog Food":
        base_refs = (
            'We reference UK veterinary and welfare organisations including the '
            '<a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, '
            '<a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>, '
            '<a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>, '
            '<a href="https://fediaf.org/" rel="nofollow">FEDIAF</a>, and the '
            '<a href="https://www.pfma.org.uk/" rel="nofollow">PFMA</a>.'
        )
    elif cluster == "Dog Health":
        base_refs = (
            'We reference UK veterinary and welfare organisations including the '
            '<a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>, '
            '<a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>, '
            '<a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, and '
            '<a href="https://fediaf.org/" rel="nofollow">FEDIAF</a>.'
        )
    elif cluster == "Puppy Care":
        base_refs = (
            'We reference UK veterinary and welfare organisations including the '
            '<a href="https://www.thekennelclub.org.uk/" rel="nofollow">Kennel Club</a>, '
            '<a href="https://www.dogstrust.org.uk/" rel="nofollow">Dogs Trust</a>, '
            '<a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>, '
            '<a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, and '
            '<a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>.'
        )
    elif cluster == "Dog Training":
        base_refs = (
            'We reference UK training and welfare organisations including the '
            '<a href="https://apdt.co.uk/" rel="nofollow">APDT</a>, '
            '<a href="https://www.thekennelclub.org.uk/" rel="nofollow">Kennel Club</a>, '
            '<a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, '
            '<a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>, and '
            '<a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>.'
        )
    elif cluster == "Dog Care":
        base_refs = (
            'We reference UK veterinary and welfare organisations including the '
            '<a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, '
            '<a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>, '
            '<a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>, and '
            '<a href="https://fediaf.org/" rel="nofollow">FEDIAF</a>.'
        )
    else:
        base_refs = (
            'We reference UK veterinary and welfare organisations including the '
            '<a href="https://www.rspca.org.uk/" rel="nofollow">RSPCA</a>, '
            '<a href="https://www.pdsa.org.uk/" rel="nofollow">PDSA</a>, '
            '<a href="https://www.bva.co.uk/" rel="nofollow">BVA</a>, and '
            '<a href="https://fediaf.org/" rel="nofollow">FEDIAF</a>.'
        )

    return f'''<!-- wp:group {{"style":{{"color":{{"background":"#f8fafb"}},"border":{{"radius":"8px","color":"#e2e8f0","width":"1px"}},"spacing":{{"padding":{{"top":"20px","bottom":"20px","left":"24px","right":"24px"}},"margin":{{"top":"32px","bottom":"32px"}}}}}},"layout":{{"type":"constrained"}}}} -->
<div class="wp-block-group has-border-color has-background" style="border-color:#e2e8f0;border-width:1px;border-radius:8px;background-color:#f8fafb;margin-top:32px;margin-bottom:32px;padding-top:20px;padding-right:24px;padding-bottom:20px;padding-left:24px">
<!-- wp:heading {{"level":4}} -->
<h4 class="wp-block-heading">Our Editorial Standards</h4>
<!-- /wp:heading -->
<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"14px"}}}}}} -->
<p style="font-size:14px">All content on Pet Hub Online is created following our <a href="https://pethubonline.com/our-editorial-process/">editorial process</a>, supported by thorough <a href="https://pethubonline.com/how-we-research-pet-products/">research methodology</a>. {base_refs} We maintain transparency through our <a href="https://pethubonline.com/corrections-and-updates-policy/">corrections and updates policy</a>. Content is AI-assisted and editorially reviewed. For details on how we handle affiliate relationships, see our <a href="https://pethubonline.com/affiliate-disclosure/">affiliate disclosure</a>.</p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''


def main():
    print("Fixing trust footer for 9 posts with NOT_FOUND status...")

    for post_id, cluster in POSTS_TO_FIX.items():
        print(f"\n  Processing post {post_id} ({cluster})...")

        data = api_get(f"posts/{post_id}?context=edit")
        content = data['content']['raw']
        time.sleep(DELAY)

        # Find and replace "About Our Editorial Standards" section
        # Pattern: <h3...>About Our Editorial Standards</h3> followed by paragraph(s) to end or next heading
        pattern = r'<h3[^>]*>\s*About Our Editorial Standards\s*</h3>\s*<p[^>]*>.*?</p>(?:\s*<p[^>]*>.*?</p>)*'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            new_footer = generate_upgraded_trust_footer(cluster)
            new_content = content[:match.start()] + new_footer + content[match.end():]

            # Also check for and clean up the small-font-size trust block if present
            # This is a separate block that may exist in some posts
            small_font_pattern = r'<p class="[^"]*has-small-font-size[^"]*wp-block-paragraph[^"]*"[^>]*>This content follows our.*?</p>'
            small_match = re.search(small_font_pattern, new_content, re.DOTALL)
            if small_match:
                new_content = new_content[:small_match.start()] + new_content[small_match.end():]
                print(f"    Also removed small-font trust block")

            success, resp = api_update(post_id, {"content": new_content})
            if success:
                print(f"    OK - trust footer upgraded")
            else:
                print(f"    ERROR: {str(resp)[:200]}")
        else:
            print(f"    About Our Editorial Standards section not found!")
            # Try to print what's near the end
            print(f"    Last 200 chars: {content[-200:]}")

        time.sleep(DELAY)

    print("\nDone!")


if __name__ == "__main__":
    main()
