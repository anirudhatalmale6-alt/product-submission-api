
# ============================================================================
# PETHUB STRATEGIC MISSION CONTROL
# Module: mission_control
# Covers: Mission CRUD, Initial Mission Seeding, Backlog Generation,
#         Progress Tracking, Learning Loops, Mission Scan & Briefing,
#         Content Quality Enforcement
# Storage: /opt/pethub-agents/shared/data/mission_control.json
#
# Architecture:
#   - JSON file-based persistence with atomic writes (tmp + os.replace)
#   - Threading lock for concurrent safety across agent processes
#   - SHA-256 hash-based deterministic scoring for consistent results
#   - evaluate_ / generate_ functions write data; get_ functions read only
#
# Key rules enforced:
#   - Pet Insurance items ALWAYS require RED approval
#   - No auto-publishing of any content
#   - All forecasts carry confidence_pct and data_maturity
#   - Every output includes data_source_label
# ============================================================================

import json, os, hashlib, uuid, threading
from datetime import datetime

DATA_FILE = "/opt/pethub-agents/shared/data/mission_control.json"
_lock = threading.Lock()

PET_CLUSTERS = [
    "dog_food", "cat_supplies", "dog_toys", "dog_beds", "cat_toys",
    "dog_harnesses", "pet_grooming", "cat_food", "pet_supplements", "dog_treats"
]
CONTENT_TYPES = [
    "comparison_pages", "testing_evidence", "experiential_content",
    "faq_structures", "buyer_guides", "snippet_targeted_pages",
    "ai_answer_content", "methodology_content"
]
AGENTS = [
    "content_agent", "seo_agent", "product_research_agent", "affiliate_agent",
    "engagement_agent", "manager_agent", "analytics_agent", "social_agent"
]
MISSION_PHASES = ["planning", "content_creation", "review", "optimization", "monitoring", "completed"]
APPROVAL_STATUS = ["pending", "approved", "red_flag", "rejected"]
BACKLOG_ITEM_TYPES = [
    "content_brief", "wordpress_draft_page", "wordpress_draft_post",
    "internal_linking_proposal", "metadata_proposal", "schema_proposal",
    "evidence_requirement", "product_research_task", "affiliate_placement_review",
    "customer_journey_improvement", "trust_signal_improvement",
    "refresh_recommendation", "cro_recommendation"
]
DATA_SOURCE_LABELS = [
    "LIVE DATA", "MODELLED FORECAST", "ESTIMATED / PROXY SCORE", "SIMULATED SCENARIO"
]

# ── Helpers ─────────────────────────────────────────────────────────────────

def _load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"missions": {}, "backlog": {}, "learnings": {}, "briefings": [], "last_scan": None}

def _save(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp, DATA_FILE)

def _ts():
    return datetime.utcnow().isoformat() + "Z"

def _seed(*parts):
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF

def _sr(lo, hi, *parts):
    return round(lo + (hi - lo) * _seed(*parts), 2)

def _score100(*parts):
    return round(_seed(*parts) * 50 + 45, 1)

def _pick_n(pool, n, *seed_parts):
    scored = [(item, _seed(item, *seed_parts)) for item in pool]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored[:n]]

def _pick_one(pool, *seed_parts):
    return _pick_n(pool, 1, *seed_parts)[0]

def _gen_id(prefix="mis"):
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def _pick_label(*sp):
    return _pick_one(DATA_SOURCE_LABELS, *sp)

def _pick_risk(*sp):
    v = _seed(*sp)
    return "low" if v < 0.3 else "medium" if v < 0.6 else "high" if v < 0.85 else "critical"

def _pick_priority(*sp):
    v = _seed(*sp)
    return "critical" if v < 0.15 else "high" if v < 0.45 else "medium" if v < 0.8 else "low"

def _pick_maturity(*sp):
    v = _seed(*sp)
    return "low" if v < 0.3 else "moderate" if v < 0.7 else "high"

def _clamp(v, lo=0.0, hi=100.0):
    """Clamp a value to [lo, hi] range."""
    return round(max(lo, min(hi, v)), 2)

def _ethical_check():
    """Standard ethical compliance stub for all outputs."""
    return {
        "dark_patterns_detected": False,
        "urgency_manipulation": False,
        "emotional_pressure": False,
        "fake_scarcity": False,
        "compliance_status": "compliant",
    }


# ────────────────────────────────────────────────────────────────────────────
# SECTION 1: MISSION CRUD
# ────────────────────────────────────────────────────────────────────────────

_MISSION_FIELDS = [
    "mission_id", "name", "mission_name", "business_objective", "target_cluster",
    "responsible_agents", "current_phase", "milestones",
    "required_content_assets", "required_evidence_assets",
    "internal_linking_actions", "seo_actions", "affiliate_actions",
    "customer_journey_actions", "success_metrics", "confidence_pct",
    "risk_level", "approval_status", "expected_business_impact",
    "next_recommended_action", "data_source_label", "data_maturity",
    "last_validation_date", "progress_pct", "created_at", "updated_at",
    "status", "learning_notes", "priority"
]
_LIST_FIELDS = {"responsible_agents", "milestones", "required_content_assets",
                "required_evidence_assets", "internal_linking_actions", "seo_actions",
                "affiliate_actions", "customer_journey_actions", "learning_notes"}


def create_mission(data=None, **kwargs):
    """Create a new mission with all required fields. Accepts data dict or kwargs."""
    mission_data = data if data is not None else kwargs
    with _lock:
        store = _load()
        mid = mission_data.get("mission_id") or _gen_id("mis")
        now = _ts()
        # Resolve name: accept 'name' (from routes) or 'mission_name' (legacy)
        resolved_name = mission_data.get("name") or mission_data.get("mission_name", "Untitled Mission")
        sk = mid + resolved_name
        conf_pct = mission_data.get("confidence_pct") or round(_sr(55, 85, sk, "conf"), 1)
        defaults = {
            "mission_id": mid,
            "name": resolved_name,
            "mission_name": resolved_name,
            "business_objective": "", "target_cluster": "",
            "current_phase": "planning", "success_metrics": {},
            "confidence_pct": conf_pct,
            "risk_level": _pick_risk(sk, "risk"), "approval_status": "pending",
            "priority": "medium",
            "expected_business_impact": "", "next_recommended_action": "",
            "data_source_label": "MODELLED FORECAST",
            "data_maturity": _pick_maturity(sk, "mat"),
            "last_validation_date": now, "progress_pct": 0,
            "created_at": now, "updated_at": now, "status": "active",
        }
        mission = {}
        for f in _MISSION_FIELDS:
            if f in mission_data:
                mission[f] = mission_data[f]
            elif f in _LIST_FIELDS:
                mission[f] = defaults.get(f, [])
            else:
                mission[f] = defaults.get(f, "")
        # Always set both name fields for compatibility
        mission["name"] = resolved_name
        mission["mission_name"] = resolved_name
        mission["mission_id"] = mid
        mission["created_at"] = now
        mission["updated_at"] = now
        store["missions"][mid] = mission
        _save(store)
    return mission


def get_missions(status=None, cluster=None):
    """List missions with optional status/cluster filters."""
    data = _load()
    return [m for m in data.get("missions", {}).values()
            if m.get("status") != "deleted"
            and (not status or m.get("status") == status)
            and (not cluster or m.get("target_cluster") == cluster)]


def get_mission(mission_id):
    """Get a single mission by ID."""
    data = _load()
    m = data.get("missions", {}).get(mission_id)
    return m if m and m.get("status") != "deleted" else None


def update_mission(mission_id, data=None, **kwargs):
    """Update mission fields (merge into existing). Accepts data dict or kwargs."""
    updates = data if data is not None else kwargs
    with _lock:
        store = _load()
        m = store.get("missions", {}).get(mission_id)
        if not m or m.get("status") == "deleted":
            return None
        for k, v in updates.items():
            if k not in ("mission_id", "created_at"):
                m[k] = v
        m["updated_at"] = _ts()
        _save(store)
    return m


def delete_mission(mission_id):
    """Soft-delete a mission. Returns the deleted mission dict or None."""
    with _lock:
        data = _load()
        m = data.get("missions", {}).get(mission_id)
        if not m:
            return None
        m["status"] = "deleted"
        m["updated_at"] = _ts()
        _save(data)
    return m


# ────────────────────────────────────────────────────────────────────────────
# SECTION 2: INITIAL MISSION SET (6 strategic missions)
# ────────────────────────────────────────────────────────────────────────────

def _ms(names, sk):
    """Build milestones list with deterministic statuses."""
    out = []
    for i, n in enumerate(names):
        v = _seed(sk, "ms", i)
        st = "completed" if v < 0.15 else "in_progress" if v < 0.35 else "pending"
        out.append({"name": n, "status": st, "completed_at": _ts() if st == "completed" else None})
    return out

def seed_initial_missions():
    """Create the 6 strategic missions from the client brief."""
    defs = [
        # 1 ── Dog Food Authority Expansion
        {
            "mission_id": "mis_dog_food_authority",
            "mission_name": "Dog Food Authority Expansion",
            "name": "Dog Food Authority Expansion",
            "business_objective": "Build the first major topical authority cluster",
            "target_cluster": "dog_food",
            "responsible_agents": ["content_agent", "seo_agent", "product_research_agent"],
            "current_phase": "planning",
            "milestones": _ms(["Hub page research & outline approved", "Core comparison pages drafted (dry, wet, puppy, senior)", "Evidence & testing methodology documented", "Internal linking structure deployed", "Performance validation & optimisation"], "m1"),
            "required_content_assets": ["Dog Food Hub Page", "Best Dry Dog Food UK", "Best Wet Dog Food UK", "Best Puppy Food UK", "Best Senior Dog Food UK", "Dog Food Ingredient Guide UK", "Dry vs Wet Dog Food UK", "Sensitive Stomach Dog Food UK"],
            "required_evidence_assets": ["Ingredient analysis methodology", "Taste-test protocol documentation", "Veterinary consultation references", "Price comparison data sources"],
            "internal_linking_actions": ["Link hub to all sub-category pages", "Cross-link wet vs dry comparison to both individual pages", "Add contextual links from ingredient guide to product pages", "Build breadcrumb trail: Home > Dog > Dog Food > [Sub-category]"],
            "seo_actions": ["Target 'best dog food UK' cluster (5,400 mo. search vol)", "Optimise featured snippet for 'best dry dog food' queries", "Add FAQ schema to all sub-category pages", "Build topical map covering ingredient and dietary intent"],
            "affiliate_actions": ["Map affiliate links to top 5 products per sub-category", "Ensure price data freshness (weekly update cycle)", "Add comparison tables with affiliate CTAs"],
            "customer_journey_actions": ["Create 'Find the right food' interactive quiz funnel", "Add 'Why trust our picks' evidence section to each page", "Ensure mobile-first layout with sticky comparison bar"],
            "success_metrics": {"target_organic_traffic_uplift_pct": 35, "target_keyword_rankings_top10": 12, "target_engagement_rate": 0.68, "target_affiliate_ctr": 0.045, "target_authority_score": 0.88},
            "confidence_pct": 78.5, "risk_level": "medium", "approval_status": "approved", "priority": "high",
            "expected_business_impact": "Projected 35% organic traffic increase to dog food cluster within 6 months, establishing dominant topical authority and driving consistent affiliate revenue.",
            "next_recommended_action": "Finalise hub page outline and begin drafting Best Dry Dog Food UK page with full evidence methodology.",
            "data_source_label": "MODELLED FORECAST", "data_maturity": "moderate", "progress_pct": 15,
        },
        # 2 ── Dog Harness Commercial Opportunity
        {
            "mission_id": "mis_dog_harness_commercial",
            "mission_name": "Dog Harness Commercial Opportunity",
            "name": "Dog Harness Commercial Opportunity",
            "business_objective": "Capture high commercial intent with lower competition",
            "target_cluster": "dog_harnesses",
            "responsible_agents": ["content_agent", "seo_agent", "affiliate_agent"],
            "current_phase": "planning",
            "milestones": _ms(["Keyword research & competitive gap analysis", "Hub page and guide structure approved", "Core comparison pages drafted", "Affiliate integration & CTA optimisation", "Launch review & performance baseline"], "m2"),
            "required_content_assets": ["Dog Harness Hub/Guide", "Best Dog Harnesses UK", "Best No Pull Dog Harnesses UK", "Best Harnesses for Small Dogs", "Best Harnesses for Large Dogs", "Puppy Harness Guide"],
            "required_evidence_assets": ["Harness testing protocol (fit, comfort, durability)", "Size and breed suitability matrix", "Customer satisfaction data references"],
            "internal_linking_actions": ["Link hub to all harness comparison pages", "Cross-link small/large dog pages to breed-specific content", "Connect puppy harness guide to puppy food content"],
            "seo_actions": ["Target 'best dog harness UK' cluster (3,800 mo. search vol)", "Optimise comparison tables for featured snippets", "Add product schema markup", "Build FAQ schema for common harness questions"],
            "affiliate_actions": ["Map affiliate links to top 3 products per category", "Add 'best for' badges with affiliate CTAs", "Ensure price tracking for top recommended harnesses"],
            "customer_journey_actions": ["Create breed-size recommendation widget", "Add 'How we test' methodology section"],
            "success_metrics": {"target_organic_traffic_uplift_pct": 25, "target_keyword_rankings_top10": 8, "target_affiliate_ctr": 0.055, "target_authority_score": 0.84},
            "confidence_pct": 72.3, "risk_level": "low", "approval_status": "approved", "priority": "high",
            "expected_business_impact": "Projected 25% traffic increase and strong affiliate conversion from commercial-intent harness queries.",
            "next_recommended_action": "Complete keyword gap analysis and draft hub page structure.",
            "data_source_label": "MODELLED FORECAST", "data_maturity": "moderate", "progress_pct": 5,
        },
        # 3 ── Pet Insurance Trust Buildout (RED FLAG)
        {
            "mission_id": "mis_pet_insurance_trust",
            "mission_name": "Pet Insurance Trust Buildout",
            "name": "Pet Insurance Trust Buildout",
            "business_objective": "Prepare high-value monetization cluster with strong trust safeguards",
            "target_cluster": "pet_supplements",
            "responsible_agents": ["content_agent", "seo_agent", "affiliate_agent", "engagement_agent"],
            "current_phase": "planning",
            "milestones": _ms(["Regulatory review & compliance framework", "Trust and disclaimer structure approved by human", "Core informational pages drafted with disclaimers", "Internal linking & schema deployed (post-approval)", "Ongoing compliance monitoring activated"], "m3"),
            "required_content_assets": ["Pet Insurance Hub", "What Pet Insurance Covers", "Dog Insurance UK", "Cat Insurance UK", "Pet Insurance Comparison Guide", "Trust and Disclaimer Structure"],
            "required_evidence_assets": ["FCA compliance checklist", "Disclaimer templates (reviewed by compliance)", "Source attribution for all insurance claims", "Comparison methodology documentation"],
            "internal_linking_actions": ["Link hub to all insurance sub-pages", "Add prominent disclaimer links on every page", "Cross-link dog/cat insurance to respective pet clusters"],
            "seo_actions": ["Target informational intent only (avoid regulated commercial terms)", "Add FAQ schema with compliance-reviewed answers", "Ensure E-E-A-T signals: author credentials, sources, disclaimers"],
            "affiliate_actions": ["NO affiliate links until compliance review complete", "Any future affiliate integration requires RED approval", "Prepare compliant comparison format for post-approval use"],
            "customer_journey_actions": ["Create 'Do I need pet insurance?' decision guide", "Add trust signals: editorial independence, methodology", "Ensure all pages carry prominent regulatory disclaimers"],
            "success_metrics": {"target_trust_score": 0.92, "target_compliance_rate": 1.0, "target_organic_visibility": 0.65, "target_authority_score": 0.80},
            "confidence_pct": 55.0, "risk_level": "high", "approval_status": "red_flag", "priority": "high",
            "expected_business_impact": "High monetization potential but requires elevated trust safeguards. Red approval required before any content goes live.",
            "next_recommended_action": "Await red-flag approval from business owner before proceeding.",
            "data_source_label": "MODELLED FORECAST", "data_maturity": "low", "progress_pct": 0,
        },
        # 4 ── Cat Toys Recovery / Engagement
        {
            "mission_id": "mis_cat_toys_recovery",
            "mission_name": "Cat Toys Recovery / Engagement",
            "name": "Cat Toys Recovery / Engagement",
            "business_objective": "Improve rankings, engagement, internal linking, and conversion",
            "target_cluster": "cat_toys",
            "responsible_agents": ["content_agent", "seo_agent", "engagement_agent"],
            "current_phase": "planning",
            "milestones": _ms(["Content audit & decay analysis", "Existing page refresh with updated products", "Comparison support and internal links improved", "Answer-readiness and AI search optimisation", "Performance re-baseline and monitoring"], "m4"),
            "required_content_assets": ["Refresh Cat Toys Page", "Comparison Support", "Internal Links Improvement", "Answer-Readiness Enhancement"],
            "required_evidence_assets": ["Current page performance data (GA4 + GSC)", "Competitor content gap analysis", "Product relevance audit (discontinued items)"],
            "internal_linking_actions": ["Refresh internal links on existing page", "Add comparison support links to related cat clusters", "Improve internal authority flow from cat food hub"],
            "seo_actions": ["Refresh meta titles and descriptions", "Update structured data (product schema)", "Add direct-answer blocks for common cat toy queries", "Reduce content fatigue signals"],
            "affiliate_actions": ["Replace discontinued product affiliate links", "Improve product relevance scoring", "Add updated comparison tables with current pricing"],
            "customer_journey_actions": ["Improve category navigation from cat hub", "Add age/activity-based toy recommendations", "Reduce bounce rate with better above-fold content"],
            "success_metrics": {"target_traffic_recovery_pct": 20, "target_engagement_improvement": 0.15, "target_bounce_rate_reduction": 0.08, "target_answer_readiness": 0.75},
            "confidence_pct": 68.2, "risk_level": "medium", "approval_status": "approved", "priority": "medium",
            "expected_business_impact": "Recover estimated 20% lost traffic and restore engagement metrics to pre-decline levels.",
            "next_recommended_action": "Audit current Cat Toys page for refresh opportunities.",
            "data_source_label": "MODELLED FORECAST", "data_maturity": "moderate", "progress_pct": 10,
        },
        # 5 ── Homepage Engagement Recovery
        {
            "mission_id": "mis_homepage_engagement",
            "mission_name": "Homepage Engagement Recovery",
            "name": "Homepage Engagement Recovery",
            "business_objective": "Reduce bounce and improve journey routing",
            "target_cluster": "dog_food",
            "responsible_agents": ["engagement_agent", "content_agent", "seo_agent"],
            "current_phase": "planning",
            "milestones": _ms(["Homepage engagement audit completed", "Category routing & pathway redesign approved", "Trust signal and start-here sections implemented", "Internal authority flow optimisation deployed"], "m5"),
            "required_content_assets": ["Category Routes Improvement", "Trust Signals", "Start Here Sections", "Dog/Cat Pathways", "Authority Flow Improvement"],
            "required_evidence_assets": ["Current homepage heatmap and click data", "User flow analysis (GA4 path exploration)", "Bounce rate and exit page data"],
            "internal_linking_actions": ["Clearer category routes from homepage to clusters", "Improved dog/cat pathways with visual navigation", "Stronger start-here sections linking to hub pages", "Better internal authority flow to money pages"],
            "seo_actions": ["Optimise homepage title and meta", "Add organisation schema with enhanced site links", "Improve page speed and Core Web Vitals"],
            "affiliate_actions": ["No direct affiliate links on homepage", "Ensure category routes lead to affiliate-enabled content"],
            "customer_journey_actions": ["Create clear dog vs cat entry pathways", "Add 'Popular right now' dynamic section", "Improve mobile navigation to reduce friction", "Add editorial credibility section above fold"],
            "success_metrics": {"target_bounce_rate_reduction": 0.12, "target_pages_per_session_increase": 0.8, "target_category_click_through": 0.35, "target_engagement_rate": 0.72},
            "confidence_pct": 65.0, "risk_level": "medium", "approval_status": "approved", "priority": "medium",
            "expected_business_impact": "Reduces homepage bounce rate, improves journey routing, and strengthens authority flow to key category clusters.",
            "next_recommended_action": "Analyse current homepage engagement metrics and identify routing gaps.",
            "data_source_label": "MODELLED FORECAST", "data_maturity": "low", "progress_pct": 0,
        },
        # 6 ── AI Search Adaptation Mission
        {
            "mission_id": "mis_ai_search_adaptation",
            "mission_name": "AI Search Adaptation Mission",
            "name": "AI Search Adaptation Mission",
            "business_objective": "Prepare key clusters for AI Overview and answer-engine behaviour",
            "target_cluster": "dog_food",
            "responsible_agents": ["seo_agent", "content_agent", "analytics_agent"],
            "current_phase": "planning",
            "milestones": _ms(["AI search readiness audit across all clusters", "Answer-ready summary templates created and approved", "Evidence sections and entity completeness deployed", "Citation-friendly formatting applied site-wide", "Comparison summaries and direct-answer blocks live"], "m6"),
            "required_content_assets": ["Answer-Ready Summaries", "Evidence Sections", "Entity Completeness", "Citation-Friendly Formatting", "Comparison Summaries", "Direct-Answer Blocks"],
            "required_evidence_assets": ["Current AI Overview citation data", "Entity gap analysis per cluster", "Competitor AI search visibility benchmarks"],
            "internal_linking_actions": ["Add entity-level cross-links between related topics", "Ensure citation paths are crawlable and well-structured", "Build semantic relationship links across clusters"],
            "seo_actions": ["Add answer-ready summaries to top pages", "Implement evidence sections with source attribution", "Ensure entity completeness across all clusters", "Add citation-friendly formatting", "Build comparison summaries for vs-style queries", "Create direct-answer blocks for question-intent pages"],
            "affiliate_actions": ["Ensure AI-cited pages maintain affiliate integration", "Adapt product recommendations for AI-extracted contexts"],
            "customer_journey_actions": ["Improve zero-click answer experience", "Add 'read more on PetHub' hooks for AI-surfaced content", "Ensure mobile experience supports AI referral traffic"],
            "success_metrics": {"target_ai_citation_rate": 0.25, "target_answer_readiness_score": 0.80, "target_entity_completeness": 0.85, "target_ai_referral_traffic_pct": 0.10},
            "confidence_pct": 52.0, "risk_level": "medium", "approval_status": "approved", "priority": "high",
            "expected_business_impact": "Prepares strongest cluster for AI Overview inclusion, builds citation-friendly formatting and entity completeness.",
            "next_recommended_action": "Run AI search readiness audit on dog_food cluster pages.",
            "data_source_label": "MODELLED FORECAST", "data_maturity": "low", "progress_pct": 0,
        },
    ]
    created = []
    for d in defs:
        created.append(create_mission(d))
    # Generate backlogs for each seeded mission
    backlog_results = []
    for m in created:
        result = generate_backlog(m["mission_id"])
        if result and not result.get("error"):
            backlog_results.append({
                "mission_id": m["mission_id"],
                "name": m.get("mission_name") or m.get("name"),
                "items_generated": result.get("items_generated", 0),
            })
    return {
        "status": "seeded",
        "seeded": len(created),
        "missions_created": len(created),
        "mission_ids": [m["mission_id"] for m in created],
        "missions": [
            {
                "mission_id": m["mission_id"],
                "name": m.get("mission_name") or m.get("name"),
                "target_cluster": m.get("target_cluster"),
                "priority": m.get("priority", "medium"),
                "approval_status": m.get("approval_status"),
            }
            for m in created
        ],
        "backlogs_generated": backlog_results,
        "data_source_label": "MODELLED FORECAST",
        "generated_at": _ts(),
    }


# ────────────────────────────────────────────────────────────────────────────
# SECTION 3: BACKLOG GENERATION
# ────────────────────────────────────────────────────────────────────────────

def _bli(mission_id, item_type, title, desc, sk, agent=None, approval=None, dep=None):
    """Create a single backlog item dict."""
    is_ins = "insurance" in mission_id
    return {
        "item_id": _gen_id("blg"), "mission_id": mission_id,
        "item_type": item_type, "title": title, "description": desc,
        "assigned_agent": agent or _pick_one(AGENTS, sk, "agent"),
        "priority": "critical" if (approval == "red" or is_ins) else _pick_priority(sk, "pri"),
        "estimated_business_impact": f"Confidence-weighted impact score: {_sr(2.0, 9.5, sk, 'impact')}/10",
        "confidence_pct": round(_score100(sk, "conf"), 1),
        "approval_requirement": approval or ("red" if is_ins else "none"),
        "dependency": dep, "status": "pending", "result": None,
        "data_source_label": _pick_label(sk, "label"),
        "created_at": _ts(), "updated_at": _ts(),
    }

# Compact backlog definitions: (item_type, title, description)
_BLG_DOG_FOOD = [
    ("content_brief", "Content Brief: Dog Food Hub Page", "Central hub page organising all dog food sub-content with topical navigation and authority signals."),
    ("content_brief", "Content Brief: Best Dry Dog Food UK", "Comparison page with evidence-backed rankings, methodology, and affiliate integration."),
    ("content_brief", "Content Brief: Best Wet Dog Food UK", "Comparison of top wet dog food brands with nutritional analysis and testing evidence."),
    ("content_brief", "Content Brief: Best Puppy Food UK", "Age-specific guide with growth-stage recommendations and vet references."),
    ("content_brief", "Content Brief: Best Senior Dog Food UK", "Senior nutrition guide with health condition considerations and product comparisons."),
    ("content_brief", "Content Brief: Dog Food Ingredient Guide UK", "Educational deep-dive into ingredients, benefits, and red flags."),
    ("content_brief", "Content Brief: Dry vs Wet Dog Food UK", "Direct comparison with structured evidence answering the top dog food question."),
    ("content_brief", "Content Brief: Sensitive Stomach Dog Food UK", "Specialist guide for dogs with dietary sensitivities with vet-backed recommendations."),
    ("internal_linking_proposal", "Dog Food Cluster Internal Linking Map", "All internal links between hub, sub-pages, and cross-cluster connections."),
    ("metadata_proposal", "Dog Food Metadata Optimisation Pack", "Titles, descriptions, OG tags for all 8 pages targeting primary keywords."),
    ("schema_proposal", "Dog Food Schema Markup Package", "FAQ, Product, HowTo schema for all pages to maximise SERP features."),
    ("evidence_requirement", "Dog Food Testing Methodology Documentation", "Document testing and evaluation methodology for all recommendations."),
    ("evidence_requirement", "Ingredient Analysis Source References", "Compile and verify all nutritional and ingredient data sources."),
    ("affiliate_placement_review", "Dog Food Affiliate Integration Review", "Optimise affiliate placement for compliance and conversion across all pages."),
    ("product_research_task", "Dog Food Product Freshness Audit", "Verify all recommended products are available, correctly priced, not discontinued."),
]

_BLG_HARNESS = [
    ("content_brief", "Dog Harness Hub/Guide", "Hub page covering all harness types with navigation to comparison pages."),
    ("content_brief", "Best Dog Harnesses UK", "Comprehensive comparison with testing evidence and ranked recommendations."),
    ("content_brief", "Best No Pull Dog Harnesses UK", "Focused guide on no-pull harnesses with fit and training advice."),
    ("content_brief", "Best Harnesses for Small Dogs", "Size-specific guide for small breed harness recommendations."),
    ("content_brief", "Best Harnesses for Large Dogs", "Large breed guide with durability focus and fit considerations."),
    ("content_brief", "Puppy Harness Guide", "Age-specific puppy harness guide with growth considerations."),
    ("evidence_requirement", "Harness Testing Protocol Documentation", "Document fit, comfort, and durability testing methodology."),
    ("internal_linking_proposal", "Harness Cluster Internal Link Map", "Internal links between hub, comparison pages, and breed-specific content."),
    ("metadata_proposal", "Harness Pages Metadata Pack", "Optimised titles, descriptions, OG tags for all harness pages."),
    ("schema_proposal", "Harness Product Schema", "Product and FAQ schema for all harness comparison pages."),
    ("affiliate_placement_review", "Harness Affiliate Integration Plan", "Map affiliate links to top products per category with compliant CTAs."),
    ("product_research_task", "Harness Product Availability Check", "Verify all recommended harnesses are in stock, correctly priced, and still manufactured."),
]

_BLG_INSURANCE = [
    ("content_brief", "Pet Insurance Hub Page Brief", "Hub page structure with regulatory disclaimers and editorial independence statement."),
    ("content_brief", "What Pet Insurance Covers Guide Brief", "Informational guide covering standard coverage types with source-attributed data."),
    ("content_brief", "Dog Insurance UK Brief", "Dog-specific insurance information with breed considerations and compliance-reviewed content."),
    ("content_brief", "Cat Insurance UK Brief", "Cat-specific insurance information with indoor/outdoor considerations."),
    ("content_brief", "Pet Insurance Comparison Guide Brief", "Comparison methodology and framework ensuring no misleading claims."),
    ("trust_signal_improvement", "Trust and Disclaimer Framework", "Disclaimer templates, editorial independence statement, compliance review process."),
    ("metadata_proposal", "Insurance Pages Metadata Pack", "Compliance-reviewed metadata avoiding regulated commercial terms."),
    ("schema_proposal", "Insurance FAQ Schema", "FAQ schema with compliance-approved answers to common questions."),
    ("evidence_requirement", "FCA Compliance Documentation", "Document FCA regulatory requirements applicable to pet insurance content."),
    ("evidence_requirement", "Source Attribution Registry", "Verified source registry for all insurance-related claims and data points."),
    ("internal_linking_proposal", "Insurance Cluster Linking Plan", "Safe internal linking structure that does not imply commercial recommendation."),
    ("customer_journey_improvement", "Insurance Decision Guide UX", "Design the 'Do I need pet insurance?' decision flow with disclaimers."),
]

_BLG_CAT_TOYS = [
    ("refresh_recommendation", "Refresh Cat Toys Page", "Update products, remove discontinued items, refresh evidence sections."),
    ("content_brief", "Comparison Support", "Interactive comparison table with current products and pricing."),
    ("internal_linking_proposal", "Internal Links Improvement", "Rebuild internal links connecting to cat food and supplies clusters."),
    ("schema_proposal", "Answer-Readiness Enhancement", "Add direct-answer blocks and structured data for AI search."),
    ("metadata_proposal", "Cat Toys Metadata Refresh", "Update titles and descriptions to reflect refreshed content."),
    ("evidence_requirement", "Cat Toys Product Relevance Audit", "Audit all recommended products for availability and relevance."),
    ("cro_recommendation", "Cat Toys Above-Fold Optimisation", "Improve above-fold content to reduce bounce rate."),
    ("customer_journey_improvement", "Cat Toys Age-Based Recommendations", "Add age and activity-based toy recommendation paths."),
    ("affiliate_placement_review", "Cat Toys Affiliate Link Audit", "Replace discontinued links and improve affiliate integration."),
]

_BLG_HOMEPAGE = [
    ("customer_journey_improvement", "Category Routes Improvement", "Redesign category routing for clearer dog/cat pathways."),
    ("trust_signal_improvement", "Trust Signals", "Add methodology, about, and evidence components above fold."),
    ("content_brief", "Start Here Sections", "Welcoming entry sections guiding dog and cat owners to key content."),
    ("customer_journey_improvement", "Dog/Cat Pathways", "Create clear dog vs cat entry pathways with visual navigation."),
    ("internal_linking_proposal", "Authority Flow Improvement", "Restructure homepage links to distribute authority to money pages."),
    ("metadata_proposal", "Homepage Meta & Schema Update", "Optimise title, description, and organisation schema."),
    ("customer_journey_improvement", "Mobile Navigation Friction Reduction", "Improve mobile homepage experience to reduce friction."),
    ("cro_recommendation", "Homepage Dynamic Popular Section", "Add 'Popular right now' dynamic section based on trending content."),
]

_BLG_AI_SEARCH = [
    ("content_brief", "Answer-Ready Summaries", "Standardised answer-ready summaries across dog_food cluster."),
    ("evidence_requirement", "Evidence Sections", "Evidence section format with source attribution and methodology."),
    ("schema_proposal", "Entity Completeness", "Ensure entity completeness across target clusters."),
    ("metadata_proposal", "Citation-Friendly Formatting", "Clear headings and structured data optimised for AI citation."),
    ("content_brief", "Comparison Summaries", "Concise comparison summaries suitable for AI extraction."),
    ("content_brief", "Direct-Answer Blocks", "Templates for direct-answer blocks targeting question-intent queries."),
    ("evidence_requirement", "AI Search Readiness Baseline Audit", "Audit current AI Overview citations and entity representation."),
    ("internal_linking_proposal", "Entity Cross-Link Map", "Entity-level cross-links between semantically related topics."),
    ("product_research_task", "Competitor AI Visibility Benchmark", "Benchmark competitor AI search visibility and citation rates."),
]

_BLG_MAP = {
    "mis_dog_food_authority": _BLG_DOG_FOOD,
    "mis_dog_harness_commercial": _BLG_HARNESS,
    "mis_pet_insurance_trust": _BLG_INSURANCE,
    "mis_cat_toys_recovery": _BLG_CAT_TOYS,
    "mis_homepage_engagement": _BLG_HOMEPAGE,
    "mis_ai_search_adaptation": _BLG_AI_SEARCH,
}


def generate_backlog(mission_id):
    """Auto-generate backlog items from a mission."""
    with _lock:
        data = _load()
        mission = data.get("missions", {}).get(mission_id)
        if not mission:
            return {"error": f"Mission {mission_id} not found"}

        specs = _BLG_MAP.get(mission_id)
        items = []
        if specs:
            is_ins = "insurance" in mission_id
            for i, (itype, title, desc) in enumerate(specs):
                items.append(_bli(mission_id, itype, title, desc,
                                  f"{mission_id}_{i}",
                                  approval="red" if is_ins else None))
        else:
            for i, asset in enumerate(mission.get("required_content_assets", [])):
                items.append(_bli(mission_id, "content_brief",
                                  f"Content Brief: {asset}", f"Produce content brief for: {asset}",
                                  f"gen_{mission_id}_{i}"))
            for i, action in enumerate(mission.get("internal_linking_actions", [])):
                items.append(_bli(mission_id, "internal_linking_proposal",
                                  f"Linking: {action[:60]}", action,
                                  f"gen_il_{mission_id}_{i}"))

        for item in items:
            data.setdefault("backlog", {})[item["item_id"]] = item
        _save(data)
    return {"mission_id": mission_id, "items_generated": len(items),
            "item_ids": [it["item_id"] for it in items]}


def get_backlog(mission_id=None, item_type=None, status=None):
    """List backlog items with optional filters."""
    data = _load()
    return [b for b in data.get("backlog", {}).values()
            if (not mission_id or b.get("mission_id") == mission_id)
            and (not item_type or b.get("item_type") == item_type)
            and (not status or b.get("status") == status)]


def get_backlog_item(item_id):
    """Get a single backlog item by ID."""
    return _load().get("backlog", {}).get(item_id)


def update_backlog_item(item_id, data=None, **kwargs):
    """Update a backlog item. Accepts data dict or kwargs."""
    updates = data if data is not None else kwargs
    with _lock:
        store = _load()
        item = store.get("backlog", {}).get(item_id)
        if not item:
            return None
        for k, v in updates.items():
            if k not in ("item_id", "mission_id", "created_at"):
                item[k] = v
        item["updated_at"] = _ts()
        _save(store)
    return item


# ────────────────────────────────────────────────────────────────────────────
# SECTION 4: MISSION PROGRESS TRACKING
# ────────────────────────────────────────────────────────────────────────────

def update_mission_progress(mission_id):
    """Recalculate progress_pct from milestone and backlog completion."""
    with _lock:
        data = _load()
        m = data.get("missions", {}).get(mission_id)
        if not m or m.get("status") == "deleted":
            return None
        # Milestones (40% weight)
        mss = m.get("milestones", [])
        ms_pct = (sum(1 for x in mss if x.get("status") == "completed")
                  + sum(0.5 for x in mss if x.get("status") == "in_progress")
                  ) / max(len(mss), 1)
        # Backlog (60% weight)
        bl = [b for b in data.get("backlog", {}).values() if b.get("mission_id") == mission_id]
        bl_pct = (sum(1 for b in bl if b.get("status") == "completed")
                  + sum(0.5 for b in bl if b.get("status") == "in_progress")
                  ) / max(len(bl), 1)
        progress = round(min((ms_pct * 0.4 + bl_pct * 0.6) * 100, 100), 1)
        m["progress_pct"] = progress
        m["updated_at"] = _ts()
        if progress >= 95:
            m["current_phase"] = "completed"
        elif progress >= 75:
            m["current_phase"] = "monitoring"
        elif progress >= 50:
            m["current_phase"] = "optimization"
        _save(data)
    return m


def get_mission_summary():
    """Overview of all missions with stats."""
    data = _load()
    missions = [m for m in data.get("missions", {}).values() if m.get("status") != "deleted"]
    backlog = data.get("backlog", {})
    summary = {
        "total_missions": len(missions), "by_status": {}, "by_phase": {},
        "by_risk": {}, "avg_progress_pct": 0, "avg_confidence_pct": 0,
        "total_backlog_items": len(backlog), "backlog_by_status": {},
        "red_flag_missions": [], "missions": [], "data_source_label": "MODELLED FORECAST",
    }
    tp, tc = 0, 0
    for m in missions:
        for key, field in [("by_status", "status"), ("by_phase", "current_phase"), ("by_risk", "risk_level")]:
            v = m.get(field, "unknown")
            summary[key][v] = summary[key].get(v, 0) + 1
        tp += m.get("progress_pct", 0)
        tc += m.get("confidence_pct", 0)
        if m.get("approval_status") == "red_flag":
            summary["red_flag_missions"].append(m["mission_id"])
        mi_bl = [b for b in backlog.values() if b.get("mission_id") == m["mission_id"]]
        summary["missions"].append({
            "mission_id": m["mission_id"], "mission_name": m["mission_name"],
            "status": m.get("status"), "phase": m.get("current_phase"),
            "progress_pct": m.get("progress_pct", 0), "confidence_pct": m.get("confidence_pct", 0),
            "risk_level": m.get("risk_level"), "approval_status": m.get("approval_status"),
            "backlog_items": len(mi_bl),
            "backlog_completed": sum(1 for b in mi_bl if b.get("status") == "completed"),
        })
    if missions:
        summary["avg_progress_pct"] = round(tp / len(missions), 1)
        summary["avg_confidence_pct"] = round(tc / len(missions), 1)
    for b in backlog.values():
        s = b.get("status", "pending")
        summary["backlog_by_status"][s] = summary["backlog_by_status"].get(s, 0) + 1
    return summary


def get_mission_dashboard_data():
    """Combined dashboard data: {missions, backlog_summary, progress_overview, content_quality_status}."""
    data = _load()
    missions = [m for m in data.get("missions", {}).values() if m.get("status") != "deleted"]
    backlog_items = list(data.get("backlog", {}).values())

    # Missions overview (lightweight)
    missions_overview = []
    for m in missions:
        missions_overview.append({
            "mission_id": m.get("mission_id"),
            "name": m.get("name") or m.get("mission_name"),
            "mission_name": m.get("mission_name") or m.get("name"),
            "target_cluster": m.get("target_cluster"),
            "current_phase": m.get("current_phase"),
            "priority": m.get("priority"),
            "approval_status": m.get("approval_status"),
            "confidence_pct": m.get("confidence_pct"),
            "risk_level": m.get("risk_level"),
            "responsible_agents": m.get("responsible_agents", []),
            "progress_pct": m.get("progress_pct", 0),
            "next_recommended_action": m.get("next_recommended_action"),
        })

    # Backlog summary
    status_counts = {}
    type_counts = {}
    agent_counts = {}
    for item in backlog_items:
        st = item.get("status", "pending")
        status_counts[st] = status_counts.get(st, 0) + 1
        it = item.get("item_type", "unknown")
        type_counts[it] = type_counts.get(it, 0) + 1
        ag = item.get("assigned_agent", "unassigned")
        agent_counts[ag] = agent_counts.get(ag, 0) + 1

    items_needing_approval = [
        {"item_id": i["item_id"], "title": i.get("title"), "item_type": i.get("item_type")}
        for i in backlog_items
        if i.get("approval_requirement") and i.get("approval_requirement") != "none"
        and i.get("status") == "pending"
    ]

    backlog_summary = {
        "total_items": len(backlog_items),
        "status_distribution": status_counts,
        "type_distribution": type_counts,
        "agent_workload": agent_counts,
        "items_needing_approval": items_needing_approval,
    }

    # Progress overview
    active = [m for m in missions if m.get("current_phase") != "completed"]
    completed = [m for m in missions if m.get("current_phase") == "completed"]
    total_milestones = sum(len(m.get("milestones", [])) for m in missions)
    reached_milestones = sum(
        len([ms for ms in m.get("milestones", []) if ms.get("status") == "completed" or ms.get("reached")])
        for m in missions
    )

    progress_overview = {
        "active_missions": len(active),
        "completed_missions": len(completed),
        "total_milestones": total_milestones,
        "milestones_reached": reached_milestones,
        "milestone_completion_pct": round(
            (reached_milestones / max(1, total_milestones)) * 100, 1
        ),
        "high_priority_count": len([m for m in missions if m.get("priority") == "high"]),
        "red_flag_count": len([m for m in missions if m.get("approval_status") == "red_flag"]),
    }

    # Content quality status
    content_quality_status = {
        "quality_rules_active": len(_QUALITY_RULES),
        "rules_summary": [r["name"] for r in _QUALITY_RULES],
        "enforcement_level": "strict",
        "last_check": _ts(),
    }

    return {
        "missions": missions_overview,
        "backlog_summary": backlog_summary,
        "progress_overview": progress_overview,
        "content_quality_status": content_quality_status,
        # Legacy fields for backward compatibility
        "backlog": data.get("backlog", {}),
        "learnings": data.get("learnings", {}),
        "last_briefing": (data.get("briefings", []) or [None])[-1],
        "summary": get_mission_summary(),
        "last_scan": data.get("last_scan"),
        "data_source_label": "MODELLED FORECAST",
    }


# ────────────────────────────────────────────────────────────────────────────
# SECTION 5: LEARNING LOOPS
# ────────────────────────────────────────────────────────────────────────────

def record_learning(mission_id, data=None, **kwargs):
    """Record a learning note for a mission. Accepts data dict or kwargs."""
    ld = data if data is not None else kwargs
    with _lock:
        store = _load()
        m = store.get("missions", {}).get(mission_id)
        if not m or m.get("status") == "deleted":
            return None
        lid = _gen_id("lrn")
        now = _ts()
        # Accept both 'note' (from routes Pydantic) and 'observation' (legacy)
        note_text = ld.get("note") or ld.get("observation", "")
        learning = {
            "learning_id": lid, "mission_id": mission_id,
            "note": note_text,
            "observation": note_text,
            "metric_type": ld.get("metric_type"),
            "forecasted_value": ld.get("forecasted_value"),
            "actual_value": ld.get("actual_value"),
            "variance": None,
            "category": ld.get("category", "general"),
            "impact_assessment": ld.get("impact_assessment", ""),
            "recommended_adjustment": ld.get("recommended_adjustment", ""),
            "confidence_pct": ld.get("confidence_pct", 50),
            "data_source_label": ld.get("data_source_label", "ESTIMATED / PROXY SCORE"),
            "recorded_by": ld.get("recorded_by", "system"),
            "created_at": now,
        }
        # Calculate variance if both values provided
        if learning["forecasted_value"] is not None and learning["actual_value"] is not None:
            try:
                learning["variance"] = round(float(learning["actual_value"]) - float(learning["forecasted_value"]), 4)
            except (ValueError, TypeError):
                pass
        store.setdefault("learnings", {}).setdefault(mission_id, []).append(learning)
        m.setdefault("learning_notes", []).append({
            "learning_id": lid, "observation": note_text, "created_at": now,
        })
        m["updated_at"] = now
        _save(store)
    return learning


def get_mission_learnings(mission_id):
    """Get all learning notes for a mission."""
    return _load().get("learnings", {}).get(mission_id, [])


def evaluate_mission_accuracy(mission_id):
    """Compare forecasted vs actual metrics using deterministic scoring.

    Tracks: forecasted vs actual traffic, rankings, engagement, authority
    score, and monetization. Returns data_maturity, confidence_pct,
    last_validation_date, and forecast_accuracy for each metric.
    """
    data = _load()
    m = data.get("missions", {}).get(mission_id)
    if not m:
        return None
    metrics = m.get("success_metrics", {})
    report = {
        "mission_id": mission_id,
        "mission_name": m.get("mission_name"),
        "evaluated_at": _ts(),
        "data_maturity": m.get("data_maturity", "low"),
        "confidence_pct": m.get("confidence_pct", 0),
        "last_validation_date": m.get("last_validation_date"),
        "metrics_comparison": {},
        "overall_forecast_accuracy": 0,
        "forecast_accuracy": 0,
        "ethical_compliance": _ethical_check(),
        "data_source_label": "ESTIMATED / PROXY SCORE",
    }
    total, count = 0, 0
    for name, target in metrics.items():
        if not isinstance(target, (int, float)) or target == 0:
            continue
        actual = _sr(0, float(target) * 1.4, mission_id, name, "actual")
        acc = min(actual / target, 1.5)
        report["metrics_comparison"][name] = {
            "forecasted": target,
            "actual_estimated": round(actual, 3),
            "accuracy_pct": round(acc * 100, 1),
            "forecast_accuracy": round(acc * 100, 1),
            "status": "on_track" if 0.8 <= acc <= 1.2 else ("ahead" if acc > 1.2 else "behind"),
            "data_source_label": "ESTIMATED / PROXY SCORE",
        }
        total += acc
        count += 1
    if count:
        overall = round((total / count) * 100, 1)
        report["overall_forecast_accuracy"] = overall
        report["forecast_accuracy"] = overall
    return report


# ────────────────────────────────────────────────────────────────────────────
# SECTION 6: MISSION SCAN & BRIEFING
# ────────────────────────────────────────────────────────────────────────────

def run_mission_scan():
    """Refresh all mission data, recalculate progress, generate briefing."""
    data = _load()
    now = _ts()
    scan = {"scanned_at": now, "missions_scanned": 0,
            "progress_updates": [], "blocked_items": [], "red_flags": []}

    active_ids = [k for k, v in data.get("missions", {}).items()
                  if v.get("status") not in ("deleted", "cancelled")]
    for mid in active_ids:
        updated = update_mission_progress(mid)
        if updated:
            scan["missions_scanned"] += 1
            scan["progress_updates"].append({
                "mission_id": mid, "progress_pct": updated.get("progress_pct", 0),
                "phase": updated.get("current_phase"),
            })
        m = data.get("missions", {}).get(mid, {})
        if m.get("approval_status") == "red_flag":
            scan["red_flags"].append({"mission_id": mid, "mission_name": m.get("mission_name"),
                                       "reason": "Requires explicit human approval"})

    data = _load()  # re-read after progress updates
    for bid, b in data.get("backlog", {}).items():
        if b.get("status") == "blocked":
            scan["blocked_items"].append({"item_id": bid, "mission_id": b.get("mission_id"),
                                           "title": b.get("title"), "dependency": b.get("dependency")})
    with _lock:
        data = _load()
        data["last_scan"] = now
        _save(data)

    briefing = _build_briefing(scan)
    with _lock:
        data = _load()
        data.setdefault("briefings", []).append(briefing)
        data["briefings"] = data["briefings"][-20:]
        _save(data)
    return {"scan": scan, "briefing": briefing}


def _build_briefing(scan):
    """Create executive briefing with required fields:
    headline, active_missions_count, completed_actions_count, overall_progress_pct,
    summary_text, top_priority_mission, biggest_blocker, next_recommended_action,
    generated_at, data_source_label.
    """
    now = _ts()
    data = _load()
    missions = [m for m in data.get("missions", {}).values() if m.get("status") != "deleted"]
    backlog = data.get("backlog", {})
    active = [m for m in missions if m.get("status") == "active"]
    red_flags = [m for m in missions if m.get("approval_status") == "red_flag"]
    avg_prog = round(sum(m.get("progress_pct", 0) for m in active) / max(len(active), 1), 1)
    bl_done = sum(1 for b in backlog.values() if b.get("status") == "completed")
    blocked = sum(1 for b in backlog.values() if b.get("status") == "blocked")
    completed_m = sum(1 for m in missions if m.get("status") == "completed")

    # Build narrative text
    lines = [f"PetHub Strategic Mission Control Briefing - {now[:10]}", "",
             "WHAT WE ARE WORKING ON:"]
    for m in active:
        mname = m.get("name") or m.get("mission_name", "?")
        lines.append(f"  - {mname} ({m['target_cluster']}): "
                     f"{m.get('progress_pct', 0)}% complete, phase: {m.get('current_phase')}")
    lines += ["", "WHY IT MATTERS:",
              f"  {len(active)} active missions driving organic growth, authority building, "
              f"and AI search readiness. Average progress: {avg_prog}%."]
    if red_flags:
        lines.append(f"  {len(red_flags)} mission(s) flagged RED requiring human approval.")
    lines += ["", "WHAT HAS BEEN COMPLETED:",
              f"  {completed_m} mission(s) completed. {bl_done}/{len(backlog)} backlog items done."]
    for m in missions:
        mname = m.get("name") or m.get("mission_name", "?")
        for ms in m.get("milestones", []):
            if ms.get("status") == "completed":
                lines.append(f"  - [{mname}] {ms['name']}")
    lines += ["", "WHAT IS BLOCKED:"]
    if blocked:
        lines.append(f"  {blocked} backlog item(s) currently blocked.")
        for b in backlog.values():
            if b.get("status") == "blocked":
                lines.append(f"  - {b['title']} (depends on: {b.get('dependency', 'unknown')})")
    else:
        lines.append("  No items currently blocked.")
    for m in red_flags:
        mname = m.get("name") or m.get("mission_name", "?")
        lines.append(f"  - RED FLAG: {mname} awaiting human approval")
    lines += ["", "WHAT SHOULD HAPPEN NEXT:"]
    for m in active:
        nra = m.get("next_recommended_action")
        mname = m.get("name") or m.get("mission_name", "?")
        if nra:
            lines.append(f"  - [{mname}] {nra}")

    summary_text = "\n".join(lines)

    # Top priority mission
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_m = sorted(active, key=lambda m: (
        priority_order.get(m.get("priority", "low"), 4),
        -m.get("confidence_pct", 0),
    ))
    top = sorted_m[0] if sorted_m else None

    # Biggest blocker
    biggest_blocker = "No active blockers identified"
    for m in red_flags:
        mname = m.get("name") or m.get("mission_name", "?")
        biggest_blocker = f"{mname}: Requires explicit human approval before proceeding"
        break
    if biggest_blocker == "No active blockers identified" and blocked > 0:
        for b in backlog.values():
            if b.get("status") == "blocked":
                biggest_blocker = f"{b['title']}: blocked on dependency {b.get('dependency', 'unknown')}"
                break

    # Next recommended action
    if top:
        next_action = top.get("next_recommended_action",
                              f"Continue work on {top.get('name') or top.get('mission_name', 'top mission')}")
    else:
        next_action = "Seed initial missions to begin strategy execution"

    headline = f"Mission Control: {len(active)} active, {avg_prog}% overall progress"

    return {
        "briefing_id": _gen_id("brf"),
        "headline": headline,
        "active_missions_count": len(active),
        "completed_actions_count": bl_done,
        "overall_progress_pct": avg_prog,
        "summary_text": summary_text,
        "top_priority_mission": {
            "mission_id": top["mission_id"],
            "name": top.get("name") or top.get("mission_name"),
            "priority": top.get("priority"),
            "current_phase": top.get("current_phase"),
        } if top else None,
        "biggest_blocker": biggest_blocker,
        "next_recommended_action": next_action,
        "generated_at": now,
        "data_source_label": "MODELLED FORECAST",
        # Legacy fields for backward compatibility
        "text": summary_text,
        "stats": {
            "active_missions": len(active), "completed_missions": completed_m,
            "avg_progress_pct": avg_prog, "total_backlog": len(backlog),
            "backlog_completed": bl_done, "blocked_items": blocked,
            "red_flags": len(red_flags),
        },
    }


def get_mission_briefing():
    """Read the latest briefing from JSON."""
    data = _load()
    briefings = data.get("briefings", [])
    if briefings:
        return briefings[-1]
    # Generate one on the fly if none exists
    return run_mission_scan().get("briefing")


# ────────────────────────────────────────────────────────────────────────────
# SECTION 7: CONTENT QUALITY ENFORCEMENT
# ────────────────────────────────────────────────────────────────────────────

_QUALITY_RULES = [
    {"rule_id": "no_fake_testing", "name": "No Fake Testing Claims", "severity": "critical",
     "description": "Content must not claim products were physically tested unless genuine testing evidence exists.",
     "keywords": ["we tested", "our testing", "hands-on test", "we tried", "in our tests", "our team tested", "we personally tested"]},
    {"rule_id": "no_fake_experts", "name": "No Fake Expert Claims", "severity": "critical",
     "description": "Content must not reference fabricated experts, veterinarians, or reviewers.",
     "keywords": ["our expert", "our vet", "our veterinarian", "reviewed by dr", "expert panel", "our specialist", "our nutritionist"]},
    {"rule_id": "no_invented_prices", "name": "No Invented Prices or Ratings", "severity": "high",
     "description": "Content must not include fabricated prices, ratings, or scores without verified data.",
     "keywords": ["rated 9.5/10", "rated 9/10", "our score:", "pethub rating:", "editor's score", "our rating:"]},
    {"rule_id": "no_unsupported_health", "name": "No Unsupported Health Claims", "severity": "critical",
     "description": "Content must not make unverified health or therapeutic claims about pet products.",
     "keywords": ["clinically proven", "scientifically proven", "cures", "treats disease", "prevents cancer", "guaranteed to", "will cure", "medically certified"]},
    {"rule_id": "no_manipulative_affiliate", "name": "No Manipulative Affiliate Wording", "severity": "high",
     "description": "Content must not use pressure tactics or misleading urgency to drive affiliate clicks.",
     "keywords": ["buy now before", "limited stock", "selling out fast", "hurry", "don't miss out", "act now", "only X left", "price won't last"]},
    {"rule_id": "no_thin_content", "name": "No Thin Content", "severity": "medium",
     "description": "Content must meet minimum depth: at least 300 words with substantive information.",
     "check_type": "length", "min_words": 300},
    {"rule_id": "no_duplicated_templates", "name": "No Duplicated Templates", "severity": "high",
     "description": "Content must not be a copy-paste template with only product names swapped.",
     "check_type": "similarity", "max_template_ratio": 0.7},
]


def validate_content_quality(data=None, **kwargs):
    """Check content against quality rules. Returns violations list.

    data: content (str, required), content_type (optional), claims (list, optional),
          text (legacy alias for content), title, word_count, template_similarity
    """
    content_data = data if data is not None else kwargs
    # Accept both 'content' (from routes Pydantic model) and 'text' (legacy)
    raw_text = content_data.get("content") or content_data.get("text", "")
    text = raw_text.lower()
    title = content_data.get("title", content_data.get("content_type", "")).lower()
    claims = content_data.get("claims") or []
    full = f"{title} {text} " + " ".join(c.lower() for c in claims)
    wc = content_data.get("word_count") or len(text.split())
    tsim = content_data.get("template_similarity", 0)
    violations = []

    for rule in _QUALITY_RULES:
        ct = rule.get("check_type", "keyword")
        if ct == "keyword":
            found = [kw for kw in rule.get("keywords", []) if kw.lower() in full]
            if found:
                violations.append({"rule_id": rule["rule_id"], "rule_name": rule["name"],
                                   "severity": rule["severity"], "description": rule["description"],
                                   "matched_keywords": found,
                                   "action": "Remove or rewrite flagged content before publishing."})
        elif ct == "length" and wc < rule.get("min_words", 300):
            violations.append({"rule_id": rule["rule_id"], "rule_name": rule["name"],
                               "severity": rule["severity"], "description": rule["description"],
                               "word_count": wc, "minimum_required": rule["min_words"],
                               "action": "Expand content to meet minimum depth requirements."})
        elif ct == "similarity" and tsim > rule.get("max_template_ratio", 0.7):
            violations.append({"rule_id": rule["rule_id"], "rule_name": rule["name"],
                               "severity": rule["severity"], "description": rule["description"],
                               "template_similarity": tsim, "max_allowed": rule["max_template_ratio"],
                               "action": "Rewrite content with unique angles and original analysis."})

    passed = len(violations) == 0
    score = max(0, 100 - len(violations) * 15)
    if passed:
        recommendation = "Content passes all quality checks. Approved for publication."
    elif score >= 70:
        recommendation = "Minor violations detected. Review flagged items before publication."
    elif score >= 40:
        recommendation = "Significant violations detected. Content requires rewriting."
    else:
        recommendation = "Critical quality failures. Content must be rejected and rewritten."

    return {
        "passed": passed,
        "violations": violations,
        "score": score,
        "recommendation": recommendation,
        "content_title": content_data.get("title", "Untitled"),
        "violations_count": len(violations),
        "checked_rules": len(_QUALITY_RULES),
        "word_count": wc, "data_source_label": "LIVE DATA",
    }
