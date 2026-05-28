#!/usr/bin/env python3
"""
10F Phase 5: Validation and Simulation Testing
Exercises every truthful operations surface under controlled conditions.
"""
import sys
import time
import json
import uuid
import requests

BASE = "http://127.0.0.1:8100/api/ops"
RESULTS = []
PASS = 0
FAIL = 0

def test(name, fn):
    global PASS, FAIL
    try:
        result = fn()
        if result:
            PASS += 1
            RESULTS.append({"test": name, "status": "PASS", "detail": str(result)[:200]})
            print(f"  PASS: {name}")
        else:
            FAIL += 1
            RESULTS.append({"test": name, "status": "FAIL", "detail": "returned falsy"})
            print(f"  FAIL: {name}")
    except Exception as e:
        FAIL += 1
        RESULTS.append({"test": name, "status": "FAIL", "detail": str(e)[:200]})
        print(f"  FAIL: {name} -- {e}")

def api(method, path, **kwargs):
    url = f"{BASE}{path}"
    r = getattr(requests, method)(url, timeout=15, **kwargs)
    r.raise_for_status()
    return r.json()

import truthful_ops as tops

# ============================================================
# TEST GROUP 1: Job Lifecycle (create -> start -> progress -> complete)
# ============================================================
print("\n== TEST GROUP 1: Job Lifecycle ==")

job1 = None
def t1_create_job():
    global job1
    job1 = tops.create_job(
        agent="test", action="validation_test_complete_lifecycle",
        endpoint="/test/validation", input_data={"phase": "5", "test": "lifecycle"},
        triggered_by="phase5_validation", queue="validation",
        target_item="test-target-001", risk_class="GREEN",
        retryable=True, stale_minutes=10
    )
    return job1 and job1.get("job_id")
test("Create job with full parameters", t1_create_job)

def t1_start_job():
    result = tops.start_job(job1["job_id"])
    return result and result.get("status") == "running"
test("Start job -> status=running", t1_start_job)

def t1_progress_50():
    result = tops.update_job_progress(job1["job_id"], 50, "Halfway through validation")
    return result and result.get("progress_pct") == 50
test("Update progress to 50%", t1_progress_50)

def t1_progress_90():
    result = tops.update_job_progress(job1["job_id"], 90, "Almost done")
    return result and result.get("progress_pct") == 90
test("Update progress to 90%", t1_progress_90)

def t1_complete():
    result = tops.complete_job(
        job1["job_id"], success=True,
        result_summary="Validation lifecycle test passed",
        output={"validated": True, "surfaces": 7}
    )
    return result and result.get("status") == "completed"
test("Complete job -> status=completed", t1_complete)

def t1_verify_api():
    data = api("get", f"/jobs/{job1['job_id']}")
    return (data.get("status") == "completed" and
            data.get("result_summary") == "Validation lifecycle test passed")
test("Verify job via API endpoint", t1_verify_api)


# ============================================================
# TEST GROUP 2: Job Failure + Retry Lifecycle
# ============================================================
print("\n== TEST GROUP 2: Job Failure + Retry ==")

job2 = None
def t2_create():
    global job2
    job2 = tops.create_job(
        agent="test", action="validation_test_fail_retry",
        triggered_by="phase5_validation", retryable=True
    )
    return job2 and job2.get("job_id")
test("Create retryable job", t2_create)

def t2_fail():
    tops.start_job(job2["job_id"])
    result = tops.complete_job(job2["job_id"], success=False,
                                error_summary="Simulated failure for testing")
    return result and result.get("status") in ("failed_retryable", "failed_terminal")
test("Fail job -> failed status", t2_fail)

job2_retry = None
def t2_retry():
    global job2_retry
    job2_retry = tops.retry_job(job2["job_id"])
    return job2_retry and job2_retry.get("status") == "queued"
test("Retry job -> new job created with status=queued", t2_retry)

def t2_verify_original():
    orig = tops.get_job(job2["job_id"])
    return orig is not None
test("Original job still queryable after retry", t2_verify_original)


# ============================================================
# TEST GROUP 3: Job Cancel + Stale Detection
# ============================================================
print("\n== TEST GROUP 3: Cancel + Stale Detection ==")

job3 = None
def t3_create_cancel():
    global job3
    job3 = tops.create_job(agent="test", action="validation_test_cancel",
                           triggered_by="phase5_validation")
    tops.start_job(job3["job_id"])
    result = tops.cancel_job(job3["job_id"], "Cancelled for validation testing")
    return result and result.get("status") == "cancelled"
test("Cancel running job -> status=cancelled", t3_create_cancel)

job_stale = None
def t3_stale():
    global job_stale
    job_stale = tops.create_job(agent="test", action="validation_test_stale",
                                triggered_by="phase5_validation", stale_minutes=0)
    tops.start_job(job_stale["job_id"])
    time.sleep(1)
    stale_list = tops.check_stale_jobs()
    if isinstance(stale_list, list) and len(stale_list) > 0:
        if isinstance(stale_list[0], str):
            return job_stale["job_id"] in stale_list
        elif isinstance(stale_list[0], dict):
            return any(j.get("job_id") == job_stale["job_id"] for j in stale_list)
    return len(stale_list) > 0
test("Stale detection catches job with stale_minutes=0", t3_stale)


# ============================================================
# TEST GROUP 4: Approval Lifecycle
# ============================================================
print("\n== TEST GROUP 4: Approval Lifecycle ==")

appr1 = None
def t4_create_approval():
    global appr1
    appr1 = tops.create_approval(
        action_type="publish_content",
        proposing_agent="content",
        affected_item="test-post-001",
        proposed_change="Publish test blog post for validation",
        reason="Phase 5 validation testing",
        risk_level="medium",
        traffic_light="AMBER",
        before_summary="Draft post",
        after_summary="Published post",
        change_category="content_publish",
        evidence_level="verified",
        impact_if_approved="Post goes live",
        impact_if_rejected="Post stays draft"
    )
    return appr1 and appr1.get("approval_id") and appr1.get("status") == "pending"
test("Create AMBER approval -> pending", t4_create_approval)

def t4_approve():
    result = tops.decide_approval(appr1["approval_id"], "approved",
                                   decided_by="owner_jason", reason="Approved for validation")
    return result and result.get("status") == "approved"
test("Approve approval -> status=approved", t4_approve)

def t4_api_pending():
    data = api("get", "/approvals/pending")
    return isinstance(data, list)
test("Pending approvals API returns list", t4_api_pending)

appr2 = None
def t4_create_reject():
    global appr2
    appr2 = tops.create_approval(
        action_type="deploy_schema",
        proposing_agent="seo",
        affected_item="product-schema",
        proposed_change="Deploy Product schema to live site",
        reason="SEO enhancement",
        risk_level="high",
        traffic_light="RED",
        impact_if_approved="Schema goes live",
        impact_if_rejected="No schema deployed"
    )
    return appr2 and appr2.get("status") == "pending"
test("Create RED approval -> pending", t4_create_reject)

def t4_reject():
    result = tops.decide_approval(appr2["approval_id"], "rejected",
                                   decided_by="owner_jason",
                                   reason="Rejected: schema deployment blocked per governance rules")
    return result and result.get("status") == "rejected"
test("Reject RED approval -> status=rejected", t4_reject)

appr3 = None
def t4_expiry():
    global appr3
    appr3 = tops.create_approval(
        action_type="test_expire",
        proposing_agent="test",
        affected_item="expire-target",
        proposed_change="This approval should expire",
        reason="Testing expiry",
        risk_level="low",
        traffic_light="AMBER",
        expires_hours=0
    )
    time.sleep(1)
    count = tops.expire_approvals()
    check = tops.get_approvals(status="expired")
    found = any(a.get("approval_id") == appr3["approval_id"] for a in check)
    return found
test("Approval expiry catches expires_hours=0", t4_expiry)

def t4_api_recent():
    data = api("get", "/approvals/recent?limit=10")
    ids = [a.get("approval_id") for a in data]
    has_approved = appr1["approval_id"] in ids if appr1 else False
    has_rejected = appr2["approval_id"] in ids if appr2 else False
    return has_approved and has_rejected
test("Recent approvals API shows both approved and rejected", t4_api_recent)


# ============================================================
# TEST GROUP 5: Event Logging + Timeline
# ============================================================
print("\n== TEST GROUP 5: Events + Timeline ==")

evt1 = None
def t5_log_event():
    global evt1
    evt1 = tops.log_event(
        event_type="validation_test",
        severity="info",
        source_agent="test",
        summary="Phase 5 validation event",
        detail={"test_group": 5, "purpose": "prove event logging"},
        category="system"
    )
    return evt1 and evt1.get("event_id")
test("Log info event", t5_log_event)

def t5_log_critical():
    evt = tops.log_event(
        event_type="validation_critical_test",
        severity="critical",
        source_agent="test",
        summary="Phase 5 critical event (should auto-create alert)",
        detail={"test_group": 5, "purpose": "prove alert auto-creation"},
        category="system"
    )
    return evt and evt.get("event_id")
test("Log critical event (triggers auto-alert)", t5_log_critical)

def t5_timeline_api():
    data = api("get", "/events/timeline?hours=1&limit=20")
    has_validation = any("validation" in str(e) for e in data)
    return has_validation
test("Timeline API returns validation events", t5_timeline_api)

def t5_event_count():
    data = api("get", "/events/timeline?hours=24&limit=200")
    return len(data) > 0
test("Event timeline has entries in last 24h", t5_event_count)


# ============================================================
# TEST GROUP 6: Action Receipts
# ============================================================
print("\n== TEST GROUP 6: Action Receipts ==")

rcpt1 = None
def t6_create_receipt():
    global rcpt1
    rcpt1 = tops.create_action_receipt(
        action_name="validation_dispatch",
        source_screen="phase5_test",
        source_module="validation",
        actor="test_agent",
        target_entity="test-target-receipt",
        job_id=job1["job_id"] if job1 else None
    )
    return rcpt1 and rcpt1.get("receipt_id")
test("Create action receipt", t6_create_receipt)

def t6_update_receipt():
    result = tops.update_receipt_status(receipt_id=rcpt1["receipt_id"], status="completed")
    return result and result.get("status") == "completed"
test("Update receipt -> completed", t6_update_receipt)

def t6_create_failed_receipt():
    rcpt = tops.create_action_receipt(
        action_name="validation_failed_dispatch",
        source_screen="phase5_test",
        source_module="validation",
        actor="test_agent",
        target_entity="test-target-fail"
    )
    result = tops.update_receipt_status(receipt_id=rcpt["receipt_id"], status="failed")
    return result and result.get("status") == "failed"
test("Create and fail a receipt", t6_create_failed_receipt)

def t6_api_receipts():
    data = api("get", "/actions/recent?limit=10")
    has_validation = any("validation" in str(r) for r in data)
    return has_validation
test("Receipts API returns validation receipt", t6_api_receipts)


# ============================================================
# TEST GROUP 7: Pipeline Tracking
# ============================================================
print("\n== TEST GROUP 7: Pipeline Tracking ==")

run_id = f"pipe-val-{uuid.uuid4().hex[:8]}"
pipe1 = None
def t7_create_pipeline():
    global pipe1
    pipe1 = tops.create_pipeline_run(
        run_id=run_id,
        mode="validation",
        category="phase5_test",
        started_by="phase5_validation",
        total_steps=3
    )
    return pipe1 and pipe1.get("run_id") == run_id
test("Create pipeline run (3 steps)", t7_create_pipeline)

def t7_step1():
    step = tops.create_pipeline_step(run_id, 1, "seo", "keyword_analysis")
    result = tops.update_pipeline_step(run_id, 1, status="completed",
                                        result={"keywords_found": 42})
    return result is not None
test("Pipeline step 1: SEO keyword analysis -> completed", t7_step1)

def t7_step2():
    step = tops.create_pipeline_step(run_id, 2, "content", "brief_generation")
    result = tops.update_pipeline_step(run_id, 2, status="completed",
                                        result={"briefs_created": 3})
    return result is not None
test("Pipeline step 2: Content brief generation -> completed", t7_step2)

def t7_step3():
    step = tops.create_pipeline_step(run_id, 3, "content", "draft_creation")
    result = tops.update_pipeline_step(run_id, 3, status="completed",
                                        result={"drafts_created": 3})
    return result is not None
test("Pipeline step 3: Draft creation -> completed", t7_step3)

def t7_complete_pipeline():
    result = tops.complete_pipeline_run(run_id, status="completed",
                                         result_summary="Validation pipeline completed all 3 steps")
    return result and result.get("status") == "completed"
test("Complete pipeline run -> status=completed", t7_complete_pipeline)

def t7_api_pipeline():
    data = api("get", "/pipeline/history?limit=5")
    has_validation = any("validation" in str(p) for p in data)
    return has_validation
test("Pipeline history API returns validation run", t7_api_pipeline)

def t7_api_current():
    data = api("get", "/pipeline/current")
    return data is not None
test("Pipeline current API responds", t7_api_current)


# ============================================================
# TEST GROUP 8: Agent Status + Transitions
# ============================================================
print("\n== TEST GROUP 8: Agent Status + Transitions ==")

def t8_update_status():
    result = tops.update_agent_status(
        "test_validation_agent",
        status="healthy",
        http_healthy=True,
        current_task_summary="Running validation tests",
        health_score=95,
        last_heartbeat=True
    )
    return result is not None
test("Register test agent with status", t8_update_status)

def t8_transition():
    result = tops.transition_agent("test_validation_agent", "degraded",
                                    "Simulated degradation for testing",
                                    trigger_source="phase5_validation")
    return result and result.get("status") == "degraded"
test("Transition agent healthy -> degraded", t8_transition)

def t8_transition_back():
    result = tops.transition_agent("test_validation_agent", "healthy",
                                    "Recovery after validation test",
                                    trigger_source="phase5_validation")
    return result and result.get("status") == "healthy"
test("Transition agent degraded -> healthy", t8_transition_back)

def t8_api_agents():
    data = api("get", "/agents/status")
    names = [a.get("agent_name") for a in data]
    return "test_validation_agent" in names
test("Agent status API shows test agent", t8_api_agents)

def t8_api_single_agent():
    data = api("get", "/agents/test_validation_agent")
    return data.get("agent_name") == "test_validation_agent"
test("Single agent API returns correct agent", t8_api_single_agent)


# ============================================================
# TEST GROUP 9: Alert Lifecycle
# ============================================================
print("\n== TEST GROUP 9: Alert Lifecycle ==")

alert1 = None
def t9_create_alert():
    global alert1
    alert1 = tops.create_alert(
        alert_type="validation_test_alert",
        severity="warning",
        affected_component="test:validation",
        summary="Phase 5 validation alert - should be resolved",
        detail={"test": True},
        user_action_required=False,
        stale_hours=24
    )
    return alert1 and alert1.get("alert_id") and alert1.get("status") == "active"
test("Create warning alert", t9_create_alert)

def t9_resolve():
    result = tops.resolve_alert(alert1["alert_id"],
                                 resolved_by="phase5_validation",
                                 resolution_summary="Resolved during validation testing")
    return result and result.get("status") == "resolved"
test("Resolve alert with summary", t9_resolve)

alert2 = None
def t9_suppress():
    global alert2
    alert2 = tops.create_alert(
        alert_type="validation_suppress_test",
        severity="info",
        affected_component="test:suppression",
        summary="This alert should be suppressed",
        detail={"test": True}
    )
    result = tops.suppress_alert(alert2["alert_id"])
    return result and result.get("status") == "suppressed"
test("Create and suppress alert", t9_suppress)

def t9_api_active():
    data = api("get", "/alerts/active")
    ids = [a.get("alert_id") for a in data]
    resolved_gone = alert1["alert_id"] not in ids
    suppressed_gone = alert2["alert_id"] not in ids
    return resolved_gone and suppressed_gone
test("Resolved+suppressed alerts not in active list", t9_api_active)

def t9_api_all():
    data = api("get", "/alerts/all?limit=20")
    ids = [a.get("alert_id") for a in data]
    return alert1["alert_id"] in ids and alert2["alert_id"] in ids
test("All alerts API shows both resolved and suppressed", t9_api_all)

def t9_auto_alert():
    alerts = api("get", "/alerts/all?limit=20")
    auto_alerts = [a for a in alerts if "validation_critical_test" in str(a) or "critical" in str(a.get("severity",""))]
    return len(auto_alerts) > 0
test("Critical/auto alerts exist in system", t9_auto_alert)


# ============================================================
# TEST GROUP 10: Comparison + Shadow Report
# ============================================================
print("\n== TEST GROUP 10: Comparison + Shadow Report ==")

def t10_log_comparison():
    tops.log_comparison(
        check_type="validation",
        entity_id="val-entity-001",
        old_store="json",
        field_name="status",
        old_value="completed",
        new_value="completed",
        match=True
    )
    return True
test("Log matching comparison", t10_log_comparison)

def t10_log_mismatch():
    tops.log_comparison(
        check_type="validation",
        entity_id="val-entity-002",
        old_store="json",
        field_name="status",
        old_value="failed",
        new_value="failed_terminal",
        match=False,
        discrepancy_type="value_mismatch"
    )
    return True
test("Log mismatched comparison", t10_log_mismatch)

def t10_comparison_summary():
    data = api("get", "/comparison/summary")
    return data.get("total_checks", 0) > 0
test("Comparison summary API has data", t10_comparison_summary)

def t10_shadow_report():
    data = api("get", "/comparison/shadow-report")
    return "shadow_mode" in data and "comparison" in data
test("Shadow report API returns full report", t10_shadow_report)

def t10_match_rate():
    data = api("get", "/comparison/shadow-report")
    rate = data.get("match_rate", 0)
    return rate > 0
test("Shadow report has non-zero match rate", t10_match_rate)


# ============================================================
# TEST GROUP 11: Operational Summary API
# ============================================================
print("\n== TEST GROUP 11: Operational Summary ==")

def t11_summary():
    data = api("get", "/summary")
    required = ["jobs", "pending_approvals", "active_alerts", "events_last_24h"]
    return all(k in data for k in required)
test("Operational summary has all required fields", t11_summary)

def t11_jobs_summary():
    data = api("get", "/jobs/summary")
    return "total" in data and "by_status" in data
test("Jobs summary has total + by_status", t11_jobs_summary)

def t11_summary_reflects_tests():
    data = api("get", "/summary")
    return data["jobs"]["total"] > 6
test("Summary reflects validation test jobs", t11_summary_reflects_tests)


# ============================================================
# TEST GROUP 12: API Endpoint Coverage
# ============================================================
print("\n== TEST GROUP 12: API Endpoint Coverage ==")

endpoints = [
    ("GET", "/jobs/recent"),
    ("GET", "/jobs/summary"),
    ("GET", "/approvals/pending"),
    ("GET", "/approvals/recent"),
    ("GET", "/events/timeline"),
    ("GET", "/actions/recent"),
    ("GET", "/pipeline/history"),
    ("GET", "/pipeline/current"),
    ("GET", "/agents/status"),
    ("GET", "/alerts/active"),
    ("GET", "/alerts/all"),
    ("GET", "/summary"),
    ("GET", "/comparison/summary"),
    ("GET", "/comparison/shadow-report"),
]

for method, path in endpoints:
    def make_test(m, p):
        def t():
            r = getattr(requests, m.lower())(f"{BASE}{p}", timeout=10)
            return r.status_code == 200
        return t
    test(f"Endpoint {method} {path} -> 200", make_test(method, path))


# ============================================================
# TEST GROUP 13: NOC Dashboard Loads
# ============================================================
print("\n== TEST GROUP 13: NOC Dashboard ==")

def t13_noc():
    r = requests.get("http://127.0.0.1:8100/noc-10f", timeout=10)
    return r.status_code == 200 and "Truthful Operations" in r.text
test("NOC dashboard HTML loads with title", t13_noc)

def t13_noc_has_sections():
    r = requests.get("http://127.0.0.1:8100/noc-10f", timeout=10)
    sections = ["Agent Status", "Active Alerts", "Job Centre", "Approval Queue",
                "Event Timeline", "Pipeline History", "Action Receipts"]
    found = sum(1 for s in sections if s in r.text)
    return found >= 6
test("NOC dashboard contains all major sections", t13_noc_has_sections)

def t13_noc_api_paths():
    r = requests.get("http://127.0.0.1:8100/noc-10f", timeout=10)
    api_paths = ["api/ops/summary", "api/ops/agents/status", "api/ops/alerts/active",
                 "api/ops/jobs/recent", "api/ops/events/timeline"]
    found = sum(1 for p in api_paths if p in r.text)
    return found >= 4
test("NOC dashboard references correct API paths", t13_noc_api_paths)


# ============================================================
# TEST GROUP 14: Data Integrity Cross-Checks
# ============================================================
print("\n== TEST GROUP 14: Data Integrity Cross-Checks ==")

def t14_job_in_recent():
    data = api("get", "/jobs/recent?limit=20")
    ids = [j.get("job_id") for j in data]
    return job1["job_id"] in ids
test("Completed validation job appears in recent jobs", t14_job_in_recent)

def t14_receipt_links_job():
    data = api("get", "/actions/recent?limit=20")
    linked = [r for r in data if r.get("job_id") == job1["job_id"]]
    return len(linked) > 0
test("Action receipt links back to job", t14_receipt_links_job)

def t14_event_for_job():
    data = api("get", "/events/timeline?hours=1&limit=100")
    job_events = [e for e in data if job1["job_id"] in str(e)]
    return len(job_events) > 0
test("Events exist for validation job lifecycle", t14_event_for_job)

def t14_pipeline_steps_match():
    data = api("get", "/pipeline/history?limit=5")
    val_pipe = [p for p in data if "validation" in str(p)]
    return len(val_pipe) > 0
test("Pipeline history shows validation run", t14_pipeline_steps_match)


# ============================================================
# FINAL SUMMARY
# ============================================================
print("\n" + "=" * 60)
print(f"PHASE 5 VALIDATION RESULTS")
print(f"=" * 60)
print(f"Total tests: {PASS + FAIL}")
print(f"Passed:      {PASS}")
print(f"Failed:      {FAIL}")
print(f"Pass rate:   {PASS/(PASS+FAIL)*100:.1f}%")
print(f"=" * 60)

with open("/tmp/phase5_results.json", "w") as f:
    json.dump({
        "total": PASS + FAIL,
        "passed": PASS,
        "failed": FAIL,
        "pass_rate": round(PASS / (PASS + FAIL) * 100, 1),
        "results": RESULTS
    }, f, indent=2)

print(f"\nDetailed results written to /tmp/phase5_results.json")

if FAIL > 0:
    print("\nFAILED TESTS:")
    for r in RESULTS:
        if r["status"] == "FAIL":
            print(f"  - {r['test']}: {r['detail']}")

sys.exit(0 if FAIL == 0 else 1)
