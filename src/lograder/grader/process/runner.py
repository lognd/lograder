from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from ..file_utils import Command
from .process import CommandLineStep, FileProcess, OrderedCommand


class RunnerInterface(FileProcess): ...


class CommandRunner(RunnerInterface):
    def __init__(self, root: Path, command: Command):
        super().__init__(root)
        self._cmd: Command = command
        self._args: Command = []

    def set_args(self, args: Command):
        self._args = args

    def _strip_step(self) -> CommandLineStep:
        steps = list(self.steps.values())
        assert len(steps) == 1, "CommandRunner has multiple steps!"
        step = steps[0]
        assert isinstance(
            step, CommandLineStep
        ), "CommandRunner's step is not a CommandLineStep!"
        return step

    @property
    def stdout(self) -> Optional[str]:
        return self._strip_step().stdout

    @property
    def stderr(self) -> Optional[str]:
        return self._strip_step().stderr

    @property
    def commands(self) -> List[OrderedCommand]:
        """
        Construct the command that the FileProcess will execute.

        Returns:
            A list containing a single `OrderedCommand` wrapping the
            command passed to the runner.
        """
        return [OrderedCommand(order=0, command=list(self._cmd) + list(self._args))]
