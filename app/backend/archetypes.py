"""Archetype detection and defaults for Geomancer alpha generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import re

from .models import GenerationPlan


PHONE_STAND_MATCHERS: tuple[tuple[str, str], ...] = (
    (r"\bphone stand\b", "phone stand"),
    (r"\bsmartphone stand\b", "smartphone stand"),
    (r"\biphone stand\b", "iPhone stand"),
    (r"\bcell phone stand\b", "cell phone stand"),
    (r"\bmobile phone stand\b", "mobile phone stand"),
    (r"\bphone dock\b", "phone dock"),
    (r"\bstand for (?:a|an|the)?\s*(?:phone|smartphone|iphone|cell phone|mobile phone)\b", "stand for a phone"),
    (r"\bdevice stand\b[^\n]{0,24}\bphone\b", "device stand for a phone"),
)

DEVICE_NAME_PATTERNS: tuple[str, ...] = (
    r"\b(iPhone\s*\d+(?:\s*(?:Pro|Pro Max|Plus))?)\b",
    r"\b(Galaxy\s+S\d+(?:\s*(?:Ultra|Plus))?)\b",
    r"\b(Pixel\s+\d+(?:\s*Pro)?)\b",
    r"\b(OnePlus\s+\d+(?:\s*Pro)?)\b",
)

STYLE_KEYWORDS: tuple[str, ...] = ("minimal", "modern", "sleek", "industrial", "compact", "premium")
COMPETING_OBJECT_TERMS: tuple[str, ...] = ("plate", "panel", "bracket", "enclosure", "case", "housing", "clip", "hook", "adapter", "gear", "planter", "tray", "standoff")


@dataclass(frozen=True)
class PhoneStandArchetypeConfig:
    """High-confidence defaults for a usable phone stand archetype."""

    device_name: str = ""
    orientation_preference: str = "portrait"
    style: str = "minimal"
    with_cable_cutout: bool = False
    width_mm: float = 86.0
    depth_mm: float = 96.0
    height_mm: float = 120.0
    thickness_mm: float = 5.0
    viewing_angle_deg: float = 65.0
    lip_height_mm: float = 5.0
    cradle_depth_mm: float = 24.0
    device_width_mm: float = 72.0

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def angle_deg(self) -> float:
        return self.viewing_angle_deg

    @property
    def base_depth_mm(self) -> float:
        return self.depth_mm

    @property
    def base_thickness_mm(self) -> float:
        return self.thickness_mm

    @property
    def support_thickness_mm(self) -> float:
        return self.thickness_mm

    @property
    def slot_width_mm(self) -> float:
        return self.device_width_mm

    @property
    def slot_depth_mm(self) -> float:
        return self.cradle_depth_mm

    @property
    def lip_width_mm(self) -> float:
        return min(max(self.device_width_mm + 18.0, self.width_mm * 0.6), self.width_mm - 12.0)

    @property
    def lip_depth_mm(self) -> float:
        return max(self.thickness_mm * 0.9, 4.0)


@dataclass(frozen=True)
class ArchetypeSelection:
    """Structured archetype match used to route prompt intent."""

    archetype_key: str
    confidence: float
    matched_alias: str
    summary: str
    config: PhoneStandArchetypeConfig

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["config"] = self.config.to_dict()
        return payload


def select_archetype(user_request: str) -> ArchetypeSelection | None:
    """Return a high-confidence archetype match when one is obvious."""
    cleaned = user_request.strip()
    if not cleaned:
        return None

    lowered = cleaned.lower()
    matched_alias = ""
    matched_score = 0.0
    for pattern, alias in PHONE_STAND_MATCHERS:
        if re.search(pattern, lowered):
            matched_alias = alias
            matched_score = 0.97 if alias == "phone stand" else 0.93
            break

    if not matched_alias:
        return None

    if _has_competing_object_terms(lowered):
        return None

    config = infer_phone_stand_config(cleaned)
    summary = "High-confidence phone stand archetype with conservative deterministic defaults."
    return ArchetypeSelection(
        archetype_key="phone_stand",
        confidence=matched_score,
        matched_alias=matched_alias,
        summary=summary,
        config=config,
    )


def infer_phone_stand_config(user_request: str) -> PhoneStandArchetypeConfig:
    """Infer bounded phone-stand defaults from prompt language."""
    lowered = user_request.lower()
    device_name = _extract_device_name(user_request)
    orientation_preference = "landscape" if "landscape" in lowered else "portrait"
    if "portrait" not in lowered and orientation_preference != "landscape":
        orientation_preference = "portrait"
    style = _extract_style(lowered)
    with_cable_cutout = _has_cable_cutout(lowered)

    width_mm = 86.0
    height_mm = 120.0
    angle_deg = 65.0
    slot_width_mm = 12.0
    slot_depth_mm = 16.0
    base_thickness_mm = 6.0
    support_thickness_mm = 5.0

    if any(term in lowered for term in ("pro max", "plus", "ultra")):
        width_mm = 94.0
        height_mm = 130.0
        slot_width_mm = 13.0
        slot_depth_mm = 18.0
        angle_deg = 67.0
    elif any(term in lowered for term in ("mini", "se", "compact")):
        width_mm = 80.0
        height_mm = 110.0
        slot_width_mm = 11.0
        slot_depth_mm = 14.0
        angle_deg = 63.0

    if "upright" in lowered or "steep" in lowered:
        angle_deg = min(angle_deg + 3.0, 75.0)
    if "shallow" in lowered or "flat" in lowered:
        angle_deg = max(angle_deg - 5.0, 50.0)

    if "wide" in lowered:
        width_mm += 6.0
    if "compact" in lowered:
        width_mm = max(width_mm - 4.0, 74.0)

    lip_height_mm = max(base_thickness_mm * 0.8, 4.0)
    cradle_depth_mm = max(
        min(
            (height_mm - (base_thickness_mm + lip_height_mm)) / max(math.tan(math.radians(angle_deg)), 0.75),
            0.5 * width_mm,
        ),
        max(base_thickness_mm * 4.0, 18.0),
    )
    depth_mm = max(width_mm * 1.08, cradle_depth_mm + lip_height_mm + 18.0)
    depth_mm = min(max(depth_mm, 90.0), 118.0)
    device_width_mm = min(max(width_mm * 0.78, 68.0), width_mm - 12.0)
    support_height_mm = height_mm

    return PhoneStandArchetypeConfig(
        device_name=device_name,
        orientation_preference=orientation_preference,
        style=style,
        with_cable_cutout=with_cable_cutout,
        width_mm=width_mm,
        depth_mm=depth_mm,
        height_mm=support_height_mm,
        thickness_mm=base_thickness_mm,
        viewing_angle_deg=angle_deg,
        lip_height_mm=lip_height_mm,
        cradle_depth_mm=cradle_depth_mm,
        device_width_mm=device_width_mm,
    )


def build_phone_stand_generation_plan(user_request: str, selection: ArchetypeSelection | None = None) -> GenerationPlan:
    """Create a deterministic generation plan from phone-stand archetype data."""
    config = selection.config if selection else infer_phone_stand_config(user_request)
    request_text = user_request.strip()
    plan = GenerationPlan(
        family="phone_stand",
        family_label="phone stand",
        recipe="phone_stand",
        request_text=request_text,
        dimensions={
            "width_mm": config.width_mm,
            "depth_mm": config.depth_mm,
            "height_mm": config.height_mm,
            "thickness_mm": config.thickness_mm,
            "viewing_angle_deg": config.viewing_angle_deg,
            "lip_height_mm": config.lip_height_mm,
            "cradle_depth_mm": config.cradle_depth_mm,
            "device_width_mm": config.device_width_mm,
            "base_depth_mm": config.depth_mm,
            "base_thickness_mm": config.thickness_mm,
            "support_thickness_mm": config.thickness_mm,
            "slot_width_mm": config.device_width_mm,
            "slot_depth_mm": config.cradle_depth_mm,
            "angle_deg": config.viewing_angle_deg,
            "lip_width_mm": config.lip_width_mm,
            "lip_depth_mm": config.lip_depth_mm,
        },
        features={
            "device_name": config.device_name,
            "orientation_preference": config.orientation_preference,
            "style": config.style,
            "with_cable_cutout": config.with_cable_cutout,
            "cable_notch": config.with_cable_cutout,
        },
        assumptions=[],
        warnings=[],
        limitations=[],
        classification={
            "archetype_key": "phone_stand",
            "family_summary": "Deterministic phone stand archetype.",
            "matched_alias": selection.matched_alias if selection else "phone stand",
            "confidence": selection.confidence if selection else 0.93,
            "summary": selection.summary if selection else "High-confidence phone stand archetype.",
        },
    )

    if config.device_name:
        plan.assumptions.append(f"Target device: {config.device_name}.")
    else:
        plan.assumptions.append("Used broad smartphone defaults because no specific device was named.")
    plan.assumptions.append(f"Orientation preference: {config.orientation_preference}.")
    plan.assumptions.append(f"Style hint: {config.style}.")
    if config.with_cable_cutout:
        plan.warnings.append("Cable cutout is represented as a simple deterministic pass-through channel in alpha.")

    return plan


def _extract_device_name(user_request: str) -> str:
    for pattern in DEVICE_NAME_PATTERNS:
        match = re.search(pattern, user_request, flags=re.IGNORECASE)
        if match:
            return " ".join(match.group(1).split())
    return ""


def _extract_style(lowered: str) -> str:
    for keyword in STYLE_KEYWORDS:
        if keyword in lowered:
            return keyword
    return "minimal"


def _has_cable_cutout(lowered: str) -> bool:
    return any(
        term in lowered
        for term in (
            "cable cutout",
            "charging cutout",
            "charge cutout",
            "port cutout",
            "usb-c",
            "usb c",
            "lightning cutout",
            "charging port",
        )
    )


def _has_competing_object_terms(lowered: str) -> bool:
    return any(re.search(rf"\b{re.escape(term)}\b", lowered) for term in COMPETING_OBJECT_TERMS)
