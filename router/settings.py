"""Process configuration: .env (secrets, paths) and config.yaml (everything that is not a name)."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8787


class ModelsConfig(BaseModel):
    classifier: str = "anthropic/claude-haiku-4-5"
    summarizer: str = "anthropic/claude-haiku-4-5"


class MemoryConfig(BaseModel):
    db_path: str = "data/router.db"
    session_minutes: int = 30
    replay_turns: int = 12
    summarize_after_turns: int = 24


class AutoConfig(BaseModel):
    cheapest: str | None = None
    min_confidence: float = 0.5


class SttConfig(BaseModel):
    local_model: str = "small.en"
    fallback: str | None = "openai/gpt-4o-mini-transcribe"


class TtsConfig(BaseModel):
    openai_model: str = "gpt-4o-mini-tts"
    format: str = "mp3"


class SpeechConfig(BaseModel):
    stt: SttConfig = Field(default_factory=SttConfig)
    tts: TtsConfig = Field(default_factory=TtsConfig)


class Config(BaseModel):
    """Contents of config.yaml."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    auto: AutoConfig = Field(default_factory=AutoConfig)
    speech: SpeechConfig = Field(default_factory=SpeechConfig)

    @classmethod
    def load(cls, path: Path | str) -> Config:
        p = Path(path)
        if not p.exists():
            return cls()
        data = yaml.safe_load(p.read_text()) or {}
        return cls.model_validate(data)


class Settings(BaseSettings):
    """Values from the environment / .env. Prefix ROUTER_."""

    model_config = SettingsConfigDict(env_prefix="ROUTER_", env_file=".env", extra="ignore")

    assistants_file: Path = Path("assistants.yaml")
    config_file: Path = Path("config.yaml")
    prompts_dir: Path = Path("prompts")
    tokens: str = ""  # "device:token,device:token"
    default_user: str = "me"
    log_level: str = "INFO"

    def device_tokens(self) -> dict[str, str]:
        """Map token -> device_id."""
        out: dict[str, str] = {}
        for pair in self.tokens.split(","):
            pair = pair.strip()
            if not pair:
                continue
            if ":" not in pair:
                raise ValueError(f"ROUTER_TOKENS entry {pair!r} must look like device:token")
            device, token = pair.split(":", 1)
            device, token = device.strip(), token.strip()
            if not device or not token:
                raise ValueError(f"ROUTER_TOKENS entry {pair!r} has an empty device or token")
            if token in out:
                raise ValueError(f"ROUTER_TOKENS token for {device!r} is reused by {out[token]!r}")
            out[token] = device
        return out

    def load_config(self) -> Config:
        return Config.load(self.config_file)
