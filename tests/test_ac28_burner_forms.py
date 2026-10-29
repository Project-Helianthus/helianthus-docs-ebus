"""Synthetic declaration checks; these establish no peer or physical result."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/ebus-services/ebus-service-05h.md'
FIXTURE = ROOT / 'protocols/ebus-services/fixtures/ac28_burner_forms.json'


class BurnerForms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FIXTURE.read_text())
        cls.page = PAGE.read_text()
        cls.variant = cls.page.split('## Vaillant variants\n', 1)[1].split('## Communication Flow', 1)[0]

    def field(self, name, logical, carrier, domain, default, unit):
        fields = self.data['forms'][1]['fields']
        matches = [f for f in fields if f['name'] == name]
        self.assertEqual(len(matches), 1, name)
        actual = matches[0]
        self.assertEqual(actual, dict(logical=logical, name=name, carrier=carrier,
                                    domain=domain, default=default, unit=unit))
        unit_text = unit or '—'
        domain_text = f'{domain[0]}–{domain[1]}' + (' raw' if name == 'heat_state' else '')
        default_text = '0 (shutdown)' if name == 'heat_state' else str(default)
        self.assertIn(f'| {logical} | {name} | {carrier} | {domain_text} | {default_text} | {unit_text} | Hypothesis |', self.variant)

    def vector(self, field, raw, value, within):
        matches = [v for v in self.data['vectors'] if (v['field'], v['raw']) == (field, raw)]
        self.assertEqual(len(matches), 1, (field, raw))
        v = matches[0]
        self.assertEqual(v['value'], value)
        self.assertIs(v['within_candidate_domain'], within)
        fields = [f for f in self.data['forms'][1]['fields'] if f['name'] == field]
        self.assertEqual(len(fields), 1, field)
        f = fields[0]
        decoded = int(raw, 16)
        if f['carrier'] == 'signed8' and decoded >= 128:
            decoded -= 256
        conversion = self.data['identity_conversion']
        self.assertEqual(decoded * conversion['scale'] + conversion['offset'], value)
        self.assertEqual(f['domain'][0] <= value <= f['domain'][1], within)
        return v

    def test_heat_state_field(self):
        self.field('heat_state', 2, 'u8', [0, 255], 0, None)

    def test_boiler_field(self):
        self.field('boiler_target', 3, 'u8', [0, 90], 0, 'degC')

    def test_dhw_field(self):
        self.field('dhw_target', 4, 'u8', [0, 90], 0, 'degC')

    def test_outside_field(self):
        self.field('outside_temp', 5, 'signed8', [-128, 127], 0, 'degC')

    def test_setting_field(self):
        self.field('setting_degree', 6, 'u8', [0, 255], 0, '%')

    def test_exact_five_fields(self):
        self.assertEqual([f['name'] for f in self.data['forms'][1]['fields']],
                         ['heat_state', 'boiler_target', 'dhw_target', 'outside_temp', 'setting_degree'])

    def test_positive_prefix_has_no_body(self):
        self.assertEqual(self.data['forms'][0], dict(form='positive_only_prefix',
                         logical_prefix=[5, 1], body=None, meaning='Unknown'))
        self.assertIn('| Positive-only prefix alternative | `0x05` | `0x01` | None specified; no body inferred | Hypothesis |', self.variant)
        self.assertIn('Prefix relevance does not imply an echo, status, physical acknowledgement, or\neffect confirmation.', self.variant)

    def test_request_prefix_is_separate(self):
        self.assertEqual(len(self.data['forms']), 2)
        self.assertEqual(self.data['forms'][1]['form'], 'five_field_request')
        self.assertEqual(self.data['forms'][1]['logical_prefix'], [5, 1])
        self.assertIn('| Five-field request candidate | `0x05` | `0x01` | Five fields at logical 2–6 below | Hypothesis |', self.variant)
        self.assertIn('five-field request and service `0x05 0x04`', self.variant)

    def test_signed_outside_ff(self):
        self.vector('outside_temp', 'FF', -1, True)
        self.assertIn('Outside raw `0xFF` gives -1 degC', self.variant)

    def test_setting_ff_is_not_clipped(self):
        self.vector('setting_degree', 'FF', 255, True)
        self.assertIn('gives 255 %, without clipping to 100.', self.variant)

    def test_boiler_candidate_bounds(self):
        self.vector('boiler_target', '5A', 90, True)
        self.vector('boiler_target', '5B', 91, False)

    def test_dhw_candidate_bounds(self):
        self.vector('dhw_target', '5A', 90, True)
        self.vector('dhw_target', '5B', 91, False)

    def test_identity_not_unit_metadata_conversion(self):
        self.assertEqual(self.data['unit_metadata'], [273.15, 0.01])
        self.assertEqual(self.data['identity_conversion'], dict(scale=1, offset=0))
        self.vector('boiler_target', '5A', 90, True)
        self.vector('dhw_target', '5A', 90, True)
        self.assertIn('does not add a conversion to identity values:', self.variant)
        self.assertIn('boiler and DHW raw decimal 90 give candidate 90 degC, while 91 is outside', self.variant)

    def test_dd_is_distinct_unresolved_candidate(self):
        self.assertEqual(self.data['heat_check_candidate'], dict(raw='DD', meaning='unresolved', support='Unknown'))
        self.assertEqual(self.vector('heat_state', 'DD', 221, True)['meaning'], 'unresolved')
        self.assertIn('| `0xDD` | separate check candidate; meaning unresolved | Hypothesis |', self.variant)
        self.assertIn('universally absent nor an established supported meaning', self.variant)

    def test_labels_preserve_full_carrier(self):
        self.assertEqual(self.data['heat_labels'], {'00':'shutdown', '55':'DHW', 'AA':'heating', 'CC':'emission-check', 'EE':'controller-stop'})
        for raw, label in self.data['heat_labels'].items():
            self.assertIn(f'| `0x{raw}` | {label} | Hypothesis |', self.variant)
        self.assertIn('Unlabelled raw values remain raw.', self.variant)

    def test_3f_replacement_is_unknown(self):
        self.assertEqual(self.vector('outside_temp', '3F', 63, True)['replacement'], 'Unknown')
        self.assertIn('replacement for this variant is **Unknown**.', self.variant)

    def test_qualification_and_defaults_remain_unknown(self):
        self.assertEqual(self.data['family'], 'Vaillant')
        self.assertEqual(self.data['evidence_status'], 'Hypothesis')
        self.assertEqual(self.data['qualification'], 'Unknown')
        self.assertEqual(self.data['unknown'], ['outside_3F_replacement', 'scheduling', 'admission', 'default_materialization', 'physical_acknowledgement', 'effect_confirmation'])
        self.assertIn('**Unknown:** physical support, physical acknowledgement, effect confirmation,\n  scheduling, admission, and default materialization', self.variant)
        self.assertIn('Declared\n  defaults do not establish what a peer sends when fields are omitted.', self.variant)
        self.assertIn('**Proven (synthetic software checks only):**', self.variant)
        self.assertIn('This does not qualify native behavior or any device.', self.variant)

    def test_generic_standard_tables_preserved(self):
        standard = self.page.split('### Service 0x05 0x01 —', 1)[1].split('**Bus load:**', 1)[0]
        rows = [
            '| 0 | heat_request | BYTE | — | — | `0x00`=shutdown, `0x55`=DHW, `0xAA`=heating, `0xCC`=emission check, `0xDD`=QC service, `0xEE`=controller stop |',
            '| 1 | boiler_target | CHAR | 0–100 degC | — | Boiler target temperature |',
            '| 2 | dhw_target | CHAR | 0–100 degC | — | Service water target temperature |',
            '| 3 | outside_temp | SIGNED CHAR | -50 to +50 degC | `0x3F` | Outside temperature effective value |',
            '| 4 | setting_degree | CHAR | 0–100% | — | Setting degree between min/max boiler performance |',
        ]
        self.assertEqual([line for line in standard.splitlines() if line.startswith('| ') and line[2:3].isdigit()], rows)
        performance = self.page.split('### Service 0x05 0x04 —', 1)[1].split('### Service 0x05 0x05', 1)[0]
        for row in ['| 0 | eff_setting | CHAR | 0–100% | Effective setting degree |',
                    '| 1 | min_setting | CHAR | 0–100% | Minimum setting degree |',
                    '| 2 | max_setting | CHAR | 0–100% | Maximum setting degree |']:
            self.assertIn(row, performance)


if __name__ == '__main__':
    unittest.main(verbosity=2)
