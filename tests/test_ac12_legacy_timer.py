"""Synthetic representation checks; no native adaptation or physical result."""

import copy
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "protocols/vaillant/ebus-vaillant-b515.md"
FIXTURE = ROOT / "protocols/vaillant/fixtures/ac12_legacy_timer.json"
AXES = ("family", "variant", "direction", "service", "operation", "alternative")
EXCHANGES = (
    ("read", "request", "request", 4),
    ("read", "positive", "response", 11),
    ("read", "negative", "response", None),
    ("write", "request", "request", 11),
    ("write", "positive", "response", 3),
    ("write", "negative", "response", None),
)
CARRIERS = (
    ("weekday", "read/write request and read positive", "Monday"),
    ("channel", "read/write request: circulation", 2),
    ("channel", "read/write request: DHW", 1),
    ("channel", "read/write request: mixer one", 0),
    ("channel", "read/write request: mixer two", 0),
    ("channel", "read positive", 0),
    ("mode", "read/write request and read positive", None),
)
UNKNOWNS = (
    "physical forms", "competing two-position gap", "enforcement",
    "deletion/reset", "atomicity", "overlap", "midnight-crossing",
    "timezone/DST", "physical schedule effects", "native adaptation",
    "peer effects", "physical qualification",
)


def expected_entries():
    """Independent finite expectations, never derived from page or fixture."""
    rows = []
    for operation, alternative, direction, extent in EXCHANGES:
        rows.append(dict(
            family="Vaillant legacy timer", variant="periods",
            direction=direction, service="B515", operation=operation,
            alternative=alternative, logical_extent=extent,
            physical_extent=None, grade="Hypothesis",
        ))
    for number in range(1, 6):
        name = f"mode candidate {number}"
        rows.append(dict(
            family="Vaillant legacy timer", variant=name, direction=None,
            service="B515", operation=None, alternative=name,
            logical_extent=None, physical_extent=None, grade="Hypothesis",
            raw_domain=[0, 3], injective=False, inverse_default=None, labels=None,
        ))
    return rows


def table(page, heading):
    """Read exactly one scoped Markdown table, including its column names."""
    section = page.split("### " + heading + "\n", 1)[1].split("\n##", 1)[0]
    lines = [line for line in section.splitlines() if line.startswith("|")]
    cells = [[cell.strip() for cell in line.strip("|").split("|")]
             for line in lines]
    return [cells[0]] + cells[2:]


def display(value):
    return "Unknown" if value is None else str(value)


def role_term_pattern():
    """Same role tokens the initiator/target terminology gate rejects."""
    terms = ["m" + "aster", "sl" + "ave"]
    return re.compile(r"\b(" + "|".join(map(re.escape, terms)) + r")\b", re.IGNORECASE)


def role_term_hits(text):
    """Whole-page hits. A legacy-role-mapping region does not excuse them."""
    return [match.group(0) for match in role_term_pattern().finditer(text)]


def invert_unique(mapping):
    """Synthetic ambiguity check, not a protocol encoder."""
    result = {}
    for raw, label in mapping.items():
        if label in result:
            raise ValueError("ambiguous synthetic mode")
        result[label] = raw
    return result


class LegacyTimerTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_entries(self):
        # Catches selector/direction, extent, grade, lost alternatives and
        # null-to-zero mutations, including every identity axis of every row.
        self.assertEqual(self.data["entries"], expected_entries())

    def test_identity_axes_independently(self):
        # Valid control plus one-axis substitutions and omissions. In
        # particular, null direction/operation are not missing identities.
        expected = expected_entries()
        self.assertEqual(self.data["entries"], expected)
        for index, row in enumerate(self.data["entries"]):
            for axis in AXES:
                for omit in (False, True):
                    with self.subTest(index=index, axis=axis, omit=omit):
                        changed = copy.deepcopy(row)
                        if omit:
                            del changed[axis]
                        else:
                            changed[axis] = "distinct synthetic identity"
                        self.assertNotEqual(changed, expected[index])
                        with self.assertRaises(AssertionError):
                            self.assertEqual(changed, expected[index])

    def test_periods(self):
        # Independent clock enumeration catches any conversion change across
        # all 145 labels; endpoints and unknowns have explicit controls.
        expected = {str(hour * 6 + step): f"{hour:02d}:{step * 10:02d}"
                    for hour in range(24) for step in range(6)}
        expected["144"] = "24:00"
        self.assertEqual(self.data["periods"], expected)
        for raw, time in (("0", "00:00"), ("54", "09:00"), ("144", "24:00")):
            self.assertEqual(self.data["periods"][raw], time)
        self.assertEqual(len(self.data["periods"]), 145)
        self.assertEqual(self.data["unknown_raw"], {"145": "Unknown", "255": "Unknown"})
        for raw in ("145", "255"):
            self.assertNotIn(raw, self.data["periods"])
        self.assertEqual(self.data["undeclared_conversion"], {"09:05": None})
        self.assertNotIn("09:05", self.data["periods"].values())

    def test_carriers(self):
        # Catches domains, each context/field selector, defaults and grades.
        self.assertEqual(self.data["carriers"], [
            dict(field=field, context=context, default=default,
                 raw_domain=[0, 255], grade="Hypothesis")
            for field, context, default in CARRIERS
        ])

    def test_grades_and_unknowns(self):
        # Catches promotion of software checks to physical qualification and
        # removal/promotion of any independently unresolved property.
        self.assertIs(self.data["synthetic"], True)
        self.assertEqual(self.data["representation_grade"], "Proven")
        self.assertEqual(self.data["candidate_grade"], "Hypothesis")
        self.assertEqual(self.data["physical_qualification"], "Unknown")
        self.assertEqual(self.data["unknown_properties"],
                         dict.fromkeys(UNKNOWNS, "Unknown"))
        self.assertEqual(set(self.data), {
            "synthetic", "representation_grade", "candidate_grade",
            "physical_qualification", "entries", "periods", "unknown_raw",
            "undeclared_conversion", "carriers", "ordering",
            "unknown_properties", "synthetic_mode", "interval_examples",
        })

    def test_ordering_examples(self):
        # Catches equal=>deletion, peer enforcement, reordered declarations,
        # and any altered raw byte in either synthetic example.
        self.assertEqual(self.data["ordering"], {
            "grade": "Hypothesis", "written_equal": "disabled interval",
            "order": ["first", "second", "third"], "out_of_order": "Unknown",
        })
        self.assertEqual(self.data["interval_examples"], [
            {"raw": [54, 54], "declaration": "disabled interval", "physical_effect": "Unknown"},
            {"raw": [60, 66, 12, 18, 120, 126], "declaration": "out of order", "physical_effect": "Unknown"},
        ])

    def test_ambiguous_mode(self):
        # Changing any synthetic enum member is caught before inversion;
        # allowing a four-to-one inverse must fail the ambiguity assertion.
        self.assertEqual(self.data["synthetic_mode"], {
            "0": "same synthetic label", "1": "same synthetic label",
            "2": "same synthetic label", "3": "same synthetic label",
        })
        self.assertEqual(invert_unique({"0": "a", "1": "b"}), {"a": "0", "b": "1"})
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            invert_unique(self.data["synthetic_mode"])

    def test_page_periods(self):
        self.assertEqual(table(self.page, "Period vocabulary"), [
            ["Raw decimal", "Declared time", "Grade"],
            ["0", "00:00", "Hypothesis"], ["54", "09:00", "Hypothesis"],
            ["144", "24:00", "Hypothesis"], ["145", "Unknown", "Unknown"],
            ["255 (FF)", "Unknown", "Unknown"],
        ])

    def test_page_carriers(self):
        self.assertEqual(table(self.page, "Selector carriers and defaults"), [
            ["Field", "Raw decimal domain", "Context", "Default", "Grade"],
            *[[field, "0..255", context, display(default), "Hypothesis"]
              for field, context, default in CARRIERS],
        ])

    def test_page_extents(self):
        self.assertEqual(table(self.page, "Logical extents"), [
            ["Family", "Variant", "Direction", "Service", "Operation",
             "Alternative", "Logical extent", "Physical extent", "Grade"],
            *[["Vaillant legacy timer", "periods", direction, "B515", op,
               alt, display(extent), "Unknown", "Hypothesis"]
              for op, alt, direction, extent in EXCHANGES],
        ])

    def test_page_modes(self):
        self.assertEqual(table(self.page, "Unnamed mode variants"), [
            ["Family", "Variant", "Direction", "Service", "Operation",
             "Alternative", "Raw decimal domain", "Injective",
             "Inverse default", "Labels", "Grade"],
            *[["Vaillant legacy timer", f"mode candidate {n}", "Unknown",
               "B515", "Unknown", f"mode candidate {n}", "0..3", "no",
               "Unknown", "Unknown", "Hypothesis"] for n in range(1, 6)],
        ])

    def test_page_unknowns(self):
        self.assertEqual(table(self.page, "Ordering and qualification"), [
            ["Property", "Grade"], *[[name, "Unknown"] for name in UNKNOWNS],
        ])

    def test_page_scoped_claims(self):
        # Exact scoped prose guards finite conversion, grade boundaries,
        # unresolved alternatives and preservation, not mere keyword presence.
        scoped = self.page.split("## Finite period declarations\n", 1)[1].split(
            "## Relationship to B555", 1)[0]
        normalized = " ".join(scoped.split())
        for claim in (
            "These are **Hypothesis** candidate declarations for the Vaillant legacy timer family, not confirmed native behavior.",
            "The synthetic representation can be checked as **Proven** software behavior; physical qualification remains **Unknown**.",
            "Raw 0..144 inclusive declares ten-minute steps: 145 labels, not 144.",
            "There is no declared conversion or rounding rule for 09:05.",
            "Raw 145 and FF have no established role; preserve their raw bytes.",
            "Logical extents include prefix positions; they are not physical offsets or validated payload lengths.",
            "The physical forms, including the competing two-position gap, remain Unknown.",
            "Keep both the echoed day/channel reply and the template's up-to-one-ignored-byte reply above as unresolved alternatives.",
            "An absent extent is Unknown, never zero.",
            "Five candidate variants map raw 0..3 non-injectively.",
            "Their exact per-variant labels remain absent.",
            "Preserve each variant and raw value; do not derive a reversible default or merge these variants with the generic ordering above.",
            "Hypothesis: a written start equal to end declares a disabled interval.",
            "First-before-second-before-third ordering is declared as Hypothesis.",
            "An out-of-order interval example remains unqualified; it does not establish rejection, sorting, or any other peer enforcement.",
            "Disabled does not establish deletion or reset.",
            "Preserve complete native bytes and independent useful fields beside any candidate interpretation.",
            "Native adaptation and peer effects remain Unknown; these declarations grant no runtime capability or write admission.",
        ):
            with self.subTest(claim=claim):
                self.assertIn(claim, normalized)
        # Keep the qualified generic layout and its competing reply form.
        for retained in (
            "Read reply:      <weekday> <channel> s1 e1 s2 e2 s3 e3 mode",
            "ign : up to 1 ignored byte",
            "Generic programming mode", "Monday..Friday", "Saturday..Sunday",
        ):
            self.assertIn(retained, self.page)

    def test_reference_role_terms(self):
        # Restoring the default-branch token in a TypeSpec URL is the page
        # mutation this rejects, including inside a legacy-role-mapping region.
        # The three repository-relative paths stay cited on their own.
        token = "m" + "aster"
        self.assertEqual(role_term_hits("initiator and target"), [])
        self.assertEqual(role_term_hits("blob/" + token + "/src"), [token])
        self.assertEqual(role_term_hits(self.page), [])
        references = self.page.split("## References\n", 1)[1]
        for path in (
            "src/vaillant/_templates.tsp",
            "src/vaillant/timerhc_inc.tsp",
            "src/vaillant/timerhwc_inc.tsp",
        ):
            self.assertIn(path, references)
        self.assertIn("https://github.com/john30/ebusd-configuration", references)


if __name__ == "__main__":
    unittest.main()
