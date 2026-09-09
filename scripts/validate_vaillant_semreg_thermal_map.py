#!/usr/bin/env python3
"""Validate the typed Vaillant B524-to-SemReg thermal mapping index."""
from __future__ import annotations

import json
from pathlib import Path
import sys


INDEX = Path("architecture/fixtures/vaillant-semreg-thermal-map-v1.json")
EXPECTED_SELECTORS = {
    "state.outdoor_temperature": "0x0073",
    "state.system_flow_temperature": "0x004B",
    "state.outdoor_temperature_avg24h": "0x0095",
}
EXPECTED_FACTS = {
    "state.outdoor_temperature": (
        "thermal.measurement.air_temperature", "temperature:outdoor_air", "exact", None
    ),
    "state.system_flow_temperature": (
        "thermal.measurement.water_temperature", "temperature:system_flow", "exact", None
    ),
    "state.outdoor_temperature_avg24h": (
        None, None, "withheld", "rolling_average_window_unrepresentable"
    ),
}
REQUIRED_NONCLAIMS = {
    "write_route_established", "operation_authority_established", "topology_established",
    "full_portal_descriptor_established", "prometheus_output_established",
    "eebus_output_established", "matter_output_established",
    "hardware_qualification_established",
}


class CheckError(ValueError):
    """The typed public thermal mapping index is invalid."""


def require(value: object, expected: object, label: str) -> None:
    if value != expected:
        raise CheckError(f"{label}: expected {expected!r}, got {value!r}")


def validate_index(index: object) -> None:
    if not isinstance(index, dict):
        raise CheckError("index must be an object")
    require(index.get("schema_version"), 1, "schema_version")
    require(index.get("contract_id"), "helianthus.docs.ebus.b524-semreg-thermal/v1", "contract_id")
    require(index.get("scope"), "read_only_candidate_mapping", "scope")
    require(index.get("pack"), {"id": "helianthus.pack.thermal", "version": "1.0.0"}, "pack")

    applicability = index.get("applicability")
    if not isinstance(applicability, dict):
        raise CheckError("applicability must be an object")
    require(applicability, {
        "qualified_binding_required": True,
        "generalizes_to_other_controllers": False,
        "generalizes_to_other_products": False,
        "generalizes_to_other_firmware": False,
    }, "applicability")
    require(index.get("qualification"), {
        "contract_id": "helianthus.docs.ebus.vaillant-controller-qualification/v1",
        "revision": "vaillant-controller-qualification-evidence-gap/v1",
        "fixture": "architecture/fixtures/vaillant-controller-qualification-v1.json",
        "evidence_status": "unproven",
        "qualified_binding_required": True,
        "runtime_qualification_permitted": False,
    }, "qualification")

    mappings = index.get("mappings")
    if not isinstance(mappings, list) or len(mappings) != 3:
        raise CheckError("mappings must contain exactly three rows")
    by_legacy: dict[str, dict[str, object]] = {}
    for row in mappings:
        if not isinstance(row, dict):
            raise CheckError("mapping row must be an object")
        legacy = row.get("legacy_system_field")
        if not isinstance(legacy, str) or legacy in by_legacy:
            raise CheckError("mapping rows need unique legacy_system_field values")
        by_legacy[legacy] = row
        selector = row.get("native_selector")
        if not isinstance(selector, dict):
            raise CheckError(f"{legacy}: native_selector must be an object")
        require(selector, {
            "pb": "0xB5", "sb": "0x24", "operation": "0x02", "group": "0x00",
            "instance": "0x00", "register": EXPECTED_SELECTORS.get(legacy),
            "destination": "0x15", "controller_family": "BASV2/CTLV2/VRC720",
            "request_direction": "initiator_to_target", "value_direction": "target_to_initiator",
        }, f"{legacy}: native_selector")
        require(row.get("native_value"), {"wire_type": "f32_le", "unit": "degC"}, f"{legacy}: native_value")

        fact, dimension_value, disposition, loss = EXPECTED_FACTS.get(legacy, (None, None, None, None))
        require(row.get("semreg_fact"), fact, f"{legacy}: semreg_fact")
        require(row.get("disposition"), disposition, f"{legacy}: disposition")
        require(row.get("loss"), loss, f"{legacy}: loss")
        expected_dimensions = (
            {"thermal.dimension.temperature": dimension_value}
            if disposition == "exact" else None
        )
        require(row.get("dimensions"), expected_dimensions, f"{legacy}: dimensions")
        expected_semreg_value = {"kind": "quantity", "unit": "unit.celsius"} if disposition == "exact" else None
        require(row.get("semreg_value"), expected_semreg_value, f"{legacy}: semreg_value")
    if set(by_legacy) != set(EXPECTED_SELECTORS):
        raise CheckError("mapping inventory differs from the closed three-row contract")

    nonclaims = index.get("nonclaims")
    if not isinstance(nonclaims, dict) or set(nonclaims) != REQUIRED_NONCLAIMS:
        raise CheckError("nonclaims must contain the closed public-boundary inventory")
    if any(value is not False for value in nonclaims.values()):
        raise CheckError("all nonclaims must remain false")
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


def main() -> int:
    try:
        validate_index(json.loads(INDEX.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, CheckError) as error:
        print(f"thermal SemReg mapping contract failed: {error}", file=sys.stderr)
        return 1
    print("Vaillant SemReg thermal mapping index passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
