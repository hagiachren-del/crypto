"""Decide which assistant a request is for, in this order:

1. Client hint (`assistant=<name>` in the request).
2. A vocative at the start of the text, which overrides the hint. Only at the start:
   `(hey|ok|okay|yo)? <name>[,:—-]?`, `ask <name> (to)?`, `switch to <name>`, `talk to <name>`.
   Names and mishears match fuzzily at `fuzzy_threshold` when there is a cue (greeting, ask,
   switch/talk to, or a separator after the name). With no cue the word must be an exact name
   or mishear, so "cloudy skies ahead" does not route to Claude. Names listed in
   `plain_words` always need a cue.
3. Sticky: the assistant that answered this session within `sticky_minutes`.
4. `default_assistant`.

A name is never matched mid-sentence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

from router.registry import Assistant, Registry, normalize_name

Source = Literal["hint", "vocative", "sticky", "default"]

_GREETING = re.compile(r"^(?:hey|ok|okay|yo)[,!]?\s+", re.IGNORECASE)
_ASK = re.compile(r"^ask\s+", re.IGNORECASE)
_SWITCH = re.compile(r"^(?:switch|talk)\s+to\s+", re.IGNORECASE)
_WORD = re.compile(r"[a-z0-9']+", re.IGNORECASE)
_WS = re.compile(r"\s*")
_SEPARATOR_AFTER = re.compile(r"^\s*[,:;.!?—–-]")
_LEADING_JUNK = re.compile(r"^[\s,:;.!?—–-]+")
_MAX_NAME_WORDS = 3


class UnknownAssistantError(ValueError):
    pass


@dataclass(frozen=True)
class VocativeMatch:
    assistant: Assistant
    matched: str  # the words in the text that matched
    name: str  # the registry name or mishear they matched
    score: float
    cue: str  # greeting | ask | switch | separator | exact
    rest: str  # the query with the vocative stripped


@dataclass(frozen=True)
class Resolution:
    assistant: Assistant
    text: str
    source: Source
    bare_switch: bool = False
    match: VocativeMatch | None = None


def name_score(candidate: str, name: str) -> float:
    """0..100. Indel ratio catches insertions; Jaro-Winkler catches the one-letter
    substitutions ASR produces in short names ("jarvus")."""
    a, b = normalize_name(candidate), normalize_name(name)
    if not a or not b:
        return 0.0
    if a == b or a.replace(" ", "") == b.replace(" ", ""):
        return 100.0
    return max(
        fuzz.ratio(a, b),
        fuzz.ratio(a.replace(" ", ""), b.replace(" ", "")),
        JaroWinkler.normalized_similarity(a, b) * 100,
    )


def find_vocative(text: str, registry: Registry) -> VocativeMatch | None:
    s = text.strip()
    if not s:
        return None

    cue: str | None = None
    pos = 0
    if m := _GREETING.match(s):
        cue, pos = "greeting", m.end()
    elif m := _ASK.match(s):
        cue, pos = "ask", m.end()
    elif m := _SWITCH.match(s):
        cue, pos = "switch", m.end()

    # up to three word tokens right after the prefix, separated by whitespace only
    tokens: list[re.Match[str]] = []
    scan = pos
    while len(tokens) < _MAX_NAME_WORDS:
        ws = _WS.match(s, scan)
        assert ws is not None
        m = _WORD.match(s, ws.end())
        if m is None:
            break
        tokens.append(m)
        scan = m.end()
    if not tokens:
        return None

    best: tuple[float, int, str, str, int] | None = None  # score, n_words, matched, name, end
    for n in range(1, len(tokens) + 1):
        start, end = tokens[0].start(), tokens[n - 1].end()
        candidate = s[start:end]
        for name in registry.names_index():
            score = name_score(candidate, name)
            if best is None or (score, n) > (best[0], best[1]):
                best = (score, n, candidate, name, end)
    if best is None:
        return None
    score, _, matched, name, end = best

    after = s[end:]
    separator = bool(_SEPARATOR_AFTER.match(after)) or after == ""
    if after and not (after[0].isspace() or _SEPARATOR_AFTER.match(after)):
        return None  # the name runs straight into more letters, e.g. "claude's"

    exact = score >= 100.0
    has_cue = cue is not None or (separator and after != "")
    plain = registry.is_plain_word(name)

    if exact and (has_cue or not plain):
        matched_cue = cue or ("separator" if separator and after else "exact")
    elif has_cue and score >= registry.fuzzy_threshold:
        matched_cue = cue or "separator"
    else:
        return None

    rest = _LEADING_JUNK.sub("", after)
    if cue == "ask":
        rest = re.sub(r"^to\b\s*", "", rest, flags=re.IGNORECASE)
    key = registry.names_index()[normalize_name(name)]
    return VocativeMatch(
        assistant=registry.get(key),
        matched=matched,
        name=name,
        score=score,
        cue=matched_cue,
        rest=rest.strip(),
    )


def resolve(
    text: str,
    registry: Registry,
    *,
    hint: str | None = None,
    sticky: str | None = None,
) -> Resolution:
    """Apply hint → vocative → sticky → default. Raises UnknownAssistantError for a hint
    that names nothing in the registry."""
    hinted: Assistant | None = None
    if hint:
        hinted = registry.lookup(hint)
        if hinted is None:
            raise UnknownAssistantError(f"unknown assistant {hint!r}")

    if match := find_vocative(text, registry):
        return Resolution(
            assistant=match.assistant,
            text=match.rest,
            source="vocative",
            bare_switch=match.rest == "",
            match=match,
        )

    cleaned = text.strip()
    if hinted is not None:
        return Resolution(hinted, cleaned, "hint")
    if sticky and sticky in registry.assistants:
        return Resolution(registry.get(sticky), cleaned, "sticky")
    return Resolution(registry.default, cleaned, "default")
