"""
10F Step 1: Create ops_* tables in PostgreSQL.
These are the canonical operational truth tables that replace
parallel JSON/Redis/in-memory stores.
"""
import psycopg2
import sys

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "database": "agent_manager",
    "user": "productapi",
    "password": "productapi",
}

TABLES = [
    ("ops_jobs", """
        CREATE TABLE IF NOT EXISTS ops_jobs (
            id              BIGSERIAL PRIMARY KEY,
            job_id          VARCHAR(50) UNIQUE NOT NULL,
            parent_job_id   VARCHAR(50),
            correlation_id  VARCHAR(50),
            agent           VARCHAR(50) NOT NULL,
            action          VARCHAR(200) NOT NULL,
            endpoint        VARCHAR(200),
            input_data      JSONB DEFAULT '{}',
            triggered_by    VARCHAR(100) NOT NULL DEFAULT 'manual',
            queue           VARCHAR(50) DEFAULT 'default',
            target_item     VARCHAR(200),
            status          VARCHAR(30) NOT NULL DEFAULT 'draft',
            risk_class      VARCHAR(10) DEFAULT 'GREEN',
            progress_pct    INT DEFAULT 0,
            output          JSONB,
            result_summary  TEXT,
            error_summary   TEXT,
            blocking_reason TEXT,
            dependency_reason TEXT,
            fallback_indicator BOOLEAN DEFAULT FALSE,
            completion_summary TEXT,
            approval_id     VARCHAR(50),
            retry_count     INT DEFAULT 0,
            max_retries     INT DEFAULT 3,
            retryable       BOOLEAN DEFAULT TRUE,
            cancellable     BOOLEAN DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            started_at      TIMESTAMPTZ,
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at    TIMESTAMPTZ,
            stale_after     TIMESTAMPTZ,
            duration_ms     INT,
            follow_up       TEXT,
            next_expected   TEXT
        )
    """, [
        "CREATE INDEX IF NOT EXISTS idx_ops_jobs_status ON ops_jobs(status)",
        "CREATE INDEX IF NOT EXISTS idx_ops_jobs_agent ON ops_jobs(agent)",
        "CREATE INDEX IF NOT EXISTS idx_ops_jobs_created ON ops_jobs(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_ops_jobs_correlation ON ops_jobs(correlation_id)",
        "CREATE INDEX IF NOT EXISTS idx_ops_jobs_parent ON ops_jobs(parent_job_id)",
        "CREATE INDEX IF NOT EXISTS idx_ops_jobs_approval ON ops_jobs(approval_id)",
    ]),

    ("ops_approvals", """
        CREATE TABLE IF NOT EXISTS ops_approvals (
            id                  BIGSERIAL PRIMARY KEY,
            approval_id         VARCHAR(50) UNIQUE NOT NULL,
            correlation_id      VARCHAR(50),
            action_type         VARCHAR(100) NOT NULL,
            affected_item       VARCHAR(200) NOT NULL,
            proposed_change     TEXT NOT NULL,
            before_summary      TEXT,
            after_summary       TEXT,
            change_category     VARCHAR(50),
            proposing_agent     VARCHAR(50) NOT NULL,
            decided_by          VARCHAR(100),
            reason              TEXT NOT NULL,
            evidence_level      VARCHAR(30) DEFAULT 'none',
            data_source_type    VARCHAR(30) DEFAULT 'live',
            risk_level          VARCHAR(10) NOT NULL,
            traffic_light       VARCHAR(10) NOT NULL,
            status              VARCHAR(30) NOT NULL DEFAULT 'pending',
            decision_reason     TEXT,
            impact_if_approved  TEXT,
            impact_if_rejected  TEXT,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            decided_at          TIMESTAMPTZ,
            expires_at          TIMESTAMPTZ,
            auto_approved       BOOLEAN DEFAULT FALSE,
            job_id              VARCHAR(50)
        )
    """, [
        "CREATE INDEX IF NOT EXISTS idx_ops_approvals_status ON ops_approvals(status)",
        "CREATE INDEX IF NOT EXISTS idx_ops_approvals_risk ON ops_approvals(risk_level)",
        "CREATE INDEX IF NOT EXISTS idx_ops_approvals_created ON ops_approvals(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_ops_approvals_job ON ops_approvals(job_id)",
    ]),

    ("ops_events", """
        CREATE TABLE IF NOT EXISTS ops_events (
            id              BIGSERIAL PRIMARY KEY,
            event_id        VARCHAR(50) UNIQUE NOT NULL,
            event_type      VARCHAR(100) NOT NULL,
            category        VARCHAR(50) NOT NULL DEFAULT 'system',
            severity        VARCHAR(20) NOT NULL DEFAULT 'info',
            source_agent    VARCHAR(50),
            source_module   VARCHAR(100),
            actor           VARCHAR(100),
            target_entity   VARCHAR(200),
            target_type     VARCHAR(50),
            correlation_id  VARCHAR(50),
            causation_id    VARCHAR(50),
            job_id          VARCHAR(50),
            summary         TEXT NOT NULL,
            detail          JSONB DEFAULT '{}',
            risk_level      VARCHAR(10) DEFAULT 'GREEN',
            status          VARCHAR(20) DEFAULT 'active',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            acknowledged_at TIMESTAMPTZ,
            resolved_at     TIMESTAMPTZ
        )
    """, [
        "CREATE INDEX IF NOT EXISTS idx_ops_events_type ON ops_events(event_type)",
        "CREATE INDEX IF NOT EXISTS idx_ops_events_category ON ops_events(category)",
        "CREATE INDEX IF NOT EXISTS idx_ops_events_created ON ops_events(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_ops_events_severity ON ops_events(severity)",
        "CREATE INDEX IF NOT EXISTS idx_ops_events_correlation ON ops_events(correlation_id)",
        "CREATE INDEX IF NOT EXISTS idx_ops_events_job ON ops_events(job_id)",
    ]),

    ("ops_action_receipts", """
        CREATE TABLE IF NOT EXISTS ops_action_receipts (
            id              BIGSERIAL PRIMARY KEY,
            receipt_id      VARCHAR(50) UNIQUE NOT NULL,
            action_name     VARCHAR(200) NOT NULL,
            source_screen   VARCHAR(100),
            source_module   VARCHAR(100),
            actor           VARCHAR(100) NOT NULL DEFAULT 'operator',
            target_entity   VARCHAR(200),
            job_id          VARCHAR(50),
            correlation_id  VARCHAR(50),
            status          VARCHAR(30) NOT NULL,
            accepted        BOOLEAN,
            requested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_update     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            next_expected   TEXT,
            detail          JSONB DEFAULT '{}'
        )
    """, [
        "CREATE INDEX IF NOT EXISTS idx_ops_receipts_created ON ops_action_receipts(requested_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_ops_receipts_job ON ops_action_receipts(job_id)",
        "CREATE INDEX IF NOT EXISTS idx_ops_receipts_actor ON ops_action_receipts(actor)",
    ]),

    ("ops_pipeline_runs", """
        CREATE TABLE IF NOT EXISTS ops_pipeline_runs (
            id              BIGSERIAL PRIMARY KEY,
            run_id          VARCHAR(50) UNIQUE NOT NULL,
            mode            VARCHAR(20) NOT NULL,
            category        VARCHAR(100),
            started_by      VARCHAR(100) NOT NULL DEFAULT 'manual',
            correlation_id  VARCHAR(50),
            article_topic   VARCHAR(500),
            article_title   VARCHAR(500),
            article_post_id INT,
            status          VARCHAR(30) NOT NULL DEFAULT 'running',
            current_step    INT DEFAULT 1,
            total_steps     INT DEFAULT 6,
            started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at    TIMESTAMPTZ,
            duration_ms     INT,
            result_summary  TEXT,
            next_action     TEXT,
            error_summary   TEXT
        )
    """, [
        "CREATE INDEX IF NOT EXISTS idx_ops_pipeline_status ON ops_pipeline_runs(status)",
        "CREATE INDEX IF NOT EXISTS idx_ops_pipeline_started ON ops_pipeline_runs(started_at DESC)",
    ]),

    ("ops_pipeline_steps", """
        CREATE TABLE IF NOT EXISTS ops_pipeline_steps (
            id              BIGSERIAL PRIMARY KEY,
            run_id          VARCHAR(50) NOT NULL,
            step_number     INT NOT NULL,
            agent           VARCHAR(50) NOT NULL,
            action          VARCHAR(200) NOT NULL,
            status          VARCHAR(30) NOT NULL DEFAULT 'queued',
            skipped_reason  TEXT,
            skipped_by      VARCHAR(100),
            result          JSONB DEFAULT '{}',
            error_summary   TEXT,
            fallback_used   BOOLEAN DEFAULT FALSE,
            fallback_detail TEXT,
            started_at      TIMESTAMPTZ,
            completed_at    TIMESTAMPTZ,
            duration_ms     INT,
            waiting_for     VARCHAR(200),
            blocked_reason  TEXT
        )
    """, [
        "CREATE INDEX IF NOT EXISTS idx_ops_steps_run ON ops_pipeline_steps(run_id)",
        "CREATE INDEX IF NOT EXISTS idx_ops_steps_status ON ops_pipeline_steps(status)",
    ]),

    ("ops_agent_status", """
        CREATE TABLE IF NOT EXISTS ops_agent_status (
            id              BIGSERIAL PRIMARY KEY,
            agent_name      VARCHAR(50) UNIQUE NOT NULL,
            port            INT NOT NULL,
            status          VARCHAR(30) NOT NULL DEFAULT 'unknown',
            previous_status VARCHAR(30),
            current_mode    VARCHAR(50) DEFAULT 'unknown',
            last_heartbeat  TIMESTAMPTZ,
            last_successful_run TIMESTAMPTZ,
            last_failed_run TIMESTAMPTZ,
            last_http_check TIMESTAMPTZ,
            http_healthy    BOOLEAN,
            current_queue_depth INT DEFAULT 0,
            current_task_summary TEXT,
            last_error_summary TEXT,
            total_tasks_completed INT DEFAULT 0,
            total_tasks_failed INT DEFAULT 0,
            error_count     INT DEFAULT 0,
            uptime_pct      NUMERIC(5,2),
            health_score    INT DEFAULT 0,
            health_factors  JSONB DEFAULT '{}',
            status_changed_at TIMESTAMPTZ,
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """, [
        "CREATE INDEX IF NOT EXISTS idx_ops_agent_status ON ops_agent_status(status)",
        "CREATE INDEX IF NOT EXISTS idx_ops_agent_name ON ops_agent_status(agent_name)",
    ]),

    ("ops_agent_transitions", """
        CREATE TABLE IF NOT EXISTS ops_agent_transitions (
            id              BIGSERIAL PRIMARY KEY,
            agent_name      VARCHAR(50) NOT NULL,
            from_status     VARCHAR(30) NOT NULL,
            to_status       VARCHAR(30) NOT NULL,
            reason          TEXT,
            trigger_source  VARCHAR(100),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """, [
        "CREATE INDEX IF NOT EXISTS idx_ops_transitions_agent ON ops_agent_transitions(agent_name)",
        "CREATE INDEX IF NOT EXISTS idx_ops_transitions_created ON ops_agent_transitions(created_at DESC)",
    ]),

    ("ops_alerts", """
        CREATE TABLE IF NOT EXISTS ops_alerts (
            id              BIGSERIAL PRIMARY KEY,
            alert_id        VARCHAR(50) UNIQUE NOT NULL,
            alert_type      VARCHAR(100) NOT NULL,
            severity        VARCHAR(20) NOT NULL,
            affected_component VARCHAR(100) NOT NULL,
            summary         TEXT NOT NULL,
            detail          JSONB DEFAULT '{}',
            status          VARCHAR(30) NOT NULL DEFAULT 'active',
            user_action_required BOOLEAN DEFAULT FALSE,
            auto_retry_in_progress BOOLEAN DEFAULT FALSE,
            resolved_but_pending_clear BOOLEAN DEFAULT FALSE,
            resolution_summary TEXT,
            resolved_by     VARCHAR(100),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            resolved_at     TIMESTAMPTZ,
            suppressed_at   TIMESTAMPTZ,
            stale_after     TIMESTAMPTZ
        )
    """, [
        "CREATE INDEX IF NOT EXISTS idx_ops_alerts_status ON ops_alerts(status)",
        "CREATE INDEX IF NOT EXISTS idx_ops_alerts_severity ON ops_alerts(severity)",
        "CREATE INDEX IF NOT EXISTS idx_ops_alerts_created ON ops_alerts(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_ops_alerts_component ON ops_alerts(affected_component)",
    ]),

    ("ops_workflow_items", """
        CREATE TABLE IF NOT EXISTS ops_workflow_items (
            id              BIGSERIAL PRIMARY KEY,
            item_id         VARCHAR(50) UNIQUE NOT NULL,
            wp_post_id      INT,
            title           VARCHAR(500),
            item_type       VARCHAR(50) NOT NULL,
            category        VARCHAR(100),
            stage_research  VARCHAR(30) DEFAULT 'pending',
            stage_content   VARCHAR(30) DEFAULT 'pending',
            stage_seo       VARCHAR(30) DEFAULT 'pending',
            stage_affiliate VARCHAR(30) DEFAULT 'pending',
            stage_social    VARCHAR(30) DEFAULT 'pending',
            stage_engagement VARCHAR(30) DEFAULT 'pending',
            overall_status  VARCHAR(30) DEFAULT 'draft',
            current_stage   VARCHAR(30),
            blocked_at_stage VARCHAR(30),
            blocked_reason  TEXT,
            pipeline_run_id VARCHAR(50),
            last_job_id     VARCHAR(50),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            published_at    TIMESTAMPTZ,
            quality_score   INT,
            trust_score     INT,
            readiness_pct   INT DEFAULT 0
        )
    """, [
        "CREATE INDEX IF NOT EXISTS idx_ops_workflow_status ON ops_workflow_items(overall_status)",
        "CREATE INDEX IF NOT EXISTS idx_ops_workflow_wp ON ops_workflow_items(wp_post_id)",
        "CREATE INDEX IF NOT EXISTS idx_ops_workflow_stage ON ops_workflow_items(current_stage)",
    ]),

    ("ops_comparison_log", """
        CREATE TABLE IF NOT EXISTS ops_comparison_log (
            id              BIGSERIAL PRIMARY KEY,
            check_type      VARCHAR(50) NOT NULL,
            entity_id       VARCHAR(50) NOT NULL,
            old_store       VARCHAR(50) NOT NULL,
            new_store       VARCHAR(50) NOT NULL DEFAULT 'ops_jobs',
            field_name      VARCHAR(100),
            old_value       TEXT,
            new_value       TEXT,
            match           BOOLEAN NOT NULL,
            discrepancy_type VARCHAR(50),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """, [
        "CREATE INDEX IF NOT EXISTS idx_ops_comparison_created ON ops_comparison_log(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_ops_comparison_match ON ops_comparison_log(match)",
    ]),
]

AGENTS_SEED = [
    ("manager", 8100),
    ("seo", 8101),
    ("analytics", 8102),
    ("social", 8103),
    ("maintenance", 8104),
    ("content", 8105),
    ("product_research", 8106),
    ("affiliate", 8107),
    ("engagement", 8108),
]


def main():
    print("10F Step 1: Creating ops_* tables in PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    created = []
    for table_name, create_sql, indexes in TABLES:
        try:
            cur.execute(create_sql)
            for idx_sql in indexes:
                cur.execute(idx_sql)
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cur.fetchone()[0]
            created.append(table_name)
            print(f"  OK: {table_name} (rows: {count})")
        except Exception as e:
            print(f"  FAIL: {table_name} — {e}")
            conn.rollback()

    # Seed agent status records
    print("\nSeeding ops_agent_status with 9 agents...")
    for agent_name, port in AGENTS_SEED:
        try:
            cur.execute("""
                INSERT INTO ops_agent_status (agent_name, port, status, updated_at)
                VALUES (%s, %s, 'unknown', NOW())
                ON CONFLICT (agent_name) DO NOTHING
            """, (agent_name, port))
            print(f"  OK: {agent_name} (port {port})")
        except Exception as e:
            print(f"  FAIL: {agent_name} — {e}")

    # Verify all tables
    print(f"\nVerification: {len(created)}/{len(TABLES)} tables created")
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema='public' AND table_name LIKE 'ops_%'
        ORDER BY table_name
    """)
    rows = cur.fetchall()
    print(f"ops_* tables in database: {len(rows)}")
    for r in rows:
        print(f"  {r[0]}")

    cur.close()
    conn.close()
    print("\nStep 1 complete.")


if __name__ == "__main__":
    main()
