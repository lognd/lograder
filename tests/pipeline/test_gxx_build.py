"""Unit tests for GXXBuild."""

import subprocess
from pathlib import Path

import pytest

from lograder.pipeline.build.gxx import GXXBuild, GXXBuildError, GXXBuildOutput
from lograder.pipeline.config import config
from lograder.pipeline.types.artifacts import FileArtifact
from lograder.pipeline.types.parcels import Manifest
from lograder.process.registry.gcc import GNUXXStandard


def _manifest(tmp_path: Path) -> Manifest:
    with config(root_directory=tmp_path):
        return Manifest.from_flat([Path("main.cpp")])


def _write_main(tmp_path: Path, content: str = None) -> None:
    src = content or '#include <iostream>\nint main(){std::cout<<"hi\\n";return 0;}\n'
    (tmp_path / "main.cpp").write_text(src, encoding="utf-8")


def _run_step(step, manifest):
    """Drive a Step generator to completion, collecting yields and return."""
    gen = step(manifest)
    yields = []
    try:
        while True:
            yields.append(next(gen))
    except StopIteration as e:
        return yields, e.value


@pytest.mark.skipif(
    subprocess.run(["which", "g++"], capture_output=True).returncode != 0,
    reason="g++ not installed",
)
def test_gxx_build_success(tmp_path):
    _write_main(tmp_path)
    manifest = _manifest(tmp_path)
    step = GXXBuild(sources=["main.cpp"], output="prog")
    yields, result = _run_step(step, manifest)

    assert result.is_ok
    artifacts = result.danger_ok
    assert "prog" in artifacts
    assert isinstance(artifacts["prog"], FileArtifact)
    assert artifacts["prog"].path.exists()

    assert len(yields) == 1
    assert yields[0].is_ok
    assert isinstance(yields[0].danger_ok, GXXBuildOutput)


@pytest.mark.skipif(
    subprocess.run(["which", "g++"], capture_output=True).returncode != 0,
    reason="g++ not installed",
)
def test_gxx_build_compile_error(tmp_path):
    (tmp_path / "main.cpp").write_text("this is not valid c++", encoding="utf-8")
    manifest = _manifest(tmp_path)
    step = GXXBuild(sources=["main.cpp"], output="prog")
    yields, result = _run_step(step, manifest)

    assert result.is_err
    err = result.danger_err
    assert isinstance(err, GXXBuildError)
    assert err.return_code is not None
    assert len(yields) == 0


@pytest.mark.skipif(
    subprocess.run(["which", "g++"], capture_output=True).returncode != 0,
    reason="g++ not installed",
)
def test_gxx_build_missing_source(tmp_path):
    manifest = _manifest(tmp_path)  # main.cpp not actually written
    step = GXXBuild(sources=["missing.cpp"], output="prog")
    yields, result = _run_step(step, manifest)

    assert result.is_err
    assert "not found" in result.danger_err.message.lower()
    assert len(yields) == 0


@pytest.mark.skipif(
    subprocess.run(["which", "g++"], capture_output=True).returncode != 0,
    reason="g++ not installed",
)
def test_gxx_build_with_extra_source(tmp_path):
    (tmp_path / "main.cpp").write_text(
        "extern void helper(); int main(){helper();return 0;}",
        encoding="utf-8",
    )
    helper_src = tmp_path / "helper.cpp"
    helper_src.write_text("void helper(){}", encoding="utf-8")

    manifest = _manifest(tmp_path)
    step = GXXBuild(
        sources=["main.cpp"],
        output="prog",
        extra_sources=[helper_src],
    )
    yields, result = _run_step(step, manifest)
    assert result.is_ok


@pytest.mark.skipif(
    subprocess.run(["which", "g++"], capture_output=True).returncode != 0,
    reason="g++ not installed",
)
def test_gxx_build_standard_flag(tmp_path):
    # C++20 structured binding with initializer - valid in C++20 only
    _write_main(tmp_path)
    manifest = _manifest(tmp_path)
    step = GXXBuild(
        sources=["main.cpp"],
        output="prog",
        standard=GNUXXStandard.CXX20,
    )
    yields, result = _run_step(step, manifest)
    assert result.is_ok
