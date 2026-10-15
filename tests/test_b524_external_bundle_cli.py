"""Exercise public evidence bundles through the real CLI outside the checkout."""

import json
import os
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
def external_bundle(tmp_path: Path):
    bundle = tmp_path / "public-bundle"
    bundle.mkdir()
    cwd = tmp_path / "unrelated-consumer"
    cwd.mkdir()
    originals = tuple(source.read_bytes() for source in SOURCES)
    paths = tuple(bundle / source.name for source in SOURCES)
    for path, content in zip(paths, originals):
        path.write_bytes(content)
    try:
        yield cwd, paths
    finally:
        for source, content in zip(SOURCES, originals):
            assert source.read_bytes() == content, f"Repository fixture changed: {source.name}"


def run_cli(cwd: Path, paths: tuple[Path, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(paths[0]),
         "--observations", str(paths[1]), "--scopes", str(paths[2])],
        cwd=cwd, text=True, capture_output=True, check=False, timeout=30,
    )


def assert_result(result: subprocess.CompletedProcess[str], message: str = "") -> None:
    diagnostics = f"exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    assert "Traceback" not in result.stderr, diagnostics
    assert result.returncode == (1 if message else 0), diagnostics
    assert result.stderr.strip() == message, diagnostics


@pytest.mark.parametrize("relative", [False, True], ids=["absolute", "relative"])
def test_external_bundle_paths_are_resolved_from_consumer_cwd(external_bundle, relative: bool) -> None:
    cwd, paths = external_bundle
    for path, source in zip(paths, SOURCES):
        assert path.read_bytes() == source.read_bytes()
    if relative:
        paths = tuple(Path(os.path.relpath(path, cwd)) for path in paths)
    assert_result(run_cli(cwd, paths))


@pytest.mark.parametrize("target,message", [
    (1, "observation records[1] description selector mismatch; "
     "records[1] request opcode corroboration failed "
     "(linked observation must match operation, group, instance and register)"),
    (0, "records[0].decoded.max disagrees with raw limits"),
])
def test_supplied_native_file_corruption_cannot_fall_back_to_defaults(
    external_bundle, target: int, message: str,
) -> None:
    cwd, paths = external_bundle
    # The valid repository inputs stay available throughout each negative case.
    assert_result(run_cli(cwd, SOURCES))
    assert_result(run_cli(cwd, paths))
    original = paths[target].read_bytes()
    candidate = json.loads(original)
    if target == 1:
        link = candidate["records"][1]["description"]
        assert link["record_index"] == 0
        link["record_index"] = 1
    else:
        candidate["records"][0]["decoded"]["max"] = 999
    paths[target].write_text(json.dumps(candidate), encoding="utf-8")
    assert_result(run_cli(cwd, paths), message)
    for index, (path, source) in enumerate(zip(paths, SOURCES)):
        if index != target:
            assert path.read_bytes() == source.read_bytes()
    assert_result(run_cli(cwd, SOURCES))
    paths[target].write_bytes(original)
    assert_result(run_cli(cwd, paths))
