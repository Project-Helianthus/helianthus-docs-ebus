#!/usr/bin/env python3
"""Fail-closed verifier for the MSP-08 EEBUS-G18 coexistence contract."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import sys
from typing import Any


SCRIPT_ROOT = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))
import validate_candidate_fact_graph as candidate


EVIDENCE_CONTRACT = "helianthus.platform.multi-runtime-coexistence-evidence.v1"
REGISTRY_CONTRACT = "helianthus.platform.multi-runtime-coexistence-registry.v1"
REPORT_CONTRACT = "helianthus.platform.multi-runtime-coexistence-report.v1"
RAW_PAYLOAD_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-RAW-PAYLOAD:V1"
SHAPE_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-PAYLOAD-SHAPE:V1"
CANONICAL_PAYLOAD_DOMAIN = (
    b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-CANONICAL-PAYLOAD:V1"
)
PROFILE_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-NORMALIZATION:V1"
CLOCK_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-CLOCK:V1"
BUILD_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-BUILD:V1"
CONFIG_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-CONFIG:V1"
AUTH_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-AUTH:V1"
EVIDENCE_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-EVIDENCE:V1"
REPORT_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-REPORT:V1"
SAFE_INTEGER = 9_007_199_254_740_991
BASELINE_SOURCE_SHA = "ff511b035b85aef6123fb0853bb3d2f3af6fc01e"
EXPECTED_REGISTRY_SHA256 = "82cf854d335da31dcda65ff45a024cbb4a1ce515965cb8165122c0b4ef7d8505"
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TOKEN_RE = re.compile(r"^[\x20-\x7e]+$")
RFC3339_UTC_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z$"
)
HARD_LIMITS = {
    "max_evidence_bytes": 2_097_152,
    "max_depth": 32,
    "max_runs": 8,
    "max_views_per_run": 16,
    "max_inputs_per_run": 16,
    "max_internal_facts_per_run": 64,
    "max_payload_bytes": 262_144,
    "max_string_bytes": 4_096,
    "max_total_members": 65_536,
    "max_total_list_items": 32_768,
}


class Failure(Exception):
    pass


def fail(category: str) -> None:
    raise Failure(category)


def canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest(domain: bytes, value: Any) -> str:
    return "sha256:" + hashlib.sha256(domain + b"\0" + canonical(value)).hexdigest()


def _bounded_preflight(raw: bytes) -> None:
    if len(raw) > HARD_LIMITS["max_evidence_bytes"]:
        fail("limits.exceeded")
    depth = 0
    members = 0
    items = 0
    in_string = False
    escaped = False
    string_bytes = 0
    for byte in raw:
        if in_string:
            if escaped:
                escaped = False
                string_bytes += 1
            elif byte == 0x5C:
                escaped = True
                string_bytes += 1
            elif byte == 0x22:
                in_string = False
            else:
                string_bytes += 1
            if string_bytes > HARD_LIMITS["max_string_bytes"]:
                fail("limits.exceeded")
            continue
        if byte == 0x22:
            in_string = True
            string_bytes = 0
        elif byte in (0x7B, 0x5B):
            depth += 1
            if depth > HARD_LIMITS["max_depth"]:
                fail("limits.exceeded")
        elif byte in (0x7D, 0x5D):
            depth -= 1
        elif byte == 0x3A:
            members += 1
            if members > HARD_LIMITS["max_total_members"]:
                fail("limits.exceeded")
        elif byte == 0x2C:
            items += 1
            if items > HARD_LIMITS["max_total_list_items"]:
                fail("limits.exceeded")


def load_json(path: pathlib.Path, category: str, *, bounded: bool = False) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError:
        fail(category)
    if bounded:
        _bounded_preflight(raw)
    if re.search(rb"(?<![0-9A-Za-z_])-0(?:[^0-9.]|$)", raw):
        fail(category)

    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                fail(category)
            result[key] = value
        return result

    def integer(value: str) -> int:
        parsed = int(value)
        if abs(parsed) > SAFE_INTEGER:
            fail(category)
        return parsed

    def reject_number(_: str) -> None:
        fail(category)

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_int=integer,
            parse_float=reject_number,
            parse_constant=reject_number,
        )
    except Failure:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        fail(category)
    return value, raw


def exact(value: Any, keys: set[str], category: str = "schema.evidence") -> None:
    if not isinstance(value, dict) or set(value) != keys:
        fail(category)


def integer(value: Any, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def token(value: Any, maximum: int = 256) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value.encode("utf-8")) <= maximum
        and TOKEN_RE.fullmatch(value) is not None
    )


def _portable(value: Any, counters: dict[str, int], depth: int = 0) -> None:
    if depth > HARD_LIMITS["max_depth"]:
        fail("limits.exceeded")
    if isinstance(value, dict):
        counters["members"] += len(value)
        if counters["members"] > HARD_LIMITS["max_total_members"]:
            fail("limits.exceeded")
        for key, item in value.items():
            if not token(key, HARD_LIMITS["max_string_bytes"]):
                fail("schema.evidence")
            _portable(item, counters, depth + 1)
    elif isinstance(value, list):
        counters["items"] += len(value)
        if counters["items"] > HARD_LIMITS["max_total_list_items"]:
            fail("limits.exceeded")
        for item in value:
            _portable(item, counters, depth + 1)
    elif isinstance(value, str):
        if (
            len(value.encode("utf-8")) > HARD_LIMITS["max_string_bytes"]
            or "\x00" in value
        ):
            fail("limits.exceeded")
    elif isinstance(value, bool) or value is None:
        return
    elif isinstance(value, int):
        if abs(value) > SAFE_INTEGER:
            fail("json.syntax")
    else:
        fail("json.syntax")


def schema_check(evidence: Any) -> None:
    schema_path = (
        SCRIPT_ROOT.parent
        / "docs/platform/schemas/multi-runtime-coexistence-evidence-v1.schema.json"
    )
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail("schema.evidence")
    if not candidate._schema_validate(evidence, schema, schema):
        fail("schema.evidence")
    exact(
        evidence,
        {
            "contract",
            "schema_version",
            "fixture_id",
            "evidence_class",
            "evidence_id",
            "evidence_hash",
            "registry",
            "scope",
            "m7_binding",
            "capture_clock",
            "normalization",
            "limits",
            "runs",
        },
    )
    if (
        evidence["contract"] != EVIDENCE_CONTRACT
        or evidence["schema_version"] != 1
        or not token(evidence["fixture_id"], 128)
        or evidence["evidence_class"]
        not in {"SYNTHETIC_OFFLINE_FIXTURE", "CAPTURED_RUNTIME_EVIDENCE"}
        or not isinstance(evidence["evidence_id"], str)
        or not re.fullmatch(r"mrcv1:sha256:[0-9a-f]{64}", evidence["evidence_id"])
        or not isinstance(evidence["evidence_hash"], str)
        or not DIGEST_RE.fullmatch(evidence["evidence_hash"])
        or not isinstance(evidence["runs"], list)
    ):
        fail("schema.evidence")
    exact(evidence["registry"], {"contract", "version", "digest"})
    exact(
        evidence["scope"],
        {"gate", "claims", "excluded_gates", "live_vr940_claim", "public_version_policy"},
    )
    exact(
        evidence["m7_binding"],
        {
            "completion_token",
            "docs_source_commit",
            "graph_contract",
            "graph_id",
            "graph_hash",
            "replay_contract",
            "replay_id",
            "replay_hash",
        },
    )
    exact(
        evidence["capture_clock"],
        {
            "clock_id",
            "basis",
            "wall_anchor_utc",
            "monotonic_epoch_id",
            "max_clock_error_ns",
            "max_capture_age_ns",
            "verification_offset_ns",
            "clock_hash",
        },
    )
    exact(
        evidence["normalization"],
        {
            "profile_id",
            "canonicalization",
            "timestamp_replacement",
            "mask_replacement",
            "view_rules",
            "profile_digest",
        },
    )
    exact(evidence["limits"], set(HARD_LIMITS))
    for rule in evidence["normalization"]["view_rules"]:
        exact(rule, {"view_id", "capture_path", "timestamp_pointers", "mask_pointers"})
        if not all(
            isinstance(rule[name], list)
            for name in ("timestamp_pointers", "mask_pointers")
        ):
            fail("schema.evidence")
    for run in evidence["runs"]:
        exact(
            run,
            {"run_id", "state", "capture_offset_ns", "provenance", "state_evidence", "protected_views"},
        )
        if not token(run["run_id"]) or not integer(run["capture_offset_ns"]):
            fail("schema.evidence")
        provenance = run["provenance"]
        exact(
            provenance,
            {"capture_clock_id", "runtime", "config", "auth_scope", "mask_scope_digest", "immutable_inputs"},
        )
        runtime = provenance["runtime"]
        exact(
            runtime,
            {
                "repository",
                "source_commit",
                "source_parent_commit",
                "artifact_id",
                "artifact_digest",
                "artifact_size_bytes",
                "build_manifest",
                "build_manifest_hash",
            },
        )
        exact(runtime["build_manifest"], {"go_version", "target", "build_mode", "flags"})
        config = provenance["config"]
        exact(config, {"config_id", "payload", "config_hash"})
        exact(
            config["payload"],
            {"eebus_runtime_enabled", "candidate_graph_enabled", "outbound_enabled", "public_v2_enabled"},
        )
        auth = provenance["auth_scope"]
        exact(auth, {"scope_id", "principal_class", "permissions", "scope_hash"})
        if not isinstance(provenance["immutable_inputs"], list):
            fail("schema.evidence")
        for item in provenance["immutable_inputs"]:
            exact(item, {"input_id", "kind", "digest", "byte_length"})
        state = run["state_evidence"]
        exact(
            state,
            {
                "outcome",
                "eebus_runtime_enabled",
                "candidate_graph_enabled",
                "service_count",
                "candidate_count",
                "conflict_count",
                "degraded",
                "empty_success",
                "facts",
            },
        )
        if not isinstance(state["facts"], list) or not isinstance(run["protected_views"], list):
            fail("schema.evidence")
        for fact in state["facts"]:
            exact(fact, {"candidate_id", "status", "terminal_negative_state", "visibility_channel"})
        for view in run["protected_views"]:
            exact(
                view,
                {"view_id", "capture_path", "media_type", "payload", "raw_payload_hash", "shape_hash", "canonical_payload_hash"},
            )
    _portable(evidence, {"members": 0, "items": 0})


def check_limits(evidence: dict[str, Any], raw_size: int) -> None:
    if evidence["limits"] != HARD_LIMITS or raw_size > HARD_LIMITS["max_evidence_bytes"]:
        fail("limits.exceeded")
    if len(evidence["runs"]) > HARD_LIMITS["max_runs"]:
        fail("limits.exceeded")
    for run in evidence["runs"]:
        if (
            len(run["protected_views"]) > HARD_LIMITS["max_views_per_run"]
            or len(run["provenance"]["immutable_inputs"])
            > HARD_LIMITS["max_inputs_per_run"]
            or len(run["state_evidence"]["facts"])
            > HARD_LIMITS["max_internal_facts_per_run"]
        ):
            fail("limits.exceeded")
        for view in run["protected_views"]:
            if len(canonical(view["payload"])) > HARD_LIMITS["max_payload_bytes"]:
                fail("limits.exceeded")


def check_registry(evidence: dict[str, Any], registry: Any, raw: bytes) -> None:
    exact(
        registry,
        {
            "contract",
            "version",
            "evidence_contract",
            "report_contract",
            "gate",
            "excluded_gates",
            "m7_completion_token",
            "m7_docs_source_commit",
            "m7_binding",
            "scenario_order",
            "protected_views",
            "view_rules",
            "required_acceptance_checks",
            "validation_precedence",
            "limits",
            "fixture_ids",
        },
        "registry.binding",
    )
    expected_digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    if (
        hashlib.sha256(raw).hexdigest() != EXPECTED_REGISTRY_SHA256
        or
        registry["contract"] != REGISTRY_CONTRACT
        or registry["version"] != 1
        or registry["limits"] != HARD_LIMITS
        or evidence["registry"]
        != {"contract": REGISTRY_CONTRACT, "version": 1, "digest": expected_digest}
    ):
        fail("registry.binding")


def _verify_m7(
    evidence: dict[str, Any],
    registry: dict[str, Any],
    paths: dict[str, pathlib.Path],
) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
    try:
        graph, graph_raw = candidate.load_json(paths["graph"], input_kind="graph")
        m7_registry, m7_registry_raw = candidate.load_json(
            paths["registry"], input_kind="registry"
        )
        source_bundle, source_bundle_raw = candidate.load_json(
            paths["source_bundle"], input_kind="source"
        )
        source_replay, _ = candidate.load_json(paths["source_replay"], input_kind="source")
        verified_source, verified_source_replay = candidate._verify_source_inputs(
            m7_registry,
            paths["registry"],
            source_bundle,
            source_bundle_raw,
            source_replay,
        )
        candidate.verify(
            graph,
            m7_registry,
            m7_registry_raw,
            len(graph_raw),
            verified_source,
            verified_source_replay,
        )
        replay, replay_raw = candidate.load_json(paths["replay"], input_kind="source")
        if candidate.replay(graph) != replay:
            fail("provenance.m7")
    except Failure:
        raise
    except (candidate.Failure, KeyError, TypeError, ValueError, OSError):
        fail("provenance.m7")
    expected = {
        "completion_token": registry["m7_completion_token"],
        "docs_source_commit": registry["m7_docs_source_commit"],
        **registry["m7_binding"],
    }
    actual = {
        "completion_token": evidence["m7_binding"]["completion_token"],
        "docs_source_commit": evidence["m7_binding"]["docs_source_commit"],
        "graph_contract": graph["contract"],
        "graph_id": graph["graph_id"],
        "graph_hash": graph["graph_hash"],
        "replay_contract": replay["contract"],
        "replay_id": replay["replay_id"],
        "replay_hash": replay["replay_hash"],
    }
    if evidence["m7_binding"] != expected or actual != expected:
        fail("provenance.m7")
    return graph, replay, graph_raw, replay_raw


def check_runtime(
    evidence: dict[str, Any], graph: dict[str, Any], replay: dict[str, Any]
) -> None:
    baseline = evidence["runs"][0]["provenance"]["runtime"]
    if baseline["source_commit"] != BASELINE_SOURCE_SHA or baseline["source_parent_commit"] is not None:
        fail("provenance.runtime")
    compared_runtime = evidence["runs"][1]["provenance"]["runtime"]
    if compared_runtime["source_parent_commit"] != BASELINE_SOURCE_SHA:
        fail("provenance.runtime")
    for run in evidence["runs"]:
        runtime = run["provenance"]["runtime"]
        if (
            runtime["repository"]
            != "github.com/Project-Helianthus/helianthus-ebusgateway"
            or not SHA_RE.fullmatch(runtime["source_commit"])
            or runtime["artifact_id"]
            != "gateway:" + runtime["artifact_digest"]
            or runtime["build_manifest_hash"]
            != digest(BUILD_DOMAIN, runtime["build_manifest"])
            or not integer(runtime["artifact_size_bytes"], 1)
        ):
            fail("provenance.runtime")
    for run in evidence["runs"][1:]:
        if run["provenance"]["runtime"] != compared_runtime:
            fail("provenance.runtime")
    m7_sizes = {
        "m7:graph": (graph["graph_hash"], len(canonical(graph))),
        "m7:replay": (replay["replay_hash"], len(canonical(replay))),
    }
    for run in evidence["runs"]:
        views = {view["view_id"]: view for view in run["protected_views"]}
        expected = {
            f"view:{view_id}": (view["raw_payload_hash"], len(canonical(view["payload"])))
            for view_id, view in views.items()
        }
        expected.update(m7_sizes)
        actual = {
            item["input_id"]: (item["digest"], item["byte_length"])
            for item in run["provenance"]["immutable_inputs"]
        }
        if actual != expected:
            fail("provenance.runtime")


def check_config(evidence: dict[str, Any]) -> None:
    for run in evidence["runs"]:
        config = run["provenance"]["config"]
        if config["config_hash"] != digest(CONFIG_DOMAIN, config["payload"]):
            fail("provenance.config")
        if config["payload"]["outbound_enabled"] or config["payload"]["public_v2_enabled"]:
            fail("provenance.config")


def check_auth_mask(evidence: dict[str, Any]) -> None:
    profile = evidence["normalization"]
    profile_view = {key: value for key, value in profile.items() if key != "profile_digest"}
    if profile["profile_digest"] != digest(PROFILE_DOMAIN, profile_view):
        fail("provenance.auth_mask")
    first_auth = evidence["runs"][0]["provenance"]["auth_scope"]
    for run in evidence["runs"]:
        provenance = run["provenance"]
        auth = provenance["auth_scope"]
        auth_view = {key: value for key, value in auth.items() if key != "scope_hash"}
        if (
            auth != first_auth
            or auth["principal_class"] != "READ_ONLY_TEST"
            or auth["scope_hash"] != digest(AUTH_DOMAIN, auth_view)
            or provenance["mask_scope_digest"] != profile["profile_digest"]
        ):
            fail("provenance.auth_mask")


def check_clock(evidence: dict[str, Any]) -> None:
    clock = evidence["capture_clock"]
    view = {key: value for key, value in clock.items() if key != "clock_hash"}
    if (
        clock["basis"] != "MONOTONIC_CAPTURE_OFFSETS"
        or not isinstance(clock["wall_anchor_utc"], str)
        or not RFC3339_UTC_RE.fullmatch(clock["wall_anchor_utc"])
        or clock["clock_hash"] != digest(CLOCK_DOMAIN, view)
        or not integer(clock["verification_offset_ns"])
        or not integer(clock["max_capture_age_ns"], 1)
    ):
        fail("provenance.clock")
    for run in evidence["runs"]:
        if (
            run["provenance"]["capture_clock_id"] != clock["clock_id"]
            or run["capture_offset_ns"] > clock["verification_offset_ns"]
            or clock["verification_offset_ns"] - run["capture_offset_ns"]
            > clock["max_capture_age_ns"]
        ):
            fail("provenance.clock")


def check_ordering(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    runs = evidence["runs"]
    if [run["state"] for run in runs] != registry["scenario_order"]:
        fail("ordering.duplicate")
    if len({run["run_id"] for run in runs}) != len(runs):
        fail("ordering.duplicate")
    offsets = [run["capture_offset_ns"] for run in runs]
    if offsets != sorted(offsets) or len(set(offsets)) != len(offsets):
        fail("ordering.duplicate")
    for run in runs:
        views = [view["view_id"] for view in run["protected_views"]]
        inputs = [item["input_id"] for item in run["provenance"]["immutable_inputs"]]
        expected_inputs = [f"view:{item}" for item in views] + ["m7:graph", "m7:replay"]
        if (
            len(views) != len(set(views))
            or len(inputs) != len(set(inputs))
            or inputs != expected_inputs
            or (
                len(views) == len(registry["protected_views"])
                and views != registry["protected_views"]
            )
        ):
            fail("ordering.duplicate")


def check_states(evidence: dict[str, Any]) -> None:
    expected = {
        "EEBUS_DISABLED_BASELINE": ("BASELINE_CAPTURED", False, False, 0, 0, 0, False, []),
        "EEBUS_DISABLED_CONFIRMED": ("DISABLED_CONFIRMED", False, False, 0, 0, 0, False, []),
        "EEBUS_ENABLED_NO_SERVICES": ("NO_SERVICES_OBSERVED", True, True, 0, 0, 0, True, []),
        "EEBUS_CONNECTED_CANDIDATE_ONLY": (
            "CANDIDATE_ONLY_OBSERVED",
            True,
            True,
            1,
            1,
            0,
            False,
            [{"candidate_id": "m7-candidate-synthetic-0001", "status": "CANDIDATE", "terminal_negative_state": None, "visibility_channel": "CANDIDATE_DEBUG_REPLAY"}],
        ),
        "EEBUS_CONFLICTED_WITHHELD": (
            "CONFLICT_WITHHELD_OBSERVED",
            True,
            True,
            1,
            0,
            1,
            True,
            [{"candidate_id": "m7-candidate-synthetic-conflict-0001", "status": "WITHHELD", "terminal_negative_state": "CONFLICT", "visibility_channel": "CANDIDATE_DEBUG_REPLAY"}],
        ),
        "EEBUS_DISABLED_ROLLBACK": ("ROLLBACK_BASELINE_RESTORED", False, False, 0, 0, 0, False, []),
    }
    for run in evidence["runs"]:
        state = run["state_evidence"]
        actual = (
            state["outcome"],
            state["eebus_runtime_enabled"],
            state["candidate_graph_enabled"],
            state["service_count"],
            state["candidate_count"],
            state["conflict_count"],
            state["degraded"],
            state["facts"],
        )
        config = run["provenance"]["config"]["payload"]
        if (
            actual != expected[run["state"]]
            or state["empty_success"] is not False
            or config["eebus_runtime_enabled"] != state["eebus_runtime_enabled"]
            or config["candidate_graph_enabled"] != state["candidate_graph_enabled"]
        ):
            fail("state.evidence")


def check_view_coverage(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    for run in evidence["runs"]:
        if [view["view_id"] for view in run["protected_views"]] != registry["protected_views"]:
            fail("view.coverage")


def _resolve_pointer(value: Any, pointer: str) -> tuple[Any, str | int]:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        fail("canonicalization.invalid")
    parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]
    current = value
    try:
        for part in parts[:-1]:
            current = current[int(part)] if isinstance(current, list) else current[part]
        leaf: str | int = int(parts[-1]) if isinstance(current, list) else parts[-1]
        target = current[leaf]
    except (KeyError, IndexError, TypeError, ValueError):
        fail("canonicalization.invalid")
    if not isinstance(target, str):
        fail("canonicalization.invalid")
    return current, leaf


def normalized_payload(payload: Any, rule: dict[str, Any], profile: dict[str, Any]) -> Any:
    result = copy.deepcopy(payload)
    pointers = rule["timestamp_pointers"] + rule["mask_pointers"]
    if len(pointers) != len(set(pointers)):
        fail("canonicalization.invalid")
    for pointer in rule["timestamp_pointers"]:
        parent, leaf = _resolve_pointer(result, pointer)
        if not RFC3339_UTC_RE.fullmatch(parent[leaf]):
            fail("canonicalization.invalid")
        parent[leaf] = profile["timestamp_replacement"]
    for pointer in rule["mask_pointers"]:
        parent, leaf = _resolve_pointer(result, pointer)
        parent[leaf] = profile["mask_replacement"]
    return result


def payload_shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: payload_shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return [payload_shape(item) for item in value]
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    return "string"


def check_normalization(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    profile = evidence["normalization"]
    if (
        profile["profile_id"] != "multi-runtime-coexistence-no-drift-v1"
        or profile["canonicalization"] != "RFC8785_JCS_INTEGER_SUBSET"
        or profile["timestamp_replacement"] != "<TIMESTAMP>"
        or profile["mask_replacement"] != "<MASKED>"
        or profile["view_rules"] != registry["view_rules"]
    ):
        fail("canonicalization.invalid")


def check_payload_hashes(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    rules = {rule["view_id"]: rule for rule in registry["view_rules"]}
    for run in evidence["runs"]:
        for view in run["protected_views"]:
            if view["capture_path"] != rules[view["view_id"]]["capture_path"] or view["media_type"] != "application/json":
                fail("hash.payload")
            normalized = normalized_payload(
                view["payload"], rules[view["view_id"]], evidence["normalization"]
            )
            if (
                view["raw_payload_hash"] != digest(RAW_PAYLOAD_DOMAIN, view["payload"])
                or view["shape_hash"] != digest(SHAPE_DOMAIN, payload_shape(view["payload"]))
                or view["canonical_payload_hash"]
                != digest(CANONICAL_PAYLOAD_DOMAIN, normalized)
            ):
                fail("hash.payload")


def _contains_candidate_leak(value: Any) -> bool:
    if isinstance(value, dict):
        if set(value) & {"candidate_status", "conflict_status", "candidate_fact", "candidate_facts"}:
            return True
        return any(_contains_candidate_leak(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_candidate_leak(item) for item in value)
    return isinstance(value, str) and value in {"CANDIDATE", "WITHHELD/CONFLICT"}


def check_anti_leak(evidence: dict[str, Any]) -> None:
    for run in evidence["runs"]:
        if run["state"] == "EEBUS_DISABLED_ROLLBACK":
            continue
        if any(_contains_candidate_leak(view["payload"]) for view in run["protected_views"]):
            fail("anti_leak.candidate")


def check_authority(evidence: dict[str, Any]) -> None:
    for run in evidence["runs"][:-1]:
        registry_view = next(
            view for view in run["protected_views"] if view["view_id"] == "semantic.registry"
        )
        routes_view = next(
            view for view in run["protected_views"] if view["view_id"] == "command.routing"
        )
        if registry_view["payload"]["data"]["authority"] != "ebus.promoted":
            fail("authority.ebus")
        if any(route["source"] != "ebus" for route in routes_view["payload"]["data"]["routes"]):
            fail("authority.ebus")


def check_scope(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    scope = evidence["scope"]
    if (
        scope["gate"] != registry["gate"]
        or scope["claims"] != ["EEBUS-G18"]
        or scope["excluded_gates"] != registry["excluded_gates"]
        or scope["live_vr940_claim"] is not False
        or scope["public_version_policy"] != "V1_ONLY_NO_PUBLIC_V2"
    ):
        fail("gate.scope")
    for run in evidence["runs"]:
        inventory = next(
            view for view in run["protected_views"] if view["view_id"] == "mcp.tool.inventory"
        )
        eebus_contract = next(
            view for view in run["protected_views"] if view["view_id"] == "mcp.eebus.v1.contract"
        )
        if (
            any(".v2" in tool for tool in inventory["payload"]["data"]["tools"])
            or eebus_contract["payload"]["data"]["version"] != 1
        ):
            fail("gate.scope")


def check_drift(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    baseline = evidence["runs"][0]
    baseline_views = {view["view_id"]: view for view in baseline["protected_views"]}
    rules = {rule["view_id"]: rule for rule in registry["view_rules"]}
    for run in evidence["runs"][1:-1]:
        for view in run["protected_views"]:
            original = baseline_views[view["view_id"]]
            original_bytes = canonical(
                normalized_payload(
                    original["payload"],
                    rules[view["view_id"]],
                    evidence["normalization"],
                )
            )
            compared_bytes = canonical(
                normalized_payload(
                    view["payload"],
                    rules[view["view_id"]],
                    evidence["normalization"],
                )
            )
            if (
                view["shape_hash"] != original["shape_hash"]
                or view["canonical_payload_hash"] != original["canonical_payload_hash"]
                or compared_bytes != original_bytes
            ):
                fail("drift.consumer")


def check_rollback(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    baseline = evidence["runs"][0]
    rollback = evidence["runs"][-1]
    baseline_hashes = [
        (view["view_id"], view["shape_hash"], view["canonical_payload_hash"])
        for view in baseline["protected_views"]
    ]
    rollback_hashes = [
        (view["view_id"], view["shape_hash"], view["canonical_payload_hash"])
        for view in rollback["protected_views"]
    ]
    rules = {rule["view_id"]: rule for rule in registry["view_rules"]}
    baseline_bytes = [
        canonical(
            normalized_payload(
                view["payload"], rules[view["view_id"]], evidence["normalization"]
            )
        )
        for view in baseline["protected_views"]
    ]
    rollback_bytes = [
        canonical(
            normalized_payload(
                view["payload"], rules[view["view_id"]], evidence["normalization"]
            )
        )
        for view in rollback["protected_views"]
    ]
    config = rollback["provenance"]["config"]["payload"]
    if (
        rollback["state"] != "EEBUS_DISABLED_ROLLBACK"
        or config["eebus_runtime_enabled"]
        or config["candidate_graph_enabled"]
        or rollback_hashes != baseline_hashes
        or rollback_bytes != baseline_bytes
    ):
        fail("rollback.drift")


def check_evidence_hash(evidence: dict[str, Any]) -> None:
    view = {key: value for key, value in evidence.items() if key not in {"evidence_id", "evidence_hash"}}
    expected = digest(EVIDENCE_DOMAIN, view)
    if evidence["evidence_hash"] != expected or evidence["evidence_id"] != "mrcv1:" + expected:
        fail("hash.evidence")


def verify(
    evidence: dict[str, Any],
    raw_size: int,
    registry: dict[str, Any],
    registry_raw: bytes,
    m7_paths: dict[str, pathlib.Path],
) -> dict[str, Any]:
    schema_check(evidence)
    check_limits(evidence, raw_size)
    check_registry(evidence, registry, registry_raw)
    graph, replay, _, _ = _verify_m7(evidence, registry, m7_paths)
    check_runtime(evidence, graph, replay)
    check_config(evidence)
    check_auth_mask(evidence)
    check_clock(evidence)
    check_ordering(evidence, registry)
    check_states(evidence)
    check_view_coverage(evidence, registry)
    check_normalization(evidence, registry)
    check_payload_hashes(evidence, registry)
    check_anti_leak(evidence)
    check_authority(evidence)
    check_scope(evidence, registry)
    check_drift(evidence, registry)
    check_rollback(evidence, registry)
    check_evidence_hash(evidence)
    return evidence


def _view_hashes(run: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "view_id": view["view_id"],
            "shape_hash": view["shape_hash"],
            "canonical_payload_hash": view["canonical_payload_hash"],
        }
        for view in run["protected_views"]
    ]


def report(evidence: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    checks = registry["required_acceptance_checks"]
    result_by_state = {
        "EEBUS_DISABLED_CONFIRMED": "NO_DRIFT",
        "EEBUS_ENABLED_NO_SERVICES": "EXPECTED_NO_SERVICES_NO_DRIFT",
        "EEBUS_CONNECTED_CANDIDATE_ONLY": "CANDIDATE_CONFINED_NO_DRIFT",
        "EEBUS_CONFLICTED_WITHHELD": "CONFLICT_WITHHELD_NO_DRIFT",
        "EEBUS_DISABLED_ROLLBACK": "ROLLBACK_EXACT_BASELINE",
    }
    baseline = evidence["runs"][0]
    value = {
        "contract": REPORT_CONTRACT,
        "schema_version": 1,
        "fixture_id": registry["fixture_ids"]["positive_report"],
        "report_id": "mrcrv1:sha256:" + "0" * 64,
        "report_hash": "sha256:" + "0" * 64,
        "evidence_id": evidence["evidence_id"],
        "evidence_hash": evidence["evidence_hash"],
        "gate": registry["gate"],
        "verdict": "PASS",
        "m7_binding": {
            key: evidence["m7_binding"][key]
            for key in (
                "completion_token",
                "docs_source_commit",
                "graph_id",
                "graph_hash",
                "replay_id",
                "replay_hash",
            )
        },
        "baseline": {
            "run_id": baseline["run_id"],
            "state": baseline["state"],
            "source_commit": baseline["provenance"]["runtime"]["source_commit"],
            "artifact_digest": baseline["provenance"]["runtime"]["artifact_digest"],
            "view_hashes": _view_hashes(baseline),
        },
        "scenarios": [
            {
                "run_id": run["run_id"],
                "state": run["state"],
                "result": result_by_state[run["state"]],
                "checks": checks,
                "view_hashes": _view_hashes(run),
            }
            for run in evidence["runs"][1:]
        ],
        "acceptance_matrix": [
            {"state": run["state"], "required_checks": checks, "passed": True}
            for run in evidence["runs"]
        ],
        "rollback": {
            "run_id": evidence["runs"][-1]["run_id"],
            "runtime_disabled": True,
            "candidate_graph_disabled": True,
            "exact_baseline_restored": True,
        },
    }
    view = {key: item for key, item in value.items() if key not in {"report_id", "report_hash"}}
    report_hash = digest(REPORT_DOMAIN, view)
    value["report_id"] = "mrcrv1:" + report_hash
    value["report_hash"] = report_hash
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "report"))
    parser.add_argument("--evidence", type=pathlib.Path, required=True)
    parser.add_argument("--registry", type=pathlib.Path, required=True)
    parser.add_argument("--m7-graph", type=pathlib.Path, required=True)
    parser.add_argument("--m7-replay", type=pathlib.Path, required=True)
    parser.add_argument("--m7-registry", type=pathlib.Path, required=True)
    parser.add_argument("--m7-source-bundle", type=pathlib.Path, required=True)
    parser.add_argument("--m7-source-replay", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        evidence, evidence_raw = load_json(args.evidence, "json.syntax", bounded=True)
        schema_check(evidence)
        check_limits(evidence, len(evidence_raw))
        registry, registry_raw = load_json(args.registry, "registry.binding")
        m7_paths = {
            "graph": args.m7_graph,
            "replay": args.m7_replay,
            "registry": args.m7_registry,
            "source_bundle": args.m7_source_bundle,
            "source_replay": args.m7_source_replay,
        }
        verify(evidence, len(evidence_raw), registry, registry_raw, m7_paths)
        if args.command == "verify":
            sys.stdout.write("ok\n")
        else:
            sys.stdout.write(canonical(report(evidence, registry)).decode("utf-8") + "\n")
        return 0
    except Failure as error:
        sys.stdout.write(str(error) + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
