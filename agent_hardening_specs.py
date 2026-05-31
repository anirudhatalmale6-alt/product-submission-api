"""
PetHub Phase 12 — Agent Hardening Architecture Specifications
5 new specialized agents to convert authority into visibility, citations, rankings, and revenue.

Each agent spec defines: purpose, port, data sources, API endpoints, scoring model,
integration points, and deployment plan.

Generated: 2026-05-31
"""

# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 1: AUTHORITY AGENT (Port 8109)
# ═══════════════════════════════════════════════════════════════════════════════

AUTHORITY_AGENT = {
    "name": "authority",
    "port": 8109,
    "purpose": "Continuously scores and tracks topical authority across all clusters. "
               "Owns authority scoring, cluster leadership measurement, moat tracking, "
               "and authority gap identification.",

    "data_sources": [
        "WordPress REST API (post metadata, categories, internal links)",
        "Google Search Console (impressions, clicks, avg position by query)",
        "SEO Agent audit results (on-page scores per post)",
        "Trust Evidence Engine (evidence coverage, claim validation rates)",
        "Cluster Expansion Engine (spoke counts, publish status)",
        "Internal Link Graph (link density, hub-spoke connectivity)",
    ],

    "core_modules": {
        "authority_scorer": {
            "description": "Calculates per-cluster authority score (0-100)",
            "inputs": ["spoke_count", "published_ratio", "avg_seo_score",
                       "internal_link_density", "evidence_coverage", "gsc_impressions"],
            "weights": {
                "content_depth": 0.25,       # spoke count * quality
                "search_presence": 0.20,     # GSC impressions + clicks
                "link_authority": 0.15,      # internal link density
                "trust_signals": 0.15,       # evidence coverage
                "content_freshness": 0.10,   # days since last update
                "competitive_position": 0.15 # avg position vs competitors
            },
            "output": "authority_score (0-100) per cluster"
        },
        "cluster_ownership_tracker": {
            "description": "Tracks which clusters PetHub 'owns' (top 3 positions)",
            "metrics": ["queries_owned", "queries_contested", "queries_absent"],
            "threshold": "owned = avg_position <= 3.0 for primary query"
        },
        "moat_tracker": {
            "description": "Measures defensive moat strength per cluster",
            "factors": ["content_volume_vs_competitor", "backlink_gap",
                        "freshness_advantage", "trust_signal_density"],
            "output": "moat_score (thin/moderate/strong/dominant)"
        },
        "authority_gap_finder": {
            "description": "Identifies clusters where authority is below potential",
            "method": "Compare spoke count vs search volume, link density vs peers",
            "output": "prioritized list of gaps with estimated impact"
        }
    },

    "api_endpoints": [
        "GET  /api/authority-agent/scores          — all cluster authority scores",
        "GET  /api/authority-agent/scores/{cluster} — single cluster detail",
        "GET  /api/authority-agent/ownership        — query ownership map",
        "GET  /api/authority-agent/moat             — moat strength per cluster",
        "GET  /api/authority-agent/gaps             — authority gaps ranked by impact",
        "POST /api/authority-agent/recalculate      — force full recalculation",
        "GET  /api/authority-agent/trends           — 30-day authority trend per cluster",
        "GET  /api/authority-agent/health           — agent health check",
    ],

    "integration_points": {
        "regression_engine": "Feeds authority dimension score to regression prevention",
        "content_agent": "Provides cluster priority list for content velocity decisions",
        "expansion_engine": "Informs which clusters need more spokes vs maintenance",
        "executive_dashboard": "Supplies authority KPIs for executive summary",
    },

    "scheduled_jobs": [
        {"job": "full_recalculate", "interval": "6h", "description": "Recalculate all cluster scores"},
        {"job": "ownership_check", "interval": "24h", "description": "Update query ownership from GSC"},
        {"job": "moat_assessment", "interval": "24h", "description": "Refresh moat strength metrics"},
    ],

    "existing_modules_to_integrate": [
        "seo_authority_centre.py — current authority scoring logic, adapt to per-cluster",
        "cluster_authority_scoring.py — cluster-level scoring foundation",
        "trust_authority.py — trust signal aggregation",
        "topical_authority.py — topical coverage calculations",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 2: VISIBILITY AGENT (Port 8110)
# ═══════════════════════════════════════════════════════════════════════════════

VISIBILITY_AGENT = {
    "name": "visibility",
    "port": 8110,
    "purpose": "Maximizes search visibility across Google, AI search engines, and "
               "featured snippets. Owns snippet optimization, citation tracking, "
               "AI visibility readiness, and query ownership strategy.",

    "data_sources": [
        "Google Search Console (queries, positions, CTR, impressions)",
        "WordPress REST API (content structure, schema markup)",
        "Indexing/Crawl/AI Search module (crawl status, AI readiness scores)",
        "SEO Agent (on-page optimization data)",
        "Answer Readiness module (answer-ready scores per page)",
    ],

    "core_modules": {
        "snippet_optimizer": {
            "description": "Identifies and optimizes for featured snippet opportunities",
            "methods": [
                "Detect query patterns that trigger snippets (what/how/why/best)",
                "Score content structure against snippet requirements",
                "Generate snippet-ready content blocks (paragraph/list/table)",
                "Track snippet wins/losses over time"
            ],
            "output": "snippet_opportunities with priority and content suggestions"
        },
        "ai_citation_tracker": {
            "description": "Monitors whether PetHub is cited by AI search engines",
            "targets": ["Google AI Overview", "Bing Chat", "Perplexity", "ChatGPT"],
            "method": "Periodic query sampling against AI engines, track citation presence",
            "output": "citation_rate per cluster, trending direction"
        },
        "query_ownership_engine": {
            "description": "Maps queries to ownership status and tracks changes",
            "states": ["owned (pos 1-3)", "competitive (pos 4-10)",
                        "opportunity (pos 11-20)", "absent (pos 20+)"],
            "output": "query_map with ownership transitions over time"
        },
        "visibility_readiness_scorer": {
            "description": "Scores each page's readiness for maximum visibility",
            "checks": ["quick_answer_block", "faq_schema_candidate", "table_of_contents",
                        "structured_headings", "entity_markup", "internal_link_depth",
                        "mobile_speed", "core_web_vitals"],
            "output": "readiness_score (0-100) per page"
        }
    },

    "api_endpoints": [
        "GET  /api/visibility/summary              — overall visibility metrics",
        "GET  /api/visibility/snippets              — snippet opportunities ranked",
        "GET  /api/visibility/snippets/{cluster}    — cluster snippet detail",
        "GET  /api/visibility/citations             — AI citation tracking results",
        "GET  /api/visibility/ownership             — query ownership map",
        "GET  /api/visibility/readiness             — page readiness scores",
        "POST /api/visibility/scan                  — trigger full visibility scan",
        "GET  /api/visibility/health                — agent health check",
    ],

    "integration_points": {
        "regression_engine": "Feeds visibility_readiness + citation_readiness scores",
        "authority_agent": "Shares query ownership data for authority calculations",
        "content_agent": "Provides snippet optimization suggestions for content generation",
        "seo_agent": "Coordinates on-page optimizations for visibility gains",
    },

    "scheduled_jobs": [
        {"job": "gsc_query_sync", "interval": "6h", "description": "Sync query data from GSC"},
        {"job": "snippet_scan", "interval": "12h", "description": "Scan for snippet opportunities"},
        {"job": "readiness_audit", "interval": "24h", "description": "Score all pages for visibility readiness"},
        {"job": "citation_sample", "interval": "48h", "description": "Sample AI engines for citation presence"},
    ],

    "existing_modules_to_integrate": [
        "indexing_crawl_ai_search.py — AI readiness scoring, crawl monitoring",
        "answer_readiness.py — answer-ready content scoring",
        "bulk_answer_readiness.py — batch readiness scoring",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 3: COMPETITOR AGENT (Port 8111)
# ═══════════════════════════════════════════════════════════════════════════════

COMPETITOR_AGENT = {
    "name": "competitor",
    "port": 8111,
    "purpose": "Monitors and benchmarks against key competitors: Pets at Home, Cats.com, "
               "Zooplus, Purina, Rover. Tracks their content moves, authority changes, "
               "and identifies displacement opportunities.",

    "competitors": [
        {"name": "Pets at Home", "domain": "petsathome.com", "priority": "primary"},
        {"name": "Cats.com", "domain": "cats.com", "priority": "primary"},
        {"name": "Zooplus", "domain": "zooplus.co.uk", "priority": "secondary"},
        {"name": "Purina", "domain": "purina.co.uk", "priority": "secondary"},
        {"name": "Rover", "domain": "rover.com", "priority": "secondary"},
    ],

    "data_sources": [
        "Google Search Console (position data for shared queries)",
        "SERP sampling (competitor positions for target queries)",
        "Content structure analysis (competitor page audits)",
        "Authority Agent (PetHub's own authority for comparison)",
    ],

    "core_modules": {
        "competitive_intelligence": {
            "description": "Tracks competitor positioning across shared queries",
            "metrics": ["shared_queries_count", "position_advantage",
                        "content_gap_count", "authority_differential"],
            "output": "competitor_scorecard per competitor"
        },
        "displacement_engine": {
            "description": "Identifies queries where PetHub can displace competitors",
            "method": "Find queries where competitor is pos 1-5 and PetHub is pos 6-15, "
                      "prioritize by search volume and content quality gap",
            "output": "displacement_opportunities ranked by feasibility * impact"
        },
        "content_gap_tracker": {
            "description": "Identifies topics competitors cover that PetHub doesn't",
            "method": "Compare competitor sitemaps/categories against PetHub's cluster map",
            "output": "content_gaps with estimated search volume and priority"
        },
        "competitor_alert_system": {
            "description": "Detects significant competitor moves",
            "triggers": [
                "Competitor gains featured snippet PetHub previously held",
                "New competitor content in PetHub's core clusters",
                "Competitor position improvement > 5 places on target query",
                "New competitor backlink campaign detected"
            ],
            "output": "alerts with severity and recommended response"
        }
    },

    "api_endpoints": [
        "GET  /api/competitor/summary               — competitive landscape overview",
        "GET  /api/competitor/scorecard/{competitor} — single competitor detail",
        "GET  /api/competitor/displacement           — displacement opportunities",
        "GET  /api/competitor/gaps                   — content gaps vs competitors",
        "GET  /api/competitor/alerts                 — recent competitor alerts",
        "POST /api/competitor/scan                   — trigger competitive analysis",
        "GET  /api/competitor/health                 — agent health check",
    ],

    "integration_points": {
        "authority_agent": "Provides competitive position data for moat calculations",
        "visibility_agent": "Shares snippet contest data (who holds which snippets)",
        "content_agent": "Feeds content gap priorities for content velocity decisions",
        "expansion_engine": "Informs cluster expansion priorities based on competitive gaps",
    },

    "scheduled_jobs": [
        {"job": "competitor_scan", "interval": "24h", "description": "Full competitive position scan"},
        {"job": "content_gap_update", "interval": "48h", "description": "Refresh content gap analysis"},
        {"job": "alert_check", "interval": "6h", "description": "Check for competitor position changes"},
    ],

    "existing_modules_to_integrate": [
        "competitor_benchmark.py — existing competitor trust benchmark data",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 4: QA AGENT (Port 8112)
# ═══════════════════════════════════════════════════════════════════════════════

QA_AGENT = {
    "name": "qa",
    "port": 8112,
    "purpose": "Automated regression testing, endpoint validation, dashboard verification, "
               "and quality gate enforcement. Ensures platform quality never degrades below "
               "90% threshold across all dimensions.",

    "data_sources": [
        "All 9 agent /api/status endpoints",
        "All 8 dashboard endpoints",
        "WordPress REST API (content validation)",
        "Regression Prevention Engine (quality scores, remediation tasks)",
        "Content Standards Agent (compliance rates)",
    ],

    "core_modules": {
        "endpoint_validator": {
            "description": "Validates all API endpoints return correct responses",
            "checks": [
                "HTTP status code",
                "Response time < 5s",
                "JSON schema validation",
                "Required fields present",
                "Data freshness (not stale)"
            ],
            "coverage": "All agent APIs + all dashboard APIs + WP REST API"
        },
        "dashboard_verifier": {
            "description": "Verifies dashboards render correctly and show fresh data",
            "method": "Headless browser screenshot + visual diff against baseline",
            "checks": ["renders without error", "shows current data",
                        "all sections populated", "no broken components"]
        },
        "regression_test_runner": {
            "description": "Runs regression test suite on schedule",
            "test_suites": [
                "agent_health_suite — all 9 agents respond correctly",
                "dashboard_render_suite — all 8 dashboards load",
                "content_compliance_suite — sample posts meet standards",
                "api_contract_suite — API responses match schemas",
                "data_freshness_suite — no stale data in dashboards"
            ],
            "output": "test_report with pass/fail counts and details"
        },
        "quality_gate_enforcer": {
            "description": "Blocks content publication when quality gates fail",
            "gates": [
                "trust_lint — all claims have evidence",
                "structure_check — all required sections present",
                "metadata_check — SEO title, meta desc, focus keyword set",
                "link_check — internal links present, no broken links",
                "disclosure_check — editorial + affiliate disclosures present",
                "image_check — 4-6 images with alt text",
                "approval_check — content approved for publication"
            ],
            "enforcement": "Returns gate_pass boolean + detailed check results"
        }
    },

    "api_endpoints": [
        "GET  /api/qa/summary                — overall QA status",
        "GET  /api/qa/tests                  — latest test results",
        "POST /api/qa/run                    — trigger full test suite",
        "GET  /api/qa/endpoints              — endpoint validation results",
        "GET  /api/qa/dashboards             — dashboard verification results",
        "POST /api/qa/gate-check/{post_id}   — run quality gates on a post",
        "GET  /api/qa/history                — test run history",
        "GET  /api/qa/health                 — agent health check",
    ],

    "integration_points": {
        "regression_engine": "Primary consumer — feeds QA compliance score",
        "content_agent": "Gate enforcement before any content update/publish",
        "expansion_engine": "Gate check on spoke status transitions",
        "manager_agent": "Reports to operations centre dashboard",
    },

    "scheduled_jobs": [
        {"job": "full_regression_suite", "interval": "6h", "description": "Run all regression tests"},
        {"job": "endpoint_health_check", "interval": "2m", "description": "Quick endpoint ping"},
        {"job": "dashboard_render_check", "interval": "1h", "description": "Verify dashboard rendering"},
        {"job": "data_freshness_check", "interval": "30m", "description": "Check for stale data"},
    ],

    "existing_modules_to_integrate": [
        "regression_prevention.py — core quality scoring engine (just deployed)",
        "qa_api.py — existing QA API routes",
        "qa_lab.py — simulation testing lab",
        "qa_runner.py — test execution engine",
        "compliance_checker.py — content compliance validation",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 5: CONTENT STANDARDS AGENT (Port 8113)
# ═══════════════════════════════════════════════════════════════════════════════

CONTENT_STANDARDS_AGENT = {
    "name": "content_standards",
    "port": 8113,
    "purpose": "Validates all content against the permanent platform standards. Ensures "
               "every post (published and draft) includes all 22 mandatory elements. "
               "Provides continuous compliance monitoring and remediation suggestions.",

    "mandatory_elements": [
        "focus_keyword", "seo_title", "meta_description",
        "table_of_contents", "quick_answer", "at_a_glance",
        "faq_section", "key_terms", "sources_references",
        "editorial_disclosure", "author_box", "internal_links",
        "related_reading", "trust_footer", "affiliate_disclosure",
        "amazon_integration", "comparison_table", "common_mistakes",
        "decision_pathway", "key_takeaways", "images_4_6",
        "mobile_friendly"
    ],

    "data_sources": [
        "WordPress REST API (post content, metadata, Rank Math data)",
        "Regression Prevention Engine (content compliance checks)",
        "Trust Evidence Engine (evidence coverage data)",
        "Image tracking (media library counts per post)",
    ],

    "core_modules": {
        "standard_validator": {
            "description": "Checks each post against all 22 mandatory elements",
            "method": "Content parsing + regex matching + metadata API checks",
            "output": "compliance_report per post (22 checks, pass/fail each)"
        },
        "bulk_compliance_auditor": {
            "description": "Audits all published + draft posts for compliance",
            "method": "Batch WordPress API calls, parallel validation",
            "output": "platform_compliance_rate + per-post breakdown"
        },
        "remediation_generator": {
            "description": "Generates specific fix instructions for non-compliant posts",
            "method": "For each failed check, generate actionable remediation step",
            "examples": [
                "Missing FAQ: 'Add FAQ section with 5-7 questions after Key Takeaways'",
                "Missing images: 'Add 4-6 Pexels images with descriptive alt text'",
                "Missing affiliate: 'Add Amazon UK product section with pethubonline-21 tag'"
            ]
        },
        "template_enforcer": {
            "description": "Ensures content generation templates include all standards",
            "method": "Validates template output against standards before content creation",
            "output": "template_compliance status + missing elements"
        },
        "compliance_trend_tracker": {
            "description": "Tracks compliance rates over time per standard element",
            "metrics": ["per_element_compliance_rate", "overall_platform_rate",
                        "trend_direction", "worst_performing_elements"],
            "output": "compliance_dashboard_data with 30-day trends"
        }
    },

    "api_endpoints": [
        "GET  /api/content-standards/summary        — platform compliance overview",
        "GET  /api/content-standards/audit/{post_id} — single post audit",
        "POST /api/content-standards/bulk-audit      — audit all posts",
        "GET  /api/content-standards/compliance-rate  — per-element compliance rates",
        "GET  /api/content-standards/non-compliant    — list non-compliant posts",
        "GET  /api/content-standards/remediation      — remediation task queue",
        "POST /api/content-standards/validate-template — validate a content template",
        "GET  /api/content-standards/trends           — compliance trend data",
        "GET  /api/content-standards/health           — agent health check",
    ],

    "integration_points": {
        "regression_engine": "Feeds content compliance rate into quality scoring",
        "content_agent": "Pre-publish validation, blocks non-compliant content",
        "qa_agent": "Provides compliance data for quality gate enforcement",
        "expansion_engine": "Validates spoke content meets standards before status change",
    },

    "scheduled_jobs": [
        {"job": "full_compliance_audit", "interval": "24h", "description": "Audit all posts"},
        {"job": "new_content_check", "interval": "1h", "description": "Check recently modified posts"},
        {"job": "trend_snapshot", "interval": "24h", "description": "Record daily compliance snapshot"},
    ],

    "existing_modules_to_integrate": [
        "regression_prevention.py — content standard checks (22 elements)",
        "compliance_checker.py — existing compliance validation logic",
        "compliance_api.py — existing compliance API routes",
        "content_quality_scorer.py — content quality scoring",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# DEPLOYMENT ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════════════

DEPLOYMENT_PLAN = {
    "port_allocation": {
        "authority_agent": 8109,
        "visibility_agent": 8110,
        "competitor_agent": 8111,
        "qa_agent": 8112,
        "content_standards_agent": 8113,
    },

    "directory_structure": {
        "authority": "/opt/pethub-agents/authority-agent/",
        "visibility": "/opt/pethub-agents/visibility-agent/",
        "competitor": "/opt/pethub-agents/competitor-agent/",
        "qa": "/opt/pethub-agents/qa-agent/",
        "content_standards": "/opt/pethub-agents/content-standards-agent/",
    },

    "shared_dependencies": [
        "httpx — async HTTP client for inter-agent communication",
        "fastapi + uvicorn — API framework",
        "apscheduler — scheduled job execution",
        "pydantic — data validation",
    ],

    "manager_registration": "Each agent registers with manager on startup via POST /api/agents/register. "
                            "Manager health monitor pings /api/status every 2 minutes.",

    "nginx_proxy": "Each agent exposed via nginx reverse proxy at "
                   "https://167.99.198.145/{agent-name}/ with basic auth.",

    "implementation_order": [
        "1. Content Standards Agent — most foundational, needed by QA and regression",
        "2. QA Agent — builds on content standards + regression engine",
        "3. Authority Agent — needs GSC data + cluster expansion data",
        "4. Visibility Agent — needs authority data + GSC data",
        "5. Competitor Agent — needs authority + visibility data for comparison",
    ],

    "estimated_effort_per_agent": "1-2 sessions each (core module + routes + deployment + dashboard)",
}


# ═══════════════════════════════════════════════════════════════════════════════
# INTER-AGENT COMMUNICATION MAP
# ═══════════════════════════════════════════════════════════════════════════════

COMMUNICATION_MAP = {
    "regression_engine": {
        "consumes_from": ["authority_agent", "visibility_agent", "qa_agent", "content_standards_agent"],
        "description": "Central quality scoring. Pulls dimension scores from specialized agents."
    },
    "authority_agent": {
        "consumes_from": ["visibility_agent", "competitor_agent"],
        "provides_to": ["regression_engine", "content_agent", "expansion_engine"],
    },
    "visibility_agent": {
        "consumes_from": ["authority_agent", "seo_agent"],
        "provides_to": ["regression_engine", "authority_agent", "content_agent"],
    },
    "competitor_agent": {
        "consumes_from": ["authority_agent", "visibility_agent"],
        "provides_to": ["authority_agent", "content_agent", "expansion_engine"],
    },
    "qa_agent": {
        "consumes_from": ["all_agents", "content_standards_agent"],
        "provides_to": ["regression_engine", "manager_agent"],
    },
    "content_standards_agent": {
        "consumes_from": ["wordpress_api", "trust_evidence_engine"],
        "provides_to": ["qa_agent", "regression_engine", "content_agent"],
    },
}
