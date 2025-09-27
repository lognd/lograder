from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from ...types import AscendingOrder, Status, TextFormat, Visibility


# -----------------------------
# JSON schema for a single test case
# -----------------------------
class TestCaseJSON(BaseModel):
    __test__: bool = False  # Prevent pytest from treating this class as a test

    # Core test result data
    score: Optional[float]  # Score for this test
    max_score: Optional[float]  # Maximum possible score
    status: Optional[Status] = None  # Pass/Fail/Other status
    name: Optional[str]  # Name of the test
    name_format: Optional[TextFormat] = "text"  # Format for the test name
    number: Optional[str] = None  # Optional test number/index

    # Output-related fields
    output: Optional[str]  # Output of the test (raw text or ANSI)
    output_format: Optional[TextFormat] = (
        "ansi"  # Format of output (ansi, markdown, etc.)
    )

    # Metadata
    tags: List[str] = Field(default_factory=list)  # Custom tags for filtering
    visibility: Optional[Visibility] = "visible"  # Visibility on Gradescope
    extra_data: Optional[Dict[str, Any]] = Field(  # Arbitrary extra data
        default_factory=dict
    )

    @property
    def is_scored(self) -> bool:
        """Whether this test has been assigned a score."""
        return self.score is not None


# -----------------------------
# JSON schema for leaderboard entries
# -----------------------------
class LeaderboardJSON(BaseModel):
    name: str  # Display name on the leaderboard
    value: float | str  # Numeric score or placeholder string ("***")
    order: Optional[AscendingOrder] = None  # Optional ordering preference

    @field_validator("value")
    def validate_value(cls, v):
        """
        If value is a string, it must only contain '*'.
        Example valid string: "***"
        """
        if isinstance(v, str) and any(char != "*" for char in v):
            raise ValueError(
                "If passing a string for value, it must be made entirely of the character, '*'."
            )
        return v


# -----------------------------
# JSON schema for entire assignment grading dump
# -----------------------------
class AssignmentJSON(BaseModel):
    # Top-level submission information
    score: Optional[float] = None  # Overall assignment score
    output: Optional[str] = None  # Text relevant to the whole submission
    output_format: Optional[TextFormat] = "ansi"  # Format for global output
    test_output_format: Optional[TextFormat] = (
        "ansi"  # Format for individual test outputs
    )
    visibility: Optional[Visibility] = "visible"  # Overall visibility setting
    extra_data: Optional[Dict[str, Any]] = Field(  # Arbitrary metadata
        default_factory=dict
    )

    # Per-test and leaderboard data
    tests: Optional[List[TestCaseJSON]]  # List of test case results
    leaderboard: Optional[List[LeaderboardJSON]] = None  # Leaderboard entries

    @model_validator(mode="after")
    def check_score_existence(self):
        """
        Validation logic:
        - If there are no tests, `score` must be provided.
        - If all tests are scored, `score` must NOT be overwritten.
        """
        if not self.tests:
            if self.score is None:
                raise ValueError(
                    "If there are no tests specified, please pass `score` to Grade object."
                )
        elif all(test.is_scored for test in self.tests):
            if self.score is not None:
                # Overwriting allowed by schema, but discouraged
                raise ValueError(
                    "You have specified tests with `tests`, but you are overwriting "
                    "the score of the Grade object."
                )
        return self
