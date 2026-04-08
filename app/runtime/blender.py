"""Local Blender detection and verification for the desktop runtime."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from app.blender_runner import DEFAULT_BLENDER_PATH
from app.llm_client import load_dotenv_values


def get_configured_blender_path() -> Path:
    """Resolve Blender from env configuration or the default example path."""
    env_values = load_dotenv_values()
    configured_path = os.getenv("BLENDER_PATH") or env_values.get("BLENDER_PATH") or DEFAULT_BLENDER_PATH
    return Path(configured_path)


def _candidate_blender_paths() -> list[Path]:
    configured = get_configured_blender_path()
    program_files = Path(os.getenv("ProgramFiles", r"C:\Program Files"))
    candidates = [configured]
    blender_root = program_files / "Blender Foundation"
    if blender_root.exists():
        candidates.extend(sorted(blender_root.glob("Blender*\\blender.exe"), reverse=True))
    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def detect_blender_path() -> dict[str, Any]:
    """Detect a Blender executable on the local machine."""
    configured = get_configured_blender_path()
    if configured.exists():
        return {
            "detected": True,
            "path": str(configured),
            "source": "configured",
        }

    for candidate in _candidate_blender_paths():
        if candidate.exists():
            source = "configured" if candidate == configured else "common_windows_path"
            return {
                "detected": True,
                "path": str(candidate),
                "source": source,
            }

    return {
        "detected": False,
        "path": str(configured),
        "source": "not_found",
    }


def verify_blender_callable(blender_path: str | Path | None = None, timeout: int = 20) -> tuple[bool, str]:
    """Verify that the Blender executable can be invoked."""
    detected = detect_blender_path() if blender_path is None else {"detected": True, "path": str(blender_path)}
    path_text = str(detected.get("path", "")).strip()
    if not path_text:
        return False, "No Blender executable path is configured."

    path = Path(path_text)
    if not path.exists():
        return False, f"Blender executable was not found at {path}."

    try:
        result = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"Blender did not respond to --version within {timeout} seconds."
    except OSError as error:
        return False, f"Blender could not be launched from {path}. Details: {error}"

    if result.returncode != 0:
        stderr_text = result.stderr.strip() or result.stdout.strip() or "No output returned."
        return False, f"Blender returned exit code {result.returncode}. Details: {stderr_text}"

    first_line = (result.stdout.strip() or result.stderr.strip() or "Blender callable check succeeded.").splitlines()[0]
    return True, first_line


def run_health_check() -> dict[str, Any]:
    """Return a structured Blender runtime health payload."""
    detected = detect_blender_path()
    callable_ok, message = verify_blender_callable(detected["path"]) if detected["detected"] else (
        False,
        f"Blender was not found. Expected path: {detected['path']}",
    )
    status = "ready" if detected["detected"] and callable_ok else "missing"
    return {
        "status": status,
        "message": message,
        "detected": bool(detected["detected"]),
        "path": detected["path"],
        "callable": callable_ok,
        "source": detected.get("source", ""),
    }
