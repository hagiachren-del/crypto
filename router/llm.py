"""Provider adapter. Everything that talks to a model goes through `Provider`, so tests swap in
a fake and never touch the network. The real one is LiteLLM."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any, Protocol

log = logging.getLogger(__name__)

Message = dict[str, Any]


class Provider(Protocol):
    async def complete(self, model: str, messages: list[Message], **kwargs: Any) -> str: ...

    def stream(self, model: str, messages: list[Message], **kwargs: Any) -> AsyncIterator[str]: ...


class ProviderError(RuntimeError):
    pass


class LiteLLMProvider:
    """Thin wrapper over litellm.acompletion. `model` is a LiteLLM model string such as
    `anthropic/claude-sonnet-5`, `openai/gpt-6-sol`, `gemini/gemini-3.8-flash`,
    `ollama/gemma3:12b`."""

    def __init__(self, *, timeout: float = 60.0, max_tokens: int = 1024) -> None:
        self.timeout = timeout
        self.max_tokens = max_tokens
        self._litellm: Any = None

    def _lib(self) -> Any:
        if self._litellm is None:
            import litellm  # slow import, do it once and late

            litellm.drop_params = True  # providers ignore params they don't support
            litellm.suppress_debug_info = True
            self._litellm = litellm
        return self._litellm

    async def complete(self, model: str, messages: list[Message], **kwargs: Any) -> str:
        litellm = self._lib()
        params = {"timeout": self.timeout, "max_tokens": self.max_tokens, **kwargs}
        try:
            resp = await litellm.acompletion(model=model, messages=messages, **params)
        except Exception as e:  # litellm raises many exception types; the caller only needs one
            raise ProviderError(f"{model}: {e.__class__.__name__}: {e}") from e
        content = resp.choices[0].message.content
        return content or ""

    async def stream(
        self, model: str, messages: list[Message], **kwargs: Any
    ) -> AsyncIterator[str]:
        litellm = self._lib()
        params = {"timeout": self.timeout, "max_tokens": self.max_tokens, **kwargs}
        try:
            response = await litellm.acompletion(
                model=model, messages=messages, stream=True, **params
            )
            async for chunk in response:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"{model}: {e.__class__.__name__}: {e}") from e


def merge_consecutive(messages: list[Message]) -> list[Message]:
    """Some providers reject two consecutive messages with the same role. Join them."""
    out: list[Message] = []
    for m in messages:
        if out and out[-1]["role"] == m["role"] and m["role"] != "system":
            out[-1] = {**out[-1], "content": f"{out[-1]['content']}\n\n{m['content']}"}
        else:
            out.append(dict(m))
    return out
