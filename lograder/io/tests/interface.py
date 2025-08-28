from __future__ import annotations

from abc import ABC, abstractmethod
import time

from contextlib import contextmanager
from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field, model_validator

TextFormat = Literal["text", "html", "simple_format", "md", "ansi"]
Visibility = Literal["visible", "after_due_date", "after_published", "hidden"]
Status = Literal["passed", "failed"]

class TestEntry(BaseModel):
    score: Optional[float]
    max_score: Optional[float]
    execution_time: Optional[float] = Field(default=None, exclude=True)
    status: Optional[Status] = None
    name: Optional[str]
    name_format: Optional[TextFormat] = "text"
    number: Optional[str] = None
    output: Optional[str]
    output_format: Optional[TextFormat] = "ansi"
    tags: List[str] = Field(default_factory=list)
    visibility: Optional[Visibility] = "hidden"
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @property
    def is_scored(self) -> bool:
        return self.score is not None

class TestInterface(ABC):
    def __init__(self):
        self.time_start: Optional[float] = None
        self.time_end: Optional[float] = None

    @contextmanager
    def evaluate_time(self):
        self.time_start = time.perf_counter()
        try:
            yield
        finally:
            self.time_end = time.perf_counter()

    # ========== SCORING METHODS ==========
    @abstractmethod
    def get_successful(self) -> bool:
        pass
    @abstractmethod
    def get_max_score(self) -> float:
        pass
    def get_score(self) -> float:
        return self.get_max_score() if self.get_successful() else 0.0
    def get_execution_time(self) -> Optional[float]:
        if self.time_start is not None and self.time_end is not None:
            return self.time_end - self.time_start
        return None

    # ========== METADATA METHODS ==========
    @abstractmethod
    def get_name(self) -> str:
        pass
    @abstractmethod
    def get_output(self) -> str:
        pass
    @abstractmethod
    def get_visibility(self) -> Visibility:
        pass

    # ========== OPTIONAL METHODS (DEFAULT BLANK) ==========
    def get_status(self) -> Status:
        return "passed" if self.get_successful() else "failed"
    @staticmethod
    def get_name_format() -> TextFormat:
        return "text"
    @staticmethod
    def get_number() -> Optional[str]:
        return None
    @staticmethod
    def get_output_format() -> TextFormat:
        return "ansi"
    @staticmethod
    def get_test_output_format() -> TextFormat:
        return "ansi"
    @staticmethod
    def get_tags() -> List[str]:
        return []
    @staticmethod
    def get_extra_data() -> Dict[str, Any]:
        return {}

    def serialize(self) -> TestEntry:
        return TestEntry(
            score = self.get_score(),
            max_score = self.get_max_score(),
            execution_time = self.get_execution_time(),
            status = self.get_status(),
            name = self.get_name(),
            name_format = self.get_name_format(),
            number = self.get_number(),
            output = self.get_output(),
            output_format = self.get_output_format(),
            tags = self.get_tags(),
            visibility = self.get_visibility(),
            extra_data = self.get_extra_data(),
        )
