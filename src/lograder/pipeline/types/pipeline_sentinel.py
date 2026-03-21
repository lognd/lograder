from __future__ import annotations

from typing import Optional, final

from ...common import Empty

_PIPELINE_START_SINGLETON: Optional[PIPELINE_START] = None


# noinspection PyPep8Naming
@final
class PIPELINE_START(Empty):
    def __new__(cls) -> PIPELINE_START:
        global _PIPELINE_START_SINGLETON
        if _PIPELINE_START_SINGLETON is None:
            _PIPELINE_START_SINGLETON = super().__new__(cls)
        return _PIPELINE_START_SINGLETON
