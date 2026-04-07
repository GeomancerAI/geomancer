"""Dataclasses for the Geomancer deterministic backend pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class ClassificationResult:
    """Outcome of family-based request classification."""

    status: str
    family_key: str | None = None
    matched_alias: str | None = None
    confidence: float = 0.0
    message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GenerationPlan:
    """Normalized request plan for deterministic geometry generation."""

    family: str
    family_label: str
    recipe: str
    request_text: str
    dimensions: dict[str, float]
    features: dict[str, object]
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    classification: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ValidationReport:
    """Validation and review notes for a generation plan."""

    status: str
    summary: str
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    review_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
