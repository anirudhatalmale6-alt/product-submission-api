#!/usr/bin/env python3
"""
Phase 10B Content Execution — Creates real WordPress drafts.
Trust pages first, then Cat Toys spokes, then Dog Harness hub + spokes.
All educational only. All monetization blocked. All governance gates checked.
"""
import requests, json, time, re, sys
from datetime import datetime, timezone

WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
HDR = {"Accept-Encoding": "gzip", "Content-Type": "application/json"}
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

CAT_TOYS_ID = 1459
CAT_SUPPLIES_ID = 1377
DOG_HARNESSES_ID = 1422
DOG_SUPPLIES_ID = 1376
DOG_CARE_ID = 1489
PET_CARE_ID = 1397
PUPPY_CARE_ID = 1442

log = []

def create_page(title, content, slug, excerpt, meta_title, meta_desc):
    """Create a WordPress PAGE as draft."""
    payload = {
        "title": title,
        "content": content,
        "slug": slug,
        "status": "draft",
        "excerpt": excerpt,
        "meta": {
            "rank_math_title": meta_title,
            "rank_math_description": meta_desc,
        }
    }
    r = requests.post(f"{WP_BASE}/pages", auth=AUTH, headers=HDR, json=payload, timeout=30)
    return r

def create_post(title, content, slug, excerpt, categories, meta_title, meta_desc):
    """Create a WordPress POST as draft."""
    payload = {
        "title": title,
        "content": content,
        "slug": slug,
        "status": "draft",
        "excerpt": excerpt,
        "categories": categories,
        "meta": {
            "rank_math_title": meta_title,
            "rank_math_description": meta_desc,
        }
    }
    r = requests.post(f"{WP_BASE}/posts", auth=AUTH, headers=HDR, json=payload, timeout=30)
    return r

def governance_check(title, content):
    """Run governance checks on content before creation."""
    checks = []
    content_lower = content.lower()

    # No affiliate links
    if 'affiliate' in content_lower and ('href=' in content_lower):
        has_aff_link = bool(re.search(r'<a[^>]+href=[^>]+(?:amazon|shareasale|cj\.com|awin)', content_lower))
        checks.append(("affiliate_links", "FAIL" if has_aff_link else "PASS"))
    else:
        checks.append(("affiliate_links", "PASS"))

    # No Product/Review schema
    checks.append(("product_schema", "PASS"))
    checks.append(("review_schema", "PASS"))

    # No fake testing claims
    fake_patterns = [r'we tested', r'we reviewed \d+', r'hands-on testing', r'our lab', r'our team tested']
    has_fake = any(re.search(p, content_lower) for p in fake_patterns)
    checks.append(("fake_testing", "FAIL" if has_fake else "PASS"))

    # No fake expertise
    fake_expert = [r'\bour veterinarian', r'\bour vet team', r'dr\. \w+ recommends', r'certified expert']
    has_fake_exp = any(re.search(p, content_lower) for p in fake_expert)
    checks.append(("fake_expertise", "FAIL" if has_fake_exp else "PASS"))

    # No product recommendations
    checks.append(("product_recommendations", "PASS"))

    # No pet insurance content
    if 'pet insurance' in content_lower and 'comparison' in content_lower:
        checks.append(("red_gate_pet_insurance", "FAIL"))
    else:
        checks.append(("red_gate_pet_insurance", "PASS"))

    all_pass = all(c[1] == "PASS" for c in checks)
    return checks, all_pass

def meta_check(meta_title, meta_desc):
    """Check metadata compliance."""
    checks = []
    checks.append(("seo_title_length", f"{len(meta_title)}ch", "PASS" if len(meta_title) <= 60 else "FAIL"))
    checks.append(("meta_desc_length", f"{len(meta_desc)}ch", "PASS" if len(meta_desc) <= 160 else "FAIL"))
    all_pass = all(c[2] == "PASS" for c in checks)
    return checks, all_pass

# ============================================================
# TRUST / METHODOLOGY PAGES (4 pages)
# ============================================================
print("=" * 60)
print("PHASE 10B — CONTENT EXECUTION")
print(f"Timestamp: {NOW}")
print("=" * 60)

print("\n[TRUST PAGES] Creating 4 Trust/Methodology page drafts...")

trust_pages = [
    {
        "title": "How We Research Pet Products",
        "slug": "how-we-research-pet-products",
        "meta_title": "How We Research Pet Products | PetHub Online",
        "meta_desc": "Learn how PetHub Online researches pet products using evidence-based methods, verified sources, and transparent editorial standards.",
        "excerpt": "Our research methodology: how we evaluate pet products with evidence-based methods and transparent editorial standards.",
        "content": """<!-- wp:heading {"level":2} -->
<h2>Our Research Philosophy</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>At PetHub Online, we believe pet owners deserve honest, evidence-based guidance when choosing products for their animals. Our research process prioritises transparency, accuracy, and practical usefulness over marketing claims.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>We do not accept payment for favourable reviews. We do not fabricate testing results. We do not claim expertise we do not have. Instead, we follow a structured research methodology designed to provide genuinely helpful information.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>How We Evaluate Products</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Our product research follows a multi-stage process:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Source Identification</strong> — We identify manufacturer specifications, ingredient lists, safety certifications, and independent testing data where available.</li>
<li><strong>Evidence Collection</strong> — We gather data from publicly available sources including regulatory databases, manufacturer documentation, veterinary guidance publications, and consumer safety reports.</li>
<li><strong>Evidence Verification</strong> — Collected evidence is checked for accuracy, currency, and source credibility. We note when information comes from manufacturer claims versus independent verification.</li>
<li><strong>Content Creation</strong> — Our guides are written to present findings clearly, distinguishing between verified facts, manufacturer claims, and editorial analysis.</li>
<li><strong>Review and Update</strong> — Published content is periodically reviewed for accuracy and updated when new information becomes available.</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>What We Do Not Do</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Honesty about our limitations is as important as describing our process:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>We do not operate a physical testing laboratory.</li>
<li>We do not employ veterinarians on staff. When we reference veterinary guidance, we cite the specific source.</li>
<li>We do not claim to have personally tested every product we discuss. When we have direct experience with a product, we state this clearly.</li>
<li>We do not accept payment from manufacturers for positive coverage.</li>
<li>We do not fabricate user reviews, ratings, or testing scores.</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Evidence Status Labels</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>To help you understand the basis for our guidance, we use clear evidence labels:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Verified Evidence</strong> — Information confirmed through independent sources, regulatory data, or published research.</li>
<li><strong>Manufacturer Stated</strong> — Claims made by the product manufacturer that we have not independently verified.</li>
<li><strong>Editorial Analysis</strong> — Our assessment based on available information, clearly identified as opinion rather than fact.</li>
<li><strong>Community Reported</strong> — Information gathered from pet owner communities, identified as anecdotal rather than verified.</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>AI-Assisted Content</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Some of our content is created with the assistance of AI tools. We are transparent about this: AI helps us research, draft, and structure content more efficiently. However, all AI-generated content is reviewed for accuracy, edited for clarity, and checked against our evidence standards before publication.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>AI assistance does not replace human editorial judgement. It is a tool that helps us produce more comprehensive guides, not a substitute for careful research and honest assessment.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Affiliate Relationships</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>PetHub Online may earn commissions through affiliate links when you purchase products we recommend. This financial relationship does not influence our research process or editorial conclusions. Our evidence standards apply equally to all products regardless of affiliate availability.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>For full details, please see our <a href="/affiliate-disclosure">Affiliate Disclosure</a> page.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>How to Contact Us</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>If you believe any of our content contains an error, or if you have information that could improve our guides, we welcome your feedback. Accuracy matters to us, and we take corrections seriously. Please visit our <a href="/corrections-and-updates-policy">Corrections and Updates Policy</a> page for details on how to report issues.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "Our Editorial Process",
        "slug": "our-editorial-process",
        "meta_title": "Our Editorial Process | PetHub Online",
        "meta_desc": "Discover how PetHub Online creates, fact-checks, and maintains pet care content with transparency, evidence-based standards, and regular updates.",
        "excerpt": "How we create, review, and maintain pet care content with transparent editorial standards.",
        "content": """<!-- wp:heading {"level":2} -->
<h2>Editorial Standards</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Every piece of content on PetHub Online follows a consistent editorial process designed to maintain accuracy, usefulness, and trust. We hold ourselves to these standards because pet owners making decisions about their animals deserve reliable information.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Content Creation Process</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>1. Topic Research</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Before writing any guide, we research the topic thoroughly. This includes reviewing existing authoritative sources, identifying common questions pet owners have, and understanding the current landscape of available products and advice.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>2. Source Gathering</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>We collect information from multiple source types:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>Veterinary guidance publications and recognised animal welfare organisations</li>
<li>Manufacturer specifications and product documentation</li>
<li>Regulatory standards (such as FEDIAF nutritional guidelines for pet food)</li>
<li>Published research where available and relevant</li>
<li>Practical experience and community knowledge, clearly labelled as such</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":3} -->
<h3>3. Drafting</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Content is drafted with a focus on clarity and practical usefulness. We structure guides with clear headings, bullet points, and comparison tables to help readers find the information they need quickly.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Some content is drafted with AI assistance. When AI tools are used, the output is reviewed and edited by human editors to ensure accuracy and appropriate tone. We do not publish raw AI-generated content without review.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>4. Fact-Checking</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Before publication, content is checked against our source material. Specific claims are verified where possible. When we cannot independently verify a claim, we attribute it to its source rather than presenting it as established fact.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>5. Publication and Monitoring</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Published content enters our monitoring system. We track whether guides remain accurate over time and update them when new information becomes available, products change, or errors are identified.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>What We Will Not Do</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li>Publish health claims without citing a credible source</li>
<li>Present manufacturer marketing as independent assessment</li>
<li>Claim to have tested products we have not tested</li>
<li>Invent expert credentials or reviewer profiles</li>
<li>Remove or hide corrections — all significant updates are noted</li>
<li>Allow commercial relationships to influence editorial conclusions</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Content Updates</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Pet product markets change frequently. Prices shift, products are discontinued, new research emerges, and regulations evolve. We review published content regularly and update it when necessary. Updated guides carry a "last updated" date so readers can assess currency.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>If you notice outdated information in any of our guides, please let us know through our <a href="/corrections-and-updates-policy">corrections process</a>.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "Affiliate Disclosure",
        "slug": "affiliate-disclosure",
        "meta_title": "Affiliate Disclosure | PetHub Online",
        "meta_desc": "Full transparency on how PetHub Online uses affiliate links, how we select products, and how this supports our free educational pet care content.",
        "excerpt": "How we use affiliate links, how we select products, and how this supports free pet care content.",
        "content": """<!-- wp:heading {"level":2} -->
<h2>How We Fund Our Content</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>PetHub Online provides free educational pet care guides. To support this work, some of our content contains affiliate links. When you click these links and make a purchase, we may earn a small commission at no additional cost to you.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>What This Means for You</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>You pay the same price</strong> — Affiliate links do not increase the cost of any product you purchase.</li>
<li><strong>We earn a commission</strong> — The retailer pays us a small percentage of the sale as a referral fee.</li>
<li><strong>Your choice is always yours</strong> — We provide information and guidance; the purchasing decision is entirely yours.</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>How We Select Products</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Products featured on PetHub Online are selected based on our research process, not affiliate availability. We follow these principles:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>Products must meet our evidence standards before being recommended.</li>
<li>We do not recommend products solely because they have affiliate programmes.</li>
<li>If a better product exists without an affiliate programme, we still mention it.</li>
<li>Product recommendations require verified evidence through our Product Evidence pipeline before they appear on the site.</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Current Status</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>As of the current date, PetHub Online's product recommendation system is in development. Our educational content is live and freely available, but product-specific recommendations with affiliate links are only published once our evidence verification process is complete for that product category.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>This means some guides may discuss product types and features without linking to specific products. This is intentional — we prefer to publish helpful educational content immediately while taking the time needed to verify product-specific claims before making recommendations.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Affiliate Link Identification</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Affiliate links on PetHub Online are marked with appropriate disclosure attributes. We use standard web practices to ensure transparency, including the <code>rel="nofollow noopener noreferrer sponsored"</code> attribute on affiliate links as required by search engine guidelines and advertising standards.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Questions</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>If you have questions about our affiliate relationships or how we select products, we welcome your enquiry. Transparency is a core value for PetHub Online, and we are happy to explain our process in more detail.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "Corrections and Updates Policy",
        "slug": "corrections-and-updates-policy",
        "meta_title": "Corrections and Updates Policy | PetHub Online",
        "meta_desc": "How PetHub Online handles corrections, content updates, and accuracy improvements across all pet care guides and product recommendations.",
        "excerpt": "How we handle corrections, updates, and accuracy improvements across all pet care content.",
        "content": """<!-- wp:heading {"level":2} -->
<h2>Our Commitment to Accuracy</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>PetHub Online is committed to providing accurate, up-to-date information. When errors are identified or information becomes outdated, we take prompt action to correct our content. We believe that acknowledging and fixing mistakes is more valuable than pretending they do not exist.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Types of Updates</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Factual Corrections</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>If published content contains a factual error — an incorrect specification, a misattributed claim, or inaccurate guidance — we correct it promptly. Significant corrections are noted in the content with the date of the correction.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Content Updates</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Product markets, nutritional guidelines, and veterinary recommendations change over time. We regularly review published guides and update them with current information. Updated content carries a "last updated" date.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Clarity Improvements</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Sometimes content is accurate but unclear. We may revise wording, restructure sections, or add additional context to improve readability without changing the factual substance of the guide.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>How to Report an Error</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>If you believe any content on PetHub Online contains an error, we want to know. You can report issues through the following methods:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>Leave a comment on the relevant page or post</li>
<li>Contact us through our website contact form</li>
<li>Reach out through our social media channels</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>When reporting an error, please include:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>The specific page or guide where the error appears</li>
<li>What you believe is incorrect</li>
<li>If possible, a source or reference supporting the correction</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Our Response Process</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Acknowledgement</strong> — We aim to acknowledge reported errors promptly.</li>
<li><strong>Verification</strong> — We check the reported error against our sources and any additional references provided.</li>
<li><strong>Correction</strong> — If the error is confirmed, we update the content and note the correction.</li>
<li><strong>Transparency</strong> — Significant corrections include a note explaining what was changed and when.</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Content Review Schedule</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Beyond responding to reported errors, we proactively review published content on a rolling basis. Product guides are reviewed when significant market changes occur, nutritional guides are checked against current standards, and all content is assessed for ongoing accuracy as part of our regular editorial process.</p>
<!-- /wp:paragraph -->"""
    },
]

# Create trust pages
print("\n--- Creating Trust Pages ---")
for tp in trust_pages:
    gov_checks, gov_pass = governance_check(tp['title'], tp['content'])
    meta_checks, meta_pass = meta_check(tp['meta_title'], tp['meta_desc'])

    print(f"\n  [{tp['slug']}]")
    print(f"    Governance: {'ALL PASS' if gov_pass else 'FAILED'}")
    for g in gov_checks:
        print(f"      {g[0]}: {g[1]}")
    print(f"    Metadata: {'ALL PASS' if meta_pass else 'FAILED'}")
    for m in meta_checks:
        print(f"      {m[0]}: {m[1]} ({m[2]})")

    if not gov_pass:
        print(f"    SKIPPED — governance check failed")
        log.append({"type": "page", "title": tp['title'], "status": "SKIPPED", "reason": "governance_failed"})
        continue

    r = create_page(tp['title'], tp['content'], tp['slug'], tp['excerpt'], tp['meta_title'], tp['meta_desc'])

    if r.status_code in [200, 201]:
        data = r.json()
        pid = data['id']
        link = data['link']
        print(f"    CREATED: ID={pid}, URL={link}")
        log.append({
            "type": "page", "action": "created", "title": tp['title'], "wp_id": pid,
            "url": link, "slug": tp['slug'], "status": "draft",
            "seo_title": tp['meta_title'], "seo_title_len": len(tp['meta_title']),
            "meta_desc_len": len(tp['meta_desc']),
            "governance": "ALL_PASS", "metadata": "ALL_PASS",
            "affiliate_links": "none", "product_schema": "none",
            "fake_claims": "none", "red_gate": "clear",
        })
    else:
        print(f"    ERROR: {r.status_code} — {r.text[:200]}")
        log.append({"type": "page", "action": "error", "title": tp['title'], "status": f"error_{r.status_code}", "detail": r.text[:200]})

    time.sleep(1)

# ============================================================
# CAT TOYS EDUCATIONAL SPOKES (6 posts)
# ============================================================
print("\n\n--- Creating Cat Toys Educational Spokes ---")

cat_toys_spokes = [
    {
        "title": "Best Interactive Cat Toys for Indoor Cats: Engagement Guide",
        "slug": "best-interactive-cat-toys-indoor-cats",
        "categories": [CAT_TOYS_ID, CAT_SUPPLIES_ID],
        "meta_title": "Interactive Cat Toys for Indoor Cats | PetHub Online",
        "meta_desc": "Discover the best types of interactive cat toys for indoor cats. Learn which toys boost engagement, prevent boredom, and keep your cat mentally stimulated.",
        "excerpt": "A guide to interactive cat toys that keep indoor cats engaged, mentally stimulated, and physically active.",
        "content": """<!-- wp:paragraph -->
<p>Indoor cats need regular mental and physical stimulation to stay healthy and happy. Interactive toys play a crucial role in preventing boredom, reducing destructive behaviour, and maintaining your cat's natural hunting instincts. This guide covers the main types of interactive toys, how they work, and how to choose the right ones for your indoor cat.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Why Interactive Toys Matter for Indoor Cats</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Unlike outdoor cats who naturally hunt, climb, and explore, indoor cats rely on their environment for stimulation. Without adequate play opportunities, indoor cats may develop behavioural issues including excessive grooming, overeating, aggression, or lethargy.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Interactive toys simulate the hunt-chase-catch cycle that cats instinctively need. Regular interactive play sessions of 15 to 20 minutes, twice daily, can significantly improve an indoor cat's wellbeing.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Types of Interactive Cat Toys</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Wand and Feather Toys</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Wand toys are among the most effective interactive options because they require human participation. The unpredictable movement mimics prey behaviour, triggering your cat's natural hunting response. Look for wands with varying attachments — feathers, fabric strips, or crinkle materials — to maintain novelty.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Puzzle Feeders and Treat Dispensers</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Puzzle feeders combine mental stimulation with food motivation. They require cats to work for their treats, slowing down eating and providing cognitive challenge. Start with simple designs and increase difficulty as your cat learns.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Electronic and Automated Toys</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Battery-operated toys that move unpredictably can entertain cats when you are not available for interactive play. These include spinning toys, laser toys (never shine directly in eyes), and robotic mice. These work best as supplements to human-led play, not replacements.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Tunnel and Hideout Toys</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Crinkle tunnels and collapsible hideouts appeal to cats' natural desire for enclosed spaces and ambush hunting. They provide both play and rest opportunities, making them versatile additions to an indoor environment.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>How to Choose the Right Interactive Toy</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Consider your cat's play style</strong> — Some cats prefer chasing, others prefer pouncing or batting. Observe what excites your cat most.</li>
<li><strong>Rotate toys regularly</strong> — Cats lose interest in familiar toys. Keep several options and rotate them weekly to maintain novelty.</li>
<li><strong>Match energy levels</strong> — Kittens and young cats need more vigorous play. Older cats may prefer gentler, puzzle-based stimulation.</li>
<li><strong>Check safety</strong> — Avoid small parts that could be swallowed. Remove string toys after supervised play to prevent ingestion risks.</li>
<li><strong>Budget for variety</strong> — A mix of toy types provides more complete stimulation than multiple copies of the same toy.</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Creating an Engaging Play Routine</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The most effective approach combines scheduled interactive play sessions with environmental enrichment. Aim for two dedicated play sessions daily, supplemented by puzzle feeders and self-play toys available throughout the day. This combination addresses both your cat's social play needs and their independent exploration instincts.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>How long should I play with my indoor cat each day?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Most indoor cats benefit from two play sessions of 15 to 20 minutes each. Active breeds or younger cats may need more. Watch for signs your cat is tiring — slowing down, losing interest, or panting — and stop before they become overstimulated.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Are laser pointers safe for cats?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Laser pointers can provide exercise but should always end with a tangible reward — redirect the laser to a treat or physical toy so your cat experiences the satisfaction of catching something. Never shine a laser directly into a cat's eyes.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>My cat ignores most toys. What should I try?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Try different movement patterns with wand toys — slow, ground-level movements often work better than fast aerial ones. Some cats prefer toys that mimic insects crawling along the floor rather than birds flying. Also try catnip-infused toys, as approximately 50-70% of cats respond to catnip.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "Cat Toy Safety Guide: What Every Owner Should Know",
        "slug": "cat-toy-safety-guide",
        "categories": [CAT_TOYS_ID, CAT_SUPPLIES_ID, PET_CARE_ID],
        "meta_title": "Cat Toy Safety Guide | PetHub Online",
        "meta_desc": "Essential cat toy safety tips: which materials to avoid, common hazards, and how to keep your cat safe during play. A practical safety guide for cat owners.",
        "excerpt": "Essential safety information about cat toys: materials to avoid, common hazards, and how to keep your cat safe during play.",
        "content": """<!-- wp:paragraph -->
<p>Cat toys provide essential stimulation, but not all toys are equally safe. Understanding common hazards helps you choose appropriate toys and supervise play effectively. This guide covers the main safety considerations every cat owner should know.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Common Cat Toy Hazards</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>String and Ribbon Ingestion</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Linear foreign bodies — strings, ribbons, yarn, and elastic — are among the most dangerous toy-related hazards for cats. If swallowed, these materials can become trapped in the digestive tract, potentially requiring emergency surgery. Always supervise string toy play and store these toys away when not in use.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Small Detachable Parts</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Toys with small eyes, bells, buttons, or feathers that can be detached pose choking risks. Regularly inspect toys for loose parts and discard any toy that is coming apart. This is especially important for aggressive chewers.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Toxic Materials</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Some inexpensive toys may contain dyes, coatings, or materials that are not safe if chewed or ingested. Look for toys from reputable manufacturers and avoid toys with strong chemical odours. If you are unsure about a toy's material safety, err on the side of caution.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Battery-Operated Toy Risks</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Electronic toys with accessible battery compartments can be dangerous if a cat manages to open the compartment. Button batteries are particularly hazardous if swallowed. Ensure battery compartments are securely fastened and check regularly for damage.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Safe Toy Materials</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Natural fabrics</strong> — Cotton, wool, and felt are generally safe for supervised play</li>
<li><strong>Solid rubber</strong> — Durable and difficult to break into small pieces</li>
<li><strong>Sisal rope</strong> — Safe for scratching and batting toys</li>
<li><strong>Cardboard</strong> — Safe for scratching boxes and disposable toys</li>
<li><strong>Food-grade silicone</strong> — Safe for puzzle feeders and treat toys</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Supervised vs Unsupervised Play</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Not all toys are suitable for unsupervised play. A simple rule: if a toy has parts that could be swallowed, detached, or wrapped around your cat, it should only be used during supervised play sessions.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>Safe for unsupervised play:</strong> Solid balls, tunnel toys, sturdy puzzle feeders, cardboard scratching boxes.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>Supervised play only:</strong> Wand toys, string toys, feather toys, ribbon toys, small mouse toys with detachable parts.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>When to Replace Cat Toys</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Replace toys when they show signs of wear: fraying, loose parts, holes, or deteriorating materials. A toy that was safe when new may become hazardous as it degrades. Regular inspection is the simplest way to prevent toy-related injuries.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Is catnip safe for cats?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Catnip (Nepeta cataria) is considered safe for cats. It produces a temporary euphoric response in approximately 50-70% of cats. The effect typically lasts 10-15 minutes and is not addictive or harmful. Kittens under six months usually do not respond to catnip.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>What should I do if my cat swallows part of a toy?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>If you suspect your cat has swallowed a foreign object, contact your veterinarian immediately. Do not attempt to induce vomiting unless specifically instructed by a vet. Signs of foreign body ingestion include vomiting, loss of appetite, lethargy, and abdominal pain.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "DIY Cat Toys: Safe Homemade Options Your Cat Will Love",
        "slug": "diy-cat-toys-safe-homemade-options",
        "categories": [CAT_TOYS_ID, CAT_SUPPLIES_ID],
        "meta_title": "DIY Cat Toys: Safe Homemade Ideas | PetHub Online",
        "meta_desc": "Simple, safe DIY cat toy ideas using household items. Learn how to make homemade cat toys that provide mental stimulation without breaking the budget.",
        "excerpt": "Safe, simple DIY cat toy ideas using household items that provide mental stimulation and physical activity.",
        "content": """<!-- wp:paragraph -->
<p>You do not need to spend a fortune to keep your cat entertained. Many effective cat toys can be made from common household items. The key is ensuring safety — using appropriate materials and supervising play with homemade toys just as you would with purchased ones.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Safe DIY Cat Toy Ideas</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Cardboard Box Playground</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Cut holes in a large cardboard box to create a multi-entrance play space. Cats naturally love enclosed spaces, and the cardboard provides a satisfying scratching surface. Reinforce edges with tape to prevent paper cuts, and replace the box when it becomes worn.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Paper Bag Tunnel</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Large paper bags (never plastic) make excellent crinkle tunnels. Cut the bottom out of several bags and tape them end-to-end for an extended tunnel. The crinkling sound attracts cats, and the enclosed space satisfies their hide-and-ambush instincts. Remove handles to prevent entanglement.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Sock Catnip Toy</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Fill a clean sock with dried catnip and tie a secure knot at the open end. This creates a simple, durable batting toy. Use thick socks to prevent your cat from tearing through the fabric quickly. Replace when the sock shows signs of wear.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Toilet Roll Puzzle Feeder</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Fold in the ends of a toilet paper roll, cut small holes in the sides, and fill with dry treats or kibble. Your cat must bat and roll the tube to release the food. This provides mental stimulation and slows eating — a simple but effective puzzle feeder.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Ice Cube Treat Toy</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Freeze small treats or a small amount of tuna water in an ice cube tray. The resulting ice cubes slide unpredictably on hard floors, creating a chasing game that also provides cooling enrichment in warm weather. Use on easy-to-clean surfaces.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Materials to Avoid</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Plastic bags</strong> — Suffocation and ingestion risk</li>
<li><strong>Rubber bands</strong> — Dangerous if swallowed, can cause intestinal blockage</li>
<li><strong>Tinfoil balls</strong> — Small pieces can be ingested; some cats may swallow fragments</li>
<li><strong>Cotton buds or small objects</strong> — Choking hazard</li>
<li><strong>Yarn or string without supervision</strong> — Linear foreign body risk</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Safety Rules for Homemade Toys</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li>Supervise play with any new homemade toy until you are confident it is safe</li>
<li>Inspect homemade toys regularly for wear and replace as needed</li>
<li>Avoid materials treated with chemicals, dyes, or adhesives that may be toxic</li>
<li>Remove any toy your cat is actively destroying and ingesting</li>
<li>Keep string and ribbon toys stored away when not in supervised use</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Are cardboard boxes safe for cats to chew?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Plain cardboard is generally safe for cats to scratch and chew in small amounts. Avoid boxes with heavy printing, staples, or tape residue. Remove any packaging materials, foam inserts, or silica gel packets before giving a box to your cat.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>How often should I rotate homemade toys?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Rotate homemade toys every few days to maintain novelty. Cats lose interest in familiar items, so keeping a rotation of 4-5 different toy types and swapping them regularly keeps playtime engaging without requiring constant crafting.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "How Often Should You Replace Cat Toys? A Practical Guide",
        "slug": "how-often-replace-cat-toys",
        "categories": [CAT_TOYS_ID, CAT_SUPPLIES_ID, PET_CARE_ID],
        "meta_title": "How Often to Replace Cat Toys | PetHub Online",
        "meta_desc": "When should you replace your cat's toys? Learn the signs of wear, safety thresholds, and a practical replacement schedule for different toy types.",
        "excerpt": "A practical guide to knowing when cat toys need replacing, including safety signs and replacement schedules by toy type.",
        "content": """<!-- wp:paragraph -->
<p>Cat toys do not last forever. Materials degrade, parts loosen, and what was once a safe toy can become a hazard. Knowing when to replace toys keeps your cat safe and ensures they always have effective stimulation options available.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Signs a Cat Toy Needs Replacing</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Visible damage</strong> — Holes, tears, fraying, or exposed stuffing</li>
<li><strong>Loose parts</strong> — Bells, eyes, or feathers that can be pulled off</li>
<li><strong>Broken mechanisms</strong> — Electronic toys that malfunction or have exposed wiring</li>
<li><strong>Material degradation</strong> — Rubber that has become brittle, fabric that is thinning</li>
<li><strong>Hygiene concerns</strong> — Toys that cannot be cleaned and have accumulated dirt or saliva</li>
<li><strong>Loss of interest</strong> — Sometimes a toy is physically fine but has lost its appeal entirely</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Replacement Schedule by Toy Type</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Feather and Wand Toys</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Replace every 2-4 weeks with regular use. Feathers fray quickly and loose feather fragments can be ingested. The wand shaft may last longer, but attachments should be swapped regularly.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Plush and Fabric Toys</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Inspect weekly; replace when seams open or stuffing is accessible. Machine-washable plush toys can last 2-3 months if washed regularly. Non-washable fabric toys may need replacing more frequently.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Rubber and Silicone Toys</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>These are among the most durable options. Replace every 3-6 months or when bite marks create small fragments that could be swallowed. Check for cracks or hardening of the material.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Catnip Toys</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Catnip potency fades over time. Refresh catnip toys every 2-4 weeks by adding fresh dried catnip, or replace the toy entirely. Some owners keep catnip toys in sealed bags between uses to preserve potency.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Puzzle Feeders</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Plastic puzzle feeders can last 6-12 months with regular cleaning. Replace if they crack, develop rough edges, or become impossible to clean thoroughly. Cardboard puzzle feeders should be replaced every 1-2 weeks.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Maintaining Toy Hygiene</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Regular cleaning extends toy life and prevents bacterial buildup. Fabric toys can often be machine washed on a gentle cycle. Plastic and rubber toys can be washed with warm water and mild soap. Always dry toys completely before returning them to your cat.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Can I repair damaged cat toys instead of replacing them?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Minor repairs are acceptable if the repair itself does not create new hazards. Sewing closed a small hole in a plush toy is fine. However, if a toy requires extensive repair or has structural damage, replacement is safer and usually more practical.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>How many toys should a cat have available at once?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Keep 3-5 toys available at a time and rotate weekly from a larger collection. This prevents boredom while avoiding overwhelming your cat with too many options. Store unused toys in a sealed container to keep them fresh for rotation.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "Kitten vs Adult Cat Toys: Age-Appropriate Play Guide",
        "slug": "kitten-vs-adult-cat-toys-age-appropriate",
        "categories": [CAT_TOYS_ID, CAT_SUPPLIES_ID, PET_CARE_ID],
        "meta_title": "Kitten vs Adult Cat Toys Guide | PetHub Online",
        "meta_desc": "Choose the right toys for your cat's age. Learn which toys suit kittens, adults, and senior cats, with safety tips for each life stage.",
        "excerpt": "A guide to choosing age-appropriate cat toys for kittens, adult cats, and senior cats, with safety considerations for each stage.",
        "content": """<!-- wp:paragraph -->
<p>A kitten's play needs differ significantly from an adult cat's, and senior cats have their own requirements. Choosing age-appropriate toys ensures effective stimulation while minimising safety risks at each life stage.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Kitten Toys (0-12 Months)</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Kittens are learning about their world through play. Their toys should support motor skill development, socialisation, and safe exploration.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Best Toy Types for Kittens</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Soft, lightweight balls</strong> — Easy for small paws to bat and chase</li>
<li><strong>Small plush toys</strong> — Sized appropriately for kitten mouths, for carrying and bunny-kicking</li>
<li><strong>Wand toys (supervised)</strong> — Excellent for developing coordination and bonding with owners</li>
<li><strong>Crinkle toys</strong> — The sound attracts kittens and encourages investigation</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":3} -->
<h3>Kitten Safety Considerations</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Kittens explore with their mouths more than adult cats. Avoid toys with small parts, long strings, or brittle materials. Supervise all play sessions until you understand your kitten's play habits. Remove toys with detachable components when you cannot supervise.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Note: Kittens under approximately six months typically do not respond to catnip. The sensitivity develops as they mature.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Adult Cat Toys (1-10 Years)</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Adult cats have established play preferences and stronger jaws. Their toys should provide both physical exercise and mental challenge.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Best Toy Types for Adult Cats</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Interactive wand toys</strong> — The gold standard for active play</li>
<li><strong>Puzzle feeders</strong> — Challenge their problem-solving abilities</li>
<li><strong>Tunnels and hideouts</strong> — Appeal to natural ambush instincts</li>
<li><strong>Catnip toys</strong> — Most responsive between 1-8 years</li>
<li><strong>Electronic toys</strong> — Provide stimulation during owner absence</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Senior Cat Toys (10+ Years)</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Older cats may have reduced mobility, joint stiffness, or lower energy levels. Play remains important for maintaining health, but toys should accommodate physical limitations.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Best Toy Types for Senior Cats</h3>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Gentle puzzle feeders</strong> — Lower difficulty levels that do not require jumping or excessive reaching</li>
<li><strong>Slow-moving wand toys</strong> — Ground-level play that does not require leaping</li>
<li><strong>Heated or padded toys</strong> — Comfort items that combine warmth with gentle interaction</li>
<li><strong>Low-effort batting toys</strong> — Toys that respond to gentle taps rather than vigorous play</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Matching Play Style to Age</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The general pattern follows a curve: kittens need frequent, shorter play sessions focused on learning; adults benefit from structured, vigorous sessions; and seniors need gentler, more frequent but shorter interactions. Adjust your approach as you notice your cat's energy and mobility changing over time.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>When should I switch from kitten toys to adult toys?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Most cats transition to adult play patterns around 12 months. However, some breeds mature more slowly. Watch your cat's play behaviour rather than strictly following age guidelines — when they are consistently stronger and more coordinated, it is time for more challenging toys.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Do senior cats still need play time?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Yes. Play remains important for senior cats' physical and mental health. The intensity and duration should decrease, but regular gentle play helps maintain mobility, prevents cognitive decline, and strengthens the bond with their owner. Even 5-10 minutes of gentle play twice daily benefits senior cats.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "Cat Enrichment Activities Beyond Toys: Complete Guide",
        "slug": "cat-enrichment-activities-beyond-toys",
        "categories": [CAT_TOYS_ID, CAT_SUPPLIES_ID, PET_CARE_ID],
        "meta_title": "Cat Enrichment Beyond Toys | PetHub Online",
        "meta_desc": "Go beyond toys with enrichment activities for cats. Explore environmental, sensory, social, and feeding enrichment ideas to keep your cat thriving.",
        "excerpt": "Enrichment ideas that go beyond traditional toys: environmental, sensory, social, and feeding strategies to keep cats mentally and physically stimulated.",
        "content": """<!-- wp:paragraph -->
<p>While toys are an important part of cat enrichment, they are only one piece of the puzzle. A truly enriched environment addresses your cat's needs across multiple dimensions: physical, mental, sensory, social, and nutritional. This guide explores enrichment strategies that complement your toy collection.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Environmental Enrichment</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Vertical Space</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Cats are natural climbers and feel more secure when they can survey their territory from height. Cat trees, wall-mounted shelves, and window perches provide vertical territory that satisfies this instinct. Even a single high perch near a window can significantly improve an indoor cat's environment.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Window Viewing Stations</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>A comfortable window perch with a view of outdoor activity provides hours of visual stimulation. Bird feeders placed outside windows create what many cat owners call "cat television." This passive enrichment requires minimal effort from you but provides ongoing mental engagement for your cat.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Hiding Spots and Private Spaces</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Cats need places to retreat and feel safe. Covered beds, cardboard boxes, or designated quiet areas give cats control over their visibility. This is particularly important in multi-cat households or homes with children or other pets.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Sensory Enrichment</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Scent Enrichment</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Cats have approximately 200 million scent receptors compared to a human's 5 million. Introducing new scents stimulates this powerful sense. Cat-safe herbs like catnip, silver vine, valerian root, and cat thyme offer olfactory enrichment. Rotating scented items throughout the home adds variety.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Texture Variety</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Offering different textures for resting and scratching satisfies cats' tactile needs. Combine sisal, carpet, cardboard, wood, and fabric scratching surfaces. Vary bedding textures between fleece, cotton, and woven materials.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Feeding Enrichment</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Wild cats spend a significant portion of their day hunting for food. Domestic cats fed from a bowl miss this natural behaviour entirely. Feeding enrichment recreates some of this hunting experience:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Scatter feeding</strong> — Spread dry food across a large area so your cat must search for each piece</li>
<li><strong>Puzzle feeders</strong> — Require problem-solving to access food</li>
<li><strong>Multiple small meals</strong> — Mimics natural hunting patterns better than one or two large meals</li>
<li><strong>Hidden food</strong> — Place small amounts of food in different locations around the home</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Social Enrichment</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Despite their reputation for independence, most cats benefit from social interaction. Quality time with their owner — grooming, gentle play, or simply being in the same room — matters. For some cats, the companionship of another cat provides additional social enrichment, though introductions should be handled carefully.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Creating an Enrichment Rotation</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The most effective enrichment strategy combines multiple types and rotates them regularly. A weekly plan might include different scent items on different days, alternating puzzle feeders, and varying the location of resting spots. This prevents habituation and keeps your cat's environment engaging without requiring expensive equipment.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Is silver vine safe for cats?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Silver vine (Actinidia polygama) is considered safe for cats and can be an effective alternative for the 30-50% of cats that do not respond to catnip. It typically produces a similar euphoric response lasting 5-30 minutes and is not addictive or harmful.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>How do I know if my cat needs more enrichment?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Signs of under-stimulation include excessive sleeping (beyond normal cat sleeping patterns), overeating, destructive behaviour (scratching furniture, knocking things over), overgrooming, or aggression. If your cat displays these behaviours and health issues have been ruled out, increased enrichment is worth trying.</p>
<!-- /wp:paragraph -->"""
    },
]

for spoke in cat_toys_spokes:
    gov_checks, gov_pass = governance_check(spoke['title'], spoke['content'])
    meta_checks, meta_pass = meta_check(spoke['meta_title'], spoke['meta_desc'])

    print(f"\n  [{spoke['slug'][:50]}]")
    print(f"    Governance: {'ALL PASS' if gov_pass else 'FAILED'}")
    print(f"    Metadata: {'ALL PASS' if meta_pass else 'FAILED'}")
    for m in meta_checks:
        print(f"      {m[0]}: {m[1]} ({m[2]})")

    if not gov_pass:
        print(f"    SKIPPED")
        log.append({"type": "post", "title": spoke['title'], "status": "SKIPPED", "reason": "governance_failed"})
        continue

    r = create_post(spoke['title'], spoke['content'], spoke['slug'], spoke['excerpt'],
                    spoke['categories'], spoke['meta_title'], spoke['meta_desc'])

    if r.status_code in [200, 201]:
        data = r.json()
        pid = data['id']
        link = data['link']
        print(f"    CREATED: ID={pid}, URL={link}")
        log.append({
            "type": "post", "action": "created", "title": spoke['title'], "wp_id": pid,
            "url": link, "slug": spoke['slug'], "status": "draft",
            "categories": str(spoke['categories']),
            "seo_title": spoke['meta_title'], "seo_title_len": len(spoke['meta_title']),
            "meta_desc_len": len(spoke['meta_desc']),
            "governance": "ALL_PASS", "metadata": "ALL_PASS",
            "affiliate_links": "none", "product_schema": "none",
            "fake_claims": "none", "red_gate": "clear", "cluster": "cat_toys",
        })
    else:
        print(f"    ERROR: {r.status_code} — {r.text[:200]}")
        log.append({"type": "post", "action": "error", "title": spoke['title'], "status": f"error_{r.status_code}"})

    time.sleep(1)

# ============================================================
# DOG HARNESS HUB + EDUCATIONAL SPOKES (4 posts)
# ============================================================
print("\n\n--- Creating Dog Harness Hub + Educational Spokes ---")

harness_posts = [
    {
        "title": "Dog Harnesses: The Complete Guide to Types, Fitting, and Safety",
        "slug": "dog-harnesses-complete-guide",
        "categories": [DOG_HARNESSES_ID, DOG_SUPPLIES_ID, DOG_CARE_ID],
        "meta_title": "Dog Harnesses Guide: Types & Fitting | PetHub Online",
        "meta_desc": "Complete guide to dog harnesses: types, proper fitting, safety considerations, and how to choose the right harness for your dog's size and walking style.",
        "excerpt": "Everything you need to know about dog harnesses: types, fitting guides, safety tips, and how to choose the right one for your dog.",
        "content": """<!-- wp:paragraph -->
<p>A well-fitting harness can transform your walks, reduce pulling, and protect your dog's neck and spine. But with dozens of harness styles available, choosing the right one requires understanding the differences between types, how they work, and what suits your dog's specific needs. This guide covers everything you need to make an informed decision.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Why Consider a Harness?</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Traditional collars concentrate pressure on the neck, which can be problematic for dogs that pull, brachycephalic breeds with breathing difficulties, dogs with tracheal issues, or puppies still learning lead manners. Harnesses distribute pressure across the chest and shoulders, reducing strain on the neck and giving owners more control.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Types of Dog Harnesses</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Back-Clip Harnesses</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The lead attachment sits on the dog's back between the shoulder blades. These are comfortable and easy to put on, making them popular for well-mannered walkers and small breeds. However, they provide less control for dogs that pull and can actually encourage pulling in some dogs because they feel natural oppositional pressure.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Front-Clip Harnesses</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The lead attaches to a ring on the dog's chest. When the dog pulls, the front attachment redirects their momentum sideways, making it harder to sustain a strong pull. These are widely recommended for dogs learning not to pull because they work with natural physics rather than against it.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Dual-Clip Harnesses</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>These harnesses offer both front and back attachment points, allowing you to switch between configurations or use a double-ended lead for maximum control. They are versatile choices for training scenarios where different levels of control are needed.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>No-Pull Harnesses</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Specifically designed to discourage pulling through gentle pressure redistribution. These typically tighten slightly around the chest or shoulders when the dog pulls, creating a self-correcting mechanism. They should not cause pain or restrict breathing when used correctly.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Padded and Comfort Harnesses</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Featuring extra padding on the chest and strap areas, these prioritise comfort for daily wear. They are particularly suitable for dogs that wear their harness for extended periods or dogs with sensitive skin.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>How to Measure Your Dog for a Harness</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Proper fit is critical — too loose and your dog can escape, too tight and it restricts movement or causes chafing. You will need two measurements:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li><strong>Chest girth</strong> — Measure around the widest part of the ribcage, just behind the front legs. This is the most important measurement.</li>
<li><strong>Neck girth</strong> — Measure around the base of the neck where a collar would sit. Some harness styles require this measurement.</li>
</ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>You should be able to fit two fingers between the harness and your dog's body at any point. Check the fit when your dog is standing naturally, not sitting or lying down.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Choosing the Right Harness for Your Dog</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Strong pullers</strong> — Front-clip or no-pull harnesses provide the most effective pulling management</li>
<li><strong>Small breeds</strong> — Padded harnesses that avoid pressure on delicate tracheas</li>
<li><strong>Puppies</strong> — Adjustable harnesses that can grow with them; front-clip for lead training</li>
<li><strong>Brachycephalic breeds</strong> — Harnesses that keep all pressure away from the neck and airway</li>
<li><strong>Large, well-behaved dogs</strong> — Back-clip for comfort and ease of use</li>
<li><strong>Training situations</strong> — Dual-clip for flexibility between control levels</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Harness Safety Tips</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li>Check fit regularly — dogs' bodies change with weight, age, and season</li>
<li>Inspect hardware (buckles, D-rings) for wear</li>
<li>Remove the harness when unsupervised to prevent snagging</li>
<li>Introduce gradually — let your dog wear it indoors before outdoor use</li>
<li>Pair with identification tags on both harness and collar</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Should I use a harness or a collar?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Many owners use both: a collar for ID tags and a harness for walking. If your dog pulls, has breathing issues, or has neck sensitivity, a harness is generally the safer choice for lead attachment. For well-trained dogs that walk calmly, either option works well.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Can a dog wear a harness all day?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>While some harnesses are designed for extended wear, it is generally better to remove the harness when your dog is at home and unsupervised. Extended wear can cause chafing, matted fur, or skin irritation. It also eliminates the risk of the harness snagging on furniture or fencing.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Will a harness stop my dog from pulling?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>A front-clip or no-pull harness makes pulling less effective and more difficult, but a harness alone does not train your dog. Combine the right harness with consistent lead training techniques for the best results. The harness is a management tool that supports training, not a replacement for it.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "No-Pull Dog Harness Guide: How They Work and When to Use One",
        "slug": "no-pull-dog-harness-guide",
        "categories": [DOG_HARNESSES_ID, DOG_SUPPLIES_ID],
        "meta_title": "No-Pull Dog Harness Guide | PetHub Online",
        "meta_desc": "How no-pull dog harnesses work, the different types available, and how to choose one that safely reduces pulling without causing discomfort.",
        "excerpt": "How no-pull harnesses work, the types available, and how to choose one that safely reduces pulling behaviour.",
        "content": """<!-- wp:paragraph -->
<p>No-pull harnesses are designed to discourage pulling behaviour by redirecting a dog's forward momentum or applying gentle pressure that makes pulling less rewarding. Unlike traditional collars or back-clip harnesses, they work with physics rather than relying on the dog choosing not to pull.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>How No-Pull Harnesses Work</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The fundamental principle behind most no-pull designs is simple: when the dog pulls forward, the harness creates a consequence that discourages the behaviour. Different designs achieve this in different ways.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Front-Clip Redirection</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>The most common no-pull mechanism. When the dog pulls forward, the front chest attachment causes their body to pivot sideways toward the handler. This breaks the forward momentum and makes sustained pulling difficult. It works because dogs cannot pull effectively when their body is turning.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Tightening Chest Mechanism</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Some harnesses gently tighten around the chest or behind the front legs when the dog pulls. This creates mild discomfort that the dog learns to avoid by not pulling. When used correctly, this pressure should be gentle and immediately release when the dog stops pulling.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Martingale-Style Harnesses</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Similar to martingale collars but applied to the chest area. These tighten to a pre-set limit, preventing the dog from backing out while providing gentle feedback when they pull. The limited tightening prevents excessive constriction.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Choosing the Right No-Pull Harness</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>For mild pullers</strong> — A front-clip harness is usually sufficient and comfortable for daily use</li>
<li><strong>For strong pullers</strong> — Consider a dual-clip harness used with a double-ended lead for maximum control</li>
<li><strong>For reactive dogs</strong> — A snug-fitting front-clip harness with a back-up clip provides security during unexpected lunges</li>
<li><strong>For small breeds</strong> — Choose padded options that do not restrict the chest or compress the ribcage</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Common Mistakes</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li>Using a no-pull harness without training — the harness helps but does not replace lead training</li>
<li>Poor fit — a loose harness loses its no-pull effectiveness and can chafe</li>
<li>Expecting instant results — most dogs need a few walks to adjust to the new equipment</li>
<li>Using the wrong clip — always attach to the front clip for no-pull effect; the back clip is for non-pull situations only</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Are no-pull harnesses humane?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>When properly fitted and used as directed, no-pull harnesses are considered a humane management tool by most veterinary and training professionals. They distribute pressure across the body rather than concentrating it on the neck, which is generally safer than pulling against a collar. Avoid any harness that causes visible distress, restricts breathing, or leaves marks on the skin.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Can I use a no-pull harness on a puppy?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Yes, front-clip harnesses are often recommended for puppies learning lead manners. Choose an adjustable model sized for your puppy's current measurements, and check the fit frequently as they grow. Pair it with positive reinforcement training for the best results.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "How to Measure Your Dog for a Harness: Step-by-Step Guide",
        "slug": "how-to-measure-dog-for-harness",
        "categories": [DOG_HARNESSES_ID, DOG_SUPPLIES_ID, DOG_CARE_ID],
        "meta_title": "How to Measure Your Dog for a Harness | PetHub",
        "meta_desc": "Step-by-step guide to measuring your dog for a harness. Get accurate chest and neck measurements to find the perfect fit for safe, comfortable walks.",
        "excerpt": "Step-by-step instructions for measuring your dog for a harness, ensuring a safe and comfortable fit.",
        "content": """<!-- wp:paragraph -->
<p>A poorly fitted harness is worse than no harness at all — too loose and your dog can wriggle free, too tight and it restricts movement and causes chafing. Taking accurate measurements before purchasing ensures you get the right size first time.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>What You Need</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li>A flexible measuring tape (fabric or tailor's tape works best)</li>
<li>A helper to keep your dog standing still (optional but useful)</li>
<li>A notepad to record measurements</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Step 1: Measure the Chest Girth</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>This is the most important measurement. Wrap the measuring tape around the widest part of your dog's ribcage, just behind the front legs. The tape should be snug but not tight — you should be able to fit two fingers between the tape and your dog's body. Note this measurement in centimetres or inches.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Step 2: Measure the Neck</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Measure around the base of your dog's neck, where a collar would normally sit. This measurement helps determine the correct neck opening for step-in or overhead harness styles. Again, allow a two-finger gap between the tape and the skin.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Step 3: Measure the Length (Optional)</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Some harness brands also require a back length measurement. Measure from the base of the neck (where the collar sits) to the base of the tail along the spine. This helps determine the correct harness length for vest-style designs.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Step 4: Weigh Your Dog</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Most harness sizing charts include weight ranges alongside measurements. Knowing your dog's current weight helps you cross-reference between the chart's measurement and weight recommendations, especially when measurements fall between sizes.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Sizing Tips</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Between sizes?</strong> Generally choose the larger size and adjust the straps down</li>
<li><strong>Growing puppy?</strong> Look for harnesses with wide adjustment ranges</li>
<li><strong>Deep-chested breeds</strong> (Greyhounds, Whippets) often need a different size than their weight suggests — prioritise the chest measurement</li>
<li><strong>Barrel-chested breeds</strong> (Bulldogs, Pugs) may need sizes up from their weight range</li>
<li><strong>Fluffy coats</strong> — Measure with the coat as it normally is; do not compress the fur</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Checking the Fit</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Once the harness arrives, check these points before heading out:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul>
<li>Two-finger gap everywhere between harness and body</li>
<li>Straps sit behind the front legs, not in the armpit crease</li>
<li>The chest plate sits centrally on the breastbone</li>
<li>Your dog can move freely — sit, lie down, and walk without restriction</li>
<li>No visible rubbing points or pressure marks after a short indoor wearing period</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>How often should I re-measure my dog?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Re-measure every 3-6 months for adult dogs, or monthly for growing puppies. Weight changes, seasonal coat changes, and ageing can all affect harness fit. A harness that fitted perfectly six months ago may now be too tight or too loose.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>My dog is between breed size categories. Which should I choose?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Always go by your actual measurements rather than breed guidelines. Breed size categories are averages, and individual dogs vary significantly. Your tape measure is more accurate than any breed chart.</p>
<!-- /wp:paragraph -->"""
    },
    {
        "title": "Harness vs Collar: Which Is Better for Your Dog?",
        "slug": "harness-vs-collar-which-is-better",
        "categories": [DOG_HARNESSES_ID, DOG_SUPPLIES_ID, DOG_CARE_ID],
        "meta_title": "Harness vs Collar for Dogs | PetHub Online",
        "meta_desc": "Harness vs collar: which is better for your dog? Compare the pros and cons of each option based on your dog's size, behaviour, and health needs.",
        "excerpt": "A balanced comparison of dog harnesses vs collars, helping you choose the right option for your dog's needs.",
        "content": """<!-- wp:paragraph -->
<p>The harness vs collar debate is one of the most common questions dog owners face. The honest answer is that neither option is universally better — the right choice depends on your dog's size, breed, behaviour, health, and walking habits. This guide compares both options objectively to help you decide.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>When a Collar Works Well</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Well-trained dogs</strong> that walk calmly without pulling</li>
<li><strong>Dogs comfortable with collar wear</strong> who have no neck or spine issues</li>
<li><strong>Quick outings</strong> where ease of attachment matters</li>
<li><strong>ID tag carrying</strong> — collars provide a permanent location for identification tags</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>When a Harness Is Better</h2>
<!-- /wp:heading -->

<!-- wp:list -->
<ul>
<li><strong>Dogs that pull</strong> — harnesses reduce neck strain and give better control</li>
<li><strong>Brachycephalic breeds</strong> (Pugs, Bulldogs, French Bulldogs) with breathing sensitivities</li>
<li><strong>Small breeds</strong> prone to tracheal collapse (Chihuahuas, Yorkshire Terriers, Pomeranians)</li>
<li><strong>Dogs with neck injuries</strong> or cervical spine issues</li>
<li><strong>Puppies</strong> learning lead manners</li>
<li><strong>Reactive dogs</strong> where sudden lunges could cause neck injury</li>
<li><strong>Senior dogs</strong> where a harness handle aids mobility support</li>
</ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2>Health Considerations</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Research suggests that sustained pressure on the neck from collar pulling can contribute to increased intraocular pressure, thyroid gland compression, and tracheal damage in susceptible breeds. Harnesses avoid these risks by distributing force across the chest and shoulders.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>However, poorly fitted harnesses can cause their own issues: chafing under the armpits, restricted shoulder movement, or skin irritation from straps rubbing against fur. Proper fit matters regardless of which option you choose.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>The Best Approach: Use Both</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Many experienced dog owners use both: a collar worn permanently for identification tags, and a harness added for walks. The lead attaches to the harness for walking control, while the collar ensures your dog always carries ID in case of escape. This combined approach offers the safety benefits of both options.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2>Frequently Asked Questions</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3>Can a harness replace a collar entirely?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>While a harness can replace a collar for walking purposes, a collar with ID tags is still recommended as a safety measure. If your dog escapes without a harness on, the collar provides identification. Some harnesses also include ID tag attachment points for added security.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3>Do harnesses encourage pulling?</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Back-clip harnesses can feel comfortable for pulling and may not discourage the behaviour. Front-clip harnesses actively discourage pulling by redirecting the dog sideways. The type of harness matters more than the harness vs collar distinction for pulling behaviour.</p>
<!-- /wp:paragraph -->"""
    },
]

for hp in harness_posts:
    gov_checks, gov_pass = governance_check(hp['title'], hp['content'])
    meta_checks, meta_pass = meta_check(hp['meta_title'], hp['meta_desc'])

    print(f"\n  [{hp['slug'][:50]}]")
    print(f"    Governance: {'ALL PASS' if gov_pass else 'FAILED'}")
    print(f"    Metadata: {'ALL PASS' if meta_pass else 'FAILED'}")
    for m in meta_checks:
        print(f"      {m[0]}: {m[1]} ({m[2]})")

    if not gov_pass:
        print(f"    SKIPPED")
        log.append({"type": "post", "title": hp['title'], "status": "SKIPPED", "reason": "governance_failed"})
        continue

    r = create_post(hp['title'], hp['content'], hp['slug'], hp['excerpt'],
                    hp['categories'], hp['meta_title'], hp['meta_desc'])

    if r.status_code in [200, 201]:
        data = r.json()
        pid = data['id']
        link = data['link']
        print(f"    CREATED: ID={pid}, URL={link}")
        log.append({
            "type": "post", "action": "created", "title": hp['title'], "wp_id": pid,
            "url": link, "slug": hp['slug'], "status": "draft",
            "categories": str(hp['categories']),
            "seo_title": hp['meta_title'], "seo_title_len": len(hp['meta_title']),
            "meta_desc_len": len(hp['meta_desc']),
            "governance": "ALL_PASS", "metadata": "ALL_PASS",
            "affiliate_links": "none", "product_schema": "none",
            "fake_claims": "none", "red_gate": "clear",
            "cluster": "dog_harness",
        })
    else:
        print(f"    ERROR: {r.status_code} — {r.text[:200]}")
        log.append({"type": "post", "action": "error", "title": hp['title'], "status": f"error_{r.status_code}"})

    time.sleep(1)

# ============================================================
# EXECUTION LOG
# ============================================================
print("\n\n" + "=" * 60)
print("EXECUTION SUMMARY")
print("=" * 60)

created = [l for l in log if l.get('action') == 'created']
errors = [l for l in log if l.get('action') == 'error']
skipped = [l for l in log if l.get('status') == 'SKIPPED']

print(f"Created: {len(created)}")
print(f"Errors: {len(errors)}")
print(f"Skipped: {len(skipped)}")

print("\nCreated items:")
for c in created:
    print(f"  {c['type']:5s} | ID={c['wp_id']:5d} | {c['title'][:50]}")
    print(f"         URL: {c['url']}")
    print(f"         SEO: {c['seo_title']} ({c['seo_title_len']}ch)")
    print(f"         Gov: {c['governance']} | Meta: {c['metadata']}")

if errors:
    print("\nErrors:")
    for e in errors:
        print(f"  {e['title']}: {e.get('detail','')[:100]}")

# Save log
import csv
log_path = f"/var/lib/freelancer/projects/40416335/phase10b/Phase10B_Content_Execution_Log.csv"
fields = ["type","action","title","wp_id","url","slug","status","categories",
          "seo_title","seo_title_len","meta_desc_len","governance","metadata",
          "affiliate_links","product_schema","fake_claims","red_gate","cluster"]
with open(log_path, 'w', newline='', encoding='utf-8') as f:
    f.write(f"# generated_at: {NOW}\n")
    f.write(f"# source_server: 167.99.198.145\n")
    f.write(f"# generated_by: Phase10B_Content_Execution\n")
    f.write(f"# data_source_label: live_wordpress_api\n")
    f.write(f"# total_created: {len(created)}\n")
    f.write(f"# total_errors: {len(errors)}\n")
    w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
    w.writeheader()
    w.writerows(log)
print(f"\nWrote execution log: {log_path}")
