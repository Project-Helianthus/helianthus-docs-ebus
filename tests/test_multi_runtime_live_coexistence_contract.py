from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import time
from copy import deepcopy

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = REPO_ROOT / "docs/platform/multi-runtime-coexistence-no-drift-v1.md"
EVIDENCE_SCHEMA = (
    REPO_ROOT
    / "docs/platform/schemas/multi-runtime-coexistence-evidence-v1.schema.json"
)
REPORT_SCHEMA = (
    REPO_ROOT
    / "docs/platform/schemas/multi-runtime-coexistence-report-v1.schema.json"
)
M7_STATUS_SCHEMA = (
    REPO_ROOT
    / "docs/platform/schemas/draft-candidate-fact-public-status-v1.schema.json"
)
REGISTRY = (
    REPO_ROOT
    / "docs/platform/schemas/multi-runtime-coexistence-registry-v1.json"
)
VALIDATOR = REPO_ROOT / "scripts/validate_multi_runtime_coexistence.py"
STATUS_PROJECTOR = REPO_ROOT / "scripts/project_candidate_fact_public_status.py"
SYNTHETIC_EVIDENCE = (
    REPO_ROOT
    / "docs/platform/fixtures/coexistence-no-drift/v1/positive/evidence.json"
)
M7_ROOT = REPO_ROOT / "docs/platform/fixtures/candidate-fact-graph/v1/positive"
M7_GRAPH = M7_ROOT / "source-terminal-graph.json"
M7_REPLAY = M7_ROOT / "source-terminal-replay-result.json"
M7_SOURCE_BUNDLE = M7_ROOT / "source-terminal-bundle.json"
M7_SOURCE_REPLAY = M7_ROOT / "source-terminal-source-replay.json"
M7_LIVE_STATUS = M7_ROOT / "live-public-status.json"
M7_REGISTRY = REPO_ROOT / "docs/platform/schemas/draft-candidate-fact-registry-v1.json"
SYNCHRONIZED_ROOT = REPO_ROOT / "docs/platform/fixtures/synchronized-evidence/v1/positive"
M7_SYNTHETIC_GRAPH = M7_ROOT / "graph.json"
M7_SYNTHETIC_REPLAY = M7_ROOT / "replay-result.json"
M7_SYNTHETIC_SOURCE_BUNDLE = SYNCHRONIZED_ROOT / "bundle.json"
M7_SYNTHETIC_SOURCE_REPLAY = SYNCHRONIZED_ROOT / "replay-result.json"

M7_GATEWAY_MERGE = "8bcba2107d10b149f984ac9546ea6427a9cda8a1"
M7_DOCS_MERGE = "35d2eba256a77b6575a2b45c07e73f054ff74ced"
SYNTHETIC_PRIVATE_IPV4 = "10.255.255.254"
EXPECTED_EBUS_TOOLS = [
    "ebus.v1.registry.devices.list",
    "ebus.v1.semantic.snapshot.get",
]
EXPECTED_EEBUS_TOOLS = [
    "eebus.v1.runtime.status.get",
    "eebus.v1.services.list",
    "eebus.v1.services.get",
    "eebus.v1.sessions.list",
    "eebus.v1.sessions.get",
    "eebus.v1.topology.get",
    "eebus.v1.snapshot.capture",
    "eebus.v1.snapshot.drop",
    "eebus.v1.pairing.status.get",
]


def load(path: pathlib.Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def validator_module():
    spec = importlib.util.spec_from_file_location("msp08_validator", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_msp08_v1_declares_distinct_synthetic_and_live_profiles() -> None:
    registry = load(REGISTRY)

    assert "m7_completion_token" not in registry
    assert registry["m7_live_predecessor"] == {
        "repository": "github.com/Project-Helianthus/helianthus-ebusgateway",
        "source_commit": M7_GATEWAY_MERGE,
        "docs_source_commit": M7_DOCS_MERGE,
        "binding_mode": "VALIDATED_INPUTS_AND_REGENERATED_REPLAY",
    }
    assert (
        registry["m7_live_binding"]["graph_hash"]
        == registry["m7_live_status_binding"]["source_graph_hash"]
    )
    assert (
        registry["m7_live_binding"]["replay_hash"]
        == registry["m7_live_status_binding"]["source_replay_hash"]
    )
    assert (
        registry["m7_live_terminal_binding"]["graph_hash"]
        != registry["m7_live_binding"]["graph_hash"]
    )
    assert set(registry["m7_live_private_inputs"]) == {
        "graph",
        "replay",
        "source_bundle",
        "source_replay",
    }
    assert registry["scenario_profiles"]["SYNTHETIC_OFFLINE_FIXTURE"] == [
        "EEBUS_DISABLED_BASELINE",
        "EEBUS_DISABLED_CONFIRMED",
        "EEBUS_ENABLED_NO_SERVICES",
        "EEBUS_CONNECTED_CANDIDATE_ONLY",
        "EEBUS_CONFLICTED_WITHHELD",
        "EEBUS_DISABLED_ROLLBACK",
    ]
    assert registry["scenario_profiles"]["CAPTURED_RUNTIME_EVIDENCE"] == [
        "EEBUS_CONNECTED_BASELINE",
        "EEBUS_CONNECTED_RAW_WITHHELD",
        "EEBUS_RESTART_PERSISTED",
        "EEBUS_CONNECTED_ROLLBACK",
    ]


def test_msp08_v1_schema_exposes_real_live_fact_counts_and_m7_source() -> None:
    schema = load(EVIDENCE_SCHEMA)
    m7 = schema["$defs"]["M7Binding"]
    state = schema["$defs"]["StateEvidence"]

    assert "completion_token" not in m7["required"]
    assert "completion_token" not in m7["properties"]
    assert "source_commit" in m7["required"]
    assert "raw_only_count" in state["required"]
    assert "withheld_count" in state["required"]
    fact_ref = state["properties"]["facts"]["items"]["$ref"]
    fact = schema["$defs"][fact_ref.rsplit("/", 1)[-1]]
    assert "RAW_ONLY" in fact["properties"]["status"]["enum"]


def test_msp08_live_contract_is_same_artifact_raw_first_and_non_promoting() -> None:
    page = " ".join(PAGE.read_text(encoding="utf-8").split())

    for phrase in (
        "MSP-08-LIVE-R1",
        M7_GATEWAY_MERGE,
        M7_DOCS_MERGE,
        "same exact gateway artifact",
        "RAW_ONLY",
        "WITHHELD",
        "does not fabricate `CANDIDATE` or `CONFLICTED`",
        "restart persistence",
        "public-redacted",
        "does not authorize M8.5 or M9",
    ):
        assert phrase in page


def test_msp08_inventory_matches_the_complete_stable_v1_contract() -> None:
    validator = validator_module()
    evidence = load(SYNTHETIC_EVIDENCE)
    inventory = next(
        view
        for view in evidence["runs"][0]["protected_views"]
        if view["view_id"] == "mcp.tool.inventory"
    )

    assert inventory["payload"]["data"]["tools"] == [
        *EXPECTED_EBUS_TOOLS,
        *EXPECTED_EEBUS_TOOLS,
    ]
    assert validator.APPROVED_M8_EEBUS_TOOLS == EXPECTED_EEBUS_TOOLS
    assert validator.APPROVED_M8_TOOL_INVENTORY == [
        *EXPECTED_EBUS_TOOLS,
        *EXPECTED_EEBUS_TOOLS,
    ]


def test_msp08_machine_contract_matches_verifier_precedence_and_limits() -> None:
    validator = validator_module()
    registry = load(REGISTRY)
    schema = load(EVIDENCE_SCHEMA)
    limits = schema["$defs"]["Limits"]

    assert registry["validation_precedence"] == validator.VALIDATION_PRECEDENCE
    assert registry["limits"] == validator.HARD_LIMITS
    assert set(limits["required"]) == set(validator.HARD_LIMITS)
    assert limits["properties"]["max_source_input_bytes"]["const"] == (
        validator.MAX_SOURCE_INPUT_BYTES
    )
    assert limits["properties"]["max_source_total_bytes"]["const"] == (
        validator.MAX_SOURCE_TOTAL_BYTES
    )


@pytest.mark.parametrize("mutation", ["missing", "stale", "reordered", "write"])
def test_msp08_live_inventory_drift_fails_closed(
    tmp_path: pathlib.Path, mutation: str
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    for run in evidence["runs"][:-1]:
        inventory = next(
            view
            for view in run["protected_views"]
            if view["view_id"] == "mcp.tool.inventory"
        )
        tools = inventory["payload"]["data"]["tools"]
        if mutation == "missing":
            tools.remove("eebus.v1.sessions.get")
        elif mutation == "stale":
            tools[0] = "ebus.v1.devices.list"
        elif mutation == "reordered":
            tools[-1], tools[-2] = tools[-2], tools[-1]
        else:
            tools.append("eebus.v1.features.data.set")
    refresh_protected_views(validator, evidence)

    result = subprocess.run(
        validator_command("verify", write_evidence(tmp_path, evidence)),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        1,
        "gate.scope\n",
        "",
    )


def build_live_evidence(validator) -> dict[str, object]:
    registry = load(REGISTRY)
    evidence = deepcopy(load(SYNTHETIC_EVIDENCE))
    graph = load(M7_GRAPH)
    replay = load(M7_REPLAY)
    live_status = load(M7_LIVE_STATUS)

    evidence["registry"]["digest"] = "sha256:" + hashlib.sha256(
        REGISTRY.read_bytes()
    ).hexdigest()

    evidence["fixture_id"] = "MSP08-G18-LIVE-EVIDENCE-TEST001"
    evidence["evidence_class"] = "CAPTURED_RUNTIME_EVIDENCE"
    evidence["scope"]["live_vr940_claim"] = True
    evidence["m7_binding"] = {
        "source_commit": M7_GATEWAY_MERGE,
        "docs_source_commit": M7_DOCS_MERGE,
        **deepcopy(registry["m7_live_binding"]),
    }
    evidence["m7_live_status"] = deepcopy(registry["m7_live_status_binding"])

    selected = [deepcopy(evidence["runs"][index]) for index in (0, 3, 3, 5)]
    runtime = deepcopy(evidence["runs"][1]["provenance"]["runtime"])
    runtime["source_commit"] = "9" * 40
    runtime["source_parent_commit"] = M7_GATEWAY_MERGE
    runtime["build_manifest"]["build_mode"] = "REPRODUCIBLE_BUILD"
    runtime["build_manifest_hash"] = validator.digest(
        validator.BUILD_DOMAIN, runtime["build_manifest"]
    )
    facts = [
        {
            "candidate_id": fact["candidate_id"],
            "status": fact["status"],
            "terminal_negative_state": fact["terminal_negative_state"],
            "visibility_channel": "CANDIDATE_DEBUG_REPLAY",
        }
        for fact in live_status["facts"]
    ]
    states = registry["scenario_profiles"]["CAPTURED_RUNTIME_EVIDENCE"]
    outcomes = (
        "CONNECTED_BASELINE_CAPTURED",
        "RAW_WITHHELD_OBSERVED",
        "RESTART_PERSISTED",
        "GRAPH_EVIDENCE_DROPPED",
    )
    graph_enabled = (False, True, True, False)
    process_ids = ("process-" + "a" * 32, "process-" + "b" * 32)
    trust_state_id = "redacted:sha256:" + "c" * 12
    peer_binding_id = "redacted:sha256:" + "d" * 12
    session_ids = (
        "redacted:sha256:" + "e" * 12,
        "redacted:sha256:" + "f" * 12,
    )
    for index, run in enumerate(selected):
        run["run_id"] = f"msp08-run-{index + 1:02d}"
        run["state"] = states[index]
        run["capture_offset_ns"] = index * 1_000_000_000
        run["provenance"]["runtime"] = deepcopy(runtime)
        run["provenance"]["process_instance_id"] = process_ids[index // 2]
        payload = run["provenance"]["config"]["payload"]
        payload.update(
            {
                "eebus_runtime_enabled": True,
                "candidate_graph_enabled": graph_enabled[index],
                "outbound_enabled": True,
                "public_v2_enabled": False,
            }
        )
        run["provenance"]["config"]["config_hash"] = validator.digest(
            validator.CONFIG_DOMAIN, payload
        )
        state_facts = facts if graph_enabled[index] else []
        run["state_evidence"] = {
            "outcome": outcomes[index],
            "eebus_runtime_enabled": True,
            "candidate_graph_enabled": graph_enabled[index],
            "service_count": 1,
            "raw_only_count": sum(fact["status"] == "RAW_ONLY" for fact in state_facts),
            "candidate_count": sum(fact["status"] == "CANDIDATE" for fact in state_facts),
            "conflict_count": sum(fact["status"] == "CONFLICTED" for fact in state_facts),
            "withheld_count": sum(fact["status"] == "WITHHELD" for fact in state_facts),
            "degraded": False,
            "empty_success": False,
            "facts": state_facts,
            "restart_transition": (
                {
                    "event_id": "restart-event-redacted-001",
                    "before_process_instance_id": process_ids[0],
                    "after_process_instance_id": process_ids[1],
                    "before_trust_state_hash": validator.digest(
                        validator.RESTART_TRUST_DOMAIN, {"trust_state_id": trust_state_id}
                    ),
                    "after_trust_state_hash": validator.digest(
                        validator.RESTART_TRUST_DOMAIN, {"trust_state_id": trust_state_id}
                    ),
                    "before_peer_binding_hash": validator.digest(
                        validator.RESTART_PEER_DOMAIN, {"peer_binding_id": peer_binding_id}
                    ),
                    "after_peer_binding_hash": validator.digest(
                        validator.RESTART_PEER_DOMAIN, {"peer_binding_id": peer_binding_id}
                    ),
                    "session_reconnected": True,
                    "process_event": {
                        "event_id": "restart-event-redacted-001",
                        "event_type": "PROCESS_RESTART_OBSERVED",
                        "before_process_instance_id": process_ids[0],
                        "after_process_instance_id": process_ids[1],
                        "observed_at_offset_ns": 2_000_000_000,
                    },
                    "before_snapshot": {
                        "process_instance_id": process_ids[0],
                        "capture_offset_ns": 1_000_000_000,
                        "trust_state_id": trust_state_id,
                        "peer_binding_id": peer_binding_id,
                        "session_id": session_ids[0],
                        "session_state": "CONNECTED",
                    },
                    "after_snapshot": {
                        "process_instance_id": process_ids[1],
                        "capture_offset_ns": 2_000_000_000,
                        "trust_state_id": trust_state_id,
                        "peer_binding_id": peer_binding_id,
                        "session_id": session_ids[1],
                        "session_state": "CONNECTED",
                    },
                    "session_event": {
                        "event_id": "session-reconnected-redacted-001",
                        "event_type": "SESSION_RECONNECTED_OBSERVED",
                        "process_instance_id": process_ids[1],
                        "session_id": session_ids[1],
                        "observed_at_offset_ns": 2_000_000_000,
                        "state": "CONNECTED",
                    },
                }
                if index == 2
                else None
            ),
        }
        run["provenance"]["immutable_inputs"] = [
            item
            for item in run["provenance"]["immutable_inputs"]
            if item["input_id"].startswith("view:")
        ]
        terminal_binding = registry["m7_live_terminal_binding"]
        private_inputs = registry["m7_live_private_inputs"]
        run["provenance"]["immutable_inputs"].extend(
            [
                {
                    "input_id": "m7:terminal-graph",
                    "kind": "M7_TERMINAL_GRAPH",
                    "digest": graph["graph_hash"],
                    "byte_length": len(validator.canonical(graph)),
                },
                {
                    "input_id": "m7:terminal-replay",
                    "kind": "M7_TERMINAL_REPLAY",
                    "digest": replay["replay_hash"],
                    "byte_length": len(validator.canonical(replay)),
                },
                {
                    "input_id": "m7:registry",
                    "kind": "M7_REGISTRY",
                    "digest": terminal_binding["registry_content_hash"],
                    "byte_length": len(M7_REGISTRY.read_bytes()),
                },
                {
                    "input_id": "m7:terminal-source-bundle",
                    "kind": "M7_TERMINAL_SOURCE_BUNDLE",
                    "digest": terminal_binding["source_bundle_content_hash"],
                    "byte_length": len(M7_SOURCE_BUNDLE.read_bytes()),
                },
                {
                    "input_id": "m7:terminal-source-replay",
                    "kind": "M7_TERMINAL_SOURCE_REPLAY",
                    "digest": terminal_binding["source_replay_content_hash"],
                    "byte_length": len(M7_SOURCE_REPLAY.read_bytes()),
                },
                *[
                    {
                        "input_id": "m7:private-" + name.replace("_", "-"),
                        "kind": "M7_PRIVATE_" + name.upper(),
                        "digest": private_inputs[name]["digest"],
                        "byte_length": private_inputs[name]["byte_length"],
                    }
                    for name in (
                        "graph",
                        "replay",
                        "source_bundle",
                        "source_replay",
                    )
                ],
                {
                    "input_id": "m7:status-projection",
                    "kind": "M7_PUBLIC_STATUS",
                    "digest": evidence["m7_live_status"]["content_hash"],
                    "byte_length": len(M7_LIVE_STATUS.read_bytes()),
                },
                {
                    "input_id": "source:capture-manifest",
                    "kind": "SOURCE_CAPTURE_MANIFEST",
                    "digest": "sha256:" + ("1" if index < 2 else "2") * 64,
                    "byte_length": 1024,
                },
            ]
        )
        if index == 2:
            transition = run["state_evidence"]["restart_transition"]
            for input_id, kind, domain, field in (
                (
                    "restart:process-event",
                    "RESTART_PROCESS_EVENT",
                    validator.RESTART_PROCESS_EVENT_DOMAIN,
                    "process_event",
                ),
                (
                    "restart:before-snapshot",
                    "RESTART_STATE_SNAPSHOT",
                    validator.RESTART_SNAPSHOT_DOMAIN,
                    "before_snapshot",
                ),
                (
                    "restart:after-snapshot",
                    "RESTART_STATE_SNAPSHOT",
                    validator.RESTART_SNAPSHOT_DOMAIN,
                    "after_snapshot",
                ),
                (
                    "restart:session-event",
                    "RESTART_SESSION_EVENT",
                    validator.RESTART_SESSION_EVENT_DOMAIN,
                    "session_event",
                ),
            ):
                payload = transition[field]
                run["provenance"]["immutable_inputs"].append(
                    {
                        "input_id": input_id,
                        "kind": kind,
                        "digest": validator.digest(domain, payload),
                        "byte_length": len(validator.canonical(payload)),
                    }
                )
    evidence["runs"] = selected
    refresh_evidence_hash(validator, evidence)
    return evidence


def refresh_evidence_hash(validator, evidence: dict[str, object]) -> None:
    evidence_view = {
        key: value
        for key, value in evidence.items()
        if key not in {"evidence_id", "evidence_hash"}
    }
    evidence_hash = validator.digest(validator.EVIDENCE_DOMAIN, evidence_view)
    evidence["evidence_hash"] = evidence_hash
    evidence["evidence_id"] = "mrcv1:" + evidence_hash


def refresh_protected_views(validator, evidence: dict[str, object]) -> None:
    registry = load(REGISTRY)
    rules = {rule["view_id"]: rule for rule in registry["view_rules"]}
    for run in evidence["runs"]:
        inputs = {
            item["input_id"]: item for item in run["provenance"]["immutable_inputs"]
        }
        for view in run["protected_views"]:
            normalized = validator.normalized_payload(
                view["payload"], rules[view["view_id"]], evidence["normalization"]
            )
            view["raw_payload_hash"] = validator.digest(
                validator.RAW_PAYLOAD_DOMAIN, view["payload"]
            )
            view["shape_hash"] = validator.digest(
                validator.SHAPE_DOMAIN, validator.payload_shape(view["payload"])
            )
            view["canonical_payload_hash"] = validator.digest(
                validator.CANONICAL_PAYLOAD_DOMAIN, normalized
            )
            item = inputs["view:" + view["view_id"]]
            item["digest"] = view["raw_payload_hash"]
            item["byte_length"] = len(validator.canonical(view["payload"]))
    refresh_evidence_hash(validator, evidence)


def validator_command(
    command: str,
    evidence_path: pathlib.Path,
    *,
    graph: pathlib.Path = M7_GRAPH,
    replay: pathlib.Path = M7_REPLAY,
    source_bundle: pathlib.Path = M7_SOURCE_BUNDLE,
    source_replay: pathlib.Path = M7_SOURCE_REPLAY,
    live_status: pathlib.Path = M7_LIVE_STATUS,
) -> list[str]:
    return [
        sys.executable,
        str(VALIDATOR),
        "verify-public" if command == "verify" else command,
        "--evidence",
        str(evidence_path),
        "--registry",
        str(REGISTRY),
        "--m7-terminal-graph",
        str(graph),
        "--m7-terminal-replay",
        str(replay),
        "--m7-registry",
        str(M7_REGISTRY),
        "--m7-terminal-source-bundle",
        str(source_bundle),
        "--m7-terminal-source-replay",
        str(source_replay),
        "--m7-live-status",
        str(live_status),
    ]


def write_evidence(tmp_path: pathlib.Path, evidence: dict[str, object]) -> pathlib.Path:
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    return evidence_path


def source_mcp(validator, data: object) -> bytes:
    inner = {"data": data, "meta": {"contract": "test"}}
    return validator.canonical(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "isError": False,
                "content": [
                    {"type": "text", "text": validator.canonical(inner).decode("utf-8")}
                ]
            },
        }
    )


def source_payloads(
    validator, source_key: str, captured_at: str
) -> dict[str, bytes]:
    tools = [
        {"name": name, "inputSchema": {"type": "object", "properties": {}}}
        for name in validator.APPROVED_M8_TOOL_INVENTORY
    ]
    devices = [
        {
            "address": 8,
            "manufacturer": "Vaillant",
            "device_id": "BAI00",
            "discovery_source": "active_confirmed",
            "verification_state": "identity_confirmed",
        },
        {
            "address": 38,
            "manufacturer": "Vaillant",
            "device_id": "VR_71",
            "discovery_source": "active_confirmed",
            "verification_state": "identity_confirmed",
        },
    ]
    semantic = {
        "completed_planes": ["zones", "dhw", "system"],
        "planes": {
            "zones": [
                {
                    "id": "zone-1",
                    "name": "Zone 1",
                    "config": {
                        "operating_mode": "auto",
                        "preset": "comfort",
                        "target_temp_c": 21.5,
                        "associated_circuit": 1,
                    },
                }
            ],
            "dhw": {"config": {"operating_mode": "auto", "preset": "comfort"}},
            "system": {
                "properties": {"system_scheme": 8, "module_configuration_vr71": 3}
            },
        },
    }
    graph_values = {
        "data": {
            "zones": [
                {
                    "id": "zone-1",
                    "name": "Zone 1",
                    "config": {"operatingMode": "auto", "targetTempC": 21.5},
                }
            ],
            "dhw": {"config": {"operatingMode": "auto"}},
        }
    }
    routes = {
        "fallback": None,
        "routes": [
            {"semantic_path": "/dhw/operating_mode", "source": "ebus"},
            {"semantic_path": "/zones/1/target_temperature", "source": "ebus"},
        ],
    }
    semantic_registry = {
        "authority": "ebus.promoted",
        "leaves": [
            {
                "path": item["semantic_path"],
                "promotion_state": "PROMOTED",
                "source": item["source"],
            }
            for item in routes["routes"]
        ],
    }
    return {
        "tools.list": validator.canonical({"result": {"tools": tools}}),
        "ebus.devices": source_mcp(validator, devices),
        "ebus.semantic": source_mcp(validator, semantic),
        "ebus.debug": validator.canonical(
            {
                "transport": "ENS",
                "runtime_state": "running",
                "registry_device_count": len(devices),
                "last_frame": "redacted-live-frame",
            }
        ),
        "eebus.runtime": source_mcp(validator, {"state": "ready"}),
        "eebus.services": source_mcp(validator, {"services": [{"id": "service-1"}]}),
        "eebus.sessions": source_mcp(
            validator, {"sessions": [{"id": "session-1", "state": "connected"}]}
        ),
        "eebus.pairing": source_mcp(
            validator, {"pairing": [{"remote_ski": "test", "state": "paired"}]}
        ),
        "eebus.topology": source_mcp(
            validator,
            {"devices": [{"address": "test"}], "entities": [], "features": [], "usecases": []},
        ),
        "graphql.schema": validator.canonical(
            {
                "data": {
                    "__schema": {
                        "queryType": {"fields": [{"name": "zones"}, {"name": "dhw"}]},
                        "mutationType": {"fields": [{"name": "setZone"}]},
                    }
                }
            }
        ),
        "graphql.values": validator.canonical(graph_values),
        "portal.bootstrap": validator.canonical(
            {"capabilities": {"devices": True, "zones": True}, "ui_version": "test-v1"}
        ),
        "command.routing": validator.canonical(routes),
        "semantic.registry": validator.canonical(semantic_registry),
        "container.inspect": validator.canonical(
            [
                {
                    "Id": "container-" + source_key,
                    "State": {"StartedAt": captured_at},
                }
            ]
        ),
        "capture.timestamp": (captured_at + "\n").encode("utf-8"),
    }


def write_source_root(
    validator, tmp_path: pathlib.Path, source_key: str, captured_at: str
) -> tuple[pathlib.Path, dict[str, bytes], dict[str, object]]:
    root = tmp_path / f"source-{source_key}"
    root.mkdir()
    payloads = source_payloads(validator, source_key, captured_at)
    for input_id, raw in payloads.items():
        (root / validator.SOURCE_CAPTURE_FILES[input_id]).write_bytes(raw)
    return root, payloads, validator._source_project_views(payloads)


def source_manifest(
    validator,
    payloads: dict[str, bytes],
    *,
    auth_scope_hash: str,
    window_id: str,
    phase: str,
    process_instance_id: str,
    capture_start_offset_ns: int,
    capture_end_offset_ns: int,
) -> bytes:
    captured_at = payloads["capture.timestamp"].decode("utf-8").strip()
    value = {
        "contract": validator.SOURCE_CAPTURE_CONTRACT,
        "schema_version": 1,
        "window_id": window_id,
        "window_scope": "SINGLE_WINDOW_ONLY",
        "phase": phase,
        "projection_policy": validator.SOURCE_CAPTURE_POLICY,
        "auth_scope_hash": auth_scope_hash,
        "process_instance_id": process_instance_id,
        "capture_start_offset_ns": capture_start_offset_ns,
        "capture_end_offset_ns": capture_end_offset_ns,
        "captured_at": captured_at,
        "inputs": [
            {
                "input_id": input_id,
                "auth_boundary": boundary,
                "digest": "sha256:" + hashlib.sha256(payloads[input_id]).hexdigest(),
                "byte_length": len(payloads[input_id]),
            }
            for input_id, boundary in validator.SOURCE_CAPTURE_INPUTS.items()
        ],
    }
    return validator.canonical(value)


def bind_source_manifests(
    validator, evidence: dict[str, object], tmp_path: pathlib.Path
) -> tuple[dict[str, bytes], dict[str, pathlib.Path]]:
    manifests: dict[str, bytes] = {}
    roots: dict[str, pathlib.Path] = {}
    projections: dict[str, dict[str, object]] = {}
    for source_key, run_indexes in (("before", (0, 1)), ("after", (2, 3))):
        start_offset = min(
            evidence["runs"][index]["capture_offset_ns"] for index in run_indexes
        )
        captured_at = validator._capture_time_at(
            evidence["capture_clock"], start_offset
        )
        root, payloads, projected = write_source_root(
            validator, tmp_path, source_key, captured_at
        )
        roots[source_key] = root
        projections[source_key] = projected
        scope_hashes = {
            evidence["runs"][index]["provenance"]["auth_scope"]["scope_hash"]
            for index in run_indexes
        }
        assert len(scope_hashes) == 1
        scope_hash = scope_hashes.pop()
        process_instance_id = projected["process_instance_id"]
        bound_payloads = validator._source_bound_payloads(
            projected["views"], captured_at, scope_hash
        )
        for index in run_indexes:
            run = evidence["runs"][index]
            run["provenance"]["process_instance_id"] = process_instance_id
            run["state_evidence"]["service_count"] = projected["service_count"]
            for view in run["protected_views"]:
                view["payload"] = deepcopy(bound_payloads[view["view_id"]])
        raw = source_manifest(
            validator,
            payloads,
            auth_scope_hash=scope_hash,
            window_id=f"window-{source_key}",
            phase=validator.SOURCE_CAPTURE_PHASES[source_key],
            process_instance_id=process_instance_id,
            capture_start_offset_ns=start_offset,
            capture_end_offset_ns=max(
                evidence["runs"][index]["capture_offset_ns"] for index in run_indexes
            ),
        )
        binding = ("sha256:" + hashlib.sha256(raw).hexdigest(), len(raw))
        for index in run_indexes:
            source = next(
                item
                for item in evidence["runs"][index]["provenance"]["immutable_inputs"]
                if item["input_id"] == validator.SOURCE_CAPTURE_INPUT_ID
            )
            source["digest"], source["byte_length"] = binding
        manifests[source_key] = raw
    transition = evidence["runs"][2]["state_evidence"]["restart_transition"]
    before_process = projections["before"]["process_instance_id"]
    after_process = projections["after"]["process_instance_id"]
    transition["before_process_instance_id"] = before_process
    transition["after_process_instance_id"] = after_process
    transition["process_event"]["before_process_instance_id"] = before_process
    transition["process_event"]["after_process_instance_id"] = after_process
    transition["before_snapshot"]["process_instance_id"] = before_process
    transition["after_snapshot"]["process_instance_id"] = after_process
    transition["session_event"]["process_instance_id"] = after_process
    refresh_protected_views(validator, evidence)
    for input_id, domain, field in (
        ("restart:process-event", validator.RESTART_PROCESS_EVENT_DOMAIN, "process_event"),
        ("restart:before-snapshot", validator.RESTART_SNAPSHOT_DOMAIN, "before_snapshot"),
        ("restart:after-snapshot", validator.RESTART_SNAPSHOT_DOMAIN, "after_snapshot"),
        ("restart:session-event", validator.RESTART_SESSION_EVENT_DOMAIN, "session_event"),
    ):
        item = next(
            item
            for item in evidence["runs"][2]["provenance"]["immutable_inputs"]
            if item["input_id"] == input_id
        )
        value = transition[field]
        item["digest"] = validator.digest(domain, value)
        item["byte_length"] = len(validator.canonical(value))
    refresh_evidence_hash(validator, evidence)
    return manifests, roots


def live_m7_inputs(validator, evidence: dict[str, object]) -> dict[str, tuple[str, int]]:
    return {
        item["input_id"]: (item["digest"], item["byte_length"])
        for item in evidence["runs"][0]["provenance"]["immutable_inputs"]
        if item["input_id"].startswith("m7:")
    }


def rebind_source_manifest(
    validator,
    evidence: dict[str, object],
    source_key: str,
    manifests: dict[str, bytes],
    roots: dict[str, pathlib.Path],
) -> None:
    value = json.loads(manifests[source_key])
    for item in value["inputs"]:
        raw = (roots[source_key] / validator.SOURCE_CAPTURE_FILES[item["input_id"]]).read_bytes()
        item["digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
        item["byte_length"] = len(raw)
    raw = validator.canonical(value)
    manifests[source_key] = raw
    binding = ("sha256:" + hashlib.sha256(raw).hexdigest(), len(raw))
    run_indexes = (0, 1) if source_key == "before" else (2, 3)
    for index in run_indexes:
        source = next(
            item
            for item in evidence["runs"][index]["provenance"]["immutable_inputs"]
            if item["input_id"] == validator.SOURCE_CAPTURE_INPUT_ID
        )
        source["digest"], source["byte_length"] = binding
    refresh_evidence_hash(validator, evidence)


def test_msp08_live_profile_validates_bound_m7_and_restart(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence_path = write_evidence(tmp_path, build_live_evidence(validator))
    result = subprocess.run(
        validator_command("verify", evidence_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "public-only-ok\n"


def test_msp08_live_public_evidence_requires_source_manifest_binding(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    for run in evidence["runs"]:
        run["provenance"]["immutable_inputs"] = [
            item for item in run["provenance"]["immutable_inputs"]
            if item["input_id"] != validator.SOURCE_CAPTURE_INPUT_ID
        ]
    refresh_evidence_hash(validator, evidence)
    result = subprocess.run(
        validator_command("verify", write_evidence(tmp_path, evidence)),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert (result.returncode, result.stdout) == (1, "provenance.source_capture\n")


def test_msp08_live_public_evidence_rejects_reused_window_binding(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    before = next(
        item
        for item in evidence["runs"][0]["provenance"]["immutable_inputs"]
        if item["input_id"] == validator.SOURCE_CAPTURE_INPUT_ID
    )
    for run in evidence["runs"][2:]:
        source = next(
            item
            for item in run["provenance"]["immutable_inputs"]
            if item["input_id"] == validator.SOURCE_CAPTURE_INPUT_ID
        )
        source["digest"] = before["digest"]
        source["byte_length"] = before["byte_length"]
    refresh_evidence_hash(validator, evidence)
    result = subprocess.run(
        validator_command("verify", write_evidence(tmp_path, evidence)),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert (result.returncode, result.stdout) == (1, "provenance.source_capture\n")


def test_msp08_live_public_evidence_rejects_same_digest_with_different_length(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    before = next(
        item
        for item in evidence["runs"][0]["provenance"]["immutable_inputs"]
        if item["input_id"] == validator.SOURCE_CAPTURE_INPUT_ID
    )
    for run in evidence["runs"][2:]:
        source = next(
            item
            for item in run["provenance"]["immutable_inputs"]
            if item["input_id"] == validator.SOURCE_CAPTURE_INPUT_ID
        )
        source["digest"] = before["digest"]
        source["byte_length"] = before["byte_length"] + 1
    refresh_evidence_hash(validator, evidence)
    result = subprocess.run(
        validator_command("verify", write_evidence(tmp_path, evidence)),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert (result.returncode, result.stdout) == (1, "provenance.source_capture\n")


def test_msp08_source_manifest_binds_one_window_and_auth_scope(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    run = evidence["runs"][0]
    raw = manifests["before"]
    binding = validator._source_capture_binding(
        raw,
        roots["before"],
        run["provenance"]["auth_scope"]["scope_hash"],
        "PRE_RESTART",
        run["provenance"]["process_instance_id"],
        evidence["runs"][0]["capture_offset_ns"],
        evidence["runs"][1]["capture_offset_ns"],
        json.loads(raw)["captured_at"],
    )
    assert binding["digest"] == "sha256:" + hashlib.sha256(raw).hexdigest()
    assert binding["byte_length"] == len(raw)
    value = json.loads(raw)
    value["window_scope"] = "PRE_AND_POST"
    with pytest.raises(Exception) as error:
        validator._source_capture_binding(
            validator.canonical(value),
            roots["before"],
            run["provenance"]["auth_scope"]["scope_hash"],
            "PRE_RESTART",
            run["provenance"]["process_instance_id"],
            evidence["runs"][0]["capture_offset_ns"],
            evidence["runs"][1]["capture_offset_ns"],
            json.loads(raw)["captured_at"],
        )
    assert str(error.value) == "provenance.source_capture"


def test_msp08_source_mcp_accepts_large_envelope_with_bounded_inner_values() -> None:
    validator = validator_module()
    values = [{"id": f"item-{index:04d}", "state": "visible"} for index in range(300)]
    raw = source_mcp(validator, {"items": values})

    assert len(json.loads(raw)["result"]["content"][0]["text"].encode("utf-8")) > (
        validator.HARD_LIMITS["max_string_bytes"]
    )
    assert validator._source_inner_mcp(raw)["data"]["items"] == values


def test_msp08_source_decimal_is_bounded_and_canonical() -> None:
    validator = validator_module()
    decoded = validator._decode_source_json(b'{"temperature":21.500}')

    assert validator._source_string_number(decoded["temperature"]) == "21.5"


def test_msp08_source_decimal_preserves_long_mcp_and_graphql_values() -> None:
    validator = validator_module()
    payloads = source_payloads(validator, "before", "2026-08-11T10:00:00Z")
    exact = b"12345678901234567890123456789.5"
    for source in ("ebus.semantic", "graphql.values"):
        payloads[source] = payloads[source].replace(b"21.5", exact)

    projected = validator._source_project_views(payloads)["views"]
    semantic = projected["mcp.ebus.v1.responses"]["responses"][1]["result"]
    expected = exact.decode("ascii")
    assert semantic["zones"][0]["target_temp_c"] == expected
    assert projected["graphql.ebus.values"]["zones"][0]["target_temp_c"] == expected
    assert projected["ha.graphql.values"]["entities"][0]["target_temperature"] == expected


def test_msp08_source_decimal_canonicalizes_zero_independent_of_context() -> None:
    validator = validator_module()
    with validator.decimal.localcontext() as context:
        context.prec = 2
        for raw in (b"0", b"0.0", b"0e3", b"0.000e-100"):
            decoded = validator._decode_source_json(b'{"value":' + raw + b"}")
            assert validator._source_string_number(decoded["value"]) == "0"


@pytest.mark.parametrize(
    "raw",
    (
        b'{"temperature":-0.0}',
        b'{"temperature":1e1025}',
        ('{"temperature":0.' + "1" * 129 + "}").encode("ascii"),
    ),
)
def test_msp08_source_decimal_rejects_nonportable_bounds(raw: bytes) -> None:
    validator = validator_module()

    with pytest.raises(Exception) as error:
        validator._decode_source_json(raw)
    assert str(error.value) == "provenance.source_capture"


def test_msp08_source_manifest_rejects_auth_boundary_drift(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    run = evidence["runs"][0]
    value = json.loads(manifests["before"])
    value["inputs"][0]["auth_boundary"] = "OWNER_UNIX_MCP"
    with pytest.raises(Exception) as error:
        validator._source_capture_binding(
            validator.canonical(value),
            roots["before"],
            run["provenance"]["auth_scope"]["scope_hash"],
            "PRE_RESTART",
            run["provenance"]["process_instance_id"],
            evidence["runs"][0]["capture_offset_ns"],
            evidence["runs"][1]["capture_offset_ns"],
            json.loads(manifests["before"])["captured_at"],
        )
    assert str(error.value) == "provenance.source_capture"


def test_msp08_private_runtime_binds_distinct_single_window_manifests(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)

    assert manifests["before"] != manifests["after"]
    validator.check_runtime(
        evidence,
        live_m7_inputs(validator, evidence),
        manifests,
        roots,
        require_private=True,
    )
    for run_index in (0, 2):
        views = {
            view["view_id"]: view["payload"]["data"]
            for view in evidence["runs"][run_index]["protected_views"]
        }
        semantic = views["mcp.ebus.v1.responses"]["responses"][1]["result"]
        assert semantic["zones"][0]["target_temp_c"] == "21.5"
        assert semantic["zones"][0]["name"].startswith("redacted:sha256:")
        assert views["graphql.ebus.values"]["zones"][0]["target_temp_c"] == "21.5"
        assert views["graphql.ebus.values"]["zones"][0]["name"] == semantic["zones"][0]["name"]
        assert views["ha.graphql.values"]["entities"][0]["target_temperature"] == "21.5"
        assert b"Zone 1" not in validator.canonical(views)


def test_msp08_private_window_rejects_unprojectable_source_device(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    path = roots["before"] / validator.SOURCE_CAPTURE_FILES["ebus.devices"]
    envelope = json.loads(path.read_bytes())
    inner = json.loads(envelope["result"]["content"][0]["text"])
    inner["data"][0]["address"] = "8"
    envelope["result"]["content"][0]["text"] = validator.canonical(inner).decode(
        "utf-8"
    )
    path.write_bytes(validator.canonical(envelope))
    rebind_source_manifest(validator, evidence, "before", manifests, roots)
    run = evidence["runs"][0]

    with pytest.raises(Exception) as error:
        validator._source_capture_binding(
            manifests["before"],
            roots["before"],
            run["provenance"]["auth_scope"]["scope_hash"],
            "PRE_RESTART",
            run["provenance"]["process_instance_id"],
            evidence["runs"][0]["capture_offset_ns"],
            evidence["runs"][1]["capture_offset_ns"],
            json.loads(manifests["before"])["captured_at"],
        )
    assert str(error.value) == "provenance.source_capture"


def test_msp08_private_runtime_accepts_nanosecond_window_offset(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    evidence["runs"][0]["capture_offset_ns"] = 1
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)

    assert json.loads(manifests["before"])["captured_at"].endswith(".000000001Z")
    validator.check_runtime(
        evidence,
        live_m7_inputs(validator, evidence),
        manifests,
        roots,
        require_private=True,
    )


@pytest.mark.parametrize("invalid", ({"x": 1}, [21], True, "21.5"))
def test_msp08_private_window_rejects_nonnumeric_graphql_temperature(
    tmp_path: pathlib.Path, invalid: object
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    path = roots["before"] / validator.SOURCE_CAPTURE_FILES["graphql.values"]
    value = json.loads(path.read_bytes())
    value["data"]["zones"][0]["config"]["targetTempC"] = invalid
    path.write_bytes(validator.canonical(value))
    rebind_source_manifest(validator, evidence, "before", manifests, roots)
    run = evidence["runs"][0]

    with pytest.raises(Exception) as error:
        validator._source_capture_binding(
            manifests["before"],
            roots["before"],
            run["provenance"]["auth_scope"]["scope_hash"],
            "PRE_RESTART",
            run["provenance"]["process_instance_id"],
            evidence["runs"][0]["capture_offset_ns"],
            evidence["runs"][1]["capture_offset_ns"],
            json.loads(manifests["before"])["captured_at"],
        )
    assert str(error.value) == "provenance.source_capture"


def test_msp08_private_runtime_requires_both_source_manifests(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    manifests["after"] = None

    with pytest.raises(Exception) as error:
        validator.check_runtime(
            evidence,
            live_m7_inputs(validator, evidence),
            manifests,
            roots,
            require_private=True,
        )
    assert str(error.value) == "provenance.source_capture"


def test_msp08_private_runtime_reports_manifest_size_limit(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    oversized = tmp_path / "oversized-manifest.json"
    with oversized.open("wb") as stream:
        stream.truncate(validator.MAX_SOURCE_INPUT_BYTES + 1)
    manifests["before"] = oversized

    with pytest.raises(Exception) as error:
        validator.check_runtime(
            evidence,
            live_m7_inputs(validator, evidence),
            manifests,
            roots,
            require_private=True,
        )
    assert str(error.value) == "limits.exceeded"


@pytest.mark.parametrize("mutation", ["reuse", "swap"])
def test_msp08_private_runtime_rejects_reused_or_swapped_windows(
    tmp_path: pathlib.Path, mutation: str
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    if mutation == "reuse":
        manifests["after"] = manifests["before"]
        roots["after"] = roots["before"]
    else:
        manifests = {"before": manifests["after"], "after": manifests["before"]}
        roots = {"before": roots["after"], "after": roots["before"]}

    with pytest.raises(Exception) as error:
        validator.check_runtime(
            evidence,
            live_m7_inputs(validator, evidence),
            manifests,
            roots,
            require_private=True,
        )
    assert str(error.value) == "provenance.source_capture"


def test_msp08_private_runtime_rejects_source_bytes_tampering(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    path = roots["before"] / validator.SOURCE_CAPTURE_FILES["portal.bootstrap"]
    path.write_bytes(path.read_bytes() + b"\n")

    with pytest.raises(Exception) as error:
        validator.check_runtime(
            evidence,
            live_m7_inputs(validator, evidence),
            manifests,
            roots,
            require_private=True,
        )
    assert str(error.value) == "provenance.source_capture"


@pytest.mark.parametrize(
    "tool_mutation",
    ["extra_v2", "extra_write", "reordered", "paginated"],
)
def test_msp08_private_runtime_requires_exact_scoped_tool_inventory(
    tmp_path: pathlib.Path, tool_mutation: str
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    path = roots["before"] / validator.SOURCE_CAPTURE_FILES["tools.list"]
    value = json.loads(path.read_bytes())
    tools = value["result"]["tools"]
    if tool_mutation == "extra_v2":
        tools.append(
            {
                "name": "eebus.v2.runtime.status.get",
                "inputSchema": {"type": "object", "properties": {}},
            }
        )
    elif tool_mutation == "extra_write":
        tools.append(
            {
                "name": "eebus.v1.features.write",
                "inputSchema": {"type": "object", "properties": {}},
            }
        )
    elif tool_mutation == "reordered":
        tools[0], tools[1] = tools[1], tools[0]
    else:
        value["result"]["nextCursor"] = "page-with-write-tool"
    path.write_bytes(validator.canonical(value))
    rebind_source_manifest(validator, evidence, "before", manifests, roots)

    with pytest.raises(Exception) as error:
        validator.check_runtime(
            evidence,
            live_m7_inputs(validator, evidence),
            manifests,
            roots,
            require_private=True,
        )
    assert str(error.value) == "provenance.source_capture"


@pytest.mark.parametrize(
    ("input_id", "replacement"),
    [
        ("portal.bootstrap", {"capabilities": {}, "ui_version": "contradiction"}),
        ("ebus.debug", {"runtime_state": "stopped"}),
        ("command.routing", {"fallback": "eebus", "routes": []}),
        ("semantic.registry", {"authority": "eebus", "leaves": []}),
    ],
)
def test_msp08_private_runtime_rejects_direct_view_contradiction(
    tmp_path: pathlib.Path, input_id: str, replacement: dict[str, object]
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    path = roots["before"] / validator.SOURCE_CAPTURE_FILES[input_id]
    path.write_bytes(validator.canonical(replacement))
    rebind_source_manifest(validator, evidence, "before", manifests, roots)

    with pytest.raises(Exception) as error:
        validator.check_runtime(
            evidence,
            live_m7_inputs(validator, evidence),
            manifests,
            roots,
            require_private=True,
        )
    assert str(error.value) == "provenance.source_capture"


@pytest.mark.parametrize("metadata_field", ["captured_at", "auth_subject"])
def test_msp08_private_runtime_binds_complete_payload_metadata(
    tmp_path: pathlib.Path, metadata_field: str
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    view = evidence["runs"][0]["protected_views"][0]
    view["payload"]["meta"][metadata_field] = (
        json.loads(manifests["after"])["captured_at"]
        if metadata_field == "captured_at"
        else "redacted:sha256:ffffffffffff"
    )
    refresh_protected_views(validator, evidence)

    with pytest.raises(Exception) as error:
        validator.check_runtime(
            evidence,
            live_m7_inputs(validator, evidence),
            manifests,
            roots,
            require_private=True,
        )
    assert str(error.value) == "provenance.source_capture"


@pytest.mark.parametrize(
    "malformed",
    [b"{}", b"[]", b'{"data":{},"data":{}}', b'{"value":"\\ud800"}'],
)
def test_msp08_private_runtime_rejects_malformed_source_shape_without_traceback(
    tmp_path: pathlib.Path, malformed: bytes
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    path = roots["before"] / validator.SOURCE_CAPTURE_FILES["graphql.schema"]
    path.write_bytes(malformed)
    rebind_source_manifest(validator, evidence, "before", manifests, roots)

    with pytest.raises(Exception) as error:
        validator.check_runtime(
            evidence,
            live_m7_inputs(validator, evidence),
            manifests,
            roots,
            require_private=True,
        )
    assert str(error.value) == "provenance.source_capture"


def test_msp08_private_runtime_rejects_excessive_source_nesting_by_precedence(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    depth = validator.HARD_LIMITS["max_depth"] + 1
    path = roots["before"] / validator.SOURCE_CAPTURE_FILES["portal.bootstrap"]
    path.write_bytes(("[" * depth + "0" + "]" * depth).encode("ascii"))
    rebind_source_manifest(validator, evidence, "before", manifests, roots)

    with pytest.raises(Exception) as error:
        validator.check_runtime(
            evidence,
            live_m7_inputs(validator, evidence),
            manifests,
            roots,
            require_private=True,
        )
    assert str(error.value) == "limits.exceeded"


def test_msp08_source_reader_rejects_oversize_fifo_and_symlink_without_blocking(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    regular = tmp_path / "regular.json"
    regular.write_bytes(b"{}")
    oversized = tmp_path / "oversized.json"
    with oversized.open("wb") as stream:
        stream.truncate(validator.MAX_SOURCE_INPUT_BYTES + 1)
    fifo = tmp_path / "capture.fifo"
    os.mkfifo(fifo)
    symlink = tmp_path / "capture-link.json"
    symlink.symlink_to(regular)

    for path, expected in (
        (oversized, "limits.exceeded"),
        (fifo, "provenance.source_capture"),
        (symlink, "provenance.source_capture"),
    ):
        started = time.monotonic()
        with pytest.raises(Exception) as error:
            validator._read_bounded_regular_file(
                path,
                validator.MAX_SOURCE_INPUT_BYTES,
                "provenance.source_capture",
                limit_category="limits.exceeded",
            )
        assert str(error.value) == expected
        assert time.monotonic() - started < 1.0


def test_msp08_source_reader_rejects_aggregate_limit(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    root = tmp_path / "source-root"
    root.mkdir()
    raw = b"x" * (validator.MAX_SOURCE_TOTAL_BYTES // len(validator.SOURCE_CAPTURE_FILES) + 1)
    inputs = []
    for input_id, filename in validator.SOURCE_CAPTURE_FILES.items():
        (root / filename).write_bytes(raw)
        inputs.append(
            {
                "input_id": input_id,
                "auth_boundary": validator.SOURCE_CAPTURE_INPUTS[input_id],
                "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "byte_length": len(raw),
            }
        )

    with pytest.raises(Exception) as error:
        validator._read_source_inputs(root, {"inputs": inputs})
    assert str(error.value) == "limits.exceeded"


def test_msp08_private_runtime_rejects_cross_window_device_intersection(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    path = roots["before"] / validator.SOURCE_CAPTURE_FILES["ebus.devices"]
    envelope = json.loads(path.read_bytes())
    inner = json.loads(envelope["result"]["content"][0]["text"])
    inner["data"].append(
        {
            "address": 16,
            "manufacturer": "Vaillant",
            "device_id": "BASV2",
            "discovery_source": "active_confirmed",
            "verification_state": "identity_confirmed",
        }
    )
    envelope["result"]["content"][0]["text"] = validator.canonical(inner).decode(
        "utf-8"
    )
    path.write_bytes(validator.canonical(envelope))
    rebind_source_manifest(validator, evidence, "before", manifests, roots)

    with pytest.raises(Exception) as error:
        validator.check_runtime(
            evidence,
            live_m7_inputs(validator, evidence),
            manifests,
            roots,
            require_private=True,
        )
    assert str(error.value) == "provenance.source_capture"


def test_msp08_private_runtime_rejects_dropped_or_hardcoded_projection(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    view = next(
        item
        for item in evidence["runs"][0]["protected_views"]
        if item["view_id"] == "mcp.ebus.v1.responses"
    )
    view["payload"]["data"]["responses"][0]["result"]["devices"][0].pop(
        "verification_state"
    )
    refresh_protected_views(validator, evidence)

    with pytest.raises(Exception) as error:
        validator.check_runtime(
            evidence,
            live_m7_inputs(validator, evidence),
            manifests,
            roots,
            require_private=True,
        )
    assert str(error.value) == "provenance.source_capture"


def test_msp08_live_profile_rejects_synthetic_build_mode(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    for run in evidence["runs"]:
        runtime = run["provenance"]["runtime"]
        runtime["build_manifest"]["build_mode"] = "SYNTHETIC_FIXTURE"
        runtime["build_manifest_hash"] = validator.digest(
            validator.BUILD_DOMAIN, runtime["build_manifest"]
        )
    refresh_evidence_hash(validator, evidence)
    evidence_path = write_evidence(tmp_path, evidence)
    result = subprocess.run(
        validator_command("verify", evidence_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        1,
        "provenance.runtime\n",
        "",
    )


def test_msp08_live_report_matches_public_schema(tmp_path: pathlib.Path) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    report = validator.report(evidence, load(REGISTRY))
    assert report["evidence_class"] == "CAPTURED_RUNTIME_EVIDENCE"
    assert report["export_tier"] == "PUBLIC_REDACTED"
    report_path = tmp_path / "report.json"
    report_path.write_bytes(validator.canonical(report) + b"\n")
    checked = subprocess.run(
        ["jv", str(REPORT_SCHEMA), str(report_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_msp08_live_report_refuses_public_only_inputs(tmp_path: pathlib.Path) -> None:
    validator = validator_module()
    evidence_path = write_evidence(tmp_path, build_live_evidence(validator))
    result = subprocess.run(
        validator_command("report", evidence_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "provenance.m7\n"


def test_msp08_m7_precedence_runs_before_source_manifest_io(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    evidence["m7_binding"]["graph_hash"] = "sha256:" + "0" * 64
    refresh_evidence_hash(validator, evidence)
    missing = tmp_path / "missing-source-manifest.json"
    result = subprocess.run(
        [
            *validator_command("report", write_evidence(tmp_path, evidence)),
            "--before-source-manifest",
            str(missing),
            "--after-source-manifest",
            str(missing),
            "--before-source-root",
            str(tmp_path),
            "--after-source-root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        1,
        "provenance.m7\n",
        "",
    )


def test_msp08_runtime_precedence_runs_before_source_manifest_io(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    manifests, roots = bind_source_manifests(validator, evidence, tmp_path)
    evidence["runs"][0]["provenance"]["immutable_inputs"][0]["digest"] = (
        "sha256:" + "0" * 64
    )
    missing = tmp_path / "missing-source-manifest.json"
    manifests = {"before": missing, "after": missing}

    with pytest.raises(Exception) as error:
        validator.check_runtime(
            evidence,
            live_m7_inputs(validator, evidence),
            manifests,
            roots,
            require_private=True,
        )
    assert str(error.value) == "provenance.runtime"


@pytest.mark.parametrize("run_count", [1, 2, 3, 5])
def test_msp08_live_cardinality_fails_schema_without_traceback(
    tmp_path: pathlib.Path, run_count: int
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    if run_count < 4:
        evidence["runs"] = evidence["runs"][:run_count]
    else:
        extra = deepcopy(evidence["runs"][-1])
        extra["run_id"] = "msp08-run-extra"
        extra["capture_offset_ns"] += 1_000_000_000
        evidence["runs"].append(extra)
    refresh_evidence_hash(validator, evidence)
    result = subprocess.run(
        validator_command("verify", write_evidence(tmp_path, evidence)),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        1,
        "schema.evidence\n",
        "",
    )
    schema_result = subprocess.run(
        ["jv", str(EVIDENCE_SCHEMA), str(write_evidence(tmp_path, evidence))],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert schema_result.returncode != 0


def test_msp08_live_public_status_projection_is_redacted_and_schema_valid(
    tmp_path: pathlib.Path,
) -> None:
    checked = subprocess.run(
        ["jv", str(M7_STATUS_SCHEMA), str(M7_LIVE_STATUS)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
    status = load(M7_LIVE_STATUS)
    assert status["status_counts"] == {"RAW_ONLY": 14, "WITHHELD": 4}
    assert len(status["facts"]) == 18
    serialized = json.dumps(status, sort_keys=True)
    for forbidden in ("source_address", "target_address", "ship_id", "ski"):
        assert forbidden not in serialized


def status_projector_command(
    *,
    graph: pathlib.Path,
    replay: pathlib.Path,
    source_bundle: pathlib.Path,
    source_replay: pathlib.Path,
    expect: pathlib.Path | None = None,
) -> list[str]:
    command = [
        sys.executable,
        str(STATUS_PROJECTOR),
        "--graph",
        str(graph),
        "--replay",
        str(replay),
        "--registry",
        str(M7_REGISTRY),
        "--source-bundle",
        str(source_bundle),
        "--source-replay",
        str(source_replay),
        "--source-commit",
        M7_GATEWAY_MERGE,
        "--docs-source-commit",
        M7_DOCS_MERGE,
    ]
    if expect is not None:
        command.extend(("--expect", str(expect)))
    return command


def test_msp08_public_status_projector_is_deterministic_and_bound(
    tmp_path: pathlib.Path,
) -> None:
    command = status_projector_command(
        graph=M7_SYNTHETIC_GRAPH,
        replay=M7_SYNTHETIC_REPLAY,
        source_bundle=M7_SYNTHETIC_SOURCE_BUNDLE,
        source_replay=M7_SYNTHETIC_SOURCE_REPLAY,
    )
    first = subprocess.run(command, cwd=REPO_ROOT, capture_output=True)
    second = subprocess.run(command, cwd=REPO_ROOT, capture_output=True)
    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert first.stdout == second.stdout
    projection = json.loads(first.stdout)
    assert projection["fact_count"] == 7
    assert projection["status_counts"] == {"RAW_ONLY": 3, "WITHHELD": 4}
    expected = tmp_path / "expected-status.json"
    expected.write_bytes(first.stdout)

    bound = subprocess.run(
        status_projector_command(
            graph=M7_SYNTHETIC_GRAPH,
            replay=M7_SYNTHETIC_REPLAY,
            source_bundle=M7_SYNTHETIC_SOURCE_BUNDLE,
            source_replay=M7_SYNTHETIC_SOURCE_REPLAY,
            expect=expected,
        ),
        cwd=REPO_ROOT,
        capture_output=True,
    )
    assert bound.returncode == 0, bound.stdout + bound.stderr
    assert bound.stdout == first.stdout

    different_valid_graph = subprocess.run(
        status_projector_command(
            graph=M7_GRAPH,
            replay=M7_REPLAY,
            source_bundle=M7_SOURCE_BUNDLE,
            source_replay=M7_SOURCE_REPLAY,
            expect=expected,
        ),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert different_valid_graph.returncode == 1
    assert different_valid_graph.stdout == "projection.binding\n"


def test_msp08_live_report_reserves_fixture_suffix_space(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    evidence["fixture_id"] = "MSP08-G18-" + "A" * 111
    assert len(evidence["fixture_id"]) == 121
    refresh_evidence_hash(validator, evidence)
    report = validator.report(evidence, load(REGISTRY))
    assert len(report["fixture_id"]) == 128
    report_path = tmp_path / "max-report.json"
    report_path.write_bytes(validator.canonical(report) + b"\n")
    checked = subprocess.run(
        ["jv", str(REPORT_SCHEMA), str(report_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr


def test_msp08_live_rejects_fixture_id_without_report_suffix_space(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    evidence["fixture_id"] = "MSP08-G18-" + "A" * 112
    assert len(evidence["fixture_id"]) == 122
    refresh_evidence_hash(validator, evidence)
    evidence_path = write_evidence(tmp_path, evidence)
    result = subprocess.run(
        validator_command("verify", evidence_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "schema.evidence\n"


@pytest.mark.parametrize(
    "leak",
    [
        "RAW_ONLY",
        "CANDIDATE",
        "CONFLICTED",
        "WITHHELD",
        "CANDIDATE_DEBUG_REPLAY",
        "m7-candidate-1001",
        "m7-candidate-synthetic-0001",
        {"detail": "terminal=BACKEND_UNAVAILABLE"},
        {"source_terminal": {"state": "UNAVAILABLE"}},
        {"error_category": "BACKEND_UNAVAILABLE"},
        {"detail": "UNAVAILABLE"},
        {"detail": "BACKEND_UNAVAILABLE"},
        {"outer": {"detail": "EBUS_B509"}},
        {"m7_candidate_fact": "redacted"},
        {"candidate_refs": ["redacted"]},
        "candidateFacts",
        "candidates",
        "conflicted",
        "withheld",
        {"candidate_count": 1},
        {"candidate_ids": []},
        {"candidate_statuses": []},
        {"fact_hash": "sha256:" + "a" * 64},
        {"evidence_digests": ["sha256:" + "a" * 64]},
        {"evidence_refs": []},
        {"identity_family": "redacted"},
        {"debug_only": True},
        {"proposed_path": "/candidate/private"},
        {"retest_trigger": "private"},
        {"raw_only_count": 14},
        {"raw_only": True},
        {"source_terminals": []},
        {"source_terminal_phase": "redacted"},
        {"terminal_negative_states": []},
        {"m7-candidate-1001": "redacted"},
    ],
)
def test_msp08_live_internal_fact_vocabulary_cannot_leak(
    tmp_path: pathlib.Path, leak: object
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    for run in evidence["runs"]:
        run["protected_views"][0]["payload"]["data"]["internal_leak"] = leak
    refresh_protected_views(validator, evidence)
    evidence_path = write_evidence(tmp_path, evidence)
    result = subprocess.run(
        validator_command("verify", evidence_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "anti_leak.candidate\n"


@pytest.mark.parametrize(
    "leak",
    [
        {"tls_private_key": "-----BEGIN PRIVATE KEY-----"},
        {"ski": "b" * 40},
        {"endpoint": SYNTHETIC_PRIVATE_IPV4 + ":4712"},
        {"device_id": "unredacted-stable-device"},
        {"source_address": 247},
        {"targetAddress": 21},
        {"remoteShipId": "unredacted-ship-peer"},
        {"privateKey": "cHJpdmF0ZS1qd2stbWF0ZXJpYWw="},
        {"encrypted_pem": "-----BEGIN ENCRYPTED PRIVATE KEY-----"},
        {"dsa_pem": "-----BEGIN DSA PRIVATE KEY-----"},
        {"hw_addr": "aa-bb-cc-dd-ee-ff"},
        {"hw_addr": "aabb.ccdd.eeff"},
        {"hw_addr": "aabbccddeeff"},
        {"password_hash": "sha256:" + "a" * 64},
        {"sessionTokenDigest": "sha256:" + "b" * 64},
        {"spineSourceAddress": 247},
        {
            "spine_path": [
                {"kind": "ENTITY", "selector": "private-entity-selector"}
            ]
        },
        {"endpointHash": SYNTHETIC_PRIVATE_IPV4},
        {"endpoint": "fd00::1234"},
        {"endpoint": "fe80::1%eth0"},
        {"api_key": "private-api-key"},
        {"apikey": "private-api-key"},
        {"apiKey": "private-api-key"},
        {"spine_path": "private-spine-path"},
        {"spineKind": "ENTITY"},
        {"spineService": "private-spine-service"},
        {"spineEntity": "private-spine-entity"},
        {"spineFeature": "private-spine-feature"},
        {"eebusService": "private-eebus-service"},
        {"eebusEntity": "private-eebus-entity"},
        {"eebusFeature": "private-eebus-feature"},
        {"feature_path": "private-feature-path"},
        {"debug_detail": "127.0.0.1:4712"},
        {"debug_detail": "169.254.12.34"},
        {"debug_detail": "http://" + SYNTHETIC_PRIVATE_IPV4 + ".:4712"},
        {"debug_detail": "10..8.8.8.8"},
        {"debug_detail": "100.64.0.1"},
        {"debug_detail": "224.0.0.251"},
        {"debug_detail": "239.255.255.250:1900"},
        {"debug_detail": "8.8.8.8."},
        {"debug_detail": "Authorization: Bearer synthetic-credential"},
        {"debug_detail": "Basic dXNlcjpwYXNz"},
        {"debug_detail": "api_key: private-api-key"},
        {"debug_detail": "session_cookie=synthetic-cookie"},
        {"debug_detail": "access_token=synthetic-token"},
        {"debug_detail": "refresh_token=synthetic-token"},
        {"debug_detail": "client_secret=synthetic-secret"},
        {"debug_detail": "csrf_token=synthetic-token"},
        {"debug_detail": "private_key=synthetic-key"},
        {"debug_detail": "ff02::fb"},
        {SYNTHETIC_PRIVATE_IPV4: "redacted"},
        {"selectors": ["private-selector"]},
        {"ship_ids": ["private-ship-id"]},
        {"spine_entities": ["private-spine-entity"]},
        {"spine_services": ["private-spine-service"]},
        {"spine_sources": [247]},
        {"spine_source_hash": "b" * 40},
        {"eebus_devices": ["private-eebus-device"]},
        {"eebus_nodes": ["private-eebus-node"]},
        {"eebus_peers": ["private-eebus-peer"]},
        {"endpoint_ids": ["private-endpoint-id"]},
        {"remote_skis": ["b" * 40]},
        {"serial_numbers": ["private-serial"]},
        {"authorization": "Bearer synthetic-credential"},
        {"authHeader": "Bearer synthetic-credential"},
        {"access_key_id": "SYNTHETICACCESSKEY"},
        {"endpoint_hash": "b" * 40},
        {"session_cookie": "synthetic-cookie"},
        {"tokens": ["synthetic-token"]},
        {"ship_hash": "b" * 40},
        {"spine_hash": "b" * 40},
        {"evidenceDigest": None},
        {"extra": {"key": "selector", "value": "private-selector"}},
        {"extra": {"Key": "selector", "Value": "private-selector"}},
        {"extra": {"name": "selector", "value": "private-selector"}},
        {"device": "private-device-identity"},
        {"device_id": "sha256:" + "a" * 64},
    ],
)
def test_msp08_public_export_rejects_secrets_and_stable_identity(
    tmp_path: pathlib.Path, leak: dict[str, object]
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    for run in evidence["runs"]:
        run["protected_views"][-1]["payload"]["data"]["public_leak"] = leak
    refresh_protected_views(validator, evidence)
    evidence_path = write_evidence(tmp_path, evidence)
    result = subprocess.run(
        validator_command("verify", evidence_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "redaction.public\n"


def test_msp08_public_export_allows_boolean_auth_policy_metadata(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    for run in evidence["runs"]:
        view = next(
            view for view in run["protected_views"] if view["view_id"] == "debug.ebus"
        )
        view["payload"]["data"]["api_key_required"] = False
    refresh_protected_views(validator, evidence)
    evidence_path = write_evidence(tmp_path, evidence)
    result = subprocess.run(
        validator_command("verify", evidence_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "public-only-ok\n"
    assert result.stderr == ""


def test_msp08_public_export_allows_ambiguous_terminal_words_as_metadata(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    for run in evidence["runs"]:
        view = next(
            view for view in run["protected_views"] if view["view_id"] == "debug.ebus"
        )
        data = view["payload"]["data"]
        data["protocol_label"] = "EBUS"
        data["phase"] = "post"
        data["operation"] = "action"
    refresh_protected_views(validator, evidence)
    evidence_path = write_evidence(tmp_path, evidence)
    result = subprocess.run(
        validator_command("verify", evidence_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "public-only-ok\n"
    assert result.stderr == ""


def test_msp08_public_export_rejects_private_metadata_outside_views(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    for run in evidence["runs"]:
        run["provenance"]["config"]["config_id"] = SYNTHETIC_PRIVATE_IPV4
    refresh_evidence_hash(validator, evidence)
    evidence_path = write_evidence(tmp_path, evidence)
    result = subprocess.run(
        validator_command("verify", evidence_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "redaction.public\n"


def test_msp08_live_rejects_synthetic_m7_inputs_with_live_attribution(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence_path = write_evidence(tmp_path, build_live_evidence(validator))
    result = subprocess.run(
        validator_command(
            "verify",
            evidence_path,
            graph=M7_SYNTHETIC_GRAPH,
            replay=M7_SYNTHETIC_REPLAY,
            source_bundle=M7_SYNTHETIC_SOURCE_BUNDLE,
            source_replay=M7_SYNTHETIC_SOURCE_REPLAY,
        ),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "provenance.m7\n"


def test_msp08_live_rejects_graph_enabled_states_without_raw_only_fact() -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    withheld = [
        fact
        for fact in evidence["runs"][1]["state_evidence"]["facts"]
        if fact["status"] == "WITHHELD"
    ]
    for run in evidence["runs"][1:3]:
        state = run["state_evidence"]
        state["facts"] = deepcopy(withheld)
        state["raw_only_count"] = 0
        state["candidate_count"] = 0
        state["conflict_count"] = 0
        state["withheld_count"] = len(withheld)
    with pytest.raises(validator.Failure, match="state.evidence"):
        validator.check_states(evidence, {"facts": withheld})


def test_msp08_live_rejects_restart_without_new_process_instance(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    process_id = evidence["runs"][0]["provenance"]["process_instance_id"]
    for run in evidence["runs"]:
        run["provenance"]["process_instance_id"] = process_id
    transition = evidence["runs"][2]["state_evidence"]["restart_transition"]
    transition["after_process_instance_id"] = process_id
    refresh_evidence_hash(validator, evidence)
    evidence_path = write_evidence(tmp_path, evidence)
    result = subprocess.run(
        validator_command("verify", evidence_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "state.evidence\n"


def test_msp08_live_rejects_restart_event_not_bound_as_immutable_input(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    transition = evidence["runs"][2]["state_evidence"]["restart_transition"]
    transition["process_event"]["event_id"] = "restart-event-redacted-forged"
    transition["event_id"] = "restart-event-redacted-forged"
    refresh_evidence_hash(validator, evidence)
    evidence_path = write_evidence(tmp_path, evidence)
    result = subprocess.run(
        validator_command("verify", evidence_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "provenance.runtime\n"


def test_msp08_live_rejects_relabelled_restart_immutable_input_kind(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
    evidence = build_live_evidence(validator)
    inputs = evidence["runs"][2]["provenance"]["immutable_inputs"]
    restart_input = next(
        item for item in inputs if item["input_id"] == "restart:process-event"
    )
    restart_input["kind"] = "RESTART_SESSION_EVENT"
    refresh_evidence_hash(validator, evidence)
    evidence_path = write_evidence(tmp_path, evidence)
    result = subprocess.run(
        validator_command("verify", evidence_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "provenance.runtime\n"
