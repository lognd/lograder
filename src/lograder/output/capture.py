from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class CapturedOutput:
    """All four rendered formats of a step's packet stream, captured by the Pipeline.

    Consumers (e.g. Gradescope serializers) call ``for_format`` with whatever
    format string they need; this class handles the mapping from external format
    names (including Gradescope's) to the four lograder-native formats.
    """

    simple: str = ""
    ascii: str = ""
    ansi: str = ""
    html: str = ""

    # Maps both lograder-native and Gradescope output_format names to fields.
    _FORMAT_MAP: dict[str, str] = field(
        default_factory=lambda: {
            "simple": "simple",
            "simple_format": "simple",
            "ascii": "ascii",
            "text": "ascii",
            "ansi": "ansi",
            "html": "html",
            "md": "ascii",  # no markdown layout; fall back to plain text
        },
        init=False,
        repr=False,
        compare=False,
    )

    def for_format(self, fmt: str) -> str:
        """Return the captured text for the given format name.

        Accepts both lograder-native names (``"ansi"``, ``"ascii"``,
        ``"simple"``, ``"html"``) and Gradescope output_format names
        (``"text"``, ``"simple_format"``, ``"md"``).  Unknown names fall
        back to ``simple``.
        """
        attr = self._FORMAT_MAP.get(fmt, "simple")
        return getattr(self, attr, self.simple)
