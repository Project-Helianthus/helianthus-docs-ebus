"""Documentation/scenario checks, not an implementation of the proposed Go API."""
import copy
import json
import re
from pathlib import Path
import unittest

ab13ap13_root = Path(__file__).resolve().parents[1]
ab13ap13_selectors = [
    [181, 18, 15, 'request', 'valve-io'],
    [181, 18, 15, 'positive', 'valve-io'],
    [181, 18, 16, 'request', 'board-io'],
    [181, 18, 16, 'positive', 'board-io'],
]
ab13ap13_flags = {
    'output': ['output0', 'output1'],
    'actuator1': ['cooling-valve', 'passive-mixer1', 'passive-mixer2',
                  'cooling-active', 'well-pump', 'backup-safety', 'backup1', 'backup2'],
    'actuator2': ['backup3', 'external-valve', 'external-backup'],
    'status': ['anode1', 'anode2', 'smart-grid', 'well', 'safety-limiter', 'safety'],
}
ab13ap13_enums = {
    'valve': {0: 'off', 1: 'CH', 2: 'DHW'},
    'input': {0: 'multipurpose', 1: 'utility-contact'},
    'backup': {0: 'off', 1: 'step1', 2: 'step2', 3: 'step3', 255: 'replacement'},
    'board': {0: 'opaque-code-0', 1: 'opaque-code-1', 2: 'opaque-code-2',
              3: 'opaque-code-3', 11: 'opaque-code-11', 12: 'opaque-code-12'},
}
ab13ap13_expected_fields = [
    ['valve-io', 'request', 'output', 1, 'flags', '0:output0,1:output1', '2..7'],
    ['valve-io', 'request', 'valve', 1, 'enum', '0:off,1:CH,2:DHW', '-'],
    ['valve-io', 'positive', 'temperature1', 2, 'temperature', 'LEs16/16;[0,128]:replacement', '-'],
    ['valve-io', 'positive', 'temperature2', 2, 'temperature', 'LEs16/16;[0,128]:replacement', '-'],
    ['valve-io', 'positive', 'input', 1, 'enum', '0:multipurpose,1:utility-contact', '-'],
    ['valve-io', 'positive', 'pressure', 1, 'pressure', 'u8/10;range=0..25.5;default=255.0;conflict=true', '-'],
    ['valve-io', 'positive', 'backup', 1, 'enum', '0:off,1:step1,2:step2,3:step3,255:replacement', '-'],
    ['board-io', 'request', 'actuator1', 1, 'flags', '0:cooling-valve,1:passive-mixer1,2:passive-mixer2,3:cooling-active,4:well-pump,5:backup-safety,6:backup1,7:backup2', '-'],
    ['board-io', 'request', 'actuator2', 1, 'flags', '0:backup3,1:external-valve,2:external-backup', '3..7'],
    ['board-io', 'request', 'inverse', 2, 'opaque', 'order=Unknown;algorithm=Unknown', '-'],
    ['board-io', 'positive', 'status', 1, 'flags', '0:anode1,1:anode2,2:smart-grid,3:well,4:safety-limiter,5:safety', '6..7'],
    ['board-io', 'positive', 'phase1', 1, 'phase', 'raw-u8-percent;single-phase~50;three-phase~0/33/66/100;selection=Unknown', '-'],
    ['board-io', 'positive', 'phase2', 1, 'phase', 'raw-u8-percent;single-phase~50;three-phase~0/33/66/100;selection=Unknown', '-'],
    *[['board-io', 'positive', f'adc{ab13ap13_i}', 2, 'adc', 'LEu16;range=0..65535', '-']
      for ab13ap13_i in range(6)],
    ['board-io', 'positive', 'board', 1, 'enum', '0:opaque-code-0,1:opaque-code-1,2:opaque-code-2,3:opaque-code-3,11:opaque-code-11,12:opaque-code-12', '-'],
]
ab13ap13_expected_rules = [
    ['signature', 'package vaillant; Ab13Ap13Evaluate(ab13ap13Input json.RawMessage) (json.RawMessage, error)'],
    ['input', 'object; context:object; fields:object; arguments?:object'],
    ['arguments', 'no declared typed arguments or required arguments for these views; opaque extra keys preserved'],
    ['bytes', 'arrays of integral numbers 0..255; no Boolean, null, string, fraction, float-syntax literal such as 0.0, or coercion'],
    ['validation', 'malformed JSON, duplicate keys anywhere, wrong container/byte kinds or out-of-range bytes: error; no successful result'],
    ['width', 'missing, short or overlong named arrays: incomplete; preserve raw and independent complete siblings'],
    ['selector', 'exact typed tuple; unsupported or missing/null selector: Unknown, raw-only, no formulas'],
    ['context', 'preserve opaque family, variant and other keys; absent, null, zero and false remain distinct'],
    ['result', 'context; raw; arguments if supplied; state; fields; physical=Unknown; qualified=false'],
    ['field-result', 'raw if present; state; grade=Hypothesis; applicable number,label,flags,reserved,unmodeled,candidate_domain,alternatives'],
    ['state', 'partial if supported and any required field incomplete; otherwise complete; unsupported Unknown'],
    ['grade', 'family/behavior Hypothesis; exact arithmetic calculation=Proven; physical Unknown; qualified=false'],
    ['unknown', 'missing/unmapped/incomplete quantities have no number or label; unresolved candidate sibling does not force partial'],
    ['domain', 'explicit calculation outside candidate domain is retained with candidate_domain=false'],
    ['copy', 'context, fields, arguments and returned nested storage detached from input, other results and later calls'],
    ['roundtrip', 'JSON round trips preserve context/raw/state and absent/null/zero distinctions'],
    ['isolation', 'pure library; no initialization side effect, persistent cache, generic catalog, listing API or runtime caller'],
    ['integers', 'u8=0..255; u16=0..65535; u32=0..4294967295; integral JSON numbers only when typed; never Boolean'],
    ['defaults', 'no missing data filled by 0 or false; no relay vector declared in selected views'],
    ['native', 'selector is software input; no wire offsets, automatic phase selection, ADC10bit narrowing or native qualification'],
]

ab13ap13_claims = [
    'LEs16 means `b0+256*b1`, subtract 65536 if at least 32768, then divide by 16 to obtain Celsius',
    'The two temperatures branch on bytes `[0,128]` (word 0x8000) **before** signed conversion',
    'Replacement is a label, not a numeric temperature',
    'Pressure is exactly byte/10 bar across 0..25.5',
    'Raw FF calculates 25.5, never 255.0',
    'do not truncate the candidate default to byte 255 and call it an agreement',
    'Pressure arithmetic has `calculation="Proven"`, while its family grade stays Hypothesis',
    'Valid byte pressure calculations have `candidate_domain=true`; the conflicting default does not',
    'Temperatures and ADC calculations likewise carry `calculation="Proven"` without upgrading their family grade',
    'Backup FF is replacement; FE is unmapped',
    '`[18,52]` remains those two bytes, with `unmodeled=true`: no complement, endian interpretation',
    'Phase numbers are raw u8 percent values',
    'approximate single-phase 50 and three-phase 0/33/66/100 metadata with no tolerance and no selected kind',
    'Raw 50 and 33 never choose a phase type',
    'Board codes are named opaque codes; 13 is unmapped',
    'ADC FFFF is 65535, never clamped to 1023 from another family',
    'Unmapped enum values retain raw with `unmodeled=true`, no number or label',
]
ab13ap13_mutations = [
    ('"default_agrees":false', '"default_agrees":true'),
    ('Raw FF calculates 25.5', 'Raw FF calculates 255.0'),
    ('never clamped to 1023', 'clamped to 1023'),
    ('no tolerance and no selected kind', 'a tolerance and a selected kind'),
    ('Backup FF is replacement; FE is unmapped', 'Backup FE is replacement; FF is unmapped'),
    ('no complement', 'complement applied'),
    ('Valid byte pressure calculations have `candidate_domain=true`', 'Valid byte pressure calculations have `candidate_domain=false`'),
    ('calculation="Proven"', 'calculation="Hypothesis"'),
    ('13 is unmapped', '13 is mapped'),
    ('subtract 65536 if at least 32768', 'subtract 65536 if at least 1023'),
    ('divide by 16', 'divide by 10'),
    ('[0,128]', '[0,127]'),
    ('"default_in_byte_domain":false', '"default_in_byte_domain":true'),
]


def ab13ap13_prose_problems(ab13ap13_text):
    ab13ap13_flat = re.sub(r'\s+', ' ', ab13ap13_text)
    ab13ap13_problems = [ab13ap13_c for ab13ap13_c in ab13ap13_claims if ab13ap13_c not in ab13ap13_flat]
    ab13ap13_found = re.search(r'alternatives=(\{.*?\})', ab13ap13_flat)
    if not ab13ap13_found:
        ab13ap13_problems.append('pressure alternatives object')
    else:
        try:
            ab13ap13_alt = json.loads(ab13ap13_found.group(1).replace('} ', '}'))
        except ValueError:
            ab13ap13_alt = None
        if ab13ap13_alt != {'candidate_default': 255.0, 'default_in_byte_domain': False, 'default_agrees': False}:
            ab13ap13_problems.append('pressure alternatives value')
    return ab13ap13_problems


def ab13ap13_table(ab13ap13_text, ab13ap13_header):
    ab13ap13_tail = ab13ap13_text.split(ab13ap13_header + '\n', 1)[1]
    ab13ap13_lines = ab13ap13_tail.splitlines()[1:]
    ab13ap13_rows = []
    for ab13ap13_line in ab13ap13_lines:
        if not ab13ap13_line.startswith('|'):
            break
        ab13ap13_rows.append([ab13ap13_cell.strip() for ab13ap13_cell in ab13ap13_line.strip('|').split('|')])
    return ab13ap13_rows


class TestAb13Ap13(unittest.TestCase):
    def setUp(self):
        self.ab13ap13_fixture = json.loads((ab13ap13_root / 'architecture/fixtures/ap14_b512_heatpump_io.json').read_text())
        self.ab13ap13_page = (ab13ap13_root / 'architecture/ap14_b512_heatpump_io.md').read_text()

    def test_ab13ap13_tables_and_signature(self):
        self.assertEqual(self.ab13ap13_fixture['selectors'], ab13ap13_selectors)
        self.assertEqual(self.ab13ap13_fixture['field_table'], ab13ap13_expected_fields)
        self.assertEqual(self.ab13ap13_fixture['rules'], ab13ap13_expected_rules)
        for ab13ap13_key, ab13ap13_header, ab13ap13_expected in [
            ('selectors', '| primary | secondary | operation | direction | view |', ab13ap13_selectors),
            ('fields', '| view | direction | field | width | kind | rule | reserved |', ab13ap13_expected_fields),
            ('rules', '| key | contract |', ab13ap13_expected_rules),
        ]:
            with self.subTest(table=ab13ap13_key):
                self.assertEqual(ab13ap13_table(self.ab13ap13_page, ab13ap13_header),
                                 [[str(ab13ap13_cell) for ab13ap13_cell in ab13ap13_row] for ab13ap13_row in ab13ap13_expected])
        self.assertEqual(self.ab13ap13_fixture['grades'], {
            'grade': 'Hypothesis', 'calculation': 'Proven', 'physical': 'Unknown', 'qualified': False})
        self.assertIs(self.ab13ap13_fixture['synthetic'], True)

    def test_ab13ap13_each_scenario_independent_arithmetic(self):
        ab13ap13_widths = {ab13ap13_row[2]: ab13ap13_row[3] for ab13ap13_row in ab13ap13_expected_fields}
        ab13ap13_seen = {ab13ap13_name: set() for ab13ap13_name in ab13ap13_widths}
        ab13ap13_ids = set()
        for ab13ap13_case in self.ab13ap13_fixture['cases']:
            ab13ap13_name, ab13ap13_raw = ab13ap13_case['field'], ab13ap13_case['raw']
            with self.subTest(case=ab13ap13_case['id']):
                self.assertTrue(ab13ap13_case['id'].startswith('ab13ap13'))
                self.assertNotIn(ab13ap13_case['id'], ab13ap13_ids)
                ab13ap13_ids.add(ab13ap13_case['id'])
                ab13ap13_seen[ab13ap13_name].add(None if ab13ap13_raw is None else tuple(ab13ap13_raw))
                ab13ap13_complete = ab13ap13_raw is not None and len(ab13ap13_raw) == ab13ap13_widths[ab13ap13_name]
                self.assertEqual(ab13ap13_case['state'], 'complete' if ab13ap13_complete else 'incomplete')
                ab13ap13_number = ab13ap13_label = ab13ap13_flag_result = ab13ap13_reserved = None
                if ab13ap13_complete:
                    if ab13ap13_name in ab13ap13_flags:
                        ab13ap13_flag_result = {ab13ap13_flag: bool((ab13ap13_raw[0] // (2 ** ab13ap13_bit)) % 2)
                                               for ab13ap13_bit, ab13ap13_flag in enumerate(ab13ap13_flags[ab13ap13_name])}
                        ab13ap13_reserved = (ab13ap13_raw[0] >> len(ab13ap13_flag_result)) << len(ab13ap13_flag_result)
                    elif ab13ap13_name in ab13ap13_enums:
                        ab13ap13_label = ab13ap13_enums[ab13ap13_name].get(ab13ap13_raw[0])
                    elif ab13ap13_name.startswith('temperature'):
                        if ab13ap13_raw == [0, 128]:
                            ab13ap13_label = 'replacement'
                        else:
                            ab13ap13_number = int.from_bytes(bytes(ab13ap13_raw), 'little', signed=True) / 16
                    elif ab13ap13_name.startswith('adc'):
                        ab13ap13_number = int.from_bytes(bytes(ab13ap13_raw), 'little')
                    elif ab13ap13_name == 'pressure':
                        ab13ap13_number = ab13ap13_raw[0] * 0.1
                    elif ab13ap13_name.startswith('phase'):
                        ab13ap13_number = ab13ap13_raw[0]
                for ab13ap13_key, ab13ap13_expected in [('label', ab13ap13_label), ('flags', ab13ap13_flag_result), ('reserved', ab13ap13_reserved)]:
                    self.assertEqual(ab13ap13_case[ab13ap13_key], ab13ap13_expected)
                if ab13ap13_number is None:
                    self.assertIsNone(ab13ap13_case['number'])
                else:
                    self.assertAlmostEqual(ab13ap13_case['number'], ab13ap13_number)
        for ab13ap13_name, ab13ap13_values in ab13ap13_seen.items():
            with self.subTest(coverage=ab13ap13_name):
                self.assertIn(None, ab13ap13_values)
                self.assertIn((), ab13ap13_values)
                self.assertIn((0,) * (ab13ap13_widths[ab13ap13_name] + 1), ab13ap13_values)
                if ab13ap13_name in ab13ap13_flags:
                    for ab13ap13_bit in range(8):
                        self.assertIn((2 ** ab13ap13_bit,), ab13ap13_values)
                if ab13ap13_name in ab13ap13_enums:
                    self.assertTrue({(ab13ap13_i,) for ab13ap13_i in range(256)} <= ab13ap13_values)
                if ab13ap13_name.startswith('adc'):
                    self.assertTrue({(0, 0), (1, 0), (0, 1), (255, 255)} <= ab13ap13_values)
                if ab13ap13_name.startswith('temperature'):
                    self.assertTrue({(0, 128), (240, 255), (0, 0), (1, 128)} <= ab13ap13_values)

    def test_ab13ap13_conflicting_defaults_phase_inverse(self):
        self.assertEqual(self.ab13ap13_fixture['pressure_conflict'], {
            'raw': [255], 'number': 25.5, 'candidate_default': 255.0,
            'default_in_byte_domain': False, 'default_agrees': False})
        self.assertEqual(self.ab13ap13_fixture['phase_metadata'], {
            'single-phase': [50], 'three-phase': [0, 33, 66, 100],
            'approximate': True, 'tolerance': None, 'selected_kind': None})
        ab13ap13_inverse = [ab13ap13_case for ab13ap13_case in self.ab13ap13_fixture['cases']
                            if ab13ap13_case['field'] == 'inverse' and ab13ap13_case['state'] == 'complete']
        self.assertEqual(len(ab13ap13_inverse), 1)
        self.assertEqual(ab13ap13_inverse[0]['raw'], [18, 52])
        self.assertIsNone(ab13ap13_inverse[0]['number'])

    def test_ab13ap13_selector_axes_and_partial_siblings(self):
        self.assertEqual(len(self.ab13ap13_fixture['transitions']), 328)
        ab13ap13_context_values = {ab13ap13_axis: [] for ab13ap13_axis in
                                  ('primary', 'secondary', 'operation', 'direction', 'view', 'family', 'variant', 'opaque')}
        for ab13ap13_case in self.ab13ap13_fixture['transitions']:
            ab13ap13_axis = ab13ap13_case['axis']
            if ab13ap13_axis in ab13ap13_context_values:
                ab13ap13_context_values[ab13ap13_axis].append(
                    json.dumps([ab13ap13_axis in ab13ap13_case['context'], ab13ap13_case['context'].get(ab13ap13_axis)], sort_keys=True))
            ab13ap13_context = ab13ap13_case['context']
            ab13ap13_tuple = [ab13ap13_context.get(ab13ap13_key) for ab13ap13_key in
                              ('primary', 'secondary', 'operation', 'direction', 'view')]
            ab13ap13_supported = any(all(type(ab13ap13_a) is type(ab13ap13_b) and ab13ap13_a == ab13ap13_b
                                        for ab13ap13_a, ab13ap13_b in zip(ab13ap13_tuple, ab13ap13_selector))
                                    for ab13ap13_selector in ab13ap13_selectors)
            ab13ap13_available = []
            ab13ap13_incomplete = []
            if ab13ap13_supported:
                for ab13ap13_row in ab13ap13_expected_fields:
                    if ab13ap13_row[:2] == [ab13ap13_context['view'], ab13ap13_context['direction']]:
                        ab13ap13_raw = ab13ap13_case['fields'].get(ab13ap13_row[2])
                        (ab13ap13_available if ab13ap13_raw is not None and len(ab13ap13_raw) == ab13ap13_row[3]
                         else ab13ap13_incomplete).append(ab13ap13_row[2])
            with self.subTest(transition=ab13ap13_case['id']):
                self.assertEqual(ab13ap13_case['available'], ab13ap13_available)
                self.assertEqual(ab13ap13_case['incomplete'], ab13ap13_incomplete)
                self.assertEqual(ab13ap13_case['state'], 'Unknown' if not ab13ap13_supported else
                                 'partial' if ab13ap13_incomplete else 'complete')
                self.assertIs(ab13ap13_case['qualified'], False)
                self.assertEqual(ab13ap13_case['physical'], 'Unknown')
                self.assertEqual(json.loads(json.dumps(ab13ap13_context)), ab13ap13_context)
        ab13ap13_expected_variants = [json.dumps(ab13ap13_pair, sort_keys=True) for ab13ap13_pair in
                                     ([False, None], [True, None], [True, 0], [True, False],
                                      [True, 'opaque-other'], [True, []], [True, {'preserved': [False, None, 0]}])]
        for ab13ap13_axis, ab13ap13_values in ab13ap13_context_values.items():
            self.assertEqual(sorted(ab13ap13_values), sorted(ab13ap13_expected_variants * 4), ab13ap13_axis)
        ab13ap13_axes = {ab13ap13_case['axis'] for ab13ap13_case in self.ab13ap13_fixture['transitions']}
        self.assertEqual(ab13ap13_axes, {'control', 'primary', 'secondary', 'operation', 'direction', 'view',
                                       'family', 'variant', 'opaque', *[ab13ap13_row[2] for ab13ap13_row in ab13ap13_expected_fields]})

    def test_ab13ap13_adc_channel_identity(self):
        self.assertEqual(len(self.ab13ap13_fixture['channels']), 18)
        ab13ap13_seen = set()
        for ab13ap13_case in self.ab13ap13_fixture['channels']:
            ab13ap13_numbers = [int.from_bytes(bytes(ab13ap13_case['fields'][f'adc{ab13ap13_i}']), 'little')
                                for ab13ap13_i in range(6)]
            self.assertEqual(ab13ap13_case['numbers'], ab13ap13_numbers)
            self.assertEqual(sum(ab13ap13_n != 0 for ab13ap13_n in ab13ap13_numbers), 1)
            ab13ap13_seen.add((ab13ap13_numbers.index(max(ab13ap13_numbers)), max(ab13ap13_numbers)))
        self.assertEqual(ab13ap13_seen, {(ab13ap13_i, ab13ap13_n) for ab13ap13_i in range(6)
                                        for ab13ap13_n in (1, 256, 65535)})

    def test_ab13ap13_admission_vectors(self):
        # Only JSON/byte admission, deliberately no runtime evaluator.
        def ab13ap13_pairs(ab13ap13_items):
            ab13ap13_result = {}
            for ab13ap13_key, ab13ap13_value in ab13ap13_items:
                if ab13ap13_key in ab13ap13_result:
                    raise ValueError('duplicate key')
                ab13ap13_result[ab13ap13_key] = ab13ap13_value
            return ab13ap13_result

        for ab13ap13_case in self.ab13ap13_fixture['admission']:
            with self.subTest(admission=ab13ap13_case['id']):
                try:
                    ab13ap13_value = json.loads(ab13ap13_case['json'], object_pairs_hook=ab13ap13_pairs,
                                               parse_constant=lambda ab13ap13_constant: (_ for _ in ()).throw(ValueError('non-JSON number')))
                    if not isinstance(ab13ap13_value, dict):
                        raise ValueError('root')
                    for ab13ap13_key in ('context', 'fields'):
                        if not isinstance(ab13ap13_value.get(ab13ap13_key), dict):
                            raise ValueError('object required')
                    if 'arguments' in ab13ap13_value and not isinstance(ab13ap13_value['arguments'], dict):
                        raise ValueError('arguments object')
                    for ab13ap13_raw in ab13ap13_value['fields'].values():
                        if not isinstance(ab13ap13_raw, list) or any(
                            isinstance(ab13ap13_byte, bool) or not isinstance(ab13ap13_byte, int)
                            or not 0 <= ab13ap13_byte <= 255
                            for ab13ap13_byte in ab13ap13_raw):
                            raise ValueError('byte array')
                    ab13ap13_accepted = True
                except (ValueError, TypeError):
                    ab13ap13_accepted = False
                self.assertIs(ab13ap13_accepted, ab13ap13_case['accepted'])

    def test_ab13ap13_envelope_roundtrip_and_fixture_copy(self):
        ab13ap13_blocks = self.ab13ap13_page.split('```json\n')[1:]
        self.assertEqual(len(ab13ap13_blocks), 2)
        ab13ap13_input, ab13ap13_output = [json.loads(ab13ap13_block.split('\n```', 1)[0]) for ab13ap13_block in ab13ap13_blocks]
        self.assertEqual(ab13ap13_input, {'context': {'primary': 181, 'secondary': 18, 'operation': 15,
                         'direction': 'request', 'view': 'valve-io', 'family': 'heat-pump', 'variant': None},
                         'fields': {'output': [0], 'valve': [1]}, 'arguments': {'opaque': False}})
        self.assertEqual(ab13ap13_output, {'context': ab13ap13_input['context'], 'raw': ab13ap13_input['fields'],
                         'arguments': {'opaque': False}, 'state': 'complete', 'physical': 'Unknown', 'qualified': False,
                         'fields': {'output': {'raw': [0], 'state': 'complete', 'grade': 'Hypothesis',
                         'flags': {'output0': False, 'output1': False}, 'reserved': 0},
                         'valve': {'raw': [1], 'state': 'complete', 'grade': 'Hypothesis', 'label': 'CH'}}})
        # A fixture storage control only: cannot prove a future Go implementation's ownership.
        ab13ap13_other = copy.deepcopy(ab13ap13_output)
        ab13ap13_input['fields']['output'][0] = 255
        ab13ap13_output['raw']['output'][0] = 128
        ab13ap13_output['context']['family'] = 'opaque-other'
        ab13ap13_output['arguments']['opaque'] = [False]
        ab13ap13_output['fields']['output']['flags']['output0'] = True
        self.assertEqual(ab13ap13_other['raw']['output'], [0])
        self.assertEqual(ab13ap13_other['context']['family'], 'heat-pump')
        self.assertIs(ab13ap13_other['arguments']['opaque'], False)
        self.assertIs(ab13ap13_other['fields']['output']['flags']['output0'], False)
        ab13ap13_distinct = [{}, {'v': None}, {'v': 0}, {'v': False}, {'v': []}]
        self.assertEqual(len({json.dumps(ab13ap13_v) for ab13ap13_v in ab13ap13_distinct}), 5)
        self.assertEqual([json.loads(json.dumps(ab13ap13_v)) for ab13ap13_v in ab13ap13_distinct], ab13ap13_distinct)

    def test_ab13ap13_normative_prose_and_field_properties(self):
        self.assertEqual(ab13ap13_prose_problems(self.ab13ap13_page), [])
        for ab13ap13_old, ab13ap13_new in ab13ap13_mutations:
            with self.subTest(mutation=ab13ap13_old):
                ab13ap13_flat = re.sub(r'\s+', ' ', self.ab13ap13_page)
                self.assertIn(ab13ap13_old, ab13ap13_flat)
                self.assertNotEqual(ab13ap13_prose_problems(ab13ap13_flat.replace(ab13ap13_old, ab13ap13_new, 1)), [])
        ab13ap13_phase = {'single-phase': [50], 'three-phase': [0, 33, 66, 100],
                          'approximate': True, 'tolerance': None, 'selected_kind': None}
        self.assertEqual(self.ab13ap13_fixture['field_properties'], {
            'pressure': {'calculation': 'Proven', 'candidate_domain': True, 'unmodeled': False,
                         'alternatives': {'candidate_default': 255.0, 'default_in_byte_domain': False, 'default_agrees': False}},
            'phase1': {'calculation': 'Proven', 'unmodeled': False, 'alternatives': ab13ap13_phase},
            'phase2': {'calculation': 'Proven', 'unmodeled': False, 'alternatives': ab13ap13_phase},
            'temperature': {'calculation': 'Proven', 'replacement_raw': [0, 128], 'sign_threshold': 32768,
                            'modulus': 65536, 'divisor': 16},
            'adc': {'calculation': 'Proven', 'max': 65535, 'clamp': None},
            'backup': {'replacement': 255, 'unmapped_example': 254, 'unmodeled_when_unmapped': True},
            'board': {'mapped': [0, 1, 2, 3, 11, 12], 'unmapped_example': 13, 'unmodeled_when_unmapped': True},
            'inverse': {'raw': [18, 52], 'unmodeled': True, 'number': None, 'complement': False},
            'grade': 'Hypothesis'})
        # Independent oracle for the stated per-field properties.
        self.assertEqual(self.ab13ap13_fixture['pressure_conflict']['number'], 255 / 10)
        self.assertNotEqual(self.ab13ap13_fixture['pressure_conflict']['number'],
                            self.ab13ap13_fixture['pressure_conflict']['candidate_default'])
        for ab13ap13_raw, ab13ap13_expected in (([0, 128], None), ([240, 255], -1.0), ([0, 0], 0.0), ([255, 127], 2047.9375)):
            ab13ap13_word = ab13ap13_raw[0] + 256 * ab13ap13_raw[1]
            ab13ap13_value = None if ab13ap13_raw == [0, 128] else (ab13ap13_word - 65536 if ab13ap13_word >= 32768 else ab13ap13_word) / 16
            self.assertEqual(ab13ap13_value, ab13ap13_expected)
        ab13ap13_by_raw = {(c['field'], tuple(c['raw'])): c for c in self.ab13ap13_fixture['cases']
                           if c['raw'] is not None and c['state'] == 'complete'}
        self.assertEqual(ab13ap13_by_raw[('adc0', (255, 255))]['number'], 65535)
        self.assertEqual(ab13ap13_by_raw[('backup', (255,))]['label'], 'replacement')
        self.assertIsNone(ab13ap13_by_raw[('backup', (254,))]['label'])
        self.assertEqual(ab13ap13_by_raw[('board', (12,))]['label'], 'opaque-code-12')
        self.assertIsNone(ab13ap13_by_raw[('board', (13,))]['label'])
        self.assertEqual(ab13ap13_by_raw[('phase1', (50,))]['number'], 50)
        self.assertEqual(ab13ap13_by_raw[('phase2', (33,))]['number'], 33)
        self.assertEqual(ab13ap13_by_raw[('temperature1', (240, 255))]['number'], -1.0)
        self.assertIsNone(ab13ap13_by_raw[('temperature1', (0, 128))]['number'])
        self.assertEqual(ab13ap13_by_raw[('temperature1', (0, 128))]['label'], 'replacement')


if __name__ == '__main__':
    unittest.main()
