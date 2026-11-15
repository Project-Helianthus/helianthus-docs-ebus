#!/usr/bin/env python3
"""Validate the controller's structural relation and identity candidates.

The fixture answers, as the native owner, which controller attachments are
observable relations for a stated scope, which are configuration only, which
offer no candidate, and whether a controller-mediated device slot and a direct
bus entry of one unit share an anchor key source.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = Path("architecture/fixtures/structural-relation-candidates-v1.json")
DECISIONS_PAGE = Path("architecture/b524-structural-decisions.md")
MODULES_PAGE = Path("architecture/functional-modules.md")
DISCOVERY_PAGE = Path("architecture/semantic-structure-discovery.md")
REGISTER_MAP = Path("protocols/vaillant/ebus-vaillant-b524-register-map.md")
PAGES = (DECISIONS_PAGE, MODULES_PAGE, DISCOVERY_PAGE, REGISTER_MAP)
SCHEMA = "helianthus.docs.ebus.structural-relation-candidates/v1"

TOP_KEYS = {"schema", "decision_catalog", "attachments", "relayed_identity"}
ROW_KEYS = {
    "id", "decisions", "attachment", "published_field", "from", "to",
    "evidence_grade", "validity_scope", "disposition", "native_statements",
    "reason", "pending_review",
}
ENDPOINT_KEYS = {"kind", "identity_evidence", "resolution"}
EVIDENCE_KEYS = {"selector", "role", "classification"}
STATEMENT_KEYS = {"selector", "source", "reading", "scope"}
IDENTITY_KEYS = {
    "id", "decisions", "groups", "relaying_end", "slot_view", "direct_view",
    "shared_anchor_key_source", "disposition", "reason",
}
VIEW_KEYS = {"kind", "identity_evidence"}
DIRECT_VIEW_KEYS = {"kind", "status", "identity_evidence"}

REQUIRED_DECISIONS = (
    "SD-05", "SD-06", "SD-07", "SD-09", "SD-10", "SD-15", "functional-modules",
)
# Each catalogued row keeps the disposition its decision entry states and the
# native identity of each end: endpoint kind and (selector, role) pairs.
ROOT_END = ("b524_semantic_root", (("PB=0xB5 SB=0x24", "b524_capability"), ("ZZ", "bus_address")))
DIRECT_END = (("PB=0x07 SB=0x04", "bus_identification"), ("ZZ", "bus_address"))
ZONE = "OP=0x02 GG=0x03 II=zone"
CIRCUIT = "OP=0x02 GG=0x02 II=circuit"
MODULE = "OP=0x06 GG=0x0C II=slot"
ALL_SLOTS = "OP=0x06 GG=0x01/0x02/0x09/0x0A/0x0C/0x0E/0x0F II=slot"
ZONE_END = ("zone_instance", ((ZONE, "instance_position"),))
CIRCUIT_END = ("circuit_instance", ((CIRCUIT, "instance_position"),))
MODULE_END = ("functional_module", (
    (MODULE, "instance_position"), (MODULE + " RR=0x0002", "class_address"),
))
REQUIRED_ROWS = {
    "SRC-SD05-zone-room-unit": ("relation_candidate", ("zone_instance", (
        (ZONE, "instance_position"), (ZONE + " RR=0x0013", "binding_value"),
    )), ("device_slot", (("OP=0x06 GG=0x09/0x0A II=slot", "instance_position"),))),
    "SRC-SD06-zone-to-circuit": ("unresolved", ZONE_END, CIRCUIT_END),
    "SRC-SD07-zone-to-circuit-fallback": ("absent", ZONE_END, CIRCUIT_END),
    "SRC-SD09-circuit-managing-module": ("configuration_only", CIRCUIT_END, MODULE_END),
    "SRC-SD10-connected-device-slot": ("relation_candidate", ROOT_END, ("device_slot", (
        (ALL_SLOTS, "instance_position"), (ALL_SLOTS + " RR=0x0001", "presence"),
        (ALL_SLOTS + " RR=0x0002", "class_address"), (ALL_SLOTS + " RR=0x0004", "firmware_version"),
        ("OP=0x06 GG=0x09/0x0A II=slot RR=0x0023", "hardware_identifier"),
    ))),
    "SRC-SD10-inventory-device-slot": ("absent", ROOT_END, ("device_slot", (
        (MODULE, "instance_position"), (MODULE + " RR=0x0001", "presence"),
        (MODULE + " RR=0x0004", "firmware_version"),
    ))),
    "SRC-SD15-controller-zone": ("relation_candidate", ROOT_END, ZONE_END),
    "SRC-SD15-controller-circuit": ("relation_candidate", ROOT_END, ("circuit_instance", (
        (CIRCUIT, "instance_position"), (CIRCUIT + " RR=0x0002", "presence"),
    ))),
    "SRC-SD15-module-solar-circuit": ("configuration_only", MODULE_END, (
        "solar_circuit", (("OP=0x02 GG=0x04", "instance_position"),))),
    "SRC-SD15-module-cylinder": ("configuration_only", MODULE_END, (
        "cylinder_instance", (("OP=0x02 GG=0x05 II=cylinder", "instance_position"),))),
    "SRC-FM-second-family-slot": ("absent", ROOT_END, (
        "device_slot", (("OP=0x06 GG=0x0B II=slot", "instance_position"),))),
    "SRC-FM-second-family-status": ("absent", ROOT_END, ("functional_module", (
        ("OP=0x02 GG=0x00 RR=0x0067", "presence"), ("OP=0x02 GG=0x00 RR=0x0068", "presence"),
    ))),
}
REQUIRED_ROW_IDS = set(REQUIRED_ROWS)
# Each catalogued row also keeps its published field, the resolution of each
# end, its evidence grade and its validity scope (order not significant).
REQUIRED_ROW_FACTS = {
    "SRC-SD05-zone-room-unit": (
        "zones[].config.roomTemperatureZoneMapping", "native", "gateway_policy", "Proven", ("PROTOCOL",)),
    "SRC-SD06-zone-to-circuit": (
        "zones[].config.associatedCircuit", "native", "unresolved", "Unknown", ("LAB", "PROFILE")),
    "SRC-SD07-zone-to-circuit-fallback": (
        "zones[].config.associatedCircuit", "native", "gateway_policy", "Unknown", ("GATEWAY_POLICY",)),
    "SRC-SD09-circuit-managing-module": (
        "circuits[].managing_device", "native", "gateway_policy", "Proven", ("LAB", "PROFILE")),
    "SRC-SD10-connected-device-slot": ("radioDevices[]", "native", "native", "Proven", ("PROTOCOL",)),
    "SRC-SD10-inventory-device-slot": (
        "radioDevices[]", "native", "gateway_policy", "Hypothesis", ("GATEWAY_POLICY",)),
    "SRC-SD15-controller-zone": ("zones[]", "native", "native", "Proven", ("PROTOCOL",)),
    "SRC-SD15-controller-circuit": ("circuits[]", "native", "native", "Proven", ("PROTOCOL",)),
    "SRC-SD15-module-solar-circuit": ("solar", "gateway_policy", "native", "Proven", ("PROFILE",)),
    "SRC-SD15-module-cylinder": ("cylinders", "gateway_policy", "native", "Proven", ("PROFILE",)),
    "SRC-FM-second-family-slot": (None, "native", "unresolved", "Unknown", ("PROFILE",)),
    "SRC-FM-second-family-status": (None, "native", "unresolved", "Unknown", ("PROFILE",)),
}
# Each catalogued relayed-identity row keeps its slot grouping and the
# status of its direct view; the relaying end is always resolved natively.
REQUIRED_IDENTITY = {
    "SRI-functional-module-slot": (("0x0C",), "correlated"),
    "SRI-heat-source-slots": (("0x01", "0x02"), "not_established"),
    "SRI-room-unit-slots": (("0x09", "0x0A"), "not_established"),
    "SRI-uncharacterized-slots": (("0x0E", "0x0F"), "not_established"),
}
RELAYING_END_RESOLUTION = "native"
DISPOSITIONS = {"relation_candidate", "configuration_only", "absent", "unresolved"}
EVIDENCE_GRADES = {"Proven", "Hypothesis", "Unknown"}
SCOPES = {"PROTOCOL", "PROFILE", "LAB", "GATEWAY_POLICY"}
NATIVE_SCOPES = {"PROTOCOL", "PROFILE", "LAB"}
ENDPOINT_KINDS = {
    "b524_semantic_root", "zone_instance", "circuit_instance", "device_slot",
    "functional_module", "solar_circuit", "cylinder_instance", "direct_bus_entry",
}
RESOLUTIONS = {"native", "gateway_policy", "unresolved"}
ROLE_CLASSIFICATION = {
    "instance_position": "native_position",
    "presence": "attribute",
    "class_address": "interpretation_selector",
    "firmware_version": "attribute",
    "hardware_identifier": "attribute",
    "binding_value": "relation_value",
    "assignment_value": "relation_value",
    "configuration_code": "interpretation_selector",
    "b524_capability": "provenance",
    "bus_identification": "interpretation_selector",
    "bus_address": "bus_address",
}
ANCHOR_SOURCES = {"native_token", "native_position", "operator_label", "none"}
IDENTITY_DISPOSITIONS = {"one_resource", "two_views_unresolved"}
DIRECT_STATUSES = {"correlated", "not_established"}
SELECTOR = re.compile(
    r"(OP=0x0[26] GG=0x[0-9A-F]{2}(/0x[0-9A-F]{2})*( II=[a-z]+)?"
    r"( RR=0x[0-9A-F]{4})?|PB=0x[0-9A-F]{2} SB=0x[0-9A-F]{2}|ZZ)"
)
ROW_ID = re.compile(r"SRC-[A-Z0-9]+(-[a-z0-9]+)+")
IDENTITY_ID = re.compile(r"SRI(-[a-z0-9]+)+")
NAME = re.compile(r"[a-z][a-z0-9]*(_[a-z0-9]+)*")
STATEMENT_SOURCES = {
    "decision_catalog": DECISIONS_PAGE,
    "functional_modules": MODULES_PAGE,
    "register_map": REGISTER_MAP,
}
ZONE_TO_CIRCUIT = "zone_to_circuit"
ZONE_CIRCUIT_SELECTORS = {
    "OP=0x02 GG=0x03 II=zone RR=0x0013",
    "OP=0x02 GG=0x03 II=zone RR=0x001C",
}
FIXTURE_LINK = "fixtures/structural-relation-candidates-v1.json"
COMMON_MODEL = "common model"
RETIRED_SENTENCES = (
    "consumer-side parent resolution",
    "Consumer-specific parent trees remain consumer behavior",
)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def read_pages(root: Path) -> dict:
    return {page.as_posix(): (root / page).read_text(encoding="utf-8") for page in PAGES}


def check_keys(value, expected: set, label: str, errors: list) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label}: must be an object")
        return False
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        errors.append(f"{label}: keys differ (missing {missing}, unexpected {extra})")
        return False
    return True


def check_text(value, label: str, errors: list) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        errors.append(f"{label}: must be non-empty trimmed text")


def check_member(value, vocabulary: set, label: str, errors: list) -> None:
    if not isinstance(value, str) or value not in vocabulary:
        errors.append(f"{label}: {value!r} is not one of {sorted(vocabulary)}")


def check_selector(value, label: str, errors: list) -> None:
    if not isinstance(value, str) or not SELECTOR.fullmatch(value):
        errors.append(f"{label}: {value!r} is not a native selector")


def check_evidence(items, label: str, errors: list) -> None:
    if not isinstance(items, list) or not items:
        errors.append(f"{label}: identity evidence must be a non-empty list")
        return
    seen = set()
    for index, item in enumerate(items):
        where = f"{label}[{index}]"
        if not check_keys(item, EVIDENCE_KEYS, where, errors):
            continue
        check_selector(item["selector"], f"{where}.selector", errors)
        check_member(item["role"], set(ROLE_CLASSIFICATION), f"{where}.role", errors)
        expected = ROLE_CLASSIFICATION.get(item["role"])
        if expected is not None and item["classification"] != expected:
            errors.append(f"{where}.classification: role {item['role']} is {expected}")
        pair = (item["selector"], item["role"])
        if pair in seen:
            errors.append(f"{where}: duplicate identity evidence")
        seen.add(pair)


def check_endpoint(endpoint, label: str, errors: list) -> None:
    if not check_keys(endpoint, ENDPOINT_KEYS, label, errors):
        return
    check_member(endpoint["kind"], ENDPOINT_KINDS, f"{label}.kind", errors)
    check_member(endpoint["resolution"], RESOLUTIONS, f"{label}.resolution", errors)
    check_evidence(endpoint["identity_evidence"], f"{label}.identity_evidence", errors)


def check_statements(items, label: str, errors: list, pages: dict | None = None) -> None:
    if not isinstance(items, list):
        errors.append(f"{label}: must be a list")
        return
    for index, item in enumerate(items):
        where = f"{label}[{index}]"
        if not check_keys(item, STATEMENT_KEYS, where, errors):
            continue
        check_selector(item["selector"], f"{where}.selector", errors)
        check_member(item["source"], set(STATEMENT_SOURCES), f"{where}.source", errors)
        check_source_anchor(item, where, errors, pages)
        check_text(item["reading"], f"{where}.reading", errors)
        check_member(item["scope"], SCOPES, f"{where}.scope", errors)


def selector_groups(selector: str) -> list:
    match = re.search(r"GG=((?:0x[0-9A-F]{2}/?)+)", selector)
    return match.group(1).split("/") if match else []


def check_source_anchor(item: dict, where: str, errors: list, pages: dict | None) -> None:
    source = item.get("source")
    selector = item.get("selector")
    if pages is None or source not in STATEMENT_SOURCES or not isinstance(selector, str):
        return
    text = pages[STATEMENT_SOURCES[source].as_posix()].upper()
    register = re.search(r"RR=(0X[0-9A-F]{4})", selector.upper())
    if register and register.group(1) not in text:
        errors.append(f"{where}: source {source} does not contain register {register.group(1)}")
    groups = selector_groups(selector)
    if groups and not register and not all(group.upper() in text for group in groups):
        errors.append(f"{where}: source {source} does not contain the cited group")


def check_decisions(value, label: str, errors: list) -> None:
    if not isinstance(value, list) or not value or len(set(map(str, value))) != len(value):
        errors.append(f"{label}: must be a non-empty list without duplicates")
        return
    for item in value:
        check_member(item, set(REQUIRED_DECISIONS), label, errors)


def check_scopes(value, label: str, errors: list) -> None:
    if not isinstance(value, list) or not value or len(set(map(str, value))) != len(value):
        errors.append(f"{label}: must be a non-empty list without duplicates")
        return
    for item in value:
        check_member(item, SCOPES, label, errors)


def check_published_field(value, label: str, errors: list, pages: dict) -> None:
    if value is None:
        return
    quoted = f"`{value}`"
    if not isinstance(value, str) or not any(
        quoted in pages[page.as_posix()] for page in (DECISIONS_PAGE, MODULES_PAGE)
    ):
        errors.append(f"{label}: {value!r} is not a field quoted on the decision pages")


def check_disposition_rules(row: dict, label: str, errors: list) -> None:
    disposition = row["disposition"]
    statements = row["native_statements"] if isinstance(row["native_statements"], list) else []
    scopes = set(row["validity_scope"]) if isinstance(row["validity_scope"], list) else set()
    if disposition == "unresolved":
        if row["pending_review"] is None:
            errors.append(f"{label}: an unresolved row names its pending review")
        if len(statements) < 2 or row["evidence_grade"] != "Unknown":
            errors.append(f"{label}: an unresolved row names two native statements, grade Unknown")
    elif row["pending_review"] is not None:
        errors.append(f"{label}: only an unresolved row carries a pending review")
    if disposition == "relation_candidate":
        if not scopes or not scopes <= NATIVE_SCOPES or row["evidence_grade"] == "Unknown":
            errors.append(f"{label}: a relation candidate needs a native scope and evidence")
    if disposition in {"relation_candidate", "configuration_only"} and not statements:
        errors.append(f"{label}: {disposition} needs a native statement")


def check_row(row, index: int, errors: list, pages: dict) -> None:
    label = f"attachments[{index}]"
    if not check_keys(row, ROW_KEYS, label, errors):
        return
    if not isinstance(row["id"], str) or not ROW_ID.fullmatch(row["id"]):
        errors.append(f"{label}.id: {row['id']!r} is not a row identifier")
    check_decisions(row["decisions"], f"{label}.decisions", errors)
    if not isinstance(row["attachment"], str) or not NAME.fullmatch(row["attachment"]):
        errors.append(f"{label}.attachment: must be a snake_case native name")
    check_published_field(row["published_field"], f"{label}.published_field", errors, pages)
    check_endpoint(row["from"], f"{label}.from", errors)
    check_endpoint(row["to"], f"{label}.to", errors)
    check_member(row["evidence_grade"], EVIDENCE_GRADES, f"{label}.evidence_grade", errors)
    check_scopes(row["validity_scope"], f"{label}.validity_scope", errors)
    check_member(row["disposition"], DISPOSITIONS, f"{label}.disposition", errors)
    check_statements(row["native_statements"], f"{label}.native_statements", errors, pages)
    check_text(row["reason"], f"{label}.reason", errors)
    if row["pending_review"] is not None:
        check_text(row["pending_review"], f"{label}.pending_review", errors)
    if not errors_for(label, errors):
        check_disposition_rules(row, label, errors)
        check_pinned_row(row, errors)


def evidence_pairs(endpoint: dict) -> list:
    return sorted((item["selector"], item["role"]) for item in endpoint["identity_evidence"])


def check_pinned_end(endpoint: dict, expected: tuple, label: str, errors: list,
                     resolution: str | None = None) -> None:
    kind, pairs = expected
    if endpoint["kind"] != kind or evidence_pairs(endpoint) != sorted(pairs):
        errors.append(f"{label}: native identity differs from the catalogued {kind} end {sorted(pairs)}")
    if resolution is not None and endpoint["resolution"] != resolution:
        errors.append(f"{label}.resolution: the catalogue states {resolution}")


def check_pinned_row(row: dict, errors: list) -> None:
    row_id = row["id"]
    if row_id not in REQUIRED_ROWS:
        errors.append(f"{row_id}: not a catalogued attachment row")
        return
    disposition, source, target = REQUIRED_ROWS[row_id]
    field, source_resolution, target_resolution, grade, scopes = REQUIRED_ROW_FACTS[row_id]
    if row["disposition"] != disposition:
        errors.append(f"{row_id}.disposition: the catalogue states {disposition}")
    if row["published_field"] != field:
        errors.append(f"{row_id}.published_field: the catalogue states {field!r}")
    if row["evidence_grade"] != grade:
        errors.append(f"{row_id}.evidence_grade: the catalogue states {grade}")
    if sorted(row["validity_scope"]) != sorted(scopes):
        errors.append(f"{row_id}.validity_scope: the catalogue states {sorted(scopes)}")
    check_pinned_end(row["from"], source, f"{row_id}.from", errors, source_resolution)
    check_pinned_end(row["to"], target, f"{row_id}.to", errors, target_resolution)


def check_pinned_identity(row: dict, errors: list) -> None:
    row_id = row["id"]
    if row_id not in REQUIRED_IDENTITY:
        errors.append(f"{row_id}: not a catalogued relayed-identity row")
        return
    groups, status = REQUIRED_IDENTITY[row_id]
    if sorted(row["groups"]) != sorted(groups):
        errors.append(f"{row_id}.groups: the catalogue states {sorted(groups)}")
    if row["direct_view"]["status"] != status:
        errors.append(f"{row_id}.direct_view.status: the catalogue states {status}")
    check_pinned_end(row["relaying_end"], ROOT_END, f"{row_id}.relaying_end", errors, RELAYING_END_RESOLUTION)
    check_pinned_end(row["direct_view"], ("direct_bus_entry", DIRECT_END), f"{row_id}.direct_view", errors)


def errors_for(label: str, errors: list) -> bool:
    return any(error.startswith(label + ".") or error.startswith(label + ":") for error in errors)


def check_zone_to_circuit(rows: list, errors: list) -> None:
    matching = [row for row in rows if isinstance(row, dict) and row.get("attachment") == ZONE_TO_CIRCUIT]
    unresolved = []
    for row in matching:
        if row.get("disposition") not in {"unresolved", "absent"}:
            errors.append(f"{row.get('id')}: the zone-to-circuit assignment stays unresolved")
        if row.get("disposition") == "unresolved":
            unresolved.append(row)
    named = [
        {item.get("selector") for item in row.get("native_statements", []) if isinstance(item, dict)}
        for row in unresolved
    ]
    if not any(ZONE_CIRCUIT_SELECTORS <= selectors for selectors in named):
        errors.append("zone_to_circuit: one unresolved row names both native statements")


def check_identity_row(row, index: int, errors: list) -> None:
    label = f"relayed_identity[{index}]"
    if not check_keys(row, IDENTITY_KEYS, label, errors):
        return
    if not isinstance(row["id"], str) or not IDENTITY_ID.fullmatch(row["id"]):
        errors.append(f"{label}.id: {row['id']!r} is not a row identifier")
    check_decisions(row["decisions"], f"{label}.decisions", errors)
    groups = row["groups"]
    if not isinstance(groups, list) or not groups or not all(
        isinstance(group, str) and re.fullmatch(r"0x[0-9A-F]{2}", group) for group in groups
    ):
        errors.append(f"{label}.groups: must list OP=0x06 group numbers")
    check_endpoint(row["relaying_end"], f"{label}.relaying_end", errors)
    check_group_binding(row, label, errors)
    check_view(row["slot_view"], VIEW_KEYS, "device_slot", f"{label}.slot_view", errors)
    check_view(row["direct_view"], DIRECT_VIEW_KEYS, "direct_bus_entry", f"{label}.direct_view", errors)
    check_member(row["shared_anchor_key_source"], ANCHOR_SOURCES, f"{label}.shared_anchor_key_source", errors)
    check_member(row["disposition"], IDENTITY_DISPOSITIONS, f"{label}.disposition", errors)
    check_text(row["reason"], f"{label}.reason", errors)
    source, disposition = row["shared_anchor_key_source"], row["disposition"]
    if source == "none" and disposition != "two_views_unresolved":
        errors.append(f"{label}: without a shared anchor key source the views stay two, unresolved")
    if source in {"native_position", "none"} and disposition == "one_resource":
        errors.append(f"{label}: one resource needs a shared native token or operator label")
    if disposition == "two_views_unresolved" and source != "none":
        errors.append(f"{label}: a shared anchor key source resolves to one resource")
    if not errors_for(label, errors):
        check_pinned_identity(row, errors)


def check_group_binding(row: dict, label: str, errors: list) -> None:
    view, groups = row.get("slot_view"), row.get("groups")
    if not isinstance(view, dict) or not isinstance(groups, list):
        return
    evidence = view.get("identity_evidence")
    if not isinstance(evidence, list):
        return
    bound = [
        selector_groups(item["selector"]) for item in evidence
        if isinstance(item, dict) and isinstance(item.get("selector"), str)
        and item["selector"].startswith("OP=0x06")
    ]
    if not bound or any(sorted(found) != sorted(map(str, groups)) for found in bound):
        errors.append(f"{label}.groups: must equal the groups of the slot_view selectors")


def check_view(view, keys: set, kind: str, label: str, errors: list) -> None:
    if not check_keys(view, keys, label, errors):
        return
    if view["kind"] != kind:
        errors.append(f"{label}.kind: must be {kind}")
    if "status" in keys:
        check_member(view["status"], DIRECT_STATUSES, f"{label}.status", errors)
    check_evidence(view["identity_evidence"], f"{label}.identity_evidence", errors)


def slot_groups(pages: dict) -> list:
    text = pages[DECISIONS_PAGE.as_posix()]
    section = text.split("## B524-SD-10", 1)[-1].split("\n## ", 1)[0]
    match = re.search(r"\| Source registers \| `GG=((?:0x[0-9A-F]{2}/?)+) RR=0x0001`", section)
    return sorted(match.group(1).split("/")) if match else []


def check_identity_coverage(rows: list, errors: list, pages: dict) -> None:
    expected = slot_groups(pages)
    if not expected:
        errors.append("SD-10: the device-slot groups are not readable from the decision page")
        return
    listed = [group for row in rows if isinstance(row, dict) for group in row.get("groups", []) or []]
    if sorted(listed) != expected:
        errors.append(f"relayed_identity: groups {sorted(listed)} must cover SD-10 groups {expected} once")
    present = {row.get("id") for row in rows if isinstance(row, dict)}
    for missing in sorted(set(REQUIRED_IDENTITY) - present):
        errors.append(f"coverage: relayed-identity row {missing} is missing")


def check_coverage(rows: list, errors: list, pages: dict, identity: list) -> None:
    named = {item for row in rows if isinstance(row, dict) for item in row.get("decisions", []) or []}
    for decision in REQUIRED_DECISIONS:
        if decision not in named:
            errors.append(f"coverage: no attachment row for {decision}")
        if decision.startswith("SD-") and f"## B524-{decision} " not in pages[DECISIONS_PAGE.as_posix()]:
            errors.append(f"coverage: {decision} is not a heading of the decision page")
    present = {row.get("id") for row in rows if isinstance(row, dict)}
    for missing in sorted(REQUIRED_ROW_IDS - present):
        errors.append(f"coverage: attachment row {missing} is missing")
    ids = [row.get("id") for row in rows + identity if isinstance(row, dict)]
    if len(ids) != len(set(map(str, ids))):
        errors.append("fixture: row identifiers repeat across attachments and relayed_identity")


def check_pages(pages: dict, errors: list) -> None:
    for page in (DECISIONS_PAGE, MODULES_PAGE, DISCOVERY_PAGE):
        if FIXTURE_LINK not in pages[page.as_posix()]:
            errors.append(f"{page}: does not reference the relation-candidate fixture")
    decisions = pages[DECISIONS_PAGE.as_posix()]
    for sentence in RETIRED_SENTENCES:
        if sentence in decisions:
            errors.append(f"{DECISIONS_PAGE}: still hands parenting to consumers ({sentence!r})")
    for decision in ("SD-10", "SD-15"):
        section = decisions.split(f"## B524-{decision} ", 1)[-1].split("\n## ", 1)[0]
        if COMMON_MODEL not in section:
            errors.append(f"{DECISIONS_PAGE}: {decision} does not hand parenting to the common model")
    register_map = pages[REGISTER_MAP.as_posix()]
    for register, name in (("0x0013", "zone_room_sensor_binding_mode"), ("0x001C", "zone_circuit_assignment")):
        if f"| {register} | {name} |" not in register_map:
            errors.append(f"{REGISTER_MAP}: GG=0x03 RR={register} {name} row is missing")


def section_text(pages: dict, decision: str) -> str:
    if decision == "functional-modules":
        return pages[MODULES_PAGE.as_posix()]
    text = pages[DECISIONS_PAGE.as_posix()]
    return text.split(f"## B524-{decision} ", 1)[-1].split("\n## ", 1)[0] if f"## B524-{decision} " in text else ""


def check_citations(rows: list, errors: list, pages: dict) -> None:
    for item in rows:
        if not isinstance(item, dict) or not isinstance(item.get("decisions"), list) or not item["decisions"]:
            continue
        primary = item["decisions"][0]
        if primary in REQUIRED_DECISIONS and f"`{item.get('id')}`" not in section_text(pages, primary):
            errors.append(f"{item.get('id')}: not cited in the {primary} text")


def validate(document, pages: dict) -> list:
    errors: list = []
    if not check_keys(document, TOP_KEYS, "fixture", errors):
        return errors
    if document["schema"] != SCHEMA:
        errors.append(f"fixture.schema: must be {SCHEMA}")
    if document["decision_catalog"] != DECISIONS_PAGE.as_posix():
        errors.append(f"fixture.decision_catalog: must be {DECISIONS_PAGE}")
    rows, identity = document["attachments"], document["relayed_identity"]
    if not isinstance(rows, list) or not rows or not isinstance(identity, list) or not identity:
        errors.append("fixture: attachments and relayed_identity are non-empty lists")
        return errors
    for index, row in enumerate(rows):
        check_row(row, index, errors, pages)
    for index, row in enumerate(identity):
        check_identity_row(row, index, errors)
    check_zone_to_circuit(rows, errors)
    check_coverage(rows, errors, pages, identity)
    check_identity_coverage(identity, errors, pages)
    check_citations(rows + identity, errors, pages)
    check_pages(pages, errors)
    return errors


def main(argv: list | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0]).resolve() if args else ROOT
    try:
        document = load_json(root / FIXTURE)
        pages = read_pages(root)
    except (OSError, ValueError) as error:
        print(f"structural relation candidates: {error}", file=sys.stderr)
        return 1
    errors = validate(document, pages)
    for error in errors:
        print(f"structural relation candidates: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"structural relation candidates: {len(document['attachments'])} attachment rows "
          f"and {len(document['relayed_identity'])} relayed-identity rows valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
