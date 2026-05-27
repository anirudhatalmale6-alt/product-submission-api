#!/usr/bin/env python3
"""
Phase 10B - Dog Food Evidence Collection Pipeline
==================================================
Builds a structured evidence register for Dog Food products.
All products are BLOCKED pending evidence verification.
No recommendations, no affiliate links, no product schema until evidence is verified
AND owner approval is granted.

Generated for: pethubonline.com
Server: 167.99.198.145
"""

import csv
import os
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase10b")
CSV_PATH = os.path.join(OUTPUT_DIR, "Phase10B_Dog_Food_Evidence_Register.csv")
METHODOLOGY_PATH = os.path.join(OUTPUT_DIR, "Phase10B_Dog_Food_Evidence_Methodology.txt")

GENERATED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SOURCE_SERVER = "167.99.198.145"
GENERATED_BY = "Phase10B_Dog_Food_Evidence_Collection"
DATA_SOURCE_LABEL = "evidence_pipeline_candidates"
APPROVAL_STATUS = "evidence_collection_in_progress"
NEXT_ACTION_GLOBAL = "source_gathering"

# ── Candidate Products ─────────────────────────────────────────────────────
# Real, well-known UK dog food brands. No fabricated URLs or data.
CANDIDATES = [
    {
        "product_id": "P001",
        "brand_name": "Royal Canin",
        "product_name": "Royal Canin Medium Adult",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "chicken",
        "grain_status": "grain-inclusive",
        "price_range": "premium",
        "next_action": "Collect manufacturer nutritional data and FEDIAF compliance statement",
    },
    {
        "product_id": "P002",
        "brand_name": "Royal Canin",
        "product_name": "Royal Canin Maxi Puppy",
        "product_type": "dry",
        "target_audience": "puppy",
        "protein_source_primary": "chicken",
        "grain_status": "grain-inclusive",
        "price_range": "premium",
        "next_action": "Collect puppy-specific nutritional profile and growth-stage evidence",
    },
    {
        "product_id": "P003",
        "brand_name": "James Wellbeloved",
        "product_name": "James Wellbeloved Adult Lamb & Rice",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "lamb",
        "grain_status": "grain-inclusive",
        "price_range": "premium",
        "next_action": "Collect hypoallergenic claims evidence and ingredient sourcing data",
    },
    {
        "product_id": "P004",
        "brand_name": "James Wellbeloved",
        "product_name": "James Wellbeloved Senior Turkey & Rice",
        "product_type": "dry",
        "target_audience": "senior",
        "protein_source_primary": "chicken",
        "grain_status": "grain-inclusive",
        "price_range": "premium",
        "next_action": "Collect senior-specific joint support and digestibility evidence",
    },
    {
        "product_id": "P005",
        "brand_name": "Lily's Kitchen",
        "product_name": "Lily's Kitchen Proper Dog Food Chicken & Duck",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "chicken",
        "grain_status": "grain-free",
        "price_range": "super-premium",
        "next_action": "Collect natural ingredient claims evidence and freshness sourcing data",
    },
    {
        "product_id": "P006",
        "brand_name": "Lily's Kitchen",
        "product_name": "Lily's Kitchen Puppy Recipe",
        "product_type": "wet",
        "target_audience": "puppy",
        "protein_source_primary": "chicken",
        "grain_status": "grain-free",
        "price_range": "super-premium",
        "next_action": "Collect puppy nutritional adequacy statement and wet food preservation data",
    },
    {
        "product_id": "P007",
        "brand_name": "Burns Pet Nutrition",
        "product_name": "Burns Original Chicken & Brown Rice",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "chicken",
        "grain_status": "grain-inclusive",
        "price_range": "mid-range",
        "next_action": "Collect veterinary endorsement evidence and sensitive digestion claims data",
    },
    {
        "product_id": "P008",
        "brand_name": "Forthglade",
        "product_name": "Forthglade Complete Meal Adult Chicken",
        "product_type": "wet",
        "target_audience": "adult",
        "protein_source_primary": "chicken",
        "grain_status": "grain-free",
        "price_range": "mid-range",
        "next_action": "Collect complete meal nutritional profile and natural preservative evidence",
    },
    {
        "product_id": "P009",
        "brand_name": "Forthglade",
        "product_name": "Forthglade Complete Meal Senior Lamb",
        "product_type": "wet",
        "target_audience": "senior",
        "protein_source_primary": "lamb",
        "grain_status": "grain-free",
        "price_range": "mid-range",
        "next_action": "Collect senior formulation evidence and joint health ingredient data",
    },
    {
        "product_id": "P010",
        "brand_name": "Harringtons",
        "product_name": "Harringtons Complete Rich in Chicken",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "chicken",
        "grain_status": "grain-inclusive",
        "price_range": "budget",
        "next_action": "Collect value proposition evidence and nutritional adequacy at price point",
    },
    {
        "product_id": "P011",
        "brand_name": "Burgess",
        "product_name": "Burgess Sensitive Adult Lamb",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "lamb",
        "grain_status": "grain-inclusive",
        "price_range": "mid-range",
        "next_action": "Collect sensitive digestion claims evidence and allergen-free formulation data",
    },
    {
        "product_id": "P012",
        "brand_name": "Arden Grange",
        "product_name": "Arden Grange Adult Chicken & Rice",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "chicken",
        "grain_status": "grain-inclusive",
        "price_range": "premium",
        "next_action": "Collect fresh chicken content percentage evidence and UK manufacturing data",
    },
    {
        "product_id": "P013",
        "brand_name": "Canagan",
        "product_name": "Canagan Free-Run Chicken",
        "product_type": "dry",
        "target_audience": "all_ages",
        "protein_source_primary": "chicken",
        "grain_status": "grain-free",
        "price_range": "super-premium",
        "next_action": "Collect high-protein formulation evidence and grain-free safety data",
    },
    {
        "product_id": "P014",
        "brand_name": "Eden Holistic",
        "product_name": "Eden 80/20 Country Cuisine",
        "product_type": "dry",
        "target_audience": "all_ages",
        "protein_source_primary": "mixed",
        "grain_status": "grain-free",
        "price_range": "super-premium",
        "next_action": "Collect 80/20 meat-to-vegetable ratio evidence and multi-protein source data",
    },
    {
        "product_id": "P015",
        "brand_name": "Pooch & Mutt",
        "product_name": "Pooch & Mutt Health & Digestion",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "chicken",
        "grain_status": "grain-free",
        "price_range": "premium",
        "next_action": "Collect functional health claims evidence and prebiotic/probiotic data",
    },
    {
        "product_id": "P016",
        "brand_name": "Naturo",
        "product_name": "Naturo Adult Chicken with Rice",
        "product_type": "wet",
        "target_audience": "adult",
        "protein_source_primary": "chicken",
        "grain_status": "grain-inclusive",
        "price_range": "budget",
        "next_action": "Collect wet food nutritional analysis and preservative-free claims evidence",
    },
    {
        "product_id": "P017",
        "brand_name": "Symply",
        "product_name": "Symply Adult Lamb with Rice",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "lamb",
        "grain_status": "grain-inclusive",
        "price_range": "premium",
        "next_action": "Collect single-protein source evidence and UK-sourced ingredient data",
    },
    {
        "product_id": "P018",
        "brand_name": "Orijen",
        "product_name": "Orijen Original",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "mixed",
        "grain_status": "grain-free",
        "price_range": "super-premium",
        "next_action": "Collect biologically appropriate claims evidence and WholePrey ratio data",
    },
    {
        "product_id": "P019",
        "brand_name": "Acana",
        "product_name": "Acana Grass-Fed Lamb",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "lamb",
        "grain_status": "grain-free",
        "price_range": "super-premium",
        "next_action": "Collect grass-fed sourcing evidence and limited ingredient claims data",
    },
    {
        "product_id": "P020",
        "brand_name": "Harringtons",
        "product_name": "Harringtons Grain Free Turkey & Sweet Potato",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "chicken",
        "grain_status": "grain-free",
        "price_range": "budget",
        "next_action": "Collect grain-free budget formulation evidence and sweet potato nutritional data",
    },
    {
        "product_id": "P021",
        "brand_name": "Burns Pet Nutrition",
        "product_name": "Burns Free From Duck & Potato",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "mixed",
        "grain_status": "grain-free",
        "price_range": "mid-range",
        "next_action": "Collect hypoallergenic free-from claims evidence and novel protein data",
    },
    {
        "product_id": "P022",
        "brand_name": "Canagan",
        "product_name": "Canagan Scottish Salmon",
        "product_type": "dry",
        "target_audience": "all_ages",
        "protein_source_primary": "fish",
        "grain_status": "grain-free",
        "price_range": "super-premium",
        "next_action": "Collect omega-3 content evidence and Scottish sourcing verification data",
    },
    {
        "product_id": "P023",
        "brand_name": "Arden Grange",
        "product_name": "Arden Grange Sensitive Ocean White Fish & Potato",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "fish",
        "grain_status": "grain-free",
        "price_range": "premium",
        "next_action": "Collect sensitive skin/stomach claims evidence and fish sourcing data",
    },
    {
        "product_id": "P024",
        "brand_name": "Burgess",
        "product_name": "Burgess Puppy Rich in Chicken",
        "product_type": "dry",
        "target_audience": "puppy",
        "protein_source_primary": "chicken",
        "grain_status": "grain-inclusive",
        "price_range": "mid-range",
        "next_action": "Collect puppy growth formulation evidence and DHA content data",
    },
    {
        "product_id": "P025",
        "brand_name": "Pooch & Mutt",
        "product_name": "Pooch & Mutt Calm & Relaxed",
        "product_type": "dry",
        "target_audience": "adult",
        "protein_source_primary": "chicken",
        "grain_status": "grain-free",
        "price_range": "premium",
        "next_action": "Collect calming functional ingredient claims evidence (L-tryptophan, chamomile)",
    },
]

# ── CSV Column Headers ─────────────────────────────────────────────────────
CSV_COLUMNS = [
    "product_id",
    "brand_name",
    "product_name",
    "product_type",
    "target_audience",
    "evidence_status",
    "manufacturer_url",
    "fediaf_compliance",
    "uk_availability",
    "price_range",
    "protein_source_primary",
    "grain_status",
    "source_count",
    "freshness_check_date",
    "confidence_score",
    "evidence_blocked",
    "blocked_reason",
    "next_action",
]


def build_csv_row(candidate):
    """Build a full CSV row from a candidate dict, filling evidence fields with defaults."""
    return {
        "product_id": candidate["product_id"],
        "brand_name": candidate["brand_name"],
        "product_name": candidate["product_name"],
        "product_type": candidate["product_type"],
        "target_audience": candidate["target_audience"],
        "evidence_status": "candidate_identified",
        "manufacturer_url": "pending_collection",
        "fediaf_compliance": "pending_verification",
        "uk_availability": "available",
        "price_range": candidate["price_range"],
        "protein_source_primary": candidate["protein_source_primary"],
        "grain_status": candidate["grain_status"],
        "source_count": 0,
        "freshness_check_date": "",
        "confidence_score": 0.0,
        "evidence_blocked": "yes",
        "blocked_reason": "evidence_not_verified",
        "next_action": candidate["next_action"],
    }


def write_evidence_register():
    """Write the Dog Food Evidence Register CSV with header comments."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        # ── Header comments ────────────────────────────────────────────
        f.write(f"# generated_at: {GENERATED_AT}\n")
        f.write(f"# source_server: {SOURCE_SERVER}\n")
        f.write(f"# generated_by: {GENERATED_BY}\n")
        f.write(f"# data_source_label: {DATA_SOURCE_LABEL}\n")
        f.write(f"# approval_status: {APPROVAL_STATUS}\n")
        f.write(f"# next_action: {NEXT_ACTION_GLOBAL}\n")
        f.write(f"# total_candidates: {len(CANDIDATES)}\n")
        f.write(f"# evidence_blocked: ALL products blocked pending verification\n")
        f.write(f"# pipeline: not_started -> candidate_identified -> source_collected -> evidence_extracted -> evidence_verified -> owner_approved -> approved_for_draft_use -> approved_for_live_use\n")
        f.write("#\n")

        # ── CSV data ───────────────────────────────────────────────────
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        for candidate in CANDIDATES:
            row = build_csv_row(candidate)
            writer.writerow(row)

    return len(CANDIDATES)


def write_methodology():
    """Write the evidence collection methodology document."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    methodology = f"""Phase 10B - Dog Food Evidence Collection Methodology
=====================================================
Generated: {GENERATED_AT}
Server: {SOURCE_SERVER}
Generated by: {GENERATED_BY}

1. EVIDENCE FIELDS REQUIRED BEFORE A PRODUCT CAN BE RECOMMENDED
================================================================
Before any dog food product can move from "candidate" to "recommended" status,
ALL of the following evidence fields must be populated and verified:

  a) Manufacturer nutritional data
     - Complete ingredient list from official manufacturer source
     - Guaranteed analysis (crude protein, fat, fibre, ash, moisture)
     - Calorie content per serving
     - Feeding guidelines

  b) FEDIAF compliance status
     - Confirmation that the product meets FEDIAF (European Pet Food Industry
       Federation) nutritional guidelines for the declared life stage
     - Compliance must be verified against the most current FEDIAF guidelines

  c) UK market availability
     - Confirmed availability through at least one major UK retailer
     - Current pricing data (budget / mid-range / premium / super-premium)

  d) Independent testing or review data
     - At least one independent laboratory analysis OR
     - At least two independent expert reviews from recognised sources

  e) Ingredient sourcing transparency
     - Primary protein source identified and verified
     - Grain status confirmed (grain-free / grain-inclusive / both available)
     - Country of manufacture confirmed

  f) Safety and recall history
     - No active recalls in the UK or EU in the past 24 months
     - Any historical recalls documented with resolution status


2. ACCEPTABLE EVIDENCE SOURCES
===============================
Evidence is categorised into three tiers:

  Tier 1 - Primary Sources (highest weight):
    - Official manufacturer product pages and data sheets
    - FEDIAF nutritional guidelines and compliance databases
    - UK government / DEFRA regulatory data
    - Published peer-reviewed nutritional studies

  Tier 2 - Secondary Sources (supporting evidence):
    - Independent laboratory test results
    - Veterinary nutritionist reviews from recognised institutions
    - Which? or similar consumer testing organisations
    - Trading Standards compliance records

  Tier 3 - Tertiary Sources (contextual only, not sufficient alone):
    - Retailer product descriptions (Pets at Home, Zooplus, etc.)
    - Consumer review aggregates (only for market sentiment, not nutritional claims)
    - Industry press coverage

  NOT acceptable as evidence:
    - Affiliate marketing content
    - Unverified social media claims
    - Manufacturer advertising copy (claims require independent verification)
    - AI-generated nutritional data without source attribution


3. FRESHNESS TRACKING
======================
All evidence data is subject to freshness requirements:

  - Target refresh cycle: Every 90 days
  - freshness_check_date field records the last verification date
  - Products with evidence older than 90 days are automatically flagged for re-verification
  - Products with evidence older than 180 days are downgraded to "source_collected" status
    and must be re-verified before any recommendations can be made
  - Seasonal or reformulated products require immediate re-verification upon
    any manufacturer announcement of changes
  - The freshness_check_date is currently EMPTY for all candidates because
    no evidence has been collected yet


4. CONFIDENCE SCORING SYSTEM
==============================
Confidence scores range from 0.0 to 1.0:

  0.0  = No evidence collected
         Product is at "candidate_identified" or "not_started" stage.
         No data gathered. Cannot be referenced in any content.

  0.1-0.3 = Minimal evidence
         Some manufacturer data located but not verified.
         May have basic ingredient list but no independent confirmation.

  0.4-0.5 = Partial evidence
         Manufacturer data confirmed. Some independent sources collected.
         FEDIAF compliance not yet verified. Cannot be recommended.

  0.6-0.7 = Substantial evidence
         Manufacturer data + at least 2 independent sources.
         FEDIAF compliance status known. Minor gaps remain.

  0.8-0.9 = Strong evidence
         At least 3 independent sources confirmed.
         Manufacturer data verified against independent testing.
         FEDIAF compliance confirmed. Safety/recall check completed.

  1.0  = Fully verified
         All evidence fields populated and cross-referenced.
         3+ independent sources. FEDIAF confirmed. No active recalls.
         Freshness check within 90 days. Ready for owner review.

  Current state: ALL candidates are at 0.0 (no evidence collected yet).


5. WHAT "VERIFIED" MEANS
==========================
A product reaches "evidence_verified" status when ALL of the following are true:

  a) At least 3 independent sources have been collected and cross-referenced
  b) Manufacturer nutritional data has been confirmed against at least one
     independent source (laboratory test, regulatory filing, or expert review)
  c) FEDIAF compliance has been explicitly checked and documented
  d) No active recalls exist in the UK or EU
  e) The evidence is less than 90 days old (freshness requirement)
  f) All data has been reviewed for internal consistency
  g) Source URLs and references are documented and accessible

  "Verified" does NOT mean the product is recommended. It means the evidence
  base is complete enough for an owner to review and make an approval decision.


6. WHAT REMAINS BLOCKED
=========================
The following are ALL BLOCKED until evidence_status reaches "evidence_verified"
AND explicit owner approval is granted:

  BLOCKED - Affiliate links:
    No affiliate links, tracking codes, or monetisation for any dog food product.

  BLOCKED - Product recommendations:
    No "best of", "top picks", or recommendation language in any content.

  BLOCKED - Product Schema (structured data):
    No Product schema, Review schema, or AggregateRating schema for dog food.

  BLOCKED - Ratings and reviews:
    No star ratings, scoring, or ranking of dog food products.

  BLOCKED - Pricing data:
    No specific prices, price comparisons, or "best value" claims.
    Price ranges (budget/mid-range/premium/super-premium) are permitted as
    general market categorisation only.

  BLOCKED - Purchase CTAs:
    No "buy now", "shop here", or directional purchase language.

  UNBLOCKING REQUIREMENTS:
    1. evidence_status must reach "evidence_verified" for the specific product
    2. Owner must review and grant explicit approval (evidence_status -> "owner_approved")
    3. Content must be drafted and QA'd (evidence_status -> "approved_for_draft_use")
    4. Final owner sign-off for live publication (evidence_status -> "approved_for_live_use")


7. EVIDENCE STATUS PIPELINE
=============================
Each product progresses through a strict linear pipeline:

  not_started
    -> Product not yet identified as a candidate.
       No entry in the register.

  candidate_identified
    -> Product added to register with basic metadata (brand, type, audience).
       No evidence collected. Confidence: 0.0.
       THIS IS THE CURRENT STATE FOR ALL 25 CANDIDATES.

  source_collected
    -> Relevant sources identified and documented.
       Manufacturer URL found. Retailer listings located.
       Independent review sources identified. Confidence: 0.1-0.3.

  evidence_extracted
    -> Data extracted from sources into structured format.
       Nutritional data, ingredient lists, FEDIAF status documented.
       Confidence: 0.4-0.6.

  evidence_verified
    -> All evidence cross-referenced and validated.
       3+ independent sources confirmed. FEDIAF checked.
       No active recalls. Freshness < 90 days. Confidence: 0.8-1.0.

  owner_approved
    -> Site owner has reviewed the evidence pack for this product.
       Owner has granted explicit approval to proceed with content drafting.

  approved_for_draft_use
    -> Evidence-backed content has been drafted and passed internal QA.
       Ready for final owner sign-off before publication.

  approved_for_live_use
    -> Owner has given final approval for live publication.
       Product can now appear in live content with evidence citations.
       Affiliate links, schema, and recommendations may be enabled
       ONLY at this stage and ONLY with owner's explicit consent.


8. REGISTER STATISTICS (current state)
========================================
  Total candidates:          {len(CANDIDATES)}
  At candidate_identified:   {len(CANDIDATES)}
  At source_collected:       0
  At evidence_extracted:     0
  At evidence_verified:      0
  At owner_approved:         0
  At approved_for_draft:     0
  At approved_for_live:      0
  Average confidence score:  0.0
  Products ready for recs:   0
  Everything is BLOCKED.

=====================================================
END OF METHODOLOGY DOCUMENT
"""
    with open(METHODOLOGY_PATH, "w", encoding="utf-8") as f:
        f.write(methodology)


def print_summary(count):
    """Print execution summary."""
    print("=" * 70)
    print("Phase 10B - Dog Food Evidence Collection Pipeline")
    print("=" * 70)
    print()
    print(f"  Generated at:       {GENERATED_AT}")
    print(f"  Source server:       {SOURCE_SERVER}")
    print(f"  Generated by:       {GENERATED_BY}")
    print()
    print("  FILES CREATED:")
    print(f"    1. {CSV_PATH}")
    print(f"    2. {METHODOLOGY_PATH}")
    print()
    print(f"  CANDIDATE PRODUCTS:  {count}")
    print()

    # Brand breakdown
    brands = {}
    for c in CANDIDATES:
        brands.setdefault(c["brand_name"], 0)
        brands[c["brand_name"]] += 1
    print("  BRANDS INCLUDED:")
    for brand, n in sorted(brands.items()):
        print(f"    - {brand}: {n} product(s)")
    print()

    # Type breakdown
    types = {}
    for c in CANDIDATES:
        types.setdefault(c["product_type"], 0)
        types[c["product_type"]] += 1
    print("  PRODUCT TYPES:")
    for t, n in sorted(types.items()):
        print(f"    - {t}: {n}")
    print()

    # Audience breakdown
    audiences = {}
    for c in CANDIDATES:
        audiences.setdefault(c["target_audience"], 0)
        audiences[c["target_audience"]] += 1
    print("  TARGET AUDIENCES:")
    for a, n in sorted(audiences.items()):
        print(f"    - {a}: {n}")
    print()

    # Price breakdown
    prices = {}
    for c in CANDIDATES:
        prices.setdefault(c["price_range"], 0)
        prices[c["price_range"]] += 1
    print("  PRICE RANGES:")
    for p, n in sorted(prices.items()):
        print(f"    - {p}: {n}")
    print()

    print("  EVIDENCE STATUS:")
    print(f"    - All {count} products at: candidate_identified")
    print(f"    - All {count} products blocked: yes")
    print(f"    - All {count} products confidence: 0.0")
    print(f"    - All {count} products source_count: 0")
    print()
    print("  BLOCKED ITEMS:")
    print("    - Affiliate links:         BLOCKED")
    print("    - Product recommendations:  BLOCKED")
    print("    - Product Schema:           BLOCKED")
    print("    - Ratings and reviews:      BLOCKED")
    print("    - Pricing data:             BLOCKED")
    print("    - Purchase CTAs:            BLOCKED")
    print()
    print("  PIPELINE STATUS:")
    print("    not_started -> candidate_identified -> source_collected ->")
    print("    evidence_extracted -> evidence_verified -> owner_approved ->")
    print("    approved_for_draft_use -> approved_for_live_use")
    print()
    print(f"  NEXT ACTION: {NEXT_ACTION_GLOBAL}")
    print("    Begin collecting manufacturer URLs and FEDIAF compliance data")
    print("    for each candidate product.")
    print()
    print("=" * 70)
    print("Pipeline execution complete. All evidence collection is in progress.")
    print("NO recommendations will be made until evidence is verified AND")
    print("owner approval is granted.")
    print("=" * 70)


# ── Main ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    count = write_evidence_register()
    write_methodology()
    print_summary(count)
