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


def test_accepts_exact_observed_tuple() -> None:
    CHECKER.validate_fixture(fixture(), thermal())


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("direct_identification", "software_version"), "0508"),
        (("direct_identification", "hardware_version"), "1705"),
        (("direct_identification", "target_address"), "0x08"),
        (("direct_identification", "manufacturer_wire_byte"), "0x19"),
    ),
)
def test_rejects_unsupported_or_address_mismatch(path: tuple[str, str], value: str) -> None:
    candidate = deepcopy(fixture())
    candidate[path[0]][path[1]] = value  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())


@pytest.mark.parametrize("member", ("manufacturer", "device_id", "serial_number"))
def test_rejects_missing_or_sentinel_authority_rule(member: str) -> None:
    candidate = deepcopy(fixture())
    candidate["required_current_authority"]["complete_identity_witness"].remove(member)  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())


def test_rejects_evidence_or_thermal_binding_tampering() -> None:
    candidate = deepcopy(fixture())
    candidate["native_evidence"]["sha256"] = "a" * 64  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(candidate, thermal())

    changed_thermal = deepcopy(thermal())
    changed_thermal["qualification"]["rule_revision"] = "wrong"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_fixture(fixture(), changed_thermal)
