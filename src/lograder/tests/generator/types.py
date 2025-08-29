from typing import NotRequired, Protocol, TypedDict, Union, runtime_checkable


@runtime_checkable
class TestCaseProtocol(Protocol):
    def get_name(self): ...
    def get_input(self): ...
    def get_expected_output(self): ...


@runtime_checkable
class WeightedTestCaseProtocol(TestCaseProtocol, Protocol):
    def get_weight(self): ...


class TestCaseDict(TypedDict):
    name: str
    input: str
    expected_output: str
    weight: NotRequired[float]


TestCase = Union[TestCaseProtocol, WeightedTestCaseProtocol, TestCaseDict]
