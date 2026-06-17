"""Embeddings for semantic change-detection and dedup.

Provider-agnostic, mirroring the LLM client:

* ``hashing`` (default) - a deterministic, dependency-free signed feature-hashing
  embedding over word + char-trigram features. No torch, no network, instant,
  reproducible. Captures lexical overlap well enough to distinguish a minor edit
  (high cosine) from a real change (low cosine) - the gate we need.
* ``minilm`` - sentence-transformers all-MiniLM-L6-v2 (install ``--extra embed``).
* ``gemini`` - Google text-embedding-004 via the API (needs GOOGLE_API_KEY).

See ADR 0002 and AGENTS.md for the rationale and the cost/quality trade-off.
"""

from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

from pipeline.config import Settings, get_settings
from pipeline.logging_setup import get_logger

log = get_logger(__name__)

_WORD = re.compile(r"\w+", re.UNICODE)


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity. Robust to non-normalized / zero vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / (na * nb)))


class Embedder(ABC):
    dim: int

    @abstractmethod
    def embed_one(self, text: str) -> list[float]: ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_one(t) for t in texts]


class HashingEmbedder(Embedder):
    """Signed feature-hashing embedding (word + char-trigram), L2-normalized."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def _features(self, text: str):
        t = text.lower()
        yield from (f"w:{w}" for w in _WORD.findall(t))
        s = re.sub(r"\s+", " ", t)
        for i in range(len(s) - 2):
            yield f"c:{s[i : i + 3]}"

    def embed_one(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        if not text:
            return v
        for feat in self._features(text):
            h = int(hashlib.md5(feat.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 8) & 1 else -1.0
            v[idx] += sign
        norm = math.sqrt(sum(x * x for x in v))
        if norm > 0.0:
            v = [x / norm for x in v]
        return v


class MiniLMEmbedder(Embedder):
    """sentence-transformers all-MiniLM-L6-v2 (lazy import)."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def embed(self, texts: list[str]) -> list[list[float]]:
        vecs = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, v)) for v in vecs]


class GeminiEmbedder(Embedder):
    """Google text-embedding-004 (lazy import; needs GOOGLE_API_KEY)."""

    def __init__(self, api_key: str, model_name: str = "models/text-embedding-004") -> None:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_name = model_name
        self.dim = 768

    def embed_one(self, text: str) -> list[float]:
        resp = self._genai.embed_content(model=self._model_name, content=text or " ")
        return [float(x) for x in resp["embedding"]]


def get_embedder(settings: Settings | None = None) -> Embedder:
    """Construct the configured embedder, with a safe fallback to hashing."""
    s = settings or get_settings()
    provider = s.embed_provider.lower()
    if provider == "minilm":
        try:
            return MiniLMEmbedder(s.embed_model)
        except Exception as exc:  # missing extra / model download failure
            log.warning("minilm embedder unavailable (%s); falling back to hashing", exc)
            return HashingEmbedder(s.embed_dim)
    if provider == "gemini":
        if not s.google_api_key:
            log.warning("GOOGLE_API_KEY missing; falling back to hashing embedder")
            return HashingEmbedder(s.embed_dim)
        try:
            return GeminiEmbedder(s.google_api_key)
        except Exception as exc:
            log.warning("gemini embedder unavailable (%s); falling back to hashing", exc)
            return HashingEmbedder(s.embed_dim)
    return HashingEmbedder(s.embed_dim)
