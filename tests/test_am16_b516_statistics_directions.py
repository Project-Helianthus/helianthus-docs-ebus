"""Offline page/package conformance; no companion runtime or wire decoder."""
import copy
import json
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'architecture/fixtures/am16_b516_statistics_directions.json'
PAGE = ROOT / 'architecture/am16_b516_statistics_directions.md'
QUALIFICATIONS = ('physical_support', 'presence', 'freshness', 'execution',
                  'effects', 'persistence', 'delivery')
NATIVE = ('https://github.com/Project-Helianthus/helianthus-docs-ebus/'
          'blob/main/protocols/ebus-services/ebus-overview.md')
ORDER = ['Version', 'Build', 'TotalEnergies', 'Days', 'DailyEnergies',
         'Months', 'MonthlyEnergies', 'Years', 'YearlyEnergies']
ABSENT = object()


def key(variant, op, side, field, selector=ABSENT):
    result = dict(family='vaillant', variant=variant, operation=op,
                  direction=side, field=field)
    if selector is not ABSENT:
        result['selector'] = selector
    return result


def expected_catalog():
    """Independent finite oracle from the ticket, never loaded from AM15/data."""
    result = []
    ordinary = ['offsets', 'defaults', 'physical support']

    def add(variant, op, side, field, selector=ABSENT, **metadata):
        result.append(dict(key=key(variant, op, side, field, selector),
                           grade='Hypothesis', software_contract='Proven',
                           native_contract=NATIVE,
                           **dict.fromkeys(QUALIFICATIONS, 'Unknown'),
                           **dict(unknown=ordinary, **metadata)))

    # Unknown lists differ by field; override after construction to keep the
    # oracle explicit without importing any catalog-generating implementation.
    def unknown(*items):
        result[-1]['unknown'] = list(items)

    periods = {'time-base:0': 'total', 'time-base:1': 'daily',
               'time-base:2': 'monthly', 'time-base:3': 'yearly'}
    for variant, side, length, access, value_side in [
            ('ab72-statistics-read', 'request', 7, 2, False),
            ('ab72-statistics-read', 'positive', 11, None, True),
            ('ab72-statistics-write', 'request', 11, 2, True),
            ('ab72-statistics-write', 'positive', 7, 3, False)]:
        add(variant, 16, side, 'layout', length=length,
            rules=['Lengths are after the sub-ID.'])
        bits = {'time-base-low': 0, 'time-base-high': 1}
        if access is not None:
            bits['access'] = access
        values = dict(periods)
        if side == 'request':
            values.update({'access:0': 'read', 'access:1': 'write'})
        add(variant, 16, side, 'flags', bits=bits, values=values)
        if value_side:
            add(variant, 16, side, 'energy-value', width=32,
                encoding='binary32 LE', unit='Wh')
        for selector in (0, 255):
            add(variant, 16, side, 'period-index', selector,
                rules=['Total ignores period index and date.',
                       'Select by date.' if selector == 255 else
                       'Select table row; ignore date.'])
            unknown('date packing', 'offsets', 'defaults')
            add(variant, 16, side, 'energy-index', selector,
                rules=['Select energy type and operation mode.' if selector == 255
                       else 'Ignore energy type and operation mode.'])
        if side == 'positive':
            add(variant, 16, side, 'return-nibble', width=4,
                values={'0': 'value-contained', '1': 'NOK'})
            unknown('meanings 2..15', 'offsets')
    variant = 'ab72-statistics-index'
    add(variant, 17, 'request', 'layout', length=0)
    add(variant, 17, 'positive', 'ordered-fields', order=ORDER,
        rules=['Counts are returned metadata, not installed counts or enforced bounds.'])
    for position, field in enumerate(ORDER):
        add(variant, 17, 'positive', field, position=position, width=8, encoding='u8')
    for action in ('meter', 'clear'):
        for selector_type in ('scalar-u8', 'low-six-bits'):
            variant = f'ab72-{action}-{selector_type}'
            add(variant, 18, 'request', 'flags',
                bits={'total': 0, 'daily': 1, 'monthly': 2, 'yearly': 3},
                rules=['Four independent request bits.'])
            add(variant, 18, 'request', 'energy-selector', width=8, encoding='u8',
                bits={} if selector_type == 'scalar-u8' else {'sum-6': 6, 'sum-7': 7},
                rules=['Scalar u8 selector.' if selector_type == 'scalar-u8' else
                       'Low six bits selector; independent sum bits 6 and 7.'])
            add(variant, 18, 'request', 'mode', width=8, encoding='u8')
            add(variant, 18, 'positive', 'flags',
                bits={'not-supported': 0, 'energy-unavailable': 1, 'mode-unavailable': 2},
                conflicts=['Nested and outer duplicate flags; packing precedence Unknown.'])
            unknown('packing precedence', 'offsets', 'defaults',
                    'full variant-specific meter/clear tables')
    yields = {'0': 'solar', '1': 'environment', '2': 'energy', '3': 'gas-or-oil'}
    for variant, side, has_value in [
            ('ab72-yield-read', 'request', False),
            ('ab72-yield-read', 'positive', True),
            ('ab72-yield-write', 'request', True),
            ('ab72-yield-write', 'positive', False)]:
        add(variant, 24, side, 'yield-type', width=8, values=yields)
        if has_value:
            add(variant, 24, side, 'yield-value', width=32, encoding='LEu32', unit='kWh',
                rules=['All u32 values retain their raw numeric meaning; no sentinel inferred.'])
    add('ab72-yield-reset', 25, 'request', 'yield-type', width=8, values=yields)
    add('ab72-yield-reset', 25, 'positive', 'feedback', width=8, values={'1': 'accepted'})
    unknown('other feedback meanings', 'effects', 'persistence')
    for field, values in [('yield-type', yields), ('month', {}),
                          ('year-index', {'0': 'this-year', '1': 'last-year'}),
                          ('mode', {'0': 'all', '1': 'heating', '2': 'DHW'}), ('sum', {})]:
        extra = {'width': 32, 'encoding': 'LEu32'} if field == 'sum' else {}
        add('ab72-yield-month', 26, 'positive', field, values=values,
            conflicts=['Unit-type overlaps second sum byte.', 'Month 10/11 conflict.'], **extra)
        unknown('offsets', 'defaults', 'packing precedence', 'unit')
    return result


def parse_catalog(raw):
    """Local admission model, separate from the companion runtime parser."""
    entries = json.loads(raw)
    if not isinstance(entries, list) or not entries:
        raise ValueError('empty or non-list catalog')
    allowed = {'key', 'grade', 'software_contract', 'native_contract',
               *QUALIFICATIONS, 'length', 'position', 'width', 'encoding',
               'unit', 'bits', 'values', 'order', 'rules', 'conflicts', 'unknown'}
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) - allowed:
            raise ValueError('unknown entry field')
        k = entry.get('key', {})
        if set(k) - {'family', 'variant', 'operation', 'direction', 'selector', 'field'}:
            raise ValueError('unknown key field')
        if not all(k.get(n) for n in ('family', 'variant', 'field')):
            raise ValueError('incomplete key')
        if type(k.get('operation')) is not int or not 0 <= k['operation'] <= 255:
            raise ValueError('operation')
        if 'selector' in k and (type(k['selector']) is not int or not 0 <= k['selector'] <= 255):
            raise ValueError('selector')
        if k.get('direction') not in ('request', 'positive'):
            raise ValueError('direction')
        identity = json.dumps(k, sort_keys=True)
        if identity in seen:
            raise ValueError('duplicate key')
        seen.add(identity)
        if (entry.get('grade'), entry.get('software_contract'), entry.get('native_contract')) != (
                'Hypothesis', 'Proven', NATIVE):
            raise ValueError('evidence')
        if any(entry.get(n) != 'Unknown' for n in QUALIFICATIONS):
            raise ValueError('qualification')
        if any(type(b) is not int or not 0 <= b <= 7 for b in entry.get('bits', {}).values()):
            raise ValueError('bit')
        if 'width' in entry and (type(entry['width']) is not int or not 1 <= entry['width'] <= 32):
            raise ValueError('width')
    return copy.deepcopy(entries)


def lookup(entries, query):
    """Exact-key model with independent result storage, including absence."""
    for entry in entries:
        # Python bool/int equality must not make malformed coordinates match.
        if json.dumps(entry['key'], sort_keys=True) == json.dumps(query, sort_keys=True):
            return copy.deepcopy(entry)
    return None


def field_result(entries, query, raw, last_good=None):
    """Explicit field-slice model; never locates fields in native payloads."""
    output = dict(raw=copy.deepcopy(raw), value=None, unit=None,
                  status='unknown', last_good=copy.deepcopy(last_good))
    if not isinstance(raw, (list, bytearray, bytes)) or any(
            type(b) is not int or not 0 <= b <= 255 for b in raw):
        output['status'] = 'malformed'
        return output
    entry = lookup(entries, query)
    if entry is None:
        return output
    output['metadata'] = entry
    output['unit'] = entry.get('unit')
    if entry.get('conflicts'):
        output['status'] = 'conflict'
        return output
    codec = entry.get('encoding')
    size = {'binary32 LE': 4, 'LEu32': 4, 'u8': 1}.get(codec)
    if size is None:
        return output
    if len(raw) != size:
        output['status'] = 'partial' if len(raw) < size else 'extra'
        return output
    output['value'] = (struct.unpack('<f', bytes(raw))[0] if codec == 'binary32 LE'
                       else int.from_bytes(raw, 'little'))
    output['status'] = 'candidate'
    output['last_good'] = output['value']
    return output


def catalog_table(entries):
    common = {'key', 'grade', 'software_contract', 'native_contract', *QUALIFICATIONS}
    rows = ['| Variant | OP | Direction | Selector | Field | Metadata |',
            '| --- | --- | --- | --- | --- | --- |']
    for entry in entries:
        k = entry['key']
        metadata = {a: b for a, b in entry.items() if a not in common}
        rows.append('| ' + ' | '.join([
            k['variant'], f"{k['operation']:02X}", k['direction'],
            str(k.get('selector', 'absent')), k['field'],
            '`' + json.dumps(metadata, sort_keys=True, separators=(',', ':')) + '`']) + ' |')
    return '\n'.join(rows)


def example_table(examples):
    rows = ['| Case | Variant / OP / direction / field / selector | Field slice (hex) | Value | Unit | Status |',
            '| --- | --- | --- | --- | --- | --- |']
    for e in examples:
        rows.append('| ' + ' | '.join([
            e['case'], f"{e['variant']} / {e['operation']:02X} / {e['direction']} / {e['field']} / {e.get('selector', 'absent')}",
            ' '.join(f'{b:02X}' for b in e['raw']), str(e['value']), str(e['unit']), e['status']]) + ' |')
    return '\n'.join(rows)


class StatisticsContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = json.loads(FIXTURE.read_text())
        cls.entries = cls.package['catalog']
        cls.page = PAGE.read_text()

    def test_complete_independent_catalog(self):
        expected = expected_catalog()
        self.assertEqual(len(expected), 68)
        self.assertEqual(set(self.package), {'catalog', 'examples', 'conflict_evidence'})
        self.assertEqual(self.entries, expected)

    def test_page_catalog_and_examples_agree(self):
        def section(name):
            return self.page.split(f'<!-- {name}:start -->\n')[1].split(
                f'\n<!-- {name}:end -->')[0]
        self.assertEqual(section('catalog'), catalog_table(expected_catalog()))
        self.assertEqual(section('examples'), example_table(self.package['examples']))
        for text in ['**Hypothesis** applies to every candidate native meaning below. **Proven** applies',
                     'Physical support, presence, freshness,\nexecution, effects, persistence and delivery each remain **Unknown**',
                     'Date packing is Unknown in this candidate; no date codec is inferred.',
                     'Unit-type overlaps the second\nsum byte; month 10/11 conflict remains unresolved.',
                     'Counts are returned metadata, not installed counts or enforced\nbounds.',
                     'packing precedence is Unknown', 'No encoder, method registration or physical exchange',
                     'eBUS MCP compatibility and GraphQL parity',
                     'last-known-good candidate', 'all seven qualification properties `Unknown`']:
            self.assertIn(text, self.page)

    def test_each_key_axis_independently(self):
        # Every catalog entry is a valid control. Changing one axis must return
        # exactly the independent oracle's other entry or an explicit miss.
        expected = expected_catalog()
        independent = {json.dumps(e['key'], sort_keys=True): e for e in expected}
        alternatives = {
            'family': ['vaillant', 'other-family', '', None],
            'variant': sorted({e['key']['variant'] for e in expected}) + ['', 'unknown'],
            'operation': [0, 16, 17, 18, 24, 25, 26, 255, None, True],
            'direction': ['request', 'positive', 'response', '', None],
            'selector': [0, 1, 255, None, True],
            'field': sorted({e['key']['field'] for e in expected}) + ['', 'unknown'],
        }
        for entry in expected:
            original = entry['key']
            self.assertEqual(lookup(self.entries, original), entry)
            for axis, values in alternatives.items():
                for value in values:
                    query = dict(original, **{axis: value})
                    with self.subTest(key=original, axis=axis, value=value):
                        self.assertEqual(lookup(self.entries, query), independent.get(json.dumps(query, sort_keys=True)))
                missing = dict(original)
                missing.pop(axis, None)
                self.assertEqual(lookup(self.entries, missing), independent.get(json.dumps(missing, sort_keys=True)))
        query = key('ab72-statistics-read', 16, 'request', 'period-index', 0)
        self.assertIsNotNone(lookup(self.entries, query))
        query.pop('selector')
        self.assertIsNone(lookup(self.entries, query))
        query = key('ab72-statistics-index', 17, 'request', 'layout')
        self.assertEqual(lookup(self.entries, query)['length'], 0)
        query['operation'] = 0
        self.assertIsNone(lookup(self.entries, query))

    def test_op10_side_collision_and_flags(self):
        for variant, side, length, access, value in [
                ('ab72-statistics-read', 'request', 7, 2, False),
                ('ab72-statistics-read', 'positive', 11, None, True),
                ('ab72-statistics-write', 'request', 11, 2, True),
                ('ab72-statistics-write', 'positive', 7, 3, False)]:
            query = key(variant, 16, side, 'layout')
            self.assertEqual(lookup(self.entries, query)['length'], length)
            query['field'] = 'flags'
            bits = lookup(self.entries, query)['bits']
            self.assertEqual(bits.get('access'), access)
            if access is not None:
                for raw in (0, 4, 8, 12):
                    self.assertEqual((raw >> bits['access']) & 1,
                                     (raw // (2 ** access)) % 2)
            for raw in range(4):
                self.assertEqual((raw >> bits['time-base-low']) & 1, raw % 2)
                self.assertEqual((raw >> bits['time-base-high']) & 1, raw // 2)
            query['field'] = 'energy-value'
            self.assertEqual(lookup(self.entries, query) is not None, value)

    def test_op11_all_fields_and_partial_metadata(self):
        for count in range(10):
            raw = list(range(count))
            decoded = {}
            for field in ORDER:
                entry = lookup(self.entries, key('ab72-statistics-index', 17, 'positive', field))
                if entry['position'] < len(raw):
                    decoded[field] = raw[entry['position']]
            self.assertEqual(decoded, dict(zip(ORDER[:count], range(count))))
        # Zero is a returned value, not absent metadata or an installed bound.
        self.assertEqual(decoded['Version'], 0)
        self.assertEqual(len(decoded), 9)

    def test_op12_bits_selectors_duplicate_flags(self):
        for action in ('meter', 'clear'):
            for form in ('scalar-u8', 'low-six-bits'):
                variant = f'ab72-{action}-{form}'
                for side, names in [('request', ['total', 'daily', 'monthly', 'yearly']),
                                    ('positive', ['not-supported', 'energy-unavailable', 'mode-unavailable'])]:
                    entry = lookup(self.entries, key(variant, 18, side, 'flags'))
                    for index, name in enumerate(names):
                        raw = 2 ** index
                        got = {n: bool(raw & (1 << b)) for n, b in entry['bits'].items()}
                        self.assertEqual(got, {n: n == name for n in names})
                selector = lookup(self.entries, key(variant, 18, 'request', 'energy-selector'))
                for raw in (0, 1, 63, 64, 128, 192, 255):
                    if form == 'scalar-u8':
                        self.assertEqual(selector['bits'], {})
                        self.assertEqual(int.from_bytes(bytes([raw]), 'little'), raw)
                    else:
                        self.assertEqual(raw & 63, raw % 64)
                        for bit_name, shift in [('sum-6', 6), ('sum-7', 7)]:
                            self.assertEqual((raw >> selector['bits'][bit_name]) & 1,
                                             (raw // (2 ** shift)) % 2)
                flags = lookup(self.entries, key(variant, 18, 'positive', 'flags'))
                self.assertEqual(len(flags['conflicts']), 1)
                raw = {'outer': [1], 'nested': [2]}
                retained = copy.deepcopy(raw)
                self.assertNotEqual(retained['outer'], retained['nested'])
                self.assertIn('packing precedence', flags['unknown'])
                self.assertEqual(raw, retained)

    def test_examples_independent_numeric_results(self):
        examples = self.package['examples']
        self.assertEqual([e['case'] for e in examples], [
            'op10-wh', 'op10-write-wh', 'op18-maximum', 'op18-write-zero',
            'op18-partial', 'op18-extra', 'op1a-conflict', 'op10-unknown-date'])
        expected = [(1.0, 'Wh', 'candidate'), (2.0, 'Wh', 'candidate'),
                    ((1 << 32) - 1, 'kWh', 'candidate'), (0, 'kWh', 'candidate'),
                    (None, 'kWh', 'partial'), (None, 'kWh', 'extra'),
                    (None, None, 'conflict'), (None, None, 'unknown')]
        for e, want in zip(examples, expected):
            query = key(e['variant'], e['operation'], e['direction'], e['field'],
                        e.get('selector', ABSENT))
            output = field_result(self.entries, query, e['raw'])
            self.assertEqual((e['value'], e['unit'], e['status']), want)
            self.assertEqual((output['value'], output['unit'], output['status']), want)
            self.assertEqual(output['raw'], e['raw'])
        self.assertEqual(examples[0]['raw'], list(struct.pack('<f', 1.0)))
        self.assertEqual(examples[1]['raw'], list(struct.pack('<f', 2.0)))
        self.assertEqual(examples[2]['value'], int.from_bytes(bytes([255]*4), 'little'))
        self.assertEqual(examples[2]['raw'], [255]*4)
        self.assertEqual(examples[3]['raw'], [0]*4)

    def test_malformed_partial_extra_unknown_and_owned_raw(self):
        query = key('ab72-yield-read', 24, 'positive', 'yield-value')
        for raw in (None, 'FFFF', [-1], [256], [True], [1.0], {'byte': 0}):
            self.assertEqual(field_result(self.entries, query, raw)['status'], 'malformed')
        for raw, status in [([], 'partial'), ([1, 2, 3], 'partial'),
                            ([0]*5, 'extra'), ([0]*4, 'candidate')]:
            result = field_result(self.entries, query, raw, last_good=7)
            self.assertEqual(result['status'], status)
            self.assertEqual(result['last_good'], 0 if status == 'candidate' else 7)
            self.assertEqual(result['metadata']['unit'], 'kWh')
            result['raw'].append(9)
            self.assertNotEqual(raw, result['raw'])
        source = bytearray([1, 0, 0, 0])
        a = field_result(self.entries, query, source)
        b = field_result(self.entries, query, source)
        source[0] = 4
        a['raw'][0] = 9
        self.assertEqual(b['raw'], bytearray([1, 0, 0, 0]))
        self.assertEqual(b['value'], 1)
        self.assertEqual(field_result(self.entries, dict(query, family='other-family'), [0]*4)['status'], 'unknown')
        absent = field_result(self.entries, query, [])
        zero = field_result(self.entries, query, [0]*4)
        self.assertIsNone(absent['value'])
        self.assertEqual(zero['value'], 0)

    def test_all_nested_return_storage_is_owned(self):
        for entry in self.entries:
            original = copy.deepcopy(entry)
            a = lookup(self.entries, entry['key'])
            b = lookup(self.entries, entry['key'])
            a['key']['operation'] = 0
            a['unknown'].append('modified')
            for name, value in list(a.items()):
                if isinstance(value, dict):
                    value['modified'] = 99
                elif isinstance(value, list):
                    value.append('modified')
            self.assertEqual(b, original)
            self.assertEqual(entry, original)
        enumerated = copy.deepcopy(self.entries)
        enumerated[0]['key']['family'] = 'other-family'
        self.assertEqual(self.entries[0]['key']['family'], 'vaillant')

    def test_catalog_admission_malformed_extra_unknown_partial(self):
        self.assertEqual(parse_catalog(json.dumps(self.entries)), self.entries)
        for raw in ('', '[', '[]', '{}', json.dumps(self.entries) + ' []'):
            with self.subTest(raw=raw[:20]), self.assertRaises((ValueError, TypeError)):
                parse_catalog(raw)
        seed = self.entries[0]
        mutations = []
        for field, value in [('extra', 1), ('grade', 'Proven'),
                             ('software_contract', 'Hypothesis'),
                             ('native_contract', ''), ('bits', {'x': 8}), ('width', 0),
                             ('width', 33)]:
            mutations.append([dict(seed, **{field: value})])
        for field in QUALIFICATIONS:
            mutations.append([dict(seed, **{field: 'Proven'})])
        for field in ('family', 'variant', 'operation', 'direction', 'field'):
            candidate = copy.deepcopy(seed)
            candidate['key'].pop(field)
            mutations.append([candidate])
        mutations.extend([[dict(seed, key=dict(seed['key'], selector=None))],
                          [dict(seed, key=dict(seed['key'], extra=1))],
                          [seed, seed]])
        for candidate in mutations:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                parse_catalog(json.dumps(candidate))
        # Admission of structurally valid partial metadata does not confer
        # completeness; the independent finite-catalog assertion rejects it.
        partial = copy.deepcopy(self.entries[:-1])
        self.assertEqual(len(parse_catalog(json.dumps(partial))), 67)
        self.assertNotEqual(partial, expected_catalog())

    def test_conflict_evidence_never_flattened_or_repaired(self):
        expected = [
            {'case': 'duplicate-flags', 'variant': 'ab72-meter-low-six-bits',
             'operation': 18, 'direction': 'positive', 'outer_flags': [1],
             'nested_flags': [2], 'packing_precedence': 'Unknown'},
            {'case': 'month-overlap', 'variant': 'ab72-yield-month',
             'operation': 26, 'direction': 'positive', 'sum_raw': [1, 2, 3, 4],
             'unit_type_raw': [2], 'month_alternatives': [[10], [11]],
             'positions': None, 'unit': None, 'packing_precedence': 'Unknown'}]
        self.assertEqual(self.package['conflict_evidence'], expected)
        block = self.page.split('<!-- conflicts:start -->\n```json\n')[1].split(
            '\n```\n<!-- conflicts:end -->')[0]
        self.assertEqual(json.loads(block), expected)
        independent = copy.deepcopy(self.package['conflict_evidence'])
        independent[0]['outer_flags'][0] = 4
        independent[1]['sum_raw'][1] = 99
        self.assertEqual(self.package['conflict_evidence'], expected)
        for field in ('yield-type', 'month', 'year-index', 'mode', 'sum'):
            result = field_result(self.entries, key('ab72-yield-month', 26,
                                                   'positive', field), [10], last_good=3)
            self.assertEqual(result['status'], 'conflict')
            self.assertEqual(result['last_good'], 3)
            self.assertNotIn('position', result['metadata'])
            self.assertIsNone(result['unit'])

    def test_relative_links_resolve(self):
        links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', self.page)
        self.assertGreaterEqual(len(links), 5)
        for target in links:
            if '://' not in target:
                self.assertTrue((PAGE.parent / target.split('#')[0]).is_file(), target)


if __name__ == '__main__':
    unittest.main()
