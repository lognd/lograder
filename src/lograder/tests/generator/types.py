from pathlib import Path
from typing import NotRequired, Protocol, TypedDict, Union, runtime_checkable, List


@runtime_checkable
class TestCaseProtocol(Protocol):
    def get_name(self) -> str: ...
    def get_input(self) -> str: ...
    def get_expected_output(self) -> str: ...

@runtime_checkable
class FlaggedTestCaseProtocol(TestCaseProtocol, Protocol):
    def get_flags(self) -> List[str | Path]: ...

@runtime_checkable
class WeightedTestCaseProtocol(TestCaseProtocol, Protocol):
    def get_weight(self) -> float: ...

@runtime_checkable
class FlaggedWeightedTestCaseProtocol(FlaggedTestCaseProtocol, WeightedTestCaseProtocol, Protocol):
    pass

class TestCaseDict(TypedDict):
    name: str
    input: str
    expected_output: str
    flags: NotRequired[List[str | Path]]
    weight: NotRequired[float]


TestCase = Union[TestCaseProtocol, FlaggedTestCaseProtocol, WeightedTestCaseProtocol, FlaggedWeightedTestCaseProtocol, TestCaseDict]
