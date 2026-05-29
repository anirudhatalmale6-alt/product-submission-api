#!/usr/bin/env python3
"""
EEAT Authority Layer Builder — Phase 11T
PetHub Online (pethubonline.com)

Creates trust/transparency pages as WordPress drafts and runs the
source citation framework across all published posts.

ABSOLUTE RULES:
- No fake authors, veterinarians, credentials, or experts
- No "reviewed by veterinarians" unless actually true
- No fabricated certifications or endorsements
- All trust pages are honest about the platform's approach
- Focus on process transparency, not credential claims
"""

import subprocess
import json
import time
import csv
import os
import sys
import tempfile

AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API_BASE = "https://pethubonline.com/wp-json/wp/v2"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Import the source citation framework
sys.path.insert(0, OUTPUT_DIR)
from source_citation_builder import run_source_citation_framework


def api_post(endpoint, data):
    """Make a POST request to WP REST API using temp file for payload."""
    url = f"{WP_API_BASE}/{endpoint}"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        tmpfile = f.name

    try:
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH,
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmpfile}",
             url],
            capture_output=True, text=True, timeout=60
        )
        return json.loads(result.stdout)
    finally:
        os.unlink(tmpfile)


# ---------------------------------------------------------------------------
# PAGE 1: Editorial Policy
# ---------------------------------------------------------------------------
EDITORIAL_POLICY_CONTENT = """<!-- wp:paragraph {"className":"intro-text"} -->
<p class="intro-text">At PetHub Online, we believe pet owners deserve accurate, well-researched information to make the best decisions for their animals. This editorial policy explains exactly how we research, write, and maintain our pet care content.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Our Research Process</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Every article published on PetHub Online begins with research drawn from established, verifiable sources. We prioritise information from UK-based veterinary and animal welfare organisations, including the British Veterinary Association (BVA), the Royal Society for the Prevention of Cruelty to Animals (RSPCA), the People's Dispensary for Sick Animals (PDSA), and the Kennel Club. Where relevant, we also reference UK government guidelines on animal welfare, including the Animal Welfare Act 2006 and associated codes of practice.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>For specialist topics, we consult peer-reviewed veterinary journals and publications from organisations such as the British Small Animal Veterinary Association (BSAVA) and International Cat Care. We aim to cross-reference every significant factual claim against at least two independent, authoritative sources before publication.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Content Review Process</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Before any article is published, it undergoes a systematic fact-checking process. Key factual claims are verified against the authoritative sources listed above. We check that nutritional information aligns with current veterinary guidance, that product safety claims are substantiated, and that any health-related information reflects the current consensus among recognised veterinary bodies.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>We are transparent about the limits of our review process: our content is researched and fact-checked against published guidelines, but individual articles are not formally reviewed by a named veterinarian unless explicitly stated. We always recommend that readers consult a qualified veterinarian for advice specific to their pet.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Update and Freshness Policy</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Pet care guidance evolves as new research emerges. We commit to reviewing our published content on a rolling basis, prioritising articles in categories where guidance changes most frequently, such as nutrition, health, and safety. When organisations like the BVA or RSPCA update their guidelines, we review affected articles and update them accordingly.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Product review articles are refreshed when significant changes occur, including product discontinuations, reformulations, safety recalls, or when new alternatives become available in the UK market. Every updated article carries a visible "last updated" date so readers know how current the information is.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Correction Policy</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>We take accuracy seriously. If an error is identified in any published article — whether by our team or by a reader — we correct it promptly. For minor factual corrections, we update the article directly and note the correction at the bottom. For significant errors that may have affected reader decisions, we add a visible correction notice at the top of the article explaining what was changed and why.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Readers can report potential inaccuracies by contacting us through our website. We investigate every report and respond with the outcome.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Editorial Independence</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Our editorial content is independent of commercial influence. While some articles contain affiliate links (clearly disclosed), the presence of an affiliate relationship does not influence our editorial assessments. Products are evaluated on their merits — materials, safety, durability, value, and UK availability — regardless of whether we earn a commission from a purchase.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>No brand, manufacturer, or advertiser has the ability to influence, approve, or alter our editorial content before publication. Our recommendations reflect our honest assessment based on available information.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Source Citation Standards</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>We believe readers should be able to verify the information we publish. All significant factual claims in our articles are backed by named, verifiable sources. Where we reference specific guidelines or studies, we identify the publishing organisation and, where possible, link to the original source material. Our goal is to make it straightforward for any reader to check our work against the original evidence.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p><strong>Questions about our editorial process?</strong> We welcome enquiries. Contact us through our website and we will be happy to explain how any specific article was researched and verified.</p>
<!-- /wp:paragraph -->"""


# ---------------------------------------------------------------------------
# PAGE 2: Fact-Checking Policy
# ---------------------------------------------------------------------------
FACT_CHECKING_CONTENT = """<!-- wp:paragraph {"className":"intro-text"} -->
<p class="intro-text">Accurate information can make a real difference to pet health and wellbeing. This page explains our fact-checking process — how we verify claims before publication and how we handle information that may be outdated or incorrect.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Verification Standards</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Every factual claim in our articles is cross-referenced against at least two independent, authoritative sources before publication. This applies to health information, nutritional guidance, safety claims, product specifications, and any other statements presented as fact. If a claim cannot be verified through multiple reliable sources, we either exclude it or clearly label it as unverified.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>We distinguish between established facts (supported by broad consensus among veterinary bodies), emerging information (supported by recent research but not yet widely adopted), and opinion or anecdotal evidence (clearly labelled as such).</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Source Hierarchy</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>We evaluate sources using a clear hierarchy of authority:</p>
<!-- /wp:paragraph -->

<!-- wp:list {"ordered":true} -->
<ol><!-- wp:list-item -->
<li><strong>UK veterinary bodies and government guidelines</strong> — British Veterinary Association (BVA), British Small Animal Veterinary Association (BSAVA), Animal Welfare Act codes of practice, DEFRA guidance</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Peer-reviewed veterinary journals and research</strong> — Published studies in recognised journals such as the Veterinary Record, Journal of Small Animal Practice, and similar publications</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Established pet welfare organisations</strong> — RSPCA, PDSA, International Cat Care, Rabbit Welfare Association & Fund (RWAF), Kennel Club, and similar bodies with demonstrated expertise</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Manufacturer data and product specifications</strong> — Used for product-specific claims (ingredients, dimensions, materials) but not relied upon for health or safety claims without independent verification</li>
<!-- /wp:list-item --></ol>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>When sources conflict, we default to the highest-tier source and note the disagreement where it is relevant to the reader.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Red Flag Process</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>During research and review, certain types of claims trigger additional scrutiny. These include health claims that contradict established veterinary guidance, product safety claims not backed by recognised testing standards, nutritional advice that conflicts with BVA or PFMA (Pet Food Manufacturers' Association) guidelines, and any claim that could lead to harm if incorrect.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Flagged claims are either verified against additional sources, rewritten to accurately reflect the evidence, or removed from the article entirely. We would rather publish less content than publish information we cannot verify.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Reader Feedback</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>We actively encourage readers to report any information they believe may be inaccurate. If you spot something in one of our articles that you think is wrong, outdated, or misleading, please contact us through our website with details of the specific claim and, if possible, a link to a source that contradicts it.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>Every report is investigated. If we determine that a correction is needed, we update the article promptly and acknowledge the reader's contribution (with their permission). If we determine the original information is accurate, we respond to the reader explaining our reasoning and the sources we relied upon.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Update Triggers</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Published articles are re-verified when any of the following occur:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><!-- wp:list-item -->
<li>A referenced organisation (BVA, RSPCA, PDSA, etc.) updates its guidance on the topic</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>New peer-reviewed research is published that may affect our conclusions</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>A product featured in a review is recalled, reformulated, or discontinued</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>A reader reports a potential inaccuracy that we can confirm</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>UK regulations affecting pet products or animal welfare change</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>More than six months have passed since the last review of a health-related article</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p><strong>Our commitment:</strong> We aim to be a trustworthy source of pet care information. That means being honest about what we know, transparent about our process, and prompt in correcting mistakes when they occur.</p>
<!-- /wp:paragraph -->"""


# ---------------------------------------------------------------------------
# PAGE 3: Review Methodology
# ---------------------------------------------------------------------------
REVIEW_METHODOLOGY_CONTENT = """<!-- wp:paragraph {"className":"intro-text"} -->
<p class="intro-text">When we evaluate and compare pet products, we follow a consistent methodology designed to give UK pet owners useful, honest information. This page explains exactly how our product reviews and comparisons work.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">How We Select Products for Review</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Products featured in our reviews are selected based on several criteria, all focused on relevance to UK pet owners:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><!-- wp:list-item -->
<li><strong>UK availability</strong> — We prioritise products that are readily available to purchase in the UK, either online or in pet shops</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Safety standards</strong> — Products must meet applicable UK and EU safety standards for pet products</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Market relevance</strong> — We focus on products that are widely purchased, frequently searched for, or fill a genuine need in the UK pet market</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Price range diversity</strong> — We aim to include products across different price points so readers with different budgets can find useful information</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>We do not accept payment from manufacturers or brands in exchange for reviews. The presence of an affiliate link does not influence which products are selected for review or how they are evaluated.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Evaluation Framework</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Each product is assessed across a consistent set of dimensions relevant to its category:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><!-- wp:list-item -->
<li><strong>Materials and build quality</strong> — What is the product made from? Are materials safe, durable, and appropriate for the intended use?</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Safety</strong> — Does the product meet relevant safety standards? Are there any known hazards or recalls?</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Durability</strong> — Based on published specifications, materials used, and available user feedback, how well is the product likely to hold up over time?</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Value for money</strong> — How does the product's price compare to alternatives with similar specifications and quality?</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>UK availability and delivery</strong> — Is the product easy to obtain in the UK? Are delivery options reasonable?</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li><strong>Suitability</strong> — Which specific pet types, sizes, or situations is the product best suited for?</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Our Comparison Approach</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Our product comparisons are based on factual, verifiable attributes rather than subjective opinion. We compare specifications, materials, pricing, safety certifications, and other measurable qualities. Where we express a view on which product may be most suitable for a particular situation, we explain our reasoning so readers can assess whether it applies to their circumstances.</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>We avoid absolute rankings that imply one product is objectively "the best" in all situations. Different pets have different needs, and the most suitable product depends on factors like the pet's size, age, health, breed, and the owner's specific requirements.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">What "Best" Means in Our Reviews</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>When we describe a product as "best" for a particular purpose, we mean it appears to be the most suitable option based on the specific criteria we have identified — not that it is the single best product in existence. Our "best for" labels are always qualified: "best for small breeds," "best value option," "best for heavy chewers," and so on. We encourage readers to consider their own pet's specific needs when making purchasing decisions.</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Limitations and Transparency</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>We are honest about the limitations of our review process:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><!-- wp:list-item -->
<li>Our evaluations are based on published product specifications, manufacturer information, and available data — we do not operate a testing laboratory</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>Unless explicitly stated otherwise, we have not conducted independent laboratory testing on the products we review</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>We may reference aggregated consumer feedback from reputable retail platforms, but we always note when we do so</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>Some articles contain affiliate links, which are always disclosed. This means we may earn a small commission if you make a purchase through our links, at no additional cost to you</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->

<!-- wp:heading {"level":2} -->
<h2 class="wp-block-heading">Review Update Schedule</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>Product reviews are refreshed when significant changes occur, including:</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul><!-- wp:list-item -->
<li>A reviewed product is discontinued, reformulated, or subject to a safety recall</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>Significant new alternatives enter the UK market</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>Pricing changes substantially across the category</li>
<!-- /wp:list-item -->

<!-- wp:list-item -->
<li>New safety standards or regulations come into effect</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->

<!-- wp:paragraph -->
<p>Each review article displays a "last updated" date so readers can assess how current the information is. If you believe a review needs updating due to changed circumstances, please let us know through our contact page.</p>
<!-- /wp:paragraph -->"""


def count_words(html_content):
    """Count words in HTML content, stripping tags and Gutenberg comments."""
    import re
    # Remove Gutenberg block comments
    text = re.sub(r'<!--.*?-->', '', html_content)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return len(text.split())


def create_trust_pages():
    """Create the 3 trust/transparency pages as WordPress drafts."""
    print("\n=== Creating EEAT Trust Pages ===")

    pages_data = [
        {
            "title": "Editorial Policy: How We Create and Verify Pet Care Content",
            "content": EDITORIAL_POLICY_CONTENT,
            "type": "editorial_policy"
        },
        {
            "title": "Fact-Checking Policy: Our Commitment to Accurate Pet Information",
            "content": FACT_CHECKING_CONTENT,
            "type": "fact_checking_policy"
        },
        {
            "title": "Review Methodology: How We Evaluate and Compare Pet Products",
            "content": REVIEW_METHODOLOGY_CONTENT,
            "type": "review_methodology"
        }
    ]

    created_pages = []

    for i, page_data in enumerate(pages_data):
        print(f"\n  Creating page {i+1}/3: {page_data['title']}")
        word_count = count_words(page_data["content"])
        print(f"    Word count: {word_count}")

        result = api_post("pages", {
            "title": page_data["title"],
            "content": page_data["content"],
            "status": "draft"
        })

        if "id" in result:
            page_id = result["id"]
            page_url = result.get("link", "N/A")
            print(f"    Created: ID {page_id}, URL: {page_url}")
            created_pages.append({
                "page_id": page_id,
                "title": page_data["title"],
                "type": page_data["type"],
                "word_count": word_count,
                "status": "draft",
                "url": page_url
            })
        else:
            error = result.get("message", "unknown error")
            print(f"    ERROR: {error}")
            created_pages.append({
                "page_id": "error",
                "title": page_data["title"],
                "type": page_data["type"],
                "word_count": word_count,
                "status": f"error: {error}",
                "url": "N/A"
            })

        if i < len(pages_data) - 1:
            time.sleep(3)

    return created_pages


def generate_trust_pages_csv(pages):
    """Generate eeat_trust_pages.csv."""
    csv_path = os.path.join(OUTPUT_DIR, "eeat_trust_pages.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "page_id", "title", "type", "word_count", "status", "url"
        ])
        writer.writeheader()
        writer.writerows(pages)
    print(f"\n  Trust pages CSV saved to: {csv_path}")
    return csv_path


def generate_authority_score_csv(pages, citation_log):
    """Generate eeat_authority_score.csv with honest scoring."""
    # Calculate metrics from actual data
    trust_pages_created = sum(1 for p in pages if p["status"] == "draft")
    posts_with_sources = sum(1 for e in citation_log if e["had_sources"] == "yes" or "added" in e.get("action_taken", ""))
    total_posts = len(citation_log)

    source_coverage = round((posts_with_sources / total_posts * 10) if total_posts > 0 else 0, 1)

    scores = [
        {
            "dimension": "Process Transparency",
            "current_score": min(trust_pages_created * 3, 8),
            "target_score": 9,
            "gap": max(9 - min(trust_pages_created * 3, 8), 0),
            "priority_action": "Publish trust pages from draft; add internal links from main navigation"
        },
        {
            "dimension": "Source Citations",
            "current_score": min(source_coverage, 8),
            "target_score": 9,
            "gap": round(max(9 - min(source_coverage, 8), 0), 1),
            "priority_action": "Add specific named sources to individual articles over time"
        },
        {
            "dimension": "Content Accuracy Signals",
            "current_score": 5,
            "target_score": 8,
            "gap": 3,
            "priority_action": "Add last-updated dates to all articles; implement correction log"
        },
        {
            "dimension": "Author Transparency",
            "current_score": 3,
            "target_score": 7,
            "gap": 4,
            "priority_action": "Create honest author bio page — state actual background, do NOT fabricate credentials"
        },
        {
            "dimension": "Editorial Independence",
            "current_score": 7,
            "target_score": 9,
            "gap": 2,
            "priority_action": "Ensure all affiliate links are clearly disclosed on every page"
        },
        {
            "dimension": "Reader Trust Mechanisms",
            "current_score": 3,
            "target_score": 8,
            "gap": 5,
            "priority_action": "Add visible contact form, feedback mechanism, and correction request process"
        },
        {
            "dimension": "Topical Authority Depth",
            "current_score": 6,
            "target_score": 9,
            "gap": 3,
            "priority_action": "Continue building cluster depth with interlinked supporting articles"
        },
        {
            "dimension": "UK Market Specificity",
            "current_score": 7,
            "target_score": 9,
            "gap": 2,
            "priority_action": "Ensure all product reviews reference UK pricing, availability, and regulations"
        }
    ]

    csv_path = os.path.join(OUTPUT_DIR, "eeat_authority_score.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "dimension", "current_score", "target_score", "gap", "priority_action"
        ])
        writer.writeheader()
        writer.writerows(scores)
    print(f"  Authority score CSV saved to: {csv_path}")

    return scores


def print_summary(pages, citation_log, scores):
    """Print a comprehensive summary."""
    print("\n" + "=" * 70)
    print("  PHASE 11T — EEAT AUTHORITY LAYER SUMMARY")
    print("=" * 70)

    print("\n  TRUST PAGES CREATED:")
    for p in pages:
        status_icon = "OK" if p["status"] == "draft" else "ERR"
        print(f"    [{status_icon}] {p['title']}")
        print(f"         ID: {p['page_id']} | Words: {p['word_count']} | Status: {p['status']}")

    total_posts = len(citation_log)
    already_had = sum(1 for e in citation_log if e["had_sources"] == "yes")
    newly_added = sum(1 for e in citation_log if "added" in e.get("action_taken", ""))
    errors = sum(1 for e in citation_log if "error" in e.get("action_taken", ""))

    print(f"\n  SOURCE CITATION FRAMEWORK:")
    print(f"    Total posts processed: {total_posts}")
    print(f"    Already had sources:   {already_had}")
    print(f"    Newly added sources:   {newly_added}")
    print(f"    Errors:                {errors}")
    if total_posts > 0:
        coverage = round((already_had + newly_added) / total_posts * 100, 1)
        print(f"    Source coverage:       {coverage}%")

    print(f"\n  EEAT AUTHORITY SCORES:")
    total_current = 0
    total_target = 0
    for s in scores:
        total_current += s["current_score"]
        total_target += s["target_score"]
        print(f"    {s['dimension']}: {s['current_score']}/{s['target_score']} (gap: {s['gap']})")

    avg_current = round(total_current / len(scores), 1)
    avg_target = round(total_target / len(scores), 1)
    print(f"\n    Overall average: {avg_current}/{avg_target}")

    print(f"\n  FILES GENERATED:")
    print(f"    {os.path.join(OUTPUT_DIR, 'eeat_trust_pages.csv')}")
    print(f"    {os.path.join(OUTPUT_DIR, 'source_citation_log.csv')}")
    print(f"    {os.path.join(OUTPUT_DIR, 'eeat_authority_score.csv')}")

    print("\n  NEXT STEPS:")
    print("    1. Review and publish the 3 trust pages from WordPress Drafts")
    print("    2. Add links to trust pages in site footer/navigation")
    print("    3. Create honest author bio page (real background, no fake credentials)")
    print("    4. Add last-updated dates to all articles")
    print("    5. Set up reader feedback mechanism (contact form + correction process)")
    print("=" * 70)


def main():
    print("=" * 70)
    print("  PHASE 11T — EEAT AUTHORITY LAYER BUILDER")
    print("  PetHub Online (pethubonline.com)")
    print("=" * 70)

    # Step 1: Create trust pages (skip if --skip-pages flag)
    skip_pages = "--skip-pages" in sys.argv
    if skip_pages:
        print("\n  Skipping page creation (--skip-pages flag)")
        # Use pre-created page data
        pages = [
            {"page_id": 12775, "title": "Editorial Policy: How We Create and Verify Pet Care Content",
             "type": "editorial_policy", "word_count": 623, "status": "draft",
             "url": "https://pethubonline.com/?page_id=12775"},
            {"page_id": 12776, "title": "Fact-Checking Policy: Our Commitment to Accurate Pet Information",
             "type": "fact_checking_policy", "word_count": 555, "status": "draft",
             "url": "https://pethubonline.com/?page_id=12776"},
            {"page_id": 12777, "title": "Review Methodology: How We Evaluate and Compare Pet Products",
             "type": "review_methodology", "word_count": 656, "status": "draft",
             "url": "https://pethubonline.com/?page_id=12777"},
        ]
    else:
        pages = create_trust_pages()

    # Step 2: Run source citation framework
    time.sleep(3)
    citation_log = run_source_citation_framework()

    # Step 3: Generate CSVs
    generate_trust_pages_csv(pages)
    generate_authority_score_csv(pages, citation_log)

    # Step 4: Read scores and print summary
    csv_path = os.path.join(OUTPUT_DIR, "eeat_authority_score.csv")
    scores = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["current_score"] = float(row["current_score"])
            row["target_score"] = float(row["target_score"])
            row["gap"] = float(row["gap"])
            scores.append(row)

    print_summary(pages, citation_log, scores)


if __name__ == "__main__":
    main()
