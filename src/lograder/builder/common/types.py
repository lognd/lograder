from datetime import datetime, timezone
from importlib import metadata
from typing import List

from pydantic import BaseModel, Field

# TODO: Add leaderboard support.


class AssignmentMetadata(BaseModel):
    assignment_name: str
    assignment_authors: List[str]
    assignment_description: str
    assignment_due_date: datetime
    assignment_submit_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    library_name: str = Field(default="lograder")
    library_meta: metadata.PackageMetadata = Field(
        default=metadata.metadata(library_name), exclude=True
    )
    authors = library_meta.get_all("Author") or []
    library_authors: List[str] = Field(default=authors)
    library_version: str = Field(default=metadata.version(library_name))


class PreprocessorOutput(BaseModel):
    commands: List[List[str]]
    stdout: List[str]
    stderr: List[str]

    @property
    def is_successful(self) -> bool:
        return all([cerr == "" for cerr in self.stderr])


class BuilderOutput(BaseModel):
    commands: List[List[str]]
    stdout: List[str]
    stderr: List[str]
    build_type: str

    @property
    def is_successful(self) -> bool:
        return all([cerr == "" for cerr in self.stderr])
