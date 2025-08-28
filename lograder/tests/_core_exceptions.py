from .._core_exceptions import LograderError

class LograderTestError(LograderError):
    """
    This is the base exception class for all exceptions raised
    by the `lograder.tests` module, for easy error handling.
    """
    pass

class LograderBuildError(LograderTestError):
    """
    This is the base exception class for all exceptions raised
    by the `lograder.tests` module, when the *professor or grader*
    is at fault, for easy error handling.
    """
    pass
