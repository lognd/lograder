from os.path import normpath
from pathlib import Path
from typing import Generator, Literal, TypeAlias, cast

from pydantic import Field

from ...common import Err, Ok, Result, Unreachable
from ..types.parcels import Manifest
from .check import Check
from .manifest import ManifestCheckData, ManifestCheckError

ProjectType: TypeAlias = Literal["CMake", "Makefile", "PyProject"]
REQUIRED_FILES: dict[ProjectType, list[Path | str]] = {
    "CMake": ["CMakeLists.txt"],
    "Makefile": ["Makefile"],
    "PyProject": ["pyproject.toml"],
}


def make_simple_manifest_checker(
    project_name: ProjectType, req_files: list[Path | str]
) -> tuple[
    type[Manifest], type[ManifestCheckData], type[ManifestCheckError], type[Check]
]:
    _req_files: list[Path] = [Path(normpath(p)) for p in req_files]

    manifest_name = f"{project_name}ProjectManifest"
    data_name = f"{project_name}ManifestCheckData"
    error_name = f"{project_name}ManifestCheckError"
    check_name = f"{project_name}ManifestCheck"
    display_name = f"{project_name} Manifest Check"

    class ProjectManifest(Manifest):
        def __init__(self, manifest: Manifest):
            super().__init__(manifest._mapping)

    ProjectManifest.__name__ = manifest_name
    ProjectManifest.__qualname__ = manifest_name

    class ProjectCheckData(ManifestCheckData):
        check_name: str = Field(default=display_name)

    ProjectCheckData.__name__ = data_name
    ProjectCheckData.__qualname__ = data_name
    ProjectCheckData.model_rebuild()

    class ProjectCheckError(ManifestCheckError):
        check_name: str = Field(default=display_name)

    ProjectCheckError.__name__ = error_name
    ProjectCheckError.__qualname__ = error_name
    ProjectCheckError.model_rebuild()

    class ProjectManifestCheck(
        Check[
            Manifest, ProjectManifest, ProjectCheckError, ProjectCheckData, Unreachable
        ]
    ):
        def __call__(
            self, input: Manifest
        ) -> Generator[
            Result[ProjectCheckData, Unreachable],
            None,
            Result[ProjectManifest, ProjectCheckError],
        ]:
            for file in _req_files:
                if file not in input:
                    return Err(
                        ProjectCheckError(
                            manifest_expected=Manifest.from_flat(_req_files),
                            manifest_received=input,
                        )
                    )
            yield Ok(
                ProjectCheckData(
                    manifest_expected=Manifest.from_flat(_req_files),
                    manifest_received=input,
                )
            )
            return Ok(ProjectManifest(input))

    ProjectManifestCheck.__name__ = check_name
    ProjectManifestCheck.__qualname__ = check_name

    return ProjectManifest, ProjectCheckData, ProjectCheckError, ProjectManifestCheck


REGISTERED_TYPES: dict[
    str,
    tuple[
        type[Manifest], type[ManifestCheckData], type[ManifestCheckError], type[Check]
    ],
] = {}


def get_manifest_cls(project_name: ProjectType) -> type[Manifest]:
    return REGISTERED_TYPES[project_name][0]


def get_data_cls(project_name: ProjectType) -> type[ManifestCheckData]:
    return REGISTERED_TYPES[project_name][1]


def get_error_cls(project_name: ProjectType) -> type[ManifestCheckError]:
    return REGISTERED_TYPES[project_name][2]


def get_check_cls(project_name: ProjectType) -> type[Check]:
    return REGISTERED_TYPES[project_name][3]


for project_name, req_files in REQUIRED_FILES.items():
    manifest_cls, data_cls, error_cls, check_cls = make_simple_manifest_checker(
        project_name, req_files
    )

    globals()[manifest_cls.__name__] = manifest_cls
    globals()[data_cls.__name__] = data_cls
    globals()[error_cls.__name__] = error_cls
    globals()[check_cls.__name__] = check_cls

    REGISTERED_TYPES[project_name] = (manifest_cls, data_cls, error_cls, check_cls)
