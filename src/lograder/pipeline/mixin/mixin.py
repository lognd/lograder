import shutil
from abc import ABC
from pathlib import Path
from typing import Generator, final

from pydantic import BaseModel

from lograder.common import Ok, Result, Unreachable
from lograder.exception import StaffException
from lograder.pipeline.step import Step
from lograder.pipeline.types.parcels import Manifest


class MixinData(BaseModel):
    source_directory: Path
    destination_directory: Path
    files_copied: list[str]


class Mixin(Step[Manifest, Manifest, Unreachable, MixinData, Unreachable], ABC):
    """Abstract base for pipeline stages that copy files between two directories."""

    pass


@final
class InjectStudentIntoStaff(Mixin):
    """Copies student source files into the staff's project directory.

    Use when staff controls the build system (CMakeLists.txt, Makefile) and
    students submit only implementation files. The returned Manifest is rooted
    at the staff directory.

    Both ``staff_directory`` and the student submission directory must be under
    ``config.root_directory``.

    Args:
        staff_directory: Destination into which student files are copied.
        student_files: Relative path strings or bare filenames to copy.
            ``None`` copies every file in the student manifest.
        overwrite: When ``True`` (default) existing files in ``staff_directory``
            are silently replaced by the student versions.
    """

    def __init__(
        self,
        staff_directory: Path,
        *,
        student_files: list[str] | None = None,
        overwrite: bool = True,
    ) -> None:
        if not staff_directory.exists():
            raise StaffException(
                f"`{self.__class__.__name__}`: staff directory `{staff_directory}` does not exist."
            )
        if not staff_directory.is_dir():
            raise StaffException(
                f"`{self.__class__.__name__}`: staff path `{staff_directory}` is not a directory."
            )
        self._staff_directory = staff_directory
        self._student_files = student_files
        self._overwrite = overwrite

    def __call__(
        self, source_manifest: Manifest
    ) -> Generator[
        Result[MixinData, Unreachable],
        None,
        Result[Manifest, Unreachable],
    ]:
        copied: list[str] = []
        for file_path in source_manifest._files:
            rel = file_path.relative_to(source_manifest.root)
            if self._student_files is not None:
                rel_str = str(rel)
                if (
                    rel_str not in self._student_files
                    and rel.name not in self._student_files
                ):
                    continue
            dest = self._staff_directory / rel
            if dest.exists() and not self._overwrite:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest)
            copied.append(str(rel))

        yield Ok(
            MixinData(
                source_directory=source_manifest.root,
                destination_directory=self._staff_directory,
                files_copied=copied,
            )
        )
        return Ok(Manifest.from_directory(self._staff_directory))


@final
class InjectStaffIntoStudent(Mixin):
    """Copies staff files into the student's submission directory.

    Use when staff needs to inject helper files (test harnesses, private
    headers, override configurations) into a student's submitted project.
    The returned Manifest is rooted at the student's submission directory.

    Both ``staff_source`` and the student submission directory must be under
    ``config.root_directory``.

    Args:
        staff_source: Directory containing the staff files to inject.
        staff_files: Relative path strings or bare filenames to copy.
            ``None`` copies every file in the staff source directory.
        overwrite: When ``True`` (default) existing student files are replaced
            by the injected staff versions.
    """

    def __init__(
        self,
        staff_source: Path,
        *,
        staff_files: list[str] | None = None,
        overwrite: bool = True,
    ) -> None:
        if not staff_source.exists():
            raise StaffException(
                f"`{self.__class__.__name__}`: staff source `{staff_source}` does not exist."
            )
        if not staff_source.is_dir():
            raise StaffException(
                f"`{self.__class__.__name__}`: staff source `{staff_source}` is not a directory."
            )
        self._staff_source = staff_source
        self._staff_files = staff_files
        self._overwrite = overwrite

    def __call__(
        self, source_manifest: Manifest
    ) -> Generator[
        Result[MixinData, Unreachable],
        None,
        Result[Manifest, Unreachable],
    ]:
        staff_manifest = Manifest.from_directory(self._staff_source)
        copied: list[str] = []
        for file_path in staff_manifest._files:
            rel = file_path.relative_to(self._staff_source)
            if self._staff_files is not None:
                rel_str = str(rel)
                if (
                    rel_str not in self._staff_files
                    and rel.name not in self._staff_files
                ):
                    continue
            dest = source_manifest.root / rel
            if dest.exists() and not self._overwrite:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest)
            copied.append(str(rel))

        yield Ok(
            MixinData(
                source_directory=self._staff_source,
                destination_directory=source_manifest.root,
                files_copied=copied,
            )
        )
        return Ok(Manifest.from_directory(source_manifest.root))


import lograder.output.layout.pipeline.mixin  # noqa: E402, F401
