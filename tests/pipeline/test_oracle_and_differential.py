# mypy: ignore-errors
import subprocess
from pathlib import Path

import pytest

import lograder.output.layout.process.executable  # register ExecutableData layout
import lograder.output.layout.test.differential  # register Differential* layouts
from lograder.common import Err, Ok
from lograder.pipeline.config import config
from lograder.pipeline.test.differential import (
    DifferentialError,
    DifferentialFailure,
    DifferentialSuccess,
    DifferentialTest,
)
from lograder.pipeline.test.oracle import OracleInput, cases_from_matrix, oracle_cases
from lograder.pipeline.test.output_compare import ComparisonMode
from lograder.pipeline.types.artifacts import CMakeArtifact, FileArtifact

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def echo_bin(tmp_path_factory):
    """Prints its args joined by spaces, then a newline."""
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


@pytest.fixture(scope="module")
def reverse_bin(tmp_path_factory):
    """Prints its first arg reversed, then a newline."""
    d = tmp_path_factory.mktemp("reverse_bin")
    src = d / "main.c"
    src.write_text(
        """
#include <stdio.h>
#include <string.h>
int main(int argc, char **argv) {
    if (argc < 2) { printf("\\n"); return 0; }
    int n = strlen(argv[1]);
    for (int i = n - 1; i >= 0; i--) printf("%c", argv[1][i]);
    printf("\\n");
    return 0;
}
""",
        encoding="utf-8",
    )
    binary = d / "reverse"
    subprocess.run(["gcc", "-o", str(binary), str(src)], check=True)
    return binary


def _run_step(step, artifacts):
    gen = step(artifacts)
    packets = []
    try:
        while True:
            packets.append(next(gen))
    except StopIteration as e:
        return packets, e.value


# ---------------------------------------------------------------------------
# cases_from_matrix
# ---------------------------------------------------------------------------


def test_cases_from_matrix_cartesian_product():
    cases = cases_from_matrix(["add", "sub"], ["1", "2", "3"])
    assert len(cases) == 6
    assert [c.args for c in cases] == [
        ["add", "1"],
        ["add", "2"],
        ["add", "3"],
        ["sub", "1"],
        ["sub", "2"],
        ["sub", "3"],
    ]


def test_cases_from_matrix_default_names():
    cases = cases_from_matrix(["x", "y"], ["a", "b"])
    assert [c.name for c in cases] == ["x_a", "x_b", "y_a", "y_b"]


def test_cases_from_matrix_custom_name_fn():
    cases = cases_from_matrix(
        ["x", "y"],
        ["1", "2"],
        name_fn=lambda a: f"test_{a[0]}_{a[1]}",
    )
    assert cases[0].name == "test_x_1"
    assert cases[3].name == "test_y_2"


def test_cases_from_matrix_single_pool():
    cases = cases_from_matrix(["a", "b", "c"])
    assert [c.args for c in cases] == [["a"], ["b"], ["c"]]


def test_cases_from_matrix_accepts_generators():
    cases = cases_from_matrix((str(i) for i in range(3)), ["x", "y"])
    assert len(cases) == 6


def test_cases_from_matrix_comparison_propagated():
    cases = cases_from_matrix(["a"], comparison=ComparisonMode.EXACT)
    assert cases[0].comparison == ComparisonMode.EXACT


def test_cases_from_matrix_stdin_propagated():
    cases = cases_from_matrix(["a"], stdin=b"hello")
    assert cases[0].stdin == b"hello"


def test_cases_from_matrix_empty_pools_returns_empty():
    assert cases_from_matrix() == []


def test_cases_from_matrix_exceeds_max_cases_raises():
    with pytest.raises(ValueError, match="max_cases"):
        cases_from_matrix(["a"] * 100, ["b"] * 100, max_cases=500)


def test_cases_from_matrix_error_message_includes_total():
    with pytest.raises(ValueError, match="10000"):
        cases_from_matrix(["a"] * 100, ["b"] * 100, max_cases=500)


def test_cases_from_matrix_exactly_at_limit_ok():
    cases = cases_from_matrix(["a"] * 10, ["b"] * 10, max_cases=100)
    assert len(cases) == 100


def test_cases_from_matrix_one_over_limit_raises():
    with pytest.raises(ValueError):
        cases_from_matrix(["a"] * 10, ["b"] * 11, max_cases=100)


# ---------------------------------------------------------------------------
# oracle_cases
# ---------------------------------------------------------------------------


def test_oracle_cases_captures_stdout(echo_bin):
    with config(root_directory=echo_bin.parent):
        inputs = [OracleInput(name="hello", args=["hello", "world"])]
        cases = oracle_cases(echo_bin, inputs)
    assert len(cases) == 1
    assert cases[0].expected_stdout.strip() == "hello world"
    assert cases[0].name == "hello"
    assert cases[0].args == ["hello", "world"]


def test_oracle_cases_captures_exit_code(echo_bin):
    with config(root_directory=echo_bin.parent):
        inputs = [OracleInput(name="run", args=["x"])]
        cases = oracle_cases(echo_bin, inputs)
    assert cases[0].expected_exit_code == 0


def test_oracle_cases_composes_with_cases_from_matrix(echo_bin):
    inputs = cases_from_matrix(["hello", "bye"], ["world", "there"])
    with config(root_directory=echo_bin.parent):
        cases = oracle_cases(echo_bin, inputs)
    assert len(cases) == 4
    names = {c.name for c in cases}
    assert names == {"hello_world", "hello_there", "bye_world", "bye_there"}


def test_oracle_cases_preserves_comparison_mode(echo_bin):
    with config(root_directory=echo_bin.parent):
        inputs = [OracleInput(name="x", args=["x"], comparison=ComparisonMode.EXACT)]
        cases = oracle_cases(echo_bin, inputs)
    assert cases[0].comparison == ComparisonMode.EXACT


# ---------------------------------------------------------------------------
# DifferentialTest
# ---------------------------------------------------------------------------


def test_differential_test_pass_same_binary(echo_bin):
    artifact = FileArtifact(path=echo_bin)
    test = DifferentialTest(
        "echo",
        echo_bin,
        cases_from_matrix(["hello", "world"], ["foo", "bar"]),
    )
    with config(root_directory=echo_bin.parent):
        packets, result = _run_step(test, {"echo": artifact})
    assert result.is_ok
    assert all(p.is_ok for p in packets)
    assert all(isinstance(p.danger_ok, DifferentialSuccess) for p in packets)


def test_differential_test_fail_different_binary(echo_bin, reverse_bin):
    artifact = FileArtifact(path=reverse_bin)
    test = DifferentialTest(
        "reverse",
        echo_bin,
        [OracleInput(name="abc", args=["abc"])],
    )
    with config(root_directory=echo_bin.parent):
        packets, result = _run_step(test, {"reverse": artifact})
    assert result.is_ok
    assert len(packets) == 1
    assert packets[0].is_err
    failure = packets[0].danger_err
    assert isinstance(failure, DifferentialFailure)
    assert failure.diff != ""
    assert "reference" in failure.diff
    assert "student" in failure.diff


def test_differential_test_missing_artifact():
    test = DifferentialTest("missing", Path("/bin/echo"), [])
    _, result = _run_step(test, {})
    assert result.is_err
    assert isinstance(result.danger_err, DifferentialError)


def test_differential_test_non_file_artifact(echo_bin):
    artifact = CMakeArtifact(
        name="echo", target_type="EXECUTABLE", build_dir=Path("/tmp")
    )
    test = DifferentialTest("echo", echo_bin, [])
    _, result = _run_step(test, {"echo": artifact})
    assert result.is_err
    assert isinstance(result.danger_err, DifferentialError)


def test_differential_test_check_exit_codes_pass(echo_bin):
    artifact = FileArtifact(path=echo_bin)
    test = DifferentialTest(
        "echo",
        echo_bin,
        [OracleInput(name="x", args=["x"])],
        check_exit_codes=True,
    )
    with config(root_directory=echo_bin.parent):
        packets, result = _run_step(test, {"echo": artifact})
    assert result.is_ok
    assert packets[0].is_ok


def test_differential_test_accepts_generator_cases(echo_bin):
    def gen():
        for word in ["hello", "world", "foo"]:
            yield OracleInput(name=word, args=[word])

    artifact = FileArtifact(path=echo_bin)
    test = DifferentialTest("echo", echo_bin, gen())
    with config(root_directory=echo_bin.parent):
        packets, result = _run_step(test, {"echo": artifact})
    assert result.is_ok
    assert len(packets) == 3


def test_differential_test_passthrough_artifacts(echo_bin):
    artifact = FileArtifact(path=echo_bin)
    artifacts = {"echo": artifact, "other": artifact}
    test = DifferentialTest("echo", echo_bin, [OracleInput(name="x", args=["x"])])
    with config(root_directory=echo_bin.parent):
        _, result = _run_step(test, artifacts)
    assert result.is_ok
    assert result.danger_ok is artifacts
