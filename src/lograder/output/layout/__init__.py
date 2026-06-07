import lograder.output.layout.check.source  # noqa: F401

# Import all layout modules so their @register_layout decorators run automatically.
# Pipeline authors never need to import layout modules manually; any code that does
# `from lograder.output.layout import ...` gets all registrations for free.
import lograder.output.layout.exception  # noqa: F401
import lograder.output.layout.pipeline.bash_script  # noqa: F401
import lograder.output.layout.pipeline.build  # noqa: F401
import lograder.output.layout.pipeline.mixin  # noqa: F401
import lograder.output.layout.pipeline.prebuilt  # noqa: F401
import lograder.output.layout.process.executable  # noqa: F401
import lograder.output.layout.project.manifest  # noqa: F401
import lograder.output.layout.project.simple_project  # noqa: F401
import lograder.output.layout.test.catch2  # noqa: F401
import lograder.output.layout.test.ctest  # noqa: F401
import lograder.output.layout.test.differential  # noqa: F401
import lograder.output.layout.test.file_output  # noqa: F401
import lograder.output.layout.test.gtest  # noqa: F401
import lograder.output.layout.test.output_compare  # noqa: F401
import lograder.output.layout.test.performance  # noqa: F401
import lograder.output.layout.test.pytest  # noqa: F401
import lograder.output.layout.test.symbol  # noqa: F401
import lograder.output.layout.test.valgrind  # noqa: F401
from lograder.output.layout.layout import (
    Layout,
    SupportedFormat,
    dispatch_layout,
    register_layout,
)

__all__ = ["dispatch_layout", "Layout", "register_layout", "SupportedFormat"]
