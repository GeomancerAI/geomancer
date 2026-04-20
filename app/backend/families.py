"""Supported Geomancer alpha families and extension metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FamilyDefinition:
    """Definition for one supported alpha family."""

    key: str
    label: str
    recipe: str
    aliases: tuple[str, ...]
    summary: str


FAMILY_DEFINITIONS: tuple[FamilyDefinition, ...] = (
    FamilyDefinition("enclosure", "enclosure", "box_shell", ("enclosure", "case", "box enclosure", "project box", "electronics case", "housing"), "Rectangular shell or case blockout."),
    FamilyDefinition("bracket", "bracket", "bracket", ("bracket", "mounting bracket", "angle bracket", "l bracket", "l-bracket"), "Simple L-style support bracket blockout."),
    FamilyDefinition("cable_clip", "cable clip", "cable_clip", ("cable clip", "clip", "wire clip", "cable holder"), "Open clip for holding a cable or wire bundle."),
    FamilyDefinition("planter_vessel", "planter / vessel", "vessel", ("planter", "vessel", "pot", "cup", "container"), "Round open-top vessel or planter blockout."),
    FamilyDefinition("gear", "gear", "gear", ("gear", "spur gear", "cog", "cogwheel"), "Simplified radial gear blockout with rectangular teeth."),
    FamilyDefinition("adapter", "adapter", "adapter", ("adapter", "coupler", "reducer", "bushing"), "Stepped cylindrical adapter or coupler blockout."),
    FamilyDefinition("panel_plate", "panel / plate", "panel_plate", ("panel", "plate", "face plate", "cover plate", "mounting plate"), "Flat plate or panel with optional mounting holes."),
    FamilyDefinition("spacer_standoff", "spacer / standoff", "standoff", ("spacer", "standoff", "standoff spacer", "bushing spacer"), "Simple spacer or standoff with optional center hole."),
    FamilyDefinition("tray_box", "tray / box", "tray_box", ("tray", "open box", "parts tray", "bin", "organizer tray"), "Open-top tray or shallow box blockout."),
    FamilyDefinition("hook_mount", "simple hook / mount", "hook_mount", ("hook", "mount", "hanger", "wall hook"), "Simple mounted hook blockout."),
    FamilyDefinition("phone_stand", "phone stand", "phone_stand", ("phone stand", "smartphone stand", "cell phone stand", "mobile phone stand", "phone dock", "device stand"), "Deterministic phone stand blockout with a stable base and angled support."),
    FamilyDefinition("housing_shell", "simple housing / mechanical shell", "box_shell", ("housing", "shell", "mechanical shell", "cover"), "Mechanical shell blockout using conservative enclosure geometry."),
    FamilyDefinition("primitive_assembly", "dimensional primitive/blockout assemblies", "primitive_assembly", ("assembly", "blockout", "primitive assembly", "blockout assembly", "primitive"), "Simple assembly made from deterministic primitives."),
)

SUPPORTED_ALPHA_FAMILIES = [family.key for family in FAMILY_DEFINITIONS]
FAMILY_BY_KEY = {family.key: family for family in FAMILY_DEFINITIONS}
