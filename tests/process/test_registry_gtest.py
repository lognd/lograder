from __future__ import annotations

from lograder.process.registry.gtest import GTestArgs, GTestExecutable

# ---------------------------------------------------------------------------
# GTestArgs emit
# ---------------------------------------------------------------------------


def test_default_args_emit_empty():
    args = GTestArgs()
    assert args.emit() == []


def test_gtest_filter():
    args = GTestArgs(gtest_filter="MathSuite.*")
    tokens = args.emit()
    assert any("gtest_filter" in t and "MathSuite.*" in t for t in tokens)


def test_gtest_output():
    args = GTestArgs(gtest_output="xml:/tmp/out.xml")
    tokens = args.emit()
    assert any("gtest_output" in t and "xml:/tmp/out.xml" in t for t in tokens)


def test_gtest_also_run_disabled():
    args = GTestArgs(gtest_also_run_disabled_tests=True)
    assert any("gtest_also_run_disabled_tests" in t for t in args.emit())


def test_gtest_repeat():
    args = GTestArgs(gtest_repeat=5)
    tokens = args.emit()
    assert any("gtest_repeat" in t and "5" in t for t in tokens)


def test_gtest_shuffle():
    args = GTestArgs(gtest_shuffle=True)
    assert any("gtest_shuffle" in t for t in args.emit())


def test_gtest_random_seed():
    args = GTestArgs(gtest_random_seed=42)
    tokens = args.emit()
    assert any("gtest_random_seed" in t and "42" in t for t in tokens)


def test_gtest_recreate_environments():
    args = GTestArgs(gtest_recreate_environments_when_repeating=True)
    assert any("gtest_recreate_environments_when_repeating" in t for t in args.emit())


def test_gtest_fail_fast():
    args = GTestArgs(gtest_fail_fast=True)
    assert any("gtest_fail_fast" in t for t in args.emit())


def test_gtest_brief():
    args = GTestArgs(gtest_brief=True)
    assert any("gtest_brief" in t for t in args.emit())


def test_gtest_print_time():
    args = GTestArgs(gtest_print_time=True)
    assert any("gtest_print_time" in t for t in args.emit())


def test_gtest_death_test_style():
    args = GTestArgs(gtest_death_test_style="fast")
    tokens = args.emit()
    assert any("gtest_death_test_style" in t and "fast" in t for t in tokens)


def test_gtest_list_tests():
    args = GTestArgs(gtest_list_tests=True)
    assert any("gtest_list_tests" in t for t in args.emit())


def test_multiple_flags_together():
    args = GTestArgs(
        gtest_filter="Suite.*",
        gtest_shuffle=True,
        gtest_random_seed=99,
    )
    tokens = args.emit()
    assert any("gtest_filter" in t for t in tokens)
    assert any("gtest_shuffle" in t for t in tokens)
    assert any("gtest_random_seed" in t for t in tokens)


def test_false_flags_not_emitted():
    args = GTestArgs(gtest_shuffle=False, gtest_fail_fast=False)
    tokens = args.emit()
    assert not any("gtest_shuffle" in t for t in tokens)
    assert not any("gtest_fail_fast" in t for t in tokens)


def test_gtest_executable_instantiable():
    exe = GTestExecutable()
    assert exe is not None


def test_gtest_check_runnable_returns_result():
    exe = GTestExecutable()
    result = exe.check_runnable()
    assert result.is_ok or result.is_err
