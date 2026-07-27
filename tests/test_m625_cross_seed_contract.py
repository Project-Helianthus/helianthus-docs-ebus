from __future__ import annotations

import copy
import importlib.util
import pathlib

import yaml


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "docs/platform/manifests/eebus-doc-ownership.yaml"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_platform_contracts",
        REPO_ROOT / "scripts/validate_platform_contracts.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cross_seed_text() -> str:
    return (
        REPO_ROOT
        / "docs/platform/msp-0625-public-acquisition-methodology.md"
    ).read_text(encoding="utf-8")


def test_m625_cross_seed_is_active_methodology_and_immutably_bound() -> None:
    validator = load_validator()
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    entry = next(
        item
        for item in manifest["entries"]
        if item["id"] == validator.M625_CROSS_SEED_ID
    )

    assert entry["state"] == "active"
    assert entry["canonical"] is True
    assert entry["owner"]["path"] == validator.M625_CROSS_SEED_PATH.as_posix()
    assert entry["lifecycle"]["source_ref"] is None
    assert entry["lifecycle"]["content_sha256"] is None
    assert validator._m625_cross_seed_categories(REPO_ROOT, manifest) == set()

    forged = copy.deepcopy(entry)
    forged["source"]["path"] = "architecture/unbound.md"
    assert validator._surface_binding_valid(forged) is False


def test_m625_cross_seed_binds_exact_external_source_locators() -> None:
    validator = load_validator()
    allowed = {
        validator.M625_PROVENANCE_LOCATOR,
        validator.M625_ARCHITECTURE_LOCATOR,
    }

    assert all(link in cross_seed_text() for link in allowed)
    assert "cedf238e34f879815ba773e9cd76b2b31c2822a3" in cross_seed_text()


def test_m625_cross_seed_rejects_protocol_native_leakage() -> None:
    validator = load_validator()

    for leaked_term in validator.M625_PROTOCOL_NATIVE_TERMS:
        categories = validator._m625_cross_seed_text_categories(
            cross_seed_text() + f"\n{leaked_term}\n"
        )
        assert categories == {"m625.cross-seed-protocol-leak"}


def test_m625_cross_seed_rejects_restricted_or_private_material() -> None:
    validator = load_validator()

    for leaked_material in (
        "-----BEGIN PRIVATE KEY-----",
        "Bearer credential-value",
        "device_id: retained-identity",
        "192.168.1.10",
    ):
        categories = validator._m625_cross_seed_text_categories(
            cross_seed_text() + f"\n{leaked_material}\n"
        )
        assert categories == {"m625.cross-seed-restricted-material"}
