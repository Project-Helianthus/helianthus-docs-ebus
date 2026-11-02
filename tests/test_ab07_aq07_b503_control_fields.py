"""Synthetic reference oracle for the local B503 control-field evaluator contract.

No production implementation is exercised; the page examples are checked
against this independent oracle and the admission rules are asserted directly.
"""
import json
from pathlib import Path
import re
import unittest

PAGE = Path(__file__).resolve().parents[1] / 'architecture' / 'aq08_b503_control_fields.md'
RESERVED = ('state', 'results', 'physical', 'qualified')
UNKNOWN = 'Unknown'
VIEWS = {
    ('reset-acceptance', 3, 'positive'): {'acceptance': 1},
    ('reset-acceptance', 6, 'positive'): {'acceptance': 1},
    ('current-errors', 7, 'positive'): dict(
        [('flags', 1)] + [('error%d' % i, 2) for i in range(5)] + [('feedback', 1)]),
    ('category-common', 4, 'request'): {'category': 1},
    ('category-reset', 3, 'request'): {'category': 1},
    ('category-reset', 6, 'request'): {'category': 1},
}


class Rejected(Exception):
    pass


def no_duplicates(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise Rejected('duplicate key')
    return dict(pairs)


def no_constant(_):
    raise Rejected('nonfinite')


def is_byte(v):
    return type(v) is int and 0 <= v <= 255


def evaluate(text):
    try:
        data = json.loads(text, object_pairs_hook=no_duplicates, parse_constant=no_constant)
    except (ValueError, RecursionError) as exc:
        raise Rejected(str(exc))
    if type(data) is not dict or any(k in data for k in RESERVED):
        raise Rejected('shape or reserved key')
    ctx, fields = data.get('context'), data.get('fields')
    if type(ctx) is not dict or type(fields) is not dict:
        raise Rejected('kinds')
    if 'arguments' in data and type(data['arguments']) is not dict:
        raise Rejected('arguments')
    for key in ('primary', 'secondary', 'operation'):
        if key in ctx and not is_byte(ctx[key]):
            raise Rejected(key)
    for raw in fields.values():
        if type(raw) is not list or not all(is_byte(b) for b in raw):
            raise Rejected('field bytes')
    out = dict(data)
    out.update(physical=UNKNOWN, qualified=False)
    spec = None
    if ctx.get('primary') == 181 and ctx.get('secondary') == 3 and 'operation' in ctx:
        spec = VIEWS.get((ctx.get('view'), ctx['operation'], ctx.get('direction')))
    if spec is None:
        out.update(state=UNKNOWN, results={})
        return out
    results, partial = {}, False
    for name, width in spec.items():
        raw = fields.get(name)
        if raw is None:
            results[name] = {'state': 'incomplete'}
            partial = True
        elif len(raw) != width:
            results[name] = {'raw': raw, 'state': 'incomplete'}
            partial = True
        else:
            results[name] = interpret(ctx['view'], name, raw)
    out.update(state='partial' if partial else 'complete', results=results)
    return out


def interpret(view, name, raw):
    res = {'raw': raw, 'state': 'complete', 'grade': 'Hypothesis'}
    if name.startswith('error'):
        res['number'] = raw[0] + 256 * raw[1]
        res['calculation'] = 'Proven'
    elif name == 'flags':
        res['flags'] = [bool((raw[0] >> i) & 1) for i in range(5)]
        res['reserved'] = raw[0] & 0xE0
        res['calculation'] = 'Proven'
    elif name == 'feedback':
        res['label'] = 'accepted' if raw[0] == 1 else 'rejected'
    elif view == 'reset-acceptance':
        res['label'] = {0: False, 1: True}.get(raw[0], UNKNOWN)
    elif view == 'category-common':
        res['label'] = 'predictive-maintenance' if raw[0] == 2 else UNKNOWN
        res['candidate_domain'] = [1, 2, 3, 4, 5]
    else:
        res['label'] = {1: 'error', 3: 'status'}.get(raw[0], UNKNOWN)
    return res


def base(**fields):
    return json.dumps({'context': {'primary': 181, 'secondary': 3, 'operation': 7,
                                   'direction': 'positive', 'view': 'current-errors'},
                       'fields': fields})


class Ab07Aq07Test(unittest.TestCase):
    def blocks(self):
        return re.findall(r'```json\n(.*?)\n```', PAGE.read_text(), re.S)

    def test_TestAb07Aq07_page_examples_match_oracle(self):
        blocks = self.blocks()
        self.assertEqual(len(blocks), 4)
        for src, expected in ((blocks[0], blocks[1]), (blocks[2], blocks[3])):
            self.assertEqual(evaluate(src), json.loads(expected))

    def test_TestAb07Aq07_reserved_keys_rejected(self):
        for key in RESERVED:
            doc = json.loads(base(flags=[0]))
            doc[key] = 1
            with self.assertRaises(Rejected):
                evaluate(json.dumps(doc))
        doc = json.loads(base(flags=[0]))
        doc['extra'] = {'state': 1}
        self.assertEqual(evaluate(json.dumps(doc))['extra'], {'state': 1})

    def test_TestAb07Aq07_rejections(self):
        bad = [base(acceptance=[True]), base(a=[1.5]), base(a=[256]), base(a=[-1]),
               base(a='x'), base(a=None), base(a=[1]) + ' {}', '{"a":1,"a":2}',
               '{"context":{},"fields":{"a":[NaN]}}',
               base(a=[1]).replace('"operation": 7', '"operation": null'),
               base(a=[1]).replace('181', '181.5'),
               '{"context":{},"fields":{},"arguments":[]}']
        for text in bad:
            with self.assertRaises(Rejected, msg=text):
                evaluate(text)

    def test_TestAb07Aq07_width_and_siblings(self):
        full = dict(flags=[31], error0=[1, 0], error1=[0, 1], error2=[52, 18],
                    error3=[0, 0], error4=[255, 255], feedback=[2])
        out = evaluate(base(**full))
        self.assertEqual([out['results']['error%d' % i]['number'] for i in range(5)],
                         [1, 256, 4660, 0, 65535])
        del full['error2']
        out = evaluate(base(**full))
        self.assertEqual(out['state'], 'partial')
        self.assertEqual(out['results']['error2'], {'state': 'incomplete'})
        self.assertNotIn('error2', out['fields'])
        self.assertEqual(out['results']['error4']['number'], 65535)
        for raw in ([], [52], [52, 18, 0]):
            full['error2'] = raw
            res = evaluate(base(**full))['results']['error2']
            self.assertEqual(res, {'raw': raw, 'state': 'incomplete'})

    def test_TestAb07Aq07_flags_and_views(self):
        res = evaluate(base(flags=[224]))['results']['flags']
        self.assertEqual((res['flags'], res['reserved']), ([False] * 5, 224))
        self.assertEqual(evaluate(base(feedback=[1]))['results']['feedback']['label'], 'accepted')

        def view(name, op, direction, **fields):
            return evaluate(json.dumps({'context': {
                'primary': 181, 'secondary': 3, 'operation': op,
                'direction': direction, 'view': name}, 'fields': fields}))['results']
        self.assertEqual(view('reset-acceptance', 3, 'positive', acceptance=[0])
                         ['acceptance']['label'], False)
        self.assertEqual(view('reset-acceptance', 6, 'positive', acceptance=[2])
                         ['acceptance']['label'], UNKNOWN)
        self.assertEqual(view('reset-acceptance', 3, 'positive')['acceptance'],
                         {'state': 'incomplete'})
        self.assertEqual(view('category-common', 4, 'request', category=[2])
                         ['category']['label'], 'predictive-maintenance')
        self.assertEqual(view('category-common', 4, 'request', category=[3])
                         ['category']['candidate_domain'], [1, 2, 3, 4, 5])
        self.assertEqual(view('category-reset', 3, 'request', category=[2])
                         ['category']['label'], UNKNOWN)
        self.assertEqual(view('category-reset', 6, 'request', category=[3])
                         ['category']['label'], 'status')

    def test_TestAb07Aq07_absent_operation_is_unknown(self):
        text = json.dumps({'context': {'primary': 181, 'secondary': 3,
                                       'direction': 'positive', 'view': 'current-errors'},
                           'fields': {}})
        self.assertEqual(evaluate(text)['state'], UNKNOWN)


if __name__ == '__main__':
    unittest.main()
