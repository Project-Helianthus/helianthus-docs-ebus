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
import tempfile
from typing import Any


SCRIPT_ROOT = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))
import validate_candidate_fact_graph as candidate
import project_candidate_fact_public_status as status_projector
import validate_multi_runtime_coexistence as coexistence


DOSSIER_CONTRACT = "helianthus.platform.leaf-promotion-dossier.v1"
REGISTRY_CONTRACT = "helianthus.platform.leaf-promotion-registry.v1"
RESULT_CONTRACT = "helianthus.platform.leaf-promotion-lock-result.v1"
CAPTURED_ASSESSMENT_CONTRACT = (
    "helianthus.platform.leaf-promotion-captured-assessment.v1"
)
DOSSIER_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION-DOSSIER:V1"
LEAF_REPLAY_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION-REPLAY:V1"
RESULT_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION-LOCK-RESULT:V1"
CAPTURED_ASSESSMENT_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION-CAPTURED-ASSESSMENT:V1"
EXPECTED_REGISTRY_SHA256 = (
    "a694a897160f3f56cc0221fae7b7999e8dcf0009eeec0d7bbe764d12871c4273"
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


def _contract_schema(name: str, category: str) -> dict[str, Any]:
    path = SCRIPT_ROOT.parent / "docs/platform/schemas" / name
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail(category)


def _schema_validate(value: Any, name: str, category: str) -> None:
    schema = _contract_schema(name, category)
    if not candidate._schema_validate(value, schema, schema):
        fail(category)


def schema_check(dossier: Any) -> None:
    schema = _schema()
    if not candidate._schema_validate(dossier, schema, schema):
        fail("schema.dossier")
    if (
        dossier["contract"] != DOSSIER_CONTRACT
        or dossier["schema_version"] != 1
        or dossier["profile"] != "SYNTHETIC_CONFORMANCE"
        or dossier["export_tier"] != "PUBLIC_REDACTED"
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
        or registry.get("profiles")
        != {
            "SYNTHETIC_CONFORMANCE": {
                "live_promotion_claim": False,
                "persist_private_assessment": False,
            },
            "CAPTURED_RUNTIME_ZERO_PROMOTION": {
                "live_promotion_claim": False,
                "persist_private_assessment": False,
            },
        }
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


def captured_registry_check(registry: Any, registry_raw: bytes) -> dict[str, Any]:
    if not isinstance(registry, dict):
        fail("registry.binding")
    profiles = registry.get("profiles")
    predecessors = registry.get("captured_runtime_predecessors")
    if (
        registry.get("contract") != REGISTRY_CONTRACT
        or registry.get("version") != 1
        or registry.get("gate") != "MSP-085"
        or registry.get("limits") != HARD_LIMITS
        or not isinstance(profiles, dict)
        or set(profiles)
        != {"SYNTHETIC_CONFORMANCE", "CAPTURED_RUNTIME_ZERO_PROMOTION"}
        or not isinstance(predecessors, dict)
        or set(predecessors)
        != {
            "m7_gateway_source_commit",
            "m7_docs_source_commit",
            "m8_gateway_source_commit",
            "m8_docs_source_commit",
        }
        or registry.get("zero_promotion_consumer_gate")
        != "BLOCKED_ZERO_PROMOTED_LEAVES"
    ):
        fail("registry.binding")
    if hashlib.sha256(registry_raw).hexdigest() != EXPECTED_REGISTRY_SHA256:
        fail("registry.binding")
    return registry


def _captured_predecessor_check(
    registry: dict[str, Any],
    graph: dict[str, Any],
    replay: dict[str, Any],
    status: dict[str, Any],
    evidence: dict[str, Any],
    report: dict[str, Any],
) -> None:
    expected = registry["captured_runtime_predecessors"]
    m7_binding = registry["captured_runtime_status_binding"]
    if (
        status.get("source_commit") != expected["m7_gateway_source_commit"]
        or status.get("docs_source_commit") != expected["m7_docs_source_commit"]
        or graph.get("graph_id") != m7_binding["source_graph_id"]
        or graph.get("graph_hash") != m7_binding["source_graph_hash"]
        or replay.get("replay_id") != m7_binding["source_replay_id"]
        or replay.get("replay_hash") != m7_binding["source_replay_hash"]
        or status.get("projection_id") != m7_binding["projection_id"]
        or status.get("projection_hash") != m7_binding["projection_hash"]
        or status.get("fact_count") != m7_binding["fact_count"]
        or status.get("status_counts") != m7_binding["status_counts"]
        or evidence.get("evidence_class") != "CAPTURED_RUNTIME_EVIDENCE"
        or report.get("evidence_class") != "CAPTURED_RUNTIME_EVIDENCE"
        or report.get("verdict") != "PASS"
    ):
        fail("captured.predecessor")
    for run in evidence["runs"]:
        runtime = run["provenance"]["runtime"]
        if runtime["source_commit"] != expected["m8_gateway_source_commit"]:
            fail("captured.predecessor")


def _write_verified_m7_snapshot(
    directory: pathlib.Path, verified_raw: dict[str, bytes]
) -> tuple[pathlib.Path, pathlib.Path]:
    graph_path = directory / "graph.json"
    replay_path = directory / "replay.json"
    graph_path.write_bytes(verified_raw["graph"])
    replay_path.write_bytes(verified_raw["replay"])
    return graph_path, replay_path


def _exact_ebus_identity(fact: dict[str, Any]) -> tuple[bool, bool]:
    provenance = fact["provenance"]
    identity = provenance.get("ebus")
    source_terminal = provenance.get("source_terminal")
    if identity is None and isinstance(source_terminal, dict):
        identity = source_terminal.get("ebus_identity")
    if identity is None:
        return False, False
    return True, identity.get("family") in {"B509", "B524", "B555"}


def _private_assessment(
    graph: dict[str, Any],
    status: dict[str, Any],
    evidence: dict[str, Any],
    report: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, Any]:
    status_by_id = {item["candidate_id"]: item for item in status["facts"]}
    if len(status_by_id) != len(status["facts"]):
        fail("captured.status")
    reasons_order = registry["captured_zero_promotion_reason_precedence"]
    assessments: list[dict[str, Any]] = []
    for fact in sorted(
        graph["facts"], key=lambda item: (item["proposed_path"], item["candidate_id"])
    ):
        public = status_by_id.get(fact["candidate_id"])
        if public != {
            "candidate_id": fact["candidate_id"],
            "status": fact["status"],
            "terminal_negative_state": fact["terminal_negative_state"],
            "fact_hash": fact["fact_hash"],
        }:
            fail("captured.status")
        if fact["status"] not in {"RAW_ONLY", "WITHHELD"}:
            fail("promotion.forbidden")
        has_ebus, eligible_ebus = _exact_ebus_identity(fact)
        exact_eebus = fact["provenance"].get("eebus") is not None
        comparator_match = fact["comparator"]["outcome"] == "MATCH"
        captured_eligible = (
            eligible_ebus
            and exact_eebus
            and comparator_match
            and fact["status"] == "CANDIDATE"
        )
        flags = {
            "exact_ebus_identity": eligible_ebus,
            "exact_eebus_path": exact_eebus,
            "comparator_match": comparator_match,
            "captured_evidence_eligible": captured_eligible,
            "coexistence_no_drift": report["verdict"] == "PASS",
        }
        reason_set = {
            "SOURCE_STATUS_WITHHELD"
            if fact["status"] == "WITHHELD"
            else "SOURCE_STATUS_RAW_ONLY"
        }
        if not has_ebus:
            reason_set.add("EXACT_EBUS_IDENTITY_MISSING")
        elif not eligible_ebus:
            reason_set.add("EXACT_EBUS_IDENTITY_INELIGIBLE")
        if not exact_eebus:
            reason_set.add("EXACT_EEBUS_PATH_MISSING")
        if not comparator_match:
            reason_set.add("COMPARATOR_NOT_MATCHED")
        if not captured_eligible:
            reason_set.add("CAPTURED_EVIDENCE_INELIGIBLE")
        if report["verdict"] != "PASS":
            reason_set.add("COEXISTENCE_PROOF_MISSING")
        retest = fact["retest_trigger"]
        assessments.append(
            {
                "candidate_id": fact["candidate_id"],
                "semantic_path": fact["proposed_path"],
                "fact_hash": fact["fact_hash"],
                "source_status": fact["status"],
                "terminal_state": fact["terminal_negative_state"],
                "eligibility": flags,
                "decision": "WITHHELD",
                "withholding_reasons": [
                    reason for reason in reasons_order if reason in reason_set
                ],
                "retest_trigger": {
                    "trigger": retest["trigger_code"],
                    "required_source_kinds": retest["required_source_kinds"],
                    "minimum_new_samples": retest["minimum_new_samples"],
                },
            }
        )
    if set(status_by_id) != {item["candidate_id"] for item in assessments}:
        fail("captured.status")
    source = registry["captured_runtime_predecessors"]
    value: dict[str, Any] = {
        "contract": CAPTURED_ASSESSMENT_CONTRACT,
        "schema_version": 1,
        "profile": "CAPTURED_RUNTIME_ZERO_PROMOTION",
        "export_tier": "PRIVATE_OPERATOR",
        "source_bindings": {
            **source,
            "m7_graph_id": graph["graph_id"],
            "m7_graph_hash": graph["graph_hash"],
            "m7_replay_id": status["source_replay_id"],
            "m7_replay_hash": status["source_replay_hash"],
            "m7_status_projection_id": status["projection_id"],
            "m7_status_projection_hash": status["projection_hash"],
            "m8_evidence_id": evidence["evidence_id"],
            "m8_evidence_hash": evidence["evidence_hash"],
            "m8_report_id": report["report_id"],
            "m8_report_hash": report["report_hash"],
            "coexistence_verdict": report["verdict"],
        },
        "assessments": assessments,
        "dossiers": [],
        "m9_consumer_gate": "BLOCKED_ZERO_PROMOTED_LEAVES",
        "assessment_hash": "sha256:" + "0" * 64,
    }
    view = {key: item for key, item in value.items() if key != "assessment_hash"}
    value["assessment_hash"] = digest(CAPTURED_ASSESSMENT_DOMAIN, view)
    _schema_validate(
        value,
        "leaf-promotion-captured-assessment-v1.schema.json",
        "captured.schema",
    )
    return value


def build_captured_result(assessment: dict[str, Any]) -> dict[str, Any]:
    public_assessments = [
        {
            key: item[key]
            for key in (
                "candidate_id",
                "fact_hash",
                "source_status",
                "terminal_state",
                "decision",
                "withholding_reasons",
                "retest_trigger",
            )
        }
        for item in assessment["assessments"]
    ]
    total = len(public_assessments)
    result: dict[str, Any] = {
        "contract": RESULT_CONTRACT,
        "schema_version": 1,
        "profile": "CAPTURED_RUNTIME_ZERO_PROMOTION",
        "export_tier": "PUBLIC_REDACTED",
        "source_bindings": dict(assessment["source_bindings"]),
        "replay_tool": "leaf-promotion-replay",
        "replay_version": 1,
        "counts": {"total": total, "promoted": 0, "withheld": total},
        "dossier_count": 0,
        "assessments": public_assessments,
        "m9_consumer_gate": "BLOCKED_ZERO_PROMOTED_LEAVES",
        "verdict": "VALID_ZERO_PROMOTION",
        "result_hash": "sha256:" + "0" * 64,
    }
    view = {key: item for key, item in result.items() if key != "result_hash"}
    result["result_hash"] = digest(RESULT_DOMAIN, view)
    captured_result_check(result, assessment)
    return result


def captured_result_check(
    result: dict[str, Any], assessment: dict[str, Any]
) -> None:
    expected_keys = {
        "contract",
        "schema_version",
        "profile",
        "export_tier",
        "source_bindings",
        "replay_tool",
        "replay_version",
        "counts",
        "dossier_count",
        "assessments",
        "m9_consumer_gate",
        "verdict",
        "result_hash",
    }
    if (
        not isinstance(result, dict)
        or set(result) != expected_keys
        or result.get("contract") != RESULT_CONTRACT
        or result.get("schema_version") != 1
        or result.get("profile") != "CAPTURED_RUNTIME_ZERO_PROMOTION"
        or result.get("export_tier") != "PUBLIC_REDACTED"
        or result.get("replay_tool") != "leaf-promotion-replay"
        or result.get("replay_version") != 1
    ):
        fail("captured.result")
    _schema_validate(
        result, "leaf-promotion-lock-result-v1.schema.json", "captured.result"
    )
    private_items = assessment["assessments"]
    expected_order = sorted(
        private_items, key=lambda item: (item["semantic_path"], item["candidate_id"])
    )
    if private_items != expected_order or len(
        {item["candidate_id"] for item in private_items}
    ) != len(private_items):
        fail("assessment.ordering")
    expected_public = [
        {
            key: item[key]
            for key in (
                "candidate_id",
                "fact_hash",
                "source_status",
                "terminal_state",
                "decision",
                "withholding_reasons",
                "retest_trigger",
            )
        }
        for item in private_items
    ]
    if (
        result["assessments"] != expected_public
        or result["source_bindings"] != assessment["source_bindings"]
    ):
        fail("assessment.derivation")
    total = len(expected_public)
    if (
        result["counts"] != {"total": total, "promoted": 0, "withheld": total}
        or result["dossier_count"] != 0
        or any(item["decision"] != "WITHHELD" for item in expected_public)
        or assessment["dossiers"] != []
    ):
        fail("promotion.forbidden")
    if (
        result["m9_consumer_gate"] != "BLOCKED_ZERO_PROMOTED_LEAVES"
        or result["verdict"] != "VALID_ZERO_PROMOTION"
    ):
        fail("consumer.block")
    serialized = canonical(result).lower()
    for forbidden in (
        b"semantic_path",
        b"proposed_path",
        b"source_address",
        b"target_address",
        b"ship_id",
        b"candidate_ref",
        b"private_key",
        b"trust_store",
    ):
        if forbidden in serialized:
            fail("redaction.public")
    view = {key: item for key, item in result.items() if key != "result_hash"}
    if result["result_hash"] != digest(RESULT_DOMAIN, view):
        fail("hash.result")


def derive_captured(
    *,
    graph_path: pathlib.Path,
    replay_path: pathlib.Path,
    m7_registry_path: pathlib.Path,
    source_bundle_path: pathlib.Path,
    source_replay_path: pathlib.Path,
    status_path: pathlib.Path,
    terminal_graph_path: pathlib.Path,
    terminal_replay_path: pathlib.Path,
    terminal_source_bundle_path: pathlib.Path,
    terminal_source_replay_path: pathlib.Path,
    evidence_path: pathlib.Path,
    report_path: pathlib.Path,
    m8_registry_path: pathlib.Path,
    promotion_registry: dict[str, Any],
) -> dict[str, Any]:
    predecessor = promotion_registry["captured_runtime_predecessors"]
    try:
        projected, verified_raw = status_projector.load_verified_projection(
            graph_path=graph_path,
            replay_path=replay_path,
            registry_path=m7_registry_path,
            source_bundle_path=source_bundle_path,
            source_replay_path=source_replay_path,
            source_commit=predecessor["m7_gateway_source_commit"],
            docs_source_commit=predecessor["m7_docs_source_commit"],
        )
        status, status_raw = coexistence.load_json(
            status_path, "captured.status", bounded=True
        )
        if status_projector.render(projected) != status_raw:
            fail("captured.status")
        graph = json.loads(verified_raw["graph"])
        replay = json.loads(verified_raw["replay"])
        evidence, evidence_raw = coexistence.load_json(
            evidence_path, "json.syntax", bounded=True
        )
        m8_registry, m8_registry_raw = coexistence.load_json(
            m8_registry_path, "registry.binding"
        )
        with tempfile.TemporaryDirectory(prefix="leaf-promotion-m7-") as directory:
            snapshot_root = pathlib.Path(directory)
            snapshot_graph, snapshot_replay = _write_verified_m7_snapshot(
                snapshot_root, verified_raw
            )
            m7_paths = {
                "graph": snapshot_graph,
                "replay": snapshot_replay,
                "registry": m7_registry_path,
                "source_bundle": source_bundle_path,
                "source_replay": source_replay_path,
                "terminal_graph": terminal_graph_path,
                "terminal_replay": terminal_replay_path,
                "terminal_source_bundle": terminal_source_bundle_path,
                "terminal_source_replay": terminal_source_replay_path,
                "status": status_path,
            }
            coexistence.verify(
                evidence,
                len(evidence_raw),
                m8_registry,
                m8_registry_raw,
                m7_paths,
                require_private=True,
            )
        report, report_raw = coexistence.load_json(
            report_path, "captured.coexistence", bounded=True
        )
        generated_report = coexistence.report(evidence, m8_registry)
        if report != generated_report or report_raw != coexistence.canonical(report) + b"\n":
            fail("captured.coexistence")
    except Failure:
        raise
    except (candidate.Failure, coexistence.Failure, status_projector.Failure) as error:
        fail(str(error))
    except (AttributeError, KeyError, OSError, TypeError, ValueError):
        fail("captured.input")
    _captured_predecessor_check(
        promotion_registry, graph, replay, status, evidence, report
    )
    assessment = _private_assessment(
        graph, status, evidence, report, promotion_registry
    )
    return build_captured_result(assessment)


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
        perturbation_hashes = [
            cycle["perturbation_input_hash"] for cycle in proof["cycles"]
        ]
        lease = proof["lease"]
        try:
            valid_from = parse_utc(lease["valid_from"])
            valid_until = parse_utc(lease["valid_until"])
            performed_at = [
                parse_utc(cycle["performed_at"]) for cycle in proof["cycles"]
            ]
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
            or len(set(perturbation_hashes)) != len(perturbation_hashes)
            or not all(cycle["independent"] for cycle in proof["cycles"])
            or performed_at != sorted(performed_at)
            or len(set(performed_at)) != len(performed_at)
            or not all(valid_from <= instant <= valid_until for instant in performed_at)
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
        "profile": "SYNTHETIC_CONFORMANCE",
        "export_tier": "PUBLIC_REDACTED",
        "dossier_id": dossier["dossier_id"],
        "dossier_hash": dossier["dossier_hash"],
        "replay_tool": "leaf-promotion-replay",
        "replay_version": 1,
        "counts": {
            "total": len(dossier["leaves"]),
            "promoted": promoted,
            "withheld": len(dossier["leaves"]) - promoted,
        },
        "dossier_count": 1,
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
    parser.add_argument("command", choices=("verify", "replay", "derive-captured"))
    parser.add_argument("--dossier", type=pathlib.Path)
    parser.add_argument("--registry", required=True, type=pathlib.Path)
    parser.add_argument("--m7-graph", type=pathlib.Path)
    parser.add_argument("--m7-replay", type=pathlib.Path)
    parser.add_argument("--m7-registry", type=pathlib.Path)
    parser.add_argument("--m7-source-bundle", type=pathlib.Path)
    parser.add_argument("--m7-source-replay", type=pathlib.Path)
    parser.add_argument("--m7-live-status", type=pathlib.Path)
    parser.add_argument("--m7-terminal-graph", type=pathlib.Path)
    parser.add_argument("--m7-terminal-replay", type=pathlib.Path)
    parser.add_argument("--m7-terminal-source-bundle", type=pathlib.Path)
    parser.add_argument("--m7-terminal-source-replay", type=pathlib.Path)
    parser.add_argument("--m8-evidence", type=pathlib.Path)
    parser.add_argument("--m8-report", type=pathlib.Path)
    parser.add_argument("--m8-registry", type=pathlib.Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "derive-captured":
            names = (
                "m7_graph",
                "m7_replay",
                "m7_registry",
                "m7_source_bundle",
                "m7_source_replay",
                "m7_live_status",
                "m7_terminal_graph",
                "m7_terminal_replay",
                "m7_terminal_source_bundle",
                "m7_terminal_source_replay",
                "m8_evidence",
                "m8_report",
                "m8_registry",
            )
            if any(getattr(args, name) is None for name in names):
                fail("captured.arguments")
            registry, registry_raw = load_json(args.registry)
            registry = captured_registry_check(registry, registry_raw)
            result = derive_captured(
                graph_path=args.m7_graph,
                replay_path=args.m7_replay,
                m7_registry_path=args.m7_registry,
                source_bundle_path=args.m7_source_bundle,
                source_replay_path=args.m7_source_replay,
                status_path=args.m7_live_status,
                terminal_graph_path=args.m7_terminal_graph,
                terminal_replay_path=args.m7_terminal_replay,
                terminal_source_bundle_path=args.m7_terminal_source_bundle,
                terminal_source_replay_path=args.m7_terminal_source_replay,
                evidence_path=args.m8_evidence,
                report_path=args.m8_report,
                m8_registry_path=args.m8_registry,
                promotion_registry=registry,
            )
            print(canonical(result).decode("utf-8"))
        else:
            if args.dossier is None:
                fail("captured.arguments")
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
