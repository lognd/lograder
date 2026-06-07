# mypy: ignore-errors
import subprocess
from pathlib import Path

import pytest

from lograder.pipeline.config import config
from lograder.pipeline.test.output_compare import (
    ComparisonMode,
    OutputCompareCase,
    OutputCompareError,
    OutputCompareFailure,
    OutputCompareSuccess,
    OutputCompareTest,
    compare_outputs,
    make_unified_diff,
)
from lograder.pipeline.types.artifacts import CMakeArtifact, FileArtifact


@pytest.fixture(scope="module")
def echo_bin(tmp_path_factory):
    d = tmp_path_factory.mktemp("echo_bin")
    src = d / "main.c"
    src.write_text(
        """
#include <stdio.h>
int main(int argc, char **argv) {
    for (int i = 1; i < argc; i++) {
        if (i > 1) printf(" ");
        printf("%s", argv[i]);
    }
    printf("\\n");
    return 0;
}
""",
        encoding="utf-8",
    )
    binary = d / "echo"
    subprocess.run(["gcc", "-o", str(binary), str(src)], check=True)
    return binary


def test_compare_outputs_exact_match():
    assert compare_outputs("hello\n", "hello\n", ComparisonMode.EXACT)


def test_compare_outputs_exact_mismatch():
    assert not compare_outputs("hello\n", "hello", ComparisonMode.EXACT)


def test_compare_outputs_strip_matches_trimmed():
    assert compare_outputs("  hello  \n", "hello", ComparisonMode.STRIP)


def test_compare_outputs_strip_rejects_different():
    assert not compare_outputs("hello", "world", ComparisonMode.STRIP)


def test_compare_outputs_ignore_trailing_whitespace_matches():
    assert compare_outputs(
        "hello   \nworld   \n",
        "hello\nworld\n",
        ComparisonMode.IGNORE_TRAILING_WHITESPACE,
    )


def test_compare_outputs_ignore_trailing_whitespace_rejects_middle():
    assert not compare_outputs(
        "hel lo\n", "hello\n", ComparisonMode.IGNORE_TRAILING_WHITESPACE
    )


def test_make_unified_diff_produces_diff_string():
    diff = make_unified_diff("expected\n", "actual\n")
    assert "expected" in diff
    assert "actual" in diff


def test_make_unified_diff_identical_strings_empty():
    diff = make_unified_diff("same\n", "same\n")
    assert diff == ""


def test_output_compare_test_missing_artifact():
    test = OutputCompareTest("missing", [])
    gen = test({})
    try:
        while True:
            next(gen)
    except StopIteration as e:
        result = e.value
    assert result.is_err
    assert isinstance(result.danger_err, OutputCompareError)


def test_output_compare_test_non_file_artifact():
    artifact = CMakeArtifact(
        name="echo",
        target_type="EXECUTABLE",
        build_dir=Path("/tmp"),
    )
    test = OutputCompareTest("echo", [])
    gen = test({"echo": artifact})
    try:
        while True:
            next(gen)
    except StopIteration as e:
        result = e.value
    assert result.is_err
    assert isinstance(result.danger_err, OutputCompareError)


def test_output_compare_test_passing_case(echo_bin):
    with config(root_directory=echo_bin.parent):
        artifact = FileArtifact(path=echo_bin)
        cases = [
            OutputCompareCase(name="hello", args=["hello"], expected_stdout="hello\n")
        ]
        test = OutputCompareTest("echo", cases)
        packets = []
        gen = test({"echo": artifact})
        try:
            while True:
                packets.append(next(gen))
        except StopIteration as e:
            result = e.value

    assert result.is_ok
    assert len(packets) == 1
    assert packets[0].is_ok
    assert isinstance(packets[0].danger_ok, OutputCompareSuccess)


def test_output_compare_test_failing_case(echo_bin):
    with config(root_directory=echo_bin.parent):
        artifact = FileArtifact(path=echo_bin)
        cases = [
            OutputCompareCase(name="wrong", args=["hello"], expected_stdout="goodbye\n")
        ]
        test = OutputCompareTest("echo", cases)
        packets = []
        gen = test({"echo": artifact})
        try:
            while True:
                packets.append(next(gen))
        except StopIteration as e:
            result = e.value

    assert result.is_ok
    assert len(packets) == 1
    assert packets[0].is_err
    assert isinstance(packets[0].danger_err, OutputCompareFailure)


def test_output_compare_test_exit_code_check(echo_bin):
    with config(root_directory=echo_bin.parent):
        artifact = FileArtifact(path=echo_bin)
        cases = [
            OutputCompareCase(
                name="bad_exit",
                args=["hello"],
                expected_stdout="hello\n",
                expected_exit_code=1,
            )
        ]
        test = OutputCompareTest("echo", cases)
        packets = []
        gen = test({"echo": artifact})
        try:
            while True:
                packets.append(next(gen))
        except StopIteration:
            pass

    assert len(packets) == 1
    assert packets[0].is_err


def test_output_compare_test_returns_artifacts_unchanged(echo_bin):
    with config(root_directory=echo_bin.parent):
        artifact = FileArtifact(path=echo_bin)
        artifacts = {"echo": artifact}
        cases = [OutputCompareCase(name="hi", args=["hi"], expected_stdout="hi\n")]
        test = OutputCompareTest("echo", cases)
        gen = test(artifacts)
        try:
            while True:
                next(gen)
        except StopIteration as e:
            result = e.value

    assert result.is_ok
    assert result.danger_ok is artifacts
