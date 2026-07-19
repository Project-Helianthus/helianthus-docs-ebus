#!/usr/bin/env python3
"""Offline verifier and deterministic replayer for MSP-065 evidence bundles."""

from __future__ import annotations

import argparse
import calendar
import copy
import hashlib
import json
import pathlib
import re
import sys
import unicodedata
from datetime import datetime
from typing import Any


ARTIFACT_DOMAIN = b"HELIANTHUS:SYNCHRONIZED-EVIDENCE-ARTIFACT:V1\0"
BUNDLE_DOMAIN = b"HELIANTHUS:SYNCHRONIZED-EVIDENCE-BUNDLE:V1\0"
SAFE_MAX = 9007199254740991
MAXIMUM_SKEW_NS = 1_000_000_000
HARD_LIMITS = {
    "max_sources": 64,
    "max_items_per_source": 4096,
    "max_artifact_bytes": 1_048_576,
    "max_bundle_bytes": 67_108_864,
    "max_depth": 32,
    "max_string_bytes": 65_536,
    "max_capture_duration_ns": 900_000_000_000,
    "max_source_duration_ns": 60_000_000_000,
}
PHASE_RANK = {"pre": 0, "action": 1, "post": 2}
KIND_RANK = {"EBUS": 0, "EEBUS": 1, "CLOUD_APP": 2}
RUNTIME_KINDS = set(KIND_RANK)
TIMESTAMP = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?Z$"
)
IPV4 = re.compile(r"(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])")
MAC = re.compile(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![0-9a-f])")
ROOT_KEYS = {
    "contract", "schema_version", "bundle_id", "captured_at", "capture_window",
    "clock", "scope", "mask_tier", "auth_scope", "limits", "evidence_refs",
    "sources", "artifacts", "recorder_version", "replay_version", "bundle_hash",
}
SOURCE_KEYS = {
    "contract", "schema_version", "source_id", "source_kind", "phase", "state",
    "error_category", "source_contract", "source_schema_version", "source_binding",
    "capture_window", "clock", "scope", "mask_tier", "auth_scope", "evidence_refs",
    "recorder_version", "replay_version", "acquisition_started_at",
    "acquisition_ended_at", "acquisition_start_offset_ns",
    "acquisition_end_offset_ns", "measured_latency_ns", "maximum_skew_ns",
    "ebus_identity", "artifact_ids",
}
ARTIFACT_KEYS = {
    "contract", "schema_version", "artifact_id", "source_id", "source_kind", "phase",
    "source_contract", "source_schema_version", "source_binding", "ebus_identity",
    "source_observed_at", "recorder_ingested_at", "recorder_ingested_offset_ns",
    "capture_window", "clock", "scope", "mask_tier", "auth_scope", "evidence_refs",
    "recorder_version", "replay_version", "remasking", "item_count", "byte_count",
    "normalized_evidence", "redacted_hash",
}
BINDING_KEYS = {
    "runtime_kind", "runtime_pseudonym", "operation_id", "operation_version",
    "request_scope", "snapshot_scope", "source_kind", "source_contract",
    "source_schema_version", "owner_repository", "owner_path", "owner_commit",
    "schema_sha256", "capture_window", "mask_tier", "auth_scope", "ebus_identity",
}
LIMIT_KEYS = set(HARD_LIMITS)
AUTH_KEYS = {"authority", "permissions"}
REF_KEYS = {"kind", "digest_algorithm", "digest", "repository", "commit", "path"}
WINDOW_KEYS = {"pre", "action", "post"}
SEGMENT_KEYS = {"start_offset_ns", "end_offset_ns"}
ACTION_KEYS = {
    "start_offset_ns", "marker_offset_ns", "marker_captured_at", "marker_id",
    "evidence_ref", "end_offset_ns",
}
CLOCK_KEYS = {
    "clock_id", "wall_anchor", "monotonic_anchor_ns", "captured_offset_ns",
    "resolution_ns", "maximum_skew_ns", "observations",
}
CLOCK_OBSERVATION_KEYS = {"observed_at", "offset_ns", "uncertainty_ns"}
TIMING_FIELDS = (
    "acquisition_started_at", "acquisition_ended_at",
    "acquisition_start_offset_ns", "acquisition_end_offset_ns",
    "measured_latency_ns",
)
IDENTITY_KEYS = {
    "B509": {
        "family", "target_pseudonym", "target_address", "target_product",
        "register_family", "register_id", "unit_scale_source", "evidence_role",
    },
    "B524": {
        "family", "target_pseudonym", "opcode", "GG", "II", "RR", "target_address",
        "source_address", "group_meaning", "instance_gate", "register_category",
        "unit_scale_source",
    },
    "B555": {
        "family", "target_pseudonym", "device_family", "schedule_program",
        "slot_index", "day_of_week", "time_identity", "operation_mode_context",
        "unit_scale_source",
    },
}


class Failure(Exception):
    def __init__(self, category: str):
        self.category = category


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Failure("schema.bundle")
        result[key] = value
    return result


def load_json(path: pathlib.Path, category: str) -> Any:
    try:
        size = path.stat().st_size
        if size > HARD_LIMITS["max_bundle_bytes"]:
            raise Failure("limits.exceeded")
        raw = path.read_bytes()
        preflight_json_bytes(raw)
        return json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
    except Failure:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise Failure(category)


def preflight_json_bytes(raw: bytes) -> None:
    """Reject oversized/deep input before the recursive JSON decoder runs."""
    if len(raw) > HARD_LIMITS["max_bundle_bytes"]:
        raise Failure("limits.exceeded")
    depth = 0
    in_string = False
    escaped = False
    for byte in raw:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x7B, 0x5B):
            depth += 1
            if depth > HARD_LIMITS["max_depth"] + 1:
                raise Failure("limits.exceeded")
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth < 0:
                raise Failure("schema.bundle")


def validate_string(value: str, maximum: int) -> None:
    if len(value.encode("utf-8")) > maximum:
        raise Failure("limits.exceeded")
    if unicodedata.normalize("NFC", value) != value:
        raise Failure("schema.bundle")
    if any(unicodedata.category(char) in {"Cc", "Cs"} for char in value):
        raise Failure("schema.bundle")


def check_canonical_subset(value: Any, depth: int = 0, *, key: bool = False) -> None:
    """Enforce the RFC 8785-compatible V1 safe-integer/fixed-ASCII-key subset."""
    if depth > HARD_LIMITS["max_depth"]:
        raise Failure("limits.exceeded")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if value < 0 or value > SAFE_MAX:
            raise Failure("schema.bundle")
        return
    if isinstance(value, float):
        raise Failure("schema.bundle")
    if isinstance(value, str):
        validate_string(value, HARD_LIMITS["max_string_bytes"])
        if key and (not value.isascii() or any(ord(char) < 32 or ord(char) > 126 for char in value)):
            raise Failure("schema.bundle")
        return
    if isinstance(value, list):
        for item in value:
            check_canonical_subset(item, depth + 1)
        return
    if isinstance(value, dict):
        for field, item in value.items():
            check_canonical_subset(field, depth + 1, key=True)
            check_canonical_subset(item, depth + 1)
        return
    raise Failure("schema.bundle")


def canonical(value: Any) -> bytes:
    check_canonical_subset(value)
    try:
        return json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError):
        raise Failure("schema.bundle")


def digest(domain: bytes, value: Any) -> str:
    return hashlib.sha256(domain + canonical(value)).hexdigest()


def timestamp_ns(value: Any) -> int:
    if not isinstance(value, str):
        raise Failure("schema.bundle")
    match = TIMESTAMP.fullmatch(value)
    if not match:
        raise Failure("schema.bundle")
    year, month, day, hour, minute, second = map(int, match.groups()[:6])
    fraction = match.group(7) or ""
    if fraction.endswith("0"):
        raise Failure("schema.bundle")
    try:
        seconds = calendar.timegm(datetime(year, month, day, hour, minute, second).timetuple())
    except ValueError:
        raise Failure("schema.bundle")
    return seconds * 1_000_000_000 + int(fraction.ljust(9, "0") or "0")


def check_portable(value: Any, depth: int, limits: dict[str, Any], *, key: bool = False) -> None:
    if depth > limits["max_depth"]:
        raise Failure("limits.exceeded")
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if value < 0 or value > SAFE_MAX:
            raise Failure("schema.bundle")
        return
    if isinstance(value, float):
        raise Failure("schema.bundle")
    if isinstance(value, str):
        validate_string(value, limits["max_string_bytes"])
        if key and (not value.isascii() or any(ord(char) < 32 or ord(char) > 126 for char in value)):
            raise Failure("schema.bundle")
        return
    if isinstance(value, list):
        for item in value:
            check_portable(item, depth + 1, limits)
        return
    if isinstance(value, dict):
        for field, item in value.items():
            check_portable(field, depth + 1, limits, key=True)
            check_portable(item, depth + 1, limits)
        return
    raise Failure("schema.bundle")


def exact_keys(value: Any, keys: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise Failure("schema.bundle")


def validate_identity(identity: Any, expected_kind: str | None = None) -> None:
    if not isinstance(identity, dict):
        raise Failure("schema.bundle")
    family = identity.get("family")
    if family not in IDENTITY_KEYS or set(identity) != IDENTITY_KEYS[family]:
        raise Failure("schema.bundle")
    if expected_kind and expected_kind != "EBUS_" + family:
        raise Failure("schema.bundle")
    target = identity["target_pseudonym"]
    if not isinstance(target, str) or not re.fullmatch(r"target-[0-9a-f]{32}", target):
        raise Failure("schema.bundle")
    numeric = {
        "B509": (("target_address", 255), ("register_id", 65535)),
        "B524": (("opcode", 255), ("GG", 255), ("II", 255), ("RR", 65535),
                 ("target_address", 255), ("source_address", 255)),
        "B555": (("slot_index", 255),),
    }[family]
    for key, maximum in numeric:
        if type(identity[key]) is not int or not 0 <= identity[key] <= maximum:
            raise Failure("schema.bundle")


def validate_binding(binding: Any, registry: dict[tuple[str, str, int], dict[str, Any]]) -> None:
    exact_keys(binding, BINDING_KEYS)
    exact_keys(binding["request_scope"], {"phase", "source_kind", "operation_scope"})
    exact_keys(binding["snapshot_scope"], {"mode", "selector"})
    if binding["runtime_kind"] not in RUNTIME_KINDS:
        raise Failure("schema.bundle")
    if not isinstance(binding["runtime_pseudonym"], str) or not re.fullmatch(
        r"runtime-[0-9a-f]{32}", binding["runtime_pseudonym"]
    ):
        raise Failure("schema.bundle")
    if not isinstance(binding["operation_id"], str) or not isinstance(binding["operation_version"], str):
        raise Failure("schema.bundle")
    if not re.fullmatch(r"git:[0-9a-f]{40}", binding["operation_version"]):
        raise Failure("schema.bundle")
    if binding["snapshot_scope"]["mode"] not in {"SNAPSHOT", "LIVE_READ", "PRECAPTURED"}:
        raise Failure("schema.bundle")
    key = (binding["source_kind"], binding["source_contract"], binding["source_schema_version"])
    entry = registry.get(key)
    if entry is None:
        raise Failure("binding.registry")
    for field in ("owner_repository", "owner_path", "owner_commit", "schema_sha256"):
        if binding[field] != entry[field]:
            raise Failure("binding.registry")
    identity = binding["ebus_identity"]
    if binding["source_kind"].startswith("EBUS_"):
        validate_identity(identity, binding["source_kind"])
    elif identity is not None:
        raise Failure("schema.bundle")


def validate_refs(refs: Any) -> None:
    if not isinstance(refs, list) or not refs:
        raise Failure("schema.bundle")
    encoded: list[tuple[Any, ...]] = []
    for ref in refs:
        exact_keys(ref, REF_KEYS)
        if ref["kind"] == "CONTENT":
            if ref["digest_algorithm"] != "SHA256_CONTENT_BYTES" or any(
                ref[field] is not None for field in ("repository", "commit", "path")
            ):
                raise Failure("schema.bundle")
        elif ref["kind"] == "GIT_BLOB":
            if ref["digest_algorithm"] != "SHA256_GIT_BLOB_V1" or any(
                not isinstance(ref[field], str) for field in ("repository", "commit", "path")
            ):
                raise Failure("schema.bundle")
        else:
            raise Failure("schema.bundle")
        if not isinstance(ref["digest"], str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", ref["digest"]):
            raise Failure("schema.bundle")
        encoded.append(tuple("" if ref[field] is None else ref[field] for field in (
            "kind", "digest_algorithm", "digest", "repository", "commit", "path",
        )))
    if encoded != sorted(set(encoded)):
        raise Failure("ordering.invalid")


def validate_auth(auth: Any, root_permissions: set[str] | None = None) -> set[str]:
    exact_keys(auth, AUTH_KEYS)
    permissions = auth["permissions"]
    if auth["authority"] != "effective" or not isinstance(permissions, list) or not permissions:
        raise Failure("schema.bundle")
    if permissions != sorted(set(permissions)) or any(not isinstance(item, str) for item in permissions):
        raise Failure("ordering.invalid")
    result = set(permissions)
    if root_permissions is not None and not result <= root_permissions:
        raise Failure("binding.registry")
    return result


def validate_capture_window(window: Any) -> None:
    exact_keys(window, WINDOW_KEYS)
    exact_keys(window["pre"], SEGMENT_KEYS)
    exact_keys(window["action"], ACTION_KEYS)
    exact_keys(window["post"], SEGMENT_KEYS)
    for segment in (window["pre"], window["action"], window["post"]):
        for field in ("start_offset_ns", "end_offset_ns"):
            if type(segment[field]) is not int or not 0 <= segment[field] <= SAFE_MAX:
                raise Failure("schema.bundle")
    action = window["action"]
    if type(action["marker_offset_ns"]) is not int or not re.fullmatch(
        r"marker-[0-9a-f]{32}", action["marker_id"]
    ):
        raise Failure("schema.bundle")
    timestamp_ns(action["marker_captured_at"])
    validate_refs([action["evidence_ref"]])


def validate_scope(scope: Any) -> None:
    exact_keys(scope, {"purpose", "source_kinds", "phases"})
    if scope["purpose"] != "SYNCHRONIZED_EVIDENCE_ONLY" or scope["phases"] != ["pre", "action", "post"]:
        raise Failure("schema.bundle")
    kinds = scope["source_kinds"]
    if not isinstance(kinds, list) or not kinds or kinds != sorted(set(kinds), key=KIND_RANK.get):
        raise Failure("ordering.invalid")
    if any(kind not in RUNTIME_KINDS for kind in kinds):
        raise Failure("schema.bundle")


def validate_phase_timing(
    source: dict[str, Any], window: dict[str, Any], limits: dict[str, int]
) -> None:
    values = [source[field] for field in TIMING_FIELDS]
    all_null = all(value is None for value in values)
    all_present = all(value is not None for value in values)
    state = source["state"]
    if not (all_null or all_present):
        raise Failure("schema.bundle")
    if state in {"PRESENT", "UNAVAILABLE"} and not all_present:
        raise Failure("schema.bundle")
    if state == "NOT_TESTED" and not all_null:
        raise Failure("schema.bundle")
    allowed_errors = {
        "PRESENT": {None},
        "WITHHELD": {"POLICY_WITHHELD", "AUTHORIZATION_DENIED", "REDACTION_FAILED", "EXACT_IDENTITY_MISSING"},
        "NOT_TESTED": {"NOT_SELECTED", "BUDGET_EXHAUSTED", "EXACT_IDENTITY_MISSING"},
        "UNAVAILABLE": {"BACKEND_UNAVAILABLE", "TIMEOUT", "ACQUISITION_FAILED"},
    }
    if state not in allowed_errors or source["error_category"] not in allowed_errors[state]:
        raise Failure("schema.bundle")
    if (state == "PRESENT") != bool(source["artifact_ids"]):
        raise Failure("schema.bundle")
    if all_present:
        start = source["acquisition_start_offset_ns"]
        end = source["acquisition_end_offset_ns"]
        segment = window[source["phase"]]
        if not segment["start_offset_ns"] <= start <= end <= segment["end_offset_ns"]:
            raise Failure("schema.bundle")
        if source["measured_latency_ns"] != end - start:
            raise Failure("schema.bundle")
        if source["measured_latency_ns"] > limits["max_source_duration_ns"]:
            raise Failure("limits.exceeded")


def load_registry(path: pathlib.Path) -> dict[tuple[str, str, int], dict[str, Any]]:
    raw = load_json(path, "schema.registry")
    if not isinstance(raw, dict) or set(raw) != {"contract", "version", "entries"}:
        raise Failure("schema.registry")
    if raw["contract"] != "helianthus.platform.source-schema-registry.v1" or raw["version"] != 1:
        raise Failure("schema.registry")
    result = {}
    root = path.resolve().parents[3]
    entry_keys = {
        "source_kind", "source_contract", "source_schema_version", "owner_repository",
        "owner_path", "owner_commit", "schema_sha256", "embedded_schema",
    }
    for entry in raw["entries"]:
        if not isinstance(entry, dict) or set(entry) != entry_keys:
            raise Failure("schema.registry")
        key = (entry["source_kind"], entry["source_contract"], entry["source_schema_version"])
        if key in result:
            raise Failure("schema.registry")
        embedded = entry["embedded_schema"]
        if embedded is not None:
            schema_path = root / embedded
            try:
                actual = hashlib.sha256(schema_path.read_bytes()).hexdigest()
            except OSError:
                raise Failure("schema.registry")
            if actual != entry["schema_sha256"]:
                raise Failure("schema.registry")
        result[key] = entry
    return result


def validate_clock(bundle: dict[str, Any]) -> None:
    clock = bundle["clock"]
    exact_keys(clock, CLOCK_KEYS)
    observations = clock["observations"]
    if not isinstance(observations, list) or len(observations) < 2:
        raise Failure("clock.skew")
    for row in observations:
        exact_keys(row, CLOCK_OBSERVATION_KEYS)
        if any(type(row[field]) is not int for field in ("offset_ns", "uncertainty_ns")):
            raise Failure("clock.skew")
    if any(type(clock[field]) is not int for field in (
        "monotonic_anchor_ns", "captured_offset_ns", "resolution_ns", "maximum_skew_ns",
    )):
        raise Failure("clock.skew")
    if clock["clock_id"] != "capture-clock-1" or clock["monotonic_anchor_ns"] != 0 or clock["resolution_ns"] < 1:
        raise Failure("clock.skew")
    anchor = timestamp_ns(clock["wall_anchor"])
    if observations[0]["offset_ns"] != 0 or observations[0]["observed_at"] != clock["wall_anchor"]:
        raise Failure("clock.skew")
    offsets = [row["offset_ns"] for row in observations]
    if offsets != sorted(set(offsets)):
        raise Failure("clock.skew")
    computed = max(
        abs(timestamp_ns(row["observed_at"]) - anchor - row["offset_ns"]) + row["uncertainty_ns"]
        for row in observations
    )
    if computed > MAXIMUM_SKEW_NS or clock["maximum_skew_ns"] > MAXIMUM_SKEW_NS:
        raise Failure("clock.skew")
    if computed != clock["maximum_skew_ns"]:
        raise Failure("clock.skew")
    if offsets[-1] < clock["captured_offset_ns"]:
        raise Failure("clock.skew")
    pairs = [(bundle["captured_at"], clock["captured_offset_ns"])]
    action = bundle["capture_window"]["action"]
    pairs.append((action["marker_captured_at"], action["marker_offset_ns"]))
    for source in bundle["sources"]:
        if source["acquisition_started_at"] is not None:
            pairs.extend([
                (source["acquisition_started_at"], source["acquisition_start_offset_ns"]),
                (source["acquisition_ended_at"], source["acquisition_end_offset_ns"]),
            ])
    for artifact in bundle["artifacts"]:
        pairs.append((artifact["recorder_ingested_at"], artifact["recorder_ingested_offset_ns"]))
    for wall, offset in pairs:
        if abs(timestamp_ns(wall) - anchor - offset) > computed:
            raise Failure("clock.skew")


def walk_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from walk_values(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from walk_values(item)


def validate_privacy(bundle: dict[str, Any]) -> None:
    prohibited = (
        "password", "private_key", "access_token", "refresh_token", "serial_number",
        "ship_id", "ski", "hostname", "interface_name", "host_path",
        "vendor_restricted", "raw_packet", "packet_capture", "wire_transcript",
    )
    for value in walk_values(bundle):
        lowered = value.lower()
        if IPV4.search(value) or MAC.search(value) or any(
            re.search(r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])", lowered)
            for token in prohibited
        ):
            raise Failure("privacy.prohibited")


def pointer_get(value: Any, pointer: str) -> Any:
    current = value
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(token)]
        elif isinstance(current, dict):
            current = current[token]
        else:
            raise KeyError(pointer)
    return current


def identity_digest_paths(value: Any, prefix: str = "") -> set[str]:
    paths: set[str] = set()
    if isinstance(value, list):
        for index, item in enumerate(value):
            paths |= identity_digest_paths(item, f"{prefix}/{index}")
    elif isinstance(value, dict):
        for key, item in value.items():
            escaped = key.replace("~", "~0").replace("/", "~1")
            path = f"{prefix}/{escaped}"
            if key == "digest" and isinstance(item, str):
                paths.add(path)
            paths |= identity_digest_paths(item, path)
    return paths


def validate_remasking(artifacts: list[dict[str, Any]]) -> None:
    scope_ids = {artifact["remasking"]["scope_id"] for artifact in artifacts}
    if len(scope_ids) > 1:
        raise Failure("privacy.remask")
    assignments: dict[str, tuple[str, str]] = {}
    for artifact in artifacts:
        remasking = artifact["remasking"]
        exact_keys(remasking, {"method", "scope_id", "entries"})
        if remasking["method"] != "PER_BUNDLE_CSPRNG":
            raise Failure("privacy.remask")
        if not re.fullmatch(r"remask-[0-9a-f]{32}", remasking["scope_id"]):
            raise Failure("privacy.remask")
        seen_paths: set[str] = set()
        seen_values: set[str] = set()
        ordered_entries: list[tuple[str, str]] = []
        for entry in remasking["entries"]:
            if set(entry) != {"path", "pseudonym"}:
                raise Failure("schema.bundle")
            path, pseudonym = entry["path"], entry["pseudonym"]
            if path in seen_paths or pseudonym in seen_values:
                raise Failure("privacy.remask")
            try:
                actual = pointer_get(artifact["normalized_evidence"], path)
            except (KeyError, IndexError, ValueError, TypeError):
                raise Failure("privacy.remask")
            if actual != pseudonym or not re.fullmatch(r"[A-Za-z0-9_-]{43}", pseudonym):
                raise Failure("privacy.remask")
            previous = assignments.get(pseudonym)
            identity = (artifact["source_id"], path)
            if previous is not None and previous != identity:
                raise Failure("privacy.remask")
            assignments[pseudonym] = identity
            seen_paths.add(path)
            seen_values.add(pseudonym)
            ordered_entries.append((path, pseudonym))
        if ordered_entries != sorted(ordered_entries):
            raise Failure("ordering.invalid")
        if artifact["source_binding"]["source_kind"] == "CLOUD_APP":
            declared = {entry["path"] for entry in remasking["entries"]}
            if "/subject_pseudonym" not in declared:
                raise Failure("privacy.remask")
        if artifact["source_binding"]["source_kind"] == "EEBUS":
            declared = {entry["path"] for entry in remasking["entries"]}
            if not identity_digest_paths(artifact["normalized_evidence"]) <= declared:
                raise Failure("privacy.remask")


def validate_source_payload(artifact: dict[str, Any]) -> int:
    payload = artifact["normalized_evidence"]
    if not isinstance(payload, dict):
        raise Failure("schema.source")
    kind = artifact["source_binding"]["source_kind"]
    common = {"contract", "schema_version", "source_observed_at"}
    if kind.startswith("EBUS_"):
        if payload.get("contract") != artifact["source_contract"] or payload.get("schema_version") != artifact["source_schema_version"]:
            raise Failure("schema.source")
        if payload.get("source_observed_at") != artifact["source_observed_at"]:
            raise Failure("schema.source")
        if set(payload) != common | {"identity", "observations"}:
            raise Failure("schema.source")
        validate_identity(payload["identity"], kind)
        if payload["identity"] != artifact["ebus_identity"]:
            raise Failure("schema.source")
        if not isinstance(payload["observations"], list) or not payload["observations"]:
            raise Failure("schema.source")
        family = payload["identity"]["family"]
        observation_keys = {
            "B509": {"register_id", "value", "unit", "quality"},
            "B524": {"value", "unit", "quality"},
            "B555": {"value", "quality"},
        }[family]
        for observation in payload["observations"]:
            exact_keys(observation, observation_keys)
            if observation["quality"] not in {"OBSERVED", "STALE"}:
                raise Failure("schema.source")
            if family == "B509" and (
                type(observation["register_id"]) is not int
                or not 0 <= observation["register_id"] <= 65535
            ):
                raise Failure("schema.source")
        return len(payload["observations"])
    elif kind == "CLOUD_APP":
        if payload.get("contract") != artifact["source_contract"] or payload.get("schema_version") != artifact["source_schema_version"]:
            raise Failure("schema.source")
        if payload.get("source_observed_at") != artifact["source_observed_at"]:
            raise Failure("schema.source")
        if set(payload) != common | {"subject_pseudonym", "observation_type", "value", "unit"}:
            raise Failure("schema.source")
        return 1
    elif kind == "EEBUS":
        if set(payload) != {"meta", "data", "error"} or payload["error"] is not None:
            raise Failure("schema.source")
        meta = payload["meta"]
        data = payload["data"]
        if not isinstance(meta, dict) or set(meta) != {
            "contract", "tool", "scope", "mask_tier", "auth_scope", "mode",
            "data_timestamp", "data_hash", "runtime",
        }:
            raise Failure("schema.source")
        if meta["contract"] != {"name": "helianthus-eebus-mcp", "major": 1, "minor": 0}:
            raise Failure("schema.source")
        if (meta["tool"], meta["scope"], meta["mask_tier"], meta["auth_scope"], meta["mode"]) != (
            "eebus.v1.services.list", "services", "redacted", "eebus.raw.read", "evidence",
        ):
            raise Failure("schema.source")
        if meta["data_timestamp"] != artifact["source_observed_at"]:
            raise Failure("schema.source")
        if not isinstance(meta["data_hash"], str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", meta["data_hash"]):
            raise Failure("schema.source")
        if meta["runtime"] != {"state": "ready"}:
            raise Failure("schema.source")
        if not isinstance(data, dict) or set(data) != {"services"} or not isinstance(data["services"], list):
            raise Failure("schema.source")
        for service in data["services"]:
            if not isinstance(service, dict) or set(service) != {"id", "kind", "visible", "paired"}:
                raise Failure("schema.source")
            if set(service["id"]) != {"kind", "digest"} or service["id"]["kind"] != "service":
                raise Failure("schema.source")
            if not re.fullmatch(r"[A-Za-z0-9_-]{43}", service["id"]["digest"]):
                raise Failure("schema.source")
            if service["kind"] not in {"local", "remote"} or type(service["visible"]) is not bool or type(service["paired"]) is not bool:
                raise Failure("schema.source")
        if meta["data_hash"] != "sha256:" + hashlib.sha256(canonical(data)).hexdigest():
            raise Failure("hash.artifact")
        if artifact["source_binding"]["operation_id"] != meta["tool"]:
            raise Failure("binding.registry")
        return len(data["services"])
    else:
        raise Failure("schema.source")


def verify(bundle: Any, registry: dict[tuple[str, str, int], dict[str, Any]], raw_size: int) -> dict[str, Any]:
    exact_keys(bundle, ROOT_KEYS)
    limits = bundle["limits"]
    exact_keys(limits, LIMIT_KEYS)
    for field, ceiling in HARD_LIMITS.items():
        if type(limits[field]) is not int or not 1 <= limits[field] <= ceiling:
            raise Failure("limits.exceeded")
    check_portable(bundle, 0, limits)
    if (
        raw_size > limits["max_bundle_bytes"]
        or not isinstance(bundle["sources"], list)
        or len(bundle["sources"]) > limits["max_sources"]
        or not isinstance(bundle["artifacts"], list)
        or len(bundle["artifacts"]) > limits["max_sources"] * 3
    ):
        raise Failure("limits.exceeded")
    if bundle["contract"] != "helianthus.platform.synchronized-evidence-bundle.v1" or bundle["schema_version"] != 1:
        raise Failure("schema.bundle")
    if not isinstance(bundle["bundle_id"], str) or not re.fullmatch(r"sebv1:sha256:[0-9a-f]{64}", bundle["bundle_id"]):
        raise Failure("schema.bundle")
    timestamp_ns(bundle["captured_at"])
    validate_capture_window(bundle["capture_window"])
    validate_scope(bundle["scope"])
    if bundle["mask_tier"] != "redacted":
        raise Failure("schema.bundle")
    root_permissions = validate_auth(bundle["auth_scope"])
    validate_refs(bundle["evidence_refs"])
    root_refs = {canonical(ref) for ref in bundle["evidence_refs"]}
    window = bundle["capture_window"]
    if (
        window["pre"]["start_offset_ns"] > window["pre"]["end_offset_ns"]
        or window["pre"]["end_offset_ns"] != window["action"]["start_offset_ns"]
        or window["action"]["start_offset_ns"] > window["action"]["marker_offset_ns"]
        or window["action"]["marker_offset_ns"] > window["action"]["end_offset_ns"]
        or window["action"]["end_offset_ns"] != window["post"]["start_offset_ns"]
        or window["post"]["start_offset_ns"] > window["post"]["end_offset_ns"]
        or window["post"]["end_offset_ns"] - window["pre"]["start_offset_ns"] > limits["max_capture_duration_ns"]
    ):
        raise Failure("schema.bundle")
    for source in bundle["sources"]:
        exact_keys(source, SOURCE_KEYS)
        if source["contract"] != bundle["contract"] or source["schema_version"] != 1:
            raise Failure("schema.bundle")
        if source["phase"] not in PHASE_RANK or source["source_kind"] not in RUNTIME_KINDS:
            raise Failure("schema.bundle")
        if not isinstance(source["source_id"], str) or not re.fullmatch(r"(?:ebus|eebus|cloud)-[0-9a-f]{32}", source["source_id"]):
            raise Failure("schema.bundle")
        validate_binding(source["source_binding"], registry)
        binding = source["source_binding"]
        if binding["runtime_kind"] != source["source_kind"]:
            raise Failure("binding.registry")
        if binding["request_scope"] != {
            "phase": source["phase"],
            "source_kind": source["source_kind"],
            "operation_scope": binding["snapshot_scope"]["selector"],
        }:
            raise Failure("binding.registry")
        expected_operations = {
            "EBUS": ("ebus.v1.snapshot.capture", "SNAPSHOT"),
            "EEBUS": ("eebus.v1.services.list", "LIVE_READ"),
            "CLOUD_APP": ("cloud.precaptured.import", "PRECAPTURED"),
        }
        if (binding["operation_id"], binding["snapshot_scope"]["mode"]) != expected_operations[source["source_kind"]]:
            raise Failure("binding.registry")
        if source["source_kind"] == "EBUS":
            if not binding["source_kind"].startswith("EBUS_"):
                raise Failure("binding.registry")
        elif binding["source_kind"] != source["source_kind"]:
            raise Failure("binding.registry")
        for field in ("capture_window", "mask_tier", "auth_scope"):
            if source["source_binding"][field] != source[field]:
                raise Failure("binding.registry")
        for field in ("capture_window", "scope", "mask_tier", "recorder_version", "replay_version"):
            if source[field] != bundle[field]:
                raise Failure("binding.registry")
        validate_auth(source["auth_scope"], root_permissions)
        validate_refs(source["evidence_refs"])
        if not {canonical(ref) for ref in source["evidence_refs"]} <= root_refs:
            raise Failure("binding.registry")
        if source["artifact_ids"] != sorted(set(source["artifact_ids"])):
            raise Failure("ordering.invalid")
        validate_phase_timing(source, window, limits)
        if source["maximum_skew_ns"] != bundle["clock"]["maximum_skew_ns"]:
            raise Failure("clock.skew")
        identity = source["ebus_identity"]
        if source["source_kind"] == "EBUS":
            validate_identity(identity, source["source_binding"]["source_kind"])
        elif identity is not None:
            raise Failure("schema.bundle")
        if source["source_binding"]["ebus_identity"] != identity:
            raise Failure("schema.bundle")
    for artifact in bundle["artifacts"]:
        exact_keys(artifact, ARTIFACT_KEYS)
        if artifact["contract"] != bundle["contract"] or artifact["schema_version"] != 1:
            raise Failure("schema.bundle")
        timestamp_ns(artifact["source_observed_at"])
        timestamp_ns(artifact["recorder_ingested_at"])
        validate_binding(artifact["source_binding"], registry)
        validate_auth(artifact["auth_scope"], root_permissions)
        validate_refs(artifact["evidence_refs"])
        if not {canonical(ref) for ref in artifact["evidence_refs"]} <= root_refs:
            raise Failure("binding.registry")
        if artifact["source_binding"]["ebus_identity"] != artifact["ebus_identity"]:
            raise Failure("schema.bundle")
    source_order = sorted(bundle["sources"], key=lambda row: (PHASE_RANK[row["phase"]], KIND_RANK[row["source_kind"]], row["source_id"]))
    artifact_order = sorted(bundle["artifacts"], key=lambda row: (PHASE_RANK[row["phase"]], KIND_RANK[row["source_kind"]], row["source_id"], row["artifact_id"]))
    if source_order != bundle["sources"] or artifact_order != bundle["artifacts"]:
        raise Failure("ordering.invalid")
    binding_to_id: dict[bytes, str] = {}
    id_to_binding: dict[str, bytes] = {}
    for source in bundle["sources"]:
        encoded = canonical(source["source_binding"])
        if encoded in binding_to_id and binding_to_id[encoded] != source["source_id"]:
            raise Failure("binding.duplicate")
        if source["source_id"] in id_to_binding and id_to_binding[source["source_id"]] != encoded:
            raise Failure("binding.duplicate")
        binding_to_id[encoded] = source["source_id"]
        id_to_binding[source["source_id"]] = encoded
    validate_clock(bundle)
    validate_privacy(bundle)
    validate_remasking(bundle["artifacts"])
    by_id = {source["source_id"]: source for source in bundle["sources"]}
    referenced: set[str] = set()
    artifact_hashes: list[str] = []
    for artifact in bundle["artifacts"]:
        source = by_id.get(artifact["source_id"])
        if source is None or source["state"] != "PRESENT":
            raise Failure("binding.registry")
        for field in ("source_kind", "phase", "source_contract", "source_schema_version", "source_binding", "ebus_identity", "capture_window", "clock", "scope", "mask_tier", "auth_scope", "recorder_version", "replay_version"):
            if artifact[field] != source[field]:
                raise Failure("binding.registry")
        segment = window[artifact["phase"]]
        if not segment["start_offset_ns"] <= artifact["recorder_ingested_offset_ns"] <= segment["end_offset_ns"]:
            raise Failure("schema.bundle")
        actual_items = validate_source_payload(artifact)
        if artifact["item_count"] != actual_items or actual_items > limits["max_items_per_source"]:
            raise Failure("limits.exceeded")
        encoded_evidence = canonical(artifact["normalized_evidence"])
        if artifact["byte_count"] != len(encoded_evidence) or artifact["byte_count"] > limits["max_artifact_bytes"]:
            raise Failure("limits.exceeded")
        view = {key: value for key, value in artifact.items() if key not in {"artifact_id", "redacted_hash"}}
        hexdigest = digest(ARTIFACT_DOMAIN, view)
        if artifact["artifact_id"] != "seav1:sha256:" + hexdigest or artifact["redacted_hash"] != "sha256:" + hexdigest:
            raise Failure("hash.artifact")
        if artifact["artifact_id"] not in source["artifact_ids"] or artifact["artifact_id"] in referenced:
            raise Failure("binding.duplicate")
        referenced.add(artifact["artifact_id"])
        artifact_hashes.append("sha256:" + hexdigest)
    expected_refs = {item for source in bundle["sources"] for item in source["artifact_ids"]}
    if referenced != expected_refs:
        raise Failure("binding.duplicate")
    view = {key: value for key, value in bundle.items() if key not in {"bundle_id", "bundle_hash"}}
    hexdigest = digest(BUNDLE_DOMAIN, view)
    if bundle["bundle_id"] != "sebv1:sha256:" + hexdigest or bundle["bundle_hash"] != "sha256:" + hexdigest:
        raise Failure("hash.bundle")
    bundle["_verified_artifact_hashes"] = artifact_hashes
    return bundle


def replay(bundle: dict[str, Any]) -> dict[str, Any]:
    artifacts = bundle["artifacts"]
    timestamps = [{
        "event_kind": "ACTION_MARKER", "source_id": None, "artifact_id": None,
        "source_observed_at": None,
        "recorder_observed_at": bundle["capture_window"]["action"]["marker_captured_at"],
        "recorder_offset_ns": bundle["capture_window"]["action"]["marker_offset_ns"],
    }]
    for source in bundle["sources"]:
        if source["acquisition_started_at"] is not None:
            timestamps.extend([
                {
                    "event_kind": "SOURCE_ACQUISITION_START", "source_id": source["source_id"],
                    "artifact_id": None, "source_observed_at": None,
                    "recorder_observed_at": source["acquisition_started_at"],
                    "recorder_offset_ns": source["acquisition_start_offset_ns"],
                },
                {
                    "event_kind": "SOURCE_ACQUISITION_END", "source_id": source["source_id"],
                    "artifact_id": None, "source_observed_at": None,
                    "recorder_observed_at": source["acquisition_ended_at"],
                    "recorder_offset_ns": source["acquisition_end_offset_ns"],
                },
            ])
    for artifact in artifacts:
        timestamps.append({
            "event_kind": "ARTIFACT_INGESTION", "source_id": artifact["source_id"],
            "artifact_id": artifact["artifact_id"],
            "source_observed_at": artifact["source_observed_at"],
            "recorder_observed_at": artifact["recorder_ingested_at"],
            "recorder_offset_ns": artifact["recorder_ingested_offset_ns"],
        })
    hashes = [
        {"kind": "ARTIFACT", "artifact_id": artifact["artifact_id"], "digest": digest(
            ARTIFACT_DOMAIN,
            {key: value for key, value in artifact.items() if key not in {"artifact_id", "redacted_hash"}},
        )}
        for artifact in artifacts
    ]
    for row in hashes:
        row["digest"] = "sha256:" + row["digest"]
    hashes.append({"kind": "BUNDLE", "artifact_id": None, "digest": bundle["bundle_hash"]})
    return {
        "contract": "helianthus.platform.synchronized-evidence-replay.v1",
        "schema_version": 1,
        "bundle_id": bundle["bundle_id"],
        "raw_normalized_evidence": [{
            "artifact_id": artifact["artifact_id"],
            "source_binding": artifact["source_binding"],
            "source_observed_at": artifact["source_observed_at"],
            "normalized_evidence": artifact["normalized_evidence"],
        } for artifact in artifacts],
        "captured_timestamps": timestamps,
        "terminal_states": [{
            "source_id": source["source_id"], "phase": source["phase"],
            "state": source["state"], "error_category": source["error_category"],
        } for source in bundle["sources"]],
        "redacted_hashes": hashes,
        "future_candidate_inputs": [{
            "artifact_id": artifact["artifact_id"], "source_id": artifact["source_id"],
            "source_binding": artifact["source_binding"],
            "evidence_refs": artifact["evidence_refs"],
            "redacted_hash": artifact["redacted_hash"],
        } for artifact in artifacts],
    }


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("command", choices=("verify", "replay"))
    parser.add_argument("--bundle", required=True, type=pathlib.Path)
    parser.add_argument("--registry", required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        if args.bundle.stat().st_size > HARD_LIMITS["max_bundle_bytes"]:
            raise Failure("limits.exceeded")
        raw = args.bundle.read_bytes()
        preflight_json_bytes(raw)
        bundle = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
        registry = load_registry(args.registry)
        verified = verify(bundle, registry, len(raw))
        if args.command == "verify":
            sys.stdout.write("ok\n")
        else:
            sys.stdout.write(canonical(replay(verified)).decode("utf-8") + "\n")
        return 0
    except Failure as error:
        sys.stdout.write(error.category + "\n")
        return 1
    except Exception:
        sys.stdout.write("schema.bundle\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
