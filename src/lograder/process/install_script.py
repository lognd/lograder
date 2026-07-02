from pathlib import Path
from typing import Callable, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from lograder.common import Err, Ok, Result
from lograder.exception import DeveloperException
from lograder.process.cli_args import CLIArgs
from lograder.process.executable import (
    ExecutableInput,
    ExecutableOptions,
    ExecutableOutput,
    InstallationError,
    InstallationExecutable,
    TypedExecutable,
)
from lograder.process.registry.bash import BashExecutable, BashScriptArgs

T = TypeVar("T")


class PlatformInstallScript(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    executable: TypedExecutable
    args: CLIArgs
    install_location: Optional[Path] = None
    append_command_arguments: list[str] = Field(default_factory=list)
    input: ExecutableInput = Field(default_factory=ExecutableInput)
    options: ExecutableOptions = Field(default_factory=ExecutableOptions)


def simple_bash_install_script(
    caller_file: str,
    script_filename: str,
    *,
    install_location: Optional[Path] = None,
) -> PlatformInstallScript:
    """Build a PlatformInstallScript that runs a bash script from data/install_scripts/.

    ``caller_file`` should be the registry module's own ``__file__``, so the
    script path resolves relative to that module regardless of caller depth.
    """
    return PlatformInstallScript(
        executable=BashExecutable(),
        args=BashScriptArgs(
            script=Path(caller_file).parents[2]
            / "data/install_scripts"
            / script_filename
        ),
        install_location=install_location,
    )


class InstallScript(InstallationExecutable):
    def __init__(self, script_map: dict[Callable[[], bool], PlatformInstallScript]):
        self._install_location: Optional[Path] = None
        self._append_command_arguments: list[str] = []
        self._run_checker: Callable[[], bool] = lambda: False
        self._p_checks = script_map

        for platform_check, platform_install in script_map.items():
            if platform_check():
                super().__init__(
                    executable=platform_install.executable,
                    args=platform_install.args,
                    input=platform_install.input,
                    options=platform_install.options,
                )
                self._install_location = platform_install.install_location
                self._append_command_arguments = (
                    platform_install.append_command_arguments
                )
                self._run_checker = platform_check
                return

    def validate_runnable(self) -> None:
        if not self._run_checker():
            raise DeveloperException(
                f"None of the platform checks in (`{'`, `'.join(getattr(f, '__name__', repr(f)) for f in self._p_checks)}`, total of {len(self._p_checks)} checks) "
                f"within class, `{self.__class__.__name__}`, were true, likely meaning that an install script is not implemented for your platform."
            )

    def get_command(
        self, output: ExecutableOutput
    ) -> Result[Optional[list[str]], InstallationError]:
        if self._install_location is not None and not self._install_location.exists():
            current_dir_items = "`, `".join(str(d) for d in Path.cwd().iterdir())
            return Err(
                InstallationError(
                    module=output.command,
                    message=(
                        f"The installation succeeded (return code was zero), but the location where the executable should "
                        f"be, `{self._install_location}`, does not exist. The current working directory is `{Path.cwd()}` and "
                        f"{'is empty.' if not current_dir_items else 'has the children, `' + current_dir_items + '`.'}"
                    ),
                )
            )
        elif self._install_location is not None:
            return Ok([str(self._install_location)])
        return Ok(None)
