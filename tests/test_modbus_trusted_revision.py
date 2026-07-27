from __future__ import annotations

import hashlib
import json
import pathlib
import shutil

from scripts import validate_modbus_revision_transition as transition_validator

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "scripts/validate_modbus_revision_transition.py"
WORKFLOW = REPO_ROOT / ".github/workflows/modbus-trusted-revision.yml"
SEMANTIC_VALIDATOR = REPO_ROOT / "scripts/validate_modbus_companion.py"
MANIFEST = pathlib.Path(
    "docs/platform/manifests/modbus-foundation-profile-contract-v1.json"
)
ANCHOR_SHA = "e633fa22a6a6fe3e4f3b74a68eb44401fe26f38d"


def materialize(root: pathlib.Path) -> pathlib.Path:
    manifest = json.loads((REPO_ROOT / MANIFEST).read_text(encoding="utf-8"))
    relative_paths = [MANIFEST]
    artifacts = manifest["artifacts"]
    assert isinstance(artifacts, dict)
    relative_paths.extend(pathlib.Path(path) for path in artifacts.values())
    relative_paths.append(
        SEMANTIC_VALIDATOR.relative_to(REPO_ROOT)
    )
    for relative in relative_paths:
        source = REPO_ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return root


def load_manifest(root: pathlib.Path) -> dict[str, object]:
    return json.loads((root / MANIFEST).read_text(encoding="utf-8"))


def write_manifest(root: pathlib.Path, manifest: dict[str, object]) -> None:
    (root / MANIFEST).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_validator(
    prior_root: pathlib.Path,
    current_root: pathlib.Path,
) -> list[str]:
    return transition_validator.validate_transition(
        prior_root.resolve(),
        current_root.resolve(),
        ANCHOR_SHA,
    )


def mutate_policy(
    root: pathlib.Path,
    manifest: dict[str, object],
) -> None:
    artifacts = manifest["artifacts"]
    hashes = manifest["artifact_sha256"]
    assert isinstance(artifacts, dict)
    assert isinstance(hashes, dict)
    policy = root / str(artifacts["policy"])
    policy.write_text(
        policy.read_text(encoding="utf-8") + "\nNormative mutation.\n",
        encoding="utf-8",
    )
    hashes["policy"] = hashlib.sha256(policy.read_bytes()).hexdigest()


def bump_revision(manifest: dict[str, object]) -> None:
    manifest["content_revision"] = 2
    consumer_pin = manifest["consumer_pin"]
    assert isinstance(consumer_pin, dict)
    consumer_pin["content_revision"] = 2


def test_first_contract_starts_at_revision_one(tmp_path: pathlib.Path) -> None:
    prior = tmp_path / "prior"
    prior.mkdir()
    current = materialize(tmp_path / "current")
    assert run_validator(prior, current) == []


def test_workflow_executes_only_base_owned_transition_code() -> None:
    workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    assert workflow == transition_validator.expected_workflow(ANCHOR_SHA)
    manifest = load_manifest(REPO_ROOT)
    hashes = manifest["artifact_sha256"]
    assert isinstance(hashes, dict)
    assert hashlib.sha256(VALIDATOR.read_bytes()).hexdigest() == (
        hashes["trusted_revision_validator"]
    )


def test_unchanged_contract_retains_revision(tmp_path: pathlib.Path) -> None:
    prior = materialize(tmp_path / "prior")
    current = materialize(tmp_path / "current")
    assert run_validator(prior, current) == []


def test_policy_change_without_revision_bump_fails(
    tmp_path: pathlib.Path,
) -> None:
    prior = materialize(tmp_path / "prior")
    current = materialize(tmp_path / "current")
    manifest = load_manifest(current)
    mutate_policy(current, manifest)
    write_manifest(current, manifest)
    errors = run_validator(prior, current)
    assert any("require exactly the next" in error for error in errors)


def test_manifest_change_without_revision_bump_fails(
    tmp_path: pathlib.Path,
) -> None:
    prior = materialize(tmp_path / "prior")
    current = materialize(tmp_path / "current")
    manifest = load_manifest(current)
    source_policy = manifest["source_policy"]
    assert isinstance(source_policy, dict)
    source_policy["restricted_source_copy"] = "allowed"
    write_manifest(current, manifest)
    errors = run_validator(prior, current)
    assert any("require exactly the next" in error for error in errors)


def test_changed_contract_with_revision_bump_requires_new_external_anchor(
    tmp_path: pathlib.Path,
) -> None:
    prior = materialize(tmp_path / "prior")
    current = materialize(tmp_path / "current")
    manifest = load_manifest(current)
    mutate_policy(current, manifest)
    bump_revision(manifest)
    write_manifest(current, manifest)
    assert (
        "current manifest is not the independently frozen V1 contract"
        in run_validator(prior, current)
    )


def test_contract_removal_fails(tmp_path: pathlib.Path) -> None:
    prior = materialize(tmp_path / "prior")
    current = tmp_path / "current"
    current.mkdir()
    errors = run_validator(prior, current)
    assert "the Modbus companion manifest cannot be removed" in errors
