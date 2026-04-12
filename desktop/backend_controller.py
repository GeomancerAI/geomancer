"""Desktop-facing controller that wraps the existing Geomancer backend."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable
from uuid import uuid4

from app.blender_runner import run_generated_script
from app.backend.pipeline import generate_model_request
from app.backend.runtime import GENERATED_SCRIPT_PATH
from app.backend.versioning import load_version
from app.model_library import delete_saved_model_entry, get_library_summary, list_saved_models
from app.runtime.health import collect_runtime_health, sync_runtime_health
from app.runtime.models import RECOMMENDED_OLLAMA_MODEL
from app.runtime.ollama import pull_model, run_smoke_test as run_ollama_smoke_test
from app.runtime.setup import build_setup_flow, persist_setup_completion
from app.state import load_state, save_state
from app.runtime.blender import verify_blender_callable


LogCallback = Callable[[str], None]


@dataclass
class DesktopStatus:
    """Simple status snapshot for the desktop shell."""

    version: str
    generation_id: str
    generated_script_path: str
    preview_model_path: str
    preview_asset_version: str
    preview_export_status: str
    preview_export_message: str
    last_user_request: str
    last_generation_family: str
    last_generation_status: str
    last_generation_raw_status: str
    last_generation_message: str
    last_generation_timestamp: str
    last_validation_summary: str
    last_plan: dict
    last_validation: dict
    last_classification: dict
    last_saved_model_entry: dict
    library_summary: dict
    saved_models: list[dict]
    last_run_status: str
    setup_completed: bool
    first_run_completed: bool
    ollama_installed: bool
    ollama_running: bool
    ollama_version: str
    ollama_model_name: str
    ollama_model_ready: bool
    blender_detected: bool
    blender_path: str
    runtime_health_status: str
    runtime_health_message: str
    runtime_health: dict
    setup_flow: list[dict]


class BackendController:
    """Thin adapter over the current Python generation pipeline.

    The goal is to keep the existing backend behavior intact while exposing
    operations that a desktop UI can call via a bridge layer.
    """

    def get_status(self) -> DesktopStatus:
        """Return current persisted backend state for the desktop shell."""
        runtime_health = self.refresh_runtime_health()
        state = load_state()
        return DesktopStatus(
            version=load_version(),
            generation_id=state.get("last_generation_id") or "",
            generated_script_path=state.get("last_generated_script_path") or str(GENERATED_SCRIPT_PATH),
            preview_model_path=state.get("last_preview_model_path") or "",
            preview_asset_version=state.get("last_preview_asset_version") or "",
            preview_export_status=state.get("last_preview_export_status") or "",
            preview_export_message=state.get("last_preview_export_message") or "",
            last_user_request=state.get("last_user_request") or "",
            last_generation_family=state.get("last_generation_family") or "",
            last_generation_status=state.get("last_generation_status") or "",
            last_generation_raw_status=state.get("last_generation_raw_status") or "",
            last_generation_message=state.get("last_generation_message") or "",
            last_generation_timestamp=state.get("last_generation_timestamp") or "",
            last_validation_summary=state.get("last_validation_summary") or "",
            last_plan=state.get("last_plan") or {},
            last_validation=state.get("last_validation") or {},
            last_classification=state.get("last_classification") or {},
            last_saved_model_entry=state.get("last_saved_model_entry") or {},
            library_summary=get_library_summary(),
            saved_models=list_saved_models(),
            last_run_status=state.get("last_run_status") or "idle",
            setup_completed=bool(state.get("setup_completed")),
            first_run_completed=bool(state.get("first_run_completed")),
            ollama_installed=bool(state.get("ollama_installed")),
            ollama_running=bool(state.get("ollama_running")),
            ollama_version=state.get("ollama_version") or "",
            ollama_model_name=state.get("ollama_model_name") or RECOMMENDED_OLLAMA_MODEL.name,
            ollama_model_ready=bool(state.get("ollama_model_ready")),
            blender_detected=bool(state.get("blender_detected")),
            blender_path=state.get("blender_path") or "",
            runtime_health_status=state.get("runtime_health_status") or "unknown",
            runtime_health_message=state.get("runtime_health_message") or "",
            runtime_health=runtime_health,
            setup_flow=build_setup_flow(collect_runtime_health(state)),
        )

    def get_status_payload(self) -> dict:
        """Return a JSON-safe status payload for bridge serialization."""
        return self.make_json_safe(self.get_status())

    def generate_model(self, prompt_text: str, log: LogCallback | None = None) -> dict:
        """Run the existing generation flow and return the structured result."""
        logger = log or (lambda _message: None)
        runtime_health = self.get_runtime_health(refresh=True)
        if runtime_health.get("runtime_health_status") != "ready":
            message = runtime_health.get("runtime_health_message") or "Runtime setup is incomplete."
            logger(f"[CONTROLLER] generation blocked: {message}")
            payload = self.record_terminal_failure(
                prompt_text=prompt_text,
                message=message,
                status="error",
                raw_status="runtime_unhealthy",
                runtime_health=runtime_health,
            )
            payload["setup_required"] = True
            return payload
        logger(f"[CONTROLLER] generate_model start: request_text={prompt_text!r}")
        result = self.make_json_safe(generate_model_request(prompt_text, log=logger, show_spinner=False))
        result["runtime_health"] = runtime_health
        logger(
            "[CONTROLLER] generate_model returned: "
            f"status={result.get('status', '')!r}, "
            f"generation_id={result.get('generation_id', '')!r}, "
            f"request_text={result.get('request_text', '')!r}, "
            f"preview_path={result.get('preview_model_path', '')!r}"
        )
        return result

    def record_terminal_failure(
        self,
        *,
        prompt_text: str,
        message: str,
        status: str = "error",
        raw_status: str = "controller_failure",
        runtime_health: dict | None = None,
    ) -> dict:
        """Persist and return a controller-owned terminal failure payload."""
        generation_id = self._build_controller_generation_id()
        state = load_state()
        state["last_user_request"] = prompt_text
        state["last_generation_id"] = generation_id
        state["last_generated_script_path"] = str(GENERATED_SCRIPT_PATH)
        state["last_preview_model_path"] = ""
        state["last_preview_asset_version"] = ""
        state["last_preview_export_status"] = "error"
        state["last_preview_export_message"] = message
        state["last_generation_timestamp"] = datetime.now().isoformat(timespec="seconds")
        state["last_generation_family"] = ""
        state["last_generation_status"] = status
        state["last_generation_raw_status"] = raw_status
        state["last_generation_message"] = message
        state["last_validation_summary"] = message
        state["last_plan"] = {}
        state["last_validation"] = {}
        state["last_classification"] = {}
        state["last_saved_model_entry"] = {}
        state["last_run_status"] = status
        save_state(state)
        return {
            "generation_id": generation_id,
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
            "runtime_health": runtime_health or self.get_runtime_health(refresh=False),
        }

    def open_in_blender(self, script_path: str | None = None, interactive: bool = True) -> tuple[bool, str]:
        """Launch Blender for the current generated script."""
        health = self.get_runtime_health(refresh=True)
        if not health.get("blender_detected"):
            return False, health.get("runtime_health_message", "Blender is not configured.")
        target_path = Path(script_path) if script_path else GENERATED_SCRIPT_PATH
        return run_generated_script(target_path, interactive=interactive)

    def open_saved_model_in_blender(self, model_id: str) -> dict:
        """Launch Blender for a saved model entry's script path."""
        entry = next((item for item in list_saved_models() if item.get("id") == model_id), None)
        if not entry:
            return {"success": False, "message": "Saved model not found.", "model_id": model_id}
        success, message = self.open_in_blender(script_path=entry.get("script_path") or None, interactive=True)
        return {
            "success": success,
            "message": message,
            "model_id": model_id,
        }

    def delete_saved_model(self, model_id: str) -> dict:
        """Delete one saved model entry from the local library."""
        removed = delete_saved_model_entry(model_id)
        state = load_state()
        last_saved = state.get("last_saved_model_entry") or {}
        if removed and last_saved.get("id") == model_id:
            state["last_saved_model_entry"] = {}
            save_state(state)
        return {
            "success": removed,
            "message": "Saved model deleted." if removed else "Saved model not found.",
            "model_id": model_id,
            "library_summary": get_library_summary(),
            "saved_models": list_saved_models(),
        }

    def get_runtime_health(self, refresh: bool = False) -> dict:
        """Return the structured runtime health payload for desktop use."""
        if refresh:
            return self.refresh_runtime_health()
        return self.make_json_safe(collect_runtime_health(load_state()).to_dict())

    def refresh_runtime_health(self) -> dict:
        """Probe and persist the local runtime health."""
        state = load_state()
        health = collect_runtime_health(state)
        updated_state = sync_runtime_health(health, state=state)
        return self.make_json_safe(collect_runtime_health(updated_state).to_dict())

    def run_setup_smoke_test(self) -> dict:
        """Run a small runtime smoke test and persist successful completion."""
        health = self.get_runtime_health(refresh=True)
        model_name = health.get("ollama_model_name") or RECOMMENDED_OLLAMA_MODEL.name
        blender_ok, blender_message = verify_blender_callable(health.get("blender_path") or None)
        ollama_result = run_ollama_smoke_test(model_name)
        smoke_ok = blender_ok and bool(ollama_result.get("ok"))
        message = "Setup smoke test passed." if smoke_ok else "Setup smoke test failed."
        details = {
            "ok": smoke_ok,
            "message": message,
            "ollama": ollama_result,
            "blender": {"ok": blender_ok, "message": blender_message},
        }
        if smoke_ok:
            refreshed = collect_runtime_health(load_state())
            persist_setup_completion(refreshed, completed=True)
            details["runtime_health"] = self.refresh_runtime_health()
        else:
            details["runtime_health"] = health
        return self.make_json_safe(details)

    def start_model_pull(self, model_name: str, progress_callback: LogCallback | None = None) -> dict:
        """Pull the configured Ollama model and refresh runtime state."""
        callback = progress_callback or (lambda _message: None)

        def relay_progress(event: dict) -> None:
            callback(self.make_json_safe(event))

        result = pull_model(model_name or RECOMMENDED_OLLAMA_MODEL.name, progress_callback=relay_progress)
        runtime_health = self.refresh_runtime_health()
        return self.make_json_safe({"pull_result": result, "runtime_health": runtime_health})

    def maybe_detect_or_repair_environment(self) -> dict:
        """Refresh health and seed missing state defaults for first-run setup."""
        state = load_state()
        if not state.get("ollama_model_name"):
            state["ollama_model_name"] = RECOMMENDED_OLLAMA_MODEL.name
        save_state(state)
        return self.refresh_runtime_health()

    def _build_controller_generation_id(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"ctrl-{timestamp}-{uuid4().hex[:8]}"

    @classmethod
    def make_json_safe(cls, value):
        """Convert nested values into JSON-safe Python primitives."""
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, BaseException):
            return str(value)
        if is_dataclass(value):
            return cls.make_json_safe(asdict(value))
        if isinstance(value, dict):
            return {str(key): cls.make_json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [cls.make_json_safe(item) for item in value]
        if hasattr(value, "to_dict") and callable(value.to_dict):
            return cls.make_json_safe(value.to_dict())
        if hasattr(value, "__dict__"):
            return cls.make_json_safe(vars(value))
        return str(value)
