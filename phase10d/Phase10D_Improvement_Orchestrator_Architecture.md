# Phase 10D: Improvement Orchestrator Architecture

## Purpose
The Improvement Orchestrator is the top-level controller that drives autonomous content improvement cycles for PetHub Online. It coordinates cluster scanning, gap detection, content generation, quality validation, and publication in a closed-loop pipeline.

## System Context
- Site: pethubonline.com (WordPress + WooCommerce)
- API: https://pethubonline.com/wp-json/wp/v2
- Auth: Application Password (jasonsarah2026)
- Content model: pillar → supporting → expansion (informational)

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Improvement Orchestrator                │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Cluster  │  │  Gap     │  │  Content         │  │
│  │ Scanner  │→ │ Detector │→ │  Generator       │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│        ↑               ↓              ↓             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Monitor  │  │ Publish  │  │  Quality         │  │
│  │ & Report │← │ Policy   │← │  Evaluator       │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Components

### 1. Cluster Scanner
- Input: WordPress API posts/pages list
- Behaviour: Groups all content by cluster (Dog Beds, Dog Toys, etc.)
- Output: ClusterInventory JSON with post counts, publish dates, block counts
- Frequency: Daily

### 2. Gap Detector
- Input: ClusterInventory, keyword research targets (CSV)
- Behaviour: Identifies missing informational posts vs. target keyword list
  - Missing slug check (GET /wp-json/wp/v2/posts?slug=target-slug)
  - Competitor gap analysis (manual import from Ahrefs/SEMrush exports)
- Output: GapReport JSON ranked by search volume × topical relevance

### 3. Content Generator
- Input: GapReport item, cluster context (existing pillar + supporting posts)
- Behaviour:
  - Generates full post content with Gutenberg blocks
  - Applies 12-gate safety check before submission
  - Calls gutenberg_utils.py for block validation
  - Sets RankMath SEO metadata via REST API
- Output: Draft post on WordPress (status=draft)
- Safety: NEVER publishes directly; passes to Publish Policy Controller

### 4. Quality Evaluator
- Input: Draft post ID
- Behaviour: Runs automated quality checks (see Output Evaluator Spec)
- Output: QualityReport JSON with pass/fail per gate
- Escalation: Fails → flag for human review; do not auto-publish

### 5. Publish Policy Controller
- Input: QualityReport (all gates pass), operator approval flag
- Behaviour: Determines publish lane (auto/review/hold)
- Output: Published post or escalation alert
- Detail: See Phase10D_Publish_Policy_Controller_Spec.md

### 6. Monitor & Report
- Input: Publication log, search console data (weekly import)
- Behaviour: Tracks rank movement, traffic, indexing status
- Output: Weekly monitoring report CSV

## Data Flows

```python
# Pseudocode – main orchestration loop
def run_improvement_cycle():
    inventory = cluster_scanner.scan()
    gaps = gap_detector.find_gaps(inventory)
    for gap in gaps[:MAX_PER_CYCLE]:
        post_id = content_generator.generate(gap)
        quality = quality_evaluator.evaluate(post_id)
        if quality.all_pass:
            publish_controller.submit(post_id)
        else:
            alert_operator(post_id, quality.failures)
    monitor.report(inventory)
```

## Safety Constraints
1. MAX_PER_CYCLE = 5 posts per orchestration run to prevent content floods
2. All posts start as draft; no direct publish without QualityReport pass
3. gutenberg_utils.validate_blocks() MUST pass before any API write
4. Cluster lock: if a cluster has >10 drafts pending, pause generation for that cluster
5. Human approval required for: pillar posts, trust pages, any post with product comparisons
6. Rate limit: max 10 WP API writes per minute; back off 60s on 429

## Implementation Notes
- Language: Python 3.11+
- Dependencies: requests, python-wordpress-xmlrpc (backup), gutenberg_utils (local)
- Config: environment variables for WP_API_URL, WP_USER, WP_APP_PASSWORD
- Logging: structured JSON logs to /var/log/pethub/orchestrator.log
- Retry: exponential backoff (1s, 2s, 4s, max 30s) on transient errors

## Deployment
- Run as scheduled job (cron or systemd timer)
- Recommended schedule: daily at 02:00 UTC
- Alert channel: email or Slack webhook on failures
