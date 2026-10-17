from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prometheus_semantic_coverage", ROOT / "scripts/validate_prometheus_semantic_coverage.py"
)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def document() -> str:
    return (ROOT / CHECKER.DOCUMENT).read_text(encoding="utf-8")


def test_prometheus_semantic_coverage_accepts_document() -> None:
    CHECKER.validate(document())


@pytest.mark.parametrize(("old", "new"), [
    ("`0..15`", "`0..31`"),
    ("`thermal, infrastructure`", "`thermal, infrastructure, can`"),
    ("`domain_field_table`", "`arbitrary_fields`"),
    ("`semantic_values` | `slot`", "`semantic_values` | `asset`"),
    ("helianthus_thermal_power_watts", "helianthus_thermal_power_kilowatts"),
    ("thermal.measurement.power", "thermal.measurement.unreviewed"),
    ("litre/minute / 60,000", "litre/minute / 60"),
    ("idle=0, heating=1", "idle=1, heating=0"),
    ("ebus_passive_tap_connected` | gauge", "ebus_passive_tap_connected` | counter"),
    ("| `window`: `1m`, `5m`, `15m`, `1h` |", "| `window`: `1m`, `5m`, `15m`, `1h`, `1d` |"),
    ("| gauge / physical symbols per second | none |", "| gauge / physical symbols per second | `bus` |"),
    ("ebus_passive_tap_connected == 0", "ebus_passive_tap_connected == 1"),
    ("on(job, instance, slot)", "on(job, instance)"),
    ('field="thermal.status.fault"', 'field="thermal.status.operation"'),
    ('domain="infrastructure",field=', 'domain="thermal",field='),
    ("helianthus_semantic_field_available == 0", "helianthus_semantic_field_available == 0 or vector(0)"),
    ("for: 10m", "for: 0m"),
    ("severity: info", "severity: critical"),
    ("expr: ebus_passive_tap_connected == 0", "expr: ignored\n        expr: ebus_passive_tap_connected == 0"),
    ("groups:\n", "groups: []\nignored:\n"),
])
def test_prometheus_semantic_coverage_rejects_contract_drift(old: str, new: str) -> None:
    text = document()
    assert old in text
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate(text.replace(old, new))


@pytest.mark.parametrize("operation", ["remove", "duplicate", "add", "swap", "move"])
def test_prometheus_semantic_coverage_rejects_table_drift(operation: str) -> None:
    text = document()
    row = next(line for line in text.splitlines(keepends=True)
               if line.startswith('| `thermal.measurement.power`'))
    if operation == "remove":
        text = text.replace(row, "")
    elif operation == "duplicate":
        text = text.replace(row, row * 2)
    elif operation == "add":
        text = text.replace(row, row + row.replace("power", "unreviewed"))
    elif operation == "swap":
        text = text.replace("helianthus_thermal_power_watts", "temporary_metric")
        text = text.replace("helianthus_thermal_demand_ratio", "helianthus_thermal_power_watts")
        text = text.replace("temporary_metric", "helianthus_thermal_demand_ratio")
    else:
        text = text.replace(row, "").replace("### Infrastructure\n", "### Infrastructure\n" + row)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate(text)


def test_prometheus_semantic_coverage_accepts_formatting_and_row_order() -> None:
    text = document()
    lines = [line for line in text.splitlines(keepends=True)
             if line.startswith('| `thermal.') and len(CHECKER.rows(line)[0]) == 3]
    text = text.replace("".join(lines), "".join(reversed(lines)))
    text = text.replace('| `thermal.', '|  `thermal.')
    text = text.replace("and on(job, instance, slot)\n", "and   on(job, instance, slot)\n")
    text = text.replace("reevaluation cannot refresh acquisition time.",
                        "reevaluation cannot\nrefresh acquisition time.")
    text = text.replace("Bus store; implemented,", "Bus store;   implemented,")
    CHECKER.validate(text)


def test_prometheus_semantic_coverage_registered_in_ci() -> None:
    gate = (ROOT / "scripts/ci_local.sh").read_text()
    assert "python3 scripts/validate_prometheus_semantic_coverage.py\n" in gate
    assert "python3 -m pytest -q tests/test_prometheus_semantic_coverage.py\n" in gate


@pytest.mark.parametrize(("old", "new"), [
    ("Setpoint visibility supplies no write authority.",
     "Observing a setpoint grants no permission to write."),
    ("The rolling-average candidate remains\nwithheld:",
     "The candidate for the rolling average is withheld:"),
    ("The baud target measures physical signaling intervals over a completed,",
     "Physical signaling intervals determine the baud target over a completed,"),
    ("The new baud series have no exporter labels:",
     "Exporter labels are absent from the new baud series:"),
    ("They have no exporter reset-to-zero operation.",
     "The exporter cannot reset these gauges to zero."),
    ("Bus store; implemented in inspected source, known connection state 0/1; exact-candidate revalidation required",
     "The bus store implements known connection state; revalidate the candidate"),
    ("summary: Passive tap reports disconnected", "summary: Passive tap is disconnected"),
])
def test_prometheus_semantic_coverage_accepts_rewording(old: str, new: str) -> None:
    text = document()
    assert old in text
    CHECKER.validate(text.replace(old, new))


@pytest.mark.parametrize("operation", ["remove", "duplicate", "add"])
def test_prometheus_semantic_coverage_rejects_label_rows(operation: str) -> None:
    text = document()
    row = "| `semantic_values` | `slot` | `0..15` |\n"
    replacement = {"remove": "", "duplicate": row * 2,
                   "add": row + row.replace("`slot`", "`asset`")}[operation]
    with pytest.raises(CHECKER.CheckError, match="structured label domains"):
        CHECKER.validate(text.replace(row, replacement))


@pytest.mark.parametrize(("old", "new"), [
    ("| `thermal.measurement.air_temperature` |\n",
     "| `thermal.measurement.power` |\n"),
    ("| `thermal.measurement.air_temperature` |\n", ""),
    ("| `thermal.measurement.air_temperature` |\n",
     "| `thermal.measurement.air_temperature` |\n" * 2),
    ("| `state.outdoor_temperature_avg24h` | `rolling_average_window_unrepresentable` |\n", ""),
    ("| `state.outdoor_temperature_avg24h` | `rolling_average_window_unrepresentable` |\n",
     "| `state.outdoor_temperature_avg24h` |\n"),
    ("| `state.outdoor_temperature_avg24h` | `rolling_average_window_unrepresentable` |\n",
     "| `state.outdoor_temperature` | `rolling_average_window_unrepresentable` |\n"),
    ("| `state.outdoor_temperature_avg24h` | `rolling_average_window_unrepresentable` |\n",
     "| `state.outdoor_temperature_avg24h` | `other_loss` |\n"),
])
def test_prometheus_semantic_coverage_rejects_disposition_drift(old: str, new: str) -> None:
    text = document()
    assert text.count(old) == 1
    with pytest.raises(CHECKER.CheckError, match="source fixture"):
        CHECKER.validate(text.replace(old, new))


@pytest.mark.parametrize("mutation", ["exact", "field", "loss", "add_withheld", "remove_withheld"])
def test_prometheus_semantic_coverage_derives_dispositions_from_source(tmp_path: Path, mutation: str) -> None:
    fixture = json.loads(CHECKER.THERMAL_FIXTURE.read_text())
    mappings = fixture["mappings"]
    assert mappings[2]["semreg_fact"] is None
    if mutation == "exact":
        mappings[0]["semreg_fact"] = "thermal.measurement.power"
    elif mutation == "field":
        mappings[2]["legacy_system_field"] = "state.other_average"
    elif mutation == "loss":
        mappings[2]["loss"] = "other_loss"
    elif mutation == "add_withheld":
        mappings.append(dict(mappings[2], legacy_system_field="state.other_average"))
    else:
        mappings.pop()
    source = tmp_path / "thermal.json"
    source.write_text(json.dumps(fixture))
    with pytest.raises(CHECKER.CheckError, match="source fixture"):
        CHECKER.validate(document(), thermal_fixture=source)
    # Matching source and structured claim changes pass, proving there is no
    # independent list of exact facts or withheld associations in the checker.
    if mutation == "exact":
        CHECKER.validate(document().replace("| `thermal.measurement.air_temperature` |\n",
                                          "| `thermal.measurement.power` |\n"),
                         thermal_fixture=source)


def test_prometheus_semantic_coverage_accepts_source_order_and_shared_exact_fact(tmp_path: Path) -> None:
    fixture = json.loads(CHECKER.THERMAL_FIXTURE.read_text())
    fixture["mappings"].append(dict(fixture["mappings"][0], legacy_system_field="state.other_temperature"))
    fixture["mappings"].reverse()
    source = tmp_path / "thermal.json"
    source.write_text(json.dumps(fixture))
    CHECKER.validate(document(), thermal_fixture=source)
