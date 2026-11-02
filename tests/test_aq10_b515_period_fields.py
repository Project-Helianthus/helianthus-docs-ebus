"""Bounded synthetic oracle for the B515 finite-period field contract.

No production implementation is exercised; the oracle restates the documented
admission rules and calculations so later edits to the page cannot silently
contradict them.
"""
import json
from decimal import Decimal
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'architecture' / 'aq10_b515_period_fields.md'
UNKNOWN = 'Unknown'


class Rejected(Exception):
    pass


def is_int(value, low, high):
    return type(value) is int and low <= value <= high


def reject_duplicates(pairs):
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise Rejected('duplicate key')
    return dict(pairs)


def reject_constant(name):
    raise Rejected('nonfinite number')


def parse_float(text):
    if float(text) in (float('inf'), float('-inf')):
        raise Rejected('nonfinite number')
    return Decimal(text)


def convert(raw):
    if not is_int(raw, 0, 255):
        raise Rejected('byte')
    if raw > 144:
        return {'raw': raw, 'state': UNKNOWN}
    minutes = 10 * raw
    return {'raw': raw, 'state': 'complete', 'minutes': minutes,
            'hour': minutes // 60, 'minute': minutes % 60,
            'label': '%02d:%02d' % (minutes // 60, minutes % 60)}


def evaluate(text):
    try:
        data = json.loads(text, object_pairs_hook=reject_duplicates,
                          parse_constant=reject_constant,
                          parse_float=parse_float)
    except ValueError as error:
        raise Rejected(str(error))
    if type(data) is not dict:
        raise Rejected('object')
    context, fields = data.get('context'), data.get('fields')
    arguments = data.get('arguments', {})
    if (type(context) is not dict or type(fields) is not dict
            or type(arguments) is not dict):
        raise Rejected('kind')
    for key in ('primary', 'secondary'):
        if not is_int(context.get(key), 0, 255):
            raise Rejected(key)
    for key in ('direction', 'view'):
        if type(context.get(key)) is not str or not context[key]:
            raise Rejected(key)
    if 'operation' in context and not is_int(context['operation'], 0, 255):
        raise Rejected('operation')
    for value in fields.values():
        if type(value) is not list or not all(is_int(b, 0, 255) for b in value):
            raise Rejected('field')
    if {'state', 'results', 'physical', 'qualified'} & set(data):
        raise Rejected('reserved output member')
    out = dict(data)
    out.update({'physical': UNKNOWN, 'qualified': False})
    view, direction = context.get('view'), context.get('direction')
    supported = (context['primary'] == 181 and context['secondary'] == 21
                 and 'operation' not in context)
    if view == 'intervals' and context['primary'] == 181 \
            and context['secondary'] == 21 and 'operation' not in context:
        pairs = arguments.get('pairs')
        if (type(pairs) is not list or len(pairs) != 3 or not all(
                type(p) is list and len(p) == 2 and all(is_int(b, 0, 255) for b in p)
                for p in pairs)):
            raise Rejected('pairs')
    if view == 'periods' and 'minutes' in arguments \
            and not is_int(arguments['minutes'], 0, 1440):
        raise Rejected('minutes')
    if view == 'periods' and supported and direction in ('request', 'positive'):
        results = {}
        for name in ('period0', 'period1', 'period2'):
            raw = fields.get(name)
            if raw is None:
                results[name] = {'state': 'incomplete'}
            elif len(raw) != 1:
                results[name] = {'raw': raw, 'state': 'incomplete'}
            else:
                results[name] = dict(convert(raw[0]), raw=raw)
                if results[name]['state'] == 'complete':
                    results[name].update(grade='Hypothesis', calculation='Proven')
        if 'minutes' in arguments:
            minutes = arguments['minutes']
            entry = {'raw': minutes}
            if minutes % 10:
                entry['state'] = UNKNOWN
            else:
                entry.update(state='complete', encoded=minutes // 10,
                             grade='Hypothesis', calculation='Proven')
            results['minutes'] = entry
        out['results'] = results
        out['state'] = 'complete' if all(
            r['state'] == 'complete' for r in results.values()) else 'partial'
    elif view == 'intervals' and supported and direction == 'request':
        pairs = arguments['pairs']
        rows = [{'raw': p, 'state': 'complete',
                 'label': 'disabled' if p[0] == p[1] else 'enabled-candidate',
                 'grade': 'Hypothesis', 'start': convert(p[0]),
                 'end': convert(p[1])} for p in pairs]
        starts = [p[0] for p in pairs]
        order = {'raw': starts, 'grade': 'Hypothesis'}
        if any(s > 144 for s in starts):
            order['state'] = UNKNOWN
        else:
            order.update(state='complete', calculation='Proven',
                         value=starts[0] < starts[1] < starts[2])
        out['results'] = {'pairs': rows, 'order': order}
        out['state'] = 'complete'
    else:
        out['results'] = {}
        out['state'] = UNKNOWN
    return out


def periods(fields, arguments=None, **context):
    base = {'primary': 181, 'secondary': 21, 'direction': 'positive',
            'view': 'periods'}
    base.update(context)
    body = {'context': base, 'fields': fields}
    if arguments is not None:
        body['arguments'] = arguments
    return json.dumps(body)


def intervals(pairs, **context):
    base = {'primary': 181, 'secondary': 21, 'direction': 'request',
            'view': 'intervals'}
    base.update(context)
    return json.dumps({'context': base, 'fields': {},
                       'arguments': {'pairs': pairs}})


FULL = {'period0': [0], 'period1': [54], 'period2': [144], 'mode': []}


class PeriodFieldContract(unittest.TestCase):
    def test_complete_and_label_domain(self):
        out = evaluate(periods(FULL, {'minutes': 540}))
        self.assertEqual(out['state'], 'complete')
        self.assertEqual(out['results']['period1']['label'], '09:00')
        self.assertEqual(out['results']['period2']['label'], '24:00')
        self.assertEqual(out['results']['minutes']['encoded'], 54)
        labels = {convert(r)['label'] for r in range(145)}
        self.assertEqual(len(labels), 145)
        self.assertEqual(out['fields']['mode'], [])

    def test_partial_keeps_complete_siblings(self):
        fields = {'period1': [], 'period2': [144]}
        out = evaluate(periods(fields))
        self.assertEqual(out['state'], 'partial')
        self.assertEqual(out['results']['period0'], {'state': 'incomplete'})
        self.assertEqual(out['results']['period1']['raw'], [])
        self.assertEqual(out['results']['period2']['minutes'], 1440)
        out = evaluate(periods(dict(FULL, period0=[0, 54])))
        self.assertEqual(out['state'], 'partial')
        self.assertEqual(out['results']['period1']['state'], 'complete')

    def test_unknown_conversions_and_inverse(self):
        out = evaluate(periods(dict(FULL, period0=[145], period1=[255]),
                               {'minutes': 545}))
        self.assertEqual(out['results']['period0'], {'raw': [145], 'state': UNKNOWN})
        self.assertNotIn('minutes', out['results']['period1'])
        self.assertEqual(out['results']['minutes'], {'raw': 545, 'state': UNKNOWN})
        self.assertEqual(out['results']['period2']['state'], 'complete')

    def test_unsupported_context_is_unknown(self):
        for text in (periods(FULL, operation=0),
                     intervals([[1, 1], [2, 3], [4, 5]], direction='positive')):
            out = evaluate(text)
            self.assertEqual(out['state'], UNKNOWN)
            self.assertEqual(out['results'], {})
            self.assertEqual(out['physical'], UNKNOWN)
            self.assertIs(out['qualified'], False)

    def test_extra_keys_retained(self):
        extra = {'empty': [], 'null': None, 'zero': 0, 'false': False}
        body = json.loads(periods(FULL))
        body['extra'] = extra
        self.assertEqual(evaluate(json.dumps(body))['extra'], extra)

    def test_finite_decimals_retained_losslessly(self):
        text = periods(FULL).replace(
            '"fields"', '"extra":{"tiny":1e-9999,"fine":0.1234567890123456789},"fields"')
        out = evaluate(text)
        self.assertEqual(out['extra']['tiny'], Decimal('1e-9999'))
        self.assertNotEqual(out['extra']['tiny'], 0)
        self.assertEqual(out['extra']['fine'], Decimal('0.1234567890123456789'))

    def test_rejections(self):
        collide = []
        for key in ('state', 'results', 'physical', 'qualified'):
            body = json.loads(periods(FULL))
            body[key] = None
            collide.append(json.dumps(body))
        bad = collide + [
            periods(FULL, {'minutes': 1441}), periods(FULL, {'minutes': -1}),
            periods(FULL, {'minutes': 1.5}), periods(FULL, {'minutes': '540'}),
            periods(FULL, {'minutes': None}), periods(FULL, {'minutes': True}),
            periods(FULL, {'minutes': None}, operation=0),
            periods(FULL, {'minutes': 1441}, direction='response'),
            periods(dict(FULL, period0='0')), periods(dict(FULL, period0=[256])),
            periods(FULL, operation=None), periods(FULL, primary=256),
            periods(FULL) + ' {}', '{"context":{},"context":{}}',
            periods(FULL, {'minutes': 540}).replace('540', 'NaN'),
            '{"context":{"primary":181,"secondary":21,"view":"periods"},'
            '"fields":{"period0":[0,0]},"fields":{}}',
            intervals([[1, 1], [2, 3]]),
            json.dumps({'context': {'primary': 181, 'secondary': 21,
                                    'view': 'periods'}, 'fields': FULL}),
            json.dumps({'context': {'primary': 181, 'secondary': 21,
                                    'direction': 'positive'}, 'fields': FULL}),
            periods(FULL, direction=None), periods(FULL, view=None),
            periods(FULL, view=[]), periods(FULL, direction=[]),
            periods(FULL, direction=''), periods(FULL, view=7),
            intervals([[1, 1], [2, 3]], direction='positive'),
            json.dumps({'context': {'primary': 181, 'secondary': 21,
                                    'direction': 'positive',
                                    'view': 'intervals'}, 'fields': {}}),
            periods(FULL).replace('"fields"', '"extra":{"big":1e999},"fields"'), intervals([[1, 1], [2, 3], [4, 256]]),
            intervals([[1, 1], [2, 3], [4]]),
            json.dumps({'context': {'primary': 181, 'secondary': 21,
                                    'direction': 'request', 'view': 'intervals'},
                        'fields': {}}),
        ]
        for text in bad:
            with self.assertRaises(Rejected, msg=text):
                evaluate(text)


class IntervalContract(unittest.TestCase):
    def test_complete_example(self):
        out = evaluate(intervals([[10, 10], [20, 30], [40, 50]]))
        self.assertEqual(out['state'], 'complete')
        rows, order = out['results']['pairs'], out['results']['order']
        self.assertEqual([r['label'] for r in rows],
                         ['disabled', 'enabled-candidate', 'enabled-candidate'])
        self.assertEqual(rows[1]['end']['label'], '05:00')
        self.assertEqual(order['value'], True)
        self.assertEqual(order['calculation'], 'Proven')

    def test_swapped_starts_false_classifications_unchanged(self):
        out = evaluate(intervals([[10, 10], [40, 30], [20, 50]]))
        self.assertIs(out['results']['order']['value'], False)
        self.assertEqual([r['label'] for r in out['results']['pairs']],
                         ['disabled', 'enabled-candidate', 'enabled-candidate'])

    def test_order_depends_only_on_starts(self):
        out = evaluate(intervals([[10, 10], [20, 255], [40, 50]]))
        self.assertIs(out['results']['order']['value'], True)
        self.assertEqual(out['results']['pairs'][1]['end']['state'], UNKNOWN)
        self.assertEqual(out['results']['pairs'][1]['label'], 'enabled-candidate')

    def test_unmapped_start_is_unknown(self):
        out = evaluate(intervals([[10, 10], [200, 30], [40, 50]]))
        order = out['results']['order']
        self.assertEqual(order['state'], UNKNOWN)
        self.assertNotIn('value', order)
        self.assertEqual(out['results']['pairs'][1]['label'], 'enabled-candidate')

    def test_equal_unmapped_pair_stays_disabled_and_odd_pairs_admitted(self):
        out = evaluate(intervals([[255, 255], [40, 30], [0, 0]]))
        rows = out['results']['pairs']
        self.assertEqual(rows[0]['label'], 'disabled')
        self.assertEqual(rows[0]['start']['state'], UNKNOWN)
        self.assertEqual(rows[1]['label'], 'enabled-candidate')


class DocumentAgreement(unittest.TestCase):
    def test_page_states_the_checked_rules(self):
        text = DOC.read_text()
        for needle in ('`results.order`', '145 labels', '`[[10,10],[20,255],[40,50]]`',
                       '`[[10,10],[200,30],[40,50]]`', 'only on the three starts'):
            self.assertIn(needle, text)
        self.assertNotIn('If any endpoint, including an end', text)

    def test_page_json_blocks_parse_and_match_oracle(self):
        text = DOC.read_text()
        blocks = [b.split('```')[0] for b in text.split('```json\n')[1:]]
        self.assertEqual(len(blocks), 3)
        data = [json.loads(b) for b in blocks]
        out = evaluate(blocks[0])
        for key in ('context', 'fields', 'arguments', 'extra', 'state',
                    'physical', 'qualified'):
            self.assertEqual(out[key], data[1][key])
        self.assertEqual(out['results'], data[1]['results'])
        self.assertEqual(set(out['results']),
                         {'period0', 'period1', 'period2', 'minutes'})
        interval = evaluate(intervals([[10, 10], [20, 30], [40, 50]]))
        documented = json.loads(json.dumps(data[2]))
        for row in documented['pairs']:
            self.assertEqual(row['grade'], 'Hypothesis')
        self.assertEqual(interval['results'], documented)


if __name__ == '__main__':
    unittest.main()
