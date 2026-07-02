"""Unit tests for TyCheck."""

import subprocess
from pathlib import Path

import pytest

from lograder.pipeline.check.ty_check import (
    TyCheck,
    TyCheckData,
    TyCheckError,
    TyViolation,
    _parse_diagnostics,
)
from lograder.pipeline.config import config
from lograder.pipeline.types.parcels import Manifest

# ---------------------------------------------------------------------------
# Diagnostic parser (no ty binary required)
# ---------------------------------------------------------------------------


def test_parse_diagnostics_error_line():
    output = (
        "foo.py:10:5: error[invalid-return-type] "
        "Return type does not match returned value"
    )
    diags = _parse_diagnostics(output)
    assert len(diags) == 1
    d = diags[0]
    assert d.file == "foo.py"
    assert d.line == 10
    assert d.column == 5
    assert d.severity == "error"
    assert "Return type" in d.message
    assert d.rule == "invalid-return-type"


def test_parse_diagnostics_warning_line():
    output = "bar.py:3:1: warning[unused-ignore-comment] Unused ignore comment"
    diags = _parse_diagnostics(output)
    assert len(diags) == 1
    assert diags[0].severity == "warning"
    assert diags[0].rule == "unused-ignore-comment"


def test_parse_diagnostics_summary_ignored():
    output = "Found 2 diagnostics"
    diags = _parse_diagnostics(output)
    assert len(diags) == 0


def test_parse_diagnostics_all_checks_passed_ignored():
    output = "All checks passed!"
    diags = _parse_diagnostics(output)
    assert len(diags) == 0


def test_parse_diagnostics_mixed():
    output = (
        "a.py:1:1: error[invalid-assignment] Type mismatch\n"
        "a.py:2:2: warning[unresolved-import] Cannot resolve module\n"
        "Found 2 diagnostics\n"
    )
    diags = _parse_diagnostics(output)
    assert len(diags) == 2
    assert diags[0].severity == "error"
    assert diags[1].severity == "warning"


# ---------------------------------------------------------------------------
# TyCheck step
# ---------------------------------------------------------------------------


_HAS_TY = subprocess.run(["ty", "--version"], capture_output=True).returncode == 0


def _make_manifest(tmp_path, files):
    """Write files dict {name: content} and return a Manifest."""
    for name, content in files.items():
        (tmp_path / name).write_text(content, encoding="utf-8")
    with config(root_directory=tmp_path):
        return Manifest.from_flat([Path(n) for n in files])


def _drive(step, manifest):
    gen = step(manifest)
    yields = []
    try:
        while True:
            yields.append(next(gen))
    except StopIteration as e:
        return yields, e.value


def test_ty_check_missing_file(tmp_path):
    with config(root_directory=tmp_path):
        manifest = Manifest.from_flat([Path("existing.py")])
        (tmp_path / "existing.py").write_text("x: int = 1\n", encoding="utf-8")

    step = TyCheck(files=["nonexistent.py"])
    yields, result = _drive(step, manifest)
    assert result.is_err
    err = result.danger_err
    assert isinstance(err, TyCheckError)
    assert "not found" in err.message.lower()


@pytest.mark.skipif(not _HAS_TY, reason="ty not installed")
def test_ty_check_clean_file_yields_ok(tmp_path):
    manifest = _make_manifest(tmp_path, {"clean.py": "x: int = 1\ny: str = 'hello'\n"})
    step = TyCheck(files=["clean.py"])
    yields, result = _drive(step, manifest)

    assert result.is_ok
    assert result.danger_ok is manifest
    oks = [y for y in yields if y.is_ok]
    errs = [y for y in yields if y.is_err]
    assert len(oks) == 1
    assert len(errs) == 0
    assert isinstance(oks[0].danger_ok, TyCheckData)


@pytest.mark.skipif(not _HAS_TY, reason="ty not installed")
def test_ty_check_type_error_yields_violation(tmp_path):
    src = "def f(x: int) -> str:\n    return x\n"
    manifest = _make_manifest(tmp_path, {"typed.py": src})
    step = TyCheck(files=["typed.py"])
    yields, result = _drive(step, manifest)

    assert result.is_ok
    errs = [y for y in yields if y.is_err]
    assert len(errs) >= 1
    violation = errs[0].danger_err
    assert isinstance(violation, TyViolation)
    assert violation.severity == "error"
    assert violation.line > 0


@pytest.mark.skipif(not _HAS_TY, reason="ty not installed")
def test_ty_check_ignore_rule_suppresses_violation(tmp_path):
    src = "import nonexistent_module_xyz\n"
    manifest = _make_manifest(tmp_path, {"imports.py": src})
    step = TyCheck(files=["imports.py"], ignore=["unresolved-import"])
    yields, result = _drive(step, manifest)

    assert result.is_ok
    errs = [y for y in yields if y.is_err]
    assert len(errs) == 0


@pytest.mark.skipif(not _HAS_TY, reason="ty not installed")
def test_ty_check_manifest_returned_on_ok(tmp_path):
    manifest = _make_manifest(tmp_path, {"ok.py": "pass\n"})
    step = TyCheck(files=["ok.py"])
    yields, result = _drive(step, manifest)
    assert result.is_ok
    assert result.danger_ok is manifest
