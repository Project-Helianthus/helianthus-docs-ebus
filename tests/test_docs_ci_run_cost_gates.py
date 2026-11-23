"""Docs CI cost gates: main-push cancellation, with the combined-ref caller absent."""

from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS_CI = ROOT / ".github/workflows/docs-ci.yml"


def load(path: pathlib.Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_main_pushes_cancel_superseded_runs_but_never_the_nightly_run():
    workflow = load(DOCS_CI)
    concurrency = workflow["concurrency"]
    assert concurrency["group"] == "${{ github.workflow }}-${{ github.event_name }}-${{ github.ref }}"
    assert concurrency["cancel-in-progress"] == (
        "${{ github.event_name == 'pull_request' || github.event_name == 'push' }}"
    )
    # Schedule and dispatch runs share no group with pushes and never cancel.
    triggers = workflow[True]
    assert set(triggers) == {"pull_request", "push", "schedule", "workflow_dispatch"}
    assert triggers["push"]["branches"] == ["main"]

    assert "platform-contracts-combined-ref" not in workflow["jobs"]
    for event in ("pull_request", "push"):
        assert ".github/workflows/platform-contracts-combined-ref.yml" not in triggers[event]["paths"]
