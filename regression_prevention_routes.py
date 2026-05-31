"""
Regression Prevention Engine - API Routes
Mounts under /api/regression/ on the manager agent.
"""

from fastapi import APIRouter
from regression_prevention import get_engine

router = APIRouter(prefix="/api/regression", tags=["regression"])


@router.get("/summary")
async def get_summary():
    engine = get_engine()
    return engine.get_summary()


@router.post("/scan")
async def run_scan():
    engine = get_engine()
    result = await engine.run_full_scan()
    return result


@router.get("/scores")
async def get_scores():
    engine = get_engine()
    quality = await engine.score_quality_dimensions()
    return quality


@router.get("/agents")
async def get_agent_health():
    engine = get_engine()
    return await engine.check_all_agents()


@router.get("/dashboards")
async def get_dashboard_health():
    engine = get_engine()
    return await engine.check_dashboard_health()


@router.get("/tasks")
async def get_remediation_tasks():
    engine = get_engine()
    return {
        "open": engine.get_open_tasks(),
        "total": len(engine.remediation_tasks),
    }


@router.post("/tasks/{task_id}/resolve")
async def resolve_task(task_id: str):
    engine = get_engine()
    task = engine.resolve_task(task_id)
    if task:
        return {"status": "resolved", "task": task}
    return {"status": "not_found"}


@router.post("/check-content")
async def check_content_compliance(body: dict):
    engine = get_engine()
    content = body.get("content", "")
    title = body.get("title", "")
    return engine.check_content_compliance(content, title)


@router.get("/history")
async def get_scan_history():
    from regression_prevention import _load_list, HISTORY_FILE
    history = _load_list(HISTORY_FILE)
    return {"scans": history[-20:], "total": len(history)}
