"""AST-based operator counting for C, C++, and Python source files.

C/C++ workflow: preprocess with cpp (via CPPExecutable), then parse the
expanded source with tree-sitter-cpp. Preprocessing resolves #define
shenanigans before the AST is built.

Python workflow: parse directly with tree-sitter-python.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from pydantic import BaseModel

from lograder.common import Err, Ok, Result
from lograder.process.executable import ExecutableOptions
from lograder.process.os_helpers import StreamMode


# ---------------------------------------------------------------------------
# Structured error type
# ---------------------------------------------------------------------------

class PreprocessError(BaseModel):
    """Describes a failed C/C++ preprocessing attempt."""
    path: Path
    tried: list[str]              # tools attempted in order
    return_code: int | None       # exit code of the last tool that ran, if any
    stderr: str | None            # stderr of the last tool that ran, if any
    exception: str | None         # str(exc) if a Python exception occurred

    @property
    def message(self) -> str:
        parts = [f"Preprocessing '{self.path}' failed (tried: {', '.join(self.tried)})."]
        if self.exception:
            parts.append(f"Exception: {self.exception}")
        if self.return_code is not None:
            parts.append(f"Exit code: {self.return_code}.")
        if self.stderr:
            parts.append(f"Stderr:\n{self.stderr}")
        return " ".join(parts)


# ---------------------------------------------------------------------------
# tree-sitter language objects (imported lazily)
# ---------------------------------------------------------------------------

def _cpp_language():  # type: ignore[return]
    import tree_sitter_cpp as tscpp
    from tree_sitter import Language
    return Language(tscpp.language())


def _python_language():  # type: ignore[return]
    import tree_sitter_python as tspy
    from tree_sitter import Language
    return Language(tspy.language())


# ---------------------------------------------------------------------------
# Node types carrying an "operator" named field in each grammar
# ---------------------------------------------------------------------------

_CPP_OP_NODES = frozenset({
    "binary_expression",
    "assignment_expression",
    "unary_expression",
    "update_expression",
    "pointer_expression",
})

_PY_OP_NODES = frozenset({
    "binary_operator",
    "augmented_assignment",
    "unary_operator",
    "boolean_operator",
})


# ---------------------------------------------------------------------------
# Tree-walking
# ---------------------------------------------------------------------------

def _collect_operators(node, node_types: frozenset[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    stack = [node]
    while stack:
        n = stack.pop()
        if n.type in node_types:
            op = n.child_by_field_name("operator")
            if op is not None and op.text:
                counts[op.text.decode("utf-8", errors="replace")] += 1
        elif n.type == "comparison_operator":
            # Python: comparison operators are anonymous children
            for child in n.children:
                if not child.is_named and child.text:
                    counts[child.text.decode("utf-8", errors="replace")] += 1
        stack.extend(reversed(n.children))
    return counts


# ---------------------------------------------------------------------------
# C preprocessor (with structured fallback chain)
# ---------------------------------------------------------------------------

def _preprocess(path: Path, include_dirs: list[Path]) -> Result[str, PreprocessError]:
    tried: list[str] = []
    last_rc: int | None = None
    last_stderr: str | None = None
    last_exc: str | None = None

    # --- attempt 1: standalone cpp ---
    try:
        from lograder.process.registry.cpp import CPPArgs, CPPExecutable
        cpp_exe = CPPExecutable()
        tried.append("cpp")
        if cpp_exe.check_runnable().is_ok:
            res = cpp_exe(
                CPPArgs(
                    input=path,
                    suppress_line_markers=True,
                    include_dirs=include_dirs,
                    suppress_warnings=True,
                ),
                options=ExecutableOptions(
                    stdout_mode=StreamMode.PIPE,
                    stderr_mode=StreamMode.PIPE,
                    timeout=30.0,
                ),
            )
            if res.is_ok:
                out = res.danger_ok
                last_rc = out.return_code
                last_stderr = out.stderr_text.strip() or None
                if out.return_code == 0:
                    return Ok(out.stdout_text)
            else:
                last_exc = res.danger_err.message
    except Exception as exc:
        last_exc = str(exc)

    # --- attempt 2: clang++ -E -P ---
    try:
        from lograder.process.registry.clang import ClangXXArgs, ClangXXExecutable
        clang_exe = ClangXXExecutable()
        tried.append("clang++")
        if clang_exe.check_runnable().is_ok:
            res = clang_exe(
                ClangXXArgs(
                    input=[path],
                    preprocess_only=True,
                    add_opts=["-P", "-w"],
                    include_dirs=list(include_dirs),
                    warnings_all=False,
                    warnings_extra=False,
                ),
                options=ExecutableOptions(timeout=30.0),
            )
            if res.is_ok:
                out = res.danger_ok
                last_rc = out.return_code
                last_stderr = out.stderr_text.strip() or None
                if out.return_code == 0:
                    return Ok(out.stdout_text)
            else:
                last_exc = res.danger_err.message
    except Exception as exc:
        last_exc = str(exc)

    # --- attempt 3: naive #define expansion (no subprocess) ---
    tried.append("naive-expand")
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        return Ok(_naive_expand(source))
    except OSError as exc:
        last_exc = str(exc)
        return Err(PreprocessError(
            path=path,
            tried=tried,
            return_code=last_rc,
            stderr=last_stderr,
            exception=last_exc,
        ))


def _naive_expand(source: str) -> str:
    """Object-like #define substitution; handles the most common evasion pattern."""
    import re
    defines: dict[str, str] = {}
    kept: list[str] = []
    for line in source.splitlines():
        s = line.strip()
        m = re.match(r"#\s*define\s+(\w+)\s*(.*)", s)
        # Skip function-like macros (name immediately followed by '(')
        if m and not re.match(r"#\s*define\s+\w+\s*\(", s):
            defines[m.group(1)] = m.group(2).strip()
        elif not s.startswith("#"):
            kept.append(line)
    text = "\n".join(kept)
    if not defines:
        return text
    pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in defines) + r")\b")
    for _ in range(10):
        next_text = pattern.sub(lambda m: defines[m.group(0)], text)
        if next_text == text:
            break
        text = next_text
    return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def count_operators_cpp(
    path: Path,
    include_dirs: list[Path] | None = None,
) -> Result[Counter[str], PreprocessError]:
    """Preprocess then AST-parse a C/C++ file; return operator token counts."""
    preprocess_result = _preprocess(path, include_dirs or [])
    if preprocess_result.is_err:
        return preprocess_result  # type: ignore[return-value]
    source = preprocess_result.danger_ok

    from tree_sitter import Parser
    parser = Parser(_cpp_language())
    tree = parser.parse(source.encode("utf-8", errors="replace"))
    return Ok(_collect_operators(tree.root_node, _CPP_OP_NODES))


def count_operators_python(path: Path) -> Result[Counter[str], OSError]:
    """AST-parse a Python file; return operator token counts."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return Err(exc)

    from tree_sitter import Parser
    parser = Parser(_python_language())
    tree = parser.parse(source.encode("utf-8", errors="replace"))
    return Ok(_collect_operators(tree.root_node, _PY_OP_NODES))
