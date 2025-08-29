from .._core_exceptions import LograderError


class LograderBuilderError(LograderError):
    """
    This is the base exception class for all exceptions raised
    by the `lograder.builder` module, for easy error handling.
    """

    pass


class LograderPreprocessorError(LograderError):
    """
    This is the base exception class for all exceptions raised
    by the `lograder.builder` preprocessor tools, for easy error handling.
    """

    pass


class LograderCompilationError(LograderError):
    """
    This is the base exception class for all exceptions raised
    by the `lograder.builder` build tools, for easy error handling.
    """

    pass


class LograderRuntimeError(LograderError):
    """
    This is the base exception class for all exceptions raised
    by the `lograder.builder` run tools, for easy error handling.
    """

    pass
