import unittest

from app.backend.plan_schema import (
    ALLOWED_COMPONENT_TYPES,
    ALLOWED_COMPOSITION_ITEM_TYPES,
    ALLOWED_CONSTRUCTION_MODES,
    ALLOWED_OBJECT_TYPES,
    GeomancerComponent,
    GeomancerCompositionItem,
    GeomancerHybridDetail,
    GeomancerIntent,
    GeomancerPlan,
    GeomancerStyle,
    PLAN_SCHEMA_VERSION,
    ALLOWED_STYLE_PROFILES,
)
from app.backend.plan_validator import validate_plan


class BackendPlanSchemaTests(unittest.TestCase):
    def test_plan_schema_serializes_authoritative_v1_shape(self):
        plan = GeomancerPlan(
            request_text="Create a simple wall-mounted phone stand with a cable cutout",
            intent=GeomancerIntent(
                object_type="phone_stand",
                object_label="wall-mounted phone stand",
                use_case="hold_phone",
            ),
            dimensions={
                "overall_width_mm": 90,
                "overall_depth_mm": 85,
                "overall_height_mm": 120,
                "material_thickness_mm": 5,
            },
            components=[
                GeomancerComponent(
                    id="base",
                    type="base_plate",
                    params={"width_mm": 90, "depth_mm": 85, "thickness_mm": 5},
                )
            ],
        )

        payload = plan.to_dict()

        self.assertEqual(payload["schema_version"], PLAN_SCHEMA_VERSION)
        self.assertEqual(payload["construction_mode"], "constraint")
        self.assertEqual(payload["units"], "mm")
        self.assertEqual(payload["intent"]["object_type"], "phone_stand")
        self.assertEqual(payload["components"][0]["type"], "base_plate")
        self.assertEqual(payload["style"]["style_profile"], "minimal")
        self.assertEqual(payload["composition"], [])
        self.assertIn("phone_stand", ALLOWED_OBJECT_TYPES)
        self.assertIn("base_plate", ALLOWED_COMPONENT_TYPES)
        self.assertIn("constraint", ALLOWED_CONSTRUCTION_MODES)
        self.assertIn("hybrid", ALLOWED_CONSTRUCTION_MODES)
        self.assertIn("cube", ALLOWED_COMPOSITION_ITEM_TYPES)
        self.assertIn("rounded", ALLOWED_STYLE_PROFILES)

    def test_composition_item_serializes_cleanly(self):
        item = GeomancerCompositionItem(
            id="crate_body",
            type="cube",
            operation="union",
            params={"width_mm": 80, "depth_mm": 80, "height_mm": 60},
            position=[0.0, 0.0, 0.0],
        )

        self.assertEqual(
            item.to_dict(),
            {
                "id": "crate_body",
                "type": "cube",
                "operation": "union",
                "params": {"width_mm": 80, "depth_mm": 80, "height_mm": 60},
                "position": [0.0, 0.0, 0.0],
            },
        )

    def test_hybrid_detail_serializes_cleanly(self):
        detail = GeomancerHybridDetail(
            id="crate_mount_holes",
            source_mode="constraint",
            type="hole_pattern",
            operation="difference",
            params={"count": 4, "diameter_mm": 5.0, "layout": "corners"},
            position=[0.0, 0.0, 0.0],
        )

        self.assertEqual(
            detail.to_dict(),
            {
                "id": "crate_mount_holes",
                "source_mode": "constraint",
                "type": "hole_pattern",
                "operation": "difference",
                "params": {"count": 4, "diameter_mm": 5.0, "layout": "corners"},
                "position": [0.0, 0.0, 0.0],
            },
        )

    def test_style_serializes_cleanly(self):
        style = GeomancerStyle(
            style_profile="sci_fi",
            shape_language="panelized",
            edge_treatment="hard",
            detail_density="medium",
            accent_profile="panels",
        )

        self.assertEqual(
            style.to_dict(),
            {
                "style_profile": "sci_fi",
                "shape_language": "panelized",
                "edge_treatment": "hard",
                "detail_density": "medium",
                "accent_profile": "panels",
            },
        )

    def test_validator_rejects_unknown_object_type(self):
        result = validate_plan(
            {
                "request_text": "unknown thing",
                "intent": {"object_type": "dragon"},
                "components": [{"id": "base", "type": "base_plate", "params": {"thickness_mm": 5}}],
            }
        )

        self.assertEqual(result.status, "invalid")
        self.assertTrue(any("Unsupported object type" in error for error in result.errors))

    def test_validator_rejects_unknown_component_type(self):
        result = validate_plan(
            {
                "request_text": "plate",
                "intent": {"object_type": "plate"},
                "components": [{"id": "mystery", "type": "weird_feature", "params": {}}],
            }
        )

        self.assertEqual(result.status, "invalid")
        self.assertTrue(any("Unsupported component type" in error for error in result.errors))

    def test_validator_accepts_compositional_plan(self):
        result = validate_plan(
            {
                "request_text": "low poly crate",
                "construction_mode": "compositional",
                "intent": {"object_type": "crate", "printable": True},
                "composition": [
                    {
                        "id": "crate_body",
                        "type": "cube",
                        "operation": "union",
                        "params": {"width_mm": 80, "depth_mm": 80, "height_mm": 60},
                    }
                ],
            }
        )

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.normalized_plan.construction_mode, "compositional")
        self.assertEqual(result.normalized_plan.composition[0].type, "cube")
        self.assertTrue(result.normalized_plan.dimensions["overall_width_mm"] >= 80)

    def test_validator_clamps_thickness_and_emits_warning(self):
        result = validate_plan(
            {
                "request_text": "thin bracket",
                "intent": {"object_type": "bracket", "printable": True},
                "dimensions": {
                    "overall_width_mm": 120,
                    "overall_depth_mm": 30,
                    "overall_height_mm": 80,
                    "material_thickness_mm": "1.0",
                },
                "components": [
                    {
                        "id": "horizontal_leg",
                        "type": "horizontal_leg",
                        "params": {"length_mm": 120, "width_mm": 30, "thickness_mm": 1.5},
                    }
                ],
            }
        )

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.normalized_plan.dimensions["material_thickness_mm"], 2.4)
        self.assertEqual(result.normalized_plan.components[0].params["thickness_mm"], 2.4)
        self.assertTrue(any("clamped" in warning for warning in result.warnings))

    def test_validator_requires_dimensions_for_supported_printable_object(self):
        result = validate_plan(
            {
                "request_text": "make a bracket",
                "intent": {"object_type": "bracket", "printable": True},
                "components": [{"id": "horizontal_leg", "type": "horizontal_leg", "params": {}}],
            }
        )

        self.assertEqual(result.status, "clarify")
        self.assertTrue(any("overall_width_mm" in item for item in result.normalized_plan.missing_info))

    def test_validator_rejects_unrealistically_large_hole_pattern(self):
        result = validate_plan(
            {
                "request_text": "plate",
                "intent": {"object_type": "plate"},
                "dimensions": {
                    "overall_width_mm": 80,
                    "overall_height_mm": 60,
                    "material_thickness_mm": 4,
                },
                "components": [
                    {"id": "base", "type": "base_plate", "params": {"width_mm": 80, "height_mm": 60, "thickness_mm": 4}},
                    {"id": "holes", "type": "hole_pattern", "params": {"count": 4, "diameter_mm": 50}},
                ],
            }
        )

        self.assertEqual(result.status, "invalid")
        self.assertTrue(any("unrealistically large" in error for error in result.errors))

    def test_validator_rejects_hole_wider_than_bracket_arm(self):
        result = validate_plan(
            {
                "request_text": "bracket",
                "intent": {"object_type": "bracket"},
                "dimensions": {
                    "overall_width_mm": 120,
                    "overall_depth_mm": 30,
                    "overall_height_mm": 80,
                    "material_thickness_mm": 4,
                },
                "components": [
                    {"id": "horizontal_leg", "type": "horizontal_leg", "params": {"length_mm": 120, "width_mm": 6, "thickness_mm": 4}},
                    {"id": "vertical_leg", "type": "vertical_leg", "params": {"height_mm": 80, "thickness_mm": 4}},
                    {"id": "holes", "type": "hole_pattern", "params": {"count": 2, "diameter_mm": 8}},
                ],
            }
        )

        self.assertEqual(result.status, "invalid")
        self.assertTrue(any("bracket arm" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
