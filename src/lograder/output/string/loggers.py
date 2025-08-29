from .formatters.assignment import (
    AssignmentStatsFormatter,
    BuildErrorFormatter,
    BuildInfoFormatter,
    PreprocessorErrorFormatter,
    PreprocessorInfoFormatter,
)
from .formatters.test_case import (
    ActualSTDOUTFormatter,
    ExpectedSTDOUTFormatter,
    ReprFormatter,
    StatusFormatter,
    STDERRFormatter,
    STDINFormatter,
)


class AssignmentLogger:
    _preprocessor_error_fmt = PreprocessorErrorFormatter()
    _preprocessor_info_fmt = PreprocessorInfoFormatter()
    _builder_error_fmt = BuildErrorFormatter()
    _builder_info_fmt = BuildInfoFormatter()
    _runtime_summary_fmt = AssignmentStatsFormatter()


class TestCaseLogger:
    _status_fmt = StatusFormatter()
    _stdin_fmt = STDINFormatter()
    _exp_stdout_fmt = ExpectedSTDOUTFormatter()
    _act_stdout_fmt = ActualSTDOUTFormatter()
    _exp_stdout_str_fmt = ReprFormatter()
    _act_stdout_str_fmt = ReprFormatter()
    _stderr_fmt = STDERRFormatter()
