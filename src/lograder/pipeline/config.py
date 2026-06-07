from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, ContextManager, Iterator, Optional

from pydantic import BaseModel, Field, ValidationError

from lograder.exception import StaffException

try:
    import tomllib
except ImportError:
    # This block was added for tomli backwards compatibility.
    # Note that the mypy-suppression is done intentionally because it is wrong.
    import tomli as tomllib  # type: ignore[no-redef]


class EnvironmentConfig(BaseModel):
    root_directory: Path = Field(default=Path("/"))
    executable_timeout: Optional[float] = None
    executable_max_workers: int = 16
    allow_auto_install: bool = False
    """
    .. warning::
        Auto-installation fetches and runs external scripts at grading time.
        Leave this ``False`` (the default) unless you have specifically
        verified that the target executable cannot be pre-installed on the
        grading machine.  Enabling it dramatically slows every pipeline run
        that encounters a missing tool and introduces a network dependency
        that can break grading silently.

    When ``False``, ``TypedExecutable`` treats a missing executable as a
    fatal ``InstallationError`` rather than attempting installation.
    Enable with ``config(allow_auto_install=True)`` or via
    ``config.toml``.
    """

    @staticmethod
    def diff_keys(*keys: str) -> set[str]:
        bad_keys = set(keys)
        for key in EnvironmentConfig.model_fields.keys():
            bad_keys.discard(key)
        return bad_keys


_config: ContextVar[EnvironmentConfig] = ContextVar("_config")
_config.set(EnvironmentConfig())


def get_config() -> EnvironmentConfig:
    return _config.get()


@contextmanager
def config(**changes: Any) -> Iterator[EnvironmentConfig]:
    """Context manager that temporarily overrides EnvironmentConfig fields for the duration of the block."""
    base = get_config()
    bad_keys = EnvironmentConfig.diff_keys(*changes.keys())
    if bad_keys:
        raise StaffException(
            f"Following `EnvironmentConfig` keys are invalid: `{'`, `'.join(bad_keys)}`."
        )
    try:
        new = base.model_copy(update=changes)
    except ValidationError as e:
        raise StaffException(
            "`EnvironmentConfig` was created with invalid values. (See `pydantic.ValidationError`'s traceback for more information.)"
        ) from e

    tok = _config.set(new)
    try:
        yield new
    finally:
        _config.reset(tok)


def config_from_toml(toml: Path) -> ContextManager[EnvironmentConfig]:
    try:
        return config(**tomllib.load(toml.open("rb")))
    except Exception as e:
        if not toml.is_file():
            raise StaffException(
                f"Could not find provided toml file, `{str(toml)}`"
            ) from e
        raise StaffException(
            f"Provided toml file (`{str(toml)}`) was unparsable. (See traceback for more info.)"
        ) from e
