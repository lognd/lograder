from abc import ABC, abstractmethod
from typing import List, Optional

from .analytics import CallSummary, MemoryLossSummary, TimeSummary, WarningSummary


class TestInterface(ABC):
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
    def get_weight(self) -> float:
        pass

    def get_warnings(self) -> Optional[WarningSummary]:
        return None

    def get_execution_time(self) -> Optional[TimeSummary]:
        return None

    def get_calls(self) -> Optional[List[CallSummary]]:
        return None

    def get_leaks(self) -> Optional[MemoryLossSummary]:
        return None
