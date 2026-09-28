"""System prompt assembly: the shared voice-hygiene prompt, the persona prompt (appended), a
line about who else is in the room, and the session summary."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from router.registry import Assistant, Registry

FALLBACK_VOICE_PROMPT = (
    "You are {assistant_name}. Your reply is spoken aloud: at most two sentences unless asked "
    "for more, no markdown or lists, numbers written the way they are said. Earlier replies in "
    "the transcript are labelled with the speaker's name; do not label your own."
)


@lru_cache(maxsize=32)
def _read(path: str) -> str:
    return Path(path).read_text().strip()


def read_prompt(path: Path | str) -> str:
    return _read(str(path))


def build_system_prompt(
    assistant: Assistant,
    registry: Registry,
    *,
    prompts_dir: Path | str = "prompts",
    summary: str | None = None,
) -> str:
    prompts_dir = Path(prompts_dir)
    voice_file = prompts_dir / "voice.md"
    template = read_prompt(voice_file) if voice_file.exists() else FALLBACK_VOICE_PROMPT
    parts = [template.replace("{assistant_name}", assistant.display_name)]

    others = [
        a.display_name
        for a in registry.assistants.values()
        if a.key != assistant.key and a.kind == "model" and not a.base
    ]
    if others:
        parts.append(
            "The user also talks to these assistants, whose earlier replies you may see in the "
            "transcript: " + ", ".join(others) + "."
        )

    if assistant.system_prompt:
        persona = Path(assistant.system_prompt)
        if not persona.is_absolute() and not persona.exists():
            persona = prompts_dir.parent / assistant.system_prompt
        parts.append(read_prompt(persona))

    if summary:
        parts.append("Summary of the conversation so far:\n" + summary.strip())

    return "\n\n".join(parts)
