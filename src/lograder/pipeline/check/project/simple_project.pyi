from pathlib import Path
from typing import Generator, Literal, TypeAlias, overload

from ....common import Result, Unreachable
from ...types.parcels import Manifest
from ..check import Check
from .manifest import ManifestCheckData, ManifestCheckError

ProjectType: TypeAlias = Literal["CMake", "Makefile", "PyProject"]
REQUIRED_FILES: dict[ProjectType, list[Path | str]]

class CMakeProjectManifest(Manifest):
    def __init__(self, manifest: Manifest): ...

class MakefileProjectManifest(Manifest):
    def __init__(self, manifest: Manifest): ...

class PyProjectProjectManifest(Manifest):
    def __init__(self, manifest: Manifest): ...

class CMakeProjectCheckData(ManifestCheckData): ...
class MakefileProjectCheckData(ManifestCheckData): ...
class PyProjectProjectCheckData(ManifestCheckData): ...
class CMakeProjectCheckError(ManifestCheckError): ...
class MakefileProjectCheckError(ManifestCheckError): ...
class PyProjectProjectCheckError(ManifestCheckError): ...

class CMakeProjectManifestCheck(
    Check[
        Manifest,
        CMakeProjectManifest,
        CMakeProjectCheckError,
        CMakeProjectCheckData,
        Unreachable,
    ]
):
    def __call__(
        self, input: Manifest
    ) -> Generator[
        Result[CMakeProjectCheckData, Unreachable],
        None,
        Result[CMakeProjectManifest, CMakeProjectCheckError],
    ]: ...

class MakefileProjectManifestCheck(
    Check[
        Manifest,
        MakefileProjectManifest,
        MakefileProjectCheckError,
        MakefileProjectCheckData,
        Unreachable,
    ]
):
    def __call__(
        self, input: Manifest
    ) -> Generator[
        Result[MakefileProjectCheckData, Unreachable],
        None,
        Result[MakefileProjectManifest, MakefileProjectCheckError],
    ]: ...

class PyProjectProjectManifestCheck(
    Check[
        Manifest,
        PyProjectProjectManifest,
        PyProjectProjectCheckError,
        PyProjectProjectCheckData,
        Unreachable,
    ]
):
    def __call__(
        self, input: Manifest
    ) -> Generator[
        Result[PyProjectProjectCheckData, Unreachable],
        None,
        Result[PyProjectProjectManifest, PyProjectProjectCheckError],
    ]: ...

def get_manifest_cls(project_name: ProjectType) -> type[Manifest]: ...
def get_data_cls(project_name: ProjectType) -> type[ManifestCheckData]: ...
def get_error_cls(project_name: ProjectType) -> type[ManifestCheckError]: ...
def get_check_cls(project_name: ProjectType) -> type[Check]: ...
def make_simple_manifest_checker(
    project_name: str, req_files: list[Path | str]
) -> tuple[
    type[Manifest], type[ManifestCheckData], type[ManifestCheckError], type[Check]
]: ...
