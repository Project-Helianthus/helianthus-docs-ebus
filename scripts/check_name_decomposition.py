#!/usr/bin/env python3
"""Block inventory drift and false decompositions of canonical value names.

The contract applies to every eBUS service and fixture, then other protocols
and value surfaces. This guard covers the B524 register map and the naming
page's checked examples only; other native pages require enforcement children.
It does not establish native meaning, writability or equipment qualification.
Acceptance entries are maintained data, never generated during a check.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import check_register_names as grammar

ROOT = Path(__file__).resolve().parents[1]
MAP = 'protocols/vaillant/ebus-vaillant-B524-register-map.md'
CONTRACT = 'architecture/naming.md'
DATA = 'scripts/name-decomposition.json'
ROLES = {'subject', 'predicate', 'object', 'attribute', 'circumstance', 'feature',
         'index', 'part', 'placeholder', 'target', 'action'}
CIRCUMSTANCES = {'purpose', 'place', 'period', 'manner', 'condition'}


def extract_registers(text: str) -> dict[str, str]:
    """Read primary RR/Name tables, preserving operation and group namespaces.

    II is profile-dependent, not specified by these tables. The selector here
    identifies a catalog row, not a concrete device/register instance.
    Summary and correspondence tables do not create extra native identities.
    """
    result = {}
    operation = group = None
    active = False
    for line in text.splitlines():
        if line.startswith('## '):
            match = re.match(r'## OP=(0x[0-9A-F]{2})\b', line)
            operation = match[1] if match else None
            group = None
        if line.startswith('### GG='):
            group = re.match(r'### GG=(0x[0-9A-F]{2})\b', line)[1]
        if line.startswith('#') or not line.startswith('|'):
            active = False
        if re.match(r'^\| RR \| Name \| Cat \| Wire \|', line):
            active = True
            if operation is None or group is None:
                raise ValueError('register table without operation/group')
            continue
        if not active:
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if not cells or set(cells[0]) <= set('-: '):
            continue
        if not re.fullmatch(r'0x[0-9A-F]{4}(?:-0x[0-9A-F]{4})?', cells[0]):
            raise ValueError('malformed register selector')
        selector = f'{operation}/{group}/{cells[0]}'
        if selector in result:
            raise ValueError(f'duplicated selector {selector}')
        # Even unnamed rows participate in duplicate-selector detection.
        result[selector] = cells[1].strip('`')
    return {key: name for key, name in result.items() if not grammar.UNNAMED.fullmatch(name)}


def documented_examples(text: str) -> set[str]:
    names = set()
    active = False
    for line in text.splitlines():
        if line.startswith('| Name | Subject |') or line.startswith('| Checked spelling |'):
            active = True
            continue
        if not line.startswith('|'):
            active = False
        if active:
            cell = line.split('|')[1].strip()
            if cell.startswith('`') and cell.endswith('`'):
                name = cell[1:-1]
                if name in names:
                    raise ValueError(f'duplicate documented example {name}')
                names.add(name)
    return names


def normalized_role(role: str) -> str:
    if role in CIRCUMSTANCES:
        return 'circumstance'
    if role == 'bound':
        return 'attribute'
    return role


def validate_entry(entry: dict, vocabulary: grammar.Vocabulary, features: dict) -> None:
    name = entry['emitted']
    if not grammar.NAME.fullmatch(name):
        raise ValueError(f'{name}: requires snake_case')
    status = entry['status']
    if status not in {'compliant', 'provisional', 'existing_debt'}:
        raise ValueError(f'{name}: invalid status')
    roles = entry['roles']
    if set(roles) != ROLES:
        raise ValueError(f'{name}: incomplete role record')
    for values in roles.values():
        if not isinstance(values, list) or not all(isinstance(v, str) and v for v in values):
            raise ValueError(f'{name}: roles must contain term lists')
    if status != 'compliant':
        if not entry.get('open_question') or not re.fullmatch(r'Project-Helianthus/[a-z-]+#[0-9]+', entry.get('follow_up', '')):
            raise ValueError(f'{name}: debt requires an open question or violated rule and follow-up')
        if entry.get('current_spelling') != name:
            raise ValueError(f'{name}: debt must retain exact current spelling')
    if status == 'existing_debt':
        if entry['source'] != MAP:
            raise ValueError(f'{name}: debt is restricted to existing catalog rows')
        if entry.get('value_class') != 'unresolved' or any(roles.values()):
            raise ValueError(f'{name}: do not invent a decomposition for existing debt')
        return
    kind = entry['kind']
    if kind == 'structural':
        if any(roles.values()) or entry['value_class'] != 'structural' or status != 'compliant':
            raise ValueError(f'{name}: structural keys are outside the grammar')
        return
    if kind not in {'value', 'metric'}:
        raise ValueError(f'{name}: unknown kind')
    parts = entry['parts']
    expected_roles = {role: [] for role in ROLES}
    for term, role in parts:
        normalized = normalized_role(role)
        if normalized not in expected_roles:
            raise ValueError(f'{name}: unknown role')
        expected_roles[normalized].append(term)
    if roles != expected_roles:
        raise ValueError(f'{name}: role record differs from composition')
    feature = roles['feature']
    plain_parts = [(term, role) for term, role in parts if role != 'feature']
    if feature:
        if len(feature) != 1 or feature[0] not in features:
            raise ValueError(f'{name}: undocumented maker feature')
        definition = features[feature[0]]
        if not definition.get('observed_vaillant_definition') or not definition.get('generic_term_insufficient'):
            raise ValueError(f'{name}: feature needs a documented function')
        # Feature occupies the slot immediately before the value-class predicate.
        at = next(i for i, part in enumerate(parts) if part[1] == 'feature')
        if at + 1 >= len(parts) or parts[at + 1][1] != 'predicate':
            raise ValueError(f'{name}: predicate must follow feature')
    reconstructed = '_'.join(term for term, _ in parts)
    if kind == 'metric':
        prefix = entry.get('prefix')
        if prefix != 'helianthus':
            raise ValueError(f'{name}: requires single metric prefix')
        reconstructed = prefix + '_' + reconstructed
        unit = entry.get('unit')
        exception = entry.get('unit_exception')
        if exception:
            if (exception not in {'library', 'expvar', 'translation'}
                    or not entry.get('exception_reason') or not unit or entry.get('unit_label')):
                raise ValueError(f'{name}: undocumented unit exception')
            reconstructed += '_' + unit
        elif not unit or entry.get('unit_label') != unit:
            raise ValueError(f'{name}: requires constant unit label')
        if entry.get('counter'):
            reconstructed += '_total'
    if reconstructed != name:
        raise ValueError(f'{name}: spelling does not reconstruct from roles')
    plain = '_'.join(term for term, _ in plain_parts)
    # A maker feature may itself be the complete subject of a Boolean predicate.
    if feature and not any(role in {'subject', 'object'} for _, role in plain_parts):
        # Put the validation-only subject after purpose/attributes, preserving
        # their normal order. It never contributes to the emitted spelling.
        insertion = next((i for i, (_, role) in enumerate(plain_parts)
                          if role not in {'purpose', 'attribute'}), 0)
        expected = plain_parts[:insertion] + [('pump', 'subject')] + plain_parts[insertion:]
        plain = '_'.join(term for term, _ in expected)
    else:
        expected = plain_parts
    parsed = grammar.decompose(plain, vocabulary)
    if parsed != expected:
        raise ValueError(f'{name}: forbidden role order or incorrect role assignment')
    if len([term for term, role in parts if role != 'index']) > grammar.MAX_WORDS:
        raise ValueError(f'{name}: too many words')
    predicates = roles['predicate']
    value_class = entry['value_class']
    if value_class == 'measured':
        valid = not predicates and not roles['placeholder']
    elif value_class == 'unknown':
        valid = bool(roles['placeholder']) and status == 'provisional'
    else:
        valid = predicates == [value_class] and value_class in grammar.PREDICATES | grammar.PREDICATE_COMPOUNDS.keys()
    if not valid:
        raise ValueError(f'{name}: missing or incorrect predicate for value class')


def check(root: Path = ROOT) -> tuple[int, int]:
    data = json.loads((root / DATA).read_text())
    vocabulary = grammar.load_vocabulary()
    if data['schema_version'] != 1:
        raise ValueError('unsupported decomposition schema')
    entries = {}
    for entry in data['entries']:
        key = (entry['source'], entry['selector'])
        if key in entries:
            raise ValueError(f'duplicate decomposition entry {key}')
        validate_entry(entry, vocabulary, data['features'])
        entries[key] = entry['emitted']
    actual = {(MAP, key): name for key, name in extract_registers((root / MAP).read_text()).items()}
    actual.update({(CONTRACT, name): name for name in documented_examples((root / CONTRACT).read_text())})
    if entries != actual:
        missing = len(actual.keys() - entries.keys())
        unknown = len(entries.keys() - actual.keys())
        changed = sum(entries[key] != actual[key] for key in entries.keys() & actual.keys())
        raise ValueError(f'inventory drift: missing={missing}, unknown={unknown}, changed={changed}')
    return len(actual), sum(e['status'] != 'compliant' for e in data['entries'])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', required=True)
    parser.parse_args()
    try:
        count, debt = check()
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f'Naming decomposition failed: {error}', file=sys.stderr)
        return 1
    print(f'Naming decomposition passed: {count} entries; {debt} retained non-compliant entries.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
