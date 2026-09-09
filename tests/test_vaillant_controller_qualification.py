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


def test_accepts_unknown_evidence_gap() -> None:
    CHECKER.validate_fixture(fixture(), thermal())
    assert b"](" not in CHECKER.receipt_bytes()


@pytest.mark.parametrize(
    ("field", "value"),
    (("path", "architecture/fixtures/not-the-receipt.json"), ("sha256", "a" * 64), ("sha256_path", "architecture/fixtures/not-the-receipt.sha256")),
)
def test_rejects_hostile_receipt_substitution(field: str, value: str) -> None:
    candidate = deepcopy(fixture())
    candidate["context_receipt"][field] = value  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())


def test_rejects_digest_mismatch_for_the_exact_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(CHECKER, "receipt_bytes", lambda: b"not the pinned receipt")
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(fixture(), thermal())


def test_rejects_receipt_provenance_or_sidecar_substitution(monkeypatch: pytest.MonkeyPatch) -> None:
    original_receipt_bytes = CHECKER.receipt_bytes
    receipt = deepcopy(CHECKER.RECEIPT)
    receipt["canonical_upstream"]["revision"] = "f" * 40
    monkeypatch.setattr(CHECKER, "receipt_bytes", lambda: json.dumps(receipt).encode())
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(fixture(), thermal())

    sidecar = Path(CHECKER.CONTEXT_RECEIPT["sha256_path"])
    original_read_text = Path.read_text

    def bad_sidecar(path: Path, *args: object, **kwargs: object) -> str:
        if path == sidecar:
            return "a" * 64 + "  wrong.json\n"
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", bad_sidecar)
    monkeypatch.setattr(CHECKER, "receipt_bytes", original_receipt_bytes)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(fixture(), thermal())


def test_rejects_claiming_direct_evidence_or_runtime_authority() -> None:
    candidate = deepcopy(fixture())
    candidate["evidence_status"] = "Proven"  # type: ignore[index]
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
