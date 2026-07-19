#!/usr/bin/env python3
"""Offline verifier and deterministic replayer for the M7 candidate fact graph."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any


SCRIPT_ROOT = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))
import validate_synchronized_evidence as synchronized


GRAPH_CONTRACT = "helianthus.platform.draft-candidate-fact-graph.v1"
REGISTRY_CONTRACT = "helianthus.platform.draft-candidate-fact-registry.v1"
SOURCE_CONTRACT = "helianthus.platform.synchronized-evidence-bundle.v1"
FACT_DOMAIN = b"HELIANTHUS:DRAFT-CANDIDATE-FACT:V1"
GRAPH_DOMAIN = b"HELIANTHUS:DRAFT-CANDIDATE-FACT-GRAPH:V1"
REPLAY_DOMAIN = b"HELIANTHUS:DRAFT-CANDIDATE-FACT-REPLAY:V1"
SOURCE_REPLAY_DOMAIN = b"HELIANTHUS:SYNCHRONIZED-EVIDENCE-REPLAY:V1"
SAFE_INTEGER = 9_007_199_254_740_991
HARD_LIMITS = {
    "max_graph_bytes": 1_048_576,
    "max_depth": 32,
    "max_facts": 64,
    "max_evidence_refs_per_fact": 16,
    "max_samples_per_comparator": 1024,
    "max_string_bytes": 4096,
    "max_path_segments": 32,
    "max_total_members": 16_384,
    "max_total_list_items": 8192,
}
DECIMAL_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
GRAPH_ID_RE = re.compile(r"^dcfgv1:sha256:[0-9a-f]{64}$")
BUNDLE_ID_RE = re.compile(r"^sebv1:sha256:[0-9a-f]{64}$")
CANDIDATE_ID_RE = re.compile(r"^m7-candidate-[0-9]{4}$")
PATH_RE = re.compile(r"^/[a-z0-9_]+(?:/[a-z0-9_]+)*$")
PUBLIC_EVIDENCE_RE = re.compile(r"^public-evidence:sha256:[0-9a-f]{64}$")

ROOT_KEYS = {
    "contract",
    "schema_version",
    "graph_id",
    "graph_hash",
    "registry",
    "source_bundle",
    "visibility",
    "limits",
    "comparator_drafts",
    "facts",
}
PROVENANCE_KEYS = {
    "source_bundle_id",
    "native_evidence_refs",
    "ebus_source_id",
    "ebus_artifact_id",
    "ebus",
    "eebus_source_id",
    "eebus_artifact_id",
    "eebus_service",
    "eebus",
    "cloud",
}
EVIDENCE_REF_KEYS = {
    "kind",
    "digest_algorithm",
    "digest",
    "repository",
    "commit",
    "path",
}
OBSERVATION_BINDING_KEYS = {
    "source_kind",
    "source_id",
    "artifact_id",
    "evidence_ref",
    "observed_offset_ns",
    "value_pointer",
    "unit_pointer",
    "native_decimal",
    "native_unit",
}
VALIDATION_PRECEDENCE = [
    "json.syntax",
    "schema.graph",
    "limits.exceeded",
    "registry.binding",
    "provenance.binding",
    "identity.native",
    "ordering.invalid",
    "state.terminal",
    "comparator.invalid",
    "anti_leak.consumer",
    "hash.fact",
    "hash.graph",
]


class Failure(Exception):
    pass


def fail(category: str) -> None:
    raise Failure(category)


def _input_category(input_kind: str) -> str:
    return {
        "graph": "json.syntax",
        "registry": "registry.binding",
        "source": "provenance.binding",
    }[input_kind]


def _bounded_preflight(raw: bytes, limits: dict[str, int]) -> None:
    """Bound allocation drivers before Python's recursive decoder is entered."""
    if len(raw) > limits["max_graph_bytes"]:
        fail("limits.exceeded")
    depth = 0
    members = 0
    list_items = 0
    in_string = False
    escaped = False
    string_bytes = 0
    stack: list[dict[str, Any]] = []

    def mark_list_value() -> None:
        nonlocal list_items
        if stack and stack[-1]["kind"] == "list" and stack[-1]["expecting"]:
            stack[-1]["expecting"] = False
            stack[-1]["items"] += 1
            list_items += 1
            if (
                stack[-1]["items"] > limits["max_samples_per_comparator"]
                or list_items > limits["max_total_list_items"]
            ):
                fail("limits.exceeded")

    index = 0
    while index < len(raw):
        byte = raw[index]
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
            if string_bytes > limits["max_string_bytes"]:
                fail("limits.exceeded")
            index += 1
            continue
        if byte in b" \t\r\n":
            index += 1
            continue
        if byte == 0x22:
            mark_list_value()
            in_string = True
            string_bytes = 0
        elif byte in (0x7B, 0x5B):
            mark_list_value()
            depth += 1
            if depth > limits["max_depth"]:
                fail("limits.exceeded")
            stack.append(
                {
                    "kind": "list" if byte == 0x5B else "object",
                    "expecting": byte == 0x5B,
                    "items": 0,
                }
            )
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth < 0 or not stack:
                return
            stack.pop()
        elif byte == 0x3A:
            members += 1
            if members > limits["max_total_members"]:
                fail("limits.exceeded")
        elif byte == 0x2C:
            if stack and stack[-1]["kind"] == "list":
                stack[-1]["expecting"] = True
        else:
            mark_list_value()
        index += 1


def _parse_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        fail("json.syntax")
    if abs(parsed) > SAFE_INTEGER:
        fail("json.syntax")
    return parsed


def load_json(path: pathlib.Path, *, input_kind: str = "graph") -> tuple[Any, bytes]:
    category = _input_category(input_kind)
    try:
        raw = path.read_bytes()
    except OSError:
        fail(category)
    try:
        if input_kind in {"graph", "registry"}:
            _bounded_preflight(raw, HARD_LIMITS)
        else:
            synchronized.preflight_json_bytes(raw)
    except (Failure, synchronized.Failure):
        if input_kind == "graph":
            raise
        fail(category)
    if re.search(rb"(?<![0-9A-Za-z_])-0(?:[^0-9.]|$)", raw):
        fail(category)

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                fail(category)
            result[key] = value
        return result

    def reject_non_integer(_: str) -> None:
        fail(category)

    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_int=_parse_integer if input_kind == "graph" else int,
            parse_float=reject_non_integer if input_kind == "graph" else float,
            parse_constant=reject_non_integer,
        )
    except Failure:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        fail(category)
    return value, raw


def exact_keys(value: Any, expected: set[str], category: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        fail(category)


def check_portable(value: Any, limits: dict[str, int] = HARD_LIMITS) -> None:
    members = 0
    list_items = 0
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        if current is None or isinstance(current, bool):
            continue
        if isinstance(current, int):
            if abs(current) > SAFE_INTEGER:
                fail("json.syntax")
            continue
        if isinstance(current, float):
            fail("json.syntax")
        if isinstance(current, str):
            if len(current.encode("utf-8")) > limits["max_string_bytes"] or "\x00" in current:
                fail("limits.exceeded")
            continue
        if isinstance(current, list):
            if depth > limits["max_depth"]:
                fail("limits.exceeded")
            if len(current) > limits["max_samples_per_comparator"]:
                fail("limits.exceeded")
            list_items += len(current)
            if list_items > limits["max_total_list_items"]:
                fail("limits.exceeded")
            stack.extend((item, depth + 1) for item in reversed(current))
            continue
        if isinstance(current, dict):
            if depth > limits["max_depth"]:
                fail("limits.exceeded")
            members += len(current)
            if members > limits["max_total_members"]:
                fail("limits.exceeded")
            for key, item in reversed(list(current.items())):
                if not isinstance(key, str):
                    fail("json.syntax")
                stack.append((item, depth + 1))
                stack.append((key, depth + 1))
            continue
        fail("json.syntax")


def canonical(value: Any) -> bytes:
    check_portable(value)
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    if len(encoded) > HARD_LIMITS["max_graph_bytes"]:
        fail("limits.exceeded")
    return encoded


def digest(domain: bytes, value: Any) -> str:
    return hashlib.sha256(domain + b"\0" + canonical(value)).hexdigest()


def fact_hexdigest(fact: dict[str, Any]) -> str:
    return digest(
        FACT_DOMAIN,
        {key: value for key, value in fact.items() if key != "fact_hash"},
    )


def graph_hexdigest(graph: dict[str, Any]) -> str:
    return digest(
        GRAPH_DOMAIN,
        {
            key: value
            for key, value in graph.items()
            if key not in {"graph_id", "graph_hash"}
        },
    )


def source_replay_hexdigest(value: Any) -> str:
    return hashlib.sha256(
        SOURCE_REPLAY_DOMAIN + b"\0" + synchronized.canonical(value)
    ).hexdigest()


def _is_schema_type(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def _schema_validate(value: Any, rule: dict[str, Any], root: dict[str, Any]) -> bool:
    if "$ref" in rule:
        prefix = "#/$defs/"
        reference = rule["$ref"]
        if not isinstance(reference, str) or not reference.startswith(prefix):
            return False
        target = root.get("$defs", {}).get(reference.removeprefix(prefix))
        return isinstance(target, dict) and _schema_validate(value, target, root)
    if "oneOf" in rule:
        return sum(_schema_validate(value, item, root) for item in rule["oneOf"]) == 1
    if "anyOf" in rule and not any(
        _schema_validate(value, item, root) for item in rule["anyOf"]
    ):
        return False
    if "allOf" in rule and not all(
        _schema_validate(value, item, root) for item in rule["allOf"]
    ):
        return False
    expected_type = rule.get("type")
    if expected_type is not None:
        if isinstance(expected_type, list):
            if not any(_is_schema_type(value, item) for item in expected_type):
                return False
        elif not _is_schema_type(value, expected_type):
            return False
    if "const" in rule and value != rule["const"]:
        return False
    if "enum" in rule and value not in rule["enum"]:
        return False
    if isinstance(value, str):
        if len(value) < rule.get("minLength", 0) or len(value) > rule.get(
            "maxLength", SAFE_INTEGER
        ):
            return False
        if "pattern" in rule and re.fullmatch(rule["pattern"], value) is None:
            return False
    if isinstance(value, int) and not isinstance(value, bool):
        if value < rule.get("minimum", -SAFE_INTEGER) or value > rule.get(
            "maximum", SAFE_INTEGER
        ):
            return False
    if isinstance(value, list):
        if len(value) < rule.get("minItems", 0) or len(value) > rule.get(
            "maxItems", SAFE_INTEGER
        ):
            return False
        if rule.get("uniqueItems"):
            encoded = [
                json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                for item in value
            ]
            if len(encoded) != len(set(encoded)):
                return False
        item_rule = rule.get("items")
        if item_rule is not None and not all(
            _schema_validate(item, item_rule, root) for item in value
        ):
            return False
    if isinstance(value, dict):
        required = rule.get("required", [])
        if not isinstance(required, list) or not set(required) <= set(value):
            return False
        properties = rule.get("properties", {})
        if rule.get("additionalProperties") is False and not set(value) <= set(properties):
            return False
        for key, item in value.items():
            if key in properties and not _schema_validate(item, properties[key], root):
                return False
    return True


def schema_check(graph: Any) -> None:
    schema_path = (
        SCRIPT_ROOT.parent
        / "docs/platform/schemas/draft-candidate-fact-graph-v1.schema.json"
    )
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        fail("schema.graph")
    if not _schema_validate(graph, schema, schema):
        fail("schema.graph")


def check_limits(graph: dict[str, Any], raw_size: int) -> None:
    if graph["limits"] != HARD_LIMITS or raw_size > HARD_LIMITS["max_graph_bytes"]:
        fail("limits.exceeded")
    check_portable(graph, HARD_LIMITS)
    if len(graph["facts"]) > HARD_LIMITS["max_facts"]:
        fail("limits.exceeded")
    for fact in graph["facts"]:
        if (
            len(fact["provenance"]["native_evidence_refs"])
            > HARD_LIMITS["max_evidence_refs_per_fact"]
            or len(fact["comparator"]["samples"])
            > HARD_LIMITS["max_samples_per_comparator"]
            or len([part for part in fact["proposed_path"].split("/") if part])
            > HARD_LIMITS["max_path_segments"]
        ):
            fail("limits.exceeded")


def check_registry_binding(
    graph: dict[str, Any], registry: Any, registry_raw: bytes
) -> None:
    binding = graph["registry"]
    expected_digest = "sha256:" + hashlib.sha256(registry_raw).hexdigest()
    if binding != {
        "contract": REGISTRY_CONTRACT,
        "version": 1,
        "digest": expected_digest,
    }:
        fail("registry.binding")
    expected_top = {
        "contract",
        "version",
        "candidate_contract",
        "source_contract",
        "statuses",
        "terminal_negative_states",
        "comparators",
        "candidate_channel",
        "forbidden_surfaces",
        "validation_precedence",
        "limits",
    }
    if not isinstance(registry, dict) or set(registry) != expected_top:
        fail("registry.binding")
    if (
        registry["contract"] != REGISTRY_CONTRACT
        or registry["version"] != 1
        or registry["candidate_contract"]
        != {
            "contract": GRAPH_CONTRACT,
            "schema_version": 1,
            "schema_path": "docs/platform/schemas/draft-candidate-fact-graph-v1.schema.json",
            "replay_contract": "helianthus.platform.draft-candidate-fact-replay.v1",
            "replay_schema_path": "docs/platform/schemas/draft-candidate-fact-replay-v1.schema.json",
        }
        or registry["statuses"]
        != ["RAW_ONLY", "CANDIDATE", "CONFLICTED", "WITHHELD"]
        or registry["terminal_negative_states"]
        != ["NO_SIGNAL", "CLOUD_ONLY", "CONFLICT", "NOT_TESTED"]
        or registry["candidate_channel"] != "CANDIDATE_DEBUG_REPLAY"
        or registry["validation_precedence"] != VALIDATION_PRECEDENCE
        or registry["limits"] != HARD_LIMITS
    ):
        fail("registry.binding")
    comparators = registry["comparators"]
    if (
        not isinstance(comparators, list)
        or len(comparators) != 1
        or comparators[0]
        != {
            "draft_id": "NUMERIC_WINDOW_V1_DRAFT",
            "type": "NUMERIC_WINDOW",
            "required_parameters": [
                "window",
                "tolerance",
                "unit_conversion",
                "rounding",
                "minimum_samples",
                "maximum_missing_samples",
                "stale_cutoff_ns",
                "conflict_threshold",
            ],
            "outcomes": [
                "MATCH",
                "MISMATCH",
                "CONFLICT",
                "INDETERMINATE",
                "NOT_EVALUATED",
            ],
        }
    ):
        fail("registry.binding")
    source_contract = registry["source_contract"]
    if (
        not isinstance(source_contract, dict)
        or set(source_contract)
        != {
            "contract",
            "schema_version",
            "owner_repository",
            "owner_commit",
            "schema_path",
            "schema_sha256",
            "source_registry_path",
            "source_registry_sha256",
            "replay_digest_algorithm",
            "replay_digest_domain",
        }
        or source_contract.get("contract") != SOURCE_CONTRACT
        or source_contract.get("schema_version") != 1
        or not _ascii_token(source_contract.get("owner_repository"))
        or re.fullmatch(r"[0-9a-f]{40}", source_contract.get("owner_commit", ""))
        is None
        or not _ascii_token(source_contract.get("schema_path"), maximum=512)
        or re.fullmatch(r"[0-9a-f]{64}", source_contract.get("schema_sha256", ""))
        is None
        or source_contract.get("replay_digest_algorithm") != "SHA256_JCS_DOMAIN_V1"
        or source_contract.get("replay_digest_domain")
        != SOURCE_REPLAY_DOMAIN.decode("ascii")
        or not isinstance(source_contract.get("source_registry_path"), str)
        or not re.fullmatch(
            r"[0-9a-f]{64}", source_contract.get("source_registry_sha256", "")
        )
    ):
        fail("registry.binding")
    forbidden = registry["forbidden_surfaces"]
    if forbidden != [
        "STABLE_DOC_NAVIGATION",
        "STABLE_DOC_SEARCH",
        "STABLE_DOC_SITEMAP",
        "VERSIONED_DOC_BUNDLE",
        "RELEASE_DOC_BUNDLE",
        "EBUS_V1_MCP",
        "GRAPHQL",
        "PORTAL",
        "HOME_ASSISTANT",
        "COMMAND_ROUTING",
        "PROMOTED_SEMANTICS",
        "STABLE_SEMANTIC_REGISTRY",
    ]:
        fail("registry.binding")


def validate_evidence_ref(ref: Any) -> None:
    exact_keys(ref, EVIDENCE_REF_KEYS, "provenance.binding")
    if not isinstance(ref["digest"], str) or not DIGEST_RE.fullmatch(ref["digest"]):
        fail("provenance.binding")
    if ref["kind"] == "CONTENT":
        if (
            ref["digest_algorithm"] != "SHA256_CONTENT_BYTES"
            or ref["repository"] is not None
            or ref["commit"] is not None
            or ref["path"] is not None
        ):
            fail("provenance.binding")
    elif ref["kind"] == "GIT_BLOB":
        if (
            ref["digest_algorithm"] != "SHA256_GIT_BLOB_V1"
            or not _ascii_token(ref["repository"])
            or not isinstance(ref["commit"], str)
            or re.fullmatch(r"[0-9a-f]{40}", ref["commit"]) is None
            or not _ascii_token(ref["path"], maximum=512)
        ):
            fail("provenance.binding")
    else:
        fail("provenance.binding")


def ref_sort_key(ref: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(
        (0, "") if ref[field] is None else (1, ref[field])
        for field in ("kind", "digest_algorithm", "digest", "repository", "commit", "path")
    )


def _artifact_index(source_bundle: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (artifact["source_id"], artifact["artifact_id"]): artifact
        for artifact in source_bundle["artifacts"]
    }


def _check_sample_provenance(
    fact: dict[str, Any], artifacts: dict[tuple[str, str], dict[str, Any]]
) -> None:
    provenance = fact["provenance"]
    fact_refs = {canonical(ref) for ref in provenance["native_evidence_refs"]}
    for sample in fact["comparator"]["samples"]:
        for side_name, expected_kind, source_field, artifact_field in (
            ("left", "EBUS", "ebus_source_id", "ebus_artifact_id"),
            ("right", "EEBUS", "eebus_source_id", "eebus_artifact_id"),
        ):
            side = sample[side_name]
            expected_pair = (
                provenance[source_field],
                provenance[artifact_field],
            )
            actual_pair = (side["source_id"], side["artifact_id"])
            artifact = artifacts.get(actual_pair)
            encoded_ref = canonical(side["evidence_ref"])
            if (
                side["source_kind"] != expected_kind
                or None in expected_pair
                or actual_pair != expected_pair
                or artifact is None
                or artifact["source_kind"] != expected_kind
                or encoded_ref not in fact_refs
                or not any(
                    encoded_ref == canonical(ref) for ref in artifact["evidence_refs"]
                )
            ):
                fail("provenance.binding")


def check_provenance(
    graph: dict[str, Any],
    registry: dict[str, Any],
    source_bundle: dict[str, Any],
    source_replay: dict[str, Any],
) -> None:
    bundle = graph["source_bundle"]
    expected_source_binding = {
        "contract": source_bundle["contract"],
        "schema_version": source_bundle["schema_version"],
        "bundle_id": source_bundle["bundle_id"],
        "bundle_hash": source_bundle["bundle_hash"],
        "replay_hash": "sha256:" + source_replay_hexdigest(source_replay),
        "evidence_refs": source_bundle["evidence_refs"],
    }
    if (
        bundle != expected_source_binding
        or bundle["contract"] != registry["source_contract"]["contract"]
        or not BUNDLE_ID_RE.fullmatch(bundle["bundle_id"])
        or bundle["bundle_id"].removeprefix("sebv1:") != bundle["bundle_hash"]
    ):
        fail("provenance.binding")
    root_refs: set[bytes] = set()
    for ref in bundle["evidence_refs"]:
        validate_evidence_ref(ref)
        encoded = canonical(ref)
        if encoded in root_refs:
            fail("provenance.binding")
        root_refs.add(encoded)
    sources = {source["source_id"]: source for source in source_bundle["sources"]}
    artifacts = _artifact_index(source_bundle)
    for fact in graph["facts"]:
        provenance = fact["provenance"]
        exact_keys(provenance, PROVENANCE_KEYS, "provenance.binding")
        if provenance["source_bundle_id"] != bundle["bundle_id"]:
            fail("provenance.binding")
        refs = provenance["native_evidence_refs"]
        if not isinstance(refs, list) or not refs:
            fail("provenance.binding")
        seen: set[bytes] = set()
        for ref in refs:
            validate_evidence_ref(ref)
            encoded = canonical(ref)
            if encoded not in root_refs or encoded in seen:
                fail("provenance.binding")
            seen.add(encoded)
        referenced: list[dict[str, Any]] = []
        for source_field, artifact_field, expected_kind in (
            ("ebus_source_id", "ebus_artifact_id", "EBUS"),
            ("eebus_source_id", "eebus_artifact_id", "EEBUS"),
        ):
            source_id = provenance[source_field]
            artifact_id = provenance[artifact_field]
            if source_id is None and artifact_id is None:
                continue
            source = sources.get(source_id)
            artifact = artifacts.get((source_id, artifact_id))
            if (
                source_id is None
                or artifact_id is None
                or source is None
                or artifact is None
                or source["source_kind"] != expected_kind
                or artifact["source_kind"] != expected_kind
                or artifact_id not in source["artifact_ids"]
            ):
                fail("provenance.binding")
            referenced.append(artifact)
        cloud = provenance["cloud"]
        if cloud is not None:
            source = sources.get(cloud["source_id"])
            artifact = artifacts.get((cloud["source_id"], cloud["artifact_id"]))
            if (
                source is None
                or artifact is None
                or source["source_kind"] != "CLOUD_APP"
                or artifact["source_kind"] != "CLOUD_APP"
                or cloud["artifact_id"] not in source["artifact_ids"]
                or not PUBLIC_EVIDENCE_RE.fullmatch(cloud["evidence_id"])
                or cloud["evidence_id"]
                not in {
                    "public-evidence:" + ref["digest"]
                    for ref in artifact["evidence_refs"]
                }
            ):
                fail("provenance.binding")
            referenced.append(artifact)
        for artifact in referenced:
            if any(canonical(ref) not in seen for ref in artifact["evidence_refs"]):
                fail("provenance.binding")
        _check_sample_provenance(fact, artifacts)
        if (
            fact["comparator"]["samples"]
            or fact["status"] in {"CANDIDATE", "CONFLICTED"}
            or fact["terminal_negative_state"] == "CONFLICT"
        ):
            if (
                provenance["ebus"] is None
                or provenance["eebus"] is None
                or provenance["ebus_source_id"] is None
                or provenance["eebus_source_id"] is None
                or not fact["comparator"]["samples"]
            ):
                fail("provenance.binding")


def _ascii_token(value: Any, *, maximum: int = 256) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= maximum
        and value.isascii()
        and all(0x20 <= ord(char) <= 0x7E for char in value)
    )


def _byte_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 255


def _word_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 65535


def validate_ebus_identity(identity: Any) -> None:
    if not isinstance(identity, dict):
        fail("identity.native")
    family = identity.get("family")
    common = all(
        _ascii_token(identity.get(field))
        for field in ("target_pseudonym", "unit_scale_source")
    )
    if family == "B509":
        expected = {
            "family",
            "target_pseudonym",
            "target_address",
            "target_product",
            "register_family",
            "register_id",
            "unit_scale_source",
            "evidence_role",
        }
        valid = (
            set(identity) == expected
            and common
            and _byte_int(identity["target_address"])
            and _ascii_token(identity["target_product"])
            and _ascii_token(identity["register_family"])
            and _word_int(identity["register_id"])
            and identity["evidence_role"] in {"AUTHORITATIVE", "MIRROR", "FALLBACK"}
        )
    elif family == "B524":
        expected = {
            "family",
            "target_pseudonym",
            "opcode",
            "GG",
            "II",
            "RR",
            "target_address",
            "source_address",
            "group_meaning",
            "instance_gate",
            "register_category",
            "unit_scale_source",
        }
        valid = (
            set(identity) == expected
            and common
            and all(
                _byte_int(identity[field])
                for field in ("opcode", "GG", "II", "target_address", "source_address")
            )
            and _word_int(identity["RR"])
            and _ascii_token(identity["group_meaning"])
            and _ascii_token(identity["instance_gate"])
            and identity["register_category"] in {"STATE", "CONFIG", "PARAMS"}
        )
    elif family == "B555":
        expected = {
            "family",
            "target_pseudonym",
            "device_family",
            "schedule_program",
            "slot_index",
            "day_of_week",
            "time_identity",
            "operation_mode_context",
            "unit_scale_source",
        }
        valid = (
            set(identity) == expected
            and common
            and _ascii_token(identity["device_family"])
            and _ascii_token(identity["schedule_program"])
            and _byte_int(identity["slot_index"])
            and identity["day_of_week"]
            in {
                "MONDAY",
                "TUESDAY",
                "WEDNESDAY",
                "THURSDAY",
                "FRIDAY",
                "SATURDAY",
                "SUNDAY",
            }
            and isinstance(identity["time_identity"], str)
            and re.fullmatch(
                r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]",
                identity["time_identity"],
            )
            is not None
            and _ascii_token(identity["operation_mode_context"])
        )
    else:
        valid = False
    if not valid:
        fail("identity.native")


def validate_eebus_path(value: Any) -> None:
    expected = {"service", "entity", "feature", "feature_path"}
    if not isinstance(value, dict) or set(value) != expected:
        fail("identity.native")
    if not all(_ascii_token(value[field]) for field in ("service", "entity", "feature")):
        fail("identity.native")
    path = value["feature_path"]
    if not isinstance(path, list) or not 3 <= len(path) <= HARD_LIMITS["max_path_segments"]:
        fail("identity.native")
    for segment in path:
        if (
            not isinstance(segment, dict)
            or set(segment) != {"kind", "selector"}
            or segment["kind"] not in {"SERVICE", "ENTITY", "FEATURE", "FIELD"}
            or not _ascii_token(segment["selector"])
        ):
            fail("identity.native")
    if (
        [segment["kind"] for segment in path[:3]]
        != ["SERVICE", "ENTITY", "FEATURE"]
        or any(segment["kind"] != "FIELD" for segment in path[3:])
        or [path[0]["selector"], path[1]["selector"], path[2]["selector"]]
        != [value["service"], value["entity"], value["feature"]]
    ):
        fail("identity.native")


def check_identities(graph: dict[str, Any], source_bundle: dict[str, Any]) -> None:
    artifacts = _artifact_index(source_bundle)
    for fact in graph["facts"]:
        provenance = fact["provenance"]
        if provenance["ebus"] is None:
            if provenance["ebus_source_id"] is not None or provenance["ebus_artifact_id"] is not None:
                fail("identity.native")
        else:
            validate_ebus_identity(provenance["ebus"])
            artifact = artifacts[(provenance["ebus_source_id"], provenance["ebus_artifact_id"])]
            if provenance["ebus"] != artifact["ebus_identity"]:
                fail("identity.native")
        eebus_pair = (provenance["eebus_source_id"], provenance["eebus_artifact_id"])
        if eebus_pair == (None, None):
            if provenance["eebus_service"] is not None or provenance["eebus"] is not None:
                fail("identity.native")
        else:
            if not _ascii_token(provenance["eebus_service"]):
                fail("identity.native")
            artifact = artifacts[eebus_pair]
            services = artifact["normalized_evidence"]["data"]["services"]
            service_ids = {service["id"]["digest"] for service in services}
            if provenance["eebus_service"] not in service_ids:
                fail("identity.native")
            if provenance["eebus"] is not None:
                validate_eebus_path(provenance["eebus"])
                feature_paths = artifact["normalized_evidence"]["data"].get("feature_paths")
                if (
                    provenance["eebus"]["service"] != provenance["eebus_service"]
                    or not isinstance(feature_paths, list)
                    or provenance["eebus"] not in feature_paths
                ):
                    fail("identity.native")


def check_ordering(graph: dict[str, Any]) -> None:
    refs = graph["source_bundle"]["evidence_refs"]
    if refs != sorted(refs, key=ref_sort_key):
        fail("ordering.invalid")
    facts = graph["facts"]
    if facts != sorted(
        facts,
        key=lambda fact: (
            fact["proposed_path"].encode("utf-8"),
            fact["candidate_id"].encode("utf-8"),
        ),
    ):
        fail("ordering.invalid")
    ids: set[str] = set()
    paths: set[str] = set()
    for fact in facts:
        if fact["candidate_id"] in ids or fact["proposed_path"] in paths:
            fail("ordering.invalid")
        ids.add(fact["candidate_id"])
        paths.add(fact["proposed_path"])
        refs = fact["provenance"]["native_evidence_refs"]
        if refs != sorted(refs, key=ref_sort_key):
            fail("ordering.invalid")
        samples = fact["comparator"]["samples"]
        encoded = [canonical(sample) for sample in samples]
        if len(encoded) != len(set(encoded)):
            fail("ordering.invalid")
        if samples != sorted(samples, key=lambda sample: (sample["offset_ns"], canonical(sample))):
            fail("ordering.invalid")
        required = fact["retest_trigger"]["required_source_kinds"]
        if required != sorted(set(required), key=lambda value: value.encode("utf-8")):
            fail("ordering.invalid")


def check_states(graph: dict[str, Any], registry: dict[str, Any]) -> None:
    statuses = set(registry["statuses"])
    terminals = set(registry["terminal_negative_states"])
    for fact in graph["facts"]:
        if (
            not CANDIDATE_ID_RE.fullmatch(fact["candidate_id"])
            or not PATH_RE.fullmatch(fact["proposed_path"])
            or fact["status"] not in statuses
            or (
                fact["terminal_negative_state"] is not None
                and fact["terminal_negative_state"] not in terminals
            )
            or fact["debug_only"] is not True
        ):
            fail("state.terminal")
        status = fact["status"]
        terminal = fact["terminal_negative_state"]
        samples = fact["comparator"]["samples"]
        outcome = fact["comparator"]["outcome"]
        provenance = fact["provenance"]
        native_kinds = {
            kind
            for kind, source_id in (
                ("EBUS", provenance["ebus_source_id"]),
                ("EEBUS", provenance["eebus_source_id"]),
            )
            if source_id is not None
        }
        cloud_only = provenance["cloud"] is not None and not native_kinds
        if cloud_only and (status != "WITHHELD" or terminal != "CLOUD_ONLY"):
            fail("state.terminal")
        if status == "RAW_ONLY":
            if (
                terminal is not None
                or fact["draft_value"] is not None
                or fact["draft_unit"] is not None
                or samples
                or outcome != "NOT_EVALUATED"
            ):
                fail("state.terminal")
        elif status == "CANDIDATE":
            if (
                terminal is not None
                or fact["draft_value"] is None
                or fact["draft_unit"] is None
                or not samples
                or outcome != "MATCH"
                or native_kinds != {"EBUS", "EEBUS"}
            ):
                fail("state.terminal")
        elif status == "CONFLICTED":
            if (
                terminal is not None
                or fact["draft_value"] is not None
                or fact["draft_unit"] is not None
                or not samples
                or outcome not in {"MISMATCH", "CONFLICT"}
                or native_kinds != {"EBUS", "EEBUS"}
            ):
                fail("state.terminal")
        elif status == "WITHHELD":
            if terminal is None or fact["draft_value"] is not None or fact["draft_unit"] is not None:
                fail("state.terminal")
            if terminal in {"CLOUD_ONLY", "NO_SIGNAL"} and (
                samples or outcome != "NOT_EVALUATED"
            ):
                fail("state.terminal")
            if terminal == "CLOUD_ONLY" and not cloud_only:
                fail("state.terminal")
            if terminal == "NO_SIGNAL" and not native_kinds:
                fail("state.terminal")
            if terminal == "NOT_TESTED" and not (
                (not samples and outcome == "NOT_EVALUATED")
                or (
                    samples
                    and outcome == "INDETERMINATE"
                    and native_kinds == {"EBUS", "EEBUS"}
                )
            ):
                fail("state.terminal")
            if terminal == "CONFLICT" and (
                outcome != "CONFLICT" or native_kinds != {"EBUS", "EEBUS"} or not samples
            ):
                fail("state.terminal")


def _decimal(value: Any, *, nonnegative: bool = False) -> Decimal:
    if not isinstance(value, str) or len(value) > 64 or not DECIMAL_RE.fullmatch(value):
        fail("comparator.invalid")
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        fail("comparator.invalid")
    if (parsed == 0 and value.startswith("-")) or (nonnegative and parsed < 0):
        fail("comparator.invalid")
    return parsed


def _pointer_get(value: Any, pointer: str) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/") or len(pointer) > 512:
        fail("comparator.invalid")
    current = value
    for raw_segment in pointer.split("/")[1:]:
        segment = raw_segment.replace("~1", "/").replace("~0", "~")
        if "~" in raw_segment.replace("~0", "").replace("~1", ""):
            fail("comparator.invalid")
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        elif isinstance(current, list) and re.fullmatch(r"0|[1-9][0-9]*", segment):
            index = int(segment)
            if index >= len(current):
                fail("comparator.invalid")
            current = current[index]
        else:
            fail("comparator.invalid")
    return current


def _bind_observation_side(
    side: Any,
    expected_kind: str,
    artifacts: dict[tuple[str, str], dict[str, Any]],
    allowed_refs: set[bytes] | None,
) -> tuple[Decimal | None, str | None, int]:
    exact_keys(side, OBSERVATION_BINDING_KEYS, "comparator.invalid")
    if side["source_kind"] != expected_kind:
        fail("comparator.invalid")
    artifact = artifacts.get((side["source_id"], side["artifact_id"]))
    if artifact is None or artifact["source_kind"] != expected_kind:
        fail("comparator.invalid")
    encoded_ref = canonical(side["evidence_ref"])
    if (
        not any(encoded_ref == canonical(ref) for ref in artifact["evidence_refs"])
        or (allowed_refs is not None and encoded_ref not in allowed_refs)
        or side["observed_offset_ns"] != artifact["recorder_ingested_offset_ns"]
    ):
        fail("comparator.invalid")
    selected_value = _pointer_get(
        artifact["normalized_evidence"], side["value_pointer"]
    )
    selected_unit = _pointer_get(
        artifact["normalized_evidence"], side["unit_pointer"]
    )
    if selected_value != side["native_decimal"] or selected_unit != side["native_unit"]:
        fail("comparator.invalid")
    parsed = None if selected_value is None else _decimal(selected_value)
    if selected_unit is not None and not _ascii_token(selected_unit):
        fail("comparator.invalid")
    return parsed, selected_unit, side["observed_offset_ns"]


def _validate_parameters(parameters: dict[str, Any]) -> None:
    window = parameters["window"]
    tolerance = parameters["tolerance"]
    conversion = parameters["unit_conversion"]
    rounding = parameters["rounding"]
    threshold = parameters["conflict_threshold"]
    if (
        window["start_offset_ns"] >= window["end_offset_ns"]
        or tolerance["relative_ppm"] > 1_000_000
        or parameters["minimum_samples"] > HARD_LIMITS["max_samples_per_comparator"]
        or parameters["maximum_missing_samples"]
        > HARD_LIMITS["max_samples_per_comparator"]
        or threshold["consecutive_samples"]
        > HARD_LIMITS["max_samples_per_comparator"]
        or (rounding["mode"] == "NONE" and rounding["decimal_places"] is not None)
        or (rounding["mode"] == "HALF_EVEN" and rounding["decimal_places"] is None)
        or (
            conversion["mode"] == "IDENTITY"
            and (
                conversion["source_unit"] != conversion["target_unit"]
                or conversion["scale_decimal"] != "1"
                or conversion["offset_decimal"] != "0"
            )
        )
    ):
        fail("comparator.invalid")
    _decimal(tolerance["absolute_decimal"], nonnegative=True)
    _decimal(conversion["scale_decimal"])
    _decimal(conversion["offset_decimal"])
    _decimal(threshold["absolute_decimal"], nonnegative=True)


def _round_decimal(value: Decimal, rounding: dict[str, Any]) -> Decimal:
    if rounding["mode"] == "NONE":
        return value
    quantum = Decimal(1).scaleb(-rounding["decimal_places"])
    try:
        return value.quantize(quantum, rounding=ROUND_HALF_EVEN)
    except InvalidOperation:
        fail("comparator.invalid")


def _format_decimal(value: Decimal, rounding: dict[str, Any]) -> str:
    if rounding["mode"] == "HALF_EVEN":
        return f"{value:.{rounding['decimal_places']}f}"
    return format(value, "f")


def _evaluate_numeric_window_details(
    parameters: dict[str, Any],
    samples: list[dict[str, Any]],
    artifacts: dict[tuple[str, str], dict[str, Any]],
    allowed_refs: set[bytes] | None = None,
) -> tuple[str, Decimal | None]:
    _validate_parameters(parameters)
    if not samples:
        return "NOT_EVALUATED", None
    encoded = [canonical(sample) for sample in samples]
    if len(encoded) != len(set(encoded)):
        fail("ordering.invalid")
    window = parameters["window"]
    conversion = parameters["unit_conversion"]
    rounding = parameters["rounding"]
    unavailable = 0
    present = 0
    mismatch = False
    conflict_run = 0
    conflict = False
    last_right: Decimal | None = None
    with localcontext() as context:
        context.prec = 512
        absolute_tolerance = _decimal(
            parameters["tolerance"]["absolute_decimal"], nonnegative=True
        )
        relative_ppm = Decimal(parameters["tolerance"]["relative_ppm"])
        conflict_threshold = _decimal(
            parameters["conflict_threshold"]["absolute_decimal"],
            nonnegative=True,
        )
        for sample in samples:
            offset = sample["offset_ns"]
            if not window["start_offset_ns"] <= offset <= window["end_offset_ns"]:
                fail("comparator.invalid")
            left, left_unit, left_offset = _bind_observation_side(
                sample["left"], "EBUS", artifacts, allowed_refs
            )
            right, right_unit, right_offset = _bind_observation_side(
                sample["right"], "EEBUS", artifacts, allowed_refs
            )
            if offset < left_offset or offset < right_offset:
                fail("comparator.invalid")
            if left is None or right is None or left_unit is None or right_unit is None:
                computed_state = "MISSING"
            elif (
                offset - left_offset > parameters["stale_cutoff_ns"]
                or offset - right_offset > parameters["stale_cutoff_ns"]
            ):
                computed_state = "STALE"
            else:
                computed_state = "PRESENT"
            if sample["state"] != computed_state:
                fail("comparator.invalid")
            if computed_state != "PRESENT":
                unavailable += 1
                conflict_run = 0
                continue
            if left_unit != conversion["source_unit"] or right_unit != conversion["target_unit"]:
                fail("comparator.invalid")
            converted_left = left * _decimal(conversion["scale_decimal"]) + _decimal(
                conversion["offset_decimal"]
            )
            rounded_left = _round_decimal(converted_left, rounding)
            rounded_right = _round_decimal(right, rounding)
            last_right = rounded_right
            delta = abs(rounded_left - rounded_right)
            allowed = absolute_tolerance + abs(rounded_right) * relative_ppm / Decimal(
                1_000_000
            )
            present += 1
            mismatch = mismatch or delta > allowed
            if delta >= conflict_threshold:
                conflict_run += 1
                if conflict_run >= parameters["conflict_threshold"]["consecutive_samples"]:
                    conflict = True
            else:
                conflict_run = 0
    if (
        unavailable > parameters["maximum_missing_samples"]
        or present < parameters["minimum_samples"]
    ):
        return "INDETERMINATE", last_right
    if conflict:
        return "CONFLICT", last_right
    return ("MISMATCH" if mismatch else "MATCH"), last_right


def _evaluate_numeric_window(
    parameters: dict[str, Any],
    samples: list[dict[str, Any]],
    artifacts: dict[tuple[str, str], dict[str, Any]],
) -> str:
    return _evaluate_numeric_window_details(parameters, samples, artifacts)[0]


def check_comparators(
    graph: dict[str, Any], registry: dict[str, Any], source_bundle: dict[str, Any]
) -> None:
    drafts = graph["comparator_drafts"]
    if (
        len(drafts) != 1
        or drafts[0]["draft_id"] != "NUMERIC_WINDOW_V1_DRAFT"
        or drafts[0]["type"] != "NUMERIC_WINDOW"
        or registry["comparators"][0]["draft_id"] != drafts[0]["draft_id"]
    ):
        fail("comparator.invalid")
    parameters = drafts[0]["parameters"]
    _validate_parameters(parameters)
    artifacts = _artifact_index(source_bundle)
    for fact in graph["facts"]:
        evaluation = fact["comparator"]
        if evaluation["draft_id"] != drafts[0]["draft_id"]:
            fail("comparator.invalid")
        allowed_refs = {
            canonical(ref) for ref in fact["provenance"]["native_evidence_refs"]
        }
        computed, last_right = _evaluate_numeric_window_details(
            parameters, evaluation["samples"], artifacts, allowed_refs
        )
        if evaluation["outcome"] != computed:
            fail("comparator.invalid")
        status = fact["status"]
        expected = {
            ("RAW_ONLY", None): {"NOT_EVALUATED"},
            ("CANDIDATE", None): {"MATCH"},
            ("CONFLICTED", None): {"MISMATCH", "CONFLICT"},
            ("WITHHELD", "CONFLICT"): {"CONFLICT"},
            ("WITHHELD", "NOT_TESTED"): {
                "NOT_EVALUATED",
                "INDETERMINATE",
            },
            ("WITHHELD", "NO_SIGNAL"): {"NOT_EVALUATED"},
            ("WITHHELD", "CLOUD_ONLY"): {"NOT_EVALUATED"},
        }
        terminal = fact["terminal_negative_state"]
        if computed not in expected.get((status, terminal), set()):
            fail("comparator.invalid")
        if status == "CANDIDATE":
            if (
                last_right is None
                or fact["draft_unit"] != parameters["unit_conversion"]["target_unit"]
                or fact["draft_value"]
                != _format_decimal(last_right, parameters["rounding"])
            ):
                fail("comparator.invalid")
        if terminal == "CONFLICT" and computed != "CONFLICT":
            fail("comparator.invalid")
        if terminal in {"NO_SIGNAL", "CLOUD_ONLY"} and computed != "NOT_EVALUATED":
            fail("comparator.invalid")


def check_anti_leak(graph: dict[str, Any], registry: dict[str, Any]) -> None:
    if graph["visibility"] != {
        "channel": registry["candidate_channel"],
        "promotion_state": "NOT_PROMOTED",
        "stable_exposure": False,
        "command_capable": False,
        "protocol_translation": False,
    }:
        fail("anti_leak.consumer")


def check_hashes(graph: dict[str, Any]) -> None:
    for fact in graph["facts"]:
        if fact["fact_hash"] != "sha256:" + fact_hexdigest(fact):
            fail("hash.fact")
    hexdigest = graph_hexdigest(graph)
    if (
        graph["graph_hash"] != "sha256:" + hexdigest
        or graph["graph_id"] != "dcfgv1:sha256:" + hexdigest
    ):
        fail("hash.graph")


def verify(
    graph: Any,
    registry: dict[str, Any],
    registry_raw: bytes,
    raw_size: int,
    source_bundle: dict[str, Any],
    source_replay: dict[str, Any],
) -> dict[str, Any]:
    schema_check(graph)
    check_limits(graph, raw_size)
    check_registry_binding(graph, registry, registry_raw)
    check_provenance(graph, registry, source_bundle, source_replay)
    check_identities(graph, source_bundle)
    check_ordering(graph)
    check_states(graph, registry)
    check_comparators(graph, registry, source_bundle)
    check_anti_leak(graph, registry)
    check_hashes(graph)
    return graph


def replay(graph: dict[str, Any]) -> dict[str, Any]:
    results = [
        {
            "candidate_id": fact["candidate_id"],
            "proposed_path": fact["proposed_path"],
            "status": fact["status"],
            "terminal_negative_state": fact["terminal_negative_state"],
            "confidence": fact["confidence"],
            "comparator_outcome": fact["comparator"]["outcome"],
            "fact_hash": fact["fact_hash"],
            "native_evidence_digests": sorted(
                {
                    ref["digest"]
                    for ref in fact["provenance"]["native_evidence_refs"]
                }
            ),
        }
        for fact in graph["facts"]
    ]
    value = {
        "contract": "helianthus.platform.draft-candidate-fact-replay.v1",
        "schema_version": 1,
        "replay_id": "dcfrv1:sha256:" + "0" * 64,
        "replay_hash": "sha256:" + "0" * 64,
        "graph_id": graph["graph_id"],
        "graph_hash": graph["graph_hash"],
        "registry_digest": graph["registry"]["digest"],
        "source_bundle": {
            "bundle_id": graph["source_bundle"]["bundle_id"],
            "bundle_hash": graph["source_bundle"]["bundle_hash"],
            "replay_hash": graph["source_bundle"]["replay_hash"],
        },
        "results": results,
    }
    check_portable(value)
    view = {
        key: item
        for key, item in value.items()
        if key not in {"replay_id", "replay_hash"}
    }
    hexdigest = digest(REPLAY_DOMAIN, view)
    value["replay_id"] = "dcfrv1:sha256:" + hexdigest
    value["replay_hash"] = "sha256:" + hexdigest
    return value


def _verify_source_inputs(
    registry: dict[str, Any],
    registry_path: pathlib.Path,
    source_bundle: dict[str, Any],
    source_bundle_raw: bytes,
    source_replay: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_registry_path = registry_path.parent / pathlib.Path(
        registry["source_contract"]["source_registry_path"]
    ).name
    try:
        if (
            hashlib.sha256(source_registry_path.read_bytes()).hexdigest()
            != registry["source_contract"]["source_registry_sha256"]
        ):
            fail("provenance.binding")
        source_registry = synchronized.load_registry(source_registry_path)
        verified_source = synchronized.verify(
            copy.deepcopy(source_bundle), source_registry, len(source_bundle_raw)
        )
        generated_source_replay = synchronized.replay(verified_source)
    except Failure:
        raise
    except (synchronized.Failure, OSError, KeyError, TypeError, ValueError):
        fail("provenance.binding")
    if generated_source_replay != source_replay:
        fail("provenance.binding")
    return verified_source, generated_source_replay


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("command", choices=("verify", "replay"))
    parser.add_argument("--graph", type=pathlib.Path, required=True)
    parser.add_argument("--registry", type=pathlib.Path, required=True)
    parser.add_argument("--source-bundle", type=pathlib.Path, required=True)
    parser.add_argument("--source-replay", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        graph, graph_raw = load_json(args.graph, input_kind="graph")
        schema_check(graph)
        check_limits(graph, len(graph_raw))

        registry, registry_raw = load_json(args.registry, input_kind="registry")
        check_registry_binding(graph, registry, registry_raw)

        source_bundle, source_bundle_raw = load_json(
            args.source_bundle, input_kind="source"
        )
        source_replay, _ = load_json(args.source_replay, input_kind="source")
        verified_source, verified_source_replay = _verify_source_inputs(
            registry,
            args.registry,
            source_bundle,
            source_bundle_raw,
            source_replay,
        )

        check_provenance(graph, registry, verified_source, verified_source_replay)
        check_identities(graph, verified_source)
        check_ordering(graph)
        check_states(graph, registry)
        check_comparators(graph, registry, verified_source)
        check_anti_leak(graph, registry)
        check_hashes(graph)
        if args.command == "verify":
            sys.stdout.write("ok\n")
        else:
            sys.stdout.write(canonical(replay(graph)).decode("utf-8") + "\n")
        return 0
    except Failure as error:
        sys.stdout.write(str(error) + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
