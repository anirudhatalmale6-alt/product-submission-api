"""10G Maturity Block: API routes for evidence backfill, claim extraction, meta fix, mismatch routing, author trust."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import trust_maturity_engine as tm

router = APIRouter(prefix="/api/trust-maturity", tags=["trust-maturity"])


class AuthorCreate(BaseModel):
    display_name: str
    role: str = "contributor"
    expertise_areas: Optional[list] = None
    credentials: Optional[str] = None
    bio: Optional[str] = None

class ReviewCreate(BaseModel):
    content_id: int
    reviewer: Optional[str] = None
    review_type: str = "standard"

class ReviewUpdate(BaseModel):
    review_status: str
    lint_passed: Optional[bool] = None
    evidence_sufficient: Optional[bool] = None
    claims_assessed: Optional[bool] = None
    notes: Optional[str] = None

class MismatchUpdate(BaseModel):
    resolution_status: str
    resolution_notes: Optional[str] = None


@router.get("/summary")
def maturity_summary():
    return tm.get_maturity_summary()

@router.post("/evidence/backfill/{post_id}")
def backfill_evidence(post_id: int):
    return tm.backfill_evidence_for_post(post_id)

@router.post("/evidence/bulk-backfill")
def bulk_backfill(limit: int = 20):
    return tm.bulk_backfill_evidence(limit=limit)

@router.post("/claims/extract/{post_id}")
def extract_claims(post_id: int):
    return tm.extract_claims_for_post(post_id)

@router.post("/claims/bulk-extract")
def bulk_extract(limit: int = 20):
    return tm.bulk_extract_claims(limit=limit)

@router.post("/meta-fix/bulk")
def bulk_fix_meta(limit: int = 20):
    return tm.bulk_fix_meta_lint(limit=limit)

@router.post("/meta-fix/{post_id}")
def fix_meta(post_id: int):
    return tm.fix_meta_lint_for_post(post_id)

@router.post("/mismatches/route")
def route_mismatches():
    return tm.route_product_count_mismatches()

@router.get("/mismatches")
def list_mismatches(status: Optional[str] = None, severity: Optional[str] = None, limit: int = 50):
    return tm.list_mismatches(status=status, severity=severity, limit=limit)

@router.put("/mismatches/{mismatch_id}")
def update_mismatch(mismatch_id: str, body: MismatchUpdate):
    result = tm.update_mismatch(mismatch_id, body.resolution_status, body.resolution_notes)
    if "error" in result:
        raise HTTPException(404, result)
    return result

@router.post("/authors")
def register_author(body: AuthorCreate):
    return tm.register_author(**body.dict())

@router.get("/authors")
def list_authors():
    return tm.list_authors()

@router.post("/reviews")
def create_review(body: ReviewCreate):
    return tm.create_editorial_review(**body.dict())

@router.get("/reviews")
def list_reviews(content_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50):
    return tm.list_editorial_reviews(content_id=content_id, status=status, limit=limit)

@router.put("/reviews/{review_id}")
def update_review(review_id: str, body: ReviewUpdate):
    result = tm.update_editorial_review(review_id, **body.dict())
    if "error" in result:
        raise HTTPException(404, result)
    return result

@router.post("/full-backfill")
def full_backfill(limit: int = 86):
    return tm.run_full_maturity_backfill(limit=limit)
