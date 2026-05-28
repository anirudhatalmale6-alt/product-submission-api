#!/usr/bin/env python3
"""
10AE-I: Live Authority Telemetry - pethubonline.com
Master telemetry system: 15 authority dimensions, unified scoring, cluster dashboards.
"""

import subprocess, json, csv, re, os, sys, math
from collections import defaultdict, Counter
from html import unescape

# ── Config ──────────────────────────────────────────────────────────────────
WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
AUTH = "jasonsarah2026:yUmn Rngy EFE1 r7jr kjtm jmqx"
OUT_DIR = "/var/lib/freelancer/projects/40416335/phase10ae_data"

# Dimension weights (must sum to 1.0)
WEIGHTS = {
    "trust_intensity": 0.15,
    "glossary_density": 0.07,
    "faq_coverage": 0.07,
    "comparison_density": 0.10,
    "practical_usefulness": 0.10,
    "educational_depth": 0.08,
    "external_references": 0.12,
    "internal_link_density": 0.05,
    "answer_readiness": 0.08,
    "citation_confidence": 0.08,
    "semantic_depth": 0.03,
    "beginner_accessibility": 0.02,
    "safety_coverage": 0.02,
    "decision_support": 0.02,
    "authority_balance": 0.01,
}

DIMENSION_NAMES = list(WEIGHTS.keys())

# Authoritative reference domains
AUTHORITY_DOMAINS = [
    "rspca", "bva.co.uk", "pdsa.org", "gov.uk", "battersea.org",
    "bluecross.org", "fediaf", "defra", "avma.org", "aspca.org",
    "akc.org", "vet.cornell", "merckvetmanual", "petmd.com",
    "ncbi.nlm.nih.gov", "pubmed", "sciencedirect", "springer.com",
    "wiley.com", "nature.com",
]

# Cluster keywords mapping
CLUSTER_KEYWORDS = {
    "Dog Toys": ["dog toy", "chew toy", "tug toy", "fetch toy", "puzzle toy", "interactive toy",
                 "indestructible toy", "squeaky toy", "dog ball", "rope toy"],
    "Dog Food": ["dog food", "puppy food", "dry dog food", "wet dog food", "raw dog food",
                 "grain-free dog food", "kibble", "dog diet", "dog nutrition", "best food for dog"],
    "Dog Beds": ["dog bed", "orthopedic dog bed", "dog crate bed", "dog mattress", "calming dog bed",
                 "elevated dog bed", "waterproof dog bed", "dog sleeping"],
    "Dog Health": ["dog health", "vet", "veterinar", "dog disease", "dog illness", "dog symptoms",
                   "dog medication", "dog supplement", "dog vitamin", "dog allergy", "dog skin",
                   "flea", "tick", "worm", "parasite", "vaccination", "neuter", "spay"],
    "Dog Training": ["dog training", "puppy training", "obedience", "dog behavior", "crate training",
                     "house training", "leash training", "clicker", "positive reinforcement",
                     "dog command", "recall training"],
    "Dog Grooming": ["dog grooming", "dog shampoo", "dog brush", "nail trim", "dog bath",
                     "deshedding", "grooming tool", "dog coat care", "dog hair"],
    "Cat Food": ["cat food", "kitten food", "wet cat food", "dry cat food", "cat diet",
                 "cat nutrition", "best food for cat", "grain-free cat"],
    "Cat Health": ["cat health", "cat vet", "cat disease", "cat illness", "cat symptom",
                   "cat medication", "cat supplement", "cat allergy", "cat flea"],
    "Cat Toys": ["cat toy", "interactive cat", "cat puzzle", "catnip", "laser toy cat",
                 "feather toy", "cat scratching", "scratch post"],
    "Dog Accessories": ["dog collar", "dog harness", "dog leash", "dog lead", "dog tag",
                        "dog bowl", "dog feeder", "dog water", "dog carrier", "dog crate",
                        "dog kennel", "dog gate", "dog ramp", "dog stroller"],
    "Cat Accessories": ["cat collar", "cat harness", "cat carrier", "cat litter", "litter box",
                        "cat tree", "cat tower", "cat bed", "cat fountain", "cat bowl"],
    "Dog Breeds": ["breed", "labrador", "golden retriever", "german shepherd", "bulldog",
                   "poodle", "beagle", "rottweiler", "husky", "dachshund", "chihuahua",
                   "spaniel", "terrier", "corgi", "dalmatian"],
    "Pet Insurance": ["pet insurance", "dog insurance", "cat insurance", "vet bill",
                      "pet cover", "insurance policy pet", "claim pet"],
    "Aquarium & Fish": ["fish", "aquarium", "fish tank", "goldfish", "betta", "tropical fish",
                        "fish food", "filter aquarium"],
    "Small Pets": ["rabbit", "hamster", "guinea pig", "gerbil", "ferret", "chinchilla",
                   "small pet", "rodent pet", "cage pet"],
    "Birds": ["bird", "parrot", "budgie", "cockatiel", "bird cage", "bird food", "bird seed",
              "avian"],
    "Reptiles": ["reptile", "snake", "lizard", "gecko", "turtle", "tortoise", "terrarium",
                 "vivarium", "bearded dragon"],
    "Pet Travel": ["pet travel", "dog travel", "cat travel", "pet friendly hotel",
                   "traveling with pet", "pet passport", "pet airline"],
    "Pet Adoption": ["adopt", "rescue dog", "rescue cat", "shelter pet", "rehome",
                     "foster pet", "adoption process"],
}


# ── Helper functions ────────────────────────────────────────────────────────

def strip_html(html_str):
    """Remove HTML tags and decode entities."""
    if not html_str:
        return ""
    text = re.sub(r'<[^>]+>', ' ', html_str)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_all_posts():
    """Fetch all published posts via WP REST API using curl."""
    all_posts = []
    page = 1
    while True:
        url = f"{WP_BASE}/posts?status=publish&per_page=100&page={page}&context=edit"
        print(f"  Fetching page {page}...", end=" ", flush=True)
        result = subprocess.run(
            ["curl", "-s", "--compressed", "-u", AUTH, url],
            capture_output=True, text=True, timeout=60
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"JSON decode error on page {page}, stopping.")
            break
        if isinstance(data, dict) and "code" in data:
            print(f"API error: {data.get('message', 'unknown')}")
            break
        if not data or not isinstance(data, list) or len(data) == 0:
            print("empty, done.")
            break
        all_posts.extend(data)
        print(f"got {len(data)} posts (total: {len(all_posts)})")
        if len(data) < 100:
            break
        page += 1
    return all_posts


def classify_cluster(title, slug, content_text):
    """Classify a post into a cluster based on keyword matching."""
    combined = f"{title} {slug} {content_text[:2000]}".lower()
    scores = {}
    for cluster, keywords in CLUSTER_KEYWORDS.items():
        score = 0
        for kw in keywords:
            occurrences = combined.count(kw.lower())
            if occurrences > 0:
                # Title/slug matches weighted more
                title_slug = f"{title} {slug}".lower()
                if kw.lower() in title_slug:
                    score += occurrences + 5
                else:
                    score += occurrences
        scores[cluster] = score
    if not scores or max(scores.values()) == 0:
        return "General Pet Care"
    return max(scores, key=scores.get)


def count_pattern(text, patterns, case_insensitive=True):
    """Count total occurrences of multiple regex patterns."""
    total = 0
    flags = re.IGNORECASE if case_insensitive else 0
    for pat in patterns:
        total += len(re.findall(pat, text, flags))
    return total


def clamp(val, lo=0, hi=100):
    return max(lo, min(hi, val))


# ── Dimension scorers ───────────────────────────────────────────────────────
# Each returns a score 0-100

def score_trust_intensity(html, text, wc):
    """Editorial quality, methodology, corrections, AI transparency, disclosure."""
    s = 0
    # Editorial markers
    editorial_patterns = [
        r'editor[\'’]?s?\s+note', r'reviewed\s+by', r'fact[\s-]?check',
        r'medically\s+reviewed', r'written\s+by', r'updated\s+on',
        r'last\s+updated', r'author\s*:', r'expert\s+reviewed',
    ]
    s += min(25, count_pattern(text, editorial_patterns) * 8)

    # Methodology markers
    method_patterns = [
        r'methodology', r'how\s+we\s+(test|review|rank|evaluate|choose|select)',
        r'our\s+(testing|review|evaluation)\s+process',
        r'selection\s+criteria', r'scoring\s+(system|criteria|method)',
    ]
    s += min(20, count_pattern(text, method_patterns) * 10)

    # Corrections / transparency
    correction_patterns = [
        r'correction\s*:', r'update\s*:', r'editor[\'’]?s?\s+update',
        r'we\s+(previously|originally|incorrectly)',
        r'this\s+article\s+(has\s+been|was)\s+updated',
    ]
    s += min(15, count_pattern(text, correction_patterns) * 8)

    # AI transparency / disclosure
    ai_patterns = [
        r'ai[\s-]?(generated|assisted|written)', r'artificial\s+intelligence',
        r'disclosure\s*:', r'affiliate\s+disclosure', r'sponsored',
        r'disclaimer\s*:', r'transparency',
    ]
    s += min(20, count_pattern(text, ai_patterns) * 7)

    # Trust signals in structure
    trust_struct = [
        r'<blockquote', r'class=["\'][^"\']*quote', r'class=["\'][^"\']*testimonial',
        r'class=["\'][^"\']*callout', r'class=["\'][^"\']*notice',
    ]
    s += min(20, count_pattern(html, trust_struct) * 5)

    return clamp(s)


def score_glossary_density(html, text, wc):
    """Key Terms blocks, bold-dash definitions, inline terminology."""
    s = 0
    # Key Terms / Glossary blocks
    glossary_patterns_html = [
        r'key\s+terms?\s*:', r'glossary\s*:', r'terminology\s*:',
        r'definitions?\s*:', r'what\s+(?:does|do|is)\s+\w+\s+mean',
    ]
    s += min(25, count_pattern(text, glossary_patterns_html) * 10)

    # Bold-dash definitions: **Term** - definition OR **Term:** definition
    bold_dash = re.findall(r'<strong>[^<]{2,50}</strong>\s*[–—\-:]\s*\w', html, re.IGNORECASE)
    s += min(30, len(bold_dash) * 3)

    # Inline terminology (domain-specific pet terms)
    pet_terms = [
        r'kibble', r'palatab', r'glucosamine', r'chondroitin', r'probiotic',
        r'omega[\s-]?[36]', r'antioxidant', r'hydrolyz', r'dehydrat',
        r'by[\s-]?product', r'holistic', r'grain[\s-]?free', r'hypoallergenic',
        r'digestib', r'bioavailab', r'microbiome', r'taurine', r'l[\s-]?carnitine',
        r'enrichment', r'desensiti[sz]', r'socializ', r'reinforcement',
        r'brachycephalic', r'dermatitis', r'atop', r'zoonotic',
    ]
    term_count = count_pattern(text, pet_terms)
    s += min(30, term_count * 2)

    # Definition list structures
    dl_count = len(re.findall(r'<dl|<dt|<dd', html, re.IGNORECASE))
    s += min(15, dl_count * 5)

    return clamp(s)


def score_faq_coverage(html, text, wc):
    """FAQ blocks, question headings, Q&A structures."""
    s = 0
    # FAQ schema / blocks
    faq_blocks = [
        r'class=["\'][^"\']*faq', r'id=["\'][^"\']*faq',
        r'<h[2-4][^>]*>\s*(?:FAQ|Frequently\s+Asked\s+Questions)',
        r'wp:yoast/faq-block', r'schema.*FAQPage',
    ]
    s += min(25, count_pattern(html, faq_blocks) * 12)

    # Question headings (h2/h3/h4 containing ?)
    q_headings = re.findall(r'<h[2-4][^>]*>[^<]*\?[^<]*</h[2-4]>', html, re.IGNORECASE)
    s += min(35, len(q_headings) * 5)

    # General question patterns in text
    q_patterns = [
        r'(?:^|\.\s+)(?:Can|Should|Is|Are|Do|Does|What|When|Where|Why|How|Which)\s+\w+.*\?',
    ]
    q_count = count_pattern(text, q_patterns)
    s += min(25, q_count * 2)

    # Q&A structured pairs
    qa_pairs = re.findall(r'<strong>[^<]*\?</strong>', html, re.IGNORECASE)
    s += min(15, len(qa_pairs) * 5)

    return clamp(s)


def score_comparison_density(html, text, wc):
    """Tables, vs-sections, pro/con lists."""
    s = 0
    # HTML tables
    tables = len(re.findall(r'<table', html, re.IGNORECASE))
    s += min(25, tables * 10)

    # Table rows (depth indicator)
    rows = len(re.findall(r'<tr', html, re.IGNORECASE))
    s += min(15, rows * 1)

    # Vs / comparison patterns
    vs_patterns = [
        r'\bvs\.?\b', r'\bversus\b', r'compared?\s+to', r'comparison',
        r'difference\s+between', r'better\s+than', r'alternative\s+to',
        r'head[\s-]?to[\s-]?head',
    ]
    s += min(25, count_pattern(text, vs_patterns) * 4)

    # Pro/con patterns
    procon = [
        r'pros?\s*(and|&|/)\s*cons?', r'\bpros\s*:', r'\bcons\s*:',
        r'advantages?\s*(and|&)\s*disadvantages?', r'benefits?\s*(and|&)\s*drawbacks?',
        r'(?:what\s+we\s+)?like[d]?\s*:', r'(?:what\s+we\s+)?didn[\'’]?t\s+like\s*:',
    ]
    s += min(20, count_pattern(text, procon) * 8)

    # Rating/score patterns
    rating = [r'\d+(\.\d+)?\s*/\s*(?:5|10)\b', r'rating\s*:', r'score\s*:', r'stars?\s*:']
    s += min(15, count_pattern(text, rating) * 5)

    return clamp(s)


def score_practical_usefulness(html, text, wc):
    """Checklists, step-by-step, tips, troubleshooting."""
    s = 0
    # Checklists
    checklist = [
        r'checklist', r'☑', r'☐', r'☒',  # checkbox chars
        r'class=["\'][^"\']*checklist', r'\[\s*[xX\s]\s*\]',
    ]
    s += min(15, count_pattern(html, checklist) * 6)

    # Step-by-step
    steps = [
        r'step\s+\d', r'step[\s-]?by[\s-]?step', r'how\s+to\b',
        r'(?:first|second|third|next|then|finally)\s*,?\s+\w',
    ]
    s += min(20, count_pattern(text, steps) * 4)

    # Tips / advice
    tips = [
        r'\btips?\b', r'\btrick', r'\bhack', r'pro[\s-]?tip',
        r'top\s+\d+\s+(?:tip|way|method|trick)',
        r'quick\s+tip', r'expert\s+tip', r'our\s+tip',
    ]
    s += min(20, count_pattern(text, tips) * 3)

    # Troubleshooting
    trouble = [
        r'troubleshoot', r'common\s+(?:problem|issue|mistake)',
        r'what\s+(?:to\s+do\s+)?if', r'(?:fix|solve|resolv)\w*\s+(?:the|this|a|common)',
        r'doesn[\'’]?t\s+work', r'not\s+working',
    ]
    s += min(20, count_pattern(text, trouble) * 5)

    # Ordered lists (practical instructions)
    ol_items = len(re.findall(r'<ol|<li', html, re.IGNORECASE))
    s += min(15, ol_items * 1)

    # Actionable language
    action = [
        r'\b(?:make\s+sure|ensure|always|never|avoid|try|consider|remember|keep\s+in\s+mind)\b',
    ]
    s += min(10, count_pattern(text, action) * 1)

    return clamp(s)


def score_educational_depth(html, text, wc):
    """Word count, headings, lists, topic breadth."""
    s = 0
    # Word count scoring
    if wc >= 3000:
        s += 30
    elif wc >= 2000:
        s += 25
    elif wc >= 1500:
        s += 20
    elif wc >= 1000:
        s += 15
    elif wc >= 500:
        s += 8
    else:
        s += 3

    # Heading structure depth
    headings = re.findall(r'<h([2-6])', html, re.IGNORECASE)
    unique_levels = len(set(headings))
    s += min(15, unique_levels * 4)
    s += min(15, len(headings) * 1)

    # List items (educational content tends to have many)
    li_count = len(re.findall(r'<li', html, re.IGNORECASE))
    s += min(15, li_count * 1)

    # Paragraph count
    p_count = len(re.findall(r'<p[\s>]', html, re.IGNORECASE))
    s += min(10, p_count * 1)

    # Images (visual educational content)
    img_count = len(re.findall(r'<img\s', html, re.IGNORECASE))
    s += min(10, img_count * 2)

    # Breadth: unique informational subheadings
    subheads = re.findall(r'<h[2-4][^>]*>([^<]+)</h[2-4]>', html, re.IGNORECASE)
    s += min(5, len(subheads) * 1)

    return clamp(s)


def score_external_references(html, text, wc):
    """Authoritative external links and citations."""
    s = 0
    # Extract all hrefs
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)
    external_links = [h for h in hrefs if h.startswith('http') and 'pethubonline.com' not in h]

    # Count authority domain links
    auth_count = 0
    for link in external_links:
        link_lower = link.lower()
        for domain in AUTHORITY_DOMAINS:
            if domain in link_lower:
                auth_count += 1
                break

    s += min(40, auth_count * 10)

    # General external link count
    s += min(20, len(external_links) * 2)

    # In-text citations: patterns like (Source: ...), [Source], According to...
    cite_patterns = [
        r'(?:according\s+to|source\s*:|cited?\s+(?:by|from|in)|reference\s*:)',
        r'\((?:source|ref|citation)\s*:', r'as\s+(?:reported|noted|stated)\s+by',
        r'research\s+(?:shows|suggests|indicates|found|published)',
        r'study\s+(?:shows|suggests|found|published|conducted)',
    ]
    s += min(25, count_pattern(text, cite_patterns) * 5)

    # Scholarly / numeric citations
    num_cite = re.findall(r'\[\d+\]', text)
    s += min(15, len(num_cite) * 3)

    return clamp(s)


def score_internal_link_density(html, text, wc):
    """Internal links (outbound + inbound approximation)."""
    s = 0
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)
    internal = [h for h in hrefs if 'pethubonline.com' in h or (h.startswith('/') and not h.startswith('//'))]

    # Outbound internal links
    out_count = len(internal)
    s += min(50, out_count * 5)

    # Related posts sections
    related = [
        r'related\s+(?:post|article|read)', r'you\s+(?:may|might)\s+also\s+(?:like|enjoy)',
        r'see\s+also', r'further\s+reading', r'read\s+(?:more|next)',
        r'check\s+out\s+(?:our|this|these)',
    ]
    s += min(25, count_pattern(text, related) * 8)

    # Anchor text quality (internal links with descriptive text)
    internal_anchors = re.findall(
        r'<a[^>]*href=["\'][^"\']*pethubonline\.com[^"\']*["\'][^>]*>([^<]+)</a>',
        html, re.IGNORECASE
    )
    descriptive = [a for a in internal_anchors if len(a.split()) >= 2]
    s += min(25, len(descriptive) * 5)

    return clamp(s)


def score_answer_readiness(html, text, wc):
    """Quick-answer blocks, FAQ, structured Q&A for featured snippets."""
    s = 0
    # Quick answer / TLDR / summary at top
    quick = [
        r'(?:quick|short)\s+answer', r'tl\s*;\s*dr', r'in\s+(?:a\s+)?(?:nutshell|brief|short)',
        r'(?:the\s+)?(?:bottom|key)\s+(?:line|takeaway)', r'summary\s*:',
        r'key\s+(?:point|takeaway|finding)s?\s*:',
    ]
    s += min(20, count_pattern(text, quick) * 8)

    # Direct answer patterns (sentence starting with "The best...", "You should...")
    direct = [
        r'(?:the\s+best|the\s+top|the\s+most|we\s+recommend|our\s+(?:top|best)\s+pick)',
        r'(?:the\s+answer\s+is|yes\s*,|no\s*,)\s',
    ]
    s += min(20, count_pattern(text, direct) * 5)

    # Structured data / schema
    schema = [
        r'application/ld\+json', r'schema\.org', r'itemtype',
        r'FAQPage', r'HowTo', r'Product', r'Review', r'Article',
    ]
    s += min(20, count_pattern(html, schema) * 8)

    # List-based answers (numbered or bulleted near headings)
    s += min(20, count_pattern(html, [r'</h[2-4]>\s*(?:<[^>]*>\s*)*<[ou]l']) * 8)

    # Definition/answer boxes
    answer_boxes = [
        r'class=["\'][^"\']*(?:answer|summary|highlight|callout|info[\s-]?box)',
    ]
    s += min(20, count_pattern(html, answer_boxes) * 8)

    return clamp(s)


def score_citation_confidence(html, text, wc):
    """Composite: extractability + trust + comparison + source quality."""
    s = 0
    # Extractability: clean formatting, lists, short paragraphs
    short_paras = re.findall(r'<p[^>]*>([^<]{10,200})</p>', html)
    s += min(15, len(short_paras) * 1)

    # Trust markers (overlap with trust_intensity, but weighted differently here)
    trust = [r'reviewed\s+by', r'fact[\s-]?check', r'expert', r'certified', r'qualified']
    s += min(20, count_pattern(text, trust) * 6)

    # Source diversity
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)
    external = [h for h in hrefs if h.startswith('http') and 'pethubonline.com' not in h]
    unique_domains = set()
    for link in external:
        m = re.search(r'https?://(?:www\.)?([^/]+)', link)
        if m:
            unique_domains.add(m.group(1))
    s += min(25, len(unique_domains) * 5)

    # Data/statistics presence
    data_patterns = [
        r'\d+\s*%', r'\d+\s*(?:mg|g|kg|ml|l|oz|lb|cal|kcal)',
        r'(?:study|survey|research|data)\s+(?:show|suggest|found|reveal)',
    ]
    s += min(20, count_pattern(text, data_patterns) * 3)

    # Quotations
    quotes = len(re.findall(r'<blockquote', html, re.IGNORECASE))
    s += min(10, quotes * 5)

    # Named expert/vet quotes
    named = [r'(?:Dr\.?|Prof\.?|Professor)\s+[A-Z][a-z]+', r'(?:veterinarian|vet)\s+\w+\s+\w+']
    s += min(10, count_pattern(text, named) * 5)

    return clamp(s)


def score_semantic_depth(html, text, wc):
    """Terminology richness, definition coverage, entity overlap."""
    s = 0
    # Unique pet/vet terms used
    domain_terms = set()
    term_patterns = [
        r'kibble', r'palatab\w*', r'glucosamine', r'chondroitin', r'probiotic\w*',
        r'omega[\s-]?[36]', r'antioxidant\w*', r'hydrolyz\w*', r'microbiome',
        r'taurine', r'l[\s-]?carnitine', r'enrichment', r'desensiti[sz]\w*',
        r'brachycephalic', r'dermatitis', r'atop\w*', r'zoonotic',
        r'anaphyla\w*', r'neoplasi\w*', r'cardiomyopath\w*', r'dysplasia',
        r'hypothyroid\w*', r'hyperthyroid\w*', r'pancreatitis',
        r'coprophag\w*', r'pica\b', r'separation\s+anxiety',
        r'resource\s+guarding', r'counter[\s-]?conditioning',
        r'bioavailab\w*', r'amino\s+acid', r'fatty\s+acid', r'crude\s+protein',
        r'metaboli[sz]\w*', r'digestib\w*', r'fiber\b', r'fibre\b',
    ]
    text_lower = text.lower()
    for pat in term_patterns:
        if re.search(pat, text_lower):
            domain_terms.add(pat)

    s += min(40, len(domain_terms) * 4)

    # Definition patterns ("X is a...", "X refers to...")
    defs = [
        r'\b\w+\s+(?:is|are|refers?\s+to|means?|defined?\s+as)\s+(?:a|an|the)\s',
    ]
    s += min(25, count_pattern(text, defs) * 2)

    # Entity density (capitalized multi-word proper nouns)
    entities = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+', text)
    unique_entities = set(entities)
    s += min(20, len(unique_entities) * 1)

    # Technical depth marker
    tech = [r'(?:clinical|peer[\s-]?reviewed|evidence[\s-]?based|scientif)',]
    s += min(15, count_pattern(text, tech) * 5)

    return clamp(s)


def score_beginner_accessibility(html, text, wc):
    """Plain language, beginner explanations, 'what this means' patterns."""
    s = 0
    # Beginner-friendly markers
    beginner = [
        r'beginner', r'for\s+(?:new|first[\s-]?time)\s+(?:owner|parent|pet)',
        r'getting\s+started', r'ultimate\s+guide', r'complete\s+guide',
        r'everything\s+you\s+need\s+to\s+know', r'what\s+(?:you\s+)?need\s+to\s+know',
    ]
    s += min(25, count_pattern(text, beginner) * 8)

    # "What this means" / explanation patterns
    explain = [
        r'(?:what|this)\s+(?:this\s+)?means', r'in\s+other\s+words',
        r'(?:simply|basically)\s+put', r'(?:to\s+put\s+it|in)\s+simpl',
        r'(?:for\s+example|e\.g\.|i\.e\.)', r'in\s+layman[\'’]?s?\s+terms',
        r'think\s+of\s+it\s+(?:as|like)',
    ]
    s += min(30, count_pattern(text, explain) * 4)

    # Short sentences (readability)
    sentences = re.split(r'[.!?]+', text)
    short_sentences = [s_item for s_item in sentences if 3 <= len(s_item.split()) <= 15]
    ratio = len(short_sentences) / max(1, len(sentences))
    s += min(25, int(ratio * 40))

    # Analogies / comparisons for explanation
    analogy = [r'(?:just\s+)?like\s+(?:a|when|how)', r'similar\s+to', r'imagine\s+(?:a|that|if)']
    s += min(20, count_pattern(text, analogy) * 5)

    return clamp(s)


def score_safety_coverage(html, text, wc):
    """Safety warnings, 'when to seek help', hazard alerts."""
    s = 0
    # Safety/warning markers
    safety = [
        r'warning\s*:', r'caution\s*:', r'danger\s*:', r'important\s*:',
        r'safety\s+(?:tip|note|warning|precaution|concern)',
        r'(?:is|are)\s+(?:it\s+)?(?:safe|dangerous|toxic|poisonous|harmful)',
    ]
    s += min(25, count_pattern(text, safety) * 6)

    # When to seek help
    vet_seek = [
        r'(?:see|visit|consult|contact|call)\s+(?:a\s+|your\s+)?vet',
        r'when\s+to\s+(?:see|visit|call|seek)',
        r'emergency\s+(?:vet|sign|symptom)',
        r'seek\s+(?:immediate\s+)?(?:veterinary|medical|professional)',
        r'if\s+(?:symptoms?\s+)?persist',
    ]
    s += min(30, count_pattern(text, vet_seek) * 5)

    # Hazard/toxicity content
    hazard = [
        r'toxic\s+(?:to|for)\s+(?:dog|cat|pet)', r'poison\w*',
        r'choking\s+hazard', r'supervisi', r'never\s+(?:give|feed|let|leave)',
        r'avoid\s+(?:giving|feeding|using)', r'(?:harmful|unsafe)\s+(?:for|to)',
    ]
    s += min(25, count_pattern(text, hazard) * 4)

    # Visual safety callouts
    callouts = [
        r'class=["\'][^"\']*(?:warning|alert|danger|caution|notice)',
        r'⚠', r'☢', r'☣',  # warning emojis
    ]
    s += min(20, count_pattern(html, callouts) * 8)

    return clamp(s)


def score_decision_support(html, text, wc):
    """Buying criteria, troubleshooting, evaluation frameworks."""
    s = 0
    # Buying guide patterns
    buying = [
        r'buying\s+guide', r'how\s+to\s+choose', r'what\s+to\s+look\s+for',
        r'(?:key|important)\s+(?:feature|factor|consideration|criteri)',
        r'(?:before|when)\s+(?:you\s+)?buy', r'shopping\s+(?:guide|tip)',
        r'budget\s+(?:option|pick|friendly|range)',
    ]
    s += min(25, count_pattern(text, buying) * 6)

    # Evaluation framework
    eval_fw = [
        r'(?:we\s+)?(?:evaluat|assess|test|measur|compar|rank)\w*\s+(?:each|every|all)',
        r'(?:rating|scoring)\s+(?:system|criteria|method)',
        r'(?:weighted|overall)\s+score',
        r'our\s+(?:verdict|recommendation|pick|choice)',
    ]
    s += min(25, count_pattern(text, eval_fw) * 7)

    # Decision matrix / criteria lists
    criteria = [
        r'(?:size|weight|material|durability|price|quality|safety)\s*(?::|rating|\d)',
    ]
    s += min(15, count_pattern(text, criteria) * 3)

    # Recommendation patterns
    reco = [
        r'(?:best|ideal|perfect|great|recommend\w*)\s+(?:for|choice|option|pick)',
        r'(?:we|our)\s+(?:top|best|favorite|favourite)\s+(?:pick|choice|recommendation)',
        r'(?:winner|runner[\s-]?up|best\s+overall|best\s+value|best\s+budget)',
    ]
    s += min(20, count_pattern(text, reco) * 4)

    # Size/breed/age matching
    match_patterns = [
        r'(?:best\s+for|ideal\s+for|suited?\s+for|recommended\s+for)\s+(?:small|medium|large|puppy|kitten|senior|adult)',
    ]
    s += min(15, count_pattern(text, match_patterns) * 5)

    return clamp(s)


def score_authority_balance(all_scores):
    """How balanced are the other 14 dimensions? Penalize extreme imbalance."""
    other_scores = [all_scores[d] for d in DIMENSION_NAMES if d != "authority_balance"]
    if not other_scores:
        return 50
    mean = sum(other_scores) / len(other_scores)
    if mean == 0:
        return 10
    # Coefficient of variation (lower = more balanced)
    variance = sum((x - mean) ** 2 for x in other_scores) / len(other_scores)
    std = math.sqrt(variance)
    cv = std / mean if mean > 0 else 1.0
    # CV of 0 = perfect balance = 100, CV of 1+ = very unbalanced = ~20
    score = max(10, min(100, int(100 - cv * 80)))
    return score


# ── Master analysis ─────────────────────────────────────────────────────────

def analyze_post(post, all_slugs=None):
    """Compute all 15 dimension scores for a single post."""
    title = strip_html(post.get("title", {}).get("rendered", ""))
    slug = post.get("slug", "")
    html = post.get("content", {}).get("rendered", "")
    text = strip_html(html)
    wc = len(text.split())
    post_id = post.get("id", 0)

    cluster = classify_cluster(title, slug, text)

    scores = {}
    scores["trust_intensity"] = score_trust_intensity(html, text, wc)
    scores["glossary_density"] = score_glossary_density(html, text, wc)
    scores["faq_coverage"] = score_faq_coverage(html, text, wc)
    scores["comparison_density"] = score_comparison_density(html, text, wc)
    scores["practical_usefulness"] = score_practical_usefulness(html, text, wc)
    scores["educational_depth"] = score_educational_depth(html, text, wc)
    scores["external_references"] = score_external_references(html, text, wc)
    scores["internal_link_density"] = score_internal_link_density(html, text, wc)
    scores["answer_readiness"] = score_answer_readiness(html, text, wc)
    scores["citation_confidence"] = score_citation_confidence(html, text, wc)
    scores["semantic_depth"] = score_semantic_depth(html, text, wc)
    scores["beginner_accessibility"] = score_beginner_accessibility(html, text, wc)
    scores["safety_coverage"] = score_safety_coverage(html, text, wc)
    scores["decision_support"] = score_decision_support(html, text, wc)
    scores["authority_balance"] = score_authority_balance(scores)

    # Overall authority density (weighted composite)
    overall = sum(scores[d] * WEIGHTS[d] for d in DIMENSION_NAMES)
    overall = round(overall, 2)

    # Authority tier
    if overall >= 75:
        tier = "S"
    elif overall >= 55:
        tier = "A"
    elif overall >= 40:
        tier = "B"
    elif overall >= 25:
        tier = "C"
    else:
        tier = "D"

    return {
        "post_id": post_id,
        "title": title,
        "slug": slug,
        "cluster": cluster,
        "word_count": wc,
        "scores": scores,
        "overall_authority_density": overall,
        "authority_tier": tier,
    }


def compute_inbound_links(posts, results):
    """Second pass: count inbound internal links for each post."""
    slug_to_idx = {}
    for i, r in enumerate(results):
        slug_to_idx[r["slug"]] = i

    inbound_counts = defaultdict(int)
    for post in posts:
        html = post.get("content", {}).get("rendered", "")
        hrefs = re.findall(r'href=["\'](?:https?://pethubonline\.com)?/([^"\'#?]+)', html, re.IGNORECASE)
        for href_slug in hrefs:
            href_slug = href_slug.strip("/").split("/")[-1]
            if href_slug in slug_to_idx:
                inbound_counts[href_slug] += 1

    # Adjust internal_link_density scores with inbound data
    for r in results:
        inbound = inbound_counts.get(r["slug"], 0)
        bonus = min(25, inbound * 5)
        old = r["scores"]["internal_link_density"]
        r["scores"]["internal_link_density"] = clamp(old + bonus)
        # Recalculate overall
        r["overall_authority_density"] = round(
            sum(r["scores"][d] * WEIGHTS[d] for d in DIMENSION_NAMES), 2
        )
        # Re-tier
        oa = r["overall_authority_density"]
        if oa >= 75:
            r["authority_tier"] = "S"
        elif oa >= 55:
            r["authority_tier"] = "A"
        elif oa >= 40:
            r["authority_tier"] = "B"
        elif oa >= 25:
            r["authority_tier"] = "C"
        else:
            r["authority_tier"] = "D"


def write_full_csv(results):
    """Write Authority_Telemetry_Full.csv."""
    path = os.path.join(OUT_DIR, "Authority_Telemetry_Full.csv")
    headers = ["post_id", "title", "slug", "cluster", "word_count"] + DIMENSION_NAMES + \
              ["overall_authority_density", "authority_tier"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in sorted(results, key=lambda x: x["overall_authority_density"], reverse=True):
            row = [r["post_id"], r["title"], r["slug"], r["cluster"], r["word_count"]]
            row += [r["scores"][d] for d in DIMENSION_NAMES]
            row += [r["overall_authority_density"], r["authority_tier"]]
            w.writerow(row)
    print(f"\n  Written: {path} ({len(results)} rows)")


def write_cluster_dashboard(results):
    """Write Cluster_Authority_Dashboard.csv."""
    path = os.path.join(OUT_DIR, "Cluster_Authority_Dashboard.csv")
    clusters = defaultdict(list)
    for r in results:
        clusters[r["cluster"]].append(r)

    headers = ["cluster", "post_count", "avg_word_count"] + \
              [f"avg_{d}" for d in DIMENSION_NAMES] + \
              ["overall_authority", "authority_tier", "strongest_dimension",
               "weakest_dimension", "top_priority_action"]

    rows = []
    for cluster_name, posts in sorted(clusters.items(), key=lambda x: -len(x[1])):
        n = len(posts)
        avg_wc = round(sum(p["word_count"] for p in posts) / n, 1)
        dim_avgs = {}
        for d in DIMENSION_NAMES:
            dim_avgs[d] = round(sum(p["scores"][d] for p in posts) / n, 2)

        overall = round(sum(dim_avgs[d] * WEIGHTS[d] for d in DIMENSION_NAMES), 2)

        if overall >= 75:
            tier = "S"
        elif overall >= 55:
            tier = "A"
        elif overall >= 40:
            tier = "B"
        elif overall >= 25:
            tier = "C"
        else:
            tier = "D"

        strongest = max(DIMENSION_NAMES, key=lambda d: dim_avgs[d])
        weakest = min(DIMENSION_NAMES, key=lambda d: dim_avgs[d])

        # Generate priority action
        action = generate_priority_action(weakest, dim_avgs[weakest], cluster_name)

        row = [cluster_name, n, avg_wc]
        row += [dim_avgs[d] for d in DIMENSION_NAMES]
        row += [overall, tier, strongest.replace("_", " ").title(),
                weakest.replace("_", " ").title(), action]
        rows.append(row)

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for row in sorted(rows, key=lambda x: -x[headers.index("overall_authority")]):
            w.writerow(row)
    print(f"  Written: {path} ({len(rows)} clusters)")
    return rows


def generate_priority_action(weakest_dim, score, cluster):
    """Generate a specific action recommendation for the weakest dimension."""
    actions = {
        "trust_intensity": f"Add 'Reviewed by' credentials and editorial methodology section to {cluster} posts",
        "glossary_density": f"Add Key Terms block with bold-dash definitions to each {cluster} post",
        "faq_coverage": f"Add structured FAQ section (5+ questions) with schema markup to {cluster} posts",
        "comparison_density": f"Add comparison tables with ratings and pro/con sections to {cluster} posts",
        "practical_usefulness": f"Add step-by-step guides, checklists, and troubleshooting sections to {cluster} posts",
        "educational_depth": f"Expand {cluster} posts with deeper subheadings, lists, and 1500+ word targets",
        "external_references": f"Add 3+ authoritative citations (RSPCA/BVA/PDSA/gov.uk) to each {cluster} post",
        "internal_link_density": f"Add 3-5 contextual internal links per {cluster} post to related content",
        "answer_readiness": f"Add quick-answer boxes and structured data markup to {cluster} posts",
        "citation_confidence": f"Add named expert quotes and data-backed claims to {cluster} posts",
        "semantic_depth": f"Incorporate more domain-specific terminology and definitions in {cluster} posts",
        "beginner_accessibility": f"Add beginner-friendly explanations and 'what this means' sections to {cluster} posts",
        "safety_coverage": f"Add safety warnings and 'when to see a vet' sections to {cluster} posts",
        "decision_support": f"Add buying guides with evaluation criteria and size/breed matching to {cluster} posts",
        "authority_balance": f"Balance dimension scores across {cluster} posts by lifting weakest areas",
    }
    return actions.get(weakest_dim, f"Improve {weakest_dim} in {cluster} posts")


def write_acceleration_map(results):
    """Write Authority_Acceleration_Map.csv."""
    path = os.path.join(OUT_DIR, "Authority_Acceleration_Map.csv")
    clusters = defaultdict(list)
    for r in results:
        clusters[r["cluster"]].append(r)

    headers = ["cluster", "dimension", "current_score", "target_score", "gap",
               "effort_to_close", "priority", "suggested_first_action"]

    rows = []
    for cluster_name, posts in sorted(clusters.items()):
        n = len(posts)
        for d in DIMENSION_NAMES:
            current = round(sum(p["scores"][d] for p in posts) / n, 2)
            # Target: at least 60 for all, or current+15, whichever is higher
            target = max(60, min(100, current + 15))
            gap = round(target - current, 2)

            # Effort estimate based on gap and dimension complexity
            if gap <= 5:
                effort = "Low"
            elif gap <= 20:
                effort = "Medium"
            elif gap <= 40:
                effort = "High"
            else:
                effort = "Very High"

            # Priority based on weight * gap
            priority_score = WEIGHTS[d] * gap
            if priority_score >= 3:
                priority = "Critical"
            elif priority_score >= 1.5:
                priority = "High"
            elif priority_score >= 0.5:
                priority = "Medium"
            else:
                priority = "Low"

            action = generate_priority_action(d, current, cluster_name)
            rows.append([cluster_name, d.replace("_", " ").title(), current, target,
                         gap, effort, priority, action])

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for row in rows:
            w.writerow(row)
    print(f"  Written: {path} ({len(rows)} acceleration entries)")


def print_summary(results):
    """Print comprehensive summary."""
    print("\n" + "=" * 90)
    print("  10AE-I: LIVE AUTHORITY TELEMETRY - pethubonline.com")
    print("=" * 90)

    # Site-wide stats
    total = len(results)
    avg_overall = sum(r["overall_authority_density"] for r in results) / max(1, total)
    avg_wc = sum(r["word_count"] for r in results) / max(1, total)

    print(f"\n  SITE-WIDE AUTHORITY DENSITY: {avg_overall:.2f} / 100")
    print(f"  Total Published Posts: {total}")
    print(f"  Average Word Count: {avg_wc:.0f}")

    # Tier distribution
    tier_counts = Counter(r["authority_tier"] for r in results)
    print(f"\n  TIER DISTRIBUTION:")
    for tier in ["S", "A", "B", "C", "D"]:
        count = tier_counts.get(tier, 0)
        pct = (count / total * 100) if total > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"    Tier {tier}: {count:>4} posts ({pct:5.1f}%) {bar}")

    # Dimension rankings (site-wide averages)
    print(f"\n  DIMENSION RANKINGS (Site-Wide Averages):")
    dim_avgs = {}
    for d in DIMENSION_NAMES:
        dim_avgs[d] = sum(r["scores"][d] for r in results) / max(1, total)
    for rank, (d, avg) in enumerate(sorted(dim_avgs.items(), key=lambda x: -x[1]), 1):
        bar = "#" * int(avg / 2)
        label = d.replace("_", " ").title()
        weight_pct = WEIGHTS[d] * 100
        print(f"    {rank:>2}. {label:<28} {avg:5.1f} (wt:{weight_pct:.0f}%) {bar}")

    # Per-cluster dashboard
    clusters = defaultdict(list)
    for r in results:
        clusters[r["cluster"]].append(r)

    print(f"\n  CLUSTER AUTHORITY DASHBOARD ({len(clusters)} clusters):")
    print(f"  {'Cluster':<28} {'Posts':>5} {'AvgWC':>6} {'AuthDen':>7} {'Tier':>4} {'Strongest':<24} {'Weakest':<24}")
    print(f"  {'-'*28} {'-'*5} {'-'*6} {'-'*7} {'-'*4} {'-'*24} {'-'*24}")

    cluster_rows = []
    for cluster_name, posts in sorted(clusters.items(), key=lambda x: -len(x[1])):
        n = len(posts)
        avg_wc_c = sum(p["word_count"] for p in posts) / n
        c_dim_avgs = {d: sum(p["scores"][d] for p in posts) / n for d in DIMENSION_NAMES}
        c_overall = sum(c_dim_avgs[d] * WEIGHTS[d] for d in DIMENSION_NAMES)
        strongest = max(DIMENSION_NAMES, key=lambda d: c_dim_avgs[d])
        weakest = min(DIMENSION_NAMES, key=lambda d: c_dim_avgs[d])
        if c_overall >= 75:
            tier = "S"
        elif c_overall >= 55:
            tier = "A"
        elif c_overall >= 40:
            tier = "B"
        elif c_overall >= 25:
            tier = "C"
        else:
            tier = "D"
        cluster_rows.append((cluster_name, n, avg_wc_c, c_overall, tier, strongest, weakest))

    for (cn, n, awc, co, t, s, w) in sorted(cluster_rows, key=lambda x: -x[3]):
        s_label = s.replace("_", " ").title()[:23]
        w_label = w.replace("_", " ").title()[:23]
        print(f"  {cn:<28} {n:>5} {awc:>6.0f} {co:>7.2f} {t:>4} {s_label:<24} {w_label:<24}")

    # Top 10 strongest posts
    sorted_by_auth = sorted(results, key=lambda x: x["overall_authority_density"], reverse=True)
    print(f"\n  TOP 10 STRONGEST POSTS:")
    print(f"  {'#':>3} {'Auth':>5} {'Tier':>4} {'WC':>5} {'Cluster':<24} Title")
    print(f"  {'-'*3} {'-'*5} {'-'*4} {'-'*5} {'-'*24} {'-'*40}")
    for i, r in enumerate(sorted_by_auth[:10], 1):
        print(f"  {i:>3} {r['overall_authority_density']:>5.1f} {r['authority_tier']:>4} "
              f"{r['word_count']:>5} {r['cluster']:<24} {r['title'][:60]}")

    # Top 10 weakest posts
    print(f"\n  TOP 10 WEAKEST POSTS (Priority Improvements):")
    print(f"  {'#':>3} {'Auth':>5} {'Tier':>4} {'WC':>5} {'Cluster':<24} Title")
    print(f"  {'-'*3} {'-'*5} {'-'*4} {'-'*5} {'-'*24} {'-'*40}")
    for i, r in enumerate(sorted_by_auth[-10:], 1):
        print(f"  {i:>3} {r['overall_authority_density']:>5.1f} {r['authority_tier']:>4} "
              f"{r['word_count']:>5} {r['cluster']:<24} {r['title'][:60]}")

    # Recommended next actions
    print(f"\n  RECOMMENDED NEXT ACTIONS:")
    print(f"  " + "-" * 80)

    # 1. Weakest dimension site-wide
    weakest_dim = min(dim_avgs, key=dim_avgs.get)
    print(f"  1. LIFT WEAKEST DIMENSION: {weakest_dim.replace('_',' ').title()} "
          f"(avg {dim_avgs[weakest_dim]:.1f})")
    print(f"     -> {generate_priority_action(weakest_dim, dim_avgs[weakest_dim], 'all')}")

    # 2. Highest-weight low-scoring dimension
    weighted_gaps = [(d, (60 - dim_avgs[d]) * WEIGHTS[d]) for d in DIMENSION_NAMES if dim_avgs[d] < 60]
    if weighted_gaps:
        critical_dim = max(weighted_gaps, key=lambda x: x[1])[0]
        print(f"  2. CRITICAL WEIGHTED GAP: {critical_dim.replace('_',' ').title()} "
              f"(avg {dim_avgs[critical_dim]:.1f}, weight {WEIGHTS[critical_dim]*100:.0f}%)")
        print(f"     -> {generate_priority_action(critical_dim, dim_avgs[critical_dim], 'all')}")

    # 3. Tier D posts
    d_posts = [r for r in results if r["authority_tier"] == "D"]
    if d_posts:
        print(f"  3. RESCUE TIER-D POSTS: {len(d_posts)} posts need urgent attention")
        for r in d_posts[:5]:
            print(f"     - [{r['overall_authority_density']:.1f}] {r['title'][:70]}")

    # 4. Cluster with lowest authority
    if cluster_rows:
        worst_cluster = min(cluster_rows, key=lambda x: x[3])
        print(f"  4. WEAKEST CLUSTER: {worst_cluster[0]} "
              f"(auth: {worst_cluster[3]:.1f}, {worst_cluster[1]} posts)")
        wk = worst_cluster[6]
        print(f"     -> Focus on {wk.replace('_',' ').title()} dimension first")

    # 5. Quick wins: posts just below tier threshold
    near_a = [r for r in results if 50 <= r["overall_authority_density"] < 55]
    near_b = [r for r in results if 35 <= r["overall_authority_density"] < 40]
    if near_a:
        print(f"  5. QUICK WIN (B->A): {len(near_a)} posts within 5 pts of Tier A")
        for r in near_a[:3]:
            print(f"     - [{r['overall_authority_density']:.1f}] {r['title'][:70]}")
    if near_b:
        print(f"  6. QUICK WIN (C->B): {len(near_b)} posts within 5 pts of Tier B")
        for r in near_b[:3]:
            print(f"     - [{r['overall_authority_density']:.1f}] {r['title'][:70]}")

    print(f"\n{'=' * 90}")
    print(f"  Authority telemetry complete. 3 CSVs written to {OUT_DIR}")
    print(f"{'=' * 90}\n")


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  10AE-I: Live Authority Telemetry")
    print("  pethubonline.com - 15-Dimension Authority Measurement")
    print("=" * 70)

    # Verify weights sum to 1.0
    weight_sum = sum(WEIGHTS.values())
    assert abs(weight_sum - 1.0) < 0.001, f"Weights sum to {weight_sum}, expected 1.0"
    print(f"\n  Weight validation OK (sum={weight_sum})")

    print(f"\n[1/5] Fetching all published posts...")
    posts = fetch_all_posts()
    if not posts:
        print("ERROR: No posts fetched. Aborting.")
        sys.exit(1)
    print(f"  Total posts fetched: {len(posts)}")

    print(f"\n[2/5] Analyzing 15 authority dimensions per post...")
    results = []
    for i, post in enumerate(posts):
        r = analyze_post(post)
        results.append(r)
        if (i + 1) % 25 == 0 or (i + 1) == len(posts):
            print(f"  Analyzed {i+1}/{len(posts)} posts...", flush=True)

    print(f"\n[3/5] Computing inbound link graph and adjusting scores...")
    compute_inbound_links(posts, results)

    print(f"\n[4/5] Writing CSV outputs...")
    write_full_csv(results)
    write_cluster_dashboard(results)
    write_acceleration_map(results)

    print(f"\n[5/5] Generating summary report...")
    print_summary(results)


if __name__ == "__main__":
    main()
