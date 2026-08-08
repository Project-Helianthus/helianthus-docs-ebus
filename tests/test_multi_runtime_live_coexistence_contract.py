from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
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
        {"source_terminal": {"state": "UNAVAILABLE"}},
        {"error_category": "BACKEND_UNAVAILABLE"},
        {"detail": "UNAVAILABLE"},
        {"detail": "BACKEND_UNAVAILABLE"},
        {"outer": {"detail": "EBUS_B509"}},
        {"m7_candidate_fact": "redacted"},
        {"candidate_refs": ["redacted"]},
        {"source_terminal_phase": "redacted"},
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
        {SYNTHETIC_PRIVATE_IPV4: "redacted"},
        {"selectors": ["private-selector"]},
        {"ship_ids": ["private-ship-id"]},
        {"spine_entities": ["private-spine-entity"]},
        {"spine_services": ["private-spine-service"]},
        {"endpoint_ids": ["private-endpoint-id"]},
        {"remote_skis": ["b" * 40]},
        {"serial_numbers": ["private-serial"]},
        {"authorization": "Bearer synthetic-credential"},
        {"authHeader": "Bearer synthetic-credential"},
        {"access_key_id": "SYNTHETICACCESSKEY"},
        {"endpoint_hash": "b" * 40},
        {"evidenceDigest": None},
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
