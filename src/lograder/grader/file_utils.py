"""file_utils.py

Core utilities for filesystem interaction, command resolution, and project-type detection.

This module provides:
    - Token substitution helpers for process command resolution.
    - Utility functions for scanning and classifying files.
    - Automatic detection of project types (CMake, Makefile, or C++ source).
    - BFS-based directory traversal for efficiency and predictability.

All functions are designed to be pure and easily unit-tested.
"""

import random
import re
import string
import subprocess
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Literal, Optional, Sequence, Union, cast

# ==========================================================
#  Type aliases and constants
# ==========================================================
ProjectType = Literal["cxx-source", "makefile", "cmake"]
FunctionTag = Literal[
    "executable",
    "temp_folder",
    "file_content",
    "file",
    "files",
    "cxx_file",
    "cxx_files",
    "root",
]
Command = Sequence[Union[str, Path]]
Commands = Sequence[Command]
TOKEN_PATTERN = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


# ==========================================================
#  Token and path utilities
# ==========================================================
def random_name() -> str:
    """Generate a random alphanumeric string."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=25))


def random_exe() -> str:
    """Generate a platform-appropriate random executable filename."""
    return f"{random_name()}.exe" if sys.platform.startswith("win") else random_name()


def contains_token(command: Command, token: FunctionTag) -> bool:
    """Check if a token (e.g. ${root}) appears in a command sequence."""
    return f"${{{token}}}" in command


def resolve_tokens(command: Command, context: Dict[FunctionTag, Command]) -> Command:
    """Replace tokens like ${root} in a command with values from a given context."""

    def replace(token: Union[str, Path]):
        if isinstance(token, Path):
            return [token]
        match = TOKEN_PATTERN.match(token)
        if match:
            key = match.group(1)
            if key in context:
                key = cast(FunctionTag, key)
                return context[key]
        return [token]

    return [tok for tokens in command for tok in replace(tokens)]


# ==========================================================
#  File scanning and helpers
# ==========================================================
def bfs_walk(root: Path):
    """Perform a breadth-first traversal of a directory tree."""
    queue = deque([root])
    while queue:
        current = queue.popleft()
        if current.is_dir():
            for child in current.iterdir():
                queue.append(child)
        else:
            yield current


def is_text(path: Path) -> bool:
    """Determine if a file can be decoded as UTF-8 text."""
    if not path.exists():
        return False
    try:
        chunk = path.read_bytes()[:65536]
        chunk.decode("utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    return True


def is_cxx_source_file(path: Path) -> bool:
    """Check if a file is a valid C/C++ source file."""
    if not path.exists() or path.suffix not in {
        ".cc",
        ".cp",
        ".cxx",
        ".cpp",
        ".CPP",
        ".c++",
        ".C",
        ".c",
    }:
        return False
    return is_text(path)


def is_cmake_file(path: Path) -> bool:
    """Return True if the given path is a valid CMakeLists.txt file."""
    return path.exists() and path.name == "CMakeLists.txt" and is_text(path)


def is_catch2_file(path: Path) -> bool:
    """Return True if a file defines a Catch2 test main/runner macro."""
    if not is_cxx_source_file(path):
        return False
    try:
        content = path.read_text(encoding="utf-8")
        return (
            "#define CATCH_CONFIG_RUNNER" in content
            or "#define CATCH_CONFIG_MAIN" in content
        )
    except UnicodeDecodeError:
        return False


def is_makefile_file(path: Path) -> bool:
    """Return True if the given path is a Makefile."""
    return path.exists() and path.name == "Makefile"


def is_makefile_target(makefile: Path, target: str) -> bool:
    """Check if a Makefile defines a given target."""
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
    """Filter out invalid or internal Make/CMake targets."""
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
    if target.endswith((".obj", ".i", ".s")):
        return False
    return True


# ==========================================================
#  Project-type detection system
# ==========================================================
@dataclass
class ProjectDetectionResult:
    """Structured result for project detection heuristics."""

    type: ProjectType
    reason: str
    path: Optional[Path] = None


def detect_cmake_project(root: Path) -> Optional[ProjectDetectionResult]:
    """Detect if the directory contains a CMake project."""
    for path in bfs_walk(root):
        if is_cmake_file(path):
            return ProjectDetectionResult("cmake", "Found CMakeLists.txt", path)
    return None


def detect_make_project(root: Path) -> Optional[ProjectDetectionResult]:
    """Detect if the directory contains a Makefile project."""
    for path in bfs_walk(root):
        if is_makefile_file(path):
            return ProjectDetectionResult("makefile", "Found Makefile", path)
    return None


def detect_cxx_source_project(root: Path) -> Optional[ProjectDetectionResult]:
    """Detect if the directory contains standalone C/C++ source files."""
    for path in bfs_walk(root):
        if is_cxx_source_file(path):
            return ProjectDetectionResult("cxx-source", "Found C/C++ source file", path)
    return None


def detect_project_type(root: Path) -> ProjectType:
    """Detect the type a project folder by applying detection heuristics.

    Detection order:
        1. CMake project  → if CMakeLists.txt exists
        2. Makefile project → if Makefile exists
        3. C++ source project → fallback if C/C++ files exist

    Args:
        root: Path to the project directory.

    Returns:
        One of "cmake", "makefile", or "cxx-source".
    """
    for detector in (
        detect_cmake_project,
        detect_make_project,
        detect_cxx_source_project,
    ):
        result = detector(root)
        if result is not None:
            return result.type
    return "cxx-source"
