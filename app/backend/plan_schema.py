"""Authoritative Plan Schema v1 for the Geomancer backend."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


PLAN_SCHEMA_VERSION = "1.0"
ALLOWED_STYLE_PROFILES = {
    "minimal",
    "industrial",
    "sci_fi",
    "low_poly",
    "rounded",
}
ALLOWED_CONSTRUCTION_MODES = {
    "constraint",
    "compositional",
    "hybrid",
}
ALLOWED_OBJECT_TYPES = {
    "phone_stand",
    "bracket",
    "tray",
    "enclosure",
    "plate",
    "standoff",
    "hook_mount",
    "adapter",
    "primitive_assembly",
    "crate",
    "barrel",
    "canister",
    "pedestal",
}
ALLOWED_COMPONENT_TYPES = {
    "base_plate",
    "angled_support",
    "retaining_lip",
    "back_plate",
    "vertical_leg",
    "horizontal_leg",
    "gusset",
    "shell",
    "opening",
    "rim",
    "hole_pattern",
    "mount_hole",
    "drain_hole",
    "hook_arm",
    "hook_tip",
    "through_hole",
    "boss",
    "tab",
    "slot",
    "cube",
    "cylinder",
    "sphere",
}
ALLOWED_COMPOSITION_ITEM_TYPES = {
    "cube",
    "cylinder",
    "sphere",
}
STYLE_DEFAULTS_BY_PROFILE = {
    "minimal": {
        "shape_language": "prismatic",
        "edge_treatment": "soft",
        "detail_density": "low",
        "accent_profile": "none",
    },
    "industrial": {
        "shape_language": "panelized",
        "edge_treatment": "hard",
        "detail_density": "medium",
        "accent_profile": "ribs",
    },
    "sci_fi": {
        "shape_language": "panelized",
        "edge_treatment": "hard",
        "detail_density": "medium",
        "accent_profile": "panels",
    },
    "low_poly": {
        "shape_language": "faceted",
        "edge_treatment": "faceted",
        "detail_density": "low",
        "accent_profile": "none",
    },
    "rounded": {
        "shape_language": "rounded",
        "edge_treatment": "rounded",
        "detail_density": "low",
        "accent_profile": "soft_caps",
    },
}
STYLE_COMPATIBILITY_BY_OBJECT_TYPE = {
    "phone_stand": {"minimal", "industrial", "rounded"},
    "bracket": {"minimal", "industrial", "sci_fi"},
    "tray": {"minimal", "industrial", "rounded"},
    "enclosure": {"minimal", "industrial", "sci_fi", "rounded"},
    "plate": {"minimal", "industrial", "rounded"},
    "standoff": {"minimal", "industrial"},
    "hook_mount": {"minimal", "industrial", "sci_fi"},
    "adapter": {"minimal", "industrial", "sci_fi"},
    "primitive_assembly": {"minimal", "industrial", "sci_fi", "low_poly", "rounded"},
    "crate": {"minimal", "industrial", "sci_fi", "low_poly", "rounded"},
    "barrel": {"minimal", "industrial", "sci_fi", "low_poly", "rounded"},
    "canister": {"minimal", "industrial", "sci_fi", "low_poly", "rounded"},
    "pedestal": {"minimal", "industrial", "sci_fi", "low_poly", "rounded"},
}
STYLE_DEFAULT_BY_OBJECT_TYPE = {
    "phone_stand": "minimal",
    "bracket": "minimal",
    "tray": "minimal",
    "enclosure": "minimal",
    "plate": "minimal",
    "standoff": "minimal",
    "hook_mount": "minimal",
    "adapter": "minimal",
    "primitive_assembly": "low_poly",
    "crate": "low_poly",
    "barrel": "industrial",
    "canister": "industrial",
    "pedestal": "low_poly",
}


@dataclass
class GeomancerIntent:
    object_type: str = ""
    object_label: str = ""
    use_case: str = ""
    printable: bool = True
    editable_in_blender: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GeomancerComponent:
    id: str = ""
    type: str = ""
    params: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "params": dict(self.params),
        }


@dataclass
class GeomancerCompositionItem:
    id: str = ""
    type: str = ""
    operation: str = "union"
    params: dict[str, object] = field(default_factory=dict)
    position: list[float] = field(default_factory=list)
    rotation_deg: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        payload = {
            "id": self.id,
            "type": self.type,
            "operation": self.operation,
            "params": dict(self.params),
        }
        if self.position:
            payload["position"] = list(self.position)
        if self.rotation_deg:
            payload["rotation_deg"] = list(self.rotation_deg)
        return payload


@dataclass
class GeomancerStyle:
    style_profile: str = "minimal"
    shape_language: str = "prismatic"
    edge_treatment: str = "soft"
    detail_density: str = "low"
    accent_profile: str = "none"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GeomancerHybridDetail:
    id: str = ""
    source_mode: str = ""
    type: str = ""
    operation: str = "union"
    params: dict[str, object] = field(default_factory=dict)
    position: list[float] = field(default_factory=list)
    rotation_deg: list[float] = field(default_factory=list)
    target: str = ""

    def to_dict(self) -> dict:
        payload = {
            "id": self.id,
            "source_mode": self.source_mode,
            "type": self.type,
            "operation": self.operation,
            "params": dict(self.params),
        }
        if self.position:
            payload["position"] = list(self.position)
        if self.rotation_deg:
            payload["rotation_deg"] = list(self.rotation_deg)
        if self.target:
            payload["target"] = self.target
        return payload


@dataclass
class GeomancerPlan:
    schema_version: str = PLAN_SCHEMA_VERSION
    request_text: str = ""
    intent: GeomancerIntent = field(default_factory=GeomancerIntent)
    construction_mode: str = "constraint"
    units: str = "mm"
    dimensions: dict[str, object] = field(default_factory=dict)
    components: list[GeomancerComponent] = field(default_factory=list)
    composition: list[GeomancerCompositionItem] = field(default_factory=list)
    hybrid_details: list[GeomancerHybridDetail] = field(default_factory=list)
    constraints: dict[str, object] = field(default_factory=dict)
    style: GeomancerStyle = field(default_factory=GeomancerStyle)
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_info: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def object_type(self) -> str:
        return self.intent.object_type

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "request_text": self.request_text,
            "intent": self.intent.to_dict(),
            "construction_mode": self.construction_mode,
            "units": self.units,
            "dimensions": dict(self.dimensions),
            "components": [component.to_dict() for component in self.components],
            "composition": [item.to_dict() for item in self.composition],
            "hybrid_details": [detail.to_dict() for detail in self.hybrid_details],
            "constraints": dict(self.constraints),
            "style": self.style.to_dict() if hasattr(self.style, "to_dict") else dict(self.style),
            "assumptions": list(self.assumptions),
            "warnings": list(self.warnings),
            "missing_info": list(self.missing_info),
            "notes": list(self.notes),
        }


@dataclass
class GeomancerPlanValidationResult:
    status: str
    normalized_plan: GeomancerPlan
    warnings: list[str] = field(default_factory=list)
    clarification_needed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    summary: str = ""

    @property
    def is_valid(self) -> bool:
        return self.status == "ready"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "normalized_plan": self.normalized_plan.to_dict(),
            "warnings": list(self.warnings),
            "clarification_needed": list(self.clarification_needed),
            "errors": list(self.errors),
            "summary": self.summary,
        }
