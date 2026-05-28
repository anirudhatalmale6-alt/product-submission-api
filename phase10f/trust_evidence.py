"""
PetHub 10G: Trust Evidence Layer
Content claim classification, trust linting, evidence gating, and publish gates.
Standalone module — does not import truthful_ops.
"""

import json
import logging
import re
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

import psycopg2
import psycopg2.extras

logger = logging.getLogger("trust_evidence")

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "database": "agent_manager",
    "user": "productapi",
    "password": "productapi",
}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _get_conn():
    return psycopg2.connect(**DB_CONFIG)


@contextmanager
def _db(autocommit=False):
    conn = _get_conn()
    if autocommit:
        conn.autocommit = True
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur
        if not autocommit:
            conn.commit()
    except Exception:
        if not autocommit:
            conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


# ============================================================
# TABLE CREATION
# ============================================================

def create_trust_tables():
    """Create all trust_* tables if they don't exist."""
    ddl = """
    CREATE TABLE IF NOT EXISTS trust_evidence (
        id SERIAL PRIMARY KEY,
        evidence_id VARCHAR(32) UNIQUE NOT NULL,
        content_id INTEGER,
        evidence_type VARCHAR(64) NOT NULL CHECK (evidence_type IN (
            'live_verified','source_attributed','manufacturer_claim',
            'editorial_inference','estimated_proxy','simulated_modelled','missing_insufficient'
        )),
        source_url TEXT,
        source_name TEXT,
        verification_date DATE,
        verified_by VARCHAR(128),
        confidence_score INTEGER DEFAULT 50 CHECK (confidence_score BETWEEN 0 AND 100),
        claim_text TEXT,
        supporting_text TEXT,
        status VARCHAR(32) DEFAULT 'active' CHECK (status IN ('active','disputed','expired','retracted')),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS trust_claims (
        id SERIAL PRIMARY KEY,
        claim_id VARCHAR(32) UNIQUE NOT NULL,
        content_id INTEGER,
        claim_text TEXT,
        claim_type VARCHAR(64) NOT NULL CHECK (claim_type IN (
            'product_performance','health_wellbeing','veterinary_behaviour',
            'urgency_discount','testing_review','community_social_proof','general_editorial'
        )),
        risk_level VARCHAR(16) DEFAULT 'low' CHECK (risk_level IN ('low','medium','high','critical')),
        evidence_ids TEXT[],
        evidence_sufficient BOOLEAN DEFAULT FALSE,
        requires_disclosure BOOLEAN DEFAULT FALSE,
        requires_expert_source BOOLEAN DEFAULT FALSE,
        lint_status VARCHAR(16) DEFAULT 'unchecked' CHECK (lint_status IN ('pass','warn','fail','unchecked')),
        resolution_action TEXT,
        reviewer VARCHAR(128),
        reviewed_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS trust_lint_results (
        id SERIAL PRIMARY KEY,
        lint_id VARCHAR(32) UNIQUE NOT NULL,
        content_id INTEGER,
        rule_name VARCHAR(64),
        severity VARCHAR(16) CHECK (severity IN ('info','warning','error','blocker')),
        passed BOOLEAN DEFAULT TRUE,
        detail TEXT,
        snippet TEXT,
        fix_suggestion TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS trust_audit (
        id SERIAL PRIMARY KEY,
        audit_id VARCHAR(32) UNIQUE NOT NULL,
        content_id INTEGER,
        content_title TEXT,
        content_url TEXT,
        trust_state VARCHAR(32) DEFAULT 'untested' CHECK (trust_state IN (
            'untested','lint_pass','lint_fail','evidence_sufficient',
            'evidence_insufficient','approved_publish','blocked','needs_review'
        )),
        evidence_state TEXT,
        risk_state VARCHAR(16) DEFAULT 'low' CHECK (risk_state IN ('low','medium','high','critical')),
        approval_required BOOLEAN DEFAULT FALSE,
        blocking_reason TEXT,
        recommended_action TEXT,
        last_audited TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS trust_publish_gates (
        id SERIAL PRIMARY KEY,
        gate_id VARCHAR(32) UNIQUE NOT NULL,
        content_id INTEGER,
        gate_type VARCHAR(32) CHECK (gate_type IN (
            'trust_lint','evidence_check','risk_review','owner_approval'
        )),
        status VARCHAR(16) DEFAULT 'pending' CHECK (status IN (
            'pending','passed','failed','bypassed','expired'
        )),
        required BOOLEAN DEFAULT TRUE,
        checked_at TIMESTAMPTZ,
        checked_by VARCHAR(128),
        result_detail TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
    with _db() as cur:
        cur.execute(ddl)
    logger.info("trust_* tables created/verified")
    return {"status": "ok", "tables": ["trust_evidence","trust_claims","trust_lint_results","trust_audit","trust_publish_gates"]}


# ============================================================
# EVIDENCE CLASSIFICATION
# ============================================================

EVIDENCE_TYPES = (
    "live_verified","source_attributed","manufacturer_claim",
    "editorial_inference","estimated_proxy","simulated_modelled","missing_insufficient"
)


def classify_evidence(
    content_id: int,
    claim_text: str,
    source_url: str = "",
    source_name: str = "",
    evidence_type: str = "editorial_inference",
    confidence_score: int = 50,
    verified_by: str = None,
) -> dict:
    if evidence_type not in EVIDENCE_TYPES:
        evidence_type = "editorial_inference"
    evidence_id = _gen_id("evd")
    try:
        with _db() as cur:
            cur.execute("""
                INSERT INTO trust_evidence (
                    evidence_id, content_id, evidence_type, source_url, source_name,
                    confidence_score, claim_text, verified_by, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()) RETURNING *
            """, (evidence_id, content_id, evidence_type, source_url, source_name,
                  confidence_score, claim_text, verified_by))
            row = cur.fetchone()
        return dict(row)
    except Exception as e:
        logger.error(f"classify_evidence failed: {e}")
        return {"error": str(e), "evidence_id": evidence_id}


def get_evidence(content_id: int = None, evidence_type: str = None, limit: int = 50) -> list:
    clauses, params = [], []
    if content_id is not None:
        clauses.append("content_id=%s"); params.append(content_id)
    if evidence_type:
        clauses.append("evidence_type=%s"); params.append(evidence_type)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)
    try:
        with _db() as cur:
            cur.execute(f"SELECT * FROM trust_evidence {where} ORDER BY created_at DESC LIMIT %s", params)
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"get_evidence failed: {e}")
        return []


def update_evidence_status(evidence_id: str, status: str, reason: str = "") -> dict:
    try:
        with _db() as cur:
            cur.execute("""
                UPDATE trust_evidence SET status=%s, supporting_text=COALESCE(NULLIF(%s,''), supporting_text),
                updated_at=NOW() WHERE evidence_id=%s RETURNING *
            """, (status, reason, evidence_id))
            row = cur.fetchone()
        return dict(row) if row else {"error": "not_found"}
    except Exception as e:
        logger.error(f"update_evidence_status failed: {e}")
        return {"error": str(e)}


# ============================================================
# CLAIM RISK
# ============================================================

_CLAIM_RISK_MAP = {
    "veterinary_behaviour": "critical",
    "health_wellbeing": "high",
    "product_performance": "medium",
    "testing_review": "medium",
    "urgency_discount": "medium",
    "community_social_proof": "low",
    "general_editorial": "low",
}

_EXPERT_REQUIRED = {"veterinary_behaviour", "health_wellbeing"}
_DISCLOSURE_REQUIRED = {"urgency_discount", "testing_review"}


def assess_claim(
    content_id: int,
    claim_text: str,
    claim_type: str,
    evidence_ids: list = None,
) -> dict:
    claim_id = _gen_id("clm")
    risk_level = _CLAIM_RISK_MAP.get(claim_type, "low")
    requires_expert = claim_type in _EXPERT_REQUIRED
    requires_disclosure = claim_type in _DISCLOSURE_REQUIRED
    evidence_sufficient = bool(evidence_ids)
    if risk_level in ("high", "critical") and not evidence_sufficient:
        lint_status = "fail"
    elif risk_level == "medium" and not evidence_sufficient:
        lint_status = "warn"
    else:
        lint_status = "pass"

    try:
        with _db() as cur:
            cur.execute("""
                INSERT INTO trust_claims (
                    claim_id, content_id, claim_text, claim_type, risk_level,
                    evidence_ids, evidence_sufficient, requires_disclosure,
                    requires_expert_source, lint_status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()) RETURNING *
            """, (claim_id, content_id, claim_text, claim_type, risk_level,
                  evidence_ids or [], evidence_sufficient, requires_disclosure,
                  requires_expert, lint_status))
            row = cur.fetchone()
        return dict(row)
    except Exception as e:
        logger.error(f"assess_claim failed: {e}")
        return {"error": str(e), "claim_id": claim_id}


def get_claims(content_id: int = None, risk_level: str = None, lint_status: str = None, limit: int = 50) -> list:
    clauses, params = [], []
    if content_id is not None:
        clauses.append("content_id=%s"); params.append(content_id)
    if risk_level:
        clauses.append("risk_level=%s"); params.append(risk_level)
    if lint_status:
        clauses.append("lint_status=%s"); params.append(lint_status)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)
    try:
        with _db() as cur:
            cur.execute(f"SELECT * FROM trust_claims {where} ORDER BY created_at DESC LIMIT %s", params)
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"get_claims failed: {e}")
        return []


# ============================================================
# TRUST LINT ENGINE
# ============================================================

_LINT_RULES = [
    {
        "name": "fake_authority",
        "severity": "blocker",
        "pattern": r"(our experts|our team of|we tested|our veterinarians)",
        "fix": "Remove unsupported authority claims or link to specific named expert/source",
        "scope": "body",
    },
    {
        "name": "implied_interview",
        "severity": "error",
        "pattern": r"(we spoke with|according to our conversation)",
        "fix": "Cite the actual interview source with name, title, and date",
        "scope": "body",
    },
    {
        "name": "unsupported_testing",
        "severity": "blocker",
        "pattern": r"(we tested|in our tests|our testing shows)",
        "fix": "Provide structured testing evidence or remove claim",
        "scope": "body",
    },
    {
        "name": "vague_expert",
        "severity": "error",
        "pattern": r"(experts say|professionals recommend|vets recommend|specialists agree)",
        "fix": "Name the expert and provide credentials or source link",
        "scope": "body",
    },
    {
        "name": "filler_padding",
        "severity": "warning",
        "pattern": r"(in conclusion,|as we all know,|it goes without saying|needless to say)",
        "fix": "Remove filler language to improve content quality score",
        "scope": "body",
    },
    {
        "name": "missing_disclosure",
        "severity": "error",
        "pattern": r"(affiliate link|sponsored|paid partnership|commission)",
        "fix": "Add FTC-compliant disclosure at top of page",
        "scope": "body",
        "invert": True,  # flag if sponsored content exists but no disclosure header
    },
    {
        "name": "weak_evidence",
        "severity": "warning",
        "pattern": r"(studies show|research indicates|research suggests|science says)",
        "fix": "Add citation link or DOI for the referenced study",
        "scope": "body",
    },
    {
        "name": "templated_trust",
        "severity": "info",
        "pattern": r"(our editorial team|our strict editorial|we only recommend products we believe)",
        "fix": "Ensure editorial policy language links to /editorial-policy page",
        "scope": "body",
    },
    {
        "name": "product_count_mismatch",
        "severity": "warning",
        "pattern": None,  # handled in code
        "fix": "Align product count in title with actual products reviewed in body",
        "scope": "special",
    },
    {
        "name": "duplicate_h1",
        "severity": "error",
        "pattern": None,
        "fix": "Ensure only one H1 tag per page",
        "scope": "special",
    },
    {
        "name": "weak_meta_title",
        "severity": "warning",
        "pattern": None,
        "fix": "Keep meta title between 30-60 characters",
        "scope": "meta",
    },
    {
        "name": "weak_meta_desc",
        "severity": "warning",
        "pattern": None,
        "fix": "Keep meta description between 50-160 characters",
        "scope": "meta",
    },
]


def run_trust_lint(
    content_id: int,
    content_title: str,
    content_body: str,
    meta_title: str = "",
    meta_description: str = "",
) -> dict:
    results = []
    passed = warnings = errors = blockers = 0
    body_lower = content_body.lower()

    def _save_result(rule_name, severity, rule_passed, detail, snippet="", fix=""):
        lint_id = _gen_id("lnt")
        try:
            with _db() as cur:
                cur.execute("""
                    INSERT INTO trust_lint_results (lint_id, content_id, rule_name, severity, passed, detail, snippet, fix_suggestion, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, (lint_id, content_id, rule_name, severity, rule_passed, detail, snippet[:300], fix))
        except Exception as e:
            logger.error(f"lint save failed for {rule_name}: {e}")
        return {"lint_id": lint_id, "rule": rule_name, "severity": severity, "passed": rule_passed, "detail": detail, "snippet": snippet[:200], "fix": fix}

    for rule in _LINT_RULES:
        name = rule["name"]
        severity = rule["severity"]
        fix = rule["fix"]

        if rule["scope"] == "body" and rule.get("pattern"):
            matches = re.findall(rule["pattern"], body_lower, re.IGNORECASE)
            if rule.get("invert"):
                # For missing_disclosure: if body has affiliate/sponsored words, expect disclosure in title/meta
                if matches and "disclosure" not in body_lower and "sponsored" not in content_title.lower():
                    r = _save_result(name, severity, False, "Potentially sponsored/affiliate content without disclosure", matches[0] if matches else "", fix)
                    results.append(r)
                    if severity == "blocker": blockers += 1
                    elif severity == "error": errors += 1
                    elif severity == "warning": warnings += 1
                else:
                    r = _save_result(name, severity, True, "Disclosure check passed", "", fix)
                    results.append(r); passed += 1
            else:
                if matches:
                    snippet = matches[0]
                    r = _save_result(name, severity, False, f"Found unsupported claim: '{snippet}'", snippet, fix)
                    results.append(r)
                    if severity == "blocker": blockers += 1
                    elif severity == "error": errors += 1
                    elif severity == "warning": warnings += 1
                else:
                    r = _save_result(name, severity, True, "No violations found", "", fix)
                    results.append(r); passed += 1

        elif rule["scope"] == "special":
            if name == "product_count_mismatch":
                m = re.search(r"\b(top\s+)?(\d+)\b", content_title.lower())
                if m:
                    title_count = int(m.group(2))
                    # Count h2/h3 product entries as proxy
                    body_count = len(re.findall(r"<h[23][^>]*>", content_body, re.IGNORECASE))
                    if body_count > 0 and abs(body_count - title_count) > 2:
                        r = _save_result(name, severity, False, f"Title implies {title_count} products, body has ~{body_count} sections", "", fix)
                        results.append(r); warnings += 1
                        continue
                r = _save_result(name, severity, True, "Product count consistent or not applicable", "", fix)
                results.append(r); passed += 1

            elif name == "duplicate_h1":
                h1_count = len(re.findall(r"<h1[^>]*>", content_body, re.IGNORECASE))
                if h1_count > 1:
                    r = _save_result(name, severity, False, f"Found {h1_count} H1 tags (expected 1)", "", fix)
                    results.append(r); errors += 1
                else:
                    r = _save_result(name, severity, True, f"H1 count OK ({h1_count})", "", fix)
                    results.append(r); passed += 1

        elif rule["scope"] == "meta":
            if name == "weak_meta_title":
                mt = meta_title.strip()
                if not mt or len(mt) > 60:
                    detail = "Meta title empty" if not mt else f"Meta title too long ({len(mt)} chars)"
                    r = _save_result(name, severity, False, detail, mt[:60], fix)
                    results.append(r); warnings += 1
                else:
                    r = _save_result(name, severity, True, f"Meta title OK ({len(mt)} chars)", "", fix)
                    results.append(r); passed += 1

            elif name == "weak_meta_desc":
                md = meta_description.strip()
                if not md or len(md) > 160:
                    detail = "Meta description empty" if not md else f"Meta description too long ({len(md)} chars)"
                    r = _save_result(name, severity, False, detail, md[:160], fix)
                    results.append(r); warnings += 1
                else:
                    r = _save_result(name, severity, True, f"Meta description OK ({len(md)} chars)", "", fix)
                    results.append(r); passed += 1

    total_checks = len(results)
    return {
        "content_id": content_id,
        "total_checks": total_checks,
        "passed": passed,
        "warnings": warnings,
        "errors": errors,
        "blockers": blockers,
        "lint_score": round(passed / max(total_checks, 1) * 100, 1),
        "results": results,
        "timestamp": _now_iso(),
    }


# ============================================================
# TRUST AUDIT
# ============================================================

def audit_content(content_id: int, content_title: str, content_url: str) -> dict:
    """Run lint, check evidence, and determine overall trust state."""
    audit_id = _gen_id("aud")
    try:
        # Run lint using title as both title and a minimal body if we don't have body
        lint = run_trust_lint(content_id, content_title, content_title)
        blockers = lint["blockers"]
        errors = lint["errors"]

        # Check evidence
        evidence_list = get_evidence(content_id=content_id)
        claims_list = get_claims(content_id=content_id)
        high_risk_claims = [c for c in claims_list if c.get("risk_level") in ("high", "critical")]

        # Determine trust state
        if blockers > 0:
            trust_state = "lint_fail"
            blocking_reason = f"{blockers} blocker(s) in lint"
        elif errors > 0:
            trust_state = "lint_fail"
            blocking_reason = f"{errors} error(s) in lint"
        elif high_risk_claims and not all(c.get("evidence_sufficient") for c in high_risk_claims):
            trust_state = "evidence_insufficient"
            blocking_reason = "High-risk claims lack sufficient evidence"
        elif lint["warnings"] > 0:
            trust_state = "lint_pass"
            blocking_reason = None
        else:
            trust_state = "lint_pass"
            blocking_reason = None

        # Overall risk state
        if blockers > 0 or any(c.get("risk_level") == "critical" for c in claims_list):
            risk_state = "critical"
        elif errors > 0 or any(c.get("risk_level") == "high" for c in claims_list):
            risk_state = "high"
        elif lint["warnings"] > 0:
            risk_state = "medium"
        else:
            risk_state = "low"

        approval_required = risk_state in ("high", "critical")
        evidence_state = f"{len(evidence_list)} evidence items, {len(claims_list)} claims assessed"
        recommended_action = (
            "Block publication" if trust_state == "lint_fail" else
            "Resolve evidence gaps" if trust_state == "evidence_insufficient" else
            "Review warnings before publish" if lint["warnings"] > 0 else
            "Safe to publish"
        )

        with _db() as cur:
            cur.execute("""
                INSERT INTO trust_audit (
                    audit_id, content_id, content_title, content_url, trust_state,
                    evidence_state, risk_state, approval_required, blocking_reason,
                    recommended_action, last_audited, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW())
                ON CONFLICT (audit_id) DO UPDATE SET
                    trust_state=EXCLUDED.trust_state, evidence_state=EXCLUDED.evidence_state,
                    risk_state=EXCLUDED.risk_state, approval_required=EXCLUDED.approval_required,
                    blocking_reason=EXCLUDED.blocking_reason, recommended_action=EXCLUDED.recommended_action,
                    last_audited=NOW(), updated_at=NOW()
                RETURNING *
            """, (audit_id, content_id, content_title, content_url, trust_state,
                  evidence_state, risk_state, approval_required, blocking_reason,
                  recommended_action))
            row = cur.fetchone()

        result = dict(row)
        result["lint_summary"] = {"passed": lint["passed"], "warnings": lint["warnings"], "errors": lint["errors"], "blockers": lint["blockers"]}
        return result
    except Exception as e:
        logger.error(f"audit_content failed: {e}")
        return {"error": str(e), "audit_id": audit_id}


def get_audit(content_id: int = None, trust_state: str = None, limit: int = 50) -> list:
    clauses, params = [], []
    if content_id is not None:
        clauses.append("content_id=%s"); params.append(content_id)
    if trust_state:
        clauses.append("trust_state=%s"); params.append(trust_state)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)
    try:
        with _db() as cur:
            cur.execute(f"SELECT * FROM trust_audit {where} ORDER BY last_audited DESC LIMIT %s", params)
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"get_audit failed: {e}")
        return []


def get_audit_summary() -> dict:
    try:
        with _db() as cur:
            cur.execute("SELECT trust_state, COUNT(*) as c FROM trust_audit GROUP BY trust_state")
            by_trust = {r["trust_state"]: r["c"] for r in cur.fetchall()}
            cur.execute("SELECT risk_state, COUNT(*) as c FROM trust_audit GROUP BY risk_state")
            by_risk = {r["risk_state"]: r["c"] for r in cur.fetchall()}
            cur.execute("SELECT COUNT(*) as total FROM trust_audit")
            total = cur.fetchone()["total"]
        return {"total": total, "by_trust_state": by_trust, "by_risk_state": by_risk, "timestamp": _now_iso()}
    except Exception as e:
        logger.error(f"get_audit_summary failed: {e}")
        return {"error": str(e)}


# ============================================================
# PUBLISH GATING
# ============================================================

GATE_TYPES = ("trust_lint", "evidence_check", "risk_review", "owner_approval")


def create_publish_gate(content_id: int, gate_type: str, required: bool = True) -> dict:
    if gate_type not in GATE_TYPES:
        return {"error": f"Invalid gate_type: {gate_type}"}
    gate_id = _gen_id("gate")
    try:
        with _db() as cur:
            cur.execute("""
                INSERT INTO trust_publish_gates (gate_id, content_id, gate_type, status, required, created_at)
                VALUES (%s, %s, %s, 'pending', %s, NOW()) RETURNING *
            """, (gate_id, content_id, gate_type, required))
            row = cur.fetchone()
        return dict(row)
    except Exception as e:
        logger.error(f"create_publish_gate failed: {e}")
        return {"error": str(e), "gate_id": gate_id}


def update_gate(gate_id: str, status: str, checked_by: str = "system", result_detail: str = "") -> dict:
    try:
        with _db() as cur:
            cur.execute("""
                UPDATE trust_publish_gates SET status=%s, checked_by=%s, result_detail=%s, checked_at=NOW()
                WHERE gate_id=%s RETURNING *
            """, (status, checked_by, result_detail, gate_id))
            row = cur.fetchone()
        return dict(row) if row else {"error": "not_found"}
    except Exception as e:
        logger.error(f"update_gate failed: {e}")
        return {"error": str(e)}


def check_publish_gates(content_id: int) -> dict:
    """Auto-create and check all gates for a content item, returns gate status."""
    try:
        # Ensure all gate types exist for this content
        with _db() as cur:
            cur.execute("SELECT gate_type FROM trust_publish_gates WHERE content_id=%s", (content_id,))
            existing = {r["gate_type"] for r in cur.fetchall()}

        for gt in GATE_TYPES:
            if gt not in existing:
                create_publish_gate(content_id, gt, required=(gt != "owner_approval"))

        # Run automatic checks
        lint_results = run_trust_lint(content_id, f"content_{content_id}", "")
        evidence = get_evidence(content_id=content_id)
        claims = get_claims(content_id=content_id)

        # Trust lint gate
        lint_passed = lint_results["blockers"] == 0 and lint_results["errors"] == 0
        with _db() as cur:
            cur.execute("SELECT gate_id FROM trust_publish_gates WHERE content_id=%s AND gate_type='trust_lint'", (content_id,))
            g = cur.fetchone()
        if g:
            detail = f"blockers={lint_results['blockers']}, errors={lint_results['errors']}, warnings={lint_results['warnings']}"
            update_gate(g["gate_id"], "passed" if lint_passed else "failed", "system", detail)

        # Evidence check gate
        ev_passed = len(evidence) > 0
        with _db() as cur:
            cur.execute("SELECT gate_id FROM trust_publish_gates WHERE content_id=%s AND gate_type='evidence_check'", (content_id,))
            g = cur.fetchone()
        if g:
            update_gate(g["gate_id"], "passed" if ev_passed else "failed", "system", f"{len(evidence)} evidence items")

        # Risk review gate
        high_risk = any(c.get("risk_level") in ("high", "critical") for c in claims)
        with _db() as cur:
            cur.execute("SELECT gate_id FROM trust_publish_gates WHERE content_id=%s AND gate_type='risk_review'", (content_id,))
            g = cur.fetchone()
        if g:
            update_gate(g["gate_id"], "failed" if high_risk else "passed", "system",
                        "High/critical claims present" if high_risk else "No high-risk claims")

        # Fetch final gate states
        with _db() as cur:
            cur.execute("SELECT * FROM trust_publish_gates WHERE content_id=%s ORDER BY created_at", (content_id,))
            gates = [dict(r) for r in cur.fetchall()]

        blocking = [g for g in gates if g["required"] and g["status"] == "failed"]
        all_passed = len(blocking) == 0

        return {
            "content_id": content_id,
            "all_passed": all_passed,
            "gates": gates,
            "blocking_gates": blocking,
            "publish_safe": all_passed,
            "timestamp": _now_iso(),
        }
    except Exception as e:
        logger.error(f"check_publish_gates failed: {e}")
        return {"error": str(e), "content_id": content_id, "all_passed": False, "gates": [], "blocking_gates": []}
