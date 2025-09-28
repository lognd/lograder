import subprocess
from collections import deque
from pathlib import Path

from ..types import ProjectType


def detect_project_type(project_root: Path) -> ProjectType:
    for file in bfs_walk(project_root):
        if is_cmake_file(file):
            return "cmake"
        if is_makefile_file(file):
            return "makefile"
    return "cxx-source"


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


def is_catch2_file(path: Path) -> bool:
    if not is_cxx_source_file(path):
        return False
    try:
        content = open(path).read()
        if (
            "#define CATCH_CONFIG_RUNNER" in content
            or "#define CATCH_CONFIG_MAIN" in content
        ):
            return True
        return False
    except UnicodeDecodeError:
        return False


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
    if len(target) < 3:
        return False
    if target in (
        "all",
        "install",
        "depend",
        "package",
        "test",
        "package_source",
        "edit_cache",
        "rebuild_cache",
        "clean",
        "help",
        "build.ninja",
        "ALL_BUILD",
        "ZERO_CHECK",
        "INSTALL",
        "RUN_TESTS",
        "PACKAGE",
    ):
        return False
    if "catch2" in target.lower():
        return False
    for banned in ("experimental", "nightly", "continuous", "cache", "cmake"):
        if banned in target.lower():
            return False
    if target.endswith(".obj") or target.endswith(".i") or target.endswith(".s"):
        return False
    return True
