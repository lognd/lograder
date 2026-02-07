from __future__ import annotations

from typing import Generic, Literal, NewType, cast

from typing_extensions import TypeVar

from ..common import Empty
from ..exception import StaffException
from .block import Block
from .build import Build
from .check import Check
from .input import Input
from .step import Step
from .test import Test


class PipelineState(Empty): ...


class _Init(PipelineState): ...


T = TypeVar("T", bound=PipelineState, default=_Init)


class Pipeline(Generic[T]):
    def __init__(self, *steps: Step) -> None:
        if len(steps) < 2:
            raise StaffException(
                f'`Pipeline` requires at least two steps (a "beginning step" defining the inputs and an "ending step" defining the outputs). Received only {len(steps)} `Steps` (`{"`, `".join(step.__class__.__name__ if step.__class__.__repr__ is object.__repr__ else repr(step) for step in steps)}`).'
            )
        steps[0].assert_begin()
        for step_prev, step_next in zip(steps[:-1], steps[1:]):
            step_next.assert_follow(step_prev.__class__)
        steps[-1].assert_end()
