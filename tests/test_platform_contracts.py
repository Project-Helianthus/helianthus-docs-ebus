from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
from dataclasses import dataclass
from typing import Any, Callable

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "scripts/validate_platform_contracts.py"
MANIFEST_PATH = pathlib.Path("docs/platform/manifests/eebus-doc-ownership.yaml")
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
        "docs-ebus ref",
        "docs-eebus ref",
        "clean clone",
        "pinned",
        "no ambient checkout state",
        "evaluation timestamp",
        "timestamp source",
        "terminal",
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
PINNED_TOOLS = {"python": "3.12.10", "pyyaml": "6.0.2"}


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
    }


def base_manifest() -> dict[str, Any]:
    active_lifecycle = lifecycle(
        created_at="2026-01-01T00:00:00Z",
        approved_at="2026-01-02T00:00:00Z",
        frozen_at="2026-01-03T00:00:00Z",
    )
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
                state_lifecycle=copy.deepcopy(active_lifecycle),
            ),
            entry(
                "eebus-architecture-planned",
                "architecture",
                "helianthus-docs-eebus",
                "architecture/lifecycle.md",
                "helianthus-docs-eebus",
                "architecture/lifecycle.md",
                "planned",
                canonical=False,
                output=outputs(),
                state_lifecycle=lifecycle(
                    created_at="2026-01-01T00:00:00Z",
                    expires_at="2026-01-15T00:00:00Z",
                    source_issue="Project-Helianthus/helianthus-docs-eebus#8",
                ),
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
                state_lifecycle=copy.deepcopy(active_lifecycle),
            ),
            entry(
                "code-repo-docs-withdrawn",
                "code_repo",
                "helianthus-eebusreg",
                "docs",
                "helianthus-eebusreg",
                "docs",
                "withdrawn",
                canonical=False,
                output=outputs(),
                state_lifecycle=lifecycle(
                    created_at="2026-01-01T00:00:00Z", cleanup_required=True
                ),
            ),
            entry(
                "code-repo-summary",
                "summary_only",
                "helianthus-eebusreg",
                "README.md",
                "helianthus-docs-eebus",
                "README.md",
                "active",
                canonical=False,
                output=outputs(stable=True),
                state_lifecycle=copy.deepcopy(active_lifecycle),
            ),
        ],
    }


def base_spec() -> dict[str, Any]:
    platform_header = "Canonical source: this page.\n\n"
    return {
        "manifest": base_manifest(),
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
            + "# Ownership Validation\n\nPR validation uses an explicit docs-ebus ref and docs-eebus ref, separate clean clones, pinned Python 3.12.10 and PyYAML 6.0.2, and no ambient checkout state. Main expiry validation requires an RFC 3339 evaluation timestamp and named timestamp source, and any diagnostic is terminal.\n",
        },
        "docs_eebus": {
            "README.md": "# eeBUS Documentation\n",
            "protocols/ship-spine.md": "# SHIP/SPINE Protocol\n\nCanonical protocol behavior.\n",
            "api/_candidate/lifecycle.md": "# Candidate Go API\n\nHidden candidate API.\n",
        },
        "eebusreg": {
            "README.md": "# eeBUS Registry\n\nCanonical docs: ../helianthus-docs-eebus/README.md\n",
            "api/lifecycle.go": "package api\n",
        },
        "mode": "pr",
        "evaluated_at": None,
        "evaluation_source": None,
        "docs_ebus_ref": "__AUTO__",
        "docs_eebus_ref": "__AUTO__",
        "dirty_repo": None,
        "manifest_present": True,
        "pinned_tools": copy.deepcopy(PINNED_TOOLS),
    }


def write_files(root: pathlib.Path, files: dict[str, str]) -> None:
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def commit_fixture(root: pathlib.Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
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
    mode: str
    evaluated_at: str | None
    evaluation_source: str | None
    pinned_tools: dict[str, str]


def build_workspace(
    tmp_path: pathlib.Path, mutate: Callable[[dict[str, Any]], None] | None = None
) -> Workspace:
    spec = base_spec()
    if mutate is not None:
        mutate(spec)

    eebusreg = tmp_path / "helianthus-eebusreg"
    eebusreg.mkdir()
    write_files(eebusreg, spec["eebusreg"])
    eebusreg_head = commit_fixture(eebusreg)

    docs_eebus = tmp_path / "helianthus-docs-eebus"
    docs_eebus.mkdir()
    write_files(docs_eebus, spec["docs_eebus"])
    docs_eebus_head = commit_fixture(docs_eebus)

    for item in spec["manifest"]["entries"]:
        if item["lifecycle"]["source_ref"] == "__SOURCE_REF__":
            item["lifecycle"]["source_ref"] = eebusreg_head

    docs_ebus = tmp_path / "helianthus-docs-ebus"
    docs_ebus.mkdir()
    write_files(docs_ebus, spec["docs_ebus"])
    if spec["manifest_present"]:
        manifest_path = docs_ebus / MANIFEST_PATH
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(spec["manifest"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    docs_ebus_head = commit_fixture(docs_ebus)

    roots = {
        "docs_ebus": docs_ebus,
        "docs_eebus": docs_eebus,
        "eebusreg": eebusreg,
    }
    dirty_repo = spec["dirty_repo"]
    if dirty_repo is not None:
        (roots[dirty_repo] / "ambient-untracked.txt").write_text(
            "dirty\n", encoding="utf-8"
        )

    docs_ebus_ref = (
        docs_ebus_head if spec["docs_ebus_ref"] == "__AUTO__" else spec["docs_ebus_ref"]
    )
    docs_eebus_ref = (
        docs_eebus_head
        if spec["docs_eebus_ref"] == "__AUTO__"
        else spec["docs_eebus_ref"]
    )
    return Workspace(
        docs_ebus=docs_ebus,
        docs_eebus=docs_eebus,
        eebusreg=eebusreg,
        docs_ebus_ref=docs_ebus_ref,
        docs_eebus_ref=docs_eebus_ref,
        mode=spec["mode"],
        evaluated_at=spec["evaluated_at"],
        evaluation_source=spec["evaluation_source"],
        pinned_tools=spec["pinned_tools"],
    )


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "platform_contract_validator", VALIDATOR_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate(validator: Any, workspace: Workspace) -> list[str]:
    diagnostics = validator.validate_workspace(
        docs_ebus_root=workspace.docs_ebus,
        docs_eebus_root=workspace.docs_eebus,
        eebusreg_root=workspace.eebusreg,
        mode=workspace.mode,
        docs_ebus_ref=workspace.docs_ebus_ref,
        docs_eebus_ref=workspace.docs_eebus_ref,
        evaluated_at=workspace.evaluated_at,
        evaluation_source=workspace.evaluation_source,
        pinned_tools=workspace.pinned_tools,
    )
    assert isinstance(diagnostics, list)
    assert diagnostics == sorted(set(diagnostics))
    assert all(
        isinstance(item, str) and item and " " not in item for item in diagnostics
    )
    return diagnostics


def find_entry(spec: dict[str, Any], entry_id: str) -> dict[str, Any]:
    return next(item for item in spec["manifest"]["entries"] if item["id"] == entry_id)


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
    duplicate = copy.deepcopy(find_entry(spec, "code-repo-summary"))
    duplicate["id"] = "duplicate-pair"
    spec["manifest"]["entries"].append(duplicate)


def duplicate_canonical(spec: dict[str, Any]) -> None:
    duplicate = copy.deepcopy(find_entry(spec, "platform-contracts"))
    duplicate["id"] = "duplicate-canonical"
    duplicate["source"]["path"] = "docs/platform/shared-registry-boundary.md"
    spec["manifest"]["entries"].append(duplicate)


def add_substantive(path_group: str, path: str, text: str):
    def mutate(spec: dict[str, Any]) -> None:
        spec[path_group][path] = text

    return mutate


def expire_candidate(spec: dict[str, Any]) -> None:
    find_entry(spec, "eebus-architecture-planned")["lifecycle"].update(
        {
            "created_at": "2026-02-15T00:00:00Z",
            "expires_at": "2026-03-01T00:00:00Z",
        }
    )
    spec.update(
        {
            "mode": "main",
            "evaluated_at": "2026-02-15T00:00:00Z",
            "evaluation_source": "github.event.repository.updated_at",
        }
    )


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
        lambda s: find_entry(s, "platform-contracts")["owner"].update({"extra": True}),
    ),
    NegativeCase(
        "unknown_output_field",
        "manifest.schema",
        lambda s: find_entry(s, "platform-contracts")["outputs"].update(
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
        "planned_linkable_output",
        "state.planned",
        set_nested("eebus-architecture-planned", "outputs", "stable_navigation", True),
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
        "candidate_stable_output",
        "state.candidate",
        set_nested("eebus-api-candidate", "outputs", "release_bundle", True),
    ),
    NegativeCase(
        "candidate_outside_hidden_area",
        "state.candidate",
        set_nested("eebus-api-candidate", "owner", "path", "api/lifecycle.md"),
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
        "withdrawn_cleanup_optional",
        "state.withdrawn",
        set_nested("code-repo-docs-withdrawn", "lifecycle", "cleanup_required", False),
    ),
    NegativeCase(
        "withdrawn_in_output",
        "state.withdrawn",
        set_nested("code-repo-docs-withdrawn", "outputs", "search", True),
    ),
    NegativeCase(
        "absolute_path",
        "path.absolute",
        set_nested("platform-contracts", "owner", "path", "/Users/operator/private.md"),
    ),
    NegativeCase(
        "private_identifier",
        "privacy.private-identifier",
        set_nested(
            "eebus-protocol", "source", "path", "devices/serial=VR940F-123456789"
        ),
    ),
    NegativeCase(
        "forward_link",
        "link.forward",
        lambda s: s["docs_ebus"].update(
            {
                "docs/platform/cross-runtime-envelope.md": s["docs_ebus"][
                    "docs/platform/cross-runtime-envelope.md"
                ]
                + "[Unmerged](../../helianthus-docs-eebus/architecture/lifecycle.md)\n"
            }
        ),
    ),
    NegativeCase(
        "docs_ebus_ref_missing",
        "input.docs-ebus-ref",
        lambda s: s.update({"docs_ebus_ref": None}),
    ),
    NegativeCase(
        "docs_ebus_ref_not_commit",
        "input.docs-ebus-ref",
        lambda s: s.update({"docs_ebus_ref": "main"}),
    ),
    NegativeCase(
        "docs_eebus_ref_missing",
        "input.docs-eebus-ref",
        lambda s: s.update({"docs_eebus_ref": None}),
    ),
    NegativeCase(
        "docs_eebus_ref_not_commit",
        "input.docs-eebus-ref",
        lambda s: s.update({"docs_eebus_ref": "feature/docs"}),
    ),
    NegativeCase(
        "ambient_dirty_clone",
        "input.clean-clone",
        lambda s: s.update({"dirty_repo": "docs_eebus"}),
    ),
    NegativeCase(
        "unpinned_tool",
        "input.pinned-tools",
        lambda s: s.update({"pinned_tools": {"python": "3.12"}}),
    ),
    NegativeCase(
        "main_timestamp_missing",
        "expiry.timestamp",
        lambda s: s.update(
            {"mode": "main", "evaluation_source": "github.event.repository.updated_at"}
        ),
    ),
    NegativeCase(
        "main_timestamp_source_missing",
        "expiry.source",
        lambda s: s.update({"mode": "main", "evaluated_at": "2026-01-10T00:00:00Z"}),
    ),
    NegativeCase(
        "planned_expired",
        "expiry.planned",
        lambda s: s.update(
            {
                "mode": "main",
                "evaluated_at": "2026-01-16T00:00:00Z",
                "evaluation_source": "github.event.repository.updated_at",
            }
        ),
    ),
    NegativeCase("candidate_expired", "expiry.candidate", expire_candidate),
    NegativeCase(
        "protocol_copy",
        "ownership.protocol-copy",
        add_substantive(
            "docs_ebus",
            "docs/platform/ship-spine-protocol.md",
            "# SHIP/SPINE Protocol\n\nPeers MUST negotiate this protocol.\n",
        ),
    ),
    NegativeCase(
        "architecture_copy",
        "ownership.architecture-copy",
        add_substantive(
            "docs_ebus",
            "docs/platform/eebus-runtime-trust.md",
            "# eeBUS Trust\n\nThe runtime MUST persist trust.\n",
        ),
    ),
    NegativeCase(
        "api_copy",
        "ownership.api-copy",
        add_substantive(
            "docs_ebus",
            "docs/platform/eebus-go-api.md",
            "# eeBUS Go API\n\nfunc Snapshot() returns the API value.\n",
        ),
    ),
    NegativeCase(
        "code_repo_docs",
        "ownership.code-repo-substantive",
        add_substantive(
            "eebusreg",
            "docs/guide.md",
            "# Runtime Guide\n\nSubstantive implementation documentation.\n",
        ),
    ),
    NegativeCase(
        "summary_becomes_normative",
        "ownership.summary-only-substantive",
        lambda s: s["eebusreg"].update(
            {
                "README.md": s["eebusreg"]["README.md"]
                + "The runtime MUST expose this API.\n"
            }
        ),
    ),
)


def test_required_platform_artifacts_exist() -> None:
    diagnostics: list[str] = []
    if not (REPO_ROOT / MANIFEST_PATH).is_file():
        diagnostics.append("artifact.manifest-missing")
    if any(not (REPO_ROOT / path).is_file() for path in CONTRACT_PAGES):
        diagnostics.append("artifact.contract-page-missing")
    assert diagnostics == []


def test_production_validator_entrypoint_exists() -> None:
    assert VALIDATOR_PATH.is_file(), "artifact.validator-missing"


@pytest.mark.parametrize("path,required_terms", PAGE_REQUIRED_TERMS.items())
def test_contract_page_contains_required_clauses(
    path: pathlib.Path, required_terms: tuple[str, ...]
) -> None:
    full_path = REPO_ROOT / path
    if not full_path.is_file():
        pytest.skip("artifact.contract-page-missing")
    text = full_path.read_text(encoding="utf-8")
    diagnostics = [
        "contract.required-clause-missing"
        for term in required_terms
        if term.casefold() not in text.casefold()
    ]
    assert diagnostics == []


@pytest.mark.skipif(not VALIDATOR_PATH.is_file(), reason="artifact.validator-missing")
def test_closed_manifest_fixture_is_valid(tmp_path: pathlib.Path) -> None:
    workspace = build_workspace(tmp_path)
    assert validate(load_validator(), workspace) == []


@pytest.mark.skipif(not VALIDATOR_PATH.is_file(), reason="artifact.validator-missing")
@pytest.mark.parametrize("case", NEGATIVE_CASES, ids=lambda case: case.name)
def test_negative_mutations_emit_one_exact_category(
    tmp_path: pathlib.Path, case: NegativeCase
) -> None:
    workspace = build_workspace(tmp_path, case.mutate)
    assert validate(load_validator(), workspace) == [case.category]


def test_negative_matrix_is_exhaustive_and_category_unique() -> None:
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
        "input.clean-clone",
        "input.pinned-tools",
        "expiry.timestamp",
        "expiry.source",
        "expiry.planned",
        "expiry.candidate",
        "ownership.protocol-copy",
        "ownership.architecture-copy",
        "ownership.api-copy",
        "ownership.code-repo-substantive",
        "ownership.summary-only-substantive",
    } <= categories


@pytest.mark.skipif(not VALIDATOR_PATH.is_file(), reason="artifact.validator-missing")
def test_main_expiry_cli_is_terminal_and_category_only(tmp_path: pathlib.Path) -> None:
    def expire_planned(spec: dict[str, Any]) -> None:
        spec.update(
            {
                "mode": "main",
                "evaluated_at": "2026-01-16T00:00:00Z",
                "evaluation_source": "github.event.repository.updated_at",
            }
        )

    workspace = build_workspace(tmp_path, expire_planned)
    result = subprocess.run(
        [
            "python3",
            str(VALIDATOR_PATH),
            "--mode",
            workspace.mode,
            "--docs-ebus-root",
            str(workspace.docs_ebus),
            "--docs-eebus-root",
            str(workspace.docs_eebus),
            "--eebusreg-root",
            str(workspace.eebusreg),
            "--docs-ebus-ref",
            str(workspace.docs_ebus_ref),
            "--docs-eebus-ref",
            str(workspace.docs_eebus_ref),
            "--evaluated-at",
            str(workspace.evaluated_at),
            "--evaluation-source",
            str(workspace.evaluation_source),
            "--pinned-tool",
            "python=3.12.10",
            "--pinned-tool",
            "pyyaml=6.0.2",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == "expiry.planned\n"
    assert result.stderr == ""
