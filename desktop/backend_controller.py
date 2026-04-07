"""Desktop-facing controller that wraps the existing Geomancer backend."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.blender_runner import run_generated_script
from app.chat_agent import GENERATED_SCRIPT_PATH, generate_model_request, load_version
from app.llm_client import OllamaClient
from app.state import load_state


LogCallback = Callable[[str], None]


@dataclass
class DesktopStatus:
    """Simple status snapshot for the desktop shell."""

    version: str
    generated_script_path: str
    preview_model_path: str
    preview_export_status: str
    preview_export_message: str
    last_user_request: str
    last_generation_family: str
    last_generation_status: str
    last_generation_message: str
    last_generation_timestamp: str
    last_validation_summary: str
    last_plan: dict
    last_validation: dict
    last_classification: dict
    last_run_status: str


class BackendController:
    """Thin adapter over the current Python generation pipeline.

    The goal is to keep the existing backend behavior intact while exposing
    operations that a desktop UI can call via a bridge layer.
    """

    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or OllamaClient()

    def get_status(self) -> DesktopStatus:
        """Return current persisted backend state for the desktop shell."""
        state = load_state()
        return DesktopStatus(
            version=load_version(),
            generated_script_path=state.get("last_generated_script_path") or str(GENERATED_SCRIPT_PATH),
            preview_model_path=state.get("last_preview_model_path") or "",
            preview_export_status=state.get("last_preview_export_status") or "",
            preview_export_message=state.get("last_preview_export_message") or "",
            last_user_request=state.get("last_user_request") or "",
            last_generation_family=state.get("last_generation_family") or "",
            last_generation_status=state.get("last_generation_status") or "",
            last_generation_message=state.get("last_generation_message") or "",
            last_generation_timestamp=state.get("last_generation_timestamp") or "",
            last_validation_summary=state.get("last_validation_summary") or "",
            last_plan=state.get("last_plan") or {},
            last_validation=state.get("last_validation") or {},
            last_classification=state.get("last_classification") or {},
            last_run_status=state.get("last_run_status") or "idle",
        )

    def generate_model(self, prompt_text: str, log: LogCallback | None = None) -> dict:
        """Run the existing generation flow and return the structured result."""
        logger = log or (lambda _message: None)
        return generate_model_request(prompt_text, self.client, log=logger, show_spinner=False)

    def open_in_blender(self, script_path: str | None = None, interactive: bool = True) -> tuple[bool, str]:
        """Launch Blender for the current generated script."""
        target_path = Path(script_path) if script_path else GENERATED_SCRIPT_PATH
        return run_generated_script(target_path, interactive=interactive)
