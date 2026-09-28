"""FastAPI application. Slice 1: `POST /voice` (JSON, text only) and `GET /health`."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from router.auth import Authenticator
from router.engine import EmptyRequestError, Engine, VoiceRequest
from router.llm import LiteLLMProvider, Provider, ProviderError
from router.memory import Memory
from router.registry import RegistryHolder
from router.resolver import UnknownAssistantError
from router.settings import Config, Settings

log = logging.getLogger(__name__)


class VoiceIn(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    user_id: str | None = None
    device_id: str | None = None
    assistant: str | None = None
    device_voice: bool = False


class VoiceOut(BaseModel):
    reply: str
    assistant: str
    assistant_name: str
    session_id: str
    routed_by: str
    announce: bool
    audio_url: str | None = None


def create_app(
    settings: Settings | None = None,
    *,
    config: Config | None = None,
    registry: RegistryHolder | None = None,
    memory: Memory | None = None,
    provider: Provider | None = None,
    watch_registry: bool = True,
) -> FastAPI:
    settings = settings or Settings()
    config = config or settings.load_config()
    registry = registry or RegistryHolder(settings.assistants_file)
    memory = memory or Memory(config.memory)
    provider = provider or LiteLLMProvider()
    auth = Authenticator(settings.device_tokens())
    engine = Engine(
        registry=registry,
        memory=memory,
        provider=provider,
        config=config,
        prompts_dir=settings.prompts_dir,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if watch_registry and Path(registry.path).exists():
            registry.start()
        try:
            yield
        finally:
            await registry.stop()

    app = FastAPI(title="voice-router", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.config = config
    app.state.registry = registry
    app.state.memory = memory
    app.state.engine = engine
    app.state.auth = auth

    @app.exception_handler(UnknownAssistantError)
    async def _unknown_assistant(_: Request, exc: UnknownAssistantError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(EmptyRequestError)
    async def _empty(_: Request, exc: EmptyRequestError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(ProviderError)
    async def _provider(_: Request, exc: ProviderError) -> JSONResponse:
        log.error("provider error: %s", exc)
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.get("/health")
    async def health() -> dict[str, Any]:
        reg = registry.registry
        return {
            "ok": True,
            "assistants": list(reg.assistants),
            "default": reg.default_assistant,
            "auth": auth.required,
        }

    @app.post("/voice", response_model=VoiceOut)
    async def voice(body: VoiceIn, device: str | None = Depends(auth)) -> VoiceOut:
        if not body.text.strip():
            raise HTTPException(status_code=400, detail="text is empty")
        req = VoiceRequest(
            text=body.text,
            user_id=body.user_id or settings.default_user,
            device_id=body.device_id or device,
            assistant=body.assistant,
            device_voice=body.device_voice,
        )
        result = await engine.handle(req)
        return VoiceOut(**result.__dict__)

    return app


def default_app() -> FastAPI:
    """For `uvicorn router.app:default_app --factory`."""
    settings = Settings()
    logging.basicConfig(level=settings.log_level.upper())
    return create_app(settings)
