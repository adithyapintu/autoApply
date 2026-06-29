"""
Local embedding service using fastembed (BAAI/bge-small-en-v1.5).
No external API key required — model is downloaded on first use (~130 MB) and cached.
"""
import asyncio
from typing import ClassVar

_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384
_MAX_CHARS = 8192  # truncate long texts


class EmbeddingService:
    """Async-friendly wrapper around the synchronous fastembed TextEmbedding model."""

    _model: ClassVar[object] = None  # lazy singleton

    def _load_model(self):
        if EmbeddingService._model is None:
            from fastembed import TextEmbedding  # deferred import so startup is fast
            EmbeddingService._model = TextEmbedding(model_name=_MODEL_NAME)
        return EmbeddingService._model

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        model = self._load_model()
        truncated = [t[:_MAX_CHARS] for t in texts]
        return [vec.tolist() for vec in model.embed(truncated)]

    async def embed(self, text: str) -> list[float]:
        """Embed a single string. Runs the CPU-bound model in the default executor."""
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, self._embed_sync, [text])
        return results[0]

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of strings."""
        if not texts:
            return []
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._embed_sync, texts)

    def build_profile_text(self, profile: dict) -> str:
        """Flatten a profile dict into a single string for embedding."""
        parts: list[str] = []
        if profile.get("field"):
            parts.append(profile["field"])
        parts.extend(profile.get("tech_stacks", []))
        parts.extend(profile.get("preferred_roles", []))
        parts.extend(profile.get("domain_expertise", []))
        if profile.get("summary"):
            parts.append(profile["summary"])
        for skill in profile.get("skills", []):
            parts.append(skill["name"] if isinstance(skill, dict) else skill)
        for exp in profile.get("experience", []):
            if isinstance(exp, dict):
                parts.append(f"{exp.get('title', '')} at {exp.get('company', '')}")
                parts.extend(exp.get("achievements", []))
        return " ".join(filter(None, parts))

    def build_job_text(self, job: dict) -> str:
        """Flatten a job dict into a single string for embedding."""
        parts: list[str] = [
            job.get("title", ""),
            job.get("description", "")[:4000],
        ]
        if job.get("location"):
            parts.append(job["location"])
        return " ".join(filter(None, parts))
