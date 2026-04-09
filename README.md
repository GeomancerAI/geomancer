# Geomancer

Geomancer is a local-first desktop geometry tool. Local AI interprets requests, Geomancer owns deterministic geometry generation, and Blender remains the local preview and editing target.

## Current Status

- Version: `0.7.27-alpha`
- Stage: `alpha`
- Product direction: desktop shell -> local setup -> deterministic geometry pipeline -> Blender handoff
- Core rule: AI interprets language, Geomancer owns geometry

## Product Shape

The current alpha experience is centered on one desktop workspace:

- left column: chat-style conversation thread, generation progress, system updates, prompt entry
- center stage: viewer, generation summary, readiness state, bottom info strip
- right column: current model facts, dimensions, features, actions

The UI now prioritizes truthful state over placeholder polish. If dimensions, features, or review signals are not available yet, the shell says so directly. The viewer is the hero surface and now uses a thinner toolbar, a denser telemetry strip, a dominant-face-first generic preview pose solver, support-aware floor grounding, a final settling pass, conservative dominant-surface leveling, and more deliberate first-view framing. The left rail now behaves like a compact product conversation: Geomancer posts readiness, progress, and result updates into a timestamped thread while user prompts appear as right-aligned messages, the opening Geomancer prompt carries the example chips directly inside the conversation, the Geomancer system avatar now uses the product icon instead of a placeholder initial, the chat bubbles use a tighter shadow treatment, the conversation history scrolls in its own dedicated vertical region between the fixed header and fixed composer, the composer includes a compact toolbelt with prompt-improver and quick-settings controls, the conversation header shows the dynamic session title in a stacked two-line layout with a faint divider and single-line ellipsis truncation, the viewer status/meta content lives in one compact footer band below the viewer instead of a separate top strip, the four-column strip beneath the viewer reads as a unified instrument panel with cleaner product wording and restrained teal accents, and the viewer controls now live inside the canvas overlay with a calm play/pause auto-orbit control.

## Architecture

### Desktop path

- `desktop/main.py` and `desktop/shell.py`: Qt desktop host
- `desktop/bridge.py`: WebChannel bridge plus Python background execution for generation
- `desktop/backend_controller.py`: desktop-facing controller and runtime health API
- `desktop/ui/`: setup gate, grounded viewer, workspace layout, and status surfaces

### Runtime/setup path

- `app/runtime/ollama.py`: local AI detection, reachability, model readiness, pulls, smoke checks
- `app/runtime/blender.py`: Blender detection and callability checks
- `app/runtime/health.py`: structured runtime health for UI/controller use
- `app/runtime/setup.py`: first-run setup state, step flow, and completion persistence
- `app/runtime/models.py`: recommended local AI model definitions

### Geometry path

- `app/backend/classifier.py`: supported-family classification
- `app/backend/normalizer.py`: deterministic parameter extraction
- `app/backend/geometry.py`: deterministic Blender Python generation
- `app/backend/validation.py`: validation and review summaries
- `app/backend/pipeline.py`: orchestration, preview export, and state updates

## First-Run Flow

The alpha product uses an in-app local setup flow:

1. Check this PC for Blender and the local AI runtime
2. Guide local setup if the AI runtime is missing
3. Set up the required AI model
4. Run a quick local check
5. Unlock the main workspace

The workspace remains gated until runtime health is complete.

## Generation Flow

1. The user submits a dimensional part request.
2. Local AI interprets the request.
3. Geomancer classifies the request into a supported family.
4. Geomancer normalizes dimensions and features.
5. Geomancer generates deterministic Blender Python.
6. Blender is used locally for preview export and handoff, with the desktop viewer showing a grounded review preview first.

Geomancer does not use arbitrary AI-written Blender code as the main path.

## Run

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the desktop shell:

```powershell
python -m desktop.main
```

Legacy developer entrypoints still exist:

- `python app/chat_agent.py`
- `python app/dev_console.py`

## Local Configuration

Optional `.env` overrides:

```text
BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 5.0\blender.exe
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b
```

## State And Outputs

- Session state: `data/session_state.json`
- Model library: `data/model_library.json`
- Generated script: `blender/generated_model.py`
- Preview exports: `data/previews/`

## Current Alpha Limits

- The desktop shell is now more product-shaped, but still alpha.
- Export, save-project, and deeper plan-inspection actions remain staged for later passes.
- The new conversation rail is still compact and alpha-oriented; it does not yet support threaded clarifications, message actions, or rich plan drill-down.
- Blender detection is still Windows-oriented.
- Deterministic geometry coverage is still limited to supported alpha families.
- Viewer framing is deterministic and family-aware, but still based on lightweight heuristics rather than deep geometry analysis.
- The compact telemetry strip is optimized for glanceability, so deeper inspection still belongs in later detail views rather than the main workspace chrome.
- Viewer support placement is still a lightweight sampled heuristic from preview geometry, not a semantic understanding of real-world load-bearing faces.
- Resting orientation is selected from a small deterministic candidate set rather than inferred from deeper mesh semantics or physics.
- The generic preview pose solver now prefers a dominant-face presentation frame and falls back to principal-axis normalization when face evidence is weak, but it is still a lightweight viewer heuristic rather than a full geometry semantics system.
- Floor contact and corner orientation aids are polished for readability, but they remain lightweight viewer-side presentation heuristics rather than CAD-accurate tooling.
