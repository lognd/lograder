from abc import ABC, abstractmethod
from typing import Optional


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

    def get_execution_time(self) -> Optional[float]:
        return None
