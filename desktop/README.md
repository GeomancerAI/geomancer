# Geomancer Desktop

The desktop app is the intended product surface for Geomancer alpha. It now has a clearer workspace structure, a local setup gate, a simpler background execution path for generation, a real conversation-style left rail, a more dominant grounded viewer presentation, tighter fit/stability polish across the lower summary and footer areas, compact Workspace app controls, a token-based light/dark theme surface system, and real top-level Workspace, Models, Projects, and Templates modes inside the same shell.

## Current Desktop Shape

- top shell modes: `Workspace`, `Models`, `Projects`, and `Templates`
- Workspace mode: left rail conversation thread, center viewer/review stage, right rail properties/actions
- Models mode: real saved-model library with search, sorting, single-select browsing, explicit multi-select deletion mode, selected-model Workspace reopen support, and a compact synced sidebar list for faster browsing
- Projects mode: alpha project browser with in-memory project creation, project selection/deletion controls, derived saved-model containers, open-project navigation, and model cards reused from the Models visual language
- Templates mode: curated starter blueprint library with category filtering, geometric starter-card previews, and one-click prompt launch into Workspace

Viewer presentation notes:

- preview orientation is normalized before grounding using a dominant-face-first generic pose solver, with PCA retained only as fallback
- previews are placed cleanly on the stage floor rather than floating ambiguously
- support-aware placement now favors the resting footprint near the floor instead of always centering from the full model bounds
- a final settling pass, conservative dominant-surface leveling, and tighter contact shadow help the support region read as flush with the stage
- first-load framing is deterministic and lightly family-aware
- empty, generating, and ready states use lighter product-facing overlay language
- the corner orientation helper is now a real miniature 3D orientation cube rendered in its own overlay scene and rotated from the main viewer camera, with wider framing to avoid clipping plus calmer teal-led materials and glow
- the top viewer controls are intentionally compressed into a thin toolbar
- the lower summary area now lands as three user-facing groups for model info, printability, and mesh readiness, with printability carrying slightly stronger visual emphasis and mesh kept more muted
- the lower summary area and footer/meta row now use denser alignment, better overflow handling, and more stable text footprints so longer values and animated generation states do not crowd adjacent content
- the footer now presents generation/status copy as a flexible strip and moves runtime emphasis into AI/Blender connection pips, version text, and the `Show logs` action
- the dark mode treatment now uses shared background/surface/panel tokens so panels and cards separate cleanly instead of flattening into an inverted gray wash
- runtime logs remain available from the `Show logs` modal instead of occupying the main workspace
- startup readiness, setup actions, user prompts, and generation progress now appear as timestamped Geomancer/user chat bubbles instead of static sidebar cards
- the opening Geomancer message now carries the clickable example prompts, while the composer stays a simpler stable input zone
- the conversation thread now uses the real Geomancer chat avatar, top-aligned assistant bubbles, premium new-chat control styling, and stricter vertical-only scrolling
- chat bubbles use a tighter, less diffuse shadow so the thread feels crisper without changing layout
- the conversation history now owns the only scrollable region in the left rail, while the header and composer stay fixed and message rows no longer clip or overlap
- the composer now includes a compact toolbelt beneath the prompt with coming-soon media controls, an active prompt improver modal, and a lightweight quick settings menu
- the prompt submit control now uses a compact send icon with enough reserved textarea space to avoid scrollbar overlap
- the conversation header now uses a stacked `Session` plus dynamic-title treatment with single-line ellipsis truncation instead of the previous inline header
- the corner XYZ gizmo is offset higher within the viewer so it clears the lower edge instead of clipping
- viewer generation state, summary text, and the subtle View plan action now live in the bottom footer/meta band instead of a separate top status strip above the viewer
- the lower section beneath the viewer emphasizes readiness, dimensions, model identity, and attention instead of broader system telemetry
- the right rail now behaves as a truthful read-only properties panel that only shows dimensions, wall thickness, and generated features when those values are actually available
- the actions area is now visually separated as its own soft container so next steps read distinctly from model understanding
- the orientation cube now reflects the main viewer basis correctly by mapping the main camera through the gizmo camera's own render basis instead of treating the gizmo as if it rendered in world space directly
- runtime and setup emphasis now lives in the footer/meta area instead of dominating the lower summary band
- Orbit / Pan / Zoom now sit inside the viewer as overlay controls, the lower-right orientation aid is now a compact cube rather than an axis widget, a lower-left icon-based auto-orbit toggle controls calm camera motion, the orbit puck has a more refined glass treatment, and the top-left viewer status card now remains visible as a persistent guide instead of acting like a temporary toast
The UI is intentionally truthful:

- no fake dimensions or features
- unavailable data is labeled clearly
- review-level metrics are described as approximate or not yet measured
- idle and in-flight states now use clearer waiting/generating language, with a lightweight animated ellipsis during generation instead of repeated `Pending` placeholders
- the footer generation chip now holds a fixed width so animated ellipsis states do not jitter nearby text
- real generation-state loading treatment is now intentionally lightweight: the viewer overlay, properties empty state, lower summary values, and footer status use subtle in-flight motion without inventing fake progress
- top-level mode switching now happens inside the desktop shell without leaving the app, and Workspace stays mounted so returning to it preserves the active session state as much as practical
- Models now emphasize the visual tile library first, with a lighter contextual actions row and no dominant selected-model management strip above the grid
- the remaining old Models-only management framing has been removed so the screen reads as one coherent library view, with cleaner tile hierarchy and quieter metadata
- the Models empty state now hides cleanly whenever saved models exist, the left sidebar now uses its spare vertical space for a compact list browser that stays selection-synced with the main grid, and the Models header now uses a tighter two-zone tool header with normalized selected-model actions plus a separate multi-select delete mode
- Projects now has a functional alpha browser: a project-card overview, New Project control, project selection/delete mode for user-created in-memory projects, open-project detail view, back navigation, and saved-model browsing inside the selected project using existing model-card presentation patterns
- Templates now has a library surface with category navigation, refined starter cards, geometry-specific CSS preview marks, fallback starter definitions, backend-provided template support, and Workspace prompt prefill launch behavior
- the top-right shell controls now provide existing Workspace actions for new session and reset workspace plus a real theme toggle, while unsupported save behavior remains intentionally absent

## Current Architecture

- `desktop/main.py`: desktop entrypoint
- `desktop/shell.py`: Qt window and WebEngine host
- `desktop/bridge.py`: bridge surface plus Python background generation execution
- `desktop/backend_controller.py`: generation adapter and runtime health controller
- `desktop/ui/`: setup gate, viewer, layout, and shell styling

Runtime flow:

1. desktop shell
2. local setup and runtime health
3. deterministic geometry pipeline
4. Blender preview and handoff

## Runtime Truth

Desktop status should come from real runtime checks, not placeholder copy.

The current shell reports:

- local AI setup state
- Blender detection state
- generation readiness
- current generation summary
- runtime logs through the logs modal

The main workspace stays gated until:

- local AI is installed and reachable
- the required AI model is ready
- Blender is detected and callable
- setup completion is recorded

## Run

```powershell
python -m desktop.main
```

## Scope Notes

- `app/chat_agent.py` remains a legacy developer entrypoint.
- The desktop path still uses deterministic geometry generation as the core product path.
- Future passes can deepen export actions, model-library views, and plan inspection without changing the product direction.
- Viewer grounding and framing are polished for alpha presentation, but they are still lightweight heuristics rather than CAD-grade camera logic.
