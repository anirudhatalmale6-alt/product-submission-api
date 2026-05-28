#!/usr/bin/env python3
"""10H: Safe Cluster Expansion Engine.

Draft-first, quality-gated content expansion with upstream trust controls.
No 'scale first, fix later' - quality gates are upstream, not retrospective.
"""
import psycopg2, psycopg2.extras, json, uuid, datetime, threading

_lock = threading.Lock()

DB_CFG = dict(host="127.0.0.1", port=5432, dbname="agent_manager", user="productapi", password="productapi")

def _db():
    conn = psycopg2.connect(**DB_CFG)
    conn.autocommit = True
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def create_expansion_tables():
    with _db() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS expansion_clusters (
            id SERIAL PRIMARY KEY,
            cluster_id TEXT UNIQUE NOT NULL,
            cluster_name TEXT NOT NULL,
            slug TEXT NOT NULL,
            hub_intent TEXT NOT NULL,
            hub_post_id INTEGER,
            hub_url TEXT,
            spoke_count INTEGER DEFAULT 0,
            published_spoke_count INTEGER DEFAULT 0,
            draft_spoke_count INTEGER DEFAULT 0,
            category_id INTEGER,
            importance TEXT DEFAULT 'medium' CHECK (importance IN ('critical','high','medium','low')),
            authority_score REAL DEFAULT 0.0,
            evidence_coverage REAL DEFAULT 0.0,
            trust_lint_pass_rate REAL DEFAULT 0.0,
            expansion_readiness TEXT DEFAULT 'not_ready' CHECK (expansion_readiness IN ('not_ready','partially_ready','ready','expanding','paused','complete')),
            expansion_mode TEXT DEFAULT 'draft_only' CHECK (expansion_mode IN ('draft_only','review_required','auto_publish')),
            content_type TEXT DEFAULT 'educational',
            evidence_requirements TEXT DEFAULT '[]',
            trust_requirements TEXT DEFAULT '[]',
            internal_link_targets TEXT DEFAULT '[]',
            formatting_contract TEXT DEFAULT '{}',
            image_media_state TEXT DEFAULT 'not_assessed',
            publish_gate_state TEXT DEFAULT 'closed' CHECK (publish_gate_state IN ('closed','conditional','open')),
            metadata TEXT DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS expansion_spokes (
            id SERIAL PRIMARY KEY,
            spoke_id TEXT UNIQUE NOT NULL,
            cluster_id TEXT NOT NULL REFERENCES expansion_clusters(cluster_id),
            spoke_name TEXT NOT NULL,
            slug TEXT NOT NULL,
            spoke_intent TEXT NOT NULL,
            content_type TEXT DEFAULT 'educational' CHECK (content_type IN ('educational','comparison','guide','review','hub','faq','how_to','listicle')),
            wp_post_id INTEGER,
            wp_url TEXT,
            status TEXT DEFAULT 'planned' CHECK (status IN ('planned','drafted','lint_pending','lint_pass','lint_fail','review_pending','approved','published','rejected','archived')),
            priority INTEGER DEFAULT 50,
            evidence_state TEXT DEFAULT 'not_assessed' CHECK (evidence_state IN ('not_assessed','insufficient','partial','sufficient','verified')),
            trust_lint_state TEXT DEFAULT 'not_run' CHECK (trust_lint_state IN ('not_run','running','pass','warnings','errors','blockers')),
            structure_format_state TEXT DEFAULT 'not_assessed',
            metadata_state TEXT DEFAULT 'not_assessed',
            internal_link_state TEXT DEFAULT 'not_assessed',
            disclosure_required BOOLEAN DEFAULT FALSE,
            disclosure_present BOOLEAN DEFAULT FALSE,
            approval_required BOOLEAN DEFAULT TRUE,
            approved_by TEXT,
            approved_at TIMESTAMPTZ,
            blocking_reasons TEXT DEFAULT '[]',
            gate_checklist TEXT DEFAULT '{}',
            internal_links_planned TEXT DEFAULT '[]',
            internal_links_actual TEXT DEFAULT '[]',
            word_count INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS expansion_jobs (
            id SERIAL PRIMARY KEY,
            job_id TEXT UNIQUE NOT NULL,
            cluster_id TEXT NOT NULL,
            job_type TEXT NOT NULL CHECK (job_type IN ('template_seed','spoke_plan','spoke_draft','lint_check','evidence_check','link_plan','gate_check','publish_request','bulk_audit')),
            status TEXT DEFAULT 'pending' CHECK (status IN ('pending','running','completed','failed','cancelled')),
            target_spoke_id TEXT,
            input_data TEXT DEFAULT '{}',
            output_data TEXT DEFAULT '{}',
            error_summary TEXT,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS expansion_link_plan (
            id SERIAL PRIMARY KEY,
            link_id TEXT UNIQUE NOT NULL,
            source_spoke_id TEXT,
            source_post_id INTEGER,
            source_url TEXT,
            target_spoke_id TEXT,
            target_post_id INTEGER,
            target_url TEXT,
            anchor_text TEXT,
            context_relevance TEXT DEFAULT 'high' CHECK (context_relevance IN ('high','medium','low','poor')),
            cluster_coherent BOOLEAN DEFAULT TRUE,
            link_type TEXT DEFAULT 'contextual' CHECK (link_type IN ('contextual','hub_to_spoke','spoke_to_hub','spoke_to_spoke','cross_cluster','navigational')),
            status TEXT DEFAULT 'planned' CHECK (status IN ('planned','inserted','verified','broken','removed')),
            inserted_at TIMESTAMPTZ,
            verified_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS expansion_quality_gates (
            id SERIAL PRIMARY KEY,
            gate_id TEXT UNIQUE NOT NULL,
            spoke_id TEXT NOT NULL,
            cluster_id TEXT NOT NULL,
            trust_lint_pass BOOLEAN DEFAULT FALSE,
            evidence_sufficient BOOLEAN DEFAULT FALSE,
            structure_format_pass BOOLEAN DEFAULT FALSE,
            metadata_pass BOOLEAN DEFAULT FALSE,
            internal_link_ready BOOLEAN DEFAULT FALSE,
            disclosure_satisfied BOOLEAN DEFAULT FALSE,
            approval_satisfied BOOLEAN DEFAULT FALSE,
            overall_pass BOOLEAN DEFAULT FALSE,
            gate_score REAL DEFAULT 0.0,
            blocking_items TEXT DEFAULT '[]',
            checked_at TIMESTAMPTZ DEFAULT NOW(),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_exp_spokes_cluster ON expansion_spokes(cluster_id);
        CREATE INDEX IF NOT EXISTS idx_exp_spokes_status ON expansion_spokes(status);
        CREATE INDEX IF NOT EXISTS idx_exp_jobs_cluster ON expansion_jobs(cluster_id);
        CREATE INDEX IF NOT EXISTS idx_exp_jobs_status ON expansion_jobs(status);
        CREATE INDEX IF NOT EXISTS idx_exp_links_source ON expansion_link_plan(source_spoke_id);
        CREATE INDEX IF NOT EXISTS idx_exp_links_target ON expansion_link_plan(target_spoke_id);
        CREATE INDEX IF NOT EXISTS idx_exp_gates_spoke ON expansion_quality_gates(spoke_id);
        """)


# --- Cluster Template Contract ---

def create_cluster(cluster_name, slug, hub_intent, content_type="educational",
                   importance="medium", category_id=None, hub_post_id=None, hub_url=None,
                   evidence_requirements=None, trust_requirements=None,
                   internal_link_targets=None, formatting_contract=None,
                   expansion_mode="draft_only"):
    cluster_id = f"cl-{uuid.uuid4().hex[:8]}"
    with _db() as cur:
        cur.execute("""
            INSERT INTO expansion_clusters
            (cluster_id, cluster_name, slug, hub_intent, content_type, importance,
             category_id, hub_post_id, hub_url, evidence_requirements, trust_requirements,
             internal_link_targets, formatting_contract, expansion_mode)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (cluster_id) DO NOTHING
            RETURNING *
        """, (cluster_id, cluster_name, slug, hub_intent, content_type, importance,
              category_id, hub_post_id, hub_url,
              json.dumps(evidence_requirements or []),
              json.dumps(trust_requirements or []),
              json.dumps(internal_link_targets or []),
              json.dumps(formatting_contract or {}),
              expansion_mode))
        return dict(cur.fetchone()) if cur.description else None


def get_cluster(cluster_id):
    with _db() as cur:
        cur.execute("SELECT * FROM expansion_clusters WHERE cluster_id=%s", (cluster_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_clusters(importance=None, readiness=None):
    with _db() as cur:
        q = "SELECT * FROM expansion_clusters WHERE 1=1"
        params = []
        if importance:
            q += " AND importance=%s"
            params.append(importance)
        if readiness:
            q += " AND expansion_readiness=%s"
            params.append(readiness)
        q += " ORDER BY CASE importance WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, cluster_name"
        cur.execute(q, params)
        return [dict(r) for r in cur.fetchall()]


def update_cluster(cluster_id, **kwargs):
    allowed = {'cluster_name','hub_intent','importance','authority_score','evidence_coverage',
               'trust_lint_pass_rate','expansion_readiness','expansion_mode','content_type',
               'evidence_requirements','trust_requirements','internal_link_targets',
               'formatting_contract','image_media_state','publish_gate_state','hub_post_id',
               'hub_url','category_id','spoke_count','published_spoke_count','draft_spoke_count','metadata'}
    updates, params = [], []
    for k, v in kwargs.items():
        if k in allowed:
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
            updates.append(f"{k}=%s")
            params.append(v)
    if not updates:
        return None
    updates.append("updated_at=NOW()")
    params.append(cluster_id)
    with _db() as cur:
        cur.execute(f"UPDATE expansion_clusters SET {', '.join(updates)} WHERE cluster_id=%s RETURNING *", params)
        row = cur.fetchone()
        return dict(row) if row else None


# --- Spoke Management ---

def create_spoke(cluster_id, spoke_name, slug, spoke_intent, content_type="educational",
                 priority=50, disclosure_required=False, approval_required=True,
                 wp_post_id=None, wp_url=None, status="planned"):
    spoke_id = f"sp-{uuid.uuid4().hex[:8]}"
    with _db() as cur:
        cur.execute("""
            INSERT INTO expansion_spokes
            (spoke_id, cluster_id, spoke_name, slug, spoke_intent, content_type,
             priority, disclosure_required, approval_required, wp_post_id, wp_url, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING *
        """, (spoke_id, cluster_id, spoke_name, slug, spoke_intent, content_type,
              priority, disclosure_required, approval_required, wp_post_id, wp_url, status))
        row = cur.fetchone()
        _refresh_cluster_counts(cluster_id)
        return dict(row) if row else None


def get_spoke(spoke_id):
    with _db() as cur:
        cur.execute("SELECT * FROM expansion_spokes WHERE spoke_id=%s", (spoke_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_spokes(cluster_id=None, status=None, limit=50):
    with _db() as cur:
        q = "SELECT * FROM expansion_spokes WHERE 1=1"
        params = []
        if cluster_id:
            q += " AND cluster_id=%s"
            params.append(cluster_id)
        if status:
            q += " AND status=%s"
            params.append(status)
        q += " ORDER BY priority DESC, created_at LIMIT %s"
        params.append(limit)
        cur.execute(q, params)
        return [dict(r) for r in cur.fetchall()]


def update_spoke(spoke_id, **kwargs):
    allowed = {'spoke_name','spoke_intent','content_type','status','priority',
               'evidence_state','trust_lint_state','structure_format_state',
               'metadata_state','internal_link_state','disclosure_required',
               'disclosure_present','approval_required','approved_by','approved_at',
               'blocking_reasons','gate_checklist','internal_links_planned',
               'internal_links_actual','word_count','wp_post_id','wp_url'}
    updates, params = [], []
    for k, v in kwargs.items():
        if k in allowed:
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
            updates.append(f"{k}=%s")
            params.append(v)
    if not updates:
        return None
    updates.append("updated_at=NOW()")
    params.append(spoke_id)
    with _db() as cur:
        cur.execute(f"UPDATE expansion_spokes SET {', '.join(updates)} WHERE spoke_id=%s RETURNING *", params)
        row = cur.fetchone()
        if row:
            _refresh_cluster_counts(row['cluster_id'])
        return dict(row) if row else None


def transition_spoke(spoke_id, new_status):
    VALID_TRANSITIONS = {
        'planned': ['drafted'],
        'drafted': ['lint_pending'],
        'lint_pending': ['lint_pass', 'lint_fail'],
        'lint_pass': ['review_pending', 'approved'],
        'lint_fail': ['drafted'],
        'review_pending': ['approved', 'rejected'],
        'approved': ['published'],
        'rejected': ['drafted', 'archived'],
        'published': ['archived'],
    }
    spoke = get_spoke(spoke_id)
    if not spoke:
        return {"error": "spoke not found"}
    current = spoke['status']
    if new_status not in VALID_TRANSITIONS.get(current, []):
        return {"error": f"invalid transition {current} -> {new_status}",
                "valid": VALID_TRANSITIONS.get(current, [])}
    return update_spoke(spoke_id, status=new_status)


def _refresh_cluster_counts(cluster_id):
    with _db() as cur:
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status='published') as published,
                COUNT(*) FILTER (WHERE status IN ('planned','drafted','lint_pending','lint_pass','lint_fail','review_pending','approved')) as drafts
            FROM expansion_spokes WHERE cluster_id=%s
        """, (cluster_id,))
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE expansion_clusters
                SET spoke_count=%s, published_spoke_count=%s, draft_spoke_count=%s, updated_at=NOW()
                WHERE cluster_id=%s
            """, (row['total'], row['published'], row['drafts'], cluster_id))


# --- Expansion Quality Gates ---

def run_gate_check(spoke_id):
    spoke = get_spoke(spoke_id)
    if not spoke:
        return {"error": "spoke not found"}

    cluster = get_cluster(spoke['cluster_id'])
    blocking = []

    trust_lint_pass = spoke.get('trust_lint_state') in ('pass', 'warnings')
    evidence_sufficient = spoke.get('evidence_state') in ('sufficient', 'verified')
    structure_pass = spoke.get('structure_format_state') in ('pass', 'good')
    metadata_pass = spoke.get('metadata_state') in ('pass', 'good')
    link_ready = spoke.get('internal_link_state') in ('ready', 'good', 'pass')

    disclosure_satisfied = True
    if spoke.get('disclosure_required') and not spoke.get('disclosure_present'):
        disclosure_satisfied = False
        blocking.append("disclosure_missing")

    approval_satisfied = True
    if spoke.get('approval_required') and not spoke.get('approved_by'):
        approval_satisfied = False
        blocking.append("approval_pending")

    if not trust_lint_pass:
        blocking.append("trust_lint_not_passed")
    if not evidence_sufficient:
        blocking.append("evidence_insufficient")
    if not structure_pass:
        blocking.append("structure_format_not_passed")
    if not metadata_pass:
        blocking.append("metadata_not_passed")
    if not link_ready:
        blocking.append("internal_links_not_ready")

    checks = [trust_lint_pass, evidence_sufficient, structure_pass, metadata_pass,
              link_ready, disclosure_satisfied, approval_satisfied]
    gate_score = sum(1 for c in checks if c) / len(checks) * 100
    overall_pass = all(checks)

    gate_id = f"gate-{uuid.uuid4().hex[:8]}"
    with _db() as cur:
        cur.execute("""
            INSERT INTO expansion_quality_gates
            (gate_id, spoke_id, cluster_id, trust_lint_pass, evidence_sufficient,
             structure_format_pass, metadata_pass, internal_link_ready,
             disclosure_satisfied, approval_satisfied, overall_pass, gate_score, blocking_items)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING *
        """, (gate_id, spoke_id, spoke['cluster_id'],
              trust_lint_pass, evidence_sufficient, structure_pass, metadata_pass,
              link_ready, disclosure_satisfied, approval_satisfied, overall_pass,
              gate_score, json.dumps(blocking)))
        gate = dict(cur.fetchone())

    update_spoke(spoke_id, gate_checklist=json.dumps({
        "trust_lint": trust_lint_pass, "evidence": evidence_sufficient,
        "structure": structure_pass, "metadata": metadata_pass,
        "links": link_ready, "disclosure": disclosure_satisfied,
        "approval": approval_satisfied, "score": gate_score, "pass": overall_pass
    }), blocking_reasons=blocking)

    return gate


def get_gate_history(spoke_id, limit=10):
    with _db() as cur:
        cur.execute("""
            SELECT * FROM expansion_quality_gates
            WHERE spoke_id=%s ORDER BY checked_at DESC LIMIT %s
        """, (spoke_id, limit))
        return [dict(r) for r in cur.fetchall()]


# --- Internal Link Planning ---

def plan_link(source_spoke_id, target_spoke_id, anchor_text,
              context_relevance="high", link_type="contextual", cluster_coherent=True,
              source_post_id=None, source_url=None, target_post_id=None, target_url=None):
    link_id = f"lnk-{uuid.uuid4().hex[:8]}"
    with _db() as cur:
        cur.execute("""
            INSERT INTO expansion_link_plan
            (link_id, source_spoke_id, source_post_id, source_url,
             target_spoke_id, target_post_id, target_url,
             anchor_text, context_relevance, cluster_coherent, link_type)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING *
        """, (link_id, source_spoke_id, source_post_id, source_url,
              target_spoke_id, target_post_id, target_url,
              anchor_text, context_relevance, cluster_coherent, link_type))
        return dict(cur.fetchone())


def list_links(cluster_id=None, spoke_id=None, status=None, limit=100):
    with _db() as cur:
        q = "SELECT l.* FROM expansion_link_plan l"
        joins = []
        params = []
        if cluster_id:
            q += " JOIN expansion_spokes s ON l.source_spoke_id=s.spoke_id WHERE s.cluster_id=%s"
            params.append(cluster_id)
        elif spoke_id:
            q += " WHERE (l.source_spoke_id=%s OR l.target_spoke_id=%s)"
            params.extend([spoke_id, spoke_id])
        else:
            q += " WHERE 1=1"
        if status:
            q += " AND l.status=%s"
            params.append(status)
        q += " ORDER BY l.created_at DESC LIMIT %s"
        params.append(limit)
        cur.execute(q, params)
        return [dict(r) for r in cur.fetchall()]


def update_link(link_id, **kwargs):
    allowed = {'anchor_text','context_relevance','cluster_coherent','link_type',
               'status','inserted_at','verified_at'}
    updates, params = [], []
    for k, v in kwargs.items():
        if k in allowed:
            updates.append(f"{k}=%s")
            params.append(v)
    if not updates:
        return None
    params.append(link_id)
    with _db() as cur:
        cur.execute(f"UPDATE expansion_link_plan SET {', '.join(updates)} WHERE link_id=%s RETURNING *", params)
        row = cur.fetchone()
        return dict(row) if row else None


# --- Expansion Jobs ---

def create_expansion_job(cluster_id, job_type, target_spoke_id=None, input_data=None):
    job_id = f"ej-{uuid.uuid4().hex[:8]}"
    with _db() as cur:
        cur.execute("""
            INSERT INTO expansion_jobs
            (job_id, cluster_id, job_type, target_spoke_id, input_data)
            VALUES (%s,%s,%s,%s,%s)
            RETURNING *
        """, (job_id, cluster_id, job_type, target_spoke_id, json.dumps(input_data or {})))
        return dict(cur.fetchone())


def update_expansion_job(job_id, status, output_data=None, error_summary=None):
    with _db() as cur:
        started = ", started_at=NOW()" if status == "running" else ""
        completed = ", completed_at=NOW()" if status in ("completed", "failed", "cancelled") else ""
        cur.execute(f"""
            UPDATE expansion_jobs
            SET status=%s, output_data=%s, error_summary=%s{started}{completed}
            WHERE job_id=%s RETURNING *
        """, (status, json.dumps(output_data or {}), error_summary, job_id))
        row = cur.fetchone()
        return dict(row) if row else None


def list_expansion_jobs(cluster_id=None, status=None, limit=50):
    with _db() as cur:
        q = "SELECT * FROM expansion_jobs WHERE 1=1"
        params = []
        if cluster_id:
            q += " AND cluster_id=%s"
            params.append(cluster_id)
        if status:
            q += " AND status=%s"
            params.append(status)
        q += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        cur.execute(q, params)
        return [dict(r) for r in cur.fetchall()]


# --- Expansion Readiness Assessment ---

def assess_cluster_readiness(cluster_id):
    cluster = get_cluster(cluster_id)
    if not cluster:
        return {"error": "cluster not found"}

    spokes = list_spokes(cluster_id=cluster_id)
    total = len(spokes)
    if total == 0:
        return {**cluster, "readiness": "not_ready", "reason": "no spokes defined",
                "stats": {"total": 0}}

    by_status = {}
    lint_pass = 0
    evidence_ok = 0
    gate_pass = 0
    for s in spokes:
        st = s['status']
        by_status[st] = by_status.get(st, 0) + 1
        if s.get('trust_lint_state') in ('pass', 'warnings'):
            lint_pass += 1
        if s.get('evidence_state') in ('sufficient', 'verified'):
            evidence_ok += 1
        gc = s.get('gate_checklist')
        if gc:
            try:
                gc_data = json.loads(gc) if isinstance(gc, str) else gc
                if gc_data.get('pass'):
                    gate_pass += 1
            except:
                pass

    lint_rate = lint_pass / total * 100 if total else 0
    evidence_rate = evidence_ok / total * 100 if total else 0
    gate_rate = gate_pass / total * 100 if total else 0

    published = by_status.get('published', 0)
    approved = by_status.get('approved', 0)

    if gate_rate >= 80 and lint_rate >= 90:
        readiness = "ready"
    elif lint_rate >= 50 or evidence_rate >= 50:
        readiness = "partially_ready"
    else:
        readiness = "not_ready"

    update_cluster(cluster_id, expansion_readiness=readiness,
                   trust_lint_pass_rate=lint_rate, evidence_coverage=evidence_rate)

    return {
        "cluster_id": cluster_id,
        "cluster_name": cluster.get('cluster_name'),
        "readiness": readiness,
        "expansion_mode": cluster.get('expansion_mode', 'draft_only'),
        "publish_gate_state": cluster.get('publish_gate_state', 'closed'),
        "stats": {
            "total_spokes": total,
            "by_status": by_status,
            "published": published,
            "approved": approved,
            "lint_pass_rate": round(lint_rate, 1),
            "evidence_coverage": round(evidence_rate, 1),
            "gate_pass_rate": round(gate_rate, 1),
        }
    }


def get_expansion_summary():
    clusters = list_clusters()
    total_spokes = 0
    total_published = 0
    total_draft = 0
    total_planned = 0
    readiness_counts = {}
    importance_counts = {}

    for c in clusters:
        total_spokes += c.get('spoke_count', 0)
        total_published += c.get('published_spoke_count', 0)
        total_draft += c.get('draft_spoke_count', 0)
        r = c.get('expansion_readiness', 'not_ready')
        readiness_counts[r] = readiness_counts.get(r, 0) + 1
        imp = c.get('importance', 'medium')
        importance_counts[imp] = importance_counts.get(imp, 0) + 1

    total_planned = total_spokes - total_published

    return {
        "total_clusters": len(clusters),
        "total_spokes": total_spokes,
        "total_published": total_published,
        "total_draft": total_draft,
        "total_planned": total_planned,
        "by_readiness": readiness_counts,
        "by_importance": importance_counts,
        "expansion_mode": "draft_only",
        "scaling_paused": True,
        "clusters": [{
            "cluster_id": c['cluster_id'],
            "name": c['cluster_name'],
            "importance": c['importance'],
            "readiness": c['expansion_readiness'],
            "spokes": c['spoke_count'],
            "published": c['published_spoke_count'],
            "drafts": c['draft_spoke_count'],
            "lint_pass_rate": c.get('trust_lint_pass_rate', 0),
            "evidence_coverage": c.get('evidence_coverage', 0),
            "publish_gate": c.get('publish_gate_state', 'closed'),
            "mode": c.get('expansion_mode', 'draft_only'),
        } for c in clusters]
    }


# --- Seed clusters from real site data ---

SITE_CLUSTERS = {
    "dog_food": {
        "name": "Dog Food", "slug": "dog-food", "category_id": 1467,
        "hub_intent": "Complete guide to choosing the best dog food for every breed, age, and dietary need",
        "importance": "high", "content_type": "educational",
        "evidence_requirements": ["ingredient_analysis", "nutritional_standards", "feeding_guidelines"],
        "trust_requirements": ["no_vet_claims_without_source", "no_fake_testing", "clear_affiliate_disclosure"],
        "subtopics": [
            ("Best Dry Dog Food UK", "best-dry-dog-food-uk", "Compare dry dog food options by nutritional value and ingredients", "comparison"),
            ("Dry vs Wet Dog Food", "dry-vs-wet-dog-food", "Evidence-based comparison of dry and wet feeding approaches", "educational"),
            ("Best Puppy Food UK", "best-puppy-food-uk", "Age-appropriate nutrition guide for puppies", "guide"),
            ("Best Senior Dog Food", "best-senior-dog-food", "Nutritional needs for ageing dogs", "guide"),
            ("Grain-Free Dog Food Guide", "grain-free-dog-food", "Science-based look at grain-free diets", "educational"),
            ("Raw Feeding Guide", "raw-feeding-guide", "Practical guide to raw dog food diets", "educational"),
        ]
    },
    "dog_toys": {
        "name": "Dog Toys", "slug": "dog-toys", "category_id": 1441,
        "hub_intent": "Help dog owners choose safe, engaging toys matched to their dog's size, age, and play style",
        "importance": "medium", "content_type": "educational",
        "evidence_requirements": ["material_safety", "durability_evidence", "size_guidance"],
        "trust_requirements": ["no_fake_testing", "clear_affiliate_disclosure"],
        "subtopics": [
            ("Best Indestructible Dog Toys", "best-indestructible-dog-toys", "Heavy-duty toys for power chewers", "comparison"),
            ("Best Interactive Dog Toys", "best-interactive-dog-toys", "Mental stimulation and puzzle toys", "comparison"),
            ("Best Puppy Toys", "best-puppy-toys", "Safe toys for teething and early development", "guide"),
        ]
    },
    "cat_toys": {
        "name": "Cat Toys", "slug": "cat-toys", "category_id": 1459,
        "hub_intent": "Guide cat owners to enrichment toys that match their cat's play instincts and indoor needs",
        "importance": "medium", "content_type": "educational",
        "evidence_requirements": ["material_safety", "enrichment_evidence"],
        "trust_requirements": ["no_fake_testing", "clear_affiliate_disclosure"],
        "subtopics": [
            ("Best Indoor Cat Toys", "best-indoor-cat-toys", "Enrichment for indoor-only cats", "comparison"),
            ("Best Interactive Cat Toys", "best-interactive-cat-toys", "Wand toys and automated play", "comparison"),
            ("Catnip Toys Guide", "best-catnip-toys", "Understanding catnip effects and safe toys", "educational"),
        ]
    },
    "dog_beds": {
        "name": "Dog Beds", "slug": "dog-beds", "category_id": 1401,
        "hub_intent": "Help owners choose the right bed for their dog's size, sleeping style, and health needs",
        "importance": "medium", "content_type": "educational",
        "evidence_requirements": ["material_specs", "orthopaedic_claims_sourced"],
        "trust_requirements": ["no_health_claims_without_source", "clear_affiliate_disclosure"],
        "subtopics": [
            ("Best Orthopaedic Dog Beds", "best-orthopaedic-dog-beds", "Joint support beds with evidence", "comparison"),
            ("Best Cooling Dog Beds", "best-cooling-dog-beds", "Temperature regulation beds", "comparison"),
            ("Best Puppy Beds", "best-puppy-beds", "Size-appropriate beds for growing puppies", "guide"),
        ]
    },
    "dog_harnesses": {
        "name": "Dog Harnesses", "slug": "dog-harnesses", "category_id": 1422,
        "hub_intent": "Guide owners to safe, comfortable harnesses matched to their dog's breed and walking needs",
        "importance": "medium", "content_type": "educational",
        "evidence_requirements": ["fit_guidance", "material_safety", "breed_suitability"],
        "trust_requirements": ["no_fake_testing", "clear_affiliate_disclosure"],
        "subtopics": [
            ("Best No-Pull Harnesses", "best-no-pull-harnesses", "Training harnesses for leash pullers", "comparison"),
            ("Best Dog Collars and Leads", "best-dog-collars-leads", "Complete collar and lead guide", "guide"),
            ("Best Puppy Collars", "best-puppy-collars", "First collar selection for puppies", "guide"),
        ]
    },
    "dog_health": {
        "name": "Dog Health & Wellness", "slug": "dog-health", "category_id": 1450,
        "hub_intent": "Practical health and wellness guidance for dog owners - not veterinary advice",
        "importance": "high", "content_type": "educational",
        "evidence_requirements": ["sourced_health_info", "vet_disclaimer", "no_diagnosis"],
        "trust_requirements": ["no_vet_claims_without_source", "mandatory_vet_disclaimer", "no_diagnosis_advice"],
        "subtopics": [
            ("Dog Dental Care Guide", "dog-dental-care-guide", "Teeth cleaning and dental health basics", "educational"),
            ("Dog Joint Care Guide", "dog-joint-care-guide", "Supporting joint health as dogs age", "educational"),
            ("Flea and Tick Prevention", "flea-tick-prevention-guide", "Prevention product types and usage", "guide"),
        ]
    },
    "dog_grooming": {
        "name": "Dog Grooming", "slug": "dog-grooming", "category_id": None,
        "hub_intent": "Practical grooming guides matched to coat type and breed needs",
        "importance": "medium", "content_type": "educational",
        "evidence_requirements": ["coat_type_guidance", "product_safety"],
        "trust_requirements": ["no_fake_testing", "clear_affiliate_disclosure"],
        "subtopics": [
            ("Best Dog Brushes", "best-dog-brushes", "Brush types matched to coat types", "comparison"),
            ("Best Dog Shampoo", "best-dog-shampoo", "Safe shampoo selection guide", "comparison"),
            ("Dog Nail Clipping Guide", "dog-nail-clipping-guide", "Safe nail trimming technique", "how_to"),
        ]
    },
    "dog_training": {
        "name": "Training Supplies", "slug": "training-supplies", "category_id": 1474,
        "hub_intent": "Positive-reinforcement training equipment and technique guides",
        "importance": "medium", "content_type": "educational",
        "evidence_requirements": ["training_methodology_sourced", "product_safety"],
        "trust_requirements": ["positive_reinforcement_only", "no_aversive_methods", "clear_affiliate_disclosure"],
        "subtopics": [
            ("Best Dog Training Treats", "best-dog-training-treats", "Treat selection for training sessions", "comparison"),
            ("Puppy Training Essentials", "puppy-training-essentials", "First-time puppy training equipment", "guide"),
            ("Best Dog Training Leads", "best-dog-training-leads", "Lead types for training exercises", "comparison"),
        ]
    },
    "cat_supplies": {
        "name": "Cat Supplies", "slug": "cat-supplies", "category_id": 1377,
        "hub_intent": "Complete cat care equipment guide covering all essential supply categories",
        "importance": "high", "content_type": "educational",
        "evidence_requirements": ["material_safety", "cat_behaviour_evidence"],
        "trust_requirements": ["no_fake_testing", "clear_affiliate_disclosure"],
        "subtopics": [
            ("Best Cat Beds", "best-cat-beds", "Bed types matched to cat sleeping preferences", "comparison"),
            ("Best Cat Scratching Posts", "best-cat-scratching-posts", "Scratching solutions for indoor cats", "comparison"),
            ("Best Cat Litter Guide", "best-cat-litter-guide", "Litter types compared by performance", "comparison"),
            ("Best Cat Grooming Tools", "best-cat-grooming-tools", "Grooming essentials for cats", "comparison"),
            ("Best Cat Collars", "best-cat-collars", "Safe collar options for cats", "comparison"),
        ]
    },
    "puppy_care": {
        "name": "Puppy Care", "slug": "puppy-care", "category_id": 1442,
        "hub_intent": "First-time puppy owner essentials from equipment to early training",
        "importance": "high", "content_type": "educational",
        "evidence_requirements": ["age_appropriate_guidance", "safety_standards"],
        "trust_requirements": ["no_health_claims_without_source", "clear_affiliate_disclosure"],
        "subtopics": [
            ("New Puppy Checklist", "new-puppy-checklist", "Complete first-week equipment list", "guide"),
            ("Puppy Crate Training Guide", "puppy-crate-training", "Positive crate introduction steps", "how_to"),
            ("Puppy Socialisation Guide", "puppy-socialisation-guide", "Safe early socialisation approach", "educational"),
        ]
    },
}


def seed_clusters_from_site():
    results = []
    for key, data in SITE_CLUSTERS.items():
        existing = None
        with _db() as cur:
            cur.execute("SELECT * FROM expansion_clusters WHERE slug=%s", (data['slug'],))
            existing = cur.fetchone()

        if existing:
            results.append({"cluster": data['name'], "action": "already_exists", "cluster_id": existing['cluster_id']})
            cluster_id = existing['cluster_id']
        else:
            cluster = create_cluster(
                cluster_name=data['name'], slug=data['slug'],
                hub_intent=data['hub_intent'], content_type=data['content_type'],
                importance=data['importance'], category_id=data.get('category_id'),
                evidence_requirements=data.get('evidence_requirements', []),
                trust_requirements=data.get('trust_requirements', []),
                expansion_mode="draft_only"
            )
            cluster_id = cluster['cluster_id']
            results.append({"cluster": data['name'], "action": "created", "cluster_id": cluster_id})

        for st_name, st_slug, st_intent, st_type in data.get('subtopics', []):
            with _db() as cur:
                cur.execute("SELECT * FROM expansion_spokes WHERE cluster_id=%s AND slug=%s",
                           (cluster_id, st_slug))
                if cur.fetchone():
                    continue
            create_spoke(cluster_id, st_name, st_slug, st_intent,
                        content_type=st_type, disclosure_required=True, approval_required=True)

    return results


def match_existing_posts_to_spokes():
    """Match published WordPress posts to expansion spokes by slug/title similarity."""
    import requests
    s = requests.Session()
    s.headers["Accept-Encoding"] = "gzip, deflate"
    s.auth = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")

    page = 1
    all_posts = []
    while True:
        r = s.get(f"https://pethubonline.com/wp-json/wp/v2/posts?per_page=50&page={page}&status=publish&_fields=id,title,link,slug")
        if r.status_code != 200:
            break
        posts = r.json()
        if not posts:
            break
        all_posts.extend(posts)
        page += 1

    matched = 0
    spokes = list_spokes(limit=500)
    for spoke in spokes:
        spoke_slug = spoke['slug']
        for post in all_posts:
            post_slug = post.get('slug', '')
            if spoke_slug in post_slug or post_slug in spoke_slug:
                if not spoke.get('wp_post_id'):
                    update_spoke(spoke['spoke_id'], wp_post_id=post['id'],
                               wp_url=post.get('link', ''), status='published')
                    matched += 1
                break

    return {"total_posts": len(all_posts), "total_spokes": len(spokes), "matched": matched}
