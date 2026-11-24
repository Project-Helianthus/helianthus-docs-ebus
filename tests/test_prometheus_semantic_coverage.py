from __future__ import annotations

import importlib.util
import json
import re
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
    ("thermal.measurement.thermal_power", "thermal.measurement.unreviewed"),
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
               if line.startswith('| `thermal.measurement.thermal_power`'))
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
    ("| `thermal.measurement.outdoor_air_temperature` |\n",
     "| `thermal.measurement.power` |\n"),
    ("| `thermal.measurement.outdoor_air_temperature` |\n", ""),
    ("| `thermal.measurement.outdoor_air_temperature` |\n",
     "| `thermal.measurement.outdoor_air_temperature` |\n" * 2),
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
        CHECKER.validate(document().replace("| `thermal.measurement.outdoor_air_temperature` |\n",
                                          "| `thermal.measurement.power` |\n"),
                         thermal_fixture=source)


def test_prometheus_semantic_coverage_accepts_source_order_and_shared_exact_fact(tmp_path: Path) -> None:
    fixture = json.loads(CHECKER.THERMAL_FIXTURE.read_text())
    fixture["mappings"].append(dict(fixture["mappings"][0], legacy_system_field="state.other_temperature"))
    fixture["mappings"].reverse()
    source = tmp_path / "thermal.json"
    source.write_text(json.dumps(fixture))
    CHECKER.validate(document(), thermal_fixture=source)


@pytest.mark.parametrize("row", CHECKER.rows("\n".join(
    "| " + line for line in CHECKER.RENDERER_ROWS.strip().splitlines())))
@pytest.mark.parametrize("field", range(4), ids=["name", "type", "labels", "constant_unit"])
def test_emitted_metric_tuple_rejects_each_changed_field(row, field):
    # Name catches renaming/collision; type catches counter/gauge changes;
    # labels catch cardinality expansion; constant_unit catches unit drift.
    text = document()
    original = "| " + " | ".join("`" + value + "`" for value in row) + " |"
    changed = list(row)
    changed[field] = {0: "unauthorized_series", 1: "untyped",
                      2: "unbounded_identity",
                      3: "celsius" if row[3] == "kelvin" else "kelvin"}[field]
    replacement = "| " + " | ".join("`" + value + "`" for value in changed) + " |"
    assert text.count(original) == 1
    with pytest.raises(CHECKER.CheckError, match="emitted metric"):
        CHECKER.validate(text.replace(original, replacement))


@pytest.mark.parametrize("operation", ["missing", "extra", "duplicate", "collision"])
def test_emitted_metric_membership_rejects_drift(operation):
    text = document()
    row = "| `helianthus_semantic_evidence_age` | `gauge` | `connector, dimension, fact, pack, resource, resource_kind, unit` | `seconds` |"
    assert row in text
    replacement = {"missing": "", "extra": row + "\n" + row.replace(
        "helianthus_semantic_evidence_age", "unregistered_series"),
        "duplicate": row + "\n" + row,
        "collision": row.replace("helianthus_semantic_evidence_age",
                                  "helianthus_thermal_air_temperature")}[operation]
    with pytest.raises(CHECKER.CheckError, match="emitted metric"):
        CHECKER.validate(text.replace(row, replacement))


@pytest.mark.parametrize(("canonical", "removed"), [
    ("helianthus_semantic_evidence_age", "helianthus_semantic_evidence_age_seconds"),
    ("helianthus_thermal_air_temperature", "helianthus_thermal_air_temperature_celsius"),
    ("helianthus_thermal_temperature_setpoint", "helianthus_thermal_setpoint_celsius"),
])
def test_emitted_metric_rejects_removed_spelling(canonical, removed):
    text = document()
    row = next(line for line in text.splitlines()
               if line.startswith("| `" + canonical + "` | `gauge`"))
    with pytest.raises(CHECKER.CheckError, match="emitted metric"):
        CHECKER.validate(text.replace(row, row + "\n" + row.replace(canonical, removed)))


NATIVE_ROW_TEXT = "| `helianthus_native_temperature` | `gauge` | temperature | `kelvin` | `protocol, device, index, point, unit, driver_instance` | `emitted` |"
NATIVE_LABELS = "`protocol, device, index, point, unit, driver_instance`"


def native_rows():
    return CHECKER.rows("\n".join("| " + line for line in CHECKER.NATIVE_ROWS.strip().splitlines()))


def test_native_families_are_members_of_the_emitted_table():
    assert len(native_rows()) == 15
    emitted = CHECKER.rows("\n".join("| " + line for line in CHECKER.RENDERER_ROWS.strip().splitlines()))
    assert len(emitted) == 124
    assert "all 124 custom families" in document()
    by_name = {row[0]: row for row in emitted}
    for name, kind, _quantity, unit, labels, status in native_rows():
        assert status == "emitted"
        assert by_name[name] == (name, kind, labels, unit)
    native = document().split("## Native point coverage\n", 1)[1]
    assert "1,024 value series" not in native
    assert "lifetime admission set of value series" not in native


@pytest.mark.parametrize("row", native_rows(), ids=lambda row: row[0])
@pytest.mark.parametrize("field", range(6),
                         ids=["name", "type", "quantity", "constant_unit", "labels", "status"])
def test_native_family_tuple_rejects_each_changed_field(row, field):
    # name catches an unreviewed family; type catches a counter; quantity
    # catches a changed physical meaning; constant_unit catches a non-SI unit;
    # labels catch a forbidden locator key; status catches a premature claim.
    text = document()
    cells = ["`" + value + "`" for value in row]
    cells[2] = row[2]
    original = "| " + " | ".join(cells) + " |"
    changed = list(cells)
    changed[field] = {0: "`helianthus_native_unreviewed`", 1: "`counter`",
                      2: "unreviewed quantity", 3: "`celsius`",
                      4: "`address, device, point, protocol, unit`", 5: "`Proven`"}[field]
    assert text.count(original) == 1
    with pytest.raises(CHECKER.CheckError, match="native"):
        CHECKER.validate(text.replace(original, "| " + " | ".join(changed) + " |"))


@pytest.mark.parametrize("replacement", [
    NATIVE_ROW_TEXT + "\n" + NATIVE_ROW_TEXT.replace("`kelvin`", "`celsius`"),
    NATIVE_ROW_TEXT + "\n" + NATIVE_ROW_TEXT.replace("`kelvin`", "`pascals`"),
    NATIVE_ROW_TEXT.replace("`kelvin`", "`kelvin, celsius`"),
    NATIVE_ROW_TEXT + "\n" + NATIVE_ROW_TEXT,
], ids=["second_unit_row", "second_si_unit_row", "two_units_in_cell", "duplicate_row"])
def test_native_family_rejects_second_unit(replacement):
    text = document()
    assert text.count(NATIVE_ROW_TEXT) == 1
    with pytest.raises(CHECKER.CheckError, match="native"):
        CHECKER.validate(text.replace(NATIVE_ROW_TEXT, replacement))


@pytest.mark.parametrize("key", ["address", "serial", "slot", "model", "fact_id"])
def test_native_family_rejects_forbidden_label_key(key):
    text = document()
    changed = NATIVE_ROW_TEXT.replace(NATIVE_LABELS, "`protocol, device, index, " + key + ", point, unit`")
    with pytest.raises(CHECKER.CheckError, match="forbidden native label key"):
        CHECKER.validate(text.replace(NATIVE_ROW_TEXT, changed))


@pytest.mark.parametrize(("old", "new", "message"), [
    ("`helianthus_native_temperature` | `gauge` | temperature |", "`helianthus_native_temperature_kelvin` | `gauge` | temperature |", "native family name"),
    ("`helianthus_native_temperature` | `gauge` | temperature |", "`native_temperature` | `gauge` | temperature |", "native family name"),
    ("`helianthus_native_temperature` | `gauge` | temperature |", "`helianthus_native_Temperature` | `gauge` | temperature |", "native family name"),
    ("`helianthus_native_count` | `gauge` | count |", "`helianthus_native_count_total` | `gauge` | count |", "native family name"),
    ("`helianthus_native_temperature` | `gauge` | temperature |", "`helianthus_semantic_render_overflow` | `gauge` | temperature |", "native family name"),
    ("| `helianthus_native_render_overflow` | `gauge` | value series omitted in the scrape | `none` | `none` |",
     "| `helianthus_native_render_overflow` | `gauge` | value series omitted in the scrape | `none` | `protocol` |",
     "native"),
    ("| `helianthus_native_render_overflow` | `gauge` | value series omitted in the scrape | `none` | `none` |",
     "| `helianthus_native_render_overflow` | `gauge` | value series omitted in the scrape | `none` | `unit` |",
     "native"),
    ("| `helianthus_native_power` | `gauge` | power | `watts` | `protocol, device, index, point, unit, driver_instance` | `emitted` |\n",
     "", "native families"),
    ("| `protocol` | `ebus, modbus, eebus, can` |", "| `protocol` | `ebus, modbus, eebus, unsupported` |", "native label"),
    ("| `device` | `documented_device_class` |", "| `device` | `device_address` |", "native label"),
    ("| `index` | `documented_instance_index` |\n", "", "native label"),
    ("| `unit` | `family_constant_unit` |",
     "| `unit` | `family_constant_unit` |\n| `address` | `documented_device_class` |", "native label"),
    ("### Native labels\n", "### Native label domains\n", "heading"),
    ("## Native point coverage\n", "## Native points\n", "native"),
])
def test_native_section_rejects_drift(old, new, message):
    text = document()
    assert text.count(old) == 1
    with pytest.raises(CHECKER.CheckError, match=message):
        CHECKER.validate(text.replace(old, new))


def test_native_section_requires_lifetime_rules():
    phrase = "A label set belongs to one native identity for the\nlifetime of the scrape target"
    text = document()
    assert " ".join(phrase.split()) in " ".join(text.split())
    with pytest.raises(CHECKER.CheckError, match="lifetime rules"):
        CHECKER.validate(_without_phrase(text, phrase))


def test_native_section_rejects_old_admission_set_sentence():
    text = document()
    native = text.split("## Native point coverage\n", 1)[1]
    assert "1,024 value series" not in native
    CHECKER.validate(text)
    injected = text.replace(
        "## Native point coverage\n",
        "## Native point coverage\n\nThe gateway keeps a lifetime admission set of "
        "value series, each keyed by its family name together with its label set.\n",
        1,
    )
    with pytest.raises(CHECKER.CheckError, match="admission-set"):
        CHECKER.validate(injected)


def test_native_membership_rejects_a_dropped_or_changed_tuple():
    emitted = {row[0]: row for row in CHECKER.rows(
        "\n".join("| " + line for line in CHECKER.RENDERER_ROWS.strip().splitlines()))}
    dropped = dict(emitted)
    dropped.pop("helianthus_native_temperature")
    with pytest.raises(CHECKER.CheckError, match="not a member of the emitted table"):
        CHECKER._validate_native_points(document(), dropped)
    changed = dict(emitted)
    name, kind, labels, unit = changed["helianthus_native_temperature"]
    changed[name] = (name, kind, labels, "celsius")
    with pytest.raises(CHECKER.CheckError, match="tuple differs"):
        CHECKER._validate_native_points(document(), changed)


def test_native_family_rejects_dropped_driver_instance_and_fabricated_index():
    text = document()
    dropped = NATIVE_ROW_TEXT.replace(
        NATIVE_LABELS, "`protocol, device, index, point, unit`")
    with pytest.raises(CHECKER.CheckError, match="driver_instance"):
        CHECKER.validate(text.replace(NATIVE_ROW_TEXT, dropped))
    rule = ("A row without\n"
            "  a documented instance index has no `index` label.")
    fabricated = "A row without a documented instance index carries `index` `0`."
    assert text.count(rule) == 1
    with pytest.raises(CHECKER.CheckError, match="index rule"):
        CHECKER.validate(text.replace(rule, fabricated))


@pytest.mark.parametrize("replacement", [
    "Each family has exactly one constant `unit` label value, and it is SI.",
    "Each value family and the age family has exactly one constant `unit` label\n"
    "value, and it is SI. Every native family carries the `unit` label.",
], ids=["unqualified_every_family", "overflow_exemption_missing"])
def test_native_unit_rule_exempts_overflow_family(replacement):
    # The overflow row has no labels and no unit, so a sentence requiring a
    # unit label on every native family contradicts its row.
    text = document()
    scoped = ("Each value family and the age family has exactly one constant `unit` label\n"
              "value, and it is SI. `helianthus_native_render_overflow` has no labels and no\n"
              "unit.")
    assert text.count(scoped) == 1
    with pytest.raises(CHECKER.CheckError, match="native unit rule"):
        CHECKER.validate(text.replace(scoped, replacement))


def _without_phrase(text, phrase):
    words = phrase.split()
    pattern = r"\s+".join(re.escape(word) for word in words)
    result, count = re.subn(pattern, "removed", text, count=1)
    assert count == 1
    return result


def test_native_section_accepts_row_order_and_spacing():
    text = document()
    lines = [line for line in text.splitlines(keepends=True)
             if line.startswith("| `helianthus_native_") and line.count("|") >= 7]
    assert len(lines) == 15
    text = text.replace("".join(lines), "".join(reversed(lines)).replace("| `helianthus_native_", "|  `helianthus_native_"))
    CHECKER.validate(text)
