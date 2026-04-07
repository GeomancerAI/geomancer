"""Qt WebChannel bridge between the desktop UI and Python backend."""

from __future__ import annotations

import json

from PySide6.QtCore import QObject, QThread, QUrl, Signal, Slot

from desktop.backend_controller import BackendController


class GenerationWorker(QObject):
    """Background worker for long-running generation requests."""

    finished = Signal(str)
    log = Signal(str)
    failed = Signal(str)

    def __init__(self, controller: BackendController, prompt_text: str) -> None:
        super().__init__()
        self._controller = controller
        self._prompt_text = prompt_text

    @Slot()
    def run(self) -> None:
        """Execute generation and emit JSON-serializable results."""
        try:
            result = self._controller.generate_model(self._prompt_text, log=self.log.emit)
            self.finished.emit(json.dumps(result))
        except Exception as error:  # pragma: no cover - UI runtime guard
            self.failed.emit(str(error))


class GeomancerBridge(QObject):
    """Exposes a minimal desktop API to the embedded web UI."""

    stateChanged = Signal(str)
    generationCompleted = Signal(str)
    generationFailed = Signal(str)
    logMessage = Signal(str)

    def __init__(self, controller: BackendController | None = None) -> None:
        super().__init__()
        self._controller = controller or BackendController()
        self._thread: QThread | None = None
        self._worker: GenerationWorker | None = None

    @Slot(result=str)
    def getInitialState(self) -> str:
        """Return shell bootstrap state as JSON."""
        status = self._controller.get_status()
        payload = {
            "appName": "Geomancer",
            "version": status.version,
            "generatedScriptPath": status.generated_script_path,
            "previewModelPath": status.preview_model_path,
            "previewExportStatus": status.preview_export_status,
            "previewExportMessage": status.preview_export_message,
            "lastUserRequest": status.last_user_request,
            "lastGenerationFamily": status.last_generation_family,
            "lastGenerationStatus": status.last_generation_status,
            "lastGenerationMessage": status.last_generation_message,
            "lastGenerationTimestamp": status.last_generation_timestamp,
            "lastValidationSummary": status.last_validation_summary,
            "lastPlan": status.last_plan,
            "lastValidation": status.last_validation,
            "lastClassification": status.last_classification,
            "lastSavedModelEntry": status.last_saved_model_entry,
            "librarySummary": status.library_summary,
            "lastRunStatus": status.last_run_status,
            "viewerStatus": status.preview_export_status or "idle",
        }
        return json.dumps(payload)

    @Slot(str)
    def generateModel(self, prompt_text: str) -> None:
        """Start a generation request in a background thread."""
        cleaned_prompt = prompt_text.strip()
        if not cleaned_prompt:
            self.generationFailed.emit("Enter a prompt before generating.")
            return

        if self._thread is not None:
            self.generationFailed.emit("Generation is already running.")
            return

        self._thread = QThread()
        self._worker = GenerationWorker(self._controller, cleaned_prompt)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self.logMessage.emit)
        self._worker.finished.connect(self._handle_generation_finished)
        self._worker.failed.connect(self._handle_generation_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_worker)
        self._thread.start()

    @Slot()
    def refreshState(self) -> None:
        """Emit the latest persisted backend state."""
        self.stateChanged.emit(self.getInitialState())

    @Slot(result=str)
    def openLatestInBlender(self) -> str:
        """Launch the latest generated script in Blender."""
        success, message = self._controller.open_in_blender(interactive=True)
        self.refreshState()
        return json.dumps({"success": success, "message": message})

    def _handle_generation_finished(self, payload: str) -> None:
        self.generationCompleted.emit(payload)
        self.refreshState()

    def _handle_generation_failed(self, message: str) -> None:
        self.generationFailed.emit(message)

    def _cleanup_worker(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
        if self._thread is not None:
            self._thread.deleteLater()
        self._worker = None
        self._thread = None
