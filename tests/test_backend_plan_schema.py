import unittest
from unittest.mock import patch

from app.backend.classifier import classify_request
from app.backend.models import GenerationPlan
from app.backend.normalizer import normalize_request
from app.backend.pipeline import generate_model_request
from app.backend.plan_bridge import bridge_canonical_plan_to_generation_plan, build_canonical_plan
from app.backend.runtime import GENERATED_SCRIPT_PATH
from app.backend.recipe_executor import RecipeExecutionResult, execute_recipe
from app.backend.recipe_builder import build_deterministic_recipe
from app.backend.recipe_schema import DeterministicRecipe, RecipeOp
from app.backend.plan_validator import validate_canonical_plan


class BackendPlanSchemaTests(unittest.TestCase):
    def test_bridge_creates_canonical_bracket_plan(self):
        request = "Make a reinforced mounting bracket 120 x 30 x 80 mm with four 5 mm holes and 6 mm thickness"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None

        canonical_plan = build_canonical_plan(plan)
        self.assertEqual(canonical_plan.schema_version, "1.0")
        self.assertEqual(canonical_plan.source_family, "bracket")
        self.assertEqual(canonical_plan.object_type, "bracket")
        self.assertEqual(canonical_plan.dimensions["base_length_mm"], 120.0)
        self.assertTrue(any(feature.type == "hole_pattern" for feature in canonical_plan.features))

        bridged_plan = bridge_canonical_plan_to_generation_plan(canonical_plan, source_plan=plan)
        self.assertEqual(bridged_plan.family, "bracket")
        self.assertEqual(bridged_plan.dimensions["base_length_mm"], 120.0)

    def test_recipe_builder_creates_deterministic_bracket_recipe(self):
        request = "Make a reinforced mounting bracket 120 x 30 x 80 mm with four 5 mm holes and 6 mm thickness"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None

        canonical_plan = build_canonical_plan(plan)
        validation = validate_canonical_plan(canonical_plan)
        self.assertTrue(validation.is_valid)

        recipe_result = build_deterministic_recipe(validation.normalized_plan)
        self.assertTrue(recipe_result.is_valid)
        self.assertEqual(recipe_result.normalized_recipe.object_type, "bracket")
        self.assertGreaterEqual(len(recipe_result.normalized_recipe.ops), 2)
        self.assertTrue(any(feature.type == "gusset" for feature in canonical_plan.features))
        op_names = [op.op for op in recipe_result.normalized_recipe.ops]
        self.assertIn("bracket_body", op_names)
        self.assertIn("hole_pattern", op_names)
        self.assertGreater(op_names.index("hole_pattern"), op_names.index("bracket_body"))
        body_op = next(op for op in recipe_result.normalized_recipe.ops if op.id == "bracket_body")
        self.assertEqual(body_op.params["base_length_mm"], 120.0)
        self.assertEqual(body_op.params["flange_width_mm"], 30.0)
        self.assertEqual(body_op.params["vertical_height_mm"], 80.0)
        self.assertEqual(body_op.params["thickness_mm"], 6.0)
        self.assertTrue(all(op.op in {"bracket_body", "hole_pattern", "add_hole", "shell", "flatten_bottom", "add_cylinder", "add_sphere", "boolean_difference", "add_box", "boolean_union"} for op in recipe_result.normalized_recipe.ops))

    def test_bracket_recipe_matches_build_spec_golden_prompt(self):
        request = "make a bracket 120 x 40 x 90 mm"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None

        canonical_plan = build_canonical_plan(plan)
        validation = validate_canonical_plan(canonical_plan)
        self.assertTrue(validation.is_valid)

        recipe_result = build_deterministic_recipe(validation.normalized_plan)
        self.assertTrue(recipe_result.is_valid)
        op_names = [op.op for op in recipe_result.normalized_recipe.ops]
        self.assertIn("bracket_body", op_names)
        self.assertLess(op_names.index("bracket_body"), op_names.index("hole_pattern"))

    def test_hook_mount_recipe_builds_direct_body(self):
        request = "make a wall hook"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None

        canonical_plan = build_canonical_plan(plan)
        self.assertEqual(canonical_plan.object_type, "hook_mount")
        self.assertTrue(any(feature.type == "hook_mount_body" for feature in canonical_plan.features))

        validation = validate_canonical_plan(canonical_plan)
        self.assertTrue(validation.is_valid)

        recipe_result = build_deterministic_recipe(validation.normalized_plan)
        self.assertTrue(recipe_result.is_valid)
        self.assertEqual(recipe_result.normalized_recipe.object_type, "hook_mount")
        self.assertEqual(recipe_result.normalized_recipe.implementation_id, "hook_mount_wall_hook_v1")
        op_names = [op.op for op in recipe_result.normalized_recipe.ops]
        self.assertIn("hook_mount_body", op_names)
        self.assertIn("hole_pattern", op_names)
        self.assertLess(op_names.index("hook_mount_body"), op_names.index("hole_pattern"))
        body_op = next(op for op in recipe_result.normalized_recipe.ops if op.id == "hook_mount_body")
        self.assertGreater(body_op.params["width_mm"], 0.0)
        self.assertGreater(body_op.params["height_mm"], 0.0)
        self.assertGreater(body_op.params["depth_mm"], 0.0)
        self.assertGreater(body_op.params["thickness_mm"], 0.0)

        execution = execute_recipe(recipe_result.normalized_recipe)
        self.assertTrue(execution.executed)
        self.assertFalse(execution.fallback_required)
        self.assertEqual(execution.execution_path, "recipe")
        self.assertIn("make_hook_mount_body", execution.script_text)
        self.assertIn("plate_thickness", execution.script_text)
        self.assertIn("arm_start_x", execution.script_text)
        self.assertIn("arm_tip_x", execution.script_text)
        self.assertIn("hook_tip_z", execution.script_text)
        self.assertIn("profile = [", execution.script_text)
        self.assertIn("HookMountHole", execution.script_text)
        self.assertIn("Geomancer_Final", execution.script_text)
        self.assertNotIn("join_objects([base_plate, hook_arm, hook_lip]", execution.script_text)

    def test_recipe_executor_executes_supported_bracket_recipe(self):
        request = "Make a reinforced mounting bracket 120 x 30 x 80 mm with four 5 mm holes and 6 mm thickness"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None

        canonical_plan = build_canonical_plan(plan)
        validation = validate_canonical_plan(canonical_plan)
        self.assertTrue(validation.is_valid)
        recipe_result = build_deterministic_recipe(validation.normalized_plan)
        self.assertTrue(recipe_result.is_valid)

        execution = execute_recipe(recipe_result.normalized_recipe)
        self.assertTrue(execution.executed)
        self.assertFalse(execution.fallback_required)
        self.assertEqual(execution.execution_path, "recipe")
        self.assertIn("make_bracket_body", execution.script_text)
        self.assertIn("# Family: bracket", execution.script_text)
        self.assertIn("# Execution recipe: bracket", execution.script_text)
        self.assertIn("# Family implementation: bracket", execution.script_text)
        self.assertNotIn("join_objects([base_leg, vertical_leg]", execution.script_text)
        self.assertIn("Geomancer_Final", execution.script_text)
        self.assertNotIn("BracketBevel", execution.script_text)

    def test_recipe_executor_gracefully_disables_gusset_for_four_holes(self):
        request = "Make a reinforced mounting bracket 120 x 40 x 90 mm with 4 holes"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None

        canonical_plan = build_canonical_plan(plan)
        validation = validate_canonical_plan(canonical_plan)
        self.assertTrue(validation.is_valid)
        recipe_result = build_deterministic_recipe(validation.normalized_plan)
        self.assertTrue(recipe_result.is_valid)

        op_ids = [op.id for op in recipe_result.normalized_recipe.ops]
        self.assertNotIn("gusset", op_ids)
        execution = execute_recipe(recipe_result.normalized_recipe)
        self.assertTrue(execution.executed)
        self.assertFalse(execution.fallback_required)
        self.assertIn("BracketBaseHole", execution.script_text)
        self.assertIn("make_bracket_body", execution.script_text)

    def test_recipe_executor_executes_supported_phone_stand_recipe(self):
        plan = GenerationPlan(
            family="phone_stand",
            family_label="phone stand",
            recipe="phone_stand",
            request_text="make a phone stand",
            dimensions={
                "width_mm": 86.0,
                "depth_mm": 96.0,
                "height_mm": 120.0,
                "thickness_mm": 5.0,
                "viewing_angle_deg": 65.0,
                "lip_height_mm": 5.0,
                "cradle_depth_mm": 24.0,
                "device_width_mm": 72.0,
            },
            features={"with_cable_cutout": False},
        )
        canonical_plan = build_canonical_plan(plan)
        validation = validate_canonical_plan(canonical_plan)
        self.assertTrue(validation.is_valid)
        recipe_result = build_deterministic_recipe(validation.normalized_plan)
        self.assertTrue(recipe_result.is_valid)
        self.assertEqual(recipe_result.normalized_recipe.object_type, "phone_stand")
        self.assertTrue(any(op.id == "phone_stand_body" for op in recipe_result.normalized_recipe.ops))
        execution = execute_recipe(recipe_result.normalized_recipe)
        self.assertTrue(execution.executed)
        self.assertFalse(execution.fallback_required)
        self.assertEqual(execution.execution_path, "recipe")
        self.assertIn("make_phone_stand_body", execution.script_text)
        self.assertIn("base_back_y", execution.script_text)
        self.assertIn("support_step_z", execution.script_text)
        self.assertIn("lip_back_y", execution.script_text)
        self.assertNotIn("support_y, support_peak_z", execution.script_text)
        self.assertIn("Geomancer_Final", execution.script_text)
        self.assertNotIn("join_objects([base_plate, support_anchor", execution.script_text)

    def test_recipe_executor_executes_supported_tray_recipe(self):
        request = "make a tray"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None

        canonical_plan = build_canonical_plan(plan)
        self.assertEqual(canonical_plan.object_type, "tray")
        opening_feature = next(feature for feature in canonical_plan.features if feature.type == "opening")
        self.assertTrue(opening_feature.params["open_top"])
        validation = validate_canonical_plan(canonical_plan)
        self.assertTrue(validation.is_valid)
        self.assertLessEqual(validation.normalized_plan.dimensions["height_mm"], 36.0)
        self.assertGreater(validation.normalized_plan.dimensions["base_thickness_mm"], validation.normalized_plan.dimensions["wall_thickness_mm"])

        recipe_result = build_deterministic_recipe(validation.normalized_plan)
        self.assertTrue(recipe_result.is_valid)
        self.assertEqual(recipe_result.normalized_recipe.object_type, "tray")
        self.assertEqual(recipe_result.normalized_recipe.implementation_id, "tray_box_shell_v1")

        execution = execute_recipe(recipe_result.normalized_recipe)
        self.assertTrue(execution.executed)
        self.assertFalse(execution.fallback_required)
        self.assertEqual(execution.execution_path, "recipe")
        self.assertIn("InnerCavity", execution.script_text)
        self.assertIn("# Implementation ID: tray_box_shell_v1", execution.script_text)
        self.assertIn("Geomancer_Final", execution.script_text)
        self.assertNotIn("join_objects([outer_box, tray_rim]", execution.script_text)

    def test_phone_stand_lip_height_is_clamped_to_remain_visible(self):
        plan = GenerationPlan(
            family="phone_stand",
            family_label="phone stand",
            recipe="phone_stand",
            request_text="make a phone stand",
            dimensions={
                "width_mm": 86.0,
                "depth_mm": 96.0,
                "height_mm": 120.0,
                "thickness_mm": 5.0,
                "viewing_angle_deg": 65.0,
                "lip_height_mm": 1.0,
                "cradle_depth_mm": 24.0,
                "device_width_mm": 72.0,
            },
            features={"with_cable_cutout": False},
        )
        canonical_plan = build_canonical_plan(plan)
        validation = validate_canonical_plan(canonical_plan)
        self.assertTrue(validation.is_valid)
        self.assertGreaterEqual(validation.normalized_plan.dimensions["lip_height_mm"], 4.0)

    def test_recipe_builder_rejects_unsupported_object_type(self):
        canonical_plan = build_canonical_plan(
            GenerationPlan(
                family="bracket",
                family_label="bracket",
                recipe="bracket",
                request_text="bracket",
                dimensions={"base_length_mm": 120.0, "flange_width_mm": 30.0, "vertical_height_mm": 80.0, "thickness_mm": 6.0},
                features={"hole_diameter_mm": 5.0, "hole_count": 4, "gusset": True},
            )
        )
        canonical_plan.object_type = "unsupported_widget"
        recipe_result = build_deterministic_recipe(canonical_plan)
        self.assertFalse(recipe_result.is_valid)
        self.assertEqual(recipe_result.status, "invalid")
        self.assertTrue(recipe_result.errors)

    def test_recipe_executor_falls_back_for_unsupported_object_type(self):
        recipe = DeterministicRecipe(
            object_type="unsupported_widget",
            source_family="bracket",
            source_recipe="bracket",
            ops=[RecipeOp(op="add_box", id="body", params={"size_x_mm": 10.0, "size_y_mm": 10.0, "size_z_mm": 10.0})],
        )
        execution = execute_recipe(recipe)
        self.assertFalse(execution.executed)
        self.assertTrue(execution.fallback_required)
        self.assertEqual(execution.execution_path, "legacy")
        self.assertEqual(execution.fallback_reason, "unsupported_recipe_object_type")
        self.assertTrue(execution.unsupported_reasons)

    def test_validator_accepts_valid_supported_plan(self):
        plan = GenerationPlan(
            family="enclosure",
            family_label="enclosure",
            recipe="box_shell",
            request_text="enclosure",
            dimensions={"width_mm": 120.0, "depth_mm": 80.0, "height_mm": 50.0},
            features={"wall_thickness_mm": 3.0, "base_thickness_mm": 4.0, "open_top": False, "front_opening": False},
        )
        canonical_plan = build_canonical_plan(plan)
        opening_feature = next(feature for feature in canonical_plan.features if feature.type == "opening")
        self.assertTrue(opening_feature.params["open_top"])
        validation = validate_canonical_plan(canonical_plan)
        self.assertTrue(validation.is_valid)
        self.assertEqual(validation.status, "valid")
        self.assertEqual(validation.normalized_plan.dimensions["width_mm"], 120.0)
        self.assertFalse(validation.errors)

    def test_enclosure_shell_plan_carries_base_thickness_and_bevel(self):
        request = "Create a 120 x 80 x 50 mm enclosure with 3 mm walls"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None

        canonical_plan = build_canonical_plan(plan)
        shell_feature = next(feature for feature in canonical_plan.features if feature.type == "shell")
        self.assertIn("base_thickness_mm", shell_feature.params)
        opening_feature = next(feature for feature in canonical_plan.features if feature.type == "opening")
        self.assertTrue(opening_feature.params["open_top"])
        validation = validate_canonical_plan(canonical_plan)
        self.assertTrue(validation.is_valid)

        recipe_result = build_deterministic_recipe(validation.normalized_plan)
        self.assertTrue(recipe_result.is_valid)
        execution = execute_recipe(recipe_result.normalized_recipe)
        self.assertTrue(execution.executed)
        self.assertIn("ShellBevel", execution.script_text)

    def test_validator_rejects_negative_dimensions(self):
        canonical_plan = build_canonical_plan(
            GenerationPlan(
                family="bracket",
                family_label="bracket",
                recipe="bracket",
                request_text="bracket",
                dimensions={"base_length_mm": -120.0, "flange_width_mm": 30.0, "vertical_height_mm": 80.0, "thickness_mm": 6.0},
                features={"hole_diameter_mm": 5.0, "hole_count": 4, "gusset": True},
            )
        )
        validation = validate_canonical_plan(canonical_plan)
        self.assertFalse(validation.is_valid)
        self.assertEqual(validation.status, "invalid")
        self.assertTrue(validation.errors)

    def test_validator_clamps_unsafe_bracket_hole_diameter(self):
        canonical_plan = build_canonical_plan(
            GenerationPlan(
                family="bracket",
                family_label="bracket",
                recipe="bracket",
                request_text="bracket",
                dimensions={"base_length_mm": 120.0, "flange_width_mm": 40.0, "vertical_height_mm": 90.0, "thickness_mm": 6.0},
                features={"hole_diameter_mm": 30.0, "hole_count": 4, "gusset": True},
            )
        )
        validation = validate_canonical_plan(canonical_plan)
        self.assertTrue(validation.is_valid)
        hole_feature = next(feature for feature in validation.normalized_plan.features if feature.type == "hole_pattern")
        self.assertLessEqual(hole_feature.params["diameter_mm"], 8.0)

    def test_pipeline_stops_before_generation_on_invalid_canonical_plan(self):
        request = "Make a bracket 120 x 30 x 80 mm with four 5 mm holes and 6 mm thickness"
        invalid_plan = GenerationPlan(
            family="bracket",
            family_label="bracket",
            recipe="bracket",
            request_text=request,
            dimensions={"base_length_mm": -120.0, "flange_width_mm": 30.0, "vertical_height_mm": 80.0, "thickness_mm": 6.0},
            features={"hole_diameter_mm": 5.0, "hole_count": 4, "gusset": True},
        )
        with patch("app.backend.pipeline.normalize_request", return_value=("ready", "", invalid_plan)), patch(
            "app.backend.pipeline.save_generated_script"
        ) as save_script, patch("app.backend.pipeline.export_preview_model") as export_preview, patch(
            "app.backend.pipeline.load_state", return_value={}
        ), patch("app.backend.pipeline.save_state") as save_state, patch("app.backend.pipeline.add_saved_model_entry") as add_saved_model_entry:
            result = generate_model_request(request, log=lambda _msg: None)

        self.assertEqual(result["status"], "validation_failed")
        self.assertEqual(result["raw_status"], "invalid")
        save_script.assert_not_called()
        export_preview.assert_not_called()
        add_saved_model_entry.assert_not_called()
        self.assertEqual(save_state.call_count, 2)

    def test_pipeline_returns_recipe_payload_for_valid_prompt(self):
        with patch("app.backend.pipeline.save_generated_script") as save_script, patch(
            "app.backend.pipeline.export_preview_model",
            return_value=(True, "Preview exported successfully."),
        ), patch("app.backend.pipeline.load_state", return_value={}), patch("app.backend.pipeline.save_state") as save_state, patch(
            "app.backend.pipeline.add_saved_model_entry",
            return_value={"id": "saved-model-4"},
        ):
            result = generate_model_request("Create a 120 x 80 x 50 mm enclosure with 3 mm walls", log=lambda _msg: None)

        save_script.assert_called_once()
        self.assertEqual(save_state.call_count, 2)
        self.assertEqual(result["status"], "ready")
        self.assertIn("recipe", result)
        self.assertEqual(result["recipe"]["object_type"], "enclosure")
        self.assertTrue(result["recipe"]["ops"])
        self.assertIn("execution_path", result)
        self.assertEqual(result["generation_path"], "recipe")
        self.assertEqual(result["generation_route"], "recipe_success")

    def test_pipeline_quarantines_legacy_fallback_for_recipe_only_family(self):
        unsupported_execution = RecipeExecutionResult(
            executed=False,
            fallback_required=True,
            warnings=[],
            unsupported_ops=["hole_pattern"],
            unsupported_reasons=["Unsupported recipe op: hole_pattern."],
            execution_path="legacy",
            summary="Legacy fallback required for unsupported recipe execution details.",
        )
        with patch("app.backend.pipeline.execute_recipe", return_value=unsupported_execution), patch(
            "app.backend.pipeline.build_script",
            return_value="legacy blender script",
        ) as build_script, patch("app.backend.pipeline.save_generated_script") as save_script, patch(
            "app.backend.pipeline.export_preview_model",
            return_value=(True, "Preview exported successfully."),
        ), patch("app.backend.pipeline.load_state", return_value={}), patch("app.backend.pipeline.save_state") as save_state, patch(
            "app.backend.pipeline.add_saved_model_entry",
            return_value={"id": "saved-model-4"},
        ):
            result = generate_model_request("Create a 120 x 80 x 50 mm enclosure with 3 mm walls", log=lambda _msg: None)

        build_script.assert_not_called()
        save_script.assert_not_called()
        self.assertEqual(save_state.call_count, 2)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["raw_status"], "error")
        self.assertEqual(result["generation_path"], "")
        self.assertEqual(result["generation_route"], "")

    def test_pipeline_can_still_fall_back_for_primitive_assembly(self):
        unsupported_execution = RecipeExecutionResult(
            executed=False,
            fallback_required=True,
            warnings=[],
            unsupported_ops=["add_box"],
            unsupported_reasons=["Unsupported recipe op: add_box."],
            execution_path="legacy",
            summary="Legacy fallback required for unsupported recipe execution details.",
        )
        with patch("app.backend.pipeline.execute_recipe", return_value=unsupported_execution), patch(
            "app.backend.pipeline.build_script",
            return_value="legacy blender script",
        ) as build_script, patch("app.backend.pipeline.save_generated_script") as save_script, patch(
            "app.backend.pipeline.export_preview_model",
            return_value=(True, "Preview exported successfully."),
        ), patch("app.backend.pipeline.load_state", return_value={}), patch("app.backend.pipeline.save_state") as save_state, patch(
            "app.backend.pipeline.add_saved_model_entry",
            return_value={"id": "saved-model-4"},
        ):
            result = generate_model_request("make a primitive assembly 80 x 50 x 40", log=lambda _msg: None)

        build_script.assert_called_once()
        save_script.assert_called_once_with("legacy blender script", GENERATED_SCRIPT_PATH)
        self.assertEqual(save_state.call_count, 2)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["execution_path"], "legacy")
        self.assertEqual(result["generation_path"], "legacy")
        self.assertEqual(result["generation_route"], "legacy_fallback_unsupported_recipe_op")


if __name__ == "__main__":
    unittest.main()
