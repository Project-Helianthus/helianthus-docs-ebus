from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/platform/canonical-pv-semantics-v1.md"


def test_continuous_acquisition_is_bounded_and_keeps_registry_freshness_owned():
    text = DOC.read_text(encoding="utf-8")
    section = text.split("## Production Acquisition Lifecycle", 1)[1].split(
        "\n## ", 1
    )[0]

    assert "15 seconds after the previous attempt finishes" in section
    assert "Only one acquisition may be in flight" in section
    assert "new positive\npoll-generation and deadline identities" in section
    assert "one-reconnect\nmaximum" in section
    assert "Cancellation joins the worker" in section
    assert "below the 30-second fresh window" in section
    assert "does not create a partial update" in section
    assert "advances naturally through `FRESH`, `STALE`, and\n`EXPIRED`" in section


def test_current_publication_cannot_exhaust_or_rewrite_immutable_evidence():
    text = DOC.read_text(encoding="utf-8")
    section = text.split("## Production Acquisition Lifecycle", 1)[1].split(
        "\n## ", 1
    )[0]

    assert "separate\nbounded ownership" in section
    assert "replace only the current semantic slot" in section
    assert "do not\nconsume, evict, alias, or overwrite" in section
    assert "cannot stop healthy current\npublication" in section
    assert "complete source provenance and projection accounting" in section
    assert "No worker exists when Modbus is disabled" in section
    assert "only bounded FC03 or\nFC04 reads" in section
    assert "never issues a Modbus write function" in section
