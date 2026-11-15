"""Validate the proposed DHW contract; no native or runtime qualification."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "architecture/fixtures/dhw-setpoint-semreg-cutover-v1.json"
DOCUMENT = ROOT / "architecture/dhw-setpoint-semreg-cutover.md"
SPEC = importlib.util.spec_from_file_location(
    "vaillant_semreg_thermal_map", ROOT / "scripts/validate_vaillant_semreg_thermal_map.py"
)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)

FACT = "thermal.setpoint.dhw_temperature_setpoint"
PAGE_FACT = "thermal.setpoint.dhw_temperature"
NATIVE_KEY = "PB=0xB5 SB=0x24 OP=0x02 GG=0x01 II=0x00 RR=0x0004"
HOT_WATER_GROUP = "OP=0x02 GG=0x01 II=0x00"
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


def validate_fixture(data):
    CHECKER.validate_dhw(data)


def validate_page(document):
    visible = " ".join(document.split())
    for token in ("FactKey.PackID = helianthus.pack.thermal", "PackVersion = 1.0.0",
                  f"FactID = {PAGE_FACT}", "thermal.dimension.dhw",
                  "thermal.dimension.temperature", "temperature:dhw_requested",
                  "dhw:alpha", "thermal.service.dhw", "thermal.capability.read.dhw",
                  "unit.celsius"):
        assert f"`{token}`" in visible
    for clause in CLAUSES:
        assert clause in visible


def rejects(data):
    with pytest.raises(CHECKER.CheckError):
        validate_fixture(data)


def test_dhw_setpoint_semreg_contract():
    validate_fixture(fixture())
    validate_page(DOCUMENT.read_text())
    gate = (ROOT / "scripts/ci_local.sh").read_text()
    assert "python3 -m pytest -q tests/test_dhw_setpoint_semreg_cutover.py\n" in gate


def test_dhw_row_is_keyed_by_native_identity_and_names_its_native_resource():
    data = fixture()
    assert data["native_resources"] == [{"selector": HOT_WATER_GROUP, "kind": "dhw_instance"}]
    [row] = data["rows"]
    assert row["native_key"] == NATIVE_KEY
    assert row["native_resource"] == HOT_WATER_GROUP
    assert row["native_value"] == {"wire_type": "f32_le", "unit": "degC"}
    assert row["relation_candidates"]["refs"] == []
    assert row["relation_candidates"]["absence"]
    assert row["target"] == {
        "definition": {
            "pack": {"id": "helianthus.pack.thermal", "version": "1.0.0"},
            "id": FACT, "version": "1.0.0",
        },
        "element_kind": "fact",
        "disposition": "unknown",
        "planes": [],
        "reason": "catalog.reason.subject_unresolved",
    }


def test_service_identity_gap_is_an_unresolved_subject_not_a_projection_loss():
    data = fixture()
    [row] = data["rows"]
    assert row["subject"] == {"status": "unresolved", "sources": ["alpha", "beta"]}
    for case in data["projection_cases"]:
        for disposition in case["dispositions"]:
            assert disposition["loss"] == []
            assert disposition["reason"] == row["target"]["reason"]


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("PB", "0xB6"), ("SB", "0x23"), ("OP", "0x06"),
        ("GG", "0x00"), ("II", "0x01"), ("RR", "0x0005"),
    ),
)
def test_dhw_rejects_native_key_drift(field, value):
    data = fixture()
    row = data["rows"][0]
    parts = dict(part.split("=") for part in row["native_key"].split())
    parts[field] = value
    row["native_key"] = " ".join(f"{name}={parts[name]}" for name in ("PB", "SB", "OP", "GG", "II", "RR"))
    rejects(data)


@pytest.mark.parametrize(
    ("path", "value"),
    (
        (("definition", "pack", "id"), "helianthus.pack.storage"),
        (("definition", "pack", "version"), "1.1.0"),
        (("definition", "id"), PAGE_FACT),
        (("definition", "version"), "1.0.1"),
        (("element_kind",), "dimension"),
        (("disposition",), "member"),
        (("planes",), ["control"]),
        (("reason",), "catalog.reason.no_fact_or_relation"),
    ),
)
def test_dhw_rejects_target_drift_in_every_member(path, value):
    data = fixture()
    target = data["rows"][0]["target"]
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    rejects(data)


@pytest.mark.parametrize("attachment", ("ordinal", "ordinal_text", "unlisted"))
def test_dhw_rejects_an_ordinal_or_unlisted_attachment(attachment):
    data = fixture()
    data["rows"][0]["native_resource"] = {
        "ordinal": 0, "ordinal_text": "0", "unlisted": "OP=0x02 GG=0x05 II=0x00",
    }[attachment]
    rejects(data)


@pytest.mark.parametrize(
    ("selector", "kind"),
    (
        ("OP=0x06 GG=0x01 II=0x00", "dhw_instance"),
        ("OP=0x02 GG=0x00 II=0x00", "dhw_instance"),
        ("OP=0x02 GG=0x01 II=0x01", "dhw_instance"),
        (HOT_WATER_GROUP, "cylinder_instance"),
    ),
)
def test_dhw_rejects_a_false_join(selector, kind):
    data = fixture()
    data["native_resources"] = [{"selector": selector, "kind": kind}]
    data["rows"][0]["native_resource"] = selector
    rejects(data)


def test_dhw_rejects_a_dangling_endpoint():
    data = fixture()
    data["rows"][0]["relation_candidates"] = {"refs": ["SRC-SD15-module-cylinder"], "absence": None}
    rejects(data)


@pytest.mark.parametrize(
    "mutation",
    ("duplicate", "global_absence", "foreign_owner", "loss", "no_reason", "resolved_subject",
     "dimension_text", "semantic_value"),
)
def test_dhw_rejects_projection_and_subject_drift(mutation):
    data = fixture()
    case = data["projection_cases"][1]
    if mutation == "duplicate":
        case["dispositions"].append(deepcopy(case["dispositions"][0]))
    elif mutation == "global_absence":
        case["dispositions"][0]["outcome"] = "unsupported"
    elif mutation == "foreign_owner":
        case["dispositions"][0]["source_keys"] = [{"pack_id": "helianthus.pack.thermal"}]
    elif mutation == "loss":
        case["dispositions"][0]["loss"] = ["dhw_service_identity_unrepresentable"]
    elif mutation == "no_reason":
        case["dispositions"][0]["reason"] = None
    elif mutation == "resolved_subject":
        data["rows"][0]["subject"]["status"] = "resolved"
    elif mutation == "dimension_text":
        data["rows"][0]["dimensions"] = [{"id": "thermal.dimension.dhw", "value": {"kind": "text", "text": "dhw:alpha"}}]
    else:
        data["rows"][0]["value"] = {"kind": "quantity", "quantity": {"number": {"coefficient": "5", "exponent10": 1}, "unit": "unit.kelvin"}}
    rejects(data)


@pytest.mark.parametrize("unit", ("unit.celsius", "unit.kelvin"))
def test_dhw_keeps_the_native_unit(unit):
    data = fixture()
    data["rows"][0]["native_value"]["unit"] = unit
    rejects(data)


@pytest.mark.parametrize("clause", CLAUSES)
def test_dhw_setpoint_rejects_document_invariant_drift(clause):
    document = " ".join(DOCUMENT.read_text().split())
    with pytest.raises(AssertionError):
        validate_page(document.replace(clause, "omitted"))


@pytest.mark.parametrize("token", (
    "FactKey.PackID = helianthus.pack.thermal", "PackVersion = 1.0.0",
    f"FactID = {PAGE_FACT}", "temperature:dhw_requested", "thermal.dimension.dhw",
    "thermal.dimension.temperature",
))
def test_dhw_setpoint_rejects_document_binding_drift(token):
    with pytest.raises(AssertionError):
        validate_page(DOCUMENT.read_text().replace(f"`{token}`", "`invalid`"))
