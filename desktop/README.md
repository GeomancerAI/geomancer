# Geomancer Desktop Alpha

This directory contains the current desktop-facing alpha shell for Geomancer. It is not a separate product line from the Python backend. Its purpose is to wrap the existing backend pipeline in a native desktop window, expose controlled bridge operations to the UI layer, and create a stable surface for future product iteration.

## Current Role In The Architecture

- `desktop/` is the intended product direction for Geomancer.
- `app/` remains the source of truth for generation, Blender execution, and persisted backend state.
- `app/backend/` now contains the deterministic alpha-family backend pipeline used by both terminal and desktop flows.
- The desktop shell is currently a thin integration layer, not a backend replacement.
- During the current backend-first phase, desktop work should prefer stabilizing contracts and observability over broad UI expansion.

## Current Files

- `main.py`: desktop entrypoint
- `shell.py`: Qt main window and WebEngine host
- `bridge.py`: JS-to-Python bridge surface
- `backend_controller.py`: thin adapter over the existing backend pipeline
- `ui/`: HTML, CSS, JavaScript, and bundled viewer dependencies for the desktop shell

The backend result flow now centers on:

- family classification
- normalized plan output
- validation/reporting metadata
- generated script path
- preview export path/status

The desktop shell now consumes those backend outputs directly for:

- prompt and family history
- normalized parameter summaries
- validation/readiness messaging
- preview model path handoff to the viewer

## Run

```powershell
python -m desktop.main
```

## Alpha Notes

- The desktop shell is still alpha scaffolding.
- The terminal workflow in `app/chat_agent.py` remains useful for direct backend testing.
- The Tkinter dev console in `app/dev_console.py` remains available as a legacy developer tool.
- The current backend is deterministic by supported alpha family and no longer depends on a freeform prompt-to-code path for core generation.
- Future passes in this folder should document bridge changes, controller changes, and UI contract changes explicitly in the root `CHANGELOG.md`.

## Review Expectations For Future Passes

When work touches `desktop/`, document:

- the milestone or version label
- exact files changed
- bridge or controller contract changes
- incomplete UI/backend integration areas
- rollback notes if the pass changes desktop startup or backend invocation behavior
