import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.state import DEFAULT_STATE
from app.backend.classifier import classify_request
from app.backend.geometry import build_script
from app.backend.models import GenerationPlan
from app.backend.normalizer import normalize_request
from app.backend.pipeline import generate_model_request
from app.blender_runner import open_generated_model_file
from app.backend.recipe_executor import RecipeExecutionResult
from app.path_utils import to_file_url
from desktop.backend_controller import BackendController


class BackendAlphaPipelineTests(unittest.TestCase):
    def test_classifier_maps_supported_family(self):
        result = classify_request("Create a 120 x 80 x 50 mm enclosure with 3 mm walls")
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.family_key, "enclosure")

    def test_normalizer_extracts_bracket_dimensions(self):
        request = "Make a bracket 100 x 30 x 80 mm with 6 mm thickness"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None
        self.assertEqual(plan.family, "bracket")
        self.assertEqual(plan.dimensions["base_length_mm"], 100.0)
        self.assertEqual(plan.dimensions["thickness_mm"], 6.0)

    def test_geometry_builds_family_specific_script(self):
        plan = GenerationPlan(
            family="panel_plate",
            family_label="panel / plate",
            recipe="panel_plate",
            request_text="plate",
            dimensions={"width_mm": 100.0, "height_mm": 60.0, "thickness_mm": 3.0},
            features={"hole_diameter_mm": 4.0, "corner_holes": True},
        )
        script = build_script(plan)
        self.assertIn("Geomancer_Final", script)
        self.assertIn("PanelHole", script)

    def test_bracket_geometry_reads_as_hardware_bracket(self):
        plan = GenerationPlan(
            family="bracket",
            family_label="bracket",
            recipe="bracket",
            request_text="mounting bracket",
            dimensions={"base_length_mm": 120.0, "flange_width_mm": 30.0, "vertical_height_mm": 80.0, "thickness_mm": 6.0},
            features={"hole_diameter_mm": 5.0, "hole_count": 4, "gusset": True},
        )
        script = build_script(plan)
        self.assertIn("base_leg", script)
        self.assertIn("vertical_leg", script)
        self.assertIn("JoinBracket", script)
        self.assertIn("final_obj = base_leg", script)
        self.assertNotIn("final_obj = join_objects([base_leg, vertical_leg", script)
        self.assertIn("BaseHole", script)
        self.assertIn("VerticalHole", script)
        self.assertIn("location=(mm(60.0), mm(15.0), mm(3.0))", script)
        self.assertIn("location=(mm(3.0), mm(15.0), mm(40.0))", script)
        self.assertNotIn("BracketBevel", script)

    def test_classifier_prefers_tray_for_open_top_box_language(self):
        result = classify_request("Create an open top parts box 140 x 90 x 35 mm with 3 mm walls")
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.family_key, "tray_box")
        self.assertGreater(result.confidence, 0.5)

    def test_pipeline_returns_tray_payload_for_open_top_prompt(self):
        with patch("app.backend.pipeline.save_generated_script") as save_script, patch(
            "app.backend.pipeline.export_preview_model",
            return_value=(True, "Preview exported successfully."),
        ), patch("app.backend.pipeline.load_state", return_value={}), patch("app.backend.pipeline.save_state") as save_state, patch(
            "app.backend.pipeline.add_saved_model_entry",
            return_value={"id": "saved-tray-1"},
        ):
            result = generate_model_request("make a tray", log=lambda _msg: None)

        save_script.assert_called_once()
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["family"], "tray_box")
        self.assertEqual(result["generation_path"], "recipe")
        self.assertEqual(result["generation_route"], "recipe_success")
        self.assertEqual(result["implementation_id"], "tray_box_shell_v1")
        self.assertEqual(result["execution_recipe"], "tray_box")
        self.assertEqual(result["output_source"], "recipe")
        saved_state = save_state.call_args.args[0]
        self.assertEqual(saved_state["last_generation_path"], "recipe")
        self.assertEqual(saved_state["last_generation_route"], "recipe_success")
        self.assertEqual(saved_state["last_implementation_id"], "tray_box_shell_v1")
        self.assertEqual(saved_state["last_execution_recipe"], "tray_box")

    def test_panel_plate_normalizer_supports_four_hole_pattern(self):
        request = "Make a panel plate 120 x 80 x 4 mm with four 5 mm mounting holes"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None
        self.assertEqual(plan.family, "panel_plate")
        self.assertEqual(plan.features["hole_pattern"], "corners")
        self.assertEqual(plan.features["hole_diameter_mm"], 5.0)

    def test_panel_plate_normalizer_infers_holes_from_count_only_prompt(self):
        request = "120 mm plate with 4 holes"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None
        self.assertEqual(plan.family, "panel_plate")
        self.assertEqual(plan.features["hole_count"], 4)
        self.assertEqual(plan.features["hole_diameter_mm"], 5.0)
        self.assertEqual(plan.features["hole_pattern"], "corners")

    def test_standoff_normalizer_supports_hex_profile(self):
        request = "Create a hex standoff 12 mm outer diameter 5 mm inner diameter 25 mm tall"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None
        self.assertEqual(plan.family, "spacer_standoff")
        self.assertEqual(plan.features["profile"], "hex")
        self.assertEqual(plan.dimensions["length_mm"], 25.0)

    def test_enclosure_geometry_supports_front_opening(self):
        plan = GenerationPlan(
            family="enclosure",
            family_label="enclosure",
            recipe="box_shell",
            request_text="enclosure",
            dimensions={"width_mm": 120.0, "depth_mm": 80.0, "height_mm": 50.0},
            features={
                "wall_thickness_mm": 3.0,
                "base_thickness_mm": 4.0,
                "open_top": False,
                "front_opening": True,
                "opening_width_mm": 60.0,
                "opening_height_mm": 25.0,
            },
        )
        script = build_script(plan)
        self.assertIn("InnerCavity", script)
        self.assertIn("FrontOpening", script)
        self.assertIn("ShellBevel", script)
        self.assertNotIn("open_top = False", script)

    def test_enclosure_geometry_handles_small_shells_without_collapsing(self):
        plan = GenerationPlan(
            family="enclosure",
            family_label="enclosure",
            recipe="box_shell",
            request_text="small enclosure",
            dimensions={"width_mm": 20.0, "depth_mm": 18.0, "height_mm": 14.0},
            features={
                "wall_thickness_mm": 8.0,
                "base_thickness_mm": 8.0,
                "open_top": False,
                "front_opening": False,
            },
        )
        script = build_script(plan)
        self.assertIn("ShellBevel", script)
        self.assertIn("inner_box", script)

    def test_pipeline_returns_preview_payload_for_target_family(self):
        with patch("app.backend.pipeline.save_generated_script") as save_script, patch(
            "app.backend.pipeline.export_preview_model",
            return_value=(True, "Preview exported successfully."),
        ), patch("app.backend.pipeline.load_state", return_value={}), patch("app.backend.pipeline.save_state") as save_state, patch(
            "app.backend.pipeline.add_saved_model_entry",
            return_value={"id": "saved-model-1"},
        ) as add_saved_model_entry:
            result = generate_model_request("Create a 120 x 80 x 50 mm enclosure with 3 mm walls", log=lambda _msg: None)

        save_script.assert_called_once()
        self.assertEqual(save_state.call_count, 2)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["family"], "enclosure")
        self.assertEqual(result["preview_export_status"], "ready")
        self.assertIn("validation", result)
        self.assertTrue(result["generation_id"].startswith("gen-"))
        self.assertEqual(result["preview_asset_version"], result["generation_id"])
        self.assertIn(result["generation_id"], result["preview_model_path"])
        self.assertEqual(result["final_model_path"], result["preview_model_path"])
        self.assertEqual(result["output_source"], "recipe")
        self.assertEqual(result["generation_path"], "recipe")
        self.assertEqual(result["generation_route"], "recipe_success")
        self.assertEqual(result["implementation_id"], "enclosure_open_top_shell_v1")
        self.assertEqual(result["execution_recipe"], "box_shell")
        self.assertTrue(result["preview_model_url"].startswith("file:///"))
        self.assertEqual(result["preview_model_url"], result["final_model_url"])
        saved_state = save_state.call_args.args[0]
        self.assertEqual(saved_state["last_generation_id"], result["generation_id"])
        self.assertEqual(saved_state["last_preview_asset_version"], result["generation_id"])
        self.assertEqual(saved_state["last_final_model_path"], result["preview_model_path"])
        self.assertEqual(saved_state["last_output_source"], "recipe")
        self.assertEqual(saved_state["last_generation_path"], "recipe")
        self.assertEqual(saved_state["last_generation_route"], "recipe_success")
        self.assertEqual(saved_state["last_implementation_id"], "enclosure_open_top_shell_v1")
        self.assertEqual(saved_state["last_execution_recipe"], "box_shell")
        self.assertEqual(add_saved_model_entry.call_args.kwargs["implementation_id"], "enclosure_open_top_shell_v1")
        self.assertEqual(add_saved_model_entry.call_args.kwargs["execution_recipe"], "box_shell")

    def test_generation_context_resets_between_requests(self):
        state: dict = {}

        def load_state() -> dict:
            return dict(state)

        def save_state(payload: dict) -> Path:
            state.clear()
            state.update(payload)
            return Path("ignored")

        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model",
            return_value=(True, "Preview exported successfully."),
        ), patch("app.backend.pipeline.load_state", side_effect=load_state), patch("app.backend.pipeline.save_state", side_effect=save_state), patch(
            "app.backend.pipeline.add_saved_model_entry",
            return_value={"id": "saved-model-reset"},
        ):
            first = generate_model_request("make me a phone stand", log=lambda _msg: None)
            second = generate_model_request("120 mm plate with 4 holes", log=lambda _msg: None)

        self.assertEqual(first["family"], "phone_stand")
        self.assertEqual(first["implementation_id"], "phone_stand_cradle_v1")
        self.assertEqual(second["family"], "panel_plate")
        self.assertEqual(state["last_generation_family"], "panel_plate")
        self.assertEqual(state["last_classification"]["family_key"], "panel_plate")
        self.assertEqual(state["last_plan"]["family"], "panel_plate")

    def test_classifier_prefers_cable_clip_for_wire_clip_language(self):
        result = classify_request("Create a wire clip for a 10 mm cable with a mounting base")
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.family_key, "cable_clip")
        self.assertGreater(result.confidence, 0.5)

    def test_bracket_normalizer_supports_four_holes_and_gusset(self):
        request = "Make a reinforced mounting bracket 120 x 30 x 80 mm with four 5 mm holes and 6 mm thickness"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None
        self.assertEqual(plan.family, "bracket")
        self.assertEqual(plan.features["hole_count"], 4)
        self.assertTrue(plan.features["gusset"])

    def test_small_bracket_geometry_remains_stable(self):
        plan = GenerationPlan(
            family="bracket",
            family_label="bracket",
            recipe="bracket",
            request_text="small bracket",
            dimensions={"base_length_mm": 22.0, "flange_width_mm": 12.0, "vertical_height_mm": 18.0, "thickness_mm": 8.0},
            features={"hole_diameter_mm": 4.0, "hole_count": 2, "gusset": False},
        )
        script = build_script(plan)
        self.assertIn("JoinBracket", script)
        self.assertIn("final_obj = base_leg", script)
        self.assertIn("BaseHole", script)
        self.assertNotIn("BracketBevel", script)

    def test_adapter_normalizer_supports_reducer_language(self):
        request = "Create an adapter reducer from 40 mm to 24 mm diameter, 50 mm long with 12 mm through hole"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None
        self.assertEqual(plan.family, "adapter")
        self.assertEqual(plan.dimensions["large_diameter_mm"], 40.0)
        self.assertEqual(plan.features["center_hole_mm"], 12.0)

    def test_cable_clip_normalizer_supports_mount_hole(self):
        request = "Create a cable clip for 10 mm cable with 30 mm width, 18 mm depth, 4 mm thickness, and 4 mm mount hole"
        classification = classify_request(request)
        status, _, plan = normalize_request(request, classification)
        self.assertEqual(status, "ready")
        assert plan is not None
        self.assertEqual(plan.family, "cable_clip")
        self.assertEqual(plan.features["mount_hole_mm"], 4.0)
        self.assertEqual(plan.features["cable_diameter_mm"], 10.0)

    def test_hook_mount_pipeline_returns_preview_payload(self):
        with patch("app.backend.pipeline.save_generated_script") as save_script, patch(
            "app.backend.pipeline.export_preview_model",
            return_value=(True, "Preview exported successfully."),
        ), patch("app.backend.pipeline.load_state", return_value={}), patch("app.backend.pipeline.save_state") as save_state, patch(
            "app.backend.pipeline.add_saved_model_entry",
            return_value={"id": "saved-model-hook"},
        ):
            result = generate_model_request("make a wall hook", log=lambda _msg: None)

        save_script.assert_called_once()
        self.assertEqual(save_state.call_count, 2)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["family"], "hook_mount")
        self.assertEqual(result["preview_export_status"], "ready")
        self.assertEqual(result["final_model_path"], result["preview_model_path"])
        self.assertEqual(result["output_source"], "recipe")
        self.assertEqual(result["generation_path"], "recipe")
        self.assertEqual(result["generation_route"], "recipe_success")
        self.assertEqual(result["implementation_id"], "hook_mount_wall_hook_v1")
        self.assertEqual(result["execution_recipe"], "hook_mount")
        self.assertTrue(result["preview_model_url"].startswith("file:///"))

    def test_pipeline_returns_preview_payload_for_bracket(self):
        with patch("app.backend.pipeline.save_generated_script") as save_script, patch(
            "app.backend.pipeline.export_preview_model",
            return_value=(True, "Preview exported successfully."),
        ), patch("app.backend.pipeline.load_state", return_value={}), patch("app.backend.pipeline.save_state") as save_state, patch(
            "app.backend.pipeline.add_saved_model_entry",
            return_value={"id": "saved-model-2"},
        ):
            result = generate_model_request("Make a bracket 120 x 30 x 80 mm with four 5 mm holes and 6 mm thickness", log=lambda _msg: None)

        save_script.assert_called_once()
        self.assertEqual(save_state.call_count, 2)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["family"], "bracket")
        self.assertEqual(result["preview_export_status"], "ready")
        self.assertEqual(result["final_model_path"], result["preview_model_path"])
        self.assertEqual(result["output_source"], "recipe")
        self.assertEqual(result["generation_path"], "recipe")
        self.assertEqual(result["generation_route"], "recipe_success")
        self.assertEqual(result["implementation_id"], "bracket_body_v1")
        self.assertEqual(result["execution_recipe"], "bracket")
        self.assertTrue(result["preview_model_url"].startswith("file:///"))

    def test_pipeline_returns_preview_payload_for_golden_bracket_prompt(self):
        with patch("app.backend.pipeline.save_generated_script") as save_script, patch(
            "app.backend.pipeline.export_preview_model",
            return_value=(True, "Preview exported successfully."),
        ), patch("app.backend.pipeline.load_state", return_value={}), patch("app.backend.pipeline.save_state") as save_state, patch(
            "app.backend.pipeline.add_saved_model_entry",
            return_value={"id": "saved-model-golden"},
        ):
            result = generate_model_request("make a bracket 120 x 40 x 90 mm", log=lambda _msg: None)

        save_script.assert_called_once()
        self.assertEqual(save_state.call_count, 2)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["family"], "bracket")
        self.assertEqual(result["preview_export_status"], "ready")
        self.assertEqual(result["output_source"], "recipe")
        self.assertEqual(result["generation_path"], "recipe")
        self.assertEqual(result["generation_route"], "recipe_success")
        self.assertEqual(result["implementation_id"], "bracket_body_v1")
        self.assertEqual(result["execution_recipe"], "bracket")
        self.assertTrue(result["preview_model_url"].startswith("file:///"))

    def test_pipeline_returns_generation_identity_for_nonready_result(self):
        with patch("app.backend.pipeline.load_state", return_value={}), patch("app.backend.pipeline.save_state") as save_state:
            result = generate_model_request("Make me a dragon sculpture", log=lambda _msg: None)

        self.assertEqual(result["status"], "unsupported")
        self.assertTrue(result["is_terminal"])
        self.assertTrue(result["generation_id"].startswith("gen-"))
        self.assertEqual(result["request_text"], "Make me a dragon sculpture")
        self.assertEqual(result["final_model_path"], "")
        self.assertEqual(result["output_source"], "")
        saved_state = save_state.call_args.args[0]
        self.assertEqual(saved_state["last_generation_id"], result["generation_id"])
        self.assertEqual(saved_state["last_preview_asset_version"], "")

    def test_pipeline_returns_ready_when_preview_export_fails(self):
        with patch("app.backend.pipeline.save_generated_script"), patch(
            "app.backend.pipeline.export_preview_model",
            return_value=(False, "Preview export failed."),
        ), patch("app.backend.pipeline.load_state", return_value={}), patch("app.backend.pipeline.save_state") as save_state, patch(
            "app.backend.pipeline.add_saved_model_entry",
            return_value={"id": "saved-model-3"},
        ) as add_saved_model_entry:
            result = generate_model_request("Create a 120 x 80 x 50 mm enclosure with 3 mm walls", log=lambda _msg: None)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["preview_export_status"], "error")
        self.assertEqual(result["preview_model_path"], "")
        self.assertEqual(result["preview_export_message"], "Preview export failed.")
        self.assertEqual(result["generation_path"], "recipe")
        self.assertEqual(result["generation_route"], "recipe_success")
        self.assertEqual(result["implementation_id"], "enclosure_open_top_shell_v1")
        self.assertEqual(result["execution_recipe"], "box_shell")
        saved_state_payload = save_state.call_args.args[0]
        self.assertEqual(saved_state_payload["last_generation_status"], "ready")
        self.assertEqual(saved_state_payload["last_preview_export_status"], "error")
        self.assertEqual(saved_state_payload["last_implementation_id"], "enclosure_open_top_shell_v1")
        self.assertEqual(add_saved_model_entry.call_args.kwargs["implementation_id"], "enclosure_open_top_shell_v1")
        self.assertEqual(add_saved_model_entry.call_args.kwargs["execution_recipe"], "box_shell")

    def test_pipeline_returns_error_when_generation_raises(self):
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
            side_effect=RuntimeError("script build exploded"),
        ), patch(
            "app.backend.pipeline.load_state",
            return_value={},
        ), patch("app.backend.pipeline.save_state") as save_state:
            result = generate_model_request("Create a 120 x 80 x 50 mm enclosure with 3 mm walls", log=lambda _msg: None)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["raw_status"], "error")
        self.assertTrue(result["is_terminal"])
        self.assertEqual(result["preview_export_status"], "not_requested")
        self.assertEqual(result["generation_path"], "")
        self.assertEqual(result["generation_route"], "")
        saved_state_payload = save_state.call_args.args[0]
        self.assertEqual(saved_state_payload["last_generation_status"], "error")
        self.assertEqual(saved_state_payload["last_generation_raw_status"], "error")

    def test_backend_controller_surfaces_terminal_status_fields(self):
        controller = BackendController()
        mocked_state = {
            "last_generation_id": "gen-test-1",
            "last_generated_script_path": "blender/generated_model.py",
            "last_preview_model_path": "",
            "last_preview_asset_version": "",
            "last_preview_export_status": "error",
            "last_preview_export_message": "Preview export failed.",
            "last_user_request": "make something unsupported",
            "last_generation_family": "",
            "last_generation_status": "unsupported",
            "last_generation_raw_status": "unsupported",
            "last_generation_message": "Unsupported request.",
            "last_generation_timestamp": "2026-04-07T12:00:00",
            "last_validation_summary": "Unsupported request.",
            "last_plan": {},
            "last_validation": {},
            "last_classification": {},
            "last_saved_model_entry": {},
            "last_run_status": "unsupported",
            "last_generation_path": "recipe",
            "last_generation_route": "recipe_success",
            "last_generation_fallback_reason": "",
            "last_implementation_id": "panel_plate_v1",
            "last_execution_recipe": "panel_plate",
        }
        with patch("desktop.backend_controller.load_state", return_value=mocked_state), patch(
            "desktop.backend_controller.get_library_summary",
            return_value={"saved_model_count": 0, "recent_saved_models": [], "project_count": 0, "template_count": 0, "templates": []},
        ), patch.object(controller, "refresh_runtime_health", return_value={"runtime_health_status": "setup_required"}):
            status = controller.get_status()

        self.assertEqual(status.generation_id, "gen-test-1")
        self.assertEqual(status.last_generation_status, "unsupported")
        self.assertEqual(status.last_generation_raw_status, "unsupported")
        self.assertEqual(status.last_generation_path, "recipe")
        self.assertEqual(status.last_generation_route, "recipe_success")
        self.assertEqual(status.last_implementation_id, "panel_plate_v1")
        self.assertEqual(status.last_execution_recipe, "panel_plate")
        self.assertEqual(status.preview_export_status, "error")

    def test_state_defaults_include_runtime_setup_fields(self):
        required_keys = {
            "setup_completed",
            "first_run_completed",
            "ollama_installed",
            "ollama_running",
            "ollama_version",
            "ollama_model_name",
            "ollama_model_ready",
            "blender_detected",
            "blender_path",
            "runtime_health_status",
            "runtime_health_message",
            "last_final_model_path",
            "last_output_source",
        }
        self.assertTrue(required_keys.issubset(DEFAULT_STATE))

    def test_windows_path_normalizes_to_file_url(self):
        raw_path = r"C:\Users\Studl\geomancer\geomancer\data\previews\generated_preview_xxx.glb"
        self.assertEqual(
            to_file_url(raw_path),
            "file:///C:/Users/Studl/geomancer/geomancer/data/previews/generated_preview_xxx.glb",
        )

    def test_saved_model_open_uses_persisted_final_artifact(self):
        controller = BackendController()
        saved_models = [
            {
                "id": "saved-model-1",
                "preview_model_path": "C:/models/generated_preview.glb",
                "final_model_path": "C:/models/generated_preview.glb",
                "script_path": "C:/models/generated_model.py",
            }
        ]
        with patch("desktop.backend_controller.list_saved_models", return_value=saved_models), patch(
            "desktop.backend_controller.open_generated_model_file",
            return_value=(True, "Opened artifact."),
        ) as open_artifact, patch(
            "desktop.backend_controller.run_generated_script",
            return_value=(True, "Opened script."),
        ) as run_script, patch.object(
            controller,
            "get_runtime_health",
            return_value={"blender_detected": True, "runtime_health_message": "ready"},
        ):
            result = controller.open_saved_model_in_blender("saved-model-1")

        self.assertTrue(result["success"])
        open_artifact.assert_called_once()
        run_script.assert_not_called()

    def test_open_generated_model_file_imports_glb_via_temporary_script(self):
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as handle:
            model_path = Path(handle.name)

        try:
            with patch("app.blender_runner.get_blender_path", return_value=Path(__file__)), patch(
                "app.blender_runner.subprocess.run"
            ) as run_mock:
                run_mock.return_value = type("Result", (), {"returncode": 0, "stderr": "", "stdout": ""})()

                success, message = open_generated_model_file(model_path, interactive=False)

            self.assertTrue(success)
            self.assertIn("Blender completed successfully", message)
            run_mock.assert_called_once()
            command = run_mock.call_args.args[0]
            self.assertIn("--python", command)
            self.assertFalse(any(str(model_path) == arg for arg in command))
            self.assertTrue(any(str(arg).endswith("_geomancer_model_open.py") for arg in command))
        finally:
            model_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
