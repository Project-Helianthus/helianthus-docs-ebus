"""Run the complete production gate with cheap, synthetic phase signals."""

import os
from pathlib import Path
import signal
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
LINT_BOUNDARY = 'echo "Pinned workflow/schema gate tools passed."\n'
BEGIN_FRAGMENT = "# BEGIN unchanged production fragment\n"
END_FRAGMENT = "# END unchanged production fragment\n"


def production_fragment():
    return (ROOT / "scripts/ci_local.sh").read_text()


# Keep the complete gate tail cheap while executing its real shell control flow.
# Bash builtins avoid starting a Python interpreter for each synthetic tool.
STUBS = r'''
python3() {
  case "$*" in
    'scripts/check_workflow_shells.py actionlint-version')
      printf 'v1.7.7\n'
      ;;
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
    '-m unittest discover -s tests -p test_ao06_b507_quantity_views.py') ;;
    scripts/*.py*|'-m pytest -q '*|'-') ;;
    *) printf 'Unexpected synthetic tool call: %s\n' "$*" >&2; return 98 ;;
  esac
  return 0
}
git() {
  case "$1" in
    ls-files) printf 'synthetic.md\n' ;;
    grep) return 1 ;;
    *) return 98 ;;
  esac
}
actionlint() { :; }
shellcheck() { :; }
jv() {
  if [ "$*" = --version ]; then
    printf 'github.com/santhosh-tekuri/jsonschema/cmd/jv v0.7.0\n'
  fi
}
go() { :; }
bash() {
  case "$*" in
    scripts/check_address_table_taxonomy_hash.sh) ;;
    scripts/check_runtime_state_schema.sh)
      printf 'runtime-schema\n' >> "$CALL_LOG"
      if [ "$CLEANUP_CASE" = runtime-schema ]; then return 31; fi
      ;;
    *) return 98 ;;
  esac
}
'''


def run_case(tmp_path, mode, inherited_traps=False, mutation=None):
    repo = tmp_path / "repo"
    (repo / "tests/semreg_thermal_map_contract").mkdir(parents=True)
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
    (repo / "scripts").mkdir()
    entry = repo / "scripts/ci_local.sh"
    fragment = production_fragment()
    entry.write_text(STUBS + BEGIN_FRAGMENT + fragment + END_FRAGMENT)
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
               CLEANUP_CASE=mode,
               PLATFORM_M625_DOCS_EEBUS_ROOT=str(repo),
               PLATFORM_M625_EXECUTION_PLANS_ROOT=str(repo))
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
    assert ("later" in phases) == (mode in ("success", "later", "runtime-schema")), "later reachability"
    assert ("cleanup-tests" in phases) == (mode in ("success", "runtime-schema")), "cleanup-test reachability"
    assert ("runtime-schema" in phases) == (mode in ("success", "runtime-schema")), "tail reachability"
    assert len(phases) == (5 if mode in ("success", "runtime-schema") else 3 if mode == "later" else 2)
    if mode == "success":
        assert "==> check NM 07FE/07FF service names\n" in result.stdout, "final gate reachability"
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
    ("later", 29), ("runtime-schema", 31), ("TERM", 143), ("INT", 130),
])
def test_invocation_cleanup(tmp_path, mode, expected, inherited_traps):
    assert_case(run_case(tmp_path, mode, inherited_traps), mode, expected, inherited_traps)


@pytest.mark.parametrize(("mode", "expected", "mutation", "failure"), [
    pytest.param("success", 0, (LINT_BOUNDARY, LINT_BOUNDARY + "exit 0\n"),
                 "tail reachability", id="exit-before-gate-tail"),
    pytest.param("success", 0, (LINT_BOUNDARY, LINT_BOUNDARY + "trap : EXIT\n"),
                 "invocation cleanup", id="overwrite-cleanup-in-gate-tail"),
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
