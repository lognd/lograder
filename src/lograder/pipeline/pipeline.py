from __future__ import annotations

from typing import Any

from lograder.common import Result
from lograder.exception import DeveloperException, StaffException
from lograder.output import get_logger
from lograder.pipeline.metadata import GraderMetadata
from lograder.pipeline.score import PipelineScore
from lograder.pipeline.step import Step
from lograder.pipeline.types.sentinel import PIPELINE_START

_LOGGER = get_logger(__name__)


class Pipeline:
    """Executes a sequence of Steps, threading each step's Ok output into the next step's input."""

    def __init__(self, steps: list[Step] | None = None) -> None:
        self.steps: list[Step] = list(steps) if steps else []
        self.datum: Any = PIPELINE_START()
        # TODO: implement validation for pipeline.

    def add(self, step: Step) -> None:
        self.steps.append(step)

    def validate_step_types(self) -> None:
        if len(self.steps) == 0:
            raise DeveloperException(
                "Called `validate_step_types()` on a `Pipeline` with no steps."
            )
        for prev_step, next_step in zip(self.steps[:-1], self.steps[1:]):
            next_step.assert_follow(
                prev_step.__class__, origin_exception_type=StaffException
            )

    def __call__(self, metadata: GraderMetadata | None = None) -> PipelineScore:
        # Auto-stamp submission_time if not already set
        if metadata is not None and metadata.submission_time is None:
            metadata = metadata.with_submission_time_now()

        score = PipelineScore(metadata=metadata)
        stop_index = len(self.steps)
        for i, step in enumerate(self.steps):
            gen = step(self.datum)
            while True:
                try:
                    display: Result = next(gen)
                    if display.is_ok:
                        # TODO: I know the duplicate branches look real stupid, but I'm likely going to add more logic in here.
                        _LOGGER.packet(display.danger_ok)
                    else:
                        _LOGGER.packet(display.danger_err)
                    if step.scorer is not None:
                        step.scorer.on_packet(display)
                except StopIteration as exc:
                    output: Result = exc.value
                    break
            if step.scorer is not None:
                step.scorer.on_complete(output)
                score.add(step, step.scorer.contribution())
            if output.is_ok:
                self.datum = output.danger_ok
            else:
                # TODO: Same here.
                _LOGGER.packet(output.danger_err)
                stop_index = i + 1
                break
        # Steps skipped by early exit contribute 0/possible so total.possible stays accurate.
        for skipped in self.steps[stop_index:]:
            if skipped.scorer is not None:
                score.add(skipped, skipped.scorer.contribution())
        return score
