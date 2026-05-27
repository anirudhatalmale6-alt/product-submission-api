#!/usr/bin/env python3
"""Gutenberg block utilities — canonical module for all PetHub automation.
All scripts that create or modify post content MUST use this module."""

import re

APPROVED_BLOCKS = [
    'paragraph', 'heading', 'list', 'list-item', 'image',
    'quote', 'table', 'group', 'separator', 'columns', 'column',
    'details', 'buttons', 'button', 'cover', 'spacer'
]


def wrap_paragraph(text):
    if not text.strip():
        return ''
    inner = text.strip()
    if not inner.startswith('<p'):
        inner = f'<p>{inner}</p>'
    return f'<!-- wp:paragraph -->\n{inner}\n<!-- /wp:paragraph -->'


def wrap_heading(text, level=2, attrs=''):
    return (
        f'<!-- wp:heading {{"level":{level}}} -->\n'
        f'<h{level}{attrs}>{text}</h{level}>\n'
        f'<!-- /wp:heading -->'
    )


def wrap_list(items, ordered=False):
    tag = 'ol' if ordered else 'ul'
    attr = ' {"ordered":true}' if ordered else ''
    li_html = '\n'.join(f'<li>{item}</li>' for item in items)
    return (
        f'<!-- wp:list{attr} -->\n'
        f'<{tag}>\n{li_html}\n</{tag}>\n'
        f'<!-- /wp:list -->'
    )


def wrap_image(url, alt='', caption=''):
    fig_inner = f'<img src="{url}" alt="{alt}"/>'
    if caption:
        fig_inner += f'\n<figcaption class="wp-element-caption">{caption}</figcaption>'
    return (
        f'<!-- wp:image -->\n'
        f'<figure class="wp-block-image">{fig_inner}</figure>\n'
        f'<!-- /wp:image -->'
    )


def wrap_separator():
    return (
        '<!-- wp:separator -->\n'
        '<hr class="wp-block-separator has-alpha-channel-opacity"/>\n'
        '<!-- /wp:separator -->'
    )


def wrap_group(inner_blocks):
    content = '\n\n'.join(inner_blocks)
    return (
        f'<!-- wp:group -->\n'
        f'<div class="wp-block-group">{content}</div>\n'
        f'<!-- /wp:group -->'
    )


def wrap_quote(text):
    inner = text.strip()
    if not inner.startswith('<p'):
        inner = f'<p>{inner}</p>'
    return (
        f'<!-- wp:quote -->\n'
        f'<blockquote class="wp-block-quote">{inner}</blockquote>\n'
        f'<!-- /wp:quote -->'
    )


def wrap_table(rows, has_header=False):
    html_rows = []
    for i, row in enumerate(rows):
        tag = 'th' if (has_header and i == 0) else 'td'
        cells = ''.join(f'<{tag}>{cell}</{tag}>' for cell in row)
        html_rows.append(f'<tr>{cells}</tr>')

    parts = []
    if has_header and rows:
        parts.append(f'<thead>{html_rows[0]}</thead>')
        parts.append(f'<tbody>{"".join(html_rows[1:])}</tbody>')
    else:
        parts.append(f'<tbody>{"".join(html_rows)}</tbody>')

    table_html = f'<table>{"".join(parts)}</table>'
    return (
        f'<!-- wp:table -->\n'
        f'<figure class="wp-block-table">{table_html}</figure>\n'
        f'<!-- /wp:table -->'
    )


def build_page(blocks):
    return '\n\n'.join(b for b in blocks if b)


def validate_gutenberg(content):
    """Validate Gutenberg block structure. Returns (is_valid, issues_list).
    MUST be called before any API write to post content."""
    issues = []

    if not content or not content.strip():
        return True, []

    if '<!-- wp:' not in content:
        issues.append('no_block_markers')
        return False, issues

    opens = {}
    for m in re.finditer(r'<!-- wp:(\S+?)[\s{]', content):
        bt = m.group(1)
        opens[bt] = opens.get(bt, 0) + 1
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

    all_block_types = set(list(opens.keys()) + list(closes.keys()))
    unapproved = [bt for bt in all_block_types if bt not in APPROVED_BLOCKS]
    if unapproved:
        issues.append(f'unapproved_blocks:{",".join(unapproved)}')

    return len(issues) == 0, issues


def safe_update_content(session, wp_base, endpoint, post_id, content, extra_fields=None):
    """Update post/page content with mandatory block validation.
    Returns (success: bool, message: str)."""
    is_valid, issues = validate_gutenberg(content)
    if not is_valid:
        return False, f'Block validation failed: {"; ".join(issues)}'

    payload = {"content": content}
    if extra_fields:
        payload.update(extra_fields)

    r = session.post(f"{wp_base}/{endpoint}/{post_id}", json=payload)
    if r.status_code == 200:
        return True, 'ok'
    return False, f'API error {r.status_code}'
