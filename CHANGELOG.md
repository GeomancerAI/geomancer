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

## 2026-04-22 - 0.8.0-alpha - capability-expansion-release

### Summary
- [H1] Hybrid generation is now a first-class deterministic path alongside functional and compositional generation.
- [S1] A deterministic style system now applies bounded visual language across supported builds.
- [P1] The right rail now supports bounded parameter editing and deterministic regenerate-from-plan behavior.
- [R1] Saved models can reopen into truthful editable workspace context when plan data is available.
- [R4] Artifact-only or incomplete saved models remain view-only rather than being mislabeled as editable.
- The desktop payload, persisted state, export truth, and observability contract remain intact.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline tests.test_desktop_bridge`
- `node --check desktop/ui/app.js`

## 2026-04-22 - saved-model-reopen-edit-workflow

### Summary
- [R1] Saved model entries now preserve enough structured plan/context metadata to reopen truthful edit surfaces when a saved model is actually editable.
- [R2] Opening a saved model in Workspace now restores the current plan, observability summaries, and saved-model provenance so the edit panel can reappear without inventing context.
- [R3] Reopened editable models can regenerate through the same deterministic validate -> recipe -> execute pipeline as in-session edits.
- [R4] Artifact-only or incomplete saved models are handled honestly as view-only instead of being relabeled as editable.
- [R5] Export truth and observability truth remain tied to the restored or regenerated final artifact.
- Desktop payload and persisted state contracts remain unchanged.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline tests.test_desktop_bridge`
- `node --check desktop/ui/app.js`

## 2026-04-22 - parameter-edit-regenerate-workflow

### Summary
- [P1] Exposed a bounded editable parameter surface derived from the current interpreted plan so users can adjust supported dimensions, style, and selected features without raw JSON editing.
- [P2] Added a deterministic regenerate-from-plan workflow that routes edited plans back through the same validator, recipe builder, executor, and preview/export pipeline.
- [P3] Kept edit handling validation-aware so invalid parameter changes still return honest clarification or validation failures rather than silently mutating geometry.
- [P4] Added right-rail edit controls and regenerate/reset actions inside the existing observability/actions layout without changing the desktop contract.
- [P5] Persisted edited-plan metadata and editable parameter state so the desktop can restore the last truthful edit surface after refresh or restart.
- Desktop payload and persisted state contracts remain unchanged.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline tests.test_desktop_bridge`
- `node --check desktop/ui/app.js`

## 2026-04-22 - deterministic-style-system

### Summary
- [S1] Added an explicit deterministic style layer to Plan Schema v1 so supported plans can carry bounded style profiles and derived style metadata.
- [S2] Updated prompt interpretation to route supported style signals like `sci-fi`, `industrial`, `low poly`, and `rounded` into the plan when they are supported for the selected object type.
- [S3] Added style compatibility validation so unsupported object/style pairings fall back honestly with clear warnings and normalized style metadata.
- [S4] Extended recipe building and execution with deterministic style modifiers such as beveling and style-sensitive primitive templates.
- [S5] Style summaries now flow through interpretation, validation, build, and desktop observability state so the right rail can explain the applied visual language.
- Desktop payload and persisted state contracts remain unchanged.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline tests.test_desktop_bridge`
- `node --check desktop/ui/app.js`

## 2026-04-22 - hybrid-constraint-compositional-generation

### Summary
- [H1] Added a bounded hybrid plan layer so a single plan can combine a primary functional or compositional base with supported secondary details.
- [H2] Updated prompt interpretation to route mixed prompts like functional parts with decorative accents or compositional props with mounting features into the hybrid path when supported.
- [H3] Extended validation to enforce a narrow supported hybrid matrix while keeping unsupported combinations honest.
- [H4] Extended recipe building to emit deterministic hybrid ops through the same recipe pipeline and executor.
- [H5] Hybrid builds now surface clearly in interpretation, decision, and build summaries without changing the desktop payload/state contract.
- Desktop payload and persisted state contracts remain unchanged.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline tests.test_desktop_bridge`
- `node --check desktop/ui/app.js`

## 2026-04-22 - capability-aware-ux-guidance

### Summary
- [U1] Refined Workspace prompt guidance and example prompts so the composer now surfaces both practical functional objects and bounded compositional props.
- [U2] Updated idle and empty-state copy to describe the expanded capability surface without overclaiming beyond the current supported modes.
- [U3] Polished unsupported and clarification wording so they feel calmer, more actionable, and consistent with the plan-first backend contract.
- [U4] Adjusted right-rail wording and build-path labeling so functional and compositional outputs read naturally in the same observability surface.
- [U5] Improved discoverability of supported prompt types through compact helper copy and mixed example prompts.
- Desktop payload and persisted state contracts remain unchanged.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline tests.test_desktop_bridge`
- `node --check desktop/ui/app.js`

## 2026-04-21 - compositional-geometry-foundation

### Summary
- [X1] Added an explicit `construction_mode` to Plan Schema v1 so plans can distinguish constraint-driven parts from compositional assets.
- [X2] Added typed compositional plan items and deterministic template support for simple assets such as crates, barrels, canisters, pedestals, and primitive assemblies.
- [X3] Updated prompt interpretation to route supported simple asset requests into compositional mode while keeping sculptural/organic requests unsupported.
- [X4] Extended validation to handle compositional plans with deterministic primitive-item checks and envelope bounds while preserving strict constraint-mode validation.
- [X5] Extended recipe building and execution to deterministically emit compositional primitive geometry through the existing recipe pipeline.
- Desktop payload and persisted state contracts remain unchanged.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline`
- `python -m unittest tests.test_desktop_bridge`
- `node --check desktop/ui/app.js`

## 2026-04-21 - stl-export-right-rail-action

### Summary
- [E5] Stabilized STL export around the current final model artifact so the app distinguishes preview, final, and exported STL truth cleanly.
- Added an `Export STL` action to the Workspace right rail and wired it through the desktop bridge/controller path with honest success, unavailable, and failure states.
- Preserved the existing desktop payload/state contract while adding STL export metadata for readiness, status, message, and source artifact tracking.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline`
- `python -m unittest tests.test_desktop_bridge`
- `node --check desktop/ui/app.js`

## 2026-04-21 - backend-natural-language-dimensions

### Summary
- [B2] Natural-language dimension phrases such as `22mm wide`, `4mm depth`, `22mm height`, and `3mm thick` now map into canonical Plan v1 dimension fields during interpretation.
- [B3] Clarification output now narrows to only the truly missing dimensions when partial size information is provided.
- [C5] Compact dimension forms like `120 x 80 x 20 mm` are parsed conservatively for supported object types, while labeled dimensions take priority over ambiguous compact forms.
- [G1] Interpretation now preserves partially recognized dimensions in the draft plan so the backend can explain exactly what it understood.
- Desktop payload and persisted state contract remain unchanged.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline`

## 2026-04-21 - desktop-observability-right-rail

### Summary
- [G4] Surfaced interpretation, decision, validation, missing-info, assumption, warning, and build metadata in the existing Workspace right rail.
- [G5] Upgraded the right rail with compact observability cards so clarification, unsupported, success, and error states explain themselves without dumping raw JSON.
- Persisted backend metadata now renders from both fresh generation payloads and restored shell state.
- Preserved the existing workspace layout, viewer balance, and desktop bridge/backend contract.

### Verification
- `python -m compileall app desktop tests`
- `node --check desktop/ui/app.js`

## 2026-04-21 - backend-interpretation-clarification-observability

### Summary
- [B4] Unsupported and invalid prompts now fail honestly instead of being coerced into fake geometry, with clear unsupported and empty-prompt responses.
- [B5] Interpretation now records assumptions, warnings, and missing info explicitly when defaults are used or clarification is required.
- [C4] Validator compatibility checks were broadened for hole size, slot size, shell wall thickness, opening bounds, and related component relationships.
- [C5] Clarification-mode output now carries partial plan context, missing info, assumptions, warnings, and concise summaries.
- [G1] [G2] [G3] The backend now persists richer interpretation, decision, missing-info, assumption, and warning metadata for future UI inspection.
- Desktop payload and persisted state keys remain compatible with the current shell contract.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline`

## 2026-04-21 - backend-legacy-cleanup-recipe-id-standardization

### Summary
- [D3] Standardized recipe naming around deterministic recipe identifiers derived from Plan Schema v1 instead of ad hoc family routing.
- [D4] Standardized implementation IDs behind a single recipe-builder code path so the same plan always resolves to the same implementation metadata.
- [F5] Deleted dead legacy backend modules and removed stale imports/re-exports from the live path where they were no longer needed.
- Deleted `plan_bridge.py` rather than keeping a transitional shim, and updated documentation to reflect the plan -> validate -> recipe -> execute architecture.
- Preserved the desktop payload/state contract, including the existing result keys and persisted generation metadata.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline`

## 2026-04-21 - plan-schema-v1-pipeline-rewrite

### Summary
- [A2] Introduced Plan Schema v1 as the authoritative backend plan format with `GeomancerIntent`, typed `GeomancerComponent` entries, `GeomancerPlan`, and structured validation results.
- [A5] Aligned defaults and validation-ready plan structure around `mm` units, printable constraints, thickness minimums, and desktop-safe serialization.
- [B1] Rewrote `pipeline.py` around a strict `interpret_prompt_to_plan(...) -> validate_plan(...) -> build_deterministic_recipe(...) -> execute_recipe(...)` entry boundary.
- [C1] Replaced canonical-schema validation with conservative Plan v1 validation, including unknown-type rejection, thickness clamping, and clarification on printable plans with no components.
- [D1] Updated the deterministic recipe builder to consume only validated Plan v1 data.
- [F1] [F2] [F3] Removed classifier/archetype/normalizer routing from the live generation path while preserving desktop payload/state compatibility fields.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline`

## 2026-04-21 - plan-schema-v1-hardening-cleanup

### Summary
- Removed public canonical-plan aliases from `plan_schema.py` and dropped the deprecated `validate_canonical_plan(...)` shim so new code must use Plan Schema v1 directly.
- Quarantined the old `plan_bridge.py` path behind explicit runtime errors instead of leaving transitional canonical helpers silently available.
- Hardened `interpret_prompt_to_plan(...)` to reject unsupported sculptural prompts, stop inventing default overall dimensions for incomplete requests, and keep only recipe naming continuity for plate execution metadata.
- Tightened `validate_plan(...)` with required-dimension checks, printable-envelope checks, and unrealistic component validation while preserving the desktop payload/state contract.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline tests.test_backend_archetypes`

Recommended entry format:

```md
## 2026-04-20 - recipe-executor-mm-to-meter-direct-builds

### Summary
- Moved active recipe-path body construction for boxes, shells, brackets, phone stands, and hook mounts onto direct meter-space mesh creation so recipe output no longer depends on object scaling after creation.

### Verification
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline`
- `python -m compileall app/backend/recipe_executor.py tests/test_backend_plan_schema.py`

## 2026-04-19 - hook-mount-wall-hook-v1-profile-fix

### Summary
- Corrected the `hook_mount` direct-body profile so it now builds a recognizable wall hook silhouette with an explicit wall plate, horizontal arm, and visible upward tip using a named X/Z side profile extruded along Y.

### Verification
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline`
- `python -m compileall app tests`

## 2026-04-19 - hook-mount-wall-hook-v1

### Summary
- Reworked `hook_mount` onto a direct coherent `hook_mount_body` recipe op, updated its implementation id to `hook_mount_wall_hook_v1`, and carried the new provenance through the backend pipeline and recipe executor.

### Verification
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline`
- `python -m compileall app tests`

## 2026-04-19 - desktop-clean-dev-reload

### Summary
- Turned `File > Reload UI` into a clean development reload that clears generated preview artifacts and project-local `__pycache__` directories before refreshing the desktop UI.

### Verification
- `python -m unittest tests.test_desktop_bridge`
- `python -m compileall desktop app tests`

## 2026-04-19 - tray-box-shell-v1-pass

### Summary
- Tightened the tray box family into a shallow open-top shell profile, updated the tray implementation id to `tray_box_shell_v1`, and preserved tray provenance through the backend pipeline and desktop bridge.

### Verification
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_alpha_pipeline`
- `python -m compileall app tests`

## 2026-04-19 - phone-stand-provenance-plumbing-fix

### Summary
- Preserved `generation_path`, `generation_route`, `execution_recipe`, `implementation_id`, `generation_fallback_reason`, and `output_source` through the desktop bridge so phone stand and other migrated recipe-path families no longer render their provenance as unavailable in the right-rail implementation panel.

### Verification
- `python -m unittest tests.test_desktop_bridge tests.test_backend_plan_schema tests.test_backend_archetypes`
- `python -m compileall app tests`

## 2026-04-19 - phone-stand-cradle-v1-structure-refinement

### Summary
- Refined the direct-body phone stand silhouette so the stand reads more clearly as a cradle with a flat base shelf, a distinct front lip, and a stepped support transition rather than a single wedge block.
- Raised the minimum visible lip height during validation so compact phone stands keep a readable retaining edge.

### Verification
- `python -m unittest tests.test_backend_plan_schema tests.test_backend_archetypes`
- `python -m compileall app tests`

## 2026-04-19 - phone-stand-cradle-v1-pass

### Summary
- Replaced the phone stand recipe path with a single coherent cradle-body construction for `phone_stand_cradle_v1`.
- Aligned phone stand defaults and validation around width, depth, height, thickness, viewing angle, lip height, and cradle depth while keeping the implementation stamp visible in logs, state, and the desktop UI.

### Verification
- `python -m unittest tests.test_backend_archetypes tests.test_backend_plan_schema tests.test_backend_alpha_pipeline tests.test_desktop_bridge`
- `python -m compileall app tests`

## 2026-04-18 - viewer-auto-fit-bounds-framing-pass

### Summary
- Auto-fit the Workspace camera to the actual bounds of loaded artifacts so real-world-sized models remain readable without changing model scale.
- Moved orbit target and camera placement onto the loaded object bounds for truthier framing across phone stands, plates, and enclosures.

### Verification
- `python -m unittest tests.test_viewer_framing tests.test_backend_alpha_pipeline tests.test_backend_archetypes tests.test_backend_plan_schema`
- `python -m compileall app desktop tests`

## 2026-04-18 - generation-truth-composition-hardening-pass

### Summary
- Reset generation-specific backend state at the start of each request so archetype and plan metadata do not leak between generations.
- Hardened `phone_stand` composition with a small structural anchor, stronger part overlap, and final transform normalization before export.
- Fixed plate normalization so `120 mm plate with 4 holes` infers a real hole count and default hole diameter instead of collapsing into a plain slab.

### Verification
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_backend_archetypes tests.test_backend_plan_schema`
- `python -m compileall app tests`

## 2026-04-18 - glb-path-normalization-viewer-load-fix

### Summary
- Normalized preview artifact paths into browser-safe file URLs before GLB loading.
- Exposed clearer preview-load errors when the expected artifact cannot be opened.

### Verification
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_backend_archetypes tests.test_backend_plan_schema`
- `python -m compileall app desktop tests`

## 2026-04-18 - viewer-glb-truth-pass

### Summary
- Made the Workspace viewer prefer the persisted final artifact and surface explicit load failures instead of silently substituting a procedural preview.
- Added final-artifact and preview-load metadata so preview, save, and reload stay honest about what was actually loaded.

### Verification
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_backend_archetypes tests.test_backend_plan_schema`
- `python -m compileall app desktop tests`

## 2026-04-18 - preview-output-unification-pass

### Summary
- Unified preview, saved-model persistence, and Blender-open behavior around a single final artifact path.
- Saved models now record the final output artifact alongside execution metadata so reloads and previews stay aligned.

### Verification
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_backend_archetypes tests.test_backend_plan_schema`
- `python -m compileall app tests`

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

## 2026-04-19 - backend-legacy-quarantine-pass

### Summary
- Simplified the active backend flow so migrated families stay recipe-authoritative and no longer drop into legacy geometry during normal operation.
- Quarantined legacy fallback to the remaining non-migrated primitive-assembly path, reducing overlap and making the active generation route easier to follow.

### Verification
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_backend_plan_schema tests.test_backend_archetypes`
- `python -m compileall app tests`

## 2026-04-19 - backend-authority-fallback-audit-pass

### Summary
- Tightened backend generation provenance so the deterministic recipe path is surfaced explicitly as the normal success route and legacy fallback is labeled when it is used.
- Hardened the legacy bracket fallback to boolean-fuse its flanges instead of leaving joined mesh islands behind.
- Added explicit generation-path metadata to backend state and saved-model entries so future debugging can tell which path built the artifact.

### Verification
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_backend_plan_schema tests.test_backend_archetypes`
- `python -m compileall app tests`

## 2026-04-18 - bracket-build-spec-v1-stabilization

### Files Changed
- `app/backend/plan_bridge.py`
- `app/backend/plan_validator.py`
- `app/backend/recipe_builder.py`
- `app/backend/recipe_executor.py`
- `tests/test_backend_alpha_pipeline.py`
- `tests/test_backend_plan_schema.py`
- `CHANGELOG.md`

### Summary
- Aligned the bracket recipe path with the v1 build spec by carrying flange width into the canonical vertical-leg feature, keeping the shared inner-corner frame coherent, clamping unsafe hole diameters earlier, and treating zero-hole bracket requests as a supported no-op in the recipe executor.

### Verification
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_backend_plan_schema`
- `python -m compileall app tests`

### Known Limitations
- Gussets remain disabled for `hole_count >= 4` during stabilization.

## 2026-04-18 - bracket-authoritative-frame-pass-1-2

### Files Changed
- `app/backend/recipe_builder.py`
- `app/backend/recipe_executor.py`
- `app/backend/geometry.py`
- `tests/test_backend_alpha_pipeline.py`
- `tests/test_backend_plan_schema.py`
- `CHANGELOG.md`

### Summary
- Rebased the deterministic bracket path onto a single inner-corner origin, aligned both flanges to that frame, and moved bracket hole cuts onto the joined object after union for a cleaner, coherent L-bracket.

### Verification
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_backend_plan_schema`
- `python -m compileall app tests`

### Known Limitations
- Gussets remain deferred for high-hole-count brackets to preserve stability.

## 2026-04-18 - bracket-stabilization-pass-1-1

### Files Changed
- `app/backend/recipe_builder.py`
- `app/backend/recipe_executor.py`
- `app/backend/geometry.py`
- `tests/test_backend_alpha_pipeline.py`
- `tests/test_backend_plan_schema.py`
- `CHANGELOG.md`

### Summary
- Reordered bracket construction so hole cuts happen before the final bracket union, removed the risky bracket bevel pass, and deferred gusset generation for high-hole-count brackets to keep the output exportable and coherent.

### Verification
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_backend_plan_schema`
- `python -m compileall app tests`

### Known Limitations
- High-hole-count brackets may temporarily omit gussets to preserve mesh stability.

### Rollback / Review Notes
- Revert the bracket recipe ordering, gusset guard, executor, and legacy geometry updates together to restore the prior more decorated path.

## 2026-04-18 - bracket-enrichment-pass-1

### Files Changed
- `app/backend/normalizer.py`
- `app/backend/plan_validator.py`
- `app/backend/geometry.py`
- `app/backend/recipe_executor.py`
- `tests/test_backend_alpha_pipeline.py`
- `tests/test_backend_plan_schema.py`
- `CHANGELOG.md`

### Summary
- Tightened the deterministic bracket path so bracket prompts now normalize and render with more believable mounting-bracket proportions, safer hole margins, optional gusset support, and a light bevel pass.

### Verification
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_backend_plan_schema`
- `python -m compileall app tests`

### Known Limitations
- This pass stays within the existing 90-degree bracket family and does not introduce angled or slotted variants.

### Rollback / Review Notes
- Revert the bracket normalization, validation, geometry, executor, and test updates together to restore the earlier blockier bracket output.

## 2026-04-18 - enclosure-open-top-fix-pass-1-1

### Files Changed
- `app/backend/normalizer.py`
- `app/backend/plan_bridge.py`
- `app/backend/recipe_builder.py`
- `app/backend/recipe_executor.py`
- `app/backend/geometry.py`
- `tests/test_backend_alpha_pipeline.py`
- `tests/test_backend_plan_schema.py`
- `CHANGELOG.md`

### Summary
- Adjusted the deterministic enclosure path so enclosure shells now normalize and generate as visibly open-top containers instead of leaving a top cap in solid view.

### Verification
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_backend_plan_schema`
- `python -m compileall app tests`

### Known Limitations
- The pass is limited to the existing enclosure shell family and does not add lids, rails, or other enclosure features.

### Rollback / Review Notes
- Revert the enclosure normalization, bridge, recipe, emitter, and geometry updates together to restore the prior closed-top read.

## 2026-04-18 - enclosure-shell-enrichment-pass-1

### Files Changed
- `app/backend/plan_bridge.py`
- `app/backend/plan_validator.py`
- `app/backend/recipe_builder.py`
- `app/backend/recipe_executor.py`
- `app/backend/geometry.py`
- `tests/test_backend_alpha_pipeline.py`
- `tests/test_backend_plan_schema.py`
- `CHANGELOG.md`

### Summary
- Tightened the deterministic enclosure shell path so the canonical plan carries base thickness through to generation and both the recipe and legacy Blender emitters build a clearer shell with a stable flat base, cavity depth derived from wall thickness, and light bevel softening.

### Verification
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_backend_plan_schema`

### Known Limitations
- This pass stays within the existing rectangular enclosure family and does not add lids, rails, bosses, or port features.
- Beveling is intentionally light and deterministic rather than a fully parametric hardware-grade edge treatment.

### Rollback / Review Notes
- Revert the enclosure bridge, validator, recipe, emitter, and test updates together to restore the earlier blockier shell behavior.

## 2026-04-18 - 0.7.56-alpha - archetype-phone-stand-structure-pass

### Files Changed
- `app/backend/archetypes.py`
- `app/backend/plan_bridge.py`
- `app/backend/plan_validator.py`
- `app/backend/recipe_builder.py`
- `app/backend/geometry.py`
- `tests/test_backend_archetypes.py`
- `CHANGELOG.md`

### Summary
- Tightened the `phone_stand` archetype so its defaults and canonical features now emphasize a flat base, angled support, and retaining lip instead of a generic tilted slab.
- Updated the recipe and fallback geometry to compose the stand from distinct structural parts with bounded optional cable-cutout behavior.

### Verification
- `python -m unittest tests.test_backend_archetypes tests.test_backend_alpha_pipeline tests.test_backend_plan_schema`

### Known Limitations
- Only the first archetype has been hardened this way.
- The phone-stand geometry remains intentionally simple and deterministic rather than feature-rich.

### Rollback / Review Notes
- Revert the archetype, canonical feature, recipe, and fallback geometry changes together to return to the earlier phone-stand shape.

## 2026-04-18 - 0.7.56-alpha - archetype-phone-stand-pass

### Files Changed
- `app/backend/archetypes.py`
- `app/backend/families.py`
- `app/backend/normalizer.py`
- `app/backend/plan_bridge.py`
- `app/backend/plan_validator.py`
- `app/backend/recipe_builder.py`
- `app/backend/recipe_executor.py`
- `app/backend/geometry.py`
- `app/backend/pipeline.py`
- `tests/test_backend_archetypes.py`
- `CHANGELOG.md`

### Summary
- Added the first archetype layer with a high-confidence `phone_stand` shortcut that feeds the canonical plan, recipe, executor, and legacy fallback paths.
- Preserved the existing family/generic generation behavior for non-phone-stand prompts while making the phone stand path deterministic and usable.

### Verification
- `python -m unittest tests.test_backend_archetypes tests.test_backend_alpha_pipeline tests.test_backend_plan_schema`

### Known Limitations
- Only `phone_stand` is currently routed through the archetype layer.
- Unknown prompts still rely on the existing family/generic path rather than a broader open-ended archetype system.

### Rollback / Review Notes
- Revert the archetype selector, phone-stand family additions, and backend pipeline hook together to disable the new shortcut without disturbing other generation paths.

## 2026-04-18 - 0.7.56-alpha - backend-recipe-executor-pass-3

### Files Changed
- `app/backend/recipe_executor.py`
- `app/backend/pipeline.py`
- `app/model_library.py`
- `app/state.py`
- `tests/test_backend_alpha_pipeline.py`
- `tests/test_backend_plan_schema.py`
- `CHANGELOG.md`

### Summary
- Added a bounded hybrid recipe executor that can render supported deterministic recipe ops into Blender Python for the current alpha families.
- Kept a safe legacy fallback path for unsupported recipe/object combinations and recorded the chosen execution path in state and saved-model metadata.
- Preserved current generation behavior while moving the recipe contract closer to the real execution layer.

### Verification
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_backend_plan_schema`
- `python -m compileall app tests`

### Known Limitations
- The executor is intentionally bounded and still falls back to the legacy family generator for unsupported combinations or future recipe expansions.
- No frontend changes were made in this pass.

### Rollback / Review Notes
- Revert the pipeline/executor/state/model-library changes together to return to the pre-pass hybrid bridge state.

## 2026-04-18 - 0.7.56-alpha - backend-recipe-builder-pass-2

### Files Changed
- `app/backend/recipe_schema.py`
- `app/backend/recipe_builder.py`
- `app/backend/pipeline.py`
- `app/model_library.py`
- `app/state.py`
- `tests/test_backend_plan_schema.py`
- `CHANGELOG.md`

### Summary
- Added a bounded deterministic recipe schema and builder between canonical plan validation and the existing family-shaped generator path.
- Converted validated canonical plans into explicit recipe ops for supported alpha families while preserving current generation behavior.
- Threaded recipe artifacts into saved model metadata and session state for inspection and future execution-layer work.

### Verification
- Backend unit tests will be run after the implementation pass.

### Known Limitations
- The current Blender/script execution path still consumes the existing family-shaped plan contract.
- Recipe execution remains bridged to the legacy generator path rather than replacing it.

### Rollback / Review Notes
- Revert `app/backend/pipeline.py`, `app/backend/recipe_*`, `app/model_library.py`, and `app/state.py` together if the recipe bridge needs to be isolated.

## 2026-04-17 - 0.7.56-alpha - backend-plan-schema-pass-1

### Files Changed
- `app/backend/plan_schema.py`
- `app/backend/plan_bridge.py`
- `app/backend/plan_validator.py`
- `app/backend/pipeline.py`
- `tests/test_backend_plan_schema.py`
- `CHANGELOG.md`

### Summary
- Added a canonical backend plan schema and validation layer between family normalization and deterministic generation.
- Bridged current family-specific normalized plans into the canonical plan structure without changing the successful generation path.
- Added focused tests for canonical bridge creation, validation success/failure, and pre-generation rejection of invalid canonical plans.

### Verification
- Backend unit tests to run after implementation.

### Known Limitations
- Current geometry generation still uses the established family-shaped plan after canonical validation.
- Canonical validation currently covers the supported alpha family/object subset only.

### Rollback / Review Notes
- Remove the canonical bridge and validator insertion from `app/backend/pipeline.py` to return to the prior flow.

## 2026-04-17 - 0.7.56-alpha - dark-mode-surface-token-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/app.js`
- `desktop/ui/styles.css`

### Summary
- Converted the Workspace theme switch to a `data-theme="dark"` surface-token theme rather than a simple class-based inversion.
- Introduced shared background, surface, panel, text, border, and viewer tokens so dark mode keeps a layered hierarchy across the top shell, Workspace panels, composer, footer, viewer, and runtime controls.
- Darkened the viewer canvas and reduced the glow intensity on buttons and controls so geometry remains legible without the surface feeling washed out.

### Verification
- `node --check desktop/ui/app.js`
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- A few secondary hardcoded neutrals still exist outside the main Workspace surfaces, but the core theme now reads from shared tokens and the most visible dark-mode surfaces are layered correctly.

### Rollback / Review Notes
- Review `desktop/ui/styles.css` and `desktop/ui/app.js`; the change is local to theme tokens and the Workspace shell surfaces.

## 2026-04-12 - 0.7.55-alpha - workspace-footer-controls-polish

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Replaced the top-right `Alpha / Review` chips with compact icon-only Workspace controls for new session, reset workspace, and a real theme toggle.
- Converted the prompt submit control from `Go` text to a compact send icon and reserved extra textarea space so the button does not collide with the scrollbar.
- Removed the footer `View plan` action and reorganized the right footer row into AI runtime, Blender runtime, version, and `Show logs`.
- Restyled the left footer status area as a flexible status strip so longer generation/status text remains stable and aligned.
- Added runtime pips that derive from existing runtime health, with calm teal pulse for connected/busy states and muted static indicators otherwise.

### Verification
- `node --check desktop/ui/app.js`
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Save was intentionally not added to the top controls because there is no existing supported save action to wire without inventing behavior.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js`; this pass is localized to Workspace shell controls, footer status presentation, and composer submit styling.

## 2026-04-12 - 0.7.54-alpha - templates-pass-2-card-polish

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Refined Templates copy from `Start from structured, reusable model blueprints.` to `Start from structured model blueprints.`
- Added a subtle helper line above the template grid without changing launch behavior.
- Replaced the generic template circle glyph with CSS-only geometric preview marks for brackets, enclosures, planters, clips, plates, and mechanical templates.
- Improved template card depth, hover lift, surface contrast, and sidebar active-category hierarchy.

### Verification
- `node --check desktop/ui/app.js`
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Template cards are still prompt starters only; no template parameter editor or authoring flow was added.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js`; this pass is visual/interactions-only for Templates.

## 2026-04-12 - 0.7.53-alpha - templates-pass-1-library-launch

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Replaced the Templates placeholder with a real first-pass template library mode using a left category sidebar and main template-card grid.
- Added template category filtering with one active category at a time.
- Added template cards with category labels, curated descriptions, and starter prompt launch behavior.
- Wired template launch to switch to Workspace, prefill the prompt composer, update the session title, and leave generation under user control.
- Used backend-provided `librarySummary.templates` when available, with a local fallback starter list for alpha stability.

### Verification
- `node --check desktop/ui/app.js`
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Templates are starter prompt definitions only; no parameter editor, tutorial flow, authoring, or marketplace behavior was added.
- Template launch preloads the Workspace prompt but does not auto-generate.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js`; this pass is scoped to Templates-mode browsing and launch behavior.

## 2026-04-12 - 0.7.52-alpha - projects-pass-2-controls-and-polish

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Added Projects header controls for `New Project` and `Select`, aligned to the same two-zone header pattern used by Models.
- Added session-local project creation through a lightweight project-name prompt and an empty-state `New Project` action.
- Added Projects selection mode with selection indicators, selected count, `Delete selected`, and `Cancel`.
- Refined project cards with denser grid sizing, compact metadata (`model count` plus updated date), stronger hover/selected states, and a more dimensional Geomancer-styled folder icon.

### Verification
- `node --check desktop/ui/app.js`
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- New projects are session-local UI state only; persistent project storage and model assignment are still postponed.
- Delete selected removes only user-created projects; saved-model-derived project groups remain because they are virtual library views.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js`; this pass is scoped to Projects controls, selection mode, and visual polish.

## 2026-04-12 - 0.7.51-alpha - projects-pass-1-browser-structure

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Replaced the Projects placeholder with a real first-pass Projects mode that shows a project-card overview and opens a selected project in place.
- Added project detail navigation with a Back control, project context header, and model grid for the models inside the selected project.
- Derived alpha-safe project containers from the existing saved-model library: an all-models project plus family-grouped project containers.
- Reused the existing Models card presentation for project-contained model browsing to keep the browsing language consistent without changing Models behavior.

### Verification
- `node --check desktop/ui/app.js`
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Projects are derived from saved models in UI state for PASS 1; no persistent project membership, rename, delete, or custom project creation flow was added.
- Templates remain a placeholder mode.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js`; this pass is scoped to Projects-mode structure and rendering.

## 2026-04-12 - 0.7.50-alpha - models-header-and-action-row-polish-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`

### Summary
- Reworked the Models header into a true two-zone tool header with `MODEL LIBRARY` plus subtitle grouped on the left and `Saved models` aligned on the right.
- Added a faint divider under the header so the selected-model summary and action area no longer visually blend into the page identity row.
- Normalized selected-model action button height, padding, radius, spacing, and text sizing so primary, secondary, tertiary, and utility actions share one compact rhythm.

### Verification
- `node --check desktop/ui/app.js`
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- This is intentionally a visual Models-only polish pass; no Projects/Templates structure was added.

### Rollback / Review Notes
- Review `desktop/ui/index.html` and `desktop/ui/styles.css`; the changes are limited to Models header and action-row presentation.

## 2026-04-12 - 0.7.49-alpha - models-select-mode-and-card-polish-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Compressed the Models header into a horizontal `MODEL LIBRARY` / `Saved models` row with the purpose subtitle retained beneath it.
- Added a dedicated Models selection mode with card/sidebar toggle selection, a stable selected-count label, `Delete selected`, and `Cancel`, keeping it separate from normal single-select browsing.
- Improved model card surface contrast, hover lift, title hierarchy, metadata quietness, and selected-state emphasis so saved models read more like tangible library items.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`
- `node --check desktop/ui/app.js`

### Known Limitations
- Bulk selection intentionally supports deletion only; no bulk open/export behavior was added.
- Models still use branded placeholder preview tiles when no persisted thumbnail asset exists.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js`; this pass is isolated to Models-mode header, selection mode, and card styling.

## 2026-04-12 - 0.7.48-alpha - models-selected-summary-polish-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Refined Models mode around a clearer page identity plus selected-model summary that shows the active model name, family, created time, and dimensions when available.
- Moved Models actions into the selected-model context so Open in Blender, Go to Workspace, and Delete model read as selection-tied controls rather than generic page actions.
- Strengthened selected states in both the main model grid and compact sidebar list while preserving the shared selected-model id and real saved-model data source.
- Improved Models search/no-results behavior by including dimensions in matching and using explicit no-results copy for search and family filters.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Models still use branded placeholder preview tiles when no dedicated thumbnail asset exists.
- Projects and Templates remain intentionally placeholder modes.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the behavior changes are limited to Models-mode selection, summary, and browsing polish.

## 2026-04-11 - 0.7.47-alpha - models-empty-state-and-sidebar-sync-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Fixed the Models empty-state bug by making the empty panel and the populated grid explicitly mutually exclusive based on real saved-model count.
- Added a compact sidebar list browser beneath the existing Models sidebar controls so the otherwise unused vertical space now supports fast scanning and selection.
- Kept selection unified between sidebar and grid by driving both from the same filtered model set and shared selected-model id.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The sidebar browser is intentionally compact and text-light; the main grid remains the primary visual browsing surface.
- This pass does not add new model actions or change Projects/Templates placeholders.

### Rollback / Review Notes
- Review `desktop/ui/app.js` first for the explicit empty-state visibility logic and shared selection handling, then `desktop/ui/index.html` and `desktop/ui/styles.css` for the sidebar browser structure and styling.

## 2026-04-11 - 0.7.46-alpha - models-cleanup-and-hierarchy-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`

### Summary
- Removed the remaining Models-only management framing by collapsing the old selection toolbar structure into the main library header and keeping actions compact and contextual.
- Tightened the library grid hierarchy so tiles read more like browseable files: larger preview anchors, quieter metadata, clamped names, wider gutters, and a stronger but still restrained selected state.
- Kept the sidebar, real model data, and existing model actions intact while making the overall Models screen read as one coherent visual library view.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Models still use branded placeholder preview tiles when no dedicated thumbnail asset exists.
- This pass does not add new model actions or change Projects/Templates placeholders.

### Rollback / Review Notes
- Review `desktop/ui/index.html` and `desktop/ui/styles.css` together; the cleanup is intentionally local to Models-mode structure and tile hierarchy.

## 2026-04-11 - 0.7.45-alpha - models-library-browser-refinement-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Reworked Models from a management-first screen into a content-first visual library by removing the dominant selected-model strip and promoting the saved-model tile grid to the main focus.
- Moved real model actions into a lighter contextual toolbar above the grid, where `Open in Blender` and `Delete model` now act on the current selection without dominating the screen.
- Refined model tiles into cleaner browser-style cards with stronger preview-area emphasis, quieter metadata, and a more natural single-click selection feel.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Models still use a branded placeholder preview tile when no persisted thumbnail exists because the library does not yet store thumbnail assets.
- Projects and Templates remain placeholders; this pass only refines Models presentation.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the refinement depends on the lighter toolbar, revised tile markup, and selection/action behavior staying aligned.

## 2026-04-11 - 0.7.44-alpha - workspace-models-mode-expansion-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `app/model_library.py`
- `desktop/backend_controller.py`
- `desktop/bridge.py`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Added a shell-level mode system so the persistent top navigation now switches between the existing Workspace and a new in-app Models view without leaving the desktop shell.
- Implemented a real Models mode backed by persisted saved-model entries, with search, sorting, family filters, selection, empty-state handling, deletion, and Blender-open support for selected saved entries.
- Kept Workspace mounted and behavior-stable while adding only light placeholder screens for Projects and Templates to establish the multi-mode pattern for later passes.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Models currently use tasteful placeholder tiles rather than generated thumbnails because the existing desktop library does not yet persist thumbnail assets.
- Projects and Templates remain placeholders in this pass; only Workspace and Models are real modes.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together for mode switching, then `app/model_library.py`, `desktop/backend_controller.py`, and `desktop/bridge.py` for the minimal saved-model data path additions.

## 2026-04-11 - 0.7.43-alpha - bottom-printability-and-footer-spacing-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Removed the one-off stacked treatment from the bottom `Printability` status row so all three rows now follow the same left-label/right-value layout.
- Shortened only the bottom printability wording where needed for fit, mapping `Review recommended` to `Needs review` and `Likely manageable` to `Manageable`.
- Opened the footer left cluster slightly by increasing chip-to-summary spacing and softening the summary text footprint so the status chip and sentence no longer read as visually glued together.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- This pass is intentionally tiny and does not change loading behavior, summary content structure, or any other workspace surface.
- Wording compaction is scoped to the bottom printability group only.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/app.js`, and `desktop/ui/styles.css` together; the cleanup depends on the status row no longer using the stacked class and the shorter labels landing in the same normalized row layout.

## 2026-04-11 - 0.7.42-alpha - workspace-fit-and-loading-polish-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Tightened the lower three-group summary band with cleaner internal alignment, more resilient label/value layout, and calmer spacing so longer values no longer crowd adjacent content.
- Refined the viewer footer/meta row with a clearer split between primary status and runtime/version metadata, fixed-width runtime/version footprints, and more deliberate spacing.
- Added restrained real generation-state polish driven only by the existing in-flight generation flag, including stable animated labels, a body-level generating state, and subtle in-place loading treatment across the viewer status, properties empty state, summary band, and footer.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- This pass is presentation-only; it does not introduce richer backend progress phases or any new interactivity.
- Loading treatment remains intentionally lightweight and tied to the existing desktop generation lifecycle rather than granular backend progress events.

### Rollback / Review Notes
- Review `desktop/ui/styles.css` first and `desktop/ui/app.js` second; the pass is intentionally localized to layout stability and real generation-state presentation.

## 2026-04-11 - 0.7.41-alpha - orientation-cube-basis-correction-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/app.js`

### Summary
- Fixed the orientation cube basis mapping so it now reflects the main viewer orientation inside the gizmo's own camera space instead of using only inverse(main camera) and ignoring the gizmo camera basis.
- Removed the trust-breaking mismatch where the cube could appear out of alignment with the staged model and stage orientation even though the main viewer camera itself was correct.
- Kept viewer interaction, generation flow, and the rest of the workspace unchanged.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- This pass fixes orientation correctness only; it does not redesign the gizmo visuals or add new gizmo interactivity.
- The cube remains a passive orientation aid rendered through its own overlay scene.

### Rollback / Review Notes
- Review `desktop/ui/app.js` first; the fix is isolated to the cube quaternion mapping in `updateAxisIndicator()`.

## 2026-04-11 - 0.7.40-alpha - right-rail-actions-separation-and-hierarchy-polish

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/styles.css`

### Summary
- Restored the right-rail `Actions` area as its own soft visual container so next-step controls read separately from the read-only `Properties` content.
- Tightened right-rail hierarchy with smaller section labels, denser property rows, slightly reduced padding, and cleaner value alignment.
- Lightly refined lower-band hierarchy by giving `Printability` slightly stronger emphasis and keeping `Mesh` more muted without changing the existing grouped content structure.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- This pass is styling-only; it does not change any data bindings, interaction flow, or action availability.
- The properties rail remains read-only except for the existing working action button.

### Rollback / Review Notes
- Review `desktop/ui/styles.css` first; the pass is intentionally CSS-first so behavior stays unchanged.

## 2026-04-10 - 0.7.39-alpha - truthful-properties-and-bottom-band-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Reworked the right rail into a truthful read-only `Properties` panel that only shows real generated dimensions, wall thickness, and feature rows when that information exists.
- Replaced the lower four-part operational strip with three more user-facing groups for `Model info`, `Printability`, and `Mesh`, removing internal-only fields such as recipe and confidence from the primary summary surface.
- Moved runtime emphasis into the footer by relocating AI/Blender status and logs access there while preserving the existing working actions and generation flow.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The properties panel remains read-only in this pass; no editing affordances were introduced because those controls are not yet real.
- Mesh/export guidance is still alpha-level and derived from current preview and Blender readiness signals rather than a full export pipeline model.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the properties layout, conditional rendering, and lower-band data landing are designed to ship as one coherent UI pass.

## 2026-04-10 - 0.7.38-alpha - safe-ui-styling-polish-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/styles.css`

### Summary
- Softened the lower four-part rail so it feels like a lighter integrated workspace band instead of a heavy dashboard strip.
- Tightened the right rail with smaller type, reduced padding, softer dividers, and stronger overflow protection while keeping the same `Model`, `Key features`, `Printability`, and `Actions` structure.
- Fixed footer status jitter by giving the animated generation chip a true fixed footprint so dot animation no longer shifts adjacent text.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- This pass is styling-only; it does not change data bindings, interaction design, or the right rail content model.
- Viewer, chat, runtime setup, and generation flows remain unchanged by design.

### Rollback / Review Notes
- Review `desktop/ui/styles.css` first; the pass is intentionally concentrated in styling so behavior can be preserved.

## 2026-04-10 - 0.7.37-alpha - ui-semantics-and-hierarchy-refinement-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `desktop/ui/index.html`
- `desktop/ui/app.js`

### Summary
- Refined the lower strip semantics so it behaves more clearly as a fast operational glance surface, with `Readiness`, `Dimensions`, `Model`, and `Attention` replacing muddier telemetry-like wording.
- Tightened the right rail into a more user-facing model-understanding panel by improving the model description tone, reducing feature dump behavior, and keeping printability advisory rather than overconfident.
- Lightened the actions section language so it feels more intentional and less weighed down by passive future-state phrasing.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Model descriptions and feature prioritization are still driven by lightweight heuristics over the current normalized plan rather than a richer authored summary object.
- The lower strip still surfaces some technical readiness signals because the desktop shell remains a local-first alpha product.

### Rollback / Review Notes
- Review `desktop/ui/index.html` and `desktop/ui/app.js` together; the stronger responsibility split depends on the lower-strip labels, right-rail wording, and shared printability/review summaries moving in the same direction.

## 2026-04-09 - 0.7.36-alpha - ui-state-language-and-animation-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Replaced repeated placeholder wording such as `Pending` with clearer idle-state language like `Waiting` and `—` across the lower telemetry strip and right rail.
- Added a lightweight animated ellipsis loop during generation so generation, analysis, normalization, feature extraction, and printability evaluation states feel active without adding heavy loaders.
- Refined idle and generating copy in the right rail so the model, key-features, and printability sections read more intentionally before and during generation.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The animation is intentionally text-only and subtle; it does not attempt richer progress estimation or phase tracking from the backend.
- Some backend-driven phrases such as family detection chat updates remain factual/log-like rather than fully product-polished copy.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the updated wording and animated ellipsis behavior depend on the fallback HTML copy, multiline description styling, and generation-state animation loop working together.

## 2026-04-09 - 0.7.35-alpha - right-rail-printability-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/app.js`

### Summary
- Added a new `Printability` section to the right rail between `Key features` and `Actions`.
- Derived lightweight advisory printability rows from current normalized plan and validation signals, including `Status`, `Base contact`, `Overhang risk`, `Thin features`, and `Note`.
- Kept the wording intentionally advisory, using phrases like `Likely printable`, `Review recommended`, and `Needs support review` instead of absolute fabrication claims.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Printability guidance is still a heuristic alpha estimate, not a slicer, structural analysis, or manufacturing validator.
- The section depends on currently available plan keys and validation warnings, so richer fabrication guidance will improve as model metadata grows.

### Rollback / Review Notes
- Review `desktop/ui/index.html` and `desktop/ui/app.js` together; the new right-rail printability section depends on the inserted section markup and the heuristic row generation landing together.

## 2026-04-09 - 0.7.34-alpha - right-rail-deduplication-pass

### Files Changed
- `CHANGELOG.md`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Removed duplicated telemetry fields from the right rail so family, recipe, state, confidence, and repeated dimensions remain exclusive to the lower system strip.
- Replaced the old model-overview rows with a short human-readable model description derived from the current normalized plan.
- Merged the upper inspection content into a single `Key features` section that only shows meaningful non-duplicated model attributes.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The descriptive summary remains heuristic and depends on whichever normalized feature keys are currently available in the plan.
- The right rail still does not offer editing controls; it remains a read-only understanding and inspection surface.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the deduplicated right-rail behavior depends on the new summary markup, compact feature row styling, and description/key-feature mapping working as one pass.

## 2026-04-09 - 0.7.34-alpha - right-rail-model-details-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Reworked the right rail from a dimensions-first facts panel into a model-details panel led by model overview, conditional details, and openings/holes.
- Replaced the repeated top dimensions section with overview fields for family, recipe, state, and confidence so the rail answers what Geomancer made before listing deeper inspection data.
- Reduced weak placeholder noise by only surfacing family-specific detail rows when they are meaningful and leaving the lower actions area intact.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Detail rows still depend on currently available normalized plan keys, so richer family-specific inspection data will improve as backend plan structure grows.
- The right rail remains read-only in this pass; it is a clearer inspection surface, not yet an editable model-properties panel.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the improved right-rail content model depends on the markup, compact row styling, and plan-to-panel mapping changing as one pass.

## 2026-04-09 - 0.7.33-alpha - orientation-cube-framing-and-teal-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Prevented lower-right orientation cube clipping by widening the gizmo slot slightly, increasing the render size, and pulling the mini-scene camera back with a slightly wider field of view.
- Shifted the cube's materials toward Geomancer teal with a softer cyan top face, lightly teal-influenced neutral side faces, and brighter teal edge lines.
- Added a restrained halo treatment through a slightly richer CSS glow plus a subtle teal rim light inside the gizmo scene.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The orientation cube remains a passive viewer aid and still does not expose click-to-snap view controls.
- Glow treatment stays intentionally subtle, so the premium halo is still dependent on the live renderer rather than strong post-processing.

### Rollback / Review Notes
- Review `desktop/ui/styles.css` and `desktop/ui/app.js` together; the clipping fix depends on the CSS slot sizing, mini-scene camera framing, and material/light tuning changing as one pass.

## 2026-04-09 - 0.7.32-alpha - real-3d-orientation-cube-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Removed the flat DOM-style orientation cube implementation and replaced it with a real miniature Three.js scene rendered in the lower-right viewer corner.
- Built the new gizmo as an actual shaded cube mesh with crisp edge lines, premium neutral materials, and a restrained teal-accented top face so it reads as a true 3D object instead of a rotating sticker.
- Kept the background tile removed and synchronized the gizmo cube directly from the main viewer camera quaternion so the orientation aid reflects the active view correctly.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The real 3D cube remains passive in this pass and still does not support interactive click-to-snap view changes.
- The mini-scene uses lightweight shading and edge lines rather than labeled faces to keep the gizmo compact.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the old DOM cube was intentionally removed and replaced with a separate renderer, scene, camera, and cube mesh.

## 2026-04-09 - 0.7.31-alpha - orientation-cube-depth-restoration-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/styles.css`

### Summary
- Restored the lower-right orientation cube's dimensional read by increasing its size slightly, deepening the face offsets, and strengthening top/side face separation.
- Kept the cube freestanding with no visible background tile while using only a subtle ambient glow and shadow to support the 3D read.
- Increased edge and face contrast so the top, front, and side planes remain legible at the cube's small viewer-corner size.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The cube remains a passive orientation aid and still does not expose click-to-snap camera controls.
- Labeling is still intentionally minimal, so the 3D read depends mostly on face contrast and camera-linked rotation.

### Rollback / Review Notes
- Review `desktop/ui/styles.css` alongside the existing cube markup and rotation behavior in `desktop/ui/index.html` and `desktop/ui/app.js`; this pass is a styling-only refinement of the freestanding cube.

## 2026-04-09 - 0.7.30-alpha - geomancer-orientation-cube-refinement-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/styles.css`

### Summary
- Removed the visible square plate behind the lower-right orientation cube so the gizmo stands on its own instead of reading like a floating dice button.
- Restyled the cube with sharper edges, tighter radii, subtler neutral faces, and restrained teal emphasis on the front and top faces so it better matches Geomancer's geometric brand language.
- Kept the same placement, compact footprint, and camera-linked rotation while making the orientation aid feel more precise and less playful.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The cube remains display-only and still does not provide click-to-snap camera interactions.
- Face labels are still present, just lighter and more restrained than the previous pass.

### Rollback / Review Notes
- Review `desktop/ui/styles.css` together with the existing cube markup and rotation logic in `desktop/ui/index.html` and `desktop/ui/app.js`; this pass is intentionally a styling-only refinement of the new orientation cube.

## 2026-04-09 - 0.7.29-alpha - orientation-cube-gizmo-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Replaced the lower-right line-based XYZ widget with a compact orientation cube that better matches Geomancer's geometric brand language.
- Rebuilt the gizmo styling around a softer frosted corner pad, translucent cube faces, restrained teal accents, and calmer shading instead of primary RGB axis bars.
- Kept the orientation aid linked to camera movement by rotating the cube from the active camera quaternion each frame.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The orientation cube is display-only in this pass; it does not yet support click-to-snap view interactions.
- Face labels are intentionally minimal and remain small to keep the cube unobtrusive.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the lower-right gizmo replacement depends on the markup, cube styling, and camera-linked transform logic changing as one pass.

## 2026-04-09 - 0.7.28-alpha - viewer-overlay-premium-polish-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Kept the top-left viewer status card permanently visible and updated the ready state so it continues to provide guidance instead of disappearing after preview load.
- Replaced the lower-left Play / Pause text control with a compact icon-based auto-orbit toggle while preserving paused-by-default behavior and manual-interaction suppression.
- Refined the orbit puck, left-side viewer controls, and corner XYZ gizmo with calmer frosted materials, tighter shadows, and cleaner overlay styling.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The auto-orbit toggle still uses simple glyph icons rather than custom product artwork.
- Overlay polish in this pass is visual and behavioral only; it does not change viewer generation, framing, or geometry logic.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the persistent status surface, icon toggle behavior, and overlay material polish are one coordinated viewer pass.

## 2026-04-08 - 0.7.27-alpha - viewer-control-overlay-and-teal-polish-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Added restrained teal accents to the four-column instrument strip by shifting headings and row labels slightly toward Geomancer teal while keeping values dark and readable.
- Moved the Orbit / Pan / Zoom controls into the viewer as a left-side overlay stack and returned the XYZ gizmo to the conventional lower-right corner inside the viewer.
- Added a lower-left Play / Pause viewer button that controls slow auto-orbit around the model, with the default state paused.
- Manual viewer interaction now disables auto-orbit so the camera never fights the user.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Auto-orbit is still a lightweight camera convenience built on top of orbit controls rather than a richer cinematic viewer mode.
- The overlay controls use text labels rather than custom icon artwork in this pass.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the overlay control placement, teal strip polish, and auto-orbit behavior are one coordinated viewer pass.

## 2026-04-08 - 0.7.26-alpha - info-strip-instrument-panel-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Simplified the four strip headings to `System`, `Dimensions`, `Generation`, and `Review`.
- Reworked the strip content into cleaner label-value rows, replaced the weaker volume/wall placeholder rows with more useful generation facts, and reduced repeated `Unavailable` style wording in favor of `Pending`, `N/A`, and concrete generation/review states.
- Softened the visual separation so the strip reads as one compact instrument band with lighter headings, subtler separators, tighter spacing, and stronger value emphasis.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Generation facts still come from currently available plan metadata and lightweight UI derivation rather than a richer backend summary object.
- Triangles remain `Not measured yet` because the viewer still does not compute mesh triangle counts for the instrument strip.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the new strip wording and hierarchy depend on the markup, styling, and data wiring changing as one pass.

## 2026-04-08 - 0.7.25-alpha - viewer-status-footer-consolidation-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Removed the separate top generation-status strip above the viewer to return that vertical space to the preview area.
- Rebuilt the bottom viewer footer as the single compact meta band, with generation status, concise summary text, and a lighter inline `View plan` action on the left, plus right-aligned version text on the right.
- Kept the existing viewer controls row, info strip, and surrounding panel layout intact while tightening footer summary text for one-line footer use.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- `View plan` remains a lightweight placeholder action and is still disabled until a fuller plan surface is introduced.
- Footer summaries are shortened conservatively for layout fit rather than semantically rewritten from richer generation metadata.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the footer consolidation depends on the markup move, lighter footer styling, and retained status bindings working together.

## 2026-04-08 - 0.7.24-alpha - viewer-corner-gizmo-offset-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/styles.css`

### Summary
- Moved the viewer's bottom-right XYZ gizmo upward by increasing the lower HUD offset so the bars no longer clip against the bottom edge of the viewer.
- Kept the gizmo styling, behavior, and viewer layout unchanged aside from the vertical repositioning.

### Verification
- `python -m compileall app desktop tests`

### Known Limitations
- This pass only changes the gizmo offset; it does not change gizmo size, rendering, or camera coupling.
- Final visual fit is still best checked in the live desktop shell.

### Rollback / Review Notes
- Review `desktop/ui/styles.css` only; this is a single-position adjustment for the viewer HUD anchor.

## 2026-04-08 - 0.7.23-alpha - stacked-session-header-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`

### Summary
- Reworked the conversation header into a stacked two-line treatment with `Session` on the first line and the dynamic session title on the second line.
- Added single-line truncation behavior with ellipsis for both the session label and title so long project names no longer force width pressure in the left rail.
- Reduced the visual weight of the stacked title treatment and added a faint divider beneath the header to separate it from the conversation thread without changing the rest of the panel.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The title still derives directly from prompt text rather than richer generation metadata.
- This pass only changes the visual header arrangement; it does not change title-generation logic or session behavior.

### Rollback / Review Notes
- Review `desktop/ui/index.html` and `desktop/ui/styles.css` together; this is a contained presentation pass on the conversation header block.

## 2026-04-08 - 0.7.22-alpha - dynamic-session-title-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Replaced the static conversation header title with the new `Session • <dynamic title>` treatment.
- Added a lightweight session-title generator that strips common measurement prefixes, normalizes whitespace, limits length, converts to title case, and falls back to `Untitled` when there is no usable prompt.
- Stored the active session title in memory and updated it on prompt submission, active-session application, and session reset so the header stays aligned with the current generation flow.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Session titles are derived from prompt text only and do not yet use richer backend plan/family information for refinement.
- Long prompts are truncated conservatively rather than semantically summarized.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the visual header treatment and title-generation logic are one connected pass.

## 2026-04-08 - 0.7.21-alpha - composer-toolbelt-and-prompt-improver-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Added a compact composer toolbelt beneath the existing prompt input without changing the established textarea-plus-Go layout.
- Introduced three left-side tool buttons: disabled image-to-model and voice-prompt placeholders with coming-soon tooltips, plus an active improve-prompt control.
- Added a lightweight prompt-improver modal that reads the current prompt, generates a clearer suggested Geomancer prompt, and lets the user use the suggestion or keep the original text.
- Added a right-side quick settings menu with clear conversation, auto-scroll, and timestamp toggles while preserving the existing thread-only scrolling behavior.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The prompt improver currently uses a local UI-side suggestion builder rather than a backend-powered prompt-quality model.
- Image and microphone actions are presentation placeholders only and remain disabled for this alpha pass.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the toolbelt, prompt-improver modal, and quick menu are one coordinated composer pass.

## 2026-04-08 - 0.7.20-alpha - conversation-thread-scroll-fix

### Files Changed
- `CHANGELOG.md`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`

### Summary
- Added a dedicated `conversation-thread-region` wrapper so the message history owns the only vertical scrollable region inside the left rail.
- Reinforced flex sizing and `min-height: 0` behavior between the fixed header, flexible thread region, and fixed composer so the chat history shrinks and scrolls instead of overflowing visually.
- Removed row-level overflow clipping and kept normal vertical message stacking so bubbles no longer cut off or appear to overlap after longer generation runs.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- This pass only fixes thread containment and scrolling behavior; it does not add virtualized chat rendering or deep history management.
- Live desktop confirmation is still the final check for exact scroll feel and long-thread behavior.

### Rollback / Review Notes
- Review `desktop/ui/index.html` and `desktop/ui/styles.css` together; the fix depends on the new wrapper and the corresponding flex/overflow rules landing as one change.

## 2026-04-08 - 0.7.20-alpha - chat-bubble-shadow-tightening-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/styles.css`

### Summary
- Tightened the chat bubble shadow treatment so assistant and user bubbles read crisper and less diffuse without changing the conversation layout, spacing, or input structure.
- Kept the polish isolated to the bubble surface itself instead of altering the broader panel or card shadow system.

### Verification
- Visual CSS refinement only

### Known Limitations
- This pass does not change chat behavior, layout, or avatar sizing.
- Final perception of the shadow still depends on the live desktop shell and monitor contrast.

### Rollback / Review Notes
- Review `desktop/ui/styles.css` only; this is a small isolated presentation pass on the chat bubble shadow stack.

## 2026-04-08 - 0.7.19-alpha - chat-ui-polish-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Replaced the placeholder Geomancer text avatar with the real chat icon asset and kept assistant bubbles top-aligned so the avatar reads as the speaker anchor at the upper-left of the message.
- Tightened the conversation thread for vertical-only scrolling, added stronger line wrapping safeguards, and blocked horizontal overflow so the left panel behaves like a clean product chat surface.
- Upgraded the new-conversation header control from a plain circular plus button to a more deliberate premium action button while preserving its position and behavior.
- Kept the restored composer structure unchanged from the previous pass and left the example prompts embedded in Geomancer's opening message rather than reintroducing chips near the input area.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- This pass improves the visual polish of the conversation rail but does not add richer chat behaviors such as resend, editing, or contextual message menus.
- Live desktop confirmation of the final avatar sizing and overflow behavior still depends on launching the Qt shell; the automated checks here only verify static assets and script integrity.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the header polish, avatar rendering, and overflow behavior are one coordinated chat UI pass.

## 2026-04-08 - 0.7.18-alpha - conversation-polish-and-input-restore-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Kept the new chat-style left rail but corrected the Geomancer speaker presentation so the avatar now anchors to the top-left of each Geomancer bubble instead of reading like a footer attachment.
- Removed the lower composer suggestion chips and restored the prompt area to the simpler stable input-plus-Go layout so the tool zone remains familiar and compact.
- Moved the example prompts into Geomancer's second startup message using the requested opening copy, and rendered those examples as clickable chips directly inside the message bubble.
- Kept timestamps, left/right message alignment, and auto-scroll-to-latest behavior intact while switching prompt-chip interaction over to the conversation thread itself.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The conversation thread is still an alpha UI surface and does not yet support richer message actions beyond prompt-chip insertion.
- Prompt chips currently populate the composer and focus it; they do not auto-submit or branch into a deeper guided prompt flow yet.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the composer restore, avatar alignment, and embedded startup chips are one coordinated UI pass.

## 2026-04-08 - 0.7.17-alpha - conversation-panel-chat-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Replaced the static left-rail workflow cards with a real conversation thread that renders timestamped Geomancer and user messages as compact bubbles while keeping the existing workspace layout intact.
- Seeded the thread with startup readiness messages when runtime health is complete, moved prompt examples down beside the composer, and kept the prompt composer pinned to the bottom of the panel.
- Routed existing setup actions, user submissions, family detection, normalization summaries, AI setup progress, and final generation outcomes into the chat thread so the left rail now behaves like a live product conversation instead of a stack of static cards.
- Added automatic scroll-to-latest behavior for new messages and escaped rendered message content so user prompts and system text are safe to display in the bubble renderer.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The conversation rail is still an alpha presentation surface; it does not yet support clarifying follow-up turns, message actions, or persistent multi-session chat history.
- System logs remain separate in the modal and are not yet summarized into structured conversation events beyond the setup and generation milestones already wired.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; the new conversation panel depends on the markup, bubble styling, and message/event routing changing as one pass.

## 2026-04-08 - 0.7.16-alpha - dominant-face-frame-pose-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/app.js`

### Summary
- Replaced the PCA-first candidate-basis generation with a dominant-face-frame approach for the generic preview pose solver.
- Triangle normals are now sampled across the mesh, weighted by face area, and clustered by sign-insensitive directional similarity so the viewer can recover the major planar directions present in engineered geometry.
- The pose solver constructs a stable orthogonal presentation frame from the strongest dominant face directions and uses that as the primary candidate basis, while falling back to PCA when face evidence is too weak or not sufficiently orthogonal.
- Candidate scoring now includes structural readability terms that reward strong axis alignment, orthogonal face structure, and broad dominant-face coverage alongside the existing grounding and balance terms.
- The downstream pipeline remains intact after candidate selection: grounding, support/contact centering, conservative leveling, shadow placement, and framing still run as before.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Dominant-face clustering is still a lightweight viewer-side heuristic based on sampled triangle normals rather than exact semantic surface classification.
- Highly organic or weakly planar meshes may still fall back to PCA and therefore retain more generic presentation behavior.

### Rollback / Review Notes
- Review `desktop/ui/app.js` together; face clustering, frame construction, PCA fallback, and structural readability scoring are one connected policy change.

## 2026-04-08 - 0.7.15-alpha - conservative-leveling-and-dominant-face-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/app.js`

### Summary
- Removed the aggressive full support-plane snap introduced in `0.7.14-alpha` and replaced it with a conservative final leveling pass.
- Dominant resting surfaces are now detected from near-bottom mesh triangles using a blend of area, near-horizontal normal alignment, and proximity to the grounded bottom band.
- Final leveling only runs when the dominant surface evidence is strong and the required correction is already small; otherwise the generic PCA/candidate pose is left unchanged.
- Added explicit guardrails that discard a proposed correction if it exceeds the maximum allowed angle or materially worsens height, footprint, or support balance.
- Kept the generic pose solver, grounding, support/contact centering, shadow placement, framing, and corner gizmo architecture intact.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Dominant-surface detection is still a lightweight viewer heuristic based on sampled triangles near the bottom of the mesh rather than exact semantic face classification.
- This pass only affects viewer presentation and does not change backend geometry generation or Blender output.

### Rollback / Review Notes
- Review `desktop/ui/app.js` as one unit; the rollback from hard plane snap to guarded dominant-surface leveling depends on the scoring, correction, and rejection logic working together.

## 2026-04-08 - 0.7.14-alpha - support-plane-snap-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/app.js`

### Summary
- Replaced the previous timid micro floor-squaring behavior with a true support-plane snap after generic pose selection.
- Tightened support-point selection so the fitted support plane is derived from a stricter dominant low-contact band instead of a broad noisy lower slice, which better matches planar-bottom parts such as plates and panels.
- After snapping the support plane normal to world up, the viewer now re-grounds by bounding-box minimum Y and re-centers from the refreshed support/contact footprint before shadow placement and framing continue.
- Removed the large in-scene `AxesHelper`, leaving the fixed corner XYZ gizmo as the single orientation aid.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Support-plane snap is still based on sampled support geometry rather than exact mesh-face semantics, so unusual bottoms can still need later refinement.
- The corner gizmo remains a DOM/CSS overlay driven by camera orientation, not a 3D inset scene.

### Rollback / Review Notes
- Review `desktop/ui/app.js` as one cohesive change; support-point selection, plane fitting, snap rotation, and helper cleanup all contribute to the final planted look.

## 2026-04-08 - 0.7.13-alpha - floor-squaring-and-axis-gizmo-fix

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Kept the generic principal-axis pose solver and added a tightly clamped post-pose floor-squaring correction so previews lose small residual pitch/roll lean without entering a new pose-selection loop.
- Floor squaring now fits a lightweight support plane from the grounded support slice, applies a tiny corrective rotation only for micro-tilt, then re-grounds and re-centers the preview before shadow and framing continue.
- Rebuilt the corner orientation aid as a clearer fixed XYZ-line gizmo with a shared origin marker and larger desktop-readable sizing instead of the previous undersized corner treatment.
- Preserved the existing layout, viewer size, and generic pose-selection architecture.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Floor squaring is still a lightweight presentation correction derived from sampled support geometry rather than a full contact solver.
- The corner gizmo remains a DOM/CSS overlay driven by camera orientation, not a separate 3D inset scene.

### Rollback / Review Notes
- Review `desktop/ui/app.js`, `desktop/ui/styles.css`, and `desktop/ui/index.html` together; the lean correction and gizmo clarity rely on the logic and markup changes working together.

## 2026-04-08 - 0.7.12-alpha - contact-weight-and-axis-helper-polish

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/app.js`
- `desktop/ui/styles.css`

### Summary
- Kept the generic principal-axis preview pose solver from `0.7.11-alpha` and added a small post-pose settling pass so the visible support region reads more flush with the floor.
- Tightened contact-shadow sizing and opacity so grounded parts feel slightly more planted without making the viewer heavier or more dramatic.
- Removed the old circular corner-axis badge styling and replaced it with a cleaner fixed XYZ-line helper that still rotates with camera motion.
- Preserved the existing layout, generic pose-selection architecture, and final grounding/contact/shadow/framing pipeline.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The final settling pass is still a lightweight presentation correction driven by support-slice metrics rather than a physically accurate contact solver.
- The corner orientation aid remains a CSS/DOM overlay driven from camera orientation, not a separate inset 3D scene.

### Rollback / Review Notes
- Review `desktop/ui/app.js` and `desktop/ui/styles.css` together; the final contact read depends on both the settling/shadow logic and the lighter axis-helper presentation.

## 2026-04-08 - 0.7.11-alpha - generic-preview-pose-solver-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/app.js`

### Summary
- Replaced the family-specific preview pose rules with a generic deterministic viewer-side pose solver.
- Added principal-axis normalization by sampling representative mesh vertices, computing a covariance matrix, and extracting a stable PCA-like basis for the preview object.
- The viewer now evaluates six generic grounded candidate poses from that basis: `+X up`, `-X up`, `+Y up`, `-Y up`, `+Z up`, and `-Z up`.
- Candidate selection now uses blended presentation scoring based on support footprint quality, projected center balance over support, grounded height, and silhouette spread instead of family-specific hardcoded pose policies.
- Kept the existing final pipeline intact after pose selection: floor grounding, support/contact centering, contact shadow placement, and camera framing still run on the winning pose.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The principal-axis solver is still a lightweight viewer heuristic and may need further refinement for highly symmetric or visually ambiguous meshes.
- This pass only affects desktop preview presentation and does not alter backend geometry generation or Blender output.

### Rollback / Review Notes
- Review `desktop/ui/app.js` together; the PCA basis extraction, generic candidate generation, and pose scoring are a single coupled policy shift.

## 2026-04-08 - 0.7.10-alpha - orientation-heuristic-rollback-and-family-pose-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/app.js`

### Summary
- Rolled back the overly aggressive orientation search for sensitive preview families and replaced it with a more restrained presentation-first pose policy.
- Constrained `clip`, `bracket`, `hook`, and `adapter`-style previews to family-specific candidate sets that mainly preserve the authored upright pose and only allow limited yaw-style presentation variants.
- Added upright-readability weighting, pose-alignment weighting relative to the base pose, and family-specific guardrails that heavily penalize or reject side-lying and overly tipped candidates.
- Kept the existing post-selection pipeline intact: bounding-box grounding, support/contact centering, shadow placement, and camera framing still run after pose selection.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Presentation pose selection is still heuristic and preview-family driven rather than based on deeper semantic understanding of functional faces.
- This pass only affects the desktop preview viewer and does not change backend geometry generation or Blender output.

### Rollback / Review Notes
- Review `desktop/ui/app.js` together; the candidate set restriction, readability scoring, and guardrails are designed as one policy change.

## 2026-04-08 - 0.7.9-alpha - resting-orientation-and-floor-contact-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/app.js`

### Summary
- Added a deterministic resting-orientation normalization pass before grounding and framing in the desktop viewer.
- The viewer now evaluates a small candidate rotation set around the current orientation, computes support quality from a lower support slice, and selects the orientation with the strongest believable resting footprint.
- Added lightweight family-aware tie bias so flat parts prefer natural broad support while clips, brackets, and similar parts favor practical support faces.
- Preserved the existing support-aware grounding, contact shadow, floor stability, and camera framing pipeline after orientation normalization.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Resting orientation is still chosen from a small heuristic candidate set, so unusual shapes may still need later tuning.
- This pass only affects desktop preview presentation and does not change backend geometry generation or Blender output.

### Rollback / Review Notes
- Review `desktop/ui/app.js` together; the orientation selection, support scoring, and post-orientation grounding pipeline are intentionally connected.

## 2026-04-08 - 0.7.8-alpha - stage-contact-and-shadow-stability-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/app.js`

### Summary
- Kept the existing bounding-box grounding sequence, then improved resting placement by sampling a lower support slice of the preview geometry and centering from that support footprint when available.
- Updated the contact shadow to size and position from the support footprint instead of the full object bounds, which gives offset parts such as clips a more believable resting read on the stage.
- Simplified and stabilized the floor stack by removing a redundant shadow-catching layer, separating render-order responsibilities across the floor, halo, contact shadow, and grid, and disabling depth writes on the transparent floor overlays.
- Kept the existing viewer size and layout changes from `0.7.7-alpha` intact.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Support-aware centering is still a lightweight sampled heuristic from preview vertices, so unusual meshes can still need later tuning.
- This pass improves stage stability in the desktop preview scene only; it does not change Blender output or backend geometry behavior.

### Rollback / Review Notes
- Review `desktop/ui/app.js` in one pass; the placement, camera-target, and floor-layer changes are intentionally coupled.

## 2026-04-08 - 0.7.7-alpha - viewer-dominance-and-grounding-fix

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Compressed the viewer chrome so the model occupies more of the workspace: the generation bar is thinner, the viewer toolbar is lighter, and the bottom summary area now reads as a compact telemetry strip instead of a dashboard.
- Tightened info-strip typography and spacing, shortened several labels, removed non-essential explanatory copy from the primary view, and kept the four-section structure intact.
- Corrected preview grounding by lifting each loaded object so its lowest bounding-box point sits exactly on the floor, recentering it horizontally at the origin, and keeping the contact shadow fixed on the floor plane.
- Adjusted camera targeting to use a lower-biased focal point based on model height rather than the raw geometric center, which makes framing feel more grounded.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Grounding and framing still rely on preview-scene heuristics and bounding boxes rather than semantic geometry anchors.
- The compact telemetry strip intentionally favors glanceable data over explanation, so richer review detail still needs a later dedicated surface.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; this pass depends on the layout density and grounding logic changing in tandem.

## 2026-04-08 - 0.7.6-alpha - viewer-grounding-and-presentation-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Refined the desktop viewer presentation without changing the corrected workspace layout.
- Added a stronger but still minimal stage floor, contact shadow treatment, and floor placement logic so preview objects sit cleanly in space instead of feeling detached from the scene.
- Removed automatic preview spin and introduced more deliberate, deterministic first-load framing with lightweight family-aware camera profiles for flatter parts, box-like parts, and depth-sensitive parts.
- Reduced overlay weight around the viewer, tightened the generation bar styling, and polished the orbit puck and XYZ orientation indicator so the model remains the visual focus.
- Updated empty, generating, and ready viewer messaging to use lighter product-facing language.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Viewer framing remains heuristic and preview-kind driven; it is not yet based on richer geometry semantics or saved camera presets.
- Grounding improvements currently affect the desktop preview scene only and do not change backend-generated geometry or Blender output.
- The orientation aid is still a lightweight overlay rather than a full inset 3D navigation widget.

### Rollback / Review Notes
- Review `desktop/ui/app.js` and `desktop/ui/styles.css` together; the behavioral and visual parts of the viewer polish are intentionally paired.
- This pass is presentation-focused and does not alter backend generation contracts or setup/runtime architecture.

## 2026-04-08 - 0.7.5-alpha - system-status-layout-correction

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Removed the incorrect full-width bottom system-status dock and restored the main workspace to a cleaner single-page layout.
- Integrated system status into the existing info strip so the lower summary area now contains four consistent sections: System status, Dimensions, Generation summary, and Review status.
- Moved logs out of the primary layout into a modal accessed from the new `Show logs` button in the System status section.
- Preserved real runtime state wiring for local AI readiness, Blender status, last action, and generation status without reducing viewer height.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Logs are now modal-only; if persistent inline diagnostics are needed later, they should return in a secondary debug-only surface rather than the core workspace.
- The `Show logs` flow is intentionally lightweight and does not yet include filtering or copy/export actions.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; this pass is a focused correction to the system-status placement and layout balance.

## 2026-04-08 - 0.7.4-alpha - ui-refinement-layout-polish

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Reworked the workspace layout toward a clearer single-page modeling shell with a smaller inline generation bar above the viewer instead of a heavier summary card.
- Replaced the previous new-chat treatment with a circular `+` button and tooltip, shortened the prompt placeholder, and improved prompt spacing and focus treatment.
- Moved runtime/log output into a collapsible bottom dock labeled `System status` and `Logs`.
- Refined the right rail into a scrollable facts area with the Actions section pinned to the bottom.
- Added viewer overlay controls: a bottom-right XYZ axis indicator that responds to camera orientation and a top-right circular orbit control for quick view rotation.
- Kept the working generation loop and real backend state wiring intact while reducing visual weight and increasing viewer dominance.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The on-screen orbit puck is a lightweight alpha interaction aid, not a full CAD navigation widget.
- The axis indicator is a UI overlay driven from camera orientation rather than a separate full 3D inset scene.
- `View plan` and several right-rail actions remain staged for later alpha passes.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; this pass is primarily layout and interaction polish.

## 2026-04-08 - 0.7.3-alpha - alpha-ux-lock-pass

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `README.md`
- `desktop/README.md`
- `docs/README.md`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `desktop/ui/app.js`

### Summary
- Refined the desktop workspace into clearer product roles: setup and request context on the left, viewer and current-state summary in the center, and model facts plus actions on the right.
- Replaced developer-ish setup wording with more understandable local-first language such as `Set Up AI`, `AI ready`, and `Check This PC`.
- Improved visual hierarchy, spacing, and action emphasis so the current generation state is easier to read at a glance.
- Removed misleading placeholder values from the initial UI and made unavailable or review-level information explicitly labeled.
- Updated all README surfaces to reflect the current alpha product shape and local-first desktop experience.

### Verification
- `python -m compileall app desktop tests`

### Known Limitations
- Some actions remain intentionally disabled or staged for later alpha passes, including export, save-project flow, and deep plan inspection.
- This pass focuses on UX shaping and wording; it does not change backend geometry logic.
- Full live desktop polish still depends on future passes with real interactive runtime review.

### Rollback / Review Notes
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; they define the full UX lock pass.
- Review the three README files together; they now describe the same desktop-first alpha product story.

## 2026-04-07 - 0.7.2-alpha - python-executor-generation-refactor

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `desktop/bridge.py`
- `tests/test_desktop_bridge.py`

### Summary
- Removed Qt ownership of model-generation execution and moved the generation path onto a single-worker `ThreadPoolExecutor` for simpler alpha reliability.
- Added a plain Python generation job wrapper that logs job start, calls `backend_controller.generate_model(...)`, preserves terminal payload shape, and converts unexpected exceptions into structured failure payloads.
- Added a Qt-safe handoff from executor futures back into the bridge through internal bridge signals so UI-facing signal emission and bridge state mutation still occur on the Qt side.
- Preserved the runtime/setup architecture, desktop payload contract, and existing UI-facing `generationCompleted` / `generationFailed` flow.
- Kept alpha stability simple by rejecting overlapping generation requests while one job is active.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- Model generation now avoids Qt-thread execution, but live runtime behavior still depends on end-to-end desktop execution outside unit tests.
- Ollama model-pull handling still uses the existing Qt thread path; this pass only changes model-generation execution.

### Rollback / Review Notes
- Review `desktop/bridge.py` and `tests/test_desktop_bridge.py` together; they contain the full execution-model change.
- `desktop/backend_controller.py` remains the generation/runtime API boundary; this pass does not alter backend geometry logic.

## 2026-04-07 - 0.7.1-alpha - qthread-worker-pattern-fix

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `desktop/bridge.py`
- `tests/test_desktop_bridge.py`

### Summary
- Replaced the `GenerationThread(QThread)` generation path with a `GenerationWorker(QObject)` moved onto a plain `QThread`.
- Wired `thread.started -> worker.run`, `worker.resultReady/resultFailed -> thread.quit`, and kept strong references in the bridge via `_active_thread` and `_active_worker`.
- Preserved the bridge architecture while adding explicit worker-run logs before and after `thread.start()` plus worker entry/exception logs.
- Updated focused desktop bridge tests for the worker lifecycle, cleanup, and success/failure payloads.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_desktop_bridge`

### Known Limitations
- This pass fixes the generation worker threading pattern only; it does not change backend generation logic or broader desktop UI flow.
- Live runtime confirmation still depends on running the desktop shell and observing the emitted worker logs.

### Rollback / Review Notes
- Review `desktop/bridge.py` and `tests/test_desktop_bridge.py` together; the main change is the move from QThread subclassing to a QObject worker.
- If rollback is needed, revert this pass as a single threading-pattern checkpoint.

## 2026-04-07 - 0.7.0-alpha - local-first-runtime-foundation

### Files Changed
- `.gitignore`
- `CHANGELOG.md`
- `README.md`
- `VERSION`
- `app/state.py`
- `app/runtime/__init__.py`
- `app/runtime/blender.py`
- `app/runtime/health.py`
- `app/runtime/models.py`
- `app/runtime/ollama.py`
- `app/runtime/setup.py`
- `desktop/README.md`
- `desktop/backend_controller.py`
- `desktop/bridge.py`
- `desktop/ui/app.js`
- `desktop/ui/index.html`
- `desktop/ui/styles.css`
- `tests/test_backend_alpha_pipeline.py`
- `tests/test_desktop_bridge.py`

### Summary
- Added a dedicated `app/runtime/` package for Ollama detection, Blender detection, runtime health, setup coordination, and recommended model definitions.
- Extended persisted session state with runtime/setup fields so desktop startup, repair flows, and readiness gating share one source of truth.
- Refactored the desktop controller and bridge to expose runtime health APIs, model pulls, and a setup smoke test without depending on terminal chat orchestration.
- Added an in-app setup gate in the desktop UI so generation is blocked until Ollama, the required local model, Blender, and setup completion are all verified.
- Replaced placeholder Ollama-connected footer copy with runtime-health-driven status text.
- Tightened ignore rules for review zips, nested `.git` folders, generated previews, Blender outputs, and cache artifacts.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline tests.test_desktop_bridge`

### Known Limitations
- The setup UI is still a foundational guided gate, not a polished multi-screen wizard.
- Blender detection is currently Windows-oriented and relies on common local install paths plus `BLENDER_PATH`.
- The model recommendation set is intentionally small and opinionated for the transition pass.
- This pass does not fully redesign the main workspace after setup completion; it focuses on runtime/setup backbone and truthful gating.

### Rollback / Review Notes
- Review `app/runtime/*`, `desktop/backend_controller.py`, and `desktop/bridge.py` together; they define the new runtime contract.
- Review `desktop/ui/index.html`, `desktop/ui/styles.css`, and `desktop/ui/app.js` together; they define the setup gate and runtime-truth UI changes.
- Revert this pass as one architectural checkpoint if the runtime/setup foundation needs to be backed out cleanly.

## 2026-04-07 - 0.6.12-alpha - webchannel-generate-model-entrypoint-verification

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `desktop/bridge.py`
- `desktop/ui/app.js`
- `tests/test_desktop_bridge.py`

### Summary
- Kept the direct `QThread.run()` generation path and cleaned up the WebChannel entrypoint around it.
- Added a first-line bridge slot log for the exposed `@Slot(str) generateModel(self, prompt_text: str)` method and wrapped the full slot body so any pre-thread exception logs a traceback and emits a terminal failure payload.
- Renamed the generation-thread payload signals from `finished`/`failed` to `resultReady`/`resultFailed` to avoid colliding with `QThread.finished()`.
- Added JS-side logging of `typeof bridge.generateModel`, explicit missing-entrypoint handling, and a guarded `try/catch` around the WebChannel method call.
- Updated focused bridge tests for the renamed signals and new generateModel slot exception message.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_desktop_bridge`

### Known Limitations
- Live runtime confirmation is still needed to prove whether the Python slot is now being entered when the UI logs `bridge generateModel call start`.
- This pass verifies and hardens the JS -> Python boundary only; it does not change backend generation logic or UI rendering logic.

### Rollback / Review Notes
- Review `desktop/bridge.py` and `desktop/ui/app.js` together; this pass is about the exposed entrypoint and unambiguous signal naming.
- `tests/test_desktop_bridge.py` now asserts the slot-entry log and `resultReady`/`resultFailed` signal usage.
- If rollback is needed, revert this as a single WebChannel entrypoint verification checkpoint on top of `0.6.11-alpha`.

## 2026-04-07 - 0.6.11-alpha - bridge-generation-thread-refactor

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `desktop/bridge.py`
- `tests/test_desktop_bridge.py`

### Summary
- Replaced the `QObject` worker plus `moveToThread` startup path with a direct `GenerationThread(QThread)` implementation that performs deterministic generation inside `run()`.
- Removed the active-path `moveToThread`, `thread.started -> worker.run`, and `invokeMethod` choreography from bridge startup, leaving a simpler thread lifecycle with direct `thread.start()`.
- Kept the completion contract intact by emitting JSON-safe terminal payloads from the generation thread on both success and exception paths.
- Simplified cleanup so the thread is allowed to finish naturally and the bridge clears active refs in one thread-finished cleanup path.
- Updated the focused bridge tests for the new direct-thread lifecycle and structured failure emission.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_desktop_bridge`

### Known Limitations
- Live Qt runtime confirmation is still needed to prove the direct `QThread.run()` path resolves the original thread-start stall in the packaged desktop shell.
- This pass does not change backend generation logic or UI rendering behavior; it only replaces the generation-thread startup mechanism.

### Rollback / Review Notes
- Review `desktop/bridge.py` first; the core change is the replacement of `GenerationWorker` with `GenerationThread`.
- `tests/test_desktop_bridge.py` now covers the direct thread success/failure path rather than the removed `moveToThread` choreography.
- If rollback is needed, revert this as a single generation-thread refactor checkpoint on top of `0.6.10-alpha`.

## 2026-04-07 - 0.6.10-alpha - bridge-worker-log-slot-fix

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `desktop/bridge.py`
- `tests/test_desktop_bridge.py`

### Summary
- Made the bridge worker log relay a real Qt slot with `@Slot(str)` so the `worker.log` hookup uses an explicit signature-safe receiver.
- Added an explicit `[BRIDGE] worker.log connected` trace immediately after the connection point that now appears to be the last visible setup boundary before the live stall.
- Kept the rest of the minimal signal map unchanged and did not alter backend generation or UI rendering behavior.
- Added a focused bridge test assertion that the setup path reaches the new worker-log connection trace before thread start.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_desktop_bridge`

### Known Limitations
- This pass makes the `worker.log` hookup Qt-safe and observable, but live runtime confirmation is still needed to prove whether this connection was the actual blocker.
- If the next live trace now reaches `worker.log connected` and stops later, the blocker has moved further down the setup path and is narrower again.

### Rollback / Review Notes
- Review `desktop/bridge.py` first; the change is narrowly centered on the worker log relay and its connection trace.
- `tests/test_desktop_bridge.py` now asserts that setup reaches the `worker.log connected` boundary.
- If rollback is needed, revert this as a single worker-log slot hardening checkpoint on top of `0.6.9-alpha`.

## 2026-04-07 - 0.6.9-alpha - worker-run-invokemethod-start-fix

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `desktop/bridge.py`
- `tests/test_desktop_bridge.py`

### Summary
- Replaced the direct `thread.started -> worker.run` hookup with a bridge-owned `QMetaObject.invokeMethod(...)` start path so worker execution is triggered explicitly after the thread start signal fires.
- Kept `GenerationWorker.run` as an explicit zero-argument Qt slot and added bridge logs around invoke start, invoke return value, and invoke failure.
- Made invoke failures terminal: if `invokeMethod` returns false or raises, the bridge now emits a structured terminal failure payload and requests thread shutdown so the desktop shell unwinds cleanly.
- Added a focused regression test covering the `invokeMethod` failure path.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_desktop_bridge`

### Known Limitations
- This pass still needs live Qt runtime confirmation to prove the worker now starts reliably in the real desktop shell.
- The exact original failure is most likely the direct `thread.started -> worker.run` hookup, but live trace after this pass is still needed for final confirmation.

### Rollback / Review Notes
- Review `desktop/bridge.py` first; the core change is in `_handle_thread_started`.
- `tests/test_desktop_bridge.py` now covers the `invokeMethod` failure unwind path.
- If rollback is needed, revert this as a single worker-start invocation checkpoint on top of `0.6.8-alpha`.

## 2026-04-07 - 0.6.8-alpha - bridge-minimal-signal-wiring

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `desktop/bridge.py`
- `tests/test_desktop_bridge.py`

### Summary
- Simplified the Qt bridge start path to a minimal explicit signal/slot map: `thread.started -> worker.run`, `worker.finished -> _handle_worker_finished`, `worker.failed -> _handle_worker_failed`, and `thread.finished -> _handle_thread_finished`.
- Removed direct setup-time quit and inline cleanup signal hookups from the active generation path, so bridge-owned handlers now control completion, thread shutdown, and cleanup in one place.
- Added explicit lifecycle handlers for worker-finished, worker-failed, thread-finished, and cleanup, with trace logs around each remaining connection and lifecycle boundary.
- Kept the submit/setup exception trap so any remaining setup failure still emits a terminal failure payload instead of leaving the shell stuck in `Generating...`.
- Added focused bridge regression coverage for the simplified cleanup path and updated completion-path tests to the new handler names.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_desktop_bridge`

### Known Limitations
- Live Qt runtime confirmation is still needed to prove the simplified signal map resolves the original setup-time failure in the actual desktop shell.
- This pass narrows the setup path, but it does not change backend generation or UI rendering behavior.

### Rollback / Review Notes
- Review `desktop/bridge.py` first; the core change is the reduced signal wiring and explicit bridge-owned lifecycle handlers.
- `tests/test_desktop_bridge.py` covers cleanup and failure behavior for the new handler structure.
- If rollback is needed, revert this as a single bridge wiring simplification checkpoint on top of `0.6.7-alpha`.

## 2026-04-07 - 0.6.7-alpha - bridge-submitprompt-exception-trap

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `desktop/bridge.py`
- `tests/test_desktop_bridge.py`

### Summary
- Wrapped the full bridge submit/setup path in `try/except` so thread/worker setup failures can no longer stop silently between connection wiring and `thread.start()`.
- Added explicit trace logs for every remaining setup step, including finished/failed signal hookups, thread-quit hookups, thread-finished hookup, cleanup hookup, and the boundary around `thread.start()`.
- Added explicit early-return logs for empty-prompt and already-running guards.
- Ensured setup-time exceptions emit a terminal failure payload and failure signal so the UI can unwind instead of remaining in `Generating...`.
- Added a focused bridge regression test that forces a setup exception before thread start and verifies terminal failure emission.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_desktop_bridge`

### Known Limitations
- This pass traps setup failure, but the exact live failing line still requires one traced runtime reproduction to confirm whether it is in a Qt connect call or `thread.start()` boundary.
- The pass is intentionally limited to bridge setup and does not change backend generation or UI rendering logic.

### Rollback / Review Notes
- Review `desktop/bridge.py` first; the entire fix is in the submit/setup block.
- `tests/test_desktop_bridge.py` now covers one synthetic setup-time exception path.
- If rollback is needed, revert this as a single submitPrompt exception-trap checkpoint on top of `0.6.6-alpha`.

## 2026-04-07 - 0.6.6-alpha - qt-worker-start-path-fix

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `desktop/bridge.py`
- `tests/test_desktop_bridge.py`

### Summary
- Tightened the Qt worker start path by keeping explicit active thread/worker references on the bridge and tracing the full start lifecycle from thread creation through thread start and worker-start watchdog.
- Switched the worker run connection to an explicit queued connection and added thread-start and thread-finished trace hooks.
- Added a lightweight watchdog log to report when `worker.run` has not started shortly after `thread.start()`.
- Kept completion logic intact and focused only on guaranteeing and tracing the pre-generation start path.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_desktop_bridge`

### Known Limitations
- This pass improves lifecycle persistence and traceability, but live Qt runtime confirmation is still needed to verify the original failure is resolved.
- The watchdog is diagnostic only and does not force-start the worker.

### Rollback / Review Notes
- Review `desktop/bridge.py` first; that file contains the entire lifecycle change.
- `tests/test_desktop_bridge.py` now includes a focused assertion that active thread/worker refs persist through the start call.
- If rollback is needed, revert this as a single Qt start-path fix checkpoint on top of `0.6.5-alpha`.

## 2026-04-07 - 0.6.5-alpha - desktop-live-trace-instrumentation

### Files Changed
- `CHANGELOG.md`
- `VERSION`
- `desktop/backend_controller.py`
- `desktop/bridge.py`
- `desktop/ui/app.js`

### Summary
- Added explicit live trace logging across the desktop generation path so one failing run can be followed from submit through worker execution, bridge completion emit, state refresh, UI terminal handling, and preview loading.
- Added bridge-side logging for submit, worker creation, worker start, backend return, payload details before emit, completion handler entry, completion emit boundaries, refresh boundaries, fallback emission, and full tracebacks.
- Added UI-side logging for WebChannel bootstrap, bridge/signal connection, generation start, completion callback entry, raw payload receipt, payload parse, terminal status identity, terminal renderer entry, preview load start/success/failure, and final terminal UI application.
- Added one safety measure so the UI clears `generationInFlight` before awaiting preview load, preventing preview delay from leaving the shell visually stuck in `Generating...`.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_desktop_bridge`

### Known Limitations
- This pass is diagnostic and does not attempt to fix the underlying live runtime failure beyond ensuring preview wait does not hold the active-generation state.
- Duplicate trace lines may appear because the bridge and UI now both log adjacent phases intentionally.
- Live terminal output and desktop DevTools/browser console capture are still needed to identify the exact failing hop.

### Rollback / Review Notes
- Review `desktop/bridge.py` and `desktop/ui/app.js` together; the value of this pass is the aligned trace coverage across the handoff boundary.
- `desktop/backend_controller.py` only gained narrow trace output around deterministic generation start/return.
- If rollback is needed, revert this as a single diagnostics-only checkpoint on top of `0.6.4-alpha`.

## 2026-04-07 - 0.6.4-alpha - desktop-flow-decoupling-cleanup

### Files Changed
- `README.md`
- `CHANGELOG.md`
- `VERSION`
- `.gitignore`
- `app/backend/runtime.py`
- `app/backend/pipeline.py`
- `app/chat_agent.py`
- `desktop/README.md`
- `desktop/backend_controller.py`
- `desktop/bridge.py`
- `desktop/ui/app.js`

### Summary
- Decoupled the desktop path from `app/chat_agent.py` by moving controller imports to the deterministic backend pipeline, backend runtime paths, and backend version helpers directly.
- Removed unused Ollama coupling from the desktop controller; the desktop path no longer constructs or passes `OllamaClient` for deterministic generation.
- Simplified bridge responsibilities so the worker serializes through the controller JSON-safe path and the bridge centers on generation completion emission plus passive state refresh.
- Removed the misleading procedural gear preview fallback from the desktop UI so frontend expectations stay aligned with current backend alpha-family support.
- Added repo hygiene ignore rules for runtime state, generated previews, generated Blender scripts, and Python cache artifacts.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline`
- `python -m unittest tests.test_desktop_bridge`

### Known Limitations
- Live desktop runtime confirmation is still needed after decoupling to validate the simplified flow under real Qt WebEngine conditions.
- Terminal chat mode in `app/chat_agent.py` still keeps its own optional Ollama-oriented terminal behavior for legacy use; this cleanup only removes that dependency from the desktop path.
- The bridge still contains defensive fallback logic because the desktop shell needs explicit unwind guarantees, though the core desktop path is now narrower and easier to trace.

### Rollback / Review Notes
- Review `app/backend/runtime.py`, `desktop/backend_controller.py`, `desktop/bridge.py`, and `app/chat_agent.py` together; those files carry the desktop-path decoupling.
- `desktop/ui/app.js` changed only to remove the misleading gear fallback preview.
- If rollback is needed, revert this as a single desktop flow cleanup checkpoint on top of `0.6.3-alpha`.

## 2026-04-07 - 0.6.3-alpha - desktop-bridge-crash-hardening

### Files Changed
- `README.md`
- `CHANGELOG.md`
- `VERSION`
- `desktop/backend_controller.py`
- `desktop/bridge.py`
- `desktop/ui/app.js`
- `tests/test_desktop_bridge.py`

### Summary
- Hardened bridge completion so `_handle_generation_finished` now logs each step, normalizes payloads defensively, and catches completion/refresh exceptions instead of letting the slot raise.
- Made `getInitialState()` JSON-safe by converting controller status values recursively before serialization and returning a safe fallback state payload if bridge serialization fails.
- Added a last-resort bridge fallback so malformed completion payloads and bridge-side failures still emit a terminal event to the UI.
- Kept refresh failures from killing the run loop: a successful completion emit is preserved even if later state refresh fails.
- Added focused bridge regression coverage for JSON-safe bootstrap state, malformed completion payload fallback, refresh failure after completion emit, and terminal failure delivery.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline`
- `python -m unittest tests.test_desktop_bridge`
- Manual inspection confirmed:
- `generationFailed` now also unwinds the UI if completion emit degrades
- bridge logs include payload type/preview, refresh status, and exception tracebacks
- bridge fallback still reaches the UI terminal path

### Known Limitations
- Live Qt runtime confirmation is still needed to verify the exact original crash signature against the new bridge logging.
- This pass does not remove duplicate terminal notifications in every fallback case; it prioritizes guaranteed unwind over deduplicating diagnostics.
- The Chromium GPU SharedImage warning remains unrelated to this Python-side crash hardening pass.

### Rollback / Review Notes
- Review `desktop/bridge.py` first, then `desktop/backend_controller.py`, `desktop/ui/app.js`, and `tests/test_desktop_bridge.py`.
- This pass is narrowly focused on bridge serialization, completion safety, and refresh fallback behavior.
- If rollback is needed, revert this as a single bridge crash hardening checkpoint on top of `0.6.2-alpha`.

## 2026-04-07 - 0.6.2-alpha - desktop-terminal-failure-unwind-hardening

### Files Changed
- `README.md`
- `CHANGELOG.md`
- `VERSION`
- `app/backend/pipeline.py`
- `app/state.py`
- `desktop/backend_controller.py`
- `desktop/bridge.py`
- `desktop/ui/app.js`
- `tests/test_backend_alpha_pipeline.py`

### Summary
- Normalized the terminal generation contract so desktop-facing results now carry explicit terminal status fields for ready, unsupported, validation-failed, and error outcomes.
- Made backend pipeline exceptions return structured terminal payloads instead of escaping the worker path without a normal completion payload.
- Routed bridge-level failures through the same terminal completion signal so the UI receives a terminal event for worker exceptions and local bridge failures.
- Hardened the UI to unwind every terminal outcome, replace loading overlays with explicit terminal messages, and log request text, generation id, status, reason, and preview path for alpha diagnosis.
- Added regression coverage for unsupported results, caught backend errors, preview export failures, and controller status passthrough.

### Verification
- `python -m compileall app desktop tests`
- `python -m unittest tests.test_backend_alpha_pipeline`
- Manual inspection of `desktop/ui/app.js` confirmed:
- `generationInFlight` is always cleared in `finally`
- non-ready terminal payloads do not wait for preview
- unsupported and error outcomes render explicit terminal messaging
- bridge failures are converted into terminal completion payloads

### Known Limitations
- Live Qt desktop runtime still needs confirmation for every failure mode, especially malformed payload handling inside the WebChannel runtime.
- `pytest` is not installed in this environment, so verification used the requested unittest target instead.
- Preview export failure still leaves model generation marked `ready`; the terminal contract relies on `preview_export_status="error"` plus explicit UI messaging rather than redefining generation success.

### Rollback / Review Notes
- Review `app/backend/pipeline.py`, `desktop/bridge.py`, and `desktop/ui/app.js` together because the stabilization depends on the shared terminal payload shape.
- `desktop/backend_controller.py` now also persists controller-owned terminal failures so runtime status cards reflect actual bridge/worker failures.
- If rollback is needed, revert this as a single failure-path hardening checkpoint on top of `0.6.1-alpha`.

## 2026-04-07 - 0.6.1-alpha - desktop-active-run-loop-hardening

### Files Changed
- `README.md`
- `CHANGELOG.md`
- `VERSION`
- `desktop/README.md`
- `app/state.py`
- `app/model_library.py`
- `app/backend/pipeline.py`
- `desktop/backend_controller.py`
- `desktop/bridge.py`
- `desktop/ui/app.js`
- `tests/test_backend_alpha_pipeline.py`

### Summary
- Added backend-owned `generation_id` and preview asset identity to each generation result and persisted both into session state for desktop bootstrap and refresh.
- Switched preview export to generation-specific GLB filenames so the viewer no longer depends on a constant preview path or frontend-owned timestamps to refresh.
- Passed generation identity and preview identity through the desktop controller and bridge unchanged.
- Hardened the desktop completion flow with guarded result handling, backend-owned request text, awaited preview loading, and procedural fallback when external preview loading fails.
- Blocked New Chat during an in-flight generation so the active desktop session cannot desynchronize from the worker result.

### Verification
- `python -m compileall app desktop tests`
- `pytest tests/test_backend_alpha_pipeline.py`
- Static inspection of `desktop/ui/app.js` confirmed:
- `generationCompleted` is guarded by `try/catch/finally`
- `generationInFlight` is cleared in `finally`
- preview loading uses backend-owned preview identity
- New Chat is blocked while a generation is in flight

### Known Limitations
- This pass still needs live desktop runtime confirmation in Qt WebEngine to validate end-to-end refresh behavior with repeated GLB loads.
- Generation-specific preview files currently accumulate in `data/previews/`; this pass stabilizes identity and caching first, not cleanup policy.
- The desktop shell still supports only one active generation worker at a time and does not implement cancellation.

### Rollback / Review Notes
- Review `app/backend/pipeline.py`, `app/state.py`, `desktop/backend_controller.py`, `desktop/bridge.py`, and `desktop/ui/app.js` together because the stabilization depends on the shared payload contract.
- `app/model_library.py` was updated only to carry the backend-owned generation identity into saved model entries.
- If rollback is needed, revert this as a single cross-layer desktop loop hardening checkpoint on top of `0.6.0-alpha`.

## 2026-04-06 - 0.6.0-alpha - desktop-core-loop-stabilization

### Files Changed
- `README.md`
- `CHANGELOG.md`
- `VERSION`
- `desktop/README.md`
- `app/state.py`
- `app/model_library.py`
- `app/backend/pipeline.py`
- `desktop/backend_controller.py`
- `desktop/bridge.py`
- `desktop/ui/index.html`
- `desktop/ui/app.js`

### Summary
- Stabilized the core desktop loop around a clean idle launch, reliable prompt submission, successful generation application, and repeatable new-chat resets.
- Split passive restored backend/library state from the active desktop chat session so the app no longer boots into the last generation as if it were the current session.
- Added a lightweight local-first model library store and wired successful generations to create saved model entries.
- Added tab-intent groundwork for Chat, Models, Projects, and Templates, plus a starter template data structure for future use.
- Preserved the current backend and viewer architecture while improving desktop session/state flow.

### Verification
- `python -m compileall app desktop tests`
- Controller/library smoke checks for `DesktopStatus.library_summary`
- Static inspection of desktop UI wiring for:
- idle bootstrap reset
- new chat reset handlers
- repeated-generation guard handling
- tab intent groundwork

### Known Limitations
- The Models/Projects/Templates tabs still use groundwork data and intent only; they are not full tab views yet.
- Model library persistence is intentionally lightweight and local-first, not yet a full project-management system.
- Desktop verification in this pass is static/code-path based rather than live UI automation.

### Rollback / Review Notes
- Review `app/model_library.py`, `app/backend/pipeline.py`, `desktop/backend_controller.py`, `desktop/bridge.py`, and `desktop/ui/app.js` together.
- This pass avoids cosmetic redesign and focuses on desktop loop stability and lightweight persistence groundwork.
- If rollback is needed, revert this as a single desktop-loop stabilization checkpoint on top of `0.5.2-alpha`.

## 2026-04-06 - 0.5.2-alpha - desktop-restored-state-and-viewer-fit-fix

### Files Changed
- `README.md`
- `CHANGELOG.md`
- `VERSION`
- `desktop/ui/app.js`

### Summary
- Fixed the desktop restored-state behavior so bootstrapped previous results are treated as restored history instead of an active generation.
- Cleared generation guard state after restored state is applied so prompt submission is immediately usable on app load and identical prompts can be resubmitted.
- Added UI debug logging for restored state application, submit allow/block decisions, generation start, and generation completion.
- Replaced the viewer auto-fit distance logic so real preview assets are framed from their actual bounds rather than being pushed away by a hardcoded minimum-size clamp.

### Verification
- `python -m compileall app desktop tests`
- Static inspection of `desktop/ui/app.js` confirmed:
- restored state clears `generationInFlight`
- submit path logs allow/block reasons
- generation completion clears the guard
- viewer fit now uses actual bounds and bounding-sphere-aware distance instead of `Math.max(..., 1)`

### Known Limitations
- This pass does not add live runtime desktop automation.
- Very unusual models may still need manual Focus/Reset interaction if their origin or orientation is unexpected.
- Debug logging remains temporary and UI-side only.

### Rollback / Review Notes
- The fix is intentionally narrow and centered in `desktop/ui/app.js`.
- If rollback is needed, revert this as a focused desktop-state/viewer-fit patch on top of `0.5.1-alpha`.

## 2026-04-06 - 0.5.1-alpha - desktop-result-flow-promise-fix

### Files Changed
- `README.md`
- `CHANGELOG.md`
- `VERSION`
- `desktop/ui/app.js`

### Summary
- Fixed the desktop UI result flow bug where Promise-returning Qt WebChannel slot calls were being parsed as if they were already JSON strings.
- Updated the UI bridge handling so initial state and Blender-launch responses are awaited before JSON parsing.
- Added temporary UI-layer debug logging around prompt submit, bridge call start, result receipt, result application, and preview path application.
- Preserved the existing backend, bridge, and viewer architecture while unblocking the desktop shell from leaving the UI stuck in `Generating...`.

### Verification
- `python -m compileall app desktop tests`
- Static inspection of `desktop/ui/app.js` confirmed:
- `getInitialState()` is now awaited before parsing
- `openLatestInBlender()` is now awaited before parsing
- `generationCompleted` still parses a resolved signal payload string directly

### Known Limitations
- This pass does not add full live desktop end-to-end runtime automation; verification is still static plus code-path review.
- Debug logging is intentionally temporary and UI-side only.

### Rollback / Review Notes
- The bug fix is intentionally narrow and centered in `desktop/ui/app.js`.
- If rollback is needed, revert this as a small UI result-handling patch on top of `0.5.0-alpha`.

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
