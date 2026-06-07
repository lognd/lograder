# mypy: ignore-errors
from __future__ import annotations

from lograder.process.parsers.nm import parse_nm_output


def test_empty_output_returns_empty_list():
    assert parse_nm_output("") == []


def test_blank_lines_ignored():
    output = "\n\n  \n"
    assert parse_nm_output(output) == []


def test_defined_text_symbol():
    symbols = parse_nm_output("0000000000001149 T main")
    assert len(symbols) == 1
    s = symbols[0]
    assert s.name == "main"
    assert s.type == "T"
    assert s.address == int("0000000000001149", 16)
    assert s.is_defined is True
    assert s.is_text is True
    assert s.is_external is True  # uppercase = external


def test_undefined_symbol():
    symbols = parse_nm_output("                 U printf")
    assert len(symbols) == 1
    s = symbols[0]
    assert s.name == "printf"
    assert s.type == "U"
    assert s.is_defined is False
    assert s.is_text is False
    assert s.is_external is True


def test_local_symbol_lowercase_type():
    symbols = parse_nm_output("0000000000000000 t helper")
    assert len(symbols) == 1
    s = symbols[0]
    assert s.type == "t"
    assert s.is_external is False  # lowercase = local
    assert s.is_text is True


def test_multiple_symbols():
    output = """\
0000000000001149 T main
0000000000001100 T foo
                 U malloc
"""
    symbols = parse_nm_output(output)
    names = {s.name for s in symbols}
    assert names == {"main", "foo", "malloc"}


def test_data_symbol():
    symbols = parse_nm_output("0000000000004010 D global_var")
    assert len(symbols) == 1
    s = symbols[0]
    assert s.type == "D"
    assert s.is_text is False
    assert s.is_defined is True


def test_bss_symbol():
    symbols = parse_nm_output("0000000000004020 B uninit_global")
    assert len(symbols) == 1
    s = symbols[0]
    assert s.type == "B"
    assert s.is_defined is True
    assert s.is_text is False


def test_file_header_lines_skipped():
    output = """\
mylib.a:
mylib.o:
0000000000001149 T exported_fn
"""
    symbols = parse_nm_output(output)
    assert len(symbols) == 1
    assert symbols[0].name == "exported_fn"


def test_demangled_cpp_name():
    output = "0000000000001200 T _ZN3FooC1Ev"
    symbols = parse_nm_output(output)
    assert len(symbols) == 1
    assert symbols[0].name == "_ZN3FooC1Ev"
