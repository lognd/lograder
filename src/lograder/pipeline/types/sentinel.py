from __future__ import annotations

from typing import Optional, final

from ...common import Empty

_PIPELINE_START_SINGLETON: Optional[PIPELINE_START] = None
_NOT_APPLICABLE_SINGLETON: Optional[NOT_APPLICABLE] = None


# noinspection PyPep8Naming
@final
class PIPELINE_START(Empty):
    def __new__(cls) -> PIPELINE_START:
        global _PIPELINE_START_SINGLETON
        if _PIPELINE_START_SINGLETON is None:
            _PIPELINE_START_SINGLETON = super().__new__(cls)
        return _PIPELINE_START_SINGLETON


# noinspection PyPep8Naming
@final
class NOT_APPLICABLE(Empty):
    def __new__(cls) -> NOT_APPLICABLE:
        global _NOT_APPLICABLE_SINGLETON
        if _NOT_APPLICABLE_SINGLETON is None:
            _NOT_APPLICABLE_SINGLETON = super().__new__(cls)
        return _NOT_APPLICABLE_SINGLETON
