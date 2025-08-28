from typing import Protocol, TypedDict, Generator, NotRequired

class TestCaseProtocol(Protocol):
    def get_name(self): ...
    def get_input(self): ...
    def get_expected_output(self): ...

class WeightedTestCaseProtocol(TestCaseProtocol):
    def get_weight(self): ...

class TestCaseDict(TypedDict):
    name: str
    input: str
    expected_output: str
    weight: NotRequired[float]
