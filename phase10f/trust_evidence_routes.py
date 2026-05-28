"""
10G: Trust Evidence API Routes
All /api/trust/* endpoints for the trust evidence layer.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

import trust_evidence as te

logger = logging.getLogger("trust_evidence_routes")
router = APIRouter(prefix="/api/trust", tags=["trust"])


# ── Request Models ──────────────────────────────────────────

class EvidenceClassifyBody(BaseModel):
    content_id: int
    claim_text: str
    source_url: str = ""
    source_name: str = ""
    evidence_type: str = "editorial_inference"
    confidence_score: int = 50
    verified_by: Optional[str] = None

class EvidenceStatusBody(BaseModel):
    status: str
    reason: str = ""

class ClaimAssessBody(BaseModel):
    content_id: int
    claim_text: str
    claim_type: str
    evidence_ids: Optional[List[str]] = None

class LintRunBody(BaseModel):
    content_id: int
    content_title: str
    content_body: str
    meta_title: str = ""
    meta_description: str = ""

class AuditRunBody(BaseModel):
    content_id: int
    content_title: str
    content_url: str = ""

class GateCreateBody(BaseModel):
    content_id: int
    gate_type: str
    required: bool = True

class GateUpdateBody(BaseModel):
    status: str
    checked_by: str = "operator"
    result_detail: str = ""


# ── Evidence ────────────────────────────────────────────────

@router.post("/evidence/classify")
async def classify_evidence(body: EvidenceClassifyBody):
    return te.classify_evidence(
        content_id=body.content_id,
        claim_text=body.claim_text,
        source_url=body.source_url,
        source_name=body.source_name,
        evidence_type=body.evidence_type,
        confidence_score=body.confidence_score,
        verified_by=body.verified_by,
    )


@router.get("/evidence")
async def get_evidence(
    content_id: Optional[int] = Query(None),
    evidence_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    return te.get_evidence(content_id=content_id, evidence_type=evidence_type, limit=limit)


@router.put("/evidence/{evidence_id}/status")
async def update_evidence_status(evidence_id: str, body: EvidenceStatusBody):
    result = te.update_evidence_status(evidence_id, body.status, body.reason)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Claims ──────────────────────────────────────────────────

@router.post("/claims/assess")
async def assess_claim(body: ClaimAssessBody):
    return te.assess_claim(
        content_id=body.content_id,
        claim_text=body.claim_text,
        claim_type=body.claim_type,
        evidence_ids=body.evidence_ids,
    )


@router.get("/claims")
async def get_claims(
    content_id: Optional[int] = Query(None),
    risk_level: Optional[str] = Query(None),
    lint_status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    return te.get_claims(content_id=content_id, risk_level=risk_level, lint_status=lint_status, limit=limit)


# ── Lint ────────────────────────────────────────────────────

@router.post("/lint/run")
async def run_trust_lint(body: LintRunBody):
    return te.run_trust_lint(
        content_id=body.content_id,
        content_title=body.content_title,
        content_body=body.content_body,
        meta_title=body.meta_title,
        meta_description=body.meta_description,
    )


# ── Audit ───────────────────────────────────────────────────

@router.get("/audit")
async def get_audit(
    content_id: Optional[int] = Query(None),
    trust_state: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
):
    return te.get_audit(content_id=content_id, trust_state=trust_state, limit=limit)


@router.get("/audit/summary")
async def get_audit_summary():
    return te.get_audit_summary()


@router.post("/audit/run")
async def audit_content(body: AuditRunBody):
    return te.audit_content(
        content_id=body.content_id,
        content_title=body.content_title,
        content_url=body.content_url,
    )


# ── Publish Gates ────────────────────────────────────────────

@router.get("/gates/check/{content_id}")
async def check_publish_gates(content_id: int):
    return te.check_publish_gates(content_id)


@router.post("/gates/create")
async def create_publish_gate(body: GateCreateBody):
    result = te.create_publish_gate(
        content_id=body.content_id,
        gate_type=body.gate_type,
        required=body.required,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.put("/gates/{gate_id}")
async def update_gate(gate_id: str, body: GateUpdateBody):
    result = te.update_gate(
        gate_id=gate_id,
        status=body.status,
        checked_by=body.checked_by,
        result_detail=body.result_detail,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
