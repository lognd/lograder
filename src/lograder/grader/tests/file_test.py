from __future__ import annotations

import difflib
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .interfaces.test import TestInterface

if TYPE_CHECKING:
    from ...types import ByteStreamComparisonOutput


class FileTest(TestInterface):
    def __init__(self):
        super().__init__()
        self._name: str = ""
        self._base_filename: Optional[Path] = None
        self._target_filename: Optional[Path] = None
        self._run: bool = False

    @classmethod
    def make(
        cls, name: str, expected_file: Path, actual_file: Path, visible: bool = True
    ) -> FileTest:
        test = cls()
        test.set_name(name)
        test.set_base_filename(expected_file)
        test.set_target_filename(actual_file)
        test.set_visibility(visible)
        return test

    def set_name(self, name: str):
        self._name = name

    def get_name(self) -> str:
        return self._name

    def set_base_filename(self, path: Path):
        self._base_filename = path

    def get_base_filename(self):
        assert self._base_filename is not None
        return self._base_filename

    def set_target_filename(self, path: Path):
        self._target_filename = path

    def get_target_filename(self):
        assert self._target_filename is not None
        return self._target_filename

    def get_expected_output(self) -> bytes:
        with open(self.get_base_filename(), "rb") as f:
            return f.read()

    def get_actual_output(self):
        with open(self.get_target_filename(), "rb") as f:
            return f.read()

    def get_score(self) -> float:
        streams: ByteStreamComparisonOutput = {
            "stream_expected_bytes": self.get_expected_output(),
            "stream_actual_bytes": self.get_actual_output(),
        }
        if not self._run:  # stop duplicate appending
            self.add_to_output("byte-cmp", streams)
            self._run = True

        return (
            (
                difflib.SequenceMatcher(
                    None,
                    streams["stream_actual_bytes"],
                    streams["stream_expected_bytes"],
                ).ratio()
            )
            * self.get_max_score()
            * self.get_weight()
        )
