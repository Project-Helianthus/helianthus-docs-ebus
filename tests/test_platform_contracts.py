from __future__ import annotations

import copy
import hashlib
import importlib.util
import os
import pathlib
import subprocess
from dataclasses import dataclass
from typing import Any, Callable

import pytest
import yaml


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "scripts/validate_platform_contracts.py"
MANIFEST_PATH = pathlib.Path("docs/platform/manifests/eebus-doc-ownership.yaml")
PLATFORM_STAGE = "MSP-DOCS-PLATFORM"
E2_STAGE = "MSP-DOCS-E2"
CLEAN_STAGE = "MSP-DOCS-CLEAN"
CONTRACT_PAGES = (
    pathlib.Path("docs/platform/cross-runtime-envelope.md"),
    pathlib.Path("docs/platform/hash-auth-binding.md"),
    pathlib.Path("docs/platform/shared-registry-boundary.md"),
    pathlib.Path("docs/platform/promotion-and-consumer-contract.md"),
    pathlib.Path("docs/platform/ownership-validation.md"),
)
PAGE_REQUIRED_TERMS = {
    pathlib.Path("docs/platform/cross-runtime-envelope.md"): (
        "language-neutral",
        "version",
        "envelope",
        "runtime",
    ),
    pathlib.Path("docs/platform/hash-auth-binding.md"): (
        "RFC 8785",
        "hash",
        "auth",
        "scope",
    ),
    pathlib.Path("docs/platform/shared-registry-boundary.md"): (
        "protocol-neutral",
        "registry",
        "canonical",
    ),
    pathlib.Path("docs/platform/promotion-and-consumer-contract.md"): (
        "per-leaf",
        "GraphQL",
        "Portal",
        "Home Assistant",
    ),
    pathlib.Path("docs/platform/ownership-validation.md"): (
        "current PR head SHA",
        "clean root",
        "actual Python runtime",
        "supported",
        "actionlint `v1.7.7`",
        "jv v0.7.0",
        "six decimal digits",
        "inclusive",
    ),
}
SURFACES = {
    "protocol",
    "architecture",
    "api",
    "platform",
    "code_repo",
    "summary_only",
}


def lifecycle(
    *,
    created_at: str,
    expires_at: str | None = None,
    source_issue: str | None = None,
    source_pr: str | None = None,
    source_ref: str | None = None,
    content_sha256: str | None = None,
    approved_at: str | None = None,
    frozen_at: str | None = None,
    cleanup_required: bool = False,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "expires_at": expires_at,
        "source_issue": source_issue,
        "source_pr": source_pr,
        "source_ref": source_ref,
        "content_sha256": content_sha256,
        "approved_at": approved_at,
        "frozen_at": frozen_at,
        "cleanup_required": cleanup_required,
    }


def outputs(*, candidate: bool = False, stable: bool = False) -> dict[str, bool]:
    return {
        "candidate": candidate,
        "stable_navigation": stable,
        "search": stable,
        "sitemap": stable,
        "versioned_bundle": stable,
        "release_bundle": stable,
    }


def enforcement(milestone: str, required_state: str) -> dict[str, str]:
    return {"milestone": milestone, "required_state": required_state}


def entry(
    entry_id: str,
    surface: str,
    owner_repo: str,
    owner_path: str,
    source_repo: str,
    source_path: str,
    state: str,
    *,
    canonical: bool,
    output: dict[str, bool],
    state_lifecycle: dict[str, Any],
    state_enforcement: dict[str, str],
) -> dict[str, Any]:
    return {
        "id": entry_id,
        "surface": surface,
        "owner": {"repository": owner_repo, "path": owner_path},
        "source": {"repository": source_repo, "path": source_path},
        "canonical": canonical,
        "state": state,
        "outputs": output,
        "lifecycle": state_lifecycle,
        "enforcement": state_enforcement,
    }


def active_lifecycle() -> dict[str, Any]:
    return lifecycle(
        created_at="2026-01-01T00:00:00Z",
        approved_at="2026-01-02T00:00:00Z",
        frozen_at="2026-01-03T00:00:00Z",
    )


def base_manifest() -> dict[str, Any]:
    return {
        "schema": "helianthus.platform.doc-ownership",
        "version": 1,
        "entries": [
            entry(
                "eebus-protocol",
                "protocol",
                "helianthus-docs-eebus",
                "protocols/ship-spine.md",
                "helianthus-docs-eebus",
                "protocols/ship-spine.md",
                "active",
                canonical=True,
                output=outputs(stable=True),
                state_lifecycle=active_lifecycle(),
                state_enforcement=enforcement(
                    "MSP-DOCS-API-SCHEMA", "active"
                ),
            ),
            entry(
                "eebus-architecture-planned",
                "architecture",
                "helianthus-docs-eebus",
                "architecture/README.md",
                "helianthus-docs-eebus",
                "architecture/README.md",
                "planned",
                canonical=False,
                output=outputs(),
                state_lifecycle=lifecycle(
                    created_at="2026-01-01T00:00:00Z",
                    expires_at="2026-01-15T00:00:00Z",
                    source_issue="Project-Helianthus/helianthus-docs-eebus#8",
                ),
                state_enforcement=enforcement(E2_STAGE, "active"),
            ),
            entry(
                "eebus-api-candidate",
                "api",
                "helianthus-docs-eebus",
                "api/_candidate/lifecycle.md",
                "helianthus-eebusreg",
                "api/lifecycle.go",
                "candidate",
                canonical=False,
                output=outputs(candidate=True),
                state_lifecycle=lifecycle(
                    created_at="2026-01-15T00:00:00Z",
                    expires_at="2026-02-14T00:00:00Z",
                    source_pr="Project-Helianthus/helianthus-eebusreg#20",
                    source_ref="__SOURCE_REF__",
                    content_sha256=hashlib.sha256(b"package api\n").hexdigest(),
                ),
                state_enforcement=enforcement(E2_STAGE, "candidate"),
            ),
            entry(
                "platform-contracts",
                "platform",
                "helianthus-docs-ebus",
                "docs/platform/cross-runtime-envelope.md",
                "helianthus-docs-ebus",
                "docs/platform/cross-runtime-envelope.md",
                "active",
                canonical=True,
                output=outputs(stable=True),
                state_lifecycle=active_lifecycle(),
                state_enforcement=enforcement(PLATFORM_STAGE, "active"),
            ),
            entry(
                "code-repo-docs-planned",
                "code_repo",
                "helianthus-eebusreg",
                "docs",
                "helianthus-eebusreg",
                "docs",
                "planned",
                canonical=False,
                output=outputs(),
                state_lifecycle=lifecycle(
                    created_at="2026-01-01T00:00:00Z",
                    expires_at="2026-01-15T00:00:00Z",
                    source_issue="Project-Helianthus/helianthus-execution-plans#58",
                ),
                state_enforcement=enforcement(CLEAN_STAGE, "withdrawn"),
            ),
            entry(
                "code-repo-summary-planned",
                "summary_only",
                "helianthus-eebusreg",
                "README.md",
                "helianthus-docs-eebus",
                "README.md",
                "planned",
                canonical=False,
                output=outputs(),
                state_lifecycle=lifecycle(
                    created_at="2026-01-01T00:00:00Z",
                    expires_at="2026-01-15T00:00:00Z",
                    source_issue="Project-Helianthus/helianthus-execution-plans#58",
                ),
                state_enforcement=enforcement(CLEAN_STAGE, "active"),
            ),
        ],
    }


def base_spec() -> dict[str, Any]:
    platform_header = "Canonical source: this page.\n\n"
    return {
        "manifest": base_manifest(),
        "manifest_present": True,
        "docs_ebus": {
            "docs/platform/cross-runtime-envelope.md": platform_header
            + "# Cross-Runtime Envelope\n\nLanguage-neutral envelope rules.\n",
            "docs/platform/hash-auth-binding.md": platform_header
            + "# Hash And Auth Binding\n\nRFC 8785 hash and effective auth binding.\n",
            "docs/platform/shared-registry-boundary.md": platform_header
            + "# Shared Registry Boundary\n\nProtocol-neutral registry authority.\n",
            "docs/platform/promotion-and-consumer-contract.md": platform_header
            + "# Promotion And Consumer Contract\n\nPer-leaf promotion precedes GraphQL, Portal, and Home Assistant.\n",
            "docs/platform/ownership-validation.md": platform_header
            + "# Ownership Validation\n\nExact refs and clean roots.\n",
        },
        "docs_eebus": {
            "README.md": "# eeBUS Documentation\n",
            "protocols/ship-spine.md": "# SHIP/SPINE Protocol Ownership\n",
            "architecture/README.md": "# Architecture Ownership Landing\n",
            "api/_candidate/lifecycle.md": "# Candidate Go API\n",
        },
        "eebusreg": {
            "README.md": "# eeBUS Registry\n\n## Current Work\n\nThe runtime MUST keep this pre-CLEAN material.\n",
            "docs/legacy.md": "# Pre-CLEAN Runtime Notes\n",
            "api/lifecycle.go": "package api\n",
        },
        "symlinks": {"docs_ebus": {}, "docs_eebus": {}, "eebusreg": {}},
        "remotes": {
            "docs_ebus": "helianthus-docs-ebus",
            "docs_eebus": "helianthus-docs-eebus",
            "eebusreg": "helianthus-eebusreg",
        },
        "docs_ebus_ref": "__AUTO__",
        "docs_eebus_ref": "__AUTO__",
        "eebusreg_ref": "__AUTO__",
        "dirty_repo": None,
        "enforce_through": PLATFORM_STAGE,
        "toolchain_mode": "supported",
    }


def find_entry(spec: dict[str, Any], entry_id: str) -> dict[str, Any]:
    return next(item for item in spec["manifest"]["entries"] if item["id"] == entry_id)


def set_active(item: dict[str, Any], *, canonical: bool) -> None:
    item.update(
        {
            "state": "active",
            "canonical": canonical,
            "outputs": outputs(stable=True),
            "lifecycle": active_lifecycle(),
        }
    )


def transition_e2(spec: dict[str, Any]) -> None:
    set_active(find_entry(spec, "eebus-architecture-planned"), canonical=True)
    spec["enforce_through"] = E2_STAGE


def transition_clean(
    spec: dict[str, Any], *, remove_docs: bool = True, minimal_summary: bool = True
) -> None:
    transition_e2(spec)
    code = find_entry(spec, "code-repo-docs-planned")
    code.update(
        {
            "state": "withdrawn",
            "canonical": False,
            "outputs": outputs(),
            "lifecycle": lifecycle(
                created_at="2026-01-01T00:00:00Z",
                source_issue="Project-Helianthus/helianthus-execution-plans#58",
                cleanup_required=True,
            ),
        }
    )
    summary = find_entry(spec, "code-repo-summary-planned")
    set_active(summary, canonical=False)
    if remove_docs:
        spec["eebusreg"] = {
            path: text
            for path, text in spec["eebusreg"].items()
            if not path.startswith("docs/")
        }
    if minimal_summary:
        spec["eebusreg"]["README.md"] = (
            "# eeBUS Registry\n\n"
            "Canonical docs: Project-Helianthus/helianthus-docs-eebus.\n\n"
            "Build: `./scripts/ci_local.sh`.\n"
        )
    spec["enforce_through"] = CLEAN_STAGE


def write_files(root: pathlib.Path, files: dict[str, str]) -> None:
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def write_symlinks(root: pathlib.Path, links: dict[str, str]) -> None:
    for relative, target in links.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if target.startswith("ABS:"):
            target = str(root / target.removeprefix("ABS:"))
        os.symlink(target, path)


def commit_fixture(
    root: pathlib.Path, repository: str, *, remote_repository: str | None = None
) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    remote = remote_repository or repository
    subprocess.run(
        [
            "git",
            "remote",
            "add",
            "origin",
            f"https://github.com/Project-Helianthus/{remote}.git",
        ],
        cwd=root,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
        }
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Contract Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=root,
        check=True,
        env=env,
    )
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


@dataclass(frozen=True)
class Workspace:
    docs_ebus: pathlib.Path
    docs_eebus: pathlib.Path
    eebusreg: pathlib.Path
    docs_ebus_ref: str | None
    docs_eebus_ref: str | None
    eebusreg_ref: str | None
    enforce_through: str
    toolchain_mode: str


def build_workspace(
    tmp_path: pathlib.Path, mutate: Callable[[dict[str, Any]], None] | None = None
) -> Workspace:
    tmp_path.mkdir(parents=True, exist_ok=True)
    spec = base_spec()
    if mutate is not None:
        mutate(spec)

    eebusreg = tmp_path / "helianthus-eebusreg"
    eebusreg.mkdir()
    write_files(eebusreg, spec["eebusreg"])
    write_symlinks(eebusreg, spec["symlinks"]["eebusreg"])
    eebusreg_head = commit_fixture(
        eebusreg,
        "helianthus-eebusreg",
        remote_repository=spec["remotes"]["eebusreg"],
    )
    for item in spec["manifest"]["entries"]:
        if item["lifecycle"]["source_ref"] == "__SOURCE_REF__":
            item["lifecycle"]["source_ref"] = eebusreg_head

    docs_eebus = tmp_path / "helianthus-docs-eebus"
    docs_eebus.mkdir()
    write_files(docs_eebus, spec["docs_eebus"])
    write_symlinks(docs_eebus, spec["symlinks"]["docs_eebus"])
    docs_eebus_head = commit_fixture(
        docs_eebus,
        "helianthus-docs-eebus",
        remote_repository=spec["remotes"]["docs_eebus"],
    )

    docs_ebus = tmp_path / "helianthus-docs-ebus"
    docs_ebus.mkdir()
    docs_files = {
        path: text.replace("__DOCS_EEBUS_REF__", docs_eebus_head)
        for path, text in spec["docs_ebus"].items()
    }
    write_files(docs_ebus, docs_files)
    if spec["manifest_present"]:
        manifest_path = docs_ebus / MANIFEST_PATH
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            yaml.safe_dump(spec["manifest"], sort_keys=False), encoding="utf-8"
        )
    write_symlinks(docs_ebus, spec["symlinks"]["docs_ebus"])
    docs_ebus_head = commit_fixture(
        docs_ebus,
        "helianthus-docs-ebus",
        remote_repository=spec["remotes"]["docs_ebus"],
    )

    roots = {
        "docs_ebus": docs_ebus,
        "docs_eebus": docs_eebus,
        "eebusreg": eebusreg,
    }
    if spec["dirty_repo"] is not None:
        (roots[spec["dirty_repo"]] / "ambient-untracked.txt").write_text(
            "dirty\n", encoding="utf-8"
        )

    def selected(value: str | None, automatic: str) -> str | None:
        return automatic if value == "__AUTO__" else value

    return Workspace(
        docs_ebus=docs_ebus,
        docs_eebus=docs_eebus,
        eebusreg=eebusreg,
        docs_ebus_ref=selected(spec["docs_ebus_ref"], docs_ebus_head),
        docs_eebus_ref=selected(spec["docs_eebus_ref"], docs_eebus_head),
        eebusreg_ref=selected(spec["eebusreg_ref"], eebusreg_head),
        enforce_through=spec["enforce_through"],
        toolchain_mode=spec["toolchain_mode"],
    )


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "platform_contract_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate(validator: Any, workspace: Workspace) -> list[str]:
    diagnostics = validator.validate_workspace(
        docs_ebus_root=workspace.docs_ebus,
        docs_eebus_root=workspace.docs_eebus,
        eebusreg_root=workspace.eebusreg,
        mode="combined-ref",
        docs_ebus_ref=workspace.docs_ebus_ref,
        docs_eebus_ref=workspace.docs_eebus_ref,
        eebusreg_ref=workspace.eebusreg_ref,
        enforce_through=workspace.enforce_through,
        toolchain_mode=workspace.toolchain_mode,
    )
    assert diagnostics == sorted(set(diagnostics))
    assert all(
        isinstance(item, str) and item and " " not in item for item in diagnostics
    )
    return diagnostics


def repository_validate(
    validator: Any,
    root: pathlib.Path,
    *,
    mode: str = "repository",
    evaluated_at: str | None = None,
    evaluation_source: str | None = None,
) -> list[str]:
    return validator.validate_repository(
        docs_ebus_root=root,
        mode=mode,
        enforce_through=PLATFORM_STAGE,
        toolchain_mode="supported",
        evaluated_at=evaluated_at,
        evaluation_source=evaluation_source,
    )


@dataclass(frozen=True)
class NegativeCase:
    name: str
    category: str
    mutate: Callable[[dict[str, Any]], None]


def set_nested(entry_id: str, section: str, key: str, value: Any):
    def mutate(spec: dict[str, Any]) -> None:
        find_entry(spec, entry_id)[section][key] = value

    return mutate


def remove_surface(spec: dict[str, Any]) -> None:
    spec["manifest"]["entries"] = [
        item for item in spec["manifest"]["entries"] if item["surface"] != "protocol"
    ]


def duplicate_pair(spec: dict[str, Any]) -> None:
    duplicate = copy.deepcopy(find_entry(spec, "code-repo-summary-planned"))
    duplicate["id"] = "duplicate-pair"
    spec["manifest"]["entries"].append(duplicate)


def duplicate_canonical(spec: dict[str, Any]) -> None:
    duplicate = copy.deepcopy(find_entry(spec, "platform-contracts"))
    duplicate["id"] = "duplicate-canonical"
    duplicate["source"]["path"] = "docs/platform/shared-registry-boundary.md"
    spec["manifest"]["entries"].append(duplicate)


def append_platform(text: str):
    def mutate(spec: dict[str, Any]) -> None:
        path = "docs/platform/cross-runtime-envelope.md"
        spec["docs_ebus"][path] += text

    return mutate


def invalid_withdrawn_cleanup(spec: dict[str, Any]) -> None:
    transition_clean(spec)
    find_entry(spec, "code-repo-docs-planned")["lifecycle"][
        "cleanup_required"
    ] = False


def invalid_withdrawn_output(spec: dict[str, Any]) -> None:
    transition_clean(spec)
    find_entry(spec, "code-repo-docs-planned")["outputs"]["search"] = True


def clean_with_docs(spec: dict[str, Any]) -> None:
    transition_clean(spec, remove_docs=False)


def clean_with_substantive_summary(spec: dict[str, Any]) -> None:
    transition_clean(spec)
    spec["eebusreg"]["README.md"] += "The eeBUS runtime MUST persist trust.\n"


def early_architecture(spec: dict[str, Any]) -> None:
    set_active(find_entry(spec, "eebus-architecture-planned"), canonical=True)


def candidate_outside_hidden_area(spec: dict[str, Any]) -> None:
    find_entry(spec, "eebus-api-candidate")["owner"]["path"] = "api/lifecycle.md"
    spec["docs_eebus"]["api/lifecycle.md"] = "# Candidate Go API\n"


NEGATIVE_CASES = (
    NegativeCase(
        "manifest_missing",
        "manifest.missing",
        lambda s: s.update({"manifest_present": False}),
    ),
    NegativeCase(
        "unknown_top_level",
        "manifest.schema",
        lambda s: s["manifest"].update({"extra": True}),
    ),
    NegativeCase(
        "unknown_entry_field",
        "manifest.schema",
        lambda s: find_entry(s, "platform-contracts").update({"extra": True}),
    ),
    NegativeCase(
        "unknown_owner_field",
        "manifest.schema",
        lambda s: find_entry(s, "platform-contracts")["owner"].update(
            {"extra": True}
        ),
    ),
    NegativeCase(
        "unknown_output_field",
        "manifest.schema",
        lambda s: find_entry(s, "platform-contracts")["outputs"].update(
            {"extra": True}
        ),
    ),
    NegativeCase(
        "unknown_lifecycle_field",
        "manifest.schema",
        lambda s: find_entry(s, "platform-contracts")["lifecycle"].update(
            {"extra": True}
        ),
    ),
    NegativeCase(
        "unknown_enforcement_field",
        "manifest.schema",
        lambda s: find_entry(s, "platform-contracts")["enforcement"].update(
            {"extra": True}
        ),
    ),
    NegativeCase(
        "unsupported_version",
        "manifest.version",
        lambda s: s["manifest"].update({"version": 2}),
    ),
    NegativeCase("surface_missing", "ownership.surface-missing", remove_surface),
    NegativeCase(
        "owner_source_pair_duplicate", "ownership.pair-duplicate", duplicate_pair
    ),
    NegativeCase(
        "canonical_duplicate", "ownership.canonical-duplicate", duplicate_canonical
    ),
    NegativeCase(
        "unknown_state",
        "state.invalid",
        lambda s: find_entry(s, "platform-contracts").update({"state": "draft"}),
    ),
    NegativeCase(
        "planned_wrong_expiry",
        "state.planned",
        set_nested(
            "eebus-architecture-planned",
            "lifecycle",
            "expires_at",
            "2026-01-16T00:00:00Z",
        ),
    ),
    NegativeCase(
        "planned_output",
        "state.planned",
        set_nested(
            "eebus-architecture-planned", "outputs", "stable_navigation", True
        ),
    ),
    NegativeCase(
        "planned_missing_source_issue",
        "state.planned",
        set_nested(
            "eebus-architecture-planned", "lifecycle", "source_issue", None
        ),
    ),
    NegativeCase(
        "planned_basic_iso_timestamp",
        "manifest.schema",
        set_nested(
            "eebus-architecture-planned",
            "lifecycle",
            "created_at",
            "20260101T000000Z",
        ),
    ),
    NegativeCase(
        "candidate_wrong_expiry",
        "state.candidate",
        set_nested(
            "eebus-api-candidate", "lifecycle", "expires_at", "2026-02-15T00:00:00Z"
        ),
    ),
    NegativeCase(
        "candidate_missing_source_pr",
        "state.candidate",
        set_nested("eebus-api-candidate", "lifecycle", "source_pr", None),
    ),
    NegativeCase(
        "candidate_missing_source_ref",
        "state.candidate",
        set_nested("eebus-api-candidate", "lifecycle", "source_ref", None),
    ),
    NegativeCase(
        "candidate_missing_hash",
        "state.candidate",
        set_nested("eebus-api-candidate", "lifecycle", "content_sha256", None),
    ),
    NegativeCase(
        "candidate_digest_mismatch",
        "state.candidate",
        set_nested("eebus-api-candidate", "lifecycle", "content_sha256", "0" * 64),
    ),
    NegativeCase(
        "candidate_stable_output",
        "state.candidate",
        set_nested("eebus-api-candidate", "outputs", "release_bundle", True),
    ),
    NegativeCase(
        "candidate_outside_hidden_area",
        "state.candidate",
        candidate_outside_hidden_area,
    ),
    NegativeCase(
        "active_not_frozen",
        "state.active",
        set_nested("platform-contracts", "lifecycle", "frozen_at", None),
    ),
    NegativeCase(
        "active_has_expiry",
        "state.active",
        set_nested(
            "platform-contracts", "lifecycle", "expires_at", "2026-02-01T00:00:00Z"
        ),
    ),
    NegativeCase(
        "active_offset_timestamp",
        "manifest.schema",
        set_nested(
            "platform-contracts",
            "lifecycle",
            "approved_at",
            "2026-01-02T00:00:00+00:00",
        ),
    ),
    NegativeCase(
        "withdrawn_cleanup_optional", "state.withdrawn", invalid_withdrawn_cleanup
    ),
    NegativeCase("withdrawn_output", "state.withdrawn", invalid_withdrawn_output),
    NegativeCase(
        "absolute_path",
        "path.absolute",
        set_nested(
            "eebus-architecture-planned", "owner", "path", "/private/future.md"
        ),
    ),
    NegativeCase(
        "traversal_path",
        "path.absolute",
        set_nested(
            "eebus-architecture-planned", "source", "path", "../future.md"
        ),
    ),
    NegativeCase(
        "private_identifier",
        "privacy.private-identifier",
        set_nested(
            "eebus-architecture-planned",
            "source",
            "path",
            "devices/serial=redacted-value",
        ),
    ),
    NegativeCase(
        "forward_inline_link",
        "link.forward",
        append_platform(
            "[Unmerged](../../helianthus-docs-eebus/architecture/future.md)\n"
        ),
    ),
    NegativeCase(
        "forward_reference_link",
        "link.forward",
        append_platform(
            "[Unmerged][future]\n\n"
            "[future]: ../../helianthus-docs-eebus/architecture/future.md\n"
        ),
    ),
    NegativeCase(
        "candidate_immutable_link",
        "link.forward",
        append_platform(
            "[Candidate](https://github.com/Project-Helianthus/"
            "helianthus-docs-eebus/blob/__DOCS_EEBUS_REF__/"
            "api/_candidate/lifecycle.md)\n"
        ),
    ),
    NegativeCase(
        "docs_ebus_ref_missing",
        "input.docs-ebus-ref",
        lambda s: s.update({"docs_ebus_ref": None}),
    ),
    NegativeCase(
        "docs_ebus_ref_moving",
        "input.docs-ebus-ref",
        lambda s: s.update({"docs_ebus_ref": "main"}),
    ),
    NegativeCase(
        "docs_eebus_ref_missing",
        "input.docs-eebus-ref",
        lambda s: s.update({"docs_eebus_ref": None}),
    ),
    NegativeCase(
        "docs_eebus_ref_moving",
        "input.docs-eebus-ref",
        lambda s: s.update({"docs_eebus_ref": "feature/docs"}),
    ),
    NegativeCase(
        "eebusreg_ref_missing",
        "input.eebusreg-ref",
        lambda s: s.update({"eebusreg_ref": None}),
    ),
    NegativeCase(
        "eebusreg_ref_moving",
        "input.eebusreg-ref",
        lambda s: s.update({"eebusreg_ref": "main"}),
    ),
    NegativeCase(
        "ambient_dirty_clone",
        "input.clean-clone",
        lambda s: s.update({"dirty_repo": "docs_eebus"}),
    ),
    NegativeCase(
        "e2_transition_skipped",
        "enforcement.transition",
        lambda s: s.update({"enforce_through": E2_STAGE}),
    ),
    NegativeCase(
        "future_state_activated_early",
        "enforcement.transition",
        early_architecture,
    ),
    NegativeCase(
        "protocol_copy_alternate_heading",
        "ownership.protocol-copy",
        append_platform("\n## Wire Notes\n\nSHIP peers MUST negotiate sessions.\n"),
    ),
    NegativeCase(
        "architecture_copy_without_h1",
        "ownership.architecture-copy",
        append_platform("\nState notes: the eeBUS runtime MUST persist trust state.\n"),
    ),
    NegativeCase(
        "api_copy_normative_summary",
        "ownership.api-copy",
        append_platform(
            "\nSummary-only: the eeBUS Go API MUST expose package symbols.\n"
        ),
    ),
    NegativeCase(
        "code_repo_docs_at_clean",
        "ownership.code-repo-substantive",
        clean_with_docs,
    ),
    NegativeCase(
        "summary_substantive_at_clean",
        "ownership.summary-only-substantive",
        clean_with_substantive_summary,
    ),
)


def test_required_platform_artifacts_exist() -> None:
    assert (REPO_ROOT / MANIFEST_PATH).is_file()
    assert all((REPO_ROOT / path).is_file() for path in CONTRACT_PAGES)


def test_production_validator_entrypoint_exists() -> None:
    assert VALIDATOR_PATH.is_file()


@pytest.mark.parametrize("path,required_terms", PAGE_REQUIRED_TERMS.items())
def test_contract_page_contains_required_clauses(
    path: pathlib.Path, required_terms: tuple[str, ...]
) -> None:
    text = (REPO_ROOT / path).read_text(encoding="utf-8")
    assert [term for term in required_terms if term.casefold() not in text.casefold()] == []


def test_current_platform_fixture_passes_with_pre_e2_and_pre_clean_material(
    tmp_path: pathlib.Path,
) -> None:
    workspace = build_workspace(tmp_path)
    assert validate(load_validator(), workspace) == []


@pytest.mark.parametrize("case", NEGATIVE_CASES, ids=lambda case: case.name)
def test_negative_mutations_emit_one_exact_category(
    tmp_path: pathlib.Path, case: NegativeCase
) -> None:
    workspace = build_workspace(tmp_path, case.mutate)
    assert validate(load_validator(), workspace) == [case.category]


def test_negative_matrix_has_broad_unique_category_coverage() -> None:
    categories = {case.category for case in NEGATIVE_CASES}
    assert SURFACES == {item["surface"] for item in base_manifest()["entries"]}
    assert {
        "manifest.missing",
        "manifest.schema",
        "manifest.version",
        "ownership.surface-missing",
        "ownership.pair-duplicate",
        "ownership.canonical-duplicate",
        "state.invalid",
        "state.planned",
        "state.candidate",
        "state.active",
        "state.withdrawn",
        "path.absolute",
        "privacy.private-identifier",
        "link.forward",
        "input.docs-ebus-ref",
        "input.docs-eebus-ref",
        "input.eebusreg-ref",
        "input.clean-clone",
        "enforcement.transition",
        "ownership.protocol-copy",
        "ownership.architecture-copy",
        "ownership.api-copy",
        "ownership.code-repo-substantive",
        "ownership.summary-only-substantive",
    } <= categories


def test_e2_transition_passes_but_clean_cannot_be_skipped(tmp_path: pathlib.Path) -> None:
    e2 = build_workspace(tmp_path / "e2", transition_e2)
    assert validate(load_validator(), e2) == []

    def require_clean(spec: dict[str, Any]) -> None:
        transition_e2(spec)
        spec["enforce_through"] = CLEAN_STAGE

    clean_required = build_workspace(tmp_path / "clean-required", require_clean)
    assert validate(load_validator(), clean_required) == ["enforcement.transition"]


def test_clean_transition_passes_after_docs_removed_and_summary_trimmed(
    tmp_path: pathlib.Path,
) -> None:
    workspace = build_workspace(tmp_path, transition_clean)
    assert validate(load_validator(), workspace) == []


def remove_active_owner(spec: dict[str, Any]) -> None:
    del spec["docs_eebus"]["protocols/ship-spine.md"]


def remove_candidate_owner(spec: dict[str, Any]) -> None:
    del spec["docs_eebus"]["api/_candidate/lifecycle.md"]


def remove_candidate_source(spec: dict[str, Any]) -> None:
    del spec["eebusreg"]["api/lifecycle.go"]


def missing_active_source(spec: dict[str, Any]) -> None:
    find_entry(spec, "platform-contracts")["source"]["path"] = (
        "docs/platform/missing-source.md"
    )


def directory_as_active_owner(spec: dict[str, Any]) -> None:
    item = find_entry(spec, "eebus-protocol")
    item["owner"]["path"] = "protocols"
    item["source"]["path"] = "protocols"


def relative_symlink_component(spec: dict[str, Any]) -> None:
    item = find_entry(spec, "eebus-protocol")
    item["owner"]["path"] = "protocol-link/ship-spine.md"
    item["source"]["path"] = "protocol-link/ship-spine.md"
    spec["symlinks"]["docs_eebus"]["protocol-link"] = "protocols"


def absolute_symlink_component(spec: dict[str, Any]) -> None:
    item = find_entry(spec, "eebus-protocol")
    item["owner"]["path"] = "protocol-link/ship-spine.md"
    item["source"]["path"] = "protocol-link/ship-spine.md"
    spec["symlinks"]["docs_eebus"]["protocol-link"] = "ABS:protocols"


def source_symlink(spec: dict[str, Any]) -> None:
    find_entry(spec, "platform-contracts")["source"]["path"] = (
        "docs/platform/source-link.md"
    )
    spec["symlinks"]["docs_ebus"]["docs/platform/source-link.md"] = (
        "cross-runtime-envelope.md"
    )


@pytest.mark.parametrize(
    "mutate,expected",
    (
        (remove_active_owner, "artifact.owner"),
        (remove_candidate_owner, "artifact.owner"),
        (remove_candidate_source, "artifact.source"),
        (missing_active_source, "artifact.source"),
        (directory_as_active_owner, "artifact.owner"),
        (relative_symlink_component, "path.symlink"),
        (absolute_symlink_component, "path.symlink"),
        (source_symlink, "path.symlink"),
    ),
    ids=(
        "missing-active-owner",
        "missing-candidate-owner",
        "missing-candidate-source",
        "missing-active-source",
        "owner-not-regular",
        "relative-symlink-component",
        "absolute-symlink-component",
        "source-symlink",
    ),
)
def test_owner_source_artifact_safety(
    tmp_path: pathlib.Path,
    mutate: Callable[[dict[str, Any]], None],
    expected: str,
) -> None:
    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == [expected]


def test_repository_root_identity_is_verified(tmp_path: pathlib.Path) -> None:
    def wrong_remote(spec: dict[str, Any]) -> None:
        spec["remotes"]["docs_eebus"] = "helianthus-docs-ebus"

    workspace = build_workspace(tmp_path, wrong_remote)
    assert validate(load_validator(), workspace) == ["input.repository-root"]


@pytest.mark.parametrize(
    "addition",
    (
        "\n```markdown\nSHIP peers MUST negotiate sessions.\n```\n",
        "\n`The eeBUS runtime MUST persist trust state.`\n",
        "\n    The eeBUS Go API MUST expose package symbols.\n",
        "\nSummary: SHIP peers negotiate sessions in the canonical protocol docs.\n",
        "\nThe platform evidence gate MUST record whether a SHIP session was observed.\n",
    ),
    ids=(
        "fenced-code",
        "inline-code",
        "indented-code",
        "non-normative-summary",
        "evidence-gate-false-positive",
    ),
)
def test_semantic_copy_false_positive_controls(
    tmp_path: pathlib.Path, addition: str
) -> None:
    workspace = build_workspace(tmp_path, append_platform(addition))
    assert validate(load_validator(), workspace) == []


@pytest.mark.parametrize(
    "addition,expected",
    (
        (
            "\n## SHIP Protocol Reference\n\n"
            "Peers MUST negotiate a session before sending messages.\n",
            "ownership.protocol-copy",
        ),
        (
            "\n#### eeBUS Runtime Trust And Lifecycle\n\n"
            "Implementations MUST persist trust state before reconnecting.\n",
            "ownership.architecture-copy",
        ),
        (
            "\n## eeBUS\n\n### [Go API Reference][api-reference]\n\n"
            "The package MUST expose exported lifecycle functions.\n\n"
            "[api-reference]: https://example.invalid/api\n",
            "ownership.api-copy",
        ),
    ),
    ids=("protocol-h2", "architecture-h4", "reference-style-api-h3"),
)
def test_semantic_copy_preserves_heading_section_context(
    tmp_path: pathlib.Path, addition: str, expected: str
) -> None:
    workspace = build_workspace(tmp_path, append_platform(addition))
    assert validate(load_validator(), workspace) == [expected]


@pytest.mark.parametrize(
    "addition",
    (
        "\n## SHIP Protocol Example\n\n"
        "Non-normative example quotation:\n\n"
        "> Peers MUST negotiate a session before sending SPINE messages.\n",
        "\n### Non-normative eeBUS Runtime Trust Example\n\n"
        "Implementations MUST persist trust state before reconnecting.\n",
        "\n#### eeBUS Go API Example\n\nNon-normative example:\n\n"
        "The package MUST expose lifecycle functions.\n",
        "\n#### eeBUS Go API Reference\n\n"
        "This non-normative example says the package MUST expose lifecycle functions.\n",
        "\n## eeBUS Runtime Trust And Lifecycle Ownership\n\n"
        "The canonical eeBUS documentation MUST own runtime, trust, and lifecycle details; "
        "this platform page remains a summary only.\n",
        "\n# eeBUS HA Network Proof Gate\n\n## Credential Boundary\n\n"
        "Production trust-store semantics, clone/restore lockout, quarantine/backoff, "
        "and first-trust confirmation are M4 work. MSP-03C evidence must not claim "
        "those properties.\n",
        "\n# eeBUS Interop Smoke Gate\n\n## Live VR940f Boundary\n\n"
        "The artifact may record service visibility, but it must not claim pairing/session, "
        "feature graph, reconnect, or semantic facts.\n",
    ),
    ids=(
        "quoted-protocol-example",
        "non-normative-architecture-section",
        "non-normative-api-lead-in",
        "non-normative-api-example",
        "platform-ownership-summary",
        "network-proof-boundary",
        "interop-artifact-boundary",
    ),
)
def test_heading_context_semantic_copy_false_positive_controls(
    tmp_path: pathlib.Path, addition: str
) -> None:
    workspace = build_workspace(tmp_path, append_platform(addition))
    assert validate(load_validator(), workspace) == []


@pytest.mark.parametrize(
    "addition",
    (
        "\n[Protocol [stable]][proto]\n\n"
        "[proto]: https://github.com/Project-Helianthus/helianthus-docs-eebus/"
        "blob/__DOCS_EEBUS_REF__/protocols/ship-spine.md \"title\"\n",
        "\n<a href=\"https://github.com/Project-Helianthus/"
        "helianthus-docs-eebus/blob/__DOCS_EEBUS_REF__/"
        "protocols/ship-spine.md\">Protocol</a>\n",
        "\n```markdown\n[Bad][future]\n"
        "[future]: ../../helianthus-docs-eebus/architecture/future.md\n```\n",
    ),
    ids=("reference-style-active", "html-active", "code-link-ignored"),
)
def test_markdown_link_parser_accepts_only_real_active_links(
    tmp_path: pathlib.Path, addition: str
) -> None:
    workspace = build_workspace(tmp_path, append_platform(addition))
    assert validate(load_validator(), workspace) == []


def write_manifest_text(workspace: Workspace, text: str | bytes) -> None:
    path = workspace.docs_ebus / MANIFEST_PATH
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text, encoding="utf-8")


@pytest.mark.parametrize(
    "mutation",
    (
        lambda text: text.replace(
            "schema: helianthus.platform.doc-ownership\n",
            "schema: helianthus.platform.doc-ownership\n"
            "schema: helianthus.platform.doc-ownership\n",
            1,
        ),
        lambda text: text.replace(
            "    candidate: false\n",
            "    candidate: false\n    candidate: false\n",
            1,
        ),
        lambda _text: "schema: [unterminated /private/secret-value\n",
        lambda _text: (
            "schema: helianthus.platform.doc-ownership\n"
            "version: 1\nentries: &entries [*entries]\n"
        ),
    ),
    ids=("duplicate-top", "duplicate-nested", "malformed", "cyclic-alias"),
)
def test_manifest_parser_failures_are_schema_only(
    tmp_path: pathlib.Path, mutation: Callable[[str], str]
) -> None:
    workspace = build_workspace(tmp_path)
    path = workspace.docs_ebus / MANIFEST_PATH
    write_manifest_text(workspace, mutation(path.read_text(encoding="utf-8")))
    assert repository_validate(load_validator(), workspace.docs_ebus) == [
        "manifest.schema"
    ]


def test_manifest_invalid_utf8_is_schema_only(tmp_path: pathlib.Path) -> None:
    workspace = build_workspace(tmp_path)
    write_manifest_text(workspace, b"\xff\xfeprivate-value")
    assert repository_validate(load_validator(), workspace.docs_ebus) == [
        "manifest.schema"
    ]


@pytest.mark.parametrize(
    "limit_name,limit_value",
    (
        ("MAX_MANIFEST_BYTES", 32),
        ("MAX_YAML_NESTING", 2),
        ("MAX_YAML_TOKENS", 10),
        ("MAX_YAML_NODES", 10),
    ),
)
def test_manifest_resource_bounds_are_schema_only(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, limit_name: str, limit_value: int
) -> None:
    workspace = build_workspace(tmp_path)
    validator = load_validator()
    monkeypatch.setattr(validator, limit_name, limit_value)
    assert repository_validate(validator, workspace.docs_ebus) == ["manifest.schema"]


def test_manifest_alias_limit_and_small_alias_behavior(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = build_workspace(tmp_path)
    path = workspace.docs_ebus / MANIFEST_PATH
    text = path.read_text(encoding="utf-8")
    text = text.replace("    source_ref: null\n", "    source_ref: &none null\n", 1)
    text = text.replace("    content_sha256: null\n", "    content_sha256: *none\n", 1)
    write_manifest_text(workspace, text)
    validator = load_validator()
    assert repository_validate(validator, workspace.docs_ebus) == []
    monkeypatch.setattr(validator, "MAX_YAML_ALIASES", 0)
    assert repository_validate(validator, workspace.docs_ebus) == ["manifest.schema"]


def test_manifest_cli_never_leaks_parser_value_or_path(tmp_path: pathlib.Path) -> None:
    workspace = build_workspace(tmp_path)
    write_manifest_text(
        workspace, "schema: [unterminated /private/operator/secret-marker\n"
    )
    result = subprocess.run(
        [
            "python3",
            str(VALIDATOR_PATH),
            "--mode",
            "repository",
            "--docs-ebus-root",
            str(workspace.docs_ebus),
            "--enforce-through",
            PLATFORM_STAGE,
            "--toolchain-mode",
            "supported",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "manifest.schema\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    "timestamp",
    (
        "20260115T000000Z",
        "2026-01-15 00:00:00Z",
        "2026-01-15T00:00:00+00:00",
        "2026-01-15T01:00:00+01:00",
        "2026-01-15T00:00:00z",
        "2026-01-15T00:00:60Z",
        "2026-01-15T00:00:00,1Z",
        "2026-01-15T00:00:00.1234567Z",
    ),
)
def test_main_expiry_rejects_non_contract_timestamps(
    tmp_path: pathlib.Path, timestamp: str
) -> None:
    workspace = build_workspace(tmp_path)
    assert repository_validate(
        load_validator(),
        workspace.docs_ebus,
        mode="main-expiry",
        evaluated_at=timestamp,
        evaluation_source="test.event.timestamp",
    ) == ["expiry.timestamp"]


def test_main_expiry_requires_named_source(tmp_path: pathlib.Path) -> None:
    workspace = build_workspace(tmp_path)
    assert repository_validate(
        load_validator(),
        workspace.docs_ebus,
        mode="main-expiry",
        evaluated_at="2026-01-10T00:00:00Z",
        evaluation_source=None,
    ) == ["expiry.source"]


def test_planned_expiry_boundary_is_inclusive(tmp_path: pathlib.Path) -> None:
    workspace = build_workspace(tmp_path)
    validator = load_validator()
    assert repository_validate(
        validator,
        workspace.docs_ebus,
        mode="main-expiry",
        evaluated_at="2026-01-14T23:59:59.999999Z",
        evaluation_source="test.event.timestamp",
    ) == []
    assert repository_validate(
        validator,
        workspace.docs_ebus,
        mode="main-expiry",
        evaluated_at="2026-01-15T00:00:00Z",
        evaluation_source="test.event.timestamp",
    ) == ["expiry.planned"]


def test_fractional_expiry_boundary_is_inclusive(tmp_path: pathlib.Path) -> None:
    def fractional(spec: dict[str, Any]) -> None:
        for entry_id in (
            "eebus-architecture-planned",
            "code-repo-docs-planned",
            "code-repo-summary-planned",
        ):
            item = find_entry(spec, entry_id)
            item["lifecycle"]["created_at"] = "2026-01-01T00:00:00.123456Z"
            item["lifecycle"]["expires_at"] = "2026-01-15T00:00:00.123456Z"

    workspace = build_workspace(tmp_path, fractional)
    validator = load_validator()
    assert repository_validate(
        validator,
        workspace.docs_ebus,
        mode="main-expiry",
        evaluated_at="2026-01-15T00:00:00.123455Z",
        evaluation_source="test.event.timestamp",
    ) == []
    assert repository_validate(
        validator,
        workspace.docs_ebus,
        mode="main-expiry",
        evaluated_at="2026-01-15T00:00:00.123456Z",
        evaluation_source="test.event.timestamp",
    ) == ["expiry.planned"]


def test_candidate_expiry_boundary_is_inclusive(tmp_path: pathlib.Path) -> None:
    def candidate_first(spec: dict[str, Any]) -> None:
        item = find_entry(spec, "eebus-api-candidate")
        item["lifecycle"]["created_at"] = "2025-12-11T00:00:00Z"
        item["lifecycle"]["expires_at"] = "2026-01-10T00:00:00Z"

    workspace = build_workspace(tmp_path, candidate_first)
    assert repository_validate(
        load_validator(),
        workspace.docs_ebus,
        mode="main-expiry",
        evaluated_at="2026-01-10T00:00:00Z",
        evaluation_source="test.event.timestamp",
    ) == ["expiry.candidate"]


@pytest.mark.parametrize(
    "timestamp",
    (
        "2026-01-15T00:00:00Z",
        "2026-01-15T00:00:00.1Z",
        "2026-01-15T00:00:00.123456Z",
    ),
)
def test_strict_timestamp_parser_accepts_documented_forms(timestamp: str) -> None:
    assert load_validator()._parse_instant(timestamp) is not None


def lifecycle_timestamp_case(
    state: str, field: str, timestamp: str
) -> Callable[[dict[str, Any]], None]:
    def mutate(spec: dict[str, Any]) -> None:
        if state == "planned":
            item = find_entry(spec, "eebus-architecture-planned")
        elif state == "candidate":
            item = find_entry(spec, "eebus-api-candidate")
        elif state == "active":
            item = find_entry(spec, "platform-contracts")
        else:
            transition_clean(spec)
            item = find_entry(spec, "code-repo-docs-planned")
        item["lifecycle"][field] = timestamp

    return mutate


@pytest.mark.parametrize(
    "state,field,timestamp",
    (
        ("planned", "approved_at", "2026-01-02T00:00:00+00:00"),
        ("candidate", "frozen_at", "20260103T000000Z"),
        ("active", "expires_at", "2026-02-30T00:00:00Z"),
        ("withdrawn", "created_at", "not-a-timestamp"),
    ),
    ids=(
        "planned-optional-offset",
        "candidate-optional-basic",
        "active-optional-invalid-date",
        "withdrawn-required-invalid",
    ),
)
def test_present_lifecycle_timestamps_fail_schema_before_state_logic(
    tmp_path: pathlib.Path, state: str, field: str, timestamp: str
) -> None:
    workspace = build_workspace(
        tmp_path, lifecycle_timestamp_case(state, field, timestamp)
    )
    assert validate(load_validator(), workspace) == ["manifest.schema"]


def test_malformed_optional_lifecycle_timestamp_cli_is_category_only(
    tmp_path: pathlib.Path,
) -> None:
    workspace = build_workspace(
        tmp_path,
        lifecycle_timestamp_case(
            "planned", "approved_at", "2026-01-02T00:00:00+00:00"
        ),
    )
    result = subprocess.run(
        [
            "python3",
            str(VALIDATOR_PATH),
            "--mode",
            "repository",
            "--docs-ebus-root",
            str(workspace.docs_ebus),
            "--enforce-through",
            PLATFORM_STAGE,
            "--toolchain-mode",
            "supported",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "manifest.schema\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    "field", ("created_at", "expires_at", "approved_at", "frozen_at")
)
@pytest.mark.parametrize(
    "timestamp",
    (
        "2026-01-02T00:00:00+00:00",
        "20260102T000000Z",
        "2026-02-30T00:00:00Z",
    ),
    ids=("offset", "basic", "invalid-date"),
)
def test_every_present_lifecycle_timestamp_field_uses_strict_parser(
    field: str, timestamp: str
) -> None:
    manifest = base_manifest()
    find_entry({"manifest": manifest}, "platform-contracts")["lifecycle"][field] = (
        timestamp
    )
    assert load_validator()._schema_valid(manifest) is False


def test_toolchain_checks_actual_versions_not_caller_claims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validator = load_validator()
    monkeypatch.setattr(
        validator, "_actual_tool_versions", lambda: ((3, 12, 10), "6.0.2", "6.0.2")
    )
    assert validator._toolchain_categories("exact") == set()
    monkeypatch.setattr(
        validator, "_actual_tool_versions", lambda: ((3, 12, 9), "6.0.2", "6.0.2")
    )
    assert validator._toolchain_categories("exact") == {"toolchain.python"}
    monkeypatch.setattr(
        validator, "_actual_tool_versions", lambda: ((3, 14, 5), "6.0.3", "6.0.2")
    )
    assert validator._toolchain_categories("supported") == {"toolchain.pyyaml"}


def test_removed_caller_pin_arguments_are_category_only(tmp_path: pathlib.Path) -> None:
    workspace = build_workspace(tmp_path)
    result = subprocess.run(
        [
            "python3",
            str(VALIDATOR_PATH),
            "--mode",
            "repository",
            "--docs-ebus-root",
            str(workspace.docs_ebus),
            "--enforce-through",
            PLATFORM_STAGE,
            "--toolchain-mode",
            "supported",
            "--pinned-tool",
            "python=0.0.0-secret-value",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "input.arguments\n"
    assert result.stderr == ""


def test_main_expiry_cli_is_terminal_and_category_only(tmp_path: pathlib.Path) -> None:
    workspace = build_workspace(tmp_path)
    result = subprocess.run(
        [
            "python3",
            str(VALIDATOR_PATH),
            "--mode",
            "main-expiry",
            "--docs-ebus-root",
            str(workspace.docs_ebus),
            "--evaluated-at",
            "2026-01-15T00:00:00Z",
            "--evaluation-source",
            "test.event.timestamp",
            "--enforce-through",
            PLATFORM_STAGE,
            "--toolchain-mode",
            "supported",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "expiry.planned\n"
    assert result.stderr == ""
