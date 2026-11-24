#!/usr/bin/env python3
"""Validate the Vaillant controller qualification decision record.

A controller pair is qualified from the Identification descriptor, the
crosswalk's device ID and product number, and the register matrix. The
crosswalk's product-line column is read only to join the matrix and is not
published.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


FIXTURE = Path("architecture/fixtures/vaillant-controller-qualification-v1.json")
THERMAL = Path("architecture/fixtures/vaillant-semreg-thermal-map-v1.json")
CROSSWALK = Path("tests/fixtures/vaillant_regulator_identity_crosswalk_v1.json")
MATRIX = Path("protocols/vaillant/fixtures/b524-op02-requester-register-matrix.csv")
CONTEXT_RECEIPT = {
    "path": "architecture/fixtures/vaillant-controller-context-receipt-v1.json",
    "sha256": "45c49efa12526add9d6f1a975c37b9a159cf081b0925cca9476193c244d58f0a",
    "sha256_path": "architecture/fixtures/vaillant-controller-context-receipt-v1.sha256",
}
RECEIPT = {
    "schema_version": 1,
    "receipt_id": "helianthus.docs.ebus.vaillant-controller-context/v1",
    "conclusion": "Unknown",
    "receipt_status": "context_only_not_direct_identification",
    "direct_identification_evidence": None,
    "canonical_upstream": {
        "repository": "Project-Helianthus/helianthus-docs-ebus",
        "revision": "055738bbad31f5cfe7fcd87bffc16bc09e021571",
        "path": "protocols/vaillant/ebus-vaillant-b555-timer-protocol.md",
        "lines": "28-37",
        "blob_sha256": "2eff947174e4eb163b8e38f5eb93deb795491ec084e3e89ebc1dcdb7431e12ff",
        "canonical_url": "https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/055738bbad31f5cfe7fcd87bffc16bc09e021571/protocols/vaillant/ebus-vaillant-b555-timer-protocol.md",
        "canonical_url_status": "upstream metadata only; this receipt validator does not retrieve network or Git history",
    },
    "extracted_context": {"address": "0x15", "device_id": "BASV2", "software_version": "0507", "hardware_version": "1704"},
    "does_not_establish": ["direct 0x07/0x04 request", "direct 0x07/0x04 response", "raw manufacturer byte for this tuple", "registry qualification authority"],
}
REVISION = "vaillant-controller-qualification-evidence-gap/v1"
SCOPE = "native_controller_qualification"
WRITE_PERMISSION = (
    "Write operations of these rows follow the access flag the device reports "
    "for each register. This record grants or withholds none."
)
IDENTIFICATION = {
    "primary": "0x07",
    "secondary": "0x04",
    "length": 10,
    "manufacturer": "0xB5",
    "device_id_bytes": "1-5",
    "software_version_bytes": "6-7",
    "product_number_bytes": "8-9",
    "product_number_encoding": "bcd_least_significant_byte_first",
}
EVIDENCE_GRADES = {
    "identification_layout": "Proven",
    "product_number_reading": "Hypothesis",
    "crosswalk_pair": "Hypothesis",
}
TRANSITION = {
    "malformed_or_incomplete_input": "reject_without_mutation",
    "valid_direct_conflicting_observation": "retire_current_qualification_atomically",
    "sparse_matching_refresh": "may_retain_existing_direct_proof",
}
THERMAL_ROWS = [
    "PB=0xB5 SB=0x24 OP=0x02 GG=0x00 II=0x00 RR=0x0073",
    "PB=0xB5 SB=0x24 OP=0x02 GG=0x00 II=0x00 RR=0x004B",
    "PB=0xB5 SB=0x24 OP=0x02 GG=0x00 II=0x00 RR=0x0095",
]
NONCLAIMS = {
    "controller_or_firmware_tuple_qualified": False,
    "controller_family_range_qualified": False,
    "live_or_physical_qualification": False,
}
IDENTITY_KEYS = {"device_id", "product_number", "level", "evidence_grade"}
# group, register, page, semreg element or None, grade, unknown fact or None
DECLARED_PAGE_ROWS = (
    ("0x00", "0x0073", "architecture/outdoor-temperature-semreg-cutover.md", "thermal.measurement.outdoor_air_temperature", "Hypothesis", None),
    ("0x00", "0x004B", "architecture/b524-semantic-mapping.md", "thermal.measurement.system_flow_temperature", "Hypothesis", None),
    ("0x00", "0x0095", "architecture/outdoor-temperature-semreg-cutover.md", None, "Hypothesis", "rolling average has no SemReg element"),
    ("0x00", "0x0039", "architecture/system-pressure-semreg-disposition.md", None, "Hypothesis", "system pressure has no admitted SemReg element on this page"),
    ("0x00", "0x0007", "architecture/maintenance-system-state-cutover.md", None, "Hypothesis", "system switch is not a mode fact"),
    ("0x01", "0x0003", "architecture/dhw-mode-semreg-cutover.md", None, "Hypothesis", "hot-water mode element is not named"),
    ("0x01", "0x0004", "architecture/dhw-setpoint-semreg-cutover.md", "thermal.setpoint.dhw_temperature_setpoint", "Proven", None),
    ("0x01", "0x0005", "architecture/dhw-measured-temperature-cutover.md", "thermal.measurement.dhw_temperature", "Hypothesis", None),
    ("0x02", "0x0006", "architecture/circuit-capability-semreg-cutover.md", None, "Hypothesis", "circuit cooling enabled has no SemReg element"),
    ("0x02", "0x0008", "architecture/circuit-temperature-cutover.md", "thermal.measurement.circuit_flow_temperature", "Hypothesis", None),
    ("0x02", "0x001D", "architecture/b524-semantic-mapping.md", None, "Hypothesis", "circuit special function mode has no SemReg element"),
    ("0x03", "0x0006", "architecture/zone-mode-semreg-cutover.md", None, "Hypothesis", "zone mode element is not named"),
    ("0x03", "0x000F", "architecture/zone-room-temperature-cutover.md", "thermal.measurement.air_temperature", "Hypothesis", None),
    ("0x03", "0x0014", "architecture/zone-setpoint-semreg-cutover.md", None, "Hypothesis", "heating computed effective is a separate value"),
    ("0x03", "0x0022", "architecture/zone-setpoint-semreg-cutover.md", "thermal.setpoint.temperature_setpoint", "Hypothesis", None),
    ("0x03", "0x0028", "architecture/humidity-semreg-cutover.md", "thermal.measurement.humidity", "Hypothesis", None),
)
BOILER_TARGET = {
    "manufacturer": "0xB5",
    "device_id_prefix": "BAI",
    "heat_pump_device_id": "EHP00",
    "heat_pump_prefix": "HMU",
    "level": "declared",
    "hardware_test_record": None,
    "evidence_grade": "Hypothesis",
    "device_type_gate": "protocols/vaillant/ebus-vaillant-b509.md",
    "flow_row": {
        "service": "B509",
        "opcode": "0x0D",
        "selector": "18 00",
        "encoding": "DATA2c",
        "semreg_element": "thermal.measurement.heat_generator_flow_temperature",
        "evidence_grade": "Hypothesis",
        "qualified_binding_required": False,
        "page": "architecture/boiler-temperature-semreg-mapping.md",
    },
}
WRITE_ROUTES = {
    "zone_setpoint": "architecture/zone-setpoint-semreg-cutover.md",
    "zone_mode": "architecture/zone-mode-semreg-cutover.md",
    "hot_water_setpoint": "architecture/dhw-setpoint-semreg-cutover.md",
    "hot_water_mode": "architecture/dhw-mode-semreg-cutover.md",
    "system_mode": "architecture/b524-semantic-mapping.md",
}
GENERALIZES = {
    "qualified_binding_required": True,
    "generalizes_to_other_controllers": "The rule covers every device-id and product-number pair the identification descriptor matches in the crosswalk.",
    "generalizes_to_other_products": "A product number is bytes 8-9, BCD, least-significant byte first. An unlisted pair is unknown.",
    "generalizes_to_other_firmware": "The software version is recorded beside the result and does not restrict the pair.",
}
TOP_KEYS = {
    "schema_version", "contract_id", "revision", "scope", "qualified_use_permitted",
    "context_receipt", "transition_contract", "thermal_mapping", "thermal_rows",
    "identification", "evidence_grades", "level", "hardware_test_record",
    "identities", "declared_rows", "boiler_target", "vectors", "sources",
    "nonclaims", "write_permission",
}


class CheckError(ValueError):
    pass


def require(value: object, expected: object, label: str) -> None:
    if value != expected:
        raise CheckError(f"{label}: expected {expected!r}, got {value!r}")


def receipt_bytes() -> bytes:
    return Path(CONTEXT_RECEIPT["path"]).read_bytes()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_crosswalk() -> list[list[str]]:
    payload = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        raise CheckError("crosswalk rows")
    for row in rows:
        if not isinstance(row, list) or len(row) != 4 or any(not isinstance(item, str) for item in row):
            raise CheckError("crosswalk row shape")
    return rows


def load_matrix() -> list[dict[str, str]]:
    with MATRIX.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def listed_by_label() -> dict[str, set[tuple[str, str]]]:
    rows = load_crosswalk()
    found = {row[3]: set() for row in rows}
    for record in load_matrix():
        cell = record.get("family", "")
        group = record.get("group", "")
        register = record.get("register", "")
        for label in found:
            if cell == f"{label} family":
                found[label].add((group, register))
    return found


def device_ids_for(group: str, register: str) -> list[str]:
    listed = listed_by_label()
    seen: list[str] = []
    for device_id, _product, _model, label in load_crosswalk():
        if (group, register) in listed.get(label, set()) and device_id not in seen:
            seen.append(device_id)
    return seen


def controller_family(group: str, register: str) -> str:
    return "/".join(device_ids_for(group, register))


def expected_identities() -> list[dict[str, str]]:
    return [
        {
            "device_id": device_id,
            "product_number": product,
            "level": "declared",
            "evidence_grade": "Hypothesis",
        }
        for device_id, product, _model, _label in load_crosswalk()
    ]


def expected_declared_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for group, register, page, element, grade, unknown in DECLARED_PAGE_ROWS:
        device_ids = device_ids_for(group, register)
        if not device_ids:
            raise CheckError(f"{group} {register} is not listed for any pair")
        rows.append({
            "group": group,
            "register": register,
            "page": page,
            "semreg_element": element,
            "evidence_grade": grade,
            "unknown_fact": unknown,
            "device_ids": device_ids,
            "level": "declared",
            "hardware_test_record": None,
        })
    return rows


def expected_sources() -> dict[str, str]:
    return {
        "crosswalk": str(CROSSWALK),
        "register_matrix": str(MATRIX),
        "crosswalk_sha256": file_sha256(CROSSWALK),
        "register_matrix_sha256": file_sha256(MATRIX),
    }


def _bcd_nibbles(value: int) -> tuple[int, int] | None:
    high, low = value >> 4, value & 0x0F
    if high > 9 or low > 9:
        return None
    return high, low


def product_number(low: int, high: int) -> str:
    if low == 0xFF or high == 0xFF:
        return "ff_replacement"
    high_digits = _bcd_nibbles(high)
    low_digits = _bcd_nibbles(low)
    if high_digits is None or low_digits is None:
        return "invalid_bcd"
    number = 0
    for digit in high_digits + low_digits:
        number = number * 10 + digit
    return f"{number:04X}"


def software_version(first: int, second: int) -> str | None:
    left = _bcd_nibbles(first)
    right = _bcd_nibbles(second)
    if left is None or right is None:
        return None
    return f"{left[0]}{left[1]}{right[0]}{right[1]}"


def decode_descriptor(payload: bytes) -> dict[str, str]:
    if len(payload) != 10:
        return {"status": "reject_without_mutation", "reason": "incomplete"}
    device_bytes = payload[1:6]
    if any(byte < 32 or byte > 126 for byte in device_bytes):
        return {"status": "reject_without_mutation", "reason": "incomplete"}
    product = product_number(payload[8], payload[9])
    if product == "invalid_bcd":
        return {"status": "reject_without_mutation", "reason": "invalid_bcd"}
    version = software_version(payload[6], payload[7])
    if version is None:
        return {"status": "reject_without_mutation", "reason": "invalid_bcd"}
    decoded = {
        "status": "decoded",
        "manufacturer": f"0x{payload[0]:02X}",
        "device_id": device_bytes.decode("ascii"),
        "software_version": version,
        "product_number": product,
    }
    if product == "ff_replacement":
        decoded["status"] = "unknown"
        decoded["reason"] = "ff_replacement"
    return decoded


def _pair_index() -> dict[tuple[str, str], str]:
    return {(device_id, product): label for device_id, product, _model, label in load_crosswalk()}


def classify_controller(
    payload: bytes,
    request_address: str,
    response_address: str,
    *,
    group: str,
    register: str,
    current: dict[str, str] | None = None,
) -> dict[str, str]:
    if request_address.lower() != response_address.lower():
        return {"outcome": "reject_without_mutation", "reason": "address_mismatch"}
    decoded = decode_descriptor(payload)
    if decoded["status"] == "reject_without_mutation":
        return {"outcome": "reject_without_mutation", "reason": decoded["reason"]}
    if decoded["status"] == "unknown":
        return {"outcome": "unknown", "reason": decoded["reason"], "device_id": decoded["device_id"]}
    if decoded["manufacturer"] != "0xB5":
        return {"outcome": "unknown", "reason": "other_manufacturer", "device_id": decoded["device_id"]}
    label = _pair_index().get((decoded["device_id"], decoded["product_number"]))
    if label is None:
        return {
            "outcome": "unknown",
            "reason": "unlisted_pair",
            "device_id": decoded["device_id"],
            "product_number": decoded["product_number"],
        }
    listed = listed_by_label().get(label, set())
    if (group, register) not in listed:
        return {
            "outcome": "unknown",
            "reason": "register_not_listed",
            "device_id": decoded["device_id"],
            "product_number": decoded["product_number"],
        }
    qualified = {
        "device_id": decoded["device_id"],
        "product_number": decoded["product_number"],
        "software_version": decoded["software_version"],
        "level": "declared",
    }
    if current is None:
        return {"outcome": "qualified", **qualified}
    same = (
        current.get("address", "").lower() == response_address.lower()
        and current.get("device_id") == decoded["device_id"]
        and current.get("product_number") == decoded["product_number"]
    )
    if same:
        return {"outcome": "may_retain_existing_direct_proof", **qualified}
    return {"outcome": "retire_current_qualification_atomically", **qualified}


def classify_boiler(payload: bytes, selector: str) -> dict[str, str]:
    decoded = decode_descriptor(payload)
    if decoded["status"] == "reject_without_mutation":
        return {"outcome": "reject_without_mutation", "reason": decoded["reason"]}
    flow = BOILER_TARGET["flow_row"]
    if selector != flow["selector"]:
        return {"outcome": "unknown", "reason": "not_the_flow_row"}
    if decoded["status"] == "unknown":
        return {"outcome": "unknown", "reason": decoded["reason"]}
    if decoded["manufacturer"] != BOILER_TARGET["manufacturer"]:
        return {"outcome": "unknown", "reason": "other_manufacturer", "device_id": decoded["device_id"]}
    device_id = decoded["device_id"]
    if device_id == BOILER_TARGET["heat_pump_device_id"] or device_id.startswith(BOILER_TARGET["heat_pump_prefix"]):
        return {"outcome": "reject_heat_pump_collision", "device_id": device_id}
    if device_id.startswith(BOILER_TARGET["device_id_prefix"]):
        return {
            "outcome": "publish",
            "device_id": device_id,
            "semreg_element": flow["semreg_element"],
            "qualified_binding_required": "false",
            "level": "declared",
        }
    return {"outcome": "unknown", "reason": "not_boiler_class", "device_id": device_id}


def _vectors() -> list[dict[str, object]]:
    success_70000 = "B5373030303001232103"
    success_72000 = "B5373230303004567703"
    return [
        {
            "id": "exact_success_70000",
            "class": "controller",
            "request_address": "0x15",
            "response_address": "0x15",
            "payload_hex": success_70000,
            "group": "0x00",
            "register": "0x0073",
            "current": None,
            "expect": {
                "outcome": "qualified",
                "device_id": "70000",
                "product_number": "0141",
                "software_version": "0123",
                "level": "declared",
            },
        },
        {
            "id": "exact_success_72000",
            "class": "controller",
            "request_address": "0x15",
            "response_address": "0x15",
            "payload_hex": success_72000,
            "group": "0x00",
            "register": "0x004B",
            "current": None,
            "expect": {
                "outcome": "qualified",
                "device_id": "72000",
                "product_number": "0179",
                "software_version": "0456",
                "level": "declared",
            },
        },
        {
            "id": "unlisted_pair",
            "class": "controller",
            "request_address": "0x15",
            "response_address": "0x15",
            "payload_hex": "B5373030303001230100",
            "group": "0x00",
            "register": "0x0073",
            "current": None,
            "expect": {"outcome": "unknown", "reason": "unlisted_pair", "device_id": "70000", "product_number": "0001"},
        },
        {
            "id": "unknown_family",
            "class": "controller",
            "request_address": "0x15",
            "response_address": "0x15",
            "payload_hex": "B55A5A5A303001232103",
            "group": "0x00",
            "register": "0x0073",
            "current": None,
            "expect": {"outcome": "unknown", "reason": "unlisted_pair", "device_id": "ZZZ00"},
        },
        {
            "id": "other_manufacturer",
            "class": "controller",
            "request_address": "0x15",
            "response_address": "0x15",
            "payload_hex": "08373030303001232103",
            "group": "0x00",
            "register": "0x0073",
            "current": None,
            "expect": {"outcome": "unknown", "reason": "other_manufacturer"},
        },
        {
            "id": "truncated_payload",
            "class": "controller",
            "request_address": "0x15",
            "response_address": "0x15",
            "payload_hex": "B53730303030012321",
            "group": "0x00",
            "register": "0x0073",
            "current": None,
            "expect": {"outcome": "reject_without_mutation", "reason": "incomplete"},
        },
        {
            "id": "overlong_payload",
            "class": "controller",
            "request_address": "0x15",
            "response_address": "0x15",
            "payload_hex": "B537303030300123210300",
            "group": "0x00",
            "register": "0x0073",
            "current": None,
            "expect": {"outcome": "reject_without_mutation", "reason": "incomplete"},
        },
        {
            "id": "invalid_bcd_product_number",
            "class": "controller",
            "request_address": "0x15",
            "response_address": "0x15",
            "payload_hex": "B5373030303001230A03",
            "group": "0x00",
            "register": "0x0073",
            "current": None,
            "expect": {"outcome": "reject_without_mutation", "reason": "invalid_bcd"},
        },
        {
            "id": "replacement_ff",
            "class": "controller",
            "request_address": "0x15",
            "response_address": "0x15",
            "payload_hex": "B537303030300123FF03",
            "group": "0x00",
            "register": "0x0073",
            "current": None,
            "expect": {"outcome": "unknown", "reason": "ff_replacement"},
        },
        {
            "id": "address_mismatch",
            "class": "controller",
            "request_address": "0x15",
            "response_address": "0x16",
            "payload_hex": success_70000,
            "group": "0x00",
            "register": "0x0073",
            "current": None,
            "expect": {"outcome": "reject_without_mutation", "reason": "address_mismatch"},
        },
        {
            "id": "conflicting_direct_observation",
            "class": "controller",
            "request_address": "0x15",
            "response_address": "0x15",
            "payload_hex": success_72000,
            "group": "0x00",
            "register": "0x004B",
            "current": {"address": "0x15", "device_id": "70000", "product_number": "0141"},
            "expect": {"outcome": "retire_current_qualification_atomically", "device_id": "72000", "product_number": "0179"},
        },
        {
            "id": "sparse_matching_refresh_70000",
            "class": "controller",
            "request_address": "0x15",
            "response_address": "0x15",
            "payload_hex": success_70000,
            "group": "0x00",
            "register": "0x0073",
            "current": {"address": "0x15", "device_id": "70000", "product_number": "0141"},
            "expect": {"outcome": "may_retain_existing_direct_proof", "device_id": "70000", "product_number": "0141"},
        },
        {
            "id": "unlisted_row_70000",
            "class": "controller",
            "request_address": "0x15",
            "response_address": "0x15",
            "payload_hex": success_70000,
            "group": "0x00",
            "register": "0x0096",
            "current": None,
            "expect": {"outcome": "unknown", "reason": "register_not_listed", "device_id": "70000", "product_number": "0141"},
        },
        {
            "id": "declared_boiler_BAI00",
            "class": "boiler",
            "payload_hex": "B5424149303001230000",
            "selector": "18 00",
            "expect": {
                "outcome": "publish",
                "device_id": "BAI00",
                "semreg_element": "thermal.measurement.heat_generator_flow_temperature",
                "qualified_binding_required": "false",
                "level": "declared",
            },
        },
        {
            "id": "heat_pump_EHP00",
            "class": "boiler",
            "payload_hex": "B5454850303001230000",
            "selector": "18 00",
            "expect": {"outcome": "reject_heat_pump_collision", "device_id": "EHP00"},
        },
        {
            "id": "heat_pump_HMU00",
            "class": "boiler",
            "payload_hex": "B5484D55303001230000",
            "selector": "18 00",
            "expect": {"outcome": "reject_heat_pump_collision", "device_id": "HMU00"},
        },
        {
            "id": "boiler_other_manufacturer",
            "class": "boiler",
            "payload_hex": "08424149303001230000",
            "selector": "18 00",
            "expect": {"outcome": "unknown", "reason": "other_manufacturer"},
        },
        {
            "id": "boiler_malformed",
            "class": "boiler",
            "payload_hex": "B54241493030012300",
            "selector": "18 00",
            "expect": {"outcome": "reject_without_mutation", "reason": "incomplete"},
        },
    ]


def build_record() -> dict[str, object]:
    return {
        "schema_version": 1,
        "contract_id": "helianthus.docs.ebus.vaillant-controller-qualification/v1",
        "revision": REVISION,
        "scope": SCOPE,
        "qualified_use_permitted": True,
        "context_receipt": dict(CONTEXT_RECEIPT),
        "transition_contract": dict(TRANSITION),
        "thermal_mapping": {
            "contract_id": "helianthus.docs.ebus.b524-semreg-thermal/v1",
            "fixture": "architecture/fixtures/vaillant-semreg-thermal-map-v1.json",
            "qualified_binding_required": True,
        },
        "thermal_rows": list(THERMAL_ROWS),
        "identification": dict(IDENTIFICATION),
        "evidence_grades": dict(EVIDENCE_GRADES),
        "level": "declared",
        "hardware_test_record": None,
        "identities": expected_identities(),
        "declared_rows": expected_declared_rows(),
        "boiler_target": BOILER_TARGET,
        "vectors": _vectors(),
        "sources": expected_sources(),
        "nonclaims": dict(NONCLAIMS),
        "write_permission": WRITE_PERMISSION,
    }


def _run_vector(vector: dict[str, object]) -> dict[str, str]:
    payload = bytes.fromhex(str(vector["payload_hex"]))
    if vector["class"] == "boiler":
        return classify_boiler(payload, str(vector["selector"]))
    current = vector["current"]
    return classify_controller(
        payload,
        str(vector["request_address"]),
        str(vector["response_address"]),
        group=str(vector["group"]),
        register=str(vector["register"]),
        current=current if isinstance(current, dict) else None,
    )


def _forbidden_labels() -> set[str]:
    labels: set[str] = set()
    for _device, _product, model, family in load_crosswalk():
        labels.add(model)
        labels.add(family)
    return {label for label in labels if label}


def _walk_strings(value: object) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, dict):
        found.extend(_walk_strings(list(value.keys())))
        for item in value.values():
            found.extend(_walk_strings(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_walk_strings(item))
    return found


def _check_level(level: object, record_path: object, label: str) -> None:
    if level == "declared":
        return
    if level == "tested_on_hardware":
        if not isinstance(record_path, str) or not record_path:
            raise CheckError(f"{label}: tested_on_hardware requires a public test record path")
        return
    raise CheckError(f"{label}: level {level!r} is not a recorded level")


def validate_context_receipt() -> None:
    received = receipt_bytes()
    if b"](" in received:
        raise CheckError("context receipt must not contain relative links")
    if hashlib.sha256(received).hexdigest() != CONTEXT_RECEIPT["sha256"]:
        raise CheckError("context receipt digest")
    sidecar = Path(CONTEXT_RECEIPT["sha256_path"]).read_text(encoding="utf-8")
    expected_sidecar = f"{CONTEXT_RECEIPT['sha256']}  {Path(CONTEXT_RECEIPT['path']).name}\n"
    if sidecar != expected_sidecar:
        raise CheckError("context receipt digest sidecar")
    require(json.loads(received), RECEIPT, "context receipt")


def _validate_fixture_fields(value: dict[str, object]) -> None:
    if set(value) != TOP_KEYS:
        raise CheckError(f"qualification members must be exactly {sorted(TOP_KEYS)}")
    require(value.get("schema_version"), 1, "schema_version")
    require(value.get("contract_id"), "helianthus.docs.ebus.vaillant-controller-qualification/v1", "contract_id")
    require(value.get("revision"), REVISION, "revision")
    require(value.get("scope"), SCOPE, "scope")
    require(value.get("context_receipt"), CONTEXT_RECEIPT, "context_receipt")
    validate_context_receipt()
    require(value.get("transition_contract"), TRANSITION, "transition_contract")
    require(value.get("thermal_mapping"), {
        "contract_id": "helianthus.docs.ebus.b524-semreg-thermal/v1",
        "fixture": str(THERMAL),
        "qualified_binding_required": True,
    }, "thermal_mapping")
    require(value.get("thermal_rows"), THERMAL_ROWS, "thermal_rows")
    require(value.get("identification"), IDENTIFICATION, "identification")
    require(value.get("evidence_grades"), EVIDENCE_GRADES, "evidence_grades")
    require(value.get("write_permission"), WRITE_PERMISSION, "write_permission")
    require(value.get("nonclaims"), NONCLAIMS, "nonclaims")
    require(value.get("boiler_target"), BOILER_TARGET, "boiler_target")
    if value.get("boiler_target", {}).get("flow_row", {}).get("qualified_binding_required") is not False:
        raise CheckError("boiler flow row qualified_binding_required stays false")
    _check_level(value.get("level"), value.get("hardware_test_record"), "record")


def _validate_fixture_identities_and_sources(value: dict[str, object]) -> list[dict[str, object]]:
    identities = value.get("identities")
    if not _identities_allow_hardware(identities):
        raise CheckError("identities must be the crosswalk device-id and product-number pairs")
    for identity in identities:
        _check_level(identity.get("level"), value.get("hardware_test_record"), str(identity.get("device_id")))
    declared = value.get("declared_rows")
    if declared != expected_declared_rows():
        raise CheckError("declared rows must be the page rows the matrix lists, keyed by device id")
    sources = value.get("sources")
    if sources != expected_sources():
        raise CheckError("crosswalk or register-matrix digest")
    for text in _walk_strings(value):
        for label in _forbidden_labels():
            if label and label in text:
                raise CheckError("a product-line or model name is not a published key")
    if "write_or_operation_authority" in json.dumps(value):
        raise CheckError("write_or_operation_authority is not a member")
    return identities


def _validate_fixture_vectors(value: dict[str, object], identities: list[dict[str, object]]) -> None:
    vectors = value.get("vectors")
    canonical = _vectors()
    if not isinstance(vectors, list) or len(vectors) != len(canonical):
        raise CheckError("vectors")
    for vector, expected in zip(vectors, canonical, strict=True):
        if not isinstance(vector, dict):
            raise CheckError("vector")
        got = _run_vector(vector)
        expect = vector.get("expect")
        if not isinstance(expect, dict) or any(got.get(key) != item for key, item in expect.items()):
            raise CheckError(f"{vector.get('id')}: vector contradicts the rule ({got!r})")
    if vectors != canonical:
        raise CheckError("vectors")
    declared_levels = [row.get("level") for row in identities] if isinstance(identities, list) else []
    if any(level in {"declared", "tested_on_hardware"} for level in declared_levels):
        if value.get("qualified_use_permitted") is not True:
            raise CheckError("qualified_use_permitted stays true while a pair is declared")


def validate_fixture(value: object, thermal: object) -> None:
    if not isinstance(value, dict) or not isinstance(thermal, dict):
        raise CheckError("fixtures must be objects")
    _validate_fixture_fields(value)
    identities = _validate_fixture_identities_and_sources(value)
    _validate_fixture_vectors(value, identities)
    _check_thermal_binding(value, thermal)


def _identities_allow_hardware(identities: object) -> bool:
    if not isinstance(identities, list) or len(identities) != len(expected_identities()):
        return False
    for got, expected in zip(identities, expected_identities(), strict=True):
        if not isinstance(got, dict) or set(got) != IDENTITY_KEYS:
            return False
        if got.get("device_id") != expected["device_id"] or got.get("product_number") != expected["product_number"]:
            return False
        if got.get("evidence_grade") != "Hypothesis":
            return False
        if got.get("level") not in {"declared", "tested_on_hardware"}:
            return False
    return True


def _check_thermal_binding(value: dict[str, object], thermal: dict[str, object]) -> None:
    require(thermal.get("qualification"), {
        "contract_id": value["contract_id"],
        "revision": value["revision"],
        "fixture": str(FIXTURE),
        "level": "declared",
        "qualified_binding_required": True,
        "runtime_qualification_permitted": True,
        "hardware_test_record": None,
    }, "thermal qualification binding")
    require(thermal.get("boiler_target"), value["boiler_target"], "thermal boiler target")
    require(thermal.get("write_routes"), WRITE_ROUTES, "thermal write_routes")
    require(thermal.get("applicability"), GENERALIZES, "thermal applicability")
    family = controller_family("0x00", "0x0073")
    mappings = thermal.get("mappings")
    if not isinstance(mappings, list):
        raise CheckError("thermal mappings")
    for row in mappings:
        if not isinstance(row, dict):
            raise CheckError("thermal mapping row")
        selector = row.get("native_selector")
        if not isinstance(selector, dict) or selector.get("controller_family") != family:
            raise CheckError("controller_family must list the device ids the bus transmits")
    nonclaims = thermal.get("nonclaims")
    if not isinstance(nonclaims, dict):
        raise CheckError("thermal nonclaims")
    if "write_route_established" in nonclaims or "operation_authority_established" in nonclaims:
        raise CheckError("retired write nonclaims")
    hardware = nonclaims.get("hardware_qualification_established")
    if not isinstance(hardware, bool):
        raise CheckError("hardware_qualification_established records whether a public test record exists")


def main() -> int:
    try:
        validate_fixture(json.loads(FIXTURE.read_text(encoding="utf-8")), json.loads(THERMAL.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, CheckError, ValueError) as error:
        print(f"Vaillant controller qualification failed: {error}")
        return 1
    print("Vaillant controller qualification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
