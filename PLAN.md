# voice-router — build plan

One self-hosted FastAPI service that every device talks to. Names live in `assistants.yaml`,
memory lives in SQLite, providers go through LiteLLM. This document is the file layout, the
model IDs I chose, the decisions I made where the spec left room, and the questions I have.

## File layout

```
.
├── PLAN.md                      # this file
├── pyproject.toml               # uv project; `router` CLI entry point
├── assistants.yaml              # THE registry (names, mishears, models, voices, personas)
├── config.yaml                  # everything that is not a name: utility model IDs, memory
│                                # windows, STT/TTS settings, server bind address
├── .env.example                 # device tokens + provider API keys (copy to .env)
├── prompts/
│   ├── voice.md                 # shared "spoken aloud" system prompt
│   └── coach.md                 # persona prompt for `coach`
├── router/
│   ├── settings.py              # pydantic-settings: paths, tokens; loads config.yaml
│   ├── registry.py              # assistants.yaml loader, validation, inheritance, file watch
│   ├── resolver.py              # hint → vocative → sticky → default
│   ├── memory.py                # SQLModel: sessions, turns, summaries, private flag
│   ├── llm.py                   # LiteLLM adapter behind a Provider protocol (mockable)
│   ├── prompts.py               # system-prompt assembly (voice hygiene + persona + summary)
│   ├── engine.py                # one request end to end: commands, resolve, auto, council
│   ├── auth.py                  # per-device bearer tokens
│   ├── app.py                   # FastAPI app factory + /voice          (slice 1)
│   ├── audio.py                 # faster-whisper / OpenAI STT, per-assistant TTS (slice 2)
│   ├── streaming.py             # sentence chunker + SSE                 (slice 2)
│   ├── openai_compat.py         # /v1/chat/completions                  (slice 4)
│   ├── names.py                 # voice name commands + /names API      (slice 7)
│   ├── sync.py                  # regenerate client artifacts            (slices 5, 7)
│   └── cli.py                   # `router serve|names|listen`
├── static/app.html              # the PWA                                (slice 3)
├── shortcuts/                   # Router recipe, wrapper generator, README (slice 5)
├── listener/                    # Mac always-on listener + launchd plist  (slice 6)
├── wakewords/                   # trained openWakeWord models             (slice 6)
├── data/                        # SQLite db + generated audio (gitignored)
└── tests/
    ├── conftest.py              # FakeProvider, temp registry, temp db, app client
    ├── test_registry.py
    ├── test_resolver.py         # table-driven, ~35 utterances
    ├── test_memory.py
    ├── test_engine.py           # auto, council, bare switch, announce flag
    └── test_voice_api.py
```

The repo currently holds only a README for an unrelated trading-platform stub. I built at the
repo root and left that README untouched. See question 1.

## Model IDs (looked up 2026-09-28)

| Role | ID | Why |
|---|---|---|
| `claude` | `anthropic/claude-sonnet-5` | Current Sonnet. |
| `gpt` | `openai/gpt-6-sol` | GPT-6 line. Sol is the mid-tier "balances intelligence and cost" model, the Sonnet-equivalent. `gpt-6-astra` is the flagship, `gpt-6-luna` the cheap one. See question 2. |
| `gemini` | `gemini/gemini-3.8-flash` | Current stable general-purpose Gemini. `gemini-3.1-pro-preview` exists but is preview. |
| `local` | `ollama/gemma3:12b` | Fits a Mac, no thinking-tag noise in spoken replies. Change to taste. |
| classifier (`auto`) | `anthropic/claude-haiku-4-5` | Haiku-class, current generation. |
| summarizer | `anthropic/claude-haiku-4-5` | Same. |
| TTS | OpenAI `gpt-4o-mini-tts`, voices `onyx` / `nova` / `shimmer` | All three voices are in the current voice list. |
| STT fallback | OpenAI `gpt-4o-mini-transcribe` | Local `faster-whisper` first. |
| image generation | `gemini/gemini-3.1-flash-image` | Only referenced by the auto classifier. |

Assistant models live in `assistants.yaml` (spec section 1). Utility models live in
`config.yaml`. Nothing is hardcoded in Python.

## Decisions I made (say so if you want them changed)

1. **Bare vocative needs an exact hit.** With a cue (a greeting, `ask`, `switch to`, `talk to`,
   or a comma/colon after the name) names and mishears match fuzzily at `fuzzy_threshold`.
   With no cue, the first word must equal a name or mishear exactly. Otherwise "cloudy skies
   ahead" scores 91 against "cloud" and routes to Claude. The mishear list is what makes the
   bare form reliable, which is what it is for.
2. **Plain-word names** are a top-level `plain_words:` list in `assistants.yaml` (default:
   `local, house, coach, google, everyone, assistant, router, auto`). Those need a cue.
3. **Any vocative with nothing after it is a bare switch** ("Hey Gemini" and "switch to
   Gemini" both reply "Gemini here." and set stickiness), not only `switch to`.
4. **Display names** come from an optional `display_name` (default: first name capitalised),
   so GPT reads "GPT" not "Gpt".
5. **`announce`**: the response carries `announce: true` when routing was by the classifier
   or the answering assistant differs from the one that answered last in this session. A
   client that speaks with the device voice sends `device_voice: true` and the server then
   prefixes the reply text itself, so Shortcuts needs no branching.
6. **Private turns** flag both the user's utterance and the reply when a `private: true`
   assistant answers. They never go into summaries and are only replayed to private assistants.
7. **Memory replay** labels every earlier assistant turn `Name: text` in the assistant role and
   the system prompt says not to label your own reply. A leading `Name:` is stripped from
   output defensively.
8. **"new conversation"** is handled in slice 1 because memory (section 3) needs it. The rest
   of the voice commands are slice 7.
9. **Auth**: `ROUTER_TOKENS=iphone:token1,mac:token2` in `.env`. With no tokens configured the
   service starts open and logs a loud warning, for first-run on Tailscale.
10. **Council** fans out with `asyncio.gather`, synthesizes with the council's first member
    unless `synthesizer:` is set on the entry. Private members are excluded from the fan-out
    unless every member is private.
11. **Per-assistant flags for the classifier**: `search: true` and `image: true` on entries;
    `config.yaml` names `auto.cheapest`.

## Questions for you

1. The repo is named `crypto` and its README describes a trading platform. Fine to keep
   building at the root, or do you want this under `voice-router/` (or a new repo)?
2. GPT: Sol (mid tier, faster) or Astra (flagship, slower)? Either is a one-line change.
3. Ollama model: `gemma3:12b` is a guess at what your Mac runs. What do you actually have
   pulled?
4. Do you have an OpenAI key you want used for TTS/STT fallback, or should local TTS
   (e.g. macOS `say` / Kokoro) be the default with OpenAI optional? Slice 2 assumes OpenAI TTS.
5. `user_id`: a single user is assumed. Is there ever more than one person, or can every
   device default to one `user_id` (`ROUTER_DEFAULT_USER=hagi`)?

## Build order

1. Registry + validation, resolver with table-driven tests, memory, `/voice` text-only,
   LiteLLM adapter with mocked providers. **(this commit)**
2. Audio: faster-whisper transcription, per-assistant TTS, `/tts`, SSE streaming.
3. `/app` PWA.
4. `/v1/chat/completions` with streaming.
5. Apple Shortcuts: Router recipe, wrapper generator + signing, `shortcuts/README.md`.
6. `router listen` for Mac + launchd plist + `listener/README.md`.
7. Name management by voice, `/names` API, CLI, sync.

## Running

```
uv sync
cp .env.example .env            # add tokens and provider keys
uv run router serve             # http://0.0.0.0:8787
uv run pytest                   # no network, providers are mocked
```
