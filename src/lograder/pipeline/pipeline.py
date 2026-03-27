from __future__ import annotations

from typing import Any

from .step import Step
from .types.sentinel import PIPELINE_START
from ..common import Result
from ..exception import DeveloperException, StaffException
from ..output import get_logger

_LOGGER = get_logger(__name__)


class Pipeline:
    def __init__(self) -> None:
        self.steps: list[Step] = []
        self.datum: Any = PIPELINE_START()
        # TODO: implement validation for pipeline.

    def validate_step_types(self) -> None:
        if len(self.steps) == 0:
            raise DeveloperException(
                "Called `validate_step_types()` on a `Pipeline` with no steps."
            )
        for prev_step, next_step in zip(self.steps[:-1], self.steps[1:]):
            next_step.assert_follow(
                prev_step.__class__, origin_exception_type=StaffException
            )

    def __call__(self) -> None:
        for step in self.steps:
            gen = step(self.datum)
            while True:
                try:
                    display: Result = next(gen)
                    if display.ok:
                        # TODO: I know the duplicate branches look real stupid, but I'm likely going to add more logic in here.
                        _LOGGER.packet(display.danger_ok)
                    else:
                        _LOGGER.packet(display.danger_err)
                except StopIteration as exc:
                    output: Result = exc.value
                    break
            if output.ok:
                self.datum = output.danger_ok
            else:
                # TODO: Same here.
                _LOGGER.packet(output.danger_err)
                break
