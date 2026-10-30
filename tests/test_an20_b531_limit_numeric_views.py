"""Checks for the AN20 B531 local numeric helper contract.

The oracle below is the software contract. Fixture rows and the architecture
page must agree with it. A byte-for-byte copy of either file is not the check.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "architecture" / "an20_b531_limit_numeric_views.md"
FIXTURE = ROOT / "architecture" / "fixtures" / "an20_b531_limit_numeric_views.json"

POLICY = {
    "api": "ab19an19",
    "decode": "unsigned_le16",
    "scale": "mul10_to_u32",
    "ffff_sentinel": False,
    "min_max_order": "retain",
    "getter": "floor_div_10_then_low16",
    "fresh_pair": "both_attempt_fields_complete",
    "native_unit": "Unknown",
    "numeric_grade": "Proven",
    "semantic_grade": "Hypothesis",
    "getter_numeric_grade": "Hypothesis",
    "raw_buffers": "copied_per_call",
}

PAIR_GRADES = {"numeric": "Proven", "semantic": "Hypothesis", "native": "Unknown"}
GETTER_GRADES = {
    "numeric": "Hypothesis",
    "semantic": "Hypothesis",
    "native": "Unknown",
}

SELECTION_KEYS = ("family", "variant", "operation", "direction")
BASELINE_ID = "limits-ffff"

# Each id changes only these input paths relative to limits-ffff.
# The production mutation named in the test method is the fixture or page
# change that this delta-plus-oracle pair rejects.
INPUT_DELTAS = {
    "limits-ffff": set(),
    "limits-unsorted": {"minimum.raw_hex", "maximum.raw_hex"},
    "identity-family": {"selection.family"},
    "identity-variant": {"selection.variant"},
    "identity-operation": {"selection.operation"},
    "identity-direction": {"selection.direction"},
    "word-min-0001": {"minimum.raw_hex"},
    "word-min-00ff": {"minimum.raw_hex"},
    "word-max-00ff": {"maximum.raw_hex"},
    "length-min-missing": {"minimum.raw_hex"},
    "length-min-one": {"minimum.raw_hex"},
    "length-min-three": {"minimum.raw_hex"},
    "length-max-one": {"maximum.raw_hex"},
    "outcome-min-failed": {"minimum.read"},
    "outcome-max-failed": {"maximum.read"},
    "outcome-both-failed": {"minimum.read", "maximum.read"},
    "outcome-min-failed-empty": {"minimum.read", "minimum.raw_hex"},
    "prior-min-state-missing": {
        "prior_minimum.state",
        "prior_minimum.raw_hex",
        "prior_minimum.scaled_u32",
    },
    "prior-max-state-missing": {
        "prior_maximum.state",
        "prior_maximum.raw_hex",
        "prior_maximum.scaled_u32",
    },
    "prior-min-state-malformed": {
        "prior_minimum.state",
        "prior_minimum.raw_hex",
        "prior_minimum.scaled_u32",
    },
    "prior-min-value": {"prior_minimum.scaled_u32"},
    "prior-max-value": {"prior_maximum.scaled_u32"},
}

REQUIRED_PHRASES = (
    "unsigned LE16",
    "multiply each by 10",
    "Native unit is Unknown",
    "Minimum greater than maximum is retained",
    "FFFF has no qualified sentinel",
    "floor(raw/10)",
    "low16",
    "fresh-pair requires both successful fields",
    "The result echoes Family, Variant, Operation and Direction",
    "not saturation or round-to-nearest",
    "ab19an19",
    "AN19",
    "DecodeB531LimitField",
    "ProjectB531LimitPair",
    "GetterB531LocalCount",
    "Proven",
    "Hypothesis",
    "Unknown",
)

AUTHORIZATIONS = (
    re.compile(r"signed\s*16\s+decoding\s+is\s+permitted", re.I),
    re.compile(r"saturate\s+at\s+65535", re.I),
    re.compile(r"narrow\s+before\s+dividing", re.I),
    re.compile(r"round\s+to\s+nearest", re.I),
    re.compile(r"FFFF\s+is\s+unavailable", re.I),
    re.compile(r"sort\s+minimum\s+and\s+maximum", re.I),
    re.compile(r"retained\s+limits\s+are\s+fresh", re.I),
)

POLICY_RE = re.compile(
    r"<!-- an20-policy:begin -->\s*```json\n(.*?)\n```\s*<!-- an20-policy:end -->",
    re.S,
)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")
PAIR_HEADER = (
    "| id | min_read | min_raw | max_read | max_raw | min_scaled | max_scaled "
    "| fresh_pair | prior_min_scaled | prior_max_scaled |"
)
GETTER_HEADER = "| raw_u32 | result_u16 |"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def page_policy(text: str) -> dict:
    match = POLICY_RE.search(text)
    if match is None:
        raise ValueError("policy block missing")
    return json.loads(match.group(1))


def decode_attempt(raw, read: str) -> dict:
    """Copy raw, then apply the unsigned-LE16 contract. read is independent of length."""
    if isinstance(raw, str):
        blob = bytes.fromhex(raw)
    else:
        blob = bytes(raw)
    if read == "failed":
        return {"raw_hex": blob.hex(), "state": "failed", "scaled_u32": None}
    if read != "succeeded":
        raise ValueError(read)
    if len(blob) == 0:
        return {"raw_hex": "", "state": "missing", "scaled_u32": None}
    if len(blob) != 2:
        return {"raw_hex": blob.hex(), "state": "malformed", "scaled_u32": None}
    scaled = int.from_bytes(blob, "little", signed=False) * 10
    return {"raw_hex": blob.hex(), "state": "complete", "scaled_u32": scaled}


def copy_field(field: dict) -> dict:
    return {
        "raw_hex": field["raw_hex"],
        "state": field["state"],
        "scaled_u32": field["scaled_u32"],
    }


def project(example: dict) -> dict:
    attempt_minimum = decode_attempt(example["minimum"]["raw_hex"], example["minimum"]["read"])
    attempt_maximum = decode_attempt(example["maximum"]["raw_hex"], example["maximum"]["read"])
    fresh = (
        attempt_minimum["state"] == "complete" and attempt_maximum["state"] == "complete"
    )
    return {
        "selection": {key: example["selection"][key] for key in SELECTION_KEYS},
        "attempt_minimum": attempt_minimum,
        "attempt_maximum": attempt_maximum,
        "prior_minimum": copy_field(example["prior_minimum"]),
        "prior_maximum": copy_field(example["prior_maximum"]),
        "fresh_pair": fresh,
        "ffff_sentinel": False,
    }


def getter(raw: int) -> int:
    if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0 or raw > 0xFFFFFFFF:
        raise ValueError(raw)
    return (raw // 10) & 0xFFFF


def input_delta(example: dict, baseline: dict) -> set[str]:
    deltas = set()
    for key in SELECTION_KEYS:
        if example["selection"][key] != baseline["selection"][key]:
            deltas.add(f"selection.{key}")
    for side in ("minimum", "maximum"):
        for key in ("read", "raw_hex"):
            if example[side][key] != baseline[side][key]:
                deltas.add(f"{side}.{key}")
    for side in ("prior_minimum", "prior_maximum"):
        for key in ("state", "raw_hex", "scaled_u32"):
            if example[side][key] != baseline[side][key]:
                deltas.add(f"{side}.{key}")
    return deltas


def parse_table(text: str, header: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == header:
            start = index
            break
    if start is None:
        raise ValueError(f"missing table {header}")
    rows = []
    for line in lines[start + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        header_cells = [cell.strip() for cell in header.strip().strip("|").split("|")]
        if len(cells) != len(header_cells):
            raise ValueError(line)
        rows.append(dict(zip(header_cells, cells)))
    if not rows:
        raise ValueError(f"empty table {header}")
    return rows


def scaled_cell(value):
    if value is None:
        return "absent"
    return str(value)


def contract_errors(page_path: Path, fixture_path: Path) -> list[str]:
    errors: list[str] = []
    text = page_path.read_text(encoding="utf-8")
    try:
        policy = page_policy(text)
    except ValueError as exc:
        return [str(exc)]
    if policy != POLICY:
        errors.append("page policy != software contract")
    for phrase in REQUIRED_PHRASES:
        if phrase not in text:
            errors.append(f"missing phrase: {phrase}")
    for pattern in AUTHORIZATIONS:
        if pattern.search(text):
            errors.append(f"authorizes rejected behavior: {pattern.pattern}")
    if re.search(r"\bwatts?\b", text, re.I) or "10 W" in text:
        errors.append("page states a wire unit")
    for target in LINK_RE.findall(text):
        if "://" in target or target.startswith("mailto:"):
            errors.append(f"external link: {target}")
            continue
        relative = target.split("#", 1)[0]
        if not relative:
            continue
        resolved = (page_path.parent / relative).resolve()
        if not resolved.is_file():
            errors.append(f"unresolved link: {target}")
    try:
        document = load_json(fixture_path)
    except json.JSONDecodeError as exc:
        return errors + [f"fixture json: {exc}"]
    if document.get("contract") != POLICY:
        errors.append("fixture contract != software contract")
    if document.get("pair_grades") != PAIR_GRADES:
        errors.append("fixture pair grades changed")
    if document.get("getter_grades") != GETTER_GRADES:
        errors.append("fixture getter grades changed")
    examples = {row["id"]: row for row in document["pair_examples"]}
    if set(examples) != set(INPUT_DELTAS):
        errors.append("pair example ids != independent axis set")
        return errors
    baseline = examples[BASELINE_ID]
    for example_id, row in examples.items():
        if input_delta(row, baseline) != INPUT_DELTAS[example_id]:
            errors.append(f"{example_id}: input axes are not independent")
        expected = project(row)
        declared = row["expect"]
        if declared != expected:
            errors.append(f"{example_id}: declared result != oracle")
    for row in document["getter_examples"]:
        if getter(row["raw_u32"]) != row["result_u16"]:
            errors.append(f"{row['id']}: getter result != floor then low16")
    try:
        pair_rows = parse_table(text, PAIR_HEADER)
        getter_rows = parse_table(text, GETTER_HEADER)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    by_page = {row["id"]: row for row in pair_rows}
    for example_id in (
        "limits-ffff",
        "limits-unsorted",
        "outcome-min-failed",
        "outcome-both-failed",
    ):
        page_row = by_page.get(example_id)
        if page_row is None:
            errors.append(f"page table missing {example_id}")
            continue
        fixture_row = examples[example_id]
        projected = project(fixture_row)
        observed_min = decode_attempt(
            page_row["min_raw"].replace(" ", ""), page_row["min_read"]
        )
        observed_max = decode_attempt(
            page_row["max_raw"].replace(" ", ""), page_row["max_read"]
        )
        if scaled_cell(observed_min["scaled_u32"]) != page_row["min_scaled"]:
            errors.append(f"{example_id}: page minimum scale != unsigned LE16")
        if scaled_cell(observed_max["scaled_u32"]) != page_row["max_scaled"]:
            errors.append(f"{example_id}: page maximum scale != unsigned LE16")
        fresh = (
            observed_min["state"] == "complete" and observed_max["state"] == "complete"
        )
        if page_row["fresh_pair"] != ("true" if fresh else "false"):
            errors.append(f"{example_id}: page fresh-pair != both complete")
        if page_row["min_scaled"] != scaled_cell(projected["attempt_minimum"]["scaled_u32"]):
            errors.append(f"{example_id}: page and fixture minimum differ")
        if page_row["max_scaled"] != scaled_cell(projected["attempt_maximum"]["scaled_u32"]):
            errors.append(f"{example_id}: page and fixture maximum differ")
        if page_row["prior_min_scaled"] != scaled_cell(projected["prior_minimum"]["scaled_u32"]):
            errors.append(f"{example_id}: page prior minimum was replaced")
        if page_row["prior_max_scaled"] != scaled_cell(projected["prior_maximum"]["scaled_u32"]):
            errors.append(f"{example_id}: page prior maximum was replaced")
    getter_page = {int(row["raw_u32"]): int(row["result_u16"]) for row in getter_rows}
    for raw, result in ((655360, 0), (655359, 65535), (19, 1)):
        if getter_page.get(raw) != result or getter(raw) != result:
            errors.append(f"getter {raw} is not floor then low16")
    return errors


class ContractTests(unittest.TestCase):
    def test_owned_page_and_fixture_match_oracle(self) -> None:
        self.assertEqual(contract_errors(PAGE, FIXTURE), [])

    def test_acceptance_numbers(self) -> None:
        document = load_json(FIXTURE)
        rows = {row["id"]: row for row in document["pair_examples"]}
        limits = project(rows["limits-ffff"])
        self.assertEqual(limits["attempt_minimum"]["scaled_u32"], 10)
        self.assertEqual(limits["attempt_maximum"]["scaled_u32"], 655350)
        self.assertEqual(limits["attempt_maximum"]["state"], "complete")
        self.assertFalse(limits["ffff_sentinel"])
        self.assertTrue(limits["fresh_pair"])
        unsorted = project(rows["limits-unsorted"])
        self.assertEqual(
            (
                unsorted["attempt_minimum"]["scaled_u32"],
                unsorted["attempt_maximum"]["scaled_u32"],
            ),
            (100, 50),
        )
        partial = project(rows["outcome-min-failed"])
        self.assertEqual(partial["attempt_minimum"]["state"], "failed")
        self.assertIsNone(partial["attempt_minimum"]["scaled_u32"])
        self.assertEqual(partial["attempt_minimum"]["raw_hex"], "0100")
        self.assertEqual(partial["attempt_maximum"]["scaled_u32"], 655350)
        self.assertEqual(partial["prior_minimum"]["scaled_u32"], 20)
        self.assertEqual(partial["prior_minimum"]["raw_hex"], "0200")
        self.assertFalse(partial["fresh_pair"])
        total = project(rows["outcome-both-failed"])
        self.assertEqual(total["prior_minimum"]["scaled_u32"], 20)
        self.assertEqual(total["prior_maximum"]["scaled_u32"], 30)
        self.assertIsNone(total["attempt_minimum"]["scaled_u32"])
        self.assertIsNone(total["attempt_maximum"]["scaled_u32"])
        self.assertFalse(total["fresh_pair"])
        self.assertEqual(getter(655360), 0)
        self.assertEqual(getter(655359), 65535)
        self.assertEqual(getter(19), 1)

    def test_grades_stay_independent_of_freshness(self) -> None:
        document = load_json(FIXTURE)
        self.assertEqual(document["pair_grades"], PAIR_GRADES)
        self.assertEqual(document["getter_grades"], GETTER_GRADES)
        failed = next(
            row for row in document["pair_examples"] if row["id"] == "outcome-both-failed"
        )
        self.assertFalse(project(failed)["fresh_pair"])
        self.assertEqual(document["pair_grades"]["native"], "Unknown")
        self.assertEqual(document["pair_grades"]["numeric"], "Proven")

    def test_identity_fields_echo_one_at_a_time(self) -> None:
        """family, variant, operation and direction are separate key fields.

        Collapsing any one of them to the baseline token fails that row.
        """
        document = load_json(FIXTURE)
        rows = {row["id"]: row for row in document["pair_examples"]}
        baseline = rows[BASELINE_ID]
        expected_tokens = {
            "identity-family": ("family", "controller"),
            "identity-variant": ("variant", "alternate"),
            "identity-operation": ("operation", "OP03"),
            "identity-direction": ("direction", "reply"),
        }
        for example_id, (field, token) in expected_tokens.items():
            projected = project(rows[example_id])
            self.assertEqual(projected["selection"][field], token)
            self.assertNotEqual(projected["selection"][field], baseline["selection"][field])
            for other in SELECTION_KEYS:
                if other == field:
                    continue
                self.assertEqual(
                    projected["selection"][other], baseline["selection"][other]
                )
            self.assertEqual(input_delta(rows[example_id], baseline), {f"selection.{field}"})

    def test_word_bytes_length_and_outcome_are_separate(self) -> None:
        """Word bytes, length and read outcome each move without the others.

        Big-endian, prefix decoding, zero-padding and decode-on-failure each
        miss the oracle on one of these rows.
        """
        document = load_json(FIXTURE)
        rows = {row["id"]: row for row in document["pair_examples"]}
        self.assertEqual(project(rows["word-min-0001"])["attempt_minimum"]["scaled_u32"], 2560)
        self.assertEqual(project(rows["word-min-00ff"])["attempt_minimum"]["scaled_u32"], 652800)
        self.assertEqual(project(rows["word-max-00ff"])["attempt_maximum"]["scaled_u32"], 652800)
        self.assertEqual(project(rows["length-min-missing"])["attempt_minimum"]["state"], "missing")
        self.assertEqual(project(rows["length-min-one"])["attempt_minimum"]["state"], "malformed")
        self.assertEqual(project(rows["length-min-three"])["attempt_minimum"]["state"], "malformed")
        self.assertIsNone(project(rows["length-min-three"])["attempt_minimum"]["scaled_u32"])
        self.assertEqual(project(rows["length-max-one"])["attempt_maximum"]["state"], "malformed")
        self.assertEqual(project(rows["length-max-one"])["attempt_minimum"]["scaled_u32"], 10)
        empty_failed = project(rows["outcome-min-failed-empty"])
        self.assertEqual(empty_failed["attempt_minimum"]["state"], "failed")
        self.assertNotEqual(empty_failed["attempt_minimum"]["state"], "missing")
        self.assertEqual(project(rows["outcome-max-failed"])["attempt_minimum"]["scaled_u32"], 10)
        self.assertFalse(project(rows["outcome-max-failed"])["fresh_pair"])

    def test_prior_state_and_value_are_not_redecoded(self) -> None:
        """Prior state and prior scaled value are caller-owned fields.

        Re-decoding prior raw, or copying the new attempt into the prior,
        fails prior-min-value or prior-min-state-missing.
        """
        document = load_json(FIXTURE)
        rows = {row["id"]: row for row in document["pair_examples"]}
        kept = project(rows["prior-min-value"])
        self.assertEqual(kept["prior_minimum"]["scaled_u32"], 77)
        self.assertEqual(kept["prior_minimum"]["raw_hex"], "0200")
        self.assertEqual(kept["attempt_minimum"]["scaled_u32"], 10)
        self.assertTrue(kept["fresh_pair"])
        kept_max = project(rows["prior-max-value"])
        self.assertEqual(kept_max["prior_maximum"]["scaled_u32"], 88)
        missing = project(rows["prior-min-state-missing"])
        self.assertEqual(missing["prior_minimum"]["state"], "missing")
        self.assertEqual(missing["attempt_minimum"]["state"], "complete")
        self.assertTrue(missing["fresh_pair"])
        malformed = project(rows["prior-min-state-malformed"])
        self.assertEqual(malformed["prior_minimum"]["state"], "malformed")
        self.assertEqual(malformed["prior_minimum"]["raw_hex"], "01")
        self.assertIsNone(malformed["prior_minimum"]["scaled_u32"])
        absent_max = project(rows["prior-max-state-missing"])
        self.assertEqual(absent_max["prior_maximum"]["state"], "missing")
        self.assertEqual(absent_max["prior_minimum"]["scaled_u32"], 20)

    def test_distinct_calls_own_raw_buffers(self) -> None:
        first_min = bytearray.fromhex("0100")
        first_max = bytearray.fromhex("ffff")
        second_min = bytearray.fromhex("0a00")
        second_max = bytearray.fromhex("0500")
        first = decode_attempt(first_min, "succeeded")
        second = decode_attempt(second_min, "succeeded")
        first_maximum = decode_attempt(first_max, "succeeded")
        second_maximum = decode_attempt(second_max, "succeeded")
        first_min[0] = 0xFF
        second_min[0] = 0x00
        first_max[0] = 0x00
        second_max[0] = 0xFF
        self.assertEqual(first["raw_hex"], "0100")
        self.assertEqual(first["scaled_u32"], 10)
        self.assertEqual(second["raw_hex"], "0a00")
        self.assertEqual(second["scaled_u32"], 100)
        self.assertEqual(first_maximum["scaled_u32"], 655350)
        self.assertEqual(second_maximum["scaled_u32"], 50)
        document = load_json(FIXTURE)
        row = next(item for item in document["pair_examples"] if item["id"] == BASELINE_ID)
        left = project(row)
        right = project(row)
        left["prior_minimum"]["scaled_u32"] = 1
        left["attempt_minimum"]["raw_hex"] = "ffff"
        self.assertEqual(right["prior_minimum"]["scaled_u32"], 20)
        self.assertEqual(right["attempt_minimum"]["raw_hex"], "0100")

    def test_algorithmic_mutants_disagree_with_oracle(self) -> None:
        """Executed kills. Each mutant is a rejected reading of a fixture input."""
        document = load_json(FIXTURE)
        rows = {row["id"]: row for row in document["pair_examples"]}
        ffff = bytes.fromhex(rows["limits-ffff"]["maximum"]["raw_hex"])
        unsigned = int.from_bytes(ffff, "little", signed=False) * 10
        signed = int.from_bytes(ffff, "little", signed=True) * 10
        self.assertEqual(unsigned, 655350)
        self.assertNotEqual(signed, unsigned)
        high = bytes.fromhex(rows["word-min-00ff"]["minimum"]["raw_hex"])
        self.assertNotEqual(
            int.from_bytes(high, "little", signed=True) * 10,
            project(rows["word-min-00ff"])["attempt_minimum"]["scaled_u32"],
        )
        self.assertNotEqual(min(unsigned, 65535), unsigned)
        self.assertNotEqual((655359 & 0xFFFF) // 10, getter(655359))
        self.assertNotEqual(min(655360 // 10, 65535), getter(655360))
        self.assertNotEqual(((19 + 5) // 10) & 0xFFFF, getter(19))
        self.assertNotEqual(tuple(sorted((100, 50))), (100, 50))
        partial = project(rows["outcome-min-failed"])
        prior_both_complete = (
            partial["prior_minimum"]["state"] == "complete"
            and partial["prior_maximum"]["state"] == "complete"
        )
        self.assertTrue(prior_both_complete)
        self.assertFalse(partial["fresh_pair"])
        self.assertNotEqual("unavailable", partial["attempt_maximum"]["state"])


def _reject(testcase: unittest.TestCase, mutator) -> None:
    temp_root = os.environ.get("TMPDIR") or None
    with tempfile.TemporaryDirectory(dir=temp_root) as tmp:
        directory = Path(tmp)
        page = directory / "page.md"
        fixture = directory / "fixture.json"
        page.write_text(PAGE.read_text(encoding="utf-8"), encoding="utf-8")
        fixture.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
        mutator(page, fixture)
        errors = contract_errors(page, fixture)
        testcase.assertTrue(errors)


class FileMutationTests(unittest.TestCase):
    def test_reject_signed16_policy(self) -> None:
        def mutate(page: Path, fixture: Path) -> None:
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    '"decode": "unsigned_le16"', '"decode": "signed16"'
                ),
                encoding="utf-8",
            )
            fixture.write_text(
                fixture.read_text(encoding="utf-8").replace(
                    '"decode": "unsigned_le16"', '"decode": "signed16"', 1
                ),
                encoding="utf-8",
            )

        _reject(self, mutate)

    def test_reject_saturation_at_65535(self) -> None:
        def mutate(page: Path, fixture: Path) -> None:
            text = fixture.read_text(encoding="utf-8").replace(
                '"scaled_u32": 655350', '"scaled_u32": 65535', 1
            )
            fixture.write_text(text, encoding="utf-8")
            page.write_text(
                page.read_text(encoding="utf-8").replace("| 10 | 655350 | true |", "| 10 | 65535 | true |", 1),
                encoding="utf-8",
            )

        _reject(self, mutate)

    def test_reject_narrowing_before_dividing(self) -> None:
        def mutate(page: Path, fixture: Path) -> None:
            fixture.write_text(
                fixture.read_text(encoding="utf-8").replace(
                    '{"id": "getter-655359", "raw_u32": 655359, "result_u16": 65535}',
                    '{"id": "getter-655359", "raw_u32": 655359, "result_u16": 6553}',
                ),
                encoding="utf-8",
            )
            page.write_text(
                page.read_text(encoding="utf-8").replace("| 655359 | 65535 |", "| 655359 | 6553 |"),
                encoding="utf-8",
            )

        _reject(self, mutate)

    def test_reject_rounding_19_to_2(self) -> None:
        def mutate(page: Path, fixture: Path) -> None:
            fixture.write_text(
                fixture.read_text(encoding="utf-8").replace(
                    '{"id": "getter-19", "raw_u32": 19, "result_u16": 1}',
                    '{"id": "getter-19", "raw_u32": 19, "result_u16": 2}',
                ),
                encoding="utf-8",
            )
            page.write_text(
                page.read_text(encoding="utf-8").replace("| 19 | 1 |", "| 19 | 2 |"),
                encoding="utf-8",
            )

        _reject(self, mutate)

    def test_reject_ffff_unavailable(self) -> None:
        def mutate(page: Path, fixture: Path) -> None:
            document = load_json(fixture)
            for row in document["pair_examples"]:
                if row["id"] == "limits-ffff":
                    row["expect"]["attempt_maximum"] = {
                        "raw_hex": "ffff",
                        "state": "unavailable",
                        "scaled_u32": None,
                    }
                    row["expect"]["fresh_pair"] = False
                    row["expect"]["ffff_sentinel"] = True
            fixture.write_text(json.dumps(document), encoding="utf-8")
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    "FFFF has no qualified sentinel", "FFFF is unavailable"
                ),
                encoding="utf-8",
            )

        _reject(self, mutate)

    def test_reject_min_max_sorting(self) -> None:
        def mutate(page: Path, fixture: Path) -> None:
            document = load_json(fixture)
            for row in document["pair_examples"]:
                if row["id"] == "limits-unsorted":
                    row["expect"]["attempt_minimum"]["scaled_u32"] = 50
                    row["expect"]["attempt_maximum"]["scaled_u32"] = 100
            fixture.write_text(json.dumps(document), encoding="utf-8")
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    "| 100 | 50 | true |", "| 50 | 100 | true |"
                ),
                encoding="utf-8",
            )

        _reject(self, mutate)

    def test_reject_promoting_retained_limits_to_fresh(self) -> None:
        def mutate(page: Path, fixture: Path) -> None:
            document = load_json(fixture)
            for row in document["pair_examples"]:
                if row["id"] == "outcome-min-failed":
                    row["expect"]["fresh_pair"] = True
            fixture.write_text(json.dumps(document), encoding="utf-8")
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    "| absent | 655350 | false | 20 | 30 |",
                    "| absent | 655350 | true | 20 | 30 |",
                ),
                encoding="utf-8",
            )

        _reject(self, mutate)


if __name__ == "__main__":
    unittest.main()
