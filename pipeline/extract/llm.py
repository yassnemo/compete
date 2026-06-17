"""Provider-agnostic LLM extraction client.

The only "agentic" behaviour in the system lives here: extract a structured
``Signal`` from page content, enforced by ``instructor``/Pydantic, with an
explicit **validation-retry loop** - on a schema failure we retry once, feeding
the validation error back to the model.

Providers (swappable via ``COMPETE_LLM_PROVIDER``):
  * ``gemini`` - Google Gemini Flash (default; needs GOOGLE_API_KEY)
  * ``groq``   - Llama 3.3 70B on Groq (needs GROQ_API_KEY)
  * ``ollama`` - any local model via the OpenAI-compatible endpoint
  * ``mock``   - deterministic, no network/key; powers tests and offline demos

Every call's token usage is returned so the runner can log it for cost tracking.
"""

from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import ValidationError

from pipeline.config import Settings, get_settings
from pipeline.logging_setup import get_logger
from pipeline.schemas import Signal, SignalType

log = get_logger(__name__)

try:  # instructor raises this when retries are exhausted
    from instructor.exceptions import InstructorRetryException

    _VALIDATION_ERRORS: tuple[type[Exception], ...] = (ValidationError, InstructorRetryException)
except Exception:  # pragma: no cover
    _VALIDATION_ERRORS = (ValidationError,)


SYSTEM_PROMPT = (
    "You are a competitive-intelligence analyst. From the provided web content "
    "about a competitor, extract exactly ONE structured signal. Be precise and "
    "conservative - do not invent facts not present in the text.\n"
    "Rules:\n"
    "- Choose the single best `signal_type`.\n"
    "- `summary` must be at most two sentences.\n"
    "- `significance` is 1 (trivial) to 5 (major strategic move).\n"
    "- `confidence` is your certainty from 0 to 1.\n"
    "- `entities` lists concrete products, people, or organizations mentioned."
)


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ExtractionResult:
    signal: Signal
    usage: TokenUsage
    attempts: int


class ExtractionError(RuntimeError):
    """Raised when extraction fails after the retry."""


def build_messages(
    text: str, signal_hint: SignalType | None, competitor: str, max_chars: int
) -> list[dict[str, str]]:
    hint = f" The source URL suggests this may be a '{signal_hint}'." if signal_hint else ""
    content = (text or "").strip()[:max_chars]
    user = (
        f"Competitor: {competitor}.{hint}\n\n"
        f'Content:\n"""\n{content}\n"""\n\n'
        "Extract the single best signal as the structured schema."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


class LLMClient(ABC):
    """Base client implementing the shared retry loop."""

    provider: str = "base"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.model = self.settings.llm_model

    @abstractmethod
    def _complete(
        self, messages: list[dict[str, str]], signal_hint: SignalType | None
    ) -> tuple[Signal, TokenUsage]:
        """Single model call returning a validated Signal + usage (no retry)."""

    def extract_signal(
        self, text: str, signal_hint: SignalType | None, competitor: str
    ) -> ExtractionResult:
        messages = build_messages(text, signal_hint, competitor, self.settings.llm_max_input_chars)
        last_err: Exception | None = None
        for attempt in (1, 2):
            try:
                signal, usage = self._complete(messages, signal_hint)
                return ExtractionResult(signal=signal, usage=usage, attempts=attempt)
            except _VALIDATION_ERRORS as exc:
                last_err = exc
                log.warning("extraction validation failed (attempt %d): %s", attempt, exc)
                messages = [
                    *messages,
                    {
                        "role": "user",
                        "content": (
                            f"Your previous response failed schema validation: {exc}. "
                            "Return a corrected object that matches the schema exactly."
                        ),
                    },
                ]
        raise ExtractionError(f"extraction failed after retry: {last_err}")


# --------------------------------------------------------------------------- #
# Real providers (instructor-backed). Verified path in this repo is `mock`;
# these are exercised when the matching API key / endpoint is configured.
# --------------------------------------------------------------------------- #
class GeminiClient(LLMClient):
    provider = "gemini"

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(settings)
        if not self.settings.google_api_key:
            raise ExtractionError("GOOGLE_API_KEY not set (required for provider=gemini).")
        import google.generativeai as genai
        import instructor

        genai.configure(api_key=self.settings.google_api_key)
        model = genai.GenerativeModel(self.model)
        self._client = instructor.from_gemini(model, mode=instructor.Mode.GEMINI_JSON)

    def _complete(self, messages, signal_hint):
        signal, completion = self._client.chat.completions.create_with_completion(
            messages=messages, response_model=Signal, max_retries=0
        )
        meta = getattr(completion, "usage_metadata", None)
        usage = TokenUsage(
            prompt_tokens=getattr(meta, "prompt_token_count", 0) or 0,
            completion_tokens=getattr(meta, "candidates_token_count", 0) or 0,
            total_tokens=getattr(meta, "total_token_count", 0) or 0,
        )
        return signal, usage


class GroqClient(LLMClient):
    provider = "groq"

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(settings)
        if not self.settings.groq_api_key:
            raise ExtractionError("GROQ_API_KEY not set (required for provider=groq).")
        import instructor
        from groq import Groq

        self._client = instructor.from_groq(
            Groq(api_key=self.settings.groq_api_key), mode=instructor.Mode.JSON
        )

    def _complete(self, messages, signal_hint):
        signal, completion = self._client.chat.completions.create_with_completion(
            model=self.model, messages=messages, response_model=Signal, max_retries=0
        )
        usage = _openai_usage(completion)
        return signal, usage


class OllamaClient(LLMClient):
    provider = "ollama"

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(settings)
        import instructor
        from openai import OpenAI

        self.model = self.settings.ollama_model
        oai = OpenAI(base_url=self.settings.ollama_base_url, api_key="ollama")
        self._client = instructor.from_openai(oai, mode=instructor.Mode.JSON)

    def _complete(self, messages, signal_hint):
        signal, completion = self._client.chat.completions.create_with_completion(
            model=self.model, messages=messages, response_model=Signal, max_retries=0
        )
        usage = _openai_usage(completion)
        return signal, usage


def _openai_usage(completion: object) -> TokenUsage:
    usage = getattr(completion, "usage", None)
    return TokenUsage(
        prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
        completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
        total_tokens=getattr(usage, "total_tokens", 0) or 0,
    )


# --------------------------------------------------------------------------- #
# Mock provider - deterministic heuristic extraction. No network, no key.
# --------------------------------------------------------------------------- #
_KEYWORDS: list[tuple[SignalType, tuple[str, ...]]] = [
    (SignalType.PRICING_CHANGE, ("pricing", "price", "/mo", "per month", "subscription", "$")),
    (SignalType.FUNDING_NEWS, ("raised", "funding", "series ", "valuation", "investment")),
    (SignalType.LEADERSHIP_CHANGE, ("ceo", "cfo", "cto", "appoints", "joins as", "steps down")),
    (SignalType.JOB_POSTING, ("hiring", "job", "role", "apply", "engineer", "remote")),
    (
        SignalType.PRODUCT_LAUNCH,
        ("launch", "introducing", "announc", "new model", "release", "now available"),
    ),
    (SignalType.PRESS_RELEASE, ("press", "newsroom", "media")),
    (SignalType.BLOG_POST, ("blog", "post", "read more", "tutorial")),
]
_HIGH_SIG = ("acqui", "raised", "launch", "partnership", "valuation", "ceo")


class MockClient(LLMClient):
    """Deterministic, offline heuristic extractor (great for tests/demos)."""

    provider = "mock"

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(settings)
        self.model = "mock-1"

    def _complete(self, messages, signal_hint):
        text = messages[-1]["content"]
        signal = self._heuristic(text, signal_hint)
        usage = TokenUsage(
            prompt_tokens=max(1, len(text) // 4),
            completion_tokens=40,
            total_tokens=max(1, len(text) // 4) + 40,
        )
        return signal, usage

    @staticmethod
    def _heuristic(text: str, signal_hint: SignalType | None) -> Signal:
        low = text.lower()
        signal_type = signal_hint
        if signal_type is None:
            for st, kws in _KEYWORDS:
                if any(k in low for k in kws):
                    signal_type = st
                    break
        signal_type = signal_type or SignalType.OTHER

        # Title: first meaningful line of the quoted content.
        body = text
        m = re.search(r'"""\n(.*?)\n"""', text, re.DOTALL)
        if m:
            body = m.group(1)
        first_line = next((ln.strip() for ln in body.splitlines() if ln.strip()), "Untitled")
        title = first_line[:140]
        summary = " ".join(body.split())[:280] or title
        significance = 4 if any(k in low for k in _HIGH_SIG) else 2
        entities = _capitalized_entities(body)
        return Signal(
            signal_type=signal_type,
            title=title,
            summary=summary,
            entities=entities,
            significance=significance,
            confidence=0.6,
        )


_CAP = re.compile(r"\b([A-Z][a-zA-Z0-9]+(?:\s[A-Z][a-zA-Z0-9]+){0,2})\b")


def _capitalized_entities(text: str, limit: int = 5) -> list[str]:
    seen: dict[str, None] = {}
    for match in _CAP.findall(text):
        if len(match) > 2:
            seen.setdefault(match, None)
        if len(seen) >= limit:
            break
    return list(seen.keys())


_PROVIDERS: dict[str, type[LLMClient]] = {
    "gemini": GeminiClient,
    "groq": GroqClient,
    "ollama": OllamaClient,
    "mock": MockClient,
}


def get_llm_client(
    settings: Settings | None = None, provider_override: str | None = None
) -> LLMClient:
    s = settings or get_settings()
    provider = (provider_override or s.llm_provider).lower()
    cls = _PROVIDERS.get(provider)
    if cls is None:
        raise ExtractionError(
            f"Unknown LLM provider '{provider}'. Choose: {', '.join(_PROVIDERS)}."
        )
    return cls(s)


def now_ms() -> int:
    return int(time.time() * 1000)
