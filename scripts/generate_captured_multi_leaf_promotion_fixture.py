#!/usr/bin/env python3
"""Generate deterministic MSP-085-LIVE-R2 conformance fixtures."""

from __future__ import annotations

import importlib.util
import json
import pathlib
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_captured_multi_leaf_promotion.py"
REGISTRY = ROOT / "docs/platform/schemas/leaf-promotion-captured-multi-leaf-registry-v1.json"
FIXTURE = ROOT / "docs/platform/fixtures/leaf-promotion-captured-multi-leaf/v1"


def validator_module():
    spec = importlib.util.spec_from_file_location("multi_leaf_validator", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(character: str) -> str:
    return "sha256:" + character * 64


def encoded(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        + b"\n"
    )


def typed_numeric(number: int, scale: int) -> dict[str, object]:
    return {
        "kind": "NUMERIC",
        "decimal": {"number": number, "scale": scale},
        "enum": None,
        "boolean": None,
        "string": None,
    }


def typed_enum(value: str) -> dict[str, object]:
    return {
        "kind": "ENUM",
        "decimal": None,
        "enum": value,
        "boolean": None,
        "string": None,
    }


def typed_boolean(value: bool) -> dict[str, object]:
    return {
        "kind": "BOOLEAN",
        "decimal": None,
        "enum": None,
        "boolean": value,
        "string": None,
    }


def typed_string(value: str) -> dict[str, object]:
    return {
        "kind": "STRING",
        "decimal": None,
        "enum": None,
        "boolean": None,
        "string": value,
    }


def ebus_identity(module, candidate: dict[str, Any]) -> dict[str, Any]:
    selector = (
        candidate["ebus_fallback"]
        if candidate["candidate_id"] == "m7-candidate-0006"
        else candidate["ebus_selector"]
    )
    assert isinstance(selector, dict)
    identity = {
        **selector,
        "target_pseudonym": "target-" + "1" * 32,
        "target_address": 21,
        "source_address": 253,
        "selector_hash": sha("0"),
    }
    domain = (
        module.EBUS_SELECTOR_DOMAIN
        if identity["family"] == "B524"
        else module.EBUS_B555_SELECTOR_DOMAIN
    )
    identity["selector_hash"] = module.digest(
        domain,
        {key: value for key, value in identity.items() if key != "selector_hash"},
    )
    return identity


def eebus_identity(module, candidate: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(candidate["candidate_id"])
    source = candidate["eebus_source"]
    assert isinstance(source, dict)
    index = int(candidate_id[-4:])
    identity = {
        "service_id": "sanitized-service-v1",
        "device_address": "sanitized-device-v1",
        "entity_address": [1000 + index],
        "feature_address": 100 + index,
        **source,
        "source_profile_hash": module.digest(module.SOURCE_PROFILE_DOMAIN, source),
        "identity_hash": sha("0"),
    }
    identity["identity_hash"] = module.digest(
        module.EEBUS_IDENTITY_DOMAIN,
        {key: value for key, value in identity.items() if key != "identity_hash"},
    )
    return identity


def sample(
    module,
    source: str,
    timestamp: str,
    raw_value: dict[str, object],
    value: dict[str, object],
    unit: str | None,
    window: dict[str, object],
    suffix: str,
) -> dict[str, object]:
    return {
        "source": source,
        "observed_at": timestamp,
        "valid": True,
        "capture_generation": window["capture_generation"],
        "poll_id": "poll-" + suffix if source == "EBUS" else None,
        "poll_generation": window["ebus_poll_generation"] if source == "EBUS" else None,
        "runtime_epoch": window["eebus_runtime_epoch"] if source == "EEBUS" else None,
        "connection_generation": (
            window["connection_generation"] if source == "EEBUS" else None
        ),
        "raw_hash": module.digest(module.RAW_VALUE_DOMAIN, raw_value),
        "raw_value": raw_value,
        "value": value,
        "unit": unit,
    }


def comparator(module, expected: dict[str, Any], outcome: str) -> dict[str, Any]:
    source = expected["eebus_source"]
    assert isinstance(source, dict)
    if expected["comparator_class"] == "NUMERIC_DECLARED_GRANULARITY":
        return {
            "class": expected["comparator_class"],
            "declared_spine_step": source["declared_constraints"]["step"],
            "delta": None,
            "conversion": expected["conversion"],
            "mapping_hash": None,
            "outcome": outcome,
        }
    return {
        "class": expected["comparator_class"],
        "declared_spine_step": None,
        "delta": None,
        "conversion": None,
        "mapping_hash": module.digest(module.MAPPING_DOMAIN, expected["mapping_profile"]),
        "outcome": outcome,
    }


def cross_values(
    expected: dict[str, Any], position: int
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, int] | None]:
    candidate_id = expected["candidate_id"]
    if expected["comparator_class"] == "NUMERIC_DECLARED_GRANULARITY":
        if candidate_id == "m7-candidate-0018":
            ebus = typed_numeric(125 if position == 0 else 13, -1 if position == 0 else 0)
            eebus = typed_numeric(13 if position == 0 else 135, 0 if position == 0 else -1)
            delta = {"number": 5, "scale": -1}
        else:
            values = {
                "m7-candidate-0005": (45, 0),
                "m7-candidate-0006": (55, 0),
                "m7-candidate-0010": (21, 0),
                "m7-candidate-0011": (21, 0),
                "m7-candidate-0014": (22, 0),
                "m7-candidate-0015": (22, 0),
            }
            number, scale = values[candidate_id]
            ebus = typed_numeric(number, scale)
            eebus = typed_numeric(number, scale)
            delta = {"number": 0, "scale": 0}
        return ebus, ebus, eebus, eebus, delta
    if expected["comparator_class"] == "ENUM_EXACT_MAPPING":
        decoded = typed_enum("off")
        return typed_numeric(0, 0), decoded, typed_numeric(2, 0), decoded, None
    decoded = typed_boolean(False)
    return typed_numeric(0, 0), decoded, typed_boolean(False), decoded, None


def native_value(expected: dict[str, Any]) -> dict[str, object]:
    if expected["validation_mode"] == "EEBUS_NATIVE_CAPABILITY":
        return typed_boolean(False)
    values = {
        "m7-candidate-0019": "sanitized-brand-v1",
        "m7-candidate-0020": "sanitized-vendor-v1",
        "m7-candidate-0021": "sanitized-zone-one",
        "m7-candidate-0022": "sanitized-zone-two",
    }
    return typed_string(values[expected["candidate_id"]])


def cross_assessment(
    module,
    registry: dict[str, Any],
    expected: dict[str, Any],
    candidate: dict[str, Any],
    window: dict[str, Any],
    position: int,
) -> dict[str, Any]:
    prefix = "2026-08-11T10:00:05" if position == 0 else "2026-08-11T10:05:05"
    suffix = expected["candidate_id"][-4:] + ("-pre" if position == 0 else "-post")
    ebus_raw, ebus_value, eebus_raw, eebus_value, delta = cross_values(
        expected, position
    )
    comparison = comparator(module, expected, "MATCH")
    comparison["delta"] = delta
    source = expected["eebus_source"]
    assert isinstance(source, dict)
    return {
        "window_id": window["window_id"],
        "ebus_sample": sample(
            module,
            "EBUS",
            prefix + "Z",
            ebus_raw,
            ebus_value,
            expected["conversion"]["source_unit"]
            if expected["conversion"] is not None
            else source["unit"],
            window,
            suffix,
        ),
        "eebus_sample": sample(
            module,
            "EEBUS",
            prefix + ".100000000Z",
            eebus_raw,
            eebus_value,
            source["unit"],
            window,
            suffix,
        ),
        "observed_ebus_identity_hash": candidate["ebus_identity"]["selector_hash"],
        "observed_eebus_identity_hash": candidate["eebus_identity"]["identity_hash"],
        "conflict_samples": [],
        "skew_ns": 100_000_000,
        "max_skew_ns": registry["capture_limits"]["max_skew_ns"],
        "age_ns": 5_000_000_000,
        "max_age_ns": registry["capture_limits"]["max_age_ns"],
        "comparator": comparison,
    }


def native_assessment(
    module,
    registry: dict[str, Any],
    expected: dict[str, Any],
    candidate: dict[str, Any],
    window: dict[str, Any],
    position: int,
) -> dict[str, Any]:
    prefix = "2026-08-11T10:00:05" if position == 0 else "2026-08-11T10:05:05"
    suffix = expected["candidate_id"][-4:] + ("-pre" if position == 0 else "-post")
    value = native_value(expected)
    mapping_hash = (
        module.digest(module.MAPPING_DOMAIN, expected["eebus_source"]["exact_mapping"])
        if expected["validation_mode"] == "EEBUS_NATIVE_CAPABILITY"
        else None
    )
    return {
        "window_id": window["window_id"],
        "ebus_sample": None,
        "eebus_sample": sample(
            module,
            "EEBUS",
            prefix + ".100000000Z",
            value,
            value,
            expected["eebus_source"]["unit"],
            window,
            suffix,
        ),
        "observed_ebus_identity_hash": None,
        "observed_eebus_identity_hash": candidate["eebus_identity"]["identity_hash"],
        "conflict_samples": [],
        "skew_ns": None,
        "max_skew_ns": registry["capture_limits"]["max_skew_ns"],
        "age_ns": 4_900_000_000,
        "max_age_ns": registry["capture_limits"]["max_age_ns"],
        "comparator": {
            "class": expected["comparator_class"],
            "declared_spine_step": None,
            "delta": None,
            "conversion": None,
            "mapping_hash": mapping_hash,
            "outcome": "NATIVE_VALID",
        },
    }


def build_campaign(module, registry: dict[str, Any]) -> dict[str, Any]:
    windows: list[dict[str, Any]] = [
        {
            "window_id": "window-pre-restart",
            "phase": "PRE_RESTART",
            "started_at": "2026-08-11T10:00:00Z",
            "ended_at": "2026-08-11T10:00:10Z",
            "capture_generation": "capture-pre",
            "process_instance_hash": sha("1"),
            "local_identity_hash": sha("3"),
            "trust_state_hash": sha("4"),
            "peer_binding_hash": sha("5"),
            "admitted_source": 253,
            "eebus_runtime_epoch": 2,
            "connection_generation": 94,
            "ebus_poll_generation": "poll-generation-pre",
            "m8_no_drift": True,
            "rollback_exact": True,
        },
        {
            "window_id": "window-post-restart",
            "phase": "POST_RESTART",
            "started_at": "2026-08-11T10:05:00Z",
            "ended_at": "2026-08-11T10:05:10Z",
            "capture_generation": "capture-post",
            "process_instance_hash": sha("2"),
            "local_identity_hash": sha("3"),
            "trust_state_hash": sha("4"),
            "peer_binding_hash": sha("5"),
            "admitted_source": 253,
            "eebus_runtime_epoch": 2,
            "connection_generation": 1,
            "ebus_poll_generation": "poll-generation-post",
            "m8_no_drift": True,
            "rollback_exact": True,
        },
    ]
    candidates: list[dict[str, Any]] = []
    for expected in registry["candidate_catalog"]:
        candidate = {
            "candidate_id": expected["candidate_id"],
            "fact_hash": expected["fact_hash"],
            "source_status": expected["source_status"],
            "retirement_state": expected["retirement_state"],
            "semantic_path": expected["semantic_path"],
            "validation_mode": expected["validation_mode"],
            "comparator_class": expected["comparator_class"],
            "ebus_identity": None,
            "eebus_identity": None,
            "assessments": [],
            "decision": "WITHHELD",
            "terminal_state": expected["terminal_state"],
            "visibility": "RAW_DEBUG_ONLY",
            "dossier_hash": None,
        }
        if expected["protocol_eligibility"] == "TERMINAL":
            candidates.append(candidate)
            continue

        candidate["eebus_identity"] = eebus_identity(module, expected)
        candidate["decision"] = "PROMOTED"
        candidate["terminal_state"] = None
        candidate["visibility"] = "LOCKED_NOT_EXPOSED"
        if expected["protocol_eligibility"] == "CROSS_PROTOCOL_EQUIVALENCE":
            candidate["ebus_identity"] = ebus_identity(module, expected)
            candidate["assessments"] = [
                cross_assessment(
                    module, registry, expected, candidate, window, position
                )
                for position, window in enumerate(windows)
            ]
        else:
            candidate["assessments"] = [
                native_assessment(
                    module, registry, expected, candidate, window, position
                )
                for position, window in enumerate(windows)
            ]
        candidate["dossier_hash"] = module.digest(
            module.DOSSIER_DOMAIN, module._candidate_payload(candidate)
        )
        candidates.append(candidate)

    campaign = {
        "contract": "helianthus.platform.leaf-promotion-captured-multi-leaf.v1",
        "schema_version": 1,
        "profile": "CAPTURED_RUNTIME_MULTI_LEAF_V1",
        "evidence_mode": "SANITIZED_CONFORMANCE",
        "export_tier": "PRIVATE_OPERATOR",
        "provenance": registry["sanitized_provenance"],
        "source_bindings": {
            "registry_sha256": module.PINNED_REGISTRY_SHA256,
            "docs_eebus_commit": registry["docs_eebus_source_commit"],
            "m7_graph_id": "dcfgv1:captured-campaign",
            "m7_graph_hash": sha("a"),
            "m7_graph_bytes_hash": sha("1"),
            "m7_replay_id": "dcfrv1:captured-campaign",
            "m7_replay_hash": sha("2"),
            "m7_replay_bytes_hash": sha("3"),
            "m7_status_id": "dcfpsv1:captured-campaign",
            "m7_status_hash": sha("b"),
            "m7_status_bytes_hash": sha("4"),
            "m8_evidence_id": "mrcv1:captured-campaign",
            "m8_evidence_hash": sha("c"),
            "m8_evidence_bytes_hash": sha("5"),
            "m8_report_id": "mrcrv1:captured-campaign",
            "m8_report_hash": sha("d"),
            "m8_report_bytes_hash": sha("6"),
            "replay_hash": sha("0"),
        },
        "windows": windows,
        "candidates": candidates,
        "campaign_hash": sha("0"),
    }
    campaign["source_bindings"]["replay_hash"] = module.replay_hash(campaign)
    campaign["campaign_hash"] = module.digest(
        module.CAMPAIGN_DOMAIN,
        {key: value for key, value in campaign.items() if key != "campaign_hash"},
    )
    module.verify_private(campaign, registry)
    return campaign


def write(path: pathlib.Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


def main() -> None:
    module = validator_module()
    registry, _ = module.load_json(REGISTRY)
    module.registry_value(REGISTRY)
    campaign = build_campaign(module, registry)
    private_raw = encoded(campaign)
    public = module.derive_public(campaign, registry, private_raw)
    write(FIXTURE / "positive/private-campaign.json", campaign)
    write(FIXTURE / "positive/public-result.json", public)
    negatives = {
        "granularity-substitution.json": ("GRANULARITY_SUBSTITUTION", "comparator.invalid"),
        "missing-granularity.json": ("MISSING_GRANULARITY", "schema.private"),
        "identity-mismatch.json": ("IDENTITY_MISMATCH", "identity.binding"),
        "generation-change.json": ("GENERATION_CHANGE", "sample.invalid"),
        "skew-exceeded.json": ("SKEW_EXCEEDED", "sample.invalid"),
        "stale-sample.json": ("STALE_SAMPLE", "sample.invalid"),
        "missing-sample.json": ("MISSING_SAMPLE", "identity.binding"),
        "conflict-as-match.json": ("CONFLICT_AS_MATCH", "state.invalid"),
        "replay-drift.json": ("REPLAY_DRIFT", "hash.replay"),
        "public-identity-leak.json": ("PUBLIC_IDENTITY_LEAK", "schema.public"),
        "public-secret-leak.json": ("PUBLIC_SECRET_LEAK", "schema.public"),
    }
    for name, (mutation, category) in negatives.items():
        write(
            FIXTURE / "negative" / name,
            {
                "contract": "helianthus.platform.leaf-promotion-captured-multi-leaf-negative.v1",
                "mutation": mutation,
                "expected_category": category,
            },
        )


if __name__ == "__main__":
    main()
