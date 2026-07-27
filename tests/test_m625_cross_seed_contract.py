from __future__ import annotations

import copy
import importlib.util
import pathlib

import pytest
import yaml


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "docs/platform/manifests/eebus-doc-ownership.yaml"
INPUTS_PATH = REPO_ROOT / "docs/platform/manifests/msp-0625-public-inputs.yaml"
M625_SOURCE_REF = "cedf238e34f879815ba773e9cd76b2b31c2822a3"
M625_PLAN_REF = "fb384ab57d79f0020c54d2c66416e8a7666f0ceb"
M625_PROVENANCE_URL = (
    "https://github.com/Project-Helianthus/helianthus-docs-eebus/blob/"
    f"{M625_SOURCE_REF}/development/msp-0625-provenance-policy.md"
)
M625_ARCHITECTURE_URL = (
    "https://github.com/Project-Helianthus/helianthus-docs-eebus/blob/"
    f"{M625_SOURCE_REF}/architecture/_candidate/"
    "msp-0625-raw-feature-command-path.md"
)


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
    assert entry["source"] == {
        "repository": "helianthus-docs-eebus",
        "path": "development/msp-0625-provenance-policy.md",
    }
    assert entry["lifecycle"]["source_pr"] == (
        "Project-Helianthus/helianthus-docs-eebus#77"
    )
    assert entry["lifecycle"]["source_ref"] == M625_SOURCE_REF
    assert entry["lifecycle"]["content_sha256"] == (
        "f52a15cab0ec7cfebb67a1932b27259489846619b109ea71e43ca54531191db2"
    )
    assert validator._m625_cross_seed_categories(REPO_ROOT, manifest) == set()

    forged = copy.deepcopy(entry)
    forged["source"]["path"] = "architecture/unbound.md"
    assert validator._surface_binding_valid(forged) is False


def test_m625_cross_seed_manifest_entry_is_required_fail_closed() -> None:
    validator = load_validator()
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["entries"] = [
        entry
        for entry in manifest["entries"]
        if entry["id"] != "platform-m625-public-acquisition-methodology"
    ]

    assert validator._m625_cross_seed_categories(REPO_ROOT, manifest) == {
        "m625.cross-seed-manifest"
    }


def test_m625_cross_seed_machine_binds_exact_external_inputs() -> None:
    validator = load_validator()
    binding = yaml.safe_load(INPUTS_PATH.read_text(encoding="utf-8"))
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert binding["sources"] == [
        {
            "repository": "Project-Helianthus/helianthus-execution-plans",
            "ref": M625_PLAN_REF,
            "path": (
                "multi-runtime-semantic-platform.locked/"
                "118-w30-26-m625-raw-spine-feature-acquisition.md"
            ),
            "content_sha256": (
                "21c4e525a39090a1c4f4ca6efdedb05978bc9f7588f9acbcaa6039fc21fa4536"
            ),
            "url": validator.M625_PLAN_URL,
        },
        {
            "repository": "Project-Helianthus/helianthus-docs-eebus",
            "ref": M625_SOURCE_REF,
            "path": "development/msp-0625-provenance-policy.md",
            "content_sha256": (
                "f52a15cab0ec7cfebb67a1932b27259489846619b109ea71e43ca54531191db2"
            ),
            "url": M625_PROVENANCE_URL,
        },
        {
            "repository": "Project-Helianthus/helianthus-docs-eebus",
            "ref": M625_SOURCE_REF,
            "path": (
                "architecture/_candidate/"
                "msp-0625-raw-feature-command-path.md"
            ),
            "content_sha256": (
                "e782c764e5bed3ca103b3544e2bfcb97f7869416184175ad576a90c8f6302e64"
            ),
            "url": M625_ARCHITECTURE_URL,
        },
    ]
    text = cross_seed_text()
    assert f"[canonical provenance policy]({M625_PROVENANCE_URL})" in text
    assert (
        "[candidate command-path ownership record]"
        f"({M625_ARCHITECTURE_URL})"
    ) in text
    assert validator._m625_cross_seed_categories(REPO_ROOT, manifest) == set()


@pytest.mark.parametrize(
    ("mutation", "category"),
    [
        (
            "The protocol defines a command payload field named operationCode.",
            "m625.cross-seed-protocol-api-declaration",
        ),
        (
            "The public API exposes a stable rawFeature query.",
            "m625.cross-seed-protocol-api-declaration",
        ),
        (
            "Live support is implemented and verified.",
            "m625.cross-seed-live-claim",
        ),
        (
            "This behavior is confirmed by a confidential vendor manual.",
            "m625.cross-seed-private-source-attribution",
        ),
        (
            "password: example-password-value",
            "m625.cross-seed-restricted-material",
        ),
        (
            "session_token = example-session-value",
            "m625.cross-seed-restricted-material",
        ),
        (
            "trust_store: example-trust-bytes",
            "m625.cross-seed-restricted-material",
        ),
        (
            "private_key: example-private-key-bytes",
            "m625.cross-seed-restricted-material",
        ),
        (
            "cryptographic_secret: example-secret-bytes",
            "m625.cross-seed-restricted-material",
        ),
        (
            "-----BEGIN ENCRYPTED PRIVATE KEY-----",
            "m625.cross-seed-restricted-material",
        ),
        (
            "Bearer example-authorization-value",
            "m625.cross-seed-restricted-material",
        ),
        (
            "The owner-authorized raw tier may expose a session token.",
            "m625.cross-seed-secret-policy",
        ),
        (
            "A SHA-256 digest may replace a password in public evidence.",
            "m625.cross-seed-secret-policy",
        ),
    ],
)
def test_m625_cross_seed_rejects_independent_policy_mutations(
    mutation: str, category: str
) -> None:
    validator = load_validator()

    assert validator._m625_cross_seed_text_categories(
        cross_seed_text() + f"\n{mutation}\n"
    ) == {category}


def test_m625_cross_seed_policy_checks_allow_legitimate_exclusion_prose() -> None:
    validator = load_validator()
    exclusion = (
        "\nNo protocol or API declaration is made. Live support remains unverified. "
        "Private vendor material is prohibited as evidence. Passwords, session "
        "tokens, bearer tokens, private keys, and trust-store bytes are prohibited "
        "in every tier and cannot be replaced by a digest.\n"
    )

    assert validator._m625_cross_seed_text_categories(
        cross_seed_text() + exclusion
    ) == set()


def test_m625_cross_seed_states_all_tier_secret_and_digest_prohibition() -> None:
    text = cross_seed_text()

    assert "Every tier, including the owner-authorized local raw operator view" in text
    assert "private keys, passwords, credentials, bearer, session, and authentication tokens" in text
    assert "cryptographic secrets, and trust-store bytes" in text
    assert "cannot be replaced by a digest or other deterministic commitment" in text


def test_m625_focused_contract_is_in_local_and_github_docs_ci() -> None:
    local_ci = (REPO_ROOT / "scripts/ci_local.sh").read_text(encoding="utf-8")
    docs_ci = (REPO_ROOT / ".github/workflows/docs-ci.yml").read_text(
        encoding="utf-8"
    )

    assert "python3 -m pytest -q tests/test_m625_cross_seed_contract.py" in local_ci
    assert "run: ./scripts/ci_local.sh" in docs_ci
