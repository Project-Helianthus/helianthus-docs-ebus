#!/usr/bin/env python3
"""Generate the canonical synthetic MSP-08 positive fixture and report."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib

import validate_multi_runtime_coexistence as coexistence


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "docs/platform/fixtures/coexistence-no-drift/v1/positive"
REGISTRY_PATH = (
    REPO_ROOT / "docs/platform/schemas/multi-runtime-coexistence-registry-v1.json"
)
M7_ROOT = REPO_ROOT / "docs/platform/fixtures/candidate-fact-graph/v1/positive"
M7_GRAPH_PATH = M7_ROOT / "graph.json"
M7_REPLAY_PATH = M7_ROOT / "replay-result.json"


def load(path: pathlib.Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest(build_mode: str) -> dict[str, object]:
    return {
        "go_version": "go1.25.1",
        "target": "linux/arm64",
        "build_mode": build_mode,
        "flags": ["-trimpath", "CGO_ENABLED=0"],
    }


def _runtime(
    source_commit: str,
    source_parent_commit: str | None,
    artifact_digit: str,
    build_mode: str,
) -> dict[str, object]:
    manifest = _manifest(build_mode)
    artifact_digest = "sha256:" + artifact_digit * 64
    return {
        "repository": "github.com/Project-Helianthus/helianthus-ebusgateway",
        "source_commit": source_commit,
        "source_parent_commit": source_parent_commit,
        "artifact_id": "gateway:" + artifact_digest,
        "artifact_digest": artifact_digest,
        "artifact_size_bytes": 16_777_216,
        "build_manifest": manifest,
        "build_manifest_hash": coexistence.digest(coexistence.BUILD_DOMAIN, manifest),
    }


def _config(state: str, runtime_enabled: bool, graph_enabled: bool) -> dict[str, object]:
    payload = {
        "eebus_runtime_enabled": runtime_enabled,
        "candidate_graph_enabled": graph_enabled,
        "outbound_enabled": False,
        "public_v2_enabled": False,
    }
    return {
        "config_id": "msp08-" + state.lower().replace("_", "-"),
        "payload": payload,
        "config_hash": coexistence.digest(coexistence.CONFIG_DOMAIN, payload),
    }


def _auth_scope() -> dict[str, object]:
    value = {
        "scope_id": "msp08-read-only-contract-capture",
        "principal_class": "READ_ONLY_TEST",
        "permissions": [
            "read:ebus",
            "read:eebus-v1-contract",
            "read:graphql",
            "read:portal-bootstrap",
            "read:debug",
        ],
    }
    return {**value, "scope_hash": coexistence.digest(coexistence.AUTH_DOMAIN, value)}


def _view_payloads() -> dict[str, object]:
    return {
        "mcp.ebus.v1.responses": {
            "contract": "ebus.v1",
            "responses": [
                {
                    "operation": "ebus.v1.devices.list",
                    "result": {
                        "devices": [
                            {
                                "address": "0x15",
                                "device_id": "fixture-regulator",
                                "manufacturer": "fixture-vendor",
                            }
                        ]
                    },
                }
            ],
        },
        "mcp.tool.inventory": {
            "tools": [
                "ebus.v1.devices.list",
                "ebus.v1.zones.list",
                "eebus.v1.runtime.status",
                "eebus.v1.services.list",
            ]
        },
        "graphql.schema": {
            "query_fields": ["devices", "dhw", "energyTotals", "zones"],
            "schema_version": 1,
        },
        "graphql.ebus.values": {
            "zones": [
                {
                    "id": "fixture-zone-1",
                    "name": "Fixture Zone",
                    "currentTempC": "21.5",
                    "targetTempC": "22.0",
                    "source": "ebus",
                }
            ]
        },
        "ha.graphql.values": {
            "entities": [
                {
                    "entity_id": "climate.fixture_zone_1",
                    "state": "heat",
                    "current_temperature": "21.5",
                    "target_temperature": "22.0",
                }
            ]
        },
        "ha.identity": {
            "devices": [
                {
                    "unique_id": "helianthus-ebus-fixture-regulator",
                    "manufacturer": "fixture-vendor",
                    "model": "fixture-regulator",
                    "via_device": "helianthus-gateway-fixture",
                }
            ]
        },
        "debug.ebus": {
            "transport": "ENS",
            "frames_seen": 42,
            "decode_errors": 0,
            "last_frame": "fixture-redacted-frame",
        },
        "portal.ebus.bootstrap": {
            "sections": ["devices", "zones", "dhw", "energy"],
            "default_protocol": "ebus",
        },
        "command.routing": {
            "routes": [
                {"semantic_path": "/zones/fixture/setpoint", "source": "ebus"}
            ],
            "fallback": None,
        },
        "semantic.registry": {
            "authority": "ebus.promoted",
            "leaves": [
                {
                    "path": "/zones/fixture/current_temp",
                    "source": "ebus",
                    "promotion_state": "PROMOTED",
                }
            ],
        },
        "mcp.eebus.v1.contract": {
            "namespace": "eebus.v1",
            "version": 1,
            "schema_digest": "sha256:" + "d" * 64,
            "public_v2": False,
        },
    }


def _views(
    registry: dict[str, object], run_index: int
) -> list[dict[str, object]]:
    payloads = _view_payloads()
    rule_by_id = {rule["view_id"]: rule for rule in registry["view_rules"]}
    result: list[dict[str, object]] = []
    for view_id in registry["protected_views"]:
        payload = {
            "meta": {
                "captured_at": f"2026-07-20T00:00:0{run_index}Z",
                "auth_subject": f"fixture-principal-{run_index}",
            },
            "data": copy.deepcopy(payloads[view_id]),
        }
        rule = rule_by_id[view_id]
        normalized = copy.deepcopy(payload)
        for pointer in rule["timestamp_pointers"]:
            parent, leaf = coexistence._resolve_pointer(normalized, pointer)
            parent[leaf] = "<TIMESTAMP>"
        for pointer in rule["mask_pointers"]:
            parent, leaf = coexistence._resolve_pointer(normalized, pointer)
            parent[leaf] = "<MASKED>"
        result.append(
            {
                "view_id": view_id,
                "capture_path": rule["capture_path"],
                "media_type": "application/json",
                "payload": payload,
                "raw_payload_hash": coexistence.digest(
                    coexistence.RAW_PAYLOAD_DOMAIN, payload
                ),
                "shape_hash": coexistence.digest(
                    coexistence.SHAPE_DOMAIN, coexistence.payload_shape(payload)
                ),
                "canonical_payload_hash": coexistence.digest(
                    coexistence.CANONICAL_PAYLOAD_DOMAIN, normalized
                ),
            }
        )
    return result


def _state_evidence(state: str) -> dict[str, object]:
    values: dict[str, tuple[object, ...]] = {
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
            [
                {
                    "candidate_id": "m7-candidate-synthetic-0001",
                    "status": "CANDIDATE",
                    "terminal_negative_state": None,
                    "visibility_channel": "CANDIDATE_DEBUG_REPLAY",
                }
            ],
        ),
        "EEBUS_CONFLICTED_WITHHELD": (
            "CONFLICT_WITHHELD_OBSERVED",
            True,
            True,
            1,
            0,
            1,
            True,
            [
                {
                    "candidate_id": "m7-candidate-synthetic-conflict-0001",
                    "status": "WITHHELD",
                    "terminal_negative_state": "CONFLICT",
                    "visibility_channel": "CANDIDATE_DEBUG_REPLAY",
                }
            ],
        ),
        "EEBUS_DISABLED_ROLLBACK": ("ROLLBACK_BASELINE_RESTORED", False, False, 0, 0, 0, False, []),
    }
    (
        outcome,
        runtime_enabled,
        graph_enabled,
        service_count,
        candidate_count,
        conflict_count,
        degraded,
        facts,
    ) = values[state]
    return {
        "outcome": outcome,
        "eebus_runtime_enabled": runtime_enabled,
        "candidate_graph_enabled": graph_enabled,
        "service_count": service_count,
        "candidate_count": candidate_count,
        "conflict_count": conflict_count,
        "degraded": degraded,
        "empty_success": False,
        "facts": facts,
    }


def build_evidence(
    registry: dict[str, object], registry_raw: bytes, graph: dict[str, object], replay: dict[str, object]
) -> dict[str, object]:
    profile = {
        "profile_id": "multi-runtime-coexistence-no-drift-v1",
        "canonicalization": "RFC8785_JCS_INTEGER_SUBSET",
        "timestamp_replacement": "<TIMESTAMP>",
        "mask_replacement": "<MASKED>",
        "view_rules": copy.deepcopy(registry["view_rules"]),
    }
    profile["profile_digest"] = coexistence.digest(coexistence.PROFILE_DOMAIN, profile)
    clock = {
        "clock_id": "clock-0123456789abcdef0123456789abcdef",
        "basis": "MONOTONIC_CAPTURE_OFFSETS",
        "wall_anchor_utc": "2026-07-20T00:00:00Z",
        "monotonic_epoch_id": "msp08-synthetic-clock-epoch",
        "max_clock_error_ns": 1_000_000,
        "max_capture_age_ns": 10_000_000_000,
        "verification_offset_ns": 6_000_000_000,
    }
    clock["clock_hash"] = coexistence.digest(coexistence.CLOCK_DOMAIN, clock)
    baseline_runtime = _runtime(coexistence.BASELINE_SOURCE_SHA, None, "c", "REPRODUCIBLE_BUILD")
    compared_runtime = _runtime("a" * 40, coexistence.BASELINE_SOURCE_SHA, "b", "SYNTHETIC_FIXTURE")
    auth = _auth_scope()
    runs: list[dict[str, object]] = []
    for index, state in enumerate(registry["scenario_order"]):
        views = _views(registry, index)
        state_evidence = _state_evidence(state)
        runtime = baseline_runtime if index == 0 else compared_runtime
        config = _config(
            state,
            state_evidence["eebus_runtime_enabled"],
            state_evidence["candidate_graph_enabled"],
        )
        inputs = [
            {
                "input_id": "view:" + view["view_id"],
                "kind": "PROTECTED_VIEW_PAYLOAD",
                "digest": view["raw_payload_hash"],
                "byte_length": len(coexistence.canonical(view["payload"])),
            }
            for view in views
        ]
        inputs.extend(
            [
                {
                    "input_id": "m7:graph",
                    "kind": "M7_GRAPH",
                    "digest": graph["graph_hash"],
                    "byte_length": len(coexistence.canonical(graph)),
                },
                {
                    "input_id": "m7:replay",
                    "kind": "M7_REPLAY",
                    "digest": replay["replay_hash"],
                    "byte_length": len(coexistence.canonical(replay)),
                },
            ]
        )
        runs.append(
            {
                "run_id": f"msp08-run-{index + 1:02d}",
                "state": state,
                "capture_offset_ns": index * 1_000_000_000,
                "provenance": {
                    "capture_clock_id": clock["clock_id"],
                    "runtime": copy.deepcopy(runtime),
                    "config": config,
                    "auth_scope": copy.deepcopy(auth),
                    "mask_scope_digest": profile["profile_digest"],
                    "immutable_inputs": inputs,
                },
                "state_evidence": state_evidence,
                "protected_views": views,
            }
        )
    evidence = {
        "contract": coexistence.EVIDENCE_CONTRACT,
        "schema_version": 1,
        "fixture_id": registry["fixture_ids"]["positive_evidence"],
        "evidence_class": "SYNTHETIC_OFFLINE_FIXTURE",
        "evidence_id": "mrcv1:sha256:" + "0" * 64,
        "evidence_hash": "sha256:" + "0" * 64,
        "registry": {
            "contract": registry["contract"],
            "version": registry["version"],
            "digest": "sha256:" + hashlib.sha256(registry_raw).hexdigest(),
        },
        "scope": {
            "gate": "EEBUS-G18",
            "claims": ["EEBUS-G18"],
            "excluded_gates": ["EEBUS-G17", "EEBUS-G19"],
            "live_vr940_claim": False,
            "public_version_policy": "V1_ONLY_NO_PUBLIC_V2",
        },
        "m7_binding": {
            "completion_token": registry["m7_completion_token"],
            "docs_source_commit": registry["m7_docs_source_commit"],
            **copy.deepcopy(registry["m7_binding"]),
        },
        "capture_clock": clock,
        "normalization": profile,
        "limits": copy.deepcopy(registry["limits"]),
        "runs": runs,
    }
    hash_view = {
        key: value
        for key, value in evidence.items()
        if key not in {"evidence_id", "evidence_hash"}
    }
    evidence_hash = coexistence.digest(coexistence.EVIDENCE_DOMAIN, hash_view)
    evidence["evidence_id"] = "mrcv1:" + evidence_hash
    evidence["evidence_hash"] = evidence_hash
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=pathlib.Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    registry_raw = REGISTRY_PATH.read_bytes()
    registry = json.loads(registry_raw.decode("utf-8"))
    graph = load(M7_GRAPH_PATH)
    replay = load(M7_REPLAY_PATH)
    evidence = build_evidence(registry, registry_raw, graph, replay)
    report = coexistence.report(evidence, registry)
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.output_root / "report.json").write_text(
        coexistence.canonical(report).decode("utf-8") + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
