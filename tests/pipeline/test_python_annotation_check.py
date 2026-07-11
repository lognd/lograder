"""Unit tests for PythonAnnotationCheck."""

from __future__ import annotations

from pathlib import Path

from lograder.pipeline.check.source.python_annotation_check import (
    PythonAnnotationCheck,
    PythonAnnotationCheckError,
)
from lograder.pipeline.config import config
from lograder.pipeline.types.parcels import Manifest


def _run(check: PythonAnnotationCheck, manifest: Manifest):
    gen = check(manifest)
    yields = []
    try:
        while True:
            yields.append(next(gen))
    except StopIteration as e:
        return yields, e.value


def _check(tmp_path, source: str, **kwargs):
    src = tmp_path / "m.py"
    src.write_text(source)
    with config(root_directory=tmp_path):
        manifest = Manifest.from_flat([Path("m.py")])
        return _run(PythonAnnotationCheck(files=["m.py"], **kwargs), manifest)


class TestPythonAnnotationCheck:
    def test_fully_annotated_yields_ok_no_violation(self, tmp_path):
        yields, final = _check(tmp_path, "def f(x: int) -> int:\n    return x\n")
        assert final.is_ok
        assert any(y.is_ok for y in yields)
        assert not any(y.is_err for y in yields)

    def test_unannotated_function_is_a_violation(self, tmp_path):
        yields, final = _check(tmp_path, "def f(x):\n    return x\n")
        assert final.is_ok
        violations = [y for y in yields if y.is_err]
        assert len(violations) == 1

    def test_missing_return_annotation_is_a_violation(self, tmp_path):
        yields, final = _check(tmp_path, "def f(x: int):\n    return x\n")
        assert [y for y in yields if y.is_err]

    def test_missing_return_ignored_when_require_return_false(self, tmp_path):
        yields, final = _check(
            tmp_path, "def f(x: int):\n    return x\n", require_return=False
        )
        assert not any(y.is_err for y in yields)

    def test_leading_self_and_cls_are_exempt(self, tmp_path):
        source = (
            "class C:\n"
            "    def m(self, x: int) -> int:\n        return x\n"
            "    @classmethod\n"
            "    def k(cls, y: int) -> int:\n        return y\n"
        )
        yields, final = _check(tmp_path, source)
        assert not any(y.is_err for y in yields)

    def test_private_functions_skipped_by_default(self, tmp_path):
        yields, final = _check(tmp_path, "def _helper(x):\n    return x\n")
        assert not any(y.is_err for y in yields)

    def test_explicit_functions_list_including_dotted_method(self, tmp_path):
        source = "class C:\n    def m(self, x):\n        return x\n"
        yields, final = _check(tmp_path, source, functions=["C.m"])
        assert [y for y in yields if y.is_err]

    def test_required_but_missing_function_is_a_violation(self, tmp_path):
        yields, final = _check(tmp_path, "def g(x: int) -> int:\n    return x\n", functions=["f"])
        assert [y for y in yields if y.is_err]

    def test_missing_file_is_fatal_error(self, tmp_path):
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("nope.py")])
            yields, final = _run(PythonAnnotationCheck(files=["nope.py"]), manifest)
        assert final.is_err
        assert isinstance(final.danger_err, PythonAnnotationCheckError)
