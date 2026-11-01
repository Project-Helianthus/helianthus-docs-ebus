"""Finite synthetic declarations and companion contract; no wire qualification."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / 'protocols/vaillant/ebus-b506-rf-sequence.md'
DATA = ROOT / 'protocols/vaillant/fixtures/ak06_b506_rf_sequence.json'
API = ROOT / 'architecture/ak06_b506_rf_sequence_api.md'
COUNTS = [(0, 'unlimited'), (1, 'finite-1'), (2, 'finite-2'), (255, 'finite-255')]
CLASSES = [(0, 'rf-class-a'), (1, 'rf-class-a'), (2, 'rf-class-a'),
           (3, 'rf-class-b'), (4, None)]
AXES = [
    ('Ab17Family', 'string', 'family', 'vaillant'),
    ('Ab17Variant', 'string', 'variant', 'B506-RF'),
    ('Ab17Primary', 'uint8', 'primary', '181'),
    ('Ab17Secondary', '*uint8', 'secondary', '6'),
    ('Ab17Operation', '*uint8', 'operation', '13 or 14'),
    ('Ab17Direction', 'string', 'direction', 'none'),
    ('Ab17Field', 'string', 'field', 'count, sequence or stop'),
    ('Ab17Alternative', 'string', 'alternative', 'none or 0/1/2/3'),
    ('Ab17Group', '*uint8', 'group', 'null'),
    ('Ab17InstanceScope', 'string', 'instance_scope', 'none'),
    ('Ab17Register', '*uint16', 'register', 'null'),
]
CONTROLS = [
    ('family', 'vaillant', 'other-family'),
    ('variant', 'B506-RF', 'other-variant'), ('primary', '181', '182'),
    ('secondary', '6', '7'), ('operation', '13', '7'),
    ('direction', 'none', 'read'), ('field', 'count', 'other-field'),
    ('alternative', 'none', 'other-alternative'), ('group', 'null', '1'),
    ('instance_scope', 'none', 'dynamic'), ('register', 'null', '1'),
    ('secondary', 'null', '0'), ('operation', 'null', '0'),
    ('group', 'null', '0'), ('register', 'null', '0'),
]


def tables(text):
    result = []
    current = []
    for line in text.splitlines() + ['']:
        if line.startswith('|'):
            current.append(tuple(c.strip() for c in line.strip('|').split('|')))
        elif current:
            result.append((current[0], current[2:]))
            current = []
    return result


def table(text, first_header):
    found = [rows for header, rows in tables(text) if header[0] == first_header]
    if len(found) != 1:
        raise AssertionError('expected exactly one table: ' + first_header)
    return found[0]


class RFSequenceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text())
        cls.native = NATIVE.read_text()
        cls.api = API.read_text()
        cls.flat_api = ' '.join(cls.api.split())

    def test_complete_finite_native_rows(self):
        expected = []
        for field, choice in [('count', None), ('sequence', 0), ('sequence', 1),
                              ('sequence', 2), ('sequence', 3), ('stop', None)]:
            row = dict(
                id='ak06-rf-' + field + ('' if choice is None else '-' + str(choice)),
                family='vaillant', variant='B506-RF', primary='0xB5', secondary='0x06',
                operation='OP14' if field == 'stop' else 'OP13', field=field,
                choice=choice, grade='Hypothesis', qualification='Unknown',
                extent_bytes=None, minimum_bytes=None, maximum_bytes=None,
                field_position={'count': 4, 'sequence': 3, 'stop': None}[field],
                raw_form='retain-original-bytes',
                unknown={k: 'Unknown' for k in
                         ('native_support', 'physical_effects', 'persistence', 'delivery')})
            if field == 'count':
                row['count'] = dict(zero_meaning='unlimited', finite_minimum=1,
                                    finite_maximum=255, finite_meaning='count-value')
            elif field == 'sequence':
                row['extent_class'] = ['rf-class-a', 'rf-class-a', 'rf-class-a', 'rf-class-b'][choice]
            else:
                row.update(related_operations=['OP13'], activation_order='Unknown',
                           retry_count=None, timeout=None, delivery_guarantee='Unknown',
                           completed_stop='Unknown')
            expected.append(row)
        self.assertEqual(self.data['rows'], expected)
        self.assertEqual(self.data['grade'], 'Hypothesis')
        self.assertEqual(self.data['qualification'], 'Unknown')
        self.assertEqual(set(self.data), {'grade', 'qualification', 'rows',
                                         'count_cases', 'sequence_cases', 'payload_cases'})

    def test_candidate_positions_and_provenance(self):
        self.assertEqual([(r['field'], r['field_position']) for r in self.data['rows']],
                         [('count', 4), ('sequence', 3), ('sequence', 3),
                          ('sequence', 3), ('sequence', 3), ('stop', None)])
        for text in (self.native, self.api):
            flat = ' '.join(text.split())
            self.assertIn('fixtures/b506-b508-candidate-fields.csv', text)
            self.assertIn('unconfirmed on the wire', flat)
        self.assertIn('count is at candidate request offset 4 and sequence at offset 3',
                      ' '.join(self.native.split()))
        self.assertIn('offset 0 is PB, 1 is SB and 2 is the operation byte',
                      ' '.join(self.native.split()))
        self.assertIn('candidate request offset 4 for count and 3 for sequence', self.flat_api)
        self.assertIn('stop position remains `null`', self.flat_api)

    def test_count_cases_and_independent_page(self):
        self.assertEqual(self.data['count_cases'],
                         [dict(count=n, meaning=m) for n, m in COUNTS])
        self.assertEqual(table(self.native, 'Count byte (decimal)'),
                         [(str(n), m, 'Hypothesis') for n, m in COUNTS])
        rule = self.data['rows'][0]['count']
        for value, expected in COUNTS:
            with self.subTest(count=value):
                if value == 0:
                    actual = rule['zero_meaning']
                else:
                    self.assertLessEqual(rule['finite_minimum'], value)
                    self.assertLessEqual(value, rule['finite_maximum'])
                    self.assertEqual(rule['finite_meaning'], 'count-value')
                    actual = 'finite-' + str(value)
                self.assertEqual(actual, expected)

    def test_sequence_cases_and_independent_page(self):
        self.assertEqual(self.data['sequence_cases'], [dict(sequence=n, extent_class=c,
                                                          extent_bytes=None) for n, c in CLASSES])
        self.assertEqual(table(self.native, 'Sequence (decimal)'),
                         [(str(n), c or 'unmapped', *(['Unknown'] * 3), '3',
                           'Hypothesis' if n < 4 else 'Unknown') for n, c in CLASSES])
        declared = {r['choice']: r['extent_class'] for r in self.data['rows']
                    if r['field'] == 'sequence'}
        for value in range(256):
            with self.subTest(sequence=value):
                self.assertEqual(declared.get(value),
                                 ['rf-class-a', 'rf-class-a', 'rf-class-a', 'rf-class-b'][value]
                                 if value < 4 else None)

    def test_absent_extent_and_payloads(self):
        self.assertEqual(self.data['payload_cases'], [dict(raw_hex=h, qualification='Unknown',
                                                         extent_bytes=None) for h in ('', '23 45')])
        self.assertEqual(table(self.native, 'Fabricated payload (hex)'),
                         [('empty', 'Unknown', 'Unknown'), ('23 45', 'Unknown', 'Unknown')])
        for row in self.data['rows']:
            for name in ('extent_bytes', 'minimum_bytes', 'maximum_bytes'):
                with self.subTest(row=row['id'], metadata=name):
                    self.assertIn(name, row)
                    self.assertIsNone(row[name])
            for case in self.data['payload_cases']:
                raw = bytes.fromhex(case['raw_hex'])
                self.assertIn(len(raw), (0, 2))
                self.assertEqual(row['qualification'], 'Unknown')
                self.assertEqual(case['qualification'], 'Unknown')

    def test_stop_relations_and_unknowns(self):
        self.assertEqual(table(self.native, 'Stop'), [
            ('OP14', op, 'Hypothesis', 'Unknown', 'Unknown', 'Unknown')
            for op in ('OP13',)])
        stop = self.data['rows'][-1]
        self.assertEqual(stop['related_operations'], ['OP13'])
        for name in ('activation_order', 'delivery_guarantee', 'completed_stop'):
            self.assertEqual(stop[name], 'Unknown')
        for name in ('retry_count', 'timeout'):
            self.assertIsNone(stop[name])

    def test_api_signatures_and_eleven_axes(self):
        self.assertEqual(re.findall(r'^Ab17\w+\(.*$', self.api, re.M), [
            'Ab17Entries() (json.RawMessage, error)',
            'Ab17Lookup(Ab17Key) (json.RawMessage, bool, error)'])
        self.assertIn('package `vaillant`', self.api)
        self.assertEqual(table(self.api, 'Field'), AXES)
        self.assertIn('Optional absent and explicit zero differ.', self.api)
        self.assertIn('such as `00` or `dynamic`', self.api)

    def test_api_finite_production_rows(self):
        self.assertEqual(table(self.api, 'ID'), [
            ('ab17-rf-count-none', '13', 'count', 'none', '0 unlimited; 1..255 finite count-value'),
            *[('ab17-rf-sequence-' + str(n), '13', 'sequence', str(n), c)
              for n, c in enumerate(['ab17-class-a', 'ab17-class-a', 'ab17-class-a', 'ab17-class-b'])],
            ('ab17-rf-stop-none', '14', 'stop', 'none', 'associated with 13; order Unknown')])
        for phrase in ('not hexadecimal-to-decimal conversions',
                       '**Unknown:** their numeric wire adaptation',
                       '`grade: Hypothesis`', '`qualification: Unknown`',
                       '`ab17_raw_form: retain-original-bytes`', '`ab17_unknown`'):
            self.assertIn(phrase, self.flat_api)

    def test_identity_controls_and_mutation_mapping(self):
        controls = table(self.api, 'Axis')
        self.assertEqual([r[:3] for r in controls], CONTROLS)
        for axis, control, changed, mutation in controls:
            with self.subTest(axis=axis, control=control):
                self.assertNotEqual(control, changed)
                self.assertEqual(mutation, 'collapse absent and zero ' + axis
                                 if control == 'null' and changed == '0' else 'ignore ' + axis)
        self.assertEqual({r[0] for r in controls}, {r[2] for r in AXES})

    def test_api_copy_error_and_lookup_boundaries(self):
        for phrase in (
            '`Ab17Entries` returns a JSON array',
            '`Ab17Lookup` returns exactly one whole row for an exact key',
            'returns `(nil, false, nil)`',
            'Invalid embedded JSON or duplicate keys return an error',
            'Validation checks identity uniqueness', 'requires every axis',
            'No wildcard or nearest-key lookup is permitted',
            'There is no cross-family, variant, direction, field or alternative fallback',
            'Every call returns independent deep byte copies',
            'cannot affect another outstanding result or a later result',
            'including a later call through the other API',
            'Raw form and candidate grade are retained in whole-row results',
        ):
            self.assertIn(phrase, self.flat_api)

    def test_unknown_boundaries_and_compatibility(self):
        for phrase in ('ab17_extent_bytes', 'ab17_minimum_bytes', 'ab17_maximum_bytes',
                       'ab17_field_position', 'ab17_activation_order', 'ab17_retry_count',
                       'ab17_timeout', 'ab17_delivery_guarantee', 'ab17_completed_stop',
                       'Missing extent is not zero', 'last-known-good', 'uncertain freshness',
                       'Existing catalog/provider APIs and routability remain unchanged',
                       'eBUS MCP compatibility and GraphQL parity remain unchanged',
                       'not stable before Helianthus 1.0', 'registry has no dependency back'):
            self.assertIn(phrase, self.flat_api)
        for phrase in ('an absent extent is not zero', 'All other byte values (4..255)',
                       'not an ordered activation sequence', 'last-known-good',
                       'Synthetic correctness', 'No native capture'):
            self.assertIn(phrase, ' '.join(self.native.split()))

    def test_native_boundary_and_links(self):
        combined = self.native + DATA.read_text()
        self.assertIsNone(re.search(r'Ab17|GraphQL|MCP|Helianthus|json.RawMessage|Go behavior', combined))
        for target in re.findall(r'\]\(([^)]+)\)', self.native):
            self.assertNotIn(':', target)
            self.assertTrue((NATIVE.parent / target).is_file(), target)
        self.assertTrue(self.native.index('native B506 contract') < self.native.index('## Count candidates'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
