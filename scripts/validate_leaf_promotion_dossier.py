#!/usr/bin/env python3
"""Fail-closed verifier for the MSP-085 per-leaf promotion lock."""

from __future__ import annotations

import argparse
import datetime as dt
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


DOSSIER_CONTRACT = "helianthus.platform.leaf-promotion-dossier.v1"
REGISTRY_CONTRACT = "helianthus.platform.leaf-promotion-registry.v1"
RESULT_CONTRACT = "helianthus.platform.leaf-promotion-lock-result.v1"
DOSSIER_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION-DOSSIER:V1"
LEAF_REPLAY_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION-REPLAY:V1"
RESULT_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION-LOCK-RESULT:V1"
EXPECTED_REGISTRY_SHA256 = (
    "89d2abad7c981d95a2cb6077ee383404ef13be04a3f1f34f79b8bf177a90792e"
)
SAFE_INTEGER = 9_007_199_254_740_991
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
TERMINAL_STATES = {"NO_SIGNAL", "CLOUD_ONLY", "CONFLICT", "NOT_TESTED"}
HARD_LIMITS = {
    "max_dossier_bytes": 1_048_576,
    "max_depth": 32,
    "max_leaves": 64,
    "max_string_bytes": 4_096,
    "max_total_members": 16_384,
    "max_total_list_items": 8_192,
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
    if len(raw) > HARD_LIMITS["max_dossier_bytes"]:
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


def load_json(path: pathlib.Path, *, bounded: bool = False) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError:
        fail("json.syntax")
    if bounded:
        _bounded_preflight(raw)
    if re.search(rb"(?<![0-9A-Za-z_])-0(?:[^0-9.]|$)", raw):
        fail("json.syntax")

    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                fail("json.syntax")
            result[key] = value
        return result

    def integer(value: str) -> int:
        parsed = int(value)
        if abs(parsed) > SAFE_INTEGER:
            fail("json.syntax")
        return parsed

    def reject_number(_: str) -> None:
        fail("json.syntax")

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
        fail("json.syntax")
    return value, raw


def _schema() -> dict[str, Any]:
    path = (
        SCRIPT_ROOT.parent
        / "docs/platform/schemas/leaf-promotion-dossier-v1.schema.json"
    )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail("schema.dossier")


def schema_check(dossier: Any) -> None:
    schema = _schema()
    if not candidate._schema_validate(dossier, schema, schema):
        fail("schema.dossier")
    if (
        dossier["contract"] != DOSSIER_CONTRACT
        or dossier["schema_version"] != 1
        or len(dossier["leaves"]) > HARD_LIMITS["max_leaves"]
    ):
        fail("schema.dossier")


def limits_check(value: Any, depth: int = 0) -> tuple[int, int]:
    if depth > HARD_LIMITS["max_depth"]:
        fail("limits.exceeded")
    if isinstance(value, dict):
        members = len(value)
        items = 0
        for key, child in value.items():
            if len(key.encode("utf-8")) > HARD_LIMITS["max_string_bytes"]:
                fail("limits.exceeded")
            child_members, child_items = limits_check(child, depth + 1)
            members += child_members
            items += child_items
    elif isinstance(value, list):
        members = 0
        items = len(value)
        for child in value:
            child_members, child_items = limits_check(child, depth + 1)
            members += child_members
            items += child_items
    elif isinstance(value, str):
        if len(value.encode("utf-8")) > HARD_LIMITS["max_string_bytes"]:
            fail("limits.exceeded")
        return 0, 0
    else:
        return 0, 0
    if (
        members > HARD_LIMITS["max_total_members"]
        or items > HARD_LIMITS["max_total_list_items"]
    ):
        fail("limits.exceeded")
    return members, items


def registry_check(
    dossier: dict[str, Any], registry: Any, registry_raw: bytes
) -> dict[str, Any]:
    if (
        not isinstance(registry, dict)
        or registry.get("contract") != REGISTRY_CONTRACT
        or registry.get("version") != 1
        or registry.get("gate") != "MSP-085"
        or registry.get("limits") != HARD_LIMITS
        or registry.get("terminal_states")
        != ["NO_SIGNAL", "CLOUD_ONLY", "CONFLICT", "NOT_TESTED"]
        or registry.get("b524_namespaces") != ["OP_0X02", "OP_0X06"]
        or registry.get("required_perturbation_cycles") != 3
        or registry.get("zero_promotion_consumer_gate")
        != "BLOCKED_ZERO_PROMOTED_LEAVES"
    ):
        fail("registry.binding")
    raw_hash = hashlib.sha256(registry_raw).hexdigest()
    if raw_hash != EXPECTED_REGISTRY_SHA256:
        fail("registry.binding")
    binding = dossier["registry"]
    if (
        binding["contract"] != REGISTRY_CONTRACT
        or binding["version"] != 1
        or binding["digest"] != "sha256:" + raw_hash
    ):
        fail("registry.binding")
    return registry


def load_source_artifacts(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected_contracts = registry.get("source_contracts")
    paths = registry.get("source_artifacts")
    if not isinstance(expected_contracts, dict) or not isinstance(paths, dict):
        fail("registry.binding")
    expected_keys = {"m7_graph", "m7_replay", "m8_evidence", "m8_report"}
    if set(expected_contracts) != expected_keys or set(paths) != expected_keys:
        fail("registry.binding")

    repository_root = SCRIPT_ROOT.parent.resolve()
    artifacts: dict[str, dict[str, Any]] = {}
    for key in sorted(expected_keys):
        relative = pathlib.PurePosixPath(paths[key])
        if relative.is_absolute() or ".." in relative.parts:
            fail("registry.binding")
        path = (repository_root / pathlib.Path(*relative.parts)).resolve()
        if path != repository_root and repository_root not in path.parents:
            fail("registry.binding")
        value, _ = load_json(path, bounded=True)
        if not isinstance(value, dict) or value.get("contract") != expected_contracts[key]:
            fail("registry.binding")
        artifacts[key] = value
    return artifacts


def source_binding_check(
    dossier: dict[str, Any], artifacts: dict[str, dict[str, Any]]
) -> None:
    graph = artifacts["m7_graph"]
    replay = artifacts["m7_replay"]
    evidence = artifacts["m8_evidence"]
    report = artifacts["m8_report"]
    expected = {
        "m7_graph_id": graph.get("graph_id"),
        "m7_graph_hash": graph.get("graph_hash"),
        "m7_replay_id": replay.get("replay_id"),
        "m7_replay_hash": replay.get("replay_hash"),
        "m8_evidence_id": evidence.get("evidence_id"),
        "m8_evidence_hash": evidence.get("evidence_hash"),
        "m8_report_id": report.get("report_id"),
        "m8_report_hash": report.get("report_hash"),
        "coexistence_verdict": report.get("verdict"),
    }
    if dossier["source_bindings"] != expected:
        fail("provenance.binding")
    if (
        replay.get("graph_id") != graph.get("graph_id")
        or replay.get("graph_hash") != graph.get("graph_hash")
        or report.get("evidence_id") != evidence.get("evidence_id")
        or report.get("evidence_hash") != evidence.get("evidence_hash")
    ):
        fail("provenance.binding")
    for item in (evidence, report):
        binding = item.get("m7_binding")
        if not isinstance(binding, dict):
            fail("provenance.binding")
        if (
            binding.get("graph_id") != graph.get("graph_id")
            or binding.get("graph_hash") != graph.get("graph_hash")
            or binding.get("replay_id") != replay.get("replay_id")
            or binding.get("replay_hash") != replay.get("replay_hash")
        ):
            fail("provenance.binding")


def identity_check(dossier: dict[str, Any]) -> None:
    leaf_ids: set[str] = set()
    paths: set[str] = set()
    semantic_paths = [leaf["semantic_path"] for leaf in dossier["leaves"]]
    if semantic_paths != sorted(semantic_paths):
        fail("identity.native")
    for leaf in dossier["leaves"]:
        if leaf["leaf_id"] in leaf_ids or leaf["semantic_path"] in paths:
            fail("identity.native")
        leaf_ids.add(leaf["leaf_id"])
        paths.add(leaf["semantic_path"])
        ebus = leaf["source_identity"]["ebus"]
        if ebus["family"] == "B524":
            expected = {2: "OP_0X02", 6: "OP_0X06"}[ebus["opcode"]]
            if ebus["namespace"] != expected:
                fail("identity.native")
        eebus = leaf["source_identity"]["eebus"]
        path = eebus["path"]
        if [item["kind"] for item in path[:3]] != [
            "ENTITY",
            "SERVICE",
            "FEATURE",
        ]:
            fail("identity.native")
        if [item["selector"] for item in path[:3]] != [
            eebus["entity"],
            eebus["service"],
            eebus["feature"],
        ]:
            fail("identity.native")
        if any(item["kind"] != "FIELD" for item in path[3:]):
            fail("identity.native")


def comparator_check(dossier: dict[str, Any]) -> None:
    for leaf in dossier["leaves"]:
        comparator = leaf["comparator"]
        window = comparator["window"]
        if (
            window["start_offset_ns"] >= window["end_offset_ns"]
            or window["sample_period_ns"]
            > window["end_offset_ns"] - window["start_offset_ns"]
            or comparator["missing_samples"] > comparator["maximum_missing"]
        ):
            fail("comparator.invalid")
        tolerance = comparator["tolerance"]
        if tolerance["mode"] == "EXACT" and (
            tolerance["absolute_decimal"] is not None
            or tolerance["relative_ppm"] is not None
        ):
            fail("comparator.invalid")
        if tolerance["mode"] == "ABSOLUTE" and (
            tolerance["absolute_decimal"] is None
            or tolerance["relative_ppm"] is not None
        ):
            fail("comparator.invalid")
        if tolerance["mode"] == "ABSOLUTE_OR_RELATIVE" and (
            tolerance["absolute_decimal"] is None
            or tolerance["relative_ppm"] is None
        ):
            fail("comparator.invalid")
        conversion = comparator["conversion"]
        if conversion["mode"] == "IDENTITY" and (
            conversion["source_unit"] != conversion["target_unit"]
            or conversion["scale_decimal"] != "1"
            or conversion["offset_decimal"] != "0"
        ):
            fail("comparator.invalid")
        rounding = comparator["rounding"]
        if (rounding["mode"] == "NONE") != (rounding["decimal_places"] is None):
            fail("comparator.invalid")
        if comparator["outcome"] == "MATCH" and (
            comparator["observed_samples"] < comparator["minimum_samples"]
            or comparator["missing_samples"] > comparator["maximum_missing"]
        ):
            fail("comparator.invalid")


def inheritance_check(dossier: dict[str, Any], registry: dict[str, Any]) -> None:
    expected = registry["inheritance_policy"]
    for leaf in dossier["leaves"]:
        if leaf["inheritance"] != expected:
            fail("inheritance.forbidden")


def coexistence_check(
    dossier: dict[str, Any], artifacts: dict[str, dict[str, Any]]
) -> None:
    source = dossier["source_bindings"]
    report = artifacts["m8_report"]
    expected_runs = [report["baseline"]["run_id"]]
    expected_runs.extend(item["run_id"] for item in report["scenarios"])
    expected_runs = list(dict.fromkeys(expected_runs))
    expected_views = [
        item["canonical_payload_hash"] for item in report["baseline"]["view_hashes"]
    ]
    for leaf in dossier["leaves"]:
        proof = leaf["coexistence_proof"]
        if (
            proof["report_id"] != source["m8_report_id"]
            or proof["report_hash"] != source["m8_report_hash"]
            or not proof["no_drift"]
            or not proof["rollback_exact"]
            or len(set(proof["scenario_run_ids"]))
            != len(proof["scenario_run_ids"])
            or len(set(proof["protected_view_hashes"]))
            != len(proof["protected_view_hashes"])
            or proof["scenario_run_ids"] != expected_runs
            or proof["protected_view_hashes"] != expected_views
        ):
            fail("coexistence.invalid")


def provenance_check(
    dossier: dict[str, Any], artifacts: dict[str, dict[str, Any]]
) -> None:
    source_binding_check(dossier, artifacts)
    source = dossier["source_bindings"]
    expected_hashes = [source["m7_graph_hash"], source["m8_evidence_hash"]]
    for leaf in dossier["leaves"]:
        provenance = leaf["provenance"]
        if (
            provenance["redacted_input_hashes"] != expected_hashes
            or len(set(provenance["source_artifact_ids"]))
            != len(provenance["source_artifact_ids"])
        ):
            fail("provenance.binding")


def parse_utc(value: str) -> dt.datetime:
    if not value.endswith("Z"):
        raise ValueError("timestamp is not canonical UTC")
    parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo != dt.timezone.utc:
        raise ValueError("timestamp is not UTC")
    return parsed


def mutable_safety_check(
    dossier: dict[str, Any], registry: dict[str, Any]
) -> None:
    required_abort = set(registry["required_abort_conditions"])
    for leaf in dossier["leaves"]:
        proof = leaf["mutable_proof"]
        if leaf["mutability"] == "READ_ONLY":
            if proof is not None:
                fail("mutable.safety")
            continue
        if proof is None:
            fail("mutable.safety")
        cycle_ids = [cycle["cycle_id"] for cycle in proof["cycles"]]
        lease = proof["lease"]
        try:
            valid_from = parse_utc(lease["valid_from"])
            valid_until = parse_utc(lease["valid_until"])
        except ValueError:
            fail("mutable.safety")
        if (
            not proof["one_writer"]
            or lease["holder"] != proof["writer_id"]
            or valid_from >= valid_until
            or proof["direct_adapter_write"]
            or proof["write_path"] != "GATEWAY_ROUTER_ONLY"
            or set(proof["abort_conditions"]) != required_abort
            or len(proof["cycles"]) != registry["required_perturbation_cycles"]
            or len(set(cycle_ids)) != len(cycle_ids)
            or not all(cycle["independent"] for cycle in proof["cycles"])
        ):
            fail("mutable.safety")


def mutable_rollback_check(dossier: dict[str, Any]) -> None:
    for leaf in dossier["leaves"]:
        proof = leaf["mutable_proof"]
        if proof is not None and not all(
            cycle["rollback"] == "EXACT" for cycle in proof["cycles"]
        ):
            fail("mutable.rollback")


def state_check(dossier: dict[str, Any]) -> None:
    for leaf in dossier["leaves"]:
        decision = leaf["decision"]
        terminal = leaf["terminal_state"]
        visibility = leaf["visibility"]
        if terminal in TERMINAL_STATES and (
            decision != "WITHHELD" or visibility != "RAW_DEBUG_ONLY"
        ):
            fail("state.terminal")
        if decision == "WITHHELD" and (
            terminal not in TERMINAL_STATES or visibility != "RAW_DEBUG_ONLY"
        ):
            fail("state.terminal")
        if decision == "PROMOTED" and (
            terminal is not None or visibility != "LOCKED_NOT_EXPOSED"
        ):
            fail("state.terminal")


def evidence_check(
    dossier: dict[str, Any], artifacts: dict[str, dict[str, Any]]
) -> None:
    promoted = [leaf for leaf in dossier["leaves"] if leaf["decision"] == "PROMOTED"]
    source_evidence_class = artifacts["m8_evidence"].get("evidence_class")
    if dossier["evidence_class"] != source_evidence_class:
        fail("evidence.ineligible")
    if source_evidence_class == "SYNTHETIC_OFFLINE_FIXTURE" and (
        dossier["capture_context"] != "OFF_LAN"
    ):
        fail("evidence.ineligible")
    if promoted and (
        dossier["evidence_class"] != "CAPTURED_RUNTIME_EVIDENCE"
        or dossier["capture_context"] != "SAME_LAN_LAB"
        or not dossier["positive_promotion_claim"]
        or source_evidence_class != "CAPTURED_RUNTIME_EVIDENCE"
    ):
        fail("evidence.ineligible")
    if promoted and any(
        leaf["comparator"]["outcome"] != "MATCH" for leaf in promoted
    ):
        fail("evidence.ineligible")
    if not promoted and dossier["positive_promotion_claim"]:
        fail("evidence.ineligible")


def leaf_replay_hash(leaf: dict[str, Any]) -> str:
    payload = {
        "leaf_id": leaf["leaf_id"],
        "semantic_path": leaf["semantic_path"],
        "source_identity": leaf["source_identity"],
        "comparator": leaf["comparator"],
        "decision": leaf["decision"],
        "terminal_state": leaf["terminal_state"],
    }
    return digest(LEAF_REPLAY_DOMAIN, payload)


def replay_check(dossier: dict[str, Any]) -> None:
    source = dossier["source_bindings"]
    expected_inputs = [source["m7_replay_hash"], source["m8_report_hash"]]
    for leaf in dossier["leaves"]:
        regenerated = leaf_replay_hash(leaf)
        replay = leaf["replay"]
        if (
            replay["input_hashes"] != expected_inputs
            or not replay["deterministic"]
            or replay["expected_output_hash"] != regenerated
            or replay["actual_output_hash"] != regenerated
            or leaf["provenance"]["normalized_output_hash"] != regenerated
        ):
            fail("hash.replay")


def consumer_check(dossier: dict[str, Any]) -> None:
    promoted = sum(
        leaf["decision"] == "PROMOTED" for leaf in dossier["leaves"]
    )
    expected = "READY_FOR_M9" if promoted else "BLOCKED_ZERO_PROMOTED_LEAVES"
    if dossier["m9_consumer_gate"] != expected:
        fail("consumer.block")


def dossier_hash_check(dossier: dict[str, Any]) -> None:
    payload = {key: value for key, value in dossier.items() if key != "dossier_hash"}
    if dossier["dossier_hash"] != digest(DOSSIER_DOMAIN, payload):
        fail("hash.dossier")


def verify(dossier_path: pathlib.Path, registry_path: pathlib.Path) -> dict[str, Any]:
    dossier, _ = load_json(dossier_path, bounded=True)
    schema_check(dossier)
    limits_check(dossier)
    registry, registry_raw = load_json(registry_path)
    registry = registry_check(dossier, registry, registry_raw)
    artifacts = load_source_artifacts(registry)
    identity_check(dossier)
    comparator_check(dossier)
    inheritance_check(dossier, registry)
    coexistence_check(dossier, artifacts)
    provenance_check(dossier, artifacts)
    mutable_safety_check(dossier, registry)
    mutable_rollback_check(dossier)
    state_check(dossier)
    evidence_check(dossier, artifacts)
    replay_check(dossier)
    consumer_check(dossier)
    dossier_hash_check(dossier)
    return dossier


def build_result(dossier: dict[str, Any]) -> dict[str, Any]:
    promoted = sum(
        leaf["decision"] == "PROMOTED" for leaf in dossier["leaves"]
    )
    result: dict[str, Any] = {
        "contract": RESULT_CONTRACT,
        "schema_version": 1,
        "dossier_id": dossier["dossier_id"],
        "dossier_hash": dossier["dossier_hash"],
        "replay_tool": "leaf-promotion-replay",
        "replay_version": 1,
        "counts": {
            "total": len(dossier["leaves"]),
            "promoted": promoted,
            "withheld": len(dossier["leaves"]) - promoted,
        },
        "leaves": [
            {
                "leaf_id": leaf["leaf_id"],
                "semantic_path": leaf["semantic_path"],
                "decision": leaf["decision"],
                "terminal_state": leaf["terminal_state"],
                "visibility": leaf["visibility"],
            }
            for leaf in dossier["leaves"]
        ],
        "m9_consumer_gate": dossier["m9_consumer_gate"],
        "verdict": (
            "VALID_PROMOTION_LOCK" if promoted else "VALID_ZERO_PROMOTION"
        ),
    }
    result["result_hash"] = digest(RESULT_DOMAIN, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "replay"))
    parser.add_argument("--dossier", required=True, type=pathlib.Path)
    parser.add_argument("--registry", required=True, type=pathlib.Path)
    args = parser.parse_args(argv)
    try:
        dossier = verify(args.dossier, args.registry)
        if args.command == "verify":
            print("PASS")
        else:
            print(canonical(build_result(dossier)).decode("utf-8"))
    except Failure as error:
        print(str(error))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
