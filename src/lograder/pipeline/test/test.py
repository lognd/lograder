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


class TestFailure(BaseModel):
    __test__: bool = False


class TestSuccess(BaseModel):
    __test__: bool = False


class Build(Step[InputT, OkOutputT, ErrOutputT, OkDisplayT, ErrDisplayT], ABC): ...
