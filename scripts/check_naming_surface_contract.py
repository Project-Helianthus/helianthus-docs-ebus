#!/usr/bin/env python3
"""Check bounded public spelling and optional offline emission parity."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

SCRIPT_ROOT = Path(__file__).resolve().parent


def _load_checkers():
    if str(SCRIPT_ROOT) not in sys.path:
        sys.path.insert(0, str(SCRIPT_ROOT))
    import check_mcp_inventory as mcp
    import validate_prometheus_semantic_coverage as metrics

    return mcp, metrics


mcp, metrics = _load_checkers()

ROOT = SCRIPT_ROOT.parent
# This unit has a different shape; spelling alone cannot establish parity.
# Its six artifacts remain excluded under docs-ebus#1166.
EXCLUSIONS = {
    path: "shape differs; docs-ebus#1166"
    for path in (
        "api/public-graphql-m2m-v1.graphql",
        "api/public-graphql-m2m-v1.query.graphql",
        "docs/platform/manifests/public-graphql-m2m-v1.json",
        "docs/platform/fixtures/public-graphql-m2m/v1/cases.json",
        "scripts/validate_public_graphql_m2m_v1.py",
        "tests/test_public_graphql_m2m_v1.py",
    )
}
SETTER_FAMILIES = {
    "circuit": ("circuit_heating_curve_factor",
                "heating_circuit_flow_temperature_setpoint_maximum",
                "circuit_flow_temperature_setpoint_minimum",
                "heating_circuit_outdoor_temperature_limit_maximum",
                "circuit_room_temperature_influence_mode", "circuit_cooling_enabled"),
    "system": ("dhwBivalencePointC", "installerMenuCode"),
    "zone": ("operatingMode", "quickVetoTemperature", "quickVetoDuration",
             "desiredSetpoint", "holidaySetpoint"),
    "boiler": ("flowsetHcMaxC", "flowsetHwcMaxC", "partloadHcKW",
               "partloadHwcKW", "phoneNumber", "installerMenuCode"),
}


def _validate_tool_names(tools: str, registration) -> None:
    profiles, rows = mcp.documented_rows(tools)
    mcp.unique_rows(rows, profiles)
    for row in rows:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", row["name"]):
            raise ValueError("registered tool spelling is not snake_case")
        if row["name"] in {"ebus_devices", "ebus_invoke"}:
            raise ValueError("removed tool restored under a second name")
    if registration is not None:
        mcp.validate(registration, tools)


def _validate_graphql_names(graphql: str) -> None:
    # Scope the value assertions to the zone object, preserving distinct DHW meaning.
    zone = re.search(r"type zone_state\s*\{([^}]+)\}", graphql)
    if zone is None:
        raise ValueError("zone_state declaration missing")
    fields = re.findall(r"^\s*(\w+)\s*:", zone[1], re.M)
    if fields != ["zone_room_temperature", "zone_room_humidity"]:
        raise ValueError("zone value spelling or membership differs")
    for old in ("ZoneState", "ZoneConfig", "semanticSnapshot", "assetIds"):
        if re.search(r"\b" + old + r"\b", graphql):
            raise ValueError("removed GraphQL spelling restored")
    # Restrict API member checks to schema/examples; native strings and the
    # documentary correspondence retain their own identities.
    graphql_blocks = "\n".join(re.findall(r"```graphql\n(.*?)\n```", graphql, re.S))
    removed = (
        "currentTempC", "currentHumidityPct", "targetTempC", "operatingMode",
        "semanticSnapshot", "assetIds", "assetId", "snapshotId", "packId",
        "packVersion", "factId", "candidateId", "itemId", "sourceItems",
        "unavailableReason", "zoneUpdate", "ZoneState", "ZoneConfig",
    )
    for old in removed:
        if re.search(r"\b" + old + r"\b", graphql_blocks):
            raise ValueError("removed GraphQL member spelling restored")


def _validate_setter_families(tools: str) -> None:
    for family, keys in SETTER_FAMILIES.items():
        if any(
                f"`{key}`" not in tools for key in keys):
            raise ValueError(f"missing setter family: {family}")


def _validate_qualifications(graphql: str, tools: str) -> None:
    if "provisional" not in tools or "provisional" not in graphql:
        raise ValueError("provisional naming qualification missing")
    if not all(key in tools for key in ("frostProtC", "frost_prot_c", "rejected without dispatch")):
        raise ValueError("withdrawn control boundary missing")
    if "docs-ebus#1166" not in graphql and "public-graphql-m2m-v1" not in graphql:
        raise ValueError("separate M2M shape limitation missing")


def validate(graphql: str, tools: str, coverage: str, registration=None) -> None:
    _validate_tool_names(tools, registration)
    _validate_graphql_names(graphql)
    _validate_setter_families(tools)
    _validate_qualifications(graphql, tools)
    metrics.validate(coverage)



OPERATION_NAMES = {
    "semanticOperation": "semantic_operation",
    "SemanticOperationInput": "semantic_operation_input",
    "SemanticOperationResult": "semantic_operation_result",
    "SemanticDefinitionRefInput": "semantic_definition_ref_input",
    "SemanticTypedFieldInput": "semantic_typed_field_input",
    "SemanticPreconditionInput": "semantic_precondition_input",
    "assetId": "asset_id", "bindingId": "binding_id",
    "capabilityInstanceId": "capability_instance_id",
    "expectedSemanticRevision": "expected_semantic_revision",
    "expectedCapabilityRevision": "expected_capability_revision",
    "expectedCapabilityInstanceRevision": "expected_capability_instance_revision",
    "expectedSourceEpochId": "expected_source_epoch_id",
    "expectedDriverGeneration": "expected_driver_generation",
    "timeoutMs": "timeout_ms", "kernelOutcome": "kernel_outcome",
    "readbackRelation": "readback_relation",
}


def validate_operation(page: str, contract: str) -> None:
    for old, adopted in OPERATION_NAMES.items():
        for document in (page, contract):
            if re.search(r"\b" + old + r"\b", document):
                raise ValueError("removed operation spelling restored")
            if not re.search(r"\b" + adopted + r"\b", document):
                raise ValueError("operation member or type missing")


def validate_root(root: Path, gateway: Path | None = None) -> None:
    validate_operation((root / "api/semantic-operation-route.md").read_text(),
                       (root / "tests/semantic_operation_route_contract.json").read_text())
    registration = None
    if gateway is not None:
        text = (gateway / "docs/mcp-tool-inventory.md").read_text()
        registration = json.loads(re.search(r"```json\n(.*?)\n```", text, re.S)[1])
        emitted = json.loads((gateway / "docs/metrics-inventory.json").read_text())
        expected = [(r["name"], r["type"], ", ".join(r["labels"]) or "none",
                     r.get("constant_unit", "none")) for r in emitted["families"]]
        actual = metrics.rows("\n".join("| " + line for line in metrics.RENDERER_ROWS.strip().splitlines()))
        if actual != expected:
            raise ValueError("metric emission parity differs")
    validate((root / "api/graphql.md").read_text(),
             (root / "api/mcp.md").read_text(),
             (root / metrics.DOCUMENT).read_text(), registration)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--gateway-root", type=Path)
    args = parser.parse_args()
    supplied = args.root / ".tmp/references/ebusgateway"
    gateway = args.gateway_root or (supplied if supplied.is_dir() else None)
    if gateway is None:
        print("Naming contract: UNVERIFIED without an offline emission reference", file=sys.stderr)
        return 2
    try:
        validate_root(args.root, gateway)
    except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
        print(f"Naming contract: {error}", file=sys.stderr)
        return 1
    print("Naming contract passed; offline emission parity checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
