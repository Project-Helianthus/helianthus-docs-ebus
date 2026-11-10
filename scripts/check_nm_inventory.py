#!/usr/bin/env python3
"""Validate coverage and source limits in the NM implementation inventory."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('nm-model.md', 'nm-discovery.md', 'nm-participant-policy.md')
FIELDS = {'key', 'page', 'section', 'status', 'source', 'symbol', 'limit'}
EXTRA = {'target-list', 'cycle-timer', 'status-map', 'aggregate-health',
         'active-flag', 'state-machine', 'broadcast-helper', 'responder-helper'}
HELPERS = {
    'broadcast-helper': ('internal/nm_runtime/nm_runtime.go', 'NewRuntime and Emit', 'Broadcast Lane'),
    'responder-helper': ('internal/nm_runtime/responder_runtime.go', 'NewResponderRuntime and EmitResponder', 'Responder Lane'),
}


def expected_sections(root):
    result = {}
    for page in PAGES:
        path = 'architecture/' + page
        text = (root / path).read_text()
        for title in re.findall(r'^#{2,4} (.+)$', text, re.MULTILINE):
            if title in {'Implementation status', 'Purpose', 'Cross-References', 'Evidence Snapshot'}:
                continue
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
            result[page[:-3] + '-' + slug] = (path, title)
    return result


def validate(rows, root=ROOT):
    expected = expected_sections(root)
    keys = [row.get('key') for row in rows]
    if len(keys) != len(set(keys)) or set(keys) != set(expected) | EXTRA:
        raise ValueError('missing, duplicate or unexpected element')
    for row in rows:
        if set(row) != FIELDS or not isinstance(row['limit'], str) or not row['limit'].strip():
            raise ValueError('invalid fields or missing qualification limit')
        key = row['key']
        page, section = expected.get(key, ('architecture/nm-model.md', 'Runtime Components'))
        if key in HELPERS:
            source, symbol, section = HELPERS[key]
            if (row['status'], row['source'], row['symbol']) != ('implemented helper', source, symbol):
                raise ValueError('helper source, symbol or status mismatch')
            if 'Uncomposed' not in row['limit']:
                raise ValueError('helper composition limit missing')
        else:
            status = 'excluded' if key == 'nm-participant-policy-fe-01-explicitly-out-of-baseline' else 'target'
            if (row['status'], row['source'], row['symbol']) != (status, '', ''):
                raise ValueError('unsubstantiated implementation status or source')
        if (row['page'], row['section']) != (page, section):
            raise ValueError('page or section mismatch')


def main():
    rows = json.loads((ROOT / 'architecture/nm-implementation-inventory.json').read_text())
    validate(rows)
    print(f'NM inventory: {len(rows)} elements validated')


if __name__ == '__main__':
    main()
