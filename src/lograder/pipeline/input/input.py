from abc import ABC
from typing import TypeVar

from pydantic import BaseModel

from ..step import Step


class InputError(BaseModel):
    check_name: str


class InputData(BaseModel):
    check_name: str


InputT = TypeVar("InputT")
OkOutputT = TypeVar("OkOutputT")
ErrOutputT = TypeVar("ErrOutputT")
OkDisplayT = TypeVar("OkDisplayT")
ErrDisplayT = TypeVar("ErrDisplayT")


class Input(Step[InputT, OkOutputT, ErrOutputT, OkDisplayT, ErrDisplayT], ABC): ...
