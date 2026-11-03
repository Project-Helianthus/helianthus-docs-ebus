"""Finite page/example checks and a local oracle; no companion or wire execution."""

import base64
import copy
import csv
import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "architecture/al04_b513_symbolic_dictionary.md"
FIXTURE = ROOT / "architecture/fixtures/al04_b513_symbolic_dictionary.json"
CATALOG = ROOT / "protocols/vaillant/fixtures/hem-b513-symbolic-addresses.csv"
AXES = ["family", "opcode", "dictionary_namespace", "raw_address",
        "bus_family", "variant", "direction"]
CONTRACT = {
    "api": ["Ab38Entries", "Lookup"],
    "key_axes": AXES,
    "family": "B513", "opcode": "04",
    "dictionary_namespace": "b513-generic-candidate",
    "variant": "unqualified", "direction": "unqualified",
    "unique_addresses": 1263,
    "candidate_memberships": {"eBUS": 1263, "PeBUS": 1263},
    "candidate_grade": "Hypothesis", "representation_grade": "Proven",
    "physical_qualification": "Unknown", "presence": "Unknown",
    "freshness": "Unknown", "execution": "Unknown",
    "missing_address": "error:missing-address",
    "invalid_address": "error:invalid-address",
    "incomplete_key": "error:incomplete-key", "unknown_key": "absent:Unknown",
    "zero_address": "literal-address", "ffff": "label-only", "gap_fill": False,
    "value_codec": None, "executable_capability": False,
    "returned_memory": "independent-deep-copies",
}
KEY = dict(zip(AXES, ["B513", "04", "b513-generic-candidate", 0,
                      "eBUS", "unqualified", "unqualified"]))
EXAMPLES = (
    (0x0000, "AccessoryRelaisOne"), (0x0001, "AccessoryRelaisTwo"),
    (0x00EE, "DCF is Valid"), (0x02D0, "IsInSavingsFunction"),
    (0x02D3, "LanguageVariant"), (0x0371, "PowerOnCounter"),
    (0x0372, "PowerOnCounter"), (0xFFFF, "All Addresses"),
)
GAPS = (0x02D1, 0x02D2, 0x0364, 0x0365, 0x0368,
        0x0391, 0x0392, 0x0393, 0x0394, 0x0395, 0x0396, 0x0397, 0x0398)
KEY_ROWS = [
    ("family", "B513", "B512 is absent"),
    ("opcode", "04", "05 is absent"),
    ("dictionary_namespace", "b513-generic-candidate", "synthetic-other-dictionary is absent"),
    ("raw_address", "explicit numeric u16", "0000 and 0001 have different labels; 0100 differs from 0000"),
    ("bus_family", "eBUS or PeBUS, matched separately", "synthetic-other-bus is absent"),
    ("variant", "literal unqualified", "synthetic-family-a is absent"),
    ("direction", "literal unqualified", "request and response are each absent"),
]


def example(address, label):
    return dict(raw_address=address, address_bytes_le=[address & 255, address >> 8],
                label=label, bus_membership={"eBUS": "Hypothesis", "PeBUS": "Hypothesis"},
                value_codec=None, executable_capability=False)


def expected_fixture():
    return dict(synthetic=True, contract=copy.deepcopy(CONTRACT),
                examples=[example(address, label) for address, label in EXAMPLES])


def validate_documents(page, data):
    """Assert independently specified declarations, including all example cells."""
    blocks = re.findall(r"```json\n(.*?)\n```", page, re.S)
    if len(blocks) != 1 or json.loads(blocks[0]) != CONTRACT:
        raise AssertionError("page contract differs")
    if data != expected_fixture():
        raise AssertionError("example declarations differ")
    rows = [tuple(cell.strip() for cell in line.strip('|').split('|'))
            for line in page.splitlines()
            if re.match(r"^\| [0-9A-F]{4} \|", line)]
    expected_rows = [(f"{a:04X}", label, "Hypothesis", "Hypothesis")
                     for a, label in EXAMPLES]
    if rows != expected_rows:
        raise AssertionError("page example rows differ")
    key_rows = [tuple(cell.strip() for cell in line.strip('|').split('|'))
                for line in page.splitlines()
                if line.startswith(tuple(f"| {axis} |" for axis in AXES))]
    if key_rows != KEY_ROWS:
        raise AssertionError("page key rows differ")
    for phrase in (
        "The catalog prerequisite must merge before this\npage.",
        "Nothing is stable before Helianthus 1.0.",
        "Literal native symbols are opaque dictionary labels",
        "`Ab38Entries()` returns the finite list of 1263 address entries",
        "`Lookup(key)` returns `(entry, found, error)`",
        "List order\nis ascending numeric address; labels are not unique keys.",
        "The literal `unqualified` is metadata, never all-directions permission",
        "Admission remains fail-closed.",
        "it does not mean unsupported.",
        "Preserve the\nraw query and every independently useful key field on all outcomes.",
        "Missing, null or empty address returns `missing-address`, never numeric zero.",
        "address validation precedes other key checks.",
        "Every call owns its returned list, entries, address-byte buffers and nested\nmembership maps.",
        "FFFF carries the All Addresses label only in this dictionary. It is neither an\niterable interval nor an admitted all-address operation.",
        "Actual gaps 02D1, 02D2, 0364, 0365,\n0368 and 0391 through 0398 remain unknown raw addresses",
        "no code result, native effect or full parity",
        "MCP compatibility and GraphQL parity remain requirements",
    ):
        if phrase not in page:
            raise AssertionError(f"missing scope assertion: {phrase}")


def catalog_entries(rows):
    """Local representation oracle over the public catalog, never a runtime import."""
    return [dict(example(int(row["address"], 16), row["vaillant_name"]),
                 family="B513", opcode="04", dictionary_namespace="b513-generic-candidate",
                 variant="unqualified", direction="unqualified", grade="Hypothesis")
            for row in rows]


def entries(catalog):
    return copy.deepcopy(catalog)


def lookup(catalog, key):
    """Synthetic specification oracle, with query preservation outside the API tuple."""
    result = dict(key=copy.deepcopy(key), entry=None, found=False, error=None,
                  interpretation="Unknown", executable_capability=False)
    address = key.get("raw_address")
    if address is None or address == "":
        result["error"] = "missing-address"
        return result
    if type(address) is not int or not 0 <= address <= 65535:
        result["error"] = "invalid-address"
        return result
    if any(key.get(axis) is None or key.get(axis) == "" for axis in AXES):
        result["error"] = "incomplete-key"
        return result
    for entry in catalog:
        if (all(key[axis] == entry[axis] for axis in AXES
                if axis not in ("raw_address", "bus_family"))
                and address == entry["raw_address"]
                and key["bus_family"] in entry["bus_membership"]):
            result.update(entry=copy.deepcopy(entry), found=True, interpretation="Hypothesis")
            break
    return result


class SymbolicDictionaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text(encoding="utf-8")
        cls.data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        with CATALOG.open(encoding="utf-8", newline="") as stream:
            cls.rows = list(csv.DictReader(stream))

    def setUp(self):
        self.catalog = catalog_entries(self.rows)

    def test_page_and_small_fixture_contract(self):
        validate_documents(self.page, self.data)
        self.assertEqual(len(self.data["examples"]), 8)
        for target in re.findall(r"\]\(([^)]+)\)", self.page):
            self.assertTrue((PAGE.parent / target.split("#")[0]).is_file(), target)

    def test_complete_public_table_cardinality_addresses_and_labels(self):
        addresses = [int(row["address"], 16) for row in self.rows]
        self.assertEqual(len(addresses), 1263)
        self.assertEqual(len(set(addresses)), 1263)
        expected_addresses = sorted((set(range(0x04FB)) - set(GAPS)) | {0xFFFF})
        self.assertEqual(addresses, expected_addresses)
        canonical = "".join(f"{int(row['address'], 16):04X}|{row['vaillant_name']}\n"
                            for row in self.rows).encode("utf-8")
        # Computed from the cited public CSV's complete address|native-label table.
        # Base64 encodes digest bytes; no literal hex digest or commit identifier.
        self.assertEqual(base64.b64encode(hashlib.sha256(canonical).digest()).decode(),
                         "9IaRK6+W8DMD5vkpITYyXM5Wa39ybelbAfUbv8VfnjM=")
        labels = {int(row["address"], 16): row["vaillant_name"] for row in self.rows}
        for address, label in EXAMPLES:
            self.assertEqual(labels[address], label)
        for row in self.rows:
            with self.subTest(address=row["address"]):
                self.assertEqual(int(row["address_decimal"]), int(row["address"], 16))
                self.assertEqual(row["bus_profile"], "eBUS|PeBUS")
                self.assertEqual(row["status"], "candidate, unconfirmed on the wire")

    def test_all_entries_and_independent_known_results(self):
        snapshot = entries(self.catalog)
        self.assertEqual(len(snapshot), 1263)
        self.assertEqual([r["raw_address"] for r in snapshot],
                         sorted(r["raw_address"] for r in snapshot))
        for bus in ("eBUS", "PeBUS"):
            self.assertEqual(sum(bus in r["bus_membership"] for r in snapshot), 1263)
            for address, label in EXAMPLES:
                with self.subTest(bus=bus, address=address):
                    key = dict(KEY, raw_address=address, bus_family=bus)
                    result = lookup(self.catalog, key)
                    self.assertTrue(result["found"])
                    self.assertIsNone(result["error"])
                    self.assertEqual(result["key"], key)
                    self.assertEqual(result["entry"], dict(example(address, label),
                        family="B513", opcode="04", dictionary_namespace="b513-generic-candidate",
                        variant="unqualified", direction="unqualified", grade="Hypothesis"))
                    self.assertEqual(result["interpretation"], "Hypothesis")
                    self.assertFalse(result["executable_capability"])

    def test_every_key_axis_independently(self):
        self.assertTrue(lookup(self.catalog, KEY)["found"])
        alternatives = dict(family="B512", opcode="05",
                            dictionary_namespace="synthetic-other-dictionary",
                            raw_address=1, bus_family="synthetic-other-bus",
                            variant="synthetic-family-a", direction="request")
        for axis, alternate in alternatives.items():
            with self.subTest(axis=axis):
                key = dict(KEY, **{axis: alternate})
                self.assertEqual([a for a in AXES if key[a] != KEY[a]], [axis])
                result = lookup(self.catalog, key)
                self.assertEqual(result["key"], key)
                self.assertIsNone(result["error"])
                self.assertEqual(result["found"], axis == "raw_address")
                self.assertEqual(result["entry"]["label"] if result["found"] else None,
                                 "AccessoryRelaisTwo" if axis == "raw_address" else None)
        for bus in ("eBUS", "PeBUS"):
            self.assertEqual(lookup(self.catalog, dict(KEY, bus_family=bus))["key"]["bus_family"], bus)
            for direction in ("request", "response"):
                self.assertFalse(lookup(self.catalog, dict(KEY, bus_family=bus,
                                                        direction=direction))["found"])

    def test_each_address_byte_independently(self):
        # Low-byte omission/shift and high-byte truncation cannot alias these keys.
        for address, raw, label in ((0, [0, 0], "AccessoryRelaisOne"),
                                    (1, [1, 0], "AccessoryRelaisTwo"),
                                    (256, [0, 1], "DesiredDegreeBoiler_2")):
            with self.subTest(address=address):
                result = lookup(self.catalog, dict(KEY, raw_address=address))
                self.assertEqual(result["entry"]["address_bytes_le"], raw)
                self.assertEqual(result["entry"]["label"], label)

    def test_real_gaps_ffff_and_duplicate_labels(self):
        actual = {int(row["address"], 16) for row in self.rows}
        for address in GAPS:
            self.assertNotIn(address, actual)
            for bus in ("eBUS", "PeBUS"):
                key = dict(KEY, raw_address=address, bus_family=bus)
                result = lookup(self.catalog, key)
                self.assertEqual(result, dict(key=key, entry=None, found=False, error=None,
                                             interpretation="Unknown", executable_capability=False))
        for address in (0xFFFF, 0x0371, 0x0372):
            result = lookup(self.catalog, dict(KEY, raw_address=address))
            self.assertEqual(result["entry"]["raw_address"], address)
            self.assertIsNone(result["entry"]["value_codec"])
            self.assertFalse(result["entry"]["executable_capability"])
        # FFFF in another dictionary is absent, not an all-address operation.
        self.assertFalse(lookup(self.catalog, dict(KEY, raw_address=65535,
                         dictionary_namespace="synthetic-other-dictionary"))["found"])

    def test_absent_null_empty_zero_and_malformed_addresses(self):
        missing = dict(KEY)
        del missing["raw_address"]
        cases = [(missing, "missing-address")]
        cases += [(dict(KEY, raw_address=value), error) for values, error in (
            ((None, ""), "missing-address"),
            ((False, True, "0000", 0.0, -1, 65536, [], {}), "invalid-address"))
                  for value in values]
        for key, error in cases:
            with self.subTest(key=key):
                result = lookup(self.catalog, key)
                self.assertEqual(result, dict(key=key, entry=None, found=False, error=error,
                                             interpretation="Unknown", executable_capability=False))
        self.assertEqual(lookup(self.catalog, KEY)["entry"]["label"], "AccessoryRelaisOne")

    def test_each_other_axis_missing_null_and_empty(self):
        for axis in AXES:
            if axis == "raw_address":
                continue
            for kind in ("missing", "null", "empty"):
                key = dict(KEY)
                if kind == "missing":
                    del key[axis]
                else:
                    key[axis] = None if kind == "null" else ""
                with self.subTest(axis=axis, kind=kind):
                    result = lookup(self.catalog, key)
                    self.assertEqual(result["key"], key)
                    self.assertEqual(result["error"], "incomplete-key")
                    self.assertFalse(result["found"])
                    self.assertIsNone(result["entry"])

    def test_independent_memory_for_entries_lookup_and_failures(self):
        for field, mutation in (
            ("label", "synthetic-mutated"), ("address_bytes_le", [7, 8]),
            ("bus_membership", {"eBUS": "Unknown"}),
        ):
            with self.subTest(field=field):
                self.catalog = catalog_entries(self.rows)
                original = copy.deepcopy(self.catalog)
                first, second = entries(self.catalog), entries(self.catalog)
                result = lookup(self.catalog, KEY)
                if isinstance(mutation, list):
                    first[0][field][:] = mutation
                    result["entry"][field][:] = mutation
                elif isinstance(mutation, dict):
                    first[0][field].clear()
                    result["entry"][field].clear()
                else:
                    first[0][field] = result["entry"][field] = mutation
                self.assertEqual(self.catalog, original)
                self.assertEqual(second, original)
                self.assertEqual(lookup(self.catalog, KEY)["entry"], original[0])
        self.catalog = catalog_entries(self.rows)
        first = entries(self.catalog)
        first.pop()
        self.assertEqual(len(entries(self.catalog)), 1263)
        for address in (0, 0x02D1, None):
            key = dict(KEY, raw_address=address)
            result = lookup(self.catalog, key)
            original = copy.deepcopy(result["key"])
            key["variant"] = "synthetic-family-a"
            self.assertEqual(result["key"], original)
            result["key"]["family"] = "B512"
            self.assertEqual(key["family"], "B513")

    def test_each_example_address_label_byte_and_membership_mutation_rejected(self):
        validate_documents(self.page, self.data)
        for index in range(len(EXAMPLES)):
            for field in ("raw_address", "label", "address_bytes_le", "bus_membership",
                          "value_codec", "executable_capability"):
                mutations = (0, 1) if field in ("address_bytes_le", "bus_membership") else (None,)
                for part in mutations:
                    changed = copy.deepcopy(self.data)
                    row = changed["examples"][index]
                    if field == "raw_address":
                        row[field] ^= 1
                    elif field == "label":
                        row[field] += "changed"
                    elif field == "address_bytes_le":
                        row[field][part] ^= 1
                    elif field == "bus_membership":
                        del row[field][("eBUS", "PeBUS")[part]]
                    elif field == "value_codec":
                        row[field] = "inferred-temperature"
                    else:
                        row[field] = True
                    with self.subTest(index=index, field=field, part=part):
                        with self.assertRaises(AssertionError):
                            validate_documents(self.page, changed)

    def test_page_rows_and_contract_mutations_rejected(self):
        for address, label in EXAMPLES:
            row = f"| {address:04X} | {label} | Hypothesis | Hypothesis |"
            for changed_row in (row.replace(f"{address:04X}", f"{address ^ 1:04X}", 1),
                                row.replace(label, label + "changed", 1)):
                with self.subTest(address=address, row=changed_row):
                    with self.assertRaises(AssertionError):
                        validate_documents(self.page.replace(row, changed_row), self.data)
        for field, alternate in (("ffff", "admitted-wildcard"), ("gap_fill", True),
                                 ("value_codec", "inferred"),
                                 ("missing_address", "literal-zero"),
                                 ("candidate_grade", "Proven")):
            changed = copy.deepcopy(CONTRACT)
            changed[field] = alternate
            page = re.sub(r"```json\n.*?\n```", lambda _: "```json\n" +
                          json.dumps(changed, indent=2) + "\n```", self.page, flags=re.S)
            with self.subTest(field=field):
                with self.assertRaises(AssertionError):
                    validate_documents(page, self.data)
        changed = copy.deepcopy(self.data)
        changed["examples"].append(example(0x02D1, "invented-gap-label"))
        with self.assertRaises(AssertionError):
            validate_documents(self.page, changed)


if __name__ == "__main__":
    unittest.main()
