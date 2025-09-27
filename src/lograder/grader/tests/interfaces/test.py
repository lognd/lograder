from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING, Any, Optional, Mapping

from ...json.raw_gradescope import TestCaseJSON

if TYPE_CHECKING:
    from ...penalties.interfaces.penalty import PenaltyInterface
    from ...addons.addon import AddonInterface
    from ...formatters.dispatcher import FormatPackage, FormatDispatcher
    from ....types import FormatLabel

class TestInterface(ABC):

    __test__: bool = False
    _created_tests: List[TestInterface] = []

    def __init__(self):
        super().__init__()
        self._penalties: List[PenaltyInterface] = []
        self._addons: List[AddonInterface] = []
        self._outputs: List[FormatPackage] = []

        self._visible: bool = True
        self._weight: float = 1.0
        self._override: Optional[bool] = None

        self._created_tests.append(self)

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_score(self) -> float:
        pass

    def get_weight(self) -> float:
        return self._weight

    @classmethod
    def get_max_score(cls) -> float:
        return 100.0 / sum([test.get_weight() for test in cls._created_tests])

    def set_weight(self, weight: float):
        self._weight = weight

    def set_visibility(self, visibility: bool):
        self._visible = visibility

    def set_penalties(self, penalties: List[PenaltyInterface]):
        self._penalties = penalties

    def set_addons(self, addons: List[AddonInterface]):
        self._addons = addons

    def add_to_output(self, label: FormatLabel, data: Mapping[str, Any]):
        self._add_to_output_raw(FormatPackage(label=label, data=data))

    def get_visibility(self):
        return self._visible

    def run(self) -> TestCaseJSON:
        if self._override is not None:
            score: float = self._override * self.get_weight() * self.get_max_score()
        else:
            score: float = self.get_score()

            for addon in self._addons:
                score *= addon.get_penalty()
                self._add_to_output_raw(addon.get_output())

            for penalty in self._penalties:
                score *= penalty.get_penalty()
                self._add_to_output_raw(penalty.get_output())

        test_output: list[str] = []
        for output in self._outputs:
            test_output.append(FormatDispatcher.format(output))

        pyd_output: TestCaseJSON = TestCaseJSON(
            score = score,
            max_score = self.get_max_score(),
            name = self.get_name(),
            output = '\n'.join(test_output),
            visibility = "visible" if self.get_visibility() else "hidden",
        )

        return pyd_output

    def force_pass(self) -> None:
        self._override = True

    def force_fail(self) -> None:
        self._override = False

    def _add_to_output_raw(self, package: FormatPackage):
        self._outputs.append(package)

