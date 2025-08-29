from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..common import Status, TextFormat, Visibility


class TestCaseJSON(BaseModel):
    score: Optional[float]
    max_score: Optional[float]
    execution_time: Optional[float] = Field(default=None, exclude=True)
    status: Optional[Status] = None
    name: Optional[str]
    name_format: Optional[TextFormat] = "text"
    number: Optional[str] = None
    output: Optional[str]
    output_format: Optional[TextFormat] = "ansi"
    tags: List[str] = Field(default_factory=list)
    visibility: Optional[Visibility] = "hidden"
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
