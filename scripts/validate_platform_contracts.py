#!/usr/bin/env python3
"""Validate the closed cross-runtime documentation ownership contract."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import ipaddress
import pathlib
import re
import stat
import subprocess
import sys
import urllib.parse
from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from typing import Any

import yaml


MANIFEST = pathlib.Path("docs/platform/manifests/eebus-doc-ownership.yaml")
REPOSITORIES = (
    "helianthus-docs-ebus",
    "helianthus-docs-eebus",
    "helianthus-eebusreg",
)
SURFACES = {
    "protocol",
    "architecture",
    "api",
    "platform",
    "code_repo",
    "summary_only",
}
STATES = {"planned", "candidate", "active", "withdrawn"}
MILESTONES = (
    "MSP-DOCS-API-SCHEMA",
    "MSP-DOCS-PLATFORM",
    "MSP-DOCS-E2",
    "MSP-DOCS-CLEAN",
)
MILESTONE_INDEX = {name: index for index, name in enumerate(MILESTONES)}
TARGET_STATES = {"candidate", "active", "withdrawn"}

EXACT_PYTHON = (3, 12, 10)
EXACT_PYYAML = "6.0.2"
SUPPORTED_PYTHON_MIN = (3, 12, 0)
SUPPORTED_PYTHON_MAX = (3, 15, 0)
SUPPORTED_PYYAML_MIN = (6, 0, 2)
SUPPORTED_PYYAML_MAX = (7, 0, 0)
TOOLCHAIN_MODES = {"exact", "supported"}

MAX_MANIFEST_BYTES = 64 * 1024
MAX_YAML_NESTING = 24
MAX_YAML_ALIASES = 16
MAX_YAML_TOKENS = 8192
MAX_YAML_NODES = 4096

TOP_FIELDS = {"schema", "version", "entries"}
ENTRY_FIELDS = {
    "id",
    "surface",
    "owner",
    "source",
    "canonical",
    "state",
    "outputs",
    "lifecycle",
    "enforcement",
}
LOCATION_FIELDS = {"repository", "path"}
OUTPUT_FIELDS = {
    "candidate",
    "stable_navigation",
    "search",
    "sitemap",
    "versioned_bundle",
    "release_bundle",
}
LIFECYCLE_FIELDS = {
    "created_at",
    "expires_at",
    "source_issue",
    "source_pr",
    "source_ref",
    "content_sha256",
    "approved_at",
    "frozen_at",
    "cleanup_required",
}
LIFECYCLE_TIMESTAMP_FIELDS = {
    "created_at",
    "expires_at",
    "approved_at",
    "frozen_at",
}
ENFORCEMENT_FIELDS = {"milestone", "required_state"}
STABLE_OUTPUTS = OUTPUT_FIELDS - {"candidate"}
CANONICAL_SURFACES = {"protocol", "architecture", "api", "platform"}

IMMUTABLE_REF = re.compile(r"[0-9a-fA-F]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
ENTRY_ID = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
RFC3339_UTC = re.compile(
    r"[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.[0-9]{1,6})?Z\Z"
)
PRIVATE_IDENTIFIER = re.compile(
    r"(?i)(?:serial|ski|mac|peer[_-]?id|device[_-]?id|token|password|secret)\s*="
)
WINDOWS_ABSOLUTE = re.compile(r"[A-Za-z]:[\\/]")
NORMATIVE = re.compile(
    r"\b(?:must|shall|should|required|mandatory|acceptance criteria|needs? to)\b",
    re.I,
)
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
SETEXT_HEADING = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
REFERENCE_DEFINITION = re.compile(
    r"^ {0,3}\[([^\]]+)\]:[ \t]*(?:<([^>\n]+)>|(\S+))"
)
VERSION = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)\Z")
RENDERED_URL = re.compile(r"\bhttps?://[^\s<>\"']+", re.I)
CLAUSE_BOUNDARY = re.compile(r"(?:;|(?<=[.!?])\s+)")
EXPLICIT_PREDICATE_BOUNDARY = re.compile(
    r"(?:,\s*|\s+\b(?:and|but|yet|while|whereas)\b\s+|"
    r"\s+(?=(?:which|that|who)\b))"
    r"(?=(?:(?:which|that|who)\b\s+)?[^,;]{0,80}"
    r"\b(?:must|shall|should|required|mandatory|needs?\s+to)\b)",
    re.I,
)

PROTOCOL_CONTEXT = re.compile(
    r"\b(?:SHIP|SPINE|SKI|wire protocol|protocol peer|protocol frame|protocol message)\b",
    re.I,
)
PROTOCOL_BEHAVIOR = re.compile(
    r"\b(?:send(?:s|ing)?|receiv(?:e|es|ed|ing)|negotiat(?:e|es|ed|ing)|"
    r"encod(?:e|es|ed|ing)|decod(?:e|es|ed|ing)|respond(?:s|ed|ing)?|"
    r"retr(?:y|ies|ied|ying)|acknowledg(?:e|es|ed|ing)|"
    r"advertis(?:e|es|ed|ing)|initiat(?:e|es|ed|ing)|"
    r"establish(?:es|ed|ing)?|clos(?:e|es|ed|ing))\b",
    re.I,
)
ARCHITECTURE_CONTEXT = re.compile(
    r"\beebus\b.*\b(?:runtime|trust|persistence|lifecycle|adapter|reconnect|"
    r"session store|cache)\b|\b(?:runtime|trust|persistence|lifecycle|adapter|"
    r"reconnect|session store|cache)\b.*\beebus\b",
    re.I | re.S,
)
ARCHITECTURE_BEHAVIOR = re.compile(
    r"\b(?:persist|store|load|restore|reconnect|manage|own|create|listen|cache)s?\b",
    re.I,
)
API_CONTEXT = re.compile(
    r"\beebus\b.*\b(?:Go API|package|function|method|symbol|signature|public API)\b|"
    r"\b(?:Go API|package|function|method|symbol|signature|public API)\b.*\beebus\b",
    re.I | re.S,
)
API_BEHAVIOR = re.compile(
    r"\b(?:expos(?:e|es|ed|ing)|export(?:s|ed|ing)?|return(?:s|ed|ing)?|"
    r"accept(?:s|ed|ing)?|declar(?:e|es|ed|ing)|defin(?:e|es|ed|ing)|"
    r"provid(?:e|es|ed|ing))\b",
    re.I,
)
GO_DECLARATION = re.compile(r"\bfunc\s+[A-Z][A-Za-z0-9_]*\s*\(")
NON_NORMATIVE = re.compile(
    r"\b(?:non[- ]normative|informative only|example only)\b", re.I
)
NON_NORMATIVE_LEAD = re.compile(
    r"\b(?:non[- ]normative|informative)\b.*"
    r"\b(?:example|quotation|quote|excerpt|reference)\b",
    re.I,
)
DOCUMENTATION_OWNERSHIP = re.compile(
    r"(?:\b(?:documentation|docs?|page|repository)\b[^.!?]{0,80}"
    r"\b(?:must|shall|required)\b[^.!?]{0,80}"
    r"\b(?:own|ownership|summar(?:y|ize|izes|ized)|link|reference|"
    r"source of truth)\b|"
    r"\b(?:must|shall|required)\b[^.!?]{0,80}"
    r"\b(?:owned|documented|summarized|linked|referenced)\b[^.!?]{0,80}"
    r"\b(?:documentation|docs?|page|repository|source of truth)\b)",
    re.I,
)
PLATFORM_GOVERNANCE_CONTEXT = re.compile(
    r"\b(?:gate|proof|artifact|evidence|ownership|summary)\b", re.I
)
PLATFORM_GOVERNANCE_PROSE = re.compile(
    r"\b(?:artifact|evidence|proof|case|result|record|claim|reference|scope)\w*\b",
    re.I,
)
PLATFORM_GOVERNANCE_ACTION = re.compile(
    r"\b(?:record|report|claim|prove|verify|capture|include|reference|link|"
    r"document|state)s?\b",
    re.I,
)
GOVERNANCE_COMPLEMENT = re.compile(
    r"\b(?:record|report|claim|prove|verify|capture|include|reference|link|"
    r"document|state)s?\b[^,;]*\b(?:whether|if)\b",
    re.I,
)
NEGATIVE_GOVERNANCE_CLAIM = re.compile(
    r"\b(?:must|shall|should|needs?\s+to)\s+not\s+"
    r"(?:claim|report|state|document)\b",
    re.I,
)
TOMBSTONE_IMMUTABLE_FIELDS = ("surface", "owner", "source")


class _ManifestSchemaError(Exception):
    """Internal marker for non-reflective manifest parse failures."""


def _result(categories: Iterable[str]) -> list[str]:
    return sorted(set(categories))


def _run_git(root: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _run_git_bytes(
    root: pathlib.Path, *args: str
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
    )


def _clean_checkout(root: pathlib.Path) -> bool:
    inside = _run_git(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return False
    status_result = _run_git(
        root, "status", "--porcelain=v1", "--untracked-files=all"
    )
    return status_result.returncode == 0 and not status_result.stdout


def _checkout_matches_ref(root: pathlib.Path, ref: str | None) -> bool:
    if not isinstance(ref, str) or IMMUTABLE_REF.fullmatch(ref) is None:
        return False
    resolved = _run_git(root, "rev-parse", "--verify", f"{ref}^{{commit}}")
    head = _run_git(root, "rev-parse", "HEAD")
    return (
        resolved.returncode == 0
        and head.returncode == 0
        and resolved.stdout.strip().casefold() == ref.casefold()
        and head.stdout.strip().casefold() == ref.casefold()
    )


def _remote_repository(value: str) -> str | None:
    remote = value.strip().removesuffix(".git")
    if remote.startswith("git@github.com:"):
        return remote.split(":", 1)[1]
    parsed = urllib.parse.urlsplit(remote)
    if parsed.hostname == "github.com":
        return parsed.path.lstrip("/")
    return None


def _repository_root_valid(root: pathlib.Path, repository: str) -> bool:
    try:
        root_stat = root.lstat()
    except OSError:
        return False
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        return False
    top = _run_git(root, "rev-parse", "--show-toplevel")
    remote = _run_git(root, "remote", "get-url", "origin")
    if top.returncode != 0 or remote.returncode != 0:
        return False
    try:
        top_path = pathlib.Path(top.stdout.strip()).resolve(strict=True)
        root_path = root.resolve(strict=True)
    except OSError:
        return False
    expected = f"Project-Helianthus/{repository}"
    actual = _remote_repository(remote.stdout)
    return top_path == root_path and actual is not None and actual.casefold() == expected.casefold()


def _portable_path(value: str) -> bool:
    path = pathlib.PurePosixPath(value)
    return (
        bool(value)
        and not value.startswith(("/", "~", "./"))
        and WINDOWS_ABSOLUTE.match(value) is None
        and "\\" not in value
        and "//" not in value
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def _path_at_or_below(value: str, prefix: str) -> bool:
    path_parts = pathlib.PurePosixPath(value).parts
    prefix_parts = pathlib.PurePosixPath(prefix).parts
    return path_parts[: len(prefix_parts)] == prefix_parts


def _location_matches(
    location: Mapping[str, str], repository: str, prefix: str
) -> bool:
    return location["repository"] == repository and _path_at_or_below(
        location["path"], prefix
    )


def _surface_binding_valid(entry: Mapping[str, Any]) -> bool:
    surface = entry["surface"]
    owner = entry["owner"]
    source = entry["source"]
    if surface == "protocol":
        return _location_matches(
            owner, "helianthus-docs-eebus", "protocols"
        ) and _location_matches(source, "helianthus-docs-eebus", "protocols")
    if surface == "architecture":
        return _location_matches(
            owner, "helianthus-docs-eebus", "architecture"
        ) and _location_matches(source, "helianthus-docs-eebus", "architecture")
    if surface == "api":
        source_valid = _location_matches(
            source, "helianthus-docs-eebus", "api"
        ) or _location_matches(source, "helianthus-eebusreg", "api")
        return (
            _location_matches(owner, "helianthus-docs-eebus", "api")
            and source_valid
        )
    if surface == "platform":
        return _location_matches(
            owner, "helianthus-docs-ebus", "docs/platform"
        ) and _location_matches(source, "helianthus-docs-ebus", "docs/platform")
    if surface == "code_repo":
        return _location_matches(
            owner, "helianthus-eebusreg", "docs"
        ) and _location_matches(source, "helianthus-eebusreg", "docs")
    if surface == "summary_only":
        return owner == {
            "repository": "helianthus-eebusreg",
            "path": "README.md",
        } and source == {
            "repository": "helianthus-docs-eebus",
            "path": "README.md",
        }
    return False


def _artifact_kind(root: pathlib.Path, relative: str) -> str:
    if not _portable_path(relative):
        return "outside"
    try:
        root_path = root.absolute()
        root_stat = root_path.lstat()
    except OSError:
        return "missing"
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        return "symlink" if stat.S_ISLNK(root_stat.st_mode) else "invalid"

    current = root_path
    parts = pathlib.PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        try:
            item_stat = current.lstat()
        except FileNotFoundError:
            return "missing"
        except OSError:
            return "invalid"
        if stat.S_ISLNK(item_stat.st_mode):
            return "symlink"
        if index < len(parts) - 1 and not stat.S_ISDIR(item_stat.st_mode):
            return "invalid"

    try:
        resolved_root = root_path.resolve(strict=True)
        resolved_item = current.resolve(strict=True)
    except OSError:
        return "invalid"
    if not resolved_item.is_relative_to(resolved_root):
        return "outside"
    final_stat = current.lstat()
    if stat.S_ISREG(final_stat.st_mode):
        return "regular"
    if stat.S_ISDIR(final_stat.st_mode):
        return "directory"
    return "invalid"


def _read_regular_artifact(root: pathlib.Path, relative: str) -> bytes | None:
    if _artifact_kind(root, relative) != "regular":
        return None
    try:
        return (root / pathlib.PurePosixPath(relative)).read_bytes()
    except OSError:
        return None


def _scan_yaml_resources(text: str) -> None:
    alias_count = 0
    depth = 0
    token_count = 0
    starts = (
        yaml.tokens.BlockMappingStartToken,
        yaml.tokens.BlockSequenceStartToken,
        yaml.tokens.FlowMappingStartToken,
        yaml.tokens.FlowSequenceStartToken,
    )
    ends = (
        yaml.tokens.BlockEndToken,
        yaml.tokens.FlowMappingEndToken,
        yaml.tokens.FlowSequenceEndToken,
    )
    for token in yaml.scan(text, Loader=yaml.SafeLoader):
        token_count += 1
        if token_count > MAX_YAML_TOKENS:
            raise _ManifestSchemaError
        if isinstance(token, yaml.tokens.AliasToken):
            alias_count += 1
            if alias_count > MAX_YAML_ALIASES:
                raise _ManifestSchemaError
        if isinstance(token, starts):
            depth += 1
            if depth > MAX_YAML_NESTING:
                raise _ManifestSchemaError
        elif isinstance(token, ends):
            depth = max(0, depth - 1)


def _inspect_yaml_node(root: yaml.nodes.Node | None) -> None:
    if root is None:
        raise _ManifestSchemaError
    seen: set[int] = set()
    active: set[int] = set()
    node_count = 0

    def visit(node: yaml.nodes.Node, depth: int) -> None:
        nonlocal node_count
        if depth > MAX_YAML_NESTING:
            raise _ManifestSchemaError
        identity = id(node)
        if identity in active:
            raise _ManifestSchemaError
        if identity in seen:
            return
        seen.add(identity)
        active.add(identity)
        node_count += 1
        if node_count > MAX_YAML_NODES:
            raise _ManifestSchemaError
        try:
            if isinstance(node, yaml.nodes.MappingNode):
                keys: set[str] = set()
                for key, value in node.value:
                    if (
                        not isinstance(key, yaml.nodes.ScalarNode)
                        or key.tag != "tag:yaml.org,2002:str"
                        or key.value in keys
                    ):
                        raise _ManifestSchemaError
                    keys.add(key.value)
                    visit(key, depth + 1)
                    visit(value, depth + 1)
            elif isinstance(node, yaml.nodes.SequenceNode):
                for value in node.value:
                    visit(value, depth + 1)
            elif not isinstance(node, yaml.nodes.ScalarNode):
                raise _ManifestSchemaError
        finally:
            active.remove(identity)

    visit(root, 1)


def _parse_manifest_path(path: pathlib.Path) -> dict[str, Any] | None:
    loader: yaml.SafeLoader | None = None
    try:
        path_stat = path.lstat()
        if not stat.S_ISREG(path_stat.st_mode):
            raise _ManifestSchemaError
        raw = path.read_bytes()
        if len(raw) > MAX_MANIFEST_BYTES:
            raise _ManifestSchemaError
        text = raw.decode("utf-8")
        _scan_yaml_resources(text)
        loader = yaml.SafeLoader(text)
        node = loader.get_single_node()
        _inspect_yaml_node(node)
        assert node is not None
        loaded = loader.construct_document(node)
    except (
        OSError,
        UnicodeError,
        yaml.YAMLError,
        RecursionError,
        MemoryError,
        OverflowError,
        _ManifestSchemaError,
    ):
        return None
    finally:
        if loader is not None:
            loader.dispose()
    if not isinstance(loaded, dict):
        return None
    return loaded


def _load_manifest(root: pathlib.Path) -> tuple[dict[str, Any] | None, str | None]:
    kind = _artifact_kind(root, MANIFEST.as_posix())
    if kind == "missing":
        return None, "manifest.missing"
    if kind != "regular":
        return None, "manifest.schema"
    loaded = _parse_manifest_path(root / MANIFEST)
    return (loaded, None) if loaded is not None else (None, "manifest.schema")


def _optional_text(value: Any) -> bool:
    return value is None or isinstance(value, str)


def _schema_valid(manifest: Mapping[str, Any]) -> bool:
    if set(manifest) != TOP_FIELDS:
        return False
    if not isinstance(manifest.get("schema"), str):
        return False
    version = manifest.get("version")
    if not isinstance(version, int) or isinstance(version, bool):
        return False
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        return False

    ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != ENTRY_FIELDS:
            return False
        entry_id = entry.get("id")
        surface = entry.get("surface")
        if (
            not isinstance(entry_id, str)
            or ENTRY_ID.fullmatch(entry_id) is None
            or entry_id in ids
            or not isinstance(surface, str)
            or surface not in SURFACES
            or not isinstance(entry.get("canonical"), bool)
            or not isinstance(entry.get("state"), str)
        ):
            return False
        ids.add(entry_id)
        for field in ("owner", "source"):
            location = entry.get(field)
            if (
                not isinstance(location, dict)
                or set(location) != LOCATION_FIELDS
                or location.get("repository") not in REPOSITORIES
                or not isinstance(location.get("path"), str)
                or not location.get("path")
            ):
                return False
        outputs = entry.get("outputs")
        if (
            not isinstance(outputs, dict)
            or set(outputs) != OUTPUT_FIELDS
            or any(not isinstance(outputs.get(key), bool) for key in OUTPUT_FIELDS)
        ):
            return False
        lifecycle = entry.get("lifecycle")
        if not isinstance(lifecycle, dict) or set(lifecycle) != LIFECYCLE_FIELDS:
            return False
        if _parse_instant(lifecycle.get("created_at")) is None:
            return False
        if any(
            not _optional_text(lifecycle.get(key))
            for key in LIFECYCLE_FIELDS - {"created_at", "cleanup_required"}
        ):
            return False
        if any(
            lifecycle.get(key) is not None
            and _parse_instant(lifecycle.get(key)) is None
            for key in LIFECYCLE_TIMESTAMP_FIELDS - {"created_at"}
        ):
            return False
        if not isinstance(lifecycle.get("cleanup_required"), bool):
            return False
        enforcement = entry.get("enforcement")
        milestone = enforcement.get("milestone") if isinstance(enforcement, dict) else None
        required_state = (
            enforcement.get("required_state") if isinstance(enforcement, dict) else None
        )
        if (
            not isinstance(enforcement, dict)
            or set(enforcement) != ENFORCEMENT_FIELDS
            or not isinstance(milestone, str)
            or milestone not in MILESTONE_INDEX
            or not isinstance(required_state, str)
            or required_state not in TARGET_STATES
        ):
            return False
    return True


def _parse_instant(value: Any) -> datetime | None:
    if not isinstance(value, str) or RFC3339_UTC.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        return None
    return parsed.astimezone(timezone.utc)


def _all_strings(value: Any) -> Iterable[str]:
    seen: set[int] = set()

    def walk(item: Any) -> Iterable[str]:
        if isinstance(item, str):
            yield item
            return
        if not isinstance(item, (Mapping, list)):
            return
        identity = id(item)
        if identity in seen:
            return
        seen.add(identity)
        if isinstance(item, Mapping):
            for child in item.values():
                yield from walk(child)
        else:
            for child in item:
                yield from walk(child)

    yield from walk(value)


def _contains_private_network(value: str) -> bool:
    for token in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", value):
        try:
            address = ipaddress.ip_address(token)
        except ValueError:
            continue
        if address.is_private or address.is_link_local or address.is_loopback:
            return True
    return False


def _manifest_categories(manifest: dict[str, Any]) -> set[str]:
    categories: set[str] = set()
    if manifest["schema"] != "helianthus.platform.doc-ownership":
        categories.add("manifest.schema")
    if manifest["version"] != 1:
        categories.add("manifest.version")
    if {entry["surface"] for entry in manifest["entries"]} != SURFACES:
        categories.add("ownership.surface-missing")

    pairs: set[tuple[str, str, str, str]] = set()
    canonical_owners: set[tuple[str, str]] = set()
    for entry in manifest["entries"]:
        pair = (
            entry["owner"]["repository"],
            entry["owner"]["path"],
            entry["source"]["repository"],
            entry["source"]["path"],
        )
        if pair in pairs:
            categories.add("ownership.pair-duplicate")
        pairs.add(pair)
        if entry["canonical"]:
            owner = (entry["owner"]["repository"], entry["owner"]["path"])
            if owner in canonical_owners:
                categories.add("ownership.canonical-duplicate")
            canonical_owners.add(owner)
        for location in (entry["owner"], entry["source"]):
            if not _portable_path(location["path"]):
                categories.add("path.absolute")
        if all(
            _portable_path(location["path"])
            for location in (entry["owner"], entry["source"])
        ) and not _surface_binding_valid(entry):
            categories.add("ownership.surface-binding")
        if entry["state"] in STATES:
            expected_canonical = (
                entry["surface"] in CANONICAL_SURFACES
                and entry["state"] == "active"
            )
            if entry["canonical"] != expected_canonical:
                categories.add("ownership.canonical-state")

    if any(
        PRIVATE_IDENTIFIER.search(value) or _contains_private_network(value)
        for value in _all_strings(manifest)
    ):
        categories.add("privacy.private-identifier")
    return categories


def _enforcement_categories(
    manifest: dict[str, Any], enforce_through: str
) -> set[str]:
    if enforce_through not in MILESTONE_INDEX:
        return {"enforcement.stage"}
    stage = MILESTONE_INDEX[enforce_through]
    for entry in manifest["entries"]:
        enforcement = entry["enforcement"]
        required_at = MILESTONE_INDEX[enforcement["milestone"]]
        state = entry["state"]
        if state not in STATES:
            continue
        if state == "withdrawn":
            continue
        if required_at <= stage:
            if state != enforcement["required_state"]:
                return {"enforcement.transition"}
        elif state not in {"planned", "candidate"}:
            return {"enforcement.transition"}
    return set()


def _state_categories(
    manifest: dict[str, Any], roots: Mapping[str, pathlib.Path]
) -> set[str]:
    categories: set[str] = set()
    for entry in manifest["entries"]:
        state = entry["state"]
        if state not in STATES:
            categories.add("state.invalid")
            continue

        lifecycle = entry["lifecycle"]
        outputs = entry["outputs"]
        created = _parse_instant(lifecycle["created_at"])
        expires = _parse_instant(lifecycle["expires_at"])
        approved = _parse_instant(lifecycle["approved_at"])
        frozen = _parse_instant(lifecycle["frozen_at"])

        if state == "planned":
            invalid = (
                created is None
                or expires is None
                or expires - created != timedelta(days=14)
                or entry["canonical"]
                or any(outputs.values())
                or not (lifecycle["source_issue"] or lifecycle["source_pr"])
                or lifecycle["source_ref"] is not None
                or lifecycle["content_sha256"] is not None
                or approved is not None
                or frozen is not None
                or lifecycle["cleanup_required"]
            )
            if invalid:
                categories.add("state.planned")

        elif state == "candidate":
            hidden = "_candidate" in pathlib.PurePosixPath(
                entry["owner"]["path"]
            ).parts
            source_ref = lifecycle["source_ref"]
            content_hash = lifecycle["content_sha256"]
            invalid = (
                created is None
                or expires is None
                or expires - created != timedelta(days=30)
                or entry["canonical"]
                or outputs["candidate"] is not True
                or any(outputs[key] for key in STABLE_OUTPUTS)
                or not hidden
                or not lifecycle["source_pr"]
                or not isinstance(source_ref, str)
                or IMMUTABLE_REF.fullmatch(source_ref or "") is None
                or not isinstance(content_hash, str)
                or SHA256.fullmatch(content_hash or "") is None
                or approved is not None
                or frozen is not None
                or lifecycle["cleanup_required"]
            )
            source_root = roots.get(entry["source"]["repository"])
            if (
                not invalid
                and source_root is not None
                and _artifact_kind(source_root, entry["source"]["path"]) == "regular"
            ):
                shown = _run_git_bytes(
                    source_root,
                    "show",
                    f"{source_ref}:{entry['source']['path']}",
                )
                invalid = shown.returncode != 0 or hashlib.sha256(
                    shown.stdout
                ).hexdigest() != content_hash
            if invalid:
                categories.add("state.candidate")

        elif state == "active":
            invalid = (
                created is None
                or lifecycle["expires_at"] is not None
                or approved is None
                or frozen is None
                or not (created <= approved <= frozen)
                or outputs["candidate"]
                or any(not outputs[key] for key in STABLE_OUTPUTS)
                or lifecycle["cleanup_required"]
            )
            if invalid:
                categories.add("state.active")

        elif state == "withdrawn":
            invalid = (
                created is None
                or entry["canonical"]
                or any(outputs.values())
                or lifecycle["expires_at"] is not None
                or approved is not None
                or frozen is not None
                or not lifecycle["cleanup_required"]
            )
            if invalid:
                categories.add("state.withdrawn")
    return categories


def _artifact_categories(
    manifest: dict[str, Any], roots: Mapping[str, pathlib.Path]
) -> set[str]:
    categories: set[str] = set()
    for entry in manifest["entries"]:
        state = entry["state"]
        if state in {"active", "candidate"}:
            owner = entry["owner"]
            owner_root = roots.get(owner["repository"])
            owner_kind = (
                _artifact_kind(owner_root, owner["path"])
                if owner_root is not None
                else None
            )
            if owner_kind == "symlink":
                categories.add("path.symlink")
            elif owner_kind == "outside":
                categories.add("path.absolute")
            elif owner_kind is not None and owner_kind != "regular":
                categories.add("artifact.owner")

            source = entry["source"]
            same_location = source == owner
            source_root = roots.get(source["repository"])
            source_kind = (
                owner_kind
                if same_location
                else (
                    _artifact_kind(source_root, source["path"])
                    if source_root is not None
                    else None
                )
            )
            if same_location and owner_kind != "regular":
                continue
            if source_kind == "symlink":
                categories.add("path.symlink")
            elif source_kind == "outside":
                categories.add("path.absolute")
            elif source_kind is not None and source_kind != "regular":
                categories.add("artifact.source")

        elif state == "withdrawn" and entry["surface"] != "code_repo":
            checked: set[tuple[str, str]] = set()
            for location in (entry["owner"], entry["source"]):
                identity = (location["repository"], location["path"])
                if identity in checked:
                    continue
                checked.add(identity)
                location_root = roots.get(location["repository"])
                if location_root is not None and _artifact_kind(
                    location_root, location["path"]
                ) != "missing":
                    categories.add("artifact.withdrawn")
    return categories


def _expiry_categories(
    manifest: dict[str, Any], evaluated_at: str | None, evaluation_source: str | None
) -> set[str]:
    if not isinstance(evaluation_source, str) or not evaluation_source.strip():
        return {"expiry.source"}
    evaluated = _parse_instant(evaluated_at)
    if evaluated is None:
        return {"expiry.timestamp"}
    categories: set[str] = set()
    for entry in manifest["entries"]:
        state = entry["state"]
        if state not in {"planned", "candidate"}:
            continue
        expires = _parse_instant(entry["lifecycle"]["expires_at"])
        if expires is not None and evaluated >= expires:
            categories.add(f"expiry.{state}")
    return categories


def _strip_inline_code(line: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(line):
        if line[index] != "`":
            result.append(line[index])
            index += 1
            continue
        end_run = index
        while end_run < len(line) and line[end_run] == "`":
            end_run += 1
        marker = line[index:end_run]
        closing = line.find(marker, end_run)
        if closing == -1:
            result.append(marker)
            index = end_run
            continue
        result.append(" " * (closing + len(marker) - index))
        index = closing + len(marker)
    return "".join(result)


def _strip_markdown_code(text: str) -> str:
    clean: list[str] = []
    fence_char: str | None = None
    fence_length = 0
    for line in text.splitlines():
        match = FENCE.match(line)
        if fence_char is not None:
            if (
                match is not None
                and match.group(1)[0] == fence_char
                and len(match.group(1)) >= fence_length
                and not match.group(2).strip()
            ):
                fence_char = None
                fence_length = 0
            clean.append("")
            continue
        if match is not None:
            fence_char = match.group(1)[0]
            fence_length = len(match.group(1))
            clean.append("")
            continue
        if line.startswith(("    ", "\t")):
            clean.append("")
            continue
        clean.append(_strip_inline_code(line))
    return "\n".join(clean)


def _platform_markdown(root: pathlib.Path) -> Iterable[tuple[pathlib.Path, str]]:
    platform = root / "docs/platform"
    if _artifact_kind(root, "docs/platform") != "directory":
        return
    for path in sorted(platform.rglob("*.md")):
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if _artifact_kind(root, relative) != "regular":
            continue
        try:
            yield path, path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue


def _normalize_reference_label(value: str) -> str:
    return " ".join(value.split()).casefold()


def _find_markdown_closer(text: str, start: int, opening: str, closing: str) -> int:
    depth = 1
    index = start
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == opening:
            depth += 1
        elif text[index] == closing:
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


def _inline_destination(value: str) -> str | None:
    content = value.strip()
    if not content:
        return None
    if content.startswith("<"):
        end = content.find(">", 1)
        return content[1:end] if end > 1 else None
    depth = 0
    result: list[str] = []
    index = 0
    while index < len(content):
        char = content[index]
        if char == "\\" and index + 1 < len(content):
            result.append(content[index + 1])
            index += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif char.isspace() and depth == 0:
            break
        result.append(char)
        index += 1
    return "".join(result) or None


class _HTMLLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.targets: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        for key, value in attrs:
            if key.casefold() == "href" and value:
                self.targets.append(value)


def _trim_rendered_url(value: str) -> str:
    trimmed = value.rstrip(".,;:!?")
    for opening, closing in (("(", ")"), ("[", "]"), ("{", "}")):
        while trimmed.endswith(closing) and trimmed.count(closing) > trimmed.count(
            opening
        ):
            trimmed = trimmed[:-1]
    return trimmed


def _markdown_links(text: str) -> list[str]:
    clean = _strip_markdown_code(text)
    definitions: dict[str, str] = {}
    body_lines: list[str] = []
    for line in clean.splitlines():
        match = REFERENCE_DEFINITION.match(line)
        if match is None:
            body_lines.append(line)
            continue
        definitions[_normalize_reference_label(match.group(1))] = (
            match.group(2) or match.group(3)
        )
        body_lines.append("")
    body = "\n".join(body_lines)
    targets: list[str] = []
    index = 0
    while index < len(body):
        if body[index] != "[" or (index > 0 and body[index - 1] == "\\"):
            index += 1
            continue
        label_end = _find_markdown_closer(body, index + 1, "[", "]")
        if label_end == -1:
            index += 1
            continue
        label = body[index + 1 : label_end]
        cursor = label_end + 1
        while cursor < len(body) and body[cursor] in " \t\n":
            cursor += 1
        if cursor < len(body) and body[cursor] == "(":
            destination_end = _find_markdown_closer(body, cursor + 1, "(", ")")
            if destination_end != -1:
                destination = _inline_destination(body[cursor + 1 : destination_end])
                if destination is not None:
                    targets.append(destination)
                index = destination_end + 1
                continue
        if cursor < len(body) and body[cursor] == "[":
            reference_end = _find_markdown_closer(body, cursor + 1, "[", "]")
            if reference_end != -1:
                reference = body[cursor + 1 : reference_end] or label
                target = definitions.get(_normalize_reference_label(reference))
                if target is not None:
                    targets.append(target)
                index = reference_end + 1
                continue
        shortcut = definitions.get(_normalize_reference_label(label))
        if shortcut is not None:
            targets.append(shortcut)
        index = label_end + 1

    html_links = _HTMLLinks()
    try:
        html_links.feed(body)
    except (ValueError, RecursionError):
        pass
    targets.extend(html_links.targets)
    targets.extend(
        target
        for match in RENDERED_URL.finditer(body)
        if (target := _trim_rendered_url(match.group(0)))
    )
    return list(dict.fromkeys(targets))


def _eebus_link_target(
    target: str, docs_eebus_ref: str
) -> tuple[str | None, bool]:
    decoded = urllib.parse.unquote(target)
    parsed = urllib.parse.urlsplit(decoded)
    hostname = (parsed.hostname or "").casefold()
    if hostname in {"github.com", "www.github.com"}:
        parts = parsed.path.strip("/").split("/")
        folded = [part.casefold() for part in parts]
        if len(parts) >= 6 and folded[:3] == [
            "project-helianthus",
            "helianthus-docs-eebus",
            "blob",
        ]:
            ref = parts[3]
            relative = "/".join(parts[4:])
            valid = (
                IMMUTABLE_REF.fullmatch(ref) is not None
                and ref.casefold() == docs_eebus_ref.casefold()
                and _portable_path(relative)
            )
            return relative, valid
        if "helianthus-docs-eebus" in folded:
            return "", False
    if hostname == "raw.githubusercontent.com":
        parts = parsed.path.strip("/").split("/")
        folded = [part.casefold() for part in parts]
        if len(parts) >= 4 and folded[:2] == [
            "project-helianthus",
            "helianthus-docs-eebus",
        ]:
            ref = parts[2]
            relative = "/".join(parts[3:])
            valid = (
                IMMUTABLE_REF.fullmatch(ref) is not None
                and ref.casefold() == docs_eebus_ref.casefold()
                and _portable_path(relative)
            )
            return relative, valid
    repository = "helianthus-docs-eebus/"
    repository_index = decoded.casefold().find(repository)
    if repository_index >= 0 and (
        repository_index == 0 or decoded[repository_index - 1] == "/"
    ):
        relative = decoded[repository_index + len(repository) :].split("#", 1)[0]
        return relative, False
    return None, True


def _link_categories(
    docs_ebus_root: pathlib.Path,
    docs_eebus_root: pathlib.Path,
    docs_eebus_ref: str,
    manifest: dict[str, Any],
) -> set[str]:
    active_targets = {
        entry["owner"]["path"]
        for entry in manifest["entries"]
        if entry["owner"]["repository"] == "helianthus-docs-eebus"
        and entry["state"] == "active"
    }
    for _, text in _platform_markdown(docs_ebus_root):
        for target in _markdown_links(text):
            relative, immutable = _eebus_link_target(target, docs_eebus_ref)
            if relative is None:
                continue
            if (
                not immutable
                or relative not in active_targets
                or _artifact_kind(docs_eebus_root, relative) != "regular"
            ):
                return {"link.forward"}
    return set()


def _semantic_sections(text: str) -> list[tuple[str, str, bool]]:
    headings: dict[int, str] = {}
    sections: list[tuple[str, str, bool]] = []
    paragraph: list[str] = []
    non_normative_lead = False

    def flush() -> None:
        nonlocal non_normative_lead
        compact = " ".join(" ".join(paragraph).split())
        quoted = bool(paragraph) and all(
            line.lstrip().startswith(">") for line in paragraph
        )
        paragraph.clear()
        if not compact:
            return
        heading_context = " ".join(headings[level] for level in sorted(headings))
        explicitly_non_normative = (
            NON_NORMATIVE.search(compact) is not None
            or any(NON_NORMATIVE.search(heading) for heading in headings.values())
            or non_normative_lead
            or quoted
        )
        sections.append((heading_context, compact, explicitly_non_normative))
        non_normative_lead = NON_NORMATIVE_LEAD.search(compact) is not None

    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        atx = ATX_HEADING.match(line)
        setext = (
            SETEXT_HEADING.match(lines[index + 1])
            if line.strip() and index + 1 < len(lines)
            else None
        )
        if atx is not None or setext is not None:
            flush()
            non_normative_lead = False
            if atx is not None:
                level = len(atx.group(1))
                heading = atx.group(2).strip()
            else:
                assert setext is not None
                level = 1 if setext.group(1).startswith("=") else 2
                heading = line.strip()
                index += 1
            headings = {
                current_level: current_heading
                for current_level, current_heading in headings.items()
                if current_level < level
            }
            headings[level] = heading
        elif not line.strip():
            flush()
        else:
            paragraph.append(line)
        index += 1
    flush()
    return sections


def _documentation_ownership_summary(paragraph: str) -> bool:
    return DOCUMENTATION_OWNERSHIP.search(paragraph) is not None


def _platform_governance_summary(heading_context: str, paragraph: str) -> bool:
    governance = bool(
        PLATFORM_GOVERNANCE_CONTEXT.search(heading_context)
        and PLATFORM_GOVERNANCE_PROSE.search(paragraph)
        and PLATFORM_GOVERNANCE_ACTION.search(paragraph)
    )
    if not governance:
        return False
    has_owned_behavior = bool(
        PROTOCOL_BEHAVIOR.search(paragraph)
        or ARCHITECTURE_BEHAVIOR.search(paragraph)
        or API_BEHAVIOR.search(paragraph)
    )
    return bool(
        not has_owned_behavior
        or GOVERNANCE_COMPLEMENT.search(paragraph)
        or NEGATIVE_GOVERNANCE_CLAIM.search(paragraph)
    )


def _predicate_units(clause: str) -> list[tuple[str, bool]]:
    """Return predicate-local text and whether a leading modal is inherited."""

    return [
        (part.strip(), False)
        for part in EXPLICIT_PREDICATE_BOUNDARY.split(clause)
        if part.strip()
    ]


def _prohibited_clause_categories(
    heading_context: str, clause: str, *, inherited_normative: bool = False
) -> set[str]:
    if not inherited_normative and NORMATIVE.search(clause) is None:
        return set()
    contextual = " ".join(part for part in (heading_context, clause) if part)
    categories: set[str] = set()
    if PROTOCOL_CONTEXT.search(contextual) and PROTOCOL_BEHAVIOR.search(clause):
        categories.add("ownership.protocol-copy")
    if ARCHITECTURE_CONTEXT.search(
        contextual
    ) and ARCHITECTURE_BEHAVIOR.search(clause):
        categories.add("ownership.architecture-copy")
    if API_CONTEXT.search(contextual) and API_BEHAVIOR.search(clause):
        categories.add("ownership.api-copy")
    return categories


def _semantic_copy_categories(text: str) -> set[str]:
    categories: set[str] = set()
    clean = _strip_markdown_code(text)
    for heading_context, paragraph, explicitly_non_normative in _semantic_sections(
        clean
    ):
        contextual = " ".join(part for part in (heading_context, paragraph) if part)
        if GO_DECLARATION.search(paragraph) and re.search(
            r"\b(?:eebus|SHIP|SPINE)\b", contextual, re.I
        ) and not explicitly_non_normative:
            categories.add("ownership.api-copy")
        for clause in CLAUSE_BOUNDARY.split(paragraph):
            for predicate, inherited_normative in _predicate_units(clause):
                prohibited = _prohibited_clause_categories(
                    heading_context,
                    predicate,
                    inherited_normative=inherited_normative,
                )
                if not prohibited:
                    continue
                if (
                    explicitly_non_normative
                    or _documentation_ownership_summary(predicate)
                    or _platform_governance_summary(heading_context, predicate)
                ):
                    continue
                categories.update(prohibited)
    return categories


def _ownership_copy_categories(docs_ebus_root: pathlib.Path) -> set[str]:
    categories: set[str] = set()
    for _, text in _platform_markdown(docs_ebus_root):
        categories.update(_semantic_copy_categories(text))
    return categories


def _code_repo_categories(
    manifest: dict[str, Any],
    roots: Mapping[str, pathlib.Path],
    enforce_through: str,
) -> set[str]:
    if MILESTONE_INDEX[enforce_through] < MILESTONE_INDEX["MSP-DOCS-CLEAN"]:
        return set()
    categories: set[str] = set()
    for entry in manifest["entries"]:
        if entry["surface"] == "code_repo" and entry["state"] == "withdrawn":
            owner_root = roots.get(entry["owner"]["repository"])
            if owner_root is not None and _artifact_kind(
                owner_root, entry["owner"]["path"]
            ) != "missing":
                categories.add("ownership.code-repo-substantive")
        if entry["surface"] != "summary_only" or entry["state"] != "active":
            continue
        owner_root = roots.get(entry["owner"]["repository"])
        if owner_root is None:
            continue
        raw = _read_regular_artifact(owner_root, entry["owner"]["path"])
        if raw is None:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeError:
            categories.add("ownership.summary-only-substantive")
            continue
        prose = _strip_markdown_code(text)
        nonblank_lines = [line for line in text.splitlines() if line.strip()]
        if (
            NORMATIVE.search(prose)
            or len(nonblank_lines) > 12
            or re.search(r"(?m)^##\s+", prose)
            or _semantic_copy_categories(prose)
        ):
            categories.add("ownership.summary-only-substantive")
    return categories


def _privacy_categories(root: pathlib.Path) -> set[str]:
    for _, text in _platform_markdown(root):
        if PRIVATE_IDENTIFIER.search(text) or _contains_private_network(text):
            return {"privacy.private-identifier"}
    return set()


def _version_tuple(value: str | None) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    match = VERSION.fullmatch(value)
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _actual_tool_versions() -> tuple[tuple[int, int, int], str | None, str | None]:
    python = tuple(sys.version_info[:3])
    try:
        distribution = importlib.metadata.version("PyYAML")
    except importlib.metadata.PackageNotFoundError:
        distribution = None
    module = getattr(yaml, "__version__", None)
    return python, distribution, module


def _toolchain_categories(mode: str) -> set[str]:
    if mode not in TOOLCHAIN_MODES:
        return {"toolchain.mode"}
    python, pyyaml_distribution, pyyaml_module = _actual_tool_versions()
    categories: set[str] = set()
    if mode == "exact":
        if python != EXACT_PYTHON:
            categories.add("toolchain.python")
        if (
            pyyaml_distribution != EXACT_PYYAML
            or pyyaml_module != EXACT_PYYAML
        ):
            categories.add("toolchain.pyyaml")
        return categories

    if not (SUPPORTED_PYTHON_MIN <= python < SUPPORTED_PYTHON_MAX):
        categories.add("toolchain.python")
    parsed_pyyaml = _version_tuple(pyyaml_distribution)
    if (
        parsed_pyyaml is None
        or not (SUPPORTED_PYYAML_MIN <= parsed_pyyaml < SUPPORTED_PYYAML_MAX)
        or pyyaml_distribution != pyyaml_module
    ):
        categories.add("toolchain.pyyaml")
    return categories


def _validated_manifest(root: pathlib.Path) -> tuple[dict[str, Any] | None, set[str]]:
    manifest, error = _load_manifest(root)
    if error is not None:
        return None, {error}
    assert manifest is not None
    if not _schema_valid(manifest):
        return None, {"manifest.schema"}
    return manifest, _manifest_categories(manifest)


def _history_categories(
    manifest: dict[str, Any], prior_manifest_path: pathlib.Path | None
) -> set[str]:
    if prior_manifest_path is None:
        return set()
    prior = _parse_manifest_path(pathlib.Path(prior_manifest_path))
    if prior is None or not _schema_valid(prior):
        return {"history.prior-manifest"}
    prior_errors = _manifest_categories(prior)
    prior_errors.update(_state_categories(prior, {}))
    if prior_errors:
        return {"history.prior-manifest"}

    categories: set[str] = set()
    current_by_id = {entry["id"]: entry for entry in manifest["entries"]}
    for prior_entry in prior["entries"]:
        if prior_entry["state"] != "withdrawn":
            continue
        current_entry = current_by_id.get(prior_entry["id"])
        if current_entry is None or current_entry["state"] != "withdrawn":
            categories.add("history.withdrawn-terminal")
            continue
        if any(
            current_entry[field] != prior_entry[field]
            for field in TOMBSTONE_IMMUTABLE_FIELDS
        ):
            categories.add("history.tombstone-identity")
    return categories


def validate_repository(
    *,
    docs_ebus_root: pathlib.Path,
    mode: str,
    enforce_through: str,
    toolchain_mode: str,
    prior_manifest: pathlib.Path | None = None,
    evaluated_at: str | None = None,
    evaluation_source: str | None = None,
) -> list[str]:
    root = pathlib.Path(docs_ebus_root)
    categories = _toolchain_categories(toolchain_mode)
    root_valid = _repository_root_valid(root, "helianthus-docs-ebus")
    if not root_valid:
        categories.add("input.repository-root")
    manifest, manifest_categories = _validated_manifest(root)
    categories.update(manifest_categories)
    if manifest is None:
        return _result(categories)
    categories.update(_history_categories(manifest, prior_manifest))
    categories.update(_enforcement_categories(manifest, enforce_through))
    roots = {"helianthus-docs-ebus": root} if root_valid else {}
    categories.update(_state_categories(manifest, roots))
    categories.update(_artifact_categories(manifest, roots))
    categories.update(_ownership_copy_categories(root))
    categories.update(_privacy_categories(root))
    if mode == "main-expiry":
        categories.update(_expiry_categories(manifest, evaluated_at, evaluation_source))
    elif mode != "repository":
        categories.add("input.mode")
    return _result(categories)


def validate_workspace(
    *,
    docs_ebus_root: pathlib.Path,
    docs_eebus_root: pathlib.Path,
    eebusreg_root: pathlib.Path,
    mode: str,
    docs_ebus_ref: str | None,
    docs_eebus_ref: str | None,
    eebusreg_ref: str | None,
    enforce_through: str,
    toolchain_mode: str,
    prior_manifest: pathlib.Path | None = None,
) -> list[str]:
    roots = {
        "helianthus-docs-ebus": pathlib.Path(docs_ebus_root),
        "helianthus-docs-eebus": pathlib.Path(docs_eebus_root),
        "helianthus-eebusreg": pathlib.Path(eebusreg_root),
    }
    refs = {
        "helianthus-docs-ebus": docs_ebus_ref,
        "helianthus-docs-eebus": docs_eebus_ref,
        "helianthus-eebusreg": eebusreg_ref,
    }
    ref_categories = {
        "helianthus-docs-ebus": "input.docs-ebus-ref",
        "helianthus-docs-eebus": "input.docs-eebus-ref",
        "helianthus-eebusreg": "input.eebusreg-ref",
    }
    categories = _toolchain_categories(toolchain_mode)
    if mode != "combined-ref":
        categories.add("input.mode")
    for repository, root in roots.items():
        if not _checkout_matches_ref(root, refs[repository]):
            categories.add(ref_categories[repository])
    if any(not _clean_checkout(root) for root in roots.values()):
        categories.add("input.clean-clone")

    valid_roots: dict[str, pathlib.Path] = {}
    resolved: set[pathlib.Path] = set()
    for repository, root in roots.items():
        if not _repository_root_valid(root, repository):
            categories.add("input.repository-root")
            continue
        resolved_root = root.resolve(strict=True)
        if resolved_root in resolved:
            categories.add("input.repository-root")
            continue
        resolved.add(resolved_root)
        valid_roots[repository] = root

    manifest, manifest_categories = _validated_manifest(roots["helianthus-docs-ebus"])
    categories.update(manifest_categories)
    if manifest is None:
        return _result(categories)
    categories.update(_history_categories(manifest, prior_manifest))
    categories.update(_enforcement_categories(manifest, enforce_through))
    categories.update(_state_categories(manifest, valid_roots))
    categories.update(_artifact_categories(manifest, valid_roots))
    categories.update(_ownership_copy_categories(roots["helianthus-docs-ebus"]))
    categories.update(_code_repo_categories(manifest, valid_roots, enforce_through))
    categories.update(_privacy_categories(roots["helianthus-docs-ebus"]))
    if (
        "helianthus-docs-eebus" in valid_roots
        and isinstance(docs_eebus_ref, str)
        and IMMUTABLE_REF.fullmatch(docs_eebus_ref) is not None
    ):
        categories.update(
            _link_categories(
                roots["helianthus-docs-ebus"],
                roots["helianthus-docs-eebus"],
                docs_eebus_ref,
                manifest,
            )
        )
    return _result(categories)


class _CategoryParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _CategoryParser(add_help=True)
    parser.add_argument(
        "--mode",
        default="repository",
        choices=("repository", "combined-ref", "main-expiry"),
    )
    parser.add_argument("--docs-ebus-root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--docs-eebus-root", type=pathlib.Path)
    parser.add_argument("--eebusreg-root", type=pathlib.Path)
    parser.add_argument("--docs-ebus-ref")
    parser.add_argument("--docs-eebus-ref")
    parser.add_argument("--eebusreg-ref")
    parser.add_argument("--evaluated-at")
    parser.add_argument("--evaluation-source")
    parser.add_argument("--prior-manifest", type=pathlib.Path)
    parser.add_argument("--enforce-through", required=True, choices=MILESTONES)
    parser.add_argument(
        "--toolchain-mode", default="exact", choices=tuple(sorted(TOOLCHAIN_MODES))
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mode in {"repository", "main-expiry"}:
        diagnostics = validate_repository(
            docs_ebus_root=args.docs_ebus_root,
            mode=args.mode,
            enforce_through=args.enforce_through,
            toolchain_mode=args.toolchain_mode,
            prior_manifest=args.prior_manifest,
            evaluated_at=args.evaluated_at,
            evaluation_source=args.evaluation_source,
        )
    elif args.docs_eebus_root is None or args.eebusreg_root is None:
        diagnostics = ["input.roots"]
    else:
        diagnostics = validate_workspace(
            docs_ebus_root=args.docs_ebus_root,
            docs_eebus_root=args.docs_eebus_root,
            eebusreg_root=args.eebusreg_root,
            mode=args.mode,
            docs_ebus_ref=args.docs_ebus_ref,
            docs_eebus_ref=args.docs_eebus_ref,
            eebusreg_ref=args.eebusreg_ref,
            enforce_through=args.enforce_through,
            toolchain_mode=args.toolchain_mode,
            prior_manifest=args.prior_manifest,
        )
    for diagnostic in diagnostics:
        print(diagnostic)
    return 1 if diagnostics else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(1) from None
    except (
        OSError,
        ValueError,
        yaml.YAMLError,
        RecursionError,
        MemoryError,
        OverflowError,
    ):
        print("input.arguments")
        raise SystemExit(1) from None
