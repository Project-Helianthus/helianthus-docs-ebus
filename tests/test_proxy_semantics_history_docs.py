"""Keep the proxy PX01..PX12 case set presented as history, not as a current gate."""
import re
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
CONTRIBUTING = "development/contributing.md"
BLOCK_SPLIT = re.compile(r"\n\s*\n|\n(?=\s*(?:[-*|]|\d+\.)\s)")
PX_STATEMENT = re.compile(r"PX\d|proxy", re.IGNORECASE)
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


def px_statements(text):
    """Paragraphs, list items and table rows that speak about the proxy or its PX cases."""
    return [flat(block) for block in BLOCK_SPLIT.split(text) if PX_STATEMENT.search(block)]


def check_no_current_gate(text):
    for statement in px_statements(text):
        for phrase in CURRENT_GATE_PHRASES:
            assert phrase not in statement, phrase


def bullet(text, label):
    for statement in BLOCK_SPLIT.split(text):
        statement = flat(statement)
        if statement.startswith(f"- **{label}:**"):
            return statement
    raise AssertionError(label)


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
        check_no_current_gate(f"Intro.\n\n- The `PX01..PX12` cases: {phrase} here.\n")
    with pytest.raises(AssertionError):
        check_no_current_gate(f"Intro.\n\nThe proxy matrix: {phrase} here.\n")


@pytest.mark.parametrize("phrase", [p for p in CURRENT_GATE_PHRASES if not PX_STATEMENT.search(p)])
def test_current_gate_phrase_outside_px_statements_is_accepted(phrase):
    check_no_current_gate(f"The PX cases are historical.\n\n- Lint gate: {phrase} the lint result.\n")


def test_contributing_primary_artifact_is_the_gateway_matrix():
    text = read(CONTRIBUTING)
    primary = bullet(text, "Primary required artifact")
    assert MATRIX_LINK in primary
    assert "T01..T88" not in primary
    assert "T09..T88" not in primary
    history = bullet(text, "Historical evidence")
    assert "`T01..T88`" in history
    assert "consolidated candidate session's last `T01..T88` run" in history
    assert "not a merge requirement for new changes" in history
    reference = bullet(text, "Required reference")
    assert "results/index.json" not in reference
    assert "gateway matrix result" in reference


def section(text, heading):
    body = text.split(f"\n{heading}\n", 1)[1]
    level = heading.split(" ", 1)[0]
    return re.split(rf"\n#{{2,{len(level)}}} ", body, maxsplit=1)[0]


def test_runbook_full_run_describes_the_last_run_not_a_current_gate():
    text = read(RUNBOOK)
    full_run = flat(section(text, "### Full run recommendation"))
    assert "For transport/protocol merges, run the complete set" not in full_run
    assert "consolidated candidate session's last full `T01..T88` run" in full_run
    assert "not a merge gate for new changes" in full_run
    assert MATRIX_LINK in full_run
    observe_first = flat(section(text, "## Observe-First Proof Note"))
    assert "the current `T01..T88` transport gate" not in observe_first
    assert "consolidated candidate session's last `T01..T88` run" in observe_first


def test_m4_proof_gates_require_only_gateway_cells():
    gates = section(read("architecture/adaptermux/first-byte-arbitration-revalidation.md"), "## M4 Live Proof Gates")
    rows = [flat(line) for line in gates.splitlines() if line.startswith("| ")]
    assert rows, "M4 gate table"
    for row in rows:
        assert "T01..T88" not in row, row
    px = [row for row in rows if row.startswith("| PX |")]
    assert len(px) == 1
    assert MATRIX_LINK in px[0]
    assert "`<transport>-PX01` to `<transport>-PX12`" in px[0]
    history = flat(gates)
    assert "consolidated candidate session's last `T01..T88` run is historical context" in history
    assert "not part of this proof" in history


def test_missing_gateway_cells_are_rejected():
    with pytest.raises(AssertionError):
        check_names_gateway_cells(f"The case set is historical; see [{MATRIX_LINK}].")
