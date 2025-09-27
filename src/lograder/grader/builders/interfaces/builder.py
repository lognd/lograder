from __future__ import annotations

from pathlib import Path
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ....types import Command

class BuilderInterface(ABC):
    def __init__(self):
        super().__init__()
        self._project_root: Optional[Path] = None

    def set_project_root(self, path: Path) -> None:
        self._project_root = path

    @abstractmethod
    def build_project(self) -> None:
        pass

    @abstractmethod
    def get_start_command(self) -> Command:
        pass
