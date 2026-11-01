"""Synthetic B51B offline budget and checksum contract.

The helpers here are the hypothetical ab23an23 surface. They do not qualify a
device, talk to a peer, or read expectations back out of the published page.
"""

from __future__ import annotations

import copy
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "architecture" / "an24_b51b_local_budget_crc.md"
FIXTURE = ROOT / "architecture" / "fixtures" / "an24_b51b_local_budget_crc.json"

WIDTH_BITS = 64
UINT64_MAX = (1 << WIDTH_BITS) - 1
POLYNOMIAL = 0x1021
DEFAULT_INITIAL = 0xFFFF
CRC_DIGITS = 0x29B1
CRC_INITIAL_ZERO = 0x31C3
CRC_EMPTY = 0xFFFF
CRC_LENGTH_EIGHT = 0xA12B
CRC_START_ONE = 0x1FDC
CRC_INITIAL_ONE = 0x7610
CRC_EMPTY_INITIAL_ZERO = 0x0000
FLIP_CRC = (
    0xC292,
    0x6E62,
    0x91D0,
    0x6C11,
    0x83E0,
    0x5F05,
    0x1E81,
    0x1A80,
    0x3990,
)
DIGITS = b"123456789"
RAW_RULE_TEXT = "(i * 17 + 3) & 255"
GROUPED = "grouped_1024"
SINGLE = "single_205"
SIGNATURES = {
    "plan": (
        "PlanLocalBudget(procedure, input) -> "
        "(procedure, chunks, consumed, unplanned)"
    ),
    "progress": (
        "AdvanceLocalProgress(prior, accepted, actual) -> "
        "(outcome, last_known_good, next)"
    ),
    "checksum": (
        "LocalChecksum(payload, start, length, initial) -> "
        "(outcome, value, raw, start, length)"
    ),
}
BOUNDARY = {
    "transfer_client": "false",
    "programming_command": "false",
    "framing": "false",
    "io": "false",
    "timeout": "false",
    "routing": "false",
    "executor": "false",
    "authorization_gate": "false",
}
UNKNOWN_TOPICS = (
    "peer_append",
    "erase_geometry",
    "segment_identity",
    "physical_capacities",
    "native_crc",
    "repeated_group_scheduling",
    "persistence",
    "support",
)
REQUIRED_POLICY = {
    "alias_chunk_buffers": "false",
    "auto_plan_later_groups": "false",
    "copy_slices": "true",
    "crc.bit_order": "msb_first",
    "crc.byte_swap": "false",
    "crc.covers": "caller_selected_span_only",
    "crc.extra_byte": "false",
    "crc.final_xor": "0",
    "crc.initial_default": "65535",
    "crc.polynomial": "4129",
    "crc.reflect_input": "false",
    "crc.reflect_output": "false",
    "crc.returns": "numeric_only",
    "grouped_1024.chunk_caps": "206,206,206,206,200",
    "grouped_1024.group_limit": "1024",
    "grouped_1024.groups_per_call": "1",
    "grouped_1024.inherits_grouped_1024": "false",
    "grouped_1024.slot_role": "chunks",
    "peer_empty_packet_claim": "false",
    "progress.advances_on_rejected": "false",
    "progress.bool_is_integer": "false",
    "progress.buffer_offset_from_byte_progress": "false",
    "progress.buffer_offset_from_chunk_index": "false",
    "progress.overflow": "reject",
    "progress.width_bits": "64",
    "raw_rule": RAW_RULE_TEXT,
    "single_205.chunk_caps": "205",
    "single_205.group_limit": "none",
    "single_205.groups_per_call": "1",
    "single_205.inherits_grouped_1024": "false",
    "single_205.slot_role": "chunks",
}
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")


def raw_byte(index):
    return (index * 17 + 3) & 255


def materialize(raw):
    form = raw["form"]
    if form == "none":
        return b""
    if form == "rule":
        return bytes(raw_byte(index) for index in range(raw["length"]))
    if form == "hex":
        return bytes.fromhex(raw["hex"])
    if form == "ascii":
        return raw["text"].encode("ascii")
    raise AssertionError(form)


def grade(numeric, semantic):
    return {
        "numeric_grade": numeric,
        "semantic_grade": semantic,
        "native_grade": "Unknown",
        "physical_qualification": "Unknown",
        "presence": "not_claimed",
        "freshness": "not_applicable",
        "execution": "not_run",
    }


def example(
    identifier,
    procedure,
    raw,
    selection,
    context,
    outcome,
    reason,
    result,
    numeric,
    semantic,
):
    row = {
        "id": identifier,
        "procedure": procedure,
        "raw": raw,
        "selection": selection,
        "context": context,
        "outcome": outcome,
        "reason": reason,
        "result": result,
    }
    row.update(grade(numeric, semantic))
    return row


def rule(length):
    return {"form": "rule", "length": length}


def hex_raw(value):
    return {"form": "hex", "hex": value}


def ascii_raw(text):
    return {"form": "ascii", "text": text}


def input_selection(length):
    return {"kind": "input", "start": 0, "length": length}


def span_selection(start, length, initial=None):
    return {"kind": "span", "start": start, "length": length, "initial": initial}


def progress_selection(prior, accepted, actual):
    return {"kind": "progress", "prior": prior, "accepted": accepted, "actual": actual}


def budget_result(lengths, consumed, unplanned, keep_raw=False):
    result = {
        "chunk_lengths": list(lengths),
        "consumed": consumed,
        "unplanned": unplanned,
    }
    if keep_raw:
        result["raw"] = "kept"
    return result


def progress_result(last_known_good, nxt):
    return {"last_known_good": last_known_good, "next": nxt}


def checksum_result(value, keep_raw=True):
    result = {"raw": "kept" if keep_raw else "dropped"}
    result["value"] = None if value is None else f"{value:04X}"
    return result


def build_examples():
    proven = ("Proven", "Proven")
    hypo = ("Hypothesis", "Hypothesis")
    rows = [
        example(
            "grouped_1024_exact",
            GROUPED,
            rule(1024),
            input_selection(1024),
            "first_group",
            "planned",
            None,
            budget_result((206, 206, 206, 206, 200), 1024, 0),
            *proven,
        ),
        example(
            "grouped_1025_unplanned",
            GROUPED,
            rule(1025),
            input_selection(1025),
            "unplanned_remainder",
            "planned",
            None,
            budget_result((206, 206, 206, 206, 200), 1024, 1),
            *proven,
        ),
        example(
            "grouped_2048_one_group",
            GROUPED,
            rule(2048),
            input_selection(2048),
            "later_group_not_planned",
            "planned",
            None,
            budget_result((206, 206, 206, 206, 200), 1024, 1024),
            *proven,
        ),
        example(
            "grouped_824_four_chunks",
            GROUPED,
            rule(824),
            input_selection(824),
            "four_chunks_no_fifth",
            "planned",
            None,
            budget_result((206, 206, 206, 206), 824, 0),
            *proven,
        ),
        example(
            "grouped_825_short_fifth",
            GROUPED,
            rule(825),
            input_selection(825),
            "short_fifth_chunk",
            "planned",
            None,
            budget_result((206, 206, 206, 206, 1), 825, 0),
            *proven,
        ),
        example(
            "grouped_207_short_second",
            GROUPED,
            rule(207),
            input_selection(207),
            "short_second_chunk",
            "planned",
            None,
            budget_result((206, 1), 207, 0),
            *proven,
        ),
        example(
            "grouped_three_byte_hex",
            GROUPED,
            hex_raw("00ff10"),
            input_selection(3),
            "short_input",
            "planned",
            None,
            budget_result((3,), 3, 0),
            *proven,
        ),
        example(
            "empty_grouped",
            GROUPED,
            rule(0),
            input_selection(0),
            "no_peer_empty_packet",
            "planned",
            None,
            budget_result((), 0, 0),
            *proven,
        ),
        example(
            "single_205_over_206",
            SINGLE,
            rule(206),
            input_selection(206),
            "single_chunk_remainder",
            "planned",
            None,
            budget_result((205,), 205, 1),
            *proven,
        ),
        example(
            "single_205_exact",
            SINGLE,
            rule(205),
            input_selection(205),
            "exact_single_chunk",
            "planned",
            None,
            budget_result((205,), 205, 0),
            *proven,
        ),
        example(
            "single_205_over_1024",
            SINGLE,
            rule(1024),
            input_selection(1024),
            "group_policy_not_inherited",
            "planned",
            None,
            budget_result((205,), 205, 819),
            *proven,
        ),
        example(
            "empty_single_205",
            SINGLE,
            rule(0),
            input_selection(0),
            "no_peer_empty_packet",
            "planned",
            None,
            budget_result((), 0, 0),
            *proven,
        ),
        example(
            "unknown_procedure",
            "other",
            hex_raw("00ff10"),
            input_selection(3),
            "supplied_procedure",
            "rejected",
            "unknown_procedure",
            budget_result((), 0, 3, keep_raw=True),
            *proven,
        ),
        example(
            "progress_accept_10_17",
            None,
            {"form": "none"},
            progress_selection(10, True, 17),
            "accepted_chunk",
            "advanced",
            None,
            progress_result(10, 27),
            *hypo,
        ),
        example(
            "progress_reject_10_17",
            None,
            {"form": "none"},
            progress_selection(10, False, 17),
            "rejected_chunk",
            "unchanged",
            None,
            progress_result(10, 10),
            *hypo,
        ),
        example(
            "progress_actual_16",
            None,
            {"form": "none"},
            progress_selection(10, True, 16),
            "actual_length",
            "advanced",
            None,
            progress_result(10, 26),
            *hypo,
        ),
        example(
            "progress_actual_0",
            None,
            {"form": "none"},
            progress_selection(10, True, 0),
            "zero_actual",
            "unchanged",
            None,
            progress_result(10, 10),
            *hypo,
        ),
        example(
            "progress_prior_11",
            None,
            {"form": "none"},
            progress_selection(11, True, 17),
            "prior_count",
            "advanced",
            None,
            progress_result(11, 28),
            *hypo,
        ),
        example(
            "progress_overflow",
            None,
            {"form": "none"},
            progress_selection(UINT64_MAX, True, 1),
            "overflow",
            "rejected",
            "overflow",
            progress_result(UINT64_MAX, None),
            *hypo,
        ),
        example(
            "progress_reject_at_limit",
            None,
            {"form": "none"},
            progress_selection(UINT64_MAX, False, 1),
            "rejected_at_limit",
            "unchanged",
            None,
            progress_result(UINT64_MAX, UINT64_MAX),
            *hypo,
        ),
        example(
            "progress_negative_actual",
            None,
            {"form": "none"},
            progress_selection(10, True, -1),
            "negative_actual",
            "rejected",
            "negative_count",
            progress_result(10, None),
            *hypo,
        ),
        example(
            "progress_negative_prior",
            None,
            {"form": "none"},
            progress_selection(-1, True, 17),
            "negative_prior",
            "rejected",
            "negative_count",
            progress_result(None, None),
            *hypo,
        ),
        example(
            "progress_negative_actual_while_rejected",
            None,
            {"form": "none"},
            progress_selection(10, False, -1),
            "negative_actual_while_rejected",
            "rejected",
            "negative_count",
            progress_result(10, None),
            *hypo,
        ),
        example(
            "crc_digits_default",
            None,
            ascii_raw("123456789"),
            span_selection(0, 9, None),
            "caller_selected_span",
            "checksum",
            None,
            checksum_result(CRC_DIGITS),
            *hypo,
        ),
        example(
            "crc_empty_default",
            None,
            ascii_raw(""),
            span_selection(0, 0, None),
            "empty_selection",
            "checksum",
            None,
            checksum_result(CRC_EMPTY),
            *hypo,
        ),
        example(
            "crc_digits_initial_0",
            None,
            ascii_raw("123456789"),
            span_selection(0, 9, 0),
            "explicit_initial",
            "checksum",
            None,
            checksum_result(CRC_INITIAL_ZERO),
            *hypo,
        ),
        example(
            "crc_explicit_default_initial",
            None,
            ascii_raw("123456789"),
            span_selection(0, 9, DEFAULT_INITIAL),
            "explicit_initial",
            "checksum",
            None,
            checksum_result(CRC_DIGITS),
            *hypo,
        ),
        example(
            "crc_empty_initial_0",
            None,
            ascii_raw(""),
            span_selection(0, 0, 0),
            "explicit_initial",
            "checksum",
            None,
            checksum_result(CRC_EMPTY_INITIAL_ZERO),
            *hypo,
        ),
        example(
            "crc_span_length_8",
            None,
            ascii_raw("123456789"),
            span_selection(0, 8, None),
            "caller_selected_span",
            "checksum",
            None,
            checksum_result(CRC_LENGTH_EIGHT),
            *hypo,
        ),
        example(
            "crc_span_start_1",
            None,
            ascii_raw("123456789"),
            span_selection(1, 8, None),
            "caller_selected_span",
            "checksum",
            None,
            checksum_result(CRC_START_ONE),
            *hypo,
        ),
        example(
            "crc_initial_1",
            None,
            ascii_raw("123456789"),
            span_selection(0, 9, 1),
            "explicit_initial",
            "checksum",
            None,
            checksum_result(CRC_INITIAL_ONE),
            *hypo,
        ),
        example(
            "crc_negative_length",
            None,
            ascii_raw("123456789"),
            span_selection(0, -1, None),
            "malformed_span",
            "rejected",
            "negative_span",
            checksum_result(None),
            *hypo,
        ),
        example(
            "crc_negative_start",
            None,
            ascii_raw("123456789"),
            span_selection(-1, 9, None),
            "malformed_span",
            "rejected",
            "negative_span",
            checksum_result(None),
            *hypo,
        ),
        example(
            "crc_span_past_end",
            None,
            ascii_raw("123456789"),
            span_selection(0, 10, None),
            "span_out_of_range",
            "rejected",
            "span_out_of_range",
            checksum_result(None),
            *hypo,
        ),
        example(
            "crc_empty_span_at_end",
            None,
            ascii_raw("123456789"),
            span_selection(9, 0, None),
            "empty_selection",
            "checksum",
            None,
            checksum_result(CRC_EMPTY),
            *hypo,
        ),
    ]
    for index, value in enumerate(FLIP_CRC):
        payload = bytearray(DIGITS)
        payload[index] ^= 0x01
        rows.append(
            example(
                f"crc_flip_byte_{index}",
                None,
                hex_raw(bytes(payload).hex()),
                span_selection(0, 9, None),
                "mutated_input_byte",
                "checksum",
                None,
                checksum_result(value),
                *hypo,
            )
        )
    return rows


EXAMPLES = build_examples()
EXAMPLES_BY_ID = {row["id"]: row for row in EXAMPLES}


def parse_caps(text):
    if text == "":
        return ()
    return tuple(int(part) for part in text.split(","))


def reflect8(value):
    out = 0
    for bit in range(8):
        if value & (1 << bit):
            out |= 1 << (7 - bit)
    return out


def reflect16(value):
    out = 0
    for bit in range(16):
        if value & (1 << bit):
            out |= 1 << (15 - bit)
    return out


def crc16(data, initial, polynomial, reflect_input, reflect_output, final_xor):
    value = initial & 0xFFFF
    for byte in data:
        if reflect_input:
            byte = reflect8(byte)
        value ^= byte << 8
        for _ in range(8):
            if value & 0x8000:
                value = ((value << 1) ^ polynomial) & 0xFFFF
            else:
                value = (value << 1) & 0xFFFF
    if reflect_output:
        value = reflect16(value)
    return (value ^ final_xor) & 0xFFFF


def _plan(procedure, data, caps, group_limit, groups, copy):
    chunks = []
    consumed = 0
    total = len(data)
    for _group in range(groups):
        group_consumed = 0
        for cap in caps:
            if consumed >= total:
                break
            room = cap
            if group_limit is not None:
                room = min(room, group_limit - group_consumed)
            if room <= 0:
                break
            take = min(room, total - consumed)
            if take <= 0:
                break
            if copy:
                chunks.append(bytearray(data[consumed : consumed + take]))
            else:
                chunks.append(memoryview(data)[consumed : consumed + take])
            consumed += take
            group_consumed += take
        if consumed >= total:
            break
    return {
        "procedure": procedure,
        "outcome": "planned",
        "reason": None,
        "chunks": chunks,
        "consumed": consumed,
        "unplanned": total - consumed,
    }


def rejected_plan(procedure, data, reason):
    return {
        "procedure": procedure,
        "outcome": "rejected",
        "reason": reason,
        "chunks": [],
        "consumed": 0,
        "unplanned": len(data),
        "raw": bytearray(data),
    }


def plan_reference(procedure, data):
    if procedure == GROUPED:
        return _plan(procedure, data, (206, 206, 206, 206, 200), 1024, 1, True)
    if procedure == SINGLE:
        return _plan(procedure, data, (205,), None, 1, True)
    return rejected_plan(procedure, data, "unknown_procedure")


def _as_int(value, bool_is_integer):
    if isinstance(value, bool):
        if not bool_is_integer:
            return None
        return int(value)
    if isinstance(value, int):
        return value
    return None


def advance_with_rules(prior, accepted, actual, width_bits, overflow, add_when_rejected, bool_is_integer):
    limit = 1 << width_bits
    prior_int = _as_int(prior, bool_is_integer)
    actual_int = _as_int(actual, bool_is_integer)
    prior_known = prior_int if prior_int is not None and 0 <= prior_int < limit else None
    if prior_int is None or actual_int is None:
        return {
            "outcome": "rejected",
            "reason": "malformed_integer",
            "last_known_good": prior_known,
            "next": None,
        }
    if not isinstance(accepted, bool):
        return {
            "outcome": "rejected",
            "reason": "malformed_boolean",
            "last_known_good": prior_known,
            "next": None,
        }
    if prior_int < 0 or actual_int < 0:
        return {
            "outcome": "rejected",
            "reason": "negative_count",
            "last_known_good": prior_known,
            "next": None,
        }
    if prior_int >= limit or actual_int >= limit:
        return {
            "outcome": "rejected",
            "reason": "out_of_range",
            "last_known_good": prior_known,
            "next": None,
        }
    if not accepted and not add_when_rejected:
        return {
            "outcome": "unchanged",
            "reason": None,
            "last_known_good": prior_int,
            "next": prior_int,
        }
    if prior_int + actual_int >= limit:
        if overflow == "wrap":
            return {
                "outcome": "advanced",
                "reason": None,
                "last_known_good": prior_int,
                "next": (prior_int + actual_int) % limit,
            }
        return {
            "outcome": "rejected",
            "reason": "overflow",
            "last_known_good": prior_int,
            "next": None,
        }
    nxt = prior_int + actual_int
    outcome = "unchanged" if nxt == prior_int else "advanced"
    return {
        "outcome": outcome,
        "reason": None,
        "last_known_good": prior_int,
        "next": nxt,
    }


def advance_reference(prior, accepted, actual):
    return advance_with_rules(
        prior, accepted, actual, WIDTH_BITS, "reject", False, False
    )


def checksum_with_rules(
    payload,
    start,
    length,
    initial,
    polynomial,
    default_initial,
    bit_order,
    reflect_input,
    reflect_output,
    final_xor,
    extra_byte,
    byte_swap,
    covers,
):
    raw = bytearray(payload)
    if isinstance(start, bool) or isinstance(length, bool) or not isinstance(start, int) or not isinstance(length, int):
        return {
            "outcome": "rejected",
            "reason": "malformed_span",
            "value": None,
            "raw": raw,
            "start": start,
            "length": length,
        }
    if start < 0 or length < 0:
        return {
            "outcome": "rejected",
            "reason": "negative_span",
            "value": None,
            "raw": raw,
            "start": start,
            "length": length,
        }
    if start > len(payload) or start + length > len(payload):
        return {
            "outcome": "rejected",
            "reason": "span_out_of_range",
            "value": None,
            "raw": raw,
            "start": start,
            "length": length,
        }
    if covers == "caller_selected_span_only":
        selected = bytes(payload[start : start + length])
    else:
        selected = bytes(payload)
    if extra_byte:
        selected += b"\x00"
    if bit_order == "lsb_first":
        reflect_input = True
    value = crc16(
        selected,
        default_initial if initial is None else initial,
        polynomial,
        reflect_input,
        reflect_output,
        final_xor,
    )
    if byte_swap:
        value = ((value & 0xFF) << 8) | (value >> 8)
    return {
        "outcome": "checksum",
        "reason": None,
        "value": value,
        "raw": raw,
        "start": start,
        "length": length,
    }


def checksum_reference(payload, start, length, initial=None):
    return checksum_with_rules(
        payload,
        start,
        length,
        initial,
        POLYNOMIAL,
        DEFAULT_INITIAL,
        "msb_first",
        False,
        False,
        0,
        False,
        False,
        "caller_selected_span_only",
    )


def _bool_text(value):
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(value)


def interpret_plan(policy, procedure, data):
    if procedure not in (GROUPED, SINGLE):
        return rejected_plan(procedure, data, "unknown_procedure")
    prefix = procedure + "."
    role = policy[prefix + "slot_role"]
    if role != "chunks":
        return rejected_plan(procedure, data, "retries_not_chunks")
    inherit = _bool_text(policy[prefix + "inherits_grouped_1024"])
    source = "grouped_1024." if inherit else prefix
    caps = parse_caps(policy[source + "chunk_caps"])
    limit_text = policy[source + "group_limit"]
    group_limit = None if limit_text == "none" else int(limit_text)
    groups = int(policy[source + "groups_per_call"])
    if _bool_text(policy["auto_plan_later_groups"]):
        groups = max(groups, 1_000_000)
    copy = _bool_text(policy["copy_slices"]) and not _bool_text(policy["alias_chunk_buffers"])
    result = _plan(procedure, data, caps, group_limit, groups, copy)
    if _bool_text(policy["peer_empty_packet_claim"]) and len(data) == 0:
        result["peer_empty_packet"] = True
    return result


def interpret_progress(policy, prior, accepted, actual):
    if _bool_text(policy["progress.buffer_offset_from_chunk_index"]):
        return {"offset_from": "chunk_index"}
    if _bool_text(policy["progress.buffer_offset_from_byte_progress"]):
        return {"offset_from": "byte_progress"}
    return advance_with_rules(
        prior,
        accepted,
        actual,
        int(policy["progress.width_bits"]),
        policy["progress.overflow"],
        _bool_text(policy["progress.advances_on_rejected"]),
        _bool_text(policy["progress.bool_is_integer"]),
    )


def interpret_checksum(policy, payload, start, length, initial):
    value = checksum_with_rules(
        payload,
        start,
        length,
        initial,
        int(policy["crc.polynomial"]),
        int(policy["crc.initial_default"]),
        policy["crc.bit_order"],
        _bool_text(policy["crc.reflect_input"]),
        _bool_text(policy["crc.reflect_output"]),
        int(policy["crc.final_xor"]),
        _bool_text(policy["crc.extra_byte"]),
        _bool_text(policy["crc.byte_swap"]),
        policy["crc.covers"],
    )
    if policy["crc.returns"] != "numeric_only" and value["outcome"] == "checksum":
        value["swapped_bytes"] = "returned"
    return value


def _pipe_row(cells):
    return "| " + " | ".join(cells) + " |"


def _table(headers, rows):
    lines = [_pipe_row(headers), _pipe_row(["---"] * len(headers))]
    lines.extend(_pipe_row(row) for row in rows)
    return "\n".join(lines)


def _cell_int(text):
    if text == "absent":
        return None
    return int(text)


def encode_raw(raw):
    form = raw["form"]
    if form == "none":
        return "-"
    if form == "rule":
        return f"rule:{raw['length']}"
    if form == "hex":
        return f"hex:{raw['hex']}"
    if form == "ascii":
        return "ascii:" + raw["text"]
    raise AssertionError(form)


def decode_raw(text):
    if text == "-":
        return {"form": "none"}
    kind, value = text.split(":", 1)
    if kind == "rule":
        return {"form": "rule", "length": int(value)}
    if kind == "hex":
        return {"form": "hex", "hex": value}
    if kind == "ascii":
        return {"form": "ascii", "text": value}
    raise AssertionError(text)


def encode_selection(selection):
    kind = selection["kind"]
    if kind == "input":
        return f"input:{selection['start']}+{selection['length']}"
    if kind == "span":
        initial = selection["initial"]
        initial_text = "default" if initial is None else str(initial)
        return (
            f"span:{selection['start']}+{selection['length']};"
            f"initial={initial_text}"
        )
    if kind == "progress":
        accepted = "true" if selection["accepted"] else "false"
        return (
            f"progress:prior={selection['prior']};"
            f"accepted={accepted};actual={selection['actual']}"
        )
    raise AssertionError(kind)


def decode_selection(text):
    if text.startswith("input:"):
        start, length = text[len("input:") :].split("+", 1)
        return {"kind": "input", "start": int(start), "length": int(length)}
    if text.startswith("span:"):
        span, initial = text[len("span:") :].split(";initial=", 1)
        start, length = span.split("+", 1)
        return {
            "kind": "span",
            "start": int(start),
            "length": int(length),
            "initial": None if initial == "default" else int(initial),
        }
    if text.startswith("progress:"):
        fields = dict(part.split("=", 1) for part in text[len("progress:") :].split(";"))
        return {
            "kind": "progress",
            "prior": int(fields["prior"]),
            "accepted": fields["accepted"] == "true",
            "actual": int(fields["actual"]),
        }
    raise AssertionError(text)


def encode_result(result):
    if "chunk_lengths" in result:
        lengths = result["chunk_lengths"]
        chunks = "none" if not lengths else "+".join(str(item) for item in lengths)
        text = f"chunks={chunks};consumed={result['consumed']};unplanned={result['unplanned']}"
        if result.get("raw") == "kept":
            text += ";raw=kept"
        return text
    if "last_known_good" in result:
        last = "absent" if result["last_known_good"] is None else str(result["last_known_good"])
        nxt = "absent" if result["next"] is None else str(result["next"])
        return f"last_known_good={last};next={nxt}"
    value = "absent" if result["value"] is None else result["value"]
    raw = result["raw"]
    return f"value={value};raw={raw}"


def decode_result(text):
    fields = dict(part.split("=", 1) for part in text.split(";"))
    if "chunks" in fields:
        chunks = fields["chunks"]
        lengths = [] if chunks == "none" else [int(part) for part in chunks.split("+")]
        result = {
            "chunk_lengths": lengths,
            "consumed": int(fields["consumed"]),
            "unplanned": int(fields["unplanned"]),
        }
        if "raw" in fields:
            result["raw"] = fields["raw"]
        return result
    if "last_known_good" in fields:
        return {
            "last_known_good": _cell_int(fields["last_known_good"]),
            "next": _cell_int(fields["next"]),
        }
    return {
        "value": None if fields["value"] == "absent" else fields["value"],
        "raw": fields["raw"],
    }


def encode_example(row):
    return [
        row["id"],
        "-" if row["procedure"] is None else row["procedure"],
        encode_raw(row["raw"]),
        encode_selection(row["selection"]),
        row["context"],
        row["outcome"],
        "-" if row["reason"] is None else row["reason"],
        encode_result(row["result"]),
        row["numeric_grade"],
        row["semantic_grade"],
        row["native_grade"],
        row["physical_qualification"],
        row["presence"],
        row["freshness"],
        row["execution"],
    ]


EXAMPLE_HEADERS = [
    "ID",
    "Procedure",
    "Raw",
    "Selection",
    "Context",
    "Outcome",
    "Reason",
    "Result",
    "Numeric",
    "Semantic",
    "Native",
    "Qualification",
    "Presence",
    "Freshness",
    "Execution",
]


def decode_example(cells):
    mapped = dict(zip(EXAMPLE_HEADERS, cells))
    return example(
        mapped["ID"],
        None if mapped["Procedure"] == "-" else mapped["Procedure"],
        decode_raw(mapped["Raw"]),
        decode_selection(mapped["Selection"]),
        mapped["Context"],
        mapped["Outcome"],
        None if mapped["Reason"] == "-" else mapped["Reason"],
        decode_result(mapped["Result"]),
        mapped["Numeric"],
        mapped["Semantic"],
    ) | {
        "physical_qualification": mapped["Qualification"],
        "presence": mapped["Presence"],
        "freshness": mapped["Freshness"],
        "execution": mapped["Execution"],
        "native_grade": mapped["Native"],
    }


def render_policy_table():
    return _table(
        ["Key", "Value"],
        [[key, REQUIRED_POLICY[key]] for key in sorted(REQUIRED_POLICY)],
    )


def render_examples_table():
    return _table(EXAMPLE_HEADERS, [encode_example(row) for row in EXAMPLES])


def render_unknowns_table():
    return _table(
        ["Topic", "Evidence", "Semantic", "Native", "Qualification", "Presence", "Freshness", "Execution"],
        [
            [topic, "Unknown", "Unknown", "Unknown", "Unknown", "not_claimed", "not_applicable", "not_run"]
            for topic in UNKNOWN_TOPICS
        ],
    )


def render_boundary_table():
    return _table(
        ["Boundary", "Admitted"],
        [[key, BOUNDARY[key]] for key in sorted(BOUNDARY)],
    )


def render_signature_table():
    return _table(
        ["Role", "Signature"],
        [[role, SIGNATURES[role]] for role in ("plan", "progress", "checksum")],
    )


def render_page():
    return f"""# B51B local byte budgets and checksums

This page is a pre-1.0 software contract for offline helpers on the B51B family. It is the ordinary companion of AN23 for the same ab23an23 helper surface, and a partial child of issue 736. The parent stays open. The page does not qualify a device, repeat a native family page, or depend on an implementation change.

Nothing here is a Helianthus 1.0 stable surface. The contract adds no major namespace and no experimental namespace. It adds no authorization gate. Roadmap wording for any later gate is 0.11, and this helper does not schedule that work.

Evidence grades stay independent of physical qualification, presence, freshness, and execution. Every row below keeps those axes. Native grade is Unknown on every row. Execution is not run.

## Boundary

The helpers are pure. One call reads its arguments and returns a value. It does not keep a cursor, open a transfer, or decide a later group on its own.

The helper is offline. It does not add or change an MCP tool or a GraphQL field, so those faces gain no new operation.

A call does not yield a device buffer offset. Chunk index and byte progress are not offsets.

{render_boundary_table()}

## Signatures

These signatures are hypothetical and are the names used for the whole contract. `procedure` is `grouped_1024` or `single_205`. An omitted `initial` selects the default initial value. Boolean values are not integers for `prior`, `actual`, `start`, or `length`.

{render_signature_table()}

`PlanLocalBudget` copies input bytes into owned mutable chunk buffers and returns those chunks, the consumed count, and the unplanned count. The procedure identity is returned with them. Empty input returns no chunks. That result is not a peer-empty-packet claim.

`AdvanceLocalProgress` is a pure transition. `accepted` false leaves a valid prior count unchanged. Adding a valid actual count that would exceed the unsigned width is rejected, and the prior count stays the last known good value. A negative prior or actual is rejected. An `accepted` value that is not a Boolean is rejected. The next count is absent when the transition is rejected.

`LocalChecksum` covers exactly the caller-selected span and returns one numeric value. The raw payload, start, and length are kept when the span is rejected. The numeric value is absent in that case. The returned number is not a byte-swapped pair and not a framed field.

## States

`planned` means the budget call returned owned chunks. `advanced` means a progress call produced a greater next count. `unchanged` means a well-formed progress call kept the prior count, including a rejected chunk whose actual length was not added. `rejected` means the call was not admitted: unknown procedure, a slot role other than chunks, negative count, overflow, malformed span, or a span outside the payload. `checksum` means a numeric value was returned.

Bytes beyond the one grouped plan stay unplanned. The caller plans them by passing that suffix in a new call. Calling again with the same bytes plans the same first group.

The `single_205` alternative returns at most one chunk. It does not inherit the 1024-byte group, the five chunk slots, or the grouped caps.

Local progress is a hypothesis. It advances only by the actual byte count of an accepted chunk. It does not invent a peer counter.

The local checksum is a hypothesis. The polynomial is `0x1021`, the default initial value is `0xFFFF`, the bit order is MSB first, reflection is off, and the final XOR is zero. ASCII `123456789` has check value `0x29B1`. The same digits with explicit initial zero have check value `0x31C3`. Empty input under the default initial value is `0xFFFF`. No peer, block, or transport checksum is identified by these numbers.

## Normative policy

The table is the normative software policy. Planning uses the chunk slots named there. The fifth grouped slot is the last value in `grouped_1024.chunk_caps`. The single-chunk alternative keeps its own cap. `group_limit` `none` means that alternative has no 1024-byte group.

{render_policy_table()}

Synthetic input bytes for a `rule` length are `byte[i] = (i * 17 + 3) & 255`.

## Unknowns

These topics are Unknown. The software rows do not promote them.

{render_unknowns_table()}

## Examples

The table is the finite synthetic set. Raw forms, selection, context, and partial outcomes are on each row. Numeric, semantic, and native grades are separate. Qualification, presence, freshness, and execution are separate again.

{render_examples_table()}

## Fixture

The machine-readable copy of this contract is [`an24_b51b_local_budget_crc.json`](fixtures/an24_b51b_local_budget_crc.json).
"""


def fixture_document():
    return {
        "id": "an24_b51b_local_budget_crc",
        "family": "B51B",
        "api": "ab23an23",
        "stability": "pre_1_0",
        "companion": "AN23",
        "parent_issue": 736,
        "executor_added": False,
        "authorization_gate_added": False,
        "signatures": dict(SIGNATURES),
        "boundary": dict(BOUNDARY),
        "policy": dict(sorted(REQUIRED_POLICY.items())),
        "unknowns": [
            {
                "topic": topic,
                "evidence_grade": "Unknown",
                "semantic_grade": "Unknown",
                "native_grade": "Unknown",
                "physical_qualification": "Unknown",
                "presence": "not_claimed",
                "freshness": "not_applicable",
                "execution": "not_run",
            }
            for topic in UNKNOWN_TOPICS
        ],
        "examples": EXAMPLES,
        "presence": "not_claimed",
        "freshness": "not_applicable",
        "physical_qualification": "Unknown",
        "native_grade": "Unknown",
        "execution": "not_run",
    }


def _tables(text):
    tables = []
    current = []
    for line in text.splitlines():
        if line.startswith("|"):
            current.append(tuple(cell.strip() for cell in line.strip().strip("|").split("|")))
        elif current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    parsed = []
    for table in tables:
        headers = table[0]
        body = [row for row in table[1:] if not all(set(cell) <= {"-", " "} for cell in row)]
        parsed.append((headers, body))
    return parsed


def _table_map(text, header):
    for headers, body in _tables(text):
        if headers[0] == header:
            return headers, body
    raise KeyError(header)


def parse_page(text):
    policy_headers, policy_rows = _table_map(text, "Key")
    if policy_headers != ("Key", "Value"):
        raise ValueError("policy header")
    policy = {key: value for key, value in policy_rows}
    example_headers, example_rows = _table_map(text, "ID")
    if list(example_headers) != EXAMPLE_HEADERS:
        raise ValueError("example header")
    examples = [decode_example(row) for row in example_rows]
    unknown_headers, unknown_rows = _table_map(text, "Topic")
    unknowns = []
    for row in unknown_rows:
        mapped = dict(zip(unknown_headers, row))
        unknowns.append(
            {
                "topic": mapped["Topic"],
                "evidence_grade": mapped["Evidence"],
                "semantic_grade": mapped["Semantic"],
                "native_grade": mapped["Native"],
                "physical_qualification": mapped["Qualification"],
                "presence": mapped["Presence"],
                "freshness": mapped["Freshness"],
                "execution": mapped["Execution"],
            }
        )
    boundary_headers, boundary_rows = _table_map(text, "Boundary")
    if boundary_headers != ("Boundary", "Admitted"):
        raise ValueError("boundary header")
    boundary = {key: value for key, value in boundary_rows}
    signature_headers, signature_rows = _table_map(text, "Role")
    if signature_headers != ("Role", "Signature"):
        raise ValueError("signature header")
    signatures = {role: signature for role, signature in signature_rows}
    return {
        "policy": policy,
        "examples": examples,
        "unknowns": unknowns,
        "boundary": boundary,
        "signatures": signatures,
    }


def relative_link_errors(page_text, page_path):
    errors = []
    for match in LINK_RE.finditer(page_text):
        target = match.group(1).split("#", 1)[0]
        if not target or "://" in target or target.startswith("/"):
            errors.append(f"link:{match.group(1)}")
            continue
        resolved = (page_path.parent / target).resolve()
        if not resolved.is_file():
            errors.append(f"link-missing:{target}")
    return errors


def behavior_errors(policy, label):
    errors = []
    if policy.get("grouped_1024.inherits_grouped_1024") != "false":
        errors.append(f"behavior:{label}:grouped-inherits")
    if policy.get("single_205.group_limit") != "none":
        errors.append(f"behavior:{label}:single-group-limit")
    cases = (
        (GROUPED, 1024, [206, 206, 206, 206, 200], 1024, 0),
        (GROUPED, 1025, [206, 206, 206, 206, 200], 1024, 1),
        (GROUPED, 2048, [206, 206, 206, 206, 200], 1024, 1024),
        (GROUPED, 824, [206, 206, 206, 206], 824, 0),
        (GROUPED, 825, [206, 206, 206, 206, 1], 825, 0),
        (GROUPED, 207, [206, 1], 207, 0),
        (GROUPED, 0, [], 0, 0),
        (SINGLE, 206, [205], 205, 1),
        (SINGLE, 205, [205], 205, 0),
        (SINGLE, 1024, [205], 205, 819),
        (SINGLE, 0, [], 0, 0),
    )
    for procedure, length, lengths, consumed, unplanned in cases:
        data = bytearray(raw_byte(index) for index in range(length))
        try:
            got = interpret_plan(policy, procedure, data)
        except (KeyError, ValueError) as exc:
            errors.append(f"behavior:{label}:{procedure}:{length}:{exc}")
            continue
        if got.get("peer_empty_packet"):
            errors.append(f"behavior:{label}:peer-empty")
        if (
            got["outcome"] != "planned"
            or [len(chunk) for chunk in got["chunks"]] != lengths
            or got["consumed"] != consumed
            or got["unplanned"] != unplanned
        ):
            errors.append(f"behavior:{label}:{procedure}:{length}")
            continue
        offset = 0
        for chunk in got["chunks"]:
            size = len(chunk)
            if bytes(chunk) != bytes(data[offset : offset + size]):
                errors.append(f"behavior-bytes:{label}:{procedure}:{length}")
                break
            offset += size
    progress_cases = (
        (10, True, 17, "advanced", 10, 27, None),
        (10, False, 17, "unchanged", 10, 10, None),
        (10, True, 16, "advanced", 10, 26, None),
        (10, True, 0, "unchanged", 10, 10, None),
        (11, True, 17, "advanced", 11, 28, None),
        (UINT64_MAX, True, 1, "rejected", UINT64_MAX, None, "overflow"),
        (UINT64_MAX, False, 1, "unchanged", UINT64_MAX, UINT64_MAX, None),
        (10, True, -1, "rejected", 10, None, "negative_count"),
        (-1, True, 17, "rejected", None, None, "negative_count"),
        (10, False, -1, "rejected", 10, None, "negative_count"),
        (True, True, 1, "rejected", None, None, "malformed_integer"),
    )
    for prior, accepted, actual, outcome, last_known, nxt, reason in progress_cases:
        try:
            got = interpret_progress(policy, prior, accepted, actual)
        except (KeyError, ValueError) as exc:
            errors.append(f"behavior:{label}:progress:{prior}:{accepted}:{actual}:{exc}")
            continue
        if "offset_from" in got or got.get("outcome") != outcome or got.get("last_known_good") != last_known or got.get("next") != nxt or got.get("reason") != reason:
            errors.append(f"behavior:{label}:progress:{prior}:{accepted}:{actual}")
    checksum_cases = (
        (DIGITS, 0, 9, None, CRC_DIGITS),
        (b"", 0, 0, None, CRC_EMPTY),
        (DIGITS, 0, 9, 0, CRC_INITIAL_ZERO),
        (DIGITS, 0, 9, DEFAULT_INITIAL, CRC_DIGITS),
        (b"", 0, 0, 0, CRC_EMPTY_INITIAL_ZERO),
        (DIGITS, 0, 8, None, CRC_LENGTH_EIGHT),
        (DIGITS, 1, 8, None, CRC_START_ONE),
        (DIGITS, 0, 9, 1, CRC_INITIAL_ONE),
    )
    for payload, start, length, initial, value in checksum_cases:
        try:
            got = interpret_checksum(policy, payload, start, length, initial)
        except (KeyError, ValueError) as exc:
            errors.append(f"behavior:{label}:crc:{start}:{length}:{initial}:{exc}")
            continue
        if got["outcome"] != "checksum" or got["value"] != value or "swapped_bytes" in got:
            errors.append(f"behavior:{label}:crc:{start}:{length}:{initial}")
        elif bytes(got["raw"]) != payload:
            errors.append(f"behavior:{label}:crc-raw:{start}:{length}:{initial}")
    for start, length, reason in ((0, -1, "negative_span"), (-1, 9, "negative_span"), (0, 10, "span_out_of_range")):
        got = interpret_checksum(policy, DIGITS, start, length, None)
        if got["outcome"] != "rejected" or got["reason"] != reason or got["value"] is not None or bytes(got["raw"]) != DIGITS:
            errors.append(f"behavior:{label}:crc-reject:{start}:{length}")
    for index, value in enumerate(FLIP_CRC):
        payload = bytearray(DIGITS)
        payload[index] ^= 0x01
        got = interpret_checksum(policy, bytes(payload), 0, 9, None)
        if got["value"] != value:
            errors.append(f"behavior:{label}:crc-byte:{index}")
    return errors


def alias_errors(policy, label):
    source = bytearray(b"\x11\x22\x33")
    try:
        got = interpret_plan(policy, GROUPED, source)
    except (KeyError, ValueError):
        return [f"alias-probe:{label}"]
    if got["outcome"] != "planned" or not got["chunks"]:
        return [f"alias-probe:{label}"]
    original = source[0]
    try:
        got["chunks"][0][0] ^= 0xFF
    except TypeError:
        return [f"alias-probe:{label}"]
    if source[0] != original:
        return [f"alias-probe:{label}"]
    return []


def contract_errors(page_text, fixture, page_path=PAGE):
    errors = []
    try:
        parsed = parse_page(page_text)
    except (KeyError, ValueError, IndexError) as exc:
        return [f"page-unreadable:{exc}"]
    if set(parsed["policy"]) != set(REQUIRED_POLICY):
        errors.append("policy-keys")
    for key, value in REQUIRED_POLICY.items():
        if parsed["policy"].get(key) != value:
            errors.append(f"policy:{key}")
        if fixture.get("policy", {}).get(key) != value:
            errors.append(f"fixture-policy:{key}")
    if parsed["signatures"] != SIGNATURES or fixture.get("signatures") != SIGNATURES:
        errors.append("signatures")
    if parsed["boundary"] != BOUNDARY or fixture.get("boundary") != BOUNDARY:
        errors.append("boundary")
    if fixture.get("executor_added") is not False or fixture.get("authorization_gate_added") is not False:
        errors.append("gate-added")
    expected_unknowns = fixture_document()["unknowns"]
    if parsed["unknowns"] != expected_unknowns or fixture.get("unknowns") != expected_unknowns:
        errors.append("unknowns")
    if parsed["examples"] != EXAMPLES or fixture.get("examples") != EXAMPLES:
        errors.append("examples")
    for token in ("0x1021", "0xFFFF", "0x29B1", "0x31C3"):
        if token not in page_text:
            errors.append(f"prose:{token}")
    if "retries" in page_text.lower() or re.search(r"\b201\b", page_text):
        errors.append("prose-authorization")
    errors.extend(relative_link_errors(page_text, page_path))
    errors.extend("page-" + item for item in behavior_errors(parsed["policy"], "page"))
    errors.extend("fixture-" + item for item in behavior_errors(fixture.get("policy", {}), "fixture"))
    errors.extend(alias_errors(parsed["policy"], "page"))
    errors.extend(alias_errors(fixture.get("policy", {}), "fixture"))
    return errors


def apply_page_replacement(text, old, new):
    if old not in text:
        raise AssertionError(old)
    return text.replace(old, new, 1)


def load_owned():
    return PAGE.read_text(), json.loads(FIXTURE.read_text())


class BudgetAndChecksumHelpers(unittest.TestCase):
    def test_grouped_1024_lengths_and_bytes(self):
        data = bytes(raw_byte(index) for index in range(1024))
        got = plan_reference(GROUPED, data)
        lengths = [len(chunk) for chunk in got["chunks"]]
        self.assertEqual(lengths, [206, 206, 206, 206, 200])
        self.assertEqual(got["consumed"], 1024)
        self.assertEqual(got["unplanned"], 0)
        self.assertEqual(got["procedure"], GROUPED)
        offset = 0
        for chunk in got["chunks"]:
            self.assertEqual(bytes(chunk), data[offset : offset + len(chunk)])
            self.assertGreater(len(chunk), 0)
            offset += len(chunk)

    def test_grouped_1025_leaves_one_unplanned_byte(self):
        data = bytes(raw_byte(index) for index in range(1025))
        got = plan_reference(GROUPED, data)
        self.assertEqual([len(chunk) for chunk in got["chunks"]], [206, 206, 206, 206, 200])
        self.assertEqual(got["consumed"], 1024)
        self.assertEqual(got["unplanned"], 1)
        self.assertNotIn(data[-1], b"".join(bytes(chunk) for chunk in got["chunks"])[-1:])
        self.assertEqual(bytes(got["chunks"][-1])[-1], data[1023])

    def test_later_group_is_not_planned_until_the_caller_passes_the_suffix(self):
        data = bytearray(raw_byte(index) for index in range(2048))
        first = plan_reference(GROUPED, data)
        second = plan_reference(GROUPED, data)
        self.assertEqual(first["unplanned"], 1024)
        self.assertEqual([len(chunk) for chunk in second["chunks"]], [206, 206, 206, 206, 200])
        suffix = plan_reference(GROUPED, data[first["consumed"] :])
        self.assertEqual(suffix["consumed"], 1024)
        self.assertEqual(suffix["unplanned"], 0)
        self.assertEqual(bytes(suffix["chunks"][0]), bytes(data[1024:1230]))

    def test_short_group_boundaries(self):
        expectations = {
            824: [206, 206, 206, 206],
            825: [206, 206, 206, 206, 1],
            207: [206, 1],
            206: [206],
        }
        for length, lengths in expectations.items():
            with self.subTest(length=length):
                got = plan_reference(GROUPED, bytes(raw_byte(index) for index in range(length)))
                self.assertEqual([len(chunk) for chunk in got["chunks"]], lengths)
                self.assertEqual(got["unplanned"], 0)
                self.assertEqual(got["consumed"], length)

    def test_empty_input_has_zero_chunks_and_no_peer_packet(self):
        for procedure in (GROUPED, SINGLE):
            with self.subTest(procedure=procedure):
                got = plan_reference(procedure, b"")
                self.assertEqual(got["chunks"], [])
                self.assertEqual(got["consumed"], 0)
                self.assertEqual(got["unplanned"], 0)
                self.assertNotIn("peer_empty_packet", got)

    def test_single_205_remainder_and_group_isolation(self):
        over = plan_reference(SINGLE, bytes(raw_byte(index) for index in range(206)))
        self.assertEqual([len(chunk) for chunk in over["chunks"]], [205])
        self.assertEqual(over["consumed"], 205)
        self.assertEqual(over["unplanned"], 1)
        exact = plan_reference(SINGLE, bytes(raw_byte(index) for index in range(205)))
        self.assertEqual(exact["unplanned"], 0)
        wide = plan_reference(SINGLE, bytes(raw_byte(index) for index in range(1024)))
        self.assertEqual([len(chunk) for chunk in wide["chunks"]], [205])
        self.assertEqual(wide["unplanned"], 819)
        self.assertEqual(wide["procedure"], SINGLE)

    def test_procedure_choice_changes_the_plan(self):
        data = bytes(raw_byte(index) for index in range(206))
        grouped = plan_reference(GROUPED, data)
        single = plan_reference(SINGLE, data)
        self.assertNotEqual(
            [len(chunk) for chunk in grouped["chunks"]],
            [len(chunk) for chunk in single["chunks"]],
        )
        self.assertEqual(grouped["procedure"], GROUPED)
        self.assertEqual(single["procedure"], SINGLE)
        unknown = plan_reference("other", data)
        self.assertEqual(unknown["reason"], "unknown_procedure")
        self.assertEqual(unknown["chunks"], [])
        self.assertEqual(unknown["procedure"], "other")
        self.assertEqual(bytes(unknown["raw"]), data)

    def test_each_input_byte_is_copied_into_the_owned_chunk(self):
        data = bytearray(raw_byte(index) for index in range(1024))
        for index in (0, 1, 205, 206, 823, 824, 1023):
            with self.subTest(index=index):
                mutated = bytearray(data)
                mutated[index] ^= 0x01
                original = plan_reference(GROUPED, data)
                changed = plan_reference(GROUPED, mutated)
                flat_original = b"".join(bytes(chunk) for chunk in original["chunks"])
                flat_changed = b"".join(bytes(chunk) for chunk in changed["chunks"])
                self.assertEqual(flat_original[index], data[index])
                self.assertNotEqual(flat_changed[index], flat_original[index])
                self.assertEqual(flat_changed[index], mutated[index])

    def test_each_declared_chunk_cap_changes_the_plan(self):
        data = bytearray(raw_byte(index) for index in range(1024))
        baseline = [len(chunk) for chunk in plan_reference(GROUPED, data)["chunks"]]
        caps = [206, 206, 206, 206, 200]
        for slot in range(4):
            with self.subTest(slot=slot):
                policy = dict(REQUIRED_POLICY)
                changed = caps.copy()
                changed[slot] = 205
                policy["grouped_1024.chunk_caps"] = ",".join(str(item) for item in changed)
                got = interpret_plan(policy, GROUPED, data)
                self.assertNotEqual([len(chunk) for chunk in got["chunks"]], baseline)
                self.assertEqual(len(got["chunks"][slot]), 205)
        tighter = dict(REQUIRED_POLICY)
        tighter["grouped_1024.chunk_caps"] = "206,206,206,206,199"
        tightened = interpret_plan(tighter, GROUPED, data)
        self.assertEqual([len(chunk) for chunk in tightened["chunks"]], [206, 206, 206, 206, 199])
        self.assertEqual(tightened["unplanned"], 1)

    def test_returned_chunk_edits_do_not_change_the_input_or_the_next_call(self):
        source = bytearray(raw_byte(index) for index in range(300))
        first = plan_reference(GROUPED, source)
        edited = first["chunks"][0][0]
        first["chunks"][0][0] ^= 0xFF
        self.assertEqual(source[0], raw_byte(0))
        second = plan_reference(GROUPED, source)
        self.assertEqual(second["chunks"][0][0], raw_byte(0))
        self.assertNotEqual(first["chunks"][0][0], second["chunks"][0][0])
        self.assertIsNot(first["chunks"][0], second["chunks"][0])
        self.assertNotEqual(edited, first["chunks"][0][0])

    def test_progress_acceptance_actual_and_prior_are_independent(self):
        accepted = advance_reference(10, True, 17)
        rejected = advance_reference(10, False, 17)
        shorter = advance_reference(10, True, 16)
        zero = advance_reference(10, True, 0)
        prior = advance_reference(11, True, 17)
        self.assertEqual(accepted["next"], 27)
        self.assertEqual(rejected["next"], 10)
        self.assertEqual(rejected["outcome"], "unchanged")
        self.assertEqual(shorter["next"], 26)
        self.assertEqual(zero["next"], 10)
        self.assertEqual(prior["next"], 28)
        self.assertNotIn("offset", accepted)
        self.assertNotIn("chunk_index", accepted)

    def test_progress_rejects_non_boolean_acceptance(self):
        for bad in ("false", "true", None, 0, 1, 1.0, []):
            got = advance_reference(10, bad, 17)
            self.assertEqual(got["outcome"], "rejected", bad)
            self.assertEqual(got["reason"], "malformed_boolean", bad)
            self.assertIsNone(got["next"], bad)
            self.assertEqual(got["last_known_good"], 10, bad)

    def test_malformed_actual_counts_preserve_valid_prior_progress(self):
        for prior in (0, 10, UINT64_MAX):
            for accepted in (True, False):
                for actual in (None, True, False, "17", 17.0, []):
                    with self.subTest(prior=prior, accepted=accepted, actual=actual):
                        got = advance_reference(prior, accepted, actual)
                        self.assertEqual(got["outcome"], "rejected")
                        self.assertEqual(got["reason"], "malformed_integer")
                        self.assertEqual(got["last_known_good"], prior)
                        self.assertIsNone(got["next"])
        for prior in (None, True, -1, UINT64_MAX + 1):
            with self.subTest(prior=prior):
                got = advance_reference(prior, True, None)
                self.assertIsNone(got["last_known_good"])
                self.assertIsNone(got["next"])

    def test_progress_overflow_and_negative_counts_fail_closed(self):
        overflow = advance_reference(UINT64_MAX, True, 1)
        self.assertEqual(overflow["reason"], "overflow")
        self.assertIsNone(overflow["next"])
        self.assertEqual(overflow["last_known_good"], UINT64_MAX)
        held = advance_reference(UINT64_MAX, False, 1)
        self.assertEqual(held["next"], UINT64_MAX)
        self.assertEqual(held["outcome"], "unchanged")
        negative_actual = advance_reference(10, True, -1)
        self.assertEqual(negative_actual["reason"], "negative_count")
        self.assertIsNone(negative_actual["next"])
        self.assertEqual(negative_actual["last_known_good"], 10)
        negative_prior = advance_reference(-1, True, 17)
        self.assertIsNone(negative_prior["last_known_good"])
        self.assertIsNone(negative_prior["next"])
        rejected_negative = advance_reference(10, False, -1)
        self.assertEqual(rejected_negative["reason"], "negative_count")
        self.assertIsNone(rejected_negative["next"])
        malformed = advance_reference(True, False, 4)
        self.assertEqual(malformed["reason"], "malformed_integer")
        self.assertIsNone(malformed["next"])

    def test_checksum_anchor_values(self):
        self.assertEqual(checksum_reference(DIGITS, 0, 9)["value"], CRC_DIGITS)
        self.assertEqual(checksum_reference(b"", 0, 0)["value"], CRC_EMPTY)
        self.assertEqual(checksum_reference(DIGITS, 0, 9, 0)["value"], CRC_INITIAL_ZERO)
        self.assertEqual(checksum_reference(DIGITS, 0, 9, DEFAULT_INITIAL)["value"], CRC_DIGITS)
        self.assertEqual(checksum_reference(b"", 0, 0, 0)["value"], CRC_EMPTY_INITIAL_ZERO)
        self.assertEqual(CRC_DIGITS, 0x29B1)
        self.assertEqual(CRC_INITIAL_ZERO, 0x31C3)
        self.assertEqual(CRC_EMPTY, 0xFFFF)

    def test_checksum_span_start_length_and_initial_each_change_the_value(self):
        whole = checksum_reference(DIGITS, 0, 9)["value"]
        shorter = checksum_reference(DIGITS, 0, 8)
        shifted = checksum_reference(DIGITS, 1, 8)
        initial = checksum_reference(DIGITS, 0, 9, 1)
        self.assertEqual(shorter["value"], CRC_LENGTH_EIGHT)
        self.assertEqual(shifted["value"], CRC_START_ONE)
        self.assertEqual(initial["value"], CRC_INITIAL_ONE)
        self.assertNotEqual(shorter["value"], whole)
        self.assertNotEqual(shifted["value"], whole)
        self.assertNotEqual(initial["value"], whole)
        self.assertEqual(shorter["start"], 0)
        self.assertEqual(shorter["length"], 8)
        self.assertEqual(shifted["start"], 1)

    def test_each_checksum_input_byte_changes_the_value(self):
        for index, expected in enumerate(FLIP_CRC):
            with self.subTest(index=index):
                payload = bytearray(DIGITS)
                payload[index] ^= 0x01
                got = checksum_reference(bytes(payload), 0, 9)
                self.assertEqual(got["value"], expected)
                self.assertNotEqual(got["value"], CRC_DIGITS)
                self.assertEqual(bytes(got["raw"]), bytes(payload))

    def test_malformed_spans_keep_raw_bytes_and_omit_the_value(self):
        source = bytearray(DIGITS)
        for start, length, reason in ((0, -1, "negative_span"), (-1, 9, "negative_span"), (0, 10, "span_out_of_range"), (8, 2, "span_out_of_range")):
            with self.subTest(start=start, length=length):
                got = checksum_reference(source, start, length)
                self.assertEqual(got["reason"], reason)
                self.assertIsNone(got["value"])
                self.assertEqual(got["start"], start)
                self.assertEqual(got["length"], length)
                self.assertEqual(bytes(got["raw"]), DIGITS)
                got["raw"][0] ^= 0xFF
                self.assertEqual(source[0], DIGITS[0])

    def test_helper_results_carry_no_grade_or_native_claim(self):
        planned = plan_reference(GROUPED, b"abc")
        moved = advance_reference(10, True, 17)
        summed = checksum_reference(DIGITS, 0, 9)
        for got in (planned, moved, summed):
            for key in ("numeric_grade", "semantic_grade", "native_grade", "physical_qualification", "offset"):
                self.assertNotIn(key, got)


class PublishedContract(unittest.TestCase):
    def setUp(self):
        self.page, self.fixture = load_owned()

    def test_codec_round_trip_covers_every_example_field(self):
        for row in EXAMPLES:
            with self.subTest(example=row["id"]):
                self.assertEqual(decode_example(encode_example(row)), row)

    def test_page_and_fixture_match_the_contract_and_the_helpers(self):
        self.assertEqual(self.page, render_page())
        self.assertEqual(self.fixture, fixture_document())
        self.assertEqual(contract_errors(self.page, self.fixture), [])
        for row in EXAMPLES:
            with self.subTest(example=row["id"]):
                self._execute_published_row(row)

    def _execute_published_row(self, row):
        self.assertEqual(row["native_grade"], "Unknown")
        self.assertEqual(row["physical_qualification"], "Unknown")
        self.assertEqual(row["presence"], "not_claimed")
        self.assertEqual(row["freshness"], "not_applicable")
        self.assertEqual(row["execution"], "not_run")
        if row["selection"]["kind"] == "input":
            got = plan_reference(row["procedure"], materialize(row["raw"]))
            self.assertEqual(got["outcome"], row["outcome"])
            self.assertEqual(got["reason"], row["reason"])
            self.assertEqual([len(chunk) for chunk in got["chunks"]], row["result"]["chunk_lengths"])
            self.assertEqual(got["consumed"], row["result"]["consumed"])
            self.assertEqual(got["unplanned"], row["result"]["unplanned"])
            return
        if row["selection"]["kind"] == "progress":
            fields = row["selection"]
            got = advance_reference(fields["prior"], fields["accepted"], fields["actual"])
            self.assertEqual(got["outcome"], row["outcome"])
            self.assertEqual(got["reason"], row["reason"])
            self.assertEqual(got["last_known_good"], row["result"]["last_known_good"])
            self.assertEqual(got["next"], row["result"]["next"])
            return
        fields = row["selection"]
        got = checksum_reference(materialize(row["raw"]), fields["start"], fields["length"], fields["initial"])
        self.assertEqual(got["outcome"], row["outcome"])
        self.assertEqual(got["reason"], row["reason"])
        if row["result"]["value"] is None:
            self.assertIsNone(got["value"])
        else:
            self.assertEqual(f"{got['value']:04X}", row["result"]["value"])
        self.assertEqual(bytes(got["raw"]), materialize(row["raw"]))

    def test_relative_page_links_resolve_locally(self):
        self.assertEqual(relative_link_errors(self.page, PAGE), [])
        self.assertIn("(fixtures/an24_b51b_local_budget_crc.json)", self.page)

    def _mutant_detected(self, errors, side, fragment):
        if fragment.startswith("policy:"):
            needle = fragment if side == "page" else "fixture-" + fragment
            return needle in errors
        if fragment.startswith("alias-probe"):
            return f"alias-probe:{side}" in errors
        tail = fragment.split(":", 1)[1]
        prefix = f"{side}-behavior:{side}:"
        return any(error.startswith(prefix) and tail in error for error in errors)

    def test_mutants_of_page_or_fixture_fail_closed(self):
        mutants = {
            "fifth_cap_201": ("grouped_1024.chunk_caps", "206,206,206,206,200", "206,206,206,206,201", "policy:grouped_1024.chunk_caps"),
            "slot_role_retries": ("grouped_1024.slot_role", "chunks", "retries", "behavior:grouped_1024:1024"),
            "single_cap_206": ("single_205.chunk_caps", "205", "206", "behavior:single_205:206"),
            "inherit_grouped": ("single_205.inherits_grouped_1024", "false", "true", "behavior:single_205:206"),
            "auto_plan": ("auto_plan_later_groups", "false", "true", "behavior:grouped_1024:2048"),
            "second_group": ("grouped_1024.groups_per_call", "1", "2", "behavior:grouped_1024:2048"),
            "rejected_advances": ("progress.advances_on_rejected", "false", "true", "behavior:progress:10:False:17"),
            "overflow_wrap": ("progress.overflow", "reject", "wrap", f"behavior:progress:{UINT64_MAX}:True:1"),
            "width_65": ("progress.width_bits", "64", "65", f"behavior:progress:{UINT64_MAX}:True:1"),
            "reflect_input": ("crc.reflect_input", "false", "true", "behavior:crc:0:9:None"),
            "reflect_output": ("crc.reflect_output", "false", "true", "behavior:crc:0:9:None"),
            "final_xor": ("crc.final_xor", "0", "65535", "behavior:crc:0:9:None"),
            "extra_byte": ("crc.extra_byte", "false", "true", "behavior:crc:0:9:None"),
            "byte_swap": ("crc.byte_swap", "false", "true", "behavior:crc:0:9:None"),
            "covers_whole_payload": ("crc.covers", "caller_selected_span_only", "whole_payload", "behavior:crc:1:8:None"),
            "alias_buffers": ("alias_chunk_buffers", "false", "true", "alias-probe:"),
            "copy_slices_false": ("copy_slices", "true", "false", "alias-probe:"),
            "peer_empty_claim": ("peer_empty_packet_claim", "false", "true", "behavior:peer-empty"),
            "default_initial_0": ("crc.initial_default", "65535", "0", "behavior:crc:0:9:None"),
            "bit_order_lsb": ("crc.bit_order", "msb_first", "lsb_first", "behavior:crc:0:9:None"),
        }
        for name, (key, old, new, fragment) in mutants.items():
            for side in ("page", "fixture"):
                with self.subTest(mutant=name, side=side):
                    page, fixture = load_owned()
                    if side == "page":
                        page = apply_page_replacement(page, f"| {key} | {old} |", f"| {key} | {new} |")
                    else:
                        fixture = copy.deepcopy(fixture)
                        fixture["policy"][key] = new
                    errors = contract_errors(page, fixture, PAGE)
                    self.assertTrue(self._mutant_detected(errors, side, fragment), errors)

        with self.subTest(mutant="final_xor_collusion"):
            page, fixture = load_owned()
            page = apply_page_replacement(page, "| crc.final_xor | 0 |", "| crc.final_xor | 65535 |")
            page = page.replace("value=29B1", "value=D64E")
            fixture = copy.deepcopy(fixture)
            fixture["policy"]["crc.final_xor"] = "65535"
            for row in fixture["examples"]:
                if row["result"].get("value") == "29B1":
                    row["result"]["value"] = "D64E"
            errors = contract_errors(page, fixture)
            self.assertTrue(any("crc:0:9:None" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
