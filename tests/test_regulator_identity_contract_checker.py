from __future__ import annotations

import importlib.util
import pathlib
import shutil

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / "scripts/check_regulator_identity_contract.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("regulator_identity_checker", CHECKER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_contract_docs(destination: pathlib.Path) -> None:
    for relative in (
        "architecture/regulator-identity-enrichment.md",
        "architecture/atr/04-sn-merge-gate.md",
        "architecture/overview.md",
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, target)


def test_qualified_identity_contract_accepts_current_docs(tmp_path: pathlib.Path) -> None:
    checker = load_checker()
    copy_contract_docs(tmp_path)

    checker.validate_documents(tmp_path)


def test_qualified_identity_contract_rejects_serial_only_merge_wording(tmp_path: pathlib.Path) -> None:
    checker = load_checker()
    copy_contract_docs(tmp_path)
    path = tmp_path / "architecture/regulator-identity-enrichment.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(
            "a serial-only match, a\nMAC-only match, or a matching model signature alone MUST NOT merge independent\naddresses.",
            "a serial-only match may merge independent addresses.",
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(checker.CheckError, match="serial-only"):
        checker.validate_documents(tmp_path)
