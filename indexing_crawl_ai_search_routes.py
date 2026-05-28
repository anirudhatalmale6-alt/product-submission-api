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

@router.get("/orphans")
def orphan_pages():
    return ix.detect_orphan_pages()

@router.get("/broken-links")
def broken_links():
    return ix.scan_broken_links()

# ── 10I PATCHES: Crawl Monitoring + Active Link Crawler + Publish Trigger ──

@router.post("/10i/setup-tables")
def setup_10i_tables():
    return ix.create_10i_patch_tables()

@router.post("/10i/broken-link-crawl")
def run_link_crawl(limit: int = 50):
    return ix.run_broken_link_crawler(limit=limit)

@router.get("/10i/broken-links")
def get_crawled_broken_links(limit: int = 50):
    return ix.get_broken_links(limit=limit)

@router.post("/10i/crawl-budget-check")
def crawl_budget_check():
    return ix.run_crawl_budget_check()

@router.get("/10i/crawl-budget-history")
def crawl_budget_history(limit: int = 20):
    return ix.get_crawl_budget_history(limit=limit)

@router.post("/10i/publish-trigger")
def publish_trigger(post_id: int, title: str = None, url: str = None):
    return ix.register_publish_trigger(post_id, title, url)

@router.post("/10i/check-index-status")
def check_index_status():
    return ix.check_publish_index_status()

@router.get("/10i/publish-log")
def publish_log(limit: int = 20):
    return ix.get_publish_trigger_log(limit=limit)
