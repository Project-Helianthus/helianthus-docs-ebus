"""Offline page/example contract checks; no companion import or runtime claim."""

import copy
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "architecture/al12_b509_identity_shapes.md"
FIXTURE = ROOT / "architecture/fixtures/al12_b509_identity_shapes.json"
KEY = {
    "family": "vaillant", "variant": "B509", "primary": 181,
    "secondary": 9, "operation": 83, "direction": "read",
    "field": "hardware_identifier", "alternative": "packed_decimal_candidate",
    "group": None, "instance_scope": "none", "register": None,
}
AXES = [
    ("family", "exact string"), ("variant", "exact string"),
    ("primary", "required uint16"), ("secondary", "nullable uint16"),
    ("operation", "nullable uint16"), ("direction", "exact string"),
    ("field", "exact string"), ("alternative", "exact string"),
    ("group", "nullable uint16"), ("instance_scope", "exact string"),
    ("register", "nullable uint16"),
]
POLICY = [
    ("hardware_encoding", "packed_decimal_pairs", "Hypothesis"),
    ("hardware_width_bytes", "6", "Hypothesis"),
    ("flags_bits", "Unknown", "Unknown"),
    ("invalid_nibble", "candidate absent; preserve all raw bytes", "Proven"),
    ("selection_by_length", "false", "Proven"),
    ("complete_identity_inference", "false", "Proven"),
    ("native_request_admission", "false", "Proven"),
    ("qualification", "Unknown", "Unknown"),
    ("presence", "Unknown", "Unknown"),
    ("freshness", "Unknown", "Unknown"),
    ("execution", "Unknown", "Unknown"),
]


def table(page, heading):
    block = page.split(heading + "\n", 1)[1].split("\n\n", 1)[0]
    return [tuple(cell.strip() for cell in line.strip("|").split("|"))
            for line in block.splitlines()[1:]]


def decimal_pairs(raw):
    """Synthetic arithmetic only, with no position/transport assumptions."""
    if len(raw) != 6 or any(type(b) is not int or not 0 <= b <= 255 for b in raw):
        return None
    if any((b >> 4) > 9 or (b & 15) > 9 for b in raw):
        return None
    return [(b >> 4) * 10 + (b & 15) for b in raw]


class IdentityShapes(unittest.TestCase):
    def setUp(self):
        self.page = PAGE.read_text(encoding="utf-8")
        self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def check_page(self, page):
        self.assertEqual(table(page, "| Key member | Matching |"), AXES)
        self.assertEqual(table(page, "| Property | Value | Grade |"), POLICY)
        self.assertEqual(table(page, "| Operation | Directions | Field | Alternatives | Rows |"), [
            ("83", "read, write", "hardware_identifier", "packed_decimal_candidate", "2"),
            ("84", "Unknown", "identity_content",
             "link_address_six, conflicting_seven, segmented_characters", "3"),
            ("84", "Unknown", "identity_state", "none", "1"),
        ])

    def test_page_contract(self):
        self.check_page(self.page)
        for declaration in (
            "Ab46Entries() (json.RawMessage, error)",
            "Ab46Lookup(key Ab46Key) (json.RawMessage, bool, error)",
            "`nil, false, nil`", "Each call returns independent memory",
            "validates the entire array before exact matching",
            "absence is distinct from zero", "completion predicate remain **Unknown**",
            "No Python check\nhere executes those Go functions",
        ):
            with self.subTest(declaration=declaration):
                self.assertIn(declaration, self.page)

    def test_key_control_and_each_axis(self):
        self.assertEqual(self.data["key_control"], KEY)
        # A structured documentation mutation must fail for each key axis.
        # This tests the declared identity, not another repository's lookup.
        for axis, matching in AXES:
            with self.subTest(axis=axis):
                altered = self.page.replace(
                    f"| {axis} | {matching} |", f"| {axis} | ignored |", 1)
                with self.assertRaises(AssertionError):
                    self.check_page(altered)
                changed = copy.deepcopy(self.data["key_control"])
                changed[axis] = 0 if not isinstance(KEY[axis], str) else "distinct"
                self.assertEqual([k for k in KEY if changed[k] != KEY[k]], [axis])
                self.assertNotEqual(tuple(changed[k] for k, _ in AXES),
                                    tuple(KEY[k] for k, _ in AXES))
        for axis in ("secondary", "operation", "group", "register"):
            with self.subTest(nullable_axis=axis):
                absent, zero = copy.deepcopy(KEY), copy.deepcopy(KEY)
                absent[axis], zero[axis] = None, 0
                self.assertNotEqual(tuple(absent[k] for k, _ in AXES),
                                    tuple(zero[k] for k, _ in AXES))

    def test_hardware_examples(self):
        cases = self.data["hardware"]
        self.assertEqual(len(cases), 2)
        self.assertEqual(cases[0], {
            "raw": [0x12, 0x34, 0x56, 0x78, 0x90, 0x12],
            "candidate_decimal_pairs": [12, 34, 56, 78, 90, 12],
            "candidate_valid": True,
        })
        self.assertEqual(cases[1], {
            "raw": [0xFA, 0x34, 0x56, 0x78, 0x90, 0x12],
            "candidate_decimal_pairs": None, "candidate_valid": False,
        })
        for case in cases:
            with self.subTest(raw=case["raw"]):
                before = copy.deepcopy(case["raw"])
                self.assertEqual(decimal_pairs(case["raw"]), case["candidate_decimal_pairs"])
                self.assertEqual(case["candidate_valid"], decimal_pairs(before) is not None)
                self.assertEqual(case["raw"], before)

    def test_each_decimal_position_and_nibble(self):
        control = [0x12, 0x34, 0x56, 0x78, 0x90, 0x12]
        self.assertEqual(decimal_pairs(control), [12, 34, 56, 78, 90, 12])
        for position in range(6):
            for invalid in (0xA1, 0x1A):
                with self.subTest(position=position, invalid=invalid):
                    changed = control.copy()
                    changed[position] = invalid
                    self.assertIsNone(decimal_pairs(changed))

    def test_alternatives_remain_distinct(self):
        self.assertEqual(self.data["alternatives"], [
            {"alternative": "link_address_six", "raw": [1, 2, 3, 4, 5, 6],
             "width_bytes": 6, "selection_by_length": False},
            {"alternative": "conflicting_seven", "raw": [1, 2, 3, 4, 5, 6, 7],
             "width_bytes": 7, "selection_by_length": False},
        ])

    def test_state_controls_and_independent_axes(self):
        states = {row["id"]: row for row in self.data["states"]}
        self.assertEqual(len(states), len(self.data["states"]))
        self.assertEqual(set(states), {
            "control", "feedback_failure", "status_failure", "extent_partial",
            "segments_incomplete", "segment_failure", "empty_success", "partial_success",
        })
        control = states["control"]
        self.assertEqual(control, {
            "id": "control", "feedback_success": True, "status_success": True,
            "content_extent": "synthetic_full", "segment_completeness": True,
            "segments": [{"raw": [65, 66], "valid": True},
                         {"raw": [67, 68], "valid": True}], "completeIdentity": False,
        })
        for name, axis, value in (
            ("feedback_failure", "feedback_success", False),
            ("status_failure", "status_success", False),
            ("extent_partial", "content_extent", "partial"),
            ("segments_incomplete", "segment_completeness", False),
        ):
            with self.subTest(axis=axis):
                expected = dict(control, id=name)
                expected[axis] = value
                self.assertEqual(states[name], expected)
        for row in states.values():
            with self.subTest(state=row["id"]):
                self.assertIs(row["completeIdentity"], False)
        for name, extent, segments in (
            ("empty_success", "empty", []),
            ("partial_success", "partial", [{"raw": [65, 66], "valid": True}]),
        ):
            self.assertEqual(states[name], dict(
                control, id=name, content_extent=extent,
                segments=segments, segment_completeness=False))

    def test_independent_segment_failure_retains_raw_and_useful_bytes(self):
        row = next(s for s in self.data["states"] if s["id"] == "segment_failure")
        self.assertEqual(row["previous_segments"], [[69, 70], [67, 68]])
        self.assertEqual(row["segments"], [
            {"raw": [65, 66], "valid": True}, {"raw": [250], "valid": False}])
        self.assertEqual(row["retained_segments"], [[65, 66], [67, 68]])
        before = copy.deepcopy(row)
        retained = [list(s["raw"] if s["valid"] else prior)
                    for s, prior in zip(row["segments"], row["previous_segments"])]
        self.assertEqual(retained, [[65, 66], [67, 68]])
        retained[0][0] = 0
        self.assertEqual(row, before)
        self.assertTrue(row["feedback_success"])
        self.assertTrue(row["status_success"])
        self.assertEqual(row["content_extent"], "partial")
        self.assertFalse(row["segment_completeness"])

    def test_each_segment_failure_has_an_unaffected_control(self):
        # Reference retention arithmetic only; not the companion's runtime.
        for failed, expected in ((0, [[69, 70], [67, 68]]),
                                 (1, [[65, 66], [71, 72]])):
            with self.subTest(failed_segment=failed):
                previous = [[69, 70], [71, 72]]
                segments = [{"raw": [65, 66], "valid": True},
                            {"raw": [67, 68], "valid": True}]
                segments[failed] = {"raw": [250], "valid": False}
                retained = [list(s["raw"] if s["valid"] else prior)
                            for s, prior in zip(segments, previous)]
                self.assertEqual(retained, expected)
                self.assertEqual(segments[failed]["raw"], [250])
                self.assertEqual(previous, [[69, 70], [71, 72]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
