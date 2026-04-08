# Geomancer Desktop

The desktop app is the intended product surface for Geomancer alpha. It now has a clearer workspace structure, a local setup gate, a simpler background execution path for generation, and a more dominant grounded viewer presentation.

## Current Desktop Shape

- left rail: setup guidance, request history, generation status, prompt entry
- center stage: model viewer, generation summary, readiness messaging, compact info strip
- right rail: current model facts, parsed dimensions, features, and next actions

Viewer presentation notes:

- preview orientation is normalized before grounding using a generic principal-axis pose solver instead of family-specific exception rules
- previews are placed cleanly on the stage floor rather than floating ambiguously
- support-aware placement now favors the resting footprint near the floor instead of always centering from the full model bounds
- first-load framing is deterministic and lightly family-aware
- empty, generating, and ready states use lighter product-facing overlay language
- the top viewer controls are intentionally compressed into a thin toolbar
- the lower summary area is now a denser telemetry strip instead of a dashboard-style card row
- runtime logs remain available from the `Show logs` modal instead of occupying the main workspace

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
