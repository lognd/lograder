from abc import ABC
from typing import TypeVar
from pydantic import BaseModel

from lograder.pipeline.step import Step


InputT = TypeVar("InputT")
OkOutputT = TypeVar("OkOutputT")
ErrOutputT = TypeVar("ErrOutputT")
OkDisplayT = TypeVar("OkDisplayT")
ErrDisplayT = TypeVar("ErrDisplayT")


class BuildError(BaseModel): ...


class BuildData(BaseModel): ...


class Build(Step[InputT, OkOutputT, ErrOutputT, OkDisplayT, ErrDisplayT], ABC): ...
