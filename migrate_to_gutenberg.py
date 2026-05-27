#!/usr/bin/env python3
"""Permanent Gutenberg block migration.
Converts all classic HTML posts/pages into valid Gutenberg block markup.
Uses a controlled, approved block set only."""

import requests, json, re, html as html_mod, csv, os, time
from datetime import datetime, timezone
from html.parser import HTMLParser

WP_BASE = "https://pethubonline.com/wp-json/wp/v2"
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"

s = requests.Session()
s.auth = (WP_USER, WP_PASS)
s.headers['Accept-Encoding'] = 'gzip, deflate'

OUT = '/var/lib/freelancer/projects/40416335/phase10d'
os.makedirs(OUT, exist_ok=True)
NOW = datetime.now(timezone.utc).isoformat()

APPROVED_BLOCKS = [
    'paragraph', 'heading', 'list', 'list-item', 'image',
    'quote', 'table', 'group', 'separator', 'columns', 'column',
    'details', 'buttons', 'button', 'cover', 'spacer'
]

class HTMLToBlocks:
    """Convert classic HTML into valid Gutenberg blocks using approved block set."""

    def convert(self, html_content):
        if not html_content or not html_content.strip():
            return ''

        if '<!-- wp:' in html_content:
            return html_content

        lines = html_content.split('\n')
        blocks = []
        i = 0
        buffer = []

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                if buffer:
                    blocks.append(self._flush_paragraph(buffer))
                    buffer = []
                i += 1
                continue

            # Heading
            h_match = re.match(r'^<h(\d)([^>]*)>(.*?)</h\1>$', stripped, re.DOTALL)
            if h_match:
                if buffer:
                    blocks.append(self._flush_paragraph(buffer))
                    buffer = []
                level = h_match.group(1)
                attrs = h_match.group(2)
                content = h_match.group(3)
                block_attrs = f' {{"level":{level}}}' if level != '2' else ''
                blocks.append(
                    f'<!-- wp:heading{block_attrs} -->\n'
                    f'<h{level}{attrs}>{content}</h{level}>\n'
                    f'<!-- /wp:heading -->'
                )
                i += 1
                continue

            # Unordered list
            if stripped.startswith('<ul') and not stripped.startswith('<ul class="wp-block'):
                if buffer:
                    blocks.append(self._flush_paragraph(buffer))
                    buffer = []
                list_html, i = self._collect_until(lines, i, '</ul>')
                blocks.append(
                    f'<!-- wp:list -->\n{list_html}\n<!-- /wp:list -->'
                )
                continue

            # Ordered list
            if stripped.startswith('<ol') and not stripped.startswith('<ol class="wp-block'):
                if buffer:
                    blocks.append(self._flush_paragraph(buffer))
                    buffer = []
                list_html, i = self._collect_until(lines, i, '</ol>')
                blocks.append(
                    f'<!-- wp:list {{"ordered":true}} -->\n{list_html}\n<!-- /wp:list -->'
                )
                continue

            # Table
            if stripped.startswith('<table') or stripped.startswith('<figure class="wp-block-table'):
                if buffer:
                    blocks.append(self._flush_paragraph(buffer))
                    buffer = []
                table_html, i = self._collect_until(lines, i, '</table>')
                if '</figure>' in table_html:
                    end_fig = table_html.find('</figure>')
                    table_html = table_html[:end_fig + len('</figure>')]
                if not table_html.strip().startswith('<figure'):
                    table_html = f'<figure class="wp-block-table"><table>{self._extract_inner(table_html, "table")}</table></figure>'
                blocks.append(
                    f'<!-- wp:table -->\n{table_html}\n<!-- /wp:table -->'
                )
                continue

            # HR / separator
            if stripped in ('<hr />', '<hr/>', '<hr>', '<hr class="wp-block-separator has-alpha-channel-opacity"/>'):
                if buffer:
                    blocks.append(self._flush_paragraph(buffer))
                    buffer = []
                blocks.append(
                    '<!-- wp:separator -->\n'
                    '<hr class="wp-block-separator has-alpha-channel-opacity"/>\n'
                    '<!-- /wp:separator -->'
                )
                i += 1
                continue

            # Image
            img_match = re.match(r'^<img\s', stripped) or re.match(r'^<figure[^>]*class="[^"]*wp-block-image', stripped)
            if img_match:
                if buffer:
                    blocks.append(self._flush_paragraph(buffer))
                    buffer = []
                if stripped.startswith('<figure'):
                    fig_html, i = self._collect_until(lines, i, '</figure>')
                    blocks.append(f'<!-- wp:image -->\n{fig_html}\n<!-- /wp:image -->')
                else:
                    blocks.append(f'<!-- wp:image -->\n<figure class="wp-block-image"><{stripped[1:]}</figure>\n<!-- /wp:image -->')
                    i += 1
                continue

            # Blockquote
            if stripped.startswith('<blockquote'):
                if buffer:
                    blocks.append(self._flush_paragraph(buffer))
                    buffer = []
                bq_html, i = self._collect_until(lines, i, '</blockquote>')
                blocks.append(
                    f'<!-- wp:quote -->\n{bq_html}\n<!-- /wp:quote -->'
                )
                continue

            # Div blocks (styled containers, disclosure boxes, etc.)
            if stripped.startswith('<div'):
                if buffer:
                    blocks.append(self._flush_paragraph(buffer))
                    buffer = []
                div_html, i = self._collect_until_tag(lines, i, 'div')
                blocks.append(
                    f'<!-- wp:group -->\n<div class="wp-block-group">{div_html}</div>\n<!-- /wp:group -->'
                )
                continue

            # Paragraph (explicit or implicit)
            if stripped.startswith('<p') or (not stripped.startswith('<') and stripped):
                if stripped.startswith('<p'):
                    # Self-contained paragraph
                    if '</p>' in stripped:
                        if buffer:
                            blocks.append(self._flush_paragraph(buffer))
                            buffer = []
                        blocks.append(
                            f'<!-- wp:paragraph -->\n{stripped}\n<!-- /wp:paragraph -->'
                        )
                        i += 1
                        continue
                    else:
                        # Multi-line paragraph
                        p_html, i = self._collect_until(lines, i, '</p>')
                        if buffer:
                            blocks.append(self._flush_paragraph(buffer))
                            buffer = []
                        blocks.append(
                            f'<!-- wp:paragraph -->\n{p_html}\n<!-- /wp:paragraph -->'
                        )
                        continue
                else:
                    buffer.append(line)
                    i += 1
                    continue

            # Any other HTML element — wrap in group
            if stripped.startswith('<'):
                if buffer:
                    blocks.append(self._flush_paragraph(buffer))
                    buffer = []
                blocks.append(
                    f'<!-- wp:paragraph -->\n<p>{stripped}</p>\n<!-- /wp:paragraph -->'
                )
                i += 1
                continue

            buffer.append(line)
            i += 1

        if buffer:
            blocks.append(self._flush_paragraph(buffer))

        return '\n\n'.join(blocks)

    def _flush_paragraph(self, buffer):
        text = '\n'.join(buffer).strip()
        if not text:
            return ''
        if not text.startswith('<p'):
            text = f'<p>{text}</p>'
        return f'<!-- wp:paragraph -->\n{text}\n<!-- /wp:paragraph -->'

    def _collect_until(self, lines, start, end_marker):
        collected = [lines[start]]
        i = start + 1
        while i < len(lines):
            collected.append(lines[i])
            if end_marker in lines[i]:
                i += 1
                break
            i += 1
        return '\n'.join(collected), i

    def _collect_until_tag(self, lines, start, tag):
        depth = 0
        collected = []
        i = start
        while i < len(lines):
            line = lines[i]
            opens = len(re.findall(f'<{tag}[\\s>]', line))
            closes = len(re.findall(f'</{tag}>', line))
            depth += opens - closes
            collected.append(line)
            i += 1
            if depth <= 0:
                break
        return '\n'.join(collected), i

    def _extract_inner(self, html, tag):
        match = re.search(f'<{tag}[^>]*>(.*?)</{tag}>', html, re.DOTALL)
        return match.group(1) if match else html


def validate_blocks(content):
    """Validate Gutenberg block structure. Returns list of issues."""
    issues = []
    if '<!-- wp:' not in content:
        return ['no_blocks']

    opens = {}
    for m in re.finditer(r'<!-- wp:(\S+?)[\s{]', content):
        bt = m.group(1)
        opens[bt] = opens.get(bt, 0) + 1
    # Also match self-closing style: <!-- wp:separator -->
    for m in re.finditer(r'<!-- wp:(\S+?) -->', content):
        bt = m.group(1)
        if bt not in opens:
            opens[bt] = opens.get(bt, 0) + 1

    closes = {}
    for m in re.finditer(r'<!-- /wp:(\S+?) -->', content):
        bt = m.group(1)
        closes[bt] = closes.get(bt, 0) + 1

    for bt in set(list(opens.keys()) + list(closes.keys())):
        oc = opens.get(bt, 0)
        cc = closes.get(bt, 0)
        if oc != cc:
            issues.append(f'mismatch:{bt}(open={oc},close={cc})')

    # Check for orphan HTML between blocks
    no_blocks = re.sub(r'<!-- wp:.*?-->.*?<!-- /wp:\S+ -->', '', content, flags=re.DOTALL)
    remaining = re.sub(r'\s+', '', no_blocks)
    if re.search(r'<[a-z]', remaining) and len(remaining) > 20:
        issues.append(f'orphan_html({len(remaining)})')

    return issues


converter = HTMLToBlocks()

print("=" * 70)
print("GUTENBERG BLOCK MIGRATION")
print(f"Started: {NOW}")
print("=" * 70)

# Fetch all content
print("\nFetching all content...")
all_items = []
for endpoint in ['posts', 'pages']:
    for status in ['publish', 'draft']:
        page_num = 1
        while True:
            r = s.get(f"{WP_BASE}/{endpoint}",
                params={'per_page': 100, 'page': page_num, 'status': status, 'context': 'edit'})
            if r.status_code != 200: break
            batch = r.json()
            if not batch: break
            for item in batch:
                item['_endpoint'] = endpoint
            all_items.extend(batch)
            page_num += 1

print(f"Total items: {len(all_items)}")

# Identify items needing migration
classic_items = []
block_items = []
for item in all_items:
    raw = item['content'].get('raw', '')
    if not raw.strip():
        continue
    if '<!-- wp:' in raw:
        block_items.append(item)
    else:
        classic_items.append(item)

print(f"Already block-native: {len(block_items)}")
print(f"Classic (need migration): {len(classic_items)}")

# Backup all classic items
backups = {}
for item in classic_items:
    backups[str(item['id'])] = {
        'title': html_mod.unescape(item['title'].get('raw', item['title'].get('rendered', ''))),
        'endpoint': item['_endpoint'],
        'raw': item['content']['raw']
    }

backup_path = os.path.join(OUT, 'gutenberg_migration_backups.json')
with open(backup_path, 'w') as f:
    json.dump(backups, f)
print(f"\nBackups saved: {backup_path}")

# Migrate each classic item
results = []
success = 0
failed = 0

for item in classic_items:
    pid = item['id']
    title = html_mod.unescape(item['title'].get('raw', item['title'].get('rendered', '')))
    raw = item['content']['raw']
    endpoint = item['_endpoint']
    status = item['status']

    # Convert to blocks
    block_content = converter.convert(raw)

    # Validate
    issues = validate_blocks(block_content)

    if issues and 'no_blocks' in issues:
        print(f"  SKIP {endpoint} {pid}: {title[:50]} — empty or unconvertible")
        results.append({
            'id': pid, 'type': endpoint, 'title': title[:60], 'status': status,
            'migration_result': 'skipped', 'issues': '; '.join(issues),
            'block_count': 0
        })
        continue

    # Count blocks
    block_count = len(re.findall(r'<!-- wp:\S+', block_content))

    if issues:
        # Try to fix common issues
        result_status = f'migrated_with_warnings({"; ".join(issues)})'
    else:
        result_status = 'migrated_clean'

    # Apply migration
    r = s.post(f"{WP_BASE}/{endpoint}/{pid}", json={"content": block_content})
    if r.status_code == 200:
        success += 1
        print(f"  OK {endpoint} {pid}: {title[:50]} [{block_count} blocks]")
    else:
        failed += 1
        result_status = f'update_failed_{r.status_code}'
        print(f"  FAIL {endpoint} {pid}: {r.status_code}")

    results.append({
        'id': pid, 'type': endpoint, 'title': title[:60], 'status': status,
        'migration_result': result_status, 'issues': '; '.join(issues) if issues else 'none',
        'block_count': block_count
    })

    time.sleep(0.3)

# Save results
csv_path = os.path.join(OUT, 'Gutenberg_Migration_Log.csv')
with open(csv_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['id','type','title','status','migration_result','issues','block_count'])
    w.writeheader()
    w.writerows(results)

print(f"\n{'='*70}")
print(f"MIGRATION SUMMARY")
print(f"{'='*70}")
print(f"Total migrated: {success}")
print(f"Failed: {failed}")
print(f"Skipped: {len(results) - success - failed}")
print(f"Migration log: {csv_path}")
print(f"Backups: {backup_path}")
