"""Table-driven resolver test. Each row: utterance, hint, sticky -> assistant, cleaned text, source."""

from __future__ import annotations

import pytest

from router.registry import Registry
from router.resolver import UnknownAssistantError, find_vocative, name_score, resolve

V, H, S, D = "vocative", "hint", "sticky", "default"

CASES = [
    # --- default names, comma / greeting / bare -----------------------------------------
    ("Claude, what's the weather", None, None, "claude", "what's the weather", V),
    ("hey jarvis what time is it", None, None, "claude", "what time is it", V),
    (
        "Hey Gemini, what do you think of what Claude just said?",
        None,
        None,
        "gemini",
        "what do you think of what Claude just said?",
        V,
    ),
    ("OK Google, play some jazz", None, None, "gemini", "play some jazz", V),
    ("  hey   Jarvis ,  what's up ", None, None, "claude", "what's up", V),
    ("Friday. What's on my calendar", None, None, "gpt", "What's on my calendar", V),
    ("Claude", None, None, "claude", "", V),
    ("Hey Claude.", None, None, "claude", "", V),
    # --- ask / switch / talk ------------------------------------------------------------
    (
        "ask friday to set a timer for ten minutes",
        None,
        None,
        "gpt",
        "set a timer for ten minutes",
        V,
    ),
    ("ask GPT what's new", None, None, "gpt", "what's new", V),
    ("switch to gemini", None, None, "gemini", "", V),
    ("talk to coach", None, None, "coach", "", V),
    ("Hey Gemini", None, None, "gemini", "", V),
    ("switch to Jarvis and tell me a joke", None, None, "claude", "and tell me a joke", V),
    # --- mishears (exact, bare) -------------------------------------------------------
    ("Cloud what time is it", None, None, "claude", "what time is it", V),
    ("clawed, remind me to call mum", None, None, "claude", "remind me to call mum", V),
    ("jeep tea, tell me a joke", None, None, "gpt", "tell me a joke", V),
    ("hey g p t what's new", None, None, "gpt", "what's new", V),
    ("chat gpt, hello", None, None, "gpt", "hello", V),
    # --- fuzzy, needs a cue -------------------------------------------------------------
    ("Hey Jarvus, what's up", None, None, "claude", "what's up", V),
    ("hey clod, what's up", None, None, "claude", "what's up", V),
    ("yo gemeni what's the capital of peru", None, None, "gemini", "what's the capital of peru", V),
    ("Jarvus what's up", None, "gemini", "gemini", "Jarvus what's up", S),  # no cue, not exact
    # --- plain-word names need a cue ---------------------------------------------------
    ("local, turn off the lights", None, None, "local", "turn off the lights", V),
    ("hey house, is the garage closed", None, None, "local", "is the garage closed", V),
    ("Router, what's the tallest mountain", None, None, "auto", "what's the tallest mountain", V),
    (
        "everyone, what's the best pizza topping",
        None,
        None,
        "council",
        "what's the best pizza topping",
        V,
    ),
    ("local weather tomorrow", None, None, "claude", "local weather tomorrow", D),
    ("house prices are rising", None, None, "claude", "house prices are rising", D),
    ("coach me through a workout", None, None, "claude", "coach me through a workout", D),
    ("google the nearest pharmacy", None, None, "claude", "google the nearest pharmacy", D),
    (
        "assistant what's the tallest mountain",
        None,
        None,
        "claude",
        "assistant what's the tallest mountain",
        D,
    ),
    # --- never mid-sentence, never a near-miss without a cue --------------------------
    ("the cloud is grey today", None, "gemini", "gemini", "the cloud is grey today", S),
    ("cloudy skies ahead", None, "gemini", "gemini", "cloudy skies ahead", S),
    (
        "what did jarvis say about dinner",
        None,
        "gemini",
        "gemini",
        "what did jarvis say about dinner",
        S,
    ),
    ("I want to talk to Claude later", None, "gpt", "gpt", "I want to talk to Claude later", S),
    ("Claude's a good name isn't it", None, "gemini", "gemini", "Claude's a good name isn't it", S),
    ("hey, how's the weather", None, None, "claude", "hey, how's the weather", D),
    # --- hint, sticky, default precedence ------------------------------------------------
    ("what's the weather", "jarvis", None, "claude", "what's the weather", H),
    ("hello", "cloud", None, "claude", "hello", H),
    ("hello", "gpt", None, "gpt", "hello", H),
    ("Gemini, what's the weather", "claude", None, "gemini", "what's the weather", V),
    ("and tomorrow?", None, "gpt", "gpt", "and tomorrow?", S),
    ("and tomorrow?", "gemini", "gpt", "gemini", "and tomorrow?", H),
    ("and tomorrow?", None, None, "claude", "and tomorrow?", D),
]


@pytest.mark.parametrize("text,hint,sticky,key,cleaned,source", CASES, ids=[c[0] for c in CASES])
def test_resolve_table(
    registry: Registry,
    text: str,
    hint: str | None,
    sticky: str | None,
    key: str,
    cleaned: str,
    source: str,
) -> None:
    res = resolve(text, registry, hint=hint, sticky=sticky)
    assert (res.assistant.key, res.text, res.source) == (key, cleaned, source)
    assert res.bare_switch == (source == V and cleaned == "")


def test_unknown_hint_raises(registry: Registry) -> None:
    with pytest.raises(UnknownAssistantError, match="nobody"):
        resolve("hello", registry, hint="nobody")


def test_vocative_wins_even_with_unknown_sticky(registry: Registry) -> None:
    res = resolve("hi there", registry, sticky="retired-assistant")
    assert res.assistant.key == "claude" and res.source == D


def test_match_details(registry: Registry) -> None:
    m = find_vocative("Hey Jarvus, what's up", registry)
    assert m is not None
    assert m.assistant.key == "claude"
    assert m.name == "jarvis"
    assert m.matched == "Jarvus"
    assert m.cue == "greeting"
    assert 85 <= m.score < 100

    m = find_vocative("Cloud what time is it", registry)
    assert m is not None and m.cue == "exact" and m.score == 100


def test_fuzzy_threshold_is_respected(registry_data: dict) -> None:
    strict = dict(registry_data, fuzzy_threshold=100)
    reg = Registry.from_dict(strict)
    assert find_vocative("Hey Jarvus, what's up", reg) is None
    assert find_vocative("Hey Jarvis, what's up", reg) is not None


def test_name_score() -> None:
    assert name_score("jarvis", "Jarvis") == 100
    assert name_score("g p t", "gpt") == 100
    assert name_score("chat gpt", "chatgpt") == 100
    assert name_score("jarvus", "jarvis") >= 85
    assert name_score("cloudy", "cloud") >= 85  # which is why bare matches must be exact
    assert name_score("weather", "gemini") < 60
