from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lograder.pipeline.score import PipelineScore


class GradescopeVisibility(str, Enum):
    HIDDEN = "hidden"
    AFTER_DUE_DATE = "after_due_date"
    AFTER_PUBLISHED = "after_published"
    VISIBLE = "visible"


_DEFAULT_RESULTS_PATH = Path("/autograder/results/results.json")


def write_gradescope_results(
    score: PipelineScore,
    *,
    output: str = "",
    path: Path = _DEFAULT_RESULTS_PATH,
    visibility: GradescopeVisibility = GradescopeVisibility.VISIBLE,
    stdout_visibility: GradescopeVisibility = GradescopeVisibility.HIDDEN,
) -> dict[str, Any]:
    """Serialize ``score`` to Gradescope's ``results.json`` format and write it.

    Returns the dict that was written so callers can inspect or assert on it
    without needing to re-read the file.

    Args:
        score: The ``PipelineScore`` returned by ``Pipeline.__call__()``.
        output: Free-text shown to the student at the top of the Gradescope page.
        path: Destination path. Defaults to the standard Gradescope location.
            Parent directories are created automatically.
        visibility: Visibility of the overall submission result.
        stdout_visibility: Whether captured stdout is shown to students.
    """
    result = score.to_gradescope_dict(output=output)
    result["visibility"] = visibility.value
    result["stdout_visibility"] = stdout_visibility.value

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    return result
