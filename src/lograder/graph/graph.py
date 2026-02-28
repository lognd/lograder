from __future__ import annotations

import logging
import traceback
from contextlib import contextmanager
from typing import Any, Iterable, Iterator, Optional, cast

from pydantic import BaseModel

from ..common import Empty, Err, Ok, Result
from ..exception import DeveloperException, StaffException
from ..output.logger import get_logger
from .artifact import Artifact
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


class GraphStateError(BaseModel):
    error_type: str


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
        self._states: dict[Step, Any] = {}
        self._f_adj_list: dict[Step, set[Step]] = {}
        self._r_adj_list: dict[Step, Step] = {}  # every in-degree must be 1.

        self.unflatten_and_connect(flat_seq)

        for prev_step, next_steps in self._f_adj_list.items():
            for next_step in next_steps:
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
        if step_to in self._r_adj_list:
            raise DeveloperException(
                f"Tried to add a connect a second predecessor (`{step_from.__class__.__name__}`: <{repr(step_from)}>) to "
                f"`Step`, `{step_to.__class__.__name__}`: <{repr(step_to)}>, when predecessor is already assigned "
                f"(`{self._r_adj_list[step_to].__class__.__name__}`: <{repr(self._r_adj_list[step_to])}>)."
            )
        self._f_adj_list.setdefault(step_from, set()).add(step_to)
        self._r_adj_list[step_to] = step_from

    def get_next_steps(self, step: Step) -> frozenset[Step]:
        return frozenset(self._f_adj_list.get(step, frozenset()))

    def get_previous_step(self, step: Step) -> Optional[Step]:
        if step in self._r_adj_list:
            return self._r_adj_list[step]
        return None

    def get_previous_state(self, step: Step) -> Result[Any, GraphStateError]:
        prev_step = self.get_previous_step(step)
        if prev_step is None:
            if step in self._roots:
                return Err(GraphStateError(error_type="is-root"))
            return Err(GraphStateError(error_type="not-in-graph"))
        if prev_step not in self._states:
            return Err(GraphStateError(error_type="step-was-const"))
        return Ok(self._states[prev_step])

    def _handle_step(self, step: Step) -> None:
        match step:
            case Block():  # const
                # Not sure if PyCharm is bugged, but `step` must be a `Block`
                # to be in this section, and thus is callable.
                # noinspection PyCallingNonCallable
                step()

            case Build():  # mut
                # Because `Build` is not a root step, we can safely cast it from None.

                prev_state = self.get_previous_state(step)
                if prev_state.is_err:
                    match prev_state.danger_err:
                        case "is-root":
                            # TODO: WRITE HELPFUL, DATA-FILLED ERROR MSG.
                            raise DeveloperException()
                        case "not-in-graph":
                            # TODO: WRITE HELPFUL, DATA-FILLED ERROR MSG.
                            raise DeveloperException()
                        case "step-was-const":
                            # TODO: WRITE HELPFUL, DATA-FILLED ERROR MSG.
                            raise DeveloperException()
                # This cast is okay because if it was `None`, it would have been caught by the above match.
                # noinspection PyUnnecessaryCast
                prev_step = cast(Step, self.get_previous_step(step))
                conversions = step.get_conversions_from(prev_step.__class__)
                if len(conversions) > 1:
                    # TODO: WRITE HELPFUL, DATA-FILLED ERROR MSG: "Conversion is ambiguous..."
                    raise StaffException()

                conv = conversions.pop()
                # This cast is okay because of this graph's invariance.
                # We checked that the previous step's output is a valid input,
                # meaning there exists a conversion from the previous type to
                # the current type.

                input_state = conv(prev_state)
                if input_state.is_err:
                    # TODO: Handle error case.
                    return

                # noinspection PyCallingNonCallable,PyUnnecessaryCast
                self._states[step] = step(
                    cast(dict[str, Artifact], input_state.danger_ok)
                )

            case Check():  # const
                pass

            case Input():  # mut
                pass

            case Test():  # const
                pass

    def __call__(self) -> None:
        pass
