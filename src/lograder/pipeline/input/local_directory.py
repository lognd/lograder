from pathlib import Path
from typing import Generator

from ...common import Err, Ok, Result, Unreachable
from ...exception import UncaughtException
from ..config import get_config
from ..types.parcels import Manifest
from ..types.sentinel import PIPELINE_START
from .input import Input


class LocalDirectory(
    Input[PIPELINE_START, Manifest, UncaughtException, Unreachable, Unreachable]
):
    def __init__(self, root: Path = get_config().root_directory) -> None:
        self.root = root

    def __call__(
        self, _: PIPELINE_START
    ) -> Generator[
        Result[Unreachable, Unreachable],
        None,
        Result[Manifest, UncaughtException],
    ]:
        if False:
            yield  # required for python to see this as a generator.
        try:
            manifest = Manifest.from_directory(self.root)
            return Ok(manifest)
        except Exception as e:
            return Err(UncaughtException(error=e))
