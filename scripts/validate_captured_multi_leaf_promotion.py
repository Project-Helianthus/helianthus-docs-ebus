#!/usr/bin/env python3
"""Validate and deterministically redact MSP-085-LIVE-R2 campaigns."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

SCRIPT_ROOT = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))
import validate_candidate_fact_graph as candidate_schema  # noqa: E402
import project_candidate_fact_public_status as status_projector  # noqa: E402
import validate_multi_runtime_coexistence as coexistence  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "docs/platform/schemas"
DEFAULT_REGISTRY = SCHEMA_ROOT / "leaf-promotion-captured-multi-leaf-registry-v1.json"
PRIVATE_SCHEMA = SCHEMA_ROOT / "leaf-promotion-captured-multi-leaf-v1.schema.json"
PUBLIC_SCHEMA = SCHEMA_ROOT / "leaf-promotion-captured-multi-leaf-result-v1.schema.json"
M7_GRAPH_SCHEMA = SCHEMA_ROOT / "draft-candidate-fact-graph-v1.schema.json"
M7_STATUS_SCHEMA = SCHEMA_ROOT / "draft-candidate-fact-public-status-v1.schema.json"
M7_REPLAY_SCHEMA = SCHEMA_ROOT / "draft-candidate-fact-replay-v1.schema.json"
M8_EVIDENCE_SCHEMA = SCHEMA_ROOT / "multi-runtime-coexistence-evidence-v1.schema.json"
M8_REGISTRY = SCHEMA_ROOT / "multi-runtime-coexistence-registry-v1.json"

CAMPAIGN_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION:CAPTURED-MULTI-LEAF:V1\x00"
DOSSIER_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION:CAPTURED-DOSSIER:V1\x00"
RESULT_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION:CAPTURED-PUBLIC:V1\x00"
REPLAY_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION:CAPTURED-REPLAY:V1\x00"
SOURCE_PROFILE_DOMAIN = b"HELIANTHUS:EEBUS:SOURCE-PROFILE:V1\x00"
EEBUS_IDENTITY_DOMAIN = b"HELIANTHUS:EEBUS:CAPTURED-IDENTITY:V1\x00"
EBUS_SELECTOR_DOMAIN = b"HELIANTHUS:EBUS:B524-SELECTOR:V1\x00"
RAW_VALUE_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION:RAW-VALUE:V1\x00"
MAPPING_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION:MAPPING:V1\x00"
PROVENANCE_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION:PROVENANCE:V1\x00"
WINDOW_EVIDENCE_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION:CAPTURE-WINDOW:V1\x00"
PROCESS_INSTANCE_DOMAIN = b"HELIANTHUS:LEAF-PROMOTION:PROCESS-INSTANCE:V1\x00"
PINNED_REGISTRY_SHA256 = "sha256:d17a66da1919796f57ecd2a515fa4e538c6be8d00a24c8c7e5d38bce7f36e3cd"
SAFE_INTEGER = 9_007_199_254_740_991
MAX_INPUT_BYTES = 1_048_576
MAX_LIVE_ARTIFACT_BYTES = 16_777_216
MAX_DEPLOYMENT_BINARY_BYTES = 268_435_456
SECRET_MARKERS = re.compile(
    r"(?i)(?:-----BEGIN [^-]*(?:PRIVATE KEY|OPENSSH KEY)-----|"
    r"\b(?:bearer|basic)\s+[A-Za-z0-9+/_.=-]{8,}|"
    r"\b(?:private[_ -]?key|trust[_ -]?store|client[_ -]?secret)\s*[:=])"
)
JWT_TOKEN = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
LONG_ENCODED_SECRET = re.compile(r"^[A-Za-z0-9+/=_-]{160,}$")
RAW_256_BIT_MATERIAL = re.compile(
    r"^(?:[A-Fa-f0-9]{64}|[A-Za-z0-9+/]{43}=|[A-Za-z0-9_-]{43})$"
)
SYNTHETIC_SELECTOR = re.compile(r"(?i)(?:synthetic|fixture|sanitized|placeholder|dummy|opaque)")


class ValidationFailure(Exception):
    def __init__(self, category: str):
        super().__init__(category)
        self.category = category


def fail(category: str) -> None:
    raise ValidationFailure(category)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("json.syntax")
        result[key] = value
    return result


def load_json(
    path: pathlib.Path, *, max_bytes: int = MAX_INPUT_BYTES
) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        if len(raw) > max_bytes or re.search(
            rb"(?<![0-9A-Za-z_])-0(?:[^0-9.]|$)", raw
        ):
            fail("json.syntax")
        text = raw.decode("utf-8", errors="strict")

        def integer(raw_integer: str) -> int:
            value = int(raw_integer)
            if abs(value) > SAFE_INTEGER:
                fail("json.syntax")
            return value

        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_int=integer,
            parse_float=lambda _: fail("json.syntax"),
            parse_constant=lambda _: fail("json.syntax"),
        )
    except ValidationFailure:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail("json.syntax")
    if not isinstance(value, dict):
        fail("json.syntax")
    return value, raw


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for child in value.values() for item in _walk_strings(child)]
    if isinstance(value, list):
        return [item for child in value for item in _walk_strings(child)]
    return []


def reject_secret_material(value: Any) -> None:
    for item in _walk_strings(value):
        compact = re.sub(r"\s+", "", item)
        if (
            SECRET_MARKERS.search(item)
            or JWT_TOKEN.search(item)
            or RAW_256_BIT_MATERIAL.fullmatch(compact)
            or (LONG_ENCODED_SECRET.fullmatch(compact) and not item.startswith("sha256:"))
        ):
            fail("secret.material")


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def json_exact_equal(left: Any, right: Any) -> bool:
    return canonical(left) == canonical(right)


def digest(domain: bytes, value: Any) -> str:
    return "sha256:" + hashlib.sha256(domain + canonical(value)).hexdigest()


def bytes_digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def schema_validate(value: dict[str, Any], path: pathlib.Path, category: str) -> None:
    schema, _ = load_json(path)
    if not candidate_schema._schema_validate(value, schema, schema):
        fail(category)


def decimal_value(value: dict[str, int] | None) -> Decimal | None:
    if value is None:
        return None
    number = value["number"]
    scale = value["scale"]
    return Decimal(number) * (Decimal(10) ** scale)


def timestamp_ns(value: str) -> int:
    match = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,9}))?Z", value
    )
    if match is None:
        fail("window.restart")
    try:
        base = datetime.fromisoformat(match.group(1)).replace(tzinfo=timezone.utc)
    except ValueError:
        fail("window.restart")
    fraction = (match.group(2) or "").ljust(9, "0")
    return int(base.timestamp()) * 1_000_000_000 + int(fraction or "0")


def registry_value(path: pathlib.Path) -> dict[str, Any]:
    registry, raw = load_json(path)
    if bytes_digest(raw) != PINNED_REGISTRY_SHA256:
        fail("registry.binding")
    if (
        registry.get("contract")
        != "helianthus.platform.leaf-promotion-captured-multi-leaf-registry.v1"
        or registry.get("schema_version") != 1
        or len(registry.get("candidate_catalog", [])) != 18
    ):
        fail("registry.binding")
    status_path = ROOT / registry.get("m7_public_status", "")
    status, _ = load_json(status_path)
    projected = [
        {
            "candidate_id": item["candidate_id"],
            "fact_hash": item["fact_hash"],
            "source_status": item["status"],
            "terminal_state": item["terminal_negative_state"],
        }
        for item in status.get("facts", [])
    ]
    catalog_projection = [
        {
            "candidate_id": item["candidate_id"],
            "fact_hash": item["fact_hash"],
            "source_status": item["source_status"],
            "terminal_state": item["terminal_state"],
        }
        for item in registry["candidate_catalog"]
    ]
    if projected != catalog_projection:
        fail("registry.binding")
    return registry


def _typed(value: dict[str, Any], expected: str) -> Any:
    if value["kind"] != expected:
        fail("comparator.invalid")
    populated = [value["decimal"] is not None, value["enum"] is not None, value["boolean"] is not None]
    if sum(populated) != 1:
        fail("comparator.invalid")
    if expected == "NUMERIC":
        return decimal_value(value["decimal"])
    if expected == "ENUM":
        return value["enum"]
    return value["boolean"]


def _validate_sample(
    sample: dict[str, Any],
    source: str,
    window: dict[str, Any],
    *,
    require_valid: bool = True,
    require_generation: bool = True,
    allow_stale: bool = False,
) -> None:
    if sample["source"] != source or (require_valid and not sample["valid"]):
        fail("sample.invalid")
    if sample["raw_hash"] != digest(RAW_VALUE_DOMAIN, sample["raw_value"]):
        fail("raw.binding")
    if sample["value"]["kind"] == "NUMERIC":
        if (
            sample["raw_value"]["kind"] != "NUMERIC"
            or _typed(sample["raw_value"], "NUMERIC")
            != _typed(sample["value"], "NUMERIC")
        ):
            fail("raw.binding")
    observed = timestamp_ns(sample["observed_at"])
    if observed > timestamp_ns(window["ended_at"]) or (
        not allow_stale and observed < timestamp_ns(window["started_at"])
    ):
        fail("sample.invalid")
    if source == "EBUS":
        if (
            sample["poll_id"] is None
            or sample["poll_generation"] is None
            or sample["runtime_epoch"] is not None
            or sample["connection_generation"] is not None
        ):
            fail("sample.invalid")
    else:
        if (
            sample["poll_id"] is not None
            or sample["poll_generation"] is not None
            or sample["runtime_epoch"] is None
            or sample["connection_generation"] is None
        ):
            fail("sample.invalid")
    if require_generation and not _sample_generation_matches(sample, source, window):
        fail("sample.invalid")


def _sample_generation_matches(
    sample: dict[str, Any], source: str, window: dict[str, Any]
) -> bool:
    if sample["capture_generation"] != window["capture_generation"]:
        return False
    if source == "EBUS":
        return sample["poll_generation"] == window["ebus_poll_generation"]
    return (
        sample["runtime_epoch"] == window["eebus_runtime_epoch"]
        and sample["connection_generation"] == window["connection_generation"]
    )


def _converted(value: Decimal, conversion: dict[str, Any]) -> Decimal:
    if conversion["mode"] == "IDENTITY":
        if conversion["source_unit"] != conversion["target_unit"]:
            fail("comparator.invalid")
        if decimal_value(conversion["scale"]) != Decimal(1) or decimal_value(conversion["offset"]) != Decimal(0):
            fail("comparator.invalid")
    return value * decimal_value(conversion["scale"]) + decimal_value(conversion["offset"])


def _numeric_values_in_range(
    expected: dict[str, Any], ebus: dict[str, Any], eebus: dict[str, Any]
) -> tuple[Decimal, Decimal]:
    source = expected["eebus_source"]
    constraints = source["declared_constraints"]
    minimum = decimal_value(constraints["minimum"])
    maximum = decimal_value(constraints["maximum"])
    if minimum is None or maximum is None or minimum > maximum:
        fail("comparator.invalid")
    left = _converted(_typed(ebus["value"], "NUMERIC"), source["conversion"])
    right = _typed(eebus["value"], "NUMERIC")
    if left < minimum or left > maximum or right < minimum or right > maximum:
        fail("comparator.range")
    return left, right


def _numeric_values_are_in_range(
    expected: dict[str, Any], ebus: dict[str, Any], eebus: dict[str, Any]
) -> bool:
    try:
        _numeric_values_in_range(expected, ebus, eebus)
        return True
    except ValidationFailure as exc:
        if exc.category == "comparator.range":
            return False
        raise


def _numeric_sample_is_in_range(
    expected: dict[str, Any], sample: dict[str, Any], sample_source: str
) -> bool:
    constraints = expected["eebus_source"]["declared_constraints"]
    minimum = decimal_value(constraints["minimum"])
    maximum = decimal_value(constraints["maximum"])
    value = _typed(sample["value"], "NUMERIC")
    if sample_source == "EBUS":
        value = _converted(value, expected["eebus_source"]["conversion"])
    return minimum <= value <= maximum


def _expected_mapping_hash(expected: dict[str, Any]) -> str | None:
    source = expected.get("eebus_source")
    if source is None or source.get("mapping_profile") is None:
        return None
    return digest(MAPPING_DOMAIN, source["mapping_profile"])


def _raw_profile_value(value: dict[str, Any]) -> Any:
    kind = value["kind"]
    if kind == "NUMERIC":
        _typed(value, "NUMERIC")
        return value["decimal"]
    if kind == "ENUM":
        return _typed(value, "ENUM")
    if kind == "BOOLEAN":
        return _typed(value, "BOOLEAN")
    fail("comparator.invalid")


def _protocol_raw_value(value: dict[str, Any]) -> Any:
    raw = _raw_profile_value(value)
    if value["kind"] != "NUMERIC":
        return raw
    if raw["scale"] != 0:
        fail("comparator.invalid")
    return raw["number"]


def _protocol_mapping_matches(source: dict[str, Any], sample: dict[str, Any], normalized: Any) -> bool:
    profile = source.get("exact_mapping")
    if not isinstance(profile, dict) or not isinstance(profile.get("pairs"), list):
        return False
    raw = _protocol_raw_value(sample["raw_value"])
    expected = {"raw": raw, "normalized": normalized}
    return any(json_exact_equal(pair, expected) for pair in profile["pairs"])


def _mapping_pair_matches(
    expected: dict[str, Any], ebus: dict[str, Any], eebus: dict[str, Any], normalized: Any
) -> bool:
    profile = expected["eebus_source"]["mapping_profile"]
    if not isinstance(profile, dict) or not isinstance(profile.get("pairs"), list):
        return False
    ebus_raw = _raw_profile_value(ebus["raw_value"])
    eebus_raw = _raw_profile_value(eebus["raw_value"])
    observed = {
        "ebus_raw": ebus_raw,
        "eebus_raw": eebus_raw,
        "normalized": normalized,
    }
    return any(json_exact_equal(pair, observed) for pair in profile["pairs"])


def _catalog_sample_matches(
    expected: dict[str, Any], sample: dict[str, Any], sample_source: str
) -> bool:
    source = expected["eebus_source"]
    comparator_class = expected["comparator_class"]
    if comparator_class == "NUMERIC_DECLARED_GRANULARITY":
        expected_unit = source["conversion"][
            "source_unit" if sample_source == "EBUS" else "target_unit"
        ]
        return sample["value"]["kind"] == "NUMERIC" and sample["unit"] == expected_unit
    expected_kind = "ENUM" if comparator_class == "ENUM_EXACT_MAPPING" else "BOOLEAN"
    if sample["value"]["kind"] != expected_kind or sample["unit"] != source["unit"]:
        return False
    normalized = _typed(sample["value"], expected_kind)
    if sample_source == "EEBUS":
        return _protocol_mapping_matches(source, sample, normalized)
    ebus_raw = _raw_profile_value(sample["raw_value"])
    profile = source["mapping_profile"]
    return any(
        json_exact_equal(pair["ebus_raw"], ebus_raw)
        and json_exact_equal(pair["normalized"], normalized)
        for pair in profile["pairs"]
    )


def _catalog_sample_is_valid(
    expected: dict[str, Any], sample: dict[str, Any], sample_source: str
) -> bool:
    try:
        return _catalog_sample_matches(expected, sample, sample_source)
    except ValidationFailure as exc:
        if exc.category == "comparator.invalid":
            return False
        raise


def _identity_observation(
    assessment: dict[str, Any], candidate: dict[str, Any]
) -> tuple[bool, bool]:
    expected_ebus = candidate["ebus_identity"]["selector_hash"]
    expected_eebus = candidate["eebus_identity"]["identity_hash"]
    observed_ebus = assessment["observed_ebus_identity_hash"]
    observed_eebus = assessment["observed_eebus_identity_hash"]
    if (assessment["ebus_sample"] is None) != (observed_ebus is None):
        fail("identity.binding")
    if (assessment["eebus_sample"] is None) != (observed_eebus is None):
        fail("identity.binding")
    return observed_ebus == expected_ebus, observed_eebus == expected_eebus


def _validate_match(
    assessment: dict[str, Any],
    candidate: dict[str, Any],
    expected: dict[str, Any],
    window: dict[str, Any],
    capture_limits: dict[str, int],
) -> None:
    comparator_class = expected["comparator_class"]
    if _identity_observation(assessment, candidate) != (True, True):
        fail("identity.binding")
    if assessment["conflict_samples"]:
        fail("state.invalid")
    ebus, eebus = _validate_pair(assessment, window, capture_limits)

    comparator = assessment["comparator"]
    if comparator["class"] != comparator_class or comparator["outcome"] != "MATCH":
        fail("comparator.invalid")
    source = expected["eebus_source"]
    if comparator_class == "NUMERIC_DECLARED_GRANULARITY":
        step = decimal_value(comparator["declared_spine_step"])
        if (
            comparator["declared_spine_step"] != source["declared_constraints"]["step"]
            or comparator["conversion"] != source["conversion"]
            or step is None
            or step <= 0
        ):
            fail("comparator.invalid")
        left, right = _numeric_values_in_range(expected, ebus, eebus)
        delta = abs(left - right)
        if decimal_value(comparator["delta"]) != delta or delta > step or comparator["mapping_hash"] is not None:
            fail("comparator.invalid")
        if (
            ebus["unit"] != comparator["conversion"]["source_unit"]
            or eebus["unit"] != comparator["conversion"]["target_unit"]
        ):
            fail("comparator.invalid")
    elif comparator_class == "ENUM_EXACT_MAPPING":
        if (
            comparator["mapping_hash"] != _expected_mapping_hash(expected)
            or comparator["declared_spine_step"] is not None
            or comparator["delta"] is not None
            or comparator["conversion"] is not None
            or ebus["unit"] != source["unit"]
            or eebus["unit"] != source["unit"]
        ):
            fail("comparator.invalid")
        normalized = _typed(ebus["value"], "ENUM")
        if (
            normalized != _typed(eebus["value"], "ENUM")
            or not _protocol_mapping_matches(source, eebus, normalized)
            or not _mapping_pair_matches(expected, ebus, eebus, normalized)
        ):
            fail("comparator.invalid")
    elif comparator_class == "BOOLEAN_EXACT_MAPPING":
        if (
            comparator["mapping_hash"] != _expected_mapping_hash(expected)
            or comparator["declared_spine_step"] is not None
            or comparator["delta"] is not None
            or comparator["conversion"] is not None
            or ebus["unit"] != source["unit"]
            or eebus["unit"] != source["unit"]
        ):
            fail("comparator.invalid")
        normalized = _typed(ebus["value"], "BOOLEAN")
        if (
            normalized != _typed(eebus["value"], "BOOLEAN")
            or not _protocol_mapping_matches(source, eebus, normalized)
            or not _mapping_pair_matches(expected, ebus, eebus, normalized)
        ):
            fail("comparator.invalid")
    else:
        fail("comparator.invalid")


def _validate_pair(
    assessment: dict[str, Any],
    window: dict[str, Any],
    capture_limits: dict[str, int],
) -> tuple[dict[str, Any], dict[str, Any]]:
    ebus = assessment["ebus_sample"]
    eebus = assessment["eebus_sample"]
    if ebus is None or eebus is None:
        fail("comparator.invalid")
    _validate_sample(ebus, "EBUS", window)
    _validate_sample(eebus, "EEBUS", window)
    if (
        assessment["max_skew_ns"] != capture_limits["max_skew_ns"]
        or assessment["max_age_ns"] != capture_limits["max_age_ns"]
    ):
        fail("sample.invalid")
    ebus_ns = timestamp_ns(ebus["observed_at"])
    eebus_ns = timestamp_ns(eebus["observed_at"])
    if (
        assessment["skew_ns"] != abs(ebus_ns - eebus_ns)
        or assessment["skew_ns"] > assessment["max_skew_ns"]
    ):
        fail("sample.invalid")
    age = max(
        timestamp_ns(window["ended_at"]) - ebus_ns,
        timestamp_ns(window["ended_at"]) - eebus_ns,
    )
    if assessment["age_ns"] != age or age > assessment["max_age_ns"]:
        fail("sample.invalid")
    return ebus, eebus


def _validate_ebus_identity(
    identity: dict[str, Any],
    selector: dict[str, Any],
    windows: list[dict[str, Any]],
) -> None:
    if any(identity.get(key) != value for key, value in selector.items()):
        fail("identity.binding")
    if any(identity["source_address"] != window["admitted_source"] for window in windows):
        fail("identity.binding")
    selector_payload = {key: value for key, value in identity.items() if key != "selector_hash"}
    if identity["selector_hash"] != digest(EBUS_SELECTOR_DOMAIN, selector_payload):
        fail("identity.binding")


def _validate_eebus_identity(identity: dict[str, Any], source: dict[str, Any]) -> None:
    if any(identity.get(key) != value for key, value in source.items()):
        fail("identity.binding")
    if identity["source_profile_hash"] != digest(SOURCE_PROFILE_DOMAIN, source):
        fail("identity.binding")
    identity_payload = {key: value for key, value in identity.items() if key != "identity_hash"}
    if identity["identity_hash"] != digest(EEBUS_IDENTITY_DOMAIN, identity_payload):
        fail("identity.binding")


def _validate_non_match_assessment(
    assessment: dict[str, Any],
    candidate: dict[str, Any],
    expected: dict[str, Any],
    window: dict[str, Any],
    capture_limits: dict[str, int],
) -> None:
    comparator = assessment["comparator"]
    source = expected["eebus_source"]
    if comparator["class"] != expected["comparator_class"]:
        fail("comparator.invalid")
    if (
        assessment["max_skew_ns"] != capture_limits["max_skew_ns"]
        or assessment["max_age_ns"] != capture_limits["max_age_ns"]
    ):
        fail("sample.invalid")
    if expected["comparator_class"] == "NUMERIC_DECLARED_GRANULARITY":
        if (
            comparator["declared_spine_step"] != source["declared_constraints"]["step"]
            or comparator["conversion"] != source["conversion"]
            or comparator["mapping_hash"] is not None
        ):
            fail("comparator.invalid")
    elif expected["comparator_class"] in {"ENUM_EXACT_MAPPING", "BOOLEAN_EXACT_MAPPING"}:
        if (
            comparator["declared_spine_step"] is not None
            or comparator["delta"] is not None
            or comparator["conversion"] is not None
            or comparator["mapping_hash"] != _expected_mapping_hash(expected)
        ):
            fail("comparator.invalid")
    else:
        fail("comparator.invalid")

    ebus = assessment["ebus_sample"]
    eebus = assessment["eebus_sample"]
    if ebus is None or eebus is None:
        if (
            comparator["outcome"] != "MISSING"
            or assessment["skew_ns"] is not None
            or assessment["age_ns"] is not None
            or comparator["delta"] is not None
            or assessment["conflict_samples"]
        ):
            fail("state.invalid")
        identity_matches = _identity_observation(assessment, candidate)
        if ebus is not None:
            _validate_sample(ebus, "EBUS", window)
            if not identity_matches[0] or not _catalog_sample_matches(expected, ebus, "EBUS"):
                fail("comparator.invalid")
        if eebus is not None:
            _validate_sample(eebus, "EEBUS", window)
            if not identity_matches[1] or not _catalog_sample_matches(expected, eebus, "EEBUS"):
                fail("comparator.invalid")
        return

    _validate_sample(
        ebus, "EBUS", window, require_valid=False, require_generation=False, allow_stale=True
    )
    _validate_sample(
        eebus, "EEBUS", window, require_valid=False, require_generation=False, allow_stale=True
    )
    ebus_ns = timestamp_ns(ebus["observed_at"])
    eebus_ns = timestamp_ns(eebus["observed_at"])
    skew = abs(ebus_ns - eebus_ns)
    age = max(
        timestamp_ns(window["ended_at"]) - ebus_ns,
        timestamp_ns(window["ended_at"]) - eebus_ns,
    )
    if assessment["skew_ns"] != skew or skew > assessment["max_skew_ns"]:
        fail("sample.invalid")
    if assessment["age_ns"] != age:
        fail("sample.invalid")

    identity_matches = _identity_observation(assessment, candidate)
    generations_match = _sample_generation_matches(
        ebus, "EBUS", window
    ) and _sample_generation_matches(eebus, "EEBUS", window)
    catalog_matches = _catalog_sample_is_valid(
        expected, ebus, "EBUS"
    ) and _catalog_sample_is_valid(expected, eebus, "EEBUS")
    values_in_range = True
    if expected["comparator_class"] == "NUMERIC_DECLARED_GRANULARITY" and catalog_matches:
        values_in_range = _numeric_values_are_in_range(expected, ebus, eebus)
    invalid = not ebus["valid"] or not eebus["valid"] or not catalog_matches or not values_in_range
    stale = age > assessment["max_age_ns"]
    conflict = _validate_conflict_samples(
        assessment, candidate, expected, window, capture_limits
    )

    mismatch = False
    computed_delta: Decimal | None = None
    if not invalid:
        if expected["comparator_class"] == "NUMERIC_DECLARED_GRANULARITY":
            left, right = _numeric_values_in_range(expected, ebus, eebus)
            computed_delta = abs(left - right)
            mismatch = computed_delta > decimal_value(comparator["declared_spine_step"])
        else:
            expected_kind = (
                "ENUM"
                if expected["comparator_class"] == "ENUM_EXACT_MAPPING"
                else "BOOLEAN"
            )
            mismatch = _typed(ebus["value"], expected_kind) != _typed(
                eebus["value"], expected_kind
            )

    if identity_matches != (True, True):
        computed = "IDENTITY_MISMATCH"
    elif not generations_match:
        computed = "GENERATION_CHANGED"
    elif invalid:
        computed = "INVALID"
    elif stale:
        computed = "STALE"
    elif conflict:
        computed = "CONFLICT"
    elif mismatch:
        computed = "MISMATCH"
    else:
        computed = "MATCH"
    if comparator["outcome"] != computed or computed == "MATCH":
        fail("state.invalid")
    if expected["comparator_class"] == "NUMERIC_DECLARED_GRANULARITY":
        if computed == "MISMATCH":
            if decimal_value(comparator["delta"]) != computed_delta:
                fail("comparator.invalid")
        elif comparator["delta"] is not None:
            fail("comparator.invalid")


def _validate_conflict_samples(
    assessment: dict[str, Any],
    candidate: dict[str, Any],
    expected: dict[str, Any],
    window: dict[str, Any],
    capture_limits: dict[str, int],
) -> bool:
    samples = assessment["conflict_samples"]
    if not samples:
        return False
    if len(samples) != 2 or samples[0]["source"] != samples[1]["source"]:
        fail("conflict.invalid")
    source = samples[0]["source"]
    source_key = "EBUS" if source == "EBUS" else "EEBUS"
    identity_index = 0 if source_key == "EBUS" else 1
    if not _identity_observation(assessment, candidate)[identity_index]:
        fail("identity.binding")
    for sample in samples:
        _validate_sample(sample, source_key, window)
        if not _catalog_sample_is_valid(expected, sample, source_key):
            fail("conflict.invalid")
        if (
            expected["comparator_class"] == "NUMERIC_DECLARED_GRANULARITY"
            and not _numeric_sample_is_in_range(expected, sample, source_key)
        ):
            fail("conflict.invalid")
        age = timestamp_ns(window["ended_at"]) - timestamp_ns(sample["observed_at"])
        if age > capture_limits["max_age_ns"]:
            fail("conflict.invalid")
    conflict_skew = abs(
        timestamp_ns(samples[0]["observed_at"])
        - timestamp_ns(samples[1]["observed_at"])
    )
    comparator_class = expected["comparator_class"]
    if comparator_class == "NUMERIC_DECLARED_GRANULARITY":
        same_value = _typed(samples[0]["value"], "NUMERIC") == _typed(
            samples[1]["value"], "NUMERIC"
        )
    elif comparator_class == "ENUM_EXACT_MAPPING":
        same_value = _typed(samples[0]["value"], "ENUM") == _typed(
            samples[1]["value"], "ENUM"
        )
    elif comparator_class == "BOOLEAN_EXACT_MAPPING":
        same_value = _typed(samples[0]["value"], "BOOLEAN") == _typed(
            samples[1]["value"], "BOOLEAN"
        )
    else:
        fail("conflict.invalid")
    if conflict_skew > capture_limits["max_skew_ns"] or same_value:
        fail("conflict.invalid")
    return True


def _derived_terminal(outcomes: list[str]) -> str | None:
    for outcome in outcomes:
        if outcome != "MATCH":
            if outcome in {"NOT_EVALUATED", "NOT_COMPARABLE"}:
                fail("state.invalid")
            return outcome
    return None


def _candidate_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in candidate.items() if key != "dossier_hash"}


def replay_hash(value: dict[str, Any]) -> str:
    bindings = {
        key: item
        for key, item in value["source_bindings"].items()
        if key != "replay_hash"
    }
    return digest(
        REPLAY_DOMAIN,
        {
            "source_bindings": bindings,
            "windows": value["windows"],
            "candidates": value["candidates"],
        },
    )


def _read_bounded_bytes(path: pathlib.Path, maximum: int, category: str) -> bytes:
    try:
        raw = path.read_bytes()
    except OSError:
        fail(category)
    if not raw or len(raw) > maximum:
        fail(category)
    return raw


def _process_instance_hash(process_instance_id: str) -> str:
    return digest(
        PROCESS_INSTANCE_DOMAIN, {"process_instance_id": process_instance_id}
    )


def _immutable_input(run: dict[str, Any], input_id: str) -> dict[str, Any]:
    matches = [
        item
        for item in run["provenance"]["immutable_inputs"]
        if item["input_id"] == input_id
    ]
    if len(matches) != 1:
        fail("live.sources.binding")
    return matches[0]


def _validate_live_cross_bindings(
    value: dict[str, Any],
    graph: dict[str, Any],
    graph_raw: bytes,
    replay: dict[str, Any],
    replay_raw: bytes,
    status: dict[str, Any],
    status_raw: bytes,
    evidence: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    m7_binding = {
        "source_commit": status["source_commit"],
        "docs_source_commit": status["docs_source_commit"],
        "graph_contract": graph["contract"],
        "graph_id": graph["graph_id"],
        "graph_hash": graph["graph_hash"],
        "replay_contract": replay["contract"],
        "replay_id": replay["replay_id"],
        "replay_hash": replay["replay_hash"],
    }
    if any(evidence["m7_binding"].get(key) != item for key, item in m7_binding.items()):
        fail("live.sources.binding")
    expected_live_status = {
        "contract": status["contract"],
        "projection_id": status["projection_id"],
        "projection_hash": status["projection_hash"],
        "content_hash": bytes_digest(status_raw),
        "source_graph_id": status["source_graph_id"],
        "source_graph_hash": status["source_graph_hash"],
        "source_replay_id": status["source_replay_id"],
        "source_replay_hash": status["source_replay_hash"],
    }
    if (
        status["source_graph_id"] != graph["graph_id"]
        or status["source_graph_hash"] != graph["graph_hash"]
        or status["source_replay_id"] != replay["replay_id"]
        or status["source_replay_hash"] != replay["replay_hash"]
        or evidence["m7_live_status"] != expected_live_status
    ):
        fail("live.sources.binding")
    expected_report_m7 = {
        "source_commit": status["source_commit"],
        "docs_source_commit": status["docs_source_commit"],
        "graph_id": graph["graph_id"],
        "graph_hash": graph["graph_hash"],
        "replay_id": replay["replay_id"],
        "replay_hash": replay["replay_hash"],
        "live_status_projection_id": status["projection_id"],
        "live_status_projection_hash": status["projection_hash"],
    }
    if report["m7_binding"] != expected_report_m7:
        fail("live.sources.binding")

    expected_inputs = {
        "m7:private-graph": (bytes_digest(graph_raw), len(graph_raw)),
        "m7:private-replay": (bytes_digest(replay_raw), len(replay_raw)),
        "m7:status-projection": (bytes_digest(status_raw), len(status_raw)),
    }
    for run in evidence["runs"]:
        for input_id, (input_digest, byte_length) in expected_inputs.items():
            item = _immutable_input(run, input_id)
            if item["digest"] != input_digest or item["byte_length"] != byte_length:
                fail("live.sources.binding")

    transition_runs = [
        run
        for run in evidence["runs"]
        if run["state_evidence"]["restart_transition"] is not None
    ]
    restart_runs = [
        run for run in evidence["runs"] if run["state"] == "EEBUS_RESTART_PERSISTED"
    ]
    if (
        len(transition_runs) != 1
        or transition_runs != restart_runs
        or transition_runs[0]["state_evidence"]["outcome"] != "RESTART_PERSISTED"
    ):
        fail("live.restart.binding")
    restart_run = transition_runs[0]
    transition = restart_run["state_evidence"]["restart_transition"]
    before_runs = [
        run
        for run in evidence["runs"]
        if run["state"] == "EEBUS_CONNECTED_RAW_WITHHELD"
        and run["provenance"]["process_instance_id"]
        == transition["before_process_instance_id"]
    ]
    if (
        len(before_runs) != 1
        or restart_run["provenance"]["process_instance_id"]
        != transition["after_process_instance_id"]
    ):
        fail("live.restart.binding")
    before_run = before_runs[0]
    windows = value["windows"]
    expected_window_bindings = (
        {
            "process_instance_hash": _process_instance_hash(
                transition["before_process_instance_id"]
            ),
            "trust_state_hash": transition["before_trust_state_hash"],
            "peer_binding_hash": transition["before_peer_binding_hash"],
        },
        {
            "process_instance_hash": _process_instance_hash(
                transition["after_process_instance_id"]
            ),
            "trust_state_hash": transition["after_trust_state_hash"],
            "peer_binding_hash": transition["after_peer_binding_hash"],
        },
    )
    for window, expected in zip(windows, expected_window_bindings, strict=True):
        if any(window[key] != item for key, item in expected.items()):
            fail("live.restart.binding")

    runtime = restart_run["provenance"]["runtime"]
    if (
        any(
            run["provenance"]["runtime"] != runtime
            for run in evidence["runs"][1:]
        )
        or runtime["source_parent_commit"] != status["source_commit"]
        or runtime["artifact_id"] != "gateway:" + runtime["artifact_digest"]
    ):
        fail("live.deployment")
    return {
        "m7_binding": {
            "graph_id": graph["graph_id"],
            "graph_hash": graph["graph_hash"],
            "replay_id": replay["replay_id"],
            "replay_hash": replay["replay_hash"],
            "status_id": status["projection_id"],
            "status_hash": status["projection_hash"],
            "source_commit": status["source_commit"],
            "docs_source_commit": status["docs_source_commit"],
        },
        "m8_binding": {
            "evidence_id": evidence["evidence_id"],
            "evidence_hash": evidence["evidence_hash"],
            "report_id": report["report_id"],
            "report_hash": report["report_hash"],
        },
        "deployment_binding": {
            "source_commit": runtime["source_commit"],
            "binary_hash": runtime["artifact_digest"],
        },
        "runtime": runtime,
        "window_runs": (before_run, restart_run),
        "transition": transition,
    }


def _validate_capture_receipts(
    value: dict[str, Any],
    receipt_paths: list[pathlib.Path],
    live_context: dict[str, Any],
) -> None:
    if len(receipt_paths) != 2:
        fail("live.receipt")
    windows = value["windows"]
    observed: list[str] = []
    transition = live_context["transition"]
    process_hashes = (
        _process_instance_hash(transition["before_process_instance_id"]),
        _process_instance_hash(transition["after_process_instance_id"]),
    )
    for index, (path, window, run) in enumerate(
        zip(receipt_paths, windows, live_context["window_runs"], strict=True)
    ):
        receipt, raw = load_json(path)
        if set(receipt) != {
            "contract",
            "capture_campaign_id",
            "window_id",
            "phase",
            "capture_generation",
            "process_instance_hash",
            "local_identity_hash",
            "trust_state_hash",
            "peer_binding_hash",
            "admitted_source",
            "window_evidence_hash",
            "m8_run_id",
            "m7_binding",
            "m8_binding",
            "deployment_binding",
            "captured_at",
            "restart_event",
        } or receipt["contract"] != "helianthus.platform.leaf-promotion-capture-receipt.v1":
            fail("live.receipt")
        reject_secret_material(receipt)
        if (
            receipt["capture_campaign_id"]
            != value["provenance"]["capture_campaign_id"]
            or any(
                receipt[key] != window[key]
                for key in (
                    "window_id",
                    "phase",
                    "capture_generation",
                    "process_instance_hash",
                    "local_identity_hash",
                    "trust_state_hash",
                    "peer_binding_hash",
                    "admitted_source",
                )
            )
            or receipt["window_evidence_hash"]
            != digest(WINDOW_EVIDENCE_DOMAIN, window)
            or receipt["m8_run_id"] != run["run_id"]
            or receipt["m7_binding"] != live_context["m7_binding"]
            or receipt["m8_binding"] != live_context["m8_binding"]
            or receipt["deployment_binding"]
            != live_context["deployment_binding"]
        ):
            fail("live.receipt")
        expected_restart = None
        if index == 1:
            expected_restart = {
                "event_type": "HA_ADDON_RESTART_COMPLETED",
                "event_id": transition["event_id"],
                "outcome": "COMPLETED",
                "before_process_instance_hash": process_hashes[0],
                "after_process_instance_hash": process_hashes[1],
            }
            restart_event = receipt["restart_event"]
            if (
                not isinstance(restart_event, dict)
                or set(restart_event) != set(expected_restart) | {"completed_at"}
                or any(
                    restart_event[key] != item
                    for key, item in expected_restart.items()
                )
                or timestamp_ns(restart_event["completed_at"])
                <= timestamp_ns(windows[0]["ended_at"])
                or timestamp_ns(restart_event["completed_at"])
                >= timestamp_ns(windows[1]["started_at"])
            ):
                fail("live.receipt")
        elif receipt["restart_event"] is not None:
            fail("live.receipt")
        captured_at = timestamp_ns(receipt["captured_at"])
        if captured_at < timestamp_ns(window["started_at"]) or captured_at > timestamp_ns(
            window["ended_at"]
        ):
            fail("live.receipt")
        observed.append(bytes_digest(raw))
    if value["provenance"]["capture_receipts"] != observed:
        fail("live.receipt")


def _validate_deployment_source(
    value: dict[str, Any],
    source_path: pathlib.Path,
    binary_path: pathlib.Path,
    live_context: dict[str, Any],
) -> None:
    source, source_raw = load_json(source_path)
    binary_raw = _read_bounded_bytes(
        binary_path, MAX_DEPLOYMENT_BINARY_BYTES, "live.deployment"
    )
    expected_binary = bytes_digest(binary_raw)
    if set(source) != {"contract", "source_commit", "binary_hash"} or source.get(
        "contract"
    ) != "helianthus.platform.deployment-source-receipt.v1":
        fail("live.deployment")
    reject_secret_material(source)
    provenance = value["provenance"]
    runtime = live_context["runtime"]
    if (
        source["source_commit"] != provenance["deployment_source_commit"]
        or source["source_commit"] != runtime["source_commit"]
        or source["binary_hash"] != expected_binary
        or source["binary_hash"] != runtime["artifact_digest"]
        or len(binary_raw) != runtime["artifact_size_bytes"]
        or provenance["deployment_binary_hash"] != expected_binary
        or provenance["deployment_source_hash"] != bytes_digest(source_raw)
    ):
        fail("live.deployment")


def _validate_non_synthetic_selectors(value: dict[str, Any]) -> None:
    for candidate in value["candidates"]:
        ebus = candidate["ebus_identity"]
        eebus = candidate["eebus_identity"]
        selectors: list[str] = []
        if ebus is not None:
            selectors.extend((ebus["target_pseudonym"], ebus["unit_scale_source"]))
        if eebus is not None:
            selectors.extend(
                (
                    eebus["service_id"],
                    eebus["device_address"],
                    eebus["entity_slot"],
                    eebus["field_path"],
                )
            )
        if any(SYNTHETIC_SELECTOR.search(selector) for selector in selectors):
            fail("live.selector")


def _validate_live_source_bundle(
    value: dict[str, Any],
    registry: dict[str, Any],
    live_sources: dict[str, pathlib.Path | list[pathlib.Path]],
) -> None:
    required = {
        "m7_graph",
        "m7_status",
        "m7_replay",
        "m8_evidence",
        "m8_report",
        "capture_receipts",
        "deployment_source",
        "deployment_binary",
    }
    if set(live_sources) != required:
        fail("live.sources.required")
    artifacts: dict[str, dict[str, Any]] = {}
    raw_artifacts: dict[str, bytes] = {}
    for name in ("m7_graph", "m7_status", "m7_replay", "m8_evidence", "m8_report"):
        path = live_sources[name]
        if not isinstance(path, pathlib.Path):
            fail("live.sources.required")
        artifacts[name], raw_artifacts[name] = load_json(
            path, max_bytes=MAX_LIVE_ARTIFACT_BYTES
        )
    schema_validate(artifacts["m7_graph"], M7_GRAPH_SCHEMA, "live.m7")
    schema_validate(artifacts["m7_status"], M7_STATUS_SCHEMA, "live.m7")
    schema_validate(artifacts["m7_replay"], M7_REPLAY_SCHEMA, "live.m7")
    schema_validate(artifacts["m8_evidence"], M8_EVIDENCE_SCHEMA, "live.m8")
    graph = artifacts["m7_graph"]
    replay = artifacts["m7_replay"]
    status = artifacts["m7_status"]
    try:
        candidate_schema.check_hashes(graph)
        if candidate_schema.replay(graph) != replay:
            fail("live.m7")
        projected = status_projector.project(
            graph, replay, status["source_commit"], status["docs_source_commit"]
        )
    except (candidate_schema.Failure, status_projector.Failure, KeyError, TypeError, ValueError):
        fail("live.m7")
    if projected != status:
        fail("live.m7")
    expected_facts = [
        {
            "candidate_id": item["candidate_id"],
            "status": item["source_status"],
            "terminal_negative_state": item["terminal_state"],
            "fact_hash": item["fact_hash"],
        }
        for item in registry["candidate_catalog"]
    ]
    if status["facts"] != expected_facts:
        fail("live.m7")

    evidence = artifacts["m8_evidence"]
    report = artifacts["m8_report"]
    m8_registry, m8_registry_raw = load_json(M8_REGISTRY)
    try:
        coexistence.check_limits(evidence, len(raw_artifacts["m8_evidence"]))
        coexistence.check_registry(evidence, m8_registry, m8_registry_raw)
        coexistence.check_config(evidence)
        coexistence.check_auth_mask(evidence)
        coexistence.check_clock(evidence)
        coexistence.check_ordering(evidence, m8_registry)
        coexistence.check_states(evidence, {"facts": status["facts"]})
        coexistence.check_restart(evidence)
        coexistence.check_view_coverage(evidence, m8_registry)
        coexistence.check_normalization(evidence, m8_registry)
        coexistence.check_payload_hashes(evidence, m8_registry)
        coexistence.check_public_redaction(evidence)
        coexistence.check_authority(evidence)
        coexistence.check_scope(evidence, m8_registry)
        coexistence.check_drift(evidence, m8_registry)
        coexistence.check_rollback(evidence, m8_registry)
        coexistence.check_evidence_hash(evidence)
        derived_report = coexistence.report(copy.deepcopy(evidence), m8_registry)
    except (coexistence.Failure, KeyError, TypeError, ValueError):
        fail("live.m8")
    if (
        evidence["evidence_class"] != "CAPTURED_RUNTIME_EVIDENCE"
        or not evidence["scope"]["live_vr940_claim"]
        or report != derived_report
        or report["verdict"] != "PASS"
        or not report["rollback"]["exact_baseline_restored"]
    ):
        fail("live.m8")

    bindings = value["source_bindings"]
    expected_bindings = {
        "m7_graph_id": graph["graph_id"],
        "m7_graph_hash": graph["graph_hash"],
        "m7_replay_id": replay["replay_id"],
        "m7_replay_hash": replay["replay_hash"],
        "m7_status_id": status["projection_id"],
        "m7_status_hash": status["projection_hash"],
        "m8_evidence_id": evidence["evidence_id"],
        "m8_evidence_hash": evidence["evidence_hash"],
        "m8_report_id": report["report_id"],
        "m8_report_hash": report["report_hash"],
    }
    for name in ("m7_graph", "m7_status", "m7_replay", "m8_evidence", "m8_report"):
        expected_bindings[name + "_bytes_hash"] = bytes_digest(raw_artifacts[name])
    if any(bindings.get(key) != expected for key, expected in expected_bindings.items()):
        fail("live.sources.binding")
    live_context = _validate_live_cross_bindings(
        value,
        graph,
        raw_artifacts["m7_graph"],
        replay,
        raw_artifacts["m7_replay"],
        status,
        raw_artifacts["m7_status"],
        evidence,
        report,
    )
    receipt_paths = live_sources["capture_receipts"]
    if not isinstance(receipt_paths, list) or not all(
        isinstance(path, pathlib.Path) for path in receipt_paths
    ):
        fail("live.sources.required")
    deployment_source = live_sources["deployment_source"]
    deployment_binary = live_sources["deployment_binary"]
    if not isinstance(deployment_source, pathlib.Path) or not isinstance(
        deployment_binary, pathlib.Path
    ):
        fail("live.sources.required")
    _validate_deployment_source(
        value, deployment_source, deployment_binary, live_context
    )
    _validate_capture_receipts(value, receipt_paths, live_context)
    _validate_non_synthetic_selectors(value)


def verify_private(
    value: dict[str, Any],
    registry: dict[str, Any],
    live_sources: dict[str, pathlib.Path | list[pathlib.Path]] | None = None,
) -> None:
    reject_secret_material(value)
    schema_validate(value, PRIVATE_SCHEMA, "schema.private")
    if (
        value["source_bindings"]["registry_sha256"] != PINNED_REGISTRY_SHA256
        or value["source_bindings"]["docs_eebus_commit"]
        != registry["docs_eebus_source_commit"]
    ):
        fail("registry.binding")
    provenance = value["provenance"]
    if provenance["class"] != value["evidence_mode"]:
        fail("provenance.binding")
    if value["evidence_mode"] == "SANITIZED_CONFORMANCE":
        if provenance != registry["sanitized_provenance"]:
            fail("provenance.binding")
        if live_sources is not None:
            fail("live.sources.unexpected")
    elif (
        provenance["fixture_id"] is not None
        or provenance["generator"] is not None
        or provenance["capture_campaign_id"] is None
        or len(provenance["capture_receipts"]) != 2
        or provenance["deployment_source_commit"] is None
        or provenance["deployment_source_hash"] is None
        or provenance["deployment_binary_hash"] is None
    ):
        fail("provenance.binding")

    windows = value["windows"]
    capture_limits = registry.get("capture_limits")
    if (
        not isinstance(capture_limits, dict)
        or set(capture_limits) != {"max_skew_ns", "max_age_ns"}
        or any(
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or limit <= 0
            or limit > SAFE_INTEGER
            for limit in capture_limits.values()
        )
    ):
        fail("candidate.catalog")
    if [window["phase"] for window in windows] != registry["window_phases"]:
        fail("window.restart")
    if len({window["window_id"] for window in windows}) != 2:
        fail("window.restart")
    for window in windows:
        if timestamp_ns(window["started_at"]) >= timestamp_ns(window["ended_at"]):
            fail("window.restart")
    if timestamp_ns(windows[0]["ended_at"]) >= timestamp_ns(windows[1]["started_at"]):
        fail("window.restart")
    if (
        windows[0]["process_instance_hash"] == windows[1]["process_instance_hash"]
        or windows[0]["local_identity_hash"] != windows[1]["local_identity_hash"]
        or windows[0]["trust_state_hash"] != windows[1]["trust_state_hash"]
        or windows[0]["peer_binding_hash"] != windows[1]["peer_binding_hash"]
        or windows[0]["admitted_source"] != windows[1]["admitted_source"]
    ):
        fail("window.restart")

    catalog = registry["candidate_catalog"]
    if [item["candidate_id"] for item in value["candidates"]] != [
        item["candidate_id"] for item in catalog
    ]:
        fail("candidate.catalog")
    window_ids = [window["window_id"] for window in windows]
    window_by_id = {window["window_id"]: window for window in windows}
    ebus_peer: tuple[Any, ...] | None = None
    for candidate, expected in zip(value["candidates"], catalog, strict=True):
        for field in (
            "candidate_id",
            "fact_hash",
            "source_status",
            "semantic_path",
            "comparator_class",
        ):
            if candidate[field] != expected[field]:
                fail("candidate.catalog")

        if expected["protocol_eligibility"] == "TERMINAL":
            if (
                candidate["decision"] != "WITHHELD"
                or candidate["terminal_state"] != expected["terminal_state"]
                or candidate["visibility"] != "RAW_DEBUG_ONLY"
                or candidate["ebus_identity"] is not None
                or candidate["eebus_identity"] is not None
                or candidate["assessments"]
                or candidate["dossier_hash"] is not None
            ):
                fail("candidate.catalog")
            continue

        source = expected["eebus_source"]
        if source is None or candidate["eebus_identity"] is None:
            fail("identity.binding")
        _validate_eebus_identity(candidate["eebus_identity"], source)

        if expected["protocol_eligibility"] == "WITHHOLD_NO_EBUS_CAPABILITY_SOURCE":
            if (
                expected["ebus_selector"] is not None
                or candidate["decision"] != "WITHHELD"
                or candidate["terminal_state"] != "NOT_COMPARABLE"
                or candidate["visibility"] != "RAW_DEBUG_ONLY"
                or candidate["assessments"]
                or candidate["ebus_identity"] is not None
                or candidate["dossier_hash"] is not None
            ):
                fail("candidate.catalog")
            continue

        selector = expected["ebus_selector"]
        if selector is None or candidate["ebus_identity"] is None:
            fail("identity.binding")
        _validate_ebus_identity(candidate["ebus_identity"], selector, windows)
        peer = tuple(
            candidate["ebus_identity"][key]
            for key in ("target_pseudonym", "target_address", "source_address")
        )
        if ebus_peer is None:
            ebus_peer = peer
        elif peer != ebus_peer:
            fail("identity.binding")

        assessments = candidate["assessments"]
        if len(assessments) != 2 or [item["window_id"] for item in assessments] != window_ids:
            fail("state.invalid")
        outcomes = [assessment["comparator"]["outcome"] for assessment in assessments]
        for assessment in assessments:
            window = window_by_id[assessment["window_id"]]
            if assessment["comparator"]["outcome"] == "MATCH":
                _validate_match(assessment, candidate, expected, window, capture_limits)
            else:
                _validate_non_match_assessment(
                    assessment, candidate, expected, window, capture_limits
                )

        terminal = _derived_terminal(outcomes)
        if terminal is None:
            if (
                candidate["decision"] != "PROMOTED"
                or candidate["terminal_state"] is not None
                or candidate["visibility"] != "LOCKED_NOT_EXPOSED"
                or candidate["dossier_hash"]
                != digest(DOSSIER_DOMAIN, _candidate_payload(candidate))
            ):
                fail("state.invalid")
        elif (
            candidate["decision"] != "WITHHELD"
            or candidate["terminal_state"] != terminal
            or candidate["visibility"] != "RAW_DEBUG_ONLY"
            or candidate["dossier_hash"] is not None
        ):
            fail("state.invalid")

    if value["source_bindings"]["replay_hash"] != replay_hash(value):
        fail("hash.replay")
    expected_hash = digest(
        CAMPAIGN_DOMAIN,
        {key: item for key, item in value.items() if key != "campaign_hash"},
    )
    if value["campaign_hash"] != expected_hash:
        fail("hash.campaign")
    if value["evidence_mode"] == "LIVE_CAPTURE":
        if live_sources is None:
            fail("live.sources.required")
        _validate_live_source_bundle(value, registry, live_sources)


def _build_public(value: dict[str, Any], private_raw: bytes) -> dict[str, Any]:
    results = [
        {
            "candidate_id": candidate["candidate_id"],
            "fact_hash": candidate["fact_hash"],
            "decision": candidate["decision"],
            "terminal_state": candidate["terminal_state"],
            "visibility": candidate["visibility"],
            "dossier_hash": candidate["dossier_hash"],
            "window_outcomes": [assessment["comparator"]["outcome"] for assessment in candidate["assessments"]],
        }
        for candidate in value["candidates"]
    ]
    promoted = sum(item["decision"] == "PROMOTED" for item in results)
    if value["evidence_mode"] == "SANITIZED_CONFORMANCE":
        gate = "BLOCKED_CONFORMANCE_ONLY"
        verdict = "VALID_SUBSET_PROMOTION_CONFORMANCE"
    elif promoted:
        gate = "READY_FOR_M9_PLANNING"
        verdict = "VALID_PROMOTION_LOCK"
    else:
        gate = "BLOCKED_ZERO_PROMOTED_LEAVES"
        verdict = "VALID_ZERO_PROMOTION"
    public: dict[str, Any] = {
        "contract": "helianthus.platform.leaf-promotion-captured-multi-leaf-result.v1",
        "schema_version": 1,
        "profile": "CAPTURED_RUNTIME_MULTI_LEAF_V1",
        "evidence_mode": value["evidence_mode"],
        "export_tier": "PUBLIC_REDACTED",
        "provenance": {
            "class": value["provenance"]["class"],
            "binding_hash": digest(PROVENANCE_DOMAIN, value["provenance"]),
        },
        "source_bindings": {
            "registry_sha256": value["source_bindings"]["registry_sha256"],
            "docs_eebus_commit": value["source_bindings"]["docs_eebus_commit"],
            "m7_graph_hash": value["source_bindings"]["m7_graph_hash"],
            "m7_graph_bytes_hash": value["source_bindings"]["m7_graph_bytes_hash"],
            "m7_replay_hash": value["source_bindings"]["m7_replay_hash"],
            "m7_replay_bytes_hash": value["source_bindings"]["m7_replay_bytes_hash"],
            "m7_status_hash": value["source_bindings"]["m7_status_hash"],
            "m7_status_bytes_hash": value["source_bindings"]["m7_status_bytes_hash"],
            "m8_evidence_hash": value["source_bindings"]["m8_evidence_hash"],
            "m8_evidence_bytes_hash": value["source_bindings"]["m8_evidence_bytes_hash"],
            "m8_report_hash": value["source_bindings"]["m8_report_hash"],
            "m8_report_bytes_hash": value["source_bindings"]["m8_report_bytes_hash"],
            "replay_hash": value["source_bindings"]["replay_hash"],
            "campaign_hash": value["campaign_hash"],
            "private_campaign_bytes_hash": bytes_digest(private_raw),
        },
        "counts": {"total": 18, "promoted": promoted, "withheld": 18 - promoted},
        "candidate_results": results,
        "m9_consumer_gate": gate,
        "verdict": verdict,
        "result_hash": "sha256:" + "0" * 64,
    }
    public["result_hash"] = digest(
        RESULT_DOMAIN,
        {key: item for key, item in public.items() if key != "result_hash"},
    )
    return public


def derive_public(
    value: dict[str, Any],
    registry: dict[str, Any],
    private_raw: bytes,
    live_sources: dict[str, pathlib.Path | list[pathlib.Path]] | None = None,
) -> dict[str, Any]:
    verify_private(value, registry, live_sources)
    public = _build_public(value, private_raw)
    _verify_public_structure(public, registry)
    return public


def _walk_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key.lower())
            keys.extend(_walk_keys(item))
        return keys
    if isinstance(value, list):
        return [key for item in value for key in _walk_keys(item)]
    return []


def _verify_public_structure(value: dict[str, Any], registry: dict[str, Any]) -> None:
    reject_secret_material(value)
    schema_validate(value, PUBLIC_SCHEMA, "schema.public")
    catalog = registry["candidate_catalog"]
    if (
        value["source_bindings"]["registry_sha256"] != PINNED_REGISTRY_SHA256
        or value["source_bindings"]["docs_eebus_commit"]
        != registry["docs_eebus_source_commit"]
    ):
        fail("registry.binding")
    if [item["candidate_id"] for item in value["candidate_results"]] != [
        item["candidate_id"] for item in catalog
    ]:
        fail("candidate.catalog")
    if any(key in set(registry["public_forbidden_keys"]) for key in _walk_keys(value)):
        fail("redaction.public")
    promoted = sum(item["decision"] == "PROMOTED" for item in value["candidate_results"])
    if value["counts"] != {"total": 18, "promoted": promoted, "withheld": 18 - promoted}:
        fail("state.invalid")
    for item, expected in zip(value["candidate_results"], catalog, strict=True):
        if item["candidate_id"] != expected["candidate_id"] or item["fact_hash"] != expected["fact_hash"]:
            fail("candidate.catalog")
        if expected["protocol_eligibility"] == "TERMINAL":
            if (
                item["decision"] != "WITHHELD"
                or item["terminal_state"] != expected["terminal_state"]
                or item["visibility"] != "RAW_DEBUG_ONLY"
                or item["dossier_hash"] is not None
                or item["window_outcomes"]
            ):
                fail("candidate.catalog")
            continue
        if expected["protocol_eligibility"] == "WITHHOLD_NO_EBUS_CAPABILITY_SOURCE":
            if (
                item["decision"] != "WITHHELD"
                or item["terminal_state"] != "NOT_COMPARABLE"
                or item["visibility"] != "RAW_DEBUG_ONLY"
                or item["dossier_hash"] is not None
                or item["window_outcomes"]
            ):
                fail("candidate.catalog")
            continue
        outcomes = item["window_outcomes"]
        if len(outcomes) != 2:
            fail("state.invalid")
        terminal = _derived_terminal(outcomes)
        if terminal is None:
            if (
                item["decision"] != "PROMOTED"
                or item["terminal_state"] is not None
                or item["visibility"] != "LOCKED_NOT_EXPOSED"
                or item["dossier_hash"] is None
            ):
                fail("state.invalid")
        elif (
            item["decision"] != "WITHHELD"
            or item["terminal_state"] != terminal
            or item["visibility"] != "RAW_DEBUG_ONLY"
            or item["dossier_hash"] is not None
        ):
            fail("state.invalid")
    if value["evidence_mode"] == "SANITIZED_CONFORMANCE":
        expected_gate = "BLOCKED_CONFORMANCE_ONLY"
        expected_verdict = "VALID_SUBSET_PROMOTION_CONFORMANCE"
    elif promoted:
        expected_gate = "READY_FOR_M9_PLANNING"
        expected_verdict = "VALID_PROMOTION_LOCK"
    else:
        expected_gate = "BLOCKED_ZERO_PROMOTED_LEAVES"
        expected_verdict = "VALID_ZERO_PROMOTION"
    if value["m9_consumer_gate"] != expected_gate or value["verdict"] != expected_verdict:
        fail("state.invalid")
    if value["provenance"]["class"] != value["evidence_mode"]:
        fail("provenance.binding")
    expected_hash = digest(
        RESULT_DOMAIN,
        {key: item for key, item in value.items() if key != "result_hash"},
    )
    if value["result_hash"] != expected_hash:
        fail("hash.result")


def verify_public(
    value: dict[str, Any],
    registry: dict[str, Any],
    private_value: dict[str, Any] | None = None,
    private_raw: bytes | None = None,
    live_sources: dict[str, pathlib.Path | list[pathlib.Path]] | None = None,
) -> None:
    _verify_public_structure(value, registry)
    if value["evidence_mode"] == "LIVE_CAPTURE" and (
        private_value is None or private_raw is None
    ):
        fail("private.required")
    if (private_value is None) != (private_raw is None):
        fail("private.required")
    if private_value is not None and private_raw is not None:
        verify_private(private_value, registry, live_sources)
        if value != _build_public(private_value, private_raw):
            fail("private.binding")


def _live_sources_from_args(
    args: argparse.Namespace,
) -> dict[str, pathlib.Path | list[pathlib.Path]] | None:
    values = {
        "m7_graph": args.m7_graph,
        "m7_status": args.m7_status,
        "m7_replay": args.m7_replay,
        "m8_evidence": args.m8_evidence,
        "m8_report": args.m8_report,
        "capture_receipts": args.capture_receipt,
        "deployment_source": args.deployment_source,
        "deployment_binary": args.deployment_binary,
    }
    supplied = any(value not in (None, []) for value in values.values())
    if not supplied:
        return None
    if any(value in (None, []) for value in values.values()) or len(args.capture_receipt) != 2:
        fail("live.sources.required")
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify-private", "derive-public", "verify-public"))
    parser.add_argument("--input", required=True, type=pathlib.Path)
    parser.add_argument("--registry", type=pathlib.Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--private-campaign", type=pathlib.Path)
    parser.add_argument("--m7-graph", type=pathlib.Path)
    parser.add_argument("--m7-status", type=pathlib.Path)
    parser.add_argument("--m7-replay", type=pathlib.Path)
    parser.add_argument("--m8-evidence", type=pathlib.Path)
    parser.add_argument("--m8-report", type=pathlib.Path)
    parser.add_argument("--capture-receipt", type=pathlib.Path, action="append", default=[])
    parser.add_argument("--deployment-source", type=pathlib.Path)
    parser.add_argument("--deployment-binary", type=pathlib.Path)
    args = parser.parse_args()
    try:
        value, raw = load_json(args.input)
        registry = registry_value(args.registry)
        live_sources = _live_sources_from_args(args)
        if args.command == "verify-private":
            verify_private(value, registry, live_sources)
            print("PASS")
        elif args.command == "derive-public":
            print(
                canonical(derive_public(value, registry, raw, live_sources)).decode(
                    "utf-8"
                )
            )
        else:
            private_value = None
            private_raw = None
            if args.private_campaign is not None:
                private_value, private_raw = load_json(args.private_campaign)
            verify_public(value, registry, private_value, private_raw, live_sources)
            print("PASS")
        return 0
    except ValidationFailure as exc:
        print(exc.category)
        return 1


if __name__ == "__main__":
    sys.exit(main())
