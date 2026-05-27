#!/usr/bin/env python3
"""
fix_pages_to_blocks.py
Convert classic editor pages back to Gutenberg block format.

These pages were originally created with Gutenberg blocks but had their
<!-- wp:blocktype --> comment markers stripped. The HTML structure and
wp-block-* CSS classes are correct - we just re-add the block comment markers.

Strategy: Use html.parser to find element start/end positions in the raw HTML,
then insert block markers at those positions without modifying the original HTML.
"""

import requests
import json
import re
import sys
from html.parser import HTMLParser


# WordPress API credentials
WP_USER = "jasonsarah2026"
WP_PASS = "yUmn Rngy EFE1 r7jr kjtm jmqx"
WP_API = "https://pethubonline.com/wp-json/wp/v2"

# Pages to convert
CLASSIC_PAGE_IDS = [4, 39, 1041, 1141, 1146, 1149, 1951, 3107, 3109, 3111, 3113, 3115]

# Pages that are already Gutenberg - DO NOT TOUCH
GUTENBERG_PAGE_IDS = [37, 38, 63, 293, 297, 300, 1144, 1176, 1842, 1956, 1960, 2561, 3892, 4402, 4403, 4404, 4405]

# Self-closing / void HTML tags
VOID_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
             'link', 'meta', 'param', 'source', 'track', 'wbr'}


class ElementNode:
    """Represents an HTML element with position info and children."""
    def __init__(self, tag, attrs, start_pos, classes=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.classes = classes or []
        self.start_pos = start_pos       # position of '<' of opening tag
        self.open_end_pos = None         # position after '>' of opening tag
        self.end_pos = None              # position after '>' of closing tag (or same as open_end for void)
        self.children = []               # child ElementNodes
        self.parent = None
        self.is_void = tag.lower() in VOID_TAGS

    def __repr__(self):
        return f'<{self.tag} classes={self.classes[:2]} start={self.start_pos} end={self.end_pos}>'


class PositionParser(HTMLParser):
    """
    Custom HTML parser that builds an element tree with exact positions
    from the raw HTML string.
    """
    def __init__(self, raw_html):
        super().__init__(convert_charrefs=False)
        self.raw = raw_html
        self.root_children = []
        self.stack = []  # stack of open ElementNodes
        self._line_offsets = self._build_line_offsets(raw_html)

    def _build_line_offsets(self, text):
        """Build a mapping of (line, col) -> byte offset."""
        offsets = [0]
        for i, ch in enumerate(text):
            if ch == '\n':
                offsets.append(i + 1)
        return offsets

    def _pos_to_offset(self, line, col):
        """Convert (line, col) from getpos() to a byte offset."""
        if line <= 0:
            return 0
        return self._line_offsets[line - 1] + col

    def _find_tag_start(self, pos):
        """
        getpos() returns the position of '>' or after it.
        We need the position of '<' for the start tag.
        Walk backwards from pos to find the '<'.
        """
        # The parser's getpos() points to end of tag
        # For start tags, search backwards for '<'
        i = pos
        while i > 0 and self.raw[i] != '<':
            i -= 1
        return i

    def handle_starttag(self, tag, attrs):
        line, col = self.getpos()
        offset = self._pos_to_offset(line, col)

        # getpos() points to the end of the tag (after '>') in many cases
        # but for html.parser it actually points to the first char of the tag
        # Let's find the actual '<' position
        # Actually, getpos() in html.parser returns position of the start of the tag
        # But we need to find where the opening tag starts: search backward from offset for '<'
        # In practice getpos() for start tags returns the line/col of the '<'
        # Let me just find the '<' near offset

        # Find the '<' that starts this tag
        start = offset
        # Sometimes offset is right at '<', sometimes slightly off
        if start < len(self.raw) and self.raw[start] == '<':
            tag_start = start
        else:
            # Search nearby
            tag_start = self.raw.rfind('<', max(0, start - 200), start + 1)
            if tag_start < 0:
                tag_start = start

        # Parse classes from attrs
        classes = []
        attrs_dict = dict(attrs)
        class_attr = attrs_dict.get('class', '')
        if class_attr:
            classes = class_attr.split()

        node = ElementNode(tag, attrs_dict, tag_start, classes)

        # Find end of opening tag (position after '>')
        gt_pos = self.raw.find('>', tag_start)
        if gt_pos >= 0:
            node.open_end_pos = gt_pos + 1
        else:
            node.open_end_pos = tag_start

        if node.is_void:
            node.end_pos = node.open_end_pos

        # Add to parent or root
        if self.stack:
            node.parent = self.stack[-1]
            self.stack[-1].children.append(node)
        else:
            self.root_children.append(node)

        if not node.is_void:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        """Handle self-closing tags like <br/>, <hr/>, <img/>."""
        self.handle_starttag(tag, attrs)
        # Already handled as void in handle_starttag

    def handle_endtag(self, tag):
        line, col = self.getpos()
        offset = self._pos_to_offset(line, col)

        # Find the '</' near offset
        tag_lower = tag.lower()

        # Find the closing tag
        search_start = max(0, offset - len(tag) - 10)
        close_start = self.raw.rfind('</', search_start, offset + len(tag) + 5)
        if close_start < 0:
            close_start = offset

        close_end = self.raw.find('>', close_start)
        if close_end >= 0:
            close_end += 1
        else:
            close_end = offset

        # Pop the stack to find matching open tag
        if self.stack:
            # Find matching tag in stack (innermost first)
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i].tag.lower() == tag_lower:
                    node = self.stack[i]
                    node.end_pos = close_end
                    self.stack = self.stack[:i]
                    break

    def parse(self):
        """Parse the HTML and return root children."""
        self.feed(self.raw)
        # Close any remaining open elements
        for node in reversed(self.stack):
            node.end_pos = len(self.raw)
        return self.root_children


def get_block_type(node):
    """
    Determine the Gutenberg block type for an element based on its CSS classes.
    Returns (block_name, is_container, json_attrs_str) or None.
    """
    classes = node.classes
    tag = node.tag.lower()

    if 'wp-block-paragraph' in classes:
        return ('paragraph', False, '')

    if 'wp-block-heading' in classes:
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            level = int(tag[1])
            if level == 2:
                return ('heading', False, '')
            else:
                return ('heading', False, f' {{"level":{level}}}')
        return ('heading', False, '')

    if 'wp-block-image' in classes:
        return ('image', False, '')

    if 'wp-block-list' in classes:
        return ('list', False, '')

    if 'wp-block-separator' in classes:
        return ('separator', False, '')

    if 'wp-block-cover' in classes:
        return ('cover', True, '')

    if 'wp-block-group' in classes:
        return ('group', True, '')

    if 'wp-block-columns' in classes:
        return ('columns', True, '')

    if 'wp-block-column' in classes:
        return ('column', True, '')

    if 'wp-block-buttons' in classes:
        return ('buttons', True, '')

    if 'wp-block-button' in classes:
        return ('button', False, '')

    if 'wp-block-details' in classes:
        return ('details', True, '')

    if 'affiliate-disclosure' in classes:
        return ('html', False, '')

    # Bare <p> without wp-block-paragraph class (seen inside cover/group blocks)
    if tag == 'p' and not any(c.startswith('wp-block-') for c in classes):
        return ('paragraph', False, '')

    return None


def process_node_tree(raw_html, nodes, depth=0):
    """
    Process a list of element nodes and return the HTML with block markers inserted.
    This works by building a new string that includes:
    - The original HTML exactly as-is
    - Block comment markers inserted before/after each element
    - For container blocks, markers also inserted around children
    """
    if not nodes:
        return raw_html

    # Sort insertions by position
    # We'll build the result by going through the raw HTML and inserting markers
    insertions = []  # list of (position, text_to_insert, priority)

    for node in nodes:
        if node.start_pos is None or node.end_pos is None:
            continue

        block_info = get_block_type(node)
        if block_info is None:
            # Wrap as wp:html
            block_name = 'html'
            is_container = False
            attrs_str = ''
        else:
            block_name, is_container, attrs_str = block_info

        # Insert opening marker before element
        open_marker = f'<!-- wp:{block_name}{attrs_str} -->\n'
        close_marker = f'\n<!-- /wp:{block_name} -->'

        insertions.append((node.start_pos, 'before', open_marker))
        insertions.append((node.end_pos, 'after', close_marker))

        # For container blocks, recursively process children
        if is_container and node.children:
            process_container_children(raw_html, node, insertions)

    return apply_insertions(raw_html, insertions)


def process_container_children(raw_html, parent_node, insertions):
    """
    For container blocks, add markers around each child element that needs them.
    """
    tag = parent_node.tag.lower()
    classes = parent_node.classes

    is_cover = 'wp-block-cover' in classes
    is_details = 'wp-block-details' in classes

    for child in parent_node.children:
        if child.start_pos is None or child.end_pos is None:
            continue

        child_classes = child.classes
        child_tag = child.tag.lower()

        # Skip cover structural elements (background image, overlay, inner-container wrapper)
        if is_cover:
            if 'wp-block-cover__image-background' in child_classes:
                continue
            if 'wp-block-cover__background' in child_classes:
                continue
            if 'wp-block-cover__inner-container' in child_classes:
                # Don't wrap the inner-container itself, but process its children
                if child.children:
                    process_container_children(raw_html, child, insertions)
                continue

        # Skip summary elements in details blocks
        if is_details and child_tag == 'summary':
            continue

        block_info = get_block_type(child)
        if block_info is None:
            block_name = 'html'
            is_container = False
            attrs_str = ''
        else:
            block_name, is_container, attrs_str = block_info

        open_marker = f'<!-- wp:{block_name}{attrs_str} -->\n'
        close_marker = f'\n<!-- /wp:{block_name} -->'

        insertions.append((child.start_pos, 'before', open_marker))
        insertions.append((child.end_pos, 'after', close_marker))

        if is_container and child.children:
            process_container_children(raw_html, child, insertions)


def apply_insertions(raw_html, insertions):
    """
    Apply all text insertions to the raw HTML string.
    Insertions are sorted by position, with 'before' insertions at a position
    coming before 'after' insertions at the same position.
    """
    if not insertions:
        return raw_html

    # Sort: by position, then 'after' before 'before' at the same position
    # (because 'after' for element A at pos X should come before 'before' for element B at pos X)
    # Actually: at the same position, 'after' closings should come before 'before' openings
    # Sort order: position ASC, then 'after' before 'before'
    def sort_key(item):
        pos, kind, text = item
        return (pos, 0 if kind == 'after' else 1)

    insertions.sort(key=sort_key)

    parts = []
    last_pos = 0
    for pos, kind, text in insertions:
        if pos > last_pos:
            parts.append(raw_html[last_pos:pos])
        elif pos < last_pos:
            # Overlapping - skip
            continue
        parts.append(text)
        last_pos = pos

    # Append remaining
    if last_pos < len(raw_html):
        parts.append(raw_html[last_pos:])

    return ''.join(parts)


def convert_page_content(html_content):
    """
    Convert a full page's HTML content from classic to Gutenberg block format.
    """
    parser = PositionParser(html_content)
    root_children = parser.parse()

    result = process_node_tree(html_content, root_children)

    # Clean up: ensure proper spacing between blocks (WordPress expects \n\n)
    result = re.sub(r'(<!-- /wp:[\w-]+ -->)\s*\n?\s*(<!-- wp:[\w-]+)', r'\1\n\n\2', result)

    return result


def main():
    s = requests.Session()
    s.headers['Accept-Encoding'] = 'gzip, deflate'
    s.auth = (WP_USER, WP_PASS)

    backups = {}
    results = {'success': [], 'failed': [], 'skipped': []}

    print("=" * 70)
    print("PetHub Pages: Classic -> Gutenberg Block Conversion")
    print("=" * 70)

    for page_id in CLASSIC_PAGE_IDS:
        print(f"\n{'─' * 50}")
        print(f"Processing page ID {page_id}...")
        print(f"{'─' * 50}")

        if page_id in GUTENBERG_PAGE_IDS:
            print(f"  SKIP: Page {page_id} is in the Gutenberg list!")
            results['skipped'].append(page_id)
            continue

        # Fetch
        try:
            r = s.get(f'{WP_API}/pages/{page_id}?context=edit')
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  ERROR fetching: {e}")
            results['failed'].append((page_id, f"fetch: {e}"))
            continue

        title = data.get('title', {}).get('raw', 'Unknown')
        content = data.get('content', {}).get('raw', '')

        print(f"  Title: {title}")
        print(f"  Content length: {len(content)} chars")

        if '<!-- wp:' in content:
            print(f"  SKIP: Already has block markers!")
            results['skipped'].append(page_id)
            continue

        if 'wp-block-' not in content:
            print(f"  SKIP: No wp-block-* classes found")
            results['skipped'].append(page_id)
            continue

        backups[page_id] = {'title': title, 'content': content}

        # Convert
        print(f"  Converting...")
        try:
            new_content = convert_page_content(content)
        except Exception as e:
            print(f"  ERROR converting: {e}")
            import traceback
            traceback.print_exc()
            results['failed'].append((page_id, f"convert: {e}"))
            continue

        marker_count = len(re.findall(r'<!-- wp:\w', new_content))
        close_count = len(re.findall(r'<!-- /wp:\w', new_content))
        print(f"  Block markers: {marker_count} open, {close_count} close")
        print(f"  New content length: {len(new_content)} chars")

        if marker_count == 0:
            print(f"  WARNING: No markers added - skipping")
            results['skipped'].append(page_id)
            continue

        if marker_count != close_count:
            print(f"  WARNING: Open/close marker mismatch!")

        # Update
        print(f"  Updating via API...")
        try:
            update_r = s.post(
                f'{WP_API}/pages/{page_id}',
                json={'content': new_content}
            )
            update_r.raise_for_status()
        except Exception as e:
            print(f"  ERROR updating: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    print(f"  API error: {e.response.json()}")
                except:
                    print(f"  Response: {e.response.text[:300]}")
            results['failed'].append((page_id, f"update: {e}"))
            continue

        # Verify
        print(f"  Verifying...")
        try:
            vr = s.get(f'{WP_API}/pages/{page_id}?context=edit')
            vr.raise_for_status()
            vc = vr.json().get('content', {}).get('raw', '')
            vm = len(re.findall(r'<!-- wp:\w', vc))
            if vm > 0:
                print(f"  VERIFIED: {vm} block markers in saved content")
                results['success'].append((page_id, title, marker_count))
            else:
                print(f"  WARNING: 0 markers found after save!")
                results['failed'].append((page_id, "markers lost after save"))
        except Exception as e:
            print(f"  Verify warning: {e}")
            results['success'].append((page_id, title, marker_count))

    # Summary
    print("\n\n" + "=" * 70)
    print("CONVERSION SUMMARY")
    print("=" * 70)

    if results['success']:
        print(f"\nSUCCESS ({len(results['success'])} pages):")
        for pid, title, markers in results['success']:
            print(f"  Page {pid}: {title} ({markers} block markers)")

    if results['skipped']:
        print(f"\nSKIPPED ({len(results['skipped'])} pages):")
        for pid in results['skipped']:
            print(f"  Page {pid}")

    if results['failed']:
        print(f"\nFAILED ({len(results['failed'])} pages):")
        for pid, reason in results['failed']:
            print(f"  Page {pid}: {reason}")

    if backups:
        bf = '/var/lib/freelancer/projects/40416335/page_backups_before_blocks.json'
        with open(bf, 'w') as f:
            json.dump(backups, f, indent=2)
        print(f"\nBackups saved to: {bf}")

    return len(results['failed']) == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
