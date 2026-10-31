"""Offline contract checks; these helpers do not implement a runtime feature."""
import copy
import json
import os
from pathlib import Path
import unittest


ROOT = Path(os.environ.get('AJ18_CONTRACT_ROOT', Path(__file__).resolve().parents[1]))
BASE = dict(slot_index=2, participant_address='76', route_address='08', spn=375,
            family_match=True, record_match=True, generic_heat_generator_class=3,
            other_classifier=3, registered=True, capability=True, eligibility=1,
            failure=None)
# Literal independent controls, rather than expectations calculated from fixture inputs.
CONTROLS = {
    'base': ({}, True, True, False),
    'participant': ({'participant_address': '78'}, False, True, False),
    'spn': ({'spn': 376}, False, True, False),
    'family_false': ({'family_match': False}, False, True, False),
    'record_false': ({'record_match': False}, False, True, False),
    'family_unknown': ({'family_match': None}, False, True, False),
    'record_unknown': ({'record_match': None}, False, True, False),
    'generic_other': ({'generic_heat_generator_class': 9}, True, True, False),
    'other_classifier': ({'other_classifier': 9}, True, True, False),
    'slot': ({'slot_index': 5}, True, True, False),
    'route': ({'route_address': '18'}, True, True, False),
    'failure': ({'failure': 'synthetic_failure'}, True, True, False),
    'eligibility': ({'eligibility': 0}, True, True, False),
    'class_alone': ({'participant_address': '78', 'spn': 376,
                     'family_match': False, 'record_match': False}, False, True, False),
    'unregistered': ({'registered': False}, True, False, False),
    'incapable': ({'capability': False}, True, False, False),
    'limit': ({}, True, True, True),
    'limit_unregistered': ({'registered': False}, True, False, True),
    'limit_incapable': ({'capability': False}, True, False, True),
}


def table(page, header):
    """Read a Markdown table so documentation edits participate in the checks."""
    lines = page.splitlines()
    start = lines.index(header)
    rows = []
    for line in lines[start + 2:]:
        if not line.startswith('|'):
            break
        rows.append([cell.strip() for cell in line.strip('|').split('|')])
    return rows


class TargetsStatusContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'architecture/fixtures/aj18_b531_targets_status.json').read_text())
        cls.page = (ROOT / 'architecture/aj18_b531_targets_status.md').read_text()

    def test_grades_and_unknowns(self):
        self.assertEqual(self.data['grade'], 'Hypothesis')
        self.assertEqual(self.data['qualification'], 'Unknown')
        self.assertEqual(self.data['unknowns'], dict(family_prefix=None, record_matcher=None,
                         native_behavior=None, status_encoding=None, physical_unit=None))
        for text in ('**Hypothesis**', '**Unknown**', 'unconfirmed on the wire',
                     '../protocols/vaillant/ebus-vaillant-B531-hem-power-limit.md',
                     'exact family prefix', 'record matcher are Unknown',
                     'no authorization gate is introduced before 0.9', 'roadmap wording is 0.11',
                     'no new major or experimental namespace', 'GraphQL parity',
                     'eBUS MCP', 'adds no publisher, route registration, active limit request'):
            self.assertIn(text, self.page)

    def test_predicate_table(self):
        self.assertEqual(table(self.page, '| Predicate | Required for marker 1 | Unknown treatment |'), [
            ['participant_address', '76 hex', 'deny marker 1'],
            ['spn', '375 decimal', 'deny marker 1'],
            ['family_match', 'true', 'deny marker 1'],
            ['record_match', 'true', 'deny marker 1']])

    def test_publication_table(self):
        self.assertEqual(table(self.page, '| registered | capability | device entry |'), [
            ['true', 'true', 'present'], ['true', 'false', 'absent'],
            ['false', 'true', 'absent'], ['false', 'false', 'absent']])

    def test_scenarios_and_independent_axes(self):
        cases = self.data['cases']
        self.assertEqual(len(cases), len(CONTROLS))
        self.assertEqual({c['name'] for c in cases}, set(CONTROLS))
        for case in cases:
            with self.subTest(case=case['name']):
                changes, marker, entry, limit = CONTROLS[case['name']]
                self.assertEqual(case['slot'], BASE | changes)
                self.assertIs(case['expected']['marker_1'], marker)
                self.assertIs(case['expected']['entry'], entry)
                self.assertIs(case['limit_present'], limit)
                fields = ['participant_address', 'route_address']
                if limit:
                    fields += ['power_limit']
                fields += ['min', 'max']
                self.assertEqual(case['expected']['fields'], fields if entry else [])
                self.assertEqual(case['raw'], {'power_limit': 7, 'min': 2, 'max': 11})

    def test_status_table_and_raw_independence(self):
        fields = ['lpc_effective', 'lpc_possible', 'lpc_active', 'lpc_device_status']
        self.assertEqual(table(self.page, '| Status field | Treatment | Grade |'),
                         [[f, 'retain raw independently', 'Hypothesis'] for f in fields])
        self.assertEqual(self.data['status'], dict(zip(fields, [2, 7, 0, 9])))
        self.assertEqual(self.data['status_variants'],
                         [dict(field=f, value=v) for f, v in zip(fields, [3, 8, 1, 10])])
        for variant in self.data['status_variants']:
            projected = copy.deepcopy(self.data['status'])
            projected[variant['field']] = variant['value']
            self.assertEqual(sum(projected[f] != self.data['status'][f] for f in fields), 1)

    def test_transition_table(self):
        self.assertEqual(table(self.page, '| Observation | Local acknowledgement | Receipt | Delivery | Materialized state |'), [
            [name, 'true', 'Unknown', 'Unknown', state] for name, state in [
                ('connection denial', 'prior retained in fixture'),
                ('membership denial', 'prior retained in fixture'),
                ('restriction denial', 'prior retained in fixture'),
                ('duplicate', 'prior retained in fixture'),
                ('local control', 'partial update in fixture')]])

    def test_transitions_against_literal_observations(self):
        controls = {
            'connection_denial': ({'connection': False}, True, 5),
            'membership_denial': ({'membership': False}, True, 5),
            'restriction_denial': ({'restriction_allowed': False}, True, 5),
            'duplicate': ({'duplicate': True}, True, 5),
            'local_control': ({}, True, 7),
            'no_ack': ({'acknowledgement': False}, False, 7),
            'startup_zero': ({'startup_restriction': 0}, True, 7),
            'control_true': ({'subsequent_control': True}, True, 7),
        }
        self.assertEqual(len(self.data['transitions']), len(controls))
        self.assertEqual({r['name'] for r in self.data['transitions']}, set(controls))
        for row in self.data['transitions']:
            with self.subTest(transition=row['name']):
                changes, ack, limit = controls[row['name']]
                self.assertEqual(row['inputs'], dict(acknowledgement=True, connection=True,
                                 membership=True, restriction_allowed=True, duplicate=False,
                                 startup_restriction=1, subsequent_control=False) | changes)
                self.assertEqual(row['prior'], {'power_limit': 5, 'min': 2, 'max': 11})
                self.assertEqual(row['proposed'], {'power_limit': 7})
                self.assertEqual(row['expected'], dict(local_acknowledgement=ack,
                                 receipt='Unknown', delivery='Unknown',
                                 materialized={'power_limit': limit, 'min': 2, 'max': 11}))

    def test_partial_values_and_raw_arithmetic(self):
        self.assertEqual(self.data['arithmetic'], dict(raw_min=2, raw_max=11,
                         expected_span=9, physical_unit='Unknown'))
        self.assertEqual(self.data['arithmetic']['raw_max'] - self.data['arithmetic']['raw_min'], 9)
        rows = self.data['partial_observations']
        self.assertEqual([r['name'] for r in rows], ['limit_only', 'min_only', 'max_only'])
        expected = [{'power_limit': 7, 'min': 2, 'max': 11},
                    {'power_limit': 5, 'min': 3, 'max': 11},
                    {'power_limit': 5, 'min': 2, 'max': 13}]
        for row, observed, result in zip(rows, [{'power_limit': 7}, {'min': 3}, {'max': 13}], expected):
            self.assertEqual(row['prior'], {'power_limit': 5, 'min': 2, 'max': 11})
            self.assertEqual(row['observed'], observed)
            self.assertEqual(row['expected'], result)
            self.assertEqual(row['prior'] | row['observed'], result)


if __name__ == '__main__':
    unittest.main()
