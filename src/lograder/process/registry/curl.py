from pathlib import Path
from typing import Any

from lograder.process.cli_args import CLIArgs, CLIOption, CLIPresenceFlag
from lograder.process.executable import TypedExecutable, register_typed_executable


class CURLArgs(CLIArgs):
    url: str = CLIOption(emit=["{}"])
    output: Path = CLIOption(emit=["-o", "{}"])

    response_headers_only: bool = CLIPresenceFlag(emit=["-I"], default=False)
    follow_redirects: bool = CLIPresenceFlag(emit=["-L"], default=False)

    data: dict[str, Any] = CLIOption(
        emitter=lambda d: (
            ["-d", "&".join(f"{k}={str(v)}" for k, v in d.items())] if d else []
        ),
        default_factory=dict,
    )
    headers: dict[str, Any] = CLIOption(
        emitter=lambda d: (
            ["-H", "\n\r".join(f"{k}: {str(v)}" for k, v in d.items())] if d else []
        ),
        default_factory=dict,
    )


@register_typed_executable(["curl"])
class CURLExecutable(TypedExecutable[CURLArgs]): ...
