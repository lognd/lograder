from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import Enum
from pathlib import Path
from typing import Any, Callable, ClassVar, Literal

from pydantic import BaseModel, Field

CLIHookResult = list[str] | None
CLIHook = Callable[
    ["CLIArgs", str, Any, Mapping[str, Any], str],
    CLIHookResult,
]


class CLIArgs(BaseModel):
    _default_prefix: ClassVar[str] = "--"
    _default_kebab_case: ClassVar[bool] = False
    _default_repeat_iterables: ClassVar[bool] = True
    _default_bool_style: ClassVar[Literal["presence", "explicit"]] = "presence"
    _default_join_style: ClassVar[Literal["separate", "equals"]] = "separate"

    # Ordered hook pipeline. First non-None result wins.
    _emit_hooks: ClassVar[list[CLIHook]] = []

    def to_arguments(self) -> list[str]:
        args: list[str] = []

        for name, field in self.__class__.model_fields.items():
            value = getattr(self, name)

            if value is None:
                continue

            cli_meta = (field.json_schema_extra or {}).get("cli", {})

            if cli_meta.get("exclude", False):
                continue

            if cli_meta.get("positional", False):
                args.extend(self._flatten_value(value, cli_meta))
                continue

            flag = self._field_flag(name, field, cli_meta)
            args.extend(self._emit_option(name, flag, value, cli_meta))

        return args

    def _field_flag(self, name: str, field: Any, cli_meta: Mapping[str, Any]) -> str:
        explicit = cli_meta.get("flag")
        if explicit:
            return str(explicit)

        raw = field.serialization_alias or field.alias or name
        if not raw.startswith("-"):
            raw = raw.replace("_", "-")
            raw = f"{self._default_prefix}{raw}"
        return raw

    def _emit_option(
        self,
        name: str,
        flag: str,
        value: Any,
        cli_meta: Mapping[str, Any],
    ) -> list[str]:
        # Hook pipeline first.
        for hook in self._iter_emit_hooks():
            result = hook(self, name, value, cli_meta, flag)
            if result is not None:
                return result

        if isinstance(value, bool):
            return self._emit_bool(flag, value, cli_meta)

        if self._is_flattenable_iterable(value):
            return self._emit_iterable(flag, value, cli_meta)

        return self._emit_scalar(flag, value, cli_meta)

    @classmethod
    def _iter_emit_hooks(cls) -> Iterable[CLIHook]:
        # Subclasses can extend _emit_hooks; walk MRO so base hooks still apply.
        hooks: list[CLIHook] = []
        for typ in reversed(cls.__mro__):
            class_hooks = getattr(typ, "_emit_hooks", None)
            if class_hooks:
                hooks.extend(class_hooks)
        return hooks

    def _emit_scalar(
        self,
        flag: str,
        value: Any,
        cli_meta: Mapping[str, Any],
    ) -> list[str]:
        rendered = self._render_scalar(value)
        join_style = cli_meta.get("join", self._default_join_style)
        compact = bool(cli_meta.get("compact", False))

        if compact:
            return [f"{flag}{rendered}"]

        if join_style == "equals":
            return [f"{flag}={rendered}"]

        return [flag, rendered]

    def _emit_bool(
        self, flag: str, value: bool, cli_meta: Mapping[str, Any]
    ) -> list[str]:
        style = cli_meta.get("bool_style", self._default_bool_style)

        if style == "explicit":
            true_value = str(cli_meta.get("true_value", "true"))
            false_value = str(cli_meta.get("false_value", "false"))
            compact = bool(cli_meta.get("compact", False))

            chosen = true_value if value else false_value
            if compact:
                return [f"{flag}{chosen}"]
            return [flag, chosen]

        if style == "presence":
            if value:
                return [flag]
            false_flag = cli_meta.get("false_flag")
            return [str(false_flag)] if false_flag else []

        raise ValueError(f"Unsupported bool style: {style!r}")

    def _emit_iterable(
        self, flag: str, value: Iterable[Any], cli_meta: Mapping[str, Any]
    ) -> list[str]:
        items = self._flatten_value(value, cli_meta)
        if not items:
            return []

        repeat = cli_meta.get("repeat", self._default_repeat_iterables)
        join_style = cli_meta.get("join", self._default_join_style)
        compact = bool(cli_meta.get("compact", False))

        if repeat:
            if compact:
                return [f"{flag}{item}" for item in items]
            if join_style == "equals":
                return [f"{flag}={item}" for item in items]

            out: list[str] = []
            for item in items:
                out.extend([flag, item])
            return out

        return [flag, *items]

    def _flatten_value(self, value: Any, cli_meta: Mapping[str, Any]) -> list[str]:
        if isinstance(value, (str, Path, Enum)):
            return [self._render_scalar(value)]

        if isinstance(value, bytes):
            return [value.decode()]

        if isinstance(value, BaseModel):
            if isinstance(value, CLIArgs):
                return value.to_arguments()
            raise TypeError(
                f"Nested BaseModel {type(value).__name__} must inherit from CLIArgs"
            )

        if isinstance(value, Mapping):
            mapping_mode = cli_meta.get("mapping", "key_value")
            sep = str(cli_meta.get("kv_sep", "="))

            if mapping_mode == "key_value":
                return [
                    f"{self._render_scalar(k)}{sep}{self._render_scalar(v)}"
                    for k, v in value.items()
                ]

            raise ValueError(f"Unsupported mapping mode: {mapping_mode!r}")

        if self._is_flattenable_iterable(value):
            out: list[str] = []
            for item in value:
                out.extend(self._flatten_value(item, cli_meta))
            return out

        return [self._render_scalar(value)]

    @staticmethod
    def _is_flattenable_iterable(value: Any) -> bool:
        return isinstance(value, Iterable) and not isinstance(
            value, (str, bytes, bytearray, Path, Enum, BaseModel, Mapping)
        )

    @staticmethod
    def _render_scalar(value: Any) -> str:
        if isinstance(value, Enum):
            return str(value.value)
        if isinstance(value, Path):
            return str(value)
        return str(value)


# ---------- Reusable hooks ----------


def hook_joined_prefix(
    model: CLIArgs,
    name: str,
    value: Any,
    cli_meta: Mapping[str, Any],
    flag: str,
) -> CLIHookResult:
    """
    Supports:
      join="prefix"      -> ['-Wl,a,b']
      join="prefix_each" -> ['-Lfoo', '-Lbar']
    """
    join_mode = cli_meta.get("join")
    if join_mode not in {"prefix", "prefix_each"}:
        return None

    if isinstance(value, bool):
        if not value:
            false_flag = cli_meta.get("false_flag")
            return [str(false_flag)] if false_flag else []
        return [flag]

    items = model._flatten_value(value, cli_meta)
    if not items:
        return []

    if join_mode == "prefix":
        item_sep = str(cli_meta.get("item_sep", ","))
        return [f"{flag}{item_sep.join(items)}"]

    return [f"{flag}{item}" for item in items]


def hook_mapping_repeat_compact(
    model: CLIArgs,
    name: str,
    value: Any,
    cli_meta: Mapping[str, Any],
    flag: str,
) -> CLIHookResult:
    """
    Supports dicts like:
      {'A': 1, 'B': 2} with flag='-D', compact=True
      -> ['-DA=1', '-DB=2']
    Or non-compact:
      -> ['-D', 'A=1', '-D', 'B=2']
    """
    if not isinstance(value, Mapping):
        return None

    if cli_meta.get("mapping", "key_value") != "key_value":
        return None

    sep = str(cli_meta.get("kv_sep", "="))
    items = [
        f"{model._render_scalar(k)}{sep}{model._render_scalar(v)}"
        for k, v in value.items()
    ]
    if not items:
        return []

    repeat = cli_meta.get("repeat", model._default_repeat_iterables)
    compact = bool(cli_meta.get("compact", False))
    join_style = cli_meta.get("join", model._default_join_style)

    if repeat:
        if compact:
            return [f"{flag}{item}" for item in items]
        if join_style == "equals":
            return [f"{flag}={item}" for item in items]

        out: list[str] = []
        for item in items:
            out.extend([flag, item])
        return out

    return [flag, *items]


# Install default reusable hooks.
CLIArgs._emit_hooks = [
    hook_joined_prefix,
    hook_mapping_repeat_compact,
]


# noinspection PyPep8Naming
def CLIField(
    *args: Any,
    positional: bool = False,
    flag: str | None = None,
    repeat: bool | None = None,
    bool_style: str | None = None,
    false_flag: str | None = None,
    join: str | None = None,
    mapping: str | None = None,
    kv_sep: str | None = None,
    compact: bool | None = None,
    item_sep: str | None = None,
    exclude: bool = False,
    **kwargs: Any,
) -> Any:
    cli: dict[str, Any] = {"exclude": exclude}

    if positional:
        cli["positional"] = True
    if flag is not None:
        cli["flag"] = flag
    if repeat is not None:
        cli["repeat"] = repeat
    if bool_style is not None:
        cli["bool_style"] = bool_style
    if false_flag is not None:
        cli["false_flag"] = false_flag
    if join is not None:
        cli["join"] = join
    if mapping is not None:
        cli["mapping"] = mapping
    if kv_sep is not None:
        cli["kv_sep"] = kv_sep
    if compact is not None:
        cli["compact"] = compact
    if item_sep is not None:
        cli["item_sep"] = item_sep

    extra = kwargs.pop("json_schema_extra", {}) or {}
    extra = {**extra, "cli": cli}
    return Field(*args, json_schema_extra=extra, **kwargs)
