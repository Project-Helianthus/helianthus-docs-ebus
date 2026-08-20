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
    assert "one shared 10-second\ndeadline" in section
    assert "including its one permitted reconnect and retry" in section
    assert "new positive poll-generation and\ndeadline identities" in section
    assert "Cancellation joins the worker" in section
    assert "10-second total cycle bound plus the 15-second post-cycle delay" in section
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
    assert "immutable bounded read plan admitted by the selected capability" in section
    assert "current Fronius phase-one plan is FC03-only" in section
    assert "FC04 is unavailable unless a\nfuture versioned profile explicitly admits it" in section
    assert "never issues a\nModbus write function" in section
