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
        self.assertEqual(len(blocks), 3)
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


if __name__ == '__main__':
    unittest.main()
