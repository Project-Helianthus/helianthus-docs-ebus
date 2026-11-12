#!/usr/bin/env python3
"""Check bounded public spelling and optional offline emission parity."""
from __future__ import annotations

import argparse
import os
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
        'heatingMode',
        'EnergyCategory',
        'EnergyBucket',
        'zonesUpdate',
        'energyTotalsUpdate',
        'systemUpdate',
        'circuitsUpdate',
        "currentTempC", "currentHumidityPct", "targetTempC", "operatingMode",
        "semanticSnapshot", "assetIds", "assetId", "snapshotId", "packId",
        "packVersion", "factId", "candidateId", "itemId", "sourceItems",
        "unavailableReason", "zoneUpdate", "ZoneState", "ZoneConfig",
    )
    # Enum values retain their spelling; only names are adopted by this wave.
    preserved_values = (
        "REGULATOR", "FUNCTION_MODULE", "UNKNOWN", "INTERPRETED", "GPIO_ONLY",
        "ABSENT", "CONTROLLER_UNREACHABLE", "CONFIGURATION_UNAVAILABLE",
        "CONFIGURATION_NOT_INTERPRETABLE", "SOLAR_ACQUISITION_FAILED",
        "CYLINDER_ACQUISITION_FAILED", "EVIDENCE_STALE", "INCOHERENT_ACQUISITION",
    )
    for value in preserved_values:
        if re.search(r"\b" + value.lower() + r"\b", graphql_blocks):
            raise ValueError("GraphQL enum value spelling changed")
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



REMAINING_TOKENS = ['maintenanceDue', 'heatingMode', 'calcFlowTempC', 'corroboratedPending', 'macAddress', 'activeKeys', 'boilerConfig', 'deviceId', 'maxInterval', 'targetBucket', 'dhwStarts', 'm2mGraphqlConfig', 'systemStatus', 'fm5SemanticMode', 'activationCounts', 'busAdmissionRejectedCandidate', 'completionMode', 'staticPinnedFootprint', 'unqualifiedBound', 'unsupportedOrMisconfigured', 'systemUpdate', 'dhwDemandActive', 'snakeCase', 'invokeError', 'deactivationsIfc', 'automaticRetryScheduled', 'circuitManagingDevice', 'minC', 'passiveObserved', 'coolingEnabled', 'flowsetHwcMaxC', 'dedupDegraded', 'systemScheme', 'staticSeed', 'systemOff', 'pumpActive', 'requestLen', 'freshnessClasses', 'systemWaterPressure', 'compactorDegraded', 'unknownProfile', 'targetTempC', 'meanInterval', 'fanHours', 'dhwBivalencePoint', 'discoverySource', 'pumpHours', 'storageLoadPumpPct', 'dhwWaterFlowLpm', 'pinnedBudgetDegraded', 'busBoundedListSummary', 'updatesAvailable', 'maxC', 'seriesBudgetOverflowTotal', 'interfaceVersion', 'busPeriodicity', 'boilerDiagnostics', 'm2mGraphqlRuntime', 'selectedSource', 'heatingSwitchActive', 'outdoorTemperatureAvg24H', 'quickVetoExpiry', 'writeConfirmPinnedActive', 'circuitConfig', 'watchSummaryDegraded', 'lastSeen', 'elapsedSeconds', 'responseSchema', 'projectionNode', 'dhwState', 'flowTemperatureC', 'hcEmergencyTemperature', 'adaptiveHeatingCurve', 'sourceSelection', 'partNumber', 'companionTarget', 'zoneRoomHumidity', 'requiredTransactions', 'circuitState', 'evidenceRevision', 'setSystemConfig', 'dhwConfig', 'busMessages', 'busSummary', 'startupTimeout', 'boilerStatus', 'daemonStatus', 'diverterValvePositionPct', 'hwcCylinderTemperatureTop', 'flowsetHcMaxC', 'catalogDescriptors', 'centralHeatingHours', 'directApplyEligibilityClasses', 'returnTemperatureC', 'busAdmissionSourceSelection', 'shadowingEnabled', 'firmwareVersion', 'dhwBivalencePointBound', 'energyTotalsUpdate', 'dhwTemperatureC', 'productFamily', 'circulationPumpActive', 'degradedReason', 'summerLimitC', 'ebusV1SemanticSystemSetConfig', 'activeProbe', 'boilerConfigMutationResult', 'modulationPct', 'currentTempC', 'dewPoint', 'energyBucket', 'dhwOperatingMode', 'dhwUpdate', 'alternativePoint', 'activeConfirmed', 'controllerProfile', 'reconnectTimeout', 'verificationState', 'partloadHwcKw', 'centralHeatingStarts', 'sourceBucket', 'dhwHours', 'liveEpoch', 'boilerState', 'unmatchedPolicy', 'cacheEpoch', 'nextAction', 'flowTempMaxC', 'circuitType', 'warmingUp', 'narrowedOnly', 'circuitsUpdate', 'readOnly', 'flowTempDesiredC', 'moduleConfigurationVr71', 'pumpStarts', 'ebusV1RpcInvoke', 'capabilityWithdrawn', 'zoneConfig', 'stateClasses', 'dhwOutdoorBivalenceTemperatureLimit', 'interfaceRevision', 'systemConfig', 'activeSupported', 'waterPressureBar', 'maxRoomHumidity', 'managingDeviceRole', 'projectionEdge', 'dhwTempDesiredC', 'timingQuality', 'broadcastSupported', 'mixerPositionPct', 'managingDevice', 'sourceAddress', 'dhwStatusRaw', 'fanSpeedRpm', 'busPeriodicityEntry', 'systemFlowTemperature', 'primaryCircuitFlowLpm', 'busPeriodicityList', 'serviceStatus', 'busObservabilityStatus', 'roomTempControl', 'hwcCylinderTemperatureBottom', 'flowSetpointC', 'systemProperties', 'observedAt', 'lastInterval', 'responseLen', 'productModel', 'initiatorAddress', 'configMutationResult', 'broadcastEvent', 'deactivationsTemplimiter', 'sourceClasses', 'pinClasses', 'outdoorTemperature', 'energyCategory', 'unknownRegister', 'setBoilerConfig', 'softwareVersion', 'tapConnected', 'rejectedCandidates', 'frameType', 'hardwareVersion', 'getOperationalData', 'circuitStatus', 'busMessage', 'centralHeatingPumpActive', 'lastSuccessfulSource', 'busObservabilityWarmup', 'pinnedEntries', 'displayName', 'zoneState', 'systemState', 'watchSummaryClassCount', 'quickVetoSetpoint', 'hasMixer', 'heatingCircuitBivalencePoint', 'boilerStatusUpdate', 'endpointState', 'dhwTargetTemperatureC', 'busObservabilityCounters', 'systemBounds', 'zoneRoomTemperature', 'heatingStatusRaw', 'flowTempMinC', 'systemConfigBound', 'targetAddress', 'targetFanSpeedRpm', 'invalidBound', 'ebusV1SemanticFm5InterpretationGet', 'busMessagesList', 'socketLoss', 'evictableEntries', 'zonesUpdate', 'busObservabilityCapability', 'busObservabilityDegraded', 'invokeResult', 'm2mGraphqlEnabled', 'quickVeto', 'watchSummaryInventory', 'minInterval', 'busAdmissionActiveProbe', 'operatingMode', 'watchSummary', 'identityConfirmed', 'heatingCurve', 'periodicityBudgetOverflowTotal', 'passiveState', 'totalEntries', 'completedTransactions', 'sampleCount', 'frostProtC', 'testSystemConfigBoundContract', 'passiveReason', 'serialNumber', 'passiveSupported', 'hwcMaxFlowTempDesired', 'flapDampened', 'partloadHcKw', 'gasValveActive', 'ebusV1SemanticSystemGet', 'flameActive', 'energyTotals', 'ionisationVoltageUa', 'busObservabilityTimingQuality', 'busAdmission', 'watchSummaryActivationCounts', 'canonicalPath', 'fm5Interpretation', 'fm5SemanticDegradedReason', 'passiveAvailable', 'transportClass', 'externalPumpActive', 'stateNumber', 'modbus.v1.profile.observation.get', 'modbus.v1.raw.read', 'ebus.v1.semantic.boiler_status.get', 'ebus.v1.semantic.dhw.get', 'ebus.v1.semantic.circuits.get', 'ebus.v1.semantic.solar.get', 'current_temp_c', 'circuitState', 'frameType', 'assetIds', 'circuitType']


# Adopted spellings may occur in the exemption inventory for correspondence.
# They do not make extensions of the adopted schema names stale.
ADOPTED_GRAPHQL_TOKENS = {"current_temp_c"}
STALE_GRAPHQL_TOKENS = set(REMAINING_TOKENS) - ADOPTED_GRAPHQL_TOKENS


def graphql_fence_spans(text: str):
    """Yield body offsets for GraphQL fences, including extended info strings."""
    opening = None
    offset = 0
    for line in text.splitlines(keepends=True):
        if opening is None:
            match = re.match(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)", line)
            if match and not (match[1][0] == "`" and "`" in match[2]):
                info = match[2].split()
                opening = (match[1], bool(info and info[0] == "graphql"),
                           offset + len(line))
        else:
            marker, is_graphql, start = opening
            if re.fullmatch(r" {0,3}" + re.escape(marker[0]) +
                            r"{" + str(len(marker)) + r",}[ \t]*(?:\r?\n)?", line):
                if is_graphql:
                    yield start, offset
                opening = None
        offset += len(line)
    if opening is not None and opening[1]:
        yield opening[2], len(text)


def graphql_name_text(body: str) -> str:
    """Mask comments and regular/block strings before scanning GraphQL names."""
    lexical_data = r'"""(?:\\"""|(?!""")[\s\S])*"""|"(?:\\[\s\S]|[^"\\])*"|#[^\r\n]*'
    return re.sub(lexical_data, lambda match: " " * len(match[0]), body)


def remaining_occurrences(root: Path):
    result = {}
    paths = []
    for directory, directories, files in os.walk(root):
        directories[:] = sorted(d for d in directories if not d.startswith('.') and d != '__pycache__')
        paths.extend(Path(directory) / name for name in sorted(files))
    for path in paths:
        relative = path.relative_to(root)
        if (not path.is_file() or any(part.startswith(".") for part in relative.parts)
                or "__pycache__" in relative.parts or str(relative) in EXCLUSIONS
                or str(relative) == "tests/fixtures/remaining_page_name_exemptions.json"):
            continue
        try:
            text = path.read_text()
        except (UnicodeError, OSError):
            continue
        fences = list(graphql_fence_spans(text))
        blocks = "\n".join(graphql_name_text(text[start:end]) for start, end in fences)
        for identifier in re.findall(r"\b[A-Za-z_]\w*\b", blocks):
            if any(re.match(re.escape(token) + r"[_A-Z]", identifier)
                   for token in STALE_GRAPHQL_TOKENS):
                raise ValueError("partial stale GraphQL identifier")
        for token in REMAINING_TOKENS:
            if token not in text:
                continue
            for match in re.finditer(r"(?<![\w])" + re.escape(token) + r"(?![\w])", text):
                # Bind exemptions to prose or GraphQL context as well as counts.
                in_graphql = any(start <= match.start() < end for start, end in fences)
                context = "graphql:" + token if in_graphql else token
                key = (str(relative), token, context)
                result[key] = result.get(key, 0) + 1
    return result


def validate_remaining_pages(root: Path):
    entries = json.loads((root / "tests/fixtures/remaining_page_name_exemptions.json").read_text())
    expected = {}
    for entry in entries:
        key = (entry["file"], entry["token"], entry["context"])
        if key in expected or not entry["reason"]:
            raise ValueError("duplicate or unexplained naming exemption")
        expected[key] = entry["count"]
    if remaining_occurrences(root) != expected:
        raise ValueError("remaining API spelling or stale naming exemption")


def validate_root(root: Path, gateway: Path | None = None) -> None:
    validate_remaining_pages(root)
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
