# Phase 10D: Prompt & Workflow Registry Specification

## Purpose
The Prompt Workflow Registry (PWR) is a versioned catalogue of all prompts, generation templates, and workflow sequences used to produce PetHub Online content. It enables reproducibility, A/B testing, and safe updates without breaking existing pipelines.

## Site Context
- Site: pethubonline.com
- Content types: pillar posts, supporting posts, informational expansion posts, trust pages
- Prompt engine: Claude (Anthropic API) or equivalent LLM with structured output

## Registry Structure

### Prompt Record Schema
```json
{
  "prompt_id": "P-DOG-BED-EXPANSION-001",
  "version": "1.0.0",
  "created": "2026-05-27",
  "cluster": "Dog Beds",
  "content_type": "informational_expansion",
  "purpose": "Generate informational expansion post for Dog Beds cluster",
  "template_file": "templates/dog_beds_expansion.txt",
  "input_variables": ["target_keyword","pillar_url","supporting_urls","word_count_target"],
  "output_format": "gutenberg_blocks_json",
  "quality_gates": 12,
  "avg_quality_score": 84,
  "last_used": "2026-05-27",
  "status": "active"
}
```

## Current Registry (Phase 10D)

| ID | Cluster | Type | Version | Status | Avg Score |
|----|---------|------|---------|--------|-----------|
| P-DOG-BED-EXPANSION-001 | Dog Beds | informational | 1.0.0 | active | 84 |
| P-DOG-TOY-EXPANSION-001 | Dog Toys | informational | 1.0.0 | active | 83 |
| P-TRAINING-EXPANSION-001 | Dog Training | informational | 1.0.0 | active | 85 |
| P-PUPPY-CARE-EXPANSION-001 | Puppy Care | informational | 1.0.0 | active | 85 |
| P-GUTENBERG-MIGRATION-001 | All | migration | 1.0.0 | active | 99 |
| P-TRUST-PAGE-REFINEMENT-001 | Trust | refinement | 1.0.0 | active | 90 |
| P-CROSS-LINK-INJECTION-001 | All | enhancement | 1.0.0 | active | 88 |
| P-PILLAR-GENERATION-001 | All | pillar | 1.0.0 | draft | N/A |
| P-SUPPORTING-GENERATION-001 | All | supporting | 1.0.0 | draft | N/A |

## Workflow Sequences

### WF-001: New Cluster Expansion
1. Scan existing cluster posts → ClusterInventory
2. Run gap detector → GapReport
3. Select P-{CLUSTER}-EXPANSION-001 prompt
4. Generate post content (Gutenberg JSON)
5. Run Output Evaluator (12 gates)
6. If pass → submit draft to WordPress
7. Run Publish Policy Controller
8. If lane=auto → publish; else await operator approval
9. Run cross-link injection (P-CROSS-LINK-INJECTION-001)
10. Log to Phase10D_Publication_Log.csv

### WF-002: Gutenberg Migration
1. Fetch post content from WordPress API
2. Backup original to JSON file
3. Apply P-GUTENBERG-MIGRATION-001 transformation
4. Validate blocks via gutenberg_utils.validate_blocks()
5. If valid → PUT updated content to WordPress
6. Log to Gutenberg_Migration_Log.csv

### WF-003: Trust Page Refinement
1. Fetch trust page content
2. Apply P-TRUST-PAGE-REFINEMENT-001 (add cross-links + last-updated date)
3. PUT updated content
4. Log to Phase10D_Live_Page_Improvement_Log.csv

## Versioning Policy
- Version format: MAJOR.MINOR.PATCH (semver)
- MAJOR: prompt completely rewritten (break with old output format)
- MINOR: new output sections or variables added (backward compatible)
- PATCH: wording tweaks, clarifications
- Old versions archived but never deleted (audit trail)
- A/B testing: run new version in shadow mode for 5 posts before promoting to active

## Governance
- New prompts require: purpose statement, cluster assignment, test run on 2 posts
- Promotions from draft → active require: avg quality score >= 80 over 3 test runs
- Deprecated prompts kept for 90 days then archived
- Registry stored in: /var/lib/freelancer/projects/40416335/prompt_registry.json

## Safety Constraints
1. Prompts MUST include explicit instruction to pass 12-gate check
2. Prompts MUST NOT instruct model to fabricate product reviews or test results
3. Any prompt that generates affiliate content must include disclosure instruction
4. Prompts for trust pages require human review before activation
5. No prompt may instruct bypassing the Output Evaluator
