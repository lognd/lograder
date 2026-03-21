import traceback

from pydantic import BaseModel, Field


class LograderException(Exception):
    pass


class DeveloperException(LograderException):
    """
    Raised when library source code has an unexpected error, (i.e. it's `lognd`'s fault).
    """


class StaffException(LograderException):
    """
    Raised when the implementation/exercise has an invalid configuration, (i.e. it's the course staff's fault).
    """


class UncaughtException(BaseModel):
    error: Exception
    error_traceback: str = Field(default_factory=traceback.format_exc)

    @property
    def error_type(self) -> str:
        return self.error.__class__.__name__

    @property
    def error_msg(self) -> str:
        return str(self.error)
