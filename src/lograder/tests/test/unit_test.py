from pathlib import Path
from typing import Optional, List

from .interface import UnitTestWrapperInterface

class Catch2Test(UnitTestWrapperInterface):
    def __init__(self):
        super().__init__()
        self._executable: Optional[List[str | Path]] = None
        self._catch2_output: Optional[str] = None

    def get_success(self) -> bool:
        pass

    def set_target(self, target: List[str | Path]):
        self._executable = target

    def is_executed(self) -> bool:
        return self._catch2_output is not None

    def get_error(self) -> str:
        pass

    def get_input(self) -> str:
        pass

    def get_actual_output(self) -> Optional[str]:
        pass

    def override_output(self, stdout: str, stderr: str):
        pass

    def run(self, wrap_args: bool = False, working_directory: Optional[Path] = None) -> None:
        pass

    def get_name(self) -> str:
        pass

    def get_successful(self) -> bool:
        pass

    def get_weight(self) -> float:
        pass

    def force_successful(self) -> None:
        pass

    def force_unsuccessful(self) -> None:
        pass