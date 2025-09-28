from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ....types import Command


class BuilderInterface(ABC):
    def __init__(self):
        super().__init__()
        self._project_root: Optional[Path] = None
        self._built: bool = False
        self._build_error: bool = False

    def set_build_error(self, build_error: bool = True) -> None:
        self._build_error = build_error

    def get_build_error(self) -> bool:
        return self._build_error

    def set_project_root(self, path: Path) -> None:
        self._project_root = path

    def get_project_root(self) -> Path:
        assert self._project_root is not None
        return self._project_root

    def build(self) -> None:
        if not self._built:
            self._built = True
            self.build_project()

    def wrap_args(self) -> bool:
        return False

    @abstractmethod
    def build_project(self) -> None:
        pass

    @abstractmethod
    def get_build_directory(self) -> Path:
        pass

    @abstractmethod
    def get_start_command(self) -> Command:
        pass
