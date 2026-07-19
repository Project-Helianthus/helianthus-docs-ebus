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
FIXTURE_ROOT = REPO_ROOT / "docs/platform/fixtures/synchronized-evidence/v1"
VALIDATOR = REPO_ROOT / "scripts/validate_synchronized_evidence.py"
BUNDLE_SCHEMA = SCHEMA_ROOT / "synchronized-evidence-bundle-v1.schema.json"
REPLAY_SCHEMA = SCHEMA_ROOT / "synchronized-evidence-replay-v1.schema.json"
REGISTRY = SCHEMA_ROOT / "synchronized-evidence-source-registry-v1.json"
POSITIVE = FIXTURE_ROOT / "positive/bundle.json"
GOLDEN_REPLAY = FIXTURE_ROOT / "positive/replay-result.json"
NEGATIVE_ROOT = FIXTURE_ROOT / "negative"
EXPECTED_NEGATIVE = {
    "bundle-hash-mismatch.json": "hash.bundle",
    "duplicate-source-binding.json": "binding.duplicate",
    "incomplete-b509-identity.json": "schema.bundle",
    "incomplete-b524-identity.json": "schema.bundle",
    "incomplete-b555-identity.json": "schema.bundle",
    "invalid-clock-skew.json": "clock.skew",
    "privacy-ip-address.json": "privacy.prohibited",
    "runtime-pseudonym-not-remasked.json": "privacy.remask",
    "unknown-field.json": "schema.bundle",
}
EEBUS_SCHEMA_REF = "9819762a61c28eeceb11beb775aa2a91c83a68b6"
EEBUS_SCHEMA_PATH = (
    "api/_candidate/msp-06/helianthus.eebus.mcp.v1.schema.json"
)
EEBUS_SCHEMA_SHA256 = (
    "7f10fa6860e8ccee1af7f155e03d5ac208b5a6fb30518aa3145122a9a1dc0a1c"
)


def load_json(path: pathlib.Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def run_validator(command: str, bundle: pathlib.Path) -> subprocess.CompletedProcess[str]:
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


def test_machine_contract_inventory_is_complete() -> None:
    required = (
        VALIDATOR,
        BUNDLE_SCHEMA,
        REPLAY_SCHEMA,
        REGISTRY,
        POSITIVE,
        GOLDEN_REPLAY,
    )
    for path in required:
        assert path.is_file(), f"missing executable MSP-065 contract file: {path}"
    assert {path.name for path in NEGATIVE_ROOT.glob("*.json")} == set(
        EXPECTED_NEGATIVE
    )


def test_source_schema_registry_is_closed_pinned_and_self_verifying() -> None:
    registry = load_json(REGISTRY)
    assert isinstance(registry, dict)
    assert set(registry) == {"contract", "version", "entries"}
    assert registry["contract"] == "helianthus.platform.source-schema-registry.v1"
    assert registry["version"] == 1
    entries = registry["entries"]
    assert isinstance(entries, list)
    keys: set[tuple[str, str, int]] = set()
    seen_kinds: set[str] = set()
    for entry in entries:
        assert set(entry) == {
            "source_kind",
            "source_contract",
            "source_schema_version",
            "owner_repository",
            "owner_path",
            "owner_commit",
            "schema_sha256",
            "embedded_schema",
        }
        key = (
            entry["source_kind"],
            entry["source_contract"],
            entry["source_schema_version"],
        )
        assert key not in keys
        keys.add(key)
        seen_kinds.add(entry["source_kind"])
        assert len(entry["owner_commit"]) == 40
        assert len(entry["schema_sha256"]) == 64
        if entry["embedded_schema"] is not None:
            schema_path = REPO_ROOT / entry["embedded_schema"]
            assert schema_path.is_file()
            assert hashlib.sha256(schema_path.read_bytes()).hexdigest() == entry[
                "schema_sha256"
            ]
    assert {"EBUS_B509", "EBUS_B524", "EBUS_B555", "EEBUS", "CLOUD_APP"} <= seen_kinds
    eebus = next(entry for entry in entries if entry["source_kind"] == "EEBUS")
    assert eebus["owner_repository"] == "Project-Helianthus/helianthus-docs-eebus"
    assert eebus["owner_commit"] == EEBUS_SCHEMA_REF
    assert eebus["owner_path"] == EEBUS_SCHEMA_PATH
    assert eebus["schema_sha256"] == EEBUS_SCHEMA_SHA256
    protocol_paths = {
        "EBUS_B509": "protocols/vaillant/ebus-vaillant-B509.md",
        "EBUS_B524": "protocols/vaillant/ebus-vaillant-B524.md",
        "EBUS_B555": "protocols/vaillant/ebus-vaillant-b555-timer-protocol.md",
    }
    for source_kind, owner_path in protocol_paths.items():
        entry = next(row for row in entries if row["source_kind"] == source_kind)
        assert entry["owner_repository"] == "Project-Helianthus/helianthus-docs-ebus"
        assert entry["owner_path"] == owner_path
        assert entry["owner_commit"] == "e1962c0dc83836b0dbea129d198c7be6bea738da"


def test_positive_bundle_has_complete_bindings_and_remasked_eebus_evidence() -> None:
    bundle = load_json(POSITIVE)
    expected_binding_fields = {
        "runtime_kind",
        "runtime_pseudonym",
        "operation_id",
        "operation_version",
        "request_scope",
        "snapshot_scope",
        "source_kind",
        "source_contract",
        "source_schema_version",
        "owner_repository",
        "owner_path",
        "owner_commit",
        "schema_sha256",
        "capture_window",
        "mask_tier",
        "auth_scope",
        "ebus_identity",
    }
    for source in bundle["sources"]:
        assert set(source["source_binding"]) == expected_binding_fields
        assert source["source_binding"]["runtime_kind"] == source["source_kind"]
        assert source["source_binding"]["capture_window"] == bundle["capture_window"]
        assert source["source_binding"]["auth_scope"] == source["auth_scope"]
    eebus_source = next(row for row in bundle["sources"] if row["source_kind"] == "EEBUS")
    assert eebus_source["state"] == "PRESENT"
    assert len(eebus_source["artifact_ids"]) == 1
    artifact = next(row for row in bundle["artifacts"] if row["source_kind"] == "EEBUS")
    assert artifact["normalized_evidence"]["meta"]["tool"] == "eebus.v1.services.list"
    digest_paths = {
        entry["path"] for entry in artifact["remasking"]["entries"]
    }
    assert "/data/services/0/id/digest" in digest_paths


def test_positive_bundle_and_golden_replay_are_schema_valid() -> None:
    for schema, fixture in (
        (BUNDLE_SCHEMA, POSITIVE),
        (REPLAY_SCHEMA, GOLDEN_REPLAY),
    ):
        result = subprocess.run(
            ["jv", str(schema), str(fixture)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_positive_bundle_replays_to_exact_golden_bytes() -> None:
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
def test_negative_bundles_fail_with_one_category(name: str, category: str) -> None:
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
            "--bundle",
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


@pytest.mark.parametrize(
    "mutation,category",
    (
        (lambda value: value["limits"].__setitem__("max_sources", 65), "limits.exceeded"),
        (lambda value: value["sources"][0].__setitem__("state", "NOT_TESTED"), "schema.bundle"),
        (lambda value: value["evidence_refs"].reverse(), "ordering.invalid"),
    ),
    ids=("hard-limit", "terminal-state-matrix", "reference-order"),
)
def test_validator_fails_closed_on_cross_field_invariants(
    tmp_path: pathlib.Path, mutation, category: str
) -> None:
    bundle = load_json(POSITIVE)
    mutation(bundle)
    path = tmp_path / "mutated.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    result = run_validator("verify", path)
    assert result.returncode == 1
    assert result.stdout == f"{category}\n"
    assert result.stderr == ""
