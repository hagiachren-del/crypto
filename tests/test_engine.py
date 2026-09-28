from __future__ import annotations

import json

import pytest

from router.engine import EmptyRequestError, Engine, VoiceRequest, clean_reply
from router.llm import ProviderError
from router.memory import Memory

from .conftest import FakeClock, FakeProvider

CLAUDE = "anthropic/claude-sonnet-5"
GPT = "openai/gpt-6-sol"
GEMINI = "gemini/gemini-3.8-flash"
LOCAL = "ollama/gemma3:12b"
HAIKU = "anthropic/claude-haiku-4-5"


def req(text: str, **kw) -> VoiceRequest:
    return VoiceRequest(text=text, user_id=kw.pop("user_id", "me"), **kw)


async def test_default_assistant_answers(engine: Engine, provider: FakeProvider) -> None:
    provider.script(CLAUDE, "It is sunny.")
    r = await engine.handle(req("what's the weather", device_id="iphone"))
    assert r.reply == "It is sunny."
    assert (r.assistant, r.assistant_name, r.routed_by, r.announce) == (
        "claude",
        "Claude",
        "default",
        False,
    )
    model, messages = provider.calls[0]
    assert model == CLAUDE
    assert messages[0]["role"] == "system"
    assert "You are Claude" in messages[0]["content"]
    assert "two sentences" in messages[0]["content"]
    assert messages[-1] == {"role": "user", "content": "what's the weather"}


async def test_vocative_strips_name_and_switch_announces(
    engine: Engine, provider: FakeProvider
) -> None:
    r1 = await engine.handle(req("hello"))
    assert r1.assistant == "claude" and r1.announce is False
    r2 = await engine.handle(req("Gemini, what's two plus two"))
    assert r2.assistant == "gemini" and r2.routed_by == "vocative"
    assert r2.announce is True  # switched away from Claude
    assert provider.last_user(provider.calls[-1][1]) == "what's two plus two"
    r3 = await engine.handle(req("and times three?"))
    assert r3.assistant == "gemini" and r3.routed_by == "sticky" and r3.announce is False


async def test_first_answer_by_named_assistant_is_not_announced(engine: Engine) -> None:
    r = await engine.handle(req("Gemini, hi"))
    assert r.assistant == "gemini" and r.announce is False


async def test_bare_switch_sets_stickiness_without_calling_a_model(
    engine: Engine, provider: FakeProvider
) -> None:
    r = await engine.handle(req("switch to Gemini"))
    assert r.reply == "Gemini here." and r.assistant == "gemini" and provider.calls == []
    r2 = await engine.handle(req("what's the weather"))
    assert r2.assistant == "gemini" and r2.routed_by == "sticky"
    assert provider.calls[0][0] == GEMINI


async def test_sticky_expires(engine: Engine, clock: FakeClock) -> None:
    await engine.handle(req("switch to gpt"))
    clock.advance(minutes=11)
    r = await engine.handle(req("what's the weather"))
    assert r.assistant == "claude" and r.routed_by == "default"


async def test_hint_routes_and_vocative_overrides_hint(engine: Engine) -> None:
    r = await engine.handle(req("what's up", assistant="jarvis"))
    assert r.assistant == "claude" and r.routed_by == "hint"
    r = await engine.handle(req("Friday, what's up", assistant="claude"))
    assert r.assistant == "gpt" and r.routed_by == "vocative"


async def test_device_voice_prefixes_only_when_announcing(
    engine: Engine, provider: FakeProvider
) -> None:
    provider.script(CLAUDE, "Hi.")
    r = await engine.handle(req("hello", device_voice=True))
    assert r.reply == "Hi."
    provider.script(GEMINI, "Four.")
    r = await engine.handle(req("Gemini, two plus two", device_voice=True))
    assert r.reply == "Gemini. Four." and r.announce is True
    r = await engine.handle(req("and times three", device_voice=True))
    assert r.announce is False and not r.reply.startswith("Gemini.")  # sticky, no switch


async def test_transcript_is_shared_and_labelled(engine: Engine, provider: FakeProvider) -> None:
    provider.script(CLAUDE, "Pizza, obviously.")
    await engine.handle(req("Claude, what should I eat tonight", device_id="iphone"))
    await engine.handle(req("Gemini, what do you think of what Claude just said?", device_id="mac"))
    _, messages = provider.calls[-1]
    assert messages[1] == {"role": "user", "content": "what should I eat tonight"}
    assert messages[2] == {"role": "assistant", "content": "Claude: Pizza, obviously."}
    assert messages[-1]["content"] == "what do you think of what Claude just said?"
    assert "Claude" in messages[0]["content"]  # told who else is in the room


async def test_private_turns_never_reach_cloud_assistants(
    engine: Engine, provider: FakeProvider
) -> None:
    await engine.handle(req("hello"))
    await engine.handle(req("house, unlock the front door"))
    assert provider.calls[-1][0] == LOCAL
    await engine.handle(req("Claude, what did I just ask?"))
    _, messages = provider.calls[-1]
    text = json.dumps(messages)
    assert "unlock" not in text
    await engine.handle(req("local, and the back door"))
    _, messages = provider.calls[-1]
    assert "unlock the front door" in json.dumps(messages)


async def test_auto_classifier_routes_and_announces(engine: Engine, provider: FakeProvider) -> None:
    provider.script(
        HAIKU,
        '{"target": "gemini", "cleaned_query": "who won the game last night", "confidence": 0.9}',
    )
    provider.script(GEMINI, "The home side, three two.")
    r = await engine.handle(req("hey assistant, who won the game last night"))
    assert (r.assistant, r.routed_by, r.announce) == ("gemini", "auto", True)
    assert r.reply == "The home side, three two."
    cls_model, cls_messages = provider.calls[0]
    assert cls_model == HAIKU
    assert "gemini" in cls_messages[0]["content"] and "web search" in cls_messages[0]["content"]
    assert provider.last_user(cls_messages) == "who won the game last night"
    assert provider.last_user(provider.calls[1][1]) == "who won the game last night"


@pytest.mark.parametrize(
    "classifier_reply",
    [
        "I think Gemini should answer this one.",
        '{"target": "nobody", "cleaned_query": "x", "confidence": 0.9}',
        '{"target": "council", "cleaned_query": "x", "confidence": 0.9}',
        '{"target": "gemini", "cleaned_query": "x", "confidence": 0.2}',
    ],
)
async def test_auto_falls_back_to_default(
    engine: Engine, provider: FakeProvider, classifier_reply: str
) -> None:
    provider.script(HAIKU, classifier_reply)
    r = await engine.handle(req("router, tell me something"))
    assert r.assistant == "claude" and r.routed_by == "auto"
    assert provider.calls[1][0] == CLAUDE
    assert provider.last_user(provider.calls[1][1]) == "tell me something"


async def test_auto_survives_classifier_outage(engine: Engine, provider: FakeProvider) -> None:
    provider.failing.add(HAIKU)
    r = await engine.handle(req("auto, hello"))
    assert r.assistant == "claude"


async def test_council_fans_out_and_synthesizes(engine: Engine, provider: FakeProvider) -> None:
    provider.script(CLAUDE, "Tabs.", "The council mostly says tabs; GPT prefers spaces.")
    provider.script(GPT, "Spaces.")
    provider.script(GEMINI, "Tabs.")
    r = await engine.handle(req("everyone, tabs or spaces?"))
    assert r.assistant == "council" and r.assistant_name == "Council"
    assert r.reply == "The council mostly says tabs; GPT prefers spaces."
    models = [m for m, _ in provider.calls]
    assert sorted(models[:3]) == sorted([CLAUDE, GPT, GEMINI])
    assert models[3] == CLAUDE  # synthesizer
    synth_prompt = provider.last_user(provider.calls[3][1])
    assert "Claude answered: Tabs." in synth_prompt
    assert "GPT answered: Spaces." in synth_prompt
    assert "Gemini answered: Tabs." in synth_prompt
    assert "council" in provider.calls[3][1][0]["content"].lower()


async def test_council_tolerates_one_failure(engine: Engine, provider: FakeProvider) -> None:
    provider.failing.add(GPT)
    provider.script(CLAUDE, "Yes.", "Both say yes; GPT did not answer.")
    r = await engine.handle(req("council, is water wet"))
    assert r.reply.startswith("Both say yes")
    assert "Did not answer: GPT" in provider.last_user(provider.calls[-1][1])


async def test_council_all_failing_raises(engine: Engine, provider: FakeProvider) -> None:
    provider.failing |= {CLAUDE, GPT, GEMINI}
    with pytest.raises(ProviderError):
        await engine.handle(req("council, anyone there"))


async def test_persona_uses_base_model_with_its_own_prompt(
    engine: Engine, provider: FakeProvider
) -> None:
    r = await engine.handle(req("coach, what should I do today"))
    assert r.assistant == "coach"
    model, messages = provider.calls[0]
    assert model == CLAUDE
    assert "You are Coach" in messages[0]["content"]
    assert "fitness" in messages[0]["content"]


async def test_new_conversation_command(
    engine: Engine, provider: FakeProvider, memory: Memory
) -> None:
    r1 = await engine.handle(req("hello"))
    r2 = await engine.handle(req("new conversation"))
    assert r2.routed_by == "command" and "new conversation" in r2.reply.lower()
    assert r2.session_id != r1.session_id
    assert len(provider.calls) == 1
    r3 = await engine.handle(req("hello again"))
    assert r3.session_id == r2.session_id
    assert len(provider.calls[-1][1]) == 2  # system + user, no history carried over


async def test_summary_is_built_and_used(
    engine: Engine, provider: FakeProvider, clock: FakeClock
) -> None:
    engine.config.memory.replay_turns = 2
    engine.config.memory.summarize_after_turns = 4
    engine.memory.config = engine.config.memory
    provider.script(HAIKU, "User asked about q0 and q1.")
    for i in range(3):
        await engine.handle(req(f"q{i}"))
        clock.advance(seconds=1)
    assert HAIKU in [m for m, _ in provider.calls]
    await engine.handle(req("q3"))
    _, messages = provider.calls[-1]
    assert "User asked about q0 and q1." in messages[0]["content"]
    assert [m["content"] for m in messages[1:]] == [
        "q2",
        "Claude: [anthropic/claude-sonnet-5] q2",
        "q3",
    ]


async def test_empty_text_rejected(engine: Engine) -> None:
    with pytest.raises(EmptyRequestError):
        await engine.handle(req("   "))


def test_clean_reply() -> None:
    assert clean_reply("Claude: hello there", "Claude") == "hello there"
    assert clean_reply("[GPT] - hi", "GPT") == "hi"
    assert clean_reply("  plain  ", "Claude") == "plain"
    assert clean_reply("Claude is a name.", "Claude") == "Claude is a name."
