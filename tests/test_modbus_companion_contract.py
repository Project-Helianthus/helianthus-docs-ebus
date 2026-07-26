from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
from collections.abc import Callable

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR = pathlib.Path("scripts/validate_modbus_companion.py")
MANIFEST = pathlib.Path(
    "docs/platform/manifests/modbus-foundation-profile-contract-v1.json"
)
POLICY = pathlib.Path(
    "docs/platform/modbus-foundation-profile-contract-v1.md"
)
WIRE = pathlib.Path("protocols/modbus/modbus-phase-one-wire-v1.md")


def run_validator(root: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "python3",
            str(root / VALIDATOR),
            "--root",
            str(root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def materialize_fixture(tmp_path: pathlib.Path) -> pathlib.Path:
    for relative in (
        VALIDATOR,
        MANIFEST,
        POLICY,
        WIRE,
        pathlib.Path("README.md"),
        pathlib.Path("protocols/LICENSE"),
    ):
        source = REPO_ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return tmp_path


def load_manifest(root: pathlib.Path) -> dict[str, object]:
    return json.loads((root / MANIFEST).read_text(encoding="utf-8"))


def write_manifest(root: pathlib.Path, value: dict[str, object]) -> None:
    (root / MANIFEST).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_repository_modbus_companion_contract_is_valid() -> None:
    result = run_validator(REPO_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "modbus_companion_contract_ok" in result.stdout


Mutation = Callable[[pathlib.Path, dict[str, object]], None]


def mutate_wire_license(
    _root: pathlib.Path, manifest: dict[str, object]
) -> None:
    licenses = manifest["licenses"]
    assert isinstance(licenses, dict)
    licenses["wire"] = "AGPL-3.0"


def mutate_remove_operation(
    _root: pathlib.Path, manifest: dict[str, object]
) -> None:
    operations = manifest["phase1_operations"]
    assert isinstance(operations, list)
    operations.pop()


def mutate_policy_path(
    _root: pathlib.Path, manifest: dict[str, object]
) -> None:
    artifacts = manifest["artifacts"]
    assert isinstance(artifacts, dict)
    artifacts["wire"] = POLICY.as_posix()


def mutate_remove_recovery_row(
    _root: pathlib.Path, manifest: dict[str, object]
) -> None:
    rows = manifest["transport_recovery_rows"]
    assert isinstance(rows, list)
    rows.pop()


def mutate_remove_companion(
    _root: pathlib.Path, manifest: dict[str, object]
) -> None:
    companions = manifest["companion_for"]
    assert isinstance(companions, list)
    companions.pop()


def mutate_remove_consumer_pin(
    _root: pathlib.Path, manifest: dict[str, object]
) -> None:
    pin = manifest["consumer_pin"]
    assert isinstance(pin, dict)
    pin.pop("merged_commit_sha")


def mutate_agpl_wire_fact(
    root: pathlib.Path, _manifest: dict[str, object]
) -> None:
    policy = root / POLICY
    policy.write_text(
        policy.read_text(encoding="utf-8")
        + "\nCRC polynomial `0xA001`.\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "mutation",
    (
        mutate_wire_license,
        mutate_remove_operation,
        mutate_policy_path,
        mutate_remove_recovery_row,
        mutate_remove_companion,
        mutate_remove_consumer_pin,
        mutate_agpl_wire_fact,
    ),
)
def test_modbus_companion_mutations_fail_closed(
    tmp_path: pathlib.Path, mutation: Mutation
) -> None:
    root = materialize_fixture(tmp_path)
    manifest = load_manifest(root)
    mutation(root, manifest)
    write_manifest(root, manifest)
    result = run_validator(root)
    assert result.returncode != 0
    assert "modbus_companion_contract_invalid" in result.stderr
