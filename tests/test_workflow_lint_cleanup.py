"""Run the production cleanup/lint fragment with cheap, synthetic phase signals."""

import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
START = 'gate_temp_dir="$(mktemp -d '
END = 'echo "Pinned workflow/schema gate tools passed."\n'
BEGIN_FRAGMENT = "# BEGIN unchanged production fragment\n"
END_FRAGMENT = "# END unchanged production fragment\n"


def production_fragment():
    source = (ROOT / "scripts/ci_local.sh").read_text()
    assert source.count(START) == source.count(END) == 1
    return source[source.index(START):source.index(END) + len(END)]


# Only the lint/later entry points used by the fragment are accepted.
# Bash builtins avoid starting a Python interpreter for each synthetic tool.
STUBS = r'''
python3() {
  case "$*" in
    'scripts/check_workflow_shells.py actionlint')
      printf 'actionlint\n' >> "$CALL_LOG"
      if [ "$CLEANUP_CASE" = actionlint ]; then return 17; fi
      ;;
    'scripts/check_workflow_shells.py shellcheck --temp-dir '*)
      [ "$#" -eq 4 ] && [ "$4" = "$gate_temp_dir" ] || return 97
      printf 'shellcheck\n' >> "$CALL_LOG"
      printf '%s\n' "$4" > "$OWNED_PATH"
      printf 'echo synthetic\n\necho final' > "$4/synthetic-step.bash"
      printf 'echo other\n' > "$4/synthetic-step.sh"
      # Vary the directory basename prefix and suffix independently. Neither
      # a shared invocation prefix nor a shared suffix grants cleanup ownership.
      mkdir "$4.extra" "${4%/*}/unrelated-${4##*/}"
      printf 'suffix neighbor' > "$4.extra/sentinel"
      printf 'prefix neighbor' > "${4%/*}/unrelated-${4##*/}/sentinel"
      case "$CLEANUP_CASE" in
        shellcheck)
          printf '%s:3:1: synthetic lint finding\n' "$4/synthetic-step.bash" >&2
          return 23 ;;
        TERM|INT) kill -s "$CLEANUP_CASE" "$$" ;;
      esac
      ;;
    '-m pytest -q tests/test_workflow_shells.py')
      printf 'later\n' >> "$CALL_LOG"
      if [ "$CLEANUP_CASE" = later ]; then return 29; fi
      ;;
    '-m pytest -q tests/test_workflow_lint_cleanup.py')
      printf 'cleanup-tests\n' >> "$CALL_LOG"
      ;;
    *) printf 'Unexpected synthetic tool call: %s\n' "$*" >&2; return 98 ;;
  esac
  return 0
}
'''


def run_case(tmp_path, mode, inherited_traps=False, mutation=None):
    repo = tmp_path / "repo"
    repo.mkdir()
    caller = tmp_path / "caller"
    caller.mkdir()
    sentinel = caller / "sentinel"
    sentinel.write_text("caller owned")
    other = caller / "docs-ebus-ci.other-run"
    other.mkdir()
    (other / "sentinel").write_text("other invocation")
    outside = tmp_path / "outside"
    outside.write_text("unrelated")
    log = tmp_path / "phases"
    owned_path = tmp_path / "owned-path"
    entry = tmp_path / "harness.bash"
    fragment = production_fragment()
    entry.write_text("set -euo pipefail\n"
                     f"repo_root={shlex.quote(str(repo))}\n"
                     'cd "$repo_root"\n' + STUBS + BEGIN_FRAGMENT
                     + fragment + END_FRAGMENT)
    # Check the actual executable file, not a transformed or hand-copied model.
    assembled = entry.read_text().split(BEGIN_FRAGMENT, 1)[1].split(END_FRAGMENT, 1)[0]
    assert assembled == production_fragment()
    if mutation is not None:
        old, new = mutation
        assert fragment.count(old) == 1
        mutated = fragment.replace(old, new)
        assert mutated != fragment
        entry.write_text(entry.read_text().replace(fragment, mutated, 1))
    inherited = tmp_path / "inherited.bash"
    inherited.write_text("trap 'echo previous-exit:$?' EXIT\n"
                         "trap 'echo previous-term' TERM\n"
                         "trap 'echo previous-int' INT\n")
    env = dict(os.environ, BASH_ENV=str(inherited) if inherited_traps else "",
               TMPDIR=str(caller), CALL_LOG=str(log), OWNED_PATH=str(owned_path),
               CLEANUP_CASE=mode)
    # A background runner can inherit ignored INT; normalize before exec.
    launcher = ("import os, signal, sys; "
                "signal.signal(signal.SIGINT, signal.SIG_DFL); "
                "os.execv('/bin/bash', ['/bin/bash', sys.argv[1]])")
    with subprocess.Popen([sys.executable, "-c", launcher, str(entry)], env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, start_new_session=True) as process:
        try:
            stdout, stderr = process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            # Kill descendants too, so a hung tool cannot retain capture pipes.
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            pytest.fail("cleanup harness exceeded the 15-second watchdog")
        result = subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
    return result, log, owned_path, caller, sentinel, other, outside


def assert_case(run, mode, expected, inherited_traps=False):
    result, log, owned_path, caller, sentinel, other, outside = run
    phases = log.read_text().splitlines()
    assert phases[:2] == ["actionlint", "shellcheck"], "lint phase order"
    assert ("later" in phases) == (mode in ("success", "later")), "later reachability"
    assert ("cleanup-tests" in phases) == (mode == "success"), "cleanup-test reachability"
    assert len(phases) == (4 if mode == "success" else 3 if mode == "later" else 2)
    assert result.returncode == expected, "exit status: " + result.stdout + result.stderr
    if inherited_traps:
        assert f"previous-exit:{expected}\n" in result.stdout
        if mode in ("TERM", "INT"):
            assert f"previous-{mode.lower()}\n" in result.stdout
    owned = Path(owned_path.read_text().strip())
    assert owned.parent == caller
    assert owned.name.startswith("docs-ebus-ci.")
    assert not owned.exists(), "invocation cleanup"
    evidence = f"Extracted workflow source: {owned / 'synthetic-step.bash'}\n"
    other_evidence = f"Extracted workflow source: {owned / 'synthetic-step.sh'}\n"
    if mode == "shellcheck":
        assert result.stderr.count(evidence) == 1
        assert result.stderr.count(other_evidence) == 1
        assert f"{owned / 'synthetic-step.bash'}:3:1: synthetic lint finding" in result.stderr
        assert evidence + "     1\techo synthetic\n     2\t\n     3\techo final" in result.stderr, "numbered diagnostics"
        assert other_evidence + "     1\techo other\n" in result.stderr, "numbered diagnostics"
    else:
        assert "Extracted workflow source:" not in result.stderr
    assert sentinel.read_text() == "caller owned"
    assert other.is_dir(), "other invocation preserved"
    assert (other / "sentinel").read_text() == "other invocation"
    assert outside.read_text() == "unrelated"
    suffix_neighbor = Path(str(owned) + ".extra")
    prefix_neighbor = caller / f"unrelated-{owned.name}"
    assert suffix_neighbor.is_dir(), "suffix neighbor preserved"
    assert prefix_neighbor.is_dir(), "prefix neighbor preserved"
    assert (suffix_neighbor / "sentinel").read_text() == "suffix neighbor"
    assert (prefix_neighbor / "sentinel").read_text() == "prefix neighbor"
    assert set(caller.iterdir()) == {sentinel, other, suffix_neighbor, prefix_neighbor}


@pytest.mark.parametrize("inherited_traps", [False, True])
@pytest.mark.parametrize(("mode", "expected"), [
    ("success", 0), ("actionlint", 17), ("shellcheck", 23),
    ("later", 29), ("TERM", 143), ("INT", 130),
])
def test_invocation_cleanup(tmp_path, mode, expected, inherited_traps):
    assert_case(run_case(tmp_path, mode, inherited_traps), mode, expected, inherited_traps)


@pytest.mark.parametrize(("mode", "expected", "mutation", "failure"), [
    pytest.param("success", 0, ("install_workflow_cleanup_trap EXIT ''\n", ""),
                 "invocation cleanup", id="remove-cleanup-trap"),
    pytest.param("actionlint", 17, ('exit "$workflow_lint_status"', "exit 0"),
                 "exit status", id="mask-lint-status"),
    pytest.param("success", 0, ('rm -rf -- "$gate_temp_dir"',
                               'rm -rf -- "$gate_temp_dir" "${TMPDIR}/docs-ebus-ci.other-run"'),
                 "other invocation preserved", id="delete-other-invocation"),
    pytest.param("success", 0, ('rm -rf -- "$gate_temp_dir"',
                               'rm -rf -- "$gate_temp_dir"*'),
                 "suffix neighbor preserved", id="delete-suffix-neighbor"),
    pytest.param("success", 0, ('rm -rf -- "$gate_temp_dir"',
                               'rm -rf -- "$gate_temp_dir" "${TMPDIR}/unrelated-${gate_temp_dir##*/}"'),
                 "prefix neighbor preserved", id="delete-prefix-neighbor"),
    pytest.param("shellcheck", 23, ('nl -ba "$workflow_script" >&2 || :', ":"),
                 "numbered diagnostics", id="suppress-numbered-source"),
    pytest.param("actionlint", 17,
                 ('if [ "$workflow_lint_status" -ne 0 ]; then\n  exit "$workflow_lint_status"\nfi\n', ""),
                 "later reachability", id="continue-after-lint-failure"),
])
def test_production_mutation_is_detected(tmp_path, mode, expected, mutation, failure):
    run = run_case(tmp_path, mode, mutation=mutation)
    with pytest.raises(AssertionError, match=failure):
        assert_case(run, mode, expected)
