#!/usr/bin/env python3
"""Fail-closed verifier for the MSP-08 EEBUS-G18 coexistence contract."""

from __future__ import annotations

import argparse
import base64
import copy
import datetime as dt
import hashlib
import ipaddress
import json
import os
import pathlib
import re
import stat
import sys
from typing import Any


SCRIPT_ROOT = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))
import validate_candidate_fact_graph as candidate
import project_candidate_fact_public_status as status_projector


EVIDENCE_CONTRACT = "helianthus.platform.multi-runtime-coexistence-evidence.v1"
REGISTRY_CONTRACT = "helianthus.platform.multi-runtime-coexistence-registry.v1"
REPORT_CONTRACT = "helianthus.platform.multi-runtime-coexistence-report.v1"
RAW_PAYLOAD_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-RAW-PAYLOAD:V1"
SHAPE_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-PAYLOAD-SHAPE:V1"
CANONICAL_PAYLOAD_DOMAIN = (
    b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-CANONICAL-PAYLOAD:V1"
)
PROFILE_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-NORMALIZATION:V1"
CLOCK_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-CLOCK:V1"
BUILD_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-BUILD:V1"
CONFIG_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-CONFIG:V1"
AUTH_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-AUTH:V1"
M7_STATUS_PROJECTION_DOMAIN = (
    b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-M7-PUBLIC-STATUS:V1"
)
RESTART_PROCESS_EVENT_DOMAIN = (
    b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-RESTART-PROCESS-EVENT:V1"
)
RESTART_SNAPSHOT_DOMAIN = (
    b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-RESTART-SNAPSHOT:V1"
)
RESTART_SESSION_EVENT_DOMAIN = (
    b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-RESTART-SESSION-EVENT:V1"
)
RESTART_TRUST_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-RESTART-TRUST:V1"
RESTART_PEER_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-RESTART-PEER:V1"
EVIDENCE_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-EVIDENCE:V1"
REPORT_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-REPORT:V1"
SAFE_INTEGER = 9_007_199_254_740_991
BASELINE_SOURCE_SHA = "ff511b035b85aef6123fb0853bb3d2f3af6fc01e"
EXPECTED_REGISTRY_SHA256 = "8fab50c488cf99a5f6c29cb8cddc41df9728b5c5edde99e3c1e58d13c9f8407b"
READ_ONLY_PERMISSIONS = [
    "read:ebus",
    "read:eebus-v1-contract",
    "read:graphql",
    "read:portal-bootstrap",
    "read:debug",
]
APPROVED_M8_EEBUS_TOOLS = [
    "eebus.v1.runtime.status.get",
    "eebus.v1.services.list",
    "eebus.v1.services.get",
    "eebus.v1.sessions.list",
    "eebus.v1.sessions.get",
    "eebus.v1.topology.get",
    "eebus.v1.snapshot.capture",
    "eebus.v1.snapshot.drop",
    "eebus.v1.pairing.status.get",
]
APPROVED_M8_TOOL_INVENTORY = [
    "ebus.v1.registry.devices.list",
    "ebus.v1.semantic.snapshot.get",
    *APPROVED_M8_EEBUS_TOOLS,
]
APPROVED_M8_EEBUS_CONTRACT_FIELDS = {
    "namespace",
    "public_v2",
    "schema_digest",
    "version",
}
SOURCE_CAPTURE_CONTRACT = "helianthus.platform.multi-runtime-source-capture-manifest.v1"
SOURCE_CAPTURE_INPUT_ID = "source:capture-manifest"
SOURCE_CAPTURE_INPUT_KIND = "SOURCE_CAPTURE_MANIFEST"
SOURCE_CAPTURE_POLICY = "M8_PROTECTED_VIEWS_SINGLE_WINDOW_V1"
SOURCE_CAPTURE_INPUTS = {
    "tools.list": "READ_ONLY_TEST_MCP",
    "ebus.devices": "PUBLIC_LOOPBACK_MCP",
    "ebus.semantic": "PUBLIC_LOOPBACK_MCP",
    "ebus.debug": "READ_ONLY_TEST_MCP",
    "eebus.runtime": "OWNER_UNIX_MCP",
    "eebus.services": "OWNER_UNIX_MCP",
    "eebus.sessions": "OWNER_UNIX_MCP",
    "eebus.pairing": "OWNER_UNIX_MCP",
    "eebus.topology": "OWNER_UNIX_MCP",
    "graphql.schema": "PUBLIC_LOOPBACK_GRAPHQL",
    "graphql.values": "PUBLIC_LOOPBACK_GRAPHQL",
    "portal.bootstrap": "PUBLIC_LOOPBACK_HTTP",
    "command.routing": "LOCAL_RUNTIME_OBSERVATION",
    "semantic.registry": "LOCAL_RUNTIME_OBSERVATION",
    "container.inspect": "LOCAL_RUNTIME_ADMIN",
    "capture.timestamp": "LOCAL_CAPTURE_CLOCK",
}
SOURCE_CAPTURE_FILES = {
    "tools.list": "tools-list.json",
    "ebus.devices": "ebus-devices.json",
    "ebus.semantic": "ebus-semantic.json",
    "ebus.debug": "ebus-debug.json",
    "eebus.runtime": "eebus-runtime.json",
    "eebus.services": "eebus-services.json",
    "eebus.sessions": "eebus-sessions.json",
    "eebus.pairing": "eebus-pairing.json",
    "eebus.topology": "eebus-topology.json",
    "graphql.schema": "graphql-schema.json",
    "graphql.values": "graphql-values.json",
    "portal.bootstrap": "portal-bootstrap.json",
    "command.routing": "command-routing.json",
    "semantic.registry": "semantic-registry.json",
    "container.inspect": "container-inspect.json",
    "capture.timestamp": "captured-at.txt",
}
SOURCE_CAPTURE_PHASES = {"before": "PRE_RESTART", "after": "POST_RESTART"}
MAX_SOURCE_INPUT_BYTES = 2_097_152
MAX_SOURCE_TOTAL_BYTES = 16_777_216
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TOKEN_RE = re.compile(r"^[\x20-\x7e]+$")
RFC3339_UTC_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z$"
)
PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN (?:[A-Z0-9]+(?: [A-Z0-9]+)* )?PRIVATE KEY-----",
    re.IGNORECASE,
)
DOTTED_NUMERIC_RUN_RE = re.compile(
    r"(?<![a-z0-9_])[0-9][0-9.]*(?![a-z0-9_])", re.IGNORECASE
)
IPV6_CANDIDATE_RE = re.compile(
    r"(?i)(?<![0-9a-f:])(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}"
    r"(?:%[a-z0-9_.-]+)?(?![0-9a-f:])"
)
MAC_RE = re.compile(
    r"(?i)(?:^|[^0-9a-f])(?:"
    r"(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}|"
    r"[0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4}|"
    r"[0-9a-f]{12}"
    r")(?:$|[^0-9a-f])"
)
SKI_RE = re.compile(r"(?i)(?:^|[^0-9a-f])[0-9a-f]{40}(?:$|[^0-9a-f])")
REDACTED_ID_RE = re.compile(r"^redacted:sha256:[0-9a-f]{12}$")
TOOL_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z0-9]+)+$")
CREDENTIAL_VALUE_RE = re.compile(
    r"(?i)\bauthorization\s*:\s*(?:bearer|basic)\s+[a-z0-9._~+/=-]+"
    r"|\bbearer\s+[a-z0-9._~+/=-]+"
    r"|\b(?:set-cookie|cookie)\s*:\s*\S+"
    r"|\b(?:access[_-]?keys?|api[_-]?keys?|credentials?|passwords?|secrets?|"
    r"session[_-]?cookies?|tokens?)\s*(?::|=|\bis\b)\s*\S+"
    r"|(?<![a-z0-9])(?:[a-z0-9]+[_-])+(?:cookie|credential|password|secret|"
    r"token)\s*[:=]\s*\S+"
    r"|(?<![a-z0-9])private[_-]key\s*[:=]\s*\S+"
)
BASIC_CREDENTIAL_RE = re.compile(r"(?i)\bbasic\s+([a-z0-9+/]+={0,2})(?!\S)")
CANDIDATE_LEAK_COMPACT_NAMES = frozenset(
    {
        "bindingsourcekind",
        "candidate",
        "candidatefact",
        "candidatefacts",
        "candidateid",
        "candidateids",
        "candidatecount",
        "candidatecounts",
        "candidates",
        "candidateref",
        "candidaterefs",
        "candidatestatus",
        "candidatestatuses",
        "conflictstatus",
        "conflict",
        "conflicted",
        "conflicts",
        "comparatoroutcome",
        "debugonly",
        "draftunit",
        "draftvalue",
        "errorcategory",
        "evidencedigests",
        "evidencerefs",
        "facthash",
        "facthashes",
        "identityfamily",
        "nativeevidencedigests",
        "nativeevidencerefs",
        "proposedpath",
        "rawonlycount",
        "rawonlycounts",
        "rawonly",
        "sourcecontract",
        "sourceid",
        "sourceschemaversion",
        "sourceterminal",
        "sourceterminals",
        "sourcebundleid",
        "terminalnegativestate",
        "terminalnegativestates",
        "retesttrigger",
        "visibilitychannel",
        "withheld",
        "withheldcount",
        "withheldcounts",
    }
)
CANDIDATE_LEAK_TOKEN_PATTERNS = frozenset(
    {
        ("binding", "source", "kind"),
        ("candidate",),
        ("candidate", "fact"),
        ("candidate", "facts"),
        ("candidate", "count"),
        ("candidate", "counts"),
        ("candidate", "id"),
        ("candidate", "ids"),
        ("candidate", "ref"),
        ("candidate", "refs"),
        ("candidate", "status"),
        ("candidate", "statuses"),
        ("candidates",),
        ("conflict", "status"),
        ("conflict",),
        ("conflicted",),
        ("conflicts",),
        ("comparator", "outcome"),
        ("debug", "only"),
        ("draft", "unit"),
        ("draft", "value"),
        ("error", "category"),
        ("evidence", "digests"),
        ("evidence", "refs"),
        ("fact", "hash"),
        ("fact", "hashes"),
        ("identity", "family"),
        ("native", "evidence", "digests"),
        ("native", "evidence", "refs"),
        ("proposed", "path"),
        ("raw", "only", "count"),
        ("raw", "only", "counts"),
        ("raw", "only"),
        ("source", "contract"),
        ("source", "id"),
        ("source", "kind"),
        ("source", "schema", "version"),
        ("source", "terminal"),
        ("source", "terminals"),
        ("source", "bundle", "id"),
        ("terminal", "negative", "state"),
        ("terminal", "negative", "states"),
        ("retest", "trigger"),
        ("visibility", "channel"),
        ("withheld",),
    }
)
PUBLIC_IDENTITY_GENERIC_TOKENS = frozenset(
    {
        "address",
        "addresses",
        "device",
        "endpoint",
        "endpoints",
        "host",
        "hostname",
        "identifier",
        "identifiers",
        "identities",
        "identity",
        "ip",
        "ipv4",
        "ipv6",
        "selector",
        "selectors",
        "serial",
        "serials",
        "ski",
        "skis",
        "uid",
        "uids",
    }
)
PUBLIC_IDENTITY_PREFIXES = frozenset(
    {
        "auth",
        "client",
        "device",
        "eebus",
        "endpoint",
        "entity",
        "feature",
        "ip",
        "mac",
        "peer",
        "remote",
        "serial",
        "service",
        "session",
        "ship",
        "source",
        "spine",
        "target",
        "unique",
    }
)
PUBLIC_IDENTITY_SUFFIXES = frozenset(
    {
        "address",
        "addresses",
        "entities",
        "entity",
        "device",
        "devices",
        "feature",
        "features",
        "id",
        "identifier",
        "identifiers",
        "identities",
        "identity",
        "ids",
        "kind",
        "kinds",
        "number",
        "numbers",
        "node",
        "nodes",
        "path",
        "paths",
        "peer",
        "peers",
        "selector",
        "selectors",
        "serial",
        "serials",
        "service",
        "services",
        "ski",
        "skis",
        "source",
        "sources",
        "subject",
        "subjects",
        "target",
        "targets",
        "uid",
        "uids",
    }
)
PUBLIC_IDENTITY_HASH_ROOTS = frozenset(
    {
        "device",
        "eebus",
        "endpoint",
        "entity",
        "feature",
        "peer",
        "remote",
        "service",
        "session",
        "ship",
        "ski",
        "spine",
    }
)
PUBLIC_IDENTITY_COMPACT_NAMES = frozenset(
    {
        "authsubject",
        "id",
        "ids",
        "ip",
        "ipv4",
        "ipv6",
        "remoteshipid",
        "remoteski",
        "viadevice",
    }
    | {
        prefix + suffix
        for prefix in PUBLIC_IDENTITY_PREFIXES
        for suffix in PUBLIC_IDENTITY_SUFFIXES
    }
)
SENSITIVE_KEY_COMPACT_NAMES = frozenset(
    {
        "accesskey",
        "accesskeyid",
        "accesskeys",
        "apikey",
        "apikeys",
        "authheader",
        "authorization",
        "credential",
        "credentials",
        "encryptionkey",
        "keymaterial",
        "password",
        "passwords",
        "passphrase",
        "passphrases",
        "presharedkey",
        "privatekey",
        "psk",
        "secret",
        "secrets",
        "sessioncookie",
        "signingkey",
        "tlskey",
        "token",
        "tokens",
        "truststore",
    }
)
SENSITIVE_KEY_TOKEN_PATTERNS = frozenset(
    {
        ("access", "key"),
        ("access", "keys"),
        ("api", "key"),
        ("api", "keys"),
        ("auth", "header"),
        ("authorization",),
        ("cookie",),
        ("cookies",),
        ("credential",),
        ("credentials",),
        ("encryption", "key"),
        ("key", "material"),
        ("key", "materials"),
        ("password",),
        ("passwords",),
        ("passphrase",),
        ("passphrases",),
        ("pre", "shared", "key"),
        ("private", "key"),
        ("private", "keys"),
        ("psk",),
        ("secret",),
        ("secrets",),
        ("session", "cookie"),
        ("signing", "key"),
        ("tls", "key"),
        ("token",),
        ("tokens",),
        ("trust", "store"),
        ("trust", "stores"),
    }
)
HARD_LIMITS = {
    "max_evidence_bytes": 2_097_152,
    "max_depth": 32,
    "max_runs": 8,
    "max_views_per_run": 16,
    "max_inputs_per_run": 27,
    "max_internal_facts_per_run": 64,
    "max_payload_bytes": 262_144,
    "max_string_bytes": 4_096,
    "max_total_members": 65_536,
    "max_total_list_items": 32_768,
}


class Failure(Exception):
    pass


def fail(category: str) -> None:
    raise Failure(category)


def canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest(domain: bytes, value: Any) -> str:
    return "sha256:" + hashlib.sha256(domain + b"\0" + canonical(value)).hexdigest()


def _bounded_preflight(raw: bytes) -> None:
    if len(raw) > HARD_LIMITS["max_evidence_bytes"]:
        fail("limits.exceeded")
    depth = 0
    members = 0
    items = 0
    in_string = False
    escaped = False
    string_bytes = 0
    for byte in raw:
        if in_string:
            if escaped:
                escaped = False
                string_bytes += 1
            elif byte == 0x5C:
                escaped = True
                string_bytes += 1
            elif byte == 0x22:
                in_string = False
            else:
                string_bytes += 1
            if string_bytes > HARD_LIMITS["max_string_bytes"]:
                fail("limits.exceeded")
            continue
        if byte == 0x22:
            in_string = True
            string_bytes = 0
        elif byte in (0x7B, 0x5B):
            depth += 1
            if depth > HARD_LIMITS["max_depth"]:
                fail("limits.exceeded")
        elif byte in (0x7D, 0x5D):
            depth -= 1
        elif byte == 0x3A:
            members += 1
            if members > HARD_LIMITS["max_total_members"]:
                fail("limits.exceeded")
        elif byte == 0x2C:
            items += 1
            if items > HARD_LIMITS["max_total_list_items"]:
                fail("limits.exceeded")


def load_json(path: pathlib.Path, category: str, *, bounded: bool = False) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError:
        fail(category)
    if bounded:
        _bounded_preflight(raw)
    if re.search(rb"(?<![0-9A-Za-z_])-0(?:[^0-9.]|$)", raw):
        fail(category)

    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                fail(category)
            result[key] = value
        return result

    def integer(value: str) -> int:
        parsed = int(value)
        if abs(parsed) > SAFE_INTEGER:
            fail(category)
        return parsed

    def reject_number(_: str) -> None:
        fail(category)

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_int=integer,
            parse_float=reject_number,
            parse_constant=reject_number,
        )
    except Failure:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        fail(category)
    return value, raw


def exact(value: Any, keys: set[str], category: str = "schema.evidence") -> None:
    if not isinstance(value, dict) or set(value) != keys:
        fail(category)


def integer(value: Any, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def token(value: Any, maximum: int = 256) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value.encode("utf-8")) <= maximum
        and TOKEN_RE.fullmatch(value) is not None
    )


def _portable(value: Any, counters: dict[str, int], depth: int = 0) -> None:
    if depth > HARD_LIMITS["max_depth"]:
        fail("limits.exceeded")
    if isinstance(value, dict):
        counters["members"] += len(value)
        if counters["members"] > HARD_LIMITS["max_total_members"]:
            fail("limits.exceeded")
        for key, item in value.items():
            if not token(key, HARD_LIMITS["max_string_bytes"]):
                fail("schema.evidence")
            _portable(item, counters, depth + 1)
    elif isinstance(value, list):
        counters["items"] += len(value)
        if counters["items"] > HARD_LIMITS["max_total_list_items"]:
            fail("limits.exceeded")
        for item in value:
            _portable(item, counters, depth + 1)
    elif isinstance(value, str):
        if (
            len(value.encode("utf-8")) > HARD_LIMITS["max_string_bytes"]
            or "\x00" in value
        ):
            fail("limits.exceeded")
    elif isinstance(value, bool) or value is None:
        return
    elif isinstance(value, int):
        if abs(value) > SAFE_INTEGER:
            fail("json.syntax")
    else:
        fail("json.syntax")


def schema_check(evidence: Any) -> None:
    schema_path = (
        SCRIPT_ROOT.parent
        / "docs/platform/schemas/multi-runtime-coexistence-evidence-v1.schema.json"
    )
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail("schema.evidence")
    if not candidate._schema_validate(evidence, schema, schema):
        fail("schema.evidence")
    exact(
        evidence,
        {
            "contract",
            "schema_version",
            "fixture_id",
            "evidence_class",
            "export_tier",
            "evidence_id",
            "evidence_hash",
            "registry",
            "scope",
            "m7_binding",
            "m7_live_status",
            "capture_clock",
            "normalization",
            "limits",
            "runs",
        },
    )
    if (
        evidence["contract"] != EVIDENCE_CONTRACT
        or evidence["schema_version"] != 1
        or not token(evidence["fixture_id"], 121)
        or evidence["evidence_class"]
        not in {"SYNTHETIC_OFFLINE_FIXTURE", "CAPTURED_RUNTIME_EVIDENCE"}
        or evidence["export_tier"] != "PUBLIC_REDACTED"
        or not isinstance(evidence["evidence_id"], str)
        or not re.fullmatch(r"mrcv1:sha256:[0-9a-f]{64}", evidence["evidence_id"])
        or not isinstance(evidence["evidence_hash"], str)
        or not DIGEST_RE.fullmatch(evidence["evidence_hash"])
        or not isinstance(evidence["runs"], list)
    ):
        fail("schema.evidence")
    exact(evidence["registry"], {"contract", "version", "digest"})
    exact(
        evidence["scope"],
        {"gate", "claims", "excluded_gates", "live_vr940_claim", "public_version_policy"},
    )
    exact(
        evidence["m7_binding"],
        {
            "source_commit",
            "docs_source_commit",
            "graph_contract",
            "graph_id",
            "graph_hash",
            "replay_contract",
            "replay_id",
            "replay_hash",
            "registry_content_hash",
            "source_bundle_content_hash",
            "source_replay_content_hash",
        },
    )
    if evidence["m7_live_status"] is not None:
        exact(
            evidence["m7_live_status"],
            {
                "contract",
                "projection_id",
                "projection_hash",
                "content_hash",
                "source_graph_id",
                "source_graph_hash",
                "source_replay_id",
                "source_replay_hash",
            },
        )
    exact(
        evidence["capture_clock"],
        {
            "clock_id",
            "basis",
            "wall_anchor_utc",
            "monotonic_epoch_id",
            "max_clock_error_ns",
            "max_capture_age_ns",
            "verification_offset_ns",
            "clock_hash",
        },
    )
    exact(
        evidence["normalization"],
        {
            "profile_id",
            "canonicalization",
            "timestamp_replacement",
            "mask_replacement",
            "view_rules",
            "profile_digest",
        },
    )
    exact(evidence["limits"], set(HARD_LIMITS))
    for rule in evidence["normalization"]["view_rules"]:
        exact(rule, {"view_id", "capture_path", "timestamp_pointers", "mask_pointers"})
        if not all(
            isinstance(rule[name], list)
            for name in ("timestamp_pointers", "mask_pointers")
        ):
            fail("schema.evidence")
    for run in evidence["runs"]:
        exact(
            run,
            {"run_id", "state", "capture_offset_ns", "provenance", "state_evidence", "protected_views"},
        )
        if not token(run["run_id"]) or not integer(run["capture_offset_ns"]):
            fail("schema.evidence")
        provenance = run["provenance"]
        exact(
            provenance,
            {"capture_clock_id", "process_instance_id", "runtime", "config", "auth_scope", "mask_scope_digest", "immutable_inputs"},
        )
        runtime = provenance["runtime"]
        exact(
            runtime,
            {
                "repository",
                "source_commit",
                "source_parent_commit",
                "artifact_id",
                "artifact_digest",
                "artifact_size_bytes",
                "build_manifest",
                "build_manifest_hash",
            },
        )
        exact(runtime["build_manifest"], {"go_version", "target", "build_mode", "flags"})
        config = provenance["config"]
        exact(config, {"config_id", "payload", "config_hash"})
        exact(
            config["payload"],
            {"eebus_runtime_enabled", "candidate_graph_enabled", "outbound_enabled", "public_v2_enabled"},
        )
        auth = provenance["auth_scope"]
        exact(auth, {"scope_id", "principal_class", "permissions", "scope_hash"})
        if not isinstance(provenance["immutable_inputs"], list):
            fail("schema.evidence")
        for item in provenance["immutable_inputs"]:
            exact(item, {"input_id", "kind", "digest", "byte_length"})
        state = run["state_evidence"]
        exact(
            state,
            {
                "outcome",
                "eebus_runtime_enabled",
                "candidate_graph_enabled",
                "service_count",
                "raw_only_count",
                "candidate_count",
                "conflict_count",
                "withheld_count",
                "degraded",
                "empty_success",
                "facts",
                "restart_transition",
            },
        )
        if not isinstance(state["facts"], list) or not isinstance(run["protected_views"], list):
            fail("schema.evidence")
        for fact in state["facts"]:
            exact(fact, {"candidate_id", "status", "terminal_negative_state", "visibility_channel"})
        if state["restart_transition"] is not None:
            transition = state["restart_transition"]
            exact(
                transition,
                {
                    "event_id",
                    "before_process_instance_id",
                    "after_process_instance_id",
                    "before_trust_state_hash",
                    "after_trust_state_hash",
                    "before_peer_binding_hash",
                    "after_peer_binding_hash",
                    "session_reconnected",
                    "process_event",
                    "before_snapshot",
                    "after_snapshot",
                    "session_event",
                },
            )
            exact(
                transition["process_event"],
                {
                    "event_id",
                    "event_type",
                    "before_process_instance_id",
                    "after_process_instance_id",
                    "observed_at_offset_ns",
                },
            )
            for snapshot_name in ("before_snapshot", "after_snapshot"):
                exact(
                    transition[snapshot_name],
                    {
                        "process_instance_id",
                        "capture_offset_ns",
                        "trust_state_id",
                        "peer_binding_id",
                        "session_id",
                        "session_state",
                    },
                )
            exact(
                transition["session_event"],
                {
                    "event_id",
                    "event_type",
                    "process_instance_id",
                    "session_id",
                    "observed_at_offset_ns",
                    "state",
                },
            )
        for view in run["protected_views"]:
            exact(
                view,
                {"view_id", "capture_path", "media_type", "payload", "raw_payload_hash", "shape_hash", "canonical_payload_hash"},
            )
    _portable(evidence, {"members": 0, "items": 0})


def check_limits(evidence: dict[str, Any], raw_size: int) -> None:
    if evidence["limits"] != HARD_LIMITS or raw_size > HARD_LIMITS["max_evidence_bytes"]:
        fail("limits.exceeded")
    if len(evidence["runs"]) > HARD_LIMITS["max_runs"]:
        fail("limits.exceeded")
    for run in evidence["runs"]:
        if (
            len(run["protected_views"]) > HARD_LIMITS["max_views_per_run"]
            or len(run["provenance"]["immutable_inputs"])
            > HARD_LIMITS["max_inputs_per_run"]
            or len(run["state_evidence"]["facts"])
            > HARD_LIMITS["max_internal_facts_per_run"]
        ):
            fail("limits.exceeded")
        for view in run["protected_views"]:
            if len(canonical(view["payload"])) > HARD_LIMITS["max_payload_bytes"]:
                fail("limits.exceeded")


def check_registry(evidence: dict[str, Any], registry: Any, raw: bytes) -> None:
    exact(
        registry,
        {
            "contract",
            "version",
            "evidence_contract",
            "report_contract",
            "gate",
            "excluded_gates",
            "m7_synthetic_predecessor",
            "m7_live_predecessor",
            "m7_synthetic_binding",
            "m7_live_binding",
            "m7_live_terminal_binding",
            "m7_live_private_inputs",
            "m7_live_status_binding",
            "scenario_profiles",
            "protected_views",
            "view_rules",
            "required_acceptance_checks",
            "validation_precedence",
            "limits",
            "fixture_ids",
        },
        "registry.binding",
    )
    expected_digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    if (
        hashlib.sha256(raw).hexdigest() != EXPECTED_REGISTRY_SHA256
        or
        registry["contract"] != REGISTRY_CONTRACT
        or registry["version"] != 1
        or registry["limits"] != HARD_LIMITS
        or evidence["registry"]
        != {"contract": REGISTRY_CONTRACT, "version": 1, "digest": expected_digest}
    ):
        fail("registry.binding")
    for key, mode in (
        ("m7_synthetic_predecessor", "EXACT_SYNTHETIC_FIXTURE"),
        ("m7_live_predecessor", "VALIDATED_INPUTS_AND_REGENERATED_REPLAY"),
    ):
        predecessor = registry[key]
        exact(
            predecessor,
            {"repository", "source_commit", "docs_source_commit", "binding_mode"},
            "registry.binding",
        )
        if (
            predecessor["repository"]
            != "github.com/Project-Helianthus/helianthus-ebusgateway"
            or not SHA_RE.fullmatch(predecessor["source_commit"])
            or not SHA_RE.fullmatch(predecessor["docs_source_commit"])
            or predecessor["binding_mode"] != mode
        ):
            fail("registry.binding")
    if set(registry["scenario_profiles"]) != {
        "SYNTHETIC_OFFLINE_FIXTURE",
        "CAPTURED_RUNTIME_EVIDENCE",
    }:
        fail("registry.binding")


def _verify_m7_status(
    evidence: dict[str, Any], registry: dict[str, Any], path: pathlib.Path
) -> tuple[dict[str, Any], bytes]:
    if evidence["evidence_class"] == "SYNTHETIC_OFFLINE_FIXTURE":
        if evidence["m7_live_status"] is not None:
            fail("provenance.m7")
        return {"facts": []}, b""
    try:
        status, raw = candidate.load_json(path, input_kind="source")
        schema_path = (
            pathlib.Path(__file__).resolve().parents[1]
            / "docs/platform/schemas/draft-candidate-fact-public-status-v1.schema.json"
        )
        schema, _ = load_json(schema_path, "provenance.m7")
        if not candidate._schema_validate(status, schema, schema):
            fail("provenance.m7")
    except Failure:
        raise
    except (candidate.Failure, KeyError, TypeError, ValueError, OSError):
        fail("provenance.m7")
    view = {
        key: value
        for key, value in status.items()
        if key not in {"projection_id", "projection_hash"}
    }
    projection_hash = digest(M7_STATUS_PROJECTION_DOMAIN, view)
    counts = {
        name: sum(fact["status"] == name for fact in status["facts"])
        for name in ("RAW_ONLY", "WITHHELD")
    }
    expected_binding = {
        "contract": status["contract"],
        "projection_id": status["projection_id"],
        "projection_hash": status["projection_hash"],
        "content_hash": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "source_graph_id": status["source_graph_id"],
        "source_graph_hash": status["source_graph_hash"],
        "source_replay_id": status["source_replay_id"],
        "source_replay_hash": status["source_replay_hash"],
    }
    facts = status["facts"]
    if (
        status["projection_hash"] != projection_hash
        or status["projection_id"] != "dcfpsv1:" + projection_hash
        or status["source_commit"]
        != registry["m7_live_predecessor"]["source_commit"]
        or status["docs_source_commit"]
        != registry["m7_live_predecessor"]["docs_source_commit"]
        or expected_binding != registry["m7_live_status_binding"]
        or evidence["m7_live_status"] != expected_binding
        or status["fact_count"] != len(facts)
        or status["status_counts"] != counts
        or counts["RAW_ONLY"] < 1
        or counts["WITHHELD"] < 1
        or [fact["candidate_id"] for fact in facts]
        != sorted(fact["candidate_id"] for fact in facts)
        or len({fact["candidate_id"] for fact in facts}) != len(facts)
        or any(
            (fact["status"] == "RAW_ONLY")
            != (fact["terminal_negative_state"] is None)
            for fact in facts
        )
    ):
        fail("provenance.m7")
    return {"facts": facts}, raw


def _load_verified_m7_graph(
    paths: dict[str, pathlib.Path | None], prefix: str = ""
) -> tuple[
    dict[str, Any],
    bytes,
    dict[str, Any],
    bytes,
    bytes,
    bytes,
    dict[str, Any],
    bytes,
]:
    try:
        graph_path = paths[prefix + "graph"]
        replay_path = paths[prefix + "replay"]
        source_bundle_path = paths[prefix + "source_bundle"]
        source_replay_path = paths[prefix + "source_replay"]
        if any(
            path is None
            for path in (
                graph_path,
                replay_path,
                source_bundle_path,
                source_replay_path,
            )
        ):
            fail("provenance.m7")
        graph, graph_raw = candidate.load_json(graph_path, input_kind="graph")
        m7_registry, m7_registry_raw = candidate.load_json(
            paths["registry"], input_kind="registry"
        )
        source_bundle, source_bundle_raw = candidate.load_json(
            source_bundle_path, input_kind="source"
        )
        source_replay, source_replay_raw = candidate.load_json(
            source_replay_path, input_kind="source"
        )
        verified_source, verified_source_replay = candidate._verify_source_inputs(
            m7_registry,
            paths["registry"],
            source_bundle,
            source_bundle_raw,
            source_replay,
        )
        candidate.verify(
            graph,
            m7_registry,
            m7_registry_raw,
            len(graph_raw),
            verified_source,
            verified_source_replay,
        )
        replay, replay_raw = candidate.load_json(replay_path, input_kind="source")
        if candidate.replay(graph) != replay:
            fail("provenance.m7")
    except Failure:
        raise
    except (candidate.Failure, KeyError, TypeError, ValueError, OSError):
        fail("provenance.m7")
    return (
        graph,
        graph_raw,
        replay,
        replay_raw,
        m7_registry_raw,
        source_bundle_raw,
        source_replay,
        source_replay_raw,
    )


def _binding(
    graph: dict[str, Any],
    replay: dict[str, Any],
    registry_raw: bytes,
    source_bundle_raw: bytes,
    source_replay_raw: bytes,
) -> dict[str, Any]:
    return {
        "graph_contract": graph["contract"],
        "graph_id": graph["graph_id"],
        "graph_hash": graph["graph_hash"],
        "replay_contract": replay["contract"],
        "replay_id": replay["replay_id"],
        "replay_hash": replay["replay_hash"],
        "registry_content_hash": "sha256:" + hashlib.sha256(registry_raw).hexdigest(),
        "source_bundle_content_hash": "sha256:"
        + hashlib.sha256(source_bundle_raw).hexdigest(),
        "source_replay_content_hash": "sha256:"
        + hashlib.sha256(source_replay_raw).hexdigest(),
    }


def _verify_m7(
    evidence: dict[str, Any],
    registry: dict[str, Any],
    paths: dict[str, pathlib.Path | None],
    *,
    require_private: bool,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, tuple[str, int]],
    dict[str, Any],
]:
    status_graph, status_raw = _verify_m7_status(
        evidence, registry, paths["status"]
    )
    evidence_class = evidence["evidence_class"]
    if evidence_class == "SYNTHETIC_OFFLINE_FIXTURE":
        (
            graph,
            _,
            replay,
            _,
            m7_registry_raw,
            source_bundle_raw,
            _,
            source_replay_raw,
        ) = _load_verified_m7_graph(paths)
        predecessor = registry["m7_synthetic_predecessor"]
        content_binding = _binding(
            graph, replay, m7_registry_raw, source_bundle_raw, source_replay_raw
        )
        fixed = {
            "source_commit": predecessor["source_commit"],
            "docs_source_commit": predecessor["docs_source_commit"],
            **registry["m7_synthetic_binding"],
        }
        if evidence["m7_binding"] != fixed or content_binding != registry["m7_synthetic_binding"]:
            fail("provenance.m7")
        inputs = {
            "m7:graph": (graph["graph_hash"], len(canonical(graph))),
            "m7:replay": (replay["replay_hash"], len(canonical(replay))),
            "m7:registry": (
                content_binding["registry_content_hash"],
                len(m7_registry_raw),
            ),
            "m7:source-bundle": (
                content_binding["source_bundle_content_hash"],
                len(source_bundle_raw),
            ),
            "m7:source-replay": (
                content_binding["source_replay_content_hash"],
                len(source_replay_raw),
            ),
        }
        return graph, replay, inputs, graph

    (
        terminal_graph,
        _,
        terminal_replay,
        _,
        terminal_registry_raw,
        terminal_source_bundle_raw,
        _,
        terminal_source_replay_raw,
    ) = _load_verified_m7_graph(paths, "terminal_")
    terminal_binding = _binding(
        terminal_graph,
        terminal_replay,
        terminal_registry_raw,
        terminal_source_bundle_raw,
        terminal_source_replay_raw,
    )
    if terminal_binding != registry["m7_live_terminal_binding"]:
        fail("provenance.m7")

    predecessor = registry["m7_live_predecessor"]
    fixed_live_binding = {
        "source_commit": predecessor["source_commit"],
        "docs_source_commit": predecessor["docs_source_commit"],
        **registry["m7_live_binding"],
    }
    if evidence["m7_binding"] != fixed_live_binding:
        fail("provenance.m7")
    if (
        status_graph["facts"]
        and (
            evidence["m7_live_status"]["source_graph_id"]
            != registry["m7_live_binding"]["graph_id"]
            or evidence["m7_live_status"]["source_graph_hash"]
            != registry["m7_live_binding"]["graph_hash"]
            or evidence["m7_live_status"]["source_replay_id"]
            != registry["m7_live_binding"]["replay_id"]
            or evidence["m7_live_status"]["source_replay_hash"]
            != registry["m7_live_binding"]["replay_hash"]
        )
    ):
        fail("provenance.m7")

    private_inputs = registry["m7_live_private_inputs"]
    if require_private:
        try:
            projected, private_raw = status_projector.load_verified_projection(
                graph_path=paths["graph"],
                replay_path=paths["replay"],
                registry_path=paths["registry"],
                source_bundle_path=paths["source_bundle"],
                source_replay_path=paths["source_replay"],
                source_commit=predecessor["source_commit"],
                docs_source_commit=predecessor["docs_source_commit"],
            )
        except (
            status_projector.Failure,
            candidate.Failure,
            AttributeError,
            OSError,
            KeyError,
            TypeError,
            ValueError,
        ):
            fail("provenance.m7")
        if status_projector.render(projected) != status_raw:
            fail("provenance.m7")
        actual_private_inputs = {
            name: {
                "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "byte_length": len(raw),
            }
            for name, raw in private_raw.items()
            if name != "registry"
        }
        if actual_private_inputs != private_inputs:
            fail("provenance.m7")

    inputs = {
        "m7:terminal-graph": (
            terminal_graph["graph_hash"],
            len(canonical(terminal_graph)),
        ),
        "m7:terminal-replay": (
            terminal_replay["replay_hash"],
            len(canonical(terminal_replay)),
        ),
        "m7:registry": (
            terminal_binding["registry_content_hash"],
            len(terminal_registry_raw),
        ),
        "m7:terminal-source-bundle": (
            terminal_binding["source_bundle_content_hash"],
            len(terminal_source_bundle_raw),
        ),
        "m7:terminal-source-replay": (
            terminal_binding["source_replay_content_hash"],
            len(terminal_source_replay_raw),
        ),
        "m7:private-graph": (
            private_inputs["graph"]["digest"],
            private_inputs["graph"]["byte_length"],
        ),
        "m7:private-replay": (
            private_inputs["replay"]["digest"],
            private_inputs["replay"]["byte_length"],
        ),
        "m7:private-source-bundle": (
            private_inputs["source_bundle"]["digest"],
            private_inputs["source_bundle"]["byte_length"],
        ),
        "m7:private-source-replay": (
            private_inputs["source_replay"]["digest"],
            private_inputs["source_replay"]["byte_length"],
        ),
        "m7:status-projection": (
            evidence["m7_live_status"]["content_hash"],
            len(status_raw),
        ),
    }
    return status_graph, terminal_replay, inputs, terminal_graph


def check_runtime_identity(evidence: dict[str, Any]) -> None:
    baseline = evidence["runs"][0]["provenance"]["runtime"]
    if evidence["evidence_class"] == "SYNTHETIC_OFFLINE_FIXTURE":
        if (
            baseline["source_commit"] != BASELINE_SOURCE_SHA
            or baseline["source_parent_commit"] is not None
        ):
            fail("provenance.runtime")
        compared_runtime = evidence["runs"][1]["provenance"]["runtime"]
        if compared_runtime["source_parent_commit"] != BASELINE_SOURCE_SHA:
            fail("provenance.runtime")
    else:
        compared_runtime = baseline
        if (
            baseline["source_parent_commit"]
            != evidence["m7_binding"]["source_commit"]
            or baseline["build_manifest"]["build_mode"]
            != "REPRODUCIBLE_BUILD"
        ):
            fail("provenance.runtime")
    for run in evidence["runs"]:
        runtime = run["provenance"]["runtime"]
        if (
            runtime["repository"]
            != "github.com/Project-Helianthus/helianthus-ebusgateway"
            or not SHA_RE.fullmatch(runtime["source_commit"])
            or runtime["artifact_id"]
            != "gateway:" + runtime["artifact_digest"]
            or runtime["build_manifest_hash"]
            != digest(BUILD_DOMAIN, runtime["build_manifest"])
            or not integer(runtime["artifact_size_bytes"], 1)
        ):
            fail("provenance.runtime")
    compared_runs = (
        evidence["runs"][1:]
        if evidence["evidence_class"] == "SYNTHETIC_OFFLINE_FIXTURE"
        else evidence["runs"]
    )
    for run in compared_runs:
        if run["provenance"]["runtime"] != compared_runtime:
            fail("provenance.runtime")


def _decode_source_json(raw: bytes) -> Any:
    _bounded_preflight(raw)
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                fail("provenance.source_capture")
            result[key] = value
        return result

    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_int=lambda value: int(value),
            parse_float=lambda _: fail("provenance.source_capture"),
            parse_constant=lambda _: fail("provenance.source_capture"),
        )
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, RecursionError):
        fail("provenance.source_capture")


def _read_bounded_regular_file(
    path: pathlib.Path, maximum: int, category: str
) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    try:
        descriptor = os.open(path, flags)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size <= 0 or info.st_size > maximum:
            fail(category)
        chunks: list[bytes] = []
        remaining = info.st_size
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                fail(category)
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            fail(category)
        raw = b"".join(chunks)
        if not raw or len(raw) != info.st_size:
            fail(category)
        return raw
    except OSError:
        fail(category)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _source_inner_mcp(raw: bytes) -> dict[str, Any]:
    envelope = _decode_source_json(raw)
    try:
        content = envelope["result"]["content"]
        if (
            envelope["result"].get("isError") is not False
            or len(content) != 1
            or content[0]["type"] != "text"
        ):
            fail("provenance.source_capture")
        value = _decode_source_json(content[0]["text"].encode("utf-8"))
    except (KeyError, TypeError, AttributeError):
        fail("provenance.source_capture")
    if not isinstance(value, dict):
        fail("provenance.source_capture")
    return value


def _source_redacted(value: Any) -> str:
    return "redacted:sha256:" + hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def _source_string_number(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _source_device_projection(item: dict[str, Any]) -> dict[str, Any] | None:
    address = item.get("address")
    device_id = item.get("device_id")
    manufacturer = item.get("manufacturer")
    if not isinstance(address, int) or not device_id or not manufacturer:
        return None
    return {
        "address": _source_redacted(f"ebus-address:{address}"),
        "device_id": _source_redacted(f"ebus-device:{address}:{device_id}"),
        "manufacturer": manufacturer,
        "model": device_id,
        "discovery_source": item.get("discovery_source") or "unknown",
        "verification_state": item.get("verification_state") or "unknown",
    }


def _source_semantic(snapshot: dict[str, Any]) -> dict[str, Any]:
    planes = snapshot["data"]["planes"]
    zones = []
    for zone in planes.get("zones", []):
        config = zone.get("config") or {}
        zones.append(
            {
                "id": _source_redacted("semantic-zone:" + zone["id"]),
                "name": zone.get("name") or "",
                "source": "ebus",
                "operating_mode": config.get("operating_mode"),
                "preset": config.get("preset"),
                "target_temp_c": _source_string_number(config.get("target_temp_c")),
                "associated_circuit": _source_string_number(
                    config.get("associated_circuit")
                ),
            }
        )
    zones.sort(key=lambda item: item["id"])
    dhw_config = (planes.get("dhw") or {}).get("config") or {}
    system_properties = (planes.get("system") or {}).get("properties") or {}
    return {
        "zones": zones,
        "dhw": {
            "source": "ebus",
            "operating_mode": dhw_config.get("operating_mode"),
            "preset": dhw_config.get("preset"),
        },
        "system_properties": {
            "source": "ebus",
            "system_scheme": _source_string_number(
                system_properties.get("system_scheme")
            ),
            "module_configuration_vr71": _source_string_number(
                system_properties.get("module_configuration_vr71")
            ),
        },
    }


def _source_graphql_schema(raw: dict[str, Any]) -> dict[str, Any]:
    schema = raw["data"]["__schema"]
    return {
        "query_fields": sorted(item["name"] for item in schema["queryType"]["fields"]),
        "mutation_fields": sorted(
            item["name"] for item in schema["mutationType"]["fields"]
        ),
    }


def _source_graphql_values(raw: dict[str, Any]) -> dict[str, Any]:
    data = raw["data"]
    zones = [
        {
            "id": _source_redacted("graphql-zone:" + zone["id"]),
            "name": zone["name"],
            "source": "ebus",
            "operating_mode": zone["config"]["operatingMode"],
            "target_temp_c": _source_string_number(zone["config"]["targetTempC"]),
        }
        for zone in data["zones"]
    ]
    zones.sort(key=lambda item: item["id"])
    return {
        "zones": zones,
        "dhw": {
            "source": "ebus",
            "operating_mode": data["dhw"]["config"]["operatingMode"],
        },
    }


def _source_project_views(inputs: dict[str, bytes]) -> dict[str, Any]:
    tools = _decode_source_json(inputs["tools.list"])
    devices_response = _source_inner_mcp(inputs["ebus.devices"])
    semantic_response = _source_inner_mcp(inputs["ebus.semantic"])
    runtime = _source_inner_mcp(inputs["eebus.runtime"])
    services = _source_inner_mcp(inputs["eebus.services"])
    sessions = _source_inner_mcp(inputs["eebus.sessions"])
    pairing = _source_inner_mcp(inputs["eebus.pairing"])
    topology = _source_inner_mcp(inputs["eebus.topology"])
    graph_schema = _decode_source_json(inputs["graphql.schema"])
    graph_raw = _decode_source_json(inputs["graphql.values"])
    portal_raw = _decode_source_json(inputs["portal.bootstrap"])
    debug_raw = _decode_source_json(inputs["ebus.debug"])
    routes_raw = _decode_source_json(inputs["command.routing"])
    semantic_registry_raw = _decode_source_json(inputs["semantic.registry"])
    inspect = _decode_source_json(inputs["container.inspect"])
    try:
        listed_tools = tools["result"]["tools"]
        by_name = {item["name"]: item for item in listed_tools}
        if (
            len(by_name) != len(listed_tools)
            or [item["name"] for item in listed_tools]
            != APPROVED_M8_TOOL_INVENTORY
        ):
            fail("provenance.source_capture")
        schemas = [
            {"name": name, "inputSchema": by_name[name]["inputSchema"]}
            for name in APPROVED_M8_EEBUS_TOOLS
        ]
        devices = [
            projected
            for item in devices_response["data"]
            if (projected := _source_device_projection(item)) is not None
        ]
        devices.sort(key=lambda item: item["address"])
        if not devices:
            fail("provenance.source_capture")
        semantic = _source_semantic(semantic_response)
        graph_values = _source_graphql_values(graph_raw)
        if not all(
            isinstance(value, dict)
            for value in (portal_raw, debug_raw, routes_raw, semantic_registry_raw)
        ):
            fail("provenance.source_capture")
        ha_values = {
            "entities": [
                {
                    "entity_id": _source_redacted("ha-zone:" + zone["id"]),
                    "source": "ebus",
                    "state": zone["operating_mode"],
                    "target_temperature": zone["target_temp_c"],
                }
                for zone in graph_values["zones"]
            ]
        }
        ha_identity = {
            "devices": [
                {
                    "manufacturer": item["manufacturer"],
                    "model": item["model"],
                    "unique_id": _source_redacted("ha:" + item["device_id"]),
                    "via_device": _source_redacted("ha-via:" + item["address"]),
                }
                for item in devices
            ]
        }
        if (
            runtime["data"]["state"] != "ready"
            or not services["data"]["services"]
            or not any(item.get("state") == "connected" for item in sessions["data"]["sessions"])
            or not any(item.get("state") == "paired" for item in pairing["data"]["pairing"])
            or not topology["data"]["devices"]
            or not isinstance(inspect, list)
            or len(inspect) != 1
        ):
            fail("provenance.source_capture")
        process_source = inspect[0]["Id"] + "\x00" + inspect[0]["State"]["StartedAt"]
    except (KeyError, TypeError, AttributeError):
        fail("provenance.source_capture")
    return {
        "views": {
            "mcp.ebus.v1.responses": {
                "contract": "ebus.v1",
                "responses": [
                    {
                        "operation": "ebus.v1.registry.devices.list",
                        "result": {
                            "selection": {
                                "criteria": "all_structurally_identified_devices_in_single_window",
                                "selected_count": len(devices),
                            },
                            "devices": devices,
                        },
                    },
                    {
                        "operation": "ebus.v1.semantic.snapshot.get",
                        "result": semantic,
                    },
                ],
            },
            "mcp.tool.inventory": {"tools": APPROVED_M8_TOOL_INVENTORY},
            "graphql.schema": _source_graphql_schema(graph_schema),
            "graphql.ebus.values": graph_values,
            "ha.graphql.values": ha_values,
            "ha.identity": ha_identity,
            "debug.ebus": debug_raw,
            "portal.ebus.bootstrap": portal_raw,
            "command.routing": routes_raw,
            "semantic.registry": semantic_registry_raw,
            "mcp.eebus.v1.contract": {
                "namespace": "eebus.v1",
                "public_v2": False,
                "schema_digest": "sha256:" + hashlib.sha256(canonical(schemas)).hexdigest(),
                "version": 1,
            },
        },
        "process_instance_id": "process-"
        + hashlib.sha256(process_source.encode("utf-8")).hexdigest()[:32],
        "service_count": len(services["data"]["services"]),
    }


def _read_source_inputs(root: pathlib.Path, manifest: dict[str, Any]) -> dict[str, bytes]:
    try:
        if root.is_symlink():
            fail("provenance.source_capture")
        resolved_root = root.resolve(strict=True)
    except OSError:
        fail("provenance.source_capture")
    if not resolved_root.is_dir():
        fail("provenance.source_capture")
    try:
        if {item.name for item in resolved_root.iterdir()} != set(
            SOURCE_CAPTURE_FILES.values()
        ):
            fail("provenance.source_capture")
    except OSError:
        fail("provenance.source_capture")
    result: dict[str, bytes] = {}
    total = 0
    manifest_inputs = {item["input_id"]: item for item in manifest["inputs"]}
    for input_id, relative in SOURCE_CAPTURE_FILES.items():
        path = resolved_root / relative
        try:
            if path.is_symlink() or path.resolve(strict=True).parent != resolved_root:
                fail("provenance.source_capture")
            raw = _read_bounded_regular_file(
                path, MAX_SOURCE_INPUT_BYTES, "provenance.source_capture"
            )
        except OSError:
            fail("provenance.source_capture")
        total += len(raw)
        if (
            total > MAX_SOURCE_TOTAL_BYTES
            or manifest_inputs[input_id]["digest"]
            != "sha256:" + hashlib.sha256(raw).hexdigest()
            or manifest_inputs[input_id]["byte_length"] != len(raw)
        ):
            fail("provenance.source_capture")
        result[input_id] = raw
    return result


def _source_capture_binding(
    raw: bytes,
    root: pathlib.Path,
    auth_scope_hash: str,
    phase: str,
    process_instance_id: str,
    start_offset_ns: int,
    end_offset_ns: int,
    captured_at: str,
) -> dict[str, Any]:
    if not raw or len(raw) > MAX_SOURCE_INPUT_BYTES:
        fail("provenance.source_capture")
    value = _decode_source_json(raw)
    if not isinstance(value, dict) or set(value) != {
        "contract", "schema_version", "window_id", "window_scope",
        "phase", "projection_policy", "auth_scope_hash", "process_instance_id",
        "capture_start_offset_ns", "capture_end_offset_ns", "captured_at", "inputs",
    }:
        fail("provenance.source_capture")
    if (
        value["contract"] != SOURCE_CAPTURE_CONTRACT
        or not integer(value["schema_version"], 1)
        or value["schema_version"] != 1
        or not isinstance(value["window_id"], str)
        or not TOKEN_RE.fullmatch(value["window_id"])
        or value["window_scope"] != "SINGLE_WINDOW_ONLY"
        or value["phase"] != phase
        or value["projection_policy"] != SOURCE_CAPTURE_POLICY
        or value["auth_scope_hash"] != auth_scope_hash
        or value["process_instance_id"] != process_instance_id
        or not integer(value["capture_start_offset_ns"])
        or not integer(value["capture_end_offset_ns"])
        or value["capture_start_offset_ns"] != start_offset_ns
        or value["capture_end_offset_ns"] != end_offset_ns
        or value["capture_start_offset_ns"] > value["capture_end_offset_ns"]
        or not isinstance(value["captured_at"], str)
        or not RFC3339_UTC_RE.fullmatch(value["captured_at"])
        or value["captured_at"] != captured_at
        or not isinstance(value["inputs"], list)
    ):
        fail("provenance.source_capture")
    expected = list(SOURCE_CAPTURE_INPUTS.items())
    observed: list[tuple[str, str]] = []
    for item in value["inputs"]:
        if not isinstance(item, dict) or set(item) != {
            "input_id", "auth_boundary", "digest", "byte_length",
        }:
            fail("provenance.source_capture")
        if (
            not isinstance(item["input_id"], str)
            or not isinstance(item["auth_boundary"], str)
            or not isinstance(item["digest"], str)
            or not DIGEST_RE.fullmatch(item["digest"])
            or not integer(item["byte_length"], 1)
        ):
            fail("provenance.source_capture")
        observed.append((item["input_id"], item["auth_boundary"]))
    if observed != expected:
        fail("provenance.source_capture")
    inputs = _read_source_inputs(root, value)
    try:
        captured_at = inputs["capture.timestamp"].decode("utf-8").strip()
    except UnicodeDecodeError:
        fail("provenance.source_capture")
    if captured_at != value["captured_at"]:
        fail("provenance.source_capture")
    try:
        projected = _source_project_views(inputs)
    except Failure:
        raise
    except (KeyError, TypeError, AttributeError, IndexError, ValueError):
        fail("provenance.source_capture")
    if projected["process_instance_id"] != process_instance_id:
        fail("provenance.source_capture")
    return {
        "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "byte_length": len(raw),
        "window_id": value["window_id"],
        "phase": value["phase"],
        "captured_at": value["captured_at"],
        **projected,
    }


def _capture_time_at(clock: dict[str, Any], offset_ns: int) -> str:
    if offset_ns % 1_000 != 0:
        fail("provenance.source_capture")
    try:
        anchor = dt.datetime.fromisoformat(
            clock["wall_anchor_utc"].replace("Z", "+00:00")
        )
    except (KeyError, TypeError, ValueError):
        fail("provenance.source_capture")
    value = anchor + dt.timedelta(microseconds=offset_ns // 1_000)
    return value.astimezone(dt.timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def check_runtime(
    evidence: dict[str, Any],
    m7_inputs: dict[str, tuple[str, int]],
    source_manifests: dict[str, bytes | None] | None = None,
    source_roots: dict[str, pathlib.Path | None] | None = None,
    *,
    require_private: bool = True,
) -> None:
    check_runtime_identity(evidence)
    source_bindings: dict[str, dict[str, Any]] = {}
    if evidence["evidence_class"] == "CAPTURED_RUNTIME_EVIDENCE" and require_private:
        groups = {"before": (0, 1), "after": (2, 3)}
        for source_key, run_indexes in groups.items():
            grouped = [evidence["runs"][index] for index in run_indexes]
            auth_hashes = {
                run["provenance"]["auth_scope"]["scope_hash"] for run in grouped
            }
            process_ids = {
                run["provenance"]["process_instance_id"] for run in grouped
            }
            source_raw = (source_manifests or {}).get(source_key)
            source_root = (source_roots or {}).get(source_key)
            if (
                len(auth_hashes) != 1
                or len(process_ids) != 1
                or source_raw is None
                or source_root is None
            ):
                fail("provenance.source_capture")
            source_bindings[source_key] = _source_capture_binding(
                source_raw,
                source_root,
                auth_hashes.pop(),
                SOURCE_CAPTURE_PHASES[source_key],
                process_ids.pop(),
                min(run["capture_offset_ns"] for run in grouped),
                max(run["capture_offset_ns"] for run in grouped),
                _capture_time_at(
                    evidence["capture_clock"],
                    min(run["capture_offset_ns"] for run in grouped),
                ),
            )
        before = source_bindings["before"]
        after = source_bindings["after"]
        restart = evidence["runs"][2]["state_evidence"]["restart_transition"]
        before_end = evidence["runs"][1]["capture_offset_ns"]
        after_start = evidence["runs"][2]["capture_offset_ns"]
        if (
            before["digest"] == after["digest"]
            or before["window_id"] == after["window_id"]
            or before["captured_at"] == after["captured_at"]
            or before_end >= after_start
            or restart is None
            or not before_end
            < restart["process_event"]["observed_at_offset_ns"]
            <= after_start
        ):
            fail("provenance.source_capture")
    elif evidence["evidence_class"] == "CAPTURED_RUNTIME_EVIDENCE":
        public_bindings: dict[str, tuple[str, int]] = {}
        for source_key, run_indexes in {"before": (0, 1), "after": (2, 3)}.items():
            observed = set()
            for index in run_indexes:
                items = [
                    item
                    for item in evidence["runs"][index]["provenance"]["immutable_inputs"]
                    if item.get("input_id") == SOURCE_CAPTURE_INPUT_ID
                ]
                if len(items) != 1:
                    fail("provenance.source_capture")
                observed.add((items[0].get("digest"), items[0].get("byte_length")))
            if len(observed) != 1:
                fail("provenance.source_capture")
            public_bindings[source_key] = observed.pop()
        if public_bindings["before"] == public_bindings["after"]:
            fail("provenance.source_capture")
    for run in evidence["runs"]:
        views = {view["view_id"]: view for view in run["protected_views"]}
        expected = {
            f"view:{view_id}": (view["raw_payload_hash"], len(canonical(view["payload"])))
            for view_id, view in views.items()
        }
        expected_kinds = {
            f"view:{view_id}": "PROTECTED_VIEW_PAYLOAD" for view_id in views
        }
        expected.update(m7_inputs)
        m7_kinds = {
            "m7:graph": "M7_GRAPH",
            "m7:replay": "M7_REPLAY",
            "m7:registry": "M7_REGISTRY",
            "m7:source-bundle": "M7_SOURCE_BUNDLE",
            "m7:source-replay": "M7_SOURCE_REPLAY",
            "m7:terminal-graph": "M7_TERMINAL_GRAPH",
            "m7:terminal-replay": "M7_TERMINAL_REPLAY",
            "m7:terminal-source-bundle": "M7_TERMINAL_SOURCE_BUNDLE",
            "m7:terminal-source-replay": "M7_TERMINAL_SOURCE_REPLAY",
            "m7:private-graph": "M7_PRIVATE_GRAPH",
            "m7:private-replay": "M7_PRIVATE_REPLAY",
            "m7:private-source-bundle": "M7_PRIVATE_SOURCE_BUNDLE",
            "m7:private-source-replay": "M7_PRIVATE_SOURCE_REPLAY",
            "m7:status-projection": "M7_PUBLIC_STATUS",
        }
        expected_kinds.update(
            {input_id: m7_kinds[input_id] for input_id in m7_inputs}
        )
        if evidence["evidence_class"] == "CAPTURED_RUNTIME_EVIDENCE":
            source_key = "before" if run["state"] in {
                "EEBUS_CONNECTED_BASELINE", "EEBUS_CONNECTED_RAW_WITHHELD"
            } else "after"
            if require_private:
                source = source_bindings[source_key]
                expected[SOURCE_CAPTURE_INPUT_ID] = (
                    source["digest"], source["byte_length"]
                )
                if (
                    source["service_count"] != run["state_evidence"]["service_count"]
                    or set(source["views"]) != set(views)
                    or any(
                        canonical(views[view_id]["payload"]["data"])
                        != canonical(source["views"][view_id])
                        for view_id in views
                    )
                ):
                    fail("provenance.source_capture")
            else:
                candidates = [
                    item for item in run["provenance"]["immutable_inputs"]
                    if item.get("input_id") == SOURCE_CAPTURE_INPUT_ID
                ]
                if len(candidates) != 1:
                    fail("provenance.source_capture")
                source = candidates[0]
                if (
                    source.get("kind") != SOURCE_CAPTURE_INPUT_KIND
                    or not isinstance(source.get("digest"), str)
                    or not DIGEST_RE.fullmatch(source["digest"])
                    or not integer(source.get("byte_length"), 1)
                ):
                    fail("provenance.source_capture")
                expected[SOURCE_CAPTURE_INPUT_ID] = (
                    source["digest"], source["byte_length"]
                )
            expected_kinds[SOURCE_CAPTURE_INPUT_ID] = SOURCE_CAPTURE_INPUT_KIND
        transition = run["state_evidence"]["restart_transition"]
        if transition is not None:
            expected.update(
                {
                    "restart:process-event": (
                        digest(RESTART_PROCESS_EVENT_DOMAIN, transition["process_event"]),
                        len(canonical(transition["process_event"])),
                    ),
                    "restart:before-snapshot": (
                        digest(RESTART_SNAPSHOT_DOMAIN, transition["before_snapshot"]),
                        len(canonical(transition["before_snapshot"])),
                    ),
                    "restart:after-snapshot": (
                        digest(RESTART_SNAPSHOT_DOMAIN, transition["after_snapshot"]),
                        len(canonical(transition["after_snapshot"])),
                    ),
                    "restart:session-event": (
                        digest(RESTART_SESSION_EVENT_DOMAIN, transition["session_event"]),
                        len(canonical(transition["session_event"])),
                    ),
                }
            )
            expected_kinds.update(
                {
                    "restart:process-event": "RESTART_PROCESS_EVENT",
                    "restart:before-snapshot": "RESTART_STATE_SNAPSHOT",
                    "restart:after-snapshot": "RESTART_STATE_SNAPSHOT",
                    "restart:session-event": "RESTART_SESSION_EVENT",
                }
            )
        actual = {
            item["input_id"]: (item["digest"], item["byte_length"])
            for item in run["provenance"]["immutable_inputs"]
        }
        actual_kinds = {
            item["input_id"]: item["kind"]
            for item in run["provenance"]["immutable_inputs"]
        }
        if actual != expected or actual_kinds != expected_kinds:
            fail("provenance.runtime")


def check_config(evidence: dict[str, Any]) -> None:
    for run in evidence["runs"]:
        config = run["provenance"]["config"]
        if config["config_hash"] != digest(CONFIG_DOMAIN, config["payload"]):
            fail("provenance.config")
        expected_outbound = evidence["evidence_class"] == "CAPTURED_RUNTIME_EVIDENCE"
        if (
            config["payload"]["outbound_enabled"] is not expected_outbound
            or config["payload"]["public_v2_enabled"]
        ):
            fail("provenance.config")


def check_auth_mask(evidence: dict[str, Any]) -> None:
    profile = evidence["normalization"]
    profile_view = {key: value for key, value in profile.items() if key != "profile_digest"}
    if profile["profile_digest"] != digest(PROFILE_DOMAIN, profile_view):
        fail("provenance.auth_mask")
    first_auth = evidence["runs"][0]["provenance"]["auth_scope"]
    for run in evidence["runs"]:
        provenance = run["provenance"]
        auth = provenance["auth_scope"]
        auth_view = {key: value for key, value in auth.items() if key != "scope_hash"}
        if (
            auth != first_auth
            or auth["principal_class"] != "READ_ONLY_TEST"
            or auth["permissions"] != READ_ONLY_PERMISSIONS
            or auth["scope_hash"] != digest(AUTH_DOMAIN, auth_view)
            or provenance["mask_scope_digest"] != profile["profile_digest"]
        ):
            fail("provenance.auth_mask")


def check_clock(evidence: dict[str, Any]) -> None:
    clock = evidence["capture_clock"]
    view = {key: value for key, value in clock.items() if key != "clock_hash"}
    if (
        clock["basis"] != "MONOTONIC_CAPTURE_OFFSETS"
        or not isinstance(clock["wall_anchor_utc"], str)
        or not RFC3339_UTC_RE.fullmatch(clock["wall_anchor_utc"])
        or clock["clock_hash"] != digest(CLOCK_DOMAIN, view)
        or not integer(clock["verification_offset_ns"])
        or not integer(clock["max_capture_age_ns"], 1)
    ):
        fail("provenance.clock")
    for run in evidence["runs"]:
        if (
            run["provenance"]["capture_clock_id"] != clock["clock_id"]
            or run["capture_offset_ns"] > clock["verification_offset_ns"]
            or clock["verification_offset_ns"] - run["capture_offset_ns"]
            > clock["max_capture_age_ns"]
        ):
            fail("provenance.clock")


def check_ordering(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    runs = evidence["runs"]
    scenario_order = registry["scenario_profiles"][evidence["evidence_class"]]
    if [run["state"] for run in runs] != scenario_order:
        fail("ordering.duplicate")
    if len({run["run_id"] for run in runs}) != len(runs):
        fail("ordering.duplicate")
    offsets = [run["capture_offset_ns"] for run in runs]
    if offsets != sorted(offsets) or len(set(offsets)) != len(offsets):
        fail("ordering.duplicate")
    for run in runs:
        views = [view["view_id"] for view in run["protected_views"]]
        inputs = [item["input_id"] for item in run["provenance"]["immutable_inputs"]]
        expected_inputs = [f"view:{item}" for item in views]
        if evidence["evidence_class"] == "CAPTURED_RUNTIME_EVIDENCE":
            expected_inputs.extend(
                [
                    "m7:terminal-graph",
                    "m7:terminal-replay",
                    "m7:registry",
                    "m7:terminal-source-bundle",
                    "m7:terminal-source-replay",
                    "m7:private-graph",
                    "m7:private-replay",
                    "m7:private-source-bundle",
                    "m7:private-source-replay",
                    "m7:status-projection",
                    SOURCE_CAPTURE_INPUT_ID,
                ]
            )
        else:
            expected_inputs.extend(
                [
                    "m7:graph",
                    "m7:replay",
                    "m7:registry",
                    "m7:source-bundle",
                    "m7:source-replay",
                ]
            )
        if run["state_evidence"]["restart_transition"] is not None:
            expected_inputs.extend(
                [
                    "restart:process-event",
                    "restart:before-snapshot",
                    "restart:after-snapshot",
                    "restart:session-event",
                ]
            )
        if (
            len(views) != len(set(views))
            or len(inputs) != len(set(inputs))
            or inputs != expected_inputs
            or (
                len(views) == len(registry["protected_views"])
                and views != registry["protected_views"]
            )
        ):
            fail("ordering.duplicate")


def _fact_summaries(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": fact["candidate_id"],
            "status": fact["status"],
            "terminal_negative_state": fact["terminal_negative_state"],
            "visibility_channel": "CANDIDATE_DEBUG_REPLAY",
        }
        for fact in graph["facts"]
    ]


def _state_tuple(state: dict[str, Any]) -> tuple[Any, ...]:
    return (
        state["outcome"],
        state["eebus_runtime_enabled"],
        state["candidate_graph_enabled"],
        state["service_count"],
        state["raw_only_count"],
        state["candidate_count"],
        state["conflict_count"],
        state["withheld_count"],
        state["degraded"],
        state["facts"],
    )


def check_states(evidence: dict[str, Any], graph: dict[str, Any]) -> None:
    if evidence["evidence_class"] == "SYNTHETIC_OFFLINE_FIXTURE":
        expected = {
            "EEBUS_DISABLED_BASELINE": ("BASELINE_CAPTURED", False, False, 0, 0, 0, 0, 0, False, []),
            "EEBUS_DISABLED_CONFIRMED": ("DISABLED_CONFIRMED", False, False, 0, 0, 0, 0, 0, False, []),
            "EEBUS_ENABLED_NO_SERVICES": ("NO_SERVICES_OBSERVED", True, True, 0, 0, 0, 0, 0, True, []),
            "EEBUS_CONNECTED_CANDIDATE_ONLY": (
                "CANDIDATE_ONLY_OBSERVED", True, True, 1, 0, 1, 0, 0, False,
                [{"candidate_id": "m7-candidate-synthetic-0001", "status": "CANDIDATE", "terminal_negative_state": None, "visibility_channel": "CANDIDATE_DEBUG_REPLAY"}],
            ),
            "EEBUS_CONFLICTED_WITHHELD": (
                "CONFLICT_WITHHELD_OBSERVED", True, True, 1, 0, 0, 1, 1, True,
                [{"candidate_id": "m7-candidate-synthetic-conflict-0001", "status": "WITHHELD", "terminal_negative_state": "CONFLICT", "visibility_channel": "CANDIDATE_DEBUG_REPLAY"}],
            ),
            "EEBUS_DISABLED_ROLLBACK": ("ROLLBACK_BASELINE_RESTORED", False, False, 0, 0, 0, 0, 0, False, []),
        }
    else:
        facts = _fact_summaries(graph)
        counts = {
            status: sum(fact["status"] == status for fact in facts)
            for status in ("RAW_ONLY", "CANDIDATE", "CONFLICTED", "WITHHELD")
        }
        if counts["RAW_ONLY"] < 1 or counts["WITHHELD"] < 1:
            fail("state.evidence")
        services = evidence["runs"][0]["state_evidence"]["service_count"]
        if services < 1:
            fail("state.evidence")
        connected = (
            True,
            services,
            counts["RAW_ONLY"],
            counts["CANDIDATE"],
            counts["CONFLICTED"],
            counts["WITHHELD"],
        )
        expected = {
            "EEBUS_CONNECTED_BASELINE": ("CONNECTED_BASELINE_CAPTURED", True, False, services, 0, 0, 0, 0, False, []),
            "EEBUS_CONNECTED_RAW_WITHHELD": ("RAW_WITHHELD_OBSERVED", connected[0], True, *connected[1:], False, facts),
            "EEBUS_RESTART_PERSISTED": ("RESTART_PERSISTED", connected[0], True, *connected[1:], False, facts),
            "EEBUS_CONNECTED_ROLLBACK": ("GRAPH_EVIDENCE_DROPPED", True, False, services, 0, 0, 0, 0, False, []),
        }
    for run in evidence["runs"]:
        state = run["state_evidence"]
        config = run["provenance"]["config"]["payload"]
        if (
            _state_tuple(state) != expected[run["state"]]
            or state["empty_success"] is not False
            or config["eebus_runtime_enabled"] != state["eebus_runtime_enabled"]
            or config["candidate_graph_enabled"] != state["candidate_graph_enabled"]
        ):
            fail("state.evidence")


def check_restart(evidence: dict[str, Any]) -> None:
    runs = evidence["runs"]
    transitions = [run["state_evidence"]["restart_transition"] for run in runs]
    if evidence["evidence_class"] == "SYNTHETIC_OFFLINE_FIXTURE":
        if any(item is not None for item in transitions):
            fail("state.evidence")
        return
    process_ids = [run["provenance"]["process_instance_id"] for run in runs]
    transition = transitions[2]
    if not isinstance(transition, dict):
        fail("state.evidence")
    process_event = transition["process_event"]
    before_snapshot = transition["before_snapshot"]
    after_snapshot = transition["after_snapshot"]
    session_event = transition["session_event"]
    if (
        process_ids[0] != process_ids[1]
        or process_ids[2] != process_ids[3]
        or process_ids[0] == process_ids[2]
        or transitions[:2] != [None, None]
        or transitions[3] is not None
        or transition["before_process_instance_id"] != process_ids[1]
        or transition["after_process_instance_id"] != process_ids[2]
        or transition["before_process_instance_id"]
        == transition["after_process_instance_id"]
        or transition["before_trust_state_hash"]
        != transition["after_trust_state_hash"]
        or transition["before_peer_binding_hash"]
        != transition["after_peer_binding_hash"]
        or transition["session_reconnected"] is not True
        or process_event["event_id"] != transition["event_id"]
        or process_event["event_type"] != "PROCESS_RESTART_OBSERVED"
        or process_event["before_process_instance_id"] != process_ids[1]
        or process_event["after_process_instance_id"] != process_ids[2]
        or process_event["observed_at_offset_ns"] != runs[2]["capture_offset_ns"]
        or before_snapshot["process_instance_id"] != process_ids[1]
        or before_snapshot["capture_offset_ns"] != runs[1]["capture_offset_ns"]
        or after_snapshot["process_instance_id"] != process_ids[2]
        or after_snapshot["capture_offset_ns"] != runs[2]["capture_offset_ns"]
        or before_snapshot["trust_state_id"] != after_snapshot["trust_state_id"]
        or before_snapshot["peer_binding_id"] != after_snapshot["peer_binding_id"]
        or before_snapshot["session_id"] == after_snapshot["session_id"]
        or before_snapshot["session_state"] != "CONNECTED"
        or after_snapshot["session_state"] != "CONNECTED"
        or transition["before_trust_state_hash"]
        != digest(
            RESTART_TRUST_DOMAIN,
            {"trust_state_id": before_snapshot["trust_state_id"]},
        )
        or transition["after_trust_state_hash"]
        != digest(
            RESTART_TRUST_DOMAIN,
            {"trust_state_id": after_snapshot["trust_state_id"]},
        )
        or transition["before_peer_binding_hash"]
        != digest(
            RESTART_PEER_DOMAIN,
            {"peer_binding_id": before_snapshot["peer_binding_id"]},
        )
        or transition["after_peer_binding_hash"]
        != digest(
            RESTART_PEER_DOMAIN,
            {"peer_binding_id": after_snapshot["peer_binding_id"]},
        )
        or session_event["event_type"] != "SESSION_RECONNECTED_OBSERVED"
        or session_event["process_instance_id"] != process_ids[2]
        or session_event["session_id"] != after_snapshot["session_id"]
        or session_event["observed_at_offset_ns"] != runs[2]["capture_offset_ns"]
        or session_event["state"] != "CONNECTED"
    ):
        fail("state.evidence")


def check_view_coverage(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    for run in evidence["runs"]:
        if [view["view_id"] for view in run["protected_views"]] != registry["protected_views"]:
            fail("view.coverage")


def _resolve_pointer(value: Any, pointer: str) -> tuple[Any, str | int]:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        fail("canonicalization.invalid")
    parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]
    current = value
    try:
        for part in parts[:-1]:
            current = current[int(part)] if isinstance(current, list) else current[part]
        leaf: str | int = int(parts[-1]) if isinstance(current, list) else parts[-1]
        target = current[leaf]
    except (KeyError, IndexError, TypeError, ValueError):
        fail("canonicalization.invalid")
    if not isinstance(target, str):
        fail("canonicalization.invalid")
    return current, leaf


def normalized_payload(payload: Any, rule: dict[str, Any], profile: dict[str, Any]) -> Any:
    result = copy.deepcopy(payload)
    pointers = rule["timestamp_pointers"] + rule["mask_pointers"]
    if len(pointers) != len(set(pointers)):
        fail("canonicalization.invalid")
    for pointer in rule["timestamp_pointers"]:
        parent, leaf = _resolve_pointer(result, pointer)
        if not RFC3339_UTC_RE.fullmatch(parent[leaf]):
            fail("canonicalization.invalid")
        parent[leaf] = profile["timestamp_replacement"]
    for pointer in rule["mask_pointers"]:
        parent, leaf = _resolve_pointer(result, pointer)
        parent[leaf] = profile["mask_replacement"]
    return result


def payload_shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: payload_shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return [payload_shape(item) for item in value]
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    return "string"


def check_normalization(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    profile = evidence["normalization"]
    if (
        profile["profile_id"] != "multi-runtime-coexistence-no-drift-v1"
        or profile["canonicalization"] != "RFC8785_JCS_INTEGER_SUBSET"
        or profile["timestamp_replacement"] != "<TIMESTAMP>"
        or profile["mask_replacement"] != "<MASKED>"
        or profile["view_rules"] != registry["view_rules"]
    ):
        fail("canonicalization.invalid")


def check_payload_hashes(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    rules = {rule["view_id"]: rule for rule in registry["view_rules"]}
    for run in evidence["runs"]:
        for view in run["protected_views"]:
            if view["capture_path"] != rules[view["view_id"]]["capture_path"] or view["media_type"] != "application/json":
                fail("hash.payload")
            normalized = normalized_payload(
                view["payload"], rules[view["view_id"]], evidence["normalization"]
            )
            if (
                view["raw_payload_hash"] != digest(RAW_PAYLOAD_DOMAIN, view["payload"])
                or view["shape_hash"] != digest(SHAPE_DOMAIN, payload_shape(view["payload"]))
                or view["canonical_payload_hash"]
                != digest(CANONICAL_PAYLOAD_DOMAIN, normalized)
            ):
                fail("hash.payload")


def _compact_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.casefold())


def _key_tokens(key: str) -> tuple[str, ...]:
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key)
    return tuple(re.findall(r"[a-z0-9]+", separated.casefold()))


def _contains_token_sequence(
    tokens: tuple[str, ...],
    patterns: set[tuple[str, ...]] | frozenset[tuple[str, ...]],
) -> bool:
    return any(
        tokens[index : index + len(pattern)] == pattern
        for pattern in patterns
        for index in range(len(tokens) - len(pattern) + 1)
    )


def _contains_candidate_field_key(value: str) -> bool:
    return bool(
        _compact_key(value) in CANDIDATE_LEAK_COMPACT_NAMES
        or _contains_token_sequence(_key_tokens(value), CANDIDATE_LEAK_TOKEN_PATTERNS)
    )


def _is_candidate_field_value(value: str) -> bool:
    return bool(
        _compact_key(value) in CANDIDATE_LEAK_COMPACT_NAMES
        or _key_tokens(value) in CANDIDATE_LEAK_TOKEN_PATTERNS
    )


def _terminal_vocabulary(graph: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for fact in graph["facts"]:
        terminal = fact.get("terminal_negative_state")
        if isinstance(terminal, str):
            values.add(terminal)
        source_terminal = fact.get("provenance", {}).get("source_terminal")
        if not isinstance(source_terminal, dict):
            continue
        for key in (
            "binding_source_kind",
            "error_category",
            "source_contract",
            "source_id",
            "state",
        ):
            item = source_terminal.get(key)
            if isinstance(item, str):
                values.add(item)
    return values


def _contains_candidate_leak(
    value: Any, candidate_ids: set[str], terminal_values: set[str]
) -> bool:
    if isinstance(value, dict):
        if any(_contains_candidate_field_key(key) for key in value):
            return True
        return any(
            _contains_candidate_leak(item_key, candidate_ids, terminal_values)
            or _contains_candidate_leak(item, candidate_ids, terminal_values)
            for item_key, item in value.items()
        )
    if isinstance(value, list):
        return any(
            _contains_candidate_leak(item, candidate_ids, terminal_values)
            for item in value
        )
    return isinstance(value, str) and (
        _is_candidate_field_value(value)
        or value
        in {
            "RAW_ONLY",
            "CANDIDATE",
            "CONFLICTED",
            "WITHHELD",
            "WITHHELD/CONFLICT",
            "CANDIDATE_DEBUG_REPLAY",
        }
        or any(candidate_id in value for candidate_id in candidate_ids)
        or any(
            re.search(
                rf"(?<![a-z0-9_]){re.escape(terminal)}(?![a-z0-9_])",
                value,
                re.IGNORECASE,
            )
            is not None
            for terminal in terminal_values
        )
        or re.search(
            r"(?i)(?<![a-z0-9_])m7-candidate-[a-z0-9-]+(?![a-z0-9_-])",
            value,
        )
        is not None
    )


def check_anti_leak(evidence: dict[str, Any], *graphs: dict[str, Any]) -> None:
    candidate_ids = {
        fact["candidate_id"] for graph in graphs for fact in graph["facts"]
    }
    terminal_values = set().union(*(_terminal_vocabulary(graph) for graph in graphs))
    for run in evidence["runs"]:
        for fact in run["state_evidence"]["facts"]:
            candidate_id = fact.get("candidate_id")
            if isinstance(candidate_id, str):
                candidate_ids.add(candidate_id)
            terminal = fact.get("terminal_negative_state")
            if isinstance(terminal, str):
                terminal_values.add(terminal)
    for run in evidence["runs"]:
        if any(
            _contains_candidate_leak(view["payload"], candidate_ids, terminal_values)
            for view in run["protected_views"]
        ):
            fail("anti_leak.candidate")


def _contains_private_ipv6(value: str) -> bool:
    for match in IPV6_CANDIDATE_RE.finditer(value):
        candidate_value = match.group(0).split("%", 1)[0]
        try:
            address = ipaddress.ip_address(candidate_value)
        except ValueError:
            continue
        if isinstance(address, ipaddress.IPv6Address) and (
            not address.is_global or address.is_multicast
        ):
            return True
    return False


def _contains_non_public_ipv4(value: str) -> bool:
    for match in DOTTED_NUMERIC_RUN_RE.finditer(value):
        candidate_value = match.group(0)
        if candidate_value.count(".") < 3:
            continue
        trailing_dots = len(candidate_value) - len(candidate_value.rstrip("."))
        if trailing_dots:
            return True
        try:
            address = ipaddress.ip_address(candidate_value)
        except ValueError:
            return True
        if isinstance(address, ipaddress.IPv4Address) and (
            not address.is_global or address.is_multicast
        ):
            return True
    return False


def _valid_hash_like(value: Any) -> bool:
    return isinstance(value, str) and bool(
        DIGEST_RE.fullmatch(value)
        or SHA_RE.fullmatch(value)
        or re.fullmatch(r"[a-z0-9.-]+:sha256:[0-9a-f]{64}", value)
    )


def _valid_redacted_identity(value: Any) -> bool:
    if isinstance(value, list):
        return all(_valid_redacted_identity(item) for item in value)
    return isinstance(value, str) and bool(REDACTED_ID_RE.fullmatch(value))


def _contains_credential_value(value: str) -> bool:
    if CREDENTIAL_VALUE_RE.search(value):
        return True
    for match in BASIC_CREDENTIAL_RE.finditer(value):
        token = match.group(1)
        if len(token) % 4 != 0:
            continue
        try:
            decoded = base64.b64decode(token, validate=True)
        except ValueError:
            continue
        if b":" in decoded:
            return True
    return False


def _has_public_identity_key(key: str) -> bool:
    normalized = _compact_key(key)
    tokens = _key_tokens(key)
    hash_qualified = bool(tokens and tokens[-1] in {"digest", "hash"})
    identity_tokens = tokens[:-1] if hash_qualified else tokens
    return bool(
        identity_tokens and identity_tokens[-1] in PUBLIC_IDENTITY_GENERIC_TOKENS
        or hash_qualified
        and identity_tokens
        and identity_tokens[-1] in PUBLIC_IDENTITY_HASH_ROOTS
        or any(
            left in PUBLIC_IDENTITY_PREFIXES and right in PUBLIC_IDENTITY_SUFFIXES
            for left, right in zip(identity_tokens, identity_tokens[1:])
        )
        or normalized in PUBLIC_IDENTITY_COMPACT_NAMES
    )


def _has_sensitive_key(key: str, value: Any) -> bool:
    normalized = _compact_key(key)
    tokens = _key_tokens(key)
    if (
        normalized.endswith(("hash", "digest"))
        and isinstance(value, str)
        and any(
            _contains_token_sequence(tokens, {pattern})
            for pattern in {
                ("encryption", "key"),
                ("private", "key"),
                ("signing", "key"),
                ("tls", "key"),
            }
        )
        and (
            DIGEST_RE.fullmatch(value)
            or re.fullmatch(r"[a-z0-9.-]+:sha256:[0-9a-f]{64}", value)
        )
    ):
        return False
    if (
        tokens
        and tokens[-1] in {"count", "counts", "total", "totals"}
        and isinstance(value, int)
        and not isinstance(value, bool)
    ):
        return False
    if (
        tokens
        and tokens[-1] in {"available", "enabled", "required", "supported"}
        and isinstance(value, bool)
    ):
        return False
    if (
        tokens
        and tokens[-1] in {"description", "detail", "message", "note"}
        and isinstance(value, str)
        and len(value.split()) >= 3
        and not _contains_credential_value(value)
    ):
        return False
    return bool(
        normalized in SENSITIVE_KEY_COMPACT_NAMES
        or _contains_token_sequence(tokens, SENSITIVE_KEY_TOKEN_PATTERNS)
    )


def _declared_key_value_pairs(value: dict[str, Any]) -> list[tuple[str, Any]]:
    declared_keys = [
        item
        for item_key, item in value.items()
        if _compact_key(item_key) in {"key", "name"} and isinstance(item, str)
    ]
    declared_values = [
        item for item_key, item in value.items() if _compact_key(item_key) == "value"
    ]
    return [
        (declared_key, item)
        for declared_key in declared_keys
        for item in declared_values
    ]


def _contains_identity_descriptor_value(value: Any, declared_key: str) -> bool:
    if isinstance(value, dict):
        for item_key, item in value.items():
            if _compact_key(item_key) in {
                "const",
                "default",
                "enum",
                "example",
                "examples",
                "value",
                "values",
            } and _contains_public_secret(item, declared_key):
                return True
            if _contains_identity_descriptor_value(item, declared_key):
                return True
        return False
    if isinstance(value, list):
        return any(
            _contains_identity_descriptor_value(item, declared_key) for item in value
        )
    return False


def _contains_public_identity_descriptor(value: Any) -> bool:
    if isinstance(value, dict):
        declared_keys = [
            item
            for item_key, item in value.items()
            if _compact_key(item_key) in {"key", "name"}
            and isinstance(item, str)
            and _has_public_identity_key(item)
        ]
        for declared_key in declared_keys:
            for item_key, item in value.items():
                normalized_key = _compact_key(item_key)
                if normalized_key in {
                    "const",
                    "default",
                    "enum",
                    "example",
                    "examples",
                    "value",
                    "values",
                } and _contains_public_secret(item, declared_key):
                    return True
                if normalized_key in {"field", "schema", "type"} and (
                    _contains_identity_descriptor_value(item, declared_key)
                ):
                    return True
    return False


def _contains_public_secret(value: Any, key: str | None = None) -> bool:
    if key is not None:
        normalized = _compact_key(key)
        if (
            normalized in {"source", "target"}
            and (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                or isinstance(value, str)
                and re.fullmatch(r"(?i)(?:0x[0-9a-f]{1,2}|[0-9]{1,3})", value)
                is not None
            )
        ):
            return True
        if _has_sensitive_key(key, value):
            return True
        if normalized.endswith("commit"):
            if value is None:
                return normalized != "sourceparentcommit"
            return not _valid_hash_like(value)
        if normalized.endswith(("hash", "digest")):
            if value is None:
                return True
            return not (
                isinstance(value, str)
                and (
                    DIGEST_RE.fullmatch(value)
                    or re.fullmatch(r"[a-z0-9.-]+:sha256:[0-9a-f]{64}", value)
                )
            )
        if _has_public_identity_key(key):
            return not _valid_redacted_identity(value)
        if normalized.endswith(("spinepath", "spinekind")):
            return True
    if isinstance(value, dict):
        if _contains_public_identity_descriptor(value):
            return True
        if any(
            _contains_public_secret(item, declared_key)
            for declared_key, item in _declared_key_value_pairs(value)
        ):
            return True
        return any(
            _contains_public_secret(item_key)
            or _contains_public_secret(item, item_key)
            for item_key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_public_secret(item) for item in value)
    if not isinstance(value, str):
        return False
    if (
        REDACTED_ID_RE.fullmatch(value)
        or DIGEST_RE.fullmatch(value)
        or re.fullmatch(r"[a-z0-9.-]+:sha256:[0-9a-f]{64}", value)
    ):
        return False
    return bool(
        PRIVATE_KEY_RE.search(value)
        or _contains_credential_value(value)
        or _contains_non_public_ipv4(value)
        or _contains_private_ipv6(value)
        or MAC_RE.search(value)
        or SKI_RE.search(value)
    )


def check_public_redaction(evidence: dict[str, Any]) -> None:
    if evidence["export_tier"] != "PUBLIC_REDACTED":
        fail("redaction.public")
    if _contains_public_secret(evidence):
        fail("redaction.public")


EEBUS_AUTHORITY_KEY_TOKENS = frozenset(
    {
        "adapter",
        "adapters",
        "authority",
        "authorities",
        "backend",
        "backends",
        "driver",
        "drivers",
        "origin",
        "origins",
        "provider",
        "providers",
        "protocol",
        "protocols",
        "runtime",
        "runtimes",
        "source",
        "sources",
        "transport",
        "transports",
    }
)
EEBUS_IDENTIFIER_RE = re.compile(
    r"^eebus(?:(?:[._-]?v?[0-9]+)?(?:[._-][a-z0-9][a-z0-9._-]*)?)?$",
    re.IGNORECASE,
)
EEBUS_DECLARATION_CONTEXT_KEYS = frozenset(
    {"contract", "contracts", "namespace", "namespaces", "surface", "surfaces"}
)


def _normalize_eebus_prefix(value: str) -> str:
    return re.sub(r"(?i)^ee[._-]?bus", "eebus", value)


def _is_eebus_identifier(value: str) -> bool:
    return EEBUS_IDENTIFIER_RE.fullmatch(
        _normalize_eebus_prefix(value).casefold()
    ) is not None


def _eebus_surface_tokens(value: str) -> tuple[str, ...]:
    if any(character.isspace() for character in value):
        return ()
    normalized_value = _normalize_eebus_prefix(value)
    tokens = _key_tokens(normalized_value)
    if tokens and tokens[0] == "eebus":
        return tokens
    compact = _compact_key(normalized_value)
    if compact == "eebus":
        return ("eebus",)
    compact_surface = re.fullmatch(
        r"eebus((?:v|version)?[0-9]+)([a-z0-9]*)", compact
    )
    if compact_surface is not None:
        version, operation = compact_surface.groups()
        if not operation:
            return ("eebus", version)
        for action in sorted(EEBUS_MUTATION_TOOL_ACTIONS, key=len, reverse=True):
            if operation.endswith(action):
                operation_root = operation[: -len(action)]
                return tuple(
                    item
                    for item in ("eebus", version, operation_root, action)
                    if item
                )
        return ("eebus", version, operation)
    return ()


def _is_eebus_authority_declaration_key(key: str) -> bool:
    tokens = set(_eebus_surface_tokens(key) or _key_tokens(key))
    return bool(
        "eebus" in tokens and tokens.intersection(EEBUS_AUTHORITY_KEY_TOKENS)
    )


def _contains_eebus_authority(
    value: Any,
    key: str | None = None,
    *,
    authority_context: bool = False,
) -> bool:
    context = authority_context or bool(
        key
        and (
            _compact_key(key) in EEBUS_AUTHORITY_KEY_TOKENS
            or set(_eebus_surface_tokens(key) or _key_tokens(key)).intersection(
                EEBUS_AUTHORITY_KEY_TOKENS
            )
        )
    )
    if isinstance(value, dict):
        for item_key, item in value.items():
            if _is_eebus_authority_declaration_key(item_key) and bool(item):
                return True
            if _is_eebus_identifier(item_key):
                return True
            if _contains_eebus_authority(
                item, item_key, authority_context=context
            ):
                return True
        return any(
            _contains_eebus_authority(
                item, declared_key, authority_context=context
            )
            for declared_key, item in _declared_key_value_pairs(value)
        )
    if isinstance(value, list):
        return any(
            _contains_eebus_authority(item, key, authority_context=context)
            for item in value
        )
    if not isinstance(value, str):
        return False
    normalized = value.casefold()
    return bool(
        context
        and _is_eebus_identifier(normalized)
    )


def _contains_eebus_reference(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            _contains_eebus_reference(item_key) or _contains_eebus_reference(item)
            for item_key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_eebus_reference(item) for item in value)
    return isinstance(value, str) and bool(_eebus_surface_tokens(value))


def _contains_eebus_namespace_declaration(value: Any) -> bool:
    if isinstance(value, dict):
        if any(
            _compact_key(item_key) in {"namespace", "namespaces"}
            for item_key, _ in _container_declarations(value)
        ):
            return True
        return any(
            _contains_eebus_namespace_declaration(item) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_eebus_namespace_declaration(item) for item in value)
    return False


def _contains_eebus_contract_declaration(value: Any) -> bool:
    if isinstance(value, dict):
        if any(
            _compact_key(item_key) in EEBUS_DECLARATION_CONTEXT_KEYS
            and _contains_eebus_reference(item)
            for item_key, item in _container_declarations(value)
        ):
            return True
        return any(
            _contains_eebus_contract_declaration(item) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_eebus_contract_declaration(item) for item in value)
    return False


def _contains_structured_authority_declaration(value: Any) -> bool:
    if isinstance(value, dict):
        if any(
            _compact_key(item_key) in {"authority", "authorities"}
            and isinstance(item, (dict, list))
            and bool(item)
            for item_key, item in _container_declarations(value)
        ):
            return True
        return any(
            _contains_structured_authority_declaration(item)
            for item in value.values()
        )
    if isinstance(value, list):
        return any(
            _contains_structured_authority_declaration(item) for item in value
        )
    return False


def _contains_contract_descriptor_declaration(value: Any) -> bool:
    if isinstance(value, dict):
        for item_key, item in value.items():
            normalized_key = _compact_key(item_key)
            if normalized_key in {"propertynames", "patternproperties"} and bool(
                item
            ):
                return True
            if (
                normalized_key in {"key", "name"}
                and isinstance(item, str)
                and _compact_key(item)
                in {
                    "authority",
                    "authorities",
                    "contract",
                    "contracts",
                    "namespace",
                    "namespaces",
                    "surface",
                    "surfaces",
                }
            ):
                return True
        return any(
            _contains_contract_descriptor_declaration(item)
            for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_contract_descriptor_declaration(item) for item in value)
    return False


def _container_declarations(value: Any) -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        return [*value.items(), *_declared_key_value_pairs(value)]
    if isinstance(value, list):
        declarations: list[tuple[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                declarations.extend(item.items())
                declarations.extend(_declared_key_value_pairs(item))
        return declarations
    return []


def _exact_version_one(value: Any) -> bool:
    return integer(value, 1) and value == 1


def _is_alias_declaration_key(key: str) -> bool:
    normalized = _compact_key(key)
    if normalized in {
        "alias",
        "aliases",
        "compatibilityalias",
        "compatibilityaliases",
    }:
        return True
    tokens = set(_key_tokens(key))
    return bool(
        tokens.intersection(
            {
                "accepted",
                "alternate",
                "compat",
                "compatibility",
                "deprecated",
                "legacy",
                "previous",
            }
        )
        and tokens.intersection(
            {"alias", "aliases", "name", "names", "namespace", "namespaces"}
        )
    )


def _invalid_eebus_declarations(
    declarations: list[tuple[str, Any]],
    *,
    reject_any_alias: bool,
    eebus_context: bool,
) -> bool:
    namespaces = [
        item
        for item_key, item in declarations
        if _compact_key(item_key) in {"namespace", "namespaces"}
        and isinstance(item, str)
    ]
    eebus_namespace = eebus_context or any(
        namespace.casefold().startswith("eebus") for namespace in namespaces
    )
    if any(
        namespace.casefold() != "eebus.v1"
        for namespace in namespaces
        if namespace.casefold().startswith("eebus")
    ):
        return True
    for item_key, item in declarations:
        if _is_alias_declaration_key(item_key) and item is not None and item != "":
            if (not isinstance(item, (list, dict)) or item) and (
                reject_any_alias
                or eebus_namespace
                or _contains_eebus_reference(item)
            ):
                return True
    if eebus_namespace:
        version_values = [
            item
            for item_key, item in declarations
            if _compact_key(item_key)
            in {
                "apiversion",
                "contractversion",
                "publicversion",
                "revision",
                "schema",
                "schemaversion",
                "version",
            }
        ]
        public_v2_values = [
            item
            for item_key, item in declarations
            if _compact_key(item_key) == "publicv2"
        ]
        if any(not _exact_version_one(item) for item in version_values) or any(
            item is not False for item in public_v2_values
        ):
            return True
    return False


def _contains_non_v1_eebus_surface(
    value: Any, *, reject_any_alias: bool = False, eebus_context: bool = False
) -> bool:
    if isinstance(value, dict):
        if any(_is_eebus_identifier(item_key) for item_key in value):
            return True
        declarations = _container_declarations(value)
        child_context = eebus_context or any(
            _compact_key(item_key) in EEBUS_DECLARATION_CONTEXT_KEYS
            and _contains_eebus_reference(item)
            for item_key, item in declarations
        )
        if _invalid_eebus_declarations(
            declarations,
            reject_any_alias=reject_any_alias,
            eebus_context=eebus_context,
        ):
            return True
        return any(
            _contains_non_v1_eebus_surface(
                item_key,
                reject_any_alias=reject_any_alias,
                eebus_context=child_context,
            )
            or _contains_non_v1_eebus_surface(
                item,
                reject_any_alias=reject_any_alias,
                eebus_context=child_context,
            )
            for item_key, item in value.items()
        )
    if isinstance(value, list):
        declarations = _container_declarations(value)
        child_context = eebus_context or any(
            _compact_key(item_key) in EEBUS_DECLARATION_CONTEXT_KEYS
            and _contains_eebus_reference(item)
            for item_key, item in declarations
        )
        if _invalid_eebus_declarations(
            declarations,
            reject_any_alias=reject_any_alias,
            eebus_context=eebus_context,
        ):
            return True
        return any(
            _contains_non_v1_eebus_surface(
                item,
                reject_any_alias=reject_any_alias,
                eebus_context=child_context,
            )
            for item in value
        )
    if not isinstance(value, str):
        return False
    normalized = value.casefold()
    compact = _compact_key(normalized)
    versioned_surface = re.fullmatch(r"eebus(?:v|version)?([0-9]+)", compact)
    surface_tokens = _eebus_surface_tokens(value)
    token_version = (
        re.fullmatch(r"(?:v|version)?([0-9]+)", surface_tokens[1])
        if len(surface_tokens) > 1
        else None
    )
    return bool(
        (versioned_surface is not None and versioned_surface.group(1) != "1")
        or (token_version is not None and token_version.group(1) != "1")
        or (
            TOOL_NAME_RE.fullmatch(normalized)
            and normalized.startswith("eebus.")
            and normalized != "eebus.v1"
            and not normalized.startswith("eebus.v1.")
        )
    )


def _contains_later_milestone_declaration(
    value: Any, *, milestone_context: bool = False
) -> bool:
    if isinstance(value, dict):
        for item_key, item in _container_declarations(value):
            normalized = _compact_key(item_key)
            if normalized.startswith(("m85", "m9")):
                return True
            key_tokens = set(_key_tokens(item_key))
            child_context = milestone_context or bool(
                key_tokens.intersection(
                    {
                        "gate",
                        "gates",
                        "milestone",
                        "milestones",
                        "phase",
                        "phases",
                        "release",
                        "releases",
                    }
                )
            )
            if child_context and isinstance(item, str):
                item_normalized = _compact_key(item)
                if item_normalized.startswith(("m85", "m9")):
                    return True
            if _contains_later_milestone_declaration(
                item, milestone_context=child_context
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _contains_later_milestone_declaration(
                item, milestone_context=milestone_context
            )
            for item in value
        )
    return bool(
        milestone_context
        and isinstance(value, str)
        and _compact_key(value).startswith(("m85", "m9"))
    )


EEBUS_WRITE_DECLARATION_KEYS = frozenset(
    {
        "mutationauthority",
        "mutationenabled",
        "mutationsenabled",
        "writeauthority",
        "writeenabled",
        "writesenabled",
    }
)
EEBUS_MUTATION_TOOL_ACTIONS = frozenset(
    {
        "authorize",
        "create",
        "delete",
        "pair",
        "register",
        "set",
        "trust",
        "unpair",
        "unregister",
        "untrust",
        "update",
        "write",
    }
)


def _contains_eebus_write_surface(
    value: Any, *, eebus_context: bool = False
) -> bool:
    if isinstance(value, dict):
        declarations = _container_declarations(value)
        child_context = (
            eebus_context
            or any(
                _compact_key(item_key) in EEBUS_DECLARATION_CONTEXT_KEYS
                and _contains_eebus_reference(item)
                for item_key, item in declarations
            )
            or any(_is_eebus_identifier(item_key) for item_key in value)
        )
        if child_context and any(
            _compact_key(item_key) in EEBUS_WRITE_DECLARATION_KEYS
            and bool(item)
            for item_key, item in declarations
        ):
            return True
        return any(
            _contains_eebus_write_surface(item, eebus_context=child_context)
            for item in value.values()
        )
    if isinstance(value, list):
        return any(
            _contains_eebus_write_surface(item, eebus_context=eebus_context)
            for item in value
        )
    if not isinstance(value, str):
        return False
    normalized = value.casefold()
    surface_tokens = _eebus_surface_tokens(value)
    if (
        len(surface_tokens) > 2
        and surface_tokens[0] == "eebus"
        and surface_tokens[1] in {"1", "v1", "version1"}
    ):
        operation_tokens = surface_tokens[2:]
    elif eebus_context and TOOL_NAME_RE.fullmatch(normalized):
        operation_tokens = _key_tokens(normalized)
    else:
        return False
    if operation_tokens == ("snapshot", "drop"):
        return False
    return any(token in EEBUS_MUTATION_TOOL_ACTIONS for token in operation_tokens)


def check_authority(evidence: dict[str, Any]) -> None:
    for run in evidence["runs"][:-1]:
        registry_view = next(
            view for view in run["protected_views"] if view["view_id"] == "semantic.registry"
        )
        routes_view = next(
            view for view in run["protected_views"] if view["view_id"] == "command.routing"
        )
        registry_data = registry_view["payload"]["data"]
        routes_data = routes_view["payload"]["data"]
        if (
            registry_data["authority"] != "ebus.promoted"
            or _contains_eebus_authority(registry_data)
        ):
            fail("authority.ebus")
        if any(
            leaf.get("source") != "ebus"
            or leaf.get("promotion_state") != "PROMOTED"
            for leaf in registry_data["leaves"]
        ):
            fail("authority.ebus")
        if _contains_eebus_authority(routes_data) or any(
            route["source"] != "ebus" for route in routes_data["routes"]
        ):
            fail("authority.ebus")


def check_scope(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    scope = evidence["scope"]
    expected_live_claim = evidence["evidence_class"] == "CAPTURED_RUNTIME_EVIDENCE"
    if (
        scope["gate"] != registry["gate"]
        or scope["claims"] != ["EEBUS-G18"]
        or scope["excluded_gates"] != registry["excluded_gates"]
        or scope["live_vr940_claim"] is not expected_live_claim
        or scope["public_version_policy"] != "V1_ONLY_NO_PUBLIC_V2"
    ):
        fail("gate.scope")
    for run_index, run in enumerate(evidence["runs"]):
        rollback_run = run_index == len(evidence["runs"]) - 1
        if rollback_run:
            continue
        if any(
            _contains_non_v1_eebus_surface(view["payload"])
            or _contains_later_milestone_declaration(view["payload"])
            or _contains_eebus_write_surface(view["payload"])
            or view["view_id"] != "mcp.eebus.v1.contract"
            and (
                _contains_eebus_namespace_declaration(view["payload"])
                or _contains_eebus_contract_declaration(view["payload"])
                or _contains_structured_authority_declaration(
                    view["payload"]
                )
                or _contains_contract_descriptor_declaration(view["payload"])
                or _contains_eebus_authority(view["payload"])
            )
            for view in run["protected_views"]
        ):
            fail("gate.scope")
        inventory = next(
            view for view in run["protected_views"] if view["view_id"] == "mcp.tool.inventory"
        )
        eebus_contract = next(
            view for view in run["protected_views"] if view["view_id"] == "mcp.eebus.v1.contract"
        )
        tools = inventory["payload"]["data"]["tools"]
        contract_data = eebus_contract["payload"]["data"]
        eebus_tools = [
            tool
            for tool in tools
            if isinstance(tool, str) and tool.startswith("eebus.v1.")
        ]
        if (
            tools != APPROVED_M8_TOOL_INVENTORY
            or set(contract_data) != APPROVED_M8_EEBUS_CONTRACT_FIELDS
            or any(
                not isinstance(tool, str) or not TOOL_NAME_RE.fullmatch(tool)
                for tool in tools
            )
            or any(
                tool.casefold().startswith("eebus.")
                and not tool.startswith("eebus.v1.")
                for tool in tools
            )
            or eebus_tools != APPROVED_M8_EEBUS_TOOLS
            or contract_data["namespace"] != "eebus.v1"
            or not _exact_version_one(contract_data["version"])
            or contract_data["public_v2"] is not False
            or _contains_non_v1_eebus_surface(
                contract_data, reject_any_alias=True
            )
        ):
            fail("gate.scope")


def check_drift(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    baseline = evidence["runs"][0]
    baseline_views = {view["view_id"]: view for view in baseline["protected_views"]}
    rules = {rule["view_id"]: rule for rule in registry["view_rules"]}
    for run in evidence["runs"][1:-1]:
        for view in run["protected_views"]:
            original = baseline_views[view["view_id"]]
            original_bytes = canonical(
                normalized_payload(
                    original["payload"],
                    rules[view["view_id"]],
                    evidence["normalization"],
                )
            )
            compared_bytes = canonical(
                normalized_payload(
                    view["payload"],
                    rules[view["view_id"]],
                    evidence["normalization"],
                )
            )
            if (
                view["shape_hash"] != original["shape_hash"]
                or view["canonical_payload_hash"] != original["canonical_payload_hash"]
                or compared_bytes != original_bytes
            ):
                fail("drift.consumer")


def check_rollback(evidence: dict[str, Any], registry: dict[str, Any]) -> None:
    baseline = evidence["runs"][0]
    rollback = evidence["runs"][-1]
    baseline_hashes = [
        (view["view_id"], view["shape_hash"], view["canonical_payload_hash"])
        for view in baseline["protected_views"]
    ]
    rollback_hashes = [
        (view["view_id"], view["shape_hash"], view["canonical_payload_hash"])
        for view in rollback["protected_views"]
    ]
    rules = {rule["view_id"]: rule for rule in registry["view_rules"]}
    baseline_bytes = [
        canonical(
            normalized_payload(
                view["payload"], rules[view["view_id"]], evidence["normalization"]
            )
        )
        for view in baseline["protected_views"]
    ]
    rollback_bytes = [
        canonical(
            normalized_payload(
                view["payload"], rules[view["view_id"]], evidence["normalization"]
            )
        )
        for view in rollback["protected_views"]
    ]
    config = rollback["provenance"]["config"]["payload"]
    live = evidence["evidence_class"] == "CAPTURED_RUNTIME_EVIDENCE"
    expected_state = "EEBUS_CONNECTED_ROLLBACK" if live else "EEBUS_DISABLED_ROLLBACK"
    if (
        rollback["state"] != expected_state
        or config["eebus_runtime_enabled"] is not live
        or config["candidate_graph_enabled"]
        or rollback_hashes != baseline_hashes
        or rollback_bytes != baseline_bytes
    ):
        fail("rollback.drift")


def check_evidence_hash(evidence: dict[str, Any]) -> None:
    view = {key: value for key, value in evidence.items() if key not in {"evidence_id", "evidence_hash"}}
    expected = digest(EVIDENCE_DOMAIN, view)
    if evidence["evidence_hash"] != expected or evidence["evidence_id"] != "mrcv1:" + expected:
        fail("hash.evidence")


def verify(
    evidence: dict[str, Any],
    raw_size: int,
    registry: dict[str, Any],
    registry_raw: bytes,
    m7_paths: dict[str, pathlib.Path | None],
    *,
    require_private: bool = True,
    source_manifests: dict[str, bytes | None] | None = None,
    source_roots: dict[str, pathlib.Path | None] | None = None,
) -> dict[str, Any]:
    schema_check(evidence)
    check_limits(evidence, raw_size)
    check_registry(evidence, registry, registry_raw)
    graph, _, m7_inputs, source_graph = _verify_m7(
        evidence, registry, m7_paths, require_private=require_private
    )
    check_runtime(
        evidence,
        m7_inputs,
        source_manifests,
        source_roots,
        require_private=require_private,
    )
    check_config(evidence)
    check_auth_mask(evidence)
    check_clock(evidence)
    check_ordering(evidence, registry)
    check_states(evidence, graph)
    check_restart(evidence)
    check_view_coverage(evidence, registry)
    check_normalization(evidence, registry)
    check_payload_hashes(evidence, registry)
    check_anti_leak(evidence, graph, source_graph)
    check_public_redaction(evidence)
    check_authority(evidence)
    check_scope(evidence, registry)
    check_drift(evidence, registry)
    check_rollback(evidence, registry)
    check_evidence_hash(evidence)
    return evidence


def _view_hashes(run: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "view_id": view["view_id"],
            "shape_hash": view["shape_hash"],
            "canonical_payload_hash": view["canonical_payload_hash"],
        }
        for view in run["protected_views"]
    ]


def report(evidence: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    checks = registry["required_acceptance_checks"]
    result_by_state = {
        "EEBUS_DISABLED_CONFIRMED": "NO_DRIFT",
        "EEBUS_ENABLED_NO_SERVICES": "EXPECTED_NO_SERVICES_NO_DRIFT",
        "EEBUS_CONNECTED_CANDIDATE_ONLY": "CANDIDATE_CONFINED_NO_DRIFT",
        "EEBUS_CONFLICTED_WITHHELD": "CONFLICT_WITHHELD_NO_DRIFT",
        "EEBUS_DISABLED_ROLLBACK": "ROLLBACK_EXACT_BASELINE",
        "EEBUS_CONNECTED_RAW_WITHHELD": "RAW_WITHHELD_CONFINED_NO_DRIFT",
        "EEBUS_RESTART_PERSISTED": "RESTART_PERSISTED_NO_DRIFT",
        "EEBUS_CONNECTED_ROLLBACK": "GRAPH_EVIDENCE_DROPPED_NO_DRIFT",
    }
    baseline = evidence["runs"][0]
    fixture_id = (
        registry["fixture_ids"]["synthetic_positive_report"]
        if evidence["evidence_class"] == "SYNTHETIC_OFFLINE_FIXTURE"
        else evidence["fixture_id"] + registry["fixture_ids"]["live_report_suffix"]
    )
    value = {
        "contract": REPORT_CONTRACT,
        "schema_version": 1,
        "fixture_id": fixture_id,
        "evidence_class": evidence["evidence_class"],
        "export_tier": evidence["export_tier"],
        "report_id": "mrcrv1:sha256:" + "0" * 64,
        "report_hash": "sha256:" + "0" * 64,
        "evidence_id": evidence["evidence_id"],
        "evidence_hash": evidence["evidence_hash"],
        "gate": registry["gate"],
        "verdict": "PASS",
        "m7_binding": {
            key: evidence["m7_binding"][key]
            for key in (
                "source_commit",
                "docs_source_commit",
                "graph_id",
                "graph_hash",
                "replay_id",
                "replay_hash",
            )
        }
        | {
            "live_status_projection_id": (
                evidence["m7_live_status"]["projection_id"]
                if evidence["m7_live_status"] is not None
                else None
            ),
            "live_status_projection_hash": (
                evidence["m7_live_status"]["projection_hash"]
                if evidence["m7_live_status"] is not None
                else None
            ),
        },
        "baseline": {
            "run_id": baseline["run_id"],
            "state": baseline["state"],
            "source_commit": baseline["provenance"]["runtime"]["source_commit"],
            "artifact_digest": baseline["provenance"]["runtime"]["artifact_digest"],
            "view_hashes": _view_hashes(baseline),
        },
        "scenarios": [
            {
                "run_id": run["run_id"],
                "state": run["state"],
                "result": result_by_state[run["state"]],
                "checks": checks,
                "view_hashes": _view_hashes(run),
            }
            for run in evidence["runs"][1:]
        ],
        "acceptance_matrix": [
            {"state": run["state"], "required_checks": checks, "passed": True}
            for run in evidence["runs"]
        ],
        "rollback": {
            "run_id": evidence["runs"][-1]["run_id"],
            "runtime_enabled": evidence["runs"][-1]["state_evidence"]["eebus_runtime_enabled"],
            "candidate_graph_disabled": True,
            "exact_baseline_restored": True,
        },
    }
    view = {key: item for key, item in value.items() if key not in {"report_id", "report_hash"}}
    report_hash = digest(REPORT_DOMAIN, view)
    value["report_id"] = "mrcrv1:" + report_hash
    value["report_hash"] = report_hash
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify-public", "verify", "report"))
    parser.add_argument("--evidence", type=pathlib.Path, required=True)
    parser.add_argument("--registry", type=pathlib.Path, required=True)
    parser.add_argument("--m7-graph", type=pathlib.Path)
    parser.add_argument("--m7-replay", type=pathlib.Path)
    parser.add_argument("--m7-registry", type=pathlib.Path, required=True)
    parser.add_argument("--m7-source-bundle", type=pathlib.Path)
    parser.add_argument("--m7-source-replay", type=pathlib.Path)
    parser.add_argument("--m7-terminal-graph", type=pathlib.Path)
    parser.add_argument("--m7-terminal-replay", type=pathlib.Path)
    parser.add_argument("--m7-terminal-source-bundle", type=pathlib.Path)
    parser.add_argument("--m7-terminal-source-replay", type=pathlib.Path)
    parser.add_argument(
        "--m7-live-status",
        type=pathlib.Path,
        default=(
            pathlib.Path(__file__).resolve().parents[1]
            / "docs/platform/fixtures/candidate-fact-graph/v1/positive/live-public-status.json"
        ),
    )
    parser.add_argument("--before-source-manifest", type=pathlib.Path)
    parser.add_argument("--after-source-manifest", type=pathlib.Path)
    parser.add_argument("--before-source-root", type=pathlib.Path)
    parser.add_argument("--after-source-root", type=pathlib.Path)
    args = parser.parse_args()
    try:
        evidence, evidence_raw = load_json(args.evidence, "json.syntax", bounded=True)
        schema_check(evidence)
        check_limits(evidence, len(evidence_raw))
        registry, registry_raw = load_json(args.registry, "registry.binding")
        m7_paths = {
            "graph": args.m7_graph,
            "replay": args.m7_replay,
            "registry": args.m7_registry,
            "source_bundle": args.m7_source_bundle,
            "source_replay": args.m7_source_replay,
            "terminal_graph": args.m7_terminal_graph,
            "terminal_replay": args.m7_terminal_replay,
            "terminal_source_bundle": args.m7_terminal_source_bundle,
            "terminal_source_replay": args.m7_terminal_source_replay,
            "status": args.m7_live_status,
        }
        verify(
            evidence,
            len(evidence_raw),
            registry,
            registry_raw,
            m7_paths,
            require_private=args.command != "verify-public",
            source_manifests={
                "before": _read_bounded_regular_file(
                    args.before_source_manifest,
                    MAX_SOURCE_INPUT_BYTES,
                    "provenance.source_capture",
                )
                if args.before_source_manifest is not None else None,
                "after": _read_bounded_regular_file(
                    args.after_source_manifest,
                    MAX_SOURCE_INPUT_BYTES,
                    "provenance.source_capture",
                )
                if args.after_source_manifest is not None else None,
            },
            source_roots={
                "before": args.before_source_root,
                "after": args.after_source_root,
            },
        )
        if args.command == "verify-public":
            sys.stdout.write("public-only-ok\n")
        elif args.command == "verify":
            sys.stdout.write("ok\n")
        else:
            sys.stdout.write(canonical(report(evidence, registry)).decode("utf-8") + "\n")
        return 0
    except Failure as error:
        sys.stdout.write(str(error) + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
