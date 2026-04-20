"""Parameter extraction and normalization for deterministic alpha families."""

from __future__ import annotations

import re

from .archetypes import build_phone_stand_generation_plan
from .families import FAMILY_BY_KEY
from .models import ClassificationResult, GenerationPlan


NUMBER_PATTERN = r"(\d+(?:\.\d+)?)\s*mm\b"
COUNT_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "eight": 8,
}
ANGLE_WORDS = {
    "right angle": 90.0,
    "right-angle": 90.0,
    "90 degree": 90.0,
    "90-degree": 90.0,
    "45 degree": 45.0,
    "45-degree": 45.0,
}


def normalize_request(user_request: str, classification: ClassificationResult) -> tuple[str, str, GenerationPlan | None]:
    """Convert a classified request into a deterministic generation plan."""
    if classification.status != "ready" or not classification.family_key:
        return classification.status, classification.message, None

    family = FAMILY_BY_KEY[classification.family_key]
    text = user_request.strip()
    lowered = text.lower()

    plan = GenerationPlan(
        family=family.key,
        family_label=family.label,
        recipe=family.recipe,
        request_text=text,
        dimensions={},
        features={},
        classification={
            "matched_alias": classification.matched_alias or "",
            "family_summary": family.summary,
        },
    )

    extractors = {
        "enclosure": _normalize_box_shell_like,
        "housing_shell": _normalize_box_shell_like,
        "tray_box": _normalize_tray_box,
        "bracket": _normalize_bracket,
        "cable_clip": _normalize_cable_clip,
        "planter_vessel": _normalize_vessel,
        "gear": _normalize_gear,
        "adapter": _normalize_adapter,
        "panel_plate": _normalize_panel_plate,
        "spacer_standoff": _normalize_standoff,
        "hook_mount": _normalize_hook_mount,
        "phone_stand": _normalize_phone_stand,
        "primitive_assembly": _normalize_primitive_assembly,
    }

    extractors[family.key](lowered, plan)

    if not _has_any_dimension(plan):
        return "clarify", f"Provide at least one dimension in mm for the {family.label} request.", None

    return "ready", "", plan


def _normalize_box_shell_like(text: str, plan: GenerationPlan) -> None:
    triplet = _extract_triplet(text)
    width = _extract_named_mm(text, ("width", "wide")) or (triplet[0] if triplet else None) or _extract_first_mm(text) or 120.0
    depth = _extract_named_mm(text, ("depth", "deep")) or (triplet[1] if triplet else None) or _extract_second_mm(text) or 80.0
    height = _extract_named_mm(text, ("height", "tall")) or (triplet[2] if triplet else None) or _extract_third_mm(text) or 60.0
    wall = _extract_named_mm(text, ("wall", "shell", "thickness")) or 3.0
    base_thickness = _extract_named_mm(text, ("base", "bottom")) or wall
    opening_pair = _extract_labeled_pair(text, ("opening", "cutout", "front opening", "front cutout"))
    plan.dimensions.update({"width_mm": width, "depth_mm": depth, "height_mm": height})
    plan.features["wall_thickness_mm"] = min(max(wall, 1.5), max(min(width, depth, height) * 0.2, 1.5))
    plan.features["base_thickness_mm"] = min(max(base_thickness, 1.5), max(height * 0.35, 1.5))
    plan.features["open_top"] = "open top" in text or plan.family in {"tray_box", "enclosure", "housing_shell"}
    plan.features["front_opening"] = "front opening" in text or "front cutout" in text
    plan.features["opening_width_mm"] = opening_pair[0] if opening_pair else max(width * 0.55, 20.0)
    plan.features["opening_height_mm"] = opening_pair[1] if opening_pair else max(height * 0.45, 20.0)
    if not triplet and not any(keyword in text for keyword in ("width", "depth", "height", "wide", "deep", "tall")):
        plan.assumptions.append("Used fallback rectangular dimensions because the request did not provide explicit width/depth/height cues.")
    if plan.features["front_opening"]:
        plan.warnings.append("Front openings are represented as simple rectangular cutouts in alpha.")
    if plan.features["base_thickness_mm"] > plan.dimensions["height_mm"] * 0.45:
        plan.warnings.append("Base thickness was clamped to keep the enclosure shell believable.")


def _normalize_tray_box(text: str, plan: GenerationPlan) -> None:
    triplet = _extract_triplet(text)
    _normalize_box_shell_like(text, plan)
    plan.features["open_top"] = True
    width = plan.dimensions.get("width_mm", 0.0)
    depth = plan.dimensions.get("depth_mm", 0.0)
    wall = plan.features.get("wall_thickness_mm", 0.0)
    if not triplet and not any(keyword in text for keyword in ("height", "tall")):
        shallow_height = max(min(width, depth) * 0.28, 18.0)
        plan.dimensions["height_mm"] = min(plan.dimensions.get("height_mm", shallow_height), shallow_height)
    max_tray_height = max(min(width, depth) * 0.35, 18.0)
    if plan.dimensions.get("height_mm", 0.0) > max_tray_height:
        plan.dimensions["height_mm"] = max_tray_height
    if wall:
        plan.features["base_thickness_mm"] = max(plan.features.get("base_thickness_mm", wall), wall * 1.2, 4.0)
    plan.features["lip_height_mm"] = _extract_named_mm(text, ("lip", "rim")) or 0.0
    plan.features["front_opening"] = False


def _normalize_bracket(text: str, plan: GenerationPlan) -> None:
    triplet = _extract_triplet(text)
    length = _extract_named_mm(text, ("length", "base length", "long")) or (triplet[0] if triplet else None) or _extract_first_mm(text) or 100.0
    width = _extract_named_mm(text, ("width", "flange width", "wide")) or (triplet[1] if triplet else None) or _extract_second_mm(text) or 30.0
    height = _extract_named_mm(text, ("height", "leg height", "tall")) or (triplet[2] if triplet else None) or _extract_third_mm(text) or 80.0
    thickness = _extract_named_mm(text, ("thickness", "wall")) or 6.0
    hole_diameter = _extract_hole_diameter(text) or _extract_named_mm(text, ("hole", "mounting hole", "screw hole")) or 0.0
    hole_count = _extract_hole_count(text) or (4 if hole_diameter > 0 else 0)
    bracket_angle = _extract_angle(text) or 90.0
    plan.dimensions.update(
        {
            "base_length_mm": length,
            "flange_width_mm": width,
            "vertical_height_mm": height,
            "thickness_mm": thickness,
        }
    )
    plan.features["hole_diameter_mm"] = hole_diameter
    plan.features["mounting_holes"] = hole_diameter > 0
    plan.features["hole_count"] = hole_count
    plan.features["bracket_angle_deg"] = bracket_angle
    plan.features["gusset"] = "gusset" in text or "reinforced" in text or hole_count >= 4
    if hole_count > 0 and hole_diameter <= 0:
        plan.features["hole_diameter_mm"] = 5.0
        plan.features["mounting_holes"] = True
        hole_diameter = 5.0
    if "mount" in text or "mounting" in text or "hardware" in text:
        if hole_count == 0:
            plan.features["hole_count"] = 2
            plan.features["hole_diameter_mm"] = hole_diameter or 5.0
            plan.features["mounting_holes"] = True
            plan.assumptions.append("Assumed a two-hole mounting bracket pattern from the request wording.")
    if bracket_angle != 90.0:
        plan.limitations.append("Bracket geometry currently remains a right-angle blockout even when another angle is requested.")
    if not triplet:
        plan.assumptions.append("Used default bracket dimensions where the request did not provide a complete length x width x height set.")


def _normalize_cable_clip(text: str, plan: GenerationPlan) -> None:
    cable_diameter = _extract_named_mm(text, ("cable diameter", "wire diameter", "bundle diameter")) or _extract_named_mm(text, ("cable", "wire", "bundle"))
    width = _extract_named_mm(text, ("width", "wide")) or _extract_first_mm(text) or 28.0
    opening = _extract_named_mm(text, ("opening", "gap")) or (cable_diameter + 2.0 if cable_diameter is not None else max(width * 0.55, 12.0))
    depth = _extract_named_mm(text, ("depth", "deep")) or 16.0
    thickness = _extract_named_mm(text, ("thickness", "wall")) or 4.0
    base_length = _extract_named_mm(text, ("base", "mounting base")) or max(width * 0.8, width)
    mount_hole = _extract_hole_diameter(text) or _extract_named_mm(text, ("mount hole", "screw hole", "hole")) or 0.0
    plan.dimensions.update(
        {
            "clip_width_mm": width,
            "opening_mm": opening,
            "depth_mm": depth,
            "thickness_mm": thickness,
        }
    )
    plan.features["cable_diameter_mm"] = cable_diameter or max(opening - 2.0, 1.0)
    plan.features["base_length_mm"] = base_length
    plan.features["mount_hole_mm"] = mount_hole
    plan.features["closed_ring"] = "closed" in text or "loop" in text
    if cable_diameter is None:
        plan.assumptions.append("Inferred cable diameter from the requested opening and clip width.")
    if plan.features["closed_ring"]:
        plan.limitations.append("Cable clip geometry remains an open printable clip in alpha rather than a fully closed ring.")


def _normalize_vessel(text: str, plan: GenerationPlan) -> None:
    diameter = _extract_named_mm(text, ("diameter", "opening")) or _extract_first_mm(text) or 100.0
    height = _extract_named_mm(text, ("height", "tall")) or _extract_second_mm(text) or 90.0
    thickness = _extract_named_mm(text, ("wall", "shell", "thickness")) or 3.0
    plan.dimensions.update({"diameter_mm": diameter, "height_mm": height})
    plan.features["wall_thickness_mm"] = thickness
    plan.features["drain_hole_mm"] = _extract_named_mm(text, ("drain", "drain hole")) or 0.0


def _normalize_gear(text: str, plan: GenerationPlan) -> None:
    diameter = _extract_named_mm(text, ("diameter", "outer diameter")) or _extract_first_mm(text) or 60.0
    thickness = _extract_named_mm(text, ("thickness", "face width")) or _extract_second_mm(text) or 8.0
    center_hole = _extract_named_mm(text, ("center hole", "bore", "shaft")) or 8.0
    teeth = _extract_count(text, ("teeth", "tooth")) or 12
    plan.dimensions.update({"diameter_mm": diameter, "thickness_mm": thickness})
    plan.features["center_hole_mm"] = center_hole
    plan.features["tooth_count"] = teeth
    plan.limitations.append("Gear teeth are simplified rectangular blockouts, not involute profiles.")


def _normalize_adapter(text: str, plan: GenerationPlan) -> None:
    values = _extract_mm_values(text)
    diameter_pair = _extract_adapter_diameters(text)
    first = (diameter_pair[0] if diameter_pair else None) or _extract_named_mm(text, ("large diameter", "outer diameter", "input diameter")) or (values[0] if values else None) or 40.0
    second = (diameter_pair[1] if diameter_pair else None) or _extract_named_mm(text, ("small diameter", "output diameter", "reduced diameter")) or (values[1] if len(values) > 1 else None) or 24.0
    third = _extract_named_mm(text, ("length", "overall length", "tall")) or (values[2] if len(values) > 2 else None) or 40.0
    center_hole = _extract_named_mm(text, ("hole", "inner", "inner diameter", "through hole")) or 0.0
    plan.dimensions.update(
        {
            "large_diameter_mm": max(first, second),
            "small_diameter_mm": min(first, second),
            "length_mm": third,
        }
    )
    plan.features["center_hole_mm"] = center_hole
    plan.features["step_ratio"] = 0.55 if "step" in text or "stepped" in text else 0.5
    plan.features["through_hole"] = center_hole > 0
    plan.features["flange_diameter_mm"] = _extract_named_mm(text, ("flange", "lip")) or 0.0
    if _count_mm_values(text) < 3:
        plan.assumptions.append("Used default adapter length because fewer than three mm values were provided.")


def _normalize_panel_plate(text: str, plan: GenerationPlan) -> None:
    triplet = _extract_triplet(text)
    pair = _extract_pair(text)
    width = _extract_named_mm(text, ("width", "wide", "length")) or (triplet[0] if triplet else None) or (pair[0] if pair else None) or _extract_first_mm(text) or 100.0
    height = _extract_named_mm(text, ("height", "tall")) or (triplet[1] if triplet else None) or (pair[1] if pair else None) or _extract_second_mm(text) or 60.0
    thickness = _extract_named_mm(text, ("thickness", "panel thickness", "plate thickness")) or (triplet[2] if triplet else None) or _extract_third_mm(text) or 3.0
    hole_count = _extract_count(text, ("holes", "hole")) or _infer_hole_count_words(text) or 0
    hole_diameter = _extract_hole_diameter(text) or _extract_named_mm(text, ("hole", "mounting hole")) or 0.0
    spacing = _extract_named_mm(text, ("spacing", "pitch")) or max(min(width, height) * 0.6, 12.0)
    if hole_count == 0 and ("corner" in text or "mounting" in text):
        hole_count = 4
    if hole_diameter == 0.0 and hole_count > 0:
        hole_diameter = 5.0
    plan.dimensions.update({"width_mm": width, "height_mm": height, "thickness_mm": thickness})
    plan.features["hole_diameter_mm"] = hole_diameter
    plan.features["hole_count"] = hole_count
    plan.features["hole_spacing_mm"] = min(spacing, min(width, height) - 8.0) if hole_diameter > 0 else 0.0
    plan.features["hole_pattern"] = "corners" if hole_count >= 4 else ("pair_horizontal" if hole_count == 2 else "none")
    plan.features["corner_holes"] = plan.features["hole_pattern"] == "corners"
    if hole_diameter > 0 and hole_count == 0:
        plan.assumptions.append("Assumed a 4-hole corner pattern because a hole diameter was provided without a count.")


def _normalize_standoff(text: str, plan: GenerationPlan) -> None:
    values = _extract_mm_values(text)
    outer_diameter = _extract_named_mm(text, ("outer diameter", "od", "diameter")) or (values[0] if values else None) or 14.0
    inner_diameter = _extract_named_mm(text, ("inner diameter", "id", "hole", "bore")) or (values[1] if len(values) > 2 else None) or max(outer_diameter * 0.4, 3.0)
    length = _extract_named_mm(text, ("length", "height", "tall")) or (values[2] if len(values) > 2 else None) or (values[1] if len(values) > 1 else None) or 20.0
    inner_diameter = min(inner_diameter, max(outer_diameter - 2.0, 1.0))
    plan.dimensions.update({"outer_diameter_mm": outer_diameter, "length_mm": length})
    plan.features["inner_diameter_mm"] = inner_diameter
    plan.features["profile"] = "hex" if "hex" in text or "hexagonal" in text else "round"
    if "hex" in text:
        plan.assumptions.append("Hex standoffs use a simple six-sided primitive rather than chamfered hardware detail.")


def _normalize_hook_mount(text: str, plan: GenerationPlan) -> None:
    triplet = _extract_triplet(text)
    pair = _extract_pair(text)
    width = _extract_named_mm(text, ("width", "base width", "plate width", "wide")) or (triplet[0] if triplet else None) or (pair[0] if pair else None) or _extract_first_mm(text) or 50.0
    height = _extract_named_mm(text, ("height", "base height", "plate height", "tall")) or (triplet[1] if triplet else None) or (pair[1] if pair else None) or _extract_second_mm(text) or 80.0
    depth = _extract_named_mm(text, ("depth", "projection", "reach", "hook length", "arm length")) or (triplet[2] if triplet else None) or _extract_third_mm(text) or 35.0
    thickness = _extract_named_mm(text, ("thickness", "plate thickness", "wall")) or 6.0
    base_thickness = _extract_named_mm(text, ("base thickness", "base plate thickness")) or max(thickness * 1.25, 6.0)
    hook_length = _extract_named_mm(text, ("hook length", "arm length", "reach", "projection")) or max(depth * 0.72, thickness * 4.0)
    hook_radius = _extract_named_mm(text, ("hook radius", "bend radius", "radius")) or max(thickness * 1.5, 3.0)
    hook_angle = _extract_named_mm(text, ("hook angle", "tilt", "upward angle")) or 18.0
    hole_count = _extract_count(text, ("holes", "hole")) or 2
    hole_diameter = _extract_hole_diameter(text) or _extract_named_mm(text, ("hole", "mounting hole")) or 5.0
    hole_margin = _extract_named_mm(text, ("hole margin", "margin")) or max(thickness * 2.0, hole_diameter * 1.5, 8.0)
    plan.dimensions.update(
        {
            "width_mm": width,
            "height_mm": height,
            "depth_mm": depth,
            "thickness_mm": thickness,
            "base_thickness_mm": base_thickness,
            "hook_length_mm": hook_length,
            "hook_radius_mm": hook_radius,
            "hook_angle_deg": hook_angle,
            "base_width_mm": width,
            "base_height_mm": height,
            "arm_length_mm": depth,
        }
    )
    plan.features["hole_count"] = hole_count
    plan.features["hole_diameter_mm"] = hole_diameter
    plan.features["hole_margin_mm"] = hole_margin
    plan.features["mount_hole_mm"] = hole_diameter
    plan.features["mount_hole_count"] = hole_count
    plan.features["hook_drop_mm"] = max(hook_length * 0.35, thickness * 1.5)
    plan.features["double_hook"] = "double hook" in text or "two hooks" in text
    if plan.features["double_hook"]:
        plan.limitations.append("Double-hook requests are normalized to a single hook in alpha.")

    if plan.dimensions["thickness_mm"] < 3.0:
        plan.dimensions["thickness_mm"] = 3.0
        plan.assumptions.append("Clamped hook mount thickness to the printable minimum.")
    if plan.dimensions["base_thickness_mm"] < max(plan.dimensions["thickness_mm"] * 1.25, 4.0):
        plan.dimensions["base_thickness_mm"] = max(plan.dimensions["thickness_mm"] * 1.25, 4.0)
        plan.assumptions.append("Clamped hook mount base thickness to keep the mounting plate readable.")
    if plan.dimensions["hook_length_mm"] < 10.0:
        plan.dimensions["hook_length_mm"] = 10.0
        plan.assumptions.append("Clamped hook mount hook length to a visible minimum.")
    if plan.dimensions["hook_angle_deg"] < 12.0:
        plan.dimensions["hook_angle_deg"] = 12.0
    if plan.dimensions["hook_angle_deg"] > 35.0:
        plan.dimensions["hook_angle_deg"] = 35.0
    if plan.dimensions["depth_mm"] < plan.dimensions["hook_length_mm"] + max(plan.dimensions["thickness_mm"] * 1.5, 6.0):
        plan.dimensions["depth_mm"] = plan.dimensions["hook_length_mm"] + max(plan.dimensions["thickness_mm"] * 1.5, 6.0)


def _normalize_phone_stand(text: str, plan: GenerationPlan) -> None:
    del text
    archetype_plan = build_phone_stand_generation_plan(plan.request_text)
    plan.dimensions.update(archetype_plan.dimensions)
    plan.features.update(archetype_plan.features)
    plan.assumptions.extend(archetype_plan.assumptions)
    plan.warnings.extend(archetype_plan.warnings)
    plan.limitations.extend(archetype_plan.limitations)
    plan.classification.update(archetype_plan.classification)


def _normalize_primitive_assembly(text: str, plan: GenerationPlan) -> None:
    width, depth, height = _extract_triplet(text) or (80.0, 50.0, 40.0)
    plan.dimensions.update({"width_mm": width, "depth_mm": depth, "height_mm": height})
    plan.features["include_cube"] = "cube" in text or "box" in text or "plate" in text
    plan.features["include_cylinder"] = "cylinder" in text or "tube" in text
    plan.features["include_sphere"] = "sphere" in text or "ball" in text
    if not any((plan.features["include_cube"], plan.features["include_cylinder"], plan.features["include_sphere"])):
        plan.features["include_cube"] = True
        plan.features["include_cylinder"] = True
        plan.assumptions.append("Used a mixed primitive assembly because no specific primitive list was provided.")


def _extract_triplet(text: str) -> tuple[float, float, float] | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:x|by)\s*(\d+(?:\.\d+)?)\s*(?:x|by)\s*(\d+(?:\.\d+)?)\s*mm\b", text)
    if not match:
        return None
    return tuple(float(match.group(index)) for index in range(1, 4))


def _extract_pair(text: str) -> tuple[float, float] | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:x|by)\s*(\d+(?:\.\d+)?)\s*mm\b", text)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def _extract_named_mm(text: str, names: tuple[str, ...]) -> float | None:
    for name in names:
        before = re.search(rf"\b{re.escape(name)}\b[^\d]{{0,24}}{NUMBER_PATTERN}", text)
        if before:
            return float(before.group(1))
        after = re.search(rf"{NUMBER_PATTERN}[^\w]{{0,8}}\b{re.escape(name)}\b", text)
        if after:
            return float(after.group(1))
    return None


def _extract_hole_diameter(text: str) -> float | None:
    patterns = (
        r"(\d+(?:\.\d+)?)\s*mm\s+mounting holes?\b",
        r"(\d+(?:\.\d+)?)\s*mm\s+\w+\s+holes?\b",
        r"(\d+(?:\.\d+)?)\s*mm\s+holes?\b",
        r"\bhole\b[^\d]{0,12}(\d+(?:\.\d+)?)\s*mm\b",
    )
    for pattern in patterns:
        matches = list(re.finditer(pattern, text))
        if matches:
            return float(matches[-1].group(1))
    return None


def _extract_hole_count(text: str) -> int | None:
    patterns = (
        r"\b(\d+)\s+(?:mounting\s+)?holes?\b",
        rf"\b({'|'.join(COUNT_WORDS)})\s+(?:mounting\s+)?holes?\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        value = match.group(1)
        if value.isdigit():
            return int(value)
        return COUNT_WORDS[value]
    return None


def _extract_adapter_diameters(text: str) -> tuple[float, float] | None:
    patterns = (
        r"from\s+(\d+(?:\.\d+)?)\s*mm\s+to\s+(\d+(?:\.\d+)?)\s*mm",
        r"(\d+(?:\.\d+)?)\s*mm\s+to\s+(\d+(?:\.\d+)?)\s*mm",
        r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*mm",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1)), float(match.group(2))
    return None


def _extract_labeled_pair(text: str, names: tuple[str, ...]) -> tuple[float, float] | None:
    for name in names:
        before = re.search(rf"\b{re.escape(name)}\b[^\d]{{0,20}}(\d+(?:\.\d+)?)\s*(?:x|by)\s*(\d+(?:\.\d+)?)\s*mm\b", text)
        if before:
            return float(before.group(1)), float(before.group(2))
        after = re.search(rf"(\d+(?:\.\d+)?)\s*(?:x|by)\s*(\d+(?:\.\d+)?)\s*mm\b[^\n]{{0,20}}\b{re.escape(name)}\b", text)
        if after:
            return float(after.group(1)), float(after.group(2))
    return None


def _extract_mm_values(text: str) -> list[float]:
    return [float(match) for match in re.findall(NUMBER_PATTERN, text)]


def _extract_first_mm(text: str) -> float | None:
    values = _extract_mm_values(text)
    return values[0] if values else None


def _extract_second_mm(text: str) -> float | None:
    values = _extract_mm_values(text)
    return values[1] if len(values) > 1 else None


def _extract_third_mm(text: str) -> float | None:
    values = _extract_mm_values(text)
    return values[2] if len(values) > 2 else None


def _count_mm_values(text: str) -> int:
    return len(_extract_mm_values(text))


def _extract_count(text: str, names: tuple[str, ...]) -> int | None:
    for name in names:
        before = re.search(rf"(\d+)[-\s]*{re.escape(name)}\b", text)
        if before:
            return int(before.group(1))
        word_before = re.search(rf"\b({'|'.join(COUNT_WORDS)})\b[-\s]*{re.escape(name)}\b", text)
        if word_before:
            return COUNT_WORDS[word_before.group(1)]
        after = re.search(rf"\b{re.escape(name)}\b[^\d]{{0,12}}(\d+)", text)
        if after:
            return int(after.group(1))
    return None


def _extract_angle(text: str) -> float | None:
    for phrase, value in ANGLE_WORDS.items():
        if phrase in text:
            return value
    explicit = re.search(r"(\d+(?:\.\d+)?)\s*degree", text)
    if explicit:
        return float(explicit.group(1))
    return None


def _infer_hole_count_words(text: str) -> int | None:
    if "hole" not in text:
        return None
    for word, value in COUNT_WORDS.items():
        if re.search(rf"\b{word}\b", text):
            return value
    return None


def _has_any_dimension(plan: GenerationPlan) -> bool:
    return any(float(value) > 0 for value in plan.dimensions.values())
