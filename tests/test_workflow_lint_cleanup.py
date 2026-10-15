"""Exercise the actual gate entry point with bounded, synthetic tool stubs."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("inherited_traps", [False, True])
@pytest.mark.parametrize(("mode", "expected"), [
    ("success", 0), ("actionlint", 17), ("shellcheck", 23),
    ("later", 29), ("TERM", 143), ("INT", 130),
])
def test_invocation_cleanup(tmp_path, mode, expected, inherited_traps):
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "tests/semreg_thermal_map_contract").mkdir(parents=True)
    entry = repo / "scripts/ci_local.sh"
    shutil.copyfile(ROOT / "scripts/ci_local.sh", entry)
    caller = tmp_path / "caller"
    caller.mkdir()
    sentinel = caller / "sentinel"
    sentinel.write_text("caller owned")
    other = caller / "docs-ebus-ci.other-run"
    other.mkdir()
    (other / "sentinel").write_text("other invocation")
    outside = tmp_path / "outside"
    outside.write_text("unrelated")
    log = tmp_path / "calls.jsonl"
    tools = tmp_path / "bin"
    tools.mkdir()
    stub = tools / "stub"
    stub.write_text(f"#!{sys.executable}\n" + r'''
import json
import os
from pathlib import Path
import signal
import sys

name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ["CALL_LOG"], "a") as stream:
    stream.write(json.dumps([name, *args]) + "\n")
mode = os.environ["CLEANUP_CASE"]
if name == "jv" and args == ["--version"]:
    print("github.com/santhosh-tekuri/jsonschema/cmd/jv v0.7.0")
if name == "git":
    if args[0] == "ls-files":
        print("synthetic.md")
    elif args[0] == "grep":
        sys.exit(1)
if name == "python3":
    if args[:1] == ["-"]:
        sys.stdin.read()
    if args[:2] == ["scripts/check_workflow_shells.py", "actionlint-version"]:
        print("v1.7.7")
    if args[:2] == ["scripts/check_workflow_shells.py", "actionlint"]:
        sys.exit(17 if mode == "actionlint" else 0)
    if args[:2] == ["scripts/check_workflow_shells.py", "shellcheck"]:
        directory = Path(args[3])
        (directory / "synthetic-step.bash").write_text("echo synthetic\n")
        if mode in ("TERM", "INT"):
            os.kill(os.getppid(), getattr(signal, "SIG" + mode))
        sys.exit(23 if mode == "shellcheck" else 0)
    if args == ["-m", "pytest", "-q", "tests/test_workflow_shells.py"]:
        sys.exit(29 if mode == "later" else 0)
''')
    stub.chmod(0o755)
    for name in ("python3", "actionlint", "shellcheck", "jv", "git", "go", "bash"):
        (tools / name).symlink_to(stub)
    inherited = tmp_path / "inherited.bash"
    inherited.write_text("trap 'echo previous-exit:$?' EXIT\n"
                         "trap 'echo previous-term' TERM\n"
                         "trap 'echo previous-int' INT\n")
    env = dict(os.environ, BASH_ENV=str(inherited) if inherited_traps else "", PATH=f"{tools}:{os.environ['PATH']}", TMPDIR=str(caller),
               CALL_LOG=str(log), CLEANUP_CASE=mode,
               PLATFORM_M625_DOCS_EEBUS_ROOT=str(repo),
               PLATFORM_M625_EXECUTION_PLANS_ROOT=str(repo))
    # Background gate runners may ignore SIGINT. Bash cannot trap a signal that
    # was ignored when it started, so normalize it in a child before exec.
    # The real Bash executes the unmodified entry point; later tools are synthetic.
    launcher = ("import os, signal, sys; "
                "signal.signal(signal.SIGINT, signal.SIG_DFL); "
                "os.execv('/bin/bash', ['/bin/bash', sys.argv[1]])")
    result = subprocess.run([sys.executable, "-c", launcher, str(entry)], env=env,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == expected, result.stdout + result.stderr
    if inherited_traps:
        assert f"previous-exit:{expected}" in result.stdout
    if inherited_traps and mode in ("TERM", "INT"):
        assert f"previous-{mode.lower()}" in result.stdout
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    lint_calls = [call for call in calls if call[:2] ==
                  ["python3", "scripts/check_workflow_shells.py"]]
    assert [call[2] for call in lint_calls] == ["actionlint-version", "actionlint", "shellcheck"]
    owned = Path(lint_calls[-1][4])
    assert owned.parent == caller
    assert owned.name.startswith("docs-ebus-ci.")
    assert not owned.exists()
    assert sentinel.read_text() == "caller owned"
    assert (other / "sentinel").read_text() == "other invocation"
    assert outside.read_text() == "unrelated"
    assert set(caller.iterdir()) == {sentinel, other}
    later = ["python3", "-m", "pytest", "-q", "tests/test_workflow_shells.py"]
    assert (later in calls) == (mode in ("success", "later"))
    if mode == "success":
        assert ["bash", "scripts/check_runtime_state_schema.sh"] in calls
        assert "NM 07FE/07FF service names" in result.stdout
