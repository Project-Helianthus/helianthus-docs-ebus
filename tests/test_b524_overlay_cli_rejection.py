"""Explicit consumer overlays must fail closed against unchanged public evidence."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_b524_basv0_description_profile.py"
SOURCES = (
    ROOT / "protocols/vaillant/fixtures/b524-basv0-description-profile-v1.json",
    ROOT / "protocols/vaillant/fixtures/b524-basv0-register-observations-v1.json",
    ROOT / "development/fixtures/b524-basv0-validation-scope-v1.json",
)


@pytest.fixture
def consumer_bundle(tmp_path: Path):
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    originals = tuple(source.read_bytes() for source in SOURCES)
    paths = tuple(consumer / source.name for source in SOURCES)
    for path, content in zip(paths, originals):
        path.write_bytes(content)
    try:
        yield consumer, paths
    finally:
        for source, content in zip(SOURCES, originals):
            assert source.read_bytes() == content, source.name
        for path, content in zip(paths[:2], originals[:2]):
            assert path.read_bytes() == content, path.name


def run_cli(consumer: Path, paths: tuple[Path, ...], *, default: bool = False):
    command = [sys.executable, str(VALIDATOR), str(paths[0]),
               "--observations", str(paths[1])]
    if not default:
        command.extend(["--scopes", str(paths[2])])
    return subprocess.run(
        command, cwd=consumer, text=True, capture_output=True,
        check=False, timeout=30,
    )


def assert_result(result: subprocess.CompletedProcess[str], message: str = "") -> None:
    diagnostics = f"exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    assert result.returncode == (1 if message else 0), diagnostics
    assert result.stderr.strip() == message, diagnostics
    assert "Traceback" not in result.stderr, diagnostics


@pytest.mark.parametrize("mutation", [
    "observation-identity", "description-catalog", "duplicate-selector",
    "missing-selector", "DATE_DMY_U8X3", "TIME_HMS_U8X3",
])
def test_explicit_semantically_bad_overlay_cannot_use_valid_default(
    consumer_bundle, mutation: str,
) -> None:
    consumer, paths = consumer_bundle
    original = paths[2].read_bytes()
    overlay = json.loads(original)
    descriptions = json.loads(paths[0].read_bytes())
    assert_result(run_cli(consumer, paths))

    if mutation == "observation-identity":
        overlay["observation_id"] = "synthetic-other-observation"
        message = "validation-scope overlay observation identity mismatch"
    elif mutation == "description-catalog":
        overlay["description_catalog"] = "synthetic-other-catalog.json"
        message = "validation-scope overlay catalog mismatch"
    elif mutation == "duplicate-selector":
        index = len(overlay["records"])
        overlay["records"].append(overlay["records"][0].copy())
        message = f"validation-scope overlay records[{index}] duplicates a selector"
    elif mutation == "missing-selector":
        removed = overlay["records"].pop(0)
        index = next(i for i, record in enumerate(descriptions["records"])
                     if record["selector"] == removed["selector"])
        message = f"records[{index}] has no validation-scope overlay entry"
    else:
        # Candidate layouts remain Hypothesis despite codec qualification;
        # see protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md.
        index, record = next(
            (i, record) for i, record in enumerate(descriptions["records"])
            if (record.get("decoded") or {}).get("codec") == mutation
        )
        assert record["decoded"]["qualification"] == "qualified"
        assert record["decoded"]["codec_basis"] == "public_exact_selector_schema"
        entry = next(entry for entry in overlay["records"]
                     if entry["selector"] == record["selector"])
        assert entry["validation_scope"] == "display_only"
        entry["validation_scope"] = "format_range_and_step"
        message = (
            f"records[{index}] grants range validation to a plain-byte "
            "DATE_DMY_U8X3/TIME_HMS_U8X3 candidate decoding, which must stay display_only"
        )

    paths[2].write_text(json.dumps(overlay), encoding="utf-8")
    # The same native inputs still pass with the repository's valid default.
    assert_result(run_cli(consumer, paths, default=True))
    assert_result(run_cli(consumer, paths), message)
    paths[2].write_bytes(original)
    assert paths[2].read_bytes() == SOURCES[2].read_bytes()
    assert_result(run_cli(consumer, paths))
