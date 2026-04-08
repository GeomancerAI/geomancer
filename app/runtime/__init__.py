"""Runtime setup and health helpers for the desktop product flow."""

from .health import RuntimeHealth, collect_runtime_health, sync_runtime_health
from .setup import build_setup_flow, determine_setup_status, persist_setup_completion

__all__ = [
    "RuntimeHealth",
    "build_setup_flow",
    "collect_runtime_health",
    "determine_setup_status",
    "persist_setup_completion",
    "sync_runtime_health",
]
