# Geomancer

Geomancer is a local-first AI-assisted 3D modeling tool. Local AI interprets requests, Geomancer owns deterministic geometry generation, and Blender remains the local preview and editing target.

## Current Status

- Version: `0.8.0-alpha`
- Stage: `alpha`
- Product direction: desktop shell -> local setup -> deterministic geometry pipeline -> Blender handoff
- Core rule: AI interprets language, Geomancer owns deterministic geometry

## Product Shape

The current alpha experience is centered on one desktop shell with top-level modes:

- Workspace: chat-style conversation thread, generation progress, viewer, read-only properties, actions, bottom summary surfaces, compact top-right app controls, and a cleaner runtime/footer status row
- Models: saved local model library with search, sorting, single-select browsing, explicit multi-select deletion mode, selection-tied actions, Workspace reopen/edit support, and a synced compact sidebar browser
- Projects: alpha project containers with in-memory project creation, selection/deletion controls, and saved-model group browsing
- Templates: curated starter blueprint library with category filtering, geometric starter cards, and Workspace prompt launch

The UI now prioritizes truthful state over placeholder polish. If dimensions, features, or review signals are not available yet, the shell says so directly. The viewer is the hero surface and now uses a thinner toolbar, a dominant-face-first generic preview pose solver, support-aware floor grounding, a final settling pass, conservative dominant-surface leveling, and more deliberate first-view framing. The left rail now behaves like a compact product conversation: Geomancer posts readiness, progress, and result updates into a timestamped thread while user prompts appear as right-aligned messages, the opening Geomancer prompt carries the example chips directly inside the conversation, the Geomancer system avatar now uses the product icon instead of a placeholder initial, the chat bubbles use a tighter shadow treatment, the conversation history scrolls in its own dedicated vertical region between the fixed header and fixed composer, the composer includes a compact toolbelt with prompt-improver and quick-settings controls, the composer submit control is now a compact send icon with reserved textarea space so it does not collide with scrollbars, the conversation header shows the dynamic session title in a stacked two-line layout with a faint divider and single-line ellipsis truncation, the lower section beneath the viewer now lands as three user-facing groups for model info, printability, and mesh readiness, the right rail now behaves as a truthful read-only properties panel that only shows real generated dimensions, wall thickness, and features when available, the actions area is visually separated as its own next-step container, runtime status emphasis lives in the footer instead of the lower summary band, the footer status area is now a flexible generation/status strip with AI and Blender runtime pips, version, and `Show logs`, the top-right shell now exposes compact icon controls for new session, reset workspace, and a real surface-based theme toggle, the bottom summary band and footer have been tightened for cleaner alignment and more stable long-value layout, the bottom printability rows now use the same left/right row rhythm as the other summary groups with shorter fit-safe wording where needed, restrained real generation-state loading cues now appear across the viewer, properties, summary band, and footer, the top shell now switches cleanly between Workspace, Models, Projects, and Templates without leaving the app, Models now read as one coherent visual library view instead of carrying older management-first framing, the Models empty state now hides correctly whenever real saved models exist, the sidebar now includes a compact synced model browser that shares the same selection as the main grid, the Models header now uses a compact two-zone tool header with a left label/subtitle block and right `Saved models` label, Models has normalized selected-model action buttons and a dedicated multi-select deletion mode that stays separate from normal single-select browsing, Projects now supports a polished alpha project browser with in-memory project creation, project-card selection mode, delete controls for user-created projects, and open-project model browsing derived from saved model groups, Templates now provides a curated starter blueprint library with category filtering, minimal geometry-specific preview marks, refined card hover treatment, and prompt launch into Workspace, and the orientation cube now uses the same effective viewer basis as the staged model and main camera instead of a mismatched local gizmo basis. The dark mode theme now uses shared surface tokens instead of a simple inversion so the workspace reads as layered surfaces rather than a flat grayscale flip.

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

- `app/backend/plan_schema.py`: authoritative Plan Schema v1 dataclasses
- `app/backend/plan_validator.py`: conservative normalization and validation
- `app/backend/recipe_builder.py`: deterministic recipe construction
- `app/backend/recipe_executor.py`: deterministic Blender-facing execution
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
2. Local AI interprets the request into a structured plan.
3. Geomancer validates and normalizes the plan.
4. Geomancer builds a deterministic recipe from the validated plan.
5. Geomancer executes the recipe into deterministic geometry.
6. Blender is used locally for preview export and handoff, with the desktop viewer showing a grounded review preview first.
7. Supported parameters can be edited in the right rail and regenerated deterministically from the edited plan, including reopened saved models when truthful plan data is available.

Geomancer now covers bounded functional objects, compositional props, hybrid combinations, a deterministic style layer, right-rail parameter editing and regeneration, and truthful saved-model reopen/edit workflows.

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

Legacy terminal helpers remain for compatibility only:

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
- Deterministic geometry coverage now includes the existing functional families, a small compositional prop foundation, bounded hybrid combinations, and a deterministic style layer, but it is still bounded and deterministic rather than freeform.
- Viewer framing is deterministic and object-type-aware, but still based on lightweight heuristics rather than deep geometry analysis.
- The compact telemetry strip is optimized for glanceability, so deeper inspection still belongs in later detail views rather than the main workspace chrome.
- Viewer support placement is still a lightweight sampled heuristic from preview geometry, not a semantic understanding of real-world load-bearing faces.
- Resting orientation is selected from a small deterministic candidate set rather than inferred from deeper mesh semantics or physics.
- The generic preview pose solver now prefers a dominant-face presentation frame and falls back to principal-axis normalization when face evidence is weak, but it is still a lightweight viewer heuristic rather than a full geometry semantics system.
- Floor contact and corner orientation aids are polished for readability, but they remain lightweight viewer-side presentation heuristics rather than CAD-accurate tooling.
