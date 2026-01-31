import datetime as dt
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from ..exception import DeveloperException


class HTMLItem(BaseModel):
    timestamp: dt.datetime
    level: str
    fragment: str


class HTMLHandler(logging.Handler):
    _TEMPLATE_ROOT: Path = Path(__file__).resolve().parents[1] / "data" / "html"
    _TEMPLATE_PAGE: str = (
        _TEMPLATE_ROOT / "default_handler_page_template.html"
    ).read_text()
    _TEMPLATE_CARD: str = (
        _TEMPLATE_ROOT / "default_handler_card_template.htmf"
    ).read_text()

    def __init__(self, output_file: Optional[str] = None):
        super().__init__()
        self._items: list[HTMLItem] = []
        self._output_file: Optional[Path] = (
            None if output_file is None else Path(output_file).resolve()
        )

    @staticmethod
    def _substitute(base: str, **kwargs: str) -> str:
        # I can't just use format because that would break on the <style> and <script> tags.
        for key, value in kwargs.items():
            base = base.replace(f"{{{{{key}}}}}", value)
        return base

    @classmethod
    def _substitute_page(cls, **kwargs: str) -> str:
        return cls._substitute(cls._TEMPLATE_PAGE, **kwargs)

    @classmethod
    def _substitute_card(cls, **kwargs: str) -> str:
        return cls._substitute(cls._TEMPLATE_CARD, **kwargs)

    def emit(self, record: logging.LogRecord) -> None:
        # noinspection PyBroadException
        try:
            fragment = self.format(record)
            item = HTMLItem(
                timestamp=dt.datetime.fromtimestamp(record.created, tz=dt.timezone.utc),
                level=record.levelname,
                fragment=fragment,
            )
            self._items.append(item)
        # Broad exception handling required for logging handlers; no exception
        # can be raised lest there be an infinite exception loop.
        except Exception:  # noqa: BLE001  (ruff)
            self.handleError(record)

    def render_page(self, *, title: str = "Lograder Report") -> str:
        cards = [
            self._substitute_card(
                timestamp=item.timestamp.isoformat(),
                level=item.level,
                fragment=item.fragment,
            )
            for item in self._items
        ]
        return self._substitute_page(title=title, cards="\n".join(cards))

    @property
    def output_file(self) -> Optional[Path]:
        return self._output_file

    @output_file.setter
    def output_file(self, output_file: Optional[Path]) -> None:
        self._output_file = output_file

    def render_page_to_file(self) -> None:
        if self.output_file is None:
            raise DeveloperException(
                "Tried to render HTML to file from `HTMLHandler`, but there is no assigned file."
            )
        with self.output_file.open("w", encoding="utf-8") as f:
            f.write(self.render_page())
