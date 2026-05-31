#!/usr/bin/env python3
"""
PetHub Citation Readiness Audit
Audits all published posts for citation quality indicators and generates a remediation plan.
"""

import subprocess
import json
import csv
import time
import re
import sys
from html.parser import HTMLParser
from collections import Counter

# WordPress API config
BASE_URL = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUTPUT_CSV = "/var/lib/freelancer/projects/40416335/phase12_data/Citation_Remediation_Plan.csv"

class HTMLTextExtractor(HTMLParser):
    """Extract text and links from HTML content."""
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.links = []
        self.current_tag = None
        self.headings = []
        self.in_heading = False
        self.heading_text = ""
        self.tables = 0
        self.lists = 0
        self.has_schema_markup = False
        self.has_author_box = False
        self.current_classes = []
        self.div_depth = 0
        self.in_faq_schema = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.current_tag = tag
        classes = attrs_dict.get("class", "")
        self.current_classes = classes.lower().split() if classes else []
        item_type = attrs_dict.get("itemtype", "")

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.in_heading = True
            self.heading_text = ""

        if tag == "a":
            href = attrs_dict.get("href", "")
            if href:
                self.links.append(href)

        if tag == "table":
            self.tables += 1

        if tag in ("ul", "ol"):
            self.lists += 1

        # Check for author box patterns
        if any(c in self.current_classes for c in [
            "author-box", "author-bio", "author-info", "post-author",
            "entry-author", "about-author", "author-card", "author-widget",
            "pp-author-boxes", "saboxplugin-wrap", "author-description"
        ]):
            self.has_author_box = True

        # Check for schema markup
        if "faqpage" in item_type.lower():
            self.in_faq_schema = True
            self.has_schema_markup = True

        if "application/ld+json" in classes:
            self.has_schema_markup = True

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self.in_heading:
            self.in_heading = False
            self.headings.append(self.heading_text.strip().lower())

    def handle_data(self, data):
        self.text_parts.append(data)
        if self.in_heading:
            self.heading_text += data

    def get_text(self):
        return " ".join(self.text_parts)

    def get_headings(self):
        return self.headings


def fetch_posts(page, per_page=50):
    """Fetch a page of published posts from WordPress API."""
    url = f"{BASE_URL}/posts?status=publish&per_page={per_page}&page={page}&_fields=id,title,content,link,slug,date"
    result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, url],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"  [ERROR] curl failed for page {page}: {result.stderr}")
        return [], 0

    # Get total pages from headers
    header_result = subprocess.run(
        ["curl", "-s", "--compressed", "-u", AUTH, "-I", url],
        capture_output=True, text=True, timeout=60
    )
    total_pages = 1
    total_posts = 0
    for line in header_result.stdout.split("\n"):
        if line.lower().startswith("x-wp-totalpages:"):
            total_pages = int(line.split(":")[1].strip())
        if line.lower().startswith("x-wp-total:"):
            total_posts = int(line.split(":")[1].strip())

    try:
        data = json.loads(result.stdout)
        if isinstance(data, dict) and "code" in data:
            print(f"  [ERROR] API error on page {page}: {data.get('message', 'Unknown')}")
            return [], 0
        return data, total_pages
    except json.JSONDecodeError as e:
        print(f"  [ERROR] JSON decode failed for page {page}: {e}")
        return [], 0


def count_external_links(links, site_domain="pethubonline.com"):
    """Count external reference links (excluding social media, navigation, etc.)."""
    external = []
    excluded_domains = [
        "facebook.com", "twitter.com", "instagram.com", "pinterest.com",
        "youtube.com", "linkedin.com", "tiktok.com", "x.com",
        "amazon.com", "amzn.to",  # affiliate links
        "wp.me", "wordpress.com", "wordpress.org",
        "gravatar.com", "googleapis.com", "gstatic.com",
        "cloudflare.com", "jsdelivr.net",
        "#",  # anchor links
    ]
    authoritative_domains = [
        "nih.gov", "ncbi.nlm.nih.gov", "pubmed", "gov", "edu",
        "akc.org", "aspca.org", "avma.org", "petmd.com",
        "vcahospitals.com", "merckvetmanual.com", "cornell.edu",
        "who.int", "cdc.gov", "fda.gov", "usda.gov",
        "nature.com", "sciencedirect.com", "springer.com",
        "wiley.com", "journals.", "research.", "study",
        "veterinary", "vet.", "animal",
    ]

    for link in links:
        if not link or link.startswith("#") or link.startswith("mailto:"):
            continue
        link_lower = link.lower()
        if site_domain in link_lower:
            continue
        if any(excl in link_lower for excl in excluded_domains):
            continue
        if link_lower.startswith("http"):
            external.append(link)

    return external


def check_sources_section(headings, text_lower):
    """Check if a Sources/References section exists."""
    source_patterns = [
        "sources", "references", "works cited", "bibliography",
        "source", "reference", "citations", "cited sources",
        "sources & references", "sources and references",
        "resources", "further reading", "related resources",
        "scientific sources", "medical sources", "veterinary sources",
    ]
    for heading in headings:
        for pattern in source_patterns:
            if pattern in heading:
                return True
    # Also check for inline patterns
    if re.search(r'<h[2-4][^>]*>\s*(sources|references|works cited)', text_lower):
        return True
    return False


def check_comparison(headings, text_lower, content_lower):
    """Check if comparison content exists."""
    # Check headings
    comparison_heading_patterns = ["compared", "comparison", "vs", "versus", "difference"]
    for heading in headings:
        for pattern in comparison_heading_patterns:
            if pattern in heading:
                return True
    # Check for comparison tables or structured comparison content
    if "compared:" in text_lower or "comparison table" in text_lower:
        return True
    if re.search(r'<table[^>]*>.*?(vs|compared|versus|difference)', content_lower, re.DOTALL):
        return True
    # Check for vs. in title or content patterns
    if " vs " in text_lower or " vs. " in text_lower:
        return True
    return False


def check_faq(headings, content_lower, text_lower):
    """Check if FAQ section exists and is populated."""
    faq_patterns = [
        "faq", "frequently asked questions", "common questions",
        "questions and answers", "q&a", "q & a",
        "people also ask", "related questions",
    ]
    has_faq_heading = False
    for heading in headings:
        for pattern in faq_patterns:
            if pattern in heading:
                has_faq_heading = True
                break

    # Also check for FAQ schema markup
    has_faq_schema = "faqpage" in content_lower or '"@type":"faqpage"' in content_lower.replace(" ", "")

    # Check for question patterns (strong/bold questions followed by answers)
    question_patterns = re.findall(r'<(strong|b|h[3-4])[^>]*>\s*[^<]*\?\s*</', content_lower)

    return has_faq_heading or has_faq_schema or len(question_patterns) >= 3


def check_key_terms(headings, text_lower):
    """Check if Key Terms/Glossary section exists."""
    terms_patterns = [
        "key terms", "glossary", "terminology", "definitions",
        "key definitions", "important terms", "vocabulary",
        "terms to know", "key concepts",
    ]
    for heading in headings:
        for pattern in terms_patterns:
            if pattern in heading:
                return True
    return False


def check_editorial_disclosure(content_lower, text_lower):
    """Check for editorial disclosure/trust signals."""
    disclosure_patterns = [
        "editorial", "disclosure", "disclaimer",
        "reviewed by", "medically reviewed", "vet reviewed",
        "fact-checked", "fact checked", "veterinarian-reviewed",
        "expert reviewed", "professionally reviewed",
        "affiliate disclosure", "editorial policy",
        "this article was reviewed", "this post was reviewed",
        "written by", "author:", "reviewed:",
        "last updated", "medically accurate",
        "our team", "our editorial",
    ]
    for pattern in disclosure_patterns:
        if pattern in text_lower or pattern in content_lower:
            return True
    return False


def check_author_box(content_lower, parser):
    """Check for author box presence."""
    if parser.has_author_box:
        return True
    author_patterns = [
        "author-box", "author-bio", "author-info", "about-author",
        "post-author-box", "author-card", "saboxplugin",
        "pp-author-boxes", "author-description",
    ]
    for pattern in author_patterns:
        if pattern in content_lower:
            return True
    return False


def check_quick_answer(headings, content_lower, text_lower):
    """Check for Quick Answer block (AI extractability)."""
    quick_answer_patterns = [
        "quick answer", "short answer", "in brief",
        "at a glance", "the short version", "tl;dr",
        "key takeaway", "key takeaways", "bottom line",
        "summary", "overview", "quick summary",
    ]
    for heading in headings:
        for pattern in quick_answer_patterns:
            if pattern in heading:
                return True
    # Check for callout/highlight boxes with quick answers
    if re.search(r'<(div|section|blockquote)[^>]*class="[^"]*(?:callout|highlight|summary|key-point|takeaway)', content_lower):
        return True
    # Check for strong-tagged quick answers near the top
    if re.search(r'<(strong|b)>\s*(quick answer|key takeaway|short answer)', content_lower[:2000]):
        return True
    return False


def count_evidence_claims(text_lower, external_link_count):
    """Estimate evidence depth - factual claims supported by references."""
    # Look for evidence language patterns
    evidence_patterns = [
        r'according to', r'studies? (show|suggest|indicate|found|reveal)',
        r'research (shows?|suggests?|indicates?|found)',
        r'data (shows?|suggests?|indicates?)',
        r'evidence (shows?|suggests?|indicates?)',
        r'experts? (say|recommend|suggest|advise)',
        r'veterinarians? (recommend|suggest|advise|say)',
        r'\d+%', r'\d+ percent',
        r'published in', r'journal of',
        r'clinical (trial|study|research)',
        r'peer-reviewed',
        r'scientifically (proven|supported|backed)',
    ]
    claim_count = 0
    for pattern in evidence_patterns:
        matches = re.findall(pattern, text_lower)
        claim_count += len(matches)

    # Factor in external links as potential reference backing
    claim_count += external_link_count

    return claim_count


def calculate_citation_score(metrics):
    """Calculate overall citation readiness score (0-100)."""
    score = 0

    # Sources/References section (20 points)
    if metrics["has_sources_section"]:
        score += 20

    # External reference links (20 points)
    ref_count = metrics["external_ref_count"]
    if ref_count >= 5:
        score += 20
    elif ref_count >= 3:
        score += 15
    elif ref_count >= 1:
        score += 10
    elif ref_count == 0:
        score += 0

    # Comparison content (10 points)
    if metrics["has_comparison"]:
        score += 10

    # FAQ section (10 points)
    if metrics["has_faq"]:
        score += 10

    # Key Terms/Glossary (5 points)
    if metrics["has_key_terms"]:
        score += 5

    # Evidence depth (15 points)
    evidence = metrics["evidence_depth"]
    if evidence >= 8:
        score += 15
    elif evidence >= 5:
        score += 12
    elif evidence >= 3:
        score += 8
    elif evidence >= 1:
        score += 4

    # Trust signals - editorial disclosure (10 points)
    if metrics["has_editorial_disclosure"]:
        score += 10

    # Author box (5 points)
    if metrics["has_author_box"]:
        score += 5

    # Quick Answer block (5 points)
    if metrics["has_quick_answer"]:
        score += 5

    return min(score, 100)


def identify_issues_and_actions(metrics):
    """Generate issue list and remediation actions."""
    issues = []
    actions = []

    if not metrics["has_sources_section"]:
        issues.append("No Sources/References section")
        actions.append("Add Sources & References section with 3-5 authoritative links")

    if metrics["external_ref_count"] == 0:
        issues.append("Zero external references")
        actions.append("Add 3-5 external reference links to authoritative sources (NIH, AVMA, ASPCA, PetMD, university studies)")
    elif metrics["external_ref_count"] < 3:
        issues.append(f"Only {metrics['external_ref_count']} external reference(s)")
        actions.append(f"Add {3 - metrics['external_ref_count']} more authoritative external references")

    if not metrics["has_comparison"]:
        issues.append("No comparison content")
        actions.append("Add breed/product/method comparison table or 'Compared:' section where applicable")

    if not metrics["has_faq"]:
        issues.append("No FAQ section")
        actions.append("Add FAQ section with 3-5 questions using FAQ schema markup")

    if not metrics["has_key_terms"]:
        issues.append("No Key Terms/Glossary")
        actions.append("Add Key Terms section defining 3-5 topic-specific terms")

    if metrics["evidence_depth"] < 3:
        issues.append(f"Low evidence depth ({metrics['evidence_depth']} claims)")
        actions.append("Add evidence-backed claims with citations (e.g., 'According to [source]...')")

    if not metrics["has_editorial_disclosure"]:
        issues.append("No editorial disclosure")
        actions.append("Add editorial disclosure/vet-reviewed badge or disclaimer")

    if not metrics["has_author_box"]:
        issues.append("No author box")
        actions.append("Enable author box with bio and credentials")

    if not metrics["has_quick_answer"]:
        issues.append("No Quick Answer block")
        actions.append("Add Quick Answer/Key Takeaway callout near top of post for AI extractability")

    return "; ".join(issues) if issues else "None", "; ".join(actions) if actions else "None"


def audit_post(post):
    """Audit a single post for citation quality."""
    post_id = post["id"]
    title = post["title"]["rendered"] if isinstance(post["title"], dict) else post["title"]
    content = post["content"]["rendered"] if isinstance(post["content"], dict) else post["content"]
    content_lower = content.lower()

    # Parse HTML
    parser = HTMLTextExtractor()
    try:
        parser.feed(content)
    except Exception:
        pass

    text = parser.get_text()
    text_lower = text.lower()
    headings = parser.get_headings()
    all_links = parser.links

    # Check each citation quality dimension
    has_sources = check_sources_section(headings, content_lower)
    external_links = count_external_links(all_links)
    external_ref_count = len(external_links)
    has_comparison = check_comparison(headings, text_lower, content_lower)
    has_faq = check_faq(headings, content_lower, text_lower)
    has_key_terms = check_key_terms(headings, text_lower)
    has_editorial = check_editorial_disclosure(content_lower, text_lower)
    has_author = check_author_box(content_lower, parser)
    has_quick_answer = check_quick_answer(headings, content_lower, text_lower)
    evidence = count_evidence_claims(text_lower, external_ref_count)

    metrics = {
        "has_sources_section": has_sources,
        "external_ref_count": external_ref_count,
        "has_comparison": has_comparison,
        "has_faq": has_faq,
        "has_key_terms": has_key_terms,
        "evidence_depth": evidence,
        "has_editorial_disclosure": has_editorial,
        "has_author_box": has_author,
        "has_quick_answer": has_quick_answer,
    }

    citation_score = calculate_citation_score(metrics)
    issues, remediation_actions = identify_issues_and_actions(metrics)

    # Clean title of HTML entities
    title = title.replace("&#8211;", "-").replace("&#8212;", "--")
    title = title.replace("&#8216;", "'").replace("&#8217;", "'")
    title = title.replace("&#8220;", '"').replace("&#8221;", '"')
    title = title.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")

    return {
        "post_id": post_id,
        "title": title,
        "citation_score": citation_score,
        "has_sources_section": has_sources,
        "external_ref_count": external_ref_count,
        "has_comparison": has_comparison,
        "has_faq": has_faq,
        "has_key_terms": has_key_terms,
        "has_editorial_disclosure": has_editorial,
        "has_author_box": has_author,
        "has_quick_answer": has_quick_answer,
        "evidence_depth": evidence,
        "issues": issues,
        "remediation_actions": remediation_actions,
    }


def main():
    print("=" * 70)
    print("PetHub Citation Readiness Audit")
    print("=" * 70)

    # Step 1: Fetch all published posts with pagination
    all_posts = []
    page = 1
    total_pages = 1

    print("\n[1/3] Fetching all published posts...")

    while page <= total_pages:
        print(f"  Fetching page {page}...")
        posts, tp = fetch_posts(page, per_page=50)
        if tp > 0:
            total_pages = tp
        if not posts:
            print(f"  No posts returned on page {page}, stopping.")
            break
        all_posts.extend(posts)
        print(f"  Got {len(posts)} posts (total so far: {len(all_posts)})")
        page += 1
        if page <= total_pages:
            time.sleep(1)  # Rate limiting

    print(f"\n  Total posts fetched: {len(all_posts)}")

    if not all_posts:
        print("[ERROR] No posts fetched. Exiting.")
        sys.exit(1)

    # Step 2: Audit each post
    print("\n[2/3] Auditing each post for citation quality...")
    results = []
    for i, post in enumerate(all_posts):
        title = post["title"]["rendered"] if isinstance(post["title"], dict) else post["title"]
        title_clean = title.replace("&#8211;", "-").replace("&#8217;", "'")
        print(f"  [{i+1}/{len(all_posts)}] Post #{post['id']}: {title_clean[:60]}...")
        result = audit_post(post)
        results.append(result)

    # Step 3: Write CSV
    print(f"\n[3/3] Writing remediation plan to {OUTPUT_CSV}...")
    fieldnames = [
        "post_id", "title", "citation_score", "has_sources_section",
        "external_ref_count", "has_comparison", "has_faq", "has_key_terms",
        "has_editorial_disclosure", "has_author_box", "has_quick_answer",
        "evidence_depth", "issues", "remediation_actions"
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        # Sort by citation score ascending (worst first)
        results.sort(key=lambda x: x["citation_score"])
        for row in results:
            writer.writerow(row)

    print(f"  CSV written: {OUTPUT_CSV}")

    # Summary statistics
    print("\n" + "=" * 70)
    print("CITATION READINESS AUDIT SUMMARY")
    print("=" * 70)

    total = len(results)
    scores = [r["citation_score"] for r in results]
    avg_score = sum(scores) / total if total else 0
    above_90 = sum(1 for s in scores if s >= 90)
    below_90 = sum(1 for s in scores if s < 90)
    below_50 = sum(1 for s in scores if s < 50)

    print(f"\nTotal posts audited:     {total}")
    print(f"Average citation score:  {avg_score:.1f}%")
    print(f"Posts >= 90% (passing):  {above_90} ({above_90/total*100:.1f}%)")
    print(f"Posts < 90% (needs fix): {below_90} ({below_90/total*100:.1f}%)")
    print(f"Posts < 50% (critical):  {below_50} ({below_50/total*100:.1f}%)")
    print(f"Highest score:           {max(scores)}%")
    print(f"Lowest score:            {min(scores)}%")
    print(f"Median score:            {sorted(scores)[total//2]}%")

    # Score distribution
    print("\nScore Distribution:")
    brackets = [(0, 20), (21, 40), (41, 60), (61, 80), (81, 90), (91, 100)]
    for low, high in brackets:
        count = sum(1 for s in scores if low <= s <= high)
        bar = "#" * count
        print(f"  {low:3d}-{high:3d}%: {count:3d} posts  {bar}")

    # Most common issues
    print("\nMost Common Issues:")
    issue_counter = Counter()
    for r in results:
        if r["issues"] != "None":
            for issue in r["issues"].split("; "):
                issue_counter[issue] += 1

    for issue, count in issue_counter.most_common(10):
        pct = count / total * 100
        print(f"  {count:3d} posts ({pct:5.1f}%): {issue}")

    # Dimension-level breakdown
    print("\nDimension Coverage:")
    dimensions = {
        "Sources/References section": sum(1 for r in results if r["has_sources_section"]),
        "3+ external references": sum(1 for r in results if r["external_ref_count"] >= 3),
        "Comparison content": sum(1 for r in results if r["has_comparison"]),
        "FAQ section": sum(1 for r in results if r["has_faq"]),
        "Key Terms/Glossary": sum(1 for r in results if r["has_key_terms"]),
        "Editorial disclosure": sum(1 for r in results if r["has_editorial_disclosure"]),
        "Author box": sum(1 for r in results if r["has_author_box"]),
        "Quick Answer block": sum(1 for r in results if r["has_quick_answer"]),
        "Evidence depth >= 3": sum(1 for r in results if r["evidence_depth"] >= 3),
    }
    for dim, count in dimensions.items():
        pct = count / total * 100
        missing = total - count
        print(f"  {dim:30s}: {count:3d}/{total} ({pct:5.1f}%)  [{missing} missing]")

    # Estimated improvement
    print("\nEstimated Score Improvement if All Issues Fixed:")
    current_avg = avg_score
    target_avg = 100.0  # If every post hit 100
    # More realistic: estimate improvement per dimension
    potential_gains = {
        "Add Sources sections": (total - dimensions["Sources/References section"]) * 20 / total,
        "Add external refs to 3+": (total - dimensions["3+ external references"]) * 15 / total,
        "Add FAQ sections": (total - dimensions["FAQ section"]) * 10 / total,
        "Add comparison content": (total - dimensions["Comparison content"]) * 10 / total,
        "Add Key Terms": (total - dimensions["Key Terms/Glossary"]) * 5 / total,
        "Add editorial disclosure": (total - dimensions["Editorial disclosure"]) * 10 / total,
        "Add author boxes": (total - dimensions["Author box"]) * 5 / total,
        "Add Quick Answer blocks": (total - dimensions["Quick Answer block"]) * 5 / total,
    }
    total_potential = sum(potential_gains.values())
    print(f"  Current average score: {current_avg:.1f}%")
    print(f"  Maximum potential gain: +{total_potential:.1f} points")
    print(f"  Projected average after full remediation: {min(current_avg + total_potential, 100):.1f}%")
    print(f"\n  Gain breakdown:")
    for action, gain in sorted(potential_gains.items(), key=lambda x: -x[1]):
        if gain > 0:
            print(f"    {action:40s}: +{gain:.1f} points avg")

    # Top 10 worst posts
    print("\nTop 10 Posts Needing Most Remediation:")
    for r in results[:10]:
        print(f"  Post #{r['post_id']:5d} | Score: {r['citation_score']:3d}% | {r['title'][:55]}")

    # Top 10 best posts
    print("\nTop 10 Best-Scoring Posts:")
    for r in results[-10:]:
        print(f"  Post #{r['post_id']:5d} | Score: {r['citation_score']:3d}% | {r['title'][:55]}")

    print(f"\nFull remediation plan saved to: {OUTPUT_CSV}")
    print("=" * 70)


if __name__ == "__main__":
    main()
