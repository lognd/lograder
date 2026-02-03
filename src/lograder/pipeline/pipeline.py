from typing import Literal
from .check import Check
from .build import Build
from .test import Test
from .block import Block
from .input import Input
from .step import Step

# TODO: Implement pipeline verification

PSMState = Literal["input", "check", "build", "test"]
class _PSM:  # Internal Pipeline State Machine
    def __init__(self):
        self.state: PSMState = "input"



class Pipeline:
    def __init__(self, *steps: Step):
        pass