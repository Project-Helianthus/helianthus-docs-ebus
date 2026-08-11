#!/usr/bin/env python3
"""Validate and deterministically redact MSP-085-LIVE-R2 campaigns."""

from __future__ import annotations

import argparse
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
import validate_candidate_fact_graph as candidate_schema


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "docs/platform/schemas"
DEFAULT_REGISTRY = SCHEMA_ROOT / "leaf-promotion-captured-multi-leaf-registry-v1.json"
PRIVATE_SCHEMA = SCHEMA_ROOT / "leaf-promotion-captured-multi-leaf-v1.schema.json"
PUBLIC_SCHEMA = SCHEMA_ROOT / "leaf-promotion-captured-multi-leaf-result-v1.schema.json"

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
PINNED_REGISTRY_SHA256 = "sha256:854eb51398c949f14bc905d1d26c906f37243e4a218b7e990734064944621f59"
SAFE_INTEGER = 9_007_199_254_740_991
MAX_INPUT_BYTES = 1_048_576


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


def load_json(path: pathlib.Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        if len(raw) > MAX_INPUT_BYTES or re.search(
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


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


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


def _validate_sample(sample: dict[str, Any], source: str, window: dict[str, Any]) -> None:
    if sample["source"] != source or not sample["valid"]:
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
    if observed < timestamp_ns(window["started_at"]) or observed > timestamp_ns(window["ended_at"]):
        fail("sample.invalid")
    if sample["capture_generation"] != window["capture_generation"]:
        fail("sample.invalid")
    if source == "EBUS":
        if (
            sample["poll_id"] is None
            or sample["poll_generation"] != window["ebus_poll_generation"]
            or sample["runtime_epoch"] is not None
            or sample["connection_generation"] is not None
        ):
            fail("sample.invalid")
    else:
        if (
            sample["poll_id"] is not None
            or sample["poll_generation"] is not None
            or sample["runtime_epoch"] != window["eebus_runtime_epoch"]
            or sample["connection_generation"] != window["connection_generation"]
        ):
            fail("sample.invalid")


def _converted(value: Decimal, conversion: dict[str, Any]) -> Decimal:
    if conversion["mode"] == "IDENTITY":
        if conversion["source_unit"] != conversion["target_unit"]:
            fail("comparator.invalid")
        if decimal_value(conversion["scale"]) != Decimal(1) or decimal_value(conversion["offset"]) != Decimal(0):
            fail("comparator.invalid")
    return value * decimal_value(conversion["scale"]) + decimal_value(conversion["offset"])


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
    numeric = decimal_value(raw)
    if numeric != numeric.to_integral_value():
        fail("comparator.invalid")
    return int(numeric)


def _protocol_mapping_matches(source: dict[str, Any], sample: dict[str, Any], normalized: Any) -> bool:
    profile = source.get("exact_mapping")
    if not isinstance(profile, dict) or not isinstance(profile.get("pairs"), list):
        return False
    raw = _protocol_raw_value(sample["raw_value"])
    return any(
        pair == {"raw": raw, "normalized": normalized}
        for pair in profile["pairs"]
    )


def _mapping_pair_matches(
    expected: dict[str, Any], ebus: dict[str, Any], eebus: dict[str, Any], normalized: Any
) -> bool:
    profile = expected["eebus_source"]["mapping_profile"]
    if not isinstance(profile, dict) or not isinstance(profile.get("pairs"), list):
        return False
    ebus_raw = _raw_profile_value(ebus["raw_value"])
    eebus_raw = _raw_profile_value(eebus["raw_value"])
    return any(
        pair == {"ebus_raw": ebus_raw, "eebus_raw": eebus_raw, "normalized": normalized}
        for pair in profile["pairs"]
    )


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
        pair["ebus_raw"] == ebus_raw and pair["normalized"] == normalized
        for pair in profile["pairs"]
    )


def _validate_match(
    assessment: dict[str, Any],
    expected: dict[str, Any],
    window: dict[str, Any],
    capture_limits: dict[str, int],
) -> None:
    comparator_class = expected["comparator_class"]
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
        left = _converted(_typed(ebus["value"], "NUMERIC"), comparator["conversion"])
        right = _typed(eebus["value"], "NUMERIC")
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
        ):
            fail("state.invalid")
        if ebus is not None:
            _validate_sample(ebus, "EBUS", window)
            if not _catalog_sample_matches(expected, ebus, "EBUS"):
                fail("comparator.invalid")
        if eebus is not None:
            _validate_sample(eebus, "EEBUS", window)
            if not _catalog_sample_matches(expected, eebus, "EEBUS"):
                fail("comparator.invalid")
        return
    if comparator["outcome"] == "MISSING":
        fail("state.invalid")
    if comparator["outcome"] != "MISMATCH":
        fail("state.invalid")

    ebus, eebus = _validate_pair(assessment, window, capture_limits)
    if not _catalog_sample_matches(expected, ebus, "EBUS") or not _catalog_sample_matches(
        expected, eebus, "EEBUS"
    ):
        fail("comparator.invalid")

    if expected["comparator_class"] == "NUMERIC_DECLARED_GRANULARITY":
        step = decimal_value(comparator["declared_spine_step"])
        left = _converted(_typed(ebus["value"], "NUMERIC"), comparator["conversion"])
        right = _typed(eebus["value"], "NUMERIC")
        delta = abs(left - right)
        if decimal_value(comparator["delta"]) != delta or delta <= step:
            fail("comparator.invalid")
        return

    expected_kind = (
        "ENUM"
        if expected["comparator_class"] == "ENUM_EXACT_MAPPING"
        else "BOOLEAN"
    )
    if _typed(ebus["value"], expected_kind) == _typed(
        eebus["value"], expected_kind
    ):
        fail("comparator.invalid")


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


def verify_private(value: dict[str, Any], registry: dict[str, Any]) -> None:
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
    elif (
        provenance["fixture_id"] is not None
        or provenance["generator"] is not None
        or len(provenance["capture_receipts"]) != 2
        or provenance["deployment_source_commit"] is None
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
                _validate_match(assessment, expected, window, capture_limits)
            else:
                _validate_non_match_assessment(assessment, expected, window, capture_limits)

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
            "m7_status_hash": value["source_bindings"]["m7_status_hash"],
            "m8_evidence_hash": value["source_bindings"]["m8_evidence_hash"],
            "m8_report_hash": value["source_bindings"]["m8_report_hash"],
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
    value: dict[str, Any], registry: dict[str, Any], private_raw: bytes
) -> dict[str, Any]:
    verify_private(value, registry)
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
) -> None:
    _verify_public_structure(value, registry)
    if value["evidence_mode"] == "LIVE_CAPTURE" and (
        private_value is None or private_raw is None
    ):
        fail("private.required")
    if (private_value is None) != (private_raw is None):
        fail("private.required")
    if private_value is not None and private_raw is not None:
        verify_private(private_value, registry)
        if value != _build_public(private_value, private_raw):
            fail("private.binding")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify-private", "derive-public", "verify-public"))
    parser.add_argument("--input", required=True, type=pathlib.Path)
    parser.add_argument("--registry", type=pathlib.Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--private-campaign", type=pathlib.Path)
    args = parser.parse_args()
    try:
        value, raw = load_json(args.input)
        registry = registry_value(args.registry)
        if args.command == "verify-private":
            verify_private(value, registry)
            print("PASS")
        elif args.command == "derive-public":
            print(canonical(derive_public(value, registry, raw)).decode("utf-8"))
        else:
            private_value = None
            private_raw = None
            if args.private_campaign is not None:
                private_value, private_raw = load_json(args.private_campaign)
            verify_public(value, registry, private_value, private_raw)
            print("PASS")
        return 0
    except ValidationFailure as exc:
        print(exc.category)
        return 1


if __name__ == "__main__":
    sys.exit(main())
