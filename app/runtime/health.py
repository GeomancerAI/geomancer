"""Structured runtime health for the desktop controller and UI."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.state import load_state, save_state

from .blender import run_health_check as run_blender_health_check
from .models import RECOMMENDED_OLLAMA_MODEL
from .ollama import run_health_check as run_ollama_health_check


@dataclass
class RuntimeHealth:
    """Unified local runtime health state for desktop setup and gating."""

    setup_completed: bool
    first_run_completed: bool
    setup_required: bool
    ollama_installed: bool
    ollama_running: bool
    ollama_version: str
    ollama_model_name: str
    ollama_model_ready: bool
    blender_detected: bool
    blender_path: str
    runtime_health_status: str
    runtime_health_message: str
    blender_callable: bool = False
    available_models: list[str] = field(default_factory=list)
    recommended_model: str = RECOMMENDED_OLLAMA_MODEL.name
    issues: list[str] = field(default_factory=list)
    next_step: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return asdict(self)

    def to_state_fields(self) -> dict[str, Any]:
        """Return the persisted subset used by app.state."""
        return {
            "setup_completed": self.setup_completed,
            "first_run_completed": self.first_run_completed,
            "ollama_installed": self.ollama_installed,
            "ollama_running": self.ollama_running,
            "ollama_version": self.ollama_version,
            "ollama_model_name": self.ollama_model_name,
            "ollama_model_ready": self.ollama_model_ready,
            "blender_detected": self.blender_detected,
            "blender_path": self.blender_path,
            "runtime_health_status": self.runtime_health_status,
            "runtime_health_message": self.runtime_health_message,
        }


def collect_runtime_health(state: dict | None = None) -> RuntimeHealth:
    """Probe local dependencies and return the structured runtime health."""
    persisted_state = state or load_state()
    preferred_model = (
        persisted_state.get("ollama_model_name")
        or RECOMMENDED_OLLAMA_MODEL.name
    )
    ollama = run_ollama_health_check(preferred_model)
    blender = run_blender_health_check()

    issues: list[str] = []
    if not ollama["installed"]:
        issues.append("Install Ollama locally.")
        runtime_status = "setup_required"
        runtime_message = "Install Ollama locally to continue first-run setup."
        next_step = "install_ollama"
    elif not ollama["running"]:
        issues.append("Start the local Ollama service.")
        runtime_status = "setup_required"
        runtime_message = ollama["message"]
        next_step = "start_ollama"
    elif not ollama["model_ready"]:
        issues.append(f"Pull the required Ollama model '{ollama['model_name']}'.")
        runtime_status = "setup_required"
        runtime_message = ollama["message"]
        next_step = "pull_model"
    elif not blender["detected"] or not blender["callable"]:
        issues.append("Configure a working Blender executable.")
        runtime_status = "setup_required"
        runtime_message = blender["message"]
        next_step = "configure_blender"
    elif not persisted_state.get("setup_completed"):
        runtime_status = "setup_required"
        runtime_message = "Runtime dependencies are healthy. Run the smoke test to finish setup."
        next_step = "smoke_test"
    else:
        runtime_status = "ready"
        runtime_message = "Local runtime is healthy. Geomancer is ready to generate deterministic geometry."
        next_step = "workspace"

    return RuntimeHealth(
        setup_completed=bool(persisted_state.get("setup_completed")) and runtime_status == "ready",
        first_run_completed=bool(persisted_state.get("first_run_completed")),
        setup_required=runtime_status != "ready",
        ollama_installed=bool(ollama["installed"]),
        ollama_running=bool(ollama["running"]),
        ollama_version=str(ollama.get("version", "")),
        ollama_model_name=str(ollama["model_name"]),
        ollama_model_ready=bool(ollama["model_ready"]),
        blender_detected=bool(blender["detected"]),
        blender_path=str(blender.get("path", "")),
        runtime_health_status=runtime_status,
        runtime_health_message=runtime_message,
        blender_callable=bool(blender["callable"]),
        available_models=list(ollama.get("available_models", [])),
        recommended_model=str(ollama.get("recommended_model", RECOMMENDED_OLLAMA_MODEL.name)),
        issues=issues,
        next_step=next_step,
    )


def sync_runtime_health(health: RuntimeHealth, state: dict | None = None, persist: bool = True) -> dict[str, Any]:
    """Merge runtime health fields into session state and optionally save them."""
    merged_state = load_state() if state is None else dict(state)
    merged_state.update(health.to_state_fields())
    if persist:
        save_state(merged_state)
    return merged_state
