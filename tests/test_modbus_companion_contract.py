from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
from collections.abc import Callable

import pytest
from scripts import validate_modbus_companion as companion_validator


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR = pathlib.Path("scripts/validate_modbus_companion.py")
MANIFEST = pathlib.Path(
    "docs/platform/manifests/modbus-foundation-profile-contract-v1.json"
)
SCHEMA = pathlib.Path(
    "docs/platform/schemas/modbus-companion-consumer-lock-v1.schema.json"
)
POLICY = pathlib.Path(
    "docs/platform/modbus-foundation-profile-contract-v1.md"
)
WIRE = pathlib.Path("protocols/modbus/modbus-phase-one-wire-v1.md")
TRUSTED_VALIDATOR = pathlib.Path(
    "scripts/validate_modbus_revision_transition.py"
)
TRUSTED_WORKFLOW = pathlib.Path(
    ".github/workflows/modbus-trusted-revision.yml"
)


def run_validator(
    root: pathlib.Path,
    *,
    prior_root: pathlib.Path | None = None,
    consumer_lock: pathlib.Path | None = None,
    docs_commit_sha: str | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        "python3",
        str(root / VALIDATOR),
        "--root",
        str(root),
    ]
    if prior_root is not None:
        command.extend(("--prior-root", str(prior_root)))
    if consumer_lock is not None:
        command.extend(("--consumer-lock", str(consumer_lock)))
    if docs_commit_sha is not None:
        command.extend(("--docs-commit-sha", docs_commit_sha))
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )


def validate_consumer_lock(
    root: pathlib.Path,
    lock_path: pathlib.Path,
    docs_commit_sha: str,
    monkeypatch: pytest.MonkeyPatch,
    *,
    canonical_contains: bool = True,
) -> list[str]:
    monkeypatch.setattr(
        companion_validator,
        "_canonical_main_contains",
        lambda _sha, _errors: canonical_contains,
    )
    errors, _ = companion_validator.validate(
        root.resolve(),
        consumer_lock=lock_path.resolve(),
        docs_commit_sha=docs_commit_sha,
    )
    return errors


def materialize_fixture(tmp_path: pathlib.Path) -> pathlib.Path:
    for relative in (
        VALIDATOR,
        MANIFEST,
        SCHEMA,
        POLICY,
        TRUSTED_VALIDATOR,
        TRUSTED_WORKFLOW,
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


def make_consumer_lock(
    root: pathlib.Path,
    *,
    docs_commit_sha: str = "a" * 40,
) -> dict[str, object]:
    manifest = load_manifest(root)
    return {
        "schema": "helianthus.modbus.companion-consumer-lock",
        "schema_version": 1,
        "repository": manifest["repository"],
        "merged_commit_sha": docs_commit_sha,
        "contract_id": manifest["contract_id"],
        "contract_version": manifest["version"],
        "content_revision": manifest["content_revision"],
        "manifest_sha256": hashlib.sha256(
            (root / MANIFEST).read_bytes()
        ).hexdigest(),
    }


def write_consumer_lock(
    root: pathlib.Path,
    value: dict[str, object],
) -> pathlib.Path:
    path = root.parent / f"{root.name}-consumer-lock.json"
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def initialize_git_checkout(root: pathlib.Path) -> str:
    subprocess.run(
        ["git", "init", "-q", str(root)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "user.name", "Contract Test"],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "config",
            "user.email",
            "contract-test@example.invalid",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "add", "."],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "commit", "-q", "-m", "fixture"],
        check=True,
        capture_output=True,
        text=True,
    )
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "remote",
            "add",
            "origin",
            "https://github.com/Project-Helianthus/helianthus-docs-ebus.git",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "update-ref",
            "refs/remotes/origin/main",
            head,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return head


def test_repository_modbus_companion_contract_is_valid() -> None:
    result = run_validator(REPO_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "modbus_companion_contract_ok" in result.stdout


def test_new_contract_revision_one_accepts_trusted_base_without_manifest(
    tmp_path: pathlib.Path,
) -> None:
    root = materialize_fixture(tmp_path / "current")
    prior_root = tmp_path / "prior"
    prior_root.mkdir()
    result = run_validator(root, prior_root=prior_root)
    assert result.returncode == 0, result.stdout + result.stderr


def test_valid_consumer_lock_matches_exact_docs_checkout(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = materialize_fixture(tmp_path)
    docs_commit_sha = initialize_git_checkout(root)
    lock_path = write_consumer_lock(
        root,
        make_consumer_lock(root, docs_commit_sha=docs_commit_sha),
    )
    errors = validate_consumer_lock(
        root,
        lock_path,
        docs_commit_sha,
        monkeypatch,
    )
    assert errors == []


def test_consumer_lock_rejects_untracked_docs_content(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = materialize_fixture(tmp_path / "docs")
    docs_commit_sha = initialize_git_checkout(root)
    (root / "untracked.txt").write_text("not canonical\n", encoding="utf-8")
    lock_path = write_consumer_lock(
        root,
        make_consumer_lock(root, docs_commit_sha=docs_commit_sha),
    )
    errors = validate_consumer_lock(
        root,
        lock_path,
        docs_commit_sha,
        monkeypatch,
    )
    assert any("tracked or untracked modifications" in error for error in errors)


def test_consumer_lock_rejects_commit_not_on_canonical_main(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = materialize_fixture(tmp_path / "docs")
    initialize_git_checkout(root)
    readme = root / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8") + "\nPR-only commit.\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "-C", str(root), "add", "README.md"],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "commit", "-q", "-m", "pr-only"],
        check=True,
        capture_output=True,
        text=True,
    )
    docs_commit_sha = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    lock_path = write_consumer_lock(
        root,
        make_consumer_lock(root, docs_commit_sha=docs_commit_sha),
    )
    errors = validate_consumer_lock(
        root,
        lock_path,
        docs_commit_sha,
        monkeypatch,
        canonical_contains=False,
    )
    assert "locked docs commit is not on canonical GitHub main" in errors


def test_canonical_main_fetch_uses_fixed_https_and_fresh_ref(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(companion_validator.subprocess, "run", fake_run)
    errors: list[str] = []
    assert companion_validator._canonical_main_contains("a" * 40, errors)
    assert errors == []
    fetch_command, fetch_options = calls[1]
    assert companion_validator.CANONICAL_REPOSITORY_URL in fetch_command
    assert (
        "+refs/heads/main:"
        + companion_validator.CANONICAL_MAIN_REF
    ) in fetch_command
    fetch_env = fetch_options["env"]
    assert isinstance(fetch_env, dict)
    assert fetch_env["GIT_CONFIG_GLOBAL"] == os.devnull
    assert fetch_env["GIT_CONFIG_SYSTEM"] == os.devnull


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


def mutate_extra_schema_key(
    _root: pathlib.Path, manifest: dict[str, object]
) -> None:
    manifest["extension"] = "not-allowed"


def mutate_source_policy(
    _root: pathlib.Path, manifest: dict[str, object]
) -> None:
    policy = manifest["source_policy"]
    assert isinstance(policy, dict)
    policy["restricted_source_copy"] = "allowed"


def mutate_hard_stop(
    _root: pathlib.Path, manifest: dict[str, object]
) -> None:
    execution = manifest["execution"]
    assert isinstance(execution, dict)
    execution["hard_stop_before"] = "FMV3-M5-01"


def mutate_read_only_type(
    _root: pathlib.Path, manifest: dict[str, object]
) -> None:
    manifest["read_only"] = 1


def refresh_policy_hash(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    hashes = manifest["artifact_sha256"]
    assert isinstance(hashes, dict)
    hashes["policy"] = hashlib.sha256((root / POLICY).read_bytes()).hexdigest()


def mutate_contradict_tombstone_and_rehash(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    policy = root / POLICY
    text = policy.read_text(encoding="utf-8")
    original = (
        "A tombstoned\nidentifier MUST NOT be reused on that socket."
    )
    replacement = "A tombstoned identifier MAY be reused immediately."
    assert original in text
    policy.write_text(text.replace(original, replacement), encoding="utf-8")
    refresh_policy_hash(root, manifest)


def mutate_unrecognized_wire_fact_and_rehash(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    policy = root / POLICY
    policy.write_text(
        policy.read_text(encoding="utf-8")
        + "\nThe MBAP length includes the unit and PDU.\n",
        encoding="utf-8",
    )
    refresh_policy_hash(root, manifest)


def mutate_policy_hash(
    _root: pathlib.Path, manifest: dict[str, object]
) -> None:
    hashes = manifest["artifact_sha256"]
    assert isinstance(hashes, dict)
    hashes["policy"] = "0" * 64


def mutate_admission_reservation_row_and_rehash(
    root: pathlib.Path, manifest: dict[str, object]
) -> None:
    policy = root / POLICY
    text = policy.read_text(encoding="utf-8")
    original = (
        "| one admission key exhausts its protected and shared capacity | "
        "another key still activates, admits its protected request, and "
        "receives round-robin service |"
    )
    assert original in text
    policy.write_text(
        text.replace(
            original,
            "| one admission key exhausts endpoint capacity | reject all peers |",
        ),
        encoding="utf-8",
    )
    refresh_policy_hash(root, manifest)


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
        mutate_extra_schema_key,
        mutate_source_policy,
        mutate_hard_stop,
        mutate_read_only_type,
        mutate_contradict_tombstone_and_rehash,
        mutate_unrecognized_wire_fact_and_rehash,
        mutate_policy_hash,
        mutate_admission_reservation_row_and_rehash,
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


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("schema", "helianthus.modbus.other-lock"),
        ("schema_version", 2),
        ("repository", "Project-Helianthus/other"),
        ("merged_commit_sha", "a" * 12),
        ("contract_id", "OTHER_CONTRACT"),
        ("contract_version", 2),
        ("content_revision", 2),
        ("manifest_sha256", "0" * 64),
    ),
)
def test_consumer_lock_mutations_fail_closed(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    key: str,
    value: object,
) -> None:
    root = materialize_fixture(tmp_path)
    docs_commit_sha = initialize_git_checkout(root)
    lock = make_consumer_lock(root, docs_commit_sha=docs_commit_sha)
    lock[key] = value
    lock_path = write_consumer_lock(root, lock)
    errors = validate_consumer_lock(
        root,
        lock_path,
        docs_commit_sha,
        monkeypatch,
    )
    assert errors


def test_consumer_lock_additional_key_fails_closed(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = materialize_fixture(tmp_path)
    docs_commit_sha = initialize_git_checkout(root)
    lock = make_consumer_lock(root, docs_commit_sha=docs_commit_sha)
    lock["moving_ref"] = "main"
    lock_path = write_consumer_lock(root, lock)
    errors = validate_consumer_lock(
        root,
        lock_path,
        docs_commit_sha,
        monkeypatch,
    )
    assert "consumer lock keys must match the closed schema" in errors


def test_coordinated_hash_edit_without_revision_bump_fails_against_prior(
    tmp_path: pathlib.Path,
) -> None:
    prior_root = materialize_fixture(tmp_path / "prior")
    current_root = materialize_fixture(tmp_path / "current")
    manifest = load_manifest(current_root)
    policy = current_root / POLICY
    policy.write_text(
        policy.read_text(encoding="utf-8")
        + "\nA weakened coordinated policy edit.\n",
        encoding="utf-8",
    )
    refresh_policy_hash(current_root, manifest)
    write_manifest(current_root, manifest)

    old_hashes = load_manifest(prior_root)["artifact_sha256"]
    new_hashes = manifest["artifact_sha256"]
    assert isinstance(old_hashes, dict)
    assert isinstance(new_hashes, dict)
    old_policy_hash = old_hashes["policy"]
    new_policy_hash = new_hashes["policy"]
    assert isinstance(old_policy_hash, str)
    assert isinstance(new_policy_hash, str)
    validator = current_root / VALIDATOR
    validator_text = validator.read_text(encoding="utf-8")
    assert old_policy_hash in validator_text
    validator.write_text(
        validator_text.replace(old_policy_hash, new_policy_hash),
        encoding="utf-8",
    )

    result = run_validator(current_root, prior_root=prior_root)
    assert result.returncode != 0
    assert "normative artifact changes require exactly" in result.stderr
