#!/usr/bin/env python3
"""Generate the canonical synthetic MSP-085 zero-promotion fixture."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib

import validate_leaf_promotion_dossier as promotion


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    REPO_ROOT / "docs/platform/fixtures/leaf-promotion-dossier/v1/positive"
)
REGISTRY_PATH = (
    REPO_ROOT / "docs/platform/schemas/leaf-promotion-registry-v1.json"
)
M7_GRAPH_PATH = (
    REPO_ROOT / "docs/platform/fixtures/candidate-fact-graph/v1/positive/graph.json"
)
M7_REPLAY_PATH = (
    REPO_ROOT
    / "docs/platform/fixtures/candidate-fact-graph/v1/positive/replay-result.json"
)
M8_EVIDENCE_PATH = (
    REPO_ROOT
    / "docs/platform/fixtures/coexistence-no-drift/v1/positive/evidence.json"
)
M8_REPORT_PATH = (
    REPO_ROOT / "docs/platform/fixtures/coexistence-no-drift/v1/positive/report.json"
)


def load(path: pathlib.Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_identity(index: int) -> dict[str, object]:
    ebus_values: list[dict[str, object]] = [
        {
            "family": "B509",
            "target_pseudonym": "target-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "target_address": 8,
            "target_product": "fixture-product-a",
            "register_family": "fixture-family-a",
            "register_id": 512,
            "unit_scale_source": "fixture-catalog-v1",
            "evidence_role": "AUTHORITATIVE",
        },
        {
            "family": "B524",
            "target_pseudonym": "target-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "opcode": 2,
            "namespace": "OP_0X02",
            "group": 3,
            "instance": 0,
            "register": 28,
            "target_address": 21,
            "source_address": 247,
            "group_meaning": "fixture-group-local",
            "instance_gate": "fixture-gate-local",
            "register_category": "STATE",
            "unit_scale_source": "fixture-catalog-v1",
        },
        {
            "family": "B524",
            "target_pseudonym": "target-cccccccccccccccccccccccccccccccc",
            "opcode": 6,
            "namespace": "OP_0X06",
            "group": 3,
            "instance": 0,
            "register": 28,
            "target_address": 38,
            "source_address": 247,
            "group_meaning": "fixture-group-remote",
            "instance_gate": "fixture-gate-remote",
            "register_category": "STATE",
            "unit_scale_source": "fixture-catalog-v1",
        },
        {
            "family": "B555",
            "target_pseudonym": "target-dddddddddddddddddddddddddddddddd",
            "device_family": "fixture-device-family",
            "schedule_program": "fixture-program-1",
            "slot_index": 0,
            "day_of_week": "MONDAY",
            "time_identity": "06:00:00",
            "operation_mode_context": "fixture-mode",
            "unit_scale_source": "fixture-catalog-v1",
        },
    ]
    entity = f"entity-{index + 1:02d}-opaque"
    service = f"service-{index + 1:02d}-opaque"
    feature = f"feature-{index + 1:02d}-opaque"
    return {
        "ebus": ebus_values[index],
        "eebus": {
            "entity": entity,
            "service": service,
            "feature": feature,
            "path": [
                {"kind": "ENTITY", "selector": entity},
                {"kind": "SERVICE", "selector": service},
                {"kind": "FEATURE", "selector": feature},
                {"kind": "FIELD", "selector": "value-opaque"},
            ],
        },
    }


def comparator(terminal_state: str) -> dict[str, object]:
    outcomes = {
        "NO_SIGNAL": ("NOT_EVALUATED", 0, 3),
        "CLOUD_ONLY": ("INDETERMINATE", 0, 3),
        "CONFLICT": ("CONFLICT", 3, 0),
        "NOT_TESTED": ("NOT_EVALUATED", 0, 3),
    }
    outcome, observed, missing = outcomes[terminal_state]
    return {
        "type": "NUMERIC_WINDOW",
        "window": {
            "start_offset_ns": 0,
            "end_offset_ns": 180_000_000_000,
            "sample_period_ns": 60_000_000_000,
        },
        "tolerance": {
            "mode": "ABSOLUTE_OR_RELATIVE",
            "absolute_decimal": "0.2",
            "relative_ppm": 1000,
        },
        "conversion": {
            "mode": "IDENTITY",
            "source_unit": "fixture-unit",
            "target_unit": "fixture-unit",
            "scale_decimal": "1",
            "offset_decimal": "0",
        },
        "rounding": {"mode": "HALF_EVEN", "decimal_places": 2},
        "minimum_samples": 3,
        "maximum_missing": 3,
        "stale_cutoff_ns": 120_000_000_000,
        "conflict_threshold": {
            "absolute_decimal": "0.5",
            "consecutive_samples": 2,
        },
        "observed_samples": observed,
        "missing_samples": missing,
        "outcome": outcome,
    }


def mutable_proof() -> dict[str, object]:
    cycles = []
    for index in range(3):
        digit = str(index + 1)
        cycles.append(
            {
                "cycle_id": f"fixture-cycle-{index + 1}",
                "performed_at": f"2026-07-20T00:{(index + 1) * 10:02d}:00Z",
                "perturbation_input_hash": "sha256:" + digit * 64,
                "observed_state_hash": "sha256:" + str(index + 4) * 64,
                "rollback_state_hash": "sha256:" + str(index + 7) * 64,
                "independent": True,
                "rollback": "EXACT",
            }
        )
    return {
        "lab_whitelist_id": "fixture-lab-whitelist-entry",
        "lease": {
            "lease_id": "fixture-lease-redacted",
            "holder": "fixture-writer-redacted",
            "valid_from": "2026-07-20T00:00:00Z",
            "valid_until": "2026-07-20T01:00:00Z",
        },
        "one_writer": True,
        "writer_id": "fixture-writer-redacted",
        "write_path": "GATEWAY_ROUTER_ONLY",
        "direct_adapter_write": False,
        "abort_conditions": [
            "LEASE_EXPIRED",
            "WRITER_CONFLICT",
            "GATEWAY_ROUTER_PATH_LOST",
            "SOURCE_STALE",
            "CONFLICT_THRESHOLD_EXCEEDED",
            "ROLLBACK_FAILED",
        ],
        "cycles": cycles,
    }


def build_dossier() -> dict[str, object]:
    registry_raw = REGISTRY_PATH.read_bytes()
    m7_graph = load(M7_GRAPH_PATH)
    m7_replay = load(M7_REPLAY_PATH)
    m8_evidence = load(M8_EVIDENCE_PATH)
    m8_report = load(M8_REPORT_PATH)
    source_bindings = {
        "m7_graph_id": m7_graph["graph_id"],
        "m7_graph_hash": m7_graph["graph_hash"],
        "m7_replay_id": m7_replay["replay_id"],
        "m7_replay_hash": m7_replay["replay_hash"],
        "m8_evidence_id": m8_evidence["evidence_id"],
        "m8_evidence_hash": m8_evidence["evidence_hash"],
        "m8_report_id": m8_report["report_id"],
        "m8_report_hash": m8_report["report_hash"],
        "coexistence_verdict": m8_report["verdict"],
    }
    states = ["NO_SIGNAL", "CLOUD_ONLY", "CONFLICT", "NOT_TESTED"]
    paths = [
        "/fixtures/leaf_01",
        "/fixtures/leaf_02",
        "/fixtures/leaf_03",
        "/fixtures/leaf_04",
    ]
    leaves = []
    protected_hashes = [
        item["canonical_payload_hash"]
        for item in m8_report["baseline"]["view_hashes"]
    ]
    scenario_run_ids = [m8_report["baseline"]["run_id"]]
    scenario_run_ids.extend(item["run_id"] for item in m8_report["scenarios"])
    scenario_run_ids = list(dict.fromkeys(scenario_run_ids))
    for index, (state, path) in enumerate(zip(states, paths, strict=True)):
        leaf: dict[str, object] = {
            "leaf_id": f"msp085-fixture-leaf-{index + 1:02d}",
            "semantic_path": path,
            "mutability": "MUTABLE" if index == 3 else "READ_ONLY",
            "source_identity": source_identity(index),
            "comparator": comparator(state),
            "decision": "WITHHELD",
            "terminal_state": state,
            "visibility": "RAW_DEBUG_ONLY",
            "inheritance": {"family": False, "device": False, "sibling": False},
            "coexistence_proof": {
                "report_id": m8_report["report_id"],
                "report_hash": m8_report["report_hash"],
                "scenario_run_ids": scenario_run_ids,
                "protected_view_hashes": protected_hashes,
                "no_drift": True,
                "rollback_exact": True,
            },
            "provenance": {
                "source_artifact_ids": [
                    f"ebus-artifact-redacted-{index + 1:02d}",
                    f"eebus-artifact-redacted-{index + 1:02d}",
                ],
                "redacted_input_hashes": [
                    m7_graph["graph_hash"],
                    m8_evidence["evidence_hash"],
                ],
                "normalized_output_hash": "sha256:" + "0" * 64,
            },
            "replay": {
                "tool_id": "leaf-promotion-replay",
                "tool_version": 1,
                "input_hashes": [
                    m7_replay["replay_hash"],
                    m8_report["report_hash"],
                ],
                "expected_output_hash": "sha256:" + "0" * 64,
                "actual_output_hash": "sha256:" + "0" * 64,
                "deterministic": True,
            },
            "retest_trigger": {
                "trigger": "SOURCE_RECOVERED" if index < 2 else "RUNTIME_CHANGED",
                "changed_inputs": ["evidence", "runtime"],
                "minimum_new_samples": 3,
            },
            "mutable_proof": mutable_proof() if index == 3 else None,
        }
        replay_hash = promotion.leaf_replay_hash(leaf)
        leaf["provenance"]["normalized_output_hash"] = replay_hash
        leaf["replay"]["expected_output_hash"] = replay_hash
        leaf["replay"]["actual_output_hash"] = replay_hash
        leaves.append(leaf)
    dossier: dict[str, object] = {
        "contract": promotion.DOSSIER_CONTRACT,
        "schema_version": 1,
        "dossier_id": "MSP085-SYNTHETIC-ZERO-PROMOTION-001",
        "evidence_class": "SYNTHETIC_OFFLINE_FIXTURE",
        "capture_context": "OFF_LAN",
        "positive_promotion_claim": False,
        "registry": {
            "contract": promotion.REGISTRY_CONTRACT,
            "version": 1,
            "digest": "sha256:" + hashlib.sha256(registry_raw).hexdigest(),
        },
        "source_bindings": source_bindings,
        "m9_consumer_gate": "BLOCKED_ZERO_PROMOTED_LEAVES",
        "leaves": leaves,
        "dossier_hash": "sha256:" + "0" * 64,
    }
    payload = {key: value for key, value in dossier.items() if key != "dossier_hash"}
    dossier["dossier_hash"] = promotion.digest(promotion.DOSSIER_DOMAIN, payload)
    return dossier


def write(path: pathlib.Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=pathlib.Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    dossier = build_dossier()
    write(args.output_root / "dossier.json", dossier)
    write(args.output_root / "result.json", promotion.build_result(copy.deepcopy(dossier)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
