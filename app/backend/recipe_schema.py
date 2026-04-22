"""Canonical deterministic recipe schema for Geomancer backend generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


RECIPE_SCHEMA_VERSION = "1.0"
RECIPE_OP_VOCABULARY = {
    "add_box",
    "add_cylinder",
    "add_sphere",
    "add_hole",
    "hole_pattern",
    "shell",
    "flatten_bottom",
    "bracket_body",
    "hook_mount_body",
    "phone_stand_body",
    "boolean_union",
    "boolean_difference",
    "apply_bevel",
}


@dataclass(frozen=True)
class RecipeOp:
    """A single deterministic recipe step."""

    op: str
    id: str = ""
    params: dict[str, object] = field(default_factory=dict)
    target: str = ""
    tool: str = ""

    def to_dict(self) -> dict:
        payload = asdict(self)
        return {
            key: value
            for key, value in payload.items()
            if value not in ("", None) and value != {}
        }


@dataclass
class DeterministicRecipe:
    """Canonical recipe contract between validation and deterministic generation."""

    recipe_version: str = RECIPE_SCHEMA_VERSION
    object_type: str = ""
    source_family: str = ""
    source_recipe: str = ""
    execution_recipe: str = ""
    generation_id: str = ""
    implementation_id: str = ""
    ops: list[RecipeOp] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["ops"] = [op.to_dict() for op in self.ops]
        return payload


@dataclass
class DeterministicRecipeBuildResult:
    """Structured build result for canonical recipe generation."""

    status: str
    normalized_recipe: DeterministicRecipe
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    summary: str = ""

    @property
    def is_valid(self) -> bool:
        return self.status == "ready"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "normalized_recipe": self.normalized_recipe.to_dict(),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "summary": self.summary,
        }
