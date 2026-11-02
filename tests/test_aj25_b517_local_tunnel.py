"""Offline documentation checks; these helpers are not a tunnel executor."""
import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/aj25_b517_local_tunnel.md'
FIXTURE = ROOT / 'architecture/fixtures/aj25_b517_local_tunnel.json'
UNKNOWN = {
    'native_behavior', 'physical_route', 'fragmentation', 'timeout',
    'correlation', 'negative_code_mapping', 'trust', 'channel_number',
    'code_meanings', 'physical_qualification',
}


def page_table(text, heading):
    section = text.split('| ' + heading + ' |', 1)[1].split('\n\n', 1)[0]
    rows = section.splitlines()[2:]
    result = {}
    for row in rows:
        key, value = row.strip('|').strip().split(' | ')
        if key in result:
            raise AssertionError('duplicate table key: ' + key)
        result[key] = json.loads(value)
    return result


class LocalTunnelContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text(encoding='utf-8')
        cls.data = json.loads(FIXTURE.read_text(encoding='utf-8'))

    def test_page_tables(self):
        self.assertEqual(page_table(self.page, 'Identity key'), {
            'grade': 'Hypothesis', 'tunnel_destination_min': 1,
            'tunnel_destination_max': 254, 'channel': 'fixed-channel',
            'channel_number': None, 'outer_destination': 'tunnel_destination',
            'inner_destination': 'original_destination',
            'inner_pdu': 'original_pdu', 'returned_context': 'original_service',
            'raw_policy': 'preserve',
        })
        self.assertEqual(page_table(self.page, 'Predicate key'), {
            'grade': 'Hypothesis', 'ready': 3, 'final_option': 'nonzero',
            'minimum_input_length': 5, 'length_index': 4, 'length_bias': 6,
            'length_relation': 'input[4] + 6 == len(input)',
            'request_service': [181, 23], 'input_service': [181, 24],
            'prefix_policy': 'no universal stripping',
        })
        self.assertEqual(page_table(self.page, 'State key'), {
            'grade': 'Hypothesis', 'local_codes': [10, 6, 7],
            'code_meanings': 'Unknown', 'remote_feedback': 'separate',
            'incomplete': 'preserve raw and last_known_good',
            'ineligible': 'preserve raw and last_known_good',
            'admission': 'withheld',
        })
        self.assertEqual(page_table(self.page, 'Property'),
                         dict.fromkeys(UNKNOWN, 'Unknown'))

    def test_grade_and_scope(self):
        self.assertEqual(set(self.data), {
            'grade', 'unknown', 'admission', 'clients', 'adaptations', 'outcomes',
        })
        self.assertEqual(self.data['grade'], 'Hypothesis')
        self.assertEqual(self.data['unknown'], dict.fromkeys(UNKNOWN, 'Unknown'))
        self.assertEqual(self.data['admission'], 'withheld')
        for phrase in (
            '**Hypothesis**', 'Nothing here is\nstable before 1.0',
            '../protocols/vaillant/ebus-vaillant.md#b517-and-b518-sub-ebus-tunnel',
            'unresolved B518', 'not a universal\neBUS or PeBUS prefix rule',
            'Check that index 4 exists before reading it',
            'No transport, channel opener or tunnel executor changes',
            'No eBUS MCP or GraphQL contract changes',
            'roadmap wording remains 0.11',
        ):
            self.assertIn(phrase, self.page)

    def test_client_identity_and_return_context(self):
        control = {
            'tunnel_destination': 1, 'original_destination': 42,
            'original_pdu': [181, 24, 0, 255],
            'original_service': [181, 9], 'returned_data': [181, 24, 9],
        }
        # Independent input/transition expectations, never read from page rules.
        patches = {
            'destination-zero': ({'tunnel_destination': 0}, False),
            'control': ({}, True),
            'matching-destinations': ({'tunnel_destination': 42}, True),
            'destination-max': ({'tunnel_destination': 254}, True),
            'destination-255': ({'tunnel_destination': 255}, False),
            'original-destination': ({'original_destination': 43}, True),
            'original-pdu': ({'original_pdu': [181, 24, 1, 254]}, True),
            'original-pb': ({'original_service': [180, 9]}, True),
            'original-sb': ({'original_service': [181, 10]}, True),
            'returned-data': ({'returned_data': [181, 24, 8]}, True),
        }
        cases = self.data['clients']
        self.assertEqual(len(cases), len(patches))
        self.assertEqual({c['id'] for c in cases}, set(patches))
        for case in cases:
            with self.subTest(case=case['id']):
                patch, accepted = patches[case['id']]
                expected_input = copy.deepcopy(control)
                expected_input.update(patch)
                self.assertEqual(case['input'], expected_input)
                self.assertEqual(case['direction'], 'client_request_and_returned_data')
                x = case['input']
                self.assertEqual(0 < x['tunnel_destination'] < 255, accepted)
                expected = {'state': 'candidate' if accepted else 'ineligible',
                            'admission': 'withheld', 'raw': expected_input,
                            'envelope': None, 'returned': None}
                if accepted:
                    # Separate axes: changing the outer never changes the inner.
                    envelope = case['expected']['envelope']
                    self.assertEqual(envelope['outer_destination'],
                                     expected_input['tunnel_destination'])
                    self.assertEqual(envelope['inner']['original_destination'],
                                     expected_input['original_destination'])
                    expected['envelope'] = {
                        'channel': 'fixed-channel',
                        'outer_destination': x['tunnel_destination'],
                        'inner': {'original_destination': x['original_destination'],
                                  'original_pdu': x['original_pdu']},
                    }
                    expected['returned'] = {'context': x['original_service'],
                                            'raw': x['returned_data']}
                self.assertEqual(case['expected'], expected)

    def test_adaptation_conjunction_and_arithmetic(self):
        control = {
            'ready': 3, 'final_option': 1, 'request_service': [181, 23],
            'input_service': [181, 24],
            'input': [181, 24, 0, 0, 4, 0, 0, 0, 0, 0],
            'last_known_good': {'original_destination': 42,
                                'original_service': [181, 9],
                                'raw': [181, 24, 55]},
        }
        patches = {
            'control': ({}, 'eligible'),
            'ready': ({'ready': 2}, 'ineligible'),
            'option-zero': ({'final_option': 0}, 'ineligible'),
            'option-nonunit': ({'final_option': 2}, 'eligible'),
            'length-byte': ({'input': [181, 24, 0, 0, 3, 0, 0, 0, 0, 0]}, 'ineligible'),
            'actual-length': ({'input': [181, 24, 0, 0, 4, 0, 0, 0, 0]}, 'ineligible'),
            'request-pb': ({'request_service': [180, 23]}, 'ineligible'),
            'request-sb': ({'request_service': [181, 22]}, 'ineligible'),
            'input-pb': ({'input_service': [180, 24]}, 'ineligible'),
            'input-sb': ({'input_service': [181, 25]}, 'ineligible'),
            'raw-body': ({'input': [181, 24, 99, 88, 4, 77, 66, 55, 44, 33]}, 'eligible'),
            'short-and-unready': ({'ready': 2, 'input': []}, 'incomplete'),
        }
        for length in range(5):
            patches['short-' + str(length)] = (
                {'input': [181, 24, 0, 0][:length]}, 'incomplete')
        cases = self.data['adaptations']
        self.assertEqual(len(cases), len(patches))
        self.assertEqual({c['id'] for c in cases}, set(patches))
        for case in cases:
            with self.subTest(case=case['id']):
                patch, state = patches[case['id']]
                expected_input = copy.deepcopy(control)
                expected_input.update(patch)
                self.assertEqual(case['input'], expected_input)
                self.assertEqual(case['direction'], 'logical_request_and_input')
                x = case['input']
                raw = x['input']
                if len(raw) < 5:
                    actual = 'incomplete'
                else:
                    # Subtraction is an independent arithmetic form of the page sum.
                    valid = (x['ready'] == 3 and x['final_option'] != 0
                             and len(raw) - raw[4] == 6
                             and tuple(x['request_service']) == (181, 23)
                             and tuple(x['input_service']) == (181, 24))
                    actual = 'eligible' if valid else 'ineligible'
                self.assertEqual(actual, state)
                self.assertEqual(case['expected'], {
                    'state': state, 'admission': 'withheld', 'raw': raw,
                    'last_known_good': control['last_known_good'],
                })

    def test_local_and_remote_outcomes(self):
        expected = []
        for code in (10, 6, 7):
            expected.append({
                'direction': 'local_result', 'local_code': code,
                'remote_feedback': None,
                'expected': {'local_code': code, 'meaning': 'Unknown',
                             'remote_feedback': None, 'admission': 'withheld'},
            })
        expected.append({
            'direction': 'remote_feedback', 'local_code': None,
            'remote_feedback': 'negative',
            'expected': {'local_code': None, 'meaning': 'Unknown',
                         'remote_feedback': 'negative', 'admission': 'withheld'},
        })
        self.assertEqual(self.data['outcomes'], expected)


if __name__ == '__main__':
    unittest.main()
