from typing import Literal

from .block import Block
from .build import Build
from .check import Check
from .input import Input
from .step import Step
from .test import Test

# TODO: Implement pipeline verification

PSMState = Literal["input", "check", "build", "test"]


class _PSM:  # Internal Pipeline State Machine
    def __init__(self):
        self.state: PSMState = "input"


class Pipeline:
    def __init__(self, *steps: Step):
        pass
