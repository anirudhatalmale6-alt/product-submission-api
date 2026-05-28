"""10I: Indexing, Crawl, and AI Search Adaptation Engine.

PostgreSQL-backed system tracking:
- Crawl health and sitemap status
- Page indexing coverage (discovered, indexed, not_indexed, error)
- AI search readiness scoring per page and per cluster
- Citation tracking across 5 AI search engines
- Structured data validation
- Content adaptation recommendations
"""
import json, os, hashlib, uuid, re, threading
from datetime import datetime, timedelta

DB_DSN = "host=127.0.0.1 port=5432 dbname=agent_manager user=productapi password=productapi"
_lock = threading.Lock()

AI_ENGINES = [
    {"key": "google_aio", "name": "Google AI Overviews", "weight": 0.35},
    {"key": "chatgpt", "name": "ChatGPT Search", "weight": 0.20},
    {"key": "perplexity", "name": "Perplexity", "weight": 0.15},
    {"key": "gemini", "name": "Gemini", "weight": 0.15},
    {"key": "bing_copilot", "name": "Bing Copilot", "weight": 0.10},
    {"key": "future", "name": "Future Engines", "weight": 0.05},
]

READINESS_CRITERIA = [
    "structured_data", "answer_format", "citation_signals", "entity_markup",
    "freshness", "evidence_depth", "trust_signals", "internal_linking",
]

STRUCTURED_DATA_TYPES = [
    "Article", "FAQPage", "HowTo", "BreadcrumbList", "WebPage",
    "Organization", "WebSite",
]

ADAPTATION_TYPES = [
    "add_faq_schema", "improve_answer_format", "add_citation_signals",
    "strengthen_entity_markup", "update_freshness", "add_evidence_depth",
    "add_trust_signals", "improve_internal_links", "add_structured_data",
]

SITE_URL = "https://pethubonline.com"


def _conn():
    import psycopg2
    return psycopg2.connect(DB_DSN)


def _ts():
    return datetime.utcnow().isoformat() + "Z"


def _uid(prefix="ix"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# ── Table creation ────────────────────────────────────────────────────────

def create_indexing_tables():
    ddl = """
    CREATE TABLE IF NOT EXISTS crawl_index_status (
        page_id TEXT PRIMARY KEY,
        url TEXT NOT NULL,
        slug TEXT,
        page_type TEXT DEFAULT 'post',
        sitemap_present BOOLEAN DEFAULT FALSE,
        index_status TEXT DEFAULT 'unknown',
        last_crawled TIMESTAMP,
        last_indexed TIMESTAMP,
        lastmod TEXT,
        http_status INTEGER,
        canonical_url TEXT,
        has_noindex BOOLEAN DEFAULT FALSE,
        structured_data_types TEXT DEFAULT '[]',
        word_count INTEGER DEFAULT 0,
        cluster_id TEXT,
        spoke_id TEXT,
        crawl_errors TEXT DEFAULT '[]',
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS ai_search_readiness (
        readiness_id TEXT PRIMARY KEY,
        page_id TEXT REFERENCES crawl_index_status(page_id),
        url TEXT NOT NULL,
        cluster_slug TEXT,
        overall_score REAL DEFAULT 0,
        structured_data_score REAL DEFAULT 0,
        answer_format_score REAL DEFAULT 0,
        citation_signals_score REAL DEFAULT 0,
        entity_markup_score REAL DEFAULT 0,
        freshness_score REAL DEFAULT 0,
        evidence_depth_score REAL DEFAULT 0,
        trust_signals_score REAL DEFAULT 0,
        internal_linking_score REAL DEFAULT 0,
        ai_engine_scores TEXT DEFAULT '{}',
        adaptations_needed TEXT DEFAULT '[]',
        last_assessed TIMESTAMP DEFAULT NOW(),
        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS ai_search_citations (
        citation_id TEXT PRIMARY KEY,
        url TEXT NOT NULL,
        page_id TEXT,
        ai_engine TEXT NOT NULL,
        query_text TEXT,
        citation_type TEXT DEFAULT 'direct',
        citation_context TEXT,
        confidence REAL DEFAULT 0.5,
        first_seen TIMESTAMP DEFAULT NOW(),
        last_seen TIMESTAMP DEFAULT NOW(),
        cluster_slug TEXT,
        verified BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_crawl_index_status ON crawl_index_status(index_status);
    CREATE INDEX IF NOT EXISTS idx_crawl_cluster ON crawl_index_status(cluster_id);
    CREATE INDEX IF NOT EXISTS idx_readiness_cluster ON ai_search_readiness(cluster_slug);
    CREATE INDEX IF NOT EXISTS idx_readiness_score ON ai_search_readiness(overall_score);
    CREATE INDEX IF NOT EXISTS idx_citations_engine ON ai_search_citations(ai_engine);
    CREATE INDEX IF NOT EXISTS idx_citations_url ON ai_search_citations(url);
    """
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()
        return {"status": "ok", "tables": ["crawl_index_status", "ai_search_readiness", "ai_search_citations"]}
    finally:
        conn.close()


# ── Crawl & Indexing ──────────────────────────────────────────────────────

def crawl_sitemap():
    """Fetch pethubonline.com sitemap and populate crawl_index_status."""
    import requests
    import xml.etree.ElementTree as ET

    sitemap_urls = [
        f"{SITE_URL}/sitemap_index.xml",
        f"{SITE_URL}/wp-sitemap.xml",
        f"{SITE_URL}/sitemap.xml",
    ]
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    discovered = {}

    for surl in sitemap_urls:
        try:
            resp = requests.get(surl, timeout=30, headers={
                "User-Agent": "PetHub-Internal-Agent/1.0"
            })
            if resp.status_code != 200:
                continue
            root = ET.fromstring(resp.text)
            child_maps = root.findall("sm:sitemap", ns)
            if child_maps:
                for sm in child_maps:
                    loc = sm.find("sm:loc", ns)
                    if loc is not None and loc.text:
                        try:
                            r2 = requests.get(loc.text.strip(), timeout=30, headers={
                                "User-Agent": "PetHub-Internal-Agent/1.0"
                            })
                            if r2.status_code == 200:
                                r2root = ET.fromstring(r2.text)
                                for u in r2root.findall("sm:url", ns):
                                    uloc = u.find("sm:loc", ns)
                                    lm = u.find("sm:lastmod", ns)
                                    if uloc is not None and uloc.text:
                                        discovered[uloc.text.strip()] = lm.text.strip() if lm is not None and lm.text else None
                        except Exception:
                            pass
            else:
                for u in root.findall("sm:url", ns):
                    uloc = u.find("sm:loc", ns)
                    lm = u.find("sm:lastmod", ns)
                    if uloc is not None and uloc.text:
                        discovered[uloc.text.strip()] = lm.text.strip() if lm is not None and lm.text else None
        except Exception:
            continue

    conn = _conn()
    inserted = 0
    updated = 0
    try:
        with conn.cursor() as cur:
            for url, lastmod in discovered.items():
                slug = url.replace(SITE_URL, "").strip("/") or "home"
                page_type = _classify_page_type(url, slug)
                page_id = "pg-" + hashlib.sha256(url.encode()).hexdigest()[:10]
                cur.execute("SELECT page_id FROM crawl_index_status WHERE page_id=%s", (page_id,))
                if cur.fetchone():
                    cur.execute("""UPDATE crawl_index_status
                        SET sitemap_present=TRUE, lastmod=%s, updated_at=NOW()
                        WHERE page_id=%s""", (lastmod, page_id))
                    updated += 1
                else:
                    cur.execute("""INSERT INTO crawl_index_status
                        (page_id, url, slug, page_type, sitemap_present, lastmod, index_status, created_at, updated_at)
                        VALUES (%s,%s,%s,%s,TRUE,%s,'discovered',NOW(),NOW())""",
                        (page_id, url, slug, page_type, lastmod))
                    inserted += 1
        conn.commit()
    finally:
        conn.close()

    return {
        "sitemap_urls_checked": len(sitemap_urls),
        "pages_discovered": len(discovered),
        "inserted": inserted,
        "updated": updated,
        "timestamp": _ts()
    }


def _classify_page_type(url, slug):
    if slug == "home" or url.rstrip("/") == SITE_URL:
        return "homepage"
    if "/category/" in url:
        return "category"
    if any(x in slug for x in ["about", "contact", "privacy", "terms", "disclaimer", "methodology"]):
        return "static"
    if "hub" in slug or slug.count("/") == 0 and any(x in slug for x in ["dog-food", "dog-toys", "cat-toys", "dog-beds", "dog-harnesses", "dog-grooming", "dog-training", "cat-supplies", "puppy-care", "dog-health"]):
        return "hub"
    return "post"


def check_page_indexing(page_id):
    """Check a single page's indexing signals (HTTP status, canonical, noindex)."""
    import requests
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT url FROM crawl_index_status WHERE page_id=%s", (page_id,))
            row = cur.fetchone()
            if not row:
                return {"error": "page not found"}
            url = row[0]

        try:
            resp = requests.get(url, timeout=30, headers={
                "User-Agent": "PetHub-Internal-Agent/1.0",
                "Accept-Encoding": "gzip, deflate"
            }, allow_redirects=True)
            http_status = resp.status_code
            has_noindex = "noindex" in resp.headers.get("X-Robots-Tag", "").lower()
            canonical = None
            if resp.status_code == 200:
                canon_match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', resp.text)
                if canon_match:
                    canonical = canon_match.group(1)
                if '<meta' in resp.text and 'noindex' in resp.text.lower():
                    noindex_match = re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)', resp.text, re.IGNORECASE)
                    if noindex_match and 'noindex' in noindex_match.group(1).lower():
                        has_noindex = True
                sd_types = _extract_structured_data_types(resp.text)
                word_count = len(re.findall(r'\w+', re.sub(r'<[^>]+>', '', resp.text)))
            else:
                sd_types = []
                word_count = 0

            idx_status = "indexed" if http_status == 200 and not has_noindex else "not_indexed"
            if http_status >= 400:
                idx_status = "error"

            with conn.cursor() as cur:
                cur.execute("""UPDATE crawl_index_status SET
                    http_status=%s, canonical_url=%s, has_noindex=%s,
                    structured_data_types=%s, word_count=%s,
                    index_status=%s, last_crawled=NOW(), updated_at=NOW()
                    WHERE page_id=%s""",
                    (http_status, canonical, has_noindex,
                     json.dumps(sd_types), word_count, idx_status, page_id))
            conn.commit()

            return {
                "page_id": page_id, "url": url, "http_status": http_status,
                "canonical": canonical, "has_noindex": has_noindex,
                "structured_data": sd_types, "word_count": word_count,
                "index_status": idx_status
            }
        except Exception as e:
            errors = [{"type": "request_error", "message": str(e), "ts": _ts()}]
            with conn.cursor() as cur:
                cur.execute("""UPDATE crawl_index_status SET
                    index_status='error', crawl_errors=%s, updated_at=NOW()
                    WHERE page_id=%s""", (json.dumps(errors), page_id))
            conn.commit()
            return {"page_id": page_id, "url": url, "error": str(e)}
    finally:
        conn.close()


def _extract_structured_data_types(html):
    types_found = set()
    ld_blocks = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
    def _add_type(val):
        if isinstance(val, str):
            types_found.add(val)
        elif isinstance(val, list):
            for v in val:
                if isinstance(v, str):
                    types_found.add(v)
    for block in ld_blocks:
        try:
            data = json.loads(block)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "@type" in item:
                        _add_type(item["@type"])
            elif isinstance(data, dict):
                if "@type" in data:
                    _add_type(data["@type"])
                if "@graph" in data:
                    for item in data["@graph"]:
                        if isinstance(item, dict) and "@type" in item:
                            _add_type(item["@type"])
        except (json.JSONDecodeError, TypeError):
            pass
    return list(types_found)


def bulk_check_indexing(limit=20):
    """Check indexing for pages that haven't been crawled recently."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT page_id FROM crawl_index_status
                WHERE last_crawled IS NULL OR last_crawled < NOW() - INTERVAL '24 hours'
                ORDER BY last_crawled ASC NULLS FIRST LIMIT %s""", (limit,))
            page_ids = [r[0] for r in cur.fetchall()]
    finally:
        conn.close()

    results = []
    for pid in page_ids:
        results.append(check_page_indexing(pid))
    return {"checked": len(results), "results": results}


# ── AI Search Readiness ───────────────────────────────────────────────────

def assess_page_readiness(page_id):
    """Score a page's readiness for AI search engines."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT page_id, url, slug, page_type, structured_data_types,
                word_count, has_noindex, http_status, cluster_id
                FROM crawl_index_status WHERE page_id=%s""", (page_id,))
            row = cur.fetchone()
            if not row:
                return {"error": "page not found"}

            pid, url, slug, ptype, sd_json, wc, noindex, status, cluster = row
            sd_types = json.loads(sd_json) if sd_json else []

            structured_data_score = _score_structured_data(sd_types, ptype)
            answer_format_score = _score_answer_format(wc, ptype)
            citation_signals_score = _score_citation_signals(sd_types, wc)
            entity_markup_score = _score_entity_markup(sd_types)
            freshness_score = _score_freshness(page_id, cur)
            evidence_depth_score = _score_evidence_depth(wc, ptype)
            trust_signals_score = _score_trust_signals(sd_types, ptype)
            internal_linking_score = _score_internal_linking(page_id, cluster, cur)

            overall = round((
                structured_data_score * 0.15 +
                answer_format_score * 0.15 +
                citation_signals_score * 0.15 +
                entity_markup_score * 0.10 +
                freshness_score * 0.10 +
                evidence_depth_score * 0.15 +
                trust_signals_score * 0.10 +
                internal_linking_score * 0.10
            ), 2)

            engine_scores = {}
            for eng in AI_ENGINES:
                base = overall
                if eng["key"] == "google_aio":
                    base = (structured_data_score * 0.25 + answer_format_score * 0.25 +
                            entity_markup_score * 0.15 + freshness_score * 0.15 +
                            evidence_depth_score * 0.1 + trust_signals_score * 0.1)
                elif eng["key"] == "chatgpt":
                    base = (evidence_depth_score * 0.25 + citation_signals_score * 0.25 +
                            trust_signals_score * 0.2 + answer_format_score * 0.15 +
                            freshness_score * 0.15)
                elif eng["key"] == "perplexity":
                    base = (citation_signals_score * 0.3 + evidence_depth_score * 0.25 +
                            freshness_score * 0.2 + trust_signals_score * 0.15 +
                            structured_data_score * 0.1)
                engine_scores[eng["key"]] = round(base, 2)

            adaptations = _identify_adaptations(
                structured_data_score, answer_format_score, citation_signals_score,
                entity_markup_score, freshness_score, evidence_depth_score,
                trust_signals_score, internal_linking_score, sd_types, ptype
            )

            readiness_id = "rd-" + hashlib.sha256(f"{page_id}-readiness".encode()).hexdigest()[:10]
            cluster_slug = _resolve_cluster_slug(cluster, slug)

            cur.execute("SELECT readiness_id FROM ai_search_readiness WHERE readiness_id=%s", (readiness_id,))
            if cur.fetchone():
                cur.execute("""UPDATE ai_search_readiness SET
                    overall_score=%s, structured_data_score=%s, answer_format_score=%s,
                    citation_signals_score=%s, entity_markup_score=%s, freshness_score=%s,
                    evidence_depth_score=%s, trust_signals_score=%s, internal_linking_score=%s,
                    ai_engine_scores=%s, adaptations_needed=%s, last_assessed=NOW()
                    WHERE readiness_id=%s""",
                    (overall, structured_data_score, answer_format_score,
                     citation_signals_score, entity_markup_score, freshness_score,
                     evidence_depth_score, trust_signals_score, internal_linking_score,
                     json.dumps(engine_scores), json.dumps(adaptations), readiness_id))
            else:
                cur.execute("""INSERT INTO ai_search_readiness
                    (readiness_id, page_id, url, cluster_slug, overall_score,
                     structured_data_score, answer_format_score, citation_signals_score,
                     entity_markup_score, freshness_score, evidence_depth_score,
                     trust_signals_score, internal_linking_score, ai_engine_scores,
                     adaptations_needed, last_assessed, created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),NOW())""",
                    (readiness_id, page_id, url, cluster_slug, overall,
                     structured_data_score, answer_format_score, citation_signals_score,
                     entity_markup_score, freshness_score, evidence_depth_score,
                     trust_signals_score, internal_linking_score, json.dumps(engine_scores),
                     json.dumps(adaptations)))
        conn.commit()
        return {
            "readiness_id": readiness_id, "page_id": page_id, "url": url,
            "cluster": cluster_slug, "overall_score": overall,
            "scores": {
                "structured_data": structured_data_score,
                "answer_format": answer_format_score,
                "citation_signals": citation_signals_score,
                "entity_markup": entity_markup_score,
                "freshness": freshness_score,
                "evidence_depth": evidence_depth_score,
                "trust_signals": trust_signals_score,
                "internal_linking": internal_linking_score,
            },
            "engine_scores": engine_scores,
            "adaptations_needed": adaptations,
        }
    finally:
        conn.close()


def _score_structured_data(sd_types, ptype):
    if not sd_types:
        return 0.1
    score = 0.3
    if "Article" in sd_types or "BlogPosting" in sd_types:
        score += 0.2
    if "FAQPage" in sd_types:
        score += 0.15
    if "HowTo" in sd_types:
        score += 0.15
    if "BreadcrumbList" in sd_types:
        score += 0.1
    if "Organization" in sd_types or "WebSite" in sd_types:
        score += 0.1
    return min(round(score, 2), 1.0)


def _score_answer_format(word_count, ptype):
    if word_count < 300:
        return 0.2
    if word_count < 800:
        return 0.4
    if word_count < 1500:
        return 0.6
    if word_count < 3000:
        return 0.8
    return 0.9


def _score_citation_signals(sd_types, word_count):
    score = 0.2
    if word_count > 1000:
        score += 0.2
    if word_count > 2000:
        score += 0.1
    if any(t in sd_types for t in ["Article", "BlogPosting"]):
        score += 0.15
    if "FAQPage" in sd_types:
        score += 0.15
    if "Organization" in sd_types:
        score += 0.1
    return min(round(score, 2), 1.0)


def _score_entity_markup(sd_types):
    score = 0.15
    if "Organization" in sd_types:
        score += 0.25
    if "WebSite" in sd_types:
        score += 0.15
    if "Person" in sd_types:
        score += 0.2
    if any(t in sd_types for t in ["Article", "BlogPosting"]):
        score += 0.15
    if "BreadcrumbList" in sd_types:
        score += 0.1
    return min(round(score, 2), 1.0)


def _score_freshness(page_id, cur):
    cur.execute("SELECT lastmod FROM crawl_index_status WHERE page_id=%s", (page_id,))
    row = cur.fetchone()
    if not row or not row[0]:
        return 0.3
    try:
        lm = row[0]
        if isinstance(lm, str):
            lm = datetime.fromisoformat(lm.replace("Z", "+00:00").replace("T", " ").split("+")[0])
        age_days = (datetime.utcnow() - lm).days
        if age_days < 7:
            return 0.95
        if age_days < 30:
            return 0.8
        if age_days < 90:
            return 0.6
        if age_days < 180:
            return 0.4
        return 0.2
    except Exception:
        return 0.3


def _score_evidence_depth(word_count, ptype):
    if ptype in ("category", "homepage", "static"):
        return 0.5
    if word_count < 500:
        return 0.2
    if word_count < 1000:
        return 0.4
    if word_count < 2000:
        return 0.6
    if word_count < 3000:
        return 0.75
    return 0.85


def _score_trust_signals(sd_types, ptype):
    score = 0.2
    if "Organization" in sd_types:
        score += 0.2
    if any(t in sd_types for t in ["Article", "BlogPosting"]):
        score += 0.15
    if ptype == "post":
        score += 0.1
    if "WebSite" in sd_types:
        score += 0.1
    return min(round(score, 2), 0.85)


def _score_internal_linking(page_id, cluster_id, cur):
    if not cluster_id:
        return 0.3
    cur.execute("""SELECT COUNT(*) FROM expansion_link_plan
        WHERE (source_spoke_id IN (SELECT spoke_id FROM expansion_spokes WHERE cluster_id=%s)
        OR target_spoke_id IN (SELECT spoke_id FROM expansion_spokes WHERE cluster_id=%s))
        AND status != 'broken'""", (cluster_id, cluster_id))
    row = cur.fetchone()
    count = row[0] if row else 0
    if count >= 5:
        return 0.8
    if count >= 3:
        return 0.6
    if count >= 1:
        return 0.4
    return 0.3


def _resolve_cluster_slug(cluster_id, slug):
    cluster_map = {
        "dog-food": "dog_food", "dog-toys": "dog_toys", "cat-toys": "cat_toys",
        "dog-beds": "dog_beds", "dog-harnesses": "dog_harnesses",
        "dog-health": "dog_health", "dog-grooming": "dog_grooming",
        "dog-training": "dog_training", "cat-supplies": "cat_supplies",
        "puppy-care": "puppy_care",
    }
    if cluster_id:
        conn2 = _conn()
        try:
            with conn2.cursor() as cur:
                cur.execute("SELECT slug FROM expansion_clusters WHERE cluster_id=%s", (cluster_id,))
                row = cur.fetchone()
                if row:
                    return row[0]
        finally:
            conn2.close()
    for prefix, cs in cluster_map.items():
        if prefix in slug:
            return cs
    return "uncategorized"


def _identify_adaptations(sd, af, cs, em, fr, ed, ts, il, sd_types, ptype):
    adaptations = []
    if sd < 0.5 and "FAQPage" not in sd_types:
        adaptations.append("add_faq_schema")
    if sd < 0.4:
        adaptations.append("add_structured_data")
    if af < 0.5:
        adaptations.append("improve_answer_format")
    if cs < 0.4:
        adaptations.append("add_citation_signals")
    if em < 0.4:
        adaptations.append("strengthen_entity_markup")
    if fr < 0.5:
        adaptations.append("update_freshness")
    if ed < 0.5 and ptype == "post":
        adaptations.append("add_evidence_depth")
    if ts < 0.4:
        adaptations.append("add_trust_signals")
    if il < 0.4:
        adaptations.append("improve_internal_links")
    return adaptations


def bulk_assess_readiness(limit=20):
    """Assess AI search readiness for pages that haven't been assessed."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT c.page_id FROM crawl_index_status c
                LEFT JOIN ai_search_readiness r ON c.page_id = r.page_id
                WHERE c.index_status IN ('indexed','discovered')
                AND c.http_status IS NOT NULL
                AND (r.readiness_id IS NULL OR r.last_assessed < NOW() - INTERVAL '24 hours')
                ORDER BY r.last_assessed ASC NULLS FIRST LIMIT %s""", (limit,))
            page_ids = [r[0] for r in cur.fetchall()]
    finally:
        conn.close()

    results = []
    for pid in page_ids:
        results.append(assess_page_readiness(pid))
    return {"assessed": len(results), "results": results}


# ── Citation Tracking ─────────────────────────────────────────────────────

def record_citation(url, ai_engine, query_text, citation_type="direct",
                    citation_context=None, confidence=0.5, cluster_slug=None):
    conn = _conn()
    try:
        cid = "ct-" + hashlib.sha256(f"{url}-{ai_engine}-{query_text}".encode()).hexdigest()[:10]
        page_id = "pg-" + hashlib.sha256(url.encode()).hexdigest()[:10]
        with conn.cursor() as cur:
            cur.execute("SELECT page_id FROM crawl_index_status WHERE page_id=%s", (page_id,))
            if not cur.fetchone():
                page_id = None

            cur.execute("SELECT citation_id FROM ai_search_citations WHERE citation_id=%s", (cid,))
            if cur.fetchone():
                cur.execute("""UPDATE ai_search_citations SET
                    last_seen=NOW(), confidence=%s WHERE citation_id=%s""",
                    (confidence, cid))
            else:
                cur.execute("""INSERT INTO ai_search_citations
                    (citation_id, url, page_id, ai_engine, query_text, citation_type,
                     citation_context, confidence, cluster_slug, created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())""",
                    (cid, url, page_id, ai_engine, query_text, citation_type,
                     citation_context, confidence, cluster_slug))
        conn.commit()
        return {"citation_id": cid, "status": "recorded"}
    finally:
        conn.close()


def list_citations(ai_engine=None, cluster_slug=None, limit=50):
    conn = _conn()
    try:
        with conn.cursor() as cur:
            q = "SELECT * FROM ai_search_citations WHERE 1=1"
            params = []
            if ai_engine:
                q += " AND ai_engine=%s"
                params.append(ai_engine)
            if cluster_slug:
                q += " AND cluster_slug=%s"
                params.append(cluster_slug)
            q += " ORDER BY last_seen DESC LIMIT %s"
            params.append(limit)
            cur.execute(q, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()


# ── Summary & Reporting ───────────────────────────────────────────────────

def get_indexing_summary():
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM crawl_index_status")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM crawl_index_status WHERE index_status='indexed'")
            indexed = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM crawl_index_status WHERE index_status='not_indexed'")
            not_indexed = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM crawl_index_status WHERE index_status='error'")
            errors = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM crawl_index_status WHERE index_status='discovered'")
            discovered = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM crawl_index_status WHERE sitemap_present=TRUE")
            in_sitemap = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM crawl_index_status WHERE has_noindex=TRUE")
            noindexed = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM ai_search_readiness")
            assessed = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(AVG(overall_score),0) FROM ai_search_readiness")
            avg_readiness = round(cur.fetchone()[0], 2)
            cur.execute("SELECT COUNT(*) FROM ai_search_readiness WHERE overall_score >= 0.7")
            ready_pages = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM ai_search_readiness WHERE overall_score < 0.4")
            needs_work = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM ai_search_citations")
            total_citations = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT ai_engine) FROM ai_search_citations")
            engines_citing = cur.fetchone()[0]

            cur.execute("""SELECT index_status, COUNT(*) FROM crawl_index_status
                GROUP BY index_status ORDER BY COUNT(*) DESC""")
            status_dist = {r[0]: r[1] for r in cur.fetchall()}

            cur.execute("""SELECT page_type, COUNT(*) FROM crawl_index_status
                GROUP BY page_type ORDER BY COUNT(*) DESC""")
            type_dist = {r[0]: r[1] for r in cur.fetchall()}

            return {
                "total_pages": total,
                "indexed": indexed,
                "not_indexed": not_indexed,
                "errors": errors,
                "discovered": discovered,
                "in_sitemap": in_sitemap,
                "noindexed": noindexed,
                "assessed": assessed,
                "avg_readiness": avg_readiness,
                "ready_pages": ready_pages,
                "needs_work": needs_work,
                "total_citations": total_citations,
                "engines_citing": engines_citing,
                "status_distribution": status_dist,
                "type_distribution": type_dist,
                "timestamp": _ts(),
            }
    finally:
        conn.close()


def get_cluster_readiness():
    """Get AI search readiness aggregated by cluster."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT cluster_slug,
                COUNT(*) as pages,
                ROUND(AVG(overall_score)::numeric, 2) as avg_score,
                ROUND(AVG(structured_data_score)::numeric, 2) as avg_sd,
                ROUND(AVG(answer_format_score)::numeric, 2) as avg_af,
                ROUND(AVG(citation_signals_score)::numeric, 2) as avg_cs,
                ROUND(AVG(entity_markup_score)::numeric, 2) as avg_em,
                ROUND(AVG(freshness_score)::numeric, 2) as avg_fr,
                ROUND(AVG(evidence_depth_score)::numeric, 2) as avg_ed,
                ROUND(AVG(trust_signals_score)::numeric, 2) as avg_ts,
                ROUND(AVG(internal_linking_score)::numeric, 2) as avg_il,
                COUNT(*) FILTER (WHERE overall_score >= 0.7) as ready,
                COUNT(*) FILTER (WHERE overall_score < 0.4) as needs_work
                FROM ai_search_readiness
                GROUP BY cluster_slug
                ORDER BY avg_score DESC""")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()


def get_engine_readiness():
    """Get readiness scores broken down by AI engine."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT ai_engine_scores FROM ai_search_readiness")
            rows = cur.fetchall()

        engine_totals = {e["key"]: [] for e in AI_ENGINES}
        for row in rows:
            scores = json.loads(row[0]) if row[0] else {}
            for ekey, val in scores.items():
                if ekey in engine_totals:
                    engine_totals[ekey].append(val)

        result = []
        for eng in AI_ENGINES:
            vals = engine_totals.get(eng["key"], [])
            result.append({
                "engine": eng["name"],
                "key": eng["key"],
                "weight": eng["weight"],
                "pages_assessed": len(vals),
                "avg_score": round(sum(vals)/len(vals), 2) if vals else 0,
                "ready_count": sum(1 for v in vals if v >= 0.7),
                "needs_work": sum(1 for v in vals if v < 0.4),
            })
        return result
    finally:
        conn.close()


def get_adaptation_queue(limit=30):
    """Get pages needing adaptation, sorted by potential impact."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT r.readiness_id, r.page_id, r.url, r.cluster_slug,
                r.overall_score, r.adaptations_needed, c.page_type, c.word_count
                FROM ai_search_readiness r
                JOIN crawl_index_status c ON r.page_id = c.page_id
                WHERE r.overall_score < 0.7
                ORDER BY r.overall_score ASC
                LIMIT %s""", (limit,))
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            for r in rows:
                if isinstance(r["adaptations_needed"], str):
                    r["adaptations_needed"] = json.loads(r["adaptations_needed"])
            return rows
    finally:
        conn.close()


def get_pages(index_status=None, page_type=None, limit=100):
    conn = _conn()
    try:
        with conn.cursor() as cur:
            q = "SELECT * FROM crawl_index_status WHERE 1=1"
            params = []
            if index_status:
                q += " AND index_status=%s"
                params.append(index_status)
            if page_type:
                q += " AND page_type=%s"
                params.append(page_type)
            q += " ORDER BY updated_at DESC LIMIT %s"
            params.append(limit)
            cur.execute(q, params)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()


def get_readiness_list(cluster_slug=None, min_score=None, max_score=None, limit=100):
    conn = _conn()
    try:
        with conn.cursor() as cur:
            q = "SELECT * FROM ai_search_readiness WHERE 1=1"
            params = []
            if cluster_slug:
                q += " AND cluster_slug=%s"
                params.append(cluster_slug)
            if min_score is not None:
                q += " AND overall_score >= %s"
                params.append(min_score)
            if max_score is not None:
                q += " AND overall_score <= %s"
                params.append(max_score)
            q += " ORDER BY overall_score DESC LIMIT %s"
            params.append(limit)
            cur.execute(q, params)
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            for r in rows:
                if isinstance(r.get("ai_engine_scores"), str):
                    r["ai_engine_scores"] = json.loads(r["ai_engine_scores"])
                if isinstance(r.get("adaptations_needed"), str):
                    r["adaptations_needed"] = json.loads(r["adaptations_needed"])
            return rows
    finally:
        conn.close()


def link_pages_to_clusters():
    """Link crawl_index_status pages to expansion_clusters where possible."""
    conn = _conn()
    linked = 0
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT s.spoke_id, s.slug, s.cluster_id
                FROM expansion_spokes s WHERE s.status='published'""")
            spokes = cur.fetchall()
            for spoke_id, slug, cluster_id in spokes:
                cur.execute("""UPDATE crawl_index_status
                    SET cluster_id=%s, spoke_id=%s, updated_at=NOW()
                    WHERE slug LIKE %s AND cluster_id IS NULL""",
                    (cluster_id, spoke_id, f"%{slug}%"))
                linked += cur.rowcount
        conn.commit()
    finally:
        conn.close()
    return {"linked": linked}


def run_full_scan():
    """Run complete scan: crawl sitemap, check indexing, assess readiness, link clusters."""
    results = {}
    results["sitemap"] = crawl_sitemap()
    results["indexing"] = bulk_check_indexing(limit=50)
    link_pages_to_clusters()
    results["readiness"] = bulk_assess_readiness(limit=50)
    results["summary"] = get_indexing_summary()
    return results


# ── Orphan Detection + Broken Link Scanner ──────────────────────────────

def detect_orphan_pages():
    """Identify pages with zero inbound internal links (orphan risk)."""
    import psycopg2.extras
    conn = _conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT c.page_id, c.url, c.slug as title, c.index_status, c.sitemap_present,
                    COALESCE(link_count.inbound, 0) as inbound_links
                FROM crawl_index_status c
                LEFT JOIN (
                    SELECT target_spoke_id, COUNT(*) as inbound
                    FROM expansion_link_plan
                    WHERE status != 'broken' AND status != 'removed'
                    GROUP BY target_spoke_id
                ) link_count ON c.page_id::text = link_count.target_spoke_id
                WHERE COALESCE(link_count.inbound, 0) = 0
                ORDER BY c.slug
            """)
            orphans = [dict(r) for r in cur.fetchall()]
            return {
                "orphan_count": len(orphans),
                "orphan_pages": orphans,
                "total_pages_checked": _get_total_pages(cur),
            }
    finally:
        conn.close()


def scan_broken_links():
    """Scan expansion_link_plan for broken links and report them."""
    import psycopg2.extras
    conn = _conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT link_id, source_spoke_id, target_spoke_id, anchor_text,
                    link_type, status, created_at
                FROM expansion_link_plan
                WHERE status = 'broken'
                ORDER BY created_at DESC
            """)
            broken = [dict(r) for r in cur.fetchall()]

            cur.execute("SELECT COUNT(*) FROM expansion_link_plan")
            total = cur.fetchone()["count"]

            return {
                "broken_count": len(broken),
                "total_links": total,
                "broken_links": broken,
            }
    except Exception:
        return {"broken_count": 0, "total_links": 0, "broken_links": [], "note": "expansion_link_plan table may not exist"}
    finally:
        conn.close()


def _get_total_pages(cur):
    cur.execute("SELECT COUNT(*) as cnt FROM crawl_index_status")
    return cur.fetchone()["cnt"]


# ── 10I PATCHES: Broken-Link Crawler + Crawl Monitoring + Publish Trigger ──

def create_10i_patch_tables():
    """Create tables for crawl monitoring, broken links, and publish triggers."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS crawl_budget_monitoring (
                    id SERIAL PRIMARY KEY,
                    check_id TEXT UNIQUE NOT NULL,
                    total_pages INTEGER DEFAULT 0,
                    indexed_pages INTEGER DEFAULT 0,
                    not_indexed_pages INTEGER DEFAULT 0,
                    error_pages INTEGER DEFAULT 0,
                    crawl_rate FLOAT DEFAULT 0.0,
                    index_rate FLOAT DEFAULT 0.0,
                    degradation_alert BOOLEAN DEFAULT FALSE,
                    alert_reason TEXT,
                    checked_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS broken_link_scan (
                    id SERIAL PRIMARY KEY,
                    scan_id TEXT UNIQUE NOT NULL,
                    source_url TEXT NOT NULL,
                    source_post_id INTEGER,
                    target_url TEXT NOT NULL,
                    http_status INTEGER,
                    link_text TEXT,
                    link_type TEXT DEFAULT 'internal',
                    is_broken BOOLEAN DEFAULT FALSE,
                    first_detected TIMESTAMPTZ DEFAULT NOW(),
                    last_checked TIMESTAMPTZ DEFAULT NOW(),
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMPTZ
                );

                CREATE TABLE IF NOT EXISTS publish_trigger_log (
                    id SERIAL PRIMARY KEY,
                    trigger_id TEXT UNIQUE NOT NULL,
                    post_id INTEGER NOT NULL,
                    post_title TEXT,
                    post_url TEXT,
                    action TEXT DEFAULT 'publish',
                    triggered_at TIMESTAMPTZ DEFAULT NOW(),
                    sitemap_submitted_at TIMESTAMPTZ,
                    first_crawled_at TIMESTAMPTZ,
                    first_indexed_at TIMESTAMPTZ,
                    time_to_crawl_seconds INTEGER,
                    time_to_index_seconds INTEGER,
                    status TEXT DEFAULT 'triggered'
                );

                CREATE INDEX IF NOT EXISTS idx_broken_link_source ON broken_link_scan(source_post_id);
                CREATE INDEX IF NOT EXISTS idx_broken_link_broken ON broken_link_scan(is_broken) WHERE is_broken = TRUE;
                CREATE INDEX IF NOT EXISTS idx_publish_trigger_status ON publish_trigger_log(status);
            """)
            conn.commit()
            return {"status": "ok", "tables_created": ["crawl_budget_monitoring", "broken_link_scan", "publish_trigger_log"]}
    finally:
        conn.close()


def run_broken_link_crawler(limit=50):
    """Active broken-link crawler: fetches pages, extracts internal links, checks each one."""
    import requests
    import psycopg2.extras
    from bs4 import BeautifulSoup

    conn = _conn()
    results = {"scanned_pages": 0, "links_checked": 0, "broken_found": 0, "errors": []}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT page_id, url FROM crawl_index_status WHERE http_status = 200 ORDER BY last_crawled ASC NULLS FIRST LIMIT %s", (limit,))
            pages = cur.fetchall()

        for page in pages:
            try:
                resp = requests.get(page["url"], timeout=10, allow_redirects=True,
                                    headers={"User-Agent": "PetHub-LinkChecker/1.0"})
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                links = soup.find_all("a", href=True)
                results["scanned_pages"] += 1

                for link in links:
                    href = link.get("href", "")
                    if not href.startswith(SITE_URL):
                        continue

                    text = link.get_text(strip=True)[:100]
                    results["links_checked"] += 1

                    try:
                        lr = requests.head(href, timeout=5, allow_redirects=True,
                                          headers={"User-Agent": "PetHub-LinkChecker/1.0"})
                        status = lr.status_code
                        is_broken = status >= 400
                    except:
                        status = 0
                        is_broken = True

                    if is_broken:
                        results["broken_found"] += 1

                    scan_id = f"bl-{hashlib.md5(f'{page["url"]}-{href}'.encode()).hexdigest()[:12]}"
                    with conn.cursor() as cur2:
                        cur2.execute("""
                            INSERT INTO broken_link_scan (scan_id, source_url, source_post_id, target_url, http_status, link_text, is_broken, last_checked)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                            ON CONFLICT (scan_id) DO UPDATE SET http_status = %s, is_broken = %s, last_checked = NOW()
                        """, (scan_id, page["url"], page.get("page_id"), href, status, text, is_broken, status, is_broken))
                    conn.commit()

            except Exception as e:
                results["errors"].append(f"{page['url']}: {str(e)[:60]}")

        return results
    finally:
        conn.close()


def get_broken_links(limit=50):
    """Return all broken links found by the crawler."""
    import psycopg2.extras
    conn = _conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT scan_id, source_url, source_post_id, target_url, http_status, link_text, first_detected, last_checked
                FROM broken_link_scan
                WHERE is_broken = TRUE AND resolved = FALSE
                ORDER BY first_detected DESC
                LIMIT %s
            """, (limit,))
            broken = [dict(r) for r in cur.fetchall()]
            cur.execute("SELECT COUNT(*) as cnt FROM broken_link_scan WHERE is_broken = TRUE AND resolved = FALSE")
            total_broken = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) as cnt FROM broken_link_scan")
            total_scanned = cur.fetchone()["cnt"]
            return {"total_broken": total_broken, "total_scanned": total_scanned, "broken_links": broken}
    finally:
        conn.close()


def run_crawl_budget_check():
    """Check crawl budget health and detect degradation."""
    import psycopg2.extras
    conn = _conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN index_status = 'indexed' THEN 1 ELSE 0 END) as indexed,
                    SUM(CASE WHEN index_status = 'not_indexed' THEN 1 ELSE 0 END) as not_indexed,
                    SUM(CASE WHEN http_status >= 400 OR http_status = 0 THEN 1 ELSE 0 END) as errors
                FROM crawl_index_status
            """)
            stats = dict(cur.fetchone())

            total = stats["total"] or 1
            index_rate = (stats["indexed"] or 0) / total
            crawl_rate = 1.0 - ((stats["not_indexed"] or 0) / total)

            # Check for degradation vs previous check
            degradation = False
            alert_reason = None

            cur.execute("SELECT index_rate, crawl_rate FROM crawl_budget_monitoring ORDER BY checked_at DESC LIMIT 1")
            prev = cur.fetchone()
            if prev:
                if index_rate < prev["index_rate"] - 0.05:
                    degradation = True
                    alert_reason = f"Index rate dropped from {prev['index_rate']:.2f} to {index_rate:.2f}"
                elif crawl_rate < prev["crawl_rate"] - 0.05:
                    degradation = True
                    alert_reason = f"Crawl rate dropped from {prev['crawl_rate']:.2f} to {crawl_rate:.2f}"

            if stats["errors"] and stats["errors"] > 3:
                degradation = True
                alert_reason = (alert_reason or "") + f" {stats['errors']} error pages detected."

            check_id = f"cb-{_ts()}"
            cur.execute("""
                INSERT INTO crawl_budget_monitoring
                    (check_id, total_pages, indexed_pages, not_indexed_pages, error_pages, crawl_rate, index_rate, degradation_alert, alert_reason)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (check_id, stats["total"], stats["indexed"], stats["not_indexed"], stats["errors"],
                  crawl_rate, index_rate, degradation, alert_reason))
            conn.commit()

            return {
                "check_id": check_id,
                "total_pages": stats["total"],
                "indexed": stats["indexed"],
                "not_indexed": stats["not_indexed"],
                "errors": stats["errors"],
                "crawl_rate": round(crawl_rate, 3),
                "index_rate": round(index_rate, 3),
                "degradation_alert": degradation,
                "alert_reason": alert_reason
            }
    finally:
        conn.close()


def get_crawl_budget_history(limit=20):
    """Return crawl budget monitoring history."""
    import psycopg2.extras
    conn = _conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT check_id, total_pages, indexed_pages, not_indexed_pages, error_pages,
                       crawl_rate, index_rate, degradation_alert, alert_reason, checked_at
                FROM crawl_budget_monitoring
                ORDER BY checked_at DESC
                LIMIT %s
            """, (limit,))
            return {"history": [dict(r) for r in cur.fetchall()]}
    finally:
        conn.close()


def register_publish_trigger(post_id, post_title=None, post_url=None):
    """Register a publish event and start time-to-index tracking."""
    conn = _conn()
    try:
        trigger_id = f"pub-{post_id}-{_ts()}"
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO publish_trigger_log (trigger_id, post_id, post_title, post_url, action, status)
                VALUES (%s, %s, %s, %s, 'publish', 'triggered')
            """, (trigger_id, post_id, post_title, post_url))
            conn.commit()
        return {"trigger_id": trigger_id, "post_id": post_id, "status": "triggered"}
    finally:
        conn.close()


def check_publish_index_status():
    """Check pending publish triggers and update time-to-crawl/index."""
    import requests
    import psycopg2.extras

    conn = _conn()
    results = {"checked": 0, "crawled": 0, "indexed": 0}
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT trigger_id, post_id, post_url, triggered_at, first_crawled_at, first_indexed_at
                FROM publish_trigger_log
                WHERE status != 'indexed'
                ORDER BY triggered_at DESC
                LIMIT 50
            """)
            pending = cur.fetchall()

        for p in pending:
            results["checked"] += 1
            url = p["post_url"]
            if not url:
                continue

            try:
                resp = requests.head(url, timeout=10, allow_redirects=True,
                                    headers={"User-Agent": "PetHub-IndexChecker/1.0"})
                if resp.status_code == 200 and not p["first_crawled_at"]:
                    triggered = p["triggered_at"]
                    ttc = int((datetime.now(triggered.tzinfo) - triggered).total_seconds()) if triggered else None
                    with conn.cursor() as cur2:
                        cur2.execute("""
                            UPDATE publish_trigger_log SET
                                first_crawled_at = NOW(),
                                time_to_crawl_seconds = %s,
                                status = 'crawled'
                            WHERE trigger_id = %s AND first_crawled_at IS NULL
                        """, (ttc, p["trigger_id"]))
                    conn.commit()
                    results["crawled"] += 1
            except:
                pass

            # Check index status from crawl_index_status
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur3:
                cur3.execute("SELECT index_status FROM crawl_index_status WHERE url = %s", (url,))
                idx = cur3.fetchone()
                if idx and idx["index_status"] == "indexed" and not p["first_indexed_at"]:
                    triggered = p["triggered_at"]
                    tti = int((datetime.now(triggered.tzinfo) - triggered).total_seconds()) if triggered else None
                    cur3.execute("""
                        UPDATE publish_trigger_log SET
                            first_indexed_at = NOW(),
                            time_to_index_seconds = %s,
                            status = 'indexed'
                        WHERE trigger_id = %s AND first_indexed_at IS NULL
                    """, (tti, p["trigger_id"]))
                    conn.commit()
                    results["indexed"] += 1

        return results
    finally:
        conn.close()


def get_publish_trigger_log(limit=20):
    """Return recent publish trigger events with time-to-index data."""
    import psycopg2.extras
    conn = _conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT trigger_id, post_id, post_title, post_url, action, triggered_at,
                       sitemap_submitted_at, first_crawled_at, first_indexed_at,
                       time_to_crawl_seconds, time_to_index_seconds, status
                FROM publish_trigger_log
                ORDER BY triggered_at DESC
                LIMIT %s
            """, (limit,))
            return {"triggers": [dict(r) for r in cur.fetchall()]}
    finally:
        conn.close()
