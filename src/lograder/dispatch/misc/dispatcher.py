from datetime import datetime
from pathlib import Path
from typing import List

from ...static import LograderBasicConfig
from ..common.file_operations import bfs_walk, is_cmake_file, is_makefile_file
from ..common.interface import (
    DispatcherInterface,
    ExecutableBuildResults,
    PreprocessorInterface,
    PreprocessorResults,
    RuntimeResults,
)
from ..common.templates import TrivialPreprocessor
from ..common.types import AssignmentMetadata, ProjectType
from ..cpp import CMakeDispatcher, CxxSourceDispatcher
from .makefile import MakefileDispatcher


def detect_project_type(project_root: Path) -> ProjectType:
    for file in bfs_walk(project_root):
        if is_cmake_file(file):
            return "cmake"
        if is_makefile_file(file):
            return "makefile"
    return "cxx-source"


class ProjectDispatcher(DispatcherInterface):
    def __init__(
        self,
        *,
        assignment_name: str,
        assignment_authors: List[str],
        assignment_description: str,
        assignment_due_date: datetime,
        project_root: Path = LograderBasicConfig.DEFAULT_SUBMISSION_PATH,
        preprocessor: PreprocessorInterface = TrivialPreprocessor(),
    ):
        super().__init__()
        self._metadata = AssignmentMetadata(
            assignment_name=assignment_name,
            assignment_authors=assignment_authors,
            assignment_description=assignment_description,
            assignment_due_date=assignment_due_date,
        )

        project_type: ProjectType = detect_project_type(project_root)
        self._internal_project: DispatcherInterface

        if project_type == "cmake":
            self._internal_project = CMakeDispatcher(
                assignment_name=assignment_name,
                assignment_authors=assignment_authors,
                assignment_description=assignment_description,
                assignment_due_date=assignment_due_date,
                project_root=project_root,
                preprocessor=preprocessor,
            )
        elif project_type == "makefile":
            self._internal_project = MakefileDispatcher(
                assignment_name=assignment_name,
                assignment_authors=assignment_authors,
                assignment_description=assignment_description,
                assignment_due_date=assignment_due_date,
                project_root=project_root,
                preprocessor=preprocessor,
            )
        else:
            self._internal_project = CxxSourceDispatcher(
                assignment_name=assignment_name,
                assignment_authors=assignment_authors,
                assignment_description=assignment_description,
                assignment_due_date=assignment_due_date,
                project_root=project_root,
                preprocessor=preprocessor,
            )

    def metadata(self) -> AssignmentMetadata:
        return self._internal_project.metadata()

    def preprocess(self) -> PreprocessorResults:
        return self._internal_project.preprocess()

    def build(self) -> ExecutableBuildResults:
        return self._internal_project.build()

    def run_tests(self) -> RuntimeResults:
        return self._internal_project.run_tests()
