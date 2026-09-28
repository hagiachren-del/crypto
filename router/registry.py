"""assistants.yaml: load, validate, resolve inheritance, and watch for edits.

The file is the single source of truth for names. Every name and mishear must be unique across
the file; loading fails loudly otherwise. A `base:` entry inherits model/voice/tools/flags from
its base unless it overrides them.
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

log = logging.getLogger(__name__)

DEFAULT_PLAIN_WORDS = [
    "local",
    "house",
    "coach",
    "google",
    "everyone",
    "assistant",
    "router",
    "auto",
]


class RegistryError(ValueError):
    """assistants.yaml is invalid. The message says exactly what and where."""


def normalize_name(name: str) -> str:
    """Lowercase, trim, collapse whitespace, drop punctuation except internal spaces."""
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


class Voice(BaseModel):
    provider: str = "openai"
    voice: str


class AssistantEntry(BaseModel):
    """One raw entry of assistants.yaml, before inheritance."""

    model: str | None = None
    names: list[str] = Field(min_length=1)
    mishears: list[str] = Field(default_factory=list)
    display_name: str | None = None
    voice: Voice | None = None
    private: bool | None = None
    router: bool = False
    council: list[str] | None = None
    synthesizer: str | None = None
    base: str | None = None
    system_prompt: str | None = None
    tools: list[str] | None = None
    search: bool | None = None
    image: bool | None = None

    @model_validator(mode="after")
    def _one_kind(self) -> AssistantEntry:
        kinds = [
            k
            for k, v in (
                ("model", self.model),
                ("base", self.base),
                ("router", self.router or None),
                ("council", self.council),
            )
            if v
        ]
        if len(kinds) != 1:
            raise ValueError(
                f"needs exactly one of model/base/router/council, got {kinds or 'none'}"
            )
        return self


class RegistryFile(BaseModel):
    default_assistant: str
    sticky_minutes: int = 10
    fuzzy_threshold: int = Field(default=85, ge=50, le=100)
    plain_words: list[str] = Field(default_factory=lambda: list(DEFAULT_PLAIN_WORDS))
    assistants: dict[str, AssistantEntry] = Field(min_length=1)


@dataclass(frozen=True)
class Assistant:
    """A fully resolved assistant (inheritance applied)."""

    key: str
    names: tuple[str, ...]
    mishears: tuple[str, ...]
    display_name: str
    model: str | None = None
    voice: Voice | None = None
    private: bool = False
    router: bool = False
    council: tuple[str, ...] = ()
    synthesizer: str | None = None
    base: str | None = None
    system_prompt: str | None = None
    tools: tuple[str, ...] = ()
    search: bool = False
    image: bool = False

    @property
    def kind(self) -> str:
        if self.router:
            return "router"
        if self.council:
            return "council"
        return "model"

    @property
    def all_names(self) -> tuple[str, ...]:
        return self.names + self.mishears


@dataclass
class Registry:
    default_assistant: str
    sticky_minutes: int
    fuzzy_threshold: int
    plain_words: frozenset[str]
    assistants: dict[str, Assistant]
    _by_name: dict[str, str] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._by_name = {}
        for a in self.assistants.values():
            for n in a.all_names:
                self._by_name[normalize_name(n)] = a.key

    # -- lookups -------------------------------------------------------------------------
    def get(self, key: str) -> Assistant:
        try:
            return self.assistants[key]
        except KeyError:
            raise KeyError(f"unknown assistant {key!r}") from None

    def lookup(self, name_or_key: str) -> Assistant | None:
        """Exact (case-insensitive) match on a key, a name or a mishear."""
        if name_or_key in self.assistants:
            return self.assistants[name_or_key]
        key = self._by_name.get(normalize_name(name_or_key))
        return self.assistants[key] if key else None

    def names_index(self) -> dict[str, str]:
        """normalized name/mishear -> assistant key."""
        return dict(self._by_name)

    @property
    def default(self) -> Assistant:
        return self.assistants[self.default_assistant]

    def is_plain_word(self, name: str) -> bool:
        return normalize_name(name) in self.plain_words

    # -- loading -------------------------------------------------------------------------
    @classmethod
    def from_dict(cls, data: dict[str, Any], *, source: str = "assistants.yaml") -> Registry:
        try:
            parsed = RegistryFile.model_validate(data)
        except ValidationError as e:
            raise RegistryError(f"{source}: {_format_validation_error(e)}") from None

        problems: list[str] = []
        entries = parsed.assistants

        if parsed.default_assistant not in entries:
            problems.append(f"default_assistant {parsed.default_assistant!r} is not an assistant")

        # unique names + mishears across the whole file
        seen: dict[str, tuple[str, str]] = {}
        for key, e in entries.items():
            for kind, values in (("name", e.names), ("mishear", e.mishears)):
                for raw in values:
                    n = normalize_name(raw)
                    if not n:
                        problems.append(f"{key}: empty {kind} {raw!r}")
                        continue
                    if n in seen:
                        other_key, other_kind = seen[n]
                        where = f"{other_key} ({other_kind})"
                        problems.append(
                            f"{key}: {kind} {raw!r} is already used by {where}; names and "
                            "mishears must be unique across the file"
                        )
                    else:
                        seen[n] = (key, kind)
            if key != normalize_name(key) or " " in key:
                problems.append(f"{key}: assistant keys must be lowercase words, no spaces")

        # references
        for key, e in entries.items():
            if e.base is not None:
                if e.base not in entries:
                    problems.append(f"{key}: base {e.base!r} is not an assistant")
                elif entries[e.base].base is not None:
                    problems.append(f"{key}: base {e.base!r} is itself a persona; one level only")
                elif entries[e.base].router or entries[e.base].council:
                    problems.append(f"{key}: base {e.base!r} must be a plain model assistant")
            if e.council is not None:
                if len(e.council) < 2:
                    problems.append(f"{key}: a council needs at least two members")
                for m in e.council:
                    if m not in entries:
                        problems.append(f"{key}: council member {m!r} is not an assistant")
                    elif entries[m].router or entries[m].council:
                        problems.append(f"{key}: council member {m!r} must be a model assistant")
                if e.synthesizer is not None and e.synthesizer not in entries:
                    problems.append(f"{key}: synthesizer {e.synthesizer!r} is not an assistant")
            if e.system_prompt is not None and not e.system_prompt.strip():
                problems.append(f"{key}: system_prompt is empty")

        if problems:
            raise RegistryError(f"{source}:\n  - " + "\n  - ".join(problems))

        resolved = {key: _resolve(key, e, entries) for key, e in entries.items()}
        return cls(
            default_assistant=parsed.default_assistant,
            sticky_minutes=parsed.sticky_minutes,
            fuzzy_threshold=parsed.fuzzy_threshold,
            plain_words=frozenset(normalize_name(w) for w in parsed.plain_words),
            assistants=resolved,
        )

    @classmethod
    def load(cls, path: Path | str) -> Registry:
        p = Path(path)
        try:
            data = yaml.safe_load(p.read_text())
        except FileNotFoundError:
            raise RegistryError(f"{p}: file not found") from None
        except yaml.YAMLError as e:
            raise RegistryError(f"{p}: not valid YAML: {e}") from None
        if not isinstance(data, dict):
            raise RegistryError(f"{p}: top level must be a mapping")
        return cls.from_dict(data, source=str(p))


def _resolve(key: str, e: AssistantEntry, entries: dict[str, AssistantEntry]) -> Assistant:
    parent = entries[e.base] if e.base else None

    def inherit(attr: str, default: Any) -> Any:
        v = getattr(e, attr)
        if v is None and parent is not None:
            v = getattr(parent, attr)
        return default if v is None else v

    display = e.display_name or _default_display(e.names[0])
    return Assistant(
        key=key,
        names=tuple(e.names),
        mishears=tuple(e.mishears),
        display_name=display,
        model=inherit("model", None),
        voice=inherit("voice", None),
        private=bool(inherit("private", False)),
        router=e.router,
        council=tuple(e.council or ()),
        synthesizer=e.synthesizer or (e.council[0] if e.council else None),
        base=e.base,
        system_prompt=e.system_prompt,
        tools=tuple(inherit("tools", ())),
        search=bool(inherit("search", False)),
        image=bool(inherit("image", False)),
    )


def _default_display(name: str) -> str:
    n = name.strip()
    return n.upper() if len(n) <= 3 else n[:1].upper() + n[1:]


def _format_validation_error(e: ValidationError) -> str:
    parts = []
    for err in e.errors():
        loc = ".".join(str(x) for x in err["loc"]) or "<root>"
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)


class RegistryHolder:
    """Holds the live registry and reloads it when assistants.yaml changes.

    A bad edit is logged and the previous good registry stays in service.
    """

    def __init__(self, path: Path | str, registry: Registry | None = None) -> None:
        self.path = Path(path)
        self.registry = registry or Registry.load(self.path)
        self._listeners: list[Callable[[Registry], None]] = []
        self._task: asyncio.Task[None] | None = None

    def on_reload(self, fn: Callable[[Registry], None]) -> None:
        self._listeners.append(fn)

    def reload(self) -> bool:
        try:
            self.registry = Registry.load(self.path)
        except RegistryError as e:
            log.error("assistants.yaml rejected, keeping the previous registry:\n%s", e)
            return False
        log.info("registry reloaded: %s", ", ".join(self.registry.assistants))
        for fn in self._listeners:
            fn(self.registry)
        return True

    async def watch(self) -> None:
        from watchfiles import awatch

        directory = self.path.resolve().parent
        target = self.path.resolve()
        async for changes in awatch(directory):
            if any(Path(p).resolve() == target for _, p in changes):
                self.reload()

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self.watch(), name="registry-watch")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None
