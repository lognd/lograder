import itertools
import math
from collections.abc import Callable, Iterable
from pathlib import Path

from pydantic import BaseModel, Field

from lograder.pipeline.test.output_compare import ComparisonMode, OutputCompareCase
from lograder.process.executable import (
    ExecutableInput,
    ExecutableOptions,
    StaticExecutable,
)


class OracleInput(BaseModel):
    """Partial test case spec — expected output is derived by running the oracle binary."""

    name: str
    args: list[str] = Field(default_factory=list)
    stdin: bytes = b""
    comparison: ComparisonMode = ComparisonMode.STRIP


def oracle_cases(
    binary: Path | str,
    inputs: Iterable[OracleInput],
    options: ExecutableOptions | None = None,
) -> list[OutputCompareCase]:
    """Run a reference binary on each input and capture its stdout as expected output.

    Useful when you have a staff solution and want to generate test cases without
    hard-coding expected outputs. The oracle's exit code is captured and used as
    ``expected_exit_code`` for each case.

    Example::

        cases = oracle_cases(
            Path("staff_solution/bin/myprogram"),
            [
                OracleInput(name="empty", args=[]),
                OracleInput(name="small", args=["5"]),
                *(OracleInput(name=f"rand_{i}", args=[str(random.randint(1, 1000))]) for i in range(50)),
            ],
        )
        test = OutputCompareTest("myprogram", cases)
    """
    exe = StaticExecutable([str(binary)])
    opts = options or ExecutableOptions()
    result: list[OutputCompareCase] = []
    for inp_spec in inputs:
        inp = ExecutableInput(stdin_bytes=inp_spec.stdin, arguments=inp_spec.args)
        output = exe(inp, options=opts)
        result.append(
            OutputCompareCase(
                name=inp_spec.name,
                args=inp_spec.args,
                stdin=inp_spec.stdin,
                expected_stdout=output.stdout_text,
                comparison=inp_spec.comparison,
                expected_exit_code=output.return_code,
            )
        )
    return result


def cases_from_matrix(
    *arg_pools: Iterable[str],
    name_fn: Callable[[list[str]], str] | None = None,
    stdin: bytes = b"",
    comparison: ComparisonMode = ComparisonMode.STRIP,
    max_cases: int = 500,
) -> list[OracleInput]:
    """Generate test cases from the cartesian product of argument pools.

    Each pool represents one argument position. All combinations are produced.
    Raises ``ValueError`` if the total would exceed ``max_cases`` to prevent
    accidental combinatorial explosions.

    Composes directly with ``oracle_cases`` and ``DifferentialTest``::

        # 3 × 4 = 12 cases, expected outputs filled in by oracle
        cases = oracle_cases(
            reference_binary,
            cases_from_matrix(["add", "sub", "mul"], ["1", "2", "10", "100"]),
        )

        # or run both binaries at grading time
        test = DifferentialTest("prog", reference_binary,
                                cases_from_matrix(["add", "sub"], ["1", "2"]))
    """
    pools = [list(p) for p in arg_pools]
    if not pools:
        return []
    total = math.prod(len(p) for p in pools)
    if total > max_cases:
        sizes = " × ".join(str(len(p)) for p in pools)
        raise ValueError(
            f"cases_from_matrix would generate {total} cases ({sizes}) but "
            f"max_cases={max_cases}. Pass max_cases=N to allow it if intentional."
        )
    _name_fn = name_fn or (lambda args: "_".join(args))
    return [
        OracleInput(
            name=_name_fn(list(combo)),
            args=list(combo),
            stdin=stdin,
            comparison=comparison,
        )
        for combo in itertools.product(*pools)
    ]
