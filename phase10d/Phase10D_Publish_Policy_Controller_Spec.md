# Phase 10D: Publish Policy Controller Specification

## Purpose
The Publish Policy Controller (PPC) implements the three-lane publication model for PetHub Online. It determines whether a validated draft is published automatically, queued for operator review, or held pending human approval — based on content type, cluster maturity, and risk signals.

## Three-Lane Model

### Lane A: Auto-Publish
Criteria (ALL must be true):
- All 12 quality gates: PASS
- Content type: informational_expansion
- Cluster: established (>5 published posts in cluster)
- No product price claims or specific affiliate links
- Word count: 1500-3000
- Operator auto-publish flag: enabled for this cluster

### Lane B: Review Queue (publish within 24h unless rejected)
Criteria (ANY triggers Lane B):
- Content type: supporting post
- Cluster: new or < 5 published posts
- Contains affiliate product links
- Word count > 3000
- Quality score < 80 (gates pass but quality metrics borderline)
- Post targets a keyword with existing cluster content (cannibalisation risk)

### Lane C: Hold for Approval (must be manually approved)
Criteria (ANY triggers Lane C):
- Content type: pillar post
- Content type: trust page or editorial policy page
- Contains specific product price claims
- Content is in Dog Food, Dog Health, or Puppy Care clusters (YMYL-adjacent)
- Any quality gate: FAIL (should not reach PPC but safety catch)
- Operator hold-all flag: enabled

## Decision Logic

```python
class PublishPolicyController:
    YMYL_CLUSTERS = {'Dog Food', 'Dog Health', 'Puppy Care', 'Cat Health'}
    ESTABLISHED_MIN = 5

    def determine_lane(self, post_id, quality_report, cluster_context, operator_config):
        # Hard stops → Lane C
        if not quality_report['pass']:
            return 'C', 'Quality gate failure'
        if cluster_context['type'] in ('pillar', 'trust_page'):
            return 'C', 'Content type requires approval'
        if cluster_context['cluster'] in self.YMYL_CLUSTERS:
            return 'C', 'YMYL-adjacent cluster'
        if operator_config.get('hold_all'):
            return 'C', 'Operator hold-all active'

        # Review triggers → Lane B
        if cluster_context['type'] == 'supporting':
            return 'B', 'Supporting post type'
        if cluster_context['post_count'] < self.ESTABLISHED_MIN:
            return 'B', 'New cluster'
        if quality_report.get('has_affiliate_links'):
            return 'B', 'Contains affiliate links'
        if quality_report['quality_scores']['word_count_est'] > 3000:
            return 'B', 'Long-form content'

        # Auto-publish → Lane A
        if operator_config.get('auto_publish_enabled'):
            return 'A', 'All criteria met'
        return 'B', 'Auto-publish not enabled'

    def execute(self, post_id, lane, reason):
        if lane == 'A':
            self.publish_immediately(post_id)
            self.log(post_id, 'auto_published', reason)
        elif lane == 'B':
            self.queue_for_review(post_id, deadline_hours=24)
            self.notify_operator(post_id, lane, reason)
        elif lane == 'C':
            self.hold(post_id)
            self.notify_operator(post_id, lane, reason, priority='high')
```

## Operator Configuration
```json
{
  "auto_publish_enabled": true,
  "auto_publish_clusters": ["Dog Beds", "Dog Toys", "Dog Training", "Cat Toys", "Cat Beds"],
  "hold_all": false,
  "review_queue_deadline_hours": 24,
  "notify_email": "anirudhatalmale22@gmail.com",
  "notify_on_lane_a": false,
  "notify_on_lane_b": true,
  "notify_on_lane_c": true
}
```

## Audit Log Schema
```csv
timestamp,post_id,title,lane,reason,action,operator,duration_to_publish_hours
2026-05-27T14:00:00Z,4791,How to Choose Dog Training Treats,A,All criteria met,auto_published,system,0
2026-05-27T14:05:00Z,4792,Puppy Socialisation Guide,A,All criteria met,auto_published,system,0
```

## Review Queue Interface
Lane B posts are presented to the operator via:
- Email digest (daily at 08:00 UTC): list of posts pending review
- WordPress draft list with "PPC-Review" tag applied
- Each post has deadline timestamp in custom field

## Safety Constraints
1. Lane C posts NEVER auto-publish, even if operator config changes
2. Lane B posts auto-reject (not publish) if not reviewed within 48h and hold_all=true
3. Any post that was held (Lane C) and later approved must be re-evaluated by Output Evaluator before publish
4. PPC never modifies post content — only status (draft→publish) or tags
5. All lane decisions logged permanently; log is append-only
6. If WordPress API returns error on publish: retry once after 30s; on second failure, escalate to operator

## Integration with Phase 10D
During Phase 10D, all 10 new expansion posts were Lane A eligible (informational, established clusters, gates passed). Trust page updates (4402, 4403, 300, 4405) were handled as Lane C (trust pages) with direct operator involvement.
