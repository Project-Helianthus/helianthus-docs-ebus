from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("vaillant_controller_qualification", ROOT / "scripts/validate_vaillant_controller_qualification.py")
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def fixture() -> dict[str, object]:
    return json.loads((ROOT / "architecture/fixtures/vaillant-controller-qualification-v1.json").read_text())


def thermal() -> dict[str, object]:
    return json.loads((ROOT / "architecture/fixtures/vaillant-semreg-thermal-map-v1.json").read_text())


def test_accepts_unproven_evidence_gap() -> None:
    CHECKER.validate_fixture(fixture(), thermal())


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("canonical_url", "https://invalid.example/artifact"),
        ("revision", "f" * 40),
        ("path", "protocols/vaillant/not-the-artifact.md"),
        ("sha256", "a" * 64),
    ),
)
def test_rejects_hostile_artifact_substitution(field: str, value: str) -> None:
    candidate = deepcopy(fixture())
    candidate["context_artifact"][field] = value  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())


def test_rejects_digest_mismatch_for_the_exact_artifact(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CHECKER, "artifact_bytes", lambda: b"not the pinned artifact")
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(fixture(), thermal())


def test_rejects_claiming_direct_evidence_or_runtime_authority() -> None:
    candidate = deepcopy(fixture())
    candidate["evidence_status"] = "proven"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())

    candidate = deepcopy(fixture())
    candidate["qualified_use_permitted"] = True  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())

    candidate = deepcopy(fixture())
    candidate["direct_identification_evidence"] = {"invented": True}  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())


def test_rejects_transition_or_thermal_binding_ambiguity() -> None:
    candidate = deepcopy(fixture())
    candidate["transition_contract"]["valid_direct_conflicting_observation"] = "reject_without_mutation"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())

    changed_thermal = deepcopy(thermal())
    changed_thermal["qualification"]["runtime_qualification_permitted"] = True  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(fixture(), changed_thermal)
