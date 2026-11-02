"""Independent checks of the finite B504 representation and API documentation.

These checks do not execute the companion registry implementation.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-b504-circuit-roles.md'
DATA = ROOT / 'protocols/vaillant/fixtures/ak02_b504_circuit_roles.json'
API = ROOT / 'architecture/ak02_b504_circuit_roles_api.md'

# Expected meanings come from the finite contract, independently of the fixture.
RELATIONS = (
    ('0B', 'response', 'reload-delay', 'solar-storage', 'solar-storage-charging'),
    ('0B', 'response', 'parallel-tank-filling', 'mixer', 'global-mixer-circuits'),
    ('2D', 'response', 'room-setpoint', 'inverter-indoor', 'indoor-room-setpoint'),
    ('2D', 'response', 'room-temperature', 'inverter-indoor', 'regulation-input'),
    ('0D', 'request', 'system-support', 'system', 'cooling-support-bit-0'),
    ('0D', 'request', 'system-generation', 'system', 'separate-byte-generation-unknown'),
    ('0D', 'response', 'dhw-request', 'dhw', 'dhw-circuit-request'),
    ('0D', 'response', 'circuit-temperature', 'burner', 'common-sensor-temperature'),
    ('0D', 'response', 'circuit-temperature', 'mixer', 'flow-temperature'),
    ('0D', 'response', 'circuit-temperature', 'dhw', 'tank-temperature'),
    ('0D', 'response', 'desired-temperature', 'burner', 'desired-common-sensor-temperature'),
    ('0D', 'response', 'desired-temperature', 'mixer', 'desired-flow-temperature'),
    ('0D', 'response', 'desired-temperature', 'dhw', 'desired-tank-temperature'),
    ('18', 'response', 'unsuppressed-desired-flow', 'heating', 'unsuppressed-demand'),
    ('18', 'response', 'suppressed-flow', 'tank-charging', 'suppressed-zero'),
    ('01', 'response', 'drying-day', 'circuit', 'nonzero-program-indication'),
    ('33', 'response', 'averaged-outside-temperature', 'system', 'correction-included'),
    ('21', 'response', 'maximum-solar-temperature', 'solar', 'all-solar-circuits'),
    ('21', 'response', 'tank-state', 'solar', 'temperature-to-maximum-percentage'),
    ('21', 'response', 'solar-yield', 'solar', 'collector-to-tank-switching-ratio'),
)
CELL_NAMES = ('burner-temperature', 'mixer-temperature', 'dhw-temperature',
              'burner-desired', 'mixer-desired', 'dhw-desired',
              'unsuppressed-demand', 'suppressed-flow', 'tank-percentage', 'switching-ratio')
CELL_ROLES = ('common-sensor-temperature', 'flow-temperature', 'tank-temperature',
              'desired-common-sensor-temperature', 'desired-flow-temperature',
              'desired-tank-temperature', 'unsuppressed-demand', 'suppressed-zero',
              'temperature-to-maximum-percentage', 'collector-to-tank-switching-ratio')
CELL_CONTEXTS = ('burner', 'mixer', 'dhw', 'burner', 'mixer', 'dhw',
                 'heating', 'tank-charging', 'solar', 'solar')
CELL_FIELDS = ('circuit-temperature',) * 3 + ('desired-temperature',) * 3 + (
    'unsuppressed-desired-flow', 'suppressed-flow', 'tank-state', 'solar-yield')
CELL_OPS = ('0D',) * 6 + ('18', '18', '21', '21')
CELL_TOKENS = (40, 40, 40, 40, 40, 40, 45, 0, 50, 50)
KEY_FIELDS = ('Ab15Family', 'Ab15Variant', 'Ab15Primary', 'Ab15Secondary',
              'Ab15Operation', 'Ab15Direction', 'Ab15Field', 'Ab15Alternative',
              'Ab15Group', 'Ab15InstanceScope', 'Ab15Register')
KEY_TYPES = ('string', 'string', 'uint8', '*uint8', '*uint8', 'string', 'string',
             'string', '*uint8', 'string', '*uint16')
KEY_AXES = ('family', 'variant', 'primary', 'secondary', 'operation', 'direction',
            'field', 'alternative', 'group', 'instance_scope', 'register')
CONTROLS = (
    ('Ab15Family', 'B504', 'B505', 'ignoring family'),
    ('Ab15Variant', 'role-a', 'role-b', 'ignoring variant'),
    ('Ab15Primary', '181', '180', 'ignoring primary'),
    ('Ab15Secondary', '4', '5', 'ignoring secondary'),
    ('Ab15Operation', '13', '24', 'ignoring operation'),
    ('Ab15Direction', 'request', 'response', 'ignoring direction'),
    ('Ab15Field', 'circuit-temperature', 'desired-temperature', 'ignoring field'),
    ('Ab15Alternative', 'none', 'candidate-b', 'ignoring alternative'),
    ('Ab15Group', '1', '2', 'ignoring group'),
    ('Ab15InstanceScope', '00', 'dynamic', 'ignoring instance scope'),
    ('Ab15Register', '1', '2', 'ignoring register'),
    ('Ab15Secondary', 'absent', '0', 'coalescing absent secondary with zero'),
    ('Ab15Operation', 'absent', '0', 'coalescing absent operation with zero'),
    ('Ab15Group', 'absent', '0', 'coalescing absent group with zero'),
    ('Ab15Register', 'absent', '0', 'coalescing absent register with zero'),
)


def tables(text):
    result = []
    for block in text.split('\n\n'):
        lines = block.splitlines()
        if lines and all(line.startswith('|') for line in lines):
            rows = [[cell.strip() for cell in line.strip('|').split('|')] for line in lines]
            result.append((rows[0], rows[2:]))
    return result


class NativeRepresentation(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DATA.read_text())
        self.page = PAGE.read_text()
        self.cases = self.data['cases']

    def test_exact_finite_relations_and_raw_metadata(self):
        expected = [dict(zip(('operation', 'direction', 'field', 'context', 'role'), row),
                         grade='Hypothesis', byte_position='Unknown', width='Unknown',
                         raw_form='independent logical token; wire encoding Unknown')
                    for row in RELATIONS]
        self.assertEqual(self.data['entries'], expected)
        identities = [row[:4] for row in RELATIONS]
        self.assertEqual(len(set(identities)), 20)
        self.assertEqual(set(self.data), {'service', 'primary', 'secondary', 'family',
                                         'provenance', 'grade', 'entries', 'unknown',
                                         'qualification', 'cases'})
        self.assertEqual([self.data[k] for k in ('service', 'primary', 'secondary',
                                               'family', 'provenance', 'grade')],
                         ['B504', 'B5', '04', 'Vaillant B504 family', 'synthetic', 'Hypothesis'])

    def test_temperature_flow_and_solar_cells(self):
        expected = [dict(cell=name, operation=op, field=field, context=context,
                         raw_token=token, role=role, grade='Hypothesis')
                    for name, op, field, context, token, role in
                    zip(CELL_NAMES, CELL_OPS, CELL_FIELDS, CELL_CONTEXTS, CELL_TOKENS, CELL_ROLES)]
        self.assertEqual(self.cases['role_cells'], expected)
        # Equal numeric tokens cannot erase independent semantic cells.
        self.assertEqual(len(set(CELL_ROLES[:3])), 3)
        self.assertEqual(self.cases['role_cells'][6]['raw_token'], 45)
        self.assertEqual(self.cases['role_cells'][7]['raw_token'], 0)
        self.assertNotEqual(self.cases['role_cells'][8]['role'], self.cases['role_cells'][9]['role'])

    def test_each_role_cell_varies_alone(self):
        expected = []
        for index, name in enumerate(CELL_NAMES):
            changed = list(CELL_TOKENS)
            changed[index] = 61 + index
            expected.append(dict(changed_cell=name, before=list(CELL_TOKENS),
                                 after=changed, roles=list(CELL_ROLES)))
        self.assertEqual(self.cases['independent_cells'], expected)
        for index, case in enumerate(self.cases['independent_cells']):
            with self.subTest(cell=CELL_NAMES[index]):
                self.assertEqual([i for i, (a, b) in enumerate(zip(case['before'], case['after']))
                                  if a != b], [index])

    def test_dhw_request_has_no_mixer_or_burner_interpretation(self):
        self.assertEqual(self.cases['dhw_request'], [
            dict(operation='0D', context='dhw', raw_token=1,
                 role='dhw-circuit-request', grade='Hypothesis'),
            dict(operation='0D', context='mixer', raw_token=1,
                 role='no-dhw-interpretation', grade='Hypothesis'),
            dict(operation='0D', context='burner', raw_token=1,
                 role='no-dhw-interpretation', grade='Hypothesis')])

    def test_cooling_support_and_generation_are_separate(self):
        self.assertEqual(self.cases['support_generation'], dict(
            operation='0D', direction='request', support_token=1, support_bit=0,
            support_role='system-cooling-support', generation_token=7,
            generation_role='system-generation', generation_value_meaning='Unknown',
            different_byte=True, grade='Hypothesis'))
        self.assertEqual(self.cases['support_generation_independence'], [
            dict(support_token=0, generation_token=7),
            dict(support_token=1, generation_token=8)])
        self.assertIs(self.cases['support_generation']['different_byte'], True)

    def test_nonzero_drying_and_corrected_average_without_arithmetic(self):
        self.assertEqual(self.cases['drying_day'], [
            dict(operation='01', raw_token=0, nonzero_program_indication=False, grade='Hypothesis'),
            dict(operation='01', raw_token=1, nonzero_program_indication=True, grade='Hypothesis')])
        self.assertIs(self.cases['drying_day'][0]['nonzero_program_indication'], False)
        self.assertIs(self.cases['drying_day'][1]['nonzero_program_indication'], True)
        self.assertEqual(self.cases['outside_average'], dict(
            operation='33', raw_token=17, configured_correction_token=3,
            correction_included=True, arithmetic='Unknown', grade='Hypothesis'))
        self.assertIs(self.cases['outside_average']['correction_included'], True)
        self.assertEqual(self.cases['outside_average_independence'], [
            dict(raw_token=18, configured_correction_token=3,
                 correction_included=True, arithmetic='Unknown'),
            dict(raw_token=17, configured_correction_token=4,
                 correction_included=True, arithmetic='Unknown')])

    def test_scopes_and_regulation_input(self):
        controls = (
            ('0B', 'reload-delay', 'solar-storage', 'solar-storage-charging', 2),
            ('0B', 'parallel-tank-filling', 'mixer', 'global-mixer-circuits', 1),
            ('2D', 'room-setpoint', 'inverter-indoor', 'indoor-room-setpoint', 21),
            ('2D', 'room-temperature', 'inverter-indoor', 'regulation-input', 20),
            ('21', 'maximum-solar-temperature', 'solar', 'all-solar-circuits', 60))
        self.assertEqual(self.cases['scopes'], [dict(operation=op, field=field, context=context,
                         role=role, raw_token=token, grade='Hypothesis')
                         for op, field, context, role, token in controls])
        expected = []
        for index, field in enumerate(('reload-delay', 'parallel-tank-filling',
                                       'room-setpoint', 'room-temperature',
                                       'maximum-solar-temperature')):
            changed = [2, 1, 21, 20, 60]
            changed[index] = 70 + index
            expected.append(dict(changed_field=field, before=[2, 1, 21, 20, 60],
                                 after=changed, roles=['solar-storage-charging',
                                 'global-mixer-circuits', 'indoor-room-setpoint',
                                 'regulation-input', 'all-solar-circuits']))
        self.assertEqual(self.cases['scope_independence'], expected)

    def test_unknown_boundaries_qualification_and_raw_fallback(self):
        self.assertEqual(self.data['unknown'], dict.fromkeys((
            'byte_positions', 'widths', 'generation_values', 'suppression_algorithm',
            'tank_percentage_formula', 'switching_ratio_formula', 'wire_encoding',
            'unit_encoding'), 'Unknown'))
        self.assertEqual(self.data['qualification'], dict.fromkeys((
            'native_support', 'physical_effects', 'persistence', 'delivery'), 'Unknown'))
        self.assertEqual(self.cases['raw_fallback'], dict(operation='0D',
            field='circuit-temperature', context='unclassified', raw_token=40,
            role='Unknown', grade='Unknown'))
        self.assertEqual(set(self.cases), {'role_cells', 'independent_cells', 'dhw_request',
                         'drying_day', 'outside_average', 'support_generation',
                         'support_generation_independence', 'scopes', 'raw_fallback',
                         'scope_independence', 'outside_average_independence'})

    def test_native_tables_have_independent_expected_results(self):
        parsed = tables(self.page)
        self.assertEqual(len(parsed), 4)
        self.assertEqual(parsed[0], (['Operation', 'Direction', 'Field', 'Context',
                                     'Candidate role', 'Grade'],
                                    [list(row) + ['Hypothesis'] for row in RELATIONS]))
        self.assertEqual(parsed[1], (['Cell', 'Operation', 'Context', 'Raw token',
                                     'Candidate role', 'Grade'],
            [[name, op, context, str(token), role, 'Hypothesis']
             for name, op, context, token, role in
             zip(CELL_NAMES, CELL_OPS, CELL_CONTEXTS, CELL_TOKENS, CELL_ROLES)]))
        self.assertEqual(parsed[2], (['Operation', 'Context or field', 'Raw token',
                                     'Candidate result', 'Grade'], [
            ['0D', 'dhw', '1', 'dhw-circuit-request', 'Hypothesis'],
            ['0D', 'mixer', '1', 'no-dhw-interpretation', 'Hypothesis'],
            ['0D', 'burner', '1', 'no-dhw-interpretation', 'Hypothesis'],
            ['01', 'drying-day', '0', 'no-nonzero-program-indication', 'Hypothesis'],
            ['01', 'drying-day', '1', 'nonzero-program-indication', 'Hypothesis'],
            ['33', 'averaged-outside-temperature', '17', 'correction-included; arithmetic Unknown', 'Hypothesis'],
            ['21', 'tank-state', '50', 'temperature-to-maximum-percentage; formula Unknown', 'Hypothesis'],
            ['21', 'solar-yield', '50', 'collector-to-tank-switching-ratio; formula Unknown', 'Hypothesis']]))
        self.assertEqual(parsed[3], (['Qualification', 'Value'], [
            ['Native support', 'Unknown'], ['Physical effects', 'Unknown'],
            ['Persistence', 'Unknown'], ['Delivery', 'Unknown']]))

    def test_native_prose_keeps_evidence_and_formula_limits(self):
        text = ' '.join(self.page.split())
        for phrase in ('request bit 0 expresses system cooling support',
                       'A different byte carries system generation',
                       'DHW interpretation only in a DHW circuit',
                       'averaging window and correction arithmetic are Unknown',
                       'Exact formulas are Unknown', 'No suppression algorithm is selected',
                       'No OP16 conversion, OP20/21 sentinel table',
                       'solar scalar enumeration or preheat-domain table is added',
                       'Synthetic', 'no native capture'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


class ArchitectureContract(unittest.TestCase):
    def setUp(self):
        self.text = API.read_text()
        self.prose = ' '.join(self.text.split())

    def test_exact_api_signatures_and_all_eleven_key_axes(self):
        self.assertEqual(re.findall(r'^func .+$', self.text, re.M), [
            'func Ab15Entries() (json.RawMessage, error)',
            'func Ab15Lookup(Ab15Key) (json.RawMessage, bool, error)'])
        parsed = tables(self.text)
        self.assertEqual(len(parsed), 2)
        rules = ('exact family', 'exact variant', 'exact primary',
                 'absent differs from zero', 'absent differs from zero',
                 'exact direction', 'exact field', 'exact alternative',
                 'absent differs from zero', 'exact explicit string', 'absent differs from zero')
        self.assertEqual(parsed[0], (['Ab15Key field', 'Go type', 'Identity axis', 'Matching rule'],
            [list(row) for row in zip(KEY_FIELDS, KEY_TYPES, KEY_AXES, rules)]))
        self.assertIn('Package `vaillant`', self.text)

    def test_documented_identity_controls_independent_expectations(self):
        self.assertEqual(tables(self.text)[1], (
            ['Axis', 'Left control', 'Right control', 'Mutation detected'],
            [list(row) for row in CONTROLS]))
        self.assertEqual(len(CONTROLS), 15)
        self.assertEqual({row[0] for row in CONTROLS}, set(KEY_FIELDS))
        for phrase in ('changes only the named axis', 'Both keys are valid typed controls',
                       'each exact lookup selects its own whole row',
                       'With only the left row present, the right key is a miss',
                       'not observed native traffic or executed registry qualification'):
            self.assertIn(phrase, self.prose)

    def test_whole_rows_fail_closed_copies_and_last_known_good(self):
        for phrase in ('returns a JSON array', 'returns exactly one whole row',
                       'missing exact key returns no row, `false` and no error',
                       'Invalid embedded JSON or duplicate keys produce an error',
                       'Validation of the entire embedded array precedes admission',
                       'Errors return no entries buffer or lookup row',
                       'lookup also returns `false`', 'No wildcard or nearest-key lookup',
                       'All eleven axes match independently',
                       'No cross-family, variant, direction, field or alternative fallback',
                       'Non-applicable string axes use an explicit `none` token',
                       'explicit string such as `00` or `dynamic`',
                       '`ab15-` ticket-prefixed ID', 'complete identity',
                       'candidate grade `Hypothesis`', 'retained `raw_form`',
                       'embeds its own JSON', 'Identity uniqueness is validated',
                       'independent deep byte copy', 'including calls through the other function',
                       'partial last-known-good state preserves its raw evidence and provenance',
                       'failed new data cannot replace it or be admitted as fresh',
                       'prose and synthetic data checks alone do not establish production behavior'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.prose)

    def test_api_finite_unknowns_and_compatibility(self):
        for phrase in ('byte positions', 'widths', 'generation values', 'suppression algorithm',
                       'percentage formula', 'switching-ratio formula', 'remain Unknown',
                       'No OP16 conversion, OP20/21 sentinel table',
                       'solar scalar enumeration or preheat-domain table',
                       'retains correction-included metadata',
                       'Existing catalog/provider APIs and routability remain unchanged',
                       'eBUS MCP compatibility and GraphQL parity remain unchanged',
                       'no transmit route, scan-default change, active executor',
                       'automatic native qualification', 'Nothing is stable before Helianthus 1.0',
                       'AK01 must merge before AK02',
                       'no dependency from the registry back to this page',
                       'Their merge does not establish native qualification'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.prose)


class PublicationBoundary(unittest.TestCase):
    def test_native_separation_links_and_no_fingerprints(self):
        native = PAGE.read_text() + DATA.read_text()
        self.assertNotRegex(native, r'\b(?:Ab15\w*|GraphQL|MCP|Helianthus|gateway|json.RawMessage)\b')
        for page in (PAGE, API):
            for target in re.findall(r'\]\(([^)]+)\)', page.read_text()):
                self.assertNotIn(':', target)
                self.assertTrue((page.parent / target.split('#')[0]).is_file(), target)
        for path in (PAGE, DATA, API, Path(__file__)):
            self.assertNotRegex(path.read_text(), r'(?<!\w)[a-fA-F0-9]{40,64}(?!\w)')


if __name__ == '__main__':
    unittest.main(verbosity=2)
