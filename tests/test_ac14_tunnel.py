"""Synthetic declaration checks; no transport or physical qualification."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B517.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ac14_tunnel.json'
AXES = ('family', 'variant', 'direction', 'service', 'operation', 'alternative')
UNKNOWN = ['physical relationship of B517/B518', 'destination roles', 'forwarder',
           'correlation', 'timeout', 'refusal', 'fragmentation', 'transport/peer support',
           'scheduling', 'write permission', 'native adaptation', 'peer effects',
           'physical qualification']


def expected_records():
    # Independent literal expectations: no values read from the page or fixture.
    def constant(position, value):
        return {'logical': position, 'value': value, 'bits': 8}
    def opaque(position):
        return {'logical': position, 'kind': 'opaque', 'extent': 'end-of-PDU',
                'minimum': 0, 'abstract_maximum': 65535}
    return [
        {'family': 'B517', 'variant': None, 'direction': 'request',
         'service': [181, 23], 'operation': None, 'alternative': 'tunnel-request',
         'grade': 'Hypothesis', 'constants': [constant(0, 181), constant(1, 23)],
         'destination': {'logical': 2, 'type': 'u8', 'minimum': 0, 'maximum': 255, 'default': 8},
         'data': opaque(3)},
        {'family': 'B517', 'variant': None, 'direction': 'positive',
         'service': [181, 24], 'operation': None, 'alternative': 'tunnel-positive',
         'grade': 'Hypothesis', 'constants': [constant(0, 181), constant(1, 24)], 'data': opaque(2)},
        {'family': 'B518', 'variant': None, 'direction': 'request', 'service': None,
         'operation': None, 'alternative': 'partial-identity-request', 'grade': 'Hypothesis',
         'constants': []},
        {'family': 'B518', 'variant': None, 'direction': 'positive', 'service': None,
         'operation': None, 'alternative': 'partial-identity-positive', 'grade': 'Hypothesis',
         'constants': []},
    ]


HEADERS = {
    ('## Candidate fields', 0): ('Family', 'Direction', 'Service declaration', 'Logical fields', 'Grade'),
    ('## Candidate fields', 1): ('Field', 'Domain or extent', 'Default', 'Interpretation', 'Grade'),
    ('## Evidence and limits', 0): ('Unresolved property', 'Grade'),
}


def table(page, heading, index=0):
    # One table only: the index-th run of consecutive table lines under the heading, up to the next '## '.
    section = page.split(heading + '\n', 1)[1].split('\n## ', 1)[0]
    runs, current = [], []
    for line in section.splitlines():
        if line.startswith('|'):
            current.append(tuple(cell.strip() for cell in line.strip('|').split('|')))
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    if index >= len(runs):
        raise AssertionError('Scoped table missing')
    rows, header = runs[index], HEADERS[(heading, index)]
    if rows[0] != header or rows[1] != ('---',) * len(header):
        raise AssertionError('Scoped table header changed')
    return rows[2:]


class TunnelDeclarations(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_records_exact(self):
        # Kills numeric, selector, extent, grade, codec and alternative changes.
        self.assertEqual(self.data['records'], expected_records())
        self.assertEqual(set(self.data), {'synthetic', 'representation_grade', 'candidate_grade',
                         'physical_qualification', 'records', 'unknowns', 'examples'})

    def test_each_record_identity_axis(self):
        # Each identity axis of each fixture record is compared on its own with the independent literals, so a
        # change to any single family/variant/direction/service/operation/alternative value fails with that axis
        # named. The four identities stay pairwise distinct, and the page's first field table names the same
        # family and direction in the same row order as the fixture.
        expected = expected_records()
        self.assertEqual(len(self.data['records']), len(expected))
        for row, (record, want) in enumerate(zip(self.data['records'], expected)):
            for axis in AXES:
                with self.subTest(row=row, axis=axis):
                    self.assertIn(axis, record)
                    self.assertEqual(record[axis], want[axis])
        identities = [tuple(json.dumps(record[axis], sort_keys=True) for axis in AXES)
                      for record in self.data['records']]
        self.assertEqual(len(set(identities)), len(identities))
        page_rows = table(self.page, '## Candidate fields', 0)
        self.assertEqual([(row[0], row[1]) for row in page_rows],
                         [(record['family'], record['direction']) for record in self.data['records']])

    def test_partial_identity_separate_and_no_zero_extent(self):
        positive = self.data['records'][3]
        self.assertEqual(positive['constants'], [])
        for row in self.data['records'][2:]:
            self.assertNotIn('data', row)
            self.assertNotIn('extent', row)
            self.assertNotIn('body_extent', row)
            self.assertIsNone(row['service'])
            self.assertIsNone(row['operation'])
        self.assertNotEqual(self.data['records'][1], positive)

    def test_opaque_data_and_destination(self):
        self.assertEqual(self.data['examples']['empty_data'], [])
        self.assertEqual(self.data['examples']['opaque_data'], [181, 24, 0, 245])
        for record in self.data['records'][:2]:
            self.assertEqual(record['data']['minimum'], 0)
            self.assertEqual(record['data']['abstract_maximum'], 65535)
            for unset in ('encoding', 'width', 'byte_order', 'conversion', 'wire_capacity'):
                self.assertNotIn(unset, record['data'])
        self.assertEqual(self.data['records'][0]['destination'],
                         {'logical': 2, 'type': 'u8', 'minimum': 0, 'maximum': 255, 'default': 8})

    def test_grades_and_unknowns(self):
        self.assertIs(self.data['synthetic'], True)
        self.assertEqual(self.data['representation_grade'], 'Proven')
        self.assertEqual(self.data['candidate_grade'], 'Hypothesis')
        self.assertEqual(self.data['physical_qualification'], 'Unknown')
        self.assertEqual(self.data['unknowns'], UNKNOWN)

    def test_page_field_tables(self):
        self.assertEqual(table(self.page, '## Candidate fields', 0), [
            ('B517', 'request', 'B5/17', 'B5 at 0; 17 at 1; destination at 2; opaque data at 3 through end-of-PDU', 'Hypothesis'),
            ('B517', 'positive', 'B5/18', 'B5 at 0; 18 at 1; opaque data at 2 through end-of-PDU', 'Hypothesis'),
            ('B518', 'request', 'Unknown', 'no constants established; body extent absent', 'Hypothesis'),
            ('B518', 'positive', 'Unknown', 'no constants established; body extent absent', 'Hypothesis')])
        self.assertEqual(table(self.page, '## Candidate fields', 1), [
            ('B517 destination', 'raw u8 0..255', '8', 'raw destination; installed address Unknown', 'Hypothesis'),
            ('B517 request data', '0..65535 bytes, through end-of-PDU', 'absent', 'opaque; abstract maximum only', 'Hypothesis'),
            ('B517 positive data', '0..65535 bytes, through end-of-PDU', 'absent', 'opaque; abstract maximum only', 'Hypothesis')])

    def test_page_limits_table_and_no_local_policy(self):
        self.assertEqual(table(self.page, '## Evidence and limits'), [(key, 'Unknown') for key in UNKNOWN])
        self.assertNotIn('## Policy', self.page)
        self.assertNotIn('Predicate', self.page)
        self.assertNotIn('policy', self.data)
        self.assertNotIn('adaptation', self.data)

    def test_page_scoped_claims(self):
        normalized = ' '.join(self.page.split())
        for claim in (
            'B518 is recorded as a separate declaration from the B517 positive form; '
            'whether they describe the same service is Unknown.',
            'Every row is **Hypothesis**.',
            'An absent body extent is **Unknown**, not zero.',
            'Unset encoding, width and byte order remain absent.',
            'Each stated constant is eight bits.',
            "B518's name adds no encoded subgroup 18, operation, body, CRC, success predicate or one-byte physical packet.",
            'Default 8 is not an installed address.',
            'The abstract maximum 65535 is neither a scalar codec nor a demonstrated transport capacity.',
            'Opaque bytes receive no scalar conversion.',
            'Empty opaque data remains empty and proves no successful exchange.',
            'No client or transport is implemented',
            '**Proven** applies only to mechanically checked software representation;',
            'all physical interpretations remain **Hypothesis**.',
        ):
            with self.subTest(claim=claim):
                self.assertIn(claim, normalized)


if __name__ == '__main__':
    unittest.main(verbosity=2)
