from __future__ import annotations

import logging
import traceback
from contextlib import contextmanager
from typing import Any, Iterable, Iterator, Optional, Type, cast

from pydantic import BaseModel

from ..common import Empty, Result
from ..exception import DeveloperException, StaffException
from ..output.logger import get_logger
from .block import Block
from .build import Build
from .check import Check, CheckData
from .conversion import convert
from .input import Input
from .output import Output
from .step import Step
from .test import Test, TestData

_LOGGER = get_logger("lograder.pipeline.pipeline")


class PreinitializedPipelineData(
    Empty
):  # Dummy class serving as a smarter sentinel for pipeline misconfigurations.
    ...


class PipelineError(BaseModel):
    error: Exception
    error_type: str
    error_msg: str
    error_traceback: str


@contextmanager
def graceful_pipeline_context() -> Iterator[None]:
    try:
        yield
    except Exception as e:
        _LOGGER.packet(
            PipelineError(
                error=e,
                error_type=e.__class__.__name__,
                error_msg=str(e),
                error_traceback=traceback.format_exc(),
            ),
            level=logging.ERROR,
        )
    finally:
        return


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
        self._previous_step: Optional[Type[Step]] = None
        self._data: Any = PreinitializedPipelineData()

    def _handle_step(self, step: Step) -> None:
        if self._previous_step is None:
            step.assert_begin()
        else:
            step.assert_follow(self._previous_step)
            if isinstance(self._data, PreinitializedPipelineData):
                # If the invariants for this class are correct, this
                # section of code should be unreachable; however, this
                # is to serve as a canary for some future bugs.
                raise DeveloperException(
                    f"Beginning step failed to transform the data from its `PreinitializedPipelineData` state. The "
                    f"current step is `{step.__class__.__name__}`, the previous was `{self._previous_step.__name__}`. "
                    f"The whole pipeline is `{'`, `'.join(stp.__class__.__name__ for stp in self._steps)}`."
                )

        match step:
            case Block():
                # noinspection PyUnnecessaryCast
                cast(Block, step)()  # type: ignore[redundant-cast]
                # This cast is called "useless" by both mypy and resharper, but
                # I'm still getting complaints by PyCharm, so I'm just doing this
                # to shut it up.
            case Build():
                # noinspection PyUnnecessaryCast
                build_step: Build = cast(Build, step)  # type: ignore[redundant-cast]
                # Same here.

        self._previous_step = step.__class__

    def __call__(self) -> None:
        with graceful_pipeline_context():
            for step in self._steps:
                pass
