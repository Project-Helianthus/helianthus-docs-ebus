#!/usr/bin/env python3
"""Generate deterministic MSP-085-LIVE-R2 conformance fixtures."""

from __future__ import annotations

import importlib.util
import json
import pathlib


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


def typed_numeric(number: int, scale: int) -> dict[str, object]:
    return {"kind": "NUMERIC", "decimal": {"number": number, "scale": scale}, "enum": None, "boolean": None}


def eebus_identity(candidate: dict[str, object]) -> dict[str, object]:
    candidate_id = str(candidate["candidate_id"])
    descriptor = str(candidate["descriptor"])
    index = int(candidate_id[-4:])
    entity = [1000 + index]
    feature_type = "Generic"
    feature_address = 100 + index
    function = "sanitizedConformanceRead"
    return {
        "service_id": "sanitized-service-v1",
        "device_address": "sanitized-device-v1",
        "entity_address": entity,
        "feature_address": feature_address,
        "feature_type": feature_type,
        "feature_role": "server",
        "function": function,
        "field_path": [descriptor],
        "descriptor": descriptor,
        "unit": "degC" if candidate["comparator_class"] == "NUMERIC_DECLARED_GRANULARITY" else "unitless",
        "identity_hash": sha("8"),
    }


def sample(source: str, timestamp: str, value: dict[str, object], window: dict[str, object], suffix: str) -> dict[str, object]:
    return {
        "source": source,
        "observed_at": timestamp,
        "valid": True,
        "capture_generation": "capture-" + suffix,
        "poll_id": "poll-" + suffix if source == "EBUS" else None,
        "runtime_epoch": window["eebus_runtime_epoch"] if source == "EEBUS" else None,
        "connection_generation": window["connection_generation"] if source == "EEBUS" else None,
        "raw_hash": sha("6" if source == "EBUS" else "7"),
        "value": value,
        "unit": "degC",
    }


def build_campaign(module, registry: dict[str, object]) -> dict[str, object]:
    windows = [
        {
            "window_id": "window-pre-restart",
            "phase": "PRE_RESTART",
            "started_at": "2026-08-11T10:00:00Z",
            "ended_at": "2026-08-11T10:00:10Z",
            "process_instance_hash": sha("1"),
            "local_identity_hash": sha("3"),
            "trust_state_hash": sha("4"),
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
            "process_instance_hash": sha("2"),
            "local_identity_hash": sha("3"),
            "trust_state_hash": sha("4"),
            "admitted_source": 253,
            "eebus_runtime_epoch": 2,
            "connection_generation": 1,
            "ebus_poll_generation": "poll-generation-post",
            "m8_no_drift": True,
            "rollback_exact": True,
        },
    ]
    candidates: list[dict[str, object]] = []
    missing_numeric = {5, 6, 10, 11, 14, 15}
    missing_mapped = {7, 9, 12, 16}
    for expected in registry["candidate_catalog"]:
        index = int(expected["candidate_id"][-4:])
        if expected["source_status"] == "WITHHELD":
            candidate = {
                "candidate_id": expected["candidate_id"],
                "fact_hash": expected["fact_hash"],
                "source_status": expected["source_status"],
                "semantic_path": expected["semantic_path"],
                "comparator_class": expected["comparator_class"],
                "ebus_identity": None,
                "eebus_identity": None,
                "assessments": [],
                "decision": "WITHHELD",
                "terminal_state": expected["terminal_state"],
                "visibility": "RAW_DEBUG_ONLY",
                "dossier_hash": None,
            }
        else:
            terminal = "MISSING" if index in missing_numeric | missing_mapped else "NOT_COMPARABLE"
            candidate = {
                "candidate_id": expected["candidate_id"],
                "fact_hash": expected["fact_hash"],
                "source_status": expected["source_status"],
                "semantic_path": expected["semantic_path"],
                "comparator_class": expected["comparator_class"],
                "ebus_identity": None,
                "eebus_identity": eebus_identity(expected),
                "assessments": [],
                "decision": "WITHHELD",
                "terminal_state": terminal,
                "visibility": "RAW_DEBUG_ONLY",
                "dossier_hash": None,
            }
        candidates.append(candidate)

    promoted = candidates[-1]
    promoted["ebus_identity"] = {
        "family": "B524",
        "target_address": 254,
        "source_address": 253,
        "opcode": 2,
        "group": 254,
        "instance": 254,
        "register": 65535,
        "register_id": None,
        "selector_hash": sha("5"),
    }
    promoted["decision"] = "PROMOTED"
    promoted["terminal_state"] = None
    promoted["visibility"] = "LOCKED_NOT_EXPOSED"
    promoted["assessments"] = []
    for position, window in enumerate(windows):
        prefix = "2026-08-11T10:00:05" if position == 0 else "2026-08-11T10:05:05"
        ebus = sample("EBUS", prefix + "Z", typed_numeric(13125 if position == 0 else 13375, -3), window, "pre" if position == 0 else "post")
        eebus = sample("EEBUS", prefix + ".100000000Z", typed_numeric(13 if position == 0 else 135, 0 if position == 0 else -1), window, "pre" if position == 0 else "post")
        promoted["assessments"].append(
            {
                "window_id": window["window_id"],
                "ebus_sample": ebus,
                "eebus_sample": eebus,
                "skew_ns": 100_000_000,
                "max_skew_ns": 1_000_000_000,
                "age_ns": 5_000_000_000,
                "max_age_ns": 10_000_000_000,
                "comparator": {
                    "class": "NUMERIC_DECLARED_GRANULARITY",
                    "declared_spine_step": {"number": 5, "scale": -1},
                    "delta": {"number": 125, "scale": -3},
                    "conversion": {
                        "mode": "IDENTITY",
                        "source_unit": "degC",
                        "target_unit": "degC",
                        "scale": {"number": 1, "scale": 0},
                        "offset": {"number": 0, "scale": 0},
                    },
                    "mapping_hash": None,
                    "outcome": "MATCH",
                },
            }
        )
    promoted["dossier_hash"] = module.digest(module.DOSSIER_DOMAIN, module._candidate_payload(promoted))

    campaign: dict[str, object] = {
        "contract": "helianthus.platform.leaf-promotion-captured-multi-leaf.v1",
        "schema_version": 1,
        "profile": "CAPTURED_RUNTIME_MULTI_LEAF_V1",
        "evidence_mode": "SANITIZED_CONFORMANCE",
        "export_tier": "PRIVATE_OPERATOR",
        "source_bindings": {
            "docs_eebus_commit": registry["docs_eebus_source_commit"],
            "m7_graph_id": "dcfgv1:captured-campaign",
            "m7_graph_hash": sha("a"),
            "m7_status_id": "dcfpsv1:captured-campaign",
            "m7_status_hash": sha("b"),
            "m8_evidence_id": "mrcv1:captured-campaign",
            "m8_evidence_hash": sha("c"),
            "m8_report_id": "mrcrv1:captured-campaign",
            "m8_report_hash": sha("d"),
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
    path.write_bytes(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii") + b"\n")


def main() -> None:
    module = validator_module()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    campaign = build_campaign(module, registry)
    public = module.derive_public(campaign, registry)
    write(FIXTURE / "positive/private-campaign.json", campaign)
    write(FIXTURE / "positive/public-result.json", public)
    negatives = {
        "granularity-substitution.json": ("GRANULARITY_SUBSTITUTION", "comparator.invalid"),
        "missing-granularity.json": ("MISSING_GRANULARITY", "comparator.invalid"),
        "identity-mismatch.json": ("IDENTITY_MISMATCH", "identity.binding"),
        "generation-change.json": ("GENERATION_CHANGE", "sample.invalid"),
        "skew-exceeded.json": ("SKEW_EXCEEDED", "sample.invalid"),
        "stale-sample.json": ("STALE_SAMPLE", "sample.invalid"),
        "missing-sample.json": ("MISSING_SAMPLE", "comparator.invalid"),
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
