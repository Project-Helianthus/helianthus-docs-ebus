"""Guard the documented gateway readiness contract against source drift."""
import os
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GATEWAY_REFERENCE_SOURCE", ROOT / ".tmp/reference/ebusgateway/graphql/semantic_live.go"))
DOC = ROOT / "architecture/startup-semantic-fsm.md"
PAIRS = {
    "Zones": ("zonePublished", "zoneLiveSeen"),
    "DHW": ("dhwPublished", "dhwLiveSeen"),
    "Boiler status": ("boilerPublished", "boilerLiveSeen"),
    "Circuits": ("circuitPublished", "circuitLiveSeen"),
    "Radio devices": ("radioPublished", "radioLiveSeen"),
}


def contract(source, doc):
    predicate = source.split("func (provider *LiveSemanticProvider) liveReadyCriteriaLocked() bool {", 1)[1].split("\n}", 1)[0]
    caller = source.split("func (provider *LiveSemanticProvider) recordEpochUpdateLocked(", 1)[1].split("\n}\n", 1)[0]
    for domain, (published, live) in PAIRS.items():
        assert f"| {domain} | `{published}` | `{live}` |" in doc
        assert re.search(rf"if provider\.{published} && !provider\.{live} \{{\s*return false\s*}}", predicate)
    check_prose(doc)
    expected = " || ".join(f"provider.{live}" for _, live in PAIRS.values())
    assert f"return {expected}" in predicate
    assert re.search(r"provider\.liveEpoch\+\+.*?if provider\.liveEpoch == 1 \{\s*return provider\.transitionPhaseLocked\(SemanticStartupPhaseLiveWarmup, reason\)\s*}.*?if provider\.liveReadyCriteriaLocked\(\) \{\s*return provider\.transitionPhaseLocked\(SemanticStartupPhaseLiveReady, reason\)", caller, re.S)


PROSE = (
    "returns `LIVE_WARMUP` on the first one",
    "On subsequent live updates it evaluates the predicate and transitions to `LIVE_READY` if it succeeds",
    "The epoch threshold belongs to the caller, not the predicate",
    "a published domain without a live observation makes the predicate false",
    "at least one of the five live observation flags",
    "energy-only updates do not satisfy it",
)


def check_prose(doc):
    flat = " ".join(doc.split())
    for phrase in PROSE:
        assert phrase in flat, phrase


def reference_excerpt():
    """Minimal in-repo reference of the documented predicate and its caller."""
    clauses = "".join(
        f"\tif provider.{p} && !provider.{live} {{\n\t\treturn false\n\t}}\n"
        for p, live in PAIRS.values()
    )
    expression = " || ".join(f"provider.{live}" for _, live in PAIRS.values())
    return (
        "func (provider *LiveSemanticProvider) liveReadyCriteriaLocked() bool {\n"
        + clauses
        + f"\treturn {expression}\n}}\n"
        + "func (provider *LiveSemanticProvider) recordEpochUpdateLocked(reason string) error {\n"
        "\tprovider.liveEpoch++\n"
        "\tif provider.liveEpoch == 1 {\n"
        "\t\treturn provider.transitionPhaseLocked(SemanticStartupPhaseLiveWarmup, reason)\n"
        "\t}\n"
        "\tif provider.liveReadyCriteriaLocked() {\n"
        "\t\treturn provider.transitionPhaseLocked(SemanticStartupPhaseLiveReady, reason)\n"
        "\t}\n}\n"
    )


def test_document_matches_contract_unconditionally():
    contract(reference_excerpt(), DOC.read_text())


def test_staged_source_matches_when_available():
    if not SOURCE.is_file():
        if os.environ.get("REQUIRE_GATEWAY_REFERENCE") == "1":
            pytest.fail("REQUIRE_GATEWAY_REFERENCE=1 but the staged gateway reference is missing")
        pytest.skip("staged public gateway reference unavailable; the unconditional tests still enforce the documented contract")
    contract(SOURCE.read_text(), DOC.read_text())


def test_mutation_controls():
    source, doc = reference_excerpt(), DOC.read_text()
    contract(source, doc)
    for phrase in PROSE:
        with pytest.raises(AssertionError):
            contract(source, doc.replace(phrase, "x"))
    for domain, (published, live) in PAIRS.items():
        row = f"| {domain} | `{published}` | `{live}` |"
        with pytest.raises(AssertionError):
            contract(source, doc.replace(row, ""))
        clause = f"if provider.{published} && !provider.{live} {{\n\t\treturn false\n\t}}"
        with pytest.raises(AssertionError):
            contract(source.replace(clause, ""), doc)
        with pytest.raises(AssertionError):
            contract(source.replace(f"provider.{published} && !provider.{live}", f"provider.{published} && provider.{live}"), doc)
    expression = " || ".join(f"provider.{live}" for _, live in PAIRS.values())
    with pytest.raises(AssertionError):
        contract(source.replace(f"return {expression}", "return true"), doc)
    with pytest.raises(AssertionError):
        contract(source.replace("if provider.liveEpoch == 1 {", "if provider.liveEpoch == 2 {"), doc)
