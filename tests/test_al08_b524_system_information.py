"""Page/fixture checks and synthetic specification controls, not companion tests."""

import copy
import json
import math
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "architecture/al08-b524-system-information.md"
FIXTURE = ROOT / "architecture/fixtures/al08_b524_system_information.json"
CONTEXT_FIELDS = [
    "family", "software", "hardware", "api_version",
    "api_revision", "identifier",
]
RESULT_FIELDS = [
    "context", "raw", "state", "value", "capacity",
    "capacity_state",
]
EXPECTED_CONTRACT = {
    "request_order": ["00", "IDlo", "IDhi"],
    "reply_length": 4,
    "representation": "little-endian IEEE binary32",
    "context_fields": CONTEXT_FIELDS,
    "result_fields": RESULT_FIELDS,
    "invalid_lengths": [0, 1, 2, 3, 5],
    "non_finite": ["NaN", "positive infinity", "negative infinity"],
    "capacity_rule": "profile-supported integer: 1, 2, 3, 5, 7, 8",
    "cardinality": "supported capacity; never discovered cardinality or slot presence",
    "interpretation_grade": "Hypothesis",
}


def example_result(context, raw):
    """Local arithmetic oracle; does not execute or validate the companion API."""
    result = {
        "context": copy.deepcopy(context), "raw": bytearray(raw),
        "state": "invalid_length", "value": None,
        "capacity": None, "capacity_state": "Unknown",
    }
    if len(raw) != 4:
        return result
    value = struct.unpack("<f", raw)[0]
    if not math.isfinite(value):
        result["state"] = "invalid_non_finite"
        return result
    result.update(state="decoded", value=value)
    if context["identifier"] in (0, 1) and value in (1, 2, 3, 5, 7, 8):
        result.update(capacity=int(value), capacity_state="decoded")
    return result


class InformationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text(encoding="utf-8")
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.context = cls.fixture["context"]

    def test_page_declaration(self):
        blocks = re.findall(r"```json\n(.*?)\n```", self.page, re.S)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(json.loads(blocks[0]), EXPECTED_CONTRACT)
        for phrase in (
            "B524SystemBuildInformation(identifier uint16) []byte",
            "B524SystemDecodeInformation(requestContext, raw) result",
            "Identifier 0x1234 builds `00 34 12`.",
            "accepts exactly four",
            "returns a fresh three-byte\nbuffer `[00, IDlo, IDhi]`",
            "The result owns a copy of `raw` and a snapshot of all six context fields.",
            "`state` is `decoded`, `invalid_length` or `invalid_non_finite`.",
            "`value` is a finite number only for `decoded`, otherwise null.",
            "Invalid\nlengths and NaN or either infinity retain owned raw bytes with explicit invalid\nstate.",
            "profile-supported integer value in {1, 2, 3, 5, 7, 8}",
            "Any other finite\nvalue remains decoded while capacity is Unknown",
            "There is no implicit count label for an unknown identifier;\npreserve 0xFFFF numerically.",
            "API version and API revision\nare distinct fields",
            "Zero is numeric zero,\nnot absence.",
            "Never fabricate a terminal discovery marker.",
            "IDs 0x0000 and 0x0001 describe supported circuit/zone capacities, never\n discovered cardinality or slot presence.",
            "ID 0x000D heat-pump count and separate eligibility\nchecks are independent",
            "**Hypothesis:**", "**Proven:**", "**Unknown:**",
            "this page changes neither surface",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.page)
        for target in re.findall(r"\]\(([^)]+)\)", self.page):
            if not target.startswith("https:"):
                self.assertTrue((PAGE.parent / target.split("#")[0]).is_file())

    def test_small_fixture_and_independent_expected_results(self):
        # Literal expectations are independent of fixture values and the oracle.
        expected = [
            (4660, [0, 52, 18], [0, 0, 128, 63], 1.0, None, "Unknown"),
            (0, [0, 0, 0], [0, 0, 128, 63], 1.0, 1, "decoded"),
            (0, [0, 0, 0], [0, 0, 192, 63], 1.5, None, "Unknown"),
            (0, [0, 0, 0], [0, 0, 128, 191], -1.0, None, "Unknown"),
            (1, [0, 1, 0], [0, 0, 0, 0], 0.0, None, "Unknown"),
            (65535, [0, 255, 255], [0, 0, 128, 63], 1.0, None, "Unknown"),
            (13, [0, 13, 0], [0, 0, 128, 63], 1.0, None, "Unknown"),
        ]
        self.assertEqual(set(self.fixture), {"context", "examples"})
        self.assertEqual(len(self.fixture["examples"]), len(expected))
        for example, (identifier, request, raw, value, capacity, state) in zip(
            self.fixture["examples"], expected
        ):
            with self.subTest(identifier=identifier, raw=raw):
                self.assertEqual(example, dict(
                    identifier=identifier, request=request, raw=raw,
                    value=value, capacity=capacity, capacity_state=state,
                ))
                context = dict(self.context, identifier=identifier)
                result = example_result(context, bytearray(raw))
                self.assertEqual(set(result), set(RESULT_FIELDS))
                self.assertEqual(result["state"], "decoded")
                self.assertEqual(result["value"], value)
                self.assertEqual(result["capacity"], capacity)
                self.assertEqual(result["capacity_state"], state)
                self.assertEqual(result["raw"], bytearray(raw))

    def test_synthetic_build_buffers(self):
        # Specification arithmetic only; companion build ownership is still unverified.
        for identifier, expected in ((0, [0, 0, 0]), (1, [0, 1, 0]),
                                     (4660, [0, 52, 18]), (65535, [0, 255, 255])):
            with self.subTest(identifier=identifier):
                first = bytearray([0, identifier & 255, identifier >> 8])
                second = bytearray([0, identifier & 255, identifier >> 8])
                self.assertEqual(list(first), expected)
                first[0] = 17
                self.assertEqual(list(second), expected)

    def test_context_baseline_has_distinct_version_revision(self):
        self.assertEqual(self.context, dict(zip(CONTEXT_FIELDS, [
            "synthetic-family-a", "synthetic-software-a", "synthetic-hardware-a",
            2, 7, 4660,
        ])))

    def test_every_context_axis_independently_survives_success_and_failure(self):
        alternatives = ["synthetic-family-b", "synthetic-software-b",
                        "synthetic-hardware-b", 3, 8, 65535]
        for field, alternate in zip(CONTEXT_FIELDS, alternatives):
            for raw in (bytearray([0, 0, 128, 63]), bytearray([0])):
                with self.subTest(field=field, length=len(raw)):
                    changed = dict(self.context, **{field: alternate})
                    before = example_result(self.context, raw)
                    after = example_result(changed, raw)
                    self.assertEqual(after["context"], changed)
                    self.assertEqual([
                        key for key in CONTEXT_FIELDS
                        if before["context"][key] != after["context"][key]
                    ], [field])
                    for key in RESULT_FIELDS[1:]:
                        self.assertEqual(before[key], after[key])

    def test_short_and_extra_replies_retain_raw(self):
        for length in (0, 1, 2, 3, 5):
            with self.subTest(length=length):
                raw = bytearray(range(length))
                result = example_result(self.context, raw)
                self.assertEqual(result["state"], "invalid_length")
                self.assertEqual(result["raw"], raw)
                self.assertEqual(result["context"], self.context)
                self.assertIsNone(result["value"])
                self.assertIsNone(result["capacity"])
                self.assertEqual(result["capacity_state"], "Unknown")

    def test_generated_nan_and_both_infinities_retain_raw(self):
        # Generate bits; no platform NaN serialization or native capture input.
        exponent = 255 << 23
        for bits in (exponent | (1 << 22), exponent, (1 << 31) | exponent):
            with self.subTest(bits=bits):
                raw = bytearray(struct.pack("<I", bits))
                result = example_result(self.context, raw)
                self.assertEqual(result["state"], "invalid_non_finite")
                self.assertEqual(result["raw"], raw)
                self.assertEqual(result["context"], self.context)
                self.assertIsNone(result["value"])
                self.assertIsNone(result["capacity"])
                self.assertEqual(result["capacity_state"], "Unknown")

    def test_both_capacity_identifiers_with_independent_numeric_controls(self):
        for identifier in (0, 1):
            for raw, value, capacity in (
                ([0, 0, 128, 63], 1.0, 1),
                ([0, 0, 0, 64], 2.0, 2),
                ([0, 0, 64, 64], 3.0, 3),
                ([0, 0, 160, 64], 5.0, 5),
                ([0, 0, 224, 64], 7.0, 7),
                ([0, 0, 0, 65], 8.0, 8),
                ([0, 0, 192, 63], 1.5, None),
                ([0, 0, 128, 191], -1.0, None),
                ([0, 0, 0, 0], 0.0, None),
                ([0, 0, 128, 64], 4.0, None),
                ([0, 0, 192, 64], 6.0, None),
                ([0, 0, 16, 65], 9.0, None),
            ):
                with self.subTest(identifier=identifier, value=value):
                    result = example_result(
                        dict(self.context, identifier=identifier), bytes(raw)
                    )
                    self.assertEqual(result["state"], "decoded")
                    self.assertEqual(result["raw"], bytearray(raw))
                    self.assertEqual(result["context"],
                                     dict(self.context, identifier=identifier))
                    self.assertEqual(result["value"], value)
                    self.assertEqual(result["capacity"], capacity)
                    self.assertEqual(result["capacity_state"],
                                     "Unknown" if capacity is None else "decoded")

    def test_caller_and_returned_buffers_are_independent(self):
        for raw in (bytearray([0, 0, 128, 63]), bytearray([0]),
                    bytearray(struct.pack("<I", 255 << 23))):
            with self.subTest(length=len(raw)):
                original = bytes(raw)
                first = example_result(self.context, raw)
                second = example_result(self.context, raw)
                raw[0] = 17
                self.assertEqual(bytes(first["raw"]), original)
                first["raw"][0] = 29
                self.assertEqual(raw[0], 17)
                self.assertEqual(bytes(second["raw"]), original)
        for field in CONTEXT_FIELDS:
            context = dict(self.context)
            result = example_result(context, bytes([0, 0, 128, 63]))
            context[field] = "mutated caller"
            self.assertEqual(result["context"], self.context)
            result["context"][field] = "mutated result"
            self.assertEqual(context[field], "mutated caller")


if __name__ == "__main__":
    unittest.main(verbosity=2)
