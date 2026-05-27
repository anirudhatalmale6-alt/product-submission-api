# Phase 10D: Operational Runbook Updates

## Document Purpose
This runbook captures all procedures added or updated during Phase 10D. It supersedes equivalent sections in the Phase 10C runbook. Operators should refer to this document for day-to-day content operations.

## Prerequisites
- WordPress admin access: pethubonline.com/wp-admin
- WP Application Password: jasonsarah2026 / yUmn Rngy EFE1 r7jr kjtm jmqx
- Python 3.11+ with requests library
- Phase 10D scripts: /var/lib/freelancer/projects/40416335/phase10d/

---

## Procedure 1: Publish a Trust Page (4402, 4403, 4405)

1. Log in to pethubonline.com/wp-admin
2. Pages → All Pages → find the trust page by ID or title
3. Review content for accuracy; check cross-links are working (click each link)
4. Change Status from Draft → Published
5. Set permalink to clean slug (e.g., /how-we-research-pet-products/)
6. Click Update
7. Verify live URL loads correctly
8. Add URL to GSC URL Inspection → Request Indexing
9. Update Phase10D_Trust_Methodology_Publication_Status.csv

**Time estimate**: 10 minutes per page

---

## Procedure 2: Running the 12-Gate Quality Check

The check is embedded in gutenberg_utils.py. To run manually:

```python
import requests
session = requests.Session()
session.auth = ("jasonsarah2026", "yUmn Rngy EFE1 r7jr kjtm jmqx")
session.headers['Accept-Encoding'] = 'gzip, deflate'

post = session.get("https://pethubonline.com/wp-json/wp/v2/posts/POST_ID").json()
# Check gates manually:
print("Title:", bool(post['title']['rendered']))
print("Excerpt:", bool(post['excerpt']['rendered']))
print("Categories:", len(post['categories']) >= 1)
print("Tags:", len(post['tags']) >= 2)
```

Full automated check: run `python3 phase10d/output_evaluator.py POST_ID`

---

## Procedure 3: Gutenberg Block Migration

**When to use**: When a post shows as "classic" format in WP editor.

1. Backup content: `python3 phase10d/backup_post.py POST_ID`
2. Run migration: `python3 phase10d/gutenberg_utils.py migrate POST_ID`
3. Verify output: visit post in WP editor; confirm blocks render correctly
4. Check frontend: view post URL; confirm formatting is correct
5. Log result in Gutenberg_Migration_Log.csv

**Safety**: Migration never overwrites without backup. Check JSON backup in gutenberg_migration_backups.json.

---

## Procedure 4: Adding Internal Cross-Links

1. Identify source post (the one being updated)
2. Identify target posts from Phase10D_Internal_Linking_Map.csv
3. In WP editor, locate relevant paragraph in source post
4. Highlight anchor text → Insert Link → paste target URL
5. Ensure link is contextually relevant (not forced)
6. Update post
7. Log in Phase10D_Internal_Linking_Map.csv: source_id, target_url, date

**Target**: minimum 3 internal links per informational post; 5 per supporting; 7 per pillar

---

## Procedure 5: Submitting New Posts to Google Search Console

1. Open Google Search Console → pethubonline.com property
2. URL Inspection → enter post URL
3. Click "Request Indexing"
4. Update Phase10D_Indexing_Crawl_Assurance.csv: set indexing_status to "submitted_to_gsc"
5. Repeat for each new post (max 10 submissions/day recommended)
6. Check back in 7 days; update status to "indexed" or "crawled_not_indexed"

---

## Procedure 6: Weekly Quality Drift Check (Manual)

Until QDD is automated:

1. Open WP admin → Posts → All Posts
2. Filter by "Published" → note total count
3. Spot-check 5 random posts:
   - Open each in editor
   - Confirm blocks render (not classic editor)
   - Check RankMath score is >= 70
   - Verify at least 2 internal links
4. If any issue found: log in Phase10D_Live_Page_Improvement_Log.csv and fix
5. Run this check every Monday

**Time estimate**: 20 minutes

---

## Procedure 7: Adding a New Expansion Post (Agent-Assisted)

1. Provide agent with: target keyword, cluster name, existing pillar URL
2. Agent generates post using prompt registry template
3. Agent submits as draft to WordPress
4. Operator reviews draft in WP admin
5. If content looks good: check 12 gates manually (Procedure 2)
6. If all pass: change status to Published
7. Submit URL to GSC (Procedure 5)
8. Add cross-links from pillar/supporting posts (Procedure 4)

---

## Procedure 8: Reviewing Lane B Queue (Pending Review Posts)

1. WP Admin → Posts → All Posts → filter by Draft
2. Look for posts tagged "PPC-Review"
3. Open each post and review:
   - Quality: does content read naturally? Is it accurate?
   - Gates: run 12-gate check (Procedure 2)
   - Links: are affiliate links properly disclosed?
4. If approved: Remove "PPC-Review" tag; set status to Published
5. If rejected: add "PPC-Rejected" tag; leave as Draft; notify agent with reason

---

## Known Issues & Workarounds

| Issue | Symptom | Workaround |
|-------|---------|------------|
| Classic block appears after migration | WP editor shows "Classic" block | Re-run gutenberg_utils.py migrate POST_ID |
| RankMath meta not visible via API | meta field returns empty | Use WP admin to set manually; check RankMath REST API extension is enabled |
| Internal link 404 after slug change | Link returns 404 | Check Redirection plugin; add redirect from old slug to new |
| Post not indexed after 14 days | GSC shows "Discovered – not indexed" | Check page load speed; add more internal links pointing to post |

---

## Contact & Escalation
- Agent contact: submit task via Freelancer project 40416335
- Urgent WordPress issues: check hosting provider (SiteGround/WP Engine) status page first
- GSC issues: Google Search Console Help Centre

## Change Log
| Date | Change | Author |
|------|--------|--------|
| 2026-05-27 | Phase 10D procedures added (Gutenberg migration, trust pages, expansion posts) | Phase 10D Agent |
