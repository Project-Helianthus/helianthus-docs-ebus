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
SOURCE_TERMINAL_GRAPH = FIXTURE_ROOT / "positive/source-terminal-graph.json"
SOURCE_TERMINAL_REPLAY = (
    FIXTURE_ROOT / "positive/source-terminal-replay-result.json"
)
SOURCE_TERMINAL_BUNDLE = FIXTURE_ROOT / "positive/source-terminal-bundle.json"
SOURCE_TERMINAL_SOURCE_REPLAY = (
    FIXTURE_ROOT / "positive/source-terminal-source-replay.json"
)
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
    "source-terminal-candidate.json": "provenance.binding",
    "source-terminal-conflicted.json": "provenance.binding",
    "source-terminal-cross-runtime-pairing.json": "provenance.binding",
    "source-terminal-evaluated-samples.json": "provenance.binding",
    "source-terminal-forged-binding-kind.json": "provenance.binding",
    "source-terminal-forged-contract.json": "provenance.binding",
    "source-terminal-forged-error.json": "schema.graph",
    "source-terminal-forged-evidence-refs.json": "provenance.binding",
    "source-terminal-forged-identity.json": "provenance.binding",
    "source-terminal-forged-phase.json": "provenance.binding",
    "source-terminal-forged-source-id.json": "provenance.binding",
    "source-terminal-forged-source-kind.json": "schema.graph",
    "source-terminal-forged-state.json": "schema.graph",
    "source-terminal-forged-version.json": "provenance.binding",
    "source-terminal-no-signal.json": "state.terminal",
    "source-terminal-null.json": "provenance.binding",
    "source-terminal-omitted.json": "provenance.binding",
    "source-terminal-promoted-exposure.json": "anti_leak.consumer",
}

COEXISTENCE_VALIDATOR = REPO_ROOT / "scripts/validate_multi_runtime_coexistence.py"
COEXISTENCE_GENERATOR = (
    REPO_ROOT / "scripts/generate_multi_runtime_coexistence_fixture.py"
)
COEXISTENCE_SCHEMA = (
    SCHEMA_ROOT / "multi-runtime-coexistence-evidence-v1.schema.json"
)
COEXISTENCE_REPORT_SCHEMA = (
    SCHEMA_ROOT / "multi-runtime-coexistence-report-v1.schema.json"
)
COEXISTENCE_REGISTRY = (
    SCHEMA_ROOT / "multi-runtime-coexistence-registry-v1.json"
)
COEXISTENCE_FIXTURE_ROOT = (
    REPO_ROOT / "docs/platform/fixtures/coexistence-no-drift/v1"
)
COEXISTENCE_POSITIVE = COEXISTENCE_FIXTURE_ROOT / "positive/evidence.json"
COEXISTENCE_GOLDEN_REPORT = COEXISTENCE_FIXTURE_ROOT / "positive/report.json"
COEXISTENCE_NEGATIVE_ROOT = COEXISTENCE_FIXTURE_ROOT / "negative"
M7_GRAPH = FIXTURE_ROOT / "positive/graph.json"
M7_REPLAY = FIXTURE_ROOT / "positive/replay-result.json"
M7_REGISTRY = REGISTRY
M7_SOURCE_BUNDLE = SOURCE_BUNDLE
M7_SOURCE_REPLAY = SOURCE_REPLAY
EXPECTED_COEXISTENCE_NEGATIVE = {
    "candidate-leak-ebus-mcp.json": "anti_leak.candidate",
    "canonical-hash-mismatch.json": "hash.payload",
    "clock-mismatch.json": "provenance.clock",
    "config-hash-mismatch.json": "provenance.config",
    "conflict-leak-graphql.json": "anti_leak.candidate",
    "dropped-payload-field.json": "drift.consumer",
    "duplicate-provenance.json": "ordering.duplicate",
    "g17-claim.json": "gate.scope",
    "g19-claim.json": "gate.scope",
    "input-hash-mismatch.json": "provenance.runtime",
    "m7-graph-mismatch.json": "provenance.m7",
    "mask-scope-mismatch.json": "provenance.auth_mask",
    "missing-provenance.json": "schema.evidence",
    "missing-required-view.json": "view.coverage",
    "no-services-empty-success.json": "state.evidence",
    "public-v2-surface.json": "gate.scope",
    "resource-limit-exceeded.json": "limits.exceeded",
    "rollback-drift.json": "rollback.drift",
    "runtime-artifact-mismatch.json": "provenance.runtime",
    "stale-capture.json": "provenance.clock",
    "timestamp-exclusion-mismatch.json": "canonicalization.invalid",
    "unknown-field.json": "schema.evidence",
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
        SOURCE_TERMINAL_GRAPH,
        SOURCE_TERMINAL_REPLAY,
        SOURCE_TERMINAL_BUNDLE,
        SOURCE_TERMINAL_SOURCE_REPLAY,
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


def test_existing_artifact_backed_v1_fixture_bytes_are_unchanged() -> None:
    assert hashlib.sha256(POSITIVE.read_bytes()).hexdigest() == (
        "b5c5d79e540a1691ee60c6db3e9405a92d9d544d871c74b26800fe449a318b0e"
    )
    assert hashlib.sha256(GOLDEN_REPLAY.read_bytes()).hexdigest() == (
        "8280f6278ffe8598dfd767bb5bf9e60dce3c145b4612174b7c5a32fbff282f5c"
    )
    assert all(
        "source_terminal" not in fact["provenance"]
        for fact in load_json(POSITIVE)["facts"]
    )


def test_source_terminal_fixture_binds_b509_b524_b555_without_artifacts() -> None:
    graph = load_json(SOURCE_TERMINAL_GRAPH)
    bundle = load_json(SOURCE_TERMINAL_BUNDLE)
    assert bundle["artifacts"] == []
    assert {
        (source["ebus_identity"]["family"], source["state"], source["error_category"])
        for source in bundle["sources"]
    } == {
        ("B509", "UNAVAILABLE", "BACKEND_UNAVAILABLE"),
        ("B524", "UNAVAILABLE", "BACKEND_UNAVAILABLE"),
        ("B555", "UNAVAILABLE", "BACKEND_UNAVAILABLE"),
    }
    sources = {source["source_id"]: source for source in bundle["sources"]}
    for fact in graph["facts"]:
        terminal = fact["provenance"]["source_terminal"]
        source = sources[terminal["source_id"]]
        assert terminal == {
            "source_id": source["source_id"],
            "source_kind": source["source_kind"],
            "binding_source_kind": source["source_binding"]["source_kind"],
            "source_contract": source["source_contract"],
            "source_schema_version": source["source_schema_version"],
            "phase": source["phase"],
            "state": source["state"],
            "error_category": source["error_category"],
            "ebus_identity": source["ebus_identity"],
            "evidence_refs": source["evidence_refs"],
        }
        assert fact["status"] == "WITHHELD"
        assert fact["terminal_negative_state"] == "NOT_TESTED"
        assert fact["draft_value"] is None and fact["draft_unit"] is None
        assert fact["comparator"] == {
            "draft_id": "NUMERIC_WINDOW_V1_DRAFT",
            "samples": [],
            "outcome": "NOT_EVALUATED",
        }
        assert fact["debug_only"] is True
        assert fact["retest_trigger"] == {
            "trigger_code": "SOURCE_RECOVERED",
            "required_source_kinds": ["EBUS"],
            "minimum_new_samples": 1,
        }


def test_source_terminal_graph_and_replay_are_schema_valid_and_deterministic() -> None:
    for schema, fixture in (
        (SCHEMA, SOURCE_TERMINAL_GRAPH),
        (REPLAY_SCHEMA, SOURCE_TERMINAL_REPLAY),
    ):
        result = subprocess.run(
            ["jv", str(schema), str(fixture)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
    first = run_validator(
        "replay",
        SOURCE_TERMINAL_GRAPH,
        SOURCE_TERMINAL_BUNDLE,
        SOURCE_TERMINAL_SOURCE_REPLAY,
    )
    second = run_validator(
        "replay",
        SOURCE_TERMINAL_GRAPH,
        SOURCE_TERMINAL_BUNDLE,
        SOURCE_TERMINAL_SOURCE_REPLAY,
    )
    golden = SOURCE_TERMINAL_REPLAY.read_text(encoding="utf-8")
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout == golden
    assert first.stderr == second.stderr == ""
    replay = load_json(SOURCE_TERMINAL_REPLAY)
    assert {result["source_terminal"]["identity_family"] for result in replay["results"]} == {
        "B509",
        "B524",
        "B555",
    }


def test_source_terminal_replay_deduplicates_shared_evidence_digests(
    tmp_path: pathlib.Path,
) -> None:
    module = load_validator_module()
    graph = deepcopy(load_json(SOURCE_TERMINAL_GRAPH))
    terminal = graph["facts"][0]["provenance"]["source_terminal"]
    duplicate = deepcopy(terminal["evidence_refs"][0])
    duplicate.update(
        {
            "repository": "Project-Helianthus/helianthus-docs-ebus",
            "commit": "a" * 40,
            "path": "evidence/same-content-at-another-path.json",
        }
    )
    terminal["evidence_refs"].append(duplicate)

    replay = module.replay(graph)
    digests = replay["results"][0]["source_terminal"]["evidence_digests"]
    assert digests == [duplicate["digest"]]

    fixture = write_json(tmp_path / "replay.json", replay)
    result = subprocess.run(
        ["jv", str(REPLAY_SCHEMA), str(fixture)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifact_backed_v1_accepts_explicit_null_source_terminal(
    tmp_path: pathlib.Path,
) -> None:
    module = load_validator_module()
    graph = deepcopy(load_json(POSITIVE))
    for fact in graph["facts"]:
        fact["provenance"]["source_terminal"] = None
        fact["fact_hash"] = "sha256:" + module.fact_hexdigest(fact)
    hexdigest = module.graph_hexdigest(graph)
    graph["graph_id"] = "dcfgv1:sha256:" + hexdigest
    graph["graph_hash"] = "sha256:" + hexdigest
    result = run_validator("verify", write_json(tmp_path / "graph.json", graph))
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "ok\n"
    assert all(
        item["source_terminal"] is None for item in module.replay(graph)["results"]
    )


def test_source_terminal_participates_in_fact_graph_and_replay_hashes() -> None:
    module = load_validator_module()
    graph = deepcopy(load_json(SOURCE_TERMINAL_GRAPH))
    fact = graph["facts"][0]
    original_fact_digest = module.fact_hexdigest(fact)
    original_graph_digest = module.graph_hexdigest(graph)
    original_replay_hash = module.replay(graph)["replay_hash"]
    fact["provenance"]["source_terminal"]["source_contract"] = (
        "helianthus.ebus.synthetic-mutated.evidence.v1"
    )
    assert module.fact_hexdigest(fact) != original_fact_digest
    assert module.graph_hexdigest(graph) != original_graph_digest
    assert module.replay(graph)["replay_hash"] != original_replay_hash


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
    base = (NEGATIVE_ROOT / fixture["base"]).resolve()
    graph = deepcopy(load_json(base))
    source_bundle = SOURCE_BUNDLE
    source_replay = SOURCE_REPLAY
    if base == SOURCE_TERMINAL_GRAPH.resolve():
        source_bundle = SOURCE_TERMINAL_BUNDLE
        source_replay = SOURCE_TERMINAL_SOURCE_REPLAY
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
    elif mutation.startswith("SOURCE_TERMINAL_"):
        target = graph["facts"][0]
        terminal = target["provenance"]["source_terminal"]
        if mutation == "SOURCE_TERMINAL_CANDIDATE":
            target["status"] = "CANDIDATE"
            target["terminal_negative_state"] = None
        elif mutation == "SOURCE_TERMINAL_CONFLICTED":
            target["status"] = "CONFLICTED"
            target["terminal_negative_state"] = None
        elif mutation == "SOURCE_TERMINAL_EVALUATED_SAMPLES":
            ref = deepcopy(target["provenance"]["native_evidence_refs"][0])
            target["comparator"] = {
                "draft_id": "NUMERIC_WINDOW_V1_DRAFT",
                "samples": [
                    {
                        "offset_ns": 1,
                        "left": {
                            "source_kind": "EBUS",
                            "source_id": "ebus-" + "a" * 32,
                            "artifact_id": "seav1:sha256:" + "a" * 64,
                            "evidence_ref": ref,
                            "observed_offset_ns": 1,
                            "value_pointer": "/value",
                            "unit_pointer": "/unit",
                            "native_decimal": "1",
                            "native_unit": "degC",
                        },
                        "right": {
                            "source_kind": "EEBUS",
                            "source_id": "eebus-" + "b" * 32,
                            "artifact_id": "seav1:sha256:" + "b" * 64,
                            "evidence_ref": ref,
                            "observed_offset_ns": 1,
                            "value_pointer": "/value",
                            "unit_pointer": "/unit",
                            "native_decimal": "1",
                            "native_unit": "degC",
                        },
                        "state": "PRESENT",
                    }
                ],
                "outcome": "INDETERMINATE",
            }
        elif mutation == "SOURCE_TERMINAL_PROMOTED_EXPOSURE":
            graph["visibility"]["stable_exposure"] = True
        elif mutation == "SOURCE_TERMINAL_FORGED_SOURCE_ID":
            terminal["source_id"] = "ebus-" + "f" * 32
        elif mutation == "SOURCE_TERMINAL_FORGED_SOURCE_KIND":
            terminal["source_kind"] = "EEBUS"
        elif mutation == "SOURCE_TERMINAL_FORGED_BINDING_KIND":
            terminal["binding_source_kind"] = "EBUS_B524"
        elif mutation == "SOURCE_TERMINAL_FORGED_CONTRACT":
            terminal["source_contract"] = "helianthus.ebus.forged.evidence.v1"
        elif mutation == "SOURCE_TERMINAL_FORGED_VERSION":
            terminal["source_schema_version"] = 2
        elif mutation == "SOURCE_TERMINAL_FORGED_PHASE":
            terminal["phase"] = "action"
        elif mutation == "SOURCE_TERMINAL_FORGED_STATE":
            terminal["state"] = "NOT_TESTED"
        elif mutation == "SOURCE_TERMINAL_FORGED_ERROR":
            terminal["error_category"] = "TIMEOUT"
        elif mutation == "SOURCE_TERMINAL_FORGED_IDENTITY":
            terminal["ebus_identity"]["target_address"] += 1
        elif mutation == "SOURCE_TERMINAL_FORGED_EVIDENCE_REFS":
            terminal["evidence_refs"][0]["digest"] = "sha256:" + "f" * 64
        elif mutation == "SOURCE_TERMINAL_CROSS_RUNTIME_PAIRING":
            target["provenance"]["eebus_source_id"] = "eebus-" + "e" * 32
            target["provenance"]["eebus_artifact_id"] = (
                "seav1:sha256:" + "e" * 64
            )
            target["provenance"]["eebus_service"] = "service-" + "e" * 32
        elif mutation == "SOURCE_TERMINAL_NO_SIGNAL":
            target["terminal_negative_state"] = "NO_SIGNAL"
            target["falsifier"]["expected_terminal_state"] = "NO_SIGNAL"
        elif mutation == "SOURCE_TERMINAL_NULL":
            target["provenance"]["source_terminal"] = None
        elif mutation == "SOURCE_TERMINAL_OMITTED":
            del target["provenance"]["source_terminal"]
        else:
            raise AssertionError(f"unhandled source-terminal mutation: {mutation}")
    else:
        raise AssertionError(f"unhandled test-only mutation: {mutation}")
    result = run_validator(
        "verify",
        write_json(tmp_path / name, graph),
        source_bundle,
        source_replay,
    )
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
    left = _artifact("EBUS", "a", "8", left_value, "degC" if left_value else None)
    right = _artifact("EEBUS", "b", "9", right_value, "degC" if right_value else None)
    target = next(
        fact
        for fact in graph["facts"]
        if fact["provenance"]["ebus"]
        and fact["provenance"]["ebus"]["family"] == "B524"
    )
    eebus_path = {
        "service": "service-" + "a" * 32,
        "entity": "entity-" + "b" * 32,
        "feature": "feature-" + "c" * 32,
        "feature_path": [
            {"kind": "SERVICE", "selector": "service-" + "a" * 32},
            {"kind": "ENTITY", "selector": "entity-" + "b" * 32},
            {"kind": "FEATURE", "selector": "feature-" + "c" * 32},
        ],
    }
    left["ebus_identity"] = deepcopy(target["provenance"]["ebus"])
    right["normalized_evidence"]["data"] = {
        "services": [{"id": {"digest": eebus_path["service"]}}],
        "feature_paths": [deepcopy(eebus_path)],
    }
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
    target["provenance"]["eebus_service"] = eebus_path["service"]
    target["provenance"]["eebus"] = eebus_path
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
    source = deepcopy(load_json(SOURCE_BUNDLE))
    source["sources"].extend(
        [
            {
                "source_id": left["source_id"],
                "source_kind": "EBUS",
                "artifact_ids": [left["artifact_id"]],
            },
            {
                "source_id": right["source_id"],
                "source_kind": "EEBUS",
                "artifact_ids": [right["artifact_id"]],
            },
        ]
    )
    source["artifacts"].extend([left, right])
    source["evidence_refs"].extend(
        [deepcopy(left["evidence_refs"][0]), deepcopy(right["evidence_refs"][0])]
    )
    graph["source_bundle"]["evidence_refs"] = deepcopy(source["evidence_refs"])
    return graph, target, source


def _validate_comparison_vector(
    module, graph: dict[str, object], target: dict[str, object], source: dict[str, object]
) -> None:
    registry = load_json(REGISTRY)
    module.check_provenance(
        graph,
        registry,
        source,
        load_json(SOURCE_REPLAY),
    )
    module.check_identities(graph, source)
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


def test_failed_availability_bounds_precede_conflict_classification() -> None:
    left = _artifact("EBUS", "a", "1", "10", "degC")
    unavailable_left = _artifact("EBUS", "c", "3", None, None)
    right = _artifact("EEBUS", "b", "2", "11", "degC")
    parameters = _parameters()
    parameters["minimum_samples"] = 1
    parameters["maximum_missing_samples"] = 0
    parameters["conflict_threshold"] = {
        "absolute_decimal": "1",
        "consecutive_samples": 1,
    }
    samples = [
        _sample(left, right, offset_ns=4_000_000_000),
        _sample(
            unavailable_left,
            right,
            offset_ns=5_000_000_000,
            state="MISSING",
        ),
    ]
    assert (
        _evaluate(parameters, samples, [left, unavailable_left, right])
        == "INDETERMINATE"
    )


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


def run_coexistence_validator(
    command: str, evidence: pathlib.Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(COEXISTENCE_VALIDATOR),
            command,
            "--evidence",
            str(evidence),
            "--registry",
            str(COEXISTENCE_REGISTRY),
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
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONHASHSEED": "random"},
    )


def _coexistence_digest(domain: bytes, value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(domain + b"\0" + encoded).hexdigest()


def _replace_pointer(value: object, pointer: str, replacement: str) -> None:
    current = value
    for raw_part in pointer.split("/")[1:-1]:
        part = raw_part.replace("~1", "/").replace("~0", "~")
        current = current[int(part)] if isinstance(current, list) else current[part]
    raw_leaf = pointer.split("/")[-1]
    leaf = raw_leaf.replace("~1", "/").replace("~0", "~")
    if isinstance(current, list):
        current[int(leaf)] = replacement
    else:
        current[leaf] = replacement


def _payload_shape(value: object) -> object:
    if isinstance(value, dict):
        return {key: _payload_shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_payload_shape(item) for item in value]
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    return "string"


def _refresh_view_hashes(evidence: dict[str, object], view: dict[str, object]) -> None:
    rules = next(
        item
        for item in evidence["normalization"]["view_rules"]
        if item["view_id"] == view["view_id"]
    )
    normalized = deepcopy(view["payload"])
    for pointer in rules["timestamp_pointers"]:
        _replace_pointer(normalized, pointer, "<TIMESTAMP>")
    for pointer in rules["mask_pointers"]:
        _replace_pointer(normalized, pointer, "<MASKED>")
    view["raw_payload_hash"] = _coexistence_digest(
        b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-RAW-PAYLOAD:V1",
        view["payload"],
    )
    view["shape_hash"] = _coexistence_digest(
        b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-PAYLOAD-SHAPE:V1",
        _payload_shape(view["payload"]),
    )
    view["canonical_payload_hash"] = _coexistence_digest(
        b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-CANONICAL-PAYLOAD:V1",
        normalized,
    )
    run = next(run for run in evidence["runs"] if view in run["protected_views"])
    immutable_input = next(
        item
        for item in run["provenance"]["immutable_inputs"]
        if item["input_id"] == "view:" + view["view_id"]
    )
    immutable_input["digest"] = view["raw_payload_hash"]
    immutable_input["byte_length"] = len(
        json.dumps(
            view["payload"],
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )


def _refresh_coexistence_evidence_identity(evidence: dict[str, object]) -> None:
    evidence_view = {
        key: value
        for key, value in evidence.items()
        if key not in {"evidence_id", "evidence_hash"}
    }
    evidence_hash = _coexistence_digest(
        b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-EVIDENCE:V1", evidence_view
    )
    evidence["evidence_hash"] = evidence_hash
    evidence["evidence_id"] = "mrcv1:" + evidence_hash


def _run_by_state(evidence: dict[str, object], state: str) -> dict[str, object]:
    return next(run for run in evidence["runs"] if run["state"] == state)


def _view_by_id(run: dict[str, object], view_id: str) -> dict[str, object]:
    return next(view for view in run["protected_views"] if view["view_id"] == view_id)


def _apply_coexistence_mutation(
    evidence: dict[str, object], mutation: str
) -> None:
    disabled = _run_by_state(evidence, "EEBUS_DISABLED_CONFIRMED")
    no_services = _run_by_state(evidence, "EEBUS_ENABLED_NO_SERVICES")
    candidate = _run_by_state(evidence, "EEBUS_CONNECTED_CANDIDATE_ONLY")
    conflicted = _run_by_state(evidence, "EEBUS_CONFLICTED_WITHHELD")
    rollback = _run_by_state(evidence, "EEBUS_DISABLED_ROLLBACK")
    if mutation == "CANDIDATE_LEAK_EBUS_MCP":
        view = _view_by_id(candidate, "mcp.ebus.v1.responses")
        view["payload"]["data"]["candidate_status"] = "CANDIDATE"
        _refresh_view_hashes(evidence, view)
    elif mutation == "CANONICAL_HASH_MISMATCH":
        disabled["protected_views"][0]["canonical_payload_hash"] = (
            "sha256:" + "f" * 64
        )
    elif mutation == "CLOCK_MISMATCH":
        disabled["provenance"]["capture_clock_id"] = "clock-" + "f" * 32
    elif mutation == "CONFIG_HASH_MISMATCH":
        disabled["provenance"]["config"]["config_hash"] = "sha256:" + "f" * 64
    elif mutation == "CONFLICT_LEAK_GRAPHQL":
        view = _view_by_id(conflicted, "graphql.ebus.values")
        view["payload"]["data"]["conflict_status"] = "WITHHELD/CONFLICT"
        _refresh_view_hashes(evidence, view)
    elif mutation == "DROPPED_PAYLOAD_FIELD":
        view = _view_by_id(disabled, "ha.identity")
        del view["payload"]["data"]["devices"][0]["manufacturer"]
        _refresh_view_hashes(evidence, view)
    elif mutation == "DUPLICATE_PROVENANCE":
        disabled["provenance"]["immutable_inputs"].append(
            deepcopy(disabled["provenance"]["immutable_inputs"][0])
        )
    elif mutation == "G17_CLAIM":
        evidence["scope"]["claims"].append("EEBUS-G17")
    elif mutation == "G19_CLAIM":
        evidence["scope"]["claims"].append("EEBUS-G19")
    elif mutation == "INPUT_HASH_MISMATCH":
        disabled["provenance"]["immutable_inputs"][0]["digest"] = (
            "sha256:" + "f" * 64
        )
    elif mutation == "M7_GRAPH_MISMATCH":
        evidence["m7_binding"]["graph_hash"] = "sha256:" + "f" * 64
    elif mutation == "MASK_SCOPE_MISMATCH":
        disabled["provenance"]["mask_scope_digest"] = "sha256:" + "f" * 64
    elif mutation == "MISSING_PROVENANCE":
        del disabled["provenance"]
    elif mutation == "MISSING_REQUIRED_VIEW":
        removed = disabled["protected_views"].pop()
        disabled["provenance"]["immutable_inputs"] = [
            item
            for item in disabled["provenance"]["immutable_inputs"]
            if item["input_id"] != "view:" + removed["view_id"]
        ]
    elif mutation == "NO_SERVICES_EMPTY_SUCCESS":
        no_services["state_evidence"]["empty_success"] = True
    elif mutation == "PUBLIC_V2_SURFACE":
        view = _view_by_id(disabled, "mcp.tool.inventory")
        view["payload"]["data"]["tools"].append("eebus.v2.runtime.status")
        _refresh_view_hashes(evidence, view)
    elif mutation == "RESOURCE_LIMIT_EXCEEDED":
        evidence["limits"]["max_runs"] += 1
    elif mutation == "ROLLBACK_DRIFT":
        view = _view_by_id(rollback, "semantic.registry")
        view["payload"]["data"]["authority"] = "eebus-candidate"
        _refresh_view_hashes(evidence, view)
    elif mutation == "RUNTIME_ARTIFACT_MISMATCH":
        disabled["provenance"]["runtime"]["artifact_digest"] = (
            "sha256:" + "f" * 64
        )
    elif mutation == "STALE_CAPTURE":
        evidence["capture_clock"]["verification_offset_ns"] = (
            evidence["capture_clock"]["max_capture_age_ns"]
            + evidence["runs"][0]["capture_offset_ns"]
            + 1
        )
    elif mutation == "TIMESTAMP_EXCLUSION_MISMATCH":
        evidence["normalization"]["view_rules"][0]["timestamp_pointers"] = []
        profile = {
            key: value
            for key, value in evidence["normalization"].items()
            if key != "profile_digest"
        }
        digest = _coexistence_digest(
            b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-NORMALIZATION:V1",
            profile,
        )
        evidence["normalization"]["profile_digest"] = digest
        for run in evidence["runs"]:
            run["provenance"]["mask_scope_digest"] = digest
    elif mutation == "UNKNOWN_FIELD":
        evidence["verdict"] = "PASS"
    else:
        raise AssertionError(f"unhandled MSP-08 mutation: {mutation}")


def test_msp08_executable_contract_inventory_is_frozen_for_gateway_red() -> None:
    for path in (
        COEXISTENCE_VALIDATOR,
        COEXISTENCE_GENERATOR,
        COEXISTENCE_SCHEMA,
        COEXISTENCE_REPORT_SCHEMA,
        COEXISTENCE_REGISTRY,
        COEXISTENCE_POSITIVE,
        COEXISTENCE_GOLDEN_REPORT,
        M7_GRAPH,
        M7_REPLAY,
        M7_REGISTRY,
        M7_SOURCE_BUNDLE,
        M7_SOURCE_REPLAY,
    ):
        assert path.is_file(), f"missing executable MSP-08 contract file: {path}"
    assert {path.name for path in COEXISTENCE_NEGATIVE_ROOT.glob("*.json")} == set(
        EXPECTED_COEXISTENCE_NEGATIVE
    )


def test_msp08_positive_fixture_ids_states_and_protected_views_are_closed() -> None:
    evidence = load_json(COEXISTENCE_POSITIVE)
    registry = load_json(COEXISTENCE_REGISTRY)
    assert evidence["fixture_id"] == "MSP08-G18-SYNTHETIC-POSITIVE-001"
    assert evidence["evidence_class"] == "SYNTHETIC_OFFLINE_FIXTURE"
    assert evidence["scope"]["live_vr940_claim"] is False
    assert evidence["scope"]["claims"] == ["EEBUS-G18"]
    assert [run["state"] for run in evidence["runs"]] == registry[
        "scenario_profiles"
    ]["SYNTHETIC_OFFLINE_FIXTURE"]
    expected_views = registry["protected_views"]
    for run in evidence["runs"]:
        assert [view["view_id"] for view in run["protected_views"]] == (
            expected_views
        )
        assert run["state_evidence"]["empty_success"] is False
    candidate = _run_by_state(evidence, "EEBUS_CONNECTED_CANDIDATE_ONLY")
    conflicted = _run_by_state(evidence, "EEBUS_CONFLICTED_WITHHELD")
    assert candidate["state_evidence"]["facts"][0]["status"] == "CANDIDATE"
    assert conflicted["state_evidence"]["facts"][0] == {
        "candidate_id": "m7-candidate-synthetic-conflict-0001",
        "status": "WITHHELD",
        "terminal_negative_state": "CONFLICT",
        "visibility_channel": "CANDIDATE_DEBUG_REPLAY",
    }


def test_msp08_positive_evidence_and_report_are_schema_valid() -> None:
    for schema, fixture in (
        (COEXISTENCE_SCHEMA, COEXISTENCE_POSITIVE),
        (COEXISTENCE_REPORT_SCHEMA, COEXISTENCE_GOLDEN_REPORT),
    ):
        result = subprocess.run(
            ["jv", str(schema), str(fixture)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_msp08_report_is_verifier_derived_and_byte_deterministic() -> None:
    first = run_coexistence_validator("report", COEXISTENCE_POSITIVE)
    second = run_coexistence_validator("report", COEXISTENCE_POSITIVE)
    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    golden = COEXISTENCE_GOLDEN_REPORT.read_text(encoding="utf-8")
    assert first.stdout == golden
    assert second.stdout == golden
    assert first.stderr == ""
    assert second.stderr == ""


@pytest.mark.parametrize(
    "leak",
    [
        {"spineService": "private-spine-service"},
        {"spineEntity": "private-spine-entity"},
        {"spineFeature": "private-spine-feature"},
        {"eebusService": "private-eebus-service"},
        {"eebusEntity": "private-eebus-entity"},
        {"eebusFeature": "private-eebus-feature"},
        {"feature_path": "private-feature-path"},
        {"debug_detail": "127.0.0.1:4712"},
        {"debug_detail": "169.254.12.34"},
        {"debug_detail": "10.255.255.025:4712"},
        {"debug_detail": "999.999.999.999:4712"},
        {"debug_detail": "1.10.255.255.254:4712"},
        {"addresses": [4, 246]},
        {"ship_identifier": "synthetic-peer-identity"},
        {"ship_identity": "synthetic-peer-identity"},
        {"ship_identities": ["synthetic-peer-identity"]},
        {"debug_detail": "http://10.255.255.254.:4712"},
        {"debug_detail": "10..8.8.8.8"},
        {"debug_detail": "100.64.0.1"},
        {"debug_detail": "224.0.0.251"},
        {"debug_detail": "239.255.255.250:1900"},
        {"debug_detail": "8.8.8.8."},
        {"debug_detail": "Authorization: Bearer synthetic-credential"},
        {"debug_detail": "session_cookie=synthetic-cookie"},
        {"debug_detail": "access_token=synthetic-token"},
        {"debug_detail": "refresh_token=synthetic-token"},
        {"debug_detail": "client_secret=synthetic-secret"},
        {"debug_detail": "csrf_token=synthetic-token"},
        {"debug_detail": "private_key=synthetic-key"},
        {"debug_detail": "ff02::fb"},
        {"10.255.255.254": "redacted"},
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
    ],
)
def test_msp08_report_rejects_native_identity_and_non_public_ipv4(
    tmp_path: pathlib.Path, leak: dict[str, object]
) -> None:
    evidence = deepcopy(load_json(COEXISTENCE_POSITIVE))
    for run in evidence["runs"]:
        view = run["protected_views"][-1]
        view["payload"]["data"]["public_leak"] = leak
        _refresh_view_hashes(evidence, view)
    evidence_view = {
        key: value
        for key, value in evidence.items()
        if key not in {"evidence_id", "evidence_hash"}
    }
    evidence_hash = _coexistence_digest(
        b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-EVIDENCE:V1", evidence_view
    )
    evidence["evidence_hash"] = evidence_hash
    evidence["evidence_id"] = "mrcv1:" + evidence_hash

    result = run_coexistence_validator(
        "report", write_json(tmp_path / "redaction-leak.json", evidence)
    )
    assert result.returncode == 1
    assert result.stdout == "redaction.public\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    "leak",
    [
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
        {"terminal_negative_states": []},
    ],
)
def test_msp08_report_rejects_candidate_metadata_names(
    tmp_path: pathlib.Path, leak: object
) -> None:
    evidence = deepcopy(load_json(COEXISTENCE_POSITIVE))
    for run in evidence["runs"]:
        view = run["protected_views"][-1]
        view["payload"]["data"]["candidate_metadata_leak"] = leak
        _refresh_view_hashes(evidence, view)
    _refresh_coexistence_evidence_identity(evidence)

    result = run_coexistence_validator(
        "report", write_json(tmp_path / "candidate-metadata-leak.json", evidence)
    )
    assert result.returncode == 1
    assert result.stdout == "anti_leak.candidate\n"
    assert result.stderr == ""


def test_msp08_report_allows_globally_routable_ipv4(
    tmp_path: pathlib.Path,
) -> None:
    evidence = deepcopy(load_json(COEXISTENCE_POSITIVE))
    for run in evidence["runs"]:
        view = run["protected_views"][-1]
        view["payload"]["data"]["debug_detail"] = "8.8.8.8:53"
        view["payload"]["data"]["endpoint_count"] = 2
        view["payload"]["data"]["address_count"] = 2
        view["payload"]["data"]["resource_id"] = "public-resource"
        view["payload"]["data"]["endpoint_hash"] = "sha256:" + "c" * 64
        view["payload"]["data"]["ship_ids"] = ["sha256:" + "d" * 64]
        view["payload"]["data"]["token_count"] = 2
        view["payload"]["data"]["monkey_material"] = "public"
        view["payload"]["data"]["debug_note"] = "basic public metadata"
        view["payload"]["data"]["debug_version"] = "v10.2.3.4"
        view["payload"]["data"]["debug_note_secondary"] = (
            "candidate facts are not published"
        )
        view["payload"]["data"]["scope_note"] = "eebus.v2 is not active"
        _refresh_view_hashes(evidence, view)
    evidence_view = {
        key: value
        for key, value in evidence.items()
        if key not in {"evidence_id", "evidence_hash"}
    }
    evidence_hash = _coexistence_digest(
        b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-EVIDENCE:V1", evidence_view
    )
    evidence["evidence_hash"] = evidence_hash
    evidence["evidence_id"] = "mrcv1:" + evidence_hash

    result = run_coexistence_validator(
        "report", write_json(tmp_path / "public-ipv4.json", evidence)
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["verdict"] == "PASS"
    assert result.stderr == ""


@pytest.mark.parametrize(
    "mutation",
    [
        "LEGACY_TOOL",
        "LEGACY_NAMESPACE",
        "MALFORMED_TOOL",
        "NESTED_V2",
        "NESTED_VERSION2",
        "ALIASES",
    ],
)
def test_msp08_report_rejects_non_v1_eebus_surfaces(
    tmp_path: pathlib.Path, mutation: str
) -> None:
    evidence = deepcopy(load_json(COEXISTENCE_POSITIVE))
    for run in evidence["runs"]:
        if mutation in {"LEGACY_TOOL", "MALFORMED_TOOL"}:
            view = _view_by_id(run, "mcp.tool.inventory")
            tool = (
                "eebus.runtime.status.get"
                if mutation == "LEGACY_TOOL"
                else " eebus.runtime.status.get"
            )
            view["payload"]["data"]["tools"].append(tool)
        elif mutation == "LEGACY_NAMESPACE":
            view = _view_by_id(run, "mcp.eebus.v1.contract")
            view["payload"]["data"]["namespace"] = "eebus.legacy"
        elif mutation == "NESTED_V2":
            view = _view_by_id(run, "mcp.eebus.v1.contract")
            view["payload"]["data"]["alternate_contracts"] = [
                {"active": True, "namespace": "eebus.v2"}
            ]
        elif mutation == "NESTED_VERSION2":
            view = _view_by_id(run, "mcp.eebus.v1.contract")
            view["payload"]["data"]["alternate_contracts"] = [
                {"active": True, "namespace": "eebus.v1", "version": 2}
            ]
        else:
            view = _view_by_id(run, "mcp.eebus.v1.contract")
            view["payload"]["data"]["aliases"] = ["eebus.v1.compat"]
        _refresh_view_hashes(evidence, view)
    _refresh_coexistence_evidence_identity(evidence)

    result = run_coexistence_validator(
        "report", write_json(tmp_path / "legacy-eebus.json", evidence)
    )
    assert result.returncode == 1
    assert result.stdout == "gate.scope\n"
    assert result.stderr == ""


def test_msp08_report_rejects_eebus_semantic_leaf_promotion(
    tmp_path: pathlib.Path,
) -> None:
    evidence = deepcopy(load_json(COEXISTENCE_POSITIVE))
    for run in evidence["runs"]:
        view = _view_by_id(run, "semantic.registry")
        for leaf in view["payload"]["data"]["leaves"]:
            leaf["source"] = "eebus"
        _refresh_view_hashes(evidence, view)
    _refresh_coexistence_evidence_identity(evidence)

    result = run_coexistence_validator(
        "report", write_json(tmp_path / "eebus-semantic-leaf.json", evidence)
    )
    assert result.returncode == 1
    assert result.stdout == "authority.ebus\n"
    assert result.stderr == ""


def test_msp08_report_rejects_nested_eebus_semantic_leaf_promotion(
    tmp_path: pathlib.Path,
) -> None:
    evidence = deepcopy(load_json(COEXISTENCE_POSITIVE))
    for run in evidence["runs"]:
        view = _view_by_id(run, "semantic.registry")
        view["payload"]["data"]["alternate_registry"] = {
            "leaves": [{"promotion_state": "PROMOTED", "source": "eebus"}]
        }
        _refresh_view_hashes(evidence, view)
    _refresh_coexistence_evidence_identity(evidence)

    result = run_coexistence_validator(
        "report", write_json(tmp_path / "nested-eebus-semantic-leaf.json", evidence)
    )
    assert result.returncode == 1
    assert result.stdout == "authority.ebus\n"
    assert result.stderr == ""


def test_msp08_report_rejects_nested_eebus_semantic_promotion_shape(
    tmp_path: pathlib.Path,
) -> None:
    evidence = deepcopy(load_json(COEXISTENCE_POSITIVE))
    for run in evidence["runs"]:
        view = _view_by_id(run, "semantic.registry")
        view["payload"]["data"]["alternate_registry"] = {
            "leaves": [{"promotion": {"state": "PROMOTED"}, "source": "eebus"}]
        }
        _refresh_view_hashes(evidence, view)
    _refresh_coexistence_evidence_identity(evidence)

    result = run_coexistence_validator(
        "report", write_json(tmp_path / "nested-eebus-promotion-shape.json", evidence)
    )
    assert result.returncode == 1
    assert result.stdout == "authority.ebus\n"
    assert result.stderr == ""


def test_msp08_report_rejects_nested_eebus_command_route(
    tmp_path: pathlib.Path,
) -> None:
    evidence = deepcopy(load_json(COEXISTENCE_POSITIVE))
    for run in evidence["runs"]:
        view = _view_by_id(run, "command.routing")
        view["payload"]["data"]["alternate_routes"] = [
            {"path": "/candidate/private", "source": "eebus"}
        ]
        _refresh_view_hashes(evidence, view)
    _refresh_coexistence_evidence_identity(evidence)

    result = run_coexistence_validator(
        "report", write_json(tmp_path / "nested-eebus-route.json", evidence)
    )
    assert result.returncode == 1
    assert result.stdout == "authority.ebus\n"
    assert result.stderr == ""


def test_msp08_generator_reproduces_exact_positive_artifacts(
    tmp_path: pathlib.Path,
) -> None:
    generated = tmp_path / "positive"
    result = subprocess.run(
        [
            sys.executable,
            str(COEXISTENCE_GENERATOR),
            "--output-root",
            str(generated),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == ""
    assert result.stderr == ""
    assert (generated / "evidence.json").read_bytes() == COEXISTENCE_POSITIVE.read_bytes()
    assert (generated / "report.json").read_bytes() == COEXISTENCE_GOLDEN_REPORT.read_bytes()


def test_msp08_generator_refuses_unverified_pass_report(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = importlib.util.spec_from_file_location(
        "msp08_fixture_generator_under_test", COEXISTENCE_GENERATOR
    )
    assert spec is not None and spec.loader is not None
    monkeypatch.syspath_prepend(str(REPO_ROOT / "scripts"))
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    graph = json.loads(M7_GRAPH.read_text(encoding="utf-8"))
    graph["graph_hash"] = "sha256:" + "f" * 64
    malformed_graph = tmp_path / "malformed-graph.json"
    malformed_graph.write_text(
        json.dumps(graph, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    output_root = tmp_path / "positive"
    monkeypatch.setattr(generator, "M7_GRAPH_PATH", malformed_graph)
    monkeypatch.setattr(
        sys,
        "argv",
        [str(COEXISTENCE_GENERATOR), "--output-root", str(output_root)],
    )

    with pytest.raises(generator.coexistence.Failure, match="provenance.m7"):
        generator.main()
    assert not output_root.exists()


def test_msp08_report_is_offline_under_host_variation(
    tmp_path: pathlib.Path,
) -> None:
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(tmp_path / "unavailable-home"),
        "LANG": "invalid_LOCALE",
        "LC_ALL": "C",
        "TZ": "Pacific/Kiritimati",
        "PYTHONHASHSEED": "7234",
    }
    result = subprocess.run(
        [
            sys.executable,
            str(COEXISTENCE_VALIDATOR),
            "report",
            "--evidence",
            str(COEXISTENCE_POSITIVE),
            "--registry",
            str(COEXISTENCE_REGISTRY),
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
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == COEXISTENCE_GOLDEN_REPORT.read_text(encoding="utf-8")
    assert result.stderr == ""


def test_msp08_registry_cannot_be_caller_substituted(
    tmp_path: pathlib.Path,
) -> None:
    registry = deepcopy(load_json(COEXISTENCE_REGISTRY))
    registry["protected_views"].pop()
    registry_path = write_json(tmp_path / "registry.json", registry)
    evidence = deepcopy(load_json(COEXISTENCE_POSITIVE))
    evidence["registry"]["digest"] = "sha256:" + hashlib.sha256(
        registry_path.read_bytes()
    ).hexdigest()
    evidence_path = write_json(tmp_path / "evidence.json", evidence)
    result = subprocess.run(
        [
            sys.executable,
            str(COEXISTENCE_VALIDATOR),
            "verify",
            "--evidence",
            str(evidence_path),
            "--registry",
            str(registry_path),
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
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "registry.binding\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    "name,category",
    sorted(EXPECTED_COEXISTENCE_NEGATIVE.items()),
    ids=sorted(EXPECTED_COEXISTENCE_NEGATIVE),
)
def test_msp08_mutation_classes_fail_at_one_precedence_category(
    tmp_path: pathlib.Path, name: str, category: str
) -> None:
    descriptor = load_json(COEXISTENCE_NEGATIVE_ROOT / name)
    assert descriptor["contract"] == (
        "helianthus.platform.multi-runtime-coexistence-negative-fixture.v1"
    )
    assert descriptor["fixture_id"].startswith("MSP08-G18-SYNTHETIC-NEG-")
    evidence = deepcopy(load_json(COEXISTENCE_POSITIVE))
    _apply_coexistence_mutation(evidence, descriptor["mutation"])
    result = run_coexistence_validator(
        "verify", write_json(tmp_path / name, evidence)
    )
    assert result.returncode == 1
    assert result.stdout == f"{category}\n"
    assert result.stderr == ""


def test_msp08_production_validator_has_no_test_fixture_mutation_language() -> None:
    source = COEXISTENCE_VALIDATOR.read_text(encoding="utf-8")
    for token in (
        "CANDIDATE_LEAK_EBUS_MCP",
        "DROPPED_PAYLOAD_FIELD",
        "ROLLBACK_DRIFT",
        "expand_negative_fixture",
    ):
        assert token not in source
