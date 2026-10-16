"""Reject malformed primary JSON inputs at the real native validator CLI."""

import importlib.util
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
def bundle(tmp_path: Path):
    cwd = tmp_path / "consumer"
    cwd.mkdir()
    paths = tuple(tmp_path / source.name for source in SOURCES)
    originals = tuple(source.read_bytes() for source in SOURCES)
    for path, content in zip(paths, originals):
        path.write_bytes(content)
    yield cwd, paths, originals
    for source, content in zip(SOURCES, originals):
        assert source.read_bytes() == content
    for path, content in zip(paths, originals):
        assert path.read_bytes() == content


def run_cli(cwd: Path, paths: tuple[Path, ...], *, observations: bool = True):
    command = [sys.executable, str(VALIDATOR), str(paths[0])]
    if observations:
        command += ["--observations", str(paths[1])]
    command += ["--scopes", str(paths[2])]
    return subprocess.run(
        command, cwd=cwd, text=True, capture_output=True, check=False, timeout=30,
    )


def assert_result(result, message: str = "") -> None:
    diagnostics = f"exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    assert "Traceback" not in result.stderr, diagnostics
    assert result.returncode == (1 if message else 0), diagnostics
    assert result.stdout == "", diagnostics
    assert result.stderr.strip() == message, diagnostics


@pytest.mark.parametrize("target,label", [(0, "description"), (1, "observations")])
@pytest.mark.parametrize("shape", ["missing", "directory", "truncated", "null", "list"])
def test_bad_primary_input_is_rejected(bundle, target: int, label: str, shape: str) -> None:
    cwd, paths, originals = bundle
    # Repository defaults remain valid and available during every negative case.
    assert_result(run_cli(cwd, SOURCES))
    assert_result(run_cli(cwd, paths))
    path = paths[target]
    path.unlink()
    if shape == "directory":
        path.mkdir()
    elif shape != "missing":
        path.write_text({"truncated": "{", "null": "null", "list": "[]"}[shape], encoding="utf-8")
    try:
        category = f"{label} must be an object" if shape in ("null", "list") else "cannot read JSON"
        assert_result(run_cli(cwd, paths), f"{path}: {category}")
        for index, companion in enumerate(paths):
            if index != target:
                assert companion.read_bytes() == originals[index]
        assert_result(run_cli(cwd, SOURCES))
    finally:
        if path.is_dir():
            path.rmdir()
        path.write_bytes(originals[target])
    assert_result(run_cli(cwd, paths))


def test_observations_argument_remains_optional(bundle) -> None:
    cwd, paths, _ = bundle
    assert_result(run_cli(cwd, paths))
    # A malformed file beside the description must not be read without the flag.
    paths[1].write_text("null", encoding="utf-8")
    try:
        assert_result(run_cli(cwd, paths, observations=False))
        spec = importlib.util.spec_from_file_location("cli_input_validator", VALIDATOR)
        validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        validator.validate_fixture(paths[0], observations=None, scopes=paths[2])
    finally:
        paths[1].write_bytes(SOURCES[1].read_bytes())
    assert_result(run_cli(cwd, paths))
