from __future__ import annotations

import json
import importlib.util
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
REGISTRY = (
    REPO_ROOT
    / "docs/platform/schemas/multi-runtime-coexistence-registry-v1.json"
)
VALIDATOR = REPO_ROOT / "scripts/validate_multi_runtime_coexistence.py"
SYNTHETIC_EVIDENCE = (
    REPO_ROOT
    / "docs/platform/fixtures/coexistence-no-drift/v1/positive/evidence.json"
)
M7_ROOT = REPO_ROOT / "docs/platform/fixtures/candidate-fact-graph/v1/positive"
M7_GRAPH = M7_ROOT / "source-terminal-graph.json"
M7_REPLAY = M7_ROOT / "source-terminal-replay-result.json"
M7_SOURCE_BUNDLE = M7_ROOT / "source-terminal-bundle.json"
M7_SOURCE_REPLAY = M7_ROOT / "source-terminal-source-replay.json"
M7_REGISTRY = REPO_ROOT / "docs/platform/schemas/draft-candidate-fact-registry-v1.json"
SYNCHRONIZED_ROOT = REPO_ROOT / "docs/platform/fixtures/synchronized-evidence/v1/positive"
M7_SYNTHETIC_GRAPH = M7_ROOT / "graph.json"
M7_SYNTHETIC_REPLAY = M7_ROOT / "replay-result.json"
M7_SYNTHETIC_SOURCE_BUNDLE = SYNCHRONIZED_ROOT / "bundle.json"
M7_SYNTHETIC_SOURCE_REPLAY = SYNCHRONIZED_ROOT / "replay-result.json"

M7_GATEWAY_MERGE = "8bcba2107d10b149f984ac9546ea6427a9cda8a1"
M7_DOCS_MERGE = "35d2eba256a77b6575a2b45c07e73f054ff74ced"


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

    evidence["fixture_id"] = "MSP08-G18-LIVE-EVIDENCE-TEST001"
    evidence["evidence_class"] = "CAPTURED_RUNTIME_EVIDENCE"
    evidence["scope"]["live_vr940_claim"] = True
    evidence["m7_binding"] = {
        "source_commit": M7_GATEWAY_MERGE,
        "docs_source_commit": M7_DOCS_MERGE,
        **deepcopy(registry["m7_live_binding"]),
    }

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
        for fact in graph["facts"]
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
    continuity_hash = "sha256:" + "c" * 64
    peer_binding_hash = "sha256:" + "d" * 64
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
                    "before_trust_state_hash": continuity_hash,
                    "after_trust_state_hash": continuity_hash,
                    "before_peer_binding_hash": peer_binding_hash,
                    "after_peer_binding_hash": peer_binding_hash,
                    "session_reconnected": True,
                }
                if index == 2
                else None
            ),
        }
        for item in run["provenance"]["immutable_inputs"]:
            if item["input_id"] == "m7:graph":
                item["digest"] = graph["graph_hash"]
                item["byte_length"] = len(validator.canonical(graph))
            elif item["input_id"] == "m7:replay":
                item["digest"] = evidence["m7_binding"]["replay_hash"]
                item["byte_length"] = len(validator.canonical(replay))
            elif item["input_id"] == "m7:registry":
                item["digest"] = evidence["m7_binding"]["registry_content_hash"]
                item["byte_length"] = len(M7_REGISTRY.read_bytes())
            elif item["input_id"] == "m7:source-bundle":
                item["digest"] = evidence["m7_binding"]["source_bundle_content_hash"]
                item["byte_length"] = len(M7_SOURCE_BUNDLE.read_bytes())
            elif item["input_id"] == "m7:source-replay":
                item["digest"] = evidence["m7_binding"]["source_replay_content_hash"]
                item["byte_length"] = len(M7_SOURCE_REPLAY.read_bytes())
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
) -> list[str]:
    return [
        sys.executable,
        str(VALIDATOR),
        command,
        "--evidence",
        str(evidence_path),
        "--registry",
        str(REGISTRY),
        "--m7-graph",
        str(graph),
        "--m7-replay",
        str(replay),
        "--m7-registry",
        str(M7_REGISTRY),
        "--m7-source-bundle",
        str(source_bundle),
        "--m7-source-replay",
        str(source_replay),
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
    assert result.stdout == "ok\n"


def test_msp08_live_report_matches_public_schema(tmp_path: pathlib.Path) -> None:
    validator = validator_module()
    evidence_path = write_evidence(tmp_path, build_live_evidence(validator))
    result = subprocess.run(
        validator_command("report", evidence_path),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["evidence_class"] == "CAPTURED_RUNTIME_EVIDENCE"
    assert report["export_tier"] == "PUBLIC_REDACTED"
    report_path = tmp_path / "report.json"
    report_path.write_text(result.stdout, encoding="utf-8")
    checked = subprocess.run(
        ["jv", str(REPORT_SCHEMA), str(report_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr


@pytest.mark.parametrize(
    "leak",
    [
        "RAW_ONLY",
        "CANDIDATE",
        "CONFLICTED",
        "WITHHELD",
        "CANDIDATE_DEBUG_REPLAY",
        "m7-candidate-1001",
    ],
)
def test_msp08_live_internal_fact_vocabulary_cannot_leak(
    tmp_path: pathlib.Path, leak: str
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
        {"endpoint": "192.168.100.4:4712"},
        {"device_id": "unredacted-stable-device"},
    ],
)
def test_msp08_public_export_rejects_secrets_and_stable_identity(
    tmp_path: pathlib.Path, leak: dict[str, str]
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
