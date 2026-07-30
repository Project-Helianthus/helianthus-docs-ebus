from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from copy import deepcopy
from decimal import Decimal

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_ROOT = REPO_ROOT / "docs/platform/schemas"
FIXTURE_ROOT = REPO_ROOT / "docs/platform/fixtures/synchronized-evidence/v1"
HISTORICAL_BUNDLE = FIXTURE_ROOT / "positive/bundle.json"
HISTORICAL_REPLAY = FIXTURE_ROOT / "positive/replay-result.json"
M625_ROOT = FIXTURE_ROOT / "m625/positive"
M625_BUNDLE = M625_ROOT / "bundle.json"
M625_REPLAY = M625_ROOT / "replay-result.json"
REGISTRY = SCHEMA_ROOT / "synchronized-evidence-source-registry-v1.json"
VALIDATOR = REPO_ROOT / "scripts/validate_synchronized_evidence.py"
GENERATOR = REPO_ROOT / "scripts/generate_synchronized_evidence_m625_fixture.py"
CANDIDATE_VALIDATOR = REPO_ROOT / "scripts/validate_candidate_fact_graph.py"

HISTORICAL_TUPLE = ("EEBUS", "helianthus-eebus-mcp", 1)
HISTORICAL_OWNER_COMMIT = "9819762a61c28eeceb11beb775aa2a91c83a68b6"
HISTORICAL_SCHEMA_SHA256 = (
    "7f10fa6860e8ccee1af7f155e03d5ac208b5a6fb30518aa3145122a9a1dc0a1c"
)
HISTORICAL_BUNDLE_SHA256 = (
    "e6db2862f9001148deb6f40e286ee5f1eef2907812685a9b48128ddbfca5ce5a"
)
HISTORICAL_REPLAY_SHA256 = (
    "3061c507677f1f41861c20096ff7581ccb6e35c2e01bf66a568e2277df285539"
)

M625_TUPLE = (
    "EEBUS",
    "helianthus.eebus.m625.public-redacted-evidence.v1",
    1,
)
M625_OWNER_COMMIT = "a09e3a77153204bc3117e233c71e77ef1859834e"
M625_OWNER_PATH = (
    "api/_candidate/msp-0625/"
    "helianthus.eebus.m625.public-redacted-evidence.v1.schema.json"
)
M625_SCHEMA_SHA256 = (
    "0a2885d01d6703389541e246db59bcd845a332e7ed296abca2d49b4f8de31811"
)


def load_json(path: pathlib.Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def registry_entries() -> dict[tuple[str, str, int], dict]:
    return {
        (
            entry["source_kind"],
            entry["source_contract"],
            entry["source_schema_version"],
        ): entry
        for entry in load_json(REGISTRY)["entries"]
    }


def run_validator(
    command: str, bundle: pathlib.Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            command,
            "--bundle",
            str(bundle),
            "--registry",
            str(REGISTRY),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONHASHSEED": "random"},
    )


def write_mutation(tmp_path: pathlib.Path, mutation) -> pathlib.Path:
    bundle = deepcopy(load_json(M625_BUNDLE))
    mutation(bundle)
    path = tmp_path / "mutated.json"
    path.write_text(
        json.dumps(bundle, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    return path


def eebus_source(bundle: dict) -> dict:
    return next(source for source in bundle["sources"] if source["source_kind"] == "EEBUS")


def eebus_artifact(bundle: dict) -> dict:
    return next(
        artifact for artifact in bundle["artifacts"] if artifact["source_kind"] == "EEBUS"
    )


def test_historical_tuple_and_fixture_bytes_are_immutable() -> None:
    assert hashlib.sha256(HISTORICAL_BUNDLE.read_bytes()).hexdigest() == (
        HISTORICAL_BUNDLE_SHA256
    )
    assert hashlib.sha256(HISTORICAL_REPLAY.read_bytes()).hexdigest() == (
        HISTORICAL_REPLAY_SHA256
    )
    historical = registry_entries()[HISTORICAL_TUPLE]
    assert historical["owner_commit"] == HISTORICAL_OWNER_COMMIT
    assert historical["schema_sha256"] == HISTORICAL_SCHEMA_SHA256


def test_registry_appends_exact_m625_source_authority_tuple() -> None:
    entries = registry_entries()
    assert HISTORICAL_TUPLE in entries
    m625 = entries[M625_TUPLE]
    assert m625 == {
        "source_kind": "EEBUS",
        "source_contract": M625_TUPLE[1],
        "source_schema_version": 1,
        "owner_repository": "Project-Helianthus/helianthus-docs-eebus",
        "owner_path": M625_OWNER_PATH,
        "owner_commit": M625_OWNER_COMMIT,
        "schema_sha256": M625_SCHEMA_SHA256,
        "embedded_schema": None,
    }


def test_m625_fixture_and_canonical_generator_inventory_is_complete() -> None:
    for path in (GENERATOR, M625_BUNDLE, M625_REPLAY):
        assert path.is_file(), f"missing M6.25 synchronized-evidence artifact: {path}"


def test_generator_reproduces_committed_bundle_and_replay_bytes(
    tmp_path: pathlib.Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    for output in (first, second):
        result = subprocess.run(
            [
                sys.executable,
                str(GENERATOR),
                "--output-dir",
                str(output),
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONHASHSEED": "random"},
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert result.stderr == ""
    for name, committed in (
        ("bundle.json", M625_BUNDLE),
        ("replay-result.json", M625_REPLAY),
    ):
        assert (first / name).read_bytes() == committed.read_bytes()
        assert (second / name).read_bytes() == committed.read_bytes()


def test_m625_bundle_validates_and_replays_to_exact_golden_bytes() -> None:
    verified = run_validator("verify", M625_BUNDLE)
    replayed = run_validator("replay", M625_BUNDLE)
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert verified.stdout == "ok\n"
    assert verified.stderr == ""
    assert replayed.returncode == 0, replayed.stdout + replayed.stderr
    assert replayed.stdout == M625_REPLAY.read_text(encoding="utf-8")
    assert replayed.stderr == ""


def test_m625_dispatch_preserves_complete_path_and_comparison_pointers() -> None:
    bundle = load_json(M625_BUNDLE)
    source = eebus_source(bundle)
    artifact = eebus_artifact(bundle)
    payload = artifact["normalized_evidence"]
    assert (
        source["source_contract"],
        artifact["source_contract"],
        source["source_binding"]["source_contract"],
    ) == (M625_TUPLE[1],) * 3
    assert source["source_binding"]["operation_id"] == "eebus.v1.features.data.get"

    observation = payload["observations"][0]
    path = payload["feature_paths"][observation["path_index"]]
    assert [segment["kind"] for segment in path["feature_path"]] == [
        "SERVICE",
        "ENTITY",
        "FEATURE",
        "FIELD",
    ]
    assert [segment["selector"] for segment in path["feature_path"][:3]] == [
        path["service"],
        path["entity"],
        path["feature"],
    ]
    assert observation["value"] == "21.5"
    assert observation["unit"] == "degC"

    remasked = {entry["pseudonym"] for entry in artifact["remasking"]["entries"]}
    assert {
        payload["services"][0],
        path["service"],
        path["entity"],
        path["feature"],
        path["feature_path"][3]["selector"],
    } <= remasked


@pytest.mark.parametrize(
    "mutation,category",
    (
        (
            lambda bundle: _substitute_historical_tuple(bundle),
            "schema.source",
        ),
        (
            lambda bundle: eebus_source(bundle)["source_binding"].__setitem__(
                "owner_commit", HISTORICAL_OWNER_COMMIT
            ),
            "binding.registry",
        ),
        (
            lambda bundle: eebus_artifact(bundle)["source_binding"].__setitem__(
                "schema_sha256", HISTORICAL_SCHEMA_SHA256
            ),
            "binding.registry",
        ),
        (
            lambda bundle: eebus_artifact(bundle)["normalized_evidence"].pop(
                "observations"
            ),
            "schema.source",
        ),
        (
            lambda bundle: eebus_artifact(bundle)["normalized_evidence"][
                "feature_paths"
            ][0]["feature_path"][1].__setitem__("selector", "Z" * 43),
            "schema.source",
        ),
    ),
    ids=(
        "tuple-substitution",
        "owner-mismatch",
        "schema-hash-mismatch",
        "malformed-payload",
        "incomplete-pseudonymous-path",
    ),
)
def test_m625_tuple_and_payload_mutations_fail_closed(
    tmp_path: pathlib.Path, mutation, category: str
) -> None:
    result = run_validator("verify", write_mutation(tmp_path, mutation))
    assert result.returncode == 1
    assert result.stdout == f"{category}\n"
    assert result.stderr == ""


def _substitute_historical_tuple(bundle: dict) -> None:
    historical = registry_entries()[HISTORICAL_TUPLE]
    for value in (eebus_source(bundle), eebus_artifact(bundle)):
        value["source_contract"] = HISTORICAL_TUPLE[1]
        binding = value["source_binding"]
        binding["source_contract"] = HISTORICAL_TUPLE[1]
        for field in (
            "owner_repository",
            "owner_path",
            "owner_commit",
            "schema_sha256",
        ):
            binding[field] = historical[field]
        binding["operation_id"] = "eebus.v1.services.list"
        binding["snapshot_scope"] = {"mode": "LIVE_READ", "selector": "services"}
        binding["request_scope"]["operation_scope"] = "services"


def load_candidate_validator():
    scripts = str(REPO_ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(
        "candidate_fact_m625_validator", CANDIDATE_VALIDATOR
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_candidate_fact_consumes_m625_identity_and_observation_pointers() -> None:
    module = load_candidate_validator()
    bundle = load_json(M625_BUNDLE)
    artifact = eebus_artifact(bundle)
    payload = artifact["normalized_evidence"]
    observation = payload["observations"][0]
    path = payload["feature_paths"][observation["path_index"]]
    source = eebus_source(bundle)
    provenance = {
        "ebus_source_id": None,
        "ebus_artifact_id": None,
        "ebus": None,
        "eebus_source_id": source["source_id"],
        "eebus_artifact_id": artifact["artifact_id"],
        "eebus_service": path["service"],
        "eebus": path,
    }
    module.check_identities({"facts": [{"provenance": provenance}]}, bundle)

    side = {
        "source_kind": "EEBUS",
        "source_id": source["source_id"],
        "artifact_id": artifact["artifact_id"],
        "evidence_ref": deepcopy(artifact["evidence_refs"][0]),
        "observed_offset_ns": artifact["recorder_ingested_offset_ns"],
        "value_pointer": "/observations/0/value",
        "unit_pointer": "/observations/0/unit",
        "native_decimal": "21.5",
        "native_unit": "degC",
    }
    index = {(source["source_id"], artifact["artifact_id"]): artifact}
    value, unit, offset = module._bind_observation_side(
        side, "EEBUS", index, None
    )
    assert value == Decimal("21.5")
    assert unit == "degC"
    assert offset == artifact["recorder_ingested_offset_ns"]
