"""An unset docs root fails. A pytest cache directory is not a checkout."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_listed_resolvers_have_no_pytest_cache_fallback():
    paths = [
        "scripts/ci_local.sh",
        "scripts/validate_adversarial_runtime_report_v1.py",
        "scripts/validate_vaillant_semreg_thermal_map.py",
        "scripts/check_naming_surface_contract.py",
        "scripts/check_name_decomposition.py",
        "scripts/check_regulator_identity_contract.py",
        "scripts/check_graphql_face_provenance.py",
        "tests/test_vaillant_semreg_thermal_map.py",
        "tests/test_eebus_operator_admin_contract.py",
        "tests/test_live_readiness_docs.py",
        "tests/test_graphql_face_provenance_checker.py",
        "tests/test_system_config_bound_contract.py",
        "tests/test_regulator_identity_contract_checker.py",
    ]
    for relative in paths:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert ".pytest_cache" not in text, relative


def test_platform_docs_root_rejects_pytest_cache(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("PLATFORM_DOCS_ROOT", str(tmp_path / "explicit"))
    module = _load("adversarial_root", "scripts/validate_adversarial_runtime_report_v1.py")
    monkeypatch.delenv("PLATFORM_DOCS_ROOT", raising=False)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    (tmp_path / ".pytest_cache" / "platform-docs").mkdir(parents=True)
    with pytest.raises(OSError, match="PLATFORM_DOCS_ROOT is required"):
        module.platform_docs_root()
    checkout = tmp_path / "checkouts" / "docs"
    checkout.mkdir(parents=True)
    assert module.platform_docs_root() == checkout


def test_owner_root_rejects_pytest_cache(monkeypatch, tmp_path: Path):
    module = _load("operator_admin_root", "tests/test_eebus_operator_admin_contract.py")
    monkeypatch.delenv("PLATFORM_DOCS_EEBUS_ROOT", raising=False)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    (tmp_path / ".pytest_cache" / "platform-eebus").mkdir(parents=True)
    with pytest.raises(OSError, match="PLATFORM_DOCS_EEBUS_ROOT is required"):
        module._owner_root("PLATFORM_DOCS_EEBUS_ROOT", "docs-eebus")
    checkout = tmp_path / "checkouts" / "docs-eebus"
    checkout.mkdir(parents=True)
    assert module._owner_root("PLATFORM_DOCS_EEBUS_ROOT", "docs-eebus") == checkout


def test_ci_local_unset_root_fails_closed():
    env = os.environ.copy()
    for key in ("PLATFORM_DOCS_ROOT", "PLATFORM_DOCS_EEBUS_ROOT"):
        env.pop(key, None)
    env["PATH"] = os.environ.get("PATH", "")
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/ci_local.sh")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 1
    assert "PLATFORM_DOCS_ROOT is required" in result.stderr
    assert ".pytest_cache" not in result.stderr


def test_ci_local_requires_the_public_modbus_checkout_and_keeps_the_companion_check(tmp_path: Path):
    text = (ROOT / "scripts/ci_local.sh").read_text(encoding="utf-8")
    assert 'PLATFORM_DOCS_MODBUS_ROOT="${repo_root}/checkouts/docs-modbus"' in text
    assert 'cd "${PLATFORM_DOCS_MODBUS_ROOT}"' in text
    assert "PLATFORM_DOCS_MODBUS_PRIOR_ROOT" not in text
    assert "python3 scripts/validate_modbus_companion.py" in text
    assert "tests/test_modbus_trusted_revision.py" in text
    assert "PLATFORM_DOCS_ROOT" in text
    assert "PLATFORM_DOCS_EEBUS_ROOT" in text
    docs = tmp_path / "docs"
    eebus = tmp_path / "docs-eebus"
    docs.mkdir()
    eebus.mkdir()
    env = os.environ.copy()
    for key in (
        "PLATFORM_DOCS_ROOT",
        "PLATFORM_DOCS_EEBUS_ROOT",
        "PLATFORM_DOCS_MODBUS_ROOT",
        "PLATFORM_DOCS_MODBUS_PRIOR_ROOT",
    ):
        env.pop(key, None)
    env["PLATFORM_DOCS_ROOT"] = str(docs)
    env["PLATFORM_DOCS_EEBUS_ROOT"] = str(eebus)
    env["PATH"] = os.defpath
    modbus = tmp_path / "docs-modbus"
    env["PLATFORM_DOCS_MODBUS_ROOT"] = str(modbus)
    command = ["bash", str(ROOT / "scripts/ci_local.sh")]
    missing = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=20, check=False)
    assert missing.returncode == 1
    assert "PLATFORM_DOCS_MODBUS_ROOT is required" in missing.stderr

    modbus.mkdir()
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=20, check=False)
    combined = result.stdout + result.stderr
    assert result.returncode == 2
    assert "PLATFORM_DOCS_MODBUS_ROOT is required" not in combined
    assert "actionlint v1.7.7 is required" in result.stderr


@pytest.mark.parametrize(("case", "status"), [("pinned", 71), ("wrong-head", 1), ("missing", 69)])
def test_modbus_staging_without_a_preconfigured_root(tmp_path: Path, case: str, status: int):
    gate = ROOT / "scripts/ci_local.sh"
    pin = re.search(r"^docs_modbus_ref=([0-9a-f]{40})$", gate.read_text(encoding="utf-8"), re.M)
    assert pin is not None
    fake_git = tmp_path / "git"
    other_head = ("0" if pin[1][0] != "0" else "1") + pin[1][1:]
    fake_git.write_text(
        r'''#!/bin/bash
set -eu
[ "${GIT_CONFIG_NOSYSTEM}:${GIT_CONFIG_GLOBAL}:${GIT_TERMINAL_PROMPT}" = "1:/dev/null:0" ]
[ "${GIT_CONFIG_COUNT-unset}" = unset ]
if [ "$1" = init ] && [ "$2" = --template= ]; then
  mkdir "$3"
  exit
fi
[ "$1" = -C ] || exit 89
case "$2" in
  "${0%/*}"/docs-ebus-ci.*/checkouts/docs-modbus) ;;
  *) exit 89 ;;
esac
cd "$2"
shift 2
case "$*" in
  "fetch --depth 1 https://github.com/Project-Helianthus/helianthus-docs-modbus.git @PIN@")
    [ @CASE@ != missing ] || exit 69
    echo fetched > fetched
    ;;
  "checkout --detach FETCH_HEAD")
    [ -f fetched ]
    echo detached > detached
    echo 'synthetic checkout'
    ;;
  "rev-parse --verify HEAD")
    [ -f detached ]
    echo @HEAD@
    ;;
  *) exit 89 ;;
esac
'''.replace("@PIN@", pin[1]).replace("@CASE@", case).replace("@HEAD@", other_head if case == "wrong-head" else pin[1]),
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    lint_stub = tmp_path / "lint-stub.bash"
    lint_stub.write_text(
        r'''actionlint() { :; }
        shellcheck() { :; }
        jv() { echo 'github.com/santhosh-tekuri/jsonschema/cmd/jv v0.7.0'; }
        python3() {
          case "$*" in
            'scripts/check_workflow_shells.py actionlint-version') echo v1.7.7 ;;
            'scripts/check_workflow_shells.py actionlint')
              printenv PLATFORM_DOCS_MODBUS_ROOT
              return 71
              ;;
            'scripts/check_workflow_shells.py shellcheck --temp-dir '*) ;;
            *) return 89 ;;
          esac
        }
        ''', encoding="utf-8",
    )
    result = subprocess.run(
        ["/bin/bash", str(gate)],
        cwd=tmp_path,
        env={
            "PATH": f"{tmp_path}:{os.defpath}",
            "BASH_ENV": str(lint_stub),
            "TMPDIR": str(tmp_path),
            "PLATFORM_DOCS_ROOT": str(tmp_path),
            "PLATFORM_DOCS_EEBUS_ROOT": str(tmp_path),
            "GIT_CONFIG_COUNT": "0",
        },
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == status, result.stdout + result.stderr
    if case == "pinned":
        assert any(line.startswith(f"{tmp_path}/docs-ebus-ci.") and line.endswith("/checkouts/docs-modbus")
                   for line in result.stdout.splitlines())
    if case == "wrong-head":
        assert "must be at the public Modbus revision pinned in Docs CI" in result.stderr
    if case == "missing":
        assert "Could not fetch the pinned public helianthus-docs-modbus checkout." in result.stderr
        assert "synthetic checkout" not in result.stdout


def test_explicit_root_is_used(monkeypatch, tmp_path: Path):
    module = _load("graphql_root", "scripts/check_graphql_face_provenance.py")
    monkeypatch.setenv("PLATFORM_DOCS_ROOT", str(tmp_path))
    (tmp_path / ".pytest_cache" / "platform-docs").mkdir(parents=True)
    assert module.platform_docs_root() == tmp_path


def _naming_help(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_naming_surface_contract.py"), "--help"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


def test_naming_checker_help_does_not_import_the_moved_mcp_module(tmp_path: Path):
    docs = tmp_path / "docs"
    (docs / "scripts").mkdir(parents=True)
    (docs / "scripts" / "check_mcp_inventory.py").write_text(
        "raise RuntimeError('mcp checker imported at startup')\n",
        encoding="utf-8",
    )
    decoy = tmp_path / "decoy"
    decoy.mkdir()
    (decoy / "check_mcp_inventory.py").write_text(
        "raise RuntimeError('decoy mcp checker imported')\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(decoy)
    env.pop("PLATFORM_DOCS_ROOT", None)
    unset = _naming_help(env)
    assert unset.returncode == 0, unset.stderr
    assert "ModuleNotFoundError" not in unset.stderr
    assert "decoy mcp checker imported" not in unset.stderr
    env["PLATFORM_DOCS_ROOT"] = str(docs)
    pointed = _naming_help(env)
    assert pointed.returncode == 0, pointed.stderr
    assert "mcp checker imported at startup" not in pointed.stderr + pointed.stdout


def test_naming_checker_loads_mcp_from_the_docs_checkout(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    decoy = tmp_path / "decoy"
    decoy.mkdir()
    (decoy / "check_mcp_inventory.py").write_text(
        "MARKER = 'decoy'\n"
        "def documented_rows(text):\n"
        "    raise AssertionError('decoy checker used')\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(decoy))
    module = _load("naming_docs_mcp", "scripts/check_naming_surface_contract.py")
    monkeypatch.delenv("PLATFORM_DOCS_ROOT", raising=False)
    repo = tmp_path / "repo"
    monkeypatch.setattr(module, "ROOT", repo)
    with pytest.raises(OSError, match="PLATFORM_DOCS_ROOT is required"):
        module._load_mcp_checker()
    checkout = repo / "checkouts" / "docs"
    (checkout / "scripts").mkdir(parents=True)
    (checkout / "scripts" / "check_mcp_inventory.py").write_text(
        "MARKER = 'checkout'\n"
        "def documented_rows(text):\n"
        "    return {}, [{'name': 'zone_room_temperature'}]\n"
        "def unique_rows(rows, profiles):\n"
        "    return {}\n"
        "def validate(inventory, text):\n"
        "    raise AssertionError('registration checker unused')\n",
        encoding="utf-8",
    )
    loaded = module._load_mcp_checker()
    assert loaded.MARKER == "checkout"
    assert Path(loaded.__file__).resolve() == (checkout / "scripts" / "check_mcp_inventory.py").resolve()
    module._validate_tool_names("tools", None)
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("PLATFORM_DOCS_ROOT", str(empty))
    with pytest.raises(OSError, match="checker missing: scripts/check_mcp_inventory.py"):
        module._load_mcp_checker()
    explicit = tmp_path / "explicit"
    (explicit / "scripts").mkdir(parents=True)
    (explicit / "scripts" / "check_mcp_inventory.py").write_text(
        "MARKER = 'explicit'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PLATFORM_DOCS_ROOT", str(explicit))
    assert module._load_mcp_checker().MARKER == "explicit"
