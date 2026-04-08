"""Runtime model recommendations for local Ollama orchestration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OllamaModelRecommendation:
    """Metadata for a locally recommended Ollama model."""

    name: str
    label: str
    purpose: str


RECOMMENDED_OLLAMA_MODEL = OllamaModelRecommendation(
    name="qwen2.5:7b",
    label="Qwen 2.5 7B",
    purpose="prompt interpretation and orchestration for deterministic geometry generation",
)

FALLBACK_OLLAMA_MODELS: tuple[OllamaModelRecommendation, ...] = (
    OllamaModelRecommendation(
        name="llama3.2:3b",
        label="Llama 3.2 3B",
        purpose="lighter local fallback when the recommended model is unavailable",
    ),
)

ALL_RECOMMENDED_MODEL_NAMES: tuple[str, ...] = (
    RECOMMENDED_OLLAMA_MODEL.name,
    *(model.name for model in FALLBACK_OLLAMA_MODELS),
)
