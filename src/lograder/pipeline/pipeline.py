from __future__ import annotations

from typing import Any, Generic

from typing_extensions import TypeVar

from ..common import Empty, Result
from ..exception import StaffException
from .block import Block
from .build import Build
from .check import Check, CheckData
from .conversion import Conversion
from .input import Input
from .output import Output
from .step import Step
from .test import Test, TestData


class Pipeline:
    def __init__(self, *steps: Step) -> None:
        if len(steps) < 2:
            raise StaffException(
                f'`Pipeline` requires at least two steps (a "beginning step" defining the inputs and an "ending step" defining the outputs). Received only {len(steps)} `Steps` (`{"`, `".join(step.__class__.__name__ if step.__class__.__repr__ is object.__repr__ else repr(step) for step in steps)}`).'
            )
        steps[0].assert_begin()
        for step_prev, step_next in zip(steps[:-1], steps[1:]):
            step_next.assert_follow(step_prev.__class__)
        steps[-1].assert_end()
        self._steps = steps

    def __call__(self) -> None:
        intermediate: Any = None
        intermediate_result: Result[Any, Any]
        check_data: list[CheckData] = []
        test_data: list[TestData] = []
        for step in self._steps:
            # There seems to be a lot of "type-unsafety" in the following section,
            # but remember that as long as every object actually follows its type
            # contract, the beginning step should have alerted us to any mismatch,
            # thus ignoring and `Any`-ing below should be safe-ish.
            if isinstance(step, Input):
                intermediate_result = step()
                if intermediate_result.is_ok:
                    intermediate = intermediate_result.danger_ok
                else:
                    # TODO: Fix handling!
                    raise NotImplementedError
            elif isinstance(step, Check):
                check_result = step(intermediate)
                check = check_result.ok
                if check is not None:
                    check_data.extend(check)
            elif isinstance(step, Build):
                intermediate_result = step(intermediate)
                if intermediate_result.is_ok:
                    intermediate = intermediate_result.danger_ok
                else:
                    # TODO: Fix handling!
                    raise NotImplementedError
            elif isinstance(step, Conversion):
                intermediate_result = step(intermediate)
                if intermediate_result.is_ok:
                    intermediate = intermediate_result.danger_ok
                else:
                    # TODO: Fix handling!
                    raise NotImplementedError
            elif isinstance(step, Test):
                test_result = step(intermediate)
                test = test_result.ok
                if test is not None:
                    test_data.extend(test)
            elif isinstance(step, (Block, Output)):
                step()
