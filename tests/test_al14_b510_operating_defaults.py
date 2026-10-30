"""Offline declaration checks; these do not implement or test the Go lookup API."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/al14_b510_operating_defaults.md'
FIXTURE = ROOT / 'architecture/fixtures/al14_b510_operating_defaults.json'


class OperatingDefaultsContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text(encoding='utf-8')
        cls.data = json.loads(FIXTURE.read_text(encoding='utf-8'))

    def test_exact_example_identity(self):
        expected = {
            'family': 'vaillant', 'variant': 'B510', 'primary': 181,
            'secondary': 16, 'operation': 0, 'direction': 'request',
            'field': 'loading_pump', 'alternative': 'none', 'group': None,
            'instance_scope': 'none', 'register': None,
        }
        self.assertEqual(self.data['key'], expected)
        expected_axes = [
            ('family', 'Family', 'string', 'vaillant'),
            ('variant', 'Variant', 'string', 'B510'),
            ('primary', 'Primary', 'uint8', '181'),
            ('secondary', 'Secondary', '*uint8', '16'),
            ('operation', 'Operation', '*uint8', '0'),
            ('direction', 'Direction', 'string', 'request'),
            ('field', 'Field', 'string', 'loading_pump'),
            ('alternative', 'Alternative', 'string', 'none'),
            ('group', 'Group', '*uint8', 'null'),
            ('instance_scope', 'InstanceScope', 'string', 'none'),
            ('register', 'Register', '*uint16', 'null'),
        ]
        actual = [tuple(part.strip() for part in line.split('|')[1:-1])
                  for line in self.page.splitlines()
                  if line.startswith('| ') and line.split('|')[1].strip() in expected]
        self.assertEqual(actual, expected_axes)

    def test_page_declarations(self):
        expected = {
            'catalog_entries': ('6', 'Proven'),
            'identity_axes': ('11', 'Proven'),
            'forced_contexts': ('3', 'Proven'),
            'mode_default': ('forced-heating', 'Hypothesis'),
            'numeric_mode_code': ('null', 'Unknown'),
            'modulation_default': ('67', 'Hypothesis'),
            'option_bit_defaults': ('1,0,0,0,0,0,0,0', 'Hypothesis'),
            'option_bit2': ('CH_setpoint: heating -> cooling; raw unchanged', 'Hypothesis'),
            'loading_pump_domain': ('0..127.5 percent; unsigned u8 / 2', 'Hypothesis'),
            'loading_pump_default': ('255.0; conflicting literal, not a byte', 'Hypothesis'),
            'raw_FF_arithmetic': ('FF / 2 = 127.5', 'Proven'),
            'forced_mode_dependency': ('loading_pump meaning and pump_activation', 'Hypothesis'),
            'zero_degrees': ('stop / pump-stop', 'Hypothesis'),
            'zero_to_positive': ('candidate minimum 300 seconds', 'Hypothesis'),
            'execution_guarantee': ('false', 'Unknown'),
            'transition_enforcement': ('Unknown', 'Unknown'),
        }
        rows = [tuple(part.strip() for part in line.split('|')[1:-1])
                for line in self.page.splitlines() if line.startswith('| ')]
        declarations = [row for row in rows if row[0] in expected]
        self.assertEqual(declarations, [(name, *value) for name, value in expected.items()])

    def test_api_and_evidence_boundary(self):
        # These clauses pin the declared interface, not companion runtime behavior.
        text = ' '.join(self.page.split())
        for clause in (
            'Ab48Entries() (json.RawMessage, error)',
            'Ab48Lookup(Ab48Key) (json.RawMessage, bool, error)',
            'Optional pointer axes distinguish absent/null from explicit zero',
            'Grade and width are row metadata, not identity axes',
            'Absence returns `(nil, false, nil)`',
            'invalid source returns `(nil, false, error)`',
            'An invalid later row prevents an earlier match',
            'mutating a returned array or row must not alter the catalog or later results',
            'Preserve raw bytes and independent useful fields on partial interpretation failure',
            'partial last-known-good state', 'fail closed on new admission',
            'No real timer runs', 'not a timing guarantee or actuator implementation',
            'does not import or execute the companion implementation',
            'Nothing is stable before Helianthus 1.0',
            '../protocols/vaillant/ebus-vaillant-B510.md',
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, text)

    def test_defaults_are_separate(self):
        self.assertEqual(self.data['defaults'], {
            'mode': 'forced-heating', 'numeric_mode_code': None,
            'modulation': 67, 'option_bits': [1, 0, 0, 0, 0, 0, 0, 0],
            'loading_pump': 255.0,
        })
        self.assertNotEqual(self.data['defaults']['modulation'],
                            self.data['defaults']['loading_pump'])

    def test_raw_ff_and_conflicting_literal(self):
        pump = self.data['loading_pump']
        self.assertEqual(pump, {
            'formal_domain': [0, 127.5], 'unit': 'percent',
            'raw_bytes': 'FF', 'value': 127.5, 'default_conflict': True,
        })
        self.assertEqual(int(pump['raw_bytes'], 16) / 2, 127.5)
        self.assertGreater(self.data['defaults']['loading_pump'], pump['formal_domain'][1])

    def test_option_and_raw_axes_independently(self):
        # Full two-by-two controls: change bit2 at fixed raw, and raw at fixed bit2.
        self.assertEqual(self.data['option_cases'], [
            {'raw_setpoint': 42, 'option_bit2': 0, 'role': 'heating'},
            {'raw_setpoint': 42, 'option_bit2': 1, 'role': 'cooling'},
            {'raw_setpoint': 44, 'option_bit2': 0, 'role': 'heating'},
            {'raw_setpoint': 44, 'option_bit2': 1, 'role': 'cooling'},
        ])

    def test_forced_roles_without_byte_codes(self):
        contexts = self.data['forced_contexts']
        self.assertEqual(contexts, [
            {'mode': 'forced-heating', 'numeric_mode_code': None,
             'loading_pump_meaning': 'Unknown', 'pump_activation': 'Unknown'},
            {'mode': 'forced-DHW', 'numeric_mode_code': None,
             'loading_pump_meaning': 'Unknown', 'pump_activation': 'Unknown'},
            {'mode': 'forced-off', 'numeric_mode_code': None,
             'loading_pump_meaning': 'Unknown', 'pump_activation': 'Unknown'},
        ])

    def test_transition_axes_independently(self):
        self.assertEqual(self.data['zero_degrees_roles'], ['stop', 'pump-stop'])
        # From-only: (0,1)/(1,1); to-only: (0,1)/(0,0)/(0,2).
        # The requested (1,2) control has no invented minimum.
        expected = [(0, 1, 300), (1, 1, None), (0, 0, None),
                    (0, 2, 300), (1, 2, None)]
        self.assertEqual(self.data['transitions'], [
            {'from': start, 'to': end, 'candidate_minimum_seconds': seconds,
             'execution_guarantee': False, 'enforcement': 'Unknown'}
            for start, end, seconds in expected
        ])

    def test_independent_evidence_dimensions(self):
        self.assertIs(self.data['synthetic'], True)
        self.assertEqual(self.data['grade'], 'Hypothesis')
        for dimension in ('physical_qualification', 'presence', 'freshness', 'execution'):
            with self.subTest(dimension=dimension):
                self.assertEqual(self.data[dimension], 'Unknown')


if __name__ == '__main__':
    unittest.main(verbosity=2)
