#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import sys
from decimal import Decimal, InvalidOperation
from typing import Any


GRAPH_CONTRACT = "helianthus.platform.draft-candidate-fact-graph.v1"
REGISTRY_CONTRACT = "helianthus.platform.draft-candidate-fact-registry.v1"
SOURCE_CONTRACT = "helianthus.platform.synchronized-evidence-bundle.v1"
NEGATIVE_FIXTURE_CONTRACT = (
    "helianthus.platform.draft-candidate-fact-negative-fixture.v1"
)
FACT_DOMAIN = b"HELIANTHUS:DRAFT-CANDIDATE-FACT:V1"
GRAPH_DOMAIN = b"HELIANTHUS:DRAFT-CANDIDATE-FACT-GRAPH:V1"
REPLAY_DOMAIN = b"HELIANTHUS:DRAFT-CANDIDATE-FACT-REPLAY:V1"
SAFE_INTEGER = 9007199254740991
DECIMAL_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
GRAPH_ID_RE = re.compile(r"^dcfgv1:sha256:[0-9a-f]{64}$")
BUNDLE_ID_RE = re.compile(r"^sebv1:sha256:[0-9a-f]{64}$")
CANDIDATE_ID_RE = re.compile(r"^m7-candidate-[0-9]{4}$")
PATH_RE = re.compile(r"^/[a-z0-9_]+(?:/[a-z0-9_]+)*$")

ROOT_KEYS = {
    "contract",
    "schema_version",
    "graph_id",
    "graph_hash",
    "registry",
    "source_bundle",
    "visibility",
    "limits",
    "comparator_drafts",
    "facts",
}
REGISTRY_BINDING_KEYS = {"contract", "version", "digest"}
SOURCE_BUNDLE_KEYS = {
    "contract",
    "schema_version",
    "bundle_id",
    "bundle_hash",
    "replay_hash",
    "evidence_refs",
}
VISIBILITY_KEYS = {
    "channel",
    "promotion_state",
    "stable_exposure",
    "command_capable",
    "protocol_translation",
}
LIMIT_KEYS = {
    "max_graph_bytes",
    "max_depth",
    "max_facts",
    "max_evidence_refs_per_fact",
    "max_samples_per_comparator",
    "max_string_bytes",
    "max_path_segments",
}
COMPARATOR_DRAFT_KEYS = {"draft_id", "type", "parameters"}
PARAMETER_KEYS = {
    "window",
    "tolerance",
    "unit_conversion",
    "rounding",
    "minimum_samples",
    "maximum_missing_samples",
    "stale_cutoff_ns",
    "conflict_threshold",
}
FACT_KEYS = {
    "candidate_id",
    "proposed_path",
    "draft_value",
    "draft_unit",
    "status",
    "terminal_negative_state",
    "confidence",
    "provenance",
    "comparator",
    "falsifier",
    "retest_trigger",
    "debug_only",
    "fact_hash",
}
CONFIDENCE_KEYS = {"level", "basis", "score_milli"}
PROVENANCE_KEYS = {
    "source_bundle_id",
    "native_evidence_refs",
    "ebus_source_id",
    "ebus_artifact_id",
    "ebus",
    "eebus_source_id",
    "eebus_artifact_id",
    "eebus",
    "cloud",
}
COMPARATOR_KEYS = {"draft_id", "samples", "outcome"}
SAMPLE_KEYS = {"offset_ns", "left_decimal", "right_decimal", "state"}
FALSIFIER_KEYS = {"condition_code", "expected_terminal_state", "description"}
RETEST_KEYS = {"trigger_code", "required_source_kinds", "minimum_new_samples"}
EVIDENCE_REF_KEYS = {
    "kind",
    "digest_algorithm",
    "digest",
    "repository",
    "commit",
    "path",
}


class Failure(Exception):
    pass


def fail(category: str) -> None:
    raise Failure(category)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("json.syntax")
        result[key] = value
    return result


def reject_float(_: str) -> None:
    fail("json.syntax")


def load_json(path: pathlib.Path) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError:
        fail("json.syntax")
    if re.search(rb"(?<![0-9A-Za-z_])-0(?:[^0-9.]|$)", raw):
        fail("json.syntax")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_float=reject_float,
            parse_constant=reject_float,
        )
    except Failure:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("json.syntax")
    return value, raw


def exact_keys(value: Any, expected: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        fail("schema.graph")


def canonical(value: Any) -> bytes:
    check_portable(value, 0, {"max_depth": 32, "max_string_bytes": 4096})
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest(domain: bytes, value: Any) -> str:
    return hashlib.sha256(domain + b"\0" + canonical(value)).hexdigest()


def fact_hexdigest(fact: dict[str, Any]) -> str:
    return digest(FACT_DOMAIN, {key: value for key, value in fact.items() if key != "fact_hash"})


def graph_hexdigest(graph: dict[str, Any]) -> str:
    return digest(
        GRAPH_DOMAIN,
        {key: value for key, value in graph.items() if key not in {"graph_id", "graph_hash"}},
    )


def check_portable(value: Any, depth: int, limits: dict[str, int]) -> None:
    if depth > limits["max_depth"]:
        fail("limits.exceeded")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if abs(value) > SAFE_INTEGER:
            fail("json.syntax")
        return
    if isinstance(value, float):
        fail("json.syntax")
    if isinstance(value, str):
        if len(value.encode("utf-8")) > limits["max_string_bytes"] or "\x00" in value:
            fail("limits.exceeded")
        return
    if isinstance(value, list):
        for item in value:
            check_portable(item, depth + 1, limits)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                fail("json.syntax")
            check_portable(key, depth + 1, limits)
            check_portable(item, depth + 1, limits)
        return
    fail("json.syntax")


def schema_check(graph: Any) -> None:
    exact_keys(graph, ROOT_KEYS)
    if graph["contract"] != GRAPH_CONTRACT or graph["schema_version"] != 1:
        fail("schema.graph")
    if not isinstance(graph["graph_id"], str) or not GRAPH_ID_RE.fullmatch(graph["graph_id"]):
        fail("schema.graph")
    if not isinstance(graph["graph_hash"], str) or not DIGEST_RE.fullmatch(graph["graph_hash"]):
        fail("schema.graph")
    exact_keys(graph["registry"], REGISTRY_BINDING_KEYS)
    exact_keys(graph["source_bundle"], SOURCE_BUNDLE_KEYS)
    exact_keys(graph["visibility"], VISIBILITY_KEYS)
    exact_keys(graph["limits"], LIMIT_KEYS)
    if not isinstance(graph["comparator_drafts"], list) or not graph["comparator_drafts"]:
        fail("schema.graph")
    if not isinstance(graph["facts"], list) or not graph["facts"]:
        fail("schema.graph")
    for draft in graph["comparator_drafts"]:
        exact_keys(draft, COMPARATOR_DRAFT_KEYS)
        exact_keys(draft["parameters"], PARAMETER_KEYS)
    for fact in graph["facts"]:
        exact_keys(fact, FACT_KEYS)
        exact_keys(fact["confidence"], CONFIDENCE_KEYS)
        exact_keys(fact["provenance"], PROVENANCE_KEYS)
        exact_keys(fact["comparator"], COMPARATOR_KEYS)
        exact_keys(fact["falsifier"], FALSIFIER_KEYS)
        exact_keys(fact["retest_trigger"], RETEST_KEYS)
        if not isinstance(fact["comparator"]["samples"], list):
            fail("schema.graph")
        for sample in fact["comparator"]["samples"]:
            exact_keys(sample, SAMPLE_KEYS)


def check_limits(graph: dict[str, Any], registry: dict[str, Any], raw_size: int) -> None:
    limits = graph["limits"]
    if limits != registry.get("limits"):
        fail("limits.exceeded")
    if raw_size > limits["max_graph_bytes"] or len(graph["facts"]) > limits["max_facts"]:
        fail("limits.exceeded")
    check_portable(graph, 0, limits)
    for fact in graph["facts"]:
        if len(fact["provenance"]["native_evidence_refs"]) > limits["max_evidence_refs_per_fact"]:
            fail("limits.exceeded")
        if len(fact["comparator"]["samples"]) > limits["max_samples_per_comparator"]:
            fail("limits.exceeded")
        path_segments = [part for part in fact["proposed_path"].split("/") if part]
        if len(path_segments) > limits["max_path_segments"]:
            fail("limits.exceeded")


def check_registry_binding(
    graph: dict[str, Any], registry: dict[str, Any], registry_raw: bytes
) -> None:
    binding = graph["registry"]
    expected_digest = "sha256:" + hashlib.sha256(registry_raw).hexdigest()
    if binding != {
        "contract": REGISTRY_CONTRACT,
        "version": 1,
        "digest": expected_digest,
    }:
        fail("registry.binding")
    expected_top = {
        "contract",
        "version",
        "candidate_contract",
        "source_contract",
        "statuses",
        "terminal_negative_states",
        "comparators",
        "candidate_channel",
        "forbidden_surfaces",
        "validation_precedence",
        "limits",
    }
    if not isinstance(registry, dict) or set(registry) != expected_top:
        fail("registry.binding")
    if registry["contract"] != REGISTRY_CONTRACT or registry["version"] != 1:
        fail("registry.binding")
    if registry["candidate_contract"].get("contract") != GRAPH_CONTRACT:
        fail("registry.binding")
    if registry["source_contract"].get("contract") != SOURCE_CONTRACT:
        fail("registry.binding")


def validate_evidence_ref(ref: Any) -> None:
    exact_keys(ref, EVIDENCE_REF_KEYS)
    if not isinstance(ref["digest"], str) or not DIGEST_RE.fullmatch(ref["digest"]):
        fail("provenance.binding")
    if ref["kind"] == "CONTENT":
        if (
            ref["digest_algorithm"] != "SHA256_CONTENT_BYTES"
            or ref["repository"] is not None
            or ref["commit"] is not None
            or ref["path"] is not None
        ):
            fail("provenance.binding")
    elif ref["kind"] == "GIT_BLOB":
        if (
            ref["digest_algorithm"] != "SHA256_GIT_BLOB_V1"
            or not isinstance(ref["repository"], str)
            or not isinstance(ref["commit"], str)
            or not re.fullmatch(r"[0-9a-f]{40}", ref["commit"])
            or not isinstance(ref["path"], str)
        ):
            fail("provenance.binding")
    else:
        fail("provenance.binding")


def ref_sort_key(ref: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(
        (0, "") if ref[field] is None else (1, ref[field])
        for field in ("kind", "digest_algorithm", "digest", "repository", "commit", "path")
    )


def check_provenance(graph: dict[str, Any], registry: dict[str, Any]) -> None:
    bundle = graph["source_bundle"]
    if (
        bundle["contract"] != registry["source_contract"]["contract"]
        or bundle["schema_version"] != registry["source_contract"]["schema_version"]
        or not isinstance(bundle["bundle_id"], str)
        or not BUNDLE_ID_RE.fullmatch(bundle["bundle_id"])
        or not isinstance(bundle["bundle_hash"], str)
        or not DIGEST_RE.fullmatch(bundle["bundle_hash"])
        or bundle["bundle_id"].removeprefix("sebv1:") != bundle["bundle_hash"]
        or not isinstance(bundle["replay_hash"], str)
        or not DIGEST_RE.fullmatch(bundle["replay_hash"])
        or not isinstance(bundle["evidence_refs"], list)
        or not bundle["evidence_refs"]
    ):
        fail("provenance.binding")
    root_refs: set[bytes] = set()
    for ref in bundle["evidence_refs"]:
        validate_evidence_ref(ref)
        encoded = canonical(ref)
        if encoded in root_refs:
            fail("provenance.binding")
        root_refs.add(encoded)
    for fact in graph["facts"]:
        provenance = fact["provenance"]
        if provenance["source_bundle_id"] != bundle["bundle_id"]:
            fail("provenance.binding")
        refs = provenance["native_evidence_refs"]
        if not isinstance(refs, list) or not refs:
            fail("provenance.binding")
        seen: set[bytes] = set()
        for ref in refs:
            validate_evidence_ref(ref)
            encoded = canonical(ref)
            if encoded not in root_refs or encoded in seen:
                fail("provenance.binding")
            seen.add(encoded)


def token(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value) <= 256 and "\x00" not in value


def byte_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 255


def word_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 65535


def validate_ebus_identity(identity: Any) -> None:
    if not isinstance(identity, dict):
        fail("identity.native")
    family = identity.get("family")
    common = all(token(identity.get(field)) for field in ("target_pseudonym", "unit_scale_source"))
    if family == "B509":
        expected = {
            "family",
            "target_pseudonym",
            "target_address",
            "target_product",
            "register_family",
            "register_id",
            "unit_scale_source",
            "evidence_role",
        }
        valid = (
            set(identity) == expected
            and common
            and byte_int(identity["target_address"])
            and token(identity["target_product"])
            and token(identity["register_family"])
            and word_int(identity["register_id"])
            and identity["evidence_role"] in {"AUTHORITATIVE", "MIRROR", "FALLBACK"}
        )
    elif family == "B524":
        expected = {
            "family",
            "target_pseudonym",
            "opcode",
            "GG",
            "II",
            "RR",
            "target_address",
            "source_address",
            "group_meaning",
            "instance_gate",
            "register_category",
            "unit_scale_source",
        }
        valid = (
            set(identity) == expected
            and common
            and all(byte_int(identity[field]) for field in ("opcode", "GG", "II", "target_address", "source_address"))
            and word_int(identity["RR"])
            and token(identity["group_meaning"])
            and token(identity["instance_gate"])
            and identity["register_category"] in {"STATE", "CONFIG", "PARAMS"}
        )
    elif family == "B555":
        expected = {
            "family",
            "target_pseudonym",
            "device_family",
            "schedule_program",
            "slot_index",
            "day_of_week",
            "time_identity",
            "operation_mode_context",
            "unit_scale_source",
        }
        valid = (
            set(identity) == expected
            and common
            and token(identity["device_family"])
            and token(identity["schedule_program"])
            and byte_int(identity["slot_index"])
            and identity["day_of_week"] in {"MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"}
            and isinstance(identity["time_identity"], str)
            and re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]", identity["time_identity"]) is not None
            and token(identity["operation_mode_context"])
        )
    else:
        valid = False
    if not valid:
        fail("identity.native")


def validate_eebus_path(value: Any) -> None:
    expected = {"service", "entity", "feature", "feature_path"}
    if not isinstance(value, dict) or set(value) != expected:
        fail("identity.native")
    if not all(token(value[field]) for field in ("service", "entity", "feature")):
        fail("identity.native")
    path = value["feature_path"]
    if not isinstance(path, list) or len(path) < 3 or len(path) > 32:
        fail("identity.native")
    for segment in path:
        if not isinstance(segment, dict) or set(segment) != {"kind", "selector"}:
            fail("identity.native")
        if segment["kind"] not in {"SERVICE", "ENTITY", "FEATURE", "FIELD"} or not token(segment["selector"]):
            fail("identity.native")
    if [segment["kind"] for segment in path[:3]] != ["SERVICE", "ENTITY", "FEATURE"]:
        fail("identity.native")
    if any(segment["kind"] != "FIELD" for segment in path[3:]):
        fail("identity.native")
    if [path[0]["selector"], path[1]["selector"], path[2]["selector"]] != [
        value["service"],
        value["entity"],
        value["feature"],
    ]:
        fail("identity.native")


def check_identities(graph: dict[str, Any]) -> None:
    for fact in graph["facts"]:
        provenance = fact["provenance"]
        if provenance["ebus"] is None:
            if provenance["ebus_source_id"] is not None or provenance["ebus_artifact_id"] is not None:
                fail("identity.native")
        else:
            if not token(provenance["ebus_source_id"]) or not token(provenance["ebus_artifact_id"]):
                fail("identity.native")
            validate_ebus_identity(provenance["ebus"])
        if provenance["eebus"] is None:
            if provenance["eebus_source_id"] is not None or provenance["eebus_artifact_id"] is not None:
                fail("identity.native")
        else:
            if not token(provenance["eebus_source_id"]) or not token(provenance["eebus_artifact_id"]):
                fail("identity.native")
            validate_eebus_path(provenance["eebus"])
        cloud = provenance["cloud"]
        if cloud is not None:
            if not isinstance(cloud, dict) or set(cloud) != {"source_id", "artifact_id", "evidence_id"}:
                fail("identity.native")
            if not all(token(cloud[field]) for field in cloud):
                fail("identity.native")


def check_ordering(graph: dict[str, Any]) -> None:
    refs = graph["source_bundle"]["evidence_refs"]
    if refs != sorted(refs, key=ref_sort_key):
        fail("ordering.invalid")
    facts = graph["facts"]
    if facts != sorted(facts, key=lambda fact: (fact["proposed_path"].encode(), fact["candidate_id"].encode())):
        fail("ordering.invalid")
    ids: set[str] = set()
    paths: set[str] = set()
    for fact in facts:
        if fact["candidate_id"] in ids or fact["proposed_path"] in paths:
            fail("ordering.invalid")
        ids.add(fact["candidate_id"])
        paths.add(fact["proposed_path"])
        refs = fact["provenance"]["native_evidence_refs"]
        if refs != sorted(refs, key=ref_sort_key):
            fail("ordering.invalid")
        samples = fact["comparator"]["samples"]
        if samples != sorted(samples, key=lambda sample: (sample["offset_ns"], canonical(sample))):
            fail("ordering.invalid")
        required = fact["retest_trigger"]["required_source_kinds"]
        if required != sorted(set(required), key=lambda value: value.encode()):
            fail("ordering.invalid")


def check_states(graph: dict[str, Any], registry: dict[str, Any]) -> None:
    statuses = set(registry["statuses"])
    terminals = set(registry["terminal_negative_states"])
    for fact in graph["facts"]:
        if not isinstance(fact["candidate_id"], str) or not CANDIDATE_ID_RE.fullmatch(fact["candidate_id"]):
            fail("state.terminal")
        if not isinstance(fact["proposed_path"], str) or not PATH_RE.fullmatch(fact["proposed_path"]):
            fail("state.terminal")
        status = fact["status"]
        terminal = fact["terminal_negative_state"]
        if status not in statuses or (terminal is not None and terminal not in terminals):
            fail("state.terminal")
        if fact["debug_only"] is not True:
            fail("state.terminal")
        if terminal is not None:
            if status != "WITHHELD" or fact["draft_value"] is not None or fact["draft_unit"] is not None:
                fail("state.terminal")
        elif status == "WITHHELD":
            fail("state.terminal")
        confidence = fact["confidence"]
        if (
            confidence["level"] not in {"LOW", "MEDIUM", "HIGH"}
            or confidence["basis"] not in {"OBSERVED", "INFERRED", "INSUFFICIENT"}
            or not isinstance(confidence["score_milli"], int)
            or not 0 <= confidence["score_milli"] <= 1000
        ):
            fail("state.terminal")
        falsifier = fact["falsifier"]
        if (
            falsifier["condition_code"] not in {"VALUE_DIVERGES", "IDENTITY_CHANGES", "SIGNAL_DISAPPEARS", "ORDER_CHANGES", "PROVENANCE_BREAKS"}
            or falsifier["expected_terminal_state"] not in terminals
            or not token(falsifier["description"])
        ):
            fail("state.terminal")
        trigger = fact["retest_trigger"]
        if (
            trigger["trigger_code"] not in {"NEW_SYNCHRONIZED_BUNDLE", "SOURCE_RECOVERED", "IDENTITY_CONFIRMED", "COMPARATOR_REVISED"}
            or not isinstance(trigger["minimum_new_samples"], int)
            or not 1 <= trigger["minimum_new_samples"] <= 1024
            or not isinstance(trigger["required_source_kinds"], list)
            or not trigger["required_source_kinds"]
            or not set(trigger["required_source_kinds"]) <= {"CLOUD_APP", "EBUS", "EEBUS"}
        ):
            fail("state.terminal")


def decimal(value: Any, *, nonnegative: bool = False) -> Decimal:
    if not isinstance(value, str) or not DECIMAL_RE.fullmatch(value):
        fail("comparator.invalid")
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        fail("comparator.invalid")
    if nonnegative and parsed < 0:
        fail("comparator.invalid")
    return parsed


def check_comparators(graph: dict[str, Any], registry: dict[str, Any]) -> None:
    drafts = graph["comparator_drafts"]
    if len(drafts) != 1:
        fail("comparator.invalid")
    draft = drafts[0]
    if draft["draft_id"] != "NUMERIC_WINDOW_V1_DRAFT" or draft["type"] != "NUMERIC_WINDOW":
        fail("comparator.invalid")
    if registry["comparators"][0]["draft_id"] != draft["draft_id"]:
        fail("comparator.invalid")
    parameters = draft["parameters"]
    window = parameters["window"]
    tolerance = parameters["tolerance"]
    conversion = parameters["unit_conversion"]
    rounding = parameters["rounding"]
    threshold = parameters["conflict_threshold"]
    for value, keys in (
        (window, {"start_offset_ns", "end_offset_ns"}),
        (tolerance, {"absolute_decimal", "relative_ppm"}),
        (conversion, {"mode", "source_unit", "target_unit", "scale_decimal", "offset_decimal"}),
        (rounding, {"mode", "decimal_places"}),
        (threshold, {"absolute_decimal", "consecutive_samples"}),
    ):
        if not isinstance(value, dict) or set(value) != keys:
            fail("comparator.invalid")
    if (
        not isinstance(window["start_offset_ns"], int)
        or not isinstance(window["end_offset_ns"], int)
        or not 0 <= window["start_offset_ns"] < window["end_offset_ns"]
        or not isinstance(tolerance["relative_ppm"], int)
        or tolerance["relative_ppm"] < 0
        or conversion["mode"] not in {"IDENTITY", "AFFINE"}
        or not token(conversion["source_unit"])
        or not token(conversion["target_unit"])
        or rounding["mode"] not in {"NONE", "HALF_EVEN"}
        or (rounding["decimal_places"] is not None and (not isinstance(rounding["decimal_places"], int) or not 0 <= rounding["decimal_places"] <= 9))
        or not isinstance(parameters["minimum_samples"], int)
        or parameters["minimum_samples"] < 1
        or not isinstance(parameters["maximum_missing_samples"], int)
        or parameters["maximum_missing_samples"] < 0
        or not isinstance(parameters["stale_cutoff_ns"], int)
        or parameters["stale_cutoff_ns"] < 1
        or not isinstance(threshold["consecutive_samples"], int)
        or threshold["consecutive_samples"] < 1
    ):
        fail("comparator.invalid")
    decimal(tolerance["absolute_decimal"], nonnegative=True)
    decimal(conversion["scale_decimal"])
    decimal(conversion["offset_decimal"])
    decimal(threshold["absolute_decimal"], nonnegative=True)
    for fact in graph["facts"]:
        evaluation = fact["comparator"]
        if evaluation["draft_id"] != draft["draft_id"]:
            fail("comparator.invalid")
        samples = evaluation["samples"]
        present = 0
        missing = 0
        for sample in samples:
            if (
                not isinstance(sample["offset_ns"], int)
                or not window["start_offset_ns"] <= sample["offset_ns"] <= window["end_offset_ns"]
                or sample["state"] not in {"PRESENT", "MISSING", "STALE"}
            ):
                fail("comparator.invalid")
            if sample["state"] == "MISSING":
                missing += 1
                if sample["left_decimal"] is not None or sample["right_decimal"] is not None:
                    fail("comparator.invalid")
            else:
                if sample["left_decimal"] is None or sample["right_decimal"] is None:
                    fail("comparator.invalid")
                decimal(sample["left_decimal"])
                decimal(sample["right_decimal"])
                if sample["state"] == "PRESENT":
                    present += 1
        if missing > parameters["maximum_missing_samples"]:
            fail("comparator.invalid")
        status = fact["status"]
        outcome = evaluation["outcome"]
        expected = {
            "RAW_ONLY": {"NOT_EVALUATED"},
            "CANDIDATE": {"MATCH"},
            "CONFLICTED": {"CONFLICT"},
            "WITHHELD": {"NOT_EVALUATED", "CONFLICT"},
        }
        if outcome not in expected[status]:
            fail("comparator.invalid")
        if status in {"CANDIDATE", "CONFLICTED"} and present < parameters["minimum_samples"]:
            fail("comparator.invalid")
        terminal = fact["terminal_negative_state"]
        if terminal == "CONFLICT" and outcome != "CONFLICT":
            fail("comparator.invalid")
        if terminal in {"NO_SIGNAL", "CLOUD_ONLY", "NOT_TESTED"} and outcome != "NOT_EVALUATED":
            fail("comparator.invalid")


def check_anti_leak(graph: dict[str, Any], registry: dict[str, Any]) -> None:
    if graph["visibility"] != {
        "channel": registry["candidate_channel"],
        "promotion_state": "NOT_PROMOTED",
        "stable_exposure": False,
        "command_capable": False,
        "protocol_translation": False,
    }:
        fail("anti_leak.consumer")


def check_hashes(graph: dict[str, Any]) -> None:
    for fact in graph["facts"]:
        expected = "sha256:" + fact_hexdigest(fact)
        if fact["fact_hash"] != expected:
            fail("hash.fact")
    hexdigest = graph_hexdigest(graph)
    if graph["graph_hash"] != "sha256:" + hexdigest or graph["graph_id"] != "dcfgv1:sha256:" + hexdigest:
        fail("hash.graph")


def verify(
    graph: Any,
    registry: dict[str, Any],
    registry_raw: bytes,
    raw_size: int,
) -> dict[str, Any]:
    schema_check(graph)
    check_limits(graph, registry, raw_size)
    check_registry_binding(graph, registry, registry_raw)
    check_provenance(graph, registry)
    check_identities(graph)
    check_ordering(graph)
    check_states(graph, registry)
    check_comparators(graph, registry)
    check_anti_leak(graph, registry)
    check_hashes(graph)
    return graph


def replay(graph: dict[str, Any]) -> dict[str, Any]:
    results = []
    for fact in graph["facts"]:
        results.append(
            {
                "candidate_id": fact["candidate_id"],
                "proposed_path": fact["proposed_path"],
                "status": fact["status"],
                "terminal_negative_state": fact["terminal_negative_state"],
                "confidence": fact["confidence"],
                "comparator_outcome": fact["comparator"]["outcome"],
                "fact_hash": fact["fact_hash"],
                "native_evidence_digests": sorted(
                    {ref["digest"] for ref in fact["provenance"]["native_evidence_refs"]}
                ),
            }
        )
    value = {
        "contract": "helianthus.platform.draft-candidate-fact-replay.v1",
        "schema_version": 1,
        "replay_id": "dcfrv1:sha256:" + "0" * 64,
        "replay_hash": "sha256:" + "0" * 64,
        "graph_id": graph["graph_id"],
        "graph_hash": graph["graph_hash"],
        "registry_digest": graph["registry"]["digest"],
        "source_bundle": {
            "bundle_id": graph["source_bundle"]["bundle_id"],
            "bundle_hash": graph["source_bundle"]["bundle_hash"],
            "replay_hash": graph["source_bundle"]["replay_hash"],
        },
        "results": results,
    }
    view = {key: item for key, item in value.items() if key not in {"replay_id", "replay_hash"}}
    hexdigest = digest(REPLAY_DOMAIN, view)
    value["replay_id"] = "dcfrv1:sha256:" + hexdigest
    value["replay_hash"] = "sha256:" + hexdigest
    return value


def expand_negative_fixture(path: pathlib.Path, value: Any) -> Any:
    if not isinstance(value, dict) or value.get("contract") != NEGATIVE_FIXTURE_CONTRACT:
        return value
    if set(value) != {"contract", "base", "mutation"} or value["base"] != "../positive/graph.json":
        fail("json.syntax")
    base_path = path.parent.parent / "positive/graph.json"
    graph, _ = load_json(base_path)
    graph = copy.deepcopy(graph)
    mutation = value["mutation"]
    if mutation == "ANTI_LEAK_STABLE_SURFACE":
        graph["visibility"]["stable_exposure"] = True
    elif mutation == "COMPARATOR_PARAMETER_INVALID":
        graph["comparator_drafts"][0]["parameters"]["minimum_samples"] = 0
    elif mutation == "EVIDENCE_REF_NOT_IN_BUNDLE":
        graph["facts"][0]["provenance"]["native_evidence_refs"][0]["digest"] = "sha256:" + "f" * 64
    elif mutation == "GRAPH_HASH_MISMATCH":
        graph["graph_hash"] = "sha256:" + "0" * 64
    elif mutation == "INCOMPLETE_B524_IDENTITY":
        target = next(fact for fact in graph["facts"] if fact["provenance"]["ebus"] and fact["provenance"]["ebus"]["family"] == "B524")
        del target["provenance"]["ebus"]["RR"]
    elif mutation == "INVALID_EEBUS_FEATURE_PATH":
        target = next(fact for fact in graph["facts"] if fact["provenance"]["eebus"] is not None)
        target["provenance"]["eebus"]["feature_path"][0]["kind"] = "FEATURE"
    elif mutation == "LIMIT_EXCEEDED":
        graph["limits"]["max_facts"] = 65
    elif mutation == "ORDERING_INVALID":
        graph["facts"].reverse()
    elif mutation == "REGISTRY_MISMATCH":
        graph["registry"]["digest"] = "sha256:" + "0" * 64
    elif mutation == "TERMINAL_STATE_NOT_WITHHELD":
        target = next(fact for fact in graph["facts"] if fact["terminal_negative_state"] is not None)
        target["status"] = "CANDIDATE"
    elif mutation == "UNKNOWN_FIELD":
        graph["unknown"] = True
    else:
        fail("json.syntax")
    return graph


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("command", choices=("verify", "replay"))
    parser.add_argument("--graph", type=pathlib.Path, required=True)
    parser.add_argument("--registry", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        value, raw = load_json(args.graph)
        registry, registry_raw = load_json(args.registry)
        graph = expand_negative_fixture(args.graph, value)
        verified = verify(graph, registry, registry_raw, len(raw))
        if args.command == "verify":
            sys.stdout.write("ok\n")
        else:
            sys.stdout.write(canonical(replay(verified)).decode("utf-8") + "\n")
        return 0
    except Failure as error:
        sys.stdout.write(str(error) + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
