import unittest
from unittest.mock import patch

from app.backend.archetypes import build_phone_stand_generation_plan, select_archetype
from app.backend.classifier import classify_request
from app.backend.pipeline import generate_model_request
from app.backend.normalizer import normalize_request
from app.backend.plan_bridge import build_canonical_plan
from app.backend.plan_validator import validate_canonical_plan
from app.backend.recipe_builder import build_deterministic_recipe
from app.backend.recipe_executor import execute_recipe


class BackendArchetypeTests(unittest.TestCase):
    def test_phone_stand_archetype_is_detected(self):
        selection = select_archetype("Make me a modern phone stand with a cable cutout for an iPhone 16")
        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.archetype_key, "phone_stand")
        self.assertEqual(selection.config.device_name, "iPhone 16")
        self.assertTrue(selection.config.with_cable_cutout)
        self.assertGreater(selection.confidence, 0.9)

    def test_phone_stand_archetype_uses_sensible_defaults(self):
        selection = select_archetype("make a phone stand")
        self.assertIsNotNone(selection)
        assert selection is not None

        plan = build_phone_stand_generation_plan("make a phone stand", selection)
        self.assertEqual(plan.family, "phone_stand")
        self.assertEqual(plan.dimensions["viewing_angle_deg"], 65.0)
        self.assertGreater(plan.dimensions["width_mm"], 0.0)
        self.assertGreater(plan.dimensions["depth_mm"], plan.dimensions["width_mm"] * 0.9)
        self.assertGreater(plan.dimensions["lip_height_mm"], 0.0)
        self.assertGreater(plan.dimensions["cradle_depth_mm"], 0.0)
        self.assertEqual(plan.features["orientation_preference"], "portrait")
        self.assertFalse(plan.features["with_cable_cutout"])

    def test_phone_stand_canonical_plan_and_recipe_are_valid(self):
        selection = select_archetype("make a modern phone stand with a cable cutout for an iPhone 16")
        self.assertIsNotNone(selection)
        assert selection is not None
        plan = build_phone_stand_generation_plan("make a modern phone stand with a cable cutout for an iPhone 16", selection)

        canonical_plan = build_canonical_plan(plan)
        self.assertEqual(canonical_plan.object_type, "phone_stand")
        self.assertTrue(any(feature.type == "retaining_lip" for feature in canonical_plan.features))
        validation = validate_canonical_plan(canonical_plan)
        self.assertTrue(validation.is_valid)
        recipe_result = build_deterministic_recipe(validation.normalized_plan)
        self.assertTrue(recipe_result.is_valid)
        self.assertEqual(recipe_result.normalized_recipe.object_type, "phone_stand")
        self.assertTrue(any(op.id == "phone_stand_body" for op in recipe_result.normalized_recipe.ops))
        self.assertFalse(any(op.id == "support_anchor" for op in recipe_result.normalized_recipe.ops))
        execution = execute_recipe(recipe_result.normalized_recipe)
        self.assertTrue(execution.executed)
        self.assertFalse(execution.fallback_required)
        self.assertEqual(execution.execution_path, "recipe")
        self.assertIn("make_phone_stand_body", execution.script_text)
        self.assertNotIn("join_objects([base_plate, support_anchor", execution.script_text)
        self.assertIn("Geomancer_Final", execution.script_text)

    def test_phone_stand_selector_rejects_competing_object_terms(self):
        self.assertIsNone(select_archetype("phone stand plate"))
        self.assertIsNone(select_archetype("phone stand bracket"))

    def test_phone_stand_pipeline_succeeds(self):
        with patch("app.backend.pipeline.save_generated_script") as save_script, patch(
            "app.backend.pipeline.export_preview_model",
            return_value=(True, "Preview exported successfully."),
        ), patch("app.backend.pipeline.load_state", return_value={}), patch("app.backend.pipeline.save_state") as save_state, patch(
            "app.backend.pipeline.add_saved_model_entry",
            return_value={"id": "saved-phone-stand"},
        ):
            result = generate_model_request("make me a phone stand with a cable cutout for an iPhone 16", log=lambda _msg: None)

        save_script.assert_called_once()
        self.assertEqual(save_state.call_count, 2)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["family"], "phone_stand")
        self.assertEqual(result["execution_path"], "recipe")
        self.assertIn("recipe", result)
        self.assertEqual(result["recipe"]["object_type"], "phone_stand")
        self.assertTrue(any(op["id"] == "phone_stand_body" for op in result["recipe"]["ops"]))
        self.assertEqual(result["implementation_id"], "phone_stand_cradle_v1")
        self.assertEqual(result["execution_recipe"], "phone_stand")

    def test_phone_stand_family_normalization_stays_supported(self):
        classification = classify_request("make a phone stand with a cable cutout")
        self.assertEqual(classification.status, "ready")
        self.assertEqual(classification.family_key, "phone_stand")
        status, _, plan = normalize_request("make a phone stand with a cable cutout", classification)
        self.assertEqual(status, "ready")
        assert plan is not None
        self.assertEqual(plan.family, "phone_stand")
        self.assertIn("with_cable_cutout", plan.features)
        self.assertTrue(plan.features["with_cable_cutout"])

    def test_non_phone_prompt_does_not_hit_archetype(self):
        selection = select_archetype("Make a reinforced mounting bracket 120 x 30 x 80 mm with four 5 mm holes")
        self.assertIsNone(selection)


if __name__ == "__main__":
    unittest.main()
