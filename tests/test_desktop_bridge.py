import json
import unittest
from concurrent.futures import Future
from datetime import datetime
from pathlib import Path
import tempfile
from unittest.mock import patch

from desktop.backend_controller import BackendController
from desktop.bridge import GeomancerBridge, run_generation_job


class FakeController:
    def __init__(self):
        self.failure_payloads = []
        self.status_payload = {
            "version": "0.6.2-alpha",
            "generation_id": "gen-status-1",
            "generated_script_path": Path("blender/generated_model.py"),
            "preview_model_path": Path("data/previews/generated_preview.glb"),
            "preview_asset_version": ("asset", "1"),
            "preview_export_status": "ready",
            "preview_export_message": RuntimeError("preview ok"),
            "last_user_request": "status request",
            "last_generation_family": "panel_plate",
            "last_generation_status": "ready",
            "last_generation_raw_status": "ready",
            "last_generation_message": "",
            "last_generation_timestamp": datetime(2026, 4, 7, 12, 0, 0),
            "last_validation_summary": "ok",
            "last_plan": {"dims": {1, 2}},
            "last_validation": {"items": ("a", "b")},
            "last_classification": {"exc": ValueError("bad")},
            "last_saved_model_entry": {"path": Path("data/example.glb")},
            "last_generation_path": "recipe",
            "last_generation_route": "recipe_success",
            "last_generation_fallback_reason": "",
            "last_implementation_id": "panel_plate_v1",
            "last_execution_recipe": "panel_plate",
            "library_summary": {"templates": {"a", "b"}, "recent_saved_models": ()},
            "last_run_status": "ready",
            "setup_completed": False,
            "first_run_completed": False,
            "ollama_installed": True,
            "ollama_running": True,
            "ollama_version": "0.5.0",
            "ollama_model_name": "qwen2.5:7b",
            "ollama_model_ready": True,
            "blender_detected": True,
            "blender_path": Path("C:/Program Files/Blender Foundation/Blender 5.0/blender.exe"),
            "runtime_health_status": "ready",
            "runtime_health_message": "Runtime is healthy.",
            "runtime_health": {"runtime_health_status": "ready"},
            "setup_flow": [{"id": "welcome", "label": "Welcome", "status": "complete"}],
        }

    def get_status_payload(self):
        return self.status_payload

    def get_runtime_health(self, refresh: bool = False):
        del refresh
        return {"runtime_health_status": "ready", "runtime_health_message": "Runtime is healthy."}

    def refresh_runtime_health(self):
        return {"runtime_health_status": "ready", "runtime_health_message": "Runtime is healthy."}

    def maybe_detect_or_repair_environment(self):
        return self.refresh_runtime_health()

    def run_setup_smoke_test(self):
        return {"ok": True, "message": "Smoke test passed.", "runtime_health": self.refresh_runtime_health()}

    def start_model_pull(self, model_name, progress_callback=None):
        if progress_callback is not None:
            progress_callback({"status": "success", "model": model_name, "done": True})
        return {"pull_result": {"model_name": model_name, "done": True}, "runtime_health": self.refresh_runtime_health()}

    def clean_dev_reload(self, log=None):
        if log is not None:
            log("Cleared preview artifact: fake.glb")
            log("Cleared Python cache directory: fake/__pycache__")
            log("UI reload triggered.")
        return {
            "success": True,
            "preview_directory": "data/previews",
            "preview_artifacts_cleared": 1,
            "preview_artifacts_failed": 0,
            "pycache_directories_cleared": 1,
            "pycache_directories_failed": 0,
            "messages": ["Cleared preview artifact: fake.glb", "Cleared Python cache directory: fake/__pycache__", "UI reload triggered."],
        }

    def generate_model(self, prompt_text, log=None):
        if log is not None:
            log(f"[CONTROLLER] fake generate_model called: request_text={prompt_text!r}")
        return {
            "generation_id": "gen-fake-1",
            "request_text": prompt_text,
            "status": "ready",
            "raw_status": "ready",
            "is_terminal": True,
            "message": "",
            "preview_model_path": "",
            "preview_asset_version": "",
            "preview_export_status": "ready",
        }

    def record_terminal_failure(self, *, prompt_text: str, message: str, status: str = "error", raw_status: str = "controller_failure", runtime_health=None):
        del runtime_health
        payload = {
            "generation_id": "ctrl-failure-1",
            "request_text": prompt_text,
            "status": status,
            "raw_status": raw_status,
            "is_terminal": True,
            "message": message,
            "classification": {},
            "plan": {},
            "validation": {},
            "preview_model_path": "",
            "preview_asset_version": "",
            "preview_export_status": "error",
            "preview_export_message": message,
            "supported_families": [],
        }
        self.failure_payloads.append(payload)
        return payload

    @staticmethod
    def make_json_safe(value):
        return BackendController.make_json_safe(value)


class DesktopBridgeTests(unittest.TestCase):
    def test_get_initial_state_json_safe_conversion(self):
        bridge = GeomancerBridge(controller=FakeController())

        payload = json.loads(bridge.getInitialState())

        self.assertEqual(payload["generatedScriptPath"], str(Path("blender/generated_model.py")))
        self.assertEqual(payload["previewModelPath"], str(Path("data/previews/generated_preview.glb")))
        self.assertEqual(payload["previewAssetVersion"], ["asset", "1"])
        self.assertEqual(payload["previewExportMessage"], "preview ok")
        self.assertEqual(payload["lastGenerationTimestamp"], "2026-04-07T12:00:00")
        self.assertEqual(payload["lastPlan"], {"dims": [1, 2]})
        self.assertEqual(payload["lastValidation"], {"items": ["a", "b"]})
        self.assertEqual(payload["lastSavedModelEntry"], {"path": str(Path("data/example.glb"))})
        self.assertEqual(payload["lastGenerationPath"], "recipe")
        self.assertEqual(payload["lastGenerationRoute"], "recipe_success")
        self.assertEqual(payload["lastGenerationFallbackReason"], "")
        self.assertEqual(payload["lastImplementationId"], "panel_plate_v1")
        self.assertEqual(payload["lastExecutionRecipe"], "panel_plate")
        self.assertEqual(payload["runtimeHealthStatus"], "ready")
        self.assertEqual(payload["runtimeHealth"]["runtime_health_status"], "ready")

    def test_run_generation_job_returns_success_payload_and_logs(self):
        controller = FakeController()

        result = run_generation_job(controller, "make a plate")

        self.assertFalse(result["failed"])
        self.assertEqual(result["payload"]["status"], "ready")
        self.assertEqual(result["payload"]["request_text"], "make a plate")
        self.assertTrue(any("python generation job start" in entry for entry in result["logs"]))
        self.assertTrue(any("backend generation returned" in entry for entry in result["logs"]))

    def test_terminal_payload_preserves_generation_provenance_fields(self):
        controller = FakeController()
        bridge = GeomancerBridge(controller=controller)

        payload = bridge._normalize_terminal_payload(
            {
                "generation_id": "gen-phone-1",
                "request_text": "make a phone stand",
                "status": "ready",
                "raw_status": "ready",
                "is_terminal": True,
                "message": "",
                "generation_path": "recipe",
                "generation_route": "recipe_success",
                "generation_fallback_reason": "",
                "execution_recipe": "phone_stand",
                "implementation_id": "phone_stand_cradle_v1",
                "output_source": "recipe",
                "preview_export_status": "ready",
                "preview_model_path": "data/previews/generated_preview.glb",
            }
        )

        self.assertEqual(payload["generation_path"], "recipe")
        self.assertEqual(payload["generation_route"], "recipe_success")
        self.assertEqual(payload["generation_fallback_reason"], "")
        self.assertEqual(payload["execution_recipe"], "phone_stand")
        self.assertEqual(payload["implementation_id"], "phone_stand_cradle_v1")
        self.assertEqual(payload["output_source"], "recipe")

    def test_clean_dev_reload_payload_is_preserved_by_bridge(self):
        controller = FakeController()
        bridge = GeomancerBridge(controller=controller)
        logs = []
        bridge.logMessage.connect(logs.append)

        payload = json.loads(bridge.cleanDevReload())

        self.assertTrue(payload["success"])
        self.assertEqual(payload["preview_artifacts_cleared"], 1)
        self.assertEqual(payload["pycache_directories_cleared"], 1)
        self.assertTrue(any("Cleared preview artifact" in entry for entry in logs))
        self.assertTrue(any("UI reload triggered." in entry for entry in logs))

    def test_run_generation_job_returns_failure_payload_and_logs(self):
        controller = FakeController()

        with patch.object(controller, "generate_model", side_effect=RuntimeError("boom")):
            result = run_generation_job(controller, "make a plate")

        self.assertTrue(result["failed"])
        self.assertEqual(result["payload"]["status"], "error")
        self.assertEqual(result["payload"]["raw_status"], "thread_exception")
        self.assertTrue(any("run exception: boom" in entry for entry in result["logs"]))

    def test_generate_model_submits_executor_job(self):
        controller = FakeController()
        bridge = GeomancerBridge(controller=controller)
        logs = []
        bridge.logMessage.connect(logs.append)
        submitted_future = Future()

        with patch.object(bridge._generation_executor, "submit", return_value=submitted_future) as submit_mock:
            bridge.generateModel("make a plate")

        self.assertIs(bridge._active_generation_future, submitted_future)
        self.assertEqual(bridge._active_request_text, "make a plate")
        submit_mock.assert_called_once()
        self.assertTrue(any("submitting generation job" in entry for entry in logs))

    def test_generate_model_rejects_when_job_is_active(self):
        controller = FakeController()
        bridge = GeomancerBridge(controller=controller)
        completions = []
        failures = []
        pending_future = Future()
        bridge._active_generation_future = pending_future
        bridge.generationCompleted.connect(lambda payload: completions.append(json.loads(payload)))
        bridge.generationFailed.connect(lambda message: failures.append(message))

        bridge.generateModel("make a plate")

        self.assertEqual(len(completions), 1)
        self.assertEqual(completions[0]["status"], "error")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0], "Generation is already running.")

    def test_backend_controller_clean_dev_reload_clears_only_safe_artifacts(self):
        controller = BackendController()
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            preview_dir = root / "data" / "previews"
            preview_dir.mkdir(parents=True)
            preview_file = preview_dir / "generated_preview_test.glb"
            preview_file.write_text("preview", encoding="utf-8")
            nested_preview_dir = preview_dir / "nested"
            nested_preview_dir.mkdir()
            (nested_preview_dir / "stale.txt").write_text("stale", encoding="utf-8")
            cache_dir = root / "app" / "__pycache__"
            cache_dir.mkdir(parents=True)
            (cache_dir / "stale.pyc").write_text("cache", encoding="utf-8")
            preserved_file = root / "keep.txt"
            preserved_file.write_text("keep", encoding="utf-8")

            with patch("desktop.backend_controller.PROJECT_ROOT", root), patch("desktop.backend_controller.PREVIEWS_DIR", preview_dir):
                logs = []
                result = controller.clean_dev_reload(log=logs.append)

            self.assertTrue(result["success"])
            self.assertEqual(result["preview_artifacts_cleared"], 2)
            self.assertEqual(result["pycache_directories_cleared"], 1)
            self.assertFalse(preview_file.exists())
            self.assertFalse(nested_preview_dir.exists())
            self.assertFalse(cache_dir.exists())
            self.assertTrue(preserved_file.exists())
            self.assertTrue(any("Cleared preview artifact" in entry for entry in logs))
            self.assertTrue(any("Cleared Python cache directory" in entry for entry in logs))
            self.assertTrue(any("UI reload triggered." in entry for entry in logs))

    def test_handle_generation_job_resolved_success_emits_completion(self):
        controller = FakeController()
        bridge = GeomancerBridge(controller=controller)
        completions = []
        logs = []
        bridge.generationCompleted.connect(lambda payload: completions.append(json.loads(payload)))
        bridge.logMessage.connect(logs.append)

        bridge._handle_generation_job_resolved({
            "failed": False,
            "payload": {
                "generation_id": "gen-1",
                "request_text": "plate",
                "status": "ready",
                "raw_status": "ready",
                "is_terminal": True,
                "message": "",
                "preview_model_path": "",
                "preview_export_status": "ready",
            },
            "logs": ["[WORKER] python generation job start", "[WORKER] backend generation returned"],
        })

        self.assertEqual(len(completions), 1)
        self.assertEqual(completions[0]["generation_id"], "gen-1")
        self.assertTrue(any("future completed successfully" in entry for entry in logs))
        self.assertTrue(any("emitting generationCompleted" in entry for entry in logs))

    def test_handle_generation_job_resolved_failure_emits_failure_signal(self):
        controller = FakeController()
        bridge = GeomancerBridge(controller=controller)
        completions = []
        failures = []
        logs = []
        bridge.generationCompleted.connect(lambda payload: completions.append(json.loads(payload)))
        bridge.generationFailed.connect(lambda message: failures.append(message))
        bridge.logMessage.connect(logs.append)

        bridge._handle_generation_job_resolved({
            "failed": True,
            "payload": {
                "generation_id": "gen-1",
                "request_text": "plate",
                "status": "error",
                "raw_status": "thread_exception",
                "is_terminal": True,
                "message": "boom",
                "preview_model_path": "",
                "preview_export_status": "error",
            },
            "logs": ["[WORKER] python generation job start", "[WORKER] run exception: boom"],
        })

        self.assertEqual(len(completions), 1)
        self.assertEqual(completions[0]["status"], "error")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0], "boom")
        self.assertTrue(any("emitting generationFailed" in entry for entry in logs))

    def test_handle_generation_job_crashed_emits_terminal_failure(self):
        controller = FakeController()
        bridge = GeomancerBridge(controller=controller)
        completions = []
        failures = []
        logs = []
        bridge._active_request_text = "make a plate"
        bridge.generationCompleted.connect(lambda payload: completions.append(json.loads(payload)))
        bridge.generationFailed.connect(lambda message: failures.append(message))
        bridge.logMessage.connect(logs.append)

        bridge._handle_generation_job_crashed("executor exploded")

        self.assertEqual(len(completions), 1)
        self.assertEqual(completions[0]["status"], "error")
        self.assertIn("Generation future crashed", completions[0]["message"])
        self.assertEqual(len(failures), 1)
        self.assertIn("Generation future crashed", failures[0])
        self.assertTrue(any("future completed with exception" in entry for entry in logs))

    def test_handle_worker_finished_with_malformed_payload_emits_fallback(self):
        controller = FakeController()
        bridge = GeomancerBridge(controller=controller)
        completions = []
        failures = []
        bridge.generationCompleted.connect(lambda payload: completions.append(json.loads(payload)))
        bridge.generationFailed.connect(lambda message: failures.append(message))

        bridge._handle_worker_finished("not-json")

        self.assertEqual(len(completions), 1)
        self.assertEqual(completions[0]["status"], "error")
        self.assertEqual(completions[0]["raw_status"], "controller_failure")
        self.assertEqual(len(failures), 1)
        self.assertIn("Bridge completion handling failed", failures[0])

    def test_handle_worker_finished_refresh_failure_keeps_completion_result(self):
        controller = FakeController()
        bridge = GeomancerBridge(controller=controller)
        completions = []
        logs = []
        bridge.generationCompleted.connect(lambda payload: completions.append(json.loads(payload)))
        bridge.logMessage.connect(logs.append)
        bridge.refreshState = lambda: (_ for _ in ()).throw(RuntimeError("refresh exploded"))

        bridge._handle_worker_finished(json.dumps({
            "generation_id": "gen-1",
            "request_text": "plate",
            "status": "ready",
            "raw_status": "ready",
            "is_terminal": True,
            "message": "",
            "preview_model_path": "",
            "preview_export_status": "ready",
        }))

        self.assertEqual(len(completions), 1)
        self.assertEqual(completions[0]["generation_id"], "gen-1")
        self.assertTrue(any("refreshState failed after completion emit" in entry for entry in logs))

    def test_generate_model_setup_exception_emits_terminal_failure(self):
        controller = FakeController()
        bridge = GeomancerBridge(controller=controller)
        completions = []
        failures = []
        logs = []
        bridge.generationCompleted.connect(lambda payload: completions.append(json.loads(payload)))
        bridge.generationFailed.connect(lambda message: failures.append(message))
        bridge.logMessage.connect(logs.append)

        with patch.object(bridge._generation_executor, "submit", side_effect=RuntimeError("submit failed")):
            bridge.generateModel("make a plate")

        self.assertEqual(len(completions), 1)
        self.assertEqual(completions[0]["status"], "error")
        self.assertIn("Bridge generateModel failed", completions[0]["message"])
        self.assertEqual(len(failures), 1)
        self.assertIn("Bridge generateModel failed", failures[0])
        self.assertTrue(any("generateModel slot exception" in entry for entry in logs))


if __name__ == "__main__":
    unittest.main()
