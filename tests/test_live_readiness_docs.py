"""Guard the documented gateway readiness contract against source drift."""
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".tmp/reference/ebusgateway/graphql/semantic_live.go"
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
    expected = " || ".join(f"provider.{live}" for _, live in PAIRS.values())
    assert f"return {expected}" in predicate
    assert re.search(r"provider\.liveEpoch\+\+.*?if provider\.liveEpoch == 1 \{\s*return provider\.transitionPhaseLocked\(SemanticStartupPhaseLiveWarmup, reason\)\s*}.*?if provider\.liveReadyCriteriaLocked\(\) \{\s*return provider\.transitionPhaseLocked\(SemanticStartupPhaseLiveReady, reason\)", caller, re.S)


def test_staged_source_and_mutation_controls():
    if not SOURCE.is_file():
        pytest.skip("staged public gateway reference unavailable")
    source, doc = SOURCE.read_text(), DOC.read_text()
    contract(source, doc)
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
