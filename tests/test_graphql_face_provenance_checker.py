from __future__ import annotations

import importlib.util
import pathlib

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("graphql_face_provenance", ROOT / "scripts/check_graphql_face_provenance.py")
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def texts() -> tuple[str, str]:
    return (
        (ROOT / "api/graphql.md").read_text(encoding="utf-8"),
        (ROOT / "architecture/atr/07-live-validation-acceptance.md").read_text(encoding="utf-8"),
    )


def mcp_text() -> str:
    return (ROOT / "api/mcp.md").read_text(encoding="utf-8")


def rejects(doc_old: str | None = None, doc_new: str = "", atr_old: str | None = None, atr_new: str = "") -> None:
    doc, atr = texts()
    if doc_old is not None:
        assert doc_old in doc
        doc = doc.replace(doc_old, doc_new, 1)
    if atr_old is not None:
        assert atr_old in atr
        atr = atr.replace(atr_old, atr_new, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(doc, atr)


def test_accepts_current_independent_label_contract() -> None:
    CHECKER.validate_text(*texts())
    CHECKER.validate_mcp_text(mcp_text())


@pytest.mark.parametrize(
    ("old", "new"),
    (
        (CHECKER.HEADING, "### Device Face Discovery Provenance"),
        ("  discoverySource: String", "  discovery_source: String"),
        ("  verificationState: String", "  verification_state: String"),
        ("  discoverySource: String", "  discoverySource: String!"),
        ("| `static_seed` |\n", "| `manual` |\n"),
        ("| `identity_confirmed` |\n", "| `verified` |\n"),
        ("| `passive_observed` | `corroborated_pending` |", "| `passive_observed` | `candidate` |"),
        ("no source label determines or\nrestricts the state label.", "each source label determines its state label."),
        (CHECKER.SOURCE_RETENTION, CHECKER.SOURCE_RETENTION.replace("MUST NOT", "MAY")),
        ("`static_seed` / `identity_confirmed`", "`static_seed` / `candidate`"),
        ("`passive_observed` / `identity_confirmed`", "`passive_observed` / `corroborated_pending`"),
        (CHECKER.DEVICES_FACE, "`devices` selects an arbitrary face."),
        (CHECKER.NON_PROOF, "A discovery source or verification state proves a\n"
         "supported device, current qualification, stable cross-address identity, and\n"
         "live behavior."),
        (CHECKER.TOPOLOGY_NON_PROOF, "Topology grouping proves identity."),
        ("canonical or alias face's discovery provenance", "device-level provenance"),
        ("returned device identity remains canonical", "returned identity follows the queried face"),
        ("`device(address:)` returns `null` for an unknown address.", "Unknown lookup behavior is unspecified."),
        ("both\nfields resolve to GraphQL `null`", "both fields resolve to empty strings"),
        ("A slotless entry remains visible through\n`devices` and `device(address:)`", "A slotless entry is excluded."),
        ("This matches MCP, which omits both\nsnake-case provenance members for the same slotless condition.", "MCP behavior is unrelated."),
        ("The current gateway schema exposes", "The future gateway schema will expose"),
        (CHECKER.GATEWAY_REVIEWED_HEAD, "0" * 40),
        (CHECKER.GATEWAY_REVIEWED_MERGE_TREE, "1" * 40),
        (CHECKER.GATEWAY_MAIN_MERGE, "2" * 40),
        (CHECKER.REGISTRY_DEPENDENCY, "3" * 40),
    ),
)
def test_rejects_document_contract_mutations(old: str, new: str) -> None:
    rejects(doc_old=old, doc_new=new)


def test_rejects_missing_or_non_nullable_current_fields() -> None:
    rejects(doc_old="  discoverySource: String\n")
    rejects(doc_old="  verificationState: String\n", doc_new="  verificationState: String!\n")


def test_rejects_obsolete_atr_spelling() -> None:
    rejects(
        atr_old="verificationState=corroborated_pending`",
        atr_new="verificationState=corroborated`",
    )


def test_rejects_mcp_source_rewrite_rule() -> None:
    text = mcp_text()
    assert CHECKER.MCP_SOURCE_RETENTION in text
    mutated = text.replace(
        CHECKER.MCP_SOURCE_RETENTION,
        "Verification advancement rewrites every source to `active_confirmed`.",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(mutated)


@pytest.mark.parametrize(
    "pin",
    (
        CHECKER.GATEWAY_REVIEWED_HEAD,
        CHECKER.GATEWAY_REVIEWED_MERGE_TREE,
        CHECKER.GATEWAY_MAIN_MERGE,
        CHECKER.REGISTRY_DEPENDENCY,
    ),
)
def test_rejects_wrong_mcp_runtime_or_dependency_pin(pin: str) -> None:
    text = mcp_text()
    mutated = text.replace(pin, "f" * 40, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_mcp_text(mutated)
