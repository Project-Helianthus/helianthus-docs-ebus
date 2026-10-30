"""Finite checks for the B509 OP33 constraint-word helper contract.

The decoder under test is the pure helper defined by this module. The
architecture page and fixture publish the same contract. Each variation names
the production defect it catches, and the assertions execute that check.
"""

from __future__ import annotations

import copy
import json
import os
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = ROOT / "architecture" / "an08_b509_constraint_word_views.md"
FIXTURE_PATH = ROOT / "architecture" / "fixtures" / "an08_b509_constraint_word_views.json"

WORD_FIELDS = ("minimum", "maximum", "default", "step", "factor")
SELECTED_FAMILY = "B509"
SELECTED_VARIANT = "positive"
SELECTED_OPERATION = "OP33"
OP32_OPERATION = "OP32"
SIGNATURE = (
    "interpret_b509_op33_positive_alternative(selection, addresses, words) -> view"
)
PROVENANCE = "synthetic finite helper examples; no device observation"

NORMATIVE = {
    "selected_family": ("B509", "none", "Proven", "Unknown"),
    "selected_variant": ("positive", "none", "Proven", "Unknown"),
    "selected_operation": ("OP33", "none", "Proven", "Unknown"),
    "op32_token": ("OP32", "none", "Proven", "Unknown"),
    "op32_role": ("address-status-query", "none", "Hypothesis", "Unknown"),
    "op32_result": ("not-shared-with-op33", "none", "Proven", "Unknown"),
    "word_signedness": ("signed", "Hypothesis", "Hypothesis", "Unknown"),
    "word_endian": ("little-endian", "Hypothesis", "Hypothesis", "Unknown"),
    "word_width_bytes": ("2", "Hypothesis", "Hypothesis", "Unknown"),
    "word_scale": ("none", "Hypothesis", "Hypothesis", "Unknown"),
    "factor_role": ("raw-signed-field", "Hypothesis", "Hypothesis", "Unknown"),
    "min_above_max": ("retain-supplied-order", "Hypothesis", "Hypothesis", "Unknown"),
    "negative_step": ("retain-candidate", "Hypothesis", "Hypothesis", "Unknown"),
    "zero_factor": ("retain-candidate", "Hypothesis", "Hypothesis", "Unknown"),
    "default_outside_bounds": ("retain-candidate", "Hypothesis", "Hypothesis", "Unknown"),
    "partial_malformed": ("siblings-remain", "none", "Proven", "Unknown"),
    "independent_word_decode": ("per-word", "none", "Proven", "Unknown"),
    "address_mismatch_edit_bounds": ("not-granted", "none", "Proven", "Unknown"),
    "edit_bounds_on_match": ("not-granted", "none", "Proven", "Unknown"),
    "local_address_equality": ("raw-bytes-only", "none", "Proven", "Unknown"),
    "returned_raw": ("detached-copy", "none", "Proven", "Unknown"),
    "shared_cache": ("unchanged", "none", "Proven", "Unknown"),
    "constraint_store": ("unchanged", "none", "Proven", "Unknown"),
    "address_width": ("unspecified", "Unknown", "Proven", "Unknown"),
    "packet_offsets": ("unspecified", "Unknown", "Proven", "Unknown"),
    "native_echo": ("unresolved", "Unknown", "Unknown", "Unknown"),
    "native_success": ("not-reported", "Unknown", "Proven", "Unknown"),
    "native_qualification": ("unresolved", "Unknown", "Unknown", "Unknown"),
    "universal_family_applicability": ("unresolved", "Unknown", "Unknown", "Unknown"),
    "factor_algorithm": ("unresolved", "Unknown", "Unknown", "Unknown"),
    "writability": ("unresolved", "Unknown", "Unknown", "Unknown"),
    "peer_enforcement": ("unresolved", "Unknown", "Unknown", "Unknown"),
    "physical_adaptation": ("unresolved", "Unknown", "Unknown", "Unknown"),
    "packet_association": ("unresolved", "Unknown", "Unknown", "Unknown"),
}

REQUIRED_SENTENCES = (
    "Unsigned conversion is outside this contract.",
    "Big-endian conversion is outside this contract.",
    "The factor is not a converter and does not scale the other words.",
    "Minimum greater than maximum is not rejected and is not reordered.",
    "One malformed word does not erase the other words.",
    "An address mismatch does not grant the requested edit bounds.",
    "Returned raw bytes are detached copies.",
    "OP32 does not share the OP33 word view.",
    "Empty address strings stay explicit, and native success is not invented.",
    "Selection tokens are exact and case-sensitive.",
    "This software contract is not a stable interface before Helianthus 1.0.",
    "This helper is not an authorization gate.",
    "This helper adds no GraphQL field and no MCP tool.",
    "This page does not qualify a device.",
)

FORBIDDEN_PROSE = (
    (re.compile(r"unsigned conversion is (?:accepted|authorized|used)"), "unsigned conversion"),
    (re.compile(r"big-endian conversion is (?:accepted|authorized|used)"), "big-endian conversion"),
    (re.compile(r"factor multiplies|factor is a converter"), "factor converter"),
    (re.compile(r"minimum greater than maximum is rejected"), "reject min>max"),
    (re.compile(r"minimum greater than maximum is swapped"), "swap min>max"),
    (re.compile(r"minimum and maximum are reordered"), "reorder min>max"),
    (re.compile(r"malformed word erases"), "erase on malformed"),
    (re.compile(r"address mismatch grants"), "grant after mismatch"),
)

# case, field, raw bytes, state, signed le16 or None, numeric, semantic, native
WORD_PAGE_ROWS = (
    ("extremes", "minimum", (0x00, 0x80), "decoded", -32768, "Hypothesis", "Proven", "Unknown"),
    ("extremes", "maximum", (0xFF, 0x7F), "decoded", 32767, "Hypothesis", "Proven", "Unknown"),
    ("extremes", "default", (0xFF, 0xFF), "decoded", -1, "Hypothesis", "Proven", "Unknown"),
    ("extremes", "step", (0x02, 0x00), "decoded", 2, "Hypothesis", "Proven", "Unknown"),
    ("extremes", "factor", (0x00, 0x00), "decoded", 0, "Hypothesis", "Proven", "Unknown"),
    ("min10-max5", "minimum", (0x0A, 0x00), "decoded", 10, "Hypothesis", "Proven", "Unknown"),
    ("min10-max5", "maximum", (0x05, 0x00), "decoded", 5, "Hypothesis", "Proven", "Unknown"),
    ("min10-max5", "default", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("min10-max5", "step", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("min10-max5", "factor", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("factor-one-byte", "minimum", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("factor-one-byte", "maximum", (0x02, 0x00), "decoded", 2, "Hypothesis", "Proven", "Unknown"),
    ("factor-one-byte", "default", (0x03, 0x00), "decoded", 3, "Hypothesis", "Proven", "Unknown"),
    ("factor-one-byte", "step", (0x04, 0x00), "decoded", 4, "Hypothesis", "Proven", "Unknown"),
    ("factor-one-byte", "factor", (0x02,), "malformed", None, "Unknown", "Proven", "Unknown"),
    ("factor-two", "minimum", (0x0A, 0x00), "decoded", 10, "Hypothesis", "Proven", "Unknown"),
    ("factor-two", "maximum", (0x05, 0x00), "decoded", 5, "Hypothesis", "Proven", "Unknown"),
    ("factor-two", "default", (0x07, 0x00), "decoded", 7, "Hypothesis", "Proven", "Unknown"),
    ("factor-two", "step", (0x09, 0x00), "decoded", 9, "Hypothesis", "Proven", "Unknown"),
    ("factor-two", "factor", (0x02, 0x00), "decoded", 2, "Hypothesis", "Proven", "Unknown"),
    ("negative-step", "minimum", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("negative-step", "maximum", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("negative-step", "default", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("negative-step", "step", (0xFF, 0xFF), "decoded", -1, "Hypothesis", "Proven", "Unknown"),
    ("negative-step", "factor", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("zero-factor", "minimum", (0x04, 0x00), "decoded", 4, "Hypothesis", "Proven", "Unknown"),
    ("zero-factor", "maximum", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("zero-factor", "default", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("zero-factor", "step", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("zero-factor", "factor", (0x00, 0x00), "decoded", 0, "Hypothesis", "Proven", "Unknown"),
    ("default-outside", "minimum", (0x00, 0x00), "decoded", 0, "Hypothesis", "Proven", "Unknown"),
    ("default-outside", "maximum", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("default-outside", "default", (0x64, 0x00), "decoded", 100, "Hypothesis", "Proven", "Unknown"),
    ("default-outside", "step", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("default-outside", "factor", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("address-mismatch", "minimum", (0x0A, 0x00), "decoded", 10, "Hypothesis", "Proven", "Unknown"),
    ("address-mismatch", "maximum", (0x14, 0x00), "decoded", 20, "Hypothesis", "Proven", "Unknown"),
    ("address-mismatch", "default", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("address-mismatch", "step", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("address-mismatch", "factor", (0x01, 0x00), "decoded", 1, "Hypothesis", "Proven", "Unknown"),
    ("all-malformed", "minimum", (), "malformed", None, "Unknown", "Proven", "Unknown"),
    ("all-malformed", "maximum", (0x11,), "malformed", None, "Unknown", "Proven", "Unknown"),
    ("all-malformed", "default", (0x01, 0x02, 0x03), "malformed", None, "Unknown", "Proven", "Unknown"),
    ("all-malformed", "step", (0x04, 0x05, 0x06, 0x07), "malformed", None, "Unknown", "Proven", "Unknown"),
    ("all-malformed", "factor", (0x08,), "malformed", None, "Unknown", "Proven", "Unknown"),
)

# case, requested, returned, local_equal, grants, native_success
ADDRESS_PAGE_ROWS = (
    ("base", (0x10, 0x20), (0x10, 0x20), True, False, None),
    ("both-empty", (), (), True, False, None),
    ("requested-missing", None, (0x10, 0x20), False, False, None),
    ("returned-missing", (0x10, 0x20), None, False, False, None),
    ("address-mismatch", (0x01, 0x02), (0x01, 0x09), False, False, None),
)

# case, result_kind, shares, words present, direction, numeric, semantic, native
RESULT_PAGE_ROWS = (
    ("base", "op33-positive-alternative", True, True, "request", "Hypothesis", "Proven", "Unknown"),
    ("direction-response", "op33-positive-alternative", True, True, "response", "Hypothesis", "Proven", "Unknown"),
    ("direction-empty", "op33-positive-alternative", True, True, "", "Hypothesis", "Proven", "Unknown"),
    ("op32-extremes", "op32-address-status-query", False, False, "read", "Unknown", "Proven", "Unknown"),
    ("family-b510", "selection-not-admitted", False, False, "request", "Unknown", "Proven", "Unknown"),
    ("family-missing", "selection-incomplete", False, False, "request", "Unknown", "Proven", "Unknown"),
)


def signed_le16(raw):
    value = raw[0] | (raw[1] << 8)
    if value >= 0x8000:
        value -= 0x10000
    return value


def unsigned_le16(raw):
    return raw[0] | (raw[1] << 8)


def signed_be16(raw):
    value = (raw[0] << 8) | raw[1]
    if value >= 0x8000:
        value -= 0x10000
    return value


def detach_bytes(value):
    if isinstance(value, (bytes, bytearray)):
        return list(value)
    return [item for item in value]


def decodable(raw):
    return len(raw) == 2 and all(type(item) is int and 0 <= item <= 255 for item in raw)


def word_grades(numeric):
    return {"numeric": numeric, "semantic": "Proven", "native": "Unknown"}


def interpret_word(value):
    if value is None:
        return {
            "state": "missing",
            "raw": None,
            "length": None,
            "signed_le16": None,
            "scale": None,
            "grades": word_grades("Unknown"),
        }
    raw = detach_bytes(value)
    if not decodable(raw):
        return {
            "state": "malformed",
            "raw": raw,
            "length": len(raw),
            "signed_le16": None,
            "scale": None,
            "grades": word_grades("Unknown"),
        }
    return {
        "state": "decoded",
        "raw": raw,
        "length": 2,
        "signed_le16": signed_le16(raw),
        "scale": None,
        "grades": word_grades("Hypothesis"),
    }


def interpret(selection, addresses, words):
    """Pure B509 OP33 positive-alternative field interpreter.

    The caller supplies selection, opaque address byte strings, and the five
    word slices. This function does not read a packet, a cache, or a store.
    """
    echoed = {
        "family": selection.get("family"),
        "variant": selection.get("variant"),
        "operation": selection.get("operation"),
        "direction": selection.get("direction"),
    }
    requested = addresses.get("requested", None)
    returned = addresses.get("returned", None)
    requested_raw = None if requested is None else detach_bytes(requested)
    returned_raw = None if returned is None else detach_bytes(returned)
    both_present = requested_raw is not None and returned_raw is not None
    address = {
        "requested_state": "missing" if requested_raw is None else "present",
        "returned_state": "missing" if returned_raw is None else "present",
        "requested_raw": requested_raw,
        "returned_raw": returned_raw,
        "requested_length": None if requested_raw is None else len(requested_raw),
        "returned_length": None if returned_raw is None else len(returned_raw),
        "local_equal": bool(both_present and requested_raw == returned_raw),
        "native_echo": "Unknown",
        "native_success": None,
        "grants_requested_edit_bounds": False,
        "admitted_minimum": None,
        "admitted_maximum": None,
    }
    operation = echoed["operation"]
    if operation == OP32_OPERATION:
        kind = "op32-address-status-query"
        shares = False
        decoded_words = None
        numeric = "Unknown"
    elif any(echoed[key] is None for key in echoed):
        kind = "selection-incomplete"
        shares = False
        decoded_words = None
        numeric = "Unknown"
    elif (
        echoed["family"] != SELECTED_FAMILY
        or echoed["variant"] != SELECTED_VARIANT
        or operation != SELECTED_OPERATION
    ):
        kind = "selection-not-admitted"
        shares = False
        decoded_words = None
        numeric = "Unknown"
    else:
        kind = "op33-positive-alternative"
        shares = True
        decoded_words = {
            name: interpret_word(words[name] if name in words else None)
            for name in WORD_FIELDS
        }
        numeric = (
            "Hypothesis"
            if any(item["state"] == "decoded" for item in decoded_words.values())
            else "Unknown"
        )
    return {
        "result_kind": kind,
        "shares_op33_result": shares,
        "selection": echoed,
        "address": address,
        "words": decoded_words,
        "constraint_store_changed": False,
        "shared_cache_changed": False,
        "grades": {"numeric": numeric, "semantic": "Proven", "native": "Unknown"},
    }


def selected_input(direction="request", operation=SELECTED_OPERATION):
    return {
        "selection": {
            "family": SELECTED_FAMILY,
            "variant": SELECTED_VARIANT,
            "operation": operation,
            "direction": direction,
        },
        "addresses": {"requested": [0x10, 0x20], "returned": [0x10, 0x20]},
        "words": {name: [0x01, 0x00] for name in WORD_FIELDS},
    }


def base_input():
    return selected_input()


def _words(overrides):
    words = {name: [0x01, 0x00] for name in WORD_FIELDS}
    for name, raw in overrides.items():
        words[name] = None if raw is None else list(raw)
    return words


def _anchor(direction, addresses, words, operation=SELECTED_OPERATION):
    return {
        "selection": {
            "family": SELECTED_FAMILY,
            "variant": SELECTED_VARIANT,
            "operation": operation,
            "direction": direction,
        },
        "addresses": {
            "requested": None if addresses[0] is None else list(addresses[0]),
            "returned": None if addresses[1] is None else list(addresses[1]),
        },
        "words": words,
    }


def anchor_inputs():
    """Hand-listed acceptance inputs. Values are literals, not derived encodings."""
    extremes_words = _words({
        "minimum": (0x00, 0x80),
        "maximum": (0xFF, 0x7F),
        "default": (0xFF, 0xFF),
        "step": (0x02, 0x00),
        "factor": (0x00, 0x00),
    })
    extremes = _anchor("read", ([0x01, 0x02], [0x01, 0x02]), extremes_words)
    op32 = copy.deepcopy(extremes)
    op32["selection"]["operation"] = OP32_OPERATION
    return [
        ("extremes", extremes),
        ("op32-extremes", op32),
        ("min10-max5", _anchor("request", ([0x10, 0x20], [0x10, 0x20]), _words({
            "minimum": (0x0A, 0x00), "maximum": (0x05, 0x00),
        }))),
        ("factor-one-byte", _anchor("request", ([0x10, 0x20], [0x10, 0x20]), _words({
            "minimum": (0x01, 0x00), "maximum": (0x02, 0x00),
            "default": (0x03, 0x00), "step": (0x04, 0x00), "factor": (0x02,),
        }))),
        ("factor-two", _anchor("request", ([0x10, 0x20], [0x10, 0x20]), _words({
            "minimum": (0x0A, 0x00), "maximum": (0x05, 0x00),
            "default": (0x07, 0x00), "step": (0x09, 0x00), "factor": (0x02, 0x00),
        }))),
        ("negative-step", _anchor("request", ([0x10, 0x20], [0x10, 0x20]), _words({
            "step": (0xFF, 0xFF),
        }))),
        ("zero-factor", _anchor("request", ([0x10, 0x20], [0x10, 0x20]), _words({
            "minimum": (0x04, 0x00), "factor": (0x00, 0x00),
        }))),
        ("default-outside", _anchor("request", ([0x10, 0x20], [0x10, 0x20]), _words({
            "minimum": (0x00, 0x00), "maximum": (0x01, 0x00), "default": (0x64, 0x00),
        }))),
        ("address-mismatch", _anchor("request", ([0x01, 0x02], [0x01, 0x09]), _words({
            "minimum": (0x0A, 0x00), "maximum": (0x14, 0x00),
        }))),
        ("all-malformed", _anchor("request", ([0x10, 0x20], [0x10, 0x20]), _words({
            "minimum": (), "maximum": (0x11,), "default": (0x01, 0x02, 0x03),
            "step": (0x04, 0x05, 0x06, 0x07), "factor": (0x08,),
        }))),
    ]


def _word_value(word, suffix, raw, signed, catches):
    return {
        "id": f"{word}-{suffix}",
        "field": f"words.{word}.{suffix}",
        "catches": catches,
        "kind": "word-value",
        "word": word,
        "raw": list(raw),
        "signed_le16": signed,
    }


def _word_bad(word, suffix, raw, catches):
    return {
        "id": f"{word}-{suffix}",
        "field": f"words.{word}.{suffix}",
        "catches": catches,
        "kind": "word-malformed",
        "word": word,
        "raw": list(raw),
    }


def _word_missing(word):
    return {
        "id": f"{word}-missing",
        "field": f"words.{word}.presence",
        "catches": f"erasing sibling words or decoding a zero when {word} is absent",
        "kind": "word-missing",
        "word": word,
    }


def variation_specs():
    """One isolated input change per identity field, byte, length, or presence."""
    specs = []
    low = {
        "minimum": (0x11, 0x00, 17),
        "maximum": (0x12, 0x00, 18),
        "default": (0x13, 0x00, 19),
        "step": (0x14, 0x00, 20),
        "factor": (0x15, 0x00, 21),
    }
    high = {
        "minimum": (0x01, 0x80, -32767),
        "maximum": (0x02, 0x80, -32766),
        "default": (0x03, 0x80, -32765),
        "step": (0x04, 0x80, -32764),
        "factor": (0x05, 0x80, -32763),
    }
    for word, (lo, hi, signed) in low.items():
        specs.append(_word_value(
            word, "low-byte", (lo, hi), signed,
            f"ignoring the {word} low byte or decoding that word as big-endian",
        ))
    for word, (lo, hi, signed) in high.items():
        specs.append(_word_value(
            word, "high-byte", (lo, hi), signed,
            f"decoding {word} as unsigned or big-endian, or ignoring its high byte",
        ))
    specs.append(_word_value(
        "factor", "isolated-two", (0x02, 0x00), 2,
        "applying factor as a converter onto the other words",
    ))
    for word in WORD_FIELDS:
        specs.append(_word_missing(word))
        specs.append(_word_bad(
            word, "len0", (),
            f"treating an empty {word} slice as missing or as the value zero",
        ))
        specs.append(_word_bad(
            word, "len1", (0x09,),
            f"decoding a one-byte {word} or clearing the other words",
        ))
        specs.append(_word_bad(
            word, "len3", (0x01, 0x02, 0x03),
            f"decoding the first two bytes of {word} and dropping the third",
        ))
        specs.append(_word_bad(
            word, "non-byte", (0x01, 256),
            f"masking a non-byte in {word} and decoding the masked pair",
        ))
    specs.extend([
        {
            "id": "family-b510",
            "field": "selection.family",
            "catches": "treating every family token as the selected B509 view",
            "kind": "selection-value",
            "key": "family",
            "value": "B510",
            "result_kind": "selection-not-admitted",
        },
        {
            "id": "family-lower",
            "field": "selection.family.case",
            "catches": "case-folding the family token into B509",
            "kind": "selection-value",
            "key": "family",
            "value": "b509",
            "result_kind": "selection-not-admitted",
        },
        {
            "id": "variant-other",
            "field": "selection.variant",
            "catches": "admitting a non-positive variant as the positive alternative",
            "kind": "selection-value",
            "key": "variant",
            "value": "other",
            "result_kind": "selection-not-admitted",
        },
        {
            "id": "variant-case",
            "field": "selection.variant.case",
            "catches": "case-folding the variant token into positive",
            "kind": "selection-value",
            "key": "variant",
            "value": "Positive",
            "result_kind": "selection-not-admitted",
        },
        {
            "id": "operation-op34",
            "field": "selection.operation",
            "catches": "sharing the OP33 word view with a different operation token",
            "kind": "selection-value",
            "key": "operation",
            "value": "OP34",
            "result_kind": "selection-not-admitted",
        },
        {
            "id": "operation-lower",
            "field": "selection.operation.case",
            "catches": "case-folding the operation token into OP33",
            "kind": "selection-value",
            "key": "operation",
            "value": "op33",
            "result_kind": "selection-not-admitted",
        },
        {
            "id": "operation-op32",
            "field": "selection.operation.op32",
            "catches": "sharing the OP33 constraint view with the OP32 address-status query",
            "kind": "op32",
            "key": "operation",
            "value": "OP32",
        },
        {
            "id": "direction-response",
            "field": "selection.direction",
            "catches": "dropping direction or overwriting it with the base direction",
            "kind": "direction-value",
            "key": "direction",
            "value": "response",
        },
        {
            "id": "direction-empty",
            "field": "selection.direction.empty",
            "catches": "treating an empty direction string as missing or as native success",
            "kind": "direction-value",
            "key": "direction",
            "value": "",
        },
        {
            "id": "family-missing",
            "field": "selection.family.presence",
            "catches": "defaulting a missing family to B509 and emitting the word view",
            "kind": "selection-missing",
            "key": "family",
        },
        {
            "id": "variant-missing",
            "field": "selection.variant.presence",
            "catches": "defaulting a missing variant to positive and emitting the word view",
            "kind": "selection-missing",
            "key": "variant",
        },
        {
            "id": "operation-missing",
            "field": "selection.operation.presence",
            "catches": "defaulting a missing operation to OP33 and emitting the word view",
            "kind": "selection-missing",
            "key": "operation",
        },
        {
            "id": "direction-missing",
            "field": "selection.direction.presence",
            "catches": "defaulting a missing direction and emitting the word view",
            "kind": "selection-missing",
            "key": "direction",
        },
    ])
    address_rows = (
        ("requested-byte0", "addresses.requested.byte0", [0x11, 0x20], [0x10, 0x20], False,
         "ignoring requested address byte 0"),
        ("requested-byte1", "addresses.requested.byte1", [0x10, 0x21], [0x10, 0x20], False,
         "ignoring requested address byte 1"),
        ("requested-byte2", "addresses.requested.byte2", [0x10, 0x20, 0x30], [0x10, 0x20], False,
         "dropping requested address byte 2"),
        ("requested-byte2-next", "addresses.requested.byte2", [0x10, 0x20, 0x31], [0x10, 0x20], False,
         "collapsing two different requested third bytes"),
        ("returned-byte0", "addresses.returned.byte0", [0x10, 0x20], [0x12, 0x20], False,
         "ignoring returned address byte 0"),
        ("returned-byte1", "addresses.returned.byte1", [0x10, 0x20], [0x10, 0x22], False,
         "ignoring returned address byte 1"),
        ("returned-byte2", "addresses.returned.byte2", [0x10, 0x20], [0x10, 0x20, 0x30], False,
         "dropping returned address byte 2"),
        ("returned-byte2-next", "addresses.returned.byte2", [0x10, 0x20], [0x10, 0x20, 0x31], False,
         "collapsing two different returned third bytes"),
        ("requested-length", "addresses.requested.length", [0x10], [0x10, 0x20], False,
         "ignoring requested address length"),
        ("returned-length", "addresses.returned.length", [0x10, 0x20], [0x10], False,
         "ignoring returned address length"),
        ("requested-empty", "addresses.requested.empty", [], [0x10, 0x20], False,
         "treating an empty requested address as the base address"),
        ("returned-empty", "addresses.returned.empty", [0x10, 0x20], [], False,
         "treating an empty returned address as the base address"),
        ("both-empty", "addresses.both.empty", [], [], True,
         "inventing native success for two empty address strings, or calling them unequal"),
        ("requested-missing", "addresses.requested.presence", None, [0x10, 0x20], False,
         "treating a missing requested address as empty or equal"),
        ("returned-missing", "addresses.returned.presence", [0x10, 0x20], None, False,
         "treating a missing returned address as empty or equal"),
        ("both-missing", "addresses.both.presence", None, None, False,
         "treating two missing addresses as a local match"),
    )
    for spec_id, field, requested, returned, local_equal, catches in address_rows:
        specs.append({
            "id": spec_id,
            "field": field,
            "catches": catches,
            "kind": "address",
            "requested": None if requested is None else list(requested),
            "returned": None if returned is None else list(returned),
            "local_equal": local_equal,
        })
    return specs


REQUIRED_VARIATION_FIELDS = (
    "selection.family",
    "selection.family.case",
    "selection.variant",
    "selection.variant.case",
    "selection.operation",
    "selection.operation.case",
    "selection.operation.op32",
    "selection.direction",
    "selection.direction.empty",
    "selection.family.presence",
    "selection.variant.presence",
    "selection.operation.presence",
    "selection.direction.presence",
    "addresses.requested.byte0",
    "addresses.requested.byte1",
    "addresses.requested.byte2",
    "addresses.returned.byte0",
    "addresses.returned.byte1",
    "addresses.returned.byte2",
    "addresses.requested.length",
    "addresses.returned.length",
    "addresses.requested.empty",
    "addresses.returned.empty",
    "addresses.both.empty",
    "addresses.requested.presence",
    "addresses.returned.presence",
    "addresses.both.presence",
    *(
        f"words.{word}.{suffix}"
        for word in WORD_FIELDS
        for suffix in ("low-byte", "high-byte", "presence", "len0", "len1", "len3", "non-byte")
    ),
    "words.factor.isolated-two",
)


def apply_spec(base, spec):
    updated = copy.deepcopy(base)
    kind = spec["kind"]
    if kind in ("word-value", "word-malformed"):
        updated["words"][spec["word"]] = list(spec["raw"])
    elif kind == "word-missing":
        updated["words"][spec["word"]] = None
    elif kind in ("selection-value", "op32", "direction-value"):
        updated["selection"][spec["key"]] = spec["value"]
    elif kind == "selection-missing":
        updated["selection"][spec["key"]] = None
    elif kind == "address":
        updated["addresses"]["requested"] = copy.deepcopy(spec["requested"])
        updated["addresses"]["returned"] = copy.deepcopy(spec["returned"])
    else:
        raise AssertionError(kind)
    return updated


def project(case):
    return {
        "selection": case["selection"],
        "addresses": case["addresses"],
        "words": case["words"],
    }


def interpret_input(value):
    return interpret(value["selection"], value["addresses"], value["words"])


def catalog_cases():
    cases = [{"id": "base", **base_input()}]
    cases.extend({"id": spec_id, **value} for spec_id, value in anchor_inputs())
    base = base_input()
    cases.extend({"id": spec["id"], **apply_spec(base, spec)} for spec in variation_specs())
    for case in cases:
        case["expect"] = interpret_input(case)
    return cases


def fixture_document():
    return {
        "name": "an08-b509-op33-constraint-word-views",
        "provenance": PROVENANCE,
        "native_qualification": "Unknown",
        "signature": SIGNATURE,
        "word_fields": list(WORD_FIELDS),
        "normative": {
            key: {
                "value": value,
                "numeric": numeric,
                "semantic": semantic,
                "native": native,
            }
            for key, (value, numeric, semantic, native) in NORMATIVE.items()
        },
        "cases": catalog_cases(),
    }


def hex_cell(raw):
    if raw is None:
        return "missing"
    if len(raw) == 0:
        return "empty"
    return " ".join(f"{byte:02X}" for byte in raw)


def signed_cell(value):
    if value is None:
        return "none"
    return str(value)


def normative_markdown():
    lines = [
        "| key | value | numeric grade | semantic grade | native grade |",
        "| --- | --- | --- | --- | --- |",
    ]
    for key, (value, numeric, semantic, native) in NORMATIVE.items():
        lines.append(f"| {key} | {value} | {numeric} | {semantic} | {native} |")
    return "\n".join(lines)


def word_table_markdown():
    lines = [
        "| case | field | raw bytes | state | signed le16 | numeric grade | semantic grade | native grade |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case, field, raw, state, signed, numeric, semantic, native in WORD_PAGE_ROWS:
        lines.append(
            f"| {case} | {field} | {hex_cell(raw)} | {state} | {signed_cell(signed)} "
            f"| {numeric} | {semantic} | {native} |"
        )
    return "\n".join(lines)


def address_table_markdown():
    lines = [
        "| case | requested | returned | local equal | grants edit bounds | native success |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for case, requested, returned, local_equal, grants, native_success in ADDRESS_PAGE_ROWS:
        lines.append(
            "| {case} | {requested} | {returned} | {local_equal} | {grants} | {native_success} |".format(
                case=case,
                requested=hex_cell(requested),
                returned=hex_cell(returned),
                local_equal="true" if local_equal else "false",
                grants="true" if grants else "false",
                native_success="none" if native_success is None else native_success,
            )
        )
    return "\n".join(lines)


def direction_cell(value):
    if value == "":
        return "empty"
    return value


def result_table_markdown():
    lines = [
        "| case | result kind | shares op33 | words | direction | numeric grade | semantic grade | native grade |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case, kind, shares, words_present, direction, numeric, semantic, native in RESULT_PAGE_ROWS:
        lines.append(
            "| {case} | {kind} | {shares} | {words} | {direction} | {numeric} | {semantic} | {native} |".format(
                case=case,
                kind=kind,
                shares="true" if shares else "false",
                words="present" if words_present else "none",
                direction=direction_cell(direction),
                numeric=numeric,
                semantic=semantic,
                native=native,
            )
        )
    return "\n".join(lines)


def parse_table(text, heading):
    rows = []
    capturing = False
    for line in text.splitlines():
        if line.startswith("## "):
            capturing = line.strip() == heading
            continue
        if not capturing or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] in {"key", "case"} or set(cells[0]) <= {"-", " "}:
            continue
        if all(set(cell) <= {"-", " ", ":"} for cell in cells):
            continue
        rows.append(cells)
    return rows


def parse_normative(text):
    found = {}
    for cells in parse_table(text, "## Normative keys"):
        if len(cells) != 5:
            found.setdefault("__malformed__", []).append(cells)
            continue
        found[cells[0]] = tuple(cells[1:])
    return found


def parse_hex_cell(cell):
    if cell == "missing":
        return None
    if cell == "empty":
        return ()
    return tuple(int(part, 16) for part in cell.split())


def parse_signed_cell(cell):
    if cell == "none":
        return None
    return int(cell)


def parse_bool(cell):
    if cell == "true":
        return True
    if cell == "false":
        return False
    raise ValueError(cell)


def page_problems(text):
    problems = []
    for sentence in REQUIRED_SENTENCES:
        if sentence not in text:
            problems.append(f"missing sentence: {sentence}")
    for pattern, label in FORBIDDEN_PROSE:
        if pattern.search(text):
            problems.append(f"authorizes {label}")
    if SIGNATURE not in text:
        problems.append("missing signature")
    for token in (
        "op33-positive-alternative",
        "op32-address-status-query",
        "selection-incomplete",
        "selection-not-admitted",
        "`missing`",
        "`malformed`",
        "`decoded`",
        "`present`",
    ):
        if token not in text:
            problems.append(f"missing state {token}")
    normative = parse_normative(text)
    if "__malformed__" in normative:
        problems.append("normative row width")
    for key, expected in NORMATIVE.items():
        if normative.get(key) != expected:
            problems.append(f"normative {key}")
    extra = set(normative) - set(NORMATIVE) - {"__malformed__"}
    for key in sorted(extra):
        problems.append(f"unexpected normative {key}")
    word_rows = parse_table(text, "## Published examples")
    expected_words = {
        (case, field): (raw, state, signed, numeric, semantic, native)
        for case, field, raw, state, signed, numeric, semantic, native in WORD_PAGE_ROWS
    }
    seen = set()
    for cells in word_rows:
        if len(cells) != 8:
            problems.append("word row width")
            continue
        case, field, raw_cell, state, signed_cell_text, numeric, semantic, native = cells
        seen.add((case, field))
        expected = expected_words.get((case, field))
        if expected is None:
            problems.append(f"unexpected word row {case} {field}")
            continue
        raw, exp_state, signed, exp_numeric, exp_semantic, exp_native = expected
        try:
            parsed_raw = parse_hex_cell(raw_cell)
            parsed_signed = parse_signed_cell(signed_cell_text)
        except ValueError:
            problems.append(f"unreadable word row {case} {field}")
            continue
        if parsed_raw != tuple(raw) or state != exp_state or parsed_signed != signed:
            problems.append(f"word example {case} {field}")
        if (numeric, semantic, native) != (exp_numeric, exp_semantic, exp_native):
            problems.append(f"word grades {case} {field}")
    for key in expected_words:
        if key not in seen:
            problems.append(f"missing word row {key[0]} {key[1]}")
    address_rows = {
        cells[0]: cells
        for cells in parse_table(text, "## Address examples")
        if len(cells) == 6
    }
    for case, requested, returned, local_equal, grants, native_success in ADDRESS_PAGE_ROWS:
        cells = address_rows.get(case)
        if cells is None:
            problems.append(f"missing address row {case}")
            continue
        try:
            parsed = (
                parse_hex_cell(cells[1]),
                parse_hex_cell(cells[2]),
                parse_bool(cells[3]),
                parse_bool(cells[4]),
                None if cells[5] == "none" else cells[5],
            )
        except ValueError:
            problems.append(f"unreadable address row {case}")
            continue
        if parsed != (None if requested is None else tuple(requested),
                      None if returned is None else tuple(returned),
                      local_equal, grants, native_success):
            problems.append(f"address example {case}")
    result_rows = {
        cells[0]: cells
        for cells in parse_table(text, "## Result examples")
        if len(cells) == 8
    }
    for case, kind, shares, words_present, direction, numeric, semantic, native in RESULT_PAGE_ROWS:
        cells = result_rows.get(case)
        if cells is None:
            problems.append(f"missing result row {case}")
            continue
        expected = (
            kind,
            "true" if shares else "false",
            "present" if words_present else "none",
            direction_cell(direction),
            numeric,
            semantic,
            native,
        )
        if tuple(cells[1:]) != expected:
            problems.append(f"result example {case}")
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = match.group(1)
        if "://" in target:
            problems.append(f"external link {target}")
            continue
        path = target.split("#", 1)[0]
        if path and not (PAGE_PATH.parent / path).is_file():
            problems.append(f"missing link {target}")
    if re.search(r"\b[0-9a-fA-F]{64}\b", text):
        problems.append("literal digest")
    if "BAS" + "V2" in text:
        problems.append("disallowed profile token")
    return problems


def _expect_words(case):
    try:
        return case["expect"]["words"]
    except (KeyError, TypeError):
        return None


def literal_problems(document):
    problems = []
    by_id = {case["id"]: case for case in document.get("cases", [])}
    required = {"base", "extremes", "op32-extremes", "min10-max5", "factor-one-byte",
                "factor-two", "negative-step", "zero-factor", "default-outside",
                "address-mismatch", "all-malformed"}
    required.update(spec["id"] for spec in variation_specs())
    if set(by_id) != required:
        problems.append("case id set")
        return problems

    def words_of(spec_id):
        return _expect_words(by_id[spec_id])

    extremes = words_of("extremes")
    expected_extremes = {
        "minimum": (-32768, [0x00, 0x80]),
        "maximum": (32767, [0xFF, 0x7F]),
        "default": (-1, [0xFF, 0xFF]),
        "step": (2, [0x02, 0x00]),
        "factor": (0, [0x00, 0x00]),
    }
    if not isinstance(extremes, dict):
        problems.append("extremes erased")
    else:
        for name, (signed, raw) in expected_extremes.items():
            word = extremes.get(name, {})
            if word.get("signed_le16") != signed or word.get("raw") != raw:
                problems.append(f"extremes {name} encoding")
            if word.get("state") != "decoded" or word.get("grades", {}).get("numeric") != "Hypothesis":
                problems.append(f"extremes {name} grade")
    pair = words_of("min10-max5")
    if not isinstance(pair, dict):
        problems.append("min10-max5 rejected")
    else:
        if pair.get("minimum", {}).get("signed_le16") != 10 or pair.get("minimum", {}).get("raw") != [0x0A, 0x00]:
            problems.append("min10-max5 minimum moved")
        if pair.get("maximum", {}).get("signed_le16") != 5 or pair.get("maximum", {}).get("raw") != [0x05, 0x00]:
            problems.append("min10-max5 maximum moved")
        if pair["minimum"].get("signed_le16", 0) <= pair["maximum"].get("signed_le16", 0):
            problems.append("min10-max5 normalized")
    partial = words_of("factor-one-byte")
    if not isinstance(partial, dict) or partial.get("factor", {}).get("state") != "malformed":
        problems.append("factor-one-byte factor")
    elif partial["factor"].get("raw") != [0x02] or partial["factor"].get("signed_le16") is not None:
        problems.append("factor-one-byte factor value")
    else:
        for name, signed in (("minimum", 1), ("maximum", 2), ("default", 3), ("step", 4)):
            if partial.get(name, {}).get("state") != "decoded" or partial[name].get("signed_le16") != signed:
                problems.append(f"factor-one-byte erased {name}")
    scaled = words_of("factor-two")
    products = {"minimum": (10, 20), "maximum": (5, 10), "default": (7, 14), "step": (9, 18), "factor": (2, 4)}
    if not isinstance(scaled, dict):
        problems.append("factor-two erased")
    else:
        for name, (plain, product) in products.items():
            value = scaled.get(name, {}).get("signed_le16")
            if value != plain or value == product:
                problems.append(f"factor-two scaled {name}")
    step = words_of("negative-step")
    if not isinstance(step, dict) or step.get("step", {}).get("signed_le16") != -1:
        problems.append("negative-step normalized")
    elif step["step"].get("state") != "decoded":
        problems.append("negative-step rejected")
    zero = words_of("zero-factor")
    if not isinstance(zero, dict) or zero.get("factor", {}).get("state") != "decoded":
        problems.append("zero-factor rejected")
    elif zero["factor"].get("signed_le16") != 0 or zero.get("minimum", {}).get("signed_le16") != 4:
        problems.append("zero-factor changed")
    outside = words_of("default-outside")
    if not isinstance(outside, dict):
        problems.append("default-outside rejected")
    else:
        if outside.get("default", {}).get("signed_le16") != 100:
            problems.append("default-outside clamped")
        if outside.get("minimum", {}).get("signed_le16") != 0 or outside.get("maximum", {}).get("signed_le16") != 1:
            problems.append("default-outside bounds moved")
    malformed = words_of("all-malformed")
    if not isinstance(malformed, dict):
        problems.append("all-malformed erased")
    else:
        for name in WORD_FIELDS:
            if malformed.get(name, {}).get("state") != "malformed" or malformed[name].get("signed_le16") is not None:
                problems.append(f"all-malformed decoded {name}")
    mismatch = by_id["address-mismatch"]["expect"]
    if mismatch["address"]["local_equal"] is not False:
        problems.append("address-mismatch called equal")
    if mismatch["address"]["grants_requested_edit_bounds"] is not False:
        problems.append("address-mismatch granted edit bounds")
    if mismatch["address"]["admitted_minimum"] is not None or mismatch["address"]["admitted_maximum"] is not None:
        problems.append("address-mismatch admitted constraints")
    if mismatch["address"]["native_success"] is not None:
        problems.append("address-mismatch invented native success")
    if not isinstance(mismatch.get("words"), dict):
        problems.append("address-mismatch dropped candidates")
    op32 = by_id["op32-extremes"]["expect"]
    if op32["result_kind"] != "op32-address-status-query" or op32["shares_op33_result"] is not False:
        problems.append("op32 shared the op33 view")
    if op32["words"] is not None:
        problems.append("op32 returned op33 words")
    if "-32768" in json.dumps(op32) or "32767" in json.dumps(op32):
        problems.append("op32 leaked extreme word values")
    both_empty = by_id["both-empty"]["expect"]
    if both_empty["address"]["local_equal"] is not True or both_empty["address"]["native_success"] is not None:
        problems.append("empty addresses invented native success")
    if both_empty["address"]["requested_raw"] != [] or both_empty["address"]["returned_raw"] != []:
        problems.append("empty addresses were not explicit")
    return problems


def sibling_values(view, skipped):
    if not isinstance(view.get("words"), dict):
        return False
    for name in WORD_FIELDS:
        if name == skipped:
            continue
        word = view["words"][name]
        if word["state"] != "decoded" or word["signed_le16"] != 1 or word["raw"] != [1, 0]:
            return False
    return True


def spec_problem(spec, case):
    """Return the defect name when this isolated case no longer catches it."""
    view = case.get("expect")
    if not isinstance(view, dict):
        return spec["catches"]
    kind = spec["kind"]
    if kind == "word-value":
        words = view.get("words")
        if not isinstance(words, dict):
            return spec["catches"]
        word = words[spec["word"]]
        if word["state"] != "decoded" or word["raw"] != spec["raw"] or word["signed_le16"] != spec["signed_le16"]:
            return spec["catches"]
        if word["scale"] is not None or word["grades"]["numeric"] != "Hypothesis":
            return spec["catches"]
        if signed_le16(spec["raw"]) != spec["signed_le16"]:
            return spec["catches"]
        if spec["signed_le16"] == signed_be16(spec["raw"]):
            return spec["catches"]
        if unsigned_le16(spec["raw"]) != spec["signed_le16"] and word["signed_le16"] == unsigned_le16(spec["raw"]):
            return spec["catches"]
        if not sibling_values(view, spec["word"]):
            return spec["catches"]
    elif kind == "word-malformed":
        words = view.get("words")
        if not isinstance(words, dict):
            return spec["catches"]
        word = words[spec["word"]]
        if word["state"] != "malformed" or word["raw"] != spec["raw"] or word["signed_le16"] is not None:
            return spec["catches"]
        if word["length"] != len(spec["raw"]) or word["grades"]["numeric"] != "Unknown":
            return spec["catches"]
        if not sibling_values(view, spec["word"]):
            return spec["catches"]
    elif kind == "word-missing":
        words = view.get("words")
        if not isinstance(words, dict):
            return spec["catches"]
        word = words[spec["word"]]
        if word["state"] != "missing" or word["raw"] is not None or word["signed_le16"] is not None:
            return spec["catches"]
        if not sibling_values(view, spec["word"]):
            return spec["catches"]
    elif kind == "selection-value":
        if view["result_kind"] != spec["result_kind"] or view["words"] is not None:
            return spec["catches"]
        if view["shares_op33_result"] is not False or view["selection"][spec["key"]] != spec["value"]:
            return spec["catches"]
    elif kind == "selection-missing":
        if view["result_kind"] != "selection-incomplete" or view["words"] is not None:
            return spec["catches"]
        if view["selection"][spec["key"]] is not None or view["shares_op33_result"] is not False:
            return spec["catches"]
    elif kind == "op32":
        if view["result_kind"] != "op32-address-status-query" or view["words"] is not None:
            return spec["catches"]
        if view["selection"]["operation"] != "OP32" or view["shares_op33_result"] is not False:
            return spec["catches"]
        if view["grades"]["numeric"] != "Unknown":
            return spec["catches"]
    elif kind == "direction-value":
        if view["result_kind"] != "op33-positive-alternative" or view["selection"]["direction"] != spec["value"]:
            return spec["catches"]
        if view["words"]["minimum"]["signed_le16"] != 1:
            return spec["catches"]
    elif kind == "address":
        address = view.get("address", {})
        if address.get("requested_raw") != spec["requested"] or address.get("returned_raw") != spec["returned"]:
            return spec["catches"]
        if address.get("local_equal") is not spec["local_equal"] or address.get("native_success") is not None:
            return spec["catches"]
        if address.get("grants_requested_edit_bounds") is not False:
            return spec["catches"]
        if view["result_kind"] != "op33-positive-alternative" or not sibling_values(view, None):
            return spec["catches"]
    else:
        return spec["catches"]
    if view["address"]["grants_requested_edit_bounds"] is not False:
        return spec["catches"]
    if view["constraint_store_changed"] is not False or view["shared_cache_changed"] is not False:
        return spec["catches"]
    if view["grades"]["native"] != "Unknown" or view["address"]["native_echo"] != "Unknown":
        return spec["catches"]
    return None


def catalog_problems(document):
    problems = []
    if document.get("provenance") != PROVENANCE:
        problems.append("provenance")
    if document.get("native_qualification") != "Unknown":
        problems.append("native qualification")
    if document.get("signature") != SIGNATURE:
        problems.append("signature")
    if document.get("word_fields") != list(WORD_FIELDS):
        problems.append("word fields")
    normative = document.get("normative")
    if not isinstance(normative, dict):
        problems.append("normative missing")
    else:
        for key, (value, numeric, semantic, native) in NORMATIVE.items():
            item = normative.get(key)
            if item != {"value": value, "numeric": numeric, "semantic": semantic, "native": native}:
                problems.append(f"fixture normative {key}")
        for key in normative:
            if key not in NORMATIVE:
                problems.append(f"unexpected fixture normative {key}")
    by_id = {case["id"]: case for case in document.get("cases", [])}
    base = base_input()
    if "base" not in by_id or project(by_id["base"]) != base:
        problems.append("base input")
    elif by_id["base"].get("expect") != interpret_input(base):
        problems.append("base output")
    for spec_id, value in anchor_inputs():
        case = by_id.get(spec_id)
        if case is None or project(case) != value:
            problems.append(f"{spec_id} input")
        elif case.get("expect") != interpret_input(value):
            problems.append(f"{spec_id} output")
    for spec in variation_specs():
        case = by_id.get(spec["id"])
        expected_input = apply_spec(base, spec)
        if case is None or project(case) != expected_input:
            problems.append(f"{spec['id']} input")
            continue
        if case.get("expect") != interpret_input(expected_input):
            problems.append(f"{spec['id']} output")
        caught = spec_problem(spec, case)
        if caught:
            problems.append(f"{spec['id']}: {caught}")
    third = by_id.get("requested-byte2", {}).get("expect", {})
    third_next = by_id.get("requested-byte2-next", {}).get("expect", {})
    try:
        if third["address"]["requested_raw"][2] == third_next["address"]["requested_raw"][2]:
            problems.append("requested third bytes collapsed")
    except (KeyError, IndexError, TypeError):
        problems.append("requested third byte missing")
    returned = by_id.get("returned-byte2", {}).get("expect", {})
    returned_next = by_id.get("returned-byte2-next", {}).get("expect", {})
    try:
        if returned["address"]["returned_raw"][2] == returned_next["address"]["returned_raw"][2]:
            problems.append("returned third bytes collapsed")
    except (KeyError, IndexError, TypeError):
        problems.append("returned third byte missing")
    problems.extend(literal_problems(document))
    return problems


def disposable_dir():
    root = Path(os.environ.get("TMPDIR") or (ROOT / ".tmp"))
    path = root / "an08-mutants"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_fixture():
    return json.loads(FIXTURE_PATH.read_text())


class ConstraintWordViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE_PATH.read_text()
        cls.fixture = load_fixture()

    def test_page_contract(self):
        self.assertEqual(page_problems(self.page), [])

    def test_fixture_catalog_and_literals(self):
        self.assertEqual(catalog_problems(self.fixture), [])

    def test_decoder_pins(self):
        self.assertEqual(signed_le16([0x00, 0x80]), -32768)
        self.assertEqual(unsigned_le16([0x00, 0x80]), 32768)
        self.assertEqual(signed_be16([0x00, 0x80]), 128)
        self.assertEqual(signed_le16([0xFF, 0x7F]), 32767)
        self.assertEqual(signed_be16([0xFF, 0x7F]), -129)
        self.assertEqual(signed_le16([0xFF, 0xFF]), -1)
        self.assertEqual(unsigned_le16([0xFF, 0xFF]), 65535)
        self.assertEqual(signed_be16([0xFF, 0xFF]), -1)
        self.assertEqual(signed_le16([0x02, 0x00]), 2)
        self.assertEqual(signed_be16([0x02, 0x00]), 512)
        self.assertEqual(signed_le16([0x00, 0x00]), 0)

    def test_extremes_and_rejected_encodings(self):
        view = interpret_input(dict(anchor_inputs())["extremes"])
        self.assertEqual(
            [view["words"][name]["signed_le16"] for name in WORD_FIELDS],
            [-32768, 32767, -1, 2, 0],
        )
        self.assertNotEqual(view["words"]["minimum"]["signed_le16"], 32768)
        self.assertNotEqual(view["words"]["minimum"]["signed_le16"], 128)
        self.assertNotEqual(view["words"]["maximum"]["signed_le16"], -129)
        self.assertNotEqual(view["words"]["default"]["signed_le16"], 65535)
        self.assertFalse(view["address"]["grants_requested_edit_bounds"])
        self.assertTrue(view["address"]["local_equal"])
        self.assertIsNone(view["address"]["native_success"])

    def test_min_above_max_factor_and_partial_rows(self):
        anchors = dict(anchor_inputs())
        retained = interpret_input(anchors["min10-max5"])
        self.assertEqual(retained["words"]["minimum"]["signed_le16"], 10)
        self.assertEqual(retained["words"]["maximum"]["signed_le16"], 5)
        self.assertGreater(
            retained["words"]["minimum"]["signed_le16"],
            retained["words"]["maximum"]["signed_le16"],
        )
        partial = interpret_input(anchors["factor-one-byte"])
        self.assertEqual(partial["words"]["factor"]["state"], "malformed")
        self.assertEqual(
            [partial["words"][name]["signed_le16"] for name in WORD_FIELDS[:4]],
            [1, 2, 3, 4],
        )
        plain = interpret_input(anchors["factor-two"])
        self.assertEqual(
            [plain["words"][name]["signed_le16"] for name in WORD_FIELDS],
            [10, 5, 7, 9, 2],
        )
        self.assertNotEqual(
            [plain["words"][name]["signed_le16"] for name in WORD_FIELDS],
            [20, 10, 14, 18, 4],
        )
        step = interpret_input(anchors["negative-step"])
        self.assertEqual(step["words"]["step"]["signed_le16"], -1)
        zero = interpret_input(anchors["zero-factor"])
        self.assertEqual(zero["words"]["factor"]["state"], "decoded")
        self.assertEqual(zero["words"]["factor"]["signed_le16"], 0)
        outside = interpret_input(anchors["default-outside"])
        self.assertEqual(outside["words"]["default"]["signed_le16"], 100)
        self.assertLess(
            outside["words"]["maximum"]["signed_le16"],
            outside["words"]["default"]["signed_le16"],
        )

    def test_address_and_op32_boundaries(self):
        mismatch = interpret_input(dict(anchor_inputs())["address-mismatch"])
        self.assertFalse(mismatch["address"]["local_equal"])
        self.assertFalse(mismatch["address"]["grants_requested_edit_bounds"])
        self.assertIsNone(mismatch["address"]["admitted_minimum"])
        self.assertEqual(mismatch["words"]["minimum"]["signed_le16"], 10)
        self.assertEqual(mismatch["words"]["maximum"]["signed_le16"], 20)
        empty = interpret(
            base_input()["selection"],
            {"requested": [], "returned": []},
            base_input()["words"],
        )
        self.assertEqual(empty["address"]["requested_state"], "present")
        self.assertEqual(empty["address"]["requested_raw"], [])
        self.assertTrue(empty["address"]["local_equal"])
        self.assertIsNone(empty["address"]["native_success"])
        self.assertEqual(empty["address"]["native_echo"], "Unknown")
        op32 = interpret_input(dict(anchor_inputs())["op32-extremes"])
        extremes = interpret_input(dict(anchor_inputs())["extremes"])
        self.assertEqual(op32["result_kind"], "op32-address-status-query")
        self.assertIsNone(op32["words"])
        self.assertFalse(op32["shares_op33_result"])
        self.assertNotEqual(op32["result_kind"], extremes["result_kind"])
        self.assertIsNone(op32["address"]["native_success"])

    def test_every_isolated_field_catches_its_mutation(self):
        fields = [spec["field"] for spec in variation_specs()]
        self.assertEqual(len(fields), len(set(spec["id"] for spec in variation_specs())))
        for required in REQUIRED_VARIATION_FIELDS:
            self.assertIn(required, fields)
        by_id = {case["id"]: case for case in self.fixture["cases"]}
        for spec in variation_specs():
            with self.subTest(spec=spec["id"], catches=spec["catches"]):
                self.assertGreater(len(spec["catches"]), 20)
                self.assertIsNone(spec_problem(spec, by_id[spec["id"]]))

    def test_grade_boundaries_for_every_case(self):
        for case in self.fixture["cases"]:
            with self.subTest(case=case["id"]):
                view = interpret_input(project(case))
                self.assertEqual(view, case["expect"])
                self.assertEqual(view["grades"]["native"], "Unknown")
                self.assertNotEqual(view["grades"]["native"], "Proven")
                self.assertEqual(view["grades"]["semantic"], "Proven")
                self.assertFalse(view["constraint_store_changed"])
                self.assertFalse(view["shared_cache_changed"])
                self.assertFalse(view["address"]["grants_requested_edit_bounds"])
                self.assertIsNone(view["address"]["native_success"])
                self.assertEqual(view["address"]["native_echo"], "Unknown")
                self.assertIsNone(view["address"]["admitted_minimum"])
                self.assertIsNone(view["address"]["admitted_maximum"])
                words = view["words"]
                if words is None:
                    self.assertNotEqual(view["result_kind"], "op33-positive-alternative")
                    self.assertFalse(view["shares_op33_result"])
                    self.assertEqual(view["grades"]["numeric"], "Unknown")
                    continue
                self.assertEqual(view["result_kind"], "op33-positive-alternative")
                decoded = 0
                for name in WORD_FIELDS:
                    word = words[name]
                    self.assertEqual(word["grades"]["native"], "Unknown")
                    self.assertEqual(word["grades"]["semantic"], "Proven")
                    self.assertIsNone(word["scale"])
                    if word["state"] == "decoded":
                        decoded += 1
                        self.assertEqual(word["grades"]["numeric"], "Hypothesis")
                        self.assertNotEqual(word["grades"]["numeric"], "Proven")
                        self.assertEqual(word["signed_le16"], signed_le16(word["raw"]))
                    else:
                        self.assertEqual(word["grades"]["numeric"], "Unknown")
                        self.assertIsNone(word["signed_le16"])
                        self.assertIn(word["state"], {"missing", "malformed"})
                self.assertEqual(view["grades"]["numeric"], "Hypothesis" if decoded else "Unknown")

    def test_returned_raw_memory_is_detached_and_calls_do_not_share(self):
        requested = [0x10, 0x20]
        factor = [0x02, 0x00]
        words = {name: [0x01, 0x00] for name in WORD_FIELDS}
        words["factor"] = factor
        selection = base_input()["selection"]
        first = interpret(selection, {"requested": requested, "returned": [0x10, 0x20]}, words)
        self.assertIsNot(first["address"]["requested_raw"], requested)
        self.assertIsNot(first["words"]["factor"]["raw"], factor)
        requested[0] = 0x99
        factor[1] = 0x99
        self.assertEqual(first["address"]["requested_raw"], [0x10, 0x20])
        self.assertEqual(first["words"]["factor"]["signed_le16"], 2)
        first["address"]["requested_raw"][0] = 0x77
        first["words"]["factor"]["raw"][0] = 0x08
        self.assertEqual(requested[0], 0x99)
        self.assertEqual(factor[0], 0x02)
        second_words = {name: [0x01, 0x00] for name in WORD_FIELDS}
        second_words["factor"] = [0x02]
        second = interpret(selection, {"requested": [0x10, 0x20], "returned": [0x10, 0x20]}, second_words)
        self.assertEqual(first["words"]["factor"]["state"], "decoded")
        self.assertEqual(second["words"]["factor"]["state"], "malformed")
        self.assertEqual(second["words"]["minimum"]["signed_le16"], 1)
        omitted = {name: [0x01, 0x00] for name in WORD_FIELDS if name != "step"}
        omitted_view = interpret(selection, base_input()["addresses"], omitted)
        self.assertEqual(omitted_view["words"]["step"]["state"], "missing")
        self.assertEqual(omitted_view["words"]["minimum"]["signed_le16"], 1)
        extra = copy.deepcopy(selection)
        extra["unused"] = "ignored"
        echoed = interpret(extra, base_input()["addresses"], base_input()["words"])
        self.assertEqual(set(echoed["selection"]), {"family", "variant", "operation", "direction"})

    def test_relative_page_links_resolve_locally(self):
        targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", self.page)
        self.assertGreaterEqual(len(targets), 2)
        for target in targets:
            self.assertNotIn("://", target)
            path = target.split("#", 1)[0]
            self.assertTrue((PAGE_PATH.parent / path).is_file(), target)

    def test_page_mutants_are_killed(self):
        self.assertEqual(page_problems(self.page), [])
        replacements = (
            ("unsigned-word", "| word_signedness | signed |", "| word_signedness | unsigned |"),
            ("big-endian-word", "| word_endian | little-endian |", "| word_endian | big-endian |"),
            ("factor-converter", "| factor_role | raw-signed-field |", "| factor_role | converter |"),
            ("swap-min-max", "| min_above_max | retain-supplied-order |", "| min_above_max | swap |"),
            ("reject-min-max", "| min_above_max | retain-supplied-order |", "| min_above_max | reject |"),
            ("erase-malformed", "| partial_malformed | siblings-remain |", "| partial_malformed | erase-all |"),
            (
                "grant-on-mismatch",
                "| address_mismatch_edit_bounds | not-granted |",
                "| address_mismatch_edit_bounds | granted |",
            ),
            (
                "prose-unsigned",
                "Unsigned conversion is outside this contract.",
                "Unsigned conversion is accepted.",
            ),
            (
                "prose-endian",
                "Big-endian conversion is outside this contract.",
                "Big-endian conversion is used.",
            ),
            (
                "prose-factor",
                "The factor is not a converter and does not scale the other words.",
                "The factor is a converter and factor multiplies the other words.",
            ),
            (
                "prose-reorder",
                "Minimum greater than maximum is not rejected and is not reordered.",
                "Minimum greater than maximum is swapped and minimum and maximum are reordered.",
            ),
            (
                "prose-erase",
                "One malformed word does not erase the other words.",
                "One malformed word erases the other words.",
            ),
            (
                "prose-grant",
                "An address mismatch does not grant the requested edit bounds.",
                "An address mismatch grants the requested edit bounds.",
            ),
        )
        work = disposable_dir()
        for name, old, new in replacements:
            with self.subTest(mutant=name):
                self.assertEqual(self.page.count(old), 1)
                path = work / f"page-{name}.md"
                path.write_text(self.page.replace(old, new, 1))
                try:
                    self.assertNotEqual(page_problems(path.read_text()), [])
                finally:
                    path.unlink(missing_ok=True)

    def test_fixture_mutants_are_killed(self):
        self.assertEqual(catalog_problems(self.fixture), [])
        work = disposable_dir()

        def mutated(name, edit):
            document = copy.deepcopy(self.fixture)
            edit(document)
            path = work / f"fixture-{name}.json"
            path.write_text(json.dumps(document))
            try:
                loaded = json.loads(path.read_text())
                self.assertNotEqual(catalog_problems(loaded), [])
            finally:
                path.unlink(missing_ok=True)

        def case(document, spec_id):
            return next(item for item in document["cases"] if item["id"] == spec_id)

        def set_unsigned(document):
            case(document, "extremes")["expect"]["words"]["minimum"]["signed_le16"] = 32768

        def set_big_endian(document):
            words = case(document, "extremes")["expect"]["words"]
            words["minimum"]["signed_le16"] = 128
            words["maximum"]["signed_le16"] = -129
            words["step"]["signed_le16"] = 512

        def apply_factor(document):
            case(document, "factor-two")["expect"]["words"]["minimum"]["signed_le16"] = 20

        def swap_bounds(document):
            words = case(document, "min10-max5")["expect"]["words"]
            words["minimum"]["signed_le16"] = 5
            words["maximum"]["signed_le16"] = 10
            words["minimum"]["raw"] = [0x05, 0x00]
            words["maximum"]["raw"] = [0x0A, 0x00]

        def reject_bounds(document):
            item = case(document, "min10-max5")
            item["expect"]["result_kind"] = "selection-not-admitted"
            item["expect"]["words"] = None
            item["expect"]["shares_op33_result"] = False

        def erase_all(document):
            words = case(document, "factor-one-byte")["expect"]["words"]
            for name in WORD_FIELDS:
                words[name] = interpret_word(None)

        def grant_mismatch(document):
            address = case(document, "address-mismatch")["expect"]["address"]
            address["grants_requested_edit_bounds"] = True
            address["admitted_minimum"] = 10
            address["admitted_maximum"] = 20

        def authorize_unsigned_key(document):
            document["normative"]["word_signedness"]["value"] = "unsigned"

        mutants = (
            ("unsigned-word", set_unsigned),
            ("big-endian-word", set_big_endian),
            ("factor-converter", apply_factor),
            ("swap-min-max", swap_bounds),
            ("reject-min-max", reject_bounds),
            ("erase-malformed", erase_all),
            ("grant-on-mismatch", grant_mismatch),
            ("normative-unsigned", authorize_unsigned_key),
        )
        for name, edit in mutants:
            with self.subTest(mutant=name):
                mutated(name, edit)


if __name__ == "__main__":
    unittest.main()
