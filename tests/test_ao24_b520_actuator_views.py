"""Contract checks of the page case table and fixture; no interpreter lives here."""

import copy
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/ao24_b520_actuator_views.md'
FIXTURE = ROOT / 'architecture/fixtures/ao24_b520_actuator_views.json'
P = 'ab23ao23_'
SIGNATURE = ('func Ab23Ao23Interpret(ab23ao23Input json.RawMessage) '
             '(json.RawMessage, error)')

# id -> (field, state, number, label, candidate_domain); hand-written constants.
EXPECTED = {
    'req_zero': ('stepper', 'ok', 0, 'steps', None),
    'req_pwm_ed_ff': ('pwm1', 'ok', 127.5, None, True),
    'req_stepper_240': ('stepper', 'ok', 240, 'steps', None),
    'req_stepper_241': ('stepper', 'unmapped', None, None, None),
    'req_stepper_254': ('stepper', 'unmapped', None, None, None),
    'req_stepper_255': ('stepper', 'ok', None, 'calibrate_go_to_zero', None),
    'req_led_0': ('led', 'ok', None, 'disabled', None),
    'req_led_1': ('led', 'ok', None, 'enabled', None),
    'req_led_2': ('led', 'unmapped', None, None, None),
    'req_table_0': ('temperature_table', 'ok', None, 'standard_3k3', None),
    'req_table_1': ('temperature_table', 'ok', None, 'extended_1k', None),
    'req_table_2': ('temperature_table', 'ok', None, 'low_temperature_15k', None),
    'req_table_3': ('temperature_table', 'ok', None, 'standard_1k', None),
    'req_table_4': ('temperature_table', 'unmapped', None, None, None),
    'pos_adc_1023': ('adc', 'ok', 1023, None, True),
    'pos_adc_1024': ('adc', 'ok', 1024, None, False),
    'pos_temperature_1_000c': ('temperature_1', 'ok', 192, None, True),
    'pos_temperature_2_ffff': ('temperature_2', 'ok', -0.0625, None, False),
    'pos_temperature_3_zero': ('temperature_3', 'ok', 0, None, True),
    'pos_temperature_4_max': ('temperature_4', 'ok', 200, None, True),
    'pos_temperature_1_over': ('temperature_1', 'ok', 200.0625, None, False),
    'pos_vortex_0': ('vortex_hz', 'ok', 0, None, True),
    'pos_vortex_4': ('vortex_hz', 'ok', 4, None, True),
    'pos_vortex_5': ('vortex_hz', 'ok', 5, None, True),
    'pos_vortex_350': ('vortex_hz', 'ok', 350, None, True),
    'pos_vortex_351': ('vortex_hz', 'ok', 351, None, False),
    'pos_impeller_1000': ('impeller_hz', 'ok', 1000, None, True),
    'pos_impeller_1001': ('impeller_hz', 'ok', 1001, None, False),
}
VORTEX_FLAGS = {0: (True, False), 4: (True, False), 5: (True, True),
                350: (True, True), 351: (False, False)}
DISTINCT_TEMPERATURES = {'temperature_1': 192, 'temperature_2': 128,
                         'temperature_3': 64, 'temperature_4': 16}
ENDS = {
    'request': [('prefix', 3), ('relay', 4), ('pwm1', 5), ('pwm2', 6),
                ('stepper', 7), ('led', 8), ('ed', 9), ('temperature_table', 10)],
    'positive': [('prefix', 3), ('adc', 5), ('temperature_1', 7),
                 ('temperature_2', 9), ('temperature_3', 11),
                 ('temperature_4', 13), ('reserved', 14), ('impeller_hz', 16),
                 ('vortex_hz', 18)],
}
TABLES = {'0': ('standard_3k3', -13.5, 116), '1': ('extended_1k', -20, 155),
          '2': ('low_temperature_15k', -39, 80), '3': ('standard_1k', -13.9, 130)}
REQUIRED_KEYS = ['primary', 'secondary', 'operation', 'direction', 'view']
INPUT_KEYS = ['context', 'fields', 'arguments']
RESULT_STATES = ['complete', 'partial', 'unknown']
FIELD_STATES = ['ok', 'unmapped', 'incomplete', 'missing', 'opaque']
CALCULATION_FIELDS = {'request': ['pwm1', 'pwm2', 'ed'],
                      'positive': ['temperature_1', 'temperature_2',
                                   'temperature_3', 'temperature_4']}
# word kind -> (number, candidate_domain); the same for each of the four sensors.
TEMPERATURE_WORDS = {'000c': (192, True), 'ffff': (-0.0625, False),
                     'zero': (0, True), 'max': (200, True), 'over': (200.0625, False)}
# Bytes beyond the logical extent are retained and never change the state.
TAIL_CASES = {
    'req_relay_tail': ('relay', {'state': 'ok', 'number': 7}),
    'pos_tail': ('vortex_hz', {'state': 'ok', 'number': 0, 'candidate_domain': True,
                               'flags': {'formal_domain': True,
                                         'operational_window': False}}),
}
ERROR_IDS = ['malformed', 'duplicate_top_key', 'duplicate_field_key',
             'byte_256', 'byte_negative', 'byte_fraction', 'byte_string',
             'field_not_array', 'fields_not_object', 'context_missing',
             'operation_string', 'arguments_nested',
             'primary_string', 'secondary_string', 'direction_number',
             'view_number', 'primary_missing', 'secondary_missing',
             'operation_missing', 'direction_missing', 'view_missing',
             'fields_missing']
UNKNOWN_IDS = ['operation', 'direction', 'view', 'primary', 'secondary']
CONTROL_CONTEXT = {'primary': 181, 'secondary': 32, 'operation': 0,
                   'direction': 'request', 'view': 'logical_object'}
# Truncation cases n = 0..extent carry the first n bytes of these reference objects.
TRUNCATION_REFERENCE = {
    'request': [161, 178, 195, 1, 2, 3, 4, 1, 6, 2],
    'positive': [161, 178, 195, 2, 1, 0, 12, 0, 8, 0, 4, 0, 1, 126, 3, 2, 100, 0],
}
# Unknown cases vary exactly one context axis of the control context.
UNKNOWN_VARIED = {'operation': 1, 'direction': 'response', 'view': 'payload_length_10',
                  'primary': 180, 'secondary': 33}
# Error inputs; CONTROL_TEXT is the control context as compact JSON text.
CONTROL_TEXT = json.dumps(CONTROL_CONTEXT, separators=(',', ':'))
ERROR_TEXTS = {
    'malformed': '{"context":',
    'duplicate_top_key': '{"context":{},"context":{},"fields":{}}',
    'duplicate_field_key': '{"context":%s,"fields":{"logical_object":[],"logical_object":[]}}' % CONTROL_TEXT,
    'byte_256': '{"context":%s,"fields":{"logical_object":[256]}}' % CONTROL_TEXT,
    'byte_negative': '{"context":%s,"fields":{"logical_object":[-1]}}' % CONTROL_TEXT,
    'byte_fraction': '{"context":%s,"fields":{"logical_object":[1.5]}}' % CONTROL_TEXT,
    'byte_string': '{"context":%s,"fields":{"logical_object":["1"]}}' % CONTROL_TEXT,
    'field_not_array': '{"context":%s,"fields":{"logical_object":5}}' % CONTROL_TEXT,
    'fields_not_object': '{"context":%s,"fields":[]}' % CONTROL_TEXT,
    'context_missing': '{"fields":{}}',
    'operation_string': '{"context":{"primary":181,"secondary":32,"operation":"0","direction":"request","view":"logical_object"},"fields":{}}',
    'arguments_nested': '{"context":%s,"fields":{},"arguments":{"flag":[true]}}' % CONTROL_TEXT,
    'primary_string': '{"context":{"primary":"181","secondary":32,"operation":0,"direction":"request","view":"logical_object"},"fields":{}}',
    'secondary_string': '{"context":{"primary":181,"secondary":"32","operation":0,"direction":"request","view":"logical_object"},"fields":{}}',
    'direction_number': '{"context":{"primary":181,"secondary":32,"operation":0,"direction":5,"view":"logical_object"},"fields":{}}',
    'view_number': '{"context":{"primary":181,"secondary":32,"operation":0,"direction":"request","view":5},"fields":{}}',
    'primary_missing': '{"context":{"secondary":32,"operation":0,"direction":"request","view":"logical_object"},"fields":{}}',
    'secondary_missing': '{"context":{"primary":181,"operation":0,"direction":"request","view":"logical_object"},"fields":{}}',
    'operation_missing': '{"context":{"primary":181,"secondary":32,"direction":"request","view":"logical_object"},"fields":{}}',
    'direction_missing': '{"context":{"primary":181,"secondary":32,"operation":0,"view":"logical_object"},"fields":{}}',
    'view_missing': '{"context":{"primary":181,"secondary":32,"operation":0,"direction":"request"},"fields":{}}',
    'fields_missing': '{"context":%s}' % CONTROL_TEXT,
}
# Every case of the page table: (id suffix, direction, logical object, result state, fields).
CASES = [
    ('req_zero', 'request', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'relay': {'state': 'ok', 'number': 0},
        'pwm1': {'state': 'ok', 'number': 0, 'candidate_domain': True, 'calculation': 'Proven'},
        'pwm2': {'state': 'ok', 'number': 0, 'candidate_domain': True, 'calculation': 'Proven'},
        'stepper': {'state': 'ok', 'number': 0, 'label': 'steps'},
        'led': {'state': 'ok', 'label': 'disabled'},
        'ed': {'state': 'ok', 'number': 0, 'candidate_domain': True, 'calculation': 'Proven'},
        'temperature_table': {'state': 'ok', 'label': 'standard_3k3'},
    }),
    ('req_pwm_ed_ff', 'request', [161, 178, 195, 1, 255, 255, 0, 0, 255, 0], 'complete', {
        'relay': {'state': 'ok', 'number': 1},
        'pwm1': {'state': 'ok', 'number': 127.5, 'candidate_domain': True, 'calculation': 'Proven'},
        'pwm2': {'state': 'ok', 'number': 127.5, 'candidate_domain': True, 'calculation': 'Proven'},
        'ed': {'state': 'ok', 'number': 127.5, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('req_pwm_distinct', 'request', [161, 178, 195, 0, 100, 60, 0, 0, 20, 0], 'complete', {
        'pwm1': {'state': 'ok', 'number': 50, 'candidate_domain': True, 'calculation': 'Proven'},
        'pwm2': {'state': 'ok', 'number': 30, 'candidate_domain': True, 'calculation': 'Proven'},
        'ed': {'state': 'ok', 'number': 10, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('req_stepper_240', 'request', [161, 178, 195, 0, 0, 0, 240, 0, 0, 0], 'complete', {
        'stepper': {'state': 'ok', 'number': 240, 'label': 'steps'},
    }),
    ('req_stepper_241', 'request', [161, 178, 195, 0, 0, 0, 241, 0, 0, 0], 'complete', {
        'stepper': {'state': 'unmapped'},
    }),
    ('req_stepper_254', 'request', [161, 178, 195, 0, 0, 0, 254, 0, 0, 0], 'complete', {
        'stepper': {'state': 'unmapped'},
    }),
    ('req_stepper_255', 'request', [161, 178, 195, 0, 0, 0, 255, 0, 0, 0], 'complete', {
        'stepper': {'state': 'ok', 'label': 'calibrate_go_to_zero'},
    }),
    ('req_led_0', 'request', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'led': {'state': 'ok', 'label': 'disabled'},
    }),
    ('req_led_1', 'request', [161, 178, 195, 0, 0, 0, 0, 1, 0, 0], 'complete', {
        'led': {'state': 'ok', 'label': 'enabled'},
    }),
    ('req_led_2', 'request', [161, 178, 195, 0, 0, 0, 0, 2, 0, 0], 'complete', {
        'led': {'state': 'unmapped'},
    }),
    ('req_table_0', 'request', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_table': {'state': 'ok', 'label': 'standard_3k3'},
    }),
    ('req_table_1', 'request', [161, 178, 195, 0, 0, 0, 0, 0, 0, 1], 'complete', {
        'temperature_table': {'state': 'ok', 'label': 'extended_1k'},
    }),
    ('req_table_2', 'request', [161, 178, 195, 0, 0, 0, 0, 0, 0, 2], 'complete', {
        'temperature_table': {'state': 'ok', 'label': 'low_temperature_15k'},
    }),
    ('req_table_3', 'request', [161, 178, 195, 0, 0, 0, 0, 0, 0, 3], 'complete', {
        'temperature_table': {'state': 'ok', 'label': 'standard_1k'},
    }),
    ('req_table_4', 'request', [161, 178, 195, 0, 0, 0, 0, 0, 0, 4], 'complete', {
        'temperature_table': {'state': 'unmapped'},
    }),
    ('req_relay_tail', 'request', [161, 178, 195, 7, 0, 0, 0, 0, 0, 0, 238, 1], 'complete', {
        'relay': {'state': 'ok', 'number': 7},
    }),
    ('pos_adc_1023', 'positive', [161, 178, 195, 255, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'adc': {'state': 'ok', 'number': 1023, 'candidate_domain': True},
    }),
    ('pos_adc_1024', 'positive', [161, 178, 195, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'adc': {'state': 'ok', 'number': 1024, 'candidate_domain': False},
    }),
    ('pos_temperature_1_000c', 'positive', [161, 178, 195, 0, 0, 0, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_1': {'state': 'ok', 'number': 192, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('pos_temperature_2_000c', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_2': {'state': 'ok', 'number': 192, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('pos_temperature_3_000c', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 12, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_3': {'state': 'ok', 'number': 192, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('pos_temperature_4_000c', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 12, 0, 0, 0, 0, 0], 'complete', {
        'temperature_4': {'state': 'ok', 'number': 192, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('pos_temperature_1_ffff', 'positive', [161, 178, 195, 0, 0, 255, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_1': {'state': 'ok', 'number': -0.0625, 'candidate_domain': False, 'calculation': 'Proven'},
    }),
    ('pos_temperature_2_ffff', 'positive', [161, 178, 195, 0, 0, 0, 0, 255, 255, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_2': {'state': 'ok', 'number': -0.0625, 'candidate_domain': False, 'calculation': 'Proven'},
    }),
    ('pos_temperature_3_ffff', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 255, 255, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_3': {'state': 'ok', 'number': -0.0625, 'candidate_domain': False, 'calculation': 'Proven'},
    }),
    ('pos_temperature_4_ffff', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 255, 255, 0, 0, 0, 0, 0], 'complete', {
        'temperature_4': {'state': 'ok', 'number': -0.0625, 'candidate_domain': False, 'calculation': 'Proven'},
    }),
    ('pos_temperature_1_zero', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_1': {'state': 'ok', 'number': 0, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('pos_temperature_2_zero', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_2': {'state': 'ok', 'number': 0, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('pos_temperature_3_zero', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_3': {'state': 'ok', 'number': 0, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('pos_temperature_4_zero', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_4': {'state': 'ok', 'number': 0, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('pos_temperature_1_max', 'positive', [161, 178, 195, 0, 0, 128, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_1': {'state': 'ok', 'number': 200, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('pos_temperature_2_max', 'positive', [161, 178, 195, 0, 0, 0, 0, 128, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_2': {'state': 'ok', 'number': 200, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('pos_temperature_3_max', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 128, 12, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_3': {'state': 'ok', 'number': 200, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('pos_temperature_4_max', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 128, 12, 0, 0, 0, 0, 0], 'complete', {
        'temperature_4': {'state': 'ok', 'number': 200, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('pos_temperature_1_over', 'positive', [161, 178, 195, 0, 0, 129, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_1': {'state': 'ok', 'number': 200.0625, 'candidate_domain': False, 'calculation': 'Proven'},
    }),
    ('pos_temperature_2_over', 'positive', [161, 178, 195, 0, 0, 0, 0, 129, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_2': {'state': 'ok', 'number': 200.0625, 'candidate_domain': False, 'calculation': 'Proven'},
    }),
    ('pos_temperature_3_over', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 129, 12, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'temperature_3': {'state': 'ok', 'number': 200.0625, 'candidate_domain': False, 'calculation': 'Proven'},
    }),
    ('pos_temperature_4_over', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 129, 12, 0, 0, 0, 0, 0], 'complete', {
        'temperature_4': {'state': 'ok', 'number': 200.0625, 'candidate_domain': False, 'calculation': 'Proven'},
    }),
    ('pos_temperature_distinct', 'positive', [161, 178, 195, 0, 0, 0, 12, 0, 8, 0, 4, 0, 1, 0, 0, 0, 0, 0], 'complete', {
        'temperature_1': {'state': 'ok', 'number': 192, 'candidate_domain': True, 'calculation': 'Proven'},
        'temperature_2': {'state': 'ok', 'number': 128, 'candidate_domain': True, 'calculation': 'Proven'},
        'temperature_3': {'state': 'ok', 'number': 64, 'candidate_domain': True, 'calculation': 'Proven'},
        'temperature_4': {'state': 'ok', 'number': 16, 'candidate_domain': True, 'calculation': 'Proven'},
    }),
    ('pos_vortex_0', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'vortex_hz': {'state': 'ok', 'number': 0, 'candidate_domain': True, 'flags': {'formal_domain': True, 'operational_window': False}},
    }),
    ('pos_vortex_4', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0], 'complete', {
        'vortex_hz': {'state': 'ok', 'number': 4, 'candidate_domain': True, 'flags': {'formal_domain': True, 'operational_window': False}},
    }),
    ('pos_vortex_5', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0], 'complete', {
        'vortex_hz': {'state': 'ok', 'number': 5, 'candidate_domain': True, 'flags': {'formal_domain': True, 'operational_window': True}},
    }),
    ('pos_vortex_350', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 94, 1], 'complete', {
        'vortex_hz': {'state': 'ok', 'number': 350, 'candidate_domain': True, 'flags': {'formal_domain': True, 'operational_window': True}},
    }),
    ('pos_vortex_351', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 95, 1], 'complete', {
        'vortex_hz': {'state': 'ok', 'number': 351, 'candidate_domain': False, 'flags': {'formal_domain': False, 'operational_window': False}},
    }),
    ('pos_impeller_0', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'impeller_hz': {'state': 'ok', 'number': 0, 'candidate_domain': True},
    }),
    ('pos_impeller_1000', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 232, 3, 0, 0], 'complete', {
        'impeller_hz': {'state': 'ok', 'number': 1000, 'candidate_domain': True},
    }),
    ('pos_impeller_1001', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 233, 3, 0, 0], 'complete', {
        'impeller_hz': {'state': 'ok', 'number': 1001, 'candidate_domain': False},
    }),
    ('pos_reserved_0', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'complete', {
        'reserved': {'state': 'ok', 'reserved': 0},
    }),
    ('pos_reserved_1', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0], 'complete', {
        'reserved': {'state': 'ok', 'reserved': 1},
    }),
    ('pos_reserved_255', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 0, 0, 0, 0], 'complete', {
        'reserved': {'state': 'ok', 'reserved': 255},
    }),
    ('pos_distinct_all', 'positive', [161, 178, 195, 2, 1, 0, 12, 0, 8, 0, 4, 0, 1, 126, 3, 2, 100, 0], 'complete', {
        'prefix': {'state': 'opaque'},
        'adc': {'state': 'ok', 'number': 258, 'candidate_domain': True},
        'temperature_1': {'state': 'ok', 'number': 192, 'candidate_domain': True, 'calculation': 'Proven'},
        'temperature_2': {'state': 'ok', 'number': 128, 'candidate_domain': True, 'calculation': 'Proven'},
        'temperature_3': {'state': 'ok', 'number': 64, 'candidate_domain': True, 'calculation': 'Proven'},
        'temperature_4': {'state': 'ok', 'number': 16, 'candidate_domain': True, 'calculation': 'Proven'},
        'reserved': {'state': 'ok', 'reserved': 126},
        'impeller_hz': {'state': 'ok', 'number': 515, 'candidate_domain': True},
        'vortex_hz': {'state': 'ok', 'number': 100, 'candidate_domain': True, 'flags': {'formal_domain': True, 'operational_window': True}},
    }),
    ('pos_tail', 'positive', [161, 178, 195, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 85], 'complete', {
        'vortex_hz': {'state': 'ok', 'number': 0, 'candidate_domain': True, 'flags': {'formal_domain': True, 'operational_window': False}},
    }),
]
FIXTURE_META = {
    'schema': 'ab23ao23_synthetic_tuples',
    'provenance': 'synthetic; finite software API tuples only; no device observation',
    'qualification': 'Unknown',
    'context': {'primary': 181, 'secondary': 32, 'operation': 0, 'view': 'logical_object'},
}
# (case id suffix, field) of every fixture tuple, in fixture order.
FIXTURE_ROWS = [
    ('req_zero', 'relay'), ('req_zero', 'pwm1'), ('req_zero', 'pwm2'), ('req_zero', 'stepper'),
    ('req_zero', 'led'), ('req_zero', 'ed'), ('req_zero', 'temperature_table'),
    ('req_pwm_ed_ff', 'relay'), ('req_pwm_ed_ff', 'pwm1'), ('req_pwm_ed_ff', 'pwm2'),
    ('req_pwm_ed_ff', 'ed'), ('req_pwm_distinct', 'pwm1'), ('req_pwm_distinct', 'pwm2'),
    ('req_pwm_distinct', 'ed'), ('req_stepper_240', 'stepper'), ('req_stepper_241', 'stepper'),
    ('req_stepper_254', 'stepper'), ('req_stepper_255', 'stepper'), ('req_led_0', 'led'),
    ('req_led_1', 'led'), ('req_led_2', 'led'), ('req_table_0', 'temperature_table'),
    ('req_table_1', 'temperature_table'), ('req_table_2', 'temperature_table'),
    ('req_table_3', 'temperature_table'), ('req_table_4', 'temperature_table'),
    ('req_relay_tail', 'relay'), ('pos_adc_1023', 'adc'), ('pos_adc_1024', 'adc'),
    ('pos_temperature_1_000c', 'temperature_1'), ('pos_temperature_2_000c', 'temperature_2'),
    ('pos_temperature_3_000c', 'temperature_3'), ('pos_temperature_4_000c', 'temperature_4'),
    ('pos_temperature_1_ffff', 'temperature_1'), ('pos_temperature_2_ffff', 'temperature_2'),
    ('pos_temperature_3_ffff', 'temperature_3'), ('pos_temperature_4_ffff', 'temperature_4'),
    ('pos_temperature_1_zero', 'temperature_1'), ('pos_temperature_2_zero', 'temperature_2'),
    ('pos_temperature_3_zero', 'temperature_3'), ('pos_temperature_4_zero', 'temperature_4'),
    ('pos_temperature_1_max', 'temperature_1'), ('pos_temperature_2_max', 'temperature_2'),
    ('pos_temperature_3_max', 'temperature_3'), ('pos_temperature_4_max', 'temperature_4'),
    ('pos_temperature_1_over', 'temperature_1'), ('pos_temperature_2_over', 'temperature_2'),
    ('pos_temperature_3_over', 'temperature_3'), ('pos_temperature_4_over', 'temperature_4'),
    ('pos_temperature_distinct', 'temperature_1'),
    ('pos_temperature_distinct', 'temperature_2'),
    ('pos_temperature_distinct', 'temperature_3'),
    ('pos_temperature_distinct', 'temperature_4'), ('pos_vortex_0', 'vortex_hz'),
    ('pos_vortex_4', 'vortex_hz'), ('pos_vortex_5', 'vortex_hz'),
    ('pos_vortex_350', 'vortex_hz'), ('pos_vortex_351', 'vortex_hz'),
    ('pos_impeller_0', 'impeller_hz'), ('pos_impeller_1000', 'impeller_hz'),
    ('pos_impeller_1001', 'impeller_hz'), ('pos_reserved_0', 'reserved'),
    ('pos_reserved_1', 'reserved'), ('pos_reserved_255', 'reserved'),
    ('pos_distinct_all', 'prefix'), ('pos_distinct_all', 'adc'),
    ('pos_distinct_all', 'temperature_1'), ('pos_distinct_all', 'temperature_2'),
    ('pos_distinct_all', 'temperature_3'), ('pos_distinct_all', 'temperature_4'),
    ('pos_distinct_all', 'reserved'), ('pos_distinct_all', 'impeller_hz'),
    ('pos_distinct_all', 'vortex_hz'), ('pos_tail', 'vortex_hz'),
]


def load_page_contract():
    text = PAGE.read_text()
    blocks = re.findall(r'```json\n(.*?)\n```', text, re.S)
    assert len(blocks) == 1
    return json.loads(blocks[0])


def pairs_hook(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError('duplicate key')
    return dict(pairs)


def input_is_invalid(text):
    """Independent validity predicate for the error table, not an interpreter."""
    try:
        doc = json.loads(text, object_pairs_hook=pairs_hook)
    except ValueError:
        return True
    if not isinstance(doc, dict) or not isinstance(doc.get('context'), dict):
        return True
    ctx = doc['context']
    if any(k not in ctx for k in REQUIRED_KEYS):
        return True
    if any(type(ctx[k]) is not int for k in ('primary', 'secondary', 'operation')):
        return True
    if any(not isinstance(ctx[k], str) for k in ('direction', 'view')):
        return True
    if not isinstance(doc.get('fields'), dict):
        return True
    for arr in doc['fields'].values():
        if not isinstance(arr, list):
            return True
        for b in arr:
            if type(b) is not int or not 0 <= b <= 255:
                return True
    for v in doc.get('arguments', {}).values():
        if type(v) not in (bool, int):
            return True
    return False


def canonical(obj):
    """Exact, type-faithful text of a structure (true is not 1, 0 is not 0.0)."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def expected_contract():
    """The complete page contract, built only from the constants above."""
    starts = {d: [0] + [end for _, end in ends[:-1]] for d, ends in ENDS.items()}
    truncation = []
    for d, ends in ENDS.items():
        extent = ends[-1][1]
        for n in range(extent + 1):
            truncation.append({
                'id': '%strunc_%s_%d' % (P, d, n), 'direction': d,
                'logical_object': TRUNCATION_REFERENCE[d][:n],
                'expect': {'state': 'complete' if n >= extent else 'partial',
                           'fields': {name: ('opaque' if name == 'prefix' and n >= 3 else
                                             'ok' if end <= n else 'incomplete')
                                      for name, end in ends}}})
    return {
        'function': 'Ab23Ao23Interpret',
        'signature': SIGNATURE,
        'package': 'vaillant',
        'context': {'primary': 181, 'secondary': 32, 'operations': [0],
                    'directions': ['request', 'positive'], 'views': ['logical_object'],
                    'required_keys': REQUIRED_KEYS},
        'input_keys': INPUT_KEYS,
        'output_keys': ['context', 'raw', 'arguments', 'state', 'fields', 'physical',
                        'qualified'],
        'output_constants': {'physical': 'Unknown', 'qualified': False,
                             'field_grade': 'Hypothesis', 'calculation_grade': 'Proven'},
        'result_states': RESULT_STATES,
        'field_states': FIELD_STATES,
        'extents': {d: ends[-1][1] for d, ends in ENDS.items()},
        'field_tables': {d: [{'name': name, 'offset': start, 'width': end - start}
                             for (name, end), start in zip(ends, starts[d])]
                         for d, ends in ENDS.items()},
        'temperature_tables': {k: {'label': label, 'min_c': low, 'max_c': high}
                               for k, (label, low, high) in TABLES.items()},
        'vortex_hysteresis_hz': {'enter': 5, 'exit': 4, 'role': 'metadata'},
        'cases': [{'id': P + suffix, 'direction': d, 'logical_object': obj,
                   'expect': {'state': state, 'fields': fields}}
                  for suffix, d, obj, state, fields in CASES],
        'truncation': truncation,
        'unknown_cases': [{'id': P + 'unknown_' + axis,
                           'context': dict(CONTROL_CONTEXT, family='opaque-family-a',
                                           variant='opaque-variant-1',
                                           **{axis: UNKNOWN_VARIED[axis]}),
                           'expect': {'state': 'unknown', 'fields': {},
                                      'raw_preserved': True, 'qualified': False}}
                          for axis in UNKNOWN_IDS],
        'error_cases': [{'id': P + 'err_' + s, 'input_text': ERROR_TEXTS[s]}
                        for s in ERROR_IDS],
        'presence_cases': [
            {'id': P + 'presence_missing', 'direction': 'request', 'fields': {},
             'expect': {'state': 'partial', 'field_state': 'missing'}},
            {'id': P + 'presence_empty', 'direction': 'request',
             'fields': {'logical_object': []},
             'expect': {'state': 'partial', 'field_state': 'incomplete'}},
            {'id': P + 'presence_zero_bytes', 'direction': 'request',
             'fields': {'logical_object': [0] * 10},
             'expect': {'state': 'complete', 'field_state': 'ok'}}],
        'calculation_fields': CALCULATION_FIELDS,
    }


def expected_fixture():
    """The complete fixture: FIXTURE_META plus one tuple per FIXTURE_ROWS entry."""
    cases = {suffix: (d, obj, fields) for suffix, d, obj, _, fields in CASES}
    tuples = []
    for suffix, name in FIXTURE_ROWS:
        d, obj, fields = cases[suffix]
        f = fields[name]
        tuples.append([P + suffix, d, ''.join('%02X' % b for b in obj), name, f['state'],
                       f.get('number'), f.get('label'), f.get('candidate_domain')])
    return dict(FIXTURE_META,
                tuple_columns=['id', 'direction', 'logical_object_hex', 'field',
                               'field_state', 'number', 'label', 'candidate_domain'],
                tuples=tuples)


def problems(contract, fixture):
    """Compare page contract and fixture to the constants above."""
    out = []

    def check(label, got, want):
        if got != want:
            out.append(label)

    check('function', contract.get('function'), 'Ab23Ao23Interpret')
    check('signature', contract.get('signature'), SIGNATURE)
    check('package', contract.get('package'), 'vaillant')
    ctx = contract.get('context', {})
    check('ctx.primary', ctx.get('primary'), 181)
    check('ctx.secondary', ctx.get('secondary'), 32)
    check('ctx.operations', ctx.get('operations'), [0])
    check('ctx.directions', ctx.get('directions'), ['request', 'positive'])
    check('ctx.views', ctx.get('views'), ['logical_object'])
    check('output_keys', contract.get('output_keys'),
          ['context', 'raw', 'arguments', 'state', 'fields', 'physical', 'qualified'])
    check('constants', contract.get('output_constants'),
          {'physical': 'Unknown', 'qualified': False,
           'field_grade': 'Hypothesis', 'calculation_grade': 'Proven'})
    check('ctx.required_keys', ctx.get('required_keys'), REQUIRED_KEYS)
    check('input_keys', contract.get('input_keys'), INPUT_KEYS)
    check('result_states', contract.get('result_states'), RESULT_STATES)
    check('field_states', contract.get('field_states'), FIELD_STATES)
    check('calculation_fields', contract.get('calculation_fields'), CALCULATION_FIELDS)
    check('extents', contract.get('extents'), {'request': 10, 'positive': 18})
    check('hysteresis', contract.get('vortex_hysteresis_hz'),
          {'enter': 5, 'exit': 4, 'role': 'metadata'})
    for d in ('request', 'positive'):
        rows = contract.get('field_tables', {}).get(d, [])
        starts = [r['offset'] for r in rows]
        got = [(r['name'], r['offset'] + r['width']) for r in rows]
        check('table.' + d, got, ENDS[d])
        check('table.starts.' + d, starts,
              [0] + [e for _, e in ENDS[d][:-1]])
    got_tables = {k: (v['label'], v['min_c'], v['max_c'])
                  for k, v in contract.get('temperature_tables', {}).items()}
    check('temperature_tables', got_tables, TABLES)

    cases = {c['id']: c for c in contract.get('cases', [])}
    for suffix, (field, state, number, label, domain) in EXPECTED.items():
        c = cases.get(P + suffix)
        if c is None:
            out.append('missing case ' + suffix)
            continue
        f = c['expect']['fields'].get(field)
        if f is None:
            out.append('missing field ' + suffix)
            continue
        check(suffix + '.state', f.get('state'), state)
        check(suffix + '.number', f.get('number'), number)
        check(suffix + '.label', f.get('label'), label)
        check(suffix + '.domain', f.get('candidate_domain'), domain)
        check(suffix + '.top', c['expect']['state'], 'complete')
    for v, (formal, window) in VORTEX_FLAGS.items():
        c = cases.get('%spos_vortex_%d' % (P, v))
        flags = c['expect']['fields']['vortex_hz'].get('flags') if c else None
        check('vortex flags %d' % v, flags,
              {'formal_domain': formal, 'operational_window': window})
    c = cases.get(P + 'req_pwm_ed_ff')
    if c:
        for n in ('pwm1', 'pwm2', 'ed'):
            check('ff ' + n, c['expect']['fields'][n].get('number'), 127.5)
    c = cases.get(P + 'pos_distinct_all')
    if c:
        for n, v in DISTINCT_TEMPERATURES.items():
            check('distinct ' + n, c['expect']['fields'][n].get('number'), v)
        check('distinct reserved',
              c['expect']['fields']['reserved'].get('reserved'), 126)
        check('distinct impeller',
              c['expect']['fields']['impeller_hz'].get('number'), 515)
        check('distinct vortex',
              c['expect']['fields']['vortex_hz'].get('number'), 100)
        check('distinct adc', c['expect']['fields']['adc'].get('number'), 258)
    for n in ('pwm1', 'pwm2', 'ed'):
        check('pwm distinct ' + n,
              cases.get(P + 'req_pwm_distinct', {}).get('expect', {})
              .get('fields', {}).get(n, {}).get('number'),
              {'pwm1': 50, 'pwm2': 30, 'ed': 10}[n])
    for suffix, ref in (('pos_reserved_0', 0), ('pos_reserved_1', 1),
                        ('pos_reserved_255', 255)):
        f = cases.get(P + suffix, {}).get('expect', {}).get('fields', {}).get('reserved', {})
        check(suffix, (f.get('reserved'), 'number' in f), (ref, False))

    for n in range(1, 5):
        for kind, (number, domain) in TEMPERATURE_WORDS.items():
            f = cases.get('%spos_temperature_%d_%s' % (P, n, kind), {}).get(
                'expect', {}).get('fields', {}).get('temperature_%d' % n, {})
            check('temperature %d %s' % (n, kind),
                  (f.get('state'), f.get('number'), f.get('candidate_domain'),
                   f.get('calculation')), ('ok', number, domain, 'Proven'))
    for suffix, (field, want) in TAIL_CASES.items():
        c = cases.get(P + suffix, {})
        got = c.get('expect', {}).get('fields', {}).get(field)
        want = dict(want)
        if 'calculation' in want:
            want.pop('calculation')
        check('tail ' + suffix, got, want)
        check('tail state ' + suffix, c.get('expect', {}).get('state'), 'complete')
        check('tail len ' + suffix, len(c.get('logical_object', [])),
              ENDS[c.get('direction', 'request')][-1][1] + (2 if suffix[:3] == 'req' else 1))
    for c in cases.values():
        want_calc = CALCULATION_FIELDS[c['direction']]
        for name, f in c['expect']['fields'].items():
            check('calculation ' + c['id'] + name,
                  f.get('calculation') == 'Proven',
                  name in want_calc and f.get('state') == 'ok')

    trunc = {c['id']: c for c in contract.get('truncation', [])}
    check('truncation ids', sorted(trunc), sorted(
        '%strunc_%s_%d' % (P, d, n) for d, k in (('request', 10), ('positive', 18))
        for n in range(k + 1)))
    for d, ends in ENDS.items():
        extent = ends[-1][1]
        for n in range(extent + 1):
            c = trunc.get('%strunc_%s_%d' % (P, d, n))
            if c is None:
                continue
            want = {name: ('opaque' if name == 'prefix' and n >= 3 else
                           'ok' if end <= n else 'incomplete')
                    for name, end in ends}
            check('trunc fields %s %d' % (d, n), c['expect']['fields'], want)
            check('trunc state %s %d' % (d, n), c['expect']['state'],
                  'complete' if n >= extent else 'partial')
            check('trunc len %s %d' % (d, n), len(c['logical_object']), n)
    check('unknown ids', [c['id'] for c in contract.get('unknown_cases', [])],
          [P + 'unknown_' + s for s in UNKNOWN_IDS])
    for c in contract.get('unknown_cases', []):
        check(c['id'] + ' state', c['expect'],
              {'state': 'unknown', 'fields': {}, 'raw_preserved': True,
               'qualified': False})
    check('error ids', [c['id'] for c in contract.get('error_cases', [])],
          [P + 'err_' + s for s in ERROR_IDS])
    check('presence fields', {c['id']: c.get('fields') for c in contract.get('presence_cases', [])},
          {P + 'presence_missing': {}, P + 'presence_empty': {'logical_object': []},
           P + 'presence_zero_bytes': {'logical_object': [0] * 10}})
    check('presence', {c['id']: c['expect'] for c in contract.get('presence_cases', [])},
          {P + 'presence_missing': {'state': 'partial', 'field_state': 'missing'},
           P + 'presence_empty': {'state': 'partial', 'field_state': 'incomplete'},
           P + 'presence_zero_bytes': {'state': 'complete', 'field_state': 'ok'}})

    # The full expected structures pin every other stated result: any one-leaf change fails.
    check('contract', canonical(contract), canonical(expected_contract()))
    check('fixture', canonical(fixture), canonical(expected_fixture()))
    check('fixture.qualification', fixture.get('qualification'), 'Unknown')
    check('fixture.columns', fixture.get('tuple_columns'),
          ['id', 'direction', 'logical_object_hex', 'field', 'field_state',
           'number', 'label', 'candidate_domain'])
    rows = {(r[0], r[3]): r for r in fixture.get('tuples', [])}
    check('fixture.size', len(rows), len(fixture.get('tuples', [])))
    for suffix, (field, state, number, label, domain) in EXPECTED.items():
        r = rows.get((P + suffix, field))
        if r is None:
            out.append('fixture missing ' + suffix)
            continue
        check('fixture ' + suffix, tuple(r[4:]), (state, number, label, domain))
    for r in fixture.get('tuples', []):
        c = cases.get(r[0])
        if c is None:
            out.append('fixture orphan ' + r[0])
            continue
        check('fixture direction ' + r[0], r[1], c['direction'])
        check('fixture bytes ' + r[0], r[2],
              ''.join('%02X' % b for b in c['logical_object']))
        f = c['expect']['fields'][r[3]]
        check('fixture parity %s %s' % (r[0], r[3]), tuple(r[4:]),
              (f['state'], f.get('number'), f.get('label'), f.get('candidate_domain')))
    return out


class B520ActuatorViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_page_contract()
        cls.fixture = json.loads(FIXTURE.read_text())

    def test_valid_control_has_no_problems(self):
        self.assertEqual(problems(self.contract, self.fixture), [])

    def test_known_cases_cover_every_supplied_case(self):
        ids = {c['id'] for c in self.contract['cases']}
        for suffix in EXPECTED:
            self.assertIn(P + suffix, ids)
        self.assertEqual(len(EXPECTED), 28)

    def test_page_prose_states_boundaries(self):
        raw_text = PAGE.read_text()
        text = ' '.join(raw_text.split())
        self.assertIn(SIGNATURE, raw_text)
        for needle in ('physical', 'Unknown', 'Hypothesis', 'calculation=Proven',
                       'not clipped at 100', 'never chosen from a name',
                       'candidate_domain=false', 'calibrate_go_to_zero'):
            self.assertIn(needle, text)
        self.assertNotIn('qualified=true', text)

    def test_error_inputs_are_invalid_and_control_is_valid(self):
        for c in self.contract['error_cases']:
            with self.subTest(case=c['id']):
                self.assertTrue(input_is_invalid(c['input_text']))
        control = json.dumps({'context': CONTROL_CONTEXT,
                              'fields': {'logical_object': [0] * 10},
                              'arguments': {'flag': False, 'count': 0}})
        self.assertFalse(input_is_invalid(control))

    def test_unknown_cases_vary_one_axis_each(self):
        varied = UNKNOWN_VARIED
        for c in self.contract['unknown_cases']:
            axis = c['id'][len(P + 'unknown_'):]
            ctx = c['context']
            with self.subTest(axis=axis):
                self.assertEqual(ctx[axis], varied[axis])
                for k, v in CONTROL_CONTEXT.items():
                    if k != axis:
                        self.assertEqual(ctx[k], v)
                self.assertEqual(ctx['family'], 'opaque-family-a')
                self.assertEqual(ctx['variant'], 'opaque-variant-1')

    def mutants(self):
        def case(c, cid):
            return next(x for x in c['cases'] if x['id'] == P + cid)

        def pwm_clipped(c, f):
            case(c, 'req_pwm_ed_ff')['expect']['fields']['pwm1']['number'] = 100

        def negative_admitted(c, f):
            case(c, 'pos_temperature_2_ffff')['expect']['fields']['temperature_2'][
                'candidate_domain'] = True

        def zero_unavailable(c, f):
            del case(c, 'pos_temperature_3_zero')['expect']['fields'][
                'temperature_3']['number']

        def domains_confused(c, f):
            case(c, 'pos_vortex_4')['expect']['fields']['vortex_hz']['flags'][
                'operational_window'] = True

        def default_fill(c, f):
            next(x for x in c['truncation'] if x['id'] == P + 'trunc_positive_8')['expect']['fields']['temperature_3'] = 'ok'

        def swapped(c, f):
            fl = case(c, 'pos_distinct_all')['expect']['fields']
            fl['temperature_1'], fl['temperature_2'] = fl['temperature_2'], fl['temperature_1']

        def extent_as_physical(c, f):
            c['extents']['positive'] = 20

        def promoted(c, f):
            c['output_constants']['field_grade'] = 'Proven'

        def qualified(c, f):
            c['output_constants']['qualified'] = True

        def missing_alternative(c, f):
            c['cases'] = [x for x in c['cases'] if x['id'] != P + 'req_table_3']

        def stepper_value(c, f):
            case(c, 'req_stepper_241')['expect']['fields']['stepper'] = {
                'state': 'ok', 'number': 241, 'label': 'steps'}

        def fixture_value(c, f):
            f['tuples'][0][5] = 1

        def fixture_native(c, f):
            f['qualification'] = 'Proven'

        def led_alt(c, f):
            case(c, 'req_led_2')['expect']['fields']['led']['label'] = 'enabled'

        def over_rejected(c, f):
            case(c, 'pos_adc_1024')['expect']['fields']['adc'] = {'state': 'unmapped'}

        def table_range(c, f):
            c['temperature_tables']['2']['min_c'] = -40

        return [pwm_clipped, negative_admitted, zero_unavailable, domains_confused,
                default_fill, swapped, extent_as_physical, promoted, qualified,
                missing_alternative, stepper_value, fixture_value, fixture_native,
                led_alt, over_rejected, table_range]

    def test_each_mutation_is_detected(self):
        for mutate in self.mutants():
            with self.subTest(mutation=mutate.__name__):
                contract = copy.deepcopy(self.contract)
                fixture = copy.deepcopy(self.fixture)
                mutate(contract, fixture)
                self.assertNotEqual(problems(contract, fixture), [])

    def test_every_single_leaf_change_is_detected(self):
        def leaves(obj, path=()):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    yield from leaves(v, path + (k,))
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    yield from leaves(v, path + (i,))
            else:
                yield path, obj

        def mutated(leaf):
            if isinstance(leaf, bool):
                return not leaf
            if isinstance(leaf, (int, float)):
                return leaf + 1
            return leaf + 'x' if isinstance(leaf, str) else 'x'

        def put(root, path, value):
            for step in path[:-1]:
                root = root[step]
            root[path[-1]] = value

        count = 0
        for which, doc in (('contract', self.contract), ('fixture', self.fixture)):
            for path, leaf in leaves(doc):
                contract = copy.deepcopy(self.contract)
                fixture = copy.deepcopy(self.fixture)
                put(contract if which == 'contract' else fixture, path, mutated(leaf))
                count += 1
                try:
                    found = problems(contract, fixture)
                except (KeyError, TypeError, AttributeError, IndexError):
                    found = ['malformed']  # a structure that cannot be read fails too
                self.assertNotEqual(found, [], (which, path))
        self.assertGreater(count, 2000)

    def test_page_case_table_round_trips(self):
        again = json.loads(json.dumps(self.contract))
        self.assertEqual(again, self.contract)
        self.assertEqual(problems(again, self.fixture), [])


if __name__ == '__main__':
    unittest.main()
