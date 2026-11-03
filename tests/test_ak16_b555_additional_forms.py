#!/usr/bin/env python3
"""Finite documentation oracle, not execution of the registry companion."""
import copy
import itertools
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / 'protocols/vaillant/ebus-b555-additional-forms.md'
DATA = ROOT / 'protocols/vaillant/fixtures/ak16_b555_additional_forms.json'
API = ROOT / 'architecture/ak16_b555_additional_forms_api.md'
GLOBALS = ('dhw', 'circulation', 'noise_reduction', 'ventilation', 'high_tariff')
CHANNEL_FIELDS = ('zone_heating', 'zone_cooling', 'external_dhw', 'external_fixed_flow')
# Literal independent coordinates: do not derive the oracle from fixture formulae.
CHANNELS = ((1, 2, 0), (2, 2, 4), (3, 3, 0), (4, 3, 4),
            (5, 4, 0), (6, 4, 4), (7, 5, 0), (8, 5, 4),
            (9, 6, 0), (10, 6, 4), (11, 7, 0), (12, 7, 4))
A4_FIELDS = (('status', 0, 1, 'u8'), ('monday', 1, 1, 'u8'),
             ('tuesday', 2, 1, 'u8'), ('wednesday', 3, 1, 'u8'),
             ('thursday', 4, 1, 'u8'), ('friday', 5, 1, 'u8'),
             ('saturday', 6, 1, 'u8'), ('sunday', 7, 1, 'u8'),
             ('count_24_hour', 8, 1, 'u8'))
A5_FIELDS = (('status', 0, 1, 'u8'), ('start_hour', 1, 1, 'u8'),
             ('start_minute', 2, 1, 'u8'), ('end_hour', 3, 1, 'u8'),
             ('end_minute', 4, 1, 'u8'), ('setpoint_raw', 5, 2, 'u16_le'))
AXES = (('Ab26Family', 'string'), ('Ab26Variant', 'string'),
        ('Ab26Primary', 'uint8'), ('Ab26Secondary', '*uint8'),
        ('Ab26Operation', '*uint8'), ('Ab26Direction', 'string'),
        ('Ab26Field', 'string'), ('Ab26Alternative', 'string'),
        ('Ab26Group', '*uint8'), ('Ab26InstanceScope', 'string'),
        ('Ab26Register', '*uint16'))
UNKNOWN = ['native_support', 'physical_qualification', 'physical_adaptation',
           'persistence', 'delivery']
POLICY = {
    'package': 'vaillant',
    'entries_signature': 'Ab26Entries() (json.RawMessage, error)',
    'lookup_signature': 'Ab26Lookup(Ab26Key) (json.RawMessage, bool, error)',
    'key_axes': [list(axis) for axis in AXES], 'optional_presence': 'distinct',
    'lookup': 'exact_whole_row', 'missing': 'false', 'invalid_json': 'error',
    'duplicate_keys': 'error', 'copies': 'independent_deep_bytes',
    'row_id_prefix': 'ab26-', 'row_grade': 'Hypothesis', 'row_unknown': UNKNOWN,
    'retain_raw': True,
    'extent_axes': ['declared_extent', 'accessible_extent', 'initialized_extent',
                    'storage_length'], 'extent_rule': 'minimum_of_all_four',
    'a4_complete_bytes': 9, 'a5_complete_bytes': 7,
    'count_supplies_extent': False, 'capacity_supplies_extent': False,
    'threshold_supplies_extent': False, 'status_supplies_extent': False,
    'status_is_acceptance': False, 'raw_setpoint_scale': 1,
    'ffff_sentinel': 'Unknown', 'hour_domain': [0, 24], 'minute_domain': [0, 59],
}


def page_policy():
    return json.loads(re.search(r'```json\n(.*?)\n```', API.read_text(), re.S)[1])


def table(text, header):
    lines = text.split(header + '\n', 1)[1].splitlines()[1:]
    result = []
    for line in lines:
        if not line.startswith('|'):
            break
        result.append(tuple(cell.strip() for cell in line.strip('|').split('|')))
    return result


def project_mask(form, raw):
    """Test-local projection driven by the published finite coordinate table."""
    value = int.from_bytes(bytes(raw[:form['reply_bytes']]), 'little')
    global_true = [f['field'] for f in form['global_fields']
                   if value & (1 << (8 * f['byte'] + f['bit']))]
    channel_true = [[c['channel'], field] for c in form['channels']
                    for bit, field in enumerate(form['channel_fields'])
                    if value & (1 << (8 * c['byte'] + c['bit'] + bit))]
    reserved = [raw[r['byte']] & (((1 << r['width_bits']) - 1) << r['bit'])
                for r in form['reserved']]
    return {'command': form['command'], 'raw': list(raw),
            'global_true': global_true, 'channel_true': channel_true,
            'reserved_raw': reserved, 'meaning': form['meaning']}


def bounded_view(form, policy, storage, declared, accessible, initialized,
                 local_count, numeric_threshold, previous=None):
    """Documentation model only; count and threshold are deliberately separate."""
    extents = (declared, accessible, initialized, len(storage))
    if any(type(n) is not int or n < 0 for n in extents):
        raise ValueError('invalid extent')
    limit = min(extents)
    fields = {}
    domains = {}
    for f in form['fields']:
        start, end = f['byte'], f['byte'] + f['width_bytes']
        if end <= limit:
            value = int.from_bytes(bytes(storage[start:end]), 'little')
            if f['field'] == 'setpoint_raw':
                value *= policy['raw_setpoint_scale']
            fields[f['field']] = value
            if 'domain' in f:
                domains[f['field']] = f['domain'][0] <= value <= f['domain'][1]
    complete_bytes = policy[form['command'].lower() + '_complete_bytes']
    complete = (limit >= complete_bytes and accessible <= len(storage)
                and initialized <= len(storage))
    merged = dict(previous or {})
    merged.update(fields)
    return {'fields': fields, 'last_known_good': merged, 'complete': complete,
            'raw': storage[:min(accessible, initialized, len(storage))],
            'domain_valid': domains}


def exact_key(key, policy):
    return tuple(key[axis] for axis, _ in policy['key_axes'])


def catalog(encoded, policy, query=None):
    """Test-local executable specification; no companion runtime is invoked."""
    rows = json.loads(encoded)
    if not isinstance(rows, list):
        raise ValueError('not array')
    keys = [exact_key(row['Ab26Key'], policy) for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate keys')
    if query is None:
        return bytearray(json.dumps(rows).encode())
    target = exact_key(query, policy)
    if target not in keys:
        return None, False
    return bytearray(json.dumps(rows[keys.index(target)]).encode()), True


def row():
    return {'Ab26ID': 'ab26-synthetic-mask', 'Ab26Key': {
        'Ab26Family': 'B555', 'Ab26Variant': 'additional-forms',
        'Ab26Primary': 181, 'Ab26Secondary': 85, 'Ab26Operation': 160,
        'Ab26Direction': 'reply', 'Ab26Field': 'function-channel-mask',
        'Ab26Alternative': 'none', 'Ab26Group': None,
        'Ab26InstanceScope': 'none', 'Ab26Register': None},
        'Ab26Fields': {'raw_mask': [1, 0, 0, 0, 0, 0, 0, 128]},
        'Ab26Relations': ['availability'], 'Ab26Grade': 'Hypothesis',
        'Ab26Unknown': list(UNKNOWN), 'Ab26Raw': [1, 0, 0, 0, 0, 0, 0, 128]}


class AdditionalForms(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DATA.read_text())
        self.forms = {f['command']: f for f in self.data['forms']}
        self.policy = page_policy()

    def test_native_finite_inventory_and_grades(self):
        self.assertEqual(len(self.data['forms']), 8)
        self.assertEqual(set(self.forms), {'A0', 'A7', 'A1', 'A2', 'A8', 'A9', 'A4', 'A5'})
        self.assertEqual(self.data['grade'], 'Hypothesis')
        self.assertEqual(self.data['qualification'], 'Unknown')
        self.assertEqual(self.data['coordinate_basis'],
                         'immediately after command; not physical payload base')
        self.assertEqual(self.data['unknown'], ['physical_adaptation', 'physical_offsets',
                         'prefix_presence', 'other_timer_variants', 'native_support',
                         'physical_effects', 'persistence', 'delivery'])
        for command, meaning in [('A0', 'availability'), ('A7', 'visibility')]:
            f = self.forms[command]
            self.assertEqual(f['meaning'], meaning)
            self.assertEqual(f['request_parameters'], [])
            self.assertEqual(f['reply_bytes'], 8)
            self.assertEqual(f['global_fields'], [
                {'field': field, 'byte': 0, 'bit': bit, 'width_bits': 1}
                for bit, field in enumerate(GLOBALS)])
            self.assertEqual(f['reserved'], [{'byte': 0, 'bit': 5, 'width_bits': 3},
                                              {'byte': 1, 'bit': 0, 'width_bits': 8}])
            self.assertEqual(f['channel_fields'], list(CHANNEL_FIELDS))
            self.assertEqual(f['channels'], [dict(channel=n, byte=b, bit=s, width_bits=4)
                                             for n, b, s in CHANNELS])

    def test_native_page_tables_independently(self):
        text = NATIVE.read_text()
        self.assertEqual(table(text, '| Command | Request parameters | Reply bytes | Candidate meaning |'),
                         [('A0', 'none', '8', 'availability'), ('A7', 'none', '8', 'visibility'),
                          *[(c, 'none', '6', 'reserved') for c in ('A1', 'A2', 'A8', 'A9')]])
        self.assertEqual(table(text, '| Global field | Byte | Bit | Width in bits |'),
                         [(f, '0', str(i), '1') for i, f in enumerate(GLOBALS)] +
                         [('reserved', '0', '5', '3'), ('reserved', '1', '0', '8')])
        self.assertEqual(table(text, '| Channel | Byte | Starting bit | Width in bits |'),
                         [(str(n), str(b), str(s), '4') for n, b, s in CHANNELS])
        for command, expected in [('A4', A4_FIELDS), ('A5', A5_FIELDS)]:
            self.assertEqual(table(text, f'| {command} field | Byte | Width in bytes | Encoding |'),
                             [(n, str(b), str(w), e) for n, b, w, e in expected])

    def test_synthetic_masks_every_bit_and_same_raw_different_meaning(self):
        expected = []
        for command, meaning in [('A0', 'availability'), ('A7', 'visibility')]:
            vectors = []
            for bit, field in enumerate(GLOBALS):
                vectors.append(([1 << bit] + [0] * 7, [field], [], [0, 0]))
            for n, byte, start in CHANNELS:
                for bit, field in enumerate(CHANNEL_FIELDS):
                    raw = [0] * 8
                    raw[byte] = 1 << (start + bit)
                    vectors.append((raw, [], [[n, field]], [0, 0]))
            for byte, mask in [(0, 32), (0, 64), (0, 128),
                               (1, 1), (1, 2), (1, 4), (1, 8),
                               (1, 16), (1, 32), (1, 64), (1, 128)]:
                raw = [0] * 8
                raw[byte] = mask
                vectors.append((raw, [], [], [raw[0], raw[1]]))
            vectors.append(([255] * 8, list(GLOBALS),
                            [[n, f] for n in range(1, 13) for f in CHANNEL_FIELDS], [224, 255]))
            for raw, global_true, channel_true, reserved_raw in vectors:
                case = dict(command=command, raw=raw, global_true=global_true,
                            channel_true=channel_true, reserved_raw=reserved_raw, meaning=meaning)
                expected.append(case)
                with self.subTest(command=command, raw=raw):
                    self.assertEqual(project_mask(self.forms[command], raw), case)
        actual = [c for c in self.data['synthetic_cases'] if c['command'] in ('A0', 'A7')]
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 130)
        for a0, a7 in zip(actual[:65], actual[65:]):
            self.assertEqual(a0['raw'], a7['raw'])
            self.assertNotEqual(a0['meaning'], a7['meaning'])

    def test_reserved_forms_never_settings(self):
        expected = []
        for command in ('A1', 'A2', 'A8', 'A9'):
            self.assertEqual(self.forms[command], {'command': command, 'meaning': 'reserved',
                'request_parameters': [], 'reply_bytes': 6,
                'reserved': [{'byte': 0, 'bit': 0, 'width_bits': 48}]})
            expected.append(dict(command=command, raw=[0, 32, 85, 170, 128, 255],
                                 reserved_raw=[0, 32, 85, 170, 128, 255], meaning='reserved'))
        self.assertEqual([c for c in self.data['synthetic_cases'] if c['command'] in
                          ('A1', 'A2', 'A8', 'A9')], expected)

    def test_timer_tables_and_examples(self):
        for command, expected, span in [('A4', A4_FIELDS, 9), ('A5', A5_FIELDS, 7)]:
            self.assertEqual(self.forms[command]['reply_bytes'], span)
            self.assertEqual([(f['field'], f['byte'], f['width_bytes'], f['encoding'])
                              for f in self.forms[command]['fields']], list(expected))
        a5 = self.forms['A5']['fields']
        self.assertEqual([f.get('domain') for f in a5],
                         [None, [0, 24], [0, 59], [0, 24], [0, 59], None])
        self.assertEqual((a5[-1]['unit'], a5[-1]['sentinel']), ('Unknown', 'Unknown'))
        cases = [c for c in self.data['synthetic_cases'] if c['command'] in ('A4', 'A5')]
        self.assertEqual(cases, [
            dict(command='A4', raw=[0, 1, 2, 3, 4, 5, 6, 7, 8, 238],
                 fields=dict(zip([f[0] for f in A4_FIELDS], range(9))), extra_raw=[238]),
            dict(command='A5', raw=[3, 24, 59, 0, 0, 255, 255, 238],
                 fields=dict(status=3, start_hour=24, start_minute=59, end_hour=0,
                             end_minute=0, setpoint_raw=65535), extra_raw=[238])])
        self.assertEqual(len(self.data['synthetic_cases']), 136)
        for case in cases:
            raw = case['raw']
            out = bounded_view(self.forms[case['command']], self.policy, raw,
                               len(raw), len(raw), len(raw), 0, 0)
            self.assertEqual(out['fields'], case['fields'])
            self.assertEqual(out['raw'], raw)
            self.assertTrue(out['complete'])
            self.assertEqual(out['raw'][self.forms[case['command']]['reply_bytes']:],
                             case['extra_raw'])

    def test_extent_matrix_independent_axes(self):
        # 2 commands x 3^3 extent combinations x 3 counts x 3 thresholds.
        for command, extents, storage in [
                ('A4', (8, 9, 10), [0, 1, 2, 3, 4, 5, 6, 7, 8, 238]),
                ('A5', (6, 7, 8), [0, 24, 59, 0, 0, 255, 255, 238])]:
            for accessible, declared, initialized, count, threshold in itertools.product(
                    extents, extents, extents, (0, 1, 999), (0, 8, 999)):
                with self.subTest(command=command, accessible=accessible, declared=declared,
                                  initialized=initialized, count=count, threshold=threshold):
                    out = bounded_view(self.forms[command], self.policy, storage, declared,
                                       accessible, initialized, count, threshold)
                    required = 9 if command == 'A4' else 7
                    self.assertEqual(out['complete'], all(
                        v >= required for v in (accessible, declared, initialized)))
                    literal_fields = A4_FIELDS if command == 'A4' else A5_FIELDS
                    expected = {name: int.from_bytes(bytes(storage[b:b+w]), 'little')
                                for name, b, w, _ in literal_fields
                                if all(v >= b+w for v in (accessible, declared, initialized))}
                    self.assertEqual(out['fields'], expected)
                    self.assertEqual(out['raw'], storage[:min(accessible, initialized)])

    def test_capacity_cannot_supply_received_or_initialized_bytes(self):
        for accessible, initialized, complete in [(6, 16, False), (7, 6, False),
                                                    (7, 7, True), (16, 16, True)]:
            storage = [0, 1, 2, 3, 4, 255, 255] + [238] * 9
            out = bounded_view(self.forms['A5'], self.policy, storage, 16,
                               accessible, initialized, 999, 999)
            self.assertEqual(out['complete'], complete)
            self.assertEqual('setpoint_raw' in out['fields'], complete)
            self.assertEqual(len(out['raw']), min(accessible, initialized))
        for command, storage in [('A4', [0] * 8), ('A5', [0] * 6)]:
            for accessible, initialized in [(16, 16), (16, len(storage)),
                                             (len(storage), 16)]:
                out = bounded_view(self.forms[command], self.policy, storage, 16,
                                   accessible, initialized, 999, 999)
                self.assertFalse(out['complete'])
                self.assertEqual(out['raw'], storage)

    def test_status_and_domain_are_independent_of_field_presence(self):
        for status in (0, 1, 3, 255):
            for command, raw in [('A4', [status, 1, 2, 3, 4, 5, 6, 7, 8]),
                                 ('A5', [status, 24, 59, 0, 0, 255, 255])]:
                out = bounded_view(self.forms[command], self.policy, raw,
                                   len(raw), len(raw), len(raw), 0, 0)
                self.assertTrue(out['complete'])
                self.assertEqual(out['fields']['status'], status)
        for index, name, limit in [(1, 'start_hour', 24), (2, 'start_minute', 59),
                                   (3, 'end_hour', 24), (4, 'end_minute', 59)]:
            for value in (0, limit, limit+1, 255):
                raw = [0, 1, 2, 3, 4, 255, 255]
                raw[index] = value
                out = bounded_view(self.forms['A5'], self.policy, raw, 7, 7, 7, 0, 0)
                self.assertTrue(out['complete'])
                self.assertEqual(out['fields'][name], value)
                self.assertEqual(out['domain_valid'][name], value <= limit)
                self.assertEqual(out['fields']['setpoint_raw'], 65535)

    def test_each_timer_field_raw_value_and_partial_last_known_good(self):
        for command, literal, size in [('A4', A4_FIELDS, 9), ('A5', A5_FIELDS, 7)]:
            baseline = [0] * size
            for name, byte, width, _ in literal:
                for relative in range(width):
                    raw = list(baseline)
                    raw[byte+relative] = 1
                    out = bounded_view(self.forms[command], self.policy, raw,
                                       size, size, size, 0, 0)
                    self.assertEqual(out['fields'], {
                        field: (256**relative if field == name else 0)
                        for field, _, _, _ in literal})
            previous = {name: 42 for name, _, _, _ in literal}
            partial = bounded_view(self.forms[command], self.policy, baseline,
                                   size, size-1, size, 999, 999, previous)
            missing = literal[-1][0]
            self.assertNotIn(missing, partial['fields'])
            self.assertEqual(partial['last_known_good'][missing], 42)
            self.assertEqual(previous, {name: 42 for name, _, _, _ in literal})
            self.assertFalse(partial['complete'])

    def test_invalid_extents_fail_closed(self):
        for axis in range(3):
            for value in (-1, 1.5, True):
                extents = [7, 7, 7]
                extents[axis] = value
                with self.assertRaises(ValueError):
                    bounded_view(self.forms['A5'], self.policy, [0]*7,
                                 *extents, 0, 0)

    def test_exact_api_policy_and_key_type_table(self):
        self.assertEqual(self.policy, POLICY)
        self.assertEqual(table(API.read_text(), '| Ab26Key field | Go type | Matching |'),
                         [(axis, typ, 'exact, absent differs from zero' if typ.startswith('*')
                           else 'exact') for axis, typ in AXES])

    def test_every_identity_axis_alone_with_positive_control(self):
        # Each alternate differs only on the named axis and is a valid key value.
        changes = dict(Ab26Family='B524', Ab26Variant='other-form', Ab26Primary=180,
                       Ab26Secondary=0, Ab26Operation=167, Ab26Direction='request',
                       Ab26Field='reserved', Ab26Alternative='alternate',
                       Ab26Group=0, Ab26InstanceScope='dynamic', Ab26Register=0)
        self.assertEqual(set(changes), {axis for axis, _ in AXES})
        for axis, replacement in changes.items():
            with self.subTest(axis=axis):
                original = row()
                alternate = copy.deepcopy(original)
                alternate['Ab26ID'] = 'ab26-synthetic-control'
                alternate['Ab26Key'][axis] = replacement
                self.assertEqual(sum(original['Ab26Key'][a] != alternate['Ab26Key'][a]
                                     for a, _ in AXES), 1)
                single = json.dumps([original]).encode()
                self.assertEqual(catalog(single, self.policy, alternate['Ab26Key']), (None, False))
                encoded = json.dumps([original, alternate]).encode()
                self.assertEqual(json.loads(catalog(encoded, self.policy)), [original, alternate])
                for wanted in (original, alternate):
                    buf, found = catalog(encoded, self.policy, copy.deepcopy(wanted['Ab26Key']))
                    self.assertTrue(found)
                    self.assertEqual(json.loads(buf), wanted)

    def test_each_optional_axis_absent_zero_nonzero(self):
        for axis in ('Ab26Secondary', 'Ab26Operation', 'Ab26Group', 'Ab26Register'):
            rows = []
            for value in (None, 0, 1):
                item = row()
                item['Ab26ID'] = f'ab26-synthetic-{value}'
                item['Ab26Key'][axis] = value
                rows.append(item)
            for wanted in rows:
                buf, found = catalog(json.dumps(rows).encode(), self.policy, wanted['Ab26Key'])
                self.assertTrue(found)
                self.assertEqual(json.loads(buf), wanted)
                for other in rows:
                    if wanted is not other:
                        self.assertEqual(catalog(json.dumps([other]).encode(), self.policy,
                                                 wanted['Ab26Key']), (None, False))

    def test_entries_lookup_deep_copy_raw_grade_and_unknown(self):
        wanted = row()
        encoded = json.dumps([wanted]).encode()
        entries = catalog(encoded, self.policy)
        looked_up, found = catalog(encoded, self.policy, wanted['Ab26Key'])
        self.assertTrue(found)
        self.assertIsInstance(json.loads(entries), list)
        self.assertEqual(json.loads(looked_up), wanted)
        entries[:] = b'[]'
        looked_up[:] = b'{}'
        self.assertEqual(json.loads(catalog(encoded, self.policy)), [wanted])
        self.assertEqual(json.loads(catalog(encoded, self.policy, wanted['Ab26Key'])[0]), wanted)
        changed = json.loads(catalog(encoded, self.policy))
        changed[0]['Ab26Raw'][0] = 255
        changed[0]['Ab26Fields']['raw_mask'][0] = 255
        changed[0]['Ab26Unknown'].clear()
        self.assertEqual(json.loads(catalog(encoded, self.policy)), [wanted])
        self.assertEqual(wanted['Ab26Grade'], 'Hypothesis')
        self.assertEqual(wanted['Ab26Unknown'], UNKNOWN)
        self.assertTrue(wanted['Ab26ID'].startswith('ab26-'))

    def test_invalid_json_and_duplicate_keys_error_globally(self):
        wanted = row()
        unrelated = copy.deepcopy(wanted)
        unrelated['Ab26Key']['Ab26Operation'] = 167
        invalid = (b'[', b'{}', json.dumps([wanted, wanted]).encode(),
                   json.dumps([wanted, unrelated, unrelated]).encode())
        for encoded in invalid:
            for query in (None, wanted['Ab26Key'], unrelated['Ab26Key']):
                with self.subTest(encoded=encoded, query=query):
                    with self.assertRaises(ValueError):
                        catalog(encoded, self.policy, query)
        self.assertEqual(json.loads(catalog(b'[]', self.policy)), [])
        self.assertEqual(catalog(b'[]', self.policy, wanted['Ab26Key']), (None, False))

    def test_boundaries_and_required_contract_prose(self):
        native, architecture = NATIVE.read_text(), API.read_text()
        flat_native = ' '.join(native.split())
        flat_api = ' '.join(architecture.split())
        for phrase in ('**Hypothesis:**', '**Unknown:**', 'not physical empty packets',
                       'No physical offset subtraction or prefix rule',
                       'Other timer variants', 'FFFF remains numeric 65535',
                       'No A3 numeric-unit relationship is imported'):
            self.assertIn(phrase, flat_native)
        for phrase in ('**Proven:**', '**Hypothesis:**', '**Unknown:**',
                       'all nine accessible initialized bytes',
                       'all seven accessible initialized bytes',
                       'Storage 16 with accessible 6 does not complete A5',
                       'local count and numeric threshold never supply extent',
                       'independent deep byte copies on every call',
                       'error for invalid embedded JSON or duplicate keys',
                       'No wildcard or nearest-key lookup is permitted',
                       'No physical offset subtraction, prefix adaptation',
                       'A6 weekly refresh implementation',
                       'eBUS MCP compatibility and GraphQL parity',
                       'AK15 must merge before this page',
                       'The registry has no dependency back to this page',
                       'Nothing is stable before Helianthus 1.0',
                       'companion runtime, transport and hardware qualification',
                       'oracle does not execute the registry implementation'):
            self.assertIn(phrase, flat_api)
        cc0 = native + DATA.read_text()
        for forbidden in ('Ab26', 'json.RawMessage', 'initialized', 'local_count',
                          'local count', 'safe-decoder', 'GraphQL', 'MCP', 'Helianthus'):
            self.assertNotIn(forbidden, cc0)
        for page in (NATIVE, API):
            for target in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', page.read_text()):
                self.assertTrue((page.parent / target).is_file(), target)
        # Native links stay entirely within implementation-neutral public trees.
        for target in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', native):
            self.assertTrue((NATIVE.parent / target).resolve().is_relative_to(ROOT / 'protocols'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
