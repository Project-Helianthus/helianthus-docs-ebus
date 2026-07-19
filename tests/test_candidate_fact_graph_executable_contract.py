from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_ROOT = REPO_ROOT / "docs/platform/schemas"
FIXTURE_ROOT = REPO_ROOT / "docs/platform/fixtures/candidate-fact-graph/v1"
VALIDATOR = REPO_ROOT / "scripts/validate_candidate_fact_graph.py"
SCHEMA = SCHEMA_ROOT / "draft-candidate-fact-graph-v1.schema.json"
REPLAY_SCHEMA = SCHEMA_ROOT / "draft-candidate-fact-replay-v1.schema.json"
REGISTRY = SCHEMA_ROOT / "draft-candidate-fact-registry-v1.json"
POSITIVE = FIXTURE_ROOT / "positive/graph.json"
GOLDEN_REPLAY = FIXTURE_ROOT / "positive/replay-result.json"
NEGATIVE_ROOT = FIXTURE_ROOT / "negative"
EXPECTED_NEGATIVE = {
    "anti-leak-stable-surface.json": "anti_leak.consumer",
    "comparator-parameter-invalid.json": "comparator.invalid",
    "evidence-ref-not-in-bundle.json": "provenance.binding",
    "graph-hash-mismatch.json": "hash.graph",
    "incomplete-b524-identity.json": "identity.native",
    "invalid-eebus-feature-path.json": "identity.native",
    "limit-exceeded.json": "limits.exceeded",
    "ordering-invalid.json": "ordering.invalid",
    "registry-mismatch.json": "registry.binding",
    "terminal-state-not-withheld.json": "state.terminal",
    "unknown-field.json": "schema.graph",
}


def load_json(path: pathlib.Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def run_validator(command: str, graph: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            command,
            "--graph",
            str(graph),
            "--registry",
            str(REGISTRY),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONHASHSEED": "random"},
    )


def test_machine_contract_inventory_is_complete() -> None:
    for path in (VALIDATOR, SCHEMA, REPLAY_SCHEMA, REGISTRY, POSITIVE, GOLDEN_REPLAY):
        assert path.is_file(), f"missing executable MSP-07 contract file: {path}"
    assert {path.name for path in NEGATIVE_ROOT.glob("*.json")} == set(
        EXPECTED_NEGATIVE
    )


def test_positive_graph_exercises_closed_status_and_native_identity_vocabulary() -> None:
    graph = load_json(POSITIVE)
    facts = graph["facts"]
    assert {fact["status"] for fact in facts} == {
        "RAW_ONLY",
        "CANDIDATE",
        "CONFLICTED",
        "WITHHELD",
    }
    assert {
        fact["terminal_negative_state"]
        for fact in facts
        if fact["terminal_negative_state"] is not None
    } == {"NO_SIGNAL", "CLOUD_ONLY", "CONFLICT", "NOT_TESTED"}
    families = {
        fact["provenance"]["ebus"]["family"]
        for fact in facts
        if fact["provenance"]["ebus"] is not None
    }
    assert families == {"B509", "B524", "B555"}
    b524 = [
        fact["provenance"]["ebus"]
        for fact in facts
        if fact["provenance"]["ebus"] is not None
        and fact["provenance"]["ebus"]["family"] == "B524"
    ]
    assert {identity["opcode"] for identity in b524} >= {2, 6}
    for fact in facts:
        eebus = fact["provenance"]["eebus"]
        if eebus is not None:
            assert [segment["kind"] for segment in eebus["feature_path"][:3]] == [
                "SERVICE",
                "ENTITY",
                "FEATURE",
            ]


def test_positive_graph_and_replay_are_schema_valid() -> None:
    for schema, fixture in ((SCHEMA, POSITIVE), (REPLAY_SCHEMA, GOLDEN_REPLAY)):
        assert schema.is_file(), f"missing MSP-07 schema: {schema}"
        assert fixture.is_file(), f"missing MSP-07 fixture: {fixture}"
        result = subprocess.run(
            ["jv", str(schema), str(fixture)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_positive_graph_replays_to_exact_golden_bytes() -> None:
    first = run_validator("replay", POSITIVE)
    second = run_validator("replay", POSITIVE)
    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    golden = GOLDEN_REPLAY.read_text(encoding="utf-8")
    assert first.stdout == golden
    assert second.stdout == golden
    assert first.stderr == ""
    assert second.stderr == ""


@pytest.mark.parametrize(
    "name,category", sorted(EXPECTED_NEGATIVE.items()), ids=sorted(EXPECTED_NEGATIVE)
)
def test_negative_graphs_fail_with_one_precedence_category(
    name: str, category: str
) -> None:
    result = run_validator("verify", NEGATIVE_ROOT / name)
    assert result.returncode == 1
    assert result.stdout == f"{category}\n"
    assert result.stderr == ""


def test_validator_is_offline_and_deterministic_under_host_variation(
    tmp_path: pathlib.Path,
) -> None:
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(tmp_path / "unavailable-home"),
        "LANG": "invalid_LOCALE",
        "LC_ALL": "C",
        "TZ": "Pacific/Kiritimati",
        "PYTHONHASHSEED": "12345",
    }
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "replay",
            "--graph",
            str(POSITIVE),
            "--registry",
            str(REGISTRY),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == GOLDEN_REPLAY.read_text(encoding="utf-8")
    assert result.stderr == ""


def test_graph_declares_bounded_limits_and_candidate_only_visibility() -> None:
    graph = load_json(POSITIVE)
    assert graph["visibility"] == {
        "channel": "CANDIDATE_DEBUG_REPLAY",
        "promotion_state": "NOT_PROMOTED",
        "stable_exposure": False,
        "command_capable": False,
        "protocol_translation": False,
    }
    assert graph["limits"] == {
        "max_graph_bytes": 1048576,
        "max_depth": 32,
        "max_facts": 64,
        "max_evidence_refs_per_fact": 16,
        "max_samples_per_comparator": 1024,
        "max_string_bytes": 4096,
        "max_path_segments": 32,
    }
