"""Validation and reporting for deterministic generation plans."""

from __future__ import annotations

from .models import GenerationPlan, ValidationReport


def build_validation_report(plan: GenerationPlan) -> ValidationReport:
    """Build a review-friendly validation report for the plan."""
    warnings = list(plan.warnings)
    limitations = list(plan.limitations)
    review_notes = [
        f"Family: {plan.family_label}",
        f"Recipe: {plan.recipe}",
        "Deterministic Blender generation only; no freeform mesh synthesis is attempted.",
    ]

    for name, value in plan.dimensions.items():
        if value <= 0:
            warnings.append(f"{name} was non-positive and should be reviewed.")

    if plan.assumptions:
        review_notes.extend(plan.assumptions)
    if not limitations:
        limitations.append("Family outputs are alpha blockouts and may need manual refinement.")

    summary = f"Prepared deterministic {plan.family_label} blockout with {len(plan.dimensions)} normalized dimensions."
    return ValidationReport(
        status="ready",
        summary=summary,
        warnings=warnings,
        limitations=limitations,
        review_notes=review_notes,
    )
