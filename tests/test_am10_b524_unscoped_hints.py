"""Owned synthetic contract seam; does not import or certify production Go code."""

import copy
import json
import math
from pathlib import Path
import re
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/am10_b524_unscoped_hints.md'
FIXTURE = ROOT / 'architecture/fixtures/am10_b524_unscoped_hints.json'
KEY_FIELDS = ('opcode', 'group', 'register')
PROPERTIES = ('Type', 'Min', 'Max', 'Step')
CATALOG_CONTRACT = {
    'source': 'b524StaticConstraintsCatalog', 'count': 46,
    'key': ['opcode', 'group', 'register'],
    'sort': ['opcode', 'group', 'register'],
    'result_type': 'AM09B524UnscopedHint', 'status': 'unscoped_hint',
    'qualified': False, 'grade': 'Unknown',
    'properties': ['Type', 'Min', 'Max', 'Step'], 'no_hint': None,
}


def key_of(value):
    if not isinstance(value, dict) or set(value) != set(KEY_FIELDS):
        raise ValueError('malformed key fields')
    for field, maximum in zip(KEY_FIELDS, (255, 255, 65535)):
        if type(value[field]) is not int or not 0 <= value[field] <= maximum:
            raise ValueError('malformed key type or width')
    return tuple(value[field] for field in KEY_FIELDS)


def validate_result(result):
    if set(result) != set(KEY_FIELDS + PROPERTIES + ('status', 'qualified', 'grade')):
        raise ValueError('malformed result fields')
    key_of({field: result[field] for field in KEY_FIELDS})
    if (result['status'] != 'unscoped_hint' or result['qualified'] is not False
            or result['grade'] != 'Unknown'):
        raise ValueError('malformed qualification')
    if result['Type'] not in ('f32_range', 'u16_range'):
        raise ValueError('unknown synthetic type')
    for field in ('Min', 'Max', 'Step'):
        if type(result[field]) not in (int, float) or not math.isfinite(result[field]):
            raise ValueError('malformed numeric field')


class SyntheticHintView:
    """Validation seam over owned examples, never a replacement embedded catalog."""

    def __init__(self, rows):
        self._rows = {}
        for row in rows:
            if set(row) != {'key', 'hint'} or set(row['hint']) != set(PROPERTIES):
                raise ValueError('malformed row')
            key = key_of(row['key'])
            if key[0] != 2 or key == (2, 0, 1) or key in self._rows:
                raise ValueError('disallowed or duplicate catalog key')
            result = dict(row['key'], **row['hint'], status='unscoped_hint',
                          qualified=False, grade='Unknown')
            validate_result(result)
            self._rows[key] = copy.deepcopy(result)

    def lookup(self, key):
        return copy.deepcopy(self._rows.get(key_of(key)))

    def enumerate(self):
        return [copy.deepcopy(self._rows[key]) for key in sorted(self._rows)]


def admit(rows, raw, previous):
    """Retain independently owned raw/prior state even if admission fails."""
    result = {'raw': bytearray(raw), 'last_known_good': copy.deepcopy(previous),
              'qualified': False}
    try:
        result['view'] = SyntheticHintView(rows)
        result['hint_error'] = None
    except (ValueError, TypeError, KeyError):
        result['view'] = None
        result['hint_error'] = 'malformed'
    return result


class UnscopedHintsContract(unittest.TestCase):
    def setUp(self):
        self.package = json.loads(FIXTURE.read_text())
        self.rows = self.package['controls']
        self.page = PAGE.read_text()
        self.view = SyntheticHintView(self.rows)

    def test_package_contract_and_grades(self):
        self.assertEqual(self.package['kind'], 'AM10SyntheticHintPackage')
        self.assertEqual(self.package['catalog_contract'], CATALOG_CONTRACT)
        self.assertIs(self.package['catalog_contract']['qualified'], False)
        self.assertEqual(self.package['grades'], {
            'table_structure': 'Proven', 'numeric_interpretation': 'Hypothesis',
            'applicability': 'Unknown'})
        self.assertEqual(self.package['unknown'], [
            'family_applicability', 'physical_support', 'presence', 'freshness',
            'execution', 'effects', 'persistence', 'delivery'])

    def test_independent_numeric_controls(self):
        # Explicit byte patterns and integer arithmetic, not view-generated oracles.
        f32 = lambda raw: struct.unpack('<f', bytes.fromhex(raw))[0]
        expected = [
            ((2, 0, 2), ('f32_range', f32('0000d0c1'), f32('00002041'), 1)),
            ((2, 0, 4), ('u16_range', 0, int.from_bytes(b'\x2c\x01', 'little'), 10)),
            ((2, 3, 2), ('f32_range', f32('00007041'), f32('0000f041'), f32('0000003f'))),
        ]
        self.assertEqual(len(self.rows), 3)
        for row, (identity, numbers) in zip(self.rows, expected):
            with self.subTest(identity=identity):
                self.assertEqual(key_of(row['key']), identity)
                self.assertEqual(tuple(row['hint'][f] for f in PROPERTIES), numbers)
                result = self.view.lookup(dict(zip(KEY_FIELDS, identity)))
                self.assertEqual(tuple(result[f] for f in PROPERTIES), numbers)
                validate_result(result)
        self.assertEqual((10 - (-26)) // 1, 36)
        self.assertEqual((300 - 0) // 10, 30)
        self.assertEqual((30 - 15) / f32('0000003f'), 30)

    def test_page_numeric_table_matches_independent_examples(self):
        section = self.page.split('| Opcode | Group | Register | Type | Min | Max | Step |', 1)[1]
        section = section.split('\n\n', 1)[0]
        lines = [line for line in section.splitlines() if line.startswith('|')][1:]
        values = [[cell.strip() for cell in line.strip('|').split('|')] for line in lines]
        self.assertEqual(values, [
            ['2', '0', '2', 'f32_range', '-26', '10', '1'],
            ['2', '0', '4', 'u16_range', '0', '300', '10'],
            ['2', '3', '2', 'f32_range', '15', '30', '0.5']])
        for cells, row in zip(values, self.rows):
            self.assertEqual([int(v) for v in cells[:3]], list(row['key'].values()))
            self.assertEqual(cells[3], row['hint']['Type'])
            self.assertEqual([float(v) for v in cells[4:]],
                             [row['hint'][f] for f in ('Min', 'Max', 'Step')])

    def test_page_case_and_result_contract(self):
        cases = json.loads(re.search(r'```json\n(.*?)\n```', self.page, re.S)[1])
        self.assertEqual(cases, {
            'valid': 'unscoped_hint', 'op06': 'no_hint',
            'absent_register': 'no_hint', 'all_zero_key': 'no_hint',
            'missing_key_field': 'malformed', 'extra_key_field': 'malformed',
            'invalid_key_type_or_width': 'malformed', 'duplicate_key': 'malformed',
            'partial_hint': 'malformed', 'unknown_type': 'malformed',
            'exact_bound_or_identity_fields': 'malformed', 'storage': 'independent'})
        section = self.page.split('| Field | Required value or meaning |', 1)[1].split('\n\n', 1)[0]
        fields = [line.split('|')[1].strip() for line in section.splitlines()
                  if line.startswith('|')][1:]
        self.assertEqual(fields, list(KEY_FIELDS) + ['status', 'qualified', 'grade'] + list(PROPERTIES))
        for required in ('`unscoped_hint`', '`false`', '`Unknown` (applicability)',
                         'must not call `LookupB524Bound`, merge exact',
                         'no second\nembedded catalog', 'sorted numerically ascending',
                         'Returned collections and values own their storage.',
                         'has 46 OP02 entries', '**Hypothesis:**', '**Unknown:**',
                         'Existing eBUS MCP compatibility and GraphQL parity remain unchanged'):
            self.assertIn(required, self.page)

    def test_exact_lookup_axes_and_absences(self):
        key = {'opcode': 2, 'group': 0, 'register': 2}
        self.assertIsNotNone(self.view.lookup(key))
        # Each key component changes alone, with the unchanged key as valid control.
        for field, value in (('opcode', 6), ('group', 1), ('register', 3)):
            with self.subTest(field=field):
                changed = dict(key, **{field: value})
                self.assertIsNone(self.view.lookup(changed))
                self.assertIsNotNone(self.view.lookup(key))
        self.assertEqual(self.package['no_hint_keys'], [
            {'opcode': 2, 'group': 0, 'register': 1},
            {'opcode': 6, 'group': 0, 'register': 2},
            {'opcode': 6, 'group': 0, 'register': 4},
            {'opcode': 6, 'group': 3, 'register': 2}])
        for missing in self.package['no_hint_keys']:
            self.assertIsNone(self.view.lookup(missing))
        for opcode in (0, 1, 255):
            self.assertIsNone(self.view.lookup(dict(key, opcode=opcode)))

    def test_missing_zero_malformed_and_width_axes(self):
        valid = {'opcode': 2, 'group': 0, 'register': 2}
        for field, maximum in zip(KEY_FIELDS, (255, 255, 65535)):
            with self.subTest(field=field):
                absent = dict(valid)
                del absent[field]
                with self.assertRaises(ValueError):
                    self.view.lookup(absent)
                # Explicit zero is well-formed on each axis, even when absent in table.
                self.view.lookup(dict(valid, **{field: 0}))
                self.view.lookup(dict(valid, **{field: maximum}))
                for bad in (-1, maximum + 1, None, True, '0', 0.0, [], {}):
                    with self.subTest(bad=bad), self.assertRaises(ValueError):
                        self.view.lookup(dict(valid, **{field: bad}))
        self.assertIsNone(self.view.lookup(dict.fromkeys(KEY_FIELDS, 0)))
        for bad in (None, [], '', 0):
            with self.assertRaises(ValueError):
                self.view.lookup(bad)

    def test_context_axes_cannot_specialize(self):
        for axis in ('family', 'variant', 'instance', 'software', 'hardware',
                     'api_identity', 'operation', 'direction', 'selector', 'field'):
            for value in (None, 0, 'synthetic-family-a', 'synthetic-family-b'):
                with self.subTest(axis=axis, value=value), self.assertRaises(ValueError):
                    self.view.lookup(dict(self.rows[0]['key'], **{axis: value}))
            self.assertFalse(self.view.lookup(self.rows[0]['key'])['qualified'])

    def test_disallowed_duplicate_partial_and_extra_rows(self):
        for key in ({'opcode': 2, 'group': 0, 'register': 1},
                    {'opcode': 6, 'group': 0, 'register': 2}):
            with self.assertRaises(ValueError):
                SyntheticHintView([dict(self.rows[0], key=key)])
        with self.assertRaises(ValueError):
            SyntheticHintView(self.rows + [copy.deepcopy(self.rows[0])])
        for field in PROPERTIES:
            rows = copy.deepcopy(self.rows)
            del rows[0]['hint'][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                SyntheticHintView(rows)
        for location, field in (('hint', 'bound'), ('hint', 'instance'),
                                ('key', 'family'), ('key', 'instance')):
            rows = copy.deepcopy(self.rows)
            rows[0][location][field] = 0
            with self.assertRaises(ValueError):
                SyntheticHintView(rows)

    def test_numeric_and_type_field_axes(self):
        for field in ('Min', 'Max', 'Step'):
            for bad in (None, True, '0', float('nan'), float('inf'), -float('inf')):
                rows = copy.deepcopy(self.rows)
                rows[0]['hint'][field] = bad
                with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                    SyntheticHintView(rows)
        rows = copy.deepcopy(self.rows)
        rows[0]['hint']['Type'] = 'unknown_range'
        with self.assertRaises(ValueError):
            SyntheticHintView(rows)

    def test_exact_shape_and_qualification_rejection(self):
        original = self.view.lookup(self.rows[0]['key'])
        for field, bad in (('qualified', True), ('qualified', 0), ('status', 'success'),
                           ('status', 'exact_bound'), ('grade', 'Proven'),
                           ('grade', 'Hypothesis')):
            with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                validate_result(dict(original, **{field: bad}))
        for extra in ('bound', 'bounds', 'exact_profile', 'family', 'instance'):
            with self.assertRaises(ValueError):
                validate_result(dict(original, **{extra: 0}))

    def test_synthetic_46_enumeration_and_all_op06_counterparts(self):
        # Synthetic extra keys are invented stress inputs, never claimed real keys.
        rows = copy.deepcopy(self.rows)
        rows += [{'key': {'opcode': 2, 'group': 128, 'register': n},
                  'hint': {'Type': 'u16_range', 'Min': 0, 'Max': 300, 'Step': 10}}
                 for n in range(43)]
        view = SyntheticHintView(list(reversed(rows)))
        results = view.enumerate()
        self.assertEqual(len(results), 46)
        expected = [(2, 0, 2), (2, 0, 4), (2, 3, 2)] + [(2, 128, n) for n in range(43)]
        self.assertEqual([tuple(r[k] for k in KEY_FIELDS) for r in results], expected)
        for identity, result in zip(expected, results):
            key = dict(zip(KEY_FIELDS, identity))
            self.assertEqual(view.lookup(key), result)
            self.assertIsNone(view.lookup(dict(key, opcode=6)))

    def test_returned_and_source_storage_independence(self):
        baseline = copy.deepcopy(self.rows)
        expected = copy.deepcopy(self.view.enumerate())
        lookup = self.view.lookup(self.rows[0]['key'])
        for field in lookup:
            lookup[field] = None
        collection = self.view.enumerate()
        collection[0]['Min'] = 999
        collection[1]['register'] = 999
        collection.clear()
        self.assertEqual(self.view.enumerate(), expected)
        self.assertEqual(self.view.lookup(baseline[0]['key']), expected[0])
        self.assertEqual(self.rows, baseline)
        self.rows[0]['hint']['Min'] = 999
        self.rows[0]['key']['register'] = 999
        self.assertEqual(self.view.enumerate(), expected)

    def test_partial_raw_memory_and_last_known_good(self):
        partial = self.package['partial']
        self.assertEqual(partial, {
            'raw_hex': '0000020000', 'last_known_good': {'independent_field': 0},
            'hint_error': 'malformed', 'qualified': False})
        self.assertIn('synthetic raw payload `0000020000`', self.page)
        self.assertIn('`independent_field=0`', self.page)
        raw = bytearray.fromhex(partial['raw_hex'])
        previous = {'independent_field': 0}
        rows = copy.deepcopy(self.rows)
        del rows[0]['hint']['Step']
        retained = admit(rows, raw, previous)
        self.assertIsNone(retained['view'])
        self.assertEqual(retained['hint_error'], 'malformed')
        self.assertIs(retained['qualified'], False)
        raw[0] = 255
        previous['independent_field'] = 5
        self.assertEqual(retained['raw'], bytes.fromhex('0000020000'))
        self.assertEqual(retained['last_known_good'], {'independent_field': 0})
        retained['raw'][1] = 255
        retained['last_known_good']['independent_field'] = 8
        self.assertEqual(raw[1], 0)
        self.assertEqual(previous['independent_field'], 5)
        self.assertIsNotNone(admit(self.rows, b'\x00', {'independent_field': 0})['view'])

    def test_relative_links_resolve(self):
        for target in re.findall(r'\]\(([^)]+)\)', self.page):
            self.assertNotIn('://', target)
            self.assertTrue((PAGE.parent / target.split('#', 1)[0]).is_file(), target)


if __name__ == '__main__':
    unittest.main()
