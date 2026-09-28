"""One voice request end to end: router commands, session, resolution, the `auto` classifier,
`council` fan-out, the answer, and memory bookkeeping."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from router.llm import Message, Provider, ProviderError, merge_consecutive
from router.memory import ConversationSession, Memory, Turn
from router.prompts import build_system_prompt
from router.registry import Assistant, Registry, RegistryHolder
from router.resolver import resolve
from router.settings import Config

log = logging.getLogger(__name__)

_NEW_CONVERSATION = re.compile(
    r"^(?:(?:hey|ok|okay)\W+)?(?:start\s+(?:a\s+)?)?new\s+(?:conversation|chat|session)\W*$",
    re.IGNORECASE,
)
_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


@dataclass(frozen=True)
class VoiceRequest:
    text: str
    user_id: str
    device_id: str | None = None
    assistant: str | None = None  # client hint
    device_voice: bool = False  # client speaks with the device's own voice


@dataclass(frozen=True)
class VoiceResult:
    reply: str
    assistant: str
    assistant_name: str
    session_id: str
    routed_by: str  # hint | vocative | sticky | default | auto | command
    announce: bool
    audio_url: str | None = None


class EmptyRequestError(ValueError):
    pass


class Engine:
    def __init__(
        self,
        *,
        registry: RegistryHolder,
        memory: Memory,
        provider: Provider,
        config: Config,
        prompts_dir: Path | str = "prompts",
    ) -> None:
        self.holder = registry
        self.memory = memory
        self.provider = provider
        self.config = config
        self.prompts_dir = Path(prompts_dir)

    @property
    def registry(self) -> Registry:
        return self.holder.registry

    # -- entry point -----------------------------------------------------------------------
    async def handle(self, req: VoiceRequest) -> VoiceResult:
        text = req.text.strip()
        if not text:
            raise EmptyRequestError("text is empty")
        registry = self.registry

        if _NEW_CONVERSATION.match(text):
            self.memory.end_session(req.user_id)
            session = self.memory.get_or_create_session(req.user_id)
            return self._result(
                "Okay, new conversation.", registry.default, session, "command", False, req
            )

        session = self.memory.get_or_create_session(req.user_id)
        previous = session.last_assistant
        sticky = self.memory.sticky_assistant(session, registry.sticky_minutes)
        res = resolve(text, registry, hint=req.assistant, sticky=sticky)

        if res.bare_switch:
            reply = f"{res.assistant.display_name} here."
            session = self.memory.record_exchange(
                session,
                user_text=text,
                reply=reply,
                assistant=res.assistant,
                device_id=req.device_id,
            )
            return self._result(reply, res.assistant, session, "vocative", False, req)

        target, query, routed_by = res.assistant, res.text, str(res.source)
        if target.router:
            target, query = await self.classify(query, registry)
            routed_by = "auto"

        if target.council:
            reply = await self.run_council(target, query, session, registry)
        else:
            reply = await self.answer(target, query, session, registry)

        announce = routed_by == "auto" or (previous is not None and previous != target.key)
        session = self.memory.record_exchange(
            session, user_text=query, reply=reply, assistant=target, device_id=req.device_id
        )
        await self.summarize_if_needed(session)
        return self._result(reply, target, session, routed_by, announce, req)

    def _result(
        self,
        reply: str,
        assistant: Assistant,
        session: ConversationSession,
        routed_by: str,
        announce: bool,
        req: VoiceRequest,
    ) -> VoiceResult:
        if req.device_voice and announce:
            # the client speaks with the device's own voice, so say who is answering
            reply = f"{assistant.display_name}. {reply}"
        return VoiceResult(
            reply=reply,
            assistant=assistant.key,
            assistant_name=assistant.display_name,
            session_id=session.id,
            routed_by=routed_by,
            announce=announce,
        )

    # -- answering -------------------------------------------------------------------------
    def build_messages(
        self,
        assistant: Assistant,
        query: str,
        session: ConversationSession,
        registry: Registry,
    ) -> list[Message]:
        system = build_system_prompt(
            assistant, registry, prompts_dir=self.prompts_dir, summary=session.summary
        )
        history = self.memory.history(session, include_private=assistant.private)
        messages: list[Message] = [{"role": "system", "content": system}]
        for t in history:
            messages.append(_turn_to_message(t))
        messages.append({"role": "user", "content": query})
        return merge_consecutive(messages)

    async def answer(
        self,
        assistant: Assistant,
        query: str,
        session: ConversationSession,
        registry: Registry,
    ) -> str:
        if not assistant.model:
            raise ProviderError(f"{assistant.key} has no model")
        messages = self.build_messages(assistant, query, session, registry)
        reply = await self.provider.complete(assistant.model, messages)
        return clean_reply(reply, assistant.display_name)

    # -- auto ------------------------------------------------------------------------------
    async def classify(self, query: str, registry: Registry) -> tuple[Assistant, str]:
        """Ask the cheap model which assistant should answer. Falls back to the default."""
        candidates = [a for a in registry.assistants.values() if a.kind == "model"]
        default = registry.default
        lines = []
        for a in candidates:
            traits = []
            if a.search:
                traits.append("has web search for live information")
            if a.image:
                traits.append("can generate images")
            if a.private:
                traits.append("runs locally: smart home and anything private go here")
            if a.base:
                traits.append(f"persona on top of {a.base}")
            if a.key == self.config.auto.cheapest:
                traits.append("cheapest: trivial facts go here")
            detail = f" ({'; '.join(traits)})" if traits else ""
            lines.append(f"- {a.key}: {a.display_name}{detail}")
        prompt = (
            "You route a spoken request to one assistant. Rules: coding, reasoning and writing "
            f"go to {default.key}; live or recent information goes to an assistant with web "
            "search; image generation to one that can generate images; smart-home commands or "
            "anything private to the local one; trivial facts to the cheapest. Remove any "
            "leading name or greeting from the request. Reply with JSON only: "
            '{"target": "<key>", "cleaned_query": "<request>", "confidence": <0..1>}.\n\n'
            "Assistants:\n" + "\n".join(lines)
        )
        messages: list[Message] = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": query},
        ]
        try:
            raw = await self.provider.complete(self.config.models.classifier, messages)
            pick = _parse_json(raw)
            target = registry.lookup(str(pick.get("target", "")))
            confidence = float(pick.get("confidence", 0))
            cleaned = str(pick.get("cleaned_query") or query).strip() or query
        except (ProviderError, ValueError, TypeError) as e:
            log.warning("auto classifier failed (%s); using default", e)
            return default, query
        if target is None or target.kind != "model" or confidence < self.config.auto.min_confidence:
            return default, query
        return target, cleaned

    # -- council ---------------------------------------------------------------------------
    async def run_council(
        self,
        council: Assistant,
        query: str,
        session: ConversationSession,
        registry: Registry,
    ) -> str:
        members = [registry.get(k) for k in council.council]
        if not all(m.private for m in members):
            members = [m for m in members if not m.private]

        async def ask(member: Assistant) -> str | BaseException:
            try:
                return await self.answer(member, query, session, registry)
            except ProviderError as e:
                return e

        results = await asyncio.gather(*(ask(m) for m in members))
        paired = list(zip(members, results, strict=True))
        answers = [(m, r) for m, r in paired if isinstance(r, str)]
        failed = [m.display_name for m, r in paired if not isinstance(r, str)]
        if not answers:
            raise ProviderError("every council member failed: " + ", ".join(failed))

        synth_key = council.synthesizer or members[0].key
        synth = registry.get(synth_key)
        if not synth.model:
            raise ProviderError(f"synthesizer {synth_key} has no model")
        system = build_system_prompt(
            synth, registry, prompts_dir=self.prompts_dir, summary=session.summary
        )
        system += (
            "\n\nYou are answering on behalf of a council. Combine the members' answers below "
            "into one short spoken answer. If they disagree, say in one sentence who says what. "
            "Do not list them one by one."
        )
        body = f"The user asked: {query}\n\n" + "\n\n".join(
            f"{m.display_name} answered: {r}" for m, r in answers
        )
        if failed:
            body += "\n\nDid not answer: " + ", ".join(failed)
        reply = await self.provider.complete(
            synth.model,
            [{"role": "system", "content": system}, {"role": "user", "content": body}],
        )
        return clean_reply(reply, synth.display_name)

    # -- summaries -------------------------------------------------------------------------
    async def summarize_if_needed(self, session: ConversationSession) -> bool:
        turns = self.memory.turns_to_summarize(session)
        if not turns:
            return False
        transcript = "\n".join(
            f"{'User' if t.role == 'user' else (t.assistant_name or 'Assistant')}: {t.content}"
            for t in turns
        )
        prior = f"Previous summary:\n{session.summary}\n\n" if session.summary else ""
        messages: list[Message] = [
            {
                "role": "system",
                "content": (
                    "Summarize this conversation for an assistant that will continue it. Keep "
                    "facts, decisions, names, preferences and open questions. Plain prose, at "
                    "most one hundred and fifty words. Merge the previous summary if given."
                ),
            },
            {"role": "user", "content": prior + transcript},
        ]
        try:
            summary = await self.provider.complete(self.config.models.summarizer, messages)
        except ProviderError as e:
            log.warning("summarizer failed: %s", e)
            return False
        self.memory.apply_summary(session, summary, turns)
        return True


def _turn_to_message(t: Turn) -> Message:
    if t.role == "user":
        return {"role": "user", "content": t.content}
    label = t.assistant_name or "Assistant"
    return {"role": "assistant", "content": f"{label}: {t.content}"}


def clean_reply(reply: str, display_name: str) -> str:
    """Strip a self-label ("Claude: ...") the model may have copied from the transcript."""
    s = reply.strip()
    prefix = re.compile(rf"^\s*\[?{re.escape(display_name)}\]?\s*[:\-—]\s*", re.IGNORECASE)
    s = prefix.sub("", s, count=1)
    return s.strip()


def _parse_json(raw: str) -> dict:
    m = _JSON_OBJECT.search(raw)
    if not m:
        raise ValueError(f"no JSON object in classifier reply: {raw[:120]!r}")
    data = json.loads(m.group(0))
    if not isinstance(data, dict):
        raise ValueError("classifier reply is not an object")
    return data
