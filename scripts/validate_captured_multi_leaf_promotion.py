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
        value, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest(domain: bytes, value: Any) -> str:
    return "sha256:" + hashlib.sha256(domain + canonical(value)).hexdigest()


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
    registry, _ = load_json(path)
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
    observed = timestamp_ns(sample["observed_at"])
    if observed < timestamp_ns(window["started_at"]) or observed > timestamp_ns(window["ended_at"]):
        fail("sample.invalid")
    if source == "EBUS":
        if sample["poll_id"] is None or sample["runtime_epoch"] is not None or sample["connection_generation"] is not None:
            fail("sample.invalid")
    else:
        if (
            sample["poll_id"] is not None
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


def _validate_match(
    assessment: dict[str, Any], comparator_class: str, window: dict[str, Any]
) -> None:
    ebus = assessment["ebus_sample"]
    eebus = assessment["eebus_sample"]
    if ebus is None or eebus is None:
        fail("comparator.invalid")
    _validate_sample(ebus, "EBUS", window)
    _validate_sample(eebus, "EEBUS", window)
    ebus_ns = timestamp_ns(ebus["observed_at"])
    eebus_ns = timestamp_ns(eebus["observed_at"])
    if assessment["skew_ns"] != abs(ebus_ns - eebus_ns) or assessment["skew_ns"] > assessment["max_skew_ns"]:
        fail("sample.invalid")
    age = max(timestamp_ns(window["ended_at"]) - ebus_ns, timestamp_ns(window["ended_at"]) - eebus_ns)
    if assessment["age_ns"] != age or age > assessment["max_age_ns"]:
        fail("sample.invalid")

    comparator = assessment["comparator"]
    if comparator["class"] != comparator_class or comparator["outcome"] != "MATCH":
        fail("comparator.invalid")
    if comparator_class == "NUMERIC_DECLARED_GRANULARITY":
        step = decimal_value(comparator["declared_spine_step"])
        if step is None or step <= 0 or comparator["conversion"] is None:
            fail("comparator.invalid")
        left = _converted(_typed(ebus["value"], "NUMERIC"), comparator["conversion"])
        right = _typed(eebus["value"], "NUMERIC")
        delta = abs(left - right)
        if decimal_value(comparator["delta"]) != delta or delta > step or comparator["mapping_hash"] is not None:
            fail("comparator.invalid")
        if ebus["unit"] != comparator["conversion"]["source_unit"] or eebus["unit"] != comparator["conversion"]["target_unit"]:
            fail("comparator.invalid")
    elif comparator_class == "ENUM_EXACT_MAPPING":
        if comparator["mapping_hash"] is None or comparator["declared_spine_step"] is not None or comparator["delta"] is not None or comparator["conversion"] is not None:
            fail("comparator.invalid")
        if _typed(ebus["value"], "ENUM") != _typed(eebus["value"], "ENUM"):
            fail("comparator.invalid")
    elif comparator_class == "BOOLEAN_EXACT_MAPPING":
        if comparator["mapping_hash"] is None or comparator["declared_spine_step"] is not None or comparator["delta"] is not None or comparator["conversion"] is not None:
            fail("comparator.invalid")
        if _typed(ebus["value"], "BOOLEAN") != _typed(eebus["value"], "BOOLEAN"):
            fail("comparator.invalid")
    else:
        fail("comparator.invalid")


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
    windows = value["windows"]
    if [window["phase"] for window in windows] != registry["window_phases"]:
        fail("window.restart")
    if len({window["window_id"] for window in windows}) != 2:
        fail("window.restart")
    for window in windows:
        if timestamp_ns(window["started_at"]) >= timestamp_ns(window["ended_at"]):
            fail("window.restart")
    if (
        windows[0]["process_instance_hash"] == windows[1]["process_instance_hash"]
        or windows[0]["local_identity_hash"] != windows[1]["local_identity_hash"]
        or windows[0]["trust_state_hash"] != windows[1]["trust_state_hash"]
        or windows[0]["admitted_source"] != windows[1]["admitted_source"]
    ):
        fail("window.restart")

    catalog = registry["candidate_catalog"]
    if [item["candidate_id"] for item in value["candidates"]] != [item["candidate_id"] for item in catalog]:
        fail("candidate.catalog")
    window_by_id = {window["window_id"]: window for window in windows}
    for candidate, expected in zip(value["candidates"], catalog, strict=True):
        for field in ("candidate_id", "fact_hash", "source_status", "semantic_path", "comparator_class"):
            if candidate[field] != expected[field]:
                fail("candidate.catalog")
        if expected["source_status"] == "WITHHELD":
            if (
                candidate["decision"] != "WITHHELD"
                or candidate["terminal_state"] != expected["terminal_state"]
                or candidate["visibility"] != "RAW_DEBUG_ONLY"
                or candidate["ebus_identity"] is not None
                or candidate["eebus_identity"] is not None
                or candidate["assessments"]
                or candidate["dossier_hash"] is not None
            ):
                fail("state.invalid")
            continue
        if candidate["eebus_identity"] is None:
            fail("identity.binding")
        outcomes = [assessment["comparator"]["outcome"] for assessment in candidate["assessments"]]
        if candidate["assessments"] and (
            len(candidate["assessments"]) != 2
            or [assessment["window_id"] for assessment in candidate["assessments"]]
            != [window["window_id"] for window in windows]
        ):
            fail("state.invalid")
        if candidate["decision"] == "PROMOTED":
            if (
                candidate["ebus_identity"] is None
                or len(candidate["assessments"]) != 2
                or [assessment["window_id"] for assessment in candidate["assessments"]] != [window["window_id"] for window in windows]
                or outcomes != ["MATCH", "MATCH"]
                or candidate["terminal_state"] is not None
                or candidate["visibility"] != "LOCKED_NOT_EXPOSED"
            ):
                fail("state.invalid")
            if candidate["ebus_identity"]["source_address"] != windows[0]["admitted_source"]:
                fail("identity.binding")
            for assessment in candidate["assessments"]:
                _validate_match(assessment, candidate["comparator_class"], window_by_id[assessment["window_id"]])
            if candidate["dossier_hash"] != digest(DOSSIER_DOMAIN, _candidate_payload(candidate)):
                fail("hash.dossier")
        else:
            if candidate["terminal_state"] is None or candidate["visibility"] != "RAW_DEBUG_ONLY" or candidate["dossier_hash"] is not None:
                fail("state.invalid")
            if outcomes and all(outcome == "MATCH" for outcome in outcomes):
                fail("state.invalid")
            for assessment in candidate["assessments"]:
                if assessment["comparator"]["class"] != candidate["comparator_class"]:
                    fail("comparator.invalid")
                if assessment["comparator"]["outcome"] == "MATCH":
                    _validate_match(
                        assessment,
                        candidate["comparator_class"],
                        window_by_id[assessment["window_id"]],
                    )
    if value["source_bindings"]["replay_hash"] != replay_hash(value):
        fail("hash.replay")
    expected_hash = digest(CAMPAIGN_DOMAIN, {key: item for key, item in value.items() if key != "campaign_hash"})
    if value["campaign_hash"] != expected_hash:
        fail("hash.campaign")


def derive_public(value: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    verify_private(value, registry)
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
        "source_bindings": {
            "m7_graph_hash": value["source_bindings"]["m7_graph_hash"],
            "m7_status_hash": value["source_bindings"]["m7_status_hash"],
            "m8_evidence_hash": value["source_bindings"]["m8_evidence_hash"],
            "m8_report_hash": value["source_bindings"]["m8_report_hash"],
            "replay_hash": value["source_bindings"]["replay_hash"],
            "campaign_hash": value["campaign_hash"],
        },
        "counts": {"total": 18, "promoted": promoted, "withheld": 18 - promoted},
        "candidate_results": results,
        "m9_consumer_gate": gate,
        "verdict": verdict,
        "result_hash": "sha256:" + "0" * 64,
    }
    public["result_hash"] = digest(RESULT_DOMAIN, {key: item for key, item in public.items() if key != "result_hash"})
    verify_public(public, registry)
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


def verify_public(value: dict[str, Any], registry: dict[str, Any]) -> None:
    schema_validate(value, PUBLIC_SCHEMA, "schema.public")
    catalog = registry["candidate_catalog"]
    if [item["candidate_id"] for item in value["candidate_results"]] != [item["candidate_id"] for item in catalog]:
        fail("candidate.catalog")
    if any(key in set(registry["public_forbidden_keys"]) for key in _walk_keys(value)):
        fail("redaction.public")
    promoted = sum(item["decision"] == "PROMOTED" for item in value["candidate_results"])
    if value["counts"] != {"total": 18, "promoted": promoted, "withheld": 18 - promoted}:
        fail("state.invalid")
    for item, expected in zip(value["candidate_results"], catalog, strict=True):
        if item["fact_hash"] != expected["fact_hash"]:
            fail("candidate.catalog")
        if item["decision"] == "PROMOTED":
            if item["terminal_state"] is not None or item["visibility"] != "LOCKED_NOT_EXPOSED" or item["dossier_hash"] is None or item["window_outcomes"] != ["MATCH", "MATCH"]:
                fail("state.invalid")
        elif item["terminal_state"] is None or item["visibility"] != "RAW_DEBUG_ONLY" or item["dossier_hash"] is not None:
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
    expected_hash = digest(RESULT_DOMAIN, {key: item for key, item in value.items() if key != "result_hash"})
    if value["result_hash"] != expected_hash:
        fail("hash.result")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify-private", "derive-public", "verify-public"))
    parser.add_argument("--input", required=True, type=pathlib.Path)
    parser.add_argument("--registry", type=pathlib.Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args()
    try:
        value, _ = load_json(args.input)
        registry = registry_value(args.registry)
        if args.command == "verify-private":
            verify_private(value, registry)
            print("PASS")
        elif args.command == "derive-public":
            print(canonical(derive_public(value, registry)).decode("ascii"))
        else:
            verify_public(value, registry)
            print("PASS")
        return 0
    except ValidationFailure as exc:
        print(exc.category)
        return 1


if __name__ == "__main__":
    sys.exit(main())
