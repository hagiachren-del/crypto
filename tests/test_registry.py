from __future__ import annotations

import asyncio
import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from router.registry import Registry, RegistryError, RegistryHolder, normalize_name

from .conftest import ASSISTANTS_FILE


def test_shipped_registry_loads(registry: Registry) -> None:
    assert registry.default_assistant == "claude"
    assert set(registry.assistants) == {
        "claude",
        "gpt",
        "gemini",
        "local",
        "auto",
        "council",
        "coach",
    }
    assert registry.sticky_minutes == 10
    assert registry.fuzzy_threshold == 85


def test_display_names(registry: Registry) -> None:
    assert registry.get("claude").display_name == "Claude"
    assert registry.get("gpt").display_name == "GPT"
    assert registry.get("gemini").display_name == "Gemini"
    assert registry.get("coach").display_name == "Coach"


def test_persona_inherits_from_base(registry: Registry) -> None:
    coach, claude = registry.get("coach"), registry.get("claude")
    assert coach.base == "claude"
    assert coach.model == claude.model
    assert coach.voice == claude.voice
    assert coach.tools == ("calendar",)  # overridden
    assert coach.system_prompt == "prompts/coach.md"
    assert coach.kind == "model"


def test_kinds_and_flags(registry: Registry) -> None:
    assert registry.get("auto").kind == "router"
    assert registry.get("council").kind == "council"
    assert registry.get("council").council == ("claude", "gpt", "gemini")
    assert registry.get("council").synthesizer == "claude"
    assert registry.get("local").private is True
    assert registry.get("claude").private is False
    assert registry.get("gemini").search is True


def test_lookup_by_key_name_and_mishear(registry: Registry) -> None:
    assert registry.lookup("gpt").key == "gpt"
    assert registry.lookup("Jarvis").key == "claude"
    assert registry.lookup("CLAWED").key == "claude"
    assert registry.lookup("  jeep tea ").key == "gpt"
    assert registry.lookup("nobody") is None
    assert registry.names_index()["g p t"] == "gpt"


def test_plain_words(registry: Registry) -> None:
    assert registry.is_plain_word("local")
    assert registry.is_plain_word("Coach")
    assert not registry.is_plain_word("claude")


def test_normalize_name() -> None:
    assert normalize_name("  Jeep-Tea! ") == "jeep tea"
    assert normalize_name("G P T") == "g p t"


def _mutated(data: dict[str, Any], fn) -> dict[str, Any]:
    d = copy.deepcopy(data)
    fn(d)
    return d


def test_duplicate_name_across_assistants_fails(registry_data: dict[str, Any]) -> None:
    bad = _mutated(registry_data, lambda d: d["assistants"]["gemini"]["names"].append("jarvis"))
    with pytest.raises(RegistryError) as e:
        Registry.from_dict(bad)
    msg = str(e.value)
    assert "jarvis" in msg and "claude" in msg and "gemini" in msg


def test_mishear_colliding_with_name_fails(registry_data: dict[str, Any]) -> None:
    bad = _mutated(registry_data, lambda d: d["assistants"]["gpt"]["mishears"].append("Google"))
    with pytest.raises(RegistryError, match="google"):
        Registry.from_dict(bad)


def test_unknown_default_fails(registry_data: dict[str, Any]) -> None:
    bad = _mutated(registry_data, lambda d: d.update(default_assistant="nobody"))
    with pytest.raises(RegistryError, match="default_assistant"):
        Registry.from_dict(bad)


def test_base_must_exist_and_be_a_model(registry_data: dict[str, Any]) -> None:
    bad = _mutated(registry_data, lambda d: d["assistants"]["coach"].update(base="ghost"))
    with pytest.raises(RegistryError, match="ghost"):
        Registry.from_dict(bad)
    bad = _mutated(registry_data, lambda d: d["assistants"]["coach"].update(base="council"))
    with pytest.raises(RegistryError, match="plain model"):
        Registry.from_dict(bad)

    def chain(d: dict[str, Any]) -> None:
        d["assistants"]["trainer"] = {"base": "coach", "names": ["trainer"]}

    with pytest.raises(RegistryError, match="one level"):
        Registry.from_dict(_mutated(registry_data, chain))


def test_council_members_must_exist(registry_data: dict[str, Any]) -> None:
    bad = _mutated(registry_data, lambda d: d["assistants"]["council"]["council"].append("ghost"))
    with pytest.raises(RegistryError, match="ghost"):
        Registry.from_dict(bad)


def test_exactly_one_kind(registry_data: dict[str, Any]) -> None:
    bad = _mutated(registry_data, lambda d: d["assistants"]["coach"].update(model="x/y"))
    with pytest.raises(RegistryError, match="exactly one"):
        Registry.from_dict(bad)
    bad = _mutated(registry_data, lambda d: d["assistants"]["claude"].pop("model"))
    with pytest.raises(RegistryError, match="exactly one"):
        Registry.from_dict(bad)


def test_missing_names_fails(registry_data: dict[str, Any]) -> None:
    bad = _mutated(registry_data, lambda d: d["assistants"]["gemini"].update(names=[]))
    with pytest.raises(RegistryError, match="names"):
        Registry.from_dict(bad)


def test_load_errors_name_the_file(tmp_path: Path) -> None:
    with pytest.raises(RegistryError, match="not found"):
        Registry.load(tmp_path / "missing.yaml")
    p = tmp_path / "bad.yaml"
    p.write_text("- just\n- a list\n")
    with pytest.raises(RegistryError, match="mapping"):
        Registry.load(p)


def test_holder_keeps_previous_registry_on_bad_edit(
    tmp_path: Path, registry_data: dict[str, Any]
) -> None:
    p = tmp_path / "assistants.yaml"
    p.write_text(yaml.safe_dump(registry_data))
    holder = RegistryHolder(p)
    before = holder.registry
    p.write_text("default_assistant: nobody\nassistants: {}\n")
    assert holder.reload() is False
    assert holder.registry is before

    good = copy.deepcopy(registry_data)
    good["assistants"]["gemini"]["names"].append("bard")
    p.write_text(yaml.safe_dump(good))
    assert holder.reload() is True
    assert holder.registry.lookup("bard").key == "gemini"


async def test_holder_watches_file(tmp_path: Path, registry_data: dict[str, Any]) -> None:
    p = tmp_path / "assistants.yaml"
    p.write_text(yaml.safe_dump(registry_data))
    holder = RegistryHolder(p)
    seen: list[str] = []
    holder.on_reload(lambda r: seen.append(",".join(sorted(r.names_index()))))
    holder.start()
    try:
        await asyncio.sleep(0.3)  # let the watcher arm
        data = copy.deepcopy(registry_data)
        data["assistants"]["gpt"]["names"].append("friday night")
        p.write_text(yaml.safe_dump(data))
        for _ in range(100):
            if seen:
                break
            await asyncio.sleep(0.05)
        assert seen, "watcher did not fire within 5s"
        assert holder.registry.lookup("friday night").key == "gpt"
    finally:
        await holder.stop()


def test_shipped_file_matches_fixture() -> None:
    # The fixture parses the real file; make sure the real file is the one on disk.
    assert ASSISTANTS_FILE.exists()
    Registry.load(ASSISTANTS_FILE)
