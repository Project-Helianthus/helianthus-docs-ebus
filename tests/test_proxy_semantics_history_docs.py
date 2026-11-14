"""Keep the proxy PX01..PX12 case set presented as history, not as a current gate."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MATRIX_LINK = "https://github.com/Project-Helianthus/helianthus-ebusgateway/tree/main/matrix"
PAGES = (
    "architecture/proxy-wire-semantics.md",
    "development/contributing.md",
    "architecture/adaptermux/first-byte-arbitration-revalidation.md",
    "development/esera-passive-evidence-package.md",
    "development/smoke-matrix.md",
)
RUNBOOK = "development/smoke-matrix.md"
RUNBOOK_SECTION = "## Proxy-Semantics Adjunct Gate (`PX01..PX12`)\n"
CURRENT_GATE_PHRASES = (
    "remains the primary transport gate",
    "a required adjunct proof subset is evaluated",
    "is a required adjunct",
    "remains the primary merge gate",
    "Merge requires no unexpected",
    "`xfail` must stay bound",
    "Proof runs must include",
    "must summarize `PX01..PX12`",
    "dedicated proxy-semantics subset (`PX01..PX12`)",
)


def flat(text):
    return " ".join(text.split())


def read(page):
    return (ROOT / page).read_text()


def runbook_section(text):
    section = text.split(RUNBOOK_SECTION, 1)[1]
    return section.split("\n## ", 1)[0]


def check_names_gateway_cells(text):
    text = flat(text)
    assert "historical" in text
    assert MATRIX_LINK in text
    assert "`adaptermux-v2` matrix" in text
    assert "`<transport>-PX01` to `<transport>-PX12`" in text
    assert "`PX09` to `PX11` are planned" in text or "PX09 to PX11 are planned" in text


def check_no_current_gate(text):
    text = flat(text)
    for phrase in CURRENT_GATE_PHRASES:
        assert phrase not in text, phrase


@pytest.mark.parametrize("page", PAGES)
def test_page_presents_proxy_case_set_as_history(page):
    text = read(page)
    check_names_gateway_cells(text)
    check_no_current_gate(text)


def test_runbook_proxy_section_is_historical():
    section = runbook_section(read(RUNBOOK))
    assert flat(section).startswith("This section is historical.")
    check_names_gateway_cells(section)
    check_no_current_gate(section)
    assert "describe the last proxy-backed run of the consolidated candidate session" in flat(section)


@pytest.mark.parametrize("phrase", CURRENT_GATE_PHRASES)
def test_current_gate_phrase_is_rejected(phrase):
    with pytest.raises(AssertionError):
        check_no_current_gate(f"Intro. {phrase} here.")


def test_missing_gateway_cells_are_rejected():
    with pytest.raises(AssertionError):
        check_names_gateway_cells(f"The case set is historical; see [{MATRIX_LINK}].")
