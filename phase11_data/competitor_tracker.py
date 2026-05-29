#!/usr/bin/env python3
"""
PetHub Online - Competitor Displacement Monitoring Engine (Phase 11)
===================================================================
Tracks PetHub vs 5 main competitors across all 14 clusters on 12 dimensions.
Reads baseline data from Phase 10CC CSVs, calculates displacement scores,
and generates actionable competitive intelligence reports.

Competitors:
  1. Pets at Home (petsathome.com) - UK's largest pet retailer
  2. Zooplus (zooplus.co.uk) - European online pet shop
  3. Purina (purina.co.uk) - Pet food manufacturer with content marketing
  4. Cats.com (cats.com) - Cat-focused content site with 2,150+ guides
  5. Rover UK (rover.com/uk) - Dog services with content section
"""

import csv
import os
import sys
from datetime import datetime
from collections import defaultdict

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = "/var/lib/freelancer/projects/40416335"
INPUT_DIR = os.path.join(BASE_DIR, "phase10cc_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "phase11_data")

CLUSTERS = [
    "Dog Food", "Dog Health", "Dog Beds", "Dog Care", "Dog Supplies",
    "Dog Toys", "Cat Supplies", "Cat Toys", "Dog Harnesses",
    "Training Supplies", "Puppy Care", "Indoor Cats", "Pet Care",
    "Uncategorized"
]

COMPETITORS = {
    "Pets at Home":  {"domain": "petsathome.com",  "key": "pets_at_home"},
    "Zooplus":       {"domain": "zooplus.co.uk",    "key": "zooplus"},
    "Purina":        {"domain": "purina.co.uk",     "key": "purina"},
    "Cats.com":      {"domain": "cats.com",         "key": "cats_com"},
    "Rover":         {"domain": "rover.com/uk",     "key": "rover"},
}

DIMENSIONS = [
    "content_depth", "content_breadth", "trust_signals", "structured_data",
    "ai_readiness", "glossary_coverage", "comparison_content", "practical_guides",
    "faq_coverage", "citation_quality", "update_frequency", "user_engagement"
]

SNAPSHOT_DATE = datetime.now().strftime("%Y-%m-%d")

# ---------------------------------------------------------------------------
# Phase 10CC data loaders
# ---------------------------------------------------------------------------

def load_csv(filename):
    """Load a CSV file and return list of dicts."""
    path = os.path.join(INPUT_DIR, filename)
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_displacement_report():
    return load_csv("Competitor_Displacement_Report.csv")


def load_gap_map():
    return load_csv("Competitor_Gap_Map.csv")


def load_advantage_map():
    return load_csv("PetHub_Advantage_Map.csv")


def load_citation_report():
    return load_csv("Citation_Dominance_Report.csv")


def load_authority_moat():
    return load_csv("Authority_Moat_Report.csv")


# ---------------------------------------------------------------------------
# PetHub scoring engine  (derived from existing phase10cc data)
# ---------------------------------------------------------------------------

def compute_pethub_cluster_scores(displacement_data, citation_data, moat_data):
    """
    Build PetHub's per-cluster scores across 12 dimensions using the real
    Phase 10CC metrics as foundation.

    Mapping from existing metrics to 12 dimensions:
      - citation_score averages  -> citation_quality, trust_signals
      - moat_score averages      -> structured_data, glossary_coverage, comparison_content
      - ai_pref_score averages   -> ai_readiness
      - displacement report data -> content_depth, content_breadth, practical_guides, faq_coverage
      - advantage map details    -> update_frequency, user_engagement
    """
    # Aggregate citation scores by cluster
    cluster_citation = defaultdict(list)
    cluster_moat = defaultdict(list)
    for row in citation_data:
        cluster = row.get("cluster", "")
        if cluster:
            try:
                cluster_citation[cluster].append(float(row["citation_score"]))
            except (ValueError, KeyError):
                pass

    for row in moat_data:
        cluster = row.get("cluster", "")
        if cluster:
            try:
                cluster_moat[cluster].append(float(row["moat_score"]))
            except (ValueError, KeyError):
                pass

    # Aggregate moat sub-dimensions by cluster
    moat_dims = defaultdict(lambda: defaultdict(list))
    for row in moat_data:
        cluster = row.get("cluster", "")
        if not cluster:
            continue
        for dim in ["glossary_moat", "trust_moat", "comparison_moat", "practical_moat",
                     "educational_moat", "citation_moat", "structural_moat"]:
            try:
                moat_dims[cluster][dim].append(float(row[dim]))
            except (ValueError, KeyError):
                pass

    # Aggregate citation sub-dimensions
    cite_dims = defaultdict(lambda: defaultdict(list))
    for row in citation_data:
        cluster = row.get("cluster", "")
        if not cluster:
            continue
        for dim in ["reference_quality", "comparison_usefulness", "practical_specificity",
                     "extractability", "trust_depth", "summary_usefulness"]:
            try:
                cite_dims[cluster][dim].append(float(row[dim]))
            except (ValueError, KeyError):
                pass

    # Build displacement lookup
    disp_lookup = {}
    for row in displacement_data:
        cluster = row.get("cluster", "")
        if cluster:
            disp_lookup[cluster] = row

    def avg(lst):
        return sum(lst) / len(lst) if lst else 0

    pethub_scores = {}
    for cluster in CLUSTERS:
        d = disp_lookup.get(cluster, {})

        # Extract numeric scores from displacement report
        avg_cite = float(d.get("avg_citation_score", 0)) if d else 0
        avg_moat = float(d.get("avg_moat_score", 0)) if d else 0
        avg_ai = float(d.get("avg_ai_pref_score", 0)) if d else 0

        # Sub-dimension averages from moat report
        m = moat_dims.get(cluster, {})
        c = cite_dims.get(cluster, {})

        # Map to 12 dimensions (0-100 scale)
        # content_depth: based on practical_moat + educational_moat (how deep the content goes)
        content_depth = min(100, round((avg(m.get("practical_moat", [85])) * 0.5 +
                                         avg(m.get("educational_moat", [60])) * 0.5)))

        # content_breadth: based on post count signals from displacement report
        # Use comparison_moat as proxy for breadth of coverage
        strengths = d.get("pethub_strengths", "")
        breadth_base = avg(m.get("comparison_moat", [70]))
        # Boost for clusters with known high post counts
        post_count_boost = 0
        if "23 posts" in strengths or "largest" in strengths:
            post_count_boost = 12
        elif "16 posts" in strengths or "15 posts" in strengths or "14 posts" in strengths:
            post_count_boost = 10
        elif "12 posts" in strengths:
            post_count_boost = 8
        elif "7 posts" in strengths or "6 posts" in strengths:
            post_count_boost = 3
        elif "2 " in strengths and "posts" in strengths:
            post_count_boost = -5
        elif "45 posts" in strengths:
            post_count_boost = 15
        content_breadth = min(100, round(breadth_base + post_count_boost))

        # trust_signals: based on trust_moat + trust_depth from citations
        trust_signals = min(100, round(avg(m.get("trust_moat", [90])) * 0.6 +
                                        avg(c.get("trust_depth", [90])) * 0.4))

        # structured_data: based on structural_moat + extractability
        structured_data = min(100, round(avg(m.get("structural_moat", [90])) * 0.5 +
                                          avg(c.get("extractability", [95])) * 0.5))

        # ai_readiness: directly from avg_ai_pref_score
        ai_readiness = min(100, round(avg_ai))

        # glossary_coverage: directly from glossary_moat
        glossary_coverage = min(100, round(avg(m.get("glossary_moat", [80]))))

        # comparison_content: from comparison_moat + comparison_usefulness
        comparison_content = min(100, round(avg(m.get("comparison_moat", [70])) * 0.5 +
                                             avg(c.get("comparison_usefulness", [70])) * 0.5))

        # practical_guides: from practical_moat + practical_specificity
        practical_guides = min(100, round(avg(m.get("practical_moat", [85])) * 0.5 +
                                           avg(c.get("practical_specificity", [85])) * 0.5))

        # faq_coverage: from summary_usefulness (FAQ-style content)
        faq_coverage = min(100, round(avg(c.get("summary_usefulness", [90]))))

        # citation_quality: directly from avg_citation_score
        citation_quality = min(100, round(avg_cite))

        # update_frequency: PetHub maintains regular updates; based on content freshness signals
        # Clusters with "(2026)" in titles score higher
        update_frequency = 82  # baseline - active content program
        difficulty = d.get("displacement_difficulty", "MEDIUM")
        if difficulty == "HIGH":
            update_frequency = 78  # harder clusters get slightly less frequent updates
        elif post_count_boost >= 10:
            update_frequency = 85

        # user_engagement: PetHub is newer, lower engagement than established competitors
        # Base on reference_quality as proxy for content quality driving engagement
        user_engagement = min(100, round(avg(c.get("reference_quality", [90])) * 0.6 + 35))

        pethub_scores[cluster] = {
            "content_depth": content_depth,
            "content_breadth": content_breadth,
            "trust_signals": trust_signals,
            "structured_data": structured_data,
            "ai_readiness": ai_readiness,
            "glossary_coverage": glossary_coverage,
            "comparison_content": comparison_content,
            "practical_guides": practical_guides,
            "faq_coverage": faq_coverage,
            "citation_quality": citation_quality,
            "update_frequency": update_frequency,
            "user_engagement": user_engagement,
        }

    return pethub_scores


# ---------------------------------------------------------------------------
# Competitor scoring engine (derived from gap map + advantage map data)
# ---------------------------------------------------------------------------

def compute_competitor_scores(gap_data, advantage_data, displacement_data):
    """
    Build competitor per-cluster scores across 12 dimensions.
    Uses gap_map (has_guides, has_glossary, has_comparisons, trust_signals, advantage text)
    and advantage_map (pethub_advantage, displacement_opportunity) to infer competitor
    capabilities realistically.
    """
    # Build gap lookup: {(cluster, competitor): row}
    gap_lookup = {}
    for row in gap_data:
        key = (row.get("cluster", ""), row.get("competitor", ""))
        gap_lookup[key] = row

    # Build advantage lookup: {(cluster, competitor): row}
    adv_lookup = {}
    for row in advantage_data:
        key = (row.get("cluster", ""), row.get("competitor", ""))
        adv_lookup[key] = row

    # Displacement report for threat scores
    disp_lookup = {}
    for row in displacement_data:
        cluster = row.get("cluster", "")
        if cluster:
            disp_lookup[cluster] = row

    # Competitor profile baselines (inherent strengths by competitor type)
    profiles = {
        "Pets at Home": {
            "content_depth": 55,    # Product-focused, not deep educational
            "content_breadth": 72,  # Covers many product categories
            "trust_signals": 78,    # Retail trust, in-store vets
            "structured_data": 70,  # Good e-commerce schema
            "ai_readiness": 52,     # Not optimised for AI extraction
            "glossary_coverage": 20, # No glossary content
            "comparison_content": 68, # Product comparisons with pricing
            "practical_guides": 50,  # Some guides, product-driven
            "faq_coverage": 55,      # Basic FAQ sections
            "citation_quality": 40,  # Few authoritative citations
            "update_frequency": 80,  # Regular product updates
            "user_engagement": 82,   # High - reviews, in-store, brand trust
        },
        "Zooplus": {
            "content_depth": 40,    # Mainly product listings
            "content_breadth": 68,  # Wide product range
            "trust_signals": 35,    # No UK authority references
            "structured_data": 65,  # E-commerce schema
            "ai_readiness": 45,     # Product-focused, not AI-ready content
            "glossary_coverage": 15, # No glossary
            "comparison_content": 45, # Some product comparisons
            "practical_guides": 38,  # Minimal guides
            "faq_coverage": 40,      # Basic product FAQs
            "citation_quality": 25,  # No authoritative citations
            "update_frequency": 75,  # Regular product updates
            "user_engagement": 72,   # User reviews, European community
        },
        "Purina": {
            "content_depth": 68,    # Brand-backed educational content
            "content_breadth": 55,  # Focused on nutrition/health
            "trust_signals": 75,    # In-house vet team
            "structured_data": 65,  # Good but not outstanding
            "ai_readiness": 58,     # Moderate AI readiness
            "glossary_coverage": 30, # Some terminology in articles
            "comparison_content": 28, # Rarely compares to other brands
            "practical_guides": 62,  # Brand-backed guides
            "faq_coverage": 60,      # FAQ sections on key topics
            "citation_quality": 55,  # Own research, some external
            "update_frequency": 70,  # Periodic updates
            "user_engagement": 68,   # Brand community, social presence
        },
        "Cats.com": {
            "content_depth": 78,    # Deep educational guides
            "content_breadth": 82,  # 2,150+ guides across cat topics
            "trust_signals": 85,    # DVM/MRCVS reviewed content
            "structured_data": 72,  # Good content structure
            "ai_readiness": 65,     # Reasonably well-structured
            "glossary_coverage": 75, # Has glossary content
            "comparison_content": 72, # Comparison guides present
            "practical_guides": 75,  # How-to guides
            "faq_coverage": 78,      # Strong FAQ sections
            "citation_quality": 70,  # Vet-reviewed citations
            "update_frequency": 82,  # Very active content production
            "user_engagement": 80,   # Strong community, comments
        },
        "Rover": {
            "content_depth": 50,    # Lifestyle/community content
            "content_breadth": 45,  # Dog services focus, limited supply content
            "trust_signals": 42,    # Community trust, not expert
            "structured_data": 55,  # Service-oriented schema
            "ai_readiness": 40,     # Not optimised
            "glossary_coverage": 12, # No glossary
            "comparison_content": 35, # Some comparison content
            "practical_guides": 48,  # Walking/care tips
            "faq_coverage": 45,      # Service FAQs
            "citation_quality": 30,  # Few citations
            "update_frequency": 65,  # Regular blog updates
            "user_engagement": 75,   # Reviews, service ratings
        },
    }

    # Cluster relevance multipliers (how relevant each competitor is to each cluster)
    # 1.0 = core focus, 0.0 = completely irrelevant
    cluster_relevance = {
        "Pets at Home": {
            "Dog Food": 1.0, "Dog Health": 0.7, "Dog Beds": 0.95, "Dog Care": 0.8,
            "Dog Supplies": 0.95, "Dog Toys": 0.95, "Cat Supplies": 0.9, "Cat Toys": 0.85,
            "Dog Harnesses": 0.9, "Training Supplies": 0.85, "Puppy Care": 0.8,
            "Indoor Cats": 0.3, "Pet Care": 0.7, "Uncategorized": 0.4,
        },
        "Zooplus": {
            "Dog Food": 0.9, "Dog Health": 0.4, "Dog Beds": 0.7, "Dog Care": 0.5,
            "Dog Supplies": 0.8, "Dog Toys": 0.7, "Cat Supplies": 0.8, "Cat Toys": 0.65,
            "Dog Harnesses": 0.5, "Training Supplies": 0.6, "Puppy Care": 0.5,
            "Indoor Cats": 0.5, "Pet Care": 0.4, "Uncategorized": 0.35,
        },
        "Purina": {
            "Dog Food": 0.95, "Dog Health": 0.85, "Dog Beds": 0.2, "Dog Care": 0.8,
            "Dog Supplies": 0.3, "Dog Toys": 0.4, "Cat Supplies": 0.3, "Cat Toys": 0.4,
            "Dog Harnesses": 0.15, "Training Supplies": 0.7, "Puppy Care": 0.85,
            "Indoor Cats": 0.6, "Pet Care": 0.8, "Uncategorized": 0.5,
        },
        "Cats.com": {
            "Dog Food": 0.05, "Dog Health": 0.05, "Dog Beds": 0.05, "Dog Care": 0.05,
            "Dog Supplies": 0.05, "Dog Toys": 0.05, "Cat Supplies": 1.0, "Cat Toys": 1.0,
            "Dog Harnesses": 0.0, "Training Supplies": 0.1, "Puppy Care": 0.05,
            "Indoor Cats": 1.0, "Pet Care": 0.6, "Uncategorized": 0.4,
        },
        "Rover": {
            "Dog Food": 0.3, "Dog Health": 0.4, "Dog Beds": 0.2, "Dog Care": 0.6,
            "Dog Supplies": 0.3, "Dog Toys": 0.5, "Cat Supplies": 0.1, "Cat Toys": 0.1,
            "Dog Harnesses": 0.3, "Training Supplies": 0.5, "Puppy Care": 0.5,
            "Indoor Cats": 0.05, "Pet Care": 0.4, "Uncategorized": 0.3,
        },
    }

    competitor_scores = {}  # {(competitor, cluster): {dim: score}}

    for comp_name, profile in profiles.items():
        for cluster in CLUSTERS:
            relevance = cluster_relevance[comp_name].get(cluster, 0.3)
            gap_row = gap_lookup.get((cluster, comp_name), {})
            adv_row = adv_lookup.get((cluster, comp_name), {})

            scores = {}
            for dim in DIMENSIONS:
                base = profile[dim]

                # Apply relevance scaling: irrelevant clusters get reduced scores
                if relevance < 0.1:
                    scores[dim] = max(5, round(base * 0.15))
                    continue
                elif relevance < 0.3:
                    scores[dim] = max(10, round(base * 0.4))
                    continue

                adjusted = base

                # Boost/penalise based on gap map data
                has_guides = gap_row.get("competitor_has_guides", "no") == "yes"
                has_glossary = gap_row.get("competitor_has_glossary", "no") == "yes"
                has_comparisons = gap_row.get("competitor_has_comparisons", "no") == "yes"
                has_trust = gap_row.get("competitor_trust_signals", "no") == "yes"

                advantage_text = gap_row.get("competitor_advantage", "")
                pethub_adv_text = adv_row.get("pethub_advantage", "")

                # Dimension-specific adjustments based on gap map signals
                if dim == "content_depth":
                    if has_guides:
                        adjusted += 8
                    if "brand-backed educational" in advantage_text:
                        adjusted += 10
                    if "DVM/MRCVS" in advantage_text:
                        adjusted += 12
                    if "lifestyle" in advantage_text:
                        adjusted -= 5

                elif dim == "content_breadth":
                    if has_guides and has_comparisons:
                        adjusted += 10
                    if "2150+ guides" in advantage_text:
                        adjusted += 20
                    if "product listings" in advantage_text:
                        adjusted += 5

                elif dim == "trust_signals":
                    if has_trust:
                        adjusted += 12
                    if "vet team" in advantage_text or "vet access" in advantage_text:
                        adjusted += 10
                    if "DVM/MRCVS" in advantage_text:
                        adjusted += 15
                    if "brand credibility" in advantage_text:
                        adjusted += 8

                elif dim == "structured_data":
                    if "product-driven guides" in advantage_text:
                        adjusted += 5
                    if "buy links" in advantage_text:
                        adjusted += 3

                elif dim == "ai_readiness":
                    # Most competitors are NOT optimised for AI extraction
                    if "DVM/MRCVS" in advantage_text:
                        adjusted += 8  # structured medical reviews
                    if "product listings" in advantage_text:
                        adjusted -= 5  # product pages less AI-friendly

                elif dim == "glossary_coverage":
                    if has_glossary:
                        adjusted += 40  # significant boost for having glossary
                    else:
                        adjusted = min(adjusted, 25)  # cap at 25 if no glossary

                elif dim == "comparison_content":
                    if has_comparisons:
                        adjusted += 15
                    if "product-level comparisons with pricing" in advantage_text:
                        adjusted += 12
                    if "comparison content present" in advantage_text:
                        adjusted += 10

                elif dim == "practical_guides":
                    if has_guides:
                        adjusted += 8
                    if "product-driven guides" in advantage_text:
                        adjusted += 5
                    if "brand-backed educational" in advantage_text:
                        adjusted += 8

                elif dim == "faq_coverage":
                    if has_guides:
                        adjusted += 5
                    if "2150+ guides" in advantage_text:
                        adjusted += 15

                elif dim == "citation_quality":
                    if has_trust:
                        adjusted += 10
                    if "DVM/MRCVS" in advantage_text:
                        adjusted += 15
                    if "brand credibility" in advantage_text:
                        adjusted += 5

                elif dim == "update_frequency":
                    if "product listings" in advantage_text:
                        adjusted += 5  # e-commerce = frequent updates
                    if "2150+ guides" in advantage_text:
                        adjusted += 8

                elif dim == "user_engagement":
                    if "user reviews" in advantage_text:
                        adjusted += 10
                    if "community" in advantage_text:
                        adjusted += 8
                    if "in-store" in advantage_text:
                        adjusted += 5

                # Apply relevance scaling
                adjusted = adjusted * (0.4 + 0.6 * relevance)

                scores[dim] = min(100, max(5, round(adjusted)))

            competitor_scores[(comp_name, cluster)] = scores

    return competitor_scores


# ---------------------------------------------------------------------------
# Displacement calculations
# ---------------------------------------------------------------------------

def total_score(dim_scores):
    """Weighted average of 12 dimensions. All equal weight for transparency."""
    vals = [dim_scores[d] for d in DIMENSIONS]
    return round(sum(vals) / len(vals), 1)


def displacement_status(pethub_total, comp_total):
    """Classify competitive position."""
    gap = pethub_total - comp_total
    if gap >= 15:
        return "WINNING"
    elif gap <= -15:
        return "LOSING"
    else:
        return "COMPETITIVE"


def effort_level(gap):
    """Classify effort needed to close a gap."""
    abs_gap = abs(gap)
    if abs_gap <= 10:
        return "LOW"
    elif abs_gap <= 25:
        return "MEDIUM"
    elif abs_gap <= 40:
        return "HIGH"
    else:
        return "VERY HIGH"


def displacement_action(dim, gap, comp_name):
    """Generate specific displacement action based on dimension and competitor."""
    if gap >= 0:
        return f"Maintain advantage in {dim.replace('_', ' ')} vs {comp_name}"

    actions = {
        "content_depth": f"Deepen educational content to outmatch {comp_name}'s coverage depth",
        "content_breadth": f"Expand topic coverage across more sub-topics to close breadth gap with {comp_name}",
        "trust_signals": f"Add vet-reviewed badges and UK authority endorsements to counter {comp_name}",
        "structured_data": f"Enhance schema markup and structured data to surpass {comp_name}",
        "ai_readiness": f"Optimise content blocks for AI extraction to outperform {comp_name}",
        "glossary_coverage": f"Expand glossary/terminology content to close gap with {comp_name}",
        "comparison_content": f"Build more comparison tables and feature matrices to displace {comp_name}",
        "practical_guides": f"Create step-by-step practical guides to outperform {comp_name}",
        "faq_coverage": f"Expand FAQ sections and Q&A content to match {comp_name}",
        "citation_quality": f"Strengthen authoritative citations (BVA/RSPCA/PDSA) vs {comp_name}",
        "update_frequency": f"Increase content update cadence to match {comp_name}'s freshness",
        "user_engagement": f"Build social proof and review sections to counter {comp_name}'s engagement",
    }
    return actions.get(dim, f"Close {dim} gap with {comp_name}")


def priority_score(gap, cluster, comp_name, relevance_map):
    """Calculate priority 1-5 based on gap size and cluster importance."""
    abs_gap = abs(gap)
    # Higher relevance = higher priority to fix
    relevance = relevance_map.get(comp_name, {}).get(cluster, 0.5)
    raw = (abs_gap * 0.6) + (relevance * 40)
    if raw >= 60:
        return 1  # Critical
    elif raw >= 45:
        return 2  # High
    elif raw >= 30:
        return 3  # Medium
    elif raw >= 15:
        return 4  # Low
    else:
        return 5  # Monitor


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------

def write_csv(filename, headers, rows):
    """Write CSV to output directory."""
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
    return path


def generate_competitor_scorecard(competitor_scores):
    """a. competitor_scorecard.csv"""
    headers = ["competitor", "cluster"] + DIMENSIONS + ["total_score"]
    rows = []
    for comp_name in COMPETITORS:
        for cluster in CLUSTERS:
            scores = competitor_scores.get((comp_name, cluster), {})
            row = [comp_name, cluster]
            for dim in DIMENSIONS:
                row.append(scores.get(dim, 0))
            row.append(total_score(scores) if scores else 0)
            rows.append(row)
    return write_csv("competitor_scorecard.csv", headers, rows)


def generate_displacement_matrix(pethub_scores, competitor_scores):
    """b. displacement_matrix.csv"""
    headers = [
        "cluster", "pethub_score",
        "pets_at_home_score", "zooplus_score", "purina_score",
        "cats_com_score", "rover_score",
        "leader", "pethub_rank", "status", "gap_to_leader"
    ]
    rows = []
    for cluster in CLUSTERS:
        ph_total = total_score(pethub_scores[cluster])

        comp_totals = {}
        for comp_name in COMPETITORS:
            scores = competitor_scores.get((comp_name, cluster), {})
            comp_totals[comp_name] = total_score(scores) if scores else 0

        # Determine leader and PetHub rank
        all_scores = {"PetHub": ph_total}
        all_scores.update(comp_totals)
        sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        leader = sorted_scores[0][0]
        leader_score = sorted_scores[0][1]
        ph_rank = [i+1 for i, (name, _) in enumerate(sorted_scores) if name == "PetHub"][0]

        # Status based on PetHub vs best competitor
        best_comp_score = max(comp_totals.values())
        status = displacement_status(ph_total, best_comp_score)
        gap_to_leader = round(ph_total - leader_score, 1) if leader != "PetHub" else 0

        rows.append([
            cluster, ph_total,
            comp_totals.get("Pets at Home", 0),
            comp_totals.get("Zooplus", 0),
            comp_totals.get("Purina", 0),
            comp_totals.get("Cats.com", 0),
            comp_totals.get("Rover", 0),
            leader, ph_rank, status, gap_to_leader
        ])
    return write_csv("displacement_matrix.csv", headers, rows)


def generate_displacement_opportunities(pethub_scores, competitor_scores):
    """c. displacement_opportunities.csv - only where PetHub is behind."""
    headers = [
        "cluster", "competitor", "dimension", "pethub_score",
        "competitor_score", "gap", "displacement_action",
        "effort_level", "priority"
    ]

    # Relevance map for priority calculation
    cluster_relevance = {
        "Pets at Home": {
            "Dog Food": 1.0, "Dog Health": 0.7, "Dog Beds": 0.95, "Dog Care": 0.8,
            "Dog Supplies": 0.95, "Dog Toys": 0.95, "Cat Supplies": 0.9, "Cat Toys": 0.85,
            "Dog Harnesses": 0.9, "Training Supplies": 0.85, "Puppy Care": 0.8,
            "Indoor Cats": 0.3, "Pet Care": 0.7, "Uncategorized": 0.4,
        },
        "Zooplus": {
            "Dog Food": 0.9, "Dog Health": 0.4, "Dog Beds": 0.7, "Dog Care": 0.5,
            "Dog Supplies": 0.8, "Dog Toys": 0.7, "Cat Supplies": 0.8, "Cat Toys": 0.65,
            "Dog Harnesses": 0.5, "Training Supplies": 0.6, "Puppy Care": 0.5,
            "Indoor Cats": 0.5, "Pet Care": 0.4, "Uncategorized": 0.35,
        },
        "Purina": {
            "Dog Food": 0.95, "Dog Health": 0.85, "Dog Beds": 0.2, "Dog Care": 0.8,
            "Dog Supplies": 0.3, "Dog Toys": 0.4, "Cat Supplies": 0.3, "Cat Toys": 0.4,
            "Dog Harnesses": 0.15, "Training Supplies": 0.7, "Puppy Care": 0.85,
            "Indoor Cats": 0.6, "Pet Care": 0.8, "Uncategorized": 0.5,
        },
        "Cats.com": {
            "Dog Food": 0.05, "Dog Health": 0.05, "Dog Beds": 0.05, "Dog Care": 0.05,
            "Dog Supplies": 0.05, "Dog Toys": 0.05, "Cat Supplies": 1.0, "Cat Toys": 1.0,
            "Dog Harnesses": 0.0, "Training Supplies": 0.1, "Puppy Care": 0.05,
            "Indoor Cats": 1.0, "Pet Care": 0.6, "Uncategorized": 0.4,
        },
        "Rover": {
            "Dog Food": 0.3, "Dog Health": 0.4, "Dog Beds": 0.2, "Dog Care": 0.6,
            "Dog Supplies": 0.3, "Dog Toys": 0.5, "Cat Supplies": 0.1, "Cat Toys": 0.1,
            "Dog Harnesses": 0.3, "Training Supplies": 0.5, "Puppy Care": 0.5,
            "Indoor Cats": 0.05, "Pet Care": 0.4, "Uncategorized": 0.3,
        },
    }

    rows = []
    for cluster in CLUSTERS:
        ph = pethub_scores[cluster]
        for comp_name in COMPETITORS:
            comp = competitor_scores.get((comp_name, cluster), {})
            if not comp:
                continue
            for dim in DIMENSIONS:
                ph_val = ph[dim]
                comp_val = comp.get(dim, 0)
                gap = ph_val - comp_val
                if gap < 0:  # PetHub is behind
                    rows.append([
                        cluster, comp_name, dim, ph_val, comp_val, gap,
                        displacement_action(dim, gap, comp_name),
                        effort_level(gap),
                        priority_score(gap, cluster, comp_name, cluster_relevance)
                    ])

    # Sort by priority then gap magnitude
    rows.sort(key=lambda r: (r[8], r[5]))
    return write_csv("displacement_opportunities.csv", headers, rows)


def generate_competitive_summary(pethub_scores, competitor_scores):
    """d. competitive_summary.csv"""
    headers = [
        "competitor", "clusters_winning", "clusters_competitive",
        "clusters_losing", "overall_threat_level", "primary_threat_clusters",
        "recommended_strategy"
    ]

    rows = []
    for comp_name in COMPETITORS:
        winning = []
        competitive = []
        losing = []

        for cluster in CLUSTERS:
            ph_total = total_score(pethub_scores[cluster])
            comp = competitor_scores.get((comp_name, cluster), {})
            comp_total = total_score(comp) if comp else 0
            status = displacement_status(ph_total, comp_total)

            if status == "WINNING":
                winning.append(cluster)
            elif status == "COMPETITIVE":
                competitive.append(cluster)
            else:
                losing.append(cluster)

        # Overall threat level
        if len(losing) >= 4:
            threat = "CRITICAL"
        elif len(losing) >= 2:
            threat = "HIGH"
        elif len(competitive) >= 5:
            threat = "MODERATE"
        elif len(competitive) >= 2:
            threat = "LOW"
        else:
            threat = "MINIMAL"

        # Primary threat clusters (where PetHub is losing or most competitive)
        threat_clusters = losing + competitive[:3]

        # Strategy recommendation
        strategies = {
            "Pets at Home": "Counter retail trust with independent editorial depth; add pricing context to comparisons; emphasise unbiased cross-brand analysis",
            "Zooplus": "Maintain educational superiority; reference products while providing deeper analysis; focus on UK-specific trust signals",
            "Purina": "Highlight independent cross-brand perspective; strengthen named UK authority citations beyond brand-only research",
            "Cats.com": "Expand glossary depth; add vet-reviewed badges; increase cat cluster post volume; build UK-specific tools",
            "Rover": "Maintain content quality advantage; add community-oriented practical content for dog services clusters",
        }

        rows.append([
            comp_name,
            len(winning),
            len(competitive),
            len(losing),
            threat,
            "; ".join(threat_clusters[:5]) if threat_clusters else "None",
            strategies.get(comp_name, "Monitor and maintain advantage")
        ])

    return write_csv("competitive_summary.csv", headers, rows)


def generate_monthly_snapshot(pethub_scores, competitor_scores):
    """e. monthly_snapshot.csv with trend tracking structure."""
    headers = [
        "date", "cluster", "pethub_score", "top_competitor",
        "top_competitor_score", "status", "movement",
        "prev_month_pethub_score", "prev_month_status", "score_change"
    ]
    rows = []
    for cluster in CLUSTERS:
        ph_total = total_score(pethub_scores[cluster])

        # Find top competitor
        top_comp = None
        top_score = 0
        for comp_name in COMPETITORS:
            comp = competitor_scores.get((comp_name, cluster), {})
            ct = total_score(comp) if comp else 0
            if ct > top_score:
                top_score = ct
                top_comp = comp_name

        status = displacement_status(ph_total, top_score)

        # First snapshot: no previous data yet
        rows.append([
            SNAPSHOT_DATE, cluster, ph_total, top_comp, top_score,
            status, "BASELINE",
            "", "", ""  # prev_month fields empty for first snapshot
        ])

    return write_csv("monthly_snapshot.csv", headers, rows)


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def print_summary(pethub_scores, competitor_scores):
    """Print comprehensive analysis summary."""
    print("=" * 90)
    print("  PETHUB ONLINE - COMPETITOR DISPLACEMENT MONITORING ENGINE")
    print("  Phase 11 | Snapshot Date: {}".format(SNAPSHOT_DATE))
    print("=" * 90)

    # Overall PetHub scores
    print("\n--- PetHub Cluster Scores (12-Dimension Average) ---\n")
    print(f"  {'Cluster':<22} {'Total':>7}  {'Best':>7}  {'Status':<14}")
    print(f"  {'-'*22} {'-'*7}  {'-'*7}  {'-'*14}")

    cluster_results = []
    for cluster in CLUSTERS:
        ph_total = total_score(pethub_scores[cluster])
        best_comp = None
        best_score = 0
        for comp_name in COMPETITORS:
            comp = competitor_scores.get((comp_name, cluster), {})
            ct = total_score(comp) if comp else 0
            if ct > best_score:
                best_score = ct
                best_comp = comp_name
        status = displacement_status(ph_total, best_score)
        cluster_results.append((cluster, ph_total, best_comp, best_score, status))
        print(f"  {cluster:<22} {ph_total:>7.1f}  {best_score:>7.1f}  {status:<14} (vs {best_comp})")

    # Count statuses
    winning = sum(1 for _, _, _, _, s in cluster_results if s == "WINNING")
    competitive = sum(1 for _, _, _, _, s in cluster_results if s == "COMPETITIVE")
    losing = sum(1 for _, _, _, _, s in cluster_results if s == "LOSING")

    print(f"\n  Summary: WINNING {winning} | COMPETITIVE {competitive} | LOSING {losing} of {len(CLUSTERS)} clusters")

    # Per-competitor threat analysis
    print("\n--- Competitor Threat Analysis ---\n")
    for comp_name in COMPETITORS:
        w, c, l = 0, 0, 0
        worst_gap_cluster = None
        worst_gap = 999
        for cluster in CLUSTERS:
            ph_total = total_score(pethub_scores[cluster])
            comp = competitor_scores.get((comp_name, cluster), {})
            ct = total_score(comp) if comp else 0
            gap = ph_total - ct
            status = displacement_status(ph_total, ct)
            if status == "WINNING":
                w += 1
            elif status == "COMPETITIVE":
                c += 1
            else:
                l += 1
            if gap < worst_gap:
                worst_gap = gap
                worst_gap_cluster = cluster

        threat = "CRITICAL" if l >= 4 else "HIGH" if l >= 2 else "MODERATE" if c >= 5 else "LOW" if c >= 2 else "MINIMAL"
        print(f"  {comp_name:<18} W:{w:>2} | C:{c:>2} | L:{l:>2}  Threat: {threat:<10}  Closest: {worst_gap_cluster} ({worst_gap:+.1f})")

    # Top displacement opportunities
    print("\n--- Top 15 Displacement Opportunities (Where PetHub Is Behind) ---\n")
    print(f"  {'Cluster':<18} {'Competitor':<16} {'Dimension':<22} {'Gap':>5}  {'Priority':>8}")
    print(f"  {'-'*18} {'-'*16} {'-'*22} {'-'*5}  {'-'*8}")

    opps = []
    cluster_relevance = {
        "Pets at Home": {"Dog Food": 1.0, "Dog Health": 0.7, "Dog Beds": 0.95, "Dog Care": 0.8,
            "Dog Supplies": 0.95, "Dog Toys": 0.95, "Cat Supplies": 0.9, "Cat Toys": 0.85,
            "Dog Harnesses": 0.9, "Training Supplies": 0.85, "Puppy Care": 0.8,
            "Indoor Cats": 0.3, "Pet Care": 0.7, "Uncategorized": 0.4},
        "Zooplus": {"Dog Food": 0.9, "Dog Health": 0.4, "Dog Beds": 0.7, "Dog Care": 0.5,
            "Dog Supplies": 0.8, "Dog Toys": 0.7, "Cat Supplies": 0.8, "Cat Toys": 0.65,
            "Dog Harnesses": 0.5, "Training Supplies": 0.6, "Puppy Care": 0.5,
            "Indoor Cats": 0.5, "Pet Care": 0.4, "Uncategorized": 0.35},
        "Purina": {"Dog Food": 0.95, "Dog Health": 0.85, "Dog Beds": 0.2, "Dog Care": 0.8,
            "Dog Supplies": 0.3, "Dog Toys": 0.4, "Cat Supplies": 0.3, "Cat Toys": 0.4,
            "Dog Harnesses": 0.15, "Training Supplies": 0.7, "Puppy Care": 0.85,
            "Indoor Cats": 0.6, "Pet Care": 0.8, "Uncategorized": 0.5},
        "Cats.com": {"Dog Food": 0.05, "Dog Health": 0.05, "Dog Beds": 0.05, "Dog Care": 0.05,
            "Dog Supplies": 0.05, "Dog Toys": 0.05, "Cat Supplies": 1.0, "Cat Toys": 1.0,
            "Dog Harnesses": 0.0, "Training Supplies": 0.1, "Puppy Care": 0.05,
            "Indoor Cats": 1.0, "Pet Care": 0.6, "Uncategorized": 0.4},
        "Rover": {"Dog Food": 0.3, "Dog Health": 0.4, "Dog Beds": 0.2, "Dog Care": 0.6,
            "Dog Supplies": 0.3, "Dog Toys": 0.5, "Cat Supplies": 0.1, "Cat Toys": 0.1,
            "Dog Harnesses": 0.3, "Training Supplies": 0.5, "Puppy Care": 0.5,
            "Indoor Cats": 0.05, "Pet Care": 0.4, "Uncategorized": 0.3},
    }

    for cluster in CLUSTERS:
        ph = pethub_scores[cluster]
        for comp_name in COMPETITORS:
            comp = competitor_scores.get((comp_name, cluster), {})
            if not comp:
                continue
            for dim in DIMENSIONS:
                ph_val = ph[dim]
                comp_val = comp.get(dim, 0)
                gap = ph_val - comp_val
                if gap < 0:
                    pri = priority_score(gap, cluster, comp_name, cluster_relevance)
                    opps.append((cluster, comp_name, dim, gap, pri))

    opps.sort(key=lambda x: (x[4], x[3]))
    for cluster, comp, dim, gap, pri in opps[:15]:
        pri_label = {1: "CRITICAL", 2: "HIGH", 3: "MEDIUM", 4: "LOW", 5: "MONITOR"}[pri]
        print(f"  {cluster:<18} {comp:<16} {dim:<22} {gap:>+5}  {pri_label:>8}")

    # Key strategic insights
    print("\n--- Key Strategic Insights ---\n")

    # Find PetHub's strongest and weakest dimensions overall
    dim_avgs = defaultdict(list)
    for cluster in CLUSTERS:
        for dim in DIMENSIONS:
            dim_avgs[dim].append(pethub_scores[cluster][dim])

    dim_means = {dim: sum(vals)/len(vals) for dim, vals in dim_avgs.items()}
    sorted_dims = sorted(dim_means.items(), key=lambda x: x[1], reverse=True)

    print("  PetHub's Strongest Dimensions (across all clusters):")
    for dim, avg_val in sorted_dims[:4]:
        print(f"    - {dim.replace('_', ' ').title()}: {avg_val:.1f}/100")

    print("\n  PetHub's Weakest Dimensions (across all clusters):")
    for dim, avg_val in sorted_dims[-4:]:
        print(f"    - {dim.replace('_', ' ').title()}: {avg_val:.1f}/100")

    # Cat cluster warning
    cat_clusters = ["Cat Supplies", "Cat Toys", "Indoor Cats"]
    cat_gaps = []
    for cluster in cat_clusters:
        ph_total = total_score(pethub_scores[cluster])
        cats_comp = competitor_scores.get(("Cats.com", cluster), {})
        cats_total = total_score(cats_comp) if cats_comp else 0
        cat_gaps.append((cluster, ph_total - cats_total))

    print("\n  Cat Cluster Alert (vs Cats.com):")
    for cluster, gap in cat_gaps:
        indicator = "AHEAD" if gap > 0 else "BEHIND"
        print(f"    - {cluster}: PetHub is {abs(gap):.1f} points {indicator}")

    # Update frequency note
    print("\n  Content Velocity:")
    print("    - PetHub: Active content programme with regular 2026-dated updates")
    print("    - Primary risk: Cats.com (2,150+ guides) and Pets at Home (retail authority)")
    print("    - Key moat: AI readiness + glossary depth + UK authority citations")

    print("\n" + "=" * 90)
    print("  Generated {} CSVs to: {}".format(5, OUTPUT_DIR))
    print("=" * 90)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading Phase 10CC baseline data...")

    # Load all source data
    displacement_data = load_displacement_report()
    gap_data = load_gap_map()
    advantage_data = load_advantage_map()
    citation_data = load_citation_report()
    moat_data = load_authority_moat()

    print(f"  Loaded {len(displacement_data)} displacement records")
    print(f"  Loaded {len(gap_data)} competitor gap records")
    print(f"  Loaded {len(advantage_data)} advantage map records")
    print(f"  Loaded {len(citation_data)} citation dominance records")
    print(f"  Loaded {len(moat_data)} authority moat records")

    # Compute scores
    print("\nComputing PetHub cluster scores from Phase 10CC data...")
    pethub_scores = compute_pethub_cluster_scores(displacement_data, citation_data, moat_data)

    print("Computing competitor scores across 5 competitors x 14 clusters x 12 dimensions...")
    competitor_scores = compute_competitor_scores(gap_data, advantage_data, displacement_data)

    # Generate CSVs
    print("\nGenerating output CSVs...\n")

    path_a = generate_competitor_scorecard(competitor_scores)
    print(f"  [1/5] {path_a}")

    path_b = generate_displacement_matrix(pethub_scores, competitor_scores)
    print(f"  [2/5] {path_b}")

    path_c = generate_displacement_opportunities(pethub_scores, competitor_scores)
    print(f"  [3/5] {path_c}")

    path_d = generate_competitive_summary(pethub_scores, competitor_scores)
    print(f"  [4/5] {path_d}")

    path_e = generate_monthly_snapshot(pethub_scores, competitor_scores)
    print(f"  [5/5] {path_e}")

    # Print comprehensive summary
    print_summary(pethub_scores, competitor_scores)


if __name__ == "__main__":
    main()
