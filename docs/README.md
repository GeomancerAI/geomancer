# Geomancer Docs Site

This directory contains the static website and support pages for Geomancer. It is a presentation surface, not the engineering source of truth.

## Scope

- marketing and landing pages
- download and early-access pages
- support pages such as docs, privacy, and terms
- static assets for the public web presence

## Relationship To The Product

The current alpha product is a local-first desktop tool with:

- an in-app local setup flow
- a three-panel workspace
- a chat-style left conversation panel for prompts, setup updates, generation progress, and opening prompt examples embedded directly in Geomancer's message, now using the Geomancer avatar icon, stricter vertical-only chat scrolling, tighter bubble shadows, a dedicated thread scroll region between fixed header and composer, a compact composer toolbelt for prompt refinement and quick settings, and a stacked dynamic session title derived from the current prompt
- a grounded model viewer with a dominant-face-first generic pose solver, support-aware placement, final settling and conservative surface-leveling polish, deterministic first-load framing, compact review telemetry, a consolidated bottom footer/meta status band, a cleaner four-column instrument strip with restrained teal accents, in-view overlay navigation controls, a lower-right XYZ gizmo, and a calm play/pause auto-orbit toggle
- deterministic geometry generation
- Blender as the local handoff target

Those details should stay consistent with the root [README](../README.md) and the root `CHANGELOG.md`.

## Structure

```text
docs/
  index.html
  download.html
  early-access.html
  docs.html
  privacy.html
  terms.html
  assets/
    css/
    images/
    js/
    icons/
  README.md
```

## Local Preview

Open `index.html` directly in a browser for a quick preview, or serve the folder with a simple local static server if you want normal asset loading behavior.

## Maintenance Notes

- Keep public messaging aligned with the desktop alpha experience.
- Reflect local-first setup and deterministic geometry language where relevant.
- Avoid treating this folder as the source of truth for active application architecture.
