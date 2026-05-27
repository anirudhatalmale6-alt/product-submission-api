# Phase 10D: Quality Drift Detector Specification

## Purpose
The Quality Drift Detector (QDD) identifies gradual degradation in content quality across PetHub Online over time — caused by CMS updates, plugin conflicts, prompt drift, or accumulated small edits. It acts as a continuous quality audit separate from the per-post Output Evaluator.

## Problem Statement
Individual post gates pass at publication. But over weeks/months:
- WordPress updates may corrupt block markup
- Plugins may strip meta fields
- Internal links may break as slugs change
- RankMath metadata may be lost during bulk operations
- Content standards may drift as new contributors edit posts

The QDD detects these patterns before they affect search rankings.

## Inputs
- WordPress API: all published posts + pages (weekly full scan)
- Baseline snapshot: JSON file recording gate results at publication time
- Search Console data: imported weekly (CTR, impressions, rank)

## Outputs
```json
{
  "scan_date": "2026-05-27",
  "posts_scanned": 95,
  "drift_detected": false,
  "drift_alerts": [],
  "quality_trend": {
    "avg_block_count": {"current": 42.3, "baseline": 42.1, "delta": 0.2},
    "faq_presence_pct": {"current": 100, "baseline": 100, "delta": 0},
    "meta_title_pct": {"current": 98, "baseline": 100, "delta": -2},
    "internal_links_avg": {"current": 3.8, "baseline": 3.5, "delta": 0.3}
  },
  "posts_with_regressions": []
}
```

## Drift Metrics

| Metric | Baseline | Alert Threshold | Critical Threshold |
|--------|----------|-----------------|-------------------|
| avg_block_count | 42 | drop > 5 | drop > 15 |
| faq_presence_pct | 100% | < 95% | < 90% |
| meta_title_pct | 100% | < 98% | < 95% |
| meta_desc_pct | 100% | < 98% | < 95% |
| internal_links_avg | 3.5 | drop > 1.0 | drop > 2.0 |
| orphaned_posts_pct | 0% | > 5% | > 10% |
| broken_internal_links | 0 | > 3 | > 10 |

## Detection Algorithm

```python
class QualityDriftDetector:
    def run_weekly_scan(self):
        posts = self.fetch_all_published_posts()
        current_metrics = self.compute_metrics(posts)
        baseline = self.load_baseline()
        alerts = []
        for metric, value in current_metrics.items():
            delta = value - baseline[metric]
            threshold = ALERT_THRESHOLDS[metric]
            if abs(delta) > threshold:
                alerts.append({
                    'metric': metric,
                    'baseline': baseline[metric],
                    'current': value,
                    'delta': delta,
                    'severity': 'critical' if abs(delta) > CRITICAL_THRESHOLDS[metric] else 'warning'
                })
        self.save_report(current_metrics, alerts)
        if alerts:
            self.notify_operator(alerts)
        # Update baseline only if no critical alerts
        if not any(a['severity']=='critical' for a in alerts):
            self.update_baseline(current_metrics)
```

## Regression Identification
When aggregate drift is detected, QDD identifies individual posts:
1. Re-evaluate each post against full 12-gate check
2. Compare with stored gate results at publication
3. Flag any post where any gate has regressed from pass → fail
4. Generate per-post regression report

## Broken Link Detection
- Weekly: fetch all internal links from content
- HEAD request each link (throttled: 1 req/s)
- Flag 404, 301 chains > 2 hops, 5xx responses
- Report to operator with source post + broken URL

## Trend Reporting
Monthly trend CSV: `QDD_Monthly_Trend_YYYY-MM.csv`
- Columns: month, metric, value, delta_vs_prior, delta_vs_baseline
- Used to identify slow drift that stays under weekly alert thresholds

## Baseline Management
- Initial baseline set at end of each phase (e.g., Phase 10D completion)
- Baseline updated weekly only if zero critical alerts
- Baselines versioned and stored: baselines/baseline_YYYY-MM-DD.json
- Never auto-update baseline during active incident

## Alert Channels
- Email: anirudhatalmale22@gmail.com
- Subject: "[PetHub QDD] {severity} drift detected – {N} alerts"
- Body: metric table + list of affected post IDs

## Safety Constraints
1. QDD is read-only – never modifies posts
2. On scan error: mark as inconclusive; do NOT update baseline
3. If >20% of posts fail re-evaluation: escalate as CRITICAL immediately
4. QDD runs in isolation from Improvement Orchestrator (separate process)
5. Scan must complete within 10 minutes; abort + alert if exceeded
