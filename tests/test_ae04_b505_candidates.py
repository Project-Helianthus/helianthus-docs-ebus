"""Explicit acceptance checks of finite declarations, not decoder coverage."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ae04_b505_candidates.json'
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B505.md'


class B505Candidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.entries = cls.fixture['declarations']
        cls.page = PAGE.read_text()

    def test_finite_identities_and_absence(self):
        expected = [
            ('32', 'temperature_1', 16), ('32', 'temperature_2', 16),
            ('61', 'dhw_setpoint', None), ('4D', 'collector_temperature', None),
            ('4D', 'collector_error', 8), (None, 'pump_power_display', None),
            (None, 'remote_control', 8), ('4E', 'priority', 8),
        ]
        self.assertEqual(len(self.entries), 8)
        for entry, (operation, field, width) in zip(self.entries, expected):
            identity = dict(family='vaillant', variant='B505', pb='B5', sb='05',
                            operation=operation, direction=None, field=field)
            self.assertEqual(set(entry['identity']), set(identity))
            for axis, value in identity.items():
                with self.subTest(field=field, axis=axis):
                    self.assertEqual(entry['identity'][axis], value)
            self.assertEqual((entry['absolute_position'], entry['width_bits']),
                             (None, width))

    def test_grades_and_unresolved_metadata(self):
        self.assertEqual(self.fixture['qualification'], 'Unknown')
        self.assertEqual(self.fixture['provenance'],
                         'synthetic; finite candidate declarations only; no device observation')
        for entry in self.entries:
            with self.subTest(field=entry['identity']['field']):
                self.assertEqual(entry['grade'], 'Hypothesis')
                self.assertEqual((entry['scale'], entry['default']), (None, None))
                self.assertEqual(entry['unresolved'], {
                    'physical_support': 'Unknown', 'acknowledgement': 'Unknown',
                    'acceptance': 'Unknown', 'persistence': 'Unknown',
                    'duration_enforcement': 'Unknown', 'freshness': 'Unknown',
                    'execution': 'Unknown',
                })
                if entry['identity']['field'] != 'priority':
                    self.assertEqual((entry['signedness'], entry['bounds']),
                                     ('Unknown', None))

    def test_raw_branch_declarations(self):
        expected = [
            ({'8000': 'preserve-existing', '0000': 'circuit-default'},
             'numeric-candidate', 'raw-before-conversion'),
            ({'8000': 'preserve-existing', '0000': 'circuit-default'},
             'numeric-candidate', 'raw-before-conversion'),
            ({}, 'Unknown', None), ({}, 'Unknown', None),
            ({'55': 'short-circuit', 'AA': 'open'}, 'Unknown', None),
            ({}, 'Unknown', None),
            ({'01': 'enable-associated-output'}, 'Unknown', None),
            ({}, 'Unknown', None),
        ]
        self.assertEqual([(e['branches'], e['fallback'], e['selection_order'])
                          for e in self.entries], expected)

    def test_independent_temperature_alternatives(self):
        self.assertEqual([
            (c['raw'], c['outcomes'], c['numeric_values'])
            for c in self.fixture['op32_cases']
        ], [
            (['8000', '0000'], ['preserve-existing', 'circuit-default'], [None, None]),
            (['0000', '8000'], ['circuit-default', 'preserve-existing'], [None, None]),
            (['8000', '8000'], ['preserve-existing', 'preserve-existing'], [None, None]),
            (['0001', '0000'], ['numeric-candidate', 'circuit-default'], [None, None]),
        ])
        self.assertEqual(self.fixture['other_operation_case'], {
            'operation': '61', 'field': 'dhw_setpoint', 'raw': '8000',
            'outcome': 'Unknown', 'numeric_value': None,
        })

    def test_separate_duration_associations(self):
        self.assertEqual([e['duration_seconds'] for e in self.entries],
                         [None, None, 900, 900, 900, None, None, None])
        # Independent unit arithmetic; neither a timer nor an expiry assertion.
        for index in (2, 3, 4):
            with self.subTest(field=self.entries[index]['identity']['field']):
                self.assertEqual(self.entries[index]['duration_seconds'], 15 * 60)

    def test_sensor_display_remote_and_priority(self):
        self.assertEqual(self.fixture['sensor_cases'], [
            {'raw': '55', 'outcome': 'short-circuit'},
            {'raw': 'AA', 'outcome': 'open'},
            {'raw': '54', 'outcome': 'Unknown'},
        ])
        self.assertEqual([e['display_steps'] for e in self.entries],
                         [None, None, None, None, None, [0, 25, 50, 75, 100], None, None])
        # Adjacent step arithmetic is checked against literal expected differences.
        steps = self.entries[5]['display_steps']
        self.assertEqual([b - a for a, b in zip(steps, steps[1:])], [25, 25, 25, 25])
        self.assertEqual([e['priority'] for e in self.entries],
                         [None, None, None, None, None, None, None,
                          {'0': 'lowest', '255': 'highest'}])
        self.assertEqual((self.entries[7]['signedness'], self.entries[7]['bounds']),
                         ('unsigned', [0, 255]))
        self.assertEqual(self.fixture['priority_cases'], [
            {'raw': 0, 'order': 'lowest', 'temperature': None},
            {'raw': 255, 'order': 'highest', 'temperature': None},
        ])
        self.assertLess(self.fixture['priority_cases'][0]['raw'],
                        self.fixture['priority_cases'][1]['raw'])

    def test_structured_page_claims(self):
        section = self.page.split('## Bounded sentinel and override candidates\n', 1)[1]
        section = section.split('## Profiles\n', 1)[0]
        rows = [[cell.strip() for cell in line.strip('|').split('|')]
                for line in section.splitlines() if line.startswith('|')]
        self.assertEqual(rows[:2], [
            ['Identity (operation / field)', 'Grade', 'Direction',
             'Logical position / extent', 'Raw type/domain', 'Scale',
             'Sentinel/default/conflict', 'Unresolved'],
            ['---'] * 8,
        ])
        self.assertEqual(rows[2:], [
            ['OP32 / temperature_1', 'Hypothesis', 'Unknown',
             'first temperature / 16 bits; absolute position Unknown',
             'raw word; signedness Unknown', 'Unknown',
             '8000: preserve-existing; 0000: circuit-default; otherwise: numeric-candidate; select raw branch before conversion',
             'normal conversion and conflicting numeric bounds Unknown; default temperature Unknown'],
            ['OP32 / temperature_2', 'Hypothesis', 'Unknown',
             'second temperature / 16 bits; absolute position Unknown',
             'raw word; signedness Unknown', 'Unknown',
             '8000: preserve-existing; 0000: circuit-default; otherwise: numeric-candidate; select raw branch before conversion independently',
             'normal conversion and conflicting numeric bounds Unknown; default temperature Unknown'],
            ['OP61 / dhw_setpoint', 'Hypothesis', 'Unknown',
             'Unknown / extent Unknown', 'Unknown', 'Unknown',
             'validity 15 minutes = 900 seconds; default Unknown; no OP32 sentinel interpretation',
             'acknowledgement, acceptance, persistence and duration enforcement Unknown'],
            ['OP4D / collector_temperature', 'Hypothesis', 'Unknown',
             'Unknown / extent Unknown', 'Unknown', 'Unknown',
             'validity 15 minutes = 900 seconds; default Unknown',
             'acknowledgement, acceptance, persistence and duration enforcement Unknown'],
            ['OP4D / collector_error', 'Hypothesis', 'Unknown',
             'Unknown / 8 bits', 'raw byte; signedness Unknown', 'Unknown',
             '55: short-circuit; AA: open; other codes Unknown; validity 15 minutes = 900 seconds; default Unknown',
             'acknowledgement, acceptance, persistence and duration enforcement Unknown'],
            ['Unknown operation / pump_power_display', 'Hypothesis', 'Unknown',
             'Unknown / extent Unknown',
             'raw encoding Unknown; display domain 0, 25, 50, 75, 100 percent',
             'raw conversion Unknown; display step 25 percent', 'default Unknown',
             'operation, raw bounds and duration Unknown'],
            ['Unknown operation / remote_control', 'Hypothesis', 'Unknown',
             'Unknown / 8 bits', 'raw byte; signedness Unknown', 'Unknown',
             '01: enable-associated-output; other bytes Unknown; default Unknown',
             'operation and duration Unknown'],
            ['OP4E / priority', 'Hypothesis', 'Unknown',
             'Unknown / 8 bits', 'unsigned byte; 0..255', 'no quantity scale',
             '0: lowest; 255: highest; default Unknown',
             'absolute position and duration Unknown; independent of quantity units, freshness and execution'],
        ])

    def test_page_scope_and_conflict_corrections(self):
        for statement in [
            'Logical positions\nidentify independent alternatives, not wire offsets',
            'Unknown metadata is absent,\nnot zero.',
            'physical support, acknowledgement, acceptance, persistence,\nfreshness, execution and enforcement of any proposed duration remain **Unknown**.',
            '[Synthetic candidate cases](fixtures/ae04_b505_candidates.json)',
            'synthetic correctness does not qualify native\nwire behavior.',
            'the eight independently merged\nAE03 declarations, not a completed family catalogue.',
            'room temperatures and offsets outside the bounded slice below',
            'the older CSV does\nnot resolve their conflicting conversions, bounds, positions or response claims.',
            'does not establish acknowledgement or acceptance\n  for the bounded DHW override below.',
            'normal conversion and conflicting numeric bounds\n  remain Unknown; neither sentinel supplies a numeric temperature.',
            'the separate priority candidate is bounded\n  below and has no established absolute position here.',
        ]:
            with self.subTest(statement=statement):
                self.assertIn(statement, self.page)


if __name__ == '__main__':
    unittest.main()
