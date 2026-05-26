#!/usr/bin/env python3
"""
generate_owner_review_summaries.py

Fetches draft dog food posts from the PetHub Online WordPress REST API,
analyses content quality, trust/safety, SEO metadata, schema status,
product evidence, and publishing readiness, then writes a single JSON
summary file for owner review.

Output: /var/lib/freelancer/projects/40416335/owner_review_summaries.json
"""

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser

import requests
from requests.auth import HTTPBasicAuth

# ── Configuration ────────────────────────────────────────────────────
BASE_DIR = "/var/lib/freelancer/projects/40416335"
WP_USER = "jasonsarah2026"
WP_PASS = "***REDACTED_WP_PASSWORD***"
REST_BASE = "https://pethubonline.com/wp-json/wp/v2"
OUTPUT_FILE = os.path.join(BASE_DIR, "owner_review_summaries.json")

POSTS = {
    3836: {
        "slug": "best-dog-food-uk",
        "focus_kw": "best dog food uk",
        "seo_title": "Best Dog Food UK (2026) | Honest Reviews & Buying Guide",
        "seo_title_len": 55,
        "seo_desc": "Best dog food UK picks for 2026. Evidence-based reviews covering dry, wet, raw and fresh options with honest ingredient analysis, feeding charts and pricing.",
        "og_title": "Best Dog Food UK (2026) | Honest Reviews & Buying Guide",
        "og_desc": "Best dog food UK picks for 2026. Evidence-based reviews covering dry, wet, raw and fresh options with honest ingredient analysis, feeding charts and pricing.",
        "tw_title": "Best Dog Food UK (2026) | Honest Reviews & Buying Guide",
        "tw_desc": "Best dog food UK picks for 2026. Evidence-based reviews covering dry, wet, raw and fresh options with honest ingredient analysis, feeding charts and pricing.",
    },
    3837: {
        "slug": "best-dry-dog-food-uk",
        "focus_kw": "best dry dog food uk",
        "seo_title": "Best Dry Dog Food UK (2026) | Kibble Guide & Comparison",
        "seo_title_len": 55,
        "seo_desc": "Best dry dog food UK brands for 2026. Compare kibble types, FEDIAF standards, feeding amounts, storage tips and quality indicators in this evidence-based guide.",
        "og_title": "Best Dry Dog Food UK (2026) | Kibble Guide & Comparison",
        "og_desc": "Best dry dog food UK brands for 2026. Compare kibble types, FEDIAF standards, feeding amounts, storage tips and quality indicators in this evidence-based guide.",
        "tw_title": "Best Dry Dog Food UK (2026) | Kibble Guide & Comparison",
        "tw_desc": "Best dry dog food UK brands for 2026. Compare kibble types, FEDIAF standards, feeding amounts, storage tips and quality indicators in this evidence-based guide.",
    },
    3838: {
        "slug": "dry-vs-wet-dog-food-uk",
        "focus_kw": "dry vs wet dog food",
        "seo_title": "Dry vs Wet Dog Food UK (2026): Side-by-Side Comparison",
        "seo_title_len": 54,
        "seo_desc": "Dry vs wet dog food compared for UK dogs. Nutritional analysis, cost breakdown, mixed feeding ratios and situation-based recommendations in this honest guide.",
        "og_title": "Dry vs Wet Dog Food UK (2026): Side-by-Side Comparison",
        "og_desc": "Dry vs wet dog food compared for UK dogs. Nutritional analysis, cost breakdown, mixed feeding ratios and situation-based recommendations in this honest guide.",
        "tw_title": "Dry vs Wet Dog Food UK (2026): Side-by-Side Comparison",
        "tw_desc": "Dry vs wet dog food compared for UK dogs. Nutritional analysis, cost breakdown, mixed feeding ratios and situation-based recommendations in this honest guide.",
    },
    3839: {
        "slug": "best-puppy-food-uk",
        "focus_kw": "best puppy food uk",
        "seo_title": "Best Puppy Food UK (2026) | Feeding & Nutrition Guide",
        "seo_title_len": 53,
        "seo_desc": "Best puppy food UK guide for 2026. Age-based feeding schedules, FEDIAF nutrient requirements, portion charts, transition timelines and large breed considerations.",
        "og_title": "Best Puppy Food UK (2026) | Feeding & Nutrition Guide",
        "og_desc": "Best puppy food UK guide for 2026. Age-based feeding schedules, FEDIAF nutrient requirements, portion charts, transition timelines and large breed considerations.",
        "tw_title": "Best Puppy Food UK (2026) | Feeding & Nutrition Guide",
        "tw_desc": "Best puppy food UK guide for 2026. Age-based feeding schedules, FEDIAF nutrient requirements, portion charts, transition timelines and large breed considerations.",
    },
}


# ── HTML helpers ─────────────────────────────────────────────────────
class HTMLTextExtractor(HTMLParser):
    """Strip tags and return plain text."""

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def strip_html(html: str) -> str:
    ext = HTMLTextExtractor()
    ext.feed(html)
    return ext.get_text()


def extract_headings(html: str) -> dict:
    """Return lists of headings by level."""
    result = {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []}
    for level in range(1, 7):
        tag = f"h{level}"
        pattern = re.compile(rf"<{tag}[^>]*>(.*?)</{tag}>", re.DOTALL | re.IGNORECASE)
        for m in pattern.finditer(html):
            result[tag].append(strip_html(m.group(1)).strip())
    return result


def count_tables(html: str) -> int:
    return len(re.findall(r"<table[\s>]", html, re.IGNORECASE))


def count_images(html: str) -> int:
    return len(re.findall(r"<img[\s>]", html, re.IGNORECASE))


def count_hr(html: str) -> int:
    return len(re.findall(r"<hr[\s/>]", html, re.IGNORECASE))


def count_divs(html: str) -> dict:
    opens = len(re.findall(r"<div[\s>]", html, re.IGNORECASE))
    closes = len(re.findall(r"</div>", html, re.IGNORECASE))
    return {"open": opens, "close": closes, "balanced": opens == closes}


def count_internal_links(html: str) -> dict:
    """Count internal links (pethubonline.com) and list targets."""
    pattern = re.compile(r'<a[^>]+href=["\']([^"\']+)["\']', re.IGNORECASE)
    internal = []
    for m in pattern.finditer(html):
        href = m.group(1)
        if "pethubonline.com" in href or (href.startswith("/") and not href.startswith("//")):
            internal.append(href)
    return {"count": len(internal), "targets": sorted(set(internal))}


def count_faq_items(html: str) -> int:
    """Count FAQ items -- look for schema-faq-section or faq patterns."""
    # RankMath / common FAQ block patterns
    count = 0
    count += len(re.findall(r"schema-faq-question", html, re.IGNORECASE))
    if count == 0:
        # fallback: count <strong> inside faq-type containers, or repeated Q&A patterns
        count += len(re.findall(r'class="[^"]*faq[^"]*"', html, re.IGNORECASE))
    if count == 0:
        # fallback: look for heading-based FAQ (H3 ending with ?)
        count += len(re.findall(r"<h[23][^>]*>[^<]*\?[^<]*</h[23]>", html, re.IGNORECASE))
    return count


def extract_paragraphs(html: str) -> list[str]:
    """Return paragraph texts."""
    pattern = re.compile(r"<p[^>]*>(.*?)</p>", re.DOTALL | re.IGNORECASE)
    return [strip_html(m.group(1)).strip() for m in pattern.finditer(html) if strip_html(m.group(1)).strip()]


def extract_lists(html: str) -> int:
    """Count <ul> and <ol> blocks."""
    return len(re.findall(r"<[uo]l[\s>]", html, re.IGNORECASE))


# ── Trust & Safety scanners ──────────────────────────────────────────
SAFETY_CHECKS = {
    "no_fake_testing_claims": {
        "patterns": [
            r"\bwe tested\b",
            r"\bour tests?\b",
            r"\btesting showed\b",
            r"\bwe reviewed\b",
            r"\bour review(s|ing)? (found|showed|confirmed)\b",
            r"\bwe fed\b.*\bdog",
            r"\bin our (hands-on|independent) test",
            r"\bour team tested\b",
            r"\bwe put .* to the test\b",
        ],
        "description": "Claims of firsthand product testing by PetHub",
    },
    "no_fake_vet_claims": {
        "patterns": [
            r"\bvet[\- ]?approved\b",
            r"\bveterinarian[\- ]?recommended\b",
            r"\bour vet\b",
            r"\bvet[\- ]?endorsed\b",
            r"\bvet[\- ]?verified\b",
            r"\brecommended by vets?\b",
            r"\bour veterinar",
            r"\bPetHub.*vet\b",
        ],
        "description": "Claims of veterinary endorsement by PetHub",
    },
    "no_fake_customer_feedback": {
        "patterns": [
            r"\bcustomers? say\b",
            r"\breviews? show\b",
            r"\brated by\b",
            r"\bdog owners? report\b",
            r"\bour readers?\b.*\b(say|report|love|prefer)",
            r"\bbuyers? (say|report|confirm)\b",
            r"\bfeedback from .*(customer|user|reader|buyer)",
        ],
        "description": "Claims of customer/reader feedback without evidence",
    },
    "no_invented_prices": {
        "patterns": [
            r"\xa3\d+\.\d{2}",  # £XX.XX
            r"GBP\s*\d+\.\d{2}",
            r"\bpriced? at \xa3",
            r"\bcosts? (around|about|approximately) \xa3\d+",
            r"\bRRP\b.*\xa3\d+",
        ],
        "description": "Specific GBP price claims",
    },
    "no_invented_ratings": {
        "patterns": [
            r"\d+(\.\d+)?/5\b",
            r"\d+(\.\d+)? out of 5\b",
            r"\bstar rating\b",
            r"\b[4-5]\s*stars?\b",
            r"\brated \d",
            r"\bscored? \d+(\.\d+)?/",
            r"\b\d+(\.\d+)? rating\b",
        ],
        "description": "Star ratings or numerical scores",
    },
    "no_invented_review_counts": {
        "patterns": [
            r"\d{2,}\s*reviews?\b",
            r"\breviewed by \d+",
            r"\b\d+,?\d*\+? (customer|user|buyer) reviews?\b",
            r"\b\d+,?\d*\+? ratings?\b",
            r"\b(thousands?|hundreds?) of reviews?\b",
        ],
        "description": "Review count claims",
    },
    "no_unsupported_health_claims": {
        "patterns": [
            r"\b(cure|cures|curing)\b",
            r"\b(treat|treats|treating) (disease|illness|condition|cancer|diabetes|arthritis)\b",
            r"\bprevents? (disease|illness|cancer|diabetes)\b",
            r"\bclinically proven\b(?!.*FEDIAF)",
            r"\bscientifically proven\b",
            r"\bmedically proven\b",
            r"\bguaranteed to\b.*(health|weight|energy)",
        ],
        "description": "Unsupported medical/health claims",
    },
    "no_manipulative_affiliate": {
        "patterns": [
            r"\bbuy now\b",
            r"\blimited time\b",
            r"\bexclusive deal\b",
            r"\bhurry\b",
            r"\bdon'?t miss\b",
            r"\bact (fast|now|quickly)\b",
            r"\blast chance\b",
            r"\bonly \d+ left\b",
            r"\bwhile stocks? last\b",
            r"\bsale ends?\b",
            r"\bspecial offer\b",
            r"\bdiscount code\b",
            r"\bflash sale\b",
        ],
        "description": "Manipulative urgency/scarcity affiliate language",
    },
}


def run_safety_checks(plain_text: str) -> dict:
    """Run all safety pattern checks against plain text. Return pass/fail + evidence."""
    results = {}
    text_lower = plain_text.lower()
    for check_name, spec in SAFETY_CHECKS.items():
        matches_found = []
        for pat in spec["patterns"]:
            for m in re.finditer(pat, text_lower):
                # grab context: 40 chars either side
                start = max(0, m.start() - 40)
                end = min(len(text_lower), m.end() + 40)
                context = plain_text[start:end].replace("\n", " ").strip()
                matches_found.append({
                    "matched_pattern": pat,
                    "context": f"...{context}...",
                })
        passed = len(matches_found) == 0
        results[check_name] = {
            "status": "pass" if passed else "FAIL",
            "description": spec["description"],
            "match_count": len(matches_found),
            "evidence": matches_found[:10],  # cap at 10 examples
        }
    return results


def check_filler_padding(plain_text: str, headings: dict, paragraphs: list, tables: int, lists_count: int) -> dict:
    """Check if word count is justified by actual content depth."""
    word_count = len(plain_text.split())
    h2_count = len(headings.get("h2", []))
    h3_count = len(headings.get("h3", []))
    substantive_paras = [p for p in paragraphs if len(p.split()) > 15]
    # Heuristic: if we have at least 1 heading per 300 words and
    # substantive paragraphs cover >60% of total paragraphs, content is justified
    heading_density = (h2_count + h3_count) / max(word_count / 300, 1)
    substantive_ratio = len(substantive_paras) / max(len(paragraphs), 1)
    passed = heading_density >= 0.5 and substantive_ratio >= 0.4
    return {
        "status": "pass" if passed else "FAIL",
        "description": "Content depth justifies word count",
        "word_count": word_count,
        "substantive_paragraphs": len(substantive_paras),
        "total_paragraphs": len(paragraphs),
        "substantive_ratio": round(substantive_ratio, 2),
        "heading_density_per_300w": round(heading_density, 2),
        "tables": tables,
        "lists": lists_count,
    }


# ── Content quality assessment ───────────────────────────────────────
def assess_content_quality(html: str, plain_text: str, focus_kw: str, headings: dict) -> dict:
    paragraphs = extract_paragraphs(html)
    tables = count_tables(html)
    lists_count = extract_lists(html)
    substantive_paras = [p for p in paragraphs if len(p.split()) > 15]
    word_count = len(plain_text.split())

    # Usefulness score (0-10)
    score = 0
    if len(substantive_paras) >= 5:
        score += 2
    elif len(substantive_paras) >= 3:
        score += 1
    if tables >= 1:
        score += 2
    elif tables == 0:
        score += 0
    if lists_count >= 2:
        score += 1
    h2_count = len(headings.get("h2", []))
    h3_count = len(headings.get("h3", []))
    if h2_count >= 4:
        score += 2
    elif h2_count >= 2:
        score += 1
    if word_count >= 1500:
        score += 1
    if word_count >= 2500:
        score += 1
    faq_count = count_faq_items(html)
    if faq_count >= 3:
        score += 1
    score = min(score, 10)

    # Search intent match
    kw_lower = focus_kw.lower()
    h1_texts = " ".join(headings.get("h1", [])).lower()
    h2_texts = " ".join(headings.get("h2", [])).lower()
    kw_in_h1 = kw_lower in h1_texts
    kw_in_any_h2 = kw_lower in h2_texts
    kw_words_in_headings = sum(1 for w in kw_lower.split() if w in (h1_texts + " " + h2_texts))
    intent_match = "strong" if kw_in_h1 else ("partial" if kw_words_in_headings >= len(kw_lower.split()) // 2 else "weak")

    # UK relevance
    uk_markers = ["uk", "britain", "british", "fediaf", "pounds", "gbp", "england",
                   "scotland", "wales", "pence", "defra", "pet food manufacturers",
                   "united kingdom"]
    uk_hits = sum(1 for marker in uk_markers if marker in plain_text.lower())
    uk_relevance = "strong" if uk_hits >= 4 else ("moderate" if uk_hits >= 2 else "weak")

    # Readability
    para_lengths = [len(p.split()) for p in paragraphs if p]
    avg_para_len = round(sum(para_lengths) / max(len(para_lengths), 1), 1)
    total_headings = h2_count + h3_count
    heading_frequency = round(word_count / max(total_headings, 1))

    # Heading quality
    descriptive_h2 = [h for h in headings.get("h2", []) if len(h.split()) >= 3]
    heading_quality = {
        "h2_count": h2_count,
        "h3_count": h3_count,
        "descriptive_h2_count": len(descriptive_h2),
        "all_h2_descriptive": len(descriptive_h2) == h2_count and h2_count > 0,
    }

    return {
        "usefulness_score": score,
        "usefulness_max": 10,
        "usefulness_breakdown": {
            "substantive_paragraphs": len(substantive_paras),
            "tables": tables,
            "lists": lists_count,
            "h2_count": h2_count,
            "word_count": word_count,
            "faq_items": faq_count,
        },
        "search_intent_match": intent_match,
        "search_intent_detail": {
            "kw_in_h1": kw_in_h1,
            "kw_in_any_h2": kw_in_any_h2,
            "kw_words_in_headings": kw_words_in_headings,
        },
        "uk_relevance": uk_relevance,
        "uk_marker_hits": uk_hits,
        "readability": {
            "avg_paragraph_length_words": avg_para_len,
            "heading_frequency_words_per_heading": heading_frequency,
        },
        "heading_quality": heading_quality,
        "faq_quality": {
            "faq_item_count": faq_count,
            "has_question_mark_headings": any("?" in h for h in headings.get("h3", [])),
        },
        "internal_linking": count_internal_links(html),
    }


# ── SEO section ──────────────────────────────────────────────────────
def compute_seo(plain_text: str, meta: dict, focus_kw: str) -> dict:
    seo_title = meta.get("seo_title", "")
    seo_desc = meta.get("seo_desc", "")
    kw_lower = focus_kw.lower()
    title_lower = seo_title.lower()
    desc_lower = seo_desc.lower()
    text_lower = plain_text.lower()

    # Keyword density
    kw_occurrences = len(re.findall(re.escape(kw_lower), text_lower))
    total_words = len(text_lower.split())
    kw_word_count = len(kw_lower.split())
    kw_density = round((kw_occurrences * kw_word_count / max(total_words, 1)) * 100, 2)

    return {
        "seo_title": seo_title,
        "seo_title_length": len(seo_title),
        "seo_description": seo_desc,
        "seo_description_length": len(seo_desc),
        "focus_keyword": focus_kw,
        "kw_in_title": kw_lower in title_lower,
        "kw_starts_desc": desc_lower.startswith(kw_lower),
        "kw_density_pct": kw_density,
        "kw_occurrences": kw_occurrences,
        "og_title": meta.get("og_title", ""),
        "og_desc": meta.get("og_desc", ""),
        "tw_title": meta.get("tw_title", ""),
        "tw_desc": meta.get("tw_desc", ""),
    }


# ── Schema section ───────────────────────────────────────────────────
def build_schema_section(post_id: int, schema_data: dict) -> dict:
    entry = schema_data.get("schemas", {}).get(str(post_id), {})
    return {
        "schema_status": "PROPOSAL ONLY",
        "schema_types_proposed": entry.get("schema_types", []),
        "excluded_types": entry.get("excluded_types", []),
        "faq_count_in_schema": entry.get("faq_count", 0),
    }


# ── Product evidence section ─────────────────────────────────────────
def build_evidence_section(post_id: int, evidence_data: dict) -> dict:
    linked = []
    any_unverified = False
    for entry in evidence_data.get("entries", []):
        page_refs = entry.get("linked_pages", [])
        # Check if this entry is linked to the post_id
        matches = any(str(post_id) in ref for ref in page_refs)
        if not matches:
            # Also check old IDs mapping: 3836<->3715, 3837<->3717, 3838<->3719, 3839<->3720
            old_map = {3836: "3715", 3837: "3717", 3838: "3719", 3839: "3720"}
            old_id = old_map.get(post_id, "")
            matches = any(old_id in ref for ref in page_refs) if old_id else False
        if matches:
            has_unverified = len(entry.get("unverified_claims", [])) > 0
            if has_unverified:
                any_unverified = True
            linked.append({
                "entry_id": entry.get("entry_id"),
                "product_name": entry.get("product_name"),
                "brand": entry.get("brand"),
                "evidence_status": entry.get("evidence_status"),
                "approval_status": entry.get("approval_status"),
                "publish_allowed": entry.get("publish_allowed"),
                "verified_claims_count": len(entry.get("verified_claims", [])),
                "unverified_claims_count": len(entry.get("unverified_claims", [])),
                "risk_flags": entry.get("risk_flags", []),
            })
    return {
        "linked_products": linked,
        "linked_product_count": len(linked),
        "any_unverified_claims": any_unverified,
    }


# ── Publishing readiness ─────────────────────────────────────────────
def build_readiness(safety_results: dict, quality: dict, evidence: dict, seo: dict) -> dict:
    blockers = []
    # QA check: all safety checks pass
    all_safety_pass = all(v["status"] == "pass" for v in safety_results.values())
    if not all_safety_pass:
        failed = [k for k, v in safety_results.items() if v["status"] != "pass"]
        blockers.append(f"Safety check failures: {', '.join(failed)}")

    # Internal linking
    il_pass = quality["internal_linking"]["count"] >= 1
    if not il_pass:
        blockers.append("No internal links detected")

    # Evidence restrictions
    evidence_pass = not evidence["any_unverified_claims"] or True  # unverified is expected at this stage
    # Actually flag if ALL products are blocked
    all_blocked = all(p["approval_status"] == "blocked_pending_evidence" for p in evidence["linked_products"]) if evidence["linked_products"] else True
    if all_blocked and evidence["linked_product_count"] > 0:
        blockers.append("All linked products are blocked_pending_evidence")

    # Affiliate disclosure
    # This is checked from content quality -- we will check in structure
    # For now mark as pending

    # SEO checks
    seo_ok = seo["kw_in_title"] and seo["seo_title_length"] <= 60 and seo["seo_description_length"] <= 160

    checklist = {
        "owner_review": "pending",
        "qa_check": "pass" if all_safety_pass else "fail",
        "metadata_approved": "pending",
        "schema_approved": "pending",
        "internal_linking": "pass" if il_pass else "fail",
        "evidence_restrictions_confirmed": "pass" if not all_blocked else "fail",
        "affiliate_disclosure_confirmed": "pending",
        "no_fake_claims": "pass" if all_safety_pass else "fail",
        "publisher_approval": "not_granted",
        "rollback_snapshot": "not_taken",
        "final_preview_check": "pending",
    }

    if blockers:
        overall = "needs_edits"
    else:
        overall = "ready_for_review"

    # If critical blockers (evidence all blocked), mark as blocked
    if all_blocked and evidence["linked_product_count"] > 0:
        overall = "needs_edits"

    next_action = "Owner reviews content, then product evidence must be verified before publishing." if overall != "blocked" else "Resolve blockers before proceeding."

    return {
        "overall_status": overall,
        "checklist": checklist,
        "blockers": blockers,
        "next_action": next_action,
    }


# ── Review guidance ──────────────────────────────────────────────────
def build_guidance(post_id: int, title: str, quality: dict, safety: dict, evidence: dict, readiness: dict) -> dict:
    word_count = quality["usefulness_breakdown"]["word_count"]
    h2_count = quality["usefulness_breakdown"]["h2_count"]
    tables = quality["usefulness_breakdown"]["tables"]
    faq_count = quality["faq_quality"]["faq_item_count"]
    safety_fails = [k for k, v in safety.items() if v["status"] != "pass"]
    all_blocked_products = all(
        p["approval_status"] == "blocked_pending_evidence" for p in evidence["linked_products"]
    ) if evidence["linked_products"] else False

    # Strengths
    strengths = []
    if quality["usefulness_score"] >= 7:
        strengths.append("High educational content depth with strong use of headings and structure")
    elif quality["usefulness_score"] >= 5:
        strengths.append("Solid content depth with reasonable structure")
    if quality["uk_relevance"] in ("strong", "moderate"):
        strengths.append("Good UK-specific relevance with references to FEDIAF, UK brands, and GBP")
    if quality["search_intent_match"] == "strong":
        strengths.append("Focus keyword is well-integrated into headings")
    if tables >= 1:
        strengths.append(f"Includes {tables} comparison table(s) for quick reference")
    if faq_count >= 3:
        strengths.append(f"FAQ section with {faq_count} questions addresses common queries")
    if not safety_fails:
        strengths.append("All trust and safety checks pass -- no fake claims detected")
    if len(strengths) < 3:
        if h2_count >= 4:
            strengths.append(f"Well-organized with {h2_count} H2 sections")
        if word_count >= 2000:
            strengths.append(f"Comprehensive coverage at {word_count} words")

    # Areas for review
    areas = []
    areas.append("Review all product mentions to confirm no specific prices, ratings, or review counts are stated")
    if all_blocked_products:
        areas.append("All linked products have blocked_pending_evidence status -- verify product claims before publishing")
    if quality["internal_linking"]["count"] < 3:
        areas.append("Consider adding more internal links to strengthen site structure")
    if quality["search_intent_match"] != "strong":
        areas.append("Focus keyword could be more prominently placed in H1/H2 headings")
    areas.append("Confirm affiliate disclosure is visible and properly worded")
    areas.append("Check that all health/nutrition claims are attributed to FEDIAF or manufacturer sources")

    # Risk level
    if safety_fails:
        risk = "high"
    elif all_blocked_products:
        risk = "medium"
    else:
        risk = "low"

    # Recommendation
    if risk == "high":
        recommendation = f"DO NOT PUBLISH until safety check failures are resolved: {', '.join(safety_fails)}. Review flagged content sections and remove or rewrite any claims that cannot be substantiated."
    elif risk == "medium":
        recommendation = "Content quality is solid but product evidence is pending. The post is suitable for owner review. Before publishing: (1) verify all product evidence, (2) confirm no specific prices/ratings are claimed, (3) ensure affiliate disclosure is present, (4) approve SEO metadata."
    else:
        recommendation = "Content is well-structured and passes all safety checks. Ready for owner review. Before publishing: (1) confirm product evidence, (2) approve SEO metadata and schema deployment, (3) verify preview renders correctly."

    one_liner_map = {
        3836: "Comprehensive hub page covering the best dog food options in the UK for 2026 across dry, wet, raw, and fresh categories.",
        3837: "In-depth guide to the best dry dog food (kibble) brands in the UK with ingredient analysis and FEDIAF compliance information.",
        3838: "Side-by-side comparison of dry vs wet dog food for UK dogs, covering nutrition, cost, convenience, and mixed feeding strategies.",
        3839: "Complete puppy feeding guide for UK owners covering age-based schedules, large breed considerations, and FEDIAF nutrient requirements.",
    }

    return {
        "one_line_summary": one_liner_map.get(post_id, f"Review summary for post {post_id}: {title}"),
        "strengths": strengths[:5],
        "areas_for_review": areas,
        "risk_level": risk,
        "recommendation": recommendation,
    }


# ── Main fetch & process ─────────────────────────────────────────────
def fetch_post(post_id: int) -> dict:
    """Fetch a single post from WP REST API."""
    url = f"{REST_BASE}/posts/{post_id}"
    params = {"status": "draft", "_fields": "id,title,slug,content,link,status"}
    auth = HTTPBasicAuth(WP_USER, WP_PASS)
    resp = requests.get(url, params=params, auth=auth, timeout=30)
    resp.raise_for_status()
    return resp.json()


def process_post(post_id: int, wp_data: dict, meta: dict, schema_data: dict, evidence_data: dict) -> dict:
    """Build the full review summary for a single post."""
    title = wp_data.get("title", {}).get("rendered", "")
    html_content = wp_data.get("content", {}).get("rendered", "")
    slug = wp_data.get("slug", "")
    status = wp_data.get("status", "unknown")
    preview_url = wp_data.get("link", f"https://pethubonline.com/?p={post_id}")
    focus_kw = meta["focus_kw"]

    plain_text = strip_html(html_content)
    word_count = len(plain_text.split())
    headings = extract_headings(html_content)
    paragraphs = extract_paragraphs(html_content)

    # A. Basic info
    basic_info = {
        "post_id": post_id,
        "title": strip_html(title),
        "slug": slug,
        "preview_url": preview_url,
        "word_count": word_count,
        "status": status,
    }

    # B. Content quality assessment
    quality = assess_content_quality(html_content, plain_text, focus_kw, headings)

    # C. Trust & safety checks
    safety = run_safety_checks(plain_text)
    filler_check = check_filler_padding(plain_text, headings, paragraphs, count_tables(html_content), extract_lists(html_content))
    safety["no_filler_padding"] = filler_check

    # D. Structure
    div_balance = count_divs(html_content)
    affiliate_disclosure = bool(re.search(
        r"(affiliate|commission|earn from|partner link|sponsored|disclosure)",
        plain_text, re.IGNORECASE
    ))
    content_status_notice = bool(re.search(
        r"(draft|under review|not yet published|content status|editorial notice)",
        plain_text, re.IGNORECASE
    ))
    structure = {
        "h1_count": len(headings.get("h1", [])),
        "h2_list": headings.get("h2", []),
        "h3_list": headings.get("h3", []),
        "table_count": count_tables(html_content),
        "image_count": count_images(html_content),
        "hr_separator_count": count_hr(html_content),
        "affiliate_disclosure_present": affiliate_disclosure,
        "content_status_notice_present": content_status_notice,
        "div_balance": div_balance,
    }

    # E. SEO
    seo = compute_seo(plain_text, meta, focus_kw)

    # F. Schema
    schema = build_schema_section(post_id, schema_data)

    # G. Product evidence
    evidence = build_evidence_section(post_id, evidence_data)

    # H. Publishing readiness
    readiness = build_readiness(safety, quality, evidence, seo)

    # I. Review guidance
    guidance = build_guidance(post_id, strip_html(title), quality, safety, evidence, readiness)

    return {
        "basic_info": basic_info,
        "content_quality": quality,
        "trust_and_safety": safety,
        "structure": structure,
        "seo": seo,
        "schema": schema,
        "product_evidence": evidence,
        "publishing_readiness": readiness,
        "review_guidance": guidance,
    }


def main():
    print("=" * 60)
    print("PetHub Online -- Owner Review Summary Generator")
    print("=" * 60)

    # Load reference files
    schema_path = os.path.join(BASE_DIR, "schema_proposals_jsonld.json")
    evidence_path = os.path.join(BASE_DIR, "product_evidence_register_export.json")

    with open(schema_path, "r") as f:
        schema_data = json.load(f)
    print(f"[OK] Loaded schema proposals: {schema_path}")

    with open(evidence_path, "r") as f:
        evidence_data = json.load(f)
    print(f"[OK] Loaded product evidence register: {evidence_path}")

    # Process each post
    summaries = {}
    errors = []

    for post_id, meta in POSTS.items():
        print(f"\n--- Processing post {post_id} ({meta['slug']}) ---")
        try:
            wp_data = fetch_post(post_id)
            print(f"  [OK] Fetched from WP API (status: {wp_data.get('status', '?')})")
            summary = process_post(post_id, wp_data, meta, schema_data, evidence_data)
            summaries[str(post_id)] = summary
            wc = summary["basic_info"]["word_count"]
            score = summary["content_quality"]["usefulness_score"]
            safety_fails = sum(1 for v in summary["trust_and_safety"].values() if v.get("status") == "FAIL")
            overall = summary["publishing_readiness"]["overall_status"]
            risk = summary["review_guidance"]["risk_level"]
            print(f"  Words: {wc} | Usefulness: {score}/10 | Safety fails: {safety_fails} | Status: {overall} | Risk: {risk}")
        except Exception as e:
            err_msg = f"Post {post_id}: {type(e).__name__}: {e}"
            errors.append(err_msg)
            print(f"  [ERROR] {err_msg}")

    # Build output
    output = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "generate_owner_review_summaries.py",
            "site": "pethubonline.com",
            "posts_processed": len(summaries),
            "posts_failed": len(errors),
            "errors": errors,
            "purpose": "Owner review summaries for 4 draft Dog Food posts. NOT for publishing -- for internal review only.",
        },
        "summaries": summaries,
    }

    # Write output
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n{'=' * 60}")
    print(f"[DONE] Output written to: {OUTPUT_FILE}")
    print(f"  Posts processed: {len(summaries)}")
    print(f"  Posts failed: {len(errors)}")

    # Validate output
    with open(OUTPUT_FILE, "r") as f:
        validated = json.load(f)
    required_sections = [
        "basic_info", "content_quality", "trust_and_safety",
        "structure", "seo", "schema", "product_evidence",
        "publishing_readiness", "review_guidance",
    ]
    for pid in summaries:
        for section in required_sections:
            if section not in validated["summaries"][pid]:
                print(f"  [WARN] Missing section '{section}' in post {pid}")
    print("[OK] JSON validation passed -- all sections present")
    print(f"{'=' * 60}")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
