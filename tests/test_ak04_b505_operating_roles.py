"""Independent finite declaration checks; no companion runtime is imported."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'protocols/vaillant/fixtures/ak04_b505_operating_roles.json'
PAGE = ROOT / 'protocols/vaillant/ebus-b505-operating-roles.md'
API = ROOT / 'architecture/ak04_b505_operating_roles_api.md'

# Literal acceptance expectations, independent of the declarations being checked.
EXPECTED = '''5A|room_setpoint|room|explicit_replacement_before_numeric
3D|day_setpoint|day|explicit_replacement_before_numeric
3D|night_setpoint|night|explicit_replacement_before_numeric
47|night_heating|inverter_indoor|night_room_heating
47|night_cooling|inverter_indoor|night_room_cooling
48|holiday_heating|inverter_indoor|holiday_room_heating
48|holiday_cooling|inverter_indoor|holiday_room_cooling
41|frost_protection|solar|off_replacement_code_unknown
40|minimum_temperature|second_solar_circuit|minimum_temperature
40|minimum_temperature|solid_fuel_boiler|minimum_temperature
10|maximum_preheat|heating|advance_before_first_period
3F|maximum_preheat|heating|advance_before_first_period
15|early_cutoff|heating|stop_demand_before_reduction
2B|early_cutoff|heating|stop_demand_before_reduction
3C|uncorrected_room|room|self_heating_without_user_correction
3C|corrected_room|room|self_heating_with_user_correction
1B|switch_on_difference|solar_tank_one|switch_on_difference
1B|cutoff_difference|solar_tank_one|cutoff_difference
1E|switch_on_difference|solar_tank_two|switch_on_difference
1E|cutoff_difference|solar_tank_two|cutoff_difference
38|switch_on_difference|solar_tank_three|switch_on_difference
38|cutoff_difference|solar_tank_three|cutoff_difference
1A|maximum_loading_temperature|solar_tank_one|maximum_loading_temperature
1D|maximum_loading_temperature|solar_tank_two|maximum_loading_temperature
37|maximum_loading_temperature|solar_tank_three|maximum_loading_temperature
31|ordinary_enable|dhw|one_permits_ordinary_blocked_frost_only
19|charging_enable|dhw_tank|one_enables_charging
27|charging_enable|dhw_tank|one_enables_charging
18|charging_disable|circuit|one_suppresses_without_parallel
27|charging_disable|circuit|one_suppresses_without_parallel
14|parallel_charging|mixer|mixer_exception_only
27|tank_flow_temperature|dhw|flow_temperature
2F|external_storage_sensor|storage|external_sensor_temperature
1C|outside_correction|outside|temperature_correction
26|hydraulic_schema|solar_controller|controller_specific_schema
23|duty_control|collector_pump|pump_duty
21|flow|collector_water|water_flow
22|reset|solar_pump_hours|one_requests_clear_hours
20|reset|solar_yield|one_requests_clear_yield
17|excess|demanded_flow|add_excess_to_demand
0F|maximum|flow_demand|maximum_flow_demand
0E|minimum|flow_demand|zero_is_off
12|overrun|charging_pump|retain_pump_inhibit_boiler_after_charging
11|recharge_delay|solar_charging|limit_recharge_delay
0D|pump_idle|heating|energy_saving_after_flow_exceeds_desired
0C|outside_cutoff|heating|select_summer_operation
01|day_setpoint|heating|room_temperature
01|day_setpoint|fixed_value|flow_temperature
01|day_setpoint|dhw|tank_temperature
0A|reduction|room|room_reduction
0A|reduction|fixed_flow|flow_reduction
09|first_period_start|programming|ignored_outside_mode_zero
07|saving|heating|zero_is_off
03|drying_day|floor_drying|zero_disables_drying'''
SPECS = [line.split('|') for line in EXPECTED.splitlines()]
AXES = [
    ('Ab16Family', 'string', 'family', 'vaillant', 'synthetic_family'),
    ('Ab16Variant', 'string', 'variant', 'B505', 'synthetic_variant'),
    ('Ab16Primary', 'uint8', 'primary', 181, 180),
    ('Ab16Secondary', '*uint8', 'secondary', 5, 0),
    ('Ab16Operation', '*uint8', 'operation', 90, 0),
    ('Ab16Direction', 'string', 'direction', 'request', 'response'),
    ('Ab16Field', 'string', 'field', 'room_setpoint', 'synthetic_field'),
    ('Ab16Alternative', 'string', 'alternative', 'room', 'synthetic_role'),
    ('Ab16Group', '*uint8', 'group', None, 0),
    ('Ab16InstanceScope', 'string', 'instance_scope', 'none', 'dynamic'),
    ('Ab16Register', '*uint16', 'register', None, 0),
]


def tables(text):
    groups = []
    for line in text.splitlines():
        if line.startswith('|'):
            if not groups or groups[-1] is None:
                groups.append([])
            groups[-1].append([c.strip() for c in line.strip('|').split('|')])
        elif groups and groups[-1] is not None:
            groups.append(None)
    return [g for g in groups if g is not None]


class OperatingRoles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text())
        cls.rows = cls.data['rows']
        cls.cases = cls.data['cases']
        cls.page = PAGE.read_text()
        cls.api = API.read_text()

    def test_every_native_identity_and_relation(self):
        self.assertEqual(len(self.rows), 54)
        self.assertEqual(len({r['id'] for r in self.rows}), 54)
        for row, (op, field, role, relation) in zip(self.rows, SPECS):
            with self.subTest(op=op, field=field, role=role):
                self.assertEqual(row['id'], f'ak04_{op.lower()}_{field}_{role}')
                self.assertEqual(row['identity'], {
                    'family': 'vaillant', 'variant': 'B505', 'primary': 181,
                    'secondary': 5, 'operation': int(op, 16),
                    'direction': 'request', 'field': field, 'alternative': role,
                    'group': None, 'instance_scope': 'none', 'register': None,
                })
                self.assertEqual(row['relation'], relation)

    def test_finite_native_table_independently(self):
        self.assertEqual(tables(self.page), [[
            ['Operation', 'Field', 'Role', 'Candidate relationship', 'Grade'],
            ['---'] * 5,
            *[[f'OP{op}', field, role, relation, 'Hypothesis']
              for op, field, role, relation in SPECS],
        ]])

    def test_raw_grade_and_unknowns(self):
        self.assertEqual(self.data['provenance'],
                         'synthetic; finite candidate relationships; no device observation')
        self.assertEqual((self.data['grade'], self.data['qualification']),
                         ('Hypothesis', 'Unknown'))
        for row, (op, field, role, _) in zip(self.rows, SPECS):
            with self.subTest(op=op, field=field, role=role):
                self.assertEqual((row['grade'], row['qualification']),
                                 ('Hypothesis', 'Unknown'))
                self.assertEqual(row['raw_form'], {
                    'token': f'synthetic:{op}:{field}:{role}', 'bytes': None})
                self.assertEqual(row['unknown'], {
                    'encoding': 'Unknown', 'offset': 'Unknown', 'width': 'Unknown',
                    'scale': 'Unknown', 'duration': 'Unknown',
                    'other_formulas': 'Unknown', 'raw_replacement_code': 'Unknown',
                    'native_support': 'Unknown', 'physical_effects': 'Unknown',
                    'acceptance': 'Unknown', 'persistence': 'Unknown',
                    'delivery': 'Unknown', 'enforcement': 'Unknown',
                })
        self.assertTrue({r['identity']['operation'] for r in self.rows}.isdisjoint(
            {0x32, 0x61, 0x4D, 0x4E}))

    def test_replacement_branches_before_conversion(self):
        self.assertEqual(self.cases['replacement'], [
            {'operation': op, 'field': field, 'replacement': flag, 'prior': prior,
             'input': value, 'raw_code': None,
             'output': prior if flag else value,
             'interpretation': 'retained' if flag else 'numeric_candidate',
             'scale': None}
            for op, field, prior, value in [
                ('5A', 'room_setpoint', 'prior-room-token', 23),
                ('3D', 'day_setpoint', 'prior-day-token', 21),
                ('3D', 'night_setpoint', 'prior-night-token', 17),
            ] for flag in [True, False]
        ])
        self.assertEqual(self.cases['frost_off'], {
            'operation': '41', 'replacement': 'off', 'raw_code': None,
            'candidate': 'off', 'execution': 'Unknown'})

    def test_four_independent_indoor_values(self):
        self.assertEqual(self.cases['indoor_setpoints'], {
            'night_heating': 17, 'night_cooling': 26,
            'holiday_heating': 13, 'holiday_cooling': 29})
        self.assertEqual(len(set(self.cases['indoor_setpoints'].values())), 4)

    def test_independent_solar_tank_tokens(self):
        self.assertEqual(self.cases['solar_tanks'], [
            {'tank': 'solar_tank_one', 'token': 'tank-alpha',
             'difference_operation': '1B', 'maximum_operation': '1A'},
            {'tank': 'solar_tank_two', 'token': 'tank-beta',
             'difference_operation': '1E', 'maximum_operation': '1D'},
            {'tank': 'solar_tank_three', 'token': 'tank-gamma',
             'difference_operation': '38', 'maximum_operation': '37'},
        ])

    def test_ordinary_dhw_keeps_frost_eligibility(self):
        self.assertEqual(self.cases['ordinary_dhw'], [
            {'enabled': False, 'ordinary_eligible': False,
             'frost_eligible': True, 'execution': 'Unknown'},
            {'enabled': True, 'ordinary_eligible': True,
             'frost_eligible': True, 'execution': 'Unknown'},
        ])

    def test_parallel_exception_is_mixer_only(self):
        expected = [
            ('18', 'mixer', False, True), ('18', 'mixer', True, False),
            ('18', 'direct', False, True), ('18', 'direct', True, True),
            ('27', 'mixer', False, True), ('27', 'mixer', True, False),
            ('27', 'direct', False, True), ('27', 'direct', True, True),
        ]
        self.assertEqual(self.cases['charge_disable'], [
            {'operation': op, 'disable': 1, 'role': role, 'parallel': parallel,
             'suppressed_candidate': suppressed}
            for op, role, parallel, suppressed in expected
        ])

    def test_semantic_addition_has_no_byte_encoding(self):
        self.assertEqual(self.cases['excess'], {
            'operation': '17', 'demand': 40, 'excess': 5,
            'candidate': 45, 'byte_encoding': None})
        self.assertEqual(self.cases['excess']['demand'] + self.cases['excess']['excess'], 45)

    def test_reset_requests_are_distinct_from_accepted_state(self):
        self.assertEqual(self.cases['resets'], [
            {'operation': '22', 'reset': 1, 'requested': 'clear_solar_pump_hours',
             'accepted': 'Unknown', 'persistent': 'Unknown'},
            {'operation': '20', 'reset': 1, 'requested': 'clear_solar_yield',
             'accepted': 'Unknown', 'persistent': 'Unknown'},
        ])

    def test_day_setpoint_all_circuit_classes(self):
        self.assertEqual(self.cases['day_setpoints'], [
            {'operation': '01', 'circuit': 'heating', 'input': 21,
             'quantity': 'room_temperature'},
            {'operation': '01', 'circuit': 'fixed_value', 'input': 21,
             'quantity': 'flow_temperature'},
            {'operation': '01', 'circuit': 'dhw', 'input': 21,
             'quantity': 'tank_temperature'},
        ])

    def test_programming_modes_hold_other_inputs_equal(self):
        self.assertEqual(self.cases['programming'], [
            {'operation': '09', 'mode': 0, 'first_period': 'period-alpha',
             'other_periods': ['period-beta', 'period-gamma'],
             'first_period_candidate': 'period-alpha'},
            {'operation': '09', 'mode': 1, 'first_period': 'period-alpha',
             'other_periods': ['period-beta', 'period-gamma'],
             'first_period_candidate': 'ignored'},
        ])

    def test_zero_is_off_or_disabled(self):
        self.assertEqual(self.cases['zero_controls'], [
            {'operation': '0E', 'input': 0, 'candidate': 'off'},
            {'operation': '07', 'input': 0, 'candidate': 'off'},
            {'operation': '03', 'input': 0, 'candidate': 'disabled'},
        ])

    def test_correction_and_partial_last_known_good(self):
        self.assertEqual(self.cases['room_correction'], [
            {'field': 'uncorrected_room', 'self_heating': True,
             'user_correction': False},
            {'field': 'corrected_room', 'self_heating': True,
             'user_correction': True},
        ])
        self.assertEqual(self.cases['partial_state'], {
            'prior': {'room': 'prior-room-token', 'flow': 'prior-flow-token'},
            'unresolved_update': {'room': None},
            'retained': {'room': 'prior-room-token', 'flow': 'prior-flow-token'},
            'admission': 'Unknown'})

    def test_exact_api_and_all_eleven_typed_axes(self):
        signatures = self.api.split('```go\n', 1)[1].split('```', 1)[0]
        self.assertEqual(signatures, 'func Ab16Entries() (json.RawMessage, error)\n'
                         'func Ab16Lookup(Ab16Key) (json.RawMessage, bool, error)\n')
        ts = tables(self.api)
        self.assertEqual(ts[0], [
            ['Field', 'Type', 'Native identity axis'], ['---'] * 3,
            *[[name, typ, axis] for name, typ, axis, _, _ in AXES],
        ])
        self.assertEqual(ts[1], [
            ['Field', 'Baseline', 'Independent miss'], ['---'] * 3,
            *[[name, json.dumps(base), json.dumps(miss)]
              for name, _, _, base, miss in AXES],
        ])
        self.assertEqual(ts[2], [
            ['Field', 'Absent control', 'Zero control', 'Cross-match'], ['---'] * 4,
            ['Ab16Secondary', 'null', '0', 'false'],
            ['Ab16Operation', 'null', '0', 'false'],
            ['Ab16Group', 'null', '0', 'false'],
            ['Ab16Register', 'null', '0', 'false'],
        ])
        self.assertEqual(ts[3], [
            ['Condition', 'Ab16Entries result', 'Ab16Lookup result'], ['---'] * 3,
            ['valid data / exact match', 'JSON array, nil', 'whole JSON row, true, nil'],
            ['valid data / missing exact key', 'JSON array, nil', 'nil, false, nil'],
            ['invalid embedded JSON', 'nil, error', 'nil, false, error'],
            ['duplicate complete key', 'nil, error', 'nil, false, error'],
        ])

    def test_api_ownership_fail_closed_and_unknown_boundaries(self):
        prose = ' '.join(self.api.split())
        for requirement in [
            'Package `vaillant`', 'Proven local API contract',
            '54 operation/field/role associations',
            'Match all eleven axes. No wildcard, nearest-key, cross-family, variant, direction, field or alternative fallback is permitted.',
            'Optional absent and explicit zero differ for Secondary, Operation, Group and Register.',
            'For each optional numeric axis independently, an otherwise identical key with that axis absent differs from the same key with explicit zero.',
            'An admitted absent control matches itself; an admitted zero control matches itself, but neither matches the other.',
            'Every call returns independent deep byte copies.',
            'Mutating any returned row or entries buffer cannot affect a later result, including calls through the other function.',
            "Embed the companion's owned JSON in its owned Go file; validate identity uniqueness before returning data.",
            'Production IDs and exported fields are ticket-prefixed.',
            'including its complete identity, stated fields/relations, candidate grade, explicit Unknown metadata and retained raw form.',
            'Admission fails closed;', 'partial last-known-good',
            'Native support, physical effects, persistence and delivery remain Unknown.',
            'Preserve eBUS MCP compatibility and GraphQL parity.',
            'AK03 must merge before this page.',
            'there is no dependency from the registry back to this page.',
            'Their merge does not qualify native behavior.',
            'runtime uniqueness, invalid-JSON errors and defensive-copy behavior require separate companion implementation evidence.',
        ]:
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, prose)

    def test_native_prose_boundaries(self):
        prose = ' '.join(self.page.split())
        for requirement in [
            '[B505 family contract](ebus-vaillant-B505.md)',
            'Qualification remains **Unknown**',
            'select an explicitly identified replacement branch before numeric conversion.',
            'The raw replacement code is **Unknown**',
            'OP41 has an off replacement whose raw code is also **Unknown**.',
            'OP10 and OP3F advance heating before the first period.',
            'OP15 and OP2B stop demand before the reduction period.',
            'OP3C uncorrected room temperature includes self-heating and excludes user correction; corrected room temperature includes both.',
            'OP14 provides a mixer exception;',
            'OP22 reset=1 requests clearing solar-pump hours.',
            'OP20 reset=1 requests clearing yield.',
            'zero meaning off rather than a positive minimum.',
            'Unprovided encodings, offsets, widths, scales, durations, other formulas and enforcement remain **Unknown**.',
            'independent partial last-known-good values',
        ]:
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, prose)
        for excluded in ['Ab16', 'GraphQL', 'MCP', 'OP32', 'OP61', 'OP4D', 'OP4E', '8000']:
            self.assertNotIn(excluded, self.page)
            self.assertNotIn(excluded, DATA.read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
