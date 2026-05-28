"""10I: Indexing, Crawl, and AI Search Adaptation API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import indexing_crawl_ai_search as ix

router = APIRouter(prefix="/api/indexing", tags=["indexing"])


class CitationRecord(BaseModel):
    url: str
    ai_engine: str
    query_text: str
    citation_type: str = "direct"
    citation_context: Optional[str] = None
    confidence: float = 0.5
    cluster_slug: Optional[str] = None


@router.get("/summary")
def indexing_summary():
    return ix.get_indexing_summary()


@router.get("/pages")
def list_pages(index_status: Optional[str] = None, page_type: Optional[str] = None, limit: int = 100):
    return ix.get_pages(index_status=index_status, page_type=page_type, limit=limit)


@router.get("/pages/{page_id}")
def get_page(page_id: str):
    conn = ix._conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM crawl_index_status WHERE page_id=%s", (page_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "page not found")
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
    finally:
        conn.close()


@router.post("/pages/{page_id}/check")
def check_page(page_id: str):
    result = ix.check_page_indexing(page_id)
    if "error" in result:
        raise HTTPException(404, result)
    return result


@router.post("/crawl-sitemap")
def crawl_sitemap():
    return ix.crawl_sitemap()


@router.post("/bulk-check")
def bulk_check(limit: int = 20):
    return ix.bulk_check_indexing(limit=limit)


@router.get("/readiness")
def readiness_list(cluster_slug: Optional[str] = None, min_score: Optional[float] = None,
                   max_score: Optional[float] = None, limit: int = 100):
    return ix.get_readiness_list(cluster_slug=cluster_slug, min_score=min_score,
                                 max_score=max_score, limit=limit)


@router.get("/readiness/clusters")
def cluster_readiness():
    return ix.get_cluster_readiness()


@router.get("/readiness/engines")
def engine_readiness():
    return ix.get_engine_readiness()


@router.post("/readiness/{page_id}/assess")
def assess_readiness(page_id: str):
    result = ix.assess_page_readiness(page_id)
    if "error" in result:
        raise HTTPException(404, result)
    return result


@router.post("/readiness/bulk-assess")
def bulk_assess(limit: int = 20):
    return ix.bulk_assess_readiness(limit=limit)


@router.get("/adaptations")
def adaptation_queue(limit: int = 30):
    return ix.get_adaptation_queue(limit=limit)


@router.get("/citations")
def list_citations(ai_engine: Optional[str] = None, cluster_slug: Optional[str] = None, limit: int = 50):
    return ix.list_citations(ai_engine=ai_engine, cluster_slug=cluster_slug, limit=limit)


@router.post("/citations")
def record_citation(body: CitationRecord):
    return ix.record_citation(**body.dict())


@router.post("/link-clusters")
def link_clusters():
    return ix.link_pages_to_clusters()


@router.post("/full-scan")
def full_scan():
    return ix.run_full_scan()
