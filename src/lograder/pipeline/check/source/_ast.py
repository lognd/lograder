"""AST-based source analysis for C, C++, and Python.

C/C++ workflow
--------------
1. Preprocess with cpp/g++/clang++ to resolve #define aliasing.
2. Parse preprocessed source -> operators, identifiers, qualified names.
3. Parse original source -> #include directives (erased by preprocessor).

Python workflow
---------------
Parse source directly -> operators, identifiers, import statements.

The common DFS walk (operators via 'operator' field + comparison nodes,
identifiers by node type) lives in ``_Walker``; language subclasses add
their own extras via ``_handle_extra``.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import tree_sitter_cpp as tscpp
import tree_sitter_python as tspy
from pydantic import BaseModel
from tree_sitter import Language, Node, Parser

from lograder.common import Err, Ok, Result
from lograder.process.executable import ExecutableOptions
from lograder.process.os_helpers import StreamMode
from lograder.process.registry.clang import ClangXXArgs, ClangXXExecutable
from lograder.process.registry.cpp import CPPArgs, CPPExecutable

_CPP_LANGUAGE = Language(tscpp.language())
_PY_LANGUAGE = Language(tspy.language())


# ---------------------------------------------------------------------------
# Structured error
# ---------------------------------------------------------------------------


class PreprocessError(BaseModel):
    path: Path
    tried: list[str]
    return_code: int | None
    stderr: str | None
    exception: str | None

    @property
    def message(self) -> str:
        parts = [
            f"Preprocessing '{self.path}' failed (tried: {', '.join(self.tried)})."
        ]
        if self.exception:
            parts.append(f"Exception: {self.exception}")
        if self.return_code is not None:
            parts.append(f"Exit {self.return_code}.")
        if self.stderr:
            parts.append(f"Stderr: {self.stderr}")
        return " ".join(parts)


# ---------------------------------------------------------------------------
# Generic tree walker
# ---------------------------------------------------------------------------


class _Walker:
    """DFS tree walker; collects operators and identifiers for any language.

    Subclasses set ``op_node_types`` / ``identifier_node_types`` and may
    override ``_handle_extra`` to collect language-specific data.
    """

    op_node_types: frozenset[str] = frozenset()
    identifier_node_types: frozenset[str] = frozenset()

    def __init__(self) -> None:
        self.operators: Counter[str] = Counter()
        self.identifiers: Counter[str] = Counter()

    def _handle_extra(self, node: Node) -> None:  # noqa: B027 (intentional no-op)
        pass

    def walk(self, root_node: Node) -> None:
        stack: list[Node] = [root_node]
        while stack:
            n = stack.pop()

            # Operators carried in a named 'operator' field
            if n.type in self.op_node_types:
                op = n.child_by_field_name("operator")
                if op is not None and op.text:
                    self.operators[op.text.decode("utf-8", errors="replace")] += 1

            # Comparison operators are anonymous inline tokens
            elif n.type == "comparison_operator":
                for child in n.children:
                    if not child.is_named and child.text:
                        self.operators[
                            child.text.decode("utf-8", errors="replace")
                        ] += 1

            if n.type in self.identifier_node_types and n.text:
                self.identifiers[n.text.decode("utf-8", errors="replace")] += 1

            self._handle_extra(n)
            stack.extend(reversed(n.children))


# ---------------------------------------------------------------------------
# C/C++ walkers
# ---------------------------------------------------------------------------


def _qualified_name_text(node: Node) -> str:
    """Recursively reconstruct the full text of a qualified_identifier node."""
    if node.type == "qualified_identifier":
        scope = node.child_by_field_name("scope")
        name_node = node.child_by_field_name("name")
        # Unwrap template_type to get its name field (e.g. vector in vector<int>)
        if name_node is not None and name_node.type == "template_type":
            name_node = name_node.child_by_field_name("name") or name_node
        scope_str = _qualified_name_text(scope) if scope is not None else ""
        name_str = (
            name_node.text.decode("utf-8", errors="replace")
            if name_node is not None and name_node.text
            else ""
        )
        return f"{scope_str}::{name_str}" if scope_str else name_str
    return node.text.decode("utf-8", errors="replace") if node.text else ""


class _CppWalker(_Walker):
    op_node_types = frozenset(
        {
            "binary_expression",
            "assignment_expression",
            "unary_expression",
            "update_expression",
            "pointer_expression",
        }
    )
    identifier_node_types = frozenset({"identifier", "type_identifier"})

    def __init__(self) -> None:
        super().__init__()
        self.qualified_names: Counter[str] = Counter()

    def _handle_extra(self, node: Node) -> None:
        if node.type == "qualified_identifier":
            qname = _qualified_name_text(node)
            if qname:
                self.qualified_names[qname] += 1


class _CppIncludeWalker:
    """Separate walker for the original (unpreprocessed) source to find #include directives."""

    def __init__(self) -> None:
        self.includes: Counter[str] = Counter()

    def walk(self, root_node: Node) -> None:
        stack: list[Node] = [root_node]
        while stack:
            n = stack.pop()
            if n.type == "preproc_include":
                path_node = n.child_by_field_name("path")
                if path_node is not None and path_node.text:
                    self.includes[path_node.text.decode("utf-8", errors="replace")] += 1
            stack.extend(reversed(n.children))


# ---------------------------------------------------------------------------
# Python walker
# ---------------------------------------------------------------------------


class _PythonWalker(_Walker):
    op_node_types = frozenset(
        {
            "binary_operator",
            "augmented_assignment",
            "unary_operator",
            "boolean_operator",
        }
    )
    identifier_node_types = frozenset({"identifier"})

    def __init__(self) -> None:
        super().__init__()
        self.imports: Counter[str] = Counter()

    def _handle_extra(self, node: Node) -> None:
        if node.type == "import_statement":
            for child in node.named_children:
                raw = self._dotted_name_from(child)
                if raw:
                    self._record_import(raw)
        elif node.type == "import_from_statement":
            m = node.child_by_field_name("module_name")
            if m is not None and m.text:
                self._record_import(m.text.decode("utf-8", errors="replace"))

    @staticmethod
    def _dotted_name_from(node: Node) -> str:
        if node.type == "dotted_name" and node.text:
            return node.text.decode("utf-8", errors="replace")
        if node.type == "aliased_import":
            name = node.child_by_field_name("name")
            if name is not None and name.text:
                return name.text.decode("utf-8", errors="replace")
        return ""

    def _record_import(self, raw: str) -> None:
        self.imports[raw] += 1
        top = raw.split(".")[0]
        if top != raw:
            self.imports[top] += 1


# ---------------------------------------------------------------------------
# Preprocessing chain
# ---------------------------------------------------------------------------


def _preprocess(path: Path, include_dirs: list[Path]) -> Result[str, PreprocessError]:
    tried: list[str] = []
    last_rc: int | None = None
    last_stderr: str | None = None
    last_exc: str | None = None

    # --- attempt 1: standalone cpp ---
    try:
        tried.append("cpp")
        cpp_exe = CPPExecutable()
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
                last_rc, last_stderr = out.return_code, out.stderr_text.strip() or None
                if out.return_code == 0:
                    return Ok(out.stdout_text)
            else:
                last_exc = res.danger_err.message
    except Exception as exc:
        last_exc = str(exc)

    # --- attempt 2: clang++ -E -P ---
    try:
        tried.append("clang++")
        clang_exe = ClangXXExecutable()
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
                last_rc, last_stderr = out.return_code, out.stderr_text.strip() or None
                if out.return_code == 0:
                    return Ok(out.stdout_text)
            else:
                last_exc = res.danger_err.message
    except Exception as exc:
        last_exc = str(exc)

    # --- attempt 3: naive #define expansion (no subprocess) ---
    tried.append("naive-expand")
    try:
        return Ok(_naive_expand(path.read_text(encoding="utf-8", errors="replace")))
    except OSError as exc:
        last_exc = str(exc)
        return Err(
            PreprocessError(
                path=path,
                tried=tried,
                return_code=last_rc,
                stderr=last_stderr,
                exception=last_exc,
            )
        )


def _naive_expand(source: str) -> str:
    """Object-like #define expansion; catches the most common operator aliasing."""
    defines: dict[str, str] = {}
    kept: list[str] = []
    for line in source.splitlines():
        s = line.strip()
        m = re.match(r"#\s*define\s+(\w+)\s*(.*)", s)
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
# Public API  -  result models
# ---------------------------------------------------------------------------


class CppAnalysis(BaseModel):
    operators: Counter[str]
    identifiers: Counter[str]
    qualified_names: Counter[str]
    includes: Counter[str]

    model_config = {"arbitrary_types_allowed": True}


class PythonAnalysis(BaseModel):
    operators: Counter[str]
    identifiers: Counter[str]
    imports: Counter[str]

    model_config = {"arbitrary_types_allowed": True}


# ---------------------------------------------------------------------------
# Public API  -  analysis functions
# ---------------------------------------------------------------------------


def analyze_cpp(
    path: Path,
    include_dirs: list[Path] | None = None,
) -> Result[CppAnalysis, PreprocessError]:
    """Preprocess then AST-analyse a C/C++ file."""
    preprocess_result = _preprocess(path, include_dirs or [])
    if preprocess_result.is_err:
        return preprocess_result  # type: ignore[return-value]

    cpp_parser = Parser(_CPP_LANGUAGE)

    walker = _CppWalker()
    walker.walk(
        cpp_parser.parse(
            preprocess_result.danger_ok.encode("utf-8", errors="replace")
        ).root_node
    )

    include_walker = _CppIncludeWalker()
    try:
        original = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return Err(
            PreprocessError(
                path=path,
                tried=["file-read"],
                return_code=None,
                stderr=None,
                exception=str(exc),
            )
        )
    include_walker.walk(
        cpp_parser.parse(original.encode("utf-8", errors="replace")).root_node
    )

    return Ok(
        CppAnalysis(
            operators=walker.operators,
            identifiers=walker.identifiers,
            qualified_names=walker.qualified_names,
            includes=include_walker.includes,
        )
    )


def analyze_python(path: Path) -> Result[PythonAnalysis, OSError]:
    """AST-analyse a Python file."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return Err(exc)

    walker = _PythonWalker()
    walker.walk(
        Parser(_PY_LANGUAGE).parse(source.encode("utf-8", errors="replace")).root_node
    )
    return Ok(
        PythonAnalysis(
            operators=walker.operators,
            identifiers=walker.identifiers,
            imports=walker.imports,
        )
    )
