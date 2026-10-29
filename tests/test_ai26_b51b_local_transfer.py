"""Bounded synthetic candidate oracle; never a programming executor."""
import binascii
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
# Independent expected declarations: changing either publication must fail.
TABLES = {
    'sequence': [
        ['08', 'block/segment selection', 'Hypothesis'],
        ['09', 'data', 'Hypothesis'], ['0A', 'write', 'Hypothesis'],
        ['0B', 'CRC', 'Hypothesis'], ['0C', 'status', 'Hypothesis'],
        ['0E', 'application', 'Hypothesis']],
    'budgets': [
        ['grouped', '206,206,206,206,200', '1024', 'accept', 'Hypothesis'],
        ['grouped', '206,206,206,206,201', '1024', 'reject', 'Hypothesis'],
        ['cap205', '205', '205', 'accept', 'Hypothesis'],
        ['cap205', '206', '205', 'reject', 'Hypothesis']],
    'progress': [
        ['200', 'rejected', '0', 'Hypothesis'],
        ['17', 'accepted', '17', 'Hypothesis'],
        ['17', 'pending', '0', 'Hypothesis'],
        ['17', 'unprovided', 'Unknown', 'Unknown']],
    'offset': [
        ['absent', 'valid', 'none', '00 00', 'Hypothesis'],
        ['absent', 'invalid', 'none', 'absent', 'Hypothesis'],
        ['absent', 'valid', '34 12', '34 12', 'Hypothesis'],
        ['78 56', 'valid', 'none', '78 56', 'Hypothesis']],
    'crc': [
        ['313233343536373839', 'FFFF', '29B1', 'B1 29', 'Proven'],
        ['empty', 'FFFF', 'FFFF', 'FF FF', 'Proven'],
        ['313233343536373839', '0000', '31C3', 'C3 31', 'Proven'],
        ['31323334', 'FFFF', '5349', '49 53', 'Proven'],
        ['3536373839', 'FFFF', '5EB6', 'B6 5E', 'Proven']],
    'crc_parameters': [
        ['polynomial', '1021', 'Hypothesis'],
        ['initial', 'FFFF', 'Hypothesis'], ['bit_order', 'MSB-first', 'Hypothesis'],
        ['reflection', 'false', 'Hypothesis'], ['final_xor', '0000', 'Hypothesis'],
        ['coverage', 'exact call input', 'Hypothesis']],
    'shapes': [
        ['06', '1', 'Hypothesis'], ['07', '1', 'Hypothesis'],
        ['08', '9', 'Hypothesis'], ['0A', '1', 'Hypothesis'],
        ['0B', '1', 'Hypothesis'], ['0C', '1', 'Hypothesis'],
        ['0D', '2', 'Hypothesis'], ['0E', '2', 'Hypothesis']],
    'route_data': [
        ['0', '3', '8', 'accept', 'Hypothesis'],
        ['13', '16', '21', 'accept', 'Hypothesis'],
        ['14', '17', '22', 'reject', 'Hypothesis']],
    'unknowns': [[name, 'Unknown'] for name in [
        'session initiator', 'virtual block size', 'peer append/offset behavior',
        'application-start version result', 'conditional later groups',
        'custom CRC table', 'programming executor', 'transport implementation',
        'physical maximum', 'installed support', 'freshness', 'qualification']],
}
GATES = ('framing', 'address_role', 'state', 'capacity', 'routing')


def budget(procedure, chunks):
    if procedure == 'grouped':
        if len(chunks) != 5:
            return 'Unknown'
        return 'accept' if all(0 <= n <= cap for n, cap in
                               zip(chunks, (206, 206, 206, 206, 200))) and sum(chunks) <= 1024 else 'reject'
    if procedure == 'cap205':
        if len(chunks) != 1:
            return 'Unknown'
        return 'accept' if 0 <= chunks[0] <= 205 else 'reject'
    return 'Unknown'


def progress(length, status):
    if status == 'accepted':
        return length
    if status in ('rejected', 'pending'):
        return 0
    return 'Unknown'


def offset(current, valid, setter, byte_counter=0):
    if setter != 'none':
        return setter
    if current == 'absent' and valid == 'valid':
        return '00 00'
    if current == 'absent' and valid not in ('valid', 'invalid'):
        return 'Unknown'
    return current


def crc(data, initial=0xFFFF):
    value = initial
    for byte in data:
        value ^= byte << 8
        for _ in range(8):
            value = ((value << 1) ^ (0x1021 if value & 0x8000 else 0)) & 0xFFFF
    return value


def route(variant, selector, nn, gates):
    if variant not in ('filtered', 'unfiltered'):
        return 'Unknown'
    if any(gates.get(key) is False for key in GATES):
        return 'reject'
    if variant == 'filtered' and 0x06 <= selector <= 0x0E:
        return 'reject'
    if any(gates.get(key) is not True for key in GATES):
        return 'Unknown'
    if selector == 0x09:
        return 'accept' if 3 <= nn <= 16 else 'reject'
    shapes = {6: 1, 7: 1, 8: 9, 10: 1, 11: 1, 12: 1, 13: 2, 14: 2}
    if selector not in shapes:
        return 'Unknown'
    return 'accept' if nn == shapes[selector] else 'reject'


class LocalTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / 'architecture/fixtures/ai26_b51b_local_transfer.json').read_text())
        cls.page = (ROOT / 'architecture/b51b_local_transfer.md').read_text()

    def test_publication_tables_and_fixture(self):
        self.assertEqual(self.fixture, {'tables': TABLES, 'gates': list(GATES),
                                        'variants': ['filtered', 'unfiltered']})
        sections = {}
        active = None
        for line in self.page.splitlines():
            if line.startswith('### '):
                active = line[4:]
                sections[active] = []
            elif line.startswith('|') and active:
                cells = [x.strip() for x in line.strip('|').split('|')]
                if cells[0] != 'Field' and not cells[0].startswith('---'):
                    sections[active].append(cells)
        self.assertEqual(sections, TABLES)
        for declaration in (
            'Only absence plus a valid default materializes\n00 00; a later setter supersedes it.',
            'The default CRC candidate uses polynomial 1021, initialization FFFF, MSB-first,\nno reflection and no final XOR.',
            'Numeric OP0B\nfields remain LE16 with no added swap (Hypothesis); B1 29 is the LE16 encoding\nof 29B1, independently Proven as a representation.',
            'Forwarding has two distinct Hypothesis alternatives: `filtered` rejects every\nselector 06..0E; `unfiltered` lacks that selector predicate.',
            'Both retain\n`framing`, `address_role`, `state`, `capacity` and `routing` gates.',
            'For OP09, NN=3+k and\nenvelope=8+k, with structural k=0..13.',
            'The 200/205/206 transfer caps are separate\nfrom this structural route bound.',
            'The grouped procedure has five chunks, not retries.',
            'Progress is credited only after acceptance and by actual length.',
            'A byte counter\nnever supplies a buffer offset.',
        ):
            self.assertIn(declaration, self.page)

    def test_budgets_order_and_actual_progress(self):
        for procedure, chunks, limit, expected, grade in self.fixture['tables']['budgets']:
            values = list(map(int, chunks.split(',')))
            self.assertEqual(budget(procedure, values), expected)
        self.assertEqual(sum([206, 206, 206, 206, 200]), 1024)
        self.assertEqual(sum([206, 206, 206, 206, 201]), 1025)
        self.assertEqual(budget('grouped', [200, 206, 206, 206, 206]), 'reject')
        self.assertEqual(budget('grouped', [206] * 4), 'Unknown')
        self.assertEqual(budget('later-group', [17]), 'Unknown')
        for length, status, expected, grade in self.fixture['tables']['progress']:
            result = progress(int(length), status)
            self.assertEqual(str(result), expected)
        accepted_total = 0
        for n in [206, 206, 206, 206, 200]:
            accepted_total += progress(n, 'accepted')
        self.assertEqual(accepted_total, 1024)  # five chunks contribute, not five retries
        self.assertEqual(accepted_total + progress(200, 'rejected'), 1024)
        self.assertEqual(accepted_total + progress(17, 'accepted'), 1041)

    def test_offset_is_independent_of_counter(self):
        for current, valid, setter, expected, grade in self.fixture['tables']['offset']:
            for byte_counter in (0, 17, 1024):
                with self.subTest(counter=byte_counter, current=current, setter=setter):
                    self.assertEqual(offset(current, valid, setter, byte_counter), expected)
        self.assertEqual(offset('78 56', 'invalid', '34 12'), '34 12')
        self.assertEqual(offset('absent', 'unprovided', 'none'), 'Unknown')

    def test_crc_spans_initialization_and_le16(self):
        for raw, init, expected, le16, grade in self.fixture['tables']['crc']:
            data = b'' if raw == 'empty' else bytes.fromhex(raw)
            result = crc(data, int(init, 16))
            self.assertEqual(result, int(expected, 16))
            self.assertEqual(result, binascii.crc_hqx(data, int(init, 16)))
            self.assertEqual(result.to_bytes(2, 'little').hex(' ').upper(), le16)
        self.assertNotEqual(crc(b'1234'), crc(b'123456789'))
        self.assertNotEqual(crc(b'123456789', 0), crc(b'123456789'))
        self.assertNotEqual(crc(b'1234') ^ crc(b'56789'), crc(b'123456789'))

    def test_route_shapes_and_every_gate_independently(self):
        good = dict.fromkeys(GATES, True)
        for selector, nn, grade in self.fixture['tables']['shapes']:
            op, count = int(selector, 16), int(nn)
            self.assertEqual(route('unfiltered', op, count, good), 'accept')
            for wrong in (count - 1, count + 1):
                self.assertEqual(route('unfiltered', op, wrong, good), 'reject')
        for k, nn, envelope, expected, grade in self.fixture['tables']['route_data']:
            self.assertEqual(int(nn), 3 + int(k))
            self.assertEqual(int(envelope), 8 + int(k))
            self.assertEqual(route('unfiltered', 9, int(nn), good), expected)
        self.assertEqual(route('unfiltered', 9, 2, good), 'reject')
        for op in range(6, 15):
            nn = 3 if op == 9 else dict((int(s, 16), int(n)) for s, n, _ in TABLES['shapes'])[op]
            self.assertEqual(route('filtered', op, nn, good), 'reject')
            self.assertEqual(route('unfiltered', op, nn, good), 'accept')
            for gate in GATES:
                for value, expected in ((False, 'reject'), (None, 'Unknown')):
                    with self.subTest(selector=op, gate=gate, value=value):
                        altered = dict(good, **{gate: value})
                        self.assertEqual(route('unfiltered', op, nn, altered), expected)
        self.assertEqual(route('unprovided', 9, 3, good), 'Unknown')
        for op in (5, 15):
            self.assertEqual(route('unfiltered', op, 1, good), 'Unknown')

    def test_sequence_and_unprovided_transitions(self):
        sequence = [row[0] for row in self.fixture['tables']['sequence']]
        self.assertEqual(sequence, ['08', '09', '0A', '0B', '0C', '0E'])
        self.assertEqual(len(set(sequence)), 6)
        # Only the declared predicates above are evaluated; no executor transitions.
        for name, grade in self.fixture['tables']['unknowns']:
            self.assertEqual(grade, 'Unknown')
            self.assertNotIn(name, ('accepted', 'reject'))


if __name__ == '__main__':
    unittest.main()
