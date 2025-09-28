from datetime import datetime
from importlib import metadata
from typing import List

from pydantic import BaseModel, Field


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
