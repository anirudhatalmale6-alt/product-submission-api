"""10H: Cluster Expansion API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import cluster_expansion as ce

router = APIRouter(prefix="/api/expansion", tags=["expansion"])


class ClusterCreate(BaseModel):
    cluster_name: str
    slug: str
    hub_intent: str
    content_type: str = "educational"
    importance: str = "medium"
    category_id: Optional[int] = None
    hub_post_id: Optional[int] = None
    hub_url: Optional[str] = None
    evidence_requirements: Optional[list] = None
    trust_requirements: Optional[list] = None
    expansion_mode: str = "draft_only"

class SpokeCreate(BaseModel):
    cluster_id: str
    spoke_name: str
    slug: str
    spoke_intent: str
    content_type: str = "educational"
    priority: int = 50
    disclosure_required: bool = False
    approval_required: bool = True

class SpokeTransition(BaseModel):
    new_status: str

class LinkPlan(BaseModel):
    source_spoke_id: str
    target_spoke_id: str
    anchor_text: str
    context_relevance: str = "high"
    link_type: str = "contextual"
    cluster_coherent: bool = True

class JobCreate(BaseModel):
    cluster_id: str
    job_type: str
    target_spoke_id: Optional[str] = None
    input_data: Optional[dict] = None


@router.get("/summary")
def expansion_summary():
    return ce.get_expansion_summary()

@router.get("/clusters")
def list_clusters(importance: Optional[str] = None, readiness: Optional[str] = None):
    return ce.list_clusters(importance=importance, readiness=readiness)

@router.post("/clusters")
def create_cluster(body: ClusterCreate):
    result = ce.create_cluster(**body.dict())
    if not result:
        raise HTTPException(400, "cluster creation failed")
    return result

@router.get("/clusters/{cluster_id}")
def get_cluster(cluster_id: str):
    c = ce.get_cluster(cluster_id)
    if not c:
        raise HTTPException(404, "cluster not found")
    return c

@router.put("/clusters/{cluster_id}")
def update_cluster(cluster_id: str, body: dict):
    result = ce.update_cluster(cluster_id, **body)
    if not result:
        raise HTTPException(404, "cluster not found or no valid fields")
    return result

@router.get("/clusters/{cluster_id}/readiness")
def cluster_readiness(cluster_id: str):
    return ce.assess_cluster_readiness(cluster_id)

@router.get("/spokes")
def list_spokes(cluster_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50):
    return ce.list_spokes(cluster_id=cluster_id, status=status, limit=limit)

@router.post("/spokes")
def create_spoke(body: SpokeCreate):
    result = ce.create_spoke(**body.dict())
    if not result:
        raise HTTPException(400, "spoke creation failed")
    return result

@router.get("/spokes/{spoke_id}")
def get_spoke(spoke_id: str):
    s = ce.get_spoke(spoke_id)
    if not s:
        raise HTTPException(404, "spoke not found")
    return s

@router.put("/spokes/{spoke_id}")
def update_spoke(spoke_id: str, body: dict):
    result = ce.update_spoke(spoke_id, **body)
    if not result:
        raise HTTPException(404, "spoke not found or no valid fields")
    return result

@router.post("/spokes/{spoke_id}/transition")
def transition_spoke(spoke_id: str, body: SpokeTransition):
    result = ce.transition_spoke(spoke_id, body.new_status)
    if "error" in result:
        raise HTTPException(400, result)
    return result

@router.post("/spokes/{spoke_id}/gate-check")
def gate_check(spoke_id: str):
    result = ce.run_gate_check(spoke_id)
    if "error" in result:
        raise HTTPException(404, result)
    return result

@router.get("/spokes/{spoke_id}/gates")
def gate_history(spoke_id: str, limit: int = 10):
    return ce.get_gate_history(spoke_id, limit=limit)

@router.get("/links")
def list_links(cluster_id: Optional[str] = None, spoke_id: Optional[str] = None,
               status: Optional[str] = None, limit: int = 100):
    return ce.list_links(cluster_id=cluster_id, spoke_id=spoke_id, status=status, limit=limit)

@router.post("/links")
def plan_link(body: LinkPlan):
    return ce.plan_link(**body.dict())

@router.put("/links/{link_id}")
def update_link(link_id: str, body: dict):
    result = ce.update_link(link_id, **body)
    if not result:
        raise HTTPException(404, "link not found or no valid fields")
    return result

@router.get("/jobs")
def list_jobs(cluster_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50):
    return ce.list_expansion_jobs(cluster_id=cluster_id, status=status, limit=limit)

@router.post("/jobs")
def create_job(body: JobCreate):
    return ce.create_expansion_job(**body.dict())

@router.put("/jobs/{job_id}")
def update_job(job_id: str, status: str, output_data: Optional[dict] = None, error_summary: Optional[str] = None):
    result = ce.update_expansion_job(job_id, status, output_data=output_data, error_summary=error_summary)
    if not result:
        raise HTTPException(404, "job not found")
    return result

@router.post("/seed")
def seed_clusters():
    return ce.seed_clusters_from_site()

@router.post("/match-posts")
def match_posts():
    return ce.match_existing_posts_to_spokes()
