import subprocess
import sys
from collections import deque
from pathlib import Path
from typing import List, Optional

from static.lograderbasicconfig import LograderBasicConfig


def bfs_walk(root: Path):  # pathlib defaults to dfs; must implement bfs ourselves.
    queue = deque([root])
    while queue:
        current = queue.popleft()
        if current.is_dir():
            for child in current.iterdir():
                queue.append(child)
        else:
            yield current


def is_cxx_source_file(path: Path) -> bool:
    return path.exists() and path.suffix in (
        ".cc",
        ".cp",
        ".cxx",
        ".cpp",
        ".CPP",
        ".c++",
        ".C",
        ".c",
    )


def is_cmake_file(path: Path) -> bool:
    return path.exists() and path.name.startswith("CMakeLists.txt")


def is_makefile_file(path: Path) -> bool:
    return path.exists() and path.name == "Makefile"


def is_makefile_target(makefile: Path, target: str) -> bool:
    if not is_makefile_file(makefile):
        return False
    proc = subprocess.run(
        ["make", "-qp"], cwd=makefile.parent, capture_output=True, text=True
    )
    for line in proc.stdout.splitlines():
        if line.strip().startswith(f"{target}:"):
            return True
    return False


def is_valid_target(target: str) -> bool:
    if target in (
        "all",
        "install",
        "depend",
        "test",
        "package",
        "package_source",
        "edit_cache",
        "rebuild_cache",
        "clean",
        "help",
        "ALL_BUILD",
        "ZERO_CHECK",
        "INSTALL",
        "RUN_TESTS",
        "PACKAGE",
    ):
        return False
    if target.endswith(".obj") or target.endswith(".i") or target.endswith(".s"):
        return False
    return True


def do_process(args: List[str | Path], **kwargs) -> subprocess.CompletedProcess:
    win_prefix: List[str | Path] = ["cmd", "/c"]
    cmd: List[str | Path] = args
    if sys.platform.startswith("win"):
        cmd = win_prefix + cmd
    return subprocess.run(cmd, **kwargs)


def run_cmd(
    cmd: List[str | Path],
    commands: Optional[List[List[str | Path]]] = None,
    stdout: Optional[List[str]] = None,
    stderr: Optional[List[str]] = None,
    working_directory: Optional[Path] = None,
):

    if working_directory is None:
        result = do_process(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=LograderBasicConfig.DEFAULT_EXECUTABLE_TIMEOUT,
        )
    else:
        result = do_process(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=LograderBasicConfig.DEFAULT_EXECUTABLE_TIMEOUT,
            cwd=working_directory,
        )

    if commands is not None:
        commands.append(cmd)
    if stdout is not None:
        stdout.append(result.stdout)
    if stderr is not None:
        stderr.append(result.stderr)
    return result
