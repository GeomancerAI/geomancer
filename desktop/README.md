# Geomancer Desktop

The desktop app is the intended product surface for Geomancer alpha. It now has a clearer workspace structure, a local setup gate, a simpler background execution path for generation, a real conversation-style left rail, and a more dominant grounded viewer presentation.

## Current Desktop Shape

- left rail: conversation thread, readiness and generation updates, prompt entry
- center stage: model viewer, generation summary, readiness messaging, compact info strip
- right rail: current model facts, parsed dimensions, features, and next actions

Viewer presentation notes:

- preview orientation is normalized before grounding using a dominant-face-first generic pose solver, with PCA retained only as fallback
- previews are placed cleanly on the stage floor rather than floating ambiguously
- support-aware placement now favors the resting footprint near the floor instead of always centering from the full model bounds
- a final settling pass, conservative dominant-surface leveling, and tighter contact shadow help the support region read as flush with the stage
- first-load framing is deterministic and lightly family-aware
- empty, generating, and ready states use lighter product-facing overlay language
- the corner orientation helper is now a fixed XYZ-line gizmo with a visible shared origin instead of the previous circular badge treatment
- the top viewer controls are intentionally compressed into a thin toolbar
- the lower summary area is now a denser telemetry strip instead of a dashboard-style card row
- runtime logs remain available from the `Show logs` modal instead of occupying the main workspace
- startup readiness, setup actions, user prompts, and generation progress now appear as timestamped Geomancer/user chat bubbles instead of static sidebar cards
- the opening Geomancer message now carries the clickable example prompts, while the composer stays a simpler stable input zone
- the conversation thread now uses the real Geomancer chat avatar, top-aligned assistant bubbles, premium new-chat control styling, and stricter vertical-only scrolling
- chat bubbles use a tighter, less diffuse shadow so the thread feels crisper without changing layout
- the conversation history now owns the only scrollable region in the left rail, while the header and composer stay fixed and message rows no longer clip or overlap
- the composer now includes a compact toolbelt beneath the prompt with coming-soon media controls, an active prompt improver modal, and a lightweight quick settings menu
- the conversation header now uses a stacked `Session` plus dynamic-title treatment with single-line ellipsis truncation instead of the previous inline header
- the corner XYZ gizmo is offset higher within the viewer so it clears the lower edge instead of clipping
- viewer generation state, summary text, and the subtle View plan action now live in the bottom footer/meta band instead of a separate top status strip above the viewer
- the four-column strip beneath the viewer now uses shorter section titles, clearer row hierarchy, and generation/review facts that feel more like a product instrument panel than debug cards
- Orbit / Pan / Zoom now sit inside the viewer as overlay controls, the XYZ gizmo is back in the lower-right viewer corner, and a lower-left Play / Pause button controls calm auto-orbit

The UI is intentionally truthful:

- no fake dimensions or features
- unavailable data is labeled clearly
- review-level metrics are described as approximate or not yet measured

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
