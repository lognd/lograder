from __future__ import annotations

import shlex
from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .test import TestInterface

if TYPE_CHECKING:
    from ....types import Command
    from ...addons.addon import ExecAddonInterface


class CLITest(TestInterface, ABC):
    def __init__(self):
        super().__init__()

        self._args: Command = []
        self._wrap_args: bool = False
        self._working_dir: Optional[Path] = None
        self._stdin: str = ""

    def set_input(self, stdin: str) -> None:
        self._stdin = stdin

    def get_input(self) -> str:
        return self._stdin

    def set_working_dir(self, path: Path):
        self._working_dir = path

    def get_working_dir(self) -> Optional[Path]:
        return self._working_dir

    def set_wrap_args(self, wrap: bool = True) -> None:
        self._wrap_args = wrap

    def get_wrap_args(self) -> bool:
        return self._wrap_args

    def set_args(self, args: Command) -> None:
        self._args = args

    def get_args(self) -> Command:
        if self.get_wrap_args():
            return [
                f'ARGS="{shlex.join([str(arg.resolve()) if isinstance(arg, Path) else arg for arg in self._args])}"'
            ]
        return self._args

    def add_exec_addon(self, addon: ExecAddonInterface):
        addon.set_args(self.get_args())
        addon.set_input(self.get_input())
        self.add_addon(addon)
