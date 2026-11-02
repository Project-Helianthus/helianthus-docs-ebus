"""Oracle for the AN22 local B555 integer64 and float64 narrowing contract.

The conversion below is the software contract under test. It is not a device
operation and it does not qualify a native timer value. Nonfinite operands are
built at runtime. Published files store only finite literals.

Identity fields, and the production mutation each comparison catches:

- timer_kind_token: the echoed token is replaced with the family token.
- family: an absent family is replaced with a concrete device family.
- software_variant: a supplied variant is dropped.
- selected_path: an integer64 result is relabeled float64.
- caller_state.module_token: a module token is invented when caller state is absent.
- caller_state.group_token: the group token is copied from the module token.
- caller_state.instance_token: the instance token is copied from the group token.
- caller_state.day_token: the day token is copied from the instance token.
- caller_state.constructor_token: a constructor token is invented when caller state is absent.
- caller_state.request_token: the request token is copied from the constructor token.
"""

from __future__ import annotations

import copy
import json
import math
import re
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "architecture" / "an22_b555_numeric_narrowing.md"
FIXTURE = ROOT / "architecture" / "fixtures" / "an22_b555_numeric_narrowing.json"

INT64_MIN = -9223372036854775808
INT64_MAX = 9223372036854775807
UINT32_MAX = 4294967295

INTEGER_STAGES = ["low16"]
FLOAT_STAGES = [
    "binary32-round-trip",
    "widen-to-float64",
    "multiply-by-10",
    "truncate-toward-zero-uint32",
    "low16",
]
FORBIDDEN = [
    "skip-binary32",
    "round-instead-of-truncate",
    "saturate-instead-of-low16",
    "merge-integer-and-float",
    "admit-negative-nonfinite-overflow",
]
RAW_CLASSES = [
    "negative",
    "nan",
    "infinite",
    "overflow",
    "malformed_operand",
]

_INT_LITERAL = re.compile(r"^-?(?:0|[1-9]\d*)$")
_FLOAT_LITERAL = re.compile(r"^-?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_LINK = re.compile(r"\]\(([^)\s]+)\)")
_HEX_FINGERPRINT = re.compile(r"\b[0-9a-fA-F]{40}\b|\b[0-9a-fA-F]{64}\b")

REQUIRED_SENTENCES = (
    "narrowInteger64 and narrowFloat64 are separate helpers.",
    "The integer64 helper keeps the low 16 bits and does not apply a binary32 conversion.",
    "The float64 helper converts float64 to IEEE binary32, widens that value to float64, multiplies by 10, truncates toward zero into uint32, then keeps the low 16 bits.",
    "Bypassing the binary32 round-trip for 0.7 yields the wrong carrier 7; the helper returns 6.",
    "The operand 1.25 yields carrier 12, not the half-away rounding 13.",
    "The operand 6553.6 yields low 16 carrier 0.",
    "The operand 65537 yields carrier 1.",
    "The operand -1 yields carrier 65535.",
    "The operand 0 yields carrier 0.",
    "Negative, NaN, infinite, and overflowing scaled operands are unresolved and have no carrier.",
    "A missing family stays missing and does not become a qualified native family.",
    "The helper does not select a module, group, instance, day, or native constructor.",
    "No blanket generic encoder, setter, control state, or runtime registration is added.",
    "Existing A3, A4, A5, and A6 typed methods stay untouched.",
    "Units, timer-kind effects, physical persistence, availability, count materialization, and write admission stay Unknown.",
    "This page does not qualify a physical timer value.",
    "Nothing in this contract is stable before Helianthus 1.0.",
)


def to_binary32(value: float) -> float:
    """IEEE binary32 roundTiesToEven, overflowing to a signed infinity."""

    try:
        packed = struct.pack("<f", value)
    except OverflowError:
        return math.copysign(math.inf, value)
    return struct.unpack("<f", packed)[0]


def raw_f64(value: float) -> list[int]:
    return list(struct.pack("<d", value))


def raw_f32(value: float) -> list[int]:
    return list(struct.pack("<f", value))


def raw_i64(value: int) -> list[int]:
    return list((value & ((1 << 64) - 1)).to_bytes(8, "little"))


def raw_low16(value: int) -> list[int]:
    masked = value & 0xFFFF
    return [masked & 0xFF, (masked >> 8) & 0xFF]


def parse_int_literal(literal: str):
    if not isinstance(literal, str) or _INT_LITERAL.fullmatch(literal) is None:
        return None
    value = int(literal)
    if value < INT64_MIN or value > INT64_MAX:
        return None
    return value


def parse_float_literal(literal: str):
    if not isinstance(literal, str) or _FLOAT_LITERAL.fullmatch(literal) is None:
        return None
    value = float(literal)
    if not math.isfinite(value):
        return None
    return value


def _grades(numeric: str, semantic: str) -> dict[str, str]:
    return {"numeric": numeric, "semantic": semantic, "native": "Unknown"}


def _echo(path: str, context: dict) -> dict:
    return {
        "selected_path": path,
        "timer_kind_token": context.get("timer_kind_token"),
        "family": context.get("family"),
        "software_variant": context.get("software_variant"),
        "caller_state": copy.deepcopy(context.get("caller_state")),
        "selects_module": False,
        "selects_group": False,
        "selects_instance": False,
        "selects_day": False,
        "selects_native_constructor": False,
        "native_family_qualified": False,
    }


def _blank_numeric() -> dict:
    return {
        "carrier_low16": None,
        "carrier_raw_le": None,
        "original_literal": None,
        "original_raw_le": None,
        "rounded_literal": None,
        "rounded_raw_le": None,
        "scaled_literal": None,
        "truncated_uint32": None,
        "raw_classification": None,
    }


def _integer_stages(low16: str, rejected_at):
    return {
        "binary32_round_trip": "not_applicable",
        "widen_to_float64": "not_applicable",
        "multiply_by_10": "not_applicable",
        "truncate_toward_zero_uint32": "not_applicable",
        "low16": low16,
        "rejected_at": rejected_at,
    }


def _float_stages(binary32: str, widen: str, multiply: str, truncate: str, low16: str, rejected_at):
    return {
        "binary32_round_trip": binary32,
        "widen_to_float64": widen,
        "multiply_by_10": multiply,
        "truncate_toward_zero_uint32": truncate,
        "low16": low16,
        "rejected_at": rejected_at,
    }


def narrow_integer64(literal: str, context: dict) -> dict:
    result = _echo("integer64", context)
    result.update(_blank_numeric())
    value = parse_int_literal(literal)
    if value is None:
        result["disposition"] = "malformed"
        result["raw_classification"] = "malformed_operand"
        result["grades"] = _grades("Unknown", "Unknown")
        result["intermediate_status"] = _integer_stages("not_applied", "operand")
        return result
    carrier = value & 0xFFFF
    result["disposition"] = "resolved"
    result["carrier_low16"] = carrier
    result["carrier_raw_le"] = raw_low16(carrier)
    result["original_literal"] = str(value)
    result["original_raw_le"] = raw_i64(value)
    result["grades"] = _grades("Proven", "Hypothesis")
    result["intermediate_status"] = _integer_stages("applied", None)
    return result


def _float_rejected(result: dict, value: float, classification: str) -> dict:
    rounded = to_binary32(value)
    scaled = rounded * 10.0
    result["disposition"] = "unresolved"
    result["raw_classification"] = classification
    result["original_literal"] = repr(value)
    result["original_raw_le"] = raw_f64(value)
    result["rounded_raw_le"] = raw_f32(rounded)
    result["rounded_literal"] = None if not math.isfinite(rounded) else repr(rounded)
    result["scaled_literal"] = None if not math.isfinite(scaled) else repr(scaled)
    result["grades"] = _grades("Unknown", "Unknown")
    result["intermediate_status"] = _float_stages(
        "applied", "applied", "applied", "not_applied", "not_applied", "domain"
    )
    return result


def narrow_float64_value(value: float, context: dict) -> dict:
    result = _echo("float64", context)
    result.update(_blank_numeric())
    if math.isnan(value):
        return _float_rejected(result, value, "nan")
    if math.isinf(value):
        return _float_rejected(result, value, "infinite")
    if value < 0:
        return _float_rejected(result, value, "negative")
    rounded = to_binary32(value)
    scaled = rounded * 10.0
    if (not math.isfinite(scaled)) or scaled < 0 or scaled > UINT32_MAX:
        return _float_rejected(result, value, "overflow")
    truncated = math.trunc(scaled)
    carrier = truncated & 0xFFFF
    result["disposition"] = "resolved"
    result["carrier_low16"] = carrier
    result["carrier_raw_le"] = raw_low16(carrier)
    result["original_literal"] = repr(value)
    result["original_raw_le"] = raw_f64(value)
    result["rounded_literal"] = repr(rounded)
    result["rounded_raw_le"] = raw_f32(rounded)
    result["scaled_literal"] = repr(scaled)
    result["truncated_uint32"] = truncated
    result["grades"] = _grades("Proven", "Hypothesis")
    result["intermediate_status"] = _float_stages(
        "applied", "applied", "applied", "applied", "applied", None
    )
    return result


def narrow_float64(literal: str, context: dict) -> dict:
    value = parse_float_literal(literal)
    if value is None:
        result = _echo("float64", context)
        result.update(_blank_numeric())
        result["disposition"] = "malformed"
        result["raw_classification"] = "malformed_operand"
        result["grades"] = _grades("Unknown", "Unknown")
        result["intermediate_status"] = _float_stages(
            "not_applied", "not_applied", "not_applied", "not_applied", "not_applied", "operand"
        )
        return result
    return narrow_float64_value(value, context)


def evaluate(path: str, literal: str, context: dict) -> dict:
    if path == "integer64":
        return narrow_integer64(literal, context)
    if path == "float64":
        return narrow_float64(literal, context)
    raise AssertionError(path)


def context_for(
    index: int,
    *,
    timer: bool = True,
    family: bool = True,
    variant: bool = True,
    caller: bool = True,
    empty_family: bool = False,
) -> dict:
    def token(prefix: str) -> str:
        return f"{prefix}-{index}"

    if empty_family:
        family_token = ""
    elif family:
        family_token = token("device-family")
    else:
        family_token = None
    caller_state = None
    if caller:
        caller_state = {
            "module_token": token("caller-module"),
            "group_token": token("caller-group"),
            "instance_token": token("caller-instance"),
            "day_token": token("caller-day"),
            "constructor_token": token("caller-constructor"),
            "request_token": token("caller-request"),
        }
    return {
        "timer_kind_token": token("timer-kind") if timer else None,
        "family": family_token,
        "software_variant": token("software-variant") if variant else None,
        "caller_state": caller_state,
    }


def example_specs() -> list[dict]:
    rows = [
        ("integer-zero", "integer64", "0", context_for(1)),
        ("integer-65537", "integer64", "65537", context_for(2)),
        ("integer-neg-one", "integer64", "-1", context_for(3)),
        ("integer-65536", "integer64", "65536", context_for(4)),
        ("integer-neg-65536", "integer64", "-65536", context_for(5)),
        ("integer-int64-max", "integer64", str(INT64_MAX), context_for(6)),
        ("integer-int64-min", "integer64", str(INT64_MIN), context_for(7)),
        ("integer-missing-family", "integer64", "3", context_for(8, family=False)),
        (
            "integer-missing-all-context",
            "integer64",
            "65537",
            context_for(9, timer=False, family=False, variant=False, caller=False),
        ),
        ("integer-empty-family", "integer64", "4", context_for(10, empty_family=True)),
        ("integer-malformed-fraction", "integer64", "3.5", context_for(11)),
        ("integer-malformed-above-int64", "integer64", "9223372036854775808", context_for(12)),
        ("integer-malformed-below-int64", "integer64", "-9223372036854775809", context_for(13)),
        ("float-zero", "float64", "0.0", context_for(14)),
        ("float-signed-zero", "float64", "-0.0", context_for(15)),
        ("float-0-7", "float64", "0.7", context_for(16)),
        ("float-1-25", "float64", "1.25", context_for(17)),
        ("float-6553-6", "float64", "6553.6", context_for(18)),
        ("float-0-05", "float64", "0.05", context_for(19)),
        ("float-0-25", "float64", "0.25", context_for(20)),
        ("float-tie-below", "float64", "0.7000000178813933", context_for(21)),
        ("float-tie-mid-to-even-up", "float64", "0.7000000178813934", context_for(22)),
        ("float-tie-above", "float64", "0.7000000178813935", context_for(23)),
        ("float-tie-mid-to-even-down", "float64", "0.7999999821186066", context_for(24)),
        ("float-tie-above-even-down", "float64", "0.7999999821186067", context_for(25)),
        ("float-domain-max", "float64", "429496704.0", context_for(26)),
        ("float-domain-tie-inside", "float64", "429496720.0", context_for(27)),
        ("float-domain-just-outside", "float64", "429496720.00000006", context_for(28)),
        ("float-overflow-429496729-5", "float64", "429496729.5", context_for(29)),
        ("float-overflow-scaled-finite", "float64", "429496736.0", context_for(30)),
        ("float-overflow-binary32", "float64", "1e39", context_for(31)),
        ("float-negative-0-1", "float64", "-0.1", context_for(32)),
        ("float-negative-one", "float64", "-1.0", context_for(33)),
        ("float-negative-6553-6", "float64", "-6553.6", context_for(34)),
        ("float-negative-tiny", "float64", "-5e-324", context_for(35)),
        ("float-negative-huge", "float64", "-1e39", context_for(36)),
        ("float-missing-timer", "float64", "1.25", context_for(37, timer=False)),
        ("float-missing-variant", "float64", "0.7", context_for(38, variant=False)),
        ("float-malformed-text", "float64", "not-a-number", context_for(39)),
        ("float-malformed-blank", "float64", "", context_for(40)),
    ]
    return [
        {"id": name, "path": path, "operand_literal": literal, "context": context}
        for name, path, literal, context in rows
    ]


def published_document() -> dict:
    examples = []
    for spec in example_specs():
        item = copy.deepcopy(spec)
        item["expect"] = evaluate(spec["path"], spec["operand_literal"], spec["context"])
        examples.append(item)
    return {
        "schema_name": "an22-b555-numeric-narrowing-examples",
        "helper_api": "ab21an21",
        "functions": ["narrowInteger64", "narrowFloat64"],
        "integer64_stages": INTEGER_STAGES,
        "float64_stages": FLOAT_STAGES,
        "forbidden": FORBIDDEN,
        "raw_classes": RAW_CLASSES,
        "admit_negative": False,
        "admit_nonfinite": False,
        "admit_overflow": False,
        "merge_paths": False,
        "saturate_low16": False,
        "skip_binary32": False,
        "round_instead_of_truncate": False,
        "examples": examples,
    }


def markdown_table(document: dict | None = None) -> str:
    document = published_document() if document is None else document
    lines = [
        "| id | path | operand | disposition | carrier_low16 | raw_classification | numeric | semantic | native |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for example in document["examples"]:
        expect = example["expect"]
        carrier = "none" if expect["carrier_low16"] is None else str(expect["carrier_low16"])
        raw = "none" if expect["raw_classification"] is None else expect["raw_classification"]
        grades = expect["grades"]
        lines.append(
            "| {id} | {path} | {operand} | {disposition} | {carrier} | {raw} | {numeric} | {semantic} | {native} |".format(
                id=example["id"],
                path=example["path"],
                operand=example["operand_literal"],
                disposition=expect["disposition"],
                carrier=carrier,
                raw=raw,
                numeric=grades["numeric"],
                semantic=grades["semantic"],
                native=grades["native"],
            )
        )
    return "\n".join(lines)


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def parse_page_table(page: str) -> list[dict[str, str]]:
    rows = []
    for line in page.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] in {"id", "---"} or set(cells[0]) == {"-"}:
            continue
        if len(cells) != 9:
            raise AssertionError(line)
        rows.append(
            {
                "id": cells[0],
                "path": cells[1],
                "operand": cells[2],
                "disposition": cells[3],
                "carrier_low16": cells[4],
                "raw_classification": cells[5],
                "numeric": cells[6],
                "semantic": cells[7],
                "native": cells[8],
            }
        )
    return rows


def token_map(page: str) -> dict[str, str]:
    found = {}
    for line in page.splitlines():
        if ": " not in line or line.startswith("|") or line.startswith("#"):
            continue
        key, value = line.split(": ", 1)
        if re.fullmatch(r"[a-z0-9-]+", key):
            found[key] = value.strip()
    return found


class An22B555NumericNarrowingTest(unittest.TestCase):
    def test_policy_flags_reject_forbidden_algorithms(self) -> None:
        document = load_fixture()
        self.assertEqual(document["helper_api"], "ab21an21")
        self.assertEqual(document["functions"], ["narrowInteger64", "narrowFloat64"])
        self.assertEqual(document["integer64_stages"], INTEGER_STAGES)
        self.assertEqual(document["float64_stages"], FLOAT_STAGES)
        self.assertEqual(document["forbidden"], FORBIDDEN)
        self.assertEqual(document["raw_classes"], RAW_CLASSES)
        self.assertIs(document["admit_negative"], False)
        self.assertIs(document["admit_nonfinite"], False)
        self.assertIs(document["admit_overflow"], False)
        self.assertIs(document["merge_paths"], False)
        self.assertIs(document["saturate_low16"], False)
        self.assertIs(document["skip_binary32"], False)
        self.assertIs(document["round_instead_of_truncate"], False)
        self.assertLess(FLOAT_STAGES.index("binary32-round-trip"), FLOAT_STAGES.index("multiply-by-10"))
        self.assertLess(FLOAT_STAGES.index("multiply-by-10"), FLOAT_STAGES.index("truncate-toward-zero-uint32"))
        self.assertNotIn("binary32-round-trip", document["integer64_stages"])

    def test_examples_match_independent_conversion(self) -> None:
        document = load_fixture()
        specs = example_specs()
        self.assertEqual(
            [
                {
                    "id": example["id"],
                    "path": example["path"],
                    "operand_literal": example["operand_literal"],
                    "context": example["context"],
                }
                for example in document["examples"]
            ],
            specs,
        )
        self.assertGreaterEqual(len(document["examples"]), 16)
        for example in document["examples"]:
            expect = evaluate(example["path"], example["operand_literal"], example["context"])
            self.assertEqual(example["expect"], expect)
            self.assertIs(example["expect"]["native_family_qualified"], False)
            self.assertFalse(example["expect"]["selects_module"])
            self.assertFalse(example["expect"]["selects_group"])
            self.assertFalse(example["expect"]["selects_instance"])
            self.assertFalse(example["expect"]["selects_day"])
            self.assertFalse(example["expect"]["selects_native_constructor"])

    def test_required_numeric_counterexamples(self) -> None:
        by_id = {example["id"]: example for example in load_fixture()["examples"]}
        integer_one = by_id["integer-65537"]["expect"]
        self.assertEqual(integer_one["carrier_low16"], 1)
        self.assertEqual(integer_one["carrier_raw_le"], [1, 0])
        self.assertNotEqual(integer_one["carrier_low16"], 65535)
        negative = by_id["integer-neg-one"]["expect"]
        self.assertEqual(negative["carrier_low16"], 65535)
        self.assertNotEqual(negative["carrier_low16"], 0)
        zero = by_id["integer-zero"]["expect"]
        self.assertEqual(zero["carrier_low16"], 0)
        self.assertEqual(by_id["float-zero"]["expect"]["carrier_low16"], 0)
        seven = by_id["float-0-7"]["expect"]
        self.assertEqual(seven["carrier_low16"], 6)
        self.assertLess(float(seven["rounded_literal"]), 0.7)
        self.assertEqual(math.trunc(0.7 * 10.0), 7)
        self.assertEqual(math.trunc(float(seven["rounded_literal"]) * 10.0), 6)
        self.assertNotEqual(seven["carrier_low16"], math.trunc(0.7 * 10.0))
        one_two_five = by_id["float-1-25"]["expect"]
        self.assertEqual(one_two_five["scaled_literal"], "12.5")
        self.assertEqual(one_two_five["truncated_uint32"], 12)
        self.assertEqual(one_two_five["carrier_low16"], 12)
        self.assertEqual(math.floor(12.5 + 0.5), 13)
        self.assertNotEqual(one_two_five["carrier_low16"], 13)
        wrapped = by_id["float-6553-6"]["expect"]
        self.assertEqual(wrapped["truncated_uint32"], 65536)
        self.assertEqual(wrapped["carrier_low16"], 0)
        self.assertNotEqual(wrapped["carrier_low16"], 65535)
        self.assertGreater(float(wrapped["rounded_literal"]), 6553.6)

    def test_rounding_boundaries_and_domain_edges(self) -> None:
        by_id = {example["id"]: example for example in load_fixture()["examples"]}
        self.assertEqual(repr(float("0.7000000178813934")), "0.7000000178813934")
        self.assertEqual(repr(float("429496720.00000006")), "429496720.00000006")
        below = by_id["float-tie-below"]["expect"]
        mid_up = by_id["float-tie-mid-to-even-up"]["expect"]
        above = by_id["float-tie-above"]["expect"]
        self.assertEqual(below["carrier_low16"], 6)
        self.assertEqual(mid_up["carrier_low16"], 7)
        self.assertEqual(above["carrier_low16"], 7)
        self.assertEqual(mid_up["rounded_literal"], "0.7000000476837158")
        self.assertNotEqual(below["rounded_literal"], mid_up["rounded_literal"])
        even_down = by_id["float-tie-mid-to-even-down"]["expect"]
        even_above = by_id["float-tie-above-even-down"]["expect"]
        self.assertEqual(even_down["carrier_low16"], 7)
        self.assertEqual(even_above["carrier_low16"], 8)
        self.assertEqual(by_id["float-0-25"]["expect"]["carrier_low16"], 2)
        self.assertEqual(math.floor(2.5 + 0.5), 3)
        self.assertEqual(by_id["float-0-05"]["expect"]["carrier_low16"], 0)
        self.assertNotEqual(by_id["float-0-05"]["expect"]["original_literal"], "0.0")
        signed = by_id["float-signed-zero"]["expect"]
        self.assertEqual(signed["disposition"], "resolved")
        self.assertEqual(signed["carrier_low16"], 0)
        self.assertEqual(signed["original_literal"], "-0.0")
        self.assertEqual(signed["original_raw_le"][7] & 0x80, 0x80)
        self.assertEqual(by_id["float-domain-max"]["expect"]["truncated_uint32"], 4294967040)
        self.assertEqual(by_id["float-domain-max"]["expect"]["carrier_low16"], 65280)
        self.assertEqual(by_id["float-domain-tie-inside"]["expect"]["disposition"], "resolved")
        outside = by_id["float-domain-just-outside"]["expect"]
        self.assertEqual(outside["raw_classification"], "overflow")
        self.assertIsNone(outside["carrier_low16"])
        self.assertEqual(outside["grades"]["numeric"], "Unknown")
        bypass = by_id["float-overflow-429496729-5"]["expect"]
        self.assertEqual(bypass["raw_classification"], "overflow")
        self.assertIsNone(bypass["carrier_low16"])
        self.assertNotEqual(bypass["carrier_low16"], math.trunc(429496729.5 * 10.0) & 0xFFFF)
        self.assertEqual(by_id["float-overflow-scaled-finite"]["expect"]["raw_classification"], "overflow")
        self.assertTrue(math.isfinite(float(by_id["float-overflow-scaled-finite"]["expect"]["scaled_literal"])))
        self.assertGreater(float(by_id["float-overflow-scaled-finite"]["expect"]["scaled_literal"]), UINT32_MAX)

    def test_invalid_classes_have_no_qualified_carrier(self) -> None:
        by_id = {example["id"]: example for example in load_fixture()["examples"]}
        negative_ids = [
            "float-negative-0-1",
            "float-negative-one",
            "float-negative-6553-6",
            "float-negative-tiny",
            "float-negative-huge",
        ]
        overflow_ids = [
            "float-domain-just-outside",
            "float-overflow-429496729-5",
            "float-overflow-scaled-finite",
            "float-overflow-binary32",
        ]
        for name in negative_ids:
            expect = by_id[name]["expect"]
            self.assertEqual(expect["raw_classification"], "negative")
            self.assertIsNone(expect["carrier_low16"])
            self.assertEqual(expect["grades"]["numeric"], "Unknown")
            self.assertNotEqual(expect["grades"]["numeric"], "Proven")
        tiny = by_id["float-negative-tiny"]["expect"]
        self.assertLess(float(tiny["original_literal"]), 0)
        self.assertEqual(tiny["rounded_literal"], "-0.0")
        huge = by_id["float-negative-huge"]["expect"]
        self.assertIsNone(huge["scaled_literal"])
        self.assertTrue(math.isinf(struct.unpack("<f", bytes(huge["rounded_raw_le"]))[0]))
        for name in overflow_ids:
            expect = by_id[name]["expect"]
            self.assertEqual(expect["raw_classification"], "overflow")
            self.assertIsNone(expect["carrier_low16"])
            self.assertIsNone(expect["truncated_uint32"])
            self.assertEqual(expect["grades"]["numeric"], "Unknown")
        binary32_overflow = by_id["float-overflow-binary32"]["expect"]
        self.assertNotEqual(binary32_overflow["raw_classification"], "infinite")
        self.assertIsNone(binary32_overflow["rounded_literal"])
        self.assertNotEqual(by_id["integer-65536"]["expect"]["carrier_low16"], 65535)
        self.assertEqual(by_id["integer-65536"]["expect"]["carrier_low16"], 0)
        self.assertEqual(by_id["integer-neg-65536"]["expect"]["carrier_low16"], 0)
        self.assertEqual(by_id["integer-int64-max"]["expect"]["carrier_low16"], 65535)
        self.assertEqual(by_id["integer-int64-min"]["expect"]["carrier_low16"], 0)

    def test_nonfinite_operands_are_computed_at_runtime(self) -> None:
        raw = FIXTURE.read_text(encoding="utf-8")
        self.assertNotIn("NaN", raw)
        self.assertNotIn("Infinity", raw)
        contexts = [
            context_for(51),
            context_for(52),
            context_for(53),
            context_for(54),
        ]
        cases = [
            (float("nan"), "nan", contexts[0]),
            (float("inf"), "infinite", contexts[1]),
            (float("-inf"), "infinite", contexts[2]),
            (math.nextafter(float("inf"), 0.0), "overflow", contexts[3]),
        ]
        seen_timers = set()
        for value, classification, context in cases:
            got = narrow_float64_value(value, context)
            self.assertEqual(got["raw_classification"], classification)
            self.assertEqual(got["disposition"], "unresolved")
            self.assertIsNone(got["carrier_low16"])
            self.assertIsNone(got["carrier_raw_le"])
            self.assertIsNone(got["truncated_uint32"])
            self.assertEqual(got["grades"]["numeric"], "Unknown")
            self.assertEqual(got["grades"]["semantic"], "Unknown")
            self.assertEqual(got["grades"]["native"], "Unknown")
            self.assertEqual(got["timer_kind_token"], context["timer_kind_token"])
            self.assertEqual(got["family"], context["family"])
            self.assertEqual(got["software_variant"], context["software_variant"])
            self.assertEqual(got["caller_state"], context["caller_state"])
            self.assertEqual(got["original_raw_le"], raw_f64(value))
            self.assertEqual(got["intermediate_status"]["low16"], "not_applied")
            seen_timers.add(context["timer_kind_token"])
        self.assertEqual(len(seen_timers), 4)
        positive = narrow_float64_value(float("inf"), contexts[1])
        negative = narrow_float64_value(float("-inf"), contexts[2])
        self.assertNotEqual(positive["original_raw_le"], negative["original_raw_le"])
        self.assertEqual(positive["original_raw_le"][7] & 0x80, 0)
        self.assertEqual(negative["original_raw_le"][7] & 0x80, 0x80)
        self.assertNotEqual(positive["family"], negative["family"])

    def test_paths_stay_separate(self) -> None:
        by_id = {example["id"]: example for example in load_fixture()["examples"]}
        integer_negative = by_id["integer-neg-one"]["expect"]
        float_negative = by_id["float-negative-one"]["expect"]
        self.assertEqual(integer_negative["selected_path"], "integer64")
        self.assertEqual(float_negative["selected_path"], "float64")
        self.assertEqual(integer_negative["carrier_low16"], 65535)
        self.assertIsNone(float_negative["carrier_low16"])
        self.assertEqual(float_negative["raw_classification"], "negative")
        self.assertEqual(integer_negative["intermediate_status"]["binary32_round_trip"], "not_applicable")
        self.assertEqual(float_negative["intermediate_status"]["binary32_round_trip"], "applied")
        self.assertEqual(by_id["float-0-7"]["expect"]["intermediate_status"]["binary32_round_trip"], "applied")
        self.assertEqual(by_id["integer-65537"]["expect"]["intermediate_status"]["multiply_by_10"], "not_applicable")
        self.assertEqual(integer_negative["original_raw_le"], raw_i64(-1))
        self.assertEqual(float_negative["original_raw_le"], raw_f64(-1.0))
        self.assertNotEqual(integer_negative["original_raw_le"], float_negative["original_raw_le"])

    def test_missing_context_does_not_qualify_a_family(self) -> None:
        by_id = {example["id"]: example for example in load_fixture()["examples"]}
        missing_family = by_id["integer-missing-family"]["expect"]
        self.assertIsNone(missing_family["family"])
        self.assertEqual(missing_family["carrier_low16"], 3)
        self.assertEqual(missing_family["grades"]["numeric"], "Proven")
        self.assertEqual(missing_family["grades"]["semantic"], "Hypothesis")
        self.assertEqual(missing_family["grades"]["native"], "Unknown")
        self.assertIs(missing_family["native_family_qualified"], False)
        absent = by_id["integer-missing-all-context"]["expect"]
        self.assertIsNone(absent["timer_kind_token"])
        self.assertIsNone(absent["family"])
        self.assertIsNone(absent["software_variant"])
        self.assertIsNone(absent["caller_state"])
        self.assertEqual(absent["carrier_low16"], 1)
        self.assertEqual(absent["grades"]["native"], "Unknown")
        empty = by_id["integer-empty-family"]["expect"]
        self.assertEqual(empty["family"], "")
        self.assertIs(empty["native_family_qualified"], False)
        self.assertEqual(empty["grades"]["native"], "Unknown")
        self.assertNotEqual(empty["grades"]["semantic"], "Proven")
        missing_timer = by_id["float-missing-timer"]["expect"]
        self.assertIsNone(missing_timer["timer_kind_token"])
        self.assertEqual(missing_timer["carrier_low16"], 12)
        self.assertNotEqual(missing_timer["family"], "")
        missing_variant = by_id["float-missing-variant"]["expect"]
        self.assertIsNone(missing_variant["software_variant"])
        self.assertEqual(missing_variant["carrier_low16"], 6)

    def test_malformed_operands_fail_closed(self) -> None:
        by_id = {example["id"]: example for example in load_fixture()["examples"]}
        for name in (
            "integer-malformed-fraction",
            "integer-malformed-above-int64",
            "integer-malformed-below-int64",
            "float-malformed-text",
            "float-malformed-blank",
        ):
            expect = by_id[name]["expect"]
            source = by_id[name]
            self.assertEqual(expect["disposition"], "malformed")
            self.assertEqual(expect["raw_classification"], "malformed_operand")
            self.assertIsNone(expect["carrier_low16"])
            self.assertIsNone(expect["original_raw_le"])
            self.assertIsNone(expect["rounded_raw_le"])
            self.assertEqual(expect["grades"]["numeric"], "Unknown")
            self.assertEqual(expect["timer_kind_token"], source["context"]["timer_kind_token"])
            self.assertEqual(expect["family"], source["context"]["family"])
            self.assertEqual(expect["caller_state"], source["context"]["caller_state"])
            self.assertEqual(expect["intermediate_status"]["rejected_at"], "operand")
            self.assertEqual(expect["intermediate_status"]["low16"], "not_applied")
        self.assertEqual(
            by_id["integer-malformed-fraction"]["expect"]["intermediate_status"]["binary32_round_trip"],
            "not_applicable",
        )
        self.assertEqual(
            by_id["float-malformed-text"]["expect"]["intermediate_status"]["binary32_round_trip"],
            "not_applied",
        )

    def test_each_identity_field_catches_its_mutation(self) -> None:
        by_id = {example["id"]: example for example in load_fixture()["examples"]}
        populated = [
            example
            for example in by_id.values()
            if example["context"]["caller_state"] is not None
            and example["context"]["family"] not in (None, "")
            and example["context"]["timer_kind_token"] is not None
            and example["context"]["software_variant"] is not None
        ]
        self.assertGreaterEqual(len(populated), 2)
        timers = {example["context"]["timer_kind_token"] for example in populated}
        families = {example["context"]["family"] for example in populated}
        variants = {example["context"]["software_variant"] for example in populated}
        paths = {example["path"] for example in by_id.values()}
        self.assertGreaterEqual(len(timers), 2)
        self.assertGreaterEqual(len(families), 2)
        self.assertGreaterEqual(len(variants), 2)
        self.assertEqual(paths, {"integer64", "float64"})
        caller_values = {field: set() for field in (
            "module_token",
            "group_token",
            "instance_token",
            "day_token",
            "constructor_token",
            "request_token",
        )}
        for example in populated:
            caller = example["expect"]["caller_state"]
            self.assertEqual(len(set(caller.values())), len(caller))
            for field, token in caller.items():
                caller_values[field].add(token)
        for values in caller_values.values():
            self.assertGreaterEqual(len(values), 2)

        integer = by_id["integer-65537"]["expect"]
        self.assertNotEqual(integer["timer_kind_token"], integer["family"])
        replaced_timer = copy.deepcopy(integer)
        replaced_timer["timer_kind_token"] = replaced_timer["family"]
        self.assertNotEqual(replaced_timer, integer)

        missing = by_id["integer-missing-family"]["expect"]
        self.assertIsNone(missing["family"])
        filled_family = copy.deepcopy(missing)
        filled_family["family"] = "device-family-1"
        self.assertNotEqual(filled_family, missing)

        varied = by_id["float-0-7"]["expect"]
        self.assertNotEqual(varied["software_variant"], varied["family"])
        dropped_variant = copy.deepcopy(varied)
        dropped_variant["software_variant"] = None
        self.assertNotEqual(dropped_variant, varied)

        relabeled = copy.deepcopy(by_id["integer-neg-one"]["expect"])
        self.assertEqual(relabeled["selected_path"], "integer64")
        relabeled["selected_path"] = "float64"
        self.assertNotEqual(relabeled, by_id["integer-neg-one"]["expect"])

        absent_caller = by_id["integer-missing-all-context"]["expect"]
        self.assertIsNone(absent_caller["caller_state"])
        invented_module = copy.deepcopy(absent_caller)
        invented_module["caller_state"] = {
            "module_token": "caller-module-invented",
            "group_token": None,
            "instance_token": None,
            "day_token": None,
            "constructor_token": None,
            "request_token": None,
        }
        self.assertNotEqual(invented_module, absent_caller)
        invented_constructor = copy.deepcopy(absent_caller)
        invented_constructor["caller_state"] = {
            "module_token": None,
            "group_token": None,
            "instance_token": None,
            "day_token": None,
            "constructor_token": "caller-constructor-invented",
            "request_token": None,
        }
        self.assertNotEqual(invented_constructor, absent_caller)

        caller = copy.deepcopy(varied)
        self.assertNotEqual(caller["caller_state"]["group_token"], caller["caller_state"]["module_token"])
        caller["caller_state"]["group_token"] = caller["caller_state"]["module_token"]
        self.assertNotEqual(caller, varied)
        caller = copy.deepcopy(varied)
        caller["caller_state"]["instance_token"] = caller["caller_state"]["group_token"]
        self.assertNotEqual(caller, varied)
        caller = copy.deepcopy(varied)
        caller["caller_state"]["day_token"] = caller["caller_state"]["instance_token"]
        self.assertNotEqual(caller, varied)
        caller = copy.deepcopy(varied)
        caller["caller_state"]["request_token"] = caller["caller_state"]["constructor_token"]
        self.assertNotEqual(caller, varied)

    def test_page_states_the_contract_and_forbids_the_wrong_algorithms(self) -> None:
        page = PAGE.read_text(encoding="utf-8")
        for sentence in REQUIRED_SENTENCES:
            self.assertIn(sentence, page)
        tokens = token_map(page)
        self.assertEqual(tokens["integer64-stages"], "low16")
        self.assertEqual(
            tokens["float64-stages"],
            "binary32-round-trip | widen-to-float64 | multiply-by-10 | truncate-toward-zero-uint32 | low16",
        )
        self.assertEqual(
            tokens["forbidden"],
            "skip-binary32 | round-instead-of-truncate | saturate-instead-of-low16 | merge-integer-and-float | admit-negative-nonfinite-overflow",
        )
        self.assertEqual(tokens["binary32-rounding"], "roundTiesToEven")
        self.assertEqual(tokens["truncation"], "toward-zero")
        self.assertEqual(tokens["low16-integer"], "twos-complement")
        self.assertEqual(tokens["missing-family"], "stays-missing")
        self.assertEqual(tokens["native-grade"], "Unknown")
        self.assertEqual(tokens["semantic-grade-resolved"], "Hypothesis")
        self.assertEqual(tokens["numeric-grade-resolved"], "Proven")
        self.assertEqual(tokens["numeric-grade-unresolved"], "Unknown")
        self.assertEqual(tokens["admit-negative"], "false")
        self.assertEqual(tokens["admit-nonfinite"], "false")
        self.assertEqual(tokens["admit-overflow"], "false")
        self.assertEqual(tokens["merge-paths"], "false")
        self.assertEqual(tokens["saturate-low16"], "false")
        self.assertEqual(tokens["skip-binary32"], "false")
        self.assertEqual(tokens["round-instead-of-truncate"], "false")
        for line in page.splitlines():
            lowered = line.lower()
            if "native" in lowered and "proven" in lowered:
                self.assertTrue(
                    any(word in lowered for word in ("not", "no ", "unknown", "does not")),
                    line,
                )

    def test_page_table_matches_examples(self) -> None:
        document = load_fixture()
        rows = parse_page_table(PAGE.read_text(encoding="utf-8"))
        self.assertEqual([row["id"] for row in rows], [example["id"] for example in document["examples"]])
        for row, example in zip(rows, document["examples"]):
            expect = example["expect"]
            carrier = "none" if expect["carrier_low16"] is None else str(expect["carrier_low16"])
            raw = "none" if expect["raw_classification"] is None else expect["raw_classification"]
            self.assertEqual(row["path"], example["path"])
            self.assertEqual(row["operand"], example["operand_literal"])
            self.assertEqual(row["disposition"], expect["disposition"])
            self.assertEqual(row["carrier_low16"], carrier)
            self.assertEqual(row["raw_classification"], raw)
            self.assertEqual(row["numeric"], expect["grades"]["numeric"])
            self.assertEqual(row["semantic"], expect["grades"]["semantic"])
            self.assertEqual(row["native"], expect["grades"]["native"])
            self.assertEqual(row["native"], "Unknown")

    def test_relative_links_resolve_locally(self) -> None:
        page = PAGE.read_text(encoding="utf-8")
        links = _LINK.findall(page)
        self.assertGreaterEqual(len(links), 2)
        for link in links:
            self.assertNotIn("://", link)
            target = link.split("#", 1)[0]
            resolved = (PAGE.parent / target).resolve()
            self.assertTrue(resolved.is_file(), link)
            self.assertTrue(resolved.is_relative_to(ROOT))

    def test_grades_are_independent(self) -> None:
        for example in load_fixture()["examples"]:
            grades = example["expect"]["grades"]
            self.assertEqual(grades["native"], "Unknown")
            self.assertNotEqual(grades["semantic"], "Proven")
            if example["expect"]["disposition"] == "resolved":
                self.assertEqual(grades["numeric"], "Proven")
                self.assertEqual(grades["semantic"], "Hypothesis")
                self.assertNotEqual(grades["numeric"], grades["native"])
                self.assertNotEqual(grades["semantic"], grades["numeric"])
                self.assertIsNotNone(example["expect"]["carrier_low16"])
            else:
                self.assertEqual(grades["numeric"], "Unknown")
                self.assertEqual(grades["semantic"], "Unknown")
                self.assertIsNone(example["expect"]["carrier_low16"])
            self.assertEqual(set(grades), {"numeric", "semantic", "native"})

    def test_published_files_omit_revision_fingerprints(self) -> None:
        for path in (PAGE, FIXTURE):
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(_HEX_FINGERPRINT.search(text))
            self.assertNotIn("BAS" + "V2", text)
            self.assertNotRegex(text, r"private(?:-context)?/")


if __name__ == "__main__":
    unittest.main()
