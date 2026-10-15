"""Focused coverage for the local workflow lint split."""

import importlib.util
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("workflow_shells", ROOT / "scripts/check_workflow_shells.py")
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)


@pytest.fixture(scope="module", params=["default", "shellcheck-disabled-default"])
def actionlint_reference(request, tmp_path_factory):
    # Model a gate wrapper that prepends -shellcheck= to every invocation.
    # Use a stub for the selection oracle: real ShellCheck must run separately
    # because actionlint's stdin integration can hang in local gate environments.
    command = ["actionlint"]
    if request.param == "shellcheck-disabled-default":
        command.append("-shellcheck=")
    result = subprocess.run([*command, "-version"], capture_output=True,
                            text=True, timeout=10, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[0] == "v1.7.7"
    stub = tmp_path_factory.mktemp("shellcheck-oracle") / "shellcheck-stub"
    stub.write_text('#!/bin/sh\ncat > /dev/null\nprintf \'[]\\n\'\n', encoding="utf-8")
    stub.chmod(0o755)
    return [*command, f"-shellcheck={stub}"]


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


@pytest.mark.parametrize("scalar", ["false", "yes", "TRUE", "0123", "1.20", "null",
                                   "~", "2026-10-15", ""])
def test_run_scalars_reach_shellcheck_as_original_text(tmp_path, monkeypatch, scalar):
    workflow = tmp_path / "scalar.yml"
    workflow.write_text(f"jobs:\n  check:\n    steps:\n      - run: {scalar}\n")
    expected = f"set -eo pipefail\n{scalar}\n"
    [(_, dialect, source)] = lint.scripts([workflow])
    assert dialect == "bash"
    assert source == expected

    checked = []

    def check_script(command, timeout):
        checked.append(Path(command[-1]).read_text(encoding="utf-8"))
        return 0

    monkeypatch.setattr(lint, "bounded", check_script)
    assert lint.shellcheck([workflow], tmp_path) == 0
    assert checked == [expected]


@pytest.mark.parametrize("expression", [
    "${{ format('{{Hello {0}!}}', github.actor) }}",
    "${{ format('it''s }} {0}', github.actor) }}",
    "${{ format('backslash\\''}} {0}', github.actor) }}",
    "${{ format('é }} {0}', github.actor) }}",
    "${{ format(\n  '}} {0}', github.actor\n) }}",
    "${{ github.actor }}${{ format('}} {0}', github.actor) }}",
])
def test_complete_expression_spans_are_sanitized(tmp_path, expression):
    workflow = tmp_path / "expressions.yml"
    workflow.write_text(lint.yaml.safe_dump({
        "jobs": {"check": {"steps": [{"run": f"echo {expression} # retained"}]}},
    }))
    [(_, _, source)] = lint.scripts([workflow])
    assert source == f"set -eo pipefail\necho {'_' * len(expression.encode('utf-8'))} # retained\n"
    assert lint.shellcheck([workflow], tmp_path) == 0


def test_unterminated_expression_fails_extraction():
    with pytest.raises(ValueError, match="unterminated GitHub expression"):
        lint.sanitize_expressions("echo ${{ 'inner }}'")


@pytest.mark.parametrize(("step_shell", "job_shell", "workflow_shell", "runner", "expected"), [
    ("sh -e {0}", "bash", "bash", "ubuntu-latest", "sh"),
    (None, "sh", "bash", "ubuntu-latest", "sh"),
    (None, None, "sh", "ubuntu-latest", "sh"),
    (None, None, None, "ubuntu-latest", "bash"),
    (None, None, None, "windows-latest", None),
    ("python", None, None, "ubuntu-latest", None),
])
def test_shell_precedence(tmp_path, step_shell, job_shell, workflow_shell, runner, expected):
    workflow = tmp_path / "shell.yml"
    workflow.write_text(lint.yaml.safe_dump({
        "defaults": {"run": {"working-directory": "."} if workflow_shell is None
                     else {"shell": workflow_shell}},
        "jobs": {"check": {
            "runs-on": runner,
            "defaults": {"run": {"working-directory": "."} if job_shell is None
                         else {"shell": job_shell}},
            "steps": [{**({} if step_shell is None else {"shell": step_shell}),
                       "run": "echo '${{ env.VALUE }}'"}],
        }},
    }))
    [(label, dialect, source)] = lint.scripts([workflow])
    assert dialect == expected
    assert "${{" not in source


def test_timeout_is_a_clear_failure(capsys):
    assert lint.bounded([sys.executable, "-c", "import time; time.sleep(5)"], 0.05) == 1
    assert "timed out" in capsys.readouterr().err


# Offline oracle: installed actionlint v1.7.7, parse.go (parseString,
# parseDefaults, parseStep) and rule_shellcheck.go (getShellName/runShellcheck).
# None means an absent key; "" is an explicit empty scalar and INVALID workflow.
@pytest.mark.parametrize(("level", "shell", "selected"), [
    ("step", None, "fallback"),
    ("step", "", None),
    ("step", "bash", "bash"),
    ("step", "sh", "sh"),
    ("step", "python", None),
    ("job", None, "fallback"),
    ("job", "", "fallback"),
    ("job", "bash", "bash"),
    ("job", "sh", "sh"),
    ("job", "python", None),
    ("workflow", None, "runner"),
    ("workflow", "", "runner"),
    ("workflow", "bash", "bash"),
    ("workflow", "sh", "sh"),
    ("workflow", "python", None),
])
@pytest.mark.parametrize("runner", ["ubuntu-latest", "windows-latest"])
@pytest.mark.parametrize("broken", [False, True], ids=["clean", "broken"])
def test_shell_selection_and_split_gate_match_actionlint(
        tmp_path, actionlint_reference, level, shell, selected, runner, broken):
    step = {"run": "echo $unquoted" if broken else "echo safe"}
    if shell == "python":
        step["run"] = "# " + step["run"] + "\npass"
    job = {"runs-on": runner, "steps": [step]}
    document = {"on": "push", "jobs": {"check": job}}
    fallback = "sh" if runner == "ubuntu-latest" else "bash"
    if level == "step":
        document["defaults"] = {"run": {"shell": "bash"}}
        job["defaults"] = {"run": {"shell": fallback}}
        target = step
    elif level == "job":
        document["defaults"] = {"run": {"shell": fallback}}
        job["defaults"] = {"run": {"working-directory": "."}}
        target = job["defaults"]["run"]
    else:
        document["defaults"] = {"run": {"working-directory": "."}}
        target = document["defaults"]["run"]
    if shell is not None:
        target["shell"] = shell
    workflow = tmp_path / "shell.yml"
    workflow.write_text(lint.yaml.safe_dump(document), encoding="utf-8")

    # Actionlint selects the shell using a stub; standalone ShellCheck below
    # supplies the real diagnostics without actionlint's ShellCheck stdin pipe.
    reference = subprocess.run(
        [*actionlint_reference, "-debug", str(workflow)],
        capture_output=True, text=True, timeout=10, check=False)
    structural = subprocess.run(
        [*actionlint_reference, "-shellcheck=", str(workflow)],
        capture_output=True, text=True, timeout=10, check=False)
    expected = ("bash" if runner == "ubuntu-latest" else None) if selected == "runner" else selected
    if selected == "fallback":
        expected = fallback
    assert re.findall(r"Run shellcheck for (bash|sh) script:", reference.stderr) == (
        [] if expected is None else [expected])
    assert list(lint.scripts([workflow]))[0][1] == expected
    invalid_windows_shell = runner == "windows-latest" and shell == "sh" and level != "workflow"
    invalid = shell == "" or invalid_windows_shell
    assert ("string should not be empty" in structural.stdout) == (shell == "")
    assert ('shell name "sh" is invalid on Windows' in structural.stdout) == invalid_windows_shell
    assert structural.returncode == (1 if invalid else 0), structural.stdout + structural.stderr
    separate_status = lint.shellcheck([workflow], tmp_path)
    assert separate_status == (1 if broken and expected else 0)
    combined_failed = structural.returncode != 0 or separate_status != 0
    assert reference.returncode == structural.returncode, (
        reference.stdout + reference.stderr)
    assert combined_failed == bool(invalid or (broken and expected))


def test_shellcheck_tool_failure_is_propagated(tmp_path, monkeypatch):
    workflow = tmp_path / "tool-failure.yml"
    workflow.write_text("jobs:\n  check:\n    steps:\n      - run: echo safe\n")
    monkeypatch.setattr(lint, "bounded", lambda command, timeout: 2)
    assert lint.shellcheck([workflow], tmp_path) == 2


def test_missing_tool_is_a_clear_failure(tmp_path, capsys):
    assert lint.bounded([str(tmp_path / "missing-shellcheck")]) == 2
    assert "FAIL:" in capsys.readouterr().err
