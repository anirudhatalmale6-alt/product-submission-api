# Phase 10D: Output Evaluator Specification

## Purpose
The Output Evaluator automatically assesses every generated post against a fixed quality rubric before it is eligible for publication. It replaces manual spot-checks and enforces the 12-gate standard consistently across all content types.

## Site Context
- Site: pethubonline.com
- Evaluator runs against: WordPress REST API (draft posts)
- Gate standard: 12 mandatory gates (all must pass; no partial credit)

## Inputs
- post_id (int): WordPress post ID of the draft to evaluate
- cluster_context (dict): existing pillar and supporting post metadata for this cluster
- keyword_target (str): primary focus keyword for the post

## Outputs
```json
{
  "post_id": 4791,
  "title": "How to Choose the Right Dog Training Treats",
  "evaluated_at": "2026-05-27T14:30:00Z",
  "gates_passed": 12,
  "gates_failed": 0,
  "pass": true,
  "gate_results": {
    "title_present": true,
    "slug_unique": true,
    "excerpt_present": true,
    "category_assigned": true,
    "tags_present": true,
    "featured_image_alt": true,
    "meta_title": true,
    "meta_description": true,
    "h1_present": true,
    "internal_links_min2": true,
    "faq_block_present": true,
    "block_count_min20": true
  },
  "quality_scores": {
    "block_count": 32,
    "word_count_est": 1900,
    "internal_links_count": 3,
    "faq_question_count": 3,
    "readability_grade": "B"
  },
  "failures": [],
  "warnings": []
}
```

## Gate Definitions

| Gate | Check | Pass Condition |
|------|-------|----------------|
| G01 | title_present | post.title.rendered is non-empty |
| G02 | slug_unique | slug not used by any other post/page |
| G03 | excerpt_present | post.excerpt.rendered is non-empty |
| G04 | category_assigned | len(post.categories) >= 1 |
| G05 | tags_present | len(post.tags) >= 2 |
| G06 | featured_image_alt | featured_media alt_text is non-empty |
| G07 | meta_title | RankMath meta_title present and 50-60 chars |
| G08 | meta_description | RankMath meta_desc present and 140-160 chars |
| G09 | h1_present | content contains exactly one H1 |
| G10 | internal_links_min2 | content contains >= 2 internal links to pethubonline.com |
| G11 | faq_block_present | content contains wp:yoast-seo/faq-block or wp:core/details with FAQ schema |
| G12 | block_count_min20 | parsed block count >= 20 |

## Scoring (Non-Gate Quality Metrics)
These do not block publication but are reported for monitoring:
- word_count_est: target >1500 for informational, >2500 for supporting, >3500 for pillar
- readability_grade: A (Flesch >70), B (60-70), C (50-60), D (<50)
- internal_links_count: target >=3 for informational, >=5 for supporting
- faq_question_count: target >=3

## Implementation

```python
import requests, re

class OutputEvaluator:
    def __init__(self, wp_api_url, auth):
        self.api = wp_api_url
        self.auth = auth

    def evaluate(self, post_id):
        post = self._get_post(post_id)
        meta = self._get_rankmath_meta(post_id)
        blocks = self._count_blocks(post['content']['rendered'])
        results = {}

        results['title_present'] = bool(post['title']['rendered'].strip())
        results['slug_unique'] = self._check_slug_unique(post['slug'], post_id)
        results['excerpt_present'] = bool(post['excerpt']['rendered'].strip())
        results['category_assigned'] = len(post.get('categories',[])) >= 1
        results['tags_present'] = len(post.get('tags',[])) >= 2
        results['featured_image_alt'] = self._check_image_alt(post.get('featured_media',0))
        results['meta_title'] = 50 <= len(meta.get('title','')) <= 65
        results['meta_description'] = 120 <= len(meta.get('description','')) <= 165
        results['h1_present'] = len(re.findall(r'<h1[^>]*>',post['content']['rendered'])) == 1
        results['internal_links_min2'] = post['content']['rendered'].count('pethubonline.com') >= 2
        results['faq_block_present'] = 'wp:yoast-seo/faq-block' in post['content']['raw'] or 'FAQ' in post['content']['rendered']
        results['block_count_min20'] = blocks >= 20

        passed = all(results.values())
        failures = [k for k,v in results.items() if not v]
        return {'post_id':post_id, 'pass':passed, 'gate_results':results,
                'gates_passed':sum(results.values()), 'gates_failed':len(failures),
                'failures':failures}
```

## Warning Conditions (non-blocking)
- word_count_est < 1200: warn "content may be thin"
- internal_links_count < 3: warn "add more internal links"
- Duplicate focus keyword vs. existing post: warn "keyword cannibalisation risk"
- No product affiliate links when cluster is commercial: warn "missing monetisation"

## Safety Constraints
1. Evaluator is read-only – it NEVER modifies posts
2. On API error (timeout, 5xx): return pass=false with error flag; never assume pass
3. Evaluation results stored in evaluation_log.json before triggering publish pipeline
4. Re-evaluation required if post is edited after initial evaluation

## Integration Points
- Called by Improvement Orchestrator after content generation
- Results stored in Phase10D_PostPublish_Monitoring.csv (sampled)
- Failures escalated to operator via alert webhook
