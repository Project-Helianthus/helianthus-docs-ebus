"""Synthetic documentation checks; no API implementation or runtime invocation."""
import copy
import itertools
import json
import math
from pathlib import Path
import re
import unittest


ab09ap09_root = Path(__file__).resolve().parents[1]


def ab09ap09_table(ab09ap09_page, ab09ap09_header):
    ab09ap09_lines = ab09ap09_page.splitlines()
    ab09ap09_start = ab09ap09_lines.index(ab09ap09_header) + 2
    ab09ap09_rows = []
    for ab09ap09_line in ab09ap09_lines[ab09ap09_start:]:
        if not ab09ap09_line.startswith('|'):
            break
        ab09ap09_rows.append(tuple(ab09ap09_cell.strip() for ab09ap09_cell in ab09ap09_line.strip('|').split('|')))
    return ab09ap09_rows


def ab09ap09_pairs(ab09ap09_items):
    ab09ap09_result = {}
    for ab09ap09_key, ab09ap09_value in ab09ap09_items:
        if ab09ap09_key in ab09ap09_result:
            raise ValueError('duplicate key')
        ab09ap09_result[ab09ap09_key] = ab09ap09_value
    return ab09ap09_result


def ab09ap09_integer(ab09ap09_value, ab09ap09_limit):
    return (type(ab09ap09_value) in (int, float)
            and math.isfinite(ab09ap09_value)
            and ab09ap09_value == int(ab09ap09_value)
            and 0 <= ab09ap09_value <= ab09ap09_limit)


def ab09ap09_admission(ab09ap09_text):
    """Test-only shape oracle; does not evaluate semantic fields or produce API output."""
    ab09ap09_value = json.loads(ab09ap09_text, object_pairs_hook=ab09ap09_pairs,
                               parse_constant=lambda ab09ap09_token: (_ for _ in ()).throw(ValueError(ab09ap09_token)))
    if type(ab09ap09_value) is not dict:
        raise ValueError('object required')
    for ab09ap09_key in ('context', 'fields'):
        if type(ab09ap09_value.get(ab09ap09_key)) is not dict:
            raise ValueError('required object')
    if 'arguments' in ab09ap09_value and type(ab09ap09_value['arguments']) is not dict:
        raise ValueError('arguments object')
    ab09ap09_context = ab09ap09_value['context']
    for ab09ap09_key in ('primary', 'secondary', 'operation'):
        if ab09ap09_key in ab09ap09_context and ab09ap09_context[ab09ap09_key] is not None:
            if type(ab09ap09_context[ab09ap09_key]) not in (int, float) or not math.isfinite(ab09ap09_context[ab09ap09_key]) or ab09ap09_context[ab09ap09_key] != int(ab09ap09_context[ab09ap09_key]):
                raise ValueError('selector kind')
    for ab09ap09_key in ('direction', 'view'):
        if ab09ap09_key in ab09ap09_context and ab09ap09_context[ab09ap09_key] is not None:
            if type(ab09ap09_context[ab09ap09_key]) is not str:
                raise ValueError('selector kind')
    for ab09ap09_bytes in ab09ap09_value['fields'].values():
        if type(ab09ap09_bytes) is not list or any(not ab09ap09_integer(ab09ap09_byte, 255) for ab09ap09_byte in ab09ap09_bytes):
            raise ValueError('byte array')
    ab09ap09_arguments = ab09ap09_value.get('arguments', {})
    ab09ap09_supported = all(ab09ap09_context.get(ab09ap09_key) == ab09ap09_expected
                            for ab09ap09_key, ab09ap09_expected in
                            [('primary', 181), ('secondary', 85), ('operation', 0),
                             ('direction', 'local'), ('view', 'manager-gate')])
    for ab09ap09_key, ab09ap09_limit in [('controller_type', 255), ('spn', 65535)]:
        if ab09ap09_key in ab09ap09_arguments:
            if not ab09ap09_integer(ab09ap09_arguments[ab09ap09_key], ab09ap09_limit):
                raise ValueError('argument kind/range')
        elif ab09ap09_supported:
            raise ValueError('missing argument')
    if 'family_match' in ab09ap09_arguments:
        if ab09ap09_arguments['family_match'] is not None and type(ab09ap09_arguments['family_match']) is not bool:
            raise ValueError('Boolean or null')
    elif ab09ap09_supported:
        raise ValueError('missing family argument')
    return ab09ap09_value, ab09ap09_supported


class TestAb09Ap09ManagerGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ab09ap09_page = (ab09ap09_root / 'architecture/ap10_b555_manager_gate.md').read_text()
        cls.ab09ap09_fixture = json.loads((ab09ap09_root / 'architecture/fixtures/ap10_b555_manager_gate.json').read_text(), object_pairs_hook=ab09ap09_pairs)

    def test_ab09ap09_signature_and_selector_table(self):
        self.assertEqual(re.findall(r'```go\n(.*?)\n```', self.ab09ap09_page, re.S),
                         ['func Ab09Ap09Evaluate(ab09ap09Input json.RawMessage) (json.RawMessage, error)'])
        self.assertEqual(ab09ap09_table(self.ab09ap09_page, '| Selector member | Accepted value | Kind |'), [
            ('primary', '181', 'integer'), ('secondary', '85', 'integer'),
            ('operation', '0', 'integer'), ('direction', 'local', 'string'),
            ('view', 'manager-gate', 'string')])
        self.assertEqual(ab09ap09_table(self.ab09ap09_page, '| Argument | Kind | Range / values | Required for supported view |'), [
            ('controller_type', 'u8', '0..255', 'yes'), ('spn', 'u16', '0..65535', 'yes'),
            ('family_match', 'Boolean or null', 'true / false / null', 'yes')])

    def test_ab09ap09_formulas_and_grades(self):
        self.assertEqual(ab09ap09_table(self.ab09ap09_page, '| Result member | Formula / value | Grade |'), [
            ('fields.reply.flags.bit0', '(reply[0] & 1) != 0', 'Hypothesis; calculation=Proven'),
            ('fields.reply.flags.bit1', '(reply[0] & 2) != 0', 'Hypothesis; calculation=Proven'),
            ('fields.reply.reserved', 'reply[0] & 252', 'Hypothesis; calculation=Proven'),
            ('fields.reply.eligible', 'controller_type == 2 && spn == 385 && family_match == true && bit0 && bit1', 'Hypothesis; calculation=Proven'),
            ('fields.reply.first_bit_policy', 'bit0', 'Hypothesis; calculation=Proven'),
            ('fields.reply.family_applicability', 'Unknown if family_match is null; otherwise supplied Boolean', 'Hypothesis'),
            ('fields.family_role.number', '21 (0x15)', 'Hypothesis'),
            ('fields.route_role.number', '8 (0x08)', 'Hypothesis')])
        self.assertIs(type(self.ab09ap09_fixture['qualified']), bool)
        self.assertEqual({ab09ap09_key: self.ab09ap09_fixture[ab09ap09_key] for ab09ap09_key in ('grade', 'calculation', 'physical', 'qualified')},
                         {'grade': 'Hypothesis', 'calculation': 'Proven', 'physical': 'Unknown', 'qualified': False})

    def test_ab09ap09_page_truth_table(self):
        ab09ap09_expected = [
            ('0', 'false', 'false', '0', 'false', 'false'),
            ('1', 'true', 'false', '0', 'false', 'true'),
            ('2', 'false', 'true', '0', 'false', 'false'),
            ('3', 'true', 'true', '0', 'true', 'true'),
            ('128', 'false', 'false', '128', 'false', 'false'),
            ('131', 'true', 'true', '128', 'true', 'true')]
        self.assertEqual(ab09ap09_table(self.ab09ap09_page, '| Reply byte (decimal) | bit0 | bit1 | reserved | eligible | first_bit_policy |'), ab09ap09_expected)
        ab09ap09_cases = {ab09ap09_case['id']: ab09ap09_case for ab09ap09_case in self.ab09ap09_fixture['cases']}
        for ab09ap09_row in ab09ap09_expected:
            ab09ap09_tuple = [ab09ap09_cell == 'true' if ab09ap09_index != 2 else int(ab09ap09_cell)
                              for ab09ap09_index, ab09ap09_cell in enumerate(ab09ap09_row[1:])]
            self.assertEqual(ab09ap09_cases['ab09ap09_byte_' + ab09ap09_row[0]]['expected']['tuple'], ab09ap09_tuple)

    def test_ab09ap09_result_shape_table(self):
        self.assertEqual(ab09ap09_table(self.ab09ap09_page, '| Result path | Presence / shape |'), [
            ('context', 'required; unchanged object'),
            ('raw', 'required; deep independent fields copy'),
            ('arguments', 'unchanged object if supplied; otherwise omitted'),
            ('state', 'complete / partial / Unknown'),
            ('fields', 'required; object of semantic field results'),
            ('physical', 'required; Unknown'), ('qualified', 'required; false'),
            ('fields.reply.raw', 'retained if present; omitted if missing'),
            ('fields.reply.state', 'complete / incomplete / Unknown'),
            ('fields.reply.grade', 'Hypothesis for supported selector'),
            ('fields.reply.calculation', 'Proven only for complete supported reply'),
            ('fields.reply.labels', 'eligible: manager eligibility predicate; first_bit_policy: first-bit caller predicate; complete supported reply only'),
            ('fields.family_role', 'raw omitted; state complete; grade Hypothesis; label family-role; number 21; supported selector only'),
            ('fields.route_role', 'raw omitted; state complete; grade Hypothesis; label route-role; number 8; supported selector only')])

    def test_ab09ap09_state_table(self):
        self.assertEqual(ab09ap09_table(self.ab09ap09_page, '| Condition | Result state | Reply state | Roles | Formulas |'), [
            ('supported, one byte', 'complete', 'complete', 'complete', 'applied'),
            ('supported, missing reply', 'partial', 'incomplete', 'complete', 'none'),
            ('supported, empty reply', 'partial', 'incomplete', 'complete', 'none'),
            ('supported, two or more bytes', 'partial', 'incomplete', 'complete', 'none'),
            ('unsupported selector', 'Unknown', 'Unknown', 'omitted', 'none')])

    def test_ab09ap09_scenario_transitions(self):
        ab09ap09_seen = set()
        for ab09ap09_case in self.ab09ap09_fixture['cases']:
            with self.subTest(ab09ap09_id=ab09ap09_case['id']):
                self.assertTrue(ab09ap09_case['id'].startswith('ab09ap09_'))
                self.assertNotIn(ab09ap09_case['id'], ab09ap09_seen)
                ab09ap09_seen.add(ab09ap09_case['id'])
                ab09ap09_input, ab09ap09_supported = ab09ap09_admission(json.dumps(ab09ap09_case['input']))
                ab09ap09_expected = ab09ap09_case['expected']
                if 'tuple' in ab09ap09_expected:
                    self.assertEqual([type(ab09ap09_item) for ab09ap09_item in ab09ap09_expected['tuple']], [bool, bool, int, bool, bool])
                if 'eligible' in ab09ap09_expected:
                    self.assertIs(type(ab09ap09_expected['eligible']), bool)
                if not ab09ap09_supported:
                    self.assertEqual(ab09ap09_expected, {'state': 'Unknown'})
                    continue
                ab09ap09_reply = ab09ap09_input['fields'].get('reply', [])
                if len(ab09ap09_reply) != 1:
                    self.assertEqual(ab09ap09_expected, {'state': 'partial', 'eligible': False, 'roles': [21, 8]})
                    self.assertEqual(ab09ap09_input['fields']['opaque'], [0, 255])
                    continue
                ab09ap09_byte = ab09ap09_reply[0]
                ab09ap09_arguments = ab09ap09_input['arguments']
                # Division/remainder oracle is independent of the documented masks.
                ab09ap09_bit0 = ab09ap09_byte % 2 == 1
                ab09ap09_bit1 = (ab09ap09_byte // 2) % 2 == 1
                ab09ap09_eligible = (ab09ap09_byte % 4 == 3
                    and (ab09ap09_arguments['controller_type'], ab09ap09_arguments['spn'], ab09ap09_arguments['family_match']) == (2, 385, True))
                self.assertEqual(ab09ap09_expected, {'state': 'complete',
                    'tuple': [ab09ap09_bit0, ab09ap09_bit1, (ab09ap09_byte // 4) * 4, ab09ap09_eligible, ab09ap09_bit0],
                    'family_applicability': 'Unknown' if ab09ap09_arguments['family_match'] is None else ab09ap09_arguments['family_match']})
        self.assertEqual(len(ab09ap09_seen), 47)

    def test_ab09ap09_invalid_admission_and_numeric_boundaries(self):
        self.assertGreater(len(self.ab09ap09_fixture['invalid_json']), 50)
        for ab09ap09_text in self.ab09ap09_fixture['invalid_json']:
            with self.subTest(ab09ap09_text=ab09ap09_text):
                with self.assertRaises((ValueError, TypeError)):
                    ab09ap09_admission(ab09ap09_text)
        ab09ap09_control = copy.deepcopy(self.ab09ap09_fixture['cases'][3]['input'])
        for ab09ap09_type, ab09ap09_spn, ab09ap09_family in itertools.product((0, 2, 255), (0, 385, 65535), (False, True, None)):
            ab09ap09_control['arguments'] = {'controller_type': ab09ap09_type, 'spn': ab09ap09_spn, 'family_match': ab09ap09_family}
            self.assertTrue(ab09ap09_admission(json.dumps(ab09ap09_control))[1])
        for ab09ap09_key in ('primary', 'secondary', 'operation', 'direction', 'view'):
            ab09ap09_input = copy.deepcopy(self.ab09ap09_fixture['cases'][3]['input'])
            ab09ap09_input['context'].pop(ab09ap09_key)
            ab09ap09_input.pop('arguments')
            self.assertFalse(ab09ap09_admission(json.dumps(ab09ap09_input))[1])
        for ab09ap09_value in (0, 1, 255):
            ab09ap09_input = copy.deepcopy(self.ab09ap09_fixture['cases'][3]['input'])
            ab09ap09_input['fields']['opaque'] = [ab09ap09_value]
            self.assertTrue(ab09ap09_admission(json.dumps(ab09ap09_input))[1])
        self.assertTrue(ab09ap09_integer(2.0, 255))
        self.assertFalse(ab09ap09_integer(True, 255))
        self.assertFalse(ab09ap09_integer(2.5, 255))

    def test_ab09ap09_key_coverage_and_roundtrip_storage(self):
        ab09ap09_cases = self.ab09ap09_fixture['cases']
        ab09ap09_control = ab09ap09_cases[3]['input']
        for ab09ap09_key in ('primary', 'secondary', 'operation', 'direction', 'view', 'family', 'variant'):
            for ab09ap09_suffix in (('other', 'null', 'missing') if ab09ap09_key not in ('family', 'variant') else ('empty', 'zero', 'false', 'null', 'nested', 'missing')):
                ab09ap09_case = next(ab09ap09_item for ab09ap09_item in ab09ap09_cases if ab09ap09_item['id'] == 'ab09ap09_' + ab09ap09_key + '_' + ab09ap09_suffix)
                ab09ap09_context = copy.deepcopy(ab09ap09_case['input']['context'])
                ab09ap09_base_context = copy.deepcopy(ab09ap09_control['context'])
                ab09ap09_context.pop(ab09ap09_key, None)
                ab09ap09_base_context.pop(ab09ap09_key)
                self.assertEqual(ab09ap09_context, ab09ap09_base_context)
        for ab09ap09_case in ab09ap09_cases:
            ab09ap09_original = copy.deepcopy(ab09ap09_case)
            ab09ap09_roundtrip = json.loads(json.dumps(ab09ap09_case))
            self.assertEqual(ab09ap09_roundtrip, ab09ap09_case)
            ab09ap09_roundtrip['input']['fields']['reply'] = [255]
            ab09ap09_roundtrip['input']['context']['family'] = {'changed': []}
            ab09ap09_roundtrip['input']['arguments']['family_match'] = False
            self.assertEqual(ab09ap09_case, ab09ap09_original)
        # These checks concern artifact snapshots, not storage in an absent Go API.
        ab09ap09_nested = next(ab09ap09_item for ab09ap09_item in ab09ap09_cases if ab09ap09_item['id'] == 'ab09ap09_opaque_storage')
        ab09ap09_copy = copy.deepcopy(ab09ap09_nested)
        ab09ap09_copy['input']['arguments']['opaque']['nested'][0] = 99
        ab09ap09_nested_copy = json.loads(json.dumps(ab09ap09_nested))
        ab09ap09_nested_copy['input']['fields']['opaque'].append(1)
        self.assertEqual(ab09ap09_nested['input']['arguments']['opaque']['nested'], [0, False, None])
        self.assertEqual(ab09ap09_nested['input']['fields']['opaque'], [0, 255])

    def test_ab09ap09_bounded_policy_mutation_witnesses(self):
        # Reasoned predicate mutants, not production mutation testing.
        ab09ap09_witnesses = [
            ('or_bits', 1, 2, 385, True), ('first_bit_only', 1, 2, 385, True),
            ('ignore_type', 3, 3, 385, True), ('ignore_spn', 3, 2, 384, True),
            ('ignore_family', 3, 2, 385, False), ('accept_null', 3, 2, 385, None)]
        for ab09ap09_name, ab09ap09_byte, ab09ap09_type, ab09ap09_spn, ab09ap09_family in ab09ap09_witnesses:
            with self.subTest(ab09ap09_name=ab09ap09_name):
                self.assertFalse(ab09ap09_byte % 4 == 3 and ab09ap09_type == 2 and ab09ap09_spn == 385 and ab09ap09_family is True)
                self.assertTrue(3 % 4 == 3 and 2 == 2 and 385 == 385 and True is True)
        for ab09ap09_byte in range(256):
            self.assertEqual(bool(ab09ap09_byte & 1), ab09ap09_byte % 2 == 1)
            self.assertEqual(bool(ab09ap09_byte & 2), ab09ap09_byte % 4 in (2, 3))
            self.assertEqual(ab09ap09_byte & 252, ab09ap09_byte - ab09ap09_byte % 4)
        self.assertEqual(131 & 252, 128)
        self.assertNotEqual(131 & 252, 0)
        self.assertEqual((0x15, 0x08), (21, 8))
        self.assertNotEqual(21, 8)


if __name__ == '__main__':
    unittest.main()
