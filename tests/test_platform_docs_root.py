"""An unset docs root fails. A pytest cache directory is not a checkout."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess

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
    for key in ("PLATFORM_DOCS_ROOT", "PLATFORM_DOCS_MODBUS_ROOT", "PLATFORM_DOCS_EEBUS_ROOT"):
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


def test_explicit_root_is_used(monkeypatch, tmp_path: Path):
    module = _load("graphql_root", "scripts/check_graphql_face_provenance.py")
    monkeypatch.setenv("PLATFORM_DOCS_ROOT", str(tmp_path))
    (tmp_path / ".pytest_cache" / "platform-docs").mkdir(parents=True)
    assert module.platform_docs_root() == tmp_path
