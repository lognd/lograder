from typing import Generator, final

from pydantic import Field

from ...common import Err, Ok, Result, Unreachable
from ..types.package import Manifest
from .check import Check, CheckData, CheckError


class ManifestCheckData(CheckData):
    check_name: str = Field(default="Manifest Check")
    manifest_expected: Manifest
    manifest_received: Manifest


class ManifestCheckError(CheckError):
    check_name: str = Field(default="Manifest Check")
    manifest_expected: Manifest
    manifest_received: Manifest


@final
class ManifestCheck(
    Check[Manifest, Manifest, ManifestCheckError, ManifestCheckData, Unreachable]
):
    def __init__(self, expected_manifest: Manifest, strict: bool = False) -> None:
        super().__init__()
        self._expected = expected_manifest
        self._strict = strict

    def __call__(
        self, received: Manifest
    ) -> Generator[
        Result[ManifestCheckData, Unreachable],
        None,
        Result[Manifest, ManifestCheckError],
    ]:
        if received == self._expected or (
            not self._strict and self._expected <= received
        ):
            yield Ok(
                ManifestCheckData(
                    manifest_expected=self._expected,
                    manifest_received=received,
                )
            )
            return Ok(received)
        return Err(
            ManifestCheckError(
                manifest_expected=self._expected,
                manifest_received=received,
            )
        )
