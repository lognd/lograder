from pathlib import Path
from typing import Generator, Literal, TypeAlias, overload

from ....common import Result, Unreachable
from ...types.parcels import Manifest
from ..check import Check
from .manifest import ManifestCheckData, ManifestCheckError

ProjectType: TypeAlias = Literal["CMake", "Makefile", "PyProject"]
REQUIRED_FILES: dict[ProjectType, list[Path | str]]

class CMakeManifest(Manifest):
    def __init__(self, manifest: Manifest): ...

class MakefileManifest(Manifest):
    def __init__(self, manifest: Manifest): ...

class PyProjectManifest(Manifest):
    def __init__(self, manifest: Manifest): ...

class CMakeCheckData(ManifestCheckData): ...
class MakefileCheckData(ManifestCheckData): ...
class PyProjectCheckData(ManifestCheckData): ...
class CMakeCheckError(ManifestCheckError): ...
class MakefileCheckError(ManifestCheckError): ...
class PyProjectCheckError(ManifestCheckError): ...

class CMakeManifestCheck(
    Check[
        Manifest,
        CMakeManifest,
        CMakeCheckError,
        CMakeCheckData,
        Unreachable,
    ]
):
    def __call__(
        self, input: Manifest
    ) -> Generator[
        Result[CMakeCheckData, Unreachable],
        None,
        Result[CMakeManifest, CMakeCheckError],
    ]: ...

class MakefileManifestCheck(
    Check[
        Manifest,
        MakefileManifest,
        MakefileCheckError,
        MakefileCheckData,
        Unreachable,
    ]
):
    def __call__(
        self, input: Manifest
    ) -> Generator[
        Result[MakefileCheckData, Unreachable],
        None,
        Result[MakefileManifest, MakefileCheckError],
    ]: ...

class PyProjectManifestCheck(
    Check[
        Manifest,
        PyProjectManifest,
        PyProjectCheckError,
        PyProjectCheckData,
        Unreachable,
    ]
):
    def __call__(
        self, input: Manifest
    ) -> Generator[
        Result[PyProjectCheckData, Unreachable],
        None,
        Result[PyProjectManifest, PyProjectCheckError],
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
