# Example: Writing a custom step

This example shows how to write a step from scratch, wire it into a pipeline, and attach a scorer.

## The scenario

We want a step that checks whether the student's binary exits with code 0 on every test case and records each result. It goes between the build step and any existing test steps.

## Step 1 -- Define your data models

Steps yield and return `Result`-wrapped Pydantic models. Define one model for success and one for failure:

```python
from pydantic import BaseModel

class ExitCodeSuccess(BaseModel):
    case_name: str
    args: list[str]
    actual_exit_code: int

class ExitCodeFailure(BaseModel):
    case_name: str
    args: list[str]
    expected_exit_code: int
    actual_exit_code: int

class ExitCodeError(BaseModel):
    artifact_name: str
    message: str
```

## Step 2 -- Register a layout

Every model you log via `logger.packet()` needs a `Layout`. Register it in its own module so importing it registers the layout automatically:

```python
# mygrader/layouts/exit_code.py
from lograder.output.layout.layout import Layout, register_layout
from mygrader.steps.exit_code import ExitCodeSuccess, ExitCodeFailure, ExitCodeError


@register_layout("exit-code-success")
class ExitCodeSuccessLayout(Layout[ExitCodeSuccess]):
    @classmethod
    def to_ansi(cls, data: ExitCodeSuccess) -> str:
        from colorama import Fore as F, Style as S
        return (
            f"{S.BRIGHT}{F.GREEN}PASS{F.RESET}{S.RESET_ALL} "
            f"{data.case_name}: exit {data.actual_exit_code}"
        )

    @classmethod
    def to_simple(cls, data: ExitCodeSuccess) -> str:
        return f"PASS {data.case_name}: exit {data.actual_exit_code}"


@register_layout("exit-code-failure")
class ExitCodeFailureLayout(Layout[ExitCodeFailure]):
    @classmethod
    def to_ansi(cls, data: ExitCodeFailure) -> str:
        from colorama import Fore as F, Style as S
        return (
            f"{S.BRIGHT}{F.RED}FAIL{F.RESET}{S.RESET_ALL} "
            f"{data.case_name}: expected exit {data.expected_exit_code}, "
            f"got {data.actual_exit_code}"
        )

    @classmethod
    def to_simple(cls, data: ExitCodeFailure) -> str:
        return (
            f"FAIL {data.case_name}: expected exit {data.expected_exit_code}, "
            f"got {data.actual_exit_code}"
        )


@register_layout("exit-code-error")
class ExitCodeErrorLayout(Layout[ExitCodeError]):
    @classmethod
    def to_ansi(cls, data: ExitCodeError) -> str:
        from colorama import Fore as F, Style as S
        return f"{S.BRIGHT}{F.YELLOW}ERROR{F.RESET}{S.RESET_ALL} {data.message}"

    @classmethod
    def to_simple(cls, data: ExitCodeError) -> str:
        return f"ERROR {data.message}"
```

## Step 3 -- Write the step

```python
# mygrader/steps/exit_code.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generator

from lograder.common import Err, Ok, Result
from lograder.pipeline.test.test import Test, TestFailure, TestSuccess, TestError
from lograder.pipeline.types.artifacts import Artifact
from lograder.process.executable import ExecutableInput, ExecutableOptions


@dataclass
class ExitCodeCase:
    name: str
    args: list[str] = field(default_factory=list)
    expected_exit_code: int = 0


class ExitCodeSuccess(TestSuccess):
    args: list[str]
    actual_exit_code: int


class ExitCodeFailure(TestFailure):
    args: list[str]
    expected_exit_code: int
    actual_exit_code: int


class ExitCodeError(TestError):
    pass


class ExitCodeTest(
    Test[
        dict[str, Artifact],  # InputT
        dict[str, Artifact],  # OkOutputT  -- pass-through
        ExitCodeError,        # ErrOutputT -- fatal error
        ExitCodeSuccess,      # OkDisplayT -- yielded on pass
        ExitCodeFailure,      # ErrDisplayT -- yielded on fail
    ]
):
    def __init__(
        self,
        artifact_name: str,
        cases: list[ExitCodeCase],
        options: ExecutableOptions | None = None,
    ) -> None:
        self._artifact_name = artifact_name
        self._cases = cases
        self._options = options or ExecutableOptions()

    def __call__(
        self, artifacts: dict[str, Artifact]
    ) -> Generator[
        Result[ExitCodeSuccess, ExitCodeFailure],
        None,
        Result[dict[str, Artifact], ExitCodeError],
    ]:
        if self._artifact_name not in artifacts:
            return Err(ExitCodeError(
                artifact_name=self._artifact_name,
                message=f"Artifact '{self._artifact_name}' not found in build output.",
            ))

        artifact = artifacts[self._artifact_name]
        exe = artifact.executable

        for case in self._cases:
            output = exe(
                ExecutableInput(arguments=case.args),
                options=self._options,
            )

            if output.return_code == case.expected_exit_code:
                yield Ok(ExitCodeSuccess(
                    test_name=case.name,
                    artifact_name=self._artifact_name,
                    args=case.args,
                    actual_exit_code=output.return_code,
                ))
            else:
                yield Err(ExitCodeFailure(
                    test_name=case.name,
                    artifact_name=self._artifact_name,
                    args=case.args,
                    expected_exit_code=case.expected_exit_code,
                    actual_exit_code=output.return_code,
                ))

        return Ok(artifacts)
```

## Step 4 -- Use it in a pipeline

```python
# autograder.py
import mygrader.layouts.exit_code  # registers the layouts

from mygrader.steps.exit_code import ExitCodeTest, ExitCodeCase
from lograder.pipeline.score import TestCaseScorer

cases = [
    ExitCodeCase(name="success_case", args=["valid_input.txt"], expected_exit_code=0),
    ExitCodeCase(name="error_case",   args=["missing.txt"],     expected_exit_code=1),
]

pipeline.add(exit_check := ExitCodeTest("my_binary", cases))
exit_check.scorer = TestCaseScorer(
    {"success_case": 10.0, "error_case": 10.0},
    label="Exit codes",
)
```

## Key points

- **Extend `Test`**, not `Step` directly -- `Test` already wires in the 5 generic params correctly and handles the `dict[str, Artifact]` pass-through contract.
- **Yield non-fatal results**, return the final result. Yielded values are logged; the returned `Ok`/`Err` controls pipeline flow.
- **Register layouts** in a separate module. Import that module at the top of your autograder -- layout registration is an import-time side effect.
- **`TestSuccess` and `TestFailure`** provide `test_name` and `artifact_name` fields that `TestCaseScorer` hooks into via `isinstance`. Your success/failure models should extend them.
- **`TestError`** is for fatal errors (artifact missing, process crashed unexpectedly). Returning `Err(TestError(...))` stops the pipeline.

## Type checking

Add `# type: ignore` to the class definition or run mypy with the project's config -- the 5 generic parameter constraint is enforced at runtime by `Pipeline.validate_step_types()` and at static analysis time by mypy if you annotate correctly.

```bash
mypy mygrader/ src/
```
