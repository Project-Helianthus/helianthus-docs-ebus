"""Finite documentation checks; deliberately no production interpreter replica."""
import copy as ab11ao11_copy
import json as ab11ao11_json
import pathlib as ab11ao11_pathlib
import re as ab11ao11_re
import tempfile as ab11ao11_tempfile
import unittest as ab11ao11_unittest

ab11ao11_root = ab11ao11_pathlib.Path(__file__).resolve().parents[1]


def ab11ao11_pairs(ab11ao11_items):
    ab11ao11_result = {}
    for ab11ao11_key, ab11ao11_value in ab11ao11_items:
        if ab11ao11_key in ab11ao11_result:
            raise ValueError('duplicate key')
        ab11ao11_result[ab11ao11_key] = ab11ao11_value
    return ab11ao11_result


def ab11ao11_load(ab11ao11_text):
    return ab11ao11_json.loads(ab11ao11_text, object_pairs_hook=ab11ao11_pairs)


def ab11ao11_page(ab11ao11_text):
    ab11ao11_blocks = []
    for ab11ao11_name, ab11ao11_kind in [('contract', 'json'), ('cases', 'jsonl')]:
        ab11ao11_match = ab11ao11_re.findall(
            r'<!-- ab11ao11-' + ab11ao11_name + r' -->\s*```' + ab11ao11_kind
            + r'\n(.*?)\n```\s*<!-- /ab11ao11-' + ab11ao11_name + r' -->',
            ab11ao11_text, ab11ao11_re.S)
        if len(ab11ao11_match) != 1:
            raise ValueError('missing or duplicate contract table')
        ab11ao11_blocks.append(ab11ao11_match[0])
    return {'contract': ab11ao11_load(ab11ao11_blocks[0]),
            'cases': [ab11ao11_load(ab11ao11_line)
                      for ab11ao11_line in ab11ao11_blocks[1].splitlines()]}


# Fixed finite records are expectations, not a decoder or transition function.
# Numeric outcomes below are additionally checked against a separate hand table.
ab11ao11_expected_contract = {'api': 'Ab11Ao11Interpret(ab11ao11Input json.RawMessage) (json.RawMessage, error)',
 'package': 'vaillant',
 'implementation': 'standard library; pure; no global cache or runtime call site',
 'selection': {'primary': 181,
               'secondary': 16,
               'operation': 'absent',
               'direction': 'local',
               'view': 'capability-query'},
 'input': {'context': 'object; preserve every key and opaque family/variant value',
           'fields': 'object of integer byte arrays (0..255)',
           'arguments': 'object; parsed Boolean; count nonnegative integer; no other keys'},
 'required_fields': {'prior': {'width': 1, 'domain': '0..255'},
                     'feedback': {'width': 1, 'domain': '0..255'},
                     'bit_six': {'width': 1, 'domain': [0, 64]}},
 'output': {'required': ['context', 'raw', 'state', 'fields', 'physical', 'qualified'],
            'optional': ['arguments'],
            'states': ['Hypothesis', 'partial', 'Unknown'],
            'physical': 'Unknown',
            'qualified': False},
 'result_fields': {'cache_cell': {'raw': 'prior',
                                  'state': 'Hypothesis',
                                  'number': 'updated or retained byte'},
                   'freshness': {'raw': 'feedback',
                                 'state': 'Hypothesis or Unknown',
                                 'label': 'fresh or Unknown'},
                   'rule': {'raw': 'bit_six',
                            'state': 'Hypothesis or Unknown',
                            'label': 'replace or retain or Unknown'}},
 'errors': ['malformed JSON',
            'duplicate object keys at any depth',
            'invalid byte elements',
            'wrong JSON kinds'],
 'raw_only': ['unselected context',
              'missing required input',
              'invalid width',
              'bit_six outside domain',
              'negative count',
              'unknown argument'],
 'grades': {'semantic': 'Hypothesis',
            'calculation': 'Proven only for independently exact calculation; absent here',
            'physical': 'Unknown',
            'native_timing': 'Unknown',
            'qualified': False},
 'copy': 'context, raw, arguments and result-field raw are independent deep copies across inputs, '
         'outputs and calls',
 'partial': 'preserve complete independent fields; incomplete, unmapped, unit-conflict or '
            'unknown-order fields have no number; explicit Unknown stays Unknown',
 'presence': 'missing differs from empty and explicit zero; preserve through JSON round trips',
 'selection_policy': 'never infer from name, payload length or family; no operation zero '
                     'association'}

ab11ao11_expected_cases = [
    {'id': 'ab11ao11_count_0', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 0}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 165}, 'freshness': {'raw': [1], 'state': 'Unknown', 'label': 'Unknown'}, 'rule': {'raw': [64], 'state': 'Unknown', 'label': 'Unknown'}}}},
    {'id': 'ab11ao11_count_1', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 1}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 0}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_count_2', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 2}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 0}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_count_3', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 64}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_count_255', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 255}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 64}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_count_256', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 256}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 64}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_bit_zero', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [0]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 0}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [0], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_prior_zero', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [0], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [0], 'state': 'Hypothesis', 'number': 64}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_prior_other', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [42], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [42], 'state': 'Hypothesis', 'number': 64}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_parse_failure', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': False, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 165}, 'freshness': {'raw': [1], 'state': 'Unknown', 'label': 'Unknown'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'retain'}}}},
    {'id': 'ab11ao11_feedback_0', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [0], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 165}, 'freshness': {'raw': [0], 'state': 'Unknown', 'label': 'Unknown'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'retain'}}}},
    {'id': 'ab11ao11_feedback_2', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [2], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 165}, 'freshness': {'raw': [2], 'state': 'Unknown', 'label': 'Unknown'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'retain'}}}},
    {'id': 'ab11ao11_feedback_255', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [255], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 165}, 'freshness': {'raw': [255], 'state': 'Unknown', 'label': 'Unknown'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'retain'}}}},
    {'id': 'ab11ao11_failure_count_zero', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': False, 'count': 0}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 165}, 'freshness': {'raw': [1], 'state': 'Unknown', 'label': 'Unknown'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'retain'}}}},
    {'id': 'ab11ao11_tail', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64], 'unmodelled': [0, 255, 64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 64}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_opaque_family', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': {'opaque': [1, 0]}, 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 64}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_opaque_variant', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': ['opaque', None]}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 64}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_opaque_extra', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant', 'extra': {'retained': True}}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 64}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_selector_primary_180', 'input': {'context': {'primary': 180, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_selector_secondary_17', 'input': {'context': {'primary': 181, 'secondary': 17, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_selector_operation_0', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant', 'operation': 0}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_selector_operation_1', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant', 'operation': 1}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_selector_direction_reply', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'reply', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_selector_view_other', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'other', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_missing_primary', 'input': {'context': {'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_missing_secondary', 'input': {'context': {'primary': 181, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_missing_direction', 'input': {'context': {'primary': 181, 'secondary': 16, 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_missing_view', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_prior_empty', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_prior_wide', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [0, 64], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_prior_missing', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_prior_negative', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [-1], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_prior_overflow', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [256], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_prior_fraction', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [1.5], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_prior_bool', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [True], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_prior_string', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': ['1'], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_prior_null', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [None], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_prior_wrong_kind', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': 1, 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_feedback_empty', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_feedback_wide', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [0, 64], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_feedback_missing', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_feedback_negative', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [-1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_feedback_overflow', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [256], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_feedback_fraction', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1.5], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_feedback_bool', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [True], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_feedback_string', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': ['1'], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_feedback_null', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [None], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_feedback_wrong_kind', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': 1, 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_bit_six_empty', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': []}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_bit_six_wide', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [0, 64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_bit_six_missing', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_bit_six_negative', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [-1]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_bit_six_overflow', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [256]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_bit_six_fraction', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [1.5]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_bit_six_bool', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [True]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_bit_six_string', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': ['1']}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_bit_six_null', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [None]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_bit_six_wrong_kind', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': 1}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_bit_invalid', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [1]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_missing_parsed', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_missing_count', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_missing_context', 'input': {'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_context_null', 'input': {'context': None, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_context_array', 'input': {'context': [], 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_context_string', 'input': {'context': 'x', 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_missing_fields', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_fields_null', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': None, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_fields_array', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': [], 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_fields_string', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': 'x', 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_missing_arguments', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_arguments_null', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': None}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_arguments_array', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': []}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_arguments_string', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': 'x'}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_negative_count', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': -1}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_extra_argument', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3, 'extra': 1}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_parsed_integer', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': 1, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_parsed_null', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': None, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_count_bool', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': True}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_count_fraction', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 1.5}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_count_string', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': '3'}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_count_null', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': None}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_malformed', 'input_json': '{', 'error': True, 'expected': None},
    {'id': 'ab11ao11_duplicate_root', 'input_json': '{"context":{},"context":{}}', 'error': True, 'expected': None},
    {'id': 'ab11ao11_duplicate_context', 'input_json': '{"context":{"view":"capability-query","view":"other"}}', 'error': True, 'expected': None},
    {'id': 'ab11ao11_duplicate_fields', 'input_json': '{"fields":{"prior":[0],"prior":[165]}}', 'error': True, 'expected': None},
    {'id': 'ab11ao11_duplicate_arguments', 'input_json': '{"arguments":{"count":1,"count":3}}', 'error': True, 'expected': None},
    {'id': 'ab11ao11_root_array', 'input_json': '[]', 'error': True, 'expected': None},
]

# A separate, explicitly enumerated oracle for the stated transition examples.
ab11ao11_expected_cases.extend([
    {'id': 'ab11ao11_kind_primary', 'input': {'context': {'primary': '181', 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_kind_secondary', 'input': {'context': {'primary': 181, 'secondary': '16', 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_kind_operation', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant', 'operation': None}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_kind_direction', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 1, 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_kind_view', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': None, 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': True, 'expected': None},
    {'id': 'ab11ao11_absent_family', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 64}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_absent_variant', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [165], 'state': 'Hypothesis', 'number': 64}, 'freshness': {'raw': [1], 'state': 'Hypothesis', 'label': 'fresh'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'replace'}}}},
    {'id': 'ab11ao11_zero_primary', 'input': {'context': {'primary': 0, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_zero_secondary', 'input': {'context': {'primary': 181, 'secondary': 0, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': True, 'count': 3}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_arguments_empty', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [165], 'feedback': [1], 'bit_six': [64]}, 'arguments': {}}, 'error': False, 'expected': {'state': 'Unknown', 'physical': 'Unknown', 'qualified': False, 'fields': {}}},
    {'id': 'ab11ao11_retained_other_prior', 'input': {'context': {'primary': 181, 'secondary': 16, 'direction': 'local', 'view': 'capability-query', 'family': 'synthetic-family', 'variant': 'synthetic-variant'}, 'fields': {'prior': [42], 'feedback': [1], 'bit_six': [64]}, 'arguments': {'parsed': False, 'count': 3}}, 'error': False, 'expected': {'state': 'Hypothesis', 'physical': 'Unknown', 'qualified': False, 'fields': {'cache_cell': {'raw': [42], 'state': 'Hypothesis', 'number': 42}, 'freshness': {'raw': [1], 'state': 'Unknown', 'label': 'Unknown'}, 'rule': {'raw': [64], 'state': 'Hypothesis', 'label': 'retain'}}}},
    {'id': 'ab11ao11_trailing', 'input_json': '{} {}', 'error': True, 'expected': None},
    {'id': 'ab11ao11_duplicate_opaque', 'input_json': '{"context":{"family":{"x":1,"x":2}}}', 'error': True, 'expected': None},
])

ab11ao11_numeric = {
    'ab11ao11_count_0': (165, 'Unknown', 'Unknown', 'Unknown'),
    'ab11ao11_count_1': (0, 'fresh', 'replace', 'Hypothesis'),
    'ab11ao11_count_2': (0, 'fresh', 'replace', 'Hypothesis'),
    'ab11ao11_count_3': (64, 'fresh', 'replace', 'Hypothesis'),
    'ab11ao11_count_255': (64, 'fresh', 'replace', 'Hypothesis'),
    'ab11ao11_count_256': (64, 'fresh', 'replace', 'Hypothesis'),
    'ab11ao11_bit_zero': (0, 'fresh', 'replace', 'Hypothesis'),
    'ab11ao11_parse_failure': (165, 'Unknown', 'retain', 'Hypothesis'),
    'ab11ao11_feedback_0': (165, 'Unknown', 'retain', 'Hypothesis'),
    'ab11ao11_feedback_2': (165, 'Unknown', 'retain', 'Hypothesis'),
    'ab11ao11_feedback_255': (165, 'Unknown', 'retain', 'Hypothesis'),
}


class TestAb11Ao11Contract(ab11ao11_unittest.TestCase):
    def setUp(self):
        self.ab11ao11_page_text = (ab11ao11_root / 'architecture/ao12_b510_cache_transition.md').read_text()
        self.ab11ao11_page = ab11ao11_page(self.ab11ao11_page_text)
        self.ab11ao11_fixture = ab11ao11_load((ab11ao11_root / 'architecture/fixtures/ao12_b510_cache_transition.json').read_text())

    def ab11ao11_assert_table(self, ab11ao11_data):
        self.assertEqual(ab11ao11_data['contract'], ab11ao11_expected_contract)
        self.assertEqual(ab11ao11_data['cases'], ab11ao11_expected_cases)
        self.assertEqual(len(ab11ao11_data['cases']), 100)
        self.assertEqual(len({ab11ao11_c['id'] for ab11ao11_c in ab11ao11_data['cases']}), 100)

    def ab11ao11_assert_disposable(self, ab11ao11_data):
        # Only disposable copies of this owned fixture are mutated on disk.
        ab11ao11_tmp = ab11ao11_root / '.tmp'
        ab11ao11_tmp.mkdir(exist_ok=True)
        with ab11ao11_tempfile.TemporaryDirectory(dir=ab11ao11_tmp, prefix='ab11ao11-') as ab11ao11_dir:
            ab11ao11_path = ab11ao11_pathlib.Path(ab11ao11_dir) / 'ao12_b510_cache_transition.json'
            ab11ao11_path.write_text(ab11ao11_json.dumps(ab11ao11_data))
            self.ab11ao11_assert_table(ab11ao11_load(ab11ao11_path.read_text()))

    def TestAb11Ao11PageAndFixture(self):
        for ab11ao11_data in (self.ab11ao11_page, self.ab11ao11_fixture):
            self.ab11ao11_assert_table(ab11ao11_data)

    def TestAb11Ao11ExactNumericsAndGrades(self):
        for ab11ao11_data in (self.ab11ao11_page, self.ab11ao11_fixture):
            ab11ao11_cases = {ab11ao11_c['id']: ab11ao11_c for ab11ao11_c in ab11ao11_data['cases']}
            for ab11ao11_id, ab11ao11_values in ab11ao11_numeric.items():
                with self.subTest(ab11ao11_id=ab11ao11_id):
                    ab11ao11_case = ab11ao11_cases[ab11ao11_id]
                    ab11ao11_out = ab11ao11_case['expected']
                    self.assertFalse(ab11ao11_case['error'])
                    self.assertEqual((ab11ao11_out['fields']['cache_cell']['number'],
                                      ab11ao11_out['fields']['freshness']['label'],
                                      ab11ao11_out['fields']['rule']['label'],
                                      ab11ao11_out['state']), ab11ao11_values)
            for ab11ao11_case in ab11ao11_cases.values():
                self.assertTrue(ab11ao11_case['id'].startswith('ab11ao11'))
                if ab11ao11_case['error']:
                    self.assertIsNone(ab11ao11_case['expected'])
                    continue
                ab11ao11_out = ab11ao11_case['expected']
                self.assertEqual(ab11ao11_out['physical'], 'Unknown')
                self.assertIs(ab11ao11_out['qualified'], False)
                if ab11ao11_out['fields']:
                    self.assertEqual(ab11ao11_out['fields']['cache_cell']['state'], 'Hypothesis')
                else:
                    self.assertEqual(ab11ao11_out['state'], 'Unknown')

    def TestAb11Ao11SelectionAndPresence(self):
        ab11ao11_cases = {ab11ao11_c['id']: ab11ao11_c for ab11ao11_c in self.ab11ao11_fixture['cases']}
        for ab11ao11_axis in ['primary_180', 'secondary_17', 'operation_0', 'operation_1', 'direction_reply', 'view_other']:
            ab11ao11_case = ab11ao11_cases['ab11ao11_selector_' + ab11ao11_axis]
            self.assertEqual(ab11ao11_case['expected']['fields'], {})
        self.assertEqual(ab11ao11_cases['ab11ao11_count_256']['input']['arguments']['count'], 256)
        self.assertNotIn('operation', ab11ao11_cases['ab11ao11_count_3']['input']['context'])
        for ab11ao11_axis in ['prior', 'feedback', 'bit_six']:
            self.assertNotIn(ab11ao11_axis, ab11ao11_cases['ab11ao11_' + ab11ao11_axis + '_missing']['input']['fields'])
            self.assertEqual(ab11ao11_cases['ab11ao11_' + ab11ao11_axis + '_empty']['input']['fields'][ab11ao11_axis], [])
        self.assertEqual(ab11ao11_cases['ab11ao11_prior_zero']['input']['fields']['prior'], [0])
        for ab11ao11_axis in ['family', 'variant', 'extra']:
            self.assertEqual(ab11ao11_cases['ab11ao11_opaque_' + ab11ao11_axis]['expected']['fields']['cache_cell']['number'], 64)
        # These round trips validate fixture distinctions, not Go runtime copying.
        self.assertEqual(ab11ao11_load(ab11ao11_json.dumps(self.ab11ao11_fixture)), self.ab11ao11_fixture)

    def TestAb11Ao11JsonNegativeRecords(self):
        for ab11ao11_id in ['malformed', 'duplicate_root', 'duplicate_context', 'duplicate_fields', 'duplicate_arguments']:
            ab11ao11_case = next(ab11ao11_c for ab11ao11_c in self.ab11ao11_fixture['cases'] if ab11ao11_c['id'] == 'ab11ao11_' + ab11ao11_id)
            with self.subTest(ab11ao11_id=ab11ao11_id):
                with self.assertRaises(ValueError):
                    ab11ao11_load(ab11ao11_case['input_json'])
                self.assertTrue(ab11ao11_case['error'])
        for ab11ao11_axis in ['prior', 'feedback', 'bit_six']:
            for ab11ao11_kind in ['negative', 'overflow', 'fraction', 'bool', 'string', 'null', 'wrong_kind']:
                ab11ao11_case = next(ab11ao11_c for ab11ao11_c in self.ab11ao11_fixture['cases'] if ab11ao11_c['id'] == 'ab11ao11_' + ab11ao11_axis + '_' + ab11ao11_kind)
                self.assertTrue(ab11ao11_case['error'])
                self.assertIsNone(ab11ao11_case['expected'])

    def TestAb11Ao11MutationSensitivity(self):
        # Executed mutations of documentation data; not production Go mutants.
        for ab11ao11_source in (self.ab11ao11_page, self.ab11ao11_fixture):
            self.ab11ao11_assert_table(ab11ao11_source)  # valid control
            for ab11ao11_id, ab11ao11_field, ab11ao11_key, ab11ao11_value in [
                ('count_1', 'cache_cell', 'number', 64),
                ('count_2', 'cache_cell', 'number', 64),
                ('count_3', 'cache_cell', 'number', 0),
                ('count_256', 'cache_cell', 'number', 165),
                ('bit_zero', 'cache_cell', 'number', 64),
                ('feedback_2', 'cache_cell', 'number', 64),
                ('parse_failure', 'cache_cell', 'number', 0),
                ('parse_failure', 'freshness', 'label', 'fresh'),
                ('count_3', 'cache_cell', 'state', 'Proven'),
            ]:
                ab11ao11_mutant = ab11ao11_copy.deepcopy(ab11ao11_source)
                ab11ao11_case = next(ab11ao11_c for ab11ao11_c in ab11ao11_mutant['cases'] if ab11ao11_c['id'] == 'ab11ao11_' + ab11ao11_id)
                ab11ao11_case['expected']['fields'][ab11ao11_field][ab11ao11_key] = ab11ao11_value
                with self.subTest(ab11ao11_id=ab11ao11_id, ab11ao11_key=ab11ao11_key):
                    with self.assertRaises(AssertionError):
                        self.ab11ao11_assert_disposable(ab11ao11_mutant)
            ab11ao11_mutant = ab11ao11_copy.deepcopy(ab11ao11_source)
            ab11ao11_mutant['cases'].pop()
            with self.assertRaises(AssertionError):
                self.ab11ao11_assert_disposable(ab11ao11_mutant)
            ab11ao11_mutant = ab11ao11_copy.deepcopy(ab11ao11_source)
            ab11ao11_mutant['contract']['grades']['physical'] = 'Proven'
            with self.assertRaises(AssertionError):
                self.ab11ao11_assert_disposable(ab11ao11_mutant)
        # Mutate text before parsing, so a page-only result edit is caught too.
        ab11ao11_mutated_text = self.ab11ao11_page_text.replace('"number":64', '"number":63', 1)
        self.assertNotEqual(ab11ao11_mutated_text, self.ab11ao11_page_text)
        with ab11ao11_tempfile.TemporaryDirectory(dir=ab11ao11_root / '.tmp', prefix='ab11ao11-') as ab11ao11_dir:
            ab11ao11_path = ab11ao11_pathlib.Path(ab11ao11_dir) / 'ao12_b510_cache_transition.md'
            ab11ao11_path.write_text(ab11ao11_mutated_text)
            with self.assertRaises(AssertionError):
                self.ab11ao11_assert_table(ab11ao11_page(ab11ao11_path.read_text()))


def load_tests(ab11ao11_loader, ab11ao11_tests, ab11ao11_pattern):
    ab11ao11_loader.testMethodPrefix = 'TestAb11Ao11'
    return ab11ao11_loader.loadTestsFromTestCase(TestAb11Ao11Contract)
