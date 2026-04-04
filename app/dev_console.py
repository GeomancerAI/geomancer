"""Lightweight local Tkinter dev console for Geomancer."""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from tkinter import BooleanVar, PhotoImage, StringVar, Text, Tk, ttk, messagebox

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from blender_runner import run_generated_script
from chat_agent import GENERATED_SCRIPT_PATH, generate_model_request, load_version, update_run_status
from llm_client import OllamaClient, OllamaClientError


PROJECT_ROOT = APP_DIR.parent
DEFAULT_LOGO_PATH = Path(r"c:\Users\Studl\Downloads\83df502d-c211-4d34-af03-fe0ba80cd77f.png")


class DevConsole:
    """Small local GUI for testing Geomancer without replacing terminal mode."""

    def __init__(self) -> None:
        self.version = load_version()
        self.client = OllamaClient()
        self.root = Tk()
        self.root.title(f"Geomancer Dev Console v{self.version}")
        self.root.geometry("1040x860")
        self.root.configure(bg="#f5f8fb")

        self.prompt_var = StringVar()
        self.script_path_var = StringVar(value=str(GENERATED_SCRIPT_PATH))
        self.launch_blender_var = BooleanVar(value=False)
        self.plan_text: Text
        self.log_text: Text
        self.run_button: ttk.Button
        self.logo_image = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the Tkinter interface."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Geomancer.TFrame", background="#f5f8fb")
        style.configure("Geomancer.TLabel", background="#f5f8fb", foreground="#2a3f5f")
        style.configure("Geomancer.TButton", padding=8)

        container = ttk.Frame(self.root, style="Geomancer.TFrame", padding=18)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=2)
        container.rowconfigure(3, weight=1)

        hero = ttk.Frame(container, style="Geomancer.TFrame")
        hero.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        if DEFAULT_LOGO_PATH.exists():
            try:
                image = PhotoImage(file=str(DEFAULT_LOGO_PATH))
                self.logo_image = image.subsample(3, 3)
                ttk.Label(hero, image=self.logo_image, style="Geomancer.TLabel").pack()
            except Exception:
                ttk.Label(hero, text="GEOMANCER", style="Geomancer.TLabel", font=("Segoe UI", 30, "bold")).pack()
        else:
            ttk.Label(hero, text="GEOMANCER", style="Geomancer.TLabel", font=("Segoe UI", 30, "bold")).pack()

        ttk.Label(
            hero,
            text=f"Geomancer Dev Console v{self.version}",
            style="Geomancer.TLabel",
            font=("Segoe UI", 13, "bold"),
        ).pack(pady=(6, 0))

        prompt_frame = ttk.Frame(container, style="Geomancer.TFrame")
        prompt_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        prompt_frame.columnconfigure(0, weight=1)

        ttk.Label(prompt_frame, text="Prompt", style="Geomancer.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
        prompt_entry = ttk.Entry(prompt_frame, textvariable=self.prompt_var, font=("Segoe UI", 11))
        prompt_entry.grid(row=1, column=0, sticky="ew", padx=(0, 12))
        prompt_entry.bind("<Return>", lambda _event: self.start_run())

        self.run_button = ttk.Button(prompt_frame, text="Run", style="Geomancer.TButton", command=self.start_run)
        self.run_button.grid(row=1, column=1, sticky="e")

        ttk.Checkbutton(
            prompt_frame,
            text="Launch Blender after generation",
            variable=self.launch_blender_var,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))

        left_panel = ttk.Frame(container, style="Geomancer.TFrame")
        left_panel.grid(row=2, column=0, rowspan=2, sticky="nsew", padx=(0, 14))
        left_panel.rowconfigure(1, weight=1)
        left_panel.columnconfigure(0, weight=1)

        ttk.Label(left_panel, text="Output Log", style="Geomancer.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
        log_frame = ttk.Frame(left_panel, style="Geomancer.TFrame")
        log_frame.grid(row=1, column=0, sticky="nsew")
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        self.log_text = Text(log_frame, wrap="word", font=("Consolas", 10), bg="#ffffff", fg="#1d2a3a", height=22)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        right_panel = ttk.Frame(container, style="Geomancer.TFrame")
        right_panel.grid(row=2, column=1, rowspan=2, sticky="nsew")
        right_panel.rowconfigure(1, weight=1)
        right_panel.columnconfigure(0, weight=1)

        ttk.Label(right_panel, text="Last Parsed Plan", style="Geomancer.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
        plan_frame = ttk.Frame(right_panel, style="Geomancer.TFrame")
        plan_frame.grid(row=1, column=0, sticky="nsew")
        plan_frame.rowconfigure(0, weight=1)
        plan_frame.columnconfigure(0, weight=1)
        self.plan_text = Text(plan_frame, wrap="word", font=("Consolas", 10), bg="#ffffff", fg="#1d2a3a", height=12)
        self.plan_text.grid(row=0, column=0, sticky="nsew")
        plan_scrollbar = ttk.Scrollbar(plan_frame, orient="vertical", command=self.plan_text.yview)
        plan_scrollbar.grid(row=0, column=1, sticky="ns")
        self.plan_text.configure(yscrollcommand=plan_scrollbar.set)

        ttk.Label(right_panel, text="Generated Script Path", style="Geomancer.TLabel", font=("Segoe UI", 11, "bold")).grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Label(
            right_panel,
            textvariable=self.script_path_var,
            style="Geomancer.TLabel",
            font=("Consolas", 10),
            wraplength=320,
            justify="left",
        ).grid(row=3, column=0, sticky="ew", pady=(4, 0))

    def append_log(self, message: str) -> None:
        """Append a line to the output log."""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")

    def set_plan(self, plan: dict | None) -> None:
        """Update the plan display."""
        self.plan_text.delete("1.0", "end")
        if plan:
            self.plan_text.insert("1.0", json.dumps(plan, indent=2))

    def start_run(self) -> None:
        """Start a generation run in a background thread."""
        prompt = self.prompt_var.get().strip()
        if not prompt:
            messagebox.showinfo("Geomancer", "Enter a prompt first.")
            return

        self.run_button.configure(state="disabled")
        self.append_log(f"> {prompt}")
        self.set_plan(None)

        worker = threading.Thread(target=self._run_request, args=(prompt,), daemon=True)
        worker.start()

    def _run_request(self, prompt: str) -> None:
        """Run the generation request off the UI thread."""
        def log(message: str) -> None:
            self.root.after(0, lambda msg=message: self.append_log(msg))

        try:
            result = generate_model_request(prompt, self.client, log=log, show_spinner=False)
            if result.get("status") == "ready":
                plan = result.get("plan")
                script_path = result.get("script_path", str(GENERATED_SCRIPT_PATH))
                self.root.after(0, lambda: self.set_plan(plan))
                self.root.after(0, lambda: self.script_path_var.set(script_path))

                if self.launch_blender_var.get():
                    success, message = run_generated_script(Path(script_path), interactive=True)
                    update_run_status(message if success else f"failed: {message}")
                    log(message)
            else:
                self.root.after(0, lambda: self.script_path_var.set(str(GENERATED_SCRIPT_PATH)))
        except OllamaClientError as error:
            self.root.after(0, lambda: self.append_log(f"Ollama error: {error}"))
        except Exception as error:  # pragma: no cover - GUI guard
            self.root.after(0, lambda: self.append_log(f"Unexpected error: {error}"))
        finally:
            self.root.after(0, lambda: self.run_button.configure(state="normal"))

    def run(self) -> None:
        """Start the Tkinter main loop."""
        self.root.mainloop()


def main() -> int:
    """Run the Geomancer dev console."""
    DevConsole().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
