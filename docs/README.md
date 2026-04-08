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
- a grounded model viewer with a generic principal-axis pose solver, support-aware placement, deterministic first-load framing, and compact review telemetry
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
