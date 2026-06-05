# mypy: ignore-errors
"""Unit tests for the Makefile parser (no subprocess, no real build)."""

from pathlib import Path

import pytest

from lograder.process.parsers.makefile import (
    ParsedMakefile,
    _expand_vars,
    _match_pattern,
    artifacts_from_makefile,
    parse_makefile,
)

# ---------------------------------------------------------------------------
# _match_pattern
# ---------------------------------------------------------------------------


def test_match_pattern_plain_equality():
    assert _match_pattern("foo.o", "foo.o") == ""


def test_match_pattern_prefix_suffix():
    assert _match_pattern("%.o", "main.o") == "main"


def test_match_pattern_prefix_only():
    assert _match_pattern("%_test", "foo_test") == "foo"


def test_match_pattern_suffix_only():
    assert _match_pattern("lib%", "libfoo") == "foo"


def test_match_pattern_no_match():
    assert _match_pattern("%.o", "main.c") is None


def test_match_pattern_no_percent():
    assert _match_pattern("foo.o", "bar.o") is None


def test_match_pattern_stem_can_be_empty():
    assert _match_pattern("%.o", ".o") == ""


# ---------------------------------------------------------------------------
# _expand_vars
# ---------------------------------------------------------------------------


def test_expand_vars_simple():
    assert _expand_vars("$(CC)", {"CC": "gcc"}) == "gcc"


def test_expand_vars_curly():
    assert _expand_vars("${CC}", {"CC": "clang"}) == "clang"


def test_expand_vars_multiple():
    assert _expand_vars("$(CC) $(CFLAGS)", {"CC": "gcc", "CFLAGS": "-O2"}) == "gcc -O2"


def test_expand_vars_nested():
    assert _expand_vars("$($(TOOL))", {"TOOL": "CC", "CC": "gcc"}) == "gcc"


def test_expand_vars_unknown_returns_empty():
    assert _expand_vars("$(UNKNOWN)", {}) == ""


def test_expand_vars_automatic_var_unchanged():
    # $@ and friends should not be touched
    assert _expand_vars("$@", {}) == "$@"
    assert _expand_vars("$<", {}) == "$<"


def test_expand_vars_patsubst():
    result = _expand_vars("$(patsubst %.c,%.o,main.c utils.c)", {})
    assert result == "main.o utils.o"


def test_expand_vars_addprefix():
    result = _expand_vars("$(addprefix build/,main.o utils.o)", {})
    assert result == "build/main.o build/utils.o"


def test_expand_vars_addsuffix():
    result = _expand_vars("$(addsuffix .o,main utils)", {})
    assert result == "main.o utils.o"


def test_expand_vars_notdir():
    result = _expand_vars("$(notdir src/main.c build/utils.c)", {})
    assert result == "main.c utils.c"


def test_expand_vars_basename():
    result = _expand_vars("$(basename src/main.c)", {})
    assert result == "src/main"


def test_expand_vars_sort():
    result = _expand_vars("$(sort b a c a)", {})
    assert result == "a b c"


def test_expand_vars_filter():
    result = _expand_vars("$(filter %.o,main.o main.c utils.o)", {})
    assert result == "main.o utils.o"


def test_expand_vars_filter_out():
    result = _expand_vars("$(filter-out %.c,main.o main.c utils.o)", {})
    assert result == "main.o utils.o"


def test_expand_vars_subst():
    result = _expand_vars("$(subst .c,.o,main.c)", {})
    assert result == "main.o"


# ---------------------------------------------------------------------------
# parse_makefile -- variable assignment
# ---------------------------------------------------------------------------


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "Makefile"
    p.write_text(content)
    return p


def test_parse_simple_assignment(tmp_path):
    mf = _write(tmp_path, "CC = gcc\n")
    parsed = parse_makefile(mf)
    assert parsed.variables["CC"] == "gcc"


def test_parse_simple_expansion_assignment(tmp_path):
    mf = _write(tmp_path, "CC := clang\n")
    parsed = parse_makefile(mf)
    assert parsed.variables["CC"] == "clang"


def test_parse_append_assignment(tmp_path):
    mf = _write(tmp_path, "FLAGS = -O2\nFLAGS += -g\n")
    parsed = parse_makefile(mf)
    assert parsed.variables["FLAGS"] == "-O2 -g"


def test_parse_conditional_assignment(tmp_path):
    mf = _write(tmp_path, "CC ?= gcc\nCC ?= clang\n")
    parsed = parse_makefile(mf)
    assert parsed.variables["CC"] == "gcc"


def test_parse_variable_reference_in_assignment(tmp_path):
    mf = _write(tmp_path, "SRCS = main.c\nOBJS = $(patsubst %.c,%.o,$(SRCS))\n")
    parsed = parse_makefile(mf)
    assert parsed.variables["OBJS"] == "main.o"


def test_parse_define_endef(tmp_path):
    mf = _write(tmp_path, "define MSG\nhello world\nendef\n")
    parsed = parse_makefile(mf)
    assert "hello world" in parsed.variables["MSG"]


# ---------------------------------------------------------------------------
# parse_makefile -- rules
# ---------------------------------------------------------------------------


def test_parse_explicit_rule(tmp_path):
    mf = _write(
        tmp_path, "myprogram: main.o utils.o\n\tgcc -o myprogram main.o utils.o\n"
    )
    parsed = parse_makefile(mf)
    rules = [r for r in parsed.rules if "myprogram" in r.targets]
    assert rules
    assert "main.o" in rules[0].prerequisites


def test_parse_pattern_rule(tmp_path):
    mf = _write(tmp_path, "%.o: %.c\n\t$(CC) -c $< -o $@\n")
    parsed = parse_makefile(mf)
    assert any(r.is_pattern for r in parsed.rules)
    pattern_rules = [r for r in parsed.rules if r.is_pattern]
    assert "%.o" in pattern_rules[0].targets


def test_parse_phony_targets(tmp_path):
    mf = _write(tmp_path, ".PHONY: all clean\nall: myprogram\n")
    parsed = parse_makefile(mf)
    assert "all" in parsed.phony
    assert "clean" in parsed.phony


def test_parse_multiple_targets_on_one_line(tmp_path):
    mf = _write(tmp_path, "foo bar: baz.c\n\tgcc -o $@ $<\n")
    parsed = parse_makefile(mf)
    rule = next(r for r in parsed.rules if "foo" in r.targets)
    assert "bar" in rule.targets


def test_recipe_lines_not_parsed_as_rules(tmp_path):
    mf = _write(tmp_path, "all:\n\tgcc -o all main.c\n")
    parsed = parse_makefile(mf)
    # No rule should have "gcc" as a target
    assert all("gcc" not in r.targets for r in parsed.rules)


def test_parse_variable_target(tmp_path):
    mf = _write(tmp_path, "TARGET = sorter\n$(TARGET): main.o\n\tgcc -o $@ $^\n")
    parsed = parse_makefile(mf)
    assert any("sorter" in r.targets for r in parsed.rules)


def test_parse_continuation_line(tmp_path):
    mf = _write(tmp_path, "SRCS = \\\n    main.c \\\n    utils.c\n")
    parsed = parse_makefile(mf)
    assert "main.c" in parsed.variables["SRCS"]
    assert "utils.c" in parsed.variables["SRCS"]


def test_parse_inline_comment_stripped(tmp_path):
    mf = _write(tmp_path, "CC = gcc  # the compiler\n")
    parsed = parse_makefile(mf)
    assert parsed.variables["CC"] == "gcc"


def test_parse_double_colon_rule(tmp_path):
    mf = _write(tmp_path, "all:: main.o\n\tgcc -o all main.o\n")
    parsed = parse_makefile(mf)
    assert any("all" in r.targets for r in parsed.rules)


# ---------------------------------------------------------------------------
# artifacts_from_makefile
# ---------------------------------------------------------------------------


def test_artifacts_explicit_target(tmp_path):
    mf = _write(tmp_path, "sorter: main.o utils.o\n\tgcc -o sorter main.o utils.o\n")
    result = artifacts_from_makefile(mf, [])
    assert "sorter" in result
    assert result["sorter"] == tmp_path / "sorter"


def test_artifacts_phony_excluded(tmp_path):
    mf = _write(tmp_path, ".PHONY: all clean\nall: sorter\nsorter: main.o\n")
    result = artifacts_from_makefile(mf, [])
    assert "all" not in result
    assert "clean" not in result
    assert "sorter" in result


def test_artifacts_pattern_expansion(tmp_path):
    mf = _write(tmp_path, "%.o: %.c\n\t$(CC) -c $< -o $@\n")
    src_files = [tmp_path / "main.c", tmp_path / "utils.c"]
    result = artifacts_from_makefile(mf, src_files)
    assert "main.o" in result
    assert "utils.o" in result


def test_artifacts_pattern_expansion_cpp(tmp_path):
    mf = _write(tmp_path, "%.o: %.cpp\n\t$(CXX) -c $< -o $@\n")
    src_files = [tmp_path / "main.cpp", tmp_path / "graph.cpp"]
    result = artifacts_from_makefile(mf, src_files)
    assert "main.o" in result
    assert "graph.o" in result


def test_artifacts_no_pattern_match_for_wrong_extension(tmp_path):
    mf = _write(tmp_path, "%.o: %.c\n\t$(CC) -c $< -o $@\n")
    src_files = [tmp_path / "main.cpp"]  # .cpp won't match %.c
    result = artifacts_from_makefile(mf, src_files)
    assert "main.o" not in result


def test_artifacts_special_targets_excluded(tmp_path):
    mf = _write(
        tmp_path,
        ".SUFFIXES: .c .o\n.c.o:\n\t$(CC) -c $<\nsorter: main.o\n",
    )
    result = artifacts_from_makefile(mf, [tmp_path / "main.c"])
    assert ".SUFFIXES" not in result
    assert "sorter" in result


def test_artifacts_variable_in_target(tmp_path):
    mf = _write(tmp_path, "TARGET = myapp\n$(TARGET): main.o\n\tgcc -o $@ $^\n")
    result = artifacts_from_makefile(mf, [])
    assert "myapp" in result


def test_artifacts_path_target_uses_basename_as_key(tmp_path):
    mf = _write(tmp_path, "bin/myapp: main.o\n\tgcc -o $@ $^\n")
    result = artifacts_from_makefile(mf, [])
    assert "myapp" in result


def test_artifacts_complex_makefile(tmp_path):
    """Realistic student Makefile."""
    content = """\
CC = gcc
CFLAGS = -Wall -O2
TARGET = wordcount
SRCS = wordcount.c utils.c
OBJS = $(patsubst %.c,%.o,$(SRCS))

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
\t$(CC) $(CFLAGS) -o $@ $^

%.o: %.c
\t$(CC) $(CFLAGS) -c $< -o $@

clean:
\trm -f $(OBJS) $(TARGET)
"""
    mf = _write(tmp_path, content)
    src_files = [tmp_path / "wordcount.c", tmp_path / "utils.c"]
    result = artifacts_from_makefile(mf, src_files)

    assert "wordcount" in result
    assert "wordcount.o" in result
    assert "utils.o" in result
    assert "all" not in result
    assert "clean" not in result
