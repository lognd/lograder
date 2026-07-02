import time
from collections.abc import Iterable
from typing import Generator, final

from pydantic import BaseModel, Field, field_validator

from lograder.common import Err, Ok, Result
from lograder.pipeline.test.test import Test, TestError, TestFailure, TestSuccess
from lograder.pipeline.types.artifacts import Artifact
from lograder.process.executable import ExecutableOptions

_SAFETY_MARGIN: float = 30.0


class PerformanceCase(BaseModel):
    name: str
    args: list[str] = Field(default_factory=list)
    stdin: bytes = b""
    time_limit: float

    @field_validator("time_limit")
    @classmethod
    def positive_limit(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"`time_limit` must be positive, got {v}.")
        return v


class PerformanceTestSuccess(TestSuccess):
    args: list[str]
    time_limit: float
    elapsed: float


class PerformanceTestFailure(TestFailure):
    args: list[str]
    time_limit: float
    elapsed: float


class PerformanceTestError(TestError):
    pass


@final
class PerformanceTest(
    Test[
        dict[str, Artifact],
        dict[str, Artifact],
        PerformanceTestError,
        PerformanceTestSuccess,
        PerformanceTestFailure,
    ]
):
    def __init__(
        self,
        artifact_name: str,
        test_cases: Iterable[PerformanceCase],
        base_options: ExecutableOptions | None = None,
    ) -> None:
        self._artifact_name = artifact_name
        self._test_cases = test_cases
        self._base_options = base_options

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[PerformanceTestSuccess, PerformanceTestFailure],
        None,
        Result[dict[str, Artifact], PerformanceTestError],
    ]:
        artifact_result = self._resolve_artifact(artifacts, self._artifact_name)
        if artifact_result.is_err:
            return Err(
                PerformanceTestError(
                    artifact_name=self._artifact_name,
                    message=artifact_result.danger_err,
                )
            )
        artifact = artifact_result.danger_ok

        base_options = self._base_options or ExecutableOptions()

        for case in self._test_cases:
            # Safety kill fires at time_limit + _SAFETY_MARGIN to prevent
            # indefinite hangs while still allowing the wall-clock measurement
            # to determine whether the limit was exceeded.
            options = base_options.model_copy(
                update={"timeout": case.time_limit + _SAFETY_MARGIN}
            )

            start = time.perf_counter()
            try:
                self._invoke(artifact, case.args, case.stdin, options)
            except Exception:
                pass
            elapsed = time.perf_counter() - start

            if elapsed < case.time_limit:
                yield Ok(
                    PerformanceTestSuccess(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        args=case.args,
                        time_limit=case.time_limit,
                        elapsed=elapsed,
                    )
                )
            else:
                yield Err(
                    PerformanceTestFailure(
                        test_name=case.name,
                        artifact_name=self._artifact_name,
                        args=case.args,
                        time_limit=case.time_limit,
                        elapsed=elapsed,
                    )
                )

        return Ok(artifacts)
