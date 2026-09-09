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


def test_exact_rows_keep_native_and_semreg_units_and_delayed_evaluation_separate() -> None:
    rows = index()["mappings"]  # type: ignore[index]
    exact_rows = [row for row in rows if row["disposition"] == "exact"]  # type: ignore[index]
    for row in exact_rows:
        assert row["native_value"]["unit"] == "degC"  # type: ignore[index]
        assert row["semreg_value"] == {"kind": "quantity", "unit": "unit.celsius"}  # type: ignore[index]

    lifecycle = index()["lifecycle"]  # type: ignore[index]
    observation = lifecycle["retained_native_observation"]  # type: ignore[index]
    evaluation = lifecycle["caller_evaluation_context"]  # type: ignore[index]
    assert observation["received_at"] != evaluation["evaluated_at"]  # type: ignore[index]
    assert observation["receipt_monotonic"] != evaluation["evaluate_monotonic"]  # type: ignore[index]
    assert lifecycle["evaluation_cannot_overwrite_receipt"] is True  # type: ignore[index]
    assert lifecycle["freshness_axis"] == "elapsed_monotonic"  # type: ignore[index]


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
    row["native_value"]["wire_type"] = "u16"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)

    mutated = deepcopy(index())
    row = mutated["mappings"][0]  # type: ignore[index]
    row["native_value"]["unit"] = "unit.celsius"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)

    mutated = deepcopy(index())
    row = mutated["mappings"][0]  # type: ignore[index]
    row["semreg_value"]["unit"] = "degC"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)

    mutated = deepcopy(index())
    row = mutated["mappings"][0]  # type: ignore[index]
    del row["semreg_value"]["unit"]  # type: ignore[index]
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


def test_rejects_receipt_evaluation_boundary_or_freshness_drift() -> None:
    mutated = deepcopy(index())
    lifecycle = mutated["lifecycle"]  # type: ignore[index]
    lifecycle["caller_evaluation_context"]["evaluated_at"] = lifecycle["retained_native_observation"]["received_at"]  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)

    mutated = deepcopy(index())
    lifecycle = mutated["lifecycle"]  # type: ignore[index]
    lifecycle["evaluation_cannot_overwrite_receipt"] = False  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)

    mutated = deepcopy(index())
    lifecycle = mutated["lifecycle"]  # type: ignore[index]
    lifecycle["freshness_axis"] = "wall_clock"  # type: ignore[index]
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_index(mutated)
