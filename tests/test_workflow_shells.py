"""Focused coverage for the local workflow lint split."""

import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("workflow_shells", ROOT / "scripts/check_workflow_shells.py")
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)


def test_current_workflows_include_original_19_and_all_21_steps(tmp_path):
    workflows = sorted((ROOT / ".github/workflows").glob("*.y*ml"))
    extracted = list(lint.scripts(workflows))
    original = [path for path in workflows if path.name in (
        "docs-ci.yml", "platform-contracts-combined-ref.yml")]
    assert len(list(lint.scripts(original))) == 19
    assert len(extracted) == 21
    assert all(dialect == "bash" for _, dialect, _ in extracted)
    assert all("${{" not in source for _, _, source in extracted)
    assert lint.shellcheck(workflows, tmp_path) == 0


def test_broken_workflow_snippet_fails(tmp_path):
    workflow = tmp_path / "broken.yml"
    workflow.write_text("jobs:\n  check:\n    steps:\n      - run: echo $unquoted\n")
    assert lint.shellcheck([workflow], tmp_path) == 1  # SC2086, despite SC2154 exclusion


@pytest.mark.parametrize(("step_shell", "job_shell", "workflow_shell", "runner", "expected"), [
    ("sh -e {0}", "bash", "bash", "ubuntu-latest", "sh"),
    ("", "sh", "bash", "ubuntu-latest", "sh"),
    ("", "", "sh", "ubuntu-latest", "sh"),
    ("", "", "", "ubuntu-latest", "bash"),
    ("", "", "", "windows-latest", None),
    ("python", "", "", "ubuntu-latest", None),
])
def test_shell_precedence(tmp_path, step_shell, job_shell, workflow_shell, runner, expected):
    workflow = tmp_path / "shell.yml"
    workflow.write_text(lint.yaml.safe_dump({
        "defaults": {"run": {"shell": workflow_shell}},
        "jobs": {"check": {
            "runs-on": runner,
            "defaults": {"run": {"shell": job_shell}},
            "steps": [{"shell": step_shell, "run": "echo '${{ env.VALUE }}'"}],
        }},
    }))
    [(label, dialect, source)] = lint.scripts([workflow])
    assert dialect == expected
    assert "${{" not in source


def test_timeout_is_a_clear_failure(capsys):
    assert lint.bounded([sys.executable, "-c", "import time; time.sleep(5)"], 0.05) == 1
    assert "timed out" in capsys.readouterr().err
