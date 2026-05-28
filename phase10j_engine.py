"""Phase 10J: Citation, Schema, Freshness, Competitor Engine Functions."""

def _10j_conn():
    import psycopg2
    return psycopg2.connect(host='127.0.0.1', port=5432, dbname='agent_manager', user='productapi', password='productapi')


def get_10j_summary():
    import psycopg2.extras
    conn = _10j_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM ai_citation_events")
            citations = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) as cnt FROM ai_query_tracking")
            queries = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) as cnt FROM schema_recommendations")
            schemas = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) as cnt FROM schema_recommendations WHERE status = 'recommended'")
            pending_schemas = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) as cnt FROM freshness_cadence")
            freshness = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) as cnt FROM freshness_cadence WHERE staleness_risk IN ('high', 'critical')")
            stale = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) as cnt FROM competitor_analysis")
            competitors = cur.fetchone()["cnt"]
            return {
                "citation_events": citations,
                "queries_tracked": queries,
                "schema_recommendations": schemas,
                "pending_schema_recs": pending_schemas,
                "freshness_tracked": freshness,
                "stale_risk_pages": stale,
                "competitors_tracked": competitors,
                "mode": "preparation_only"
            }
    finally:
        conn.close()


def get_freshness_report(staleness_risk=None, limit=50):
    import psycopg2.extras
    conn = _10j_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if staleness_risk:
                cur.execute("SELECT * FROM freshness_cadence WHERE staleness_risk = %s ORDER BY freshness_score ASC LIMIT %s",
                           (staleness_risk, limit))
            else:
                cur.execute("SELECT * FROM freshness_cadence ORDER BY freshness_score ASC LIMIT %s", (limit,))
            return {"pages": [dict(r) for r in cur.fetchall()]}
    finally:
        conn.close()


def get_schema_recommendations(status=None, limit=50):
    import psycopg2.extras
    conn = _10j_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if status:
                cur.execute("SELECT * FROM schema_recommendations WHERE status = %s ORDER BY confidence DESC LIMIT %s",
                           (status, limit))
            else:
                cur.execute("SELECT * FROM schema_recommendations ORDER BY confidence DESC LIMIT %s", (limit,))
            return {"recommendations": [dict(r) for r in cur.fetchall()]}
    finally:
        conn.close()


def get_competitor_report(domain=None, limit=20):
    import psycopg2.extras
    conn = _10j_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if domain:
                cur.execute("SELECT * FROM competitor_analysis WHERE competitor_domain = %s ORDER BY checked_at DESC LIMIT %s",
                           (domain, limit))
            else:
                cur.execute("SELECT * FROM competitor_analysis ORDER BY checked_at DESC LIMIT %s", (limit,))
            return {"competitors": [dict(r) for r in cur.fetchall()]}
    finally:
        conn.close()


def get_citation_events(engine=None, limit=50):
    import psycopg2.extras
    conn = _10j_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if engine:
                cur.execute("SELECT * FROM ai_citation_events WHERE ai_engine = %s ORDER BY detected_at DESC LIMIT %s",
                           (engine, limit))
            else:
                cur.execute("SELECT * FROM ai_citation_events ORDER BY detected_at DESC LIMIT %s", (limit,))
            return {"citations": [dict(r) for r in cur.fetchall()]}
    finally:
        conn.close()
