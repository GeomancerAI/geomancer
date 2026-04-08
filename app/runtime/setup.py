"""First-run setup coordination for the local-first desktop flow."""

from __future__ import annotations

from typing import Any

from app.state import load_state, save_state

from .health import RuntimeHealth, collect_runtime_health, sync_runtime_health


def determine_setup_status(health: RuntimeHealth | None = None) -> dict[str, Any]:
    """Return the current first-run setup status and steps."""
    runtime_health = health or collect_runtime_health()
    return {
        "setup_required": runtime_health.setup_required,
        "setup_completed": runtime_health.setup_completed,
        "first_run_completed": runtime_health.first_run_completed,
        "next_step": runtime_health.next_step,
        "steps": build_setup_flow(runtime_health),
    }


def build_setup_flow(health: RuntimeHealth) -> list[dict[str, str]]:
    """Build the UI-facing setup wizard steps."""
    smoke_ready = (
        health.ollama_installed
        and health.ollama_running
        and health.ollama_model_ready
        and health.blender_detected
        and health.blender_callable
    )
    return [
        _build_step("welcome", "Welcome", "complete"),
        _build_step("detect_blender", "Detect Blender", "complete" if health.blender_detected and health.blender_callable else "current" if health.next_step == "configure_blender" else "pending"),
        _build_step("detect_ollama", "Detect Ollama", "complete" if health.ollama_installed and health.ollama_running else "current" if health.next_step in {"install_ollama", "start_ollama"} else "pending"),
        _build_step("pull_model", "Pull Model", "complete" if health.ollama_model_ready else "current" if health.next_step == "pull_model" else "pending"),
        _build_step("smoke_test", "Smoke Test", "complete" if health.setup_completed else "current" if smoke_ready else "pending"),
        _build_step("workspace", "Enter Workspace", "complete" if not health.setup_required else "pending"),
    ]


def persist_setup_completion(health: RuntimeHealth | None = None, *, completed: bool = True) -> dict[str, Any]:
    """Persist first-run setup completion in the local state file."""
    runtime_health = health or collect_runtime_health()
    state = load_state()
    state.update(runtime_health.to_state_fields())
    state["setup_completed"] = bool(completed)
    state["first_run_completed"] = bool(completed)
    save_state(state)
    return state


def refresh_setup_state() -> dict[str, Any]:
    """Refresh runtime health and sync it into session state."""
    health = collect_runtime_health()
    state = sync_runtime_health(health)
    state["setup_completed"] = bool(state.get("setup_completed")) and not health.setup_required
    save_state(state)
    return state


def is_first_run_setup_required() -> bool:
    """Return True when the in-app setup wizard should be shown."""
    return determine_setup_status()["setup_required"]


def _build_step(step_id: str, label: str, status: str) -> dict[str, str]:
    return {"id": step_id, "label": label, "status": status}
