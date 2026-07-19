from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from copy import deepcopy

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
    "incomplete-b524-identity.json": "schema.graph",
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


def load_validator_module():
    spec = importlib.util.spec_from_file_location("candidate_fact_validator", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: pathlib.Path, value: object) -> pathlib.Path:
    path.write_text(json.dumps(value, separators=(",", ":")), encoding="utf-8")
    return path


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
    assert {fact["status"] for fact in facts} == {"RAW_ONLY", "WITHHELD"}
    assert {
        fact["terminal_negative_state"]
        for fact in facts
        if fact["terminal_negative_state"] is not None
    } == {"NO_SIGNAL", "CLOUD_ONLY", "NOT_TESTED"}
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
        assert fact["provenance"]["eebus"] is None
        assert fact["comparator"]["samples"] == []
        assert fact["comparator"]["outcome"] == "NOT_EVALUATED"


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
        if provenance["eebus_source_id"] is not None:
            artifact = artifacts[
                (provenance["eebus_source_id"], provenance["eebus_artifact_id"])
            ]
            service_ids = {
                row["id"]["digest"]
                for row in artifact["normalized_evidence"]["data"]["services"]
            }
            assert provenance["eebus_service"] in service_ids
            if provenance["eebus"] is not None:
                assert provenance["eebus"]["service"] == provenance["eebus_service"]
        if provenance["cloud"] is not None:
            assert (
                provenance["cloud"]["source_id"],
                provenance["cloud"]["artifact_id"],
            ) in artifacts
            cloud_artifact = artifacts[
                (provenance["cloud"]["source_id"], provenance["cloud"]["artifact_id"])
            ]
            digest = cloud_artifact["evidence_refs"][0]["digest"].removeprefix(
                "sha256:"
            )
            assert provenance["cloud"]["evidence_id"] == f"public-evidence:sha256:{digest}"


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
    tmp_path: pathlib.Path, name: str, category: str
) -> None:
    fixture = load_json(NEGATIVE_ROOT / name)
    assert fixture["contract"] == (
        "helianthus.platform.draft-candidate-fact-negative-fixture.v1"
    )
    graph = deepcopy(load_json(POSITIVE))
    mutation = fixture["mutation"]
    if mutation == "ANTI_LEAK_STABLE_SURFACE":
        graph["visibility"]["stable_exposure"] = True
    elif mutation == "COMPARATOR_PARAMETER_INVALID":
        graph["comparator_drafts"][0]["parameters"]["window"][
            "start_offset_ns"
        ] = graph["comparator_drafts"][0]["parameters"]["window"]["end_offset_ns"]
    elif mutation == "EVIDENCE_REF_NOT_IN_BUNDLE":
        graph["facts"][0]["provenance"]["native_evidence_refs"][0]["digest"] = (
            "sha256:" + "f" * 64
        )
    elif mutation == "GRAPH_HASH_MISMATCH":
        graph["graph_hash"] = "sha256:" + "0" * 64
    elif mutation == "FORGED_ARTIFACT_ID":
        graph["facts"][0]["provenance"]["cloud"]["artifact_id"] = (
            "seav1:sha256:" + "f" * 64
        )
    elif mutation == "FORGED_SOURCE_ID":
        graph["facts"][0]["provenance"]["cloud"]["source_id"] = (
            "cloud-" + "f" * 32
        )
    elif mutation in {"FORGED_B524_OPCODE", "INCOMPLETE_B524_IDENTITY"}:
        target = next(
            fact
            for fact in graph["facts"]
            if fact["provenance"]["ebus"]
            and fact["provenance"]["ebus"]["family"] == "B524"
        )
        if mutation == "FORGED_B524_OPCODE":
            target["provenance"]["ebus"]["opcode"] = 6
        else:
            del target["provenance"]["ebus"]["RR"]
    elif mutation in {"INVALID_EEBUS_FEATURE_PATH", "FORGED_EEBUS_ENTITY_FEATURE"}:
        target = next(
            fact for fact in graph["facts"] if fact["provenance"]["eebus_service"]
        )
        target["provenance"]["eebus"] = {
            "service": target["provenance"]["eebus_service"],
            "entity": "entity-" + "e" * 32,
            "feature": "feature-" + "f" * 32,
            "feature_path": [
                {
                    "kind": "SERVICE",
                    "selector": target["provenance"]["eebus_service"],
                },
                {"kind": "ENTITY", "selector": "entity-" + "e" * 32},
                {"kind": "FEATURE", "selector": "feature-" + "f" * 32},
            ],
        }
        if mutation == "INVALID_EEBUS_FEATURE_PATH":
            target["provenance"]["eebus"]["feature_path"][0]["kind"] = "FEATURE"
    elif mutation == "LIMIT_EXCEEDED":
        graph["limits"]["max_facts"] = 65
    elif mutation == "ORDERING_INVALID":
        graph["facts"].reverse()
    elif mutation == "REGISTRY_MISMATCH":
        graph["registry"]["digest"] = "sha256:" + "0" * 64
    elif mutation == "WRONG_SOURCE_BUNDLE":
        graph["source_bundle"]["bundle_hash"] = "sha256:" + "f" * 64
    elif mutation == "WRONG_SOURCE_REPLAY":
        graph["source_bundle"]["replay_hash"] = "sha256:" + "f" * 64
    elif mutation == "TERMINAL_STATE_NOT_WITHHELD":
        target = next(fact for fact in graph["facts"] if fact["provenance"]["cloud"])
        target["status"] = "RAW_ONLY"
        target["terminal_negative_state"] = None
    elif mutation == "UNKNOWN_FIELD":
        graph["unknown"] = True
    else:
        raise AssertionError(f"unhandled test-only mutation: {mutation}")
    result = run_validator("verify", write_json(tmp_path / name, graph))
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
        "max_total_members": 16384,
        "max_total_list_items": 8192,
    }


def test_production_validator_has_no_negative_fixture_command_language() -> None:
    source = VALIDATOR.read_text(encoding="utf-8")
    assert "NEGATIVE_FIXTURE_CONTRACT" not in source
    assert "expand_negative_fixture" not in source
    assert "COMPARATOR_PARAMETER_INVALID" not in source


def _evidence_ref(digit: str) -> dict[str, object]:
    return {
        "kind": "CONTENT",
        "digest_algorithm": "SHA256_CONTENT_BYTES",
        "digest": "sha256:" + digit * 64,
        "repository": None,
        "commit": None,
        "path": None,
    }


def _artifact(
    kind: str,
    suffix: str,
    digit: str,
    value: str | None,
    unit: str | None,
    offset_ns: int = 2_000_000_000,
) -> dict[str, object]:
    return {
        "source_kind": kind,
        "source_id": f"{kind.lower()}-{suffix * 32}",
        "artifact_id": f"seav1:sha256:{digit * 64}",
        "recorder_ingested_offset_ns": offset_ns,
        "evidence_refs": [_evidence_ref(digit)],
        "normalized_evidence": {"observation": {"value": value, "unit": unit}},
    }


def _side(artifact: dict[str, object]) -> dict[str, object]:
    return {
        "source_kind": artifact["source_kind"],
        "source_id": artifact["source_id"],
        "artifact_id": artifact["artifact_id"],
        "evidence_ref": deepcopy(artifact["evidence_refs"][0]),
        "observed_offset_ns": artifact["recorder_ingested_offset_ns"],
        "value_pointer": "/observation/value",
        "unit_pointer": "/observation/unit",
        "native_decimal": artifact["normalized_evidence"]["observation"]["value"],
        "native_unit": artifact["normalized_evidence"]["observation"]["unit"],
    }


def _parameters() -> dict[str, object]:
    return deepcopy(load_json(POSITIVE)["comparator_drafts"][0]["parameters"])


def _sample(
    left: dict[str, object],
    right: dict[str, object],
    *,
    offset_ns: int = 4_000_000_000,
    state: str = "PRESENT",
) -> dict[str, object]:
    return {
        "offset_ns": offset_ns,
        "left": _side(left),
        "right": _side(right),
        "state": state,
    }


def _evaluate(
    parameters: dict[str, object],
    samples: list[dict[str, object]],
    artifacts: list[dict[str, object]],
) -> str:
    module = load_validator_module()
    index = {
        (artifact["source_id"], artifact["artifact_id"]): artifact
        for artifact in artifacts
    }
    return module._evaluate_numeric_window(parameters, samples, index)


def _comparison_vector(
    *,
    status: str,
    terminal: str | None,
    outcome: str,
    left_value: str | None,
    right_value: str | None,
    sample_state: str,
    sample_count: int,
    draft_value: str | None = None,
    draft_unit: str | None = None,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    graph = deepcopy(load_json(POSITIVE))
    left = _artifact("EBUS", "a", "1", left_value, "degC" if left_value else None)
    right = _artifact("EEBUS", "b", "2", right_value, "degC" if right_value else None)
    target = graph["facts"][0]
    target["status"] = status
    target["terminal_negative_state"] = terminal
    target["draft_value"] = draft_value
    target["draft_unit"] = draft_unit
    target["provenance"]["native_evidence_refs"] = [
        deepcopy(left["evidence_refs"][0]),
        deepcopy(right["evidence_refs"][0]),
    ]
    target["provenance"]["ebus_source_id"] = left["source_id"]
    target["provenance"]["ebus_artifact_id"] = left["artifact_id"]
    target["provenance"]["eebus_source_id"] = right["source_id"]
    target["provenance"]["eebus_artifact_id"] = right["artifact_id"]
    target["comparator"] = {
        "draft_id": "NUMERIC_WINDOW_V1_DRAFT",
        "samples": [
            _sample(
                left,
                right,
                offset_ns=3_000_000_000 + index,
                state=sample_state,
            )
            for index in range(sample_count)
        ],
        "outcome": outcome,
    }
    source = {"artifacts": [left, right]}
    return graph, target, source


def _validate_comparison_vector(
    module, graph: dict[str, object], target: dict[str, object], source: dict[str, object]
) -> None:
    registry = load_json(REGISTRY)
    artifacts = {
        (artifact["source_id"], artifact["artifact_id"]): artifact
        for artifact in source["artifacts"]
    }
    module._check_sample_provenance(target, artifacts)
    module.check_states(graph, registry)
    module.check_comparators(graph, registry, source)


@pytest.mark.parametrize(
    (
        "status",
        "terminal",
        "outcome",
        "left_value",
        "right_value",
        "sample_state",
        "sample_count",
        "draft_value",
        "draft_unit",
    ),
    (
        ("CANDIDATE", None, "MATCH", "10", "10", "PRESENT", 2, "10.0", "degC"),
        ("CONFLICTED", None, "MISMATCH", "10", "10.5", "PRESENT", 2, None, None),
        ("CONFLICTED", None, "CONFLICT", "10", "11", "PRESENT", 2, None, None),
        ("WITHHELD", "CONFLICT", "CONFLICT", "10", "11", "PRESENT", 2, None, None),
        (
            "WITHHELD",
            "NOT_TESTED",
            "INDETERMINATE",
            None,
            "10",
            "MISSING",
            2,
            None,
            None,
        ),
        ("WITHHELD", "NOT_TESTED", "NOT_EVALUATED", "10", "10", "PRESENT", 0, None, None),
    ),
)
def test_integrated_fully_bound_vectors_accept_exact_outcome_state_matrix(
    status: str,
    terminal: str | None,
    outcome: str,
    left_value: str | None,
    right_value: str | None,
    sample_state: str,
    sample_count: int,
    draft_value: str | None,
    draft_unit: str | None,
) -> None:
    module = load_validator_module()
    graph, target, source = _comparison_vector(
        status=status,
        terminal=terminal,
        outcome=outcome,
        left_value=left_value,
        right_value=right_value,
        sample_state=sample_state,
        sample_count=sample_count,
        draft_value=draft_value,
        draft_unit=draft_unit,
    )
    _validate_comparison_vector(module, graph, target, source)


@pytest.mark.parametrize(
    ("status", "terminal", "outcome", "left_value", "right_value", "state"),
    (
        ("WITHHELD", "CONFLICT", "MISMATCH", "10", "10.5", "PRESENT"),
        ("CONFLICTED", None, "INDETERMINATE", None, "10", "MISSING"),
    ),
)
def test_swapped_sampled_outcome_mappings_are_rejected(
    status: str,
    terminal: str | None,
    outcome: str,
    left_value: str | None,
    right_value: str | None,
    state: str,
) -> None:
    module = load_validator_module()
    graph, target, source = _comparison_vector(
        status=status,
        terminal=terminal,
        outcome=outcome,
        left_value=left_value,
        right_value=right_value,
        sample_state=state,
        sample_count=2,
    )
    with pytest.raises(module.Failure):
        _validate_comparison_vector(module, graph, target, source)


def test_sampled_outcomes_reject_empty_samples_and_non_null_draft() -> None:
    module = load_validator_module()
    empty_graph, empty_target, empty_source = _comparison_vector(
        status="CONFLICTED",
        terminal=None,
        outcome="MISMATCH",
        left_value="10",
        right_value="10.5",
        sample_state="PRESENT",
        sample_count=0,
    )
    with pytest.raises(module.Failure):
        _validate_comparison_vector(module, empty_graph, empty_target, empty_source)

    draft_graph, draft_target, draft_source = _comparison_vector(
        status="CONFLICTED",
        terminal=None,
        outcome="MISMATCH",
        left_value="10",
        right_value="10.5",
        sample_state="PRESENT",
        sample_count=2,
        draft_value="10.5",
        draft_unit="degC",
    )
    with pytest.raises(module.Failure):
        _validate_comparison_vector(module, draft_graph, draft_target, draft_source)


def test_sampled_outcome_rejects_incomplete_direct_provenance() -> None:
    module = load_validator_module()
    graph, target, source = _comparison_vector(
        status="CONFLICTED",
        terminal=None,
        outcome="MISMATCH",
        left_value="10",
        right_value="10.5",
        sample_state="PRESENT",
        sample_count=2,
    )
    target["provenance"]["native_evidence_refs"].pop()
    with pytest.raises(module.Failure) as error:
        _validate_comparison_vector(module, graph, target, source)
    assert str(error.value) == "provenance.binding"


def test_evaluator_uses_exact_absolute_plus_relative_tolerance_boundary() -> None:
    left = _artifact("EBUS", "a", "1", "10", "degC")
    right = _artifact("EEBUS", "b", "2", "10.3", "degC")
    parameters = _parameters()
    parameters["minimum_samples"] = 1
    parameters["tolerance"] = {"absolute_decimal": "0.197", "relative_ppm": 10000}
    parameters["conflict_threshold"] = {
        "absolute_decimal": "10",
        "consecutive_samples": 2,
    }
    assert _evaluate(parameters, [_sample(left, right)], [left, right]) == "MATCH"


def test_evaluator_applies_affine_conversion_then_half_even_rounding() -> None:
    left = _artifact("EBUS", "a", "1", "2.25", "source")
    right = _artifact("EEBUS", "b", "2", "5.4", "target")
    parameters = _parameters()
    parameters["minimum_samples"] = 1
    parameters["tolerance"] = {"absolute_decimal": "0", "relative_ppm": 0}
    parameters["unit_conversion"] = {
        "mode": "AFFINE",
        "source_unit": "source",
        "target_unit": "target",
        "scale_decimal": "2",
        "offset_decimal": "0.9",
    }
    parameters["rounding"] = {"mode": "HALF_EVEN", "decimal_places": 0}
    assert _evaluate(parameters, [_sample(left, right)], [left, right]) == "MATCH"


def test_evaluator_conflict_threshold_is_inclusive_and_consecutive() -> None:
    left = _artifact("EBUS", "a", "1", "10", "degC", offset_ns=3_000_000_000)
    right = _artifact("EEBUS", "b", "2", "11", "degC", offset_ns=3_000_000_000)
    parameters = _parameters()
    parameters["minimum_samples"] = 2
    parameters["conflict_threshold"] = {
        "absolute_decimal": "1",
        "consecutive_samples": 2,
    }
    samples = [
        _sample(left, right, offset_ns=4_000_000_000),
        _sample(left, right, offset_ns=5_000_000_000),
    ]
    assert _evaluate(parameters, samples, [left, right]) == "CONFLICT"


def test_evaluator_stale_cutoff_boundary_and_missing_budget() -> None:
    left = _artifact("EBUS", "a", "1", "10", "degC")
    right = _artifact("EEBUS", "b", "2", "10", "degC")
    parameters = _parameters()
    parameters["minimum_samples"] = 1
    parameters["maximum_missing_samples"] = 0
    parameters["stale_cutoff_ns"] = 2_000_000_000
    at_cutoff = _sample(left, right, offset_ns=4_000_000_000)
    assert _evaluate(parameters, [at_cutoff], [left, right]) == "MATCH"
    past_cutoff = _sample(
        left,
        right,
        offset_ns=4_000_000_001,
        state="STALE",
    )
    assert _evaluate(parameters, [past_cutoff], [left, right]) == "INDETERMINATE"


def test_evaluator_derives_missing_and_excludes_it_from_minimum_samples() -> None:
    left = _artifact("EBUS", "a", "1", None, None)
    right = _artifact("EEBUS", "b", "2", "10", "degC")
    parameters = _parameters()
    parameters["minimum_samples"] = 1
    parameters["maximum_missing_samples"] = 1
    missing = _sample(left, right, state="MISSING")
    assert _evaluate(parameters, [missing], [left, right]) == "INDETERMINATE"


def test_evaluator_resets_conflict_run_on_below_threshold_sample() -> None:
    left = _artifact(
        "EBUS", "a", "1", "10", "degC", offset_ns=4_000_000_000
    )
    right_conflict = _artifact(
        "EEBUS", "b", "2", "11", "degC", offset_ns=4_000_000_000
    )
    right_match = _artifact(
        "EEBUS", "c", "3", "10", "degC", offset_ns=4_000_000_000
    )
    parameters = _parameters()
    parameters["minimum_samples"] = 3
    parameters["conflict_threshold"] = {
        "absolute_decimal": "1",
        "consecutive_samples": 2,
    }
    samples = [
        _sample(left, right_conflict, offset_ns=4_000_000_000),
        _sample(left, right_match, offset_ns=5_000_000_000),
        _sample(left, right_conflict, offset_ns=6_000_000_000),
    ]
    assert (
        _evaluate(parameters, samples, [left, right_conflict, right_match])
        == "MISMATCH"
    )


def test_evaluator_rejects_forged_native_value_and_artifact_ref() -> None:
    module = load_validator_module()
    left = _artifact("EBUS", "a", "1", "10", "degC")
    right = _artifact("EEBUS", "b", "2", "10", "degC")
    index = {
        (artifact["source_id"], artifact["artifact_id"]): artifact
        for artifact in (left, right)
    }
    forged_value = _sample(left, right)
    forged_value["right"]["native_decimal"] = "99"
    with pytest.raises(module.Failure):
        module._evaluate_numeric_window(_parameters(), [forged_value], index)
    forged_ref = _sample(left, right)
    forged_ref["left"]["evidence_ref"]["digest"] = "sha256:" + "f" * 64
    with pytest.raises(module.Failure):
        module._evaluate_numeric_window(_parameters(), [forged_ref], index)


def test_sample_provenance_uses_exact_fact_selected_artifacts() -> None:
    module = load_validator_module()
    left = _artifact("EBUS", "a", "1", "10", "degC")
    other_left = _artifact("EBUS", "c", "3", "10", "degC")
    right = _artifact("EEBUS", "b", "2", "10", "degC")
    sample = _sample(left, right)
    fact = deepcopy(load_json(POSITIVE)["facts"][0])
    fact["provenance"]["ebus_source_id"] = left["source_id"]
    fact["provenance"]["ebus_artifact_id"] = left["artifact_id"]
    fact["provenance"]["eebus_source_id"] = right["source_id"]
    fact["provenance"]["eebus_artifact_id"] = right["artifact_id"]
    fact["provenance"]["native_evidence_refs"] = [
        deepcopy(left["evidence_refs"][0]),
        deepcopy(right["evidence_refs"][0]),
    ]
    fact["comparator"]["samples"] = [sample]
    index = {
        (artifact["source_id"], artifact["artifact_id"]): artifact
        for artifact in (left, other_left, right)
    }
    module._check_sample_provenance(fact, index)
    forged = deepcopy(sample)
    forged["left"] = _side(other_left)
    fact["provenance"]["native_evidence_refs"].append(
        deepcopy(other_left["evidence_refs"][0])
    )
    fact["comparator"]["samples"] = [forged]
    with pytest.raises(module.Failure) as error:
        module._check_sample_provenance(fact, index)
    assert str(error.value) == "provenance.binding"


def test_evaluator_rejects_caller_state_and_duplicate_canonical_samples() -> None:
    module = load_validator_module()
    left = _artifact("EBUS", "a", "1", "10", "degC")
    right = _artifact("EEBUS", "b", "2", "10", "degC")
    index = {
        (artifact["source_id"], artifact["artifact_id"]): artifact
        for artifact in (left, right)
    }
    forged = _sample(left, right, offset_ns=4_000_000_001, state="PRESENT")
    with pytest.raises(module.Failure):
        module._evaluate_numeric_window(_parameters(), [forged], index)
    duplicate = _sample(left, right)
    with pytest.raises(module.Failure):
        module._evaluate_numeric_window(
            _parameters(), [duplicate, deepcopy(duplicate)], index
        )


def test_stored_comparator_outcome_must_equal_recomputed_result() -> None:
    module = load_validator_module()
    graph = deepcopy(load_json(POSITIVE))
    registry = load_json(REGISTRY)
    left = _artifact("EBUS", "a", "1", "10", "degC")
    right = _artifact("EEBUS", "b", "2", "10", "degC")
    target = graph["facts"][0]
    target["status"] = "CANDIDATE"
    target["terminal_negative_state"] = None
    target["draft_value"] = "10"
    target["draft_unit"] = "degC"
    target["comparator"] = {
        "draft_id": "NUMERIC_WINDOW_V1_DRAFT",
        "samples": [
            _sample(left, right, offset_ns=3_000_000_000),
            _sample(left, right, offset_ns=4_000_000_000),
        ],
        "outcome": "MISMATCH",
    }
    target["provenance"]["native_evidence_refs"] = [
        deepcopy(left["evidence_refs"][0]),
        deepcopy(right["evidence_refs"][0]),
    ]
    target["provenance"]["ebus_source_id"] = left["source_id"]
    target["provenance"]["ebus_artifact_id"] = left["artifact_id"]
    target["provenance"]["eebus_source_id"] = right["source_id"]
    target["provenance"]["eebus_artifact_id"] = right["artifact_id"]
    with pytest.raises(module.Failure):
        module.check_comparators(graph, registry, {"artifacts": [left, right]})
    target["comparator"]["outcome"] = "MATCH"
    target["draft_value"] = "99.0"
    with pytest.raises(module.Failure):
        module.check_comparators(graph, registry, {"artifacts": [left, right]})
    target["draft_value"] = "10.0"
    module.check_comparators(graph, registry, {"artifacts": [left, right]})


@pytest.mark.parametrize(
    "mutation",
    (
        lambda graph: graph["facts"][0]["confidence"].__setitem__("score_milli", True),
        lambda graph: graph["facts"][0].__setitem__("draft_unit", "x" * 257),
        lambda graph: graph["facts"][0].__setitem__("draft_unit", "degr\N{DEGREE SIGN}"),
        lambda graph: graph["facts"][0].__setitem__("proposed_path", "/" + "a" * 512),
        lambda graph: graph["facts"][0]["confidence"].__setitem__("level", "CERTAIN"),
        lambda graph: graph["facts"][0]["retest_trigger"].__setitem__(
            "minimum_new_samples", 1025
        ),
        lambda graph: graph["facts"][0]["provenance"]["cloud"].__setitem__(
            "evidence_id", "arbitrary-publishable-token"
        ),
    ),
)
def test_executable_schema_rejects_all_closed_type_length_enum_and_range_errors(
    tmp_path: pathlib.Path, mutation,
) -> None:
    graph = deepcopy(load_json(POSITIVE))
    mutation(graph)
    result = run_validator("verify", write_json(tmp_path / "graph.json", graph))
    assert result.returncode == 1
    assert result.stdout == "schema.graph\n"


def test_preflight_rejects_byte_depth_member_string_and_list_budgets_before_loads(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_validator_module()
    values = (
        b" " * (1_048_576 + 1),
        (b"[" * 34) + (b"]" * 34),
        b"{" + b','.join(b'\"a%d\":0' % index for index in range(16385)) + b"}",
        b'{"value":"' + (b"a" * 4097) + b'"}',
        b"[" + b",".join(b"0" for _ in range(1025)) + b"]",
    )

    def decoder_must_not_run(*_args, **_kwargs):
        raise AssertionError("json.loads ran before bounded preflight")

    monkeypatch.setattr(module.json, "loads", decoder_must_not_run)
    for index, raw in enumerate(values):
        path = tmp_path / f"preflight-{index}.json"
        path.write_bytes(raw)
        with pytest.raises(module.Failure) as error:
            module.load_json(path, input_kind="graph")
        assert str(error.value) == "limits.exceeded"


def test_graph_validation_precedes_bad_source_inputs(tmp_path: pathlib.Path) -> None:
    malformed_source = tmp_path / "source.json"
    malformed_source.write_text("{", encoding="utf-8")

    malformed_graph = tmp_path / "malformed-graph.json"
    malformed_graph.write_text("{", encoding="utf-8")
    result = run_validator(
        "verify", malformed_graph, malformed_source, malformed_source
    )
    assert result.stdout == "json.syntax\n"

    unknown = deepcopy(load_json(POSITIVE))
    unknown["unknown"] = True
    result = run_validator(
        "verify",
        write_json(tmp_path / "unknown.json", unknown),
        malformed_source,
        malformed_source,
    )
    assert result.stdout == "schema.graph\n"

    registry_bad = deepcopy(load_json(POSITIVE))
    registry_bad["registry"]["digest"] = "sha256:" + "0" * 64
    result = run_validator(
        "verify",
        write_json(tmp_path / "registry.json", registry_bad),
        malformed_source,
        malformed_source,
    )
    assert result.stdout == "registry.binding\n"


def test_fail_closed_provenance_status_matrix(tmp_path: pathlib.Path) -> None:
    graph = deepcopy(load_json(POSITIVE))
    cloud = next(fact for fact in graph["facts"] if fact["provenance"]["cloud"])
    cloud["status"] = "RAW_ONLY"
    cloud["terminal_negative_state"] = None
    result = run_validator("verify", write_json(tmp_path / "cloud.json", graph))
    assert result.stdout == "state.terminal\n"

    graph = deepcopy(load_json(POSITIVE))
    target = next(fact for fact in graph["facts"] if fact["provenance"]["ebus"])
    target["status"] = "CANDIDATE"
    target["terminal_negative_state"] = None
    target["draft_value"] = "21.25"
    target["draft_unit"] = "degC"
    result = run_validator("verify", write_json(tmp_path / "one-sided.json", graph))
    assert result.stdout == "provenance.binding\n"

    graph = deepcopy(load_json(POSITIVE))
    service_only = next(
        fact for fact in graph["facts"] if fact["provenance"]["eebus_service"]
    )
    service_only["status"] = "CANDIDATE"
    service_only["draft_value"] = "21"
    service_only["draft_unit"] = "degC"
    result = run_validator(
        "verify", write_json(tmp_path / "service-only.json", graph)
    )
    assert result.stdout == "provenance.binding\n"
