"""Phase 10J: Citation, Schema, Freshness, Competitor API Routes."""
from fastapi import APIRouter
from typing import Optional
import phase10j_engine as j

router = APIRouter(prefix="/api/10j", tags=["phase-10j"])

@router.get("/summary")
def summary():
    return j.get_10j_summary()

@router.get("/freshness")
def freshness(staleness_risk: Optional[str] = None, limit: int = 50):
    return j.get_freshness_report(staleness_risk=staleness_risk, limit=limit)

@router.get("/schema-recommendations")
def schema_recs(status: Optional[str] = None, limit: int = 50):
    return j.get_schema_recommendations(status=status, limit=limit)

@router.get("/competitors")
def competitors(domain: Optional[str] = None, limit: int = 20):
    return j.get_competitor_report(domain=domain, limit=limit)

@router.get("/citations")
def citations(engine: Optional[str] = None, limit: int = 50):
    return j.get_citation_events(engine=engine, limit=limit)
