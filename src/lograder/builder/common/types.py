from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import List, Literal, Union

from pydantic import BaseModel, Field

# TODO: Add leaderboard support.

ProjectType = Literal["cmake", "cxx-source", "makefile"]


class AssignmentMetadata(BaseModel):
    assignment_name: str
    assignment_authors: List[str]
    assignment_description: str
    assignment_due_date: datetime
    assignment_submit_date: datetime = Field(default_factory=datetime.now)

    @property
    def library_name(self) -> str:
        return "lograder"

    @property
    def library_meta(self) -> metadata.PackageMetadata:
        return metadata.metadata(self.library_name)

    @property
    def library_authors(self) -> List[str]:
        return ["Logan Dapp"]

    @property
    def library_version(self) -> str:
        return metadata.version(self.library_name)


class PreprocessorOutput(BaseModel):
    commands: List[List[Union[str, Path]]]
    stdout: List[str]
    stderr: List[str]

    @property
    def is_successful(self) -> bool:
        return all([cerr == "" for cerr in self.stderr])


class BuilderOutput(BaseModel):
    commands: List[List[str | Path]]
    stdout: List[str]
    stderr: List[str]
    build_type: ProjectType

    @property
    def is_successful(self) -> bool:
        return all([cerr == "" for cerr in self.stderr])
