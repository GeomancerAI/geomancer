"""Helpers for running Blender with a generated Python script."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

# Update this path if Blender is installed somewhere else on your system.
DEFAULT_BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"


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


def get_blender_path() -> Path:
    """Resolve Blender's executable path from env vars or the default example."""
    env_values = load_dotenv_values()
    configured_path = os.getenv("BLENDER_PATH") or env_values.get("BLENDER_PATH") or DEFAULT_BLENDER_PATH
    return Path(configured_path)


def run_generated_script(script_path: Path, interactive: bool = True) -> tuple[bool, str]:
    """Run Blender and execute the given Python script."""
    blender_path = get_blender_path()
    script_path = Path(script_path)
    mode_text = "interactive" if interactive else "background"
    print(f"Using Blender path: {blender_path}")
    print(f"Using Blender mode: {mode_text}")

    if not blender_path.exists():
        return False, (
            f"Blender was not found at: {blender_path}. "
            "Create or update a .env file in the project root with "
            r"BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
        )

    if not script_path.exists():
        return False, f"Generated script not found at: {script_path}"

    command = [str(blender_path)]
    if not interactive:
        command.append("--background")
    command.extend(["--python", str(script_path)])

    try:
        if interactive:
            process = subprocess.Popen(command)
            print("Blender launched in interactive mode. Close Blender to return to Geomancer.")
            return_code = process.wait()
            if return_code != 0:
                return False, f"Blender exited with code {return_code} in interactive mode."
            return True, "Blender session ended."

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return False, f"Blender run failed after timing out at 300 seconds. Script: {script_path}"
    except OSError as error:
        return False, f"Blender could not be started from {blender_path}. Details: {error}"

    if result.returncode != 0:
        stderr_text = result.stderr.strip() or "No stderr output was returned."
        return False, (
            f"Blender failed with exit code {result.returncode} while running {script_path}. "
            f"Details: {stderr_text}"
        )

    return True, f"Blender completed successfully in {mode_text} mode using {blender_path}."
