"""Alpha-family request classification for Geomancer."""

from __future__ import annotations

import re

from .families import FAMILY_DEFINITIONS, FAMILY_BY_KEY
from .models import ClassificationResult


UNSUPPORTED_COMPLEXITY_TERMS = {
    "character": "Character and figure requests are outside the deterministic alpha scope.",
    "creature": "Creature and organic requests are outside the deterministic alpha scope.",
    "portrait": "Portrait-style modeling is outside the deterministic alpha scope.",
    "terrain": "Terrain generation is outside the deterministic alpha scope.",
    "threaded": "Threaded geometry is not implemented in the deterministic alpha backend yet.",
    "thread": "Threaded geometry is not implemented in the deterministic alpha backend yet.",
    "helical": "Helical geometry is not implemented in the deterministic alpha backend yet.",
    "organic": "Organic surfacing is outside the deterministic alpha scope.",
    "lattice": "Lattice-heavy geometry is not implemented in the deterministic alpha backend yet.",
}

FAMILY_HINTS = {
    "panel_plate": ("panel", "plate", "faceplate", "face plate", "cover plate", "mounting plate"),
    "spacer_standoff": ("spacer", "standoff", "standoff spacer", "sleeve spacer", "bushing spacer"),
    "enclosure": ("enclosure", "case", "lid", "housing", "electronics", "project box"),
    "tray_box": ("tray", "bin", "organizer", "open top", "open-top", "parts tray"),
    "bracket": ("bracket", "angle bracket", "l bracket", "mounting bracket", "right angle"),
    "adapter": ("adapter", "reducer", "coupler", "bushing", "step down", "step-down"),
    "cable_clip": ("cable clip", "wire clip", "cable holder", "snap clip", "clip"),
    "hook_mount": ("hook", "hanger", "mount", "wall hook", "utility hook"),
}


def classify_request(user_request: str) -> ClassificationResult:
    """Classify a request into one supported alpha family."""
    cleaned = user_request.strip()
    if not cleaned:
        return ClassificationResult(status="clarify", message="Describe the object you want Geomancer to build.")

    lowered = cleaned.lower()
    for term, message in UNSUPPORTED_COMPLEXITY_TERMS.items():
        if re.search(rf"\b{re.escape(term)}\b", lowered):
            return ClassificationResult(status="unsupported", message=message)

    scored_matches: list[tuple[int, int, int, str, str]] = []
    for family in FAMILY_DEFINITIONS:
        for alias in family.aliases:
            if re.search(rf"\b{re.escape(alias)}\b", lowered):
                scored_matches.append((100, len(alias.split()), len(alias), family.key, alias))

    hint_scores: dict[str, int] = {}
    for family_key, hints in FAMILY_HINTS.items():
        score = sum(1 for hint in hints if re.search(rf"\b{re.escape(hint)}\b", lowered))
        if score:
            hint_scores[family_key] = score

    if "box" in lowered and ("open top" in lowered or "open-top" in lowered or "tray" in lowered or "bin" in lowered):
        hint_scores["tray_box"] = hint_scores.get("tray_box", 0) + 3
    if "box" in lowered and ("lid" in lowered or "case" in lowered or "enclosure" in lowered or "housing" in lowered):
        hint_scores["enclosure"] = hint_scores.get("enclosure", 0) + 3
    if "clip" in lowered and ("cable" in lowered or "wire" in lowered):
        hint_scores["cable_clip"] = hint_scores.get("cable_clip", 0) + 3
    if "mount" in lowered and "hook" in lowered:
        hint_scores["hook_mount"] = hint_scores.get("hook_mount", 0) + 3
    if "adapter" in lowered and ("reducer" in lowered or "coupler" in lowered):
        hint_scores["adapter"] = hint_scores.get("adapter", 0) + 2

    for family_key, score in hint_scores.items():
        scored_matches.append((score * 10, score, 0, family_key, "hint"))

    if not scored_matches:
        primitive_terms = ("cube", "box", "plate", "panel", "cylinder", "sphere", "assembly", "blockout")
        if any(term in lowered for term in primitive_terms):
            fallback = FAMILY_BY_KEY["primitive_assembly"]
            return ClassificationResult(status="ready", family_key=fallback.key, matched_alias="primitive fallback", confidence=0.35)
        supported_text = ", ".join(family.label for family in FAMILY_DEFINITIONS)
        return ClassificationResult(status="unsupported", message=f"Geomancer alpha currently supports these families: {supported_text}.", confidence=0.0)

    scored_matches.sort(reverse=True)
    top_score, secondary_score, _, family_key, alias = scored_matches[0]
    confidence = min(0.99, 0.45 + (top_score / 150.0) + (secondary_score * 0.02))
    return ClassificationResult(status="ready", family_key=family_key, matched_alias=alias, confidence=confidence)
