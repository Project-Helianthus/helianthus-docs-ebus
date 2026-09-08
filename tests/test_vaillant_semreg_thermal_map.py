from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "architecture/fixtures/vaillant-semreg-thermal-map-v1.json"
SPEC = importlib.util.spec_from_file_location(
    "vaillant_semreg_thermal_map", ROOT / "scripts/validate_vaillant_semreg_thermal_map.py"
)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def index() -> dict[str, object]:
    return json.loads(INDEX.read_text(encoding="utf-8"))


def test_accepts_current_typed_index() -> None:
    CHECKER.validate_index(index())


def test_rejects_system_identity_as_temperature_dimension() -> None:
    mutated = deepcopy(index())
    row = mutated["mappings"][0]  # type: ignore[index]
    row["dimensions"] = {"thermal.dimension.system": "temperature:outdoor_air"}  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)


def test_rejects_operation_or_service_family_substitution() -> None:
    mutated = deepcopy(index())
    row = mutated["mappings"][1]  # type: ignore[index]
    row["native_selector"]["operation"] = "0x06"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)

    mutated = deepcopy(index())
    mutated["native_distinctions"]["b509_substitutable_for_b524_rows"] = True  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)


def test_rejects_type_unit_or_register_drift() -> None:
    mutated = deepcopy(index())
    row = mutated["mappings"][0]  # type: ignore[index]
    row["native_selector"]["wire_type"] = "u16"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("destination", "0x08"),
        ("controller_family", "HMU"),
        ("request_direction", "target_to_initiator"),
        ("value_direction", "initiator_to_target"),
    ),
)
def test_rejects_destination_family_or_direction_drift(field: str, value: str) -> None:
    mutated = deepcopy(index())
    row = mutated["mappings"][0]  # type: ignore[index]
    row["native_selector"][field] = value  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)

    mutated = deepcopy(index())
    row = mutated["mappings"][2]  # type: ignore[index]
    row["native_selector"]["register"] = "0x0073"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)


def test_rejects_withheld_and_nonclaim_drift() -> None:
    mutated = deepcopy(index())
    row = mutated["mappings"][2]  # type: ignore[index]
    row["disposition"] = "exact"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)

    mutated = deepcopy(index())
    mutated["nonclaims"]["write_route_established"] = True  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)
