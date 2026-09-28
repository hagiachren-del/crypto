from __future__ import annotations

import copy
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

from router.app import create_app
from router.engine import Engine
from router.llm import Message, ProviderError
from router.memory import Memory
from router.registry import Registry, RegistryHolder
from router.settings import Config, MemoryConfig, Settings

ROOT = Path(__file__).resolve().parents[1]
ASSISTANTS_FILE = ROOT / "assistants.yaml"
PROMPTS_DIR = ROOT / "prompts"

TOKENS = {"tok-iphone": "iphone", "tok-mac": "mac"}


class FakeClock:
    def __init__(self, start: datetime) -> None:
        self.t = start

    def __call__(self) -> datetime:
        return self.t

    def advance(self, *, minutes: float = 0, seconds: float = 0) -> None:
        self.t += timedelta(minutes=minutes, seconds=seconds)


class FakeProvider:
    """Records every call. Replies come from a per-model script, else an echo."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[Message]]] = []
        self.scripts: dict[str, list[str]] = {}
        self.failing: set[str] = set()

    def script(self, model: str, *replies: str) -> None:
        self.scripts.setdefault(model, []).extend(replies)

    def calls_for(self, model: str) -> list[list[Message]]:
        return [m for mdl, m in self.calls if mdl == model]

    @staticmethod
    def last_user(messages: list[Message]) -> str:
        return next(m["content"] for m in reversed(messages) if m["role"] == "user")

    async def complete(self, model: str, messages: list[Message], **_: Any) -> str:
        self.calls.append((model, copy.deepcopy(messages)))
        if model in self.failing:
            raise ProviderError(f"{model}: simulated failure")
        queue = self.scripts.get(model)
        if queue:
            return queue.pop(0)
        return f"[{model}] {self.last_user(messages)}"

    async def stream(self, model: str, messages: list[Message], **kw: Any) -> AsyncIterator[str]:
        yield await self.complete(model, messages, **kw)


@pytest.fixture
def registry_data() -> dict[str, Any]:
    return yaml.safe_load(ASSISTANTS_FILE.read_text())


@pytest.fixture
def registry(registry_data: dict[str, Any]) -> Registry:
    return Registry.from_dict(registry_data, source="assistants.yaml")


@pytest.fixture
def holder(registry: Registry) -> RegistryHolder:
    return RegistryHolder(ASSISTANTS_FILE, registry)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(datetime(2026, 9, 28, 9, 0, 0, tzinfo=UTC))


@pytest.fixture
def memory_config(tmp_path: Path) -> MemoryConfig:
    return MemoryConfig(
        db_path=str(tmp_path / "router.db"),
        session_minutes=30,
        replay_turns=6,
        summarize_after_turns=10,
    )


@pytest.fixture
def memory(memory_config: MemoryConfig, clock: FakeClock) -> Memory:
    return Memory(memory_config, now=clock)


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def config(memory_config: MemoryConfig) -> Config:
    cfg = Config()
    cfg.memory = memory_config
    cfg.auto.cheapest = "gemini"
    return cfg


@pytest.fixture
def engine(
    holder: RegistryHolder, memory: Memory, provider: FakeProvider, config: Config
) -> Engine:
    return Engine(
        registry=holder, memory=memory, provider=provider, config=config, prompts_dir=PROMPTS_DIR
    )


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        assistants_file=ASSISTANTS_FILE,
        prompts_dir=PROMPTS_DIR,
        tokens=",".join(f"{d}:{t}" for t, d in TOKENS.items()),
        default_user="me",
    )


@pytest.fixture
def client(
    settings: Settings,
    config: Config,
    holder: RegistryHolder,
    memory: Memory,
    provider: FakeProvider,
) -> Iterator[TestClient]:
    app = create_app(
        settings,
        config=config,
        registry=holder,
        memory=memory,
        provider=provider,
        watch_registry=False,
    )
    with TestClient(app) as c:
        yield c
