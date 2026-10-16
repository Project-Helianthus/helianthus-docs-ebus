from __future__ import annotations

import importlib.util
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
    ("32\n  fields", "33\n  fields"),
    ("1024", "2048"),
    ("`0` through `15`", "`0` through `31`"),
    ("16 value and 16 availability", "16 value and 32 availability"),
    ("series have only `slot`", "series have only `slot`, `asset`"),
    ("`thermal`, `infrastructure` and `field`", "`thermal`, `infrastructure`, `can` and `field`"),
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
    lines = [line for line in text.splitlines(keepends=True) if line.startswith('| `thermal.')]
    text = text.replace("".join(lines), "".join(reversed(lines)))
    text = text.replace('| `thermal.', '|  `thermal.')
    text = text.replace("and on(job, instance, slot)\n", "and   on(job, instance, slot)\n")
    CHECKER.validate(text)


def test_prometheus_semantic_coverage_registered_in_ci() -> None:
    gate = (ROOT / "scripts/ci_local.sh").read_text()
    assert "python3 scripts/validate_prometheus_semantic_coverage.py\n" in gate
    assert "python3 -m pytest -q tests/test_prometheus_semantic_coverage.py\n" in gate
