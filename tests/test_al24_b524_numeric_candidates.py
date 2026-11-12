"""Finite AL24 document checks; the reference view is not companion code."""

from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "architecture/al24-b524-numeric-candidates.md"
FIXTURE = ROOT / "architecture/fixtures/al24_b524_numeric_candidates.json"
CONTEXT = (
    "ab56_family", "ab56_software", "ab56_hardware", "ab56_api_version",
    "ab56_api_revision", "ab56_variant", "ab56_candidate_set",
)
SELECTOR = ("ab56_opcode", "ab56_group", "ab56_instance", "ab56_register")
STATE = {
    "candidate_grade": "Hypothesis", "physical_qualification": "Unknown",
    "presence": "Unknown", "freshness": "Unknown", "writable": "Unknown",
    "execution": "Unknown", "admitted": False, "runtime_bound": None,
}
POLICY = {
    "tuple_count": 20, "context_match": "exact_all_fields",
    "identity_defaults": False, "wildcard_fallback": False,
    "missing_identity": "constructor_error_or_lookup_miss",
    "memory": "independent_deep_copies", "arithmetic_grade": "Proven",
    **STATE,
    "op06_inheritance": False, "date_time_admission": False,
    "inactive_unknown_slot_admission": False,
    "raw_and_last_known_good": "caller_retains_on_failure",
}

# Independent acceptance oracle, deliberately not loaded from the fixture.
# OP/GG/II/RR, codec/width, decimal minimum/maximum/step.
EXPECTED = """
02 00 00 0003 UIN 2 0 12 1
02 00 00 0080 EXP 4 -10.0 10.0 1.0
02 01 00 0001 UIN 2 0 1 1
02 01 00 0003 UIN 2 0 2 1
02 02 01 0002 UIN 2 0 4 1
02 02 01 0004 EXP 4 15.0 80.0 1.0
02 02 01 0005 UCH 1 0 1 1
02 02 01 0006 UCH 1 0 1 1
02 02 02 0002 UIN 2 0 4 1
02 02 02 0004 EXP 4 15.0 80.0 1.0
02 02 02 0005 UCH 1 0 1 1
02 02 02 0006 UCH 1 0 1 1
02 02 09 0002 UIN 2 0 4 1
02 02 09 0004 EXP 4 15.0 80.0 1.0
02 02 09 0005 UCH 1 0 1 1
02 02 09 0006 UCH 1 0 1 1
02 03 00 0001 UIN 2 0 2 1
02 03 00 0002 EXP 4 15.0 30.0 0.5
02 03 00 0005 EXP 4 5.0 30.0 1.0
02 03 00 0006 UIN 2 0 2 1
"""


def tuple_record(cells):
    if len(cells) != 9:
        raise ValueError("tuple must have nine fields")
    return {
        **dict(zip(SELECTOR, (int(v, 16) for v in cells[:4]))),
        "codec": cells[4], "width": int(cells[5]),
        "minimum": cells[6], "maximum": cells[7], "step": cells[8],
    }


def expected_entries():
    return [tuple_record(line.split()) for line in EXPECTED.strip().splitlines()]


def page_entries(text):
    header = "| OP | GG | II | RR | Codec | Width | Min | Max | Step |"
    lines = text.splitlines()
    start = lines.index(header) + 2
    result = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        result.append(tuple_record([v.strip() for v in line.strip("|").split("|")]))
    return result


def page_policy(text):
    match = re.search(
        r"<!-- al24-policy:begin -->\s*```json\n(.*?)\n```\s*<!-- al24-policy:end -->",
        text, re.S,
    )
    if match is None:
        raise ValueError("missing AL24 policy")
    return json.loads(match[1])


class ReferenceView:
    """Test-only specification model; no runtime admission or decoding."""

    def __init__(self, context, entries):
        if any(type(context.get(k)) is not str or not context[k] for k in CONTEXT):
            raise ValueError("missing caller identity")
        self._context = deepcopy({k: context[k] for k in CONTEXT})
        self._entries = deepcopy(entries)

    def entries(self):
        return deepcopy(self._entries)

    def lookup(self, key):
        if any(type(key.get(k)) is not str or key[k] != self._context[k] for k in CONTEXT):
            return None
        if any(type(key.get(k)) is not int or not 0 <= key[k] <= limit
               for k, limit in zip(SELECTOR, (255, 255, 255, 65535))):
            return None
        for row in self._entries:
            if all(key[k] == row[k] for k in SELECTOR):
                return deepcopy({"key": {k: key[k] for k in CONTEXT + SELECTOR},
                                 "tuple": row, "state": STATE})
        return None


class AL24ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PAGE.read_text(encoding="utf-8")
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.rows = page_entries(cls.text)

    def baseline(self):
        context = dict(zip(CONTEXT, (
            "synthetic-family-a", "synthetic-software-a", "synthetic-hardware-a",
            "synthetic-api-version-a", "synthetic-api-revision-a",
            "synthetic-variant-a", "synthetic-candidate-set-a",
        )))
        key = {**context, **dict(zip(SELECTOR, (2, 3, 0, 2)))}
        view = ReferenceView(context, self.rows)
        self.assertIsNotNone(view.lookup(key), "positive half-step control missing")
        return context, key, view

    def test_complete_twenty_tuple_oracle(self):
        self.assertEqual(self.rows, expected_entries())
        selectors = [tuple(row[k] for k in SELECTOR) for row in self.rows]
        self.assertEqual(len(selectors), 20)
        self.assertEqual(len(set(selectors)), 20)
        self.assertNotIn((2, 0, 0, 1), selectors)
        self.assertEqual([sum(r["ab56_group"] == g for r in self.rows)
                          for g in range(4)], [2, 2, 12, 4])
        for row in self.rows:
            self.assertEqual(row["ab56_opcode"], 2)
            self.assertEqual(row["width"], {"UCH": 1, "UIN": 2, "EXP": 4}[row["codec"]])

    def test_page_policy_signatures_identity_and_links(self):
        self.assertEqual(page_policy(self.text), POLICY)
        for signature in (
            "Ab56Entries() -> []Ab56Tuple",
            "Ab56NewView(context Ab56Context) -> (*Ab56View, error)",
            "(*Ab56View).Ab56Lookup(key Ab56Key) -> (Ab56Entry, bool)",
        ):
            self.assertIn(signature, self.text)
        fields = re.findall(r"^\| (ab56_\w+) \| (.*?) \|$", self.text, re.M)
        self.assertEqual([name for name, _ in fields], list(CONTEXT + SELECTOR))
        self.assertEqual([domain for _, domain in fields[:7]],
                         ["nonempty opaque caller string"] * 7)
        self.assertEqual([domain for _, domain in fields[7:]],
                         ["explicit integer byte"] * 3 + ["explicit unsigned 16-bit integer"])
        for phrase in (
            "The catalog prerequisite must merge before this page.",
            "Nothing is stable before Helianthus 1.0.",
            "no companion code result, native effect or full parity",
            "Existing eBUS MCP compatibility and GraphQL parity",
            "caller", "last-known-good", "LookupB524Bound",
        ):
            self.assertIn(phrase, self.text)
        links = re.findall(r"\]\(([^)]+)\)", self.text)
        self.assertIn("../protocols/vaillant/ebus-vaillant-b524.md", links)
        self.assertIn("../types/ebusd-csv.md", links)
        for link in links:
            self.assertTrue((PAGE.parent / link.split("#")[0]).is_file(), link)

    def test_small_examples_have_independent_expected_results(self):
        self.assertEqual(set(self.fixture),
                         {"scope", "context", "expected_state", "examples", "arithmetic"})
        self.assertEqual(self.fixture["scope"], "synthetic_examples_only")
        self.assertEqual(self.fixture["expected_state"], STATE)
        self.assertEqual(set(self.fixture["context"]), set(CONTEXT))
        for token in self.fixture["context"].values():
            self.assertTrue(token.startswith("synthetic-"))
        examples = self.fixture["examples"]
        expected = {
            "system-count": (2, 0, 0, 3, "UIN", 2, "0", "12", "1"),
            "signed-range": (2, 0, 0, 128, "EXP", 4, "-10.0", "10.0", "1.0"),
            "half-step": (2, 3, 0, 2, "EXP", 4, "15.0", "30.0", "0.5"),
            "separate-instance-1": (2, 2, 1, 5, "UCH", 1, "0", "1", "1"),
            "separate-instance-2": (2, 2, 2, 5, "UCH", 1, "0", "1", "1"),
            "separate-instance-9": (2, 2, 9, 5, "UCH", 1, "0", "1", "1"),
        }
        self.assertEqual(len(examples), 6)
        self.assertEqual({e["id"] for e in examples}, set(expected))
        for example in examples:
            with self.subTest(example=example["id"]):
                self.assertEqual(set(example), {"id", "selector", "expected_candidate"})
                selector, candidate = example["selector"], example["expected_candidate"]
                self.assertEqual(set(selector), set(SELECTOR))
                self.assertEqual(set(candidate), {"codec", "width", "minimum", "maximum", "step"})
                actual = tuple(selector[k] for k in SELECTOR) + tuple(
                    candidate[k] for k in ("codec", "width", "minimum", "maximum", "step"))
                self.assertEqual(actual, expected[example["id"]])
                view = ReferenceView(self.fixture["context"], self.rows)
                entry = view.lookup({**self.fixture["context"], **selector})
                self.assertIsNotNone(entry)
                self.assertEqual({k: entry["tuple"][k] for k in candidate}, candidate)
                self.assertEqual(entry["state"], STATE)

    def test_every_context_axis_exact_and_independent(self):
        context, key, view = self.baseline()
        self.assertIsNotNone(view.lookup(key))
        for axis in CONTEXT:
            with self.subTest(axis=axis):
                changed = {**key, axis: key[axis] + "-other"}
                self.assertEqual([k for k in key if changed[k] != key[k]], [axis])
                self.assertIsNone(view.lookup(changed))
                other_context = {**context, axis: changed[axis]}
                other = ReferenceView(other_context, self.rows)
                self.assertEqual(other.lookup(changed)["key"], changed)
                self.assertIsNone(other.lookup(key))
                # Literal star and case/spacing changes have no wildcard/default effect.
                for replacement in ("*", key[axis].upper(), " " + key[axis]):
                    self.assertIsNone(view.lookup({**key, axis: replacement}))
                for invalid in (None, "", 0, False):
                    with self.assertRaises(ValueError):
                        ReferenceView({**context, axis: invalid}, self.rows)
                    self.assertIsNone(view.lookup({**key, axis: invalid}))
                missing_context, missing_key = deepcopy(context), deepcopy(key)
                del missing_context[axis]
                del missing_key[axis]
                with self.assertRaises(ValueError):
                    ReferenceView(missing_context, self.rows)
                self.assertIsNone(view.lookup(missing_key))

    def test_every_selector_axis_missing_changed_and_invalid(self):
        _, key, view = self.baseline()
        for axis, replacement in zip(SELECTOR, (6, 4, 1, 0x0102)):
            with self.subTest(axis=axis):
                changed = {**key, axis: replacement}
                self.assertEqual([k for k in key if changed[k] != key[k]], [axis])
                self.assertIsNone(view.lookup(changed))
                missing = deepcopy(key)
                del missing[axis]
                self.assertIsNone(view.lookup(missing))
                limit = 65535 if axis == "ab56_register" else 255
                for invalid in (None, "2", False, -1, limit + 1):
                    self.assertIsNone(view.lookup({**key, axis: invalid}))
        # Both bytes of the full register key vary independently.
        for register in (0x0003, 0x0102):
            self.assertIsNone(view.lookup({**key, "ab56_register": register}))

    def test_instances_remain_distinct_without_presence(self):
        context, _, view = self.baseline()
        for instance in (1, 2, 9):
            key = {**context, **dict(zip(SELECTOR, (2, 2, instance, 5)))}
            entry = view.lookup(key)
            self.assertIsNotNone(entry, "positive instance control missing")
            self.assertEqual(entry["key"], key)
            self.assertEqual(entry["tuple"]["ab56_instance"], instance)
            self.assertEqual(entry["state"], STATE)
            self.assertEqual(sum(r["ab56_group"] == 2 and r["ab56_instance"] == instance
                                 for r in self.rows), 4)
        for instance in (0, 3, 255):
            self.assertIsNone(view.lookup({**context, **dict(zip(SELECTOR, (2, 2, instance, 5)))}))

    def test_op06_excluded_bound_and_date_time_do_not_inherit(self):
        context, _, view = self.baseline()
        for row in self.rows:
            key = {**context, **{k: row[k] for k in SELECTOR}}
            self.assertEqual(view.lookup(key)["state"], STATE)
            self.assertIsNone(view.lookup({**key, "ab56_opcode": 6}))
        # Synthetic unmatched selectors; no date/time interpretation is assigned.
        for selector in ((2, 0, 0, 1), (2, 0, 0, 0xFFFE), (6, 0, 0, 1)):
            self.assertIsNone(view.lookup({**context, **dict(zip(SELECTOR, selector))}))

    def test_decimal_membership_is_not_edit_admission(self):
        _, key, view = self.baseline()
        entry = view.lookup(key)
        row = entry["tuple"]
        low, high, step = (Decimal(row[k]) for k in ("minimum", "maximum", "step"))
        self.assertEqual((low, high, step), (Decimal(15), Decimal(30), Decimal("0.5")))
        controls = [("15", True), ("15.5", True), ("30", True), ("15.25", False)]
        self.assertEqual(self.fixture["arithmetic"], [
            {"value": v, "expected_member": member, "expected_admitted": False}
            for v, member in controls])
        for value, expected in controls + [("14.5", False), ("30.5", False)]:
            number = Decimal(value)
            self.assertEqual(low <= number <= high and (number - low) % step == 0, expected)
            self.assertIs(entry["state"]["admitted"], False)
            self.assertIsNone(entry["state"]["runtime_bound"])

    def test_results_context_and_catalog_have_independent_memory(self):
        context, key, view = self.baseline()
        original = deepcopy(view.lookup(key))
        first, second = view.lookup(key), view.lookup(key)
        other_view = ReferenceView(deepcopy(context), self.rows)
        for axis in CONTEXT:
            context[axis] = "changed-input"
        first["key"]["ab56_family"] = "changed-result"
        first["tuple"]["maximum"] = "999"
        first["state"]["admitted"] = True
        catalog = view.entries()
        catalog[0]["minimum"] = "999"
        catalog.clear()
        key["ab56_register"] = 0xFFFF
        fresh_key = original["key"]
        self.assertEqual(second, original)
        self.assertEqual(view.lookup(fresh_key), original)
        self.assertEqual(other_view.lookup(fresh_key), original)
        self.assertEqual(view.entries(), expected_entries())
        self.assertEqual(self.rows, expected_entries())

    def test_miss_preserves_independent_caller_evidence(self):
        _, key, view = self.baseline()
        evidence = {"attempt_raw": bytearray.fromhex("00"),
                    "useful_fields": {"request_instance": 0},
                    "last_known_good": {"raw": bytearray.fromhex("00007841"),
                                        "local_value": "15.5", "fresh": False}}
        before = deepcopy(evidence)
        self.assertIsNone(view.lookup({**key, "ab56_opcode": 6}))
        self.assertEqual(evidence, before)


if __name__ == "__main__":
    unittest.main()
