# Changelog

This project uses lightweight milestone-based semantic versioning during alpha.

- Format: `MAJOR.MINOR.PATCH-stage`
- Current stage: `alpha`
- Current version source of truth: `VERSION`
- Milestone labels are short descriptive slugs attached to notable passes or refactor checkpoints.

## Versioning Pattern

Use this pattern going forward:

- Increment `PATCH` for docs-only passes, small reversible fixes, and narrow backend corrections.
- Increment `MINOR` for meaningful backend milestones, new internal capabilities, or cross-module refactors that change behavior but remain alpha-stage.
- Increment `MAJOR` only for deliberate project resets or major architecture breaks that redefine the product baseline.
- Keep the stage suffix explicit while the project is pre-release, for example `0.4.0-alpha`.
- Add a milestone label for each notable pass, for example `backend-pipeline-cleanup` or `desktop-bridge-contract-pass-1`.

Recommended entry format:

```md
## 2026-04-06 - 0.3.1-alpha - backend-foundation-doc-baseline

### Files Changed
- README.md
- CHANGELOG.md
- VERSION
- desktop/README.md
- docs/README.md

### Summary
- Established repo-level change tracking conventions.
- Updated project status documentation to reflect desktop direction and backend-first alpha work.

### Known Limitations
- UI remains scaffold-level.
- Backend contracts are still in flux.

### Rollback / Review Notes
- Safe docs-only pass.
- Revert as a single documentation/versioning checkpoint if needed.
```

## Codex Pass Documentation Standard

Every future backend-focused Codex pass should record, either in the changelog or in an equivalent review artifact linked from it:

### Required Fields

- `Version`: exact version string from `VERSION`
- `Milestone`: short label for the pass
- `Files Changed`: exact repo-relative paths
- `Summary`: concise explanation of what changed
- `Verification`: tests, compile checks, or manual validation performed
- `Known Limitations`: incomplete work, technical debt, temporary assumptions, or unverified areas
- `Rollback / Review Notes`: how to inspect, revert, or safely isolate the change

### Review Rules

- List exact files, not broad folders, unless a full folder-wide mechanical change was intentional.
- Separate completed work from planned follow-up.
- Call out risky migration points, state schema changes, interface changes, or generated asset updates.
- If a pass is docs-only, say so explicitly.
- If a pass is partially complete, state exactly what remains.

## Entries

## 2026-04-06 - 0.5.0-alpha - desktop-backend-truth-bridge-pass

### Files Changed
- `README.md`
- `CHANGELOG.md`
- `VERSION`
- `desktop/README.md`
- `app/state.py`
- `app/backend/pipeline.py`
- `desktop/backend_controller.py`
- `desktop/bridge.py`
- `desktop/ui/index.html`
- `desktop/ui/app.js`

### Summary
- Reconnected the hardened deterministic backend to the desktop UI so the shell now reflects real backend generation data instead of static demo placeholders.
- Extended persisted backend state with normalized plan, validation, classification, generation status/message, and preview export metadata for desktop bootstrap and refresh.
- Updated the desktop controller and bridge to return that richer backend truth to the UI.
- Rewired the desktop UI history, right panel, bottom metrics strip, and viewer flow to consume real prompt, family, dimensions, feature summaries, validation state, and preview model paths.
- Kept the current shell and viewer architecture intact while improving accuracy of displayed state.

### Verification
- `python -m compileall app desktop tests`
- Static sanity checks on bridge/UI field wiring with `rg`
- Manual review of viewer refresh key handling so repeated generations reload preview assets instead of reusing stale preview keys

### Known Limitations
- Triangle count and exact mesh statistics are still unavailable in the desktop UI because the backend does not yet emit real mesh-analysis metadata.
- Volume remains an estimate derived from normalized dimensions rather than a mesh-measured value.
- The right panel is still display-oriented rather than a full editable regeneration surface.
- Some left-rail cards and general shell chrome remain partially static outside the generation-specific data areas.

### Rollback / Review Notes
- Review `app/backend/pipeline.py`, `desktop/backend_controller.py`, `desktop/bridge.py`, and `desktop/ui/app.js` together; the pass depends on those layers sharing the same payload shape.
- This pass intentionally avoids UI redesign and focuses on truthfulness of desktop data flow.
- If rollback is needed, revert this as a single desktop-backend reconnection checkpoint on top of `0.4.2-alpha`.

## 2026-04-06 - 0.4.2-alpha - golden-path-family-hardening-pass-2

### Files Changed
- `README.md`
- `CHANGELOG.md`
- `VERSION`
- `app/backend/classifier.py`
- `app/backend/normalizer.py`
- `app/backend/geometry.py`
- `tests/test_backend_alpha_pipeline.py`

### Summary
- Hardened the next practical alpha families: `bracket`, `adapter`, `cable_clip`, and `hook_mount`.
- Improved family disambiguation and confidence scoring for bracket, adapter/reducer, wire-clip, and hook-mount phrasing.
- Added stronger family-specific normalization for bracket hole counts and gussets, adapter diameter pairs and through-holes, cable diameter/opening/base assumptions, and hook drop plus mount-hole handling.
- Improved deterministic geometry for multi-hole brackets, stepped adapters with optional flange support, printable open cable clips with mount-hole support, and more stable hook-mount proportions.
- Expanded regression coverage and kept preview export/result payload behavior intact for the new golden-path families.

### Verification
- `python -m unittest discover -s tests -p "test_*.py"`
- `python -m compileall app desktop tests`
- Manual smoke checks through `app.backend.pipeline.generate_model_request(...)` for `bracket`, `adapter`, `cable_clip`, and `hook_mount`

### Known Limitations
- `bracket` requests are still normalized to right-angle blockouts even if another angle is requested.
- `adapter` geometry remains a stepped cylindrical reducer, not a smooth lofted transition.
- `cable_clip` requests that imply a closed loop are still normalized to an open printable clip.
- `hook_mount` requests for double hooks are currently normalized to a single hook blockout.

### Rollback / Review Notes
- Review `app/backend/normalizer.py` and `app/backend/geometry.py` together; the family behavior is now more dependent on family-specific extraction rules.
- This pass preserves the desktop bridge and pipeline payload shape.
- If rollback is needed, revert this as a focused second golden-path hardening checkpoint on top of `0.4.1-alpha`.

## 2026-04-06 - 0.4.1-alpha - golden-path-family-hardening-pass-1

### Files Changed
- `README.md`
- `CHANGELOG.md`
- `VERSION`
- `app/backend/families.py`
- `app/backend/models.py`
- `app/backend/classifier.py`
- `app/backend/normalizer.py`
- `app/backend/geometry.py`
- `tests/test_backend_alpha_pipeline.py`

### Summary
- Hardened the first four golden-path alpha families: `panel_plate`, `spacer_standoff`, `enclosure`, and `tray_box`.
- Improved family disambiguation and confidence scoring for box/case/tray/plate/standoff prompts.
- Added stronger normalization for named dimensions, wall/base thickness, plate hole assumptions, standoff inner/outer diameter handling, and enclosure opening basics.
- Improved deterministic geometry for plate hole layouts, round/hex standoffs, enclosure front openings, and tray rim behavior.
- Expanded regression coverage and verified end-to-end preview payload behavior for the target families.

### Verification
- `python -m unittest discover -s tests -p "test_*.py"`
- `python -m compileall app desktop tests`
- Manual smoke checks through `app.backend.pipeline.generate_model_request(...)` for `panel_plate`, `spacer_standoff`, `enclosure`, and `tray_box`

### Known Limitations
- Hole patterns for `panel_plate` remain intentionally simple and currently focus on 2-hole and 4-corner layouts.
- `enclosure` front openings are still simple rectangular cutouts rather than full panel-feature systems.
- `tray_box` lip behavior is conservative and does not yet model nested trays, dividers, or draft angles.
- `spacer_standoff` outputs are still blockouts and do not attempt threaded or chamfered hardware detail.

### Rollback / Review Notes
- Review `app/backend/classifier.py`, `app/backend/normalizer.py`, and `app/backend/geometry.py` together; the hardening depends on all three layers staying aligned.
- This pass does not change the desktop bridge contract shape.
- If rollback is needed, revert this as a focused family-hardening checkpoint on top of `0.4.0-alpha`.

## 2026-04-06 - 0.4.0-alpha - alpha-family-backend-refactor

### Files Changed
- `README.md`
- `CHANGELOG.md`
- `VERSION`
- `desktop/README.md`
- `app/chat_agent.py`
- `app/code_utils.py`
- `app/state.py`
- `app/backend/__init__.py`
- `app/backend/families.py`
- `app/backend/models.py`
- `app/backend/classifier.py`
- `app/backend/normalizer.py`
- `app/backend/geometry.py`
- `app/backend/validation.py`
- `app/backend/versioning.py`
- `app/backend/pipeline.py`
- `tests/test_backend_alpha_pipeline.py`

### Summary
- Replaced the old narrow prototype request gating with an explicit alpha-family classifier.
- Split the backend into cleaner modules for classification, normalization, deterministic generation, validation, version loading, and orchestration.
- Added deterministic Blender generation recipes for the supported alpha family set and preserved the existing terminal and desktop result flow shape.
- Extended saved session state to include the last generated family and validation summary.
- Updated root and desktop documentation to describe the deterministic backend-first alpha architecture.

### Verification
- `python -m unittest discover -s tests -p "test_*.py"`
- `python -m compileall app desktop tests`
- Manual pipeline smoke check with a sample enclosure request through `app.backend.pipeline.generate_model_request`

### Known Limitations
- Family recipes are still coarse alpha blockouts rather than production-ready geometry.
- Several families currently use conservative simplified recipes and intentionally ignore advanced details such as threads, involute gear teeth, fillets, or complex mounting features.
- Legacy Ollama-oriented modules still exist in the repo and have not yet been fully retired.

### Rollback / Review Notes
- Review the new `app/backend/` package first; it contains the architectural center of this pass.
- `app/chat_agent.py` is now primarily a terminal wrapper around the backend pipeline rather than the source of generation logic.
- If rollback is needed, revert this pass as a single backend architecture checkpoint rather than cherry-picking individual recipe files.

## 2026-04-06 - 0.3.1-alpha - backend-foundation-doc-baseline

### Files Changed
- `README.md`
- `CHANGELOG.md`
- `VERSION`
- `desktop/README.md`
- `docs/README.md`

### Summary
- Added a root changelog to standardize version history and future Codex pass reporting.
- Updated the root README to reflect the current desktop-app direction, backend-first development phase, and alpha-state expectations.
- Aligned subfolder READMEs with the current architecture so the desktop shell and docs site are described consistently.
- Promoted version and milestone tracking to a first-class part of repo maintenance.

### Known Limitations
- This pass does not change runtime behavior.
- The alpha architecture is still evolving, especially around backend-to-desktop contracts.
- Existing code changes elsewhere in the repo were intentionally left untouched.

### Rollback / Review Notes
- This is a docs-and-versioning-only checkpoint.
- Reviewers can inspect the five files listed above to validate the full scope.
- If rollback is needed, revert this pass as a single documentation baseline change.
