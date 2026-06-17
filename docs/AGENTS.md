# Agents & Extraction

`compete` is deliberately **not** an autonomous agent (see ADR 0003). The only
LLM-driven step is **structured extraction**: turning a piece of already-known-
changed web content into one validated `Signal`. This document is the contract
for that step.

## Extraction schema (`pipeline/schemas.py`)

The LLM must return an object matching this Pydantic model, enforced by
[`instructor`](https://python.useinstructor.com/):

```python
class Signal(BaseModel):
    signal_type: SignalType   # pricing_change | product_launch | blog_post |
                              # press_release | job_posting | leadership_change |
                              # funding_news | other
    title: str                # 1-300 chars
    summary: str              # ≤ 2 sentences (≤ 600 chars)
    entities: list[str]       # products / people / orgs (deduped, stripped)
    significance: int         # 1 (trivial) … 5 (major strategic move)
    confidence: float         # 0.0 … 1.0
```

Field constraints are real validators - `significance` outside 1-5 or an empty
`title` raises `ValidationError`, which drives the retry.

## Prompt

System prompt (verbatim source: `pipeline/extract/llm.py:SYSTEM_PROMPT`):

> You are a competitive-intelligence analyst. From the provided web content
> about a competitor, extract exactly ONE structured signal. Be precise and
> conservative - do not invent facts not present in the text. Choose the single
> best `signal_type`; `summary` ≤ two sentences; `significance` 1-5;
> `confidence` 0-1; `entities` lists concrete products/people/organizations.

The user message carries the competitor name, an optional `signal_hint` derived
from the tracked-URL config, and the cleaned page text truncated to
`COMPETE_LLM_MAX_INPUT_CHARS` (default 6000) for cost control.

## Validation-retry loop

`LLMClient.extract_signal` runs at most **two** attempts:

1. Call the model with `response_model=Signal`, `max_retries=0` (our loop owns
   retries, not instructor's).
2. On `ValidationError` / `InstructorRetryException`, append a correction turn
   that includes the exact validation error and ask for a corrected object.
3. Second failure raises `ExtractionError`; the runner logs the failed call and
   moves on (one bad page never aborts a run).

This is unit-tested with a deliberately flaky client
(`tests/test_extract.py::test_retry_loop_recovers_after_validation_error`).

## Provider selection

Set `COMPETE_LLM_PROVIDER`; the client is built by `get_llm_client`:

| Provider | Notes | Key |
|----------|-------|-----|
| `gemini` (default) | Gemini Flash via `instructor.from_gemini` | `GOOGLE_API_KEY` |
| `groq` | Llama 3.3 70B via `instructor.from_groq` | `GROQ_API_KEY` |
| `ollama` | Any local model over the OpenAI-compatible endpoint | none (local) |
| `mock` | Deterministic heuristic extractor - **no network/key** | none |

`mock` is the verified path in this repo: it powers the test suite and lets the
entire pipeline + dashboard be demoed offline. The three real providers share
the same interface and retry loop; they are exercised when the matching
credential/endpoint is present. Override per-run with `compete extract -p groq`.

> Note: `instructor` currently imports the deprecated `google.generativeai`
> package (emits a FutureWarning). A migration to `google-genai` is tracked for
> a later pass; functionality is unaffected.

## Embeddings

`COMPETE_EMBED_PROVIDER` selects the embedder (`pipeline/extract/embeddings.py`):

- **`hashing`** (default) - deterministic signed feature-hashing over word +
  char-trigram features, L2-normalized. Zero dependencies, no network, instant,
  reproducible. Captures lexical overlap well enough to gate minor-vs-real
  changes. This is what keeps the demo free and offline.
- **`minilm`** - sentence-transformers `all-MiniLM-L6-v2` (`uv sync --extra embed`,
  pulls torch). Better semantics for dedup.
- **`gemini`** - `text-embedding-004` via the API (uses `GOOGLE_API_KEY`).

All providers fall back to `hashing` if unavailable, so a run never breaks.

## Cost controls

- **Snapshot-diff gate (ADR 0002):** the LLM only runs on content whose hash is
  new *and* (for updates) whose embedding cosine vs the prior snapshot is below
  `COMPETE_DIFF_SIMILARITY_THRESHOLD` (default 0.9). Unchanged/minor edits never
  reach the model.
- **Idempotency:** a `(url, content_hash)` already present in `raw.signals` is
  skipped, so re-runs don't re-spend.
- **Input truncation:** page text is capped at `COMPETE_LLM_MAX_INPUT_CHARS`.
- **`--limit`:** `compete extract -n N` bounds calls per run (useful for the
  first run of a large board like 300+ job postings).
- **Logging:** every call (success or failure) is recorded in `raw.llm_calls`
  with provider, model, token counts, and latency. `compete status` surfaces the
  running token total.
