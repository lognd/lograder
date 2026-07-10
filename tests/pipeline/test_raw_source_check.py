"""Unit tests for RawSourceCheck / ForbiddenTokenConstraint."""

from __future__ import annotations

from pathlib import Path

from lograder.pipeline.check.source.raw_source_check import (
    ForbiddenTokenConstraint,
    RawSourceCheck,
    RawSourceCheckError,
)
from lograder.pipeline.check.source.source_check import SourceViolation
from lograder.pipeline.config import config
from lograder.pipeline.types.parcels import Manifest


def _run_check(check: RawSourceCheck, manifest: Manifest):
    """Drain the generator; return (list_of_yields, final_result)."""
    gen = check(manifest)
    yields = []
    try:
        while True:
            yields.append(next(gen))
    except StopIteration as e:
        return yields, e.value


class TestForbiddenTokenConstraint:
    def test_clean_file_yields_ok(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("int main() { return 0; }\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.cpp")])
            check = RawSourceCheck(
                files=["a.cpp"],
                constraints=[ForbiddenTokenConstraint(tokens=["malloc"], max_count=0)],
            )
            yields, final = _run_check(check, manifest)
        assert final.is_ok
        assert any(y.is_ok for y in yields)
        assert not any(y.is_err for y in yields)

    def test_forbidden_token_in_code_is_caught(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("void* p = malloc(10);\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.cpp")])
            check = RawSourceCheck(
                files=["a.cpp"],
                constraints=[ForbiddenTokenConstraint(tokens=["malloc"], max_count=0)],
            )
            yields, final = _run_check(check, manifest)
        assert final.is_ok
        violations = [y for y in yields if y.is_err]
        assert len(violations) == 1
        v: SourceViolation = violations[0].danger_err
        assert v.count == 1
        assert v.max_count == 0

    def test_forbidden_token_in_comment_not_caught(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text(
            "// TODO: don't use malloc here\n"
            "/* malloc is also forbidden */\n"
            "int main() { return 0; }\n"
        )
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.cpp")])
            check = RawSourceCheck(
                files=["a.cpp"],
                constraints=[ForbiddenTokenConstraint(tokens=["malloc"], max_count=0)],
            )
            yields, final = _run_check(check, manifest)
        assert final.is_ok
        assert not any(y.is_err for y in yields)

    def test_forbidden_token_in_string_not_caught(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text('const char* msg = "please do not malloc";\n')
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.cpp")])
            check = RawSourceCheck(
                files=["a.cpp"],
                constraints=[ForbiddenTokenConstraint(tokens=["malloc"], max_count=0)],
            )
            yields, final = _run_check(check, manifest)
        assert final.is_ok
        assert not any(y.is_err for y in yields)

    def test_forbidden_token_in_char_literal_not_caught(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("char c = 'x';\nint x2 = 1;\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.cpp")])
            check = RawSourceCheck(
                files=["a.cpp"],
                constraints=[ForbiddenTokenConstraint(tokens=["x"], max_count=0)],
            )
            yields, final = _run_check(check, manifest)
        assert final.is_ok
        violations = [y for y in yields if y.is_err]
        # Only x2's "x" substring shouldn't match (word boundary), and the
        # char literal 'x' is stripped -- so no whole-word "x" survives.
        assert not violations

    def test_qualified_name_token(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("#include <algorithm>\nvoid f() { std::sort(a, b); }\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.cpp")])
            check = RawSourceCheck(
                files=["a.cpp"],
                constraints=[
                    ForbiddenTokenConstraint(tokens=["std::sort"], max_count=0)
                ],
            )
            yields, final = _run_check(check, manifest)
        assert final.is_ok
        violations = [y for y in yields if y.is_err]
        assert len(violations) == 1
        assert violations[0].danger_err.count == 1

    def test_qualified_name_token_whitespace_tolerant(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("void f() { std :: sort(a, b); }\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.cpp")])
            check = RawSourceCheck(
                files=["a.cpp"],
                constraints=[
                    ForbiddenTokenConstraint(tokens=["std::sort"], max_count=0)
                ],
            )
            yields, final = _run_check(check, manifest)
        violations = [y for y in yields if y.is_err]
        assert len(violations) == 1

    def test_keyword_token_matched_unlike_identifier_constraint(self, tmp_path):
        # This is exactly the case IdentifierConstraint can never catch:
        # `throw`/`try`/`catch`/`new`/`delete`/`template` are keyword nodes,
        # not identifier nodes, in the tree-sitter C++ grammar.
        src = tmp_path / "a.cpp"
        src.write_text(
            "void f() { try { throw 1; } catch (int e) {} int* p = new int; }\n"
        )
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.cpp")])
            check = RawSourceCheck(
                files=["a.cpp"],
                constraints=[
                    ForbiddenTokenConstraint(
                        tokens=["throw", "try", "catch", "new"], max_count=0
                    )
                ],
            )
            yields, final = _run_check(check, manifest)
        violations = [y for y in yields if y.is_err]
        assert len(violations) == 1
        assert violations[0].danger_err.count == 4

    def test_delete_special_member_not_counted(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("struct Foo { Foo(Foo&&) = delete; };\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.cpp")])
            check = RawSourceCheck(
                files=["a.cpp"],
                constraints=[ForbiddenTokenConstraint(tokens=["delete"], max_count=0)],
            )
            yields, final = _run_check(check, manifest)
        assert not any(y.is_err for y in yields)

    def test_delete_expression_still_counted(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("void f(int* p) { delete p; }\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.cpp")])
            check = RawSourceCheck(
                files=["a.cpp"],
                constraints=[ForbiddenTokenConstraint(tokens=["delete"], max_count=0)],
            )
            yields, final = _run_check(check, manifest)
        violations = [y for y in yields if y.is_err]
        assert len(violations) == 1
        assert violations[0].danger_err.count == 1

    def test_system_header_declarations_not_counted(self, tmp_path):
        # SourceCheck's IdentifierConstraint would flag `printf` merely from
        # #include <stdio.h> being pulled into the preprocessed TU, even if
        # the student never calls it. RawSourceCheck scans the original
        # source text, so an unused #include never triggers a match.
        src = tmp_path / "a.cpp"
        src.write_text("#include <stdio.h>\nint main() { return 0; }\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.cpp")])
            check = RawSourceCheck(
                files=["a.cpp"],
                constraints=[ForbiddenTokenConstraint(tokens=["printf"], max_count=0)],
            )
            yields, final = _run_check(check, manifest)
        assert not any(y.is_err for y in yields)

    def test_missing_file_fatal(self, tmp_path):
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("missing.cpp")])
            check = RawSourceCheck(
                files=["missing.cpp"],
                constraints=[ForbiddenTokenConstraint(tokens=["x"], max_count=0)],
            )
            _, final = _run_check(check, manifest)
        assert final.is_err
        assert isinstance(final.danger_err, RawSourceCheckError)

    def test_multiple_files_all_checked(self, tmp_path):
        (tmp_path / "a.cpp").write_text("int x = malloc_free_pair;\n")
        (tmp_path / "b.cpp").write_text("void* p = malloc(1);\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.cpp"), Path("b.cpp")])
            check = RawSourceCheck(
                files=["a.cpp", "b.cpp"],
                constraints=[ForbiddenTokenConstraint(tokens=["malloc"], max_count=0)],
            )
            yields, final = _run_check(check, manifest)
        assert final.is_ok
        violations = [y for y in yields if y.is_err]
        # "malloc" appears only as a substring in a.cpp's identifier
        # (word-boundary excludes it) but as a whole word in b.cpp.
        assert len(violations) == 1
        assert violations[0].danger_err.file == "b.cpp"

    def test_max_count_caps_rather_than_bans(self, tmp_path):
        src = tmp_path / "a.cpp"
        src.write_text("int a = new_val + new_val + new_val;\n")
        with config(root_directory=tmp_path):
            manifest = Manifest.from_flat([Path("a.cpp")])
            check = RawSourceCheck(
                files=["a.cpp"],
                constraints=[ForbiddenTokenConstraint(tokens=["new"], max_count=1)],
            )
            yields, final = _run_check(check, manifest)
        # "new_val" never matches whole-word "new", so 0 <= 1 -> no violation.
        assert not any(y.is_err for y in yields)
