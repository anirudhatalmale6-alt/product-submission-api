"""
PetHub Job Centre - Tracks all jobs across the manager agent.
10F UPGRADE: Dual-write to both JSON (legacy) and PostgreSQL (truthful_ops).
JSON remains primary read source during shadow mode.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("job_centre")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

JOBS_FILE = os.path.join(DATA_DIR, "jobs.json")

VALID_STATUSES = {"queued", "running", "completed", "failed", "partial", "cancelled", "skipped"}

RETRYABLE_ACTIONS = {
    "SEO audit", "SEO auto-fix", "Social post (both)", "Facebook post",
    "Reel generation", "Link scan", "Performance scan", "Security scan",
    "Analytics collection", "Engagement collection", "Link fix",
    "Schema generation", "Internal link analysis", "Content freshness refresh",
    "A/B test", "Metadata audit", "Content audit", "Agent scoring",
}

CANCELLABLE_STATUSES = {"queued", "running"}

# 10F: Import truthful_ops for dual-write
try:
    import truthful_ops as _ops
    _OPS_AVAILABLE = True
    logger.info("10F truthful_ops loaded — dual-write mode active")
except ImportError:
    _ops = None
    _OPS_AVAILABLE = False
    logger.warning("10F truthful_ops not available — JSON-only mode")


def _ops_shadow_write(fn_name, *args, **kwargs):
    """Attempt to write to truthful_ops. Never block on failure."""
    if not _OPS_AVAILABLE:
        return None
    try:
        fn = getattr(_ops, fn_name)
        return fn(*args, **kwargs)
    except Exception as e:
        logger.error(f"10F shadow write failed ({fn_name}): {e}")
        return None


def _ops_compare(job_id, json_job, field_name, json_val, ops_val):
    """Log comparison between JSON and PostgreSQL data."""
    if not _OPS_AVAILABLE:
        return
    try:
        match = str(json_val) == str(ops_val)
        _ops.log_comparison(
            check_type="job", entity_id=job_id, old_store="jobs.json",
            field_name=field_name, old_value=str(json_val)[:500],
            new_value=str(ops_val)[:500], match=match,
            discrepancy_type=None if match else "value_mismatch",
        )
    except Exception:
        pass


def _load_jobs() -> list:
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_jobs(jobs: list):
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2, default=str)


def create_job(
    agent: str,
    action: str,
    endpoint: str,
    input_data: Optional[dict] = None,
    triggered_by: str = "manual",
) -> dict:
    jobs = _load_jobs()
    job = {
        "id": "job-" + str(uuid.uuid4())[:8],
        "agent": agent,
        "action": action,
        "endpoint": endpoint,
        "input_data": input_data or {},
        "triggered_by": triggered_by,
        "status": "queued",
        "progress_pct": 0,
        "output": None,
        "error": None,
        "result_summary": None,
        "retryable": action in RETRYABLE_ACTIONS,
        "cancellable": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "started_at": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "duration_ms": None,
        "follow_up": None,
    }
    jobs.append(job)
    if len(jobs) > 1000:
        jobs = jobs[-1000:]
    _save_jobs(jobs)
    logger.info(f"Job created: {job['id']} - {action} for {agent}")

    # 10F: Shadow write to PostgreSQL
    _ops_shadow_write(
        "create_job", agent=agent, action=action, endpoint=endpoint,
        input_data=input_data, triggered_by=triggered_by,
        retryable=action in RETRYABLE_ACTIONS,
    )

    return job


def start_job(job_id: str) -> Optional[dict]:
    jobs = _load_jobs()
    for j in jobs:
        if j["id"] == job_id:
            j["status"] = "running"
            j["progress_pct"] = 10
            j["started_at"] = datetime.now(timezone.utc).isoformat()
            j["updated_at"] = datetime.now(timezone.utc).isoformat()
            j["cancellable"] = True
            _save_jobs(jobs)

            # 10F: Shadow write
            _ops_shadow_write("start_job", job_id)
            return j
    return None


def complete_job(
    job_id: str,
    success: bool,
    output: Optional[dict] = None,
    result_summary: str = "",
    follow_up: str = "",
    status_code: int = 200,
) -> Optional[dict]:
    jobs = _load_jobs()
    for j in jobs:
        if j["id"] == job_id:
            now = datetime.now(timezone.utc)
            j["status"] = "completed" if success else "failed"
            j["progress_pct"] = 100 if success else j.get("progress_pct", 0)
            j["output"] = output
            j["result_summary"] = result_summary
            j["follow_up"] = follow_up if follow_up else None
            j["completed_at"] = now.isoformat()
            j["updated_at"] = now.isoformat()
            j["cancellable"] = False
            j["status_code"] = status_code
            if j.get("started_at"):
                try:
                    start = datetime.fromisoformat(j["started_at"])
                    j["duration_ms"] = int((now - start).total_seconds() * 1000)
                except Exception:
                    pass
            _save_jobs(jobs)
            logger.info(f"Job {job_id} {'completed' if success else 'failed'}: {result_summary}")

            # 10F: Shadow write + comparison
            ops_result = _ops_shadow_write(
                "complete_job", job_id, success=success, output=output,
                result_summary=result_summary, follow_up=follow_up,
            )
            if ops_result:
                _ops_compare(job_id, j, "status", j["status"], ops_result.get("status"))

            return j
    return None


def update_job_progress(job_id: str, progress_pct: int, status_msg: str = "") -> Optional[dict]:
    jobs = _load_jobs()
    for j in jobs:
        if j["id"] == job_id:
            j["progress_pct"] = min(progress_pct, 99)
            j["updated_at"] = datetime.now(timezone.utc).isoformat()
            if status_msg:
                j["result_summary"] = status_msg
            _save_jobs(jobs)

            _ops_shadow_write("update_job_progress", job_id, progress_pct, status_msg)
            return j
    return None


def cancel_job(job_id: str) -> Optional[dict]:
    jobs = _load_jobs()
    for j in jobs:
        if j["id"] == job_id:
            if j["status"] not in CANCELLABLE_STATUSES:
                return None
            j["status"] = "cancelled"
            j["updated_at"] = datetime.now(timezone.utc).isoformat()
            j["completed_at"] = datetime.now(timezone.utc).isoformat()
            j["cancellable"] = False
            j["result_summary"] = "Cancelled by user"
            _save_jobs(jobs)
            logger.info(f"Job {job_id} cancelled")

            _ops_shadow_write("cancel_job", job_id, "Cancelled by user")
            return j
    return None


def retry_job(job_id: str) -> Optional[dict]:
    jobs = _load_jobs()
    for j in jobs:
        if j["id"] == job_id:
            if not j.get("retryable") or j["status"] not in ("failed", "partial"):
                return None
            new_job = create_job(
                agent=j["agent"],
                action=j["action"],
                endpoint=j["endpoint"],
                input_data=j.get("input_data", {}),
                triggered_by="retry:" + job_id,
            )
            return new_job
    return None


def get_job(job_id: str) -> Optional[dict]:
    jobs = _load_jobs()
    for j in jobs:
        if j["id"] == job_id:
            return j
    return None


def get_jobs_by_status(status: str = None, agent: str = None, limit: int = 50) -> list:
    jobs = _load_jobs()
    result = list(reversed(jobs))
    if status:
        result = [j for j in result if j["status"] == status]
    if agent:
        result = [j for j in result if j["agent"] == agent]
    return result[:limit]


def get_active_jobs() -> list:
    return get_jobs_by_status("running")


def get_queued_jobs() -> list:
    return get_jobs_by_status("queued")


def get_failed_jobs(limit: int = 20) -> list:
    return get_jobs_by_status("failed", limit=limit)


def get_recent_completed(limit: int = 20) -> list:
    return get_jobs_by_status("completed", limit=limit)


def get_job_centre_summary() -> dict:
    jobs = _load_jobs()
    active = [j for j in jobs if j["status"] == "running"]
    queued = [j for j in jobs if j["status"] == "queued"]
    failed = [j for j in jobs if j["status"] == "failed"]
    completed = [j for j in jobs if j["status"] == "completed"]
    cancelled = [j for j in jobs if j["status"] == "cancelled"]
    partial = [j for j in jobs if j["status"] == "partial"]

    by_agent = {}
    for j in jobs:
        ag = j.get("agent", "unknown")
        by_agent[ag] = by_agent.get(ag, 0) + 1

    recent = sorted(jobs, key=lambda x: x.get("updated_at", ""), reverse=True)[:20]

    return {
        "total_jobs": len(jobs),
        "active": len(active),
        "queued": len(queued),
        "failed": len(failed),
        "completed": len(completed),
        "cancelled": len(cancelled),
        "partial": len(partial),
        "by_agent": by_agent,
        "active_jobs": active,
        "queued_jobs": queued,
        "failed_jobs": failed[-10:],
        "recent_completed": list(reversed(completed))[:10],
        "recent_all": recent,
    }
