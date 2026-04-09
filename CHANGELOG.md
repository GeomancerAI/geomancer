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
