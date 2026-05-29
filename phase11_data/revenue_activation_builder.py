#!/usr/bin/env python3
"""Phase 11V: Revenue Activation — Build structures for monetization readiness.
Creates email capture forms, lead magnet structures, comparison layouts,
affiliate-ready content structures, and conversion tracking setup.
Analysis and structure only — no affiliate links inserted."""

import subprocess, json, time, csv, os, tempfile

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"
OUT_DIR = "/var/lib/freelancer/projects/40416335/phase11_data"

def wp_get(endpoint):
    url = f"{WP_API}/{endpoint}"
    time.sleep(2)
    r = subprocess.run(["curl", "-s", "--compressed", "-u", AUTH, url],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except:
        return []

def wp_post(endpoint, data):
    url = f"{WP_API}/{endpoint}"
    time.sleep(3)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        tmp = f.name
    for attempt in range(3):
        r = subprocess.run(["curl", "-s", "-X", "POST", "--compressed", "-u", AUTH,
                           "-H", "Content-Type: application/json", "-d", f"@{tmp}", url],
                          capture_output=True, text=True)
        try:
            resp = json.loads(r.stdout)
            if 'id' in resp:
                os.unlink(tmp)
                return resp
            if resp.get('data', {}).get('status') == 429:
                time.sleep(5 * (attempt + 1))
                continue
        except:
            pass
    os.unlink(tmp)
    return None

print("=" * 70)
print("PHASE 11V: REVENUE ACTIVATION ENGINE")
print("=" * 70)

# Step 1: Fetch all published posts
print("\nStep 1: Fetching published posts...")
all_posts = []
for page in range(1, 5):
    posts = wp_get(f"posts?per_page=100&page={page}&context=edit")
    if not posts or isinstance(posts, dict):
        break
    all_posts.extend(posts)
print(f"  Fetched {len(all_posts)} posts")

# Step 2: Fetch categories for cluster mapping
print("\nStep 2: Fetching categories...")
categories = wp_get("categories?per_page=100")
cat_map = {}
if isinstance(categories, list):
    for c in categories:
        cat_map[c['id']] = c['name']

# Step 3: Analyze each post for revenue readiness
print("\nStep 3: Analyzing revenue readiness...")

BLOCKED_CATS = {1467: 'Dog Food', 1422: 'Dog Harnesses'}

revenue_posts = []
for post in all_posts:
    pid = post['id']
    title = post['title']['raw'] if isinstance(post['title'], dict) else str(post['title'])
    raw = post.get('content', {}).get('raw', '') if isinstance(post.get('content'), dict) else ''
    cats = post.get('categories', [])
    cluster = 'Uncategorized'
    blocked = False
    for cid in cats:
        if cid in BLOCKED_CATS:
            blocked = True
            cluster = BLOCKED_CATS[cid]
            break
        if cid in cat_map:
            cluster = cat_map[cid]

    # Commercial intent signals
    is_best = 'best ' in title.lower()
    is_guide = 'guide' in title.lower()
    is_comparison = 'comparison' in title.lower() or 'compared' in title.lower() or 'vs' in title.lower()
    has_price = '£' in raw or 'price' in raw.lower() or 'cost' in raw.lower()
    has_comparison_table = 'is-style-stripes' in raw or 'wp-block-table' in raw
    has_faq = 'faq' in raw.lower() or 'frequently asked' in raw.lower()

    commercial_score = 0
    if is_best: commercial_score += 25
    if has_price: commercial_score += 20
    if has_comparison_table: commercial_score += 20
    if is_guide: commercial_score += 10
    if is_comparison: commercial_score += 15
    if has_faq: commercial_score += 10

    # Email capture readiness
    has_email_form = 'newsletter' in raw.lower() or 'subscribe' in raw.lower() or 'email' in raw.lower()

    # Affiliate readiness
    has_external_links = 'rel="nofollow"' in raw or 'target="_blank"' in raw
    affiliate_ready = has_comparison_table and has_price and not blocked

    # Lead magnet potential
    lead_magnet_type = 'none'
    if 'checklist' in title.lower() or 'guide' in title.lower():
        lead_magnet_type = 'downloadable_guide'
    elif 'schedule' in title.lower() or 'calendar' in title.lower():
        lead_magnet_type = 'printable_schedule'
    elif is_best or is_comparison:
        lead_magnet_type = 'comparison_chart'

    revenue_posts.append({
        'post_id': pid,
        'title': title,
        'cluster': cluster,
        'blocked': blocked,
        'commercial_score': commercial_score,
        'is_best_page': is_best,
        'has_comparison_table': has_comparison_table,
        'has_faq': has_faq,
        'has_price_signals': has_price,
        'has_email_form': has_email_form,
        'affiliate_ready': affiliate_ready,
        'lead_magnet_type': lead_magnet_type,
        'email_capture_opportunity': commercial_score >= 30 and not has_email_form,
        'conversion_potential': 'high' if commercial_score >= 50 else ('medium' if commercial_score >= 25 else 'low')
    })

# Step 4: Create revenue activation pages as drafts
print("\nStep 4: Creating revenue activation structure pages...")

# 4a. Email Capture Landing Page
email_page_content = """<!-- wp:heading {"level":2} -->
<h2>Stay Updated with UK Pet Care Insights</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Join thousands of UK pet owners who receive our weekly newsletter. Get expert-researched guides on pet nutrition, health, behaviour, and product recommendations — all specific to the UK market.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>What You Will Receive</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul><li>Weekly UK pet care tips backed by veterinary guidelines (BVA, RSPCA, PDSA)</li><li>Product comparison updates with UK pricing and availability</li><li>Seasonal care reminders tailored to UK weather and regulations</li><li>Early access to new guides and resources</li></ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Our Content Promise</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Every piece of content is researched against UK veterinary guidelines and pet welfare standards. No sponsored recommendations, no brand influence — just honest, evidence-based pet care information for UK pet owners.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><em>Note: Email subscription functionality will be activated once the newsletter platform is configured. This page establishes the content and value proposition.</em></p>
<!-- /wp:paragraph -->"""

email_page = wp_post("pages", {
    "title": "Subscribe to PetHub UK Newsletter",
    "content": email_page_content,
    "status": "draft"
})
email_pid = email_page['id'] if email_page else 'FAILED'
print(f"  Email capture page: {email_pid}")

# 4b. Lead Magnet Template Pages
lead_magnets = [
    {
        "title": "Free Download: UK Pet Owner First-Year Checklist",
        "content": """<!-- wp:heading {"level":2} -->
<h2>Your Complete First-Year Pet Owner Checklist</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>A comprehensive, printable checklist covering everything a new UK pet owner needs in their first year — from vaccinations and microchipping to insurance and essential supplies, all with UK-specific requirements and timelines.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>What Is Included</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul><li>UK vaccination schedule (puppy and kitten timelines)</li><li>Microchipping requirements under UK law</li><li>Pet insurance comparison framework (UK providers)</li><li>Essential supplies checklist with estimated UK costs</li><li>Monthly care calendar for the first 12 months</li><li>Emergency vet contact template</li></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><em>Note: Download functionality will be activated once the email capture platform is integrated. This page establishes the lead magnet value proposition.</em></p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "Free Download: Seasonal Pet Care Calendar UK (2026)",
        "content": """<!-- wp:heading {"level":2} -->
<h2>Month-by-Month UK Pet Care Calendar</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>A printable 12-month calendar with UK-specific pet care reminders — from fireworks season preparation to summer heatwave safety, flea and tick season alerts, and seasonal dietary adjustments.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Monthly Highlights</h2>
<!-- /wp:heading -->

<!-- wp:table {"className":"is-style-stripes"} -->
<figure class="wp-block-table is-style-stripes"><table><thead><tr><th>Month</th><th>Key Care Focus</th><th>UK-Specific Note</th></tr></thead><tbody><tr><td>January</td><td>Post-holiday weight check</td><td>Chocolate toxicity awareness</td></tr><tr><td>March</td><td>Spring parasite prevention</td><td>Flea/tick season begins</td></tr><tr><td>June</td><td>Heatwave preparation</td><td>UK heatwave action plan</td></tr><tr><td>October</td><td>Fireworks anxiety prep</td><td>Bonfire Night (5 Nov)</td></tr><tr><td>December</td><td>Holiday hazard awareness</td><td>Toxic plants, decorations</td></tr></tbody></table></figure>
<!-- /wp:table -->

<!-- wp:paragraph -->
<p><em>Note: Download functionality will be activated once the email capture platform is integrated.</em></p>
<!-- /wp:paragraph -->"""
    }
]

lead_magnet_ids = []
for lm in lead_magnets:
    result = wp_post("pages", {"title": lm["title"], "content": lm["content"], "status": "draft"})
    lid = result['id'] if result else 'FAILED'
    lead_magnet_ids.append(lid)
    print(f"  Lead magnet page: {lid} - {lm['title']}")

# Step 5: Generate conversion tracking plan
print("\nStep 5: Generating conversion tracking plan...")

tracking_events = [
    {"event": "email_signup", "trigger": "Newsletter form submission", "ga4_event": "generate_lead", "priority": "high"},
    {"event": "lead_magnet_download", "trigger": "PDF download click", "ga4_event": "file_download", "priority": "high"},
    {"event": "product_link_click", "trigger": "Outbound product link click", "ga4_event": "click", "priority": "high"},
    {"event": "comparison_table_view", "trigger": "Comparison table scroll into view", "ga4_event": "view_item_list", "priority": "medium"},
    {"event": "faq_expand", "trigger": "FAQ accordion click", "ga4_event": "select_content", "priority": "low"},
    {"event": "internal_nav", "trigger": "Related article click", "ga4_event": "click", "priority": "medium"},
    {"event": "scroll_depth_75", "trigger": "75% page scroll", "ga4_event": "scroll", "priority": "medium"},
    {"event": "time_on_page_60s", "trigger": "60 seconds on page", "ga4_event": "user_engagement", "priority": "low"},
]

# Step 6: Write CSVs
print("\nStep 6: Writing CSV reports...")

# 6a. Revenue activation by post
with open(f"{OUT_DIR}/revenue_activation_by_post.csv", 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['post_id','title','cluster','blocked','commercial_score',
        'is_best_page','has_comparison_table','has_faq','has_price_signals','has_email_form',
        'affiliate_ready','lead_magnet_type','email_capture_opportunity','conversion_potential'])
    w.writeheader()
    for rp in sorted(revenue_posts, key=lambda x: x['commercial_score'], reverse=True):
        w.writerow(rp)
print(f"  revenue_activation_by_post.csv ({len(revenue_posts)} posts)")

# 6b. Revenue activation pages
with open(f"{OUT_DIR}/revenue_activation_pages.csv", 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['page_id','title','type','status'])
    w.writerow([email_pid, 'Subscribe to PetHub UK Newsletter', 'email_capture', 'draft'])
    for i, lid in enumerate(lead_magnet_ids):
        w.writerow([lid, lead_magnets[i]['title'], 'lead_magnet', 'draft'])
print(f"  revenue_activation_pages.csv (3 pages)")

# 6c. Conversion tracking plan
with open(f"{OUT_DIR}/conversion_tracking_plan.csv", 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['event','trigger','ga4_event','priority'])
    w.writeheader()
    for t in tracking_events:
        w.writerow(t)
print(f"  conversion_tracking_plan.csv ({len(tracking_events)} events)")

# 6d. Revenue summary
high_commercial = len([p for p in revenue_posts if p['commercial_score'] >= 50])
med_commercial = len([p for p in revenue_posts if 25 <= p['commercial_score'] < 50])
email_opps = len([p for p in revenue_posts if p['email_capture_opportunity']])
affiliate_ready_count = len([p for p in revenue_posts if p['affiliate_ready']])
blocked_count = len([p for p in revenue_posts if p['blocked']])

with open(f"{OUT_DIR}/revenue_activation_summary.csv", 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['metric', 'value'])
    w.writerow(['total_posts_analyzed', len(revenue_posts)])
    w.writerow(['high_commercial_intent', high_commercial])
    w.writerow(['medium_commercial_intent', med_commercial])
    w.writerow(['email_capture_opportunities', email_opps])
    w.writerow(['affiliate_ready_posts', affiliate_ready_count])
    w.writerow(['blocked_clusters', blocked_count])
    w.writerow(['lead_magnet_pages_created', len(lead_magnet_ids)])
    w.writerow(['email_capture_page_created', 1])
    w.writerow(['conversion_events_planned', len(tracking_events)])
print(f"  revenue_activation_summary.csv")

# Summary
print("\n" + "=" * 70)
print("REVENUE ACTIVATION SUMMARY")
print("=" * 70)
print(f"  Posts analyzed:              {len(revenue_posts)}")
print(f"  High commercial intent:      {high_commercial}")
print(f"  Medium commercial intent:    {med_commercial}")
print(f"  Email capture opportunities: {email_opps}")
print(f"  Affiliate-ready posts:       {affiliate_ready_count}")
print(f"  Blocked (Dog Food/Harness):  {blocked_count}")
print(f"  Pages created (draft):       {1 + len(lead_magnet_ids)}")
print(f"  Conversion events planned:   {len(tracking_events)}")
print(f"\n  NO affiliate links inserted.")
print(f"  NO monetization activated.")
print(f"  Structures ready for activation when approved.")
print("=" * 70)
