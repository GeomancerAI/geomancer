"""Desktop-facing controller that wraps the existing Geomancer backend."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
import shutil
from pathlib import Path
from typing import Callable
from uuid import uuid4

from app.blender_runner import export_model_to_stl, open_generated_model_file, run_generated_script
from app.backend.pipeline import collect_editable_params_for_plan, generate_model_from_plan, generate_model_request
from app.backend.runtime import EXPORTS_DIR, GENERATED_SCRIPT_PATH, PREVIEWS_DIR
from app.backend.versioning import load_version
from app.model_library import delete_saved_model_entry, get_library_summary, list_saved_models, update_saved_model_entry
from app.path_utils import to_file_url
from app.runtime.health import collect_runtime_health, sync_runtime_health
from app.runtime.models import RECOMMENDED_OLLAMA_MODEL
from app.runtime.ollama import pull_model, run_smoke_test as run_ollama_smoke_test
from app.runtime.setup import build_setup_flow, persist_setup_completion
from app.state import load_state, save_state
from app.runtime.blender import verify_blender_callable


LogCallback = Callable[[str], None]
PROJECT_ROOT = Path(__file__).resolve().parent.parent


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
    last_interpretation_summary: str
    last_decision_summary: str
    last_style_summary: str
    current_saved_model_id: str
    current_saved_model_editable: bool
    last_opened_model_id: str
    reopen_source: str
    reopened_plan_summary: str
    current_editable_params: list
    last_editable_params: list
    last_regeneration_source: str
    edited_plan_summary: str
    last_missing_info: list
    last_assumptions: list
    last_warnings: list
    last_validation_summary: str
    last_plan: dict
    last_validation: dict
    last_classification: dict
    last_saved_model_entry: dict
    last_final_model_path: str
    last_final_model_url: str
    last_output_source: str
    last_stl_export_path: str
    last_stl_export_status: str
    last_stl_export_message: str
    last_stl_source_model_path: str
    last_generation_path: str
    last_generation_route: str
    last_generation_fallback_reason: str
    last_implementation_id: str
    last_execution_recipe: str
    preview_model_url: str
    last_preview_model_url: str
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
            last_interpretation_summary=state.get("last_interpretation_summary") or "",
            last_decision_summary=state.get("last_decision_summary") or "",
            last_style_summary=state.get("last_style_summary") or "",
            current_saved_model_id=state.get("current_saved_model_id") or "",
            current_saved_model_editable=bool(state.get("current_saved_model_editable")),
            last_opened_model_id=state.get("last_opened_model_id") or "",
            reopen_source=state.get("reopen_source") or "",
            reopened_plan_summary=state.get("reopened_plan_summary") or "",
            current_editable_params=state.get("current_editable_params") or [],
            last_editable_params=state.get("last_editable_params") or [],
            last_regeneration_source=state.get("last_regeneration_source") or "",
            edited_plan_summary=state.get("edited_plan_summary") or "",
            last_missing_info=state.get("last_missing_info") or [],
            last_assumptions=state.get("last_assumptions") or [],
            last_warnings=state.get("last_warnings") or [],
            last_validation_summary=state.get("last_validation_summary") or "",
            last_plan=state.get("last_plan") or {},
            last_validation=state.get("last_validation") or {},
            last_classification=state.get("last_classification") or {},
            last_saved_model_entry=state.get("last_saved_model_entry") or {},
            last_final_model_path=state.get("last_final_model_path") or "",
            last_final_model_url=state.get("last_final_model_url") or to_file_url(state.get("last_final_model_path") or ""),
            last_output_source=state.get("last_output_source") or "",
            last_stl_export_path=state.get("last_stl_export_path") or "",
            last_stl_export_status=state.get("last_stl_export_status") or "",
            last_stl_export_message=state.get("last_stl_export_message") or "",
            last_stl_source_model_path=state.get("last_stl_source_model_path") or "",
            last_generation_path=state.get("last_generation_path") or "",
            last_generation_route=state.get("last_generation_route") or "",
            last_generation_fallback_reason=state.get("last_generation_fallback_reason") or "",
            last_implementation_id=state.get("last_implementation_id") or "",
            last_execution_recipe=state.get("last_execution_recipe") or "",
            preview_model_url=state.get("last_preview_model_url") or to_file_url(state.get("last_preview_model_path") or ""),
            last_preview_model_url=state.get("last_preview_model_url") or to_file_url(state.get("last_preview_model_path") or ""),
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

    def regenerate_model_from_plan(self, plan_payload: dict, log: LogCallback | None = None) -> dict:
        """Regenerate the current model from an edited structured plan."""
        logger = log or (lambda _message: None)
        runtime_health = self.get_runtime_health(refresh=True)
        if runtime_health.get("runtime_health_status") != "ready":
            message = runtime_health.get("runtime_health_message") or "Runtime setup is incomplete."
            logger(f"[CONTROLLER] regeneration blocked: {message}")
            payload = self.record_terminal_failure(
                prompt_text=str((plan_payload or {}).get("source_request_text") or (plan_payload or {}).get("request_text") or ""),
                message=message,
                status="error",
                raw_status="runtime_unhealthy",
                runtime_health=runtime_health,
            )
            payload["setup_required"] = True
            return payload
        payload = dict(plan_payload or {})
        logger(
            "[CONTROLLER] regenerate_model_from_plan start: "
            f"source_generation_id={payload.get('source_generation_id', '')!r}, "
            f"request_text={payload.get('source_request_text') or payload.get('request_text') or ''!r}"
        )
        result = self.make_json_safe(
            generate_model_from_plan(
                payload.get("plan") or payload,
                log=logger,
                source_generation_id=payload.get("source_generation_id", ""),
                source_request_text=payload.get("source_request_text") or payload.get("request_text") or "",
                source_plan=payload.get("source_plan"),
                current_saved_model_id=payload.get("current_saved_model_id", ""),
                current_saved_model_editable=bool(payload.get("current_saved_model_editable")),
                last_opened_model_id=payload.get("last_opened_model_id", ""),
                reopen_source=payload.get("reopen_source", ""),
                reopened_plan_summary=payload.get("reopened_plan_summary", ""),
                edited_plan_summary=payload.get("edited_plan_summary", ""),
                regeneration_source=payload.get("regeneration_source", "edited_plan"),
            )
        )
        result["runtime_health"] = runtime_health
        logger(
            "[CONTROLLER] regenerate_model_from_plan returned: "
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
        state["last_preview_model_url"] = ""
        state["last_preview_asset_version"] = ""
        state["last_preview_export_status"] = "error"
        state["last_preview_export_message"] = message
        state["last_final_model_path"] = ""
        state["last_final_model_url"] = ""
        state["last_output_source"] = ""
        state["last_stl_export_path"] = ""
        state["last_stl_export_status"] = ""
        state["last_stl_export_message"] = ""
        state["last_stl_source_model_path"] = ""
        state["last_implementation_id"] = ""
        state["last_execution_recipe"] = ""
        state["last_generation_timestamp"] = datetime.now().isoformat(timespec="seconds")
        state["last_generation_family"] = ""
        state["last_generation_status"] = status
        state["last_generation_raw_status"] = raw_status
        state["last_generation_message"] = message
        state["last_interpretation_summary"] = ""
        state["last_decision_summary"] = ""
        state["last_style_summary"] = ""
        state["current_editable_params"] = []
        state["last_editable_params"] = []
        state["last_regeneration_source"] = ""
        state["edited_plan_summary"] = ""
        state["last_missing_info"] = []
        state["last_assumptions"] = []
        state["last_warnings"] = []
        state["last_validation_summary"] = message
        state["last_plan"] = {}
        state["last_recipe"] = {}
        state["last_recipe_summary"] = ""
        state["last_execution_path"] = ""
        state["last_execution_summary"] = ""
        state["last_generation_path"] = ""
        state["last_generation_route"] = ""
        state["last_generation_fallback_reason"] = ""
        state["last_validation"] = {}
        state["last_classification"] = {}
        state["last_saved_model_entry"] = {}
        state["current_saved_model_id"] = ""
        state["current_saved_model_editable"] = False
        state["last_opened_model_id"] = ""
        state["reopen_source"] = ""
        state["reopened_plan_summary"] = ""
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
            "stl_export_path": "",
            "stl_export_status": "error",
            "stl_export_message": message,
            "stl_source_model_path": "",
            "supported_families": [],
            "runtime_health": runtime_health or self.get_runtime_health(refresh=False),
        }

    def open_in_blender(self, script_path: str | None = None, interactive: bool = True) -> tuple[bool, str]:
        """Launch Blender for the current generated script."""
        health = self.get_runtime_health(refresh=True)
        if not health.get("blender_detected"):
            return False, health.get("runtime_health_message", "Blender is not configured.")
        state = load_state()
        preferred_path = state.get("last_final_model_path") or state.get("last_preview_model_path") or ""
        target_path = Path(script_path) if script_path else (Path(preferred_path) if preferred_path else GENERATED_SCRIPT_PATH)
        if target_path.suffix.lower() in {".glb", ".gltf"}:
            return open_generated_model_file(target_path, interactive=interactive)
        return run_generated_script(target_path, interactive=interactive)

    def open_saved_model_in_blender(self, model_id: str) -> dict:
        """Launch Blender for a saved model entry's persisted final artifact."""
        entry = next((item for item in list_saved_models() if item.get("id") == model_id), None)
        if not entry:
            return {"success": False, "message": "Saved model not found.", "model_id": model_id}
        target_path = entry.get("final_model_path") or entry.get("preview_model_path") or entry.get("script_path") or None
        if target_path and str(target_path).lower().endswith((".glb", ".gltf")):
            success, message = open_generated_model_file(Path(target_path), interactive=True)
        else:
            success, message = self.open_in_blender(script_path=entry.get("script_path") or None, interactive=True)
        return {
            "success": success,
            "message": message,
            "model_id": model_id,
        }

    def export_current_model_stl(self) -> dict:
        """Export the currently active final model artifact to STL."""
        health = self.get_runtime_health(refresh=True)
        if not health.get("blender_detected"):
            message = health.get("runtime_health_message", "Blender is not configured.")
            state = load_state()
            state["last_stl_export_path"] = ""
            state["last_stl_export_status"] = "unavailable"
            state["last_stl_export_message"] = message
            state["last_stl_source_model_path"] = state.get("last_final_model_path") or ""
            save_state(state)
            return self.make_json_safe(
                {
                    "success": False,
                    "message": message,
                    "export_status": "unavailable",
                    "stl_path": "",
                    "source_model_path": "",
                    "generation_id": "",
                    "saved_model_id": "",
                }
            )

        state = load_state()
        source_model_path = state.get("last_final_model_path") or ""
        if not source_model_path:
            message = "No final model artifact is available for STL export."
            state = load_state()
            state["last_stl_export_path"] = ""
            state["last_stl_export_status"] = "unavailable"
            state["last_stl_export_message"] = message
            state["last_stl_source_model_path"] = ""
            save_state(state)
            return self.make_json_safe(
                {
                    "success": False,
                    "message": message,
                    "export_status": "unavailable",
                    "stl_path": "",
                    "source_model_path": "",
                    "generation_id": state.get("last_generation_id") or "",
                    "saved_model_id": (state.get("last_saved_model_entry") or {}).get("id", ""),
                }
            )

        source_path = Path(source_model_path)
        if not source_path.exists():
            message = f"Final model artifact not found at: {source_path}"
            state["last_stl_export_path"] = ""
            state["last_stl_export_status"] = "missing_source"
            state["last_stl_export_message"] = message
            state["last_stl_source_model_path"] = str(source_path)
            save_state(state)
            return self.make_json_safe(
                {
                    "success": False,
                    "message": message,
                    "export_status": "missing_source",
                    "stl_path": "",
                    "source_model_path": str(source_path),
                    "generation_id": state.get("last_generation_id") or "",
                    "saved_model_id": (state.get("last_saved_model_entry") or {}).get("id", ""),
                }
            )

        export_name = f"{source_path.stem}.stl"
        stl_path = EXPORTS_DIR / export_name
        success, message = export_model_to_stl(source_path, stl_path)
        export_status = "ready" if success else "error"
        saved_model_entry = dict(state.get("last_saved_model_entry") or {})
        saved_model_id = saved_model_entry.get("id", "")
        if success:
            state["last_stl_export_path"] = str(stl_path)
            state["last_stl_export_status"] = export_status
            state["last_stl_export_message"] = message
            state["last_stl_source_model_path"] = str(source_path)
            if saved_model_id:
                updated_entry = update_saved_model_entry(
                    saved_model_id,
                    {
                        "stl_export_path": str(stl_path),
                        "stl_export_status": export_status,
                        "stl_export_message": message,
                        "stl_source_model_path": str(source_path),
                    },
                )
                if updated_entry is not None:
                    state["last_saved_model_entry"] = updated_entry
            save_state(state)
        else:
            state["last_stl_export_path"] = ""
            state["last_stl_export_status"] = export_status
            state["last_stl_export_message"] = message
            state["last_stl_source_model_path"] = str(source_path)
            save_state(state)

        return self.make_json_safe(
            {
                "success": success,
                "message": message,
                "export_status": export_status,
                "stl_path": str(stl_path) if success else "",
                "source_model_path": str(source_path),
                "generation_id": state.get("last_generation_id") or "",
                "saved_model_id": saved_model_id,
            }
        )

    def open_saved_model_for_workspace(self, model_id: str) -> dict:
        """Restore a saved model's truthful workspace context for editing."""
        model_id = str(model_id or "").strip()
        if not model_id:
            return {"success": False, "message": "Saved model id is required.", "model_id": "", "state": self.get_status_payload()}

        entry = next((item for item in list_saved_models() if item.get("id") == model_id), None)
        if not entry:
            return {"success": False, "message": "Saved model not found.", "model_id": model_id, "state": self.get_status_payload()}

        plan = entry.get("plan") if isinstance(entry.get("plan"), dict) else {}
        editable_params = list(entry.get("editable_params") or [])
        if not editable_params and plan:
            editable_params = collect_editable_params_for_plan(plan)
        is_editable = bool(plan and editable_params)
        reopen_source = "saved_model"
        reopened_plan_summary = entry.get("reopened_plan_summary") or entry.get("edited_plan_summary") or entry.get("validation_summary") or ""
        family_key = entry.get("family") or ""
        if not family_key and isinstance(plan, dict):
            family_key = (plan.get("intent") or {}).get("object_type", "") or ""
        state = load_state()
        state["last_user_request"] = entry.get("prompt") or entry.get("generation_id") or ""
        state["last_generation_id"] = entry.get("generation_id") or ""
        state["last_generation_timestamp"] = datetime.now().isoformat(timespec="seconds")
        state["last_generation_status"] = "ready"
        state["last_generation_raw_status"] = "ready"
        state["last_generation_message"] = entry.get("validation_summary") or "Saved model opened from the local library."
        state["last_generation_family"] = family_key
        state["last_interpretation_summary"] = entry.get("interpretation_summary") or entry.get("validation_summary") or "Saved model opened from the local library."
        state["last_decision_summary"] = entry.get("decision_summary") or reopened_plan_summary or "Saved model loaded from the local library."
        state["last_style_summary"] = entry.get("style_summary") or ""
        state["current_saved_model_id"] = model_id
        state["current_saved_model_editable"] = is_editable
        state["last_opened_model_id"] = model_id
        state["reopen_source"] = reopen_source
        state["reopened_plan_summary"] = reopened_plan_summary
        state["current_editable_params"] = editable_params if is_editable else []
        state["last_editable_params"] = editable_params if is_editable else []
        state["last_regeneration_source"] = ""
        state["edited_plan_summary"] = ""
        state["last_missing_info"] = list((plan.get("missing_info") or []) if isinstance(plan, dict) else [])
        state["last_assumptions"] = list((plan.get("assumptions") or []) if isinstance(plan, dict) else [])
        state["last_warnings"] = list((plan.get("warnings") or []) if isinstance(plan, dict) else [])
        state["last_validation_summary"] = entry.get("validation_summary") or ""
        state["last_plan"] = plan
        state["last_validation"] = entry.get("validation") or {}
        state["last_classification"] = {"family_key": entry.get("family") or "", "family_label": entry.get("family_label") or ""}
        state["last_saved_model_entry"] = entry
        state["last_recipe"] = entry.get("recipe") or {}
        state["last_recipe_summary"] = entry.get("recipe_summary") or ""
        state["last_execution_path"] = entry.get("execution_path") or ""
        state["last_execution_summary"] = entry.get("execution_summary") or ""
        state["last_generation_path"] = entry.get("generation_path") or ""
        state["last_generation_route"] = entry.get("generation_route") or ""
        state["last_generation_fallback_reason"] = entry.get("generation_fallback_reason") or ""
        state["last_implementation_id"] = entry.get("implementation_id") or ""
        state["last_execution_recipe"] = entry.get("execution_recipe") or ""
        state["last_final_model_path"] = entry.get("final_model_path") or ""
        state["last_final_model_url"] = entry.get("final_model_url") or to_file_url(entry.get("final_model_path") or "")
        state["last_output_source"] = entry.get("final_output_source") or entry.get("execution_path") or ""
        state["last_preview_model_path"] = entry.get("preview_model_path") or ""
        state["last_preview_model_url"] = entry.get("preview_model_url") or to_file_url(entry.get("preview_model_path") or "")
        state["last_preview_asset_version"] = entry.get("generation_id") or ""
        state["last_preview_export_status"] = entry.get("preview_export_status") or "ready"
        state["last_preview_export_message"] = entry.get("preview_export_message") or entry.get("validation_summary") or ""
        state["last_stl_export_path"] = entry.get("stl_export_path") or ""
        state["last_stl_export_status"] = entry.get("stl_export_status") or "not_requested"
        state["last_stl_export_message"] = entry.get("stl_export_message") or ""
        state["last_stl_source_model_path"] = entry.get("stl_source_model_path") or entry.get("final_model_path") or ""
        state["last_run_status"] = "ready" if is_editable else "view_only"
        save_state(state)
        return {
            "success": True,
            "message": "Saved model reopened for editing." if is_editable else "Saved model reopened for viewing.",
            "model_id": model_id,
            "is_editable": is_editable,
            "editable_params": editable_params,
            "state": self.get_status_payload(),
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

    def clean_dev_reload(self, log: LogCallback | None = None) -> dict:
        """Clear generated previews and local Python caches for a development reload."""
        logger = log or (lambda _message: None)
        preview_result = self._clear_preview_artifacts(logger)
        pycache_result = self._clear_python_caches(logger)
        logger("UI reload triggered.")
        return self.make_json_safe(
            {
                "success": True,
                "preview_directory": str(PREVIEWS_DIR),
                "preview_artifacts_cleared": preview_result["cleared"],
                "preview_artifacts_failed": preview_result["failed"],
                "pycache_directories_cleared": pycache_result["cleared"],
                "pycache_directories_failed": pycache_result["failed"],
                "messages": preview_result["messages"] + pycache_result["messages"] + ["UI reload triggered."],
            }
        )

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

    def _clear_preview_artifacts(self, log: LogCallback) -> dict:
        messages: list[str] = []
        cleared = 0
        failed = 0
        preview_dir = PREVIEWS_DIR
        if not preview_dir.exists():
            message = f"Preview directory not found; nothing to clear: {preview_dir}"
            log(message)
            messages.append(message)
            return {"cleared": 0, "failed": 0, "messages": messages}

        for entry in sorted(preview_dir.iterdir(), key=lambda item: item.name):
            try:
                if entry.is_dir():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
                cleared += 1
                message = f"Cleared preview artifact: {entry}"
                log(message)
                messages.append(message)
            except Exception as error:  # pragma: no cover - defensive cleanup path
                failed += 1
                message = f"Failed to clear preview artifact {entry}: {error}"
                log(message)
                messages.append(message)
        return {"cleared": cleared, "failed": failed, "messages": messages}

    def _clear_python_caches(self, log: LogCallback) -> dict:
        messages: list[str] = []
        cleared = 0
        failed = 0
        root = PROJECT_ROOT.resolve()
        for cache_dir in sorted(root.rglob("__pycache__"), key=lambda item: str(item)):
            try:
                resolved_cache = cache_dir.resolve()
                resolved_cache.relative_to(root)
            except Exception:
                continue
            try:
                shutil.rmtree(cache_dir)
                cleared += 1
                message = f"Cleared Python cache directory: {cache_dir}"
                log(message)
                messages.append(message)
            except Exception as error:  # pragma: no cover - defensive cleanup path
                failed += 1
                message = f"Failed to clear Python cache directory {cache_dir}: {error}"
                log(message)
                messages.append(message)
        if not cleared and not failed:
            message = "No Python cache directories found under the project root."
            log(message)
            messages.append(message)
        return {"cleared": cleared, "failed": failed, "messages": messages}

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
