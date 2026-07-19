from __future__ import annotations

import pathlib
import re


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = REPO_ROOT / "docs/platform/synchronized-evidence-bundle-v1.md"
INDEX = REPO_ROOT / "docs/platform/README.md"


def contract_text() -> str:
    assert PAGE.is_file(), "MSP-065 canonical platform contract is missing"
    return PAGE.read_text(encoding="utf-8")


def assert_terms(text: str, *terms: str) -> None:
    for term in terms:
        assert term in text, f"contract is missing {term!r}"


def test_msp065_page_is_canonical_and_navigable() -> None:
    index = INDEX.read_text(encoding="utf-8")
    assert "synchronized-evidence-bundle-v1.md" in index
    text = contract_text()
    assert re.search(
        r"^Canonical source: this page\.$", text, flags=re.MULTILINE
    )
    assert_terms(text, "SynchronizedEvidenceBundleV1", "MSP-065")


def test_msp065_schema_and_source_states_are_closed() -> None:
    text = contract_text()
    assert_terms(
        text,
        "additional fields are rejected",
        "contract",
        "bundle_id",
        "captured_at",
        "capture_window",
        "clock",
        "scope",
        "mask_tier",
        "auth_scope",
        "sources",
        "artifacts",
        "recorder_version",
        "replay_version",
        "bundle_hash",
        "PRESENT",
        "WITHHELD",
        "NOT_TESTED",
        "UNAVAILABLE",
    )
    assert "empty success" in text
    assert "error precedence" in text


def test_msp065_uses_one_capture_clock_and_observational_action_markers() -> None:
    text = contract_text()
    assert_terms(
        text,
        "one capture clock",
        "RFC 3339",
        "monotonic",
        "pre",
        "action",
        "post",
        "acquisition_start_offset_ns",
        "acquisition_end_offset_ns",
        "measured_latency_ns",
        "maximum_skew_ns",
        "externally supplied",
        "must not initiate",
    )


def test_msp065_requires_exact_ebus_source_identity() -> None:
    text = contract_text()
    assert_terms(
        text,
        "B509",
        "B524",
        "B555",
        "(opcode, GG, II, RR)",
        "separate namespaces",
        "WITHHELD",
        "NOT_TESTED",
        "no inferred",
        "no family",
        "existing read-only eBUS",
        "no new eBUS capture path",
    )


def test_msp065_hash_and_replay_are_deterministic_and_offline() -> None:
    text = contract_text()
    assert_terms(
        text,
        "RFC 8785",
        "domain separator",
        "content-addressed",
        "deterministic ordering",
        "duplicate",
        "captured timestamps",
        "offline",
        "side-effect-free",
        "no network",
        "no cloud",
        "no runtime",
        "no wall clock",
        "no randomness",
        "no locale",
        "future candidate inputs",
        "does not create candidate facts",
    )


def test_msp065_privacy_persistence_and_anti_leak_rules_are_explicit() -> None:
    text = contract_text()
    assert_terms(
        text,
        "per-bundle pseudonym",
        "category-only",
        "vendor_restricted",
        "0700",
        "0600",
        "symlink",
        "path traversal",
        "atomic replace",
        "fsync",
        "quota",
        "retention",
        "disabled by default",
        "ebus.v1.*",
        "GraphQL",
        "Portal",
        "Home Assistant",
        "command routing",
        "semantic registry",
    )
    for forbidden in (
        "private key",
        "access token",
        "raw packet",
        "host path",
        "stable device identifier",
        "IP address",
        "MAC address",
    ):
        assert forbidden in text


def test_msp065_cross_seed_is_immutable_and_nonduplicating() -> None:
    text = contract_text()
    assert re.search(
        r"Project-Helianthus/helianthus-docs-eebus(?:/blob|@)/"
        r"?[0-9a-f]{40}",
        text,
    ) or re.search(
        r"Project-Helianthus/helianthus-docs-eebus@[0-9a-f]{40}", text
    )
    assert_terms(
        text,
        "eeBUS-native",
        "canonical in `helianthus-docs-eebus`",
        "does not restate",
    )


def test_msp07_candidate_fact_contract_is_present_before_green() -> None:
    platform_root = REPO_ROOT / "docs/platform"
    required = (
        platform_root / "draft-candidate-fact-graph-v1.md",
        platform_root / "schemas/draft-candidate-fact-graph-v1.schema.json",
        platform_root / "schemas/draft-candidate-fact-replay-v1.schema.json",
        platform_root / "schemas/draft-candidate-fact-registry-v1.json",
        REPO_ROOT / "scripts/validate_candidate_fact_graph.py",
    )
    for path in required:
        assert path.is_file(), f"missing MSP-07 implementation artifact: {path}"
