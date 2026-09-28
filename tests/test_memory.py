from __future__ import annotations

from router.memory import Memory
from router.registry import Registry

from .conftest import FakeClock


def test_session_rolls_over_after_window(memory: Memory, clock: FakeClock) -> None:
    s1 = memory.get_or_create_session("me")
    clock.advance(minutes=29)
    assert memory.get_or_create_session("me").id == s1.id
    clock.advance(minutes=31)
    assert memory.get_or_create_session("me").id != s1.id


def test_sessions_are_per_user(memory: Memory) -> None:
    assert memory.get_or_create_session("a").id != memory.get_or_create_session("b").id


def test_new_conversation_ends_session(memory: Memory) -> None:
    s1 = memory.get_or_create_session("me")
    ended = memory.end_session("me")
    assert ended is not None and ended.ended_at is not None
    assert memory.get_or_create_session("me").id != s1.id
    assert memory.end_session("nobody") is None


def test_activity_extends_session(memory: Memory, clock: FakeClock, registry: Registry) -> None:
    s = memory.get_or_create_session("me")
    clock.advance(minutes=20)
    memory.record_exchange(s, user_text="hi", reply="hello", assistant=registry.get("claude"))
    clock.advance(minutes=20)  # 40 min since start, 20 since last activity
    assert memory.get_or_create_session("me").id == s.id


def test_sticky_assistant(memory: Memory, clock: FakeClock, registry: Registry) -> None:
    s = memory.get_or_create_session("me")
    assert memory.sticky_assistant(s, 10) is None
    s = memory.record_exchange(s, user_text="hi", reply="yo", assistant=registry.get("gemini"))
    assert memory.sticky_assistant(s, 10) == "gemini"
    clock.advance(minutes=9)
    assert memory.sticky_assistant(s, 10) == "gemini"
    clock.advance(minutes=2)
    assert memory.sticky_assistant(s, 10) is None


def test_turns_are_shared_across_devices_and_labelled(memory: Memory, registry: Registry) -> None:
    s = memory.get_or_create_session("me")
    memory.record_exchange(
        s, user_text="q1", reply="a1", assistant=registry.get("claude"), device_id="iphone"
    )
    memory.record_exchange(
        s, user_text="q2", reply="a2", assistant=registry.get("gemini"), device_id="mac"
    )
    turns = memory.history(s, include_private=False)
    assert [(t.role, t.content, t.assistant_name, t.device_id) for t in turns] == [
        ("user", "q1", "Claude", "iphone"),
        ("assistant", "a1", "Claude", "iphone"),
        ("user", "q2", "Gemini", "mac"),
        ("assistant", "a2", "Gemini", "mac"),
    ]


def test_private_turns_only_replay_to_private_assistants(
    memory: Memory, registry: Registry
) -> None:
    s = memory.get_or_create_session("me")
    memory.record_exchange(
        s, user_text="public q", reply="public a", assistant=registry.get("claude")
    )
    memory.record_exchange(
        s, user_text="unlock the door", reply="done", assistant=registry.get("local")
    )
    public = memory.history(s, include_private=False)
    assert [t.content for t in public] == ["public q", "public a"]
    everything = memory.history(s, include_private=True)
    assert [t.content for t in everything] == ["public q", "public a", "unlock the door", "done"]
    assert [t.private for t in everything] == [False, False, True, True]


def test_history_limit_keeps_most_recent(
    memory: Memory, registry: Registry, clock: FakeClock
) -> None:
    s = memory.get_or_create_session("me")
    for i in range(5):
        memory.record_exchange(
            s, user_text=f"q{i}", reply=f"a{i}", assistant=registry.get("claude")
        )
        clock.advance(seconds=1)
    turns = memory.history(s, include_private=False)  # replay_turns=6 in the fixture
    assert [t.content for t in turns] == ["q2", "a2", "q3", "a3", "q4", "a4"]


def test_summarization_window(memory: Memory, registry: Registry, clock: FakeClock) -> None:
    s = memory.get_or_create_session("me")
    assert memory.turns_to_summarize(s) == []
    for i in range(6):  # 12 turns > summarize_after_turns=10
        who = "local" if i == 1 else "claude"
        memory.record_exchange(s, user_text=f"q{i}", reply=f"a{i}", assistant=registry.get(who))
        clock.advance(seconds=1)
    to_fold = memory.turns_to_summarize(s)
    # the oldest 12-6=6 turns, minus the private pair from exchange 1
    assert [t.content for t in to_fold] == ["q0", "a0", "q2", "a2"]
    assert all(not t.private for t in to_fold)

    s = memory.apply_summary(s, "They talked about q0 and q2.", to_fold)
    assert s.summary == "They talked about q0 and q2."
    remaining = memory.history(s, include_private=True, limit=100)
    assert "q0" not in [t.content for t in remaining]
    assert "q1" in [t.content for t in remaining]  # private turn never summarized
    assert memory.turns_to_summarize(s) == []


def test_get_session(memory: Memory) -> None:
    s = memory.get_or_create_session("me")
    assert memory.get_session(s.id).user_id == "me"
    assert memory.get_session("nope") is None
