# Geomancer

Geomancer is a local-first AI 3D modeling project evolving toward a desktop application that pairs a Python backend with a native desktop shell and a web-based UI layer. The current repository still contains the original terminal workflow and a lightweight Tkinter dev console, but active development is now backend-first so the generation pipeline, state handling, Blender execution flow, and desktop integration points can stabilize before broader UI expansion.

## Current Status

- Project status: `alpha`
- Current version: `0.6.0-alpha`
- Current milestone: `desktop-core-loop-stabilization`
- Primary product direction: desktop app built around the existing Python generation pipeline
- Current development emphasis: backend-first refactors, integration hardening, and documentation discipline

The current alpha state should be treated as an actively changing foundation rather than a feature-complete product. Existing interfaces are useful for development and testing, but they are not yet the long-term final UX.

## Development Direction

Geomancer currently spans three active surfaces:

- `app/`: core Python backend pipeline for prompt handling, Ollama calls, code extraction, state, and Blender execution
- `app/backend/`: deterministic alpha-family pipeline for classification, normalization, generation, validation, and reporting
- `desktop/`: desktop alpha shell that wraps the Python backend and hosts the future product UI
- `docs/`: static site and marketing/support pages, not the authoritative source for backend architecture

The immediate priority is backend-first development. That means future passes should optimize for:

- backend correctness and reversibility
- explicit version and milestone tracking
- well-scoped refactors with file-level review notes
- documenting limitations before broadening feature scope

## Change Tracking Standard

Project change tracking is standardized through:

- `VERSION`: single current project version string
- `CHANGELOG.md`: milestone history and Codex pass documentation format
- repository and subfolder READMEs: current architecture and development-phase notes

Before or alongside meaningful backend work, each Codex pass should leave behind documentation that includes:

1. version or milestone label
2. exact files changed
3. summary of changes
4. known limitations or incomplete parts
5. rollback or review notes when relevant

Use the format defined in `CHANGELOG.md` for future passes.

## Project Structure

```text
geomancer/
  app/
    backend/
    blender_runner.py
    chat_agent.py
    code_utils.py
    dev_console.py
    llm_client.py
    prompt_builder.py
    state.py
  blender/
    generated_model.py
    rules/
    templates/
  data/
    session_state.json
  desktop/
    backend_controller.py
    bridge.py
    main.py
    shell.py
    ui/
  docs/
  tests/
  CHANGELOG.md
  README.md
  VERSION
  requirements.txt
```

## What Geomancer Does Today

1. Accepts a plain-English modeling request.
2. Classifies the request into an explicit supported alpha family.
3. Extracts and normalizes dimensions and family-specific parameters.
4. Builds deterministic Blender Python for the selected family recipe.
5. Saves the generated script to `blender/generated_model.py`.
6. Exports a preview model for the desktop viewer when Blender is available.
7. Persists session state plus validation/reporting metadata for follow-up tooling and desktop status reporting.

## Deterministic Alpha Backend

The current backend is structured around these modules:

- `app/backend/families.py`: explicit supported alpha families and aliases
- `app/backend/classifier.py`: family-based request classification
- `app/backend/normalizer.py`: parameter extraction and normalization
- `app/backend/geometry.py`: deterministic Blender script generation by family recipe
- `app/backend/validation.py`: review-friendly validation and reporting
- `app/backend/pipeline.py`: orchestration, preview export, and state updates

Supported alpha families:

- enclosure
- bracket
- cable clip
- planter / vessel
- gear
- adapter
- panel / plate
- spacer / standoff
- tray / box
- simple hook / mount
- simple housing / mechanical shell
- dimensional primitive/blockout assemblies

Current strongest golden-path families:

- panel / plate
- spacer / standoff
- enclosure
- tray / box
- bracket
- adapter
- cable clip
- simple hook / mount

## Active Entry Points

- Terminal workflow: `python app/chat_agent.py`
- Dev console: `python app/dev_console.py`
- Desktop alpha shell: `python -m desktop.main`

The terminal and dev console remain valid development tools, but the desktop shell is the intended product direction.

## Requirements

- Windows
- Python 3.10 or newer
- Blender installed locally
- Ollama is optional for legacy/local experiments and is not required for the deterministic alpha-family pipeline

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file in the project root to override defaults when needed:

```text
BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 5.0\blender.exe
```

## Blender and Ollama Notes

- Background mode runs Blender with `--background --python blender/generated_model.py`.
- Interactive mode runs Blender with `--python blender/generated_model.py`.
- Interactive mode is usually the better development loop because the Blender UI opens immediately.
- Preview export also runs through Blender in background mode.
- The old Ollama prompt pipeline remains in the repo only as legacy support code during the backend transition.

## Current Alpha Constraints

- Generated models are still rough primitive-based blockouts.
- Outputs may require manual cleanup before printing or production use.
- The Blender API surface is intentionally constrained through the rule files in `blender/rules/`.
- Family recipes are explicit and deterministic, which means complex geometry requests may be rejected or simplified.
- UI surfaces are still transitional and should not be treated as final product design.
- Backend contracts may continue to change during the backend-first phase, so change tracking is mandatory for reviewability.

## Blender Rule Library

Geomancer uses a focused local Blender rule library in `blender/rules/`:

- `blender_api_rules.md`
- `allowed_operators.json`
- `banned_patterns.json`
- `modeling_conventions.md`

These files define the conservative `bpy` subset and modeling conventions the generator should follow.

## Commands

Terminal mode currently supports:

- `/help`
- `/quit`
- `/run`
- `/show`
- `/save`
- `/last`

## Generated Outputs

- Active generated script: `blender/generated_model.py`
- Session state: `data/session_state.json`

## Documentation Notes

- `README.md` is the top-level source of truth for project status and development direction.
- `desktop/README.md` describes the desktop alpha shell and its relationship to the backend.
- `docs/README.md` describes the static site folder and clarifies that it is not the architecture source of truth.
- `CHANGELOG.md` is the required ledger for versioned changes and future backend pass summaries.
