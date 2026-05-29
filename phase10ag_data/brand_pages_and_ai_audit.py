#!/usr/bin/env python3
"""
PetHub Online - Phase 10AG: Founder/Editorial Brand Pages + AI Footprint Audit
"""

import subprocess
import json
import csv
import re
import os
import html
from collections import Counter
from datetime import datetime

BASE_DIR = "/var/lib/freelancer/projects/40416335/phase10ag_data"
WP_API = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"


def wp_request(method, endpoint, data=None):
    """Make a WordPress API request using subprocess curl."""
    url = f"{WP_API}/{endpoint}"
    cmd = ["curl", "-s", "--compressed", "-u", AUTH]
    if method == "POST":
        cmd += ["-X", "POST"]
        if data:
            cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"ERROR decoding response for {endpoint}: {result.stdout[:500]}")
        return None


def strip_html(text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def count_words(text):
    """Count words in plain text."""
    return len(text.split())


# ============================================================
# PART 1: CREATE EDITORIAL BRAND PAGES
# ============================================================

def build_page1_content():
    """How We Evaluate Pet Products and Create Our Guides (~1500 words)"""
    blocks = []

    # Intro
    blocks.append(
        '<!-- wp:paragraph {"className":"editorial-intro"} -->\n'
        '<p class="editorial-intro">PetHub Online is a UK-based pet information platform focused on providing '
        'trustworthy, research-backed guidance for pet owners. We know that choosing the right food, equipment, '
        'or care routine for your pet can feel overwhelming, especially when so much conflicting advice exists '
        'online. Our goal is to cut through the noise and deliver clear, practical information that UK pet owners '
        'can rely on with confidence.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>Every guide, comparison, and recommendation on PetHub Online follows a structured research and editorial '
        'process. This page explains exactly how we work, what sources we use, and where our limitations lie. '
        'We believe transparency about our methods is just as important as the content itself.</p>\n'
        '<!-- /wp:paragraph -->'
    )

    # Our Research Process
    blocks.append(
        '<!-- wp:heading {"level":2} -->\n'
        '<h2>Our Research Process</h2>\n'
        '<!-- /wp:heading -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>Each guide published on PetHub Online goes through a multi-stage research process designed to ensure '
        'accuracy, relevance, and practical usefulness for UK pet owners.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p><strong>Stage 1: Topic Research and Scoping</strong><br>'
        'We begin by identifying topics where UK pet owners need clear, reliable information. This includes reviewing '
        'common questions asked in veterinary waiting rooms, pet forums, and search queries. We scope each guide to '
        'address specific, actionable questions rather than producing vague overviews.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p><strong>Stage 2: Source Review</strong><br>'
        'We review published guidance from recognised UK veterinary organisations, pet welfare charities, and '
        'regulatory bodies. For product-related guides, we examine manufacturer specifications, ingredient lists, '
        'nutritional data, and published safety standards. We cross-reference information across multiple sources '
        'to verify accuracy.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p><strong>Stage 3: Content Development</strong><br>'
        'Guides are structured to be scannable and practical. We use comparison tables, feature breakdowns, and '
        'clear category explanations to help readers make informed decisions. Where products are compared, we base '
        'our analysis on published specifications and verifiable features rather than subjective opinion.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p><strong>Stage 4: Editorial Review and Publication</strong><br>'
        'Before publication, each guide undergoes editorial review for factual accuracy, clarity, and consistency '
        'with our editorial standards. We check that all claims are supported by cited sources and that practical '
        'guidance is appropriate for UK pet owners.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p><strong>Stage 5: Ongoing Updates</strong><br>'
        'Pet care guidance evolves as new research emerges and products change. We schedule regular reviews of '
        'published guides to ensure information remains current and accurate. Significant updates are noted '
        'within the content.</p>\n'
        '<!-- /wp:paragraph -->'
    )

    # Sources We Trust
    blocks.append(
        '<!-- wp:heading {"level":2} -->\n'
        '<h2>Sources We Trust</h2>\n'
        '<!-- /wp:heading -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>Our research draws on guidance published by established UK and international organisations with '
        'recognised expertise in animal welfare, veterinary science, and pet nutrition. These include:</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:list -->\n'
        '<ul>'
        '<li><strong>RSPCA</strong> (Royal Society for the Prevention of Cruelty to Animals) — the UK\'s largest animal welfare charity, providing evidence-based care guidance</li>'
        '<li><strong>PDSA</strong> (People\'s Dispensary for Sick Animals) — a veterinary charity offering free, vet-written pet health information</li>'
        '<li><strong>BVA</strong> (British Veterinary Association) — the professional body representing veterinary surgeons in the UK</li>'
        '<li><strong>Dogs Trust</strong> — the UK\'s largest dog welfare charity, with published guidance on dog care, behaviour, and nutrition</li>'
        '<li><strong>The Kennel Club</strong> — the UK\'s leading authority on dog breeds, health testing, and breed-specific care</li>'
        '<li><strong>Cats Protection</strong> — the UK\'s leading cat welfare charity, providing practical feline care guidance</li>'
        '<li><strong>Blue Cross</strong> — a pet charity offering free veterinary treatment and published pet care resources</li>'
        '<li><strong>Battersea Dogs &amp; Cats Home</strong> — one of the UK\'s oldest and most recognised animal welfare organisations</li>'
        '<li><strong>PFMA</strong> (Pet Food Manufacturers\' Association) — the trade body for UK pet food manufacturers, publishing nutritional guidelines</li>'
        '<li><strong>International Cat Care</strong> — a leading international charity dedicated to improving cat welfare through evidence-based guidance</li>'
        '<li><strong>FEDIAF</strong> (European Pet Food Industry Federation) — sets nutritional guidelines used across Europe for pet food formulation</li>'
        '</ul>\n'
        '<!-- /wp:list -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>For product-specific guides, we also reference manufacturer-published specifications, ingredient '
        'declarations, DEFRA regulations, and UK trading standards where relevant. We clearly distinguish between '
        'guidance from welfare organisations and information from commercial sources.</p>\n'
        '<!-- /wp:paragraph -->'
    )

    # What We Don't Do
    blocks.append(
        '<!-- wp:heading {"level":2} -->\n'
        '<h2>What We Don\'t Do</h2>\n'
        '<!-- /wp:heading -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>Transparency about our limitations is part of our editorial commitment. Here is what PetHub Online '
        'does <em>not</em> do:</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:list -->\n'
        '<ul>'
        '<li><strong>We do not fabricate test results.</strong> We do not claim to have physically tested products in a laboratory or controlled environment unless we explicitly state otherwise. Our comparisons are based on published specifications, nutritional data, and manufacturer information.</li>'
        '<li><strong>We do not invent expert reviews.</strong> We do not create fictional veterinary endorsements or attribute opinions to named professionals who have not provided them. Where veterinary guidance is referenced, it comes from published organisational sources.</li>'
        '<li><strong>We do not create fake rankings.</strong> Our product guides use structured criteria based on published features and specifications. We explain the reasoning behind any comparisons so readers can evaluate them for their own circumstances.</li>'
        '<li><strong>We do not provide veterinary diagnoses.</strong> Our content is educational and informational. It is not a substitute for professional veterinary advice. We consistently encourage readers to consult their veterinarian for health concerns.</li>'
        '<li><strong>We do not guarantee product availability or pricing.</strong> Product details, prices, and availability change frequently. We link to retailers for current information but cannot guarantee accuracy at the time of reading.</li>'
        '</ul>\n'
        '<!-- /wp:list -->'
    )

    # Affiliate Links
    blocks.append(
        '<!-- wp:heading {"level":2} -->\n'
        '<h2>How We Handle Affiliate Links</h2>\n'
        '<!-- /wp:heading -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>Some guides on PetHub Online include affiliate links to retailers such as Amazon. When you purchase '
        'a product through one of these links, we may earn a small commission at no additional cost to you. '
        'This commission helps support the ongoing operation of PetHub Online, including research, content '
        'development, and site maintenance.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>Affiliate relationships do not influence our editorial content. Product inclusion, comparison criteria, '
        'and guide structure are determined by our editorial process, not by commercial arrangements. We include '
        'products in guides based on their relevance, published specifications, and suitability for UK pet owners, '
        'regardless of whether an affiliate link is available.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>We disclose affiliate relationships clearly. Guides containing affiliate links include a disclosure '
        'statement. We believe readers deserve to know when a commercial relationship exists, even when it does '
        'not affect editorial decisions.</p>\n'
        '<!-- /wp:paragraph -->'
    )

    # Corrections and Updates
    blocks.append(
        '<!-- wp:heading {"level":2} -->\n'
        '<h2>Corrections and Updates</h2>\n'
        '<!-- /wp:heading -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>We take factual accuracy seriously. If we identify an error in published content, or if a reader '
        'brings one to our attention, we correct it promptly. Significant corrections are noted within the '
        'content so readers are aware of changes.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>Product guides are reviewed on a regular schedule to check for discontinued products, reformulated '
        'ingredients, price changes, and updated guidance from welfare organisations. When a guide is substantially '
        'updated, we revise the publication date to reflect the most recent review.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>If you spot an error or believe a guide contains outdated information, we welcome feedback. You can '
        'reach the editorial team through our contact page. We review all corrections reports and respond as '
        'quickly as possible.</p>\n'
        '<!-- /wp:paragraph -->'
    )

    # FAQ Section
    blocks.append(
        '<!-- wp:heading {"level":2} -->\n'
        '<h2>Frequently Asked Questions About Our Methodology</h2>\n'
        '<!-- /wp:heading -->'
    )

    faq_items = [
        (
            "Do you physically test every product you write about?",
            "No. Our guides are based on published specifications, manufacturer data, nutritional information, "
            "and guidance from recognised UK welfare organisations. We do not claim to conduct physical product "
            "testing unless explicitly stated. Our comparisons are educational, designed to help readers understand "
            "differences between products based on verifiable, published information."
        ),
        (
            "Who writes PetHub Online content?",
            "Content is produced by the PetHub Online editorial team using a combination of research, AI-assisted "
            "drafting tools, and editorial review processes. We do not fabricate author biographies or claim "
            "expertise we do not possess. Our strength lies in thorough research methodology and transparent sourcing."
        ),
        (
            "How do you decide which products to include in comparison guides?",
            "Product selection is based on relevance to UK pet owners, availability through UK retailers, published "
            "specification quality, and representation across different price points and product categories. We aim "
            "to provide a balanced overview rather than promoting specific brands."
        ),
        (
            "Can I trust your recommendations if you earn affiliate commissions?",
            "Our editorial process operates independently from our affiliate relationships. Products are included "
            "in guides based on their relevance and specifications, not on commission rates. Many products featured "
            "in our guides do not have affiliate links at all. We believe our transparent disclosure of affiliate "
            "relationships helps readers make their own judgements."
        ),
        (
            "How often do you update your guides?",
            "Guides are scheduled for regular review, typically every three to six months depending on the topic. "
            "Fast-moving categories such as pet food may be reviewed more frequently. We also update guides when "
            "readers report errors or when significant changes occur in the products or guidance we reference."
        ),
    ]

    for question, answer in faq_items:
        blocks.append(
            f'<!-- wp:heading {{"level":3}} -->\n'
            f'<h3>{question}</h3>\n'
            f'<!-- /wp:heading -->'
        )
        blocks.append(
            f'<!-- wp:paragraph -->\n'
            f'<p>{answer}</p>\n'
            f'<!-- /wp:paragraph -->'
        )

    # Trust Footer
    blocks.append(
        '<!-- wp:separator {"className":"is-style-wide"} -->\n'
        '<hr class="wp-block-separator is-style-wide"/>\n'
        '<!-- /wp:separator -->'
    )
    blocks.append(
        '<!-- wp:paragraph {"className":"trust-footer","fontSize":"small"} -->\n'
        '<p class="trust-footer has-small-font-size"><em>This page was last reviewed by the PetHub Online editorial '
        'team in May 2026. Our methodology is subject to continuous improvement. If you have questions or feedback '
        'about our editorial process, please contact us through our contact page.</em></p>\n'
        '<!-- /wp:paragraph -->'
    )

    return "\n\n".join(blocks)


def build_page2_content():
    """Our Editorial Mission (~1000 words)"""
    blocks = []

    # Mission statement
    blocks.append(
        '<!-- wp:paragraph {"className":"mission-statement","fontSize":"large"} -->\n'
        '<p class="mission-statement has-large-font-size"><strong>Our mission is to provide clear, practical, '
        'research-backed pet care guidance that UK pet owners can trust and act on with confidence.</strong></p>\n'
        '<!-- /wp:paragraph -->'
    )

    # Why PetHub Online Exists
    blocks.append(
        '<!-- wp:heading {"level":2} -->\n'
        '<h2>Why PetHub Online Exists</h2>\n'
        '<!-- /wp:heading -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>The UK pet information landscape is crowded with conflicting advice. A single search for something '
        'as straightforward as "best dog food for puppies" returns hundreds of results, many of which contradict '
        'each other, rely on undisclosed commercial relationships, or present opinion as fact. For pet owners '
        'trying to make responsible decisions, this creates genuine confusion.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>PetHub Online was created to address this problem directly. Rather than adding more noise, we aim '
        'to provide well-structured, research-backed guides that help UK pet owners understand their options '
        'clearly. We focus on practical usefulness: guidance that readers can actually apply to their daily '
        'pet care decisions.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>The UK has specific regulations, product availability, veterinary standards, and welfare organisations '
        'that differ from other markets. Much online pet content is written for a US audience and may not apply '
        'to UK pet owners. PetHub Online is built specifically for the UK context, referencing UK-available '
        'products, UK welfare organisations, and UK regulatory standards.</p>\n'
        '<!-- /wp:paragraph -->'
    )

    # Our Editorial Standards
    blocks.append(
        '<!-- wp:heading {"level":2} -->\n'
        '<h2>Our Editorial Standards</h2>\n'
        '<!-- /wp:heading -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>Every piece of content published on PetHub Online is held to the following editorial standards:</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:list -->\n'
        '<ul>'
        '<li><strong>Factual Accuracy:</strong> Claims must be supported by published guidance from recognised '
        'organisations or verifiable product specifications. We do not present opinion as fact or fabricate '
        'supporting evidence.</li>'
        '<li><strong>Practical Usefulness:</strong> Every guide must answer a real question that UK pet owners '
        'are asking. Abstract or theoretical content without practical application does not meet our publication '
        'threshold.</li>'
        '<li><strong>UK-Specific Relevance:</strong> Product recommendations, regulatory references, and care '
        'guidance must be applicable to the UK market. We reference UK-available products and UK welfare '
        'organisations.</li>'
        '<li><strong>Regular Review:</strong> Published content is not treated as permanent. Guides are scheduled '
        'for periodic review to ensure they reflect current products, pricing, and guidance.</li>'
        '<li><strong>Transparency About Limitations:</strong> Where our knowledge is incomplete or where guidance '
        'may not apply to every situation, we say so explicitly. We do not overstate our expertise or the '
        'scope of our recommendations.</li>'
        '</ul>\n'
        '<!-- /wp:list -->'
    )

    # AI-Assisted, Editorially Reviewed
    blocks.append(
        '<!-- wp:heading {"level":2} -->\n'
        '<h2>AI-Assisted, Editorially Reviewed</h2>\n'
        '<!-- /wp:heading -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>PetHub Online uses AI tools as part of its content creation process. We believe in being straightforward '
        'about this rather than obscuring it behind fictional author biographies or fabricated credentials.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>AI assists with research synthesis, content structuring, and initial drafting. The editorial review '
        'process ensures that AI-generated content is factually accurate, properly sourced, practically useful, '
        'and aligned with our editorial standards. This combination allows us to produce thoroughly researched '
        'content at a consistent quality level.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>We do not create fake human author personas. We do not invent veterinary qualifications, pet ownership '
        'histories, or professional backgrounds that do not exist. Content is attributed to the PetHub Online '
        'editorial team, which accurately reflects how it is produced.</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>This approach prioritises honesty over the appearance of traditional editorial staffing. We believe '
        'readers are better served by transparent methodology than by fictional author credentials. The quality '
        'of our content should stand on its own merits: the thoroughness of research, the accuracy of information, '
        'and the practical usefulness of guidance.</p>\n'
        '<!-- /wp:paragraph -->'
    )

    # What Makes Us Different
    blocks.append(
        '<!-- wp:heading {"level":2} -->\n'
        '<h2>What Makes Us Different</h2>\n'
        '<!-- /wp:heading -->'
    )
    blocks.append(
        '<!-- wp:paragraph -->\n'
        '<p>PetHub Online is built around several principles that shape how we approach pet care content:</p>\n'
        '<!-- /wp:paragraph -->'
    )
    blocks.append(
        '<!-- wp:list -->\n'
        '<ul>'
        '<li><strong>Practical Usefulness First:</strong> Every guide is structured to answer real questions with '
        'actionable information. We focus on what readers need to know to make informed decisions, not on '
        'word count or keyword density.</li>'
        '<li><strong>UK-Specific Guidance:</strong> Our content is written for UK pet owners, referencing UK-available '
        'products, UK veterinary organisations, and UK-specific regulations. We do not repackage US-centric '
        'content for a UK audience.</li>'
        '<li><strong>Educational Depth:</strong> Rather than surface-level listicles, our guides explain the reasoning '
        'behind recommendations. We help readers understand nutritional principles, welfare considerations, and '
        'product features so they can evaluate options for their specific circumstances.</li>'
        '<li><strong>Transparent Methodology:</strong> We publish our research process, disclose our affiliate '
        'relationships, acknowledge our use of AI tools, and are honest about our limitations. Trust is earned '
        'through transparency, not through manufactured credentials.</li>'
        '<li><strong>Source-Based Authority:</strong> Our authority comes from the quality of our sources and the '
        'rigour of our research process, not from invented personal expertise. We cite recognised UK welfare '
        'organisations, veterinary bodies, and published nutritional standards.</li>'
        '</ul>\n'
        '<!-- /wp:list -->'
    )

    # Trust Footer
    blocks.append(
        '<!-- wp:separator {"className":"is-style-wide"} -->\n'
        '<hr class="wp-block-separator is-style-wide"/>\n'
        '<!-- /wp:separator -->'
    )
    blocks.append(
        '<!-- wp:paragraph {"className":"trust-footer","fontSize":"small"} -->\n'
        '<p class="trust-footer has-small-font-size"><em>PetHub Online is committed to continuous improvement of '
        'our editorial standards and methodology. This page reflects our current approach as of May 2026. '
        'For questions about our editorial mission or to provide feedback, please visit our contact page.</em></p>\n'
        '<!-- /wp:paragraph -->'
    )

    return "\n\n".join(blocks)


def create_draft_pages():
    """Create the two editorial brand pages as drafts."""
    pages_log = []

    # Page 1
    page1_content = build_page1_content()
    page1_plain = strip_html(page1_content)
    page1_wc = count_words(page1_plain)
    print(f"Page 1 word count: {page1_wc}")

    page1_data = {
        "title": "How We Evaluate Pet Products and Create Our Guides",
        "content": page1_content,
        "status": "draft",
        "slug": "how-we-evaluate-pet-products",
    }
    resp1 = wp_request("POST", "pages", page1_data)
    if resp1 and "id" in resp1:
        print(f"  Created page 1: ID {resp1['id']}, status={resp1.get('status')}")
        pages_log.append({
            "id": resp1["id"],
            "title": "How We Evaluate Pet Products and Create Our Guides",
            "type": "page",
            "word_count": page1_wc,
            "status": resp1.get("status", "draft"),
        })
    else:
        print(f"  ERROR creating page 1: {resp1}")

    # Page 2
    page2_content = build_page2_content()
    page2_plain = strip_html(page2_content)
    page2_wc = count_words(page2_plain)
    print(f"Page 2 word count: {page2_wc}")

    page2_data = {
        "title": "Our Editorial Mission",
        "content": page2_content,
        "status": "draft",
        "slug": "our-editorial-mission",
    }
    resp2 = wp_request("POST", "pages", page2_data)
    if resp2 and "id" in resp2:
        print(f"  Created page 2: ID {resp2['id']}, status={resp2.get('status')}")
        pages_log.append({
            "id": resp2["id"],
            "title": "Our Editorial Mission",
            "type": "page",
            "word_count": page2_wc,
            "status": resp2.get("status", "draft"),
        })
    else:
        print(f"  ERROR creating page 2: {resp2}")

    # Write log CSV
    log_path = os.path.join(BASE_DIR, "brand_pages_log.csv")
    with open(log_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "type", "word_count", "status"])
        writer.writeheader()
        writer.writerows(pages_log)
    print(f"  Brand pages log written to {log_path}")

    return pages_log


# ============================================================
# PART 2: AI FOOTPRINT ANALYSIS
# ============================================================

OVERUSED_PHRASES = [
    "whether you",
    "in this guide",
    "let's explore",
    "when it comes to",
    "it's important to",
    "in summary",
    "in conclusion",
    "overall",
    "at the end of the day",
    "here's the thing",
    "it's worth noting",
    "it's no secret",
    "rest assured",
    "without further ado",
    "dive into",
    "deep dive",
    "game changer",
    "makes all the difference",
    "not all .* are created equal",
    "look no further",
    "you're not alone",
    "the good news is",
    "the bottom line",
    "peace of mind",
    "a wide range of",
    "designed to",
    "it's essential to",
    "it's crucial to",
    "plays a vital role",
    "plays a crucial role",
]

TRANSITION_PHRASES = [
    "additionally",
    "furthermore",
    "moreover",
    "however",
    "that said",
    "that being said",
    "on the other hand",
    "in addition",
    "as a result",
    "consequently",
    "nevertheless",
    "nonetheless",
    "similarly",
    "likewise",
    "in contrast",
]

POST_IDS = [3836, 3837, 3838, 3839, 4027, 4174, 4195, 4314, 4406, 4566,
            4570, 4787, 5032, 5296, 5414, 5462, 5511, 5519, 5522, 5523]


def fetch_post(post_id):
    """Fetch a single post by ID."""
    resp = wp_request("GET", f"posts/{post_id}")
    if resp and "id" in resp:
        return resp
    print(f"  WARNING: Could not fetch post {post_id}: {resp}")
    return None


def analyze_post(post):
    """Analyze a single post for AI footprint patterns."""
    raw_content = post.get("content", {}).get("rendered", "")
    plain = strip_html(raw_content)
    title = strip_html(post.get("title", {}).get("rendered", ""))

    # Split into paragraphs
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n|<\/p>|<br\s*\/?>|<\/li>', raw_content) if strip_html(p).strip()]
    paragraphs = [strip_html(p) for p in paragraphs]
    paragraphs = [p for p in paragraphs if len(p) > 20]

    # 1. Repetitive sentence starters (count paragraphs starting with same 3 words)
    starters = []
    for p in paragraphs:
        words = p.split()[:3]
        if len(words) == 3:
            starters.append(" ".join(words).lower())
    starter_counts = Counter(starters)
    repetitive_starters = sum(count for starter, count in starter_counts.items() if count >= 3)

    # 2. Overused phrases
    plain_lower = plain.lower()
    overused_count = 0
    overused_found = {}
    for phrase in OVERUSED_PHRASES:
        matches = len(re.findall(phrase, plain_lower))
        if matches > 0:
            overused_count += matches
            overused_found[phrase] = matches

    # 3. Template transitions
    transition_count = 0
    transition_found = {}
    for trans in TRANSITION_PHRASES:
        # Check for sentence-starting transitions
        pattern = r'(?:^|\. )' + re.escape(trans) + r'[,\s]'
        matches = len(re.findall(pattern, plain_lower))
        if matches > 0:
            transition_count += matches
            transition_found[trans] = matches

    # 4. Generic intro detection
    intro_text = " ".join(paragraphs[:2]).lower() if len(paragraphs) >= 2 else plain_lower[:300]
    generic_intro_markers = [
        "in this guide", "in this article", "in this post",
        "we'll explore", "we will explore", "let's explore",
        "we'll cover", "we will cover", "let's take a look",
        "whether you're a", "if you're looking for",
        "choosing the right", "finding the best",
        "welcome to our", "looking for the best",
    ]
    generic_intro = any(marker in intro_text for marker in generic_intro_markers)

    # 5. Generic outro detection
    outro_text = " ".join(paragraphs[-3:]).lower() if len(paragraphs) >= 3 else plain_lower[-500:]
    generic_outro_markers = [
        "in conclusion", "in summary", "to sum up",
        "at the end of the day", "the bottom line",
        "we hope this guide", "we hope this article",
        "happy shopping", "happy feeding",
        "your furry friend", "your furry companion",
        "whatever you choose", "whichever you choose",
        "remember, every", "remember that every",
    ]
    generic_outro = any(marker in outro_text for marker in generic_outro_markers)

    # 6. Repetitive FAQ pattern detection
    faq_sections = re.findall(r'<h[23][^>]*>.*?\?.*?</h[23]>', raw_content, re.IGNORECASE)
    faq_answers = []
    for i, faq in enumerate(faq_sections):
        pos = raw_content.find(faq)
        if pos >= 0:
            answer_text = raw_content[pos + len(faq):pos + len(faq) + 500]
            answer_plain = strip_html(answer_text).strip()
            if answer_plain:
                first_words = " ".join(answer_plain.split()[:4]).lower()
                faq_answers.append(first_words)

    faq_answer_counts = Counter(faq_answers)
    repetitive_faq = any(c >= 3 for c in faq_answer_counts.values()) if faq_answers else False

    # Calculate composite score (0-100, lower is better)
    score = 0
    score += min(repetitive_starters * 3, 20)       # max 20
    score += min(overused_count * 2, 25)             # max 25
    score += min(transition_count * 2, 15)           # max 15
    score += 10 if generic_intro else 0              # max 10
    score += 10 if generic_outro else 0              # max 10
    score += 10 if repetitive_faq else 0             # max 10
    # Density factor: penalize high phrase density
    word_count = count_words(plain)
    if word_count > 0:
        density = (overused_count + transition_count) / (word_count / 100)
        score += min(int(density * 2), 10)           # max 10
    score = min(score, 100)

    return {
        "id": post["id"],
        "title": title,
        "repetitive_starters_count": repetitive_starters,
        "overused_phrases_count": overused_count,
        "template_transitions_count": transition_count,
        "generic_intro": "YES" if generic_intro else "NO",
        "generic_outro": "YES" if generic_outro else "NO",
        "repetitive_faq_pattern": "YES" if repetitive_faq else "NO",
        "ai_footprint_score": score,
        "_overused_detail": overused_found,
        "_transition_detail": transition_found,
        "_word_count": word_count,
    }


def run_ai_footprint_audit():
    """Fetch posts and run AI footprint analysis."""
    print("\n=== AI FOOTPRINT AUDIT ===")

    results = []
    global_phrase_counts = Counter()
    global_phrase_posts = {}

    for pid in POST_IDS:
        print(f"  Fetching post {pid}...")
        post = fetch_post(pid)
        if not post:
            continue

        analysis = analyze_post(post)
        results.append(analysis)
        print(f"    {analysis['title'][:60]}... score={analysis['ai_footprint_score']}")

        # Aggregate phrase counts
        for phrase, count in analysis["_overused_detail"].items():
            global_phrase_counts[phrase] += count
            if phrase not in global_phrase_posts:
                global_phrase_posts[phrase] = set()
            global_phrase_posts[phrase].add(str(analysis["id"]))

        for phrase, count in analysis["_transition_detail"].items():
            global_phrase_counts[phrase] += count
            if phrase not in global_phrase_posts:
                global_phrase_posts[phrase] = set()
            global_phrase_posts[phrase].add(str(analysis["id"]))

    # Write main audit CSV
    audit_path = os.path.join(BASE_DIR, "ai_footprint_audit.csv")
    fieldnames = ["id", "title", "repetitive_starters_count", "overused_phrases_count",
                  "template_transitions_count", "generic_intro", "generic_outro",
                  "repetitive_faq_pattern", "ai_footprint_score"]
    with open(audit_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            row = {k: r[k] for k in fieldnames}
            writer.writerow(row)
    print(f"\n  Audit CSV written to {audit_path}")

    # Write pattern summary CSV (top 10 most overused)
    summary_path = os.path.join(BASE_DIR, "ai_pattern_summary.csv")
    top_phrases = global_phrase_counts.most_common(10)

    recommendations = {
        "whether you": "Replace with specific audience targeting or remove introductory hedging",
        "in this guide": "Remove meta-references; let content speak for itself",
        "let's explore": "Replace with direct statements; avoid conversational AI filler",
        "when it comes to": "Delete entirely or rephrase with direct subject-verb structure",
        "it's important to": "Replace with specific reasoning or remove hedging language",
        "in summary": "Remove or replace with a specific concluding insight",
        "in conclusion": "Remove or replace with a forward-looking statement",
        "overall": "Replace with specific evaluative language tied to criteria",
        "at the end of the day": "Delete entirely; cliché with no informational value",
        "here's the thing": "Delete entirely; conversational filler with no value",
        "additionally": "Vary sentence structure; integrate points without transition crutches",
        "furthermore": "Remove or restructure paragraph flow to eliminate need for transition",
        "moreover": "Replace with integrated paragraph structure",
        "however": "Use sparingly; restructure contrasting points into natural flow",
        "that said": "Remove or integrate contrast into sentence structure naturally",
        "it's worth noting": "Remove hedge; state the information directly",
        "designed to": "Replace with specific action verbs describing actual function",
        "peace of mind": "Replace with specific benefits or outcomes",
        "a wide range of": "Replace with specific quantities or examples",
        "it's essential to": "Replace with specific reasoning or remove hedging",
        "it's crucial to": "Replace with specific reasoning or remove hedging",
        "plays a vital role": "Replace with specific description of the role",
        "plays a crucial role": "Replace with specific description of the role",
        "dive into": "Replace with direct verbs: examine, review, compare",
        "the good news is": "Remove filler; state the information directly",
        "you're not alone": "Remove; patronising filler phrase",
        "that being said": "Remove or restructure the contrast naturally",
        "rest assured": "Remove; state the reassuring fact directly",
        "look no further": "Remove; clickbait filler with no value",
    }

    with open(summary_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["phrase", "occurrence_count", "posts_containing", "recommendation"])
        writer.writeheader()
        for phrase, count in top_phrases:
            posts = ", ".join(sorted(global_phrase_posts.get(phrase, set())))
            rec = recommendations.get(phrase, "Review usage and vary language to reduce AI pattern visibility")
            writer.writerow({
                "phrase": phrase,
                "occurrence_count": count,
                "posts_containing": posts,
                "recommendation": rec,
            })
    print(f"  Pattern summary CSV written to {summary_path}")

    # Print summary stats
    print("\n  === SUMMARY STATS ===")
    scores = [r["ai_footprint_score"] for r in results]
    if scores:
        print(f"  Posts analyzed: {len(results)}")
        print(f"  Average AI footprint score: {sum(scores)/len(scores):.1f}")
        print(f"  Highest score (worst): {max(scores)} (post {results[scores.index(max(scores))]['id']})")
        print(f"  Lowest score (best): {min(scores)} (post {results[scores.index(min(scores))]['id']})")
        print(f"  Posts with generic intro: {sum(1 for r in results if r['generic_intro']=='YES')}/{len(results)}")
        print(f"  Posts with generic outro: {sum(1 for r in results if r['generic_outro']=='YES')}/{len(results)}")
    print(f"\n  Top 10 overused phrases:")
    for phrase, count in top_phrases:
        print(f"    '{phrase}': {count} occurrences across {len(global_phrase_posts.get(phrase, set()))} posts")

    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PetHub Online - Phase 10AG Brand Pages + AI Footprint Audit")
    print("=" * 60)

    print("\n=== PART 1: CREATING EDITORIAL BRAND PAGES ===")
    pages = create_draft_pages()

    print("\n=== PART 2: AI FOOTPRINT ANALYSIS ===")
    audit_results = run_ai_footprint_audit()

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
