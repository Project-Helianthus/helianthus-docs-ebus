"""Synthetic declaration checks; no transport or physical qualification."""
import copy
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
         'constants': [constant(0, 181)]},
        {'family': 'B518', 'variant': None, 'direction': 'positive', 'service': None,
         'operation': None, 'alternative': 'partial-identity-positive', 'grade': 'Hypothesis',
         'constants': [constant(0, 245)]},
    ]


POLICY = {'grade': 'Hypothesis', 'destination_domain': [1, 254],
          'inner_destination': 'original destination', 'inner_data': 'original PDU',
          'returned_context': 'original service', 'local_codes': [10, 6, 7],
          'remote_feedback': 'separate', 'implemented': False}
ADAPTATION = {'grade': 'Hypothesis', 'ready': 3, 'final_option': 'nonzero',
              'length_index': 4, 'length_bias': 6, 'request_service': [181, 23],
              'input_service': [181, 24], 'universal_prefix_removal': False}


def equation(data, declaration):
    index = declaration['length_index']
    if len(data) <= index:
        return None
    return data[index] + declaration['length_bias'] == len(data)


def eligible(data, declaration, ready=3, option=1, request=(181, 23), incoming=(181, 24)):
    """Synthetic conjunction only; establishes no native adaptation."""
    return (equation(data, declaration) is True and ready == declaration['ready']
            and declaration['final_option'] == 'nonzero' and option != 0
            and list(request) == declaration['request_service']
            and list(incoming) == declaration['input_service'])


def table(page, heading):
    section = page.split(heading + '\n', 1)[1].split('\n## ', 1)[0]
    rows = [tuple(cell.strip() for cell in line.strip('|').split('|'))
            for line in section.splitlines() if line.startswith('|')]
    headers = {
        '## Candidate fields': ('Family', 'Direction', 'Service declaration', 'Logical fields', 'Grade'),
        '## Policy and distinct adaptation alternative': ('Policy', 'Declared value', 'Grade'),
        '## Evidence and limits': ('Unresolved property', 'Grade'),
    }
    if rows[0] != headers[heading] or rows[1] != ('---',) * len(headers[heading]):
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
                         'physical_qualification', 'records', 'policy', 'adaptation', 'unknowns', 'examples'})

    def test_each_record_identity_axis(self):
        # Valid control plus independent family/variant/direction/service/operation/alternative changes.
        self.assertEqual(self.data['records'], expected_records())
        for row in range(4):
            for axis in AXES:
                with self.subTest(row=row, axis=axis):
                    changed = copy.deepcopy(self.data['records'])
                    changed[row][axis] = 'synthetic-other'
                    self.assertNotEqual(changed, expected_records())
            if self.data['records'][row]['service'] is not None:
                for component in (0, 1):
                    with self.subTest(row=row, service_component=component):
                        changed = copy.deepcopy(self.data['records'])
                        changed[row]['service'][component] += 1
                        self.assertNotEqual(changed, expected_records())

    def test_partial_identity_not_alias_or_zero_extent(self):
        positive = self.data['records'][3]
        self.assertEqual(positive['constants'], [{'logical': 0, 'value': 245, 'bits': 8}])
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

    def test_policy_and_local_remote_separation(self):
        self.assertEqual(self.data['policy'], POLICY)
        self.assertFalse(self.data['policy']['implemented'])

    def test_adaptation_all_predicates_independently(self):
        rule = self.data['adaptation']
        self.assertEqual(rule, ADAPTATION)
        control = self.data['examples']['length_control']
        self.assertEqual(control, [0, 0, 0, 0, 4, 0, 0, 0, 0, 0])
        self.assertTrue(eligible(control, rule))
        for kwargs in ({'ready': 2}, {'option': 0}, {'request': (180, 23)},
                       {'request': (181, 22)}, {'incoming': (180, 24)},
                       {'incoming': (181, 25)}):
            with self.subTest(kwargs=kwargs):
                self.assertFalse(eligible(control, rule, **kwargs))
        changed = self.data['examples']['length_changed']
        self.assertEqual(changed, [0, 0, 0, 0, 5, 0, 0, 0, 0, 0])
        self.assertFalse(equation(changed, rule))
        self.assertFalse(eligible(changed, rule))
        self.assertFalse(eligible(control + [0], rule))
        for size in range(5):
            self.assertIsNone(equation([0] * size, rule))
            self.assertFalse(eligible([0] * size, rule))

    def test_grades_and_unknowns(self):
        self.assertIs(self.data['synthetic'], True)
        self.assertEqual(self.data['representation_grade'], 'Proven')
        self.assertEqual(self.data['candidate_grade'], 'Hypothesis')
        self.assertEqual(self.data['physical_qualification'], 'Unknown')
        self.assertEqual(self.data['unknowns'], UNKNOWN)

    def test_page_field_tables(self):
        self.assertEqual(table(self.page, '## Candidate fields'), [
            ('B517', 'request', 'B5/17', 'B5 at 0; 17 at 1; destination at 2; opaque data at 3 through end-of-PDU', 'Hypothesis'),
            ('B517', 'positive', 'B5/18', 'B5 at 0; 18 at 1; opaque data at 2 through end-of-PDU', 'Hypothesis'),
            ('B518', 'request', 'Unknown', 'B5 only at 0; body extent absent', 'Hypothesis'),
            ('B518', 'positive', 'Unknown', 'F5 only at 0; body extent absent', 'Hypothesis'),
            ('Field', 'Domain or extent', 'Default', 'Interpretation', 'Grade'),
            ('---', '---', '---', '---', '---'),
            ('B517 destination', 'raw u8 0..255', '8', 'raw destination; installed address Unknown', 'Hypothesis'),
            ('B517 request data', '0..65535 bytes, through end-of-PDU', 'absent', 'opaque; abstract maximum only', 'Hypothesis'),
            ('B517 positive data', '0..65535 bytes, through end-of-PDU', 'absent', 'opaque; abstract maximum only', 'Hypothesis')])

    def test_page_policy_tables(self):
        self.assertEqual(table(self.page, '## Policy and distinct adaptation alternative'), [
            ('tunnel destination domain', '1..254', 'Hypothesis'),
            ('inner destination', 'original destination', 'Hypothesis'),
            ('inner opaque data', 'original PDU', 'Hypothesis'),
            ('returned data context', 'original service', 'Hypothesis'),
            ('local result codes', 'raw 10, 6, 7; meanings Unknown', 'Hypothesis'),
            ('remote feedback', 'separate from local result codes', 'Hypothesis'),
            ('Predicate', 'Required value', 'Grade'), ('---', '---', '---'),
            ('ready-state', '3', 'Hypothesis'), ('final option', 'nonzero', 'Hypothesis'),
            ('length equation', 'input byte 4 + 6 equals available length', 'Hypothesis'),
            ('request service', 'B5/17', 'Hypothesis'), ('input service', 'B5/18', 'Hypothesis')])
        self.assertEqual(table(self.page, '## Evidence and limits'), [(key, 'Unknown') for key in UNKNOWN])

    def test_page_scoped_claims(self):
        normalized = ' '.join(self.page.split())
        for claim in (
            'B518 is not an alias for the B517 positive form.',
            'Every row is **Hypothesis**.',
            'An absent body extent is **Unknown**, not zero.',
            'Unset encoding, width and byte order remain absent.',
            'Each stated constant is eight bits.',
            "B518's name adds no encoded subgroup 18, operation, body, CRC, success predicate or one-byte physical packet.",
            'Default 8 is not an installed address.',
            'The abstract maximum 65535 is neither a scalar codec nor a demonstrated transport capacity.',
            'Opaque bytes receive no scalar conversion.',
            'Empty opaque data remains empty/partial;',
            'incomplete evidence does not erase partial last-known-good state',
            'No client or transport is implemented',
            'It is not a universal prefix-removal rule.',
            'Changing byte4 to 5 fails the equation and does not establish a valid alternative.',
            '**Proven** applies only to mechanically checked software representation;',
            'all physical interpretations remain **Hypothesis**.',
            'No runtime capability, transmit route, automatic native qualification or write admission follows.',
            'Unsupported or incomplete evidence keeps admission withheld.',
        ):
            with self.subTest(claim=claim):
                self.assertIn(claim, normalized)


if __name__ == '__main__':
    unittest.main(verbosity=2)
