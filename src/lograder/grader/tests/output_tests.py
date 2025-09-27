from typing import TYPE_CHECKING, Optional

from .interfaces.output_test import OutputTestInterface

if TYPE_CHECKING:
    from ..builders.interfaces.builder import BuilderInterface


class CLIOutputTest(OutputTestInterface):
    def __init__(self):
        super().__init__()
        self._name: Optional[str] = None
        self._builder: Optional[BuilderInterface] = None

    def set_builder(self, builder: BuilderInterface):
        self._builder = builder

    def get_builder(self) -> BuilderInterface:
        assert self._builder is not None
        return self._builder

    def set_name(self, name: str):
        self._name = name

    def get_expected_output(self) -> str:
        pass

    def get_actual_output(self) -> str:
        pass

    def get_error(self) -> str:
        pass

    def get_name(self) -> str:
        assert self._name is not None
        return self._name
