from __future__ import annotations

import json
import importlib.util
import pathlib
import subprocess
import sys
from copy import deepcopy


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = REPO_ROOT / "docs/platform/multi-runtime-coexistence-no-drift-v1.md"
EVIDENCE_SCHEMA = (
    REPO_ROOT
    / "docs/platform/schemas/multi-runtime-coexistence-evidence-v1.schema.json"
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


def test_msp08_live_profile_validates_dynamic_m7_and_regenerated_replay(
    tmp_path: pathlib.Path,
) -> None:
    validator = validator_module()
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
        "graph_contract": graph["contract"],
        "graph_id": graph["graph_id"],
        "graph_hash": graph["graph_hash"],
        "replay_contract": replay["contract"],
        "replay_id": replay["replay_id"],
        "replay_hash": replay["replay_hash"],
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
    for index, run in enumerate(selected):
        run["run_id"] = f"msp08-run-{index + 1:02d}"
        run["state"] = states[index]
        run["capture_offset_ns"] = index * 1_000_000_000
        run["provenance"]["runtime"] = deepcopy(runtime)
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
        }
        for item in run["provenance"]["immutable_inputs"]:
            if item["input_id"] == "m7:graph":
                item["digest"] = graph["graph_hash"]
                item["byte_length"] = len(validator.canonical(graph))
            elif item["input_id"] == "m7:replay":
                item["digest"] = replay["replay_hash"]
                item["byte_length"] = len(validator.canonical(replay))
    evidence["runs"] = selected
    evidence_view = {
        key: value
        for key, value in evidence.items()
        if key not in {"evidence_id", "evidence_hash"}
    }
    evidence_hash = validator.digest(validator.EVIDENCE_DOMAIN, evidence_view)
    evidence["evidence_hash"] = evidence_hash
    evidence["evidence_id"] = "mrcv1:" + evidence_hash

    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    command = [
        sys.executable,
        str(VALIDATOR),
        "verify",
        "--evidence",
        str(evidence_path),
        "--registry",
        str(REGISTRY),
        "--m7-graph",
        str(M7_GRAPH),
        "--m7-replay",
        str(M7_REPLAY),
        "--m7-registry",
        str(M7_REGISTRY),
        "--m7-source-bundle",
        str(M7_SOURCE_BUNDLE),
        "--m7-source-replay",
        str(M7_SOURCE_REPLAY),
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "ok\n"
