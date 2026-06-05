from abc import ABC
from typing import TypeVar
from typing import Optional
from typing_extensions import Self
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator

from lograder.common import Result, Ok, Err
from lograder.pipeline.types.parcels import Manifest
from lograder.exception import DeveloperException
from lograder.process.executable import ExecutableOutput, InstallationError

from lograder.pipeline.step import Step


InputT = TypeVar("InputT")
OkOutputT = TypeVar("OkOutputT")
ErrOutputT = TypeVar("ErrOutputT")
OkDisplayT = TypeVar("OkDisplayT")
ErrDisplayT = TypeVar("ErrDisplayT")


class BuildOutput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    manifest: Manifest
    config_file: Path
    executable_output: Optional[ExecutableOutput] = None
    install_error: Optional[InstallationError] = None

    @model_validator(mode="after")
    def ensure_mutually_exclusive(self) -> Self:
        if self.executable_output is None and self.install_error is None:
            raise ValueError(
                "Must specify (exclusively) either `output` or `install_error`; neither were specified."
            )
        if self.executable_output is not None and self.install_error is not None:
            raise ValueError(
                "Must specify (exclusively) either `output` or `install_error`; both were specified."
            )
        return self

    @property
    def data(self) -> ExecutableOutput | InstallationError:
        if self.install_error is not None:
            return self.install_error
        if self.executable_output is not None:
            return self.executable_output
        raise DeveloperException


def make_build_output(
    build_exec_output: Result[ExecutableOutput, InstallationError],
    manifest: Manifest,
    config_file: Path,
) -> Result[BuildOutput, BuildOutput]:
    if build_exec_output.is_err:
        return Err(
            BuildOutput(
                manifest=manifest,
                config_file=config_file,
                install_error=build_exec_output.danger_err,
            )
        )

    ok = build_exec_output.danger_ok
    if ok.return_code != 0:
        return Err(
            BuildOutput(
                manifest=manifest, config_file=config_file, executable_output=ok
            )
        )

    return Ok(
        BuildOutput(manifest=manifest, config_file=config_file, executable_output=ok)
    )


class Build(Step[InputT, OkOutputT, ErrOutputT, OkDisplayT, ErrDisplayT], ABC): ...


import lograder.output.layout.pipeline.build  # noqa: E402, F401
