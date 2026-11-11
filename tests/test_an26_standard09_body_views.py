"""Focused checks for the standard 09 body-view contract.

Each identity or key field listed here is varied by itself. The production
mutation named beside it is the change that the focused checks reject.

- prefix_byte_0: ignoring logical byte 0, or stripping two bytes from a
  mismatched first byte, still yields a represented body.
- prefix_byte_1: ignoring logical byte 1 and accepting any second byte for
  0900, 0901, or 0903.
- service: viewing a body, address, or count when the object service differs
  from the selection.
- direction: viewing an object whose direction differs from the selection, or
  viewing a matched pair whose direction is not positive.
- profile_variant: ignoring a profile_variant mismatch.
- family: ignoring a family mismatch.
- address_low: dropping or swapping the first address byte so 34 12 is not
  4660 for the little-endian form, or so the split low byte is not 52.
- address_high: dropping the second address byte, or folding the 0902 and
  0903 split fields into the little-endian integer 4660.
- address_extent: inventing a missing address byte, or reading an offset into
  a larger decoy packet.
- body_extent: rejecting a zero-length 0902 object, typing a 0901 tail as
  opaque data, stripping 09 02 from 0902, or treating a prefix-only 0900
  object as a successful mutation.
- count: clipping 11 to 10, rejecting 11 globally, or collapsing 0, 10, 11,
  and 255 into fewer values.
"""

from __future__ import annotations

import copy
import json
import os
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = ROOT / "architecture" / "an26-standard09-body-views.md"
FIXTURE_PATH = ROOT / "architecture" / "fixtures" / "an26_standard09_body_views.json"

CONTRACT_ID = "an26-standard09-body-views"
SIGNATURES = (
    "ab25an25.ViewStandard09Body(selection, object)",
    "ab25an25.ViewStandard09Address(selection, delimited)",
    "ab25an25.ViewStandard09Count(selection, count)",
)
MATCH_FIELDS = ("family", "profile_variant", "service", "direction")
SERVICES = ("0900", "0901", "0902", "0903")
DENIALS = (
    "universal prefix removal",
    "inferring 0902 PB/SB",
    "prefix-only positive implies successful mutation",
    "clipping 11 to 10",
    "inventing a packet offset",
    "address-space equivalence",
    "accepting a mismatched service",
)
BODY_KEYS = {
    "admission",
    "raw_logical_bytes",
    "data",
    "unresolved_tail",
    "typed_data",
    "execution",
    "mutation_success",
    "native_success_claim",
    "local_representation",
    "numeric_grade",
    "semantic_grade",
    "native_grade",
    "physical_support",
    "native_physical_offset",
    "positive_prefix_relevance",
    "peer_acceptance",
}
ADDRESS_KEYS = {
    "admission",
    "raw",
    "form",
    "leu16",
    "low_u8",
    "high_u8",
    "packet_offset",
    "address_space",
    "numeric_grade",
    "semantic_grade",
    "native_grade",
    "execution",
    "physical_support",
}
COUNT_KEYS = {
    "admission",
    "raw",
    "value",
    "clipped",
    "rejected",
    "conflict",
    "numeric_grade",
    "semantic_grade",
    "native_grade",
    "execution",
    "physical_support",
}

BASE_IDENTITY = {
    "family": "ebus-module",
    "profile_variant": "standard-09",
    "service": "0900",
    "direction": "positive",
}


def _bytes(values):
    return [int(value) for value in values]


def _identity(service="0900", **overrides):
    record = dict(BASE_IDENTITY)
    record["service"] = service
    record.update(overrides)
    return record


def extract_contract(page_text):
    marker = "```json\n"
    start = page_text.find(marker)
    if start < 0:
        return None
    body_start = start + len(marker)
    end = page_text.find("\n```", body_start)
    if end < 0:
        return None
    if page_text.find(marker, body_start) != -1:
        return None
    try:
        data = json.loads(page_text[body_start:end])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or data.get("contract_id") != CONTRACT_ID:
        return None
    return data


def replace_contract(page_text, contract):
    marker = "```json\n"
    start = page_text.find(marker)
    body_start = start + len(marker)
    end = page_text.find("\n```", body_start)
    dumped = json.dumps(contract, indent=2)
    return page_text[:body_start] + dumped + page_text[end:]


def denial_map(page_text):
    match = re.search(
        r"^## Normative denials\n(.*?)(?=^## |\Z)",
        page_text,
        re.S | re.M,
    )
    if match is None:
        return {}
    found = {}
    for line in match.group(1).splitlines():
        if not line.startswith("- ") or ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        found[key.strip()] = value.strip()
    return found


def relative_link_errors(page_text):
    errors = []
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", page_text):
        target = match.group(1)
        if "://" in target or target.startswith("mailto:"):
            errors.append(target)
            continue
        path = target.split("#", 1)[0]
        if not path:
            continue
        resolved = (PAGE_PATH.parent / path).resolve()
        if not resolved.is_file():
            errors.append(target)
    return errors


def _grade_triplet(rules, numeric):
    if rules is None:
        arithmetic = "Proven"
        meaning = "Hypothesis"
        native = "Unknown"
    else:
        arithmetic = rules["grades"]["arithmetic"]
        meaning = rules["grades"]["meaning"]
        native = rules["grades"]["native"]
    return {
        "numeric_grade": arithmetic if numeric else "not_applicable",
        "semantic_grade": meaning,
        "native_grade": native,
        "physical_support": native,
    }


def _body_shell(raw, rules=None):
    shell = {
        "admission": "unknown",
        "raw_logical_bytes": _bytes(raw),
        "data": None,
        "unresolved_tail": None,
        "typed_data": None,
        "execution": "not_executed",
        "mutation_success": False,
        "native_success_claim": False,
        "local_representation": False,
        "native_physical_offset": "Unknown" if rules is None else rules["grades"]["native"],
        "positive_prefix_relevance": "Unknown" if rules is None else rules["grades"]["native"],
        "peer_acceptance": "Unknown" if rules is None else rules["grades"]["native"],
    }
    shell.update(_grade_triplet(rules, False))
    return shell


def _match_admission(rules, selection, identity):
    fields = list(MATCH_FIELDS if rules is None else rules["match_fields"])
    if rules is not None and rules.get("accept_mismatched_service"):
        fields = [field for field in fields if field != "service"]
    for field in fields:
        if selection[field] != identity[field]:
            return "unmatched", None
    service = selection["service"]
    if rules is not None and (
        rules.get("accept_mismatched_service") or "service" not in rules["match_fields"]
    ):
        service = selection["service"]
    else:
        service = identity["service"]
    if selection["direction"] != "positive":
        return "unknown", None
    if service not in SERVICES:
        return "unknown", None
    return None, service


def independent_body(selection, obj):
    raw = _bytes(obj["logical_bytes"])
    result = _body_shell(raw)
    admission, service = _match_admission(None, selection, obj)
    if admission is not None:
        result["admission"] = admission
        return result
    if obj["object_state"] == "incomplete":
        result["admission"] = "incomplete"
        return result
    if obj["object_state"] == "unknown":
        result["admission"] = "unknown"
        return result
    if obj["object_state"] != "complete":
        result["admission"] = "unknown"
        return result
    if service in ("0900", "0903"):
        expected = 0 if service == "0900" else 3
        if len(raw) < 2 or raw[0] != 9 or raw[1] != expected:
            result["admission"] = "incomplete"
            return result
        result["admission"] = "represented"
        result["local_representation"] = True
        result["typed_data"] = "opaque"
        result["data"] = raw[2:]
        return result
    if service == "0901":
        if len(raw) < 2 or raw[0] != 9 or raw[1] != 1:
            result["admission"] = "incomplete"
            return result
        result["admission"] = "represented"
        result["local_representation"] = True
        result["typed_data"] = None
        result["data"] = None
        result["unresolved_tail"] = raw[2:]
        return result
    if service == "0902":
        result["admission"] = "represented"
        result["local_representation"] = True
        result["typed_data"] = "opaque"
        result["data"] = list(raw)
        return result
    result["admission"] = "unknown"
    return result


def independent_address(selection, identity, delimited):
    raw = _bytes(delimited)
    result = {
        "admission": "unknown",
        "raw": raw,
        "form": None,
        "leu16": None,
        "low_u8": None,
        "high_u8": None,
        "packet_offset": None,
        "address_space": None,
        "execution": "not_executed",
    }
    result.update(_grade_triplet(None, False))
    admission, service = _match_admission(None, selection, identity)
    if admission is not None:
        result["admission"] = admission
        return result
    if len(raw) != 2:
        result["admission"] = "incomplete"
        return result
    low, high = raw[0], raw[1]
    if service in ("0900", "0901"):
        result["admission"] = "represented"
        result["form"] = "leu16"
        result["leu16"] = low + (high * 256)
        result.update(_grade_triplet(None, True))
        return result
    result["admission"] = "represented"
    result["form"] = "split_u8"
    result["low_u8"] = low
    result["high_u8"] = high
    result.update(_grade_triplet(None, True))
    return result


def _count_conflict(value, maximum=10):
    return {
        "candidate_recommendation_maximum": maximum,
        "formal_domain": "u8-0-255",
        "value_outside_candidate_recommendation": value > maximum,
    }


def independent_count(selection, identity, count):
    result = {
        "admission": "unknown",
        "raw": count,
        "value": None,
        "clipped": False,
        "rejected": False,
        "conflict": None,
        "execution": "not_executed",
    }
    result.update(_grade_triplet(None, False))
    admission, service = _match_admission(None, selection, identity)
    if admission is not None:
        result["admission"] = admission
        return result
    if service in ("0901", "0903"):
        result["admission"] = "inapplicable"
        return result
    result["admission"] = "represented"
    result["value"] = count
    result.update(_grade_triplet(None, True))
    if service == "0902":
        result["conflict"] = _count_conflict(count)
    return result


def independent_oracle(case):
    if case["kind"] == "body":
        return independent_body(case["selection"], case["object"])
    if case["kind"] == "address":
        return independent_address(case["selection"], case["identity"], case["delimited"])
    if case["kind"] == "count":
        return independent_count(case["selection"], case["identity"], case["count"])
    raise AssertionError(case["kind"])


def _represented_body(result, raw, data, tail, typed):
    result["admission"] = "represented"
    result["local_representation"] = True
    result["data"] = None if data is None else list(data)
    result["unresolved_tail"] = None if tail is None else list(tail)
    result["typed_data"] = typed
    result["raw_logical_bytes"] = list(raw)
    return result


def evaluate_body(rules, selection, obj):
    raw = _bytes(obj["logical_bytes"])
    result = _body_shell(raw, rules)
    admission, service = _match_admission(rules, selection, obj)
    if admission is not None:
        result["admission"] = admission
        return result
    if obj["object_state"] == "incomplete":
        result["admission"] = "incomplete"
        return result
    if obj["object_state"] != "complete":
        result["admission"] = "unknown"
        return result
    if rules["universal_prefix_removal"]:
        if len(raw) < 2:
            result["admission"] = "incomplete"
            return result
        return _represented_body(result, raw, raw[2:], None, "opaque")
    if service == "0902" and rules["infer_0902_pb_sb"]:
        if len(raw) < 2 or raw[0] != 9 or raw[1] != 2:
            result["admission"] = "incomplete"
            return result
        return _represented_body(result, raw, raw[2:], None, "opaque")
    spec = rules["body_rules"][service]
    kind = spec["kind"]
    if kind == "constants_then_opaque":
        start = spec["data_start"]
        if len(raw) < 2 or raw[0] != spec["pb"] or raw[1] != spec["sb"] or len(raw) < start:
            result["admission"] = "incomplete"
            return result
        data = raw[start:]
        if data == [] and not rules["empty_opaque_is_representable"]:
            result["admission"] = "incomplete"
            return result
        _represented_body(result, raw, data, None, "opaque")
    elif kind == "constants_only":
        if len(raw) < 2 or raw[0] != spec["pb"] or raw[1] != spec["sb"]:
            result["admission"] = "incomplete"
            return result
        _represented_body(result, raw, None, raw[2:], None)
    elif kind == "opaque_from_start":
        start = spec["data_start"]
        if spec.get("strip_prefix") or start != 0:
            if len(raw) < start:
                result["admission"] = "incomplete"
                return result
            data = raw[start:]
        else:
            data = list(raw)
        if data == [] and not rules["empty_opaque_is_representable"]:
            result["admission"] = "incomplete"
            return result
        _represented_body(result, raw, data, None, "opaque")
    else:
        result["admission"] = "unknown"
        return result
    if (
        rules["prefix_only_positive_means_successful_mutation"]
        and result["admission"] == "represented"
        and service in ("0900", "0901", "0903")
        and len(raw) == 2
    ):
        result["execution"] = "success"
        result["mutation_success"] = True
    return result


def evaluate_address(rules, case):
    delimited = _bytes(case["delimited"])
    result = independent_address(case["selection"], case["identity"], delimited)
    # Rebuild from rules so a drifted page cannot pass through the oracle.
    result = {
        "admission": "unknown",
        "raw": list(delimited),
        "form": None,
        "leu16": None,
        "low_u8": None,
        "high_u8": None,
        "packet_offset": None,
        "address_space": None,
        "execution": "not_executed",
    }
    result.update(_grade_triplet(rules, False))
    admission, service = _match_admission(rules, case["selection"], case["identity"])
    if admission is not None:
        result["admission"] = admission
        return result
    spec = rules["address_rules"][service]
    used = list(delimited)
    offset = spec.get("packet_offset")
    if rules["invent_packet_offset"]:
        offset = case.get("decoy_offset", 0)
    if offset is not None:
        packet = list(case.get("decoy_packet", delimited))
        width = spec["width"]
        used = packet[offset:offset + width]
        result["packet_offset"] = offset
        result["raw"] = list(delimited)
    space = spec.get("address_space")
    if len(used) != spec["width"]:
        result["admission"] = "incomplete"
        result["address_space"] = space
        return result
    if spec["form"] == "leu16":
        if spec.get("endian") == "little":
            value = used[0] + (used[1] * 256)
        elif spec.get("endian") == "big":
            value = used[1] + (used[0] * 256)
        else:
            result["admission"] = "unknown"
            return result
        result["admission"] = "represented"
        result["form"] = "leu16"
        result["leu16"] = value
        result["address_space"] = space
        result.update(_grade_triplet(rules, True))
        return result
    if spec["form"] == "split_u8":
        result["admission"] = "represented"
        result["form"] = "split_u8"
        result["low_u8"] = used[0]
        result["high_u8"] = used[1]
        if rules["address_space_equivalence"] or spec.get("leu16_equivalent"):
            result["leu16"] = used[0] + (used[1] * 256)
            if space is None:
                space = "equivalent"
        result["address_space"] = space
        result.update(_grade_triplet(rules, True))
        return result
    result["admission"] = "unknown"
    return result


def evaluate_count(rules, case):
    count = case["count"]
    result = {
        "admission": "unknown",
        "raw": count,
        "value": None,
        "clipped": False,
        "rejected": False,
        "conflict": None,
        "execution": "not_executed",
    }
    result.update(_grade_triplet(rules, False))
    admission, service = _match_admission(rules, case["selection"], case["identity"])
    if admission is not None:
        result["admission"] = admission
        return result
    if service in ("0901", "0903"):
        result["admission"] = "inapplicable"
        return result
    spec = rules["count_rules"][service]
    value = count
    if rules["clip_count_11_to_10"] and value == 11:
        value = 10
    clip_above = spec.get("clip_above")
    if clip_above is not None and value > clip_above:
        value = clip_above
    maximum = spec.get("candidate_recommendation_maximum")
    if rules["reject_outside_candidate"] and maximum is not None and count > maximum:
        result["admission"] = "rejected"
        result["rejected"] = True
        result["clipped"] = value != count
        return result
    result["admission"] = "represented"
    result["value"] = value
    result["clipped"] = value != count
    result.update(_grade_triplet(rules, True))
    if maximum is not None:
        outside = count > maximum
        if rules["clip_count_11_to_10"] and count == 11:
            outside = False
        result["conflict"] = {
            "candidate_recommendation_maximum": maximum,
            "formal_domain": spec["domain"],
            "value_outside_candidate_recommendation": outside,
        }
    return result


def evaluate_case(rules, case):
    if case["kind"] == "body":
        return evaluate_body(rules, case["selection"], case["object"])
    if case["kind"] == "address":
        return evaluate_address(rules, case)
    if case["kind"] == "count":
        return evaluate_count(rules, case)
    return {"admission": "unknown"}


def diagnose(page_text, fixture_text):
    if "\t" in page_text:
        return "page contains a tab"
    denials = denial_map(page_text)
    for key in DENIALS:
        if denials.get(key) != "denied":
            return f"denial {key} is {denials.get(key)!r}"
    link_errors = relative_link_errors(page_text)
    if link_errors:
        return f"links {link_errors}"
    for signature in SIGNATURES:
        if page_text.count(signature) < 2:
            return f"signature missing twice: {signature}"
    for token in ("Proven", "Hypothesis", "Unknown", "4660", "09 00 AA 55", "09 02 AA 55", "09 03 AA 55"):
        if token not in page_text:
            return f"page missing {token}"
    rules = extract_contract(page_text)
    if rules is None:
        return "contract block missing"
    for signature in SIGNATURES:
        if signature not in rules["signatures"]:
            return f"contract signature missing: {signature}"
    try:
        fixture = json.loads(fixture_text)
    except json.JSONDecodeError as exc:
        return f"fixture json {exc}"
    if fixture.get("fixture_id") != CONTRACT_ID or fixture.get("synthetic") is not True:
        return "fixture identity"
    cases = fixture.get("cases")
    if not isinstance(cases, list) or not cases:
        return "fixture cases"
    seen = set()
    for case in cases:
        case_id = case.get("id")
        if case_id in seen:
            return f"duplicate {case_id}"
        seen.add(case_id)
        oracle = independent_oracle(case)
        actual = evaluate_case(rules, case)
        expect = case.get("expect")
        if oracle != expect:
            return f"{case_id} fixture expect drifted from the independent oracle"
        if actual != oracle:
            return f"{case_id} page rules drifted from the independent oracle"
        if case["kind"] == "body" and set(oracle) != BODY_KEYS:
            return f"{case_id} body keys"
        if case["kind"] == "address" and set(oracle) != ADDRESS_KEYS:
            return f"{case_id} address keys"
        if case["kind"] == "count" and set(oracle) != COUNT_KEYS:
            return f"{case_id} count keys"
        if oracle.get("execution") == "success" or oracle.get("mutation_success") is True:
            return f"{case_id} execution success"
    required = {
        "body-0900-aa55",
        "body-0903-aa55",
        "body-0902-aa55-kept",
        "body-0901-constants-only",
        "body-0901-unresolved-aa",
        "body-0900-truncated",
        "body-0901-truncated",
        "body-0903-truncated",
        "body-0900-prefix-mismatch",
        "body-0901-prefix-mismatch",
        "body-0903-prefix-mismatch",
        "body-0902-empty",
        "body-0900-prefix-only",
        "body-0902-ordinary",
        "body-0902-prefix-bytes-are-data",
        "body-service-mismatch",
        "body-direction-mismatch",
        "body-profile-mismatch",
        "body-family-mismatch",
        "body-matched-nonpositive",
        "body-incomplete-state",
        "body-unknown-state",
        "address-0900-3412",
        "address-0901-3412",
        "address-0902-3412",
        "address-0903-3412",
        "address-0900-low",
        "address-0900-high",
        "address-0902-low",
        "address-0902-high",
        "address-0900-extent-zero",
        "address-0900-extent-one",
        "address-0900-extent-three",
        "address-0902-extent-one",
        "address-service-mismatch",
        "address-direction-mismatch",
        "address-profile-mismatch",
        "address-family-mismatch",
        "count-0900-0",
        "count-0900-10",
        "count-0900-11",
        "count-0900-255",
        "count-0902-0",
        "count-0902-10",
        "count-0902-11",
        "count-0902-255",
        "count-0901-inapplicable",
        "count-0903-inapplicable",
        "count-service-mismatch",
        "count-direction-mismatch",
        "count-profile-mismatch",
        "count-family-mismatch",
    }
    missing = required - seen
    if missing:
        return f"missing cases {sorted(missing)}"
    by_id = {case["id"]: case for case in cases}
    ticket = (
        (by_id["body-0900-aa55"], [9, 0, 170, 85], [170, 85]),
        (by_id["body-0903-aa55"], [9, 3, 170, 85], [170, 85]),
    )
    for case, raw, data in ticket:
        if case["object"]["logical_bytes"] != raw or case["expect"]["data"] != data:
            return case["id"]
        if case["expect"]["execution"] != "not_executed":
            return case["id"]
    kept = by_id["body-0902-aa55-kept"]
    if kept["object"]["logical_bytes"] != [9, 2, 170, 85] or kept["expect"]["data"] != [9, 2, 170, 85]:
        return "0902 stripped"
    only = by_id["body-0901-constants-only"]
    if only["expect"]["data"] is not None or only["expect"]["unresolved_tail"] != []:
        return "0901 typed data"
    tail = by_id["body-0901-unresolved-aa"]
    if tail["expect"]["data"] is not None or tail["expect"]["unresolved_tail"] != [170]:
        return "0901 tail"
    for case_id in (
        "body-0900-truncated",
        "body-0901-truncated",
        "body-0903-truncated",
        "body-0900-prefix-mismatch",
        "body-0901-prefix-mismatch",
        "body-0903-prefix-mismatch",
    ):
        if by_id[case_id]["expect"]["admission"] != "incomplete":
            return case_id
        if by_id[case_id]["expect"]["data"] is not None:
            return case_id
    empty = by_id["body-0902-empty"]
    if empty["expect"]["data"] != [] or empty["expect"]["native_success_claim"] is not False:
        return "empty 0902"
    if empty["expect"]["admission"] != "represented" or empty["expect"]["execution"] != "not_executed":
        return "empty 0902 success"
    prefix_only = by_id["body-0900-prefix-only"]
    if prefix_only["expect"]["data"] != [] or prefix_only["expect"]["mutation_success"] is not False:
        return "prefix-only success"
    address = by_id["address-0900-3412"]["expect"]
    if address["leu16"] != 4660 or address["low_u8"] is not None or address["packet_offset"] is not None:
        return "leu16"
    if address["address_space"] is not None or address["numeric_grade"] != "Proven":
        return "leu16 grade"
    if address["semantic_grade"] != "Hypothesis" or address["native_grade"] != "Unknown":
        return "leu16 grade split"
    split = by_id["address-0902-3412"]["expect"]
    if split["low_u8"] != 52 or split["high_u8"] != 18 or split["leu16"] is not None:
        return "split"
    if split["address_space"] is not None or split["packet_offset"] is not None:
        return "split space"
    values = [by_id[f"count-0902-{value}"]["expect"]["value"] for value in (0, 10, 11, 255)]
    if values != [0, 10, 11, 255]:
        return f"counts {values}"
    if by_id["count-0902-11"]["expect"]["clipped"] is not False:
        return "clipped"
    if by_id["count-0902-11"]["expect"]["rejected"] is not False:
        return "rejected"
    conflict = by_id["count-0902-11"]["expect"]["conflict"]
    if conflict["value_outside_candidate_recommendation"] is not True:
        return "conflict"
    if conflict["candidate_recommendation_maximum"] != 10:
        return "maximum"
    if by_id["count-0900-11"]["expect"]["value"] != 11 or by_id["count-0900-11"]["expect"]["conflict"] is not None:
        return "0900 count"
    if by_id["count-0902-10"]["expect"]["conflict"]["value_outside_candidate_recommendation"] is not False:
        return "10 outside"
    return None


def _body_case(
    case_id,
    service,
    logical,
    varies,
    object_state="complete",
    selection_overrides=None,
    object_overrides=None,
):
    selection = _identity(service)
    selection.update(selection_overrides or {})
    obj = _identity(service)
    obj.update(object_overrides or {})
    obj["object_state"] = object_state
    obj["logical_bytes"] = list(logical)
    case = {
        "id": case_id,
        "kind": "body",
        "varies": list(varies),
        "selection": selection,
        "object": obj,
    }
    case["expect"] = independent_oracle(case)
    return case


def _address_case(
    case_id,
    service,
    delimited,
    varies,
    selection_overrides=None,
    identity_overrides=None,
):
    case = {
        "id": case_id,
        "kind": "address",
        "varies": list(varies),
        "selection": _identity(service) | (selection_overrides or {}),
        "identity": _identity(service) | (identity_overrides or {}),
        "delimited": list(delimited),
        "decoy_packet": [1, 2, 3, 4],
        "decoy_offset": 0,
    }
    case["expect"] = independent_oracle(case)
    return case


def _count_case(
    case_id,
    service,
    count,
    varies,
    selection_overrides=None,
    identity_overrides=None,
):
    case = {
        "id": case_id,
        "kind": "count",
        "varies": list(varies),
        "selection": _identity(service) | (selection_overrides or {}),
        "identity": _identity(service) | (identity_overrides or {}),
        "count": count,
    }
    case["expect"] = independent_oracle(case)
    return case


def build_cases():
    aa55 = [9, 0, 170, 85]
    cases = [
        _body_case("body-0900-aa55", "0900", [9, 0, 170, 85], ["baseline"]),
        _body_case("body-0903-aa55", "0903", [9, 3, 170, 85], ["service"]),
        _body_case("body-0902-aa55-kept", "0902", [9, 2, 170, 85], ["service", "prefix_byte_0", "prefix_byte_1"]),
        _body_case("body-0901-constants-only", "0901", [9, 1], ["service", "body_extent"]),
        _body_case("body-0901-unresolved-aa", "0901", [9, 1, 170], ["body_extent"]),
        _body_case("body-0900-truncated", "0900", [9], ["body_extent", "prefix_byte_1"]),
        _body_case("body-0901-truncated", "0901", [9], ["body_extent"]),
        _body_case("body-0903-truncated", "0903", [9], ["body_extent"]),
        _body_case("body-0900-prefix-mismatch", "0900", [8, 0, 170, 85], ["prefix_byte_0"]),
        _body_case("body-0901-prefix-mismatch", "0901", [9, 0], ["prefix_byte_1"]),
        _body_case("body-0903-prefix-mismatch", "0903", [9, 2, 170, 85], ["prefix_byte_1"]),
        _body_case("body-0902-empty", "0902", [], ["body_extent"]),
        _body_case("body-0900-prefix-only", "0900", [9, 0], ["body_extent"]),
        _body_case("body-0903-prefix-only", "0903", [9, 3], ["body_extent"]),
        _body_case("body-0902-ordinary", "0902", [170, 85], ["prefix_byte_0", "prefix_byte_1"]),
        _body_case("body-0902-prefix-bytes-are-data", "0902", [9, 2], ["body_extent"]),
        _body_case(
            "body-service-mismatch",
            "0900",
            aa55,
            ["service"],
            object_overrides={"service": "0903"},
        ),
        _body_case(
            "body-direction-mismatch",
            "0900",
            aa55,
            ["direction"],
            object_overrides={"direction": "initiator-request"},
        ),
        _body_case(
            "body-profile-mismatch",
            "0900",
            aa55,
            ["profile_variant"],
            object_overrides={"profile_variant": "other-profile"},
        ),
        _body_case(
            "body-family-mismatch",
            "0900",
            aa55,
            ["family"],
            object_overrides={"family": "other-family"},
        ),
        _body_case(
            "body-matched-nonpositive",
            "0900",
            aa55,
            ["direction"],
            selection_overrides={"direction": "initiator-request"},
            object_overrides={"direction": "initiator-request"},
        ),
        _body_case("body-incomplete-state", "0900", aa55, ["body_extent"], object_state="incomplete"),
        _body_case("body-unknown-state", "0900", aa55, ["body_extent"], object_state="unknown"),
        _address_case("address-0900-3412", "0900", [52, 18], ["address_low", "address_high"]),
        _address_case("address-0901-3412", "0901", [52, 18], ["service"]),
        _address_case("address-0902-3412", "0902", [52, 18], ["service", "address_low", "address_high"]),
        _address_case("address-0903-3412", "0903", [52, 18], ["service"]),
        _address_case("address-0900-low", "0900", [53, 18], ["address_low"]),
        _address_case("address-0900-high", "0900", [52, 19], ["address_high"]),
        _address_case("address-0902-low", "0902", [53, 18], ["address_low"]),
        _address_case("address-0902-high", "0902", [52, 19], ["address_high"]),
        _address_case("address-0900-swapped", "0900", [18, 52], ["address_low", "address_high"]),
        _address_case("address-0900-extent-zero", "0900", [], ["address_extent"]),
        _address_case("address-0900-extent-one", "0900", [52], ["address_extent"]),
        _address_case("address-0900-extent-three", "0900", [52, 18, 0], ["address_extent"]),
        _address_case("address-0902-extent-one", "0902", [52], ["address_extent"]),
        _address_case(
            "address-service-mismatch",
            "0900",
            [52, 18],
            ["service"],
            identity_overrides={"service": "0902"},
        ),
        _address_case(
            "address-direction-mismatch",
            "0900",
            [52, 18],
            ["direction"],
            identity_overrides={"direction": "initiator-request"},
        ),
        _address_case(
            "address-profile-mismatch",
            "0900",
            [52, 18],
            ["profile_variant"],
            identity_overrides={"profile_variant": "other-profile"},
        ),
        _address_case(
            "address-family-mismatch",
            "0900",
            [52, 18],
            ["family"],
            identity_overrides={"family": "other-family"},
        ),
    ]
    for service in ("0900", "0902"):
        for value in (0, 10, 11, 255):
            cases.append(_count_case(f"count-{service}-{value}", service, value, ["count"]))
    cases.extend(
        [
            _count_case("count-0901-inapplicable", "0901", 11, ["service", "count"]),
            _count_case("count-0903-inapplicable", "0903", 11, ["service", "count"]),
            _count_case(
                "count-service-mismatch",
                "0902",
                11,
                ["service"],
                identity_overrides={"service": "0900"},
            ),
            _count_case(
                "count-direction-mismatch",
                "0902",
                11,
                ["direction"],
                identity_overrides={"direction": "initiator-request"},
            ),
            _count_case(
                "count-profile-mismatch",
                "0902",
                11,
                ["profile_variant"],
                identity_overrides={"profile_variant": "other-profile"},
            ),
            _count_case(
                "count-family-mismatch",
                "0902",
                11,
                ["family"],
                identity_overrides={"family": "other-family"},
            ),
        ]
    )
    return cases


class Standard09BodyViewContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page_text = PAGE_PATH.read_text(encoding="utf-8")
        cls.fixture_text = FIXTURE_PATH.read_text(encoding="utf-8")
        cls.rules = extract_contract(cls.page_text)
        cls.fixture = json.loads(cls.fixture_text)
        cls.by_id = {case["id"]: case for case in cls.fixture["cases"]}

    def test_page_and_fixture_agree_with_independent_oracle(self):
        reason = diagnose(self.page_text, self.fixture_text)
        self.assertIsNone(reason)

    def test_selected_body_examples(self):
        rules = self.rules
        kept = evaluate_case(rules, self.by_id["body-0900-aa55"])
        self.assertEqual(kept["data"], [170, 85])
        self.assertEqual(evaluate_case(rules, self.by_id["body-0903-aa55"])["data"], [170, 85])
        four = evaluate_case(rules, self.by_id["body-0902-aa55-kept"])
        self.assertEqual(four["data"], [9, 2, 170, 85])
        exact = evaluate_case(rules, self.by_id["body-0901-constants-only"])
        self.assertIsNone(exact["data"])
        self.assertEqual(exact["unresolved_tail"], [])
        tail = evaluate_case(rules, self.by_id["body-0901-unresolved-aa"])
        self.assertIsNone(tail["data"])
        self.assertEqual(tail["unresolved_tail"], [170])
        self.assertIsNone(tail["typed_data"])

    def test_prefix_and_extent_each_change_the_body(self):
        rules = self.rules
        base = copy.deepcopy(self.by_id["body-0900-aa55"])
        self.assertEqual(evaluate_case(rules, base)["admission"], "represented")
        first = copy.deepcopy(base)
        first["object"]["logical_bytes"][0] = 8
        self.assertEqual(evaluate_case(rules, first)["admission"], "incomplete")
        self.assertEqual(independent_oracle(first)["data"], None)
        second = copy.deepcopy(base)
        second["object"]["logical_bytes"][1] = 1
        self.assertEqual(evaluate_case(rules, second)["admission"], "incomplete")
        short = copy.deepcopy(base)
        short["object"]["logical_bytes"] = [9]
        self.assertEqual(evaluate_case(rules, short)["admission"], "incomplete")
        only = copy.deepcopy(base)
        only["object"]["logical_bytes"] = [9, 0]
        viewed = evaluate_case(rules, only)
        self.assertEqual(viewed["data"], [])
        self.assertFalse(viewed["mutation_success"])
        self.assertEqual(viewed["execution"], "not_executed")
        longer = copy.deepcopy(base)
        longer["object"]["logical_bytes"] = [9, 0, 170, 85, 1]
        self.assertEqual(evaluate_case(rules, longer)["data"], [170, 85, 1])

    def test_identity_fields_are_independent(self):
        rules = self.rules
        base = copy.deepcopy(self.by_id["body-0900-aa55"])
        for field, bad, admission in (
            ("family", "other-family", "unmatched"),
            ("profile_variant", "other-profile", "unmatched"),
            ("service", "0903", "unmatched"),
            ("direction", "initiator-request", "unmatched"),
        ):
            varied = copy.deepcopy(base)
            varied["object"][field] = bad
            result = evaluate_case(rules, varied)
            self.assertEqual(result["admission"], admission, field)
            self.assertEqual(result["raw_logical_bytes"], [9, 0, 170, 85], field)
            self.assertIsNone(result["data"], field)
            self.assertEqual(independent_oracle(varied), result, field)
        matched = copy.deepcopy(base)
        matched["selection"]["direction"] = "initiator-request"
        matched["object"]["direction"] = "initiator-request"
        self.assertEqual(evaluate_case(rules, matched)["admission"], "unknown")
        incomplete = copy.deepcopy(base)
        incomplete["object"]["object_state"] = "incomplete"
        self.assertEqual(evaluate_case(rules, incomplete)["admission"], "incomplete")
        self.assertIsNone(evaluate_case(rules, incomplete)["data"])
        unknown = copy.deepcopy(base)
        unknown["object"]["object_state"] = "unknown"
        self.assertEqual(evaluate_case(rules, unknown)["admission"], "unknown")

    def test_0902_does_not_infer_a_prefix(self):
        rules = self.rules
        ordinary = evaluate_case(rules, self.by_id["body-0902-ordinary"])
        self.assertEqual(ordinary["data"], [170, 85])
        embedded = evaluate_case(rules, self.by_id["body-0902-prefix-bytes-are-data"])
        self.assertEqual(embedded["data"], [9, 2])
        self.assertFalse(embedded["mutation_success"])
        empty = evaluate_case(rules, self.by_id["body-0902-empty"])
        self.assertEqual(empty["data"], [])
        self.assertFalse(empty["native_success_claim"])
        self.assertEqual(empty["peer_acceptance"], "Unknown")
        self.assertEqual(empty["execution"], "not_executed")

    def test_address_bytes_and_width_are_independent(self):
        rules = self.rules
        base = evaluate_case(rules, self.by_id["address-0900-3412"])
        self.assertEqual(base["leu16"], 4660)
        self.assertIsNone(base["packet_offset"])
        self.assertIsNone(base["address_space"])
        self.assertEqual(base["numeric_grade"], "Proven")
        self.assertEqual(base["semantic_grade"], "Hypothesis")
        self.assertEqual(base["native_grade"], "Unknown")
        low = copy.deepcopy(self.by_id["address-0900-3412"])
        low["delimited"] = [53, 18]
        self.assertEqual(evaluate_case(rules, low)["leu16"], 4661)
        high = copy.deepcopy(self.by_id["address-0900-3412"])
        high["delimited"] = [52, 19]
        self.assertEqual(evaluate_case(rules, high)["leu16"], 4916)
        swapped = copy.deepcopy(self.by_id["address-0900-3412"])
        swapped["delimited"] = [18, 52]
        self.assertEqual(evaluate_case(rules, swapped)["leu16"], 13330)
        for width in ([], [52], [52, 18, 0]):
            short = copy.deepcopy(self.by_id["address-0900-3412"])
            short["delimited"] = width
            result = evaluate_case(rules, short)
            self.assertEqual(result["admission"], "incomplete")
            self.assertIsNone(result["leu16"])
            self.assertEqual(result["raw"], width)
        same = evaluate_case(rules, self.by_id["address-0901-3412"])
        self.assertEqual(same["leu16"], 4660)
        split = evaluate_case(rules, self.by_id["address-0902-3412"])
        self.assertEqual(split["low_u8"], 52)
        self.assertEqual(split["high_u8"], 18)
        self.assertIsNone(split["leu16"])
        other = evaluate_case(rules, self.by_id["address-0903-3412"])
        self.assertEqual((other["low_u8"], other["high_u8"], other["leu16"]), (52, 18, None))
        split_low = copy.deepcopy(self.by_id["address-0902-3412"])
        split_low["delimited"] = [53, 18]
        self.assertEqual(evaluate_case(rules, split_low)["low_u8"], 53)
        self.assertEqual(evaluate_case(rules, split_low)["high_u8"], 18)
        split_high = copy.deepcopy(self.by_id["address-0902-3412"])
        split_high["delimited"] = [52, 19]
        self.assertEqual(evaluate_case(rules, split_high)["high_u8"], 19)
        mismatched = copy.deepcopy(self.by_id["address-0900-3412"])
        mismatched["identity"]["service"] = "0902"
        self.assertEqual(evaluate_case(rules, mismatched)["admission"], "unmatched")
        self.assertIsNone(evaluate_case(rules, mismatched)["leu16"])

    def test_counts_stay_distinct_and_unclipped(self):
        rules = self.rules
        seen = []
        for value in (0, 10, 11, 255):
            result = evaluate_case(rules, self.by_id[f"count-0902-{value}"])
            self.assertEqual(result["value"], value)
            self.assertEqual(result["raw"], value)
            self.assertFalse(result["clipped"])
            self.assertFalse(result["rejected"])
            self.assertEqual(result["execution"], "not_executed")
            self.assertEqual(result["numeric_grade"], "Proven")
            self.assertEqual(result["semantic_grade"], "Hypothesis")
            self.assertEqual(result["native_grade"], "Unknown")
            seen.append(result["value"])
            plain = evaluate_case(rules, self.by_id[f"count-0900-{value}"])
            self.assertEqual(plain["value"], value)
            self.assertIsNone(plain["conflict"])
        self.assertEqual(len(set(seen)), 4)
        self.assertTrue(
            self.by_id["count-0902-11"]["expect"]["conflict"]["value_outside_candidate_recommendation"]
        )
        self.assertFalse(
            self.by_id["count-0902-10"]["expect"]["conflict"]["value_outside_candidate_recommendation"]
        )
        self.assertEqual(evaluate_case(rules, self.by_id["count-0901-inapplicable"])["admission"], "inapplicable")
        self.assertFalse(evaluate_case(rules, self.by_id["count-0901-inapplicable"])["rejected"])
        self.assertEqual(evaluate_case(rules, self.by_id["count-service-mismatch"])["admission"], "unmatched")

    def test_returned_sequences_are_isolated(self):
        rules = self.rules
        case = copy.deepcopy(self.by_id["body-0900-aa55"])
        first = evaluate_case(rules, case)
        second = evaluate_case(rules, case)
        self.assertIsNot(first["data"], second["data"])
        self.assertIsNot(first["raw_logical_bytes"], case["object"]["logical_bytes"])
        case["object"]["logical_bytes"][2] = 0
        self.assertEqual(first["data"], [170, 85])
        first["data"].append(7)
        self.assertEqual(second["data"], [170, 85])
        address = copy.deepcopy(self.by_id["address-0902-3412"])
        viewed = evaluate_case(rules, address)
        address["delimited"][0] = 0
        self.assertEqual(viewed["raw"], [52, 18])
        self.assertEqual(viewed["low_u8"], 52)

    def test_relative_page_links_resolve_locally(self):
        self.assertEqual(relative_link_errors(self.page_text), [])

    def test_executed_mutants_fail_closed(self):
        page = self.page_text
        fixture = self.fixture_text
        self.assertIsNone(diagnose(page, fixture))
        mutants = []

        def denial_mutant(key):
            def mutate(page_text, fixture_text):
                old = f"- {key}: denied"
                new = f"- {key}: allowed"
                if old not in page_text:
                    raise AssertionError(old)
                return page_text.replace(old, new, 1), fixture_text

            return mutate

        for key in DENIALS:
            mutants.append((f"denial {key}", denial_mutant(key)))

        def flag_mutant(name, transform):
            def mutate(page_text, fixture_text):
                contract = extract_contract(page_text)
                transform(contract)
                return replace_contract(page_text, contract), fixture_text

            return name, mutate

        mutants.append(flag_mutant("universal prefix", lambda rules: rules.__setitem__("universal_prefix_removal", True)))
        mutants.append(flag_mutant("infer 0902", lambda rules: rules.__setitem__("infer_0902_pb_sb", True)))
        mutants.append(
            flag_mutant(
                "prefix success",
                lambda rules: rules.__setitem__("prefix_only_positive_means_successful_mutation", True),
            )
        )
        mutants.append(flag_mutant("clip 11", lambda rules: rules.__setitem__("clip_count_11_to_10", True)))
        mutants.append(flag_mutant("invent offset", lambda rules: rules.__setitem__("invent_packet_offset", True)))
        mutants.append(
            flag_mutant(
                "address equivalence",
                lambda rules: rules.__setitem__("address_space_equivalence", True),
            )
        )
        mutants.append(
            flag_mutant(
                "mismatched service",
                lambda rules: rules.__setitem__("accept_mismatched_service", True),
            )
        )
        mutants.append(
            flag_mutant(
                "empty not representable",
                lambda rules: rules.__setitem__("empty_opaque_is_representable", False),
            )
        )
        mutants.append(
            flag_mutant(
                "reject 11",
                lambda rules: rules.__setitem__("reject_outside_candidate", True),
            )
        )
        mutants.append(
            flag_mutant(
                "meaning proven",
                lambda rules: rules["grades"].__setitem__("meaning", "Proven"),
            )
        )
        for field in MATCH_FIELDS:
            mutants.append(
                flag_mutant(
                    f"drop {field}",
                    lambda rules, field=field: rules.__setitem__(
                        "match_fields",
                        [item for item in rules["match_fields"] if item != field],
                    ),
                )
            )
        mutants.append(
            flag_mutant(
                "0902 kind",
                lambda rules: rules["body_rules"].__setitem__(
                    "0902",
                    {"kind": "constants_then_opaque", "pb": 9, "sb": 2, "data_start": 2},
                ),
            )
        )
        mutants.append(
            flag_mutant(
                "0900 data start",
                lambda rules: rules["body_rules"]["0900"].__setitem__("data_start", 0),
            )
        )
        mutants.append(
            flag_mutant(
                "0900 pb",
                lambda rules: rules["body_rules"]["0900"].__setitem__("pb", 8),
            )
        )
        mutants.append(
            flag_mutant(
                "0901 typed",
                lambda rules: rules["body_rules"].__setitem__(
                    "0901",
                    {"kind": "constants_then_opaque", "pb": 9, "sb": 1, "data_start": 2},
                ),
            )
        )
        mutants.append(
            flag_mutant(
                "0902 data start",
                lambda rules: rules["body_rules"]["0902"].__setitem__("data_start", 2),
            )
        )
        mutants.append(
            flag_mutant(
                "candidate max 11",
                lambda rules: rules["count_rules"]["0902"].__setitem__(
                    "candidate_recommendation_maximum", 11
                ),
            )
        )
        mutants.append(
            flag_mutant(
                "clip above 10",
                lambda rules: rules["count_rules"]["0902"].__setitem__("clip_above", 10),
            )
        )
        mutants.append(
            flag_mutant(
                "0902 leu16 form",
                lambda rules: rules["address_rules"]["0902"].__setitem__("form", "leu16"),
            )
        )
        mutants.append(
            flag_mutant(
                "big endian",
                lambda rules: rules["address_rules"]["0900"].__setitem__("endian", "big"),
            )
        )
        mutants.append(
            flag_mutant(
                "packet offset zero",
                lambda rules: rules["address_rules"]["0900"].__setitem__("packet_offset", 0),
            )
        )
        mutants.append(
            flag_mutant(
                "named space",
                lambda rules: rules["address_rules"]["0900"].__setitem__("address_space", "flat-16"),
            )
        )

        def fixture_mutant(name, case_id, transform):
            def mutate(page_text, fixture_text):
                fixture_data = json.loads(fixture_text)
                for case in fixture_data["cases"]:
                    if case["id"] == case_id:
                        transform(case)
                        break
                else:
                    raise AssertionError(case_id)
                return page_text, json.dumps(fixture_data, indent=2)

            return name, mutate

        mutants.append(
            fixture_mutant(
                "fixture strips 0902",
                "body-0902-aa55-kept",
                lambda case: case["expect"].__setitem__("data", [170, 85]),
            )
        )
        mutants.append(
            fixture_mutant(
                "fixture clips 11",
                "count-0902-11",
                lambda case: case["expect"].__setitem__("value", 10),
            )
        )
        mutants.append(
            fixture_mutant(
                "fixture equates split",
                "address-0902-3412",
                lambda case: case["expect"].__setitem__("leu16", 4660),
            )
        )
        mutants.append(
            fixture_mutant(
                "fixture accepts service",
                "body-service-mismatch",
                lambda case: case["expect"].__setitem__("admission", "represented"),
            )
        )

        tmp_root = os.environ.get("TMPDIR") or None
        killed = 0
        for name, mutate in mutants:
            with self.subTest(mutant=name):
                mutated_page, mutated_fixture = mutate(page, fixture)
                self.assertNotEqual((mutated_page, mutated_fixture), (page, fixture))
                with tempfile.TemporaryDirectory(dir=tmp_root) as directory:
                    page_copy = Path(directory) / "an26-standard09-body-views.md"
                    fixture_copy = Path(directory) / "an26_standard09_body_views.json"
                    page_copy.write_text(mutated_page, encoding="utf-8")
                    fixture_copy.write_text(mutated_fixture, encoding="utf-8")
                    reason = diagnose(page_copy.read_text(encoding="utf-8"), fixture_copy.read_text(encoding="utf-8"))
                self.assertIsNotNone(reason, name)
                killed += 1
        self.assertGreaterEqual(killed, 30)


if __name__ == "__main__":
    unittest.main()
