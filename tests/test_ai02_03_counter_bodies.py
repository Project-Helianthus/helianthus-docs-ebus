"""Synthetic metadata predicates only; no production decoder or executor."""
import copy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/ebus_standard/ai02-03-counter-bodies.md'
FIXTURE = ROOT / 'architecture/ebus_standard/fixtures/ai02_03_counter_bodies.json'
LAYOUTS = {
    '04': [('decimal_1s', 99), ('decimal_100s', 99), ('decimal_10000s', 99)],
    '05': [('minutes', 59), ('hours_100s', 59), ('hours_10000s', 59)],
    '06': [('minutes', 59), ('hours_1s', 99), ('hours_100s', 99),
           ('hours_10000s', 99)],
}
SERVICES = ('04', '05', '06', '07', '08', '10')
FIELD_KEYS = ('pb', 'sb', 'order', 'name', 'width_bits', 'type', 'minimum',
              'maximum', 'default', 'conversion', 'unit', 'encoding',
              'native_position', 'grade')
VARIANT_KEYS = ('pb', 'sb', 'variant', 'body_state', 'field_count', 'constructor',
                'callable', 'physical_side', 'qualification', 'grade')
EXPECTED_CASES = [
    ('decimal', '03', '04', [12, 34, 56], True, 563412),
    ('raw99', '03', '04', [99, 0, 0], True, 99),
    ('middle60', '03', '05', [1, 60, 2], False, None),
    ('three', '03', '05', [1, 2, 3], True, None),
    ('four', '03', '06', [59, 99, 99, 99], True, None),
    ('incomplete', '03', '06', [59, 99, 99], False, None),
    ('unknown', '03', '07', [], False, None),
]


def expected_fields():
    return [dict(zip(FIELD_KEYS, ('03', sb, order, name, 8, 'unsigned8', 0,
                                 maximum, 0 if sb == '04' else None, 'identity', 'raw', None, None,
                                 'Hypothesis')))
            for sb, fields in LAYOUTS.items()
            for order, (name, maximum) in enumerate(fields)]


def expected_variants():
    rows = []
    for sb in SERVICES:
        for variant in ('candidate-request', 'standard-response'):
            known = sb in LAYOUTS and variant == 'candidate-request'
            rows.append(dict(zip(VARIANT_KEYS, (
                '03', sb, variant, 'declared' if known else 'Unknown',
                len(LAYOUTS[sb]) if known else None, False, False, 'Unknown',
                'Unknown', 'Hypothesis' if known else 'Unknown'))))
    return rows


def cells(value):
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, list):
        return json.dumps(value)
    return str(value)


def tables(page):
    """Parse actual table cells, rather than searching for expected strings."""
    result = []
    current = []
    for line in page.splitlines() + ['']:
        if line.startswith('|'):
            current.append([part.strip() for part in line.strip('|').split('|')])
        elif current:
            result.append(current)
            current = []
    return result


def validate_contract(data, page):
    """Independent literal expectations guard both published representations."""
    fields, variants = expected_fields(), expected_variants()
    cases = [dict(zip(('id', 'pb', 'sb', 'raw', 'accepted', 'illustrative_count'), c))
             for c in EXPECTED_CASES]
    positives = [dict(name=name, pebus_relevant=True, physical_reply='Unknown')
                 for name in ('body-positive', 'prefix-only-positive')]
    expected = dict(evidence='synthetic only', fields=fields, variants=variants,
                    cases=cases, encoding_controls=[{}, {'encoding': 'raw'}],
                    position_controls=[{}, {'native_position': 0}],
                    positive_alternatives=positives)
    if data != expected:
        raise AssertionError('fixture differs from independent contract')
    parsed = tables(page)
    expected_rows = [
        [[cells(f[k]) for k in FIELD_KEYS] for f in fields],
        [[cells(v[k]) for k in VARIANT_KEYS] for v in variants],
        [[cells(x) for x in c] for c in EXPECTED_CASES],
        [[p['name'], 'true', 'Unknown'] for p in positives],
    ]
    if len(parsed) != 4 or [t[2:] for t in parsed] != expected_rows:
        raise AssertionError('page table differs from independent contract')


def local_view(data, pb, sb, variant, raw, previous=None):
    """Local admission example preserves partial data; never invokes anything."""
    out = dict(raw=list(raw), fields={}, complete=False, callable=False,
               last_known_good=copy.deepcopy(previous), count=None)
    selected = next((v for v in data['variants'] if
                     (v['pb'], v['sb'], v['variant']) == (pb, sb, variant)), None)
    if selected is None or selected['body_state'] != 'declared':
        return out
    fields = [f for f in data['fields'] if (f['pb'], f['sb']) == (pb, sb)]
    for f in fields:
        i = f['order']
        value = raw[i] if i < len(raw) else None
        valid = type(value) is int and f['minimum'] <= value <= f['maximum']
        out['fields'][f['name']] = dict(raw=value, value=value if valid else None)
    out['complete'] = len(raw) == len(fields) and all(
        f['value'] is not None for f in out['fields'].values())
    if out['complete'] and sb == '04':
        out['count'] = sum(value * 100**i for i, value in enumerate(raw))
    return out


class CounterMetadataContract(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_page_and_fixture_against_independent_constants(self):
        validate_contract(self.data, self.page)
        for target in re.findall(r'\]\(([^)]+)\)', self.page):
            self.assertNotIn('://', target)
            self.assertTrue((PAGE.parent / target.split('#')[0]).is_file(), target)

    def test_independent_examples_and_arithmetic(self):
        for _, pb, sb, raw, accepted, count in EXPECTED_CASES:
            with self.subTest(sb=sb, raw=raw):
                result = local_view(self.data, pb, sb, 'candidate-request', raw)
                self.assertEqual(result['complete'], accepted)
                self.assertEqual(result['count'], count)
                self.assertEqual(result['raw'], raw)
                self.assertFalse(result['callable'])
        self.assertEqual(int('63', 16), 99)
        self.assertEqual(12 + 100 * 34 + 10000 * 56, 563412)
        self.assertEqual(list(local_view(self.data, '03', '05', 'candidate-request',
                                        [1, 2, 3])['fields']),
                         ['minutes', 'hours_100s', 'hours_10000s'])

    def test_each_field_range_width_and_partial_preservation(self):
        for sb, fields in LAYOUTS.items():
            control = [1] * len(fields)
            self.assertTrue(local_view(self.data, '03', sb, 'candidate-request',
                                       control)['complete'])
            for i, (name, maximum) in enumerate(fields):
                for value, accepted in ((0, True), (maximum, True), (-1, False),
                                        (maximum + 1, False), (256, False),
                                        (True, False), (None, False)):
                    raw = control.copy()
                    raw[i] = value
                    previous = {'raw': control.copy()}
                    result = local_view(self.data, '03', sb, 'candidate-request',
                                        raw, previous)
                    with self.subTest(sb=sb, field=name, value=value):
                        self.assertEqual(result['complete'], accepted)
                        self.assertEqual(result['last_known_good'], previous)
                        self.assertEqual(result['raw'], raw)
                        for j, (other, _) in enumerate(fields):
                            if j != i:
                                self.assertEqual(result['fields'][other]['value'], 1)
            for raw in (control[:-1], control + [0]):
                self.assertFalse(local_view(self.data, '03', sb,
                                            'candidate-request', raw)['complete'])

    def test_each_identity_axis_independently(self):
        # Valid controls vary SB and variant independently; PB is fixed to 03.
        for sb, raw in [('04', [1, 2, 3]), ('05', [1, 2, 3]),
                        ('06', [1, 2, 3, 4])]:
            self.assertTrue(local_view(self.data, '03', sb,
                                       'candidate-request', raw)['complete'])
        base = ('03', '04', 'candidate-request')
        for axis, replacement in ((0, '05'), (1, '07'), (2, 'standard-response')):
            key = list(base)
            key[axis] = replacement
            result = local_view(self.data, *key, [1, 2, 3])
            self.assertFalse(result['complete'])
            self.assertEqual(result['fields'], {})
        for sb in ('07', '08', '10'):
            for variant in ('candidate-request', 'standard-response'):
                result = local_view(self.data, '03', sb, variant, [])
                self.assertFalse(result['complete'])
                self.assertFalse(result['callable'])

    def test_every_published_cell_and_fixture_field_is_guarded(self):
        # Deliberately corrupt each metadata value and every published data cell.
        for collection in ('fields', 'variants', 'cases', 'positive_alternatives'):
            for i, row in enumerate(self.data[collection]):
                for key in row:
                    mutant = copy.deepcopy(self.data)
                    mutant[collection][i][key] = 'CORRUPT'
                    with self.subTest(collection=collection, row=i, key=key):
                        with self.assertRaises(AssertionError):
                            validate_contract(mutant, self.page)
        for line in self.page.splitlines():
            if not line.startswith('|') or line.startswith('|---'):
                continue
            # Header cells are presentation; every claimed data value is pinned.
            if line.split('|')[1].strip() in ('PB', 'Case', 'Alternative'):
                continue
            parts = line.split('|')
            for i in range(1, len(parts) - 1):
                changed = parts.copy()
                changed[i] = ' CORRUPT '
                with self.assertRaises(AssertionError):
                    validate_contract(self.data, self.page.replace(
                        line, '|'.join(changed), 1))

    def test_encoding_and_position_absence_are_not_explicit_values(self):
        self.assertEqual(self.data['encoding_controls'], [{}, {'encoding': 'raw'}])
        self.assertEqual(self.data['position_controls'], [{}, {'native_position': 0}])
        self.assertNotEqual({}, {'encoding': 'raw'})
        self.assertNotEqual({}, {'native_position': 0})
        for control in ('encoding_controls', 'position_controls'):
            mutant = copy.deepcopy(self.data)
            mutant[control][0] = mutant[control][1].copy()
            with self.assertRaises(AssertionError):
                validate_contract(mutant, self.page)


if __name__ == '__main__':
    unittest.main()
