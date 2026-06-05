from abc import ABC
from typing import TypeVar

from pydantic import BaseModel

from lograder.pipeline.step import Step

__test__: bool = False


InputT = TypeVar("InputT")
OkOutputT = TypeVar("OkOutputT")
ErrOutputT = TypeVar("ErrOutputT")
OkDisplayT = TypeVar("OkDisplayT")
ErrDisplayT = TypeVar("ErrDisplayT")


class TestSuccess(BaseModel):
    __test__: bool = False
    test_name: str
    artifact_name: str


class TestFailure(BaseModel):
    __test__: bool = False
    test_name: str
    artifact_name: str


class TestError(BaseModel):
    __test__: bool = False
    artifact_name: str
    message: str


class Test(Step[InputT, OkOutputT, ErrOutputT, OkDisplayT, ErrDisplayT], ABC): ...
