from __future__ import annotations

import hashlib
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
SOURCE_BUNDLE = (
    REPO_ROOT / "docs/platform/fixtures/synchronized-evidence/v1/positive/bundle.json"
)
SOURCE_REPLAY = (
    REPO_ROOT
    / "docs/platform/fixtures/synchronized-evidence/v1/positive/replay-result.json"
)
EXPECTED_NEGATIVE = {
    "anti-leak-stable-surface.json": "anti_leak.consumer",
    "comparator-parameter-invalid.json": "comparator.invalid",
    "evidence-ref-not-in-bundle.json": "provenance.binding",
    "forged-artifact-id.json": "provenance.binding",
    "forged-b524-opcode.json": "identity.native",
    "forged-eebus-entity-feature.json": "identity.native",
    "forged-source-id.json": "provenance.binding",
    "graph-hash-mismatch.json": "hash.graph",
    "incomplete-b524-identity.json": "identity.native",
    "invalid-eebus-feature-path.json": "identity.native",
    "limit-exceeded.json": "limits.exceeded",
    "ordering-invalid.json": "ordering.invalid",
    "registry-mismatch.json": "registry.binding",
    "terminal-state-not-withheld.json": "state.terminal",
    "unknown-field.json": "schema.graph",
    "wrong-source-bundle.json": "provenance.binding",
    "wrong-source-replay.json": "provenance.binding",
}


def load_json(path: pathlib.Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def run_validator(
    command: str,
    graph: pathlib.Path,
    source_bundle: pathlib.Path = SOURCE_BUNDLE,
    source_replay: pathlib.Path = SOURCE_REPLAY,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            command,
            "--graph",
            str(graph),
            "--registry",
            str(REGISTRY),
            "--source-bundle",
            str(source_bundle),
            "--source-replay",
            str(source_replay),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONHASHSEED": "random"},
    )


def test_machine_contract_inventory_is_complete() -> None:
    for path in (
        VALIDATOR,
        SCHEMA,
        REPLAY_SCHEMA,
        REGISTRY,
        POSITIVE,
        GOLDEN_REPLAY,
        SOURCE_BUNDLE,
        SOURCE_REPLAY,
    ):
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
    assert {identity["opcode"] for identity in b524} == {2}
    for fact in facts:
        eebus = fact["provenance"]["eebus"]
        if eebus is not None:
            assert [segment["kind"] for segment in eebus["feature_path"][:3]] == [
                "SERVICE",
                "ENTITY",
                "FEATURE",
            ]


def test_positive_provenance_ids_and_identities_bind_to_verified_source() -> None:
    graph = load_json(POSITIVE)
    source = load_json(SOURCE_BUNDLE)
    artifacts = {
        (artifact["source_id"], artifact["artifact_id"]): artifact
        for artifact in source["artifacts"]
    }
    for fact in graph["facts"]:
        provenance = fact["provenance"]
        if provenance["ebus"] is not None:
            artifact = artifacts[
                (provenance["ebus_source_id"], provenance["ebus_artifact_id"])
            ]
            assert provenance["ebus"] == artifact["ebus_identity"]
        if provenance["eebus"] is not None:
            artifact = artifacts[
                (provenance["eebus_source_id"], provenance["eebus_artifact_id"])
            ]
            service_ids = {
                row["id"]["digest"]
                for row in artifact["normalized_evidence"]["data"]["services"]
            }
            assert provenance["eebus"]["service"] in service_ids
        if provenance["cloud"] is not None:
            assert (
                provenance["cloud"]["source_id"],
                provenance["cloud"]["artifact_id"],
            ) in artifacts


def test_source_replay_digest_is_domain_separated_jcs_not_file_bytes() -> None:
    graph = load_json(POSITIVE)
    source_replay = load_json(SOURCE_REPLAY)
    canonical = json.dumps(
        source_replay,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    expected = "sha256:" + hashlib.sha256(
        b"HELIANTHUS:SYNCHRONIZED-EVIDENCE-REPLAY:V1\0" + canonical
    ).hexdigest()
    assert graph["source_bundle"]["replay_hash"] == expected
    assert expected != "sha256:" + hashlib.sha256(SOURCE_REPLAY.read_bytes()).hexdigest()


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
            "--source-bundle",
            str(SOURCE_BUNDLE),
            "--source-replay",
            str(SOURCE_REPLAY),
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


@pytest.mark.parametrize("input_kind", ("bundle", "replay"))
def test_wrong_supplied_source_inputs_are_rejected(
    tmp_path: pathlib.Path, input_kind: str
) -> None:
    source_bundle = SOURCE_BUNDLE
    source_replay = SOURCE_REPLAY
    if input_kind == "bundle":
        value = load_json(SOURCE_BUNDLE)
        value["bundle_hash"] = "sha256:" + "f" * 64
        source_bundle = tmp_path / "wrong-bundle.json"
        source_bundle.write_text(json.dumps(value), encoding="utf-8")
    else:
        value = load_json(SOURCE_REPLAY)
        value["bundle_id"] = "sebv1:sha256:" + "f" * 64
        source_replay = tmp_path / "wrong-replay.json"
        source_replay.write_text(json.dumps(value), encoding="utf-8")
    result = run_validator("verify", POSITIVE, source_bundle, source_replay)
    assert result.returncode == 1
    assert result.stdout == "provenance.binding\n"
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
