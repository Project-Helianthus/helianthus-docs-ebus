from __future__ import annotations

import copy

import pytest
import yaml

from test_platform_contracts import REPO_ROOT, base_manifest, load_validator


CHANNEL = "canonical"
V2_KINDS = (
    "canonical_document",
    "canonical_collection",
    "summary_pointer",
    "absence_constraint",
)


def v2_manifest() -> dict:
    manifest = copy.deepcopy(base_manifest())
    manifest["version"] = 2
    manifest["channel_registry"] = {
        CHANNEL: {
            "visibility": "stable",
            "owner": "canonical_documentation_owner",
        }
    }
    manifest["eligible_channels"] = {
        entry["id"]: [CHANNEL]
        for entry in manifest["entries"]
        if entry["state"] == "active"
    }
    manifest["exact_memberships"] = {
        CHANNEL: sorted(manifest["eligible_channels"])
    }

    by_surface = {entry["surface"]: entry for entry in manifest["entries"]}
    for entry in manifest["entries"]:
        entry.pop("outputs")
        entry["kind"] = "canonical_document"

    platform = by_surface["platform"]
    platform["kind"] = "canonical_collection"
    platform["members"] = sorted(
        entry["id"]
        for entry in manifest["entries"]
        if entry["surface"] in {"protocol", "architecture", "api"}
        and entry["state"] == "active"
    )

    summary = by_surface["summary_only"]
    summary["kind"] = "summary_pointer"
    summary["canonical"] = False
    summary["target"] = by_surface["code_repo"]["id"]

    code_repo = by_surface["code_repo"]
    code_repo["kind"] = "absence_constraint"
    code_repo["canonical"] = False
    code_repo["forbidden_states"] = ["candidate"]
    code_repo["channels"] = sorted(manifest["channel_registry"])
    return manifest


def test_v1_manifest_remains_accepted_unchanged() -> None:
    validator = load_validator()
    assert validator._schema_valid(base_manifest()) is True


def test_v2_accepts_closed_publication_contract() -> None:
    validator = load_validator()
    assert validator._schema_valid(v2_manifest()) is True


@pytest.mark.parametrize("kind", V2_KINDS)
def test_v2_accepts_each_closed_entry_kind(kind: str) -> None:
    validator = load_validator()
    manifest = v2_manifest()
    manifest["entries"][0]["kind"] = kind
    if kind == "canonical_collection":
        manifest["entries"][0]["members"] = []
    elif kind == "summary_pointer":
        manifest["entries"][0]["canonical"] = False
        manifest["entries"][0]["target"] = manifest["entries"][1]["id"]
    elif kind == "absence_constraint":
        manifest["entries"][0]["canonical"] = False
        manifest["entries"][0]["forbidden_states"] = ["candidate"]
        manifest["entries"][0]["channels"] = [CHANNEL]
    assert validator._schema_valid(manifest) is True


def test_v2_rejects_unregistered_eligible_channel() -> None:
    validator = load_validator()
    manifest = v2_manifest()
    entry_id = next(iter(manifest["eligible_channels"]))
    manifest["eligible_channels"][entry_id].append("unregistered")
    assert validator._schema_valid(manifest) is False


def test_v2_rejects_exact_membership_drift() -> None:
    validator = load_validator()
    manifest = v2_manifest()
    manifest["exact_memberships"][CHANNEL].pop()
    assert validator._schema_valid(manifest) is False


def test_v2_absence_constraint_covers_all_registered_channels() -> None:
    validator = load_validator()
    manifest = v2_manifest()
    manifest["channel_registry"]["release"] = {
        "visibility": "stable",
        "owner": "canonical_documentation_owner",
    }
    absence = next(
        entry for entry in manifest["entries"] if entry["kind"] == "absence_constraint"
    )
    assert validator._schema_valid(manifest) is False
    absence["channels"].append("release")
    manifest["exact_memberships"]["release"] = []
    assert validator._schema_valid(manifest) is True


def test_expiry_boundary_is_inclusive() -> None:
    validator = load_validator()
    manifest = base_manifest()
    planned = next(entry for entry in manifest["entries"] if entry["state"] == "planned")
    expires_at = planned["lifecycle"]["expires_at"]
    assert validator._expiry_categories(manifest, expires_at, "test.clock") == {
        "expiry.planned"
    }


def test_docs_ci_tracks_makefile_for_platform_contract_changes() -> None:
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/docs-ci.yml").read_text(encoding="utf-8")
    )
    assert "Makefile" in workflow[True]["pull_request"]["paths"]
    assert "Makefile" in workflow[True]["push"]["paths"]
