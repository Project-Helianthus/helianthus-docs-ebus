"""Contract tests for the pull-request heavy-suite input classifier."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/ci_suite_inputs.py"
MANIFEST = ROOT / "scripts/ci_suite_inputs.json"
GATE = ROOT / "scripts/ci_local.sh"
BLOCK_START = re.compile(r"^if ! ci_suite_unchanged ([a-z0-9_]+); then$")

spec = importlib.util.spec_from_file_location("ci_suite_inputs", SCRIPT)
classifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classifier)


def gated_blocks() -> dict[str, set[str]]:
    """Map each suite used in the gate to the test modules its blocks run."""
    blocks: dict[str, set[str]] = {}
    current = None
    for line in GATE.read_text(encoding="utf-8").splitlines():
        start = BLOCK_START.match(line)
        if start:
            assert current is None, "nested suite block"
            current = start.group(1)
            blocks.setdefault(current, set())
            continue
        if current is not None and line == "fi":
            current = None
            continue
        if current is not None:
            blocks[current].update(re.findall(r"tests/test_[A-Za-z0-9_]+\.py", line))
    assert current is None, "unterminated suite block"
    return blocks


def tracked_files() -> list[str]:
    output = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                            text=True, check=True).stdout
    return output.splitlines()


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def trees(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "version": 1,
        "shared_inputs": ["scripts/**", "requirements-ci.txt"],
        "suites": {
            "alpha": {"inputs": ["tests/test_alpha.py", "api/alpha.md", "fixtures/alpha-*"]},
            "beta": {"inputs": ["tests/test_beta.py", "docs/beta/**"]},
        },
    }), encoding="utf-8")
    base, head = tmp_path / "base", tmp_path / "head"
    for root in (base, head):
        write(root, "scripts/ci_local.sh", "gate\n")
        write(root, "requirements-ci.txt", "pins\n")
        write(root, "tests/test_alpha.py", "alpha test\n")
        write(root, "api/alpha.md", "alpha page\n")
        write(root, "fixtures/alpha-1.json", "{}\n")
        write(root, "tests/test_beta.py", "beta test\n")
        write(root, "docs/beta/nested/page.md", "beta page\n")
        write(root, "protocols/vendor/page.md", "unrelated page\n")
    return base, head, manifest


def unchanged(trees) -> list[str]:
    base, head, manifest = trees
    return classifier.unchanged_suites(base, head, manifest)


def test_identical_trees_list_every_suite(trees):
    assert unchanged(trees) == ["alpha", "beta"]


def test_unrelated_page_change_lists_every_suite(trees):
    _, head, _ = trees
    write(head, "protocols/vendor/page.md", "changed unrelated page\n")
    write(head, "protocols/vendor/new-page.md", "new unrelated page\n")
    assert unchanged(trees) == ["alpha", "beta"]


@pytest.mark.parametrize("relative", [
    "tests/test_alpha.py", "api/alpha.md", "fixtures/alpha-1.json",
])
def test_changed_suite_input_runs_that_suite(trees, relative):
    _, head, _ = trees
    write(head, relative, "changed\n")
    assert unchanged(trees) == ["beta"]


def test_added_and_deleted_inputs_count_as_changes(trees):
    base, head, _ = trees
    write(head, "fixtures/alpha-2.json", "{}\n")
    assert unchanged(trees) == ["beta"]
    (head / "fixtures/alpha-2.json").unlink()
    (base / "docs/beta/nested/page.md").unlink()
    assert unchanged(trees) == ["alpha"]


@pytest.mark.parametrize("relative", ["scripts/ci_local.sh", "scripts/new_helper.py",
                                      "requirements-ci.txt"])
def test_shared_input_change_runs_every_suite(trees, relative):
    _, head, _ = trees
    write(head, relative, "changed\n")
    assert unchanged(trees) == []


def test_interpreter_caches_are_not_inputs(trees):
    _, head, _ = trees
    write(head, "scripts/__pycache__/ci_suite_inputs.cpython-312.pyc", "cache\n")
    write(head, "tests/__pycache__/test_alpha.cpython-312.pyc", "cache\n")
    write(head, ".pytest_cache/v/cache/lastfailed", "{}\n")
    assert unchanged(trees) == ["alpha", "beta"]


def test_cli_prints_suites_and_fails_closed(trees, tmp_path):
    base, head, manifest = trees
    ok = subprocess.run([sys.executable, str(SCRIPT), "--base", str(base), "--head", str(head),
                         "--manifest", str(manifest)], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    assert ok.stdout == "alpha beta\n"
    missing = subprocess.run([sys.executable, str(SCRIPT), "--base", str(tmp_path / "absent"),
                              "--head", str(head), "--manifest", str(manifest)],
                             capture_output=True, text=True)
    assert missing.returncode == 2 and missing.stdout == ""
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps({"version": 1, "shared_inputs": ["../x"],
                                  "suites": {"alpha": {"inputs": ["a"]}}}), encoding="utf-8")
    invalid = subprocess.run([sys.executable, str(SCRIPT), "--base", str(base), "--head", str(head),
                              "--manifest", str(broken)], capture_output=True, text=True)
    assert invalid.returncode == 2 and invalid.stdout == ""


def test_manifest_suites_match_gate_blocks():
    _, suites = classifier.load_manifest(MANIFEST)
    blocks = gated_blocks()
    assert set(blocks) == set(suites)
    for suite_id, modules in blocks.items():
        assert modules, f"{suite_id}: block runs no test module"
        missing = sorted(modules - set(suites[suite_id]))
        assert not missing, f"{suite_id}: gated modules missing from its inputs: {missing}"


def test_manifest_paths_name_tracked_files():
    shared, suites = classifier.load_manifest(MANIFEST)
    files = tracked_files()
    for pattern in [p for inputs in suites.values() for p in inputs]:
        if any(ch in pattern for ch in "*?["):
            assert any(classifier.matches(path, pattern) for path in files), pattern
        else:
            assert pattern in files, f"{pattern} is not a tracked file"
    assert "scripts/**" in shared
    assert "requirements-ci.txt" in shared
    assert ".github/workflows/**" in shared


def test_gate_and_workflow_keep_full_runs_outside_same_repository_pull_requests():
    gate = GATE.read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/docs-ci.yml").read_text(encoding="utf-8")
    assert '  case " ${CI_UNCHANGED_SUITES:-} " in\n' in gate
    assert "CI_UNCHANGED_SUITES: ${{ steps.suite_inputs.outputs.unchanged }}" in workflow
    assert ("if: github.event_name == 'pull_request' && "
            "github.event.pull_request.head.repo.full_name == github.repository") in workflow
    assert 'classifier="${base_root}/scripts/ci_suite_inputs.py"' in workflow


def helper_source() -> str:
    gate = GATE.read_text(encoding="utf-8")
    start = gate.index("ci_suite_unchanged() {\n")
    end = gate.index("\n}\n", start) + 3
    return gate[start:end]


@pytest.mark.parametrize(("listed", "suite", "skipped"), [
    ("portal_ux b503_milestones", "portal_ux", True),
    ("portal_ux b503_milestones", "b503_milestones", True),
    ("portal_ux", "portal", False),
    ("portal_ux_extra", "portal_ux", False),
    ("", "portal_ux", False),
])
def test_gate_helper_skips_only_listed_suites(listed, suite, skipped):
    script = helper_source() + f'if ci_suite_unchanged {suite}; then echo SKIP; else echo RUN; fi\n'
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                            env={"PATH": os.defpath, "CI_UNCHANGED_SUITES": listed})
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[-1] == ("SKIP" if skipped else "RUN")
    if skipped:
        assert f"Skipping the {suite} suite" in result.stdout
