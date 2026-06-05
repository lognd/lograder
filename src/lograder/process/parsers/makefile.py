"""
Makefile parser for artifact discovery.

Handles:
- Variable assignments (=, :=, ::=, ?=, !=, +=, define...endef)
- Explicit rules (target: deps)
- Pattern rules (%.o: %.c, %.o: %.cpp)
- .PHONY and other special targets
- Basic function expansion (patsubst, addprefix, addsuffix, filter, sort, ...)
- Line continuations and inline comments
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class MakefileRule:
    targets: list[str]
    prerequisites: list[str]
    is_pattern: bool = False  # any target contains %


@dataclass
class ParsedMakefile:
    variables: dict[str, str] = field(default_factory=dict)
    rules: list[MakefileRule] = field(default_factory=list)
    phony: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Variable expansion
# ---------------------------------------------------------------------------


def _match_pattern(pattern: str, word: str) -> str | None:
    """
    Return the stem if *word* matches *pattern* (which may contain one %), else None.

    For patterns without %, returns "" on exact equality (no stem concept).
    For patterns with %, returns the matched stem string (may be "").
    """
    if "%" not in pattern:
        return "" if word == pattern else None
    prefix, suffix = pattern.split("%", 1)
    if len(word) < len(prefix) + len(suffix):
        return None
    if not word.startswith(prefix):
        return None
    if suffix and not word.endswith(suffix):
        return None
    return word[len(prefix) : len(word) - len(suffix) if suffix else None]


def _find_close(s: str, start: int, close: str) -> int:
    """Find the index of the matching close delimiter, handling nesting."""
    open_ch = "(" if close == ")" else "{"
    depth = 1
    i = start
    while i < len(s):
        if s[i] == open_ch:
            depth += 1
        elif s[i] == close:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _eval_ref(inner: str, variables: dict[str, str]) -> str:
    """Evaluate an already-expanded variable reference body."""
    inner = inner.strip()
    # Check for make function (first word before space/newline)
    sep = -1
    for i, ch in enumerate(inner):
        if ch in (" ", "\t", "\n"):
            sep = i
            break
    if sep >= 0:
        func = inner[:sep].strip()
        args = inner[sep + 1 :]
        try:
            return _expand_func(func, args, variables)
        except Exception:
            return ""
    return variables.get(inner, "")


def _expand_vars(value: str, variables: dict[str, str], depth: int = 0) -> str:
    """
    Expand make variable references, handling nested $(...) and ${...}.

    Leaves automatic variables ($@, $<, $^, ...) unexpanded.
    """
    if depth > 8 or "$" not in value:
        return value

    result: list[str] = []
    i = 0
    n = len(value)
    while i < n:
        if value[i] != "$":
            result.append(value[i])
            i += 1
            continue

        if i + 1 >= n:
            result.append("$")
            i += 1
            continue

        next_ch = value[i + 1]
        if next_ch == "(":
            close_idx = _find_close(value, i + 2, ")")
            if close_idx < 0:
                # Unclosed — emit literally
                result.append(value[i])
                i += 1
                continue
            inner = value[i + 2 : close_idx]
            inner = _expand_vars(inner, variables, depth + 1)
            result.append(_eval_ref(inner, variables))
            i = close_idx + 1
        elif next_ch == "{":
            close_idx = _find_close(value, i + 2, "}")
            if close_idx < 0:
                result.append(value[i])
                i += 1
                continue
            inner = value[i + 2 : close_idx]
            inner = _expand_vars(inner, variables, depth + 1)
            result.append(_eval_ref(inner, variables))
            i = close_idx + 1
        else:
            # Single-char automatic variable — leave unexpanded
            result.append(value[i : i + 2])
            i += 2

    return "".join(result)


def _expand_func(func: str, args: str, variables: dict[str, str]) -> str:
    """Expand a single make function call. Returns '' on parse failure."""
    try:
        if func == "patsubst":
            pattern, replacement, text = (a.strip() for a in args.split(",", 2))
            result = []
            for word in text.split():
                stem = _match_pattern(pattern, word)
                if stem is not None:
                    result.append(replacement.replace("%", stem))
                else:
                    result.append(word)
            return " ".join(result)

        if func == "subst":
            from_, to, text = (a.strip() for a in args.split(",", 2))
            return text.replace(from_, to)

        if func == "addprefix":
            prefix, words = (a.strip() for a in args.split(",", 1))
            return " ".join(prefix + w for w in words.split())

        if func == "addsuffix":
            suffix, words = (a.strip() for a in args.split(",", 1))
            return " ".join(w + suffix for w in words.split())

        if func == "notdir":
            return " ".join(Path(w).name for w in args.split())

        if func == "dir":
            return " ".join(str(Path(w).parent) + "/" for w in args.split())

        if func == "basename":
            return " ".join(str(Path(w).with_suffix("")) for w in args.split())

        if func == "suffix":
            return " ".join(Path(w).suffix for w in args.split())

        if func == "sort":
            return " ".join(sorted(set(args.split())))

        if func == "strip":
            return args.strip()

        if func == "filter":
            patterns_str, words_str = (a.strip() for a in args.split(",", 1))
            pats = patterns_str.split()
            result = []
            for w in words_str.split():
                for p in pats:
                    if _match_pattern(p, w) is not None:
                        result.append(w)
                        break
            return " ".join(result)

        if func == "filter-out":
            patterns_str, words_str = (a.strip() for a in args.split(",", 1))
            pats = patterns_str.split()
            result = []
            for w in words_str.split():
                if all(_match_pattern(p, w) is None for p in pats):
                    result.append(w)
            return " ".join(result)

        if func == "join":
            list1, list2 = (a.strip() for a in args.split(",", 1))
            pairs = list(zip(list1.split(), list2.split()))
            return " ".join(a + b for a, b in pairs)

        if func == "wildcard":
            # Can't expand without filesystem access at parse time
            return ""

        if func in ("shell", "eval", "call", "value", "origin", "flavor"):
            return ""

        # Unknown — try simple variable lookup
        return variables.get(func, "")

    except (ValueError, IndexError):
        return ""


# ---------------------------------------------------------------------------
# Line preprocessing
# ---------------------------------------------------------------------------


def _join_continuations(text: str) -> list[str]:
    """
    Join backslash-continued lines into logical lines.
    Returns a list where each element is one logical line, still with
    its leading whitespace intact so we can detect recipe lines (tab-indented).
    """
    lines: list[str] = []
    buf: str = ""
    continuation: bool = False

    for raw in text.splitlines():
        if raw.endswith("\\"):
            if continuation:
                buf += raw[:-1] + " "
            else:
                continuation = True
                buf = raw[:-1] + " "
        else:
            if continuation:
                buf += raw
                lines.append(buf)
                buf = ""
                continuation = False
            else:
                lines.append(raw)

    if buf:
        lines.append(buf)

    return lines


def _strip_comment(line: str) -> str:
    """Remove inline # comment, but not escaped \\#."""
    result = []
    i = 0
    while i < len(line):
        if line[i] == "#" and (i == 0 or line[i - 1] != "\\"):
            break
        result.append(line[i])
        i += 1
    return "".join(result)


# ---------------------------------------------------------------------------
# Assignment detection
# ---------------------------------------------------------------------------


def _looks_like_varname(s: str) -> bool:
    """Simple check: make variable names don't contain spaces."""
    s = s.strip()
    if not s:
        return False
    return " " not in s and "\t" not in s and ":" not in s and "%" not in s


def _find_bare_colon(line: str) -> int:
    """
    Find the index of the first colon that is NOT part of := or ::=.
    Returns -1 if not found.
    """
    i = 0
    while i < len(line):
        if line[i] == ":":
            # Skip :: (double-colon rule separator or ::= operator)
            if i + 1 < len(line) and line[i + 1] == ":":
                # Could be ::= (assignment) or :: (double-colon rule)
                if i + 2 < len(line) and line[i + 2] == "=":
                    i += 3
                    continue
                # Double-colon rule: treat this first : as the separator
                return i
            # Skip :=
            if i + 1 < len(line) and line[i + 1] == "=":
                i += 2
                continue
            return i
        i += 1
    return -1


def _try_assignment(line: str) -> tuple[str, str, str] | None:
    """
    If *line* is a variable assignment, return (name, op, raw_value).
    Returns None if it looks like a rule.
    """
    # Compound operators take precedence
    for op in ("::=", ":=", "?=", "!=", "+="):
        idx = line.find(op)
        if idx >= 0:
            name = line[:idx].strip()
            val = line[idx + len(op) :].strip()
            if _looks_like_varname(name):
                return (name, op, val)

    # Bare =: must appear before any bare colon (otherwise it's a rule with = in deps)
    eq_idx = line.find("=")
    colon_idx = _find_bare_colon(line)
    if eq_idx >= 0 and (colon_idx < 0 or eq_idx < colon_idx):
        name = line[:eq_idx].strip()
        if _looks_like_varname(name):
            return (name, "=", line[eq_idx + 1 :].strip())

    return None


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

# Special make targets to ignore
_SPECIAL_TARGETS = {
    ".PHONY",
    ".SUFFIXES",
    ".DEFAULT",
    ".PRECIOUS",
    ".INTERMEDIATE",
    ".SECONDARY",
    ".SECONDEXPANSION",
    ".DELETE_ON_ERROR",
    ".IGNORE",
    ".LOW_RESOLUTION_TIME",
    ".SILENT",
    ".EXPORT_ALL_VARIABLES",
    ".NOTPARALLEL",
    ".ONESHELL",
    ".POSIX",
}


def parse_makefile(path: Path) -> ParsedMakefile:
    """Parse *path* and return a `ParsedMakefile`."""
    text = path.read_text(errors="replace")
    logical_lines = _join_continuations(text)

    variables: dict[str, str] = {}
    rules: list[MakefileRule] = []
    phony: set[str] = set()

    in_define = False
    define_var = ""
    define_lines: list[str] = []

    for raw_line in logical_lines:
        # Recipe lines (tab-indented) — skip entirely
        if raw_line.startswith("\t"):
            continue

        stripped = _strip_comment(raw_line).strip()

        if not stripped:
            continue

        # define ... endef multi-line variable
        if in_define:
            if stripped == "endef":
                variables[define_var] = "\n".join(define_lines)
                in_define = False
                define_lines = []
            else:
                define_lines.append(raw_line)
            continue

        m_define = re.match(r"^define\s+(\S+)", stripped)
        if m_define:
            define_var = m_define.group(1)
            in_define = True
            continue

        # ifeq / ifdef / else / endif — skip (treat as transparent)
        if re.match(
            r"^(ifeq|ifneq|ifdef|ifndef|else|endif|include|-include)\b", stripped
        ):
            continue

        # Try variable assignment
        assignment = _try_assignment(stripped)
        if assignment is not None:
            name, op, raw_val = assignment
            expanded_val = _expand_vars(raw_val, variables)
            if op == "+=":
                existing = variables.get(name, "")
                variables[name] = (
                    (existing + " " + expanded_val).strip()
                    if existing
                    else expanded_val
                )
            elif op == "?=":
                if name not in variables:
                    variables[name] = expanded_val
            else:
                variables[name] = expanded_val
            continue

        # Try rule
        colon_idx = _find_bare_colon(stripped)
        if colon_idx < 0:
            continue

        raw_targets = _expand_vars(stripped[:colon_idx].strip(), variables)
        raw_rest = stripped[colon_idx + 1 :]

        # Double-colon rule: same semantics for our purposes
        if raw_rest.startswith(":"):
            raw_rest = raw_rest[1:]

        # Inline recipe after semicolon
        semi = raw_rest.find(";")
        if semi >= 0:
            raw_rest = raw_rest[:semi]

        raw_prereqs = _expand_vars(raw_rest.strip(), variables)

        targets = raw_targets.split()
        prereqs = raw_prereqs.split()

        if not targets:
            continue

        # .PHONY
        if ".PHONY" in targets:
            phony.update(prereqs)
            continue

        # Other special targets — register what they declare but don't add as rules
        if targets[0] in _SPECIAL_TARGETS:
            continue

        is_pattern = any("%" in t for t in targets)
        rules.append(
            MakefileRule(targets=targets, prerequisites=prereqs, is_pattern=is_pattern)
        )

    return ParsedMakefile(variables=variables, rules=rules, phony=phony)


# ---------------------------------------------------------------------------
# Artifact discovery
# ---------------------------------------------------------------------------


def artifacts_from_makefile(
    makefile_path: Path,
    source_files: list[Path],
) -> dict[str, Path]:
    """
    Parse *makefile_path* and return a mapping of ``target_name → expected_path``
    for all non-phony, non-special targets.

    Pattern rules (e.g. ``%.o: %.c``) are expanded against *source_files* —
    each source file whose name matches the prerequisite pattern produces one
    output artifact at the same directory level as the Makefile.

    The caller is responsible for filtering the returned dict to paths that
    actually exist after the build.
    """
    parsed = parse_makefile(makefile_path)
    base_dir = makefile_path.parent

    src_names = [f.name for f in source_files]
    result: dict[str, Path] = {}

    for rule in parsed.rules:
        for target in rule.targets:
            # Skip phony and special targets
            if target in parsed.phony or target in _SPECIAL_TARGETS:
                continue
            if target.startswith("."):
                continue

            if rule.is_pattern and "%" in target:
                # Expand against each source file that matches any prerequisite pattern
                for prereq in rule.prerequisites:
                    if "%" not in prereq:
                        continue
                    for src_name in src_names:
                        stem = _match_pattern(prereq, src_name)
                        if stem is not None:
                            expanded = target.replace("%", stem)
                            candidate = base_dir / expanded
                            # Use expanded name as key; don't overwrite if already found
                            if expanded not in result:
                                result[expanded] = candidate
            else:
                # Explicit target — may contain path separators
                candidate = (base_dir / target).resolve()
                key = Path(target).name if "/" in target or "\\" in target else target
                if key not in result:
                    result[key] = candidate

    return result
