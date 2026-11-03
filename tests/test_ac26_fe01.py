"""Synthetic partial declarations; no native or physical qualification."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'protocols/ebus-services/fixtures/ac26_fe01.json'
PAGE = ROOT / 'protocols/ebus-services/ebus-service-FEh.md'


class FE01PartialForms(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DATA.read_text())
        self.forms = self.data['forms']
        self.page = PAGE.read_text()
        self.generic, remainder = self.page.split('## Vaillant variants\n', 1)
        self.variant, self.questions = remainder.split('## Open questions\n', 1)

    def test_direction_and_encoding_alternatives(self):
        self.assertEqual([(f['direction'], f['encoding_declaration']) for f in self.forms], [
            ('request', 'explicit'), ('request', 'unspecified'),
            ('positive', 'explicit'), ('positive', 'unspecified')])
        for f in self.forms:
            with self.subTest(direction=f['direction'], encoding=f['encoding_declaration']):
                self.assertIsNone(f['encoding'])
                self.assertEqual(f['positive_prefix_context'],
                                 'PeBUS declaration' if f['direction'] == 'positive' else None)

    def test_constants_and_logical_coordinates(self):
        self.assertEqual(self.data['coordinate_system'], 'logical declaration positions, not physical offsets')
        for f in self.forms:
            with self.subTest(direction=f['direction'], encoding=f['encoding_declaration']):
                self.assertEqual(f['constants'], [
                    {'raw_hex': 'FE', 'logical_position': 0, 'bit': 0, 'width_bits': 8},
                    {'raw_hex': '01', 'logical_position': 1, 'bit': 0, 'width_bits': 8}])

    def test_absent_body_is_not_zero_length(self):
        for f in self.forms:
            for field in ['body', 'unit', 'enum', 'selector', 'sentinel', 'text',
                          'termination', 'physical_offsets', 'physical_length']:
                with self.subTest(direction=f['direction'], encoding=f['encoding_declaration'], field=field):
                    self.assertIsNone(f[field])

    def test_hypothesis_and_unknown_qualification(self):
        self.assertEqual(self.data['evidence'], 'synthetic representation only')
        for f in self.forms:
            self.assertEqual((f['status'], f['qualification']), ('Hypothesis', 'Unknown'))
        for field in ['family_availability', 'endpoint_support', 'lifecycle', 'effects']:
            with self.subTest(field=field):
                self.assertEqual(self.data[field], 'Unknown')

    def test_page_table_independent_of_fixture(self):
        # Literal expectations deliberately do not derive from the JSON fixture.
        rows = [[cell.strip() for cell in line.split('|')[1:-1]]
                for line in self.variant.splitlines() if line.startswith('|')]
        self.assertEqual(rows, [
            ['Placement alternative', 'Encoding declaration', 'Constants (logical position, bit, width)', 'Native body', 'Status'],
            ['---', '---', '---', '---', '---'],
            ['request', 'explicit (details Unknown)', '`FE` (0, 0, 8); `01` (1, 0, 8)', 'Unknown', 'Hypothesis'],
            ['request', 'unspecified', '`FE` (0, 0, 8); `01` (1, 0, 8)', 'Unknown', 'Hypothesis'],
            ['positive (PeBUS declaration)', 'explicit (details Unknown)', '`FE` (0, 0, 8); `01` (1, 0, 8)', 'Unknown', 'Hypothesis'],
            ['positive (PeBUS declaration)', 'unspecified', '`FE` (0, 0, 8); `01` (1, 0, 8)', 'Unknown', 'Hypothesis']])

    def test_page_body_and_physical_uncertainty(self):
        for statement in [
            '**Unknown body:** No native body, unit, enum, selector, sentinel, text,\ntermination or physical length is declared in this partial form.',
            'Absence of a\nbody declaration is not a declared empty body or a zero length.',
            'constants alone cannot establish a two-byte physical reply.',
            'positive-prefix relevance\nis specific to a PeBUS declaration.',
            'unspecified encoding does not inherit the explicit one.',
            'Encoding details beyond the presence of a declaration remain Unknown.',
            'not captures or\nphysical qualification evidence.']:
            with self.subTest(statement=statement):
                self.assertIn(statement, self.variant)
        self.assertIn('**Hypothesis (partial FE01 family form):**', self.variant)
        self.assertNotIn('Proven', self.variant)
        self.assertIn('**Unknown:** Family availability, endpoint support, lifecycle and effects.', self.questions)
        self.assertIn('**Unknown:** Physical qualification, physical offsets and physical length', self.questions)

    def test_generic_text_contract_preserved_separately(self):
        self.assertIn('| 0–9 | error_text | CHAR×10 | — | — | 10-character error message (ASCII) |', self.generic)
        self.assertIn('**Payload (initiator telegram):**', self.generic)
        self.assertIn('**Telegram type:** Broadcast (`DST=0xFE`).', self.generic)
        self.assertIn('eBUS Specification Application Layer (OSI 7) V1.6.1, §3.7', self.generic)
        self.assertIn('The general-broadcast ten-character body contract above remains separate and\nauthoritative for that generic form. It is not the body of this partial family\nform.', self.variant)


if __name__ == '__main__':
    unittest.main()
