#!/usr/bin/env python3
"""Validate the closed cross-runtime documentation ownership contract."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import pathlib
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

import yaml


MANIFEST = pathlib.Path("docs/platform/manifests/eebus-doc-ownership.yaml")
SURFACES = {
    "protocol",
    "architecture",
    "api",
    "platform",
    "code_repo",
    "summary_only",
}
STATES = {"planned", "candidate", "active", "withdrawn"}
PINNED_TOOLS = {"python": "3.12.10", "pyyaml": "6.0.2"}
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
STABLE_OUTPUTS = OUTPUT_FIELDS - {"candidate"}
IMMUTABLE_REF = re.compile(r"[0-9a-fA-F]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
ENTRY_ID = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
MARKDOWN_LINK = re.compile(r"(?:\[[^]]*\]\(|href=[\"'])([^)\"'\s]+)")
PRIVATE_IDENTIFIER = re.compile(
    r"(?i)(?:serial|ski|mac|peer[_-]?id|device[_-]?id|token|password|secret)\s*="
)
WINDOWS_ABSOLUTE = re.compile(r"[A-Za-z]:[\\/]")
NORMATIVE = re.compile(r"\b(?:must|shall|required|acceptance criteria)\b", re.I)


def _result(categories: Iterable[str]) -> list[str]:
    return sorted(set(categories))


def _run_git(root: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _clean_checkout(root: pathlib.Path) -> bool:
    if not root.is_dir():
        return False
    inside = _run_git(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return False
    status = _run_git(root, "status", "--porcelain=v1", "--untracked-files=all")
    return status.returncode == 0 and not status.stdout


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


def _load_manifest(root: pathlib.Path) -> tuple[dict[str, Any] | None, str | None]:
    path = root / MANIFEST
    if not path.is_file() or path.is_symlink():
        return None, "manifest.missing"
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        return None, "manifest.schema"
    if not isinstance(loaded, dict):
        return None, "manifest.schema"
    return loaded, None


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
        if (
            not isinstance(entry_id, str)
            or not entry_id
            or ENTRY_ID.fullmatch(entry_id) is None
            or entry_id in ids
            or not isinstance(entry.get("surface"), str)
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
                or any(
                    not isinstance(location.get(key), str) or not location.get(key)
                    for key in LOCATION_FIELDS
                )
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
        if not isinstance(lifecycle.get("created_at"), str):
            return False
        if any(
            not _optional_text(lifecycle.get(key))
            for key in LIFECYCLE_FIELDS - {"created_at", "cleanup_required"}
        ):
            return False
        if not isinstance(lifecycle.get("cleanup_required"), bool):
            return False
    return True


def _parse_instant(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        return None
    return parsed.astimezone(timezone.utc)


def _portable_path(value: str) -> bool:
    path = pathlib.PurePosixPath(value)
    return (
        bool(value)
        and not value.startswith(("/", "~"))
        and not value.startswith("./")
        and WINDOWS_ABSOLUTE.match(value) is None
        and "\\" not in value
        and "//" not in value
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def _all_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _all_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_strings(item)


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

    entries = manifest["entries"]
    if {entry["surface"] for entry in entries} != SURFACES:
        categories.add("ownership.surface-missing")

    pairs: set[tuple[str, str, str, str]] = set()
    canonical_owners: set[tuple[str, str]] = set()
    for entry in entries:
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

    if any(
        PRIVATE_IDENTIFIER.search(value) or _contains_private_network(value)
        for value in _all_strings(manifest)
    ):
        categories.add("privacy.private-identifier")
    return categories


def _state_categories(
    manifest: dict[str, Any], roots: Mapping[str, pathlib.Path] | None
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
            hidden = "_candidate" in pathlib.PurePosixPath(entry["owner"]["path"]).parts
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
            if not invalid and roots is not None:
                source_root = roots.get(entry["source"]["repository"])
                if source_root is None:
                    invalid = True
                else:
                    shown = _run_git(
                        source_root,
                        "show",
                        f"{source_ref}:{entry['source']['path']}",
                    )
                    invalid = shown.returncode != 0 or hashlib.sha256(
                        shown.stdout.encode("utf-8")
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
            if not invalid and roots is not None:
                owner_root = roots.get(entry["owner"]["repository"])
                owner_path = entry["owner"]["path"]
                if _portable_path(owner_path):
                    invalid = (
                        owner_root is None
                        or not (owner_root / owner_path).exists()
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
            if (
                not invalid
                and roots is not None
                and entry["surface"] != "code_repo"
                and _portable_path(entry["owner"]["path"])
            ):
                owner_root = roots.get(entry["owner"]["repository"])
                invalid = owner_root is not None and (
                    owner_root / entry["owner"]["path"]
                ).exists()
            if invalid:
                categories.add("state.withdrawn")
    return categories


def _expiry_categories(
    manifest: dict[str, Any], evaluated_at: str | None, evaluation_source: str | None
) -> set[str]:
    if not evaluation_source:
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


def _platform_markdown(root: pathlib.Path) -> Iterable[tuple[pathlib.Path, str]]:
    platform = root / "docs/platform"
    if not platform.is_dir():
        return
    for path in sorted(platform.rglob("*.md")):
        if path.is_file() and not path.is_symlink():
            try:
                yield path, path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue


def _link_categories(
    docs_ebus_root: pathlib.Path,
    docs_eebus_root: pathlib.Path,
    manifest: dict[str, Any],
) -> set[str]:
    active_targets = {
        entry["owner"]["path"]
        for entry in manifest["entries"]
        if entry["owner"]["repository"] == "helianthus-docs-eebus"
        and entry["state"] == "active"
    }
    for _, text in _platform_markdown(docs_ebus_root):
        for match in MARKDOWN_LINK.finditer(text):
            target = match.group(1)
            marker = "helianthus-docs-eebus/"
            if marker not in target:
                continue
            relative = target.split(marker, 1)[1].split("#", 1)[0]
            if relative.startswith("blob/"):
                parts = relative.split("/", 2)
                relative = parts[2] if len(parts) == 3 else ""
            if relative not in active_targets or not (docs_eebus_root / relative).is_file():
                return {"link.forward"}
    return set()


def _ownership_copy_categories(docs_ebus_root: pathlib.Path) -> set[str]:
    categories: set[str] = set()
    for _, text in _platform_markdown(docs_ebus_root):
        normative = NORMATIVE.search(text) is not None
        if normative and re.search(
            r"(?im)^#\s+.*SHIP.*SPINE.*(?:Protocol|Behavior).*$", text
        ):
            categories.add("ownership.protocol-copy")
        if normative and re.search(
            r"(?im)^#\s+eeBUS (?:Runtime|Trust|Persistence|Lifecycle|Architecture)\b",
            text,
        ):
            categories.add("ownership.architecture-copy")
        if re.search(r"(?im)^#\s+.*eeBUS.*Go API.*$", text) and re.search(
            r"(?m)\bfunc\s+[A-Z]|schema", text
        ):
            categories.add("ownership.api-copy")
    return categories


def _code_repo_categories(
    manifest: dict[str, Any], roots: Mapping[str, pathlib.Path]
) -> set[str]:
    categories: set[str] = set()
    eebusreg = roots.get("helianthus-eebusreg")
    if eebusreg is None:
        return categories

    docs = eebusreg / "docs"
    if docs.exists() and any(path.is_file() or path.is_symlink() for path in docs.rglob("*")):
        categories.add("ownership.code-repo-substantive")

    for entry in manifest["entries"]:
        if entry["surface"] != "summary_only":
            continue
        owner_root = roots.get(entry["owner"]["repository"])
        if owner_root is None:
            continue
        path = owner_root / entry["owner"]["path"]
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        nonblank_lines = [line for line in text.splitlines() if line.strip()]
        if (
            NORMATIVE.search(text)
            or len(nonblank_lines) > 12
            or "```" in text
            or re.search(r"(?m)^##\s+", text)
        ):
            categories.add("ownership.summary-only-substantive")
    return categories


def _privacy_categories(root: pathlib.Path) -> set[str]:
    for _, text in _platform_markdown(root):
        if PRIVATE_IDENTIFIER.search(text) or _contains_private_network(text):
            return {"privacy.private-identifier"}
    return set()


def _validated_manifest(root: pathlib.Path) -> tuple[dict[str, Any] | None, set[str]]:
    manifest, error = _load_manifest(root)
    if error is not None:
        return None, {error}
    assert manifest is not None
    if not _schema_valid(manifest):
        return None, {"manifest.schema"}
    return manifest, _manifest_categories(manifest)


def validate_repository(
    *,
    docs_ebus_root: pathlib.Path,
    mode: str = "repository",
    evaluated_at: str | None = None,
    evaluation_source: str | None = None,
    pinned_tools: Mapping[str, str] | None = None,
) -> list[str]:
    categories: set[str] = set()
    if dict(pinned_tools or {}) != PINNED_TOOLS:
        categories.add("input.pinned-tools")
    manifest, manifest_categories = _validated_manifest(pathlib.Path(docs_ebus_root))
    categories.update(manifest_categories)
    if manifest is None:
        return _result(categories)
    categories.update(_state_categories(manifest, None))
    categories.update(_ownership_copy_categories(pathlib.Path(docs_ebus_root)))
    categories.update(_privacy_categories(pathlib.Path(docs_ebus_root)))
    if mode == "main-expiry":
        categories.update(_expiry_categories(manifest, evaluated_at, evaluation_source))
    return _result(categories)


def validate_workspace(
    *,
    docs_ebus_root: pathlib.Path,
    docs_eebus_root: pathlib.Path,
    eebusreg_root: pathlib.Path,
    mode: str,
    docs_ebus_ref: str | None,
    docs_eebus_ref: str | None,
    evaluated_at: str | None,
    evaluation_source: str | None,
    pinned_tools: Mapping[str, str] | None,
) -> list[str]:
    docs_ebus_root = pathlib.Path(docs_ebus_root)
    docs_eebus_root = pathlib.Path(docs_eebus_root)
    eebusreg_root = pathlib.Path(eebusreg_root)
    categories: set[str] = set()

    if dict(pinned_tools or {}) != PINNED_TOOLS:
        categories.add("input.pinned-tools")
    if not _checkout_matches_ref(docs_ebus_root, docs_ebus_ref):
        categories.add("input.docs-ebus-ref")
    if not _checkout_matches_ref(docs_eebus_root, docs_eebus_ref):
        categories.add("input.docs-eebus-ref")
    if any(
        not _clean_checkout(root)
        for root in (docs_ebus_root, docs_eebus_root, eebusreg_root)
    ):
        categories.add("input.clean-clone")

    manifest, manifest_categories = _validated_manifest(docs_ebus_root)
    categories.update(manifest_categories)
    if manifest is None:
        return _result(categories)

    roots = {
        "helianthus-docs-ebus": docs_ebus_root,
        "helianthus-docs-eebus": docs_eebus_root,
        "helianthus-eebusreg": eebusreg_root,
    }
    categories.update(_state_categories(manifest, roots))
    categories.update(_ownership_copy_categories(docs_ebus_root))
    categories.update(_code_repo_categories(manifest, roots))
    categories.update(_privacy_categories(docs_ebus_root))
    categories.update(_link_categories(docs_ebus_root, docs_eebus_root, manifest))
    if mode in {"main", "main-expiry"}:
        categories.update(_expiry_categories(manifest, evaluated_at, evaluation_source))
    return _result(categories)


def _parse_pins(values: list[str]) -> dict[str, str]:
    pins: dict[str, str] = {}
    for value in values:
        if value.count("=") != 1:
            return {}
        key, version = value.split("=", 1)
        if not key or not version or key in pins:
            return {}
        pins[key] = version
    return pins


class _CategoryParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _CategoryParser(add_help=True)
    parser.add_argument(
        "--mode",
        default="repository",
        choices=("repository", "combined-ref", "main-expiry", "pr", "main"),
    )
    parser.add_argument("--docs-ebus-root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--docs-eebus-root", type=pathlib.Path)
    parser.add_argument("--eebusreg-root", type=pathlib.Path)
    parser.add_argument("--docs-ebus-ref")
    parser.add_argument("--docs-eebus-ref")
    parser.add_argument("--eebusreg-ref")
    parser.add_argument("--evaluated-at")
    parser.add_argument("--evaluation-source")
    parser.add_argument("--pinned-tool", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    pins = _parse_pins(args.pinned_tool)
    if args.mode in {"repository", "main-expiry"} and args.docs_eebus_root is None:
        diagnostics = validate_repository(
            docs_ebus_root=args.docs_ebus_root,
            mode=args.mode,
            evaluated_at=args.evaluated_at,
            evaluation_source=args.evaluation_source,
            pinned_tools=pins,
        )
    else:
        if args.docs_eebus_root is None or args.eebusreg_root is None:
            diagnostics = ["input.roots"]
        else:
            diagnostics = validate_workspace(
                docs_ebus_root=args.docs_ebus_root,
                docs_eebus_root=args.docs_eebus_root,
                eebusreg_root=args.eebusreg_root,
                mode=args.mode,
                docs_ebus_ref=args.docs_ebus_ref,
                docs_eebus_ref=args.docs_eebus_ref,
                evaluated_at=args.evaluated_at,
                evaluation_source=args.evaluation_source,
                pinned_tools=pins,
            )
            if args.mode == "combined-ref":
                if not _checkout_matches_ref(args.eebusreg_root, args.eebusreg_ref):
                    diagnostics = _result([*diagnostics, "input.eebusreg-ref"])
    for diagnostic in diagnostics:
        print(diagnostic)
    return 1 if diagnostics else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(1) from None
    except (OSError, ValueError, yaml.YAMLError):
        print("input.arguments")
        raise SystemExit(1) from None
