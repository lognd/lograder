from __future__ import annotations

import logging
import traceback
from contextlib import contextmanager
from typing import Any, Generic, Iterable, Iterator, Optional, Type, TypeVar, cast

from pydantic import BaseModel

from ..common import Empty, Result
from ..exception import DeveloperException, StaffException
from ..output.logger import get_logger
from .block import Block
from .build import Build
from .check import Check, CheckData
from .conversion import convert
from .input import Input
from .step import Step
from .test import Test, TestData

_LOGGER = get_logger("lograder.graph.graph")


# Dummy class serving as a smarter sentinel for graph misconfigurations.
class PreinitializedGraphData(Empty): ...


class GraphError(BaseModel):
    error: Exception
    error_type: str
    error_msg: str
    error_traceback: str


@contextmanager
def graceful_graph_context() -> Iterator[None]:
    try:
        yield
    except Exception as e:
        _LOGGER.packet(
            GraphError(
                error=e,
                error_type=e.__class__.__name__,
                error_msg=str(e),
                error_traceback=traceback.format_exc(),
            ),
            level=logging.ERROR,
        )
    finally:
        return


class Graph:
    def __init__(self, *flat_seq: Step) -> None:
        self._roots: set[Step] = set()
        self._f_adj_list: dict[Step, set[Step]] = {}
        self._r_adj_list: dict[Step, set[Step]] = {}

        self.unflatten_and_connect(flat_seq)

        for next_step, prev_steps in self._r_adj_list.items():
            for prev_step in prev_steps:
                next_step.assert_follow(prev_step.__class__)

    def unflatten_and_connect(self, flat_seq: Iterable[Step]) -> None:
        previous_mutating: Step
        for step_idx, step in enumerate(flat_seq):
            if step_idx == 0:
                self.add_root(step)
                previous_mutating = step
                continue
            # I check above and assign it; I can't do a [0] access because it's iterable.
            # noinspection PyUnboundLocalVariable
            self.connect(previous_mutating, step)
            if step.is_mutating():
                previous_mutating = step

    def add_root(self, root: Step) -> None:
        root.assert_mutating(origin="Graph.add_root")
        self._roots.add(root)

    def connect(self, step_from: Step, step_to: Step) -> None:
        self._f_adj_list.setdefault(step_from, set()).add(step_to)
        self._r_adj_list.setdefault(step_to, set()).add(step_from)

    def _handle_step(self, step: Step) -> None:
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

    def __call__(self) -> None:
        pass
