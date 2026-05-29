#!/usr/bin/env python3
"""
Fix block ordering: Move Decision Pathway and Research Sources to BEFORE Quick Checklist.
Correct order should be:
  ... Practical Guide ... How to Evaluate ... [Decision Pathway] [Research Sources] [Quick Checklist] ...
"""

import subprocess
import json
import tempfile
import os
import time
import re

WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"

TARGET_POSTS = [5414, 5296, 5458, 5519, 5521, 5511, 5509, 5467, 5464, 5460]


def wp_api(method, endpoint, data=None):
    url = f"{WP_BASE}/{endpoint}"
    cmd = ["curl", "-s", "--compressed", "-u", f"{WP_USER}:{WP_PASS}"]
    if method == "GET":
        cmd.append(url)
    elif method == "POST":
        cmd.extend(["-X", "POST", "-H", "Content-Type: application/json"])
        if data:
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            json.dump(data, tmp)
            tmp.close()
            cmd.extend(["-d", f"@{tmp.name}"])
        cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if data and 'tmp' in locals():
        try:
            os.unlink(tmp.name)
        except:
            pass
    try:
        return json.loads(result.stdout)
    except:
        return None


def extract_block(content, title_marker):
    """Extract a colored div block containing the given title marker.
    Returns (block_text, start_pos, end_pos) or (None, -1, -1) if not found.
    """
    idx = content.find(title_marker)
    if idx < 0:
        return None, -1, -1

    # Walk backwards to find the containing <div
    search_start = max(0, idx - 500)
    segment = content[search_start:idx]
    last_div = segment.rfind('<div ')
    if last_div < 0:
        return None, -1, -1

    div_start = search_start + last_div

    # Find matching closing </div> by counting nesting
    pos = div_start
    depth = 0
    i = div_start

    while i < len(content):
        open_match = content.find('<div', i)
        close_match = content.find('</div>', i)

        if close_match < 0:
            break

        if open_match >= 0 and open_match < close_match:
            if open_match == div_start or (open_match > div_start and depth > 0):
                depth += 1
            elif depth == 0:
                depth = 1
            i = open_match + 4
        else:
            depth -= 1
            if depth <= 0:
                end_pos = close_match + len('</div>')
                block = content[div_start:end_pos]
                return block, div_start, end_pos
            i = close_match + 6

    return None, -1, -1


def find_block_start(content, title_marker):
    """Find the start position of a div block containing the title marker."""
    idx = content.find(title_marker)
    if idx < 0:
        return -1
    search_start = max(0, idx - 500)
    segment = content[search_start:idx]
    last_div = segment.rfind('<div ')
    if last_div < 0:
        return -1
    return search_start + last_div


def find_checklist_start(content):
    """Find the start of Quick Checklist block.
    Quick Checklist is typically an h4 heading, not inside a colored div.
    """
    idx = content.find('Quick Checklist')
    if idx < 0:
        return -1

    # Walk back to find <h4 containing Quick Checklist
    search_start = max(0, idx - 200)
    segment = content[search_start:idx]
    last_h4 = segment.rfind('<h4 ')
    if last_h4 >= 0:
        return search_start + last_h4

    return idx


for pid in TARGET_POSTS:
    print(f"\n[{pid}] Processing...")

    post = wp_api("GET", f"posts/{pid}?context=edit")
    if not post or "content" not in post:
        print(f"  ERROR: Could not fetch")
        continue

    content = post["content"]["raw"]
    title = post["title"]["raw"]
    print(f"  Title: {title[:60]}")

    # Extract the Decision Pathway block
    dp_block, dp_start, dp_end = extract_block(content, "Your Decision Pathway")
    # Extract the Research Sources block
    rs_block, rs_start, rs_end = extract_block(content, "Research Sources and Standards")

    if not dp_block:
        print(f"  WARNING: Decision Pathway not found, skipping")
        continue
    if not rs_block:
        print(f"  WARNING: Research Sources not found, skipping")
        continue

    checklist_pos = find_checklist_start(content)
    if checklist_pos < 0:
        print(f"  WARNING: Quick Checklist not found, skipping")
        continue

    # Check if already in correct order
    if dp_start < checklist_pos and rs_start < checklist_pos and dp_start < rs_start:
        print(f"  Already in correct order, skipping")
        continue

    print(f"  Decision Pathway: {dp_start}-{dp_end}")
    print(f"  Research Sources: {rs_start}-{rs_end}")
    print(f"  Quick Checklist: {checklist_pos}")

    # Remove blocks from their current positions (remove the later one first to preserve indices)
    # Determine removal order
    removals = sorted([(dp_start, dp_end, "DP"), (rs_start, rs_end, "RS")], key=lambda x: x[0], reverse=True)

    new_content = content
    for start, end, label in removals:
        # Also remove surrounding whitespace/newlines
        # Check for leading newline
        actual_start = start
        actual_end = end
        while actual_start > 0 and new_content[actual_start - 1] in '\n\r':
            actual_start -= 1
        while actual_end < len(new_content) and new_content[actual_end] in '\n\r':
            actual_end += 1
        print(f"  Removing {label} from {actual_start}-{actual_end}")
        new_content = new_content[:actual_start] + new_content[actual_end:]

    # Find the Quick Checklist position in the new content
    new_checklist_pos = find_checklist_start(new_content)
    if new_checklist_pos < 0:
        print(f"  ERROR: Quick Checklist lost after removal, skipping update")
        continue

    print(f"  New Quick Checklist pos: {new_checklist_pos}")

    # Insert Decision Pathway then Research Sources BEFORE Quick Checklist
    insert_text = "\n" + dp_block + "\n" + rs_block + "\n"
    new_content = new_content[:new_checklist_pos] + insert_text + new_content[new_checklist_pos:]

    print(f"  Content length change: {len(content)} -> {len(new_content)} ({len(new_content) - len(content):+d})")

    # Verify ordering in new content
    verify_dp = new_content.find("Your Decision Pathway")
    verify_rs = new_content.find("Research Sources and Standards")
    verify_cl = find_checklist_start(new_content)
    verify_pg = new_content.find("Step-by-Step Practical Guide")

    if verify_dp < verify_rs < verify_cl:
        print(f"  Order verified: DP({verify_dp}) < RS({verify_rs}) < CL({verify_cl})")
    else:
        print(f"  WARNING: Order may be wrong: DP({verify_dp}), RS({verify_rs}), CL({verify_cl})")

    if verify_pg >= 0 and verify_pg < verify_dp:
        print(f"  Practical Guide ({verify_pg}) correctly before Decision Pathway")

    # Update post
    result = wp_api("POST", f"posts/{pid}", {"content": new_content})
    if result and "id" in result:
        print(f"  SUCCESS: Updated")
    else:
        err = result.get("message", "Unknown") if result else "No response"
        print(f"  ERROR: {err}")

    time.sleep(2)

print("\nDone! All blocks reordered.")
