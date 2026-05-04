from __future__ import annotations

import importlib.util
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / "scripts/check_source_address_table_against_official_specs.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("source_address_checker", CHECKER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_address_table_mutation_canary() -> None:
    checker = load_checker()
    fixture = checker.load_fixture()
    expected = checker.expected_rows_from_fixture(fixture)
    doc_text = checker.read_text(checker.DOC_PATH)
    mutated = doc_text.replace(
        "| `0x71` | p1 | `0x1` | Heating controller | Heating regulator | no | none | `0x76` |",
        "| `0x71` | p1 | `0x1` | Heating controller | Heating regulator | no | none | `0x77` |",
        1,
    )

    with pytest.raises(checker.CheckError) as excinfo:
        checker.validate_doc_text(mutated, expected, check_hash=False)

    message = str(excinfo.value)
    assert "row 9" in message
    assert "source 0x71" in message
    assert "field companion" in message
    assert "expected '0x76'" in message
    assert "got '0x77'" in message
