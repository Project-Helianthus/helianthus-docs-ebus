from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import re
import shutil
from typing import Any

import pytest

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


PR_WORKFLOW = REPO_ROOT / ".github/workflows/modbus-trusted-revision-pr.yml"
STATUS_JOB_NAME = "Modbus Trusted Revision"
PR_WORKFLOW_NAME = "Modbus Trusted Revision (pull_request)"
YAML_JOB_NAME_LINE = re.compile(
    r"""^\s*name:\s*["']?Modbus Trusted Revision["']?\s*$""",
    re.MULTILINE,
)


def load_workflow(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_pull_request_workflow(protected: dict[str, Any]) -> dict[str, Any]:
    expected = copy.deepcopy(protected)
    assert set(expected["on"]) == {"pull_request_target"}
    expected["name"] = PR_WORKFLOW_NAME
    expected["on"] = {"pull_request": expected["on"]["pull_request_target"]}
    return expected


def status_producers(directory: pathlib.Path) -> list[str]:
    producers: list[str] = []
    paths = sorted([*directory.glob("*.yml"), *directory.glob("*.yaml")])
    for path in paths:
        raw = path.read_text(encoding="utf-8")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            if YAML_JOB_NAME_LINE.search(raw) is not None:
                producers.append(path.name)
            continue
        jobs = parsed.get("jobs", {}) if isinstance(parsed, dict) else {}
        if any(
            isinstance(job, dict) and job.get("name") == STATUS_JOB_NAME
            for job in jobs.values()
        ):
            producers.append(path.name)
    return producers


def anchor_ref(workflow: dict[str, object]) -> str:
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    refs = [
        step["with"]["ref"]
        for job in jobs.values()
        for step in job["steps"]
        if step.get("with", {}).get("path") == "anchor"
    ]
    assert len(refs) == 1
    return refs[0]


def test_pull_request_workflow_is_canonical_sorted_json() -> None:
    raw = PR_WORKFLOW.read_bytes()
    parsed = json.loads(raw.decode("utf-8"))
    canonical = json.dumps(parsed, indent=2, sort_keys=True) + "\n"
    assert raw == canonical.encode("utf-8")


def test_pull_request_workflow_equals_protected_except_name_and_trigger() -> None:
    expected = expected_pull_request_workflow(load_workflow(WORKFLOW))
    assert load_workflow(PR_WORKFLOW) == expected


@pytest.mark.parametrize(
    "mutation",
    [
        "top_level_env",
        "top_level_defaults",
        "top_level_concurrency",
        "changed_step",
        "added_step_env",
        "added_trigger",
        "changed_trigger_types",
    ],
)
def test_whole_document_comparison_rejects_any_other_difference(
    tmp_path: pathlib.Path, mutation: str
) -> None:
    candidate = load_workflow(PR_WORKFLOW)
    steps = candidate["jobs"]["trusted-revision"]["steps"]
    if mutation == "top_level_env":
        candidate["env"] = {"PYTHONPATH": "current"}
    elif mutation == "top_level_defaults":
        candidate["defaults"] = {"run": {"working-directory": "current"}}
    elif mutation == "top_level_concurrency":
        candidate["concurrency"] = {"group": "status", "cancel-in-progress": True}
    elif mutation == "changed_step":
        steps[-1]["run"] = "true"
    elif mutation == "added_step_env":
        steps[-1]["env"] = {"PYTHONPATH": "current"}
    elif mutation == "added_trigger":
        candidate["on"]["workflow_dispatch"] = {}
    else:
        candidate["on"]["pull_request"]["types"].append("edited")
    mutated = tmp_path / PR_WORKFLOW.name
    mutated.write_text(
        json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    expected = expected_pull_request_workflow(load_workflow(WORKFLOW))
    unchanged = tmp_path / "unchanged.yml"
    shutil.copy2(PR_WORKFLOW, unchanged)
    assert load_workflow(unchanged) == expected
    assert load_workflow(mutated) != expected


def test_only_the_two_known_workflows_produce_the_status_job() -> None:
    """YAML is matched by a line expression: it finds plain literal names only."""
    assert status_producers(REPO_ROOT / ".github/workflows") == [
        "modbus-trusted-revision-pr.yml",
        "modbus-trusted-revision.yml",
    ]


def test_status_producer_detection_finds_json_and_yaml_jobs(
    tmp_path: pathlib.Path,
) -> None:
    shutil.copy2(WORKFLOW, tmp_path / WORKFLOW.name)
    (tmp_path / "other.yaml").write_text(
        "jobs:\n  x:\n    name: 'Modbus Trusted Revision'\n",
        encoding="utf-8",
    )
    (tmp_path / "unrelated.yml").write_text(
        "jobs:\n  x:\n    name: Docs Checks\n",
        encoding="utf-8",
    )
    renamed = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    renamed["jobs"]["trusted-revision"]["name"] = "Docs Checks"
    (tmp_path / "renamed.yml").write_text(json.dumps(renamed), encoding="utf-8")
    assert status_producers(tmp_path) == [
        WORKFLOW.name,
        "other.yaml",
    ]


def test_both_workflows_pin_the_manifest_trust_anchor() -> None:
    manifest = load_manifest(REPO_ROOT)
    trust_anchor = manifest["trust_anchor"]
    assert isinstance(trust_anchor, dict)
    expected = trust_anchor["commit_sha"]
    for path in (WORKFLOW, PR_WORKFLOW):
        workflow = json.loads(path.read_text(encoding="utf-8"))
        assert anchor_ref(workflow) == expected
