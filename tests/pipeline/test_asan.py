# mypy: ignore-errors
"""Unit tests for ASanTest."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from lograder.pipeline.test.asan import (
    _ASAN_ERROR_RE,
    ASanCase,
    ASanError,
    ASanFailure,
    ASanSuccess,
    ASanTest,
)
from lograder.pipeline.types.artifacts import FileArtifact

_HAS_GPP = subprocess.run(["which", "g++"], capture_output=True).returncode == 0


def _build_binary(src_code: str, flags: list[str] | None = None) -> Path | None:
    """Compile a binary and return its path, or None on failure."""
    tmpdir = Path(tempfile.mkdtemp(prefix="lograder_asan_test_"))
    src = tmpdir / "prog.cpp"
    src.write_text(src_code, encoding="utf-8")
    binary = tmpdir / "prog"
    cmd = ["g++", "-o", str(binary), str(src)] + (flags or [])
    r = subprocess.run(cmd, capture_output=True)
    return binary if r.returncode == 0 else None


def _drive(step, artifacts):
    gen = step(artifacts)
    yields = []
    try:
        while True:
            yields.append(next(gen))
    except StopIteration as e:
        return yields, e.value


# ---------------------------------------------------------------------------
# Regex unit tests (no g++ required)
# ---------------------------------------------------------------------------


def test_asan_regex_matches_addresssanitizer():
    text = "==12345==ERROR: AddressSanitizer: heap-buffer-overflow"
    assert _ASAN_ERROR_RE.search(text) is not None


def test_asan_regex_matches_leaksanitizer():
    text = "==12345==ERROR: LeakSanitizer: detected memory leaks"
    assert _ASAN_ERROR_RE.search(text) is not None


def test_asan_regex_no_false_positive():
    text = "All tests passed. No errors found."
    assert _ASAN_ERROR_RE.search(text) is None


def test_asan_error_missing_artifact():
    step = ASanTest("missing_binary", [ASanCase(name="t")])
    yields, result = _drive(step, {})
    assert result.is_err
    assert isinstance(result.danger_err, ASanError)
    assert len(yields) == 0


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_asan_clean_binary_passes():
    src = '#include <iostream>\nint main(int argc, char**argv){\nint a[5];\nfor(int i=0;i<5;i++) a[i]=i;\nstd::cout<<a[0]<<"\\n";\nreturn 0;\n}\n'
    binary = _build_binary(src, ["-fsanitize=address", "-g"])
    if binary is None:
        pytest.skip("Compilation failed (ASan may not be available)")

    artifact = FileArtifact(path=binary)
    step = ASanTest("prog", [ASanCase(name="clean_run", args=[])])
    yields, result = _drive(step, {"prog": artifact})
    assert result.is_ok
    assert len(yields) == 1
    assert yields[0].is_ok
    assert isinstance(yields[0].danger_ok, ASanSuccess)


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_asan_heap_overflow_detected():
    src = "#include <stdlib.h>\nint main(){\nint* p = (int*)malloc(4);\np[10] = 42;\nfree(p);\nreturn 0;\n}\n"
    binary = _build_binary(src, ["-fsanitize=address", "-g"])
    if binary is None:
        pytest.skip("Compilation failed (ASan may not be available)")

    artifact = FileArtifact(path=binary)
    step = ASanTest("prog", [ASanCase(name="heap_overflow")])
    yields, result = _drive(step, {"prog": artifact})
    assert result.is_ok
    assert len(yields) == 1
    assert yields[0].is_err
    failure = yields[0].danger_err
    assert isinstance(failure, ASanFailure)
    assert failure.asan_report != ""


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_asan_exit_code_check():
    src = "int main(){return 42;}\n"
    binary = _build_binary(src, ["-fsanitize=address"])
    if binary is None:
        pytest.skip("Compilation failed")

    artifact = FileArtifact(path=binary)
    step = ASanTest(
        "prog",
        [
            ASanCase(name="correct_exit", expected_exit_code=42),
            ASanCase(name="wrong_exit", expected_exit_code=0),
        ],
    )
    yields, result = _drive(step, {"prog": artifact})
    assert result.is_ok
    assert yields[0].is_ok  # exit 42 matched
    assert yields[1].is_err  # exit 42 != 0
