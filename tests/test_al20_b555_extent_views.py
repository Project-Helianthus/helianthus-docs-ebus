#!/usr/bin/env python3
"""Offline documentation checks; the projection is not companion runtime code."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/al20_b555_extent_views.md'
FIXTURE = ROOT / 'architecture/fixtures/al20_b555_extent_views.json'


def ab52_policy():
    return json.loads(re.search(r'```json\n(.*?)\n```', PAGE.read_text(), re.S)[1])


def ab52_project(ab52_api, ab52_declared, ab52_input, ab52_rules):
    """Bounded test-local illustration of the declared representation policy."""
    ab52_raw = list(ab52_input)
    ab52_extent = min(ab52_declared, len(ab52_raw))
    ab52_required = (ab52_rules['ab52_a4_week_extent'] if ab52_api == 'Ab52DecodeA4'
                     else ab52_rules['ab52_a5_word_extent'])
    ab52_incomplete = ab52_extent < ab52_required or len(ab52_raw) < ab52_declared
    ab52_out = dict(ab52_raw=ab52_raw, ab52_incomplete=ab52_incomplete,
                    ab52_errors=['ab52_extent_incomplete'] if ab52_incomplete else [],
                    ab52_status=ab52_raw[0] if ab52_extent >= 1 else None)
    if ab52_api == 'Ab52DecodeA4':
        ab52_days = ab52_raw[1:min(ab52_extent, 8)]
        ab52_week = (ab52_extent >= ab52_required
                     and ab52_out['ab52_status'] == ab52_rules['ab52_a4_accepted_status']
                     and all(x <= ab52_rules['ab52_a4_day_limit'] for x in ab52_days))
        ab52_out.update(ab52_day_counts=ab52_days, ab52_complete_week=ab52_week,
                        ab52_eighth_count=ab52_raw[8] if ab52_extent >= 9 else None)
        if ab52_extent >= 8 and not ab52_week:
            ab52_out['ab52_errors'].append('ab52_week_rejected')
    else:
        for ab52_index, ab52_key in enumerate(
                ['ab52_start_hour', 'ab52_start_minute',
                 'ab52_end_hour', 'ab52_end_minute'], 1):
            ab52_out[ab52_key] = ab52_raw[ab52_index] if ab52_extent > ab52_index else None
        ab52_word = (ab52_raw[5] + 256 * ab52_raw[6]) if ab52_extent >= 7 else None
        ab52_out.update(ab52_setpoint_raw=ab52_word,
                        ab52_setpoint_candidate_numeric=ab52_word / 10 if ab52_word is not None else None)
    return ab52_out


class Ab52ExtentViews(unittest.TestCase):
    def setUp(self):
        self.ab52_rules = ab52_policy()

    def ab52_decode(self, api, declared, raw):
        return ab52_project(api, declared, raw, self.ab52_rules)

    def test_ab52_page_policy(self):
        self.assertEqual(self.ab52_rules, {
            'ab52_extent_rule': 'both', 'ab52_a4_week_extent': 8,
            'ab52_a4_eighth_extent': 9, 'ab52_weekday_count': 7,
            'ab52_a4_day_limit': 12, 'ab52_a4_accepted_status': 0,
            'ab52_a4_unavailable_status': 3, 'ab52_eighth_role': '24-hour-count',
            'ab52_a5_word_extent': 7, 'ab52_a5_status_gate': False,
            'ab52_a5_time_range_gate': False,
            'ab52_ffff_universally_unavailable': False,
        })
        ab52_text = PAGE.read_text()
        for ab52_phrase in (
            'Ab52DecodeA4(declaredCount, availableRaw)',
            'Ab52DecodeA5(declaredCount, availableRaw)',
            'declaredCount >= ab52_end AND len(availableRaw) >= ab52_end',
            'Byte 8 only when both extents reach 9',
            'never an eighth weekday',
            'count 13 invalidates the complete-week view',
            'A5 decoding does not evaluate status or range-check time bytes.',
            'FFFF is not universally unavailable.',
            '**Hypothesis:**', '**Proven:**', '**Unknown:**',
            'Neither routine\ninvokes or replaces existing timer methods.',
            'eBUS MCP compatibility and GraphQL parity',
        ):
            with self.subTest(phrase=ab52_phrase):
                self.assertIn(ab52_phrase, ab52_text)
        for ab52_target in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', ab52_text):
            self.assertTrue((PAGE.parent / ab52_target).is_file(), ab52_target)

    def test_ab52_literal_examples(self):
        ab52_cases = json.loads(FIXTURE.read_text())
        # Independently pin the small input set so deleting a control fails.
        self.assertEqual([(c['ab52_api'], c['ab52_declared_count'], c['ab52_available_raw'])
                          for c in ab52_cases], [
            ('Ab52DecodeA4', 8, [0, 1, 2, 3, 4, 5, 6, 12]),
            ('Ab52DecodeA4', 8, [0, 1, 2, 3, 4, 5, 6, 12, 99]),
            ('Ab52DecodeA4', 9, [0, 1, 2, 3, 4, 5, 6, 12]),
            ('Ab52DecodeA4', 9, [0, 1, 2, 3, 4, 5, 6, 13, 99]),
            ('Ab52DecodeA4', 8, [3, 1, 2, 3, 4, 5, 6, 12]),
            ('Ab52DecodeA5', 7, [3, 23, 59, 24, 60, 255, 255]),
            ('Ab52DecodeA5', 7, [3, 23, 59, 24, 60, 255]),
        ])
        for ab52_case in ab52_cases:
            with self.subTest(case=ab52_case):
                self.assertEqual(set(ab52_case), {'ab52_api', 'ab52_declared_count',
                                                 'ab52_available_raw', 'ab52_expected'})
                self.assertEqual(self.ab52_decode(ab52_case['ab52_api'],
                                                 ab52_case['ab52_declared_count'],
                                                 ab52_case['ab52_available_raw']),
                                 ab52_case['ab52_expected'])

    def test_ab52_extent_matrix(self):
        # 2 APIs x 3 declarations x 9 storage lengths, independent expected fields.
        for ab52_api in ('Ab52DecodeA4', 'Ab52DecodeA5'):
            for ab52_declared in (6, 7, 8):
                for ab52_length in range(9):
                    with self.subTest(api=ab52_api, declared=ab52_declared, length=ab52_length):
                        ab52_source = [0, 1, 2, 3, 4, 5, 6, 7, 8][:ab52_length]
                        ab52_out = self.ab52_decode(ab52_api, ab52_declared, ab52_source)
                        self.assertEqual(ab52_out['ab52_raw'], ab52_source)
                        self.assertEqual(ab52_out['ab52_status'], 0 if ab52_length else None)
                        if ab52_api == 'Ab52DecodeA4':
                            ab52_ok = ab52_declared == 8 and ab52_length == 8
                            self.assertEqual(ab52_out['ab52_complete_week'], ab52_ok)
                            self.assertIsNone(ab52_out['ab52_eighth_count'])
                            ab52_expected_days = [value for index, value in
                                                 enumerate([1, 2, 3, 4, 5, 6, 7], 1)
                                                 if index < ab52_declared and index < ab52_length]
                            self.assertEqual(ab52_out['ab52_day_counts'], ab52_expected_days)
                            ab52_incomplete = not ab52_ok
                        else:
                            ab52_word_ok = ab52_declared in (7, 8) and ab52_length in (7, 8)
                            self.assertEqual(ab52_out['ab52_setpoint_raw'], 1541 if ab52_word_ok else None)
                            self.assertEqual(ab52_out['ab52_setpoint_candidate_numeric'],
                                             154.1 if ab52_word_ok else None)
                            for ab52_index, ab52_key in enumerate([
                                    'ab52_start_hour', 'ab52_start_minute',
                                    'ab52_end_hour', 'ab52_end_minute'], 1):
                                self.assertEqual(ab52_out[ab52_key],
                                                 ab52_index if ab52_length > ab52_index else None)
                            ab52_incomplete = ((ab52_declared, ab52_length) not in
                                               {(7, 7), (7, 8), (8, 8)})
                        self.assertEqual(ab52_out['ab52_incomplete'], ab52_incomplete)
                        self.assertEqual(ab52_out['ab52_errors'],
                                         ['ab52_extent_incomplete'] if ab52_incomplete else [])

    def test_ab52_a4_each_day_limit(self):
        for ab52_day in range(7):
            for ab52_value in (12, 13):
                with self.subTest(day=ab52_day, value=ab52_value):
                    ab52_days = [1] * 7
                    ab52_days[ab52_day] = ab52_value
                    ab52_out = self.ab52_decode('Ab52DecodeA4', 8, [0] + ab52_days)
                    self.assertEqual(ab52_out['ab52_day_counts'], ab52_days)
                    self.assertEqual(ab52_out['ab52_complete_week'], ab52_value == 12)
                    self.assertEqual(ab52_out['ab52_errors'],
                                     [] if ab52_value == 12 else ['ab52_week_rejected'])

    def test_ab52_a4_optional_count_independent(self):
        for ab52_declared, ab52_length, ab52_expected, ab52_incomplete in (
                (8, 8, None, False), (8, 9, None, False),
                (9, 8, None, True), (9, 9, 13, False)):
            with self.subTest(declared=ab52_declared, length=ab52_length):
                ab52_out = self.ab52_decode('Ab52DecodeA4', ab52_declared,
                                           [0, 1, 2, 3, 4, 5, 6, 7, 13][:ab52_length])
                self.assertEqual(ab52_out['ab52_eighth_count'], ab52_expected)
                self.assertEqual(ab52_out['ab52_day_counts'], [1, 2, 3, 4, 5, 6, 7])
                self.assertTrue(ab52_out['ab52_complete_week'])
                self.assertEqual(ab52_out['ab52_incomplete'], ab52_incomplete)
        for ab52_eighth in (0, 12, 13, 255):
            ab52_out = self.ab52_decode('Ab52DecodeA4', 9, [0] + [1] * 7 + [ab52_eighth])
            self.assertEqual(ab52_out['ab52_eighth_count'], ab52_eighth)
            self.assertTrue(ab52_out['ab52_complete_week'])
            self.assertEqual(len(ab52_out['ab52_day_counts']), 7)

    def test_ab52_status_independent(self):
        for ab52_status in (0, 1, 3, 255):
            with self.subTest(status=ab52_status):
                ab52_a4 = self.ab52_decode('Ab52DecodeA4', 8, [ab52_status] + [1] * 7)
                self.assertEqual(ab52_a4['ab52_status'], ab52_status)
                self.assertEqual(ab52_a4['ab52_complete_week'], ab52_status == 0)
                self.assertEqual(ab52_a4['ab52_day_counts'], [1] * 7)
                ab52_a5 = self.ab52_decode('Ab52DecodeA5', 7, [ab52_status, 23, 59, 24, 60, 255, 255])
                self.assertEqual(ab52_a5['ab52_status'], ab52_status)
                self.assertEqual(ab52_a5['ab52_setpoint_raw'], 65535)
                self.assertEqual(ab52_a5['ab52_setpoint_candidate_numeric'], 6553.5)
                self.assertEqual(ab52_a5['ab52_errors'], [])

    def test_ab52_each_time_byte_independent(self):
        for ab52_index, ab52_key in enumerate([
                'ab52_start_hour', 'ab52_start_minute',
                'ab52_end_hour', 'ab52_end_minute'], 1):
            for ab52_value in (0, 23, 24, 59, 60, 255):
                with self.subTest(field=ab52_key, value=ab52_value):
                    ab52_raw = [0, 1, 2, 3, 4, 190, 0]
                    ab52_raw[ab52_index] = ab52_value
                    ab52_out = self.ab52_decode('Ab52DecodeA5', 7, ab52_raw)
                    self.assertEqual(ab52_out[ab52_key], ab52_value)
                    for ab52_other, ab52_other_key in enumerate([
                            'ab52_start_hour', 'ab52_start_minute',
                            'ab52_end_hour', 'ab52_end_minute'], 1):
                        if ab52_other != ab52_index:
                            self.assertEqual(ab52_out[ab52_other_key], ab52_other)
                    self.assertEqual(ab52_out['ab52_setpoint_raw'], 190)
                    self.assertEqual(ab52_out['ab52_errors'], [])

    def test_ab52_word_bytes_independent(self):
        # Change each byte alone, include a nonsymmetric endian control and FFFF.
        for ab52_lo, ab52_hi, ab52_word, ab52_numeric in (
                (0, 0, 0, 0.0), (255, 0, 255, 25.5), (0, 1, 256, 25.6),
                (0, 255, 65280, 6528.0), (255, 255, 65535, 6553.5),
                (52, 18, 4660, 466.0)):
            with self.subTest(low=ab52_lo, high=ab52_hi):
                ab52_out = self.ab52_decode('Ab52DecodeA5', 7, [0, 1, 2, 3, 4, ab52_lo, ab52_hi])
                self.assertEqual(ab52_out['ab52_setpoint_raw'], ab52_word)
                self.assertEqual(ab52_out['ab52_setpoint_candidate_numeric'], ab52_numeric)
                self.assertEqual(ab52_out['ab52_errors'], [])

    def test_ab52_owned_raw_and_empty_prefix(self):
        for ab52_api in ('Ab52DecodeA4', 'Ab52DecodeA5'):
            ab52_raw = [0, 1, 2, 3, 4, 5, 6, 7, 8]
            ab52_out = self.ab52_decode(ab52_api, 0, ab52_raw)
            self.assertTrue(ab52_out['ab52_incomplete'])
            self.assertIsNone(ab52_out['ab52_status'])
            if ab52_api == 'Ab52DecodeA4':
                self.assertEqual(ab52_out['ab52_day_counts'], [])
                self.assertIsNone(ab52_out['ab52_eighth_count'])
            else:
                self.assertIsNone(ab52_out['ab52_setpoint_raw'])
            ab52_raw[0] = 255
            self.assertEqual(ab52_out['ab52_raw'], [0, 1, 2, 3, 4, 5, 6, 7, 8])
            ab52_out['ab52_raw'][1] = 255
            self.assertEqual(ab52_raw[1], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
