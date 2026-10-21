"""Validate the proposed DHW contract; no native or runtime qualification."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "architecture/fixtures/dhw-setpoint-semreg-cutover-v1.json"
DOCUMENT = ROOT / "architecture/dhw-setpoint-semreg-cutover.md"
FACT = "thermal.setpoint.dhw_temperature"
CLAUSES = (
    "The current Thermal validator rejects the proposed additional `thermal.dimension.dhw` on this fact.",
    "Removing the service dimension merely to pass validation would lose identity.",
    "For canonical projection requests, emit exactly one disposition per requested `(kind,item_id)`",
    "per-source absence must not overwrite an already projected shared definition.",
    "Bounds with no canonical definition are described as contextual losses, not fabricated requested items.",
    "a projection evaluation never changes receipt time.",
    "No consumer silently converts a missing target to zero or a limit to a target.",
)


def fixture():
    return json.loads(FIXTURE.read_text())


def validate_contract(data, document):
    assert data["evidence_status"] == "Hypothesis"
    assert data["scope"] == "synthetic_read_projection_contract"
    assert data["current_pack_accepts_proposed_keys"] is False
    for key, service in zip(data["keys"], ("dhw:alpha", "dhw:beta"), strict=True):
        assert key == {
            "pack_id": "helianthus.pack.thermal", "pack_version": "1.0.0",
            "fact_id": FACT, "dimensions": [
                {"id": "thermal.dimension.dhw", "value": {"kind": "text", "text": service}},
                {"id": "thermal.dimension.temperature", "value": {"kind": "text", "text": "temperature:dhw_requested"}},
            ],
        }
    assert data["value"] == {"kind": "quantity", "quantity": {
        "number": {"coefficient": "5", "exponent10": 1}, "unit": "unit.celsius",
    }}
    assert len(data["projection_cases"]) == 2
    for case, name, absent in zip(
        data["projection_cases"], ("two_services", "partial_absence"),
        ([], ["dhw:beta"]), strict=True,
    ):
        assert case == {
            "case": name, "requested": [{"kind": "fact", "item_id": FACT}],
            "dispositions": [{"kind": "fact", "item_id": FACT, "outcome": "withheld",
                              "source_keys": [], "loss": ["dhw_service_identity_unrepresentable"]}],
            "absent_services": absent,
        }
    visible = " ".join(document.split())
    for token in ("FactKey.PackID = helianthus.pack.thermal", "PackVersion = 1.0.0",
                  f"FactID = {FACT}", "thermal.dimension.dhw",
                  "thermal.dimension.temperature", "temperature:dhw_requested",
                  "dhw:alpha", "thermal.service.dhw", "thermal.capability.read.dhw",
                  "unit.celsius"):
        assert f"`{token}`" in visible
    for clause in CLAUSES:
        assert clause in visible


def test_dhw_setpoint_semreg_contract():
    validate_contract(fixture(), DOCUMENT.read_text())
    gate = (ROOT / "scripts/ci_local.sh").read_text()
    assert "python3 -m pytest -q tests/test_dhw_setpoint_semreg_cutover.py\n" in gate


@pytest.mark.parametrize("field", ("pack_id", "pack_version", "fact_id", "dimensions"))
def test_dhw_setpoint_rejects_binding_drift(field):
    data = fixture()
    data["keys"][0][field] = "invalid"
    with pytest.raises(AssertionError):
        validate_contract(data, DOCUMENT.read_text())


@pytest.mark.parametrize("mutation", ("duplicate", "global_absence", "foreign_owner", "zero_default", "unit", "dimension_type"))
def test_dhw_setpoint_rejects_projection_and_value_drift(mutation):
    data = fixture()
    case = data["projection_cases"][1]
    if mutation == "duplicate":
        case["dispositions"].append(deepcopy(case["dispositions"][0]))
    elif mutation == "global_absence":
        case["dispositions"][0]["outcome"] = "unsupported"
    elif mutation == "foreign_owner":
        case["dispositions"][0]["source_keys"] = [data["keys"][1]]
    elif mutation == "zero_default":
        data["value"]["quantity"]["number"]["coefficient"] = "0"
    elif mutation == "unit":
        data["value"]["quantity"]["unit"] = "unit.kelvin"
    else:
        data["keys"][0]["dimensions"][0]["value"] = {"kind": "boolean", "boolean": False}
    with pytest.raises(AssertionError):
        validate_contract(data, DOCUMENT.read_text())


@pytest.mark.parametrize("clause", CLAUSES)
def test_dhw_setpoint_rejects_document_invariant_drift(clause):
    document = " ".join(DOCUMENT.read_text().split())
    with pytest.raises(AssertionError):
        validate_contract(fixture(), document.replace(clause, "omitted"))


@pytest.mark.parametrize("token", (
    "FactKey.PackID = helianthus.pack.thermal", "PackVersion = 1.0.0",
    f"FactID = {FACT}", "temperature:dhw_requested", "thermal.dimension.dhw",
    "thermal.dimension.temperature",
))
def test_dhw_setpoint_rejects_document_binding_drift(token):
    with pytest.raises(AssertionError):
        validate_contract(fixture(), DOCUMENT.read_text().replace(f"`{token}`", "`invalid`"))
