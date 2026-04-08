"""Qt WebChannel bridge between the desktop UI and Python backend."""

from __future__ import annotations

import json
import traceback
from concurrent.futures import Future, ThreadPoolExecutor

from PySide6.QtCore import QObject, QThread, Signal, Slot

from desktop.backend_controller import BackendController


def run_generation_job(controller: BackendController, prompt_text: str) -> dict:
    """Execute one generation request in plain Python background execution."""
    logs: list[str] = []

    def append_log(message: str) -> None:
        logs.append(str(message))

    try:
        append_log("[WORKER] python generation job start")
        result = controller.generate_model(prompt_text, log=append_log)
        safe_payload = controller.make_json_safe(result)
        append_log("[WORKER] backend generation returned")
        return {
            "failed": False,
            "payload": safe_payload,
            "logs": logs,
        }
    except Exception as error:  # pragma: no cover - runtime guard
        tb = traceback.format_exc()
        append_log(f"[WORKER] run exception: {str(error)}")
        append_log(tb)
        failure_payload = controller.record_terminal_failure(
            prompt_text=prompt_text,
            message=f"Generation job failed: {error}",
            status="error",
            raw_status="thread_exception",
        )
        safe_payload = controller.make_json_safe(failure_payload)
        safe_payload.setdefault("raw_status", "thread_exception")
        safe_payload.setdefault("preview_export_status", "error")
        return {
            "failed": True,
            "payload": safe_payload,
            "logs": logs,
        }


class ModelPullThread(QThread):
    """Background thread for Ollama model pull progress."""

    progress = Signal(str)
    resultReady = Signal(str)
    resultFailed = Signal(str)

    def __init__(self, controller: BackendController, model_name: str) -> None:
        super().__init__()
        self._controller = controller
        self._model_name = model_name

    @Slot()
    def run(self) -> None:
        try:
            result = self._controller.start_model_pull(
                self._model_name,
                progress_callback=lambda event: self.progress.emit(json.dumps(self._controller.make_json_safe(event))),
            )
            self.resultReady.emit(json.dumps(self._controller.make_json_safe(result)))
        except Exception as error:  # pragma: no cover - UI runtime guard
            payload = {
                "status": "error",
                "message": f"Model pull failed: {error}",
                "model_name": self._model_name,
            }
            self.resultFailed.emit(json.dumps(payload))


class GeomancerBridge(QObject):
    """Exposes a minimal desktop API to the embedded web UI."""

    stateChanged = Signal(str)
    generationCompleted = Signal(str)
    generationFailed = Signal(str)
    logMessage = Signal(str)
    runtimeHealthChanged = Signal(str)
    modelPullProgress = Signal(str)
    modelPullCompleted = Signal(str)
    modelPullFailed = Signal(str)
    _generationJobResolved = Signal(object)
    _generationJobCrashed = Signal(str)

    def __init__(self, controller: BackendController | None = None) -> None:
        super().__init__()
        self._controller = controller or BackendController()
        self._generation_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="geomancer-generate")
        self._active_generation_future: Future | None = None
        self._model_pull_thread: ModelPullThread | None = None
        self._active_request_text = ""
        self._generation_job_started = False
        self._generationJobResolved.connect(self._handle_generation_job_resolved)
        self._generationJobCrashed.connect(self._handle_generation_job_crashed)

    @Slot(result=str)
    def getInitialState(self) -> str:
        """Return shell bootstrap state as JSON."""
        try:
            status = self._controller.get_status_payload()
            payload = {
                "appName": "Geomancer",
                "version": status.get("version", ""),
                "generationId": status.get("generation_id", ""),
                "generatedScriptPath": status.get("generated_script_path", ""),
                "previewModelPath": status.get("preview_model_path", ""),
                "previewAssetVersion": status.get("preview_asset_version", ""),
                "previewExportStatus": status.get("preview_export_status", ""),
                "previewExportMessage": status.get("preview_export_message", ""),
                "lastUserRequest": status.get("last_user_request", ""),
                "lastGenerationFamily": status.get("last_generation_family", ""),
                "lastGenerationStatus": status.get("last_generation_status", ""),
                "lastGenerationRawStatus": status.get("last_generation_raw_status", ""),
                "lastGenerationMessage": status.get("last_generation_message", ""),
                "lastGenerationTimestamp": status.get("last_generation_timestamp", ""),
                "lastValidationSummary": status.get("last_validation_summary", ""),
                "lastPlan": status.get("last_plan", {}),
                "lastValidation": status.get("last_validation", {}),
                "lastClassification": status.get("last_classification", {}),
                "lastSavedModelEntry": status.get("last_saved_model_entry", {}),
                "librarySummary": status.get("library_summary", {}),
                "lastRunStatus": status.get("last_run_status", "idle"),
                "viewerStatus": status.get("preview_export_status", "") or "idle",
                "setupCompleted": status.get("setup_completed", False),
                "firstRunCompleted": status.get("first_run_completed", False),
                "ollamaInstalled": status.get("ollama_installed", False),
                "ollamaRunning": status.get("ollama_running", False),
                "ollamaVersion": status.get("ollama_version", ""),
                "ollamaModelName": status.get("ollama_model_name", ""),
                "ollamaModelReady": status.get("ollama_model_ready", False),
                "blenderDetected": status.get("blender_detected", False),
                "blenderPath": status.get("blender_path", ""),
                "runtimeHealthStatus": status.get("runtime_health_status", "unknown"),
                "runtimeHealthMessage": status.get("runtime_health_message", ""),
                "runtimeHealth": status.get("runtime_health", {}),
                "setupFlow": status.get("setup_flow", []),
            }
            return self._safe_json_dumps(payload)
        except Exception as error:
            self._log_bridge(f"getInitialState failed: {error!r}")
            self._log_bridge(traceback.format_exc())
            fallback = self._controller.record_terminal_failure(
                prompt_text="",
                message=f"Bridge state refresh failed: {error}",
                status="error",
            )
            payload = {
                "appName": "Geomancer",
                "version": "",
                "generationId": fallback.get("generation_id", ""),
                "generatedScriptPath": "",
                "previewModelPath": "",
                "previewAssetVersion": "",
                "previewExportStatus": "error",
                "previewExportMessage": fallback.get("message", ""),
                "lastUserRequest": fallback.get("request_text", ""),
                "lastGenerationFamily": "",
                "lastGenerationStatus": fallback.get("status", "error"),
                "lastGenerationRawStatus": fallback.get("raw_status", "bridge_state_failure"),
                "lastGenerationMessage": fallback.get("message", ""),
                "lastGenerationTimestamp": "",
                "lastValidationSummary": fallback.get("message", ""),
                "lastPlan": {},
                "lastValidation": {},
                "lastClassification": {},
                "lastSavedModelEntry": {},
                "librarySummary": {"saved_model_count": 0, "recent_saved_models": [], "project_count": 0, "template_count": 0, "templates": []},
                "lastRunStatus": "error",
                "viewerStatus": "error",
                "setupCompleted": False,
                "firstRunCompleted": False,
                "ollamaInstalled": False,
                "ollamaRunning": False,
                "ollamaVersion": "",
                "ollamaModelName": "",
                "ollamaModelReady": False,
                "blenderDetected": False,
                "blenderPath": "",
                "runtimeHealthStatus": "error",
                "runtimeHealthMessage": fallback.get("message", ""),
                "runtimeHealth": {},
                "setupFlow": [],
            }
            return self._safe_json_dumps(payload)

    @Slot(str)
    def generateModel(self, prompt_text: str) -> None:
        """Start a generation request in a Python background executor."""
        try:
            self._log_bridge(f"[BRIDGE] generateModel slot entered: request_text={prompt_text!r}")
            cleaned_prompt = prompt_text.strip()
            self._log_bridge(f"[BRIDGE] submitPrompt called: request_text={cleaned_prompt!r}")
            if not cleaned_prompt:
                self._log_bridge("[BRIDGE] submitPrompt early return: empty prompt")
                self._emit_terminal_failure(prompt_text="", message="Enter a prompt before generating.")
                return

            if self._active_generation_future is not None and not self._active_generation_future.done():
                self._log_bridge("[BRIDGE] submitPrompt early return: generation already running")
                self._emit_terminal_failure(prompt_text=cleaned_prompt, message="Generation is already running.")
                return

            self._active_request_text = cleaned_prompt
            self._generation_job_started = False
            self._log_bridge("[BRIDGE] submitting generation job")
            future = self._generation_executor.submit(run_generation_job, self._controller, cleaned_prompt)
            self._active_generation_future = future
            future.add_done_callback(self._on_generation_future_done)
        except Exception as error:
            cleaned_prompt = prompt_text.strip() if isinstance(prompt_text, str) else ""
            self._log_bridge(f"[BRIDGE] generateModel slot exception: {error!r}")
            self._log_bridge(traceback.format_exc())
            self._emit_terminal_failure(
                prompt_text=cleaned_prompt,
                message=f"Bridge generateModel failed: {error}",
            )

    @Slot()
    def refreshState(self) -> None:
        """Emit the latest persisted backend state."""
        self._log_bridge("[BRIDGE] refreshState starting")
        runtime_health = self._controller.refresh_runtime_health()
        self.runtimeHealthChanged.emit(self._safe_json_dumps(runtime_health))
        payload = self.getInitialState()
        self.stateChanged.emit(payload)
        self._log_bridge("[BRIDGE] refreshState succeeded")

    @Slot(result=str)
    def getRuntimeHealth(self) -> str:
        """Return the current runtime health as JSON."""
        return self._safe_json_dumps(self._controller.get_runtime_health(refresh=True))

    @Slot(result=str)
    def maybeDetectOrRepairEnvironment(self) -> str:
        """Refresh environment detection and return the runtime payload."""
        health = self._controller.maybe_detect_or_repair_environment()
        self.runtimeHealthChanged.emit(self._safe_json_dumps(health))
        self.refreshState()
        return self._safe_json_dumps(health)

    @Slot(result=str)
    def runSetupSmokeTest(self) -> str:
        """Run the first-run smoke test and return the result."""
        result = self._controller.run_setup_smoke_test()
        runtime_health = result.get("runtime_health", {})
        if runtime_health:
            self.runtimeHealthChanged.emit(self._safe_json_dumps(runtime_health))
        self.refreshState()
        return self._safe_json_dumps(result)

    @Slot(str, result=str)
    def startModelPull(self, model_name: str) -> str:
        """Start pulling an Ollama model in the background."""
        cleaned_model_name = model_name.strip()
        if not cleaned_model_name:
            return self._safe_json_dumps({"started": False, "message": "Model name is required."})
        if self._model_pull_thread is not None:
            return self._safe_json_dumps({"started": False, "message": "A model pull is already running."})

        self._model_pull_thread = ModelPullThread(self._controller, cleaned_model_name)
        self._model_pull_thread.progress.connect(self.modelPullProgress.emit)
        self._model_pull_thread.resultReady.connect(self._handle_model_pull_finished)
        self._model_pull_thread.resultFailed.connect(self._handle_model_pull_failed)
        QThread.finished.__get__(self._model_pull_thread, ModelPullThread).connect(self._cleanup_model_pull_thread)
        self._model_pull_thread.start()
        return self._safe_json_dumps({"started": True, "model_name": cleaned_model_name})

    @Slot(result=str)
    def openLatestInBlender(self) -> str:
        """Launch the latest generated script in Blender."""
        success, message = self._controller.open_in_blender(interactive=True)
        self.refreshState()
        return json.dumps({"success": success, "message": message})

    def _on_generation_future_done(self, future: Future) -> None:
        try:
            result = future.result()
        except Exception as error:  # pragma: no cover - executor guard
            self._generationJobCrashed.emit(str(error))
            return

        if result.get("logs"):
            self._generationJobResolved.emit(result)
            return
        self._generationJobResolved.emit(result)

    @Slot(object)
    def _handle_generation_job_resolved(self, result: object) -> None:
        result_dict = result if isinstance(result, dict) else {}
        for message in result_dict.get("logs", []):
            self._relay_worker_log(str(message))

        self._generation_job_started = any(
            str(message).startswith("[WORKER] python generation job start")
            for message in result_dict.get("logs", [])
        )
        self._log_bridge("[BRIDGE] future completed successfully")
        payload = result_dict.get("payload", {})
        if result_dict.get("failed"):
            self._handle_worker_failed(payload)
            return
        self._handle_worker_finished(payload)

    @Slot(str)
    def _handle_generation_job_crashed(self, error_message: str) -> None:
        self._log_bridge("[BRIDGE] future completed with exception")
        self._emit_terminal_failure(
            prompt_text=self._active_request_text,
            message=f"Generation future crashed: {error_message}",
        )

    @Slot(object)
    def _handle_worker_finished(self, payload: str | dict) -> None:
        self._log_bridge("[BRIDGE] worker finished handler entered")
        self._log_bridge("[BRIDGE] _handle_generation_finished entered")
        self._log_bridge(f"[BRIDGE] payload type: {type(payload).__name__}")
        self._log_bridge(f"[BRIDGE] payload preview: {self._truncate_payload_preview(payload)}")
        try:
            self._emit_completion_payload(payload)
        except Exception as error:
            self._log_bridge(f"[BRIDGE] _handle_generation_finished emit failed: {error!r}")
            self._log_bridge(traceback.format_exc())
            self._emit_bridge_fallback(
                prompt_text=self._extract_request_text(payload),
                message=f"Bridge completion handling failed: {error}",
                raw_status="bridge_completion_error",
            )

        try:
            self._log_bridge("[BRIDGE] right before refreshState()")
            self.refreshState()
            self._log_bridge("[BRIDGE] immediately after refreshState()")
        except Exception as error:
            self._log_bridge(f"[BRIDGE] refreshState failed after completion emit: {error!r}")
            self._log_bridge(traceback.format_exc())
        finally:
            self._cleanup_active_generation()

    @Slot(object)
    def _handle_worker_failed(self, payload: str | dict) -> None:
        prompt_text = self._extract_request_text(payload)
        self._log_bridge(f"[BRIDGE] worker failed handler entered: prompt_text={prompt_text!r}")
        self._log_bridge(f"[BRIDGE] failure payload preview: {self._truncate_payload_preview(payload)}")
        try:
            self._emit_completion_payload(payload)
        except Exception as error:
            self._log_bridge(f"[BRIDGE] worker failed handler emit failed: {error!r}")
            self._log_bridge(traceback.format_exc())
            self._emit_terminal_failure(prompt_text=prompt_text, message=f"Bridge worker failure handling failed: {error}")
            return

        try:
            parsed = self._normalize_terminal_payload(payload)
            message = parsed.get("message", "")
            self._log_bridge("[BRIDGE] emitting generationFailed")
            self.generationFailed.emit(str(message))
        except Exception as error:
            self._log_bridge(f"[BRIDGE] generationFailed emit failed: {error!r}")
            self._log_bridge(traceback.format_exc())
        try:
            self.refreshState()
        except Exception as error:
            self._log_bridge(f"[BRIDGE] refreshState failed after worker failure: {error!r}")
            self._log_bridge(traceback.format_exc())
        finally:
            self._cleanup_active_generation()

    @Slot()
    def _handle_model_pull_finished(self, payload: str) -> None:
        self.modelPullCompleted.emit(payload)
        try:
            parsed = json.loads(payload)
            runtime_health = parsed.get("runtime_health", {})
            if runtime_health:
                self.runtimeHealthChanged.emit(self._safe_json_dumps(runtime_health))
        except json.JSONDecodeError:
            pass
        self.refreshState()

    @Slot(str)
    def _handle_model_pull_failed(self, payload: str) -> None:
        self.modelPullFailed.emit(payload)
        self.refreshState()

    def _cleanup_active_generation(self) -> None:
        self._active_generation_future = None
        self._active_request_text = ""
        self._generation_job_started = False
        self._log_bridge("[BRIDGE] cleanup complete")

    @Slot()
    def _cleanup_model_pull_thread(self) -> None:
        if self._model_pull_thread is not None:
            self._model_pull_thread.deleteLater()
        self._model_pull_thread = None

    def _emit_terminal_failure(self, *, prompt_text: str, message: str) -> None:
        payload = self._controller.record_terminal_failure(prompt_text=prompt_text, message=message, status="error")
        self._emit_bridge_fallback(
            prompt_text=prompt_text,
            message=payload.get("message", message),
            raw_status=payload.get("raw_status", "controller_failure"),
            payload=payload,
        )

    def _emit_bridge_fallback(self, *, prompt_text: str, message: str, raw_status: str, payload: dict | None = None) -> None:
        fallback_payload = payload or self._controller.record_terminal_failure(prompt_text=prompt_text, message=message, status="error")
        fallback_payload.setdefault("status", "error")
        fallback_payload.setdefault("raw_status", raw_status)
        fallback_payload.setdefault("is_terminal", True)
        fallback_payload.setdefault("request_text", prompt_text)
        fallback_payload.setdefault("generation_id", "")
        fallback_payload.setdefault("message", message)
        fallback_payload.setdefault("preview_model_path", "")
        fallback_payload.setdefault("preview_export_status", "error")
        self._log_bridge(
            "[BRIDGE] right before fallback emission: "
            f"raw_status={raw_status!r}, request_text={prompt_text!r}, message={message!r}"
        )
        try:
            self._emit_completion_payload(fallback_payload)
        except Exception as error:
            self._log_bridge(f"[BRIDGE] fallback generationCompleted emit failed: {error!r}")
            self._log_bridge(traceback.format_exc())
        try:
            self._log_bridge("[BRIDGE] emitting generationFailed")
            self.generationFailed.emit(str(message))
        except Exception as error:
            self._log_bridge(f"[BRIDGE] generationFailed emit failed: {error!r}")
            self._log_bridge(traceback.format_exc())
        try:
            self.refreshState()
        except Exception as error:
            self._log_bridge(f"[BRIDGE] fallback refreshState failed: {error!r}")
            self._log_bridge(traceback.format_exc())
        finally:
            self._cleanup_active_generation()

    def _normalize_terminal_payload(self, payload: str | dict) -> dict:
        if isinstance(payload, str):
            parsed = json.loads(payload)
        elif isinstance(payload, dict):
            parsed = payload
        else:
            raise TypeError(f"Unsupported payload type: {type(payload).__name__}")
        normalized = self._controller.make_json_safe(parsed)
        return {
            "generation_id": normalized.get("generation_id", ""),
            "request_text": normalized.get("request_text", ""),
            "status": normalized.get("status", "error"),
            "raw_status": normalized.get("raw_status", normalized.get("status", "error")),
            "is_terminal": bool(normalized.get("is_terminal", True)),
            "message": normalized.get("message", ""),
            "family": normalized.get("family", ""),
            "family_label": normalized.get("family_label", ""),
            "plan": normalized.get("plan", {}),
            "validation": normalized.get("validation", {}),
            "classification": normalized.get("classification", {}),
            "script_path": normalized.get("script_path", ""),
            "preview_model_path": normalized.get("preview_model_path", ""),
            "preview_asset_version": normalized.get("preview_asset_version", ""),
            "preview_export_status": normalized.get("preview_export_status", "not_requested"),
            "preview_export_message": normalized.get("preview_export_message", normalized.get("message", "")),
            "saved_model_entry": normalized.get("saved_model_entry", {}),
            "supported_families": normalized.get("supported_families", []),
        }

    def _emit_completion_payload(self, payload: str | dict) -> None:
        serialized = self._safe_json_dumps(self._normalize_terminal_payload(payload))
        normalized = json.loads(serialized)
        self._log_bridge(
            "[BRIDGE] right before generationCompleted.emit(payload): "
            f"status={normalized.get('status', '')!r}, "
            f"generation_id={normalized.get('generation_id', '')!r}, "
            f"request_text={normalized.get('request_text', '')!r}"
        )
        self._log_bridge("[BRIDGE] emitting generationCompleted")
        self.generationCompleted.emit(serialized)
        self._log_bridge("[BRIDGE] immediately after generationCompleted.emit(payload)")

    def _extract_request_text(self, payload: str | dict) -> str:
        try:
            normalized = self._normalize_terminal_payload(payload)
            return normalized.get("request_text", "")
        except Exception:
            return self._active_request_text

    def _safe_json_dumps(self, payload: dict) -> str:
        return json.dumps(self._controller.make_json_safe(payload))

    def _truncate_payload_preview(self, payload: str | dict, limit: int = 280) -> str:
        try:
            text = payload if isinstance(payload, str) else self._safe_json_dumps(payload)
        except Exception as error:
            text = f"<unprintable payload: {error!r}>"
        text = text.replace("\n", "\\n")
        return text if len(text) <= limit else f"{text[:limit]}..."

    def _log_bridge(self, message: str) -> None:
        try:
            self.logMessage.emit(f"[bridge] {message}")
        except Exception:
            pass

    @Slot(str)
    def _relay_worker_log(self, message: str) -> None:
        if message.startswith("[WORKER] python generation job start"):
            self._generation_job_started = True
        self.logMessage.emit(message)
