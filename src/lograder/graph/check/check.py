from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, Field

from ...common.result import Err, Ok, Result
from ...exception import DeveloperException
from ..config import get_config
from ..package import Manifest, Package
from ..step import Step


class CheckError(BaseModel):
    check_name: str


class CheckData(BaseModel):
    check_name: str


class Check(Step, ABC):
    def __init__(self, parallel: bool = False):
        self._parallel: bool = parallel

    @property
    def parallel(self) -> bool:
        return self._parallel

    @abstractmethod
    def __call__(self, package: Package) -> Result[list[CheckData], CheckError]: ...


class ManifestCheckData(CheckData):
    check_name: str = Field(default="Manifest Check")
    manifest_expected: Manifest
    manifest_received: Manifest


class ManifestCheckError(CheckError):
    check_name: str = Field(default="Manifest Check")
    manifest_expected: Manifest
    manifest_received: Manifest


class ManifestCheck(Check, valid_inputs=[Manifest], output=Manifest):
    def __init__(
        self, expected_manifest: Manifest, strict: bool = False, parallel: bool = False
    ):
        super().__init__(parallel)
        root_dir = get_config().root_directory
        self._expect: set[Path] = set(
            p.relative_to(root_dir) if p.is_relative_to(root_dir) else p
            for p in expected_manifest.paths
        )
        self._expect_manifest = expected_manifest
        self._strict = strict

    def __call__(self, package: Package) -> Result[list[CheckData], CheckError]:
        root_dir = get_config().root_directory
        if not isinstance(package, Manifest):
            raise DeveloperException(
                f"Must pass `Manifest` to `ManifestCheck`, received {package.__class__.__name__}; additionally, this error message should be unreachable."
            )
        received = set(
            p.relative_to(root_dir) if p.is_relative_to(root_dir) else p
            for p in package.paths
        )
        if (
            received != self._expect
        ):  # TODO: This is bugged; update it to match formatter check.
            return Err(
                ManifestCheckError(
                    manifest_expected=self._expect_manifest, manifest_received=package
                )
            )
        return Ok(
            [
                ManifestCheckData(
                    manifest_expected=self._expect_manifest, manifest_received=package
                )
            ]
        )
