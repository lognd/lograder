from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from .analytics import (
    CallgrindSummary,
    ExecutionTimeSummary,
    ValgrindLeakSummary,
    ValgrindWarningSummary,
)


class TestInterface(ABC):
    __test__: bool = False

    @abstractmethod
    def set_target(self, target: List[str | Path]):
        pass

    @abstractmethod
    def run(
        self, wrap_args: bool = False, working_directory: Optional[Path] = None
    ) -> None:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_input(self) -> str:
        pass

    @abstractmethod
    def get_actual_output(self) -> str:
        pass

    @abstractmethod
    def get_successful(self) -> bool:
        pass

    @abstractmethod
    def get_expected_output(self) -> str:
        pass

    @abstractmethod
    def get_error(self) -> str:
        pass

    @abstractmethod
    def get_weight(self) -> float:
        pass

    def get_penalty(self) -> float:
        return 1.0

    def get_warnings(self) -> Optional[ValgrindWarningSummary]:
        return None

    def get_execution_time(self) -> Optional[ExecutionTimeSummary]:
        return None

    def get_calls(self) -> Optional[List[CallgrindSummary]]:
        return None

    def get_leaks(self) -> Optional[ValgrindLeakSummary]:
        return None
