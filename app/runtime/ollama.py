"""Local Ollama detection, health checks, and model management."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any, Callable
from urllib import error, request

from app.llm_client import load_dotenv_values

from .models import ALL_RECOMMENDED_MODEL_NAMES, RECOMMENDED_OLLAMA_MODEL


ProgressCallback = Callable[[dict[str, Any]], None]
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_TIMEOUT_SECONDS = 10


def get_ollama_base_url() -> str:
    """Resolve the local Ollama base URL from env or defaults."""
    env_values = load_dotenv_values()
    configured = (
        os.getenv("OLLAMA_BASE_URL")
        or os.getenv("OLLAMA_HOST")
        or env_values.get("OLLAMA_BASE_URL")
        or env_values.get("OLLAMA_HOST")
        or env_values.get("OLLAMA_URL")
    )
    if configured:
        return configured.rstrip("/")

    legacy_url = os.getenv("OLLAMA_URL")
    if legacy_url:
        if legacy_url.endswith("/api/generate"):
            return legacy_url[: -len("/api/generate")]
        return legacy_url.rstrip("/")

    return DEFAULT_OLLAMA_HOST


def _common_ollama_install_paths() -> list[Path]:
    local_app_data = os.getenv("LOCALAPPDATA", "")
    program_files = os.getenv("ProgramFiles", r"C:\Program Files")
    candidates = [
        Path(local_app_data) / "Programs" / "Ollama" / "ollama.exe",
        Path(program_files) / "Ollama" / "ollama.exe",
    ]
    return [candidate for candidate in candidates if str(candidate).strip()]


def detect_ollama_install() -> dict[str, Any]:
    """Detect whether the Ollama executable is installed locally."""
    discovered = shutil.which("ollama")
    if discovered:
        version = _read_ollama_binary_version(Path(discovered))
        return {
            "installed": True,
            "path": discovered,
            "version": version,
            "source": "PATH",
        }

    for candidate in _common_ollama_install_paths():
        if candidate.exists():
            version = _read_ollama_binary_version(candidate)
            return {
                "installed": True,
                "path": str(candidate),
                "version": version,
                "source": "common_windows_path",
            }

    return {
        "installed": False,
        "path": "",
        "version": "",
        "source": "not_found",
    }


def _read_ollama_binary_version(binary_path: Path) -> str:
    try:
        result = subprocess.run(
            [str(binary_path), "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""

    return (result.stdout or result.stderr).strip()


def _api_request(
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
):
    url = f"{get_ollama_base_url()}{path}"
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    http_request = request.Request(url, data=body, headers=headers, method=method)
    return request.urlopen(http_request, timeout=timeout)


def detect_ollama_reachability(timeout: int = 3) -> dict[str, Any]:
    """Check whether the local Ollama HTTP server is reachable."""
    try:
        with _api_request("/api/version", timeout=timeout) as response:
            raw = response.read().decode("utf-8")
        payload = json.loads(raw)
        version = str(payload.get("version", "")).strip()
        return {
            "running": True,
            "version": version,
            "message": f"Ollama is reachable at {get_ollama_base_url()}.",
        }
    except error.HTTPError as http_error:
        detail = http_error.read().decode("utf-8", errors="replace")
        return {
            "running": False,
            "version": "",
            "message": f"Ollama responded with HTTP {http_error.code}: {detail}",
        }
    except error.URLError as url_error:
        reason = getattr(url_error, "reason", url_error)
        return {
            "running": False,
            "version": "",
            "message": f"Could not reach Ollama at {get_ollama_base_url()}: {reason}",
        }
    except socket.timeout:
        return {
            "running": False,
            "version": "",
            "message": f"Ollama health check timed out at {get_ollama_base_url()}.",
        }


def list_local_models(timeout: int = DEFAULT_TIMEOUT_SECONDS) -> list[dict[str, Any]]:
    """Return locally available Ollama models."""
    try:
        with _api_request("/api/tags", timeout=timeout) as response:
            raw = response.read().decode("utf-8")
        payload = json.loads(raw)
    except (error.URLError, error.HTTPError, socket.timeout, json.JSONDecodeError):
        return []

    models = payload.get("models", [])
    return models if isinstance(models, list) else []


def is_model_ready(model_name: str, models: list[dict[str, Any]] | None = None) -> bool:
    """Return True when the requested Ollama model exists locally."""
    if not model_name:
        return False
    available_models = models if models is not None else list_local_models()
    model_names = {
        str(model.get("name", "")).strip()
        for model in available_models
        if isinstance(model, dict)
    }
    return model_name in model_names


def pull_model(
    model_name: str,
    *,
    progress_callback: ProgressCallback | None = None,
    timeout: int = 1800,
) -> dict[str, Any]:
    """Pull an Ollama model and stream progress updates."""
    if not model_name:
        raise ValueError("model_name is required for pull_model().")

    callback = progress_callback or (lambda _event: None)
    last_event: dict[str, Any] = {
        "status": "starting",
        "model": model_name,
        "completed": 0,
        "total": 0,
        "done": False,
    }
    callback(last_event)

    try:
        with _api_request(
            "/api/pull",
            method="POST",
            payload={"name": model_name, "stream": True},
            timeout=timeout,
        ) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                event.setdefault("model", model_name)
                last_event = event
                callback(event)
    except error.HTTPError as http_error:
        detail = http_error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama model pull failed with HTTP {http_error.code}: {detail}") from http_error
    except error.URLError as url_error:
        reason = getattr(url_error, "reason", url_error)
        raise RuntimeError(f"Could not connect to Ollama for model pull: {reason}") from url_error
    except socket.timeout as timeout_error:
        raise RuntimeError(f"Ollama model pull timed out after {timeout} seconds.") from timeout_error

    return {
        "model_name": model_name,
        "done": bool(last_event.get("done", False)),
        "status": str(last_event.get("status", "completed")),
        "digest": str(last_event.get("digest", "")),
        "total": int(last_event.get("total") or 0),
        "completed": int(last_event.get("completed") or 0),
        "recommended_models": list(ALL_RECOMMENDED_MODEL_NAMES),
    }


def run_health_check(model_name: str | None = None) -> dict[str, Any]:
    """Return a structured Ollama runtime health payload."""
    install = detect_ollama_install()
    reachability = detect_ollama_reachability()
    preferred_model = model_name or RECOMMENDED_OLLAMA_MODEL.name
    models = list_local_models() if reachability["running"] else []
    ready = is_model_ready(preferred_model, models=models)
    available_model_names = [
        str(model.get("name", "")).strip()
        for model in models
        if isinstance(model, dict) and model.get("name")
    ]

    if not install["installed"]:
        status = "missing"
        message = "Install Ollama locally to enable prompt interpretation."
    elif not reachability["running"]:
        status = "offline"
        message = reachability["message"]
    elif not ready:
        status = "model_missing"
        message = f"Ollama is running, but the required model '{preferred_model}' is not available yet."
    else:
        status = "ready"
        message = f"Ollama is running and model '{preferred_model}' is ready."

    return {
        "status": status,
        "message": message,
        "installed": bool(install["installed"]),
        "install_path": install["path"],
        "running": bool(reachability["running"]),
        "version": reachability["version"] or install["version"],
        "model_name": preferred_model,
        "model_ready": ready,
        "available_models": available_model_names,
        "recommended_model": RECOMMENDED_OLLAMA_MODEL.name,
    }


def run_smoke_test(model_name: str, timeout: int = 45) -> dict[str, Any]:
    """Run a minimal generate call against Ollama to validate the setup."""
    if not model_name:
        return {"ok": False, "message": "No Ollama model name is configured for the smoke test."}

    payload = {
        "model": model_name,
        "prompt": "Reply with only the word OK.",
        "stream": False,
        "options": {"temperature": 0, "num_predict": 4},
    }

    try:
        with _api_request("/api/generate", method="POST", payload=payload, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
        data = json.loads(raw)
    except error.HTTPError as http_error:
        detail = http_error.read().decode("utf-8", errors="replace")
        return {"ok": False, "message": f"Ollama smoke test failed with HTTP {http_error.code}: {detail}"}
    except error.URLError as url_error:
        reason = getattr(url_error, "reason", url_error)
        return {"ok": False, "message": f"Ollama smoke test could not reach the local server: {reason}"}
    except (socket.timeout, json.JSONDecodeError) as error_obj:
        return {"ok": False, "message": f"Ollama smoke test failed: {error_obj}"}

    response_text = str(data.get("response", "")).strip()
    if not response_text:
        return {"ok": False, "message": "Ollama smoke test returned an empty response."}

    return {
        "ok": True,
        "message": f"Ollama smoke test succeeded with model '{model_name}'.",
        "response": response_text,
    }
