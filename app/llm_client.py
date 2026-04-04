"""Small Ollama HTTP client for local text generation."""

from __future__ import annotations

import json
import os
import socket
from pathlib import Path
from typing import Any
from urllib import error, request


DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
DEFAULT_TIMEOUT_SECONDS = 300
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class OllamaClientError(Exception):
    """Raised when a local Ollama request fails."""


def load_dotenv_values() -> dict[str, str]:
    """Load simple KEY=VALUE pairs from a local .env file if it exists."""
    values: dict[str, str] = {}

    if not ENV_FILE_PATH.exists():
        return values

    for raw_line in ENV_FILE_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


class OllamaClient:
    """Minimal client around Ollama's /api/generate endpoint."""

    def __init__(self, url: str | None = None, model_name: str | None = None, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        env_values = load_dotenv_values()
        self.url = url or os.getenv("OLLAMA_URL") or env_values.get("OLLAMA_URL") or DEFAULT_OLLAMA_URL
        self.model_name = model_name or os.getenv("OLLAMA_MODEL") or env_values.get("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL
        self.timeout = timeout

    def generate(self, prompt_text: str, format_schema: dict[str, Any] | str | None = None) -> str:
        """Send the prompt to Ollama and return the raw text response."""
        payload: dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt_text,
            "stream": False,
            "keep_alive": -1,
        }
        if format_schema is not None:
            payload["format"] = format_schema

        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            self.url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as http_error:
            message = http_error.read().decode("utf-8", errors="replace")
            raise OllamaClientError(f"HTTP {http_error.code} from Ollama: {message}") from http_error
        except error.URLError as url_error:
            reason = getattr(url_error, "reason", url_error)
            if isinstance(reason, ConnectionRefusedError):
                reason_text = "Connection refused. Start Ollama and make sure it is listening on port 11434."
            else:
                reason_text = str(reason)
            raise OllamaClientError(
                f"Could not connect to Ollama at {self.url}. "
                f"Make sure Ollama is running locally. Details: {reason_text}"
            ) from url_error
        except socket.timeout as timeout_error:
            raise OllamaClientError(
                f"Ollama request timed out after {self.timeout} seconds. "
                "Try a shorter prompt, make sure the model is already warmed up, "
                "and check Ollama logs if needed."
            ) from timeout_error

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as decode_error:
            raise OllamaClientError("Ollama returned invalid JSON.") from decode_error

        response_text = data.get("response", "")
        if not response_text.strip():
            raise OllamaClientError("Ollama returned an empty response.")

        return response_text

    def generate_streaming(self, prompt_text: str, format_schema: dict[str, Any] | str | None = None) -> str:
        """Send the prompt to Ollama and return the full response while streaming chunks."""
        payload: dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt_text,
            "stream": True,
            "keep_alive": -1,
        }
        if format_schema is not None:
            payload["format"] = format_schema

        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            self.url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        collected: list[str] = []
        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                print("Receiving code stream...", flush=True)
                for raw_line in response:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    chunk = data.get("response", "")
                    if chunk:
                        collected.append(chunk)
                        print(".", end="", flush=True)
        except error.HTTPError as http_error:
            message = http_error.read().decode("utf-8", errors="replace")
            raise OllamaClientError(f"HTTP {http_error.code} from Ollama: {message}") from http_error
        except error.URLError as url_error:
            reason = getattr(url_error, "reason", url_error)
            if isinstance(reason, ConnectionRefusedError):
                reason_text = "Connection refused. Start Ollama and make sure it is listening on port 11434."
            else:
                reason_text = str(reason)
            raise OllamaClientError(
                f"Could not connect to Ollama at {self.url}. "
                f"Make sure Ollama is running locally. Details: {reason_text}"
            ) from url_error
        except socket.timeout as timeout_error:
            raise OllamaClientError(
                f"Ollama request timed out after {self.timeout} seconds. "
                "Try a shorter prompt, make sure the model is already warmed up, "
                "and check Ollama logs if needed."
            ) from timeout_error

        print("", flush=True)
        response_text = "".join(collected).strip()
        if not response_text:
            raise OllamaClientError("Ollama returned an empty response.")
        return response_text
