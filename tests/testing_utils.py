import json
import shutil
from pathlib import Path

from lograder.data.paths import PathConfig


def get_results() -> dict:
    return json.load(open(PathConfig.DEFAULT_RESULT_PATH))


def create_dummy_submission(grader_root: Path, project_root: Path) -> None:
    root_path = grader_root / "autograder"
    submission_path = root_path / "submission"
    source_path = root_path / "source"
    result_path = root_path / "results"
    json_path = result_path / "results.json"

    root_path.mkdir(parents=True, exist_ok=True)
    submission_path.mkdir(parents=True, exist_ok=True)
    source_path.mkdir(parents=True, exist_ok=True)
    result_path.mkdir(parents=True, exist_ok=True)

    PathConfig.DEFAULT_ROOT_PATH = root_path
    PathConfig.DEFAULT_SUBMISSION_PATH = submission_path
    PathConfig.DEFAULT_SOURCE_PATH = source_path
    PathConfig.DEFAULT_RESULT_PATH = json_path

    sub_root = project_root / "submission"
    sou_root = project_root / "source"
    if sub_root.exists() and sou_root.exists():
        shutil.copytree(sub_root, submission_path, dirs_exist_ok=True)
        shutil.copytree(sou_root, source_path, dirs_exist_ok=True)
    else:
        shutil.copytree(project_root, submission_path, dirs_exist_ok=True)
