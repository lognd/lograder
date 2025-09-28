import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from ..data.build import BuildConfig

if TYPE_CHECKING:
    from ..types import Command


def do_process(args: Command, **kwargs) -> subprocess.CompletedProcess:
    win_prefix: Command = ["cmd", "/c"]
    cmd: Command = args
    if sys.platform.startswith("win"):
        cmd = win_prefix + cmd
    return subprocess.run(cmd, **kwargs)


def run_cmd(
    cmd: List[str | Path],
    stdin: str = "",
    commands: Optional[List[List[str | Path]]] = None,
    stdout: Optional[List[str]] = None,
    stderr: Optional[List[str]] = None,
    working_directory: Optional[Path] = None,
):
    kwargs = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=BuildConfig.DEFAULT_EXECUTABLE_TIMEOUT,
        input=stdin,
    )

    if working_directory is not None:
        kwargs["cwd"] = working_directory

    result = do_process(cmd, **kwargs)

    if commands is not None:
        commands.append(cmd)
    if stdout is not None:
        stdout.append(result.stdout)
    if stderr is not None:
        stderr.append(result.stderr)
    return result
