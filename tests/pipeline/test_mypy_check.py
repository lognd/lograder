# mypy: ignore-errors
"""Unit tests for MypyCheck."""

import subprocess

import pytest

from lograder.pipeline.check.mypy_check import (
    MypyCheck,
    MypyCheckData,
    MypyCheckError,
    MypyViolation,
    _parse_diagnostics,
)
from lograder.pipeline.config import config
from lograder.pipeline.types.parcels import Manifest

# ---------------------------------------------------------------------------
# Diagnostic parser (no mypy binary required)
# ---------------------------------------------------------------------------


def test_parse_diagnostics_error_line():
    output = (
        'foo.py:10:5: error: Argument 1 to "len" has incompatible type "int" [arg-type]'
    )
    diags = _parse_diagnostics(output)
    assert len(diags) == 1
    d = diags[0]
    assert d.file == "foo.py"
    assert d.line == 10
    assert d.column == 5
    assert d.severity == "error"
    assert "incompatible type" in d.message
    assert d.error_code == "arg-type"


def test_parse_diagnostics_note_line():
    output = "bar.py:3:1: note: See https://mypy.rtfd.io"
    diags = _parse_diagnostics(output)
    assert len(diags) == 1
    assert diags[0].severity == "note"
    assert diags[0].error_code is None


def test_parse_diagnostics_summary_ignored():
    output = "Found 2 errors in 1 file (checked 1 source file)"
    diags = _parse_diagnostics(output)
    assert len(diags) == 0


def test_parse_diagnostics_mixed():
    output = (
        "a.py:1:1: error: Type mismatch [assignment]\n"
        "a.py:2:2: note: Revealed type is ...\n"
        "Found 1 error.\n"
    )
    diags = _parse_diagnostics(output)
    assert len(diags) == 2
    assert diags[0].severity == "error"
    assert diags[1].severity == "note"


# ---------------------------------------------------------------------------
# MypyCheck step
# ---------------------------------------------------------------------------


_HAS_MYPY = subprocess.run(["mypy", "--version"], capture_output=True).returncode == 0


def _make_manifest(tmp_path, files):
    """Write files dict {name: content} and return a Manifest."""
    for name, content in files.items():
        (tmp_path / name).write_text(content, encoding="utf-8")
    with config(root_directory=tmp_path):
        from pathlib import Path

        return Manifest.from_flat([Path(n) for n in files])


def _drive(step, manifest):
    gen = step(manifest)
    yields = []
    try:
        while True:
            yields.append(next(gen))
    except StopIteration as e:
        return yields, e.value


def test_mypy_check_missing_file(tmp_path):
    with config(root_directory=tmp_path):
        from pathlib import Path

        manifest = Manifest.from_flat([Path("existing.py")])
        (tmp_path / "existing.py").write_text("x: int = 1\n", encoding="utf-8")

    step = MypyCheck(files=["nonexistent.py"])
    yields, result = _drive(step, manifest)
    assert result.is_err
    err = result.danger_err
    assert isinstance(err, MypyCheckError)
    assert "not found" in err.message.lower()


@pytest.mark.skipif(not _HAS_MYPY, reason="mypy not installed")
def test_mypy_check_clean_file_yields_ok(tmp_path):
    manifest = _make_manifest(tmp_path, {"clean.py": "x: int = 1\ny: str = 'hello'\n"})
    step = MypyCheck(files=["clean.py"], ignore_missing_imports=True)
    yields, result = _drive(step, manifest)

    assert result.is_ok
    assert result.danger_ok is manifest
    # Should yield exactly one Ok(MypyCheckData)
    oks = [y for y in yields if y.is_ok]
    errs = [y for y in yields if y.is_err]
    assert len(oks) == 1
    assert len(errs) == 0
    assert isinstance(oks[0].danger_ok, MypyCheckData)


@pytest.mark.skipif(not _HAS_MYPY, reason="mypy not installed")
def test_mypy_check_type_error_yields_violation(tmp_path):
    src = "def add(x: int, y: int) -> int:\n    return x + y\n\nadd(1, 'two')\n"
    manifest = _make_manifest(tmp_path, {"typed.py": src})
    step = MypyCheck(files=["typed.py"], ignore_missing_imports=True)
    yields, result = _drive(step, manifest)

    assert result.is_ok
    errs = [y for y in yields if y.is_err]
    assert len(errs) >= 1
    violation = errs[0].danger_err
    assert isinstance(violation, MypyViolation)
    assert violation.severity == "error"
    assert violation.line > 0


@pytest.mark.skipif(not _HAS_MYPY, reason="mypy not installed")
def test_mypy_check_strict_mode_flags_missing_annotations(tmp_path):
    src = "def add(x, y):\n    return x + y\n"
    manifest = _make_manifest(tmp_path, {"untyped.py": src})
    step = MypyCheck(
        files=["untyped.py"],
        disallow_untyped_defs=True,
        ignore_missing_imports=True,
    )
    yields, result = _drive(step, manifest)

    assert result.is_ok
    errs = [y for y in yields if y.is_err]
    assert len(errs) >= 1


@pytest.mark.skipif(not _HAS_MYPY, reason="mypy not installed")
def test_mypy_check_manifest_returned_on_ok(tmp_path):
    manifest = _make_manifest(tmp_path, {"ok.py": "pass\n"})
    step = MypyCheck(files=["ok.py"])
    yields, result = _drive(step, manifest)
    assert result.is_ok
    assert result.danger_ok is manifest
