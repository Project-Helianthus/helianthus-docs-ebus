"""Offline contract examples; this interpreter is not a production decoder."""
import copy
import json
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/am20_standard03_candidate_views.md'
PACKAGE = ROOT / 'architecture/fixtures/am20_standard03_candidate_views.json'
DATA = json.loads(PACKAGE.read_text())
CONTRACT = DATA['contract']

# Independent literals pin every layout, mode and grade, rather than deriving
# the expected schema or expected anchor numbers from the interpreter.
EXPECTED_CONTRACT = {
    'family': 'vaillant-burner', 'operation': '03',
    'layouts': {
        '04': {'variant': 'explicit', 'encoding': 'unsigned-decimal-chunks',
               'fields': [['c0', 99], ['c1', 99], ['c2', 99]],
               'default': 0, 'width': 1, 'projection': 'local_count'},
        '05': {'variant': 'alternative', 'encoding': 'unspecified',
               'fields': [['minutes', 59], ['hundreds_of_hours', 59],
                          ['ten_thousands_of_hours', 59]],
               'default': None, 'width': 1, 'projection': None},
        '06': {'variant': 'alternative', 'encoding': 'unspecified',
               'fields': [['minutes', 59], ['h0', 99], ['h1', 99], ['h2', 99]],
               'default': None, 'width': 1, 'projection': 'local_hours'},
    },
    'modes': {'04': [['candidate', 'request'], ['standard', 'positive']],
              '05': [['candidate', 'request']],
              '06': [['candidate', 'request'], ['standard', 'positive']]},
    'grade': 'Hypothesis', 'native_support': 'Unknown',
    'physical_length': 'Unknown', 'effects': 'Unknown',
    'persistence': 'Unknown', 'delivery': 'Unknown',
}


def package_body(values):
    if not isinstance(values, list) or any(
        type(v) is not int or not 0 <= v <= 255 for v in values
    ):
        raise ValueError('body must be an array of byte integers')
    return bytes(values)


def view(selection, body):
    if not isinstance(body, (bytes, bytearray)):
        raise TypeError('isolated bytes or bytearray required')
    raw = list(body)
    out = dict(raw=raw, remainder=raw.copy(), fields={}, projection={},
               complete=False, status='raw-only', encoding='unspecified',
               grade='Hypothesis', native_support='Unknown')
    axes = ('family', 'variant', 'operation', 'function', 'direction', 'selector')
    if any(type(selection.get(axis)) is not str for axis in axes):
        return out
    function = selection['function']
    layout = CONTRACT['layouts'].get(function)
    if (layout is None or selection['family'] != CONTRACT['family']
            or selection['operation'] != CONTRACT['operation']
            or selection['variant'] != layout['variant']
            or [selection['selector'], selection['direction']]
            not in CONTRACT['modes'][function]):
        return out
    size = len(layout['fields'])
    out.update(status='incomplete', encoding=layout['encoding'],
               remainder=raw[size:])
    for offset, (name, maximum) in enumerate(layout['fields']):
        byte = raw[offset] if offset < len(raw) else None
        state = ('absent' if byte is None else
                 'valid' if byte <= maximum else 'invalid')
        out['fields'][name] = dict(state=state, raw=byte,
                                   value=byte if state == 'valid' else None)
    out['complete'] = (len(raw) == size and all(
        field['state'] == 'valid' for field in out['fields'].values()))
    if out['complete']:
        out['status'] = 'complete'
        if function == '04':
            out['projection'] = {'local_count': raw[0] + 100*raw[1] + 10000*raw[2]}
        elif function == '06':
            out['projection'] = {'minutes': raw[0],
                                 'local_hours': raw[1] + 100*raw[2] + 10000*raw[3]}
    return out


def selection(function):
    return dict(family='vaillant-burner', operation='03', function=function,
                variant='explicit' if function == '04' else 'alternative',
                selector='candidate', direction='request')


# A separate literal test matrix supplies expected names, limits and anchors.
CONTROLS = (
    ('04', '63 01 02', ('c0', 'c1', 'c2'), (99, 99, 99)),
    ('05', '01 02 03', ('minutes', 'hundreds_of_hours',
                       'ten_thousands_of_hours'), (59, 59, 59)),
    ('06', '3B 01 02 03', ('minutes', 'h0', 'h1', 'h2'), (59, 99, 99, 99)),
)


class CandidateViews(unittest.TestCase):
    def test_page_package_contract_and_links(self):
        page = PAGE.read_text()
        blocks = re.findall(r'```json\n(.*?)\n```', page, re.S)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(json.loads(blocks[0]), EXPECTED_CONTRACT)
        self.assertEqual(CONTRACT, EXPECTED_CONTRACT)
        for target in re.findall(r'\]\(([^)]+)\)', page):
            self.assertFalse('://' in target)
            self.assertTrue((PAGE.parent / target).is_file(), target)
        for row in (
            '| 03/04 explicit | 63 01 02 | 99/1/2 | 20199 |',
            '| 03/05 alternative | 01 02 03 | 1/2/3 | none |',
            '| 03/06 alternative | 3B 01 02 03 | 59/1/2/3 | minutes 59; hours 30201 |',
        ):
            self.assertIn(row, page)
        for phrase in ('not packed BCD', 'no units-hour field',
                       'direction inference by byte count',
                       'Short bodies are incomplete',
                       'incomplete even if the prefix is valid',
                       'One invalid field never erases another valid field',
                       'physical support, presence', 'GraphQL parity',
                       'eBUS MCP compatibility', 'Admission remains fail-closed'):
            self.assertIn(phrase, page)

    def test_fixture_cases(self):
        self.assertEqual(len(DATA['cases']), 93)
        ids = [case['id'] for case in DATA['cases']]
        self.assertEqual(len(ids), len(set(ids)))
        for case in DATA['cases']:
            with self.subTest(case=case['id']):
                self.assertEqual(view(case['input'], package_body(case['body'])),
                                 case['expected'])

    def test_independent_anchor_arithmetic(self):
        count = struct.unpack('3B', bytes.fromhex('63 01 02'))
        self.assertEqual(count, (99, 1, 2))
        self.assertEqual(sum(v * 100**i for i, v in enumerate(count)), 20199)
        self.assertEqual(view(selection('04'), bytes(count))['projection'],
                         {'local_count': 20199})
        minutes, *hours = struct.unpack('4B', bytes.fromhex('3B 01 02 03'))
        self.assertEqual(minutes, 59)
        self.assertEqual(sum(v * 100**i for i, v in enumerate(hours)), 30201)
        self.assertEqual(view(selection('06'), bytes([minutes, *hours]))['projection'],
                         {'minutes': 59, 'local_hours': 30201})
        alternative = view(selection('05'), bytes.fromhex('01 02 03'))
        self.assertEqual(alternative['projection'], {})
        self.assertEqual(list(alternative['fields']),
                         ['minutes', 'hundreds_of_hours', 'ten_thousands_of_hours'])
        self.assertEqual([f['value'] for f in alternative['fields'].values()], [1, 2, 3])

    def test_every_field_boundary_and_partial_independence(self):
        for function, hex_body, names, limits in CONTROLS:
            original = list(bytes.fromhex(hex_body))
            for offset, (name, limit) in enumerate(zip(names, limits)):
                for value in (0, limit, limit + 1, 255):
                    with self.subTest(function=function, field=name, value=value):
                        body = original.copy()
                        body[offset] = value
                        result = view(selection(function), bytes(body))
                        self.assertEqual(result['raw'], body)
                        self.assertEqual(list(result['fields']), list(names))
                        for i, field_name in enumerate(names):
                            field = result['fields'][field_name]
                            valid = i != offset or value <= limit
                            self.assertEqual(field, dict(
                                state='valid' if valid else 'invalid', raw=body[i],
                                value=body[i] if valid else None))
                        self.assertEqual(result['complete'], value <= limit)
                        if value > limit:
                            self.assertEqual(result['projection'], {})

    def test_all_short_lengths_extra_and_absent_versus_zero(self):
        for function, hex_body, names, _ in CONTROLS:
            body = bytes.fromhex(hex_body)
            for length in range(len(body)):
                with self.subTest(function=function, length=length):
                    result = view(selection(function), body[:length])
                    self.assertFalse(result['complete'])
                    self.assertEqual(result['projection'], {})
                    self.assertEqual(result['raw'], list(body[:length]))
                    for i, name in enumerate(names):
                        self.assertEqual(result['fields'][name], dict(
                            state='valid' if i < length else 'absent',
                            raw=body[i] if i < length else None,
                            value=body[i] if i < length else None))
            extra = view(selection(function), body + b'\xaa')
            self.assertFalse(extra['complete'])
            self.assertEqual(extra['remainder'], [170])
            self.assertEqual(extra['projection'], {})
            self.assertTrue(all(f['state'] == 'valid' for f in extra['fields'].values()))
            zero = view(selection(function), bytes(len(body)))
            self.assertTrue(zero['complete'])
            self.assertTrue(all(f['value'] == 0 for f in zero['fields'].values()))
            self.assertNotEqual(zero['fields'], view(selection(function), b'')['fields'])

    def assert_raw_only(self, result, body):
        self.assertEqual(result, dict(raw=list(body), remainder=list(body), fields={},
                                     projection={}, complete=False, status='raw-only',
                                     encoding='unspecified', grade='Hypothesis',
                                     native_support='Unknown'))

    def test_each_selection_axis_independently(self):
        for function, hex_body, _, _ in CONTROLS:
            body = bytes.fromhex(hex_body)
            baseline = selection(function)
            self.assertTrue(view(baseline, body)['complete'])
            for axis in ('family', 'variant', 'operation', 'function', 'direction', 'selector'):
                for wrong in ('unknown', '', None, 0, [], {}):
                    with self.subTest(function=function, axis=axis, wrong=wrong):
                        changed = dict(baseline, **{axis: wrong})
                        self.assert_raw_only(view(changed, body), body)
                missing = baseline.copy()
                del missing[axis]
                self.assert_raw_only(view(missing, body), body)
            for variant in ('explicit', 'alternative', 'unspecified'):
                if variant != baseline['variant']:
                    self.assert_raw_only(view(dict(baseline, variant=variant), body), body)
            for other in ('04', '05', '06', '07', '08', '10'):
                if other == function:
                    continue
                changed = dict(baseline, function=other)
                if other in ('07', '08', '10') or function == '04' or other == '04':
                    self.assert_raw_only(view(changed, body), body)
                else:
                    # 05 and 06 share a variant label, but never a field set or size.
                    result = view(changed, body)
                    self.assertFalse(result['complete'])
                    self.assertEqual(result['projection'], {})
                    self.assertNotEqual(list(result['fields']),
                                        list(view(baseline, body)['fields']))

    def test_modes_are_separate_and_never_inferred(self):
        for function, hex_body, _, _ in CONTROLS:
            body = bytes.fromhex(hex_body)
            for selector in ('candidate', 'standard'):
                for direction in ('request', 'positive'):
                    chosen = dict(selection(function), selector=selector, direction=direction)
                    admitted = ((selector, direction) == ('candidate', 'request') or
                                function != '05' and
                                (selector, direction) == ('standard', 'positive'))
                    for length in range(len(body) + 2):
                        probe = (body + b'\xaa')[:length]
                        result = view(chosen, probe)
                        if admitted:
                            self.assertEqual(result['complete'], length == len(body))
                        else:
                            self.assert_raw_only(result, probe)

    def test_malformed_package_and_body_types(self):
        for bad in (None, '630102', {}, [True], [1.0], ['1'], [-1], [256]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                package_body(bad)
        for bad in (None, [99, 1, 2], '630102', memoryview(b'abc'), 3):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                view(selection('04'), bad)

    def test_input_return_and_cross_result_ownership(self):
        for function, hex_body, _, _ in CONTROLS:
            for raw_only in (False, True):
                for extra in (False, True):
                    source = bytearray.fromhex(hex_body)
                    if extra:
                        source.append(170)
                    chosen = selection(function)
                    if raw_only:
                        chosen['selector'] = 'unknown'
                    result = view(chosen, source)
                    previous = copy.deepcopy(result)
                    other = view(chosen, source)
                    source[0] = 0
                    self.assertEqual(result, previous)
                    result['raw'][0] = 17
                    if result['remainder']:
                        self.assertEqual(result['remainder'], previous['remainder'])
                        result['remainder'][0] = 18
                        self.assertEqual(result['raw'][0], 17)
                    if result['fields']:
                        first = next(iter(result['fields']))
                        result['fields'][first]['value'] = 19
                    result['projection']['injected'] = 20
                    self.assertEqual(other, previous)
                    self.assertEqual(source[0], 0)


if __name__ == '__main__':
    unittest.main()
