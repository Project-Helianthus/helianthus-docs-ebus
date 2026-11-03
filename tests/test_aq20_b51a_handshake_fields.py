"""Static checks that the AQ20 page keeps its distinctions; no runtime API exists."""
from pathlib import Path
import unittest

Ab19Aq19Page = Path(__file__).resolve().parents[1] / 'architecture/aq20_b51a_handshake_fields.md'


class TestAb19Aq19Page(unittest.TestCase):
    def setUp(self):
        self.ab19aq19text = ' '.join(Ab19Aq19Page.read_text().split())

    def test_ab19aq19_contract_and_stem(self):
        for ab19aq19needle in (
            'func Ab19Aq19Evaluate(ab19Aq19Input json.RawMessage) (json.RawMessage, error)',
            'TestAb19Aq19',
            'null is not an omitted operation',
        ):
            self.assertIn(ab19aq19needle, self.ab19aq19text)

    def test_ab19aq19_bit_masks(self):
        for ab19aq19needle in (
            'Bits 0 `power-on/start`, 1 `change`, 2 `CRC-support`; bits 3..7 `reserved`',
            'Bits 0 `valid`, 1 `invalid`, 2 `blocked`, 3 `change`, 4 `denied`, 5 `invalid-range`, 6 `not-user-adjustable`; bit 7 `reserved`',
            'Bit 0 is candidate `denied`; bits 1..7 are `unmodeled`',
            'positive flags `02` means `invalid`, not `change`; positive `08` selects the conditional spans',
        ):
            self.assertIn(ab19aq19needle, self.ab19aq19text)

    def test_ab19aq19_arithmetic_examples(self):
        self.assertEqual(52 + 256 * 18, 4660)
        self.assertIn('Raw CRC bytes `34 12` produce `number=4660`', self.ab19aq19text)
        self.assertIn('LEu16 raw word: first byte + 256 × second byte', self.ab19aq19text)
        self.assertIn('Decoding reset ack `02` as denied violates this contract', self.ab19aq19text)

    def test_ab19aq19_aggregate_state_rules(self):
        for ab19aq19needle in (
            'Opaque `dsn`, `start` and `offset` spans are optional in every branch',
            'an absent span is result state `absent` and alone never makes the top level `partial`',
            'missing or incorrectly sized fixed-width fields, and incomplete positive flags, yield `partial`',
        ):
            self.assertIn(ab19aq19needle, self.ab19aq19text)

    def test_ab19aq19_candidate_grades_only(self):
        self.assertIn('their provenance is not published', self.ab19aq19text)
        self.assertIn('physical="Unknown"', self.ab19aq19text)
        self.assertIn('qualified=false', self.ab19aq19text)
        self.assertNotIn('Proven local API', self.ab19aq19text.replace('**Proven local API contract:**', ''))


if __name__ == '__main__':
    unittest.main()
