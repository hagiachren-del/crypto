from __future__ import annotations

from fastapi.testclient import TestClient

from router.app import create_app
from router.memory import Memory
from router.settings import Settings

from .conftest import ASSISTANTS_FILE, PROMPTS_DIR, FakeProvider

AUTH = {"Authorization": "Bearer tok-iphone"}


def test_health_is_open(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] and body["default"] == "claude" and body["auth"] is True
    assert "claude" in body["assistants"]


def test_voice_requires_token(client: TestClient) -> None:
    assert client.post("/voice", json={"text": "hi"}).status_code == 401
    bad = {"Authorization": "Bearer nope"}
    assert client.post("/voice", json={"text": "hi"}, headers=bad).status_code == 401


def test_voice_text_only(client: TestClient, provider: FakeProvider, memory: Memory) -> None:
    provider.script("anthropic/claude-sonnet-5", "Twenty three degrees and sunny.")
    r = client.post("/voice", json={"text": "what's the weather", "user_id": "me"}, headers=AUTH)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reply"] == "Twenty three degrees and sunny."
    assert body["assistant"] == "claude"
    assert body["assistant_name"] == "Claude"
    assert body["routed_by"] == "default"
    assert body["announce"] is False
    assert body["audio_url"] is None
    session = memory.get_session(body["session_id"])
    assert session is not None
    turns = memory.history(session, include_private=True)
    assert [t.device_id for t in turns] == ["iphone", "iphone"]  # device comes from the token


def test_voice_defaults_user_and_uses_hint(client: TestClient, provider: FakeProvider) -> None:
    r = client.post("/voice", json={"text": "hello", "assistant": "friday"}, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["assistant"] == "gpt" and r.json()["routed_by"] == "hint"
    assert provider.calls[0][0] == "openai/gpt-6-sol"


def test_voice_session_is_shared_across_devices(client: TestClient) -> None:
    r1 = client.post("/voice", json={"text": "hello"}, headers=AUTH)
    r2 = client.post("/voice", json={"text": "again"}, headers={"Authorization": "Bearer tok-mac"})
    assert r1.json()["session_id"] == r2.json()["session_id"]


def test_voice_device_voice_prefix(client: TestClient, provider: FakeProvider) -> None:
    client.post("/voice", json={"text": "hello"}, headers=AUTH)
    provider.script("gemini/gemini-3.8-flash", "Four.")
    r = client.post(
        "/voice", json={"text": "Gemini, two plus two", "device_voice": True}, headers=AUTH
    )
    assert r.json()["reply"] == "Gemini. Four."


def test_voice_bad_requests(client: TestClient) -> None:
    assert client.post("/voice", json={"text": ""}, headers=AUTH).status_code == 422
    r = client.post("/voice", json={"text": "   "}, headers=AUTH)
    assert r.status_code == 400
    r = client.post("/voice", json={"text": "hi", "assistant": "nobody"}, headers=AUTH)
    assert r.status_code == 400 and "nobody" in r.json()["detail"]


def test_provider_failure_is_502(client: TestClient, provider: FakeProvider) -> None:
    provider.failing.add("anthropic/claude-sonnet-5")
    r = client.post("/voice", json={"text": "hi"}, headers=AUTH)
    assert r.status_code == 502


def test_open_mode_when_no_tokens(tmp_path, provider: FakeProvider) -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        assistants_file=ASSISTANTS_FILE,
        prompts_dir=PROMPTS_DIR,
        tokens="",
    )
    from router.settings import Config, MemoryConfig

    cfg = Config()
    cfg.memory = MemoryConfig(db_path=str(tmp_path / "open.db"))
    app = create_app(settings, config=cfg, provider=provider, watch_registry=False)
    with TestClient(app) as c:
        assert c.get("/health").json()["auth"] is False
        assert c.post("/voice", json={"text": "hi"}).status_code == 200


def test_bad_token_config_is_rejected() -> None:
    import pytest

    s = Settings(_env_file=None, tokens="justatoken")  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="device:token"):
        s.device_tokens()
    s = Settings(_env_file=None, tokens="a:same,b:same")  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="reused"):
        s.device_tokens()
