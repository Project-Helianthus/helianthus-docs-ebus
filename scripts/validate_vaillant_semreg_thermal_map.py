#!/usr/bin/env python3
"""Validate the typed Vaillant B524-to-SemReg thermal mapping index.

Each row is keyed by the native identity of its value, names the native
resource it attaches to, its relation candidates in the structural candidates
fixture or their explicit absence, and the element inventory disposition of
its target definition. The hot-water fixture is checked with the same rules.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import sys


INDEX = Path("architecture/fixtures/vaillant-semreg-thermal-map-v1.json")
DHW = Path("architecture/fixtures/dhw-setpoint-semreg-cutover-v1.json")
STRUCTURAL = Path("architecture/fixtures/structural-relation-candidates-v1.json")
QUALIFICATION = Path("architecture/fixtures/vaillant-controller-qualification-v1.json")
PACK = {"id": "helianthus.pack.thermal", "version": "1.0.0"}
KEY_FIELDS = (("PB", "pb"), ("SB", "sb"), ("OP", "operation"), ("GG", "group"), ("II", "instance"), ("RR", "register"))
SYSTEM_GROUP = "OP=0x02 GG=0x00 II=0x00"
HOT_WATER_GROUP = "OP=0x02 GG=0x01 II=0x00"
UNRESOLVED_SUBJECT = "catalog.reason.subject_unresolved"


def unresolved_fact(fact: str) -> dict[str, object]:
    """The element inventory entry of a thermal fact whose subject is unresolved."""
    return {
        "definition": {"pack": dict(PACK), "id": fact, "version": "1.0.0"},
        "element_kind": "fact",
        "disposition": "unknown",
        "planes": [],
        "reason": UNRESOLVED_SUBJECT,
    }


# native key: (gateway field, register, native resource, native kind, target, projection disposition, loss)
EXPECTED_ROWS = {
    "PB=0xB5 SB=0x24 OP=0x02 GG=0x00 II=0x00 RR=0x0073": (
        "state.outdoor_temperature", "0x0073", SYSTEM_GROUP, "b524_semantic_root",
        "thermal.measurement.air_temperature", "exact", None,
    ),
    "PB=0xB5 SB=0x24 OP=0x02 GG=0x00 II=0x00 RR=0x004B": (
        "state.flow_temperature", "0x004B", SYSTEM_GROUP, "b524_semantic_root",
        "thermal.measurement.water_temperature", "exact", None,
    ),
    "PB=0xB5 SB=0x24 OP=0x02 GG=0x00 II=0x00 RR=0x0095": (
        "state.outdoor_temperature_avg24h", "0x0095", SYSTEM_GROUP, "b524_semantic_root",
        None, "withheld", "rolling_average_window_unrepresentable",
    ),
}
ROW_KEYS = {
    "native_key", "legacy_system_field", "native_selector", "native_value", "native_resource",
    "relation_candidates", "target", "semreg_fact", "disposition", "loss",
}
TARGET_KEYS = {"definition", "element_kind", "disposition", "planes", "reason"}
RESOURCE_KEYS = {"selector", "kind"}
CANDIDATE_KEYS = {"refs", "absence"}
DHW_FACT = "thermal.setpoint.dhw_temperature_setpoint"
DHW_KEY = "PB=0xB5 SB=0x24 OP=0x02 GG=0x01 II=0x00 RR=0x0004"
DHW_TOP_KEYS = {
    "evidence_status", "scope", "relation_candidates_fixture", "native_resources", "rows",
    "projection_cases", "target_domain",
}
DHW_TARGET_DOMAIN = {
    "grade": "Hypothesis",
    "documented_range_celsius": {"minimum": 35, "maximum": 70},
    "precedence": (
        "The B524 description-record MIN and MAX apply where that query exists and the device answers. "
        "Where the query exists and the device returns no reply or no result, the limits stay unknown "
        "and the documented range is not substituted. The documented range applies only where no query exists."
    ),
}
DHW_ROW_KEYS = {
    "native_key", "native_value", "native_resource", "relation_candidates", "target", "subject",
}
DHW_SOURCES = ["alpha", "beta"]
REQUIRED_NONCLAIMS = {
    "topology_established",
    "full_portal_descriptor_established", "prometheus_output_established",
    "eebus_output_established", "matter_output_established",
    "hardware_qualification_established",
}
NATIVE_TEMPERATURE = {"wire_type": "f32_le", "unit": "degC"}
MAPPED_TEMPERATURE = {
    "wire_type": "f32_le",
    "unit": "degC",
    "si_unit": "kelvin",
    "conversion": "degrees Celsius plus 273.15",
}
TEMPERATURE_SI = ("SI unit kelvin", "degrees Celsius plus 273.15")
HUMIDITY_SI = ("SI unit a ratio", "percent divided by 100")
# Wire unit on the humidity rows. It is not the SemReg quantity id `unit.percent`.
HUMIDITY_NATIVE = "percent (`%`)"
HUMIDITY_SEMANTIC = "`unit.percent`"
# A hand-off table row with no mapped quantity keeps its native unit only. Any
# SI-unit or conversion wording fails, not only the canonical phrases. A bare K
# stays allowed: it is the native candidate unit of a temperature difference.
# Every SemReg unit id fails too (`unit.celsius`, `unit.percent`, `unit.one`,
# and any other `unit.<id>`).
UNMAPPED_CONVERSIONS = tuple(re.compile(pattern) for pattern in (
    r"(?i)kelvin",
    r"(?i)\bratio\b",
    r"(?i)\bfraction\b",
    r"\b273(?:\.15)?\b",
    r"(?i)divided by 100",
    r"\bSI\b",
    r"(?i)\bconver(?:t|ts|ted|ting|sion)\b",
    r"(?i)\bunit\.[a-z][a-z0-9_]*\b",
))
# The semantic-snapshot example table shares its hand-off table with four
# non-thermal rows. Each already states that pack's own unit id. That one id
# stays; unit.celsius and any second id still fail. A withheld thermal row
# matches none of these packs, so it may name no SemReg unit id at all.
SNAPSHOT_PACK_UNITS = (
    ("api/semantic-snapshot-read.md", "helianthus.pack.pv", "unit.watt"),
    ("api/semantic-snapshot-read.md", "helianthus.pack.storage", "unit.percent"),
    ("api/semantic-snapshot-read.md", "helianthus.pack.evse", "unit.watt"),
    ("api/semantic-snapshot-read.md", "helianthus.pack.infrastructure", "unit.volt"),
)
# path, mapped-row marker, native-unit spelling, SemReg unit identifier, SI-unit
# statement, conversion statement. The marker matches one mapped row; every
# statement that is not None must sit on that row. The native-unit spelling is
# the unit of the native evidence on the row (`degC`, `°C`, wire percent), never
# a SemReg identifier, so dropping the native unit fails even when the SemReg
# identifier stays. It is None only on a row that states the SemReg target alone
# and carries no native evidence.
CELSIUS_NATIVE = "°C"
CELSIUS_SEMANTIC = "unit.celsius"
PAGE_RULES = (
    ("architecture/b524-semantic-mapping.md",
     "`PB=0xB5 SB=0x24 OP=0x02 GG=0x00 II=0x00 RR=0x0073`", "degC", None, *TEMPERATURE_SI),
    ("architecture/b524-semantic-mapping.md",
     "`PB=0xB5 SB=0x24 OP=0x02 GG=0x00 II=0x00 RR=0x004B`", "degC", None, *TEMPERATURE_SI),
    ("architecture/boiler-temperature-semreg-mapping.md",
     "| Flow: `FlowTemperatureC`", CELSIUS_NATIVE, CELSIUS_SEMANTIC, *TEMPERATURE_SI),
    ("architecture/circuit-temperature-cutover.md",
     "| `0x0008` |", CELSIUS_NATIVE, CELSIUS_SEMANTIC, *TEMPERATURE_SI),
    ("architecture/cylinder-temperature-cutover.md",
     "| `0x0004` |", CELSIUS_NATIVE, CELSIUS_SEMANTIC, *TEMPERATURE_SI),
    ("architecture/dhw-measured-temperature-cutover.md",
     "| `(0x02, 0x01, 0x00, 0x0005)` |", CELSIUS_NATIVE, CELSIUS_SEMANTIC, *TEMPERATURE_SI),
    ("architecture/dhw-measured-temperature-cutover.md",
     "| Quantity unit and dimension |", None, CELSIUS_SEMANTIC, *TEMPERATURE_SI),
    ("architecture/dhw-setpoint-semreg-cutover.md",
     "| Controller requested DHW target |", CELSIUS_NATIVE, CELSIUS_SEMANTIC, *TEMPERATURE_SI),
    ("architecture/humidity-semreg-cutover.md",
     "| Controller-zone measurement |", HUMIDITY_NATIVE, HUMIDITY_SEMANTIC, *HUMIDITY_SI),
    ("architecture/humidity-semreg-cutover.md",
     "| Remote-room measurement |", HUMIDITY_NATIVE, HUMIDITY_SEMANTIC, *HUMIDITY_SI),
    ("architecture/humidity-semreg-cutover.md",
     "| Circuit measurement |", HUMIDITY_NATIVE, HUMIDITY_SEMANTIC, *HUMIDITY_SI),
    ("architecture/outdoor-temperature-semreg-cutover.md",
     "| Instantaneous `state.outdoor_temperature` |", "degC", None, *TEMPERATURE_SI),
    ("architecture/solar-loop-temperature-cutover.md",
     "T defines `thermal.measurement.water_temperature` with", None, CELSIUS_SEMANTIC, *TEMPERATURE_SI),
    ("architecture/zone-room-temperature-cutover.md",
     "| Current room temperature |", CELSIUS_NATIVE, CELSIUS_SEMANTIC, *TEMPERATURE_SI),
    ("architecture/zone-room-temperature-cutover.md",
     "| `helianthus.pack.thermal` / `thermal.measurement.air_temperature` /",
     None, CELSIUS_SEMANTIC, *TEMPERATURE_SI),
    ("architecture/zone-setpoint-semreg-cutover.md",
     "| Heating manual |", CELSIUS_NATIVE, CELSIUS_SEMANTIC, *TEMPERATURE_SI),
    ("architecture/zone-setpoint-semreg-cutover.md",
     "| Heating computed effective |", CELSIUS_NATIVE, CELSIUS_SEMANTIC, *TEMPERATURE_SI),
    ("api/semantic-snapshot-read.md",
     "| Thermal/HVAC / `helianthus.pack.thermal` |", None, CELSIUS_SEMANTIC, *TEMPERATURE_SI),
)
# A hand-off table is a table that holds a mapped row. A page that states its
# mapped quantity in prose names, by header, the table that holds its withheld rows.
WITHHELD_TABLE_HEADERS = (
    ("architecture/solar-loop-temperature-cutover.md",
     "| Observation | Native selector (OP/GG/II/RR) |"),
)


class CheckError(ValueError):
    """The typed public thermal mapping index is invalid."""


def require(value: object, expected: object, label: str) -> None:
    if value != expected:
        raise CheckError(f"{label}: expected {expected!r}, got {value!r}")


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def qualification_rules():
    path = Path(__file__).resolve().parent / "validate_vaillant_controller_qualification.py"
    spec = importlib.util.spec_from_file_location("vaillant_controller_qualification_rules", path)
    if spec is None or spec.loader is None:
        raise CheckError("controller qualification module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_boiler_publication(target_class: str, qualified_binding_required: bool) -> None:
    """A routed boiler flow row publishes with no binding gate. A heat pump does not."""
    if target_class == "boiler":
        if qualified_binding_required:
            raise CheckError("boiler flow row qualified_binding_required stays false")
        return
    if target_class == "heat_pump":
        raise CheckError("the same selector on a heat-pump target is not a boiler publication")
    raise CheckError("not a declared boiler target")


def selector_parts(selector: object, label: str) -> dict[str, str]:
    if not isinstance(selector, str) or not selector:
        raise CheckError(f"{label}: a native selector is a non-empty string, never an ordinal")
    parts: dict[str, str] = {}
    for part in selector.split(" "):
        pair = part.split("=")
        if len(pair) != 2 or not pair[0] or not pair[1] or pair[0] in parts:
            raise CheckError(f"{label}: {selector!r} is not a native selector")
        parts[pair[0]] = pair[1]
    return parts


Endpoint = tuple[str, str | None]


def endpoint(end: dict[str, object]) -> Endpoint:
    """A candidate endpoint: its native kind and its native position, when it has one."""
    positions = [
        item["selector"] for item in end.get("identity_evidence", [])
        if isinstance(item, dict) and item.get("classification") == "native_position"
    ]
    return end["kind"], (" ".join(positions) if positions else None)  # type: ignore[return-value]


def endpoint_kinds(structural: object) -> dict[str, set[Endpoint]]:
    """Map each structural candidate id to the native endpoints it names."""
    if not isinstance(structural, dict):
        raise CheckError("structural candidates fixture must be an object")
    ends: dict[str, set[Endpoint]] = {}
    for row in structural.get("attachments", []):
        ends[row["id"]] = {endpoint(row["from"]), endpoint(row["to"])}
    for row in structural.get("relayed_identity", []):
        ends[row["id"]] = {endpoint(row[name]) for name in ("relaying_end", "slot_view", "direct_view")}
    return ends


def listed_for(end: Endpoint, resources: dict[str, str]) -> set[str]:
    kind, position = end
    return {
        selector for selector, listed in resources.items()
        if listed == kind and (position is None or selector == position)
    }


def native_resources(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, list) or not value:
        raise CheckError(f"{label}: native_resources must be a non-empty list")
    resources: dict[str, str] = {}
    for resource in value:
        if not isinstance(resource, dict) or set(resource) != RESOURCE_KEYS:
            raise CheckError(f"{label}: a native resource has exactly a selector and a kind")
        selector = resource["selector"]
        selector_parts(selector, f"{label}: native resource")
        if selector in resources:
            raise CheckError(f"{label}: native resource {selector!r} is listed twice")
        if not isinstance(resource["kind"], str) or not resource["kind"]:
            raise CheckError(f"{label}: native resource {selector!r} needs a kind")
        resources[selector] = resource["kind"]
    return resources


def check_native_value(value: object, *, mapped: bool, label: str) -> None:
    """A mapped row keeps the native unit and states the SI unit and the conversion."""
    expected = MAPPED_TEMPERATURE if mapped else NATIVE_TEMPERATURE
    if not isinstance(value, dict):
        raise CheckError(f"{label}: native value must be an object")
    require(value.get("wire_type"), "f32_le", f"{label}: wire_type")
    require(value.get("unit"), "degC", f"{label}: native unit")
    if not mapped:
        require(set(value), set(NATIVE_TEMPERATURE), f"{label}: unmapped native value")
        return
    if "si_unit" not in value:
        raise CheckError(f"{label}: mapped row lacks the SI unit")
    if "conversion" not in value:
        raise CheckError(f"{label}: mapped row lacks the conversion")
    require(value.get("si_unit"), "kelvin", f"{label}: SI unit")
    require(value.get("conversion"), MAPPED_TEMPERATURE["conversion"], f"{label}: conversion")
    require(set(value), set(expected), f"{label}: native value")


def mapped_row(path: str, text: str, marker: str) -> str:
    """The one mapped row the marker names."""
    rows = [line for line in text.splitlines() if marker in line]
    if len(rows) != 1:
        raise CheckError(f"{path}: mapped row {marker!r} appears {len(rows)} times")
    return rows[0]


def check_humidity_separation(path: str, row: str) -> None:
    """Wire percent, then the SemReg target `unit.percent`, then the ratio conversion."""
    native_at = row.find(HUMIDITY_NATIVE)
    semantic_at = row.find(HUMIDITY_SEMANTIC)
    si_at = row.find(HUMIDITY_SI[0])
    if semantic_at < 0 or not (native_at < semantic_at < si_at):
        raise CheckError(
            f"{path}: humidity row must state native percent, then the semantic target, then the conversion"
        )


def check_handoff_page(
    path: str, text: str, marker: str, native: str | None, semantic: str | None,
    si_unit: str, conversion: str,
) -> None:
    """The native unit, the SemReg unit, the SI unit and the conversion sit on that mapped row."""
    if native is not None and "unit." in native:
        raise CheckError(f"{path}: native unit {native!r} is a SemReg identifier, not native evidence")
    if native is None and semantic is None:
        raise CheckError(f"{path}: mapped row names neither a native unit nor a SemReg unit")
    row = mapped_row(path, text, marker)
    if native is not None and native not in row:
        raise CheckError(f"{path}: mapped row lacks the native unit")
    if semantic is not None and semantic not in row:
        raise CheckError(f"{path}: mapped row lacks the SemReg unit")
    if si_unit not in row:
        raise CheckError(f"{path}: mapped row lacks the SI unit")
    if conversion not in row:
        raise CheckError(f"{path}: mapped row lacks the conversion")
    if native == HUMIDITY_NATIVE:
        check_humidity_separation(path, row)


def is_table_separator(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return False
    return stripped.replace("|", "").replace(":", "").replace("-", "").strip() == ""


def page_tables(text: str) -> list[list[str]]:
    """Each run of consecutive pipe-prefixed lines on the page."""
    tables: list[list[str]] = []
    current: list[str] | None = None
    for line in text.splitlines():
        if line.strip().startswith("|"):
            if current is None:
                current = []
                tables.append(current)
            current.append(line)
        else:
            current = None
    return tables


def handoff_tables(path: str, text: str) -> list[list[str]]:
    """The tables that hold a mapped row, and the withheld-row tables the page names."""
    markers = tuple(marker for rule_path, marker, *_rest in PAGE_RULES if rule_path == path)
    headers = tuple(header for rule_path, header in WITHHELD_TABLE_HEADERS if rule_path == path)
    tables = page_tables(text)
    for header in headers:
        count = sum(1 for table in tables if table[0].strip().startswith(header))
        if count != 1:
            raise CheckError(f"{path}: withheld-row table {header!r} appears {count} times")
    return [
        table for table in tables
        if any(marker in line for line in table for marker in markers)
        or any(table[0].strip().startswith(header) for header in headers)
    ]


def unmapped_handoff_rows(path: str, text: str) -> list[str]:
    """Every body row of a hand-off table that does not carry a mapped quantity."""
    markers = tuple(marker for rule_path, marker, *_rest in PAGE_RULES if rule_path == path)
    rows: list[str] = []
    for table in handoff_tables(path, text):
        body = table[2:] if len(table) > 1 and is_table_separator(table[1]) else table
        for line in body:
            if is_table_separator(line) or any(marker in line for marker in markers):
                continue
            rows.append(line)
    return rows


def without_stated_pack_unit(path: str, line: str) -> str:
    """Drop the one pack unit id a non-thermal snapshot example already states.

    Removing that single id leaves `unit.celsius`, `unit.percent` on any other
    row, and a second id on the example row, for the SemReg-unit check to reject.
    """
    stated = [
        unit for page, pack, unit in SNAPSHOT_PACK_UNITS
        if page == path and re.search(rf"\b{re.escape(pack)}\b", line)
    ]
    if len(stated) != 1:
        return line
    return re.sub(rf"(?i)\b{re.escape(stated[0])}\b", "", line, count=1)


def check_unmapped_line(path: str, line: str) -> None:
    checked = without_stated_pack_unit(path, line)
    for banned in UNMAPPED_CONVERSIONS:
        if banned.search(checked):
            raise CheckError(f"{path}: a row with no mapped quantity states a conversion")


def handoff_text(pages: dict[str, str] | None, path: str) -> str:
    if pages is None:
        if path == "api/semantic-snapshot-read.md":
            raw = os.environ.get("PLATFORM_DOCS_ROOT")
            docs = Path(raw) if raw else None
            if docs is None:
                candidate = Path(__file__).resolve().parents[1] / "checkouts" / "docs"
                if candidate.is_dir():
                    docs = candidate
            if docs is None:
                raise CheckError("PLATFORM_DOCS_ROOT is required")
            return (docs / path).read_text(encoding="utf-8")
        return Path(path).read_text(encoding="utf-8")
    text = pages.get(path)
    if not isinstance(text, str):
        raise CheckError(f"{path}: hand-off page is missing")
    return text


def check_handoff_pages(pages: dict[str, str] | None = None) -> None:
    seen: dict[str, str] = {}
    for path, marker, native, semantic, si_unit, conversion in PAGE_RULES:
        if path not in seen:
            seen[path] = handoff_text(pages, path)
        check_handoff_page(path, seen[path], marker, native, semantic, si_unit, conversion)
    for path, text in seen.items():
        for line in unmapped_handoff_rows(path, text):
            check_unmapped_line(path, line)


def check_native_key(row: dict[str, object], selector: dict[str, object], label: str) -> str:
    key = row.get("native_key")
    expected = " ".join(f"{name}={selector.get(field)}" for name, field in KEY_FIELDS)
    require(key, expected, f"{label}: native_key")
    return expected


def check_attachment(
    row: dict[str, object], key: str, resources: dict[str, str], expected: tuple[str, str],
    candidates: dict[str, set[Endpoint]], label: str,
) -> set[str]:
    """Check the native resource and relation candidates; return the selectors the row uses."""
    resource = row.get("native_resource")
    parts = selector_parts(resource, f"{label}: native_resource")
    if resource not in resources:
        raise CheckError(f"{label}: native_resource {resource!r} is not a listed native resource")
    key_parts = selector_parts(key, f"{label}: native_key")
    if any(parts.get(name) != key_parts.get(name) for name in ("OP", "GG", "II")):
        raise CheckError(f"{label}: false join; {resource!r} does not hold {key!r}")
    require((resource, resources[resource]), expected, f"{label}: native resource")
    return check_relation_candidates(row.get("relation_candidates"), resource, resources, candidates, label)


def check_relation_candidates(
    relation: object, own: str, resources: dict[str, str], candidates: dict[str, set[Endpoint]], label: str,
) -> set[str]:
    if not isinstance(relation, dict) or set(relation) != CANDIDATE_KEYS:
        raise CheckError(f"{label}: relation_candidates has exactly refs and absence")
    refs, absence = relation["refs"], relation["absence"]
    if not isinstance(refs, list):
        raise CheckError(f"{label}: relation candidate refs must be a list")
    if refs and absence is not None:
        raise CheckError(f"{label}: relation candidates are either referenced or absent, not both")
    if not refs and (not isinstance(absence, str) or not absence.strip()):
        raise CheckError(f"{label}: an absent relation candidate needs its reason")
    used = {own}
    for ref in refs:
        if not isinstance(ref, str) or ref not in candidates:
            raise CheckError(f"{label}: relation candidate {ref!r} is not in the structural candidates fixture")
        dangling = sorted(str(end) for end in candidates[ref] if not listed_for(end, resources))
        if dangling:
            raise CheckError(f"{label}: dangling endpoint; {ref} names {dangling} that no listed native resource is")
        if not any(own in listed_for(end, resources) for end in candidates[ref]):
            raise CheckError(f"{label}: relation candidate {ref} does not end at the row's native resource")
        for end in candidates[ref]:
            used |= listed_for(end, resources)
    return used


def check_target(target: object, fact: str | None, label: str) -> None:
    if fact is None:
        require(target, None, f"{label}: target")
        return
    if not isinstance(target, dict) or set(target) != TARGET_KEYS:
        raise CheckError(f"{label}: target has exactly {sorted(TARGET_KEYS)}")
    require(target, unresolved_fact(fact), f"{label}: target copied from the element inventory")


def check_unused_resources(resources: dict[str, str], used: set[str], label: str) -> None:
    unused = sorted(selector for selector in resources if selector not in used)
    if unused:
        raise CheckError(f"{label}: native resources {unused} attach no row and end no referenced candidate")


def validate_row(
    row: object, resources: dict[str, str], candidates: dict[str, set[Endpoint]],
) -> tuple[str, set[str]]:
    if not isinstance(row, dict) or set(row) != ROW_KEYS:
        raise CheckError(f"mapping row members must be exactly {sorted(ROW_KEYS)}")
    selector = row["native_selector"]
    if not isinstance(selector, dict):
        raise CheckError("native_selector must be an object")
    key = check_native_key(row, selector, "mapping row")
    if key not in EXPECTED_ROWS:
        raise CheckError(f"{key}: not a row of the closed three-row contract")
    legacy, _register, resource, kind, fact, disposition, loss = EXPECTED_ROWS[key]
    check_native_value(row["native_value"], mapped=fact is not None, label=key)
    require(row["legacy_system_field"], legacy, f"{key}: legacy_system_field")
    used = check_attachment(row, key, resources, (resource, kind), candidates, key)
    check_target(row["target"], fact, key)
    require(row["semreg_fact"], fact, f"{key}: semreg_fact")
    require(row["disposition"], disposition, f"{key}: disposition")
    require(row["loss"], loss, f"{key}: loss")
    return key, used


def check_sidecar(qualification: dict[str, object], keys: list[str]) -> None:
    bound = qualification.get("thermal_rows")
    if not isinstance(bound, list) or any(not isinstance(item, str) for item in bound):
        raise CheckError("qualification sidecar binds to rows by native key, never by ordinal")
    require(bound, keys, "qualification sidecar thermal_rows")


def _validate_index_contract(index: dict[str, object], qualification: dict[str, object]) -> None:
    require(index.get("schema_version"), 1, "schema_version")
    require(index.get("contract_id"), "helianthus.docs.ebus.b524-semreg-thermal/v1", "contract_id")
    require(index.get("scope"), "read_only_candidate_mapping", "scope")
    require(index.get("pack"), PACK, "pack")
    require(index.get("relation_candidates_fixture"), str(STRUCTURAL), "relation_candidates_fixture")

    rules = qualification_rules()
    applicability = index.get("applicability")
    if not isinstance(applicability, dict):
        raise CheckError("applicability must be an object")
    require(applicability, rules.GENERALIZES, "applicability")
    require(index.get("qualification"), {
        "contract_id": "helianthus.docs.ebus.vaillant-controller-qualification/v1",
        "revision": "vaillant-controller-qualification-evidence-gap/v1",
        "fixture": "architecture/fixtures/vaillant-controller-qualification-v1.json",
        "level": "declared",
        "qualified_binding_required": True,
        "runtime_qualification_permitted": True,
        "hardware_test_record": None,
    }, "qualification")
    require(index.get("write_routes"), rules.WRITE_ROUTES, "write_routes")
    require(index.get("boiler_target"), rules.BOILER_TARGET, "boiler_target")
    flow = index["boiler_target"]["flow_row"]
    check_boiler_publication("boiler", bool(flow["qualified_binding_required"]))


def _validate_index_mappings(
    index: dict[str, object], structural: object, qualification: dict[str, object],
) -> None:
    rules = qualification_rules()
    resources = native_resources(index.get("native_resources"), "thermal map")
    candidates = endpoint_kinds(structural)
    mappings = index.get("mappings")
    if not isinstance(mappings, list) or len(mappings) != 3:
        raise CheckError("mappings must contain exactly three rows")
    keys: list[str] = []
    used: set[str] = set()
    for row in mappings:
        key, kinds = validate_row(row, resources, candidates)
        if key in keys:
            raise CheckError(f"{key}: rows need unique native keys")
        keys.append(key)
        used |= kinds
        require(row["native_selector"], {
            "pb": "0xB5", "sb": "0x24", "operation": "0x02", "group": "0x00",
            "instance": "0x00", "register": EXPECTED_ROWS[key][1],
            "destination": "0x15",
            "controller_family": rules.controller_family("0x00", EXPECTED_ROWS[key][1]),
            "request_direction": "initiator_to_target", "value_direction": "target_to_initiator",
        }, f"{key}: native_selector")
    check_unused_resources(resources, used, "thermal map")
    check_sidecar(qualification, keys)


def _validate_index_boundaries(index: dict[str, object]) -> None:
    nonclaims = index.get("nonclaims")
    if not isinstance(nonclaims, dict) or set(nonclaims) != REQUIRED_NONCLAIMS:
        raise CheckError("nonclaims must contain the closed public-boundary inventory")
    for name, claim in nonclaims.items():
        if name == "hardware_qualification_established":
            if not isinstance(claim, bool):
                raise CheckError("hardware_qualification_established records whether a public test record exists")
            continue
        if claim is not False:
            raise CheckError("nonclaim drifted")
    require(index.get("native_distinctions"), {
        "op06_gg00_rr0015_substitutable_for_system_flow": False,
        "b509_substitutable_for_b524_rows": False,
    }, "native_distinctions")
    require(index.get("lifecycle"), {
        "retained_native_observation": {
            "received_at": {"unix_nanoseconds": "1720000000000000000", "clock_id": "clock.utc", "uncertainty_ns": "1000000"},
            "receipt_monotonic": {"clock_epoch_id": "clock-epoch:gateway-1", "nanoseconds": "1000000000"},
        },
        "caller_evaluation_context": {
            "evaluated_at": {"unix_nanoseconds": "1720000005000000000", "clock_id": "clock.utc", "uncertainty_ns": "1000000"},
            "evaluate_monotonic": {"clock_epoch_id": "clock-epoch:gateway-1", "nanoseconds": "6000000000"},
        },
        "evaluation_cannot_overwrite_receipt": True,
        "freshness_axis": "elapsed_monotonic",
    }, "lifecycle")


def validate_index(index: object, *, structural: object = None, qualification: object = None) -> None:
    if structural is None:
        structural = load(STRUCTURAL)
    if qualification is None:
        qualification = load(QUALIFICATION)
    if not isinstance(index, dict):
        raise CheckError("index must be an object")
    if not isinstance(qualification, dict):
        raise CheckError("qualification sidecar must be an object")
    _validate_index_contract(index, qualification)
    _validate_index_mappings(index, structural, qualification)
    _validate_index_boundaries(index)


def validate_dhw(data: object, *, structural: object = None) -> None:
    if structural is None:
        structural = load(STRUCTURAL)
    if not isinstance(data, dict) or set(data) != DHW_TOP_KEYS:
        raise CheckError(f"hot-water fixture members must be exactly {sorted(DHW_TOP_KEYS)}")
    require(data.get("target_domain"), DHW_TARGET_DOMAIN, "hot water: target_domain")
    require(data["evidence_status"], "Hypothesis", "hot water: evidence_status")
    require(data["scope"], "synthetic_read_projection_contract", "hot water: scope")
    require(data["relation_candidates_fixture"], str(STRUCTURAL), "hot water: relation_candidates_fixture")
    resources = native_resources(data["native_resources"], "hot water")
    rows = data["rows"]
    if not isinstance(rows, list) or len(rows) != 1:
        raise CheckError("hot water: exactly one native row")
    row = rows[0]
    if not isinstance(row, dict) or set(row) != DHW_ROW_KEYS:
        raise CheckError(f"hot water: row members must be exactly {sorted(DHW_ROW_KEYS)}")
    key = row["native_key"]
    require(key, DHW_KEY, "hot water: native_key")
    check_native_value(row["native_value"], mapped=True, label="hot water")
    used = check_attachment(
        row, key, resources, (HOT_WATER_GROUP, "dhw_instance"), endpoint_kinds(structural), "hot water",
    )
    check_unused_resources(resources, used, "hot water")
    check_target(row["target"], DHW_FACT, "hot water")
    require(row["subject"], {"status": "unresolved", "sources": DHW_SOURCES}, "hot water: unresolved subject")

    cases = data["projection_cases"]
    if not isinstance(cases, list):
        raise CheckError("hot water: projection_cases must be a list")
    require([case.get("case") if isinstance(case, dict) else None for case in cases],
            ["two_services", "partial_absence"], "hot water: projection cases")
    for case, absent in zip(cases, ([], ["beta"]), strict=True):
        require(case, {
            "case": case["case"],
            "requested": [{"kind": "fact", "item_id": DHW_FACT}],
            "dispositions": [{
                "kind": "fact", "item_id": DHW_FACT, "outcome": "withheld",
                "source_keys": [], "loss": [], "reason": UNRESOLVED_SUBJECT,
            }],
            "absent_sources": absent,
        }, f"hot water: {case['case']}")


def main() -> int:
    try:
        validate_index(load(INDEX))
        validate_dhw(load(DHW))
        check_handoff_pages()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, CheckError) as error:
        print(f"thermal SemReg mapping contract failed: {error}", file=sys.stderr)
        return 1
    print("Vaillant SemReg thermal mapping index passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
