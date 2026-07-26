from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import subprocess


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "scripts/validate_modbus_revision_transition.py"
WORKFLOW = REPO_ROOT / ".github/workflows/modbus-trusted-revision.yml"
MANIFEST = pathlib.Path(
    "docs/platform/manifests/modbus-foundation-profile-contract-v1.json"
)


def materialize(root: pathlib.Path) -> pathlib.Path:
    manifest = json.loads((REPO_ROOT / MANIFEST).read_text(encoding="utf-8"))
    relative_paths = [MANIFEST]
    artifacts = manifest["artifacts"]
    assert isinstance(artifacts, dict)
    relative_paths.extend(pathlib.Path(path) for path in artifacts.values())
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
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "python3",
            str(VALIDATOR),
            "--prior-root",
            str(prior_root),
            "--current-root",
            str(current_root),
        ],
        check=False,
        capture_output=True,
        text=True,
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
    result = run_validator(prior, current)
    assert result.returncode == 0, result.stdout + result.stderr


def test_workflow_executes_only_base_owned_transition_code() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request_target:" in text
    assert "ref: ${{ github.event.pull_request.base.sha }}" in text
    assert "python3 trusted/scripts/validate_modbus_revision_transition.py" in text
    assert "python3 current/" not in text


def test_unchanged_contract_retains_revision(tmp_path: pathlib.Path) -> None:
    prior = materialize(tmp_path / "prior")
    current = materialize(tmp_path / "current")
    result = run_validator(prior, current)
    assert result.returncode == 0, result.stdout + result.stderr


def test_policy_change_without_revision_bump_fails(
    tmp_path: pathlib.Path,
) -> None:
    prior = materialize(tmp_path / "prior")
    current = materialize(tmp_path / "current")
    manifest = load_manifest(current)
    mutate_policy(current, manifest)
    write_manifest(current, manifest)
    result = run_validator(prior, current)
    assert result.returncode != 0
    assert "require exactly the next" in result.stderr


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
    result = run_validator(prior, current)
    assert result.returncode != 0
    assert "require exactly the next" in result.stderr


def test_changed_contract_with_exact_revision_bump_passes(
    tmp_path: pathlib.Path,
) -> None:
    prior = materialize(tmp_path / "prior")
    current = materialize(tmp_path / "current")
    manifest = load_manifest(current)
    mutate_policy(current, manifest)
    bump_revision(manifest)
    write_manifest(current, manifest)
    result = run_validator(prior, current)
    assert result.returncode == 0, result.stdout + result.stderr


def test_contract_removal_fails(tmp_path: pathlib.Path) -> None:
    prior = materialize(tmp_path / "prior")
    current = tmp_path / "current"
    current.mkdir()
    result = run_validator(prior, current)
    assert result.returncode != 0
    assert "cannot be removed" in result.stderr
