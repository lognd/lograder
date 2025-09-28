import shutil
import weakref
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from ...random_utils import random_working_directory
from ..builders.interfaces.builder import BuilderInterface


class UnitTesterInterface(BuilderInterface, ABC):
    def __init__(self):
        super().__init__()
        self._testing_root: Optional[Path] = None
        self._instance_root: Path = random_working_directory()

        weakref.finalize(self, self._cleanup, self.get_instance_root())

    def set_testing_root(self, path: Path):
        self._testing_root = path

    def get_testing_root(self):
        assert self._testing_root is not None
        return self._testing_root

    @staticmethod
    def _cleanup(path: Path):
        shutil.rmtree(path, ignore_errors=True)

    @abstractmethod
    def build_test(self) -> None:
        pass

    def set_instance_root(self, path: Path):
        self._instance_root = path

    def get_instance_root(self) -> Path:
        return self._instance_root

    def build_project(self) -> None:
        shutil.copytree(
            self.get_testing_root(), self.get_instance_root(), dirs_exist_ok=True
        )
        shutil.copytree(
            self.get_project_root(), self.get_instance_root(), dirs_exist_ok=True
        )
        self.build_test()
