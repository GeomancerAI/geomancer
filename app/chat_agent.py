"""Terminal chat loop for the current deterministic Geomancer backend."""

from __future__ import annotations

import shutil
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

try:
    from app.backend.classifier import classify_request as backend_classify_request
    from app.backend.runtime import GENERATED_SCRIPT_PATH
    from app.backend.pipeline import generate_model_request as backend_generate_model_request
    from app.backend.versioning import load_version as load_project_version
    from app.blender_runner import run_generated_script
    from app.llm_client import OllamaClient, OllamaClientError
    from app.state import load_state, save_state
except ImportError:
    from backend.classifier import classify_request as backend_classify_request
    from backend.runtime import GENERATED_SCRIPT_PATH
    from backend.pipeline import generate_model_request as backend_generate_model_request
    from backend.versioning import load_version as load_project_version
    from blender_runner import run_generated_script
    from llm_client import OllamaClient, OllamaClientError
    from state import load_state, save_state


HELP_TEXT = """Geomancer commands:
/help  - Show available commands
/quit  - Exit the program
/run   - Run the last generated Blender script
/show  - Print the current generated Blender script
/save  - Save a timestamped copy of the current generated script
/last  - Show the last request and generation status

Any normal text will be treated as a new 3D model request.
"""


def load_version() -> str:
    """Load the current project version."""
    return load_project_version()


def print_help() -> None:
    """Display command help."""
    print(HELP_TEXT)


def show_last_state() -> None:
    """Display the last saved session state in a readable format."""
    state = load_state()
    print("Last user request:", state.get("last_user_request") or "None")
    print("Last family:", state.get("last_generation_family") or "None")
    print("Last generated script path:", state.get("last_generated_script_path") or "None")
    print("Last validation summary:", state.get("last_validation_summary") or "None")
    print("Last run status:", state.get("last_run_status") or "None")


def show_generated_script() -> None:
    """Print the current generated Blender script."""
    if not GENERATED_SCRIPT_PATH.exists():
        print(f"No generated script found at: {GENERATED_SCRIPT_PATH}")
        return

    print(f"\n--- {GENERATED_SCRIPT_PATH} ---")
    print(GENERATED_SCRIPT_PATH.read_text(encoding="utf-8"))
    print("--- end script ---\n")


def save_timestamped_copy() -> None:
    """Save a timestamped copy of the current generated script for reference."""
    if not GENERATED_SCRIPT_PATH.exists():
        print("No generated script exists yet.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = GENERATED_SCRIPT_PATH.parent / f"generated_model_{timestamp}.py"
    shutil.copyfile(GENERATED_SCRIPT_PATH, archive_path)
    print(f"Saved a copy to: {archive_path}")


def update_run_status(status_text: str) -> None:
    """Update only the run status in session state."""
    state = load_state()
    state["last_run_status"] = status_text
    save_state(state)


def prompt_yes_no(message: str) -> bool:
    """Ask a simple yes/no question and return True for yes."""
    while True:
        answer = input(message).strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no", ""}:
            return False
        print("Please answer with yes or no.")


def prompt_yes_no_default_yes(message: str) -> bool:
    """Ask a simple yes/no question and return True for yes, defaulting to yes."""
    while True:
        answer = input(message).strip().lower()
        if answer in {"", "y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer with yes or no.")


def classify_request(user_request: str) -> tuple[str, str]:
    """Backward-compatible terminal classifier wrapper."""
    result = backend_classify_request(user_request)
    return result.status, result.message


def run_with_spinner(action_text: str, func, *args, **kwargs):
    """Run a blocking function while showing a lightweight terminal spinner."""
    stop_event = threading.Event()

    def spinner_worker() -> None:
        frames = "|/-\\"
        index = 0
        while not stop_event.is_set():
            frame = frames[index % len(frames)]
            print(f"\r{action_text} {frame}", end="", flush=True)
            time.sleep(0.15)
            index += 1
        print(f"\r{action_text} done.", flush=True)

    spinner_thread = threading.Thread(target=spinner_worker, daemon=True)
    spinner_thread.start()
    try:
        return func(*args, **kwargs)
    finally:
        stop_event.set()
        spinner_thread.join()


def generate_model_request(user_request: str, client: OllamaClient, log=print, show_spinner: bool = True) -> dict:
    """Generate a model request and return structured results for terminal or GUI use."""
    if show_spinner:
        return run_with_spinner(
            "Building deterministic alpha-family model...",
            backend_generate_model_request,
            user_request,
            client,
            log,
            show_spinner,
        )
    return backend_generate_model_request(user_request, client, log=log, show_spinner=show_spinner)


def handle_generation_request(user_request: str, client: OllamaClient) -> None:
    """Generate Blender Python code from a user's plain-English request."""
    result = generate_model_request(user_request, client, log=print)
    if result.get("status") != "ready":
        return

    if prompt_yes_no("Run this script in Blender now? [y/N]: "):
        interactive = prompt_yes_no_default_yes("Run in interactive mode (open Blender UI)? [Y/n]: ")
        success, message = run_generated_script(GENERATED_SCRIPT_PATH, interactive=interactive)
        update_run_status(message if success else f"failed: {message}")
        print(message)
    else:
        print("Skipped Blender run.")


def run_last_script() -> None:
    """Run the most recently generated Blender script."""
    state = load_state()
    script_path_text = state.get("last_generated_script_path")
    script_path = Path(script_path_text) if script_path_text else GENERATED_SCRIPT_PATH

    if not script_path.exists():
        print(f"No script found to run at: {script_path}")
        update_run_status("failed: no script to run")
        return

    interactive = prompt_yes_no_default_yes("Run in interactive mode (open Blender UI)? [Y/n]: ")
    success, message = run_generated_script(script_path, interactive=interactive)
    update_run_status(message if success else f"failed: {message}")
    print(message)


def main() -> int:
    """Run the terminal chat loop."""
    print(f"Geomancer v{load_version()}")
    print("Type /help for commands.")

    client = OllamaClient()

    while True:
        try:
            user_input = input("Geomancer> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Geomancer.")
            return 0

        if not user_input:
            continue

        if user_input == "/help":
            print_help()
            continue

        if user_input == "/quit":
            print("Exiting Geomancer.")
            return 0

        if user_input == "/run":
            run_last_script()
            continue

        if user_input == "/show":
            show_generated_script()
            continue

        if user_input == "/save":
            save_timestamped_copy()
            continue

        if user_input == "/last":
            show_last_state()
            continue

        try:
            handle_generation_request(user_input, client)
        except OllamaClientError as error:
            print(f"Ollama error: {error}")
        except Exception as error:  # pragma: no cover - last-resort terminal guard
            print(f"Unexpected error: {error}")


if __name__ == "__main__":
    sys.exit(main())
