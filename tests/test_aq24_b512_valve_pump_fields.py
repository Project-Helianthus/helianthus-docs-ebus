"""Offline checks for the B512 valve/pump field contract page; no runtime evaluator."""
import json
from pathlib import Path
import re
import unittest

AQ24_ROOT = Path(__file__).resolve().parents[1]
AQ24_PAGE = AQ24_ROOT / 'architecture/aq24_b512_valve_pump_fields.md'
AQ24_RESERVED = ('state', 'results', 'physical', 'qualified', 'timeout')
AQ24_TIMEOUT = {'seconds': 900, 'policy': 'reset-on-every-service', 'grade': 'Hypothesis'}


def aq24_blocks():
    return [json.loads(b) for b in re.findall(r'```json\n(.*?)```', AQ24_PAGE.read_text(), re.S)]


def aq24_op05_label(value):
    # Independent expectation for OP05 channel branches.
    if value == 0:
        return 'off'
    if 1 <= value <= 100:
        return 'on-or-speed'
    return 'unchanged' if value == 255 else 'unmapped'


class Aq24PageTest(unittest.TestCase):
    def test_signature_and_reservation(self):
        text = AQ24_PAGE.read_text()
        self.assertIn('func Ab23Aq23Evaluate(ab23Aq23Input json.RawMessage) (json.RawMessage, error)', text)
        for name in AQ24_RESERVED:
            self.assertIn('`%s`' % name, text)
        self.assertIn('is an admission error, never overwritten and never nested', text)

    def test_examples_parse_and_never_collide_with_reserved_names(self):
        blocks = aq24_blocks()
        self.assertEqual(len(blocks), 4)
        for name in AQ24_RESERVED:
            self.assertNotIn(name, blocks[0])
        for block in blocks[1:]:
            self.assertEqual(block['physical'], 'Unknown')
            self.assertIs(block['qualified'], False)
            self.assertTrue(set(block['fields']).issubset(set(block['results'])))

    def test_op05_example_matches_independent_branches(self):
        block = next(b for b in aq24_blocks() if b['context']['operation'] == 5 and 'results' in b)
        self.assertNotIn('timeout', block)
        modes = block['arguments']['external_modes']
        self.assertEqual(len(modes), 3)
        for index in range(3):
            name = 'channel%d' % index
            raw = block['fields'][name][0]
            result = block['results'][name]
            self.assertEqual(result['number'], raw)
            self.assertEqual(result['label'], aq24_op05_label(raw))
            self.assertIs(result['prerequisite'], modes[index] == 8)

    def test_op04_timeout_serialization(self):
        block = next(b for b in aq24_blocks() if b['context']['operation'] == 4)
        self.assertEqual(block['timeout'], AQ24_TIMEOUT)
        self.assertIsInstance(block['timeout']['seconds'], int)
        self.assertEqual(block['results']['setpoint']['label'], 'replacement/no-remote-control')

    def test_input_members_survive_in_complete_example(self):
        op05 = [b for b in aq24_blocks() if b['context']['operation'] == 5]
        self.assertEqual(op05[0]['extra'], op05[1]['extra'])
        self.assertEqual(op05[0]['fields'], op05[1]['fields'])
        self.assertEqual(op05[0]['extra'], {'absent_example': None, 'zero': 0, 'enabled': False, 'opaque': []})


# Independent oracle: (operation, direction, field) -> (width token, {raw: label} or ranges).
AQ24_TABLE = {
    (0, 'request', 'setpoint'): ('u8', ['0 `off`', '1..100 `on-or-speed`', '101..255 `unmapped`']),
    (2, 'request', 'valve'): ('u8', ['0 `CH`', '50 `midpoint`', '100 `DHW`', 'FE `standby`', 'FF `unchanged`']),
    (2, 'positive', 'valve'): ('u8', ['`alternatives`']),
    (2, 'positive', 'contact'): ('u8', ['0 `open`', '1 `closed`', 'other values `unmapped`']),
    (2, 'positive', 'tank'): ('signedLE16', ['Divide the signed integer by 16']),
    (2, 'positive', 'virtual_error'): ('LEu16', ['FFFF `no-error`']),
    (3, 'request', 'selector'): ('u8', ['0 `valve-temperature-input`']),
    (3, 'positive', 'status'): ('u8', ['0 `okay`', '1 `disconnected`', '2 `short-circuit`']),
    (3, 'positive', 'value'): ('LEu16', ['Raw unsigned integer only']),
    (4, 'request', 'setpoint'): ('u8', ['0 `off`', '1..100 `on-or-speed`', 'FF `replacement/no-remote-control`', '101..254 `unmapped`']),
    (4, 'positive', 'feedback'): ('u8', ['1 `accepted`', 'every other byte `rejected`']),
    (5, 'request', 'channel0`, `channel1`, `channel2'): ('u8', ['0 `off`', '1..100 `on-or-speed`', 'FF `unchanged`', '101..254 `unmapped`']),
}


def aq24_rows():
    rows = {}
    for line in AQ24_PAGE.read_text().splitlines():
        m = re.match(r'\| OP0(\d) \| (request|positive) \| `(.+?)`, (?:each )?(u8|LEu16|signedLE16) \| (.*) \|$', line)
        if m:
            rows[(int(m.group(1)), m.group(2), m.group(3))] = (m.group(4), m.group(5))
    return rows


class Aq24BranchTableTest(unittest.TestCase):
    def test_every_declared_selector_width_and_branch(self):
        rows = aq24_rows()
        self.assertEqual(set(rows), set(AQ24_TABLE))
        for key, (width, branches) in AQ24_TABLE.items():
            self.assertEqual(rows[key][0], width, key)
            for branch in branches:
                self.assertIn(branch, rows[key][1], key)

    def test_op00_and_op05_have_no_undeclared_directions(self):
        keys = set(aq24_rows())
        self.assertNotIn((0, 'positive', 'setpoint'), keys)
        self.assertFalse([k for k in keys if k[0] == 5 and k[1] == 'positive'])

    def test_rejection_and_admission_rules(self):
        text = AQ24_PAGE.read_text()
        for phrase in ('explicit null is not', 'duplicate keys at any depth',
                       'fractional or out-of-range bytes', 'missing, short or overlong',
                       'raw-only `Unknown`', 'exactly three u8 integers'):
            self.assertIn(phrase, text)

    def test_op02_alternatives_shape_and_tank_oracle(self):
        block = next(b for b in aq24_blocks() if b['context']['operation'] == 2)
        valve = block['results']['valve']
        self.assertEqual(valve['alternatives'], ['actual', 'setpoint-fallback'])
        self.assertEqual(valve['number'], block['fields']['valve'][0])
        lo, hi = block['fields']['tank']
        signed = int.from_bytes(bytes([lo, hi]), 'little', signed=True)
        self.assertEqual(block['results']['tank']['signed'], signed)
        self.assertEqual(block['results']['tank']['number'], signed / 16)
        self.assertEqual(block['results']['virtual_error']['number'], 0xFFFF)
        self.assertEqual(block['results']['virtual_error']['label'], 'no-error')
        self.assertEqual(block['results']['contact']['label'], 'unmapped')
        self.assertNotIn('timeout', block)


if __name__ == '__main__':
    unittest.main()
