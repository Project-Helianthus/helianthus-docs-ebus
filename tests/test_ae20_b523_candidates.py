"""Finite page/fixture acceptance checks, without a decoder or device coverage."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B523.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ae20_b523_candidates.json'
HEADERS = ['Grade', 'Identity', 'Direction', 'Logical position / extent',
           'Raw type / domain', 'Scale', 'Sentinel / default', 'Conflict / unresolved']
# Independent identity/position/extent oracles, never loaded from declarations.
LAYOUTS = [
    ['01', [3, 4, 5, 6, 7, 8], [9], 10, 4],
    ['05', [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14], [15, 16], 17, 4],
]
RELAY_RESULTS = ((0, 'off', None), (1, 'on-then-off', 1),
                 (253, 'on-then-off', 253), (254, 'on', None),
                 (255, 'unchanged', None))
PWM_RESULTS = ((0, 'numeric', 0, 'numeric', 0),
               (200, 'numeric', 100, 'numeric', 100),
               (201, 'numeric', 100.5, 'unchanged', None),
               (250, 'numeric', 125, 'unchanged', None),
               (255, 'outside-domain', None, 'unchanged', None))
FEEDBACK_RESULTS = (
    ('00', ('rejected', 'accepted', 'rejected', 'rejected')),
    ('01', ('rejected', 'accepted', 'rejected', 'rejected')),
    ('02', ('rejected', 'accepted', 'rejected', 'rejected')),
    ('04', ('rejected-or-unsupported', 'accepted', 'rejected-or-unsupported',
            'rejected-or-unsupported')),
    ('05', ('rejected-or-unsupported', 'accepted', 'rejected-or-unsupported',
            'rejected-or-unsupported')),
)


def expected_claims():
    rows = [
        ['Hypothesis', 'B523 OP01 relays', 'initiator-to-target',
         '3..8; request/positive extents 10/4', 'u8; 0..255',
         '1 second for 1..253',
         '0 off; 1..253 on then off; 254 on; 255 unchanged; default 0',
         'Unknown: native support, runtime effects, terminal mapping'],
        ['Hypothesis', 'B523 OP05 relays', 'initiator-to-target',
         '3..14; request/positive extents 17/4', 'u8; 0..255',
         '1 second for 1..253',
         '0 off; 1..253 on then off; 254 on; 255 unchanged; default 0',
         'Unknown: native support, runtime effects, terminal mapping'],
    ]
    for op, positions, extent in (('01', '9', '10/4'), ('05', '15,16', '17/4')):
        rows.extend([
            ['Hypothesis', f'B523 OP{op} PWM numeric candidate', 'initiator-to-target',
             f'{positions}; request/positive extents {extent}',
             'u8; numeric domain 0..250', 'raw/2 percent; 0..125 percent',
             'default 0; 251..255 outside numeric domain',
             'Conflict: behavioral candidate; Unknown: native support, runtime effects'],
            ['Hypothesis', f'B523 OP{op} PWM behavioral candidate', 'initiator-to-target',
             f'{positions}; request/positive extents {extent}', 'u8; 0..255',
             'raw/2 percent for 0..200; 0..100 percent',
             '201..255 unchanged; default 0',
             'Conflict: numeric candidate at 201..250; Unknown: native support, runtime effects'],
        ])
    for op, fallback, extent in (
            ('00', 'rejected', 'Unknown'), ('01', 'rejected', '4'),
            ('02', 'rejected', 'Unknown'), ('04', 'rejected-or-unsupported', 'Unknown'),
            ('05', 'rejected-or-unsupported', '4')):
        rows.append([
            'Hypothesis', f'B523 OP{op} feedback', 'target-to-initiator',
            f'3; positive extent {extent}', 'u8; 0..255', 'none',
            f'1 accepted; all others {fallback}; default {fallback}',
            'Unknown: physical ACK, persistence, readback, native support, runtime effects'])
    return rows


class B523CandidatesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.page = PAGE.read_text()

    def test_grade_qualification_and_explicit_absence(self):
        f = self.fixture
        self.assertEqual(set(f), {
            'family', 'synthetic', 'native_grade', 'arithmetic_grade',
            'physical_qualification', 'other_module_layouts', 'headers', 'claims',
            'layouts', 'relay_case_columns', 'pwm_case_columns',
            'feedback_case_columns', 'relay_cases', 'pwm_cases', 'feedback_cases'})
        self.assertEqual(f['family'], 'Vaillant B523')
        self.assertIs(f['synthetic'], True)
        self.assertEqual(f['native_grade'], 'Hypothesis')
        self.assertEqual(f['arithmetic_grade'], 'Proven')
        self.assertEqual(f['physical_qualification'], 'Unknown')
        self.assertIsNone(f['other_module_layouts'])
        self.assertEqual(f['relay_case_columns'],
                         ['op', 'position', 'raw', 'logical_values', 'state', 'duration_seconds'])
        self.assertEqual(f['pwm_case_columns'],
                         ['op', 'position', 'raw', 'logical_values', 'numeric_status',
                          'numeric_percent', 'behavior_status', 'behavior_percent'])
        self.assertEqual(f['feedback_case_columns'], ['op', 'raw', 'logical_values', 'result'])

    def test_structured_page_and_fixture_claims(self):
        section = self.page.split('## Relay timing, PWM alternatives and feedback\n', 1)[1]
        section = section.split('\n## ', 1)[0]
        table = [[cell.strip() for cell in line.strip('|').split('|')]
                 for line in section.splitlines() if line.startswith('|')]
        self.assertEqual(table, [HEADERS, ['---'] * 8, *expected_claims()])
        self.assertEqual(self.fixture['headers'], HEADERS)
        self.assertEqual(self.fixture['claims'], expected_claims())
        # These scope statements complement the structured table assertions.
        for statement in (
                'These are abstract\ncoordinates, not wire offsets.',
                'neither the logical response position nor an\nabstract extent establishes a physical reply length.',
                'The abstract request/positive\nextents include the three-position logical prefix; they are not physical reply\nlengths.',
                'Feedback acceptance is distinct from physical ACK, persistence and\nreadback; no such outcome follows from value 1.',
                '[synthetic examples](fixtures/ae20_b523_candidates.json)',
                'no claim about a broader set of declarations.'):
            self.assertIn(statement, self.page)
        self.assertNotIn('The coding of the feedback value of `00`, `04`', self.page)

    def test_operation_layouts_and_extents(self):
        self.assertEqual(self.fixture['layouts'], LAYOUTS)
        self.assertEqual(len(self.fixture['layouts'][0][1]), 6)
        self.assertEqual(len(self.fixture['layouts'][1][1]), 12)
        self.assertEqual(self.fixture['layouts'][1][1][-1], 14)

    def test_every_relay_position_and_duration_tuple(self):
        expected_keys = [(op, pos, raw) for op, positions, _, _, _ in LAYOUTS
                         for pos in positions for raw, _, _ in RELAY_RESULTS]
        cases = self.fixture['relay_cases']
        self.assertEqual(len(cases), 90)
        self.assertEqual([(c[0], c[1], c[2]) for c in cases], expected_keys)
        for op, positions, _, extent, _ in LAYOUTS:
            for pos in positions:
                for raw, state, duration in RELAY_RESULTS:
                    with self.subTest(op=op, position=pos, raw=raw):
                        case = cases[expected_keys.index((op, pos, raw))]
                        # Compare the full logical vector to catch a moved byte
                        # while all non-target relay/PWM values stay valid zero.
                        values = [181, 35, int(op, 16)] + [0] * (extent - 3)
                        values[pos] = raw
                        self.assertEqual(case, [op, pos, raw, values, state, duration])

    def test_every_pwm_position_keeps_both_alternatives(self):
        expected_keys = [(op, pos, raw) for op, _, positions, _, _ in LAYOUTS
                         for pos in positions for raw, *_ in PWM_RESULTS]
        cases = self.fixture['pwm_cases']
        self.assertEqual(len(cases), 15)
        self.assertEqual([(c[0], c[1], c[2]) for c in cases], expected_keys)
        for op, _, positions, extent, _ in LAYOUTS:
            for pos in positions:
                for raw, numeric_status, percent, behavior_status, behavior_percent in PWM_RESULTS:
                    with self.subTest(op=op, position=pos, raw=raw):
                        case = cases[expected_keys.index((op, pos, raw))]
                        values = [181, 35, int(op, 16)] + [0] * (extent - 3)
                        values[pos] = raw
                        self.assertEqual(case, [op, pos, raw, values, numeric_status,
                                               percent, behavior_status, behavior_percent])
                        if percent is not None:
                            # Arithmetic checked against literal expected values,
                            # without deriving the alternative's expected status.
                            self.assertEqual(raw / 2, percent)

    def test_feedback_operation_axis_and_fallbacks(self):
        expected = []
        for op, results in FEEDBACK_RESULTS:
            for raw, result in zip((0, 1, 2, 255), results):
                expected.append([op, raw, [181, 35, int(op, 16), raw], result])
        self.assertEqual(len(self.fixture['feedback_cases']), 20)
        self.assertEqual(self.fixture['feedback_cases'], expected)


if __name__ == '__main__':
    unittest.main()
