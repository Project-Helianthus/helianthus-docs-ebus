from __future__ import annotations

import copy
import hashlib
import importlib.util
import os
import pathlib
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Callable

import pytest
import yaml


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "scripts/validate_platform_contracts.py"
MANIFEST_PATH = pathlib.Path("docs/platform/manifests/eebus-doc-ownership.yaml")
WORKFLOW_PATHS = (
    REPO_ROOT / ".github/workflows/docs-ci.yml",
    REPO_ROOT / ".github/workflows/platform-contracts-combined-ref.yml",
)
REQUIREMENTS_CI_PATH = REPO_ROOT / "requirements-ci.txt"
TRUSTED_PRIOR_STEP = "Materialize trusted prior manifest"
PLATFORM_STAGE = "MSP-DOCS-PLATFORM"
E2_STAGE = "MSP-DOCS-E2"
CLEAN_STAGE = "MSP-DOCS-CLEAN"
PINNED_CI_PYTHON = "3.12.10"
PINNED_CI_PIP = "25.0.1"
PINNED_CI_REQUIREMENTS = {
    "iniconfig": "2.3.0",
    "packaging": "25.0",
    "pluggy": "1.6.0",
    "pygments": "2.19.2",
    "pyyaml": "6.0.2",
    "pytest": "9.0.2",
}
PYYAML_PORTABLE_HASHES = {
    # CPython 3.12: GitHub Linux x86_64, macOS x86_64, macOS arm64, sdist.
    "80bab7bfc629882493af4aa31a4cfa43a4c57c83813253626916b8c7ada83476",
    "c70c95198c015b85feafc136515252a261a84561b7b1d51e3384e0655ddf25ab",
    "ce826d6ef20b1bc864f0a68340c8b3287705cae2f8b4b1d932177dcc76721725",
    "d584d9ec91ad65861cc08d42e834324ef890a082e591037abe114850ff7bbc3e",
}
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
        "pip `25.0.1`",
        "--require-hashes",
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


def write_files(root: pathlib.Path, files: dict[str, str | bytes]) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")


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
    remote_full_name = (
        remote if "/" in remote else f"Project-Helianthus/{remote}"
    )
    subprocess.run(
        [
            "git",
            "remote",
            "add",
            "origin",
            f"https://github.com/{remote_full_name}.git",
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
    docs_ebus_repository: str
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
    eebusreg_initial_head = commit_fixture(
        eebusreg,
        "helianthus-eebusreg",
        remote_repository=spec["remotes"]["eebusreg"],
    )
    candidate_markers = {
        item["lifecycle"]["source_ref"] for item in spec["manifest"]["entries"]
    }
    eebusreg_head = eebusreg_initial_head
    if "__SOURCE_WRONG_COMMIT__" in candidate_markers:
        env = os.environ.copy()
        env.update(
            {
                "GIT_AUTHOR_DATE": "2026-01-02T00:00:00Z",
                "GIT_COMMITTER_DATE": "2026-01-02T00:00:00Z",
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
                "--allow-empty",
                "-qm",
                "pinned fixture",
            ],
            cwd=eebusreg,
            check=True,
            env=env,
        )
        eebusreg_head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=eebusreg, text=True
        ).strip()

    source_objects = {
        "__SOURCE_REF__": eebusreg_head,
        "__SOURCE_WRONG_COMMIT__": eebusreg_initial_head,
    }
    if "__SOURCE_TREE__" in candidate_markers:
        source_objects["__SOURCE_TREE__"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=eebusreg, text=True
        ).strip()
    if "__SOURCE_BLOB__" in candidate_markers:
        source_objects["__SOURCE_BLOB__"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD:api/lifecycle.go"],
            cwd=eebusreg,
            text=True,
        ).strip()
    if "__SOURCE_ANNOTATED_TAG__" in candidate_markers:
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Contract Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "tag",
                "-a",
                "candidate-annotated",
                "-m",
                "candidate fixture",
            ],
            cwd=eebusreg,
            check=True,
        )
        source_objects["__SOURCE_ANNOTATED_TAG__"] = subprocess.check_output(
            ["git", "rev-parse", "refs/tags/candidate-annotated"],
            cwd=eebusreg,
            text=True,
        ).strip()
    if "__SOURCE_LIGHTWEIGHT_TAG__" in candidate_markers:
        subprocess.run(
            ["git", "tag", "candidate-lightweight"], cwd=eebusreg, check=True
        )
        source_objects["__SOURCE_LIGHTWEIGHT_TAG__"] = subprocess.check_output(
            ["git", "rev-parse", "refs/tags/candidate-lightweight"],
            cwd=eebusreg,
            text=True,
        ).strip()
    for item in spec["manifest"]["entries"]:
        marker = item["lifecycle"]["source_ref"]
        if marker in source_objects:
            item["lifecycle"]["source_ref"] = source_objects[marker]

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
        docs_ebus_repository=(
            spec["remotes"]["docs_ebus"]
            if "/" in spec["remotes"]["docs_ebus"]
            else f"Project-Helianthus/{spec['remotes']['docs_ebus']}"
        ),
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


def validate(
    validator: Any,
    workspace: Workspace,
    *,
    prior_manifest: pathlib.Path | None = None,
) -> list[str]:
    diagnostics = validator.validate_workspace(
        docs_ebus_root=workspace.docs_ebus,
        docs_eebus_root=workspace.docs_eebus,
        eebusreg_root=workspace.eebusreg,
        mode="combined-ref",
        docs_ebus_ref=workspace.docs_ebus_ref,
        docs_eebus_ref=workspace.docs_eebus_ref,
        eebusreg_ref=workspace.eebusreg_ref,
        docs_ebus_repository=workspace.docs_ebus_repository,
        enforce_through=workspace.enforce_through,
        toolchain_mode=workspace.toolchain_mode,
        prior_manifest=prior_manifest,
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
    prior_manifest: pathlib.Path | None = None,
) -> list[str]:
    return validator.validate_repository(
        docs_ebus_root=root,
        mode=mode,
        enforce_through=PLATFORM_STAGE,
        toolchain_mode="supported",
        prior_manifest=prior_manifest,
        evaluated_at=evaluated_at,
        evaluation_source=evaluation_source,
    )


def write_prior_manifest(
    tmp_path: pathlib.Path, manifest: dict[str, Any]
) -> pathlib.Path:
    materialized = copy.deepcopy(manifest)
    for item in materialized["entries"]:
        if item["lifecycle"]["source_ref"] == "__SOURCE_REF__":
            item["lifecycle"]["source_ref"] = "0" * 40
    path = tmp_path / "prior-manifest.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(materialized, sort_keys=False), encoding="utf-8")
    return path


def mark_manifest_entry_withdrawn(
    manifest: dict[str, Any], entry_id: str
) -> None:
    item = next(entry for entry in manifest["entries"] if entry["id"] == entry_id)
    item.update(
        {
            "state": "withdrawn",
            "canonical": False,
            "outputs": outputs(),
            "lifecycle": lifecycle(
                created_at=item["lifecycle"]["created_at"],
                source_issue=item["lifecycle"]["source_issue"],
                source_pr=item["lifecycle"]["source_pr"],
                cleanup_required=True,
            ),
        }
    )


def trusted_prior_workflow_step(path: pathlib.Path) -> dict[str, Any]:
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            if step.get("name") == TRUSTED_PRIOR_STEP:
                return step
    raise AssertionError(f"{TRUSTED_PRIOR_STEP!r} missing from {path.name}")


def locked_requirements(path: pathlib.Path) -> dict[str, tuple[str, set[str]]]:
    blocks: list[str] = []
    current: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if raw_line[:1].isspace():
            assert current, f"orphan requirement continuation in {path.name}"
            current.append(line.removesuffix("\\").strip())
            continue
        if current:
            blocks.append(" ".join(current))
        current = [line.removesuffix("\\").strip()]
    if current:
        blocks.append(" ".join(current))

    parsed: dict[str, tuple[str, set[str]]] = {}
    for block in blocks:
        match = re.match(r"([A-Za-z0-9_.-]+)==([^\s]+)", block)
        assert match is not None, f"unpinned requirement: {block}"
        name = match.group(1).casefold().replace("_", "-")
        hashes = set(re.findall(r"--hash=sha256:([0-9a-f]{64})(?:\s|$)", block))
        assert name not in parsed, f"duplicate requirement: {name}"
        parsed[name] = (match.group(2), hashes)
    return parsed


def create_trusted_base_fixture(root: pathlib.Path, kind: str) -> tuple[str, bytes]:
    root.mkdir(parents=True)
    manifest = root / MANIFEST_PATH
    expected = b"schema: trusted-base-fixture\n"
    if kind == "regular":
        manifest.parent.mkdir(parents=True)
        manifest.write_bytes(expected)
    elif kind == "absent":
        (root / "README.md").write_text("# Prior without manifest\n", encoding="utf-8")
    elif kind == "dangling-symlink":
        manifest.parent.mkdir(parents=True)
        manifest.symlink_to("missing-manifest.yaml")
    elif kind == "wrong-type":
        manifest.mkdir(parents=True)
        (manifest / "child.yaml").write_text("not a manifest\n", encoding="utf-8")
    else:
        raise AssertionError(f"unknown fixture kind: {kind}")
    return commit_fixture(root, "helianthus-docs-ebus"), expected


def run_trusted_prior_workflow_step(
    tmp_path: pathlib.Path, workflow_path: pathlib.Path, kind: str
) -> tuple[subprocess.CompletedProcess[str], pathlib.Path, bytes]:
    workspace = tmp_path / "workspace"
    base_root = workspace / "checkouts/docs-ebus-base"
    trusted_ref, expected = create_trusted_base_fixture(base_root, kind)
    runner_temp = tmp_path / "runner-temp"
    runner_temp.mkdir()
    github_output = tmp_path / "github-output.txt"
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_WORKSPACE": str(workspace),
            "RUNNER_TEMP": str(runner_temp),
            "GITHUB_RUN_ID": "342",
            "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_OUTPUT": str(github_output),
            "TRUSTED_BASE_REF": trusted_ref,
        }
    )
    script = trusted_prior_workflow_step(workflow_path)["run"]
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", script],
        check=False,
        capture_output=True,
        text=True,
        cwd=workspace,
        env=env,
    )
    return result, github_output, expected


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


def duplicate_surface(spec: dict[str, Any]) -> None:
    duplicate = copy.deepcopy(find_entry(spec, "eebus-architecture-planned"))
    duplicate["id"] = "duplicate-architecture-surface"
    duplicate["owner"]["path"] = "architecture/future.md"
    duplicate["source"]["path"] = "architecture/future.md"
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


def reassign_protocol_to_code_readme(spec: dict[str, Any]) -> None:
    item = find_entry(spec, "eebus-protocol")
    item["owner"] = {
        "repository": "helianthus-eebusreg",
        "path": "README.md",
    }
    item["source"] = copy.deepcopy(item["owner"])


def reassign_architecture_to_platform_docs(spec: dict[str, Any]) -> None:
    path = "docs/platform/future-runtime.md"
    spec["docs_ebus"][path] = "# Future Runtime\n"
    item = find_entry(spec, "eebus-architecture-planned")
    item["owner"] = {
        "repository": "helianthus-docs-ebus",
        "path": path,
    }
    item["source"] = copy.deepcopy(item["owner"])


def move_api_outside_api_prefix(spec: dict[str, Any]) -> None:
    path = "reference/_candidate/lifecycle.md"
    spec["docs_eebus"][path] = "# Candidate Go API\n"
    find_entry(spec, "eebus-api-candidate")["owner"]["path"] = path


def reassign_platform_to_protocol_docs(spec: dict[str, Any]) -> None:
    path = "protocols/platform-envelope.md"
    spec["docs_eebus"][path] = "# Platform Envelope\n"
    item = find_entry(spec, "platform-contracts")
    item["owner"] = {
        "repository": "helianthus-docs-eebus",
        "path": path,
    }
    item["source"] = copy.deepcopy(item["owner"])


def move_code_docs_outside_docs_prefix(spec: dict[str, Any]) -> None:
    spec["eebusreg"]["legacy/README.md"] = "# Legacy Runtime Docs\n"
    item = find_entry(spec, "code-repo-docs-planned")
    item["owner"]["path"] = "legacy"
    item["source"]["path"] = "legacy"


def move_summary_from_readme(spec: dict[str, Any]) -> None:
    path = "SUMMARY.md"
    spec["eebusreg"][path] = "# Summary\n"
    find_entry(spec, "code-repo-summary-planned")["owner"]["path"] = path


def mark_protocol_noncanonical(spec: dict[str, Any]) -> None:
    find_entry(spec, "eebus-protocol")["canonical"] = False


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
        "protocol_reassigned_to_code_readme",
        "ownership.surface-binding",
        reassign_protocol_to_code_readme,
    ),
    NegativeCase(
        "architecture_reassigned_to_platform_docs",
        "ownership.surface-binding",
        reassign_architecture_to_platform_docs,
    ),
    NegativeCase(
        "api_moved_outside_api_prefix",
        "ownership.surface-binding",
        move_api_outside_api_prefix,
    ),
    NegativeCase(
        "platform_reassigned_to_protocol_docs",
        "ownership.surface-binding",
        reassign_platform_to_protocol_docs,
    ),
    NegativeCase(
        "code_docs_moved_outside_docs_prefix",
        "ownership.surface-binding",
        move_code_docs_outside_docs_prefix,
    ),
    NegativeCase(
        "summary_moved_from_readme",
        "ownership.surface-binding",
        move_summary_from_readme,
    ),
    NegativeCase(
        "protocol_marked_noncanonical",
        "ownership.canonical-state",
        mark_protocol_noncanonical,
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
            "architecture/serial=redacted-value",
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
        "forward_autolink",
        "link.forward",
        append_platform(
            "<https://github.com/Project-Helianthus/helianthus-docs-eebus/"
            "blob/main/architecture/future.md>\n"
        ),
    ),
    NegativeCase(
        "forward_bare_github_url",
        "link.forward",
        append_platform(
            "Unmerged: https://github.com/Project-Helianthus/"
            "helianthus-docs-eebus/blob/main/architecture/future.md.\n"
        ),
    ),
    NegativeCase(
        "forward_mixed_case_repository_path",
        "link.forward",
        append_platform(
            "[Unmerged](../../HeLiAnThUs-DoCs-EeBuS/architecture/future.md)\n"
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
        "summary_substantive_at_clean",
        "ownership.summary-only-substantive",
        clean_with_substantive_summary,
    ),
)


def test_required_platform_artifacts_exist() -> None:
    assert (REPO_ROOT / MANIFEST_PATH).is_file()
    assert all((REPO_ROOT / path).is_file() for path in CONTRACT_PAGES)


def test_canonical_repository_validation_passes() -> None:
    assert repository_validate(load_validator(), REPO_ROOT) == []


def test_production_validator_entrypoint_exists() -> None:
    assert VALIDATOR_PATH.is_file()


@pytest.mark.parametrize("workflow_path", WORKFLOW_PATHS, ids=lambda path: path.stem)
def test_trusted_prior_workflow_static_contract(workflow_path: pathlib.Path) -> None:
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    checkout_paths = {
        step.get("with", {}).get("path")
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if step.get("uses", "").startswith("actions/checkout@")
    }
    candidate = pathlib.PurePosixPath("checkouts/docs-ebus")
    trusted = pathlib.PurePosixPath("checkouts/docs-ebus-base")
    assert candidate.as_posix() in checkout_paths
    assert trusted.as_posix() in checkout_paths
    assert candidate.parent == trusted.parent
    assert not trusted.is_relative_to(candidate)

    step = trusted_prior_workflow_step(workflow_path)
    script = step["run"]
    assert re.search(r"\[\[\s+-e\b", script) is None
    assert "sparse-checkout" not in workflow_path.read_text(encoding="utf-8")
    assert 'cat-file -t "${TRUSTED_BASE_REF}"' in script
    assert 'ls-tree "${trusted_commit}" -- "${prefix}"' in script
    assert '"${mode}" != "040000"' in script
    assert '! "${mode}" =~ ^100(644|755)$' in script
    assert 'cat-file blob "${manifest_oid}"' in script
    assert "${RUNNER_TEMP}/helianthus-trusted-prior-" in script


def test_ci_requirement_lock_is_complete_and_portable() -> None:
    requirements = locked_requirements(REQUIREMENTS_CI_PATH)
    assert {
        name: version for name, (version, _) in requirements.items()
    } == PINNED_CI_REQUIREMENTS
    assert all(hashes for _, hashes in requirements.values())
    assert all(len(hashes) >= 2 for _, hashes in requirements.values())
    assert PYYAML_PORTABLE_HASHES <= requirements["pyyaml"][1]


@pytest.mark.parametrize("workflow_path", WORKFLOW_PATHS, ids=lambda path: path.stem)
def test_ci_workflow_uses_locked_python_pip_and_dependencies(
    workflow_path: pathlib.Path,
) -> None:
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    steps = [
        step
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
    ]
    python_steps = [
        step
        for step in steps
        if step.get("uses", "").startswith("actions/setup-python@")
    ]
    assert len(python_steps) == 1
    python_step = python_steps[0]
    assert python_step["with"]["python-version"] == PINNED_CI_PYTHON
    assert python_step.get("env", {}).get("PIP_NO_INDEX") == "1"
    assert "helianthus-pip-bootstrap" in python_step.get("env", {}).get(
        "PIP_FIND_LINKS", ""
    )

    bootstrap_artifact_steps = [
        step
        for step in steps
        if step.get("name") == "Prepare hash-locked pip bootstrap"
    ]
    assert len(bootstrap_artifact_steps) == 1
    bootstrap_artifact = bootstrap_artifact_steps[0]["run"]
    assert "pip-25.0.1-py3-none-any.whl" in bootstrap_artifact
    assert (
        "c46efd13b6aa8279f33f2864459c8ce587ea6a1a59ee20de055868d8f7688f7f"
        in bootstrap_artifact
    )
    assert "sha256sum --check --strict" in bootstrap_artifact

    bootstrap_steps = [
        step for step in steps if step.get("name") == "Verify pinned Python and pip"
    ]
    assert len(bootstrap_steps) == 1
    bootstrap = bootstrap_steps[0]["run"]
    assert "sys.version_info[:3]" in bootstrap
    assert "(3, 12, 10)" in bootstrap
    assert 'version("pip")' in bootstrap
    assert f'"{PINNED_CI_PIP}"' in bootstrap

    pip_install_steps = [
        step
        for step in steps
        if "python -m pip install" in step.get("run", "")
    ]
    assert len(pip_install_steps) == 1
    pip_install_step = pip_install_steps[0]
    assert "PIP_NO_INDEX" not in pip_install_step.get("env", {})
    install = pip_install_step["run"]
    assert "--require-hashes" in install
    assert "--no-deps" in install
    assert "--no-build-isolation" in install
    assert "requirements-ci.txt" in install


def test_combined_ref_expiry_uses_trusted_validator_and_runner_clock() -> None:
    workflow = yaml.safe_load(
        (
            REPO_ROOT / ".github/workflows/platform-contracts-combined-ref.yml"
        ).read_text(encoding="utf-8")
    )
    steps = workflow["jobs"]["validate"]["steps"]
    expiry_steps = [
        step
        for step in steps
        if step.get("name") == "Enforce trusted manifest expiry"
    ]
    assert len(expiry_steps) == 1
    step = expiry_steps[0]
    assert "if" not in step
    assert "RAW_EVALUATED_AT" not in step.get("env", {})
    assert step["env"]["ENFORCE_THROUGH"] == "${{ inputs.enforce_through }}"
    script = step["run"]
    assert "datetime.datetime.now(datetime.timezone.utc)" in script
    assert '.replace("+00:00", "Z")' in script
    assert (
        "python3 checkouts/docs-ebus-validator/scripts/validate_platform_contracts.py"
        in script
    )
    assert "python3 checkouts/docs-ebus/scripts/validate_platform_contracts.py" not in script
    assert "--mode main-expiry" in script
    assert "--docs-ebus-root checkouts/docs-ebus" in script
    assert '--evaluated-at "${evaluated_at}"' in script
    assert "github.event.head_commit.timestamp" not in script
    assert "--evaluation-source github.runner.utc_now" in script

    caller = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/docs-ci.yml").read_text(encoding="utf-8")
    )
    candidate_steps = caller["jobs"]["markdown-checks"]["steps"]
    assert all(step.get("name") != "Enforce manifest expiry" for step in candidate_steps)


def test_combined_ref_workflow_checks_out_pr_head_repository() -> None:
    caller = (REPO_ROOT / ".github/workflows/docs-ci.yml").read_text(
        encoding="utf-8"
    )
    reusable = (
        REPO_ROOT / ".github/workflows/platform-contracts-combined-ref.yml"
    ).read_text(encoding="utf-8")

    assert (
        "docs_ebus_repository: "
        "${{ github.event.pull_request.head.repo.full_name }}" in caller
    )
    assert "docs_ebus_ref: ${{ github.event.pull_request.head.sha }}" in caller
    assert reusable.count("docs_ebus_repository:") >= 2
    assert "DOCS_EBUS_REPOSITORY: ${{ inputs.docs_ebus_repository }}" in reusable
    assert "repository: ${{ inputs.docs_ebus_repository }}" in reusable
    assert '--docs-ebus-repository "${{ inputs.docs_ebus_repository }}"' in reusable
    assert "repository='^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$'" in reusable
    assert "repository: Project-Helianthus/helianthus-docs-ebus" in reusable


def test_combined_ref_caller_pins_trusted_reusable_workflow() -> None:
    caller = (REPO_ROOT / ".github/workflows/docs-ci.yml").read_text(
        encoding="utf-8"
    )

    trusted_call = (
        "uses: Project-Helianthus/helianthus-docs-ebus/"
        ".github/workflows/platform-contracts-combined-ref.yml@"
        "b612a1168c6509d04da13243e7d6cef3f2318dd7"
    )
    assert trusted_call in caller
    assert "uses: ./.github/workflows/platform-contracts-combined-ref.yml" not in caller


def test_combined_ref_executes_only_trusted_validator_checkout() -> None:
    reusable = (
        REPO_ROOT / ".github/workflows/platform-contracts-combined-ref.yml"
    ).read_text(encoding="utf-8")

    assert "bootstrap_base=114072fe8bdf027cfdd3472d7f2b0896a2496db4" in reusable
    assert (
        "bootstrap_validator=c4d87b2d1fbdc9627a3a2aedaae298547f1908d2"
        in reusable
    )
    assert "path: checkouts/docs-ebus-validator" in reusable
    assert "repository: Project-Helianthus/helianthus-docs-ebus" in reusable
    assert "cat-file -t \"${TRUSTED_VALIDATOR_REF}\"" in reusable
    assert "checkouts/docs-ebus-validator/requirements-ci.txt" in reusable
    assert (
        "checkouts/docs-ebus-validator/scripts/validate_platform_contracts.py"
        in reusable
    )
    assert "-r checkouts/docs-ebus/requirements-ci.txt" not in reusable
    assert (
        "python3 checkouts/docs-ebus/scripts/validate_platform_contracts.py"
        not in reusable
    )


def test_combined_ref_validates_milestone_before_shell_use() -> None:
    reusable = (
        REPO_ROOT / ".github/workflows/platform-contracts-combined-ref.yml"
    ).read_text(encoding="utf-8")

    assert reusable.count("ENFORCE_THROUGH: ${{ inputs.enforce_through }}") == 3
    assert "MSP-DOCS-PLATFORM|MSP-DOCS-E2|MSP-DOCS-CLEAN" in reusable
    assert '--enforce-through "${ENFORCE_THROUGH}"' in reusable
    assert '--enforce-through "${{ inputs.enforce_through }}"' not in reusable


@pytest.mark.parametrize("workflow_path", WORKFLOW_PATHS, ids=lambda path: path.stem)
def test_trusted_prior_workflow_materializes_inspected_blob(
    tmp_path: pathlib.Path, workflow_path: pathlib.Path
) -> None:
    result, github_output, expected = run_trusted_prior_workflow_step(
        tmp_path, workflow_path, "regular"
    )
    assert result.returncode == 0, result.stderr
    output = github_output.read_text(encoding="utf-8").strip()
    assert output.startswith("path=")
    materialized = pathlib.Path(output.removeprefix("path="))
    assert materialized.read_bytes() == expected
    assert materialized.is_relative_to(tmp_path / "runner-temp")


@pytest.mark.parametrize("workflow_path", WORKFLOW_PATHS, ids=lambda path: path.stem)
def test_trusted_prior_workflow_accepts_only_true_manifest_absence(
    tmp_path: pathlib.Path, workflow_path: pathlib.Path
) -> None:
    result, github_output, _ = run_trusted_prior_workflow_step(
        tmp_path, workflow_path, "absent"
    )
    assert result.returncode == 0, result.stderr
    assert github_output.read_text(encoding="utf-8") == "path=\n"


@pytest.mark.parametrize("workflow_path", WORKFLOW_PATHS, ids=lambda path: path.stem)
@pytest.mark.parametrize("kind", ("dangling-symlink", "wrong-type"))
def test_trusted_prior_workflow_rejects_nonregular_manifest_objects(
    tmp_path: pathlib.Path, workflow_path: pathlib.Path, kind: str
) -> None:
    result, _, _ = run_trusted_prior_workflow_step(tmp_path, workflow_path, kind)
    assert result.returncode != 0


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


@pytest.mark.parametrize(
    "source_marker,expected",
    (
        ("__SOURCE_TREE__", ["state.candidate"]),
        ("__SOURCE_BLOB__", ["state.candidate"]),
        ("__SOURCE_ANNOTATED_TAG__", ["state.candidate"]),
        ("__SOURCE_WRONG_COMMIT__", ["state.candidate"]),
        ("__SOURCE_LIGHTWEIGHT_TAG__", []),
        ("__SOURCE_REF__", []),
    ),
    ids=(
        "head-tree",
        "source-blob",
        "annotated-tag-object",
        "wrong-commit",
        "lightweight-tag-commit",
        "pinned-commit",
    ),
)
def test_candidate_source_ref_is_the_pinned_commit_object(
    tmp_path: pathlib.Path, source_marker: str, expected: list[str]
) -> None:
    def mutate(spec: dict[str, Any]) -> None:
        find_entry(spec, "eebus-api-candidate")["lifecycle"]["source_ref"] = (
            source_marker
        )

    workspace = build_workspace(tmp_path, mutate)
    assert validate(load_validator(), workspace) == expected


@pytest.mark.parametrize(
    "path",
    (
        "architecture/name:variant.md",
        "architecture/<draft>.md",
        'architecture/quote"name.md',
        "architecture/pipe|name.md",
        "architecture/query?.md",
        "architecture/star*.md",
        "architecture/CON",
        "architecture/prn.md",
        "architecture/AUX.txt",
        "architecture/nul.reference.md",
        "architecture/COM1.md",
        "architecture/com9",
        "architecture/LPT1.md",
        "architecture/lpt9.reference",
        "architecture/trailing.",
        "architecture/trailing ",
        "architecture/nested./page.md",
        "architecture/nested /page.md",
    ),
)
def test_manifest_paths_reject_windows_invalid_segments(
    tmp_path: pathlib.Path, path: str
) -> None:
    mutate = set_nested("eebus-architecture-planned", "owner", "path", path)
    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == [
        "path.absolute"
    ]


@pytest.mark.parametrize(
    "path",
    (
        "architecture/console.md",
        "architecture/com10.md",
        "architecture/lpt0.md",
        "architecture/auxiliary.md",
        "architecture/con-file.md",
        "architecture/question-name.md",
    ),
)
def test_manifest_paths_preserve_valid_windows_near_misses(
    tmp_path: pathlib.Path, path: str
) -> None:
    mutate = set_nested("eebus-architecture-planned", "owner", "path", path)
    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == []


@pytest.mark.parametrize(
    "mutate,expected",
    (
        (duplicate_surface, ["ownership.surface-duplicate"]),
        (
            duplicate_pair,
            ["ownership.pair-duplicate", "ownership.surface-duplicate"],
        ),
        (
            duplicate_canonical,
            ["ownership.canonical-duplicate", "ownership.surface-duplicate"],
        ),
    ),
    ids=("duplicate-surface", "duplicate-pair", "duplicate-canonical"),
)
def test_every_surface_has_exactly_one_manifest_entry(
    tmp_path: pathlib.Path,
    mutate: Callable[[dict[str, Any]], None],
    expected: list[str],
) -> None:
    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == expected


def test_negative_matrix_has_broad_unique_category_coverage() -> None:
    categories = {case.category for case in NEGATIVE_CASES} | {
        "ownership.surface-duplicate",
        "ownership.pair-duplicate",
        "ownership.canonical-duplicate",
        "ownership.code-repo-substantive",
    }
    assert SURFACES == {item["surface"] for item in base_manifest()["entries"]}
    assert {
        "manifest.missing",
        "manifest.schema",
        "manifest.version",
        "ownership.surface-missing",
        "ownership.surface-duplicate",
        "ownership.pair-duplicate",
        "ownership.canonical-duplicate",
        "ownership.surface-binding",
        "ownership.canonical-state",
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
    assert validate(load_validator(), clean_required) == [
        "enforcement.transition",
        "ownership.code-repo-substantive",
    ]


def test_clean_transition_passes_after_docs_removed_and_summary_trimmed(
    tmp_path: pathlib.Path,
) -> None:
    workspace = build_workspace(tmp_path, transition_clean)
    assert validate(load_validator(), workspace) == []


@pytest.mark.parametrize(
    "path,text",
    (
        (
            "ARCHITECTURE.md",
            "# Runtime Architecture\n\nThe eeBUS runtime MUST persist trust state.\n",
        ),
        (
            "notes/alternate/protocol.rst",
            "Protocol Notes\n\nSHIP peers MUST negotiate before sending messages.\n",
        ),
        (
            "reference/API.adoc",
            "= API\n\nThe eeBUS Go API MUST expose lifecycle methods.\n",
        ),
    ),
    ids=("root-architecture", "nested-protocol", "nested-api"),
)
def test_clean_scans_documentation_authority_outside_docs(
    tmp_path: pathlib.Path, path: str, text: str
) -> None:
    def mutate(spec: dict[str, Any]) -> None:
        transition_clean(spec)
        spec["eebusreg"][path] = text

    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == [
        "ownership.code-repo-substantive"
    ]


@pytest.mark.parametrize(
    "path",
    (
        "AUTHORITY.txt",
        "notes/nested/AUTHORITY.txt",
        "PROTOCOL.rst",
        "notes/nested/PROTOCOL.rst",
        "PROTOCOL.adoc",
        "notes/nested/PROTOCOL.adoc",
    ),
    ids=(
        "root-txt",
        "nested-txt",
        "root-rst",
        "nested-rst",
        "root-adoc",
        "nested-adoc",
    ),
)
def test_clean_scans_indented_non_markdown_authority(
    tmp_path: pathlib.Path, path: str
) -> None:
    def mutate(spec: dict[str, Any]) -> None:
        transition_clean(spec)
        spec["eebusreg"][path] = (
            "    SHIP peers MUST negotiate before sending protocol messages.\n"
        )

    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == [
        "ownership.code-repo-substantive"
    ]


@pytest.mark.parametrize(
    "path,text",
    (
        (
            "EXAMPLES.md",
            "```text\nSHIP peers MUST negotiate before sending protocol messages.\n```\n",
        ),
        (
            "notes/nested/EXAMPLES.md",
            "    SHIP peers MUST negotiate before sending protocol messages.\n",
        ),
    ),
    ids=("fenced-markdown", "indented-markdown"),
)
def test_clean_keeps_markdown_code_examples_non_authoritative(
    tmp_path: pathlib.Path, path: str, text: str
) -> None:
    def mutate(spec: dict[str, Any]) -> None:
        transition_clean(spec)
        spec["eebusreg"][path] = text

    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == []


@pytest.mark.parametrize(
    "path",
    (
        "generated/ARCHITECTURE.md",
        "build/reference/PROTOCOL.rst",
        "vendor/package/API.adoc",
        "cache/docs/DESIGN.txt",
        ".cache/docs/ARCHITECTURE.md",
    ),
)
def test_clean_excludes_nonpublishable_documentation_directories(
    tmp_path: pathlib.Path, path: str
) -> None:
    def mutate(spec: dict[str, Any]) -> None:
        transition_clean(spec)
        spec["eebusreg"][path] = "SHIP peers MUST negotiate sessions.\n"

    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == []


def test_clean_excludes_binary_documentation_like_files(
    tmp_path: pathlib.Path,
) -> None:
    def mutate(spec: dict[str, Any]) -> None:
        transition_clean(spec)
        spec["eebusreg"]["ARCHITECTURE.md"] = (
            b"\x00SHIP peers MUST negotiate sessions.\xff"
        )

    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == []


def test_clean_preserves_the_minimal_noncanonical_readme_summary(
    tmp_path: pathlib.Path,
) -> None:
    assert validate(load_validator(), build_workspace(tmp_path, transition_clean)) == []


def test_clean_rejects_retained_withdrawn_code_repo_artifacts(
    tmp_path: pathlib.Path,
) -> None:
    assert validate(load_validator(), build_workspace(tmp_path, clean_with_docs)) == [
        "artifact.withdrawn",
        "ownership.code-repo-substantive",
    ]


def test_clean_keeps_code_repo_gate_for_nonwithdrawn_entries(
    tmp_path: pathlib.Path,
) -> None:
    def mutate(spec: dict[str, Any]) -> None:
        transition_clean(spec)
        code = find_entry(spec, "code-repo-docs-planned")
        code.update(
            {
                "state": "planned",
                "canonical": False,
                "outputs": outputs(),
                "lifecycle": lifecycle(
                    created_at="2026-01-01T00:00:00Z",
                    expires_at="2026-01-15T00:00:00Z",
                    source_issue=(
                        "Project-Helianthus/helianthus-execution-plans#58"
                    ),
                ),
            }
        )
        spec["eebusreg"]["docs/legacy.md"] = "# Retained code docs\n"

    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == [
        "enforcement.transition",
        "ownership.code-repo-substantive",
    ]


def withdraw_api_candidate(
    spec: dict[str, Any],
    *,
    remove_owner: bool = True,
    remove_source: bool = True,
) -> None:
    item = find_entry(spec, "eebus-api-candidate")
    item.update(
        {
            "state": "withdrawn",
            "canonical": False,
            "outputs": outputs(),
            "lifecycle": lifecycle(
                created_at="2026-01-15T00:00:00Z",
                source_pr="Project-Helianthus/helianthus-eebusreg#20",
                cleanup_required=True,
            ),
        }
    )
    if remove_owner:
        del spec["docs_eebus"]["api/_candidate/lifecycle.md"]
    if remove_source:
        del spec["eebusreg"]["api/lifecycle.go"]


@pytest.mark.parametrize(
    "stage_transition",
    (
        lambda spec: None,
        transition_e2,
        transition_clean,
    ),
    ids=("before-target", "at-target", "after-target"),
)
def test_candidate_withdrawal_is_terminal_across_staged_enforcement(
    tmp_path: pathlib.Path,
    stage_transition: Callable[[dict[str, Any]], None],
) -> None:
    def mutate(spec: dict[str, Any]) -> None:
        stage_transition(spec)
        withdraw_api_candidate(spec)

    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == []


@pytest.mark.parametrize(
    "entry_id",
    ("eebus-architecture-planned", "code-repo-summary-planned"),
    ids=("architecture-active-required", "summary-active-required"),
)
def test_withdrawal_cannot_cancel_required_active_state(entry_id: str) -> None:
    manifest = base_manifest()
    find_entry({"manifest": manifest}, entry_id)["state"] = "withdrawn"

    assert load_validator()._enforcement_categories(manifest, CLEAN_STAGE) == {
        "enforcement.transition"
    }


def test_withdrawn_candidate_rejects_stale_owner_artifact(
    tmp_path: pathlib.Path,
) -> None:
    def mutate(spec: dict[str, Any]) -> None:
        withdraw_api_candidate(spec, remove_owner=False)

    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == [
        "artifact.withdrawn"
    ]


def test_withdrawn_candidate_rejects_stale_source_artifact(
    tmp_path: pathlib.Path,
) -> None:
    def mutate(spec: dict[str, Any]) -> None:
        withdraw_api_candidate(spec, remove_source=False)

    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == [
        "artifact.withdrawn"
    ]


def test_withdrawn_candidate_rejects_dangling_source_symlink(
    tmp_path: pathlib.Path,
) -> None:
    def mutate(spec: dict[str, Any]) -> None:
        withdraw_api_candidate(spec)
        spec["symlinks"]["eebusreg"]["api/lifecycle.go"] = "missing.go"

    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == [
        "artifact.withdrawn"
    ]


def test_withdrawn_code_repo_cleanup_is_immediate_before_clean(
    tmp_path: pathlib.Path,
) -> None:
    def mutate(spec: dict[str, Any]) -> None:
        code = find_entry(spec, "code-repo-docs-planned")
        code.update(
            {
                "state": "withdrawn",
                "canonical": False,
                "outputs": outputs(),
                "lifecycle": lifecycle(
                    created_at="2026-01-01T00:00:00Z",
                    source_issue=(
                        "Project-Helianthus/helianthus-execution-plans#58"
                    ),
                    cleanup_required=True,
                ),
            }
        )

    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == [
        "artifact.withdrawn"
    ]


@pytest.mark.parametrize(
    "entry_id,current_mutation",
    (
        ("eebus-api-candidate", lambda spec: None),
        ("eebus-architecture-planned", lambda spec: None),
        ("platform-contracts", lambda spec: None),
    ),
    ids=("withdrawn-to-candidate", "withdrawn-to-planned", "withdrawn-to-active"),
)
def test_withdrawn_history_rejects_every_nonterminal_state(
    tmp_path: pathlib.Path,
    entry_id: str,
    current_mutation: Callable[[dict[str, Any]], None],
) -> None:
    prior = base_manifest()
    mark_manifest_entry_withdrawn(prior, entry_id)
    prior_path = write_prior_manifest(tmp_path, prior)
    workspace = build_workspace(tmp_path / "current", current_mutation)

    assert validate(
        load_validator(), workspace, prior_manifest=prior_path
    ) == ["history.withdrawn-terminal"]


@pytest.mark.parametrize(
    "entry_id,replacement_id",
    (
        ("eebus-architecture-planned", "architecture-resurrected"),
        ("eebus-api-candidate", "api-resurrected"),
        ("platform-contracts", "platform-resurrected"),
    ),
    ids=("new-id-planned", "new-id-candidate", "new-id-active"),
)
def test_withdrawn_surface_rejects_new_id_resurrection_in_every_state(
    tmp_path: pathlib.Path, entry_id: str, replacement_id: str
) -> None:
    prior = base_manifest()
    mark_manifest_entry_withdrawn(prior, entry_id)
    prior_path = write_prior_manifest(tmp_path, prior)

    def replace_id(spec: dict[str, Any]) -> None:
        find_entry(spec, entry_id)["id"] = replacement_id

    workspace = build_workspace(tmp_path / "current", replace_id)
    assert validate(load_validator(), workspace, prior_manifest=prior_path) == [
        "history.withdrawn-terminal"
    ]


def test_withdrawn_surface_rejects_duplicate_replacement_entry(
    tmp_path: pathlib.Path,
) -> None:
    prior = base_manifest()
    mark_manifest_entry_withdrawn(prior, "eebus-api-candidate")
    prior_path = write_prior_manifest(tmp_path, prior)

    def add_replacement(spec: dict[str, Any]) -> None:
        withdraw_api_candidate(spec)
        spec["manifest"]["entries"].append(
            entry(
                "api-replacement-planned",
                "api",
                "helianthus-docs-eebus",
                "api/_candidate/replacement.md",
                "helianthus-eebusreg",
                "api/replacement.go",
                "planned",
                canonical=False,
                output=outputs(),
                state_lifecycle=lifecycle(
                    created_at="2026-01-01T00:00:00Z",
                    expires_at="2026-01-15T00:00:00Z",
                    source_issue="Project-Helianthus/helianthus-eebusreg#20",
                ),
                state_enforcement=enforcement(E2_STAGE, "candidate"),
            )
        )

    workspace = build_workspace(tmp_path / "current", add_replacement)
    assert validate(load_validator(), workspace, prior_manifest=prior_path) == [
        "history.withdrawn-terminal",
        "ownership.surface-duplicate",
    ]


def test_withdrawn_tombstone_ownership_is_immutable(
    tmp_path: pathlib.Path,
) -> None:
    prior = base_manifest()
    mark_manifest_entry_withdrawn(prior, "eebus-api-candidate")
    prior_path = write_prior_manifest(tmp_path, prior)

    def move_tombstone(spec: dict[str, Any]) -> None:
        withdraw_api_candidate(spec)
        find_entry(spec, "eebus-api-candidate")["owner"]["path"] = (
            "api/_candidate/renamed.md"
        )

    workspace = build_workspace(tmp_path / "current", move_tombstone)
    assert validate(
        load_validator(), workspace, prior_manifest=prior_path
    ) == ["history.tombstone-identity"]


@pytest.mark.parametrize(
    "path,value",
    (
        (("canonical",), True),
        (("owner", "repository"), "helianthus-docs-ebus"),
        (("owner", "path"), "api/_candidate/moved.md"),
        (("source", "repository"), "helianthus-docs-eebus"),
        (("source", "path"), "api/moved.go"),
        (("outputs", "candidate"), True),
        (("outputs", "stable_navigation"), True),
        (("outputs", "search"), True),
        (("outputs", "sitemap"), True),
        (("outputs", "versioned_bundle"), True),
        (("outputs", "release_bundle"), True),
        (("lifecycle", "created_at"), "2026-01-16T00:00:00Z"),
        (("lifecycle", "expires_at"), "2026-02-15T00:00:00Z"),
        (("lifecycle", "source_issue"), "Project-Helianthus/plan#1"),
        (("lifecycle", "source_pr"), "Project-Helianthus/plan#2"),
        (("lifecycle", "source_ref"), "0" * 40),
        (("lifecycle", "content_sha256"), "0" * 64),
        (("lifecycle", "approved_at"), "2026-01-16T00:00:00Z"),
        (("lifecycle", "frozen_at"), "2026-01-17T00:00:00Z"),
        (("lifecycle", "cleanup_required"), False),
        (("enforcement", "milestone"), CLEAN_STAGE),
        (("enforcement", "required_state"), "active"),
        (("future_metadata",), {"owner": "changed"}),
        (("owner", "future_metadata"), "changed"),
    ),
    ids=lambda value: ".".join(value) if isinstance(value, tuple) else None,
)
def test_withdrawn_tombstone_rejects_every_deep_entry_mutation(
    tmp_path: pathlib.Path,
    path: tuple[str, ...],
    value: Any,
) -> None:
    prior = base_manifest()
    mark_manifest_entry_withdrawn(prior, "eebus-api-candidate")
    prior_path = write_prior_manifest(tmp_path, prior)
    current = copy.deepcopy(prior)
    item = find_entry({"manifest": current}, "eebus-api-candidate")
    target = item
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    assert load_validator()._history_categories(current, prior_path) == {
        "history.tombstone-identity"
    }


def test_normal_first_withdrawal_transition_passes(
    tmp_path: pathlib.Path,
) -> None:
    prior_path = write_prior_manifest(tmp_path, base_manifest())
    workspace = build_workspace(tmp_path / "current", withdraw_api_candidate)
    assert validate(load_validator(), workspace, prior_manifest=prior_path) == []


def test_first_manifest_introduction_passes_without_prior_manifest(
    tmp_path: pathlib.Path,
) -> None:
    assert validate(load_validator(), build_workspace(tmp_path)) == []


@pytest.mark.parametrize("contents", ("entries: [", "schema: incomplete\n"))
def test_explicit_malformed_prior_manifest_fails_closed(
    tmp_path: pathlib.Path, contents: str
) -> None:
    prior_path = tmp_path / "prior-manifest.yaml"
    prior_path.write_text(contents, encoding="utf-8")
    workspace = build_workspace(tmp_path / "current")
    assert validate(
        load_validator(), workspace, prior_manifest=prior_path
    ) == ["history.prior-manifest"]


def test_explicit_missing_prior_manifest_fails_closed(
    tmp_path: pathlib.Path,
) -> None:
    workspace = build_workspace(tmp_path / "current")
    assert validate(
        load_validator(),
        workspace,
        prior_manifest=tmp_path / "missing-prior.yaml",
    ) == ["history.prior-manifest"]


def test_explicit_prior_manifest_rejects_symlinked_path_component(
    tmp_path: pathlib.Path,
) -> None:
    trusted = tmp_path / "trusted"
    prior_path = write_prior_manifest(trusted, base_manifest())
    linked = tmp_path / "linked"
    linked.symlink_to(trusted, target_is_directory=True)
    workspace = build_workspace(tmp_path / "current")

    assert validate(
        load_validator(),
        workspace,
        prior_manifest=linked / prior_path.name,
    ) == ["history.prior-manifest"]


def test_normal_nonterminal_history_progression_passes(
    tmp_path: pathlib.Path,
) -> None:
    prior_path = write_prior_manifest(tmp_path, base_manifest())
    workspace = build_workspace(tmp_path / "current", transition_e2)
    assert validate(load_validator(), workspace, prior_manifest=prior_path) == []


def test_candidate_target_cannot_activate_instead_of_reaching_required_state(
    tmp_path: pathlib.Path,
) -> None:
    def mutate(spec: dict[str, Any]) -> None:
        transition_e2(spec)
        set_active(find_entry(spec, "eebus-api-candidate"), canonical=True)

    assert validate(load_validator(), build_workspace(tmp_path, mutate)) == [
        "enforcement.transition"
    ]


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
    item["owner"]["path"] = "protocols/protocol-link/ship-spine.md"
    item["source"]["path"] = "protocols/protocol-link/ship-spine.md"
    spec["symlinks"]["docs_eebus"]["protocols/protocol-link"] = "."


def absolute_symlink_component(spec: dict[str, Any]) -> None:
    item = find_entry(spec, "eebus-protocol")
    item["owner"]["path"] = "protocols/protocol-link/ship-spine.md"
    item["source"]["path"] = "protocols/protocol-link/ship-spine.md"
    spec["symlinks"]["docs_eebus"]["protocols/protocol-link"] = "ABS:protocols"


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


def test_combined_ref_accepts_fork_candidate_origin(tmp_path: pathlib.Path) -> None:
    def fork_origin(spec: dict[str, Any]) -> None:
        spec["remotes"]["docs_ebus"] = "contributor/helianthus-docs-ebus"

    assert validate(load_validator(), build_workspace(tmp_path, fork_origin)) == []


@pytest.mark.parametrize(
    "addition",
    (
        "\n```markdown\nSHIP peers MUST negotiate sessions.\n```\n",
        "\n`The eeBUS runtime MUST persist trust state.`\n",
        "\n    The eeBUS Go API MUST expose package symbols.\n",
        "\nSummary: SHIP peers negotiate sessions in the canonical protocol docs.\n",
        "\nThe platform evidence gate MUST record whether a SHIP session was observed.\n",
        "\n## SHIP Protocol Evidence Gate\n\n"
        "The artifact MUST record whether peers negotiated before sending messages.\n",
    ),
    ids=(
        "fenced-code",
        "inline-code",
        "indented-code",
        "non-normative-summary",
        "evidence-gate-false-positive",
        "evidence-record",
    ),
)
def test_semantic_copy_false_positive_controls(
    tmp_path: pathlib.Path, addition: str
) -> None:
    workspace = build_workspace(tmp_path, append_platform(addition))
    assert validate(load_validator(), workspace) == []


@pytest.mark.parametrize(
    "statement",
    (
        "Protocol peers MUST record whether the artifact exists and negotiate "
        "before sending messages.",
        "Protocol peers MUST record whether the artifact exists, and negotiate "
        "before sending messages.",
        "Protocol peers MUST record whether the artifact exists, negotiate "
        "before sending messages.",
        "The artifact MUST record whether it exists, which protocol peers "
        "negotiate before sending messages.",
        "Protocol peers MUST record whether the artifact exists as well as "
        "send protocol messages.",
        "Protocol peers MUST record whether the artifact exists along with "
        "sending protocol messages.",
        "Protocol peers MUST record whether the artifact exists together with "
        "sending protocol messages.",
        "Protocol peers MUST record whether the artifact exists plus sending "
        "protocol messages.",
        "Protocol peers MUST record whether the artifact exists; then send "
        "protocol messages.",
        "Protocol peers MUST record whether the artifact exists: send protocol "
        "messages.",
        "Protocol peers MUST record whether the artifact exists — send protocol "
        "messages.",
        "The artifact MUST record the result and peers MUST negotiate before "
        "sending messages.",
        "The artifact MUST record the result, peers MUST negotiate before "
        "sending messages.",
        "The artifact MUST record the result, which peers MUST negotiate before "
        "sending messages.",
        "The artifact MUST record the result and negotiate before sending messages.",
        "The documentation MUST own the evidence summary and peers MUST negotiate "
        "before sending messages.",
    ),
    ids=(
        "shared-modal-conjunction",
        "shared-modal-comma-conjunction",
        "shared-modal-comma",
        "shared-modal-relative",
        "shared-modal-as-well-as",
        "shared-modal-along-with",
        "shared-modal-together-with",
        "shared-modal-plus",
        "shared-modal-semicolon",
        "shared-modal-colon",
        "shared-modal-em-dash",
        "governance-and",
        "governance-comma",
        "governance-relative-clause",
        "governance-shared-modal",
        "ownership-and",
    ),
)
def test_semantic_copy_exemptions_are_predicate_local(
    tmp_path: pathlib.Path, statement: str
) -> None:
    addition = f"\n## SHIP Protocol Evidence Gate\n\n{statement}\n"
    workspace = build_workspace(tmp_path, append_platform(addition))
    assert validate(load_validator(), workspace) == ["ownership.protocol-copy"]


@pytest.mark.parametrize(
    "exempt_prefix",
    (
        "The documentation MUST own the evidence summary",
        "The artifact MUST not claim the digest",
    ),
    ids=("ownership", "negative-governance"),
)
@pytest.mark.parametrize(
    "continuation",
    (
        " plus SHIP peers negotiate before sending messages",
        " along with SHIP peers negotiating before sending messages",
        " together with SHIP peers negotiating before sending messages",
        ", SHIP peers negotiate before sending messages",
        " and SHIP peers negotiate before sending messages",
        ", which SHIP peers negotiate before sending messages",
        " and SHIP peers MUST negotiate before sending messages",
    ),
    ids=(
        "plus",
        "along-with",
        "together-with",
        "comma",
        "and",
        "relative",
        "shared-modal",
    ),
)
def test_ownership_and_negative_governance_exempt_only_their_own_span(
    tmp_path: pathlib.Path, exempt_prefix: str, continuation: str
) -> None:
    addition = (
        "\n## SHIP Protocol Evidence Gate\n\n"
        f"{exempt_prefix}{continuation}.\n"
    )
    workspace = build_workspace(tmp_path, append_platform(addition))
    assert validate(load_validator(), workspace) == ["ownership.protocol-copy"]


@pytest.mark.parametrize(
    "statement",
    (
        "The documentation MUST own the evidence summary.",
        "The artifact MUST not claim the digest.",
    ),
    ids=("ownership", "negative-governance"),
)
def test_pure_ownership_and_negative_governance_prose_remains_allowed(
    tmp_path: pathlib.Path, statement: str
) -> None:
    addition = f"\n## SHIP Protocol Evidence Gate\n\n{statement}\n"
    workspace = build_workspace(tmp_path, append_platform(addition))
    assert validate(load_validator(), workspace) == []


@pytest.mark.parametrize(
    "statement",
    (
        "The artifact MUST record whether the manifest exists and whether the "
        "proof is complete.",
        "The artifact MUST record whether protocol peers negotiated before "
        "sending messages.",
        "The artifact MUST record whether the manifest exists, and may report "
        "the proof digest.",
    ),
    ids=(
        "coordinated-governance-complements",
        "reported-protocol-observation",
        "explicit-nonnormative-modal-reset",
    ),
)
def test_shared_modal_segmentation_preserves_governance_only_prose(
    tmp_path: pathlib.Path, statement: str
) -> None:
    addition = f"\n## SHIP Protocol Evidence Gate\n\n{statement}\n"
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
        (
            "\n## eeBUS Go API Reference\n\n"
            "The package MUST provide lifecycle methods.\n",
            "ownership.api-copy",
        ),
        (
            "\n## SHIP Protocol Evidence Gate\n\n"
            "Peers MUST negotiate before sending messages; "
            "the artifact records the result.\n",
            "ownership.protocol-copy",
        ),
    ),
    ids=(
        "protocol-h2",
        "architecture-h4",
        "reference-style-api-h3",
        "api-provide-synonym",
        "mixed-evidence-and-protocol",
    ),
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
        "\n## SHIP Protocol Quotation\n\n"
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
        "standalone-quotation",
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
        "\n[Unmerged](../../helianthus\\-docs\\-eebus/architecture/future.md)\n",
        "\n[Unmerged][future]\n\n"
        "[future]: ../../helianthus&#45;docs&#x2d;eebus/architecture/future.md\n",
        "\n[Unmerged](<../../helianthus-docs-eebus&sol;architecture&sol;future.md>)\n",
        "\n<https://github.com/Project-Helianthus/"
        "helianthus\\-docs\\-eebus/blob/main/architecture/future.md>\n",
        "\nUnmerged: https://github.com/Project-Helianthus/"
        "helianthus-docs-eebus&sol;blob&sol;main&sol;architecture&sol;future.md\n",
    ),
    ids=(
        "inline-backslash-punctuation",
        "reference-numeric-entities",
        "inline-angle-named-entities",
        "autolink-backslash-punctuation",
        "bare-named-entities",
    ),
)
def test_markdown_destinations_are_normalized_before_forward_classification(
    tmp_path: pathlib.Path, addition: str
) -> None:
    workspace = build_workspace(tmp_path, append_platform(addition))
    assert validate(load_validator(), workspace) == ["link.forward"]


@pytest.mark.parametrize(
    "addition",
    (
        "\n[Protocol [stable]][proto]\n\n"
        "[proto]: https://github.com/Project-Helianthus/helianthus-docs-eebus/"
        "blob/__DOCS_EEBUS_REF__/protocols/ship-spine.md \"title\"\n",
        "\n<a href=\"https://github.com/Project-Helianthus/"
        "helianthus-docs-eebus/blob/__DOCS_EEBUS_REF__/"
        "protocols/ship-spine.md\">Protocol</a>\n",
        "\n<https://github.com/pRoJeCt-HeLiAnThUs/"
        "HeLiAnThUs-DoCs-EeBuS/blob/__DOCS_EEBUS_REF__/"
        "protocols/ship-spine.md>\n",
        "\nStable: https://github.com/pRoJeCt-HeLiAnThUs/"
        "HeLiAnThUs-DoCs-EeBuS/blob/__DOCS_EEBUS_REF__/"
        "protocols/ship-spine.md.\n",
        "\n```markdown\n[Bad][future]\n"
        "[future]: ../../helianthus-docs-eebus/architecture/future.md\n```\n",
        "\nLiteral escaped path text: "
        "../../helianthus\\-docs\\-eebus/architecture/future.md\n",
        "\n[Safe helianthus\\-docs\\-eebus text](https://example.invalid/)\n",
    ),
    ids=(
        "reference-style-active",
        "html-active",
        "mixed-case-autolink-active",
        "mixed-case-bare-active",
        "code-link-ignored",
        "escaped-literal-text",
        "escaped-link-text",
    ),
)
def test_markdown_link_parser_accepts_only_real_active_links(
    tmp_path: pathlib.Path, addition: str
) -> None:
    workspace = build_workspace(tmp_path, append_platform(addition))
    assert validate(load_validator(), workspace) == []


@pytest.mark.parametrize(
    "addition,expected",
    (
        (
            "\n[Protocol][duplicate]\n\n"
            "[duplicate]: ../../helianthus-docs-eebus/architecture/future.md\n"
            "[duplicate]: https://github.com/Project-Helianthus/"
            "helianthus-docs-eebus/blob/__DOCS_EEBUS_REF__/"
            "protocols/ship-spine.md\n",
            ["link.forward"],
        ),
        (
            "\n[Protocol][duplicate]\n\n"
            "[duplicate]: https://github.com/Project-Helianthus/"
            "helianthus-docs-eebus/blob/__DOCS_EEBUS_REF__/"
            "protocols/ship-spine.md\n"
            "[duplicate]: ../../helianthus-docs-eebus/architecture/future.md\n",
            [],
        ),
        (
            "\n[Protocol][My Ref]\n\n"
            "[my   ref]: https://github.com/Project-Helianthus/"
            "helianthus-docs-eebus/blob/__DOCS_EEBUS_REF__/"
            "protocols/ship-spine.md\n"
            "[MY REF]: ../../helianthus-docs-eebus/architecture/future.md\n",
            [],
        ),
        (
            "\n[Protocol][protocol-ref]\n\n"
            "[protocol-ref]: https://github.com/Project-Helianthus/"
            "helianthus-docs-eebus/blob/__DOCS_EEBUS_REF__/"
            "protocols/ship-spine.md\n",
            [],
        ),
        (
            "\n[Protocol][duplicate-id]\n\n"
            "[duplicate\\-id]: ../../helianthus\\-docs\\-eebus/"
            "architecture/future.md\n"
            "[duplicate&#45;id]: https://github.com/Project-Helianthus/"
            "helianthus-docs-eebus/blob/__DOCS_EEBUS_REF__/"
            "protocols/ship-spine.md\n",
            ["link.forward"],
        ),
        (
            "\n[Protocol][duplicate-id]\n\n"
            "[duplicate&#45;id]: https://github.com/Project-Helianthus/"
            "helianthus-docs-eebus/blob/__DOCS_EEBUS_REF__/"
            "protocols/ship-spine.md\n"
            "[duplicate\\-id]: ../../helianthus\\-docs\\-eebus/"
            "architecture/future.md\n",
            [],
        ),
    ),
    ids=(
        "prohibited-first-safe-second",
        "safe-first-prohibited-second",
        "normalized-case-and-spacing",
        "ordinary-reference",
        "normalized-id-prohibited-first-safe-second",
        "normalized-id-safe-first-prohibited-second",
    ),
)
def test_markdown_reference_definitions_use_first_definition(
    tmp_path: pathlib.Path, addition: str, expected: list[str]
) -> None:
    workspace = build_workspace(tmp_path, append_platform(addition))
    assert validate(load_validator(), workspace) == expected


@pytest.mark.parametrize(
    "literal",
    (
        "fc00::42",
        "fd12:3456:789a::1",
        "fe80::1",
        "[fe80::1%en0]",
        "::1",
        "::ffff:192.168.1.25",
    ),
    ids=(
        "unique-local-fc",
        "unique-local-fd",
        "link-local",
        "link-local-zone",
        "loopback",
        "mapped-private-ipv4",
    ),
)
def test_private_ipv6_literals_are_rejected(
    tmp_path: pathlib.Path, literal: str
) -> None:
    workspace = build_workspace(
        tmp_path, append_platform(f"\nObserved endpoint: {literal}\n")
    )
    assert validate(load_validator(), workspace) == ["privacy.private-identifier"]


@pytest.mark.parametrize(
    "text",
    (
        "Documentation endpoint: 2001:db8::1",
        "Public resolver: 2606:4700:4700::1111",
        "Digest: deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        "Versions 1.2.3 and 12:30:00 remain ordinary prose.",
    ),
    ids=("documentation-ipv6", "public-ipv6", "hash", "version-and-prose"),
)
def test_ipv6_privacy_parser_avoids_nonprivate_false_positives(
    tmp_path: pathlib.Path, text: str
) -> None:
    workspace = build_workspace(tmp_path, append_platform(f"\n{text}\n"))
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
