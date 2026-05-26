"""
PetHub Strategic Mission Control – API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import mission_control as mc

router = APIRouter(prefix="/api/mission-control", tags=["mission-control"])


# ── Pydantic models ─────────────────────────────────────────────

class MissionCreate(BaseModel):
    name: str
    business_objective: str
    target_cluster: str
    responsible_agents: Optional[List[str]] = None
    priority: Optional[str] = "medium"


class MissionUpdate(BaseModel):
    name: Optional[str] = None
    business_objective: Optional[str] = None
    target_cluster: Optional[str] = None
    responsible_agents: Optional[List[str]] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class BacklogUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[str] = None
    assigned_agent: Optional[str] = None


class LearningRecord(BaseModel):
    note: str
    metric_type: Optional[str] = None
    forecasted_value: Optional[float] = None
    actual_value: Optional[float] = None


class ContentValidation(BaseModel):
    content: str
    content_type: Optional[str] = None
    claims: Optional[List[str]] = None


# ── scan ─────────────────────────────────────────────────────────
@router.post("/scan")
def scan():
    result = mc.run_mission_scan()
    return result or {"status": "ok"}


# ── briefing ─────────────────────────────────────────────────────
@router.get("/briefing")
def briefing():
    return mc.get_mission_briefing() or {}


# ── summary ──────────────────────────────────────────────────────
@router.get("/summary")
def summary():
    return mc.get_mission_summary() or {}


# ── dashboard ────────────────────────────────────────────────────
@router.get("/dashboard")
def dashboard():
    return mc.get_mission_dashboard_data() or {}


# ── missions CRUD ────────────────────────────────────────────────
@router.get("/missions")
def list_missions(status: Optional[str] = None, cluster: Optional[str] = None):
    return mc.get_missions(status=status, cluster=cluster) or []


@router.get("/missions/{mission_id}")
def get_mission(mission_id: str):
    result = mc.get_mission(mission_id=mission_id)
    if not result:
        raise HTTPException(status_code=404, detail="Mission not found")
    return result


@router.post("/missions")
def create_mission(body: MissionCreate):
    result = mc.create_mission(body.dict())
    if not result:
        raise HTTPException(status_code=400, detail="Mission creation failed")
    return result


@router.put("/missions/{mission_id}")
def update_mission(mission_id: str, body: MissionUpdate):
    result = mc.update_mission(mission_id=mission_id, data=body.dict(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Mission not found")
    return result


@router.delete("/missions/{mission_id}")
def delete_mission(mission_id: str):
    result = mc.delete_mission(mission_id=mission_id)
    if not result:
        raise HTTPException(status_code=404, detail="Mission not found")
    return result


# ── backlog generation ───────────────────────────────────────────
@router.post("/missions/{mission_id}/generate-backlog")
def generate_backlog(mission_id: str):
    result = mc.generate_backlog(mission_id=mission_id)
    if not result:
        raise HTTPException(status_code=400, detail="Backlog generation failed")
    return result


# ── mission progress ─────────────────────────────────────────────
@router.get("/missions/{mission_id}/progress")
def mission_progress(mission_id: str):
    result = mc.update_mission_progress(mission_id=mission_id)
    if not result:
        raise HTTPException(status_code=404, detail="Mission not found")
    return result


# ── learnings ────────────────────────────────────────────────────
@router.get("/missions/{mission_id}/learnings")
def get_learnings(mission_id: str):
    return mc.get_mission_learnings(mission_id=mission_id) or []


@router.post("/missions/{mission_id}/learnings")
def record_learning(mission_id: str, body: LearningRecord):
    result = mc.record_learning(mission_id=mission_id, data=body.dict())
    if not result:
        raise HTTPException(status_code=400, detail="Learning record failed")
    return result


# ── backlog items ────────────────────────────────────────────────
@router.get("/backlog")
def list_backlog(
    mission_id: Optional[str] = None,
    item_type: Optional[str] = None,
    status: Optional[str] = None,
):
    return mc.get_backlog(mission_id=mission_id, item_type=item_type, status=status) or []


@router.get("/backlog/{item_id}")
def get_backlog_item(item_id: str):
    result = mc.get_backlog_item(item_id=item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Backlog item not found")
    return result


@router.put("/backlog/{item_id}")
def update_backlog_item(item_id: str, body: BacklogUpdate):
    result = mc.update_backlog_item(item_id=item_id, data=body.dict(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Backlog item not found")
    return result


# ── content validation ───────────────────────────────────────────
@router.post("/validate-content")
def validate_content(body: ContentValidation):
    result = mc.validate_content_quality(data=body.dict())
    if not result:
        raise HTTPException(status_code=400, detail="Content validation failed")
    return result


# ── seed missions ────────────────────────────────────────────────
@router.post("/seed-missions")
def seed_missions():
    result = mc.seed_initial_missions()
    return result or {"status": "ok"}
