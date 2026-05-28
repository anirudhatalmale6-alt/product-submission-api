"""
Tracked Dispatch - Wraps agent_dispatcher calls with Job Centre tracking.
10F UPGRADE: Also creates action receipts and events via truthful_ops.
"""

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from job_centre import create_job, start_job, complete_job

logger = logging.getLogger("tracked_dispatch")

# 10F: Import truthful_ops for action receipts + events
try:
    import truthful_ops as _ops
    _OPS_AVAILABLE = True
except ImportError:
    _ops = None
    _OPS_AVAILABLE = False


async def tracked_dispatch(
    dispatch_fn: Callable,
    agent: str,
    action: str,
    endpoint: str,
    triggered_by: str = "manual",
    input_data: Optional[dict] = None,
    source_screen: str = "manager_dashboard",
) -> dict:
    job = create_job(
        agent=agent,
        action=action,
        endpoint=endpoint,
        input_data=input_data or {},
        triggered_by=triggered_by,
    )
    job_id = job["id"]

    start_job(job_id)

    # 10F: Create action receipt
    if _OPS_AVAILABLE:
        try:
            _ops.create_action_receipt(
                action_name=action,
                actor="operator" if triggered_by == "manual" else f"system:{triggered_by}",
                source_screen=source_screen,
                source_module="tracked_dispatch",
                target_entity=endpoint,
                job_id=job_id,
                status="running",
                accepted=True,
                next_expected="Waiting for agent response",
            )
        except Exception as e:
            logger.error(f"10F receipt creation failed: {e}")

    try:
        result = await dispatch_fn()
    except Exception as e:
        complete_job(
            job_id,
            success=False,
            output={"error": str(e)},
            result_summary=f"Exception: {str(e)[:200]}",
            status_code=500,
        )
        # 10F: Update receipt on failure
        if _OPS_AVAILABLE:
            try:
                _ops.update_receipt_status(job_id=job_id, status="failed")
            except Exception:
                pass
        return {
            "job_id": job_id,
            "success": False,
            "agent": agent,
            "action": action,
            "endpoint": endpoint,
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    success = result.get("success", False)
    status_code = result.get("status_code", 200 if success else 500)
    response_data = result.get("response", result)

    summary_parts = []
    if success:
        msg = response_data.get("message", "") if isinstance(response_data, dict) else ""
        if msg:
            summary_parts.append(msg)
        for key in ("fixed", "found", "total", "count", "scanned", "posts", "generated"):
            val = response_data.get(key) if isinstance(response_data, dict) else None
            if val is not None:
                summary_parts.append(f"{key}: {val}")
        if not summary_parts:
            summary_parts.append("Completed successfully")
    else:
        err = result.get("error", "")
        detail = response_data.get("detail", "") if isinstance(response_data, dict) else ""
        summary_parts.append(err or detail or "Failed")

    result_summary = ". ".join(summary_parts)

    follow_up = ""
    if isinstance(response_data, dict):
        if response_data.get("issues_found"):
            follow_up = f"Review {response_data['issues_found']} issues found"
        elif response_data.get("broken_links"):
            follow_up = f"Fix {response_data['broken_links']} broken links"
        elif response_data.get("warnings"):
            follow_up = f"Review {len(response_data['warnings'])} warnings"

    complete_job(
        job_id,
        success=success,
        output=response_data,
        result_summary=result_summary,
        follow_up=follow_up,
        status_code=status_code,
    )

    # 10F: Update receipt with final status
    if _OPS_AVAILABLE:
        try:
            _ops.update_receipt_status(
                job_id=job_id,
                status="completed" if success else "failed",
            )
        except Exception:
            pass

    return {
        "job_id": job_id,
        "success": success,
        "agent": agent,
        "action": action,
        "endpoint": endpoint,
        "status": "completed" if success else "failed",
        "status_code": status_code,
        "result_summary": result_summary,
        "response": response_data,
        "follow_up": follow_up or None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": None,
    }
