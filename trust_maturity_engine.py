"""10G Maturity Block: Evidence backfill, claim extraction, author trust, meta-source fix, mismatch routing.

Extends trust_evidence.py with operational backfill capabilities:
- Fetches real WordPress content via REST API
- Extracts evidence signals from page content
- Classifies claims using the 6-category x 4-level risk framework
- Reads real meta title/description from WP API (not body HTML)
- Routes product-count mismatches through remediation workflow
- Manages author/editorial trust records
"""
import json, re, hashlib, uuid, os
from datetime import datetime, timezone
import requests

DB_DSN = "host=127.0.0.1 port=5432 dbname=agent_manager user=productapi password=productapi"
WP_API = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
SITE_URL = "https://pethubonline.com"

EVIDENCE_LEVELS = [
    "no_evidence", "anecdotal", "manufacturer_stated", "editorial_review",
    "structured_comparison", "independent_testing", "expert_verified"
]

CLAIM_CATEGORIES = [
    "product_performance", "testing_review", "health_wellbeing",
    "veterinary_behaviour", "urgency_discount", "general_editorial"
]

CLAIM_RISK_LEVELS = ["low", "medium", "high", "critical"]

CLAIM_PATTERNS = {
    "product_performance": [
        (r"\bbest\b.*\b(?:for|uk|guide|buy|pick)", "product_ranking"),
        (r"\btop\s+\d+\b", "product_ranking"),
        (r"\b(?:number one|#1|leading)\b", "superlative_claim"),
        (r"\b(?:outperform|superior|premium quality)\b", "comparative_claim"),
    ],
    "testing_review": [
        (r"\b(?:we tested|our test|hands-on test|testing reveal)\b", "testing_claim"),
        (r"\b(?:we reviewed|our review|in our experience)\b", "review_claim"),
        (r"\b(?:we compared|side.by.side|comparison test)\b", "comparison_claim"),
        (r"\b(?:we found|we discovered|our findings)\b", "findings_claim"),
    ],
    "health_wellbeing": [
        (r"\b(?:healthy|health benefit|nutritious|wellness)\b", "health_claim"),
        (r"\b(?:safe|safety|non.toxic|hypoallergenic)\b", "safety_claim"),
        (r"\b(?:improve|boost|strengthen|enhance)\b.*\b(?:health|digestion|coat|joint)", "health_improvement"),
        (r"\b(?:prevent|reduce risk|protect against)\b", "prevention_claim"),
    ],
    "veterinary_behaviour": [
        (r"\b(?:vet|veterinar|animal doctor)\b", "veterinary_reference"),
        (r"\b(?:behaviourist|trainer|canine expert)\b", "expert_reference"),
        (r"\b(?:recommend(?:ed)? by|endorsed by|approved by)\b", "endorsement_claim"),
        (r"\b(?:clinically|scientifically|research.backed)\b", "scientific_claim"),
    ],
    "urgency_discount": [
        (r"\b(?:limited time|hurry|selling fast|running out)\b", "urgency_claim"),
        (r"\b(?:discount|save|deal|offer|% off)\b", "discount_claim"),
        (r"\b(?:exclusive|only available|special)\b", "exclusivity_claim"),
    ],
    "general_editorial": [
        (r"\b(?:according to|experts say|studies show|research indicates)\b", "attribution_claim"),
        (r"\b(?:award.winning|highly rated|top.rated)\b", "rating_claim"),
        (r"\b(?:most popular|best.selling|favourite)\b", "popularity_claim"),
    ],
}

EVIDENCE_SIGNALS = {
    "named_source": r"(?:Dr\.?\s+\w+|Professor\s+\w+|\w+\s+(?:University|College|Institute))",
    "citation_link": r"(?:https?://(?!pethubonline)[^\s\"'<>]+)",
    "data_point": r"\b\d+(?:\.\d+)?(?:\s*%|\s*(?:mg|g|kg|ml|kcal|calories|months?|years?|weeks?|days?))\b",
    "comparison_table": r"<table|<th|comparison|versus|vs\.",
    "methodology": r"(?:methodology|how we (?:test|rate|score|evaluate|assess))",
    "disclosure": r"(?:affiliate|commission|sponsored|partnership|paid)",
    "editorial_policy": r"(?:editorial (?:policy|standard|guideline|process)|fact.check)",
    "expert_quote": r"(?:says|explains|notes|recommends|advises)\s+(?:Dr\.?\s+\w+|Professor)",
    "structured_list": r"(?:<(?:ul|ol)>.*?</(?:ul|ol)>)",
    "faq_section": r"(?:faq|frequently asked|common questions|q&a)",
}


def _conn():
    import psycopg2
    return psycopg2.connect(DB_DSN)


def _ts():
    return datetime.now(timezone.utc).isoformat()


def _uid(prefix="ev"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _wp_session():
    s = requests.Session()
    s.auth = (WP_USER, WP_PASS)
    s.headers["Accept-Encoding"] = "gzip, deflate"
    s.headers["User-Agent"] = "PetHub-Internal-Agent/1.0"
    return s


# ── Author/Editorial Trust Layer ─────────────────────────────────────────

def create_maturity_tables():
    ddl = """
    CREATE TABLE IF NOT EXISTS trust_authors (
        author_id TEXT PRIMARY KEY,
        display_name TEXT NOT NULL,
        role TEXT DEFAULT 'contributor',
        expertise_areas TEXT DEFAULT '[]',
        credentials TEXT,
        verified BOOLEAN DEFAULT FALSE,
        verification_source TEXT,
        trust_score REAL DEFAULT 0.5,
        bio TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS trust_editorial_reviews (
        review_id TEXT PRIMARY KEY,
        content_id INTEGER NOT NULL,
        reviewer TEXT,
        review_type TEXT DEFAULT 'standard',
        review_status TEXT DEFAULT 'pending',
        lint_passed BOOLEAN,
        evidence_sufficient BOOLEAN,
        claims_assessed BOOLEAN,
        notes TEXT,
        reviewed_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS trust_mismatch_routing (
        mismatch_id TEXT PRIMARY KEY,
        content_id INTEGER NOT NULL,
        content_title TEXT,
        content_url TEXT,
        mismatch_type TEXT NOT NULL,
        severity TEXT DEFAULT 'medium',
        title_count TEXT,
        body_count TEXT,
        detail TEXT,
        fix_path TEXT DEFAULT 'unassigned',
        resolution_status TEXT DEFAULT 'open',
        resolution_notes TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        resolved_at TIMESTAMP WITH TIME ZONE
    );

    CREATE INDEX IF NOT EXISTS idx_trust_evidence_content ON trust_evidence(content_id);
    CREATE INDEX IF NOT EXISTS idx_trust_claims_content ON trust_claims(content_id);
    CREATE INDEX IF NOT EXISTS idx_trust_claims_type ON trust_claims(claim_type);
    CREATE INDEX IF NOT EXISTS idx_trust_claims_risk ON trust_claims(risk_level);
    CREATE INDEX IF NOT EXISTS idx_mismatch_status ON trust_mismatch_routing(resolution_status);
    """
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()
        return {"status": "ok", "tables": ["trust_authors", "trust_editorial_reviews", "trust_mismatch_routing"]}
    finally:
        conn.close()


# ── Evidence Backfill ─────────────────────────────────────────────────────

def backfill_evidence_for_post(post_id):
    """Fetch a WordPress post and extract evidence signals into trust_evidence."""
    s = _wp_session()
    try:
        resp = s.get(f"{WP_API}/posts/{post_id}?_fields=id,title,slug,link,content,excerpt,yoast_head_json")
        if resp.status_code != 200:
            return {"error": f"WP API returned {resp.status_code}"}
        post = resp.json()
    except Exception as e:
        return {"error": str(e)}

    title = post.get("title", {}).get("rendered", "")
    html = post.get("content", {}).get("rendered", "")
    url = post.get("link", "")
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()

    evidence_records = []
    for signal_name, pattern in EVIDENCE_SIGNALS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            for m in matches[:3]:
                snippet = m if isinstance(m, str) else str(m)
                if len(snippet) > 200:
                    snippet = snippet[:200]
                etype = _classify_evidence_type(signal_name, snippet)
                confidence = _evidence_confidence(signal_name, snippet)
                evidence_records.append({
                    "evidence_type": etype,
                    "source_name": signal_name,
                    "claim_text": snippet,
                    "confidence": confidence,
                })

    overall_level = _compute_evidence_level(evidence_records)

    conn = _conn()
    inserted = 0
    try:
        with conn.cursor() as cur:
            for ev in evidence_records:
                eid = _uid("ev")
                cur.execute("""INSERT INTO trust_evidence
                    (evidence_id, content_id, evidence_type, source_name,
                     confidence_score, claim_text, status, created_at, updated_at)
                    VALUES (%s,%s,%s,%s,%s,%s,'active',NOW(),NOW())
                    ON CONFLICT DO NOTHING""",
                    (eid, post_id, ev["evidence_type"], ev["source_name"],
                     ev["confidence"], ev["claim_text"]))
                inserted += cur.rowcount

            cur.execute("""UPDATE trust_audit SET
                evidence_state=%s, updated_at=NOW()
                WHERE content_id=%s""",
                (overall_level, post_id))
        conn.commit()
    finally:
        conn.close()

    return {
        "post_id": post_id, "title": title,
        "evidence_signals_found": len(evidence_records),
        "evidence_records_inserted": inserted,
        "overall_evidence_level": overall_level,
    }


def _classify_evidence_type(signal_name, snippet):
    mapping = {
        "named_source": "source_attributed",
        "citation_link": "source_attributed",
        "data_point": "live_verified",
        "comparison_table": "editorial_inference",
        "methodology": "live_verified",
        "disclosure": "editorial_inference",
        "editorial_policy": "editorial_inference",
        "expert_quote": "source_attributed",
        "structured_list": "editorial_inference",
        "faq_section": "editorial_inference",
    }
    return mapping.get(signal_name, "editorial_inference")


def _evidence_confidence(signal_name, snippet):
    high_conf = {"named_source", "expert_quote", "methodology", "editorial_policy"}
    med_conf = {"citation_link", "data_point", "comparison_table", "disclosure"}
    if signal_name in high_conf:
        return 80
    if signal_name in med_conf:
        return 60
    return 40


def _compute_evidence_level(records):
    if not records:
        return "missing_insufficient"
    types = {r["evidence_type"] for r in records}
    max_conf = max(r["confidence"] for r in records)
    if "source_attributed" in types and max_conf >= 80:
        return "source_attributed"
    if "live_verified" in types:
        return "live_verified"
    if len(types) >= 2:
        return "editorial_inference"
    if "editorial_inference" in types:
        return "editorial_inference"
    return "estimated_proxy"


def bulk_backfill_evidence(limit=20):
    """Backfill evidence for posts that don't have evidence records yet. Paginates through all WP posts."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT content_id FROM trust_evidence")
            done = {r[0] for r in cur.fetchall()}
    finally:
        conn.close()

    s = _wp_session()
    all_posts = []
    page = 1
    while True:
        try:
            resp = s.get(f"{WP_API}/posts?per_page=50&page={page}&_fields=id,title&orderby=id&order=asc")
            if resp.status_code != 200:
                break
            batch = resp.json()
            if not batch:
                break
            all_posts.extend(batch)
            page += 1
        except Exception:
            break

    pending = [p for p in all_posts if p["id"] not in done][:limit]
    results = []
    for p in pending:
        result = backfill_evidence_for_post(p["id"])
        results.append(result)

    return {"processed": len(results), "total_posts": len(all_posts), "already_done": len(done), "results": results}


# ── Claim Extraction & Classification ─────────────────────────────────────

def extract_claims_for_post(post_id):
    """Fetch a WordPress post and extract/classify claims."""
    s = _wp_session()
    try:
        resp = s.get(f"{WP_API}/posts/{post_id}?_fields=id,title,slug,link,content")
        if resp.status_code != 200:
            return {"error": f"WP API returned {resp.status_code}"}
        post = resp.json()
    except Exception as e:
        return {"error": str(e)}

    title = post.get("title", {}).get("rendered", "")
    html = post.get("content", {}).get("rendered", "")
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    title_text = re.sub(r"<[^>]+>", "", title)

    claims = []
    full_text = title_text + " " + text

    for category, patterns in CLAIM_PATTERNS.items():
        for pattern, claim_subtype in patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for m in matches:
                start = max(0, m.start() - 40)
                end = min(len(full_text), m.end() + 40)
                context = full_text[start:end].strip()
                risk = _assess_claim_risk(category, claim_subtype, context)
                claims.append({
                    "claim_text": context[:200],
                    "claim_type": category,
                    "claim_subtype": claim_subtype,
                    "risk_level": risk,
                    "requires_disclosure": category == "urgency_discount" or claim_subtype in ("endorsement_claim", "scientific_claim"),
                    "requires_expert_source": category == "veterinary_behaviour" or claim_subtype in ("testing_claim", "scientific_claim"),
                })

    seen = set()
    unique_claims = []
    for c in claims:
        key = (c["claim_type"], c["claim_subtype"])
        if key not in seen:
            seen.add(key)
            unique_claims.append(c)

    conn = _conn()
    inserted = 0
    try:
        with conn.cursor() as cur:
            for c in unique_claims:
                cid = _uid("cl")
                cur.execute("""INSERT INTO trust_claims
                    (claim_id, content_id, claim_text, claim_type, risk_level,
                     requires_disclosure, requires_expert_source, lint_status, created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,'unchecked',NOW())
                    ON CONFLICT DO NOTHING""",
                    (cid, post_id, c["claim_text"], c["claim_type"], c["risk_level"],
                     c["requires_disclosure"], c["requires_expert_source"]))
                inserted += cur.rowcount

            risk_state = "low"
            if any(c["risk_level"] in ("high", "critical") for c in unique_claims):
                risk_state = "high"
            elif any(c["risk_level"] == "medium" for c in unique_claims):
                risk_state = "medium"

            cur.execute("""UPDATE trust_audit SET
                risk_state=%s, updated_at=NOW()
                WHERE content_id=%s""",
                (risk_state, post_id))
        conn.commit()
    finally:
        conn.close()

    return {
        "post_id": post_id, "title": title_text,
        "claims_found": len(unique_claims),
        "claims_inserted": inserted,
        "by_category": {cat: sum(1 for c in unique_claims if c["claim_type"] == cat) for cat in CLAIM_CATEGORIES if any(c["claim_type"] == cat for c in unique_claims)},
        "by_risk": {rl: sum(1 for c in unique_claims if c["risk_level"] == rl) for rl in CLAIM_RISK_LEVELS if any(c["risk_level"] == rl for c in unique_claims)},
    }


def _assess_claim_risk(category, subtype, context):
    critical_subtypes = {"scientific_claim", "endorsement_claim", "testing_claim"}
    high_risk_categories = {"veterinary_behaviour", "health_wellbeing"}
    medium_subtypes = {"safety_claim", "health_improvement", "prevention_claim", "comparison_claim"}

    if subtype in critical_subtypes:
        return "critical" if category in high_risk_categories else "high"
    if category in high_risk_categories:
        return "high"
    if subtype in medium_subtypes:
        return "medium"
    if category == "urgency_discount":
        return "medium"
    return "low"


def bulk_extract_claims(limit=20):
    """Extract claims for posts that don't have claim records yet. Paginates through all WP posts."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT content_id FROM trust_claims")
            done = {r[0] for r in cur.fetchall()}
    finally:
        conn.close()

    s = _wp_session()
    all_posts = []
    page = 1
    while True:
        try:
            resp = s.get(f"{WP_API}/posts?per_page=50&page={page}&_fields=id,title&orderby=id&order=asc")
            if resp.status_code != 200:
                break
            batch = resp.json()
            if not batch:
                break
            all_posts.extend(batch)
            page += 1
        except Exception:
            break

    pending = [p for p in all_posts if p["id"] not in done][:limit]
    results = []
    for p in pending:
        result = extract_claims_for_post(p["id"])
        results.append(result)

    return {"processed": len(results), "total_posts": len(all_posts), "already_done": len(done), "results": results}


# ── Meta-Source Truth Fix ─────────────────────────────────────────────────

def fix_meta_lint_for_post(post_id):
    """Re-run meta title/desc lint using real WordPress/RankMath data."""
    s = _wp_session()
    try:
        page_resp = s.get(f"{SITE_URL}/?p={post_id}", allow_redirects=True, timeout=30)
        if page_resp.status_code != 200:
            return {"error": f"Page fetch returned {page_resp.status_code}"}

        html = page_resp.text
        meta_title = ""
        meta_desc = ""

        title_match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
        if title_match:
            meta_title = title_match.group(1).strip()

        desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)', html, re.IGNORECASE)
        if desc_match:
            meta_desc = desc_match.group(1).strip()

        og_title = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']*)', html, re.IGNORECASE)
        if not meta_title and og_title:
            meta_title = og_title.group(1).strip()

        og_desc = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']*)', html, re.IGNORECASE)
        if not meta_desc and og_desc:
            meta_desc = og_desc.group(1).strip()

        title_pass = 30 <= len(meta_title) <= 70
        desc_pass = 50 <= len(meta_desc) <= 165

        conn = _conn()
        try:
            with conn.cursor() as cur:
                cur.execute("""UPDATE trust_lint_results SET
                    passed=%s, detail=%s
                    WHERE content_id=%s AND rule_name='weak_meta_title'""",
                    (title_pass,
                     f"Meta title: {len(meta_title)} chars" + ("" if title_pass else f" (needs 30-70, got {len(meta_title)})"),
                     post_id))
                title_updated = cur.rowcount

                cur.execute("""UPDATE trust_lint_results SET
                    passed=%s, detail=%s
                    WHERE content_id=%s AND rule_name='weak_meta_desc'""",
                    (desc_pass,
                     f"Meta desc: {len(meta_desc)} chars" + ("" if desc_pass else f" (needs 50-165, got {len(meta_desc)})"),
                     post_id))
                desc_updated = cur.rowcount
            conn.commit()
        finally:
            conn.close()

        return {
            "post_id": post_id,
            "meta_title": meta_title[:60] + ("..." if len(meta_title) > 60 else ""),
            "meta_title_len": len(meta_title),
            "meta_title_pass": title_pass,
            "meta_desc": meta_desc[:80] + ("..." if len(meta_desc) > 80 else ""),
            "meta_desc_len": len(meta_desc),
            "meta_desc_pass": desc_pass,
            "lint_records_updated": title_updated + desc_updated,
        }
    except Exception as e:
        return {"error": str(e)}


def bulk_fix_meta_lint(limit=20):
    """Fix meta lint for posts with failing meta checks."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT DISTINCT content_id FROM trust_lint_results
                WHERE rule_name IN ('weak_meta_title','weak_meta_desc')
                AND NOT passed
                ORDER BY content_id LIMIT %s""", (limit,))
            post_ids = [r[0] for r in cur.fetchall()]
    finally:
        conn.close()

    results = []
    for pid in post_ids:
        result = fix_meta_lint_for_post(pid)
        results.append(result)

    return {"processed": len(results), "results": results}


# ── Product-Count Mismatch Routing ────────────────────────────────────────

def route_product_count_mismatches():
    """Find product-count mismatch lint failures and route them through remediation."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT lr.content_id, lr.detail, lr.snippet,
                ta.content_title, ta.content_url
                FROM trust_lint_results lr
                LEFT JOIN trust_audit ta ON lr.content_id = ta.content_id
                WHERE lr.rule_name='product_count_mismatch' AND NOT lr.passed""")
            mismatches = cur.fetchall()

            routed = 0
            for row in mismatches:
                content_id, detail, snippet, title, url = row
                mid = f"mm-{hashlib.sha256(f'{content_id}-product_count'.encode()).hexdigest()[:8]}"

                title_count = ""
                body_count = ""
                title_match = re.search(r"(\d+)", title or "")
                if title_match:
                    title_count = title_match.group(1)

                severity = "low"
                if title_count:
                    tc = int(title_count)
                    if tc >= 10:
                        severity = "high"
                    elif tc >= 5:
                        severity = "medium"

                fix_path = "review_content"
                if severity == "high":
                    fix_path = "update_title_or_add_products"
                elif severity == "medium":
                    fix_path = "verify_count_accuracy"

                cur.execute("""INSERT INTO trust_mismatch_routing
                    (mismatch_id, content_id, content_title, content_url,
                     mismatch_type, severity, title_count, body_count,
                     detail, fix_path, resolution_status, created_at)
                    VALUES (%s,%s,%s,%s,'product_count',%s,%s,%s,%s,%s,'open',NOW())
                    ON CONFLICT (mismatch_id) DO UPDATE SET
                    severity=EXCLUDED.severity, fix_path=EXCLUDED.fix_path,
                    detail=EXCLUDED.detail""",
                    (mid, content_id, title or "", url or "",
                     severity, title_count, body_count,
                     detail or "Product count mismatch", fix_path))
                routed += 1
            conn.commit()

            cur.execute("""SELECT resolution_status, COUNT(*) FROM trust_mismatch_routing
                GROUP BY resolution_status""")
            status_dist = {r[0]: r[1] for r in cur.fetchall()}

            cur.execute("""SELECT severity, COUNT(*) FROM trust_mismatch_routing
                GROUP BY severity""")
            sev_dist = {r[0]: r[1] for r in cur.fetchall()}

            return {
                "mismatches_found": len(mismatches),
                "routed": routed,
                "by_status": status_dist,
                "by_severity": sev_dist,
            }
    finally:
        conn.close()


def update_mismatch(mismatch_id, resolution_status, resolution_notes=None):
    conn = _conn()
    try:
        with conn.cursor() as cur:
            resolved_at = "NOW()" if resolution_status in ("fixed", "accepted", "wont_fix") else "NULL"
            cur.execute(f"""UPDATE trust_mismatch_routing SET
                resolution_status=%s, resolution_notes=%s,
                resolved_at={resolved_at}
                WHERE mismatch_id=%s RETURNING mismatch_id""",
                (resolution_status, resolution_notes, mismatch_id))
            if not cur.fetchone():
                return {"error": "mismatch not found"}
        conn.commit()
        return {"mismatch_id": mismatch_id, "status": resolution_status}
    finally:
        conn.close()


def list_mismatches(status=None, severity=None, limit=50):
    conn = _conn()
    try:
        with conn.cursor() as cur:
            q = "SELECT * FROM trust_mismatch_routing WHERE 1=1"
            params = []
            if status:
                q += " AND resolution_status=%s"
                params.append(status)
            if severity:
                q += " AND severity=%s"
                params.append(severity)
            q += " ORDER BY CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, created_at DESC LIMIT %s"
            params.append(limit)
            cur.execute(q, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()


# ── Author/Editorial Trust ────────────────────────────────────────────────

def register_author(display_name, role="contributor", expertise_areas=None,
                    credentials=None, bio=None):
    conn = _conn()
    try:
        aid = _uid("au")
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO trust_authors
                (author_id, display_name, role, expertise_areas, credentials, bio, created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,NOW(),NOW())""",
                (aid, display_name, role,
                 json.dumps(expertise_areas or []),
                 credentials, bio))
        conn.commit()
        return {"author_id": aid, "display_name": display_name, "role": role}
    finally:
        conn.close()


def list_authors():
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM trust_authors ORDER BY display_name")
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            for r in rows:
                if isinstance(r.get("expertise_areas"), str):
                    r["expertise_areas"] = json.loads(r["expertise_areas"])
            return rows
    finally:
        conn.close()


def create_editorial_review(content_id, reviewer=None, review_type="standard"):
    conn = _conn()
    try:
        rid = _uid("rv")
        with conn.cursor() as cur:
            cur.execute("""INSERT INTO trust_editorial_reviews
                (review_id, content_id, reviewer, review_type, review_status, created_at)
                VALUES (%s,%s,%s,%s,'pending',NOW())""",
                (rid, content_id, reviewer, review_type))
        conn.commit()
        return {"review_id": rid, "content_id": content_id, "status": "pending"}
    finally:
        conn.close()


def update_editorial_review(review_id, review_status, lint_passed=None,
                            evidence_sufficient=None, claims_assessed=None, notes=None):
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""UPDATE trust_editorial_reviews SET
                review_status=%s, lint_passed=%s, evidence_sufficient=%s,
                claims_assessed=%s, notes=%s, reviewed_at=NOW()
                WHERE review_id=%s RETURNING review_id""",
                (review_status, lint_passed, evidence_sufficient,
                 claims_assessed, notes, review_id))
            if not cur.fetchone():
                return {"error": "review not found"}
        conn.commit()
        return {"review_id": review_id, "status": review_status}
    finally:
        conn.close()


def list_editorial_reviews(content_id=None, status=None, limit=50):
    conn = _conn()
    try:
        with conn.cursor() as cur:
            q = "SELECT * FROM trust_editorial_reviews WHERE 1=1"
            params = []
            if content_id:
                q += " AND content_id=%s"
                params.append(content_id)
            if status:
                q += " AND review_status=%s"
                params.append(status)
            q += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            cur.execute(q, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()


# ── Maturity Summary ──────────────────────────────────────────────────────

def get_maturity_summary():
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM trust_evidence")
            ev_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT content_id) FROM trust_evidence")
            ev_posts = cur.fetchone()[0]

            cur.execute("SELECT evidence_type, COUNT(*) FROM trust_evidence GROUP BY evidence_type ORDER BY COUNT(*) DESC")
            ev_types = {r[0]: r[1] for r in cur.fetchall()}

            cur.execute("SELECT COUNT(*) FROM trust_claims")
            cl_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT content_id) FROM trust_claims")
            cl_posts = cur.fetchone()[0]

            cur.execute("SELECT claim_type, COUNT(*) FROM trust_claims GROUP BY claim_type ORDER BY COUNT(*) DESC")
            cl_types = {r[0]: r[1] for r in cur.fetchall()}

            cur.execute("SELECT risk_level, COUNT(*) FROM trust_claims GROUP BY risk_level ORDER BY COUNT(*) DESC")
            cl_risks = {r[0]: r[1] for r in cur.fetchall()}

            cur.execute("SELECT COUNT(*) FROM trust_audit")
            total_posts = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM trust_lint_results WHERE rule_name='weak_meta_title' AND passed")
            meta_title_ok = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM trust_lint_results WHERE rule_name='weak_meta_title'")
            meta_title_total = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM trust_lint_results WHERE rule_name='weak_meta_desc' AND passed")
            meta_desc_ok = cur.fetchone()[0]

            mm_total = 0
            mm_open = 0
            mm_fixed = 0
            try:
                cur.execute("SELECT COUNT(*) FROM trust_mismatch_routing")
                mm_total = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM trust_mismatch_routing WHERE resolution_status='open'")
                mm_open = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM trust_mismatch_routing WHERE resolution_status IN ('fixed','accepted')")
                mm_fixed = cur.fetchone()[0]
            except Exception:
                pass

            cur.execute("SELECT COUNT(*) FROM trust_authors")
            author_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM trust_editorial_reviews")
            review_count = cur.fetchone()[0]

            ev_coverage_pct = round(ev_posts / total_posts * 100, 1) if total_posts > 0 else 0
            cl_coverage_pct = round(cl_posts / total_posts * 100, 1) if total_posts > 0 else 0

            return {
                "total_audited_posts": total_posts,
                "evidence_records": ev_count,
                "evidence_posts_covered": ev_posts,
                "evidence_coverage_pct": ev_coverage_pct,
                "evidence_types": ev_types,
                "claims_classified": cl_count,
                "claims_posts_covered": cl_posts,
                "claims_coverage_pct": cl_coverage_pct,
                "claims_by_type": cl_types,
                "claims_by_risk": cl_risks,
                "meta_title_truthful": meta_title_ok,
                "meta_title_total": meta_title_total,
                "meta_desc_truthful": meta_desc_ok,
                "mismatches_total": mm_total,
                "mismatches_open": mm_open,
                "mismatches_fixed": mm_fixed,
                "authors_registered": author_count,
                "editorial_reviews": review_count,
                "timestamp": _ts(),
            }
    finally:
        conn.close()


def run_full_maturity_backfill(limit=86):
    """Run complete maturity backfill: evidence + claims + meta fix + mismatch routing."""
    results = {}
    results["evidence"] = bulk_backfill_evidence(limit=limit)
    results["claims"] = bulk_extract_claims(limit=limit)
    results["meta_fix"] = bulk_fix_meta_lint(limit=limit)
    results["mismatches"] = route_product_count_mismatches()
    results["summary"] = get_maturity_summary()
    return results
