from pathlib import Path
from typing import Generator

from lograder.common import Err, Ok, Result, Unreachable
from lograder.exception import UncaughtException
from lograder.pipeline.config import get_config
from lograder.pipeline.input.input import Input
from lograder.pipeline.types.parcels import Manifest
from lograder.pipeline.types.sentinel import PIPELINE_START


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
