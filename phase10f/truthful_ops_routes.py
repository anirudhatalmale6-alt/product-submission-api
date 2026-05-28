"""
10F: Truthful Operations API Routes
All /api/ops/* endpoints for the unified operational truth layer.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

import truthful_ops as ops

logger = logging.getLogger("truthful_ops_routes")
router = APIRouter(prefix="/api/ops", tags=["ops"])


# ── Request Models ──────────────────────────────────────────

class ApprovalDecision(BaseModel):
    decision: str  # "approved" or "rejected"
    decided_by: str = "operator"
    reason: str = ""

class AlertResolve(BaseModel):
    resolved_by: str = "operator"
    resolution_summary: str = ""

class JobProgress(BaseModel):
    progress_pct: int
    status_msg: str = ""

class JobComplete(BaseModel):
    success: bool
    output: dict = None
    result_summary: str = ""
    error_summary: str = ""
    follow_up: str = ""
    fallback_used: bool = False


# ── Jobs ────────────────────────────────────────────────────

@router.get("/jobs/recent")
async def get_recent_jobs(
    limit: int = Query(50, le=200),
    status: str = Query(None),
    agent: str = Query(None),
):
    return ops.get_jobs(status=status, agent=agent, limit=limit)


@router.get("/jobs/summary")
async def get_jobs_summary():
    return ops.get_jobs_summary()


@router.get("/jobs/{job_id}")
async def get_job_detail(job_id: str):
    job = ops.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    events = ops.get_timeline(hours=168, limit=50)
    job["events"] = [e for e in events if e.get("job_id") == job_id]
    return job


@router.post("/jobs/{job_id}/progress")
async def update_job_progress(job_id: str, body: JobProgress):
    result = ops.update_job_progress(job_id, body.progress_pct, body.status_msg)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    return result


@router.post("/jobs/{job_id}/complete")
async def complete_job(job_id: str, body: JobComplete):
    result = ops.complete_job(
        job_id, body.success, body.output, body.result_summary,
        body.error_summary, body.follow_up, body.fallback_used,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    ops.update_receipt_status(job_id=job_id, status="completed" if body.success else "failed")
    return result


@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str):
    result = ops.retry_job(job_id)
    if not result:
        raise HTTPException(status_code=400, detail="Job not retryable or max retries reached")
    return result


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, reason: str = "Cancelled by operator"):
    result = ops.cancel_job(job_id, reason)
    if not result:
        raise HTTPException(status_code=404, detail="Job not found or not cancellable")
    return result


# ── Approvals ───────────────────────────────────────────────

@router.get("/approvals/pending")
async def get_pending_approvals():
    return ops.get_approvals(status="pending")


@router.get("/approvals/recent")
async def get_recent_approvals(
    status: str = Query(None),
    limit: int = Query(50, le=200),
):
    return ops.get_approvals(status=status, limit=limit)


@router.post("/approvals/{approval_id}/decide")
async def decide_approval(approval_id: str, body: ApprovalDecision):
    result = ops.decide_approval(approval_id, body.decision, body.decided_by, body.reason)
    if not result:
        raise HTTPException(status_code=404, detail="Approval not found or already decided")
    return result


@router.post("/approvals/{approval_id}/approve")
async def approve(approval_id: str, reason: str = "Approved by operator"):
    return ops.decide_approval(approval_id, "approved", "operator", reason)


@router.post("/approvals/{approval_id}/reject")
async def reject(approval_id: str, reason: str = "Rejected by operator"):
    return ops.decide_approval(approval_id, "rejected", "operator", reason)


# ── Events / Timeline ──────────────────────────────────────

@router.get("/events/timeline")
async def get_event_timeline(
    hours: int = Query(24, le=720),
    category: str = Query(None),
    severity: str = Query(None),
    limit: int = Query(200, le=1000),
):
    return ops.get_timeline(hours=hours, category=category, severity=severity, limit=limit)


# ── Action Receipts ─────────────────────────────────────────

@router.get("/actions/recent")
async def get_recent_actions(limit: int = Query(50, le=200)):
    return ops.get_receipts(limit=limit)


# ── Pipeline ────────────────────────────────────────────────

@router.get("/pipeline/history")
async def get_pipeline_history(limit: int = Query(20, le=100)):
    return ops.get_pipeline_history(limit=limit)


@router.get("/pipeline/current")
async def get_current_pipeline():
    runs = ops.get_pipeline_history(limit=1)
    if runs and runs[0].get("status") == "running":
        return runs[0]
    return {"status": "no_active_pipeline"}


# ── Agent Status ────────────────────────────────────────────

@router.get("/agents/status")
async def get_agent_status():
    return ops.get_all_agent_status()


@router.get("/agents/{agent_name}")
async def get_single_agent(agent_name: str):
    agents = ops.get_all_agent_status()
    for a in agents:
        if a["agent_name"] == agent_name:
            return a
    raise HTTPException(status_code=404, detail="Agent not found")


# ── Alerts ──────────────────────────────────────────────────

@router.get("/alerts/active")
async def get_active_alerts():
    return ops.get_alerts(status="active")


@router.get("/alerts/all")
async def get_all_alerts(
    status: str = Query(None),
    limit: int = Query(50, le=200),
):
    return ops.get_alerts(status=status, limit=limit)


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, body: AlertResolve):
    result = ops.resolve_alert(alert_id, body.resolved_by, body.resolution_summary)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found or not active")
    return result


@router.post("/alerts/{alert_id}/suppress")
async def suppress_alert(alert_id: str):
    result = ops.suppress_alert(alert_id)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found or not active")
    return result


# ── Operational Summary ─────────────────────────────────────

@router.get("/summary")
async def get_operational_summary():
    return ops.get_operational_summary()


# ── Comparison / Shadow Mode ────────────────────────────────

@router.get("/comparison/summary")
async def get_comparison_summary():
    return ops.get_comparison_summary()


@router.get("/comparison/shadow-report")
async def get_shadow_report():
    """Full shadow mode report comparing JSON and PostgreSQL stores."""
    import json as _json
    import os

    comparison = ops.get_comparison_summary()
    ops_summary = ops.get_operational_summary()

    # Load JSON job summary for comparison
    json_jobs = []
    jobs_file = os.path.join(os.path.dirname(__file__), 'data', 'jobs.json')
    try:
        with open(jobs_file, 'r') as f:
            json_jobs = _json.load(f)
    except Exception:
        pass

    json_summary = {
        'total': len(json_jobs),
        'running': sum(1 for j in json_jobs if j.get('status') == 'running'),
        'completed': sum(1 for j in json_jobs if j.get('status') == 'completed'),
        'failed': sum(1 for j in json_jobs if j.get('status') == 'failed'),
    }

    return {
        'shadow_mode': 'active',
        'primary_store': 'JSON (legacy)',
        'shadow_store': 'PostgreSQL (10F)',
        'json_summary': json_summary,
        'ops_summary': ops_summary,
        'comparison': comparison,
        'match_rate': round(comparison['matches'] / max(comparison['total_checks'], 1) * 100, 1),
        'recommendation': 'safe_to_proceed' if comparison['discrepancies'] == 0 else 'investigate_discrepancies',
    }




# ── 10F Sign-off Pack ────────────────────────────────────────

@router.get("/signoff/rec-vs-action")
async def get_rec_vs_action():
    return ops.get_recommendation_vs_action_report()


@router.get("/signoff/fallback")
async def get_fallback_state():
    return ops.get_fallback_visibility()


@router.get("/signoff/pack")
async def get_signoff_pack():
    return ops.get_signoff_pack()
