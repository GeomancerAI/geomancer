"""Canonical planning schema for Geomancer backend generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


PLAN_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class CanonicalFeature:
    """A bounded, typed feature entry inside the canonical plan."""

    type: str
    params: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CanonicalPlan:
    """Canonical structured plan between prompt interpretation and generation."""

    schema_version: str = PLAN_SCHEMA_VERSION
    object_type: str = ""
    source_family: str = ""
    source_recipe: str = ""
    units: str = "mm"
    dimensions: dict[str, float] = field(default_factory=dict)
    features: list[CanonicalFeature] = field(default_factory=list)
    constraints: dict[str, object] = field(default_factory=dict)
    missing_info: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["features"] = [feature.to_dict() for feature in self.features]
        return payload


@dataclass
class CanonicalPlanValidationResult:
    """Structured validation result for a canonical plan."""

    status: str
    normalized_plan: CanonicalPlan
    warnings: list[str] = field(default_factory=list)
    clarification_needed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    summary: str = ""

    @property
    def is_valid(self) -> bool:
        return self.status == "valid"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "normalized_plan": self.normalized_plan.to_dict(),
            "warnings": list(self.warnings),
            "clarification_needed": list(self.clarification_needed),
            "errors": list(self.errors),
            "summary": self.summary,
        }
