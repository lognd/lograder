"""Parser for `nm` output (BSD format, the default)."""

from __future__ import annotations

import re
from dataclasses import dataclass

# BSD format line: [<address>] <type> <name>
# Address is absent for undefined symbols.
_BSD_LINE = re.compile(
    r"^(?:(?P<address>[0-9a-fA-F]+)\s+)?(?P<type>[A-Za-z?])\s+(?P<name>\S+)$"
)


@dataclass(frozen=True)
class NmSymbol:
    name: str
    type: str  # single letter per nm convention (T, U, D, B, W, ...)
    address: int | None

    @property
    def is_defined(self) -> bool:
        return self.type.upper() != "U"

    @property
    def is_external(self) -> bool:
        return self.type.isupper()

    @property
    def is_text(self) -> bool:
        return self.type.upper() == "T"


def parse_nm_output(output: str) -> list[NmSymbol]:
    """Parse BSD-format nm output into a list of NmSymbol instances.

    Lines that do not match the expected format (e.g. archive member headers,
    blank lines) are silently skipped.
    """
    symbols: list[NmSymbol] = []
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Skip archive member banners like "libfoo.a[foo.o]:"
        if line.endswith(":") and not re.match(r"[0-9a-fA-F]", line):
            continue
        m = _BSD_LINE.match(line)
        if not m:
            continue
        addr_str = m.group("address")
        symbols.append(
            NmSymbol(
                name=m.group("name"),
                type=m.group("type"),
                address=int(addr_str, 16) if addr_str else None,
            )
        )
    return symbols
