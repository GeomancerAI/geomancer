import copy
import unittest
import importlib.util
from pathlib import Path
from unittest.mock import patch

import app.backend.pipeline as pipeline

from app.backend.pipeline import generate_model_from_plan, generate_model_request, interpret_prompt_to_plan
from app.backend.plan_validator import validate_plan
from app.backend.recipe_builder import build_deterministic_recipe
from app.backend.recipe_executor import execute_recipe


class BackendAlphaPipelineTests(unittest.TestCase):
    def test_pipeline_success_path_does_not_call_legacy_routing(self):
        self.assertFalse(hasattr(pipeline, "classify_request"))
        self.assertFalse(hasattr(pipeline, "select_archetype"))
        self.assertFalse(hasattr(pipeline, "build_phone_stand_generation_plan"))
        self.assertFalse(hasattr(pipeline, "normalize_request"))

        with patch(
            "app.backend.pipeline.save_generated_script"
        ), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", return_value={}
        ), patch(
            "app.backend.pipeline.save_state", return_value=Path("ignored")
        ):
            result = generate_model_request("Create a 120 x 80 x 50 mm enclosure with 3 mm walls", log=lambda _msg: None)

        self.assertEqual(result["status"], "ready")

    def test_plan_bridge_module_is_deleted(self):
        self.assertIsNone(importlib.util.find_spec("app.backend.plan_bridge"))

    def test_pipeline_returns_desktop_compatible_result_keys(self):
        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", return_value={}
        ), patch(
            "app.backend.pipeline.save_state", return_value=Path("ignored")
        ):
            result = generate_model_request("make a bracket 120 x 40 x 90 mm with 6mm thick legs", log=lambda _msg: None)

        expected_keys = {
            "generation_id",
            "request_text",
            "status",
            "raw_status",
            "is_terminal",
            "plan",
            "validation",
            "recipe",
            "recipe_summary",
            "execution_path",
            "execution_summary",
            "generation_path",
            "generation_route",
            "generation_fallback_reason",
            "implementation_id",
            "execution_recipe",
            "validation_summary",
            "interpretation_summary",
            "decision_summary",
            "style_summary",
            "editable_params",
            "current_editable_params",
            "last_editable_params",
            "last_regeneration_source",
            "edited_plan_summary",
            "missing_info",
            "assumptions",
            "warnings",
            "preview_model_path",
            "preview_model_url",
            "preview_asset_version",
            "preview_export_status",
            "preview_export_message",
            "final_model_path",
            "final_model_url",
            "output_source",
            "stl_export_path",
            "stl_export_status",
            "stl_export_message",
            "stl_source_model_path",
            "saved_model_entry",
            "supported_families",
        }

        self.assertTrue(expected_keys.issubset(result.keys()))
        self.assertEqual(result["generation_path"], "recipe")
        self.assertEqual(result["generation_route"], "recipe_success")
        self.assertIn("recipe", result["decision_summary"])
        self.assertEqual(result["stl_export_status"], "not_requested")
        self.assertEqual(result["stl_export_path"], "")
        self.assertTrue(result["editable_params"])
        self.assertEqual(result["current_editable_params"], result["last_editable_params"])
        self.assertEqual(result["last_regeneration_source"], "")

    def test_pipeline_persists_expected_state_keys_after_generation_attempt(self):
        state: dict = {}

        def load_state() -> dict:
            return dict(state)

        def save_state(payload: dict) -> Path:
            state.clear()
            state.update(payload)
            return Path("ignored")

        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", side_effect=load_state
        ), patch(
            "app.backend.pipeline.save_state", side_effect=save_state
        ):
            result = generate_model_request("120 x 80 x 4 mm plate with 4 holes", log=lambda _msg: None)

        self.assertEqual(result["status"], "ready")
        expected_state_keys = {
            "last_user_request",
            "last_generation_id",
            "last_generated_script_path",
            "last_preview_model_path",
            "last_preview_model_url",
            "last_preview_asset_version",
            "last_preview_export_status",
            "last_preview_export_message",
            "last_final_model_path",
            "last_final_model_url",
            "last_output_source",
            "last_stl_export_path",
            "last_stl_export_status",
            "last_stl_export_message",
            "last_stl_source_model_path",
            "last_generation_timestamp",
            "last_generation_status",
            "last_generation_message",
            "last_generation_raw_status",
            "last_run_status",
            "last_generation_family",
            "last_validation_summary",
            "last_plan",
            "last_recipe",
            "last_recipe_summary",
            "last_execution_path",
            "last_execution_summary",
            "last_generation_path",
            "last_generation_route",
            "last_generation_fallback_reason",
            "last_implementation_id",
            "last_execution_recipe",
            "last_validation",
            "last_classification",
            "last_saved_model_entry",
            "last_interpretation_summary",
            "last_decision_summary",
            "last_style_summary",
            "current_editable_params",
            "last_editable_params",
            "last_regeneration_source",
            "edited_plan_summary",
            "last_missing_info",
            "last_assumptions",
            "last_warnings",
        }

        self.assertTrue(expected_state_keys.issubset(state.keys()))
        self.assertEqual(state["last_generation_family"], "plate")
        self.assertEqual(state["last_generation_path"], "recipe")
        self.assertEqual(state["last_generation_route"], "recipe_success")
        self.assertEqual(state["last_validation"]["status"], "ready")
        self.assertEqual(state["last_execution_recipe"], "panel_plate")
        self.assertTrue(state["last_interpretation_summary"])
        self.assertTrue(state["last_decision_summary"])
        self.assertEqual(state["last_missing_info"], [])
        self.assertTrue(state["last_assumptions"])
        self.assertIn("minimum wall thickness", " ".join(state["last_assumptions"]))
        self.assertTrue(isinstance(state["last_warnings"], list))
        self.assertTrue(state["last_style_summary"])
        self.assertEqual(state["last_stl_export_status"], "not_requested")
        self.assertEqual(state["last_stl_export_path"], "")

    def test_pipeline_success_path_exposes_editable_surface(self):
        state: dict = {}

        def load_state() -> dict:
            return dict(state)

        def save_state(payload: dict) -> Path:
            state.clear()
            state.update(payload)
            return Path("ignored")

        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", side_effect=load_state
        ), patch(
            "app.backend.pipeline.save_state", side_effect=save_state
        ):
            result = generate_model_request(
                "make a phone stand 90 x 85 x 120 mm with 5mm thick walls and cable cutout",
                log=lambda _msg: None,
            )

        self.assertEqual(result["status"], "ready")
        editable_ids = {item["id"] for item in result["editable_params"]}
        self.assertIn("dimension:overall_width_mm", editable_ids)
        self.assertIn("dimension:material_thickness_mm", editable_ids)
        self.assertIn("style:style_profile", editable_ids)
        self.assertEqual(result["current_editable_params"], result["last_editable_params"])
        self.assertTrue(result["edited_plan_summary"] == "" or result["edited_plan_summary"].startswith("No parameter changes"))

    def test_pipeline_regenerates_from_edited_plan_deterministically(self):
        state: dict = {}

        def load_state() -> dict:
            return dict(state)

        def save_state(payload: dict) -> Path:
            state.clear()
            state.update(payload)
            return Path("ignored")

        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", side_effect=load_state
        ), patch(
            "app.backend.pipeline.save_state", side_effect=save_state
        ):
            base = generate_model_request(
                "make a bracket 120 x 40 x 90 mm with 6mm thick legs and four 5 mm mounting holes",
                log=lambda _msg: None,
            )
            edited_plan = copy.deepcopy(base["plan"])
            edited_plan["dimensions"]["overall_width_mm"] = 150
            edited_plan["style"]["style_profile"] = "industrial"
            regenerated = generate_model_from_plan(
                edited_plan,
                log=lambda _msg: None,
                source_generation_id=base["generation_id"],
                source_request_text=base["request_text"],
                source_plan=base["plan"],
                current_saved_model_id="saved-model-1",
                current_saved_model_editable=True,
                last_opened_model_id="saved-model-1",
                reopen_source="saved_model",
                reopened_plan_summary="Reopened saved model saved-model-1 for editing.",
            )

        self.assertEqual(base["status"], "ready")
        self.assertEqual(regenerated["status"], "ready")
        self.assertEqual(regenerated["generation_route"], "edited_plan_success")
        self.assertEqual(regenerated["plan"]["dimensions"]["overall_width_mm"], 150)
        self.assertEqual(regenerated["plan"]["style"]["style_profile"], "industrial")
        self.assertTrue(regenerated["decision_summary"].startswith("Updated "))
        self.assertIn("Ready bracket", regenerated["decision_summary"])
        self.assertIn("overall width", regenerated["edited_plan_summary"].lower())
        self.assertTrue(regenerated["editable_params"])
        self.assertEqual(regenerated["last_regeneration_source"], "edited_plan:{}".format(base["generation_id"]))
        self.assertEqual(regenerated["current_saved_model_id"], "saved-model-1")
        self.assertTrue(regenerated["current_saved_model_editable"])
        self.assertEqual(regenerated["last_opened_model_id"], "saved-model-1")
        self.assertEqual(regenerated["reopen_source"], "saved_model")
        self.assertIn("Reopened saved model", regenerated["reopened_plan_summary"])

    def test_pipeline_invalid_edited_parameters_return_validation_failure(self):
        state: dict = {}

        def load_state() -> dict:
            return dict(state)

        def save_state(payload: dict) -> Path:
            state.clear()
            state.update(payload)
            return Path("ignored")

        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", side_effect=load_state
        ), patch(
            "app.backend.pipeline.save_state", side_effect=save_state
        ):
            base = generate_model_request("make a phone stand 90 x 85 x 120 mm with 5mm thick walls and cable cutout", log=lambda _msg: None)
            edited_plan = copy.deepcopy(base["plan"])
            opening_index = next(
                index for index, component in enumerate(edited_plan["components"])
                if component.get("type") == "opening"
            )
            edited_plan["components"][opening_index]["params"]["width_mm"] = 1000
            regenerated = generate_model_from_plan(
                edited_plan,
                log=lambda _msg: None,
                source_generation_id=base["generation_id"],
                source_request_text=base["request_text"],
                source_plan=base["plan"],
            )

        self.assertEqual(regenerated["status"], "validation_failed")
        self.assertEqual(regenerated["raw_status"], "invalid")
        self.assertTrue(regenerated["message"])
        self.assertIn("opening", regenerated["message"].lower())
        self.assertEqual(regenerated["plan"]["components"][opening_index]["params"]["width_mm"], 1000)
        self.assertTrue(regenerated["current_editable_params"])

    def test_pipeline_phone_stand_recipe_identity_is_deterministic(self):
        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", return_value={}
        ), patch(
            "app.backend.pipeline.save_state", return_value=Path("ignored")
        ):
            first = generate_model_request(
                "make a phone stand 90 x 85 x 120 mm with 5mm thick walls and a cable cutout",
                log=lambda _msg: None,
            )
            second = generate_model_request(
                "make a phone stand 90 x 85 x 120 mm with 5mm thick walls and a cable cutout",
                log=lambda _msg: None,
            )

        self.assertEqual(first["execution_recipe"], "phone_stand")
        self.assertEqual(first["implementation_id"], "phone_stand_cradle_v1")
        self.assertEqual(first["recipe"]["recipe_version"], "1.0")
        self.assertEqual(first["recipe"]["source_recipe"], "phone_stand")
        self.assertEqual(first["recipe"]["execution_recipe"], "phone_stand")
        self.assertEqual(first["plan"]["construction_mode"], "constraint")
        self.assertEqual(second["execution_recipe"], first["execution_recipe"])
        self.assertEqual(second["implementation_id"], first["implementation_id"])

    def test_pipeline_simple_phone_stand_uses_safe_defaults_and_records_assumptions(self):
        state: dict = {}

        def load_state() -> dict:
            return dict(state)

        def save_state(payload: dict) -> Path:
            state.clear()
            state.update(payload)
            return Path("ignored")

        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", side_effect=load_state
        ), patch(
            "app.backend.pipeline.save_state", side_effect=save_state
        ):
            result = generate_model_request("simple phone stand", log=lambda _msg: None)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["plan"]["dimensions"]["overall_width_mm"], 90.0)
        self.assertTrue(result["assumptions"])
        self.assertIn("smartphone-scale", " ".join(result["assumptions"]))
        self.assertIn("phone_stand", result["interpretation_summary"])
        self.assertIn("phone_stand", result["decision_summary"])
        self.assertEqual(state["last_assumptions"], result["assumptions"])
        self.assertEqual(state["last_missing_info"], [])

    def test_pipeline_routes_low_poly_crate_to_compositional_mode(self):
        state: dict = {}

        def load_state() -> dict:
            return dict(state)

        def save_state(payload: dict) -> Path:
            state.clear()
            state.update(payload)
            return Path("ignored")

        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", side_effect=load_state
        ), patch(
            "app.backend.pipeline.save_state", side_effect=save_state
        ):
            result = generate_model_request("simple sci-fi crate", log=lambda _msg: None)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["plan"]["construction_mode"], "compositional")
        self.assertEqual(result["plan"]["intent"]["object_type"], "crate")
        self.assertTrue(result["plan"]["composition"])
        self.assertEqual(result["plan"]["style"]["style_profile"], "sci_fi")
        self.assertEqual(result["execution_recipe"], "crate")
        self.assertEqual(result["implementation_id"], "crate_v1")
        self.assertTrue(result["assumptions"])
        self.assertIn("compositional", result["interpretation_summary"])
        self.assertIn("style", result["style_summary"].lower())

    def test_pipeline_routes_rounded_phone_stand_to_styled_constraint_mode(self):
        state: dict = {}

        def load_state() -> dict:
            return dict(state)

        def save_state(payload: dict) -> Path:
            state.clear()
            state.update(payload)
            return Path("ignored")

        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", side_effect=load_state
        ), patch(
            "app.backend.pipeline.save_state", side_effect=save_state
        ):
            result = generate_model_request(
                "rounded phone stand 90 x 85 x 120 mm with 5mm thick walls",
                log=lambda _msg: None,
            )

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["plan"]["construction_mode"], "constraint")
        self.assertEqual(result["plan"]["style"]["style_profile"], "rounded")
        self.assertIn("rounded", result["style_summary"].lower())
        self.assertTrue(any(op["op"] == "apply_bevel" for op in result["recipe"]["ops"]))

    def test_pipeline_routes_industrial_canister_with_mounting_tabs_to_hybrid_mode(self):
        state: dict = {}

        def load_state() -> dict:
            return dict(state)

        def save_state(payload: dict) -> Path:
            state.clear()
            state.update(payload)
            return Path("ignored")

        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", side_effect=load_state
        ), patch(
            "app.backend.pipeline.save_state", side_effect=save_state
        ):
            result = generate_model_request("industrial canister with mounting tabs", log=lambda _msg: None)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["plan"]["construction_mode"], "hybrid")
        self.assertEqual(result["plan"]["style"]["style_profile"], "industrial")
        self.assertIn("industrial", result["style_summary"].lower())
        self.assertTrue(result["plan"]["hybrid_details"])
        self.assertTrue(any(op["op"] == "apply_bevel" for op in result["recipe"]["ops"]))

    def test_pipeline_falls_back_cleanly_for_unsupported_style_pair(self):
        state: dict = {}

        def load_state() -> dict:
            return dict(state)

        def save_state(payload: dict) -> Path:
            state.clear()
            state.update(payload)
            return Path("ignored")

        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", side_effect=load_state
        ), patch(
            "app.backend.pipeline.save_state", side_effect=save_state
        ):
            result = generate_model_request("rounded bracket 120 x 40 x 90 mm with 4mm thick legs", log=lambda _msg: None)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["plan"]["style"]["style_profile"], "minimal")
        self.assertTrue(any("not supported" in warning for warning in result["warnings"]))
        self.assertIn("minimal style", result["style_summary"].lower())

    def test_pipeline_routes_crate_with_mounting_holes_to_hybrid_mode(self):
        state: dict = {}

        def load_state() -> dict:
            return dict(state)

        def save_state(payload: dict) -> Path:
            state.clear()
            state.update(payload)
            return Path("ignored")

        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", side_effect=load_state
        ), patch(
            "app.backend.pipeline.save_state", side_effect=save_state
        ):
            result = generate_model_request("crate with mounting holes", log=lambda _msg: None)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["plan"]["construction_mode"], "hybrid")
        self.assertEqual(result["plan"]["intent"]["object_type"], "crate")
        self.assertTrue(result["plan"]["composition"])
        self.assertTrue(result["plan"]["hybrid_details"])
        self.assertIn("hybrid", result["interpretation_summary"].lower())
        self.assertIn("hybrid", result["decision_summary"].lower())
        self.assertTrue(result["implementation_id"].endswith("_hybrid"))
        self.assertEqual(result["execution_recipe"], "crate")

    def test_pipeline_routes_pedestal_with_cable_slot_to_hybrid_mode(self):
        state: dict = {}

        def load_state() -> dict:
            return dict(state)

        def save_state(payload: dict) -> Path:
            state.clear()
            state.update(payload)
            return Path("ignored")

        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", side_effect=load_state
        ), patch(
            "app.backend.pipeline.save_state", side_effect=save_state
        ):
            result = generate_model_request("pedestal with a cable slot", log=lambda _msg: None)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["plan"]["construction_mode"], "hybrid")
        self.assertEqual(result["plan"]["intent"]["object_type"], "pedestal")
        self.assertTrue(result["plan"]["hybrid_details"])
        self.assertEqual(result["plan"]["hybrid_details"][0]["type"], "slot")
        self.assertIn("hybrid", result["interpretation_summary"].lower())

    def test_pipeline_routes_sci_fi_enclosure_with_raised_cylinder_details_to_hybrid_mode(self):
        state: dict = {}

        def load_state() -> dict:
            return dict(state)

        def save_state(payload: dict) -> Path:
            state.clear()
            state.update(payload)
            return Path("ignored")

        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model", return_value=(True, "Preview exported successfully.")
        ), patch(
            "app.backend.pipeline.add_saved_model_entry", return_value={"id": "saved-model-1"}
        ), patch(
            "app.backend.pipeline.load_state", side_effect=load_state
        ), patch(
            "app.backend.pipeline.save_state", side_effect=save_state
        ):
            result = generate_model_request("sci-fi enclosure with raised cylinder details", log=lambda _msg: None)

        self.assertEqual(result["status"], "validation_failed")
        self.assertEqual(result["raw_status"], "clarify")
        self.assertEqual(result["plan"]["construction_mode"], "hybrid")
        self.assertEqual(result["plan"]["intent"]["object_type"], "enclosure")
        self.assertTrue(result["plan"]["hybrid_details"])
        self.assertEqual(result["plan"]["hybrid_details"][0]["source_mode"], "compositional")
        self.assertIn("hybrid", result["interpretation_summary"].lower())
        self.assertIn("clarification", result["decision_summary"].lower())

    def test_pipeline_parses_barrel_dimensions_into_compositional_plan(self):
        interpreted = interpret_prompt_to_plan("barrel 60 x 60 x 100 mm")

        self.assertEqual(interpreted["status"], "ready")
        self.assertEqual(interpreted["plan"].construction_mode, "compositional")
        self.assertEqual(interpreted["plan"].intent.object_type, "barrel")
        self.assertEqual(interpreted["plan"].dimensions["overall_width_mm"], 60.0)
        self.assertEqual(interpreted["plan"].dimensions["overall_height_mm"], 100.0)
        self.assertTrue(interpreted["plan"].composition)

    def test_pipeline_returns_clarification_for_incomplete_supported_request(self):
        with patch("app.backend.pipeline.load_state", return_value={}), patch(
            "app.backend.pipeline.save_state", return_value=Path("ignored")
        ):
            result = generate_model_request("make a bracket", log=lambda _msg: None)

        self.assertEqual(result["status"], "validation_failed")
        self.assertEqual(result["raw_status"], "clarify")
        self.assertIn("Provide overall width", result["message"])
        self.assertEqual(
            result["missing_info"],
            ["overall_width_mm", "overall_depth_mm", "overall_height_mm", "material_thickness_mm"],
        )
        self.assertIn("Clarification needed", result["decision_summary"])

    def test_pipeline_parses_explicit_natural_language_dimensions(self):
        interpreted = interpret_prompt_to_plan("make a 22mm wide wall bracket with a 4mm depth and a 22mm height")

        self.assertEqual(interpreted["status"], "clarify")
        self.assertEqual(interpreted["plan"].dimensions["overall_width_mm"], 22.0)
        self.assertEqual(interpreted["plan"].dimensions["overall_depth_mm"], 4.0)
        self.assertEqual(interpreted["plan"].dimensions["overall_height_mm"], 22.0)
        self.assertNotIn("overall_width_mm", interpreted["missing_info"])
        self.assertNotIn("overall_depth_mm", interpreted["missing_info"])
        self.assertNotIn("overall_height_mm", interpreted["missing_info"])
        self.assertIn("material_thickness_mm", interpreted["missing_info"])

    def test_pipeline_parses_thickness_only_plate_prompt(self):
        interpreted = interpret_prompt_to_plan("3mm thick plate")

        self.assertEqual(interpreted["status"], "clarify")
        self.assertEqual(interpreted["plan"].dimensions["material_thickness_mm"], 3.0)
        self.assertIn("overall_width_mm", interpreted["missing_info"])
        self.assertIn("overall_height_mm", interpreted["missing_info"])
        self.assertNotIn("material_thickness_mm", interpreted["missing_info"])

    def test_pipeline_parses_compact_three_axis_dimensions_for_supported_objects(self):
        interpreted = interpret_prompt_to_plan("tray 120 x 80 x 20 mm")

        self.assertEqual(interpreted["status"], "clarify")
        self.assertEqual(interpreted["plan"].dimensions["overall_width_mm"], 120.0)
        self.assertEqual(interpreted["plan"].dimensions["overall_depth_mm"], 80.0)
        self.assertEqual(interpreted["plan"].dimensions["overall_height_mm"], 20.0)
        self.assertIn("material_thickness_mm", interpreted["missing_info"])

    def test_pipeline_prefers_labeled_dimensions_over_compact_patterns(self):
        interpreted = interpret_prompt_to_plan("bracket 120 x 80 x 20 mm width of 22mm")

        self.assertEqual(interpreted["status"], "clarify")
        self.assertEqual(interpreted["plan"].dimensions["overall_width_mm"], 22.0)
        self.assertEqual(interpreted["plan"].dimensions["overall_depth_mm"], 80.0)
        self.assertEqual(interpreted["plan"].dimensions["overall_height_mm"], 20.0)
        self.assertIn("material_thickness_mm", interpreted["missing_info"])

    def test_pipeline_rejects_unsupported_sculptural_request(self):
        with patch("app.backend.pipeline.load_state", return_value={}), patch(
            "app.backend.pipeline.save_state", return_value=Path("ignored")
        ):
            result = generate_model_request("Make me a dragon statue with mounting holes 120 x 80 x 20 mm", log=lambda _msg: None)

        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(result["raw_status"], "unsupported")
        self.assertFalse(result["execution_path"])
        self.assertFalse(result["recipe"])
        self.assertIn("outside the current supported object vocabulary", result["interpretation_summary"])

    def test_interpret_prompt_to_plan_returns_plan_v1_object(self):
        interpreted = interpret_prompt_to_plan("make a phone stand 90 x 85 x 120 mm with 5mm thick walls and cable cutout")
        self.assertEqual(interpreted["status"], "ready")
        self.assertEqual(interpreted["plan"].intent.object_type, "phone_stand")
        self.assertTrue(any(component.type == "retaining_lip" for component in interpreted["plan"].components))
        self.assertFalse(interpreted["missing_info"])

        validation = validate_plan(interpreted["plan"])
        recipe_result = build_deterministic_recipe(validation.normalized_plan)
        execution = execute_recipe(recipe_result.normalized_recipe)
        self.assertTrue(execution.executed)


if __name__ == "__main__":
    unittest.main()
