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
