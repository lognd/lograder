"""Integration tests for GXXBuild + OutputCompareTest + ASanTest + CompileCheckTest."""

import subprocess
from pathlib import Path

import pytest

from lograder.pipeline.build.gxx import GXXBuild
from lograder.pipeline.config import config
from lograder.pipeline.input.local_directory import LocalDirectory
from lograder.pipeline.pipeline import Pipeline
from lograder.pipeline.score import AllOrNothingScorer, TestCaseScorer
from lograder.pipeline.test.asan import ASanCase, ASanTest
from lograder.pipeline.test.compile_check import CompileCase, CompileCheckTest
from lograder.pipeline.test.output_compare import (
    OutputCompareCase,
    OutputCompareTest,
)

_HAS_GPP = subprocess.run(["which", "g++"], capture_output=True).returncode == 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_adder(directory: Path) -> None:
    """Write a correct adder program: reads two ints from args, prints sum."""
    src = (
        "#include <iostream>\n"
        "#include <cstdlib>\n"
        "int main(int argc, char** argv){\n"
        '    if(argc < 3){ std::cerr << "usage: adder a b\\n"; return 1; }\n'
        '    std::cout << atoi(argv[1]) + atoi(argv[2]) << "\\n";\n'
        "    return 0;\n"
        "}\n"
    )
    (directory / "adder.cpp").write_text(src, encoding="utf-8")


def _write_bad_adder(directory: Path) -> None:
    """Write a broken adder that does multiplication instead."""
    src = (
        "#include <iostream>\n"
        "#include <cstdlib>\n"
        "int main(int argc, char** argv){\n"
        '    std::cout << atoi(argv[1]) * atoi(argv[2]) << "\\n";\n'
        "    return 0;\n"
        "}\n"
    )
    (directory / "adder.cpp").write_text(src, encoding="utf-8")


_ADDER_CASES = [
    OutputCompareCase(
        name="add_pos", args=["3", "4"], stdin=b"", expected_stdout="7\n"
    ),
    OutputCompareCase(
        name="add_neg", args=["-2", "5"], stdin=b"", expected_stdout="3\n"
    ),
    OutputCompareCase(
        name="add_zero", args=["0", "0"], stdin=b"", expected_stdout="0\n"
    ),
]


# ---------------------------------------------------------------------------
# GXXBuild + OutputCompareTest
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_gxx_pipeline_correct_submission(tmp_path):
    submission = tmp_path / "submission"
    submission.mkdir()
    _write_adder(submission)

    with config(root_directory=submission):
        pipeline = Pipeline()
        pipeline.add(LocalDirectory())
        build = GXXBuild(sources=["adder.cpp"], output="adder")
        build.scorer = AllOrNothingScorer(10.0, label="Build")
        pipeline.add(build)

        tests = OutputCompareTest("adder", _ADDER_CASES)
        tests.scorer = TestCaseScorer(
            {"add_pos": 10.0, "add_neg": 10.0, "add_zero": 10.0}, label="Tests"
        )
        pipeline.add(tests)

        score = pipeline()

    assert score.total().earned == 40.0
    assert score.total().possible == 40.0


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_gxx_pipeline_wrong_submission(tmp_path):
    submission = tmp_path / "submission"
    submission.mkdir()
    _write_bad_adder(submission)

    with config(root_directory=submission):
        pipeline = Pipeline()
        pipeline.add(LocalDirectory())
        build = GXXBuild(sources=["adder.cpp"], output="adder")
        build.scorer = AllOrNothingScorer(10.0, label="Build")
        pipeline.add(build)

        tests = OutputCompareTest("adder", _ADDER_CASES)
        tests.scorer = TestCaseScorer(
            {"add_pos": 10.0, "add_neg": 10.0, "add_zero": 10.0}, label="Tests"
        )
        pipeline.add(tests)

        score = pipeline()

    assert (
        score.total().earned == 20.0
    )  # build passes, add_zero passes (0*0=0), others fail


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_gxx_pipeline_compile_error(tmp_path):
    submission = tmp_path / "submission"
    submission.mkdir()
    (submission / "adder.cpp").write_text("this does not compile", encoding="utf-8")

    with config(root_directory=submission):
        pipeline = Pipeline()
        pipeline.add(LocalDirectory())
        build = GXXBuild(sources=["adder.cpp"], output="adder")
        build.scorer = AllOrNothingScorer(10.0, label="Build")
        pipeline.add(build)

        tests = OutputCompareTest("adder", _ADDER_CASES)
        tests.scorer = TestCaseScorer(
            {"add_pos": 10.0, "add_neg": 10.0, "add_zero": 10.0}, label="Tests"
        )
        pipeline.add(tests)

        score = pipeline()

    # Build fails -> 0 for build, 0/possible for tests (skipped)
    assert score.total().earned == 0.0
    assert score.total().possible == 40.0


# ---------------------------------------------------------------------------
# CompileCheckTest integration
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_compile_check_pipeline(tmp_path):
    submission = tmp_path / "submission"
    submission.mkdir()
    _write_adder(submission)

    with config(root_directory=submission):
        pipeline = Pipeline()
        pipeline.add(LocalDirectory())
        build = GXXBuild(sources=["adder.cpp"], output="adder")
        build.scorer = AllOrNothingScorer(10.0, label="Build")
        pipeline.add(build)

        cc = CompileCheckTest(
            [
                CompileCase(
                    name="int_literal_compiles",
                    code="int x = 42; (void)x;",
                    should_compile=True,
                ),
                CompileCase(
                    name="string_to_int_forbidden",
                    code='int x = "hello"; (void)x;',
                    should_compile=False,
                ),
            ]
        )
        cc.scorer = TestCaseScorer(
            {"int_literal_compiles": 5.0, "string_to_int_forbidden": 5.0},
            label="Compile Checks",
        )
        pipeline.add(cc)

        score = pipeline()

    assert score.total().earned == 20.0


# ---------------------------------------------------------------------------
# ASanTest integration
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_GPP, reason="g++ not installed")
def test_asan_pipeline_clean_code(tmp_path):
    """A correct program compiled with ASan should pass all cases."""
    src = (
        "#include <iostream>\n"
        "#include <cstdlib>\n"
        "int main(int argc, char** argv){\n"
        "    int n = argc > 1 ? atoi(argv[1]) : 5;\n"
        "    int* arr = new int[n];\n"
        "    for(int i = 0; i < n; i++) arr[i] = i;\n"
        '    std::cout << arr[0] << "\\n";\n'
        "    delete[] arr;\n"
        "    return 0;\n"
        "}\n"
    )
    submission = tmp_path / "submission"
    submission.mkdir()
    (submission / "prog.cpp").write_text(src, encoding="utf-8")

    with config(root_directory=submission):
        pipeline = Pipeline()
        pipeline.add(LocalDirectory())
        build = GXXBuild(
            sources=["prog.cpp"],
            output="prog",
            sanitizers=["address"],
        )
        build.scorer = AllOrNothingScorer(5.0, label="Build")
        pipeline.add(build)

        asan = ASanTest(
            "prog",
            [
                ASanCase(name="small_n", args=["5"]),
                ASanCase(name="large_n", args=["1000"]),
            ],
        )
        asan.scorer = AllOrNothingScorer(10.0, label="Memory Safety")
        pipeline.add(asan)

        score = pipeline()

    assert score.total().earned == 15.0
