"""Offline executable-page checks; no companion implementation is imported."""

import copy
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "architecture/am12_b509_boiler_codec_dictionary.md"
FIXTURE = ROOT / "architecture/fixtures/am12_b509_boiler_codec_dictionary.json"
# Independent ticket oracle, deliberately not read from the reference or fixture.
EXPECTED = (
    ("1800", "flow_temperature", "DATA2c"),
    ("4400", "central_heating_pump_active", "on/off"),
    ("0200", "water_pressure", "DATA2b"),
    ("0500", "flame_active", "UCH (0x0F=on, 0xF0=off)"),
    ("BB00", "gas_valve_active", "UCH (0x0F=on, 0xF0=off)"),
    ("8300", "fan_speed", "UIN"),
    ("2E00", "modulation_setpoint", "SIN / 10"),
    ("AB00", "boiler_state_code", "UCH"),
    ("5400", "diverter_valve_position", "UCH"),
    ("5800", "dhw_demand_active", "on/off"),
    ("5500", "dhw_water_flow_rate", "UIN / 100"),
    ("0E04", "maximum_heating_flow_temperature_setpoint", "DATA2c"),
    ("A500", "maximum_heating_flow_temperature_setpoint", "DATA2c"),
    ("0F04", "maximum_dhw_flow_temperature_setpoint", "DATA2c"),
    ("0704", "heating_partial_load_power", "UCH"),
    ("0804", "dhw_partial_load_power", "UCH"),
    ("9E00", "storage_loading_pump_level", "percent0"),
    ("3900", "flow_temperature_setpoint", "DATA2c"),
    ("EA03", "dhw_temperature_setpoint", "DATA2c"),
    ("7B00", "circulation_pump_active", "on/off"),
    ("3F00", "external_pump_active", "on/off"),
    ("F203", "heating_switch_active", "on/off"),
    ("2400", "fan_speed_setpoint", "UIN"),
    ("A400", "flame_ionization_current", "SIN / 10"),
    ("FB00", "primary_circuit_flow_rate", "UIN / 100"),
)
CONFLICTS = {
    "2E00": ["setpoint versus achieved modulation unresolved"],
    "5400": ["position enum versus percent unresolved"],
    "0704": ["unit Unknown"], "0804": ["unit Unknown"],
    "A400": ["current versus voltage unresolved"],
    "FB00": ["litres/minute versus litres/hour unresolved"],
    "0E04": ["separate selector; family applicability Unknown"],
    "A500": ["separate selector; family applicability Unknown"],
}
NATIVE = dict.fromkeys(("support", "presence", "freshness", "execution",
                        "effects", "persistence", "delivery"), "Unknown")
KEY_TABLE = [
    ("family", "nonempty string", "boiler"),
    ("variant", "nonempty string", "direct_symbolic_candidate"),
    ("primary", "integer byte", "181"),
    ("secondary", "integer byte", "9"),
    ("operation", "integer byte", "13"),
    ("direction", "nonempty string", "read"),
    ("selector", "four uppercase hex digits", "ordered pair below"),
]
# Each field is varied independently, with an otherwise identical valid control.
KEY_VARIATIONS = {
    "family": "heat_pump", "variant": "other_candidate", "primary": 180,
    "secondary": 8, "operation": 14, "direction": "positive", "selector": "0018",
}


def key(selector="1800"):
    return {"family": "boiler", "variant": "direct_symbolic_candidate",
            "primary": 181, "secondary": 9, "operation": 13,
            "direction": "read", "selector": selector}


def expected_rows():
    return [{"key": key(s), "quantity": q, "codec": {"label": c},
             "grade": "Hypothesis", "conflicts": CONFLICTS.get(s, []).copy(),
             "native": NATIVE.copy()} for s, q, c in EXPECTED]


def expected_cases():
    cases = []

    def add(name, selection, raw, selector=None, **extra):
        cases.append(dict(name=name, key=selection, raw=raw,
                          expected_selector=selector, **extra))

    add("valid", key(), {"value": [0, 16]}, "1800")
    add("equal-name-first", key("0E04"), {}, "0E04")
    add("equal-name-second", key("A500"), {}, "A500")
    for field, value in (
            ("family", "heat_pump"), ("family", "heat_pump_interface_unit"),
            ("variant", "other_candidate"), ("primary", 180), ("secondary", 8),
            ("operation", 14), ("operation", 41), ("direction", "request"),
            ("direction", "positive"), ("selector", "0018"), ("selector", "FFFF")):
        changed = key()
        changed[field] = value
        add(f"{field}-{value}", changed, {"value": [0], "extra": [255]})
    for field in ("family", "variant", "primary", "secondary", "operation",
                  "direction", "selector"):
        changed = key()
        del changed[field]
        add(f"absent-{field}", changed, {"value": [], "status": [0]})
    for field in ("primary", "secondary", "operation"):
        changed = key()
        changed[field] = 0
        add(f"zero-{field}", changed, {"value": [0]})
    add("absent-raw-field", key(), {}, "1800")
    add("zero-raw-field", key(), {"value": [0]}, "1800")
    add("partial-raw", key("2E00"),
        {"value": [], "status": [0], "unknown": [18, 52]}, "2E00",
        last_known_good={"other": [15]})
    add("extra-raw", key("5400"), {"value": [1, 2, 3, 4, 5], "extra": [0]}, "5400")
    return cases


def reference(page):
    blocks = re.findall(r"```python\n(.*?)\n```", page, re.S)
    if len(blocks) != 1:
        raise AssertionError("exactly one executable reference required")
    namespace = {}
    exec(compile(blocks[0], "am12-local-reference", "exec"), namespace)
    return namespace


def table(page, header):
    tail = page.split(header + "\n", 1)[1].split("\n\n", 1)[0]
    return [tuple(cell.strip() for cell in line.strip("|").split("|"))
            for line in tail.splitlines()[1:]]


class BoilerCodecDictionary(unittest.TestCase):
    def setUp(self):
        self.page = PAGE.read_text(encoding="utf-8")
        self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.api = reference(self.page)

    def check_bundle(self, page, data):
        self.assertEqual(set(data), {"kind", "contract_grade", "rows", "cases"})
        self.assertEqual(data["kind"], "synthetic_metadata_contract")
        self.assertEqual(data["contract_grade"], "Proven")
        self.assertEqual(data["rows"], expected_rows())
        self.assertEqual(data["cases"], expected_cases())
        self.assertEqual(reference(page)["entries"](), expected_rows())
        self.assertEqual(table(page, "| Key member | Kind | Selected value |"), KEY_TABLE)
        self.assertEqual(table(page, "| Selector | Quantity | Codec declaration | Conflict retained |"),
                         [(s, q, c, "; ".join(CONFLICTS.get(s, [])) or "none stated")
                          for s, q, c in EXPECTED])
        self.assertEqual(table(page, "| Case | Expected selector (none means no row) |"),
                         [(c["name"], c["expected_selector"] or "none")
                          for c in expected_cases()])
        for phrase in (
                "No codec label selects an executable converter.",
                "its second byte is not a page", "No integer-address endian choice",
                "No missing\nheat-pump interface-unit row is admitted.",
                "Width, endian, unit, mapping,\nsentinel, scale, converter and numeric value fields are absent.",
                "registry. Its implementation and readiness are unverified here.",
                "eBUS MCP compatibility and GraphQL parity are\nunchanged",
                "Nothing is stable before Helianthus 1.0"):
            self.assertIn(phrase, page)

    def test_page_fixture_and_exact_set(self):
        self.check_bundle(self.page, self.data)
        self.assertEqual(len(self.api["entries"]()), 25)
        self.assertEqual(len({tuple(row["key"].values()) for row in self.api["entries"]()}), 25)
        for expected in expected_rows():
            self.assertEqual(self.api["lookup"](expected["key"]), expected)

    def test_all_package_cases_and_raw_results(self):
        by_selector = {row["key"]["selector"]: row for row in expected_rows()}
        for case in self.data["cases"]:
            with self.subTest(case=case["name"]):
                before = copy.deepcopy(case)
                arguments = {k: case[k] for k in ("key", "raw", "last_known_good") if k in case}
                result = self.api["example_lookup"](**arguments)
                expected = {"row": by_selector.get(case["expected_selector"]),
                            "raw": case["raw"], "qualification": "Unknown"}
                if "last_known_good" in case:
                    expected["last_known_good"] = case["last_known_good"]
                self.assertEqual(result, expected)
                self.assertEqual(case, before)
                self.assertEqual(json.loads(json.dumps(result)), expected)

    def test_key_axes_misses_and_valid_pair_controls(self):
        for field, alternate in KEY_VARIATIONS.items():
            with self.subTest(field=field):
                api = reference(self.page)
                base = expected_rows()[0]
                changed = copy.deepcopy(base)
                changed["key"][field] = alternate
                changed["quantity"] = "distinct_quantity"
                self.assertIsNone(api["lookup"](changed["key"]))
                # The seam's second valid row catches implementations that ignore
                # this axis for duplicate detection or choose the first near match.
                api["_EMBEDDED"] = api["validate_rows"]([base, changed])
                self.assertEqual(api["lookup"](base["key"]), base)
                self.assertEqual(api["lookup"](changed["key"]), changed)
                self.assertEqual(len(api["entries"]()), 2)
                absent = key()
                del absent[field]
                self.assertIsNone(api["lookup"](absent))
        for field in ("primary", "secondary", "operation"):
            with self.subTest(zero=field):
                api = reference(self.page)
                row = expected_rows()[0]
                row["key"][field] = 0
                api["_EMBEDDED"] = api["validate_rows"]([row])
                self.assertEqual(api["lookup"](row["key"]), row)
                absent = row["key"].copy()
                del absent[field]
                self.assertIsNone(api["lookup"](absent))

    def test_ordered_selector_octets_independent_integer_arithmetic(self):
        # These are address octets, never a numeric register address or codec.
        for selector, octets in (("1800", (24, 0)), ("0E04", (14, 4)),
                                 ("A500", (165, 0)), ("F203", (242, 3))):
            with self.subTest(selector=selector):
                self.assertEqual(tuple(bytes.fromhex(selector)), octets)
                self.assertEqual(int(selector[:2], 16), octets[0])
                self.assertEqual(int(selector[2:], 16), octets[1])
                reverse = f"{octets[1]:02X}{octets[0]:02X}"
                self.assertIsNotNone(self.api["lookup"](key(selector)))
                self.assertIsNone(self.api["lookup"](key(reverse)))

    def test_equal_names_stay_distinct(self):
        first = self.api["lookup"](key("0E04"))
        second = self.api["lookup"](key("A500"))
        self.assertEqual(first["quantity"], second["quantity"])
        self.assertNotEqual(first["key"], second["key"])
        first["codec"]["label"] = "changed"
        self.assertEqual(second["codec"]["label"], "DATA2c")
        self.assertIsNone(self.api["lookup"](dict(key("0E04"), selector="040E")))

    def test_malformed_and_partial_keys_fail_closed(self):
        for bad in (None, [], 0, "1800", False):
            with self.subTest(key=bad), self.assertRaises(ValueError):
                self.api["lookup"](bad)
        for field in key():
            invalid = [None, False, [], {}, 1.5]
            invalid += [-1, 256, "13"] if field in ("primary", "secondary", "operation") else [0, ""]
            if field == "selector":
                invalid += ["180", "18000", "0e04", "GG00", "18 00", "0x1800"]
            for value in invalid:
                with self.subTest(field=field, bad=value):
                    selection = dict(key(), **{field: value})
                    with self.assertRaises(ValueError):
                        self.api["lookup"](selection)
                    # A missing sibling must not hide the malformed member.
                    sibling = "primary" if field != "primary" else "secondary"
                    del selection[sibling]
                    with self.assertRaises(ValueError):
                        self.api["lookup"](selection)
        with self.assertRaises(ValueError):
            self.api["lookup"](dict(key(), extra=0))
        self.assertIsNone(self.api["lookup"]({}))
        self.assertEqual(self.api["lookup"](key()), expected_rows()[0])

    def test_row_validation_all_field_axes_and_duplicate_keys(self):
        validate = self.api["validate_rows"]
        base = expected_rows()[0]
        for invalid in (None, {}, "rows", 0):
            with self.subTest(rows=invalid), self.assertRaises(ValueError):
                validate(invalid)
        self.assertEqual(validate([]), [])
        for field in base:
            for operation in ("absent", "null", "zero"):
                with self.subTest(field=field, mutation=operation):
                    changed = copy.deepcopy(base)
                    if operation == "absent":
                        del changed[field]
                    else:
                        changed[field] = None if operation == "null" else 0
                    with self.assertRaises(ValueError):
                        validate([base, changed])
        for field in key():
            changed = copy.deepcopy(base)
            del changed["key"][field]
            with self.subTest(missing_key=field), self.assertRaises(ValueError):
                validate([changed])
        for patch in ({"extra": 0}, {"unit": "invented"}, {"converter": "numeric"},
                      {"grade": "Proven"}, {"quantity": "Not canonical"},
                      {"codec": {"label": "DATA2c", "scale": 16}},
                      {"codec": {"label": ""}}, {"codec": {"label": 0}},
                      {"conflicts": [0]}, {"conflicts": [""]}):
            changed = dict(copy.deepcopy(base), **patch)
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                validate([changed])
        for field in NATIVE:
            for mutation in ("absent", "zero", "Proven"):
                changed = copy.deepcopy(base)
                if mutation == "absent":
                    del changed["native"][field]
                else:
                    changed["native"][field] = 0 if mutation == "zero" else mutation
                with self.subTest(native=field, mutation=mutation), self.assertRaises(ValueError):
                    validate([changed])
        with self.assertRaises(ValueError):
            validate([base, copy.deepcopy(base)])
        changed = copy.deepcopy(base)
        changed["quantity"] = "different_name"
        with self.assertRaises(ValueError):
            validate([base, changed])
        # Entire-array validation: no prefix result may replace prior good state.
        previous = self.api["entries"]()
        with self.assertRaises(ValueError):
            validate([base, {"key": key()}])
        self.assertEqual(self.api["entries"](), previous)

    def test_unknown_codec_is_metadata_only(self):
        base = expected_rows()[0]
        base["codec"]["label"] = "opaque_unknown / alternatives"
        api = reference(self.page)
        api["_EMBEDDED"] = api["validate_rows"]([base])
        result = api["example_lookup"](key(), {"value": [0, 255]})
        self.assertEqual(result, {"row": base, "raw": {"value": [0, 255]},
                                  "qualification": "Unknown"})
        self.assertEqual(result["row"]["grade"], "Hypothesis")
        self.assertNotIn("unit", result["row"])
        self.assertNotIn("value", result["row"])

    def test_deep_independence_and_prior_state(self):
        selection = key("2E00")
        raw = {"value": [], "status": [0], "extra": {"nested": [255]}}
        prior = {"other": {"raw": [15]}}
        result = self.api["example_lookup"](selection, raw, prior)
        untouched = copy.deepcopy(result)
        selection["selector"] = "FFFF"
        raw["extra"]["nested"].append(0)
        prior["other"]["raw"].clear()
        self.assertEqual(result, untouched)
        for container in (result["row"], self.api["entries"]()[6]):
            container["key"]["selector"] = "FFFF"
            container["codec"]["label"] = "changed"
            container["conflicts"].clear()
            container["native"]["support"] = "Proven"
        self.assertEqual(self.api["lookup"](key("2E00")), expected_rows()[6])
        result["raw"]["extra"]["nested"].clear()
        result["last_known_good"]["other"]["raw"].append(0)
        self.assertEqual(raw["extra"]["nested"], [255, 0])
        self.assertEqual(prior["other"]["raw"], [])
        source = expected_rows()
        validated = self.api["validate_rows"](source)
        source[0]["codec"]["label"] = "changed"
        validated[6]["conflicts"].clear()
        self.assertEqual(validated[0]["codec"]["label"], "DATA2c")
        self.assertEqual(source[6]["conflicts"], CONFLICTS["2E00"])
        failed_key = dict(key(), operation=False)
        with self.assertRaises(ValueError):
            self.api["example_lookup"](failed_key, raw, prior)
        self.assertEqual(self.api["lookup"](key()), expected_rows()[0])
        self.assertEqual(untouched["row"], expected_rows()[6])

    def test_absent_zero_partial_extra_and_opaque_raw(self):
        for raw in ({}, {"value": []}, {"value": [0]},
                    {"value": [0, 1, 2], "status": [0]},
                    {"value": "malformed-looking", "extra": {"unknown": None}}):
            result = self.api["example_lookup"](key(), raw)
            self.assertEqual(result["raw"], raw)
            self.assertEqual(result["row"], expected_rows()[0])
            self.assertNotIn("last_known_good", result)
        with_null = self.api["example_lookup"](key(), {}, None)
        self.assertIn("last_known_good", with_null)
        self.assertIsNone(with_null["last_known_good"])
        no_row = self.api["example_lookup"](dict(key(), family="heat_pump_interface_unit"),
                                              {"value": [], "status": [0]}, {"good": [1]})
        self.assertEqual(no_row, {"row": None, "raw": {"value": [], "status": [0]},
                                  "qualification": "Unknown", "last_known_good": {"good": [1]}})

    def test_page_and_fixture_mutation_sensitivity(self):
        for field, _, _ in KEY_TABLE:
            changed = self.page.replace(f"| {field} |", f"| ignored_{field} |", 1)
            with self.subTest(page_axis=field), self.assertRaises(AssertionError):
                self.check_bundle(changed, self.data)
        for selector in CONFLICTS:
            changed = copy.deepcopy(self.data)
            row = next(row for row in changed["rows"] if row["key"]["selector"] == selector)
            row["conflicts"] = []
            with self.subTest(conflict=selector), self.assertRaises(AssertionError):
                self.check_bundle(self.page, changed)
        mutations = [
            lambda rows: rows.pop(12),  # collapsing equal quantity names
            lambda rows: rows[0]["key"].update(family="heat_pump_interface_unit"),
            lambda rows: rows[0]["key"].update(selector="0018"),
            lambda rows: rows[0].update(unit="invented"),
            lambda rows: rows[0]["codec"].update(converter="numeric"),
        ]
        for mutate in mutations:
            changed = copy.deepcopy(self.data)
            mutate(changed["rows"])
            with self.subTest(mutation=mutate), self.assertRaises(AssertionError):
                self.check_bundle(self.page, changed)

    def test_relative_links_resolve(self):
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", self.page)
        self.assertEqual(len(links), 4)
        for target in links:
            self.assertNotIn("://", target)
            self.assertTrue((PAGE.parent / target).is_file(), target)


if __name__ == "__main__":
    unittest.main()
