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
    ("including collector restarts", "excluding collector restarts"),
    ("durably persisted before publication", "persisted after publication"),
    ("must never be reassigned", "may be reassigned"),
    ("exhaustion makes the replacement unavailable", "exhaustion reuses a retired slot"),
    ("omit all semantic values", "publish semantic values"),
    ("until the original registry is restored and bindings are revalidated.", "until restart."),
    ("Do not export raw asset IDs", "Export raw asset IDs"),
    ("Do not turn arbitrary pack dimension text into labels.", "Allow arbitrary dimension labels."),
    ("A slot must not silently aggregate different sources or dimensions.", "A slot may aggregate sources."),
    ("replace an endpoint-valued `instance` before ingestion", "retain an endpoint-valued `instance`"),
    ("must not copy native payloads or private identifiers", "may copy private identifiers"),
    ("contributions fail closed", "contributions fail open"),
    ("do not evict them to admit new series", "evict them to admit new series"),
    ("`thermal`, `infrastructure` and `field`", "`thermal`, `infrastructure`, `can` and `field`"),
    ("helianthus_thermal_power_watts", "helianthus_thermal_power_kilowatts"),
    ("thermal.measurement.power", "thermal.measurement.unreviewed"),
    ("litre/minute / 60,000", "litre/minute / 60"),
    ("idle=0, heating=1", "idle=1, heating=0"),
    ("ebus_passive_tap_connected` | gauge", "ebus_passive_tap_connected` | counter"),
    ("| `window`: `1m`, `5m`, `15m`, `1h` |", "| `window`: `1m`, `5m`, `15m`, `1h`, `1d` |"),
    ("| gauge / physical symbols per second | none |", "| gauge / physical symbols per second | `bus` |"),
    ("**no value sample**", "a zero-filled value sample"),
    ("original receipt and explicit non-current state", "current receipt and current state"),
    ("reevaluation cannot refresh acquisition time", "reevaluation refreshes acquisition time"),
    ("Do not compute `rate` on energy gauges", "Compute `rate` on energy gauges"),
    ("They have no exporter reset-to-zero operation", "They reset to zero on reconnect"),
    ("Reconnection does not mean a new counter epoch", "Reconnection starts a new counter epoch"),
    ("**Target**, gateway transport timing owner", "Implemented, gateway transport timing owner"),
    ("absent if collector not implemented/configured", "always emitted"),
    ("**Pending CAN acquisition**", "Implemented CAN acquisition"),
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
    text = text.replace("reevaluation cannot refresh acquisition time.",
                        "reevaluation cannot\nrefresh acquisition time.")
    text = text.replace("Bus store; implemented,", "Bus store;   implemented,")
    CHECKER.validate(text)


@pytest.mark.parametrize("operation", ["remove", "duplicate", "add"])
def test_prometheus_semantic_coverage_rejects_admission_clause_drift(operation: str) -> None:
    text = document()
    heading = "## Bounded label and admission contract\n"
    next_heading = "## Missing values, lifecycle and resets\n"
    admission = CHECKER.section(text, heading, next_heading)
    for clause in admission.strip().split("\n- "):
        clause = clause if clause.startswith("- ") else "- " + clause
        assert clause in admission
        if operation == "remove":
            changed = admission.replace(clause, "", 1)
        elif operation == "duplicate":
            changed = admission.replace(clause, clause + "\n" + clause, 1)
        else:
            changed = admission.replace(clause, clause + "\n- Allow arbitrary labels.", 1)
        with pytest.raises(CHECKER.CheckError):
            CHECKER.validate(text.replace(admission, changed, 1))


@pytest.mark.parametrize("operation", ["remove", "duplicate", "add"])
def test_prometheus_semantic_coverage_rejects_lifecycle_clause_drift(operation: str) -> None:
    text = document()
    lifecycle = CHECKER.section(text, "## Missing values, lifecycle and resets\n",
                              "## Transport coverage\n")
    for clause in lifecycle.strip().split("\n\n"):
        if operation == "remove":
            changed = lifecycle.replace(clause, "", 1)
        elif operation == "duplicate":
            changed = lifecycle.replace(clause, clause + "\n\n" + clause, 1)
        else:
            changed = lifecycle.replace(clause, clause + "\n\nZero fill is allowed.", 1)
        with pytest.raises(CHECKER.CheckError, match="missing values, lifecycle or resets"):
            CHECKER.validate(text.replace(lifecycle, changed, 1))


def test_prometheus_semantic_coverage_rejects_each_transport_coverage_change() -> None:
    text = document()
    transport = CHECKER.section(text, "## Transport coverage\n",
                              "## Semantic coverage and units\n")
    table_rows = [line for line in transport.splitlines() if line.startswith("|")][2:]
    for row in table_rows:
        cells = row.split("|")
        cells[4] = " Always implemented and available "
        with pytest.raises(CHECKER.CheckError, match="transport metric"):
            CHECKER.validate(text.replace(row, "|".join(cells), 1))


def test_prometheus_semantic_coverage_registered_in_ci() -> None:
    gate = (ROOT / "scripts/ci_local.sh").read_text()
    assert "python3 scripts/validate_prometheus_semantic_coverage.py\n" in gate
    assert "python3 -m pytest -q tests/test_prometheus_semantic_coverage.py\n" in gate
