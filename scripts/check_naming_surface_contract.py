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
}
# The accepted keys of these families come from the gateway's published
# setter-key file; the page lists exactly those keys under one heading each.
SETTER_KEY_FILE = "docs/testing/config-setter-keys.json"
SETTER_KEY_FORMAT = "helianthus.ebusgateway.config_setter_keys.v1"
SETTER_KEY_FAMILIES = {
    "system": ("set_system_config", "#### System setter keys"),
    "zone": ("set_zone_config", "#### Zone setter keys"),
    "boiler": ("set_boiler_config", "#### Boiler setter keys"),
}
# Previous spellings of each family; none is accepted or listed as current.
PREVIOUS_SETTER_KEYS = {
    "system": ("dhwBivalencePointC", "maxRoomHumidityPct", "adaptiveHeatingCurve",
               "hcBivalencePointC", "hcEmergencyTempC", "maintenanceDate",
               "hwcMaxFlowTempC", "installerName", "installerPhone",
               "installerMenuCode"),
    "zone": ("holidaySetpoint", "operatingMode", "quickVetoTemperature",
             "desiredSetpoint", "quickVetoDuration"),
    "boiler": ("flowsetHcMaxC", "flowsetHwcMaxC", "partloadHcKW",
               "partloadHwcKW", "phoneNumber"),
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


def _validate_system_members(graphql: str) -> None:
    system_members = {
        "system_state": (
            "system_off", "water_pressure", "flow_temperature", "outdoor_temperature",
            "outdoor_temperature_avg24h", "maintenance_due",
            "hwc_cylinder_temperature_top", "hwc_cylinder_temperature_bottom",
        ),
        "system_config": (
            "adaptive_heating_curve_enabled", "alternative_point",
            "heating_outdoor_bivalence_temperature_limit", "dhw_bivalence_point",
            "dhw_bivalence_point_bound", "hc_emergency_temperature",
            "hwc_max_flow_temp_desired", "room_humidity_limit_maximum",
        ),
        "system_properties": (
            "hydraulic_scheme_code", "functional_module_configuration_code",
        ),
    }
    for type_name, expected in system_members.items():
        declarations = re.findall(r"type " + type_name + r"\s*\{([^}]+)\}", graphql)
        if len(declarations) != 1:
            raise ValueError(type_name + " declaration membership differs")
        members = re.findall(r"^\s*(\w+)\s*:", declarations[0], re.M)
        if sorted(members) != sorted(expected):
            raise ValueError(type_name + " value spelling or membership differs")


def _validate_graphql_names(graphql: str) -> None:
    _validate_system_members(graphql)
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


def _setter_key(row) -> tuple[str, bool]:
    """Return one accepted key and whether its register meaning is open."""
    key = row.get("key") if isinstance(row, dict) else None
    is_open = row.get("open") if isinstance(row, dict) else None
    if not isinstance(key, str) or not key or not isinstance(is_open, bool):
        raise ValueError("malformed setter key reference: key entry")
    question = row.get("open_question")
    if is_open and (not isinstance(question, str) or not question.strip()):
        raise ValueError("malformed setter key reference: open key without question")
    if not is_open and not re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*", key):
        raise ValueError("malformed setter key reference: key spelling")
    return key, is_open


def _setter_family_keys(setters: dict, setter: str) -> dict:
    entry = setters.get(setter)
    rows = entry.get("keys") if isinstance(entry, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError("malformed setter key reference: " + setter)
    keys = dict(_setter_key(row) for row in rows)
    if len(keys) != len(rows):
        raise ValueError("malformed setter key reference: duplicate key in " + setter)
    return keys


def load_setter_keys(gateway: Path) -> dict:
    """Read the accepted keys per family; a missing or malformed file fails."""
    path = gateway / SETTER_KEY_FILE
    if not path.is_file():
        raise ValueError("setter key reference missing: " + SETTER_KEY_FILE)
    try:
        document = json.loads(path.read_text())
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("malformed setter key reference") from error
    if not isinstance(document, dict) or document.get("format") != SETTER_KEY_FORMAT:
        raise ValueError("malformed setter key reference: format")
    setters = document.get("setters")
    if not isinstance(setters, dict):
        raise ValueError("malformed setter key reference: setters")
    return {family: _setter_family_keys(setters, setter)
            for family, (setter, _) in SETTER_KEY_FAMILIES.items()}


def documented_setter_rows(tools: str, heading: str):
    """Return (key, row) pairs of the table under one setter heading."""
    match = re.search(r"^" + re.escape(heading) + r"\n(.*?)(?=^#|\Z)", tools, re.M | re.S)
    if match is None:
        return None
    return [(row[1], row[0]) for row in
            re.finditer(r"^\| `([^`]+)` \|.*$", match[1], re.M)]


def _documented_setter_keys(tools: str) -> dict:
    documented = {}
    for family, (_, heading) in SETTER_KEY_FAMILIES.items():
        rows = documented_setter_rows(tools, heading)
        if not rows:
            raise ValueError(f"missing setter family: {family}")
        keys = [key for key, _ in rows]
        if len(set(keys)) != len(keys):
            raise ValueError(f"duplicate setter key: {family}")
        if set(keys) & set(PREVIOUS_SETTER_KEYS[family]):
            raise ValueError(f"previous setter key listed: {family}")
        documented[family] = dict(rows)
    return documented


def _reject_previous_setter_keys(texts, current: set) -> None:
    for key in sorted(set().union(*PREVIOUS_SETTER_KEYS.values()) - current):
        if any(re.search(r"(?<![\w])" + re.escape(key) + r"(?![\w])", text)
               for text in texts):
            raise ValueError(f"previous setter key named: {key}")


def _compare_setter_keys(documented: dict, setter_keys: dict) -> None:
    for family, expected in setter_keys.items():
        actual = documented[family]
        if set(expected) - set(actual):
            raise ValueError(f"missing setter key: {family}")
        if set(actual) - set(expected):
            raise ValueError(f"extra setter key: {family}")
        if any(is_open and "provisional" not in actual[key].lower()
               for key, is_open in expected.items()):
            raise ValueError(f"open setter key not provisional: {family}")


def _validate_setter_families(tools: str, graphql: str = "", setter_keys=None) -> None:
    for family, keys in SETTER_FAMILIES.items():
        if any(
                f"`{key}`" not in tools for key in keys):
            raise ValueError(f"missing setter family: {family}")
    documented = _documented_setter_keys(tools)
    current = set().union(*documented.values(), *(setter_keys or {}).values())
    _reject_previous_setter_keys((tools, graphql), current)
    if setter_keys is not None:
        _compare_setter_keys(documented, setter_keys)


def _validate_qualifications(graphql: str, tools: str) -> None:
    if "provisional" not in tools or "provisional" not in graphql:
        raise ValueError("provisional naming qualification missing")
    if not all(key in tools for key in ("frostProtC", "frost_prot_c", "rejected without dispatch")):
        raise ValueError("withdrawn control boundary missing")
    if "docs-ebus#1166" not in graphql and "public-graphql-m2m-v1" not in graphql:
        raise ValueError("separate M2M shape limitation missing")


def validate(graphql: str, tools: str, coverage: str, registration=None,
             setter_keys=None) -> None:
    _validate_tool_names(tools, registration)
    _validate_graphql_names(graphql)
    _validate_setter_families(tools, graphql, setter_keys)
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


def markdown_fence_spans(text: str):
    """Yield body offsets and language for fenced examples."""
    opening = None
    offset = 0
    for line in text.splitlines(keepends=True):
        if opening is None:
            match = re.match(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)", line)
            if match and not (match[1][0] == "`" and "`" in match[2]):
                info = match[2].split()
                opening = (match[1], info[0] if info else "",
                           offset + len(line))
        else:
            marker, language, start = opening
            if re.fullmatch(r" {0,3}" + re.escape(marker[0]) +
                            r"{" + str(len(marker)) + r",}[ \t]*(?:\r?\n)?", line):
                yield start, offset, language
                opening = None
        offset += len(line)
    if opening is not None:
        yield opening[2], len(text), opening[1]


def graphql_fence_spans(text: str):
    """Yield GraphQL bodies, including extended info strings."""
    for start, end, language in markdown_fence_spans(text):
        if language == "graphql":
            yield start, end


def graphql_name_text(body: str) -> str:
    """Mask comments and regular/block strings before scanning GraphQL names."""
    lexical_data = r'"""(?:\\"""|(?!""")[\s\S])*"""|"(?:\\[\s\S]|[^"\\])*"|#[^\r\n]*'
    return re.sub(lexical_data, lambda match: " " * len(match[0]), body)


def masked_graphql_text(text: str, fences) -> str:
    """Mask GraphQL data and comments inside the fences, keeping every offset."""
    parts = []
    cursor = 0
    for start, end in fences:
        parts.extend((text[cursor:start], graphql_name_text(text[start:end])))
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts)


def occurrence_context(position, token, examples):
    """Keep documentary and fenced-example exemptions distinct."""
    for start, end, language in examples:
        if start <= position < end:
            return (language or "code") + ":" + token
    return token


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
        examples = list(markdown_fence_spans(text))
        fences = [(start, end) for start, end, language in examples
                  if (language or "").lower() == "graphql"]
        occurrence_text = masked_graphql_text(text, fences)
        blocks = "\n".join(occurrence_text[start:end] for start, end in fences)
        for identifier in re.findall(r"\b[A-Za-z_]\w*\b", blocks):
            if any(re.match(re.escape(token) + r"\w", identifier)
                   for token in STALE_GRAPHQL_TOKENS):
                raise ValueError("partial stale GraphQL identifier")
        for token in REMAINING_TOKENS:
            if token not in text:
                continue
            for match in re.finditer(r"(?<![\w])" + re.escape(token) + r"(?![\w])", occurrence_text):
                # A documentary exemption cannot authorize a fenced API example.
                context = occurrence_context(match.start(), token, examples)
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
    setter_keys = None if gateway is None else load_setter_keys(gateway)
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
             (root / metrics.DOCUMENT).read_text(), registration, setter_keys)


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
