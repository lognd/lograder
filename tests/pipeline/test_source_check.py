"""Unit and integration tests for SourceCheck and AST analysis."""

from __future__ import annotations

from pathlib import Path

from lograder.pipeline.check.source._ast import (
    analyze_cpp,
    analyze_python,
)
from lograder.pipeline.check.source.source_check import (
    IdentifierConstraint,
    ImportConstraint,
    IncludeConstraint,
    KeywordConstraint,
    OperatorConstraint,
    SourceCheck,
    SourceCheckError,
    SourceViolation,
)
from lograder.pipeline.config import config
from lograder.pipeline.types.parcels import Manifest


def _run_check(check: SourceCheck, manifest: Manifest):
    """Drain the generator; return (list_of_yields, final_result)."""
    gen = check(manifest)
    yields = []
    try:
        while True:
            yields.append(next(gen))
    except StopIteration as e:
        return yields, e.value


# ---------------------------------------------------------------------------
# analyze_python unit tests
# ---------------------------------------------------------------------------


class TestAnalyzePython:
    def test_operators_binary(self, tmp_path):
        src = tmp_path / "a.py"
        src.write_text("x = 1 + 2\ny = 3 - 1\n")
        result = analyze_python(src)
        assert result.is_ok
        ops = result.danger_ok.operators
        assert ops["+"] >= 1
        assert ops["-"] >= 1

    def test_operators_augmented(self, tmp_path):
        src = tmp_path / "a.py"
        src.write_text("x = 0\nx += 1\n")
        result = analyze_python(src)
        assert result.is_ok
        assert result.danger_ok.operators["+="] >= 1

    def test_identifiers(self, tmp_path):
        src = tmp_path / "a.py"
        src.write_text("lst = list(range(10))\n")
        result = analyze_python(src)
        assert result.is_ok
        assert result.danger_ok.identifiers["list"] >= 1

    def test_import_statement(self, tmp_path):
        src = tmp_path / "a.py"
        src.write_text("import numpy\n")
        result = analyze_python(src)
        assert result.is_ok
        assert result.danger_ok.imports["numpy"] >= 1

    def test_from_import(self, tmp_path):
        src = tmp_path / "a.py"
        src.write_text("from collections import Counter\n")
        result = analyze_python(src)
        assert result.is_ok
        assert result.danger_ok.imports["collections"] >= 1

    def test_dotted_import_records_top_level_and_full(self, tmp_path):
        src = tmp_path / "a.py"
        src.write_text("import os.path\n")
        result = analyze_python(src)
        assert result.is_ok
        imports = result.danger_ok.imports
        assert imports["os"] >= 1
        assert imports["os.path"] >= 1

    def test_missing_file_returns_err(self, tmp_path):
        result = analyze_python(tmp_path / "nonexistent.py")
        assert result.is_err

    def test_no_ops_empty_file(self, tmp_path):
        src = tmp_path / "empty.py"
        src.write_text("")
        result = analyze_python(src)
        assert result.is_ok
        assert len(result.danger_ok.operators) == 0

    def test_for_loop_keyword(self, tmp_path):
        src = tmp_path / "a.py"
        src.write_text("for i in range(10):\n    pass\n")
        result = analyze_python(src)
        assert result.is_ok
        assert result.danger_ok.keywords["for"] >= 1

    def test_while_loop_keyword(self, tmp_path):
        src = tmp_path / "a.py"
        src.write_text("while True:\n    break\n")
        result = analyze_python(src)
        assert result.is_ok
        assert result.danger_ok.keywords["while"] >= 1

    def test_no_loop_keywords(self, tmp_path):
        src = tmp_path / "a.py"
        src.write_text("x = 1 + 2\n")
        result = analyze_python(src)
        assert result.is_ok
        assert len(result.danger_ok.keywords) == 0


# ---------------------------------------------------------------------------
# analyze_cpp unit tests
# ---------------------------------------------------------------------------


class TestAnalyzeCpp:
    def test_operators_binary(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("int main() { int x = 1 + 2; return 0; }\n")
        result = analyze_cpp(src)
        assert result.is_ok
        assert result.danger_ok.operators["+"] >= 1

    def test_identifiers(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("int main() { int myvar = 0; return myvar; }\n")
        result = analyze_cpp(src)
        assert result.is_ok
        assert result.danger_ok.identifiers["myvar"] >= 1

    def test_include_detection(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("#include <vector>\nint main() { return 0; }\n")
        result = analyze_cpp(src)
        assert result.is_ok
        includes = result.danger_ok.includes
        assert any("vector" in h for h in includes)

    def test_qualified_name_detection(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text(
            "#include <vector>\nint main() { std::vector<int> v; return 0; }\n"
        )
        result = analyze_cpp(src)
        assert result.is_ok
        qnames = result.danger_ok.qualified_names
        assert any("vector" in qn or "std" in qn for qn in qnames)

    def test_define_aliasing_resolved(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("#define PLUS +\nint main() { int x = 1 PLUS 2; return x; }\n")
        result = analyze_cpp(src)
        assert result.is_ok
        assert result.danger_ok.operators["+"] >= 1

    def test_missing_file_returns_err(self, tmp_path):
        result = analyze_cpp(tmp_path / "nonexistent.cpp")
        assert result.is_err

    def test_for_loop_keyword(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("int main() { for (int i = 0; i < 10; i++) {} return 0; }\n")
        result = analyze_cpp(src)
        assert result.is_ok
        assert result.danger_ok.keywords["for"] >= 1

    def test_while_loop_keyword(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("int main() { int i = 0; while (i < 10) { i++; } return 0; }\n")
        result = analyze_cpp(src)
        assert result.is_ok
        assert result.danger_ok.keywords["while"] >= 1

    def test_do_while_loop_keyword(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text(
            "int main() { int i = 0; do { i++; } while (i < 10); return 0; }\n"
        )
        result = analyze_cpp(src)
        assert result.is_ok
        # `while (...)` in a do-while is part of the `do_statement` node itself,
        # not a separate `while_statement`, so only "do" is counted here.
        assert result.danger_ok.keywords["do"] >= 1


# ---------------------------------------------------------------------------
# SourceCheck integration tests
# ---------------------------------------------------------------------------


class TestSourceCheckPython:
    def test_no_violation_yields_ok_packet(self, tmp_path):
        src = tmp_path / "sol.py"
        src.write_text("x = 1 + 2\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("sol.py")])
            check = SourceCheck(
                files=["sol.py"],
                constraints=[OperatorConstraint(tokens=["+"], max_count=5)],
                language="python",
            )
            yields, final = _run_check(check, manifest)
        assert final.is_ok
        assert any(y.is_ok for y in yields)

    def test_operator_violation_non_fatal(self, tmp_path):
        src = tmp_path / "sol.py"
        src.write_text("x = 1 + 2 + 3 + 4\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("sol.py")])
            check = SourceCheck(
                files=["sol.py"],
                constraints=[OperatorConstraint(tokens=["+"], max_count=0)],
                language="python",
            )
            yields, final = _run_check(check, manifest)
        assert final.is_ok
        violations = [y for y in yields if y.is_err]
        assert violations
        v: SourceViolation = violations[0].danger_err
        assert v.count > 0 and v.max_count == 0

    def test_identifier_constraint_list(self, tmp_path):
        src = tmp_path / "sol.py"
        src.write_text("result = list(range(10))\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("sol.py")])
            check = SourceCheck(
                files=["sol.py"],
                constraints=[IdentifierConstraint(names=["list"], max_count=0)],
                language="python",
            )
            yields, final = _run_check(check, manifest)
        assert [y for y in yields if y.is_err]

    def test_import_constraint_numpy(self, tmp_path):
        src = tmp_path / "sol.py"
        src.write_text("import numpy\nx = numpy.array([1])\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("sol.py")])
            check = SourceCheck(
                files=["sol.py"],
                constraints=[ImportConstraint(modules=["numpy"], max_count=0)],
                language="python",
            )
            yields, final = _run_check(check, manifest)
        assert [y for y in yields if y.is_err]

    def test_keyword_constraint_for_loop(self, tmp_path):
        src = tmp_path / "sol.py"
        src.write_text("for i in range(10):\n    pass\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("sol.py")])
            check = SourceCheck(
                files=["sol.py"],
                constraints=[KeywordConstraint(keywords=["for", "while"], max_count=0)],
                language="python",
            )
            yields, final = _run_check(check, manifest)
        assert final.is_ok
        violations = [y for y in yields if y.is_err]
        assert violations
        v: SourceViolation = violations[0].danger_err
        assert v.count > 0 and v.max_count == 0

    def test_keyword_constraint_no_violation(self, tmp_path):
        src = tmp_path / "sol.py"
        src.write_text("x = 1 + 2\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("sol.py")])
            check = SourceCheck(
                files=["sol.py"],
                constraints=[KeywordConstraint(keywords=["for", "while"], max_count=0)],
                language="python",
            )
            yields, final = _run_check(check, manifest)
        assert final.is_ok
        assert not [y for y in yields if y.is_err]

    def test_missing_file_fatal(self, tmp_path):
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([])
            check = SourceCheck(
                files=["missing.py"],
                constraints=[OperatorConstraint(tokens=["+"], max_count=0)],
                language="python",
            )
            yields, final = _run_check(check, manifest)
        assert final.is_err
        err: SourceCheckError = final.danger_err
        assert "missing.py" in err.file

    def test_multiple_files_all_checked(self, tmp_path):
        a = tmp_path / "a.py"
        b = tmp_path / "b.py"
        a.write_text("x = 1 + 2\n")
        b.write_text("y = 3 + 4\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.py"), Path("b.py")])
            check = SourceCheck(
                files=["a.py", "b.py"],
                constraints=[OperatorConstraint(tokens=["+"], max_count=0)],
                language="python",
            )
            yields, final = _run_check(check, manifest)
        violations = [y for y in yields if y.is_err]
        assert len(violations) == 2

    def test_two_constraints_both_fire(self, tmp_path):
        src = tmp_path / "sol.py"
        src.write_text("import numpy\nx = list(range(5))\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("sol.py")])
            check = SourceCheck(
                files=["sol.py"],
                constraints=[
                    ImportConstraint(modules=["numpy"], max_count=0),
                    IdentifierConstraint(names=["list"], max_count=0),
                ],
                language="python",
            )
            yields, final = _run_check(check, manifest)
        violations = [y for y in yields if y.is_err]
        assert len(violations) == 2

    def test_ok_return_is_the_same_manifest(self, tmp_path):
        src = tmp_path / "sol.py"
        src.write_text("x = 1\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("sol.py")])
            check = SourceCheck(
                files=["sol.py"],
                constraints=[],
                language="python",
            )
            _, final = _run_check(check, manifest)
        assert final.is_ok
        assert final.danger_ok is manifest


class TestSourceCheckCpp:
    def test_include_constraint(self, tmp_path):
        src = tmp_path / "sol.cpp"
        src.write_text("#include <vector>\nint main() { return 0; }\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("sol.cpp")])
            check = SourceCheck(
                files=["sol.cpp"],
                constraints=[IncludeConstraint(headers=["<vector>"], max_count=0)],
                language="cpp",
            )
            yields, final = _run_check(check, manifest)
        violations = [y for y in yields if y.is_err]
        assert violations

    def test_no_include_no_violation(self, tmp_path):
        src = tmp_path / "sol.cpp"
        src.write_text("int main() { return 0; }\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("sol.cpp")])
            check = SourceCheck(
                files=["sol.cpp"],
                constraints=[IncludeConstraint(headers=["<vector>"], max_count=0)],
                language="cpp",
            )
            yields, final = _run_check(check, manifest)
        assert final.is_ok
        assert not [y for y in yields if y.is_err]

    def test_keyword_constraint_no_loops(self, tmp_path):
        src = tmp_path / "sol.cpp"
        src.write_text("int main() { for (int i = 0; i < 10; i++) {} return 0; }\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("sol.cpp")])
            check = SourceCheck(
                files=["sol.cpp"],
                constraints=[
                    KeywordConstraint(keywords=["for", "while", "do"], max_count=0)
                ],
                language="cpp",
            )
            yields, final = _run_check(check, manifest)
        assert final.is_ok
        violations = [y for y in yields if y.is_err]
        assert violations
        v: SourceViolation = violations[0].danger_err
        assert v.count > 0 and v.max_count == 0

    def test_operator_define_bypass_caught(self, tmp_path):
        src = tmp_path / "sol.cpp"
        src.write_text("#define ADD +\nint main() { int x = 1 ADD 2; return x; }\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("sol.cpp")])
            check = SourceCheck(
                files=["sol.cpp"],
                constraints=[OperatorConstraint(tokens=["+"], max_count=0)],
                language="cpp",
            )
            yields, final = _run_check(check, manifest)
        violations = [y for y in yields if y.is_err]
        assert violations

    def test_ok_return_is_same_manifest(self, tmp_path):
        src = tmp_path / "sol.cpp"
        src.write_text("int main() { return 0; }\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("sol.cpp")])
            check = SourceCheck(
                files=["sol.cpp"],
                constraints=[],
                language="cpp",
            )
            _, final = _run_check(check, manifest)
        assert final.is_ok
        assert final.danger_ok is manifest
