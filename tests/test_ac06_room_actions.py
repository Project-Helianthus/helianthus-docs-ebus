"""Synthetic declaration checks; no native decoder or physical qualification."""
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "protocols/vaillant/ebus-vaillant.md"
FIXTURE = ROOT / "protocols/vaillant/fixtures/ac06_room_actions.json"
AXES = ("family", "variant", "direction", "service", "operation", "alternative")
SPECS = (
    ("B50A", "room-action-temperature", "read", "OP00", (0, 3, None)),
    ("B50C", "keycode-digits", "read", "OP00", (0, 4, None)),
    ("B50C", "signed-value", "read", "OP01", (0, 2, None)),
    ("B50C", "circuit-names", "read", "OP02", (None, None, None)),
    ("B50D", "ui-room-action", "UI-write", "OP00", (1, None, None)),
    ("B50D", "ui-holiday-status", "UI-write", "OP01", (1, None, None)),
)
ACTION = {
    "width": 1, "carrier": [0, 255], "signed": False,
    "byte_order": "not applicable", "factor": 1, "offset": 0, "unit": None,
    "default": None, "labels": {"0": "no-action", "1": "switch-on", "2": "thermostat"},
    "sentinel": "Unknown",
}
TEMPERATURE = {
    "width": 2, "carrier": [-32768, 32767], "signed": True,
    "byte_order": "little-endian", "factor": 0.0625, "offset": 0,
    "unit": "degrees C", "default": None, "labels": {}, "sentinel": "Unknown",
    "candidate_range": [-2048, 2047.9375],
}
DIGIT = {
    "width": 1, "carrier": [0, 255], "candidate_domain": [0, 9],
    "signed": False, "byte_order": "not applicable", "factor": 1, "offset": 0,
    "unit": None, "default": 0, "labels": {}, "sentinel": "Unknown",
}
SIGNED = {
    "width": 2, "carrier": [-32768, 32767], "signed": True,
    "byte_order": "little-endian", "factor": 1, "offset": 0,
    "unit": None, "default": None, "labels": {}, "sentinel": "Unknown",
}
FIELDS = (
    {"room_action": ACTION, "temperature": TEMPERATURE},
    {f"digit_{n}": DIGIT for n in range(1, 5)},
    {"value": SIGNED},
    {"circuit_name": {"width": None, "unit": None, "sentinel": "Unknown"}},
    {"room_action": dict(ACTION, default=0)},
    {"holiday_status": dict(ACTION, default=0, labels={"0": "0", "1": "1"})},
)
QUALIFICATIONS = [
    {"service": "07/04", "path": "working identification response, 10 bytes",
     "grade": "Proven", "boundary": "observed targets only"},
    {"service": "09/00", "path": "RAM target response",
     "grade": "Proven", "boundary": "observed controller only"},
    {"service": "09/02", "path": "EEPROM target response",
     "grade": "Proven", "boundary": "observed controller only"},
]
FIELD_PAGE_ROWS = [
    ["B50A / OP00 positive", "room-action byte, then temperature",
     "unsigned 0..255; signed LE16 / 16 degrees C",
     "0 no-action, 1 switch-on, 2 thermostat; 3..255 unlabeled", "Hypothesis"],
    ["B50C / OP00 positive", "four independent numeric digit bytes",
     "each 0..9; not ASCII/BCD/u32", "each default zero", "Hypothesis"],
    ["B50C / OP01 positive", "signed value", "signed LE16; factor 1, offset 0",
     "unit and sentinel Unknown", "Hypothesis"],
    ["B50C / OP02 positive", "circuit name", "extent Unknown",
     "independent per-circuit values/failures", "Hypothesis"],
    ["B50D / OP00 request", "raw room-action byte", "unsigned 0..255",
     "0 no-action, 1 switch-on, 2 thermostat; default zero; 3..255 unlabeled", "Hypothesis"],
    ["B50D / OP01 request", "raw holiday-status byte", "unsigned 0..255",
     "labels 0/1; default zero; 2..255 unlabeled", "Hypothesis"],
]


def section(page, start, end):
    return page.split(start, 1)[1].split(end, 1)[0]


def table(text, header):
    lines = text.splitlines()
    start = lines.index(header)
    rows = []
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


def candidate(field, raw):
    """Interpret only the declared synthetic field, retaining its raw input."""
    carrier = int.from_bytes(raw, "little", signed=field["signed"])
    return carrier * field["factor"] + field["offset"]


class RoomActions(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()
        self.room = section(self.page, "### B50A to B50D:", "### B50F:")

    def row(self, family, variant, direction, service, operation, alternative):
        key = (family, variant, direction, service, operation, alternative)
        matches = [row for row in self.doc["rows"]
                   if tuple(row[axis] for axis in AXES) == key]
        self.assertEqual(len(matches), 1, key)
        return matches[0]

    def test_identities_extents_and_grade(self):
        expected_keys = set()
        for family, variant, direction, op, extents in SPECS:
            for alternative, extent in zip(("request", "positive", "negative"), extents):
                key = (family, variant, direction, family, op, alternative)
                expected_keys.add(key)
                with self.subTest(identity=key):
                    row = self.row(*key)
                    known = (direction == "read" and alternative == "positive"
                             or direction == "UI-write" and alternative == "request")
                    fields = FIELDS[next(i for i, spec in enumerate(SPECS)
                                         if spec[:4] == (family, variant, direction, op))]
                    self.assertEqual(row, dict(
                        zip(AXES, key),
                        extent_bytes=extent, absolute_offset=None,
                        grade="Hypothesis", physical_qualification="Unknown",
                        fields=fields if known else {},
                        relative_order=list(fields) if known else [],
                    ))
        self.assertEqual(len(self.doc["rows"]), 18)
        self.assertEqual({tuple(r[a] for a in AXES) for r in self.doc["rows"]},
                         expected_keys)

    def test_unknowns_and_representation_grade(self):
        self.assertIs(self.doc["synthetic_only"], True)
        self.assertEqual(self.doc["representation_grade"], "Proven")
        self.assertEqual(self.doc["candidate_grade"], "Hypothesis")
        self.assertEqual(self.doc["physical_qualification"], "Unknown")
        self.assertEqual(self.doc["unknowns"], [
            "B50A unavailable sentinel: neither 8000 nor FFFF qualified",
            "B50C OP01 unit and sentinel", "B50C OP02 echoed circuit",
            "B50C OP02 string trimming", "B50C OP02 B524 namespace equivalence",
            "B50C OP02 wildcard semantics of zero", "absolute offsets",
            "native adaptation", "peer effects",
        ])

    def test_b50a_synthetic_results(self):
        fields = self.row("B50A", "room-action-temperature", "read", "B50A",
                          "OP00", "positive")["fields"]
        expected = [
            ("02 80 FF", 2, "thermostat", -8),
            ("03 00 00", 3, None, 0),
            ("00 00 80", 0, "no-action", -2048),
            ("00 FF FF", 0, "no-action", -0.0625),
            ("01 FF 7F", 1, "switch-on", 2047.9375),
        ]
        self.assertEqual(len(self.doc["b50a_examples"]), 5)
        for example, (raw, action, label, temperature) in zip(self.doc["b50a_examples"], expected):
            with self.subTest(raw=raw):
                self.assertEqual(example, dict(raw=raw, action=action, label=label,
                                               temperature=temperature))
                wire = bytes.fromhex(example["raw"])
                self.assertEqual(wire[0], action)
                self.assertEqual(fields["room_action"]["labels"].get(str(wire[0])), label)
                self.assertEqual(candidate(fields["temperature"], wire[1:]), temperature)
        self.assertEqual(candidate(fields["temperature"], bytes.fromhex("00 80")), -2048)
        self.assertEqual(candidate(fields["temperature"], bytes.fromhex("FF 7F")), 2047.9375)

    def test_b50c_digits_and_signed_result(self):
        fields = self.row("B50C", "keycode-digits", "read", "B50C",
                          "OP00", "positive")["fields"]
        self.assertEqual(self.doc["digits"], [1, 2, 3, 4])
        for name, raw, expected in zip(
                ("digit_1", "digit_2", "digit_3", "digit_4"),
                self.doc["digits"], (1, 2, 3, 4)):
            self.assertEqual(candidate(fields[name], bytes([raw])), expected)
        field = self.row("B50C", "signed-value", "read", "B50C",
                         "OP01", "positive")["fields"]["value"]
        self.assertEqual(self.doc["signed_example"], {"raw": "FE FF", "value": -2, "unit": None})
        self.assertEqual(candidate(field, bytes.fromhex(self.doc["signed_example"]["raw"])), -2)
        self.assertIsNone(field["unit"])

    def test_partial_circuit_state_and_raw_bytes(self):
        # Independent expected outcomes catch lost successes, trimming and erased last-good data.
        self.assertEqual(self.doc["circuit_examples"], [
            {"circuit": 1, "raw": "41 20", "failure": None, "last_good": "41 20"},
            {"circuit": 2, "raw": None, "failure": "synthetic failure", "last_good": "42 20"},
            {"circuit": 3, "raw": "43 20", "failure": None, "last_good": "43 20"},
        ])

    def test_b50d_raw_unknowns(self):
        self.assertEqual(self.doc["ui_examples"], [
            {"operation": "OP00", "raw": 255, "label": None},
            {"operation": "OP01", "raw": 255, "label": None},
        ])
        for op, variant, name in (("OP00", "ui-room-action", "room_action"),
                                  ("OP01", "ui-holiday-status", "holiday_status")):
            field = self.row("B50D", variant, "UI-write", "B50D", op, "request")["fields"][name]
            self.assertNotIn("255", field["labels"])
            self.assertEqual(candidate(field, b"\xff"), 255)

    def test_page_identity_extent_table(self):
        expected = []
        for family, variant, direction, op, extents in SPECS:
            expected.append([family, variant, direction, family, op,
                             *("Unknown" if x is None else str(x) for x in extents),
                             "Hypothesis"])
        self.assertEqual(table(self.room,
            "| Family | Variant | Direction | Service | Operation | Request extent | Positive extent | Negative extent | Grade |"),
            expected)

    def test_page_field_table(self):
        self.assertEqual(table(self.room,
            "| Family / operation | Candidate fields in relative order | Carrier / conversion | Labels / defaults | Grade |"),
            FIELD_PAGE_ROWS)

    def test_page_scoped_claims_and_preserved_variants(self):
        text = re.sub(r"\s+", " ", self.room)
        for claim in (
            "physical qualification, native adaptation and peer effects remain **Unknown**.",
            "No absolute offset is assigned to the B50A, B50C or B50D fields here.",
            "Unresolved response alternatives retain raw bytes; an Unknown extent is not zero.",
            "B50A OP00 and B50C OP00/OP01 have no arguments.",
            "Positive and negative alternatives whose extents are Unknown remain unresolved, rather than empty results.",
            "B50A's signed carrier range is -32768..32767, giving -2048..2047.9375 degrees C.",
            "Unavailable sentinel is **Unknown**: neither `8000` nor `FFFF` is a qualified unavailable marker.",
            "Synthetic `02 80 FF` is candidate thermostat and -8 degrees C;",
            "`03 00 00` retains unlabeled action 3.",
            "Temperature bytes `00 80` remain the signed candidate -2048;",
            "`FF FF` remains -0.0625, with no unavailable promotion.",
            "B50C digits `01 02 03 04` remain four values [1, 2, 3, 4].",
            "OP01 `FE FF` is candidate signed -2 with **Unknown** unit and sentinel;",
            "OP02 preserves independent per-circuit successes and failures:",
            "valid circuits 1 and 3 survive a failed circuit 2.",
            "A bounded 1..15 aggregate is not installed cardinality.",
            "Echoed circuit, string trimming, B524 namespace equivalence and wildcard semantics of zero are **Unknown**.",
            "Keep raw name bytes and partial last-known-good values;",
            "neither a failed read nor an unresolved alternative erases a successful value.",
            "UI-direction writes are distinct from remote-control writes and completed UI effects.",
            "Unknown raw 255 remains unlabeled for both operations.",
        ):
            with self.subTest(claim=claim):
                self.assertIn(claim, text)
        rows = table(self.room, "| Service | Candidate layout |")
        self.assertEqual(rows, [
            ["`B5 0B 00` request", "room action `u8` @3: 0 no action, 1 switch on, 2 thermostat"],
            ["`B5 0B 01`", "holiday period: number `u8` @3, start day/month/year @4/5/6, end day/month/year @7/8/9; plain `u8` values (day 1..31, month 1..12, year 0..99), not BCD"],
            ["`B5 0B 02`", "holiday setpoint `u8` °C, 5..30"],
            ["`B5 0B 05`", "holiday status `u8`: 0 stop, 1 start"],
            ["`B5 0B 03` (write)", "4-digit keycode as four `u8` digits (0..9) @3..6"],
            ["`B5 0B 04`", "circuit name written as 10 ASCII bytes @3..12 (default: the ten characters `0000000000`); no explicit circuit index"],
        ])

    def test_independent_return_services(self):
        self.assertEqual(self.doc["return_examples"], [
            {"tag": "B501-status", "service": "B501", "alternative": "positive-status",
             "raw": "B5 02 00", "interpretation": "status", "grade": "Proven distinction"},
            {"tag": "B502-data", "service": "B502", "alternative": "return-data",
             "raw": "B5 02 00", "interpretation": "opaque", "grade": "Proven distinction"},
        ])
        text = section(self.page, "### B501 and B502:", "### B50A to B50D:")
        self.assertEqual(table(text, "| Tagged case | Service identity | Interpretation | Grade |"), [
            ["B501-status", "B501", "positive-status form; candidate prefix B5 02", "Proven distinction"],
            ["B502-data", "B502", "independent return-data service; variable data opaque", "Proven distinction"],
        ])
        normalized = re.sub(r"\s+", " ", text)
        for claim in (
            "B502 is an independent return-data service, distinct from a B501 positive-status form",
            "B502 variable data remains opaque;",
            "the alternative candidate reading of a leading zero as no error and a nonzero value as an error number remains unresolved.",
        ):
            self.assertIn(claim, normalized)
        self.assertNotIn("B502 positive", self.page)

    def test_separate_standard_service_qualifications(self):
        self.assertEqual(self.doc["service_qualifications"], QUALIFICATIONS)
        text = section(self.page, "### Standard eBUS Protocols", "### Vaillant Proprietary")
        self.assertEqual(table(text, "| Service | Qualified path | Grade | Boundary |"),
                         [[r["service"], r["path"], r["grade"], r["boundary"]] for r in QUALIFICATIONS])
        normalized = re.sub(r"\s+", " ", text)
        self.assertIn("not family-wide peer support.", normalized)
        self.assertIn("Each target-response qualification stands separately.", normalized)
        self.assertIn("They do not establish support or absence of support for every other standard service or every peer.", normalized)
        self.assertNotIn("only standard eBUS command", text)
        self.assertNotIn("All other standard profiles", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
