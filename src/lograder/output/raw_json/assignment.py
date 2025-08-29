from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, computed_field, model_validator

from ..common import TextFormat, Visibility
from .leaderboard import LeaderboardJSON
from .test_case import TestCaseJSON


class AssignmentJSON(BaseModel):
    score: Optional[float] = None
    output: Optional[str] = None  # Text relevant to the entire submission
    output_format: Optional[TextFormat] = "ansi"
    test_output_format: Optional[TextFormat] = "ansi"
    visibility: Optional[Visibility] = "visible"
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tests: Optional[List[TestCaseJSON]]
    leaderboard: Optional[List[LeaderboardJSON]] = None

    @model_validator(mode="after")
    def check_score_existence(self):
        if not self.tests:
            if self.score is None:
                raise ValueError(
                    "If there are no tests specified, please pass `score` to Grade object."
                )
        elif all([test.is_scored for test in self.tests]):
            if (
                self.score is not None
            ):  # Technically, you are allowed to overwrite, but that's stupid.
                raise ValueError(
                    "You have specified tests with `tests`, but you are overwriting the score of the Grade object."
                )
        return self

    @property
    @computed_field
    def execution_time(self) -> float:
        total = 0.0
        if self.tests is not None:
            for test in self.tests:
                if test.execution_time is not None:
                    total += test.execution_time
        return total
