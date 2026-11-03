"""Validate the finite documentary contract, not a companion implementation."""

import copy
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/al22_standard_ff_body_states.md'
FIXTURE = ROOT / 'architecture/fixtures/al22_standard_ff_body_states.json'
POLICY = {
    'identity_axes': ['PB', 'SB', 'direction'],
    'service_identity_count': 7,
    'invocable_route': False,
    'ff04_declared_nn': [1, 10],
    'ff04_minimum_overhead': 2,
    'ff04_minimum_implies_semantic_validity': False,
    'ff06_declared_nn': [1, 10],
    'ff06_complete_nn': '1+2n',
    'ff06_even_complete': False,
    'pair_count_implies_peer_response': False,
}
SERVICE_ROWS = [
    ['FF00', '255', '0', 'broadcast', 'reset-status identity only'],
    ['FF01', '255', '1', 'broadcast', 'reset-target-configuration'],
    ['FF02', '255', '2', 'broadcast', 'failure-message'],
    ['FF03', '255', '3', 'initiator-to-target', 'net-status-query'],
    ['FF04', '255', '4', 'initiator-to-target', 'monitored-participants-query'],
    ['FF05', '255', '5', 'initiator-to-target', 'failed-nodes-query'],
    ['FF06', '255', '6', 'initiator-to-target', 'required-services-query'],
]
BODY_ROWS = [
    ['ff04-one', 'FF04', '1', 'false', 'absent', 'absent', 'truncated/raw', '80'],
    ['ff04-two', 'FF04', '2', 'true', 'absent', 'absent', 'minimum-overhead-only', '80 A5'],
    ['ff06-one', 'FF06', '1', 'true', '0', 'true', 'complete-pairs', 'empty'],
    ['ff06-two', 'FF06', '2', 'true', '0', 'false', 'incomplete/raw', '31'],
    ['ff06-three', 'FF06', '3', 'true', '1', 'true', 'complete-pairs', 'empty'],
    ['ff06-four', 'FF06', '4', 'true', '1', 'false', 'incomplete/raw', '53'],
    ['ff06-five', 'FF06', '5', 'true', '2', 'true', 'complete-pairs', 'empty'],
]
QUALIFICATION = (
    'physical_support', 'presence', 'freshness', 'native_execution',
    'installed_support', 'native_emission', 'forwarding_eligibility',
    'target_identity', 'correlation', 'lifecycle_effects',
)


def tables(page):
    """Read declared rows, excluding each heading and separator."""
    found = []
    for block in re.findall(r'(?m)^\|.*(?:\n\|.*)*', page):
        found.append([[cell.strip() for cell in row.strip('|').split('|')]
                      for row in block.splitlines()[2:]])
    return found


def selected_service(rows, key):
    """Test-only selection over page rows; no production lookup is imported."""
    if not isinstance(key, dict) or set(key) != {'PB', 'SB', 'direction'}:
        return None
    if any(type(key[name]) is not int or not 0 <= key[name] <= 255
           for name in ('PB', 'SB')):
        return None
    for service, pb, sb, direction, _ in rows:
        if key == dict(PB=int(pb), SB=int(sb), direction=direction):
            return service
    return None


class StandardFFBodyStates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text()
        cls.package = json.loads(FIXTURE.read_text())
        cls.cases = {case['id']: case for case in cls.package['body_examples']}

    def test_normative_policy_and_exact_page_tables(self):
        blocks = re.findall(r'```json\n(.*?)\n```', self.page, re.S)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(json.loads(blocks[0]), POLICY)
        self.assertEqual(self.package['policy'], POLICY)
        self.assertEqual(tables(self.page), [SERVICE_ROWS, BODY_ROWS])

    def test_finite_package_and_independent_grades(self):
        self.assertEqual(set(self.package), {
            'provenance', 'policy', 'grades', 'qualification', 'lookup_examples',
            'body_examples', 'empty_body_controls',
        })
        self.assertEqual(self.package['provenance'], 'synthetic; no device observation')
        self.assertEqual(self.package['grades'], {
            'representation': 'Proven', 'candidate_interpretation': 'Hypothesis',
        })
        self.assertEqual(self.package['qualification'],
                         dict.fromkeys(QUALIFICATION, 'Unknown'))
        self.assertEqual(len(self.package['body_examples']), 7)
        self.assertEqual(set(self.cases), {row[0] for row in BODY_ROWS})

    def test_lookup_examples_vary_every_key_axis_alone(self):
        examples = self.package['lookup_examples']
        self.assertEqual(len(examples), 4)
        keys = [dict(PB=255, SB=6, direction='initiator-to-target'),
                dict(PB=254, SB=6, direction='initiator-to-target'),
                dict(PB=255, SB=7, direction='initiator-to-target'),
                dict(PB=255, SB=6, direction='target-to-initiator')]
        for case, name, key, service in zip(
                examples, ('exact', 'wrong-pb', 'wrong-sb', 'wrong-direction'),
                keys, ('FF06', None, None, None)):
            with self.subTest(case=name):
                self.assertEqual(case, dict(id=name, key=key, selected_service=service))
                self.assertEqual(selected_service(tables(self.page)[0], key), service)
        for axis, key in zip(POLICY['identity_axes'], keys[1:]):
            self.assertEqual([name for name in keys[0] if keys[0][name] != key[name]], [axis])

    def test_all_seven_identities_and_missing_or_malformed_axes(self):
        rows = tables(self.page)[0]
        self.assertEqual(len({tuple(row[1:4]) for row in rows}), 7)
        for sb in range(7):
            key = dict(PB=255, SB=sb,
                       direction='broadcast' if sb < 3 else 'initiator-to-target')
            with self.subTest(service=sb):
                self.assertEqual(selected_service(rows, key), f'FF{sb:02X}')
                for axis in ('PB', 'SB', 'direction'):
                    for bad in (None, '', '*', 'Unknown'):
                        self.assertIsNone(selected_service(rows, dict(key, **{axis: bad})))
                    missing = key.copy()
                    del missing[axis]
                    self.assertIsNone(selected_service(rows, missing))
                for axis in ('PB', 'SB'):
                    for bad in (False, True, -1, 256, 1.5, str(key[axis])):
                        self.assertIsNone(selected_service(rows, dict(key, **{axis: bad})))
                self.assertIsNone(selected_service(rows, dict(key, direction=key['direction'].upper())))
        # Each query retains its own PB/SB response service; they cannot collapse.
        self.assertEqual([row[0] for row in rows[3:]], ['FF03', 'FF04', 'FF05', 'FF06'])

    def test_literal_ff04_results_and_minimum_is_not_semantic_validity(self):
        expected = (
            ('ff04-one', [128], False, 'truncated/raw'),
            ('ff04-two', [128, 165], True, 'minimum-overhead-only'),
        )
        for name, raw, minimum, state in expected:
            with self.subTest(case=name):
                case = self.cases[name]
                self.assertEqual(set(case), {'id', 'identity', 'body', 'expected'})
                self.assertEqual(case['identity'], dict(PB=255, SB=4, direction='initiator-to-target'))
                self.assertEqual(case['body'], raw)
                self.assertEqual(case['expected'], dict(
                    raw_body=raw, available_overhead_raw=raw,
                    minimum_overhead_met=minimum, complete_pairs=None, pair_bytes=[],
                    pair_layout_complete=None, body_state=state, raw_remainder=raw,
                    semantic_validity='Unknown'))

    def test_literal_ff06_counts_pairs_and_trailing_bytes(self):
        # Expected pair counts/states are literal, not read from fixture policy.
        lengths = ('one', 'two', 'three', 'four', 'five')
        for nn, word, count, complete, remainder in zip(
                (1, 2, 3, 4, 5), lengths, (0, 0, 1, 1, 2),
                (True, False, True, False, True), ([], [49], [], [83], [])):
            with self.subTest(nn=nn):
                case = self.cases['ff06-' + word]
                raw = [128, 49, 66, 83, 100][:nn]
                self.assertEqual(set(case), {'id', 'identity', 'body', 'expected'})
                self.assertEqual(case['identity'], dict(PB=255, SB=6, direction='initiator-to-target'))
                self.assertEqual(case['body'], raw)
                # Iterator pairing independently excludes a final unmatched byte.
                stream = iter(raw[1:])
                pairs = [list(pair) for pair in zip(stream, stream)]
                self.assertEqual(len(pairs), count)
                self.assertEqual(case['expected'], dict(
                    raw_body=raw, available_overhead_raw=[128],
                    minimum_overhead_met=True, complete_pairs=count, pair_bytes=pairs,
                    pair_layout_complete=complete,
                    body_state='complete-pairs' if complete else 'incomplete/raw',
                    raw_remainder=remainder, semantic_validity='Unknown'))
        # Adding a partial next pair preserves the preceding complete pair.
        self.assertEqual(self.cases['ff06-three']['expected']['pair_bytes'],
                         self.cases['ff06-four']['expected']['pair_bytes'])

    def test_responder_availability_does_not_change_empty_ff02(self):
        self.assertEqual(self.package['empty_body_controls'], [
            dict(service='FF01', body=[], nn=0, emitter_added=False),
            dict(service='FF02', responder_available=True, body=[], nn=0),
            dict(service='FF02', responder_available=False, body=[], nn=0),
        ])

    def test_example_raw_snapshots_are_independent_not_runtime_copy_proof(self):
        cases = copy.deepcopy(self.cases)
        case = cases['ff06-four']
        saved = copy.deepcopy(case['expected'])
        case['body'][0] = 0
        self.assertEqual(case['expected'], saved)
        case['expected']['raw_body'][1] = 0
        self.assertEqual(case['expected']['pair_bytes'], [[49, 66]])
        case['expected']['raw_body'][3] = 0
        self.assertEqual(case['expected']['raw_remainder'], [83])
        case['expected']['available_overhead_raw'][0] = 0
        self.assertEqual(case['expected']['raw_body'][0], 128)
        self.assertEqual(cases['ff06-three'], self.cases['ff06-three'])
        ff04 = cases['ff04-two']['expected']
        ff04['raw_body'][0] = 0
        self.assertEqual(ff04['raw_remainder'], [128, 165])
        self.assertEqual(ff04['available_overhead_raw'], [128, 165])

    def test_api_error_absence_ownership_and_scope_declarations(self):
        text = ' '.join(self.page.split())
        for phrase in (
            'Read the public [native FF contract]',
            'companion catalog prerequisite must merge before this page',
            '`Ab54Entries()` returns the finite metadata collection or an error',
            '`Ab54Lookup(key)` returns an entry, a found boolean and an error',
            'A well-formed miss returns no entry, false and no error',
            'Validation covers the whole catalog before lookup',
            'Duplicate exact identities are invalid',
            'Every enumeration and successful lookup returns independently owned memory',
            'preserve partial last-known-good state and its raw evidence separately',
            'NN=1 cannot contain both follow-block and status overhead and remains truncated/raw',
            'NN=2 clears only the minimum-overhead condition; full semantic validity remains Unknown',
            'Even lengths cannot contain whole pairs throughout and remain incomplete/raw',
            'An incomplete suffix must not erase preceding complete pairs',
            'their count does not establish pair meaning or a peer response',
            'Each query\'s reply belongs to that same PB/SB service',
            'Bodies for FF00, FF03 and FF05 are outside this area',
            'requires an explicit emission policy; this area adds no emitter',
            'Neither an empty body nor a catalog hit supplies physical ACK',
            'No cross-repository runtime import is added',
            'Nothing is stable before Helianthus 1.0',
            'it does not execute Ab54Entries/Ab54Lookup',
            'no invocable route, transmitter, polling default, automatic native qualification or write admission',
            'eBUS MCP compatibility and GraphQL parity remain carried requirements with their own checks',
            'this is a partial child and does not close the parent',
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertEqual(re.findall(r'\]\(([^)]+)\)', self.page), [
            '../protocols/ebus-services/ebus-service-FFh.md',
            'fixtures/al22_standard_ff_body_states.json',
            '../tests/test_al22_standard_ff_body_states.py',
        ])


if __name__ == '__main__':
    unittest.main()
