"""Independent role, spelling and catalog-identity mutation controls."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check_name_decomposition as contract


def value(name='pump_active', parts=None, value_class='active', **updates):
    parts = parts if parts is not None else [('pump', 'subject'), ('active', 'predicate')]
    roles = {role: [] for role in contract.ROLES}
    for term, role in parts:
        roles[contract.normalized_role(role)].append(term)
    entry = dict(source=contract.CONTRACT, selector=name, emitted=name, kind='value',
                 status='compliant', parts=parts, roles=roles, value_class=value_class)
    entry.update(updates)
    return entry


class DecompositionTests(unittest.TestCase):
    def setUp(self):
        self.vocabulary = contract.grammar.load_vocabulary()
        self.features = {'special_function': {
            'observed_vaillant_definition': 'Special-function mode.',
            'generic_term_insufficient': 'Generic mode does not identify the function.'}}

    def validate(self, entry):
        contract.validate_entry(entry, self.vocabulary, self.features)

    def test_independent_complete_decomposition(self):
        self.validate(value('heating_flow_temperature_setpoint_maximum', [
            ('heating', 'purpose'), ('flow', 'place'), ('temperature', 'object'),
            ('setpoint', 'predicate'), ('maximum', 'bound')], 'setpoint'))

    def test_spelling_is_reconstructed(self):
        with self.assertRaises(ValueError):
            self.validate(value('fan_active'))

    def test_reversed_roles(self):
        with self.assertRaises(ValueError):
            self.validate(value('active_pump', [('active', 'predicate'), ('pump', 'subject')]))

    def test_false_role_assignment(self):
        with self.assertRaises(ValueError):
            self.validate(value('pump_active', [('pump', 'object'), ('active', 'predicate')]))

    def test_missing_predicate(self):
        with self.assertRaises(ValueError):
            self.validate(value('pump', [('pump', 'subject')]))

    def test_incorrect_predicate(self):
        with self.assertRaises(ValueError):
            self.validate(value(value_class='enabled'))

    def test_unknown_predicate(self):
        with self.assertRaises(ValueError):
            self.validate(value('pump_running', [('pump', 'subject'), ('running', 'predicate')], 'running'))

    def test_role_record_must_match(self):
        entry = value()
        entry['roles']['subject'] = ['fan']
        with self.assertRaises(ValueError):
            self.validate(entry)

    def test_value_unit_suffix_rejected(self):
        with self.assertRaises(ValueError):
            self.validate(value('flow_temperature_celsius', [('flow', 'place'),
                ('temperature', 'object'), ('celsius', 'part')], 'measured'))

    def test_maker_feature(self):
        self.validate(value('dhw_special_function_mode', [('dhw', 'purpose'),
            ('special_function', 'feature'), ('mode', 'predicate')], 'mode'))

    def test_feature_must_precede_predicate(self):
        with self.assertRaises(ValueError):
            self.validate(value('mode_special_function', [('mode', 'predicate'),
                ('special_function', 'feature')], 'mode'))

    def test_undocumented_feature(self):
        with self.assertRaises(ValueError):
            self.validate(value('mystery_enabled', [('mystery', 'feature'), ('enabled', 'predicate')], 'enabled'))

    def test_structural_examples_are_snake_case_only(self):
        for spelling in ['source_id', 'get_status', 'observed_at']:
            self.validate(value(spelling, [], 'structural', kind='structural'))
        for spelling in ['sourceId', 'get-status']:
            with self.assertRaises(ValueError):
                self.validate(value(spelling, [], 'structural', kind='structural'))

    def metric(self, exception=False):
        return value('helianthus_compressor_operating_time' + ('_seconds' if exception else '') + '_total',
            [('compressor', 'subject'), ('operating', 'object'), ('time', 'predicate')],
            'time', kind='metric', prefix='helianthus', counter=True, unit='seconds',
            unit_label=None if exception else 'seconds',
            **({'unit_exception': 'library', 'exception_reason': 'Emitter cannot attach unit labels.'} if exception else {}))

    def test_metric_constant_unit_label_and_counter_suffix(self):
        self.validate(self.metric())
        entry = self.metric()
        entry['emitted'] = entry['emitted'].removesuffix('_total')
        with self.assertRaises(ValueError):
            self.validate(entry)

    def test_improper_metric_unit_suffix(self):
        entry = self.metric()
        entry['emitted'] = entry['emitted'].replace('_total', '_seconds_total')
        with self.assertRaises(ValueError):
            self.validate(entry)

    def test_library_exception_requires_reason(self):
        self.validate(self.metric(True))
        entry = self.metric(True)
        del entry['exception_reason']
        with self.assertRaises(ValueError):
            self.validate(entry)

    def test_metric_requires_constant_unit_label(self):
        entry = self.metric()
        entry['unit_label'] = 'minutes'
        with self.assertRaises(ValueError):
            self.validate(entry)

    def test_provisional_unknown_retains_question_and_spelling(self):
        entry = value('circuit_unknown_9', [('circuit', 'subject'), ('unknown', 'placeholder'), ('9', 'index')],
            'unknown', status='provisional', current_spelling='circuit_unknown_9',
            open_question='Meaning and polarity remain Unknown.',
            follow_up='Project-Helianthus/helianthus-docs-ebus#573')
        self.validate(entry)
        for field, replacement in [('open_question', ''), ('follow_up', ''),
                                    ('current_spelling', 'circuit_active')]:
            altered = copy.deepcopy(entry)
            altered[field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(altered)

    def test_existing_debt_exact_spelling_and_rule(self):
        entry = value('legacy_name', [], 'unresolved', source=contract.MAP,
            status='existing_debt', current_spelling='legacy_name',
            open_question='Terms do not have vocabulary roles.',
            follow_up='Project-Helianthus/helianthus-docs-ebus#1151')
        self.validate(entry)
        entry['current_spelling'] = 'another_name'
        with self.assertRaises(ValueError):
            self.validate(entry)


class InventoryTests(unittest.TestCase):
    # Each identity field is varied separately: operation, group, register.
    # These catch dropping any component from extraction or inventory lookup.
    MAP_TEXT = ('## OP=0x02 — Local parameters\n### GG=0x01 — Group\n'
                '| RR | Name | Cat | Wire |\n|----|------|-----|------|\n'
                '| 0x0001 | pump_active | S | u8 |\n')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.map_path = self.root / contract.MAP
        self.map_path.parent.mkdir(parents=True)
        self.map_path.write_text(self.MAP_TEXT)
        self.doc_path = self.root / contract.CONTRACT
        self.doc_path.parent.mkdir(parents=True)
        self.doc_path.write_text('| Checked spelling | Kind |\n|---|---|\n| `pump_active` | Value |\n')
        self.data_path = self.root / contract.DATA
        self.data_path.parent.mkdir(parents=True)
        self.data = {'schema_version': 1, 'features': {}, 'entries': [value(), value(source=contract.MAP, selector='0x02/0x01/0x0001')]}
        self.save()

    def save(self):
        self.data_path.write_text(json.dumps(self.data))

    def test_legal_complete_inventory(self):
        self.assertEqual(contract.check(self.root), (2, 0))

    def test_every_selector_identity_field(self):
        for original, replacement in [('OP=0x02', 'OP=0x06'), ('GG=0x01', 'GG=0x02'), ('0x0001', '0x0002')]:
            with self.subTest(field=original):
                self.map_path.write_text(self.MAP_TEXT.replace(original, replacement))
                with self.assertRaises(ValueError):
                    contract.check(self.root)

    def test_new_removed_changed_and_duplicated_canonical_rows(self):
        row = '| 0x0001 | pump_active | S | u8 |\n'
        variants = [self.MAP_TEXT + row.replace('0x0001', '0x0002'),
                    self.MAP_TEXT.replace(row, ''),
                    self.MAP_TEXT.replace('pump_active', 'pump_enabled'),
                    self.MAP_TEXT + row]
        for text in variants:
            with self.subTest(text=text):
                self.map_path.write_text(text)
                with self.assertRaises(ValueError):
                    contract.check(self.root)

    def test_operation_namespaces_remain_distinct(self):
        text = self.MAP_TEXT + self.MAP_TEXT.replace('OP=0x02', 'OP=0x06')
        self.assertEqual(len(contract.extract_registers(text)), 2)

    def test_unknown_inventory_entry(self):
        self.data['entries'].append(value('fan_active', [('fan', 'subject'), ('active', 'predicate')]))
        self.save()
        with self.assertRaises(ValueError):
            contract.check(self.root)

    def test_source_is_part_of_inventory_key(self):
        self.data['entries'][1]['source'] = 'protocols/synthetic.md'
        self.save()
        with self.assertRaises(ValueError):
            contract.check(self.root)

    def test_changed_and_removed_documented_examples(self):
        original = self.doc_path.read_text()
        for replacement in ['', '| `fan_active` | Value |\n']:
            self.doc_path.write_text(original.replace('| `pump_active` | Value |\n', replacement))
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                contract.check(self.root)

    def test_duplicate_documented_example(self):
        self.doc_path.write_text(self.doc_path.read_text() + '| `pump_active` | Value |\n')
        with self.assertRaises(ValueError):
            contract.check(self.root)

    def test_duplicate_inventory_entry(self):
        self.data['entries'].append(copy.deepcopy(self.data['entries'][0]))
        self.save()
        with self.assertRaises(ValueError):
            contract.check(self.root)

    def test_new_documented_example(self):
        self.doc_path.write_text(self.doc_path.read_text() + '| `fan_active` | Value |\n')
        with self.assertRaises(ValueError):
            contract.check(self.root)

    def test_repository_inventory(self):
        count, debt = contract.check()
        self.assertGreater(count, 0)
        self.assertGreater(debt, 0)


class GateTests(unittest.TestCase):
    def test_local_gate_runs_decomposition_guard_and_tests(self):
        gate = (Path(__file__).resolve().parents[1] / 'scripts/ci_local.sh').read_text(
            encoding='utf-8')
        self.assertIn('python3 scripts/check_name_decomposition.py --check\n', gate)
        self.assertIn('python3 -m pytest -q tests/test_name_decomposition.py\n', gate)


if __name__ == '__main__':
    unittest.main()
