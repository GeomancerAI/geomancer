"""Load and save simple session state for the terminal app."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = PROJECT_ROOT / "data" / "session_state.json"


DEFAULT_STATE = {
    "setup_completed": False,
    "first_run_completed": False,
    "ollama_installed": False,
    "ollama_running": False,
    "ollama_version": "",
    "ollama_model_name": "",
    "ollama_model_ready": False,
    "blender_detected": False,
    "blender_path": "",
    "runtime_health_status": "unknown",
    "runtime_health_message": "Runtime health has not been checked yet.",
    "last_user_request": "",
    "last_generation_id": "",
    "last_generated_script_path": "",
    "last_preview_model_path": "",
    "last_preview_asset_version": "",
    "last_preview_export_status": "",
    "last_preview_export_message": "",
    "last_generation_timestamp": "",
    "last_generation_family": "",
    "last_generation_status": "",
    "last_generation_raw_status": "",
    "last_generation_message": "",
    "last_validation_summary": "",
    "last_plan": {},
    "last_validation": {},
    "last_classification": {},
    "last_saved_model_entry": {},
    "last_run_status": "",
}


def load_state() -> dict:
    """Load session state from disk, or return defaults if missing/broken."""
    if not STATE_PATH.exists():
        return DEFAULT_STATE.copy()

    try:
        raw_text = STATE_PATH.read_text(encoding="utf-8").strip()
        if not raw_text:
            return DEFAULT_STATE.copy()
        loaded = json.loads(raw_text)
    except (json.JSONDecodeError, OSError):
        return DEFAULT_STATE.copy()

    if not isinstance(loaded, dict):
        return DEFAULT_STATE.copy()

    state = DEFAULT_STATE.copy()
    state.update({key: loaded.get(key, value) for key, value in DEFAULT_STATE.items()})
    return state


def save_state(state: dict) -> Path:
    """Save the session state to disk."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged_state = DEFAULT_STATE.copy()
    merged_state.update(state)
    STATE_PATH.write_text(json.dumps(merged_state, indent=2), encoding="utf-8")
    return STATE_PATH
