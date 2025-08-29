from typing import Any, Sequence

from .._core_exceptions import LograderBuildError


class LograderValidationError(LograderBuildError):
    """
    This is the base exception class for all exceptions raised
    by the `lograder.tests` module, whenever a validation error
    occurs for easy error handling.
    """


class MismatchedSequenceLengthError(LograderValidationError):
    """
    This is the exception that is raised when the inputted
    sequence lengths to a function do not match.
    """

    def __init__(self, **seqs: Sequence[Any]):
        super().__init__(
            "Mismatched sequence lengths passed to parameters: "
            + ", ".join([f"`{kw}` (length of {len(seq)})" for kw, seq in seqs.items()])
        )


class NonSingleArgumentSpecifiedError(LograderValidationError):
    """
    This is the exception that is raised when more than one or zero
    arguments are passed.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(
            "Must specify only a single argument; please choose one. Received the arguments: "
            + ", ".join(
                [f"`{kw}` = {val}" for kw, val in kwargs.items() if val is not None]
            )
        )


class ArgumentSpecifiedError(LograderValidationError):
    """
    This is the exception that is raised when an argument is passed
    when it should not have been.
    """

    def __init__(self, conflicting_arg: str, **specified_args: Any):
        super().__init__(
            "Specified arguments, "
            + ", ".join(
                [
                    f"`{kw}` = {val}"
                    for kw, val in specified_args.items()
                    if val is not None
                ]
            )
            + f", that should have been left blank because argument, `{conflicting_arg}`, was specified."
        )
