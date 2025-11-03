from __future__ import annotations

import shutil
import tempfile
import traceback
import weakref
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Dict, List, Optional, TypeAlias, TypedDict, Union

from .process import ProcessBool

# -------------------------------------------------------------------------
# Type Definitions
# -------------------------------------------------------------------------

DirectoryType: TypeAlias = Dict[str, Union[List[str], "DirectoryType"]]
"""Nested dictionary type representing a directory tree.

Example:
    {
        "_files": ["main.cpp", "CMakeLists.txt"],
        "src": {
            "_files": ["app.cpp"],
            "include": {
                "_files": ["app.h"]
            }
        }
    }
"""


class DirectoryMatch(TypedDict):
    """Structured result from a directory comparison."""

    ok: bool
    missing_files: List[Path]
    extra_files: List[Path]
    missing_dirs: List[Path]
    extra_dirs: List[Path]


# -------------------------------------------------------------------------
# Directory Tree Comparison Utility
# -------------------------------------------------------------------------


class Directory:
    """Represents an expected directory layout for structure validation.

    Each `Directory` node contains:
      - Its filesystem path (absolute or relative)
      - A list of expected files
      - A list of expected subdirectories (as `Directory` objects)
    """

    def __init__(self, name: str, parent: Optional[Directory] = None):
        """
        Args:
            name: Directory name or absolute path if `parent` is None.
            parent: Parent Directory, if nested.
        """
        if parent is None:
            self._path = Path(name)
        else:
            self._path = parent.path / name
        self._files: List[Path] = []
        self._subdirectories: List[Directory] = []

    def add_file(self, file: str) -> None:
        """Add a file to the expected directory contents."""
        self._files.append(self.path / file)

    def add_subdirectory(self, directory: Directory) -> None:
        """Add a subdirectory (as a `Directory` object)."""
        self._subdirectories.append(directory)

    def match(self, directory: Path, strict: bool = False) -> DirectoryMatch:
        """Compare the actual contents of a path against this expected structure.

        Args:
            directory: The actual filesystem directory to validate.
            strict: If True, extra files and directories also count as mismatches.

        Returns:
            A `DirectoryMatch` dictionary detailing missing and extra elements.
        """
        actual_files = {p for p in directory.glob("*") if p.is_file()}
        actual_dirs = {p for p in directory.glob("*") if p.is_dir()}

        expected_files = {self.path / f.name for f in self.files}
        expected_dirs = {self.path / d.path.name for d in self.subdirectories}

        missing_files = [f for f in expected_files if not (directory / f.name).exists()]
        extra_files = [
            f for f in actual_files if f.name not in {ef.name for ef in expected_files}
        ]

        missing_dirs = [d for d in expected_dirs if not (directory / d.name).exists()]
        extra_dirs = [
            d for d in actual_dirs if d.name not in {ed.name for ed in expected_dirs}
        ]

        # Recursively validate subdirectories
        for sub in self.subdirectories:
            real_sub = directory / sub.path.name
            if real_sub.exists() and real_sub.is_dir():
                subresult = sub.match(real_sub, strict)
                missing_files += subresult["missing_files"]
                extra_files += subresult["extra_files"]
                missing_dirs += subresult["missing_dirs"]
                extra_dirs += subresult["extra_dirs"]

        ok = not (missing_files or missing_dirs)
        if strict:
            ok = ok and not (extra_files or extra_dirs)

        return {
            "ok": ok,
            "missing_files": missing_files,
            "extra_files": extra_files,
            "missing_dirs": missing_dirs,
            "extra_dirs": extra_dirs,
        }

    @property
    def path(self) -> Path:
        """Filesystem path represented by this Directory node."""
        return self._path

    @property
    def subdirectories(self) -> List[Directory]:
        """List of nested `Directory` objects representing expected subdirectories."""
        return self._subdirectories

    @property
    def files(self) -> List[Path]:
        """List of expected file paths in this directory."""
        return self._files

    @classmethod
    def read(cls, tree: DirectoryType) -> Directory:
        """Recursively construct a `Directory` hierarchy from a nested dictionary.

        Args:
            tree: Nested structure describing directories and files.

        Returns:
            A `Directory` instance representing the root of the structure.
        """
        root = Directory("/")
        files = tree.get("_files", [])
        if files and isinstance(files, list):
            for file in files:
                root.add_file(file)
        for name, item in tree.items():
            if isinstance(item, dict):
                subdir = cls(name, root).read(item)
                root.add_subdirectory(subdir)
        return root


# -------------------------------------------------------------------------
# File Handler Interfaces
# -------------------------------------------------------------------------


class FileHandlerInterface(ProcessBool, ABC):
    """Abstract base class for managing isolated file copies.

    Creates a temporary root directory (`tempfile.mkdtemp()`) that is automatically
    deleted on garbage collection. Subclasses implement specific setup behaviors.
    """

    def __init__(self):
        super().__init__()
        self._root_dir: Path = Path(tempfile.mkdtemp())

        def _cleanup(_root_dir: Path):
            shutil.rmtree(_root_dir, ignore_errors=True)

        weakref.finalize(self, _cleanup, self._root_dir)

    @property
    def root_dir(self) -> Path:
        """Temporary working directory path."""
        return self._root_dir

    def move_file(self, file: Path, root: Path) -> Optional[Path]:
        """Copy a file into the isolated working directory, preserving structure.

        Args:
            file: File to copy.
            root: Root directory relative to which the path structure is preserved.

        Returns:
            The new file path in the temp root, or None if the operation failed.
        """
        relative_path: Path = file.relative_to(root)
        new_path: Path = self.root_dir / relative_path
        try:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(file, new_path)
            return new_path
        except PermissionError as e:
            self.set_failure(e, "Could not make new directories or copy files.")
        return None

    @abstractmethod
    def setup(self) -> None:
        """Perform the subclass-specific setup procedure."""
        ...


class ProjectFileHandler(FileHandlerInterface):
    """Copies all project files from a root directory into a temporary workspace."""

    def __init__(self, project_root: Path):
        """
        Args:
            project_root: The root directory of the project to copy.
        """
        super().__init__()
        self._project_root = project_root

    @property
    def project_root(self) -> Path:
        """Original project directory path."""
        return self._project_root

    def setup(self) -> None:
        """Copy all files from the project root into the temp workspace."""
        for file in self.project_root.rglob("*"):
            if file.is_file():
                self.move_file(file, self.project_root)


class MixinFileHandler(FileHandlerInterface):
    """Combines a base directory and a mixin/submission directory into one workspace.

    This is typically used for combining instructor-provided starter code (base)
    with student submissions (mixin). Optionally executes a callback after each
    mixin file is successfully moved.
    """

    def __init__(
        self,
        base: Path,
        submission: Path,
        mixin_callback: Optional[Callable[[Path], None]] = None,
    ):
        """
        Args:
            base: The base directory containing original project files.
            submission: The submission directory containing mix-in files.
            mixin_callback: Optional function to execute after copying each file
                from the submission directory.
        """
        super().__init__()
        self._base = base
        self._mixin = submission
        self._callback = mixin_callback or (lambda _: None)

    @property
    def base(self) -> Path:
        """Base directory (e.g., instructor code)."""
        return self._base

    @property
    def mixin(self) -> Path:
        """Mixin directory (e.g., student submission)."""
        return self._mixin

    def setup(self) -> None:
        """Copy files from both base and mixin directories into the temp workspace.

        - Base files are copied first.
        - Mixin files overwrite only if not already present.
        - Executes the callback for each successfully copied mixin file.
        """
        # Copy base files
        for file in self.base.rglob("*"):
            if file.is_file():
                self.move_file(file, self.base)

        # Copy mixin files, checking for conflicts
        for file in self.mixin.rglob("*"):
            if not file.is_file():
                continue

            dest = self.root_dir / file.relative_to(self.mixin)
            if dest.exists():
                self.set_failure(traceback=f"File `{file}` already exists.")
                continue

            new_path = self.move_file(file, self.mixin)
            if new_path is not None:
                try:
                    self._callback(new_path)
                except Exception as e:
                    self.set_failure(e, traceback=traceback.format_exc())
