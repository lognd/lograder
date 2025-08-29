from .formatters.assignment import (
    AssignmentInfoFormatter,
    AssignmentErrorFormatter,
    AssignmentStatsFormatter
)
from .formatters.test_case import (
    StatusFormatter,
    StreamFormatter,
    ReprFormatter
)

class AssignmentLogger:
    _preprocessor_error_fmt = AssignmentErrorFormatter()
    _preprocessor_info_fmt = AssignmentInfoFormatter()
    _builder_error_fmt = AssignmentErrorFormatter()
    _builder_info_fmt = AssignmentInfoFormatter()
    _runtime_summary_fmt = AssignmentStatsFormatter()

class TestCaseLogger:
    _status_fmt = StatusFormatter()
    _stdin_fmt = StreamFormatter()
    _exp_stdout_fmt = StreamFormatter()
    _act_stdout_fmt = StreamFormatter()
    _exp_stdout_str_fmt = ReprFormatter()
    _act_stdout_str_fmt = ReprFormatter()
    _stderr_fmt = StreamFormatter()
