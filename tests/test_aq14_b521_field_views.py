"""Independent reference check of the AQ14 B521 named-field contract."""

import json
from pathlib import Path
import re
import unittest

PAGE = Path(__file__).resolve().parents[1] / 'architecture/aq14_b521_field_views.md'
RESERVED = ('state', 'results', 'physical', 'qualified')
WIDTHS = {
    'request': {'flags': 1, 'appliance_bits': 1, 'noise_percent': 1, 'frost_temperature': 1},
    'positive': {'status0': 1, 'status1': 1, 'brine_percent': 1, 'fan_percent': 1,
                 'fan_speed': 1, 'temperature0': 2, 'temperature1': 2},
}
STATUS0 = ('ready', 'deicing-request', 'deicing-active', 'deicing-timeout-error',
           'deicing-with-heater', None, None, 'cleaning-request')
STATUS1 = ('heater', 'relay-output', 'fan-running', 'brine-flow-reverse',
           'fan-error', 'safety-limiter-error', 'hot-summer', 'bad-weather')


def _reject_duplicates(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError('duplicate key')
    return dict(pairs)


def _byte_array(value):
    if not isinstance(value, list):
        raise ValueError('kind')
    for item in value:
        if type(item) is not int or not 0 <= item <= 255:
            raise ValueError('byte')
    return value


def _bits(byte, names):
    flags = {n: bool(byte >> i & 1) for i, n in enumerate(names) if n}
    reserved = {'bit%d' % i: bool(byte >> i & 1) for i, n in enumerate(names) if not n}
    return flags, reserved


def evaluate(text):
    data = json.loads(text, object_pairs_hook=_reject_duplicates)
    if not isinstance(data, dict) or any(k in data for k in RESERVED):
        raise ValueError('shape')
    context, fields = data['context'], data['fields']
    if not isinstance(fields, dict):
        raise ValueError('fields')
    for raw in fields.values():
        _byte_array(raw)
    out = dict(data)
    out.update(physical='Unknown', qualified=False)
    supported = (
        context.get('primary') == 181 and context.get('secondary') == 33
        and 'operation' not in context and context.get('view') == 'module-fields'
        and context.get('direction') in WIDTHS
    )
    if not supported:
        out.update(state='Unknown', results={})
        return out
    widths = WIDTHS[context['direction']]
    results, complete = {}, True
    for name, width in widths.items():
        raw = fields.get(name)
        if raw is None or len(raw) != width:
            complete = False
            entry = {'state': 'incomplete', 'grade': 'Hypothesis'}
            if raw is not None:
                entry['raw'] = raw
            results[name] = entry
            continue
        entry = {'raw': raw, 'state': 'complete', 'grade': 'Hypothesis', 'calculation': 'Proven'}
        if name == 'status0':
            entry['flags'], entry['reserved'] = _bits(raw[0], STATUS0)
        elif name == 'status1':
            entry['flags'], _ = _bits(raw[0], STATUS1)
        elif name in ('flags', 'appliance_bits'):
            count = 6 if name == 'flags' else 5
            entry['flags'], _ = _bits(raw[0], tuple('bit%d' % i if i < count else None for i in range(8)))
            entry['reserved'] = {'bit%d' % i: bool(raw[0] >> i & 1) for i in range(count, 8)}
        elif name == 'fan_speed':
            entry.update(number=raw[0] * 10, unit='rpm')
        elif name.startswith('temperature') or name == 'frost_temperature':
            if width == 2:
                value = raw[0] + 256 * raw[1]
                value = (value - 65536 if value >= 32768 else value) / 16
            else:
                value = raw[0]
            entry.update(number=value, unit='Celsius')
        else:
            entry.update(number=raw[0], unit='percent')
        results[name] = entry
    out.update(state='complete' if complete else 'partial', results=results)
    return out


def page_json_blocks():
    return [json.loads(b) for b in re.findall(r'```json\n(.*?)```', PAGE.read_text(), re.S)]


class Aq14B521FieldViews(unittest.TestCase):
    def setUp(self):
        self.blocks = page_json_blocks()

    def test_documented_examples_match_reference(self):
        pairs = [(self.blocks[0], self.blocks[1]), (self.blocks[2], self.blocks[3])]
        for given, expected in pairs:
            self.assertEqual(evaluate(json.dumps(given)), expected)

    def test_missing_field_is_incomplete_with_partial_aggregate(self):
        given = json.loads(json.dumps(self.blocks[0]))
        del given['fields']['temperature1']
        result = evaluate(json.dumps(given))
        self.assertEqual(result['state'], 'partial')
        self.assertEqual(result['results']['temperature1'],
                         {'state': 'incomplete', 'grade': 'Hypothesis'})
        self.assertEqual(result['results']['temperature0']['number'], -0.125)
        for raw in ([0], [], [0, 128, 0]):
            given['fields']['temperature1'] = raw
            entry = evaluate(json.dumps(given))['results']['temperature1']
            self.assertEqual(entry, {'state': 'incomplete', 'grade': 'Hypothesis', 'raw': raw})

    def test_reserved_output_keys_are_rejected(self):
        for key in RESERVED:
            given = json.loads(json.dumps(self.blocks[0]))
            given[key] = 'caller-value'
            with self.assertRaises(ValueError):
                evaluate(json.dumps(given))
        text = PAGE.read_text()
        for key in RESERVED:
            self.assertIn('`%s`' % key, text)

    def test_admission_errors(self):
        base = self.blocks[0]
        for bad in ('{"context":{},"fields":{"a":[255.5]},"fields":{}}',
                    json.dumps(dict(base, fields={'status0': [255.5]})),
                    json.dumps(dict(base, fields={'status0': ['1']})),
                    json.dumps(base) + '{}'):
            with self.assertRaises(ValueError):
                evaluate(bad)

    def test_page_vocabulary(self):
        text = PAGE.read_text()
        self.assertIn('`incomplete`', text)
        self.assertNotIn('"state":"partial","grade"', text)
        self.assertRegex(text, r'aggregate\s+`state`')


if __name__ == '__main__':
    unittest.main()
